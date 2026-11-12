# Review of the B1 corrections (reviewer's script). propagate_current: j = Im(U* grad U)/k and P(z).
# (a) two interfering plane waves (closed form, periodic window); (b) propagating + evanescent parts (closed form);
# (c) the Gaussian against the derivatives of the exact Hankel integral, near the source and off the axis;
# (d) is the conservation check informative? P(z) for a world whose window is far too small (field wrong by O(1)), and
#     P against the continuous closed form of the power (independent of the grid);
# (e) the band-limited sum: P(z) falls with z.
import argparse
import math
import sys

import numpy as np
from scipy.integrate import quad

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/02_current.txt")
backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
LAM = 1.0
K = 2 * math.pi / LAM
n, dx = 64, LAM / 4
L = n * dx
x = (np.arange(n) - n // 2) * dx
X, Y = np.meshgrid(x, x, indexing="ij")

out("(a) two plane waves, window periodic (pad 1): j = [k1 + |a|^2 k2 + (k1 + k2) Re(a e^{i(k2-k1).r})]/k")
q1 = np.array([2 * math.pi * 3 / L, -2 * math.pi * 1 / L])
q2 = np.array([-2 * math.pi * 5 / L, 2 * math.pi * 2 / L])
a = 0.6 * np.exp(0.7j)
k1 = np.array([*q1, math.sqrt(K * K - q1 @ q1)])
k2 = np.array([*q2, math.sqrt(K * K - q2 @ q2)])
U0 = np.exp(1j * (q1[0] * X + q1[1] * Y)) + a * np.exp(1j * (q2[0] * X + q2[1] * Y))
zs = [0.0, 0.37, 2.9]
j, P = AS.propagate_current(U0, dx, K, zs, pad=1, check=True)
worst = 0.0
for iz, z in enumerate(zs):
    ph = (k2[0] - k1[0]) * X + (k2[1] - k1[1]) * Y + (k2[2] - k1[2]) * z
    ref = [(k1[c] + abs(a) ** 2 * k2[c] + (k1[c] + k2[c]) * np.real(a * np.exp(1j * ph))) / K for c in range(3)]
    worst = max(worst, max(np.max(np.abs(j[iz, c] - ref[c])) for c in range(3)))
Pref = (k1[2] + abs(a) ** 2 * k2[2]) / K * L * L
out(f"   max |j - closed form| = {worst:.2e}; P(z) = {P}, closed form {Pref:.6f}, rel {np.max(np.abs(P - Pref)) / Pref:.1e}")

out("(b) propagating + evanescent: U0 = 1 + b cos(q x), q = 1.5 k (evanescent, kappa = sqrt(q^2 - k^2))")
q = 2 * math.pi * round(1.5 * L / LAM) / L
kap = math.sqrt(q * q - K * K)
b = 0.8
U0 = 1.0 + b * np.cos(q * X)
zs = [0.0, 0.05, 0.2, 1.0]
j, P = AS.propagate_current(U0, dx, K, zs, pad=1, check=True)
worst = 0.0
for iz, z in enumerate(zs):
    c = b * np.cos(q * X) * math.exp(-kap * z)
    jz = 1.0 + c * (kap * math.sin(K * z) + K * math.cos(K * z)) / K
    jx = (b * q * np.sin(q * X) * math.exp(-kap * z) * math.sin(K * z)) / K  # Im(U* dU/dx)/k, U = e^{ikz} + c
    worst = max(worst, np.max(np.abs(j[iz, 2] - jz)), np.max(np.abs(j[iz, 0] - jx)), np.max(np.abs(j[iz, 1])))
out(f"   q/k = {q / K:.3f}; max |j - closed form| over z = {zs}: {worst:.2e}; P(z)/L^2 = {P / L / L} (closed form 1)")

out("(c) Gaussian w = 0.8: j against Im(U* dU)/k from the exact Hankel integral and its exact derivatives")
n2, dx2, w = 128, LAM / 6, 0.8
x2 = (np.arange(n2) - n2 // 2) * dx2
src = AS.Spectral((n2, n2), AF.gaussian_spectrum(w))
for z in (0.05, 0.4, 3.0):
    j, _ = AS.propagate_current(src, dx2, K, [z], pad=16, check=True)
    worst = 0.0
    for i in (n2 // 2, n2 // 2 + 3, n2 // 2 - 9, n2 // 2 + 20):
        r = abs(x2[i])
        U = AF.gaussian_field(K, w, z, r)[0]
        dz = AF.gaussian_field(K, w, z, r, deriv="z")[0]
        dr = AF.gaussian_field(K, w, z, r, deriv="r")[0]
        jz = (np.conj(U) * dz).imag / K
        jr = (np.conj(U) * dr).imag / K * np.sign(x2[i])
        worst = max(worst, abs(j[0, 2, i, n2 // 2] - jz), abs(j[0, 0, i, n2 // 2] - jr))
    out(f"   z = {z}: max |j - exact| = {worst:.2e} (j_z on axis {j[0, 2, n2 // 2, n2 // 2]:.6f}); "
        f"j_r sign: outward {bool(j[0, 0, n2 // 2 + 20, n2 // 2] > 0)} (a diverging beam at z = {z})")

out("(d) is the check 'power conserved' informative?")
w = 0.35  # a waist below lambda: light at wide angles
src = AS.Spectral((n2, n2), AF.gaussian_spectrum(w))
zs = [0.5, 5.0, 20.0, 40.0]
for pad in (1, 2, 16):
    jz, P = AS.propagate_current(src, dx2, K, zs, pad=pad, check=True)
    ref = AS.flux_of_spectrum(src, dx2, K, pad=pad)
    Uw = AS.propagate_field(src, dx2, K, zs[-1], pad=16, check=True)
    U = AS.propagate_field(src, dx2, K, zs[-1], pad=pad, check=True)
    err = np.max(np.abs(U - Uw)) / np.max(np.abs(Uw))
    out(f"   pad {pad:2d}: field at z = {zs[-1]} off by {err:.2e} of its peak (vs pad 16); "
        f"max|P(z) - flux_of_spectrum|/P = {np.max(np.abs(P - ref)) / ref:.1e}  -> check 'ok'")
# the continuous closed form: P = (1/k) int Re k_z |A(q)|^2 d^2q/(2 pi)^2, A = pi w^2 exp(-q^2 w^2/4)
Pc = (1 / K) * (math.pi * w * w) ** 2 / (2 * math.pi) * quad(
    lambda qq: math.sqrt(K * K - qq * qq) * math.exp(-qq * qq * w * w / 2) * qq, 0, K, limit=200)[0]
for pad in (1, 2, 16):
    Pd = AS.flux_of_spectrum(src, dx2, K, pad=pad)
    out(f"   pad {pad:2d}: P (discrete, the check's reference) = {Pd:.10f}; continuous closed form {Pc:.10f}; "
        f"rel {abs(Pd - Pc) / Pc:.1e}")
out("   (the identity P(z) = const holds for any spectrum on any window: sum_x Im(U* dU/dz) = (1/M) sum_q Re k_z |B_q|^2"
    " and |B_q| = |A_q| for propagating q)")

out("(e) the band-limited sum: P(z) / P(0)")
src = AS.Spectral((n2, n2), AF.rect_spectrum([(-0.5, 0.5, -0.5, 0.5)]))
j, P = AS.propagate_current(src, dx2, K, [0.0, 2.0, 10.0, 40.0], pad=2, check=True, band_limit=True)
out(f"   {np.round(P / P[0], 5)}")
out("done")
