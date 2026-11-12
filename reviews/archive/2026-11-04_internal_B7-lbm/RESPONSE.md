# Response to review B7 — `core.fluids.lbm` (P8) and the fluids playground `p04_fluids` (P15.7)

Processed 2026-11-04 by a subagent that wrote neither the review nor the code under review (rules: `../README.md`).
The review text and the reviewer's scripts are untouched. The reviewer's scripts were re-run on copies in the
session's scratchpad (`b7/proc_l/rerun/`; two copies, `r02` and `r08`, adapted only to read the engine's renamed private
ramp state through the new `Flow2D.inlet_scales()`); the processing's own measurements are in `b7/proc_l/scripts/` with
their outputs next to them. Environment: Docker image `light-funnel-viz`, `engine/` mounted at `/lf`, CPU with
`LFPHYS_NO_GPU=1`; GPU work on GPU 0 only through the host's `gpu_run.sh` (each job under 5 min). Quotations were checked
against texts fetched here (Schäfer & Turek 1996 from the Wayback Machine — the same file byte for byte as the
reviewer's; Ghia's tables through the GitHub API); no e-mail address or personal identifier was sent with any request.

## Summary

| id | severity | one line | decision | files |
|---|---|---|---|---|
| L1 | error | an inlet edit or a second inlet restarted every inlet's ramp | fixed: per-side ramps that blend from the side's former velocity; a velocity left unchanged keeps the ramp | `lbm.py` (kernel, `_ramp_after`, `_inlet_scales`), `viz.py`, tests |
| L2 | error | a world from a scene file lost its time base | fixed: `Flow2D(t0=...)`, t = t0 + steps·dt; ramps count steps | `lbm.py`, `viz.py`, tests |
| L3 | error | "moving" bodies do not move | fixed (relabelled as a surface velocity on a fixed shape, with its source/sink; moving bodies stay open, V41 o) | `viz.py`, `README.md`, tests |
| L4 | error | the forces shown carried the scheme's sound; the mean was never started | fixed: `acoustic_period`, `record_forces`; the playground shows the mean over the slowest sound period with its window, next to the last step's value labelled as such; the 2D-1 preset ramps | `lbm.py`, `viz.py`, `view.js`, tests |
| L5 | should-fix | benchmark presets without references, on staircase disks; the cascade unflagged | fixed: interpolated walls in the presets, benchmark comparisons (DFG 2D-1/2D-2, Ghia, Poiseuille, Couette) for exactly their set-ups, the cascade flagged | `lbm.py` (data), `viz.py`, `README.md`, tests |
| L6 | should-fix | a body force unchecked; the outlet not in hydrostatic balance | fixed: the rest state's density deviation refused above 0.045; the outlet takes the hydrostatic part; the fluid takes the hydrostatic pressure at once | `lbm.py`, `viz.py`, tests |
| L7 | should-fix | the outlet pressure unchecked; a misleading blow-up message | fixed: refused above the same limit; the blow-up message names an imposed pressure or force | `lbm.py`, tests |
| L8 | should-fix | the Kármán preset ran beyond its cell-Re limit; its test stopped in the start-up | fixed: 880 nodes (max 5.59 measured in the developed street); the test runs past the old failure time on the CPU and to the developed street on GPU 0 | `viz.py`, tests |
| L9 | should-fix | DFG 2D-2: the amplitude stood in for cLmax | fixed: cLmax (and cDmax) pinned as measured, outside the bounds; the acoustic explanation tested and withdrawn [error in earlier]; the cause → STATUS V41 (p) | `test_lbm_benchmarks.py`, `lbm.py`, verification note; STATUS via the integrator |
| L10 | should-fix | a coefficient length could not return to its default | fixed: 0 means the default in the engine | `lbm.py`, `viz.py`, tests |
| L11 | should-fix | the default laws were refused | fixed: the DFG fluid and channel by default | `viz.py`, tests |
| L12 | should-fix | the inlet's transverse layer and its edge unstated | fixed (stated and pinned by a test; the remedy stays open, V41 m) | `lbm.py`, tests; README row and STATUS via the integrator |
| L13 | nit | "resolved by the grid" was a stability limit | fixed (called stability limits; the accuracy example given) | `lbm.py`, `viz.py`, `README.md`, verification note |
| L14 | nit | `flow_rates()` read zero after an edit | fixed | `lbm.py`, tests |
| L15 | nit | the picture marked "not an approximation" | fixed | `view.js`, tests |
| L16 | nit | the picture's block averaging | fixed: an area-weighted resampling over the fluid only, covering the whole domain | `viz.py`, tests |
| L17 | nit | numbers and limits that disagreed between documents | fixed (re-measured; [error in earlier] in the test docstring) | `test_lbm_benchmarks.py`, `lbm.py`, verification note, p04 README; README row via the integrator |
| L18 | nit | the conservation bound is loose by three orders | partly fixed: a derived tight bound with a mutation test for closed domains in the tests; the running check keeps its worst-case bound (measured reason), its blind spot stated → STATUS via the integrator | `test_lbm.py`, `lbm.py` |

