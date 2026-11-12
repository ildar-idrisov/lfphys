# Helper of this review (not part of the engine): independent brute-force evaluations of the angular-spectrum sum.
# Written by the reviewer; no engine code copied. Root path of the engine in the container: /lf.
"""brute_sum: U(x, y, z) = (1/(mx my)) sum_q A_q exp(i (qx x + qy y + kz z)) evaluated point by point (no FFT, no
recurrence, no modulo reading), with A_q = fn(qx, qy) / (dx dy) on the padded frequency grid of the engine
(2 pi fftfreq(m, dx)); the band-limit mask written from the module's docstring (|q_i| z / Re k_z > m_i d_i / 2: out)."""

import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")


def padded_m(n, pad):
    return int(2 ** math.ceil(math.log2(n * pad))) if pad > 1 else n


def spectrum_grid(fn, n, dx, k, pad):
    m = padded_m(n, pad)
    q = 2 * math.pi * np.fft.fftfreq(m, dx)
    QX, QY = np.meshgrid(q, q, indexing="ij")
    A = np.asarray(fn(QX, QY), complex) / (dx * dx)
    kz = np.sqrt((k * k - QX ** 2 - QY ** 2).astype(complex))
    kz = np.where(kz.imag < 0, -kz, kz)
    return m, QX, QY, A, kz


def sampled_grid(U0, dx, k, pad):
    n = U0.shape[0]
    m = padded_m(n, pad)
    buf = np.zeros((m, m), complex)
    o = m // 2 - n // 2
    buf[o:o + n, o:o + n] = U0
    A = np.fft.fftn(np.fft.ifftshift(buf))
    q = 2 * math.pi * np.fft.fftfreq(m, dx)
    QX, QY = np.meshgrid(q, q, indexing="ij")
    kz = np.sqrt((k * k - QX ** 2 - QY ** 2).astype(complex))
    kz = np.where(kz.imag < 0, -kz, kz)
    return m, QX, QY, A, kz


def brute_sum(grid, pts, dx, band_limit=False, chunk=64):
    """grid = (m, QX, QY, A, kz); pts (N, 3) in the frame of A. Returns (N,) complex."""
    m, QX, QY, A, kz = grid
    qx, qy, a, kzf = QX.ravel(), QY.ravel(), A.ravel(), kz.ravel()
    if band_limit:
        kr = kzf.real
        safe = np.where(kr > 0, kr, 1.0)
        meas = np.maximum(np.abs(qx), np.abs(qy)) / (0.5 * m * dx * safe)
        meas = np.where(kr > 0, meas, np.where(kzf.imag > 0, 0.0, np.inf))
    out = np.empty(len(pts), complex)
    for i0 in range(0, len(pts), chunk):
        P = pts[i0:i0 + chunk]
        ph = np.exp(1j * (np.outer(P[:, 0], qx) + np.outer(P[:, 1], qy) + np.outer(P[:, 2], kzf)))
        if band_limit:
            keep = (meas[None, :] * P[:, 2:3]) <= 1.0
            keep |= (P[:, 2:3] <= 0)
            ph = ph * keep
        out[i0:i0 + chunk] = ph @ a / (m * m)
    return out


def rot_fn(fn, phi):
    """The source turned so that the original azimuth phi becomes the x' axis: A'(q) = A(R_phi q)."""
    c, s = math.cos(phi), math.sin(phi)
    return lambda qx, qy: fn(c * qx - s * qy, s * qx + c * qy)


def to_turned(P, phi):
    """Points of the original frame -> the frame turned by phi (x' along azimuth phi)."""
    c, s = math.cos(phi), math.sin(phi)
    x, y = P[:, 0], P[:, 1]
    return np.stack([c * x + s * y, -s * x + c * y, P[:, 2]], axis=1)


def rel(a, b, peak=None):
    d = np.abs(np.asarray(a) - np.asarray(b))
    d = d[np.isfinite(d)]
    p = peak if peak is not None else np.nanmax(np.abs(b))
    return float(d.max() / p) if len(d) else float("nan")


class Tee:
    def __init__(self, path):
        self.f = open(path, "w")

    def __call__(self, *a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        self.f.write(s + "\n")
        self.f.flush()
