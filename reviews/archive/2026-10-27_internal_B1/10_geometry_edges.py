# Review B1, script 10: edge cases of lfphys.core.geometry.
import math

import numpy as np

from lfphys.core import geometry as G

print("(a) Grid.uniform against the angular-spectrum convention x_i = (i - n//2) d ('as Grid.uniform')")
for n in (4, 5):
    g = G.Grid.uniform(n, float(n))
    print(f"  n={n}: Grid.uniform axis = {g.axes[0].tolist()};  (i - n//2) d = {((np.arange(n) - n // 2) * 1.0).tolist()}")

print("\n(b) a Plane built directly with non-default axes keeps the default name 'xy'")
p = G.Plane((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
print(f"  Plane(u=x, v=z).name = {p.name!r}, normal = {p.normal.tolist()}; same_as(preset 'xz') = {p.same_as(G.Plane.preset('xz'))}")

print("\n(c) slice_field on a grid with a single node along one axis (a 2-D field stored as 3-D)")
g = G.Grid((np.arange(4.0), np.arange(4.0), np.array([0.0])))
try:
    v, ex = G.slice_field(np.ones(g.shape), g, G.Plane.preset("xy", 0.0), np.arange(4.0), np.arange(4.0))
    print("  result exact =", ex, "values finite:", bool(np.all(np.isfinite(v))))
except Exception as e:  # noqa: BLE001
    print(f"  raised {type(e).__name__}: {e}")

print("\n(d) the trilinear bound for a complex field (plane wave e^{i k.r}, k = (2, 1, 0.5)) on a tilted plane")
g = G.Grid.uniform((40, 40, 40), (8.0, 8.0, 8.0))
X, Y, Z = g.mesh()
kv = np.array([2.0, 1.0, 0.5])
f = np.exp(1j * (kv[0] * X + kv[1] * Y + kv[2] * Z))
pl = G.Plane.from_normal((0.3, 1.0, 0.2), origin=(0.1, -0.2, 0.05))
a = np.linspace(-3, 3, 61)
vals, ex = G.slice_field(f, g, pl, a, a)
P = pl.to3d(*np.meshgrid(a, a, indexing="ij"))
ref = np.exp(1j * (P @ kv))
err = np.nanmax(np.abs(vals - ref))
bound = G.interpolation_bound(g, tuple(kv ** 2))
print(f"  max error {err:.3e}  bound {bound:.3e}  within: {err <= bound}")
