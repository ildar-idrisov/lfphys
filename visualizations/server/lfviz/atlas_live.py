# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""«Compute live»: an atlas's point computed on the server for any values (design
``lfphys/sources/explore_2026-11-14_design.md`` §3.7).

    POST /api/atlas/<world>/<atlas>/point  {values: {param: value}, seed?, full_header?}  ->  200 application/gzip

The answer is the point's file: the world's own run (``lfviz.headless.run_spec``), packed as a site build
(``site/atlas.py``) packs it for those values and that seed, its header a delta against the screen's base header (the
default point's) that names its base (``$base``: the sha256 of the base file, as a manifest's ``base.sha256``). On the
same CPU type as the site's build, an on-grid point is the same bytes (numpy's SIMD paths can change the last bits of a
world's computed values; review R-F F8). With ``full_header: true`` the same point comes with a full header (no
``$delta``, ``$base`` or ``$drop``): what a player asks for when its own base is another (integrator D13).

A control left out takes its default; a parameter that is not a control of the atlas, a value outside the control's span
(a slider's lowest to highest value, a toggle's or a select's own values), a compound control's value off its grid (it
sets several parameters at once: EX2 §5 F3) or one the schema refuses is ``400 {error}``; a value the world refuses
(``check_params``, its memory estimate, its constructor) is ``400 {error, hint}`` with the refusal's texts; a point
whose checks end ✗ is ``409 {error}`` naming the checks (integrator D14). The response's headers say where the point
came from and what made it: ``X-LF-Source`` = ``atlas`` (an on-grid value served from the local atlas when its key is
current), ``cache`` or ``computed``; ``X-LF-Key`` (the point's key); ``X-LF-Code`` (the world's code hash that computed
it); ``X-LF-Made`` (when it was computed, ISO 8601 in UTC: a cached point's original time, an atlas's build time).

The computation runs in a separate process, the sweeps' pattern (``lfviz.sweep``): its own hard memory limit
(``RLIMIT_DATA``) from ``LFVIZ_POINT_MEM_GB`` (by default half a worker's budget, at least 512 MB), ``oom_score_adj``
1000 and ``nice`` 10, a CPU-time limit ``RLIMIT_CPU`` of ``LFVIZ_POINT_TIMEOUT_S`` (120 s by default) and, from the
server, a wall-clock limit of 1.5 × that + 10 s. A process that runs out of memory or time ends; the server answers
``503 {error}`` and goes on. One point is computed at a time per server; up to ``QUEUE`` requests wait, the next one is
``429``.

Cache: ``<runs>/atlas-live/<world>/<atlas>/<key16>.lfpt.gz`` (and the base header ``base-<key16>.lfpt.gz``), removed with
the runs' removal period, at most ``LFVIZ_POINT_CACHE_MB`` (512 MB) in all, the oldest first. The key covers the atlas's
key without its grid (``sitelib.atlas_key(grid=False)``: the spec, the recorder's hash, the world's code hash), this
module's own hash (``SERVER_ONLY`` in the registry: it is not in the code hash), the values and the seed. The code hash
is the code on disk as the request comes (``registry.code_hash_current``, checked by the files' times); the point's
process hashes the code itself, before and after it computes, and the point is cached under the key of the code it ran,
never under another's: a point computed while the code changed is not kept and is ``503`` (review R-F F1).
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import gzip
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from . import headless, limits, protocol, registry
from .i18n import T, join, json_hook, render_in

ENV_MEM = "LFVIZ_POINT_MEM_GB"
ENV_TIMEOUT = "LFVIZ_POINT_TIMEOUT_S"
ENV_CACHE = "LFVIZ_POINT_CACHE_MB"
QUEUE = 4  # requests that may wait while one point is computed
MIB = 2 ** 20
LEFTOVER_S = 600.0  # a temporary file of the cache older than this is a killed process's leftover
EXIT_REFUSED, EXIT_MEMORY, EXIT_CHECKS = 3, 4, 5  # the point process's exit codes besides 0 and 1


def timeout_s() -> float:
    try:
        v = float(os.environ.get(ENV_TIMEOUT, "") or 120.0)
    except ValueError:
        v = 120.0
    return v if v > 0 else 120.0


def cache_cap() -> int:
    """The live points' cache's largest size in bytes: ``LFVIZ_POINT_CACHE_MB`` (512 MB by default)."""
    try:
        mb = float(os.environ.get(ENV_CACHE, "") or 512.0)
    except ValueError:
        mb = 512.0
    return int((mb if mb > 0 else 512.0) * 1e6)


def live_hash() -> str:
    """This module's own hash (12 hex digits): part of a live point's key, as the module is not in the code hash."""
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    except OSError:
        return "missing"


def _iso(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).isoformat(timespec="seconds")


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


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def request_values(viz: dict, spec: dict, body) -> tuple[dict, int, bool]:
    """The request's values over the controls' defaults, its seed and whether it asks for a full header (Refused 400
    for anything else: a value outside a control's span too, review R-F F4)."""
    if not isinstance(body, dict) or not isinstance(body.get("values", {}), dict) \
            or set(body) - {"values", "seed", "full_header"}:
        raise Refused(400, T("the request body is an object {values, seed?, full_header?}"))
    full = body.get("full_header", False)
    if not isinstance(full, bool):
        raise Refused(400, T("“full_header” is true or false"))
    ctl = {c["param"]: c for c in spec["controls"]}
    extra = sorted(set(body.get("values") or {}) - set(ctl))
    if extra:
        raise Refused(400, T("not a control of this screen: {names}", names=", ".join(extra)))
    values = {p: c.get("default", c["values"][0]) for p, c in ctl.items()}
    values.update(body.get("values") or {})
    seed = body.get("seed", spec["seed"])
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2 ** 63:
        raise Refused(400, T("the seed is a whole number ≥ 0"))
    for p, c in ctl.items():  # a compound control takes its grid values only (EX2 §5 F3): it sets several parameters
        if c.get("sets") is None:
            continue
        v = values[p]
        k = next((j for j, x in enumerate(c["values"]) if type(x) is type(v) and x == v), None)
        if k is None and not isinstance(v, bool):
            k = next((j for j, x in enumerate(c["values"]) if not isinstance(x, bool) and x == v), None)
        if k is None:
            raise Refused(400, T("“{label}” sets several parameters at once: it takes only its own values",
                                 label=c.get("label") or p))
        values[p] = c["values"][k]  # the grid's own value (0 and 0.0 are one point)
    try:
        params = headless.resolve(viz, spec["preset"], {**spec["fixed"], **registry.expand_values(spec["controls"],
                                                                                                  values)})
    except ValueError as e:
        raise Refused(400, e.args[0] if e.args else T("the values are refused")) from None
    for p, c in ctl.items():  # within the screen's span: a slider between its ends, a toggle or a select its values
        if c.get("sets") is not None:
            continue
        v, vals = params[p], c["values"]
        if all(_is_num(x) for x in vals) and _is_num(v):
            if not min(vals) <= v <= max(vals):
                raise Refused(400, T("“{label}” = {value:.6g} is outside this screen's range {lo:.6g} … {hi:.6g}",
                                     label=c.get("label") or p, value=v, lo=min(vals), hi=max(vals)))
        elif not any(type(x) is type(v) and x == v for x in vals):
            raise Refused(400, T("“{label}”: this screen offers only its own values", label=c.get("label") or p))
    ref = headless.refusal(viz, params)
    if ref is not None:
        raise Refused(400, ref.text, ref.hint)
    # the values as the schema coerced them (a "1" is 1.0): the key and the run see the same numbers; a compound
    # control's value is its grid value
    return {p: (values[p] if ctl[p].get("sets") is not None else params[p]) for p in values}, int(seed), full


def point_key(base_key: str, values: dict, seed: int, live: str | None = None) -> str:
    """A live point's key: the atlas's key without its grid, this module's hash (``live_hash``), the values, the
    seed."""
    text = json.dumps({"values": protocol.clean(values), "seed": seed}, sort_keys=True, separators=(",", ":"))
    live = live_hash() if live is None else live
    return hashlib.sha256(f"{base_key}\n{live}\n{text}".encode()).hexdigest()[:16]


def local_point(world: str, spec: dict, values: dict, seed: int, folder: Path, atlas_key: str) -> dict | None:
    """The point from the local atlas (``visualizations/recordings``) when it is on the grid, with the atlas's seed, and
    the atlas's key is ``atlas_key`` (the current one): ``{data, base, made}`` (the point's file, its base file's bytes,
    the atlas's build time), or None."""
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
        entry = next(a for a in index.get("atlases") or [] if a.get("id") == spec["id"])
        if entry.get("key") != atlas_key:
            return None
        mf = folder / world / entry["file"]
        man = json.loads(mf.read_text(encoding="utf-8"))
        if man.get("key") != atlas_key:
            return None
        name, size, state = man["points"][idx]
        if state or not name:
            return None
        data = mf.parent.joinpath(name).read_bytes()
        base = mf.parent.joinpath(man["base"]["file"]).read_bytes()
        # the point's name carries the first 8 hex digits of its sha256 (``p<i>.<hash8>.lfpt.gz``): a point of the same
        # size but other bytes is not served (review R2-F F9: its size alone was checked; the base and the pool by sha256)
        hash8 = name.rsplit(".lfpt.gz", 1)[0].rsplit(".", 1)[-1]
        if len(data) != size or hashlib.sha256(data).hexdigest()[:8] != hash8 \
                or hashlib.sha256(base).hexdigest() != man["base"]["sha256"]:
            return None
        if man.get("pool"):  # a live point is never pooled (EX2 §5 F10): its pooled blobs put back
            pool = mf.parent.joinpath(man["pool"]["file"]).read_bytes()
            if hashlib.sha256(pool).hexdigest() != man["pool"]["sha256"]:
                return None
            data = headless.unpool(data, pool)
        return {"data": data, "base": base, "made": entry.get("made") or _iso(mf.stat().st_mtime)}
    except (OSError, ValueError, KeyError, StopIteration, IndexError, TypeError):
        return None


def _packed(meta: dict, blobs: dict) -> tuple[dict, dict]:
    q = {d["name"]: d.get("q") for d in meta.get("blobs") or []}
    return ({k: v for k, v in meta.items() if k != "blobs"},
            {k: (protocol.Quantized(v, q[k]) if q.get(k) else v) for k, v in blobs.items()})


def read_packed(data: bytes) -> list[tuple[dict, dict]]:
    """The messages of a packed stream with their quantised blobs as ``protocol.Quantized`` (as the packer made them),
    so that a header compared with them gives the bytes a build gives."""
    return [_packed(meta, blobs) for meta, blobs in headless.read_stream(data, raw=True)]


def with_full_header(data: bytes, base_data: bytes) -> bytes:
    """A packed point's file with its header merged with its base (``base_data``, the base file): a full header with no
    ``$``-keys, the rest of the stream byte for byte (``full_header: true``; integrator D13)."""
    raw = gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data
    items = [m for _o, m in protocol.iter_stream(raw, len(protocol.MAGIC))]
    head = _packed(*protocol.decode(items[0], raw=True))
    if not head[0].get("$delta"):
        return data
    base = read_packed(base_data)[0]
    meta, blobs = headless.merge_header(base, head)
    return headless.gz(headless.stream([protocol.encode(meta, blobs)] + items[1:]))


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


def _code_signature(world: str, L) -> tuple[str, str, str]:
    """(the world's code hash, the recorder's hash, this module's hash) of the files as they are now."""
    return registry.code_hash(world), L.recorder_hash(), live_hash()


def compute(world: str, atlas: str, values: dict, seed: int, folder: Path) -> tuple[bytes, dict]:
    """The point's file, computed by the code on disk, and its report ``{key, base_key, code_hash, stable}``: the keys of
    the code this process hashed before it computed; ``stable`` when the code was the same after (else nothing is
    kept). The base header is read from ``folder/base-<base_key>.lfpt.gz``, or computed and written there (when
    stable)."""
    L = _sitelib()
    import atlas as A  # noqa: PLC0415 - site/atlas.py: the very packing of a build
    viz, spec = atlas_spec(world, atlas)
    sig0 = _code_signature(world, L)
    base_key = L.atlas_key(spec, sig0[0], sig0[1], grid=False)
    key = point_key(base_key, values, seed, sig0[2])
    base_file = folder / f"base-{base_key}.lfpt.gz"
    dflt = A.defaults(spec)
    base, base_gz, new_base = None, None, False
    if base_file.is_file():
        try:
            base_gz = base_file.read_bytes()
            base = read_packed(base_gz)[0]
        except (OSError, ValueError, IndexError):
            base, base_gz = None, None
    msgs = None
    if base is None:
        msgs0, _oc = A.run_point(world, spec, dflt, log=lambda *a: None)
        base = A.base_header(spec, msgs0)
        base_gz, new_base = A.pack_base_file(base), True
        if values == dflt and seed == spec["seed"]:
            msgs = msgs0
    if msgs is None:
        msgs, _oc = A.run_point(world, spec, values, seed, log=lambda *a: None)
    data, _pk = A.pack_point(spec, msgs, base, hashlib.sha256(base_gz).hexdigest())
    stable = _code_signature(world, L) == sig0
    if stable and new_base:
        tmp = base_file.with_name(base_file.name + ".tmp")
        tmp.write_bytes(base_gz)
        os.replace(tmp, base_file)
    elif stable:
        try:
            os.utime(base_file)  # in use: the cache's housekeeping keeps it as long as its points
        except OSError:
            pass
    return data, {"key": key, "base_key": base_key, "code_hash": sig0[0], "stable": stable}


def main(argv=None) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="Compute one atlas point live (spawned by the server; design §3.7).")
    ap.add_argument("--world", required=True)
    ap.add_argument("--atlas", required=True)
    ap.add_argument("--values", required=True, help="the values as JSON")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--folder", required=True, help="the cache's folder of the atlas (the base header's file)")
    ap.add_argument("--out", required=True, help="the point's file; <out>.json gets the report or a failure")
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
    report = out.with_name(out.name + ".json")

    def say(obj):
        report.write_text(json.dumps(protocol.clean(obj), ensure_ascii=False))

    try:
        data, rep = compute(a.world, a.atlas, json.loads(a.values), a.seed, Path(a.folder))
    except headless.PointRefused as e:
        say({"refused": {"text": e.text, "hint": e.hint}})
        return EXIT_REFUSED
    except MemoryError:
        say({"error": "memory"})
        return EXIT_MEMORY
    except Exception as e:  # noqa: BLE001 - reported to the server, which answers the request
        if isinstance(e.__context__, MemoryError) or isinstance(e.__cause__, MemoryError):  # the world's MemoryError
            say({"error": "memory"})
            return EXIT_MEMORY
        if isinstance(e, headless.RunFailed) and e.checks:  # the world's checks end ✗ at these values (D14)
            say({"checks": e.checks, "error": str(e)[:2000]})
            return EXIT_CHECKS
        say({"error": f"{type(e).__name__}: {e}"[:2000]})
        return 1
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, out)
    say(rep)
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
        """The cache's housekeeping (review R-F F13): the points and bases older than the runs' removal period, the
        leftovers of a killed process (``*.part``, ``*.tmp``, ``*.json``) older than ``LEFTOVER_S``, then the oldest
        files while the cache is over ``cache_cap``."""
        if not self.root.is_dir():
            return
        now = time.time()
        try:
            limit = now - float(self.keep_days()) * 86400.0
        except (TypeError, ValueError):
            limit = None
        kept = []
        for f in self.root.rglob("*"):
            try:
                if not f.is_file():
                    continue
                st = f.stat()
                if f.name.endswith(".lfpt.gz"):
                    if limit is not None and st.st_mtime < limit:
                        f.unlink()
                    else:
                        kept.append((st.st_mtime, st.st_size, f))
                elif f.name != "point.log" and st.st_mtime < now - LEFTOVER_S:
                    f.unlink()
            except OSError:
                pass
        total, cap = sum(n for _t, n, _f in kept), cache_cap()
        for _t, n, f in sorted(kept, key=lambda x: x[0]):
            if total <= cap:
                break
            try:
                f.unlink()
                total -= n
            except OSError:
                pass

    async def point(self, world: str, atlas: str, body) -> tuple[bytes, dict]:
        """(the point's file, headers) or Refused."""
        world = registry.resolve(world)
        viz, spec = atlas_spec(world, atlas)
        values, seed, full = request_values(viz, spec, body)
        L = _sitelib()
        code, rh = registry.code_hash_current(world), L.recorder_hash()
        base_key = L.atlas_key(spec, code, rh, grid=False)
        key = point_key(base_key, values, seed)
        folder = self.root / world / atlas
        f = folder / f"{key}.lfpt.gz"
        base_f = folder / f"base-{base_key}.lfpt.gz"
        heads = {"X-LF-Key": key, "X-LF-Code": code}
        hit = self._cached(f, base_f, full)
        if hit is not None:
            return hit[0], {**heads, "X-LF-Source": "cache", "X-LF-Made": hit[1]}
        from .app import recordings_dir  # noqa: PLC0415
        loc = local_point(world, spec, values, seed, recordings_dir(), L.atlas_key(spec, code, rh))
        if loc is not None:
            data = with_full_header(loc["data"], loc["base"]) if full else loc["data"]
            return data, {**heads, "X-LF-Source": "atlas", "X-LF-Made": loc["made"]}
        if self.waiting >= QUEUE + 1:  # the one computed and QUEUE waiting
            raise Refused(429, T("the server computes other points now; try again in a moment"))
        self.waiting += 1
        try:
            async with self.lock:
                hit = self._cached(f, base_f, full)  # computed while this request waited
                if hit is not None:
                    return hit[0], {**heads, "X-LF-Source": "cache", "X-LF-Made": hit[1]}
                folder.mkdir(parents=True, exist_ok=True)
                data, rep = await self._spawn(world, atlas, values, seed, folder, f)
        finally:
            self.waiting -= 1
        self._cleanup()
        if not rep.get("stable"):
            raise Refused(503, T("the server's code changed while the point was computed: try again"))
        key, code = rep["key"], rep["code_hash"]
        kept = folder / f"{key}.lfpt.gz"
        tmp = kept.with_name(kept.name + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, kept)
        made = _iso(kept.stat().st_mtime)
        if full:
            data = with_full_header(data, (folder / f"base-{rep['base_key']}.lfpt.gz").read_bytes())
        return data, {"X-LF-Key": key, "X-LF-Code": code, "X-LF-Source": "computed", "X-LF-Made": made}

    @staticmethod
    def _cached(f: Path, base_f: Path, full: bool) -> tuple[bytes, str] | None:
        """(the cached point, as asked for, and when it was computed), or None (not cached; or a full header asked for
        and its base gone: computed again)."""
        try:
            data, made = f.read_bytes(), _iso(f.stat().st_mtime)
            if full:
                data = with_full_header(data, base_f.read_bytes())
            return data, made
        except (OSError, ValueError, IndexError, KeyError):
            return None

    async def _spawn(self, world, atlas, values, seed, folder: Path, want: Path) -> tuple[bytes, dict]:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(registry.SERVER), str(registry.ROOT), str(registry.ENGINE)])
        env.setdefault("OMP_NUM_THREADS", "2")
        env.setdefault("OPENBLAS_NUM_THREADS", "2")
        env[limits.ENV] = str(point_mem(self.worker_mem))
        env["LFPHYS_NO_GPU"] = "1"  # GPU 0 belongs to the live worlds
        out = folder / f"{want.name[:-len('.lfpt.gz')]}.part"
        report = out.with_name(out.name + ".json")
        for p in (report, out):
            p.unlink(missing_ok=True)
        log = open(folder / "point.log", "wb")  # the last point's log only (review R-F F13)
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "lfviz.atlas_live", "--world", world, "--atlas", atlas,
                "--values", json.dumps(protocol.clean(values)), "--seed", str(seed), "--folder", str(folder),
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
        info = {}
        try:
            info = json.loads(report.read_text(), object_hook=json_hook)
        except (OSError, ValueError):
            pass
        data = None
        if proc.returncode == 0:
            try:
                data = out.read_bytes()
            except OSError:
                data = None
        for p in (report, out):
            p.unlink(missing_ok=True)
        if data is not None and info.get("key"):
            return data, info
        if proc.returncode == EXIT_REFUSED and info.get("refused"):
            raise Refused(400, info["refused"]["text"], info["refused"].get("hint"))
        if proc.returncode == EXIT_CHECKS and info.get("checks"):
            raise Refused(409, T("the world's checks fail at these values: {checks}",
                                 checks=join(list(info["checks"]), ", ")))
        if proc.returncode == EXIT_MEMORY or info.get("error") == "memory":
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
        except ValueError:  # not JSON, not UTF-8, or an integer of more than 4300 digits (review R-F F12)
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
