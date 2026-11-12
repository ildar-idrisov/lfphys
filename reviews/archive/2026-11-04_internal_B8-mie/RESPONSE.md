# Response to review B8-mie (the exact Mie series P1 and v17_mie_scattering P14.8)

Processed on 2026-11-04 by a subagent (Claude Opus) that did not write the review or the code under review. The review
text and the reviewer's scripts are unchanged; scripts that had to be adapted were copied to the processing scratch
folder, never edited here.

**Outcome: 14 findings — 13 fixed, 1 partly fixed (M6: stated, the air index itself open), 0 rejected; 4 problems
found while processing, all fixed.** The STATUS and README changes are in "Changes for the integrator" at the end.

## How the processing was checked

- **Environment.** Docker `light-funnel-viz` (numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0) and `light-funnel-ext`
  (miepython 3.3.0), from `engine/`, on the CPU. Containers were named `lf-b8pm-*`, and none is left
  (`docker ps -a`).
- **Reproduction.** The reviewer's scripts were re-run against a snapshot of the engine taken before any change:
  s02, s03, s03b, s03c, s05b, s06, s06b, s06c, s07, s07b, s08, s08b, s10, s11, s12 and s12b. Their outputs are identical
  to the review's except for wall times. s09 needs the external image; the same measurement is now a test
  (`test_miepython_coefficient_error_by_order`).
- **Final runs.**

  | run | result |
  |---|---|
  | `lfphys`: `test_mie.py`, `test_mie_debye.py`, `test_mie_water.py`, `test_boundary.py`, `test_layers.py`, `test_licences.py` | 398 passed |
  | `test_fdtd_scattering.py` (it calls `core.optics.mie`) | 20 passed, 2 skipped |
  | v17's tests and the shared `test_checkpoint.py` / `test_restore.py` for v17 | 31 passed |
  | the whole external suite | 2967 passed, 7 skipped, 19 xfailed |
  | `make_results.py` | RESULTS.md regenerated, problems: 0 |
  | browser key-frame check `keyframes.mjs` for v17, on a private server (port 8541, run twice) | all equal |

  Screenshots of two worlds were looked at.

- **Status tags** follow `AGENTS.md` §3 rule 11.

---

## M1 — the coefficient bound 2e-11 fails on narrow resonances — **fixed** [error in earlier]

**Summary.** On the peak of a TE resonance of width Γ the forward error is the problem's conditioning, ~u·x/Γ (6.4e-3 at
Γ = 1.5e-11). The engine is backward stable in x.

**Reproduced.** s05b gives an identical output. The engine's code for the coefficients is unchanged: this was a false
claim, not a numerical defect.

**Fix.** The accuracy is now stated as a mixed forward–backward bound:

  |a_n − a_n^exact| ≤ u (F·N·max|a_k| + K·x·|∂a_n^exact/∂x|), with u = 2⁻⁵³, F = 4 and K = 8.

- `mie.ACCURACY` and `mie.coefficient_bound(x, sensitivity)` implement it. The sensitivity is supplied by the caller
  from an exact reference; with none, the function returns the floor and says where the floor alone holds.
- The constants were measured over 22 cases (x = 1e-3 … 1e4: absorbing, m < 1, |m| up to 14, m = 1.05 … 4) and the
  five resonance peaks of s05b (Γ = 6.3e-4 … 1.5e-11). F ≤ 1 holds with K = 4, and K ≤ 4 with F = 1. The tests assert
  the half bound.
- The module docstring, ABOUT (validity) and the verification record say that the narrow resonances are
  ill-conditioned problems. Away from them the error is ~1e-13 to 1e-12 of the largest coefficient.

**Files.**
- `lfphys/lfphys/core/optics/mie.py`
- `lfphys/tests/test_mie.py`: `_ref_with_sensitivity`, `BOUND_CASES`, `PEAKS`,
  `test_every_coefficient_within_the_stated_bound`, `test_the_bound_holds_on_resonance_peaks`
- The external comparison (see M8)
- `lfphys/sources/verification_2026-11-04_p1_mie.md` §1

