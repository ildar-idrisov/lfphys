# Review LB1-p02-ux, Part A, script a5: how often a drag of a scattered wave is refused for "crossing the face" in a
# world with OPEN (absorbing) edges, where the part near the face sits inside the absorbing layer. Double slit preset,
# the electron dragged by 1, 3 and 5 nm in four directions at several moments. Run as a4 (harness).
import numpy as np
from harness import Harness
from lfphys.core.quantum import schrodinger_nd as S

V = "p02_quantum"
h = Harness(V, "double_slit")
oid = [o for o, (k, q) in h.sim.ref.items() if k == "particle"][0]
pid = h.sim.ref[oid][1]
for mult in (2, 4, 6, 8, 10):
    t_end = mult * h.sim.default_speed
    while h.sim.t < t_end:
        h.run_to(min(t_end, h.sim.t + 0.5 * h.sim.default_speed))
        h.runner._frame(0.0)
    qs = h.sim.qs
    psi = qs.wave(pid)
    g = qs.grid
    layers = qs._arr["W_parts"]["edges"]
    rho = np.abs(psi) ** 2
    in_layers = float(rho[layers > 0].sum() / rho.sum())
    res = []
    for d in (1.0, 3.0, 5.0):
        for sh in ((-d, 0), (d, 0), (0, d), (0, -d)):
            w = S.wrap_fraction(psi, g, np.array(sh))
            res.append(("ok" if w <= 1e-6 else "REFUSED") + f"{sh}:{w:.1e}")
    print(f"t = {h.sim.t:.3e} s (norm {qs.norm(pid):.4f}, in the edge layers {in_layers:.2e}):")
    print("   " + "; ".join(res))
