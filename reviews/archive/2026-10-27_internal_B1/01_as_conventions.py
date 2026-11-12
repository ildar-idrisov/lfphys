# Review B1, script 01: conventions of the N-D angular spectrum (CPU, fp64).
#  (a) the grid convention x_i = (i - n//2) d for propagate_slice at an absolute position, even and odd n, pad 1 and 2,
#      against the volume column and against an independent reference (off-axis Gaussian by Hankel quadrature, mpmath);
#  (b) the slice between grid nodes against the same independent reference (a band-limited field);
#  (c) the slice between nodes for a sharp-edged aperture near z = 0 (Gibbs ringing of the trigonometric interpolant);
#  (d) negative z (back-propagation) with evanescent content.
import math
import sys

import mpmath as mp
import numpy as np

from lfphys.core.optics import angular_spectrum as AS

LAM = 1.0
K = 2 * math.pi / LAM


def gauss_field(w, x0, y0, rho_x, rho_y, z):
    """U(x, y, z) for U(x, y, 0) = exp(-((x-x0)^2+(y-y0)^2)/w^2): (w^2/2) int q e^{-q^2 w^2/4} J0(q rho) e^{i kz z} dq,
    rho = distance from (x0, y0); mpmath quadrature, no FFT."""
    mp.mp.dps = 25
    k, W, Z = mp.mpf(K), mp.mpf(w), mp.mpf(z)
    rho = mp.sqrt(mp.mpf(rho_x - x0) ** 2 + mp.mpf(rho_y - y0) ** 2)
    f1 = lambda q: q * mp.exp(-q * q * W * W / 4) * mp.besselj(0, q * rho) * mp.expj(Z * mp.sqrt(k * k - q * q))
    f2 = lambda q: q * mp.exp(-q * q * W * W / 4) * mp.besselj(0, q * rho) * mp.exp(-Z * mp.sqrt(q * q - k * k))
    return complex(W * W / 2 * (mp.quad(f1, [0, k / 2, k]) + mp.quad(f2, [k, 2 * k, mp.inf])))


print("(a) grid convention of propagate_slice at an absolute position; Gaussian w = 1.2, centred at (0.31, -0.17)")
w, x0, y0, z = 1.2, 0.31, -0.17, 2.0
for n in (64, 65):
    dx = LAM / 6
    x = (np.arange(n) - n // 2) * dx  # the convention stated in the module docstring
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / w ** 2)
    for pad in (1, 2):
        vol = AS.propagate_volume(U0, dx, K, [z], pad=pad, check=True)[0]
        s = AS.propagate_slice(U0, dx, K, [z], axis=0, at=0.0, pad=pad, check=True)[0]  # plane x = 0: field across y
        col = vol[n // 2, :]  # x = x[n//2] = 0 by the stated convention
        j = n // 2 + 2
        ref = gauss_field(w, x0, y0, 0.0, x[j], z)
        print(f"  n={n} pad={pad}: max|slice(x=0) - volume[x index n//2]| = {np.max(np.abs(s - col)):.2e};"
              f"  |slice - ref| at y={x[j]:+.3f}: {abs(s[j] - ref):.2e};  |volume - ref|: {abs(col[j] - ref):.2e}")

print("\n(b) slice between nodes against the independent reference (n = 64, pad = 2)")
n, dx = 64, LAM / 6
x = (np.arange(n) - n // 2) * dx
X, Y = np.meshgrid(x, x, indexing="ij")
U0 = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / w ** 2)
for frac in (0.0, 0.25, 0.5, 0.77):
    at = 0.4 + frac * dx
    s = AS.propagate_slice(U0, dx, K, [z], axis=0, at=at, pad=2, check=True)[0]
    errs = [abs(s[j] - gauss_field(w, x0, y0, at, x[j], z)) for j in (n // 2 - 3, n // 2, n // 2 + 4)]
    print(f"  at = 0.4 + {frac:.2f} dx: max error over 3 points = {max(errs):.2e}")

print("\n(c) slice between nodes, sharp edge (slit |x| <= 1, 8x8 sub-pixel coverage as v08), z = 0 and z = 0.25 lambda")
n, dx = 128, LAM / 4
x = (np.arange(n) - n // 2) * dx
sub = (np.arange(8) + 0.5) / 8 - 0.5
X, Y = np.meshgrid(x, x, indexing="ij")
cov = np.zeros(X.shape)
for sx in sub:
    for sy in sub:
        cov += (np.abs(X + sx * dx) <= 1.0) & (np.abs(Y + sy * dx) <= 4.0)
U0 = (cov / 64).astype(complex)
for z in (0.0, 0.25, 1.0):
    for at in (0.5 * dx, 1.0 + 0.5 * dx, 1.0 + 1.5 * dx):  # inside the slit; just outside its edge
        s = AS.propagate_slice(U0, dx, K, [z], axis=0, at=at, pad=2, check=True)[0]
        # a finer grid (half the step, same window) evaluated at the node x = at where possible
        xf = (np.arange(2 * n) - n) * dx / 2
        Xf, Yf = np.meshgrid(xf, xf, indexing="ij")
        covf = np.zeros(Xf.shape)
        for sx in sub:
            for sy in sub:
                covf += (np.abs(Xf + sx * dx / 2) <= 1.0) & (np.abs(Yf + sy * dx / 2) <= 4.0)
        sf = AS.propagate_slice((covf / 64).astype(complex), dx / 2, K, [z], axis=0, at=at, pad=2, check=True)[0]
        print(f"  z={z:4.2f} at={at:6.3f}: |U| on the y = 0 line: grid n {abs(s[n // 2]):.4f}, grid 2n {abs(sf[n]):.4f}"
              f"  (difference {abs(s[n // 2] - sf[n]):.2e})")

print("\n(d) negative z with evanescent content (the slit above, z = -1 lambda)")
u = AS.propagate_field(U0, dx, K, -1.0, pad=2, check=True)
print(f"  max|U(z=-1)| = {np.max(np.abs(u)):.3e} (|U(0)| <= 1); no error raised")
sys.stdout.flush()