**Verification.**
- Every order of the 22 cases is within the bound, against 50-digit references and the exact coefficients' derivatives
  by a 50-digit difference.
- On the peaks:
  - the error exceeds 0.05·u·x/Γ: it really is the conditioning;
  - the old 2e-11 fails on the three narrowest peaks (negative control of the earlier claim);
  - the floor alone fails on four peaks;
  - an engine run at x moved by 256 ulps fails the bound, so K = 8 is not loose.
- In the external suite the engine's budget is now this bound with the 50-digit sensitivity, as the review suggested
  (option a).

## M2 — v17's `energy` check failed on a correct engine; the cause was Gauss–Legendre weights — **fixed** [error in earlier]

**Summary.** numpy's and scipy's weights near μ = ±1 are off by up to 6e-9. The forward peak sits there, so the
quadrature misses the series by 1e-11 to 1e-8.

**Reproduced.** s08, s08b, s12 and s12b give identical outputs. In addition (`p01_gl_weights`), weights recomputed from
the three-term recurrence are just as wrong: 1.3e-8 at n = 1120 and 8e-7 at n = 3600, also in Reinsch's difference form.

The cause is the weight formula itself. It is evaluated at the rounded node, where P_{n−1} is small, so its relative
sensitivity to the node's last bit grows like n³u. Recomputing the weights in double precision cannot fix it.

**Fix.**
- **The rule.** Angular integrals now use Fejér's second rule, `mie.fejer2(n)`.
  - Its weights are an explicit sine sum without cancellation: Waldvogel, BIT 46, 195 (2006), Eq. (2.3). It was
    fetched and quoted in the verification record.
  - The arguments of the sines are reduced in integers before rounding. Measured against 30-digit sums: ≤ 14 u at
    n = 400 and ≤ 48 u at n = 4000; 418 u before the reduction.
  - The rule is exact to degree n − 2.
- **The integrals.** `mie.angular_integrals(a, b, x)` returns Q_sca and g with the derived bound
  u(x²Q_ext²/(2Q_sca) + 8N + 16).
  - First term: the nodes are rounded cosines, |δμ| ≤ u. The forward lobe of height x⁴Q_ext²/8 and width ~1/x²
    changes by at most its total variation against the integral x²Q_sca; the bound takes 4× this estimate.
  - Second term: the sums S over N orders.
  - Measured: ≤ 0.12 of the bound for x = 2 … 2900, including absorbing spheres, m < 1, 10 + 10i and the conductor.
- **v17.** `energy` uses the quadrature for N ≤ 3000 (~0.8 s at most). Above that it uses Re a_n = |a_n|², as before,
  but with a derived tolerance of 16 u instead of "2e-11 × 5". The real part of the denominator is bit-for-bit the
  numerator, so only the complex division's rounding remains; measured ≤ 4 u.
- **Texts.** The README's "cause not found" is replaced by the cause. The test helper with numpy's weights is kept only
  as a negative control.

**Files.**
- `mie.py`
- `tests/test_mie.py`: `test_fejer_rule_is_exact_and_its_weights_accurate`, `test_angular_integrals_equal_series`
  with 11 cases up to x = 1714
- `visualizations/v17_mie_scattering/viz.py`, `README.md`, `tests/test_v17_mie_scattering.py`
- The verification record §1

**Verification.**
- The 5.3396 µm drop at 550 nm (x = 61), the review's failing world, now passes. Negative controls:
  - numpy's Gauss–Legendre weights substituted for Fejér's rule fail the derived bound (in v17, and in the engine test
    for 36 ≤ x ≤ 500: 2.1–70× the bound);
  - a τ_n wrong by 1e-6 fails the check;
  - an imaginary part leaking into D_n fails the Re a = |a|² identity;
  - T_2n, aliased to 1 at every node, shows that Fejér's rule is not exact beyond its degree.

## M3 — `theorem`, `energy` and `mueller` cannot detect wrong coefficients — **fixed**

**Summary.** These are identities of the series' structure.

**Reproduced.** s10 gives an identical output.

