# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Stationary scattering in one dimension by piecewise-constant potentials: exact transmission and reflection by
transfer matrices. In region j the solution is A_j e^{i k_j x} + B_j e^{-i k_j x}, k_j = sqrt(2 m (E - V_j))/hbar
(imaginary for E < V_j: evanescent); continuity of psi and psi' at each step gives a 2x2 matrix. Transmission
T = (k_out / k_in) |t|^2 (both propagating), R = |r|^2, T + R = 1. ``staircase_amplitudes`` gives the complex t and r of
many smooth profiles at once (B4: the phase a coupling imprints on a wave crossing a channel).
"""

from __future__ import annotations

import cmath
import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Туннелирование: точное рассеяние на ступенчатых потенциалах",
    "statement": "Коэффициенты прохождения и отражения для кусочно-постоянного потенциала методом матриц "
                 "переноса; T + R = 1; комплексные амплитуды t, r (с фазой) для плавных профилей; прямоугольный "
                 "барьер и δ-барьер в замкнутой форме.",
    "validity": "стационарное рассеяние, нерелятивистская частица",
    "basis": ["Schrödinger 1926", "Gamow 1928 (туннелирование)", "Landau & Lifshitz, т. 3, §25"],
    "conflicts": [],
}


def _k(E, V, m, hbar):
    return cmath.sqrt(2 * m * (E - V)) / hbar


def _step(k1, k2, d):
    """[A_j, B_j] = M [A_{j+1}, B_{j+1}] across one step, the waves of region j referenced at its left edge (local
    coordinate d at the step) and those of region j + 1 at the step itself. Returned as (Mt, s), M = e^s Mt: the
    growth e^{|Im k1| d} of an evanescent region is carried as the exponent (review 2026-10-23, E4)."""
    s = abs((k1 * d).imag)
    em, ep = np.exp(-1j * k1 * d - s), np.exp(1j * k1 * d - s)
    r = k2 / k1
    return (0.5 * (1 + r) * em, 0.5 * (1 - r) * em, 0.5 * (1 - r) * ep, 0.5 * (1 + r) * ep), s


def transmission(E: float, edges, Vs, m: float = 1.0, hbar: float = 1.0):
    """Potential Vs[0] for x < edges[0], Vs[i] on [edges[i-1], edges[i]], Vs[-1] for x > edges[-1]
    (len(Vs) = len(edges) + 1). Returns (T, R, t, r) for a wave incident from the left (E > V_in, V_out); the
    phases of t and r refer to plane waves e^{+-ikx} with x measured from the origin.

    The waves of every region are referenced at its own left edge and the growth of evanescent regions is carried
    as a separate exponent, so the result does not depend on where the structure sits on the x axis and a thick
    barrier gives T -> 0 instead of an overflow (review 2026-10-23, E4)."""
    edges = np.asarray(edges, float)
    ks = [_k(E, V, m, hbar) for V in Vs]
    ks = [k if k != 0 else 1e-30 for k in ks]
    M = np.eye(2, dtype=complex)
    S = 0.0
    for j in range(len(edges)):
        d = 0.0 if j == 0 else edges[j] - edges[j - 1]
        (a00, a01, a10, a11), sj = _step(ks[j], ks[j + 1], d)
        M = M @ np.array([[a00, a01], [a10, a11]])
        mx = float(np.max(np.abs(M)))
        M, S = M / mx, S + sj + math.log(mx)
    # left [1, r] = e^S Mt [t, 0], in local references
    t_loc = math.exp(-S) / M[0, 0] if S < 745 else 0j
    r_loc = M[1, 0] / M[0, 0]
    kin, kout = ks[0], ks[-1]
    x0, xN = (edges[0], edges[-1]) if len(edges) else (0.0, 0.0)
    r = r_loc * cmath.exp(2j * kin * x0)
    t = t_loc * cmath.exp(1j * kin * x0) * (cmath.exp(-1j * kout * xN) if kout.imag == 0 else 1.0)
    T = (kout.real / kin.real) * math.exp(-2 * S) / abs(M[0, 0]) ** 2 if kout.imag == 0 else 0.0
    return float(T), float(abs(r_loc) ** 2), complex(t), complex(r)


def rectangular_barrier(E: float, V0: float, a: float, m: float = 1.0, hbar: float = 1.0) -> float:
    """Closed form T(E) for a barrier of height V0 and width a (Landau & Lifshitz)."""
    if E == V0:
        return 1.0 / (1.0 + m * V0 * a * a / (2 * hbar * hbar))
    if E < V0:
        q = math.sqrt(2 * m * (V0 - E)) / hbar
        return 1.0 / (1.0 + V0 * V0 * math.sinh(q * a) ** 2 / (4 * E * (V0 - E)))
    q = math.sqrt(2 * m * (E - V0)) / hbar
    return 1.0 / (1.0 + V0 * V0 * math.sin(q * a) ** 2 / (4 * E * (E - V0)))


def delta_barrier(E: float, alpha: float, m: float = 1.0, hbar: float = 1.0) -> float:
    """V = alpha delta(x):  T = 1 / (1 + m alpha^2 / (2 hbar^2 E))."""
    return 1.0 / (1.0 + m * alpha * alpha / (2 * hbar * hbar * E))


def _normalised(a00, a01, a10, a11):
    """The four entries divided by their largest modulus, and the log of that modulus (0 for a zero matrix)."""
    mx = np.maximum(np.maximum(np.abs(a00), np.abs(a01)), np.maximum(np.abs(a10), np.abs(a11)))
    mx = np.where(mx > 0, mx, 1.0)
    return a00 / mx, a01 / mx, a10 / mx, a11 / mx, np.log(mx)


def chain(a00, a01, a10, a11, s=None):
    """The ordered product M_0 M_1 ... M_{n-1} of 2x2 matrices given entry by entry along the last axis (arrays
    (..., n); ``s`` (..., n): M_j carries the extra factor e^{s_j}) as (P00, P01, P10, P11, S), the product being
    e^S [[P00, P01], [P10, P11]] with the largest |P| = 1. Pairwise products, each normalised, in log2(n) vectorised
    levels instead of n sequential steps (review UX-ui U3: the sequential loop of ``transmission_profile`` made the
    quantum playground re-tune its absorbers for 18-60 s after every change); the same product up to rounding."""
    a00, a01, a10, a11, lg = _normalised(*(np.asarray(z, complex) for z in (a00, a01, a10, a11)))
    S = np.sum(lg if s is None else lg + np.asarray(s, float), axis=-1)
    while a00.shape[-1] > 1:
        if a00.shape[-1] % 2:  # an odd count: the identity closes the last pair
            pad = [(0, 0)] * (a00.ndim - 1) + [(0, 1)]
            a00, a11 = np.pad(a00, pad, constant_values=1.0), np.pad(a11, pad, constant_values=1.0)
            a01, a10 = np.pad(a01, pad), np.pad(a10, pad)
        l00, l01, l10, l11 = a00[..., 0::2], a01[..., 0::2], a10[..., 0::2], a11[..., 0::2]
        r00, r01, r10, r11 = a00[..., 1::2], a01[..., 1::2], a10[..., 1::2], a11[..., 1::2]
        a00, a01, a10, a11, lg = _normalised(l00 * r00 + l01 * r10, l00 * r01 + l01 * r11,
                                             l10 * r00 + l11 * r10, l10 * r01 + l11 * r11)
        S = S + np.sum(lg, axis=-1)
    return a00[..., 0], a01[..., 0], a10[..., 0], a11[..., 0], S


_CHUNK = 1 << 21  # transfer matrices per vectorised chain (memory: ~16 arrays of this many complex numbers)


def staircase_transmission(E, Vs, h: float, m: float = 1.0, hbar: float = 1.0):
    """(T, R) of staircase potentials: ``Vs[..., 0]`` left of the structure, ``Vs[..., 1:-1]`` on its slices of width
    h, ``Vs[..., -1]`` right of it (complex allowed: an absorbing -iW), a wave of energy E incident from the left; E
    broadcast against ``Vs[..., 0]``, so several energies and several potentials (e.g. one profile at many strengths)
    are computed at once. Local references and a separate growth exponent as in ``transmission``: independent of the
    position of the structure and safe for thick barriers. T = 0 where the right side is closed (evanescent)."""
    Vs = np.asarray(Vs)
    E = np.asarray(E, float)
    shape = np.broadcast_shapes(np.shape(E), Vs.shape[:-1])
    n = Vs.shape[-1]
    Eb = np.broadcast_to(E, shape).reshape(-1)
    Vb = np.broadcast_to(Vs, shape + (n,)).reshape(-1, n)
    d = np.full(n - 1, float(h))
    d[0] = 0.0
    T = np.empty(len(Eb))
    R = np.empty(len(Eb))
    rows = max(1, _CHUNK // max(n, 1))
    for i0 in range(0, len(Eb), rows):
        sl = slice(i0, i0 + rows)
        k = np.sqrt(2 * m * (Eb[sl, None].astype(complex) - Vb[sl])) / hbar
        k = np.where(np.abs(k) == 0, 1e-30, k)
        (a00, a01, a10, a11), s = _step(k[:, :-1], k[:, 1:], d[None, :])
        M00, _, M10, _, S = chain(a00, a01, a10, a11, s)
        kin, kout = k[:, 0], k[:, -1]
        with np.errstate(under="ignore", invalid="ignore", divide="ignore", over="ignore"):
            T[sl] = np.where(np.abs(kout.imag) < 1e-12 * np.abs(kout),
                             (kout.real / kin.real) * np.exp(-2 * S) / np.abs(M00) ** 2, 0.0).real
            R[sl] = np.abs(M10 / M00) ** 2
    return T.reshape(shape), R.reshape(shape)


def transmission_profile(E, V, x0: float, x1: float, n_slices: int, m: float = 1.0, hbar: float = 1.0,
                         return_r: bool = False):
    """Stationary transmission T(E) through an arbitrary potential V(x) (a callable; constant outside [x0, x1]),
    by transfer matrices over ``n_slices`` equal slices with the potential at the slice midpoints (exact for that
    staircase; for a smooth V the error falls as 1/n_slices^2, so two resolutions give a Richardson estimate).
    Vectorised over the energies E (array) and over the slices (``chain``: since review UX-ui U3). Local references
    and a separate growth exponent as in ``transmission``: independent of the position of [x0, x1] and safe for thick
    barriers (review 2026-10-23, E4). V may be complex (an absorbing potential -iW: then 1 - R - T is the absorbed
    fraction). ``return_r``: also return R(E)."""
    E = np.atleast_1d(np.asarray(E, float))
    edges = np.linspace(x0, x1, n_slices + 1)
    h = (x1 - x0) / n_slices
    Vs = np.concatenate([np.atleast_1d(V(x0 - 1.0)), np.asarray(V(0.5 * (edges[1:] + edges[:-1]))),
                         np.atleast_1d(V(x1 + 1.0))])
    T, R = staircase_transmission(E, Vs, h, m, hbar)
    if return_r:
        return T, R
    return T


def staircase_amplitudes(E, U, h: float, m: float = 1.0, hbar: float = 1.0):
    """Complex transmission and reflection amplitudes (t, r) of a staircase potential: U[..., j] on the j-th of n
    slices of width h, zero on both sides, a wave of energy E (> 0) incident from the left:
        psi = e^{ik(x - x0)} + r e^{-ik(x - x0)}  left of the structure,   psi = t e^{ik(x - x1)}  right of it,
    k = sqrt(2mE)/hbar, x1 - x0 = n h. Vectorised over the leading axes of U (several potentials at once, e.g. one
    profile scaled by many strengths) with E broadcast against them. Each slice is propagated exactly in (psi, psi');
    for a smooth U sampled at slice midpoints the error falls as h^2. Meant for propagating or thin evanescent
    regions (cosh, sinh of a thick barrier overflow: there use ``transmission``)."""
    U = np.asarray(U, float)
    E = np.asarray(E, float)
    k = np.sqrt(2 * m * E) / hbar
    shape = np.broadcast_shapes(U.shape[:-1], np.shape(k))
    M00 = np.ones(shape, complex)
    M01 = np.zeros(shape, complex)
    M10 = np.zeros(shape, complex)
    M11 = np.ones(shape, complex)
    for j in range(U.shape[-1]):
        q = np.sqrt((2 * m * (E - U[..., j])).astype(complex)) / hbar
        q = np.where(np.abs(q) == 0, 1e-30, q)
        c, s = np.cos(q * h), np.sin(q * h)
        a, b, cc, d = c, s / q, -q * s, c
        M00, M01, M10, M11 = a * M00 + b * M10, a * M01 + b * M11, cc * M00 + d * M10, cc * M01 + d * M11
    # (psi, psi')(x1) = M (psi, psi')(x0): with (1 + r, ik(1 - r)) on the left and (t, ik t) on the right
    p = M00 + 1j * k * M01
    q_ = M10 + 1j * k * M11
    mm = M00 - 1j * k * M01
    nn = M10 - 1j * k * M11
    # t = p + r mm,  ik t = q_ + r nn  ->  r = (q_ - ik p) / (ik mm - nn)
    r = (q_ - 1j * k * p) / (1j * k * mm - nn)
    t = p + r * mm
    return t, r
