# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The FLRW background (lfphys.core.cosmology.flrw, plan item P8) and the w0-wa dark energy
(lfphys.theories.models.dark_energy), each against a closed form or an independent method:

* thermal neutrinos: F(y), J(y) against 40-digit mpmath quadrature for y from 0 to 1e8; the relativistic limit
  (F - 1)/y^2 -> 5/(7 pi^2) and the non-relativistic one (the asymptotic series to 1/y^4, i.e. m n plus the kinetic
  energy); Omega_nu h^2 against m n_nu with CAMB's 94.07 eV formula;
* closed forms: Einstein-de Sitter, de Sitter, radiation only, Milne, open and closed dust (Mattig's relation as in
  Kayser et al. 1997 Eq. (B24); Hogg Eq. (17); the parametric (cycloid) solutions through turnaround and recollapse),
  flat matter + Lambda (age, Condon & Matthews 2018 Eq. (A6), (A10); a(t) in sinh^(2/3)), a matter + radiation
  sound horizon (Eisenstein & Hu 1998 Eq. (6)), a dark-energy-only universe of constant w;
* independent methods: distances and times of the general case (curvature, radiation, massive neutrinos) by mpmath
  quadrature of 1/E; q(z) by differentiating E; a(t) by integrating the acceleration equation (an ODE through the
  turnaround and the bounce) against the inversion of t(a); the stated error estimates against the actual errors;
