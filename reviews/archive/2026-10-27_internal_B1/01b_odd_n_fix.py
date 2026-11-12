# Review B1, script 01b: the suggested fix for odd n (place sample i at buffer index m//2 - n//2 + i), tried on a copy
# of the slice route (the engine is not modified): n = 65, pad 2, against the independent Hankel reference of script 01.
import math

import numpy as np

import mpmath as mp

K = 2 * math.pi
def gauss_field(w, x0, y0, rx, ry, z):
    mp.mp.dps = 25
    k, W, Z = mp.mpf(K), mp.mpf(w), mp.mpf(z)
    rho = mp.sqrt(mp.mpf(rx - x0) ** 2 + mp.mpf(ry - y0) ** 2)
    f1 = lambda q: q * mp.exp(-q * q * W * W / 4) * mp.besselj(0, q * rho) * mp.expj(Z * mp.sqrt(k * k - q * q))
    f2 = lambda q: q * mp.exp(-q * q * W * W / 4) * mp.besselj(0, q * rho) * mp.exp(-Z * mp.sqrt(q * q - k * k))
    return complex(W * W / 2 * (mp.quad(f1, [0, k / 2, k]) + mp.quad(f2, [k, 2 * k, mp.inf])))

def slice_fixed(U0, dx, k, z, at, pad=2):
    n = U0.shape[0]
    m = int(2 ** math.ceil(math.log2(n * pad)))
    off = m // 2 - n // 2  # the fix (the engine has (m - n) // 2)
    buf = np.zeros((m, m), complex)
    buf[off:off + n, off:off + n] = U0
    kk = 2 * math.pi * np.fft.fftfreq(m, dx)
    KX, KY = np.meshgrid(kk, kk, indexing="ij")
    kz = np.sqrt((k * k - KX ** 2 - KY ** 2).astype(complex)); kz = np.where(kz.imag < 0, -kz, kz)
    B = np.fft.fftn(np.fft.ifftshift(buf)) * np.exp(1j * kz * z)
    C = np.fft.fftshift(np.fft.ifft(B, axis=1), axes=1)
    line = C.T @ (np.exp(1j * kk * at) / m)
    return line[off:off + n]

w, x0, y0, z, n, dx = 1.2, 0.31, -0.17, 2.0, 65, 1 / 6
x = (np.arange(n) - n // 2) * dx
X, Y = np.meshgrid(x, x, indexing="ij")
U0 = np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / w ** 2)
s = slice_fixed(U0, dx, K, z, 0.0)
j = n // 2 + 2
print(f"n = 65, pad 2, fixed offset: |slice(x=0) - ref| at y = {x[j]:+.3f}: {abs(s[j] - gauss_field(w, x0, y0, 0.0, x[j], z)):.1e}")
