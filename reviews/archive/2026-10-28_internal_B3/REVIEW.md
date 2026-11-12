# Review of batch B3 (P6, P14.4, P14.2 and the shared player parts)

Status: **awaiting processing**

Reviewer: internal (subagent, not the author of the batch), 2026-10-28.

Scope: the uncommitted working tree against f43038a (`git -C .. diff f43038a -- engine`, `git -C .. status -- engine`):
`lfphys/lfphys/core/quantum/schrodinger_nd.py`, the 2-D/3-D Bohm functions of
`lfphys/lfphys/theories/interpretations/bohm.py`, `lfphys/lfphys/core/backend.py`, `lfphys/lfphys/core/raytrace.py`,
`lfphys/lfphys/tools/colour.py` and their tests; `visualizations/v10_fast_observer/`, `visualizations/v11_double_slit_2d/`;
`visualizations/player/js/imagewin.js`, `scene3d.js`, `env3d.js`, `slices.js`, `settings.js`; the B3 parts of
`visualizations/RULES.md`, `visualizations/README.md`, `lfphys/README.md`, `lfphys/PLAN.md`, `STATUS.md`.

Environment: Docker image `light-funnel-viz:latest` (959a1b91570e); GPU 0 only (`--gpus '"device=0"'`), short runs
(the longest single container ≈ 9 min, mostly CPU-bound Bohm integration; GPU temperature logged, ≤ 81 °C); headless
Chromium `mcr.microsoft.com/playwright:v1.58.2-jammy` against the reviewer's own server `b3rev-viz8503` on port 8503
(engine mounted read-only, runs in the reviewer's scratchpad; stopped and removed by name at the end; the shared
server on 8479 was not touched). Every script states its Docker command in its header and mounts `engine/` at `/lf`;
outputs are in `out/` (screenshots in `out/browser/`). Line numbers refer to the working tree on 2026-10-28.

Test suites as delivered: `lfphys` 580 passed (GPU 0 visible, `out/t01_engine_tests.txt`); `visualizations` 414 passed
(`out/t02_viz_tests.txt`); the player's decode test passed (`out/t03_player_node_tests.txt`).

## Summary

