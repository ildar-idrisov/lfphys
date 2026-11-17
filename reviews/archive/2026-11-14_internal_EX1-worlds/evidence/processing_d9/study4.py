"""D9 study 3 (final code): coherence_boot's error against the Monte Carlo scatter (16-84 % half-width) of |gamma|."""
import json, sys, time
import numpy as np
sys.path.insert(0, "/out")
from study_lib import basis, pattern
from lfphys.tools import stats as S
S.COH_BOOT_MIN_HITS = 0
GEOM = {"g200eq": dict(nb=200, fr=10.0, env=0.35, g22=1.0, dark=0.0), "g200": dict(nb=200, fr=10.0, env=0.35, g22=0.8, dark=0.0),
        "g60": dict(nb=60, fr=6.0, env=0.25, g22=1.0, dark=0.0),
        "g400d": dict(nb=400, fr=20.0, env=0.5, g22=0.5, dark=0.05)}
rng = np.random.default_rng(11)
out = []
for gname, gp in GEOM.items():
    b = basis(gp["nb"], gp["fr"], gp["env"])
    for gam in (1.0, 0.99, 0.97, 0.95, 0.9, 0.7, 0.3):
        P = pattern(b, 1.0, gp["g22"], gam); P = P / P.sum()
        for N in (100, 200, 300, 400, 600, 1000, 3000):
            d = np.full(gp["nb"], gp["dark"] * N / gp["nb"])
            mu = P * N * (1 - gp["dark"]) + d
            vals = []
            for _ in range(600):
                g, _ = S.coherence_ml(rng.poisson(mu).astype(float), *b, 1.0, gp["g22"], dark=d)
                if g is not None:
                    vals.append(g)
            vals = np.array(vals)
            hw = float(np.std(vals, ddof=1))
            r, none, t0 = [], 0, time.process_time()
            K = 40
            for k in range(K):
                h = rng.poisson(mu).astype(float)
                res = S.coherence_boot(h, *b, 1.0, gp["g22"], dark=d, rng=np.random.default_rng(1000 + k))
                if res["err"] is None: none += 1
                else: r.append(res["err"] / hw)
            cpu = (time.process_time() - t0) / K
            r = np.array(r)
            row = {"geom": gname, "gam": gam, "N": N, "fails": 600 - len(vals), "median_est": round(float(np.median(vals)), 4),
                   "max_est": round(float(vals.max()), 4), "hw": round(hw, 5), "sd": round(float(np.std(vals)), 5),
                   "ratio_med": round(float(np.median(r)), 3) if len(r) else None,
                   "within2": round(float(np.mean((r > 0.5) & (r < 2))), 3) if len(r) else None,
                   "within1p5": round(float(np.mean((r > 1 / 1.5) & (r < 1.5))), 3) if len(r) else None,
                   "rmin": round(float(r.min()), 3) if len(r) else None, "rmax": round(float(r.max()), 3) if len(r) else None,
                   "none": none, "cpu_s": round(cpu, 3)}
            print(json.dumps(row), flush=True)
            out.append(row)
json.dump(out, open("/out/study4.json", "w"), indent=1)
