# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Internal states, elements at the slits, the which-path detector and the analyzer: the "marks" a particle
carries away from each slit.

The state just behind slit j is  A_j(x) |m_j>  with the spatial amplitude A_j (fresnel.py) and the mark
    |m_j> = (P_a J_j chi) (x) |d_j>,
* chi: the particle's internal state (photon: Jones vector in the basis H = x (across the slits), V = y
  (along the slits); spin 1/2: spinor in the basis up/down along the beam axis z; no internal state: [1]);
* J_j: the element at slit j (polarizer, wave plate, spin rotator, spin filter, phase, blocker);
* P_a: the analyzer before the screen (polarizer / spin filter) or the identity;
* |d_j>: the which-path detector (a qubit, Englert's model): it starts in |0> and is rotated by the angle theta
  when the particle passes the coupled slit, |d_j> = cos(theta_j)|0> + sin(theta_j)|1>.

Born rule on the screen (detector read in the basis {b_r} or not read at all):
    P(x, r) = sum_s | sum_j A_j(x) <s, b_r | m_j> |^2 = sum_jl A_j A_l^* G^{(r)}_{jl},
    G^{(r)}_{jl} = <w^{(r)}_l | w^{(r)}_j>,   w^{(r)}_j = (P_a J_j chi) <b_r | d_j>.
Not reading the detector = summing over r (the screen marginal does not depend on the readout basis:
no-signalling, checked in the run). Interference between slits j and l survives only through G_jl: it is
computed from the marks, never switched off by a rule.

Conventions: time dependence exp(i(kz - wt)) (the Fresnel kernel exp(+ik(x-x')^2/2z) and the outgoing H^(1));
wave plates: the angle is the fast axis, symmetric retardance exp(-+ i Gamma/2) on the axes (no overall phase);
circular states R = (1, -i)/sqrt 2 (right-handed in the usual optics convention, S3 = +1), L = (1, i)/sqrt 2; the
custom state R(psi)(cos chi, -i sin chi) has S3 = sin 2chi; spin rotation about y by angle a: exp(-i a sigma_y / 2);
spin filter along n = (sin t, 0, cos t): (1 + n.sigma)/2.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": 'core', "kind": 'law',
    "title": T("Which-path marks: internal states, elements, a qubit detector, the Born rule"),
    "statement": T("The state behind slit j is A_j(x)|m_j⟩; P(x, r) = Σ A_j A_l* G⁽ʳ⁾_jl, G the Gram matrix of the "
                   "marks; Jones and spin matrices, Englert's detector, the readout basis, the duality V² + D² ≤ 1."),
    "validity": T("quantum mechanics (the Born rule); polarization in the paraxial approximation, the same for both "
                  "components"),
    "basis": ['Englert, PRL 77, 2154 (1996)', 'Scully, Englert, Walther, Nature 351, 111 (1991)'],
    "conflicts": [],
}

SQ2 = math.sqrt(2.0)
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)

POL_STATES = {"H": [1, 0], "V": [0, 1], "D": [1 / SQ2, 1 / SQ2], "A": [1 / SQ2, -1 / SQ2],
              "R": [1 / SQ2, -1j / SQ2], "L": [1 / SQ2, 1j / SQ2]}
SPIN_STATES = {"up_z": [1, 0], "down_z": [0, 1], "up_x": [1 / SQ2, 1 / SQ2], "down_x": [1 / SQ2, -1 / SQ2],
               "up_y": [1 / SQ2, 1j / SQ2], "down_y": [1 / SQ2, -1j / SQ2]}

PHOTON_ELEMENTS = [("none", T("no element")), ("polarizer", T("polarizer (axis angle)")),
                   ("hwp", T("half-wave plate")), ("qwp", T("quarter-wave plate")),
                   ("phase", T("phase plate (phase)")), ("block", T("shutter (slit closed)"))]
SPIN_ELEMENTS = [("none", T("no element")), ("rot_y", T("spin rotation about y (angle)")),
                 ("filter", T("spin filter (direction)")), ("phase", T("phase shift (phase)")),
                 ("block", T("shutter (slit closed)"))]
SCALAR_ELEMENTS = [("none", T("no element")), ("phase", T("phase shift (phase)")), ("block", T("shutter (slit closed)"))]


def _rot(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s], [s, c]], complex)


def element_matrix(kind: str, angle_deg: float, internal: str | None) -> np.ndarray:
    a = math.radians(angle_deg)
    d = 1 if internal is None else 2
    if kind == "none":
        return np.eye(d, dtype=complex)
    if kind == "block":
        return np.zeros((d, d), complex)
    if kind == "phase":
        return np.exp(1j * a) * np.eye(d, dtype=complex)
    if internal == "pol":
        if kind == "polarizer":
            v = np.array([math.cos(a), math.sin(a)], complex)
            return np.outer(v, v.conj())
        if kind in ("hwp", "qwp"):
            g = math.pi if kind == "hwp" else math.pi / 2
            return _rot(a) @ np.diag([np.exp(-1j * g / 2), np.exp(1j * g / 2)]) @ _rot(-a)
    if internal == "spin":
        if kind == "rot_y":
            return math.cos(a / 2) * np.eye(2) - 1j * math.sin(a / 2) * SY
        if kind == "filter":
            n = (math.sin(a), 0.0, math.cos(a))
            return 0.5 * (np.eye(2) + n[0] * SX + n[1] * SY + n[2] * SZ)
    raise ValueError(T("element {kind} does not suit this particle", kind=repr(kind)))


