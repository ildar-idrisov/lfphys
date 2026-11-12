# Response to the review UX-ui (2026-11-04): the playgrounds p03 «Частицы и молекулы» and p04 «Жидкости»

Processed by a working session other than the review's author (2026-11-05), for the findings assigned to p03 and p04 and
the engine modules behind them (`lfphys.core.md.*`, `lfphys.core.fluids.lbm`). Other agents process the framework
(player, server), the 3-D view and the other worlds; this file answers only for p03 and p04. Checks, scripts and
screenshots: `response_checks_p03-p04/` (scripts in `scripts/`, outputs in `out/`, screenshots in `shots/`).

The owner's words that set the goal (2026-11-04, verbatim): «в плейграунде, не выставляются часть объектов, …
плейграунд должен быть больше похож на плейграунд, где я могу ставить эксперименты в рамках одного мира, а не
перезапускать его постоянно и должно быть больше интерактива, когда я что=то добавляю, меняю условия и вижу результат в
реальном времени, должно быть больше возможностей по изменения нужных и важных параметров и добавлению новых объектов
для проверки взаимодействия».

## Summary

| finding | decision | one line |
|---|---|---|
| U4 (world side) | fixed | p03 and p04 place every palette object where it can exist (`place`), or refuse in Russian with the fix |
| U5 | fixed | molecule edits in one engine edit; dense requests refused at once: 34 s → 2.3 s (chains), > 90 s → 0.004 s (refused), 2.9 s → 0.09 s (bent) |
| U6 | fixed | the hard world with an atom at rest runs (the division by zero in the pressure is gone at its cause) |
| U7 | fixed | p04 «Объёмная сила» placeable in every world; p03 «Стенка», «Поршень» in a periodic box (the axis becomes walled); p03 «Кристалл» in a non-empty scene (occupied sites left empty) |
| U8 | fixed | p04 bodies, probes and dye outside the domain refused (or brought in when placed from the palette); p03 probes and thermostat regions outside walls refused; Russian texts |
| U12 | fixed | live: p03 pair model, cutoff, shift, time step; p04 ν, ρ, collision operator, dye on/off and its diffusivity; every other law stated with the reason it stays a world parameter |
| U13 (wording) | fixed | the engine's refusals in p03 (English) and p04 (Russian with «dt») put in the world's terms, with the number to use |
| U15 | fixed | p04: the flow's plane is the main view (the 3-D view on request): 330×140 → 690×145 px (channel), 328×310 → 688×670 px (cavity) at 1280×800 |
| U19 | fixed | every p03/p04 label checked for its unit; one fixed («Концентрация (доля)»), the others carry theirs |

Follow-up (2026-11-05): p03 scene files of the old format (one combined «model») load unchanged in meaning, with a
notice (U12 below). Counts: 9 fixed, 0 partly, 0 rejected, 0 deferred (new open items that these fixes revealed are listed under «Changes
for the integrator»). Tests: engine `lfphys/tests` (md, lbm, boundary, layers, licences) 404 passed, 7 skipped; p03 and
p04 tests with the shared checkpoint and restore tests for them 86 passed (after the follow-up: p03 with its shared tests 51 passed); `keyframes.mjs` for p03 and p04 on the
private server: «all equal». Every run in Docker on the CPU (`LFPHYS_NO_GPU=1`).

## U4 — a new object lands where it can exist, or is refused with the reason and the fix (world side)

**Reproduced** (`out/shots_before.jsonl`, `shots/before_p03_wall_piston.jpg`): in p03 a second «＋ Атом» and every ⧉
copy of an atom landed on the first and were refused («refused: two interacting particles at the same point»); the
default crystal in a scene with a gas was refused («overlap: … 7.5e+27»); in p04 inlets, outlets and periodicity were
refused when their side was taken, and a body's copy lay on its original.

**Fixed**, through the framework's `place(kind, values)` (the integrator's API of 2026-11-05: asked for every palette
add, deterministic, replayed by a restore) and the sections' checks at every add and edit:

