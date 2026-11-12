# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Exact beams with orbital angular momentum (plan P14.7) and the densities of their energy, momentum and angular
momentum.

Units: natural, epsilon0 = mu0 = c = 1, so omega = k; time dependence exp(-i omega t); fields are complex amplitudes,
densities time-averaged. The paraxial modes (Laguerre-Gauss, Hermite-Gauss) are an approximation and live in
``lfphys.theories.approx.beams_paraxial``; this module holds exact solutions and functions of sampled fields.

**Bessel beams** (exact scalar solutions of Helmholtz's equation): U = J_l(k sin(t0) r) exp(i l phi) exp(i k cos(t0) z).
The vector Bessel beam of helicity sigma (one cone of plane waves, below) is an exact solution of Maxwell's equations.

**Exact scalar vortex beam** given on z = 0 as U0(r) exp(i l phi): with A(q) = int_0^inf U0(r) J_l(q r) r dr (the
order-l Hankel transform; ``lg_waist_spectrum`` in closed form for a Laguerre-Gauss waist, ``gaussian_vortex_spectrum``
for a Gaussian behind a spiral phase plate, ``hankel_transform`` by quadrature for any profile)
    U(r, phi, z) = exp(i l phi) int_0^inf A(q) J_l(q r) exp(i k_z z) q dq,   k_z = sqrt(k^2 - q^2)
(evanescent for q > k, z >= 0): the Rayleigh-Sommerfeld field of these boundary values, the radial form of
``angular_spectrum`` (an independent second route; the tests compare them).

**Exact vector beam** (helicity sigma = +-1, a superposition of the two allowed): the plane-wave spectrum
    E~(k_t) = 2 pi (-i)^l A(q) exp(i (l + sigma) phi_k) (theta^ + i sigma phi^) / sqrt2,   q = k sin(theta) <= k,
E = (2 pi)^-2 int E~ exp(i k.r) d^2 k_t: every plane wave is transverse, so E is an exact solution of Maxwell's
equations; H = -i sigma E (each plane wave has helicity sigma); rotation about z by alpha multiplies it by
exp(-i (l + sigma) alpha) (an eigenstate of J_z with m = l + sigma). Doing the phi_k integral:
    E = e_s exp(i l phi) F0 + e_-s exp(i (l + 2 s) phi) F2 + z^ exp(i (l + s) phi) F1,   e_+-s = (x^ +- i s y^) / sqrt2,
    F0 = int A (1 + c)/2 J_l(q r) e^{i k c z} q dq,  F2 = int A (1 - c)/2 J_{l+2s} e^{i k c z} q dq,
    F1 = -(i^s / sqrt2) int A sin(theta) J_{l+s} e^{i k c z} q dq,   c = cos(theta),
so in the paraxial limit (c -> 1) E -> U e_s with U the scalar vortex beam of the same spectrum. The integrals run over
theta in [0, theta_max] (q dq = k^2 sin cos dtheta) by composite Gauss-Legendre, error estimated by doubling.
The vector beam is built from the propagating part of the spectrum (q <= k) only: a source whose spectrum reaches
beyond k (a waist narrower than about a wavelength, the singular centre of a spiral plate) is not reproduced on z = 0;
``propagating_fraction`` gives the share of the source's power the beam keeps (Hankel-Parseval: the L2 distance between
the named source and the beam's field on z = 0 is sqrt(1 - fraction) of the source's norm). The J_z eigenstate built
this way is the construction of Bliokh et al. 2010 (each plane wave of helicity sigma carries exp(i (l + sigma) phi_k));
J_z = l + sigma per photon is a property of this construction, not of every nonparaxial beam with a phase exp(i l phi):
Barnett & Allen's 1994 beam is not a J_z eigenstate and its ratio "was found not to be (l + sigma)/omega" (Monteiro,
Maia Neto & Nussenzveig, Phys. Rev. A 79, 033830 (2009), the secondary account; Barnett & Allen's text not obtained).

**Densities** (Berry, J. Opt. A 11, 094001 (2009), Eq. 3.5; Bliokh, Bekshaev & Nori, New J. Phys. 15, 033026 (2013),
Eqs. 3.27, 3.42, 3.43, 3.45, natural units; dual-symmetric: electric and magnetic halves):
    w = (|E|^2 + |H|^2) / 4,  P = Re(E* x H) / 2 (Poynting = momentum density),
    p_o = Im(E*.(grad)E + H*.(grad)H) / (4 omega) (canonical, orbital),  S = Im(E* x E + H* x H) / (4 omega) (spin),
    P = p_o + (1/2) curl S  (tested pointwise),
    L_z = int (x p_o,y - y p_o,x) dA,  S_z = int S_z dA,  W = int w dA  per unit length (transverse plane z).
For the vector beam, per photon (N = W / omega) and PER UNIT LENGTH, with <.> the average over |A|^2 q dq: J_z =
L_z + S_z = l + sigma, S_z = sigma <cos theta>, L_z = l + sigma (1 - <cos theta>) — the integrals over the plane are
incoherent sums over the spectrum, and in the circular basis the orders l, l + 2 sigma, l + sigma carry the weights
(1+c)^2/4, (1-c)^2/4, s^2/2. This is the canonical split of Bliokh et al. 2010 (their Eq. 22, "S = ... sigma kappa
|E~_sigma|^2 d2k", kappa = k/k, normalised by "the energy per unit z-length" of their Eq. A7, gives S_z = sigma
<cos theta> for any spectrum; for one cone, theta = t0, it is their Eq. 25: L_z = l + sigma Phi_B/2pi, S_z = sigma
(1 - Phi_B/2pi), Phi_B = 2 pi (1 - cos t0)); |S_z| < 1.
**The split depends on the definition; only J_z = l + sigma does not.** Through a plane (Maxwell stress T_ij =
Re(E_i E_j* + H_i H_j*)/2 - delta_ij (|E|^2 + |H|^2)/4; momentum flux -T) the angular-momentum flux over the energy
flux is (l + sigma)/omega for this eigenstate of J_z (Noether; measured in the tests). Barnett's separation of that
flux (J. Opt. B 4, S7 (2002), text not obtained) as Monteiro et al. 2009 apply it to a focused beam (their Eq. 33,
one helicity: spin flux = sigma/(2 omega) int |E_T|^2 dA) gives per photon crossing the plane
    S_flux = sigma <(1 + cos^2 theta)/2> / <cos theta>  (|S_flux| > 1),  L_flux = l + sigma - S_flux,
