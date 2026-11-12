# Review B1, script 02: is v08's circle check honest? (CPU, fp64)
# v08 compares the on-axis field of grid n (pad 4) with the exact RS-I closed form e^{ikz} - (z/R) e^{ikR}, with the
# tolerance 2 |U_n - U_2n| + 1e-6 (grid 2n = half the step in the same window, also pad 4). Both grids have the same
# padded period, so the field of the periodic copies of the aperture is common to U_n and U_2n and invisible to the
# tolerance. Here: the true error |U_n - ref|, the tolerance, and the part of the error that comes from the period
# (U_n at pad 4 against U_n at pad 16, same grid).
import math

import numpy as np

from lfphys.core.optics import angular_spectrum as AS
from v08_wave_3d.viz import _aperture


def onaxis(p, n, lam, z, pad, fine=1):
    dx = (lam / 4 if n <= 256 else lam / 8) / fine
    nn = n * fine
    x = (np.arange(nn) - nn // 2) * dx
    U0 = _aperture(p, x)
    return AS.propagate_field(U0, dx, 2 * math.pi / lam, z, pad=pad, check=True)[nn // 2, nn // 2]


rows = []
for (lam, a, zmax, n) in [(0.5, 3.0, 40.0, 256), (0.5, 0.75, 30.0, 256), (0.5, 2.0, 30.0, 256), (0.5, 6.0, 80.0, 256),
                          (1.0, 3.0, 40.0, 128), (0.3, 1.0, 20.0, 128), (1.5, 6.0, 80.0, 128), (0.5, 0.2, 10.0, 128)]:
    p = {"source": "circle", "a": a}
    k = 2 * math.pi / lam
    dx = lam / 4 if n <= 256 else lam / 8
    half = n // 2 * dx
    z = min(zmax, 0.6 * half)  # as v08
    R = math.hypot(z, a)
    ref = np.exp(1j * k * z) - z / R * np.exp(1j * k * R)
    Un = onaxis(p, n, lam, z, 4)
    Uf = onaxis(p, n, lam, z, 4, fine=2)
    tol = 2 * abs(Un - Uf) + 1e-6
    err = abs(Un - ref)
    Un16 = onaxis(p, n, lam, z, 16)
    Uf16 = onaxis(p, n, lam, z, 16, fine=2)
    period = abs(Un - Un16)
    rows.append((lam, a, n, z, abs(ref), err, tol, err <= tol, period, abs(Uf16 - ref)))
    print(f"lam={lam:3.1f} a={a:4.2f} n={n:3d} z={z:6.2f}: |ref|={abs(ref):.4f}  err|Un-ref|={err:.2e}  tol={tol:.2e}  "
          f"ok={err <= tol!s:5}  period part |Un(pad4)-Un(pad16)|={period:.2e}  |U2n(pad16)-ref|={abs(Uf16 - ref):.2e}",
          flush=True)
