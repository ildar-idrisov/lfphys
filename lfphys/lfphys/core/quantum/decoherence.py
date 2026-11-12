# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Which-path decoherence of a two-path superposition (plan item P5): the accepted-physics baseline against which a
spontaneous-collapse model (GRW, ``theories.alternatives.collapse``) is compared.

A particle in a|1> + b|2> (two paths, e.g. two slits) has the path coherence rho_12; behind the paths the fringe
visibility is V = 2|rho_12| / (rho_11 + rho_22) (= 2|a b| |<chi_2|chi_1>| / (|a|^2 + |b|^2) with marks chi_j).

(a) Pure dephasing (a Lindblad channel, ``core.quantum.open_systems``): L = sqrt(gamma_phi/2) sigma_z on the path
    qubit gives d rho_12/dt = -gamma_phi rho_12, so V(t) = V(0) exp(-gamma_phi t); the populations do not change.

(b) A which-path probe (an environment that records the path; Wootters & Zurek 1979, Englert 1996): the probe ends
    in |chi_1> or |chi_2>, the path coherence is multiplied by <chi_2|chi_1>: V = V0 |<chi_2|chi_1>|. With path
    weights w1, w2 and pure probe states, V = 2 sqrt(w1 w2)|<chi_2|chi_1>| and Englert's distinguishability
    D = sqrt(1 - 4 w1 w2 |<chi_2|chi_1>|^2) (sqrt(1 - |<chi_2|chi_1>|^2) at equal weights), so V^2 + D^2 = 1 at any
    weights; for mixed probe states V^2 + D^2 <= 1 (``core.quantum.marks.englert``; review B5, N8). Traced over the
    probe the path qubit undergoes the channel with Kraus operators K_k = diag(<k|chi_1>, <k|chi_2>)
    (sum_k K_k^+ K_k = I).
    A Poisson stream of such probes at rate Gamma (scattered photons, gas molecules) gives the Lindblad equation with
    jump operators sqrt(Gamma) K_k: d rho_12/dt = -Gamma (1 - <chi_2|chi_1>) rho_12, so

        V(t) = V0 exp(-Gamma t (1 - Re chi)),   fringe phase shift Gamma t Im chi,   chi = <chi_2|chi_1>.

    For a probe that kicks the particle's transverse momentum by hbar q with distribution p(q), chi(d) = <exp(i q d)>
    at path separation d and F(d) = Gamma (1 - chi(d)) is the localisation rate of collisional decoherence
    (Hornberger, arXiv:quant-ph/0612118, eqs. 5.170, 5.171: d rho(X, X')/dt = -F(X - X') rho(X, X'), saturating at
    the collision rate for large separations). Gaussian kicks q ~ N(0, 1/(2 a^2)) give chi(d) = exp(-d^2/(4 a^2)).

How the baseline compares with GRW. The GRW master equation (Bassi et al., RMP 85, 471 (2013), eqs. 21, 22) is
    <x|T[rho]|y> = lambda [1 - exp(-(x - y)^2/(4 r_C^2))] <x|rho|y>,
with lambda the localisation rate (lambda_GRW ~ 1e-16 1/s per nucleon, r_C ~ 1e-7 m, their eq. 19; N lambda for the
centre of mass of N nucleons): exactly the Gaussian-kick probe stream (b) with Gamma = lambda, a = r_C (the kicks
of ``theories.alternatives.collapse.grw_kicks``). On the visibility of one two-path superposition GRW and an
environment of that kind are therefore indistinguishable; they differ in how the rate scales: GRW with the mass and
nothing else, decoherence with the environment (pressure, temperature, scattered light), which experiments suppress
in order to bound lambda. ``localisation_rate`` and ``converging_paths_visibility`` give the baseline; a world that
uses GRW passes its lambda and r_C to the same Gaussian form (the comparison function lives outside the core:
``theories.alternatives.collapse_baseline.compare``).

Double slit: the two paths start a distance d apart at the slits and meet at the point of the screen, so the
separation falls linearly, s = d (1 - z/L); a constant rate Gamma over the flight time T with Gaussian kicks gives
    V/V0 = exp(-Gamma T [1 - (sqrt(pi) a/d) erf(d/(2a))])
(the average of the kick factor over the flight); this is the GRW factor used by the v02 world, and |phi(k d/z)| of
``collapse.grw_shift_cf`` (tested).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Декогеренция путей: дефазировка и регистрация пути средой",
    "statement": "Видность двух путей V = 2|ρ₁₂|/(ρ₁₁ + ρ₂₂): при дефазировке Линдблада V = V₀e^{−γ_φ t}; при "
                 "зонде-регистраторе V = V₀|⟨χ₂|χ₁⟩|; при пуассоновском потоке зондов V = V₀exp(−Γt(1 − Re χ)), "
                 "скорость локализации F(d) = Γ(1 − χ(d)), для гауссовых толчков χ = e^{−d²/4a²} — та же форма, что у "
                 "члена GRW (база для сравнения со спонтанным коллапсом).",
    "validity": "марковская среда (независимые столкновения, мгновенные по сравнению со временем пролёта); "
                "зонд не меняет населённости путей; две точки в пространстве путей",
    "basis": ["Wootters & Zurek, Phys. Rev. D 19, 473 (1979)", "Englert, PRL 77, 2154 (1996)",
              "Joos & Zeh, Z. Phys. B 59, 223 (1985)",
              "Hornberger, Introduction to decoherence theory, arXiv:quant-ph/0612118, eqs. (5.170)–(5.171)",
              "Bassi et al., Rev. Mod. Phys. 85, 471 (2013), eqs. (19), (21), (22) — форма члена GRW",
              "lfphys/sources/verification_2026-10-29_p5.md — проверка цитат и выводов"],
    "conflicts": [],
}

