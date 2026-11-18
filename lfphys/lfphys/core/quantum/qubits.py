# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Two-level systems and their composites: states, density matrices, measurement (Born rule), entanglement, spin
precession and the correlations of entangled pairs.

* Pauli matrices; a spin component along unit n: S_n = (hbar/2) n.sigma;
* projective measurement: P(k) = Tr(Pi_k rho) and the conditional state Pi_k rho Pi_k / P(k) (Lueders): the state
  to use for later predictions given the outcome, interpretation-neutral (Copenhagen reads it as a physical
  collapse, Everett as the relative state of the branch, Bohm as the effective wave function; review
  2026-10-23, E11); an exactly
  zero probability (an eigenstate, a perfectly (anti)correlated pair) comes out of the float trace as +-1e-17, so the
  probabilities pass through ``born_probabilities`` (round-off below zero -> 0) before they are used or sampled;
* partial trace, von Neumann entropy, concurrence (Wootters 1998);
* Larmor precession: U(t) = exp(-i omega t (n.sigma)/2);
* singlet |psi-> = (|01> - |10>)/sqrt 2: E(a, b) = <(a.sigma)(b.sigma)> = -a.b; CHSH
  S = E(a,b) - E(a,b') + E(a',b) + E(a',b') with |S| <= 2 sqrt 2 (Tsirelson) and 2 sqrt 2 at the optimal angles;
* polarization-entangled photons |Phi+> = (|HH> + |VV>)/sqrt 2: E(alpha, beta) = cos 2(alpha - beta);
* real stations (EX2 §4.7): an analyser followed by threshold detectors as a POVM. With one detector behind the
  transmitted port (projector Pi), efficiency eta and a dark-click probability p_d in the trial, the effects are
  E_0 = (1 - p_d)(I - eta Pi) (no click) and E_+ = I - E_0 (Giustina et al. 2015, eq. (1): "+" a detection, "0"
  none). With two detectors behind the ports Pi_+ and Pi_- (one photon goes to one port; each detector clicks if it
  detects the photon or has a dark click, independently), the four outcomes "+" only, "-" only, none and both have
  E_+ = [1 - (1 - eta_+)(1 - p_+)](1 - p_-) Pi_+ + p_+ (1 - eta_-)(1 - p_-) Pi_-,
  E_- = (1 - eta_+)(1 - p_+) p_- Pi_+ + (1 - p_+)[1 - (1 - eta_-)(1 - p_-)] Pi_-,
  E_0 = (1 - p_+)(1 - p_-)[(1 - eta_+) Pi_+ + (1 - eta_-) Pi_-],
  E_+- = [1 - (1 - eta_+)(1 - p_+)] p_- Pi_+ + p_+ [1 - (1 - eta_-)(1 - p_-)] Pi_-;
  eta = 1, p_d = 0 gives back the projectors (and E_+- = 0). ``joint_probabilities`` takes any effects;
* the states of real sources: Eberhard's states (|V>_A |H>_B + r |H>_A |V>_B) / sqrt(1 + r^2) (Eberhard 1993;
  Giustina et al. 2015, eq. (2); r = -1 is the singlet, r -> 0 a product state) and Werner mixtures
  V |psi><psi| + (1 - V) I/4 (a source of visibility V: every correlation <A (x) B> of traceless observables scaled by
  V, so S = V 2 sqrt 2 at the CHSH angles).

Bases: a qubit (H, V) = (|0>, |1>); a pair kron(A, B), i.e. |HH>, |HV>, |VH>, |VV>; a polariser at angle theta from H
transmits cos theta |H> + sin theta |V> (``polarizer_projectors``).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import linalg

from lfphys.i18n import T
from lfphys.codes import coded

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("Qubits and spin ½: states, measurement, entanglement, Bell correlations"),
    "statement": T("Density matrices, the Born rule and the Lüders projection, the partial trace, entropy, "
                   "concurrence, Larmor precession; the singlet correlations E(a,b) = −a·b and the CHSH parameter up "
                   "to 2√2; a station with an analyser and one or two threshold detectors (efficiency η, dark-click "
                   "probability) as a POVM; Eberhard's states (|VH⟩ + r|HV⟩)/√(1 + r²) and Werner mixtures."),
    "validity": T("quantum mechanics of finite-dimensional systems"),
    "basis": ["Bell, Physics 1, 195 (1964)", "Clauser, Horne, Shimony, Holt, PRL 23, 880 (1969)",
              "Tsirelson, Lett. Math. Phys. 4, 93 (1980)", "Wootters, PRL 80, 2245 (1998)",
              T("loophole-free experiments: Hensen et al. 2015; Giustina et al. 2015; Shalm et al. 2015"),
              T("stations with threshold detectors as POVMs; the states of real sources: Eberhard, Phys. Rev. A 47, "
                "R747 (1993) (preprint LBL-32696 read); Giustina et al., PRL 115, 250401 (2015), eqs. (1)–(2)")],
    "conflicts": [],
}

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
SIGMA = np.stack([SX, SY, SZ])


