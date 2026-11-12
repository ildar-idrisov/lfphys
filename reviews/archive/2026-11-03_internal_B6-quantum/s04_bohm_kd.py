"""Q: the Bohm points' error at the wavenumbers the scene admits. s03 showed the same 1e-3 relative error for chunks
of 2, 8 and 16 steps: the error is not the time interpolation but the spatial one (8th-order Lagrange interpolation
of psi; its derivative's remainder 576 (k d)^8 / 9! grows fast with k d). The scene admits packets up to
|k| + 6 sigma_k = pi/d, i.e. k d up to ~2.7 on the presets' grids. Free 2-D packets on the double-slit grid (256
points over 80 nm, d = 0.3125), the wrapper's dt rule, chunks of 8 steps, against the exact trajectories."""
import math
import numpy as np
from lfphys.core.quantum import scene as QS
from lfphys.theories.interpretations import bohm

UNITS = QS.Units(1e-9, 9.1093837139e-31)
el = QS.species("atom", UNITS, mass_u=UNITS.mass / 1.66053906892e-27)
d = 80 / 256
sg = (2.5, 4.0)
for kd in (0.5, 1.0, 1.5, 2.0, 2.5):
    k = (kd / d, 0.0)
    c = (-18.0, 0.0)
    sk = [1 / (2 * s) for s in sg]
    E = sum((abs(kk) + 3 * s) ** 2 for kk, s in zip(k, sk)) / 2
    dt = 2.0 ** math.floor(math.log2(0.1 / E))
    T_END = 30.0 / k[0]  # 30 nm of travel
    s = QS.Scene((256, 256), d, dt=dt)
    pid = s.add_particle(QS.Packet(el, list(c), list(k), list(sg)))
    X0 = np.random.default_rng(5).normal(c, sg, (60, 2))
    X = X0.copy()
    n = int(round(T_END / dt / 8)) * 8
    for _ in range(n // 8):
        s.advance(8, snapshots=True)
        snaps, h = s.snapshots(pid)
        grid, H, xp = s.guidance(pid)
        X, _ = bohm.advance_ensemble(grid, snaps, X, h, H, xp=xp)
    ref = bohm.gaussian_trajectory(X0, s.t, c, k, sg)
    err = np.linalg.norm(X - ref, axis=1)
    disp = np.linalg.norm(ref - X0, axis=1).mean()
    rem = 576 * kd**8 / math.factorial(9)
    print(f"k d = {kd:3.1f} (lambda = {2 * math.pi / k[0]:.3f} nm, admitted: {abs(k[0]) + 6 * sk[0] <= math.pi / d}): "
          f"dt = {dt}, t = {s.t:.3f}, max |X - exact| = {err.max():.3e} nm over {disp:.1f} nm "
          f"(rel {err.max() / disp:.2e}); derivative remainder bound 576 (kd)^8/9! = {rem:.2e}")
