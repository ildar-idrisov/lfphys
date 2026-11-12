# Response to review B6 — gravity (P15.1): `nbody`, `kerr_newman`, the charge in `kerr_geodesics`, `p01_gravity`

Processed 2026-11-03 by a subagent that wrote neither the review nor the code under review (`../README.md`: rules for
responding). The review text is unchanged. Files changed (only these): `lfphys/lfphys/core/gravity/nbody.py`,
`kerr_newman.py`, `kerr_geodesics.py` (passport only), `lfphys/tests/test_nbody.py`, `test_kerr_newman.py`,
`lfphys/sources/verification_2026-11-03_p15_1.md` (§12), `visualizations/p01_gravity/{viz.py, web/view.js, README.md,
tests/test_p01_gravity.py}`. The integrator's earlier changes to p01 (the `Trails` mixin, parameter bounds, the
non-finite box guard, the Kerr box growing with bodies and observers only) are kept. Items for `STATUS.md`,
`lfphys/README.md`, `LAYERS.md`, `pn_binary` and the registry are in the last section, for the integrator.

Environment: Docker image `light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`), containers `lf-b6pg-*`. The reviewer's
scripts were re-run unchanged from copies in the processor's scratch directory (outputs not kept in the repository; their
numbers are quoted below); my own measurement scripts are described where their numbers are used.

## Summary

