"""c07c: carry-over in p04_fluids (lattice Boltzmann): the flow is the world's state, not an object's. A run of the
preset cylinder_re20 stepped 1 s of world time, then «Новый мир» with «перенести сцену» and another fluid (a law that
starts a new world). What the notice says, and the flow measurables just before and just after (same world time)."""
import json
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, record, start, wait  # noqa: E402

rid = start("p04_fluids", "cylinder_re20", seed=1)
for _ in range(4):
    cmd(rid, "step", {"dt": 0.25})
time.sleep(8)
h1 = [m for m in record(rid) if m["type"] == "header"][0]
cmd(rid, "new_world", {"params": {**{k: v for k, v in h1["params"].items() if k != "scene"}, "fluid": "water"},
                       "carry": True})
wait(lambda: sum(1 for m in record(rid) if m["type"] == "header") == 2, 120)
cmd(rid, "step", {"dt": 1e-6})
time.sleep(4)
rec = record(rid)
i2 = [i for i, m in enumerate(rec) if m["type"] == "header"][-1]
before = [m for m in rec[:i2] if m["type"] == "frame" and m.get("meas")][-1]
after = [m for m in rec[i2:] if m["type"] == "frame" and m.get("meas")][0]
notes = [m["text"] for m in rec[i2:] if m["type"] in ("notice", "error")]
print("notices of world 2:", notes[:4])
print("world 1 last frame t =", before["t"], "| world 2 first frame t =", after["t"])
keys = [k for k in before["meas"] if k in after["meas"]][:8]
for k in keys:
    print(f"   {k}: {before['meas'][k]!r} -> {after['meas'][k]!r}")
json.dump({"run": rid, "notices": notes, "before": before["meas"], "after": after["meas"], "t": [before["t"], after["t"]]},
          open("/out/c07c_carry_p04.json", "w"), indent=1, ensure_ascii=False)
