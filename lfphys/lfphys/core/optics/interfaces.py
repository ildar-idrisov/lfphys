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

Fields inside the structure (``field_profile``, ``field_components``, ``field_jones``, ``field_intensity``). Axes: z
along the normal into the structure (the first interface at z = 0), x along the surface in the plane of incidence
(k_x = k0 n_in sin theta0 >= 0), y = z x x normal to it. Each wave's s unit vector is y; its p unit vector is
p = s x k (in the plane of incidence), so that (p, s, k) is right-handed for every wave: the incident p is
(cos theta0, 0, -sin theta0), the reflected p (-cos theta0, 0, -sin theta0). The coefficients above (Born & Wolf's
for p) are the ratios of these components: Born & Wolf's p vectors are -p for every wave, so the ratios agree. The
characteristic matrices carry the tangential fields (s: E_y and H_t = -Z0 H_x; p: E_x and Z0 H_y); the components
normal to the surface follow from Maxwell's equations with the conserved k_x: s: Z0 H_z = n_in sin(theta0) E_y;
p: E_z = -n_in sin(theta0) Z0 H_y / n_j^2 (from curl H = -i omega eps E). H is given as Z0 H (the units of E). For
light of any polarization with incident Jones vector (E_p, E_s) the field is E_p e_p(z) + E_s e_s(z); e_p has no y
component and e_s only a y component, so |E|^2 = rho_pp |e_p|^2 + rho_ss |e_s|^2 for any density matrix rho of the
incident light (unpolarised: the mean of the two profiles), without an interference term.

