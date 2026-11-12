# Review B8-mie, script s06c: the period in x of the ripple of |S1|^2 + |S2|^2 (mie_poly's docstring and v17's README:
# "a period ~1.5 in x"), at 140 deg (bow side) and 175, 180 deg (glory), water m = 1.3354, x in [1000, 1060], by FFT;
# the strongest spectral lines and what dx = 0.25 gives (nodes per period).
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie  # noqa: E402
m = 1.3354
xs = np.arange(1000.0, 1060.0, 0.02)
A, B = mie.coefficients_batch(m, xs)
th = np.radians([140.0, 175.0, 180.0])
S1, S2 = mie.amplitudes_batch(A, B, th)
I = np.abs(S1) ** 2 + np.abs(S2) ** 2
for k, t in enumerate((140, 175, 180)):
    y = I[:, k] - I[:, k].mean()
    F = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    f = np.fft.rfftfreq(len(y), d=0.02)
    top = np.argsort(F)[-4:][::-1]
    print(f"theta = {t} deg: strongest periods in x {[round(1 / f[j], 3) for j in top if f[j] > 0]} (relative power "
          f"{[round(float(F[j] / F[top[0]]), 2) for j in top]})")
print("2 pi/(4 m) =", round(2 * np.pi / (4 * m), 3), "(p = 0 against p = 2 on the axis); dx = 0.25 -> nodes per period 1.2: ",
      round(1.2 / 0.25, 1))