| ID | severity | where | one line |
|---|---|---|---|
| B3-1 | error | `v11_double_slit_2d/viz.py:339-351` (`_two_path`) → `engine/apparatus.py:129-138` | the Aharonov–Bohm phases of the approximate theories' patterns have the wrong sign: at Φ = ±Φ₀/4 the paraxial and Kirchhoff curves are shifted the opposite way to the run (and to the `ab_phase` reference); `ref_paraxial` reads 0.98 of the peak instead of 0.13 |
| B3-2 | error | `v11_double_slit_2d/engine/apparatus.py:70, 81`; `viz.py:41-42, 74, 409-430`; README "The plate", "Measured"; `STATUS.md` V26 (a) | the wall's and the mark's edges are smoothed over one grid step, so the "Сетка" choice changes the physical set-up: the pattern moves by 10 % (narrow preset, λ/6 → λ/8), 17 % (tests' geometry) and 20 % (mark180) of its peak, the 180° mark's residual visibility is 0.25 / 0.18 / 0.11 on the three grids; the run measures no grid error and shows the time-step error (5·10⁻⁴) as its only numerical error |
| B3-3 | error | `v10_fast_observer/viz.py:368-373`; `lfphys/lfphys/core/raytrace.py:460-476` (`ref_aberration`); `lfphys/tests/test_raytrace.py:101-109` | a correct run is shown **failed**: the `stars` check's reference loses precision for stars near the line of motion (cos θ′ → ±1, then sin θ′ = √(1 − cos²θ′)); preset "sky" with seed 5 fails (1.94·10⁻¹⁴ > 16 ε γ² = 1.87·10⁻¹⁴); the tracer itself errs by ≤ 1.2 ε γ² |
| B3-4 | should-fix | `lfphys/lfphys/theories/interpretations/bohm.py:159-205` (`advance_ensemble`), `v11_double_slit_2d/viz.py:253-260`, README "Bohm trajectories" | the owner asked for exact Bohm trajectories; at the default integration a few per cent of them are not converged (hits up to 11.5 λ — two fringes — away from a refined integration, fates changed); nothing in the run measures trajectory accuracy |
| B3-5 | should-fix | `v11_double_slit_2d/viz.py:300-307` (`_screen`), `web/view.js:108` | before any wave can reach the screen, round-off (|P| ≤ 1.5·10⁻¹⁶, mostly negative) is drawn at full brightness on the 3-D screen and as spikes in «Экран»: a "pattern" appears at the screen's edges while the packet is still at the plate |
| B3-6 | should-fix | `v11_double_slit_2d/viz.py` (no cost estimate), README "Cost"; `STATUS.md` V23 (c) | corners of v11's schema run ≈ 29 min of continuous GPU 0 load (measured rate × the run's own pair count), past the host's documented hang at ~18 min; no estimate, refusal or guard; V23 (c) still says "no GPU job runs longer than seconds yet" |
| B3-7 | should-fix | `v11_double_slit_2d/viz.py:64-65, 102-108` | a spin-½ path mark is offered and computed for ⁴He and C₆₀, which the engine records without an internal state (`particles.py:40-41`); the world is not flagged as modified physics |
| B3-8 | should-fix | `v10_fast_observer/viz.py:444, 507-511, 661`; `lfphys/lfphys/core/backend.py:303-306` | v10's «Где считалось» and the run's passport report the device of the last small trace (stars or retarded shapes), not of the image: "city" says CPU (size 9900) while its image runs on GPU 0 (size 1.6 M); v10 omits `core.backend` from `engine_modules()` |
| B3-9 | nit | `v11_double_slit_2d/viz.py:511-517` | `ab_phase` compares phases without wrapping: the run's +π against the reference −π is displayed as two different numbers (rel = −2) |
| B3-10 | nit | `v11_double_slit_2d/web/view.js` (chart, result, hits); `STATUS.md` V26 (e) | scrolled back, «Экран» still shows the final pattern, the end-of-run fractions and the comparison curves, while the wave window shows the earlier moment; V26 (e) names only the 3-D trajectories |
| B3-11 | nit | `v10_fast_observer/web/view.js:20-21` | in the comparison mode "only geometry" the readout says «видно как чёрное тело D·T» although the image shows the rest colours |
| B3-12 | nit | `v11_double_slit_2d/README.md:28` | "an electron at λ = 100 pm: 8.6·10⁻¹⁸ s" — the unit mλ²/ħ is 8.6·10⁻¹⁷ s (the run itself uses the right value) |
| B3-13 | nit | `v11_double_slit_2d/viz.py:316-326` (fractions), `engine/apparatus.py:110-119` | "reflected by the plate" vs "lost sideways" depends on the absorbers' geometry: in the tests' small window 0.610 vs 0.621 reflected for layers 6 λ vs 12 λ wide (the screen pattern changes by 5·10⁻⁵ only); in the narrow preset the effect is 9·10⁻⁵ |
| B3-14 | nit | layout (v10 camera window, v11 plane window, 3-D frame labels) | the images fill about a third of their windows' height; at the 3-D frame's near corner the x and z labels are drawn over each other |

What was verified and found right is listed after the findings ("Checked and found correct"), with the scripts.

## Findings

### B3-1 (error) v11: the Aharonov–Bohm phase of the comparison patterns has the wrong sign

**Where.** `visualizations/v11_double_slit_2d/viz.py:339-351` (`_two_path`: `s = π Φ/Φ₀ sign(q)`, `ph = (s, -s)` for slits
A, B), used by `_references` (`:353-369`) through `engine/apparatus.py:129-138` (`_coherence_matrix`: amplitude factor
`exp(i ph)` per slit) for `paraxial_pattern` and `kirchhoff_pattern`; the README's checks table rows `ref_paraxial`,
`ref_kirchhoff`.

**What is wrong.** With `G = v v†`, `v_j = amp_j e^{i ph_j}`, the patterns are |Σ_j v_j A_j|², so the model's
φ_B − φ_A = −2s = −2πΦ/Φ₀·sign(q). The fringe phase φ of P ∝ 1 + V cos(qx − φ) equals φ_B − φ_A (slit B at +d/2 is
nearer to x > 0). The run's own physics and the `ab_phase` reference (`:513-514`: 2πΦ/Φ₀·sign(q)) give
φ_B − φ_A = +qΦ/ħ: the tube's vector potential (`schrodinger_nd.flux_tube`, circulation +Φ counter-clockwise in (x, z))
adds ∫A_z dz > 0 along the path through x > 0. So the two comparison curves are mirrored relative to the run for every
flux that is not an integer or half-integer number of quanta (at Φ₀/2 the shifts ±π coincide, which is why the `ab`
preset and its test cannot see it).

