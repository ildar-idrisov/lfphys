# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Closed forms of thin-film optics (exact consequences of Maxwell's equations for homogeneous, isotropic, linear
media with plane boundaries; complex index n = n' + i n'', time dependence exp(-i omega t), the conventions of
``interfaces``). They are an independent route to the numbers ``interfaces.stack`` gets by multiplying transfer
matrices, so a visualization can check its run against them:

* one film: the sum of the multiply reflected waves (Airy summation) with complex Fresnel coefficients,
      r = (r01 + r12 e^{2i beta}) / (1 + r01 r12 e^{2i beta}),  t = t01 t12 e^{i beta} / (1 + r01 r12 e^{2i beta}),
      beta = 2 pi n1 d cos(theta1) / lambda;
* the Airy intensity formula of a lossless film (Fabry-Perot): T = T_max / (1 + F sin^2(Delta/2)) with
      rho = sqrt(R10 R12), F = 4 rho / (1 - rho)^2, T_max = T01 T12 / (1 - rho)^2,
      Delta = 4 pi n1 d cos(theta1)/lambda + arg r10 + arg r12 (reduces to 1/(1 + F sin^2(delta/2)) for n0 = n2),
    evaluated as T = T01 T12 / ((1 - rho)^2 + 4 rho sin^2(Delta/2)) with the Snell cosines and the phase of
    ``interfaces.stack`` and a first-order rounding bound (it grows as 1/(1 - rho) when the wave grazes inside the
    film, where F -> infinity);
* a quarter-wave layer at its design wavelength, normal incidence: R = ((n0 n2 - n1^2)/(n0 n2 + n1^2))^2
  (zero for n1 = sqrt(n0 n2));
* a quarter-wave stack (A B)^N on a substrate, layer A next to the incidence medium, normal incidence, design
  wavelength: the admittance is Y = n_s (n_A/n_B)^{2N}, so R = ((n0 - Y)/(n0 + Y))^2
  = ((n0 n_B^{2N} - n_s n_A^{2N}) / (n0 n_B^{2N} + n_s n_A^{2N}))^2;
* frustrated total internal reflection through a gap between two equal media (the optical analogue of tunnelling
  through a rectangular barrier): T = 1 / (1 + ((a^2 + b^2)/(2ab))^2 sinh^2(kappa d)),
  s: a = k_z, b = kappa;  p: a = k_z/n1^2, b = kappa/n_gap^2;  kappa = k0 sqrt(n1^2 sin^2 theta - n_gap^2);
* the evanescent wave beyond the critical angle: amplitude decay length 1/kappa = lambda / (2 pi sqrt(n1^2 sin^2
  theta - n2^2)), with q = n1^2 sin^2 theta - n2^2 evaluated in 160-bit arithmetic (``evanescent_q``): in binary64
  the subtraction loses digits as eps n1^2 sin^2 theta / q near the critical angle (review 2026-10-23, V5-2);
