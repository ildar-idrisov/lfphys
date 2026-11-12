"""c01: sweeps against the closed form (p97_osc: x'' = -(k/m) x, advanced by the exact rotation of the phase plane).

From a live world stepped to t0 by `step` commands (no wall-clock dependence), the state (x0, v0) is exact:
x0 = cos(2 t0), v0 = -2 sin(2 t0) (preset "one": x = 1, v = 0, k = 4, m = 1).

(a) a law sweep (k): x(t0 + T) = x0 cos(wT) + v0/w sin(wT), w = sqrt(k)        -- expected to pass;
(b) an object-parameter sweep of the position x of o1, values 0.5, 1.0, 1.5, where 1.0 is the STORED value of x
    (the preset's), not the current position: "set x = X at t0" gives x(t0 + T) = X cos(2T) + v0/2 sin(2T);
(c) the same for the velocity v with values -1, 0 (stored), 1: x(t0 + T) = x0 cos(2T) + V/2 sin(2T).

Prints per value: measured, closed form of "set to the value", closed form of "no change", and which one it matches.
"""
import json
import math
import sys

sys.path.insert(0, "/out")
from lbrf_client import cmd, get, post, record, start, sweep_done  # noqa: E402

out = {}
rid = start("p97_osc", "one", seed=1)
for _ in range(10):
    cmd(rid, "step", {"dt": 0.05})
import time  # noqa: E402
time.sleep(1.0)
t0_rec = max(m["t"] for m in record(rid) if m["type"] == "frame")
print("run", rid, "live world at t =", t0_rec)
T = 0.7


def x_set(X, V, k=4.0, m=1.0, T=T):
    w = math.sqrt(k / m)
    return X * math.cos(w * T) + V / w * math.sin(w * T)


def run(body):
    st, js = post(f"/api/runs/{rid}/sweep", body)
    assert st == 200, (st, js)
    return sweep_done(rid, js["n"])


res = {}
# (a) the law
js = run({"target": {"kind": "law", "id": "k"}, "values": [1.0, 4.0, 9.0], "duration": T, "measure": "o1.x",
          "stat": "final"})
t0 = js["base"]["t"]
x0, v0 = math.cos(2 * t0), -2 * math.sin(2 * t0)
print(f"base t0 = {t0!r} (source {js['base']['source']}); x0 = {x0:.15g}, v0 = {v0:.15g}")
rows = []
for r in js["results"]:
    k = r["value"]
    ref = x_set(x0, v0, k=k)
    rows.append({"k": k, "measured": r["measured"], "closed_form": ref, "err": abs(r["measured"] - ref)})
    print(f"(a) k = {k:5g}: measured {r['measured']:.15g}  closed form {ref:.15g}  |err| = {abs(r['measured'] - ref):.2e}")
res["a_law"] = rows

# (b) the object's position x, 1.0 = the stored value
js = run({"target": {"kind": "object", "obj": "o1", "param": "x"}, "values": [0.5, 1.0, 1.5], "duration": T,
          "measure": "o1.x", "stat": "final"})
assert js["base"]["t"] == t0, js["base"]
rows = []
for r in js["results"]:
    X = r["value"]
    ref_set, ref_none = x_set(X, v0), x_set(x0, v0)
    m = r["measured"]
    which = "set" if abs(m - ref_set) < 1e-9 else "NO CHANGE" if abs(m - ref_none) < 1e-9 else "neither"
    rows.append({"x": X, "measured": m, "if_set": ref_set, "if_unchanged": ref_none, "matches": which})
    print(f"(b) x = {X:4g}: measured {m:.12g}  if set {ref_set:.12g}  if unchanged {ref_none:.12g}  -> {which}")
res["b_object_x"] = rows

# (c) the object's velocity v, 0.0 = the stored value
js = run({"target": {"kind": "object", "obj": "o1", "param": "v"}, "values": [-1.0, 0.0, 1.0], "duration": T,
          "measure": "o1.x", "stat": "final"})
rows = []
for r in js["results"]:
    V = r["value"]
    ref_set, ref_none = x_set(x0, V), x_set(x0, v0)
    m = r["measured"]
    which = "set" if abs(m - ref_set) < 1e-9 else "NO CHANGE" if abs(m - ref_none) < 1e-9 else "neither"
    rows.append({"v": V, "measured": m, "if_set": ref_set, "if_unchanged": ref_none, "matches": which})
    print(f"(c) v = {V:4g}: measured {m:.12g}  if set {ref_set:.12g}  if unchanged {ref_none:.12g}  -> {which}")
res["c_object_v"] = rows
st, sc = get(f"/api/runs/{rid}")
res["run"] = rid
json.dump(res, open("/out/c01_sweep_closed_form.json", "w"), indent=1)