the change from the paraxial values having the opposite sign to the canonical split's ("r is positive and does not
depend on the sign of l nor on the value of sigma", Monteiro et al.). The engine evaluates the spin flux of sampled
fields as -int Im(E_T* . H_T) dA / (2 omega), which equals their Eq. 33 for each helicity and has no cross terms
between the helicities (derived here); ``moments`` gives both splits in closed form, ``angular_momentum`` measures both.
The Poynting angular momentum per unit length int (r x P)_z dA differs from L_z + S_z by (1/2) d/dz int r.S_T dA
(integration by parts). For a field of one helicity S = sigma P / omega pointwise (Bliokh, Bekshaev & Nori 2013,
Eq. 3.50), so int r.S_T dA = (sigma/omega) int r.P_T dA = (sigma / 2 omega) d/dz int r^2 P_z dA (div P = 0), and
int r^2 |U|^2 dA of a field with a plane-wave spectrum is quadratic in z with second derivative 2 int tan^2(theta)
|U~|^2: per photon
    J_Poynting = l + sigma + (sigma/2) <sin^2 theta / cos theta>   (sigma -> sigma_bar for a mixture; derived here),
the same on every plane z: a property of the angular spread, present at the waist as much as anywhere (measured in the
tests at z = 0, near the waist and at z_R). An ideal Bessel beam (not normalisable) has no radial flow, r.S_T = 0;
the closed form holds for every beam of finite energy, so a finite beam whose spectrum narrows to one cone keeps the
term (sigma/2) sin^2 t0 / cos t0 per photon: the limit is not uniform.

**Tables**: ``RadialTable`` interpolates a beam's radial functions (bicubic splines of the envelopes F e^{-ikz}, the
carrier exact) for fast evaluation anywhere; its error is measured against the direct route by the caller.

**Topological charge**: the winding of the phase along a closed loop, sum of wrapped differences / 2 pi; on a grid the
charges of the plaquettes (2 x 2 cells), whose sum over a region is the winding along its boundary (no
interpolation). **Flow lines**: dr/dz = P_T / P_z traced by RK4. **Equiphase surfaces**: crossings of
arg(U e^{-i Phi0}) = 0 along one axis of a sampled field (``phase_crossings``: each zero counted once), connected into a
triangle mesh.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.special import eval_genlaguerre, ive, jv

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": "Точные пучки с орбитальным моментом: бесселевы, скалярные и векторные вихревые пучки",
    "statement": "Бесселевы пучки — точные решения уравнения Гельмгольца; вихревой пучок порядка l по его спектру "
                 "(преобразование Ганкеля): скалярный (Рэлей–Зоммерфельд) и векторный (плоские волны спиральности σ с "
                 "множителем e^{i(l+σ)φ_k} — собственное состояние J_z, точное решение уравнений Максвелла, "
                 "J_z = l + σ на фотон). Плотности энергии, вектор Пойнтинга, орбитальная и спиновая части (Берри), "
                 "момент импульса на фотон на единицу длины (каноническое разделение Блиоха и др. 2010) и потоки через "
                 "плоскость (разделение потока по Барнетту — в форме Монтейру и др. 2009); момент по Пойнтингу в "
                 "замкнутой форме; топологический заряд по обходу фазы, линии потока энергии, поверхности равной фазы.",
    "validity": "свободное пространство, монохроматическое поле; численная ошибка квадратур оценивается удвоением "
                "(измерена в тестах); векторный пучок содержит только распространяющиеся волны (доля мощности "
                "источника, которую он сохраняет, — propagating_fraction); разделение момента на спин и орбиту "
                "зависит от определения, от определения не зависит только J_z = l + σ",
    "basis": ["Durnin, J. Opt. Soc. Am. A 4, 651 (1987) — бесселевы пучки",
              "Berry, J. Opt. A 11, 094001 (2009), ур. 3.5 — орбитальный и спиновый токи",
              "Bliokh, Bekshaev, Nori, New J. Phys. 15, 033026 (2013), ур. 3.27, 3.42–3.45, 3.50",
              "Bliokh, Alonso, Ostrovskaya, Aiello, Phys. Rev. A 82, 063825 (2010), ур. 22, 25–26, A7 — построение "
              "собственного состояния J_z и каноническое разделение на единицу длины",
              "Monteiro, Maia Neto, Nussenzveig, Phys. Rev. A 79, 033830 (2009), ур. 33 — разделение потока по "
              "Барнетту для сфокусированного пучка",
              "Barnett, J. Opt. B 4, S7 (2002) — поток момента (аннотация; текст не получен)",
              "Barnett & Allen, Opt. Commun. 110, 670 (1994) — их непараксиальный пучок не собственное состояние "
              "J_z (по Монтейру и др. 2009; текст не получен)"],
    "conflicts": [],
}

_GL_X, _GL_W = np.polynomial.legendre.leggauss(16)


def _nodes(a: float, b: float, npan: int):
    e = np.linspace(a, b, npan + 1)
    lo, hi = e[:-1, None], e[1:, None]
    return (0.5 * (hi - lo) * _GL_X[None, :] + 0.5 * (hi + lo)).ravel(), (0.5 * (hi - lo) * _GL_W[None, :]).ravel()


# --- spectra of sources (order-l Hankel transforms) ------------------------------------------------------------------
def lg_waist_spectrum(p: int, l: int, w0: float):
    """A(q) of the Laguerre-Gauss waist U0(r) = (C_pl/w0) (sqrt2 r/w0)^|l| L_p^|l|(2 r^2/w0^2) exp(-r^2/w0^2),
    C_pl = sqrt(2 p!/(pi (p+|l|)!)) (normalised: int |U0|^2 dA = 1), order l: the LG functions are eigenfunctions of
    the Hankel transform, A(q) = s (-1)^p (C_pl w0 / 2) y^|l| L_p^|l|(y^2) exp(-y^2/2), y = q w0/sqrt2,
    s = (-1)^|l| for l < 0 (J_{-n} = (-1)^n J_n). Returns (fn, q_max) with |A| < 1e-17 max|A| beyond q_max."""
    a = abs(l)
    C = math.sqrt(2.0 * math.factorial(p) / (math.pi * math.factorial(p + a)))
    s = (-1) ** a if l < 0 else 1
    pref = s * (-1) ** p * C * w0 / 2.0

    def fn(q):
        y = np.asarray(q, float) * w0 / math.sqrt(2.0)
        return pref * y ** a * eval_genlaguerre(p, a, y * y) * np.exp(-0.5 * y * y)
    ys = np.linspace(0.0, 60.0, 24001)
    v = np.abs(ys ** a * eval_genlaguerre(p, a, ys * ys) * np.exp(-0.5 * ys * ys))
    big = np.nonzero(v > 1e-17 * v.max())[0]
    return fn, float(ys[min(big[-1] + 1, len(ys) - 1)] * math.sqrt(2.0) / w0)