* p03 (`p03_molecules/viz.py`: `place`, `_free_spot`, `_atom`, `_piston_position`, `_pack_check`): an atom goes to the
  nearest free spot (no atom nearer than σ_ij, inside the walls by σ/2, below the piston: a fine grid around the asked
  point, then a coarse one over the box); a ⧉ copy likewise; a crystal fills only the free sites of its lattice
  (`MD.fill(..., skip_occupied=True)`, new in the engine; the count is in the inspector and a note); a piston goes above
  the highest atom on its axis; a clicked point is an atom's place, a region's centre or the nearest face for a wall or
  a piston. An atom moved by hand onto another or outside the walls is refused with the nearest free spot («ближайшее
  свободное место — (x, y) нм»).
* p04 (`p04_fluids/viz.py`: `place`, `_free_body`, `_into_fluid`, `_claim`): the palette's defaults are made for the
  world (positions and sizes in proportion to the domain, speeds a fraction of the speed it resolves, the body force the
  largest it carries); a side object takes its side when free, else the first free one (a note says so), periodicity
  the free pair; a body that would cover another moves to the nearest free place (a copy likewise); a probe or a dye spot
  asked inside a body goes to the nearest fluid node. Moving an object by hand onto a taken side is refused with the
  free sides named.
* Notes for what was done instead of what was asked are events with `notify: true` (toasted live by the framework).

**Engine** (`lfphys/lfphys/core/md/system.py`, `hard.py`): `free_sites` and `MD.fill` / `HardSpheres.fill` with
`skip_occupied`; tests `lfphys/tests/test_md_placement.py::test_fill_skips_occupied_sites` (the skipped sites counted by
brute force; negative control: without the flag the overlap is refused as before).

**Verified**: `p03_molecules/tests/test_p03_ux.py::test_atoms_land_on_free_spots_and_an_occupied_one_is_refused_with_the_nearest`,
`::test_a_crystal_in_a_gas_leaves_the_occupied_sites_empty`, `::test_a_wall_and_a_piston_on_the_default_periodic_box`;
`p04_fluids/tests/test_p04_ux.py::test_side_objects_take_a_free_side_and_none_is_left`,
`::test_bodies_land_free_and_outside_is_refused`, `::test_a_probe_inside_a_body_says_so`,
`test_p04_fluids.py::test_one_condition_per_side_and_a_removed_inlet_gives_the_wall_back` (rewritten: a palette outlet on
a taken side lands on the first free one; a hand edit onto a taken side is refused with the free sides named);
restores of placements by replay: `test_p03_ux.py::test_live_laws_and_placements_are_replayed_by_a_restore`,
`test_p04_ux.py::test_live_laws_and_placements_are_replayed_by_a_restore` (populations bit for bit).

## U5 — molecule edits block the world for 30–40 s

**Reproduced** (`scripts/lat.py`, `out/lat_before.jsonl`; harness, CPU, OMP 2, host load ≈ 12, so the review's numbers
under load 50–60 are about three times these): in the preset «molecules» (3-D, 150 dimers) «shape = chain» 34.0 s,
«count = 2000» and chains of 50 atoms > 90 s (killed), 600 molecules 26.9 s; in a 2-D box 2000 molecules > 90 s, 20
chains of 50 atoms 72 s and then refused; a 3-D gas of 20 000 atoms > 90 s, of 12 000 atoms 24.3 s.

**Cause**: `_molecules` tried random placements one at a time, each an engine transaction (a deep copy of the state and a
force computation: O(N) per try, up to 200 tries per molecule), and nothing refused a request that random packing
cannot fit; the gas's random sequential insertion was a Python loop per candidate.

