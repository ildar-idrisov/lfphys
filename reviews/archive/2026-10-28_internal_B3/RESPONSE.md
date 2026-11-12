# Response to the review of batch B3 (P6, P14.4, P14.2, the shared player parts)

Responder: the working session that wrote P6 and P14.4 and merged P14.2 (not the reviewer), 2026-10-28.
The review text is unchanged. Checks of this response are in `response_checks/` (scripts state their Docker commands;
the reviewer's scripts were re-run unchanged where they still apply, outputs `*_after.txt`).

Summary: 14 of 14 accepted; 13 fixed, 1 partly fixed (B3-10: the 3-D scene is not rewound, tracked in STATUS V26 (e)).
Found while processing: the first fix of B3-4 (doubling sub-steps by an RK4-against-trapezoid indicator) made the
trajectories slow near nodes (a reference run did not finish in 20 min) — replaced by per-particle Dormand–Prince 5(4)
with a tolerance relative to the step's displacement and host-side patches for the few slow particles (below).
Outside B3: the guide's `node --test` command fixed (`*.mjs`).

| ID | one line | decision |
|---|---|---|
| B3-1 | AB phase of the comparison curves had the wrong sign | fixed |
| B3-2 | the grid choice changed the wall; no grid error measured | fixed |
| B3-3 | v10 `stars` failed on a correct run (ill-conditioned reference) | fixed |
| B3-4 | Bohm trajectories not converged particle by particle; not measured | fixed |
| B3-5 | round-off drawn as a pattern on the screen before the wave arrives | fixed |
| B3-6 | ~29 min of GPU load at schema corners, no estimate or guard; V23 (c) false | fixed |
| B3-7 | spin-½ mark offered for ⁴He and C₆₀ | fixed |
| B3-8 | v10 reports the device of the last small trace | fixed |
| B3-9 | `ab_phase` not wrapped | fixed |
| B3-10 | «Экран» not rewound when scrolling back | partly fixed → STATUS V26 (e) |
| B3-11 | v10 readout of the geometry mode names a colour not shown | fixed |
| B3-12 | README: electron time unit 8.6·10⁻¹⁸ s | fixed |
| B3-13 | "reflected" vs "lost sideways" depended on the absorbers | fixed |
| B3-14 | windows a third filled; corner labels overlap | fixed |

## Findings

### B3-1 — the AB phase of the comparison curves (fixed)
Verified: with G = v v†, v_j ∝ e^{i ph_j}, the fringe phase is ph_B − ph_A; the run's physics gives +qΦ/ħ, so the slit
phases must be (−s, +s). `v11_double_slit_2d/viz.py` `_two_path`: `ph = (-s, s)`, with the derivation in its docstring.
Test `test_a_quarter_flux_quantum_moves_the_run_and_the_curves_the_same_way` (Φ = ±Φ₀/4: the run's fringe phase, the
reference and both curves within 0.1–0.2 rad of one another). The reviewer's `c01` re-run (`response_checks/c01_after.txt`):
at +Φ₀/4 the run −1.5687, the curves −1.5680 and −1.5683; `ref_paraxial` / `ref_kirchhoff` 0.136 / 0.148 (were 0.98 /
0.99).

### B3-2 — the grid changed the wall; the grid error was not measured (fixed)
* The wall's and the mark's edges are a world parameter («Ширина краёв стенки и поля метки», default 0.2 λ, tanh), the
  same on every grid; a grid whose step exceeds it is refused (`engine/apparatus.py` `Geometry(edge=...)`, `plate`,
  `slit_channel`; `viz.py`). The screen's face z = L is a sample of every grid (`Geometry.grid(h)`), so that grids of
  different steps measure the flux through the same plane.
* The run's numerical error is measured: a companion on a neighbouring grid (1.2 times coarser, or 1.2 times finer
  when a coarser grid would not resolve the edges, as on the coarse grid whose step is the default edge) with twice
  the time step; check `numerics` (max density difference on the screen, the companion's by a cubic spline) replaces
  `time_step`; `flux_absorbed` uses it in its tolerance.
* Re-measured with the reviewer's c03 logic (`response_checks/rc03_grid_convergence.py`, only the renamed check
  differs): tests' geometry — λ/6 vs λ/8 8.0·10⁻⁵ of the peak, λ/5 vs λ/8 3.9·10⁻⁴ (were 0.167 and 0.207); mark180 —
  visibility 0.2458 / 0.2463 / 0.2463 on the three grids (were 0.246 / 0.182 / 0.109), λ/6 vs λ/8 1.4·10⁻⁴. The run's
  `numerics` on λ/6: 3.8·10⁻⁴ and 6.1·10⁻⁴ against those true differences 0.8·10⁻⁴ and 1.4·10⁻⁴ (a margin of ~4).
