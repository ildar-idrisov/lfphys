# Response to review UX-ui (2026-11-04): the leftovers — U12 for v11–v14, U15 for p02, U19 for v11/v12

Processed on 2026-11-05 by a subagent (Claude) that did not write the review. These are the parts of three findings
that no part file processed (`RESPONSE.md`, the index: «the review's v11/v12 (slit geometry) and v13/v14 (state as a
preparation) are in no part file», «p02 (2-D) … is in no part file», «v11/v12, the review's evidence, are in no part
file»). Everything else of the review is in the other part files. Checks, scripts, outputs and screenshots:
`response_checks_leftovers/` (`scripts/`, `out/`, `shots/`); reproduction at the end.

The owner's words that set the goal (2026-11-04, verbatim): «плейграунд должен быть больше похож на плейграунд, где я
могу ставить эксперименты в рамках одного мира, а не перезапускать его постоянно … должно быть все понятно и удобно и
подготовлено для визуализации и исследований».

## Summary

| ID | one line | decision | status | files | verified by |
|---|---|---|---|---|---|
| U12 (v11) | the plate's a, d, w, V₀ were world parameters, though `set_live` → `prop.rebuild` could take them | **fixed**: live, inside the world's window; every other parameter stated with its reason | [useful] | `v11_double_slit_2d/viz.py`, `web/view.js`, `README.md`, `tests/` | 6 new tests (below); browser before/after; key frames with live plate changes |
| U12 (v12) | the same plate; the detectors' λ₀ and W₀ also world parameters | **fixed**: the plate (through the slits), λ₀ of both exponential rules and W₀ of the soft detector live; κ, the soft detector on/off and the rest stated with their reasons | [useful] | `v12_arrival_times_2d/viz.py`, `web/view.js`, `README.md`, `tests/` | 5 new tests (and L1's); key frames with live detectors |
| U12 (v13, v14) | all 13 parameters world parameters: choosing an orbital started a new world | **fixed**: the state (and the cloud grid) live — an ideal preparation at the current moment in the same world; the atom / the quark pair stays a world parameter (reason stated) | [useful] | `server/lfviz/orbitals3d.py`, `v13_hydrogen_3d/viz.py`, `web/view.js`, `README.md`, `tests/`; `v14_quarkonium_3d/` the same | 6 + 1 new tests; browser before/after; key frames with preparations |
| U15 (p02) | in p02's 2-D worlds the computed wave is a side window next to a 3-D view of a flat slab | **fixed** as p04: the plane's window fills the centre, the 3-D view on request; worlds in space unchanged | [useful] | `p02_quantum/web/view.js` | screenshots: 438×420 → 908×890 px (1600×1000), 328×310 → 688×670 px (1280×800); key frames |
| U19 (v11, v12) | lengths «в λ» said only in another parameter's help; λ, V₀, W₀, κ without unit | **fixed**: every parameter with a unit names it in its label | [useful] | `v11_double_slit_2d/viz.py`, `v12_arrival_times_2d/viz.py` | label tests (both worlds); the labels the player shows, before/after (`out/before.jsonl`, `out/after.jsonl`) |

Found while processing (not in the review):

| ID | one line | decision | status | files | verified by |
|---|---|---|---|---|---|
| L1 | v12: «Начать новый мир» without a scenario was always refused, «нет параметра «mark»; … «mark_deg»; … «flux»» (v11's fixed keys in the header's parameters and in the live values) | **fixed** | [error in earlier] | `v12_arrival_times_2d/viz.py` | `test_a_new_world_from_the_header_and_the_live_values_builds` (with the old keys: refused, the negative control); `scripts/v12_newworld.py` before/after |
| L2 | a select whose options are numbers is refused when a form sends its value as text («нет варианта «64»; можно: «64», «96»»): v08 `n`, v09 `ngrid`, v13/v14 `ng`, v17 `n_lam` cannot be changed in the catalogue's or the «Новый мир» form | **for the integrator** (the framework's `params._coerce`); the live path of v13/v14 normalises it already | [neutral] | — (`server/lfviz/params.py` is not this part's) | `out/select_as_text.out` (API and the player's form: v08 «Сетка в плоскости» → 256 refused), `shots/found_select_as_text_v08.jpg` |
| L3 | `tests/browser/scene3d_checks.mjs`, case `views`, fails since p04's U15 (its 3-D view is hidden by default; the case measures the hidden canvas) — also on the tree as it was before this part | **for the integrator** (the test; p04 is not this part's) | [neutral] | — | `out/scene3d_views_before.out` (pristine copy) and `out/scene3d_checks.out` |