**Fix.**
- **v17.** The three checks are relabelled in their labels, notes and help text:
  - `theorem` is now «Угловая сумма при θ = 0 … (оптическая теорема в форме ряда)»;
  - `energy` and `mueller` are marked «тождество»;
  - each note says what the check tests: the angular functions, the quadrature, or that the arithmetic stayed real.
- **The coefficients' checks** are `debye`, the second route, and a new `wiscombe` check. It calls
  `mie.wiscombe_self_test()`, the engine at Wiscombe's published Appendix III cases (x = 100, m = 1.5 and 1.5 − 0.1i).
  14 printed quantities are compared, within half a unit of the last printed digit; the measured worst is 0.92. Like
  `water`, it tests the engine at fixed published spheres and says so.
- **`boundary` and `plane_N`** notes now say they test the assembly of the fields, not D_n, ψ_n or χ_n.
- **Engine tests.** The docstrings are corrected (`test_optical_theorem`, `test_mueller_identities`, the energy test,
  the module docstring), and `test_optical_theorem` gained a negative control (a wrong τ_n).
- **Not adopted:** the flux optical theorem (optional in the review). It is also blind to the coefficients' values (the
  review says so), and the published-value check gives v17 what was missing.

**Files.** `mie.py` (`WISCOMBE_1979`, `wiscombe_self_test`), `viz.py`, `web/view.js` (help), v17's `README.md`,
`tests/test_mie.py`, `tests/test_v17_mie_scattering.py`.

**Verification.**
- `test_only_debye_and_wiscombe_catch_wrong_coefficients`: with D, ψ or χ wrong by 1e-3, `theorem`, `energy` and
  `mueller` pass while `debye` and `wiscombe` fail.
- `test_the_identity_checks_catch_what_they_test`: each identity check, and `boundary`, fails when its own engine part
  is broken (a wrong angular sum, S33 without the conjugate, swapped c_n and d_n).
- Every pass/fail check v17 shows now has a negative control.

## M4 — v17's `debye` tolerance 5e-10 failed for m = 0.75 at large x — **fixed** [error in earlier]

**Reproduced.** s03c gives an identical output. The review's own example world (n = 1 in 1.333, 1000 µm) is refused
by v17 (x = 2.2e4). An admitted one, 860 µm (x = 1.9e4), has an error of 1.0e-9.

**Found while processing** (the cause of the scatter, see P1). The Debye route lost up to 5e-9 at single orders: at the
poles of D_n(mx), the zeros of ψ_n, it multiplied D_n by p_n = ψ_n/ξ_n. Two cases:

| m, x | before (40-digit reference) | after |
|---|---|---|
| 2, 100 | 206 N u at n = 59 | 4.7 N u |
| 2.88, 6411 | 4632 N u | 176 N u (the Mie route itself: 113 N u) |

The product ψ'/ξ is now formed without D_n, as p_{n−1}·ξ_{n−1}/ξ_n − (n/z)p_n; the same holds for ψ'(x)/ξ(x) in 1 − R22.

**Fix.**
- `mie_debye.check_against_mie(m, x)` gives a per-order tolerance u(1000 N + 32 x|da_n/dx|/max|a|) (`ACCURACY`).
  - The floor covers the route's logarithmic sums (their partial sums reach |x|).
  - The second term covers the conditioning near narrow resonances, which both routes share. It is estimated in the run
    by a central difference of `mie.coefficients` with relative step 2⁻⁴⁶; the docstring states the step's resolution
    and noise.
- v17's `debye` uses this function.
- The ABOUT now gives the accuracy (~1e-15 at x = 10, ~1e-12 at 1000, up to 1e-9 at 2e4 for m < 1) and the tested range
  Im(m)·x ≤ 1e4; the old "≲ 700" was conservative.

**Files.** `lfphys/lfphys/core/optics/mie_debye.py`, `tests/test_mie_debye.py`, `viz.py`, v17's `README.md`, the
verification record §3.

**Verification.**
- 281 cases: 14 m from 0.5 to 10 + 10i at x = 10 … 19 900, 150 random (m, x), and the five resonance peaks. The worst
  err/tol is 0.46 (`p08b_debye_check`).
