"""s01: J_z, S_z, L_z per photon (per unit length) of one exact vector beam, three routes.

Route A (independent of the engine's densities and of its quadrature): the radial functions F0, F2, F1 computed here by
scipy.integrate.quad over theta from the module docstring's definitions, then the plane integrals in the circular basis
    W  ~ int (|F0|^2 + |F2|^2 + |F1|^2) r dr,  S_z ~ sigma int (|F0|^2 - |F2|^2) r dr,
    L_z ~ int (l |F0|^2 + (l + 2 sigma) |F2|^2 + (l + sigma) |F1|^2) r dr   (dual-symmetric, pure helicity).
Route B: the engine's closed forms from the spectrum (VortexBeam.moments).
Route C: the engine's densities on a sampled plane (as in tests/test_beams.py::_plane).
Also: Barnett's flux split (as applied to focused beams by Monteiro, Maia Neto & Nussenzveig, arXiv:0902.3214, Eqs.
33-36, 39): spin flux / energy flux * omega = sigma <(1 + c^2)/2> / <c>, from the same radial functions
(int (|F0|^2 + |F2|^2) over int P_z, P_z = (|F0|^2 - |F2|^2)/2), to show that the per-photon split depends on the
definition while J_z = l + sigma does not.
"""
import math
import sys

import numpy as np
from scipy.integrate import quad
from scipy.special import jv

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import beams as B  # noqa: E402

LAM = 1.0
K = 2 * math.pi / LAM


def radial_quad(fn, l, sigma, r, z, th_max):
    """F0, F2, F1 at (r, z) by adaptive quadrature over theta (q = k sin theta, q dq = k^2 s c dtheta)."""
    def comp(order, wfun, part):
        f = lambda th: (fn(K * math.sin(th)) * wfun(th) * jv(order, K * math.sin(th) * r)
                        * K * K * math.sin(th) * math.cos(th))  # noqa: E731
        g = (lambda th: f(th) * math.cos(K * math.cos(th) * z)) if part == 0 else \
            (lambda th: f(th) * math.sin(K * math.cos(th) * z))
        return quad(g, 0.0, th_max, limit=400, epsabs=1e-15, epsrel=1e-12)[0]
    out = []
    for order, wfun in ((l, lambda t: 0.5 * (1 + math.cos(t))), (l + 2 * sigma, lambda t: 0.5 * (1 - math.cos(t))),
                        (l + sigma, lambda t: math.sin(t))):
        out.append(comp(order, wfun, 0) + 1j * comp(order, wfun, 1))
    F0, F2, F1 = out
    F1 = -(1j ** sigma) / math.sqrt(2) * F1
    return F0, F2, F1


def route_a(l, sigma, w0, z=0.0, rmax_w=7.0, nr=500):
    fn, qmax = B.lg_waist_spectrum(0, l, w0)
    fn_s = lambda q: float(fn(np.array([q]))[0])  # noqa: E731
    th_max = math.asin(min(1.0, qmax / K))
    # r up to rmax_w * w0 (or 12 lambda) on Gauss-Legendre nodes
    R = max(rmax_w * w0, 12.0)
    x, wgt = np.polynomial.legendre.leggauss(nr)
    r = 0.5 * R * (x + 1)
    wr = 0.5 * R * wgt
    F = np.array([radial_quad(fn_s, l, sigma, ri, z, th_max) for ri in r])  # (nr, 3)
    a0, a2, a1 = (np.abs(F[:, i]) ** 2 for i in range(3))
    W = np.sum(wr * r * (a0 + a2 + a1))
    S = sigma * np.sum(wr * r * (a0 - a2)) / W
    L = np.sum(wr * r * (l * a0 + (l + 2 * sigma) * a2 + (l + sigma) * a1)) / W
    Pz = 0.5 * np.sum(wr * r * (a0 - a2))
    Wfield = 0.5 * W  # (|E|^2 + |H|^2)/4 = |E|^2/2 for pure helicity
    barnett_spin = sigma * 0.5 * np.sum(wr * r * (a0 + a2)) / Pz  # (sigma/2w) int |E_T|^2 over the flux, times omega
    return {"J": L + S, "S": S, "L": L, "flux_over_energy": Pz / Wfield, "barnett_spin": barnett_spin,
            "barnett_orb": (l + sigma) - barnett_spin}


def route_c(beam, z, n=72, half=5.5):
    x = (np.arange(n) - n // 2) * (2 * half / n)
    X, Y = np.meshgrid(x, x, indexing="ij")
    E, H = beam.fields(X, Y, z)
    Ez, Hz = beam.fields(X, Y, z, deriv_z=True)
    dx = float(x[1] - x[0])
    gE = np.stack([np.stack(B.spectral_gradient(E[i], dx, dx) + (Ez[i],)) for i in range(3)])
    gH = np.stack([np.stack(B.spectral_gradient(H[i], dx, dx) + (Hz[i],)) for i in range(3)])
    return B.angular_momentum(x, x, E, H, gE, gH, K)


def barnett_closed(beam):
    th, wt = B._nodes(0.0, beam.theta_max, 400)
    s, c = np.sin(th), np.cos(th)
    w = np.abs(np.asarray(beam.spectrum(K * s), complex)) ** 2 * s * c * wt
    return float(np.sum(w * (1 + c * c) / 2) / np.sum(w * c))


for l, sigma, w0, half, n in [(2, 1, 1.2, 5.5, 72), (3, 1, 1.5, 7.0, 96), (1, -1, 0.6, 10.0, 128)]:
    fn, qmax = B.lg_waist_spectrum(0, l, w0)
    beam = B.VortexBeam(l, K, fn, qmax, {sigma: 1.0})
    ref = beam.moments()
    a = route_a(l, sigma, w0)
    c = route_c(beam, 0.0, n, half)
    bc = sigma * barnett_closed(beam)
    print(f"--- l = {l}, sigma = {sigma:+d}, w0 = {w0} lambda (spectrum at q = k / max: "
          f"{abs(float(fn(np.array([K]))[0])) / np.max(np.abs(fn(np.linspace(0, K, 4001)))):.2e})")
    print(f"  B closed forms : J = {ref['J']:.10f}  S = {ref['S']:.10f}  L = {ref['L']:.10f}  <cos> = {ref['cos_mean']:.10f}")
    print(f"  A own quadrature: J = {a['J']:.10f}  S = {a['S']:.10f}  L = {a['L']:.10f}  flux/W = {a['flux_over_energy']:.10f}")
    print(f"  C engine plane : J = {c['J']:.10f}  S = {c['S']:.10f}  L = {c['L']:.10f}  flux_J = {c['flux_J']:.10f}"
          f"  (window +-{half}, n = {n})")
    print(f"  |A - B|: S {abs(a['S'] - ref['S']):.1e}, L {abs(a['L'] - ref['L']):.1e};  |C - B|: S {abs(c['S'] - ref['S']):.1e}")
    print(f"  Barnett flux split (Monteiro et al. 2009 Eqs. 33-36): spin = {a['barnett_spin']:.6f} (closed form "
          f"sigma<(1+c^2)/2>/<c> = {bc:.6f}), orbital = {a['barnett_orb']:.6f}")
    print(f"     -> per-unit-length canonical split: S - sigma = {ref['S'] - sigma:+.4f};  Barnett flux split: "
          f"spin - sigma = {a['barnett_spin'] - sigma:+.4f} (opposite sign)")
