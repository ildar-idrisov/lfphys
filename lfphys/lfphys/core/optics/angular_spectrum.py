# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact free-space propagation of a scalar field by its angular spectrum, in 2-D (one transverse coordinate) and 3-D
(two):

    U(r, z) = (2 pi)^-d int A(k_t) exp(i (k_t . r + k_z z)) d^d k_t,   A = FT of U(r, 0),   k_z = sqrt(k^2 - |k_t|^2)

(k_z imaginary for evanescent components: they decay). Every Cartesian component of the field in a homogeneous medium
obeys the Helmholtz equation, so this is exact for given values on z = 0 (Rayleigh-Sommerfeld boundary values).
Independent of lfphys.core.optics.scalar (the Rayleigh-Sommerfeld integral) and of
lfphys.core.optics.aperture_fields (closed forms and quadratures without FFTs): the tests compare them.

On a grid the integral becomes a sum over the frequencies of a window of m points per axis (the field on z = 0
zero-padded ``pad`` times, to a power of two; ``pad`` may be given per axis, and pad = 1 keeps the window periodic
along that axis). Two errors remain, and runs measure them:

* **the window**: the sum is the field of a periodic array of copies of the source, period m d; light leaving at wide
  angles reaches the neighbouring copies, so a deep plane needs a wide window. ``band_limit=True`` leaves out, at
  each z, the components whose transfer phase k_z z is undersampled on the frequency grid (|q_i| z / Re k_z > m_i d_i
  / 2: they would travel more than half a period sideways and alias), the idea of the band-limited angular spectrum
  (K. Matsushima, T. Shimobaba, Opt. Express 17, 19662 (2009); here the exact per-axis Nyquist condition of the
  phase). It is not exact either; it converges faster in the window (the pad);
* **the source**: samples U0 of a sharp aperture carry the staircase of its edges. A ``Spectral`` source gives the
  exact Fourier transform of the field on z = 0 instead (e.g. ``aperture_fields.rect_spectrum``): the frequencies of
  the grid's band |q_i| < pi/d_i are then exact, and only the components beyond it are left out; with d <= lambda/2
  those are evanescent and at depth z below exp(-sqrt((pi/d)^2 - k^2) z) of their size on z = 0.

Grid convention: sample i of an axis with n points and spacing d sits at x_i = (i - n//2) d (as ``Grid.uniform``).

3-D modelling (``lfphys.core.geometry.Modelling``; plan P10): ``propagate_field`` gives transverse planes z = const
(any set of z); ``propagate_volume`` the whole volume on a z grid (mode "full 3-D", any slice afterwards);
``propagate_slice`` a longitudinal plane x = c or y = c on a z grid without the volume (mode "chosen slices"),
identical to the volume's plane on the same grid (between grid nodes: the trigonometric interpolant, exact for the
sampled band-limited field); ``propagate_plane`` a plane of any orientation, by the same sum; ``propagate_current``
the energy flux of the wave (Im U* grad U / k) and the power through each plane. "Exact" here means: exact for the given source on the grid; the accuracy against the
physical field is that of the window and of the source (above), which runs measure.
The heavy part (FFTs, phase factors) runs on the CPU or on GPU 0 (``lfphys.core.backend``, kernel
"optics.angular_spectrum").
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from lfphys.codes import coded
from lfphys.i18n import T
from .. import backend

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Field propagation by the angular spectrum (2-D and 3-D)"),
    "statement": T("The field in the plane z is a sum of plane waves exp(i(k_t·r + k_z z)), k_z = √(k² − k_t²); "
                   "evanescent components decay. Exact for a given field in the plane z = 0; in 3-D: transverse "
                   "planes, the whole volume or exact longitudinal slices."),
    "validity": T("homogeneous medium; on a grid: a band-limited field and a window with a margin (zero padding)"),
    "basis": [T("Goodman, Introduction to Fourier Optics, ch. 3.10"),
              T("Matsushima & Shimobaba, Opt. Express 17, 19662 (2009) — band limiting")],
    "conflicts": [],
}

