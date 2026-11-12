"""Small checks of the scene's bookkeeping:
(a) Scene.snapshots after a measurement: the docstring says None ("when a jump or a measurement broke the interval");
    measure() sets snap_ok = False but leaves the last interval's snapshots in place.
(b) the energy check's reference: _reset_refs sets t_ref = now and E_ref = None; E_ref is taken at the first checks()
    call after it, later — so "since" (the wrapper prints «с t = ...») is not the time of the reference.
(c) a ball smaller than its edge: the peak of V is below "height" and V has a cone at the centre (not refused, not
    stated); the tunnel preset's barrier (1.5 nm, edge 0.995 nm) peaks at 0.947 of its nominal height."""
import math
import numpy as np
from lfphys.core.quantum import scene as Q, schrodinger_nd as S
import scipy.constants as sc

M1 = Q.species("atom", mass_u=sc.m_e / sc.atomic_mass)
s = Q.Scene((96, 96), 0.25, dt=0.01)
pid = s.add_particle(Q.Packet(M1, [0.0, 0.0], [1.0, 0.0], [1.5, 1.5]))
s.advance(4, snapshots=True)
before = s.snapshots(pid)
s.measure(pid, 0.5, np.random.default_rng(0))
after = s.snapshots(pid)
print(f"(a) snapshots after a measurement: {'None' if after is None else 'the pre-measurement interval (stale)'}; "
      f"same object as before: {after is before}")
s2 = Q.Scene((96, 96), 0.25, dt=0.01)
s2.add(Q.HarmonicTrap([0, 0], [1.0, 1.0]))
p2 = s2.add_particle(Q.Packet(M1, [-2.0, 0.5], [1.5, 0.5], [0.8, 0.8]))
s2.advance(300)
c = s2.checks()[p2]["energy"]
print(f"(b) after a change at t = 0 and the first check at t = {s2.t:.2f}: since = {c['since']}, but E_ref is the "
      f"energy at t = {s2.t:.2f} (drift {c['drift']:.1e} by construction)")
g = S.Grid((1, 1), 1.0)
for R, w in ((3.0, 1.0), (1.0, 1.0), (0.5, 1.0), (0.25, 1.0)):
    b = Q.Ball([0.0, 0.0], R, 1.0, w)
    peak = float(b.V(g)[0, 0])
    e = Q.edge_eps(w)
    slope = math.exp(-(R / e) ** 2) / (e * math.sqrt(math.pi))
    print(f"(c) ball R = {R} nm, edge {w} nm: V(centre)/height = {peak:.3f}; |dV/dr| at the centre (a cone) = "
          f"{slope:.3f} height per nm")
w = 1.05 * Q.edge_min(80 / 256)
print(f"    tunnel preset barrier: 1.5 nm wide, edge {w:.3f} nm: peak {float(Q.smooth_interval(0.0, -0.75, 0.75, w)):.3f} "
      f"of its height")
