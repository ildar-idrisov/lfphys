# Response (part): LB1-physics — the LBM, p04 and p01 findings

Processed 2026-11-11/12 by a processing agent that wrote neither the review nor the reviewed code. This file covers
P1, P5, P6, P7, P10, P14 and the LBM / p01 parts of P12 and P15. The MD findings (P2–P4, P8, P9, P11, P13 and the MD
parts of P12, P15) are answered in `RESPONSE_p03.md`. Rules: `../README.md`.

Environment: Docker image `light-funnel-viz` (CPU), from `engine/`, containers `lf-lpl-*` with `--memory`; one GPU check
on GPU 0 through the shared `gpu_run.sh`. Scripts and their outputs: `response_checks_p04-p01/` (each script runs as
`docker run --rm -v <engine>:/lf:ro -v <this folder>:/p -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3
/p/<script>.py`; the first lines of each say what it checks).

## Summary

| # | finding | decision | status tag |
|---|---|---|---|
| P1 | running conservation bound not a worst case | fixed at the cause (compensated books, both devices) | [error in earlier] |
| P5 | the spin/charge "what if" is physics in the world | fixed (`theories.alternatives.kn_change_whatif`, tests, listed) | [useful] |
| P6 | silent clamp at 0.999 c; photon frequency reset | fixed (no limit below c; ν kept) | [error in earlier] |
| P7 | the "remap" book blinds the balances | fixed (stated everywhere; a reference a wrong transfer breaks; test) | [error in earlier] |
| P10 | "measured" radial period doubles at a mass change | fixed (passages in seconds, cleared at a change of the hole) | [error in earlier] |
| P12 (LBM, p01) | tolerances, untested core function, memory estimate, dye transfer | fixed (tests; tolerances derived or labelled; the estimate corrected) | [error in earlier] (memory) |
| P14 | a new nx silently changes Ly | fixed (stated in the event with the nx that keep both lengths) | [neutral] |
| P15 (LBM, p01) | Lagrava misprint; Newtonian throw limits; STATUS V42 (l) stale | fixed (citation, docs); the STATUS text is for the integrator | [neutral] |

**Counts (this part): 8 of 8 fixed.**

## Findings

### P1 — the running conservation bound is not a worst case (STATUS V41 (ac))

**Reproduced** (`response_checks_p04-p01/p1_repro.py`, `p1_before.out`): the 4 × 16 body-force channel fails the
momentum check at 9 537 steps (1.698e-11 against 4.235e-12), at 32 000 (5.4e-11 / 1.4e-11) and at 64 000 (6.1e-10 /
2.8e-11); an open channel with an interpolated disk and dye fails from 64 000 steps (3.2e-11 / 2.8e-11). The reviewer's
diagnosis holds: the per-link records grow by the gross exchange every step, so a plain running sum rounds with an
error growing like n² (the body force's impulse and the dye sources' records the same way, more slowly).

**Decision: fixed at the cause.** `lfphys/lfphys/core/fluids/lbm.py`:
* every cumulative record is a Kahan-compensated sum — the per-link mass, momentum and dye records (`LINK_ACC`: `acc_*`
  with `cmp_*`), the dye sources' injected amount (`_src_acc` is now (2, N): sum and compensation) and the body force's
  impulse (`_body_imp` = [x, y, cx, cy]) — on the CPU (`_kahan`) and in the CUDA kernel with the same four operations
  (no multiplication: `--fmad=false` is not even needed for them);
* the per-owner books are summed exactly (`math.fsum` of acc − cmp, rounded once: `_ksum`), also when banked at an edit
  or a remap; older states (without the compensations) restart them at zero;