def analyzer_matrix(kind: str, angle_deg: float, internal: str | None) -> np.ndarray:
    if kind == "none" or internal is None:
        return np.eye(1 if internal is None else 2, dtype=complex)
    return element_matrix("polarizer" if internal == "pol" else "filter", angle_deg, internal)


def bloch_state(theta: float, phi: float) -> np.ndarray:
    """Pure qubit state with Bloch / Poincare angles."""
    return np.array([math.cos(theta / 2), np.exp(1j * phi) * math.sin(theta / 2)], complex)


def sample_internal(rng, internal: str | None, state: str, degree: float, custom=None) -> np.ndarray:
    """A pure internal state drawn so that the ensemble has the density matrix
    rho = P |psi><psi| + (1 - P) I/2  (P = degree of polarization)."""
    if internal is None:
        return np.ones(1, complex)
    if state == "unpol" or rng.random() >= degree:
        # Haar-random pure state (uniform on the Bloch / Poincare sphere)
        z = rng.normal(size=2) + 1j * rng.normal(size=2)
        return z / np.linalg.norm(z)
    table = POL_STATES if internal == "pol" else SPIN_STATES
    if state == "custom":
        psi_deg, chi_deg = custom or (0.0, 0.0)
        # azimuth psi (major axis from x) and ellipticity chi: Jones vector R(psi) (cos chi, -i sin chi), so that
        # chi = +45 deg is R = (1, -i)/sqrt 2 of this module (review R19)
        p, c = math.radians(psi_deg), math.radians(chi_deg)
        return _rot(p) @ np.array([math.cos(c), -1j * math.sin(c)], complex)
    return np.array(table[state], complex)


def detector_states(n_slits: int, coupled: int, theta_deg: float, on: bool) -> list[np.ndarray]:
    if not on:
        return [np.ones(1, complex)] * n_slits
    t = math.radians(theta_deg)
    out = []
    for j in range(n_slits):
        out.append(np.array([math.cos(t), math.sin(t)], complex) if j == coupled else np.array([1.0, 0.0], complex))
    return out


def readout_basis(angle_deg: float) -> list[np.ndarray]:
    b = math.radians(angle_deg)
    return [np.array([math.cos(b), math.sin(b)], complex), np.array([-math.sin(b), math.cos(b)], complex)]


def marks(chi, J: list, Pa, dets: list, ab_phases=None, weights=None) -> list[np.ndarray]:
    """Full mark vectors |m_j> (internal (x) detector), with optional per-slit phases (Aharonov-Bohm) and
    complex weights (collapse-model hits)."""
    out = []
    for j, Jj in enumerate(J):
        v = Pa @ (Jj @ chi)
        if ab_phases is not None:
            v = v * np.exp(1j * ab_phases[j])
        if weights is not None:
            v = v * weights[j]
        out.append(np.kron(v, dets[j]))
    return out


def gram_by_readout(m: list, d_int: int, read_basis: list | None) -> list[np.ndarray]:
    """G^{(r)} for each readout outcome r (one matrix if the detector is not read or absent)."""
    n = len(m)
    M = np.stack(m)  # (n, d_int * d_det)
    d_det = M.shape[1] // d_int
    if read_basis is None or d_det == 1:
        return [M @ M.conj().T]
    out = []
    Mr = M.reshape(n, d_int, d_det)
    for b in read_basis:
        W = Mr @ b.conj()  # (n, d_int): w_j^{(r)} = (internal part) <b_r|d_j>
        out.append(W @ W.conj().T)
    return out


def englert(m_a: np.ndarray, m_b: np.ndarray) -> tuple[float, float]:
    """Predicted fringe visibility V and path distinguishability D for two paths with (unnormalised) marks.
    D = trace norm of (w_a rho_a - w_b rho_b) (Englert 1996), V = 2 |<m_b|m_a>| / (|m_a|^2 + |m_b|^2)."""
    na, nb = float(np.vdot(m_a, m_a).real), float(np.vdot(m_b, m_b).real)
    if na + nb == 0:
        return 0.0, 0.0
    V = 2 * abs(np.vdot(m_b, m_a)) / (na + nb)
    R = (np.outer(m_a, m_a.conj()) - np.outer(m_b, m_b.conj())) / (na + nb)
    D = float(np.sum(np.abs(np.linalg.eigvalsh(R))))
    return float(V), D
