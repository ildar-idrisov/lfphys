# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Measured and reference numbers the engine compares with, each with its source as checked against the text.

Verification record: lfphys/sources/verification_2026-10-23.md (verbatim quotes, URLs, access date 2026-10-23).
Edition policy: particle data from PDG 2024 (S. Navas et al., Phys. Rev. D 110, 030001 (2024)); PDG 2026 (F. Takahashi
et al., Int. J. Mod. Phys. A 41, 2630011 (2026)) is online and differs slightly for some entries (noted below).
Values are (value, uncertainty) in the units stated.
"""

from __future__ import annotations

from lfphys.i18n import T
from lfphys import i18n
from lfphys.codes import coded

ABOUT = {
    "layer": "core", "kind": "data",
    "title": T("Measured and reference values (with sources)"),
    "statement": T("α_s(M_Z), M_Z, the heavy quark masses, the charmonium and bottomonium masses (PDG 2024); the "
                   "orbital elements of Mercury (NASA); tests of GR in the Solar System and at a pulsar (Will 2014; "
                   "Weisberg & Huang 2016); the Planck 2018 cosmological parameters (Tables 1 and 2) and the "
                   "temperature of the cosmic microwave background (Fixsen 2009); the refractive index of water n(λ, "
                   "T, ρ) (IAPWS R9-97) and the density of water at 0.1 MPa (IAPWS SR6-08); the nominal effective "
                   "temperature of the Sun (IAU 2015 B3); the density and viscosity of water at 1 atm (IAPWS "
                   "through the NIST WebBook) and of dry air (the U.S. Standard Atmosphere 1976)."),
    "validity": T("values with the uncertainties of the source; the PDG 2026 edition differs in some lines (stated)"),
    "basis": ["PDG 2024: Phys. Rev. D 110, 030001", "NASA Mercury Fact Sheet (2024)",
              "Will, Living Rev. Relativ. 17, 4 (2014)", "Weisberg & Huang, ApJ 829, 55 (2016)",
              "Bertotti, Iess, Tortora, Nature 425, 374 (2003)",
              "Planck Collaboration, A&A 641, A6 (2020), Tables 1, 2", "Fixsen, ApJ 707, 916 (2009)",
              T("IAPWS R9-97 (1997): the refractive index of water"), T("IAPWS SR6-08 (2011): liquid water at 0.1 MPa"),
              "IAU 2015 Resolution B3 (Prša et al., AJ 152, 41, 2016)",
              T("NIST Chemistry WebBook SRD 69: water at 0.101325 MPa (IAPWS-95, IAPWS 2008 viscosity)"),
              T("U.S. Standard Atmosphere 1976 (NOAA/NASA/USAF, NASA-TM-X-74335): dry air")],
    "conflicts": [],
}

# --- QCD (PDG 2024) ---------------------------------------------------------------------------------------------
ALPHA_S_MZ = (0.1180, 0.0009)        # PDG 2024 review 9, Eq. (9.25); same in PDG 2026
M_Z = (91.1880, 0.0020)              # GeV, PDG 2024 (2026: 91.1879)
M_C_MC = (1.2730, 0.0046)            # GeV, MS-bar m_c(m_c), PDG 2024 (2026: 1.2729 +- 0.0045)
M_B_MB = (4.183, 0.007)              # GeV, MS-bar m_b(m_b), PDG 2024 (2026: 4.186 +- 0.006)
M_T_DIRECT = (172.57, 0.29)          # GeV, direct measurements, PDG 2024 (2026: 172.60 +- 0.27)
M_T_MSBAR = 162.5                    # GeV, MS-bar m_t(m_t) from cross sections, PDG 2024 (+2.1 -1.5)

# quarkonium masses (MeV), PDG 2024 summary tables; (J, L, S, n_radial) labels for spin averaging
CHARMONIUM = {
    "eta_c(1S)": (2984.1, 0.4, 0, 0, 0, 1),    # PDG 2026: 2984.09 +- 0.30
    "J/psi(1S)": (3096.900, 0.006, 1, 0, 1, 1),
    "chi_c0(1P)": (3414.71, 0.30, 0, 1, 1, 1),  # PDG 2026: 3415.50 +- 0.19
    "chi_c1(1P)": (3510.67, 0.05, 1, 1, 1, 1),
    "h_c(1P)": (3525.37, 0.14, 1, 1, 0, 1),
    "chi_c2(1P)": (3556.17, 0.07, 2, 1, 1, 1),
    "eta_c(2S)": (3637.7, 0.9, 0, 0, 0, 2),     # PDG 2026: 3637.8 +- 0.6
    "psi(2S)": (3686.097, 0.011, 1, 0, 1, 2),
}
BOTTOMONIUM = {
    "eta_b(1S)": (9398.7, 2.0, 0, 0, 0, 1),
    "Upsilon(1S)": (9460.40, 0.10, 1, 0, 1, 1),
    "chi_b0(1P)": (9859.44, 0.52, 0, 1, 1, 1),  # +-0.42 +-0.31 combined in quadrature
    "chi_b1(1P)": (9892.78, 0.40, 1, 1, 1, 1),  # +-0.26 +-0.31
    "h_b(1P)": (9899.3, 0.8, 1, 1, 0, 1),
    "chi_b2(1P)": (9912.21, 0.40, 2, 1, 1, 1),  # +-0.26 +-0.31
    "Upsilon(2S)": (10023.4, 0.5, 1, 0, 1, 2),
    "Upsilon(3S)": (10355.1, 0.5, 1, 0, 1, 3),
}


def spin_averaged(table: dict, L: int, n: int):
    """(2J+1)-weighted mean mass of the multiplet (n, L) over the states present, and the list used."""
    rows = [(k, v) for k, v in table.items() if v[3] == L and v[5] == n]
    if not rows:
        return None, []
    w = [2 * v[2] + 1 for _, v in rows]
    return sum(wi * v[0] for wi, (_, v) in zip(w, rows)) / sum(w), [k for k, _ in rows]


# --- gravity --------------------------------------------------------------------------------------------------
MERCURY = {"a_m": 57.909e9, "ecc": 0.2056, "period_days": 87.969}  # NASA Mercury Fact Sheet (updated 2024-01-11)
MERCURY_ADVANCE_GR_ARCSEC_PER_CENTURY = 42.98  # Will 2014, Sec. 4.2, Eq. (65), the PPN part with gamma = beta = 1
CASSINI_GAMMA_MINUS_1 = (2.1e-5, 2.3e-5)       # Bertotti, Iess, Tortora 2003 (Doppler frequency shift)
VLBI_GAMMA_MINUS_1 = (-1.6e-4, 1.5e-4)         # Lambert & Le Poncin-Lafitte 2009, as quoted by Will 2014
# The binary pulsar tests GR's two-body dynamics (1PN periastron advance with the total mass, quadrupole radiation
# reaction): since B5 (plan P7) the engine has it (core.gravity.pn_binary, theories.approx.peters_mathews), and these
# values with the pulsar's elements below are checked in tests/test_peters_mathews.py and tests/test_pn_binary.py. The
# other bounds here are used in tests/test_experimental_bounds.py.
PSR_B1913_PERIASTRON_DEG_PER_YR = (4.226585, 0.000004)  # Weisberg & Huang 2016
PSR_B1913_PBDOT_RATIO = (0.9983, 0.0016)                # observed / GR orbital decay, Weisberg & Huang 2016

# --- Bell tests -------------------------------------------------------------------------------------------------
HENSEN_2015_S = (2.42, 0.20)  # Hensen et al., Nature 526, 682 (2015), 245 trials

# --- PSR B1913+16 orbit (appended 2026-10-29 for plan item P7; used by tests/test_peters_mathews.py) -------------
# Weisberg & Huang, ApJ 829, 55 (2016), text arXiv:1606.02744v1 (Table 2 "Orbital Parameters"; Secs. 3.1, 4.1, 4.3,
# 5.1), verbatim quotes in sources/verification_2026-10-29_p7.md. Figures in parentheses there are formal TEMPO errors
# of the last digit. With these, PSR_B1913_PERIASTRON_DEG_PER_YR and PSR_B1913_PBDOT_RATIO above are now used.
PSR_B1913_PB_DAYS = (0.322997448918, 0.000000000003)  # Table 2: Pb (d) 0.322997448918(3)
PSR_B1913_ECC = (0.6171340, 0.0000004)                 # Table 2: e 0.6171340(4)
PSR_B1913_X_LIGHT_S = (2.341776, 0.000002)             # Table 2: x = a1 sin i (s) 2.341776(2)
# Table 2 prints "gamma (ms) 0.004307(4)"; only gamma = 0.004307 s (4.307 ms) gives the paper's masses 1.438 and 1.390
# through its Eq. (17) (0.004307 ms would give m2 = 0.002 Msun), so the unit label is taken as a misprint: seconds.
PSR_B1913_GAMMA_S = (0.004307, 0.000004)
PSR_B1913_PBDOT_OBS = (-2.423e-12, 0.001e-12)          # Table 2
PSR_B1913_PBDOT_GAL = (-0.025e-12, 0.004e-12)          # Sec. 4.1 (galactic acceleration term)
PSR_B1913_PBDOT_INTR = (-2.398e-12, 0.004e-12)         # Sec. 4.1, Eq. (15): observed minus galactic
PSR_B1913_PBDOT_GR = (-2.40263e-12, 0.00005e-12)       # Sec. 5.1, from Eq. (22)
PSR_B1913_M_PULSAR_MSUN = (1.438, 0.001)               # Sec. 4.3 (from <omega_dot> and gamma, Eqs. (16)-(17))
PSR_B1913_M_COMPANION_MSUN = (1.390, 0.001)            # Sec. 4.3
PSR_B1913_SIN_I = (0.7327, 0.0004)                     # Sec. 4.3, (sin i)_{<omega_dot>, gamma}
PULSAR_T_SUN_S = 4.925490947e-6                        # Sec. 3.1: T_sun = G M_sun / c^3 = 4.925 490 947 us
PULSAR_YEAR_DAYS = 365.25                              # the year of <omega_dot> in deg/yr (Julian; TEMPO's unit).
# Not printed in the paper: with 365.25 d its Pb_dot^GR = -2.40263e-12 is reproduced to 1e-7 relative, with the
# tropical year (365.2422 d) the result is -2.40276e-12, 2.5 times its quoted uncertainty away (tests).

# --- Black-hole shadows (appended 2026-10-29 for plan item P7, Kerr shadows; used by theories.alternatives.
# johannsen_metric and its tests). Verbatim quotes in sources/verification_2026-10-29_p7_kerr.md.
# M87*: EHT Collaboration 2019, ApJL 875, L1 (Paper I), abstract and Table 1; ApJL 875, L6 (Paper VI), Sec. 9.5.
EHT_M87_RING_DIAMETER_UAS = (42.0, 3.0)   # Paper I abstract: "a diameter of 42±3 μas"; Table 1 "Ring diameter"
EHT_M87_THETA_G_UAS = (3.8, 0.4)          # Paper I Table 1, Paper VI Sec. 10: "θg=3.8±0.4 μas" (GM/(D c^2))
EHT_M87_MASS_1E9_MSUN = (6.5, 0.7)        # Paper I abstract: "M=(6.5±0.7)×10^9 M_sun" (stat. and syst.)
EHT_M87_DISTANCE_MPC = (16.8, 0.8)        # Paper I, Sec. 7 / Table 1: "(16.8±0.8) Mpc" (adopted prior)
# Paper VI Eq. (31): delta = theta_g/theta_dyn - 1, 68% credible: "δ=−0.01±0.17 ... for the stellar and δ=0.78±0.3
# for the gas dynamics priors". Psaltis et al. 2020 (PRL 125, 141104) read it as the shadow size being consistent
# "to within 17%" with the Kerr prediction for the bounds on parametrized metrics.
EHT_M87_DELTA_STELLAR = (-0.01, 0.17)
EHT_M87_DELTA_GAS = (0.78, 0.3)
# Sgr A*: EHT Collaboration 2022, ApJL 930, L17 (Paper VI; text arXiv:2311.09484v1). delta = d_sh/d_sh,Sch - 1
# with d_sh,Sch = 6 sqrt(3) theta_g (Sec. 3, before 3.1). Table 2, eht-imaging with the GRMHD calibration (the
# headline values):
EHT_SGRA_DELTA_VLTI = (-0.08, 0.09, 0.09)  # (value, +err, -err): "−0.08+0.09 −0.09"
EHT_SGRA_DELTA_KECK = (-0.04, 0.09, 0.10)  # "−0.04+0.09 −0.10"
# Sec. 5.1, Eqs. (12)-(13): the fiducial shadow-size bounds, in units of 3 sqrt(3) M (the Schwarzschild radius):
# "3√3(1 − 0.14)M ≲ r̃sh ≲ 3√3(1 + 0.05)M" (Keck), "3√3(1 − 0.17)M ≲ r̃sh ≲ 3√3(1 + 0.01)M" (VLTI).
EHT_SGRA_SHADOW_RADIUS_KECK = (0.86, 1.05)
EHT_SGRA_SHADOW_RADIUS_VLTI = (0.83, 1.01)
EHT_SGRA_THETA_G_UAS_VLTI = (5.125, 0.009, 0.020)  # Sec. 2.1: "θg = (5.125 ± 0.009 ± 0.020) µas (VLTI)"
EHT_SGRA_THETA_G_UAS_KECK = (4.92, 0.03, 0.01)     # Sec. 2.1: "θg = (4.92 ± 0.03 ± 0.01) µas (Keck)" (stat, syst)
# Published bounds on the Johannsen ("JP") metric's deviation parameters, reproduced by the engine's tests:
# Psaltis et al. 2020 (M87*, non-spinning): "−3.6 < α13 < 5.9"; Sgr A* Paper VI Table 3 (Keck, eht-imaging, GRMHD):
# "−1.1 ≲ α12 ≲ 0.5", "−3.1 ≲ α13 ≲ 1.5". (α12 is the 1PN term of Paper VI's non-spinning JP form, its Eq. 17,
# "Σ_{i=2}"; Johannsen 2013a's A1 starts at α13, his Eq. 52. Corrected 2026-10-29, review B5-K14.)
JP_ALPHA13_M87_PSALTIS2020 = (-3.6, 5.9)
JP_ALPHA13_SGRA_KECK = (-3.1, 1.5)
JP_ALPHA12_SGRA_KECK = (-1.1, 0.5)
# M87*'s inclination as the EHT used it (EHT 2019 Paper V, ApJL 875, L5, Fig. 8 caption: "i=17° for a* ≤ 0 and 163°
# for a* > 0"): the spin of the hole points away from us for positive a*; the same shadow size, the image flipped
# top-bottom relative to the projected spin (added 2026-10-29, review B5-K14).
EHT_M87_INCLINATION_DEG = {"a_positive": 163.0, "a_nonpositive": 17.0}

# --- Cosmology (appended 2026-11-04 for plan item P8, the FLRW background; used by core.cosmology.flrw and
# tests/test_flrw.py). Verbatim quotes in sources/verification_2026-11-04_p8_flrw.md.
# Fixsen, ApJ 707, 916 (2009), arXiv:0911.1955v2, abstract: "cosmic microwave background temperature of
# 2.72548±0.00057 K".
FIXSEN2009_T_CMB_K = (2.72548, 0.00057)
# Planck 2018 results VI, A&A 641, A6 (2020), arXiv:1807.06209v4. Footnote 14: "We take T0 = 2.7255K (Fixsen 2009),
# with the ±0.0006K error having negligible impact on results." Sect. 2.1: "We assume three neutrinos species,
# approximated as two massless states and a single massive neutrino of mass mν = 0.06 eV." Sect. 7.5.2: "The standard
# cosmological model has Neff ≈ 3.046" (the base model's value; the abstract: "the Standard Model prediction
# Neff = 3.046").
PLANCK2018_T_CMB_K = 2.7255
PLANCK2018_N_EFF = 3.046
PLANCK2018_M_NU_EV = 0.06
# The parameters below are those of the base-LambdaCDM fit (model-dependent: another model gives other values). The
# paper's abstract states the fit's H0 is "in significant, 3.6 σ, tension with local measurements of the Hubble
# constant"; DESI DR2 (arXiv:2503.14738v3, abstract) prefers w0 > −1, wa < 0 over LambdaCDM at 3.1σ with the CMB
# (2.8−4.2σ with SNe). Both are tensions, not refutations (review B7-flrw C12). The numbers were computed with CAMB
# (August 2017 version) and CosmoMC (July 2018), Sect. 2.1, whose conventions differ slightly from the engine's
# (Gyr, Mpc, constants, Omega_Lambda = 1 - Omega_m without radiation): tests/test_flrw.py::_camb17 (C4).
# Table 2, column "TT,TE,EE+lowE+lensing+BAO" (68 % limits: posterior mean, standard deviation). Omega_m includes
# the 0.06 eV neutrino (Table 1 caption: "Note that Ωm includes the contribution from one neutrino with a mass of
# 0.06 eV"). theta_* = r_* / D_M(z_*) (Sect. 3.1: "θ∗ ≡ r∗ /DM").
PLANCK2018_BAO = {
    "omega_b": (0.02242, 0.00014), "omega_c": (0.11933, 0.00091), "100theta_MC": (1.04101, 0.00029),
    "tau": (0.0561, 0.0071), "ln1e10As": (3.047, 0.014), "n_s": (0.9665, 0.0038),
    "H0": (67.66, 0.42), "Omega_L": (0.6889, 0.0056), "Omega_m": (0.3111, 0.0056), "omega_m": (0.14240, 0.00087),
    "Omega_m_h3": (0.09635, 0.00030), "age_Gyr": (13.787, 0.020), "z_star": (1089.80, 0.21),
    "r_star_Mpc": (144.57, 0.22), "100theta_star": (1.04119, 0.00029), "z_drag": (1060.01, 0.29),
    "r_drag_Mpc": (147.21, 0.23), "z_eq": (3387.0, 21.0), "k_eq_per_Mpc": (0.010339, 0.000063),
}
# Table 1, column "Plik best fit" (TT,TE,EE+lowE+lensing): one model, so its derived numbers belong to its own
# parameters (the posterior means of Table 2 are means of each quantity separately).
PLANCK2018_BESTFIT = {
    "omega_b": 0.022383, "omega_c": 0.12011, "100theta_MC": 1.040909, "tau": 0.0543, "ln1e10As": 3.0448,
    "n_s": 0.96605, "omega_m": 0.14314, "H0": 67.32, "Omega_m": 0.3158, "age_Gyr": 13.7971,
    "100theta_star": 1.041085, "r_drag_Mpc": 147.049,
}

# --- Water and the Sun (appended 2026-11-04 for plan items P1 and P14.8, Mie scattering by water drops; used by the
# tests tests/test_mie_water.py and the visualization u44_mie_scattering). Verbatim quotes in
# sources/verification_2026-11-04_p1_mie.md.
# IAPWS R9-97 (Erlangen, September 1997), "Release on the Refractive Index of Ordinary Water Substance as a Function
# of Wavelength, Temperature and Pressure", Eq. (1) with the coefficients of its Table 1:
#   (n^2 - 1)/(n^2 + 2) (1/rho_) = a0 + a1 rho_ + a2 T_ + a3 lam_^2 T_ + a4/lam_^2 + a5/(lam_^2 - lamUV^2)
#                                  + a6/(lam_^2 - lamIR^2) + a7 rho_^2,
# T_ = T/273.15 K, rho_ = rho/(1000 kg m^-3), lam_ = lambda/(0.589 um). Range (Sec. 4): -12 C <= t <= 500 C,
# 0 <= rho <= 1060 kg m^-3, 0.2 um <= lambda <= 1.1 um. Uncertainty (Table 2), liquid at ambient pressure: 1.5e-5 for
# 0.40-0.70 um and 5-60 C, < 6e-5 for -12 to 5 C, 5e-4 for 0.21-0.40 um, 1e-3 for 0.70-1.1 um. Real part only (the
# release gives no absorption).
IAPWS97_RINDEX_A = (0.244257733, 9.74634476e-3, -3.73234996e-3, 2.68678472e-4, 1.58920570e-3, 2.45934259e-3,
                    0.900704920, -1.66626219e-2)
IAPWS97_RINDEX_LAMBDA_UV = 0.2292020
IAPWS97_RINDEX_LAMBDA_IR = 5.432937
# Table 3 ("Values for Program Verification"), 0.1 MPa and 0 C (the liquid rows; the release: "to within one unit in
# the least significant digit" if the density is right to 1e-6): (wavelength in um, n)
IAPWS97_RINDEX_CHECK_0C_01MPA = ((0.22650, 1.394527), (0.58900, 1.334344), (1.01398, 1.326135))
# IAPWS SR6-08(2011), "Revised Supplementary Release on Properties of Liquid Water at 0.1 MPa", Eq. (2) with Table 1
# rows i = 5..10: v0 = (R T_R/p0) [a5 + sum_{i=6..10} a_i alpha^n_i + sum_{i=5..10} b_i beta^m_i], alpha = T_R/(T_a - T),
# beta = T_R/(T - T_b), R = 461.51805 J/(kg K), T_R = 10 K, T_a = 593 K, T_b = 232 K, p0 = 0.1 MPa; range 253.15-383.15 K
# (metastable liquid below ~273.15 K and above ~372.76 K); "a relative uncertainty of 0.0001 % for specific volume (or
# density)" in the stable region; at 0.101325 MPa v = v0 + v_p0 (p - p0) agrees with IAPWS-95 within 0.04e-6.
IAPWS08_V0_A = {5: 1.93763157e-2, 6: 6.74458446e+3, 7: -2.22521604e+5, 8: 1.00231247e+8, 9: -1.63552118e+9,
                10: 8.32299658e+9}
IAPWS08_V0_B = {5: 5.78545292e-3, 6: -1.53195665e-2, 7: 3.11337859e-2, 8: -4.23546241e-2, 9: 3.38713507e-2,
                10: -1.19946761e-2}
IAPWS08_V0_N = {6: 4, 7: 5, 8: 7, 9: 8, 10: 9}
IAPWS08_V0_M = {5: 1, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6}
IAPWS08_R, IAPWS08_TR, IAPWS08_TA, IAPWS08_TB, IAPWS08_P0 = 461.51805, 10.0, 593.0, 232.0, 0.1e6
# Table 8 ("Sample points for computer-program verification"): density at 0.1 MPa, (T in K, rho in kg m^-3)
IAPWS08_RHO_CHECK = ((260.0, 997.068360), (298.15, 997.047013), (375.0, 957.009710))


def water_density_01mpa(T_K):
    """Density of liquid water at 0.1 MPa (kg/m^3), IAPWS SR6-08(2011) Eq. (2), 253.15 K <= T <= 383.15 K."""
    import numpy as _np
    T = _np.asarray(T_K, float)
    if _np.any((T < 253.15) | (T > 383.15)):
        raise coded(ValueError(i18n.T("water density (IAPWS SR6-08): the temperature must be from 253.15 to 383.15 K")),
                    "water.out_of_range")
    al = IAPWS08_TR / (IAPWS08_TA - T)
    be = IAPWS08_TR / (T - IAPWS08_TB)
    s = IAPWS08_V0_A[5] + sum(IAPWS08_V0_A[i] * al ** IAPWS08_V0_N[i] for i in range(6, 11)) \
        + sum(IAPWS08_V0_B[i] * be ** IAPWS08_V0_M[i] for i in range(5, 11))
    return 1.0 / (IAPWS08_R * IAPWS08_TR / IAPWS08_P0 * s)


def water_refractive_index(lam_um, T_K, rho):
    """Refractive index of water with respect to vacuum, IAPWS R9-97 Eq. (1): wavelength in um (vacuum), T in K,
    density in kg/m^3 (arrays broadcast). Raises outside the release's range."""
    import numpy as _np
    lam, T, r = (_np.asarray(v, float) for v in (lam_um, T_K, rho))
    if _np.any((lam < 0.2) | (lam > 1.1)) or _np.any((T < 261.15) | (T > 773.15)) or _np.any((r < 0) | (r > 1060)):
        raise coded(ValueError(i18n.T("refractive index of water (IAPWS R9-97): 0.2–1.1 µm, −12 to 500 °C, 0–1060 "
                                      "kg/m³")), "water.out_of_range")
    a = IAPWS97_RINDEX_A
    Tb, rb, lb2 = T / 273.15, r / 1000.0, (lam / 0.589) ** 2
    f = rb * (a[0] + a[1] * rb + a[2] * Tb + a[3] * lb2 * Tb + a[4] / lb2 + a[5] / (lb2 - IAPWS97_RINDEX_LAMBDA_UV ** 2)
              + a[6] / (lb2 - IAPWS97_RINDEX_LAMBDA_IR ** 2) + a[7] * rb * rb)
    return _np.sqrt((1.0 + 2.0 * f) / (1.0 - f))


