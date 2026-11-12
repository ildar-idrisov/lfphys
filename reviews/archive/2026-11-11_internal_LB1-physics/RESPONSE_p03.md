# Response (p03 and molecular dynamics part): review LB1-physics, 2026-11-11

Processed 2026-11-12 by a processing subagent (prefix `lf-lpm-`), not the review's author and not the author of the
code. Scope of this response: P2, P3, P4, P8, P9, P11, P13 and the molecular-dynamics parts of P12 and P15. P1, P5–P7,
P10, P14 and the other parts of P12 and P15 are answered in `RESPONSE_p04-p01.md`.

Every finding was reproduced first (`response_checks_p03/before_*.out`). The checks ran in Docker on the CPU
(image `light-funnel-viz`, Python 3.11, NumPy 2.4), the browser checks with Playwright 1.58.2 (Chromium, SwiftShader)
against a private server on port 8614.

## Summary

| ID | finding | decision | tag |
|---|---|---|---|
| P2 | −P dV with the virial pressure is not the first-order work with a field, soft walls or frozen atoms | fixed | [error in earlier] |
| P3 | a live box change is one jump; the slow-limit test cannot see irreversibility | fixed | [error in earlier] |
| P4 | MD walls on centres, hard walls on surfaces | fixed | [error in earlier] |
| P8 | the wall mode says «no work» next to a soft wall | fixed | [error in earlier] |
| P9 | «phase-space volume kept» holds only relative to the centre of mass | fixed | [neutral] |
| P11 | p03's restore test compares only drawing positions | fixed | [useful] |
| P12 (MD) | tolerances of `test_md_deform.py` measured, not derived | fixed | [neutral] |
| P13 | the bisection ignores the bond limit | fixed | [neutral] |
| P15 (MD) | STATUS V42 (l) is stale | open → integrator (STATUS text below) | [neutral] |

Found while processing (in `../2026-11-11_internal_LB1-framework/RESPONSE_p03.md`, F5): p03's solver started at time 0
in a world built from a scene with a later time, so its first advance computed the whole interval [error in earlier].

Counts for this file: 8 fixed, 0 partly, 0 rejected, 1 open (the STATUS text, to the integrator).

## Findings

### P2 — first-order work with the affine stress

**Reproduced.** `before_md_deform_checks_CDE.out`, part C: (dE − pdv)/dE = −0.608 (field), +0.188 (soft walls),
−0.359 (frozen atoms) at δ → 0. The periodic control converges as δ².

