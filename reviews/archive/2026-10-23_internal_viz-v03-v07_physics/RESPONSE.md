# Response to the internal physics review of v03, v05, v06, v07 (2026-10-23)

Processed by the coordinating session, which did not write the review. v03 and v06 were fixed by the coordinating
session (their author), v05 and v07 by a separate fixing agent (not the reviewer, not their author), whose detailed
notes are appended (Appendices A and B) and whose results were verified here. Every finding was reproduced first;
each fix has a test that fails with the reviewer's input on the old code.

| ID | summary | decision | where | verified by |
|---|---|---|---|---|
| V3-1 | step just below the energy: the run stopped with 46 % of the wave in the window (T 0.26 vs 0.60) | **fixed** [error in earlier]: the run integrates until the probability whose fate is still open is below 1e-3 T + 1e-9 and 1e-3 R + 1e-6, not for a fixed time; probability already beyond the potential and moving away from it (momentum spectrum under a smooth mask of the constant-potential region) is assigned to its detector instead of waited for; the time estimate uses the transmitted wave's own speed; the stored snapshots are thinned (uniform spacing) so a long run fits in memory | `v03_quantum_1d/viz.py` (`_evolve`, `_t_end`, `_fates`, `_leftover_allowed`) | `test_review_cases_converge_to_the_stationary_reference[step V0 0.75, E 0.8]`: T 0.598164 vs reference 0.598216 (9e-5; was 0.2585), 20 s |
| V3-2 | stop at norm < 1e-5 cut small transmissions by 55 %, hidden by the absolute tolerance | **fixed** [error in earlier]: the stop criterion above; the T check's tolerance is 1e-7 + 1e-3 T + the leftover + the detectors' reflection, so a factor-2 error fails | same | `[barrier 5 nm]`: T agrees with the reference 1.6e-6 within the new tolerance (was −55 % with ok) |
| V3-3 | low energies: the reference dropped k < 0; slow parts cut; detectors reflected 0.4–17 % | **fixed**: (a) the reference uses the whole Gaussian (k ≤ 0 reflected); (b) the adaptive end; (c) the detector ramp is chosen per set-up among (15 nm, 2 eV), (30, 2), (60, 0.5), (120, 0.5) by its stationary reflection averaged over the packet's spectrum (≤ 1e-6) and its leak (≤ 1e-8), computed with the engine's transfer matrices for a complex potential (new `return_r` of `transmission_profile`) and shown as a check; packets whose slow edge (k0 − 3/(2σ)) is below 0.01 eV, which no such ramp absorbs, are refused with the σ needed | `viz.py` (`_detector`, `_expected_T`, the `det` check), `lfphys/core/quantum/transfer.py` | `test_review_cases_…[free E 0.05, σ 2.5]` (T 1.000000 vs 1.000000, reflection 3e-8); `test_unreachable_set_ups_are_refused_with_the_reason` (E 0.05, σ 1 refused); the reviewer's 15 nm ramp numbers reproduced (R 4.0e-3 at 0.05 eV) before choosing |
| V3-4 | unbounded cost: live changes froze the world for minutes, the trap OOM-killed the worker, grids capped silently | **fixed** [error in earlier]: a set-up is planned before anything changes; a grid above 32768 points or an estimated cost above 6e8 point-steps (~25 s, measured 4e-8 s per point-step) is refused with the reason; the adaptive continuation stops at 1.2e9 and says so; the trap's levels come from a 256-point DVR window around the trap, not a dense whole-grid matrix | `viz.py` (`_build`, constants `N_GRID_MAX`, `COST_MAX`) | `test_unreachable_set_ups_are_refused_with_the_reason` (trap ħω 1 eV, x0 60 nm refused: grid), `test_heavy_trap_is_refused_and_levels_come_from_a_window` (ħω 0.05 eV, x0 60 nm refused with the estimate ≈ 150 s; levels to 1e-9); presets 0.5–9 s per world. Not done: building a new set-up in the background while the old one runs (a refused or accepted change is still computed synchronously, ≤ ~25 s): `STATUS.md` V15 |
| V3-5 | wording and drawing | **fixed**: the energy is "of the central component" (mean larger by ħ²/(8mσ²)); "numerical solution, converged as stated" instead of "exact"; Bohm "exactly" restricted to outside the detector ramps; "Electrons (or protons)" removed; the grey spectrum is the distribution per unit energy (w(k) dk/dE) and labelled so | `viz.py`, `web/view.js`, `README.md` | text |
| V5-1 | θ exactly at the critical angle: ZeroDivisionError inside a live change, world half-changed | **fixed** [error in earlier] (fixing agent): exact critical angle from the run's own T(θ) = 0 on adjacent floats; `set_live`/`action` atomic (messages held, the whole state restored on any exception); the runner now also reports *any* exception as a refused change (`server/lfviz/sim.py`, done by the coordinator) | Appendix A | `test_exact_critical_angle_is_accepted_and_every_check_holds`, `test_a_change_that_fails_inside_leaves_the_world_as_it_was`; reviewer's `07_v05_adversarial_angles.py` rerun (verification below) |
| V5-2 | `evan` and `film` checks ill-conditioned near critical / grazing angles | **fixed** (fixing agent): tolerances derived from the condition number; the reference q in 160-bit arithmetic; `single_film` and `airy` share the engine's cosines and return first-order error bounds; two further failures of the same kind found by the agent's fuzz (A1 `crit` confused by an opaque film, A2 `airy` just below grazing) fixed as well | Appendix A | the tests listed there; 3000–120 000-case fuzz runs without a failure |
| V5-3 | Joule check under-resolved a 1.2 nm skin depth | **fixed** (fixing agent): composite Gauss–Legendre adapted to the layer's fastest scale; tolerance 1e-8 → 1e-12 | Appendix A | `test_joule_heating_resolves_the_skin_depth`, `test_joule_check_resolves_a_one_nanometre_skin_depth`; reviewer's `12_v05_joule_and_rate.py` rerun |
| V5-4 | README said grazing angles are refused; the statistics check tested R only | **fixed** (fixing agent): README; the `stat` check is an exact binomial test of all three outcomes (Bonferroni, 5σ two-sided) | Appendix A | `test_photon_statistics_check_covers_all_three_outcomes` |
| V6-1 | α_s(M_Z) ≥ 0.205: the world could not be built; as a first world the worker died | **fixed** [error in earlier]: the one-loop closed-form check is skipped with the reason when the Landau pole lies above its scale; the worker reports a failed first world in the player instead of a traceback | `v06_qcd/viz.py`, `server/lfviz/worker.py` | `test_large_coupling_worlds_are_built[0.205, 0.25, 0.3]`; server suite |
| V6-2 | the κ vs 4/3 α_s comparison was painted as a failure | **fixed**: a new `info: true` flag of check messages (drawn as ≈, never ✓/✗; `RULES.md` §3, player) | `viz.py`, `player/js/player.js`, `RULES.md` | `test_presets_run_and_checks_agree` (the comparison is `info`) |
| V6-3 | threshold matching: the omitted term misstated (3.8e-3 at m_c), the continuity check an identity | **fixed** [error in earlier]: the engine now decouples at m_h(m_h) with one loop less than the running (engine review E7; RunDec coefficients checked in the paper's source); the threshold check compares the jump with the decoupling relation written out in the check | `lfphys/core/qcd/running.py`, `viz.py` | `test_threshold_jump_is_the_decoupling_relation[1–4 loops]` (a jump > 1e-3 at m_c from 3 loops, continuity at 1–2); engine `test_qcd.py` |
| V6-4 | a live change of the sweep speed threw the probe back to the start scale | **fixed**: a new speed continues from the probe's current scale; only a new start scale moves it | `viz.py` (`_mu_at`, `mu_dec0`) | `test_sweep_speed_change_keeps_the_probe_where_it_is` |
| V6-5 | fixed radial box: silent 150–390 MeV level errors for light quarks / weak strings | **fixed**: the engine's Cornell spectrum sizes the box from the highest state's turning point plus 8 decay lengths (residual < 1 MeV); quark masses below 1 GeV, where the non-relativistic heavy-quark model means nothing, are refused with the reason | `lfphys/theories/models/cornell.py`, `viz.py` | engine `test_cornell_box_grows_for_large_states` (m_q 0.3 and 1 GeV within 1 MeV of a 1.6× box); `test_light_quark_is_refused_and_the_box_grows` |
| V6-6 | values above 0.5 drawn as a flat line along the top | **fixed**: the curves are clipped at the frame, an "off scale (towards the Landau pole)" mark and a triangle probe above the frame | `web/view.js` | screenshot of the `strong` preset (verification below) |
| V7-1 | ±1e-17 probabilities from round-off made `rng.choice` raise (about half of all perfectly correlated settings) | **fixed** [error in earlier] (fixing agent): `qubits.born_probabilities` clips round-off below zero within a derived bound and raises beyond it | Appendix B | `lfphys/tests/test_born_round_off.py`, `test_perfectly_correlated_settings_run`; reviewer's `09b_v07_zero_cells_in_the_run.py` rerun |
| V7-2 | coinciding settings counted twice: the error of S off by 1.55 | **fixed** (fixing agent): S and its variance over distinct cells with summed signs; coinciding settings flagged as "not a CHSH test" | Appendix B | `test_chsh_error_with_coinciding_cells_matches_the_spread`, `test_coinciding_settings_get_the_right_error_of_S` |
| V7-3 | LHV identities shown as checks | **fixed** (fixing agent): shown as information (`info: true`) in LHV worlds | Appendix B | `test_lhv_identities_are_shown_as_information` |


## Verification by the processor (Docker, 2026-10-24)

* The reviewer's scripts rerun unchanged (outputs in the processor's scratchpad):
  `07_v05_adversarial_angles.py` — every angle around the critical one (offsets 0, ±1e-12°, ±1e-9°, +1e-7°, the typed
  41.8103149°) is accepted with no failed check; `09b_v07_zero_cells_in_the_run.py` — all settings of the `scan`
  preset run, including a = b; `08_v06_qcd.py` — worlds with α_s(M_Z) up to 0.3 are built (only the expected
  convergence failure of the `strong` world), the probe stays at 316.2 GeV through a sweep change, the Cornell box
  error is 0.47–0.72 MeV for the reviewer's light-quark cases (was 152–393 MeV); `12_v05_joule_and_rate.py` — Joule
  balance at round-off for all films; `01_v03_transmission_reference.py` — the packets that cannot be done well are
  refused with the σ needed, the thick barriers agree with the reference to 5e-4 (5 nm: was −55 %).
