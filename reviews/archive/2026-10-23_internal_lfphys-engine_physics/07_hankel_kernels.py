"""07: Hankel functions of lfphys.core.optics.scalar.hankel1 (scipy below 1e4, 3-term asymptotics above) against
mpmath (40 digits) over x in [1e-3, 1e12]; the Rayleigh-Sommerfeld kernel against its plane-wave identity
int K(x - x', z) dx' = exp(i k z) (an exact property of the first-kind kernel), and the paraxial slit closed form
against mpmath quadrature of its defining integral. Usage: python3 07_hankel_kernels.py
"""
import argparse
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import mpmath as mp
import numpy as np

from lfphys.core.optics import scalar
from lfphys.theories.approx import paraxial

mp.mp.dps = 40
print("=== hankel1(nu, x): relative error vs mpmath J + iY ===")
xs = np.unique(np.concatenate([np.geomspace(1e-3, 1e12, 300), [9999.0, 9999.999, 1e4, 1.0000001e4, 2e4]]))
for nu in (0, 1):
    worst = (0.0, 0.0)
    worst_band = {}
    vals = scalar.hankel1(nu, xs)
    for x, v in zip(xs, vals):
        X = mp.mpf(float(x))
        ref = mp.besselj(nu, X) + 1j * mp.bessely(nu, X)
        e = float(abs(complex(v) - complex(ref)) / abs(ref))
        band = "x<1e4" if x < 1e4 else "x>=1e4"
        worst_band[band] = max(worst_band.get(band, 0.0), e)
        if e > worst[0]:
            worst = (e, x)
    bands = ", ".join(f"{k}: {v:.1e}" for k, v in worst_band.items())
    print(f"nu={nu}: max rel. err {worst[0]:.2e} at x = {worst[1]:.4g};  by band {bands}")

print("\n=== RS kernel: int K dx' over a wide aperture -> exp(i k z) (k = 2 pi, z = 3) ===")
k, z = 2 * math.pi, 3.0
# integrate K over |x'| < X with a smooth taper to suppress the edge diffraction; check at x = 0
for X in (200.0, 800.0):
    t, w = np.polynomial.legendre.leggauss(64)
    edges = np.linspace(-X, X, int(4 * X) + 1)
    h = 0.5 * np.diff(edges); m = 0.5 * (edges[1:] + edges[:-1])
    xp = (m[:, None] + h[:, None] * t).ravel(); wp = (h[:, None] * w).ravel()
    taper = np.where(np.abs(xp) < 0.5 * X, 1.0, np.cos(np.pi * (np.abs(xp) / X - 0.5)) ** 2)
    U = np.sum(scalar.rs_kernel(k, z, np.hypot(xp, z)) * taper * wp)
    print(f"X={X:g}: U(0, z) = {U:.10f}, exp(ikz) = {np.exp(1j * k * z):.10f}, |diff| = {abs(U - np.exp(1j * k * z)):.1e}")

print("\n=== paraxial slit amplitude vs mpmath quadrature of int exp(i[alpha x'^2 + beta x' + gamma0]) dx' ===")
cases = [dict(x=3e-4, z=0.5, k=2 * math.pi / 633e-9, c=-50e-6, a=20e-6),
         dict(x=2.5e-2, z=0.5, k=2 * math.pi / 633e-9, c=50e-6, a=20e-6),
         dict(x=-1e-3, z=1.0, k=2 * math.pi / 500e-9, c=20e-6, a=20e-6, L1=0.4, src=2e-5, kappa=3e4),
         dict(x=0.0, z=2e-4, k=2 * math.pi / 633e-9, c=0.0, a=20e-6)]
for cs in cases:
    cs = dict(cs)
    x, z, kk, c, a = cs.pop("x"), cs.pop("z"), cs.pop("k"), cs.pop("c"), cs.pop("a")
    L1 = cs.get("L1", math.inf); src = cs.get("src", 0.0); kap = cs.get("kappa", 0.0)
    A = complex(paraxial.slit_amplitudes(np.array([x]), z, kk, [c], a, **cs)[0, 0])
    X, Z, K = mp.mpf(x), mp.mpf(z), mp.mpf(kk)
    if math.isinf(L1):
        al, be, g0 = K / (2 * Z), K * mp.sin(src) - K * X / Z + kap, K * X * X / (2 * Z)
    else:
        al = K / 2 * (1 / Z + 1 / mp.mpf(L1)); be = -K * mp.mpf(src) / L1 - K * X / Z + kap
        g0 = K * mp.mpf(src) ** 2 / (2 * L1) + K * X * X / (2 * Z)
    e1, e2 = mp.mpf(c) - mp.mpf(a) / 2, mp.mpf(c) + mp.mpf(a) / 2
    nseg = 400
    ref = mp.quad(lambda t: mp.expj(al * t * t + be * t + g0), mp.linspace(e1, e2, nseg))
    print(f"x={x:g} z={z:g}: |A - ref| / a = {abs(A - complex(ref)) / a:.1e}   (|A|/a = {abs(A) / a:.3f})")
