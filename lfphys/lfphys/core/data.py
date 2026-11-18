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
                   "through the NIST WebBook) and of dry air (the U.S. Standard Atmosphere 1976); the optical "
                   "constants of real materials: the SCHOTT glasses N-BK7, N-F2 and N-SF11, crystalline MgF₂ and "
                   "fused silica, MgF₂, SiO₂ and Ta₂O₅ films, gold, silver and aluminium."),
    "validity": T("values with the uncertainties of the source; the PDG 2026 edition differs in some lines (stated)"),
    "basis": ["PDG 2024: Phys. Rev. D 110, 030001", "NASA Mercury Fact Sheet (2024)",
              "Will, Living Rev. Relativ. 17, 4 (2014)", "Weisberg & Huang, ApJ 829, 55 (2016)",
              "Bertotti, Iess, Tortora, Nature 425, 374 (2003)",
              "Planck Collaboration, A&A 641, A6 (2020), Tables 1, 2", "Fixsen, ApJ 707, 916 (2009)",
              T("IAPWS R9-97 (1997): the refractive index of water"), T("IAPWS SR6-08 (2011): liquid water at 0.1 MPa"),
              "IAU 2015 Resolution B3 (Prša et al., AJ 152, 41, 2016)",
              T("NIST Chemistry WebBook SRD 69: water at 0.101325 MPa (IAPWS-95, IAPWS 2008 viscosity)"),
              T("U.S. Standard Atmosphere 1976 (NOAA/NASA/USAF, NASA-TM-X-74335): dry air"),
              T("optical materials: the sources of each entry in DATASETS")],
    "conflicts": [],
}

