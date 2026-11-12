# Response to the review UX-params (2026-11-04): the playgrounds p03 and p04

Processed by a working session other than the review's author (2026-11-05), for the findings assigned to p03
«Частицы и молекулы», p04 «Жидкости» and the engine modules behind them (`lfphys.core.md.*`, `lfphys.core.fluids.lbm`).
Other agents process the framework (P1–P4 framework parts, P20, P22) and the other worlds. Checks, scripts and
screenshots: `response_checks_p03-p04/`. The companion response for the same worlds to the review UX-ui is
`../2026-11-04_internal_UX-ui/RESPONSE_p03-p04.md` (it holds the full latency table, the live-law table and the
changes for the integrator, which also cover these findings).

## Summary

| finding | decision | one line |
|---|---|---|
| P24 | fixed | water, air (and any own fluid) from the defaults give a working world: u_max lowered to what the grid resolves, said so; two presets at Re = 20 |
| P25 | fixed | a grid above the memory budget is refused before it is built, with nodes, memory and what to change; a large grid that fits keeps frames short |
| P27 | fixed | a probe inside a body says so («внутри тела «…»: здесь нет жидкости»); a palette probe asked there goes into the fluid |
| P31 | fixed | «Стенка» and «Поршень» on a periodic axis make it walled; every engine refusal in p03 translated with the fix |
| P32 | fixed | equal speeds with one atom / at 0 K, hard disks at 0 K, a temperature the step cannot resolve: no crash; refused in Russian with the largest T and the step for this T |
| P33 | fixed | counts beyond random packing refused at once with the count that fits; feasible large ones 7–23 times faster; frames not blocked |
| P4 (p03, p04 parts) | fixed | deliberate refusals are `lfviz.errors.Refusal` in Russian; the engine's English and «dt» texts translated; a failed MD step explained in Russian |

Counts: 7 fixed, 0 partly, 0 rejected, 0 deferred. Tests: engine 404 passed, 7 skipped; p03, p04 and their shared
checkpoint and restore tests 86 passed; `keyframes.mjs` for p03 and p04 «all equal». Docker, CPU.

## P24 — every fluid other than «dfg» refused from the defaults

**Reproduced** (`out/shots_before.jsonl`, `shots/before_p04_water.jpg`): «Жидкость» = вода with the other defaults:
«Мир не создан: неустойчиво: τ = 0.50008 слишком близко к 1/2 …; увеличьте вязкость или уменьшите dx, или увеличьте dt»
(air: the cell Reynolds number 149 > 10). The advice names dt, which the owner cannot set.

**Cause**: the grid of the default channel (dx = 5 mm) resolves water (ν = 1.0·10⁻⁶ m²/s) only up to u·dx/ν ≈ 10, i.e.
2 mm/s; the default u_max of 0.45 m/s is 225 times more (a cell Reynolds number of 2250).

**Fixed** (`p04_fluids/viz.py`, `__init__`): a fluid the grid cannot resolve at the asked u_max runs at the largest speed
it resolves, u_max = 0.9 · 10 ν / dx rounded down (cell Reynolds number 9, below the open-domain stability edge 10); a
notice and an approximation line state the trade-off («вода (ν = 1·10⁻⁶ м²/с) на сетке с шагом 0,005 м разрешается при
скоростях до 0,0018 м/с …; для бо́льших скоростей — область меньше или узлов больше (новый мир), или сценарии «Вода…»,
«Воздух…»»), and the lowered value is the world's recorded u_max (the header's parameters, so the next «Новый мир» form
shows it). The palette's speeds follow u_max (a fifth of it: 0.4 mm/s for water; the default 8 cm cylinder then runs at
Re ≈ 33). Two presets show water and air at the scale where they are resolved at useful speeds: «Вода: обтекание
цилиндра D = 1 мм в канале 22 × 4,1 мм, Re = 20» and «Воздух: … D = 1 см в канале 22 × 4,1 см, Re = 20» — the DFG 2D-1
set-up (D = 20 cells, Um = 1.5 U) in these fluids, so the same flow in units of D and U. The DFG fluid's world is
unchanged (u_max 0.45 m/s, no notice). The engine's refusals in p04 now speak of the world's parameters (U13 of UX-ui:
the speed limit in m/s, the smallest ν, «Наибольшая ожидаемая скорость»), never of dt.

**Verified**: `p04_fluids/tests/test_p04_ux.py::test_water_and_air_from_the_defaults_give_a_working_world` (u_max with
8 < u·dx/ν ≤ 9, the header's value, the notice; an inlet, an outlet and a disk added and run with every check passing;
control: the DFG world keeps 0.45 m/s); the presets in `test_p04_fluids.py::test_every_preset_and_the_default_laws_build_
run_and_keep_their_balances` (now seven presets); `shots/after_p04_water.jpg` (the water world running with dye).

## P25 — a thin or tall domain allocates without a limit

**Reproduced**: «Lx» = 10⁻⁶ m with the default Ly and nx = 440 gives 440 × 1.8·10⁸ nodes («Unable to allocate 591 GiB»);
«Ly» = 10⁴ m 6.6 GiB per array; a 4·10⁶-node grid that fits spent minutes in one frame.

