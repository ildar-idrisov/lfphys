# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Detector models for the arrival time of a quantum particle: the click-time distribution depends on a parameter
of the detector, and part of the particles is reflected or never detected.

* Absorbing boundary rule (ABR; Werner 1987, Tumulka 2022): the wave obeys  n . grad psi = i kappa psi  on the
  detecting surface (n outward), and the detector clicks at time t and point x with density (hbar kappa / m)|psi|^2
  (Tumulka, eqs. 3 and 7). A plane wave of wave number k is reflected with R_k = (k - kappa)^2 / (k + kappa)^2
  (Tumulka, eq. 12): kappa is the wave number the detector absorbs completely. For a free packet in x < L hitting
  x = L, the image solution gives the wave on the boundary
      psi(L, t) = (2 pi)^(-1/2) int dk psi~(k) (2k / (k + kappa)) e^{ikL - i hbar k^2 t / 2m}
  (``abr_boundary_wave``; written for k > 0 only: the packet must carry no weight at k <= 0, where the
  reflection amplitude has its pole k = -kappa), and the total click probability is int |psi~|^2 (1 - R_k) dk.
* Exponential click rates (Das & Struyve 2021, eq. 5, Table I):  Pi(t) = lambda(t) exp(-int_0^t lambda),
  P(no click) = exp(-int_0^inf lambda), with the intensity lambda_W = lambda0 |psi(L, t)|^2 (Wlodarz 2002; psi the
  free wave) or lambda_MS = (lambda0' eps / pi) |d psibar/dx (L, t)|^2 (Marchewka & Schuss 1998), eps = hbar/m and
  psibar(x, t) = psi(x, t) - psi(2L - x, t) the solution with a Dirichlet wall at L, whose derivative there is
  2 d psi/dx (L, t) (Das & Struyve, eqs. 27-28): lambda_MS = (4 lambda0' eps / pi) |d psi/dx (L, t)|^2 of the free wave.
  lambda0, lambda0' are the detector's parameters; a larger one makes the clicks come earlier and decay exponentially
  along a train of packets. (Until review B4-4 lambda_MS was written (lambda0 / pi)|d psi/dx|^2: a factor 4 eps off.)
* Absorbing potential (soft detector): V = -i W0 behind the surface. A plane wave is reflected from the step with
  R = |(k - q)/(k + q)|^2,  q = sqrt(k^2 + 2 i m W0 / hbar^2)  (Im q > 0); the click density is the absorption rate
  (2 W0 / hbar) int_{x > L} |psi|^2 (Allcock 1969; Muga, Palao & Leavens 1999). ``lfphys.core.quantum.schrodinger_nd``
  evolves it (``Hamiltonian(W=...)``, ``SplitOperator.absorbed``).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import cumulative_trapezoid

from ..interpretations.arrival_times import _chunks

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": "Модели детектора времени прихода",
    "statement": "Поглощающее граничное условие ∂ₙψ = iκψ с плотностью щелчков (ħκ/m)|ψ|² и отражением "
                 "R = (k−κ)²/(k+κ)²; экспоненциальные правила Π = λ exp(−∫λ) с λ = λ₀|ψ(L,t)|² (Влодаж) или "
                 "(λ₀′ħ/πm)|∂ψ̄(L,t)|² = (4λ₀′ħ/πm)|∂ψ(L,t)|² (Маркевка–Шусс; ψ̄ — решение со стенкой Дирихле в L); "
                 "поглощающий потенциал −iW₀ за поверхностью с отражением "
                 "|(k−q)/(k+q)|², q = √(k² + 2imW₀/ħ²).",
    "validity": "нерелятивистская частица; параметр детектора (κ, λ₀, W₀) задаётся, а не выводится; формула "
                "образа для поглощающей границы — свободное движение и пакет без составляющих с k ≤ 0",
    "basis": ["Werner, Ann. Inst. H. Poincaré A 47, 429 (1987) (по ссылке Das & Struyve 2021)",
              "Tumulka, Ann. Phys. 442, 168910 (2022), arXiv:1601.03715 — уравнения 3, 7, 12",
              "Das & Struyve, Phys. Rev. A 104, 042214 (2021), arXiv:2105.14744 — уравнение 5, таблица I",
              "Włodarz, Phys. Rev. A 65, 044103 (2002)",
              "Marchewka & Schuss, Phys. Lett. A 240, 177 (1998) (по ссылке Das & Struyve 2021)",
              "Allcock, Ann. Phys. 53, 253 и 286 (1969)", "Muga, Palao & Leavens, Phys. Lett. A 253, 21 (1999)"],
    "conflicts": ["собственные правила времени прихода (lfphys.theories.interpretations.arrival_times): модель "
                  "даёт другое распределение, часть частиц отражается или не обнаруживается, и ответ зависит от "
                  "параметра детектора; экспоненциальные правила гасят пики цепочки пакетов (Das & Struyve 2021)"],
}


def robin_reflection(k, kappa: float):
    """R_k = (k - kappa)^2 / (k + kappa)^2 of the absorbing boundary rule (Tumulka, eq. 12)."""
    k = np.asarray(k, float)
    return ((k - kappa) / (k + kappa)) ** 2


def abr_boundary_wave(phi: np.ndarray, k: np.ndarray, L: float, kappa: float, t, m: float = 1.0,
                      hbar: float = 1.0) -> np.ndarray:
    """psi(L, t) on the absorbing boundary x = L for a free packet starting in x < L, by the image solution, from its
    momentum amplitude on the uniform grid ``k`` (only k > 0 is used)."""
    t = np.atleast_1d(np.asarray(t, float))
    k = np.asarray(k, float)
    g = np.where(k > 0, np.asarray(phi, complex) * 2 * k / (k + kappa), 0.0) * np.exp(1j * k * L)
    out = np.empty(len(t), complex)
    for sl in _chunks(len(t), len(k)):
        out[sl] = np.trapezoid(g * np.exp(-1j * hbar / (2 * m) * np.outer(t[sl], k * k)), k, axis=-1)
    return out / math.sqrt(2 * math.pi)


def abr_density(phi: np.ndarray, k: np.ndarray, L: float, kappa: float, t, m: float = 1.0,
                hbar: float = 1.0) -> np.ndarray:
    """Click density (hbar kappa / m) |psi(L, t)|^2 of the absorbing boundary rule (free packet, image solution)."""
    return hbar * kappa / m * np.abs(abr_boundary_wave(phi, k, L, kappa, t, m, hbar)) ** 2


def abr_total(phi: np.ndarray, k: np.ndarray, kappa: float) -> float:
    """Total click probability int_{k > 0} |psi~|^2 4 k kappa / (k + kappa)^2 dk (the rest is reflected)."""
    k = np.asarray(k, float)
    w = np.where(k > 0, 4 * k * kappa / (k + kappa) ** 2, 0.0)
    return float(np.trapezoid(np.abs(phi) ** 2 * w, k))


def exponential(t: np.ndarray, lam: np.ndarray):
    """Pi(t) = lambda(t) exp(-int_0^t lambda) on the time grid ``t`` (starting at the preparation time) and the
    probability of no click by the last time exp(-int lambda); int Pi + P = 1 holds for the exact integrals."""
    t = np.asarray(t, float)
    lam = np.asarray(lam, float)
    Lam = cumulative_trapezoid(lam, t, initial=0.0)
    return lam * np.exp(-Lam), float(math.exp(-Lam[-1]))


def wlodarz_intensity(psi_L, lam0: float):
    """lambda_W(t) = lambda0 |psi(L, t)|^2 (Wlodarz 2002; Das & Struyve 2021, Table I)."""
    return lam0 * np.abs(psi_L) ** 2


def marchewka_schuss_intensity(dpsi_L, lam0p: float, m: float = 1.0, hbar: float = 1.0):
    """lambda_MS(t) = (lambda0' eps / pi) |d psibar/dx (L, t)|^2 = (4 lambda0' eps / pi) |d psi/dx (L, t)|^2, eps = hbar/m,
    from ``dpsi_L`` the derivative of the free wave at L (Marchewka & Schuss 1998; Das & Struyve 2021, Table I with
    eqs. 27-28)."""
    return 4 * lam0p * (hbar / m) / math.pi * np.abs(dpsi_L) ** 2


def step_reflection(k, W0: float, m: float = 1.0, hbar: float = 1.0):
    """Reflection of a plane wave of wave number k > 0 from the absorbing step V = -i W0 (x > L):
    |(k - q)/(k + q)|^2 with q = sqrt(k^2 + 2 i m W0 / hbar^2), the root with Im q > 0."""
    k = np.asarray(k, float)
    q = np.sqrt(k * k + 2j * m * W0 / hbar ** 2)
    return np.abs((k - q) / (k + q)) ** 2
