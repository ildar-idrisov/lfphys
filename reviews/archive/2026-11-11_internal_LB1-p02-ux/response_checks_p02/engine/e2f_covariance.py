# Is the scene's evolution itself gauge covariant between "tube at c0" and "tube at c0 - s" (the second method's
# premise)? psi_A vs exp(i q chi) psi_B with grad chi = A_A - A_B (chi = -flux_tube_segment(-s)), no move involved.
import math, sys, numpy as np
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S
el = Q.species("electron")
RP, steps, n, edges = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] == "open"
flux = 2 * math.pi * 0.37
def world(tube_at, nsteps):
    s = Q.Scene((n, n), 0.2, dt=0.004, edges=Q.EdgeLayers(0.1 * n * 0.2, 6.0) if edges else None, device="cpu")
    if RP > 0:
        s.add(Q.Ball([0.0, 0.0], RP, 60.0, 1.0))
    s.add(Q.FluxTube(list(tube_at), flux, 0.5))
    pid = s.add_particle(Q.Packet(el, [-12.0, 0.6], [2.2, 0.0], [1.6, 2.6]))
    s.advance(nsteps)
    return s, pid
sh = np.array([0.0, 0.6])
for k in (0, steps // 2, steps):
    sB, pB = world([0.0, 0.0], k); sA, pA = world(list(-sh), k)
    chi = -S.flux_tube_segment(sB.grid, flux, -sh, (0.0, 0.0), 0.5)
    a, b = sA.wave(pA), np.exp(-1j * chi) * sB.wave(pB)
    ph = np.vdot(a, b); ph /= abs(ph)
    print(f"post {RP}, n {n}, edges {'open' if edges else 'closed'}, step {k}: ||psi_A - e^(i phi) e^(i q chi) psi_B|| = "
          f"{np.sqrt(np.sum(np.abs(b - ph * a) ** 2) / np.sum(np.abs(a) ** 2)):.2e}")
