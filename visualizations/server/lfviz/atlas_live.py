# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""«Compute live»: an atlas's point computed on the server for any values (design
``lfphys/sources/explore_2026-11-14_design.md`` §3.7).

    POST /api/atlas/<world>/<atlas>/point  {values: {param: value}, seed?}  ->  200 application/gzip

The answer is the point's file, the same bytes a site build (``site/atlas.py``) makes for those values and that seed:
the world's own run (``lfviz.headless.run_spec``), packed against the screen's base header (the default point's). A
control left out takes its default; a parameter that is not a control of the atlas, or a value the schema refuses, is
``400 {error}``; a value the world refuses (``check_params``) is ``400 {error, hint}`` with the refusal's texts. The
response's headers say where the point came from: ``X-LF-Source`` = ``atlas`` (an on-grid value served from the local
atlas when its key is current), ``cache`` or ``computed``, and ``X-LF-Key`` (the point's key).

The computation runs in a separate process, the sweeps' pattern (``lfviz.sweep``): its own hard memory limit
(``RLIMIT_DATA``) from ``LFVIZ_POINT_MEM_GB`` (by default half a worker's budget, at least 512 MB), ``oom_score_adj``
1000 and ``nice`` 10, a CPU-time limit ``RLIMIT_CPU`` of ``LFVIZ_POINT_TIMEOUT_S`` (120 s by default) and, from the
server, a wall-clock limit of 1.5 × that + 10 s. A process that runs out of memory or time ends; the server answers
``503 {error}`` and goes on. One point is computed at a time per server; up to ``QUEUE`` requests wait, the next one is
``429``.

Cache: ``<runs>/atlas-live/<world>/<atlas>/<key16>.lfpt.gz`` (and the base header ``base-<key16>.lfpt.gz``), removed with
the runs' removal period. The key covers the atlas's key without its grid (``sitelib.atlas_key(grid=False)``: the spec,
the recorder's hash, the world's code hash), the values and the seed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from . import headless, limits, protocol, registry
from .i18n import T, json_hook, render_in

ENV_MEM = "LFVIZ_POINT_MEM_GB"
ENV_TIMEOUT = "LFVIZ_POINT_TIMEOUT_S"
QUEUE = 4  # requests that may wait while one point is computed
MIB = 2 ** 20


def timeout_s() -> float:
    try:
        v = float(os.environ.get(ENV_TIMEOUT, "") or 120.0)
    except ValueError:
        v = 120.0
    return v if v > 0 else 120.0


def point_mem(worker_mem: int) -> int:
    """A point process's memory budget: ``LFVIZ_POINT_MEM_GB`` when set, else half a worker's (at least 512 MB)."""
    try:
        gb = float(os.environ.get(ENV_MEM, "") or 0.0)
    except ValueError:
        gb = 0.0
    if gb > 0:
        return int(gb * limits.GIB)
    return int(max(512 * MIB, worker_mem // 2))


def _sitelib():
    """``visualizations/site/sitelib.py`` (the keys of the atlases; the folder is not a package)."""
    if "sitelib" not in sys.modules:
        site = str(registry.ROOT / "site")
        if site not in sys.path:
            sys.path.append(site)  # last: its scripts' names never shadow a module
    import sitelib  # noqa: PLC0415
    return sitelib


class Refused(Exception):
    """A request the server refuses: ``status`` and the body's texts."""

    def __init__(self, status: int, text, hint=None):
        self.status, self.text, self.hint = status, text, hint
        super().__init__(render_in(text))


def atlas_spec(world: str, atlas: str) -> tuple[dict, dict]:
    """(VIZ, the atlas's spec) or Refused 404."""
    try:
        viz = registry.load(registry.resolve(world))
    except KeyError:
        raise Refused(404, T("there is no such visualization")) from None
    spec = next((a for a in registry.atlases_of(viz) if a["id"] == atlas), None)
    if spec is None:
        raise Refused(404, T("this world has no atlas “{atlas}”", atlas=atlas))
    return viz, spec


def request_values(viz: dict, spec: dict, body) -> tuple[dict, int]:
    """The request's values over the controls' defaults, and its seed (Refused 400 for anything else)."""
    if not isinstance(body, dict) or not isinstance(body.get("values", {}), dict) or set(body) - {"values", "seed"}:
        raise Refused(400, T("the request body is an object {values, seed?}"))
    ctl = {c["param"]: c for c in spec["controls"]}
    extra = sorted(set(body.get("values") or {}) - set(ctl))
    if extra:
        raise Refused(400, T("not a control of this screen: {names}", names=", ".join(extra)))
    values = {p: c.get("default", c["values"][0]) for p, c in ctl.items()}
    values.update(body.get("values") or {})
    seed = body.get("seed", spec["seed"])
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2 ** 63:
        raise Refused(400, T("the seed is a whole number ≥ 0"))
    try:
        params = headless.resolve(viz, spec["preset"], {**spec["fixed"], **values})
    except ValueError as e:
        raise Refused(400, e.args[0] if e.args else T("the values are refused")) from None
    ref = headless.refusal(viz, params)
    if ref is not None:
        raise Refused(400, ref.text, ref.hint)
    # the values as the schema coerced them (a "1" is 1.0): the key and the run see the same numbers
    return {p: params[p] for p in values}, int(seed)


def point_key(base_key: str, values: dict, seed: int) -> str:
    text = json.dumps({"values": protocol.clean(values), "seed": seed}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{base_key}\n{text}".encode()).hexdigest()[:16]


def local_point(world: str, spec: dict, values: dict, seed: int, folder: Path, plan: dict) -> bytes | None:
    """The point's file from the local atlas (``visualizations/recordings``) when it is on the grid, with the atlas's
    seed, and the atlas's key is current."""
    if seed != spec["seed"]:
        return None
    idx = 0
    for c in spec["controls"]:
        v = values.get(c["param"])
        k = next((j for j, x in enumerate(c["values"]) if x == v), None)
        if k is None:
            return None
        idx = idx * len(c["values"]) + k
    try:
        index = json.loads((folder / world / "index.json").read_text(encoding="utf-8"))
        cur = next(a for a in plan["atlases"] if a["id"] == spec["id"])
        entry = next(a for a in index.get("atlases") or [] if a.get("id") == spec["id"])
        if entry.get("key") != cur["key"]:
            return None
        man = json.loads((folder / world / entry["file"]).read_text(encoding="utf-8"))
        name, size, state = man["points"][idx]
        if state or not name:
            return None
        data = (folder / world / entry["file"]).parent.joinpath(name).read_bytes()
        return data if len(data) == size else None
    except (OSError, ValueError, KeyError, StopIteration, IndexError, TypeError):
        return None


def read_packed(data: bytes) -> list[tuple[dict, dict]]:
    """The messages of a packed stream with their quantised blobs as ``protocol.Quantized`` (as the packer made them),
    so that a header compared with them gives the bytes a build gives."""
    out = []
    for meta, blobs in headless.read_stream(data, raw=True):
        q = {d["name"]: d.get("q") for d in meta.get("blobs") or []}
        out.append(({k: v for k, v in meta.items() if k != "blobs"},
                    {k: (protocol.Quantized(v, q[k]) if q.get(k) else v) for k, v in blobs.items()}))
    return out


# --- the process (python -m lfviz.atlas_live) ------------------------------------------------------------------------
def _lower_priority():
    try:
        os.nice(10)
    except OSError:
        pass
    try:
        with open("/proc/self/oom_score_adj", "w") as f:
            f.write("1000")
    except OSError:
        pass


def compute(world: str, atlas: str, values: dict, seed: int, base_file: Path) -> bytes:
    """The point's file, computed (the base header taken from ``base_file`` or computed and written there)."""
    _sitelib()
    import atlas as A  # noqa: PLC0415 - site/atlas.py: the very packing of a build
    viz, spec = atlas_spec(world, atlas)
    dflt = A.defaults(spec)
    base = None
    if base_file.is_file():
        try:
            base = read_packed(base_file.read_bytes())[0]
        except (OSError, ValueError, IndexError):
            base = None
    msgs = None
    if base is None:
        msgs0, _oc = A.run_point(world, spec, dflt, log=lambda *a: None)
        base = A.base_header(spec, msgs0)
        tmp = base_file.with_suffix(".tmp")
        tmp.write_bytes(A.pack_base_file(base))
        os.replace(tmp, base_file)
        if values == dflt and seed == spec["seed"]:
            msgs = msgs0
    if msgs is None:
        msgs, _oc = A.run_point(world, spec, values, seed, log=lambda *a: None)
    data, _pk = A.pack_point(spec, msgs, base)
    return data


def main(argv=None) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="Compute one atlas point live (spawned by the server; design §3.7).")
    ap.add_argument("--world", required=True)
    ap.add_argument("--atlas", required=True)
    ap.add_argument("--values", required=True, help="the values as JSON")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--base", required=True, help="the base header's cache file")
    ap.add_argument("--out", required=True, help="the point's file; <out>.json gets a failure")
    a = ap.parse_args(argv)
    limits.apply_hard_limit()  # before anything large is allocated (RULES.md §3, «Memory budget»)
    try:
        import resource  # noqa: PLC0415
        cpu = int(max(1, timeout_s()))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
    except (ImportError, ValueError, OSError):
        pass
    _lower_priority()
    registry.ensure_path()
    out = Path(a.out)
    try:
        data = compute(a.world, a.atlas, json.loads(a.values), a.seed, Path(a.base))
    except headless.PointRefused as e:
        out.with_suffix(".json").write_text(json.dumps(protocol.clean({"refused": {"text": e.text, "hint": e.hint}})))
        return 3
    except MemoryError:
        out.with_suffix(".json").write_text(json.dumps({"error": "memory"}))
        return 4
    except Exception as e:  # noqa: BLE001 - reported to the server, which answers the request
        if isinstance(e.__context__, MemoryError) or isinstance(e.__cause__, MemoryError):  # the world's MemoryError
            out.with_suffix(".json").write_text(json.dumps({"error": "memory"}))
            return 4
        out.with_suffix(".json").write_text(json.dumps({"error": f"{type(e).__name__}: {e}"[:2000]}))
        return 1
    tmp = out.with_suffix(".part")
    tmp.write_bytes(data)
    os.replace(tmp, out)
    return 0


# --- the server's side -----------------------------------------------------------------------------------------------
class LivePoints:
    """The live points of one server: one computed at a time, ``QUEUE`` waiting; the cache under the runs' folder."""

    def __init__(self, runs_dir: Path, worker_mem: int, keep_days=lambda: 3.0):
        self.root = Path(runs_dir) / "atlas-live"
        self.worker_mem = int(worker_mem)
        self.keep_days = keep_days
        self.lock = asyncio.Lock()
        self.waiting = 0
        self.procs: set = set()

    def _cleanup(self):
        """Remove the cached points older than the runs' removal period."""
        try:
            limit = time.time() - float(self.keep_days()) * 86400.0
        except (TypeError, ValueError):
            return
        for f in self.root.rglob("*.lfpt.gz") if self.root.is_dir() else []:
            try:
                if f.stat().st_mtime < limit:
                    f.unlink()
            except OSError:
                pass

    async def point(self, world: str, atlas: str, body) -> tuple[bytes, dict]:
        """(the point's file, headers) or Refused."""
        world = registry.resolve(world)
        viz, spec = atlas_spec(world, atlas)
        values, seed = request_values(viz, spec, body)
        L = _sitelib()
        code = registry.code_hash_cached(world)
        base_key = L.atlas_key(spec, code, grid=False)
        key = point_key(base_key, values, seed)
        folder = self.root / world / atlas
        f = folder / f"{key}.lfpt.gz"
        if f.is_file():
            return f.read_bytes(), {"X-LF-Source": "cache", "X-LF-Key": key}
        from .app import recordings_dir  # noqa: PLC0415
        plan = {"atlases": [{"id": spec["id"], "key": L.atlas_key(spec, code)}]}
        data = local_point(world, spec, values, seed, recordings_dir(), plan)
        if data is not None:
            return data, {"X-LF-Source": "atlas", "X-LF-Key": key}
        if self.waiting >= QUEUE + 1:  # the one computed and QUEUE waiting
            raise Refused(429, T("the server computes other points now; try again in a moment"))
        self.waiting += 1
        try:
            async with self.lock:
                if f.is_file():  # computed while this request waited
                    return f.read_bytes(), {"X-LF-Source": "cache", "X-LF-Key": key}
                folder.mkdir(parents=True, exist_ok=True)
                data = await self._spawn(world, atlas, values, seed, folder / f"base-{base_key}.lfpt.gz", f)
        finally:
            self.waiting -= 1
        self._cleanup()
        return data, {"X-LF-Source": "computed", "X-LF-Key": key}

    async def _spawn(self, world, atlas, values, seed, base: Path, out: Path) -> bytes:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(registry.SERVER), str(registry.ROOT), str(registry.ENGINE)])
        env.setdefault("OMP_NUM_THREADS", "2")
        env.setdefault("OPENBLAS_NUM_THREADS", "2")
        env[limits.ENV] = str(point_mem(self.worker_mem))
        env["LFPHYS_NO_GPU"] = "1"  # GPU 0 belongs to the live worlds
        fail = out.with_suffix(".json")
        for p in (fail, out):
            p.unlink(missing_ok=True)
        log = open(out.parent / "point.log", "ab")
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "lfviz.atlas_live", "--world", world, "--atlas", atlas,
                "--values", json.dumps(protocol.clean(values)), "--seed", str(seed), "--base", str(base),
                "--out", str(out), stdin=asyncio.subprocess.DEVNULL, stdout=log, stderr=log, env=env,
                cwd=str(registry.ROOT))
        finally:
            log.close()
        self.procs.add(proc)
        try:
            await asyncio.wait_for(proc.wait(), timeout=1.5 * timeout_s() + 10.0)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
        finally:
            self.procs.discard(proc)
        if proc.returncode == 0 and out.is_file():
            return out.read_bytes()
        info = {}
        try:
            info = json.loads(fail.read_text(), object_hook=json_hook)
            fail.unlink()
        except (OSError, ValueError):
            pass
        if proc.returncode == 3 and info.get("refused"):
            raise Refused(400, info["refused"]["text"], info["refused"].get("hint"))
        if proc.returncode == 4 or info.get("error") == "memory":
            raise Refused(503, T("the point needs more memory than a live point is given ({budget}): it was not "
                                 "computed", budget=limits.fmt_bytes(point_mem(self.worker_mem))))
        if proc.returncode is not None and proc.returncode < 0 or not info:
            raise Refused(503, T("the point's computation was ended: it took longer than {s:.0f} s or more memory "
                                 "than it is given", s=timeout_s()))
        raise Refused(500, T("the point was not computed: {error}", error=str(info.get("error"))))

    async def shutdown(self):
        for p in list(self.procs):
            try:
                p.kill()
            except ProcessLookupError:
                pass


def add_routes(app, mgr):
    from aiohttp import web  # noqa: PLC0415
    from .app import _err  # noqa: PLC0415

    live = LivePoints(mgr.dir, mgr.worker_mem, lambda: mgr.keep_days)

    async def post_point(request):
        try:
            body = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _err(T("the request body is not JSON"))
        try:
            data, headers = await live.point(request.match_info["world"], request.match_info["atlas"], body)
        except Refused as e:
            extra = {"hint": e.hint} if e.hint is not None else {}
            return _err(e.text, e.status, **extra)
        return web.Response(body=data, content_type="application/gzip", headers=headers)

    async def on_cleanup(app):
        await live.shutdown()

    app.on_cleanup.append(on_cleanup)
    app.router.add_post("/api/atlas/{world}/{atlas}/point", post_point)
    return live


if __name__ == "__main__":
    sys.exit(main())
