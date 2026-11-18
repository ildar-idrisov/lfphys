# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Local hidden-variable models of the correlations of a pair (alternatives refuted by loophole-free Bell tests).
Each pair carries a hidden variable lambda fixed at the source; each side's outcome depends only on its own setting
and lambda. Any such model obeys the CHSH inequality |S| <= 2.

* ``sign_model``: lambda = a random unit vector in the plane; A = sign(a.lambda), B = -sign(b.lambda)
  (Bell 1964): E(a, b) = -1 + 2 theta/pi, theta = angle between a and b (a straight line instead of -cos theta);
* ``polarization_model``: each photon has a definite polarization angle lambda (both the same), and passes a
  polarizer at alpha with probability cos^2(alpha - lambda) (Malus law, independently): E = (1/2) cos 2(alpha - beta),
  half the quantum value;
* ``gisin_gisin``: Gisin and Gisin's model that exploits the detection loophole (Phys. Lett. A 260, 323 (1999),
  §2): lambda a unit vector uniform on the sphere, lambda_B = -lambda_A; a side measuring along x gives
  sign((<sigma> - lambda) . x) = sign(-lambda . x) (the singlet's <sigma> = 0); one side (Alice in the asymmetric
  model; chosen by a fair hidden coin in the symmetric one) produces an outcome only with probability |lambda . x|,
  the other always. The pairs detected at both sides have exactly the singlet's correlation E = -a.b (their eqs.
  (3)-(10)), so CHSH from coincidences reaches 2 sqrt 2 under fair sampling, while each detector fires in 75 % of the
  pairs ("On average the detector efficiency is limited to 75%."), both in 1/2. With an extra hidden "no outcome at
  all" of probability nu (their 1/9) both detectors look independent, each with 3/4 (1 - nu) (2/3 at nu = 1/9).
  Closed forms (``gisin_gisin_table``): both detected with probability (1 - nu)/2 and then P(A, B) = (1 + A B E)/4;
  one side alone with (1 - nu)/4 each, its outcome +-1 with 1/2; none with nu. CH (Gisin and Gisin's (15)) is
  (1 - nu)(X - 4)/8 <= (1 - nu)(2 sqrt 2 - 4)/8 < 0, X = E(a,b) + E(a,b') + E(a',b) - E(a',b'). Photons: a polariser
  at alpha is the Bloch vector (sin 2 alpha, 0, cos 2 alpha) (``poincare``); |Phi+> is the singlet with Bob's vector
  rotated by pi about y (``state="phi_plus"``): E = cos 2(alpha - beta).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": T("Local hidden variables"),
    "statement": T("Each side's outcome is set by its setting and by a common hidden variable from the source; every "
                   "such model gives |S| ≤ 2 (the CHSH inequality). Gisin and Gisin's model makes detection depend on "
                   "the hidden variable: the detected pairs have the singlet's correlation −a·b and S = 2√2 under "
                   "fair sampling, with each detector firing in 75 % of the pairs; CH and J stay ≤ 0."),
    "validity": T("refuted by the loophole-free Bell experiments (2015): CHSH is violated; Gisin and Gisin's model "
                  "by any violation of CH or J (quantum mechanics violates them above 2/3 with weakly entangled "
                  "states, above 82.8 % with the maximally entangled state that the model imitates)"),
    "basis": ["Bell, Physics 1, 195 (1964)", "Hensen et al., Nature 526, 682 (2015)",
              "Gisin, Gisin, Phys. Lett. A 260, 323 (1999), arXiv:quant-ph/9905018",
              "Giustina et al., PRL 115, 250401 (2015)", "Shalm et al., PRL 115, 250402 (2015)"],
    "conflicts": [T("lfphys.core.quantum.qubits: quantum correlations give S up to 2√2"),
                  T("lfphys.tools.bell_stats: with efficiencies above 2/3 quantum mechanics violates CH and J, which "
                    "no local model does, Gisin and Gisin's included")],
}


