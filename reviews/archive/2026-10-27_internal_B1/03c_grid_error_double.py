# Review B1, script 03c: the grid (staircase/sampling) error of what v08 draws for its default preset "double"
# (and "square_big"-like geometry at n = 256), which no check of those worlds measures. The same window with half the
# step (2n points), both padded x8 so that the period does not matter; compared on the common nodes.
import math
import sys

import numpy as np

from lfphys.core.optics import angular_spectrum as AS
from v08_wave_3d.viz import SCHEMA, _aperture


def run(preset, extra=None):
    p, _ = SCHEMA.resolve(preset, extra or {})
    lam = p["lam"]
    n = int(p["n"])
    dx = lam / 4 if n <= 256 else lam / 8
    k = 2 * math.pi / lam
    z = float(p["zmax"])
    zs = np.linspace(0.0, z, 96)
    x = (np.arange(n) - n // 2) * dx
    xf = (np.arange(2 * n) - n) * dx / 2
    U0, U0f = _aperture(p, x), _aperture(p, xf)
    a = np.abs(AS.propagate_field(U0, dx, k, z, pad=8, check=True)) ** 2
    b = np.abs(AS.propagate_field(U0f, dx / 2, k, z, pad=8, check=True))[::2, ::2] ** 2
    sa = np.abs(AS.propagate_slice(U0, dx, k, zs[1:], axis=1, at=0.0, pad=8, check=True)) ** 2
    sb = np.abs(AS.propagate_slice(U0f, dx / 2, k, zs[1:], axis=1, at=0.0, pad=8, check=True))[:, ::2] ** 2
    print(f"{preset} {extra or ''}: z = z_max plane: max|I_n - I_2n|/max I = {np.max(np.abs(a - b)) / b.max():.2e};"
          f"  y = 0 slice (z > 0): {np.max(np.abs(sa - sb)) / sb.max():.2e};  peak I_n/I_2n = {a.max() / b.max():.4f}",
          flush=True)


run("double")
run("square_big", {"n": 256})