**Fixed**:
* engine `Flow2D.memory_estimate(nx, ny, dye)` (`core/fluids/lbm.py`): 1000 B per node with the dye, 800 without —
  measured 840 / 631 B per node at 10⁶ nodes (VmHWM after building a channel with an inlet, an outlet, a disk and a dye
  source and 5 steps: `scripts/lbm_mem.py`, `out/lbm_mem.txt`), rounded up;
* p04 `check_params` and `estimate_bytes` (the integrator's API: asked before a world is built) and the constructor
  itself: above the worker's budget (the framework's `lfviz.limits`, 85 % of it, or 6 GiB without one) the world is
  refused before any allocation: «область 1·10⁻⁶ × 0,41 м на сетке nx = 440: шаг 2,3·10⁻⁹ м, по y 1,8·10⁸ узлов, всего
  7,9·10¹⁰ узлов — это ≈ 72,2 ТБ памяти, больше предела 6 ГБ. Что изменить: «Длина области по x» не меньше 0,012 м при
  440 узлах, или область ближе к квадрату …» (the largest nx that fits is named first when one does);
* a grid that fits but is slow: an advance call is cut to the steps the CPU's rate table (`lbm.RATES`, fixed:
  deterministic) allows in 0.1 s — one step for 4·10⁶ nodes — so the frames and commands keep flowing; a step above
  0.25 s is named in the approximations. Measured cost of the cut (`scripts/chunk.py`): none on the default grid, 23 %
  at 3 steps per call on the 880-node Kármán grid, hence 0.1 s rather than 0.04 s (8 steps there).

**Verified**: `test_p04_ux.py::test_a_grid_beyond_the_budget_is_refused_before_it_is_built` (three domains: the refusal
in Russian with the nodes, the memory and «Длина области по x»; `estimate_bytes` equal to the engine's estimate; the
constructor refuses too), `::test_a_large_grid_that_fits_keeps_frames_short`;
`lfphys/tests/test_lbm_live.py::test_memory_estimate_covers_the_state`.

## P27 — a probe inside a body reads NaN without a word

**Fixed** (`p04_fluids/viz.py`, `frame`): a probe on a solid node reads «внутри тела «Цилиндр»: здесь нет жидкости —
сдвиньте датчик» instead of NaN; a probe (or a dye spot) placed from the palette inside a body goes to the nearest fluid
node with a note. **Verified**: `test_p04_ux.py::test_a_probe_inside_a_body_says_so`; `shots/after_p04_probe_body.jpg`
(before: `shots/before_p04_probe_body.jpg`, «—»).

## P31 — «Стенка» and «Поршень» in the default periodic box refused in English

**Reproduced** (`shots/before_p03_wall_piston.jpg`): «Сцена не изменена: axis y is periodic», «… a piston needs a walled
axis». **Fixed**: the axis becomes walled at the current moment (engine `MD.set_boundary` / `HardSpheres.set_boundary`;
the details and the closed-form test of the energy across the faces in the UX-ui response, U7); the piston goes above
the gas; every other English refusal of `core.md` that p03 can meet is translated with the fix (`_EN`: charges with a
periodic axis — «поставьте «Стенку» на каждую периодическую ось …», which now works —, jammed placement, overlap, region,
walls, the cutoff beyond half the box, the hard box's length, the piston's side). **Verified**:
`test_p03_ux.py::test_a_wall_and_a_piston_on_the_default_periodic_box`,
`::test_charges_in_a_periodic_box_refused_in_russian_and_taken_once_walled`, `::test_a_cutoff_beyond_half_the_box_is_
refused_in_russian`; `shots/after_p03_wall_piston.jpg`.

## P32 — edits that crash the world

**Reproduced**: «Газ» n = 1 with equal speeds → «float division by zero» (wrapper); hard disks at T = 0 → `ZeroDivisionError`
in `hard.py` every frame; a gas or crystal at 10⁵ K → «two interacting particles at the same point» / «… crossed the walls
more than 64 times» (`shots/before_p03_hot_gas.jpg`).

