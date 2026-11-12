"""Review check 01: the closed-form Fresnel amplitudes, their x-derivative, Parseval, and the RS kernel.

Independent references:
* the Fresnel integral A_j(x) = int_slit U0(x') exp(i k (x-x')^2/(2z)) dx' evaluated by brute-force
  Gauss-Legendre quadrature (many nodes) directly from its definition (not from the closed form);
* the derivative by central finite differences of the closed form, and by quadrature of d/dx of the integrand;
* the 2-D RS-I kernel: a very wide aperture must reproduce the incident plane wave exp(ikz) (sign and magnitude);
  and on the axis behind a slit it must agree with the paraxial field sqrt(k/(2 pi i z)) e^{ikz} A;
* the Hankel asymptotic branch against scipy at the switch point.

Run (from the light-funnel root):
  docker run --rm -v $PWD:/lf -w /lf/visualizations -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server \
     light-funnel-viz python3 /lf/reviews/2026-10-22_internal_viz-v02_physics/01_fresnel_rs.py
"""
import math

import numpy as np
from scipy import special

from v02_double_slit.engine import fresnel, rs


def brute(x, z, k, c, a, L1=math.inf, src=0.0, kappa=0.0, n=20000):
    """Direct quadrature of the Fresnel integral, from its definition (composite 20-point Gauss-Legendre,
    n nodes in total)."""
    t0, w0 = np.polynomial.legendre.leggauss(20)
    npan = max(1, n // 20)
    edges = np.linspace(c - 0.5 * a, c + 0.5 * a, npan + 1)
    h = np.diff(edges)
    xp = (0.5 * (edges[:-1] + edges[1:])[:, None] + 0.5 * h[:, None] * t0[None, :]).ravel()
    wp = (0.5 * h[:, None] * w0[None, :]).ravel()
    if math.isinf(L1):
        U0 = np.exp(1j * (k * math.sin(src) + kappa) * xp)
    else:
        U0 = np.exp(1j * k * (xp - src) ** 2 / (2 * L1)) * np.exp(1j * kappa * xp)
    out = []
    dout = []
    for xx in np.atleast_1d(x):
        ph = np.exp(1j * k * (xx - xp) ** 2 / (2 * z))
        out.append(np.sum(wp * U0 * ph))
        dout.append(np.sum(wp * U0 * ph * 1j * k * (xx - xp) / z))
    return np.array(out), np.array(dout)


print("== 1. closed form vs brute-force quadrature of the Fresnel integral ==")
cases = [
    ("plane wave, normal", dict(L1=math.inf, src=0.0, kappa=0.0)),
    ("plane wave, tilt 1 mrad", dict(L1=math.inf, src=1e-3, kappa=0.0)),
    ("plane wave + kick", dict(L1=math.inf, src=0.0, kappa=4e4)),
    ("point source L1=0.5, xs=30um", dict(L1=0.5, src=30e-6, kappa=0.0)),
    ("point source + kick", dict(L1=0.5, src=-20e-6, kappa=-3e4)),
]
lam, a, z = 632.8e-9, 20e-6, 0.3
k = 2 * math.pi / lam
x = np.linspace(-6e-3, 6e-3, 41)
for name, kw in cases:
    A, dA = fresnel.slit_amplitudes(x, z, k, [50e-6], a, deriv=True, **kw)
    B, dB = brute(x, z, k, 50e-6, a, **kw)
    e1 = np.max(np.abs(A[0] - B)) / np.max(np.abs(B))
    e2 = np.max(np.abs(dA[0] - dB)) / np.max(np.abs(dB))
    print(f"  {name:32s} max|A-A_quad|/max|A| = {e1:.2e}   max|dA-dA_quad|/max|dA| = {e2:.2e}")

print("\n== 2. near field (z = 2a) and electron far field, closed form vs quadrature ==")
for (lam, a, z, xr, lab) in [(632.8e-9, 20e-6, 40e-6, 40e-6, "photon z=2a"),
                             (5.355e-12, 0.1e-6, 1.0, 1.6e-4, "electron 50 keV, z=1 m"),
                             (2.77e-12, 50e-9, 1.25, 1.6e-4, "C60 200 m/s, z=1.25 m")]:
    k = 2 * math.pi / lam
    x = np.linspace(-xr, xr, 31)
    A = fresnel.slit_amplitudes(x, z, k, [0.3 * a], a)
    B, _ = brute(x, z, k, 0.3 * a, a, n=4000)
    print(f"  {lab:28s} rel. err = {np.max(np.abs(A[0] - B)) / np.max(np.abs(B)):.2e}")

print("\n== 3. Parseval: int |A|^2 dx = lambda z a, also with point source and kick ==")
lam, a, z = 1e-6, 20e-6, 0.5
k = 2 * math.pi / lam
x = np.linspace(-0.6, 0.6, 600001)
for kw in [dict(), dict(L1=0.4, src=1e-4), dict(kappa=5e4)]:
    A = fresnel.slit_amplitudes(x, z, k, [0.0], a, **kw)
    flux = float(np.sum(np.abs(A[0]) ** 2) * (x[1] - x[0]))
    print(f"  {str(kw):28s} flux/(lambda z a) = {flux / (lam * z * a):.5f}")
# cross term of two disjoint slits integrates to zero
A = fresnel.slit_amplitudes(x, z, k, [-50e-6, 50e-6], a)
cross = np.sum(A[0] * A[1].conj()) * (x[1] - x[0]) / (lam * z * a)
print(f"  cross term int A1 A2^* dx /(lambda z a) = {abs(cross):.2e}  (0 expected)")

print("\n== 4. RS kernel: sign and magnitude ==")
# (a) wide aperture under a plane wave: on the axis, U must approach exp(ikz)
lam = 1e-6
k = 2 * math.pi / lam
z = 2e-3
U = rs.slit_fields(np.array([0.0]), z, k, [0.0], 0.4e-3, math.inf)[0, 0]
print(f"  wide aperture (0.4 mm, z=2 mm, Fresnel number 80): U_RS(0,z)/exp(ikz) = {U / np.exp(1j * k * z):.4f}"
      "   (expected ~ +1 up to edge ripple)")
# (b) behind a slit in the paraxial regime: RS vs sqrt(k/(2 pi i z)) e^{ikz} A_Fresnel
lam, a, z = 632.8e-9, 20e-6, 0.2
k = 2 * math.pi / lam
x = np.array([0.0, 1e-3, 3e-3])
Ur = rs.slit_fields(x, z, k, [0.0], a, math.inf)[0]
Af = fresnel.slit_amplitudes(x, z, k, [0.0], a)[0] * np.sqrt(k / (2j * math.pi * z)) * np.exp(1j * k * z)
print("  U_RS / (sqrt(k/(2 pi i z)) e^{ikz} A_F) at x = 0, 1, 3 mm:", np.round(Ur / Af, 4))
# (c) analytic: int H1(kR) z/R dx' over the whole line = -2i e^{ikz}/k, so the RS-I kernel must be +(ikz/2) H1/R
print("  analytic: int_R H1^(1)(k sqrt(x^2+z^2)) z/sqrt(x^2+z^2) dx = -2i e^{ikz}/k  ->  RS-I kernel = +(i k z/2) H1/R;")
print("  rs.py uses -(i k z/2) H1/R (docstring and code), i.e. an overall factor -1 (no effect on |U|^2).")

print("\n== 5. Hankel asymptotic branch vs scipy at the switch (x = 1e4 .. 1e5) ==")
xx = np.array([1.0001e4, 2e4, 5e4, 1e5])
for nu in (0, 1):
    sc = special.hankel1(nu, xx)
    big = np.sqrt(2 / (math.pi * xx)) * np.exp(1j * (xx - (2 * nu + 1) * math.pi / 4))
    mu = 4.0 * nu * nu
    t1, t2, t3 = (mu - 1) / (8 * xx), (mu - 1) * (mu - 9) / (2 * (8 * xx) ** 2), (mu - 1) * (mu - 9) * (mu - 25) / (6 * (8 * xx) ** 3)
    asym = big * (1 + 1j * t1 - t2 - 1j * t3)
    # rs._h with forced asymptotic branch
    print(f"  nu={nu}: max rel |asym - scipy| = {np.max(np.abs(asym - sc) / np.abs(sc)):.2e};  "
          f"rs._h(1.0001e4) vs scipy: {abs(rs._h(nu, np.array([1.0001e4]))[0] - sc[0]) / abs(sc[0]):.2e}")