def n_sigma(n) -> np.ndarray:
    n = np.asarray(n, float)
    return np.einsum("i,ijk->jk", n / np.linalg.norm(n), SIGMA)


def ket(*amps) -> np.ndarray:
    v = np.asarray(amps, complex)
    return v / np.linalg.norm(v)


def dm(psi) -> np.ndarray:
    psi = np.asarray(psi, complex)
    return np.outer(psi, psi.conj())


def bloch(rho) -> np.ndarray:
    return np.real([np.trace(rho @ s) for s in SIGMA])


def projectors(n) -> tuple[np.ndarray, np.ndarray]:
    """(Pi_+, Pi_-) for the spin component along n."""
    S = n_sigma(n)
    return 0.5 * (I2 + S), 0.5 * (I2 - S)


def born_probabilities(p, dim: int = 4) -> np.ndarray:
    """Born probabilities from float traces Tr(rho Pi). An exact zero comes out as +-1e-17 (review 2026-10-23, V7-1:
    numpy's Generator.choice rejects any negative entry); a value below zero by at most the round-off of a trace in a
    space of dimension ``dim`` (4 dim eps times the sum of |p|: dim products and dim - 1 additions per diagonal entry of
    rho Pi, dim terms of the trace) is set to 0. A larger negative value means rho is not a state or the Pi are not
    projectors: ValueError."""
    p = np.asarray(p, float)
    tol = 4 * dim * np.finfo(float).eps * max(1.0, float(np.sum(np.abs(p))))
    if p.size and float(p.min()) < -tol:
        raise coded(ValueError(T("Born probabilities: a negative probability {p:.3g} beyond round-off ({tol:.1e})",
                                 p=float(p.min()), tol=float(tol))), "quantum.negative_probability")
    return np.where(p < 0.0, 0.0, p)


def measure(rho, projs, rng=None):
    """Probabilities of the outcomes and, with rng, one sampled outcome and the post-measurement state."""
    p = born_probabilities([np.real(np.trace(P @ rho)) for P in projs], dim=np.shape(rho)[0])
    if rng is None:
        return p
    k = int(rng.choice(len(projs), p=p / p.sum()))
    post = projs[k] @ rho @ projs[k] / p[k]
    return p, k, post


def ptrace(rho, keep: int, dims=(2, 2)) -> np.ndarray:
    r = np.asarray(rho).reshape(dims[0], dims[1], dims[0], dims[1])
    return np.einsum("ijkj->ik", r) if keep == 0 else np.einsum("ijik->jk", r)


def entropy(rho) -> float:
    w = np.linalg.eigvalsh(rho)
    w = w[w > 1e-15]
    return float(-np.sum(w * np.log2(w)))


def concurrence(rho) -> float:
    yy = np.kron(SY, SY)
    rt = yy @ rho.conj() @ yy
    ev = np.sqrt(np.abs(np.sort(np.linalg.eigvals(rho @ rt).real)[::-1]))
    return float(max(0.0, ev[0] - ev[1] - ev[2] - ev[3]))


def larmor(omega: float, t: float, n=(0, 0, 1)) -> np.ndarray:
    return linalg.expm(-0.5j * omega * t * n_sigma(n))


SINGLET = ket(0, 1, -1, 0)
PHI_PLUS = ket(1, 0, 0, 1)


def correlation(state, A, B) -> float:
    """<A (x) B> in a two-qubit state (vector or density matrix)."""
    rho = dm(state) if np.ndim(state) == 1 else state
    return float(np.real(np.trace(rho @ np.kron(A, B))))


def spin_correlation(state, a, b) -> float:
    return correlation(state, n_sigma(a), n_sigma(b))


def polarizer_observable(angle: float) -> np.ndarray:
    """+1 transmitted / -1 absorbed by a polarizer at angle (rad) in the (H, V) basis: cos 2a sz + sin 2a sx."""
    return math.cos(2 * angle) * SZ + math.sin(2 * angle) * SX


def chsh(E, a, a2, b, b2) -> float:
    return E(a, b) - E(a, b2) + E(a2, b) + E(a2, b2)


def joint_probabilities(state, projs_a, projs_b) -> np.ndarray:
    """P(i, j) = Tr(rho (Pi_a_i (x) Pi_b_j)) for a two-qubit state (round-off below zero set to 0:
    ``born_probabilities``). The Pi may be any effects of a POVM (``povm_one_detector``, ``povm_two_detectors``)."""
    rho = dm(state) if np.ndim(state) == 1 else state
    P = np.array([[np.real(np.trace(rho @ np.kron(Pa, Pb))) for Pb in projs_b] for Pa in projs_a])
    return born_probabilities(P, dim=rho.shape[0])


