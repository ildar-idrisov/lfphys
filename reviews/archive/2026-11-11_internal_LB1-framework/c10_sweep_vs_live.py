"""c10: a sweep's restored world against the live world, in real sections (p03 molecular dynamics, p04 lattice
Boltzmann), and the dependence of a swept number on the sweep's own sampling.

For each section: a run stepped a little (step commands, no wall clock), paused; a sweep of one live law over ONE value,
its current value (so the swept world is the live world), measuring a world-wide quantity over a duration T:
  (1) stat "final": one reading; the sweep advances the world in one Runner._advance(t0 + T);
  (2) stat "max" with n_samples 200: the world advanced to 200 intermediate moments; its last reading is at t0 + T;
then the live world itself is advanced by one `step {dt: T}` (Runner._advance(t0 + T), the same split as (1)).
Expected for a sweep "from the current moment, the live world unaffected": (1) == live, bit for bit. Shown: whether (2)'s
last reading equals (1), i.e. whether the number the sweep reports depends on how many readings were asked for.
"""
import json
import sys
import time

sys.path.insert(0, "/out")
from lbrf_client import cmd, post, record, start, sweep_done  # noqa: E402

CASES = [  # section, preset, live law, measurable, the step before, T (world seconds)
    ("p03_molecules", "maxwell", "dt_fs", "e", 2e-13, 3e-13),
    ("p04_fluids", "cylinder_re20", "nu", "mass_res", None, None),
]
out = {}
for viz, preset, law, mid, pre, T in CASES:
    rid = start(viz, preset, seed=2)
    h = [m for m in record(rid) if m["type"] == "header"][0]
    live = h["live"][law]
    if pre is None:  # p04: steps of its own scale (its default speed: ~1/10 of a crossing per second)
        pre = 0.5 * h.get("speed", 0) if h.get("speed") else None
    st0 = [m for m in record(rid) if m["type"] == "state"]
    sp = st0[-1]["speed"] if st0 else 1.0
    if pre is None:
        pre = 0.05 * sp
    if T is None:
        T = 0.1 * sp
    cmd(rid, "step", {"dt": pre})
    time.sleep(3)
    sc = [m for m in record(rid) if m["type"] == "scene"][-1]
    ids = [d["id"] for d in sc.get("measurables", [])]
    if mid not in ids:
        mid = [d["id"] for d in sc["measurables"] if d.get("of") is None][0]
    res = {}
    for stat in ("final", "max"):
        st, js = post(f"/api/runs/{rid}/sweep", {"target": {"kind": "law", "id": law}, "values": [live], "duration": T,
                                                 "measure": mid, "stat": stat, "n_samples": 200})
        assert st == 200, js
        js = sweep_done(rid, js["n"], 900)
        r = js["results"][0]
        res[stat] = {"measured": r.get("measured"), "last_reading": (r.get("trace") or {}).get("v", [None])[-1],
                     "t1": r.get("t1"), "t0": r.get("t0"), "error": r.get("error"), "base": js["base"]}
    n0 = len(record(rid))
    cmd(rid, "step", {"dt": T})
    t_end = res["final"]["t1"]
    for _ in range(600):
        fr = [m for m in record(rid)[n0:] if m["type"] == "frame"]
        if fr and fr[-1]["t"] >= t_end - 1e-30:
            break
        time.sleep(0.5)
    live_v = fr[-1]["meas"].get(mid)
    a, b = res["final"]["measured"], res["max"]["last_reading"]
    print(f"{viz}: law {law} = {live}, measure {mid}, t0 = {res['final']['t0']!r}, T = {T!r}")
    print(f"   live world after step(T): t = {fr[-1]['t']!r}  {mid} = {live_v!r}")
    print(f"   sweep 'final' (1 reading):  t = {res['final']['t1']!r}  {mid} = {a!r}   equal to live: {a == live_v}")
    print(f"   sweep 'max' (201 readings), its last reading: t = {res['max']['t1']!r}  {mid} = {b!r}   equal to 'final': {a == b}"
          + ("" if a is None or b is None or a == 0 else f"  (rel. difference {abs(a - b) / abs(a):.2e})"))
    out[viz] = {"law": law, "measure": mid, "T": T, "live": live_v, "live_t": fr[-1]["t"], **res}
json.dump(out, open("/out/c10_sweep_vs_live.json", "w"), indent=1, ensure_ascii=False)
