# Review B1, script 03b: is the x16 window of script 03 converged? The plane z = z_max of v08's "double" preset
# (n = 256, the grid v08 uses) computed with pads 4 (v08), 8, 16, 32; differences on the linear and the log view.
import math

import numpy as np

from lfphys.core.optics import angular_spectrum as AS
from v08_wave_3d.viz import SCHEMA, _aperture

p, _ = SCHEMA.resolve("double", {})
lam = p["lam"]
n = int(p["n"])
dx = lam / 4
x = (np.arange(n) - n // 2) * dx
U0 = _aperture(p, x)
k = 2 * math.pi / lam
z = float(p["zmax"])
I = {pad: np.abs(AS.propagate_field(U0, dx, k, z, pad=pad, check=True)) ** 2 for pad in (4, 8, 16, 32)}
for a, b in ((4, 32), (8, 32), (16, 32)):
    ref = I[b]
    pk = ref.max()
    m = ref > 1e-6 * pk
    dl = np.abs(np.log10(np.maximum(I[a][m], 1e-300) / ref[m]))
    print(f"pad {a:2d} vs pad {b}: linear max|dI|/max I = {np.max(np.abs(I[a] - ref)) / pk:.2e};  log view: "
          f"{np.mean(dl > 0.1) * 100:5.1f}% of pixels off by > 0.1 decade (worst {dl.max():.2f})", flush=True)
