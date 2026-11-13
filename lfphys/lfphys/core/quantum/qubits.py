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
* polarization-entangled photons |Phi+> = (|HH> + |VV>)/sqrt 2: E(alpha, beta) = cos 2(alpha - beta).
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
                   "to 2√2."),
    "validity": T("quantum mechanics of finite-dimensional systems"),
    "basis": ["Bell, Physics 1, 195 (1964)", "Clauser, Horne, Shimony, Holt, PRL 23, 880 (1969)",
              "Tsirelson, Lett. Math. Phys. 4, 93 (1980)", "Wootters, PRL 80, 2245 (1998)",
              T("loophole-free experiments: Hensen et al. 2015; Giustina et al. 2015; Shalm et al. 2015")],
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
    ``born_probabilities``)."""
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