Counts: 3 findings of the review processed for their remaining worlds — **3 fixed** (U12 for v11, v12, v13, v14;
U15 for p02; U19 for v11, v12), 0 partly, 0 rejected, 0 deferred. Found while processing: 1 fixed (L1), 2 for the
integrator (L2, L3). Tests: see «Verification».

## U12 — laws and set-ups the engine can already change at the current moment (v11, v12, v13, v14)

**Reproduced.** v11: the review's citation holds (`viz.py:306-312`, `:340-361` of the tree before this part): `a`, `d`,
`w`, `V0` were world parameters while closing a slit went through `set_live` → `_hamiltonian` → `prop.rebuild`
(`shots/before_v11_left.jpg`: the live panel had only the slits, the mark and the flux). v13/v14: 13 parameters, all
world; a `set` of `n, l, m` was refused «Изменение не применено: у этого мира нет параметров, меняемых на ходу»
(`shots/before_v13_after_set.jpg`).

For every parameter of the four worlds: can the engine apply it at the current moment, keeping the world, with honest
checks? Each world's README now has a section «Live and world parameters (review UX-ui U12)» with the full table; in
short:

| world | parameter | now | what an edit does to the state; or why it stays a world parameter |
|---|---|---|---|
| v11, v12 | slit width a, distance d, thickness w, wall height V₀ | **live** | the plate rebuilt at the current moment in the grid, window, screen and absorbers the world was built with (the apparatus's own plate for the new a, d, w); the run, the companion (and v12's soft-detector run) take it from the next step; the wave is kept. The probability where the potential or the mark's field changed (> 10⁻⁶ E₀) feels it at once — a sudden change, its number said in the event; at t = 0 the event says the experiment is the new plate's from the start. Refused, world unchanged: slits beyond the screen, a plate within 3 edge widths of the source's layer or the screen, a ≥ d. `grid_wall` recomputed; the mark's calibration rebuilt and its share measured anew. After a change at t > 0 the comparisons assuming one set-up (`symmetry`, `no_crossing`, `visibility`, `ab_phase`, approximate theories) are not made, as for every live change |
| v11, v12 | edge width | world | the companion's grid is chosen from it at the start (coarser only while it resolves the edges): a narrower edge later voids the error estimate `numerics` |
| v11, v12 | screen distance L | world | the grid's length, the screen's face sample, its width and the absorbers come from it; a moved screen would mix two faces in `flux_absorbed` |
| v11, v12 | particle, λ; σx, σz, σy | world | the packet in flight and the unit of every length; the initial state the Bohm starts are drawn from |
| v11 | path mark (none / spin / detector) | world | one wave component or two: `SplitOperator.rebuild` refuses to turn a scalar wave into a spinor |
| v11, v12 | grid; Bohm particles, tracks | world | regridding is not in the engine; a particle added later has no history |
| v12 | λ₀ of Włodarz's and Marchewka–Schuss's rules | **live** | the rule's rate uses the λ₀ in force when each sample on the plane was recorded: the clicks before stay, the survival is continuous; at t = 0 or before 10⁻⁶ of the signal: as from the start, else `arr_train` is information «not applicable» |
| v12 | soft detector's W₀ | **live** | the second run's absorber rebuilt at the moment (its wave and clicks go on); `soft_grid` for the highest W₀ the run had; at t = 0 or before 10⁻⁶ of the wave reached the detector: as from the start, else `arr_soft_reflection` is information «not applicable»; refused without a soft detector |
| v12 | flight; initial state, train; κ; soft detector on/off | world | other apparatus and window; the initial-state rules are functionals of the initial state; κ's rule is a closed form for one κ (a κ changed at a moment is a time-dependent Robin condition, not solved by the engine); the soft detector is a second run from t = 0 |
| v13, v14 | the state: single/superposition, n, l (L), m, real/complex, the second state, \|c₂\|², the phase of c₂ | **live** | an ideal preparation at the current moment t_p: ψ(t) = Σ c_k e^{−iE_k(t − t_p)/ħ} ψ_k, the former state discarded (no transition dynamics is modelled or claimed). The world, its clock, record and the slice planes placed stay; the box, the cloud and current of the phases reached, the slices on the planes (clamped into the new box, recomputed and checked), the radial distribution and the state's checks are made for t_p; a superposition's phases are revealed at t_p + kT/24 and the period checked at t_p + T. The former state's checks the new one does not give are retired («… — прежнее состояние», information). The run sends `prepared` first (the header's parts that describe the state), frames carry `t_p`. All or nothing: a refused preparation (equal or non-orthogonal states chosen by hand) leaves the world exactly as it was |
| v13, v14 | cloud grid 64 / 96 | **live** | the same state at the same t_p resampled (the phases reached recomputed) |
| v13 | atom | world | the nucleus and the reduced mass are the system: no operation turns one atom into another keeping its electron's state |
| v14 | quark pair | world | the system (quark mass, the model's levels) |

**Fix** (at the cause). v11: `_live_geometry` (a copy of the world's geometry with the new a, d, w, checked against the
window), `set_live` builds everything first and changes the world only when nothing failed; `_sudden` (the probability
where the Hamiltonian changed); `_wall_check`; the set-up message carries the plate in force (`geometry`), and the view
draws the plate's outline and names it from it (also when key frames go back). The world's live parameters come from
its own schema (`SCHEMA`, `FIXED_LIVE`): v12's live values are now its own. v12: `det_hist` (each detector value with the
time from which it holds and whether it came before the signal), `_strength`, `_one_value`, `_signal_so_far`,
`_soft_grid_check`; the view shows the detectors in force. v13/v14: the shared `OrbitalWorld._prepare` (transactional:
the world's attributes and its random generator restored on failure; `_build(planes)`, `_reveal_due`, `t_prep` in
`bin_at`, `advance`, `next_event_time`, `frame`; checks tracked by id to retire the stale ones); each world's
`_set_state` (what its constructor did), `live_values`, `set_live`; the title names the atom (or pair), the state is in
the panel «Состояние». The views (`v13 web/view.js`, `withPreparation`, used by v14) restart the shared orbit view from
the world's header with the `prepared` parts and count the period's phase from `t_prep`; no player file changed.

