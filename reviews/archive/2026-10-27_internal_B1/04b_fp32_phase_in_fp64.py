# Review B1, script 04b: where the fp32 error comes from. The double slit at lam = 0.3 um, z = 80 um (n = 256, pad 4):
# (1) as the kernel does it (k_z cast to complex64, the phase k_z z formed in fp32), (2) the phase factor
# exp(i k_z z) formed in fp64 and only then cast to complex64, the FFTs in fp32 as before.
import math

import numpy as np

from v08_wave_3d.viz import SCHEMA, _aperture

p, _ = SCHEMA.resolve("double", {"lam": 0.3, "zmax": 80.0})
lam, n, z = 0.3, 256, 80.0
dx = lam / 4
k = 2 * math.pi / lam
x = (np.arange(n) - n // 2) * dx
U0 = _aperture(p, x)
m = 1024
buf = np.zeros((m, m), complex)
o = (m - n) // 2
buf[o:o + n, o:o + n] = U0
kk = 2 * math.pi * np.fft.fftfreq(m, dx)
KX, KY = np.meshgrid(kk, kk, indexing="ij")
kz = np.sqrt((k * k - KX ** 2 - KY ** 2).astype(complex))
kz = np.where(kz.imag < 0, -kz, kz)
ref = np.fft.ifft2(np.fft.fft2(np.fft.ifftshift(buf)) * np.exp(1j * kz * z))
A32 = np.fft.fft2(np.fft.ifftshift(buf).astype(np.complex64))
u1 = np.fft.ifft2(A32 * np.exp(1j * kz.astype(np.complex64) * np.float32(z)))
u2 = np.fft.ifft2(A32 * np.exp(1j * kz * z).astype(np.complex64))
for lab, u in (("phase in fp32 (as the kernel)", u1), ("phase in fp64, cast", u2)):
    print(f"{lab:32s}: dtype {u.dtype}, max|U32 - U64| / max|U64| = {np.max(np.abs(u - ref)) / np.max(np.abs(ref)):.1e}")