Counts: 17 fixed, 1 partly fixed (L18), 0 rejected; the remainders of L3 (moving bodies), L9 (the cause of the 2D-2
maxima), L12 (a better inlet) and L18 (a compensated accumulation) are open items in STATUS (text below, for the
integrator).

## Findings

### L1 (error) — an inlet edit or a second inlet restarted every inlet's ramp — **fixed**

Reproduced: `r08` (a) and (a′) as reported (inflow 0.41 → 8·10⁻⁸ kg/(s·m), the Kármán preset stopped 0.126 s later).
Cause as the review says: one start time and the largest ramp for all inlets, reset whenever any inlet was set.

Fix (`lbm.py`): a ramp record per side, `{"s0": the step it starts at, "ramp", "from"}` (`_ramps`); `_ramp_after`
decides it when a side changes: no record for a non-inlet; the record kept when the new inlet's velocity (profile,
size, tangential part) equals the old one's — an edit of the dye or of the ramp time does not touch the inflow; else a
new ramp of the new inlet's duration that starts from the velocity the side has *now* (zero after a wall; the old
inlet at its present ramp, which may itself be a blend). The link value of an inlet link is `c1 (1 − s) + val s`
(`c1`: the "from" velocity's link value, `val`: the new one's) with `s` the side's own sin² ramp; the CUDA kernel gets a
per-link side index and four scales (`prm[40..43]`) and does the same operations in the same order, so the GPU state
still equals the CPU state bit for bit (the extended GPU test blends one inlet while a second ramps from rest). For a
ramp from rest `c1 = 0` and the arithmetic is the former `fo + val·s` exactly. The ramps count steps, not seconds (L2).
`Flow2D.inlet_scales()` reports them; the playground's inspector shows each inlet's ramp. The state format is
`lfphys.lbm2d/2` (format /1 is still read: its one start time becomes every inlet's).

Verification: `test_an_inlet_edit_that_keeps_its_velocity_keeps_the_inflow_and_a_new_velocity_blends` (the dye edit and
a second inlet leave the inflow to 1e-14; a new velocity 0.2 → 0.24 m/s gives inflow = (1 − s) Q_old + s Q_new at every
step to 1e-13, monotone; negative control: a ramp after a wall starts at zero); p04
`test_editing_an_inlet_keeps_the_inflow`; `r08` re-run: the inflow stays 0.41 kg/(s·m) through the dye edit and the
second inlet, no blow-up. [useful]

### L2 (error) — a world from a scene file lost its time base — **fixed**

Reproduced (`r02` b). Fix: `Flow2D(..., t0=...)`: the time of step 0; `t = t0 + steps·dt` everywhere (`advance`,
`state_dict`, `from_state_dict`, `describe`); the playground builds its flow with `t0 = scene_time(params)` and no
longer sets `fl.t` from outside. The inlet ramps count steps from their start, so a flow started at t0 evolves bit for
bit as the same flow started at 0 (tested), and the ramp of a loaded world starts at the file's time.

Verification: `test_a_flow_started_at_a_time_counts_its_steps_from_it` (two advances, the state round trip, the
negative control at t0 = 0: same populations, times 0.2 s apart); p04
`test_the_scene_file_starts_the_same_set_up_at_its_time_and_keeps_it` (loaded, advanced twice: steps and t as
expected, the ramp started at the file's time); `r02` (b) re-run: 139, 277, 416 steps against 139, 277, 416 expected.
[useful]

### L3 (error) — "moving" bodies do not move — **fixed (relabelled)**

Reproduced (`r01` a, re-run: the disk stays at (0.2, 0.1), ±500 lattice mass through its front and back halves). The
engine's motion of bodies (moving staircase bodies with refilling) is a larger item already open (STATUS V41 o), so the
playground now says what the engine does: the parameters are «Скорость поверхности (тело на месте): vx, vy» with the
help «Тело НЕ перемещается … нормальная часть — источник спереди и сток сзади … мгновенное граничное условие
движущегося тела, но не его течение»; the rotation's help says a disk's surface velocity is tangential (a rotating
cylinder); the world's approximations gain «тела с движущейся поверхностью стоят на месте …» as soon as one is set; the
README's palette row is corrected.

Verification: p04 `test_the_surface_velocity_is_labelled_as_one_and_the_cascade_is_flagged`; engine
`test_a_body_with_a_surface_velocity_stays_where_it_is` (the nodes unchanged, the front a source and the back a sink,
equal and opposite, booked). [useful]

### L4 (error) — the forces shown carried the scheme's sound; the mean was never started — **fixed**

Reproduced (`r03`: the shown C_x 4.92–6.40 between 8 and 12 s). Fix:

* Engine: `Flow2D.acoustic_period()` — the periods of the domain's slowest standing sound waves from its sides
  (closed ends: walls and velocity inlets; open: outlets; 4L/c_s for a closed and an open end, 2L/c_s for two alike,
  L/c_s periodic); checked against the measured ringing (`test_the_acoustic_period_against_the_measured_ringing`:
  1386.3 against 1385.6 steps between an inlet and an outlet, 692.83 against 692.82 between two walls; negative
  control: not 2L/c_s). `Flow2D.record_forces(every)` / `force_record()`: the force and torque on every obstacle as
  means over consecutive blocks of whole steps, the block ends counted from the step count however `advance` is called
  (chunks end at them), restarted when the flow's set-up changes (obstacles' shapes, surface motions, wall kinds; the
  sides; the body force; the viscosity — not a dye source, a label or a coefficient length), kept through the blow-up
  guard, the state round trip and pickling. `test_the_force_record_is_the_mean_over_whole_blocks_whatever_the_calls`:
  the blocks' mean equals `reset_force_mean`'s mean over the same steps to 1e-12, two call patterns give identical
  records, an edit restarts it, a steady periodic array's blocks equal the body force (1e-8).
* Playground: the record runs in blocks of 1/64 of the slowest sound period (whole steps); the inspector shows «C_x,
  среднее за период звука», «C_y, …», the mean drag and lift, and «окно среднего: a … b с (период звука 4L/c_s
  (закрытый и открытый концы) = 1.956 с, вдоль x, c_s = 4.5 м/с)», next to «C_x за последний шаг (со звуком схемы)»;
  before a whole window has passed: «окно набирается: до t = …». The running check `cd_<id>` shows the mean once
  available, labelled so, with the window, the last step's values and the basis in its note. The 2D-1 preset ramps its
  inflow over 3 s (as the engine's test); the Kármán preset keeps its 0.5-s ramp; the airfoil its 0.3 s. The
  approximations list the scheme's sound. The engine's docstring and the benchmark test's docstring now say the ±1.5 %
  is for a 3-s ramp and give the impulsive-start figure (L17).

Verification: p04 `test_the_forces_are_shown_averaged_over_the_sound_period_with_their_window` (the shown mean equals
the engine's own mean over exactly the window's steps to 1e-12; the window is the period to half a block); `r03`
re-run with the new preset: with the 3-s ramp the last step's C_x still swings 5.456–5.772 and C_y 0.0090–0.0126 between 8 and 12 s (what the playground now labels «за последний шаг»), while the mean over two sound periods after 12 s is 5.5896 / 0.01050, inside both ranges. The preset as the player builds it (`m05`, `m06`): the window means read 5.5862 / 0.00911 (3.0–6.0 s, «вне» for C_L: the flow is not settled), 5.5840 / 0.01042 (6.1–9.0 s), 5.5873 / 0.01045 (9.0–12.0 s), 5.5969 / 0.01060 (11.0–14.0 s), 5.5917 (17.0–20.0 s): the one-period mean still carries the start's ringing, which decays by ≈ 40 % per period here, with a residual that depends on the window's phase (±0.007 at 14 s, ±0.002 at 20 s); the settled value, from a 30-s run on GPU 0 (`g09`), is 5.5895 / 0.010504 (windows after 24 s). The reference note says this. [useful]

### L5 (should-fix) — benchmark presets without references, on staircase disks; the cascade unflagged — **fixed**

* Interpolated walls: a body parameter «Стенка тела» (staircase / interpolated Bouzidi; staircase is the default for a
  body added by hand, so older scene files load unchanged); the cylinder, Kármán and airfoil presets use interpolated
  walls.
* Benchmark comparisons (group «Эталоны», info checks, shown only while the scene *is* the benchmark's set-up, detected
  from the laws and the objects): DFG 2D-1 — the mean C_D, C_L over the sound period against Table 3 with «внутри / вне»,
  the grid (D in cells), the wall, U = 2Um/3, and the engine's test values at D = 20 and 40 and with staircases; DFG 2D-2
  — C_D max and C_L max over the last period of 0.005-s-scale blocks and St from C_L's crossings over the last four
  periods, against Table 4; Ghia's cavity at Re 100 — the largest differences on the centre lines (the data moved to
  `lbm.GHIA_*`, the tests read them there); a Poiseuille channel (parabolic inlet, outlet, fixed walls) — the profile at
  a probe at least 2H from the inlet and 2H upstream of every body against 4Um y(H − y)/H², with the scheme's density
  range next to it; plane Couette flow (periodic along x, one wall moving along +x, the other fixed) — the profile
  averaged along x against U·y/H, with the viscous time H²/ν it needs (the plan's "Poiseuille / Couette references",
  P15.7). The DFG ranges and geometry are `lbm.DFG_*` (quoted from the fetched text).
* What the disk gives against the DFG range: the 2D-1 preset now uses u_max = Um = 0.3 m/s as the engine's test (its D =
  20 interpolated result 5.5893 / 0.010483 is inside); measured in the playground: «внутри» at 9 and 12 s, «вне» at 14 s (5.5969: the start's ringing, L4), settling at
  5.5895 / 0.010504 — inside, 0.0005 below the upper bound; with the
  staircase wall the comparison says «вне» (`m04`: 5.631–5.644 / 0.0112–0.0114 from 9 to 14 s). At 40 cells (880 nodes) the settled value is
  5.5791 / 0.010770. The Kármán preset (D = 40 cells,
  L8) shows St inside and C_D max, C_L max outside (L9), on GPU 0: St = 0.3013 inside 0.2950–0.3050, C_D max = 3.2454 and C_L max = 0.9802 «вне», cell Re ≤ 5.59, all checks green, 8 s in 46 s.
* The airfoil preset's label says «решётка профилей (… шаг 0,8 м = 2 хорды, не одиночное крыло)», and the
  approximations of any periodic world with a body say «тела повторяются с шагом области (решётка тел)».

Verification: p04 `test_benchmark_comparisons_appear_for_their_set_ups_only` (2D-1 after its ramp and one period:
C_D, C_L with the range, the grid and the wall; moving the disk ends it; the cavity and the channel show theirs; the
airfoil none; a Couette channel built by hand meets U·y/H to 1e-6 after three viscous times),
`test_the_surface_velocity_is_labelled_as_one_and_the_cascade_is_flagged`. The presets run by the processing (`m04`):
the cavity reads 0.0050 (u) / 0.0090 (v) of the lid speed off Ghia at 25 s on 192²; the channel's probe column 0.0055
of Um off the parabola at 12 s, density range 0.9999–1.0067; the airfoil cascade's cell Re ≈ 5, Mach 0.11, no check
failed. [useful]

### L6 (should-fix) — a body force unchecked; a uniform-pressure outlet not in hydrostatic balance — **fixed**

Reproduced (`r01` b, `r02` c). Fix (`lbm.py`):

* the rest state a body force and the outlets impose, ρ = ρ_out + g·(x − x_ref)/c_s² (lattice; the force density ρ0 g
  is uniform, so the hydrostatic density is linear; zero at the outlet of an axis with one outlet, else in the middle;
  none along a periodic axis), may deviate from ρ0 by at most `RHO_DEV_MAX` = Ma_max²/2 = 0.045 anywhere (`_check_densities`,
  in every change and at construction; refused with the numbers: the scheme's pressure scale and speed of sound, which
  are properties of the computation, and what to change);
* the outlet's density along its side carries the hydrostatic part, g_s (s − s_mid)/c_s² (its pressure is the
  pressure at the middle of its side);