- `test_debye_sum_equals_mie` covers 20 cases, including both outliers and two peaks.
- `test_debye_check_detects_a_wrong_engine`: D, D(mx) only, ψ or χ wrong by 1e-3 fails (err/tol > 1e3).
- `test_debye_route_at_the_poles_of_D_against_40_digits` has a negative control.
- v17: `test_debye_check_of_an_air_bubble_at_large_x` (x = 1.9e4, error 1.0e-9) passes.

## M5 — Debye terms of a weakly absorbing m ≈ 1 drawn as "light of one path" — **fixed** [error in earlier]

**Reproduced.** s03b and s03c give identical outputs.

**Fix.**
- **The remainder.** The powers R11^p of the terms and of the remainder now use R11 = 1 − (1 − R11) from the
  cancellation-free form. For m = 1 + 1e-6 i at x = 100 the miss of the partial sums plus the remainder falls from
  5.1e-4 to 7e-9 (s03b re-run on the processed engine). The terms there are 7.8e6 times the largest coefficient, so this
  is their round-off.
- **The flags.** `coefficients` returns per-order flags `diverges_a` and `diverges_b` (|R11| > 1 + 1e-9) and the
  `amplification` (the largest term over the largest |a_n|).
- **The ABOUT and docstring** say that the series converges only where |R11| < 1, and that the closed form is its
  continuation where it does not.
- **v17** sends a notice when orders diverge or the terms exceed the total more than tenfold, and the phase-function
  legend says the curves are cancelling terms. The physical cancellation for real m → 1 is described as such.

**Files.** `mie_debye.py`, `tests/test_mie_debye.py` (`test_debye_terms_where_the_series_diverges`), `viz.py`,
`web/view.js`, `tests/test_v17_mie_scattering.py` (`test_a_diverging_debye_series_is_announced`).

**Verification.**
- m = 1 + 1e-6 i: 21 orders are flagged, all above x; the amplification is > 1e6.
- Negative controls:
  - the old remainder misses by > 1e-5;
  - m = 1.0001 has no diverging orders (amplification 10–1e3);
  - water at x = 1714 has an amplification < 2.
- v17 announces the divergence for n = 1 + 0.01i and stays silent for water. Seen on the page (screenshot).

## M6 — vacuum as the medium not stated — **partly fixed** (stated; an air index stays open)

**Reproduced.** s11 gives an identical output.

**Fix.**
- v17's header lists the vacuum medium among the approximations, with the shift of water's bows in air: −0.054° (p = 2)
  and +0.096° (p = 3) for an illustrative n_air − 1 = 2.77e-4. Any other medium is stated as homogeneous and without
  dispersion.
- v17's README and the verification record §4 now say the quoted angles are for vacuum.

**Open.** A sourced air index, with air as the default medium. Ciddor 1996 was not obtained: NIST's documentation gives
its equations only as images. This is STATUS V44 (l), with new text below.

**Verification.** `test_the_medium_cut_and_coarse_sampling_are_stated`: "вакуум" appears for n_medium = 1 and not for
1.0003.

## M7 — size averages: what `err` means, the ±3σ cut, the ripple, a README number — **fixed** [error in earlier] ×4

**Reproduced.** s06, s06b, s06c and s07 give identical outputs (supernumerary `sky_sum` 0.312).

**Fix.**
1. **`err`.** It is now described as an order-of-magnitude estimate of the largest error over the angles: the actual
   largest error is 0.1–3 times it, and it is not a per-angle error. This is said in mie_poly's docstring, ABOUT and
   `average` docstring, in v17's `sky_sum` note, in the README and in the sky text.
2. **The cut.** The default is now ±4σ instead of ±3σ. `size_nodes` and `average` return `tail`, the gamma probability
   cut off.
   - The bias was measured ≤ 2–3 × tail of the peak: at 4σ, ≤ 5.5e-4 for 15 µm ± 15 %; at 3σ it was up to 4.6e-3.
   - It is stated in the docstring, the header approximations and the note.
   - v17's cap rose from 1200 to 1600 nodes, so that the rainbow preset is not coarse at 380 nm (1589 nodes).
