# Review B1, script 11: v08's Gaussian check (tolerance 1e-8, fixed) across the schema's range, and the reference
# (mpmath quadrature split at k/2, k, 2k) against a second quadrature (Gauss-Legendre on many panels, numpy).
import math

import numpy as np

from v08_wave_3d.viz import _gauss_on_axis
from lfphys.core.optics import angular_spectrum as AS


def ref_gl(lam, w, z, panels=4000, order=20):
    """(w^2/2) int_0^inf q e^{-q^2 w^2/4} e^{i kz z} dq by composite Gauss-Legendre up to q = 12/w (e^{-36} ~ 2e-16)."""
    k = 2 * math.pi / lam
    qmax = 12.0 / w
    xg, wg = np.polynomial.legendre.leggauss(order)
    edges = np.unique(np.concatenate([np.linspace(0, qmax, panels + 1), [k] if k < qmax else []]))
    tot = 0j
    for a, b in zip(edges[:-1], edges[1:]):
        q = 0.5 * (b - a) * xg + 0.5 * (a + b)
        kz = np.sqrt((k * k - q * q).astype(complex))
        kz = np.where(kz.imag < 0, -kz, kz)
        tot += 0.5 * (b - a) * np.sum(wg * q * np.exp(-q * q * w * w / 4) * np.exp(1j * kz * z))
    return w * w / 2 * tot


for lam, w, z, n in [(0.5, 1.5, 30.0, 256), (0.3, 0.5, 80.0, 256), (1.5, 0.5, 80.0, 128), (0.3, 6.0, 80.0, 256),
                     (1.5, 6.0, 2.0, 256), (0.5, 6.0, 30.0, 128), (0.3, 6.0, 30.0, 128), (1.0, 3.0, 80.0, 256)]:
    dx = lam / 4 if n <= 256 else lam / 8
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-(X ** 2 + Y ** 2) / w ** 2).astype(complex)
    k = 2 * math.pi / lam
    U = AS.propagate_field(U0, dx, k, z, pad=4, check=True)[n // 2, n // 2]
    r_mp = _gauss_on_axis(lam, w, z)
    r_gl = ref_gl(lam, w, z)
    err = abs(U - r_mp) / abs(r_mp)
    edge = math.exp(-((n // 2 * dx) / w) ** 2)
    print(f"lam={lam:3.1f} w={w:3.1f} z={z:4.0f} n={n}: check error {err:.1e} -> {'ok  ' if err <= 1e-8 else 'FAIL'}"
          f"  | mpmath vs Gauss-Legendre {abs(r_mp - r_gl) / abs(r_gl):.1e} | Gaussian at the window edge {edge:.1e}",
          flush=True)