* a body force switched on or changed: the fluid takes the change of the hydrostatic density at once, and the
  half-step momentum (F_new − F_old)/2 of the stored post-collision state (`_hydrostatic_shift`, booked
  "body_force_change") — an incompressible fluid's pressure follows the force instantly; without this the scheme set
  it by sound waves that overshot (measured at the limit with an outlet: max |ρ − 1| 0.1045 > 0.09) and the half-step
  impulse left 1.6·10⁻³ m/s of motion; a flow built with a force starts in its rest state;
* `set_gravity` goes through the all-or-nothing edit (a refused force leaves the flow as it was).

Verification: `test_a_fluid_at_rest_in_a_body_force_stays_at_rest_also_with_an_outlet` (with an outlet after 20 s:
max |u| < 1e-8 m/s — the re-run `r02` (c): 1.7·10⁻¹⁴ m/s, against 0.129 before; negative control: the former uniform
outlet density drives > 0.05 m/s; the default gravity in the DFG world refused, the flow unchanged; at the limit the
density stays within the running check: 0.045 measured over 6 s with and without an outlet). The help text of the
palette's body force now says what it does (the pressure at once; it drives the flow along a periodic axis; the
limit). Earth's gravity across the default channel is refused (0.099 > 0.045): STATUS item (y) for the integrator.
[useful]