| id | one line | decision | files | verification |
|---|---|---|---|---|
| G1 | the default PN binary gains energy below r ≈ 9.1 and never stops | **fixed** in p01 (cause found: the truncated 2.5 + 3.5PN reaction; the run stops where that reaction stops being an ordered series; derived one-sided balance tolerance); the engine's missing 2PN-relative reaction → STATUS V34 (integrator) | `p01_gravity/viz.py`, `README.md`, tests; verification §12 | `test_the_binary_runs_to_where_its_reaction_series_ends_and_stops_there` (preset to its stop, every balance message; D against a short integration; controls: the former rule, a 3.5PN term ×1.5); r06e re-run |
| G2 | a refused duplicate left an extra body in the engine; the next frame crashed | **fixed** (transactional engine edits; refusal as `ValueError`, in words in p01) | `nbody.py`, `viz.py` | `test_a_refused_edit_leaves_everything_as_it_was`, `test_set_many_equals_the_same_changes_one_by_one`, `test_a_refused_copy_or_a_body_on_another_leaves_the_world_running`; r10 re-run |
| G3 | the energy check divided by E = 0 | **fixed** (scale Σ½mv² + Σ G mᵢmⱼ/rᵢⱼ) | `viz.py` | `test_the_energy_check_of_a_world_whose_energy_is_zero`; r02 re-run |
| G4 | a merged body kept its pre-merger mass and radius in the scene, file and edits | **fixed** | `viz.py` | `test_a_merged_body_keeps_its_mass_and_radius_in_the_scene_its_file_and_its_edits`; r02 re-run |
| G5 | a Newtonian hole took the swallowed star's radius | **fixed** (engine: compact bodies, `radius_per_mass`) | `nbody.py`, `viz.py` | `test_a_compact_body_keeps_its_radius_rule_and_absorbs_what_it_meets` (with control), `test_a_newtonian_hole_keeps_its_schwarzschild_radius_after_swallowing_a_star`; r12 re-run |
| G6 | "circular orbit" circular only for a test body; the scene drifted | **fixed** (two-body circle with the others' reflex) | `viz.py`, `nbody.py` (`set_many`) | `test_a_body_on_a_circular_orbit_is_on_the_two_body_circle_for_any_mass`; r01 re-run |
| G7 | Kerr checks failed correct runs; the p01 test read only the last message | **fixed** (per-body drift budgets in the engine; p01 tests read every message) | `kerr_newman.py`, `viz.py`, tests | `test_drift_budgets_hold_to_the_horizon_and_catch_a_wrong_force` (with controls), `test_scene_files_after_a_capture_…`; r05b, r05c re-run |
| G8 | the default symmetrization tolerance left a secular drift | **fixed** (default 1e-3 → 1e-4; the drift and the cost stated) | `nbody.py`, verification §12 | `test_secular_drift_is_set_by_the_symmetrization_tolerance` (control: 1e-3); r08b re-run |
| G9 | `max_passes = 1` silently meant PEC; the control mixed two causes | **fixed** | `nbody.py`, `test_nbody.py` | `test_periodic_energy_without_secular_drift_and_its_two_negative_controls`; r03 re-run |
| G10 | "half the step, 16 times smaller error" | **fixed** (η/2: step √2 shorter, error ≈ ¼) | `viz.py`, `web/view.js` | `test_halving_eta_quarters_the_error`; r03 (c) re-run |
| G11 | files after a capture or a stop unloadable; observers' clocks not saved | **fixed** | `viz.py`, `kerr_newman.py` (`add_state(status, K0, budget)`) | `test_scene_files_after_a_capture_and_a_stop_and_the_observers_clocks`, `test_a_saved_captured_or_escaped_body_is_added_as_it_was` (with control); r02, r14 re-run |
| G12 | an observer added later was drawn as if placed at t = 0 | **fixed** | `viz.py` | `test_kerr_observers_and_bodies_change_only_what_was_changed`; r02 re-run |
| G13 | a colour change restarted a Kerr body | **fixed** (+1 found while fixing: a refused restart lost the body) | `viz.py` | same test; r10 (3) re-run |
| G14 | Newtonian N-body in `core` with no conflict | **fixed** in the passport (the fuller forms named; why it is core); the LAYERS.md sentence → integrator | `nbody.py` | `test_the_passport_names_the_fuller_forms`, `test_layers.py` |
| G15 | two unit comments | **fixed** | `viz.py` | IAU 2015 B3 quoted (verification §12) |
| G16 | the merger's energy change, as described | **fixed** | `nbody.py` | text |
| G17 | `kerr_geodesics` passport | **fixed** | `kerr_geodesics.py` | `test_layers.py` |
| G18 | test texts and tolerances | **fixed** (three items) | `test_kerr_newman.py` | the tests themselves |
| G19 | p01 odds and ends | **partly fixed**: ISCO observers refused, the Newtonian frame capped, long preset runs added; the symplectic option → STATUS V38 (integrator) | `viz.py`, tests | `test_kerr_observers_…`, `test_the_newtonian_frame_stops_growing_when_a_body_is_flung_out`, the three long runs |

Counts: 18 fixed, 1 partly fixed (G19), 0 rejected; deferred parts (G1's engine gap, G19's symplectic option) go to
STATUS through the integrator. Found while processing: 1 (the Kerr refused restart, under G13).

## Details

### G1 — why the default equations gain energy, and what the playground now does near merger [error in earlier]

**Reproduced** (r06e re-run on the old preset: r = 305 at t = 6e4 m; the balance check passing at 4e4 m). **Cause**,
measured on circular states, where the conservative part leaves E_2PN unchanged (its rate is odd in ṙ) so that
D = −ν dE_2PN/dt is exactly the reaction's work (script `g1_cause.py`, scratch; numbers in verification §12):

* *The 3.5PN term.* On a circular state the 3.5PN coefficient of −v/r² is −νγ³(60.55 − 6.4ν) against the 2.5PN
  term's 6.4νγ²: their ratio is −0.229 at r = 40, −0.456 at 20, −0.759 at 12, −1.011 at 9 (≈ −9.1/r). Blanchet's
  Eq. (226) bracket, 1 + γ(−743/336 − 11ν/4), also contains the conservative 1PN term B ṙ v with the inspiral's ṙ,
  which does not change the energy; the energy-changing reaction at ṙ = 0 is the one above. Its work: D_2.5/F_N = 1.258
  (r = 20) … 1.593 (r = 9), D_3.5/F_N = −0.574 … −1.611.
* *The orders used.* With 1PN + 2PN + 2.5PN + 3.5PN the equations reproduce the 1PN flux to relative 1PN (D/F_1PN → 1,
  residual −35.5 x² at small x, review r06d confirmed) — but that residual is the 2PN-relative reaction the equations
  lack (the 4.5PN reaction, Gopakumar, Iyer & Iyer 1997, cited by Blanchet 2014; not in the engine), it grows (−107 x²
  at r = 8) and cancels the reaction at **r = 9.10–9.12 for every q in [0.05, 1]**: D/F_1PN = 0.973 (r = 40), 0.870
  (20), 0.535 (12), 0.236 (10), 0 (9.1), −0.480 (8). Without the 3.5PN term D/F_1PN = 1.26, 1.60, 2.22 at r = 40, 20,
  12 and never vanishes down to the 2PN binding peak (r = 6.5–7.5): that binary does inspiral to r_stop, but its
  dissipation has a relative-1PN error of the wrong sign (60 % too strong at r = 20).
* *The gauge.* "gravitational radiation reaction is inherently gauge-dependent" (Blanchet 2014, quoted in §12); the
  engine's are the harmonic-gauge terms of Eq. (220). Another admissible gauge (Iyer & Will) changes the 2PN-relative
  remainder; none was tested here (STATUS).
* *The start.* Not the cause: the sign change is a property of the equations on circular states without integration;
  the quasi-circular start's ṙ changes D by −0.8 % (r = 20) … −15 % (r = 10) (the E_2PN conservation residual ∝ ṙ, also
  relative 2PN), the same zero.