* Planck 2018 (A&A 641, A6): Table 1's best fit (Omega_m h^2, Omega_m, age) and Table 2's column
  "TT,TE,EE+lowE+lensing+BAO" (Omega_m, Omega_L, omega_m, Omega_m h^3, age, r_*, r_drag, 100 theta_*, z_eq, k_eq;
  the dependent H0 from theta_* and D_M(z_*) = r_*/theta_*), the engine read out as the paper's CAMB (August 2017) and
  CosmoMC (July 2018) computed them (``_camb17``: their constants, closure, units, integration limits and Romberg
  rule), with tolerances from the printed digits and, for the posterior means, a bound of the difference between the
  mean of a derived quantity and its value at the mean parameters; negative controls show what each row can and
  cannot detect (the massive neutrino as dust, no massive neutrino, N_eff = 3.044, Astropy's convention);
* review B7-flrw: a(t) beyond O_L a^4's overflow, forbidden bands narrower than the scan step, the big bang of a
  dark-energy-dominated universe, the neutrino split at N_eff != 3.046, S next to a root, second routes for z_eq and
  D_A(z1, z2) in a closed universe, API edges.

The comparison with Astropy's FLRW classes (BSD-3-Clause) is in tests/external/test_ext_flrw_astropy.py: Astropy is
not in the runtime image (the licence rule keeps third-party physics libraries in the comparison image only).
"""

import functools
import math

import mpmath as mp
import numpy as np
import pytest
from scipy import constants as sc
from scipy import optimize

from lfphys.core import data as D
from lfphys.core.cosmology import flrw as F
from lfphys.theories.models import dark_energy as DE

Z = np.array([0.0, 1e-4, 0.05, 0.5, 1.0, 2.0, 5.0, 10.0, 100.0, 1100.0, 1e5])
TIGHT = 2e-13            # relative: what every closed-form test demands (the default rtol is 1e-13)


def rel(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-300))


def _check_err(bg_fun, z, ref, *, factor=1.0):
    """value within TIGHT of the reference and the stated error not smaller than the actual one."""
    v, e = bg_fun(z, with_error=True)
    v, e, ref = np.asarray(v), np.asarray(e), np.asarray(ref, float)
    actual = np.abs(v - ref)
    assert np.all(actual <= TIGHT * factor * np.maximum(np.abs(ref), 1e-300)), (v, ref, actual)
    assert np.all(actual <= np.maximum(e, 4 * 2.0 ** -53 * np.abs(ref))), (actual, e)
    assert np.all(e <= 1e-12 * np.maximum(np.abs(ref), 1e-300) + 1e-300), e


# --- thermal neutrinos ----------------------------------------------------------------------------------------------
def _mp_fd(y):
    mp.mp.dps = 40
    y = mp.mpf(y)
    pts = [mp.mpf(0)] + [v for v in (y / 4, y, 4 * y) if 0 < v < 1] + [mp.mpf(v) for v in (1, 4, 16, 64)] + [mp.inf]
    e = mp.quad(lambda x: x ** 2 * mp.sqrt(x * x + y * y) / (mp.exp(x) + 1), pts)
    p = mp.quad(lambda x: x ** 4 / mp.sqrt(x * x + y * y) / (mp.exp(x) + 1) if x > 0 else mp.mpf(0), pts)
    i0 = 7 * mp.pi ** 4 / 120
    return e / i0, p / (3 * i0)


YS = [0.0, 1e-8, 1e-4, 1e-2, 0.1, 0.5, 1.0, 2.5, 10.0, 30.0, 100.0, 357.0, 1e3, 1e4, 1e6, 1e8]


def test_fermi_dirac_integrals_against_mpmath():
    """F(y) and J(y) (energy and pressure of a thermal fermion species relative to the massless energy density)
    against 40-digit mpmath: relative error below 2e-15 (the stated bound FD_REL_ERROR is 4e-15)."""
    assert abs(F._FD_I0 / float(7 * mp.pi ** 4 / 120) - 1) <= 2 * 2.0 ** -53
    Fy = F.fermi_dirac_energy(np.array(YS))
    Jy = F.fermi_dirac_pressure(np.array(YS))
    worst = 0.0
    for y, fe, fp in zip(YS, Fy, Jy):
        re, rp = _mp_fd(y)
        worst = max(worst, abs(fe / float(re) - 1), abs(fp / float(rp) - 1))
    assert worst < 2e-15, worst
    assert F.fermi_dirac_energy(0.0) == 1.0 and abs(F.fermi_dirac_pressure(0.0) - 1 / 3) < 4e-16


def test_fermi_dirac_limits():
    """Relativistic limit: (F - 1)/y^2 -> 5/(7 pi^2) (from sqrt(x^2+y^2) = x + y^2/(2x) + ...; the next term is
    O(y^2 ln y)); w = J/F -> 1/3. Non-relativistic limit (Komatsu et al. 2011: f -> 180 zeta(3) y/(7 pi^4)), with
    the kinetic terms of sqrt(x^2+y^2) = y + x^2/(2y) - x^4/(8y^3) + ... (int x^n/(e^x+1) = (1 - 2^-n) n! zeta(n+1)):
    F = A y [1 + 7.5 zeta(5)/(zeta(3) y^2) - (708.75 zeta(7)/8)/(1.5 zeta(3) y^4)] + O(y^-6), and
    w -> 5 zeta(5)/(zeta(3) y^2)."""
    y = 1e-4
    assert (F.fermi_dirac_energy(y) - 1) / y ** 2 == pytest.approx(5 / (7 * math.pi ** 2), rel=1e-6)
    assert F.fermi_dirac_pressure(y) / F.fermi_dirac_energy(y) == pytest.approx(1 / 3, rel=1e-8)
    z3, z5, z7 = F.ZETA3, F.ZETA5, float(mp.zeta(7))
    A = 180 * z3 / (7 * math.pi ** 4)
    z9 = float(mp.zeta(9))
    for y in (357.0, 1e3, 1e4):
        asym = A * y * (1 + 7.5 * z5 / (z3 * y ** 2) - (708.75 * z7 / 8) / (1.5 * z3 * y ** 4))
        nxt = (255 / 256 * 40320 * z9 / 16) / (1.5 * z3 * y ** 6)     # the first omitted term, + x^6/(16 y^5)
        assert F.fermi_dirac_energy(y) == pytest.approx(asym, rel=2 * nxt + 1e-14)
        w = F.fermi_dirac_pressure(y) / F.fermi_dirac_energy(y)
        assert w * y ** 2 == pytest.approx(5 * z5 / z3, rel=5 * 15 / y ** 2 + 1e-12)


def test_massive_neutrino_density_today_is_m_times_n():
    """Omega_nu h^2 of a 0.06 eV species today: the non-relativistic limit m n_nu with n_nu = (3 zeta(3)/(2 pi^2))
    (k T_nu/hbar c)^3, T_nu = (N_eff/3)^(1/4)(4/11)^(1/3) T_cmb, i.e. sum m / 94.07 eV x (N_eff/3)^(3/4) with the
    94.07 eV of CAMB's constants (its formula evaluated with CODATA 2022), plus the kinetic terms of
    test_fermi_dirac_limits."""
    T, neff, m = D.PLANCK2018_T_CMB_K, D.PLANCK2018_N_EFF, D.PLANCK2018_M_NU_EV
    bg = F.Background(67.0, 0.3, T_cmb=T, N_eff=neff, m_nu=(m,))
    kappa = 8 * math.pi * sc.G
    mpc = 1e6 * sc.parsec
    inv_fac = (F.ZETA3 * 3 / 2 / math.pi ** 2 * 4 / 11
               * ((sc.k * T / sc.hbar / sc.c) ** 3 * kappa / 3 / (100 * 1000 / mpc) ** 2 / (sc.c ** 2 / sc.e)))
    fac = 1 / inv_fac
    assert fac == pytest.approx(94.07, abs=0.01)           # CAMB: "~ 94.07"; CosmoMC hard-codes 94.07
    y0 = m / (F.K_B_EV * bg.T_nu0)
    kin = 1 + 7.5 * F.ZETA5 / (F.ZETA3 * y0 ** 2) - (708.75 * float(mp.zeta(7)) / 8) / (1.5 * F.ZETA3 * y0 ** 4)
    expected = m / fac * (neff / 3) ** 0.75 * kin
    assert bg.omega_nu_massive() == pytest.approx(expected, rel=1e-9)
    # the photon density from sigma_SB equals pi^2 k^4 / (15 hbar^3 c^3) T^4 (two formulas)
    a_rad = math.pi ** 2 * sc.k ** 4 / (15 * sc.hbar ** 3 * sc.c ** 3)
    assert F.A_RAD == pytest.approx(a_rad, rel=4e-16)


# --- closed forms -----------------------------------------------------------------------------------------------------
def test_einstein_de_sitter():
    bg = F.Background(70.0, 1.0)
    DH, tH = bg.hubble_distance, bg.hubble_time
    one_minus = -np.expm1(-0.5 * np.log1p(Z))          # 1 - (1+z)^(-1/2) without cancellation
    _check_err(bg.comoving_distance, Z, 2 * DH * one_minus)
    _check_err(bg.luminosity_distance, Z, 2 * DH * (1 + Z) * one_minus)
    _check_err(bg.angular_diameter_distance, Z, 2 * DH * one_minus / (1 + Z))
    _check_err(bg.age, Z, 2 / 3 * tH * (1 + Z) ** -1.5)
    _check_err(bg.lookback_time, Z, -2 / 3 * tH * np.expm1(-1.5 * np.log1p(Z)))
    _check_err(bg.conformal_time, Z, 2 * tH / np.sqrt(1 + Z))
    _check_err(bg.particle_horizon, Z, 2 * DH / np.sqrt(1 + Z))
    # z = inf: the comoving distance to the big bang is the particle horizon, the lookback time the age
    assert bg.comoving_distance(np.inf) == pytest.approx(2 * DH, rel=1e-14)
    assert bg.lookback_time(np.array([1.0, np.inf]))[1] == pytest.approx(2 / 3 * tH, rel=1e-14)
    assert rel(bg.deceleration(Z), 0.5) < 1e-15 and rel(bg.densities(Z)["matter"], 1.0) < 1e-15
    assert rel(bg.H(Z), 70.0 * (1 + Z) ** 1.5) < 4e-16
    t = np.array([0.1, 1.0, 5.0, 9.0, 20.0])
    t0 = 2 / 3 * tH
    assert rel(bg.scale_factor(t), (t / t0) ** (2 / 3)) < 2e-14
    assert rel(bg.scale_factor_ode(t - t0), (t / t0) ** (2 / 3)) < 1e-10
    # distance modulus
    mu = bg.distance_modulus(np.array([0.01, 1.0]))
    assert rel(mu, 5 * np.log10(np.asarray(bg.luminosity_distance(np.array([0.01, 1.0]))) * 1e6 / 10)) < 1e-15


def test_de_sitter():
    """Lambda only: D_C = z c/H0, D_L = z (1+z) c/H0, lookback ln(1+z)/H0, no big bang (age and conformal time
    infinite), a = exp(H0 t), q = -1."""
    bg = F.Background(70.0, 0.0)
    DH, tH = bg.hubble_distance, bg.hubble_time
    _check_err(bg.comoving_distance, Z, Z * DH)
    _check_err(bg.luminosity_distance, Z, Z * (1 + Z) * DH)
    _check_err(bg.lookback_time, Z, np.log1p(Z) * tH)
    assert np.all(np.isinf(bg.age(Z))) and np.all(np.isinf(bg.conformal_time(Z)))
    assert rel(bg.deceleration(Z), -1.0) < 1e-15
    t = np.array([-30.0, -1.0, 0.0, 2.0, 50.0])
    assert rel(bg.scale_factor(t, since="today"), np.exp(t / tH)) < 2e-14
    assert rel(bg.scale_factor_ode(t), np.exp(t / tH)) < 1e-10
    with pytest.raises(ValueError):
        bg.scale_factor(1.0)


def test_radiation_only():
    """E = (1+z)^2: D_C = (c/H0) z/(1+z), t = 1/(2 H0 (1+z)^2), eta = 1/(H0 (1+z)), a = sqrt(2 H0 t), q = 1; the
    same universe from photons alone (T_cmb chosen so that Omega_gamma = 1)."""
    bg = F.Background(70.0, 0.0, Or_extra=1.0)
    DH, tH = bg.hubble_distance, bg.hubble_time
    _check_err(bg.comoving_distance, Z, DH * Z / (1 + Z))
    _check_err(bg.age, Z, tH / (2 * (1 + Z) ** 2))
    _check_err(bg.conformal_time, Z, tH / (1 + Z))
    assert rel(bg.deceleration(Z), 1.0) < 1e-15
    t = np.array([1e-6, 0.3, 7.0, 40.0])
    assert rel(bg.scale_factor(t), np.sqrt(2 * t / tH)) < 2e-14
    # photons alone
    rho_c0 = 3 * (70.0 / F.MPC_KM) ** 2 / (8 * math.pi * sc.G)
    T = (rho_c0 * sc.c ** 2 / F.A_RAD) ** 0.25
    ph = F.Background(70.0, 0.0, T_cmb=T)
    assert ph.Ogamma == pytest.approx(1.0, rel=4e-15)
    assert rel(ph.comoving_distance(Z), DH * Z / (1 + Z)) < 1e-13


def test_milne_and_open_closed_dust_mattig():
    """Lambda = 0 dust: D_L by Mattig's relation (Kayser, Helbig & Schramm 1997, Eq. (B24) times (1+z)^2:
    D_L = (2c/(H0 O^2)) [O z - (2 - O)(sqrt(1 + O z) - 1)]) for open (O = 0.3), flat (1) and closed (2, 3)
    universes, D_M by Hogg 1999 Eq. (17); the empty (Milne) universe O = 0 by Eq. (B25): D_A = c z (1 + z/2)/
    (H0 (1+z)^2), age 1/H0."""
    z = Z[1:]
    for Om in (0.3, 1.0, 2.0, 3.0):
        bg = F.Background(70.0, Om, OL=0.0)
        DH = bg.hubble_distance
        sq1 = np.expm1(0.5 * np.log1p(Om * z))          # sqrt(1 + O z) - 1 without cancellation
        dl = 2 * DH / Om ** 2 * (Om * z - (2 - Om) * sq1)
        # Hogg's 2 - O(1 - z) - (2 - O) sqrt(1 + O z) = O z - (2 - O)(sqrt(1 + O z) - 1)
        dm = DH * 2 * (Om * z - (2 - Om) * sq1) / (Om ** 2 * (1 + z))
        lim = z if Om < 2.5 else z[z < 10]      # O = 3: past z = 10 D_M runs through the antipode (sin < 0)
        _check_err(bg.luminosity_distance, lim, dl[: lim.size], factor=5)
        _check_err(bg.transverse_comoving_distance, lim, dm[: lim.size], factor=5)
    m = F.Background(70.0, 0.0, OL=0.0)
    assert m.Ok == 1.0
    _check_err(m.angular_diameter_distance, z, m.hubble_distance * z * (1 + z / 2) / (1 + z) ** 2, factor=5)
    assert m.age() == pytest.approx(m.hubble_time, rel=1e-14)
    assert np.isinf(m.conformal_time())


def test_open_and_closed_dust_parametric_solutions():
    """Parametric solutions of a'^2 = H0^2 (O/a + 1 - O) (derived by direct integration): closed, a = A (1 - cos u),
    H0 t = B (u - sin u), A = O/(2(O-1)), B = O/(2(O-1)^(3/2)); open, a = A (cosh u - 1), H0 t = B (sinh u - u) with
    A = O/(2(1-O)), B = O/(2(1-O)^(3/2)). The closed one through its turnaround (a_max = 2A at t = pi B) and back to
    the crunch (2 pi B), by the inversion of t(a) and by the ODE of the acceleration equation."""
    Om = 2.0
    bg = F.Background(70.0, Om, OL=0.0)
    tH = bg.hubble_time
    A, B = Om / (2 * (Om - 1)), Om / (2 * (Om - 1) ** 1.5)
    a_max, t_max = bg.turnaround()
    assert a_max == pytest.approx(2 * A, rel=1e-15) and t_max == pytest.approx(math.pi * B * tH, rel=1e-14)
    u0 = math.acos(1 - 1 / A)
    assert bg.age() == pytest.approx(B * (u0 - math.sin(u0)) * tH, rel=1e-14)
    u = np.array([0.1, 1.0, 2.0, 3.0, math.pi - 1e-3, math.pi, math.pi + 1e-3, 4.0, 5.5, 6.2])
    mp.mp.dps = 30           # u - sin u and 1 - cos u cancel at small u: the references in 30 digits
    t = np.array([float(B * (mp.mpf(v) - mp.sin(v)) * tH) for v in u])
    a_ref = np.array([float(A * (1 - mp.cos(v))) for v in u])
    # conditioning: on the way back the solver sees t' = 2 t_max - t, so a carries (2/3) 4u t/t' (a ~ t'^(2/3) near
    # the crunch, ~ t^(2/3) near the bang) besides its own 1e-14
    t_eff = np.minimum(t, 2 * t_max - t)
    cond = 2 / 3 * 4 * 2.0 ** -53 * t / t_eff
    assert np.all(np.abs(bg.scale_factor(t) / a_ref - 1) <= 2e-14 + cond)
    t_today = bg.age()
    # the ODE route away from the bang and the crunch (DOP853 at rtol 1e-12; near a -> 0 its relative error grows,
    # 1e-8 at a = 0.005)
    inner = (u > 0.4) & (u < 2 * math.pi - 0.4)
    assert rel(bg.scale_factor_ode(t[inner] - t_today), a_ref[inner]) < 1e-9
    assert np.isnan(bg.scale_factor(2 * math.pi * B * tH * 1.01))
    with pytest.raises(ValueError):
        bg.comoving_distance(-0.6)        # a = 2.5 > a_max: never reached
    Om = 0.3
    bg = F.Background(70.0, Om, OL=0.0)
    A, B = Om / (2 * (1 - Om)), Om / (2 * (1 - Om) ** 1.5)
    u = np.array([0.05, 0.5, 1.0, 2.0, 3.0])
    t = np.array([float(B * (mp.sinh(v) - v)) * bg.hubble_time for v in u])
    assert rel(bg.scale_factor(t), np.array([float(A * (mp.cosh(v) - 1)) for v in u])) < 2e-14
    u0 = math.acosh(1 + 1 / A)
    assert bg.age() == pytest.approx(B * (math.sinh(u0) - u0) * bg.hubble_time, rel=1e-14)


def test_flat_lambda_matter_closed_forms():
    """Flat matter + Lambda without radiation: the age at z (Condon & Matthews 2018, Eq. (A10); (A6) at z = 0:
    t0 = (2/(3 sqrt(O_L))) ln[(1 + sqrt(O_L))/sqrt(1 - O_L)] / H0), a(t) = (O_m/O_L)^(1/3) sinh^(2/3)(3 sqrt(O_L)
    H0 t / 2), q0 = O_m/2 - O_L, Omega_m(z) = O_m (1+z)^3/E^2."""
    Om, OL = 0.3, 0.7
    bg = F.Background(70.0, Om)
    tH = bg.hubble_time
    assert bg.OL == pytest.approx(OL, rel=1e-15)
    t0 = 2 / (3 * math.sqrt(OL)) * math.log((1 + math.sqrt(OL)) / math.sqrt(1 - OL)) * tH
    assert bg.age() == pytest.approx(t0, rel=1e-14)
    # Eq. (A10) is ln(x + sqrt(x^2 + 1)) = asinh(x), x = sqrt(O_L/(1 - O_L)) (1+z)^(-3/2) (asinh avoids the
    # cancellation of the logarithm near 1 at high z)
    tz = 2 / (3 * math.sqrt(OL)) * np.arcsinh(np.sqrt(OL / (1 - OL)) * (1 + Z) ** -1.5) * tH
    _check_err(bg.age, Z, tz)
    t = np.array([0.01, 1.0, 5.0, 13.0, 30.0, 100.0])
    a_ref = (Om / OL) ** (1 / 3) * np.sinh(1.5 * math.sqrt(OL) * t / tH) ** (2 / 3)
    assert rel(bg.scale_factor(t), a_ref) < 2e-14
    assert rel(bg.scale_factor_ode(t - t0), a_ref) < 1e-10
    assert bg.deceleration(0.0) == pytest.approx(Om / 2 - OL, rel=1e-15)
    assert rel(bg.densities(Z)["matter"], Om * (1 + Z) ** 3 / (Om * (1 + Z) ** 3 + OL)) < 1e-15
    # round trip: a(t(z)) = 1/(1+z)
    zz = np.array([0.0, 0.5, 3.0, 1000.0])
    assert rel(bg.scale_factor(bg.age(zz)), 1 / (1 + zz)) < 1e-13


def test_sound_horizon_matter_radiation_closed_form():
    """Matter + radiation (no Lambda, no curvature) with baryons: r_s = (2/(3 k_eq)) sqrt(6/R_eq) ln[(sqrt(1 + R_d)
    + sqrt(R_d + R_eq))/(1 + sqrt(R_eq))] (Eisenstein & Hu 1998, Eq. (6), with k_eq = (2 O_m H0^2 (1 + z_eq))^(1/2)/c,
    the exact form of their Eq. (3) when 1 + z_eq is kept), R = 3 rho_b/(4 rho_gamma)."""
    T, neff, h = 2.7255, 3.046, 0.7
    probe = F.Background(100 * h, 0.3, T_cmb=T, N_eff=neff)
    Orad = probe.Orad
    Om = 1.0 - Orad
    bg = F.Background(100 * h, Om, Ob=0.05, T_cmb=T, N_eff=neff)
    assert abs(bg.OL) < 1e-15 and bg.Ok == 0.0
    a_eq = Orad / Om
    R0 = 3 * 0.05 / (4 * bg.Ogamma)
    Req = R0 * a_eq
    keq = math.sqrt(2 * Om / a_eq) / bg.hubble_distance
    for zd in (1060.0, 3000.0, 100.0):
        Rd = R0 / (1 + zd)
        s = 2 / (3 * keq) * math.sqrt(6 / Req) * math.log((math.sqrt(1 + Rd) + math.sqrt(Rd + Req))
                                                         / (1 + math.sqrt(Req)))
        v, e = bg.sound_horizon(zd, with_error=True)
        assert v == pytest.approx(s, rel=1e-13) and abs(v - s) <= e + 1e-15 * s
    assert bg.z_equality() == pytest.approx(1 / a_eq - 1, rel=1e-14)


def test_general_case_against_mpmath_quadrature():
    """Curvature, radiation and massive neutrinos together (O_k = +-0.05, two massive species): D_C, D_M, the
    lookback time, the age, the conformal time by 30-digit mpmath quadrature of the engine's E(z) (an independent
    integration; E itself is checked by the closed forms and the neutrino tests)."""
    for Ok in (0.05, -0.05):
        bg = F.Background(68.0, 0.31, Ok=Ok, Ob=0.049, T_cmb=2.7255, N_eff=3.046, m_nu=(0.06, 0.1))
        mp.mp.dps = 30
        Ef = lambda z: mp.mpf(float(bg.E(float(z))))  # noqa: E731
        for z in (0.3, 2.0, 1100.0):
            dc = mp.quad(lambda x: 1 / Ef(x), [0, min(z, 1), z] if z > 1 else [0, z])
            lb = mp.quad(lambda x: 1 / ((1 + x) * Ef(x)), [0, min(z, 1), z] if z > 1 else [0, z])
            assert bg.comoving_distance(z) == pytest.approx(float(dc) * bg.hubble_distance, rel=1e-13)
            assert bg.lookback_time(z) == pytest.approx(float(lb) * bg.hubble_time, rel=1e-13)
            k = math.sqrt(abs(Ok))
            dm = (math.sinh(k * float(dc)) if Ok > 0 else math.sin(k * float(dc))) / k * bg.hubble_distance
            assert bg.transverse_comoving_distance(z) == pytest.approx(dm, rel=1e-13)
        # age and conformal time in ln a (the integrands decay as a^2 and a toward the big bang)
        Ea = lambda u: mp.mpf(float(bg.E(float(mp.exp(-u) - 1))))  # noqa: E731
        age = mp.quad(lambda u: 1 / Ea(u), [-60, -20, -8, -3, 0])
        eta = mp.quad(lambda u: mp.exp(-u) / Ea(u), [-60, -20, -8, -3, 0])
        assert bg.age() == pytest.approx(float(age) * bg.hubble_time, rel=1e-13)
        assert bg.conformal_time() == pytest.approx(float(eta) * bg.hubble_time, rel=1e-13)
        # D_A between two redshifts: sinn(chi2 - chi1)/(1 + z2); z1 = 0 gives D_A
        assert bg.angular_diameter_distance_z1z2(0.0, 2.0) == pytest.approx(bg.angular_diameter_distance(2.0),
                                                                           rel=1e-14)
        if Ok > 0:   # Hogg 1999 Eq. (19), valid for O_k >= 0
            dm1, dm2 = bg.transverse_comoving_distance(0.5), bg.transverse_comoving_distance(2.0)
            DH = bg.hubble_distance
            hogg = (dm2 * math.sqrt(1 + Ok * dm1 ** 2 / DH ** 2) - dm1 * math.sqrt(1 + Ok * dm2 ** 2 / DH ** 2)) / 3
            assert bg.angular_diameter_distance_z1z2(0.5, 2.0) == pytest.approx(hogg, rel=1e-12)


def test_densities_deceleration_and_critical_density():
    """Omega_x(z) sum to one; O_k(z) = O_k (1+z)^2/E^2; q(z) = (1/2) sum Omega_x (1 + 3 w_x) against
    q = (1+z) E'(z)/E - 1 by Richardson-extrapolated central differences (an independent route through the
    neutrino pressure); rho_crit = 3 H^2/(8 pi G)."""
    bgs = [F.planck2018(), F.Background(68.0, 0.31, Ok=-0.05, Ob=0.049, T_cmb=2.7255, N_eff=3.046,
                                        m_nu=(0.06, 0.1)),
           DE.background(68.0, 0.31, w0=-0.8, wa=-0.6, T_cmb=2.7255, N_eff=3.046, m_nu=(0.1,))]
    zs = np.array([0.0, 0.3, 1.0, 3.0, 50.0, 1100.0, 3e4])
    for bg in bgs:
        d = bg.densities(zs)
        total = sum(v for k, v in d.items() if k != "baryons")
        assert rel(total, 1.0) < 1e-15
        assert rel(d["curvature"] + 1e-300, bg.Ok * (1 + zs) ** 2 / bg.E2(zs) + 1e-300) < 1e-14
        q = bg.deceleration(zs)
        for z, qz in zip(zs, q):
            def dE(h):
                return (bg.E(z + h) - bg.E(z - h)) / (2 * h)
            h = 1e-3 * (1 + z)
            d1, d2 = dE(h), dE(h / 2)
            deriv = (4 * d2 - d1) / 3
            assert (1 + z) * deriv / bg.E(z) - 1 == pytest.approx(qz, abs=1e-8)
        rho = bg.critical_density(zs)
        H = bg.H(zs) / F.MPC_KM
        assert rel(rho, 3 * H ** 2 / (8 * math.pi * sc.G)) < 1e-15
    assert bgs[0].critical_density() / bgs[0].h ** 2 == pytest.approx(1.87834e-26, rel=1e-5)


def test_bouncing_universe_scale_factor_two_routes():
    """O_m = 0.1, O_L = 2 (O_k = -1.1): no big bang; the universe contracted to a minimum and re-expanded. a(t) since
    today by the inversion of t(a) (with the bounce in w-form) and by the acceleration ODE through the bounce."""
    bg = F.Background(70.0, 0.1, OL=2.0)
    bounce, turn = bg.roots()
    assert bounce is not None and turn is None
    S = bg.Om * bounce + bg.Ok * bounce ** 2 + bg.OL * bounce ** 4
    assert abs(S) < 1e-15
    t = np.array([-20.0, -10.0, -5.0, -1.0, 0.0, 3.0])
    a1 = bg.scale_factor(t, since="today")
    a2 = bg.scale_factor_ode(t)
    assert rel(a1, a2) < 1e-9
    assert np.min(a1) >= bounce * (1 - 1e-15)
    with pytest.raises(ValueError):
        bg.age()
    with pytest.raises(ValueError):
        bg.comoving_distance(1 / bounce)       # a < a_bounce: never reached


def test_planck_scale_factor_two_routes_and_round_trip():
    bg = F.planck2018()
    t = np.array([-13.0, -10.0, -1.0, 0.0, 2.0, 30.0])
    assert rel(bg.scale_factor(t, since="today"), bg.scale_factor_ode(t)) < 1e-9
    z = np.array([0.0, 0.5, 2.0, 1100.0, 1e6])
    assert rel(bg.scale_factor(bg.age(z)), 1 / (1 + z)) < 1e-12


def test_input_validation():
    with pytest.raises(ValueError):
        F.Background(70, 0.3, m_nu=(0.06,))                        # massive neutrinos need N_eff and T_cmb
    with pytest.raises(ValueError):
        F.Background(70, 0.3, N_eff=3.046)                          # N_eff without photons
    with pytest.raises(ValueError):
        F.Background(70, 0.3, Ok=0.1, OL=0.7)                       # inconsistent closure
    with pytest.raises(ValueError):
        F.Background(70, 0.3, T_cmb=2.7, N_eff=3, m_nu=(0.1, 0.1, 0.1, 0.1))
    with pytest.raises(ValueError):
        F.Background(70, 0.3).sound_horizon(1000.0)                  # no photons
    with pytest.raises(ValueError):
        F.Background(70, 0.3, Ob=0.4)


# --- the w0-wa model --------------------------------------------------------------------------------------------------
def test_cpl_reduces_to_lambda_and_constant_w_closed_forms():
    """(w0, wa) = (-1, 0) gives the core's Lambda universe; a flat universe of a single fluid of constant w
    (O_m = 0): E = (1+z)^(3(1+w)/2), D_C = (c/H0)[(1+z)^(1-p) - 1]/(1-p), p = 3(1+w)/2, age 2/(3(1+w)H0); w = 0 is
    Einstein-de Sitter; the continuity equation d ln rho/d ln a = -3(1 + w(a)) by central differences."""
    lam = F.planck2018()
    cpl = DE.background(lam.H0, lam.Om, -1.0, 0.0, Ob=lam.Ob, T_cmb=lam.T_cmb, N_eff=lam.N_eff, m_nu=lam.m_nu)
    for f in ("comoving_distance", "age", "lookback_time", "sound_horizon"):
        assert rel(getattr(cpl, f)(Z[1:]), getattr(lam, f)(Z[1:])) < 1e-14, f
    for w in (-0.8, -0.5, 0.0, 0.5):
        bg = DE.background(70.0, 0.0, w0=w, wa=0.0)
        p = 1.5 * (1 + w)
        DH, tH = bg.hubble_distance, bg.hubble_time
        ref = DH * np.expm1((1 - p) * np.log1p(Z)) / (1 - p) if p != 1 else DH * np.log1p(Z)
        _check_err(bg.comoving_distance, Z, ref, factor=5)
        assert bg.age() == pytest.approx(2 / (3 * (1 + w)) * tH, rel=1e-13)
    eds = F.Background(70.0, 1.0)
    w0 = DE.background(70.0, 0.0, w0=0.0, wa=0.0)
    assert rel(w0.comoving_distance(Z[1:]), eds.comoving_distance(Z[1:])) < 1e-14
    m = DE.CPL(-0.9, 0.4)
    a = np.array([0.01, 0.3, 1.0, 3.0])
    h = 1e-5
    dln = (np.log(m.density_ratio(a * math.exp(h))) - np.log(m.density_ratio(a * math.exp(-h)))) / (2 * h)
    assert rel(dln, -3 * (1 + m.w(a))) < 1e-9


# --- review B7-flrw: far future, narrow bands, the big-bang endpoint, the neutrino split, API edges ------------------
def _E_of_a(bg, a):
    """E(a) = sqrt(S/a^q) a^(q/2 - 2) without forming S (a up to ~1e300)."""
    a = np.array([a], float)
    q = bg._q(a)
    return float((np.sqrt(bg._S(a, q)[0]) * a ** (0.5 * q - 2.0))[0])


def _check_a(bg, t, ln_a_ref, *, extra=0.0):
    """a(t) (t since the big bang) against ln a_ref with the derived tolerance |delta ln a| <= E(a) (err_t + 4u tau)
    (the stated error of t(a) and the rounding of the input time, tau = t H0, carried by d ln a/d tau = E) + 4u
    max(1, |ln a|) (the solver's step) + 8u |ln a| (the reference's rounding) + extra."""
    a = np.atleast_1d(np.asarray(bg.scale_factor(t), float))
    tau = np.atleast_1d(np.asarray(t, float)) / bg.hubble_time
    assert np.all(np.isfinite(a)), a
    u = 2.0 ** -53
    for ai, ti, lr in zip(a, tau, np.atleast_1d(ln_a_ref)):
        _, err_t = bg._cumulative("t", np.array([ai]), 1e-13)
        tol = _E_of_a(bg, ai) * (float(err_t[0]) + 4 * u * ti) + 4 * u * max(1.0, abs(lr)) + 8 * u * abs(lr) + extra
        assert abs(math.log(ai) - lr) <= tol, (ai, math.exp(lr), abs(math.log(ai) - lr), tol)


def test_far_future_scale_factor_closed_forms():
    """Review B7-flrw C1: a(t) where O_L a^4 overflows binary64 (a > 1.3e77). (i) Flat matter + Lambda without
    radiation: ln a = (1/3) ln(O_m/O_L) + (2/3) ln sinh x, x = 3 sqrt(O_L) H0 t / 2 (ln sinh x = x + log1p(-e^-2x) -
    ln 2), to t = 10000 Gyr (a ~ 1e260); (ii) dark energy alone with w = -0.99 (S = O_L a^(1 - 3w) exactly): t =
    a^q/(q H0), q = 3(1 + w)/2, i.e. ln a = ln(q H0 t)/q, to a = 1e250 - its integrand at the big bang is the
    singular power 2 xi^(2 + 3w) of C3; (iii) matter + the same dark energy (the reviewer's case, where the engine
    returned 2e116 for 1e70): t(a) by 30-digit mpmath quadrature in ln a. The ODE route reaches a ~ 1e124 within
    1e-9; beyond 1e300 a = inf with a warning."""
    Om, OL = 0.3, 0.7
    bg = F.Background(70.0, Om)
    tH = bg.hubble_time
    t = np.array([100.0, 1000.0, 3000.0, 5000.0, 10000.0])
    x = 1.5 * math.sqrt(OL) * t / tH
    ln_ref = np.log(Om / OL) / 3 + 2 / 3 * (x + np.log1p(-np.exp(-2 * x)) - math.log(2))
    _check_a(bg, t, ln_ref)
    assert np.exp(ln_ref[-1]) > 1e250
    t0 = bg.age()
    ode = bg.scale_factor_ode(np.array([3000.0, 5000.0]) - t0)
    assert rel(ode, np.exp(ln_ref[2:4])) < 1e-9
    with pytest.warns(RuntimeWarning, match="1e300"):
        assert np.isinf(bg.scale_factor(20000.0))
    with pytest.warns(RuntimeWarning, match="solver failed"):
        assert np.isnan(bg.scale_factor_ode(20000.0))
    # (ii) w = -0.99 alone: the closed form for every a
    w = -0.99
    q = 1.5 * (1 + w)
    de = DE.background(70.0, 0.0, w0=w, wa=0.0)
    tq = np.array([1e-3, 1.0, 100.0, 1e4]) * de.hubble_time / q    # q H0 t = 1e-3 ... 1e4: a = 1e-200 ... 1e267
    _check_a(de, tq, np.log(q * tq / de.hubble_time) / q, extra=4 * 2.0 ** -53 / q)
    with pytest.warns(RuntimeWarning, match="1e300"):
        assert np.isinf(de.scale_factor(1e5 * de.hubble_time / q))       # a = 1e333
    # (iii) matter + w = -0.99
    mw = DE.background(70.0, 0.3, w0=w, wa=0.0)
    mp.mp.dps = 30
    Omp, OLp = mp.mpf(mw.Om), mp.mpf(mw.OL)
    for target in (1e50, 1e70, 1e120):
        U = mp.log(mp.mpf(target))
        tt = mp.quad(lambda u: 1 / mp.sqrt(Omp * mp.exp(-3 * u) + OLp * mp.exp(-3 * (1 + w) * u)),
                     [-mp.inf, -20, 0, 20, 100, U]) * mw.hubble_time
        _check_a(mw, float(tt), math.log(target))


def test_scale_factor_inversion_guard():
    """Negative control of the inversion's acceptance (C1): a t(a) with a jump of 1e-6 / H0 at a = 2 has no root
    for times inside the jump; the old acceptance (a zero step taken as convergence) would return an a there, the
    residual guard raises."""
    bg = F.Background(70.0, 0.3)
    orig = bg._time

    def broken(a, origin, rtol):
        return orig(a, origin, rtol) + 1e-6 * (np.asarray(a) > 2.0)
    bg._time = broken
    t2 = float(orig(np.array([2.0]), "bang", 1e-13)[0]) * bg.hubble_time
    with pytest.raises(FloatingPointError, match="did not converge"):
        bg.scale_factor(t2 + 0.5e-6 * bg.hubble_time)
    assert bg.scale_factor(t2 * 0.9) < 2.0           # away from the jump the inversion still works


def _lambda_crit(Om):
    """O_L at which S = O_m a + O_k a^2 + O_L a^4 (O_k = 1 - O_m - O_L) has a double root: 27 O_m^2 O_L + 4 O_k^3 =
    0 (eliminating a_L from S/a = S'(a) = 0), by 40-digit mpmath."""
    mp.mp.dps = 40
    Om = mp.mpf(Om)
    return mp.findroot(lambda OL: 27 * Om ** 2 * OL + 4 * (1 - Om - OL) ** 3, 1.7)


def test_narrow_forbidden_band_found():
    """Review B7-flrw C2: O_m = 0.3, O_L = O_L,crit (1 + eps): S < 0 on a band of width ~ 2.3 sqrt(eps) a_L around
    a_L = 0.444, narrower than roots()'s scan step for eps <= 1e-6; today's universe came from a bounce at its upper
    edge (no big bang). The bounce against the roots of the cubic S/a by 40-digit mpmath (polyroots), within its
    conditioning (rounding of S over |S'|); age() refuses ("no big bang"); a(t) since today inverts t(a) =
    -int_a^1 da/(a E) of 30-digit mpmath (tolerance: E times the integrals' documented 1e-12, plus the bounce's own
    conditioning) and agrees with the ODE route within 1e-11/sqrt(eps) (the ODE's error grows through the near-static
    phase as 1/sqrt(eps): 6e-9 at eps = 1e-8); the same through the general route (a w0-wa model with w0 = -1,
    wa = 0). Negative control: eps = -1e-8 (no band, a loitering universe with a big bang)."""
    OLc = _lambda_crit(0.3)
    for eps in (1e-6, 1e-8):
        OL = float(OLc * (1 + eps))
        for bg in (F.Background(70.0, 0.3, OL=OL), DE.background(70.0, 0.3, -1.0, 0.0, OL=OL)):
            Om, Ok, OLx = (mp.mpf(v) for v in (bg.Om, bg.Ok, bg.OL))
            ref = max(r.real for r in mp.polyroots([OLx, 0, Ok, Om], maxsteps=200, extraprec=200)
                      if abs(r.imag) < mp.mpf(10) ** -30 and 0 < r.real < 1)
            b, turn = bg.roots()
            assert b is not None and turn is None, (eps, b)
            dS = float(Om + 2 * Ok * ref + 4 * OLx * ref ** 3)
            eS = float(bg._S(np.array([float(ref)]))[1][0])         # the engine's stated rounding of S there
            assert abs(b - float(ref)) <= eS / abs(dS) + 8 * 2.0 ** -53 * float(ref), (b, ref)
            assert not bg._has_big_bang()
            with pytest.raises(ValueError, match="no big bang"):
                bg.age()
            t = np.array([-30.0, -10.0, 2.0])
            assert rel(bg.scale_factor(t, since="today"), bg.scale_factor_ode(t)) < 1e-11 / math.sqrt(eps)
            mp.mp.dps = 30
            for a in (0.46, 0.5, 0.8):
                tau = -mp.quad(lambda x: 1 / (x * mp.sqrt(Om / x ** 3 + Ok / x ** 2 + OLx)), [a, 0.6, 1])
                E = math.sqrt(float(Om / a ** 3 + Ok / a ** 2 + OLx))
                tol = E * 1e-12 * max(1.0, abs(float(tau))) + eS / abs(dS) / float(ref) + 1e-14
                got = bg.scale_factor(float(tau) * bg.hubble_time, since="today")
                assert abs(math.log(got / a)) <= tol, (a, got, tol)
    bg = F.Background(70.0, 0.3, OL=float(OLc * (1 - 1e-8)))
    assert bg.roots() == (None, None) and bg._has_big_bang() and math.isfinite(bg.age())


def test_near_root_terms_without_cancellation():
    """Found while processing review B7-flrw C2: next to a root r of S the time integrand is 1/sqrt(S), S ~ (a - r)
    S'(r); the dark-energy and neutrino terms entered S as differences t(a) - t(r) of rounded terms, whose absolute
    rounding swamped S near a near-double root (a(t) of the w0-wa route off by 2e-8 at eps = 1e-8 in
    test_narrow_forbidden_band_found). Now their changes are integrals of their derivatives (Gauss-Legendre on
    [r, a]): S next to the root against 40-digit mpmath (S(a) - S(r), F by quadrature) within the stated rounding,
    for a w0-wa model at a near-double root and for a closed universe with a 0.06 eV neutrino at its turnaround.
    Negative control: the plain differences of the rounded terms are off by more than ten times that rounding."""
    mp.mp.dps = 40
    OLc = _lambda_crit(0.3)
    de = DE.background(70.0, 0.3, -1.0, 0.0, OL=float(OLc * (1 + 1e-8)))
    nu = F.Background(70.0, 2.0, OL=0.0, T_cmb=2.7255, N_eff=3.046, m_nu=(0.06,))
    i0 = 7 * mp.pi ** 4 / 120

    def Fm(y):
        return mp.quad(lambda x: x ** 2 * mp.sqrt(x * x + y * y) / (mp.exp(x) + 1), [0, 1, 4, 16, 64, mp.inf]) / i0
    for bg, sgn, root in ((de, 1, de.roots()[0]), (nu, -1, nu.roots()[1])):
        Om, Ok, OL, Orad = (mp.mpf(v) for v in (bg.Om, bg.Ok, bg.OL, bg.Orad))
        y0 = [mp.mpf(v) for v in bg._y0]
        Onu = mp.mpf(bg.Onu_per_species)
        r = mp.mpf(root)

        def change(a):                  # the dark-energy (Lambda here) or neutrino term's change from r to a
            return Onu * sum(Fm(y * a) - Fm(y * r) for y in y0) if y0 else OL * (a ** 4 - r ** 4)

        def S(a):                       # S(a) - S(r): the root placed exactly at r, as _S_root does
            return Om * (a - r) + Ok * (a ** 2 - r ** 2) + change(a) + (OL * (a ** 4 - r ** 4) if y0 else 0)
        x = np.array([1e-4, 1e-3, 3e-2])
        a, S_eng, eS = bg._S_root(root, sgn, x)
        ref = np.array([float(S(r * (1 + sgn * mp.mpf(xi) ** 2))) for xi in x])    # a = r (1 + sgn x^2) exactly
        assert np.all(np.abs(S_eng - ref) <= eS), (S_eng, ref, eS)
        k = 4 if y0 else 3                                          # t_n or t_l of _terms
        plain = bg._terms(a)[k] - bg._terms(np.array([root]))[k][0]
        exact = np.array([float(change(mp.mpf(ai))) for ai in a])
        assert abs(plain[0] - exact[0]) > 10 * eS[0], (plain - exact, eS)     # next to the root (x = 1e-4)


def test_dark_energy_dominated_big_bang_closed_forms():
    """Review B7-flrw C3: dark energy alone with constant w (S = O_L a^(1 - 3w)): t = a^q/q, eta = a^(q-1)/(q-1) in
    1/H0, q = 3(1 + w)/2; in xi = sqrt(a) the integrands are 2 xi^alpha with alpha = 2 + 3w (t) and 3w (eta), in (-1, 0)
    for w in (-1, -2/3) and (-1/3, 0): the substitution xi = s^k makes them regular. Value within TIGHT, the stated
    error not below the actual one (the bound failed at w = -0.22 and -0.86 before, and the routine failed from
    w = -0.24 (eta) and -0.9 (t)). Negative control of the reason: for 2 x^alpha on a panel [0, 1] the difference
    between the panel and its halves (the error the rule records) is smaller than the halves' actual error when
    alpha = -0.66 (by 1/(2^(1+alpha) - 1) = 3.8), larger when alpha = 0.5."""
    for w in (-0.22, -0.26, -0.3, -0.32):
        bg = DE.background(70.0, 0.0, w0=w, wa=0.0)
        q = 1.5 * (1 + w)
        a = 1 / (1 + Z)
        _check_err(bg.conformal_time, Z, a ** (q - 1) / (q - 1) * bg.hubble_time, factor=5)
    for w in (-0.86, -0.9, -0.95, -0.99):
        bg = DE.background(70.0, 0.0, w0=w, wa=0.0)
        q = 1.5 * (1 + w)
        a = 1 / (1 + Z)
        _check_err(bg.age, Z, a ** q / q * bg.hubble_time, factor=5)
    for alpha, more in ((-0.66, True), (0.5, False)):
        def f(x):
            return 2 * x ** alpha, np.zeros_like(x)
        one = F._gl(f, np.array([0.0]), np.array([1.0]))[0][0]
        halves = F._gl(f, np.array([0.0, 0.5]), np.array([0.5, 1.0]))[0].sum()
        actual = abs(halves - 2 / (1 + alpha))
        assert (actual > abs(halves - one)) == more, (alpha, actual, abs(halves - one))


def test_neutrino_split_camb_convention():
    """Review B7-flrw C7: with N_eff != N_std the massive species keeps the standard heating (CAMB/CosmoMC:
    degeneracy default_nnu/3 per massive species, the rest massless, CosmoMC's omega_nu = m/94.07 eV (3.046/3)^(3/4)
    for any N_eff): omega_nu of one 0.06 eV species is the same at N_eff = 2.5, 3.046, 3.5, 4.0 and the massless
    radiation is (N_eff - 3.046/3) (7/8)(4/11)^(4/3) Omega_gamma; below 3.046/3 the species carries N_eff
    (CAMB's rule). Negative control: N_std=None (equal sharing, the engine before C7) heats the species with the
    excess: omega_nu 11.0 % higher at N_eff = 3.5."""
    T, m = 2.7255, 0.06
    ref = F.Background(67.0, 0.3, T_cmb=T, N_eff=3.046, m_nu=(m,))
    for neff in (2.5, 3.5, 4.0):
        bg = F.Background(67.0, 0.3, T_cmb=T, N_eff=neff, m_nu=(m,))
        assert bg.omega_nu_massive() == pytest.approx(ref.omega_nu_massive(), rel=4e-15)
        assert bg.Onu_massless == pytest.approx(F.NU_FACTOR * (neff - 3.046 / 3) * bg.Ogamma, rel=4e-15)
        # CosmoMC's formula (NR limit, its literal 94.07 eV: 6e-5 from CODATA's 94.064) times the kinetic term
        y0 = m / (F.K_B_EV * bg.T_nu0)
        kin = F.fermi_dirac_energy(y0) / (F._A_NR * y0)
        assert bg.omega_nu_massive() / kin == pytest.approx(m / 94.07 * (3.046 / 3) ** 0.75, rel=1e-4)
    low = F.Background(67.0, 0.3, T_cmb=T, N_eff=0.5, m_nu=(m,))
    assert low.Onu_massless == 0.0 and low.nu_share == 0.5
    eq = F.Background(67.0, 0.3, T_cmb=T, N_eff=3.5, m_nu=(m,), N_std=None)
    assert eq.omega_nu_massive() / ref.omega_nu_massive() == pytest.approx(1.110, abs=1e-3)
    same = F.Background(67.0, 0.3, T_cmb=T, N_eff=3.046, m_nu=(m,), N_std=None)
    assert same.omega_nu_massive() == ref.omega_nu_massive() and same.Orad == pytest.approx(ref.Orad, rel=4e-16)


def test_z_equality_exact_and_z1z2_closed_curvature_second_routes():
    """Review B7-flrw C13. (i) z_equality('exact') with two massive species against mpmath: O_m a = O_rad + sum
    O_nu F(y_i a) with F by 40-digit quadrature, solved by findroot. (ii) D_A(z1, z2) for O_k < 0 and z1 > 0 against
    the comoving distance between z1 and z2 integrated directly (30-digit mpmath of 1/E from z1 to z2) and against
    Hogg's Eq. (19) with the cosines taken with their sign (sin(b - a) = sin b cos a - cos b sin a)."""
    bg = F.Background(68.0, 0.31, Ok=-0.05, Ob=0.049, T_cmb=2.7255, N_eff=3.046, m_nu=(0.06, 0.1))
    mp.mp.dps = 40
    y0 = [mp.mpf(v) for v in bg._y0]
    i0 = 7 * mp.pi ** 4 / 120

    def Fm(y):
        return mp.quad(lambda x: x ** 2 * mp.sqrt(x * x + y * y) / (mp.exp(x) + 1), [0, 1, 4, 16, 64, mp.inf]) / i0
    g = lambda a: mp.mpf(bg.Om) * a - mp.mpf(bg.Orad) - mp.mpf(bg.Onu_per_species) * sum(Fm(y * a) for y in y0)  # noqa
    a_eq = mp.findroot(g, mp.mpf(1) / 3400)
    # tolerance: the rounding of g (16u of its terms, F to FD_REL_ERROR) over |g'| a, and brentq's 8u
    nu = mp.mpf(bg.Onu_per_species) * sum(Fm(y * a_eq) for y in y0)
    tol = (float(nu) * F.FD_REL_ERROR + 16 * 2.0 ** -53 * float(2 * mp.mpf(bg.Om) * a_eq)) / float(
        abs(mp.diff(g, a_eq)) * a_eq) + 8 * 2.0 ** -53
    assert abs(bg.z_equality() / float(1 / a_eq - 1) - 1) <= tol
    assert abs(bg.z_equality() - bg.z_equality("relativistic")) > 0.1      # the two definitions differ
    mp.mp.dps = 30
    DH, k = bg.hubble_distance, math.sqrt(-bg.Ok)
    Ef = lambda z: mp.mpf(float(bg.E(float(z))))  # noqa: E731
    for z1, z2 in ((0.5, 2.0), (1.0, 1100.0), (2.0, 3.0)):
        chi = mp.quad(lambda x: 1 / Ef(x), [z1] + [v for v in (1, 10, 100) if z1 < v < z2] + [z2])
        ref = float(mp.sin(k * chi) / k) * DH / (1 + z2)
        v = bg.angular_diameter_distance_z1z2(z1, z2)
        assert v == pytest.approx(ref, rel=1e-12)
        c1, c2 = bg.comoving_distance(z1) / DH, bg.comoving_distance(z2) / DH
        hogg = (math.sin(k * c2) * math.cos(k * c1) - math.cos(k * c2) * math.sin(k * c1)) / k * DH / (1 + z2)
        assert v == pytest.approx(hogg, rel=1e-12, abs=1e-12 * DH)


def test_api_edges():
    """Review B7-flrw C14: the densities other than 'baryons' sum to one; a negative O_m is refused with its own
    message; from_physical takes OL; D_A(z1, z2) refuses z1 > z2."""
    bg = F.planck2018()
    d = bg.densities(1.0)
    assert abs(sum(v for k, v in d.items() if k != "baryons") - 1) < 4e-16
    with pytest.raises(ValueError, match="Om"):
        F.Background(70, -0.1)
    b = F.from_physical(0.7, 0.022, 0.12, T_cmb=2.7255, N_eff=3.046, OL=0.7)
    assert b.OL == 0.7 and b.Ok == pytest.approx(1 - 0.7 - b.Orad - b.Om - b.Onu_massive, abs=1e-15)
    with pytest.raises(ValueError, match="z1 <= z2"):
        bg.angular_diameter_distance_z1z2(2.0, 0.5)
    assert bg.angular_diameter_distance_z1z2(0.5, 0.5) == 0.0


# --- Planck 2018 ------------------------------------------------------------------------------------------------------
# How Planck's numbers were computed (review B7-flrw C4, C5; sources/verification_2026-11-04_p8_flrw.md §2): Planck
# 2018 VI Sect. 2.1, "the lensed CMB power spectra computed with the August 2017 version of the camb Boltzmann code
# ... and parameter constraints are based on the July 2018 version of CosmoMC". CosmoMC's commit of 2018-07-27
# ("update docs for Planck 2018 chains", 7932d48) bundles CAMB 'Sept17' (its constants.f90 is CAMB's tag Aug2017):
# * constants.f90: "G=6.6738e-11_dl", "sigma_boltz = 5.6704e-8_dl", "Mpc = 3.085678e22_dl", "Gyr=3.1556926e16_dl"
#   (omega_gamma ~ G sigma_SB Mpc^2 T^4: 7.0e-5 below CODATA 2022; its Gyr is 365.2422 d, the engine's Julian);
# * modules.f90: age "DeltaPhysicalTimeGyr(0.0_dl,1.0_dl)" = rombint(dtda, a1, a2, 1d-4/exp(AccuracyBoost-1))*Mpc/c/Gyr;
#   "rs =rombint(dsound_da_exact,1d-8,1/(z_star+1),1d-6)" (and z_drag); "DA = AngularDiameterDistance(z_star)/
#   (1/(z_star+1))" through DeltaTime at tol/1000/exp(AccuracyBoost-1), tol = 1.0d-4; z_eq with the massive species at
#   their relativistic density; "ThermoDerivedParams( derived_kEQ ) = 1/(a_eq*dtauda(a_eq))";
# * subroutines.f90 rombint: stops after more than 5 iterations once |1 - gmax/g0| < tol (Richardson to order 5);
# * CosmoMC batch3/common.ini: "accuracy_level = 1" (AccuracyBoost = 1); CosmologyParameterizations.f90:
#   "CMB%omnuh2=Params(6)/neutrino_mass_fac*(standard_neutrino_neff/3)**0.75_mcp" (94.07, 3.046) and
#   "CMB%omv = 1- CMB%omk - CMB%omb - CMB%omdm": Omega_Lambda = 1 - Omega_m, the radiation left out of the closure, so
#   that CAMB's flat universe has H(z = 0) = H0 sqrt(1 + Omega_r).
# ``_camb17`` builds the engine's universe as CosmoMC set it up and reads it out with CAMB's numerics (the engine's
# integrands through CAMB's Romberg rule, its limits and units), so that the comparison tests the background physics
# (densities, the neutrino, N_eff, the integrals) rather than the reference's conventions and numerical tolerances.
CAMB17_G, CAMB17_SIGMA, CAMB17_MPC_M, CAMB17_GYR_S = 6.6738e-11, 5.6704e-8, 3.085678e22, 3.1556926e16
COSMOMC_NU_MASS_FAC, COSMOMC_NEFF_STD = 94.07, 3.046
CAMB17_T = D.PLANCK2018_T_CMB_K * (CAMB17_G * CAMB17_SIGMA * CAMB17_MPC_M ** 2
                                   / (sc.G * sc.Stefan_Boltzmann * F.MPC_M ** 2)) ** 0.25   # same omega_gamma
CAMB17_AGE_UNITS = (CAMB17_MPC_M / F.MPC_M) * (F.GYR_S / CAMB17_GYR_S)                      # = 1 + 2.149e-5


def _romberg_camb(f, a, b, tol):
    """Romberg integration with CAMB's stopping rule (rombint, subroutines.f90, as described above; the algorithm is
    the textbook one): trapezoid refinements with Richardson extrapolation to order 5, stopped after more than 5
    iterations once the relative change of the estimate is below tol (at most 20)."""
    h = 0.5 * (b - a)
    gmax = h * float(f(np.array([a]))[0] + f(np.array([b]))[0])
    g = [gmax] + [0.0] * 5
    nint, error, i, g0 = 1, 1e20, 0, gmax
    while True:
        i += 1
        if i > 20 or (i > 5 and abs(error) < tol):
            return g0
        x = a + (2 * np.arange(1, nint + 1) - 1) * h
        g0 = 0.5 * g[0] + h * float(np.sum(f(x)))
        h *= 0.5
        nint *= 2
        jmax = min(i, 5)
        fourj = 1.0
        for j in range(jmax):
            fourj *= 4.0
            g1 = g0 + (g0 - g[j]) / (fourj - 1.0)
            g[j] = g0
            g0 = g1
        error = 1.0 - gmax / g0 if abs(g0) > tol else gmax
        gmax = g0
        g[jmax] = g0


def _camb17(H0, ob, oc, zs=None, zd=None, *, N_eff=D.PLANCK2018_N_EFF, nu="camb", numerics=True, closure=True):
    """Planck's derived numbers as CAMB Sept17 / CosmoMC Jul 2018 computed them, from the engine's background for the
    parameters (H0, omega_b, omega_c) (and z_*, z_drag): omega_gamma of CAMB's constants (through the equivalent
    T_cmb), CosmoMC's omega_nu = m/94.07 eV x (3.046/3)^(3/4) for a thermal species at the standard heating,
    Omega_Lambda = 1 - Omega_m (the same physical densities in the engine's flat universe with H0' = H0 sqrt(1 +
    Omega_r); ``closure=False``: the engine's closure with radiation), and (``numerics``) CAMB's Romberg rule, r_s
    from a = 1e-8; the age in CAMB's Gyr and Mpc.
    ``nu``: 'camb'; for the negative controls 'astropy' (density N_eff/3 times that of the mass m at the standard
    temperature), 'dust' (the species' omega_nu in the dust at all times, two massless species) or 'none' (three
    massless species, no 0.06 eV neutrino)."""
    h = H0 / 100.0
    T, m = CAMB17_T, D.PLANCK2018_M_NU_EV
    kw = dict(T_cmb=T, N_eff=N_eff, n_nu=3)
    if nu in ("camb", "astropy"):
        m = m * ((N_eff / 3) ** 0.25 if nu == "astropy" else 1.0)
        probe = F.from_physical(h, ob, oc, m_nu=(m,), **kw)
        nr = probe.Onu_per_species * F._A_NR * probe._y0[0] * h * h          # m n_nu: the non-relativistic limit
        om_nu = m / COSMOMC_NU_MASS_FAC * (COSMOMC_NEFF_STD / 3) ** 0.75 if nu == "camb" else nr
        kw["m_nu"] = (m * om_nu / nr,)
        ob_bg = ob
    elif nu == "dust":
        om_nu = D.PLANCK2018_M_NU_EV / COSMOMC_NU_MASS_FAC * (COSMOMC_NEFF_STD / 3) ** 0.75
        ob_bg, om_nu = ob + om_nu, 0.0
        kw.update(N_eff=N_eff * 2 / 3, n_nu=2)
    elif nu == "none":
        ob_bg, om_nu = ob, 0.0
    else:
        raise ValueError(nu)
    om_tot = ob_bg + oc + om_nu
    omega_L = h * h - om_tot
    bg0 = F.from_physical(h, ob_bg, oc, **kw)
    if closure:
        h2p = ob_bg + oc + bg0.omega_nu_massive() + bg0.Orad * h * h + omega_L
        bg = F.from_physical(math.sqrt(h2p), ob_bg, oc, Ok=0.0, OL=omega_L / h2p, **kw)
    else:
        bg = bg0
    out = {"Omega_m": om_tot / h ** 2, "Omega_L": omega_L / h ** 2, "omega_m": om_tot, "Omega_m_h3": om_tot * h,
           "bg": bg}
    DH, tH = bg.hubble_distance, bg.hubble_time
    R0 = 3 * bg.Ob / (4 * bg.Ogamma)

    def dtauda(a):
        return 1.0 / np.sqrt(bg._S(np.asarray(a, float))[0])

    def dtda(a):
        return np.asarray(a, float) * dtauda(a)

    def dsound(a):
        return dtauda(a) / np.sqrt(3.0 * (1.0 + R0 * np.asarray(a, float)))
    if numerics:
        out["age"] = _romberg_camb(dtda, 0.0, 1.0, 1e-4) * tH * CAMB17_AGE_UNITS
    else:
        out["age"] = bg.age() * CAMB17_AGE_UNITS
    if zs is not None:
        if numerics:
            rs = _romberg_camb(dsound, 1e-8, 1 / (1 + zs), 1e-6) * DH
            dm = _romberg_camb(dtauda, 1 / (1 + zs), 1.0, 1e-7) * DH
            rd = _romberg_camb(dsound, 1e-8, 1 / (1 + zd), 1e-6) * DH
        else:
            rs, dm, rd = bg.sound_horizon(zs), bg.transverse_comoving_distance(zs), bg.sound_horizon(zd)
        zeq = bg.z_equality("relativistic")
        out.update(r_star=rs, r_drag=rd, D_M=dm, theta=100 * rs / dm, z_eq=zeq,
                   k_eq=float(bg.H(zeq)) / (1 + zeq) / F.C_KM_S)
    return out


def _deriv(f, x, h):
    return (f(x + h) - f(x - h)) / (2 * h)


def _bf(**kw):
    p = dict(D.PLANCK2018_BESTFIT)
    p.update(kw)
    return F.from_physical(p["H0"] / 100, p["omega_b"], p["omega_c"], T_cmb=D.PLANCK2018_T_CMB_K,
                           N_eff=D.PLANCK2018_N_EFF, m_nu=(D.PLANCK2018_M_NU_EV,))


def test_camb17_readout_shifts():
    """The size of each convention of CAMB Sept17/CosmoMC, at Table 2's BAO column (recorded in the verification
    note): CAMB's Gyr and Mpc raise the age's number by 2.149e-5 and its Romberg rule (tol 1e-4) lowers it by
    2.04e-5; r_s from a = 1e-8 is 1.85e-5 short; the closure without radiation (H(0) = H0 (1 + 4.6e-5)) lowers the age
    by 1.7e-5 and raises 100 theta_* by 8e-6; CAMB's constants lower omega_gamma by 7.0e-5 (z_eq +0.24)."""
    P = D.PLANCK2018_BAO
    args = (P["H0"][0], P["omega_b"][0], P["omega_c"][0], P["z_star"][0], P["z_drag"][0])
    assert CAMB17_AGE_UNITS - 1 == pytest.approx(2.149e-5, abs=1e-8)
    assert (CAMB17_T / D.PLANCK2018_T_CMB_K) ** 4 - 1 == pytest.approx(-7.01e-5, abs=1e-7)
    full, smooth = _camb17(*args), _camb17(*args, numerics=False)
    assert full["age"] / smooth["age"] - 1 == pytest.approx(-2.04e-5, abs=0.02e-5)       # CAMB's Romberg (tol 1e-4)
    assert full["r_star"] / smooth["r_star"] - 1 == pytest.approx(-1.85e-5, abs=0.01e-5)  # the missing int_0^1e-8
    assert abs(full["D_M"] / smooth["D_M"] - 1) < 1e-9                                      # DeltaTime at 1e-7
    open_ = _camb17(*args, numerics=False, closure=False)
    assert smooth["bg"].h / open_["bg"].h - 1 == pytest.approx(0.5 * open_["bg"].Orad, rel=1e-3)
    assert smooth["age"] / open_["age"] - 1 == pytest.approx(-1.7e-5, abs=0.1e-5)
    assert smooth["theta"] - open_["theta"] == pytest.approx(8e-6, abs=1e-6)
    std = _bao(P["H0"][0], P["omega_b"][0], P["omega_c"][0])
    assert smooth["z_eq"] - std.z_equality("relativistic") == pytest.approx(0.24, abs=0.01)


def test_planck2018_best_fit_table1():
    """Table 1, "Plik best fit": one model, so its derived numbers follow from its own parameters (CAMB's readout,
    ``_camb17``). Tolerance = the printed rounding of the output plus that of the inputs (H0 to 0.005, omega_b to
    5e-7, omega_c to 5e-6) carried by the engine's derivatives. Omega_m h^2 = omega_b + omega_c + omega_nu confirms
    that one ~0.06 eV species is counted in Omega_m - not its convention: at Planck's printed precision the CAMB,
    Astropy and Mangano et al. conventions are indistinguishable (test_planck2018_omega_m_cannot_see_the_convention);
    the engine's convention is pinned by test_massive_neutrino_density_today_is_m_times_n. Measured: the readout's
    age 13.797143 (+4.3e-5 Gyr, 0.07 of the budget 6.5e-4), the engine's own 13.797366 (+2.7e-4, 0.41)."""
    p = D.PLANCK2018_BESTFIT
    c = _camb17(p["H0"], p["omega_b"], p["omega_c"])
    bg = _bf()
    assert abs(bg.Om_total * bg.h ** 2 - p["omega_m"]) <= 5e-6 + 5e-7 + 5e-6
    assert abs(c["omega_m"] - p["omega_m"]) <= 5e-6 + 5e-7 + 5e-6
    tol_Om = 5e-5 + 2 * bg.Om_total * 0.005 / p["H0"] + (5e-7 + 5e-6) / bg.h ** 2
    assert abs(c["Omega_m"] - p["Omega_m"]) <= tol_Om
    assert abs(bg.Om_total - p["Omega_m"]) <= tol_Om
    age = lambda **kw: _bf(**kw).age()  # noqa: E731
    tol_age = (5e-5 + abs(_deriv(lambda x: age(H0=x), p["H0"], 0.01)) * 0.005
               + abs(_deriv(lambda x: age(omega_b=x), p["omega_b"], 1e-5)) * 5e-7
               + abs(_deriv(lambda x: age(omega_c=x), p["omega_c"], 1e-4)) * 5e-6)
    assert abs(c["age"] - p["age_Gyr"]) <= tol_age, (c["age"], tol_age)


def _nonlinearity_bound(fun, centre, sig):
    """(1/2) sum_ij |d2f/dpi dpj| s_i s_j: a bound of |E f(p) - f(E p)| to second order for any correlations
    (|cov_ij| <= s_i s_j)."""
    keys = list(centre)
    out = 0.0
    for i, ki in enumerate(keys):
        for kj in keys[i:]:
            hi, hj = 0.5 * sig[ki], 0.5 * sig[kj]

            def at(di, dj):
                c = dict(centre)
                c[ki] += di
                c[kj] += dj
                return fun(**c)
            if ki == kj:
                d2 = (at(hi, 0) - 2 * fun(**centre) + at(-hi, 0)) / hi ** 2
                out += 0.5 * abs(d2) * sig[ki] ** 2
            else:
                d2 = (at(hi, hj) - at(hi, -hj) - at(-hi, hj) + at(-hi, -hj)) / (4 * hi * hj)
                out += abs(d2) * sig[ki] * sig[kj]
    return out


def _bao(H0, ob, oc):
    return F.from_physical(H0 / 100, ob, oc, T_cmb=D.PLANCK2018_T_CMB_K, N_eff=D.PLANCK2018_N_EFF,
                           m_nu=(D.PLANCK2018_M_NU_EV,))


_ROWS = ("Omega_m", "Omega_L", "omega_m", "Omega_m_h3", "age", "r_star", "r_drag", "theta", "z_eq", "k_eq")


@functools.lru_cache(maxsize=None)
def _bao_budgets():
    """Per row of Table 2's BAO column: (printed value, budget). Budget = the printed rounding (half a unit of the
    last digit) of the output, of the inputs omega_b, omega_c, H0 and of z_*, z_drag (through the engine's
    derivatives), and the second-order bound of |mean f - f(mean)| (``_nonlinearity_bound`` with the printed
    standard deviations: the table gives posterior means of each quantity). CAMB's numerics are not in the budget:
    ``_camb17`` reproduces them."""
    P = D.PLANCK2018_BAO
    c = {"H0": P["H0"][0], "ob": P["omega_b"][0], "oc": P["omega_c"][0]}
    s = {"H0": P["H0"][1], "ob": P["omega_b"][1], "oc": P["omega_c"][1]}
    rnd_in = {"H0": 0.005, "ob": 5e-6, "oc": 5e-6}
    zs, zd = P["z_star"][0], P["z_drag"][0]
    bg = _bao(**c)

    def budget(fun, rnd_out, extra=0.0):
        r = rnd_out + extra + _nonlinearity_bound(fun, c, s)
        for k, d in rnd_in.items():
            r += abs(_deriv(lambda x: fun(**{**c, k: x}), c[k], 10 * d)) * d
        return r

    def zeq(**k):
        return _bao(**k).z_equality("relativistic")

    def keq(**k):
        b = _bao(**k)
        z = b.z_equality("relativistic")
        return float(b.H(z)) / (1 + z) / F.C_KM_S
    th = lambda **k: 100 * _bao(**k).sound_horizon(zs) / _bao(**k).transverse_comoving_distance(zs)  # noqa: E731
    dz = {z: abs(_deriv(lambda x: bg.sound_horizon(x), z, 0.1)) * 0.005 for z in (zs, zd)}
    dth_z = abs(_deriv(lambda z: 100 * bg.sound_horizon(z) / bg.transverse_comoving_distance(z), zs, 0.1)) * 0.005
    out = {
        "Omega_m": (P["Omega_m"][0], budget(lambda **k: _bao(**k).Om_total, 5e-5)),
        "Omega_L": (P["Omega_L"][0], budget(lambda **k: 1 - _bao(**k).Om_total, 5e-5)),
        "omega_m": (P["omega_m"][0], budget(lambda **k: _bao(**k).Om_total * k["H0"] ** 2 / 1e4, 5e-6)),
        "Omega_m_h3": (P["Omega_m_h3"][0], budget(lambda **k: _bao(**k).Om_total * (k["H0"] / 100) ** 3, 5e-6)),
        "age": (P["age_Gyr"][0], budget(lambda **k: _bao(**k).age(), 5e-4)),
        "r_star": (P["r_star_Mpc"][0], budget(lambda **k: _bao(**k).sound_horizon(zs), 0.005, dz[zs])),
        "r_drag": (P["r_drag_Mpc"][0], budget(lambda **k: _bao(**k).sound_horizon(zd), 0.005, dz[zd])),
        "theta": (P["100theta_star"][0], budget(th, 5e-6, dth_z)),
        "z_eq": (P["z_eq"][0], budget(zeq, 0.5)),
        "k_eq": (P["k_eq_per_Mpc"][0], budget(keq, 5e-7)),
    }
    dth_dH0 = abs(_deriv(lambda x: th(**{**c, "H0": x}), c["H0"], 0.05))
    return out, dth_dH0


def _bao_rows(**kw):
    P = D.PLANCK2018_BAO
    return _camb17(P["H0"][0], P["omega_b"][0], P["omega_c"][0], P["z_star"][0], P["z_drag"][0], **kw)


def test_planck2018_table2_bao_column():
    """Table 2, "TT,TE,EE+lowE+lensing+BAO" (posterior means): CAMB's readout of the engine (``_camb17``) at the mean
    parameters against the means of the derived quantities, z_* and z_drag taken from the table (recombination is
    not computed: the rows test the background integrals, the densities, the neutrino and N_eff, not the physics of
    recombination). Each row within its budget (``_bao_budgets``); measured diff/budget: Omega_m -0.27, Omega_L
    +0.27 (= the Omega_m row: CosmoMC's Omega_L is 1 - Omega_m), omega_m -0.32, Omega_m h^3 -0.23, age -0.02,
    r_* -0.32, r_drag +0.20, 100 theta_* -0.04, z_eq +0.52, k_eq -0.28 (the verification note's table). H0 solved
    from theta_* is the theta_* row inverted (not an independent agreement): its tolerance is that row's budget over
    |d theta/d H0|."""
    budgets, dth_dH0 = _bao_budgets()
    c = _bao_rows()
    for k in _ROWS:
        printed, b = budgets[k]
        assert abs(c[k] - printed) <= b, (k, c[k], printed, b)
    P = D.PLANCK2018_BAO
    zs, target = P["z_star"][0], P["100theta_star"][0]
    H0_sol = optimize.brentq(lambda H: _camb17(H, P["omega_b"][0], P["omega_c"][0], zs, zs)["theta"] - target,
                             66.0, 69.0, xtol=1e-7)
    assert abs(H0_sol - P["H0"][0]) <= budgets["theta"][1] / dth_dH0
    # D_M(z_*) = r_*/theta_* from the paper's two printed numbers (the dependent pair of rows)
    dm_paper = P["r_star_Mpc"][0] / (target / 100)
    dm_rnd = dm_paper * (budgets["r_star"][1] / P["r_star_Mpc"][0] + budgets["theta"][1] / target)
    assert abs(c["D_M"] - dm_paper) <= dm_rnd


def test_planck2018_rows_detect_and_miss():
    """Negative controls: what the Table 2 rows can and cannot see (diff/budget, measured, in the verification note).
    Detected (|diff| > budget): the massive species as dust (r_*, r_drag, theta_*, z_eq, k_eq; the neutrino's
    relativistic phase sets the sound horizon), no massive neutrino (Omega_m, Omega_L, omega_m, Omega_m h^3, age,
    theta_*), N_eff = 3.044 instead of 3.046 (theta_* by 1.2, z_eq by 1.7 budgets; r_drag 1.00, k_eq 0.85: not).
    Not detected: Astropy's neutrino convention (every row within its budget), nor CAMB's own conventions (C4): the
    engine's values without the readout pass every row as well (largest |diff|/budget 0.58, k_eq)."""
    budgets, _ = _bao_budgets()

    def score(c):
        return {k: (c[k] - budgets[k][0]) / budgets[k][1] for k in _ROWS}
    dust, none, neff = score(_bao_rows(nu="dust")), score(_bao_rows(nu="none")), score(_bao_rows(N_eff=3.044))
    for k in ("r_star", "r_drag", "theta", "z_eq", "k_eq"):
        assert abs(dust[k]) > 100, (k, dust[k])
    for k in ("Omega_m", "omega_m", "Omega_m_h3", "age", "theta"):
        assert abs(none[k]) > 5, (k, none[k])
    for k in ("theta", "z_eq"):
        assert abs(neff[k]) > 1, (k, neff[k])
    astropy = score(_bao_rows(nu="astropy"))
    assert all(abs(v) <= 1 for v in astropy.values()), astropy
    P = D.PLANCK2018_BAO
    std = _bao(P["H0"][0], P["omega_b"][0], P["omega_c"][0])
    zs, zd = P["z_star"][0], P["z_drag"][0]
    zeq = std.z_equality("relativistic")
    own = score({"Omega_m": std.Om_total, "Omega_L": std.OL, "omega_m": std.Om_total * std.h ** 2,
                 "Omega_m_h3": std.Om_total * std.h ** 3, "age": std.age(), "r_star": std.sound_horizon(zs),
                 "r_drag": std.sound_horizon(zd),
                 "theta": 100 * std.sound_horizon(zs) / std.transverse_comoving_distance(zs), "z_eq": zeq,
                 "k_eq": float(std.H(zeq)) / (1 + zeq) / F.C_KM_S})
    assert all(abs(v) <= 1 for v in own.values()), own


def test_planck2018_omega_m_cannot_see_the_convention():
    """Table 1's Omega_m h^2 = 0.14314 (rounding 5e-6, inputs 5.5e-6): passes with the CAMB/CosmoMC convention, with
    Astropy's (Komatsu et al. 2011 Eq. (24)), with Mangano et al. 2005's sum m / 93.14 eV and with sum m / 94.07 eV
    without the (N_eff/3)^(3/4); fails only without the massive species (negative control): the row confirms that
    one ~0.06 eV species is in Omega_m, not how its density is computed (review B7-flrw C6)."""
    p = D.PLANCK2018_BESTFIT
    tol = 5e-6 + 5e-7 + 5e-6
    base = p["omega_b"] + p["omega_c"]
    m, neff = D.PLANCK2018_M_NU_EV, D.PLANCK2018_N_EFF
    camb = _bf().omega_nu_massive()
    astropy = F.from_physical(p["H0"] / 100, p["omega_b"], p["omega_c"], T_cmb=D.PLANCK2018_T_CMB_K, N_eff=neff,
                              m_nu=(m * (neff / 3) ** 0.25,)).omega_nu_massive()
    for om_nu in (camb, astropy, m / 93.14, m / 94.07):
        assert abs(base + om_nu - p["omega_m"]) <= tol, om_nu
    assert abs(base - p["omega_m"]) > 30 * tol


def test_planck2018_neutrino_convention_effects():
    """What the neutrino treatment changes, measured (recorded in sources/verification_2026-11-04_p8_flrw.md), at
    Table 1's best fit (age) and Table 2's BAO column (100 theta_* at z_* = 1089.80):
    (a) the engine (CAMB's convention: temperature (N_std/3)^(1/4) T_nu, the physical mass);
    (b) Astropy's convention (density N_eff/3 times that of the mass m at the standard temperature) = the engine
        with the mass multiplied by (N_eff/3)^(1/4): omega_nu +0.38 %; age -6.6e-5 Gyr, 100 theta_* +6e-6, both below
        the paper's last digits (1e-4 Gyr, 1e-5);
    (c) the massive species as dust at all times (two massless species plus omega_nu in the dust): age +9.6e-5 Gyr,
        but 100 theta_* +0.034 (about 100 sigma): the relativistic phase of the neutrino before recombination sets
        the sound horizon, so a background without it misses the paper's acoustic scale."""
    p = D.PLANCK2018_BESTFIT
    a = _bf()
    s = (D.PLANCK2018_N_EFF / 3) ** 0.25
    b = F.from_physical(p["H0"] / 100, p["omega_b"], p["omega_c"], T_cmb=D.PLANCK2018_T_CMB_K,
                        N_eff=D.PLANCK2018_N_EFF, m_nu=(D.PLANCK2018_M_NU_EV * s,))
    c = F.from_physical(p["H0"] / 100, p["omega_b"] + a.omega_nu_massive(), p["omega_c"],
                        T_cmb=D.PLANCK2018_T_CMB_K, N_eff=D.PLANCK2018_N_EFF * 2 / 3, n_nu=2)
    assert abs(b.omega_nu_massive() / a.omega_nu_massive() - s) < 2e-4
    assert abs(b.age() - a.age()) < 1e-4 and abs(c.age() - a.age()) < 1e-4
    zs = D.PLANCK2018_BAO["z_star"][0]
    P = D.PLANCK2018_BAO

    def th(bg):
        return 100 * bg.sound_horizon(zs) / bg.transverse_comoving_distance(zs)
    ab = _bao(P["H0"][0], P["omega_b"][0], P["omega_c"][0])
    bb = F.from_physical(P["H0"][0] / 100, P["omega_b"][0], P["omega_c"][0], T_cmb=D.PLANCK2018_T_CMB_K,
                         N_eff=D.PLANCK2018_N_EFF, m_nu=(D.PLANCK2018_M_NU_EV * s,))
    cb = F.from_physical(P["H0"][0] / 100, P["omega_b"][0] + ab.omega_nu_massive(), P["omega_c"][0],
                         T_cmb=D.PLANCK2018_T_CMB_K, N_eff=D.PLANCK2018_N_EFF * 2 / 3, n_nu=2)
    assert abs(th(bb) - th(ab)) < 1e-5
    assert abs(th(cb) - th(ab)) > 30 * P["100theta_star"][1]


def test_planck2018_constructor_matches_data():
    bg = F.planck2018()
    assert bg.H0 == D.PLANCK2018_BAO["H0"][0] and bg.T_cmb == 2.7255 and bg.N_eff == 3.046
    assert bg.m_nu == (0.06,) and bg.Ok == 0.0
    assert (bg.Om * bg.h ** 2) == pytest.approx(0.02242 + 0.11933, rel=1e-15)
    assert D.FIXSEN2009_T_CMB_K[0] == pytest.approx(D.PLANCK2018_T_CMB_K, abs=D.FIXSEN2009_T_CMB_K[1])