### L7 (should-fix) — the outlet pressure unchecked; a misleading blow-up message — **fixed**

Reproduced (`r11` b). The outlet's pressure enters the same rest-state check (L6): 10 Pa and 1 Pa in the DFG world
are refused («давление выхода (right) 10 Па: плотность покоя схемы отклонилась бы от ρ0 на 0.494 > 0.045 …»). The
limit is half the running check's because a step of the outlet's density is reflected by closed ends with twice its
height: at ±0.999 of it the density reached 0.0892 / 0.0855 over 6 s (< 0.09). `Unstable` now names an imposed outlet
pressure (with its lattice density) and a body force (with its hydrostatic spread), and adds «уменьшите заданное
давление или силу».

Verification: `test_the_outlet_pressure_is_checked_and_named_when_the_flow_fails` (both refusals; at the limit the
reflected step stays between 0.045 and 0.09; a blow-up message names «давление на выходе»); `r11` re-run: refused.
[useful]

### L8 (should-fix) — the Kármán preset ran beyond its cell-Re limit — **fixed**

The preset now has 880 nodes (D = 40 cells, the channel height exactly 0.41 m; the nx options gain 660 and 880) and an
interpolated disk. Measured on GPU 0 (`r04` re-run on copies, and the processing's `g02`): the cell Reynolds number
stays ≤ 5.59 over 11 s (limit 10; it was 11.24 at 440 nodes), Mach ≤ 0.112, all checks green; the shown quantities:
C_x max 3.247, C_y max 0.981, St 0.301. The cost: 8 s of the world take 37 s on GPU 0 (above the preset's default speed
of 0.11 s/s) and about 15 s per 0.1 s on the CPU (stated in the label and the README; STATUS V42 h for the integrator).
The test: `test_the_karman_preset_stays_within_its_cell_reynolds_limit` runs past the ramp and past the old crossing
(0.55 s) on the CPU and, where GPU 0 is given, to 6 s with the DFG 2D-2 comparisons present (passed on GPU 0 in 42 s); the
every-preset test still covers its build and balances. [useful]

### L9 (should-fix) — DFG 2D-2: the amplitude stood in for cLmax — **fixed** (the cause of the discrepancy → STATUS)

Verified against the source: Schäfer & Turek ask for "maximum drag coefficient cDmax , maximum lift coefficient
cLmax , Strouhal number St" (text layer lines 182–183; Table 4 bounds as quoted by the review). Measured on GPU 0
(`g01`, block means of 0.005 s over 9–12 s, interpolated walls):

| D (cells) | Ma | St | cDmax | cLmax | cLmin | (cLmax + cLmin)/2 |
|---|---|---|---|---|---|---|
| 20 | 0.1 | 0.2990 | 3.3303 | 0.9793 | −1.0163 | −0.0185 |
| 20 | 0.05 | 0.2995 | 3.3248 | 0.9781 | −1.0151 | −0.0185 |
| 40 | 0.1 | 0.3009 | 3.2477 | 0.9804 | −1.0157 | −0.0176 |

St is inside 0.2950–0.3050; cLmax is outside 0.99–1.01 and cDmax outside 3.22–3.24 at both grids. The lift's offset
does not change from Ma 0.1 to 0.05 (O(Ma²) would have shrunk it four times): the former note's attribution to the
acoustic wave is withdrawn [error in earlier]. The test `test_cylinder_dfg_2d2_strouhal_and_the_maxima` (GPU) now
asserts St in its bounds, pins cLmax (0.976–0.983) and cDmax (3.31–3.35) as measured and outside their bounds, and
asserts the Ma-independence of the offset; the amplitude is no longer asserted or reported as a benchmark result
(module docstring, test docstring, verification note §1; README row and STATUS V41 (p) through the integrator). The
cause of the maxima's discrepancy (the engine's mean lift of −0.020, or the 1996 bounds) is open: STATUS V41 (p).
Verification: the GPU tests pass (`test_cylinder_dfg_2d1_drag_and_lift` 7.5 s, `test_cylinder_dfg_2d2_strouhal_and_the_maxima` 13 s; the extended bit-equality test 6.3 s; the reviewer's `r06` re-run: equal populations, dye, link records and forces). [weakens] (the 2D-2 maxima disagree with the published bounds) / [error in earlier] (the
amplitude and the acoustic attribution)