def water_index(lam_nm, t_C: float = 20.0):
    """n of liquid water at 0.1 MPa and t (C), wavelength in nm (vacuum): IAPWS R9-97 with the density of SR6-08
    (0 <= t <= 110 C here). Above about 99.6 C (372.76 K) the liquid at 0.1 MPa is metastable (superheated): SR6-08
    Sec. 2.3, "the equilibrium phase at 0.1 MPa is ... a vapor (above approximately 372.76 K); at these conditions
    Eqs. (1)-(3) describe the properties of the metastable liquid phase", and "No uncertainty estimate is given for the
    metastable regions". [error in earlier] this docstring called 0-110 C "the stable range of both" (review B8-mie,
    M13)."""
    if not 0.0 <= float(t_C) <= 110.0:
        raise coded(ValueError(i18n.T("water at 0.1 MPa: from 0 to 110 °C")), "water.out_of_range")
    T = float(t_C) + 273.15
    import numpy as _np
    return water_refractive_index(_np.asarray(lam_nm, float) * 1e-3, T, water_density_01mpa(T))


# The Sun's nominal effective temperature: IAU 2015 Resolution B3 (Prsa et al., AJ 152, 41 (2016), arXiv:1605.09788):
# "T_sun^N = 5772 K"; the paper's best estimate 5772.0 +- 0.8 K. Sunlight as a black body at this temperature is a
# stated approximation of its spectrum (it ignores absorption lines and the limb), used only for colours.
SUN_TEFF_NOMINAL_K = 5772.0


