"""Q: the wrapper advances Bohm points over BOHM_CHUNK = 8 scene steps with psi interpolated quadratically in time
through three snapshots (t, t + h/2, t + h). How large is the error this adds, at the wrapper's own time step?

A free 2-D Gaussian packet (the double-slit preset's electron: lambda = 2 nm, sigma = (2.5, 4) nm) on the preset's
grid (256 points over 80 nm) with the wrapper's dt (largest kinetic energy turned by 0.1 rad, a power of two). Bohm
points |psi|^2-distributed are advanced in chunks of 2, 8 and 16 steps and compared with the exact trajectories
(bohm.gaussian_trajectory, each keeps its quantile). The engine's own test uses chunks of 2 steps."""
import math, sys
import numpy as np
from lfphys.core.quantum import scene as QS
from lfphys.theories.interpretations import bohm

UNITS = QS.Units(1e-9, 9.1093837139e-31)
el = QS.species("atom", UNITS, mass_u=UNITS.mass / 1.66053906892e-27)  # mass 1, spinless, neutral
c, k, sg = (-20.0, 0.0), (math.pi, 0.0), (2.5, 4.0)
sk = [1 / (2 * s) for s in sg]
E = sum((abs(kk) + 3 * s) ** 2 for kk, s in zip(k, sk)) / 2
dt = 2.0 ** math.floor(math.log2(0.1 / E))
print(f"wrapper dt for this packet: {dt} (E_max {E:.3f}, phase per step {E * dt:.3f}); E(k0) h for h = 8 dt: "
      f"{k[0] ** 2 / 2 * 8 * dt:.3f} rad")
T_END = 12.0
X0 = np.random.default_rng(5).normal(c, sg, (60, 2))
for chunk in (2, 8, 16):
    s = QS.Scene((256, 256), 80 / 256, dt=dt)
    pid = s.add_particle(QS.Packet(el, list(c), list(k), list(sg)))
    X = X0.copy()
    n = int(round(T_END / dt))
    done = 0
    while done < n:
        s.advance(chunk, snapshots=True)
        snaps, h = s.snapshots(pid)
        grid, H, xp = s.guidance(pid)
        X, _ = bohm.advance_ensemble(grid, snaps, X, h, H, xp=xp)
        done += chunk
    ref = bohm.gaussian_trajectory(X0, s.t, c, k, sg)
    err = np.linalg.norm(X - ref, axis=1)
    disp = np.linalg.norm(ref - X0, axis=1)
    print(f"chunk {chunk:2d} steps (h = {chunk * dt:.4f}): t = {s.t:.3f}, max |X - exact| = {err.max():.3e} nm, "
          f"median {np.median(err):.3e}; displacement {disp.mean():.2f} nm; rel {err.max() / disp.mean():.2e}")
