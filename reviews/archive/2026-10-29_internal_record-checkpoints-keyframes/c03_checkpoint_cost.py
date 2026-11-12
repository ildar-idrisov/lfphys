# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review 2026-10-29 (record checkpoints, key frames), check c03.
# What a checkpoint costs at a world's DEFAULT parameters (the shipped test uses small ones): the bytes, the time to
# pickle, the time to write + fsync into a folder on the same disk as the server's runs/ (the HDD; a folder of this
# review, removed afterwards), the time to load; and which objects take the special routes of lfviz.checkpoint
# (closures pickled by value with marshal, CuPy arrays, modules by name).
#
#   docker run --rm --name lf-rev-c03 -v <engine>:/lf:ro -v <this folder>/out:/out -e LFPHYS_NO_GPU=1 \
#     -w /lf/visualizations light-funnel-viz python3 /lf/reviews/archive/2026-10-29_internal_record-checkpoints-keyframes/c03_checkpoint_cost.py [viz ...]
import json
import os
import queue
import shutil
import sys
import time
import types
from pathlib import Path

sys.path[:0] = ["/lf/visualizations/server", "/lf/visualizations", "/lf/lfphys"]
from lfviz import checkpoint, registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402

counts = {}
_orig = checkpoint._Pickler.reducer_override


def counting(self, obj):
    r = _orig(self, obj)
    if r is not NotImplemented:
        kind = r[0].__name__
        if kind == "_function":
            kind += ":" + obj.__module__ + "." + obj.__qualname__
        elif kind == "import_module":
            kind += ":" + obj.__name__
        counts[kind] = counts.get(kind, 0) + 1
    return r


checkpoint._Pickler.reducer_override = counting

ids = sys.argv[1:] or [v for v in registry.viz_ids() if v != "v15_kerr_shadow"]
res = {}
disk = Path("/out/c03_tmp_checkpoints")
for viz_id in ids:
    counts.clear()
    try:
        viz = registry.load(viz_id)
        params, _ = viz["schema"].resolve(None, {})
        t0 = time.monotonic()
        sim = viz["simulation"](params, 7, lambda m, b=None: None)
        t_build = time.monotonic() - t0
        run = Runner(sim, sim.emit, queue.Queue())
        run._start_world()
        for k in range(5):
            run._advance(sim.t + 0.2 * sim.default_speed)
            run._frame(0.0)
        t0 = time.monotonic()
        data = checkpoint.dumps(run.checkpoint_state(), sim.emit)
        t_dump = time.monotonic() - t0
        t0 = time.monotonic()
        p = checkpoint.write(disk, 1, data)
        t_write = time.monotonic() - t0
        t0 = time.monotonic()
        checkpoint.loads(p.read_bytes(), sim.emit)
        t_load = time.monotonic() - t0
        res[viz_id] = {"build_s": round(t_build, 2), "bytes": len(data), "MB": round(len(data) / 2**20, 1),
                       "dump_ms": round(1e3 * t_dump), "write_fsync_ms": round(1e3 * t_write),
                       "load_ms": round(1e3 * t_load), "special": dict(counts)}
    except Exception as e:  # noqa: BLE001
        res[viz_id] = {"failed": f"{type(e).__name__}: {e}"[:500]}
    shutil.rmtree(disk, ignore_errors=True)
    print(viz_id, json.dumps(res[viz_id], ensure_ascii=False), flush=True)

with open("/out/c03_checkpoint_cost.json", "a") as f:
    f.write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