# --- fluids: cited data ------------------------------------------------------------------------------------------------
# Water at 0.101325 MPa: NIST Chemistry WebBook, SRD 69, "Isobaric Properties for Water" at 0.101325 MPa, fetched
# 2026-11-04, computed there from IAPWS-95 (Wagner & Pruss, J. Phys. Chem. Ref. Data 31, 387 (2002); IAPWS R6-95(2016))
# for the density and the IAPWS 2008 viscosity formulation (Huber et al., J. Phys. Chem. Ref. Data 38, 101 (2009));
# the WebBook states the uncertainty of the density "0.0001% at 1 atm in the liquid phase"; IAPWS R12-08 states the
# viscosity's "uncertainty of 0.17 % at 293.15 K" (the releases themselves tabulate neither value at 20 C).
# (T in deg C, density kg/m^3, dynamic viscosity Pa s), 7 digits as printed.
WATER_1ATM = (
    (0.01, 999.8438, 0.001791132),
    (1, 999.9018, 0.001731021),
    (2, 999.9430, 0.001673515),
    (3, 999.9672, 0.001619009),
    (4, 999.9749, 0.001567292),
    (5, 999.9666, 0.001518173),
    (6, 999.9429, 0.001471477),
    (7, 999.9043, 0.001427043),
    (8, 999.8510, 0.001384724),
    (9, 999.7836, 0.001344385),
    (10, 999.7025, 0.001305900),
    (11, 999.6079, 0.001269155),
    (12, 999.5003, 0.001234043),
    (13, 999.3801, 0.001200468),
    (14, 999.2474, 0.001168337),
    (15, 999.1026, 0.001137568),
    (16, 998.9461, 0.001108081),
    (17, 998.7780, 0.001079806),
    (18, 998.5986, 0.001052674),
    (19, 998.4083, 0.001026624),
    (20, 998.2072, 0.001001596),
    (21, 997.9955, 0.0009775372),
    (22, 997.7735, 0.0009543962),
    (23, 997.5414, 0.0009321258),
    (24, 997.2994, 0.0009106817),
    (25, 997.0476, 0.0008900225),
    (26, 996.7864, 0.0008701093),
    (27, 996.5158, 0.0008509058),
    (28, 996.2360, 0.0008323778),
    (29, 995.9471, 0.0008144932),
    (30, 995.6495, 0.0007972218),
    (31, 995.3431, 0.0007805353),
    (32, 995.0281, 0.0007644068),
    (33, 994.7048, 0.0007488114),
    (34, 994.3731, 0.0007337251),
    (35, 994.0333, 0.0007191256),
    (36, 993.6855, 0.0007049918),
    (37, 993.3298, 0.0006913036),
    (38, 992.9663, 0.0006780421),
    (39, 992.5951, 0.0006651895),
    (40, 992.2164, 0.0006527287))
