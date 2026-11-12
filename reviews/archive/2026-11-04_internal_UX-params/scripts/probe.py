import sys, json, time, os, traceback
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry, protocol
from lfviz.sim import Runner
import queue
registry.ensure_path()
only = sys.argv[1:] or registry.viz_ids()
out = {}
path = "/out/probe.json"
if os.path.exists(path):
    out = json.load(open(path))
for vid in only:
    viz = registry.load(vid)
    sch = viz["schema"]
    res = {}
    msgs = []
    def emit(m, b=None):
        mm, bb = protocol.decode(protocol.encode(m, b)); msgs.append(mm)
    try:
        p, errs = sch.resolve(None, {})
        t0 = time.time()
        sim = viz["simulation"](p, 1, emit)
        r = Runner(sim, emit, queue.Queue())
        r._start_world()
        res["build_s"] = round(time.time() - t0, 2)
        h = [m for m in msgs if m.get("type") == "header"][0]
        res["actions"] = h.get("actions")
        res["default_speed"] = sim.default_speed
        res["speed_range"] = sim.speed_range
        res["max_step"] = sim.max_step()
        res["next_event"] = sim.next_event_time()
        res["has_scene3d"] = "scene3d" in h
        if "scene3d" in h:
            res["planes"] = h["scene3d"].get("planes")
        res["header_keys"] = sorted(h.keys())
        if hasattr(sim, "PALETTE") and sim.PALETTE:
            res["palette"] = {k: ot.to_json() for k, ot in sim.PALETTE.items()}
        t0 = time.time(); fr = []
        r.playing = True
        for i in range(20):
            a = time.time()
            r._advance(sim.t + r.speed / 20.0, budget=0.03)
            r._frame(0.0)
            fr.append(time.time() - a)
        res["frames20_s"] = round(time.time() - t0, 2)
        res["frame_max_s"] = round(max(fr), 3)
        res["t_after"] = sim.t
        res["errors"] = [m.get("text")[:300] for m in msgs if m.get("type") == "error"]
        res["checks_failed"] = [(m["id"], m.get("value"), m.get("ref"), m.get("rel"), m.get("tol")) for m in msgs if m.get("type") == "check" and (m.get("ok") is False or (m.get("ok") is None and m.get("rel") is not None and m.get("tol") is not None and abs(m["rel"]) > m["tol"] and not m.get("info")))]
        res["types"] = sorted(set(m.get("type") for m in msgs))
    except Exception:
        res["exc"] = traceback.format_exc()[-1500:]
    out[vid] = res
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=1, default=str)
    print(vid, res.get("build_s"), res.get("frames20_s"), res.get("exc", "")[-200:], flush=True)
