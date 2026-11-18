# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Polarisation of light through planar structures and polarising devices: the Jones and Stokes calculus, the
density matrix of a beam, the reflection and transmission matrices of a planar structure built from the engine's
transfer matrices (``core.optics.interfaces.stack``), polarisers and polarising beam splitters with principal
transmittances, and the Born probabilities of a single photon's outcomes.

Conventions (stated here and tested in ``tests/test_polarization.py``):

* Time factor e^{-i omega t} (as ``interfaces``): a field is E(t) = Re(J e^{-i omega t}).
* Basis of a beam: (p, s), s normal to the plane of incidence (the same unit vector y for every beam at a structure),
  p = s x k in the plane of incidence, so that (p, s, k) is right-handed for every beam (incident, reflected,
  transmitted). The Fresnel coefficients of ``interfaces`` (Born & Wolf's sign for p) are ratios of these components:
  Born & Wolf's p vector is -p for every beam, which leaves every ratio unchanged. At normal incidence r_p = -r_s:
  the reflected beam's own p axis points the other way in the laboratory (its frame is right-handed about its own k),
  so a reflected linear polarisation at psi from p is seen at -psi in the reflected beam's frame.
* A Jones vector J = (E_p, E_s); a beam's state is its 2 x 2 polarisation density (coherency) matrix rho = <J J^dagger>
  in its own (p, s) basis, tr rho its intensity (one photon: tr rho = 1, rho the photon's polarisation state). Linear
  polarisation at psi from p towards s: J = (cos psi, sin psi); unpolarised light rho = (I/2) tr rho, nothing else
  assumed.
* Stokes parameters (Shurcliff 1962, ch. 2: I, M, C, S = <a_p^2 + a_s^2>, <a_p^2 - a_s^2>, <2 a_p a_s cos gamma>,
  <2 a_p a_s sin gamma> for the oscillations E_j = a_j cos(omega t + e_j), gamma = e_s - e_p):
  S0 = rho_pp + rho_ss, S1 = rho_pp - rho_ss, S2 = 2 Re rho_ps, S3 = 2 Im rho_ps with rho_ps = <E_p E_s^*>. S3 > 0
  is right-handed light: the field turns clockwise for an observer facing the oncoming
  beam (Shurcliff's convention; J = (1, -i)/sqrt 2 is right-circular, as in ``core.quantum.marks``). Degree of
  polarisation sqrt(S1^2 + S2^2 + S3^2) / S0; the ellipse of the polarised part: azimuth (1/2) atan2(S2, S1) from p
  towards s, ellipticity angle chi = (1/2) asin(S3 / sqrt(S1^2 + S2^2 + S3^2)), axis ratio |tan chi|.
* Mueller matrix of a Jones matrix J: M = A (J (x) J^*) A^-1 with S = A vec(rho), vec(rho) = (rho_pp, rho_ps,
  rho_sp, rho_ss); the Stokes vector of J rho J^dagger is M S.
* Rotations (Shurcliff 1962, §8.7, p. 120): R(theta) = [[cos, sin], [-sin, cos]]; an element whose principal axis is
  at theta from p has the matrix R(-theta) M0 R(theta).
* A polariser (dichroic, no retardance) with its transmission axis at alpha from p and principal transmittances
  k1 (along the axis) and k2 (across it), 0 <= k2 <= k1 <= 1 (Shurcliff 1962, ch. 3, pp. 35-36; ideal k1 = 1, k2 = 0):
  P = R(-alpha) diag(sqrt k1, sqrt k2) R(alpha). For linear light at psi it passes k1 cos^2(alpha - psi) +
  k2 sin^2(alpha - psi) of the intensity (Malus's law; generalised by Ratajczyk 1979, eq. (7)). A polarising beam
  splitter has a pass port with that operator and a reject port with R(-alpha) diag(sqrt(1 - k1), sqrt(1 - k2))
  R(alpha), so that the two ports' probabilities add to the incoming one (a lossless splitter; a POVM).
* A planar structure (``interfaces.stack``: indices ns, thicknesses ds): reflection M_R = diag(r_p, r_s), transmission
  M_T = diag(eta_p t_p, eta_s t_s) with eta^2 = ``interfaces.power_factor`` = T / |t|^2, each from the incident
  beam's (p, s) to the outgoing beam's (p, s). Then rho_R = M_R rho M_R^dagger, rho_T = M_T rho M_T^dagger, their
  traces R_p rho_pp + R_s rho_ss and T_p rho_pp + T_s rho_ss (exactly: s and p carry no cross term of the flux through
  an isotropic boundary), and the absorbed A_p rho_pp + A_s rho_ss (0 for real indices). With a lossless exit medium
  eta_p = eta_s and rho_T is the transmitted field's own state.
* Total internal reflection: |r_s| = |r_p| = 1 and the phase of p is advanced relative to s by
  delta = arg r_s - arg r_p (arguments in the e^{-i omega t} convention; Stratton's delta = delta_par - delta_perp with
  r = e^{-i delta}), tan(delta/2) = cos theta sqrt(sin^2 theta - n^2) / sin^2 theta, n = n_out/n_in < 1, largest at
  sin^2 theta = 2 n^2/(1 + n^2) where tan(delta_max/2) = (1 - n^2)/(2n) (Stratton 1941, §9.7, eqs. (43)-(47)). Linear
  light at 45 degrees comes back elliptical with S3 = -sin delta (left-handed).
* The photon's outcomes (Born rule on its density matrix): reflected and passed / rejected by the analyser of the
  reflection arm, transmitted and passed / rejected by the analyser of the transmission arm, absorbed in the
  structure; probabilities tr(E rho_R), tr((I - E) rho_R), ..., P_A, E = A^dagger A the analyser's pass element. An
  arm without an analyser has one detector: its whole probability is that arm's "pass" outcome and "reject" is 0.

Validity: plane monochromatic waves; homogeneous isotropic planar structures (no s <-> p mixing) of linear media; the
analysers are linear partial polarisers without retardance, defined by k1 and k2 (their dependence on the angle of
incidence and on the wavelength not modelled). The degree of polarisation is that of the beam's 2 x 2 matrix.
"""

from __future__ import annotations

import cmath
import math

import numpy as np

from lfphys.core.optics import interfaces
from lfphys.core.quantum.qubits import born_probabilities
from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Polarisation of light: the Jones and Stokes calculus, analysers, reflection and transmission"),
    "statement": T("Jones vectors and matrices, density matrices, Stokes parameters and Mueller matrices, rotations; "
                   "a polariser and a polarising beam splitter with the principal transmittances k₁ and k₂ (Malus's "
                   "law I = k₁ cos²(α − ψ) + k₂ sin²(α − ψ)); the reflection and transmission matrices of a planar "
                   "structure from its Fresnel coefficients (light comes back elliptical from total internal "
                   "reflection, with the phase difference δ); the degree of polarisation and the polarisation "
                   "ellipse; the Born probabilities of a photon's outcomes at the structure and the analysers."),
    "validity": T("plane monochromatic waves; isotropic planar structures (no s ↔ p mixing); linear media; an "
                  "analyser is a linear partial polariser without retardance, given by k₁ and k₂ independent of the "
                  "angle of incidence and of the wavelength"),
    "basis": ["Stratton, Electromagnetic Theory (McGraw-Hill, 1941), §9.6–9.7, eqs. (33), (41)–(47)",
              "Shurcliff, Polarized Light: Production and Use (Harvard University Press, 1962), ch. 2, 3, 8",
              "Ratajczyk, Optica Applicata 9, 281 (1979)",
              T("the Fresnel coefficients and transfer matrices of lfphys.core.optics.interfaces (Born & Wolf, "
                "Principles of Optics, §1.5–1.6)")],
    "conflicts": [],
}

OUTCOMES = ("R_pass", "R_reject", "T_pass", "T_reject", "A")
I2 = np.eye(2, dtype=complex)
EPS = np.finfo(float).eps


# --- states ------------------------------------------------------------------------------------------------------
def jones_linear(psi: float) -> np.ndarray:
    """Linear polarisation at psi (rad) from p towards s: (cos psi, sin psi). s light is psi = pi/2, p light psi = 0."""
    return np.array([math.cos(psi), math.sin(psi)], complex)


def jones_ellipse(azimuth: float, chi: float) -> np.ndarray:
    """Unit Jones vector of the ellipse with its major axis at ``azimuth`` from p and ellipticity angle chi
    (|tan chi| = minor/major; chi > 0 right-handed, S3 = sin 2chi): R(-azimuth) (cos chi, -i sin chi)."""
    return rotation(-azimuth) @ np.array([math.cos(chi), -1j * math.sin(chi)], complex)


def density(state) -> np.ndarray:
    """The density matrix of a state: J J^dagger for a Jones vector, a checked copy of a 2 x 2 matrix (Hermitian with
    non-negative eigenvalues within round-off, else ValueError)."""
    a = np.asarray(state, complex)
    if a.shape == (2,):
        return np.outer(a, a.conj())
    if a.shape != (2, 2):
        raise ValueError(T("polarisation state: a Jones vector (2) or a density matrix (2 × 2) is needed"))
    scale = max(float(np.max(np.abs(a))), 1e-300)
    w = np.linalg.eigvalsh(0.5 * (a + a.conj().T))
    if float(np.max(np.abs(a - a.conj().T))) > 16 * EPS * scale or float(w[0]) < -16 * EPS * scale:
        raise ValueError(T("polarisation state: not a density matrix (it must be Hermitian with non-negative "
                           "eigenvalues)"))
    return a.copy()


def unpolarised(intensity: float = 1.0) -> np.ndarray:
    """Unpolarised light (or an unpolarised photon): rho = (intensity/2) I."""
    return 0.5 * float(intensity) * I2.copy()


# --- rotations and devices ---------------------------------------------------------------------------------------
def rotation(theta: float) -> np.ndarray:
    """Shurcliff's rotator S(theta) = [[cos, sin], [-sin, cos]]: the components in a frame turned by theta from p
    towards s."""
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, s], [-s, c]], complex)


def rotated(M0, theta: float) -> np.ndarray:
    """The Jones matrix of an element whose principal axes are turned by theta from (p, s): R(-theta) M0 R(theta)."""
    return rotation(-theta) @ np.asarray(M0, complex) @ rotation(theta)


def _check_k(k1: float, k2: float) -> tuple[float, float]:
    k1, k2 = float(k1), float(k2)
    if not (0.0 <= k2 <= k1 <= 1.0):
        raise ValueError(T("analyser: the principal transmittances must satisfy 0 ≤ k₂ ≤ k₁ ≤ 1 (k₁ = {k1}, "
                           "k₂ = {k2})", k1=k1, k2=k2))
    return k1, k2


def polariser(alpha: float, k1: float = 1.0, k2: float = 0.0) -> np.ndarray:
    """Jones matrix of a linear (partial) polariser, transmission axis at alpha from p, principal transmittances k1
    and k2 (intensity; amplitude transmittances sqrt k1, sqrt k2): R(-alpha) diag(sqrt k1, sqrt k2) R(alpha)."""
    k1, k2 = _check_k(k1, k2)
    return rotated(np.diag([math.sqrt(k1), math.sqrt(k2)]).astype(complex), alpha)


def beam_splitter(alpha: float, k1: float = 1.0, k2: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """The two ports of a lossless polarising beam splitter with its pass axis at alpha from p: (A_pass, A_reject)
    with A_pass = ``polariser(alpha, k1, k2)`` and A_reject = R(-alpha) diag(sqrt(1 - k1), sqrt(1 - k2)) R(alpha);
    A_pass^dagger A_pass + A_reject^dagger A_reject = I. The reject port's operator is given in the incoming beam's
    frame (its own direction and geometry are the device's)."""
    k1, k2 = _check_k(k1, k2)
    return (rotated(np.diag([math.sqrt(k1), math.sqrt(k2)]).astype(complex), alpha),
            rotated(np.diag([math.sqrt(1.0 - k1), math.sqrt(1.0 - k2)]).astype(complex), alpha))


def malus(psi: float, alpha: float, k1: float = 1.0, k2: float = 0.0) -> float:
    """Closed form: the fraction of linear light at psi that passes an analyser at alpha with principal
    transmittances k1, k2: k1 cos^2(alpha - psi) + k2 sin^2(alpha - psi) (cos^2 for an ideal one)."""
    k1, k2 = _check_k(k1, k2)
    d = alpha - psi
    return k1 * math.cos(d) ** 2 + k2 * math.sin(d) ** 2


def analyse(state, ports) -> tuple[np.ndarray, np.ndarray, float, float]:
    """A state through the two ports (A_pass, A_reject) of ``beam_splitter``: (rho_pass, rho_reject, P_pass,
    P_reject), rho_x = A_x rho A_x^dagger, P_x = tr rho_x."""
    rho = density(state)
    a, b = ports
    rp, rr = a @ rho @ a.conj().T, b @ rho @ b.conj().T
    return rp, rr, float(np.trace(rp).real), float(np.trace(rr).real)


# --- Stokes parameters and Mueller matrices ----------------------------------------------------------------------
_A = np.array([[1, 0, 0, 1], [1, 0, 0, -1], [0, 1, 1, 0], [0, -1j, 1j, 0]], complex)
_A_INV = np.linalg.inv(_A)


def stokes(state) -> np.ndarray:
    """(S0, S1, S2, S3) of a Jones vector or density matrix (the conventions of the module docstring)."""
    rho = density(state)
    return np.array([(rho[0, 0] + rho[1, 1]).real, (rho[0, 0] - rho[1, 1]).real, 2 * rho[0, 1].real,
                     2 * rho[0, 1].imag])


def density_from_stokes(S) -> np.ndarray:
    """The density matrix with Stokes vector S: rho = (1/2)[[S0 + S1, S2 + i S3], [S2 - i S3, S0 - S1]]."""
    S0, S1, S2, S3 = (float(x) for x in S)
    return 0.5 * np.array([[S0 + S1, S2 + 1j * S3], [S2 - 1j * S3, S0 - S1]], complex)


def mueller(J) -> np.ndarray:
    """The 4 x 4 Mueller matrix of a Jones matrix: A (J (x) J^*) A^-1 (real)."""
    J = np.asarray(J, complex)
    return (_A @ np.kron(J, J.conj()) @ _A_INV).real


def mueller_rotation(theta: float) -> np.ndarray:
    """Shurcliff's Mueller rotator T(2 theta) = [[1, 0, 0, 0], [0, c, s, 0], [0, -s, c, 0], [0, 0, 0, 1]],
    c = cos 2theta, s = sin 2theta: an element at theta has the Mueller matrix T(-2 theta) M0 T(2 theta)."""
    c, s = math.cos(2 * theta), math.sin(2 * theta)
    return np.array([[1, 0, 0, 0], [0, c, s, 0], [0, -s, c, 0], [0, 0, 0, 1]], float)


def degree_of_polarisation(state) -> float:
    """sqrt(S1^2 + S2^2 + S3^2) / S0 (nan for S0 = 0)."""
    S = stokes(state)
    return float(math.sqrt(S[1] ** 2 + S[2] ** 2 + S[3] ** 2) / S[0]) if S[0] > 0 else math.nan


def degree_from_powers(Ps: float, Pp: float) -> float:
    """Closed form: the degree of polarisation of the light an isotropic structure reflects (or transmits) from
    unpolarised light, |R_s - R_p| / (R_s + R_p) (with T_s, T_p for the transmitted light)."""
    return abs(Ps - Pp) / (Ps + Pp)


def ellipse(state) -> dict:
    """The polarisation ellipse of the polarised part of a state: dict(azimuth (rad, from p towards s, in
    (-pi/2, pi/2]), chi (ellipticity angle, [-pi/4, pi/4], > 0 right-handed), axis_ratio = |tan chi|,
    handedness (+1 right, -1 left, 0 linear), degree (of polarisation), major and minor (the semi-axes of the
    polarised part's field, peak values of Re(J e^{-i omega t}) with |J|^2 the polarised intensity), intensity (S0)).
    Unpolarised light (degree 0): azimuth and chi are nan."""
    S0, S1, S2, S3 = (float(x) for x in stokes(state))
    Ip = math.sqrt(S1 * S1 + S2 * S2 + S3 * S3)
    if Ip == 0.0:
        return {"azimuth": math.nan, "chi": math.nan, "axis_ratio": math.nan, "handedness": 0, "degree": 0.0,
                "major": 0.0, "minor": 0.0, "intensity": S0}
    chi = 0.5 * math.asin(max(-1.0, min(1.0, S3 / Ip)))
    az = 0.5 * math.atan2(S2, S1)
    if az <= -math.pi / 2:
        az += math.pi
    hand = 0 if S3 == 0 else (1 if S3 > 0 else -1)
    return {"azimuth": az, "chi": chi, "axis_ratio": abs(math.tan(chi)), "handedness": hand,
            "degree": Ip / S0 if S0 > 0 else math.nan, "major": math.sqrt(Ip) * math.cos(chi),
            "minor": math.sqrt(Ip) * abs(math.sin(chi)), "intensity": S0}


# --- a planar structure ------------------------------------------------------------------------------------------
def boundary_matrices(ns, ds, lam: float, theta0: float) -> dict:
    """The reflection and transmission Jones matrices of a planar structure (``interfaces.stack``: ns = [n_in, n_1,
    ..., n_out], ds the thicknesses in the unit of lam, theta0 the angle of incidence in the lossless medium n_in):
    dict(M_R = diag(r_p, r_s), M_T = diag(eta_p t_p, eta_s t_s), r_p, r_s, t_p, t_s, R_p, R_s, T_p, T_s, A_p, A_s,
    eta_p, eta_s, lossless). M_R maps the incident (p, s) to the reflected beam's (p, s), M_T to the transmitted
    beam's; eta^2 = ``interfaces.power_factor`` (T = eta^2 |t|^2). ``lossless``: every index real (then A_p = A_s = 0
    exactly; the transfer matrices give R + T = 1 to round-off)."""
    ns = [complex(n) for n in ns]
    ds = [float(d) for d in ds]
    sp = interfaces.stack(ns, ds, lam, theta0, "p")
    ss = interfaces.stack(ns, ds, lam, theta0, "s")
    eta_p = math.sqrt(max(interfaces.power_factor(ns, theta0, "p"), 0.0))
    eta_s = math.sqrt(max(interfaces.power_factor(ns, theta0, "s"), 0.0))
    lossless = all(n.imag == 0 for n in ns)
    return {"M_R": np.diag([sp["r"], ss["r"]]).astype(complex),
            "M_T": np.diag([eta_p * sp["t"], eta_s * ss["t"]]).astype(complex),
            "r_p": sp["r"], "r_s": ss["r"], "t_p": sp["t"], "t_s": ss["t"],
            "R_p": sp["R"], "R_s": ss["R"], "T_p": sp["T"], "T_s": ss["T"],
            "A_p": 0.0 if lossless else sp["A"], "A_s": 0.0 if lossless else ss["A"],
            "eta_p": eta_p, "eta_s": eta_s, "lossless": lossless}


def through(state, bm: dict) -> dict:
    """The incident state through the structure ``bm`` (``boundary_matrices``): dict(rho_R, rho_T, P_R, P_T, P_A)
    with rho_X = M_X rho M_X^dagger in the outgoing beam's (p, s), P_R = tr rho_R, P_T = tr rho_T and the absorbed
    P_A = A_p rho_pp + A_s rho_ss."""
    rho = density(state)
    MR, MT = bm["M_R"], bm["M_T"]
    rR, rT = MR @ rho @ MR.conj().T, MT @ rho @ MT.conj().T
    PA = bm["A_p"] * rho[0, 0].real + bm["A_s"] * rho[1, 1].real
    return {"rho_R": rR, "rho_T": rT, "P_R": float(np.trace(rR).real), "P_T": float(np.trace(rT).real),
            "P_A": float(PA)}


def _arm(rho: np.ndarray, ports) -> tuple[float, float]:
    if ports is None:
        return float(np.trace(rho).real), 0.0
    a, b = ports
    Ea, Eb = a.conj().T @ a, b.conj().T @ b
    return float(np.trace(Ea @ rho).real), float(np.trace(Eb @ rho).real)


def outcome_probabilities(state, bm: dict, analyser_R=None, analyser_T=None) -> dict:
    """The Born probabilities of a photon (or the fractions of a beam) with polarisation state ``state`` at the
    structure ``bm`` with an analyser (the ports of ``beam_splitter``, or None for one plain detector) in each arm:
    dict over ``OUTCOMES`` (R_pass, R_reject, T_pass, T_reject, A), plus P_R, P_T, P_A (the arms' totals). Round-off
    below zero is set to 0 by ``qubits.born_probabilities``; the five add to tr rho to round-off."""
    out = through(state, bm)
    rp, rr = _arm(out["rho_R"], analyser_R)
    tp, tr = _arm(out["rho_T"], analyser_T)
    p = born_probabilities([rp, rr, tp, tr, out["P_A"]], dim=2)
    res = {k: float(v) for k, v in zip(OUTCOMES, p)}
    res.update(P_R=out["P_R"], P_T=out["P_T"], P_A=out["P_A"])
    return res


def sample_photons(probs: dict, n: int, rng) -> np.ndarray:
    """n photons' outcomes (indices into ``OUTCOMES``) drawn independently from the Born probabilities ``probs`` (the
    dict of ``outcome_probabilities``; renormalised against the round-off of their sum)."""
    p = np.array([probs[k] for k in OUTCOMES], float)
    return rng.choice(len(OUTCOMES), size=int(n), p=p / p.sum())


# --- total internal reflection ------------------------------------------------------------------------------------
def tir_phase_difference(n_in: float, n_out: float, theta: float) -> float:
    """The phase advance of p relative to s on reflection at one boundary, delta = arg r_s - arg r_p in (-pi, pi]
    (e^{-i omega t}), from the engine's coefficients (``interfaces.stack``). Beyond the critical angle |r_s| = |r_p|
    = 1 and delta = ``tir_phase_closed_form``; below it the coefficients are real and delta is 0 or pi."""
    rs = interfaces.stack([n_in, n_out], [], 1.0, theta, "s")["r"]
    rp = interfaces.stack([n_in, n_out], [], 1.0, theta, "p")["r"]
    return cmath.phase(rs * rp.conjugate())


def tir_phase_closed_form(n: float, theta: float) -> float:
    """Closed form beyond the critical angle (Stratton 1941, §9.7, eq. (45)), n = n_out/n_in < 1:
    delta = 2 atan(cos theta sqrt(sin^2 theta - n^2) / sin^2 theta)."""
    s2 = math.sin(theta) ** 2
    return 2.0 * math.atan(math.cos(theta) * math.sqrt(s2 - n * n) / s2)


def tir_phase_maximum(n: float) -> tuple[float, float]:
    """(theta_max, delta_max) of total internal reflection for n = n_out/n_in < 1 (Stratton 1941, eqs. (46), (47)):
    sin^2 theta_max = 2 n^2/(1 + n^2), tan(delta_max/2) = (1 - n^2)/(2 n)."""
    return math.asin(math.sqrt(2 * n * n / (1 + n * n))), 2.0 * math.atan((1 - n * n) / (2 * n))