SZ = np.array([[1, 0], [0, -1]], complex)


def visibility(rho) -> float:
    """Fringe visibility 2|rho_12| / (rho_11 + rho_22) of a two-path density matrix."""
    rho = np.asarray(rho, complex)
    return float(2 * abs(rho[0, 1]) / np.real(rho[0, 0] + rho[1, 1]))


# --- (a) pure dephasing ---------------------------------------------------------------------------------------------

def dephasing_operators(gamma_phi: float) -> list[np.ndarray]:
    """Jump operator of pure dephasing at coherence decay rate gamma_phi: sqrt(gamma_phi/2) sigma_z."""
    return [math.sqrt(0.5 * gamma_phi) * SZ]


def dephasing_visibility(t, gamma_phi: float, v0: float = 1.0):
    return v0 * np.exp(-gamma_phi * np.asarray(t, float))


# --- (b) which-path probes ------------------------------------------------------------------------------------------

def probe_overlap(chi1, chi2) -> complex:
    """<chi_2|chi_1> of normalised probe states."""
    c1 = np.asarray(chi1, complex)
    c2 = np.asarray(chi2, complex)
    return complex(np.vdot(c2 / np.linalg.norm(c2), c1 / np.linalg.norm(c1)))


def probe_visibility(chi1, chi2, w1: float = 0.5) -> tuple[float, float]:
    """(V, D) after one which-path probe for path weights (w1, 1 - w1): V = 2 sqrt(w1 w2)|<chi_2|chi_1>|; D (Englert,
    pure probe states) = sqrt((w1 - w2)^2 + 4 w1 w2 (1 - |<chi_2|chi_1>|^2))."""
    w2 = 1.0 - w1
    ov = abs(probe_overlap(chi1, chi2))
    V = 2 * math.sqrt(w1 * w2) * ov
    D = math.sqrt(max(0.0, (w1 - w2) ** 2 + 4 * w1 * w2 * (1 - ov * ov)))
    return V, D


