# lfphys source verification — 2026-11-04, plan item P8 (batch B7): the FLRW background

Purpose: every formula, quotation and number used by `core.cosmology.flrw`, `theories.models.dark_energy`, the
cosmology block of `core.data` and their tests (`tests/test_flrw.py`, `tests/external/test_ext_flrw_astropy.py`),
checked against the source text. Texts fetched on 2026-11-04: arXiv PDFs converted with `pdftotext -layout` (and
without `-layout` where the layout split a formula); journal references and DOIs from the arXiv API (Crossref's API
for Condon & Matthews 2018); the conventions of the Boltzmann code behind Planck 2018 from the source files of CAMB
and CosmoMC on GitHub (raw files, read only, nothing copied into the engine); Astropy's conventions from its installed
source in the comparison image `lfphys-ext` (BSD-3-Clause, comparison only). No contact parameter or personal
identifier was sent with any request. Status codes as in `verification_2026-10-23.md`: VERIFIED (quoted) / DIFFERS
(both given) / NOT FOUND / NOT FETCHED (what replaces it is said).

## 1. Planck 2018 results VI — the parameters as data

Planck Collaboration (N. Aghanim et al.), "Planck 2018 results. VI. Cosmological parameters", A&A 641, A6 (2020),
doi 10.1051/0004-6361/201833910; text arXiv:1807.06209v4 (9 Aug 2021).

* Sect. 2.1: "We assume three neutrinos species, approximated as two massless states and a single massive neutrino
  of mass mν = 0.06 eV." VERIFIED → `PLANCK2018_M_NU_EV = 0.06`, one massive and two massless species.
* Footnote 14: "We take T 0 = 2.7255K (Fixsen 2009), with the ±0.0006K error having negligible impact on results."
  VERIFIED → `PLANCK2018_T_CMB_K = 2.7255`.
* Abstract: "in agreement with the Standard Model prediction Neff = 3.046"; Sect. 7.5.2, Eq. (64): "ρrad = Neff (7/8)
  (4/11)^(4/3) ργ" (read across the layout: "7 4 !4/3 ... ρrad = Neff ... ργ . (64)"), "The standard cosmological
  model has Neff ≈ 3.046, slightly larger than 3 since the three standard model neutrinos were not completely
  decoupled at electron-positron annihilation". VERIFIED → `PLANCK2018_N_EFF = 3.046` and the engine's definition of
  N_eff.
* Sect. 3.1: "θ∗ ≡ r∗ /DM where r∗ is the comoving sound horizon at recombination ... and DM is the comoving angular
  diameter distance"; footnote 12: "The quantity DM is (1 + z)DA , where DA is the usual angular diameter distance."
  VERIFIED (the test computes D_M(z_*) = r_*/θ_* from the table).
* Table 1 caption: "Note that Ωm includes the contribution from one neutrino with a mass of 0.06 eV. The quantity
  θMC is an approximation to the acoustic scale angle, while θ∗ is the full numerical result." VERIFIED (the engine's
  `Om_total` includes the massive neutrino; `Om` does not).
* Table 1, column "Plik best fit" (TT,TE,EE+lowE+lensing), as extracted: "Ωb h2 ... 0.022383", "Ωc h2 ... 0.12011",
  "100θMC ... 1.040909", "τ ... 0.0543", "ln(1010 As ) ... 3.0448", "ns ... 0.96605", "Ωm h2 ... 0.14314",
  "H0 [ km s−1 Mpc−1 ] ... 67.32", "Ωm ... 0.3158", "Age [Gyr] ... 13.7971", "100θ∗ ... 1.041085",
  "rdrag [Mpc] ... 147.049". VERIFIED → `PLANCK2018_BESTFIT`.
* Table 2, column "TT,TE,EE+lowE+lensing+BAO" (68 % limits), as extracted: "Ω b h2 ... 0.02242 ± 0.00014",
  "Ωc h2 ... 0.11933 ± 0.00091", "100θMC ... 1.04101 ± 0.00029", "τ ... 0.0561 ± 0.0071", "ln(10 As ) ...
  3.047 ± 0.014", "ns ... 0.9665 ± 0.0038", "H0 [km s−1 Mpc−1 ] ... 67.66 ± 0.42", "ΩΛ ... 0.6889 ± 0.0056",
  "Ωm ... 0.3111 ± 0.0056", "Ωm h2 ... 0.14240 ± 0.00087", "Ωm h3 ... 0.09635 ± 0.00030", "Age [Gyr] ...
  13.787 ± 0.020", "z∗ ... 1089.80 ± 0.21", "r∗ [Mpc] ... 144.57 ± 0.22", "100θ∗ ... 1.04119 ± 0.00029", "zdrag ...
  1060.01 ± 0.29", "rdrag [Mpc] ... 147.21 ± 0.23", "zeq ... 3387 ± 21", "keq [Mpc−1 ] ... 0.010339 ± 0.000063".
  VERIFIED → `PLANCK2018_BAO`.
