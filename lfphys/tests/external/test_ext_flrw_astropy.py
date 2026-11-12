# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The engine's FLRW background (``lfphys.core.cosmology.flrw``, plan item P8) and its w0-wa dark energy
(``lfphys.theories.models.dark_energy``) against Astropy's FLRW classes (``astropy.cosmology``, BSD-3-Clause).

Universes (the same binary64 parameters on both sides):
* flat LCDM without radiation (H0 = 70, Om0 = 0.3): Astropy uses closed forms (Baes et al. 2017's hypergeometric
  comoving distance, the asinh age, the lookback time as age(0) - age(z));
* flat LCDM with photons and massless neutrinos (Planck 2018 BAO column's H0 and Om0, T_cmb = 2.7255 K,
  N_eff = 3.046); open (Om0 = 0.3, Ode0 = 0.6) and closed (Om0 = 0.35, Ode0 = 0.75) LCDM with the same radiation;
  flat w0-wa (w0 = -0.9, wa = 0.2) with the same radiation: Astropy integrates with scipy's QUADPACK;
* Planck 2018 with one 0.06 eV neutrino. Astropy's convention differs from the engine's (CAMB's): Astropy's massive
  species has N_eff/3 times the density of a Fermi-Dirac gas of mass m at T_nu = (4/11)^(1/3) T_cmb; the engine's
  has the temperature (N_std/3)^(1/4) (4/11)^(1/3) T_cmb (N_std = N_eff = 3.046 here) and the physical mass. The two
  coincide exactly when the engine is given the mass m (N_eff/3)^(1/4) (rho = T^4 F(m/T) scales so); that is what the
  rows compare. Astropy evaluates F by Komatsu et al. 2011's Eq. (26) fit, which "underestimates f(y) by 0.1% at
  y ~ 2.5, and overestimates by 0.35% at y ~ 10. The errors are smaller than these values at other y's".

Quantities at z = 0.001 ... 1000: the comoving, transverse comoving, angular-diameter and luminosity distances, the
distance modulus, the lookback time, the age, H(z), Omega_m(z), Omega_de(z), Omega_k(z) (curved universes), the
critical density; today's Omega_gamma, Omega_nu, rho_crit, T_nu; the neutrino density relative to photons (massive
case); D_A between two redshifts.