_X_ASYMP = 1e6


def _ive_diff_asymptotic(n: int, x, terms: int = 8):
    """I_{(n-1)/2}(x) e^-x - I_{(n+1)/2}(x) e^-x for large x by the asymptotic series (the k = 0 terms cancel)."""
    x = np.asarray(x, float)
    a, b = (n - 1) / 2.0, (n + 1) / 2.0
    ca = cb = 1.0
    tot = np.zeros_like(x)
    for kk in range(1, terms + 1):
        ca *= (4 * a * a - (2 * kk - 1) ** 2) / (kk * 8.0)
        cb *= (4 * b * b - (2 * kk - 1) ** 2) / (kk * 8.0)
        tot = tot + (-1) ** kk * (ca - cb) / x ** kk
    return tot / np.sqrt(2 * math.pi * x)


def gaussian_vortex_spectrum(l: int, w: float):
    """A(q) of the boundary value U0(r) exp(i l phi), U0 = exp(-r^2/w^2) (what a thin spiral phase plate imposes on a
    Gaussian: ``lfphys.theories.approx.beams_thin_masks``): int exp(-r^2/w^2) J_l(q r) r dr =
    (sqrt(pi) q w^3 / 8) exp(-x) [I_{(n-1)/2}(x) - I_{(n+1)/2}(x)], x = q^2 w^2 / 8, n = |l| (times (-1)^n for l < 0);
    evaluated with exponentially scaled Bessel functions (the test compares it with ``hankel_transform``); for
    x > 1e6 by the asymptotic series of the difference, (2 pi x)^-1/2 sum_k (-1)^k (a_k((n-1)/2) - a_k((n+1)/2)) x^-k,
    a_k(nu) = prod_{j<=k} (4 nu^2 - (2j - 1)^2) / (k! 8^k), whose leading term n / (2 x sqrt(2 pi x)) gives the q^-2 tail
    (SciPy's ``ive`` returns NaN for x of order 1e10, which an integral over the unbounded tail reaches).
    Returns (fn, q_max): q_max = inf for l != 0 (see below), 12 / w for l = 0 (|A| < 1e-15 max beyond)."""
    n = abs(l)
    s = (-1) ** n if l < 0 else 1

    def fn(q):
        q = np.asarray(q, float)
        x = q * q * w * w / 8.0
        safe = np.where(x > 0, x, 1.0)
        small = np.minimum(safe, _X_ASYMP)
        d = np.where(safe > _X_ASYMP, _ive_diff_asymptotic(n, np.maximum(safe, _X_ASYMP)),
                     ive((n - 1) / 2.0, small) - ive((n + 1) / 2.0, small))
        v = s * math.sqrt(math.pi) * q * w ** 3 / 8.0 * d
        return np.where(x > 0, v, 0.5 * w * w if n == 0 else 0.0)  # the limit q -> 0
    # for l != 0 the source is singular on the axis (a phase vortex of non-zero amplitude): the spectrum falls only
    # like q^-2, so there is no finite cut-off; the beam's evanescent part is cut where exp(-t z) is negligible
    # (``VortexBeam.scalar``'s z_min)
    return fn, (math.inf if n else 12.0 / w)


def hankel_transform(f: Callable, l: int, q, r_max: float, panels: int = 200):
    """int_0^r_max f(r) J_l(q r) r dr by composite Gauss-Legendre (f decays to nothing before r_max): a quadrature
    route for any radial profile. Returns (values, error estimate by doubling)."""
    q = np.atleast_1d(np.asarray(q, float))

    def integ(npan):
        r, wr = _nodes(0.0, r_max, npan)
        return jv(l, np.outer(q, r)) @ (wr * np.asarray(f(r), complex) * r)
    v1, v2 = integ(panels), integ(2 * panels)
    return v2, float(np.max(np.abs(v2 - v1)))


# --- Bessel beams ------------------------------------------------------------------------------------------------------
def bessel_beam(l: int, k: float, theta0: float, x, y, z):
    """Scalar Bessel beam J_l(k sin(t0) r) exp(i l phi) exp(i k cos(t0) z): an exact solution of Helmholtz's
    equation (Durnin 1987 for l = 0)."""
    x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
    r = np.hypot(x, y)
    return jv(l, k * math.sin(theta0) * r) * np.exp(1j * (l * np.arctan2(y, x) + k * math.cos(theta0) * z))


def _assemble(F0, F2, F1, l, sigma, x, y):
    """E (3, ...) from the radial functions in the circular basis (see the module's docstring)."""
    ph = np.arctan2(y, x)
    a = F0 * np.exp(1j * l * ph)
    b = F2 * np.exp(1j * (l + 2 * sigma) * ph)
    s2 = math.sqrt(2.0)
    return np.stack([(a + b) / s2, 1j * sigma * (a - b) / s2, F1 * np.exp(1j * (l + sigma) * ph)])


def vector_bessel_beam(l: int, sigma: int, k: float, theta0: float, x, y, z):
    """The vector Bessel beam of helicity sigma (one cone theta = t0 of plane waves (theta^ + i sigma phi^)/sqrt2 with
    the azimuthal factor exp(i (l + sigma) phi_k)): exact solution of Maxwell's equations, H = -i sigma E.
    Returns (E, H), each (3, ...)."""
    if sigma not in (1, -1):
        raise ValueError("sigma = +1 or -1")
    x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
    c, s = math.cos(theta0), math.sin(theta0)
    r = np.hypot(x, y)
    ez = np.exp(1j * k * c * z)
    F0 = 0.5 * (1 + c) * jv(l, k * s * r) * ez
    F2 = 0.5 * (1 - c) * jv(l + 2 * sigma, k * s * r) * ez
    F1 = -(1j ** sigma) / math.sqrt(2.0) * s * jv(l + sigma, k * s * r) * ez
    E = _assemble(F0, F2, F1, l, sigma, x, y)
    return E, -1j * sigma * E