* Sect. 7.4.1, Eq. (49): "w(a) = w0 + (1 − a)wa , (49) where w0 and wa are assumed to be constants. In ΛCDM,
  w0 = −1 and wa = 0." Eq. (50): "w0 = −1.028 ± 0.031 (68 %, Planck TT,TE,EE+lowE +lensing+SNe+BAO)" (with wa = 0).
  VERIFIED (the dark-energy model and its `conflicts`).
* Sect. 2.1: "Our main results are based upon the lensed CMB power spectra computed with the August 2017 version of
  the camb Boltzmann code (Lewis et al. 2000) and parameter constraints are based on the July 2018 version of
  CosmoMC". VERIFIED (added 2026-11-04 in the processing of review B7-flrw, C4: the code version behind the tables,
  §2).
* Abstract: "in significant, 3.6 σ, tension with local measurements of the Hubble constant (which prefer a higher
  value)". VERIFIED (the core's validity and the data block, review B7-flrw C12).
* The conversion between Σm_ν and ω_ν = Ω_ν h² is not printed in the paper (searched: "93.14", "94.", "Ων h"; only
  the sterile-neutrino "(94.1 eV) as in PCP13 and PCP15" is found). NOT FOUND in the paper; taken from the code the
  paper used (§2).

## 2. CAMB / CosmoMC: the code behind the paper, and the current code