3. **Resonances** are sampled, not resolved: [neutral], unchanged.
4. **The ripple.** The statement is corrected with the measured periods: 1.25–1.28 and 1.18 near the bows (resolved),
   ~0.27 at 180° (not resolved; the sum relies on the weight's smoothness, and the largest preset errors sit there).
5. **The supernumerary number.** The README's `sky_sum` 0.11 is corrected: 0.31 under the old code, 0.18 now. All
   preset numbers were re-measured (16 wavelengths).

**Files.** `lfphys/lfphys/core/optics/mie_poly.py`, `tests/test_mie_water.py`
(`test_the_cut_of_the_size_distribution`, `test_size_average_converges_with_the_node_spacing` now max-based), `viz.py`,
`web/view.js`, v17's `README.md`.

**Verification.**
- `tail` agrees with direct quadrature of the pdf to 1e-10.
- The 4σ bias is ≤ 3 × tail. Negative control: the old 3σ bias exceeds that bound.

## M8 — the miepython xfail text and the docstring's bound — **fixed** [error in earlier]

**Fix.**
- The xfail reason now says that miepython's coefficients carry an error of about the same size at every order: ~3e-13
  of the largest at x = 100, ~1e-12 at 1000, ~1.1e-9 at 1e4, up to 3e-8 near n ≈ x.
- The docstring now gives the engine's bound as u(4N + 8s) with the 50-digit sensitivity, instead of "1e-12 … / 2e-11".
- `test_miepython_coefficient_error_grows_with_x` became `test_miepython_coefficient_error_by_order`. It asserts the
  per-order picture (medians at x = 100, 1000 and 1e4, the size near n ≈ x) and that the engine is within its bound.

**Found while processing** (P2). With the engine's honest budget, the coefficient rows a_1 and a_60 at x = 100
(miepython 3.7–4.2e-13 off, the engine 1.6e-14) exceed the 16 N u allowance. The blanket 2e-11 had covered them. They
are now strict library-side xfails: 6 in all, previously 4.

**Files.**
- `lfphys/tests/external/test_ext_mie_miepython.py`
- `make_results.py` (basis texts)
- `README.md` (the Mie row)
- `RESULTS.md` (regenerated in `light-funnel-ext`; 2961 rows, problems 0; miepython 320 pass and 6 xfail)

## M9 — the 40-digit references not exact when |mx| ≫ N — **fixed** [error in earlier]

**Fix.** Both references (`test_mie._ref_mp_recurrence` and the external `_exact`) now start D at
N + |mx| + 20|mx|^{1/3} + 60. Over 20|z|^{1/3} orders the start's error decays by ~e^{-150}.

**Verification.** In `test_start_of_D_by_hankel_sums_and_continued_fraction`, at m = 1e5 and x = 0.5:
- the corrected reference agrees with the Bessel-function reference to 1e-15;
- the old start's D_N is off by more than 1e-6 (negative control).

## M10 — the Hankel-sum start and `log_psi` without direct tests — **fixed**

**Fix.** Two new tests against Bessel-function references in mpmath, with no recurrence:
- `test_start_of_D_by_hankel_sums_and_continued_fraction`:
  - the four Hankel cases of s14 and two continued-fraction cases with 178–264 oscillatory steps;
  - every order within the stated bound, using a sensitivity of 4N;
  - the branch taken is asserted.
- `test_log_psi_against_bessel_functions`:
  - real and complex z, including orders where ψ_n is ~1e-300 or below;
  - within 64 N u (1 + |log ψ|);
  - negative control: the double-precision ψ underflows there.

## M11 — v17 texts and labels — **fixed** [error in earlier]

- **The fixed bow angles.** The sky text's "≈ 138°, ≈ 129°" is replaced by the run's Descartes angles at the display
  wavelength, or "лучевой радуги у этой капли нет".
- **The legend.** It now says that only p = 0–3 are drawn and the rest is the remainder. It has separate texts for
  divergence and for cancellation (M5).
- **The rays for m ≤ 1.** The drop's own rays are drawn instead of those of m = 1.333. The rays of p ≥ 1 have b < m;
  `rainbow.ray_path` now refuses b ≥ m for p ≥ 1 instead of producing NaN, and the label says so.
- **The information checks.** `bow2`, `bow3`, `alexander`, `sky_sum` and `sky_bow` carry no tolerance, and their notes
  give the difference in degrees.

**Files.** `web/view.js`, `viz.py`, `engine/drops.py`, `lfphys/lfphys/theories/approx/rainbow.py`.

**Verification.**
- `test_info_checks_carry_no_misleading_tolerance_and_rays_for_m_below_1`
- `test_ray_paths_for_m_below_1` (the exit direction equals the deviation for m = 0.75; refusal for b ≥ m)
- The browser key-frame check

## M12 — physics in the visualization's code — **fixed**

**Fix.** Three new engine functions, which v17 now calls:
- `mie.intensity_polarised(I1, I2, phi, along)`, the B&H far field for x-, y- or un-polarised incident light. It is
  used by `drops.polar_mesh`.
- `mie.polarisation_from_intensities`, for P from the bin means.
- `mie.phase_function_from_intensities`, for the phase function from the bin means. `mie.phase_function` now uses it.

**Verification.**
- `test_polarised_far_intensity_against_the_near_field`: (kr)²|E_s|² of `near_field` at kr = 5e6 is within N²/kr.
  Negative control: I1 and I2 exchanged.
- `test_mueller_identities`: P from the intensities equals mueller's P.
- `test_the_polar_surface_uses_the_engine_intensity`.

## M13 — small doc slips — **fixed** [error in earlier]

- **`water_index`.** The docstring now quotes SR6-08 §2.3: the liquid above ~372.76 K at 0.1 MPa is metastable, and "No
  uncertainty estimate is given for the metastable regions". The text was fetched from iapws.org again and grepped.
- **`internal_coefficients`.** The docstring now says the function returns (c_n, d_n).

**Files.** `lfphys/lfphys/core/data.py` (water block), `mie.py`, the verification record §5.

## M14 — one place for problems; coarse sampling only a text line — **fixed** (v17); STATUS text → integrator

- **STATUS.** When this processing started, STATUS had V43 (v)–(z) for Mie and V44 (l)–(m) for v17. The reviewer's
  grep found nothing, so the rows were probably added while the review was being written (STATUS was last changed at
  18:49, the review at 18:51); this was not checked further. The integrator updates these rows with the text below,
  which also records the residuals of M1, M4, M6 and M7.
- **Coarse sampling** is now a header approximation of v17, for example big_drops: "грубая выборка размеров … шаг по x
  до 2,5 …". It also appears in the `sky_sum` note and the sky text.

**Verification.** `test_the_medium_cut_and_coarse_sampling_are_stated`: big_drops has the approximation; the rainbow
preset does not.

## Found while processing

| id | what | state |
|---|---|---|
| P1 | The Debye route lost up to 5e-9 of the largest coefficient at single orders, at the poles of D_n (M4) | fixed [error in earlier] |
| P2 | The honest engine budget exposes miepython's 3.7–4.2e-13 error at x = 100: two more strict xfails (M8) | fixed |
| P3 | `fejer2`'s plain sine sum had weight errors of up to 418 u near μ = −1 (large arguments) | fixed: integer argument reduction, ≤ 48 u |
| P4 | `ray_path` produced NaN (a warning) for p ≥ 1 with b ≥ m < 1; v17 now draws such drops | fixed: a ValueError, and v17 draws only b < m |

**A cost to know about [weakens].** With the ±4σ cut the rainbow preset's sky takes ~0.66 s per wavelength against the
0.5 s schedule; it was ~0.45 s. The run lags slightly, and the player shows it. big_drops takes ~2.7 s per wavelength.

---

## Changes for the integrator

### 1. `engine/STATUS.md`, row V43 (the Mie part)

In the description column, replace

> **Mie** (`core.optics.mie*`, `theories.approx.rainbow`): (v) no coated sphere; (w) Gauss–Legendre quadrature of the forward peak deviates 1e-9–1e-8 for N > 150 (numpy's and scipy's nodes alike; cause unknown; v17 checks energy by Re a_n = |a_n|² there); (x) the coefficient bound 2e-11 is measured, not derived (resonance conditioning); (y) the size average samples narrow resonances rather than resolving them, and its error is an estimate; above 1200 nodes per wavelength the ripple aliases; (z) not fetched: Bohren & Huffman, Hovenac & Lock 1992, Lentz 1976, Airy 1838, van de Hulst (the formulas checked by independent routes); Wiscombe's report only through the Internet Archive

with

> **Mie** (`core.optics.mie*`, `theories.approx.rainbow`): (v) no coated sphere; (w) closed 2026-11-04 (review B8-mie M2): the cause was numpy's and scipy's Gauss–Legendre weights near μ = ±1 (their formula at the rounded node, sensitivity ~n³u); angular integrals now by Fejér's second rule (`mie.fejer2`, `mie.angular_integrals`) with a derived rounding bound, v17's quadrature check restored up to N = 3000; (x) the accuracy bounds are mixed forward–backward with measured constants, not derived from a rounding analysis: coefficients u(4N max|a| + 8x|da_n/dx|) (measured F ≤ 1, K ≤ 4 over 22 cases and 5 resonance peaks; review B8-mie M1), the Debye sum against Mie u(1000N + 32 x|da_n/dx|/max|a|) (floor measured ≤ 453 N u over 281 cases; M4), the run's sensitivity a central difference with relative step 2⁻⁴⁶; (y) the size average samples narrow resonances rather than resolving them; at θ ≳ 170° the ripple (period ~0.27 in x) is not resolved at dx = 0.25 and the sum relies on the weight's smoothness; its error is an order-of-magnitude estimate (the largest over angles), not a bound; the ±4σ cut's bias (≤ 2–3 × the cut probability, reported) is measured, not included in it; above 1600 nodes per wavelength the ripple aliases (a header approximation in v17); (z) not fetched: Bohren & Huffman, Hovenac & Lock 1992 (the NASA report CR-187191 version read: Appendix A), Lentz 1976, Airy 1838, van de Hulst, Ciddor 1996 (the formulas checked by independent routes); Wiscombe's report only through the Internet Archive

In the plan column, replace

> (w) the cause found (nodes and weights in mpmath) and the quadrature check restored; (x) a per-order conditioning bound with a test;

with

> (w) — (closed); (x) a rounding analysis of the recurrences and of the Debye route's logarithmic sums giving F and K;

### 2. `engine/STATUS.md`, row V44 (the v17 part)

In the description column, replace

> (l) the Sun's angular size (0.53°) is not convolved; sunlight is a black body at 5772 K; water has no absorption; the default medium is vacuum; (m) `big_drops` is slow (≈ 3.8 s per wavelength against a 0.5 s schedule)

with

> (l) the Sun's angular size (0.53°) is not convolved; sunlight is a black body at 5772 K; water has no absorption; the default medium is vacuum (stated in the header since review B8-mie M6: in air the bows of water move by −0.054° (p = 2) and +0.096° (p = 3) for an illustrative n_air − 1 = 2.77e-4; Ciddor 1996 not obtained); (m) `big_drops` is slow (≈ 2.7 s per wavelength against a 0.5 s schedule; coarse at every wavelength, stated in the header) and since the ±4σ cut (review B8-mie M7) the `rainbow` preset takes ≈ 0.66 s per wavelength

In the plan column, replace

> (l) a solar-disc convolution, a licence-checked solar spectrum, κ(λ) of water and the index of air (Ciddor 1996) in `core.data`;

with

> (l) a solar-disc convolution, a licence-checked solar spectrum, κ(λ) of water and a sourced index of air (Ciddor 1996) in `core.data`, with air as v17's default medium;

### 3. `engine/lfphys/README.md`, "Light and optics"

Replace the four rows as follows.

`core.optics.mie`: replace

> ; tested bound 2e-11 of the largest coefficient (≤ 3e-13 away from narrow resonances) from x = 1e-6 to 2e4; Wiscombe's NCAR/TN-140 test cases in every printed digit; miepython 3.3 (326 rows, `tests/external`) |

with

> ; backward stable in x, the coefficients within u(4N max|a| + 8x|da_n/dx|) of exact (tested over all orders from x = 1e-3 to 1e4 and on resonance peaks, where the forward error reaches 6e-3 by the problem's conditioning), used from x = 1e-6 to 2e4; Q_sca and g by quadrature over the angles (Fejér's second rule) with a derived rounding bound; the far-field intensity for polarised light; a self-test against Wiscombe's published values; Wiscombe's NCAR/TN-140 test cases in every printed digit; miepython 3.3 (326 rows, 6 library-side xfails, `tests/external`) |

`core.optics.mie_debye`: replace

> the terms p = 0..P and the closed-form remainder; the sum equals the series to ~1e-12 (x ≤ 1000), 1e-10 (x = 1e4) |

with

> the terms p = 0..P and the closed-form remainder, the orders where the series diverges (|R11| > 1: absorbing m near 1) and the terms' amplification; the sum equals the series within u(1000N + 32 x|da_n/dx|/max|a|) (`check_against_mie`; ~1e-12 at x = 1000, up to 1e-9 at 2e4 for m < 1) |

`core.optics.mie_poly`: replace

> ⟨dσ/dΩ⟩(θ), its polarised part, ⟨C_sca⟩, ⟨C_ext⟩, with the half-sum error estimate |

with

> ⟨dσ/dΩ⟩(θ), its polarised part, ⟨C_sca⟩, ⟨C_ext⟩, with the half-sum error estimate (an order-of-magnitude estimate of the largest error over the angles); the distribution cut at ±4σ, the cut-off probability reported |

`theories.approx.rainbow`: replace

> Fresnel energy of the rays, ray paths)

