# where does the second method's residual sit? (shielded tube, move (0, 0.6))
import math, sys, numpy as np
from lfphys.core.quantum import scene as Q
from lfphys.core.quantum import schrodinger_nd as S
el = Q.species("electron")
V, steps, n, d, RP = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
def world(tube_at):
    s = Q.Scene((n, n), d, dt=0.004, edges=Q.EdgeLayers(0.1 * n * d, 6.0), device="cpu")
    s.add(Q.Ball([0.0, 0.0], RP, V, 1.0))
    s.add(Q.FluxTube(list(tube_at), 2 * math.pi * 0.37, 0.5))
    pid = s.add_particle(Q.Packet(el, [-12.0, 0.6], [2.2, 0.0], [1.6, 2.6]))
    s.advance(steps)
    return s, pid
sh = np.array([0.0, 0.6])
sB, pB = world([0.0, 0.0]); sA, pA = world(-sh)
sB.move_particle(pB, sh)
ref = S.translate(sA.wave(pA), sA.grid, sh); got = sB.wave(pB)
ph = np.vdot(ref, got); ph /= abs(ph)
dd = np.abs(got - ph * ref) ** 2; tot = np.sum(np.abs(ref) ** 2)
X = sB.grid.mesh(); r2 = X[0] ** 2 + X[1] ** 2
w = 0.1 * n * d; L = 0.5 * n * d
lay = (np.abs(X[0]) > L - w) | (np.abs(X[1]) > L - w)
post = np.broadcast_to(r2 < (RP + 1.0) ** 2, dd.shape)
lay = np.broadcast_to(lay, dd.shape)
rho = np.abs(got) ** 2
print(f"V {V} steps {steps} grid {n}x{d}: total {np.sqrt(dd.sum()/tot):.2e}; in r<4: {np.sqrt(dd[post].sum()/tot):.2e}; "
      f"in the layers: {np.sqrt(dd[lay].sum()/tot):.2e}; elsewhere: {np.sqrt(dd[~post & ~lay].sum()/tot):.2e}; "
      f"prob in layers {rho[lay].sum()/rho.sum():.2e}")