Rewritten 2026-11-04 in the processing of review B7-flrw (C4, C7). [error in earlier] The first version quoted the
current master branches (CAMB ≥ 1.4) as "the code behind the paper"; the paper's numbers were computed with older
code whose constants, integration limits and neutrino set-up differ (below). Read from github.com/cmbant (raw files;
nothing is copied, the engine implements the physics from the papers; licence of CAMB: "Copyright 2000-2025 Antony
Lewis and Anthony Challinor", LICENCE.txt).

**The code of Planck 2018** (Sect. 2.1 above): CAMB's tag `Aug2017` (commit 2a687f7) and CosmoMC's commit 7932d48 of
2018-07-27 ("update docs for Planck 2018 chains"), which bundles CAMB (`camb/modules.f90`: "version = 'Sept17'";
its `constants.f90` is identical to the tag Aug2017's).

* `camb/constants.f90`, lines 20-37, 57: "h_P = 6.62606896e-34_dl", "G=6.6738e-11_dl !data book 2012, last digit
  +/-8", "sigma_boltz = 5.6704e-8_dl", "k_B = 1.3806504e-23_dl", "Gyr=3.1556926e16_dl", "Mpc = 3.085678e22_dl !seem
  to be different definitions of this?", "default_nnu = 3.046_dl". VERIFIED. CAMB's photon density is "grhog =
  kappa/c**2*4*sigma_boltz/c**3*CP%tcmb**4*Mpc**2" (modules.f90 l. 364): with these G, σ_SB, Mpc ω_γ is 7.01e-5
  below the CODATA 2022 value (z_eq +0.24). Its Gyr is 365.2422 d; with its Mpc, an age's number is 2.149e-5 larger
  than in Julian Gyr. DIFFERS from the engine (CODATA 2022, Julian year); emulated in the tests (`_camb17`).
* `camb/modules.f90`, lines 2937-2953 (the derived parameters): "rs =rombint(dsound_da_exact,1d-8,1/(z_star+1),1d-6)",
  "DA = AngularDiameterDistance(z_star)/(1/(z_star+1))", "ThermoDerivedParams( derived_Age ) =
  DeltaPhysicalTimeGyr(0.0_dl,1.0_dl)", "rs =rombint(dsound_da_exact,1d-8,1/(z_drag+1),1d-6)", "z_eq =
  (grhob+grhoc)/(grhog+grhornomass+sum(grhormass(1:CP%Nu_mass_eigenstates))) -1", "ThermoDerivedParams( derived_kEQ )
  = 1/(a_eq*dtauda(a_eq))"; l. 569 (DeltaPhysicalTimeGyr) "atol = 1d-4/exp(AccuracyBoost-1)"; l. 530 (DeltaTime, the
  distances) "atol = tol/1000/exp(AccuracyBoost-1)" with l. 224 "tol=1.0d-4". `camb/subroutines.f90` l. 143, rombint:
  stops when "i.gt.5.and.abs(error).lt.tol", error = 1 − gmax/g0 (the relative change of the Richardson estimate).
  VERIFIED. So r_* and r_drag start at a = 1e-8 (the omitted ∫₀^1e-8 is 1.85e-5 of r_*, 2.68e-3 Mpc), and the age is a
  Romberg integral stopped at a relative change below 1e-4.
* CosmoMC `batch3/common.ini` l. 92, 94: "accuracy_level = 1", "high_accuracy_default = T" (so AccuracyBoost = 1);
  `batch3/params_CMB_defaults.ini` l. 34, 36: "#normal hierarchy uses one distinact eigenstate approximation for
  0.06, two for mnu>0.06", "neutrino_hierarchy = normal". VERIFIED.
* CosmoMC `source/Calculator_Cosmology.f90` l. 9, 11: "neutrino_mass_fac= 94.07_mcp !conversion factor for thermal
  with Neff=3 TCMB-2.7255", "standard_neutrino_neff = 3.046_mcp"; `source/CosmologyParameterizations.f90` l. 302:
  "CMB%omnuh2=Params(6)/neutrino_mass_fac*(standard_neutrino_neff/3)**0.75_mcp" (for any nnu), l. 341: "CMB%omv = 1-
  CMB%omk - CMB%omb - CMB%omdm" (Ω_Λ = 1 − Ω_m: the radiation is not in the closure; CAMB then adds it to H², so that
  its flat universe has H(z = 0) = H0 (1 + Ω_r)^(1/2), Ω_r ≈ 9.2e-5; `camb/modules.f90` l. 379 "grhov=grhom*
  CP%omegav", `camb/equations.f90` l. 84 "grhoa2=grhok*a2+(grhoc+grhob)*a+grhog+grhornomass"). VERIFIED. DIFFERS from
  the engine, whose closure includes radiation (H(0) = H0 exactly); emulated in the tests.
* The neutrino split: CosmoMC `source/Calculator_CAMB.f90` l. 107 "P%share_delta_neff = .false." before calling
  "CAMB_SetNeutrinoHierarchy"; `camb/camb.f90` l. 428-430: "neff_massive_standard = P%Num_Nu_Massive
  *default_nnu/3", "P%Num_Nu_Massless = nnu - neff_massive_standard" (if nnu is smaller: no massless species and the
  massive degeneracy nnu, l. 432-433: "P%Num_Nu_Massless = 0", "neff_massive_standard=nnu"). VERIFIED. Reading:
  each massive species carries default_nnu/3 = 3.046/3 of a massless species' density when relativistic and m n_std
  (3.046/3)^(3/4) when not (CosmoMC's ω_ν for any nnu) — a Fermi-Dirac gas of the physical mass at (3.046/3)^(1/4)
  T_ν; the rest of nnu is massless. [error in earlier] The
  first version read the degeneracy as N_eff/3 for any N_eff; the engine shared N_eff equally (the massive species
  heated by any extra radiation: ω_ν +11 % at N_eff = 3.5). Since the processing the engine follows CAMB's split
  (`Background(..., N_std=3.046)`; `N_std=None` keeps the equal sharing), C7.

**The current code** (master, read 2026-11-04; CAMB ≥ 1.4.0, 2022): `fortran/constants.f90` "Gyr = 365.25e9_dl*86400
! Julian gigayear", "Mpc = 3.085677581e22_dl", "G = 6.67430e-11_dl", "default_nnu = 3.044_dl"; `fortran/results.f90`
"Integrate_Romberg(this, dsound_da_exact, 1d-9, 1/(z + 1), 1e-6_dl)" (CAMB 1.0.1 to master), z_eq and k_eq as above,
"R = 3*this%grhob*a/(4*this%grhog)", "cs = 1.0d0/sqrt(3*(1 + R))", "dsound_da_exact = dtauda(this, a)*cs" (the sound
horizon the engine integrates). VERIFIED (by the reviewer's `r11_camb_versions.out` and the first version of this
note); these are not the numbers behind the paper.

* CAMB `camb/constants.py` (master): "inv_neutrino_mass_fac = ( zeta3 * 3.0 / 2 / const_pi**2 * 4.0 / 11 * ((k_B *
  COBE_CMBTemp / hbar / c) ** 3 * kappa / 3 / (100 * 1000 / Mpc) ** 2 / (c**2 / eV)) )", "# converts omnuh2 into sum
  m_nu in eV for non-relativistic but thermal neutrinos (no 0.044 factor); ~ 94.07". VERIFIED. Evaluated with
  CODATA 2022 (scipy) the formula gives 94.0641 eV (`tests/test_flrw.py::test_massive_neutrino_density_today_is_m_
  times_n`); CosmoMC's literal 94.07 differs by 6e-5 relative, i.e. 4e-8 in omega_nu: DIFFERS (negligible; both
  given; the Planck tests use the literal, `_camb17`).

