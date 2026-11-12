# Review B1, script 11b: which reference is right for lam = 0.3, w = 0.5, z = 80 (v08's mpmath quadrature or composite
# Gauss-Legendre)? GL with 4000 and 16000 panels, mpmath at dps 25 (as v08) and with quadosc-free higher degree.
import math

import mpmath as mp
import numpy as np

from lfphys.core.optics import angular_spectrum as AS
from v08_wave_3d.viz import _gauss_on_axis

def ref_gl(lam, w, z, panels, order=20):
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

lam, w, z, n = 0.3, 0.5, 80.0, 256
k = 2 * math.pi / lam
dx = lam / 4
x = (np.arange(n) - n // 2) * dx
X, Y = np.meshgrid(x, x, indexing="ij")
U = AS.propagate_field(np.exp(-(X**2 + Y**2) / w**2).astype(complex), dx, k, z, pad=4, check=True)[n // 2, n // 2]
U16 = AS.propagate_field(np.exp(-(X**2 + Y**2) / w**2).astype(complex), dx, k, z, pad=16, check=True)[n // 2, n // 2]
g1, g2 = ref_gl(lam, w, z, 4000), ref_gl(lam, w, z, 16000)
m25 = _gauss_on_axis(lam, w, z)
mp.mp.dps = 25
K, W, Z = 2 * mp.pi / mp.mpf(lam), mp.mpf(w), mp.mpf(z)
f1 = lambda q: q * mp.exp(-q * q * W * W / 4) * mp.expj(Z * mp.sqrt(K * K - q * q))
f2 = lambda q: q * mp.exp(-q * q * W * W / 4) * mp.exp(-Z * mp.sqrt(q * q - K * K))
pts = [K * j / 64 for j in range(65)]
mfine = complex(W * W / 2 * (mp.quad(f1, pts) + mp.quad(f2, [K, 2 * K, mp.inf])))
print(f"GL 4000 vs GL 16000 panels: {abs(g1 - g2) / abs(g2):.1e}")
print(f"mpmath split at k/2, k (v08) vs GL: {abs(m25 - g2) / abs(g2):.1e}")
print(f"mpmath split into 64 panels on [0, k] vs GL: {abs(mfine - g2) / abs(g2):.1e}")
print(f"FFT route (pad 4) vs GL: {abs(U - g2) / abs(g2):.1e};  vs v08's reference: {abs(U - m25) / abs(m25):.1e}")
print(f"FFT route (pad 16) vs GL: {abs(U16 - g2) / abs(g2):.1e}")