* the bound stays 2 ulps of the total per step, but its comment, the module docstring and the test helper `roundoff`
  no longer call it a worst case [error in earlier]: they name its two sources (the books, now exact to their final
  rounding; the nodes' unbiased rounding) and the measured margin.

**Verification.**
* `p1_after.out`: the same runs pass; the momentum residual is now 6.1e-14 at 64 000 steps (the reviewer's exact `fsum`
  of every step's records gave 6.8e-14), 2.6e-13 at 256 000; ratio to the limit ≤ 2.3e-3 (momentum), ≤ 4e-4 (mass) over
  the closed channel to 256 000 steps and the open channel (disk, dye source) to 128 000.
* Regression test with a negative control: `lfphys/tests/test_lbm.py::test_the_running_check_holds_on_long_runs` — the
  channel to 64 000 steps, every running check ok and the residuals below 1e-2 of the limit; with `_kahan` replaced by
  a plain addition the momentum check fails at 9 537 steps, as reported.
* GPU 0 (`gpu_parity.out`): `test_gpu_equals_cpu_bit_for_bit` (every link type, the dye with its source, geometry
  changes, ramps) and `test_gpu_equals_cpu_after_a_remap` pass: the compensated kernel equals the CPU bit for bit.
* The existing tight-bound mutation test (`test_the_tight_bound_of_a_closed_domain_and_what_it_catches`) still shows
  what the running bound cannot see (a leak below ~2 eps of the total per step) — documented, unchanged.

### P5 — the "what if" rule lives in the world

**Decision: fixed.** The rule is now the engine's declared alternative
`lfphys/lfphys/theories/alternatives/kn_change_whatif.py` (`carry(geo, chi, q)`, `observer_refusal`, `check_hole`,
`Refused`): ABOUT with layer `theories`, kind `alternative`; its statement and validity say it is a model; its
conflicts say that GR has no instantaneous change of a hole's spin or charge (no experiment tests the rule) and that
the rule depends on the Boyer–Lindquist coordinates (BL coordinates of different (a, Q) do not label the same places;
keeping the circumferential radius, or E, L, K, would give other worlds). The core gained the exact frame algebra it
needs (`kerr_newman.zamo_frame_momentum`, `momentum_from_frame`: γ and γv directly, no 1 − v² near the horizon), with
tests. p01 calls the module (`KerrMode._what_if_metric`), lists it in `engine_modules()` (always in the Kerr world:
the hole's inspector offers it at any moment and the panel is sent with the header), names it in the approximations
and in the event; the event also gives numbers: the body whose E changed most (before → after), the largest change of
the circumferential radius at the bodies, the largest γ kept. README updated.

**Verification.** `lfphys/tests/test_kn_change_whatif.py` (6 tests): the same metric gives back positions, proper times
and statuses bit for bit and the spatial momenta to rounding (the energy is re-taken from the mass shell, so E moves by
the body's own shell drift — derived tolerance); the ZAMO velocity read back through the core's independent
`zamo_velocity` equals the old to the shell drift (|Δv| ≤ |v||Δμ²|/(2e²)) for four target metrics; a photon's ZAMO
frequency kept; the closed form Schwarzschild → Reissner–Nordström (E = √(1 − 2/r + Q²/r²) for a body at rest for its
ZAMO, E = αγ, L = rγv_φ for a tangential one); refusals (no horizon; a body inside the new capture radius, named; the old
geodesics untouched); a captured body held just outside the new horizon; observers' refusals.
`lfphys/tests/test_kerr_newman.py::test_zamo_frame_momentum_and_back`. The p01 tests (below) use the module through the
world. `tests/test_layers.py` passes (layer, kind, conflicts).

### P6 — the silent clamp at 0.999 c; photons' frequency reset

**Reproduced** from the code: `vv = vz * min(1, 0.999/|vz|)` and `momentum_from_zamo(..., n=...)` with ν = 1.

**Decision: fixed** by the rule above: the ZAMO-measured momentum is kept and the energy taken from the mass shell, so
there is no limit below c and nothing to cut (refusing was not needed: any |v| < 1 is carried); a photon keeps its
ZAMO-measured frequency.

**Verification.** `test_kn_change_whatif.py::test_no_limit_below_c_near_the_horizon` (γ = 22.4 at 4.1e-4 above the
horizon of a = 0.9 kept to 1e-9 relative across a → 0.95; the control shows the former clamp would move |v| by 3e-6);
`visualizations/p01_gravity/tests/test_p01_lab.py::test_the_what_if_is_the_engines_rule_without_a_speed_limit` (a body
falling past γ = 25 in the world keeps γ across the change; the former rule would have left 0.999); the photon test
above. Browser: `p01_whatif_event.png` (the event naming the module, the circumferential radius's change and the γ kept).

### P7 — the "remap" book makes the balances blind to the transfer

**Reproduced** in a p04 world (the reviewer's mutation: the transferred velocity × 1.01): the momentum check stays ok,
the profile is ~1e-2 off.

**Decision: fixed.** (1) Stated: the `remap` docstring and the module docstring (`lbm.py`), p04's README and p04's event
now say that the balances close by construction across a remap and cannot see an error of the transfer [error in earlier:
p04's test and README cited those checks as evidence]. (2) A check a wrong transfer breaks, in the world: p04's
«Эталоны» gained the body-force Poiseuille channel (periodic ends, fixed walls, g_x only: u = g_x y (H − y)/(2ν)),
shown whenever the scene is that set-up. (3) The p04 test asserts it.

**Verification.** `p04_fluids/tests/test_p04_lab.py::test_a_wrong_transfer_is_seen_by_the_reference_not_by_the_balances`:
nx 16 → 32 and a new u_max keep the profile on the parabola to < 1e-9 of the peak with every check passing; with the
transferred velocity × 1.01 the momentum check still passes (documented) while the reference is > 3e-3 off. The engine's
closed-form tests of the transfer (Poiseuille with negative controls, Taylor–Green, now the dye's second moment: P12)
are the transfer's own check. Browser: `p04_force_poiseuille_nx32.png` (the event's sentence and the «Эталоны» row).

### P10 — the "measured" radial period across a change of the hole

**Decision: fixed.** The periapsis passages are recorded in world seconds as they happen (`self.clk.sec(tc)`), and
cleared when the hole's mass changes (`_rescale_mass`) and at a «what if» (`_what_if_metric`); the period is undefined
until two new passages, with the reason in `meas_note`.

**Verification.** `test_p01_lab.py::test_the_radial_period_restarts_when_the_hole_changes_and_the_throw_limit`: a
measured period becomes NaN with the reason at M 10 → 20 (before: it doubled without a passage), then is measured again
as exactly twice the old one (the same orbit in units of M, 1e-3), and NaN again after a spin change.

### P12 — tolerances and coverage (the LBM and p01 parts)

**Decision: fixed.**
* `Geodesics.rescale_proper_time` has an engine test: `test_kerr_newman.py::test_rescale_proper_time_reads_the_same_clocks_in_another_unit`
  (exact rescaling, nothing else touched; the continued orbits agree to 3e-14 in position, 5e-12 in momentum, 2e-13 in
  the clocks — `rescale_meas.out`; refusals).
* `remap_memory_estimate` against the measured peak (tracemalloc; `remap_mem.py`, `remap_mem.out`): it fell short of a
  coarsening by 8 % (dye) and 15 % (no dye) [error in earlier]; the per-node coefficient of the present grid is now 1000
  / 800 B (fitted 723 / 603 B); test `test_lbm_remap.py::test_the_remap_memory_estimate_bounds_the_measured_peak`
  (refine, coarsen, new time step, with and without dye: the peak within 0.3–1 of the estimate).
* The dye's transfer: `test_lbm_remap.py::test_the_dye_is_carried_through_a_refinement_by_its_second_moment` (the
  reviewer's second-moment check: the offset from S0² + 2Dt moves −3.6e-4 in the 50 time units after the refinement,
  no more than either grid alone; with the rescaling switched off it jumps −0.041: `dye_moment.py`, `dye_moment.out`).
* Tolerances: Taylor–Green's 2e-4 is now tied to a derived scale (the four-point interpolation's bound at a quarter
  cell, 0.41/24 (kh)⁴ per axis: 5.1e-5 of the amplitude; measured 7.5e-5; the assertion four times the scale) and its
  1.2× / 0.5× margins to the second order's ratio 4 — said in the docstring as measured margins around derived scales;
  the p01 lab test's rtol 1e-7 bounds the sum of the local errors (128 accepted steps per body at rtol 1e-10: 1.3e-8;
  said where it is used).

### P14 — a new nx silently changes the domain

**Decision: fixed (stated, not refused).** When nx does not fit a whole number of cells into Ly, p04's event gives the
new height and the nearest nx that keep both lengths (for 2.2 × 0.41 m: 440, 220), and says when the DFG set-up is no
longer recognised by «Эталоны». Refusing would block most nx values for most domains; the owner sees what happened.

**Verification.** `test_p04_lab.py::test_a_new_nx_states_the_new_height_and_the_scheme_compressibility` (nx 333: «высота
области 0,41 → 0,40961 м», «nx = 440, 220», «DFG больше не узнаётся»). Browser: `p04_nx333_height.png`.

### P15 — documents (the LBM and p01 parts)

**Decision: fixed.**
* Lagrava's misprint checked against the thesis text (Eq. (4.12) reads α = δt_c τ_f / (δt_f τ_c); (4.13)'s middle member
  δt_f τ_c / (δt_c τ_f) contradicts its right-hand side 2τ_c/τ_f at δt_f = δt_c/2, which (4.14)–(4.15) follow): `lbm.py`'s
  `remap` docstring and its ABOUT now cite (4.1), (4.10), (4.11), the right-hand side of (4.13), (4.14)–(4.15) and name the
  misprint.
* The Newtonian throw: the code comment and p01's README now say that the player clamps a throw to 0.05 c, the world
  accepts up to 0.1 c (Newtonian, v²/c² ≤ 1 %) and refuses from 0.1 c, and that the hidden parameters' wider range only
  lets that refusal speak.
* STATUS V42 (l) and V41 (ac): texts for the integrator (the processing agents do not edit STATUS), in the coordinator's
  report.

## Also changed while processing (not findings of this review)

* `Flow2D.adopt` (engine) for review LB1-framework F5 (p04's carry-over); `RESPONSE_p04-p01.md` in that review's folder.
* p01 Kerr bodies declare a throw limit (review LB1-p02-ux X4); p04's u_max event explains the mass change (X14):
  `../2026-11-11_internal_LB1-p02-ux/RESPONSE_p04-p01.md`.

## Tests run (2026-11-12, CPU, Docker; outputs in `response_checks_p04-p01/`)

* Engine: `test_lbm.py`, `test_lbm_remap.py`, `test_lbm_live.py`, `test_lbm_benchmarks.py`, `test_kerr_newman.py`,
  `test_kn_change_whatif.py`, `test_boundary.py`, `test_layers.py`, `test_licences.py`: 368 passed, 4 skipped (GPU).
* GPU 0 once: `test_gpu_equals_cpu_bit_for_bit`, `test_gpu_equals_cpu_after_a_remap`: 2 passed.
* p04, p01 and the framework's `test_carryover.py`: 93 passed, 1 skipped; the two lab files again after the last edits:
  21 passed.
* `tests/test_checkpoint.py tests/test_restore.py -k "p04 or p01"`, twice: 6 passed, 6 passed.
* Browser, private server: `keyframes.mjs` p04, p01 — all equal; `manipulation.mjs` p01, p04 at 1600 × 1000 — 9 of 9; the
  same with p01's Kerr preset — 5 of 5 (the Kerr throw applied, unit shown); screenshots `*.png` (each looked at).