**How the tests use this.** `tests/test_flrw.py::_camb17` builds the engine's universe as CosmoMC set it up (ω_γ of
CAMB's G, σ_SB, Mpc through the equivalent T_cmb; CosmoMC's ω_ν; Ω_Λ = 1 − Ω_m) and reads it out with CAMB's
numerics (the engine's integrands through CAMB's Romberg rule, r_s from a = 1e-8, the age in CAMB's Gyr and Mpc). The
size of each ingredient at Table 2's BAO column (`test_camb17_readout_shifts`): the age's units +2.149e-5, its
Romberg rule −2.04e-5 (it stops after 8 refinements, the change falling from 1.5e-4 to 5e-5 against the tolerance
1e-4: robust), the closure −1.7e-5 (and 100 θ_* +8e-6); r_* −1.85e-5; D_M(z_*) +2e-10; z_eq +0.24.

## 3. The CMB temperature — Fixsen 2009

D. J. Fixsen, "The Temperature of the Cosmic Microwave Background", ApJ 707, 916-920 (2009),
doi 10.1088/0004-637X/707/2/916; arXiv:0911.1955v2. Abstract: "The determination from the measurements from the
literature is cosmic microwave background temperature of 2.72548±0.00057 K." VERIFIED → `FIXSEN2009_T_CMB_K`
(Planck rounds it to 2.7255, footnote 14 above).

## 4. Massive neutrinos — Komatsu et al. 2011

E. Komatsu et al., "Seven-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Cosmological
Interpretation", ApJS 192, 18 (2011), doi 10.1088/0067-0049/192/2/18; arXiv:1001.4538v3, Sect. 3.3 "Treating Massive
Neutrinos in H(a) Exactly" (read in the text without layout).

* Eq. (21): "ρν (a) = 2 ∫ d³p/(2π)³ Σi sqrt(p² + m²ν,i) / (e^(p/Tν(a)) + 1)" (extracted as "Z Xq d3 p 1 ρν (a) = 2
  p2 + m2ν,i , (21) (2π)3 ep/Tν (a) + 1 i") — the factor 2 is particle + antiparticle, the momentum distribution is
  that of a relativistic decoupling. VERIFIED.
* "Tν0 = (4/11)1/3 Tcmb = 1.945 K"; Eq. (23): "ρν (a) → (7/8)(4/11)^(4/3) Neff ργ (a) ≃ 0.2271Neff ργ (a)";
  Eq. (24): "ρν (a) = 0.2271Neff ργ (a)f (mν a/Tν0 )"; Eq. (25): "f (y) ≡ (120/(7π⁴)) ∫0^∞ dx x² sqrt(x² + y²)/(e^x
  + 1)". VERIFIED (the engine's F). Komatsu's convention is the unscaled temperature T_ν0 with N_eff multiplying the
  density: Astropy's (§10), not the engine's. [error in earlier] The first version of the module cited Komatsu et al.
  Eqs. (21)-(26) for the engine's convention (the temperature rescaled by (N_eff/3)^(1/4)); that is CAMB's (§2). The
  module now cites Komatsu for F (Eq. (25)) and its limits, CAMB/CosmoMC for the temperature, and Eq. (26) only for
  the Astropy comparison (review B7-flrw C8).
* "The limits of this function are f (y) → 1 for y → 0, and f (y) → 180ζ(3)/(7π⁴) y for y → ∞"; Eq. (26): "f (y) ≈
  [1 + (Ay)p ]1/p", "A = 180ζ(3)/(7π⁴) ≃ 0.3173 and p = 1.83. This fitting formula is constructed such that it
  reproduces the asymptotic limits in y → 0 and y → ∞ exactly. This fitting formula underestimates f (y) by 0.1% at
  y ≃ 2.5, and overestimates by 0.35% at y ≃ 10. The errors are smaller than these values at other y's." VERIFIED.
  The engine uses the exact integral (40-digit check); the fit is what Astropy uses, so its 0.35 % enters the
  comparison's tolerance. Measured in the comparison: the fit's largest error among the rows is 0.34 % at y = 9.9
  (z = 35), consistent with the paper's statement.
* The expansions the tests use beyond these limits are derived, not quoted: sqrt(x² + y²) = x + y²/(2x) + ... gives
  F = 1 + 5y²/(7π²) + O(y⁴ ln y); y + x²/(2y) − x⁴/(8y³) + x⁶/(16y⁵) − ... with ∫ x^n/(e^x + 1) dx = (1 − 2^-n)
  n! ζ(n + 1) gives F = A y [1 + 7.5 ζ(5)/(ζ(3) y²) − (708.75 ζ(7)/8)/(1.5 ζ(3) y⁴) + ...] and w → 5 ζ(5)/(ζ(3) y²);
  each checked against the 40-digit quadrature in the tests.

## 5. Distances and times — Hogg 1999, Carroll 2001

* D. W. Hogg, "Distance measures in cosmology", arXiv:astro-ph/9905116v4 (no journal publication). Eq. (14):
  "E(z) ≡ sqrt(ΩM (1 + z)³ + Ωk (1 + z)² + ΩΛ)"; Eq. (15): "DC = DH ∫0^z dz′/E(z′)"; Eq. (16): DM = "DH (1/sqrt(Ωk))
  sinh[sqrt(Ωk) DC /DH] for Ωk > 0", "DC for Ωk = 0", "DH (1/sqrt(|Ωk|)) sin[sqrt(|Ωk|) DC /DH] for Ωk < 0";
  Eq. (17) (ΩΛ = 0): "DM = DH 2 [2 − ΩM (1 − z) − (2 − ΩM ) sqrt(1 + ΩM z)] / (Ω²M (1 + z))"; Eq. (18): "DA =
  DM/(1+z)"; Eq. (19) with "The correct formula, for Ωk ≥ 0" and "Unfortunately, the above formula is not correct
  for Ωk < 0"; Eq. (21): "DL = (1 + z) DM = (1 + z)2 DA"; Eq. (25): "DM ≡ 5 log (DL/10 pc)"; Eq. (30): "tL = tH
  ∫0^z dz′/((1 + z′) E(z′))". VERIFIED (formulas read across the layout). Eq. (17) is used in the tests in the
  cancellation-free form Ωz − (2 − Ω)(sqrt(1 + Ωz) − 1) of its numerator (algebraically identical).
* S. M. Carroll, "The Cosmological Constant", Living Rev. Relativ. 4, 1 (2001), doi 10.12942/lrr-2001-1;
  arXiv:astro-ph/0004075v2. Eq. (21): "ρcrit ≡ 3H²/(8πG)"; Eq. (36): "t0 − t∗ = ∫t∗^t0 dt = ∫1/(1+z∗)^1 da/(aH(a))";
  "For Ω = ΩM = 1, this yields the familiar answer t0 = (2/3)H0−1"; Eq. (42): "dM (z1 , z2 ) = ... (1/(H0 sqrt(|Ωk0|)))
  sinn[H0 sqrt(|Ωk0|) ∫1/(1+z2)^1/(1+z1) da/(a²H(a))]". VERIFIED. DIFFERS (a slip in the source): Carroll's sentence after Eq. (42), "“sinn(x)” denotes sinh(x) when Ωk0 <
  0, sin(x) when Ωk0 > 0", contradicts his own definitions, Eq. (23) "k = sgn(Ω − 1)" and Eq. (29) "Ωk = 1 − Ω" (with
  "ρk ≡ −(3k/8πGR0²)a−2"): an open universe (k = −1) has Ω < 1, i.e. Ωk > 0, and needs sinh — Hogg's sign. The
  engine uses sinh for O_k > 0. [error in earlier] The first version called Carroll's sentence a sign convention that
  "belongs to his definition of Ωk" (review B7-flrw C11).