def bessel_per_photon(l: int, sigma: int, theta0: float) -> dict:
    """Closed forms for one cone (Bliokh et al. 2010, Eq. 25): J_z = l + sigma, S_z = sigma cos(t0),
    L_z = l + sigma (1 - cos(t0)) (per photon, units of hbar)."""
    c = math.cos(theta0)
    return {"J": l + sigma, "S": sigma * c, "L": l + sigma * (1 - c)}


# --- exact scalar and vector vortex beams from a spectrum --------------------------------------------------------------
@dataclass
class VortexBeam:
    """A vortex beam of azimuthal order l defined by its order-l spectrum A(q) (``lg_waist_spectrum`` and the like).

    * ``scalar(r, z)``: the exact scalar field (Rayleigh-Sommerfeld for the boundary values on z = 0, including the
      evanescent part for z >= 0 when ``q_max > k``); the factor exp(i l phi) is left out.
    * ``radial(r, z, sigma)``: the radial functions (F0, F2, F1) of the exact vector beam of helicity sigma (propagating
      waves only, q <= k).
    * ``fields(x, y, z)``: E and H of the vector beam sum_s amp[s] E_s (``amp`` maps sigma -> amplitude).
    The integrating methods give an error estimate (doubled panels) on request (``estimate=True``). Every dense
    intermediate (points x quadrature nodes) is sized before it is allocated: beyond ``max_elements`` the call is
    refused with the estimate (``table_cost`` and ``nodes`` give it to a caller beforehand)."""
    l: int
    k: float
    spectrum: Callable
    q_max: float
    amp: dict = field(default_factory=lambda: {1: 1.0})
    max_elements: float = 1e8

    def __post_init__(self):
        for s in self.amp:
            if s not in (1, -1):
                raise ValueError("VortexBeam: helicities are +1 and -1")
        self.theta_max = math.asin(min(1.0, self.q_max / self.k))

    # quadrature nodes over theta (propagating): one panel of 16 Gauss-Legendre nodes per oscillation of J(q r) and of
    # exp(i k cos(theta) z) over [0, theta_max], plus 12 for the spectrum's own shape; ``factor`` multiplies them
    def _prop_panels(self, rmax, zmax, factor=1):
        osc = self.k * (rmax + zmax) * self.theta_max
        return factor * (int(math.ceil(osc / (2 * math.pi))) + 12)

    def _prop_nodes(self, rmax, zmax, factor=1):
        return _nodes(0.0, self.theta_max, self._prop_panels(rmax, zmax, factor))

    def nodes(self, rmax: float, zmax: float, factor: int = 1) -> int:
        """The number of quadrature nodes over theta the integrating methods use for radii up to rmax and depths up
        to |z| = zmax (``factor`` 2: the finer pass of an error estimate)."""
        return 16 * self._prop_panels(float(rmax), float(zmax), factor)

    def table_cost(self, nr: int, rmax: float, zmax: float, nz: int = 1, estimate: bool = True) -> dict:
        """The size of ``table`` for nr radii up to rmax and nz depths up to |z| = zmax, before it is built: the
        quadrature nodes of the finer pass ``nq``, the largest dense matrix (nr x nq Bessel values, float64) in
        elements and bytes, and the number of Bessel evaluations of one helicity (three orders, both passes when
        ``estimate``)."""
        nq = self.nodes(rmax, zmax, 2 if estimate else 1)
        nq1 = self.nodes(rmax, zmax, 1) if estimate else 0
        el = int(nr) * nq
        return {"nq": nq, "elements": el, "bytes": 8 * el + 16 * int(nz) * nq,
                "bessel": 3 * int(nr) * (nq + nq1), "products": 3 * int(nz) * int(nr) * (nq + nq1)}

    def _guard(self, what: str, n_points: int, n_nodes: int):
        if float(n_points) * n_nodes > self.max_elements:
            raise ValueError(f"VortexBeam.{what}: {n_points} points x {n_nodes} quadrature nodes = "
                             f"{float(n_points) * n_nodes:.3g} elements (~{16e-9 * n_points * n_nodes:.3g} GB) > "
                             f"max_elements = {self.max_elements:.3g}: fewer points, a smaller region or a larger budget")

    # the source's power and what the propagating beam keeps ------------------------------------------------------
    def spectrum_power(self, q_lo: float = 0.0, q_hi: float = math.inf, panels: int = 400, weight: Callable | None = None):
        """int_{q_lo}^{q_hi} |A(q)|^2 q dq (the band is cut at q_max), times ``weight(q)`` if given; 2 pi times it is the
        power of the boundary values U0(r) exp(i l phi) carried by that band (Hankel-Parseval: int |U0|^2 dA =
        2 pi int |A|^2 q dq). An unbounded band (a spectrum without cut-off, |A| ~ q^-2 for a spiral plate's singular
        centre) is integrated in s, q = q_lo + k s/(1 - s), s in [0, 1). Composite Gauss-Legendre; returns (value,
        error estimate by doubled panels)."""
        hi = min(q_hi, self.q_max)
        if hi <= q_lo:
            return 0.0, 0.0

        def integ(npan):
            if math.isfinite(hi):
                q, w = _nodes(q_lo, hi, npan)
            else:
                s, ws = _nodes(0.0, 1.0, npan)
                q = q_lo + self.k * s / (1.0 - s)
                w = ws * self.k / (1.0 - s) ** 2
            f = w * np.abs(np.asarray(self.spectrum(q), complex)) ** 2 * q
            return float(np.sum(f * weight(q) if weight is not None else f))
        a, b = integ(panels), integ(2 * panels)
        return b, abs(b - a)

    def evanescent_fraction(self, z: float) -> float:
        """The share of the source's power that its evanescent waves (q > k) still carry at the distance z >= 0 from
        the source plane: int_k |A|^2 exp(-2 sqrt(q^2 - k^2) z) q dq / int_0 |A|^2 q dq (each evanescent plane wave
        decays as exp(-sqrt(q^2 - k^2) z); for z = 0 it is 1 - ``propagating_fraction``). What the propagating vector
        beam lacks there."""
        if self.q_max <= self.k:
            return 0.0
        tot, _ = self.spectrum_power()
        k = self.k
        # in t = sqrt(q^2 - k^2) (q dq = t dt) the integrand is smooth at q = k, where it has a square-root kink in q
        tmax = math.sqrt(self.q_max ** 2 - k * k) if math.isfinite(self.q_max) else math.inf
        if math.isfinite(tmax):
            t, w = _nodes(0.0, tmax, 800)
        else:
            s, ws = _nodes(0.0, 1.0, 800)
            t, w = k * s / (1.0 - s), ws * k / (1.0 - s) ** 2
        A2 = np.abs(np.asarray(self.spectrum(np.sqrt(k * k + t * t)), complex)) ** 2
        return float(np.sum(w * A2 * t * np.exp(-2.0 * t * z))) / tot

    def propagating_fraction(self):
        """The share of the source's power that the propagating beam keeps: int_0^k |A|^2 q dq / int_0^q_max |A|^2 q dq
        (1 for a spectrum that ends below k). 1 - fraction is the evanescent part of the boundary values, which the
        vector beam leaves out; sqrt(1 - fraction) is the L2 distance between the named source and the beam's field on
        z = 0, relative to the source's norm. Returns (fraction, error estimate)."""
        if self.q_max <= self.k:
            return 1.0, 0.0
        tot, et = self.spectrum_power()
        prop, ep = self.spectrum_power(0.0, self.k)
        return prop / tot, (ep + et * prop / tot) / tot

    def energy_per_length(self) -> float:
        """W = int w dA of the vector beam on any plane z: pi sum_s |amp_s|^2 int_0^{theta_max} |A|^2 q dq (Parseval;
        no cross terms between the helicities in |E|^2 + |H|^2)."""
        th, wt = _nodes(0.0, self.theta_max, 400)
        s, c = np.sin(th), np.cos(th)
        a2 = np.abs(np.asarray(self.spectrum(self.k * s), complex)) ** 2 * self.k * self.k * s * c * wt
        return math.pi * float(np.sum(a2)) * sum(abs(a) ** 2 for a in self.amp.values())

    def scalar(self, r, z, evanescent: bool = True, estimate: bool = False):
        """U(r, z) exp(-i l phi) (r, z broadcast); with ``estimate``: (values, error estimate by doubled panels).
        The evanescent part (z >= 0) runs to t = sqrt(q^2 - k^2) <= min(sqrt(q_max^2 - k^2), 46 / z_min): beyond,
        exp(-t z) < 1e-20. For a spectrum without cut-off the node count grows as 1 / z_min: refused beyond
        ``max_elements`` with the estimate."""
        r, z = np.broadcast_arrays(np.atleast_1d(np.asarray(r, float)), np.atleast_1d(np.asarray(z, float)))
        ev = evanescent and self.q_max > self.k
        if ev and np.any(z < 0):
            raise ValueError("VortexBeam.scalar: the evanescent part only for z >= 0")
        zmin = float(np.min(z)) if ev else 0.0
        if ev and not math.isfinite(self.q_max) and zmin <= 0:
            raise ValueError("VortexBeam.scalar: a spectrum without cut-off needs z > 0")
        k = self.k
        rmax, zmax = float(np.max(r)), float(np.max(np.abs(z)))
        tmax = 0.0
        if ev:
            tmax = min(math.sqrt(self.q_max ** 2 - k * k) if math.isfinite(self.q_max) else math.inf,
                       46.0 / zmin if zmin > 0 else math.inf)
        fmax = 2 if estimate else 1
        n_ev = 16 * fmax * (int(math.ceil(tmax * (rmax + 1.0 / k) / (2 * math.pi))) + 24) if ev else 0
        self._guard("scalar", r.size, self.nodes(rmax, zmax, fmax) + n_ev)

        def integ(f):
            th, wt = self._prop_nodes(rmax, zmax, f)
            s, c = np.sin(th), np.cos(th)
            q = k * s
            wq = wt * np.asarray(self.spectrum(q), complex) * k * k * s * c
            val = np.sum(jv(self.l, r[..., None] * q) * np.exp(1j * k * z[..., None] * c) * wq, axis=-1)
            if ev:
                npan = f * (int(math.ceil(tmax * (rmax + 1.0 / k) / (2 * math.pi))) + 24)
                t, wtt = _nodes(0.0, tmax, npan)
                qe = np.sqrt(k * k + t * t)
                we = wtt * np.asarray(self.spectrum(qe), complex) * t
                val = val + np.sum(jv(self.l, r[..., None] * qe) * np.exp(-z[..., None] * t) * we, axis=-1)
            return val
        v = integ(2 if estimate else 1)
        if not estimate:
            return v
        return v, float(np.max(np.abs(v - integ(1))))

    def _radial(self, r, z, sigma, deriv_z, f):
        k, l = self.k, self.l
        self._guard("radial", r.size, self.nodes(float(np.max(r)), float(np.max(np.abs(z))), f))
        th, wt = self._prop_nodes(float(np.max(r)), float(np.max(np.abs(z))), f)
        s, c = np.sin(th), np.cos(th)
        q = k * s
        base = wt * np.asarray(self.spectrum(q), complex) * k * k * s * c
        if deriv_z:
            base = base * 1j * k * c
        ph = np.exp(1j * k * z[..., None] * c)
        rq = r[..., None] * q
        F0 = np.sum(jv(l, rq) * ph * (base * 0.5 * (1 + c)), axis=-1)
        F2 = np.sum(jv(l + 2 * sigma, rq) * ph * (base * 0.5 * (1 - c)), axis=-1)
        F1 = -(1j ** sigma) / math.sqrt(2.0) * np.sum(jv(l + sigma, rq) * ph * (base * s), axis=-1)
        return F0, F2, F1

    def radial(self, r, z, sigma: int = 1, deriv_z: bool = False, estimate: bool = False):
        """(F0, F2, F1) of the vector beam of helicity sigma at (r, z) (broadcast); with ``deriv_z`` their
        z-derivatives (the integrands times i k cos(theta)); with ``estimate``: ((F0, F2, F1), error estimate)."""
        r, z = np.broadcast_arrays(np.atleast_1d(np.asarray(r, float)), np.atleast_1d(np.asarray(z, float)))
        F = self._radial(r, z, sigma, deriv_z, 2 if estimate else 1)
        if not estimate:
            return F
        G = self._radial(r, z, sigma, deriv_z, 1)
        return F, float(max(np.max(np.abs(a - b)) for a, b in zip(F, G)))

    def fields(self, x, y, z, deriv_z: bool = False):
        """(E, H) of the vector beam at the points (x, y, z) (broadcast); each (3, ...)."""
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
        r = np.hypot(x, y)
        E = np.zeros((3,) + x.shape, complex)
        H = np.zeros_like(E)
        for s, a in self.amp.items():
            F0, F2, F1 = self.radial(r.ravel(), z.ravel(), s, deriv_z)
            Es = _assemble(F0.reshape(x.shape), F2.reshape(x.shape), F1.reshape(x.shape), self.l, s, x, y)
            E += a * Es
            H += a * (-1j * s) * Es
        return E, H

    def table(self, r, z, sigma: int = 1, estimate: bool = False):
        """The radial functions on a grid r (nr) x z (nz): array (3, nz, nr) (F0, F2, F1); the Bessel matrices are
        computed once and reused for every z. With ``estimate``: (table, error estimate by doubled panels)."""
        r = np.asarray(r, float)
        z = np.asarray(z, float)
        k, l = self.k, self.l
        self._guard("table", max(r.size, z.size), self.nodes(float(np.max(r)), float(np.max(np.abs(z))),
                                                             2 if estimate else 1))

        def tab(f):
            th, wt = self._prop_nodes(float(np.max(r)), float(np.max(np.abs(z))), f)
            s, c = np.sin(th), np.cos(th)
            q = k * s
            base = wt * np.asarray(self.spectrum(q), complex) * k * k * s * c
            ph = np.exp(1j * np.outer(z, k * c))  # (nz, nq)
            F0 = (ph * (base * 0.5 * (1 + c))) @ jv(l, np.outer(r, q)).T
            F2 = (ph * (base * 0.5 * (1 - c))) @ jv(l + 2 * sigma, np.outer(r, q)).T
            F1 = -(1j ** sigma) / math.sqrt(2.0) * ((ph * (base * s)) @ jv(l + sigma, np.outer(r, q)).T)
            return np.stack([F0, F2, F1])
        T = tab(2 if estimate else 1)
        if not estimate:
            return T
        return T, float(np.max(np.abs(T - tab(1))))

    # closed forms from the spectrum ------------------------------------------------------------------------------
    def moments(self) -> dict:
        """Per-photon values (units of hbar) from the spectrum alone (propagating part), <.> the average over
        |A|^2 q dq:
        * per unit length, the canonical split (Bliokh et al. 2010): J = l + sigma_bar, S = sigma_bar <cos theta>,
          L = J - S; and the Poynting angular momentum J_poynting = J + (sigma_bar/2) <sin^2 theta / cos theta>;
        * through a plane, per photon crossing it: the energy flux over the energy per unit length (<cos theta>), the
          angular-momentum flux over the energy flux times omega (flux_J = J), and Barnett's split of that flux in the
          form of Monteiro et al. 2009, Eq. 33: S_flux = sigma_bar <(1 + cos^2 theta)/2> / <cos theta>,
          L_flux = flux_J - S_flux;
        * W: the energy per unit length (``energy_per_length``).
        sigma_bar = sum sigma |amp_sigma|^2 / sum |amp|^2 (the helicities add without cross terms)."""
        th, wt = _nodes(0.0, self.theta_max, 400)
        s, c = np.sin(th), np.cos(th)
        A2 = np.abs(np.asarray(self.spectrum(self.k * s), complex)) ** 2
        a2 = A2 * s * c * wt
        n2 = {sg: abs(a) ** 2 for sg, a in self.amp.items()}
        tot = sum(n2.values())
        norm = float(np.sum(a2))
        cm = float(np.sum(a2 * c) / norm)
        sin2_over_cos = float(np.sum(A2 * s ** 3 * wt) / norm)  # <sin^2/cos>: the weight's cos cancels
        sbar = sum(sg * v for sg, v in n2.items()) / tot
        J = self.l + sbar
        S = sbar * cm
        S_flux = sbar * float(np.sum(a2 * 0.5 * (1 + c * c)) / norm) / cm
        return {"cos_mean": cm, "J": J, "S": S, "L": J - S, "sigma_mean": sbar,
                "flux_over_energy": cm, "flux_J": J, "S_flux": S_flux, "L_flux": J - S_flux,
                "sin2_over_cos": sin2_over_cos, "J_poynting": J + 0.5 * sbar * sin2_over_cos,
                "W": self.energy_per_length()}


