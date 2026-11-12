"""s04: the rotational Doppler shifts from sampled series built here (own rotation, own mirror, own rough surface, own
FFT on exact bins), not with beams_rotation's sample_rotating / image_rotator / SpinningSurface / peak_frequency.

Convention of the engine: fields ~ exp(-i omega t), Omega > 0 counter-clockwise about +z. A series exp(-i w t) has its
line at +w. The sampling is chosen so that every expected line falls on an FFT bin; the measured frequency is the bin
of the largest |FFT|.
(a) An observer co-rotating at Omega (position and axes) in the exact vector beam l, sigma: expected omega - (l+sigma) Omega.
(b) A beam mirrored across a line turning at Omega_p (an image rotator, a Dove prism at Omega_p): scalar l -> -l,
    expected omega - 2 l Omega_p; mirror-like vector rotator: omega - 2 (l + sigma) Omega_p.
(c) Lavery et al.: a rough phase screen exp(i h(r, phi - Omega t)) (own random Fourier series), incident LG_{0,l}; the
    on-axis amplitude int U rho dA: expected omega - l Omega; incident +l through a +-l mode filter: beat 2|l|Omega.
"""
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import beams as B  # noqa: E402
from lfphys.theories.approx import beams_paraxial as PX  # noqa: E402

K = 2 * math.pi


def line(series, dt):
    """Angular frequency of the largest line, physics convention (exp(-i w t) -> +w)."""
    n = len(series)
    F = np.fft.ifft(series) * n  # sum_j v_j exp(+i 2 pi k j / n)
    f = 2 * math.pi * np.fft.fftfreq(n, dt)
    return float(f[int(np.argmax(np.abs(F)))])


# (a) rotating observer ------------------------------------------------------------------------------------------------
Omega = 2 * math.pi * 1.0          # one turn per unit time
n = 256
dt = 1.0 / n                       # one turn sampled 256 times: lines on multiples of Omega
omega = 2 * math.pi * 40.0         # an 'optical' frequency on a bin
t = np.arange(n) * dt
print("(a) observer co-rotating at Omega in the exact vector Bessel beam: measured (omega - line)/Omega")
for l, s in [(2, 1), (3, -1), (-1, 1), (0, -1), (2, -1)]:
    a = Omega * t
    x, y = 0.43 * np.cos(0.2 + a), 0.43 * np.sin(0.2 + a)
    E = B.vector_bessel_beam(l, s, K, 0.7, x, y, 0.3 + 0 * x)[0]
    # components in the observer's co-rotating axes (its x' axis along (cos a, sin a))
    Ex = np.cos(a) * E[0] + np.sin(a) * E[1]
    ser = Ex * np.exp(-1j * omega * t)
    w = line(ser, dt)
    print(f"  l = {l:+d}, sigma = {s:+d}: (omega - w)/Omega = {(omega - w) / Omega:+.6f}   expected l + sigma = {l + s:+d}")

# (b) image rotator ---------------------------------------------------------------------------------------------------
print("(b) image rotator (mirror across the line at angle Omega_p t): measured (w - omega)/(2 Omega_p)")
Op = 2 * math.pi * 1.0
for l, s in [(2, 1), (3, -1), (1, 1)]:
    x0, y0 = 0.31, 0.22
    a = Op * t
    c2, s2 = np.cos(2 * a), np.sin(2 * a)
    xm, ym = c2 * x0 + s2 * y0, s2 * x0 - c2 * y0     # the mirrored point
    Es = B.bessel_beam(l, K, 0.5, xm, ym, 0 * xm)      # scalar rotator
    ws = line(Es * np.exp(-1j * omega * t), dt)
    Ev = B.vector_bessel_beam(l, s, K, 0.5, xm, ym, 0 * xm)[0]
    Evx = c2 * Ev[0] + s2 * Ev[1]                      # mirrored components M E(M r)
    wv = line(Evx * np.exp(-1j * omega * t), dt)
    print(f"  l = {l:+d}, sigma = {s:+d}: scalar {(ws - omega) / (2 * Op):+.6f} (expected -l = {-l:+d});"
          f"  vector {(wv - omega) / (2 * Op):+.6f} (expected -(l+sigma) = {-(l + s):+d})")

# (c) spinning rough surface ------------------------------------------------------------------------------------------
print("(c) spinning rough phase screen (own Fourier-series surface), on-axis amplitude and +-l filter")
rng = np.random.default_rng(12)
NH = 24
coef = rng.normal(size=(NH, 3)) / (1 + np.arange(NH))[:, None]
phs = rng.uniform(0, 2 * math.pi, (NH, 3))


def height(r, ph):
    out = np.zeros_like(r)
    for m in range(NH):
        radial = coef[m, 0] + coef[m, 1] * r + coef[m, 2] * r * r
        out += radial * np.cos(m * ph + phs[m, 0])
    return out


nr, nphi = 48, 256
gx, gw = np.polynomial.legendre.leggauss(nr)
R = 3.5
r = 0.5 * R * (gx + 1)
wr = 0.5 * R * gw * r
phi = 2 * math.pi * np.arange(nphi) / nphi
Rg, Pg = np.meshgrid(r, phi, indexing="ij")
W = wr[:, None] * (2 * math.pi / nphi)
for l in (3, -2):
    U = PX.lg(0, l, Rg * np.cos(Pg), Rg * np.sin(Pg), 0.0, K, 1.0)
    g = np.abs(U)
    amp, beat = [], []
    for tt in t:
        rho = np.exp(1j * height(Rg, Pg - Omega * tt))  # the surface turned by Omega t (counter-clockwise)
        amp.append(np.sum(W * U * rho))
        D = g * (np.exp(1j * l * Pg) + np.exp(-1j * l * Pg)) / math.sqrt(2)
        beat.append(abs(np.sum(W * np.conj(D) * U * rho)) ** 2)
    amp = np.array(amp)
    beat = np.array(beat)
    w_shift = line(amp, dt)
    F = np.abs(np.fft.rfft(beat - beat.mean()))
    fb = 2 * math.pi * np.fft.rfftfreq(n, dt)[int(np.argmax(F))]
    print(f"  l = {l:+d}: on-axis shift / Omega = {w_shift / Omega:+.6f} (expected -l = {-l:+d});"
          f"  filtered intensity beat / Omega = {fb / Omega:.6f} (expected 2|l| = {2 * abs(l)})")
