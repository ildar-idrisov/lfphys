# Reviewer script (B6 gravity): the playground's "circular orbit" initial velocity (p01 NewtonMode._velocity).
# The new body gets sqrt(G M_others / r) about the others' centre of mass, the others keep their velocities.
# Measured: the relative orbit's eccentricity (a circular two-body orbit needs sqrt(G (M + m) / r) relative speed,
# with the reflex motion of the others) and the drift of the whole system's centre of mass.
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from p01_gravity.viz import G_AU, KMS, YR  # noqa: E402


def scene(objs):
    return {"laws": "newton", "collisions": "pass",
            "scene": {"format": "lfscene", "version": 1, "objects": objs}}


def rel_elements(nb, k1, k2):
    b1, b2 = nb.body(k1), nb.body(k2)
    m = b1["m"] + b2["m"]
    d = np.array(b2["x"]) - np.array(b1["x"])
    w = np.array(b2["v"]) - np.array(b1["v"])
    r = np.linalg.norm(d)
    eps = 0.5 * w @ w - G_AU * m / r
    a = -G_AU * m / (2 * eps)
    h = np.cross(d, w)
    e = math.sqrt(max(0.0, 1 + 2 * eps * (h @ h) / (G_AU * m) ** 2))
    return a, e


print("case: star 1 Msun at the origin, a second star of mass m at x = 1 au, vmode = circular")
for m2 in (1.0, 0.1, 1e-3, 1e-4):
    h = Harness("p01_gravity", None, scene([
        {"type": "star", "label": "A", "values": {"mass": 1.0, "radius": 0.001}},
        {"type": "star", "label": "B", "values": {"mass": m2, "radius": 0.001, "x": 1.0, "vmode": "circular"}}]))
    nb = h.sim.mode.nb
    a, e = rel_elements(nb, "o1", "o2")
    P = nb.momentum()
    M = nb.total_mass()
    print(f"  m2 = {m2:8.3g}: relative orbit a = {a:.6f} au, e = {e:.6f} (circular needs e = 0); "
          f"expected e = m2/(M+m2) = {m2 / (1 + m2):.6f}; centre-of-mass velocity {np.linalg.norm(P) / M / KMS:.4g} km/s")

print()
print("preset 'inner': Jupiter's relative orbit about the Sun and the centre-of-mass drift")
h = Harness("p01_gravity", "inner")
nb = h.sim.mode.nb
labels = {o["id"]: o["label"] for o in h.sim.objects.values()}
for k in nb.keys[1:]:
    a, e = rel_elements(nb, "o1", k)
    print(f"  {labels[k]:10s}: a = {a:.6f} au, e(Sun-planet) = {e:.3e}")
P = nb.momentum()
M = nb.total_mass()
vc = np.linalg.norm(P) / M
print(f"  centre-of-mass velocity of the whole system: {vc / KMS * 1e3:.3f} m/s = {vc:.3e} au/yr: "
      f"the scene drifts {vc * 1000:.3f} au per 1000 yr")

print()
print("preset 'hole_stars': star 2 (2 Msun, x = -3.5) about the hole (1000 Msun) + star 1")
h = Harness("p01_gravity", "hole_stars")
nb = h.sim.mode.nb
for k in ("o2", "o3"):
    a, e = rel_elements(nb, "o1", k)
    print(f"  {k}: e(hole-star) = {e:.3e}")

print()
print("off the xy plane: star B at (1, 0, 1) au around A, vmode circular (r used = cylindrical 1 au, true 1.414 au)")
h = Harness("p01_gravity", None, scene([
    {"type": "star", "label": "A", "values": {"mass": 1.0, "radius": 0.001}},
    {"type": "planet", "label": "B", "values": {"mass": 1.0, "radius": 1.0, "x": 1.0, "z": 1.0}}]))
nb = h.sim.mode.nb
a, e = rel_elements(nb, "o1", "o2")
print(f"  planet at z = 1 au: e = {e:.4f} (a = {a:.4f} au)")