**Verified** (Docker, CPU). v11 `tests/test_v11_double_slit_2d.py`: `test_the_wall_height_set_at_the_start_is_the_world_built_with_it`
(bit for bit after 40 pairs; another V₀ differs: negative control), `test_a_live_plate_is_the_apparatus_plate_in_the_same_window`,
`test_a_plate_that_does_not_fit_the_window_is_refused_and_the_world_unchanged`,
`test_a_plate_changed_after_the_packet_passed_changes_almost_nothing` (< 2·10⁻³ of the peak, checks pass; at t = 0
> 0.05: negative control), `test_a_wall_grown_under_the_wave_is_a_sudden_change_and_said` (> 10⁻³, norm + absorbed = 1),
`test_a_live_plate_is_continued_from_a_checkpoint_and_replayed_by_a_restore` (byte for byte in a new process; a restore
by replay rebuilds the plate). v12: `test_a_detector_strength_set_before_the_signal_is_the_world_built_with_it` (bit for
bit), `test_a_detector_strength_changed_while_the_signal_arrives_acts_from_that_moment` (the past equal, the future equal
to λ₀′v₀ρe^{−Λ} by hand to 10⁻¹², the unchanged world differs: negative control),
`test_soft_detector_height_changed_at_the_detector_leaves_the_stationary_comparison_out`,
`test_detector_and_plate_refusals_leave_the_world_unchanged`, `test_through_the_slits_a_live_plate_acts_on_both_runs`.
v13: `test_a_state_set_live_is_prepared_in_the_same_world` (the cloud bit for bit a world built with 3d_z²; retired
checks; `t_prep`), `test_a_superposition_prepared_mid_world_counts_its_period_from_the_preparation` (each phase bit for
bit; the phase counted from t = 0 would differ: negative control; the period at t_p + T),
`test_a_refused_preparation_leaves_the_world_as_it_was`, `test_the_planes_placed_stay_through_a_preparation_and_the_grid_is_live`,
`test_the_atom_stays_a_world_parameter`, `test_a_preparation_is_continued_from_a_checkpoint_byte_for_byte`; v14:
`test_a_state_set_live_is_prepared_in_the_same_world`. In the browser (private server): `shots/after_v11_left.jpg` (the
plate's four controls in «Установка — меняется сразу», with units), `after_v11_live_a.jpg` (a = 2.5 λ in the same world:
«Опыт» shows the plate in force), `after_v12_left.jpg`, `after_v13_after_set.jpg` (3d_z² prepared in the 2p_z world: the
state panel, the slice and its check), `after_v13_super.jpg` (1s + 2p_z prepared: the superposition's checks, the
former state's current check marked «прежнее состояние»), `after_v14_after_set.jpg`; one world in each run
(`out/after.jsonl`, `worlds: 1`). Key frames: `keyframes.mjs` for v11, v12, v13, v14, p02 «all equal»
(`out/keyframes.out`); its copy with the new live changes in the middle (`scripts/keyframes_live.mjs`: v11 a, then w and
V₀; v12 λ₀, then W₀; v13 3d_z², then 1s + 2p_z with the grid as text; v14 1P_z, then the grid) «all equal»
(`out/keyframes_live.out`), and the records show the changes applied, not refused (`out/keyframes_live_records.out`).

## U15 — p02's 2-D sections: the computed wave is the main view

**Reproduced** (`shots/before_p02_double_slit_1600.jpg`, `_1280.jpg`; `out/before.jsonl`): the wave's window 438×420 px at
1600×1000 (the review: ≈ 430×420) and 328×310 px at 1280×800, next to a 470×915 px 3-D view of the ±40 nm × thin slab.

**Fixed** (`p02_quantum/web/view.js`, as p04's `view.js` and `RESPONSE_p03-p04.md` U15): in a plane (`grid.ndim == 2`) the
wave's window takes the whole centre and the 3-D view is hidden; a panel «Вид» on the right says why and has «Показать
3D-вид рядом» / «Скрыть 3D-вид …» (the choice kept in the browser, `p02.show3d`); in space (`dim = 3d`) the 3-D scene stays
the main view with the slice z = 0 beside it (the panel says so, no button). No header flag was needed.

**Verified.** Window 908×890 px at 1600×1000 and 688×670 px at 1280×800, no 3-D canvas (`shots/after_p02_double_slit_*.jpg`);
with the button: the former layout (`after_p02_double_slit_*_with3d.jpg`); `ball_3d` unchanged (438×420 window, 470×915
3-D; `after_p02_ball_3d_1600.jpg`); `keyframes.mjs` for p02 «all equal»; the p02 tests pass.

## U19 — units on v11's and v12's primary parameters

**Reproduced** (`out/before.jsonl`, the labels the player shows): «Ширина щели a», «Расстояние между щелями d (центр —
центр)», «Толщина пластины», «Расстояние до экрана», «Пакет: ширина поперёк σx», …, «Длина волны де Бройля λ» (its unit
`пм` only in the schema's `unit`, which the forms do not show: `ui.js` `control`/`paramForm` print the label alone), v12
«Высота стенки» without help, «Мягкий детектор: W₀», «Поглощающая граница: κ».

**Fixed**: each label names its unit — «Ширина щели a, λ», «Расстояние между щелями d (центр — центр), λ», «Толщина
пластины w, λ», «Высота стенки V₀, в E₀» (with v11's help in v12 too), «Ширина краёв …, λ», «Расстояние до экрана L, λ» /
«Расстояние до детектора L, λ», «Пакет: ширина поперёк σx, λ» (σz, σy alike), «Расстояние между пакетами, λ», «Длина
волны де Бройля λ, пм», «Метка в щели B: поворот θ, °», «Поглощающая граница: κ, в k₀» (help: k₀ the mean wavenumber),
«Мягкий детектор: высота W₀, в E₀» (new help), «Правило Влодажа: сила λ₀ (безразмерная)», «Правило Маркевки–Шусса: сила λ₀
(безразмерная)». **Verified**: `test_every_length_and_the_wall_height_carry_their_unit_in_the_label` (v11),
`test_every_length_and_detector_parameter_carries_its_unit_in_the_label` (v12): every parameter with a `unit` has it in
its label; the browser's labels after (`out/after.jsonl`, `shots/after_v11_left.jpg`, `after_v12_left.jpg`).

## Found while processing

* **L1** [error in earlier] v12's header carried v11's fixed `mark`, `mark_deg`, `flux` in its parameters (and its live
  values `mark_deg`, `flux`); the player's «Начать новый мир» without a scenario sends both back, so every such new world
  was refused (`scripts/v12_newworld.py`: before «Новый мир не создан: нет параметра «mark»; …», after: world 2 built).
  Fixed in v12: its parameters and live values are its schema's. A record made before keeps the old keys in its
  header: a resume by replay of such a v12 world would be refused as before (a checkpoint is unaffected).
* **L2** the framework refuses a select's numeric option sent as text; reproduced through the API and in the player's
  form (v08 «Сетка в плоскости, точек на ось» → 256: «Новый мир не создан: … нет варианта «256»; можно: «128», «256», …»).
  v13/v14's live `set` converts the grid's text to a number itself (tested); the forms remain — changes for the
  integrator, item 1.
* **L3** `scene3d_checks.mjs` `views` fails on p04 (the 3-D view hidden by default since p04's U15); the same on a pristine
  copy of the tree — changes for the integrator, item 6. The cases that use this part's worlds (`depth`, `planes`,
  `labels`, `quality`, `keys`: v13) pass (`out/scene3d_checks.out`).

## Verification

Docker image `light-funnel-viz`, CPU (`LFPHYS_NO_GPU=1`, `OMP_NUM_THREADS=2`):

* the world tests `v11_double_slit_2d/tests v12_arrival_times_2d/tests v13_hydrogen_3d/tests v14_quarkonium_3d/tests
  p02_quantum/tests`: 126 passed, 2 skipped (GPU = CPU, no GPU here), 18 min 21 s (a first run found two mistakes of
  this part's own new tests — a refusal case the test geometry could not reach, a wall height compared with V₀E₀ where
  the tanh edges keep it lower — fixed in the tests);
* `tests/test_checkpoint.py tests/test_restore.py -k "v11 or v12 or v13 or v14 or p02"`: 15 passed (57 deselected), 1 min 54 s;
* no engine module (`lfphys`) was changed;
* on the private server (`lf-uxj-srv`, port 8576): `keyframes.mjs` v11, v12, v13, v14, p02 — «all equal»; the variant with
  the new live changes — «all equal»; `scene3d_checks.mjs` `depth,planes,labels,quality,keys` — «all passed».

## Changes for the integrator

Yes.

1. **Framework, `server/lfviz/params.py::_coerce` (L2).** For `select`, accept a value whose text equals an option's
   text and return the option's own value, e.g.
   `match = [o[0] for o in p.options if o[0] == v or str(o[0]) == str(v)]` → `return match[0], None`. It makes v08 `n`,
   v09 `ngrid`, v13/v14 `ng`, v17 `n_lam` changeable in the catalogue's and the «Новый мир» forms (now refused); records
   with numbers keep working. A test: `resolve(None, {"ng": "64"})` of v13 gives 64.
2. **`STATUS.md`, row V42, item (l)** (live laws not possible with the engine as it is): append «; v11/v12: the screen
   distance L and the grid (regridding the wave), the path mark (a scalar wave turned into a spinor at a moment), the
   edge width (the companion's grid is chosen from it); v12: κ of the absorbing boundary (a time-dependent Robin
   condition), the soft detector switched on later (a second run from t = 0)», remedy «… the engine's regridding of a
   split-operator wave, a scalar → spinor embedding, the Robin rule with κ(t)». No other STATUS row: nothing of this
   part is deferred.
3. **`RESPONSE.md` (the index)**, rows U12, U15, U19: replace «… are in no part file» by «v11–v14: `RESPONSE_leftovers.md`»,
   «p02: `RESPONSE_leftovers.md`», «v11/v12: `RESPONSE_leftovers.md`»; the decisions become «fixed» (U12 for p01–p04 and
   v11–v14; U15 for p02, p04; U19 fixed in v11/v12); totals: 20 fixed, 3 partly, 1 deferred, 0 rejected; add the part file
   to «Part files» (`RESPONSE_leftovers.md`: U12 for v11–v14, U15 for p02, U19 for v11/v12; L1–L3 found).
4. **`RULES.md`**, §2.4, after «In a playground the laws the engine can change at the current moment are live parameters
   too (§6).»: «A demonstration's state that an experimenter can prepare (v13, v14: an ideal preparation at the current
   moment, the former state discarded) is live in the same way; a law or a system that no operation changes (the atom, the
   quark pair) stays a world parameter.» §3, the 3-D messages table, after `cloud`: «`prepared` | (v13, v14) a state
   prepared at the current moment: `t_prep`, `keep_time`, `header` (the header's parts that describe the state: title,
   states, levels, period, nb, scene3d …); the view starts its state from the world's header with them; frames carry
   `t_prep`, the period's phases count from it».
5. **Owner guide `visualizations/README.md`**: in the row «облако и фазы (v13, v14)» append «Состояние меняется на ходу
   (слева, «Установка»): новое n, l, m, суперпозиция или сетка облака — в том же мире, с момента изменения (идеальная
   подготовка: прежнее состояние отброшено), срезы остаются; период суперпозиции отсчитывается от момента подготовки;
   другой атом (пара кварков) — новый мир»; in the row «плоскость опыта (v11, v12)» append «; у p02 в плоскости окно волны —
   главный вид во весь центр, 3D-вид — по кнопке «Показать 3D-вид рядом» (панель «Вид»)»; in the catalogue row of v11
   replace «на ходу — закрыть щель, …» by «на ходу — изменить пластину (ширину щелей, расстояние между ними, толщину,
   высоту стенки), закрыть щель, …»; in v12's row append «; на ходу — пластина, сила λ₀ экспоненциальных правил и высота
   W₀ мягкого детектора»; in v13's row append «; состояние меняется на ходу, в том же мире».
6. **`tests/browser/scene3d_checks.mjs`, case `views` (L3)**: before opening p04, set `localStorage["p04.show3d"] = "1"`
   (or click «Показать 3D-вид рядом») so that the 3-D view whose camera it checks is shown; the same for any future case on
   p02 in a plane (`p02.show3d`).
7. **`p02_quantum/README.md`**, «What the player shows», first sentence: «In a plane the wave's window is the main view,
   across the whole centre (review UX-ui U15, as p04); the 3-D scene is shown beside it on request («Показать 3D-вид
   рядом», panel «Вид»). The 3-D scene (z up): …»; in space unchanged.
8. Optional: `withPreparation` (`v13_hydrogen_3d/web/view.js`, used by v14) could move into the shared
   `player/js/orbitview.js`.
9. The containers of this part (`lf-uxj-*`) were stopped by name at the end and checked.

## Reproduction

Harness scripts (`scripts/*.py`) expect the engine at `/lf` and a folder `/w` holding them in `py/`:
`docker run --rm --memory=8g -v <engine>:/lf:ro -v <dir>:/w -e LFPHYS_NO_GPU=1 -w /lf/visualizations light-funnel-viz
python3 /w/py/<script>.py` (`quick_v11.py`, `quick_v13.py`: the live changes and refusals by hand; `v12_newworld.py`:
L1; `record_check.py <run dirs>`: what a run's record holds). Browser scripts (`shots.mjs` with `PORT`, `TAG` and cases
`p02 p02small p02_3d v11 v12 v13 v14`; `select_form.mjs` with `PORT`; `keyframes_live.mjs <port> <worlds>`) run in
`mcr.microsoft.com/playwright:v1.58.2-jammy` with `--shm-size=2g --init --network host` next to a `node_modules/playwright`
1.58.2, against a private server (`server/serve.py`, `LFPHYS_NO_GPU=1`, `LFVIZ_PLAYGROUND_CKPT=6`). «before» used a
copy of `lfphys/` and `visualizations/` taken before any change of this part (server `lf-uxj-srvb`, port 8577).