KERNEL = "optics.angular_spectrum"


def _bench(size: int, xp, cplx):
    """One propagation step as a call does it: the field from host memory, FFT, phase, inverse FFT, back to the host."""
    n = max(8, int(round(math.sqrt(size))))
    a = xp.asarray(np.ones((n, n), dtype=np.complex128), dtype=cplx)
    kz = xp.ones((n, n), dtype=cplx)
    backend.to_numpy(xp.fft.ifft2(xp.fft.fft2(a) * xp.exp(1j * kz)))


backend.register(backend.KernelSpec(
    KERNEL, T("Angular spectrum (wave propagation)"),
    T("exact propagation of a scalar wave in 2-D and 3-D: FFT of the field, a phase factor, inverse FFT"),
    gpu=True,
    precisions={"fp64": {"allowed": True},
                "fp32": {"allowed": True, "bound": 1e-5, "use": T("for drawing only (checks always in fp64)"),
                         "domain": T("k·z ≤ 2000 rad, up to 1024 points per axis (the phase in fp64)"),
                         "evidence": "tests/test_backend.py::test_angular_spectrum_fp32_within_its_bound"}},
    crossover=128 * 128,
    crossover_note=T("measured 2026-10-27 on an RTX 2080 Ti against one CPU thread, fp64, with the field "
                     "transferred: the GPU is faster from 128×128 points (×2), up to ×9 at 2048×2048; “Measure again” "
                     "refines this"),
    bench=_bench, bench_sizes=(32 * 32, 64 * 64, 128 * 128, 256 * 256, 512 * 512, 1024 * 1024, 2048 * 2048)))


@dataclass(frozen=True)
class Spectral:
    """A field on z = 0 given by its exact Fourier transform: ``fn(q_1[, q_2])`` returns A(q) = int U0(r) e^{-i q.r}
    d^d r on frequency arrays (rad per unit length) given as an open grid (``np.meshgrid(..., sparse=True)``:
    broadcast them; a separable source then costs only its factors); on GPU 0 the arrays are CuPy arrays when ``fn``
    accepts them (``aperture_fields``' closed forms do), else NumPy; ``shape`` is the grid of the result (n per axis,
    convention x_i = (i - n//2) d)."""
    shape: tuple
    fn: Callable

    @property
    def ndim(self) -> int:
        return len(self.shape)


def _grid_shape(U0) -> tuple:
    return tuple(U0.shape) if isinstance(U0, Spectral) else np.asarray(U0).shape


def _shape(U0, pad):
    pads = np.broadcast_to(np.atleast_1d(np.asarray(pad, float)), (U0.ndim,))  # per axis; 1: periodic window
    return tuple(int(2 ** math.ceil(math.log2(n * pd))) if pd > 1 else n for n, pd in zip(U0.shape, pads))