#: Parts of this module that a world may name on their own in its ``engine_modules`` as "core.data:<key>"
#: (``lfphys.registry.about``): the catalogue entry of only the data the world reads, not of the whole module (a thrown
#: ball's panel then lists the air, not the PDG masses or the cosmology; review R-W F8, the integrator's decision D10).
#: Each entry has the fields of ABOUT that describe data (title, statement, validity, basis); the layer and the kind are
#: the module's. A world that reads data of a part not listed here names the whole module, "core.data".
DATASETS = {
    "air": {
        "title": T("Dry air: density and viscosity"),
        "statement": T("The density of dry air from the ideal gas law and its dynamic viscosity from Sutherland's "
                       "formula, as in the U.S. Standard Atmosphere 1976: 1.2041 kg/m³ and 1.8134·10⁻⁵ Pa·s at "
                       "20 °C and 101 325 Pa."),
        "validity": T("dry air from −50 to 100 °C; against modern reference data at 290–300 K (Lemmon et al. 2000, "
                      "Lemmon & Jacobsen 2004): the density within 2·10⁻⁴, the viscosity within 0.4 %"),
        "basis": [T("U.S. Standard Atmosphere 1976 (NOAA/NASA/USAF, NASA-TM-X-74335): dry air")],
    },
    "water": {
        "title": T("Liquid water at 1 atm: density and viscosity"),
        "statement": T("The density and the dynamic viscosity of liquid water at 101 325 Pa from 0.01 to 40 °C, "
                       "tabulated at whole degrees from the IAPWS formulations (through the NIST Chemistry WebBook) "
                       "and interpolated between them."),
        "validity": T("liquid water at 1 atm, 0.01–40 °C; the viscosity's stated uncertainty 0.17 % at 20 °C; "
                      "between whole degrees the interpolation adds about 10⁻⁴ to the viscosity"),
        "basis": [T("NIST Chemistry WebBook SRD 69: water at 0.101325 MPa (IAPWS-95, IAPWS 2008 viscosity)")],
    },
    "qcd": {
        "title": T("Particle data: the strong coupling and the heavy quarks (PDG 2024)"),
        "statement": T("α_s(M_Z), M_Z, the heavy quark masses, the charmonium and bottomonium masses (PDG 2024)."),
        "validity": T("values with the uncertainties of the source; the PDG 2026 edition differs in some lines "
                      "(stated)"),
        "basis": ["PDG 2024: Phys. Rev. D 110, 030001"],
    },
    # optical materials (EX2 step E35 part 2, 2026-11-18): the numbers in OPTICAL_MATERIALS below, the module
    # lfphys.core.optics.materials; the checks in lfphys/sources/materials_2026-11-18.md
    "schott_n_bk7": {
        "title": T("{glass} optical glass (SCHOTT): refractive index and absorption", glass="N-BK7"),
        "statement": T("SCHOTT's Sellmeier formula n² − 1 = Σ Bᵢλ²/(λ² − Cᵢ) with the data sheet's constants (n = "
                       "{n633:.5f} at 632.8 nm, n_d = {nd:.5f}) and the extinction coefficient κ = −λ ln τᵢ/(4πd) "
                       "from the sheet's internal transmittance τᵢ of a sample d = 25 mm thick (10 mm where only "
                       "that is printed), interpolated between the sheet's wavelengths.", n633=1.51509, nd=1.51680),
        "validity": T("{lo}–{hi} µm at 20 °C and normal air pressure (the sheet's dn/dT constants are recorded for "
                      "other temperatures); λ is the wavelength in air and n the index relative to air (SCHOTT, "
                      "TIE-29); the formula reproduces every index the sheet prints to its last digit (10⁻⁵), a real "
                      "melt differs from these nominal values by up to ±5·10⁻⁵ (TIE-29); κ carries the last digit of "
                      "the printed τᵢ (tens of per cent where τᵢ is close to 1)", lo=0.3, hi=2.5),
        "basis": ["SCHOTT, Optical Glass Data Sheet SCHOTT N-BK7 (as of 01-Dec-2023)",
                  "SCHOTT, TIE-29 Refractive Index and Dispersion (version August 2023)",
                  T("the same constants in the refractiveindex.info database (CC0 1.0), from SCHOTT's catalogue of "
                    "2017-01-20")],
        "checked": T("against SCHOTT's data sheet: the constants, every printed index to its last digit and κ at every "
                     "printed τᵢ (lfphys/tests/test_materials.py)"),
    },
    "schott_n_f2": {
        "title": T("{glass} optical glass (SCHOTT): refractive index and absorption", glass="N-F2"),
        "statement": T("SCHOTT's Sellmeier formula n² − 1 = Σ Bᵢλ²/(λ² − Cᵢ) with the data sheet's constants (n = "
                       "{n633:.5f} at 632.8 nm, n_d = {nd:.5f}) and the extinction coefficient κ = −λ ln τᵢ/(4πd) "
                       "from the sheet's internal transmittance τᵢ of a sample d = 25 mm thick (10 mm where only "
                       "that is printed), interpolated between the sheet's wavelengths.", n633=1.61658, nd=1.62005),
        "validity": T("{lo}–{hi} µm at 20 °C and normal air pressure (the sheet's dn/dT constants are recorded for "
                      "other temperatures); λ is the wavelength in air and n the index relative to air (SCHOTT, "
                      "TIE-29); the formula reproduces every index the sheet prints to its last digit (10⁻⁵), a real "
                      "melt differs from these nominal values by up to ±5·10⁻⁵ (TIE-29); κ carries the last digit of "
                      "the printed τᵢ (tens of per cent where τᵢ is close to 1)", lo=0.365, hi=2.5),
        "basis": ["SCHOTT, Optical Glass Data Sheets (collection, 2025), N-F2 (as of 01-Feb-2014)",
                  "SCHOTT, TIE-29 Refractive Index and Dispersion (version August 2023)",
                  T("the same constants in the refractiveindex.info database (CC0 1.0), from SCHOTT's catalogue of "
                    "2017-01-20")],
        "checked": T("against SCHOTT's data sheet: the constants, every printed index to its last digit and κ at every "
                     "printed τᵢ (lfphys/tests/test_materials.py)"),
    },
    "schott_n_sf11": {
        "title": T("{glass} optical glass (SCHOTT): refractive index and absorption", glass="N-SF11"),
        "statement": T("SCHOTT's Sellmeier formula n² − 1 = Σ Bᵢλ²/(λ² − Cᵢ) with the data sheet's constants (n = "
                       "{n633:.5f} at 632.8 nm, n_d = {nd:.5f}) and the extinction coefficient κ = −λ ln τᵢ/(4πd) "
                       "from the sheet's internal transmittance τᵢ of a sample d = 25 mm thick (10 mm where only "
                       "that is printed), interpolated between the sheet's wavelengths.", n633=1.77860, nd=1.78472),
        "validity": T("{lo}–{hi} µm at 20 °C and normal air pressure (the sheet's dn/dT constants are recorded for "
                      "other temperatures); λ is the wavelength in air and n the index relative to air (SCHOTT, "
                      "TIE-29); the formula reproduces every index the sheet prints to its last digit (10⁻⁵), a real "
                      "melt differs from these nominal values by up to ±5·10⁻⁵ (TIE-29); κ carries the last digit of "
                      "the printed τᵢ (tens of per cent where τᵢ is close to 1)", lo=0.37, hi=2.5),
        "basis": ["SCHOTT, Optical Glass Data Sheets (collection, 2025), N-SF11 (as of 01-Feb-2014)",
                  "SCHOTT, TIE-29 Refractive Index and Dispersion (version August 2023)",
                  T("the same constants in the refractiveindex.info database (CC0 1.0), from SCHOTT's catalogue of "
                    "2017-01-20")],
        "checked": T("against SCHOTT's data sheet: the constants, every printed index to its last digit and κ at every "
                     "printed τᵢ (lfphys/tests/test_materials.py)"),
    },
    "mgf2_dodge_o": {
        "title": T("Magnesium fluoride crystal, ordinary ray (Dodge)"),
        "statement": T("Dodge's Sellmeier formula n² − 1 = Σ Aᵢλ²/(λ² − λᵢ²) for the ordinary ray of crystalline "
                       "MgF₂ at 19 °C, n = 1.37698 at 632.8 nm; κ = 0 (transparent in this range)."),
        "validity": T("{lo}–{hi} µm at {t} °C; the bulk crystal (a deposited film's index differs: see the film "
                      "datasets); whether λ is in air or in vacuum and n relative to air or to vacuum is as the "
                      "database gives it, not checked in the paper (a difference of about 3·10⁻⁴ of n and of λ)",
                      lo=0.2, hi=7.0, t=19),
        "basis": ["M. J. Dodge, Appl. Opt. 23, 1980 (1984)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="MgF2/nk/Dodge-o")],
        "checked": T("the coefficients against two independent transcriptions (the refractiveindex.info database and "
                     "Wikipedia's «Sellmeier equation», which gives λᵢ²); the paper itself was not accessible to "
                     "this check (paywall)"),
    },
    "mgf2_film_rodriguez": {
        "title": T("Magnesium fluoride film, 44 nm (Rodríguez-de Marcos et al.)"),
        "statement": T("The refractive index n and the extinction coefficient κ of a 44 nm MgF₂ film evaporated from "
                       "a tungsten boat at 250 °C, from 30 nm to 2 µm, as the authors gave them to the "
                       "refractiveindex.info database."),
        "validity": T("{lo}–{hi} µm; {what}; interpolated between the table's wavelengths by a shape-preserving cubic "
                      "(PCHIP) in λ, κ in ln κ where it is positive; the interpolation's error, estimated by leaving "
                      "out each node, is stated by lfphys.core.optics.materials; whether λ is in air or in vacuum and "
                      "n relative to air or to vacuum is as the database gives it, not checked in the paper (a "
                      "difference of about 3·10⁻⁴ of n and of λ)", lo=0.03, hi=2.0,
                      what=T("a film of this preparation: a film's constants depend on how it was deposited")),
        "basis": ["L. V. Rodríguez-de Marcos, J. I. Larruquert, J. A. Méndez, J. A. Aznárez, Opt. Mater. Express 7, "
                  "989 (2017)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="MgF2/nk/Rodriguez-de Marcos")],
        "checked": T("the table as the refractiveindex.info database gives it (its file's sha256 in "
                     "lfphys/sources/materials_2026-11-18.md); the paper was not accessible to this check"),
    },
    "sio2_malitson": {
        "title": T("Fused silica (Malitson)"),
        "statement": T("Malitson's Sellmeier formula n² − 1 = Σ Aᵢλ²/(λ² − λᵢ²) for fused silica at 20 °C, n = "
                       "1.45702 at 632.8 nm; κ = 0 (transparent in this range)."),
        "validity": T("{lo}–{hi} µm at {t} °C; bulk glass (a deposited film's index differs: see the film datasets); "
                      "whether λ is in air or in vacuum and n relative to air or to vacuum is as the database gives "
                      "it, not checked in the paper (a difference of about 3·10⁻⁴ of n and of λ)",
                      lo=0.21, hi=3.71, t=20),
        "basis": ["I. H. Malitson, J. Opt. Soc. Am. 55, 1205 (1965)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="SiO2/nk/Malitson")],
        "checked": T("the coefficients against two independent transcriptions (the refractiveindex.info database and "
                     "Wikipedia's «Sellmeier equation», which gives λᵢ²); the paper itself was not accessible to "
                     "this check (paywall)"),
    },
    "sio2_film_gao": {
        "title": T("SiO₂ film, 300 nm (Gao et al.)"),
        "statement": T("The refractive index n and the extinction coefficient κ of a 300 nm SiO₂ film deposited on "
                       "fused silica by ion-assisted electron-beam evaporation, from 0.252 to 1.25 µm, as the authors "
                       "gave them to the refractiveindex.info database."),
        "validity": T("{lo}–{hi} µm; {what}; interpolated between the table's wavelengths by a shape-preserving cubic "
                      "(PCHIP) in λ, κ in ln κ where it is positive; the interpolation's error, estimated by leaving "
                      "out each node, is stated by lfphys.core.optics.materials; whether λ is in air or in vacuum and "
                      "n relative to air or to vacuum is as the database gives it, not checked in the paper (a "
                      "difference of about 3·10⁻⁴ of n and of λ)", lo=0.252, hi=1.25,
                      what=T("a film of this preparation: a film's constants depend on how it was deposited")),
        "basis": ["L. Gao, F. Lemarchand, M. Lequime, J. Eur. Opt. Soc. Rapid Publ. 8, 13010 (2013)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="SiO2/nk/Gao")],
        "checked": T("the table as the refractiveindex.info database gives it (its file's sha256 in "
                     "lfphys/sources/materials_2026-11-18.md); the paper was not accessible to this check"),
    },
    "ta2o5_film_gao": {
        "title": T("Ta₂O₅ film, 400 nm (Gao et al.)"),
        "statement": T("The refractive index n and the extinction coefficient κ of a 400 nm Ta₂O₅ film deposited on "
                       "BK7 by ion-assisted electron-beam evaporation, from 0.35 to 1.8 µm, as the authors gave them "
                       "to the refractiveindex.info database."),
        "validity": T("{lo}–{hi} µm; {what}; interpolated between the table's wavelengths by a shape-preserving cubic "
                      "(PCHIP) in λ, κ in ln κ where it is positive; the interpolation's error, estimated by leaving "
                      "out each node, is stated by lfphys.core.optics.materials; whether λ is in air or in vacuum and "
                      "n relative to air or to vacuum is as the database gives it, not checked in the paper (a "
                      "difference of about 3·10⁻⁴ of n and of λ)", lo=0.35, hi=1.8,
                      what=T("a film of this preparation: a film's constants depend on how it was deposited")),
        "basis": ["L. Gao, F. Lemarchand, M. Lequime, Opt. Express 20, 15734 (2012)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="Ta2O5/nk/Gao")],
        "checked": T("the table as the refractiveindex.info database gives it (its file's sha256 in "
                     "lfphys/sources/materials_2026-11-18.md); the paper was not accessible to this check"),
    },
    "au_johnson_christy": {
        "title": T("Gold (Johnson and Christy)"),
        "statement": T("The refractive index n and the extinction coefficient κ of gold films at room temperature "
                       "(Johnson and Christy 1972), from 0.188 to 1.94 µm, as the refractiveindex.info database "
                       "transcribes them."),
        "validity": T("{lo}–{hi} µm; {what}; interpolated between the table's wavelengths by a shape-preserving cubic "
                      "(PCHIP) in λ, κ in ln κ where it is positive; the interpolation's error, estimated by leaving "
                      "out each node, is stated by lfphys.core.optics.materials; whether λ is in air or in vacuum and "
                      "n relative to air or to vacuum is as the database gives it, not checked in the paper (a "
                      "difference of about 3·10⁻⁴ of n and of λ)", lo=0.1879, hi=1.937,
                      what=T("films at room temperature: a metal's constants depend on the film's preparation")),
        "basis": ["P. B. Johnson, R. W. Christy, Phys. Rev. B 6, 4370 (1972)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="Au/nk/Johnson")],
        "checked": T("the table as the refractiveindex.info database gives it (its file's sha256 in "
                     "lfphys/sources/materials_2026-11-18.md); the paper was not accessible to this check"),
    },
    "ag_johnson_christy": {
        "title": T("Silver (Johnson and Christy)"),
        "statement": T("The refractive index n and the extinction coefficient κ of silver films at room temperature "
                       "(Johnson and Christy 1972), from 0.188 to 1.94 µm, as the refractiveindex.info database "
                       "transcribes them."),
        "validity": T("{lo}–{hi} µm; {what}; interpolated between the table's wavelengths by a shape-preserving cubic "
                      "(PCHIP) in λ, κ in ln κ where it is positive; the interpolation's error, estimated by leaving "
                      "out each node, is stated by lfphys.core.optics.materials; whether λ is in air or in vacuum and "
                      "n relative to air or to vacuum is as the database gives it, not checked in the paper (a "
                      "difference of about 3·10⁻⁴ of n and of λ)", lo=0.1879, hi=1.937,
                      what=T("films at room temperature: a metal's constants depend on the film's preparation")),
        "basis": ["P. B. Johnson, R. W. Christy, Phys. Rev. B 6, 4370 (1972)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="Ag/nk/Johnson")],
        "checked": T("the table as the refractiveindex.info database gives it (its file's sha256 in "
                     "lfphys/sources/materials_2026-11-18.md); the paper was not accessible to this check"),
    },
    "al_rakic": {
        "title": T("Aluminium (Rakić)"),
        "statement": T("The refractive index n and the extinction coefficient κ of evaporated aluminium films (Rakić "
                       "1995), from 0.12 nm to 200 µm, as the refractiveindex.info database transcribes them."),
        "validity": T("{lo}–{hi} µm; {what}; interpolated between the table's wavelengths by a shape-preserving cubic "
                      "(PCHIP) in λ, κ in ln κ where it is positive; the interpolation's error, estimated by leaving "
                      "out each node, is stated by lfphys.core.optics.materials; whether λ is in air or in vacuum and "
                      "n relative to air or to vacuum is as the database gives it, not checked in the paper (a "
                      "difference of about 3·10⁻⁴ of n and of λ)", lo=0.00012399, hi=200.0,
                      what=T("evaporated films: a metal's constants depend on the film's preparation")),
        "basis": ["A. D. Rakić, Appl. Opt. 34, 4755 (1995)",
                  T("refractiveindex.info database (CC0 1.0), file {file}", file="Al/nk/Rakic")],
        "checked": T("the table as the refractiveindex.info database gives it (its file's sha256 in "
                     "lfphys/sources/materials_2026-11-18.md); the paper was not accessible to this check"),
    },
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


# --- optical materials (appended 2026-11-18, EX2 step E35 part 2; used by lfphys.core.optics.materials) ------------
# Each material is a DATASETS entry above. The record of the checks (files, sha256, what was compared):
# lfphys/sources/materials_2026-11-18.md. Data licences: SCHOTT's data sheets are product data (facts: constants and
# measured values, transcribed, not copied as a work); the refractiveindex.info database (M. N. Polyanskiy) is CC0 1.0
# (its LICENSE, checked 2026-11-18); no code was copied.
#
# SCHOTT glasses: indices relative to air, lambda the wavelength in air, at 20 C and 0.10133 MPa (SCHOTT, TIE-29
# "Refractive Index and Dispersion", version August 2023, media.schott.com, sha256 9d07414c481e624c...: "The refractive
# index data given in the data sheets are measured relative to the refractive index measured in air"; its Tab. 1 the
# lines' wavelengths, e.g. d 587.5618 nm, g 435.8343 nm). The Sellmeier constants B_i, C_i (um^2) as SCHOTT's catalogue
# gives them to full precision (the data sheets print the same numbers rounded to 9-10 digits, tests); the internal
# transmittance tau_i as the current data
# sheets print it ("lambda_nm tau_i(10 mm) tau_i(25 mm)", "-" where nothing is printed); dn/dT constants D0, D1, D2,
# E0, E1, lambda_TK (um) as printed, recorded for a later thermal bench (not used: the indices are at 20 C).
# N-BK7: "Optical Glass Datasheet SCHOTT N-BK7", as of 01-Dec-2023 (media.schott.com, content 41e799d0bf874807...;
# sha256 b3287ae9ef985527...). N-F2 and N-SF11: "Optical Glass Datasheet Collection" (media.schott.com, content
# 38cbbe876d324e03..., modified 2025-07-03; sha256 eb70cd8b1c72051b...), their sheets as of 01-Feb-2014. The
# refractiveindex.info database's kappa (from SCHOTT's catalogue of 2017-01-20) equals -lambda ln(tau_i(25 mm))/(4 pi
# 25 mm) of these sheets at every wavelength except N-SF11 at 370 nm (the current sheet prints tau_i(25 mm) = 0.000,
# the database used 0.002; here tau_i(10 mm) = 0.080) and at 1970 nm (0.920 now, 0.915 in the database).
SCHOTT_N_BK7_TAU = """
2500 0.67 0.36
2325 0.79 0.56
1970 0.93 0.84
1530 0.992 0.980
1060 0.999 0.997
700 0.998 0.996
660 0.998 0.994
620 0.998 0.994
580 0.998 0.995
546 0.998 0.996
500 0.998 0.994
460 0.997 0.993
436 0.997 0.992
420 0.997 0.993
405 0.997 0.993
400 0.997 0.992
390 0.996 0.989
380 0.993 0.983
370 0.991 0.977
365 0.988 0.971
350 0.967 0.92
334 0.91 0.78
320 0.77 0.52
310 0.57 0.25
300 0.29 0.05
"""
SCHOTT_N_F2_TAU = """
2500 0.75 0.48
2325 0.84 0.64
1970 0.950 0.88
1530 0.991 0.977
1060 0.998 0.996
700 0.997 0.992
660 0.996 0.990
620 0.996 0.991
580 0.997 0.993
546 0.997 0.992
500 0.994 0.984
460 0.989 0.973
436 0.985 0.963
420 0.980 0.950
405 0.959 0.90
400 0.95 0.87
390 0.89 0.75
380 0.76 0.51
370 0.48 0.16
365 0.28 0.04
"""
SCHOTT_N_SF11_TAU = """
2500 0.830 0.620
2325 0.870 0.700
1970 0.965 0.920
1530 0.994 0.985
1060 0.999 0.998
700 0.994 0.985
660 0.992 0.981
620 0.992 0.981
580 0.994 0.984
546 0.991 0.978
500 0.981 0.953
460 0.967 0.920
436 0.950 0.870
420 0.920 0.810
405 0.850 0.670
400 0.820 0.600
390 0.690 0.390
380 0.430 0.120
370 0.080 0.000
"""


# Films and metals: n and kappa tables as the refractiveindex.info database's files print them (rows "wavelength (um)
# n kappa"). The film data were given to the database by their authors ("Numerical data kindly provided by ..."); the
# metals' tables are the database's transcriptions of the papers. The original papers were not accessible to this
# check (Optica's and APS's paywalls, bot protection of the open-access copies): the values are as the database gives
# them, which lfphys/sources/materials_2026-11-18.md records with each file's sha256.
# database/data/main/MgF2/nk/Rodriguez-de Marcos.yml (sha256 f97bc672a4f3051c...):
# 960 rows, wavelength (um), n, kappa as printed there
MGF2_FILM_RODRIGUEZ_NK = """
2.99919E-02 0.925222 0.121265
3.01236E-02 0.924148 0.121903
3.02558E-02 0.922739 0.122539
3.03887E-02 0.921308 0.124188
3.05221E-02 0.920206 0.125917
3.06560E-02 0.919301 0.127636
3.07906E-02 0.918523 0.129346
3.09258E-02 0.917841 0.131045
3.10616E-02 0.917236 0.132734
3.11979E-02 0.916696 0.134413
3.13349E-02 0.916211 0.136081
3.14724E-02 0.915775 0.137738
3.16106E-02 0.915383 0.139383
3.17494E-02 0.915031 0.141018
3.18887E-02 0.914714 0.142641
3.20287E-02 0.914430 0.144252
3.21693E-02 0.914176 0.145852
3.23105E-02 0.913950 0.147439
3.24524E-02 0.913749 0.149015
3.25948E-02 0.913572 0.150578
3.27379E-02 0.913417 0.152128
3.28817E-02 0.913282 0.153666
3.30260E-02 0.913166 0.155192
3.31710E-02 0.913068 0.156705
3.33166E-02 0.912986 0.158205
3.34629E-02 0.912919 0.159691
3.36098E-02 0.912866 0.161165
3.37573E-02 0.912826 0.162626
3.39055E-02 0.912798 0.164073
3.40543E-02 0.912780 0.165507
3.42038E-02 0.912773 0.166928
3.43540E-02 0.912774 0.168335
3.45048E-02 0.912782 0.169729
3.46563E-02 0.912798 0.171108
3.48084E-02 0.912820 0.172474
3.49612E-02 0.912848 0.173826
3.51147E-02 0.912879 0.175164
3.52688E-02 0.912914 0.176488
3.54237E-02 0.912952 0.177797
3.55792E-02 0.912992 0.179092
3.57354E-02 0.913032 0.180373
3.58922E-02 0.913073 0.181638
3.60498E-02 0.913113 0.182890
3.62080E-02 0.913151 0.184126
3.63670E-02 0.913187 0.185347
3.65266E-02 0.913220 0.186552
3.66870E-02 0.913249 0.187742
3.68480E-02 0.913273 0.188917
3.70098E-02 0.913290 0.190076
3.71723E-02 0.913301 0.191218
3.73355E-02 0.913304 0.192344
3.74994E-02 0.913298 0.193454
3.76640E-02 0.913282 0.194547
3.78293E-02 0.913256 0.195622
3.79954E-02 0.913217 0.196680
3.81622E-02 0.913165 0.197720
3.83297E-02 0.913099 0.198742
3.84980E-02 0.913018 0.199746
3.86670E-02 0.912919 0.200730
3.88367E-02 0.912803 0.201694
3.90072E-02 0.912667 0.202638
3.91784E-02 0.912509 0.203561
3.93504E-02 0.912329 0.204462
3.95232E-02 0.912124 0.205341
3.96967E-02 0.911892 0.206197
3.98709E-02 0.911631 0.207028
4.00460E-02 0.911338 0.207833
4.02218E-02 0.911008 0.208611
4.03983E-02 0.910638 0.209358
4.05757E-02 0.910215 0.210073
4.07538E-02 0.909729 0.210773
4.09327E-02 0.909201 0.211506
4.11124E-02 0.908650 0.212223
4.12929E-02 0.908066 0.212913
4.14742E-02 0.907445 0.213575
4.16562E-02 0.906781 0.214204
4.18391E-02 0.906068 0.214797
4.20228E-02 0.905303 0.215351
4.22072E-02 0.904480 0.215863
4.23925E-02 0.903592 0.216329
4.25786E-02 0.902633 0.216745
4.27655E-02 0.901596 0.217104
4.29533E-02 0.900471 0.217403
4.31418E-02 0.899248 0.217633
4.33312E-02 0.897915 0.217786
4.35214E-02 0.896456 0.217852
4.37125E-02 0.894851 0.217816
4.39044E-02 0.893073 0.217661
4.40971E-02 0.891080 0.217359
4.42907E-02 0.888807 0.216870
4.44851E-02 0.886119 0.216115
4.46804E-02 0.882553 0.214887
4.48766E-02 0.878348 0.215072
4.50736E-02 0.874226 0.215889
4.52714E-02 0.870237 0.216823
4.54702E-02 0.866251 0.217699
4.56698E-02 0.862125 0.218403
4.58703E-02 0.857640 0.218791
4.60716E-02 0.852194 0.218540
4.62739E-02 0.845459 0.219177
4.64770E-02 0.838358 0.222152
4.66811E-02 0.831821 0.226280
4.68860E-02 0.825903 0.230786
4.70918E-02 0.820443 0.235449
4.72985E-02 0.815318 0.240155
4.75062E-02 0.810427 0.244826
4.77147E-02 0.805680 0.249392
4.79242E-02 0.800983 0.253783
4.81346E-02 0.796222 0.257913
4.83459E-02 0.791246 0.261662
4.85581E-02 0.785807 0.264841
4.87713E-02 0.779386 0.267079
4.89854E-02 0.770125 0.267319
4.92004E-02 0.757826 0.271658
4.94164E-02 0.745432 0.281446
4.96333E-02 0.734677 0.293601
4.98512E-02 0.725503 0.306861
5.00701E-02 0.717622 0.320765
5.02899E-02 0.710787 0.335065
5.05106E-02 0.704736 0.349557
5.07324E-02 0.698967 0.363928
5.09551E-02 0.692190 0.378138
5.11788E-02 0.686577 0.399372
5.14034E-02 0.685944 0.422188
5.16291E-02 0.686235 0.436463
5.18557E-02 0.683942 0.453521
5.20834E-02 0.684162 0.478656
5.23120E-02 0.689812 0.502338
5.25417E-02 0.697947 0.521008
5.27723E-02 0.706307 0.537604
5.30040E-02 0.714735 0.553337
5.32367E-02 0.723456 0.568700
5.34704E-02 0.732930 0.584091
5.37051E-02 0.743658 0.598995
5.39409E-02 0.755311 0.611902
5.41777E-02 0.767008 0.622974
5.44155E-02 0.778405 0.633135
5.46544E-02 0.789569 0.642653
5.48943E-02 0.800562 0.651655
5.51353E-02 0.811426 0.660221
5.53773E-02 0.822196 0.668406
5.56204E-02 0.832896 0.676253
5.58646E-02 0.843548 0.683795
5.61098E-02 0.854171 0.691059
5.63562E-02 0.864781 0.698066
5.66036E-02 0.875395 0.704838
5.68520E-02 0.886026 0.711389
5.71016E-02 0.896693 0.717734
5.73523E-02 0.907414 0.723883
5.76041E-02 0.918197 0.729824
5.78569E-02 0.929049 0.735579
5.81109E-02 0.939987 0.741165
5.83660E-02 0.951033 0.746594
5.86222E-02 0.962218 0.751876
5.88796E-02 0.973578 0.757024
5.91381E-02 0.985170 0.762054
5.93977E-02 0.997087 0.766991
5.96584E-02 1.009527 0.771885
5.99203E-02 1.022967 0.776710
6.01834E-02 1.037218 0.779506
6.04476E-02 1.050956 0.779711
6.07129E-02 1.063504 0.779183
6.09794E-02 1.074883 0.778053
6.12471E-02 1.084463 0.776296
6.15160E-02 1.093150 0.777796
6.17861E-02 1.102642 0.780571
6.20573E-02 1.113048 0.783446
6.23297E-02 1.124223 0.786333
6.26033E-02 1.136286 0.789214
6.28782E-02 1.149873 0.792139
6.31542E-02 1.163911 0.791198
6.34314E-02 1.176999 0.789496
6.37099E-02 1.189466 0.787433
6.39896E-02 1.201496 0.785068
6.42705E-02 1.213175 0.782429
6.45526E-02 1.224552 0.779538
6.48360E-02 1.235659 0.776409
6.51206E-02 1.246522 0.773056
6.54065E-02 1.257165 0.769487
6.56936E-02 1.267616 0.765712
6.59820E-02 1.277927 0.761735
6.62717E-02 1.288129 0.757436
6.65626E-02 1.298106 0.752602
6.68548E-02 1.307786 0.747501
6.71483E-02 1.317297 0.742172
6.74431E-02 1.326540 0.736102
6.77391E-02 1.335435 0.729683
6.80365E-02 1.343809 0.722219
6.83352E-02 1.351110 0.713819
6.86352E-02 1.357095 0.705249
6.89365E-02 1.361815 0.696783
6.92391E-02 1.365223 0.688490
6.95430E-02 1.367051 0.680494
6.98483E-02 1.366656 0.673261
7.01550E-02 1.365613 0.671523
7.04629E-02 1.366384 0.672269
7.07723E-02 1.368730 0.672676
7.10829E-02 1.371698 0.672939
7.13950E-02 1.374723 0.673201
7.17084E-02 1.376843 0.673776
7.20232E-02 1.380593 0.681587
7.23394E-02 1.390648 0.691890
7.26569E-02 1.404711 0.693496
7.29759E-02 1.417600 0.689920
7.32962E-02 1.428864 0.686483
7.36180E-02 1.439793 0.682902
7.39412E-02 1.450948 0.678979
7.42658E-02 1.462661 0.674005
7.45918E-02 1.474084 0.665948
7.49193E-02 1.483691 0.655694
7.52481E-02 1.491426 0.645833
7.55785E-02 1.497995 0.636216
7.59103E-02 1.503640 0.626804
7.62435E-02 1.508482 0.617591
7.65782E-02 1.512582 0.608593
7.69144E-02 1.515960 0.599843
7.72520E-02 1.518591 0.591411
7.75911E-02 1.520463 0.583570
7.79318E-02 1.521958 0.577077
7.82739E-02 1.523838 0.571832
7.86175E-02 1.526195 0.566353
7.89626E-02 1.528649 0.560782
7.93092E-02 1.531088 0.555171
7.96574E-02 1.533458 0.549546
8.00071E-02 1.535733 0.543925
8.03583E-02 1.537895 0.538318
8.07111E-02 1.539937 0.532735
8.10654E-02 1.541852 0.527179
8.14213E-02 1.543639 0.521653
8.17787E-02 1.545303 0.516154
8.21377E-02 1.546854 0.510664
8.24983E-02 1.548272 0.505085
8.28604E-02 1.549378 0.499208
8.32242E-02 1.549932 0.493281
8.35895E-02 1.550008 0.487919
8.39565E-02 1.550052 0.483356
8.43250E-02 1.550201 0.478763
8.46952E-02 1.550279 0.474220
8.50670E-02 1.550241 0.469755
8.54405E-02 1.550070 0.465379
8.58155E-02 1.549761 0.461091
8.61923E-02 1.549318 0.456861
8.65706E-02 1.548716 0.452539
8.69507E-02 1.547536 0.447532
8.73324E-02 1.545100 0.442340
8.77158E-02 1.541323 0.438345
8.81008E-02 1.536346 0.435819
8.84876E-02 1.530100 0.436086
8.88760E-02 1.526843 0.446266
8.92662E-02 1.533004 0.459205
8.96581E-02 1.542282 0.453815
9.00517E-02 1.544354 0.442449
9.04470E-02 1.539810 0.437260
9.08440E-02 1.537663 0.446421
9.12428E-02 1.542344 0.452922
9.16434E-02 1.550929 0.455904
9.20457E-02 1.561941 0.453592
9.24497E-02 1.570120 0.439965
9.28556E-02 1.572935 0.427591
9.32632E-02 1.572951 0.415678
9.36726E-02 1.569040 0.401269
9.40838E-02 1.560470 0.390121
9.44969E-02 1.548921 0.383402
9.49117E-02 1.536161 0.382669
9.53284E-02 1.527699 0.392156
9.57468E-02 1.524122 0.395446
9.61672E-02 1.520482 0.395566
9.65893E-02 1.516092 0.394990
9.70133E-02 1.509704 0.390313
9.74392E-02 1.493412 0.377165
9.78670E-02 1.468672 0.384131
9.82966E-02 1.451511 0.411995
9.87281E-02 1.443294 0.430270
9.91615E-02 1.430197 0.438304
9.95968E-02 1.410291 0.461196
1.00034E-01 1.394670 0.504175
1.00473E-01 1.394182 0.561164
1.00914E-01 1.406965 0.608032
1.01357E-01 1.426614 0.653320
1.01802E-01 1.450337 0.693004
1.02249E-01 1.478988 0.740010
1.02698E-01 1.518661 0.791328
1.03149E-01 1.569325 0.838845
1.03602E-01 1.637783 0.898753
1.04056E-01 1.741224 0.958900
1.04513E-01 1.880297 0.972986
1.04972E-01 2.014147 0.887666
1.05433E-01 2.097264 0.750410
1.05896E-01 2.121767 0.616078
1.06361E-01 2.111039 0.530400
1.06827E-01 2.101072 0.492356
1.07296E-01 2.106338 0.459934
1.07767E-01 2.123857 0.423267
1.08241E-01 2.142700 0.358978
1.08716E-01 2.141217 0.267565
1.09193E-01 2.106695 0.178498
1.09672E-01 2.052598 0.131735
1.10154E-01 2.006438 0.124047
1.10637E-01 1.974922 0.116392
1.11123E-01 1.950236 0.108771
1.11611E-01 1.929626 0.101183
1.12101E-01 1.911703 0.093629
1.12593E-01 1.895621 0.086107
1.13087E-01 1.880776 0.078618
1.13584E-01 1.866709 0.071337
1.14082E-01 1.853466 0.064950
1.14583E-01 1.841058 0.058591
1.15086E-01 1.829123 0.052260
1.15591E-01 1.817382 0.045956
1.16099E-01 1.805479 0.039680
1.16608E-01 1.792667 0.033503
1.17120E-01 1.780255 0.031640
1.17634E-01 1.769535 0.029786
1.18151E-01 1.759754 0.027940
1.18669E-01 1.750613 0.026102
1.19190E-01 1.741882 0.024272
1.19714E-01 1.733613 0.022941
1.20239E-01 1.725884 0.021625
1.20767E-01 1.718549 0.020315
1.21297E-01 1.711487 0.019010
1.21830E-01 1.704700 0.017978
1.22364E-01 1.698347 0.017231
1.22902E-01 1.692497 0.016486
1.23441E-01 1.687244 0.015745
1.23983E-01 1.682190 0.013826
1.24527E-01 1.676660 0.011427
1.25074E-01 1.670330 0.009037
1.25623E-01 1.663965 0.008738
1.26175E-01 1.658303 0.008544
1.26728E-01 1.653062 0.008351
1.27285E-01 1.648120 0.008158
1.27844E-01 1.643419 0.007966
1.28405E-01 1.638921 0.007775
1.28968E-01 1.634597 0.007585
1.29535E-01 1.630418 0.007396
1.30103E-01 1.626390 0.007279
1.30674E-01 1.622525 0.007171
1.31248E-01 1.618808 0.007064
1.31824E-01 1.615223 0.006958
1.32403E-01 1.611762 0.006851
1.32984E-01 1.608424 0.006746
1.33568E-01 1.605201 0.006619
1.34154E-01 1.602063 0.006439
1.34743E-01 1.598988 0.006260
1.35335E-01 1.595979 0.006082
1.35929E-01 1.593031 0.005904
1.36526E-01 1.590134 0.005725
1.37125E-01 1.587268 0.005547
1.37727E-01 1.584389 0.005380
1.38331E-01 1.581601 0.005527
1.38939E-01 1.579009 0.005673
1.39549E-01 1.576586 0.005819
1.40161E-01 1.574295 0.005851
1.40777E-01 1.572076 0.005798
1.41395E-01 1.569897 0.005664
1.42015E-01 1.567720 0.005460
1.42639E-01 1.565534 0.005258
1.43265E-01 1.563341 0.005056
1.43894E-01 1.561128 0.004881
1.44525E-01 1.558963 0.004884
1.45160E-01 1.556899 0.004887
1.45797E-01 1.554910 0.004890
1.46437E-01 1.552990 0.004893
1.47080E-01 1.551137 0.004881
1.47726E-01 1.549326 0.004813
1.48374E-01 1.547537 0.004744
1.49026E-01 1.545778 0.004677
1.49680E-01 1.544049 0.004609
1.50337E-01 1.542352 0.004542
1.50997E-01 1.540682 0.004475
1.51660E-01 1.539036 0.004409
1.52325E-01 1.537423 0.004378
1.52994E-01 1.535856 0.004348
1.53666E-01 1.534329 0.004318
1.54340E-01 1.532841 0.004289
1.55018E-01 1.531395 0.004259
1.55698E-01 1.529999 0.004229
1.56382E-01 1.528655 0.004169
1.57068E-01 1.527324 0.004018
1.57758E-01 1.525980 0.003868
1.58450E-01 1.524637 0.003718
1.59146E-01 1.523300 0.003569
1.59845E-01 1.521966 0.003421
1.60546E-01 1.520641 0.003289
1.61251E-01 1.519329 0.003161
1.61959E-01 1.518027 0.003033
1.62670E-01 1.516726 0.002906
1.63384E-01 1.515418 0.002795
1.64101E-01 1.514134 0.002762
1.64822E-01 1.512894 0.002729
1.65545E-01 1.511685 0.002697
1.66272E-01 1.510503 0.002665
1.67002E-01 1.509344 0.002633
1.67735E-01 1.508206 0.002601
1.68471E-01 1.507089 0.002569
1.69211E-01 1.505992 0.002537
1.69954E-01 1.504913 0.002506
1.70700E-01 1.503851 0.002475
1.71449E-01 1.502807 0.002443
1.72202E-01 1.501780 0.002412
1.72958E-01 1.500768 0.002381
1.73717E-01 1.499772 0.002350
1.74480E-01 1.498792 0.002320
1.75246E-01 1.497826 0.002289
1.76015E-01 1.496874 0.002257
1.76788E-01 1.495935 0.002226
1.77564E-01 1.495009 0.002195
1.78343E-01 1.494096 0.002164
1.79126E-01 1.493195 0.002133
1.79912E-01 1.492306 0.002103
1.80702E-01 1.491427 0.002072
1.81496E-01 1.490558 0.002041
1.82292E-01 1.489694 0.002011
1.83093E-01 1.488843 0.002000
1.83896E-01 1.488009 0.001990
1.84704E-01 1.487190 0.001980
1.85514E-01 1.486385 0.001970
1.86329E-01 1.485592 0.001960
1.87147E-01 1.484811 0.001950
1.87968E-01 1.484042 0.001941
1.88793E-01 1.483285 0.001930
1.89622E-01 1.482538 0.001921
1.90455E-01 1.481802 0.001912
1.91291E-01 1.481077 0.001902
1.92131E-01 1.480362 0.001893
1.92974E-01 1.479657 0.001883
1.93821E-01 1.478961 0.001873
1.94672E-01 1.478275 0.001864
1.95527E-01 1.477599 0.001855
1.96385E-01 1.476931 0.001846
1.97247E-01 1.476273 0.001837
1.98113E-01 1.475624 0.001827
1.98983E-01 1.474983 0.001818
1.99856E-01 1.474350 0.001809
2.00733E-01 1.473726 0.001800
2.01615E-01 1.473110 0.001791
2.02500E-01 1.472503 0.001783
2.03389E-01 1.471903 0.001774
2.04282E-01 1.471311 0.001766
2.05178E-01 1.470727 0.001757
2.06079E-01 1.470150 0.001748
2.06984E-01 1.469580 0.001739
2.07892E-01 1.469017 0.001731
2.08805E-01 1.468462 0.001723
2.09722E-01 1.467914 0.001714
2.10642E-01 1.467373 0.001706
2.11567E-01 1.466838 0.001697
2.12496E-01 1.466310 0.001690
2.13429E-01 1.465789 0.001681
2.14365E-01 1.465274 0.001673
2.15307E-01 1.464765 0.001665
2.16252E-01 1.464263 0.001657
2.17201E-01 1.463766 0.001649
2.18155E-01 1.463276 0.001640
2.19112E-01 1.462792 0.001633
2.20074E-01 1.462313 0.001625
2.21040E-01 1.461840 0.001617
2.22011E-01 1.461373 0.001609
2.22985E-01 1.460912 0.001602
2.23964E-01 1.460456 0.001594
2.24947E-01 1.460006 0.001586
2.25935E-01 1.459560 0.001579
2.26927E-01 1.459120 0.001571
2.27923E-01 1.458686 0.001563
2.28923E-01 1.458256 0.001555
2.29928E-01 1.457831 0.001549
2.30938E-01 1.457412 0.001541
2.31951E-01 1.456997 0.001534
2.32970E-01 1.456587 0.001526
2.33992E-01 1.456181 0.001519
2.35020E-01 1.455781 0.001512
2.36051E-01 1.455385 0.001504
2.37088E-01 1.454993 0.001498
2.38128E-01 1.454606 0.001490
2.39174E-01 1.454224 0.001483
2.40224E-01 1.453846 0.001476
2.41278E-01 1.453472 0.001469
2.42337E-01 1.453102 0.001462
2.43401E-01 1.452737 0.001455
2.44470E-01 1.452375 0.001448
2.45543E-01 1.452018 0.001442
2.46621E-01 1.451664 0.001434
2.47703E-01 1.451315 0.001428
2.48791E-01 1.450969 0.001421
2.49883E-01 1.450628 0.001414
2.50980E-01 1.450290 0.001407
2.52082E-01 1.449955 0.001401
2.53188E-01 1.449625 0.001395
2.54300E-01 1.449299 0.001387
2.55416E-01 1.448975 0.001381
2.56537E-01 1.448655 0.001375
2.57664E-01 1.448339 0.001368
2.58795E-01 1.448027 0.001361
2.59931E-01 1.447717 0.001355
2.61072E-01 1.447411 0.001349
2.62218E-01 1.447109 0.001343
2.63369E-01 1.446809 0.001336
2.64525E-01 1.446513 0.001330
2.65687E-01 1.446220 0.001324
2.66853E-01 1.445930 0.001318
2.68024E-01 1.445644 0.001312
2.69201E-01 1.445360 0.001305
2.70383E-01 1.445079 0.001299
2.71570E-01 1.444802 0.001293
2.72762E-01 1.444527 0.001287
2.73959E-01 1.444255 0.001281
2.75162E-01 1.443987 0.001276
2.76370E-01 1.443721 0.001269
2.77583E-01 1.443457 0.001263
2.78802E-01 1.443197 0.001257
2.80025E-01 1.442939 0.001252
2.81255E-01 1.442684 0.001246
2.82489E-01 1.442432 0.001240
2.83730E-01 1.442183 0.001234
2.84975E-01 1.441936 0.001229
2.86226E-01 1.441691 0.001222
2.87483E-01 1.441449 0.001217
2.88745E-01 1.441210 0.001211
2.90012E-01 1.440973 0.001206
2.91285E-01 1.440738 0.001200
2.92564E-01 1.440506 0.001195
2.93848E-01 1.440277 0.001189
2.95138E-01 1.440050 0.001184
2.96434E-01 1.439825 0.001178
2.97735E-01 1.439602 0.001173
2.99042E-01 1.439382 0.001168
3.00355E-01 1.439164 0.001162
3.01674E-01 1.438948 0.001157
3.02998E-01 1.438735 0.001151
3.04328E-01 1.438524 0.001145
3.05664E-01 1.438314 0.001140
3.07006E-01 1.438107 0.001135
3.08354E-01 1.437902 0.001130
3.09707E-01 1.437699 0.001125
3.11067E-01 1.437498 0.001119
3.12432E-01 1.437299 0.001114
3.13804E-01 1.437102 0.001109
3.15182E-01 1.436907 0.001104
3.16565E-01 1.436714 0.001099
3.17955E-01 1.436523 0.001094
3.19351E-01 1.436334 0.001089
3.20753E-01 1.436147 0.001084
3.22161E-01 1.435962 0.001079
3.23575E-01 1.435779 0.001074
3.24995E-01 1.435597 0.001069
3.26422E-01 1.435417 0.001064
3.27855E-01 1.435239 0.001059
3.29294E-01 1.435063 0.001054
3.30740E-01 1.434889 0.001050
3.32192E-01 1.434716 0.001045
3.33650E-01 1.434545 0.001040
3.35115E-01 1.434375 0.001035
3.36586E-01 1.434208 0.001030
3.38063E-01 1.434041 0.001026
3.39547E-01 1.433877 0.001022
3.41038E-01 1.433715 0.001017
3.42535E-01 1.433554 0.001013
3.44039E-01 1.433395 0.001008
3.45549E-01 1.433237 0.001003
3.47066E-01 1.433080 0.000999
3.48590E-01 1.432926 0.000994
3.50120E-01 1.432772 0.000990
3.51657E-01 1.432621 0.000985
3.53201E-01 1.432470 0.000980
3.54751E-01 1.432321 0.000976
3.56309E-01 1.432174 0.000971
3.57873E-01 1.432028 0.000967
3.59444E-01 1.431883 0.000963
3.61022E-01 1.431740 0.000958
3.62607E-01 1.431598 0.000954
3.64198E-01 1.431458 0.000949
3.65797E-01 1.431318 0.000945
3.67403E-01 1.431181 0.000942
3.69016E-01 1.431045 0.000937
3.70636E-01 1.430910 0.000933
3.72263E-01 1.430776 0.000929
3.73897E-01 1.430644 0.000924
3.75538E-01 1.430513 0.000920
3.77187E-01 1.430383 0.000916
3.78843E-01 1.430254 0.000912
3.80506E-01 1.430127 0.000907
3.82176E-01 1.430001 0.000903
3.83854E-01 1.429876 0.000899
3.85539E-01 1.429752 0.000895
3.87232E-01 1.429629 0.000892
3.88931E-01 1.429508 0.000888
3.90639E-01 1.429388 0.000883
3.92354E-01 1.429269 0.000879
3.94076E-01 1.429151 0.000875
3.95806E-01 1.429034 0.000871
3.97544E-01 1.428919 0.000867
3.99289E-01 1.428804 0.000863
4.01042E-01 1.428690 0.000859
4.02802E-01 1.428578 0.000855
4.04570E-01 1.428466 0.000852
4.06346E-01 1.428356 0.000848
4.08130E-01 1.428247 0.000844
4.09922E-01 1.428139 0.000840
4.11721E-01 1.428032 0.000837
4.13529E-01 1.427926 0.000833
4.15344E-01 1.427820 0.000829
4.17167E-01 1.427716 0.000825
4.18999E-01 1.427613 0.000821
4.20838E-01 1.427510 0.000818
4.22686E-01 1.427410 0.000815
4.24541E-01 1.427309 0.000811
4.26405E-01 1.427210 0.000807
4.28277E-01 1.427112 0.000803
4.30157E-01 1.427014 0.000800
4.32045E-01 1.426918 0.000796
4.33942E-01 1.426822 0.000792
4.35847E-01 1.426727 0.000789
4.37760E-01 1.426633 0.000786
4.39682E-01 1.426540 0.000782
4.41612E-01 1.426448 0.000779
4.43551E-01 1.426357 0.000775
4.45498E-01 1.426267 0.000771
4.47453E-01 1.426177 0.000768
4.49418E-01 1.426088 0.000764
4.51391E-01 1.426000 0.000761
4.53372E-01 1.425913 0.000758
4.55362E-01 1.425827 0.000755
4.57361E-01 1.425742 0.000751
4.59369E-01 1.425657 0.000748
4.61386E-01 1.425573 0.000744
4.63411E-01 1.425490 0.000741
4.65446E-01 1.425408 0.000737
4.67489E-01 1.425326 0.000735
4.69541E-01 1.425246 0.000731
4.71602E-01 1.425166 0.000728
4.73673E-01 1.425086 0.000725
4.75752E-01 1.425008 0.000721
4.77841E-01 1.424930 0.000718
4.79938E-01 1.424853 0.000715
4.82045E-01 1.424776 0.000711
4.84161E-01 1.424700 0.000709
4.86287E-01 1.424626 0.000706
4.88421E-01 1.424552 0.000702
4.90566E-01 1.424478 0.000699
4.92719E-01 1.424405 0.000696
4.94882E-01 1.424333 0.000693
4.97055E-01 1.424261 0.000689
4.99237E-01 1.424190 0.000687
5.01428E-01 1.424120 0.000684
5.03629E-01 1.424051 0.000681
5.05840E-01 1.423982 0.000678
5.08061E-01 1.423913 0.000674
5.10291E-01 1.423846 0.000671
5.12531E-01 1.423778 0.000668
5.14781E-01 1.423712 0.000665
5.17041E-01 1.423646 0.000663
5.19311E-01 1.423581 0.000660
5.21591E-01 1.423516 0.000657
5.23880E-01 1.423452 0.000654
5.26180E-01 1.423389 0.000651
5.28490E-01 1.423326 0.000648
5.30810E-01 1.423263 0.000645
5.33140E-01 1.423201 0.000643
5.35481E-01 1.423141 0.000640
5.37831E-01 1.423080 0.000637
5.40192E-01 1.423020 0.000634
5.42564E-01 1.422961 0.000631
5.44946E-01 1.422902 0.000628
5.47338E-01 1.422843 0.000625
5.49741E-01 1.422785 0.000622
5.52154E-01 1.422727 0.000620
5.54578E-01 1.422671 0.000617
5.57012E-01 1.422615 0.000614
5.59458E-01 1.422559 0.000611
5.61914E-01 1.422504 0.000609
5.64380E-01 1.422449 0.000606
5.66858E-01 1.422394 0.000603
5.69346E-01 1.422340 0.000601
5.71846E-01 1.422287 0.000598
5.74356E-01 1.422235 0.000596
5.76877E-01 1.422182 0.000593
5.79410E-01 1.422130 0.000590
5.81953E-01 1.422079 0.000587
5.84508E-01 1.422028 0.000585
5.87074E-01 1.421977 0.000583
5.89651E-01 1.421927 0.000580
5.92240E-01 1.421878 0.000577
5.94840E-01 1.421829 0.000575
5.97451E-01 1.421780 0.000572
6.00074E-01 1.421732 0.000569
6.02708E-01 1.421684 0.000567
6.05354E-01 1.421636 0.000564
6.08011E-01 1.421590 0.000562
6.10680E-01 1.421543 0.000560
6.13361E-01 1.421497 0.000557
6.16054E-01 1.421452 0.000555
6.18758E-01 1.421406 0.000552
6.21475E-01 1.421361 0.000549
6.24203E-01 1.421317 0.000547
6.26943E-01 1.421273 0.000545
6.29695E-01 1.421229 0.000543
6.32459E-01 1.421186 0.000540
6.35236E-01 1.421143 0.000538
6.38025E-01 1.421101 0.000535
6.40825E-01 1.421059 0.000533
6.43639E-01 1.421017 0.000530
6.46464E-01 1.420975 0.000528
6.49302E-01 1.420935 0.000526
6.52152E-01 1.420894 0.000524
6.55015E-01 1.420854 0.000521
6.57891E-01 1.420814 0.000519
6.60779E-01 1.420775 0.000516
6.63680E-01 1.420736 0.000514
6.66593E-01 1.420697 0.000512
6.69519E-01 1.420658 0.000510
6.72458E-01 1.420620 0.000508
6.75410E-01 1.420583 0.000505
6.78375E-01 1.420545 0.000503
6.81353E-01 1.420508 0.000501
6.84345E-01 1.420471 0.000498
6.87349E-01 1.420435 0.000496
6.90366E-01 1.420398 0.000494
6.93397E-01 1.420363 0.000492
6.96441E-01 1.420328 0.000490
6.99498E-01 1.420293 0.000488
7.02569E-01 1.420258 0.000486
7.05653E-01 1.420223 0.000483
7.08751E-01 1.420189 0.000481
7.11862E-01 1.420155 0.000479
7.14987E-01 1.420121 0.000477
7.18126E-01 1.420088 0.000475
7.21278E-01 1.420055 0.000473
7.24445E-01 1.420023 0.000471
7.27625E-01 1.419990 0.000469
7.30819E-01 1.419958 0.000466
7.34027E-01 1.419926 0.000464
7.37250E-01 1.419895 0.000462
7.40486E-01 1.419863 0.000460
7.43737E-01 1.419832 0.000459
7.47002E-01 1.419802 0.000457
7.50281E-01 1.419772 0.000455
7.53575E-01 1.419742 0.000452
7.56883E-01 1.419712 0.000450
7.60205E-01 1.419682 0.000448
7.63543E-01 1.419653 0.000446
7.66895E-01 1.419623 0.000444
7.70261E-01 1.419594 0.000443
7.73642E-01 1.419566 0.000441
7.77039E-01 1.419538 0.000439
7.80450E-01 1.419510 0.000437
7.83876E-01 1.419482 0.000435
7.87317E-01 1.419454 0.000433
7.90773E-01 1.419427 0.000431
7.94245E-01 1.419400 0.000429
7.97731E-01 1.419373 0.000428
8.01233E-01 1.419347 0.000426
8.04751E-01 1.419320 0.000424
8.08283E-01 1.419294 0.000422
8.11832E-01 1.419268 0.000420
8.15396E-01 1.419243 0.000418
8.18975E-01 1.419217 0.000416
8.22570E-01 1.419192 0.000414
8.26181E-01 1.419167 0.000412
8.29808E-01 1.419142 0.000411
8.33451E-01 1.419118 0.000409
8.37110E-01 1.419094 0.000407
8.40785E-01 1.419070 0.000405
8.44476E-01 1.419046 0.000403
8.48183E-01 1.419022 0.000401
8.51906E-01 1.418998 0.000400
8.55646E-01 1.418975 0.000398
8.59402E-01 1.418952 0.000396
8.63175E-01 1.418929 0.000395
8.66964E-01 1.418907 0.000393
8.70770E-01 1.418884 0.000391
8.74593E-01 1.418862 0.000389
8.78432E-01 1.418840 0.000388
8.82288E-01 1.418818 0.000386
8.86161E-01 1.418796 0.000384
8.90052E-01 1.418775 0.000382
8.93959E-01 1.418753 0.000381
8.97883E-01 1.418732 0.000380
9.01825E-01 1.418712 0.000378
9.05784E-01 1.418691 0.000376
9.09760E-01 1.418671 0.000374
9.13754E-01 1.418650 0.000373
9.17765E-01 1.418630 0.000371
9.21794E-01 1.418610 0.000369
9.25841E-01 1.418590 0.000367
9.29905E-01 1.418570 0.000366
9.33987E-01 1.418551 0.000365
9.38087E-01 1.418532 0.000363
9.42205E-01 1.418513 0.000361
9.46342E-01 1.418494 0.000360
9.50496E-01 1.418475 0.000358
9.54669E-01 1.418457 0.000356
9.58859E-01 1.418438 0.000355
9.63069E-01 1.418420 0.000353
9.67296E-01 1.418401 0.000351
9.71543E-01 1.418383 0.000351
9.75808E-01 1.418366 0.000349
9.80092E-01 1.418348 0.000347
9.84394E-01 1.418331 0.000346
9.88715E-01 1.418314 0.000344
9.93056E-01 1.418296 0.000343
9.97415E-01 1.418279 0.000341
1.00179E+00 1.418262 0.000339
1.00619E+00 1.418246 0.000338
1.01061E+00 1.418229 0.000336
1.01505E+00 1.418212 0.000336
1.01950E+00 1.418196 0.000334
1.02398E+00 1.418180 0.000333
1.02847E+00 1.418164 0.000331
1.03299E+00 1.418149 0.000329
1.03752E+00 1.418133 0.000328
1.04208E+00 1.418117 0.000326
1.04665E+00 1.418102 0.000325
1.05125E+00 1.418086 0.000323
1.05586E+00 1.418071 0.000322
1.06050E+00 1.418056 0.000321
1.06515E+00 1.418041 0.000320
1.06983E+00 1.418027 0.000318
1.07452E+00 1.418012 0.000317
1.07924E+00 1.417998 0.000315
1.08398E+00 1.417983 0.000314
1.08874E+00 1.417969 0.000312
1.09352E+00 1.417955 0.000311
1.09832E+00 1.417941 0.000309
1.10314E+00 1.417927 0.000308
1.10798E+00 1.417913 0.000306
1.11284E+00 1.417899 0.000306
1.11773E+00 1.417886 0.000305
1.12264E+00 1.417872 0.000303
1.12756E+00 1.417859 0.000302
1.13251E+00 1.417846 0.000300
1.13749E+00 1.417833 0.000299
1.14248E+00 1.417820 0.000298
1.14750E+00 1.417807 0.000296
1.15253E+00 1.417795 0.000295
1.15759E+00 1.417782 0.000293
1.16267E+00 1.417769 0.000292
1.16778E+00 1.417757 0.000292
1.17290E+00 1.417745 0.000290
1.17805E+00 1.417733 0.000289
1.18322E+00 1.417721 0.000288
1.18842E+00 1.417709 0.000286
1.19364E+00 1.417697 0.000285
1.19888E+00 1.417685 0.000284
1.20414E+00 1.417674 0.000282
1.20942E+00 1.417662 0.000281
1.21473E+00 1.417650 0.000280
1.22007E+00 1.417639 0.000278
1.22542E+00 1.417628 0.000278
1.23080E+00 1.417617 0.000277
1.23621E+00 1.417606 0.000275
1.24163E+00 1.417595 0.000274
1.24708E+00 1.417584 0.000273
1.25256E+00 1.417574 0.000271
1.25806E+00 1.417563 0.000270
1.26358E+00 1.417552 0.000269
1.26913E+00 1.417542 0.000268
1.27470E+00 1.417531 0.000266
1.28029E+00 1.417521 0.000265
1.28591E+00 1.417511 0.000264
1.29156E+00 1.417500 0.000263
1.29723E+00 1.417490 0.000262
1.30292E+00 1.417481 0.000261
1.30864E+00 1.417471 0.000260
1.31439E+00 1.417461 0.000259
1.32016E+00 1.417452 0.000258
1.32595E+00 1.417442 0.000256
1.33177E+00 1.417433 0.000255
1.33762E+00 1.417423 0.000254
1.34349E+00 1.417414 0.000253
1.34939E+00 1.417405 0.000252
1.35531E+00 1.417395 0.000250
1.36126E+00 1.417386 0.000249
1.36724E+00 1.417377 0.000249
1.37324E+00 1.417368 0.000248
1.37927E+00 1.417360 0.000247
1.38532E+00 1.417351 0.000246
1.39141E+00 1.417342 0.000244
1.39751E+00 1.417334 0.000243
1.40365E+00 1.417325 0.000242
1.40981E+00 1.417317 0.000241
1.41600E+00 1.417308 0.000240
1.42222E+00 1.417300 0.000239
1.42846E+00 1.417292 0.000238
1.43473E+00 1.417283 0.000236
1.44103E+00 1.417275 0.000235
1.44735E+00 1.417267 0.000235
1.45371E+00 1.417259 0.000234
1.46009E+00 1.417251 0.000233
1.46650E+00 1.417244 0.000232
1.47294E+00 1.417236 0.000231
1.47940E+00 1.417228 0.000230
1.48590E+00 1.417221 0.000229
1.49242E+00 1.417213 0.000228
1.49897E+00 1.417206 0.000227
1.50555E+00 1.417198 0.000225
1.51216E+00 1.417191 0.000224
1.51880E+00 1.417184 0.000223
1.52547E+00 1.417176 0.000222
1.53216E+00 1.417169 0.000221
1.53889E+00 1.417162 0.000221
1.54565E+00 1.417155 0.000220
1.55243E+00 1.417148 0.000219
1.55925E+00 1.417141 0.000218
1.56609E+00 1.417134 0.000217
1.57297E+00 1.417128 0.000216
1.57987E+00 1.417121 0.000215
1.58681E+00 1.417114 0.000214
1.59377E+00 1.417108 0.000213
1.60077E+00 1.417101 0.000212
1.60780E+00 1.417095 0.000211
1.61485E+00 1.417088 0.000210
1.62194E+00 1.417081 0.000209
1.62906E+00 1.417075 0.000208
1.63621E+00 1.417069 0.000208
1.64340E+00 1.417063 0.000207
1.65061E+00 1.417057 0.000206
1.65786E+00 1.417051 0.000205
1.66514E+00 1.417045 0.000204
1.67245E+00 1.417039 0.000203
1.67979E+00 1.417033 0.000202
1.68716E+00 1.417027 0.000201
1.69457E+00 1.417021 0.000200
1.70201E+00 1.417015 0.000200
1.70948E+00 1.417009 0.000199
1.71698E+00 1.417004 0.000198
1.72452E+00 1.416998 0.000197
1.73209E+00 1.416992 0.000196
1.73969E+00 1.416987 0.000195
1.74733E+00 1.416981 0.000194
1.75500E+00 1.416975 0.000194
1.76271E+00 1.416970 0.000193
1.77045E+00 1.416965 0.000192
1.77822E+00 1.416960 0.000191
1.78602E+00 1.416955 0.000190
1.79386E+00 1.416950 0.000190
1.80174E+00 1.416944 0.000189
1.80965E+00 1.416939 0.000188
1.81759E+00 1.416934 0.000187
1.82557E+00 1.416929 0.000186
1.83359E+00 1.416924 0.000185
1.84163E+00 1.416919 0.000184
1.84972E+00 1.416914 0.000183
1.85784E+00 1.416909 0.000183
1.86600E+00 1.416904 0.000182
1.87419E+00 1.416900 0.000181
1.88241E+00 1.416895 0.000180
1.89068E+00 1.416890 0.000180
1.89898E+00 1.416885 0.000179
1.90731E+00 1.416881 0.000178
1.91569E+00 1.416877 0.000178
1.92410E+00 1.416872 0.000177
1.93254E+00 1.416868 0.000176
1.94103E+00 1.416863 0.000175
1.94955E+00 1.416859 0.000174
1.95811E+00 1.416854 0.000173
1.96670E+00 1.416850 0.000173
1.97534E+00 1.416846 0.000172
1.98401E+00 1.416842 0.000171
1.99272E+00 1.416837 0.000170
2.00146E+00 1.416833 0.000169
"""

# database/data/main/SiO2/nk/Gao.yml (sha256 18803e6bde85b356...): 500 rows, wavelength (um), n, kappa as printed there
SIO2_FILM_GAO_NK = """
0.252 1.523846 0.001211
0.254 1.522945 0.001171
0.256 1.522066 0.001131
0.258 1.521208 0.001093
0.260 1.520370 0.001055
0.262 1.519552 0.001019
0.264 1.518753 0.000983
0.266 1.517972 0.000949
0.268 1.517209 0.000915
0.270 1.516463 0.000882
0.272 1.515734 0.000850
0.274 1.515021 0.000819
0.276 1.514325 0.000789
0.278 1.513643 0.000759
0.280 1.512977 0.000730
0.282 1.512325 0.000702
0.284 1.511687 0.000675
0.286 1.511063 0.000649
0.288 1.510452 0.000623
0.290 1.509854 0.000598
0.292 1.509268 0.000574
0.294 1.508695 0.000550
0.296 1.508134 0.000527
0.298 1.507584 0.000505
0.300 1.507046 0.000483
0.302 1.506518 0.000462
0.304 1.506002 0.000441
0.306 1.505495 0.000421
0.308 1.504999 0.000402
0.310 1.504512 0.000383
0.312 1.504035 0.000365
0.314 1.503568 0.000348
0.316 1.503109 0.000331
0.318 1.502660 0.000314
0.320 1.502219 0.000298
0.322 1.501786 0.000283
0.324 1.501361 0.000268
0.326 1.500945 0.000253
0.328 1.500536 0.000240
0.330 1.500135 0.000226
0.332 1.499742 0.000213
0.334 1.499355 0.000200
0.336 1.498976 0.000188
0.338 1.498603 0.000177
0.340 1.498238 0.000166
0.342 1.497878 0.000155
0.344 1.497525 0.000144
0.346 1.497179 0.000135
0.348 1.496838 0.000125
0.350 1.496504 0.000116
0.352 1.496175 0.000107
0.354 1.495852 0.000099
0.356 1.495534 0.000091
0.358 1.495222 0.000083
0.360 1.494915 0.000076
0.362 1.494613 0.000069
0.364 1.494316 0.000063
0.366 1.494025 0.000057
0.368 1.493738 0.000051
0.370 1.493455 0.000045
0.372 1.493177 0.000040
0.374 1.492904 0.000036
0.376 1.492635 0.000031
0.378 1.492370 0.000027
0.380 1.492110 0.000023
0.382 1.491854 0.000020
0.384 1.491601 0.000016
0.386 1.491353 0.000014
0.388 1.491108 0.000011
0.390 1.490867 0.000009
0.392 1.490629 0.000007
0.394 1.490396 0.000005
0.396 1.490165 0.000003
0.398 1.489938 0.000002
0.400 1.489714 0.000001
0.402 1.489494 0.000001
0.404 1.489276 0.000000
0.406 1.489062 0.000000
0.408 1.488850 0.000000
0.410 1.488641 0.000000
0.412 1.488435 0.000000
0.414 1.488231 0.000000
0.416 1.488031 0.000000
0.418 1.487833 0.000000
0.420 1.487638 0.000000
0.422 1.487446 0.000000
0.424 1.487256 0.000000
0.426 1.487069 0.000000
0.428 1.486884 0.000000
0.430 1.486702 0.000000
0.432 1.486522 0.000000
0.434 1.486345 0.000000
0.436 1.486170 0.000000
0.438 1.485997 0.000000
0.440 1.485827 0.000000
0.442 1.485659 0.000000
0.444 1.485493 0.000000
0.446 1.485329 0.000000
0.448 1.485167 0.000000
0.450 1.485008 0.000000
0.452 1.484851 0.000000
0.454 1.484695 0.000000
0.456 1.484542 0.000000
0.458 1.484390 0.000000
0.460 1.484241 0.000000
0.462 1.484094 0.000000
0.464 1.483948 0.000000
0.466 1.483804 0.000000
0.468 1.483662 0.000000
0.470 1.483522 0.000000
0.472 1.483383 0.000000
0.474 1.483247 0.000000
0.476 1.483111 0.000000
0.478 1.482978 0.000000
0.480 1.482846 0.000000
0.482 1.482716 0.000000
0.484 1.482588 0.000000
0.486 1.482461 0.000000
0.488 1.482335 0.000000
0.490 1.482211 0.000000
0.492 1.482089 0.000000
0.494 1.481968 0.000000
0.496 1.481848 0.000000
0.498 1.481730 0.000000
0.500 1.481613 0.000000
0.502 1.481498 0.000000
0.504 1.481384 0.000000
0.506 1.481271 0.000000
0.508 1.481160 0.000000
0.510 1.481050 0.000000
0.512 1.480941 0.000000
0.514 1.480834 0.000000
0.516 1.480727 0.000000
0.518 1.480622 0.000000
0.520 1.480518 0.000000
0.522 1.480416 0.000000
0.524 1.480314 0.000000
0.526 1.480214 0.000000
0.528 1.480115 0.000000
0.530 1.480016 0.000000
0.532 1.479919 0.000000
0.534 1.479823 0.000000
0.536 1.479729 0.000000
0.538 1.479635 0.000000
0.540 1.479542 0.000000
0.542 1.479450 0.000000
0.544 1.479359 0.000000
0.546 1.479269 0.000000
0.548 1.479181 0.000000
0.550 1.479093 0.000000
0.552 1.479006 0.000000
0.554 1.478920 0.000000
0.556 1.478835 0.000000
0.558 1.478751 0.000000
0.560 1.478667 0.000000
0.562 1.478585 0.000000
0.564 1.478503 0.000000
0.566 1.478423 0.000000
0.568 1.478343 0.000000
0.570 1.478264 0.000000
0.572 1.478186 0.000000
0.574 1.478108 0.000000
0.576 1.478032 0.000000
0.578 1.477956 0.000000
0.580 1.477881 0.000000
0.582 1.477807 0.000000
0.584 1.477733 0.000000
0.586 1.477660 0.000000
0.588 1.477588 0.000000
0.590 1.477517 0.000000
0.592 1.477447 0.000000
0.594 1.477377 0.000000
0.596 1.477308 0.000000
0.598 1.477239 0.000000
0.600 1.477171 0.000000
0.602 1.477104 0.000000
0.604 1.477038 0.000000
0.606 1.476972 0.000000
0.608 1.476907 0.000000
0.610 1.476842 0.000000
0.612 1.476778 0.000000
0.614 1.476715 0.000000
0.616 1.476652 0.000000
0.618 1.476590 0.000000
0.620 1.476529 0.000000
0.622 1.476468 0.000000
0.624 1.476408 0.000000
0.626 1.476348 0.000000
0.628 1.476289 0.000000
0.630 1.476230 0.000000
0.632 1.476172 0.000000
0.634 1.476115 0.000000
0.636 1.476058 0.000000
0.638 1.476001 0.000000
0.640 1.475946 0.000000
0.642 1.475890 0.000000
0.644 1.475835 0.000000
0.646 1.475781 0.000000
0.648 1.475727 0.000000
0.650 1.475674 0.000000
0.652 1.475621 0.000000
0.654 1.475568 0.000000
0.656 1.475517 0.000000
0.658 1.475465 0.000000
0.660 1.475414 0.000000
0.662 1.475364 0.000000
0.664 1.475314 0.000000
0.666 1.475264 0.000000
0.668 1.475215 0.000000
0.670 1.475166 0.000000
0.672 1.475118 0.000000
0.674 1.475070 0.000000
0.676 1.475022 0.000000
0.678 1.474975 0.000000
0.680 1.474929 0.000000
0.682 1.474883 0.000000
0.684 1.474837 0.000000
0.686 1.474791 0.000000
0.688 1.474746 0.000000
0.690 1.474702 0.000000
0.692 1.474657 0.000000
0.694 1.474614 0.000000
0.696 1.474570 0.000000
0.698 1.474527 0.000000
0.700 1.474484 0.000000
0.702 1.474442 0.000000
0.704 1.474400 0.000000
0.706 1.474358 0.000000
0.708 1.474317 0.000000
0.710 1.474276 0.000000
0.712 1.474235 0.000000
0.714 1.474195 0.000000
0.716 1.474155 0.000000
0.718 1.474115 0.000000
0.720 1.474076 0.000000
0.722 1.474037 0.000000
0.724 1.473998 0.000000
0.726 1.473960 0.000000
0.728 1.473922 0.000000
0.730 1.473884 0.000000
0.732 1.473847 0.000000
0.734 1.473810 0.000000
0.736 1.473773 0.000000
0.738 1.473737 0.000000
0.740 1.473700 0.000000
0.742 1.473665 0.000000
0.744 1.473629 0.000000
0.746 1.473594 0.000000
0.748 1.473559 0.000000
0.750 1.473524 0.000000
0.752 1.473489 0.000000
0.754 1.473455 0.000000
0.756 1.473421 0.000000
0.758 1.473387 0.000000
0.760 1.473354 0.000000
0.762 1.473321 0.000000
0.764 1.473288 0.000000
0.766 1.473255 0.000000
0.768 1.473223 0.000000
0.770 1.473191 0.000000
0.772 1.473159 0.000000
0.774 1.473127 0.000000
0.776 1.473096 0.000000
0.778 1.473065 0.000000
0.780 1.473034 0.000000
0.782 1.473003 0.000000
0.784 1.472973 0.000000
0.786 1.472942 0.000000
0.788 1.472912 0.000000
0.790 1.472883 0.000000
0.792 1.472853 0.000000
0.794 1.472824 0.000000
0.796 1.472795 0.000000
0.798 1.472766 0.000000
0.800 1.472737 0.000000
0.802 1.472709 0.000000
0.804 1.472680 0.000000
0.806 1.472652 0.000000
0.808 1.472625 0.000000
0.810 1.472597 0.000000
0.812 1.472570 0.000000
0.814 1.472542 0.000000
0.816 1.472515 0.000000
0.818 1.472489 0.000000
0.820 1.472462 0.000000
0.822 1.472436 0.000000
0.824 1.472409 0.000000
0.826 1.472383 0.000000
0.828 1.472357 0.000000
0.830 1.472332 0.000000
0.832 1.472306 0.000000
0.834 1.472281 0.000000
0.836 1.472256 0.000000
0.838 1.472231 0.000000
0.840 1.472206 0.000000
0.842 1.472182 0.000000
0.844 1.472157 0.000000
0.846 1.472133 0.000000
0.848 1.472109 0.000000
0.850 1.472085 0.000000
0.852 1.472061 0.000000
0.854 1.472038 0.000000
0.856 1.472014 0.000000
0.858 1.471991 0.000000
0.860 1.471968 0.000000
0.862 1.471945 0.000000
0.864 1.471922 0.000000
0.866 1.471900 0.000000
0.868 1.471877 0.000000
0.870 1.471855 0.000000
0.872 1.471833 0.000000
0.874 1.471811 0.000000
0.876 1.471789 0.000000
0.878 1.471767 0.000000
0.880 1.471746 0.000000
0.882 1.471724 0.000000
0.884 1.471703 0.000000
0.886 1.471682 0.000000
0.888 1.471661 0.000000
0.890 1.471640 0.000000
0.892 1.471620 0.000000
0.894 1.471599 0.000000
0.896 1.471579 0.000000
0.898 1.471558 0.000000
0.900 1.471538 0.000000
0.902 1.471518 0.000000
0.904 1.471498 0.000000
0.906 1.471479 0.000000
0.908 1.471459 0.000000
0.910 1.471439 0.000000
0.912 1.471420 0.000000
0.914 1.471401 0.000000
0.916 1.471382 0.000000
0.918 1.471363 0.000000
0.920 1.471344 0.000000
0.922 1.471325 0.000000
0.924 1.471307 0.000000
0.926 1.471288 0.000000
0.928 1.471270 0.000000
0.930 1.471251 0.000000
0.932 1.471233 0.000000
0.934 1.471215 0.000000
0.936 1.471197 0.000000
0.938 1.471180 0.000000
0.940 1.471162 0.000000
0.942 1.471144 0.000000
0.944 1.471127 0.000000
0.946 1.471110 0.000000
0.948 1.471092 0.000000
0.950 1.471075 0.000000
0.952 1.471058 0.000000
0.954 1.471041 0.000000
0.956 1.471025 0.000000
0.958 1.471008 0.000000
0.960 1.470991 0.000000
0.962 1.470975 0.000000
0.964 1.470958 0.000000
0.966 1.470942 0.000000
0.968 1.470926 0.000000
0.970 1.470910 0.000000
0.972 1.470894 0.000000
0.974 1.470878 0.000000
0.976 1.470862 0.000000
0.978 1.470846 0.000000
0.980 1.470831 0.000000
0.982 1.470815 0.000000
0.984 1.470800 0.000000
0.986 1.470785 0.000000
0.988 1.470769 0.000000
0.990 1.470754 0.000000
0.992 1.470739 0.000000
0.994 1.470724 0.000000
0.996 1.470709 0.000000
0.998 1.470695 0.000000
1.000 1.470680 0.000000
1.002 1.470665 0.000000
1.004 1.470651 0.000000
1.006 1.470636 0.000000
1.008 1.470622 0.000000
1.010 1.470608 0.000000
1.012 1.470594 0.000000
1.014 1.470580 0.000000
1.016 1.470566 0.000000
1.018 1.470552 0.000000
1.020 1.470538 0.000000
1.022 1.470524 0.000000
1.024 1.470510 0.000000
1.026 1.470497 0.000000
1.028 1.470483 0.000000
1.030 1.470470 0.000000
1.032 1.470456 0.000000
1.034 1.470443 0.000000
1.036 1.470430 0.000000
1.038 1.470417 0.000000
1.040 1.470404 0.000000
1.042 1.470391 0.000000
1.044 1.470378 0.000000
1.046 1.470365 0.000000
1.048 1.470352 0.000000
1.050 1.470340 0.000000
1.052 1.470327 0.000000
1.054 1.470314 0.000000
1.056 1.470302 0.000000
1.058 1.470290 0.000000
1.060 1.470277 0.000000
1.062 1.470265 0.000000
1.064 1.470253 0.000000
1.066 1.470241 0.000000
1.068 1.470229 0.000000
1.070 1.470217 0.000000
1.072 1.470205 0.000000
1.074 1.470193 0.000000
1.076 1.470181 0.000000
1.078 1.470169 0.000000
1.080 1.470158 0.000000
1.082 1.470146 0.000000
1.084 1.470135 0.000000
1.086 1.470123 0.000000
1.088 1.470112 0.000000
1.090 1.470100 0.000000
1.092 1.470089 0.000000
1.094 1.470078 0.000000
1.096 1.470067 0.000000
1.098 1.470056 0.000000
1.100 1.470045 0.000000
1.102 1.470034 0.000000
1.104 1.470023 0.000000
1.106 1.470012 0.000000
1.108 1.470001 0.000000
1.110 1.469990 0.000000
1.112 1.469980 0.000000
1.114 1.469969 0.000000
1.116 1.469958 0.000000
1.118 1.469948 0.000000
1.120 1.469937 0.000000
1.122 1.469927 0.000000
1.124 1.469917 0.000000
1.126 1.469906 0.000000
1.128 1.469896 0.000000
1.130 1.469886 0.000000
1.132 1.469876 0.000000
1.134 1.469866 0.000000
1.136 1.469856 0.000000
1.138 1.469846 0.000000
1.140 1.469836 0.000000
1.142 1.469826 0.000000
1.144 1.469816 0.000000
1.146 1.469807 0.000000
1.148 1.469797 0.000000
1.150 1.469787 0.000000
1.152 1.469778 0.000000
1.154 1.469768 0.000000
1.156 1.469758 0.000000
1.158 1.469749 0.000000
1.160 1.469740 0.000000
1.162 1.469730 0.000000
1.164 1.469721 0.000000
1.166 1.469712 0.000000
1.168 1.469702 0.000000
1.170 1.469693 0.000000
1.172 1.469684 0.000000
1.174 1.469675 0.000000
1.176 1.469666 0.000000
1.178 1.469657 0.000000
1.180 1.469648 0.000000
1.182 1.469639 0.000000
1.184 1.469630 0.000000
1.186 1.469622 0.000000
1.188 1.469613 0.000000
1.190 1.469604 0.000000
1.192 1.469595 0.000000
1.194 1.469587 0.000000
1.196 1.469578 0.000000
1.198 1.469570 0.000000
1.200 1.469561 0.000000
1.202 1.469553 0.000000
1.204 1.469544 0.000000
1.206 1.469536 0.000000
1.208 1.469528 0.000000
1.210 1.469519 0.000000
1.212 1.469511 0.000000
1.214 1.469503 0.000000
1.216 1.469495 0.000000
1.218 1.469487 0.000000
1.220 1.469478 0.000000
1.222 1.469470 0.000000
1.224 1.469462 0.000000
1.226 1.469454 0.000000
1.228 1.469447 0.000000
1.230 1.469439 0.000000
1.232 1.469431 0.000000
1.234 1.469423 0.000000
1.236 1.469415 0.000000
1.238 1.469407 0.000000
1.240 1.469400 0.000000
1.242 1.469392 0.000000
1.244 1.469384 0.000000
1.246 1.469377 0.000000
1.248 1.469369 0.000000
1.250 1.469362 0.000000
"""

# database/data/main/Ta2O5/nk/Gao.yml (sha256 269efa1797dc91c4...): 726 rows, wavelength (um), n, kappa as printed there
TA2O5_FILM_GAO_NK = """
0.350 2.317048 0.000655
0.352 2.313395 0.000637
0.354 2.309832 0.000619
0.356 2.306355 0.000602
0.358 2.302962 0.000585
0.360 2.299649 0.000569
0.362 2.296414 0.000553
0.364 2.293255 0.000538
0.366 2.290169 0.000523
0.368 2.287153 0.000509
0.370 2.284205 0.000495
0.372 2.281324 0.000482
0.374 2.278507 0.000468
0.376 2.275751 0.000456
0.378 2.273056 0.000443
0.380 2.270419 0.000431
0.382 2.267838 0.000419
0.384 2.265313 0.000408
0.386 2.262840 0.000397
0.388 2.260419 0.000386
0.390 2.258048 0.000376
0.392 2.255726 0.000365
0.394 2.253451 0.000355
0.396 2.251222 0.000346
0.398 2.249037 0.000336
0.400 2.246896 0.000327
0.402 2.244797 0.000318
0.404 2.242739 0.000309
0.406 2.240720 0.000301
0.408 2.238741 0.000292
0.410 2.236799 0.000284
0.412 2.234894 0.000276
0.414 2.233025 0.000269
0.416 2.231190 0.000261
0.418 2.229390 0.000254
0.420 2.227622 0.000247
0.422 2.225887 0.000240
0.424 2.224183 0.000233
0.426 2.222510 0.000226
0.428 2.220867 0.000220
0.430 2.219252 0.000214
0.432 2.217666 0.000207
0.434 2.216108 0.000201
0.436 2.214577 0.000196
0.438 2.213072 0.000190
0.440 2.211593 0.000184
0.442 2.210139 0.000179
0.444 2.208709 0.000173
0.446 2.207304 0.000168
0.448 2.205921 0.000163
0.450 2.204562 0.000158
0.452 2.203225 0.000153
0.454 2.201910 0.000149
0.456 2.200616 0.000144
0.458 2.199343 0.000140
0.460 2.198091 0.000135
0.462 2.196858 0.000131
0.464 2.195645 0.000127
0.466 2.194451 0.000123
0.468 2.193275 0.000119
0.470 2.192118 0.000115
0.472 2.190979 0.000111
0.474 2.189857 0.000108
0.476 2.188752 0.000104
0.478 2.187664 0.000100
0.480 2.186592 0.000100
0.482 2.185537 0.000094
0.484 2.184497 0.000090
0.486 2.183473 0.000087
0.488 2.182463 0.000084
0.490 2.181469 0.000081
0.492 2.180489 0.000078
0.494 2.179523 0.000075
0.496 2.178571 0.000073
0.498 2.177633 0.000070
0.500 2.176708 0.000067
0.502 2.175796 0.000065
0.504 2.174897 0.000062
0.506 2.174010 0.000060
0.508 2.173136 0.000057
0.510 2.172274 0.000055
0.512 2.171424 0.000053
0.514 2.170586 0.000051
0.516 2.169759 0.000048
0.518 2.168943 0.000046
0.520 2.168138 0.000044
0.522 2.167345 0.000042
0.524 2.166561 0.000041
0.526 2.165788 0.000039
0.528 2.165026 0.000037
0.530 2.164273 0.000035
0.532 2.163530 0.000033
0.534 2.162797 0.000032
0.536 2.162074 0.000030
0.538 2.161360 0.000029
0.540 2.160655 0.000027
0.542 2.159959 0.000026
0.544 2.159272 0.000024
0.546 2.158593 0.000023
0.548 2.157923 0.000022
0.550 2.157262 0.000021
0.552 2.156609 0.000019
0.554 2.155964 0.000018
0.556 2.155327 0.000017
0.558 2.154697 0.000016
0.560 2.154076 0.000015
0.562 2.153462 0.000014
0.564 2.152856 0.000013
0.566 2.152256 0.000012
0.568 2.151665 0.000011
0.570 2.151080 0.000010
0.572 2.150502 0.000009
0.574 2.149931 0.000009
0.576 2.149367 0.000008
0.578 2.148809 0.000007
0.580 2.148258 0.000007
0.582 2.147714 0.000006
0.584 2.147175 0.000005
0.586 2.146643 0.000005
0.588 2.146118 0.000004
0.590 2.145598 0.000004
0.592 2.145084 0.000003
0.594 2.144576 0.000003
0.596 2.144074 0.000003
0.598 2.143577 0.000002
0.600 2.143086 0.000002
0.602 2.142601 0.000001
0.604 2.142121 0.000001
0.606 2.141646 0.000001
0.608 2.141177 0.000001
0.610 2.140712 0.000001
0.612 2.140253 0
0.614 2.139799 0
0.616 2.139350 0
0.618 2.138906 0
0.620 2.138466 0
0.622 2.138032 0
0.624 2.137602 0
0.626 2.137176 0
0.628 2.136755 0
0.630 2.136339 0
0.632 2.135927 0
0.634 2.135520 0
0.636 2.135116 0
0.638 2.134717 0
0.640 2.134322 0
0.642 2.133931 0
0.644 2.133545 0
0.646 2.133162 0
0.648 2.132783 0
0.650 2.132408 0
0.652 2.132037 0
0.654 2.131669 0
0.656 2.131306 0
0.658 2.130946 0
0.660 2.130589 0
0.662 2.130236 0
0.664 2.129887 0
0.666 2.129541 0
0.668 2.129199 0
0.670 2.128860 0
0.672 2.128524 0
0.674 2.128191 0
0.676 2.127862 0
0.678 2.127536 0
0.680 2.127213 0
0.682 2.126893 0
0.684 2.126577 0
0.686 2.126263 0
0.688 2.125952 0
0.690 2.125645 0
0.692 2.125340 0
0.694 2.125038 0
0.696 2.124739 0
0.698 2.124443 0
0.700 2.124149 0
0.702 2.123858 0
0.704 2.123570 0
0.706 2.123285 0
0.708 2.123002 0
0.710 2.122722 0
0.712 2.122444 0
0.714 2.122169 0
0.716 2.121897 0
0.718 2.121626 0
0.720 2.121359 0
0.722 2.121093 0
0.724 2.120831 0
0.726 2.120570 0
0.728 2.120312 0
0.730 2.120056 0
0.732 2.119802 0
0.734 2.119551 0
0.736 2.119302 0
0.738 2.119055 0
0.740 2.118810 0
0.742 2.118567 0
0.744 2.118327 0
0.746 2.118088 0
0.748 2.117852 0
0.750 2.117617 0
0.752 2.117385 0
0.754 2.117155 0
0.756 2.116926 0
0.758 2.116700 0
0.760 2.116475 0
0.762 2.116253 0
0.764 2.116032 0
0.766 2.115813 0
0.768 2.115596 0
0.770 2.115381 0
0.772 2.115167 0
0.774 2.114955 0
0.776 2.114746 0
0.778 2.114537 0
0.780 2.114331 0
0.782 2.114126 0
0.784 2.113923 0
0.786 2.113722 0
0.788 2.113522 0
0.790 2.113324 0
0.792 2.113127 0
0.794 2.112932 0
0.796 2.112739 0
0.798 2.112547 0
0.800 2.112356 0
0.802 2.112168 0
0.804 2.111980 0
0.806 2.111794 0
0.808 2.111610 0
0.810 2.111427 0
0.812 2.111246 0
0.814 2.111066 0
0.816 2.110887 0
0.818 2.110710 0
0.820 2.110534 0
0.822 2.110359 0
0.824 2.110186 0
0.826 2.110015 0
0.828 2.109844 0
0.830 2.109675 0
0.832 2.109507 0
0.834 2.109340 0
0.836 2.109175 0
0.838 2.109011 0
0.840 2.108848 0
0.842 2.108687 0
0.844 2.108526 0
0.846 2.108367 0
0.848 2.108209 0
0.850 2.108052 0
0.852 2.107897 0
0.854 2.107742 0
0.856 2.107589 0
0.858 2.107437 0
0.860 2.107286 0
0.862 2.107136 0
0.864 2.106987 0
0.866 2.106839 0
0.868 2.106692 0
0.870 2.106547 0
0.872 2.106402 0
0.874 2.106259 0
0.876 2.106116 0
0.878 2.105975 0
0.880 2.105834 0
0.882 2.105695 0
0.884 2.105557 0
0.886 2.105419 0
0.888 2.105283 0
0.890 2.105147 0
0.892 2.105013 0
0.894 2.104879 0
0.896 2.104747 0
0.898 2.104615 0
0.900 2.104484 0
0.902 2.104354 0
0.904 2.104225 0
0.906 2.104097 0
0.908 2.103970 0
0.910 2.103844 0
0.912 2.103718 0
0.914 2.103594 0
0.916 2.103470 0
0.918 2.103347 0
0.920 2.103225 0
0.922 2.103104 0
0.924 2.102984 0
0.926 2.102864 0
0.928 2.102746 0
0.930 2.102628 0
0.932 2.102511 0
0.934 2.102394 0
0.936 2.102279 0
0.938 2.102164 0
0.940 2.102050 0
0.942 2.101937 0
0.944 2.101824 0
0.946 2.101713 0
0.948 2.101602 0
0.950 2.101491 0
0.952 2.101382 0
0.954 2.101273 0
0.956 2.101165 0
0.958 2.101057 0
0.960 2.100951 0
0.962 2.100845 0
0.964 2.100739 0
0.966 2.100635 0
0.968 2.100531 0
0.970 2.100428 0
0.972 2.100325 0
0.974 2.100223 0
0.976 2.100122 0
0.978 2.100021 0
0.980 2.099921 0
0.982 2.099822 0
0.984 2.099723 0
0.986 2.099625 0
0.988 2.099528 0
0.990 2.099431 0
0.992 2.099334 0
0.994 2.099239 0
0.996 2.099144 0
0.998 2.099049 0
1.000 2.098955 0
1.002 2.098862 0
1.004 2.098769 0
1.006 2.098677 0
1.008 2.098586 0
1.010 2.098495 0
1.012 2.098404 0
1.014 2.098315 0
1.016 2.098225 0
1.018 2.098136 0
1.020 2.098048 0
1.022 2.097961 0
1.024 2.097873 0
1.026 2.097787 0
1.028 2.097701 0
1.030 2.097615 0
1.032 2.097530 0
1.034 2.097446 0
1.036 2.097362 0
1.038 2.097278 0
1.040 2.097195 0
1.042 2.097112 0
1.044 2.097030 0
1.046 2.096949 0
1.048 2.096868 0
1.050 2.096787 0
1.052 2.096707 0
1.054 2.096627 0
1.056 2.096548 0
1.058 2.096470 0
1.060 2.096391 0
1.062 2.096314 0
1.064 2.096236 0
1.066 2.096159 0
1.068 2.096083 0
1.070 2.096007 0
1.072 2.095931 0
1.074 2.095856 0
1.076 2.095782 0
1.078 2.095707 0
1.080 2.095634 0
1.082 2.095560 0
1.084 2.095487 0
1.086 2.095415 0
1.088 2.095343 0
1.090 2.095271 0
1.092 2.095200 0
1.094 2.095129 0
1.096 2.095058 0
1.098 2.094988 0
1.100 2.094918 0
1.102 2.094849 0
1.104 2.094780 0
1.106 2.094712 0
1.108 2.094643 0
1.110 2.094576 0
1.112 2.094508 0
1.114 2.094441 0
1.116 2.094375 0
1.118 2.094308 0
1.120 2.094242 0
1.122 2.094177 0
1.124 2.094112 0
1.126 2.094047 0
1.128 2.093982 0
1.130 2.093918 0
1.132 2.093854 0
1.134 2.093791 0
1.136 2.093728 0
1.138 2.093665 0
1.140 2.093603 0
1.142 2.093541 0
1.144 2.093479 0
1.146 2.093418 0
1.148 2.093356 0
1.150 2.093296 0
1.152 2.093235 0
1.154 2.093175 0
1.156 2.093116 0
1.158 2.093056 0
1.160 2.092997 0
1.162 2.092938 0
1.164 2.092880 0
1.166 2.092821 0
1.168 2.092764 0
1.170 2.092706 0
1.172 2.092649 0
1.174 2.092592 0
1.176 2.092535 0
1.178 2.092479 0
1.180 2.092423 0
1.182 2.092367 0
1.184 2.092311 0
1.186 2.092256 0
1.188 2.092201 0
1.190 2.092147 0
1.192 2.092092 0
1.194 2.092038 0
1.196 2.091984 0
1.198 2.091931 0
1.200 2.091878 0
1.202 2.091825 0
1.204 2.091772 0
1.206 2.091720 0
1.208 2.091668 0
1.210 2.091616 0
1.212 2.091564 0
1.214 2.091513 0
1.216 2.091462 0
1.218 2.091411 0
1.220 2.091360 0
1.222 2.091310 0
1.224 2.091260 0
1.226 2.091210 0
1.228 2.091160 0
1.230 2.091111 0
1.232 2.091062 0
1.234 2.091013 0
1.236 2.090964 0
1.238 2.090916 0
1.240 2.090868 0
1.242 2.090820 0
1.244 2.090773 0
1.246 2.090725 0
1.248 2.090678 0
1.250 2.090631 0
1.252 2.090584 0
1.254 2.090538 0
1.256 2.090492 0
1.258 2.090446 0
1.260 2.090400 0
1.262 2.090354 0
1.264 2.090309 0
1.266 2.090264 0
1.268 2.090219 0
1.270 2.090174 0
1.272 2.090130 0
1.274 2.090085 0
1.276 2.090041 0
1.278 2.089998 0
1.280 2.089954 0
1.282 2.089911 0
1.284 2.089867 0
1.286 2.089824 0
1.288 2.089782 0
1.290 2.089739 0
1.292 2.089697 0
1.294 2.089654 0
1.296 2.089612 0
1.298 2.089571 0
1.300 2.089529 0
1.302 2.089488 0
1.304 2.089446 0
1.306 2.089405 0
1.308 2.089365 0
1.310 2.089324 0
1.312 2.089284 0
1.314 2.089243 0
1.316 2.089203 0
1.318 2.089163 0
1.320 2.089124 0
1.322 2.089084 0
1.324 2.089045 0
1.326 2.089006 0
1.328 2.088967 0
1.330 2.088928 0
1.332 2.088890 0
1.334 2.088851 0
1.336 2.088813 0
1.338 2.088775 0
1.340 2.088737 0
1.342 2.088699 0
1.344 2.088662 0
1.346 2.088624 0
1.348 2.088587 0
1.350 2.088550 0
1.352 2.088513 0
1.354 2.088477 0
1.356 2.088440 0
1.358 2.088404 0
1.360 2.088367 0
1.362 2.088331 0
1.364 2.088295 0
1.366 2.088260 0
1.368 2.088224 0
1.370 2.088189 0
1.372 2.088154 0
1.374 2.088119 0
1.376 2.088084 0
1.378 2.088049 0
1.380 2.088014 0
1.382 2.087980 0
1.384 2.087945 0
1.386 2.087911 0
1.388 2.087877 0
1.390 2.087843 0
1.392 2.087810 0
1.394 2.087776 0
1.396 2.087743 0
1.398 2.087709 0
1.400 2.087676 0
1.402 2.087643 0
1.404 2.087611 0
1.406 2.087578 0
1.408 2.087545 0
1.410 2.087513 0
1.412 2.087481 0
1.414 2.087449 0
1.416 2.087417 0
1.418 2.087385 0
1.420 2.087353 0
1.422 2.087321 0
1.424 2.087290 0
1.426 2.087259 0
1.428 2.087227 0
1.430 2.087196 0
1.432 2.087166 0
1.434 2.087135 0
1.436 2.087104 0
1.438 2.087074 0
1.440 2.087043 0
1.442 2.087013 0
1.444 2.086983 0
1.446 2.086953 0
1.448 2.086923 0
1.450 2.086893 0
1.452 2.086864 0
1.454 2.086834 0
1.456 2.086805 0
1.458 2.086776 0
1.460 2.086746 0
1.462 2.086717 0
1.464 2.086689 0
1.466 2.086660 0
1.468 2.086631 0
1.470 2.086603 0
1.472 2.086574 0
1.474 2.086546 0
1.476 2.086518 0
1.478 2.086490 0
1.480 2.086462 0
1.482 2.086434 0
1.484 2.086406 0
1.486 2.086379 0
1.488 2.086351 0
1.490 2.086324 0
1.492 2.086297 0
1.494 2.086269 0
1.496 2.086242 0
1.498 2.086215 0
1.500 2.086189 0
1.502 2.086162 0
1.504 2.086135 0
1.506 2.086109 0
1.508 2.086082 0
1.510 2.086056 0
1.512 2.086030 0
1.514 2.086004 0
1.516 2.085978 0
1.518 2.085952 0
1.520 2.085926 0
1.522 2.085901 0
1.524 2.085875 0
1.526 2.085850 0
1.528 2.085824 0
1.530 2.085799 0
1.532 2.085774 0
1.534 2.085749 0
1.536 2.085724 0
1.538 2.085699 0
1.540 2.085674 0
1.542 2.085650 0
1.544 2.085625 0
1.546 2.085601 0
1.548 2.085577 0
1.550 2.085552 0
1.552 2.085528 0
1.554 2.085504 0
1.556 2.085480 0
1.558 2.085456 0
1.560 2.085432 0
1.562 2.085409 0
1.564 2.085385 0
1.566 2.085362 0
1.568 2.085338 0
1.570 2.085315 0
1.572 2.085292 0
1.574 2.085268 0
1.576 2.085245 0
1.578 2.085222 0
1.580 2.085200 0
1.582 2.085177 0
1.584 2.085154 0
1.586 2.085131 0
1.588 2.085109 0
1.590 2.085087 0
1.592 2.085064 0
1.594 2.085042 0
1.596 2.085020 0
1.598 2.084998 0
1.600 2.084976 0
1.602 2.084954 0
1.604 2.084932 0
1.606 2.084910 0
1.608 2.084888 0
1.610 2.084867 0
1.612 2.084845 0
1.614 2.084824 0
1.616 2.084802 0
1.618 2.084781 0
1.620 2.084760 0
1.622 2.084739 0
1.624 2.084718 0
1.626 2.084697 0
1.628 2.084676 0
1.630 2.084655 0
1.632 2.084634 0
1.634 2.084614 0
1.636 2.084593 0
1.638 2.084573 0
1.640 2.084552 0
1.642 2.084532 0
1.644 2.084512 0
1.646 2.084492 0
1.648 2.084471 0
1.650 2.084451 0
1.652 2.084431 0
1.654 2.084412 0
1.656 2.084392 0
1.658 2.084372 0
1.660 2.084352 0
1.662 2.084333 0
1.664 2.084313 0
1.666 2.084294 0
1.668 2.084274 0
1.670 2.084255 0
1.672 2.084236 0
1.674 2.084217 0
1.676 2.084197 0
1.678 2.084178 0
1.680 2.084159 0
1.682 2.084140 0
1.684 2.084122 0
1.686 2.084103 0
1.688 2.084084 0
1.690 2.084066 0
1.692 2.084047 0
1.694 2.084028 0
1.696 2.084010 0
1.698 2.083992 0
1.700 2.083973 0
1.702 2.083955 0
1.704 2.083937 0
1.706 2.083919 0
1.708 2.083901 0
1.710 2.083883 0
1.712 2.083865 0
1.714 2.083847 0
1.716 2.083829 0
1.718 2.083812 0
1.720 2.083794 0
1.722 2.083776 0
1.724 2.083759 0
1.726 2.083741 0
1.728 2.083724 0
1.730 2.083707 0
1.732 2.083689 0
1.734 2.083672 0
1.736 2.083655 0
1.738 2.083638 0
1.740 2.083621 0
1.742 2.083604 0
1.744 2.083587 0
1.746 2.083570 0
1.748 2.083553 0
1.750 2.083536 0
1.752 2.083520 0
1.754 2.083503 0
1.756 2.083486 0
1.758 2.083470 0
1.760 2.083453 0
1.762 2.083437 0
1.764 2.083421 0
1.766 2.083404 0
1.768 2.083388 0
1.770 2.083372 0
1.772 2.083356 0
1.774 2.083340 0
1.776 2.083324 0
1.778 2.083308 0
1.780 2.083292 0
1.782 2.083276 0
1.784 2.083260 0
1.786 2.083244 0
1.788 2.083229 0
1.790 2.083213 0
1.792 2.083198 0
1.794 2.083182 0
1.796 2.083167 0
1.798 2.083151 0
1.800 2.083136 0
"""

# database/data/main/Au/nk/Johnson.yml (sha256 9f4bdab6bd49f7c6...): 49 rows, wavelength (um), n, kappa as printed there
AU_JOHNSON_CHRISTY_NK = """
0.1879 1.28 1.188
0.1916 1.32 1.203
0.1953 1.34 1.226
0.1993 1.33 1.251
0.2033 1.33 1.277
0.2073 1.30 1.304
0.2119 1.30 1.350
0.2164 1.30 1.387
0.2214 1.30 1.427
0.2262 1.31 1.460
0.2313 1.30 1.497
0.2371 1.32 1.536
0.2426 1.32 1.577
0.2490 1.33 1.631
0.2551 1.33 1.688
0.2616 1.35 1.749
0.2689 1.38 1.803
0.2761 1.43 1.847
0.2844 1.47 1.869
0.2924 1.49 1.878
0.3009 1.53 1.889
0.3107 1.53 1.893
0.3204 1.54 1.898
0.3315 1.48 1.883
0.3425 1.48 1.871
0.3542 1.50 1.866
0.3679 1.48 1.895
0.3815 1.46 1.933
0.3974 1.47 1.952
0.4133 1.46 1.958
0.4305 1.45 1.948
0.4509 1.38 1.914
0.4714 1.31 1.849
0.4959 1.04 1.833
0.5209 0.62 2.081
0.5486 0.43 2.455
0.5821 0.29 2.863
0.6168 0.21 3.272
0.6595 0.14 3.697
0.7045 0.13 4.103
0.7560 0.14 4.542
0.8211 0.16 5.083
0.8920 0.17 5.663
0.9840 0.22 6.350
1.0880 0.27 7.150
1.2160 0.35 8.145
1.3930 0.43 9.519
1.6100 0.56 11.21
1.9370 0.92 13.78
"""

# database/data/main/Ag/nk/Johnson.yml (sha256 8c79d5e2529e4d3a...): 49 rows, wavelength (um), n, kappa as printed there
AG_JOHNSON_CHRISTY_NK = """
0.1879 1.07 1.212
0.1916 1.10 1.232
0.1953 1.12 1.255
0.1993 1.14 1.277
0.2033 1.15 1.296
0.2073 1.18 1.312
0.2119 1.20 1.325
0.2164 1.22 1.336
0.2214 1.25 1.342
0.2262 1.26 1.344
0.2313 1.28 1.357
0.2371 1.28 1.367
0.2426 1.30 1.378
0.2490 1.31 1.389
0.2551 1.33 1.393
0.2616 1.35 1.387
0.2689 1.38 1.372
0.2761 1.41 1.331
0.2844 1.41 1.264
0.2924 1.39 1.161
0.3009 1.34 0.964
0.3107 1.13 0.616
0.3204 0.81 0.392
0.3315 0.17 0.829
0.3425 0.14 1.142
0.3542 0.10 1.419
0.3679 0.07 1.657
0.3815 0.05 1.864
0.3974 0.05 2.070
0.4133 0.05 2.275
0.4305 0.04 2.462
0.4509 0.04 2.657
0.4714 0.05 2.869
0.4959 0.05 3.093
0.5209 0.05 3.324
0.5486 0.06 3.586
0.5821 0.05 3.858
0.6168 0.06 4.152
0.6595 0.05 4.483
0.7045 0.04 4.838
0.7560 0.03 5.242
0.8211 0.04 5.727
0.8920 0.04 6.312
0.9840 0.04 6.992
1.0880 0.04 7.795
1.2160 0.09 8.828
1.3930 0.13 10.10
1.6100 0.15 11.85
1.9370 0.24 14.08
"""

# database/data/main/Al/nk/Rakic.yml (sha256 e93b31fe82155183...): 206 rows, wavelength (um), n, kappa as printed there
AL_RAKIC_NK = """
1.2399E-04 9.999946E-01 8.2410E-08
1.3051E-04 9.99994E-01 1.2720E-07
1.3776E-04 9.99993E-01 1.2488E-07
1.5498E-04 9.99991E-01 1.9173E-07
1.7712E-04 9.99989E-01 3.1463E-07
2.0664E-04 9.99984E-01 5.5102E-07
2.4797E-04 9.9998E-01 1.0726E-06
3.0996E-04 9.9997E-01 2.4843E-06
3.5424E-04 9.9995E-01 4.0484E-06
4.1328E-04 9.9994E-01 7.1408E-06
4.9594E-04 9.9991E-01 1.3642E-05
6.1993E-04 9.9987E-01 3.2079E-05
6.5255E-04 9.9986E-01 3.8497E-05
6.8881E-04 9.9985E-01 4.7138E-05
7.2932E-04 9.9984E-01 5.7974E-05
7.4021E-04 9.9984E-01 6.1633E-05
7.7734E-04 9.9986E-01 7.4862E-05
7.8472E-04 9.9987E-01 7.8480E-05
7.9274E-04 9.9990E-01 8.5418E-05
7.9376E-04 9.9992E-01 7.1847E-05
7.9478E-04 9.9993E-01 4.9998E-05
7.9529E-04 9.9992E-01 4.1131E-05
7.9580E-04 9.9992E-01 3.2911E-05
7.9785E-04 9.9991E-01 2.3687E-05
7.9887E-04 9.9991E-01 1.1026E-05
7.9990E-04 9.9989E-01 6.0484E-06
8.0510E-04 9.9987E-01 6.1901E-06
8.1569E-04 9.9985E-01 6.4818E-06
8.2657E-04 9.9983E-01 6.8049E-06
8.5507E-04 9.9981E-01 7.8422E-06
8.8561E-04 9.9979E-01 8.9400E-06
9.5373E-04 9.9974E-01 1.1636E-05
1.0332E-03 9.9968E-01 1.5628E-05
1.1271E-03 9.9961E-01 2.1586E-05
1.2399E-03 9.9953E-01 3.1115E-05
1.3776E-03 9.9940E-01 4.6771E-05
1.5498E-03 9.9924E-01 7.2992E-05
1.7712E-03 9.9898E-01 1.1811E-04
2.0664E-03 9.9860E-01 2.2001E-04
2.4797E-03 9.9797E-01 4.3503E-04
3.0996E-03 9.9694E-01 9.6887E-04
4.1328E-03 9.9480E-01 2.3492E-03
4.9594E-03 9.9313E-01 4.1863E-03
6.1993E-03 9.9111E-01 7.5099E-03
6.5255E-03 9.9054E-01 8.4716E-03
6.8881E-03 9.9007E-01 9.6517E-03
7.2932E-03 9.8909E-01 1.0987E-02
7.7491E-03 9.8912E-01 1.3728E-02
8.2657E-03 9.8966E-01 1.4773E-02
8.5507E-03 9.8934E-01 1.5437E-02
8.8561E-03 9.8883E-01 1.6304E-02
9.1841E-03 9.8793E-01 1.7765E-02
9.5373E-03 9.8761E-01 2.0606E-02
9.9188E-03 9.8941E-01 2.3421E-02
1.0332E-02 9.9139E-01 2.4063E-02
1.0781E-02 9.9233E-01 2.4928E-02
1.1271E-02 9.9415E-01 2.5452E-02
1.1808E-02 9.9285E-01 2.4415E-02
1.2399E-02 9.9123E-01 2.9920E-02
1.2652E-02 9.9265E-01 3.3061E-02
1.2915E-02 9.9652E-01 3.5883E-02
1.3190E-02 1.0012E+00 3.5311E-02
1.3477E-02 1.0041E+00 3.3392E-02
1.3776E-02 1.0058E+00 3.0918E-02
1.4089E-02 1.0060E+00 2.8956E-02
1.4417E-02 1.0065E+00 2.8232E-02
1.4760E-02 1.0074E+00 2.6826E-02
1.5120E-02 1.0077E+00 2.5460E-02
1.5498E-02 1.0075E+00 2.4476E-02
1.5694E-02 1.0075E+00 2.4501E-02
1.5896E-02 1.0078E+00 2.4757E-02
1.6102E-02 1.0095E+00 2.5180E-02
1.6314E-02 1.0106E+00 2.3853E-02
1.6422E-02 1.0110E+00 2.3955E-02
1.6531E-02 1.0118E+00 2.4020E-02
1.6642E-02 1.0132E+00 2.4343E-02
1.6755E-02 1.0151E+00 2.4184E-02
1.6777E-02 1.0156E+00 2.4228E-02
1.6800E-02 1.0161E+00 2.4282E-02
1.6823E-02 1.0167E+00 2.4375E-02
1.6846E-02 1.0173E+00 2.4499E-02
1.6869E-02 1.0181E+00 2.4831E-02
1.6892E-02 1.0194E+00 2.5432E-02
1.6915E-02 1.0219E+00 2.6018E-02
1.6938E-02 1.0259E+00 2.4227E-02
1.6961E-02 1.0262E+00 1.9564E-02
1.6984E-02 1.0246E+00 1.9145E-02
1.7008E-02 1.0255E+00 2.0012E-02
1.7031E-02 1.0305E+00 2.0072E-02
1.7054E-02 1.0349E+00 1.2476E-02
1.7078E-02 1.0305E+00 4.1164E-03
1.7101E-02 1.0249E+00 3.6218E-03
1.7125E-02 1.0226E+00 3.4141E-03
1.7149E-02 1.0206E+00 3.4400E-03
1.7172E-02 1.0192E+00 3.4767E-03
1.7196E-02 1.0179E+00 3.4877E-03
1.7208E-02 1.0174E+00 3.5108E-03
1.7220E-02 1.0169E+00 3.5249E-03
1.7463E-02 1.0108E+00 3.4957E-03
1.7712E-02 1.0070E+00 3.5425E-03
1.8233E-02 1.0019E+00 3.6730E-03
1.8786E-02 9.9791E-01 3.8926E-03
1.9373E-02 9.9457E-01 4.1092E-03
1.9998E-02 9.9143E-01 4.2397E-03
2.0664E-02 9.8827E-01 4.3696E-03
2.2543E-02 9.7998E-01 5.0004E-03
2.4797E-02 9.7048E-01 5.7469E-03
2.7552E-02 9.5834E-01 6.6191E-03
3.0996E-02 9.4189E-01 7.8466E-03
3.5424E-02 9.1802E-01 9.3121E-03
4.1328E-02 8.8013E-01 1.1651E-02
4.9594E-02 8.1512E-01 1.5894E-02
6.1993E-02 6.7912E-01 2.2340E-02
6.5255E-02 6.3242E-01 2.4770E-02
6.8881E-02 5.7251E-01 2.7681E-02
7.2932E-02 4.9131E-01 3.2409E-02
7.7491E-02 3.7197E-01 4.4202E-02
7.8472E-02 3.4031E-01 4.8320E-02
7.9478E-02 3.0373E-01 5.3349E-02
7.9990E-02 2.8271E-01 5.6697E-02
8.0510E-02 2.5936E-01 6.1407E-02
8.1036E-02 2.3344E-01 6.8348E-02
8.1569E-02 2.0569E-01 7.9959E-02
8.2109E-02 1.7943E-01 9.4223E-02
8.2657E-02 1.5065E-01 1.1041E-01
8.3774E-02 9.4517E-02 1.6589E-01
8.4921E-02 6.7041E-02 2.3420E-01
8.6101E-02 5.4863E-02 2.9293E-01
8.8561E-02 4.4168E-02 3.9115E-01
9.5373E-02 3.6437E-02 5.9086E-01
1.0332E-01 3.5753E-02 7.7163E-01
1.1271E-01 3.8468E-02 9.5677E-01
1.2399E-01 4.6304E-02 1.1555E+00
1.3776E-01 5.7167E-02 1.3775E+00
1.5498E-01 7.2505E-02 1.6366E+00
1.7712E-01 9.4236E-02 1.9519E+00
2.0664E-01 1.2677E-01 2.3563E+00
2.4797E-01 1.8137E-01 2.9029E+00
3.0996E-01 2.8003E-01 3.7081E+00
3.2628E-01 3.1474E-01 3.9165E+00
3.6466E-01 3.9877E-01 4.3957E+00
4.1328E-01 5.2135E-01 5.0008E+00
4.4280E-01 6.0790E-01 5.3676E+00
4.7687E-01 7.2780E-01 5.7781E+00
5.1660E-01 8.7340E-01 6.2418E+00
5.6357E-01 1.0728E+00 6.7839E+00
6.1993E-01 1.3660E+00 7.4052E+00
6.5225E-01 1.5724E+00 7.7354E+00
6.8881E-01 1.8301E+00 8.0601E+00
7.2932E-01 2.1606E+00 8.3565E+00
7.7491E-01 2.6154E+00 8.4914E+00
7.9478E-01 2.7675E+00 8.3866E+00
8.1569E-01 2.7668E+00 8.2573E+00
8.3774E-01 2.6945E+00 8.1878E+00
8.8561E-01 2.2802E+00 8.1134E+00
9.1166E-01 1.9739E+00 8.3058E+00
9.3928E-01 1.6784E+00 8.5970E+00
9.6863E-01 1.4867E+00 9.0655E+00
9.9988E-01 1.4359E+00 9.4939E+00
1.0332E+00 1.3998E+00 9.8914E+00
1.1271E+00 1.3281E+00 1.0969E+01
1.2399E+00 1.3157E+00 1.2245E+01
1.3776E+00 1.3899E+00 1.3784E+01
1.5498E+00 1.5782E+00 1.5656E+01
1.7712E+00 1.9205E+00 1.7991E+01
2.0664E+00 2.4738E+00 2.0982E+01
2.4797E+00 3.3372E+00 2.5004E+01
2.7552E+00 3.9380E+00 2.7580E+01
3.0996E+00 4.7097E+00 3.0737E+01
3.2628E+00 5.0735E+00 3.2183E+01
3.4440E+00 5.4903E+00 3.3814E+01
3.6466E+00 5.9564E+00 3.5608E+01
3.8745E+00 6.4808E+00 3.7595E+01
4.1328E+00 7.0796E+00 3.9826E+01
4.4280E+00 7.7757E+00 4.2367E+01
4.7687E+00 8.5881E+00 4.5257E+01
5.1660E+00 9.5580E+00 4.8593E+01
5.6357E+00 1.0742E+01 5.2518E+01
6.1993E+00 1.2195E+01 5.7156E+01
6.8881E+00 1.4088E+01 6.2841E+01
7.7491E+00 1.6755E+01 6.9857E+01
8.8561E+00 2.0837E+01 7.8274E+01
1.0332E+01 2.6216E+01 8.8197E+01
1.2399E+01 3.3519E+01 1.0128E+02
1.3776E+01 3.8461E+01 1.0896E+02
1.5498E+01 4.3775E+01 1.1839E+02
1.7712E+01 5.0951E+01 1.2949E+02
1.9075E+01 5.4413E+01 1.3609E+02
2.0664E+01 5.8580E+01 1.4423E+02
2.2543E+01 6.3554E+01 1.5345E+02
2.4797E+01 6.8535E+01 1.6481E+02
2.7552E+01 7.5748E+01 1.8178E+02
3.0996E+01 9.1955E+01 1.9999E+02
3.3333E+01 1.0210E+02 2.0810E+02
4.0000E+01 1.2514E+02 2.3019E+02
4.4444E+01 1.4005E+02 2.4343E+02
5.0000E+01 1.5730E+02 2.5826E+02
5.7144E+01 1.7793E+02 2.7534E+02
6.6666E+01 2.0263E+02 2.9542E+02
8.0001E+01 2.3356E+02 3.2108E+02
9.9996E+01 2.7438E+02 3.5435E+02
1.2500E+02 3.1881E+02 3.9171E+02
1.3776E+02 3.3962E+02 4.0892E+02
1.5385E+02 3.6404E+02 4.2962E+02
1.7712E+02 3.9793E+02 4.5850E+02
2.0000E+02 4.2396E+02 4.8370E+02
"""

OPTICAL_MATERIALS = {
    "schott_n_bk7": {"form": "schott", "glass": "N-BK7", "wavelength": "air", "temperature_C": 20.0,
                     "range_um": (0.3, 2.5),
                     "B": (1.03961212, 0.231792344, 1.01046945), "C": (0.00600069867, 0.0200179144, 103.560653),
                     "tau": SCHOTT_N_BK7_TAU, "nd": 1.51680,
                     "dndT": {"D0": 1.86e-6, "D1": 1.31e-8, "D2": -1.37e-11, "E0": 4.34e-7, "E1": 6.27e-10,
                              "lambda_TK_um": 0.170}},
    "schott_n_f2": {"form": "schott", "glass": "N-F2", "wavelength": "air", "temperature_C": 20.0,
                    "range_um": (0.365, 2.5),
                    "B": (1.39757037, 0.159201403, 1.2686543), "C": (0.00995906143, 0.0546931752, 119.248346),
                    "tau": SCHOTT_N_F2_TAU, "nd": 1.62005,
                    "dndT": {"D0": 4.62e-7, "D1": 1.17e-8, "D2": -2.35e-11, "E0": 7.47e-7, "E1": 9.81e-10,
                             "lambda_TK_um": 0.263}},
    "schott_n_sf11": {"form": "schott", "glass": "N-SF11", "wavelength": "air", "temperature_C": 20.0,
                      "range_um": (0.37, 2.5),
                      "B": (1.73759695, 0.313747346, 1.89878101), "C": (0.013188707, 0.0623068142, 155.23629),
                      "tau": SCHOTT_N_SF11_TAU, "nd": 1.78472,
                      "dndT": {"D0": -3.56e-6, "D1": 9.20e-9, "D2": -2.10e-11, "E0": 9.65e-7, "E1": 1.44e-9,
                               "lambda_TK_um": 0.294}},
    # Dodge 1984 (ordinary ray, 19 C) and Malitson 1965 (20 C): A_i, lambda_i (um) as the refractiveindex.info files
    # MgF2/nk/Dodge-o.yml (sha256 86f453a855b8eadc...) and SiO2/nk/Malitson.yml (c587670f397241ec...) give them; the
    # same numbers (with lambda_i^2) in Wikipedia's "Sellmeier equation" (revision of 2026-11-18). Malitson's range as
    # the paper's range, 0.21-3.71 um (the database extends it to 6.7 um after Tan 1998; not used here).
    "mgf2_dodge_o": {"form": "sellmeier", "temperature_C": 19.0, "range_um": (0.2, 7.0),
                     "A": (0.48755108, 0.39875031, 2.3120353), "L": (0.04338408, 0.09461442, 23.793604)},
    "sio2_malitson": {"form": "sellmeier", "temperature_C": 20.0, "range_um": (0.21, 3.71),
                      "A": (0.6961663, 0.4079426, 0.8974794), "L": (0.0684043, 0.1162414, 9.896161)},
    "mgf2_film_rodriguez": {"form": "table", "temperature_C": None, "table": MGF2_FILM_RODRIGUEZ_NK},
    "sio2_film_gao": {"form": "table", "temperature_C": None, "table": SIO2_FILM_GAO_NK},
    "ta2o5_film_gao": {"form": "table", "temperature_C": None, "table": TA2O5_FILM_GAO_NK},
    "au_johnson_christy": {"form": "table", "temperature_C": None, "table": AU_JOHNSON_CHRISTY_NK},
    "ag_johnson_christy": {"form": "table", "temperature_C": None, "table": AG_JOHNSON_CHRISTY_NK},
    "al_rakic": {"form": "table", "temperature_C": None, "table": AL_RAKIC_NK},
}