def sign_model(a: float, b: float, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Outcomes (+-1) for n pairs, measurement directions at angles a, b (rad) in the plane."""
    lam = rng.uniform(0, 2 * math.pi, n)
    A = np.sign(np.cos(lam - a))
    B = -np.sign(np.cos(lam - b))
    return A, B


def sign_model_E(theta: float) -> float:
    th = abs((theta + math.pi) % (2 * math.pi) - math.pi)
    return -1.0 + 2.0 * th / math.pi


def polarization_model(alpha: float, beta: float, n: int, rng) -> tuple[np.ndarray, np.ndarray]:
    lam = rng.uniform(0, math.pi, n)
    A = np.where(rng.random(n) < np.cos(alpha - lam) ** 2, 1, -1)
    B = np.where(rng.random(n) < np.cos(beta - lam) ** 2, 1, -1)
    return A, B


def polarization_model_E(alpha: float, beta: float) -> float:
    return 0.5 * math.cos(2 * (alpha - beta))


# --- Gisin and Gisin (1999): the detection loophole --------------------------------------------------------------
_RY_PI = np.diag([-1.0, 1.0, -1.0])  # rotation by pi about y: |Phi+> = (1 (x) U) |psi->, E = -a . (R b)
GG_OUTCOMES = ("+", "-", "0")


def poincare(angle: float) -> np.ndarray:
    """The Bloch (Poincare) vector of the polarisation a polariser at ``angle`` (rad, from H) transmits:
    (sin 2 angle, 0, cos 2 angle), the vector of ``qubits.polarizer_observable``."""
    return np.array([math.sin(2 * angle), 0.0, math.cos(2 * angle)])


def _bob(b, state: str) -> np.ndarray:
    b = np.asarray(b, float)
    b = b / np.linalg.norm(b)
    if state == "singlet":
        return b
    if state == "phi_plus":
        return _RY_PI @ b
    raise ValueError(T("Gisin and Gisin's model: unknown state {s}", s=str(state)))


def gisin_gisin(a, b, n: int, rng, state: str = "singlet", no_outcome: float = 0.0, symmetric: bool = True):
    """Outcomes (A, B) of n pairs, each +1, -1 or 0 (no outcome), for measurement directions a, b (unit 3-vectors; a
    polariser: ``poincare(alpha)``). ``state``: "singlet" (E = -a.b among detected pairs) or "phi_plus" (photons,
    E = cos 2(alpha - beta)); ``no_outcome``: the probability nu of the extra hidden "no outcome at all";
    ``symmetric``: a fair hidden coin picks the side whose detection depends on lambda (else always Alice's)."""
    a = np.asarray(a, float)
    a = a / np.linalg.norm(a)
    bb = _bob(b, state)
    if not 0.0 <= no_outcome <= 1.0:
        raise ValueError(T("the probability of no outcome must lie in [0, 1]"))
    lam = rng.normal(size=(n, 3))
    lam /= np.linalg.norm(lam, axis=1)[:, None]
    la, lb = lam @ a, lam @ bb
    A = np.where(la < 0.0, 1, -1)   # sign(-lambda_A . a)
    B = np.where(lb > 0.0, 1, -1)   # sign(-lambda_B . b'), lambda_B = -lambda_A
    u = rng.random(n)
    alice_partial = rng.random(n) < 0.5 if symmetric else np.ones(n, bool)
    det_a = np.where(alice_partial, u < np.abs(la), True)
    det_b = np.where(alice_partial, True, u < np.abs(lb))
    none = rng.random(n) < no_outcome if no_outcome > 0.0 else np.zeros(n, bool)
    return np.where(det_a & ~none, A, 0), np.where(det_b & ~none, B, 0)


def gisin_gisin_E(a, b, state: str = "singlet") -> float:
    """The correlation of the pairs detected at both sides: -a.b (singlet) or -a.(R b) (phi_plus)."""
    a = np.asarray(a, float)
    return float(-(a / np.linalg.norm(a)) @ _bob(b, state))


def gisin_gisin_table(a, b, state: str = "singlet", no_outcome: float = 0.0) -> np.ndarray:
    """P[A, B] over the outcomes ("+", "-", "0") of the symmetric model (closed form, see the module's docstring)."""
    E = gisin_gisin_E(a, b, state)
    k = 1.0 - no_outcome
    t = np.zeros((3, 3))
    t[0, 0] = t[1, 1] = k * (1.0 + E) / 8.0
    t[0, 1] = t[1, 0] = k * (1.0 - E) / 8.0
    t[0, 2] = t[1, 2] = t[2, 0] = t[2, 1] = k / 8.0
    t[2, 2] = no_outcome
    return t


def gisin_gisin_efficiency(no_outcome: float = 0.0, symmetric: bool = True) -> tuple[float, float]:
    """(eta_A, eta_B): the fraction of pairs in which each side gives an outcome: 3/4 (1 - nu) each (symmetric), or
    (1/2, 1) times (1 - nu) (asymmetric)."""
    k = 1.0 - no_outcome
    return (0.75 * k, 0.75 * k) if symmetric else (0.5 * k, k)