with

> Fresnel energy of the rays, ray paths, also for m < 1 where only b < m enters)

### 4. `engine/visualizations/README.md` (owner guide), the v17 row

In the first cell, after «глория у антисолнечной точки», add:

> ; проверки: значения коэффициентов — второй путь счёта (ряд Дебая) и опубликованные значения Уискомба, тождества формы ряда (оптическая теорема в форме ряда, энергия, матрица Мюллера) помечены как тождества; если ряд Дебая расходится (слабо поглощающая капля с m ≈ 1), об этом сообщается

### 5. `engine/reviews/README.md` and the archive

After the STATUS update, move this folder to `reviews/archive/2026-11-04_internal_B8-mie/` and add this registry row:

> | `archive/2026-11-04_internal_B8-mie/` | internal (Opus subagent) | batch B8: the exact Mie series (P1: `core.optics.mie`, `mie_debye`, `mie_poly`, `theories.approx.rainbow`, the water and Sun data, the miepython rows) and `v17_mie_scattering` (P14.8), 22 scripts | 2026-11-04 | `RESPONSE.md` (processed 2026-11-04: 13 of 14 fixed, M6 partly (vacuum stated; an air index → STATUS V44 l) — the coefficient bound 2e-11 failed on resonance peaks (6.4e-3 at Γ = 1.5e-11), restated as backward stability in x with a conditioning-aware bound [error in earlier]; v17's energy check failed on a correct engine for 37 ≲ x ≲ 112 because of numpy's Gauss–Legendre weights near μ = ±1 (now Fejér's rule with a derived bound) [error in earlier]; theorem, energy and mueller relabelled as identities, the coefficients checked by the Debye route and a Wiscombe self-test, every check with a negative control; the Debye tolerance derived per order, and the route's loss at the poles of D_n fixed (found while processing) [error in earlier]; a diverging Debye series flagged and announced; the ±4σ cut, err's meaning and the ripple stated [error in earlier]; miepython's errors per order (2 more xfails); references started far enough above \|mx\|) |