def probe_qubit(theta: float) -> tuple[np.ndarray, np.ndarray]:
    """A probe qubit left in |0> by path 1 and rotated to cos(theta)|0> + sin(theta)|1> by path 2: V = |cos theta|."""
    return np.array([1.0, 0.0], complex), np.array([math.cos(theta), math.sin(theta)], complex)


def probe_kraus(chi1, chi2) -> list[np.ndarray]:
    """Kraus operators K_k = diag(<k|chi_1>, <k|chi_2>) of the path channel after tracing out the probe."""
    c1 = np.asarray(chi1, complex) / np.linalg.norm(chi1)
    c2 = np.asarray(chi2, complex) / np.linalg.norm(chi2)
    return [np.diag([c1[k], c2[k]]) for k in range(len(c1))]


def probe_stream_operators(rate: float, chi1, chi2) -> list[np.ndarray]:
    """Lindblad jump operators sqrt(rate) K_k of a Poisson stream of which-path probes."""
    return [math.sqrt(rate) * K for K in probe_kraus(chi1, chi2)]


def probe_stream_coherence(t, rate: float, chi: complex, rho12_0: complex = 0.5):
    """rho_12(t) = rho_12(0) exp(-rate t (1 - chi)) under a Poisson stream of probes with overlap chi."""
    return rho12_0 * np.exp(-rate * np.asarray(t, float) * (1 - complex(chi)))


def probe_stream_visibility(t, rate: float, chi: complex, v0: float = 1.0):
    return v0 * np.exp(-rate * np.asarray(t, float) * (1 - complex(chi).real))


# --- localisation by momentum kicks ---------------------------------------------------------------------------------

def gaussian_kick_overlap(d, a: float):
    """chi(d) = <exp(i q d)> for q ~ N(0, 1/(2 a^2)): exp(-d^2/(4 a^2))."""
    d = np.asarray(d, float)
    return np.exp(-d * d / (4.0 * a * a))


def localisation_rate(d, rate: float, a: float | None = None, overlap=None):
    """F(d) = rate (1 - Re chi(d)): Gaussian kicks of width parameter a, or any overlap function chi(d)."""
    chi = gaussian_kick_overlap(d, a) if overlap is None else np.real(overlap(np.asarray(d, float)))
    return rate * (1.0 - chi)


def mean_kick_loss_converging(d: float, a: float) -> float:
    """1 - (1/d) int_0^d exp(-s^2/(4 a^2)) ds = 1 - (sqrt(pi) a/d) erf(d/(2a)): the average per-kick loss of
    coherence when the separation falls linearly from d to 0 (paths meeting at the screen)."""
    x = d / (2.0 * a)
    if x < 1e-4:  # series: 1 - (1 - x^2/3 + x^4/10) = x^2/3 - x^4/10
        return x * x / 3.0 - x ** 4 / 10.0
    return 1.0 - math.sqrt(math.pi) * special.erf(x) / (2.0 * x)


def converging_paths_visibility(d: float, rate_times_T: float, a: float, v0: float = 1.0) -> float:
    """V = V0 exp(-Gamma T [1 - (sqrt(pi) a/d) erf(d/(2a))]) for Gaussian kicks during a flight in which the path
    separation falls linearly from d to 0."""
    return v0 * math.exp(-rate_times_T * mean_kick_loss_converging(d, a))


def separation_visibility(sep_of_t, t_end: float, rate: float, a: float | None = None, overlap=None,
                          v0: float = 1.0, n: int = 200) -> float:
    """V = V0 exp(-int_0^T F(s(t)) dt) for any separation history s(t) (Gauss-Legendre with n nodes; exact for
    polynomial integrands of degree < 2n)."""
    x, w = np.polynomial.legendre.leggauss(n)
    t = 0.5 * t_end * (x + 1.0)
    F = localisation_rate(np.abs(sep_of_t(t)), rate, a, overlap)
    return v0 * math.exp(-0.5 * t_end * float(np.sum(w * F)))
