# D9 world side: stated error / scatter of |gamma| over Poisson histograms drawn from the run's expectation
import numpy as np
from lfviz import registry
from lfphys.tools import stats
VIZ = registry.load("u32_double_slit")
for vals in ({}, {"lam_nm": 500.0, "d_um": 50.0, "a_um": 40.0}, {"lam_nm": 600.0, "d_um": 100.0, "a_um": 10.0},
             {"lam_nm": 400.0, "d_um": 300.0, "a_um": 10.0}):
    p, _ = VIZ["schema"].resolve("photon_young", {"screen_um": 30000.0, "n_bohm": 0, **vals})
    sim = VIZ["simulation"](p, 1, lambda m, b=None: None)
    ex = sim.theory["curves"]["all"]
    for n in (300, 600, 2000, 5000):
        rng = np.random.default_rng(n)
        g, e, w = [], [], 0
        for _ in range(60):
            h = rng.poisson(ex * n / ex.sum()).astype(float)
            gh, _ = sim._coherence(h, bins=True, dark=np.zeros(len(ex)))
            sim._coh_err_cache = None
            err, why = sim._coherence_err(h, np.zeros(len(ex)))
            g.append(gh); e.append(err)
        ok = [x for x in e if x is not None]
        sc = float(np.std(g, ddof=1))
        print(f"{vals or 'default'} n={n}: mean|g|={np.mean(g):.4f} scatter={sc:.4f} stated median={np.median(ok) if ok else None} "
              f"ratio={np.median(ok)/sc if ok else None} none={len(e)-len(ok)}", flush=True)