class RadialTable:
    """A beam of order l, E = sum_s amp[s] (e_s e^{i l phi} F0 + e_-s e^{i (l + 2s) phi} F2 + z^ e^{i (l + s) phi} F1)
    (H = -i s E for each helicity), with its radial functions tabulated on r (nr) x z (nz) (``VortexBeam.table``, or a
    paraxial beam's u(r, z) e^{ikz} as F0 with F2 = F1 = 0): the slowly varying envelopes F e^{-ikz} are interpolated
    by bicubic splines and the carrier e^{ikz} is put back exactly. Fast evaluation anywhere in the table's region,
    with an interpolation error that a caller measures against the direct route (``max_error``). When the grid starts
    at r = 0, each function is extended to negative r by its exact parity, F_n(-r) = (-1)^n F_n(r) (a sum of
    J_n(q r): J_n(-x) = (-1)^n J_n(x); n its azimuthal order), so that the spline has no boundary at the axis (with a
    boundary there, v16's l = 0 world erred 4.4e-8 of the peak at r = 1.4 dr against 3.6e-9 on the axis; found while
    processing review B8-beams)."""

    def __init__(self, r, z, k: float, l: int, tables: dict, amp: dict):
        from scipy.interpolate import RectBivariateSpline
        self.r, self.z = np.asarray(r, float), np.asarray(z, float)
        self.k, self.l, self.amp = float(k), int(l), dict(amp)
        carrier = np.exp(-1j * self.k * self.z)[:, None]
        mirror = self.r[0] == 0.0 and len(self.r) > 1
        rs = np.concatenate([-self.r[:0:-1], self.r]) if mirror else self.r
        self.splines = {}
        for s, T in tables.items():
            T = np.asarray(T, complex)
            sp = []
            for c, order in enumerate((self.l, self.l + 2 * s, self.l + s)):
                env = T[c] * carrier
                if mirror:
                    env = np.concatenate([(-1) ** (abs(order) % 2) * env[:, :0:-1], env], axis=1)
                sp.append(None if not np.any(env) else
                          (RectBivariateSpline(self.z, rs, env.real), RectBivariateSpline(self.z, rs, env.imag)))
            self.splines[s] = sp

    def _F(self, s, c, z, r):
        sp = self.splines[s][c]
        if sp is None:
            return np.zeros(np.shape(r), complex)
        return (sp[0].ev(z, r) + 1j * sp[1].ev(z, r)) * np.exp(1j * self.k * z)

    def fields(self, x, y, z):
        """(E, H), each (3, ...), at points inside the table's region (r <= r_max, z within the table)."""
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
        r = np.hypot(x, y)
        E = np.zeros((3,) + x.shape, complex)
        H = np.zeros_like(E)
        for s, a in self.amp.items():
            Es = _assemble(self._F(s, 0, z, r), self._F(s, 1, z, r), self._F(s, 2, z, r), self.l, s, x, y)
            E += a * Es
            H += a * (-1j * s) * Es
        return E, H

    def max_error(self, direct, x, y, z) -> float:
        """Largest |E_table - E_direct| at the points, over the largest |E_direct| there; ``direct(x, y, z) -> E``."""
        E = self.fields(x, y, z)[0]
        D = np.asarray(direct(x, y, z), complex)
        return float(np.max(np.abs(E - D)) / max(np.max(np.abs(D)), 1e-300))