Tolerances (derived; the sum of the two sides' bounds):
* engine: the error bound its integrals return (``with_error=True``); for algebraic quantities (E, Omega_x(z),
  rho_crit) 16u per side times the conditioning sum|terms| / E^2 of the Friedmann sum (curvature can be negative).
* Astropy's integrals: QUADPACK's request (scipy.integrate.quad defaults epsabs = epsrel = 1.49e-8, which Astropy
  does not change): 1.49e-8 max(1, |I|) in the units of the dimensionless integral, times c/H0 or 1/H0 ("quad
  1.49e-8"). Astropy's closed forms (flat, no radiation): a difference of two terms each evaluated with a few
  roundings and one hyp2f1 or asinh: 64u times the sum of the moduli of the two terms ("closed form 64u"; scipy states
  no bound for hyp2f1, so the measured lib err against the exact value is shown with every row).
* the massive neutrino through Komatsu's fit: 0.35 % of its density, i.e. 0.35 % x Omega_nu,massive(z) relative for
  rho_crit and Omega_x(z), half of it for E and H, and half of its maximum over the integration range for the
  integrals ("+ Komatsu fit 0.35 %").
* Astropy's 7/8 (4/11)^(4/3) is the 11-digit literal 0.22710731766 (relative 1.05e-12 below the exact value): that
  fraction of the neutrinos' share is added where neutrinos are present.
* rows that combine others (D_M, D_A, D_L, mu): the bounds propagated by the derivative, plus 2u per extra operation.

Exact references: the same equations in 30-digit mpmath for the same binary64 parameters (the engine's density
parameters; Astropy's own Omega_gamma0 and Omega_nu0 agree with them to the rows "Ogamma0", "Onu0" below), for every
universe without massive neutrinos; for the neutrino density row, F(y) by 30-digit quadrature.
"""

from __future__ import annotations

import functools
import math

import astropy
import astropy.units as u
import mpmath as mp
import numpy as np
import pytest
from astropy.cosmology import FlatLambdaCDM, Flatw0waCDM, LambdaCDM

from lfphys.core.cosmology import flrw as F
from lfphys.theories.models import dark_energy as DE

from _common import Row, check, gamma, params

GROUP = "FLRW (astropy)"
U = 2.0 ** -53
ZS = [0.001, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 100.0, 1000.0]
QUAD = 1.49e-8                    # scipy.integrate.quad: epsabs = epsrel = 1.49e-8
KOMATSU = 0.0035                  # Komatsu et al. 2011, after Eq. (26): the fit's largest error
ASTROPY_NU_LITERAL = 0.22710731766
T_CMB, N_EFF = 2.7255, 3.046
H0_P, OM_P = 67.66, (0.02242 + 0.11933) / 0.6766 ** 2


# Measured 2026-11-04 (test_astropy_closed_age_is_a_quadpack_error pins the cause): Astropy's age at z = 1000 of the
# closed universe comes from scipy.integrate.quad (QAGI on [z, inf)) at its defaults; it returns 2.93119e-5 for the
# dimensionless integral with an error estimate of 9.4e-9, while the integral is 2.889449e-5 (the same integrand
# with epsrel = 1e-13, and 30-digit mpmath): the result is 1.4 % high, 45 times its own estimate. The engine agrees
# with mpmath to 1e-19 Gyr.
KNOWN_CLOSED_AGE = ("library-side: Astropy's QUADPACK (QAGI, default epsabs/epsrel 1.49e-8) returns the "
                    "dimensionless age integral 2.93119e-5 with error estimate 9.4e-9; the integral is 2.889449e-5 "
                    "(quad at epsrel 1e-13; mpmath): 1.4 % high; engine - exact = 1e-19 Gyr")


def _truncation():
    return abs(ASTROPY_NU_LITERAL - F.NU_FACTOR) / F.NU_FACTOR


def _setups():
    s = (N_EFF / 3) ** 0.25
    out = [
        ("flat LCDM, no radiation", F.Background(70.0, 0.3), FlatLambdaCDM(H0=70.0, Om0=0.3), "closed", None),
        ("flat LCDM + radiation", F.Background(H0_P, OM_P, T_cmb=T_CMB, N_eff=N_EFF),
         FlatLambdaCDM(H0=H0_P, Om0=OM_P, Tcmb0=T_CMB, Neff=N_EFF), "quad", None),
        ("open LCDM + radiation", F.Background(70.0, 0.3, OL=0.6, T_cmb=T_CMB, N_eff=N_EFF),
         LambdaCDM(H0=70.0, Om0=0.3, Ode0=0.6, Tcmb0=T_CMB, Neff=N_EFF), "quad", None),
        ("closed LCDM + radiation", F.Background(70.0, 0.35, OL=0.75, T_cmb=T_CMB, N_eff=N_EFF),
         LambdaCDM(H0=70.0, Om0=0.35, Ode0=0.75, Tcmb0=T_CMB, Neff=N_EFF), "quad", None),
        ("flat w0wa + radiation", DE.background(70.0, 0.3, -0.9, 0.2, T_cmb=T_CMB, N_eff=N_EFF),
         Flatw0waCDM(H0=70.0, Om0=0.3, w0=-0.9, wa=0.2, Tcmb0=T_CMB, Neff=N_EFF), "quad", (-0.9, 0.2)),
        ("Planck 2018, m_nu = 0.06 eV", F.Background(H0_P, OM_P, T_cmb=T_CMB, N_eff=N_EFF, m_nu=(0.06 * s,)),
         FlatLambdaCDM(H0=H0_P, Om0=OM_P, Tcmb0=T_CMB, Neff=N_EFF, m_nu=[0.0, 0.0, 0.06] * u.eV), "quad", "nu"),
    ]
    return out


# --- exact references -------------------------------------------------------------------------------------------------
def _mp_E(bg, de):
    Or, Om, Ok, OL = (mp.mpf(v) for v in (bg.Orad, bg.Om, bg.Ok, bg.OL))

    def E(z):
        x = 1 + mp.mpf(z)
        g = mp.mpf(1)
        if isinstance(de, tuple):
            w0, wa = (mp.mpf(v) for v in de)
            g = x ** (3 * (1 + w0 + wa)) * mp.exp(-3 * wa * (x - 1) / x)
        return mp.sqrt(Or * x ** 4 + Om * x ** 3 + Ok * x ** 2 + OL * g)
    return E


def _mp_int(f, a, b):
    a = mp.mpf(a)
    if b == mp.inf:
        pts = [a] + [a + mp.mpf(10) ** k * (1 + a) for k in range(0, 9)] + [mp.inf]
    else:
        b = mp.mpf(b)
        pts = sorted({a, b} | {mp.mpf(10) ** k for k in range(-3, 4) if a < mp.mpf(10) ** k < b})
    return mp.quad(f, pts)


@functools.lru_cache(maxsize=None)
def rows() -> list[Row]:
    mp.mp.dps = 30
    out = []
    tr = _truncation()
    for label, bg, ac, kind, extra in _setups():
        DH, tH = bg.hubble_distance, bg.hubble_time
        nu_frac0 = (bg.Onu_massless + bg.Onu_massive) / max(bg.Orad + bg.Onu_massive, 1e-300)
        massive = extra == "nu"
        Emp = None if massive else _mp_E(bg, extra)
        k = math.sqrt(abs(bg.Ok))
        zgrid = np.geomspace(1e-4, 1e6, 600)
        fnu_grid = np.asarray(bg.densities(zgrid)["neutrinos_massive"]) if massive else np.zeros_like(zgrid)

        def fnu_max(z_lo, z_hi):
            sel = (zgrid >= z_lo) & (zgrid <= z_hi)
            return float(fnu_grid[sel].max()) if sel.any() else 0.0

        def add(q, z, eng, lib, tol, basis, exact=None):
            eng, lib = float(eng), float(lib)
            r = Row(GROUP, f"{label}: {q}", f"z={z:g}" if isinstance(z, (int, float)) else str(z), eng, lib,
                    float(tol), basis)
            if exact is not None:
                r.eng_err, r.lib_err = abs(eng - float(exact)), abs(lib - float(exact))
            out.append(r)

        lib_basis = "quad 1.49e-8" if kind == "quad" else "closed form 64u"
        if massive:
            lib_basis += " + Komatsu fit 0.35 %"
        for z in ZS:
            dens = bg.densities(z)
            fnu_z = dens["neutrinos_massive"]
            cond = 1.0 + 2.0 * abs(dens["curvature"])
            alg = 16 * U * cond
            fit_alg = KOMATSU * fnu_z
            tr_rel = tr * (dens["neutrinos_massless"] + dens["neutrinos_massive"])
            # --- comoving distance
            dc, edc = bg.comoving_distance(z, with_error=True)
            I = dc / DH
            if kind == "quad":
                lb = QUAD * max(1.0, I) * DH
            else:
                s3 = ((1 - ac.Om0) / ac.Om0) ** (1 / 3)
                pref = DH / math.sqrt(s3 * ac.Om0)
                lb = 64 * U * pref * (abs(ac._T_hypergeometric(s3)) + abs(ac._T_hypergeometric(s3 / (1 + z))))
            lb += 0.5 * KOMATSU * fnu_max(0, z) * dc + tr * nu_frac0 * dc
            ex_dc = DH * _mp_int(lambda x: 1 / Emp(x), 0, z) if Emp else None
            add("D_C [Mpc]", z, dc, ac.comoving_distance(z).to_value(u.Mpc), edc + lb, "engine bound + " + lib_basis,
                ex_dc)
            # --- transverse comoving distance and the distances made from it
            if bg.Ok > 0:
                ddm = math.cosh(k * dc / DH)
            elif bg.Ok < 0:
                ddm = abs(math.cos(k * dc / DH))
            else:
                ddm = 1.0
            dm = bg.transverse_comoving_distance(z)
            tol_dm = ddm * (edc + lb) + 8 * U * abs(dm)
            if ex_dc is None or bg.Ok == 0:
                ex_dm = ex_dc
            else:
                ex_dm = DH / k * (mp.sinh(k * ex_dc / DH) if bg.Ok > 0 else mp.sin(k * ex_dc / DH))
            add("D_M [Mpc]", z, dm, ac.comoving_transverse_distance(z).to_value(u.Mpc), tol_dm,
                "propagated + " + lib_basis, ex_dm)
            add("D_A [Mpc]", z, bg.angular_diameter_distance(z), ac.angular_diameter_distance(z).to_value(u.Mpc),
                tol_dm / (1 + z) + 4 * U * abs(dm) / (1 + z), "propagated + " + lib_basis,
                ex_dm / (1 + mp.mpf(z)) if ex_dm is not None else None)
            dl = bg.luminosity_distance(z)
            add("D_L [Mpc]", z, dl, ac.luminosity_distance(z).to_value(u.Mpc), tol_dm * (1 + z) + 4 * U * abs(dl),
                "propagated + " + lib_basis, ex_dm * (1 + mp.mpf(z)) if ex_dm is not None else None)
            mu = bg.distance_modulus(z)
            tol_mu = 5 / math.log(10) * (tol_dm / abs(dm) + 8 * U) + 8 * U * abs(mu)
            add("distance modulus", z, mu, ac.distmod(z).to_value(u.mag), tol_mu, "propagated + " + lib_basis,
                5 * mp.log10(ex_dm * (1 + mp.mpf(z))) + 25 if ex_dm is not None else None)
            # --- lookback time and age
            lt, elt = bg.lookback_time(z, with_error=True)
            if kind == "quad":
                lbt = QUAD * max(1.0, lt / tH) * tH
            else:
                lbt = 64 * U * (ac.age(0).to_value(u.Gyr) + ac.age(z).to_value(u.Gyr))
            lbt += 0.5 * KOMATSU * fnu_max(0, z) * lt + tr * nu_frac0 * lt
            ex_lt = tH * _mp_int(lambda x: 1 / ((1 + x) * Emp(x)), 0, z) if Emp else None
            add("lookback time [Gyr]", z, lt, ac.lookback_time(z).to_value(u.Gyr), elt + lbt,
                "engine bound + " + lib_basis, ex_lt)
            ag, eag = bg.age(z, with_error=True)
            lba = (QUAD * max(1.0, ag / tH) * tH if kind == "quad" else 64 * U * ag)
            lba += 0.5 * KOMATSU * fnu_max(z, 1e6) * ag + tr * ag
            ex_ag = tH * _mp_int(lambda x: 1 / ((1 + x) * Emp(x)), z, mp.inf) if Emp else None
            add("age [Gyr]", z, ag, ac.age(z).to_value(u.Gyr), eag + lba, "engine bound + " + lib_basis, ex_ag)
            if label.startswith("closed") and z == 1000.0:
                out[-1].xfail = KNOWN_CLOSED_AGE
            # --- algebraic quantities
            alg_basis = "16u x conditioning per side" + (" + Komatsu fit 0.35 %" if massive else "")
            add("H [km/s/Mpc]", z, bg.H(z), ac.H(z).to_value(u.km / u.s / u.Mpc),
                (2 * alg + 0.5 * fit_alg + tr_rel) * bg.H(z), alg_basis, bg.H0 * Emp(z) if Emp else None)
            add("Omega_m(z)", z, dens["matter"], ac.Om(z), (2 * alg + fit_alg + 2 * tr_rel) * dens["matter"], alg_basis,
                mp.mpf(bg.Om) * (1 + mp.mpf(z)) ** 3 / Emp(z) ** 2 if Emp else None)
            ode = dens["dark_energy"]
            ex_ode = None
            if Emp:
                g = mp.mpf(1)
                if isinstance(extra, tuple):
                    w0, wa = (mp.mpf(v) for v in extra)
                    x = 1 + mp.mpf(z)
                    g = x ** (3 * (1 + w0 + wa)) * mp.exp(-3 * wa * (x - 1) / x)
                ex_ode = mp.mpf(bg.OL) * g / Emp(z) ** 2
            add("Omega_de(z)", z, ode, ac.Ode(z), (2 * alg + fit_alg + 2 * tr_rel + 32 * U) * ode, alg_basis, ex_ode)
            if bg.Ok != 0:
                add("Omega_k(z)", z, dens["curvature"], ac.Ok(z),
                    (2 * alg + fit_alg + 2 * tr_rel) * abs(dens["curvature"]), alg_basis, mp.mpf(bg.Ok) * (1 + mp.mpf(z)) ** 2 / Emp(z) ** 2 if Emp else None)
            rc = bg.critical_density(z)
            add("rho_crit(z) [kg/m^3]", z, rc, ac.critical_density(z).to_value(u.kg / u.m ** 3),
                (2 * alg + 16 * U + fit_alg + 2 * tr_rel) * rc, alg_basis,
                mp.mpf(bg.rho_crit0) * Emp(z) ** 2 if Emp else None)
        # --- today's constants
        if bg.T_cmb > 0:
            add("Omega_gamma0", "today", bg.Ogamma, ac.Ogamma0, 2 * gamma(12) * bg.Ogamma, "12 roundings")
            onu = bg.Onu_massless + bg.Onu_massive
            add("Omega_nu0", "today", onu, ac.Onu0, (2 * gamma(16) + tr + KOMATSU * bg.Onu_massive / onu) * onu,
                "16 roundings + literal" + (" + Komatsu fit 0.35 %" if massive else ""))
            s = (N_EFF / 3) ** 0.25
            add("T_nu0 [K] (engine / (N_eff/3)^(1/4))", "today", bg.T_nu0 / s, ac.Tnu0.to_value(u.K),
                2 * gamma(8) * bg.T_nu0, "8 roundings")
        add("rho_crit0 [kg/m^3]", "today", bg.rho_crit0, ac.critical_density0.to_value(u.kg / u.m ** 3),
            2 * gamma(12) * bg.rho_crit0, "12 roundings")
        add("hubble distance [Mpc]", "today", DH, ac.hubble_distance.to_value(u.Mpc), 2 * gamma(4) * DH, "4 roundings")
        add("hubble time [Gyr]", "today", tH, ac.hubble_time.to_value(u.Gyr), 2 * gamma(8) * tH, "8 roundings")
        # D_A between two redshifts (Astropy: only for Ok >= 0 by Hogg's Eq. (19); the engine's sinn(chi2 - chi1)
        # holds for any curvature)
        if bg.Ok >= 0:
            for z1, z2 in ((0.5, 2.0), (1.0, 1100.0)):
                v = bg.angular_diameter_distance_z1z2(z1, z2)
                e1 = bg.comoving_distance(z1, with_error=True)[1] + bg.comoving_distance(z2, with_error=True)[1]
                d1, d2 = bg.comoving_distance(z1), bg.comoving_distance(z2)
                if kind == "quad":
                    lbz = QUAD * (max(1.0, d1 / DH) + max(1.0, d2 / DH)) * DH
                else:
                    s3 = ((1 - ac.Om0) / ac.Om0) ** (1 / 3)
                    pref = DH / math.sqrt(s3 * ac.Om0)
                    lbz = 64 * U * pref * (2 * abs(ac._T_hypergeometric(s3)) + abs(ac._T_hypergeometric(s3 / (1 + z1)))
                                           + abs(ac._T_hypergeometric(s3 / (1 + z2))))
                lbz += 0.5 * KOMATSU * fnu_max(0, z2) * (d1 + d2) + tr * (d1 + d2)
                grow = math.cosh(k * (d1 + d2) / DH) if bg.Ok > 0 else 1.0
                tol = grow * (e1 + lbz) * (1 + 2 * k * (d1 + d2) / DH) / (1 + z2) + 16 * U * abs(v)
                add("D_A(z1, z2) [Mpc]", f"z1={z1:g}, z2={z2:g}", v,
                    ac.angular_diameter_distance_z1z2(z1, z2).to_value(u.Mpc), tol, "propagated + " + lib_basis)
        # --- the massive neutrino's density relative to photons
        if massive:
            y0 = 0.06 / (F.K_B_EV * F.T_NU_RATIO * T_CMB)        # Astropy's m/(k T_nu0) = the engine's (m s)/(k s T)
            for z in (0.0, 10.0, 35.0, 100.0, 140.0, 1000.0):
                y = mp.mpf(y0) / (1 + z)
                fy = mp.quad(lambda x: x ** 2 * mp.sqrt(x * x + y * y) / (mp.exp(x) + 1), [0, 1, 4, 16, 64, mp.inf])
                fy = fy / (7 * mp.pi ** 4 / 120)
                exact = mp.mpf(F.NU_FACTOR) * mp.mpf(N_EFF) / 3 * (2 + fy)
                d = bg.densities(z)
                eng = (d["neutrinos_massless"] + d["neutrinos_massive"]) / d["photons"]
                lib = float(ac.nu_relative_density(z))
                share = float(fy / (2 + fy))
                add("nu density / photon density", z, eng, lib,
                    (KOMATSU * share + tr + 32 * U + 2 * F.FD_REL_ERROR) * eng, "Komatsu fit 0.35 % + literal",
                    exact)
    return out


@pytest.mark.parametrize("row", params(rows()))
def test_flrw_against_astropy(row):
    check(row)


def test_astropy_conventions():
    """The conventions the rows rely on: Astropy's Om0 excludes the massive neutrinos (as the engine's Om); its
    massive species carries N_eff/3 of the Fermi-Dirac density at T_nu = (4/11)^(1/3) T_cmb (so Onu0 of a 0.06 eV
    neutrino exceeds the engine's (CAMB's) value by (N_eff/3)^(1/4) up to Komatsu's fit); its quad tolerance is
    scipy's default; Tnu0 is not scaled by N_eff."""
    ac = FlatLambdaCDM(H0=H0_P, Om0=OM_P, Tcmb0=T_CMB, Neff=N_EFF, m_nu=[0.0, 0.0, 0.06] * u.eV)
    camb = F.Background(H0_P, OM_P, T_cmb=T_CMB, N_eff=N_EFF, m_nu=(0.06,))
    assert ac.Om0 == OM_P
    ratio = (ac.Onu0 - ac.Ogamma0 * ASTROPY_NU_LITERAL * N_EFF / 3 * 2) / camb.Onu_massive
    assert abs(ratio / (N_EFF / 3) ** 0.25 - 1) < KOMATSU
    assert ac.Tnu0.to_value(u.K) == pytest.approx(F.T_NU_RATIO * T_CMB, rel=1e-15)
    import inspect

    from scipy import integrate
    assert inspect.signature(integrate.quad).parameters["epsabs"].default == 1.49e-8
    assert inspect.signature(integrate.quad).parameters["epsrel"].default == 1.49e-8
    assert astropy.__version__ == "8.0.2"


def test_astropy_closed_age_is_a_quadpack_error():
    """The one known disagreement is Astropy's integration, not its integrand: the same integrand integrated by quad
    with epsrel = 1e-13 (and over a finite range with break points) agrees with the engine to 1e-12, while quad at its
    defaults is 1.4 % high with an error estimate of 9.4e-9."""
    from scipy.integrate import quad
    ac = LambdaCDM(H0=70.0, Om0=0.35, Ode0=0.75, Tcmb0=T_CMB, Neff=N_EFF)
    bg = F.Background(70.0, 0.35, OL=0.75, T_cmb=T_CMB, N_eff=N_EFF)
    f = ac._lookback_time_integrand_scalar
    default, est = quad(f, 1000.0, np.inf)[:2]
    tight = quad(f, 1000.0, np.inf, epsabs=0.0, epsrel=1e-13, limit=200)[0]
    engine = bg.age(1000.0) / bg.hubble_time
    assert tight == pytest.approx(engine, rel=1e-12)
    assert abs(default - tight) > 40 * est and abs(default / tight - 1) > 0.01
    assert ac.age(1000.0).to_value(u.Gyr) == pytest.approx(default * ac.hubble_time.to_value(u.Gyr), rel=1e-14)
