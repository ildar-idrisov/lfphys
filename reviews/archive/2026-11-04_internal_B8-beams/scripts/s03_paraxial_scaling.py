"""s03: the paraxial error.

(a) Scalar: the exact Rayleigh-Sommerfeld field of the LG_{1,2} waist (computed here by scipy.integrate.quad over q of
    A(q) J_l(q r) exp(i k_z z) q dq, independent of the engine's composite quadrature; the engine's VortexBeam.scalar
    alongside) against the paraxial closed form PX.lg at z = z_R, for w0 = 1.5, 3, 6 lambda: the largest difference over
    r in [0, 3 w(z)], relative to the peak, should fall as (lambda/w0)^2 (ratio 4 per doubling).
(b) Vector: the exact vector beam (helicity sigma) against LG x e_sigma at the waist (what v16's information check
    'parax' compares, viz.py:382-390): its largest difference over all three components and over the transverse ones
    only. v16's note says it grows as (lambda/w0)^2; the longitudinal field E_z is of first order in lambda/w0.
"""
import math
import sys

import numpy as np
from scipy.integrate import quad
from scipy.special import jv

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import beams as B  # noqa: E402
from lfphys.theories.approx import beams_paraxial as PX  # noqa: E402

K = 2 * math.pi


def rs_quad(fn, l, r, z, qmax):
    def part(fun):
        return quad(lambda q: float(fn(np.array([q]))[0]) * jv(l, q * r) * q * fun(math.sqrt(K * K - q * q) * z),
                    0.0, min(qmax, K), limit=500, epsabs=1e-14, epsrel=1e-12)[0]
    return part(math.cos) + 1j * part(math.sin)


print("(a) scalar exact (RS) vs paraxial LG_{1,2} at z = z_R")
prev = None
p, l = 1, 2
for w0 in (1.5, 3.0, 6.0):
    fn, qmax = B.lg_waist_spectrum(p, l, w0)
    zr = PX.rayleigh(K, w0)
    wz = float(PX.params(zr, K, w0)[0])
    r = np.linspace(0.0, 3.0 * wz, 61)
    ex = np.array([rs_quad(fn, l, ri, zr, qmax) for ri in r])
    eng = B.VortexBeam(l, K, fn, qmax).scalar(r, zr)
    par = PX.lg(p, l, r, 0 * r, zr, K, w0) * np.exp(1j * K * zr)
    pk = np.max(np.abs(par))
    d = float(np.max(np.abs(ex - par)) / pk)
    print(f"  w0 = {w0:4.1f}: max|exact - paraxial|/peak = {d:.4e}   (engine RS vs own quad: {np.max(np.abs(eng - ex)) / pk:.1e})"
          + (f"   ratio to previous = {prev / d:.3f}" if prev else ""))
    prev = d

print("(b) vector beam (sigma = +1) vs LG_{0,3} e_sigma at the waist z = 0 (v16's check 'parax')")
prev = None
for w0 in (1.5, 3.0, 6.0):
    fn, qmax = B.lg_waist_spectrum(0, 3, w0)
    beam = B.VortexBeam(3, K, fn, qmax, {1: 1.0})
    r = np.linspace(0.0, 3.0 * w0, 120)
    E = beam.fields(r, 0 * r, 0 * r)[0]
    par = PX.lg(0, 3, r, 0 * r, 0.0, K, w0)[None] * (np.array([1, 1j, 0]) / math.sqrt(2))[:, None]
    pk = np.max(np.abs(par))
    d_all = float(np.max(np.abs(E - par)) / pk)
    d_t = float(np.max(np.abs(E[:2] - par[:2])) / pk)
    ez = float(np.max(np.abs(E[2])) / pk)
    print(f"  w0 = {w0:4.1f}: all components {d_all:.4e}, transverse only {d_t:.4e}, max|E_z|/peak {ez:.4e}"
          + (f"   ratios: all {prev[0] / d_all:.2f}, transverse {prev[1] / d_t:.2f}" if prev else ""))
    prev = (d_all, d_t)
