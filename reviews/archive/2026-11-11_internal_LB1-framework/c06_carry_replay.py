"""c06: a carried scene (new_world {carry: true}) rebuilt by replay, through the private server.

p99_toy, preset "two" in 3-D (a particle with random kicks: the generator matters), stepped by `step` commands (no
wall-clock dependence); a particle off the plane z = 0 and a wall across z added; then a new world with ndim = 2 and
«перенести сцену»: the particle off the plane and the z-wall must be refused and named. In the new world: steps, a drag
(`edit`) and a throw. The last frame (t, at, meas) is kept; the run is suspended, its checkpoint files deleted (so the
resume must rebuild the world from its header — the carried scene — and replay the record), resumed, and the first
frame after the resume compared with the last one before the suspension: bit for bit.
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, get, post, record, start, wait  # noqa: E402

RUNS = "/runs"  # the private server's runs folder, mounted here read-write by the caller
rid = start("p99_toy", "two", seed=7)
for _ in range(6):
    cmd(rid, "step", {"dt": 0.13})
cmd(rid, "scene", {"op": "add", "type": "particle", "values": {"x": 0.5, "y": 0.5, "z": 1.0, "vz": 0.2}})
cmd(rid, "scene", {"op": "add", "type": "wall", "values": {"axis": "z", "position": 2.0}})
cmd(rid, "scene", {"op": "add", "type": "particle", "values": {"x": -2.0, "y": 1.0, "z": 0.0, "vx": 0.3}})
for _ in range(3):
    cmd(rid, "step", {"dt": 0.07})
time.sleep(1.0)
t_before = max(m["t"] for m in record(rid) if m["type"] == "frame")
st, js = cmd(rid, "new_world", {"params": {"ndim": 2, "drag": 0.0}, "carry": True})
wait(lambda: sum(1 for m in record(rid) if m["type"] == "header") == 2, 60)
rec = record(rid)
h2 = [m for m in rec if m["type"] == "header"][-1]
note = [m for m in rec if m["type"] == "notice" and "перенес" in m.get("text", "")]
print("world 1 ended at t =", t_before, "; world 2 header t =", h2["t"], "world", h2["world"])
print("carry notice:", note[-1]["text"] if note else None)
print("carried scene in the header's params: objects", len(h2["params"]["scene"]["objects"]), "carry flag",
      h2["params"]["scene"].get("carry"), "; header JSON chars", len(json.dumps(h2)))
sc2 = [m for m in rec if m["type"] == "scene"][-1]
print("world 2 objects:", [(o["id"], o["label"], o["type"]) for o in sc2["objects"]])
for _ in range(4):
    cmd(rid, "step", {"dt": 0.11})
cmd(rid, "scene", {"op": "edit", "id": "o1", "values": {"x": 0.25, "y": -1.0}})
cmd(rid, "step", {"dt": 0.05})
cmd(rid, "scene", {"op": "edit", "id": "o2", "values": {"x": 1.5, "y": 0.0, "vx": -2.0, "vy": 1.0}})
for _ in range(5):
    cmd(rid, "step", {"dt": 0.09})
time.sleep(1.0)
rec = record(rid)
last = [m for m in rec if m["type"] == "frame"][-1]
keep = {k: last.get(k) for k in ("t", "at", "meas")}
print("last frame before the suspension: t =", keep["t"])
post(f"/api/runs/{rid}/stop")
wait(lambda: get(f"/api/runs/{rid}")[1].get("state") == "suspended", 60)
ck = glob.glob(f"{RUNS}/{rid}/checkpoints/*.pkl")
for f in ck:
    os.remove(f)
print("checkpoint files deleted:", len(ck))
n0 = len(record(rid))
st, js = post(f"/api/runs/{rid}/resume")
print("resume:", st, js)
wait(lambda: any(m["type"] == "frame" for m in record(rid)[n0:]), 120)
rec2 = record(rid)[n0:]
how = [m for m in rec2 if m["type"] in ("resumed", "notice")]
first = [m for m in rec2 if m["type"] == "frame"][0]
again = {k: first.get(k) for k in ("t", "at", "meas")}
print("resumed:", [m.get("how") or m.get("text") for m in how][:3])
print("first frame after the resume: t =", again["t"])
print("bit for bit equal (t, at, meas):", again == keep)
if again != keep:
    print("before:", json.dumps(keep)[:600])
    print("after: ", json.dumps(again)[:600])
json.dump({"run": rid, "notice": note[-1]["text"] if note else None, "equal": again == keep, "before": keep,
           "after": again, "how": [m.get("how") or m.get("text") for m in how]},
          open("/out/c06_carry_replay.json", "w"), indent=1, ensure_ascii=False)