def sample_pairs(state, projs_a, projs_b, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """n joint outcomes (indices) drawn from the Born probabilities of the pair (non-negative by construction of
    ``joint_probabilities``, renormalised against the round-off of their sum)."""
    P = joint_probabilities(state, projs_a, projs_b).ravel()
    k = rng.choice(len(P), size=n, p=P / P.sum())
    return k // len(projs_b), k % len(projs_b)


def polarizer_projectors(angle: float) -> tuple[np.ndarray, np.ndarray]:
    """(transmitted, absorbed) projectors of a polarizer at angle (rad) in the (H, V) basis."""
    v = np.array([math.cos(angle), math.sin(angle)], complex)
    P = np.outer(v, v.conj())
    return P, I2 - P


# --- real stations and real sources (EX2 §4.7) ------------------------------------------------------------------
ONE_DETECTOR_OUTCOMES = ("+", "0")
TWO_DETECTOR_OUTCOMES = ("+", "-", "0", "+-")


def _unit(x, name: str) -> float:
    x = float(x)
    if not 0.0 <= x <= 1.0:
        raise ValueError(T("{name} must lie in [0, 1], got {x:.4g}", name=name, x=x))
    return x


def povm_one_detector(proj, eta: float, p_dark: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """(E_+, E_0) of an analyser whose transmitted port (projector ``proj``) leads to one threshold detector of
    efficiency ``eta`` with a dark-click probability ``p_dark`` in the trial: E_0 = (1 - p_d)(I - eta Pi),
    E_+ = I - E_0. One photon per trial; several photons: ``lfphys.tools.bell_stats.slot_probabilities``."""
    eta, p_dark = _unit(eta, "eta"), _unit(p_dark, "p_dark")
    P = np.asarray(proj, complex)
    E0 = (1.0 - p_dark) * (np.eye(P.shape[0]) - eta * P)
    return np.eye(P.shape[0]) - E0, E0


def povm_two_detectors(projs, eta, p_dark=0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(E_+, E_-, E_0, E_+-) of an analyser with two output ports (projectors Pi_+, Pi_-, summing to I) and a
    threshold detector behind each (``eta``, ``p_dark``: one value or one per detector): "+" only, "-" only, no click,
    both clicked (a dark click beside a detection, or two dark clicks). One photon per trial."""
    Pp, Pm = (np.asarray(P, complex) for P in projs)
    ep, em = (_unit(e, "eta") for e in (np.broadcast_to(eta, 2)))
    dp, dm_ = (_unit(d, "p_dark") for d in (np.broadcast_to(p_dark, 2)))
    cp_p = 1.0 - (1.0 - ep) * (1.0 - dp)  # detector + clicks when the photon is at port +
    cm_m = 1.0 - (1.0 - em) * (1.0 - dm_)  # detector - clicks when the photon is at port -
    Ep = cp_p * (1.0 - dm_) * Pp + dp * (1.0 - cm_m) * Pm
    Em = (1.0 - cp_p) * dm_ * Pp + (1.0 - dp) * cm_m * Pm
    E0 = (1.0 - cp_p) * (1.0 - dm_) * Pp + (1.0 - dp) * (1.0 - cm_m) * Pm
    Eb = cp_p * dm_ * Pp + dp * cm_m * Pm
    return Ep, Em, E0, Eb


def is_povm(effects, tol: float = 1e-12) -> bool:
    """Every effect Hermitian and positive semidefinite (eigenvalues >= -tol) and their sum the identity (to tol)."""
    E = [np.asarray(e, complex) for e in effects]
    if not E:
        return False
    eye = np.eye(E[0].shape[0])
    if any(np.max(np.abs(e - e.conj().T)) > tol for e in E):
        return False
    if any(float(np.linalg.eigvalsh(0.5 * (e + e.conj().T)).min()) < -tol for e in E):
        return False
    return bool(np.max(np.abs(sum(E) - eye)) <= tol)


def eberhard_state(r: float) -> np.ndarray:
    """(|V>_A |H>_B + r |H>_A |V>_B) / sqrt(1 + r^2) in the basis |HH>, |HV>, |VH>, |VV> (Eberhard 1993; Giustina et
    al. 2015, eq. (2)). r = -1: the singlet (|VH> - |HV>)/sqrt 2; r = 0: the product |V>|H>; r and 1/r give the same
    state with the stations' H and V exchanged."""
    r = float(r)
    if not math.isfinite(r):
        raise ValueError(T("Eberhard parameter r must be finite"))
    return np.array([0.0, r, 1.0, 0.0], complex) / math.sqrt(1.0 + r * r)


def werner(state, V: float) -> np.ndarray:
    """V |psi><psi| + (1 - V) I/4 (or V rho + (1 - V) I/4): a source of visibility V; a state for 0 <= V <= 1 (for
    the singlet down to V = -1/3)."""
    rho = dm(state) if np.ndim(state) == 1 else np.asarray(state, complex)
    V = float(V)
    out = V * rho + (1.0 - V) * np.eye(rho.shape[0]) / rho.shape[0]
    if float(np.linalg.eigvalsh(0.5 * (out + out.conj().T)).min()) < -1e-12:
        raise ValueError(T("visibility V = {V:.4g} gives a matrix that is not a state", V=V))
    return out