## 6. Dust universes with Λ = 0 — Mattig's relation (Kayser, Helbig & Schramm 1997)

R. Kayser, P. Helbig, T. Schramm, "A general and practical method for calculating cosmological distances", A&A 318,
680-686 (1997); arXiv:astro-ph/9603028v3, Appendix B. Eq. (B24) (angular-size distance for λ0 = 0): "D(z) =
(c/H0) 2/(Ω0² (1 + z)²) × [Ω0 z − (2 − Ω0)(sqrt(Ω0 z + 1) − 1)] ... valid for Ω0 > 0"; Eq. (B25): "For Ω0 = 0 one
obtains D = (c/H0) z (1 + z/2)/(1 + z)²"; "(Multiplying Eq. (B24) or Eq. (B25) with (1 + z)/R0 results in the
respective expression for σ as a function of redshift as first derived by Mattig (1958)." VERIFIED (read in the
text without layout; D_L = (1 + z)² D). Mattig, Astron. Nachr. 284, 109 (1958): NOT FETCHED (cited through Kayser
et al.).

## 7. Flat matter + Λ — Condon & Matthews 2018

J. J. Condon, A. M. Matthews, "ΛCDM Cosmology for Astronomers", PASP 130, 073001 (2018) (Crossref: container
"Publications of the Astronomical Society of the Pacific", volume 130, issue 989, article 073001),
doi 10.1088/1538-3873/aac1b2; arXiv:1804.10047. Eq. (A6): "t0/tH0 ≈ (2/(3 Ω0,Λ^(1/2))) ln[(1 + Ω0,Λ^(1/2))/(1 −
Ω0,Λ)^(1/2)]"; Eq. (A10): "t/tH0 ≈ (2/(3 ΩΛ^(1/2))) ln{ (Ω0,Λ/(1 − Ω0,Λ))^(1/2) (1 + z)^(−3/2) + [Ω0,Λ/((1 + z)³
(1 − Ω0,Λ)) + 1]^(1/2) }"; "The fractional errors in Equations A5 and A6 are < 10−3 for all z and all Ω0,m > 0.1
only because the high redshifts at which the omitted Ω0,r (1 + z′)4 term is significant contribute little". VERIFIED.
The "≈" is the neglect of radiation: without radiation (the tests' universe) both are exact; the test evaluates
(A10) as asinh(x) (= ln(x + sqrt(x² + 1))) to avoid the cancellation of the logarithm at high z. The scale factor
a(t) = (Ωm/ΩΛ)^(1/3) sinh^(2/3)(3 sqrt(ΩΛ) H0 t/2) and the parametric dust solutions (cycloid for Ωm > 1, its
hyperbolic analogue for Ωm < 1) are derived in the tests' docstrings by direct integration of the Friedmann equation
(no quotation), and checked against 30-digit mpmath and the ODE route.

## 8. The sound horizon — Eisenstein & Hu 1998

D. J. Eisenstein, W. Hu, "Baryonic Features in the Matter Transfer Function", ApJ 496, 605 (1998),
doi 10.1086/305424; arXiv:astro-ph/9709112v1. Eq. (2): "zeq = 2.50 × 104 Ω0 h2 Θ−4 2.7"; Eq. (3): "keq ≡ (2Ω0 H0²
zeq)^(1/2) = 7.46 × 10−2 Ω0 h2 Θ−2 2.7 Mpc−1"; "The sound speed is cs = 1/sqrt(3(1 + R)) (in units where the speed of
light is unity), where R is the ratio of the baryon to photon momentum density, R ≡ 3ρb /4ργ = 31.5Ωb h2 Θ−4 2.7
(z/103)−1 . (5)"; Eq. (6): "s = ∫0^t(zd) cs (1 + z)dt = (2/(3keq)) sqrt(6/Req) ln[(sqrt(1 + Rd) + sqrt(Rd + Req))/(1
+ sqrt(Req))]". VERIFIED. Eq. (6) is the exact integral for a matter + radiation universe when k_eq is taken as (2 Ω0
H0² (1 + z_eq))^(1/2) (derived in the test; EH write z_eq, the same to 3e-4 at z_eq ~ 3400); the engine reproduces
it to 1e-13.

