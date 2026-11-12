# Review: batch B7, plan item P8 — the FLRW background (`core.cosmology.flrw`, `theories.models.dark_energy`)

**Status: awaiting processing.** Reviewer: internal, independent subagent (Claude Opus); I did not write the code under
review. Delivered 2026-11-04. Nothing outside this folder was changed.

**Scope.** `lfphys/lfphys/core/cosmology/flrw.py`, `lfphys/lfphys/theories/models/dark_energy.py`, the cosmology block
of `lfphys/lfphys/core/data.py`, `lfphys/tests/test_flrw.py`, `lfphys/tests/external/test_ext_flrw_astropy.py`,
`lfphys/sources/verification_2026-11-04_p8_flrw.md`, the "Cosmology" rows of `lfphys/README.md`, `STATUS.md` V41 (t)–(w).

**Environment.** Docker from `engine/`, CPU only: `light-funnel-viz` (Python 3, numpy 2.4.6, scipy 1.17.1, mpmath
1.3.0) and `light-funnel-ext` (Astropy 8.0.2) for the comparison suite. Every script states its own `docker run`
line; container names start with `lf-b7rc-`. Each `rNN_*.py` has its output in `rNN_*.out` next to it. Sources were
downloaded to a scratch folder outside the repository (arXiv PDFs → `pdftotext`; CAMB/CosmoMC from GitHub raw files,
`r11_camb_versions.sh`); no contact parameter or personal identifier was sent with any request.

**Baseline.** `tests/test_flrw.py`: 20 passed (7 s). `tests/external/test_ext_flrw_astropy.py`: 662 passed, 1 xfailed
(`r05_ext_suite_run.out`), as the verification note says.

## Summary

| severity | count | findings |
|---|---|---|
| error | 1 | C1 |
| should-fix | 6 | C2–C7 |
| nit | 7 | C8–C14 |

The three most important:
1. **C1** `scale_factor(t)` returns silently wrong a(t) (by 46 orders of magnitude) in the far future of a w ≠ −1
   universe: `O_L a^4` overflows in `_terms`, the Newton iteration overshoots into it and accepts a zero step as
   convergence; `scale_factor_ode` raises `IndexError` there. ΛCDM survives only because a de Sitter Newton step is exact.
2. **C2** `roots()` misses a bounce whose forbidden band is narrower than its scan step: a universe without a big bang
   is reported as having one (`roots() = (None, None)`), and age, distances and a(t) fail with a wrong diagnosis.
3. **C4/C5/C6** The Planck 2018 comparisons are presented as stronger than they are: the CAMB constants were read from
   the current CAMB, not from the CAMB that produced the paper (Gyr = 3.1556926e16 s, r_s from a = 1e-8); the "in σ"
   agreements are expected by construction; and the neutrino convention, claimed to be checked by Ω_m h², is invisible
   to every Planck row (four conventions pass).

## What was checked and holds (status per item)

* **Fermi–Dirac integrals** F(y), J(y) on 186 values of y in [0, 1e8] against 40-digit mpmath with break points at y:
  max relative error 4.4e-16 (F) and 2.2e-16 (J), below the stated 4e-15; the small-y term O(y⁴ ln y) and the large-y
  limit w → 5ζ(5)/(ζ(3) y²) confirmed (`r01`). [useful]
* **Error estimates in regular universes**: 40 checks (Planck 2018 with the massive neutrino against 50-digit
  mpmath with an independently assembled S(a); closed dust up to 1 − a/a_max = 1e-12; loitering universes): the stated
  error was never below the actual one (`r02`; the exceptions are the singular cases of C3). Planck: actual 0–2e-16,
  stated ~4e-15. [useful]
* **a(t)** of `planck2018()` from t = 1e-9 Gyr to 2000 Gyr against an mpmath inversion: ≤ 1.1e-15; 4.7e-14 at
  5000 Gyr, i.e. (tH)·u (`r08`). [useful]
