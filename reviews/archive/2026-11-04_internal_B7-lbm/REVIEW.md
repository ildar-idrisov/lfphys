# Review B7 — 2-D lattice Boltzmann flow (plan P8: `core.fluids.lbm`) and the fluids playground (P15.7: `p04_fluids`)

**Status: awaiting processing.** Internal review by a subagent that did not write the code (2026-11-04). Rules:
`../README.md`. The reviewer does not process this review, writes no `RESPONSE.md` and does not archive it.

Scope: `lfphys/lfphys/core/fluids/lbm.py`, `lfphys/tests/test_lbm.py`, `test_lbm_benchmarks.py`,
`lfphys/sources/verification_2026-11-04_p8_lbm.md`, the row `core.fluids.lbm` of `lfphys/README.md`, STATUS V41
(m)–(s) and V42 (e)–(g); `visualizations/p04_fluids/{viz.py, web/view.js, README.md, tests/test_p04_fluids.py}` on the
framework `server/lfviz/playground.py` (RULES §6). Hashes of the files as reviewed: `reviewed_files.sha256`.

Environment: Docker image `light-funnel-viz` (Python 3.11.17, NumPy 2.4.6), `engine/` mounted read-only at `/lf`,
this folder at `/out`, CPU (`LFPHYS_NO_GPU=1`) except `r06` (GPU 0 through the host's `gpu_run.sh`). Every script
`rNN_*.py` states its command in its docstring and has its output next to it (`rNN_*.out`). Downloaded sources are
kept outside this folder (the session's scratchpad, `b7/rev_lbm_src/`); no e-mail address or personal identifier was
sent with any request.

Baseline: the shipped tests pass on the CPU (`r00_shipped_tests.out`: `test_lbm.py` + `test_lbm_benchmarks.py` 38
passed, 3 skipped — the GPU-only ones; `p04_fluids/tests` 11 passed, 316 s); the shipped GPU test passes on GPU 0
(`r06_gpu_equals_cpu.out`).

## Summary

| id | severity | where | one line |
|---|---|---|---|
| L1 | error | `lbm.py:1453-1458, 1855-1878`; `viz.py:358-375` | when any inlet has a ramp, any edit of an inlet (e.g. its dye) or a second inlet restarts the ramp of **every** inlet: the inflow drops to zero within one step (0.41 → 8·10⁻⁸ kg/(s·m)) and the Kármán preset blows up 0.13 s later |
| L2 | error | `viz.py:241-242`; `lbm.py:1663-1664` | a world loaded from a scene file sets `Flow2D.t` but not `steps`: the first advance drops the engine's time back to ≈ 0, the second computes the whole file time in one call (0.2 s file: 1455 steps at once; T s: T/dt steps), with the inlets switched off meanwhile |
| L3 | error | `viz.py:123-125`, `README.md:26` | the palette's body "velocity" is described as a body moving through the fluid with its shape; the engine imposes a surface velocity on a fixed shape: the "moving" disk stays put and pumps fluid in at its front and out at its back |
| L4 | error | `viz.py:74-91, 407-423, 508-540`; `lbm.py:53-57` | the DFG presets show instantaneous C_x/C_y dominated by the scheme's standing sound wave (2D-1 preset, no ramp: C_x 4.92–6.40 between 8 and 12 s against DFG 5.57–5.59); the playground never starts the mean, so «C_x, среднее» never appears |
| L5 | should-fix | `viz.py:73-115`, `_approx` | presets labelled as benchmarks (DFG 2D-1, 2D-2, Ghia, Poiseuille) show no reference next to the computed value (P15.7's planned "Poiseuille / Couette references"), run staircase disks that cannot reach the DFG ranges (2D-1 mean 5.6465 / 0.01109; 2D-2 C_x max 3.367, C_y 1.045/−1.082), and the airfoil preset is an unflagged periodic cascade |
| L6 | should-fix | `lbm.py:1885-1890`; `viz.py:162-165` | a body force is not checked against the hydrostatic compressibility g·H/c_s²: the palette's default gravity in the DFG-sized world gives ρ from 0.885 to 1.127 (check red, force accepted); with a constant-pressure outlet the fluid at rest starts to circulate at 0.13 m/s (walls only: 4·10⁻¹²) |
| L7 | should-fix | `lbm.py:613-621, 1091-1119`; `viz.py:155-156` | the outlet pressure is not checked: 10 Pa in the DFG world is a lattice density 1.49 at the outlet and blows up at once, with a message blaming speed, dx and viscosity; 1 Pa already fails the compressibility check |
| L8 | should-fix | `viz.py:83-91`; `test_p04_fluids.py:37-45` | the Kármán preset exceeds its own open-domain cell-Re limit from t = 0.44 s (max 11.24 > 10, 100 % of the time after 1 s): its running check is red in normal use; the preset test stops at 0.22 s, inside the inlet ramp |
| L9 | should-fix | `test_lbm_benchmarks.py:108-130`; `lbm.py:80-82`; README row; STATUS V41 (p) | DFG 2D-2: the test asserts the lift *amplitude* against the bounds of **cLmax** (Schäfer & Turek: "maximum lift coefficient cLmax"); the measured cLmax 0.980 is outside 0.99–1.01 and absent from STATUS (p); the "acoustic wave" explanation is untested |
| L10 | should-fix | `viz.py:284-289, 362-364`; `lbm.py:1824-1843` | an obstacle's coefficient length set back to 0 (= its diameter) keeps the previous custom length (0.2 m stays 0.2 m): wrong C_x, C_y shown silently |
| L11 | should-fix | `viz.py:43-66` | the playground's default laws (water, 2.2 × 0.41 m, 440 nodes, 0.45 m/s) are refused by the engine (τ − ½ = 8·10⁻⁵) |
| L12 | should-fix | `lbm.py:157-164`, docstring "Velocity inlet"; STATUS V41 (m) | the velocity inlet leaves a transverse velocity at its column that grows with the cell Reynolds number (0.4 % of U at 1, 3.8 % at 10); a plain Poiseuille channel blows up from cell Re 12 (TRT) while BGK survives 12; neither is stated |
| L13 | nit | `lbm.py:121-124`, p04 README:18 | "laminar flows resolved by the grid (cell Re ≤ 25 / 10 — measured)": the limits are stability edges, not resolution (Re 1000 cavity at cell Re 15.6: 0.017 off Ghia, three times its Re 100 floor) |
| L14 | nit | `lbm.py:2192-2196`, `1357-1377` | `flow_rates()` reads zero for every side right after any edit (the last step's records are zeroed by `_bank`; `forces()` keeps them, `flow_rates()` not): a frame drawn between an edit and the next step (e.g. while paused) shows 0 inflow |
| L15 | nit | `view.js:71` | the flow picture is marked `approximation: false`, `exact: true` for a 2-D, weakly compressible, staircase model of a 3-D flow (README's own first approximation) |
| L16 | nit | `viz.py:210-216, 477-480` | the picture's block averaging (nx 768, 1024) counts solid nodes as the scale's low end in mixed blocks and crops trailing rows while the picture keeps the full size |
| L17 | nit | `lbm.py:79-82`, test docstrings, README row, p04 README | numbers and limits that disagree between documents (cD 5.5790/0.01075 vs 5.5799/0.01078; "within 0.005/0.008" vs asserted 0.008/0.012; p04 README gives only the closed-domain limit 25) |
| L18 | nit | `test_lbm.py:24-29`, `lbm.py:2229-2233` | the conservation bound 2 ε per step is ≈ 2·10³ times the measured residual: a leak of up to ~8·10⁻¹³ mass units per step at one link passes the cavity test |

Checked and found correct (with status tags) — after the findings, section "What holds".

---

## Findings

### L1 (error) — editing an inlet, or adding another, stops every inlet's inflow and restarts its ramp

Location: `lbm.py:1027, 1453-1458` (one `_inlet_t0` for all inlets, the ramp of `max(ramps)`), `set_side` /
`set_sides` `:1855-1878` (`_inlet_t0 = self.t` whenever any inlet is set); `viz.py:358-375` (`on_set` of a side object
calls `set_sides` with a new `Inlet` for any change of its values) and `on_add` of a second inlet.

Evidence (`r08_playground_edits.py/.out`): the Kármán preset (inlet ramp 0.5 s) at t = 1 s, inlet scale 1, inflow
0.41 kg/(s·m). Changing only the inlet's dye concentration to 0.5: one step later the scale is 0.0000 and the inflow
8.4·10⁻⁸; 0.05 s later 0.010. The impulsive stop of a 1.5 m/s inflow sends a pressure wave through the channel and the
world stops 0.126 s after the edit: `Unstable … Re ячейки = 14.3 (предел 10)`. Adding a second inlet (top side, 0.01
m/s, ramp 0) at t = 1.5 s does the same to the left inlet (scale 0.0000, inflow 3.4·10⁻⁷). The engine docstring
promises a ramp "after the inlet is set", per inlet; the implementation shares one start time and the largest ramp of
all inlets (the effect needs a ramp > 0 on some inlet — the Kármán and airfoil presets have one; with no ramp the
scale stays 1).

Fix: keep the ramp per inlet (its own start time and duration inside the `Inlet` or a per-side record); when an inlet
is replaced on a running flow, blend from the old profile to the new one (or ramp only when its velocity changes); a
change of dye alone must not touch the velocity. Test: edit an inlet's dye at a developed state and assert that the
inflow does not change.

### L2 (error) — a world from a scene file loses its time base

Location: `viz.py:241-242` (`self.fl.t = scene_time(params)` while `fl.steps` stays 0); `lbm.py:1663-1664`
(`advance` recomputes `self.t = self.steps * dt`); `advance_to` `:1710-1713`; `test_p04_fluids.py:109-119` asserts
the state just after loading and never advances.

Evidence (`r02_playground_world_and_scene_time.py/.out`, part b): the Kármán preset exported at t = 0.2 s and loaded:
`fl.t = 0.2, steps = 0`. `run_to(0.21)`: 69 steps, then `fl.t = 0.00996` (dropped back). `run_to(0.22)`: 1455 steps in
one call (`steps = 1524` against 139 expected from the file's time), the inlet scale 0 for the first 0.2 s of that
(its `_inlet_t0` = 0.2 was set while `fl.t` was 0.2). For a file saved at T seconds the second call computes T/dt
steps at once (a file at 60 s in this preset: ≈ 4·10⁵ steps, about half an hour on the CPU inside one runner call).

Fix: give `Flow2D` a way to start at a time (e.g. `t0` with `t = t0 + steps·dt` everywhere, or `steps =
round(T/dt)`); test by advancing a loaded world twice and checking `steps` and `t`.

### L3 (error) — "moving" bodies do not move

Location: `viz.py:123-125` (help «Тело движется сквозь жидкость (переносится вместе со своей формой)»), p04
`README.md:26` ("a moving body is carried with its shape"); the engine (`lbm.py:41-43`, `:925-926`, STATUS V41 (o))
says the opposite: only the surface velocity is imposed, "the body itself does not move".

Evidence (`r01_moving_body_and_gravity.py/.out`, part a): a disk given (0.05, 0) m/s in a closed box: after 4 s its
centre is still (0.2, 0.1) and the solid mask is unchanged (a moving body would have travelled 0.2 m). Its front half
injected +500 and its back half removed −500 lattice mass units (total 3.6·10⁻¹⁵): a source–sink pair, i.e. the
instantaneous boundary condition of a moving cylinder frozen in place, whose flow differs from that of a moving body
after the first instant.

Fix: describe the parameter as what it is ("скорость поверхности при неподвижной форме: тело стоит, его поверхность
втягивает/выпускает жидкость"), or hide `vx, vy` until the engine moves bodies (V41 (o)); list it in the
approximations.

### L4 (error) — the forces shown are dominated by sound; the mean is never computed

Location: `viz.py:416-423` (inspector: last-step `cd`, `cl`), `:420-422` («C_x, среднее» only if `F["mean"]`),
`:531-534` (running check: last-step `cd`); `reset_force_mean` is never called anywhere in `viz.py`; preset
`cylinder_re20` (`:74-82`) has no inlet ramp. The engine states the cause (`lbm.py:53-57`: standing sound waves,
"forces averaged over whole periods are unaffected"; STATUS V41 (n)) and its tests average over two acoustic periods.

Evidence (`r03_preset_dfg_2d1.py/.out`): the preset as the player builds it; what the inspector shows: C_x = −0.48 at
2 s, 1.19 at 4 s, 4.80 at 8 s, 5.26 at 10 s, 5.44 at 12 s; between 8 and 12 s C_x swings 4.92–6.40 and C_y −0.0079 –
0.0317 (DFG: 5.57–5.59 and 0.0104–0.0110). The engine docstring's "±1.5 % of the drag at Ma = 0.1" holds for the tests'
3-s ramp, not for the preset's impulsive start (here ±13 % between 8 and 12 s; the waves decay as ν(π/2L)² ≈ 5·10⁻⁴ s⁻¹ in
physical units). The mean over two acoustic periods (1.956 s each) after 12 s: 5.6465 / 0.01109. In the Kármán preset
(`r04_preset_karman.out`) the shown C_x peaks at 3.367 (cDmax 3.22–3.24).

Fix: run a mean over whole acoustic periods (the engine knows T = 4L/c_s for a channel; a running mean over the last
period otherwise) and show it next to the instantaneous value, with the period stated; ramp the inflow of every preset;
add "sound waves of the weakly compressible scheme, O(Ma²) and larger after sudden changes" to `_approx()`.

### L5 (should-fix) — benchmark-labelled presets without their references, on staircase walls

Location: `viz.py:73-115` (labels «тест DFG 2D-1: сопротивление и подъёмная сила», «тест DFG 2D-2», «Ghia, Ghia,
Shin 1982», «Пуазейль»), `on_add` `:314-317` (no `interpolated=True`), `_approx` `:600-607`; plan P15.7's checks
"mass and momentum balance, Poiseuille / Couette references" (`lfphys/PLAN.md:159`); AGENTS §3 rule 2 ("Closed forms
… appear only as references in the run's checks, next to the computed value").

Evidence: no running check compares with DFG, Ghia or Poiseuille; the disk is a staircase at 20 cells per diameter,
which the engine's own test uses as the *negative* control (cD 5.638). Measured: 2D-1 preset mean 5.6465 / 0.01109
(`r03`), 2D-2 preset C_x max 3.367, C_y max 1.045, min −1.082, St 0.2983 (`r04_preset_karman.out`; DFG cDmax
3.22–3.24, cLmax 0.99–1.01, St 0.295–0.305). The airfoil preset (`:105-114`) is periodic in y with a gap of two chords:
a cascade, not an isolated wing; its C_y (0.32–0.41 over the last 2 of 6 s, `r11_airfoil_and_outlet_pressure.out`)
depends on that gap, which is not flagged.

Fix: interpolated walls for static disks/profiles in the presets (the engine supports them); info checks with the
published ranges (DFG 2D-1/2D-2 with the period-averaged values of L4), Ghia's centre-line points for the cavity, the
Poiseuille profile upstream of the plate; flag the cascade (or use walls far away) in the preset label and
`_approx()`.

### L6 (should-fix) — body force: no hydrostatic check, and an outlet that contradicts it

Location: `lbm.py:1885-1890` (`set_gravity` does not call `_check_numbers`), the outlet rule (constant ρ_out along the
side, `:1282-1286`); `viz.py:162-165` (default gy = −9.81; help "в несжимаемой жидкости однородная сила меняет только
давление, если нет свободных границ").

Evidence (`r01`, part b; `r02`, part c): the default gravity in the DFG-sized world (u_max 0.45 m/s, dt 6.4·10⁻⁴ s):
lattice g = 8.07·10⁻⁴, g·H/c_s² = 0.199; after 3 s the density ranges 0.885–1.127, the compressibility check is red
(0.127 > 0.09), and nothing refused the force. With an outlet on the right (0.4 × 0.1 m, g = 0.5 m/s², no inflow) the
fluid at rest develops 0.129 m/s at the outlet's lower corner (mean 0.0085 m/s) after 20 s — above the declared
u_max 0.05; with walls only it stays at 3.9·10⁻¹² m/s. A uniform-pressure outlet is not in hydrostatic balance with a
body force.

Fix: refuse (or warn with the number) a body force whose g·L/c_s² (lattice) over the domain exceeds the
compressibility limit, in `set_gravity` and at world build; impose the outlet pressure with the hydrostatic part
(p_out − ρ0 g·(x − x_ref)) when a body force is on, or state the limitation; correct the help text.

### L7 (should-fix) — outlet pressure unchecked, misleading blow-up message

Location: `Outlet` (`lbm.py:613-621`), `_build` `:1282-1286`, `_check_numbers` `:1091-1119` (checks Mach, τ, cell Re;
not the outlet's density); the message `:1675-1679`; `viz.py:155-156` (range ±10⁹ Pa).

Evidence (`r11_airfoil_and_outlet_pressure.out`, part b): in the DFG world (pressure scale c_s²ρ(dx/dt)² = 20.25 Pa)
an outlet at 10 Pa is accepted (lattice density 1.494) and the first advance blows up at 0.041 s with "Уменьшите
скорость или dx, увеличьте вязкость"; 1 Pa gives ρ 1.049–1.098 and 2 Pa 1.094–1.199 after 1 s, compressibility check
red, Mach 0.05–0.08 from the pressure wave alone.

Fix: refuse |Δρ_out| = |p|/(c_s²ρc²) above the compressibility limit with the reason, and name the outlet pressure in
the blow-up message when it is set.

### L8 (should-fix) — the Kármán preset runs beyond its own limit; the preset test stops in the start-up

Location: preset `karman` (`viz.py:83-91`: u_max 2.0 m/s, declared cell Re exactly 10 = the open-domain limit);
`test_p04_fluids.py:37-45` (runs `2 × default_speed` = 0.22 s for this preset, inside its 0.5-s ramp; 0.17–0.98 s for
the others).

Evidence (`r04_preset_karman.out`, `r04b_series_summary.out`): the measured cell Re passes 10 at t = 0.44 s (10.17,
u = 2.03 m/s) and stays above it 100 % of the samples after 1 s (max 11.24); the final checks: `re_cell: False`. The
engine's own edge for the inlet is ~12 (`r07`), so the preset runs within 7 % of it; any extra disturbance (L1) blows
it up.

Fix: set the preset where the developed flow satisfies the limit (e.g. 880 nodes: cell Re 5.6, or the GPU), and make
the preset test reach the developed flow (on the GPU where given) or at least one flow-through time.

### L9 (should-fix) — DFG 2D-2: the amplitude stands in for cLmax

Location: `test_lbm_benchmarks.py:108-130` (asserts `0.99 <= (max − min)/2 <= 1.01`; docstring "cLmax alone reads
0.980, shifted by the acoustic wave"); module docstring `lbm.py:80-82` ("lift amplitude 0.998 (0.99-1.01)"); README
row; STATUS V41 (p) lists only cD,max; verification note §1 ("lift amplitude … = 0.998").

Evidence: Schäfer & Turek 1996 (Wayback copy of the authors' PDF, text layer): 2D-2 asks for "maximum drag coefficient
cDmax , maximum lift coefficient cLmax , Strouhal number St"; Table 4 "lower bound 3.2200 0.9900 0.2950 2.4600",
"upper bound 3.2400 1.0100 0.3050 2.5000" (columns cDmax, cLmax, St, ∆P). The amplitude is not a benchmark quantity,
and the engine's cLmax at D = 20 (0.980) is outside. The attribution to the acoustic wave is not tested (no run at
lower Ma or with a ramp-only start compares cLmax).

Fix: assert or report cLmax against its bounds (outside at D = 20; measure at D = 40 on the GPU), drop the amplitude
from the docs as a benchmark result, add cLmax to STATUS V41 (p), and test the acoustic explanation (cLmax at Ma 0.05)
or mark it a hypothesis.

### L10 (should-fix) — the coefficient length cannot go back to its default

Location: `viz.py:284-289` (`_ref_len` returns None for 0), `:362-364` (`update_obstacle(..., ref_length=None)`);
`lbm.py:1824-1843` (None means "keep the old value").

Evidence (`r08`, part b): a disk's `ref` set to 0.2 m, then to 0 («0 — диаметр»): the engine's length stays 0.2 m
(should be 0.1 m); C_x and C_y are then half their correct values, silently.

Fix: pass an explicit "default" (e.g. 0.0 → clear) to the engine, or call `update_obstacle` with a sentinel that
resets `ref_length`; test it.

### L11 (should-fix) — the default laws are refused

Location: `viz.py:43-66` (fluid "water", Lx 2.2, Ly 0.41, nx 440, u_max 0.45).

Evidence (`r02`, part a): `Harness(V, None, {})` raises `ValueError: неустойчиво: τ = 0.50008 слишком близко к 1/2`.
STATUS V42 (e) and the README say water and air are refused at these scales; the defaults still point there.

Fix: default to a world that builds (the DFG fluid, or water at a scale it resolves), and test the defaults.

### L12 (should-fix) — the velocity inlet: a transverse layer that grows with the cell Reynolds number; the edge is the inlet's

Location: the inlet rule (`lbm.py:44-46`, `_build` `:1273-1281`, diagonal links sample the profile at the cell edges);
the comment `:157-162`; STATUS V41 (m).

Evidence: (`r13`, part a) a plain parabolic channel started from the exact parabola, 20 000 steps: max |u_y|/U in
the inlet column 0.0040 (cell Re 1), 0.0080 (2), 0.020 (5), 0.038 (10); at column 20: 0.0006–0.0020. (`r09`) the
same channel driven by a body force with periodic ends is stable at cell Re 20 and 60; with the inlet and outlet at
cell Re 20 the transverse velocity is 1.2·10⁻³ (lattice units, 2 % of U) at the inlet column after 32 steps, grows there and blows up at node
(0, 17) at step ~1470. (`r07`) the plain channel with TRT blows up from cell Re 12 (after 8320 steps; uniform inlet
after 1408), BGK survives cell Re 12 for 30 000 steps and fails at 20. (`r09`, part c) at cell Re 10 and 11 the plain
channel runs 10⁵ steps (the limit 10 holds there). The module's note says "BGK, Lambda = 1/4 or 1/12 … did not move
the edge" — true for the cylinder runs it describes, not for a plain channel.

Fix: state the inlet layer (its size against cell Re) in the docstring, the README and STATUS V41 (m); say that the
edge belongs to the inlet (not to the obstacle), with the plain-channel number; the regularised/characteristic inlet
already planned in V41 is the remedy.

### L13 (nit) — "resolved by the grid" is a stability limit

Location: `ABOUT["validity"]` (`lbm.py:121-124`: "ламинарные течения, разрешённые сеткой (число Рейнольдса ячейки
u·dx/ν ≤ 25, с входом или выходом ≤ 10 — измерено)"), p04 README:18 ("refuses a world it cannot resolve").

Evidence (`r12_cell_re_is_not_resolution.out`): the Re 1000 cavity on 64² (cell Re 15.6, accepted, all checks green)
is 0.0171 (u) / 0.0102 (v) of the lid speed off Ghia's Re 1000 columns; on 128² 0.0072 / 0.0112; the Re 100 floor is
0.005 / 0.008 (`r10`). Accepted does not mean resolved.

Fix: call the limits stability limits; give accuracy separately (e.g. this cavity number).

### L14 (nit) — flow rates read zero after an edit

Location: `flow_rates` (`lbm.py:2192-2196`) uses `_owner_sums("last")`, which `_bank` (`:1357-1377`) zeroes at every
edit; `forces()` falls back to `_last_kept`, `flow_rates()` does not.

Evidence (`r13`, part b): before an edit {left: 0.6, right: −0.6616}; right after adding a disk all sides 0.0; one step
later 0.6 / −0.6620.

A frame drawn between an edit and the next step (e.g. while paused) shows these zeros.

Fix: use `_last_kept` in `flow_rates` as in `forces`.

### L15 (nit) — the picture's window says "not an approximation"

Location: `view.js:71` (`exact: true, approximation: false`; the slice window colours the route label red only when
`approximation` is true, `slices.js:206`).

Evidence: the README lists the 2-D model of a 3-D flow, the O(Ma²) compressibility and the staircase walls as
approximations (owner, 2026-10-24: «помечать там, где это приближение»).

Fix: `approximation: true` with the reason (2-D, weakly compressible, staircase), or the route label's `reason`.

### L16 (nit) — block averaging of the picture

Location: `viz.py:210-216`, `:477-480`: solid nodes are set to `lo` before averaging, so mixed blocks next to bodies
read low; `_block` drops `n mod s` trailing rows/columns while the message keeps `size` of the whole domain (a stretch
by up to (s − 1)/n at nx 768, 1024).

Fix: average over fluid nodes only (weights), and send the cropped size (or pad).

### L17 (nit) — numbers and limits that disagree between documents

* 2D-1 at 40 cells: module docstring, README row and verification note "cD 5.5790, cL 0.01075"; the test docstring
  `test_lbm_benchmarks.py:99` "cD = 5.5799, cL = 0.01078".
* Ghia: README row "within 0.005 / 0.008"; the test asserts 0.008 / 0.012 (`:74`).
* p04 README:18 gives only the closed-domain cell-Re limit 25 (the open one is 10).
* The engine docstring's sound amplitude (±1.5 % at Ma 0.1) is for a 3-s ramp (L4).

### L18 (nit) — the conservation bound is loose by three orders

Location: `roundoff()` (`test_lbm.py:24-29`), `checks()` (`lbm.py:2229-2233`): 2 ε per step relative to the total.

Evidence (arithmetic from the test's own numbers): in the test cavity (M0 ≈ 1.7·10³ lattice units, 1500 steps) the
bound is 6.8·10⁻¹³ relative ≈ 1.2·10⁻⁹ mass units, i.e. ≈ 8·10⁻¹³ per step that could leak at a single link
unnoticed; the measured residual is 3.8·10⁻¹⁶ (≈ 1/1800 of the bound). Unbiased rounding grows as √(N·steps)·ε.

Fix: a bound of the form c·√(N·steps)·ε (c ~ 10, derived) plus the sums' rounding, or keep 2 ε but add a mutation
test (a 10⁻¹⁴ leak at one link must fail).

---

## What holds (checked here)

* GPU = CPU bit for bit **[useful]**: in set-ups the shipped test does not cover — periodic sides in both axes with a
  body force, an interpolated and a turning disk, a dye drop; a lid with a periodic pair, a moving rectangle, a dye
  source; obstacles added between runs — populations, dye, link records and forces equal after 400 and 800 steps
  (`r06`); the shipped GPU test passes.
* Moving walls and momentum exchange **[useful]**: Taylor–Couette torque on a turning staircase disk inside a fixed
  cylinder against −4πμΩR₁²R₂²/(R₂²−R₁²): ratio 0.9987 (48²), 0.9999 (96²); the Magnus force has the Kutta–Joukowski
  sign (ω > 0 in a +x stream: F_y = −0.0016 < 0; torque opposes the spin); the momentum booked at a driven lid in steady
  Couette flow equals ±νU/H per unit length to 12 digits (`r05`). Not covered by the shipped tests.
* Bookkeeping through edits in an open channel **[useful]**: a turning disk added, an interpolated disk added, moved and
  removed, with inflow, outflow, a body force and dye: mass, momentum and dye residuals 6·10⁻¹⁵, 6·10⁻¹⁵, 0 after
  7500 steps (`r13`, part c).
* The Ghia remainder is not compressibility **[useful]**: at 64² and 128² the profiles change by 2·10⁻⁴ from Ma 0.1 to
  0.05 (and 1·10⁻⁴ to 0.025), while the difference from Ghia stays 0.005 / 0.008 (`r10`): the note's attribution to
  Ghia's own solution survives this test (it remains unproven against a refined reference).
* The open-domain limit 10 holds for long runs **[neutral]**: the plain inlet/outlet channel at cell Re 10 and 11 runs
  10⁵ steps (`r09`).
* Collision, forcing, boundaries read against the formulas **[neutral]**: Guo's term split into TRT parts adds exactly F
  to each node's momentum and nothing to its mass (worked through by hand; Guo 2002 not obtained); Ladd's moving-wall
  term and its sign (arXiv comp-gas/9306004, Eq. (3.3)); the BFL linear rules and branch coefficients against Marson et
  al., arXiv:2009.04604, Eq. (13a, b) (Bouzidi 2001 itself not obtained); the anti-bounce-back outlet and its velocity
  extrapolation against Ginzburg et al. 2008a, Eqs. (6.2), (6.4) and Tables 9–10 (without the optional correction
  term, as stated).
* Sources quoted by the engine **[useful]**: Ginzburg et al. 2008b Table 4 "BB … 16/3 Λeo − 1" and Table 5 "BB Λeo =
  3/16", p. 521 "enables the bounce-back to locate the prescribed slip velocity exactly midway the link"; 2008a p. 429
  "So far a simple link-wise approach is the first-order accurate anti-bounce-back"; Schäfer & Turek's bounds; the
  water table equals the NIST WebBook isobar at 0.101325 MPa row for row (41 rows, density and viscosity, fetched
  here); USSA 1976 Eq. (51), β = 1.458·10⁻⁶, S = 110.4 K and "basically from kinetic theory, but with constants derived
  from experiment" (printed p. 19, read on a render); Ghia's Re = 100 columns equal the gists the note cites.
* NACA four-digit profile and the angle of attack **[useful]**: NACA Report 460 (Jacobs, Ward & Pinkerton 1933, p. 4,
  read on a render) gives ±y = (t/0.20)(0.29690√x − 0.12600x − 0.35160x² + 0.28430x³ − 0.10150x⁴) and the two-parabola
  mean line; NACA Report 824 (Abbott, von Doenhoff & Stivers 1945) the construction x_U = x − y_t sin θ, y_U = y_c +
  y_t cos θ and the numbering. `naca4` follows them with the closed-trailing-edge coefficient 0.1036 (a common
  modification, stated as such in the docstring and README). The book's "§6.4" was not checked (book not obtained).
  A positive angle lowers the trailing edge for a stream along +x and the lift is +y (test and code agree).
* Layer placement **[neutral]**: `core` is right (incompressible Navier–Stokes, the most complete flow model in the
  engine; validity and numerical errors stated); `conflicts: []` is consistent with LAYERS.md.

## Sources

Obtained and grepped (kept in the scratchpad, not here): Schäfer & Turek 1996 (Wayback copy of the TU Dortmund PDF);
Ginzburg, Verhaeghe & d'Humières, CiCP 3, 427 and 519 (2008) (journal OJS galleys); Ladd, arXiv comp-gas/9306004;
Marson et al., arXiv:2009.04604 (secondary source for the BFL rules); NACA Reports 460 and 824 (NASA NTRS); U.S.
Standard Atmosphere 1976 (NTRS 19770009539); NIST WebBook water isobar (tab-separated data); Ghia's tables as the two
GitHub gists the note cites.

Not obtained: Guo, Zheng & Shi 2002 (APS); Bouzidi, Firdaouss & Lallemand 2001 (AIP); Ghia, Ghia & Shin 1982 (Elsevier);
Qian, d'Humières & Lallemand 1992; Krüger et al. 2017; Abbott & von Doenhoff 1959 (the book). Statements resting on
them are marked above.