## 9. The w0-wa dark energy — Chevallier & Polarski 2001, Linder 2003, DESI DR2

* M. Chevallier, D. Polarski, "Accelerating Universes with Scaling Dark Matter", Int. J. Mod. Phys. D 10, 213-224
  (2001), doi 10.1142/S0218271801000822; arXiv:gr-qc/0009008v2. Eq. (30): "wX = −1 + α + β(1 − x)"; Eq. (31): "ρX =
  ρX,0 x^(−3(α+β)) e^(−3β(1−x))" (x the scale factor). VERIFIED.
* E. V. Linder, "Exploring the Expansion History of the Universe", Phys. Rev. Lett. 90, 091301 (2003),
  doi 10.1103/PhysRevLett.90.091301; arXiv:astro-ph/0208512v1. Eqs. (6)-(7): "w(a) = w0 + wa (1 − a) = w0 + wa
  z/(1 + z)"; "Here the exponential in (5) resolves to a−3(1+w0 +wa ) e−3wa (1−a)". VERIFIED (`CPL.density_ratio`).
* DESI Collaboration, "DESI DR2 Results II: Measurements of Baryon Acoustic Oscillations and Cosmological
  Constraints", Phys. Rev. D 112, 083515 (2025), doi 10.1103/tr6y-kpc6; arXiv:2503.14738v3, abstract: "with a favored
  solution in the quadrant with w0 > −1 and wa < 0. This solution is preferred over ΛCDM at 3.1σ for the combination
  of DESI BAO and CMB data. When also including SNe, the preference for a dynamical dark energy model over ΛCDM
  ranges from 2.8 − 4.2σ depending on which SNe sample is used." VERIFIED (the model's `conflicts`).

## 10. Astropy's conventions (comparison only)

Astropy 8.0.2 in `lfphys-ext`, `astropy/cosmology/_src/flrw/base.py` and `traits/neutrino.py` (BSD-3-Clause):
"NEUTRINO_FERMI_DIRAC_CORRECTION: Final = 0.22710731766  # 7/8 (4/11)^4/3" (the exact value is 0.227107317660239,
1.05e-12 relative above the literal), "KOMATSU_P: Final = 1.83", "KOMATSU_K: Final = 0.3173", "TEMP_NEUTRINO: Final =
0.7137658555036082  # (4/11)^1/3"; `nu_relative_density`: "rel_mass_per = (1.0 + (KOMATSU_K * curr_nu_y) **
KOMATSU_P) ** KOMATSU_INVP", "return NEUTRINO_FERMI_DIRAC_CORRECTION * self._nu_info.neff_per_nu * rel_mass" with
"nu_y = (self.m_nu[massive] / (kB_evK * self.Tnu0))" — i.e. N_eff/3 times the density of mass m at (4/11)^(1/3)
T_cmb, which equals the engine's convention with the mass m (N_eff/3)^(1/4) (the comparison uses that). The flat
no-radiation branch uses closed forms ("_hypergeometric_comoving_distance_z1z2", Baes et al. 2017; "_flat_age" with
"np.arcsinh"; the lookback time "based on the ``age(0) - age(z)``"); everything else "quad(...)" at scipy's defaults.
VERIFIED (grepped in the installed files).

## 10a. The neutrino density against the computed physics; the current N_eff (review B7-flrw C10)

* G. Mangano, G. Miele, S. Pastor, T. Pinto, O. Pisanti, P. D. Serpico, "Relic neutrino decoupling including flavour
  oscillations", Nucl. Phys. B 729, 221-234 (2005), doi 10.1016/j.nuclphysb.2005.09.041 (arXiv API); arXiv:hep-ph/
  0506164v1, Eq. (14): "Ων = ρν/ρc = 3m0/(93.14 h2 eV)" (read across the layout: "Ων = ρν 3m0 = ρc 93.14 h2 eV
  (14)"), "Here the number in the denominator is slightly smaller than in the instantaneous decoupling limit
  (94.12)." VERIFIED. 94.12 is the instantaneous value at T_0 = 2.725 K (94.064 eV (2.7255/2.725)³ = 94.116; my
  scaling, not quoted); scaled to 2.7255 K, 93.14 becomes 93.09 eV. The engine's thermal proxy gives Σm/ω_ν = 92.99
  eV (§11.1): ω_ν 0.10 % above the computed spectra for a given Σm; Astropy's convention 0.48 % (0.38 % above the
  engine). Recorded in the module's validity; the engine keeps CAMB's convention, which the Planck numbers used.
