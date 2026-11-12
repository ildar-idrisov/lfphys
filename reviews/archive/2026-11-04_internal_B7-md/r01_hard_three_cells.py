"""Hard disks in a periodic box with three cells along an axis (3 sigma <= L < 4 sigma, allowed by core.md.hard):
the collision prediction takes the minimum image at the prediction time; two particles in adjacent cells can be
1.5 w .. 2 w apart, beyond L/2, so the image that will collide is not the minimum image then and the collision is
missed (the particles overlap). Negative control: the same pair in a box of four cells (L = 4) collides at contact."""
import common  # noqa: F401
import numpy as np

from lfphys.core.md.hard import HardSpheres


def run(Lx, xi, xj, vj, t_end):
    hs = HardSpheres(2, (Lx, 10.0), boundary="periodic", seed=0)
    hs.add_species("a", mass=1.0, sigma=1.0)
    hs.add("a", [[xi, 5.0], [xj, 5.0]], v=[[0.0, 0.0], [vj, 0.0]])
    out = []
    for t in np.linspace(0.0, t_end, 41)[1:]:
        hs.advance(t)
        x = hs.positions()
        d = x[1, 0] - x[0, 0]
        d -= Lx * np.rint(d / Lx)
        out.append((t, abs(d), hs.counters()["collisions"]))
    return hs, out


print("cells per axis:", "L=3 ->", int(np.floor(3.0 / 1.0)), "; L=4 ->", int(np.floor(4.0 / 1.0)))
# L = 3: i at x = 0.1 (cell 0), j at x = 1.9 (cell 1) moving left at 1: separation 1.8 > L/2 = 1.5, the minimum image
# is -1.2 (moving apart); the true contact (separation 1) is at t = 0.8, before j leaves its cell (t = 0.9)
for Lx in (3.0, 4.0):
    hs, out = run(Lx, 0.1, 1.9, -1.0, 2.0)
    dmin = min(d for _, d, _ in out)
    first = next(((t, d) for t, d, c in out if c > 0), None)
    print(f"Lx = {Lx}: collisions {hs.counters()['collisions']}, smallest centre distance seen {dmin:.4f} "
          f"(sigma = 1); first sample after a collision {first}")
    for t, d, c in out[12:22]:
        print(f"   t = {t:.2f}  |r_ij| = {d:.4f}  collisions = {c}")