* *Against a fuller reference* (energy balance with Blanchet's E(x) to 3PN, Eq. 232, and F(x) to 3.5PN with tails,
  Eq. 314): the time from x = 0.05 to 0.08 for q = 1 is 15787 G m/c³ with all orders, 6677 without 3.5PN, 10349 for the
  reference (12644 with the 1PN flux only); q = 0.1: 46542, 19234, 30170 (36427). No local equation of motion has the
  1.5PN tail; "all" is the consistent truncation (it matches the flux it is built to reproduce, F_1PN, to 3 % at r = 40,
  13 % at r = 20), "without 3.5PN" is closer to the full flux near merger only because its relative-1PN error offsets the
  missing tail. **So the default orders stay**, and the run stops where they stop being valid.

**Fix (p01).** At a binary's start with all orders the run computes `reaction_limit(ν)`: the outermost separation
where the reaction's remainder equals the 1PN correction it carries, |D − F_1PN| = |F_1PN − F_N| = |c₁| x F_N, c₁ =
−1247/336 − 35ν/12 — where the first neglected order of the series becomes larger than the last kept one (the
standard limit of an asymptotic series): r = 10.59 (q = 1), 10.94 (0.5), 11.69 (0.25), 12.58 (0.1), 13.01 (0.05). The
binary stops at max(r_stop, that radius) with an event naming the reason; a start at or inside it is refused with the
reason; a notice says where it will stop. The balance check's tolerance is the same ordering bound accumulated:
|ratio − 1| ≤ |c₁| x/(1 + c₁ x) at the largest x of the run (each moment's |D − F_1PN| ≤ |c₁| x F_N sums to it); it is
below 1 for x < 0.11, so a binary gaining energy (ratio < 0) fails it — the former 100 x² exceeded 1 for r < 10 and
let the outward spiral pass. The tolerance is the review's (b) with a derived bound; its (a) with a derived radius
instead of "half of F_1PN" (which would be 11.7 for every ν).

**What the playground does near merger now.** The preset (10 + 10 M☉ from r₀ = 20) inspirals for 2.03·10⁴ G m/c³
(2.0 s of world time, ≈ 100 s at the default speed) and stops at r = 10.59 G m/c² with the event «… ближе реакция
излучения этих уравнений … перестаёт быть упорядоченным рядом … Последние витки и слияние постньютоновские уравнения не
описывают — движение остановлено»; the waves then have f = 86 Hz (x = 0.0889; for q = 0.25 the stop is at 11.69, 73 Hz;
q = 0.05: 13.01, 62 Hz). There the equations' dissipation is 0.35 of F_1PN. The last orbits, the plunge and the merger
are not shown (no model of them in the engine: STATUS V34). With the orders «Ньютон + 2,5ПН» a binary still goes down
to r_stop (self-consistent at leading order, labelled as such in the README).

**Verified.** Measured on the preset: every balance message passes, the worst at 0.59 of its tolerance (q = 0.25:
0.60, q = 0.05: 0.61). Controls: without the stop the balance check fails and the binary is still running at
4.5·10⁴ G m/c³; a 3.5PN term 1.5 times too strong fails it at once. D (complex-step rate along the equations) against
a second route — the energy change of a short integration from the circular state, Richardson on dt and dt/2 — at
r = 12 and 8.5 (where D < 0). The reviewer's r06e re-run: the preset stops at r = 10.5889 by t = 4·10⁴ m (ratio 0.609,
tol 0.652); r06 now refuses its r₀ = 8.5 start (its last case). r06b, r06c, r06d call the engine directly and show its
unchanged equations (the same numbers as delivered): the gap they document is the STATUS item.