### L10 (should-fix) — the coefficient length could not return to its default — **fixed**

Reproduced (`r08` b). The engine reads `ref_length = 0` as "the default" (the width across the flow), in `add_obstacle`
and `update_obstacle` (None still keeps a value; a negative length is refused); the playground passes the object's
value as it is (0 included). Verification: engine `test_a_coefficient_length_set_back_to_zero_is_the_default_again`,
p04 `test_a_coefficient_length_set_back_to_zero_is_the_diameter_again`; `r08` (b) re-run: 0.2 m, then 0.1 m. [useful]

### L11 (should-fix) — the default laws were refused — **fixed**

Reproduced (`r02` a). The defaults are now the DFG fluid in the DFG channel (2.2 × 0.41 m, 440 nodes, u_max 0.45 m/s);
the fluid's help says why water and air at these scales are refused. Verification: the every-preset test runs the
default laws too (`preset=None`); `r02` (a) re-run: «built; errors: []». [useful]

### L12 (should-fix) — the inlet's transverse layer and its stability edge unstated — **fixed (documented)**

Reproduced: the layer (`r13` a re-run: 0.0040 … 0.038 of U in the inlet column from cell Re 1 to 10, the same numbers
on a channel half as long), and the edges (`r07`, `r09` re-run: identical to the review's outputs: the plain channel with TRT blows up at cell Re 12 after 8320 steps (uniform inlet: 1408), BGK survives 12 for 30 000 steps and fails at 20; the periodic force-driven channel is stable at 20 and 60; with the inlet at 20 the transverse velocity first grows in the inlet column; (c) the open limit holds for 10⁵ steps at cell Re 10 and 11 (max |u_y| 0.0022, 0.0024)). Stated in the module docstring
(the velocity inlet), at `RE_CELL_MAX_OPEN` (the edge is the inlet's, with the plain-channel numbers; "BGK … did not
move the edge" is now said of the cylinder runs only) and pinned by
`test_the_velocity_inlet_leaves_a_transverse_layer_that_grows_with_the_cell_reynolds_number` (0.0036–0.0044 at 1,
0.034–0.042 at 10; twenty columns in, below a tenth of it). The README row and STATUS V41 (m) through the integrator.
The remedy (a regularised or characteristic inlet) stays open in V41 (m). [neutral]

### L13 (nit) — "resolved by the grid" was a stability limit — **fixed**

`ABOUT["validity"]`, the module docstring, the constants' comment, the p04 README («refuses a world it cannot run
stably … stability edges, not accuracy») and the running check's label («… (предел устойчивости, не точности)»), with
the accuracy example from `r12` (re-run: identical to the review: Re 1000 on 64² at cell Re 15.6, accepted, all checks green, 0.0171 (u) / 0.0102 (v) of the lid speed off Ghia; on 128² 0.0072 / 0.0112; Ghia's Re = 1000 columns re-fetched and equal to the script's
arrays — verification note §2). [neutral]

### L14 (nit) — `flow_rates()` read zero after an edit — **fixed**

`flow_rates` uses the last step's records kept through an edit, as `forces` does. Verification:
`test_flow_rates_right_after_an_edit_are_the_last_steps`; `r13` (b) re-run: 0.6 / −0.6616 before and right after the
edit. [useful]

### L15 (nit) — the picture marked "not an approximation" — **fixed**

`view.js`: `exact: false, approximation: true` with the reason (2-D instead of 3-D; the weakly compressible scheme's
O(Ma²) error and sound; staircase or interpolated walls; the picture's averaging), the route label ends «— приближение».
Verification: p04 `test_the_view_marks_the_picture_as_an_approximation` (a source check of the view). [neutral]

### L16 (nit) — the picture's block averaging — **fixed**

`resample` replaces `_block`: each picture point covers an equal share of the domain (cells cut at its edges count by
their share; overlap matrices along x and y), its value is the mean over the fluid it covers only, and a point is drawn
solid when less than half of it is fluid; the picture spans the whole domain, so `size` is right. Verification: p04
`test_the_picture_averages_the_fluid_only_and_spans_the_domain` (a field constant in the fluid stays constant at every
point, mixed points included; the integral of a linear field is kept to 1e-12). [neutral]

### L17 (nit) — numbers that disagreed between documents — **fixed**

Re-measured on GPU 0 (`g01`, `g02`): 2D-1 at 40 cells cD = 5.57904, cL = 0.010752; at 80 cells 5.57746, 0.010755. The
module docstring and the verification note were right (5.5790, 0.01075; 5.5775, 0.010755); the test docstring's
5.5799 / 0.01078 and 5.5784 / 0.01078 were wrong [error in earlier] and are corrected. Ghia: the measured 0.005 / 0.008
and the asserted bounds 0.008 / 0.012 are both stated (test docstring, module docstring; README row via the
integrator). The p04 README gives both cell-Re limits. The sound's ±1.5 % is said to be for the 3-s ramp, with the
impulsive start's ±13 % (L4). [error in earlier] (the test docstring's numbers)

### L18 (nit) — the conservation bound is loose by three orders — **partly fixed**

Measured (the processing's `m03`): the mass and the dye of closed domains with fixed walls close exactly (residual 0
in a periodic Taylor–Green box and in a closed box with obstacles; 0.63 ε√(N·steps) in the lid cavity, whose lid links
book mass), but the momentum residual is 5–11 ε√(N·steps): the per-link accumulators of the booked exchanges round the
same way step after step (a steady link adds the same increment to a growing sum), so a √(N·steps) bound is wrong for
them, and a systematic bias of the nodes' rounding (the former rest-population formula: 0.36 ε per node and step) is
possible in principle.

* Tests: `roundoff_tight` — ten times ε√(N_fluid·steps) (the closure's unbiased rounding) plus the pairwise sums'
  ε(log₂ 9N + 2) of the total — for the mass and the dye of closed domains with fixed walls, ~100 times tighter than
  `roundoff`; `test_the_tight_bound_of_a_closed_domain_and_what_it_catches`: an unbooked leak of 1e-13 per step at one
  link is caught by it and passes the worst-case bound and the running check (mutation test).
* The running check keeps 2 ulps of the total per step (a worst case that must not raise false alarms over 10⁶-step
  runs with open boundaries); its blind spot is stated where it is computed and in the docstrings: a leak below ~2 ε of
  the total per step (7.5·10⁻¹³ per step at one link of the test cavity) is not seen. A tight running bound needs a
  compensated (Kahan) accumulation of the per-link records on both devices: STATUS item (z) for the integrator.
  [neutral]

## Found while processing

* The one-period mean of the 2D-1 forces carries the start's ringing while it decays (≈ 40 % per period at Ma 0.1, D =
  20 and 40): up to ±0.007 at 14 s, depending on the window's phase. The engine's test averages two periods after 9 s
  (5.5790 / 0.010752 at 40 cells) against the settled 5.5791 / 0.010770 (after 24 s, `g09`); both inside, but the
  settled D = 20 value, 5.5895, sits 0.0005 below the upper bound. The preset now uses the test's u_max (= Um), so its
  numbers are the test's; at u_max 0.45 its windows read 5.591–5.592 at 9–14 s, not separable from that residual.
  [neutral]
* The ramp's time was computed per chunk of steps (`t + (k + 1)·dt`), so its last bits depended on how `advance` was
  called; it is now a function of the step number (ramps count steps) — a replay with other advance calls is bit
  identical. [error in earlier] (latent; no test had a ramp across a replay)
* The playground's benchmark detection first returned the scene's reference tuple instead of the engine's id; caught
  by the processing's own preset run (`m04`) before the tests, fixed.

## Final test runs (after all changes)

* `lfphys`: `tests/test_lbm.py tests/test_lbm_benchmarks.py tests/test_boundary.py tests/test_layers.py
  tests/test_licences.py` on the CPU — 261 passed, 3 skipped (the GPU-only ones); the GPU-only ones on GPU 0 through the
  guard (`-k "gpu or dfg"`) — 3 passed.
* `visualizations`: `p04_fluids/tests` on the CPU — 20 passed (9.5 min); the Kármán test on GPU 0 (to the developed
  street) — passed; `tests/test_restore.py tests/test_checkpoint.py -k "p04 or shared"` — 4 passed.

## Changes for the integrator

Exact texts; I did not edit `STATUS.md`, `lfphys/README.md` or the framework.

### 1. `STATUS.md`, V41 (the lattice Boltzmann part)

In the open-items column, replace the text from `**Lattice Boltzmann** (`core.fluids.lbm`): (m)` up to (not including)
` **FLRW**` with:

> **Lattice Boltzmann** (`core.fluids.lbm`): (m) the link-wise velocity inlet leaves a transverse velocity in its column that grows with the cell Reynolds number (a plain channel: 0.4 % of U at u·dx/ν = 1, 3.8 % at 10) and sets the stability edge of open domains — a plain inlet–outlet channel blows up from 12 with TRT (BGK survives 12, fails at 20) while a periodic channel driven by a force is stable at 60: open domains are limited to 10 (a stability limit, not one of accuracy: the cavity at Re 1000 on 64² is accepted at 15.6 and lies 0.017 of the lid speed off Ghia) — review B7 L12, L13; (n) no non-reflecting outlet: standing sound waves of O(Ma²) (±1.5 % of the drag after a 3-s ramp, ±13 % after an impulsive start), forces to be averaged over whole periods (`acoustic_period`, `record_forces`; the playground shows the mean over the slowest period) — review B7 L4; (o) bodies do not move through the grid (only their surface velocity is imposed, Ladd; the playground labels it so, review B7 L3); interpolated (Bouzidi) walls only on static obstacles; (p) DFG 2D-2: St inside (0.2990 at 20 cells, 0.3009 at 40), but cLmax 0.979 / 0.980 (bounds 0.99–1.01) and cDmax 3.330 / 3.248 (bound 3.24) outside at 20 / 40 cells; the lift's mean offset (cLmax + cLmin)/2 = −0.018 is the same at Ma 0.1 and 0.05, so not the scheme's sound as assumed before [error in earlier]; cause open (2D-1 within its ranges: settled 5.5895 / 0.010504 at 20 cells, 0.0005 below the upper bound, 5.5791 / 0.010770 at 40) — review B7 L9; (q) no 3-D (D3Q19); (r) the dye is passive, its diffusivity has a floor and it carries numerical diffusion along the flow; (s) sources not fetched: Guo 2002, Bouzidi 2001, Qian 1992, the Krüger book (sections cited), Ghia 1982 itself (two agreeing transcriptions used), Lemmon 2004 for air; no Zou–He, no fp32; (y) a body force and an outlet pressure are limited to a rest-state density deviation of 0.045 (the scheme's speed of sound c_s = u_max/Ma is a property of the computation): Earth's gravity across the default 0.41-m channel is refused — review B7 L6, L7; (z) the running conservation check's bound (2 ulps of the total per step) is a worst case, since the per-link accumulators round the same way step after step: it does not see a leak below ~2 ε of the total per step (the tests use a ~100 times tighter bound for closed domains) — review B7 L18.

In the plan column, replace `(m) a regularised or characteristic inlet; (n) a sponge layer or a characteristic outlet;
(o) moving staircase bodies with refilling; (q) D3Q19;` with:

> (m) a regularised or characteristic inlet; (n) a sponge layer or a characteristic outlet; (o) moving staircase bodies with refilling; (p) 2D-2 at 80 cells and a second reference (the later literature's values, fetched and quoted); (q) D3Q19; (y) for a uniform-density fluid without a free surface, the hydrostatic pressure taken analytically (the force then changes only the reported pressure; no density limit); (z) a compensated (Kahan) accumulation of the per-link records on both devices, then a tight running bound;

### 2. `STATUS.md`, V42 (the p04 part)

Replace `**p04 «Жидкости»** (P15.7 on `core.fluids.lbm`): (e) water and air at centimetre scales and speeds are refused
(cell Reynolds number): the presets use the DFG fluid or a viscous one; (f) a scene file keeps the set-up, not the flow
(a world from a file starts from rest at its time); (g) the field picture is one field at a time (a view request)` with:

> **p04 «Жидкости»** (P15.7 on `core.fluids.lbm`): (e) water and air at centimetre scales and speeds are refused (cell Reynolds number): the defaults and the presets use the DFG fluid or a viscous one (review B7 L11); (f) a scene file keeps the set-up, not the flow (a world from a file starts from rest at its time; the engine counts its steps from there, review B7 L2); (g) the field picture is one field at a time (a view request); (h) the Kármán preset needs 880 nodes (D = 40 cells) to stay below the open cell-Reynolds limit in the developed street (max 5.59): about 1/150 of real time on the CPU, faster than its default speed on GPU 0 (review B7 L8); (i) the benchmark comparisons («Эталоны») are recognised only for the exact set-ups — the DFG 2D-1 / 2D-2 channel, Ghia's cavity at Re 100, a Poiseuille channel with a probe 2 H from the inlet and from the bodies, plane Couette flow (review B7 L5)

(the plan column of V42 is unchanged.)

### 3. `lfphys/README.md`, the row `core.fluids.lbm`

Replace the whole row with:

> | `core.fluids.lbm` | core | (P8, B7) 2-D incompressible flow by the lattice Boltzmann method (D2Q9): TRT with the magic Λ = 3/16 (BGK as an option), Guo's body force with the hydrostatic rest state taken at once; half-way bounce-back walls, moving by Ladd; staircase or interpolated (Bouzidi) obstacles — disks, rectangles, polygons, masks — added, changed or removed at any moment with mass, momentum and dye booked (or the displaced mass spread); bodies do not move (surface velocities on fixed shapes); link-wise velocity inlet (per-side ramps that blend from the side's former velocity; a transverse layer of 0.4–3.8 % of U at cell Re 1–10), anti-bounce-back pressure outlet with the hydrostatic part along it, periodic sides; a time origin t0; D2Q5 dye with sources; forces, torques, cD, cL by momentum exchange, a force record of block means and the domain's acoustic period (to average over the scheme's standing sound); mass, momentum and dye balance to round-off (a worst-case running bound); Ma, Re and cell-Re checks (refused above Ma 0.3 and cell Re 25 closed / 10 open — measured stability edges, not accuracy — and above a rest-state density deviation of 0.045 from an outlet's pressure or a body force), a blow-up guard; CPU (NumPy, threaded) or GPU 0 (CuPy kernel, bit-identical, ×8–155); water (NIST WebBook, IAPWS) and air (U.S. Standard Atmosphere 1976) data, Ghia's and the DFG reference data. Tests: exact Poiseuille and its published slip law, Couette and Taylor–Green at second order, the acoustic period against the measured ringing, DFG 2D-1 cD 5.5790 / cL 0.010752 (inside), 2D-2 St 0.2990 (inside; cLmax 0.979 and cDmax 3.330 outside, pinned), Ghia cavity 0.005 / 0.008 (asserted below 0.008 / 0.012) |

### 4. The shared framework tests

No change needed: `SMALL["p04_fluids"]` (the cavity preset's params with `nx="128"`) and the empty PLAN entry still fit
(the cavity preset is unchanged; `tests/test_restore.py tests/test_checkpoint.py -k "p04 or shared"`: 4 passed). The playground's version is 0.2 (the scene format is unchanged; older
scene files load: a body without «Стенка тела» gets the staircase wall it had).

### 5. The registry (`reviews/README.md`) and the archive

Not done here (the integrator archives after the batch). Suggested registry line: `archive/2026-11-04_internal_B7-lbm/` |
internal (subagent) | `core.fluids.lbm` (P8) and `p04_fluids` (P15.7), 13 scripts | 2026-11-04 | `RESPONSE.md`
(processed 2026-11-04: 17 of 18 fixed, L18 partly — an inlet edit restarted every inlet's ramp and stopped the inflow
[error in earlier], a world from a scene file lost its time base, "moving" bodies did not move (relabelled), the forces
shown carried the scheme's sound (now averaged over the sound period), DFG 2D-2's amplitude stood in for cLmax and the
acoustic attribution failed its test [error in earlier], the test docstring's 2D-1 numbers [error in earlier];
benchmark comparisons in the playground; the hydrostatic rest state; remainders in STATUS V41 m, o, p, y, z).

## Applied by the integrator (2026-11-04)

Items 1–3 applied as written, except that the two new V41 items are lettered (ab) and (ac) instead of (y) and (z):
the FLRW review's processing had added V41 (y) and (z) first. The folder archived with the registry row (item 5).