* J. Lesgourgues, S. Pastor, "Massive neutrinos and cosmology", Phys. Rep. 429, 307-379 (2006), doi
  10.1016/j.physrep.2006.04.001 (arXiv API); arXiv:astro-ph/0603494, Eq. (12): "Ων = ρν/ρc = Σi mi /
  (93.14 h2 eV)" (read across the layout). VERIFIED (the same number).
* J. Froustey, C. Pitrou, M. C. Volpe, "Neutrino decoupling including flavour oscillations and primordial
  nucleosynthesis", JCAP 12 (2020) 015, doi 10.1088/1475-7516/2020/12/015 (arXiv API); arXiv:2008.01074: "Neff =
  3.0440 with at least 10−4 precision". VERIFIED. The engine's default N_std = 3.046 is Planck 2018's (CAMB Aug
  2017's default_nnu); CAMB ≥ 1.4 uses 3.044.
* DESI DR2 (§9): the journal reference Phys. Rev. D 112, 083515 (2025), doi 10.1103/tr6y-kpc6, confirmed by the arXiv
  API on 2026-11-04 (the reviewer had not checked it).

## 11. Measured results

### 11.1 Planck 2018 against the engine (`tests/test_flrw.py`)

Rewritten 2026-11-04 in the processing of review B7-flrw (C4, C5, C6). [error in earlier] The first version compared
the engine's own values with the tables and gave the agreement "in σ" (posterior standard deviations): 0.002-0.018 σ
is expected of any correct implementation, because the inputs are the paper's own posterior means and z_*, z_drag
are the paper's (recombination is not computed), so that the outputs are deterministic functions of them computed
with the same equations as CAMB. The posterior σ is the wrong scale; the informative number is the difference over
the budget, together with what each row can detect. It also budgeted "CAMB's Romberg tolerance for r_s" (1e-6) and
the current CAMB's units, while the paper's CAMB (§2) integrated r_s from a = 1e-8, stopped the age's Romberg
integral at 1e-4 and used other constants and another closure.

