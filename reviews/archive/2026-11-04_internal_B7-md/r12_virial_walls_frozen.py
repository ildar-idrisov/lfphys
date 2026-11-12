"""Virial pressure against the momentum given to hard walls (MD.pressure docstring: equal for hard walls, Clausius).
(A) a 2-D LJ liquid between specular walls (all axes walled): per axis, time averages - expected equal.
(B) the same box with a block of frozen atoms (mass inf) in the middle, compressed (spacing 1.0 sigma): the pair
virial also sums the frozen-frozen pairs and the forces on the frozen atoms, which Clausius' theorem for the moving
atoms does not contain; the frozen block alone (no mobile atoms) already gives a 'pressure'."""
import common  # noqa: F401
import numpy as np

from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import LennardJones


def make(frozen):
    md = MD(dim=2, box=(20.0, 20.0), boundary="walls", pair=LennardJones(2.5, "force"), dt=0.004, seed=21)
    md.add_species("A")
    md.add_species("W", mass=float("inf"))
    if frozen:
        g = np.arange(8.0, 12.01, 1.0)
        md.add("W", np.array([[a, b] for a in g for b in g]))
    return md


def measure(md, n_eq=3000, n=2000, every=20):
    md.step(n_eq)
    md.reset_counters()
    tens = []
    for _ in range(n):
        md.step(every)
        tens.append(md.pressure()["tensor"])
    p = md.pressure()
    walls = p["walls"]
    t = np.mean(tens, axis=0)
    return t, {k: round(v, 4) for k, v in walls.items()}


m = make(False)
m.fill("A", n=250, T=1.0, region=([0.5, 0.5], [19.5, 19.5]))
t, w = measure(m)
print(f"(A) LJ, walls: virial tensor (x, y) = ({t[0]:.4f}, {t[1]:.4f}); walls {w}")
m = make(True)
print(f"(B0) frozen block only (no mobile atoms): virial = {m.pressure()['virial']:.4f}, tensor {m.pressure()['tensor']}")
pts = np.array([[x, y] for x in np.arange(1.0, 19.6, 1.25) for y in np.arange(1.0, 19.6, 1.25)
                if not (6.5 < x < 13.5 and 6.5 < y < 13.5)])
m.add("A", pts[:250], T=1.0)
t, w = measure(m)
print(f"(B) LJ + frozen block, walls: virial tensor (x, y) = ({t[0]:.4f}, {t[1]:.4f}); walls {w}")
