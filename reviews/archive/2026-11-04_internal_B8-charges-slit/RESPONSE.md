# Response to review B8 / P1: moving charges, vector slit diffraction and v02's vector mode

Processed 2026-11-04 by a subagent that wrote neither the review nor the code under review. **16 of 16 fixed**
(C12 by the review's second option: the relation is named and tested, the functions stay in the core; C11's optional
rewrite of `lienard_power` not done — β enters as a float, the loss is stated and tested). Nothing deferred; the
STATUS and README texts that change are in the last section, for the integrator.

Environment: Docker image `light-funnel-viz`, CPU, `LFPHYS_NO_GPU=1`. The processing's own scripts and outputs are in
the session scratchpad (`…/scratchpad/b8/proc_charges/`), not here; the numbers below are copied from them. Where a fix
changed what a reviewer script calls, a copy was run from there (`c04`, `s06`, `v01`, `b01`); the scripts here are
unchanged. The reviewer scripts `c01`–`c05`, `s01`, `s03`, `s05` were re-run against the fixed code as they are.

## Findings

### C1 — `retarded_time` returned times beyond the horizon of hyperbolic motion — **fixed** [error in earlier]

* **Cause confirmed.** Reproduced with `c05`: 56/57/59 of 60 points at 1 m / 0.1 m / 1 mm beyond got a time; 2.8e-2 and
  100 % errors 1e-6 m and 1e-9 m inside. At the "root" the former solver returned for the point 1 m beyond the horizon
  on the axis (τ = 5.813385e7 s) the computed g is 0 while its rounding bound is 35 m: the sign change was rounding.