* Test `test_the_grid_changes_the_pattern_only_by_its_numerical_error` (λ/6 against λ/8 < 3·10⁻³ of the peak, both runs
  passing `numerics`); `test_edges_narrower_than_the_grid_are_refused`.
* The README's measured numbers re-measured on all presets (`../../../visualizations/v11_double_slit_2d/README.md`
  "Measured"). [error in earlier] The pre-review README (never reported) explained the mark's residual visibility by
  the channel's transverse modes and called it "supported"; that number depended on the edge width (B3-2), so the
  explanation is withdrawn: with fixed edges the residual is 0.25 and depends on the edge width (0.25, 0.18, 0.11) and
  on the slit width; the cause is open (STATUS V26 (a)). The engine test's 0.50 / 0.19 / 0.078 (Kirchhoff's limit) is
  stated with its edge width (1/8 λ, one grid, fixed in that test).

### B3-3 — v10's `stars` check failed a correct run (fixed)
`lfphys/core/raytrace.py` `ref_aberration`: cos θ′ = (cos θ + β)/(1 + β cos θ) and sin θ′ = sin θ /(γ (1 + β cos θ)), both
formed directly. Test `test_aberration_reference_near_the_line_of_motion` (stars within 0.08 rad of ±u and 20 000
random ones, β = 0.3, 0.5, 0.99, tolerance unchanged 16 ε γ²). The reviewer's `c13` re-run (`response_checks/c13_after.txt`):
over 20 000 random stars the largest angle is 0.8–2.6 ε γ² (was 41–273); all twelve seeds of "sky" pass, seed 5 at
5.1·10⁻¹⁶ (was 1.94·10⁻¹⁴, failed).

### B3-4 — Bohm trajectories not converged particle by particle (fixed)
* `lfphys/theories/interpretations/bohm.py` `advance_ensemble`: per-particle error-controlled Dormand–Prince 5(4)
  steps, a step accepted when its error estimate is ≤ atol + rtol |displacement| (rtol 10⁻⁵, atol 10⁻⁶ grid steps) and
  the particle moved ≤ one grid step; ψ quadratic in time through the pair's three snapshots. The tolerance relative to
  the displacement keeps the same relative accuracy on every turn round a node (an absolute one let particles spiral
  in). The few particles left to many small steps are stepped on the host from copies of their surroundings
  (`_Patches`), equal to stepping them from the grid (test).
* Found while processing: the first fix (doubling sub-steps by an RK4-against-trapezoid indicator) was exponentially
  slow near nodes (a reference run did not finish in 20 min); it was replaced by the above.
* Measured (`response_checks/rc04_bohm_error_control.py`, `rc04_narrow.txt`, narrow preset, 400 particles, against
  rtol 10⁻⁷): no fate changed; |Δx| of the hits median 1.5·10⁻⁴, 95 % 2.5·10⁻³, max 0.066 λ (fringe period 6.12 λ)
  — the reviewer's default run had 7 of 1000 fates changed and a maximum of 11.5 λ.
* The run measures it: a control of 100 particles integrated four times more tightly in the same wave, check
  `bohm_accuracy` (target: 95 % < 0.05 λ, ≤ 2 % fates changed); on the presets 95 % within 3·10⁻⁴ – 3.8·10⁻³ λ.
* Tests: `test_error_controlled_steps_follow_a_vortex` (the 2-D oscillator's vortex: circles at angular speed 1/r²,
  30 turns at r = 0.05 kept on the circle; the bare RK4 flies off), `test_patches_on_the_host_equal_the_grid`.