**Fixed**:
* the equal-speed start with one atom or at 0 K no longer divides 0 by 0 (`_gas`);
* the hard world's pressure at T = 0 (`core/md/hard.py`; UX-ui U6);
* a temperature the time step cannot resolve is refused at once (`_check_temperature`, applied to a gas, a crystal,
  molecules, an atom's speed, a thermostat and a thermal wall, at every add and edit, and to a live change of the step).
  The criterion is measured, not assumed: an rms step v dt larger than a fraction of σ alone did not work (at 0.05 σ per
  step, 7000 K in 2-D, all three runs crashed: `out/steplimit.txt`); what matters is the steep core, the distance r_t/12
  over which the 12-6 repulsion rises by kT near the turning point r_t = σ (4ε/kT)^(1/12). With q = 12 v dt / r_t, an LJ gas
  (2-D and 3-D, 200 atoms, dt = 10 fs, three seeds, 3000 steps; `scripts/steplimit2.py`, `out/steplimit2.txt`) keeps the
  energy error below 0.6 % of kT per atom for q ≤ 0.36, 0.02–5 % at q ≈ 0.45, and two of three 2-D runs crash at
  q = 0.58; 10⁵ K is q ≈ 3.5. The bound is Q_MAX = 0.4 (argon at 300 K: 0.12; an atom of 4 u at 300 K: 0.38): at 10 fs
  argon is resolved up to about 2400 K in a plane; above it the refusal names the largest T at this step and the step
  for this T («… температура не выше 2,37·10³ K при этом шаге, или «Шаг по времени» не больше 1,1 фс (меняется на ходу,
  в «Установке»)»), and the step is now a live law, so the owner can follow the advice in the same world
  (`shots/after_p03_hot_gas.jpg`).
* A step that still fails while running (an untested combination) is reported in Russian with what to change (p03
  `advance`: «шаг Верле не удался …: уменьшите «Шаг по времени» (на ходу) или температуру …»).

**Verified**: `test_p03_ux.py::test_gas_of_equal_speeds_with_one_atom_or_at_zero_temperature`,
`::test_hard_disks_with_one_atom_at_rest_run`, `::test_a_temperature_the_step_cannot_resolve_is_refused_and_a_shorter_step_takes_it`
(10⁵ K refused, 1500 K taken; after «Шаг по времени» = 1 fs the 10⁵ K gas is taken and runs; then 10 fs is refused for
the hot gas: the negative control of the live check); `lfphys/tests/test_md_placement.py::test_hard_pressure_at_zero_temperature`.

## P33 — counts at their maxima stall the world

**Fixed**: the counts are tied to the box — a gas or molecules beyond random packing are refused at once with the count
that fits (`_pack_check`); molecules are inserted in one engine edit per batch (`MD.add_molecules`), the gas's random
insertion is vectorised in the engine and gives the same points as before (`random_sites`); the neighbour list's memory
is checked against the worker's budget before a large insertion (`lfviz.limits.require`); a large scene's advance call
is cut to 40 ms of modelled cost. Latencies before → after (`out/lat_before.jsonl`, `out/lat_final.jsonl`,
`out/lat_large.jsonl`): 2000 molecules in the preset > 90 s → refused in 0.004 s; chains of 50 atoms > 90 s → refused in
0.004 s; 600 molecules 26.9 s → 1.2 s; a 3-D gas of 20 000 atoms > 90 s → refused in 0.000 s with the count that fits
(14 629); of 12 000 atoms 24.3 s → 2.8 s; the full table is in the UX-ui response (U5). **Verified**:
`test_p03_ux.py::test_molecule_edits_are_quick`, `::test_a_large_gas_is_refused_at_once_with_the_count_that_fits`;
`test_md_placement.py` (the vectorised insertion against the one-at-a-time reference, 24 cases; `add_molecules`).

## P4 — internal exceptions reach the user as refusal texts or tracebacks (p03, p04 parts)

**Fixed** for the two worlds: their deliberate refusals are `lfviz.errors.Refusal` (Russian, with what to change; the
engine's own sentence as the detail) — the framework shows them as they are and turns anything else into its generic
Russian text with the traceback in the worker's log only. p03 translates the English `ValueError`s of `core.md` (P31);
p04 translates the engine's Russian refusals that named dt (P24); the world-specific causes behind the exceptions the
review saw in p03 and p04 are fixed at their source (P25: no `MemoryError` from a grid; P32: no `ZeroDivisionError`,
`FloatingPointError`; P33: the cell list's allocation checked). **Verified**: the `russian()` checks in
`test_p03_ux.py` and `test_p04_ux.py` (Cyrillic, none of the engine's English, no «dt», no traceback);
`out/shots_after.jsonl` (the texts the page showed).

## Follow-up (2026-11-05): old p03 scene files

The live pair model (UX-ui U12) split p03's former world parameter «model» (lj | wca | hard) into «dynamics» (world) and
«model» (live). Scene files and stored runs of the old format keep loading with the same laws: p03's schema reads
`"model": "hard"` as `dynamics = hard` (lj and wca are valid as they are, with the default dynamics, the forces), and the
world says so in a notice «файл старого формата (до 2026-11-05): …; сцена загружена с теми же законами» — nothing is
refused. **Verified**: `p03_molecules/tests/test_p03_ux.py::test_an_old_format_scene_file_still_loads` (an exported file
rewritten to the old format for each of hard, lj, wca: resolves without errors, the same dynamics and pair model, the
objects back, the notice shown, runs; control: the new-format file has no notice); p03 tests with the shared checkpoint
and restore tests for p03: 51 passed.

## Changes for the integrator

See `../2026-11-04_internal_UX-ui/RESPONSE_p03-p04.md`, «Changes for the integrator» (one list for both reviews): the
framework's `_placed` and a scalar `position`; STATUS V42 (e) closed by P24 and new items (k) and (l); V41 (ab); the
catalogue rows of `lfphys/README.md`; the owner guide's rows for p03 and p04; RULES.md on live laws in playgrounds.
