# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""When does a quantum particle arrive at a detector? Intrinsic (apparatus-independent) arrival-time proposals.

Quantum mechanics has no self-adjoint time operator, so the probability density Pi(t) of the arrival time at a
surface is not fixed by the Born rule for positions; several rules are in use and they disagree:

* quantum flux (QF):  Pi(t) = n . j(L, t),  j = (hbar/m) Im(psi* grad psi)  (integrated over the surface).
  Negative where the current flows back (quantum backflow), so it is a probability density only for states without
  backflow at L.
* de Broglie-Bohm first arrival: the time a Bohmian trajectory first reaches the surface. It equals QF when no
  trajectory crosses the surface twice; in one dimension trajectories never cross each other, so the first-arrival
  distribution follows from the probability F(t) left of L alone:  P(T <= t) = F(0) - min_{s <= t} F(s)
  (``bohm_first_arrival``). Never negative.
* Aharonov-Bohm-Kijowski (ABK), free particles: the symmetric quantisation of the classical tau = m (L - z)/p,
    Pi_AB(t) = (hbar / 2 pi m) sum_{alpha = +-} | int dk theta(alpha k) sqrt|k| psi~(k) e^{ikL - i hbar k^2 t/2m} |^2
  (Das & Noeth 2021, eq. 5, there with hbar = m = 1), normalised over -inf < t < inf; the weight at t < 0 is read as
  the probability of no detection (their eq. 7).
* semiclassical (TOF analysis):  Pi_SC(t) = (m d / hbar t^2) |psi~(m d / hbar t)|^2  for a flight of length d from the
  point the packet starts from (Das & Struyve 2021, eq. 3): the classical t = m d / p with the quantum momentum distribution.

psi~(k) = (2 pi)^(-1/2) int psi(x, 0) e^{-ikx} dx throughout (normalised in k). For a state separable along the
flight direction z and across it, psi = chi(x) phi(z), all four rules for a detecting plane z = L reduce to the
one-dimensional ones for phi (the transverse factor integrates to 1); that is how they are applied in two dimensions.