What is compared now: CAMB's readout of the engine (`_camb17`, §2) at the posterior means (ω_b = 0.02242, ω_c =
0.11933, H0 = 67.66, T_cmb = 2.7255 K, N_eff = 3.046, one 0.06 eV neutrino), z_* = 1089.80 and z_drag = 1060.01
from the table. Budget = the printed rounding of the output, of the inputs and of z_*, z_drag (through the engine's
derivatives) + the second-order bound of |mean f − f(mean)| from the printed standard deviations (any
correlations); CAMB's numerics are reproduced, not budgeted. The rows test the background integrals, the densities,
the neutrino and N_eff — not the physics of recombination. Detection (`test_planck2018_rows_detect_and_miss`, the
variant's |diff|/budget where above 1): the massive species as dust at all times ("dust"), no massive neutrino
("no ν"), N_eff = 3.044 instead of 3.046.

| quantity | readout | Planck | diff/budget | budget | detects |
|---|---|---|---|---|---|
| Ω_m (with ν) | 0.311051 | 0.3111 | −0.27 | 1.8e-4 | no ν (8.0) |
| Ω_Λ | 0.688949 | 0.6889 | +0.27 | 1.8e-4 | no ν (8.0); = 1 − Ω_m (CosmoMC's closure): the Ω_m row again. The engine's own Ω_Λ, with radiation in the closure, is 0.688870 (−0.16): the row cannot see the radiation |
| Ω_m h² | 0.1423951 | 0.14240 | −0.32 | 1.5e-5 | no ν (43) |
| Ω_m h³ | 0.0963446 | 0.09635 | −0.23 | 2.3e-5 | no ν (19) |
| age [Gyr] | 13.786967 | 13.787 | −0.02 | 1.6e-3 | no ν (10.6) |
| r_* [Mpc] | 144.5661 | 144.57 | −0.32 | 1.2e-2 | dust (389) |
| r_drag [Mpc] | 147.2125 | 147.21 | +0.20 | 1.25e-2 | dust (383); N_eff = 3.044: 1.00, not |
| 100 θ_* | 1.0411878 | 1.04119 | −0.04 | 5.5e-5 | dust (617), no ν (28), N_eff = 3.044 (1.23) |
| z_eq (CAMB's definition) | 3387.385 | 3387 | +0.52 | 0.74 | dust (748), N_eff = 3.044 (1.75) |
| k_eq [Mpc⁻¹] | 0.0103387 | 0.010339 | −0.28 | 1.2e-6 | dust (680) |
| H0 solved from θ_* | 67.6608 | 67.66 | +0.04 | 0.018 | the θ_* row inverted (the same equation and inputs): not an independent agreement; its tolerance is that row's budget over ∂(100θ_*)/∂H0 = 2.99e-3 (the former 0.1 σ(H0) = 0.042 was not derived) |
| D_M(z_*) [Mpc] vs r_*/θ_* | 13884.73 | 13885.07 | −0.18 | 1.9 | dependent on the r_*, θ_* rows |

Not detected by any row: Astropy's neutrino convention (largest |diff|/budget 0.52), T_cmb = 2.72548 instead of
2.7255, and the conventions of the paper's CAMB themselves: the engine's own values without the readout pass every
row too (age +0.12, r_* −0.23, r_drag +0.29, θ_* −0.04, z_eq +0.20, k_eq −0.58). The readout matters for the claims,
not for passing: e.g. the age's units (+2.149e-5) and Romberg rule (−2.04e-5) nearly cancel, so that the printed
age is the engine's to 1e-6. The engine's own stated errors at these points: age 7.5e-14 Gyr, D_C(z_*) 7.0e-11 Mpc,
r_s(z_*) 8.2e-13 Mpc. With the massive species counted by its actual density instead of CAMB's relativistic
convention, z_eq = 3386.78. [useful]

Table 1, "Plik best fit": Ω_m h² = 0.1431381 (printed 0.14314), Ω_m = 0.315840 (0.3158), age 13.797143 Gyr in the
readout (13.7971: +4.3e-5 Gyr, 0.07 of the budget 6.5e-4 Gyr set by the printed H0 = 67.32 ± 0.005 through ∂t/∂H0 =
−0.0894 Gyr per km/s/Mpc, ω_b, ω_c through ∂t/∂ω = −27.1 Gyr, and the age's last digit); the engine's own age
13.797366 (+2.7e-4, 0.41). ω_ν of the 0.06 eV species: 6.4522e-4 (Σm/ω_ν = 92.99 eV, i.e. 94.064 eV/(3.046/3)^(3/4)
with the kinetic correction 5e-5). [useful]

### 11.2 What the neutrino treatment changes (`test_planck2018_neutrino_convention_effects`,
`test_planck2018_omega_m_cannot_see_the_convention`)

Astropy's convention (the engine with m (N_eff/3)^(1/4)): ω_ν +0.38 %, the best-fit age −6.6e-5 Gyr, 100 θ_* +6.4e-6:
both below the paper's printed digits. The massive species as dust at all times (no relativistic phase): age
+9.6e-5 Gyr, but 100 θ_* +0.034 (about 100 σ): the neutrino's relativistic density before recombination sets the
sound horizon. Table 1's Ω_m h² (tolerance 1.05e-5) passes with the CAMB/CosmoMC convention (|diff| 1.8e-6), with
Astropy's (0.7e-6), with Mangano et al.'s Σm/93.14 eV (2.8e-6) and with Σm/94.07 eV without (N_eff/3)^(3/4)
(9.2e-6); it fails only without the massive species (6.5e-4). [error in earlier] The first version said that Ω_m h²
"checks the neutrino convention" and that "the paper's numbers fix the neutrino treatment only through θ_*": the
paper's numbers confirm that one ~0.06 eV species is counted in Ω_m (Ω_m h²) and that it is relativistic before
recombination (θ_*, r_*, z_eq), but not its convention; the engine's convention (CAMB's formula) is pinned only by
`test_massive_neutrino_density_today_is_m_times_n` (review B7-flrw C6). [useful]

### 11.3 Astropy (`tests/external/test_ext_flrw_astropy.py`, `tests/external/RESULTS.md`)

661 rows: 660 within their derived tolerances (largest diff/tol 0.996, the Ω_ν0 rows, where the whole difference is
Astropy's 11-digit literal for 7/8 (4/11)^(4/3)), one known library-side disagreement kept as a strict xfail:
Astropy's age at z = 1000 of the closed universe (Om0 = 0.35, Ode0 = 0.75, with radiation) comes from QUADPACK's QAGI
at scipy's defaults, which returns 2.93119e-5 for the dimensionless integral with an error estimate of 9.4e-9 while
the integral is 2.889449e-5 (the same integrand at epsrel 1e-13; 30-digit mpmath): 1.4 % high, 45 times its own
estimate; the engine is within 1e-19 Gyr of mpmath (`test_astropy_closed_age_is_a_quadpack_error` pins the cause).
Among the 519 rows with an mpmath reference the engine is the closer side in 344, Astropy in 57, equal in 118
(after the processing of review B7-flrw, which changed the engine's rounding at the 1e-16 level; before: 337, 50,
132); the largest engine error against the references is 8.5e-16 relative, and where Astropy is closer the engine's
error is never above 1e-14. [useful]

## 12. Not fetched

* Friedmann (1922, 1924), Lemaître (1927), Robertson (1935), Walker (1937): the Friedmann equations are textbook GR;
  the formulas used are quoted from Hogg 1999 and Carroll 2001. NOT FETCHED.
* Mattig 1958: through Kayser et al. 1997 (§6). NOT FETCHED.
* The Planck Legacy Archive chains (their best-fit files would give ω_ν to many digits and could test the neutrino
  convention beyond the printed digits): too large to fetch here. NOT FETCHED.