An absorbing incidence medium (n_in = n' + i kappa, e.g. a glass of ``core.optics.materials``, review EX2, R2-E F1):
k_x is real, k_x / k0 = n' sin theta0, so that the field is uniform along the surface: the incident wave is the
inhomogeneous wave whose planes of constant amplitude are parallel to the interface, as after entering through a face
parallel to it (Byrnes, arXiv:1603.02720, §4.4.1 and App. B, D: n0 sin theta0 must be real). theta0 is then the
angle of Snell's law with the real parts (a ray entering through a parallel face at theta_air has n' sin theta0 =
sin theta_air); the direction of the phase fronts differs from it by O((kappa / n')^2). Every medium's cos theta is
on the forward branch, Im(n cos theta) > 0, or Re(n cos theta) >= 0 for a lossless propagating wave (the two agree
for a real k_x; App. D.2). R = |r|^2 and T are the reflected and the transmitted waves' energy fluxes through the
interfaces relative to the incident wave's flux at the first interface (z = 0): the incident wave's decay on its way
there (exp(-2 k0 Im(n_in cos theta_in) L) over a normal distance L) is the caller's. The incident and the reflected
waves overlap and interfere in an absorbing medium, so the flux entering the structure is not 1 - R: it is 1 - R -
A_in with A_in = -2 Im(r) Im(n_in cos theta_in) / Re(n_in cos theta_in) (s) and -2 Im(r) Im(cos theta_in conj(n_in))
/ Re(n_in conj(cos theta_in)) (p), the extra (or, negative, the missing) absorption of the standing wave just before
the interface (Byrnes, App. B). ``stack`` returns it as A_in (0 for a real n_in); A = 1 - R - T is the absorption in
the layers plus A_in, and R + T + A = 1 still holds. The net flux into the structure, 1 - R - A_in = T + (absorbed in
the layers), is >= 0; R itself may exceed 1 by O(kappa / n') just above the critical angle (then A_in < 0), and |A_in|
grows towards grazing incidence, where the incident wave is strongly inhomogeneous (Re and Im of n_in cos theta_in
comparable): |A_in| <= 3 Im(n_in cos theta_in) / Re(n_in cos theta_in), about 3 kappa / (n' cos^2 theta_in) (tests),
e.g. 1.9e-5 for N-SF11 (kappa 2.8e-7 n') at 405 nm and 85 degrees.
"""

from __future__ import annotations

import cmath
import math

import numpy as np

from lfphys.codes import coded
from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Plane waves at interfaces and multilayer coatings"),
    "statement": T("Fresnel equations (s and p), Brewster's angle and the angle of total internal reflection, "
                   "transfer matrices for a stack of layers (anti-reflection coatings, mirrors, the Fabry–Pérot "
                   "interferometer); the balance R + T + A = 1; the electric and magnetic fields inside and around "
                   "the structure for s and p light and for any polarisation; the group delays of the reflected and "
                   "the transmitted light with the materials' dispersion."),
    "validity": T("homogeneous isotropic linear media, flat interfaces, a plane wave (Maxwell's equations exactly)"),
    "basis": ["Born & Wolf, Principles of Optics, §1.5–1.6",
              T("Byrnes, arXiv:1603.02720 (the transfer-matrix method)")],
    "conflicts": [],
}


def snell_cos(n1, n2, cos_i):
    """cos(theta_t) for n1 sin(ti) = n2 sin(tt), on the branch with Im(n2 cos tt) >= 0 (decaying into medium 2) and
    Re >= 0 for a propagating wave; n1 real (a lossless incidence medium; for an absorbing one ``fresnel`` and
    ``stack`` take the real k_x of the module docstring): a complex n1 is refused, ``optics.absorbing_incidence``."""
    if complex(n1).imag != 0:
        raise coded(ValueError(T("snell_cos takes a real incidence index (an absorbing incidence medium: use "
                                 "interfaces.stack or fresnel, which take k_x = Re(n_in) sin θ)")),
                    "optics.absorbing_incidence")
    sin_i2 = 1.0 - cos_i * cos_i
    ct = cmath.sqrt(1.0 - (n1 / n2) ** 2 * sin_i2)
    if (n2 * ct).imag < 0 or ((n2 * ct).imag == 0 and (n2 * ct).real < 0):
        ct = -ct
    return ct


def fresnel(n1, n2, theta_i: float, pol: str):
    """(r, t, R, T) for a single interface from medium n1 to n2 at incidence angle theta_i (rad), pol 's' or 'p'; the
    cosines of ``stack`` (``_cosines``: cos theta_i itself for a real n1; an absorbing n1 as in the module docstring,
    T then relative to the incident wave's flux at the interface)."""
    ci, ct = _cosines([complex(n1), complex(n2)], theta_i)
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


def _kx(ns, theta0) -> float:
    """k_x / k0 = Re(n_in) sin theta0: real, so that the field is uniform along the surface (the module docstring,
    «An absorbing incidence medium»)."""
    return complex(ns[0]).real * math.sin(theta0)


def _backward(q) -> bool:
    """Whether q = n cos theta is the backward root of (n cos theta)^2 (to be negated). The forward root has
    Im(n cos theta) > 0 (the wave decays forwards: an absorbing medium or an evanescent wave); where Im is zero or
    round-off of |n cos theta| (a lossless, propagating wave), Re(n cos theta) >= 0 (its energy flows forwards). With
    a real k_x and Im n >= 0 the two criteria agree (Byrnes, arXiv:1603.02720, App. D.2): (n cos theta)^2 = n^2 -
    (k_x/k0)^2 has Im >= 0, so its forward root lies in the first quadrant."""
    if abs(q.imag) > 8 * 2.220446049250313e-16 * abs(q):
        return q.imag < 0
    return q.real < 0


def _cosines(ns, theta0):
    """cos theta in every medium for the real k_x / k0 = s0 = Re(n_in) sin theta0, on the forward branch
    (``_backward``). The incidence medium's own cosine is computed without cancellation: cos theta0 itself for a real
    n_in; n_in cos theta_in = sqrt((n' cos theta0)^2 - kappa^2 + 2i n' kappa) for n_in = n' + i kappa (review EX2,
    R2-E F10: sqrt(1 - sin^2) loses the relative precision near grazing incidence). A medium of the same index as the
    incidence medium gets the same cosine."""
    n0 = ns[0]
    s0 = _kx(ns, theta0)
    if n0.imag == 0:
        c0 = complex(math.cos(theta0))
    else:
        a, k = n0.real, n0.imag
        q0 = cmath.sqrt(complex((a * math.cos(theta0)) ** 2 - k * k, 2 * a * k))
        c0 = (-q0 if _backward(q0) else q0) / n0
    cos = []
    for n in ns:
        if n == n0:
            cos.append(c0)
            continue
        c = cmath.sqrt(1 - (s0 / n) ** 2)
        cos.append(-c if _backward(n * c) else c)
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
    incidence angle theta0 in medium n_in (k_x / k0 = Re(n_in) sin theta0: an absorbing incidence medium as in the
    module docstring). Returns dict(r, t, R, T, A, A_in) with A = 1 - R - T the absorbed fraction (zero for lossless
    layers and a real n_in) and A_in its part absorbed just before the first interface by the interference of the
    incident and the reflected waves in an absorbing incidence medium (0 for a real n_in; module docstring); r, t in
    the convention of ``fresnel`` (Born & Wolf for p).

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
        # T = Re(eta_out) / Re(eta0) |t|^2; |e0|^2 / Re(e0) = Re(e0) for a real n0 (an absorbing one: module docstring)
        f0 = e0.real if n0.imag == 0 else abs(e0) ** 2 / e0.real
        T = 4 * f0 * es.real / abs(den) ** 2 * math.exp(-2 * S)
    else:
        den = n0 * B + c0 * C
        r = -(n0 * B - c0 * C) / den  # Born & Wolf sign for p
        t = 2 * n0 * c0 / den * math.exp(-S)  # ratio of the total E amplitudes
        q0 = (n0 * c0.conjugate()).real
        f0 = q0 if n0.imag == 0 else abs(n0 * c0) ** 2 / q0
        T = 4 * f0 * (nsub * cs.conjugate()).real / abs(den) ** 2 * math.exp(-2 * S)
    R = abs(r) ** 2
    if n0.imag == 0:
        a_in = 0.0
    elif pol == "s":  # the interference flux of the incident and reflected waves at z = 0 (module docstring)
        a_in = -2 * r.imag * e0.imag / e0.real
    else:
        a_in = -2 * r.imag * (c0 * n0.conjugate()).imag / (n0 * c0.conjugate()).real
    return {"r": complex(r), "t": complex(t), "R": float(R), "T": float(T), "A": float(1 - R - T),
            "A_in": float(a_in)}


def field_profile(ns, ds, lam: float, theta0: float, z, pol: str = "s"):
    """|E|^2 of an s- or p-polarized wave relative to the incident one, at depths z measured from the first interface
    (z < 0: incidence medium, z > total thickness: exit medium). Tangential [E, H] is carried back from the exit,
    [E, H](zeta) = M(d - zeta) [E, H](end of the layer), with the characteristic matrices of ``stack`` (no division
    by interface coefficients), starting from [1, eta_out] and normalised at the end by the entrance value (the
    exponents of opaque layers are carried separately, so nothing overflows); in the incidence medium
    E = e^{ikz} + r e^{-ikz}. s: |E_y|^2 (this code, unchanged since 2026-10-23). p: |E_x|^2 + |E_z|^2 from
    ``field_components`` (the tangential E_x and Z0 H_y carried by the same matrices, E_z = -n_in sin(theta0) Z0 H_y /
    n^2); see the module docstring for the axes and the p vectors."""
    if pol == "p":
        E, _ = field_components(ns, ds, lam, theta0, z, "p")
        return np.abs(E[..., 0]) ** 2 + np.abs(E[..., 2]) ** 2
    if pol != "s":
        raise ValueError("pol must be 's' or 'p'")
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


def _carry_back(ns, cos, ds, lam: float, pol: str):
    """The tangential fields [E_t, H_t] of a transmitted wave of unit amplitude, carried back from the exit through
    the layers with their characteristic matrices (the loop of ``field_profile``): ``ends[j]`` is the vector at the far
    side of inner layer j with its log scale; returned with the entrance vector and its log scale."""
    nL = len(ns)
    ends = [None] * nL
    EH, S = _exit_vector(ns[-1], cos[-1], pol).astype(complex), 0.0
    for j in range(nL - 2, 0, -1):
        ends[j] = (EH, S)
        Mj, sj = _layer(ns[j], cos[j], ds[j - 1], lam, pol)
        EH, S = Mj @ EH, S + sj
        m = float(np.max(np.abs(EH)))
        if m > 0:
            EH, S = EH / m, S + math.log(m)
    return ends, EH, S


def field_components(ns, ds, lam: float, theta0: float, z, pol: str = "s"):
    """Complex E and Z0 H (each of shape z.shape + (3,), components x, y, z of the module docstring's axes) of an
    s- or p-polarized plane wave of unit incident amplitude (incident E = p or s unit vector), at depths z measured
    from the first interface (z < 0: incidence medium, z >= total thickness: exit medium), time factor e^{-i omega t}.

    The tangential pair [E_t, H_t] (s: E_y and -Z0 H_x; p: E_x and Z0 H_y) is carried back from the exit by the
    characteristic matrices of ``stack`` (``_carry_back``) and scaled by tau = 2 eta0 / (eta0 B + C) (s) or
    2 n0 cos0 / (n0 B + cos0 C) (p), so that the incidence medium holds the incident wave and r e^{-ikz} with r of
    ``stack`` (p: E_x = cos0 (e^{ikz} - r e^{-ikz}), Z0 H_y = n0 (e^{ikz} + r e^{-ikz})) and the exit medium t e^{ikz}
    with t of ``stack``. The normal components follow from Maxwell's equations with k_x = k0 n0 sin theta0: s:
    Z0 H_z = n0 sin(theta0) E_y; p: E_z = -n0 sin(theta0) Z0 H_y / n^2 in the medium of index n at that depth."""
    ns = [complex(n) for n in ns]
    if len(ds) != len(ns) - 2:
        raise ValueError("need one thickness per inner layer")
    if pol not in ("s", "p"):
        raise ValueError("pol must be 's' or 'p'")
    cos = _cosines(ns, theta0)
    ends, EH, S = _carry_back(ns, cos, ds, lam, pol)
    n0, c0 = ns[0], cos[0]
    if pol == "s":
        e0 = n0 * c0
        den = e0 * EH[0] + EH[1]
        tau = 2 * e0 / den
        r = (e0 * EH[0] - EH[1]) / den
    else:
        den = n0 * EH[0] + c0 * EH[1]
        tau = 2 * n0 * c0 / den
        r = -(n0 * EH[0] - c0 * EH[1]) / den  # Born & Wolf sign, as in stack
    s0 = _kx(ns, theta0)  # k_x / k0 (real)
    edges = np.concatenate([[0.0], np.cumsum(ds)]) if len(ds) else np.array([0.0])
    k0 = 2 * math.pi * n0 * c0 / lam
    ks = 2 * math.pi * ns[-1] * cos[-1] / lam
    exit_v = _exit_vector(ns[-1], cos[-1], pol)
    z = np.asarray(z, float)
    Et = np.empty(z.shape, complex)
    Ht = np.empty(z.shape, complex)
    n2 = np.empty(z.shape, complex)
    for idx, zz in np.ndenumerate(z):
        if zz < 0:
            f, b = cmath.exp(1j * k0 * zz), cmath.exp(-1j * k0 * zz)
            if pol == "s":
                et, ht = f + r * b, e0 * (f - r * b)
            else:
                et, ht = c0 * (f - r * b), n0 * (f + r * b)
            nn = n0
        elif zz >= edges[-1]:
            a = tau * math.exp(-S) * cmath.exp(1j * ks * (zz - edges[-1]))
            et, ht = a * exit_v[0], a * exit_v[1]
            nn = ns[-1]
        else:
            j = int(np.searchsorted(edges, zz, side="right"))
            vec, sc_ = ends[j]
            Mr, sr = _layer(ns[j], cos[j], edges[j] - zz, lam, pol)
            et, ht = tau * (Mr @ vec) * math.exp(sc_ + sr - S)
            nn = ns[j]
        Et[idx], Ht[idx], n2[idx] = et, ht, nn * nn
    E = np.zeros(z.shape + (3,), complex)
    H = np.zeros(z.shape + (3,), complex)
    if pol == "s":
        E[..., 1] = Et
        H[..., 0] = -Ht
        H[..., 2] = s0 * Et
    else:
        E[..., 0] = Et
        H[..., 1] = Ht
        E[..., 2] = -s0 * Ht / n2
    return E, H


def field_jones(ns, ds, lam: float, theta0: float, z, jones):
    """E and Z0 H (complex, shape z.shape + (3,)) for incident light of Jones vector jones = (E_p, E_s) in the
    incident wave's basis (p = s x k, s = y; the module docstring): E_p times the p field plus E_s times the s field
    of ``field_components``."""
    jp, js = complex(jones[0]), complex(jones[1])
    Ep, Hp = field_components(ns, ds, lam, theta0, z, "p")
    Es, Hs = field_components(ns, ds, lam, theta0, z, "s")
    return jp * Ep + js * Es, jp * Hp + js * Hs


def field_intensity(ns, ds, lam: float, theta0: float, z, rho):
    """|E|^2 (time-averaged, relative to unit incident intensity times tr rho) for incident light of polarization
    density matrix rho in the (p, s) basis (a Jones vector J is taken as rho = J J^dagger; unpolarised light is
    rho = I/2): rho_pp |E|^2_p + rho_ss |E|^2_s with the profiles of ``field_profile``. Exact, since the p field
    has no y component and the s field only a y component (no interference term)."""
    rho = np.asarray(rho, complex)
    if rho.ndim == 1:
        rho = np.outer(rho, rho.conj())
    return rho[0, 0].real * field_profile(ns, ds, lam, theta0, z, "p") + \
        rho[1, 1].real * field_profile(ns, ds, lam, theta0, z, "s")


def power_factor(ns, theta0: float, pol: str) -> float:
    """T / |t|^2 of ``stack``: the ratio of the energy fluxes through the boundary carried by a transmitted and an
    incident wave of equal amplitudes, Re(n_out cos theta_out) / Re(n_in cos theta_in) for s and
    Re(n_out conj(cos theta_out)) / Re(n_in conj(cos theta_in)) for p (0 for an evanescent exit wave). Its square root
    is the factor eta of the transmitted beam's power-normalised Jones matrix (``core.optics.polarization``)."""
    ns = [complex(n) for n in ns]
    cos = _cosines(ns, theta0)
    n0, c0, nsub, cs = ns[0], cos[0], ns[-1], cos[-1]
    if pol == "s":
        return float((nsub * cs).real / (n0 * c0).real)
    if pol == "p":
        return float((nsub * cs.conjugate()).real / (n0 * c0.conjugate()).real)
    raise ValueError("pol must be 's' or 'p'")


def _g_series(delta):
    """(cos delta - sinc delta) / delta^2 = sum_{k>=1} (-1)^k 2k delta^(2k-2) / (2k+1)!, for |delta| < 0.5."""
    out, term_pow, fact = 0j, 1.0 + 0j, 6.0  # delta^(2k-2), (2k+1)!
    d2 = delta * delta
    for k in range(1, 12):
        out += (-1) ** k * 2 * k * term_pow / fact
        term_pow *= d2
        fact *= (2 * k + 2) * (2 * k + 3)
    return out


def _layer_d(n, dn, c, d, lam, pol, s0, ds0):
    """``_layer`` (the same matrix, the same float operations and the same scale e^s) and its derivative with respect
    to lam for an index n(lam) with dn = dn/dlam, s0 = n_in sin(theta0), ds0 = d s0/dlam. The scale e^s is held
    constant in the derivative: a real factor of the whole matrix, which no phase of r or t depends on. The entries
    are written through u = (n cos theta)^2 = n^2 - s0^2 and delta^2 = (k0 d)^2 u, with cos(delta), sinc(delta) and
    g = (cos delta - sinc delta)/delta^2 (even functions of delta), so a wave grazing inside the layer (u = 0) is a
    regular point: d cos(delta) = -sinc(delta) D/2, d sinc(delta) = g D/2, D = d(delta^2)/dlam."""
    Mt, s = _layer(n, c, d, lam, pol)
    delta = 2 * math.pi * n * c * d / lam
    k0 = 2 * math.pi / lam
    dk0 = -k0 / lam
    u = (n * c) ** 2
    du = 2 * (n * dn - s0 * ds0)
    D = d * d * (2 * k0 * dk0 * u + k0 * k0 * du)
    if s:
        ep, em = cmath.exp(1j * delta - s), cmath.exp(-1j * delta - s)
        cd, sd = 0.5 * (ep + em), (ep - em) / 2j
        sinc = sd / delta
        g = (cd - sinc) / (delta * delta)
    else:
        cd = cmath.cos(delta)
        sinc = _sinc(delta)
        g = _g_series(delta) if abs(delta) < 0.5 else (cd - sinc) / (delta * delta)
    dcd = -0.5 * sinc * D
    dsinc = 0.5 * g * D
    if pol == "s":
        dM01 = -1j * d * (dk0 * sinc + k0 * dsinc)
        dM10 = -1j * d * (dk0 * u * sinc + k0 * du * sinc + k0 * u * dsinc)
    else:
        n2, dn2 = n * n, 2 * n * dn
        dM01 = -1j * d * ((du / n2 - u * dn2 / (n2 * n2)) * k0 * sinc + (u / n2) * (dk0 * sinc + k0 * dsinc))
        dM10 = -1j * d * (dn2 * k0 * sinc + n2 * (dk0 * sinc + k0 * dsinc))
    return Mt, np.array([[dcd, dM01], [dM10, dcd]]), s


def group_delay(ns, ds, lam: float, theta0: float, pol: str, dns=None, length_unit: float = 1e-9,
                ng_ref: float = 1.0) -> dict:
    """The group delays of the reflected and the transmitted wave of a planar structure: tau = d(arg r)/d omega and
    d(arg t)/d omega at a fixed angle of incidence theta0 (time factor e^{-i omega t}: a positive tau is a delay of the
    pulse's peak; r refers to the first interface, t to the exit plane, both at the same position along the surface).
    ns, ds, lam, theta0 as in ``stack``; dns the derivatives dn/dlam of the indices in the unit of lam (each material's
    dispersion, e.g. ``core.optics.materials.dindex``, complex for an absorbing medium, the incidence medium's too;
    None: constant indices); length_unit the unit of lam and ds in metres (1e-9: nm).
    tau = -ng_ref length_unit lam^2/(2 pi c) d(arg)/dlam.

    The wavelength (review EX2, R2-E F6): omega = 2 pi c / lambda_vac. With lam in vacuum and absolute indices ng_ref
    = 1. Indices relative to a reference medium at the wavelength in it (SCHOTT's glasses: relative to air, lam in air;
    ``materials.info(...)["wavelength"] == "air"``) give the phases exactly (n_rel / lambda_ref = n_abs /
    lambda_vac), and then d lambda_ref / d omega = -(lambda_ref / omega) n_g,ref / n_ref, so tau carries the
    reference medium's group index n_g,ref = n_ref - lambda d n_ref / d lambda: pass it as ng_ref (dry air at 20 °C
    and 101.325 kPa by Ciddor's formula, Appl. Opt. 35, 1566 (1996): about 1 + 2.8e-4 at 700 nm to 1 + 2.9e-4 at
    450 nm; it depends on the air's temperature, pressure and humidity, which the caller states; 1, the default,
    leaves tau short by that fraction).

    The transfer matrices of ``stack`` differentiated exactly in lam (forward mode: the derivative of each layer's
    characteristic matrix with its index's dispersion, ``_layer_d``, carried through the product by the product rule;
    the incidence medium's dispersion through e0 = n0 cos theta0 and n0 sin theta0, the exit's through its cosine):
    d ln r = N'/N - D'/D with r = N/D as in ``stack``, d ln t = e0'/e0 - D'/D (s) or n0'/n0 - D'/D (p), and
    d(arg)/dlam = Im d ln. Real factors (the scales e^S of opaque layers, the normalisations of the running product)
    change |r| and |t|, not their phases, and drop out. A complex step is not used: r and t are complex-valued, and the
    complex-step derivative needs a real-valued function. Returns dict(tau_r, tau_t (s), dphi_r, dphi_t (rad per unit
    of lam), r, t (as ``stack``)); tau_r is nan where r = 0 (no reflected wave, no phase)."""
    from lfphys.core.constants import C as C_LIGHT
    ns = [complex(n) for n in ns]
    if len(ds) != len(ns) - 2:
        raise ValueError("need one thickness per inner layer")
    if pol not in ("s", "p"):
        raise ValueError("pol must be 's' or 'p'")
    dns = [0j] * len(ns) if dns is None else [complex(x) for x in dns]
    cos = _cosines(ns, theta0)
    sin0 = math.sin(theta0)
    s0, ds0 = _kx(ns, theta0), dns[0].real * sin0  # k_x / k0 = Re(n_in) sin theta0 and its derivative
    M = np.eye(2, dtype=complex)
    dM = np.zeros((2, 2), complex)
    S = 0.0
    for j in range(1, len(ns) - 1):
        Mj, dMj, sj = _layer_d(ns[j], dns[j], cos[j], ds[j - 1], lam, pol, s0, ds0)
        dM = dM @ Mj + M @ dMj
        M = M @ Mj
        S += sj
        m = max(float(np.max(np.abs(M))), float(np.max(np.abs(dM))))
        if m > 1e100 or 0 < m < 1e-100:  # a real factor of both: the phases' derivatives do not change
            M, dM = M / m, dM / m
            S += math.log(m)
    n0, c0, nsub, cs = ns[0], cos[0], ns[-1], cos[-1]
    dn0, dnsub = dns[0], dns[-1]
    qs = nsub * cs
    dqs = (nsub * dnsub - s0 * ds0) / qs if qs != 0 else complex(math.inf, math.inf)
    if pol == "s":
        v, dv = np.array([1.0, qs]), np.array([0.0, dqs])
    else:
        dcs = (dqs * nsub - qs * dnsub) / (nsub * nsub)
        v, dv = np.array([cs, nsub]), np.array([dcs, dnsub])
    B, Cc = M @ v
    dB, dC = dM @ v + M @ dv
    # the incidence medium: e0 = n0 cos theta0 = sqrt(n0^2 - s0^2), de0 = (n0 dn0 - s0 ds0) / e0; for a real n0 at a
    # fixed angle this is dn0 cos theta0 and cos theta0 itself does not change (dc0 = 0)
    e0 = n0 * c0
    if n0.imag == 0 and dn0.imag == 0:
        de0, dc0 = dn0 * c0, 0j
    else:
        de0 = (n0 * dn0 - s0 * ds0) / e0
        dc0 = (de0 - c0 * dn0) / n0
    if pol == "s":
        N, Dn = e0 * B - Cc, e0 * B + Cc
        dN, dD = de0 * B + e0 * dB - dC, de0 * B + e0 * dB + dC
        dlogt = de0 / e0 - dD / Dn
        t = 2 * e0 / Dn * math.exp(-S)
    else:
        N, Dn = -(n0 * B - c0 * Cc), n0 * B + c0 * Cc
        dN, dD = -(dn0 * B + n0 * dB - dc0 * Cc - c0 * dC), dn0 * B + n0 * dB + dc0 * Cc + c0 * dC
        dlogt = dn0 / n0 + (dc0 / c0 if dc0 != 0 else 0j) - dD / Dn
        t = 2 * n0 * c0 / Dn * math.exp(-S)
    dphi_r = (dN / N - dD / Dn).imag if N != 0 else math.nan
    dphi_t = complex(dlogt).imag
    if not (math.isfinite(ng_ref) and ng_ref > 0):
        raise ValueError("ng_ref must be a group index > 0")
    k = -ng_ref * length_unit * lam * lam / (2 * math.pi * C_LIGHT)
    return {"tau_r": k * dphi_r, "tau_t": k * dphi_t, "dphi_r": float(dphi_r), "dphi_t": float(dphi_t),
            "r": complex(N / Dn), "t": complex(t)}