[error in earlier] p01 README: "the PN expansion fails near r ≈ 6–10 G m/c² (the run stops at the chosen distance)" and
the tolerance 100 x² ("measured −40 x² … −70 x²") — the run never reached the chosen distance and the tolerance let a
sign error pass; corrected in the README. `pn_binary`'s validity ("ряд сходится плохо" at r ≲ 10) is too weak a
statement → integrator.

### G2 — refused edits (engine and p01)

Reproduced (r10 on the old code). `NBody.add / remove / set` and the new `set_many` run in `_transaction`: a deep copy
of every state attribute, the edit, the forces; on any failure the copy is put back (bit for bit) and the exception
re-raised, coincident points as `ValueError` (the framework's refusal). p01 rephrases it («тело оказалось бы точно в той
же точке…»). A copy of a massive body "at the current moment" is therefore refused (it lies on the original) — the
review's second option; a test body's copy is allowed. Tests compare the plain-data state and the continuation with an
untouched twin. r10 re-run: the duplicate is refused, engine rows 2/2, the world runs on. (Its second case, a star at
(0, 0, 0), is now accepted and merges with the Sun at once: since G6 the Sun moves with its reflex and is no longer
exactly at the origin; the p01 test places the star exactly on the Sun's present position, which is refused.)

### G3 — the energy check's scale

The relative change is now taken against S = Σ½mv² + Σ G mᵢmⱼ/rᵢⱼ at the reference (zero only for bodies at rest with
at most one massive body, whose energy is then exactly 0 and is shown absolute). r02 re-run: no error, checks ok.

### G4 — a merged body in the scene

`object_state` carries the mass and radius (a file or a copy restores the engine's values bit for bit); `on_set` passes
to the engine only what changed (a colour changes nothing in the world); on a merger the kept object's parameters get
the merged mass and radius (in its units) where the parameters' ranges allow — otherwise the event says the inspector
keeps the old values and the world and the file have the merged ones; the inspector's "сейчас" shows mass and radius.
r02 re-run: exported mass 1.5, reloaded 1.6 M☉ in total, radius kept after a colour change.

### G5 — compact bodies

`NBody` has a per-body radius rule: `radius_per_mass` k > 0 makes R = k m now, after a change of mass and after a
merger, and a merger with such a body keeps its key (the compact body absorbs the other, even a heavier star; of two,
the heavier). p01's holes use k = 2G M☉/c² per au, so the merged hole's radius is exactly `RS_AU · M` and the merger
is exact inside the engine's own step (a fix applied after `advance` would have left the large radius for the rest of
that call). r12 re-run: radius 1.0 × the Schwarzschild radius of 1001 M☉.

### G6 — the circular start

"circular" is the two-body circle of the new body (mass m) and the others (mass M at their centre of mass c): relative
speed sqrt(G(M + m)/d) with d the 3-D distance, along e = ẑ × (x − c) (the orbit's plane through x − c closest to xy,
counter-clockwise seen from +z); the body gets V + M/(M + m) v_rel e, all other bodies a common boost so that the
system's centre-of-mass velocity V is kept (`NBody.set_many`: one edit). A body on the z-axis through the centre of mass
has no defined plane and is refused. The label and help say so. r01 re-run: e = 0 for m = 1, 0.1, 1e-3, 1e-4 and off
the plane; preset `inner`: centre-of-mass velocity 0 (was 12.6 m/s). [error in earlier] the old test encoded the
eccentric start ("within m_earth/m_sun of 1 au"); replaced (equal stars and a planet off the plane against a companion,
x2 rule).

### G7 — the Kerr checks

The engine sums for every body over its accepted steps the most the step's allowed local error can change K and μ²:
√6 · Σₖ |∂Q/∂yₖ| · rtol · scaleₖ (the weighted RMS error ≤ rtol bounds each scaled component by √6 rtol; the analytic
gradient at the step's end, checked against central differences), linear in the steps and growing as 1/Δ near the
horizon with the shell's terms — the review's fix, accumulated per step instead of sampled (cost: 12–14 % of the
integration). `constants()` returns `K0`, `budget_K`, `budget_mu2`, `shell_scale`. p01 checks every body (also after a
capture) against its budget plus the evaluation's rounding (16 u of the terms) and shows the body nearest its limit; the
p01 tests read every check message. Measured: the r05c falls stay at ≤ 5.2·10⁻⁶ of their budgets (the former
tolerance failed by up to ×5.1, also reproduced in the new engine test), an inclined orbit over 3000 M at 1.2·10⁻³;
controls: a relative error of 10⁻⁶ in dp_r/dλ or dp_θ/dλ exceeds the budgets within 300 M (×14.5, ×67). r05b re-run:
200 check messages, 0 failed. (r05 and r05b (b) apply the reviewer's own tolerance to the engine directly; unchanged.)

### G8 — the residual secular drift

Measured (e = 0.999, η = 0.02, 300 orbits, slope per orbit / force evaluations per orbit): dt_rtol 1e-3: −2.05e-6 /
1633; 1e-4: −7.1e-8 / 1988; 1e-5: −1.57e-8 / 3098; 1e-6: −7.5e-10 / 3419 (e = 0.9: −8.4e-9 at 1e-3, −1.3e-10 at 1e-5).
The default is now 1e-4 (29 times less drift); the docstring and the validity state the drift instead of "no secular
growth". Cost: +22 % force evaluations on that orbit, but `bench`'s cold random clusters take 0.64 / 1.1 / 4.4 / 46 ms
per step for N = 3 / 30 / 100 / 300 against 0.39 / 0.66 / 3.8 / 26 ms (2.95 against 2.14 passes per step): stated, with
`dt_rtol=1e-3` named as the faster choice. The pythagorean tests pass with the new default. r08b re-run: the default
drifts −7.3e-8 per orbit over 600 orbits (was −2.2e-6). [error in earlier] the docstring's "oscillates without secular
growth" for the default.

### G9 — `max_passes = 1`

The cheap one-corrector first pass is taken only when a later pass can correct it; `max_passes = 1` is now the
extrapolated step with all `n_iter` correctors. The test has both controls (symmetric steps without iteration;
iteration without symmetric steps) and checks that P(EC)³ and PEC now differ. r03 re-run: 2555 against 853 force
evaluations, not bit-identical; late/early 1.01 (default), 18.8 and 8.2 (controls).

### G10 — η/2

The label says «вдвое меньшим η», the note «шаг ∝ √η: с η/2 он в √2 раз короче, а ошибка … примерно в 4 раза меньше,
измерено 4,05–4,11», the energy note «ошибка счёта не больше 4/3 их разности»; the view's help likewise. The engine
test measures the ratio within half an order of 4 (excluding 16). r03 (c) re-run: 4.00.

### G11 — scene files after events; clocks

Kerr bodies save their status (captured, escaped), K at their start and their drift budgets; `Geodesics.add_state`
takes `status` (an inactive saved body may lie inside the capture radius, never inside the horizon) and `K0`, `budget`
(found while fixing: a state saved at the capture radius is off the shell by its own integration drift, ~4·10⁻⁹ of the
shell's terms there, which the 1e-9 check of a new start refuses — the control in the engine test; with its budget it
is accepted and its checks continue exactly). Observers save their clock reading and azimuth. The binary saves its
status; a stopped one loads stopped. r02 re-run: the captured body reloads captured; the clock reads 0.0104485 s before
and after (it restarted at 7·10⁻¹⁰ s); r14 re-run: reloaded stopped. [error in earlier] the README's "A scene file
keeps … clocks".

### G12 — observers placed later

Each observer keeps (t₀, τ₀, φ₀) from the moment it was placed; its azimuth is φ₀ + Ω(t − t₀) (a ZAMO: ω). A moved
observer keeps its clock and its present azimuth unless the azimuth itself was changed. r02 re-run: drawn at 0.00°
(was 36.76°).

### G13 — restarts

A body or ray restarts only when a parameter of its start changed (place, velocity mode or components, direction); the
palette's help says so. Found while fixing [error in earlier]: a refused restart (e.g. a new r under the horizon) had
already removed the body from the engine, so it silently vanished while the scene kept it; the engine is now restored
from its plain-data state on any refusal (test). r10 (3) re-run: r, θ, φ, τ unchanged by a colour change.

### G14 — the layer

`LAYERS.md` §1 puts in the core "the most complete form of a law the engine has"; for N ≥ 3 Newtonian N-body gravity is
that form (no PN N-body in the engine), so the module stays in the core, but its passport now names the fuller forms
the engine has for its special cases — `pn_binary` (two bodies) and `kerr_newman` (a test body about one mass) — in
`conflicts`, which the player shows with ⚠ under «Физика этого мира», and its validity says why it is in the core. A
sentence for `LAYERS.md` (core modules may name their fuller special cases) is given to the integrator.

### G15 — units

`G_AU`'s comment: 4π²(1 − 3.8·10⁻⁵), the square of the Julian over the Gaussian year (−3.777·10⁻⁵ checked). Earth's
mass from `core.constants.GM_EARTH` (IAU 2015 B3 nominal 3.986 004·10¹⁴, quoted in §12): the presets' planet masses
change by −1.05·10⁻⁷ relative.

### G16, G17, G18

G16: the merger's energy change described with its third part (the pair's potential in the others' field). G17:
`kerr_geodesics` title and statement name Kerr–Newman, kind "numerical solution", docstring. G18: the generic-orbit
test uses coordinate-time rates (from `KerrOrbit.trajectory` at λ and λ + 10⁻⁴); the crossing's extrapolation bound is
ε²/2 · max|d²τ/dr²| with d²τ/dr² = −f′(E² − f)^(−3/2)/2 (0.35 at the horizon, derived, not 10³); the Doppler sentence
says "times D".

### G19 — odds and ends (partly fixed)

* Circular observers inside the (prograde) ISCO are refused with the reason (a test body may still be started there to
  watch it leave). r13 now builds no such scene (its first line refused).
* The Newtonian frame grows with the bodies up to 64 times the scene's size at its last change by hand: an escaping
  body leaves the frame (test: the Sun and an escaping test body, frame 128 au).
* Longer runs: `pn_inspiral` to its stop, `hole_stars` through its capture, `kerr_orbits` through its capture, each
  with every check message read.
* **Open → STATUS V38 (integrator):** the symplectic Yoshida-4 integrator is not offered in p01. Reason: it needs a
  fixed step, and a playground scene can change at any moment into one with a close encounter that a fixed step
  silently mis-integrates; with G8 the Hermite scheme's residual drift is far below its error level for thousands of
  orbits. An option would need a step chosen from the scene and a refusal (or a switch) when an encounter needs less.

## Re-runs of the reviewer's scripts (unchanged copies)

r01 (e = 0 everywhere, no drift), r02 (all four blocks fixed), r03 (P(EC)³ ≠ PEC; ratio 4.00), r04 (momentum floor
unchanged, ≤ 1.2·10⁻¹⁴), r05b (0 of 200 failed), r05c and r05 (engine-level with the reviewer's own tolerance:
unchanged by design), r06/r06b/r06c/r06d/r06e (the engine's equations unchanged; the preset now stops at 10.59; r06's
last start refused), r07 (Kerr–Newman geometry, unchanged), r08/r08b (drift −7.3·10⁻⁸ per orbit with the default),
r09 (its terms as delivered: the test's rates are now the coordinate-time ones it computes), r11 (`M_EARTH_SUN` now 3.0034893e-06 from `GM_EARTH`; the comments it prints are the script's own literals), r10, r12, r13, r14 as above.

## Tests run (Docker, CPU), all passing

Engine (`lfphys/tests`): `test_nbody.py` (28 cases), `test_kerr_newman.py`, `test_kerr_orbits.py`, `test_kerr_null.py`
(they use `kerr_geodesics`), `test_boundary.py`, `test_layers.py`, `test_licences.py`: 337 passed. Visualizations:
`p01_gravity/tests` (21 passed, 1 skipped: the Pythagorean preset's short run, which has its own test) and
`tests/test_restore.py`, `tests/test_checkpoint.py -k p01` (3 passed). Before processing: 57 passed (the two engine
files) and 13 passed, 1 skipped (p01).

## Changes for the integrator

1. **`STATUS.md` V34 (a)** — append: "Review B6-gravity G1 (2026-11-03): the harmonic-gauge reaction (2.5PN + 3.5PN)
   reproduces the 1PN flux to relative 1PN, but its 2PN-relative remainder (−35.5 x² for small x, the 4.5PN reaction of
   Gopakumar, Iyer & Iyer 1997 being absent) cancels it at r = 9.10–9.12 G m/c² for every q in [0.05, 1]; inside, the
   orbit gains energy (`lfphys/sources/verification_2026-11-03_p15_1.md` §12). p01 stops a binary with all orders where
   the remainder equals the 1PN correction (r = 10.59 for q = 1 … 13.01 for q = 0.05); the last orbits and the merger are
   not modelled." and to its "what would close it": "the 4.5PN reaction (Gopakumar, Iyer & Iyer 1997, a gauge choice),
   or a gauge in which the truncated reaction stays dissipative closer in, or a resummed inspiral-merger model as a
   labelled approximation".
2. **`STATUS.md` V38 (b)** — replace "the balance check against the 1PN circular flux, tolerance 100 x² (measured −40 x²
   … −70 x²: the 2PN dissipative terms are absent), eccentric starts information only" by "the balance check against the
   1PN circular flux, tolerance |c₁| x/(1 + c₁ x) (the ordering of the reaction series; review B6-gravity G1), eccentric
   starts information only; a binary with all orders stops at r = 10.59–13.01 G m/c² (V34 a)". Add **(f)**: "p01 offers
   only the Hermite scheme: the symplectic Yoshida-4 needs a fixed step, which a scene changed at any moment can make
   wrong (review B6-gravity G19) — an option with a step chosen from the scene and a refusal when an encounter needs a
   smaller one". In V13's B6 entry, after "its independent review pending": the gravity review processed 2026-11-03
   (`reviews/archive/2026-11-03_internal_B6-gravity/RESPONSE.md`).
3. **`lfphys/lfphys/core/gravity/pn_binary.py` `ABOUT["validity"]`** (G1 c, [error in earlier]) — replace "вблизи
   слияния (r ≲ 10 GM/c²) ряд сходится плохо" by "реакция излучения (2,5ПН + 3,5ПН, гармоническая калибровка) точна до
   относительного 1ПН; её остаток (−35,5 x² при малых x: нет реакции 4,5ПН) сокращает её при r = 9,10–9,12 GM/c² при
   любом отношении масс — ближе орбита набирает энергию; остаток равен поправке 1ПН при r = 10,6 (q = 1) … 13,0
   (q = 0,05)". Optional (rule "physics in the engine"): move `flux_c1`, `reaction_on_circle` and `reaction_limit` from
   `visualizations/p01_gravity/viz.py` into `pn_binary` (e.g. as `reaction_validity_radius(nu)`), with the criterion's
   test lines from `test_the_binary_runs_to_where_its_reaction_series_ends_and_stops_there` moved to
   `test_pn_binary.py`; p01 would then import it.
4. **`lfphys/LAYERS.md` §1**, the "core" bullet — append: "A core module whose law the engine also has in fuller form for
   special cases names those cases in `conflicts` (e.g. `core.gravity.nbody`: the most complete N-body gravity for
   N ≥ 3; for two bodies `pn_binary`, for a test body about one mass `kerr_newman`)."
5. **`lfphys/README.md`**, row `core.gravity.nbody` — replace "add / remove / change at the current time leaving the
   others bit for bit" by "add / remove / change (one body or several in one edit) at the current time leaving the others
   bit for bit, all or nothing (a refused edit leaves the object bit for bit as it was)"; after "symmetrized over the step
   (Hut et al. 1995)" add "to dt_rtol = 1e-4 (residual secular drift measured: −7·10⁻⁸ per orbit at e = 0.999, 29 times
   less than at 1e-3)"; replace "perfect merger (mass and momentum to one rounding, energy change reported)" by "perfect
   merger (mass and momentum to one rounding, energy change reported; compact bodies with a radius proportional to their
   mass absorb what they meet and keep that rule)"; replace the Hermite costs "0.4 / 0.7 / 3.5 / 26 / 260 ms for N = 3 /
   30 / 100 / 300 / 1000" by "0.64 / 1.1 / 4.4 / 46 ms for N = 3 / 30 / 100 / 300 (dt_rtol 1e-4; 0.39 / 0.66 / 3.8 / 26
   at 1e-3)". Row `core.gravity.kerr_newman` — replace "Carter's K and the mass shell with their drift" by "Carter's K and
   the mass shell with their drift and each body's drift budget (summed over its steps; +12–14 % cost)", and "plain-data
   state, bit-identical restore" by "plain-data state, bit-identical restore, saved states with their status (captured,
   escaped) and drift accounting"; its cost "0.6–0.9 ms per unit M of world time for 100–300 bodies" stays within range
   (measured now 0.41–0.44 ms on the test machine).
6. **Registry and archive** (`reviews/README.md`): after checking, move this folder to `reviews/archive/` and add the row
   "`archive/2026-11-03_internal_B6-gravity/` | internal (subagent) | the gravity physics of B6 (P15.1): `core.gravity.nbody`,
   `kerr_newman`, the charge in `kerr_geodesics`, `p01_gravity`; 21 scripts, sources quoted | 2026-11-03 | `RESPONSE.md`
   (processed 2026-11-03: 18 of 19 fixed, G19 partly (the symplectic option → STATUS V38 f) — the default PN binary gained
   energy below r ≈ 9.1 and flew apart while its balance check passed [error in earlier]: now it stops where its reaction
   series ends (10.59–13.01 G m/c²) with a derived one-sided tolerance; transactional N-body edits; compact bodies; the
   two-body circular start; per-body drift budgets for K and μ²; dt_rtol 1e-4; scene files after captures and stops;
   +1 found: a refused Kerr restart lost the body)".

## Applied by the integrator (2026-11-03)

Items 1–5 applied as written (STATUS V34 a, V38 b and f, V13; `pn_binary` `ABOUT["validity"]`; LAYERS.md §1; the
`lfphys/README.md` rows of `nbody`, `kerr_newman` and a mention in `pn_binary`'s). The optional move done:
`flux_c1`, `reaction_on_circle` and `reaction_limit` are now `pn_binary.flux_c1`, `reaction_on_circle`,
`reaction_validity_radius` (p01 uses them under its former names), with the engine test
`lfphys/tests/test_pn_binary.py::test_the_truncated_reaction_stops_being_an_ordered_series_close_in` (10.59 at q = 1,
13.01 at q = 0.05, the sign change between r = 9.0 and 9.3, the remainder of the next order far out). Item 6 (archive
and registry) after the batch's full test runs.