WATER_SOURCE = T("NIST Chemistry WebBook SRD 69 (isobar 0.101325 MPa, retrieved 2026-11-04): IAPWS-95 (Wagner & Pruß "
                 "2002) and the IAPWS 2008 viscosity (Huber et al. 2009)")
# Air: U.S. Standard Atmosphere 1976 (NOAA/NASA/USAF, NASA-TM-X-74335, NTRS 19770009539): ideal gas
# rho = P M0 / (R* T) with M0 = 28.9644 kg/kmol (p. 9), R* = 8.31432e3 N m/(kmol K) (p. 3; table 2 on p. 2 prints the
# exponent wrongly), P0 = 1.013250e5 Pa (table 2); dynamic viscosity eq. (51), p. 19: mu = beta T^(3/2) / (T + S),
# beta = 1.458e-6 kg/(s m K^(1/2)), S = 110.4 K ("basically from kinetic theory, but with constants derived from
# experiment"; table 2 prints S = 110 K, the text 110.4 K). Checked against the standard's table I (p. 52): sea level
# 288.150 K, 1.01325e3 mb, 1.2250 kg/m^3.
# Re-read from the page images on 2026-11-14 (design explore_2026-11-14 §4; printed page N = PDF page N + 16): R* p. 3,
# P0 p. 3 ("adopted in 1947 in Resolution 164 of the International Meteorological Organization"), T0 = 288.15 K p. 4,
# M0 p. 9 (section 1.2.4), eq. (51) p. 19 (section 1.3.11: "S is Sutherland's constant, equal to 110.4 K"; table 2B on
# p. 2 and the list on p. 4 print 110 K; the tabulated sea-level viscosity, table III p. 100, 1.7894e-5 N s/m^2, is the
# formula's with 110.4 K, 1.78938e-5, not with 110 K, 1.79118e-5). An independent modern check (test_mechanics_air):
# dry air on the 0.101325 MPa isobar, Lemmon, Jacobsen, Penoncello & Friend, J. Phys. Chem. Ref. Data 29, 331 (2000),
# table A2 (290 K: 0.042040 mol/dm^3, 300 K: 0.040634 mol/dm^3, M = 28.9586 g/mol): 1.21742 and 1.17670 kg/m^3, the
# formula 1.21718 and 1.17661 (-1.9e-4, -8e-5; the standard's M0 is 2e-4 above the modern molar mass); the dilute-gas
# viscosity of Lemmon & Jacobsen, Int. J. Thermophys. 25, 21 (2004), table V, at 300 K: 18.5230 uPa s ("1 % in the
# dilute gas for air"), the formula 18.460 uPa s (-0.34 %).
AIR_M0, AIR_RSTAR, AIR_BETA, AIR_S, P_ATM = 28.9644, 8.31432e3, 1.458e-6, 110.4, 1.013250e5
AIR_SOURCE = T("U.S. Standard Atmosphere 1976 (NASA-TM-X-74335): ideal gas with M0 = 28.9644 kg/kmol, R* = "
               "8.31432·10³ J/(kmol·K) (pp. 3, 9); viscosity by formula (51) with β = 1.458·10⁻⁶, S = 110.4 K (p. 19)")


