# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""HTTP + WebSocket API of the visualization server (the one API for the whole project).

REST (JSON):
    GET    /api/health                     server version, counts
    GET    /api/viz                        catalogue: [{id, title, summary, purpose, version, schema}]
    GET    /api/viz/{viz}                  one entry
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
    GET    /api/settings/runs              {keep_days}: runs without actions for this many days are removed
    PUT    /api/settings/runs              {keep_days, confirm?: [id]} -> saved and applied at once; 409 with
                                           {would_remove: [id]} if it would remove runs not all in ``confirm``

WebSocket:
    /ws/runs/{id}    server -> browser: binary messages (protocol.py): the record so far, "history_end", live tail
                     browser -> server: text JSON {cmd, args} (play, pause, speed, step, next_event, action)

The server's own worker commands (``SERVER_ONLY``: ``checkpoint_now``, which the sweeps send, and ``stop``) are refused
on the client routes, REST and WebSocket (review LB1-framework F6: any page on the LAN could make a playing world pickle
itself and start a record segment 10 times a second, with any data in the record as its tag).

Pages: ``/`` (catalogue and runs), ``/run?id=<id>`` (player), ``/legal`` (the licences, the third-party notices and the
disclaimer; their full texts at ``/legal/<name>``); static files under ``/static/``; the browser module of a
visualization under ``/viz/<id>/`` (its ``web/`` folder).
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from aiohttp import WSMsgType, web

from . import __version__, devices, registry
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
        raise ValueError("команда — объект {cmd, args}")
    if body["cmd"] in SERVER_ONLY:
        raise PermissionError(f"команду «{body['cmd']}» посылает только сам сервер")
    if body.get("args") is not None and not isinstance(body["args"], dict):
        raise ValueError("«args» команды — объект")
    return body


def _json(data, status=200):
    return web.json_response(data, status=status, dumps=lambda d: json.dumps(d, ensure_ascii=False))


