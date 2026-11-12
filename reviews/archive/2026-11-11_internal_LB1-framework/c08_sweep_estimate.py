"""c08: the sweep's cost estimate against the cost measured by the sweep itself (p97_osc: ten oscillators).

The estimate takes the record's frames: cpu_ms against the world time between frames. A frame's cpu_ms is the wall time
of the runner's loop iteration from its start (sim.Runner.run), which, when the world is paused, includes the wait for
the next command (up to one frame period, 50 ms). Two records:
(A) a world advanced by `step` commands (paused, as the player's |▶ or a script does);
(B) the same world played for 3 s.
For each: the frames' cpu_ms, the estimate of one sweep, then the sweep itself (where the budget lets it start) and
its own measured cost (advance_s, restore_s per value).
"""
import json
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, post, record, start, sweep_done  # noqa: E402

out = {}
body = {"target": {"kind": "law", "id": "k"}, "values": [2.0, 5.0], "duration": 100.0, "measure": "E", "stat": "max",
        "n_samples": 200}
for case in ("A_steps", "B_played"):
    rid = start("p97_osc", "two", seed=5)
    for i in range(8):
        cmd(rid, "scene", {"op": "add", "type": "osc", "values": {"x": 0.1 * i, "v": 0.2}})
    time.sleep(0.5)
    if case == "A_steps":
        for _ in range(20):
            cmd(rid, "step", {"dt": 0.05})
            time.sleep(0.04)
    else:
        cmd(rid, "play")
        time.sleep(3.0)
        cmd(rid, "pause")
    time.sleep(1.0)
    fr = [m for m in record(rid) if m["type"] == "frame"]
    cpu = [m["cpu_ms"] for m in fr]
    st, est = post(f"/api/runs/{rid}/sweep", {**body, "estimate": True})
    e = est.get("estimate") or {}
    print(f"[{case}] frames {len(fr)}, cpu_ms min {min(cpu):.2f} median {sorted(cpu)[len(cpu) // 2]:.2f} max {max(cpu):.2f}")
    print(f"[{case}] estimate: HTTP {st}; ms per world second {e.get('ms_per_t')}; total {e.get('total_s')} s; «{(est.get('error') or e.get('text') or '')[:200]}»")
    rec = {"frames": len(fr), "cpu_ms": cpu, "estimate_status": st, "estimate": e, "error": est.get("error")}
    st, js = post(f"/api/runs/{rid}/sweep", body)
    if st == 200:
        js = sweep_done(rid, js["n"])
        per = [r.get("advance_s") for r in js["results"]]
        wall = [r.get("wall_s") for r in js["results"]]
        print(f"[{case}] the sweep itself: advance per value {per} s, wall per value {wall} s "
              f"→ {1e3 * sum(per) / (len(per) * body['duration']):.3f} ms per world second")
        rec.update(sweep_advance_s=per, sweep_wall_s=wall)
    else:
        print(f"[{case}] the sweep refused: HTTP {st} «{js.get('error', '')[:160]}»")
        rec.update(sweep_refused=js)
    out[case] = rec
json.dump(out, open("/out/c08_sweep_estimate.json", "w"), indent=1, ensure_ascii=False)