def fluid_properties(name: str, T_C: float = 20.0, p: float = P_ATM) -> dict:
    """Density (kg/m^3), dynamic viscosity mu (Pa s) and kinematic viscosity nu (m^2/s) of "water" (at 1 atm, 0.01-40 C:
    the WebBook's IAPWS values at whole degrees, density interpolated linearly and log(mu) linearly in T; on every
    second row the interpolation errs by at most 3.4e-4 in mu and 8.5e-6 in rho, so on the whole-degree table by about
    a quarter of that: ~1e-4 and ~2e-6, tests) or "air" (dry air, any T from -50 to 100 C and pressure ``p`` in Pa:
    the U.S. Standard Atmosphere 1976 formulas), with the source."""
    import numpy as np
    if name == "water":
        if p != P_ATM:
            raise ValueError(T("water: only at 1 atm (101325 Pa)"))
        tab = np.array(WATER_1ATM)
        if not (tab[0, 0] <= T_C <= tab[-1, 0]):
            raise ValueError(T("water: the table runs from {lo} to {hi} °C", lo=float(tab[0, 0]), hi=float(tab[-1, 0])))
        at = np.flatnonzero(tab[:, 0] == T_C)
        if len(at):  # a tabulated temperature: the value as printed
            rho, mu = float(tab[at[0], 1]), float(tab[at[0], 2])
        else:
            rho = float(np.interp(T_C, tab[:, 0], tab[:, 1]))
            mu = float(np.exp(np.interp(T_C, tab[:, 0], np.log(tab[:, 2]))))
        src = WATER_SOURCE
    elif name == "air":
        if not (-50.0 <= T_C <= 100.0) or not p > 0:
            raise ValueError(T("air: from −50 to 100 °C, pressure > 0"))
        TK = T_C + 273.15  # kelvin (not "T": that name is the translatable text, lfphys.i18n)
        rho = p * AIR_M0 / (AIR_RSTAR * TK)
        mu = AIR_BETA * TK**1.5 / (TK + AIR_S)
        src = AIR_SOURCE
    else:
        raise ValueError(T("fluid {name}: 'water' or 'air'", name=repr(name)))
    return {"name": name, "T_C": float(T_C), "p": float(p), "rho": rho, "mu": mu, "nu": mu / rho, "source": src}


FLUIDS = {"water_20C": fluid_properties("water", 20.0), "air_20C": fluid_properties("air", 20.0)}
