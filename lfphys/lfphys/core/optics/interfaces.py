# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Plane electromagnetic waves at planar interfaces and multilayer stacks (exact solutions of Maxwell's equations
for homogeneous, isotropic, linear media; complex refractive index n = n' + i n'' for absorption, time dependence
exp(-i omega t)).

Fresnel amplitude coefficients (Born & Wolf convention for p: r_p = (n2 cos ti - n1 cos tt)/(n2 cos ti + n1 cos tt),
so that r_p = -r_s at normal incidence):
    r_s = (n1 cos ti - n2 cos tt)/(n1 cos ti + n2 cos tt),   t_s = 2 n1 cos ti/(n1 cos ti + n2 cos tt),
    t_p = 2 n1 cos ti/(n2 cos ti + n1 cos tt),   n1 sin ti = n2 sin tt (complex cos tt on the decaying branch).
Power: R = |r|^2; T_s = Re(n2 cos tt)/Re(n1 cos ti) |t_s|^2, T_p = Re(n2 conj(cos tt))/Re(n1 conj(cos ti)) |t_p|^2.

Multilayers: the transfer-matrix method in the formulation of Byrnes (arXiv:1603.02720): each layer j of thickness d_j
contributes a propagation phase delta_j = 2 pi n_j d_j cos(theta_j)/lambda and each interface a matrix
(1/t)[[1, r], [r, 1]].
"""

from __future__ import annotations

import cmath
import math

import numpy as np

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Плоские волны на границах сред и многослойные покрытия",
    "statement": "Уравнения Френеля (s и p), углы Брюстера и полного внутреннего отражения, матрицы переноса для "
                 "стопки слоёв (просветление, зеркала, интерферометр Фабри–Перо); баланс R + T + A = 1.",
    "validity": "однородные изотропные линейные среды, плоские границы, плоская волна (уравнения Максвелла точно)",
    "basis": ["Born & Wolf, Principles of Optics, §1.5–1.6", "Byrnes, arXiv:1603.02720 (метод матриц переноса)"],
    "conflicts": [],
}


def snell_cos(n1, n2, cos_i):
    """cos(theta_t) for n1 sin(ti) = n2 sin(tt), on the branch with Im(n2 cos tt) >= 0 (decaying into medium 2) and
    Re >= 0 for a propagating wave."""
    sin_i2 = 1.0 - cos_i * cos_i
    ct = cmath.sqrt(1.0 - (n1 / n2) ** 2 * sin_i2)
    if (n2 * ct).imag < 0 or ((n2 * ct).imag == 0 and (n2 * ct).real < 0):
        ct = -ct
    return ct


def fresnel(n1, n2, theta_i: float, pol: str):
    """(r, t, R, T) for a single interface from medium n1 to n2 at incidence angle theta_i (rad), pol 's' or 'p'."""
    ci = complex(math.cos(theta_i))
    ct = snell_cos(n1, n2, ci)
    if pol == "s":
        den = n1 * ci + n2 * ct
        r, t = (n1 * ci - n2 * ct) / den, 2 * n1 * ci / den
        T = (n2 * ct).real / (n1 * ci).real * abs(t) ** 2
    elif pol == "p":
        den = n2 * ci + n1 * ct
        r, t = (n2 * ci - n1 * ct) / den, 2 * n1 * ci / den
        T = (n2 * ct.conjugate()).real / (n1 * ci.conjugate()).real * abs(t) ** 2
    else:
        raise ValueError("pol must be 's' or 'p'")
    return r, t, abs(r) ** 2, T


def brewster(n1: float, n2: float) -> float:
    return math.atan2(n2, n1)


def critical(n1: float, n2: float) -> float | None:
    return math.asin(n2 / n1) if n2 < n1 else None


def _cosines(ns, theta0):
    s0 = ns[0] * math.sin(theta0)
    cos = [cmath.sqrt(1 - (s0 / n) ** 2) for n in ns]
    for j, n in enumerate(ns):  # forward (decaying / propagating) branch in every medium
        if (n * cos[j]).imag < 0 or ((n * cos[j]).imag == 0 and (n * cos[j]).real < 0):
            cos[j] = -cos[j]
    return cos


def _sinc(d):
    return cmath.sin(d) / d if abs(d) > 1e-8 else 1 - d * d / 6


def _layer(n, c, d, lam, pol):
    """Characteristic matrix of one layer, [E, H] at its entrance = M [E, H] at its exit (tangential fields; time
    factor e^{-i omega t}, so an absorbing medium has Im n > 0 and M = [[cos d, -i sin d / eta], [-i eta sin d,
    cos d]]). Written without dividing by the tilted admittance eta, so grazing propagation inside the layer
    (cos theta = 0) is a regular limit. Returned as (Mt, s) with M = e^s Mt: for an evanescent or absorbing layer
    (|Im delta| > 1) the growth e^{|Im delta|} is carried as the exponent s, so an opaque layer (|Im delta| of
    hundreds or thousands) does not overflow (review 2026-10-23, E3)."""
    delta = 2 * math.pi * n * c * d / lam
    k0d = 2 * math.pi * d / lam
    s = abs(delta.imag) if abs(delta.imag) > 1.0 else 0.0
    if s:
        ep, em = cmath.exp(1j * delta - s), cmath.exp(-1j * delta - s)  # both of modulus <= 1
        cd, sd = 0.5 * (ep + em), (ep - em) / 2j
        sinc = sd / delta  # |delta| > 1 here
    else:
        cd, sd, sinc = cmath.cos(delta), cmath.sin(delta), _sinc(delta)
    if pol == "s":  # eta = n cos theta
        return np.array([[cd, -1j * k0d * sinc], [-1j * n * c * sd, cd]]), s
    # p: eta = n / cos theta
    return np.array([[cd, -1j * c * sd / n], [-1j * k0d * n * n * sinc, cd]]), s


def _exit_vector(nsub, cs, pol):
    return np.array([1.0, nsub * cs]) if pol == "s" else np.array([cs, nsub])  # p: cos_s [1, eta_s]


def stack(ns, ds, lam: float, theta0: float, pol: str):
    """Multilayer: ns = [n_in, n_1, ..., n_N, n_out] (complex allowed), ds = [d_1, ..., d_N] (same unit as lam),
    incidence angle theta0 in medium n_in (lossless). Returns dict(r, t, R, T, A) with A = 1 - R - T the absorbed fraction
    (zero for lossless layers); r, t in the convention of ``fresnel`` (Born & Wolf for p).

    Characteristic (Abeles) matrices of the layers act on the tangential fields: [B, C] = prod M_j [1, eta_out];
    r = (eta0 B - C)/(eta0 B + C), T = 4 Re(eta0) Re(eta_out) / |eta0 B + C|^2, with eta = n cos theta (s) or
    n / cos theta (p). For p the vector is scaled by cos theta of the outer media, so grazing incidence or exit
    (cos theta = 0) needs no division; inside the layers a sinc form does the same. (The interface-by-interface form
    divides by the inner interfaces' t, which vanishes when a wave grazes inside a layer: review of v05, 2026-10-23.)
    The growth of evanescent layers is carried as a separate exponent S, [B, C] = e^S [Bt, Ct]: r needs only the
    ratio, t = ... e^{-S} and T = ... e^{-2S} go smoothly to 0 for an opaque structure instead of overflowing."""
    ns = [complex(n) for n in ns]
    if len(ds) != len(ns) - 2:
        raise ValueError("need one thickness per inner layer")
    cos = _cosines(ns, theta0)
    M = np.eye(2, dtype=complex)
    S = 0.0
    for j in range(1, len(ns) - 1):
        Mj, sj = _layer(ns[j], cos[j], ds[j - 1], lam, pol)
        M = M @ Mj
        S += sj
        m = float(np.max(np.abs(M)))
        if m > 1e100 or 0 < m < 1e-100:  # keep the running product in range
            M /= m
            S += math.log(m)
    n0, c0, nsub, cs = ns[0], cos[0], ns[-1], cos[-1]
    if pol not in ("s", "p"):
        raise ValueError("pol must be 's' or 'p'")
    B, C = M @ _exit_vector(nsub, cs, pol)
    if pol == "s":
        e0, es = n0 * c0, nsub * cs
        den = e0 * B + C
        r = (e0 * B - C) / den
        t = 2 * e0 / den * math.exp(-S)
        T = 4 * e0.real * es.real / abs(den) ** 2 * math.exp(-2 * S)
    else:
        den = n0 * B + c0 * C
        r = -(n0 * B - c0 * C) / den  # Born & Wolf sign for p
        t = 2 * n0 * c0 / den * math.exp(-S)  # ratio of the total E amplitudes
        T = 4 * (n0 * c0.conjugate()).real * (nsub * cs.conjugate()).real / abs(den) ** 2 * math.exp(-2 * S)
    R = abs(r) ** 2
    return {"r": complex(r), "t": complex(t), "R": float(R), "T": float(T), "A": float(1 - R - T)}


def field_profile(ns, ds, lam: float, theta0: float, z, pol: str = "s"):
    """|E|^2 of an s-polarized wave relative to the incident one, at depths z measured from the first interface
    (z < 0: incidence medium, z > total thickness: exit medium). Tangential [E, H] is carried back from the exit,
    [E, H](zeta) = M(d - zeta) [E, H](end of the layer), with the characteristic matrices of ``stack`` (no division
    by interface coefficients), starting from [1, eta_out] and normalised at the end by the entrance value (the
    exponents of opaque layers are carried separately, so nothing overflows); in the incidence medium
    E = e^{ikz} + r e^{-ikz}. Only s: for p the tangential E is E cos(theta) and |E|^2 needs both components."""
    if pol != "s":
        raise ValueError("field_profile: s polarization only")
    ns = [complex(n) for n in ns]
    cos = _cosines(ns, theta0)
    nL = len(ns)
    ends = [None] * nL  # (tangential [E, H] at the far side of inner layer j, its log scale), exit field = [1, eta_s]
    EH, S = _exit_vector(ns[-1], cos[-1], "s").astype(complex), 0.0
    for j in range(nL - 2, 0, -1):
        ends[j] = (EH, S)
        Mj, sj = _layer(ns[j], cos[j], ds[j - 1], lam, "s")
        EH, S = Mj @ EH, S + sj
        m = float(np.max(np.abs(EH)))
        if m > 0:
            EH, S = EH / m, S + math.log(m)
    e0 = ns[0] * cos[0]
    den = e0 * EH[0] + EH[1]  # the true fields are tau * (vector) * e^{scale}, tau = 2 eta0 / (den e^S)
    tau = 2 * e0 / den
    r = (e0 * EH[0] - EH[1]) / den
    edges = np.concatenate([[0.0], np.cumsum(ds)]) if len(ds) else np.array([0.0])
    k0 = 2 * math.pi * ns[0] * cos[0] / lam
    ks = 2 * math.pi * ns[-1] * cos[-1] / lam
    z = np.asarray(z, float)
    out = np.empty(z.shape)
    for idx, zz in np.ndenumerate(z):
        if zz < 0:
            out[idx] = abs(cmath.exp(1j * k0 * zz) + r * cmath.exp(-1j * k0 * zz)) ** 2
        elif zz >= edges[-1]:
            out[idx] = abs(tau * cmath.exp(1j * ks * (zz - edges[-1]))) ** 2 * math.exp(-2 * S)
        else:
            j = int(np.searchsorted(edges, zz, side="right"))
            vec, sc_ = ends[j]
            Mr, sr = _layer(ns[j], cos[j], edges[j] - zz, lam, "s")
            E = (Mr @ vec)[0]
            out[idx] = abs(tau * E) ** 2 * math.exp(2 * (sc_ + sr - S))
    return out
