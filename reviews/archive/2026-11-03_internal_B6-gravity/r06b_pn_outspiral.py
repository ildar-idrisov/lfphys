# Reviewer script (B6 gravity): the binary of r06 that moves OUT (q = 0.05, r0 = 8.5, all orders): its separation
# and 2PN energy along the run, the engine's own circular inspiral rate, and the same start with other orders.
import numpy as np

from lfphys.core.gravity import pn_binary as PN

for q, r0 in ((0.05, 8.5), (0.05, 12.0), (0.05, 20.0), (1.0, 8.5)):
    nu = q / (1 + q) ** 2
    print(f"q = {q}, nu = {nu:.4f}, r0 = {r0}: engine circular_inspiral_rate dr/dt = "
          f"{PN.circular_inspiral_rate(r0, nu):.3e} (3.5PN on), {PN.circular_inspiral_rate(r0, nu, False):.3e} (2.5PN only)")
    for name, o in (("all", (1, 2, 2.5, 3.5)), ("1+2+2.5", (1, 2, 2.5)), ("rr only", (2.5,))):
        st = PN.circular_state(r0, nu, o, quasi=True)
        res = PN.integrate(st, 3000.0, nu, o, n_out=7, r_stop=3.0)
        r = np.linalg.norm(res["x"], axis=1)
        E = np.array([float(PN.energy(x, v, nu, order=2 if 2 in o else 0)) for x, v in zip(res["x"], res["v"])])
        print(f"   {name:8s}: r(t) at t = {np.round(res['t'], 0).tolist()}: {np.round(r, 4).tolist()}; "
              f"E/mu change {E[-1] - E[0]:+.3e}")