* After the last v03 change (fate classification) the four slow cases: free E 0.2 eV σ 1 nm 15 s (was capped after
  46 s), step 20 s, free E 0.05 eV σ 2.5 nm 4 s, barrier 5 nm 7 s; all checks pass.
* Suites: all visualizations and the server 317 passed (before the fate classification); v03 again 22 passed after
  it; engine 349 passed.
* Screenshots of the fixed views (v06 `strong` with the off-scale mark, v03 step, v07 CHSH): no page errors.

Status: **processed**, archived.

---

## Appendix A — v05: the fixing agent's notes (verbatim)


Working notes of the fixing agent; the coordinator folds them into RESPONSE.md and deletes this file.
Baseline before any change: `pytest v05_optics_bench v07_bell_test` → 61 passed.

## Diagnosis (probes in the fixing agent's scratchpad, numbers reproduced)

* V5-2 `evan`: the observed error is |rel| ≈ K·u with K = n₀² sin²θ / (n₀² sin²θ − n_s²) (condition number of
  √q w.r.t. the rounding of sin²θ), u = 2⁻⁵³: θ_c + 1e-7° → K = 2.56e8, K·u = 2.84e-8 (reviewer: 2.845e-8).
  Both routes (the engine's cos θ_t = √(1 − x²) and the reference's n₁² sin²θ − n₂²) carry it.