Detector models (absorbing boundary, exponential click rates, an absorbing potential) are in
``lfphys.theories.models.detection``.
"""

from __future__ import annotations

import math

import numpy as np

ABOUT = {
    "layer": "theories", "kind": "interpretation",
    "title": "Время прихода частицы к детектору: собственные правила",
    "statement": "Правила для плотности времени прихода Π(t) к поверхности, не зависящие от устройства детектора: "
                 "квантовый поток Π = j·n (Бом при отсутствии обратного тока); первое прибытие бомовских траекторий "
                 "(в 1-D — по бегущему минимуму вероятности слева от L); Ааронов–Бом–Киёвский "
                 "Π = (ħ/2πm)Σ_α|∫dk θ(αk)√|k| ψ̃ e^{ikL−iħk²t/2m}|² для свободной частицы; полуклассическое "
                 "Π = (md/ħt²)|ψ̃(md/ħt)|².",
    "validity": "нерелятивистская частица; АБК и полуклассическое — только свободное движение (АБК — по всей "
                "оси времени, вес при t < 0 читается как вероятность «не обнаружена»); полуклассическое — когда "
                "путь много больше размера пакета; для состояния, разделимого по направлению полёта и поперёк, "
                "правила для плоскости сводятся к одномерным",
    "basis": ["Das & Struyve, Phys. Rev. A 104, 042214 (2021), arXiv:2105.14744 — экспоненциальные правила и полуклассическое",
              "Das & Nöth, Proc. R. Soc. A 477, 20210101 (2021), arXiv:2102.02661 — АБК, уравнение 5",
              "Aharonov & Bohm, Phys. Rev. 122, 1649 (1961); Kijowski, Rep. Math. Phys. 6, 361 (1974)",
              "Leavens, Phys. Lett. A 178, 27 (1993) — время прихода по Бому",
              "Muga & Leavens, Phys. Rep. 338, 353 (2000) — обзор"],
    "conflicts": ["стандартная квантовая механика (lfphys.core.quantum): оператора времени нет, правило Борна "
                  "время прихода не определяет; правила между собой расходятся — при обратном токе поток "
                  "отрицателен, у АБК есть «отрицательные времена», полуклассическое не различает пакеты с "
                  "одним распределением импульса (цепочка пакетов: Das & Struyve 2021)",
                  "модели детекторов (lfphys.theories.models.detection): дают другое распределение и долю "
                  "необнаруженных частиц, зависящие от параметров детектора"],
}


def flux_density(J: np.ndarray) -> np.ndarray:
    """Pi_QF(t): the current through the surface (already integrated over it), returned as given; its negative values
    are quantum backflow, where QF is not a probability density."""
    return np.asarray(J, float)


def bohm_first_arrival(t: np.ndarray, F: np.ndarray):
    """First-arrival distribution of one-dimensional Bohmian trajectories at x = L from F(t) = P(x < L, t).

    In one dimension Bohmian trajectories keep their order, so the trajectory started at the quantile u (the
    probability left of it) is left of L exactly while F(t) > u. It has arrived by time t if F(s) <= u for some
    s <= t, so  P(T <= t) = F(t[0]) - min_{s <= t} F(s)  for the trajectories left of L at t[0]. Returns (cdf, pdf),
    the pdf as the derivative of the running minimum (piecewise linear between the samples)."""
    t = np.asarray(t, float)
    F = np.asarray(F, float)
    cdf = F[0] - np.minimum.accumulate(F)
    pdf = np.gradient(cdf, t)
    return cdf, np.maximum(pdf, 0.0)


def _integrate(f, k):
    return np.trapezoid(f, k, axis=-1)


def _chunks(nt: int, nk: int, budget: int = 4_000_000):
    """Slices of the time axis so that a (times x wave numbers) array stays within ``budget`` elements."""
    step = max(1, budget // max(nk, 1))
    return [slice(i, min(i + step, nt)) for i in range(0, nt, step)]


def kijowski(phi: np.ndarray, k: np.ndarray, L: float, t, m: float = 1.0, hbar: float = 1.0) -> np.ndarray:
    """Aharonov-Bohm-Kijowski density at x = L for a free particle, from the momentum amplitude ``phi`` sampled on the
    uniform grid ``k`` (it must decay at both ends; the trapezoid rule then converges spectrally except at k = 0,
    where sqrt|k| has a kink: its error is negligible when phi(0) is). The phase k L - hbar k^2 t / 2m must be resolved:
    dk < 2 pi / max|L - hbar k t / m| over the support of phi. Integrates to int |phi|^2 dk = 1 over all t."""
    t = np.atleast_1d(np.asarray(t, float))
    phi = np.asarray(phi, complex)
    k = np.asarray(k, float)
    g = [np.where(alpha * k > 0, np.sqrt(np.abs(k)) * phi, 0.0) * np.exp(1j * k * L) for alpha in (1.0, -1.0)]
    out = np.zeros(len(t))
    for sl in _chunks(len(t), len(k)):
        ph = np.exp(-1j * hbar / (2 * m) * np.outer(t[sl], k * k))
        out[sl] = sum(np.abs(_integrate(gi * ph, k)) ** 2 for gi in g)
    return hbar / (2 * math.pi * m) * out


def semiclassical(phi_of_k, d: float, t, m: float = 1.0, hbar: float = 1.0) -> np.ndarray:
    """Pi_SC(t) = (m d / hbar t^2) |psi~(m d / hbar t)|^2 for a flight of length d (> 0) from the point the packet
    starts from; ``phi_of_k`` is the momentum amplitude as a function (normalised in k). Zero for t <= 0."""
    t = np.atleast_1d(np.asarray(t, float))
    out = np.zeros(len(t))
    pos = t > 0
    k = m * d / (hbar * t[pos])
    out[pos] = m * d / (hbar * t[pos] ** 2) * np.abs(phi_of_k(k)) ** 2
    return out


class Semiclassical:
    """The semiclassical rule through its cumulative distribution, exact in k: a flight of length d arrives by time t
    when hbar k / m >= d / t, so  P(T <= t) = int_{k >= m d / hbar t} |psi~(k)|^2 dk  (only k > 0 arrives). Bin
    averages [F(t2) - F(t1)] / (t2 - t1) cannot alias, unlike samples of the density, whose fringes for a train of
    packets (the comb |sum_j e^{ik j sep}|^2) are ~2 pi d / (sep k0^2 v0) apart in time (review B4-2: 1501 samples
    over a long window gave totals of 0.73-1.17). ``phi_of_k`` is the momentum amplitude (normalised in k), tabulated
    on n points of [k_lo, k_hi] (choose dk well below 2 pi / the state's extent)."""

    def __init__(self, phi_of_k, d: float, k_lo: float, k_hi: float, n: int, m: float = 1.0, hbar: float = 1.0):
        self.d, self.m, self.hbar = float(d), float(m), float(hbar)
        k = np.linspace(max(k_lo, 0.0), k_hi, int(n))
        w = np.abs(phi_of_k(k)) ** 2
        seg = 0.5 * (w[1:] + w[:-1]) * np.diff(k)
        self.k = k
        self.above = np.concatenate([np.cumsum(seg[::-1])[::-1], [0.0]])  # int_k^{k_hi} |psi~|^2
        self.w = w

    def cdf(self, t) -> np.ndarray:
        t = np.atleast_1d(np.asarray(t, float))
        out = np.zeros(len(t))
        pos = t > 0
        kc = self.m * self.d / (self.hbar * t[pos])
        out[pos] = np.interp(kc, self.k, self.above, left=self.above[0], right=0.0)
        return out

    def bin_density(self, t_edges) -> np.ndarray:
        """Average density over each interval of ``t_edges``."""
        t_edges = np.asarray(t_edges, float)
        return np.diff(self.cdf(t_edges)) / np.diff(t_edges)

    def moments(self, t_max: float):
        """(probability of arrival by t_max, the mean arrival time and its standard deviation among those), by
        quadrature in k of t(k) = m d / (hbar k) over k >= m d / (hbar t_max)."""
        kc = self.m * self.d / (self.hbar * t_max)
        sel = self.k >= kc
        k, w = self.k[sel], self.w[sel]
        if len(k) < 2:
            return 0.0, None, None
        tk = self.m * self.d / (self.hbar * k)
        tot = float(np.trapezoid(w, k))
        mean = float(np.trapezoid(w * tk, k) / tot)
        sd = float(np.sqrt(max(np.trapezoid(w * (tk - mean) ** 2, k) / tot, 0.0)))
        return tot, mean, sd