# --- densities of sampled fields -------------------------------------------------------------------------------------
def energy_density(E, H):
    """w = (|E|^2 + |H|^2) / 4 (time-averaged, natural units)."""
    return 0.25 * (np.sum(np.abs(E) ** 2, axis=0) + np.sum(np.abs(H) ** 2, axis=0))


def poynting(E, H):
    """P = Re(E* x H) / 2."""
    return 0.5 * np.real(np.cross(np.conj(E), H, axis=0))


def spin_density(E, H, omega: float):
    """S = Im(E* x E + H* x H) / (4 omega)."""
    return (np.imag(np.cross(np.conj(E), E, axis=0)) + np.imag(np.cross(np.conj(H), H, axis=0))) / (4 * omega)


def orbital_momentum(E, H, gE, gH, omega: float):
    """p_o = Im(sum_i E_i* grad E_i + H_i* grad H_i) / (4 omega); gE, gH: (3 components, 3 directions, ...)."""
    return (np.imag(np.einsum("i...,ij...->j...", np.conj(E), gE))
            + np.imag(np.einsum("i...,ij...->j...", np.conj(H), gH))) / (4 * omega)


def spectral_gradient(F, dx: float, dy: float):
    """(dF/dx, dF/dy) of a field sampled on a periodic grid (last two axes x, y; the field must vanish at the
    window's edges): exact for the band-limited periodic interpolant."""
    nx, ny = F.shape[-2:]
    kx = 2 * math.pi * np.fft.fftfreq(nx, dx)
    ky = 2 * math.pi * np.fft.fftfreq(ny, dy)
    A = np.fft.fft2(F)
    if nx % 2 == 0:
        kx[nx // 2] = 0.0
    if ny % 2 == 0:
        ky[ny // 2] = 0.0
    return (np.fft.ifft2(A * (1j * kx)[:, None]), np.fft.ifft2(A * (1j * ky)[None, :]))


def angular_momentum(x, y, E, H, gE, gH, omega: float) -> dict:
    """Integrals over a transverse plane sampled on the grid x (nx) x y (ny): energy W, canonical L_z, spin S_z,
    Poynting J_z = int (x P_y - y P_x) dA, energy flux int P_z dA, the angular-momentum flux
    int (x (-T_yz) - y (-T_xz)) dA (Maxwell stress) and its spin part in Barnett's separation,
    M_spin = -int Im(E_T* . H_T) dA / (2 omega) (Monteiro et al. 2009, Eq. 33, for each helicity; see the module's
    docstring); per photon: omega L_z / W etc. (per unit length); per photon crossing the plane: omega M / Phi
    (flux_J), omega M_spin / Phi (flux_S), their difference (flux_L)."""
    X, Y = np.meshgrid(x, y, indexing="ij")
    dA = float((x[1] - x[0]) * (y[1] - y[0]))
    w = energy_density(E, H)
    P = poynting(E, H)
    S = spin_density(E, H, omega)
    po = orbital_momentum(E, H, gE, gH, omega)
    W = float(np.sum(w)) * dA
    Lz = float(np.sum(X * po[1] - Y * po[0])) * dA
    Sz = float(np.sum(S[2])) * dA
    Jp = float(np.sum(X * P[1] - Y * P[0])) * dA
    flux = float(np.sum(P[2])) * dA
    Txz = 0.5 * np.real(E[0] * np.conj(E[2]) + H[0] * np.conj(H[2]))
    Tyz = 0.5 * np.real(E[1] * np.conj(E[2]) + H[1] * np.conj(H[2]))
    M = float(np.sum(X * (-Tyz) - Y * (-Txz))) * dA
    Ms = -float(np.sum(np.imag(np.conj(E[0]) * H[0] + np.conj(E[1]) * H[1]))) * dA / (2 * omega)
    return {"W": W, "Lz": Lz, "Sz": Sz, "J_poynting": Jp, "flux": flux, "M": M, "M_spin": Ms,
            "L": omega * Lz / W, "S": omega * Sz / W, "J": omega * (Lz + Sz) / W, "J_poynting_per_photon": omega * Jp / W,
            "flux_over_energy": flux / W, "flux_J": omega * M / flux, "flux_S": omega * Ms / flux,
            "flux_L": omega * (M - Ms) / flux, "rS": float(np.sum(X * S[0] + Y * S[1])) * dA}


def scalar_oam_per_photon(U, x, y) -> float:
    """int Im(U* (x d/dy - y d/dx) U) dA / int |U|^2 dA for a scalar field sampled on a grid (spectral derivatives):
    the orbital angular momentum per photon in units of hbar."""
    dx, dy = float(x[1] - x[0]), float(y[1] - y[0])
    gx, gy = spectral_gradient(U, dx, dy)
    X, Y = np.meshgrid(x, y, indexing="ij")
    return float(np.sum(np.imag(np.conj(U) * (X * gy - Y * gx))) / np.sum(np.abs(U) ** 2))


# --- topological charge ------------------------------------------------------------------------------------------------
def _wrap(a):
    return (np.asarray(a) + math.pi) % (2 * math.pi) - math.pi


def winding(values) -> float:
    """sum of the wrapped phase differences along a closed loop (values in order; the loop closes back to the first)
    / 2 pi. Exact while each step changes the phase by less than pi."""
    v = np.asarray(values, complex)
    ph = np.angle(v)
    return float(np.sum(_wrap(np.diff(np.append(ph, ph[0])))) / (2 * math.pi))


def charge_on_circle(fn: Callable, x0: float, y0: float, radius: float, n: int = 720) -> float:
    """Winding of fn(x, y) (complex, vectorised) along the circle of the given centre and radius."""
    a = 2 * math.pi * np.arange(n) / n
    return winding(fn(x0 + radius * np.cos(a), y0 + radius * np.sin(a)))


def plaquette_charges(U) -> np.ndarray:
    """Integer charges of the cells of a sampled field (axes x, y): the winding around each 2 x 2 cell,
    counter-clockwise in (x, y)."""
    ph = np.angle(np.asarray(U, complex))
    a, b, c, d = ph[:-1, :-1], ph[1:, :-1], ph[1:, 1:], ph[:-1, 1:]
    s = _wrap(b - a) + _wrap(c - b) + _wrap(d - c) + _wrap(a - d)
    return np.rint(s / (2 * math.pi)).astype(int)


def charge_in_disc(U, x, y, x0: float, y0: float, radius: float) -> int:
    """Total charge of the cells whose centres lie within the disc: the winding along the boundary of their union."""
    q = plaquette_charges(U)
    xc, yc = 0.5 * (x[:-1] + x[1:]), 0.5 * (y[:-1] + y[1:])
    X, Y = np.meshgrid(xc, yc, indexing="ij")
    return int(np.sum(q[(X - x0) ** 2 + (Y - y0) ** 2 <= radius * radius]))


# --- flow lines ---------------------------------------------------------------------------------------------------------
def trace_lines(current: Callable, starts, z_end: float, steps: int):
    """Lines of a current j(x, y, z) -> (3, n) (vectorised over n points) from ``starts`` (n x 3) to z = z_end, in
    ``steps`` equal steps of z by classical RK4 on dx/dz = j_x / j_z, dy/dz = j_y / j_z. Returns (n, steps + 1, 3)."""
    p = np.array(starts, float)
    z0 = p[:, 2].copy()
    if not np.allclose(z0, z0[0]):
        raise ValueError("trace_lines: all lines start on one plane z")
    h = (z_end - z0[0]) / steps
    out = np.empty((len(p), steps + 1, 3))
    out[:, 0] = p

    def f(xy, z):
        j = current(xy[:, 0], xy[:, 1], np.full(len(xy), z))
        return np.stack([j[0] / j[2], j[1] / j[2]], axis=1)
    xy, z = p[:, :2].copy(), z0[0]
    for i in range(steps):
        k1 = f(xy, z)
        k2 = f(xy + 0.5 * h * k1, z + 0.5 * h)
        k3 = f(xy + 0.5 * h * k2, z + 0.5 * h)
        k4 = f(xy + h * k3, z + h)
        xy = xy + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        z = z + h
        out[:, i + 1, :2] = xy
        out[:, i + 1, 2] = z
    return out


# --- equiphase surfaces ------------------------------------------------------------------------------------------------
def phase_crossings(G, periodic: bool = True):
    """Where arg G passes through 0 between neighbouring samples of the last axis: (hit mask, fraction f in (0, 1] of
    the step at which it does, sense +-1). A zero is counted once: the sign of the phase (negative / not negative)
    changes between the two samples and the phase does not jump across the branch cut (|difference| < pi)."""
    ph = np.angle(np.asarray(G, complex))
    nxt = np.roll(ph, -1, axis=-1) if periodic else ph[..., 1:]
    cur = ph if periodic else ph[..., :-1]
    raw = nxt - cur
    hit = ((cur < 0) != (nxt < 0)) & (np.abs(raw) < math.pi)
    with np.errstate(divide="ignore", invalid="ignore"):
        f = np.where(hit, -cur / np.where(hit, raw, 1.0), 0.0)
    return hit, f, np.sign(raw).astype(int)


def isophase_sheets(G, coords: Callable, periodic: bool = True, min_amp: float = 0.0):
    """The surfaces arg G = 0 of a field sampled on a grid (n1, n2, n3) (for arg U = Phi0 pass G = U exp(-i Phi0)):
    crossings along the third axis (``phase_crossings``, periodic or not), joined across neighbouring (i1, i2) into
    quads of two triangles where the crossings of the four corners match (the nearest crossing of the same sense,
    closer than half the mean spacing of the crossings there). ``coords(i1, i2, s3)`` maps integer indices and
    fractional positions s3 along axis 3 to points (..., 3). Crossings where |G| < min_amp are left out (near zeros the
    phase is undefined). Returns (pos (n, 3), triangles (m, 3) int)."""
    G = np.asarray(G, complex)
    n1, n2, n3 = G.shape
    amp = np.abs(G)
    hit, f, d = phase_crossings(G, periodic)
    a_cur = amp if periodic else amp[:, :, :-1]
    a_nxt = np.roll(amp, -1, axis=2) if periodic else amp[:, :, 1:]
    hit &= (a_cur > min_amp) & (a_nxt > min_amp)
    i1, i2, i3 = np.nonzero(hit)
    s3 = i3 + f[i1, i2, i3]
    sense = np.sign(d[i1, i2, i3]).astype(int)
    pos = coords(i1, i2, s3) if len(i1) else np.zeros((0, 3))
    # per cell (i1, i2): its crossings as (s3, sense, vertex index)
    cells = {}
    for v, (a, b, s, sg) in enumerate(zip(i1, i2, s3, sense)):
        cells.setdefault((int(a), int(b)), []).append((float(s), int(sg), v))

    def match(s, sg, lst):
        best, bd = None, n3 / (2.0 * len(lst))  # closer than half the mean spacing of that cell's crossings
        for s2, sg2, v2 in lst:
            if sg2 != sg:
                continue
            dd = abs(s2 - s)
            if periodic:
                dd = min(dd, n3 - dd)
            if dd < bd:
                best, bd = v2, dd
        return best
    tris = []
    for (a, b), lst in cells.items():
        right, up, diag = cells.get((a + 1, b)), cells.get((a, b + 1)), cells.get((a + 1, b + 1))
        if not (right and up and diag):
            continue
        for s, sg, v in lst:
            vr, vu, vd = match(s, sg, right), match(s, sg, up), match(s, sg, diag)
            if vr is None or vu is None or vd is None:
                continue
            tris.append((v, vr, vd))
            tris.append((v, vd, vu))
    return np.asarray(pos, float).reshape(-1, 3), np.asarray(tris, int).reshape(-1, 3)


def cylinder_coords(r, phi, z):
    """``coords`` for a field sampled on (z, r, phi) (axes in that order, phi the crossing axis, periodic)."""
    r, phi, z = np.asarray(r, float), np.asarray(phi, float), np.asarray(z, float)
    dphi = float(phi[1] - phi[0])

    def fn(iz, ir, s):
        ang = phi[0] + s * dphi
        rr = r[ir]
        return np.stack([rr * np.cos(ang), rr * np.sin(ang), z[iz]], axis=-1)
    return fn
