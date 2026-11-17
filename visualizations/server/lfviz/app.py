# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""HTTP + WebSocket API of the visualization server (the one API for the whole project).

REST (JSON):
    GET    /api/health                     server version, counts
    GET    /api/viz                        catalogue: [registry.describe: {id, title, …, code_hash, schema}]
    GET    /api/viz/{viz}                  one entry
    GET    /api/recordings                 [S] the local recordings of the public site: {worlds: {<world>: its index.json},
                                           site: the public site's address (site/site.json; LFVIZ_SITE_URL overrides),
                                           published: whether that site is live (site/site.json), expected: {<world>:
                                           {version, code_hash, recordings: {id: key}, atlases: {id: key}}}: the keys
                                           the code here gives (integrator D11)}
    GET    /api/audiences                  the audiences and the sections in their order: {audiences: [{id, prefix, label,
                                           description, ui}], sections: [{id, label}]} (registry.AUDIENCES, SECTIONS)
    GET    /api/planned                    the planned items (``visualizations/planned.json``) not yet built: those whose
                                           id names an existing folder (S02 <-> s02_*) are dropped
    GET    /api/runs                       runs (live and recorded), newest first
    POST   /api/runs                       {viz, preset?, params?, seed?, label?} -> {id}; starts a run
    GET    /api/runs/{id}                  the run's meta (params, seed, code hash, modifications, commands)
    POST   /api/runs/{id}/command          {cmd, args} -> forwarded to the worker (same as over WebSocket); a suspended
                                           run is resumed first by a command that computes or changes the world
    POST   /api/runs/{id}/cancel           cancel the command the worker is computing now (the world as just before it)
    POST   /api/runs/{id}/stop             release the worker (the run is "suspended": resumable); not in the player
    POST   /api/runs/{id}/resume           rebuild a suspended run's world from its record (replay of its commands)
    POST   /api/runs/{id}/keep             {keep: bool}; kept records are never removed by the limits
    DELETE /api/runs/{id}                  delete a run that no tab has open, with its record (one still computing is
                                           suspended first)
    GET    /api/runs/{id}/stream           the raw record (stream.lfrec; a playground's kept segments joined) for
                                           offline analysis
    POST   /api/runs/{id}/record           a playground: {on: bool, window_s?, window_mb?} -> the buffer's state;
                                           on: what the buffer holds and everything from now on is kept for good
    GET    /api/runs/{id}/series           [LB1 P16.3] ?ids=a,b[&from&to&world&format=csv&max_points]: the recorded
                                           values of the world's measurables (lfviz.instruments)
    POST   /api/runs/{id}/sweep            [LB1 P16.3] a parameter sweep from the current moment ({..., estimate?});
    GET    /api/runs/{id}/sweeps[/{n}]     its progress and results (?format=csv); POST /sweeps/{n}/cancel: stop it (what
                                           it computed is kept); DELETE /sweeps/{n}: remove a finished one (lfviz.sweep)
    POST   /api/atlas/{world}/{atlas}/point {values, seed?, full_header?} -> the point's file (application/gzip),
                                           computed live in a memory- and time-limited process, as a site build packs
                                           it (lfviz.atlas_live; design of 2026-11-14 §3.7); headers X-LF-Source,
                                           X-LF-Key, X-LF-Code, X-LF-Made; 400 {error, hint?}, 409 (its checks end ✗),
                                           429, 503
    GET    /api/settings/runs              {keep_days}: runs without actions for this many days are removed
    PUT    /api/settings/runs              {keep_days, confirm?: [id]} -> saved and applied at once; 409 with
                                           {would_remove: [id]} if it would remove runs not all in ``confirm``

WebSocket:
    /ws/runs/{id}    server -> browser: binary messages (protocol.py): the record so far, "history_end", live tail
                     browser -> server: text JSON {cmd, args} (play, pause, speed, step, next_event, action)

The server's own worker commands (``SERVER_ONLY``: ``checkpoint_now``, which the sweeps send, and ``stop``) are refused
on the client routes, REST and WebSocket (review LB1-framework F6: any page on the LAN could make a playing world pickle
itself and start a record segment 10 times a second, with any data in the record as its tag).

Pages: ``/`` (the start page: the four audiences, their demonstrations and the laboratories), ``/runs`` (the runs and
their retention), ``/run?id=<id>`` (player; ``/run?rec=<world>/<rec>``: a saved recording), ``/worksheet?demo=<world>`` (a lab's printable worksheet), ``/legal`` (the licences, the third-party notices and the
disclaimer; their full texts at ``/legal/<name>``); static files under ``/static/``; the browser module of a
visualization under ``/viz/<id>/`` (its ``web/`` folder).

Files of the public site's kind [S]: ``/recordings/<world>/<file>`` and an atlas's ``/recordings/<world>/atlas/<atlas>/<file>``
(the recordings and atlases made by ``site/record.py``, from
``visualizations/recordings/`` or ``LFVIZ_RECORDINGS``; git-ignored) and ``/images/<file>`` (the pictures of the cards
and the README, ``docs/images/``).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path

from aiohttp import WSMsgType, web

from . import __version__, devices, i18n, registry
from .i18n import T, text_of
from .runs import RunManager

PLAYER = registry.ROOT / "player"
# the texts the licence page shows (review of 2026-10-29, R4, R8): a fixed list, nothing else is served from there
LEGAL = {"LICENSE.md": registry.ROOT / "LICENSE.md", "NOTICE": registry.ROOT / "NOTICE",
         "PUBLICATIONS.md": registry.ROOT / "PUBLICATIONS.md", "COMMERCIAL.md": registry.ROOT / "COMMERCIAL.md",
         "LICENSE-DOCS.txt": registry.ROOT / "LICENSE-DOCS.txt",
         "three.js-LICENSE": PLAYER / "vendor" / "three-0.185.1" / "LICENSE"}
log = logging.getLogger("lfviz")
MGR = web.AppKey("mgr", RunManager)
HK = web.AppKey("hk", asyncio.Task)
SERVER_ONLY = ("checkpoint_now", "stop")  # [LB1 F6] worker commands only the server sends (lfviz.sweep, lfviz.runs)


def client_command(body) -> dict:
    """[LB1 F6] A command from a client (REST or WebSocket): an object {cmd, args?} with a command name, never one of
    the server's own; ValueError (400) or PermissionError (403) with the owner's text otherwise."""
    if not isinstance(body, dict) or not isinstance(body.get("cmd"), str):
        raise ValueError(T("a command is an object {cmd, args}"))
    if body["cmd"] in SERVER_ONLY:
        raise PermissionError(T("only the server itself sends the command “{cmd}”", cmd=body["cmd"]))
    if body.get("args") is not None and not isinstance(body["args"], dict):
        raise ValueError(T("a command's “args” is an object"))
    return body


PLANNED = registry.ROOT / "planned.json"


def planned_list() -> list:
    """The planned items of the catalogue (``GET /api/planned``; the site's ``api/planned.json`` is the same list): the
    entries of ``planned.json`` whose id names no existing folder (S02 is dropped once ``s02_*`` exists)."""
    try:
        items = json.loads(PLANNED.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    built = {v.split("_", 1)[0].lower() for v in registry.viz_ids()}
    return [x for x in items if isinstance(x, dict) and str(x.get("id", "")).lower() not in built]


def audiences_list() -> dict:
    """The audiences and the sections of the catalogue, in their order (``GET /api/audiences``; the site's
    ``api/audiences.json`` is the same): ``registry.AUDIENCES`` and ``registry.SECTIONS``, their labels as ``T``; an audience's ``picture`` is the world
    whose poster its tile shows (None: the start page picks one)."""
    return {"audiences": [{"id": a["id"], "prefix": a["prefix"], "label": a["label"], "description": a["text"],
                           "ui": a["ui"], "picture": a.get("picture")} for a in registry.AUDIENCES],
            "sections": [{"id": s["id"], "label": s["label"]} for s in registry.SECTIONS]}


RECORDINGS_DEFAULT = registry.ROOT / "recordings"  # [S] site/record.py writes here (git-ignored)
IMAGES = registry.ROOT.parent / "docs" / "images"  # [S] the pictures of the cards and the README (site/posters.mjs)
SITE_JSON = registry.ROOT / "site" / "site.json"  # [S] {"published": bool, "url": …}: the public site (integrator D3)


def site_setting(env: bool = True) -> dict:
    """[S] The public site's setting (``site/site.json``, committed; the owner sets ``published`` on his go):
    ``{"published": bool, "url": str}``; ``LFVIZ_SITE_URL`` overrides the address. Until ``published`` the READMEs
    carry no links to the site and the player never falls back to it (integrator D3, D4). ``env=False``: the committed
    address only (the READMEs)."""
    try:
        s = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        log.warning("site setting %s not read: %s", SITE_JSON, e)
        s = {}
    url = (env and os.environ.get("LFVIZ_SITE_URL")) or str(s.get("url") or "https://ildar-idrisov.github.io/lfphys/")
    return {"published": s.get("published") is True, "url": url if url.endswith("/") else url + "/"}


SITE_URL = site_setting()["url"]  # [S] the public site (CONTRACT S/P)
_REC_FILE = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")


def recordings_dir() -> Path:
    """[S] The folder of the local recordings: ``LFVIZ_RECORDINGS`` or ``visualizations/recordings``."""
    return Path(os.environ.get("LFVIZ_RECORDINGS") or RECORDINGS_DEFAULT)


def expected_keys() -> dict:
    """[S] Per world with recordings: the version, the code hash and the keys of its recordings and atlases as the code
    here gives them (``sitelib.expected``; the code hash by ``registry.code_hash_current``): a server's player takes the
    public site's atlas only when its key is this one, and a local atlas with another key is stale (integrator D11)."""
    from .atlas_live import _sitelib  # noqa: PLC0415
    L = _sitelib()
    rh = L.recorder_hash()
    out = {}
    for vid in registry.viz_ids():  # sitelib.demo_worlds, one world at a time: a broken world must not hide the others
        try:
            viz = registry.load(vid)
            if viz.get("kind") == "playground" or not viz.get("recordings"):
                continue
            out[vid] = L.expected(L.planned_world(vid, registry.code_hash_current(vid), rh))
        except Exception as e:  # noqa: BLE001
            log.warning("recordings: the keys of %s not computed: %s", vid, e)
    return out


def recordings_list(folder: Path | None = None) -> dict:
    """[S] ``GET /api/recordings`` (the site's ``api/recordings.json`` is the same for its own folder): the index of
    every world that has one, the public site's address and whether it is published (``site_setting``): the player
    looks for a recording there only when ``published`` is true (integrator D4); ``expected``: the keys the code here
    gives (``expected_keys``; integrator D11)."""
    folder = recordings_dir() if folder is None else Path(folder)
    worlds = {}
    if folder.is_dir():
        for f in sorted(folder.glob("*/index.json")):
            try:
                idx = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                log.warning("recordings: %s not read: %s", f, e)
                continue
            if isinstance(idx, dict) and idx.get("world") == f.parent.name:
                worlds[f.parent.name] = idx
    site = site_setting()
    return {"worlds": worlds, "site": site["url"], "published": site["published"], "expected": expected_keys()}


def _json(data, status=200):
    return web.json_response(data, status=status, dumps=lambda d: json.dumps(d, ensure_ascii=False))


def _err(text, status=400, **extra):
    """An error for an API client: ``{"error": <T or text>, "text": <English>}`` (RULES.md «Languages and i18n»)."""
    return _json(i18n.error_body(text, **extra), status)


class NotJSON(ValueError):
    """A request body that is not JSON."""


async def _body(request):
    """A request's JSON body; ``NotJSON`` for any body that is not JSON: not UTF-8, malformed, or an integer of more
    than 4300 digits (a ``ValueError`` that is not a ``JSONDecodeError``; review R-F F12)."""
    try:
        return await request.json()
    except ValueError:
        raise NotJSON(T("the request body is not JSON")) from None


@web.middleware
async def no_cache(request, handler):
    resp = await handler(request)
    if isinstance(resp, web.StreamResponse) and not request.path.startswith("/ws/"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


def create_app(runs_dir: Path, **limits) -> web.Application:
    app = web.Application(middlewares=[no_cache], client_max_size=4 * 1024 * 1024)
    mgr = RunManager(runs_dir, **limits)
    app[MGR] = mgr
    CITE = registry.citation()  # what a publication cites: the version and this copy's code identifier

    async def health(request):
        return _json({"ok": True, "version": __version__, "visualizations": registry.viz_ids(),
                      "running": mgr.n_running(), "runs": len(mgr.runs), "max_workers": mgr.max_workers,
                      "cite": CITE})

    async def viz_list(request):
        out = []
        for vid in registry.viz_ids():
            try:
                out.append(registry.describe(mgr.viz(vid)))
            except Exception as e:  # a broken visualization must not hide the others
                out.append({"id": vid, "title": vid, "error": T("the visualization does not load: {error}", error=f"{type(e).__name__}: {e}"),
                            "kind": "playground" if vid.startswith("p") else "demo"})  # under its mode (B6-F24)
        return _json(out)

    async def viz_one(request):
        try:  # an old id (registry.ALIASES) gives the new entry
            return _json(registry.describe(mgr.viz(registry.resolve(request.match_info["viz"]))))
        except KeyError:
            return _err(T("there is no such visualization"), 404)

    async def viz_file(request):
        vid = request.match_info["viz"]
        if registry.resolve(vid) != vid:  # an old id: the file is at the new address (a view's module, its imports)
            raise web.HTTPMovedPermanently(f"/viz/{registry.resolve(vid)}/{request.match_info['path']}"
                                           + (f"?{request.query_string}" if request.query_string else ""))
        if vid not in registry.viz_ids():
            return _err(T("there is no such visualization"), 404)
        try:
            base = (registry.folder(vid) / "web").resolve()
        except KeyError:
            return _err(T("there is no such visualization"), 404)
        target = (base / request.match_info["path"]).resolve()
        if base not in target.parents or not target.is_file():
            return _err(T("there is no such file"), 404)
        return web.FileResponse(target)

    async def runs_list(request):
        return _json(mgr.list())

    async def runs_start(request):
        try:
            body = await _body(request)
        except NotJSON as e:
            return _err(e.args[0])
        if not isinstance(body, dict):
            return _err(T("the request body is a JSON object"))
        vid = registry.resolve(body.get("viz"))  # an old id (registry.ALIASES) starts the renamed world
        if vid not in registry.viz_ids():
            return _err(T("there is no such visualization"), 404)
        try:  # devices and precision for this run: the settings file, with the start form's overrides (plan P11)
            bset, bnotes = await devices.for_run(body.get("backend"))
        except ValueError as e:
            return _err(T("devices: {error}", error=text_of(e)), 400)
        except Exception as e:  # noqa: BLE001
            log.warning("run devices: %s", e)
            return _err(T("the engine did not check the choice of devices (details in the server's log)"), 500)
        seed = body.get("seed")
        try:
            seed = None if seed in (None, "") else int(seed)
            run = await mgr.start(vid, body.get("preset"), body.get("params"), seed,
                                  label=str(body.get("label", ""))[:200], source=request.remote or "",  # i18n-str-ok: typed by the owner
                                  backend=bset, backend_notes=bnotes)
        except OverflowError as e:
            return _err(text_of(e), 409)
        except ValueError as e:  # refused parameters (by their labels: review UX-ui U13, UX-params P2) or a refused
            # combination / memory estimate of the world (P1, P8): the catalogue shows it on the form, by field
            from .errors import owner_text
            fields = getattr(e, "fields", None) or {}
            return _err(owner_text(e)[0] if not fields else text_of(e), 400, fields=fields)
        return _json({"id": run.id})

    def _run(request):
        return mgr.get(request.match_info["id"])

    async def run_meta(request):
        try:
            r = _run(request)
        except KeyError:
            return _err(T("there is no such run"), 404)
        out = dict(r.meta)
        out.update(r.summary())
        return _json(out)

    async def run_command(request):
        try:
            r = _run(request)
            body = client_command(await _body(request))
            await r.command_resuming(body, request.remote or "")
        except KeyError:
            return _err(T("there is no such run"), 404)
        except PermissionError as e:  # [LB1 F6]
            return _err(text_of(e), 403)
        except (RuntimeError, OverflowError) as e:
            return _err(text_of(e), 409)
        except ValueError as e:  # not JSON, or not a command [LB1 F6]
            return _err(T("the request body is not JSON") if isinstance(e, (NotJSON, json.JSONDecodeError))
                        else text_of(e))
        return _json({"ok": True})

    async def run_cancel(request):
        """Cancel what the worker is computing now (review UX-ui U9): the world goes back to just before it."""
        try:
            r = _run(request)
            res = await r.cancel(request.remote or "")
        except KeyError:
            return _err(T("there is no such run"), 404)
        except (RuntimeError, OverflowError) as e:
            return _err(text_of(e), 409)
        return _json(res)

    async def run_stop(request):
        """Release the run's worker (it is resumed when asked to compute again); kept for scripts, the player has no
        stop (owner, 2026-10-28)."""
        try:
            r = _run(request)
        except KeyError:
            return _err(T("there is no such run"), 404)
        await r.suspend("user")
        return _json({"ok": True, "state": r.meta.get("state")})

    async def run_resume(request):
        try:
            r = _run(request)
            await mgr.resume(r)
        except KeyError:
            return _err(T("there is no such run"), 404)
        except (RuntimeError, OverflowError) as e:
            return _err(text_of(e), 409)
        return _json({"ok": True})

    async def run_keep(request):
        try:
            r = _run(request)
            body = await _body(request)
        except KeyError:
            return _err(T("there is no such run"), 404)
        except NotJSON as e:
            return _err(e.args[0])
        if not isinstance(body, dict):
            return _err(T("the request body is a JSON object"))
        r.meta["keep"] = bool(body.get("keep", True))
        r.save_meta()
        return _json({"ok": True, "keep": r.meta["keep"]})

    async def run_delete(request):
        try:
            await mgr.delete(request.match_info["id"])
        except KeyError:
            return _err(T("there is no such run"), 404)
        except RuntimeError as e:
            return _err(text_of(e), 409)
        return _json({"ok": True})

    async def run_stream(request):
        try:
            r = _run(request)
        except KeyError:
            return _err(T("there is no such run"), 404)
        if not r.buffered:
            return web.FileResponse(r.stream_path, headers={
                "Content-Disposition": f'attachment; filename="{r.id}.lfrec"'})
        # a playground's buffer: one record of the kept segments, each world's header before its first kept message
        from . import protocol
        resp = web.StreamResponse(headers={"Content-Disposition": f'attachment; filename="{r.id}.lfrec"',
                                           "Content-Type": "application/octet-stream"})
        await resp.prepare(request)
        await resp.write(protocol.MAGIC)
        sent = set()
        cache: dict = {}
        r.readers += 1  # the window is not trimmed while the download reads the segments (review B6-F9)
        try:
            for e in list(r.entries):
                msg = r._read(e, cache)
                if e.kind == "header":
                    sent.add(protocol.peek_meta(msg).get("world", 1))
                else:
                    w = r._world_of_seg(e.seg)
                    if w not in sent and w in r.headers:
                        sent.add(w)
                        await resp.write(protocol.frame_stream_item(r.headers[w]))
                await resp.write(protocol.frame_stream_item(msg))
        finally:
            r.readers -= 1
            for f in cache.values():
                f.close()
        await resp.write_eof()
        return resp

    async def run_record(request):
        try:
            r = _run(request)
            body = await _body(request)
            # validated (review B6-F12): an object; "on" a JSON boolean, unchanged when absent; the window numbers
            if not isinstance(body, dict):
                raise ValueError(T("the request body is a JSON object"))
            on = body.get("on")
            if on is not None and not isinstance(on, bool):
                raise ValueError(T("“on” is true or false"))
            for k in ("window_s", "window_mb"):
                v = body.get(k)
                if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
                    raise ValueError(T("“{key}” is a number", key=k))
            return _json(r.set_recording(on, body.get("window_s"), body.get("window_mb")))
        except KeyError:
            return _err(T("there is no such run"), 404)
        except ValueError as e:  # NotJSON too
            return _err(text_of(e), 400)
        except RuntimeError as e:
            return _err(text_of(e), 409)

    async def ws_run(request):
        try:
            r = _run(request)
        except KeyError:
            return _err(T("there is no such run"), 404)
        ws = web.WebSocketResponse(heartbeat=20.0, max_msg_size=1 << 20)
        await ws.prepare(request)
        viewer = r.add_viewer(ws)
        pump = asyncio.create_task(viewer.pump())
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        await r.command_resuming(client_command(json.loads(msg.data)), request.remote or "")
                    except (ValueError, PermissionError, RuntimeError, OverflowError) as e:  # [LB1 F6] also refused
                        await ws.send_str(json.dumps(i18n.error_body(text_of(e)), ensure_ascii=False))
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        finally:
            r.remove_viewer(viewer)
            pump.cancel()
        return ws

    async def on_startup(app):
        app[HK] = asyncio.create_task(mgr.housekeeping())
        removed = mgr.cleanup()
        if removed:
            log.info("removed by limits: %s", removed)

    async def on_cleanup(app):
        app[HK].cancel()
        await mgr.shutdown()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # --- devices and precision (plan P11) ---------------------------------------------------------------------
    async def api_devices(request):
        try:
            info = await devices.probe()
        except Exception as e:
            return _err(T("the engine did not report its devices: {error}", error=text_of(e)), 500)
        return _json({**info, "settings": devices.load()})

    async def api_settings_get(request):
        return _json(devices.load())

    async def api_settings_put(request):
        if (request.content_length or 0) > devices.MAX_BYTES:
            return _err(T("the settings are longer than {n:d} KB", n=devices.MAX_BYTES // 1024), 413)
        try:
            body = await _body(request)
        except NotJSON as e:
            return _err(e.args[0])
        try:
            clean, notes = await devices.update(body)
        except ValueError as e:
            return _err(T("settings: {error}", error=text_of(e)))
        except Exception as e:  # noqa: BLE001  (the message only: the traceback goes to the server log)
            log.warning("settings: %s", e)
            return _err(T("the engine did not check the settings (details in the server's log)"), 500)
        return _json({"settings": clean, "notes": notes})

    async def api_calibrate(request):
        try:
            s = await devices.calibrate()
        except Exception as e:  # noqa: BLE001
            log.warning("calibrate: %s", e)
            return _err(T("the measurement failed (details in the server's log)"), 500)
        return _json(s)

    # --- the removal period of runs (owner, 2026-10-29: set on the catalogue page, kept on the server) ------------
    async def api_runs_settings_get(request):
        return _json({"keep_days": mgr.keep_days})

    async def api_runs_settings_put(request):
        try:
            body = await _body(request)
        except NotJSON as e:
            return _err(e.args[0])
        if not isinstance(body, dict) or set(body) - {"keep_days", "confirm"}:
            return _err(T("an object {keep_days, confirm?} is needed"))
        try:
            res = mgr.set_keep_days(body.get("keep_days"), body.get("confirm") or [])
        except ValueError as e:
            return _err(text_of(e))
        if "would_remove" in res:
            return _err(T("a period of {n} days would remove runs at once: confirm", n=body["keep_days"]), 409, **res)
        if res["removed"]:
            log.info("removed by the new period of %s days: %s", res["keep_days"], res["removed"])
        return _json(res)

    async def settings_page(request):
        return web.FileResponse(PLAYER / "settings.html")

    async def legal_page(request):
        return web.FileResponse(PLAYER / "legal.html")

    async def worksheet_page(request):  # a lab's printable worksheet (design of 2026-11-14 §2.3; ?demo=…)
        f = PLAYER / "worksheet.html"
        return web.FileResponse(f) if f.is_file() else _err(T("there is no such file"), 404)

    async def legal_text(request):
        path = LEGAL.get(request.match_info["name"])
        if path is None or not path.is_file():
            return _err(T("there is no such text"), 404)
        return web.Response(text=path.read_text(encoding="utf-8"), content_type="text/plain", charset="utf-8")

    async def index(request):
        return web.FileResponse(PLAYER / "index.html")

    async def runs_page(request):
        return web.FileResponse(PLAYER / "runs.html")

    async def api_planned(request):
        return _json(planned_list())

    async def api_audiences(request):
        return _json(audiences_list())

    async def api_i18n(request):
        """The merged catalogue of a language (lfviz.i18n): {lang, messages}; cached until a catalogue file changes; an
        ETag (weak comparison), gzip when the client takes it (review i18n-code F9, F13). Also at
        /static/locales/<lang>.json, where a static copy of the player has the same file (lfviz.i18n.export)."""
        code = i18n.normalise(request.match_info["lang"])
        gz = "gzip" in request.headers.get("Accept-Encoding", "")
        try:
            body, etag = i18n.payload(code, gz=gz)
        except KeyError:
            return _err(i18n.T("No interface language {lang}; there are: {langs}", lang=request.match_info["lang"],
                               langs=", ".join(i18n.LANGS)), 404)
        headers = {"ETag": etag, "Vary": "Accept-Encoding"}
        if i18n.etag_matches(request.headers.get("If-None-Match"), etag):
            return web.Response(status=304, headers=headers)
        if gz:
            headers["Content-Encoding"] = "gzip"
        return web.Response(body=body, content_type="application/json", charset="utf-8", headers=headers)

    async def run_page(request):
        return web.FileResponse(PLAYER / "run.html")

    app.router.add_get("/", index)
    app.router.add_get("/run", run_page)
    app.router.add_get("/runs", runs_page)
    app.router.add_get("/settings", settings_page)
    app.router.add_get("/legal", legal_page)
    app.router.add_get("/worksheet", worksheet_page)
    app.router.add_get("/legal/{name}", legal_text)
    app.router.add_get("/api/devices", api_devices)
    app.router.add_get("/api/settings", api_settings_get)
    app.router.add_put("/api/settings", api_settings_put)
    app.router.add_post("/api/settings/calibrate", api_calibrate)
    app.router.add_get("/api/settings/runs", api_runs_settings_get)
    app.router.add_put("/api/settings/runs", api_runs_settings_put)
    app.router.add_get("/static/locales/{lang}.json", api_i18n)  # before /static/: the merged catalogue
    app.router.add_static("/static/", PLAYER, show_index=False)
    app.router.add_get("/viz/{viz}/{path:.+}", viz_file)
    app.router.add_get("/api/health", health)
    app.router.add_get("/api/i18n/{lang}", api_i18n)
    app.router.add_get("/api/viz", viz_list)
    app.router.add_get("/api/viz/{viz}", viz_one)
    app.router.add_get("/api/planned", api_planned)
    app.router.add_get("/api/audiences", api_audiences)
    app.router.add_get("/api/runs", runs_list)
    app.router.add_post("/api/runs", runs_start)
    app.router.add_get("/api/runs/{id}", run_meta)
    app.router.add_post("/api/runs/{id}/command", run_command)
    app.router.add_post("/api/runs/{id}/cancel", run_cancel)
    app.router.add_post("/api/runs/{id}/stop", run_stop)
    app.router.add_post("/api/runs/{id}/resume", run_resume)
    app.router.add_post("/api/runs/{id}/keep", run_keep)
    app.router.add_delete("/api/runs/{id}", run_delete)
    app.router.add_get("/api/runs/{id}/stream", run_stream)
    app.router.add_post("/api/runs/{id}/record", run_record)
    app.router.add_get("/ws/runs/{id}", ws_run)
    # [S] the recordings of the public site and the pictures (CONTRACT S/P): files served as they are; a recording is
    # gzip that the player inflates itself, so it goes as application/gzip without a Content-Encoding
    async def api_recordings(request):
        return _json(recordings_list())

    def _file_in(base: Path, *parts) -> Path | None:
        if not all(isinstance(p, str) and _REC_FILE.match(p) and p not in (".", "..") for p in parts):
            return None
        base = base.resolve()
        target = base.joinpath(*parts).resolve()
        return target if base in target.parents and target.is_file() else None

    async def recording_file(request):
        world = registry.resolve(request.match_info["world"])  # an old id (registry.ALIASES) names the new folder
        parts = request.match_info["file"].split("/")  # an atlas's files: atlas/<atlas>/<file> (design §1.3)
        f = _file_in(recordings_dir(), world, *parts) if len(parts) <= 3 else None
        if f is None:
            return _err(T("there is no such file"), 404)
        ctype = "application/json" if f.suffix == ".json" else (
            "application/gzip" if f.suffix == ".gz" else "application/octet-stream")
        return web.Response(body=f.read_bytes(), content_type=ctype, headers={"Access-Control-Allow-Origin": "*"})

    async def image_file(request):
        f = _file_in(IMAGES, request.match_info["file"])
        if f is None or f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            return _err(T("there is no such file"), 404)
        return web.FileResponse(f)

    app.router.add_get("/api/recordings", api_recordings)
    app.router.add_get("/recordings/{world}/{file:.+}", recording_file)
    app.router.add_get("/images/{file}", image_file)
    # [LB1 P16.3 instruments] the measurables' series and CSV, parameter sweeps (lfviz.instruments, lfviz.sweep)
    from . import instruments, sweep  # noqa: PLC0415
    instruments.add_routes(app, mgr)
    sweep.add_routes(app, mgr)
    # «compute live»: an atlas's point for any values (design of 2026-11-14 §3.7; lfviz.atlas_live)
    from . import atlas_live  # noqa: PLC0415
    atlas_live.add_routes(app, mgr)
    return app