**Cause.** `MD.deform` built its trapezoid from the virial pressure. That pressure leaves out three forces the affine map
does move: the field (Σ m g_a x_a), the soft walls (Σ z F_z, with the hi wall moving with the box), and the frozen
atoms (the virial is Clausius' of the mobile atoms, but `deform` scales the frozen atoms too).

**Fix.**
- `_compute_forces` now also keeps the affine virial W^aff: −dU/dδ_a over every force the map moves. That is the pairs,
  Coulomb, bonds and angles over all their pairs, the soft walls' Σ z F_z and the field's Σ m g_a x_a (unwrapped).
- `MD.affine_stress()` = (2K + W^aff)/V.
- `MD.virial_is_affine(axes)` is true where the stress equals the virial pressure: no frozen atom, no field component
  along the axis, no soft wall across it.
- `deform` returns `pdv` from the affine stress, plus `S0`, `S1`, `pdv_virial` and `virial_is_affine`.
- The docstrings of `deform` and of the module state the condition.
- p03's event says «−P·ΔV по вириалу» only where the two agree. Elsewhere it says «−∫S dV по аффинному напряжению … это
  не давление вириала». The README row was corrected as well.

Files: `lfphys/lfphys/core/md/system.py`, `visualizations/p03_molecules/viz.py`, `visualizations/p03_molecules/README.md`.

**Verified.**
- `after_md_deform_checks_CE.out` is the reviewer's own script, unchanged. Its ratios are now −1.6e-6 / −1.6e-8 /
  −1.4e-10 (field), −2.2e-5 / −2.2e-7 / −2.2e-9 (soft walls) and −2.7e-5 / −2.7e-7 (frozen atoms): all O(δ²).
- `test_md_deform.py::test_first_order_work_is_minus_the_affine_stress_times_dv` covers four systems. The ratio must
  fall ×100 per decade, a derived order, asserted within 20 %. The negative control: the virial trapezoid misses by
  more than 0.1 at every δ in the three affected systems.

### P3 — a change of the box over a time

**Reproduced.** `before_md_deform_checks_B.out`: a single 15 % jump and back leaves +182.6 ε. In the test's spacing,
64 steps leave +17.6 ε while Σ(W − PDV) converges. So the old "slow" test could not see dissipation.

**Fix.**
- **Engine.** `MD.ramp_box(L, duration)` changes the box linearly in time. After every integrator step it makes one
  small affine step, exactly the jump's canonical map (`_affine_map`), then recomputes the forces at once. The energy
  change of that substep is booked as the work W_box, so the work is exact and integrated.
- The record (`box_ramp()`) holds W, the trapezoid of −∫S dV over the substeps, the steps, start, end, and whether the
  ramp was stopped.
- Refusals:
  - more than 0.1 % of a length per step (then a longer time, or `deform` for a jump);
  - the piston's axis;
  - the cutoff beyond half a periodic length at the end.
- A substep with non-finite forces, or with the cutoff growing beyond half the box, is not made: the ramp stops there
  and says why.
- While a ramp runs, `deform` and a piston on a changing axis are refused.
- The momentum check's rounding bound counts the ramp's substeps.
- The ramp is in the plain-data state (bit-identical continuation).
- **p03.** A new live law «Время изменения размера, пс (0 — скачком)». The default is 50 ps; 0 gives the jump.
  - At the start, the event gives the faces' speed against the atoms' thermal speed, and the view gets the region the
    change spans.
  - Every frame shows the box reached.
  - At the end, an event gives W, −∫P dV (or −∫S dV) and the temperature, and the final `box` message follows.
  - A new size stops the running change where it is; so does the switch to hard spheres. Both are said.
  - A change heating the matter beyond what the time step resolves is stopped and said.
  - An end beyond close packing at contact σ is refused.
  - The jump's event now says it is not quasi-static. The help texts give the measured sizes.

**Size, measured in p03** (`p03_ramp_heating.out`; Maxwell preset: 300 argon atoms, 2-D, 300 K, 12 → 11 → 12 nm,
4 seeds). Heat left per atom:

| change | heat per atom | as a temperature |
|---|---|---|
| jumps | 0.133 ± 0.018 ε | ≈ 16 K |
| 10 ps each way | 0.006 ± 0.005 ε | ≈ 0.7 K |
| 50 ps each way | 0.005 ± 0.002 ε | ≈ 0.6 K |
| 200 ps each way | 0.000 ± 0.001 ε | 0 ± 0.2 K |

**Engine prototype** (`proto_ramp.out`; the review's 2-D LJ fluid, 100 atoms, 15 % cycle). The net work per atom is
1.15 ε for jumps, 0.086 at τ = 1, and within noise (|mean| ≤ 0.01) from τ = 4 on. With 400 atoms in a box twice as large:
1.10, 0.093, 0.023, then within noise from τ = 16 on (the sound crossing time grows with the box).

Files: `system.py` (`ramp_box`, `box_ramp`, `stop_box_ramp`, `ramp_running`, `_ramp_substep`, `_affine_map`,
`momentum_drift`, state), `p03_molecules/viz.py` (`_set_box`, `_start_ramp`, `_stop_ramp`, `_follow_ramp`,
`_ramp_text`, the schema), README.

**Verified.**
- `test_a_slow_ramp_is_reversible_and_a_jump_dissipates`: four seeds; tolerances from the seeds' standard errors.
  - The jump dissipates: mean 115 ε > 3 SE.
  - τ = 1 dissipates measurably (> 3 SE), and less than a fifth of the jump.
  - τ = 8 is within 3 SE of 0 and below 2 % of the jump.
  - The fast ramp exceeds the slow one by more than 3 combined SE.
  - Negative control: the jump.
- `test_ramp_of_an_ideal_gas_is_the_adiabat_and_agrees_with_a_slow_piston`, the second method the review asked for:
  the ramp keeps K_y L² to 1e-12, and the driven piston approaches it and the ramp's work as w falls (0.05 → 0.01).
- `test_ramp_books_its_work_keeps_momentum_continues_bit_for_bit_and_refuses`.
- p03: `test_live_box_over_a_time_is_a_ramp_with_its_work_and_an_end_event`,
  `test_a_new_size_stops_the_change_running_and_a_too_fast_one_is_refused`,
  `test_switching_to_hard_spheres_stops_the_change_and_says_so`.
- Browser, `p03_lab_shots.out`: 12 → 8 nm over 20 ps. The start and end events appear on the page; an intermediate box
  is visible (`p3_box_mid.png`: the x wall at about 10 nm inside the 12 nm region), and the end toast with
  W = +353.1 kJ/mol and −∫P dV = +353.1 (`p3_box_end.png`).
- The restore test now ends with a ramp still running and compares the whole engine state (P11).

**Not done.** Hard spheres still change the box only by a wall. An affine change is refused there, because an affine
step does none of the collisional work; a slowly moving wall in the event-driven solver would be the fix. This is the
earlier agent's proposed STATUS item, repeated below.

### P4 — the same walls on both sides of the switch

**Reproduced.** `before_md_deform_checks_CDE.out`, part E: 170 of 200 moments refused by the walls only (n 20, L 20),
and a 7–11 % denser region for the hard bodies.

**Fix.**
- `HardSpheres(walls_on="centre")`: the walls act on the centres (x ∈ [0, L]), as MD's hard walls do. It applies to the
  calendar's wall events, `_check`, the contact planes of the pressure, and `contact_violations(..., walls_on=)`.
- `hard_from_md` creates the hard system with walls on the centres by default.
- `md_from_hard` reports `centres_region_grew` when it starts from walls on the surfaces.
- The default for other users of `HardSpheres` stays `"surface"`, and the docstrings state both conventions.
- p03 builds its hard world, fresh or switched, with walls on the centres. A drag in the hard world uses the centres'
  range.
- The switch event says «стенки действуют на центры атомов … область центров и плотность не изменились».

Files: `lfphys/lfphys/core/md/hard.py`, `p03_molecules/viz.py`, README.

**Verified.**
- `test_hard_walls_contact_plane_by_the_virial_identity[centre|surface]`: d/dt Σ m y v_y = 2K_y + Σ y F, integrated
  over 50 time units. The identity closes to 1e-9 with the contact plane at the wall (centre) or at σ/2 (surface).
  The other plane misses: the negative control. The axis's virial pressure equals the walls' impulse pressure within
  10 %.
- `test_switch_with_walls_on_centres_is_never_refused_by_the_walls`: the review's n 20, L 20 case gives 0 refusals of
  40 with centres against more than 10 with surfaces (the control). The round trip keeps every position.
- p03: `test_switch_in_a_walled_box_keeps_the_region_of_the_centres`: an atom 0.05 nm from a wall; the event text; the
  fresh hard world.
- `test_md_deform.py::test_switch_to_hard_refuses_overlaps_and_what_it_has_not`: surface walls refuse, centre walls
  switch.

### P8 — the wall mode next to a soft wall

**Reproduced.** `before_p03_softwall_wallmode.out`: W_box = +1.153 ε, and the event said «работы над системой нет».

**Fix.** The event states W when it is not 0 («мягкая стенка сдвинулась под атомами у неё — работа над системой
W = …»). Otherwise it says «работы нет (зеркальные и тепловые стенки по пустому месту); расширение в пустоту
необратимо». README corrected.

**Verified.**
- `after_p03_softwall_wallmode.out`, the reviewer's script: «… работа над системой W = +1,148 кДж/моль». That is
  1.1527 ε × 0.996 kJ/mol per ε.
- `test_wall_mode_next_to_a_soft_wall_states_its_work`, with a specular control that says «нет».

### P9 — the Jacobian

**Fix.** The docstrings of `deform` and of the module, and the README and BOX_HELP texts, now say what the review
points out: the map is canonical for the motion relative to the centre of mass; along a conserved axis it moves the
centre of mass by λ with its momentum kept, so the Jacobian is λ per such axis.

**Verified.** `test_jacobian_is_one_relative_to_the_centre_of_mass` differentiates `deform` itself numerically on three
particles. It gives det J = 0.9 × 1.1 (periodic: both axes conserved) and 1 (walls), to 1e-6.

### P11 — the restore test

**Fix.**
- `test_live_box_switch_and_drags_are_replayed_by_a_restore` now compares the whole `md.state_dict()`: positions,
  velocities, the generator, energies, the books and the running ramp. It does so at the end of the record and again
  after both worlds advance 1 ps more.
- It uses a recursive bit-exact comparator. The old `repr` comparison could hide differences in long arrays.
- Negative control: one velocity changed by one unit in the last place is detected.

**Verified.** It passes, and `test_checkpoint.py` / `test_restore.py -k p03` passed twice.

### P12 (molecular dynamics part) — derived tolerances

The measured margins at `test_md_deform.py:126, 128, 130` belonged to the "slow deformation" test, which mixed
dynamics into the path. That test was replaced:
- `test_trapezoid_of_a_pure_deformation_converges_at_second_order`: the same configuration path for every N. The ratio
  is ×4 per doubling (derived, asserted within 20 %), the work is independent of N, and the first law is exact.
- The first-order test above: ×100 per decade.
- The reversibility test: tolerances from the seeds' standard errors.

One sanity margin remains, labelled as such: the first law's residual is below 1 % of the compression's work at the
integrator's level. The other P12 items (`rescale_proper_time`, `remap_memory_estimate`, the dye) are not
molecular dynamics.

### P13 — the bisection's bond limit

**Reproduced as stated, but not reachable in p03** (`repro_p13.py`). `deform` checks the bonds at the asked size before
the overlap, so an overlap refusal implies the asked size passed the bond limit. A strain along the bisection's path is
monotone when all axes change in one direction. With opposite directions the interior extremum is below 0.5 %.

**Fixed anyway** for consistency: every trial passes `max_bond_strain=MAX_BOND_STRAIN`.

**Verified.** `test_the_size_named_after_an_overlap_respects_the_bond_limit` drives the bisection with a 30 % change of
a box with molecules:
- all 10 trials carry 0.10;
- the named size is within 10 %;
- the control (the same bisection without the limit) names more than 90 % of the 30 %.

### P15 (molecular dynamics part) — STATUS V42 (l)

STATUS.md is the integrator's. The text is below.

## Tests run (final, Docker CPU)

- Engine: `test_md_*.py` (8 files) plus `test_boundary.py`, `test_layers.py`, `test_licences.py`: 376 passed,
  4 skipped (GPU) (`final_engine_tests.out`).
- p03: all three files plus the shared `test_carryover.py`, `test_playground.py`, `test_manipulation.py`: 105 passed
  (`final_p03_tests.out`); `test_instruments.py` and `test_sweeps.py` passed in an earlier run of this processing.
- `test_checkpoint.py` and `test_restore.py -k p03`: 3 passed, twice (`final_checkpoint_restore_p03_x2.out`).
- Browser: `keyframes.mjs p03_molecules` — all equal, 6 cursors, 14 key frames (`keyframes_p03.out`);
  `manipulation.mjs` for p03 — 4/4 (`manipulation_p03.out`); `p03_lab_shots.mjs` — 4/4.