**Evidence.** `c01_v11_ab_sign.py` → `out/c01_v11_ab_sign.txt` (the tests' small geometry, electron):

| Φ/Φ₀ | run's fringe phase | `ab_phase` reference | paraxial curve | Kirchhoff curve | `ref_paraxial` | `ref_kirchhoff` |
|---|---|---|---|---|---|---|
| 0 | 0.0000 | — | −0.0000 | −0.0000 | 0.13 | 0.15 |
| +0.25 | −1.5687 | −1.5708 | +1.5680 | +1.5683 | **0.98** | **0.99** |
| −0.25 | +1.5687 | +1.5708 | −1.5680 | −1.5683 | **0.98** | **0.99** |
| 0.5 | +3.1416 | −3.1416 | −3.1416 | +3.1416 | 0.14 | 0.13 |

The run agrees with the `ab_phase` reference to 2·10⁻³ rad; the two curves drawn for comparison have the opposite sign,
and the "Сравнение" rows then report that the approximate theories miss the pattern by 98 % of its peak.

**Fix.** `ph = (-s, s)` in `_two_path` (or derive both the curves' phases and `ab_phase` from one function), and a
test at Φ = Φ₀/4 that compares the sign of the run's fringe phase with the reference and with the curves'. Also state
which way the flux points (the tube's flux is along e_x × e_z = −e_y; the control says only "Φ/Φ₀").

### B3-2 (error) v11: the grid choice changes the wall; the grid error is neither measured nor shown

**Where.** `visualizations/v11_double_slit_2d/engine/apparatus.py:70, 81` (`eps = self.h` in `plate` and
`slit_channel`); `viz.py:41-42, 74` (the parameter «Сетка» in the group «Расчёт»: λ/5, λ/6, λ/8); `viz.py:409-430`
(`_final_checks`: norm, time step, flux, Bohm — no grid check); README "The plate" ("its edges are smoothed over one
grid step, so that the sampled potential stays resolved"), "Checks", the paragraph "Measured on the presets"; `STATUS.md`
V26 (a); `lfphys/PLAN.md` P6 (the numbers 0.50 → 0.19 → 0.078 come from `test_schrodinger_nd._double_slit_deviation`,
whose wall is also smoothed over h).

**What is wrong.** Each grid builds a different wall and a different region of the path-mark field (edges of width h),
so changing a numerical parameter changes the physics, by much more than the run's only reported numerical error.
RULES §2.6: "Numerical errors (grid, window) are measured by the run and shown in its checks." The run measures the
time step (≈5·10⁻⁴ of the peak) and presents the pattern, the visibility and the comparisons with the approximate
theories as properties of the set-up.

**Evidence.**
* `c03_v11_grid_convergence.py` (three grids, normalised screen patterns compared on the fine grid's x):

  | world | max \|P_λ/6 − P_λ/8\| / peak | max \|P_λ/5 − P_λ/8\| / peak | visibility λ/5, λ/6, λ/8 | run's `time_step` |
  |---|---|---|---|---|
  | tests' small geometry (`out/c03_v11_grid_narrow_small.txt`) | 0.167 | 0.207 | 0.879, 0.862, 0.850 | 3·10⁻⁴ |
  | preset `narrow` (`out/c03_v11_grid_narrow_full.txt`) | 0.101 | 0.336 | 0.972, 0.976, 0.985 | 5·10⁻⁴ |
  | preset `mark180` (`out/c03_v11_grid_mark180_full.txt`) | 0.201 | 0.460 | **0.246, 0.182, 0.109** | 6·10⁻⁴ |

  In the small geometry the fraction reaching the screen changes from 0.287 (λ/6) to 0.310 (λ/8).
* `c04_v11_grid_fixed_wall.py` (the same, with the edges smoothed over a fixed 0.2 λ on every grid): normal vs fine
  7.9·10⁻⁵ (small, `out/c04_v11_grid_fixed_wall_narrow_small.txt`), 1.8·10⁻⁴ (narrow,
  `out/c04_v11_grid_fixed_wall_narrow_full.txt`), 1.4·10⁻⁴ and the visibility **0.2463 on all three grids** (mark180,
  `out/c04_v11_grid_fixed_wall_mark180_full.txt`). The solver converges; the difference is the model's edge width.
* Consequence for STATUS V26 (a) and the README: the "residual visibility 0.18 of a 180° mark" is set by the edge
  width (0.25 at 0.2 λ, 0.18 at λ/6, 0.11 at λ/8), so the transverse-mode explanation offered there is at best a part
  of it; the number itself is an artefact of the grid choice.

**Fix.** Make the edge width a physical parameter of the world (or a fixed constant, e.g. λ/5, resolved by every
grid; for the mark, a stated field-edge length), independent of h; add a grid check (a companion on the next coarser
grid, as for the time step, or a stated a-priori bound) and show it; re-measure the README's numbers (ref_paraxial,
ref_kirchhoff, visibilities, the engine test's 0.50/0.19/0.078) and V26 (a) with the fixed edge, stating its width.

### B3-3 (error) v10: the `stars` check fails on a correct run (the reference loses precision near the line of motion)

**Where.** `visualizations/v10_fast_observer/viz.py:368-373` (tolerance 16 ε γ²); `lfphys/lfphys/core/raytrace.py:460-476`
(`ref_aberration`: `cp = (ct + β)/(1 + β ct)`, `sp = sqrt((1 − cp)(1 + cp))`); `lfphys/tests/test_raytrace.py:101-109`
(the same tolerance, 60 stars, three seeds-fixed cases); README checks table ("`stars` ... 16 ε γ²").

**What is wrong.** For a star within a few degrees of ±u, cos θ′ is within ~10⁻³ of ±1 and sin θ′ computed from it
carries an absolute error ~ε/sin θ′; the comparison angle then exceeds 16 ε γ² although the tracer's direction is right.
Whether a world shows the check failed depends on where its random stars fall (and, since the check keeps the worst
value over all images, on how many boosts the owner makes).

**Evidence.**
* Browser, preset "sky", seed 5 (`c09_browser.mjs` → `out/c09_browser.txt`, `out/browser/c09_v10_sky.png`): «Звёзды:
  видимые направления против формулы аберрации ... 1.94263304329·10⁻¹⁴ ✗».
* `c13_v10_roundoff_tolerances.py` → `out/c13_v10_roundoff_tolerances.txt`: seeds 1..12 of the sky preset at the
  start: seed 5 fails (1.94·10⁻¹⁴ > 1.87·10⁻¹⁴), seed 8 at 1.65·10⁻¹⁴; over 20 000 random stars the largest angle is
  41–60 ε γ² at β = 0.3 and 63–273 ε γ² at β = 0.5 (the γ² scaling of the tolerance does not describe this error).
* `c17_aberration_attribution.py` → `out/c17_aberration_attribution.txt` (50-digit reference): seed 5 — tracer
  1.0·10⁻¹⁵ rad (0.9 ε γ²), `ref_aberration` 1.96·10⁻¹⁴ rad (16.8 ε γ²) for a star 1.58° from −u; 20 000 stars at
  β = 0.5 — tracer ≤ 1.2 ε γ², reference 47 ε γ² (a star 1.57° from −u).

**Fix.** A well-conditioned reference: sin θ′ = sin θ/(γ(1 + β cos θ)) from the perpendicular component directly (or
tan(θ′/2) = √((1 − β)/(1 + β)) tan(θ/2)), combined with cos θ′ through atan2; then derive the tolerance (it should
stay at a few ε γ²); the engine test with many random stars and directions near ±u.

### B3-4 (should-fix) v11: Bohm trajectories are not converged particle by particle, and the run does not measure it

**Where.** `lfphys/lfphys/theories/interpretations/bohm.py:159-205` (`advance_ensemble`: sub-steps when
|v| 2dt > one grid step, decided from the speed at the start of the pair, at most 64); `v11_double_slit_2d/viz.py:253-260`;
README "Bohm trajectories", "Checks" (`bohm_born`, `bohm_fraction`, `no_crossing` — ensemble properties only).

**What is wrong.** The owner's request (PLAN §0, 14.4): «Точные траектории Бома в 2D вместе с метками пути». Near the
nodes of the wave Bohm velocities are large and trajectories are sensitive; with the default criterion some
trajectories land fringes away from where a refined integration takes them, or change fate, while every ensemble check
passes. No test calls `advance_ensemble` directly (`test_bohm_nd.py` uses `rk4` and `velocity_nd`); it is exercised
only inside v11's world tests, whose checks are ensemble properties.

**Evidence.**
* `c02_v11_bohm_convergence.py` on the narrow preset, 1000 particles (`out/c02_v11_bohm_convergence_narrow_full.txt`):
  default vs sub-steps at 1/8 grid step: 7 particles change fate; of 144 hitting the screen in both, median |Δx|
  7.9·10⁻³ λ, 95th percentile 0.39 λ, maximum **11.5 λ** (the fringe period is 6.1 λ), 4 more than half a period
  apart; the same against the wave with dt/2: max 10.8 λ, 5 beyond half a period. All ensemble checks pass in all
  variants.
* `c10_v11_bohm_sequence.py` (`out/c10_v11_bohm_sequence.txt`, 400 particles, a sequence against R = dt/2 and 1/8 step):
  max |Δx| 3.95 λ (default), 0.42 λ (1/2 step), 0.086 λ (1/4), 0.14 λ (1/8, the remainder being the wave's dt): the
  integration converges, the default is not converged for a few per cent of the particles.
* On the tests' small geometry the default is closer (max 0.31 λ, `out/c02_v11_bohm_convergence_narrow_small.txt`).

**Fix.** A tighter default criterion (≤ 1/4 grid step) with the speed re-evaluated during the pair (an adaptive step
with error control, e.g. step doubling), and a run check: re-integrate a subsample at half the step and show the
largest and the 95 % deviation of the hits and the number of changed fates (as the time-step check does for the
pattern); state the result in the README instead of "exact".

### B3-5 (should-fix) v11: the screen shows round-off as a pattern before the wave arrives

**Where.** `visualizations/v11_double_slit_2d/viz.py:300-307` (`_screen`: `pk = P.max() if P.max() > 0 else 1`, the
3-D target drawn as P/pk); `web/view.js:108` (the chart divides by `max(total, 1e-300)`).

**What is wrong.** Until the packet's front arrives the accumulated flux into the screen is round-off of either sign
(|P| ≤ 1.5·10⁻¹⁶, the sum ≈ −10⁻¹⁴). Whenever its largest value happens to be positive (1.7·10⁻²⁶ at wave time 2.44),
the view normalises that to full brightness; when the total is negative the chart divides by 10⁻³⁰⁰. The owner sees
bright stripes at the screen's edges while the packet is still at the plate (`out/browser/c09_v11_narrow_mid.png`,
wave time 2.45: the 3-D screen and «Экран»). It reads as a consequence shown before the run's time can produce it
(RULES §2.2), and it is not a computed pattern but noise. The test `test_nothing_reaches_the_screen_before_the_wave_can`
checks |Σ flux| < 10⁻⁸ and therefore cannot see it.

**Evidence.** `c12_v11_early_screen.py` → `out/c12_v11_early_screen.txt`: the flux at wave time 0.5, 1.0, 2.44 is
≤ 1.5·10⁻¹⁶ in magnitude (sum −1.8·10⁻¹⁴ … −8·10⁻¹⁵), the 'screen' message at 2.44 carries `peak` 1.65·10⁻²⁶; the first
real arrival (the fast tail of the packet, 5.5·10⁻⁷ of probability) at wave time ≈ 4; the final peak 1.3·10⁻³.

**Fix.** Draw the screen against a fixed scale (e.g. the probability that can still arrive, or the incident
probability) or show nothing until the accumulated probability exceeds a floor above round-off (stated, e.g. 10⁻¹⁰);
the same in the chart (no normalisation by a total ≤ that floor).

### B3-6 (should-fix) v11: tens of minutes of GPU load at the schema's corners, with no estimate or guard

**Where.** `visualizations/v11_double_slit_2d/viz.py` (schema: a ≥ 0.5, L ≤ 200, σ ≤ (40, 20), grid "fine"; no cost
estimate or refusal); README "Approximations and limits" ("Cost: the presets take 50–95 s on GPU 0 ... on the CPU many
minutes"); `STATUS.md` V23 (c) ("a lowered power limit for long GPU runs (the host hangs at ~18 min of full load) is not
implemented: no GPU job runs longer than seconds yet"); `AGENTS.md` §3 rule 9.

**What is wrong.** v11 is the first world whose single experiment keeps GPU 0 busy for a long time; at the corners of
its schema that time is around half an hour, past the host's documented hang at ~18 minutes of full load. The world
neither estimates its cost nor refuses or warns (v03 refuses above ~25 s), and STATUS V23 (c) now states something
false.

**Evidence.** `c15_v11_corner_cost.py` → `out/c15_v11_corner_cost.txt` (after warm-up, 20 timed pairs on GPU 0): the
narrow preset 17.8 ms per pair (≈1 min to the run's own end estimate); a = 0.5, d = 8, L = 200, σ = (40, 20), fine
(3369 × 3072 points): 140 ms per pair × 12 268 pairs ≈ **29 min** of computation. `c11_v11_schema_edges.py` →
`out/c11_v11_schema_edges.txt` lists further corners (13–48 min by extrapolation).

**Fix.** Estimate the cost when the world is built (grid points × pairs × the measured rate of the device) and refuse
(or ask for a coarser set-up) above a stated limit, or split the run with pauses; correct V23 (c) and the README's cost
statement for the whole schema.

### B3-7 (should-fix) v11: a spin-½ path mark for particles without spin, not flagged

**Where.** `visualizations/v11_double_slit_2d/viz.py:64-65` (the parameter «Частица несёт метку пути (спин ½)» for
every particle), `:102-108` (only "mark without spin" and "flux for a neutral particle" are refused);
`lfphys/lfphys/core/quantum/particles.py:40-41` (⁴He and C₆₀: internal state `None`).

**What is wrong.** ⁴He in its ground state and ¹²C₆₀ have no spin ½ (the engine itself records no internal state for
them), yet the world builds a spinor, turns "its spin" in slit B and reports the fringes' loss as a which-path effect —
without "modified physics" (RULES §2.3: modifications only as explicit, named law parameters, flagged).

**Evidence.** `c11_v11_schema_edges.py` → `out/c11_v11_schema_edges.txt` (a): for `he4` and `c60` with the mark180
preset: "engine internal state = None; world built: yes; modifications = None; header particle.spin = True".

**Fix.** Refuse the mark for particles whose `internal` is `None`, or offer it as a named modification ("a two-level
internal marker") flagged as such.

### B3-8 (should-fix) v10: the device reported for the image is the device of the last small trace

**Where.** `visualizations/v10_fast_observer/viz.py:444` (stars' visibility trace), `:507-511` (retarded shapes'
visibility trace), both after the image's `render`; the header's `backend.used`, shown in «Где считалось»
(`web/view.js` `drawDev`) and in the passport; `lfphys/lfphys/core/backend.py:303-306` ("the last call for drawn
results"); `viz.py:661` (`engine_modules()` without `core.backend`, unlike v08, v11 and `lfphys/README.md`'s table).

**What is wrong.** P11 ("every run records its devices and precisions in its header") is not met for v10: the record
shows the device and size of whichever trace ran last.

**Evidence.** `c14_v10_device_report.py` → `out/c14_v10_device_report.txt`: "city: header reports cpu (size 9900) ...;
the image itself: gpu (size 1622016)"; the other presets report sizes 936 / 51200 / 5642 instead of the image's
147456 / 51200 / 638976. In the browser «Где считалось» shows «CPU, fp64; авто: задача 9900 меньше порога 786432» for
the city (`out/browser/c09_v10_city.png`).

**Fix.** Read `backend.used()` right after the image's `render` (or pass `check=True`-like tags for auxiliary traces)
and send it with each image; add `core.backend` to `engine_modules()`.

### B3-9 (nit) v11: `ab_phase` compares phases without wrapping

`viz.py:511-517`: value `math.remainder(phi, 2π)` against `math.remainder(shift, 2π)`; at Φ₀/2 one comes out +π and the
other −π (`out/c01_v11_ab_sign.txt`, last row; also the README's "−π (two paths: π)"), so the row shows two different
numbers with rel = −2. Compare `math.remainder(phi − shift, 2π)` with 0.

### B3-10 (nit) v11: scrolling back rewinds the wave window but not «Экран»

Moved back to wave time 13.5 (83 particles still in flight), the panel still shows the final fractions, «334 из 2000»
and the comparison curves of the end (`out/c09_browser.txt` key `v11_back`, `out/browser/c09_v11_narrow_scrolled_back.png`);
STATUS V26 (e) names only the 3-D trajectories. Either rewind the chart, hits and result with the time shown, or add
them to V26 (e).

### B3-11 (nit) v10: the readout of the "only geometry" mode

`web/view.js:20-21`: outside the snapshot mode the readout always reads «D = …, видно как чёрное тело D·T K»; in the
mode "geometry" the image is drawn at the rest temperature (`viz.py` `_colours`, `T_rest`), so the readout describes a
colour the image does not show (`out/c09_browser.txt`, key `v10_mode_geometry`: «D = 0,4964 · видно как чёрное тело
2 582 K (в покое 5 200 K)»). Say «на самом деле видно …» or show T in that mode.

### B3-12 (nit) v11 README: the time unit of an electron

`README.md:28`: "an electron at λ = 100 pm: 8.6·10⁻¹⁸ s". m_e λ²/ħ = 9.109·10⁻³¹ · 10⁻²⁰ / 1.0546·10⁻³⁴ = 8.64·10⁻¹⁷ s;
the run uses the right value (the browser panel: 0.2229 units = 1.93·10⁻¹⁷ s, `out/browser/c09_v11_live.png`).

### B3-13 (nit) v11: "reflected" vs "lost sideways" depends on the absorbers' geometry in small windows

`viz.py:316-326`: `back` is what the source-side layer absorbed; probability reflected backwards at an angle that
reaches the side layers first is counted as "ушло вбок". `c06_v11_absorber_width.py`: in the tests' small geometry the
reflected fraction is 0.6103 with layers 6 λ wide and 0.6214 with 12 λ (`out/c06_v11_absorber_width_narrow_small.txt`);
in the narrow preset 0.810953 vs 0.811041 (`..._narrow_full.txt`). The screen pattern is insensitive (5·10⁻⁵ and
1.4·10⁻⁴ of the peak). Count by the side of the plate (z < 0 → reflected), or measure the flux through a closed contour.

### B3-14 (nit) layout

The camera window (v10) and the plane window (v11) draw their images in about a third of the window's height, leaving
the rest empty; at the 3-D frame's lower near corner the axis labels of x and z are drawn on top of each other
(`out/browser/c09_v11_narrow_t0.png`, bottom left of the scene; also `c09_v11_live.png`). Cosmetic.

## Checked and found correct

* **Split operator, spin step, absorbers, Chebyshev, LOBPCG** (`schrodinger_nd.py`, read line by line): the gauge
  phases (e^{iqχ/ħ} K e^{−iqχ/ħ} = exp(−iτ(p − qA)²/2mħ)), the Strang order of the axes, the closed-form 2 × 2
  exponential, the absorbed-probability bookkeeping (each half step removes ρ(1 − e^{−W dt/ħ})), the Chebyshev series
  and its spectral bounds with A, the current's spin term (curl of ψ†σψ); the engine tests pass (`out/t01_engine_tests.txt`).
* **The solver converges for a fixed potential** (c04: 7.9·10⁻⁵, 1.8·10⁻⁴, 1.4·10⁻⁴ of the peak between λ/6 and λ/8)
  [useful].
* **The 16th-order flux difference** (`FLUX_ORDER` comment "1e-5 at λ/6"): exact error 5.0·10⁻⁶ at k₀, 6.9·10⁻⁵ at k₀
  on the coarse grid (`c05_numerics.py` (a)) [useful].
* **The absorbing layers for the pattern**: doubling their width changes the screen pattern by 5·10⁻⁵ (small) and
  1.4·10⁻⁴ (narrow) of the peak (`c06`); the layer's reflection grows below kn ≈ 0.4 k₀ (7·10⁻³ at 0.3 k₀, 0.3 at
  0.1 k₀: `c05_numerics.py` (b)), outside the angles the screen sees [neutral].
* **The Lagrange stencils**: max |ω| = 193.80, max |ω′| = 576 at the middle node (`c05` (c)) as documented [useful].
* **The run's AB phase** agrees with 2πΦ/Φ₀·sign(q) to 2·10⁻³ rad at Φ = ±Φ₀/4 (`c01`) [useful].
* **Bohm integration converges** when refined (`c10`); no trajectory crosses the axis in the symmetric worlds; all
  ensemble checks pass in every variant (`c02`, `c10`) [useful].
* **Ray tracing is frame-independent** (`c07_raytrace_frames.py` → `out/c07_raytrace_frames.txt`): the fly-by bodies
  (cube at 0.9 c, ball at 0.5 c, floor and posts at rest) traced in the lab and again in three other frames (the cube's,
  the ball's, −0.6 c), and towers seen from a frame at 0.99 c: the same body in every pixel, rest-frame points equal to
  ≤ 3·10⁻¹² (lengths ~10), D and D·T equal to ≤ 2·10⁻¹⁴ (≈ ε γ²). (Pixels whose ray meets a pattern's cell edge
  within 10⁻⁹ — a row meeting the floor exactly at its edges — take either colour by the last bit; left out.) [useful]
* **The Terrell rotation of a cube** (`c08_raytrace_terrell.py` → `out/c08_raytrace_terrell.txt`): at R = 2000 L the
  facing face is 1/γ L wide and the trailing face β L, the leading face hidden, at β = 0.5, 0.9, 0.99 (agreement to
  O(L/R) = 2.5·10⁻⁴) [useful].
* **The colour module's quotations**: Table 1 and Listing 1 of Wyman, Sloan & Shirley (JCGT 2(2), 2013) and the
  multi-lobe row of Table 2 (2.0e-4, 6.4e-5, 4.9e-4, "Max Squared Error") grepped from the paper's PDF; illuminant A
  (x, y) = (0.44758, 0.40745), c₂ 1.435 → 1.4388·10⁻², the four-decimal sRGB matrix and the transfer curve grepped
  from the Wikipedia texts (downloads in the reviewer's scratchpad, no contact parameters sent) [useful].
* **Citations** (Crossref, no contact parameters): McKinley & Doherty, Am. J. Phys. 47, 309 (1979) and Peebles &
  Wilkinson, Phys. Rev. 174, 2168 (1968) exist as cited [neutral].
* **The measured GPU speed-ups** (`out/c16_calibration.txt`, `backend.calibrate` on GPU 0, OMP 2): split operator ×3.0
  at 128², ×25 at 1024², ×29.5 at 2048²; ray tracer ×3.4 at 256² × 12, ×8.3 at 512² × 12 — as stated (×3.8, ×7)
  within run-to-run variation [useful].
* **The sky's temperature check** (`sky_T`) stays at 1–3 ε γ² over whole-sky cameras at β = 0.3–0.99, well inside
  16 ε γ² (`c13` (c)); the energy-density check passes on all seeds [useful].
* **Causality and live changes in the browser** (`c09`, `out/c09_browser.txt`): v11 at t = 0 shows the apparatus, the
  packet, the static checks only; closing slit B in flight rebuilds the plate in 3-D (one hole left) and is logged
  «действует с этого момента»; a mark without spin is refused with a toast and the controls keep their values; the
  plane's window is fixed (no ✕); v10's box starts at the bodies' t = 0 places; the comparison modes are labelled in
  the window and its status; the live boost changes the image at once on a continuous worldline (τ = t/γ checked in
  the panel). No page errors in any page opened (v11 narrow and a small world; v10 terrell, city, sky, train, rest,
  terrell_099, snapshot).
* **Test suites**: 580 engine tests, 414 visualization tests, the player's decode test pass. (Outside B3: the guide's
  `node --test visualizations/player/js/tests/` reports one failure with Node v24.13.0 (the Playwright image), because it takes the
  directory as a test file; the test file itself passes — `out/t03_player_node_tests.txt`.)

## Scripts and outputs

| script | output | what |
|---|---|---|
| `c01_v11_ab_sign.py` | `out/c01_v11_ab_sign.txt` | AB fringe phase: run vs `ab_phase` vs the comparison curves (B3-1, B3-9) |
| `c02_v11_bohm_convergence.py` | `out/c02_v11_bohm_convergence_narrow_{small,full}.txt` | Bohm hits per particle under refinement (B3-4) |
| `c03_v11_grid_convergence.py` | `out/c03_v11_grid_{narrow_small,narrow_full,mark180_full}.txt` | patterns and visibility on the three grids (B3-2) |
| `c04_v11_grid_fixed_wall.py` | `out/c04_v11_grid_fixed_wall_{narrow_small,narrow_full,mark180_full}.txt` | the same with a fixed edge width (B3-2) |
| `c05_numerics.py` | `out/c05_numerics.txt` | flux difference error, layer reflection by angle, Lagrange stencils |
| `c06_v11_absorber_width.py` | `out/c06_v11_absorber_width_narrow_{small,full}.txt` | absorbers 6 λ vs 12 λ (B3-13) |
| `c07_raytrace_frames.py` | `out/c07_raytrace_frames.txt` | frame independence of the tracer |
| `c08_raytrace_terrell.py` | `out/c08_raytrace_terrell.txt` | Terrell rotation of a cube |
| `c09_browser.mjs` | `out/c09_browser.txt`, `out/browser/c09_*.png` | v10 and v11 in headless Chromium (B3-3, B3-5, B3-8, B3-10, B3-11, B3-14) |
| `c10_v11_bohm_sequence.py` | `out/c10_v11_bohm_sequence.txt`, `out/c10_*.npz` | Bohm convergence sequence (B3-4) |
| `c11_v11_schema_edges.py` | `out/c11_v11_schema_edges.txt` | spin for spinless particles; cost at corners (B3-6, B3-7) |
| `c12_v11_early_screen.py` | `out/c12_v11_early_screen.txt` | the screen before the wave arrives (B3-5) |
| `c13_v10_roundoff_tolerances.py` | `out/c13_v10_roundoff_tolerances.txt` | v10's ε γ² tolerances over seeds and stars (B3-3) |
| `c14_v10_device_report.py` | `out/c14_v10_device_report.txt` | the device reported vs the image's (B3-8) |
| `c15_v11_corner_cost.py` | `out/c15_v11_corner_cost.txt` | measured cost per pair at a corner (B3-6) |
| `c17_aberration_attribution.py` | `out/c17_aberration_attribution.txt` | tracer vs reference in 50 digits (B3-3) |
| `run_gpu_batch1.sh` | `out/gpu_batch1.log` | the GPU runs of c04/c06 in sequence with temperatures |
| (test suites) | `out/t01_engine_tests.txt`, `out/t02_viz_tests.txt`, `out/t03_player_node_tests.txt`, `out/c16_calibration.txt` | as delivered; the calibration was run inline (command below) |

`out/c16_calibration.txt` was produced from `engine/` by
`docker run --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -v "$PWD":/lf:ro -w /lf/lfphys -e OMP_NUM_THREADS=2 light-funnel-viz python3 -c "from lfphys.core import backend as B; ..."`
(the call `B.calibrate(['quantum.split_operator', 'relativity.raytrace'])`, rows printed as CPU s, GPU s, ratio).