**Fixed**:
* engine `MD.add_molecules(species, X, bonds, angles, v | T, max_energy, limit)` (`core/md/system.py`): many candidate
  molecules in one transaction; a candidate closer than 0.9 σ_ij to an earlier one is left out first (the earlier one
  wins, as one at a time), then every candidate over the energy bound (the same per-atom energy as `add`'s refusal), until
  none is; the first `limit` kept in order. p03 draws the candidates for all the molecules still missing at once and
  repeats until all are placed (at most 200 tries per molecule); a removal takes all the object's atoms in one edit;
* engine `random_sites` vectorised (`_SiteIndex`: candidates against the placed points by cells, then in order against
  each other); for PCG64 a batch may draw more candidates than needed and give back the unused draws (`advance` modulo
  2^128): **the same points in the same order and the same generator state as the one-at-a-time algorithm**, checked on
  48 configurations (`scripts/rs_equiv.py`) and in `test_md_placement.py::test_random_sites_equals_one_at_a_time` (24
  cases against a copy of the old algorithm, the second method); 11–13 times faster (20 000 points: 0.06 s / 0.33 s
  against 0.87 s / 3.7 s in 2-D / 3-D);
* p03 `_pack_check`: a gas or molecules whose covered fraction (with the atoms already in the region) exceeds where random
  insertion jams (atoms 0.50 / 0.35, molecules 0.40 / 0.28 in a plane / the volume) are refused at once with the count
  that fits; a frame is no longer blocked by a large scene: an advance call is cut to the steps the modelled cost
  (`md_step_model`, deterministic) allows in 40 ms.

**Latencies of one edit, before → after** (`out/lat_before.jsonl`, `out/lat_final.jsonl`, `out/lat_large.jsonl`; the
same harness, machine and load):

| edit | before | after |
|---|---|---|
| «molecules», shape → bent | 2.86 s | 0.086 s |
| «molecules», shape → chain (6 atoms) | 33.96 s | 2.25 s |
| «molecules», start → «всё при T» | 1.54 s | 0.071 s |
| «molecules», ⧉ copy | 2.49 s | 0.137 s |
| «molecules», sz = 2 nm | 2.09 s | 0.066 s |
| «molecules», count = 600 | 26.93 s | 1.17 s |
| «molecules», count = 2000 | > 90 s (killed) | 0.004 s: refused, 66 % of the volume > 28 % |
| «molecules», chains of 50 atoms | > 90 s (killed) | 0.004 s: refused, 124 % > 28 % |
| 2-D, 250 dimers added | 1.50 s | 0.16 s |
| 2-D, 2000 molecules added | > 90 s (killed) | 0.000 s: refused, 253 % > 40 % |
| 2-D, 20 chains of 50 atoms added | 72.2 s, then refused | 0.000 s: refused, 63 % > 40 % |
| 3-D gas of 12 000 atoms | 24.31 s | 2.80 s |
| 3-D gas of 20 000 atoms | > 90 s (killed) | 0.000 s: refused, 48 % > 35 %, with the count that fits |
| 2-D gas of 20 000 atoms | 4.99 s, refused in English | 0.000 s, refused in Russian with the count that fits |

The remaining 2–3 s (chains in a dense 5 nm cube, 12 000 atoms at 29 % of the volume) are the tail of random insertion
near jamming, not overhead. No progress indicator was added: the framework's pending state is the framework's (U9).

**Verified**: `test_p03_ux.py::test_molecule_edits_are_quick` (six edits with time bounds; the dense ones refused in
Russian), `::test_a_large_gas_is_refused_at_once_with_the_count_that_fits` (and that count placed);
`test_md_placement.py::test_add_molecules_*` (the bound on every kept atom; overlapping candidates; the result equals
`add_molecule` for each kept candidate in turn — energy to 1e-12 and positions; a refused edit leaves the state; a
crowded batch of 600 candidates still places 150).

## U6 — hard disks + «＋ Атом» → ZeroDivisionError

**Reproduced** (`shots/before_hard_atom.jpg`): the frame after «＋ Атом» in the hard world stops the world: «деление на
ноль (ZeroDivisionError)». **Cause**: `HardSpheres.pressure` computed Z = 1 + W/(d N T Δt) with T = 0 (a single atom at
rest; also any cold gas). **Fixed at its cause** (`core/md/hard.py`): at T = 0 the pressure is 0 (the mechanical pressure
is defined) and Z has no value (None); the degrees of freedom guarded likewise. p03's «одинаковая скорость» with one
atom or at 0 K divided 0 by 0 in the wrapper (UX-params P32): guarded. **Verified**: `test_md_placement.py::
test_hard_pressure_at_zero_temperature` (negative control: two moving disks give a finite Z),
`test_p03_ux.py::test_hard_disks_with_one_atom_at_rest_run` (frames run, pressure 0, no Z check value),
`::test_gas_of_equal_speeds_with_one_atom_or_at_zero_temperature`; `shots/after_hard_atom.jpg`.

## U7 — objects never placeable with their defaults

**Reproduced** (`out/shots_before.jsonl`): p04 «Объёмная сила» in the default world: «…плотность покоя схемы отклонилась
бы от ρ0 на 0.0993 > 0.045 …» (`shots/before_p04_gravity.jpg`); p03 «Стенка» «axis y is periodic», «Поршень» «a piston
needs a walled axis» in the default periodic box (`shots/before_p03_wall_piston.jpg`).

**Fixed**:
* p03: a wall or the piston on a periodic axis makes that axis walled at the current moment — engine
  `MD.set_boundary(axis, "walls" | "periodic")` and `HardSpheres.set_boundary` (`core/md/system.py`, `hard.py`):
  specular walls at 0 and L; the pairs across the faces stop interacting (an edit booked in the first-law balance); back
  to periodic when the last wall or piston on the axis goes, refused (the axis then stays walled, with a note) when atoms
  across the joined faces would overlap; hard disks within σ/2 of a face refuse the walls with the reason. The view draws
  the walled faces («Стенки ящика»; `p03_molecules/web/view.js`) and no longer leaves a removed piston's frame behind.
  A note says that the axis became walled (`shots/after_p03_wall_piston.jpg`: gas, walls, piston above the gas).
* p03 «Кристалл» in a non-empty scene: the free sites only (U4).
* p04 «Объёмная сила»: its default is the largest force the scheme of this world carries, up to 9.81 m/s² (new engine
  `Flow2D.gravity_limit`, the edge of `set_gravity`'s own refusal, by bisection; 4.3 m/s² in the default world with
  walls on every side); a larger one from the palette is reduced with a note naming the u_max that would carry it; an
  explicit −9.81 typed into the inspector is refused in Russian with that u_max — which, as a new world, takes it
  (`shots/after_p04_gravity.jpg`). The remedy that would remove the limit (the hydrostatic pressure taken analytically
  for a uniform-density fluid) is the engine's open item STATUS V41 (ab), unchanged.
* `palette_state()` (the integrator's API): p03 names a box already packed beyond random insertion for «Газ» and
  «Молекулы»; p04 names a taken set of sides for inlets, outlets, moving walls and periodicity, and a world without dye
  for «Краситель».

**Verified**: `test_md_placement.py::test_set_boundary_energy_across_the_faces_closed_form` (two atoms 0.6 σ from
opposite faces: walled U = 0; periodic U = u_LJ(1.2 σ) of the force-shifted term, its closed form; the first-law residual
stays 0; negative control: 0.3 σ from the faces is refused and the state kept),
`::test_set_boundary_walls_keep_the_particles_and_refuse_the_pistons_axis`, `::test_hard_set_boundary`;
`test_lbm_live.py::test_gravity_limit_is_the_refusals_edge` (0.999 of it accepted, 1.001 refused with the state kept; it
scales as u_max²; inf along a periodic axis); `test_p03_ux.py::test_a_wall_and_a_piston_on_the_default_periodic_box`,
`::test_charges_in_a_periodic_box_refused_in_russian_and_taken_once_walled`, `::test_palette_state_names_a_full_box`;
`test_p04_ux.py::test_the_body_force_is_placeable_in_every_world_and_an_explicit_large_one_is_refused` (four worlds).

## U8 — values far outside the world accepted without a word (p03, p04 part)

**Reproduced** (the review's `out/place.jsonl`; again by hand): p04 disks, rectangles, airfoils, dye and probes at ±10⁴ m
accepted, nothing visible; p03 «a particle outside the walls on axis x» in English; p03 probes and thermostat regions far
outside a walled box accepted.

**Fixed**: p04 `_inside` / `_point_inside` (`p04_fluids/viz.py`): a body wholly outside the domain is refused («тело
целиком вне области 2,2 × 0,41 м», with the admissible ranges), from the palette it is brought inside; a body covering
90 % of the domain is refused; one partly outside is accepted with a note (the wall cuts it); a probe or a dye spot
outside is refused, from the palette clamped into the domain and moved into the fluid. p03: atoms outside the walls
refused in Russian with the nearest free spot (U4); a probe's centre or a thermostat's region outside the walls refused
(`_point_inside`, `_region_inside`). **Verified**: `test_p04_ux.py::test_bodies_land_free_and_outside_is_refused`,
`test_p03_ux.py::test_a_probe_or_a_thermostat_outside_the_walls_is_refused`.

## U12 — laws the engine can change now become live

The integrator's API (2026-11-05): `live=True` laws of a playground are shown in «Законы мира — меняются сразу» and
applied at the current moment through `set_live`; the scene file takes the values in force. Every law of the two worlds:

| world | law | now | engine | what an edit does to the state; or why it stays a world parameter |
|---|---|---|---|---|
| p03 | interaction LJ ↔ WCA | **live** | `MD.set_pair` | same atoms, positions, velocities; the potential energy jumps by the difference of the models — the transaction moves E₀ by it, so the first-law residual is continuous (test: residual < 1e-9 after the switch); momentum reference, MSD origin, counters restart; approximations re-emitted |
| p03 | cutoff, shift | **live** | `MD.set_pair` | as above; a cutoff + skin beyond half a periodic box refused in Russian |
| p03 | time step | **live** | `MD.set_dt` | state kept, the step origin restarts; refused when the hottest motion present (each species' kinetic temperature, baths, thermal walls) cannot be resolved (UX-params P32) |
| p03 | dynamics: forces ↔ hard spheres | world | — | another solver (events, no forces, no step, other observables): the states do not map; the world parameter was renamed `dynamics` and the pair model split off as the live `model`; scene files and runs of the old combined «model» (lj / wca / hard) still load with the same laws (`"model": "hard"` → `dynamics = hard`) and a notice «файл старого формата …» (follow-up of 2026-11-05; test `test_p03_ux.py::test_an_old_format_scene_file_still_loads`, three old models and a new-format control) |
| p03 | space 2-D / 3-D | world | — | a plane has no z |
| p03 | box sizes | world | — | a deformation of the box (affine rescale) is not in the engine |
| p03 | boundaries | **per axis, live through objects** | `MD.set_boundary` | «Стенка» / «Поршень» make a periodic axis walled and give it back (U7); the world parameter is the start |
| p04 | viscosity ν | **live** | `Flow2D.set_viscosity` | τ changes, dt stays; populations kept (mass and momentum do not jump); the viscous stress in the non-equilibrium part adapts within a few steps; refused below what the grid carries, with the smallest ν; «0 — как вязкость» dye diffusivity follows |
| p04 | density ρ | **live** | `Flow2D.set_density` (new) | the lattice state kept, velocities the same; pressures, forces, mass and momentum change scale by ρ′/ρ; relative balance residuals unchanged (engine test: a flow given ρ′ half-way equals one that had it from the start, bit for bit) |
| p04 | collision TRT / BGK | **live** | `Flow2D.set_collision` (new) | populations kept; next steps with the other odd-moment rate (same equilibrium and viscosity) (engine test: equals a flow restored with the other operator, bit for bit) |
| p04 | dye on / off, diffusivity | **live** | `enable_dye`, `disable_dye` (new), `set_dye_diffusivity` | off: the field goes, its amount booked as removed («dye_off»), the dye balance closes again when it is on (engine test); refused while dye sources exist |
| p04 | fluid (water, air, DFG, own) | world (start), its ρ and ν live | — | it sets ρ and ν at the start and, with the grid, the speeds the world resolves (UX-params P24) |
| p04 | domain, grid | world | — | regridding the populations is not in the engine |
| p04 | largest expected speed (sets dt) | world | — | a new dt needs the lattice velocities and the non-equilibrium part rescaled: not in the engine |

Each live change is a recorded command (a restore repeats it), restarts p04's force window, and is an event with what
it did («законы на ходу: …; энергия изменилась на +0,47 кДж/моль на атом (разность потенциалов; учтена в балансе)»).
**Verified**: `test_p03_ux.py::test_live_pair_model_cutoff_and_step_keep_the_energy_balance`,
`::test_a_temperature_the_step_cannot_resolve_is_refused_and_a_shorter_step_takes_it`,
`::test_a_cutoff_beyond_half_the_box_is_refused_in_russian`, `::test_live_laws_and_placements_are_replayed_by_a_restore`;
`test_p04_ux.py::test_live_viscosity_density_collision_and_dye`, `::test_live_laws_and_placements_are_replayed_by_a_restore`;
engine `lfphys/tests/test_lbm_live.py` (density: equality with a flow that had it from the start, pressures × 1000 with a
negative control; collision: equality with a restored flow, the TRT control differs; dye off and on: the balance to
1e-12, refusal with a source); `shots/after_p03_live.jpg`, `shots/after_p04_live.jpg`.

## U13 — refusals in the engine's language (p03, p04)

**Fixed**: p03 translates every English refusal of `core.md` it can meet (`_EN` in `p03_molecules/viz.py`: jammed
placement, overlap — with charges the long-range repulsion named —, coincident atoms, overlapping hard particles, the
region, the walls, a cutoff beyond half the box, charges with a periodic axis — with the fix that now works: walls on
every axis —, the hard box's length, the piston) into `lfviz.errors.Refusal` with what to change, the engine's sentence
as the detail; anything else is the framework's generic internal-error text. p04 puts the engine's Russian refusals in
its own terms (`_ru`: the speed limit of this world in m/s instead of «уменьшите dt», the smallest ν, the u_max that
would carry a force). Numbers are written with a decimal comma and powers of ten as ·10⁻⁶ (`_num`). The before/after
texts are in `out/shots_before.jsonl` / `out/shots_after.jsonl` (e.g. «axis y is periodic» → the axis made walled; «…
уменьшите dt (или скорость)» → «…скорости не больше 0,9 м/с, или «Наибольшая ожидаемая скорость» больше (новый мир)»).
**Verified**: `test_p03_ux.py` (each refusal checked to be Cyrillic and free of the engine's English),
`test_p04_ux.py::test_engine_refusals_speak_the_worlds_terms`.

## U15 — the 2-D section's computed field is a side window (p04)

**Reproduced** (`shots/before_p04_cyl_1280.jpg`, `shots/before_p04_cavity_1280.jpg`): at 1280×800 the flow is a
330×140 px picture beside a 3-D view of the flat slab; the square cavity 328×310 px. **Fixed**
(`p04_fluids/web/view.js`): the plane's window takes the whole centre; the 3-D scene is shown beside it on request
(«Показать 3D-вид рядом», the choice kept in the browser). Measured canvas (`scripts/cavity.mjs`): the cavity 438×420 →
908×890 px at 1600×1000 and 328×310 → 688×670 px at 1280×800; the channel 330×140 → 690×145 px (its 5.4 : 1 aspect bounds
the height) (`shots/after_p04_cyl_1280.jpg`, `shots/after_p04_cavity_1280.jpg`, `..._1600.jpg`). The 3-D agent's lines in
this view (`plane2d`, opaque bodies) are kept. **Verified**: the screenshots; `keyframes.mjs` for p04: «all equal».

## U19 — units (p03, p04)

Every label of the two schemas and palettes checked: lengths in nm / m, temperatures in K, times in fs / ps / s,
speeds in m/s, energies and stiffnesses in ε-based units, pressures in bar / mN/m / Pa, fractions marked «доля»; one
missing unit added (p04 «Концентрация (доля)»). New labels carry their units («Радиус обрезки, σ», «Шаг по времени,
фс», «Кинематическая вязкость ν, м²/с», «Плотность ρ, кг/м³»).

## Changes for the integrator

1. **Framework**: `server/lfviz/playground.py::_placed` pops `position` from the values `place` returns even when it is a
   number; p03's piston has its own scalar parameter `position`, which was lost (the piston then landed at its default
   10 nm and was refused). p03 works around it (the placed position is kept for `on_add`), but the framework should pop
   only a list or tuple.
2. **STATUS.md, row V42**, replace item (e) by: «(e) closed 2026-11-05 (review UX-params P24): a fluid the grid cannot
   resolve at the asked u_max runs at the largest speed it resolves (u·dx/ν = 9), said in a notice and the approximations
   and recorded as the world's u_max; the presets «Вода…» and «Воздух…» run the DFG 2D-1 set-up at Re = 20 in a 22 × 4.1 mm
   and a 22 × 4.1 cm channel» and add: «(k) p03: the insertion bound (max_insert_energy, meant for overlaps) counts the
   long-range Coulomb energy too: a gas of +1 e charges is refused by repulsion (review UX-ui U13, found while testing);
   (l) live laws not possible with the engine as it is (review UX-ui U12): p03 the box sizes (a box deformation), p04 the
   grid and domain (regridding the populations) and the largest expected speed (a new time step with the populations
   rescaled)», with remedies «(k) an insertion bound on the short-range part only; (l) the engine's box deformation and
   LBM regridding / time-step rescaling, each with its conservation test».
3. **STATUS.md, row V41**, add to (ab): «the largest force the rest state carries is now reported (`Flow2D.gravity_limit`)
   and is the default of p04's «Объёмная сила» (4.3 m/s² in the default world); Earth's g needs u_max ≥ 0.68 m/s there».
4. **`lfphys/README.md`**, catalogue rows: `core.md.system` — append «; many molecules in one edit (`add_molecules`), an
   axis made walled or periodic at the current moment (`set_boundary`), a crystal around the atoms present
   (`fill(..., skip_occupied=True)`), vectorised random sequential insertion (the same points as one at a time)»;
   `core.md.hard` — append «; `set_boundary`; the pressure at T = 0 (Z undefined)»; `core.fluids.lbm` — append «; the
   viscosity, the density, the collision operator and the dye changed at the current moment (`set_viscosity`,
   `set_density`, `set_collision`, `enable_dye` / `disable_dye`), the largest body force the rest state carries
   (`gravity_limit`), the peak memory of a grid before it is built (`memory_estimate`)».
5. **`visualizations/README.md`** (owner guide), the two rows of the playground table:
   * p03: «газ, кристалл, атомы и молекулы (связи и углы) с моделью Леннард-Джонса, только отталкиванием или твёрдыми
     шарами; стенки (зеркальные, мягкие, тепловые — ванны), поршень, термостаты, поле, термометры; распределение
     Максвелла, g(r), температура, давление, теплота и работа. На ходу меняются модель взаимодействия, радиус обрезки и
     шаг по времени; стенка или поршень на периодической оси делают её осью со стенками; новый объект ставится в
     свободное место»;
   * p04: «течение в плоскости (решёточный метод Больцмана): цилиндры, прямоугольники, профили крыла NACA, входы и
     выходы, подвижные стенки, периодичность, краситель, датчики скорости; сопротивление и подъёмная сила, балансы массы и
     импульса. На ходу меняются вязкость, плотность, оператор столкновений и краситель; вода и воздух — со скоростями,
     которые разрешает сетка, или в своих сценариях (миллиметровый и сантиметровый каналы)».
6. `RULES.md` §2.4 / §6 say that a playground's laws are world parameters; with the integrator's decision of 2026-11-05
   (live laws in playgrounds) the text should say that the laws the engine can change at the current moment are live.
7. Containers of this session (`lf-uxg2-*`) were stopped by name at the end.

## Reproduction

Harness scripts (`scripts/*.py`) expect the engine at `/lf` and this folder at `/w`:
`docker run --rm --memory=12g -v <engine>:/lf:ro -v <this folder>:/w -e LFPHYS_NO_GPU=1 -e OMP_NUM_THREADS=2 -w
/lf/visualizations light-funnel-viz python3 /w/scripts/lat.py <tag> [cases]` (latencies; `rs_equiv.py`: the vectorised
insertion against the old one; `steplimit2.py`: the energy error against the step resolution; `lbm_mem.py <nx> <ny>
<dye>`: the peak memory per node; `chunk.py`: the cost of cutting advance calls). Browser scripts (`shots.mjs`,
`cavity.mjs`) run in `mcr.microsoft.com/playwright:v1.58.2-jammy` with `--shm-size=2g --init --network host`, `PORT` and
`TAG` in the environment, against a private server; «before» used a copy of the tree with the original p03, p04,
`core/md/system.py`, `hard.py` and `core/fluids/lbm.py` (and the framework as it was on 2026-11-05).