* absorption as Joule heating (Poynting's theorem), s polarization: A = k0 / Re(n0 cos theta0) *
  sum_j Im(n_j^2) * integral over layer j of |E|^2 dz, with |E|^2 from ``interfaces.field_profile`` (field of
  unit incident amplitude); it equals 1 - R - T, which the transfer matrices give from r and t alone. Inside a
  homogeneous layer |E|^2 is a sum of exp(-+2 Im(k_z) z) and of a cross term oscillating as exp(2i Re(k_z) z); the
  quadrature (composite 16-point Gauss-Legendre) takes sub-intervals of at most 4 / max(2|Im k_z|, 2|Re k_z|), so
  a skin depth of 1 nm is resolved like a thick transparent film (review 2026-10-23, V5-3).

Rounding: ``single_film`` returns a first-order bound of its own rounding (the Airy sum is a ratio whose
denominator D = 1 + r01 r12 e^{2i beta} vanishes when the wave grazes inside the layer, so the bound grows as 1/|D|);
it evaluates the Snell cosines with the same float operations as ``interfaces.stack`` (``interfaces._cosines``),
so that a comparison of the two routes tests the algebra and not the rounding of sin^2(theta), whose effect on the
phase beta = 2 pi n1 d cos(theta1)/lambda grows as (2 pi n1 d / lambda) eps / |cos theta1| near grazing. ``airy``
does the same for the intensity formula (err_T). ``stack_error_single_layer`` is the matching first-order bound of
the rounding of ``interfaces.stack`` for one layer, so that a check can use the sum of both bounds as its tolerance.
"""

from __future__ import annotations

import cmath
import math

import mpmath
import numpy as np

from lfphys.core.optics import interfaces
from lfphys import i18n
from lfphys.codes import coded
from lfphys.i18n import T

U = 2.0 ** -53  # unit round-off of binary64

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Thin films: closed forms (Airy, the λ/4 layer, the Bragg mirror, tunnelling of light)"),
    "statement": T("The sum of multiple reflections in one layer (complex Fresnel coefficients); the Airy formula T = "
                   "T_max/(1 + F sin²(Δ/2)); R of a quarter-wave layer and of a stack (AB)^N on a substrate; "
                   "frustrated total reflection across a gap; the penetration depth of the evanescent wave; absorption "
                   "as Joule heat from the field |E|². An independent route to the numbers of the transfer-matrix "
                   "method."),
    "validity": T("homogeneous isotropic linear media, flat interfaces, a plane wave (Maxwell's equations exactly); "
                  "the Airy formula in intensities holds for a lossless film without total reflection at its "
                  "interfaces"),
    "basis": [T("Born & Wolf, Principles of Optics, §1.5–1.6 (stratified media), §7.6 (multiple-beam interference, "
                "the Airy formulae)"),
              T("Macleod, Thin-Film Optical Filters (quarter-wave layers and stacks)")],
    "conflicts": [],
}


def _cos(n_in, n, theta0: float) -> complex:
    """cos(theta) in a medium of index n for incidence at theta0 from n_in (decaying / forward branch)."""
    return interfaces.snell_cos(complex(n_in), complex(n), complex(math.cos(theta0)))


def _rt(n1, c1, n2, c2, pol: str):
    """Fresnel amplitude coefficients (convention of ``interfaces``) for complex indices and cosines."""
    if pol == "s":
        den = n1 * c1 + n2 * c2
        return (n1 * c1 - n2 * c2) / den, 2 * n1 * c1 / den
    if pol == "p":
        den = n2 * c1 + n1 * c2
        return (n2 * c1 - n1 * c2) / den, 2 * n1 * c1 / den
    raise ValueError("pol must be 's' or 'p'")


def _power(n_in, c_in, n_out, c_out, pol: str) -> float:
    """|t|^2 -> transmitted power fraction (the factor ``interfaces.stack`` uses)."""
    if pol == "s":
        return (n_out * c_out).real / (n_in * c_in).real
    return (n_out * c_out.conjugate()).real / (n_in * c_in.conjugate()).real


def _kappa(x, y) -> float:
    """Condition number (|x| + |y|)/|x + y| of a sum (inf when it vanishes)."""
    s = abs(x + y)
    return (abs(x) + abs(y)) / s if s > 0 else math.inf


def single_film(n0, n1, n2, d: float, lam: float, theta0: float, pol: str) -> dict:
    """One layer (index n1, thickness d) between n0 and n2: the Airy sum of the multiply reflected waves.
    d and lam in the same unit. Returns dict(r, t, R, T, A, D, err_r, err_t).

    The cosines in the three media are those of ``interfaces.stack`` (Snell's law with the same float operations),
    see the module docstring. D = 1 + r01 r12 e^{2i beta} is the denominator of the sum; err_r and err_t bound the
    rounding of this evaluation to first order in u = 2^-53: each Fresnel coefficient carries <= 6u times the
    condition number (|x| + |y|)/|x + y| of its denominator (complex products <= sqrt(5) u, one sum, one complex
    division <= 3u), e^{2i beta} <= 2u for the given beta, and the errors of the numerator N = r01 + r12 e^{2i beta}
    and of D are divided by |D|. At exact grazing inside the layer (cos theta1 = 0 in float) the sum is 0/0:
    ValueError (the matrices are regular there)."""
    n0, n1, n2 = complex(n0), complex(n1), complex(n2)
    c0, c1, c2 = interfaces._cosines([n0, n1, n2], theta0)
    if c1 == 0:
        raise coded(ValueError(i18n.T("single_film: the wave grazes inside the layer (cos θ1 = 0): the Airy sum is "
                                      "0/0")), "airy.grazing")
    r01, t01 = _rt(n0, c0, n1, c1, pol)
    r12, t12 = _rt(n1, c1, n2, c2, pol)
    beta = 2 * math.pi * n1 * c1 * d / lam
    e2 = cmath.exp(2j * beta)
    den = 1 + r01 * r12 * e2
    if den == 0:
        raise coded(ValueError(i18n.T("single_film: the Airy sum is 0/0 here (D = 0)")), "airy.grazing")
    r = (r01 + r12 * e2) / den
    t = t01 * t12 * cmath.exp(1j * beta) / den
    R = abs(r) ** 2
    T = _power(n0, c0, n2, c2, pol) * abs(t) ** 2
    # first-order rounding bound (absolute errors of the pieces, then of N, D, r, t)
    if pol == "s":
        k01, k12 = _kappa(n0 * c0, n1 * c1), _kappa(n1 * c1, n2 * c2)
    else:
        k01, k12 = _kappa(n1 * c0, n0 * c1), _kappa(n2 * c1, n1 * c2)
    a01, a12, ae = abs(r01), abs(r12), abs(e2)
    e01, e12 = 6 * U * k01 * (1 + a01), 6 * U * k12 * (1 + a12)
    eN = e01 + e12 * ae + 2 * U * a12 * ae + U * (a01 + a12 * ae)
    eD = (e01 * a12 + e12 * a01) * ae + 2 * U * a01 * a12 * ae + 2 * U * (1 + a01 * a12 * ae)
    aD = abs(den)
    err_r = (eN + abs(r) * eD) / aD + 2 * U * abs(r)
    err_t = abs(t) * (6 * U * (k01 + k12) + eD / aD + 5 * U)
    return {"r": complex(r), "t": complex(t), "R": float(R), "T": float(T), "A": float(1 - R - T), "D": complex(den),
            "err_r": float(err_r), "err_t": float(err_t)}


def stack_error_single_layer(n0, n1, n2, d: float, lam: float, theta0: float, pol: str) -> dict:
    """First-order bound of the rounding of ``interfaces.stack`` for one layer (the route ``single_film`` is compared
    with): [B, C] = Mt v with the layer's scaled characteristic matrix Mt (``interfaces._layer``) and the exit vector v;
    each entry of Mt carries <= 8u (exponentials, a sum, a division, two products), each of B, C <= 12u of the sum of
    the moduli of its two products; the denominator den = eta0 B + C (s) or n0 B + c0 C (p) then carries
    Delta = |w0| dB + |w1| dC + 2u (|w0 B| + |w1 C|), and r, t: (1 + |r|) Delta / |den| + 3u |r|,
    |t| (Delta / |den| + 5u), T: T (2 Delta / |den| + 8u). Returns dict(err_r, err_t, err_T, cond) with
    cond = (|w0 B| + |w1 C|) / |den|."""
    ns = [complex(n0), complex(n1), complex(n2)]
    cos = interfaces._cosines(ns, theta0)
    Mt, S = interfaces._layer(ns[1], cos[1], d, lam, pol)
    v = interfaces._exit_vector(ns[2], cos[2], pol)
    B, C = Mt @ v
    dB = 12 * U * (abs(Mt[0, 0] * v[0]) + abs(Mt[0, 1] * v[1]))
    dC = 12 * U * (abs(Mt[1, 0] * v[0]) + abs(Mt[1, 1] * v[1]))
    w0, w1 = (ns[0] * cos[0], 1.0) if pol == "s" else (ns[0], cos[0])
    den = w0 * B + w1 * C
    mag = abs(w0 * B) + abs(w1 * C)
    if den == 0:
        return {"err_r": math.inf, "err_t": math.inf, "err_T": math.inf, "cond": math.inf}
    delta = abs(w0) * dB + abs(w1) * dC + 2 * U * mag
    r = abs((w0 * B - w1 * C) / den)
    t = abs(2 * w0 * w1 / den) * math.exp(-S) if pol == "p" else abs(2 * w0 / den) * math.exp(-S)
    if pol == "s":
        T = 4 * w0.real * (ns[2] * cos[2]).real / abs(den) ** 2 * math.exp(-2 * S)
    else:
        T = 4 * (ns[0] * cos[0].conjugate()).real * (ns[2] * cos[2].conjugate()).real / abs(den) ** 2 * math.exp(-2 * S)
    return {"err_r": float((1 + r) * delta / abs(den) + 3 * U * r), "err_t": float(t * (delta / abs(den) + 5 * U)),
            "err_T": float(abs(T) * (2 * delta / abs(den) + 8 * U)), "cond": float(mag / abs(den))}


def airy(n0: float, n1: float, n2: float, d: float, lam: float, theta0: float, pol: str) -> dict:
    """Airy intensity formula of a lossless film (real indices) with propagating waves in all three media.
    Returns dict(T, T_max, F, Delta, R10, R12, err_T).

    T = T_max / (1 + F sin^2(Delta/2)) = T01 T12 / ((1 - rho)^2 + 4 rho sin^2(Delta/2)), rho = sqrt(R10 R12),
    Delta = 2 beta + arg r10 + arg r12 with beta = 2 pi n1 cos(theta1) d / lambda. The cosines are those of
    ``interfaces.stack`` and beta is computed by the same float expression as its layer phase, so that a comparison
    with the matrices tests the formula and not the rounding of sin^2(theta) or of the phase (review 2026-10-23: with
    its own asin/cos the formula disagreed with the matrices by up to 0.1 just below grazing inside the film, where
    F ~ 1e13). The real Fresnel coefficients have arg 0 or pi, so sin^2(Delta/2) is sin^2(beta) or cos^2(beta)
    exactly. err_T bounds the rounding of this evaluation to first order in u = 2^-53: r01, r12 <= 5u, rho <= 12u
    (absolute), 1 - rho then <= 12u + u (1 - rho), T01, T12 <= 10u relative, sin^2 <= 5u relative, the denominator
    (a sum of two non-negative terms) to 2 (1 - rho) d(1 - rho) + 4 sin^2 d rho + 20 rho u sin^2 + 3u den, and T to
    T (22u + d den / den). Raises ValueError when a wave in the film or in the exit medium does not propagate, or
    grazes (rho = 1 in float)."""
    for n in (n0, n1, n2):
        if isinstance(n, complex) or float(n) <= 0:
            raise coded(ValueError(i18n.T("airy: real positive indices only (a lossless film)")), "airy.lossy_index")
    ns = [complex(n0), complex(n1), complex(n2)]
    c0, c1, c2 = interfaces._cosines(ns, theta0)
    for c in (c1, c2):
        if c.imag != 0 or c.real <= 0:
            raise coded(ValueError(i18n.T("airy: total reflection at a film boundary (no propagating wave)")),
                        "airy.total_reflection")
    r01, t01 = _rt(ns[0], c0, ns[1], c1, pol)
    r12, t12 = _rt(ns[1], c1, ns[2], c2, pol)
    R10, R12 = abs(r01) ** 2, abs(r12) ** 2  # r10 = -r01
    T01 = _power(ns[0], c0, ns[1], c1, pol) * abs(t01) ** 2
    T12 = _power(ns[1], c1, ns[2], c2, pol) * abs(t12) ** 2
    rho = math.sqrt(R10 * R12)
    a = 1.0 - rho
    beta = (2 * math.pi * ns[1] * c1 * d / lam).real  # the layer phase of interfaces._layer, the same float
    # arg r10 + arg r12 is a multiple of pi: m even -> sin^2(Delta/2) = sin^2(beta), m odd -> cos^2(beta)
    m = (1 if (-r01).real < 0 else 0) + (1 if r12.real < 0 else 0)
    s2 = math.sin(beta) ** 2 if m % 2 == 0 else math.cos(beta) ** 2
    den = a * a + 4 * rho * s2
    if a <= 0 or den <= 0:
        raise coded(ValueError(i18n.T("airy: the wave grazes inside the film (ρ = 1 in floating point): the formula "
                                      "is 0/0")), "airy.grazing")
    T = T01 * T12 / den
    d_rho = 5 * U * (abs(r01) + abs(r12)) + 2 * U * rho
    d_a = d_rho + U * a
    d_den = 2 * a * d_a + 4 * s2 * d_rho + 20 * U * rho * s2 + 3 * U * den
    Delta = 2 * beta + math.pi * m
    return {"T": T, "T_max": T01 * T12 / (a * a), "F": 4 * rho / (a * a), "Delta": Delta, "R10": R10, "R12": R12,
            "err_T": float(T * (22 * U + d_den / den))}


def quarter_wave_R(n0: float, n1: float, n2: float) -> float:
    """Reflectance of a quarter-wave layer n1 between n0 and n2 at its design wavelength, normal incidence."""
    return ((n0 * n2 - n1 * n1) / (n0 * n2 + n1 * n1)) ** 2


def quarter_wave_stack_R(n0: float, n_a: float, n_b: float, n_s: float, pairs: int) -> float:
    """Reflectance of (A B)^pairs on a substrate n_s, layer A next to the incidence medium n0, every layer a quarter
    wave at the design wavelength, normal incidence: Y = n_s (n_a/n_b)^{2 pairs}, R = ((n0 - Y)/(n0 + Y))^2."""
    Y = n_s * (n_a / n_b) ** (2 * int(pairs))
    return ((n0 - Y) / (n0 + Y)) ** 2


def ftir_T(n1: float, n_gap: float, d: float, lam: float, theta: float, pol: str) -> float:
    """Transmittance through a gap of index n_gap and width d between two media of index n1, beyond the critical
    angle (n1 sin theta > n_gap): the tunnelling formula T = 1/(1 + ((a^2 + b^2)/(2ab))^2 sinh^2(kappa d)), s: a = k_z,
    b = kappa; p: a = k_z/n1^2, b = kappa/n_gap^2. Written with sinh(kappa d)/kappa, an entire function of kappa^2,
    so the critical angle itself (kappa = 0: T = 1/(1 + (a d n^2/2)^2), n^2 = 1 for s, n_gap^2 for p) is a regular
    point; below it kappa^2 < 0 continues the same expression into the symmetric-film (Airy) transmittance."""
    k0 = 2 * math.pi / lam
    q = n1 * n1 * math.sin(theta) ** 2 - n_gap * n_gap
    kappa2 = k0 * k0 * q
    log_sh = None  # for an opaque gap (kappa d > 300) sinh(kappa d)/kappa is carried as its logarithm
    if q > 0:
        kap = math.sqrt(kappa2)
        if kap * d > 300:
            log_sh = kap * d - math.log(2 * kap) + math.log1p(-math.exp(-2 * kap * d))
            sh = 0.0
        else:
            sh = math.sinh(kap * d) / kap if kap * d > 1e-8 else d * (1 + (kap * d) ** 2 / 6)
    elif q < 0:
        k = math.sqrt(-kappa2)
        sh = math.sin(k * d) / k if k * d > 1e-8 else d * (1 - (k * d) ** 2 / 6)
    else:
        sh = d
    kz = k0 * n1 * math.cos(theta)
    if pol == "s":
        a, b2, w = kz, kappa2, 1.0
    elif pol == "p":
        a, b2, w = kz / n1 ** 2, kappa2 / n_gap ** 4, n_gap ** 4
    else:
        raise ValueError("pol must be 's' or 'p'")
    if log_sh is not None:  # T = 1/(1 + X), X = A sh^2 huge: T = e^{-log X} / (1 + e^{-log X})
        logX = math.log((a * a + b2) ** 2 / (4 * a * a) * w) + 2 * log_sh
        return math.exp(-logX) / (1.0 + math.exp(-logX))
    return 1.0 / (1.0 + (a * a + b2) ** 2 / (4 * a * a) * w * sh * sh)


def evanescent_q(n1: float, n2: float, theta: float) -> float:
    """q = n1^2 sin^2(theta) - n2^2 (> 0 beyond the critical angle) for the binary64 inputs, evaluated in 160-bit
    arithmetic and rounded once: in binary64 the subtraction would carry an error ~ eps n1^2 sin^2 theta, i.e. a
    relative error eps n1^2 sin^2(theta)/q, 2.8e-8 at theta_c + 1e-7 deg for glass 1.5 / air (review 2026-10-23,
    V5-2). For binary64 inputs q is never exactly 0 (sin of a nonzero rational is irrational)."""
    with mpmath.workprec(160):
        q = (mpmath.mpf(float(n1)) * mpmath.sin(mpmath.mpf(float(theta)))) ** 2 - mpmath.mpf(float(n2)) ** 2
        return float(q)


def evanescent_length(n1: float, n2: float, lam: float, theta: float) -> float:
    """Amplitude decay length 1/kappa of the evanescent wave in n2 beyond the critical angle (|E|^2 ~ exp(-2 z/L)),
    to one rounding for the binary64 inputs (q in 160-bit arithmetic, ``evanescent_q``)."""
    with mpmath.workprec(160):
        q = (mpmath.mpf(float(n1)) * mpmath.sin(mpmath.mpf(float(theta)))) ** 2 - mpmath.mpf(float(n2)) ** 2
        if q <= 0:
            raise coded(ValueError(T("evanescent length: the angle is below the critical one")), "film.below_critical")
        return float(mpmath.mpf(float(lam)) / (2 * mpmath.pi * mpmath.sqrt(q)))


_GL_X, _GL_W = np.polynomial.legendre.leggauss(16)
GL_WIDTH = 4.0  # sub-interval width in units of the fastest scale of |E|^2 (decay rate or cross-term frequency)
GL_MAX_NODES = 400_000


def _layer_nodes(a: float, b: float, rate: float, min_nodes: int = 0):
    """Nodes and weights of composite 16-point Gauss-Legendre on [a, b], sub-intervals of width <= GL_WIDTH / rate.
    For f = e^{-g z} cos(o z) with (g + o) w <= 2 GL_WIDTH the rule's error is (2 GL_WIDTH)^32 (16!)^4 /
    (33 (32!)^3) ~ 2.5e-26 of max|f| w per sub-interval (the remainder term of Gauss-Legendre); the nodes are
    interior."""
    L = b - a
    m = max(1, math.ceil(L * rate / GL_WIDTH), math.ceil(min_nodes / 16))
    if 16 * m > GL_MAX_NODES:
        raise coded(ValueError(T("Joule absorption: {n:d} quadrature nodes needed in one layer (the limit is {lim:d})",
                                 n=16 * m, lim=GL_MAX_NODES)), "film.too_many_nodes")
    edges = np.linspace(a, b, m + 1)
    h = 0.5 * np.diff(edges)
    mid = 0.5 * (edges[:-1] + edges[1:])
    z = (mid[:, None] + h[:, None] * _GL_X[None, :]).ravel()
    w = (h[:, None] * _GL_W[None, :]).ravel()
    return z, w


def joule_absorption_s(ns, ds, lam: float, theta0: float, points: int | None = None) -> dict:
    """Absorbed fraction of s-polarized light as Joule heating in the layers, from the field |E|^2 of
    ``interfaces.field_profile``. In layer j, |E|^2 is a combination of exp(-+2 Im(k_z) z) and exp(2i Re(k_z) z),
    k_z = k0 n_j cos(theta_j); the integral is composite 16-point Gauss-Legendre with sub-intervals of at most
    GL_WIDTH / max(2 |Im k_z|, 2 |Re k_z|, 1/d) (``_layer_nodes``), so the nodes follow the skin depth (review
    2026-10-23, V5-3: Simpson with 2001 points could not resolve 1.2 nm in 500 nm). ``points``: an optional minimum
    number of nodes per layer. Returns dict(A, per_layer, nodes)."""
    ns = [complex(n) for n in ns]
    if len(ds) != len(ns) - 2:
        raise ValueError("need one thickness per inner layer")
    k0 = 2 * math.pi / lam
    c0 = _cos(ns[0], ns[0], theta0)
    flux = (ns[0] * c0).real
    edges = np.concatenate([[0.0], np.cumsum(ds)])
    per = []
    nodes = 0
    for j, n in enumerate(ns[1:-1]):
        im_eps = (n * n).imag
        if im_eps == 0 or ds[j] == 0:
            per.append(0.0)
            continue
        a, b = float(edges[j]), float(edges[j + 1])
        kz = k0 * n * _cos(ns[0], n, theta0)
        rate = max(2 * abs(kz.imag), 2 * abs(kz.real), 1.0 / (b - a))
        z, w = _layer_nodes(a, b, rate, points or 0)  # Gauss-Legendre nodes are interior: no boundary ambiguity
        E2 = interfaces.field_profile(ns, list(ds), lam, theta0, z, "s")
        nodes += len(z)
        per.append(float(k0 * im_eps * float(np.dot(w, E2)) / flux))
    return {"A": float(sum(per)), "per_layer": per, "nodes": nodes}