* **CAMB/CosmoMC neutrino convention at N_eff = 3.046** confirmed in both the 2017 Fortran CAMB (tag Aug2017:
  `nu_masses = const/(1.5 zeta3) grhom/grhor omegan .../Nu_mass_degeneracies`, degeneracy `num_massive*default_nnu/3`)
  and CAMB master (`find_nu_mass_for_rho(...grhocrit/grhormass)`, `grhormass = grhor*Nu_mass_degeneracies`): a
  Fermi–Dirac gas of the physical mass at (3.046/3)^(1/4) T_ν, as the engine has it. The ω_ν test catches convention
  mutations (`r04` M1, M4). [useful]
* **CAMB's derived quantities**: `z_eq` with the massive species at their relativistic density, `k_eq = 1/(a_eq
  dtauda(a_eq))`, `dsound_da_exact` with R = 3ρ_b/(4ρ_γ) — confirmed in the 2017 and current code. [neutral]
* **Astropy comparison** reproduced: 661 rows, largest engine error against the 30-digit references 8.5e-16; where
  Astropy is closer (50 rows) the engine's error is never above 1e-14 (`r05_ext_rows.out`). [neutral]
* **Quotations and numbers** (list at the end) all found in the sources as quoted, with the exceptions in C4, C8, C11.
  [neutral]

## Findings

### C1 (error) — far-future a(t): silent wrong values; the ODE route crashes

**Location.** `flrw.py` `_terms` l. 361/365 (`t_l = self.OL * a ** 4 [* density_ratio]`), `_integrand`/`_integrand_s`
(S overflows → integrand 0), `_invert` l. 850–866, `scale_factor_ode` l. 891–894.

**Evidence** (`r09_far_future.py/.out`).
* For `a ≳ 1.3e77` (Planck: t ≳ 3100 Gyr) `O_L a^4` overflows to inf, the integrand of t(a) becomes 0 there and
  t(a) is silently truncated: the engine's own t(a = 1e80) = 3102.3 Gyr; the de Sitter continuation from the verified
  a(2000 Gyr) gives 3220.0 Gyr.
* Matter + dark energy with constant w = −0.99 (`DE.background(70, 0.3, w0=-0.99)`): reference from the engine's own
  t(1e30) plus the closed-form DE-dominated continuation:

  | t [Gyr] | reference a | `scale_factor` |
  |---|---|---|
  | 5158 | 1.0e50 | 1.0e50 (1.8e-14) |
  | 11388 | 1.0e70 | **2.05e116** |
  | 14264 | 1.0e76 | **7.1e142** |
  | 69127 | 1.0e120 | **1e165** |

  Only a numpy `RuntimeWarning: overflow` is emitted. Mechanism: the starting grid ends at a = 1e30; the Newton step
  in ln a (exact for de Sitter, not for a power law) overshoots into the overflow region; there t(a) is too small and
  `dg = a²/sqrt(inf) = 0`, so `step = 0`, `|un − u| = 0 <= tol` and the iteration is declared converged with |g| large.
  Even a = 1e70, below the overflow, is missed. For ΛCDM the same code returns the right a only because the first
  Newton step from a = 1e30 is exact (rel. error 3e-14 at 5000 and 10000 Gyr).
* `scale_factor_ode(t)` for t − t0 ≥ 3186 Gyr (Planck): `IndexError: list index out of range` at l. 894 (the solver
  failed and `sol.y` is empty; `sol.success` is not checked).

**Fix.** Evaluate the integrands from E²(a) = S(a)/a⁴ = O_r a⁻⁴ + O_m a⁻³ + O_k a⁻² + O_L g(a) + … for a > 1 (the
t-integrand a²/√S is 1/E), so nothing overflows below a ~ 1e300; in `_invert` treat a non-finite or zero derivative
as a failed step (bisect), and accept convergence only with |g| within the time tolerance (otherwise raise); in
`scale_factor_ode` check `sol.status` and return nan with a warning after a failure. Tests: a(t) where a > 1e77 for
Λ and for w = −0.99 against the closed-form continuation above.

### C2 (should-fix) — `roots()` misses narrow forbidden bands: no-big-bang universes reported as having one

**Location.** `flrw.py` `roots()` l. 446–469 (sign scan on 4001 points in ξ, step ≈ 0.007, i.e. Δa ≈ 0.014 at a ~ 1).

**Evidence** (`r02` part D, `r06_missed_bounce.py/.out`). O_m = 0.3, O_L = O_L,crit (1 + ε) (O_L,crit = 1.71346,
double root at a_L = 0.4440): S < 0 on a band around a_L and today's universe came from a bounce at its upper edge.

| ε | true band (width / a_L) | `roots()` | `_has_big_bang()` | `age()` | `scale_factor(-30, 'today')` | ODE route |
|---|---|---|---|---|---|---|
| 1e-4 | 0.0233 | bounce 0.44920 | False | ValueError "no big bang" (right) | 0.451055 | 0.451055 |
| 1e-6 | 0.0023 | (None, None) | **True** | FloatingPointError "E^2 <= 0 inside the range?" | FloatingPointError | 0.449923 |
| 1e-8 | 0.00023 | (None, None) | **True** | same | same | 0.449912 |

The public `roots()` returns a wrong answer; every integral that crosses the band and the main a(t) route then fail
with a generic message, while the second route works. No silent wrong value was found (the adaptive quadrature lands a
node in the band), but that is not guaranteed by the code.

**Fix.** For Λ + dust + curvature + radiation S(a) is a quartic: take its real roots directly (companion matrix, then
Newton polish in extended precision as `_S_root` does). In general (massive ν, a dark-energy model), after the sign
scan, minimise S between neighbouring samples that bracket a local minimum (bounded Brent) and test the minimum's sign.
Test: ε = 1e-8 (bounce found; `age()` raises the "no big bang" error; `scale_factor(..., 'today')` agrees with the ODE
route).

### C3 (should-fix) — integrable endpoint singularity at the big bang: the error estimate is not a bound, then a crash with a false diagnosis

**Location.** `flrw.py` `_adaptive` l. 207–213 (the panel at ξ = 0 accepted when d ≤ rtol/10 of the segment; the
recorded error is d); module docstring l. 61 ("never smaller than the actual error"); `tests/test_flrw.py` l. 410–416.

**Evidence** (`r02` part A, `r10_endpoint_singularity.py/.out`). Dark energy alone with constant w (a valid FLRW
universe with finite age and, for w > −1/3, finite conformal time; closed forms η = a^(q−1)/(q−1), t = a^q/q in 1/H0,
q = 3(1+w)/2). In ξ = √a the integrand is 2ξ^α near 0 (η: α = 3w; t: α = 2 + 3w). For a panel [0, h] the
Gauss–Legendre error scales as h^(1+α), so the error left after a halving is 1/(2^(1+α) − 1) times the recorded d
(3.8 at α = −0.66):
* the estimate is exceeded: η at w = −0.22: actual 3.03e-14, stated 2.86e-14 (ratio 1.06); t at w = −0.86: ratio
  1.01; w = −0.20, −0.84, −0.88: ratios 0.86–0.98, i.e. the bound holds only by the margin of the other panels' share;
* from α ≲ −0.7 the routine fails: η for w = −0.24 … −1/3 and t for w = −0.9, −0.95: `FloatingPointError: integrand
  not finite (E^2 <= 0 inside the range?)` — E² > 0 everywhere; the bisection toward ξ = 0 converges so slowly that
  a = ξ² underflows and `O_L a^4 → 0` makes S = 0 (depth ~130).

The CPL test checks the DE-only age only for w ∈ {−0.8, −0.5, 0, 0.5} (no error check) and never η. With matter or
radiation present (all realistic universes) the integrand is regular and none of this happens.

**Fix.** On the first panel subtract the leading power law from `_early()` (p, c) and integrate it analytically
(∫₀ʰ 2ξ^α/√c dξ = 2h^(1+α)/((1+α)√c)), quadrature only for the regular remainder, with the remainder's error added;
or substitute ξ = s^k with k chosen from p so that the integrand is regular. At least replace the message by
"singular integrand at the big bang not supported". Tests: w = −0.22, −0.3, −0.86, −0.95 against the closed forms
with `_check_err`.

### C4 (should-fix) — the CAMB conventions were read from the current CAMB, not from the CAMB that produced Planck 2018

**Location.** `flrw.py` l. 112 (`GYR_S = 1e9 * YEAR_JULIAN  # Julian gigayear (CAMB's Gyr)`);
`sources/verification_2026-11-04_p8_flrw.md` §2 l. 77–81 ("line 921, Integrate_Romberg(... 1d-9 ...)", "Gyr =
365.25e9_dl*86400 ! Julian gigayear ... VERIFIED"); `tests/test_flrw.py` l. 487–489, 516–519 (budget "CAMB's Romberg
tolerance (1e-6 relative)").

**Evidence** (`r11_camb_versions.sh/.out`, `r03` §2–3). Planck 2018 VI (arXiv July 2018) predates CAMB 1.4.0 (tag
1.3.6 is dated 2022-08-31). Every CAMB tag up to 1.3.6 has `Gyr=3.1556926e16_dl` (365.2422 d, not Julian),
`Mpc = 3.085678e22_dl`, `G=6.6738e-11_dl`, `k_B = 1.3806504e-23_dl`, `h_P = 6.62606896e-34_dl`; the Julian gigayear,
CODATA 2018 G and `Mpc = 3.085677581e22` arrive in 1.4.0. The 2017 Fortran CAMB (tag Aug2017) computes the derived r_*,
r_drag as `rombint(dsound_da_exact,1d-8,1/(z_star+1),1d-6)`, i.e. from a = 1e-8; CAMB 1.0.1 (2019) and later from
1e-9. Effects (engine at the paper's parameters):
* the age number in the paper's units is the engine's × (1 + 2.15e-5): Table 1 best fit 13.797663 (engine 13.797366)
  vs printed 13.7971 → difference +5.6e-4 Gyr of the test's 6.5e-4 budget (was +2.7e-4); Table 2 +4.9e-4 of 1.6e-3;
* ω_γ with the old G, k_B, h is 7.0e-5 lower: z_eq 3387.15 → 3387.38;
* the omitted ∫₀^1e-8 of the sound horizon is 2.68e-3 Mpc = 1.85e-5 of r_*: 19 times the 1e-6 "Romberg tolerance" the
  test budgets for CAMB's r_s (1e-9: 2.7e-4 Mpc, 1.85e-6, still above it).

No test flips (`r04` M2, M3: the Planck rows pass with either convention), so the defect is in the records and budgets:
the comment and the verification state as CAMB's what the Planck numbers were not computed with. Which CAMB built the
2018 chains (Aug2017-era Fortran or 1.0) I could not establish from the paper; the Gyr is the same in both.

**Fix.** Name the CAMB version in the verification note (§2) and quote the ≤ 1.3.6 constants next to master's; change
the `GYR_S` comment ("Julian, as CAMB ≥ 1.4; the CAMB behind Planck 2018 used 3.1556926e16 s: its ages are 2.15e-5
larger in number"); either convert the printed ages to Julian Gyr before comparing or add the 2.15e-5 to the age
budget; add the a = 1e-8 truncation (with the version caveat) to the r_*, r_drag, θ_* budgets in place of 1e-6.

### C5 (should-fix) — the Planck comparisons: σ-agreements by construction, a dependent H0 row with an ad hoc tolerance, rows that cannot see what they seem to test

**Location.** `sources/verification_2026-11-04_p8_flrw.md` §11.1 table (l. 201–214, column "in σ"); `tests/test_flrw.py`
`test_planck2018_table2_bao_column` l. 529–537 (H0 from θ_*), l. 506–510 (Ω rows), docstring l. 486–490 ("Tolerance per
row: the printed rounding ... + the second-order bound ...").

**Evidence** (`r03` §5, `r07_planck_rows_power.py/.out`).
* The inputs are the paper's own posterior means, z_* and z_drag are the paper's (recombination is not computed), and
  the outputs are deterministic functions of them computed with the same equations as CAMB. Agreement at 0.002–0.018 σ
  is therefore expected for any correct implementation and says nothing about physics; the posterior σ is the wrong
  scale. The informative number is diff/budget: Ω_m −0.27, Ω_Λ −0.17, ω_m −0.32, Ω_m h³ −0.20, age +0.12, r_* −0.23,
  r_drag +0.30, 100θ_* −0.04, z_eq +0.20.
* What the rows can detect (variant − printed, in units of the row's budget; * = detected): N_eff = 3.044 instead of
  3.046 → r_drag +1.13*, θ_* +1.29*, z_eq +1.41*; the massive ν as dust → r_*, r_drag, θ_*, z_eq at ~400–740*; no
  massive ν → Ω_m, Ω_Λ, ω_m, age, θ_* detected. Not detected: the Astropy/Komatsu ν convention (all |·| ≤ 0.30),
  CAMB ≤ 1.3.6 numerics (age +0.30, θ_* −0.41), T_cmb = 2.72548 instead of 2.7255, and radiation dropped from the Ω_Λ
  closure (Ω_Λ row +0.27: the row does not test the radiation it appears to test).
* "H0 solved from θ_*" (67.6607 vs 67.66) is the θ_* row inverted (same equation, same z_*, ω_b, ω_c), presented in
  §11.1 as a separate agreement (+0.002 σ). Its tolerance is 0.005 + dH/dθ (5e-8 + 1e-6 θ) = 7.0e-3 (derived) **plus
  0.1 σ(H0) = 0.042** (not derived, 6× the rest), while the rounding of ω_b and ω_c carried into H0 (5.7e-3 and
  1.9e-3 km/s/Mpc) and of z_* are left out. Similarly `Omega_m_h3` uses 3 × 0.005/67.66 × 0.09635 (d ln/d ln H0 = 3 at
  fixed Ω_m, whereas the table fixes ω_m: 1) and an unexplained 1e-6 — generous, but not the derivation the docstring
  describes.

**Fix.** Replace the "in σ" column by diff/budget and add per row what it can detect (the r07 matrix); state that z_*,
z_drag and the parameters are the paper's, so the comparison tests the background integrals and N_eff, not the physics
of recombination; mark the H0 row as dependent on the θ_* row (or drop it) and derive its tolerance (input rounding
through ∂H0/∂ω_b, ∂H0/∂ω_c, ∂H0/∂z_*); give the Ω_m h³ row the budget used for the others.

### C6 (should-fix) — "Ω_m h² checks the neutrino convention" is false

**Location.** `tests/test_flrw.py` l. 442 ("Omega_m h^2 = omega_b + omega_c + omega_nu checks the neutrino convention:
0.14314"); `flrw.py` l. 34–37 (the convention "... is the one of CAMB/CosmoMC ...; it reproduces Planck's Omega_m h^2
(tests)"); verification §11.2 l. 230 ("the paper's numbers fix the neutrino treatment only through θ_*").

**Evidence** (`r03` §1, `r04`, `r07`). With Table 1's best fit and the test's tolerance 1.05e-5:

| convention | ω_ν | Ω_m h² | \|diff\| | test |
|---|---|---|---|---|
| engine (CAMB/CosmoMC) | 6.452e-4 | 0.1431382 | 1.8e-6 | passes |
| Astropy / Komatsu Eq. (24) | 6.477e-4 | 0.1431407 | 0.7e-6 | passes |
| Mangano et al. 2005, Σm/93.14 eV | 6.442e-4 | 0.1431372 | 2.8e-6 | passes |
| Σm/94.07 eV without the (N_eff/3)^(3/4) | 6.378e-4 | 0.1431308 | 9.2e-6 | passes |
| no massive neutrino | 0 | 0.1424930 | 6.5e-4 | fails |

The test checks that one ~0.06 eV species is in Ω_m, not its convention. θ_* does not fix the convention either (the
Astropy convention moves 100θ_* by 6e-6 against a 5.2e-5 budget; the verification's own (b)); it fixes only that the
species is relativistic before recombination. The convention is pinned solely by
`test_massive_neutrino_density_today_is_m_times_n` — against CAMB's formula, not against Planck's numbers (`r04`: M1
and M4 fail only there; all Planck rows pass).

**Fix.** Reword the three places: "Ω_m h² confirms that one 0.06 eV species is counted in Ω_m; at Planck's printed
precision the CAMB, Astropy and Mangano conventions are indistinguishable; the engine follows CAMB's formula (pinned by
the ω_ν test)".

### C7 (should-fix) — N_eff ≠ 3.046: the engine heats the massive species, CAMB/CosmoMC do not; the docstring claims CAMB's convention without the restriction

**Location.** `flrw.py` l. 20–23, 34–37 (N_eff "shared equally by n_nu species"; "This convention ... is the one of
CAMB/CosmoMC behind Planck 2018"), `Background.__init__` l. 311–313; ABOUT validity; STATUS V41 (u); verification §2
l. 63–65 ("the massive species carries N_eff/3 of a massless species' density").

**Evidence** (`r03` §4, `r11`). CosmoMC sets `P%share_delta_neff = .false.` and calls `SetNeutrinoHierarchy`, which
gives each massive species the degeneracy `standard_neutrino_neff/3` (`neff_massive_standard =
num_massive_neutrinos*default_nnu/3`; `Num_Nu_Massless = nnu - neff_massive_standard`), and CosmoMC's ω_ν uses
`(standard_neutrino_neff/3)**0.75` for nnu > 3.046. The engine scales the massive species' temperature by
(N_eff/3)^(1/4) for any N_eff. One 0.06 eV species: ω_ν engine/CosmoMC = 1.0001 at N_eff = 2.5 and 3.046, **1.110 at
3.5, 1.227 at 4.0**. Physically ΔN_eff > 0 is extra radiation (Planck 2018 §7.5.2: "We can treat any additional
massless particles produced well before recombination ... as simply an additional contribution to Neff"), which should
not raise the neutrinos' temperature; the engine already has `Or_extra` for that.

**Fix.** Either implement CAMB's split (massive species at N_std/3 each with N_std a parameter, default 3.046;
ΔN_eff massless) or keep the equal sharing as a declared alternative and restrict the CAMB claim to N_eff = 3.046 in
the docstring, ABOUT validity, README and STATUS V41 (u). Add a test at N_eff = 3.5 against CosmoMC's formula.

### C8 (nit) — Komatsu et al. 2011 is cited for a convention it does not use

**Location.** `flrw.py` l. 23 ("A species of mass m has (Komatsu et al. 2011, Eqs. (21)-(25)) rho_nu = ... F(y),
y = m c^2 / (k T_nu)" with T_ν the rescaled temperature); ABOUT `basis` "Komatsu et al. ... Eqs. (21)-(26)".

**Evidence.** Komatsu et al. (arXiv:1001.4538v3, §3.3): "the present-day neutrino temperature, Tν0 = (4/11)1/3 Tcmb =
1.945 K"; Eq. (24) "ρν (a) = 0.2271Neff ργ (a)f (mν a/Tν0 )" — the unscaled temperature with N_eff multiplying, i.e.
Astropy's convention (the external test says so). Eq. (26) is the fit the engine does not use.

**Fix.** Cite Komatsu for F(y) (Eq. (25)) and its limits; attribute the temperature rescaling to CAMB/CosmoMC; drop
Eq. (26) from the core's basis (it belongs to the Astropy comparison).

### C9 (nit) — accuracy statements stated without their conditions

**Location.** `flrw.py` l. 60–62 ("stays below 1e-12 relative"); ABOUT validity l. 93–95 ("оценка ≤ 1e-12 относительной;
фактическая ошибка ... ≤ 2e-13"; "a(t) — до ~1e-14 относительной").

**Evidence** (`r02` B, C; `r09`). Near a turnaround the conditioning of z → a dominates: closed dust at 1 − a/a_max =
1e-12: actual 1.6e-10, stated 3.8e-9; a loitering universe (ε = 1e-9): actual 2.6e-10, stated 1.9e-7. a(t) carries
(tH)·u: 4.2e-14 at 3000 Gyr. The estimates stay honest; the numbers in the text are true only for the tested universes.

**Fix.** "≤ 1e-12 / ≤ 2e-13 away from turnarounds, bounces and loitering (measured); near them the returned estimate
grows with the conditioning and remains an upper bound"; "a(t): relative error ≈ (tH) u".

### C10 (nit) — the ν density convention against the physical value is not quantified

**Location.** ABOUT validity ("спектральные искажения неполного расцепления не учитываются"); STATUS V41 (u).

**Evidence.** Mangano et al. 2005 (hep-ph/0506164, Eq. (14)): "Ων = ρν/ρc = 3m0/(93.14 h2 eV)", "slightly smaller than
in the instantaneous decoupling limit (94.12)" (94.12 corresponds to T0 = 2.725 K: 94.064 (2.7255/2.725)³; my
scaling, not quoted). Lesgourgues & Pastor 2006 (astro-ph/0603494, Eq. (12)) quote the same 93.14. Scaled to 2.7255 K
this is ≈ 93.09 eV, while the CAMB proxy (N_eff/3)^(3/4) gives 93.00 eV (engine 92.99 with the kinetic term): the
convention makes ω_ν ≈ 0.1 % larger than the computed distorted spectra for a given Σm (Astropy's: +0.38 %). The
current standard N_eff is 3.0440 (Froustey, Pitrou & Volpe 2020, arXiv:2008.01074: "Neff = 3.0440 with at least 10−4
precision").

**Fix.** One sentence with these numbers in the validity/STATUS item; keep CAMB's convention for reproducing Planck.

### C11 (nit) — verification note: wrong explanation of Carroll's sinn sign

**Location.** `sources/verification_2026-11-04_p8_flrw.md` l. 127–128 ("Carroll's sign convention for sinn — "sinh(x)
when Ωk0 < 0" — belongs to his definition of Ωk").

**Evidence.** Carroll (astro-ph/0004075v2) defines "ρk ≡ −(3k/8πGR0²)a−2", "Ωk = 1 − Ω ; (29)" and "k = sgn(Ω − 1)
(23)" — the same sign as Hogg (open: Ω_k > 0). His sentence after Eq. (42), "“sinn(x)” denotes sinh(x) when Ωk0 < 0,
sin(x) when Ωk0 > 0", contradicts his own Eqs. (23), (29): it is a slip in the source, not a different convention.
The engine (sinh for O_k > 0) is right.

**Fix.** Record it as a sign error in Carroll's text (DIFFERS), not as a convention.

### C12 (nit) — the core's ΛCDM and the Planck parameters carry no statement of the known tensions

**Location.** `flrw.py` ABOUT `conflicts: []`, validity; `data.py` Planck block.

**Evidence.** Planck 2018 VI abstract: "in significant, 3.6 σ, tension with local measurements of the Hubble constant
(which prefer a higher value)"; DESI DR2 (arXiv:2503.14738v3) prefers w0 > −1, wa < 0 at 3.1σ (2.8–4.2σ with SNe) —
cited in the CPL model's `conflicts` but not in the core module whose Λ it concerns. Neither refutes Λ (layer placement
of Λ in the core and of CPL in `theories.models` is right: CPL is a two-parameter fit), but the core's text should
point to them, and `planck2018()` should say the parameters are ΛCDM-model-dependent.

**Fix.** One line in the core's validity and in the `data.py` comment.

### C13 (nit) — functions without an independent check (LAYERS rule (c))

* `roots()`: only a closed-dust turnaround and one easy bounce (C2 shows the gap).
* `z_equality("exact")` with massive species: only reported (3386.78), never checked against a second route.
* `angular_diameter_distance_z1z2` for O_k < 0 with z1 > 0: only the z1 = 0 identity; Hogg's Eq. (19) with the cosine
  taken with its sign (sin(a − b) = sin a cos b − cos a sin b) would be an independent check.

### C14 (nit) — small API edges (`r12_api_edges.py/.out`)

* `densities()` docstring "they sum to one" while the dict contains `baryons` (a part of `matter`): the sum is 1.1233.
* `Background(70, -0.1)` → "Ob is part of Om and cannot exceed it" (the real reason is a negative Om; the
  `min(self.Om, ...) < 0` branch of `roots()` is unreachable).
* `from_physical(..., OL=0.7)` always fails ("give only one of Ok, OL") because `Ok=0.0` is passed explicitly.
* `angular_diameter_distance_z1z2(2.0, 0.5)` returns −2241 Mpc; the docstring requires z1 < z2 but nothing refuses it.

## Literature: what was quoted and checked (grepped in the downloaded text)

| source | checked | result |
|---|---|---|
| Planck 2018 VI, arXiv:1807.06209v4 | Table 1 "Plik best fit" (all values in `PLANCK2018_BESTFIT`), Table 2 "TT,TE,EE+lowE+lensing+BAO" (all values in `PLANCK2018_BAO`), Table 1 caption, footnote "We take T 0 = 2.7255K (Fixsen 2009)", Sect. 2.1 neutrino sentence, Eq. (64), "Neff ≈ 3.046", "θ∗ ≡ r∗ /DM", "DM is (1 + z)DA", Eqs. (49), (50), "(94.1 eV) as in PCP13 and PCP15", abstract "3.6 σ" | as quoted |
| Fixsen 2009, arXiv:0911.1955v2 | "2.72548±0.00057 K" | as quoted |
| Hogg 1999, astro-ph/9905116v4 | Eqs. (14)–(21), (25), (30); "The correct formula, for Ωk ≥ 0"; "not correct for Ωk < 0" | as quoted |
| Kayser, Helbig & Schramm 1997, astro-ph/9603028v3 | (B24), (B25), Mattig remark | as quoted |
| Eisenstein & Hu 1998, astro-ph/9709112v1 | Eqs. (2), (3), (5), (6) | as quoted |
| Komatsu et al. 2011, arXiv:1001.4538v3 | Eqs. (21)–(26), "Tν0 = (4/11)1/3 Tcmb = 1.945 K", fit errors | as quoted; convention attribution C8 |
| Chevallier & Polarski 2001, gr-qc/0009008v2 | Eqs. (30), (31) | as quoted |
| Linder 2003, astro-ph/0208512v1 | Eqs. (6), (7), "resolves to" | as quoted |
| Carroll 2001, astro-ph/0004075v2 | Eqs. (21), (36), (42), "familiar answer t0 = (2/3)H0−1", sinn sentence | as quoted; explanation C11 |
| Condon & Matthews 2018, arXiv:1804.10047 | (A6), (A10), "fractional errors ... < 10−3" | as quoted |
| DESI DR2, arXiv:2503.14738v3 | abstract (3.1σ; 2.8–4.2σ) | as quoted; the journal reference (PRD 112, 083515) not checked (not in the arXiv PDF) |
| CAMB, CosmoMC (GitHub) | master: `constants.py/f90`, `results.f90` l. 500, 921, 2564, 1305–1318; CosmoMC `Calculator_Cosmology.f90` l. 9, 11, `CosmologyParameterizations.f90` l. 300–310 | as quoted for master; the version behind Planck 2018 differs (C4) |
| Mangano et al. 2005, hep-ph/0506164; Lesgourgues & Pastor 2006, astro-ph/0603494; Froustey et al. 2020, arXiv:2008.01074 | 93.14 eV, 94.12, N_eff = 3.0440 | used in C10 |

Not obtained: Mattig 1958 and the Friedmann–Lemaître–Robertson–Walker originals (as in the verification note); the
Planck Legacy Archive chains (their best-fit files would give ω_ν to many digits and could actually test the neutrino
convention, C6) — too large to fetch here.

## Files in this folder

| file | what |
|---|---|
| `r01_fermi_dirac_sweep.py/.out` | F(y), J(y) on 186 y against 40-digit mpmath; limits |
| `r02_error_bounds.py/.out` | stated vs actual errors: DE-only, near turnaround, loitering, missed bands, Planck |
| `r03_planck_conventions.py/.out` | Ω_m h² under four conventions; CAMB ≤ 1.3.6 constants; r_s from 1e-8; N_eff ≠ 3.046; H0-row tolerance |
| `r04_mutations.py/.out` | six variants of the engine through `tests/test_flrw.py` |
| `r05_ext_suite_run.out`, `r05_ext_rows.py/.out` | the Astropy suite run; engine vs Astropy distances to the exact references |
| `r06_missed_bounce.py/.out` | public functions when `roots()` misses a band |
| `r07_planck_rows_power.py/.out` | which Planck rows detect which variant |
| `r08_scale_factor.py/.out` | a(t) of Planck 2018 against mpmath from 1e-9 to 5000 Gyr (ΛCDM: right even past the overflow, see C1) |
| `r09_far_future.py/.out` | a(t) beyond the overflow; the ODE route's crash; w = −0.99 |
| `r10_endpoint_singularity.py/.out` | the error estimate at the big-bang power-law singularity |
| `r11_camb_versions.sh/.out` | CAMB constants and sound-horizon call by version; CosmoMC neutrino set-up |
| `r12_api_edges.py/.out` | small API edges |