* V5-2 `film`: two error mechanisms.
  (a) the Airy sum is a ratio N/D with D = 1 + r₀₁r₁₂e^{2iβ} → 0 at grazing in the layer: rounding amplified by 1/|D|
      (FTIR, θ_c + 7.3e-11 rad: diff 4.1e-12, u·(1+|r|+|t|)/|D| = 3.9e-12);
  (b) NEW, not in the review: the two routes compute cos θ_j with different float formulas (snell_cos via 1 − cos²θ,
      the engine via (n₀ sinθ/n_j)²); the phase β = k n₁ d cosθ₁ is then off by ~k·u/|cosθ₁|, so thick films near
      grazing fail: n₀ = 4, n = 2.3, d = 20 µm, λ = 300 nm, θ_g − 1e-4 rad → diff 2.4e-12 > 1e-12 (all inputs inside
      the ranges); near an exit critical angle the same effect gives 1.4e-7 (metal film, θ = 85.0°, fuzz).
      With the engine's cosines shared by both routes the diff drops to ≤ 2e-15 there.
* V5-3: Simpson with 2001 points cannot resolve a 1.19 nm skin depth (reproduced: +2.9e-8 at the reviewer's input).

## Changes (status per item)

### V5-1 (error) — fixed [error in earlier]

* Cause: at θ = θ_c as asin gives it, the run's bisection put θ_c a few ulp below θ (midpoint of a 1e-15 bracket),
  `th > th_c` held, the engine's decay constant was exactly 0, `log(I1/I2) = 0` → ZeroDivisionError after the new
  parameters, structure and segment were installed; the runner catches only ValueError/KeyError/TypeError.
* Fixes: (a) `engine/bench.critical_from_T` bisects to adjacent binary64 angles and returns the first one with T = 0,
  so "θ ≥ θ_c" is the run's own T(θ) = 0; (b) the `evan` check is rewritten (V5-2) and decides only where the
  numbers determine the decay length; at κ = 0 it is shown for information; (c) `set_live` and `action` run through
  `Simulation._atomic`: messages are held back, the world's state (all attributes, dict/list copies, the Stream's
  columns, the RNG state) is restored if anything raises, and any exception becomes a ValueError → the runner's
  existing path emits `error` ("Изменение не применено: …") and then `live` with the values in force; (d) an exception
  while a world is being built becomes ValueError("мир не создан: …") → `new_world` is refused, not a crash.
