# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The homogeneous isotropic universe of general relativity (Friedmann-Lemaitre-Robertson-Walker background, plan
item P8): the expansion rate, the density parameters, distances, times and the scale factor a(t) of a universe of
photons, neutrinos (massless or massive), pressureless matter, curvature and a cosmological constant (or a dark-energy
component supplied by a model outside the core, ``lfphys.theories.models.dark_energy``).

Equations (G = c = 1 inside the brackets; H0 the Hubble constant today, a = 1/(1 + z) the scale factor):

    (Friedmann)      H^2 = H0^2 E^2(a),   E^2 = S(a) / a^4,
                     S(a) = O_r + O_cb a + O_k a^2 + O_L a^4 g(a) + sum_i O_nu F(y_i a),
    (acceleration)   a''/a = -(H0^2 / 2) sum_j rho_j (1 + 3 w_j) / rho_c0,

with O_r the radiation that stays relativistic (photons, massless neutrinos, any extra radiation O_r_extra), O_cb
cold dark matter + baryons, O_k = -k c^2/(a0 H0)^2 the curvature, O_L the cosmological constant (g = 1) or the
dark energy today (g(a) = rho_de(a)/rho_de(1) of the model), and one term per massive neutrino species.
Closure: S(1) = 1 (the sum of today's density parameters is one; O_L or O_k follows from the others).

Radiation. Photons: rho_gamma c^2 = a_rad T^4, a_rad = 4 sigma_SB / c = pi^2 k^4 / (15 hbar^3 c^3) (CODATA through
scipy.constants), T = T_cmb / a. Neutrinos: N_eff counts their density while relativistic (Planck 2018 Eq. (64):
rho_rad = N_eff (7/8)(4/11)^(4/3) rho_gamma). Each massive species (of n_nu, default three) is a Fermi-Dirac gas of
particles and antiparticles (g = 2) of its physical mass m at the temperature T_nu = (N_std/n_nu)^(1/4) (4/11)^(1/3)
T_cmb / a, i.e. it carries N_std/n_nu of a massless species' density while relativistic, with N_std = 3.046 the
standard heating; the rest of N_eff, N_eff - n_massive N_std/n_nu, is massless (so an excess over N_std is extra
radiation that does not heat the neutrinos). This is the split of CAMB/CosmoMC behind Planck 2018 for any N_eff
(CosmoMC: "P%share_delta_neff = .false.", CAMB_SetNeutrinoHierarchy: massive degeneracy num_massive default_nnu/3,
CosmoMC's omega_nu = sum m / 94.07 eV x (3.046/3)^(3/4), "we are using interpretation where there are
degeneracy_factor neutrinos, each exactly thermal"; sources/verification_2026-11-04_p8_flrw.md §2; review B7-flrw C7);
``N_std=None`` shares N_eff equally among the n_nu species instead (the massive ones then heated with any excess).
A massive species has, with F the function of Komatsu et al. 2011, Eq. (25), and J its pressure analogue,

    rho_nu = (7/8)(4/11)^(4/3) (N_std/n_nu) rho_gamma F(y),   y = m c^2 / (k T_nu),
    F(y) = (120 / (7 pi^4)) int_0^inf x^2 sqrt(x^2 + y^2) / (e^x + 1) dx,
    P_nu = (7/8)(4/11)^(4/3) (N_std/n_nu) rho_gamma c^2 J(y),  J(y) = (40 / (7 pi^4)) int_0^inf x^4 / sqrt(x^2+y^2)
                                                                       / (e^x + 1) dx,

computed by quadrature (composite Gauss-Legendre, 50 panels x 16 nodes on [0, 64]: geometric panels toward x = 0 so
that the branch points x = +-iy stay at three half-widths from every panel for any y; measured relative error below
2e-15 against 40-digit mpmath for y from 0 to 1e8, tests). Limits: F = 1 + 5y^2/(7 pi^2) + O(y^4 ln y) for y -> 0;
F -> (180 zeta(3) / (7 pi^4)) y (1 + (15 zeta(5) / (2 zeta(3))) / y^2 + ...) for y -> inf (the number density times
m, plus the kinetic energy; the limits as Komatsu et al. give them). The temperature scaling is CAMB's: Komatsu et al.
(Eq. (24), "rho_nu(a) = 0.2271 Neff rho_gamma(a) f(m_nu a/T_nu0)" with "T_nu0 = (4/11)^1/3 T_cmb = 1.945 K") multiply
the density at the unscaled temperature by N_eff/3 instead, Astropy's convention (omega_nu of a 0.06 eV species 0.38 %
above the engine's). Planck's printed numbers cannot tell these apart, nor Mangano et al. 2005's sum m / 93.14 eV:
Omega_m h^2 confirms that one 0.06 eV species is counted in Omega_m, not how (tests; the engine's formula is pinned by
the test of omega_nu against m n_nu). Against the computed physics: with the spectral distortions of incomplete
decoupling, Mangano et al. 2005 (Eq. (14)) find Omega_nu h^2 = sum m / 93.14 eV at T_0 = 2.725 K (93.09 eV at 2.7255 K,
scaled by T_0^3); the thermal proxy gives 92.99 eV, i.e. omega_nu 0.10 % too large for a given sum m (Astropy's 0.48 %).
The current standard value is N_eff = 3.0440 (Froustey, Pitrou & Volpe 2020: "Neff = 3.0440 with at least 10^-4
precision"); 3.046 is the value of Planck 2018 and its CAMB.

Distances (Hogg 1999, Eqs. (15), (16), (18), (21), (25)), with D_H = c/H0:
    D_C(z) = D_H int_a^1 da / sqrt(S(a)),  D_M = D_H sinn(sqrt(|O_k|) D_C/D_H)/sqrt(|O_k|) (sinh for O_k > 0, sin
    for O_k < 0), D_A = D_M/(1+z), D_L = (1+z) D_M, mu = 5 log10(D_L / 10 pc);
    between two redshifts D_A(z1, z2) = sinn(chi_2 - chi_1)/(1 + z2) in the same units (Carroll 2001, Eq. (42); valid
    for either sign of O_k, unlike Hogg's Eq. (19); Carroll's sentence after Eq. (42) gives sinh "when Omega_k0 < 0",
    a slip against his own Eqs. (23), (29), which give Hogg's sign).
Times: t(a) = (1/H0) int_0^a a' da'/sqrt(S(a')) (cosmic time since the big bang), the lookback time t(1) - t(a),
conformal time eta(a) = (1/H0) int_0^a da'/sqrt(S); the comoving particle horizon c eta; the sound horizon of the
photon-baryon fluid r_s(a) = (c/H0) int_0^a c_s da'/sqrt(S), c_s = 1/sqrt(3(1 + R)), R = 3 rho_b / (4 rho_gamma)
(Eisenstein & Hu 1998, Eq. (5); CAMB's dsound_da_exact). a(t): the inverse of t(a) by safeguarded Newton steps with
the exact derivative dt/da = 1/(a H); a second, independent route integrates the acceleration equation (with the
pressures of all components) as an ODE (``scale_factor_ode``).

Numerics. S is never formed where it would over- or underflow: every term is divided by a^q, q the power of the
term largest at a (4 where Lambda dominates: O_L a^4 alone overflows binary64 beyond a ~ 1e77; review B7-flrw C1),
and the integrands are written with the matching powers of a, so that a from ~1e-300 to ~1e300 is covered. The
integrals from the big bang (age, conformal time, particle horizon, sound horizon) are computed for a <= 4 in s with
xi = sqrt(a) = s^k and for a > 4 in xi = 2 + ln(a/4). Near a = 0, S = c a^p (1 + ...) and the integrand in xi is a
power 2 xi^alpha; k = (m + 1)/(1 + alpha), m = ceil(1 + alpha) - 1, makes its leading term the polynomial 2 k s^m
(k = 1 for radiation, matter, curvature and Lambda; k > 1 for a dark energy that dominates at the big bang, whose
alpha lies in (-1, 0): C3). The integrals from today (comoving distance, lookback time, time since today) are computed
in s = ln(1 + z), from z by log1p so that a small z keeps its relative accuracy. Both by adaptive bisection of
composite 16-point Gauss-Legendre panels: a panel is accepted when its value and the sum of its halves differ by at
most rtol (default 1e-13) times the larger of the halves' value and the segment's value per width (or by less than
their rounding: the noise floor; the panel at s = 0 once the difference is below rtol/10 of the segment). The error
returned (``with_error=True``) adds (i) these differences (an overestimate of the error of the accepted halves when
the integrand is smooth or a power s^beta, beta >= 0, at the panel's end: the substitution ensures that), (ii) a
first-order bound of the rounding of every integrand value (S summed from terms of either sign: 10u sum|terms| / S,
plus the stated error of the neutrino quadrature and of a dark-energy term formed through logarithms) and of the
quadrature sums, (iii) the compensated (Neumaier) sum over segments. Measured against closed forms and 30-digit mpmath
(tests; review B7-flrw r02 rerun): the estimate is never smaller than the actual error; away from turnarounds,
bounces and loitering it is below 1e-12 relative and the actual error below 2e-13; near them the conditioning of
a -> integral dominates (closed dust at 1 - a/a_max = 1e-12: actual 1.4e-10, estimate 4.0e-9; a loitering universe
1e-9 from critical: actual 1.5e-10, estimate 8.9e-8 to 2.1e-7) and the estimate grows with it, remaining an upper
bound (C9). Near a turnaround or a bounce (S = 0 at a = a_r) the time is integrated in w = sqrt(|1 - a/a_r|) with S
written as (a - a_r) times its divided difference, and the changes of a dark-energy or neutrino term from a_r as
integrals of their derivatives, so that the root lies exactly at a_r and S keeps its relative accuracy there (found
while processing C2). a(t) inverts t(a) to |delta ln a| <= 4u max(1, |ln a|)
on top of the conditioning E(a) (delta t H0 + 4u t H0): its relative error is about E t H0 u (4.7e-14 at 5000 Gyr for
Planck 2018) plus E times the time integral's error; beyond a = 1e300 it is inf (with a warning).

Scope: the homogeneous background only (no perturbations, no recombination: z_*, z_drag are inputs); dark energy
other than Lambda only through a model object (``dark_energy=``) from outside the core. Lambda-CDM is the standard
model; its known tensions are stated, not resolved, here: Planck 2018 VI (abstract) finds its H0 "in significant,
3.6 sigma, tension with local measurements of the Hubble constant", and DESI DR2 BAO with the CMB prefers w0 > -1,
wa < 0 at 3.1 sigma (2.8-4.2 sigma with supernovae; the w0-wa model in theories.models.dark_energy) (C12).
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from scipy import constants as sc
from scipy import integrate, optimize

from ..constants import C, G, YEAR_JULIAN

ABOUT = {
    "layer": "core", "kind": "law",
    "title": "Однородная изотропная вселенная (ФЛРУ): H(z), расстояния, возрасты, a(t)",
    "statement": "Уравнения Фридмана ОТО для фотонов (из T_CMB), нейтрино (N_eff; массивные — точный интеграл "
                 "Ферми–Дирака для плотности и давления), пылевидной материи, кривизны и космологической постоянной: "
                 "E(z), H(z), параметры плотности и параметр замедления при z; сопутствующее, поперечное, угловое и "
                 "фотометрическое расстояния, модуль расстояния; время назад, возраст, конформное время, горизонт "
                 "частиц, звуковой горизонт; a(t) обращением t(a) и вторым путём — интегрированием уравнения "
                 "ускорения; критическая плотность; параметры Planck 2018 как данные.",
    "validity": "однородный фон без возмущений (рекомбинация не считается: z_*, z_drag — входные данные); "
                "нейтрино — тепловые: массивный вид — газ Ферми–Дирака физической массы при температуре "
                "(N_std/n)^(1/4)(4/11)^(1/3) T, N_std = 3.046 (стандартный нагрев), остаток N_eff — безмассовый "
                "(разбиение CAMB/CosmoMC, по которому считался Planck 2018, при любом N_eff); спектральные "
                "искажения неполного расцепления не учитываются: ω_ν на 0.10 % больше, чем у Mangano et al. 2005 "
                "(Σm/93.14 эВ при 2.725 K, 93.09 эВ при 2.7255 K; у тепловой модели 92.99 эВ), а современное "
                "N_eff = 3.0440 (Froustey et al. 2020); "
                "интегралы — с оценкой погрешности, возвращаемой вместе со значением (запрос rtol = 1e-13 по "
                "умолчанию); вдали от точек поворота, отскока и зависания оценка ≤ 1e-12 относительной, "
                "фактическая ошибка против замкнутых форм и mpmath ≤ 2e-13 (измерено); вблизи них ошибка "
                "определяется обусловленностью и оценка растёт вместе с ней, оставаясь верхней границей; "
                "a(t) — относительная ошибка ≈ E·t·H0·u плюс E·(ошибка интеграла времени), a от ~1e-300 до "
                "~1e300 (дальше — inf с предупреждением); тёмная энергия, отличная от Λ, — только через модель "
                "вне ядра (theories.models.dark_energy); ΛCDM — стандартная модель с известными напряжениями: H0 "
                "Planck 2018 против локальных измерений (3.6σ в аннотации статьи), DESI DR2 BAO + CMB предпочитает "
                "w0 > −1, wa < 0 на 3.1σ (2.8–4.2σ со сверхновыми) — не опровержение Λ",
    "basis": ["Friedmann 1922, 1924; Lemaître 1927; Robertson 1935; Walker 1937 (ОТО)",
              "Hogg, arXiv:astro-ph/9905116 (1999), Eqs. (14)-(21), (25), (30)",
              "Carroll, Living Rev. Relativ. 4, 1 (2001), Eqs. (21), (36), (42)",
              "Komatsu et al., ApJS 192, 18 (2011), Eqs. (21)-(25): F(y) and its limits",
              "CAMB Aug 2017 / CosmoMC Jul 2018 (the codes behind Planck 2018): the neutrino temperature and N_eff "
              "split",
              "Mangano et al., Nucl. Phys. B 729, 221 (2005), Eq. (14); Froustey, Pitrou & Volpe, JCAP 12 (2020) 015 "
              "(validity)",
              "Eisenstein & Hu, ApJ 496, 605 (1998), Eqs. (5), (6)",
              "Planck Collaboration, A&A 641, A6 (2020): Tables 1, 2; Eq. (64); abstract (H0 tension)",
              "DESI Collaboration, Phys. Rev. D 112, 083515 (2025), abstract (validity)",
              "Fixsen, ApJ 707, 916 (2009): T_CMB"],
    "conflicts": [],
}

# --- units --------------------------------------------------------------------------------------------------------
C_KM_S = C / 1e3                                   # km/s, exact
PARSEC_M = sc.parsec                               # (648000/pi) au, au exact (IAU 2012 B2)
MPC_M = 1e6 * PARSEC_M
MPC_KM = MPC_M / 1e3
# Julian gigayear, as CAMB >= 1.4. The CAMB of Planck 2018 (Aug/Sept 2017) used Gyr = 3.1556926e16 s and Mpc =
# 3.085678e22 m: its ages are 2.15e-5 larger in number (review B7-flrw C4; tests/test_flrw.py::_camb17).
GYR_S = 1e9 * YEAR_JULIAN
A_RAD = 4.0 * sc.Stefan_Boltzmann / C              # J m^-3 K^-4
K_B_EV = sc.k / sc.e                               # eV/K (exact in the SI)
NU_FACTOR = 7.0 / 8.0 * (4.0 / 11.0) ** (4.0 / 3.0)
T_NU_RATIO = (4.0 / 11.0) ** (1.0 / 3.0)
ZETA3 = 1.2020569031595942853997
ZETA5 = 1.0369277551433699263314
_A_NR = 180.0 * ZETA3 / (7.0 * math.pi ** 4)        # F(y) -> A y for y -> inf (Komatsu et al. 2011)

_U = 2.0 ** -53

# --- Fermi-Dirac integrals of a thermal neutrino species ------------------------------------------------------------
_GL_T, _GL_W = np.polynomial.legendre.leggauss(16)


def _fd_nodes():
    """Composite Gauss-Legendre nodes on [0, 64]: [0, 2^-20], geometric panels [2^-k-1, 2^-k] (k = 19 ... 0), unit
    panels up to 8, width 2 up to 40, width 4 up to 64. For every panel the singularities of x^2 sqrt(x^2 + y^2)/
    (e^x + 1) (branch points +-iy, poles i pi (2n+1)) lie outside the Bernstein ellipse of parameter 3 + sqrt(8),
    except for [0, 2^-20], whose whole contribution is below 2^-60 / 6 of the integral, and the last panels (poles
    at i pi with half-width 2; their contribution is below e^-40)."""
    edges = ([0.0] + [2.0 ** -k for k in range(20, 0, -1)] + [float(v) for v in range(1, 9)]
             + [float(v) for v in range(10, 41, 2)] + [float(v) for v in range(44, 65, 4)])
    e = np.array(edges)
    mid, half = 0.5 * (e[1:] + e[:-1]), 0.5 * (e[1:] - e[:-1])
    x = (mid[:, None] + half[:, None] * _GL_T).ravel()
    w = (half[:, None] * _GL_W).ravel()
    return x, w


_FD_X, _FD_W = _fd_nodes()
_FD_WOCC = _FD_W * _FD_X ** 2 / (np.exp(_FD_X) + 1.0)
_FD_I0 = float(np.sum(_FD_WOCC * _FD_X))          # = 7 pi^4 / 120 to 2e-16 (tests); F(0) = 1 exactly
FD_REL_ERROR = 4e-15                               # stated bound of F and J (measured < 2e-15, tests)


def _fd_sums(y):
    """(F(y), J(y)) of ``fermi_dirac_energy`` and ``fermi_dirac_pressure`` for y >= 0 of any shape."""
    y = np.asarray(y, dtype=float)
    flat = np.abs(y.ravel())
    F = np.empty_like(flat)
    J = np.empty_like(flat)
    step = 2048
    for s in range(0, flat.size, step):
        h = np.hypot(_FD_X[None, :], flat[s:s + step, None])
        F[s:s + step] = np.sum(_FD_WOCC * h, axis=1)
        J[s:s + step] = np.sum(_FD_WOCC * _FD_X ** 2 / h, axis=1)
    return (F / _FD_I0).reshape(y.shape), (J / (3.0 * _FD_I0)).reshape(y.shape)


def _fd_dsums(z):
    """F'(z) = dF/dz of ``fermi_dirac_energy`` for z >= 0 of any shape (the same nodes: (120/(7 pi^4)) int x^2 z /
    sqrt(x^2 + z^2) / (e^x + 1) dx)."""
    z = np.asarray(z, dtype=float)
    flat = np.abs(z.ravel())
    out = np.empty_like(flat)
    step = 2048
    for s in range(0, flat.size, step):
        zz = flat[s:s + step, None]
        out[s:s + step] = np.sum(_FD_WOCC * zz / np.hypot(_FD_X[None, :], zz), axis=1)
    return (out / _FD_I0).reshape(z.shape)


def fermi_dirac_energy(y):
    """F(y) = rho(m)/rho(m = 0) of a thermal Fermi-Dirac species at the same temperature, y = m c^2/(k T)
    (Komatsu et al. 2011, Eq. (25)); F(0) = 1. Relative error below ``FD_REL_ERROR``."""
    F, _ = _fd_sums(y)
    return float(F) if np.ndim(F) == 0 else F


def fermi_dirac_pressure(y):
    """P(m) c^-2 / rho(m = 0) of the same species: (40/(7 pi^4)) int x^4/sqrt(x^2+y^2)/(e^x+1) dx; 1/3 at y = 0,
    (5 zeta(5)/zeta(3)) F / y^2 for y -> inf. The equation of state is w = this / F."""
    _, J = _fd_sums(y)
    return float(J) if np.ndim(J) == 0 else J


# --- the integration machinery -------------------------------------------------------------------------------------
_MAX_DEPTH = 200


def _gl(f, a, b):
    mid, half = 0.5 * (a + b), 0.5 * (b - a)
    x = mid[:, None] + half[:, None] * _GL_T
    v, r = f(x)
    wv = half[:, None] * _GL_W * v
    # the rounding of the sums; 1e-300 per panel covers values near the subnormal range
    return wv.sum(axis=1), (np.abs(wv) * (r + 20.0 * _U)).sum(axis=1) + 1e-300


def _adaptive(f, lo, hi, rtol):
    """int_lo^hi f for segments lo_i < hi_i: (value, quadrature error estimate, rounding bound) per segment.

    A panel is accepted when |Q(panel) - Q(left) - Q(right)| <= rtol max(|Q(halves)|, |Q(segment)| width/segment
    width), or when that difference is within twice the rounding bound of the three sums (the noise floor: near a
    root of S the integrand's own rounding, not the rule, limits the accuracy; the bound is then part of the error
    returned), or, for the panel at x = 0, when it is below rtol/10 of the segment's value. The difference is an
    upper bound of the halves' error only where the integrand is smooth or behaves as x^beta with beta >= 0 at x = 0
    (the error left after a halving is then 1/(2^(1+beta) - 1) <= 1 times the difference); the callers ensure that
    (the substitution of ``Background._bang_segments``; review B7-flrw C3)."""
    n = lo.size
    val, eq, er, cnt = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    if n == 0:
        return val, eq, er
    width = hi - lo
    q0, r0 = _gl(f, lo, hi)
    scale = np.abs(q0)
    a, b, seg, qw, rw = lo.copy(), hi.copy(), np.arange(n), q0, r0
    for depth in range(_MAX_DEPTH):
        m = 0.5 * (a + b)
        k = a.size
        q, r = _gl(f, np.concatenate([a, m]), np.concatenate([m, b]))
        qh, rh = q[:k] + q[k:], r[:k] + r[k:]
        if np.any(np.isnan(qh)):
            raise FloatingPointError("integrand not defined (E^2 <= 0 inside the range?)")
        with np.errstate(invalid="ignore"):
            d = np.abs(qh - qw)
        ok = (d <= rtol * np.maximum(np.abs(qh), scale[seg] * (b - a) / width[seg])) | (d <= 2.0 * (rh + rw))
        ok |= np.isinf(qh)       # an integrand beyond binary64 (e.g. t ~ a^1.5 of a dust universe at a ~ 1e300)
        # the panel at x = 0 (the big bang), where the integrand may be a non-integer power x^beta (beta >= 0 after
        # the caller's substitution): accepted once its error is below rtol/10 of the segment
        ok |= (a == 0.0) & (d <= 0.1 * rtol * scale[seg])
        if depth == _MAX_DEPTH - 1 and not ok.all():
            warnings.warn("flrw: adaptive quadrature did not reach rtol on every panel; the returned error "
                          "estimate includes the remainder", RuntimeWarning, stacklevel=3)
            ok[:] = True
        np.add.at(val, seg[ok], qh[ok])
        np.add.at(eq, seg[ok], d[ok])
        np.add.at(er, seg[ok], rh[ok])
        np.add.at(cnt, seg[ok], 1.0)
        keep = ~ok
        if not keep.any():
            break
        a, b = np.concatenate([a[keep], m[keep]]), np.concatenate([m[keep], b[keep]])
        seg = np.concatenate([seg[keep], seg[keep]])
        qw = np.concatenate([q[:k][keep], q[k:][keep]])
        rw = np.concatenate([r[:k][keep], r[k:][keep]])
    er += cnt * _U * np.abs(val)
    return val, eq, er


def _prefix(vals):
    """Prefix sums by Neumaier's compensated summation (error 2u |s_k| + O(n u^2) sum |v|)."""
    out = np.empty(len(vals))
    s = c = 0.0
    for i, v in enumerate(np.asarray(vals, float).tolist()):
        t = s + v
        c += (s - t) + v if abs(s) >= abs(v) else (v - t) + s
        s = t
        out[i] = s + c
    return out


def _xi_of_a(a):
    a = np.asarray(a, float)
    return np.where(a <= 4.0, np.sqrt(np.minimum(a, 4.0)), 2.0 + np.log(np.maximum(a, 4.0) / 4.0))


def _a_of_xi(xi):
    return np.where(xi <= 2.0, xi * xi, 4.0 * np.exp(np.maximum(xi, 2.0) - 2.0))


def _dadxi(xi, a):
    return np.where(xi <= 2.0, 2.0 * xi, a)


def _scalar_or_array(v, like):
    v = np.asarray(v).reshape(np.shape(like))
    return float(v) if v.ndim == 0 else v


# --- the background -------------------------------------------------------------------------------------------------
class Background:
    """An FLRW universe. Parameters (today's density parameters O_x = rho_x / rho_crit, rho_crit = 3 H0^2/(8 pi G)):

    H0      Hubble constant, km/s/Mpc.
    Om      cold dark matter + baryons (dust); massive neutrinos are not included (``Om_total`` includes them, as
            Planck's Omega_m does).
    Ok, OL  curvature and cosmological constant (or the dark energy of ``dark_energy``); give at most one of them,
            the other follows from closure (both None: flat).
    T_cmb   photon temperature today, K (0: no photons and no neutrinos).
    N_eff   effective number of relativistic neutrino species (needs T_cmb > 0): rho_rad,nu = N_eff (7/8)(4/11)^(4/3)
            rho_gamma while all are relativistic (Planck 2018 Eq. (64)).
    m_nu    masses of the massive species, eV (at most n_nu; the others are massless).
    N_std   how N_eff is split (review B7-flrw C7). A number (default 3.046): the N_eff of the n_nu standard
            neutrinos, whose heating each massive species shares - it carries N_std/n_nu of a massless species'
            density while relativistic, i.e. it is a Fermi-Dirac gas of the physical mass at (N_std/n_nu)^(1/4)
            (4/11)^(1/3) T_cmb - and the rest of N_eff, N_eff - n_massive N_std/n_nu, is massless (an excess over
            N_std is extra radiation that does not heat the neutrinos; if N_eff < n_massive N_std/n_nu the massive
            species share N_eff and nothing is massless). This is the split of CAMB/CosmoMC behind Planck 2018
            (CosmoMC sets share_delta_neff = .false. and calls CAMB_SetNeutrinoHierarchy, whose massive degeneracy is
            num_massive default_nnu/3 with default_nnu = 3.046; CAMB >= 1.4 uses 3.044). None: N_eff shared equally
            by the n_nu species (the massive ones heated with any excess; the engine's split before C7). The two
            agree for N_eff = N_std.
    Ob      baryons (part of Om), needed only for the sound horizon.
    Or_extra  further radiation (w = 1/3), e.g. for an idealised radiation-only universe.
    dark_energy  None (Lambda) or an object with vectorised ``density_ratio(a)`` = rho(a)/rho(1) and ``w(a)``,
            defined at a = 0 (from ``lfphys.theories.models.dark_energy``; such a universe is outside the core's
            Lambda and is flagged by that module).

    The defaults describe an idealised universe without radiation; for the observed one pass T_cmb, N_eff, m_nu, or
    use ``planck2018()``.
    """

    def __init__(self, H0, Om, *, Ok=None, OL=None, T_cmb=0.0, N_eff=0.0, m_nu=(), n_nu=3, N_std=3.046, Ob=0.0,
                 Or_extra=0.0, dark_energy=None):
        H0, Om, T_cmb, N_eff, Ob, Or_extra = (float(v) for v in (H0, Om, T_cmb, N_eff, Ob, Or_extra))
        if not H0 > 0:
            raise ValueError("H0 must be positive")
        if Om < 0:
            raise ValueError("Om (cold dark matter + baryons) must be non-negative")
        if T_cmb < 0 or N_eff < 0 or Or_extra < 0 or Ob < 0:
            raise ValueError("T_cmb, N_eff, Ob and Or_extra must be non-negative")
        if N_std is not None and not float(N_std) > 0:
            raise ValueError("N_std must be positive (or None)")
        if Ob > Om:
            raise ValueError("Ob is part of Om and cannot exceed it")
        masses = [float(m) for m in np.atleast_1d(np.asarray(m_nu, float))] if np.size(m_nu) else []
        if any(m < 0 for m in masses):
            raise ValueError("neutrino masses must be non-negative")
        if len(masses) > n_nu:
            raise ValueError(f"{len(masses)} masses given for n_nu = {n_nu} species")
        if N_eff > 0 and T_cmb == 0:
            raise ValueError("N_eff > 0 needs T_cmb > 0 (the neutrino temperature follows from it)")
        massive = [m for m in masses if m > 0]
        if massive and N_eff == 0:
            raise ValueError("massive neutrinos need N_eff > 0")
        self.H0, self.h = H0, H0 / 100.0
        self.T_cmb, self.N_eff, self.n_nu = T_cmb, N_eff, int(n_nu)
        self.N_std = None if N_std is None else float(N_std)
        self.m_nu = tuple(massive)
        self.dark_energy = dark_energy
        self.H0_si = H0 / MPC_KM                                        # 1/s
        self.rho_crit0 = 3.0 * self.H0_si ** 2 / (8.0 * math.pi * G)    # kg/m^3
        self.Ogamma = A_RAD * T_cmb ** 4 / C ** 2 / self.rho_crit0
        # the share of N_eff carried by one massive species (and the temperature it implies), and the massless rest
        n_m = len(massive)
        if self.N_std is None:
            share = N_eff / n_nu
            massless = (n_nu - n_m) * share
        else:
            share = min(self.N_std / n_nu, N_eff / n_m) if n_m else min(self.N_std, N_eff) / n_nu
            massless = max(N_eff - n_m * share, 0.0)
        self.nu_share = share if N_eff > 0 else 0.0
        self.Onu_per_species = NU_FACTOR * share * self.Ogamma if N_eff > 0 else 0.0
        self.T_nu0 = share ** 0.25 * T_NU_RATIO * T_cmb if N_eff > 0 else 0.0
        self._y0 = np.array([m / (K_B_EV * self.T_nu0) for m in massive])
        self.Onu_massless = NU_FACTOR * massless * self.Ogamma if N_eff > 0 else 0.0
        self.Or_extra = Or_extra
        self.Orad = self.Ogamma + self.Onu_massless + Or_extra
        self.Onu_massive = (self.Onu_per_species * float(np.sum(_fd_sums(self._y0)[0]))) if massive else 0.0
        self.Om, self.Ob = Om, Ob
        rest = self.Orad + Om + self.Onu_massive
        if Ok is not None and OL is not None:
            if abs(rest + Ok + OL - 1.0) > 1e-12:
                raise ValueError(f"Ok + OL + the rest = {rest + Ok + OL!r} != 1; give only one of Ok, OL")
            self.Ok, self.OL = float(Ok), float(OL)
        elif OL is not None:
            self.OL = float(OL)
            self.Ok = 1.0 - rest - self.OL
        else:
            self.Ok = 0.0 if Ok is None else float(Ok)
            self.OL = 1.0 - rest - self.Ok
        self._roots = None

    # --- derived constants ----------------------------------------------------------------------------------------
    @property
    def Om_total(self):
        """Pressureless matter today including the massive neutrinos (Planck's Omega_m)."""
        return self.Om + self.Onu_massive

    @property
    def hubble_distance(self):
        """c/H0 in Mpc."""
        return C_KM_S / self.H0

    @property
    def hubble_time(self):
        """1/H0 in Gyr (Julian)."""
        return MPC_KM / self.H0 / GYR_S

    def omega_nu_massive(self):
        """Omega_nu h^2 of the massive species today."""
        return self.Onu_massive * self.h ** 2

    # --- S(a) = a^4 E^2(a) and its terms ---------------------------------------------------------------------------
    def _terms(self, a, q=0.0):
        """The terms of S(a)/a^q (radiation, matter, curvature, Lambda/dark energy, massive neutrinos), their factors
        (1 + 3w) for the acceleration equation, and the relative rounding of the dark-energy and neutrino terms.

        Each term is divided by a^q separately (q a scalar or an array like a), so that S/a^q can be formed where S
        itself overflows or underflows (review B7-flrw C1, C3): ``_q`` chooses q as the power of the term that
        dominates at a (4 where Lambda does, so that O_L a^4, which overflows binary64 beyond a ~ 1e77, is never
        formed); q = 0 is S itself. A dark-energy term is formed as O_L exp((4 - q) ln a + ln rho(a)), so that
        neither a^(4 - q) nor rho(a) over- or underflows on its own."""
        a = np.asarray(a, dtype=float)
        q = np.asarray(q, dtype=float)
        shape = np.broadcast(a, q).shape

        def pw(c, e):                   # c a^(e - q), zero where the coefficient is (no 0 x inf)
            if c == 0:
                return np.zeros(shape)
            with np.errstate(over="ignore", divide="ignore", under="ignore"):
                return c * np.power(a, e - q)
        t_r = pw(self.Orad, 0.0)
        t_m = pw(self.Om, 1.0)
        t_k = pw(self.Ok, 2.0)
        if self.dark_energy is None:
            t_l = pw(self.OL, 4.0)
            q_l = -2.0
            r_l = 4 * _U
        else:
            lr = self._ln_rho(a)
            with np.errstate(over="ignore", divide="ignore", invalid="ignore", under="ignore"):
                x = (4.0 - q) * np.log(a) + lr
                # the direct product where both factors are normal numbers (fewer roundings), else through logs
                direct = self.OL * np.power(a, 4.0 - q) * np.asarray(self.dark_energy.density_ratio(a), float)
                use = np.isfinite(direct) & (np.abs(direct) > 1e-280) & (np.abs(x) < 600)
                t_l = np.where(use, direct, self.OL * np.exp(x)) if self.OL != 0 else np.zeros(shape)
                r_l = np.where(use, 64.0, 64 + 2 * (np.abs(4.0 - q) * np.abs(np.log(a)) + np.abs(lr))) * _U
            q_l = 1.0 + 3.0 * np.asarray(self.dark_energy.w(a), float)
        if self._y0.size:
            F, J = _fd_sums(np.multiply.outer(a, self._y0))
            sc = pw(1.0, 0.0)
            t_n = self.Onu_per_species * F.sum(axis=-1) * sc
            q_n_num = self.Onu_per_species * (F + 3.0 * J).sum(axis=-1) * sc
        else:
            t_n = np.zeros(shape)
            q_n_num = t_n
        return t_r, t_m, t_k, t_l, t_n, q_l, q_n_num, r_l

    def _ln_rho(self, a):
        """ln(rho_de(a)/rho_de(1)) of the dark-energy model (its ``log_density_ratio`` if it has one, so that a
        phantom's growth or a fast decay is not lost to overflow)."""
        de = self.dark_energy
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            if hasattr(de, "log_density_ratio"):
                return np.asarray(de.log_density_ratio(a), float)
            return np.log(np.asarray(de.density_ratio(a), float))

    def _S(self, a, q=0.0):
        """S(a)/a^q and its rounding bound (relative 8u per term and 2u for the powers a^(e - q))."""
        t_r, t_m, t_k, t_l, t_n, _, _, r_l = self._terms(a, q)
        S = t_r + t_m + t_k + t_l + t_n
        absum = np.abs(t_r) + np.abs(t_m) + np.abs(t_k) + np.abs(t_l) + np.abs(t_n)
        eS = 10 * _U * absum + r_l * np.abs(t_l) + FD_REL_ERROR * np.abs(t_n)
        return S, eS

    def _q(self, a):
        """The power q by which S is divided at a: the (effective) power of the term of S that is largest in
        magnitude at a (compared by logarithms, so nothing overflows): 0 radiation, 1 matter, 2 curvature, 4
        Lambda, 4 + ln rho(a)/ln a a dark-energy model, ln F(y a)/ln a the massive neutrinos. S/a^q is then of the
        order of that term's coefficient wherever a is between ~1e-300 and ~1e300."""
        a = np.asarray(a, float)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            la = np.log(a)
            best = np.full(a.shape, -np.inf)
            q = np.zeros(a.shape)

            def take(L, e):
                nonlocal best, q
                L = np.broadcast_to(np.asarray(L, float), a.shape)
                sel = L > best
                best = np.where(sel, L, best)
                q = np.where(sel, np.broadcast_to(np.asarray(e, float), a.shape), q)
            if self.Orad > 0:
                take(math.log(self.Orad), 0.0)
            if self.Om > 0:
                take(math.log(self.Om) + la, 1.0)
            if self.Ok != 0:
                take(math.log(abs(self.Ok)) + 2.0 * la, 2.0)
            if self.OL != 0:
                if self.dark_energy is None:
                    take(math.log(abs(self.OL)) + 4.0 * la, 4.0)
                else:
                    lr = self._ln_rho(a)
                    w1 = float(np.asarray(self.dark_energy.w(1.0)))
                    take(math.log(abs(self.OL)) + 4.0 * la + lr,
                         np.where(la != 0, 4.0 + lr / np.where(la != 0, la, 1.0), 1.0 - 3.0 * w1))
            if self._y0.size:          # F(x) ~ sqrt(1 + (A x)^2), A = 180 zeta(3)/(7 pi^4), is enough to compare
                X = _A_NR * np.multiply.outer(a, self._y0)
                lF = np.log(np.sum(np.hypot(1.0, X), axis=-1))
                take(math.log(self.Onu_per_species) + lF, np.sum(1.0 / (1.0 + X ** -2.0), axis=-1) / self._y0.size)
        q = np.where(np.isfinite(q), q, 0.0)
        return q

    def E2(self, z):
        """E^2(z) = H^2/H0^2."""
        z = np.asarray(z, float)
        a = 1.0 / (1.0 + z)
        S, _ = self._S(a, 4.0)
        return _scalar_or_array(np.asarray(S), z)

    def E(self, z):
        """E(z) = H(z)/H0; nan where E^2 < 0 (a universe that never reaches that z)."""
        e2 = np.asarray(self.E2(z))
        with np.errstate(invalid="ignore"):
            out = np.sqrt(e2)
        return _scalar_or_array(out, z)

    def H(self, z):
        """H(z) in km/s/Mpc."""
        return self.H0 * self.E(z)

    def critical_density(self, z=0.0):
        """rho_crit(z) = 3 H(z)^2 / (8 pi G) in kg/m^3."""
        return self.rho_crit0 * self.E2(z)

    def densities(self, z):
        """Density parameters at z, Omega_x(z) = rho_x(z)/rho_crit(z): 'photons', 'neutrinos_massless',
        'neutrinos_massive', 'radiation_extra', 'matter' (CDM + baryons), 'baryons', 'curvature' (O_k(z)),
        'dark_energy' (Lambda or the model). All except 'baryons' sum to one ('baryons' is a part of 'matter')."""
        z = np.asarray(z, float)
        a = 1.0 / (1.0 + z)
        q = self._q(a)
        t_r, t_m, t_k, t_l, t_n, _, _, _ = self._terms(a, q)
        S = t_r + t_m + t_k + t_l + t_n
        with np.errstate(over="ignore", divide="ignore"):
            sc = np.power(a, -q)
        out = {"photons": self.Ogamma * sc / S, "neutrinos_massless": self.Onu_massless * sc / S,
               "neutrinos_massive": t_n / S, "radiation_extra": self.Or_extra * sc / S, "matter": t_m / S,
               "baryons": self.Ob * a * sc / S, "curvature": t_k / S, "dark_energy": t_l / S}
        return {k: _scalar_or_array(np.asarray(v * np.ones_like(a)), z) for k, v in out.items()}

    def deceleration(self, z):
        """q(z) = -a a''/a'^2 = (1/2) sum_j Omega_j(z) (1 + 3 w_j(z)) (curvature has 1 + 3w = 0), with the massive
        neutrinos' pressure from their Fermi-Dirac integral."""
        z = np.asarray(z, float)
        a = 1.0 / (1.0 + z)
        t_r, t_m, t_k, t_l, t_n, q_l, q_n, _ = self._terms(a, self._q(a))
        S = t_r + t_m + t_k + t_l + t_n
        return _scalar_or_array(np.asarray(0.5 * (2.0 * t_r + t_m + q_l * t_l + q_n) / S), z)

    # --- the structure of S: big bang, bounce, turnaround -----------------------------------------------------------
    def _early_terms(self):
        """[(power, coefficient)] of the terms of S(a) ~ sum c a^p for a -> 0 (a dark-energy model's coefficient
        from its density at a = 1e-300)."""
        comps = []
        if self.Orad + self.Onu_per_species * self._y0.size > 0:
            comps.append((0.0, self.Orad + self.Onu_per_species * self._y0.size))
        if self.Om != 0:
            comps.append((1.0, self.Om))
        if self.Ok != 0:
            comps.append((2.0, self.Ok))
        if self.OL != 0:
            if self.dark_energy is None:
                comps.append((4.0, self.OL))
            else:
                p = 1.0 - 3.0 * float(self.dark_energy.w(0.0))
                la = math.log(1e-300)
                comps.append((p, self.OL * math.exp(float(self._ln_rho(np.array([1e-300]))[0]) + (4.0 - p) * la)))
        return comps

    def _early(self):
        """(p, c): S(a) ~ c a^p for a -> 0."""
        comps = self._early_terms()
        if not comps:
            return math.inf, 0.0
        p = min(c[0] for c in comps)
        return p, sum(c[1] for c in comps if c[0] == p)

    def roots(self):
        """Scale factors where E^2 = 0 between 1e-12 and 1e12: (a_bounce, a_turnaround), each None if absent.
        a_bounce < 1 means no big bang (the universe contracted to a_bounce and re-expanded); a_turnaround > 1 means
        recollapse. The points with S <= 0 are found (i) by a scan of S on 4001 points in xi, (ii) by minimising S
        (bounded Brent) between the neighbours of every local minimum of the scanned values, so that a forbidden
        band narrower than the scan step is not missed (review B7-flrw C2), and (iii) for a polynomial S (Lambda,
        dust, curvature, radiation; no dark-energy model and no massive neutrinos) also at the exact stationary
        points of S (the real roots of S'(a) = O_m + 2 O_k a + 4 O_L a^3). The edges of the band next to a = 1 are
        then polished by brentq (rtol 8u). A band is missed only if S has two extrema within one scan step (Delta ln a
        ~ 0.014) and is not a polynomial."""
        if self._roots is not None:
            return self._roots
        bounce = turn = None
        if min(self.Ok, self.OL) < 0 or self.dark_energy is not None:      # Om >= 0 and Orad >= 0 are enforced
            xi = np.linspace(float(_xi_of_a(1e-12)), float(_xi_of_a(1e12)), 4001)
            a = _a_of_xi(xi)
            with np.errstate(over="ignore", invalid="ignore"):   # a dark energy with wa > 0 grows as e^(3 wa a)
                S, _ = self._S(a, self._q(a))

            def fS(x):
                x = np.array([x])
                with np.errstate(over="ignore", invalid="ignore"):
                    return float(self._S(x, self._q(x))[0][0])
            neg = list(a[S <= 0])
            loc = np.nonzero((S[1:-1] < S[:-2]) & (S[1:-1] <= S[2:]) & (S[1:-1] > 0))[0] + 1
            # only where the parabola through the three samples dips below half the middle value (a dip that may
            # reach zero between samples; rounding noise on a plateau of S/a^q does not)
            d1, d2 = S[loc + 1] - S[loc - 1], S[loc + 1] - 2.0 * S[loc] + S[loc - 1]
            with np.errstate(divide="ignore", invalid="ignore"):
                dip = np.where(d2 > 0, S[loc] - d1 * d1 / (8.0 * d2), S[loc])
            for i in loc[dip < 0.5 * S[loc]]:
                r = optimize.minimize_scalar(fS, bounds=(a[i - 1], a[i + 1]), method="bounded",
                                             options={"xatol": 4 * _U * a[i], "maxiter": 500})
                if r.fun <= 0:
                    neg.append(float(r.x))
            if self.dark_energy is None and not self._y0.size:
                for c in np.roots([4.0 * self.OL, 0.0, 2.0 * self.Ok, self.Om]) if self.OL != 0 else (
                        np.roots([2.0 * self.Ok, self.Om]) if self.Ok != 0 else []):
                    if abs(c.imag) <= 1e-12 * abs(c) and 1e-12 < c.real < 1e12 and fS(c.real) <= 0:
                        neg.append(float(c.real))
            neg = np.array(neg)
            below = neg[neg < 1.0]
            if below.size:
                x = below.max()
                up = a[(a > x) & (a < 1.0)]
                hi = float(up.min()) if up.size else 1.0
                bounce = optimize.brentq(fS, x, hi, xtol=1e-300, rtol=8 * _U) if fS(x) < 0 else x
            above = neg[neg > 1.0]
            if above.size:
                x = above.min()
                dn = a[(a < x) & (a > 1.0)]
                lo = float(dn.max()) if dn.size else 1.0
                turn = optimize.brentq(fS, lo, x, xtol=1e-300, rtol=8 * _U) if fS(x) < 0 else x
        self._roots = (bounce, turn)
        return self._roots

    def _check_range(self, a_lo, a_hi, what):
        bounce, turn = self.roots()
        if bounce is not None and a_lo < bounce:
            raise ValueError(f"{what}: this universe has no big bang; it bounced at a = {bounce:.6g} "
                             f"(z = {1 / bounce - 1:.6g}) and never had a < {bounce:.6g}")
        if turn is not None and a_hi > turn:
            raise ValueError(f"{what}: this universe recollapses at a = {turn:.6g} and never reaches a = {a_hi:.6g}")

    def _has_big_bang(self):
        p, c = self._early()
        return c > 0 and self.roots()[0] is None

    # --- integrals ----------------------------------------------------------------------------------------------------
    def _integrand(self, kind):
        """The integrand in xi of the integrals from the big bang ('t', 'eta', 'rs'), with S divided by a^q
        (``_q``): t: a jac/sqrt(S) = a^(1 - q/2) jac/sqrt(S/a^q), eta: a^(-q/2) jac/sqrt(S/a^q), jac = da/dxi (2 xi
        for a <= 4, a beyond; for a > 4 the powers are combined, so that nothing overflows below a ~ 1e300)."""
        R0 = 3.0 * self.Ob / (4.0 * self.Ogamma) if self.Ogamma > 0 else math.inf
        if kind not in ("t", "eta", "rs"):
            raise ValueError(kind)
        e0 = 1.0 if kind == "t" else 0.0

        def f(xi):
            a = _a_of_xi(xi)
            q = self._q(a)
            S, eS = self._S(a, q)
            with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
                inv = 1.0 / np.sqrt(np.where(S > 0, S, np.nan))
                e = e0 - 0.5 * q
                pre = np.where(xi > 2.0, np.power(a, e + 1.0), 2.0 * xi * np.power(a, e))
                v = pre * inv
                rel = 0.5 * eS / np.abs(S) + 10 * _U
                if kind == "rs":
                    v = v / np.sqrt(3.0 * (1.0 + R0 * a))
                    rel = rel + 4 * _U
                rel = np.where(np.isinf(S), 0.0, rel)       # S beyond binary64 (a phantom's far future): v = 0
            return v, rel
        return f

    def _bang_segments(self, kind, xi_lo, xi_hi, rtol):
        """int of ``_integrand(kind)`` over the segments [xi_lo, xi_hi] (all within xi <= 2, i.e. a <= 4, the first
        from 0), in s with xi = s^k: near a = 0, S = c a^p (1 + ...), and the integrand in xi is 2 xi^alpha /
        sqrt(S/a^p) (alpha = 3 - p for t, 1 - p for eta and r_s), a power with -1 < alpha < 0 for a dark energy that
        dominates at the big bang (constant w in (-1, -2/3) for t, (-1/3, 0) for eta; review B7-flrw C3). With
        k = (m + 1)/(1 + alpha), m = ceil(1 + alpha) - 1 >= 0 (k = 1 when alpha is a whole number), the integrand in
        s is 2 k s^m / sqrt(S/a^p), a = s^(2k): its leading term is a polynomial, so Gauss-Legendre integrates it
        exactly, the panel at s = 0 carries only the corrections (powers s^(m + beta), beta > 0), for which the
        difference of the halves bounds the error (``_adaptive``), and a segment far from 0 spanning many decades of
        a needs no deep bisection. Returns (value, quadrature error, rounding bound) per segment."""
        p, _ = self._early()
        alpha = (3.0 if kind == "t" else 1.0) - p
        ra = round(alpha)
        if abs(alpha - ra) <= 1e-12 and ra >= 0:
            k, expo = 1.0, float(ra)
        else:
            m = math.ceil(1.0 + alpha) - 1
            k, expo = (m + 1.0) / (1.0 + alpha), float(m)
        R0 = 3.0 * self.Ob / (4.0 * self.Ogamma) if self.Ogamma > 0 else math.inf
        # where a = s^(2k) would underflow, S/a^p is taken at a = 1e-300: its relative change is below
        # sum_j |c_j/c| 1e-300^(p_j - p) over the other terms, added to the rounding there
        comps = self._early_terms()
        c_lead = abs(sum(cj for pj, cj in comps if pj == p))
        clamp = sum(abs(cj) / c_lead * 1e-300 ** (pj - p) for pj, cj in comps if pj > p)

        def f(s):
            with np.errstate(divide="ignore", under="ignore"):
                la = 2.0 * k * np.log(s)
            small = la < math.log(1e-300)
            a = np.where(small, 1e-300, np.exp(np.maximum(la, math.log(1e-300))))
            S, eS = self._S(a, p)
            with np.errstate(invalid="ignore", divide="ignore"):
                v = 2.0 * k * np.power(s, expo) / np.sqrt(np.where(S > 0, S, np.nan))
                rel = 0.5 * eS / np.abs(S) + 16 * _U + np.where(small, 0.5 * clamp, 0.0)
                if kind == "rs":
                    v = v / np.sqrt(3.0 * (1.0 + R0 * a))
                    rel = rel + 4 * _U
            return v, rel
        return _adaptive(f, np.power(np.asarray(xi_lo, float), 1.0 / k), np.power(np.asarray(xi_hi, float), 1.0 / k),
                         rtol)

    def _cumulative(self, kind, a_targets, rtol):
        """int_0^a (kind's integrand) da for every target a, in xi (1/H0 units): (value, error) arrays. The segments
        with a <= 4 through ``_bang_segments``."""
        a_t = np.asarray(a_targets, float).ravel()
        xi_t = _xi_of_a(a_t)
        out = np.zeros_like(a_t)
        err = np.zeros_like(a_t)
        sel = xi_t > 0
        if not sel.any():
            return out, err
        pts = np.unique(xi_t[sel])
        edges = np.concatenate([[0.0], pts])
        if edges[-1] > 2.0 and not np.any(edges == 2.0):       # the join of the two maps as a panel edge
            edges = np.sort(np.concatenate([edges, [2.0]]))
        low = edges[1:] <= 2.0
        v0, eq0, er0 = self._bang_segments(kind, edges[:-1][low], edges[1:][low], rtol)
        v, eq, er = _adaptive(self._integrand(kind), edges[:-1][~low], edges[1:][~low], rtol)
        v, eq, er = (np.concatenate([x0, x]) for x0, x in ((v0, v), (eq0, eq), (er0, er)))
        cum = _prefix(v)
        cerr = np.cumsum(eq + er) + 2 * _U * np.abs(cum)
        idx = np.searchsorted(edges[1:], xi_t[sel])
        out[sel] = cum[idx]
        err[sel] = cerr[idx]
        return out, err

    def _from_bang(self, kind, a, rtol, what):
        """int_0^a for the kinds 't', 'eta', 'rs' (inf where the integral diverges at the big bang)."""
        a = np.asarray(a, float)
        p, c = self._early()
        if not c > 0:
            raise ValueError(f"{what}: no big bang (E^2 < 0 or no matter, radiation or curvature as a -> 0)")
        self._check_range(0.0, float(np.max(a)) if a.size else 0.0, what)
        limit = {"t": 4.0, "eta": 2.0, "rs": 2.0}[kind]
        if p >= limit:
            inf = np.full(a.shape, math.inf)
            return inf, np.zeros(a.shape)
        v, e = self._cumulative(kind, a, rtol)
        return v.reshape(a.shape), e.reshape(a.shape)

    def _integrand_s(self, kind):
        """Integrands in s = ln(1 + z) = -ln a for the integrals from today: (1+z)/E (comoving distance) and 1/E
        (time); s is computed from z by log1p, so a small redshift keeps its relative accuracy."""
        e0 = 2.0 if kind == "t" else 1.0

        def f(s):
            a = np.exp(-s)
            q = self._q(a)
            S, eS = self._S(a, q)                   # S/a^q: E^2 for a > 1 (no overflow of O_L a^4; C1)
            with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
                inv = 1.0 / np.sqrt(np.where(S > 0, S, np.nan))
                v = np.exp(-(e0 - 0.5 * q) * s) * inv  # a^(e0 - q/2) / sqrt(S/a^q)
                rel = np.where(np.isinf(S), 0.0, 0.5 * eS / np.abs(S) + (10 + 2 * np.abs(s)) * _U)
            return v, rel
        return f

    def _cum_s(self, kind, s_targets, rtol):
        """int_0^s (kind's integrand in s) for every target s = ln(1 + z) (negative s: the future), 1/H0 units:
        (value, error)."""
        s_t = np.asarray(s_targets, float).ravel()
        out = np.zeros_like(s_t)
        err = np.zeros_like(s_t)
        f = self._integrand_s(kind)
        for side in (1, -1):
            sel = s_t * side > 0
            if not sel.any():
                continue
            pts = np.unique(np.abs(s_t[sel]))
            edges = np.concatenate([[0.0], pts]) * side
            lo, hi = np.minimum(edges[:-1], edges[1:]), np.maximum(edges[:-1], edges[1:])
            v, eq, er = _adaptive(f, lo, hi, rtol)
            cum = _prefix(v)
            cerr = np.cumsum(eq + er) + 2 * _U * np.abs(cum)
            idx = np.searchsorted(pts, np.abs(s_t[sel]))
            out[sel] = side * cum[idx]
            err[sel] = cerr[idx]
        return out, err

    def _since_today(self, kind, z, rtol, what):
        """int over the past light cone from today to z: (1/H0) int_0^z dz/E ('eta') or int_0^z dz/((1+z)E)
        ('t'); negative for z < 0 (the future)."""
        z = np.asarray(z, float)
        if z.size:
            a = 1.0 / (1.0 + z)
            self._check_range(float(np.min(a)), float(np.max(a)), what)
        fin = np.isfinite(z).ravel()
        v, e = np.empty(z.size), np.empty(z.size)
        v[fin], e[fin] = self._cum_s(kind, np.log1p(z.ravel()[fin]), rtol)
        if not fin.all():          # z = inf: the whole past, i.e. the conformal time or the age today
            v0, e0 = self._from_bang(kind, np.array([1.0]), rtol, what)
            v[~fin], e[~fin] = v0[0], e0[0]
        return v.reshape(z.shape), e.reshape(z.shape)

    @staticmethod
    def _ret(v, e, like, with_error):
        v, e = _scalar_or_array(np.asarray(v), like), _scalar_or_array(np.asarray(e), like)
        return (v, e) if with_error else v

    # --- distances ----------------------------------------------------------------------------------------------------
    def _chi(self, z, rtol):
        """Line-of-sight comoving distance in units of D_H, and its error."""
        z = np.asarray(z, float)
        v, e = self._since_today("eta", z, rtol, "comoving distance")
        return v, e

    def _sinn(self, chi):
        k = self.Ok
        if k > 0:
            s = math.sqrt(k)
            return np.sinh(s * chi) / s, np.cosh(s * chi)
        if k < 0:
            s = math.sqrt(-k)
            return np.sin(s * chi) / s, np.cos(s * chi)
        return chi, np.ones_like(chi)

    def comoving_distance(self, z, *, rtol=1e-13, with_error=False):
        """Line-of-sight comoving distance D_C(z) in Mpc (Hogg Eq. (15))."""
        v, e = self._chi(z, rtol)
        return self._ret(v * self.hubble_distance, e * self.hubble_distance, z, with_error)

    def transverse_comoving_distance(self, z, *, rtol=1e-13, with_error=False):
        """D_M(z) in Mpc (Hogg Eq. (16)); for O_k < 0 it is sin(...)/sqrt|O_k| (negative beyond the antipode)."""
        chi, e = self._chi(z, rtol)
        s, ds = self._sinn(chi)
        return self._ret(s * self.hubble_distance, np.abs(ds) * e * self.hubble_distance, z, with_error)

    def angular_diameter_distance(self, z, *, rtol=1e-13, with_error=False):
        """D_A = D_M/(1 + z) in Mpc."""
        v, e = self.transverse_comoving_distance(z, rtol=rtol, with_error=True)
        f = 1.0 / (1.0 + np.asarray(z, float))
        return self._ret(np.asarray(v) * f, np.asarray(e) * f * (1 + 2 * _U), z, with_error)

    def luminosity_distance(self, z, *, rtol=1e-13, with_error=False):
        """D_L = (1 + z) D_M in Mpc."""
        v, e = self.transverse_comoving_distance(z, rtol=rtol, with_error=True)
        f = 1.0 + np.asarray(z, float)
        return self._ret(np.asarray(v) * f, np.asarray(e) * f * (1 + 2 * _U), z, with_error)

    def distance_modulus(self, z, *, rtol=1e-13, with_error=False):
        """mu = 5 log10(D_L / 10 pc) (Hogg Eq. (25))."""
        dl, e = self.luminosity_distance(z, rtol=rtol, with_error=True)
        dl, e = np.asarray(dl), np.asarray(e)
        with np.errstate(divide="ignore"):
            mu = 5.0 * np.log10(dl) + 25.0          # D_L in Mpc; 10 pc = 1e-5 Mpc
        return self._ret(mu, 5.0 / math.log(10.0) * (e / dl + 4 * _U) + 4 * _U * np.abs(mu), z, with_error)

    def angular_diameter_distance_z1z2(self, z1, z2, *, rtol=1e-13, with_error=False):
        """D_A between z1 <= z2 (a source at z2 seen from z1), Mpc: sinn(chi_2 - chi_1)/(1 + z2) (Carroll 2001,
        Eq. (42)); any sign of O_k. z1 > z2 is refused (ValueError)."""
        z1, z2 = np.broadcast_arrays(np.asarray(z1, float), np.asarray(z2, float))
        if np.any(z1 > z2):
            raise ValueError("angular_diameter_distance_z1z2 needs z1 <= z2 (the observer at z1, the source at z2)")
        c1, e1 = self._chi(z1, rtol)
        c2, e2 = self._chi(z2, rtol)
        s, ds = self._sinn(c2 - c1)
        f = self.hubble_distance / (1.0 + z2)
        return self._ret(s * f, np.abs(ds) * (e1 + e2 + 2 * _U * np.abs(c2 - c1)) * f, z2, with_error)

    # --- times --------------------------------------------------------------------------------------------------------
    def lookback_time(self, z, *, rtol=1e-13, with_error=False):
        """t_0 - t(z) in Gyr (Hogg Eq. (30))."""
        z = np.asarray(z, float)
        v, e = self._since_today("t", z, rtol, "lookback time")
        return self._ret(v * self.hubble_time, e * self.hubble_time, z, with_error)

    def age(self, z=0.0, *, rtol=1e-13, with_error=False):
        """Cosmic time since the big bang at redshift z, Gyr (inf where the integral diverges: de Sitter)."""
        z = np.asarray(z, float)
        v, e = self._from_bang("t", 1.0 / (1.0 + z), rtol, "age")
        return self._ret(v * self.hubble_time, e * self.hubble_time, z, with_error)

    def conformal_time(self, z=0.0, *, rtol=1e-13, with_error=False):
        """eta(z) = int_0^t dt/a in Gyr (inf where it diverges)."""
        z = np.asarray(z, float)
        v, e = self._from_bang("eta", 1.0 / (1.0 + z), rtol, "conformal time")
        return self._ret(v * self.hubble_time, e * self.hubble_time, z, with_error)

    def particle_horizon(self, z=0.0, *, rtol=1e-13, with_error=False):
        """Comoving particle horizon c eta(z) in Mpc (the proper horizon is this / (1 + z))."""
        z = np.asarray(z, float)
        v, e = self._from_bang("eta", 1.0 / (1.0 + z), rtol, "particle horizon")
        return self._ret(v * self.hubble_distance, e * self.hubble_distance, z, with_error)

    def sound_horizon(self, z, *, rtol=1e-13, with_error=False):
        """Comoving sound horizon of the photon-baryon fluid at z, Mpc: int c_s dt/a with c_s = c/sqrt(3(1 + R)),
        R = 3 rho_b/(4 rho_gamma) (Eisenstein & Hu 1998, Eq. (5)). Needs photons (T_cmb > 0)."""
        if not self.Ogamma > 0:
            raise ValueError("the sound horizon needs photons (T_cmb > 0)")
        z = np.asarray(z, float)
        v, e = self._from_bang("rs", 1.0 / (1.0 + z), rtol, "sound horizon")
        return self._ret(v * self.hubble_distance, e * self.hubble_distance, z, with_error)

    def z_equality(self, neutrinos="exact"):
        """Redshift of matter-radiation equality: rho_cb = rho_gamma + rho_nu + rho_extra. neutrinos='exact': the
        massive species with their actual density F(y); 'relativistic': counted as massless, i.e. (omega_b +
        omega_c)/omega_r - 1, the definition of CAMB's derived z_EQ behind Planck 2018 Table 2."""
        if not self.Om > 0 or self.Orad + self.Onu_per_species * self._y0.size <= 0:
            raise ValueError("needs matter and radiation")
        if neutrinos == "relativistic":
            return self.Om / (self.Orad + self.Onu_per_species * self._y0.size) - 1.0
        if neutrinos != "exact":
            raise ValueError(neutrinos)

        def g(a):
            F = _fd_sums(self._y0 * a)[0].sum() if self._y0.size else 0.0
            return self.Om * a - self.Orad - self.Onu_per_species * F
        hi = 1.0
        while g(hi) < 0:
            hi *= 2.0
        a = optimize.brentq(g, 0.0, hi, xtol=1e-300, rtol=8 * _U, maxiter=500)
        return 1.0 / a - 1.0

    # --- the scale factor a(t) --------------------------------------------------------------------------------------
    def _time(self, a, origin, rtol):
        """Time in 1/H0 at scale factor a on the expanding branch, since the big bang (origin 'bang') or since today
        ('today'); next to a turnaround or a bounce through the w-form."""
        a = np.asarray(a, float)
        bounce, turn = self.roots()
        out = np.empty_like(a)
        near_t = np.zeros(a.shape, bool) if turn is None else a > 0.75 * turn
        near_b = np.zeros(a.shape, bool) if bounce is None else a < 1.25 * bounce
        reg = ~(near_t | near_b)
        if reg.any():
            out[reg] = self._time_regular(a[reg], origin, rtol)
        if near_t.any():
            out[near_t] = (self._time_root(turn, -1, origin)
                           - self._w_integral(turn, -1, np.sqrt(1.0 - a[near_t] / turn), rtol))
        if near_b.any():
            out[near_b] = (self._time_root(bounce, 1, origin)
                           + self._w_integral(bounce, 1, np.sqrt(a[near_b] / bounce - 1.0), rtol))
        return out

    def _time_regular(self, a, origin, rtol):
        if origin == "bang":
            return self._cumulative("t", a, rtol)[0]
        return -self._cum_s("t", -np.log(a), rtol)[0]

    def _S_root(self, r, sgn, x):
        """S(a) at a = r (1 + sgn x^2) next to a root r of S, with the root placed exactly at r: the polynomial
        part as (a - r) times its divided difference (no cancellation), the dark-energy model and the massive
        neutrinos as differences of their terms. Returns (S, rounding bound)."""
        a = r * (1.0 + sgn * x * x)
        da = sgn * r * x * x
        D = self.Om + self.Ok * (a + r)
        if self.dark_energy is None:
            D = D + self.OL * (a * a * a + a * a * r + a * r * r + r * r * r)
        S = da * D
        eS = 16 * _U * np.abs(da) * (np.abs(self.Om) + np.abs(self.Ok) * (a + r)
                                    + (abs(self.OL) * (a ** 3 + a * a * r + a * r * r + r ** 3)
                                       if self.dark_energy is None else 0.0))
        if self.dark_energy is not None or self._y0.size:
            # 16-point Gauss-Legendre nodes on [r, a] for every a: the changes of the dark-energy and neutrino terms
            # as integrals of their derivatives, not as differences of the terms (whose rounding, absolute, would
            # dominate S ~ (a - r) S'(r) next to the root; found while processing review B7-flrw C2)
            nodes = r + 0.5 * da[..., None] * (1.0 + _GL_T)
            wts = 0.5 * da[..., None] * _GL_W
        if self.dark_energy is not None:
            _, _, _, t_l0, _, _, _, _ = self._terms(np.array([r]))
            dlr = -3.0 * np.sum(wts * (1.0 + np.asarray(self.dark_energy.w(nodes), float)) / nodes, axis=-1)
            dl = float(t_l0[0]) * np.expm1(4.0 * np.log1p(sgn * x * x) + dlr)   # O_L (a^4 rho(a) - r^4 rho(r))
            S = S + dl
            eS = eS + 32 * _U * np.abs(dl)
        if self._y0.size:
            dF = _fd_dsums(np.multiply.outer(nodes, self._y0)) * self._y0         # d F(y a)/da = y F'(y a)
            dn = self.Onu_per_species * np.sum(wts[..., None] * dF, axis=(-2, -1))
            S = S + dn
            eS = eS + (32 * _U + FD_REL_ERROR) * np.abs(dn)
        return a, S, eS + 4 * _U * np.abs(S)

    def _w_integral(self, r, sgn, w, rtol):
        """int_0^w 2 r w' a / sqrt(S(a)) dw', a = r (1 + sgn w'^2): the time (1/H0) from the root r to a(w)."""
        w = np.asarray(w, float).ravel()

        def f(x):
            a, S, eS = self._S_root(r, sgn, x)
            with np.errstate(invalid="ignore", divide="ignore"):
                v = 2.0 * r * x * a / np.sqrt(np.where(S > 0, S, np.nan))
                rel = 0.5 * eS / np.abs(S) + 8 * _U
            v = np.where(x == 0, 0.0, v)
            return v, np.where(x == 0, 0.0, rel)
        pts = np.unique(w)
        edges = np.concatenate([[0.0], pts])
        v, _, _ = _adaptive(f, edges[:-1], edges[1:], rtol)
        cum = _prefix(v)
        return cum[np.searchsorted(pts, w)]

    def _time_root(self, r, sgn, origin):
        """Time (1/H0, since the big bang or today) at the root r of S (turnaround sgn = -1, bounce +1)."""
        key = (origin, r, sgn)
        cache = self.__dict__.setdefault("_cache", {})
        if key not in cache:
            a_sw = r * (1.0 + sgn * 0.25)       # w = 1/2
            t_sw = float(self._time_regular(np.array([a_sw]), origin, 1e-14)[0])
            cache[key] = t_sw - sgn * float(self._w_integral(r, sgn, np.array([0.5]), 1e-14)[0])
        return cache[key]

    def turnaround(self):
        """(a_max, t_max) of a recollapsing universe (t_max in Gyr since the big bang, or since today if there is no
        big bang), or None."""
        _, turn = self.roots()
        if turn is None:
            return None
        origin = "bang" if self._has_big_bang() else "today"
        return float(turn), float(self._time_root(turn, -1, origin) * self.hubble_time)

    def scale_factor(self, t, since="big_bang", *, rtol=1e-13):
        """a(t): t in Gyr since the big bang (``since='big_bang'``) or since today (``'today'``, negative in the
        past; the only choice without a big bang). A recollapsing universe is symmetric about its turnaround
        (a(t_max + s) = a(t_max - s)), a bouncing one about its bounce; times past the big crunch give nan.
        Found by safeguarded Newton steps in ln a on t(a) (exact derivative dt/d ln a = 1/H) to |delta ln a| <=
        4u max(1, |ln a|); near a turnaround the input time itself limits a (conditioning, not the solver). A time
        whose a lies outside [1e-300, 1e300] gives inf (or 0) with a RuntimeWarning; an inversion whose residual
        |t(a) - t| stays large raises FloatingPointError (review B7-flrw C1)."""
        t = np.asarray(t, float)
        tt = t.ravel() / self.hubble_time
        bounce, turn = self.roots()
        if since == "big_bang":
            if not self._has_big_bang():
                raise ValueError("no big bang: use since='today'")
            if self._early()[0] >= 4.0:
                raise ValueError("infinite age: use since='today'")
            origin, lower = "bang", 0.0
        elif since == "today":
            origin, lower = "today", -math.inf
        else:
            raise ValueError(since)
        out = np.full(tt.shape, np.nan)
        exact = np.zeros(tt.shape, bool)
        if turn is not None:
            tm = self._time_root(turn, -1, origin)
            tt = np.where(tt > tm, 2 * tm - tt, tt)
            out[tt == tm] = turn
            exact |= tt == tm
        if bounce is not None:
            tb = self._time_root(bounce, 1, origin)
            lower = tb
            tt = np.where(tt < tb, 2 * tb - tt, tt)
            out[tt == tb] = bounce
            exact |= tt == tb
        valid = (tt >= lower) & np.isfinite(tt) & ~exact
        if origin == "bang":
            out[valid & (tt == 0)] = 0.0
            valid &= tt > 0
        if valid.any():
            out[valid] = self._invert(tt[valid], origin, rtol)
        return _scalar_or_array(out, t)

    def _invert(self, tau, origin, rtol):
        """a with _time(a, origin) = tau (strictly inside the expanding branch), by Newton steps in ln a kept inside
        a bracket (bisection when a step leaves it or the derivative is not finite and positive). Accepted only when
        the last step or the bracket is below the tolerance and the residual |t(a) - tau| is within that step's
        reach plus 1e-9 (|tau| + 1/E) (a guard against a broken t(a), far above its error; review B7-flrw C1);
        otherwise FloatingPointError. A time beyond t(1e300) gives inf with a RuntimeWarning (a outside the range
        the engine represents)."""
        bounce, turn = self.roots()
        lo_a = (bounce * (1 + 1e-15)) if bounce is not None else 1e-300
        hi_a = (turn * (1 - 1e-16)) if turn is not None else 1e300
        grid = np.unique(np.concatenate([np.geomspace(max(lo_a, 1e-30), min(hi_a, 1e30), 240), [1.0],
                                         np.geomspace(1e30, hi_a, 60) if hi_a > 1e30 else [],
                                         np.geomspace(lo_a, 1e-30, 60) if lo_a < 1e-30 and origin == "today" else []]))
        grid = grid[((grid > lo_a) | (bounce is None)) & ((grid < hi_a) | (turn is None))]
        tg = self._time(grid, origin, 1e-10)
        out = np.full(tau.shape, np.nan)
        above = (tau > tg[-1]) if turn is None else np.zeros(tau.shape, bool)
        below = (tau < tg[0]) if bounce is None and origin == "today" else np.zeros(tau.shape, bool)
        if above.any() or below.any():
            warnings.warn("flrw.scale_factor: a(t) outside [1e-300, 1e300] at some of the times; returned inf "
                          "above and 0 below", RuntimeWarning, stacklevel=3)
            out[above] = math.inf
            out[below] = 0.0
        todo = ~(above | below)
        tau = tau[todo]
        u_lo = np.full(tau.shape, math.log(lo_a))
        u_hi = np.full(tau.shape, math.log(hi_a))
        j = np.searchsorted(tg, tau)
        has_lo, has_hi = j > 0, j < grid.size
        u_lo[has_lo] = np.log(grid[j[has_lo] - 1])
        u_hi[has_hi] = np.log(grid[j[has_hi]])
        mid = has_lo & has_hi
        t0, t1 = tg[np.maximum(j - 1, 0)], tg[np.minimum(j, grid.size - 1)]
        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(mid & (t1 > t0), (tau - t0) / (t1 - t0), 0.5)
        u = np.where(mid, u_lo + frac * (u_hi - u_lo), np.where(has_lo, u_lo, u_hi))
        done = np.zeros(tau.shape, bool)
        resid_ok = np.zeros(tau.shape, bool)
        for _ in range(300):
            a = np.exp(u)
            g = self._time(a, origin, rtol) - tau
            q = self._q(a)
            S, _ = self._S(a, q)
            with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
                dg = np.exp((2.0 - 0.5 * q) * u) / np.sqrt(S)      # dt/d ln a = 1/E = a^(2 - q/2)/sqrt(S/a^q)
            u_lo = np.where(g < 0, u, u_lo)
            u_hi = np.where(g > 0, u, u_hi)
            newton = np.isfinite(dg) & (dg > 0)
            with np.errstate(invalid="ignore", divide="ignore"):
                un = u + np.where(newton, -g / np.where(newton, dg, 1.0), np.nan)
            bad = ~((un >= u_lo) & (un <= u_hi)) | ~np.isfinite(un)
            un = np.where(bad, 0.5 * (u_lo + u_hi), un)
            un = np.where(g == 0, u, un)
            tol = 4 * _U * np.maximum(1.0, np.abs(u))
            small = (g == 0) | (~bad & (np.abs(un - u) <= tol)) | ((u_hi - u_lo) <= tol)
            reach = np.where(newton, dg, 0.0) * np.maximum(np.abs(un - u), u_hi - u_lo)
            resid_ok = np.abs(g) <= reach + 1e-9 * (np.abs(tau) + np.where(newton, dg, 0.0))
            done = small
            u = un
            if np.all(done):
                break
        if not np.all(done & resid_ok):
            raise FloatingPointError("flrw.scale_factor: the inversion of t(a) did not converge (residual "
                                     f"{np.max(np.abs(g[~(done & resid_ok)])):.3g} / H0)")
        out[todo] = np.exp(u)
        return out

    def scale_factor_ode(self, t, *, rtol=1e-12, atol=1e-14):
        """a(t) by integrating the acceleration equation a'' = -(H0^2/2) a^-3 sum_j S_j(a) (1 + 3 w_j(a)) with
        a(0) = 1, a'(0) = H0 (t in Gyr since today) - the second, independent route (DOP853). It passes through a
        turnaround; a contraction to a = 0 ends the solution (nan after it). The terms are divided by a^q (``_q``)
        and multiplied back as a^(q - 3), so that a up to ~1e300 is reached; if the solver fails, the times after
        the failure give nan with a RuntimeWarning (review B7-flrw C1)."""
        t = np.asarray(t, float)
        tau = t.ravel() / self.hubble_time
        out = np.full(tau.shape, np.nan)

        def rhs(_, y):
            a = np.array([y[0]])
            q = self._q(a)
            t_r, t_m, _tk, t_l, _tn, q_l, q_n, _ = self._terms(a, q)
            with np.errstate(over="ignore", invalid="ignore"):
                acc = (-0.5 * (2.0 * t_r[0] + t_m[0] + float(np.asarray(q_l * t_l).ravel()[0]) + q_n[0])
                       * float(np.power(a[0], q[0] - 3.0)))
            return [y[1], acc]

        def crunch(_, y):
            return y[0] - 1e-12
        crunch.terminal = True
        for side in (1, -1):
            sel = tau * side > 0
            if not sel.any():
                continue
            ts = np.sort(tau[sel] * side) * side
            with np.errstate(over="ignore", invalid="ignore"):
                sol = integrate.solve_ivp(rhs, (0.0, float(ts[-1])), [1.0, 1.0], method="DOP853", t_eval=ts,
                                          rtol=rtol, atol=atol, events=crunch)
            vals = np.full(ts.shape, np.nan)
            y = np.asarray(sol.y, float).reshape(2, -1) if np.size(sol.y) else np.zeros((2, 0))
            vals[: y.shape[1]] = y[0]
            if sol.status < 0:
                last = float(ts[y.shape[1] - 1]) * self.hubble_time if y.shape[1] else 0.0
                warnings.warn(f"flrw.scale_factor_ode: the solver failed ({sol.message}); a = nan after "
                              f"t - t0 = {last:.6g} Gyr", RuntimeWarning, stacklevel=2)
            order = np.argsort(tau[sel] * side)
            res = np.empty_like(vals)
            res[order] = vals
            out[sel] = res
        out[tau == 0] = 1.0
        return _scalar_or_array(out, t)


# --- constructors ---------------------------------------------------------------------------------------------------
def from_physical(h, omega_b, omega_c, *, T_cmb, N_eff, m_nu=(), n_nu=3, Ok=None, **kw):
    """A universe from the physical densities omega_x = Omega_x h^2 (as Planck samples them); flat unless Ok or OL
    is given (as for ``Background``)."""
    return Background(100.0 * h, (omega_b + omega_c) / h ** 2, Ob=omega_b / h ** 2, T_cmb=T_cmb, N_eff=N_eff,
                      m_nu=m_nu, n_nu=n_nu, Ok=Ok, **kw)


def planck2018(column="TT,TE,EE+lowE+lensing+BAO", *, H0=None):
    """Flat base-LambdaCDM of Planck 2018 (A&A 641, A6): omega_b, omega_c and H0 of Table 2's column (default
    "TT,TE,EE+lowE+lensing+BAO", posterior means) or of Table 1's "Plik best fit" (column="best fit"); T_cmb =
    2.7255 K, N_eff = 3.046, one massive neutrino of 0.06 eV and two massless (as the paper assumes). ``H0``
    overrides the tabulated value (e.g. one solved from theta_*). The parameters are those of the LambdaCDM fit
    (model-dependent; its H0 is in 3.6 sigma tension with local measurements, the paper's abstract). The engine's
    closure includes radiation (Omega_L = 1 - Omega_m - Omega_r, H(0) = H0 exactly); CosmoMC's printed Omega_L is
    1 - Omega_m (tests/test_flrw.py::_camb17)."""
    from .. import data as D
    if column == "best fit":
        p = D.PLANCK2018_BESTFIT
        ob, oc, h0 = p["omega_b"], p["omega_c"], p["H0"]
    elif column == "TT,TE,EE+lowE+lensing+BAO":
        p = D.PLANCK2018_BAO
        ob, oc, h0 = p["omega_b"][0], p["omega_c"][0], p["H0"][0]
    else:
        raise ValueError(f"unknown column {column!r}")
    h = (h0 if H0 is None else H0) / 100.0
    return from_physical(h, ob, oc, T_cmb=D.PLANCK2018_T_CMB_K, N_eff=D.PLANCK2018_N_EFF,
                         m_nu=(D.PLANCK2018_M_NU_EV,))