* **Fix** (`lfphys/lfphys/core/em/charges.py`):
  * g = cτ − R carries its rounding bound B = 4ε(c|τ| + |x| + |r|) + ε|v||t′| (the review's form, plus the rounding
    of t′ = t − τ); a bracket is accepted only where g > B; where g stays within B and a doubling of the bracket
    cannot lift it out (g′·(τ_hi − τ_lo) ≤ 2B), the point is refused ("no retarded time resolved … beyond a horizon,
    or within the rounding of one").
  * `hyperbolic` returns a `HyperbolicWorldline` with the closed-form retarded time (the quadratic in e^η, derived in
    the module docstring; it exists iff Z′ + c(t − t0) > 0, which is known to 2ε(|Z| + c²/g + c|t|)); `retarded_time`
    uses it (`closed_form=False` forces the general solver), polished by Newton steps where g exceeds its rounding (a
    weakly accelerated charge). The worldline's position is now written without the cancellation of √(1+w²) − 1.
  * `retarded_time(..., full=True)` returns the error bound with the time.
* **Verification.** `tests/test_em_charges.py::test_hyperbolic_retarded_time_near_the_horizon` (two field times, three
  transverse offsets, seven depths 1 m … 1e-9 m inside, against a 50-digit bisection in the rapidity: the closed form
  within its bound at every depth, the bound itself ≤ (1e-13/depth + 1e-12) of the delay; the general solver solves
  every depth ≥ 1e-3 m and is either within its bound or refuses below; 60 random points at six depths 1e-9 … 10 m
  beyond: both refuse all; negative control: the former fake root). `c05` re-run: 0 of 60 at every depth; inside on
  the axis the error is 0 (rel.) at 1 m … 1e-6 m; `c02 C`: ≤ 7e-16 down to 1e-9 m, all five points at or beyond
  refused.

### C2 — `FunctionWorldline` from positions only: default step 1e-3 s, silently 100 % wrong — **fixed** [error in earlier]

* Reproduced (`c04`): |Δv|/|v| = |Δa|/|a| = 1.00, field 130 % off.
* **Fix** (`charges.py`): a step is required when v or a is missing — `h` (s) or `timescale` T, which gives
  h_v = (45ε/4)^{1/5} T and h_a = (256ε)^{1/6} T (truncation and rounding balanced; derivation in the docstring);
  `derivative_errors(t)` per time: 2|D(h) − D(2h)|/15 plus the rounding 1.5 e_r/h (v), 5.7 e_r/h² (a) with
  e_r = 2ε(|r| + |v||t|); `fields` refuses the worldline where these would change the field by more than its `rtol`
  (1e-6; the sensitivity of both parts to δv and δa is written in `_check_derivatives`). The docstring says that a step
  comparable with the motion's time scale aliases it and no estimate from the samples can see that.
* **Verification.** `test_positions_only_worldline_needs_a_step_and_reports_its_error`: no step refused; with the time
  scale and with h = 1e-12 s the estimate covers the true errors (≤ 100× them) and the field is within 1e-8 (measured
  1.1e-11 and 5.6e-9); negative control: h = T/10 (v off by 3e-6) is estimated (≥ 0.9 of the true error) and refused
  by `fields`, and so is t = 1 s (argument rounding). The copy of `c04` (h = None now refused): with the time scale v
  is good to 8.8e-14 and the field to 1.1e-11; at h = 1e-12 s the estimate of a is 3.3e9 m/s² against the true ~1e8
  (the review: 6e6, below the truth).

### C3 — v02's vector expectation left out the detector efficiency — **fixed** [error in earlier]

* Reproduced through the new test's negative control (the curve without the efficiency is rejected) and the review's
  `v01` (copy, part 2): with eff = 0.2 and 300 dark counts/s the run's curve now gives p = 0.49 (was 0.0).
* **Fix** (`visualizations/v02_double_slit/viz.py`, `_vector_curves`): 'all', 'kir', 'vTE', 'vTM' are multiplied by
  the efficiency before the dark counts are added; 'diff' is the signal difference.
* **Verification.** `test_vector_mode_detector_efficiency_and_dark_counts_in_the_expectation` (60 000 photons, dark
  counts > detections): the run's curve p > 1e-4; negative control: the curve without the efficiency p < 1e-8;
  vTE + vTM = the signal of 'all' to 1e-12. Browser (`b01` copy): the orange curve now lies on the dark floor.

### C4 — "no convergence" far from the origin aborted vectorised calls; "large t lose no digits" — **fixed** [error in earlier]

* Reproduced (`c03b`): point 159 of 400 never converged.
* **Fix** (`charges.py`): the iteration stops at |g| ≤ B or a bracket at ulp(t), then takes one more Newton step if it
  stays in the bracket (the root goes from within B/g′ to the actual rounding; the returned bound is 2B/g′); refused points are
  listed with their reason (`on_fail='raise'`, ValueError) or get NaN (`on_fail='nan'`, also in `fields` and
  `potentials`), never aborting the others silently. The docstring now says what holds: the delay is resolved to B/g′,
  positions carry |v|·ulp(t′).
* **Verification.** `test_far_from_the_origin_every_point_converges_within_its_bound` (the review's 400 points at t =
  1 s, β = 0.99, against the 50-digit quadratic of uniform motion: all within their bound; max error 1.3e-14 s, bound ≤
  4e-13 s; field against Heaviside 1.2e-6, the review's γ²ε loss); `test_one_point_does_not_abort_the_others`.
  `c03b` re-run: 0 of 400 fail; `c01`: at t = 1 s the field now agrees with Heaviside to 3.6e-7 / 1.1e-6 (it raised).

### C5 — sampled worldlines refused retarded times inside their domain — **fixed** [error in earlier]

* Reproduced (`c02 D`).
* **Fix** (`charges.py`): the bracket is clamped to [max(0, t − t_max), t − t_min] and g is evaluated at the clamp; only
  g(t − t_min) < −B refuses ("before the domain"); a field time after the domain's end is served when the retarded
  time is inside.
* **Verification.** `test_sampled_worldline_retarded_time_inside_the_domain` (the review's two points, one at 9 ns, one
  at t = 12 ns after the samples; agreement with the formula worldline to 1e-20 s; two points before the samples
  refused). `c02 D` re-run: both points solved, 1.5771e-9 s and 1.1726e-9 s.

### C6 — the convergence shown by v02 understated the error 3–6×; documented orders wrong — **fixed** [error in earlier]

* Reproduced (own script, Richardson limits from 2, 4, 8 × the default count): the same digits as the review's `s02`
  (vector_narrow TE 1.05651704, TM 0.97420636; the test slit TE 0.85812062, TM 0.98232870); orders 1.23–1.36 for six
  thick geometries; true error at the default count 0.04–0.19 %.
* **Fix.**
  * Engine (`lfphys/lfphys/core/em/slit.py`): `SlitSolution.truncated(M′)` solves the sub-blocks of the same operator
    (no new quadrature; equal to a fresh solve with M′ modes to 1e-12) and `error_estimate()` gives the estimated error
    of T, the far-field pattern and any quantity of the caller: edge basis — the change from M − max(4, M/8) to M;
    waveguide modes — Richardson from M/2, M/√2, M with the observed order clamped to [0.5, 1] (0.5 for a thin screen).
    Measured 1.4–3.1× above the true error (six thick geometries), 1.2–1.9× (thin screen, k w = 60 and 100). The
    docstring of `solve` and ABOUT's validity give the measured orders and errors [error in earlier: "~M^-1.4 for TE"].
  * v02: the check `vconv` shows the estimate (max of T and the flux on 201 screen points), labelled as an estimate,
    with the tolerance derived from the display, 4e-3 (below one pixel of the ≈ 200-px curve, and below what χ² can see
    before ~3·10⁶ detections); where the waveguide modes' estimate exceeds it the run solves once more with twice the
    modes (the preset: TM 26 → 52; at the cap with t = 0.2 µm: TM 66 → 132). No second "convergence" solve any more.
  * README: the corrected numbers [error in earlier: "0.2 % TM, 0.03 % TE" held for the test slit only].
* **Verification.** `test_em_slit.py::test_truncated_solution_is_a_fresh_solve_with_fewer_modes`,
  `::test_error_estimate_bounds_the_true_truncation_error` (true < estimate < 4 × true; negative control: the former
  T(1.25 M)/T(M) − 1 < true/3); v02 `test_vector_mode_error_estimate_bounds_the_truncation_error` (the preset against
  its Richardson limits; the check passes and says "Ричардсона").

### C7 — thin screens with k a > 40 went to the waveguide modes (0.2–0.5 %) — **fixed** [error in earlier]

* Reproduced with the waveguide modes forced at k w = 60 and 100: −3.6e-3/−3.3e-3 and −2.1e-3/−2.5e-3 (TE/TM) against
  the edge basis.
* **Fix** (`slit.py`): `auto` takes the edge basis for t = 0 up to `EDGE_KW_MAX` = 140 (above v02's cap 130; default
  functions k w/2 + 10, at most 90); identical operator blocks (equal slits, equal offsets) are computed once, for the
  edge basis too — at the cap (two slits, k a = 129) 5.4 s (TE) and 3.3 s (TM) against the review's 10.7 and 6.4 s;
  T unchanged to 4e-9 / 4e-11 from 75 to 95 functions (`s05` re-run). v02 draws the difference strip only where it
  exceeds three times the method's estimated error on the screen, and says so otherwise. The README's table was
  recomputed: rows 0.3–4 µm reproduce to the printed digits; the 8 µm row is now T_TE 1.002, T_TM 1.000, differences
  0.004 / 0.0007 / 0.003 [error in earlier: 0.999, 0.997 and the TM difference 0.006 were the method's error].
* **Verification.** `test_thin_screen_uses_the_edge_basis_up_to_kw_140` (edge at k w = 60, modal at 141, edge estimate
  < 1e-5; negative control: the waveguide modes there > 2e-3 off, and their estimate says so); v02
  `test_vector_and_scalar_curves_approach_each_other_for_wide_slits` (at 8 µm the edge basis, its error < 0.1 of the
  difference).

### C8 — with scalar hits, the "vector" curve and the difference were dominated by normalisation — **fixed** [error in earlier]

* The review's numbers (zero-phase element, eff 0.5: Σ vec 0.95 against Σ all 0.48, "difference" 0.96 of the curve)
  follow from the former code's normalisation (per particle on the open width, no efficiency), read in the code.
* **Fix** (`viz.py`, `web/view.js`, README): the review's first option — 'vec' is the shape of the vector flux for the
  same slits without the elements, scaled to the same total as 'all', labelled a shape comparison (unit "shape"); no
  'diff' and no red strip then. The approximations, the caption and the README say so.
* **Verification.** `test_vector_curve_with_scalar_hits_is_a_shape_comparison` (equal totals to 1e-12, no 'diff', the
  shape equals the vector-hit world's curve to 1e-12); the eraser test now asserts no 'diff'. Browser: the caption reads
  "синяя — только форма … разность не показывается".

### C9 — v02 re-solved the conductor on every source or detector change — **fixed**

* Reproduced in kind (each such change rebuilt `exp.vec`).
* **Fix** (`viz.py`): the TE/TM solutions are cached by (k, slits, a, t) and the screen fluxes by those plus (L₂, the
  screen grid), in the world's state (so checkpoints and replays see the same); the polarisation weights are applied
  per segment as before. A refused change leaves the cache as it was.
* **Verification.** `test_vector_solution_is_not_solved_again_for_the_source_or_the_detector` (`solve` counted: eff,
  dark rate, polarisation V and H, screen distance — no new solve; thickness — solved again). Timing (own script): eff,
  polarisation 0.4 s; screen distance 1.5 s (preset) to 4–6 s (cap); first build 3 s (preset), 17 s (cap, t = 0), 21 s
  (cap, t = 0.2 µm, TM doubled for C6). Checkpoint, restore and browser key frames for v02 and v02_vector pass.

### C10 — Kirchhoff re-implemented inside the core `core.em.slit` — **fixed**

* **Fix.** `kirchhoff_spectrum/far_field/transmission/field`, `compare_kirchhoff`, `transmission_vs_width` moved to
  `lfphys/lfphys/theories/approx/kirchhoff.py` as `plane_wave_spectrum/far_field/transmission/field`,
  `compare_vector`, `transmission_vs_width` (they reuse the core's quadrature helpers; the approx module may import
  the core). Its passport: validity names `core.em.slit` (no more "(нужна векторная теория)"), and a conflict
  "lfphys.core.em.slit: векторное решение экрана-проводника …". The core's docstring, statement and `__all__` lost
  them; v02 imports them from the approx module. v11 and v12 use only `slit_fields`, unchanged.
* **Verification.** `test_em_slit.py::test_the_approximation_lives_outside_the_core`, `::test_kirchhoff_routes_agree`
  (now also the far field against the field at k r = 2e4 and the transmission against the flux through a line),
  `::test_comparison_with_kirchhoff_for_v02`; `test_layers.py`, `test_boundary.py`, `test_schrodinger_nd.py`, v11's
  tests (21 passed) pass. The player's passport line now reads the new validity (browser).

### C11 — double precision loses ~γ²ε; the validity did not say so — **fixed**

* **Fix** (`charges.py`): ABOUT's validity states "~1e-16·γ² (measured ~4e-8 at γ = 1e4, ~1e-4 at γ = 1e6, ~1e-2 at
  γ = 1e7)" and the accuracy of the retarded time; `fields`' docstring too. The optional γ⁴|β̇|² route for
  `lienard_power` is not added: the worldline delivers β as a float, so the loss is in the input; stated instead.
* **Verification.** `test_double_precision_loses_gamma_squared_eps` (uniform motion against a 50-digit Heaviside field
  of the same float inputs: γ = 1e2 < 1e-11, 1e4 and 1e6 below 100·ε·γ²; negative control: at γ = 1e6 the error is
  above 1e-8 — the loss is real). `c01` re-run: the review's table reproduced to γ = 1e6; at γ = 1e7 (delays up to
  2γ²R/c = 7e5 s straight ahead) the fields are computed with 1.5–3.8 % error (the review: 0.9–7.6 %), consistent with
  ~1e-16·γ²; from γ ≈ 2e7 such points (straight ahead and abeam at 1 m) are refused, the delay being no longer
  resolved (at γ = 1e7 the returned bound is already 0.3–0.8 of it). (A first, more conservative bound, 8ε(…),
  refused them from γ = 1e7; it was tightened to the review's form.)

### C12 — layering of the synchrotron F/G spectrum; ω_c "halves" — **fixed** (the review's second option)

* **Fix** (`charges.py`): ABOUT's `conflicts` names the relation: the F/G functions are the γ ≫ 1 limit of Schott's
  harmonics in the same module, exact at any β, with the measured difference; the module docstring says so;
  `critical_frequency` says "nominally" with 0.5000052565. The functions stay in the core: the synchrotron formula is
  the accepted standard form with its stated domain, and the module holds the exact form next to it.
* **Verification.** New `test_synchrotron_spectrum_is_the_large_gamma_limit_of_schotts_harmonics`: P_m/ω0 against the
  F-spectrum at ω/ω_c = 0.3, 1, 3 falls by 4.0 ± 5 % from γ = 10 to 20 (O(1/γ²): +4.0e-3 → +1.0e-3 at ω_c); negative
  control: at γ = 10, ω = 3ω_c it is still 1.7e-2 off.

### C13 — Libelo & Bombardt: quote, printed formulas, fragile test — **fixed** [error in earlier]

* Verified on a fresh download of NOLTR 70-58 (a scan without text layer; rendered PDF pages 33 and 39):
  (a) the sentence is exactly "However, the higher order approximation indicates about 3% difference from the other
  results and this is not terribly significant, having as its source the numerical techniques used in the computer
  program." — a difference from Skavlem and Seshadri, not a stated accuracy; (b) their (130) prints ¼ηΣ|a_n|², (131)
  σ_t ≈ (ηρ0/2)|a1|², |a1|² = π²η²/16, (132) σ_t ≈ ρ0π²η³/32 = ρ0π²(2kρ0)³/256, i.e. T → π²(kw)³/512, half the
  correct limit; the table uses ½ (η = 0.80: Σ|a_n|² 0.7307, T 0.2923).
* `s03` (the review's independent FDFD) re-run: identical output.
* **Fix.** `lfphys/sources/verification_2026-11-04_p1_charges_slit.md` quotes the sentence exactly, records the factor
  ½ of (130)–(132) and the FDFD values. The test is now
  `test_thin_slit_against_an_independent_fdfd_and_the_libelo_bombardt_table`: the FDFD levels (N = 8…64) extrapolated
  in the test, tolerance 1.5 × (order-p − order-1 extrapolation) + 3e-5 (printed digits): engine within 0.42–0.44 of
  it for TE (−0.09 … +0.03 %) and within 0.08 for TM (1e-6 rel.); the table kept as a known-high reference: 1.5–12.2 %
  above the engine at all eight η, and > 9 % above the FDFD at η ≤ 1 (negative control).

### C14 — the peak height λ/(πw) attributed to Takakura — **fixed** [error in earlier]

* Verified: Auckland & Harrington, RADC-TR-79-257, printed p. 116 (PDF page 132 of the archive.org scan, rendered;
  text layer "l/w7r"): "These peaks approach a value of 1/wπ for small w which can be shown from the equivalent
  circuit." Holley & Schnitzer (arXiv:1812.06753v2, grep): (12) "Fabry–Pérot frequencies Ω̄ = mπ", (32) "η ≈ h−1
  Ω̄|A|2", (33) |A|² = (πm)⁻²/[…] → η = 1/(πmh) = λ/(πw). Takakura's abstract (OpenAlex, re-fetched): "very low
  magnitude".
* **Fix.** The test's docstring attributes the height to Harrington & Auckland and Holley & Schnitzer and keeps
  Takakura for the shift through H–S (35); the sources file says so.

### C15 — v02 UI and documentation details — **fixed**

* The width limit is announced in advance: the select reads "идеальный проводник: векторная дифракция (щели до
  20.7 λ)", its help gives k·a ≤ 130 and why the default 20 µm (31.6 λ) is refused, the scalar panel says it too; the
  refusal says "шире 20.7 λ"; the README "up to 20.7 λ" — one number. Test:
  `test_vector_mode_announces_its_width_limit_with_one_number`.
* n = 1: the strip W = d is stated as a convention (run's approximations, panel, README).
* χ² of the preset over seeds: 1–5 give p = 0.33, 0.006, 0.67, 0.44, 0.10 (Kirchhoff ≤ 5e-7). Over 40 seeds the median
  is 0.33 and 15 % lie below 0.05 (10 % without the TM doubling): Pearson's χ² with ~120 bins, 46 expecting 5–10
  counts, is mildly anti-conservative at ~5 000 detections; at 300 000 photons p = 0.62, 0.39, 0.76 — no systematic
  mismatch [neutral]. The README says this [error in earlier: one seed, "p = 0.52"].
* The first build: 3 s for the preset, 17 s / 21 s at the cap (README, the comment at `VEC_KA_MAX`) [error in earlier:
  "~10 s"].

### C16 — source record and test naming — **fixed**

* (a) Fitzpatrick (12.335): the prime of "dt′" checked on the rendered page 300 (the text layer drops it); said in the
  sources file. (b) The test is now `test_large_times_resolve_the_delay_to_the_rounding_of_g` and asserts |g| ≤ B, the
  bound ≥ ulp(t) and the centimetre position uncertainty at t = 1e6 s. (c) The Qi et al. comparison is kept as a third
  published modal computation; the test comment and the sources file say that at 5e-3 it tests only the slope 1/π.

## Final test runs

* `lfphys`: `tests/test_em_charges.py tests/test_em_slit.py tests/test_boundary.py tests/test_layers.py
  tests/test_licences.py tests/test_schrodinger_nd.py` — see the last line below.
* `visualizations`: `v02_double_slit/tests` (85), `tests/test_checkpoint.py tests/test_restore.py -k v02`;
  `v11_double_slit_2d/tests` (21 passed, 1 skipped).
* Browser key frames on a private server (port 8543): `v02_double_slit` and `v02_vector` — all equal.

Results of the last runs (after every edit):

* `lfphys` (the six files above): **339 passed, 2 skipped**;
* `visualizations` (`v02_double_slit/tests` and `tests/test_checkpoint.py tests/test_restore.py -k v02`): **88 passed**;
  `v11_double_slit_2d/tests`: **21 passed, 1 skipped** (after the move of the Kirchhoff functions; v11 was not touched
  afterwards);
* `keyframes.mjs 8543 v02_double_slit`: `v02_double_slit` 353 frames, `v02_vector` 325 frames, every step "same" — **all
  equal**; the private server and the Playwright containers stopped and removed.

## Changes for the integrator

Not edited by the processing (other agents' files). Each item: where, the present text, the new text.

**1. `engine/STATUS.md`, row V4 (closed), last column.** Replace

> closed 2026-11-04 (B8): v02 has a vector mode — a perfectly conducting screen of thickness t solved by `lfphys.core.em.slit` (modal method; an edge-conditioned basis for thin narrow slits), both polarisations; the hits are drawn from the vector solution's energy flux, the scalar Kirchhoff curve, their difference and the power balance next to it; the narrow-slit warning points to the vector mode; the scalar model stays the default. Its own limits: V44 (g)–(k)

by

> closed 2026-11-04 (B8; review `2026-11-04_internal_B8-charges-slit` processed the same day): v02 has a vector mode — a perfectly conducting screen of thickness t solved by `lfphys.core.em.slit` (an edge-conditioned basis for a thin screen up to k a = 140, the waveguide modes otherwise), both polarisations; the hits are drawn from the vector solution's energy flux; next to it the scalar Kirchhoff curve (`lfphys.theories.approx.kirchhoff`), their difference (only where it exceeds three times the method's estimated error), the power balance and the estimated error of the method; the narrow-slit warning points to the vector mode; the scalar model stays the default. Its own limits: V44 (g)–(k)

**2. `engine/STATUS.md`, row V43, second column (the problems), the part from "**Charges**" to "(u) …".** Replace

> **Charges** (`core.em.charges`): (n) no radiation reaction (the worldline is prescribed); (o) a `FunctionWorldline` without v and a differentiates numerically (an estimated error); (p) Jackson and the Feynman Lectures not fetched (Fitzpatrick's notes instead). **Slit** (`core.em.slit`): (q) the waveguide modes converge algebraically (~M^-1.3, the screen's corners): ≈ 0.2 % in T for TM at the default count; (r) no exact Mathieu-function reference for the thin slit (Morse–Rubenstein, Bouwkamp not fetched; Libelo & Bombardt's table lies 10–12 % above the engine at η ≤ 1, beyond their stated 3 %, while two independent routes agree with the engine); (s) Takakura's PRL not fetched (his results checked through Holley & Schnitzer and Qi et al.); (t) 2-D only, in-plane incidence (no conical incidence, no finite slots); (u) a zero-thickness screen with k·w > 40 uses the waveguide modes (1/M convergence).

by

> **Charges** (`core.em.charges`): (n) no radiation reaction (the worldline is prescribed); (o) a `FunctionWorldline` given positions only differentiates numerically with the step or the time scale the caller gives (required since review B8 C2); its error estimate includes the rounding and `fields` refuses beyond the worldline's rtol, but a step that aliases the motion cannot be seen from the samples; the retarded time is resolved to the rounding of g = cτ − R, 4ε(cτ + |x| + |r|) + ε|v||t′| (the bound is returned), a general worldline is refused within that rounding of a horizon (hyperbolic motion has a closed form), and double precision costs ~1e-16·γ² in the fields (1.5–4 % at γ = 1e7; points ahead or abeam of a uniformly moving charge refused from γ ≈ 2e7); (p) Jackson and the Feynman Lectures not fetched (Fitzpatrick's notes instead). **Slit** (`core.em.slit`): (q) the waveguide modes (t > 0) converge algebraically (order 1.2–1.4, the screen's corners): T is 0.04–0.19 % low at the default count; `SlitSolution.error_estimate` (Richardson from sub-blocks) estimates it, 1.4–3.1 times above the true error; (r) no exact Mathieu-function reference for the thin slit (Morse–Rubenstein, Bouwkamp not fetched); the review's independent FDFD agrees with the engine within 0.09 % (TE) and 3e-6 (TM) at η = 0.8–2, while Libelo & Bombardt's table lies 1.5–12 % above both and their printed long-wave formulas (130)–(132) carry a factor ½; (s) Takakura's PRL not fetched (his shift checked through Holley & Schnitzer; the peak height λ/(πw) is Harrington & Auckland's and Holley & Schnitzer's); (t) 2-D only, in-plane incidence (no conical incidence, no finite slots); (u) a zero-thickness screen with k·w > 140 uses the waveguide modes (0.2–0.5 % low, estimated); up to 140 the edge basis costs ~(k w)² in its quadrature (≈ 3–5 s per polarisation at k w = 130 for two slits).

**3. `engine/STATUS.md`, row V43, third column (what would close it), items (o), (q), (u).** Replace "(o) analytic derivatives where given;" by "(o) analytic or automatic derivatives; extended precision for γ ≳ 1e6;", "(q) corner-singular basis functions or extrapolation in M;" by "(q) corner-singular basis functions (or T extrapolated in M);", and "(u) a cheaper edge-basis operator;" by "(u) a cheaper edge-basis operator (FFT-based or asymptotic kernel);".

**4. `engine/STATUS.md`, row V44, second column, the part "**v02 vector mode** …".** Replace

> **v02 vector mode** (closes V4; engine `core.em.slit`): (g) the hits stay scalar with which-path marks, elements, the analyzer or modified laws (labelled); (h) the near-field map and flow lines stay scalar paraxial (labelled); (i) photons only, a plane wave (L₁ = 0), monochromatic; (j) slits up to 20λ (the default geometry, a = 20 µm ≈ 31.6λ, is refused in vector mode); (k) a perfect conductor only.

by

> **v02 vector mode** (closes V4; engine `core.em.slit`): (g) the hits stay scalar with which-path marks, elements, the analyzer or modified laws (labelled; the vector curve is then a shape comparison without a difference strip, review B8 C8); (h) the near-field map and flow lines stay scalar paraxial (labelled); (i) photons only, a plane wave (L₁ = 0), monochromatic; (j) slits up to 20.7λ (k a ≤ 130, announced in the select's help and the panel; the default geometry, a = 20 µm ≈ 31.6λ, is refused in vector mode); setting the screen up costs ~3 s for the preset and ~17 s (thin) / ~21 s (thick) at the cap, once per wavelength, slits and thickness (a change of the source or the detector reuses it); (k) a perfect conductor only.

**5. `engine/lfphys/README.md`, "Electrodynamics", row `core.em.charges`.** Replace the row by

> | `core.em.charges` | core | (P1, B8) fields and radiation of moving point charges (SI): Liénard–Wiechert E, B (velocity and radiation parts) and potentials on any subluminal worldline (formulas, closed forms uniform/circular/harmonic/hyperbolic, or samples by quintic Hermite / quintic spline with a measured interpolation error; positions-only formulas differentiated with a given step or time scale, error estimated with the rounding, refused beyond rtol), the retarded time solved uniquely to the rounding of g = cτ − R with a returned bound (bracketed Newton on the delay; points with no resolved root — beyond a horizon or within its rounding, outside a sampled domain — refused and listed, or NaN; hyperbolic motion by its closed form); several charges; Heaviside's field; Larmor, Liénard, dP/dΩ per retarded and per observer time; synchrotron ω_c, F, G, spectrum and σ/π components, angular–spectral distribution (the γ ≫ 1 limit of Schott's harmonics, also here). Double precision: ~1e-16·γ². Tests: Coulomb 1e-14, Heaviside 1e-10 (β ≤ 0.9999), Maxwell by finite differences 1e-8, ∮dP/dΩ = Liénard 1e-10, light-cone sphere flux 2e-4, F vs mpmath 1e-13, spectrum = Liénard 1e-9, Schott sum 1e-9 and vs FFT of the computed field 1e-5, synchrotron = Schott as 1/γ²; retarded time against 50 digits near the horizon (closed form 1e-9 m inside) and 3e8 m from the origin, refusals beyond the horizon |

**6. `engine/lfphys/README.md`, "Electrodynamics", row `core.em.slit`.** Replace the row by

> | `core.em.slit` | core | (P1, B8) vector diffraction of a plane wave (any angle) by one or several slits in a perfectly conducting screen of thickness t ≥ 0, TE (E along) and TM (H along): modal method (waveguide modes, Galerkin, closed-form correlation route), edge-conditioned basis for thin screens up to k w = 140; fields everywhere, angular spectra, far field, transmission per slit width, power balance (screen's optical theorem), per-slit fields; the estimated truncation error from sub-blocks of the same operator (`truncated`, `error_estimate`); Rayleigh's narrow-slit limits; Sommerfeld's half-plane and its edge wave (the Kirchhoff comparison is in `theories.approx.kirchhoff`). Tests: optical theorem 1e-10, reciprocity 1e-9, Rayleigh limits 1e-3, TE cut-off slope 1e-6, TM resonance λ/(πw) and Harrington–Auckland circuit 1.5 %, Qi et al. 0.5 % (slope only), independent hat-basis Galerkin 1e-3, independent FDFD (review B8) 0.09 % TE / 3e-6 TM (Libelo–Bombardt's table 1.5–12 % high), half-plane Helmholtz/BCs; waveguide modes of order 1.2–1.4 (0.04–0.19 % at the default count), the error estimate 1.4–3.1 times above the true error |

**7. `engine/lfphys/README.md`, row `theories.approx.paraxial`, `paraxial_ensemble`, `kirchhoff`.** Replace its last cell "Fresnel diffraction by slits, expected ensemble patterns, Kirchhoff boundary values" by "Fresnel diffraction by slits, expected ensemble patterns, Kirchhoff boundary values (also the plane wave on slits against the vector solution of `core.em.slit`: `plane_wave_*`, `compare_vector`, `transmission_vs_width`; moved from the core, review B8 C10)".

**8. `engine/lfphys/README.md`, "Who uses it", row v02.** Replace "approx (paraxial, kirchhoff, paraxial_ensemble)" by "approx (paraxial, kirchhoff — also the Kirchhoff curve of the vector mode, paraxial_ensemble)".

**9. `engine/visualizations/README.md` (owner guide), row v02, second column.** Replace "экран со щелями — скалярная модель Кирхгофа (по умолчанию) или идеальный проводник заданной толщины: точная векторная дифракция для обеих поляризаций (TE — E вдоль щелей, TM — поперёк), попадания фотонов — по потоку энергии векторного решения, рядом скалярная кривая, разность и баланс мощности" by "экран со щелями — скалярная модель Кирхгофа (по умолчанию) или идеальный проводник заданной толщины (щели до 20.7 λ): векторная дифракция для обеих поляризаций (TE — E вдоль щелей, TM — поперёк), попадания фотонов — по потоку энергии векторного решения, рядом скалярная кривая, разность (если она больше оценки ошибки метода), баланс мощности и оценка ошибки метода".

**10. The review folder.** Move `reviews/2026-11-04_internal_B8-charges-slit/` to `reviews/archive/` and add to the registry of `reviews/README.md`:

> | `archive/2026-11-04_internal_B8-charges-slit/` | internal (subagent) | batch B8, P1: `core.em.charges`, `core.em.slit` and v02's vector mode, 15 scripts, an independent FDFD, sources quoted, browser checks | 2026-11-04 | `RESPONSE.md` (processed 2026-11-04: 16 of 16 fixed — retarded times returned beyond the horizon of hyperbolic motion and wrong just inside it [error in earlier], now a rounding-bounded bracket and the closed form; positions-only worldlines 100 % wrong at the default step [error in earlier], now a required step, a rounding term and refusal; v02's vector curves without the detector efficiency (χ² failed a correct run) [error in earlier]; non-convergence far from the origin; sampled domains; the shown convergence 3–6× low, now a sub-block Richardson estimate with a derived tolerance [error in earlier]; thin screens beyond k a = 40 on the waveguide modes, the README's 8 µm row [error in earlier]; the scalar-hit comparison now a shape; no re-solve on source or detector changes; Kirchhoff moved to `theories.approx`; γ²ε stated; synchrotron = Schott as 1/γ² tested; Libelo–Bombardt quote and factor ½, FDFD reference [error in earlier]; attributions) |