def _setup(U0, spacing, k, m, ch, band_limit):
    """Padded spectrum A (FFT order), k_z (always complex128: the phase is formed in fp64, review B1-6), the
    band-limit measure s (a component is kept at depth z when s z <= 1; None without the band limit), the crop
    slices, the frequency axes; all on the chosen device. Sample i of an axis with n points sits at buffer index
    m//2 - n//2 + i, i.e. at x = (i - n//2) d, for odd and even n alike (review B1-3: the offset (m - n)//2 put odd n
    one sample off)."""
    xp = ch.xp
    d = U0.ndim
    sp = np.broadcast_to(np.atleast_1d(np.asarray(spacing, float)), (d,))
    off = tuple(mi // 2 - n // 2 for mi, n in zip(m, U0.shape))
    crop = tuple(slice(o, o + n) for o, n in zip(off, U0.shape))
    ks = [2 * math.pi * np.fft.fftfreq(mi, si) for mi, si in zip(m, sp)]
    Qh = np.meshgrid(*ks, indexing="ij", sparse=True)  # open grid on the host (for the source's spectrum)
    Q = [xp.asarray(q) for q in Qh]
    kz = xp.sqrt((k * k - sum(q * q for q in Q)).astype(xp.complex128))
    kz = xp.where(kz.imag < 0, -kz, kz)
    if isinstance(U0, Spectral):  # the exact transform at the grid's frequencies; the DFT of samples is A / prod(d)
        A = None
        if xp is not np:  # on the device when the closed form accepts device arrays; else on the host
            try:
                A = xp.broadcast_to(xp.asarray(U0.fn(*Q), dtype=xp.complex128), m)
            except Exception:  # noqa: BLE001
                A = None
        if A is None:
            A = xp.asarray(np.broadcast_to(np.asarray(U0.fn(*Qh), complex), m))
        A = (A / float(np.prod(sp))).astype(ch.complex)
    else:
        buf = xp.zeros(m, dtype=ch.complex)
        buf[crop] = xp.asarray(U0, dtype=ch.complex)
        A = xp.fft.fftn(xp.fft.ifftshift(buf))
    s = None
    if band_limit:  # keep where |q_i| z <= (m_i d_i / 2) Re k_z for every axis (evanescent components: always)
        kr = kz.real
        safe = xp.where(kr > 0, kr, 1.0)
        s = None
        for q, mi, si in zip(Q, m, sp):
            r = xp.abs(q) / (0.5 * mi * si * safe)
            s = r if s is None else xp.maximum(s, r)
        s = xp.where(kr > 0, s, xp.where(kz.imag > 0, 0.0, xp.inf))
    return A, kz, s, crop, ks


def _phase(xp, kz, s, zz, ch):
    """exp(i k_z z) formed in fp64 and cast to the working precision (in fp32 the phase k_z z itself would lose
    ~6e-8 k z rad: 1.2e-5 at k z = 1676, review B1-6); with the band limit, zero where s z > 1."""
    ph = xp.exp(1j * kz * zz)
    if s is not None and zz > 0:
        ph = ph * (s * zz <= 1.0)
    return ph if ch.precision == "fp64" else ph.astype(ch.complex)


def _run(U0, spacing, k, z, pad, check, band_limit, body):
    """Run ``body(ch, A, kz, s, crop, ks, m)`` on the device the backend chooses; when the GPU runs out of memory,
    free the pool and redo it on the CPU (review B1-7); after a GPU call the pool's free blocks are returned."""
    if not isinstance(U0, Spectral):
        U0 = np.asarray(U0, complex)
    if U0.ndim not in (1, 2):
        raise ValueError("angular spectrum: U0 is 1-D (2-D problem) or 2-D (3-D problem)")
    if np.any(np.asarray(z, float) < 0):
        raise coded(ValueError(T("angular spectrum: z ≥ 0 (backward propagation would amplify the evanescent "
                                 "components)")), "angular_spectrum.backward")
    m = _shape(U0, pad)
    size = int(np.prod(m))
    footprint = 7 * size * 16  # buffer, spectrum, k_z, band measure, phase, product, transform (complex128)
    ch = backend.choose(KERNEL, size, check=check, footprint=footprint)
    try:
        return body(ch, *_setup(U0, spacing, k, m, ch, band_limit), m)
    except Exception as e:  # noqa: BLE001
        if ch.device != "gpu" or not backend.is_out_of_memory(e):
            raise
        backend.release()
        ch = backend.choose(KERNEL, size, check=check, force="cpu", why=T("not enough GPU memory → CPU"))
        return body(ch, *_setup(U0, spacing, k, m, ch, band_limit), m)
    finally:
        if ch.device == "gpu":
            backend.release()


def propagate_field(U0, spacing, k: float, z, pad: int = 2, check: bool = False, band_limit: bool = False):
    """Field on the transverse planes at distance(s) z >= 0 from the source U0 (samples, 1-D: a 2-D problem, 2-D: a
    3-D problem; or a ``Spectral`` source) with grid spacing ``spacing`` (scalar or per axis). Returns
    (len(z), *shape) or shape for scalar z (NumPy). ``check=True``: a reference or a check, always fp64.
    ``band_limit``: see the module's docstring."""
    zs = np.atleast_1d(np.asarray(z, float))
    shape = _grid_shape(U0)

    def body(ch, A, kz, s, crop, ks, m):
        xp = ch.xp
        out = np.empty((len(zs),) + shape, dtype=np.complex128 if ch.precision == "fp64" else np.complex64)
        for i, zz in enumerate(zs):
            out[i] = backend.to_numpy(xp.fft.fftshift(xp.fft.ifftn(A * _phase(xp, kz, s, zz, ch)))[crop])
        return out
    out = _run(U0, spacing, k, zs, pad, check, band_limit, body)
    return out if np.ndim(z) else out[0]


def propagate_volume(U0, spacing, k: float, z, pad: int = 2, check: bool = False, band_limit: bool = False):
    """The whole 3-D field on the z grid ``z`` (mode "full 3-D"): array (len(z), nx, ny); any plane can then be cut
    from it (``lfphys.core.geometry.slice_field``). Memory: len(z) * nx * ny complex values."""
    if len(_grid_shape(U0)) != 2:
        raise ValueError("propagate_volume: U0 is the 2-D field on z = 0 of a 3-D problem")
    return propagate_field(U0, spacing, k, np.atleast_1d(np.asarray(z, float)), pad, check, band_limit)


def propagate_slice(U0, spacing, k: float, z, axis: int, at: float, pad: int = 2, check: bool = False,
                    band_limit: bool = False):
    """The longitudinal plane x = ``at`` (axis 0) or y = ``at`` (axis 1) of a 3-D field, on the z grid ``z``, without
    the volume (mode "chosen slices"): the field across the other transverse axis at every z. Identical to the
    volume's plane on the same grid; ``at`` need not be a grid node: U(at) = (1/m) sum_q B_q exp(i k_q at) is the
    trigonometric interpolant, exact for the sampled band-limited periodic field (near a sharp edge of a sampled
    aperture it rings like any band-limited representation; the accuracy against the physical field is the
    window's and the source's, which a run measures). Returns (len(z), n_other) (NumPy)."""
    if len(_grid_shape(U0)) != 2 or axis not in (0, 1):
        raise ValueError("propagate_slice: a 3-D problem (2-D U0), axis 0 or 1")
    zs = np.atleast_1d(np.asarray(z, float))
    other = 1 - axis
    n_other = _grid_shape(U0)[other]

    def body(ch, A, kz, s, crop, ks, m):
        xp = ch.xp
        phase = xp.asarray(np.exp(1j * ks[axis] * at), dtype=ch.complex) / m[axis]
        out = np.empty((len(zs), n_other), dtype=np.complex128 if ch.precision == "fp64" else np.complex64)
        for i, zz in enumerate(zs):
            B = A * _phase(xp, kz, s, zz, ch)
            C = xp.fft.fftshift(xp.fft.ifft(B, axis=other), axes=other)  # positions along the other axis, k along axis
            line = xp.tensordot(C, phase, axes=([axis], [0]))
            out[i] = backend.to_numpy(line[crop[other]])
        return out
    return _run(U0, spacing, k, zs, pad, check, band_limit, body)


def propagate_plane(U0, spacing, k: float, plane, s_range, t, pad: int = 2, check: bool = False,
                    band_limit: bool = False):
    """The field of a 3-D problem on a plane of any orientation (owner, 2026-10-27: slices "под любыми углами"),
    without the volume and without interpolation: at the points origin + s u + t v of ``plane`` (a
    ``geometry.Plane`` whose u is horizontal, u_z = 0: ``Plane.horizontal``), for s on the grid of the source's
    spacing within ``s_range`` (returned) and the given t, by the same sum U = (1/(m_x m_y)) sum_q A_q exp(i (q.r +
    k_z z)). When u is along +-x or +-y this is identical to what the volume gives at those points; otherwise the
    source is turned and the sum runs over the turned lattice of periodic copies (another periodisation of the same
    field: the two differ by the window's error, review C9).

    How: the source is turned about the axis so that u becomes x (exact for a ``Spectral`` source: A(R q); a sampled
    source is accepted only with u = +x); then in the plane's frame the phase is q_x (o_x + s) + q_y y(t) + k_z z(t),
    so for each t one sum over q_y (with e^{i k_z z(t)} advanced from one t to the next in steps of increasing z, which
    keeps every factor of modulus <= 1, re-anchored every 32 steps) and one inverse FFT over q_x give the whole line
    in s (periodic in s with the window's period, so any s is read modulo it). Points with z < 0 (before the source)
    are NaN. Returns (s, U[len(t), len(s)]) (NumPy)."""
    from ..geometry import Plane  # noqa: F401  (documentation of the argument)
    from . import aperture_fields as AF
    u = np.asarray(plane.u, float)
    v = np.asarray(plane.v, float)
    o = np.asarray(plane.origin, float)
    if abs(u[2]) > 1e-12:
        raise ValueError("propagate_plane: the plane's u must be horizontal (Plane.horizontal)")
    phi = math.atan2(u[1], u[0])
    src = U0
    if abs(phi) > 1e-15:
        if not isinstance(U0, Spectral):
            raise ValueError("propagate_plane: a sampled source only for u = +x; give a Spectral source to turn it")
        src = Spectral(U0.shape, AF.rotated(U0.fn, -phi))
    if len(_grid_shape(src)) != 2:
        raise ValueError("propagate_plane: a 3-D problem (2-D source)")
    c, sn = math.cos(phi), math.sin(phi)
    ox, oy = c * o[0] + sn * o[1], -sn * o[0] + c * o[1]  # the origin in the turned frame
    vy = -sn * v[0] + c * v[1]
    vz = float(v[2])
    ts = np.atleast_1d(np.asarray(t, float))
    zt = o[2] + ts * vz
    yt = oy + ts * vy
    sp = np.broadcast_to(np.atleast_1d(np.asarray(spacing, float)), (2,))
    s_lo, s_hi = float(min(s_range)), float(max(s_range))

    def body(ch, A, kz, smeas, crop, ks, m):
        xp = ch.xp
        mx, my = m
        js = np.arange(int(math.ceil(s_lo / sp[0] - 1e-9)), int(math.floor(s_hi / sp[0] + 1e-9)) + 1)
        if not 0 < len(js) <= mx:
            raise coded(ValueError(T("the plane's extent along u is empty or longer than the window")),
                        "angular_spectrum.plane_extent")
        qx = xp.asarray(ks[0])[:, None]
        qy = xp.asarray(ks[1])[None, :]
        C0 = A * xp.exp(1j * qx * ox)  # |.| = |A|
        D = xp.zeros((len(ts), mx), dtype=xp.complex128)
        order = np.argsort(zt, kind="stable")
        valid = order[zt[order] >= 0]
        dz = np.diff(zt[valid])
        uniform = len(dz) > 0 and np.allclose(dz, dz[0], rtol=1e-12, atol=1e-15)
        E = xp.exp(1j * kz * float(dz[0])) if uniform else None  # z increasing: modulus <= 1
        P = None
        for step, i in enumerate(valid):
            if E is None or step % 32 == 0:
                P = xp.exp(1j * kz * zt[i])
            else:
                P = P * E
            term = C0 * P * xp.exp(1j * qy * yt[i])
            if smeas is not None and zt[i] > 0:
                term = term * (smeas * zt[i] <= 1.0)
            if ch.precision != "fp64":
                term = term.astype(ch.complex)
            D[i] = xp.sum(term, axis=1)
        line = xp.fft.ifft(D, axis=1) / my  # column j: s = j dx, periodic in s with the window's period m_x dx
        out = backend.to_numpy(line[:, xp.asarray(js % mx)])
        out = out.astype(np.complex128 if ch.precision == "fp64" else np.complex64)
        out[zt < 0] = np.nan
        return js * sp[0], out
    return _run(src, spacing, k, np.maximum(zt, 0.0), pad, check, band_limit, body)


def propagate_current(U0, spacing, k: float, z, pad: int = 2, check: bool = False, band_limit: bool = False):
    """The current of the scalar wave j = Im(U* grad U) / k on the transverse planes z of a 3-D problem: the energy
    flux density of the wave in units of that of the unit plane wave (a unit plane wave along the unit vector n has
    j = n; e.g. M. V. Berry, J. Opt. A 11, 094001 (2009), "optical currents"). The gradient is exact for the sum
    (i q_x, i q_y, i k_z times each component). Returns (j[len(z), 3, nx, ny], P[len(z)]), P(z) = sum j_z dx dy over
    the whole computation window: the power through the plane, which the plain sum conserves exactly
    (P = dx dy / (k m_x m_y) sum over propagating q of |A_q|^2 k_z, z-independent)."""
    zs = np.atleast_1d(np.asarray(z, float))
    shape = _grid_shape(U0)
    if len(shape) != 2:
        raise ValueError("propagate_current: a 3-D problem (2-D source)")
    sp = np.broadcast_to(np.atleast_1d(np.asarray(spacing, float)), (2,))

    def body(ch, A, kz, smeas, crop, ks, m):
        xp = ch.xp
        qx = xp.asarray(ks[0])[:, None]
        qy = xp.asarray(ks[1])[None, :]
        j = np.empty((len(zs), 3) + shape)
        P = np.empty(len(zs))
        for i, zz in enumerate(zs):
            B = A * _phase(xp, kz, smeas, zz, ch)
            U = xp.fft.ifftn(B)
            comps = [xp.fft.ifftn(B * (1j * qx)), xp.fft.ifftn(B * (1j * qy)), xp.fft.ifftn(B * (1j * kz))]
            for c, G in enumerate(comps):
                jc = xp.imag(xp.conj(U) * G) / k
                if c == 2:
                    P[i] = float(xp.sum(jc)) * sp[0] * sp[1]
                j[i, c] = backend.to_numpy(xp.fft.fftshift(jc)[crop])
        return j, P
    return _run(U0, spacing, k, zs, pad, check, band_limit, body)


def flux_of_spectrum(U0, spacing, k: float, pad: int = 2) -> float:
    """The power the plain sum carries through every transverse plane, from the spectrum alone (the closed form of
    ``propagate_current``'s P): dx dy / (k m_x m_y) sum over propagating q of |A_q|^2 k_z."""
    sp = np.broadcast_to(np.atleast_1d(np.asarray(spacing, float)), (2,))

    def body(ch, A, kz, smeas, crop, ks, m):
        xp = ch.xp
        kzr = xp.where(kz.imag == 0, kz.real, 0.0)
        return float(xp.sum(xp.abs(A) ** 2 * kzr)) * sp[0] * sp[1] / (k * m[0] * m[1])
    return _run(U0, spacing, k, [0.0], pad, True, False, body)


def propagate(U0, dx: float, k: float, z, pad: int = 2, band_limit: bool = False):
    """2-D problem (one transverse coordinate): field at distance(s) z from the source U0 (samples on a uniform grid
    of spacing dx, or a 1-D ``Spectral`` source). Returns array (len(z), N) or (N,). fp64 (used as a reference)."""
    if not isinstance(U0, Spectral):
        U0 = np.asarray(U0, complex)
    return propagate_field(U0, dx, k, z, pad, check=True, band_limit=band_limit)