* Cost: the narrow preset with 2000 particles runs 81 s on GPU 0 (before the review ~50 s with the unconverged rule);
  the README states the measured accuracy instead of calling the trajectories exact.

### B3-5 — round-off drawn on the screen (fixed)
`viz.py` `_screen`: below 10⁻¹⁰ of accumulated probability the screen is "empty" (no pattern, no 3-D image); the
view draws no curve then. Test `test_the_screen_shows_nothing_before_the_wave_can_arrive`; in the browser the screen
is empty while the packet is at the plate (`response_checks/b3r_v11_early.png`).

### B3-6 — long GPU runs without an estimate (fixed)
`viz.py` `cost_estimate` / `_cost_guard`: measured rates (whole runs, `response_checks/rates_*.txt`: GPU 1.9·10⁻⁸ s per
grid point and step, 10 µs per particle and pair; CPU 3·10⁻⁷ s and 42 µs) × grid points × the pairs estimated from the
geometry (an upper estimate: runs end at ~0.56 of it); refused above 10 min on GPU 0, 1 h on the CPU, with the
estimate and what to change. Test `test_the_corners_of_the_schema_are_refused_by_their_cost` (the reviewer's corner
is refused); presets 82–104 s measured. STATUS V23 (c) corrected; README "Cost" restated for the whole schema.

### B3-7 — a spin mark for spinless particles (fixed)
Refused for particles without spin ½ in the engine (`particles.SPECIES` internal ≠ "spin"), and the control is shown
only for the electron and the neutron. Test `test_no_spin_mark_for_particles_without_spin`.

### B3-8 — v10 reported the device of the last small trace (fixed)
`lfphys/core/backend.py` `choose(..., aux=True)`: auxiliary calls are recorded apart ("aux"), so `used()["drawn"]`
keeps the main call; `raytrace.trace_directions(aux=)`, `star_images` and v10's retarded-point visibility trace pass
it; every v10 image carries its own device record (`meta.device`), shown in «Где считалось»; `core.backend` in v10's
`engine_modules()`. Test `test_the_reported_device_is_the_images`; browser: the city shows GPU, size 912 384.

### B3-9 — `ab_phase` not wrapped (fixed)
The check shows remainder(φ − 2πΦ/Φ₀·sign q, 2π) against 0 (both phases in the note); the `ab` preset: −3.4·10⁻⁸ rad.

### B3-10 — «Экран» not rewound (partly fixed)
The chart, the hits and the result now follow the time shown (the screen messages are kept with their times); in the
browser, scrolled back to 45 % of the record, «Экран» shows the pattern of that moment and no result
(`response_checks/b3r_v11_back.png`). The 3-D scene's trajectories and target are not rewound: STATUS V26 (e).

### B3-11 — v10's readout in the geometry mode (fixed)
«нарисовано в цвете покоя T K; на самом деле видно как чёрное тело D·T K» (browser: `b3r_v10_city_geometry.png`).

### B3-12 — README time unit (fixed)
8.6·10⁻¹⁷ s.

### B3-13 — reflected vs lost sideways (fixed)
"Reflected" is what is absorbed before the plate's middle (z < 0), whichever layer takes it. The reviewer's `c06`
re-run (`response_checks/c06_narrow_small_after.txt`): 0.720809 vs 0.720800 with layers of 6 and 12 λ (were 0.610 vs
0.621).

### B3-14 — layout (fixed)
A slice window and the camera window take the height their image needs at the column's width (the column scrolls,
with a stable gutter); a world's own image window (v10's camera, v11's plane) has a wider column; the x and y tick
labels of the 3-D frame stand off the near corner. Browser: `b3r_v11_end.png`, `b3r_v10_city_geometry.png` (window
488 × 542 and 488 × 366 for their images); no page errors.

## Verification
Engine and visualization suites with GPU 0 (counts in the batch report); v10 and v11 tests on the CPU as well; the
reviewer's `c01`, `c06`, `c13` re-run unchanged, `c03` with the renamed check; headless Chromium on a private server
(stopped by name, verified gone).