* Tests: `test_exact_critical_angle_is_accepted_and_every_check_holds` (θ_c, its 12-digit display value, θ_c +
  k·1e-14°, k = −20…40: before, k = 0, 1 raised ZeroDivisionError and 18 of 39 k > 0 failed `evan` (reviewer out/07);
  after: accepted, no failed check); `test_a_change_that_fails_inside_leaves_the_world_as_it_was` (an exception
  injected after the new segment and its checks were built: before it escaped `Runner.handle`; after: exactly two
  messages `error`, `live` with the old values; params, seg, tot, segc, photons in flight, RNG state unchanged; a
  new_world that fails while being built is refused; the same change goes through once the fault is removed).
* Outside my scope (suggestion only): `server/lfviz/sim.py` `Runner.handle` (set, action) and `_new_world` catch only
  ValueError/KeyError/TypeError; catching ArithmeticError (or Exception, reported as refused) there would protect
  every visualization, not only v05. v05 no longer depends on it.

### V5-2 (should-fix) — fixed (derived, conditioning-aware tolerances)

* `evan`: reference `thin_films.evanescent_length` now evaluates q = n₁² sin²θ − n₂² in 160-bit arithmetic
  (`thin_films.evanescent_q`, one rounding; checked against Arb at 256 bits to ≤ 4u at θ_c + 1e-7°, 1e-9°, 1e-12°,
  θ_c + k·1e-14°, k = 2…40). The run measures |E|² at the face and at z = the length found from λ/4 (ln ratio ≈ 2).
  Tolerance (4.5K + 9 + 15/ln)·2⁻⁵³, K = n₀² sin²θ/q, from an operation count (README "Numerics"). Where this
  exceeds 1e-2 the line is `info: true`. Numbers: θ_c + 1e-7°: before rel 2.84e-8 > 1e-8 (fail); after rel 1.03e-8,
  tol 1.28e-7 (K = 2.6e8; the remaining error is the engine's own cos θ_t); θ_c + 1e-9°: before 2.8e-6, after 7.6e-7
  with tol 1.28e-5; θ = 60° (preset): rel 1.2e-16, tol 3.1e-15. Fuzz through the run, 2 × 800 + 1500 set-ups at
  θ_c + 10^(−14…1)°, random n₀, n_s, λ: largest |rel|/tol 0.49–0.53, 0 failures; 10–20 % informational.
* `film`: two mechanisms (see Diagnosis). `thin_films.single_film` now uses the engine's Snell cosines
  (`interfaces._cosines`) and the same float layer phase, returns D and a first-order bound err_r/err_t (∝ 1/|D|),
  raises ValueError at exact grazing (0/0); new `thin_films.stack_error_single_layer` bounds the matrix route.
  Check tolerance = sum of both; where > 1e-9 or at exact grazing also compared at θ ∓ 1e-3 rad. Numbers: 41.8103149°:
  before 4.1e-12 > 1e-12 (fail), after diff 4.1e-12 within its derived tolerance 8.1e-11 (the Airy sum's 1/|D|);
  θ_c + 1e-9°: 9.6e-12 within 1.7e-10; 20 µm film, n₀ = 4, θ_g − 1e-4 rad: before 2.4e-12 (fail), after 4.0e-16
  within 1.0e-14. Engine fuzz: 120 000 comparisons, largest diff/bound
  0.25; through the run: 2 × 1500 set-ups near grazing / exit critical: largest 0.17, 0 failures.
* Tests: `lfphys/tests/test_thin_films.py::test_evanescent_length_is_accurate_near_the_critical_angle`,
  `::test_single_film_near_grazing_within_its_error_bound` (7 inputs incl. the reviewer's), `::test_single_film_
  refuses_exact_grazing`, `::test_single_film_and_stack_agree_within_both_rounding_bounds_near_grazing` (3000 random);
  `v05 …::test_evanescent_check_tolerance_follows_the_condition_number` (5 offsets),
  `::test_single_film_check_near_grazing` (6 set-ups). All failed before, pass after (the two thick-FP film cases
  of the viz test passed already once the engine change was in, i.e. they cover the engine part).

### V5-3 (should-fix) — fixed

* `thin_films.joule_absorption_s`: composite 16-point Gauss–Legendre with sub-intervals ≤ 4/max(2|Im k_z|,
  2|Re k_z|, 1/d) (the |E|² decay rate and the cross-term frequency of the layer); GL remainder for (g + o)w ≤ 8
  is ≤ 2.5e-26 of max|f|·w; nodes are interior (no boundary ambiguity); `points` kept as an optional minimum;
  returns `nodes`. Check tolerance tightened 1e-8 → 1e-12 (`JOULE_TOL`, reasoning in viz.py/README).
* Numbers: reviewer's inputs R + T + A_J − 1: n₀ = 4, 0.2 + 20i, 500 nm, 300 nm, 70.24°: before +2.9e-8 (2001 pts),
  after 0 (1712 nodes, 18 ms); normal incidence: +2.1e-8 → −3.3e-16. Fuzz 3000 random absorbing films in the ranges:
  worst 1.4e-14.
* Tests: `lfphys/tests/test_thin_films.py::test_joule_heating_resolves_the_skin_depth` (6 films; 3 failed before);
  `v05 …::test_joule_check_resolves_a_one_nanometre_skin_depth` (failed before: tol 1e-8 and value off by 2.9e-8).

### V5-4 (nit) — fixed

* README: the sentence that grazing angles are refused is replaced by the atomic-change rule; checks table,
  numerics (derivations), tests updated.
* `stat`: `engine/bench.outcome_test` — exact two-sided binomial tail of every outcome with 0 < p < 1, Bonferroni
  over the outcomes (valid for the dependent multinomial counts), an impossible outcome that occurred → p = 0; fails
  below 5.73e-7 (the two-sided 5σ tail, the false-alarm rate of the former R-only test). Exact tails, so one photon of
  probability 1e-6 is not a "220σ" failure (the former binomial z was). Pearson χ² and per-outcome z in the note.
  The check's value is now the p-value (ref none, explicit ok).
* Test: `test_photon_statistics_check_covers_all_three_outcomes` (metal, 20 000 photons; swap pT ↔ pA → ok False;
  swap back → ok True). Before: the swapped expectation passed (only R tested). Existing statistics test adapted
  (value is the p-value; the note carries R, T, A counts).

### Found while verifying (not in the review), fixed — please decide whether to list them in RESPONSE.md

* A1 `crit`: for a thick film of lower index than n₀ (evanescent beyond its grazing angle) T of the structure
  underflows to exactly 0 long before the exit critical angle; the bisection on the structure's T reported that
  angle (n₀ = 4, n_s = 3, film 1.5 × 20 µm, λ = 300: 25.85° instead of 48.59°) and `crit` failed (3 of 1500 in the
  fuzz). Fix: θ_c is bisected on the bare boundary n_in → n_out (n sin θ is the same in every layer).
  Test `test_critical_angle_is_not_confused_with_an_opaque_structure` (failed before: 25.85 vs 48.59).
* A2 `airy`, `airymax`: just below grazing inside the film F → ∞ (1e11–1e13) and the Airy intensity formula with its
  own asin/cos disagreed with the matrices by up to 0.11 absolute (128 + 116 of 1500 fuzz set-ups; tolerances 1e-10).
  Fix: `thin_films.airy` uses the engine's cosines and layer phase, sin²(Δ/2) = sin²β or cos²β exactly, evaluated as
  T₀₁T₁₂/((1 − ρ)² + 4ρ sin²(Δ/2)) with a first-order bound err_T; `stack_error_single_layer` gives err_T of the
  matrices; per-point tolerance = sum; > 1e-9 → also compared at θ − 1e-3 rad. Tests:
  `test_airy_checks_just_below_grazing_in_the_film` (5 set-ups; 4 failed before: rel 1.4e-10 … 1.9e-3, airymax up to
  9.6e-5), `lfphys …::test_airy_formula_and_stack_agree_within_both_rounding_bounds_near_grazing` (3000 random).
  After: 0 failures in the fuzz (2 seeds × 1500).
* Cost: a live change of the `fp` preset (1600-point spectrum, unpolarized) now takes ~0.43 s (the Airy spectrum
  check evaluates two bounds per point); `bragg` (no Airy check) 0.29 s, `tir` 0.03 s.

### Reviewer scripts re-run read-only (outputs in my scratchpad, not in the review folder)

* `07`: no errors, no ZeroDivisionError; parts A (gap) all clean. Parts B/C list `evan1` for θ_c + 1e-13…1e-12°
  and k = 2…40: these are the `info: true` lines (the angle fixes the decay length only to ~K·u); the script's own
  `failed()` predates `info` and applies the tolerance rule to them; the player and the tests show them as ≈.
* `11` (300 random live changes): 0 uncaught exceptions, 0 bookkeeping violations, 0 failed checks.
* `12`: R + T + A_J − 1 = −3.3e-16 … +2.2e-16 for all six films (the script's `points=` now acts as a minimum).

v05 tests after all fixes: 51 passed; whole command `v05_optics_bench v07_bell_test tests`: 97 passed;
lfphys: 346 passed.


---

## Appendix B — v07: the fixing agent's notes (verbatim)


Working notes of the fixing agent; the coordinator folds them into RESPONSE.md and deletes this file.
Baseline before any change: `pytest v05_optics_bench v07_bell_test` → 61 passed.

## Changes (status per item)

### V7-1 (error) — fixed [error in earlier]

* Cause: `qubits.joint_probabilities` (and `qubits.measure`) return the float traces Tr(ρ Π⊗Π); an exactly-zero cell
  comes out as ±1e-17 (−3e-33 … −7e-17), and `Generator.choice` rejects a negative p.
* Fix (where the probabilities are formed): new `qubits.born_probabilities(p, dim)` — a negative value within the
  round-off of a trace, 4·dim·eps·Σ|p| (dim products + dim − 1 additions per diagonal entry, dim terms in the trace),
  is set to 0; a larger negative value raises ValueError (not a state / not projectors). Used by
  `joint_probabilities` and `measure`; `sample_pairs` still renormalises by the sum.
* `copenhagen.measure_and_collapse` (outside my scope) needs no change: its p = Re⟨b|b⟩ = Σ|b_i|² is a sum of
  non-negative floats, never negative.
* Tests: `lfphys/tests/test_born_round_off.py` (new; 6 tests failed before: P.min() < 0 / sampling raised; pass
  after); `v07_bell_test/tests/test_v07_bell.py::test_perfectly_correlated_settings_run` (photons a = b = 30°,
  a = 30°, b = 120°; spins a = b = 30°, a = 50°, b = 230°): with the pre-fix `joint_probabilities` monkeypatched in, all
  four raise `ValueError: Probabilities are not non-negative` in `advance`; after: no error, N > 2000, E = ±1 exactly.
* Files: `lfphys/lfphys/core/quantum/qubits.py`, the two test files, README (causal chain, tests).

### V7-2 (nit) — fixed (derived formula + flag)

* With a′ = a or b′ = b two CHSH cells are one angle pair (Store keys by angle pair) = the same counts. Derived:
  S = Σ_c w_c E_c over distinct cells, w_c = sum of the CHSH signs of the cells equal to c; the distinct cells are
  independent samples, so Var S = Σ_c w_c² Var E_c (a′ = a: S = 2E(a,b), Var S = 4 Var E(a,b)).
* `bell_stats.chsh(cells, signs, keys=None)` and `chsh_se_under(E_refs, ns, keys=None)` group cells by key (without
  keys: as before). v07 `_S` passes the angle-pair keys; the S check note flags coinciding settings ("S сводится к 2E
  одной пары углов, это не проверка CHSH"); a no-signalling difference between two coinciding cells is shown as
  information (identically 0).
* Numbers (40 seeds × ~4000 pairs, empirical SD of S / mean reported σ): a = a′ = 0, b = 45, b′ = 0: before
  0.0523 / 0.0316 = 1.65 (reviewer 1.55 with 60 seeds), after 0.0523 / 0.0447 = 1.17 (200 seeds: 0.0439 ± 0.0022 /
  0.0448 = 0.98); a = a′ = 0, b = 0, b′ = 45: before SD 0 vs σ 0.0316, after σ = 0 (S = 2 exactly); b = b′ = 22.5,
  a = 0, a′ = 45: 0.94 before and after (the old formula happens to coincide there).
* Tests: `lfphys/tests/test_bell_stats.py::test_chsh_error_with_coinciding_cells_matches_the_spread` (3 key patterns,
  6000 repetitions; σ formula exact, spread within 4 %); `test_v07_bell.py::test_coinciding_settings_get_the_right_
  error_of_S` (3 settings × 40 seeds; ratio within [0.75, 1.3], flag present) — failed before (no flag; ratio 1.65).

### V7-3 (nit) — fixed (marked informational)

* The player now supports `info: true` (≈, never ✓/✗; RULES.md §3). In LHV worlds `nosig_law` (P(+) = 1/2 by
  construction: an identity of the model) and `tsir_law` (implied by `chsh_law`) are emitted with `info: true`; in
  quantum worlds both remain checks of the engine's trace. The no-signalling test of an LHV world is the one from the
  run's counts (`nsA*`, `nsB*`).
* Test: `test_v07_bell.py::test_lhv_identities_are_shown_as_information` (failed before: no info flag, nosig_law
  compared 0.5 with 0.5). The preset test now skips `info` checks in its tolerance verdict, as the player does.
* README updated (checks section, tests).

v07 tests after V7-1…V7-3: 39 passed.
