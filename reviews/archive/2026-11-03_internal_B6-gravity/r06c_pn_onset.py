# Reviewer script (B6 gravity): where the playground's PN binary (all orders, quasi-circular start, the default) stops
# inspiralling: the mean dr/dt over the first 1000 m against the engine's adiabatic rate, and the 2PN energy change,
# for r0 = 8 (the playground's minimum) .. 14.
import numpy as np

from lfphys.core.gravity import pn_binary as PN

o = (1, 2, 2.5, 3.5)
for q in (1.0, 0.25, 0.05):
    nu = q / (1 + q) ** 2
    for r0 in (8.0, 9.0, 10.0, 11.0, 12.0, 14.0):
        st = PN.circular_state(r0, nu, o, quasi=True)
        res = PN.integrate(st, 1000.0, nu, o, n_out=201, r_stop=3.0)
        r = np.linalg.norm(res["x"], axis=1)
        tt = res["t"]
        slope = np.polyfit(tt, r, 1)[0]
        E = np.array([float(PN.energy(x, v, nu, order=2)) for x, v in zip(res["x"], res["v"])])
        print(f"q = {q:5.2f} r0 = {r0:5.1f}: mean dr/dt = {slope:+.3e} (adiabatic {PN.circular_inspiral_rate(r0, nu):+.3e}); "
              f"r range {r.min():.3f}..{r.max():.3f}; E/mu change {E[-1] - E[0]:+.2e}; status {res['status']}",
              flush=True)
