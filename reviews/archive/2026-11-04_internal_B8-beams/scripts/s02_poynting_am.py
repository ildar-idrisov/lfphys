"""s02: the Poynting angular momentum per unit length, int (r x P)_z dA per photon, of the exact vector beam.

The author's identity int (r x P)_z dA = L_z + S_z + (1/2) d/dz int r.S_T dA is checked at several planes, including
the waist z = 0. A closed form derived for this review (pure helicity, real spectrum A):
  S = sigma P / omega pointwise (Bliokh, Bekshaev & Nori 2013, Eq. 3.50), so int r.S_T dA = (sigma/omega) int r.P_T dA;
  div P = 0 gives int r.P_T dA = (1/2) d/dz int r^2 P_z dA; with P_z = (|F0|^2 - |F2|^2)/2 and the Hankel-space form of
  int r^2 |F|^2 dA, d^2/dz^2 int r^2 P_z dA = int tan^2(theta) (|a|^2 - |b|^2) d^2k = int tan^2(theta) cos(theta) |A|^2 d^2k,
  so per photon:  J_Poynting = l + sigma + (sigma/2) <sin^2(theta)/cos(theta)>   (<> over |A|^2 q dq), independent of z.
"""
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import beams as B  # noqa: E402
from lfphys.theories.approx import beams_paraxial as PX  # noqa: E402

K = 2 * math.pi


def plane(beam, z, n, half):
    x = (np.arange(n) - n // 2) * (2 * half / n)
    X, Y = np.meshgrid(x, x, indexing="ij")
    E, H = beam.fields(X, Y, z)
    Ez, Hz = beam.fields(X, Y, z, deriv_z=True)
    dx = float(x[1] - x[0])
    gE = np.stack([np.stack(B.spectral_gradient(E[i], dx, dx) + (Ez[i],)) for i in range(3)])
    gH = np.stack([np.stack(B.spectral_gradient(H[i], dx, dx) + (Hz[i],)) for i in range(3)])
    return B.angular_momentum(x, x, E, H, gE, gH, K)


def closed(beam, sigma):
    th, wt = B._nodes(0.0, beam.theta_max, 400)
    s, c = np.sin(th), np.cos(th)
    w = np.abs(np.asarray(beam.spectrum(K * s), complex)) ** 2 * s * c * wt
    return beam.l + sigma + 0.5 * sigma * float(np.sum(w * s * s / c) / np.sum(w))


for l, sigma, w0, n, half, zs in [(2, 1, 1.2, 72, 5.5, 'all'), (3, 1, 1.5, 96, 7.0, 'waist'), (2, -1, 1.2, 72, 5.5, 'waist')]:
    fn, qmax = B.lg_waist_spectrum(0, l, w0)
    beam = B.VortexBeam(l, K, fn, qmax, {sigma: 1.0})
    zr = PX.rayleigh(K, w0)
    ref = closed(beam, sigma)
    print(f"--- l = {l}, sigma = {sigma:+d}, w0 = {w0} lambda, z_R = {zr:.3f}: closed form J_P = {ref:.8f}")
    for z in ((0.0, 0.4, zr) if zs == 'all' else (0.0,)):  # 2 z_R dropped: the direct route is slow there (>10 min)
        h = 0.05
        hz = max(half, 5.0 * float(PX.params(z, K, w0)[0]))
        nz = int(2 * math.ceil(hz * 6))
        a, m, b = plane(beam, z - h, nz, hz), plane(beam, z, nz, hz), plane(beam, z + h, nz, hz)
        drS = (b["rS"] - a["rS"]) / (2 * h)
        lhs = m["J_poynting"]
        rhs = m["Lz"] + m["Sz"] + 0.5 * drS
        print(f"  z = {z:7.3f}: J_P/photon = {m['J_poynting_per_photon']:.8f}  (closed {ref:.8f}, diff {m['J_poynting_per_photon'] - ref:+.1e});"
              f"  (1/2) d/dz int r.S_T per photon = {0.5 * drS * K / m['W']:+.6f};  identity residual {abs(lhs - rhs) / abs(lhs):.1e}"
              f"  (window +-{hz:.2f}, n = {nz})")
