"""Peak memory (VmHWM, and the private writable data RLIMIT_DATA counts: VmData) of each world's default and presets,
built and advanced for a few frames, one process per world (fork). Output: one JSON line per world/preset."""
import json, os, sys, time, resource, queue
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations"); sys.path.insert(0, "/lf/lfphys")
from lfviz import registry
from lfviz.sim import Runner
registry.ensure_path()
def status():
    d = {}
    for line in open("/proc/self/status"):
        k, _, v = line.partition(":")
        if k in ("VmHWM", "VmData", "VmPeak", "VmRSS"):
            d[k] = int(v.split()[0]) * 1024
    return d
def one(vid, preset):
    viz = registry.load(vid)
    p, errs = viz["schema"].resolve(preset, {})
    t0 = time.time()
    sim = viz["simulation"](p, 1, lambda *a, **k: None)
    r = Runner(sim, lambda *a, **k: None, queue.Queue())
    r._start_world()
    for i in range(30):
        r._advance(sim.t + r.speed / 20, budget=2.0)
        r._frame(0.0)
    s = status()
    return {"viz": vid, "preset": preset, "secs": round(time.time() - t0, 1), "hwm_gb": round(s["VmHWM"] / 2**30, 3), "data_gb": round(s["VmData"] / 2**30, 3), "peak_vm_gb": round(s["VmPeak"] / 2**30, 3)}
ids = sys.argv[1].split(",") if len(sys.argv) > 1 else registry.viz_ids()
for vid in ids:
    viz = registry.load(vid)
    presets = [None] + list(viz["schema"].presets)[:3]
    for pr in presets:
        pid = os.fork()
        if pid == 0:
            try:
                out = one(vid, pr)
            except BaseException as e:
                out = {"viz": vid, "preset": pr, "error": f"{type(e).__name__}: {str(e)[:200]}"}
            print(json.dumps(out), flush=True)
            os._exit(0)
        os.waitpid(pid, 0)