def _err(text, status=400):
    return _json({"error": text}, status)


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
                out.append({"id": vid, "title": vid, "error": f"{type(e).__name__}: {e}",
                            "kind": "playground" if vid.startswith("p") else "demo"})  # under its mode (B6-F24)
        return _json(out)

    async def viz_one(request):
        try:
            return _json(registry.describe(mgr.viz(request.match_info["viz"])))
        except KeyError:
            return _err("нет такой визуализации", 404)

    async def viz_file(request):
        vid = request.match_info["viz"]
        if vid not in registry.viz_ids():
            return _err("нет такой визуализации", 404)
        try:
            base = (registry.folder(vid) / "web").resolve()
        except KeyError:
            return _err("нет такой визуализации", 404)
        target = (base / request.match_info["path"]).resolve()
        if base not in target.parents or not target.is_file():
            return _err("нет файла", 404)
        return web.FileResponse(target)

    async def runs_list(request):
        return _json(mgr.list())

    async def runs_start(request):
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _err("тело запроса не JSON")
        if not isinstance(body, dict):
            return _err("тело запроса — объект JSON")
        vid = body.get("viz")
        if vid not in registry.viz_ids():
            return _err("нет такой визуализации", 404)
        try:  # devices and precision for this run: the settings file, with the start form's overrides (plan P11)
            bset, bnotes = await devices.for_run(body.get("backend"))
        except ValueError as e:
            return _err(f"устройства: {e}", 400)
        except Exception as e:  # noqa: BLE001
            log.warning("run devices: %s", e)
            return _err("движок не проверил выбор устройств (подробности — в журнале сервера)", 500)
        seed = body.get("seed")
        try:
            seed = None if seed in (None, "") else int(seed)
            run = await mgr.start(vid, body.get("preset"), body.get("params"), seed,
                                  label=str(body.get("label", ""))[:200], source=request.remote or "",
                                  backend=bset, backend_notes=bnotes)
        except OverflowError as e:
            return _err(str(e), 409)
        except ValueError as e:  # refused parameters (by their labels: review UX-ui U13, UX-params P2) or a refused
            # combination / memory estimate of the world (P1, P8): the catalogue shows it on the form, by field
            from .errors import owner_text
            fields = getattr(e, "fields", None) or {}
            return _json({"error": owner_text(e)[0] if not fields else str(e), "fields": fields}, 400)
        return _json({"id": run.id})

    def _run(request):
        return mgr.get(request.match_info["id"])

    async def run_meta(request):
        try:
            r = _run(request)
        except KeyError:
            return _err("нет такого запуска", 404)
        out = dict(r.meta)
        out.update(r.summary())
        return _json(out)

    async def run_command(request):
        try:
            r = _run(request)
            body = client_command(await request.json())
            await r.command_resuming(body, request.remote or "")
        except KeyError:
            return _err("нет такого запуска", 404)
        except PermissionError as e:  # [LB1 F6]
            return _err(str(e), 403)
        except (RuntimeError, OverflowError) as e:
            return _err(str(e), 409)
        except ValueError as e:  # not JSON, or not a command [LB1 F6]
            return _err("тело запроса не JSON" if isinstance(e, (json.JSONDecodeError, UnicodeDecodeError)) else str(e))
        return _json({"ok": True})

    async def run_cancel(request):
        """Cancel what the worker is computing now (review UX-ui U9): the world goes back to just before it."""
        try:
            r = _run(request)
            res = await r.cancel(request.remote or "")
        except KeyError:
            return _err("нет такого запуска", 404)
        except (RuntimeError, OverflowError) as e:
            return _err(str(e), 409)
        return _json(res)

    async def run_stop(request):
        """Release the run's worker (it is resumed when asked to compute again); kept for scripts, the player has no
        stop (owner, 2026-10-28)."""
        try:
            r = _run(request)
        except KeyError:
            return _err("нет такого запуска", 404)
        await r.suspend("user")
        return _json({"ok": True, "state": r.meta.get("state")})

    async def run_resume(request):
        try:
            r = _run(request)
            await mgr.resume(r)
        except KeyError:
            return _err("нет такого запуска", 404)
        except (RuntimeError, OverflowError) as e:
            return _err(str(e), 409)
        return _json({"ok": True})

    async def run_keep(request):
        try:
            r = _run(request)
            body = await request.json()
        except KeyError:
            return _err("нет такого запуска", 404)
        r.meta["keep"] = bool(body.get("keep", True))
        r.save_meta()
        return _json({"ok": True, "keep": r.meta["keep"]})

    async def run_delete(request):
        try:
            await mgr.delete(request.match_info["id"])
        except KeyError:
            return _err("нет такого запуска", 404)
        except RuntimeError as e:
            return _err(str(e), 409)
        return _json({"ok": True})

    async def run_stream(request):
        try:
            r = _run(request)
        except KeyError:
            return _err("нет такого запуска", 404)
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
            body = await request.json()
            # validated (review B6-F12): an object; "on" a JSON boolean, unchanged when absent; the window numbers
            if not isinstance(body, dict):
                raise ValueError("тело запроса — объект JSON")
            on = body.get("on")
            if on is not None and not isinstance(on, bool):
                raise ValueError("«on» — true или false")
            for k in ("window_s", "window_mb"):
                v = body.get(k)
                if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
                    raise ValueError(f"«{k}» — число")
            return _json(r.set_recording(on, body.get("window_s"), body.get("window_mb")))
        except KeyError:
            return _err("нет такого запуска", 404)
        except json.JSONDecodeError:
            return _err("тело запроса не JSON")
        except ValueError as e:
            return _err(str(e), 400)
        except RuntimeError as e:
            return _err(str(e), 409)

    async def ws_run(request):
        try:
            r = _run(request)
        except KeyError:
            return _err("нет такого запуска", 404)
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
                        await ws.send_str(json.dumps({"error": str(e)}, ensure_ascii=False))
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
            return _err(f"движок не сообщил устройства: {e}", 500)
        return _json({**info, "settings": devices.load()})

    async def api_settings_get(request):
        return _json(devices.load())

    async def api_settings_put(request):
        if (request.content_length or 0) > devices.MAX_BYTES:
            return _err(f"настройки длиннее {devices.MAX_BYTES // 1024} КБ", 413)
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _err("тело запроса не JSON")
        try:
            clean, notes = await devices.update(body)
        except ValueError as e:
            return _err(f"настройки: {e}")
        except Exception as e:  # noqa: BLE001  (the message only: the traceback goes to the server log)
            log.warning("settings: %s", e)
            return _err("движок не проверил настройки (подробности — в журнале сервера)", 500)
        return _json({"settings": clean, "notes": notes})

    async def api_calibrate(request):
        try:
            s = await devices.calibrate()
        except Exception as e:  # noqa: BLE001
            log.warning("calibrate: %s", e)
            return _err("замер не удался (подробности — в журнале сервера)", 500)
        return _json(s)

    # --- the removal period of runs (owner, 2026-10-29: set on the catalogue page, kept on the server) ------------
    async def api_runs_settings_get(request):
        return _json({"keep_days": mgr.keep_days})

    async def api_runs_settings_put(request):
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return _err("тело запроса не JSON")
        if not isinstance(body, dict) or set(body) - {"keep_days", "confirm"}:
            return _err("нужен объект {keep_days, confirm?}")
        try:
            res = mgr.set_keep_days(body.get("keep_days"), body.get("confirm") or [])
        except ValueError as e:
            return _err(str(e))
        if "would_remove" in res:
            return _json({**res, "error": f"срок {body['keep_days']} дн. сразу удалит запуски: подтвердите"}, 409)
        if res["removed"]:
            log.info("removed by the new period of %s days: %s", res["keep_days"], res["removed"])
        return _json(res)

    async def settings_page(request):
        return web.FileResponse(PLAYER / "settings.html")

    async def legal_page(request):
        return web.FileResponse(PLAYER / "legal.html")

    async def legal_text(request):
        path = LEGAL.get(request.match_info["name"])
        if path is None or not path.is_file():
            return _err("нет такого текста", 404)
        return web.Response(text=path.read_text(encoding="utf-8"), content_type="text/plain", charset="utf-8")

    async def index(request):
        return web.FileResponse(PLAYER / "index.html")

    async def run_page(request):
        return web.FileResponse(PLAYER / "run.html")

    app.router.add_get("/", index)
    app.router.add_get("/run", run_page)
    app.router.add_get("/settings", settings_page)
    app.router.add_get("/legal", legal_page)
    app.router.add_get("/legal/{name}", legal_text)
    app.router.add_get("/api/devices", api_devices)
    app.router.add_get("/api/settings", api_settings_get)
    app.router.add_put("/api/settings", api_settings_put)
    app.router.add_post("/api/settings/calibrate", api_calibrate)
    app.router.add_get("/api/settings/runs", api_runs_settings_get)
    app.router.add_put("/api/settings/runs", api_runs_settings_put)
    app.router.add_static("/static/", PLAYER, show_index=False)
    app.router.add_get("/viz/{viz}/{path:.+}", viz_file)
    app.router.add_get("/api/health", health)
    app.router.add_get("/api/viz", viz_list)
    app.router.add_get("/api/viz/{viz}", viz_one)
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
    # [LB1 P16.3 instruments] the measurables' series and CSV, parameter sweeps (lfviz.instruments, lfviz.sweep)
    from . import instruments, sweep  # noqa: PLC0415
    instruments.add_routes(app, mgr)
    sweep.add_routes(app, mgr)
    return app
