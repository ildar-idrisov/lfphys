import sys, time, json
root = sys.argv[1]
sys.path[:0] = [f"{root}/visualizations", f"{root}/visualizations/server", f"{root}/lfphys", root]
from tests.harness import Harness
vals = json.loads(sys.argv[2]); preset = sys.argv[3] if len(sys.argv) > 3 else None
t0 = time.time()
h = Harness("v03_quantum_1d", preset, vals)
bad = {c["id"]: (c["value"], c["ref"], c.get("tol")) for c in h.checks().values() if c.get("ok") is False}
s = h.sim
print(json.dumps({"vals": vals, "s": round(time.time() - t0, 1), "capped": s.capped, "slow_note": s.slow_note[:60],
                  "t_end_est": s.t_end_est, "t_last": float(s.t_snap[-1]), "det": [s.det, s.W0, s.R_det], "bad": bad,
                  "T": s.PR[-1] / (s.PL[-1] + s.PR[-1]), "ref": s._expected_T()[0]}, default=str))
