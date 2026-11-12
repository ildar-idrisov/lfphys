# Response to review LB1-framework — the framework part (F5 framework, F13, F14, F15, F16 framework)

**Responder:** the framework processing agent of LB1 (lf-lpf-, a different agent from the reviewer and from the authors of
the code). **Date:** 2026-11-11/12. The other findings of this review (F1–F4, F6–F12, the instruments part of F16) are
answered by the instruments processing agent in `RESPONSE_instruments.md`; the sections' parts of F5 (p03, p04) by
their agents (`RESPONSE_p03.md`, `RESPONSE_p04-p01.md`).

**Counts (this file):** 5 findings — 5 fixed (F5 in its framework part; the sections carry their state through the new
hooks), 0 partly, 0 rejected, 0 deferred. One optional suggestion not taken (F5, «время с нуля»: reason below).

**Environment.** Image `light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`). Python tests in containers `lf-lpf-*` from
`engine/`. A private server `lf-lpf-srv` (port 8612, `--memory=6g`, 3 workers, `LFVIZ_EXTRA` = the toy section) for the
section checks and the browser checks (Playwright 1.58.2, Chromium with SwiftShader, 1600×1000 and 1280×800). The shared
server on 8479 was not used. The checks of this response are in `response_checks_framework/` with their outputs.

## Findings

### F5 — error — carry-over promised the state; objects without `object_state` and the world's own state restarted silently

**Status:** fixed (framework part) [error in earlier] — the checkbox title and the notice «все объекты (N)» claimed a
state that was not carried.

**Reproduced.** The reviewer's `c07b`/`c07c` outputs (p03: `carried object has a state: False`, T 300.46 → 300.24 K at the
same t, notice «все объекты (1)»; p04: `q_net 0.01784 → 0.0`, notice naming only the refused inlet) match the code before
the fix: `_carry_scene` counted only refused objects; the export carried only `object_state`'s JSON, which p02, p03 and
p04 leave empty because their state is megabytes.

**Fix (at the cause).** A carry-over now has a path for state that is not scene-file JSON, and the framework says what
went how.

- **Hooks** (`server/lfviz/playground.py`; announced to the section agents through the integrator on 2026-11-11, used
  already by p03 and p04):
  - `carry_state() -> {"objects": {id: state}, "world": state} | None` (old world): plain data with NumPy arrays.
  - `carry_world(state, laws)` (new world): called once in every carried world after the objects, `state` None when the
    old world gave none; raising starts the world's own state afresh, with the reason in the notice.
  - `carry_note(text, obj=None, restarted=False)`: the section says what it adapted, or what it could not take.
  - `self.carrying`: the previous world's laws during the carry.
  - `ObjectType.stateful` (default: the types with a velocity handle) tells «no state of its own» (a wall, a probe) from
    «state not carried».
- **Storage.** The runner (`sim.Runner._new_world`) takes `carry_export()` (the scene with the objects' ids and the
  heavy state). It writes the heavy state once into the run's checkpoint folder as `carry-w<N>-<ns>.npz`: arrays plus a
  JSON skeleton, written atomically, read with `np.load(allow_pickle=False)` (nothing is unpickled). The file is named
  with its SHA-256 in the new world's `params["scene"]["carry_file"]`, so a restore by replay in another process reads
  the same bytes. A changed or missing file refuses the restore with the reason; it never builds another world.
  - The file of a refused new world is deleted; earlier worlds' files are pruned (only the latest world is restored).
  - `worker.py` gives the folder to `lfviz.playground`; `runs.py` counts the files on the disk and removes cut
    temporary ones at start.
  - A scene file (a REST start, a loaded file) may not name a carried state: `check_scene` refuses `carry_file`
    unless the runner made the world.
- **The notice** (`_carry_report`), recorded and shown, lists:
  - the objects carried «с состоянием»;
  - those «по параметрам (своего состояния нет)»;
  - those whose «состояние не перенесено, начато заново из параметров» (with the section's reason);
  - the values the new world changed (a diff of the carried and the added values, «изменено при переносе — «…»: spread
    3 → 2»; a dropped parameter only when it was not zero);
  - the objects it refused («не перенесены: …»);
  - the world's own state («состояние мира перенесено: …», «состояние мира: … начато заново …»).
  - Its `carry` field holds the same as data: `{objects: [{id, was, label, how, notes, changed}], world: {how, notes}}`.
- **The player** (`player/js/player.js`): the checkbox title and the dialog's note now say that the state goes with
  the objects where the section can carry it, and that the notice says what went how.
- **The reference implementation** is the toy (`tests/playgrounds/p99_toy/viz.py`):
  - a «cloud» type whose points are in no scene file and go through `carry_state`;
  - the world's own state «visits», carried through `carry_world`;
  - a plane rule that changes a carried value, so that an adaptation is reported.

**Not taken: the optional «время с нуля».** A carried world continues the record's time base: its header, the record
and the restore all use it. A second time base for a carry with nothing dynamic would make the same command mean two
things, depending on the scene. The notice now says what is dynamic and what is not, which was the cause of the
confusion. A world from t = 0 is still «Новый мир» without «перенести сцену».

**Verification.**
- `tests/test_carryover.py`, 8 tests, all passing:
  - `test_the_carried_state_is_said_object_by_object_and_the_ids_are_kept`: the cloud's points and the visits are
    equal after the carry; the file's SHA-256 matches the header; the arrays are not in the header; how each object
    went, the changed value and the world's note are checked. A refused new world leaves no file, and a later world
    prunes the earlier world's file.
  - `test_a_section_that_gives_no_state_is_said_to_restart` (negative control): the toy without `carry_state` gives
    other points and zero visits, and the notice says «состояние не перенесено …» and «Состояние мира: посещения ячеек
    начаты заново с нуля». A state the section cannot take is said with its reason. A `carry_world` that raises is
    said as «начато заново — …».
  - `test_a_carried_state_is_plain_data_and_a_scene_file_cannot_name_one`: a round trip of the format; object arrays,
    non-string keys and foreign objects are refused; a scene file naming a carried state is refused; a changed or
    missing file is refused in Russian.
  - `test_a_carried_state_is_resumed_the_same_by_replay_through_the_server`: through a worker with its checkpoints made
    unusable, the first frame after the resume equals the last before it (`t`, `at`, `meas`). Negative control: with
    the file changed, the resume refuses («… изменён — этот мир не восстановить» in `resume_error`) and makes no world.
  - The two older tests now assert the new notice exactly.
- `response_checks_framework/f5_carry_sections.py` → `.out`, on the real sections at the processing time (their hooks
  are by their agents):
  - p03, a new world of the same laws: «все объекты (1). С состоянием — «Молекулы X₂». Состояние мира перенесено:
    случайная последовательность … продолжена».
  - p03 into the plane: the molecules refused with the reason, and the random stream carried.
  - p04 with the same laws: «состояние мира перенесено: течение перенесено как было (440 × 82 узлов …)».
  - p04 with another fluid: the inlet refused, and the flow restarted with the reason (the new grid's τ too close to ½).
- `tests/browser/manipulation.mjs` step 11 (toy, both sizes): the notice in the browser says what went with its state
  and by its parameters, and names what was refused.

### F13 — nit — the edit's log line: no units, wrong gender; `asked` unvalidated; a «clamped» readout that did not clamp

**Status:** fixed [error in earlier] — the log said «ограничено» for a throw below the limit.

**Reproduced** in `test_manipulation`: an edit with `asked = 31.5` and a sent speed of 6 m/s (vmax 12) logged
«ограничено до 12 (бросок дал 31,5)»; `asked = inf` was accepted. The toy's log read «… перемещён в (x = 2, y = -1,5,
z = 0,75)».

**Fix.**
- `server/lfviz/playground.py` `_edit`:
  - the line is «Частица 1»: перемещение в (2; −1,5; 0,75) м; бросок: v = (−0,5; 2; 0,25) м/с»: nouns (no participle
    to agree), the unit from the parameter (or from its label), the player's number form;
  - the axis form is «перемещение: x = 4 м»;
  - `asked` counts only when it is a finite positive number;
  - a clamp is said only when the world clamped, or when the player did (the sent speed equals `velocity_max` and the
    hand's was more): «— ограничено наибольшей скоростью 12 м/с (рука дала 50; уменьшите масштаб броска)»;
  - the hand's speed is named even when the player's rounded speed (12.0004) is clamped here again by a hair: found by
    the browser run, which showed «рука дала 12».
- `player/js/playground.js`:
  - the throw's readout is recomputed while the pointer rests (after `THROW_MS` without a move; redrawn only when its
    text changes, since a redraw per tick slowed the pointer's events in SwiftShader), so it no longer keeps
    «ограничено» from the last move;
  - the readout at the release is kept for the tests (`__lfManip.released()`).

**Verification.**
- `tests/test_manipulation.py`:
  - the exact lines;
  - `asked` ∈ {31.5 with an unclamped 6 m/s, inf, "много", −3}: no clamp in the log (negative controls);
  - the rounding case;
  - `test_the_log_lines_and_numbers_are_in_the_players_form`.
- `manipulation.mjs`:
  - 4c: the readout at the release and the log name the clamp and «уменьшите масштаб броска», with the hand's speed;
  - 4d (new): the pointer stops before the release; the readout drops «ограничено», the throw is sent slow and
    unclamped, and the log says no clamp.

### F14 — nit — the automatic throw scale was anchored to the ceiling `velocity_max`

**Status:** fixed (the reviewer's second option, anchored to the scene's scale; see the reason for not taking ×1).

**Fix** (`player/js/playground.js` `scaleFor`). «авто»: a brisk flick (the view's width in a wall second) throws the
object across the world's region in `AUTO_CROSS_S` = 2 wall seconds at the current playback rate. That is
v = R / (2 s · rate), never above half the declared `velocity_max`, which still clamps.
- It is independent of the zoom and of the units.
- In p01 it gives a planet a speed comparable to orbital speeds at the usual rates, instead of 0.025 c.
- Why not «авто = 1»: ×1 is the hand's speed at the playback rate. It depends on the zoom, and in worlds whose region is
  tiny or whose rate is extreme it gave the absurd throws of review LB1-p02-ux X4 (10¹² m/s, 2.33 c).
- The scale field's help states the rule.

**Verification.** `manipulation.mjs` 4b: the throw at «авто» matches min(R/(2·rate), vmax/2) × (pointer px/s) / (view
px) within the timing jitter, at both sizes. 4 (scale 1.5, rate 2): a scale set by hand is unchanged.

### F15 — nit — carried objects were renumbered

**Status:** fixed.

**Fix** (`server/lfviz/playground.py`).
- `export_message` writes each object's `id`.
- `_add(…, oid=…)` keeps an id of the framework's form (`o<n>`) when it is free, and `next_id` moves past it.
- This holds for a carried scene and for a loaded file; a duplicate or a new object gets the next free id.

**Verification.**
- `test_the_carried_state_is_said_object_by_object_and_the_ids_are_kept`: after `o2` was removed, the carried world
  has `o1, o3, o4, o5`, and the next object is `o6`.
- The notice's `carry.objects[].was` equals `id`.
- The restore-determinism test (`test_a_carried_world_is_rebuilt_the_same_…`) passes unchanged.

### F16 — nit — test gaps (framework part)

**Status:** fixed.
- **F5.** The cases the reviewer named now have tests:
  - a section whose objects export no state (`NoState`);
  - a world state the new world refuses;
  - a carried file changed before a resume;
  - a heavy state through a worker and a replay.
- **F13.** The manipulation tests now have:
  - clamp only when clamped;
  - `asked` validated;
  - the resting pointer in the browser.
- **F6.** Following the instruments agent's change, `test_checkpoint_now_through_a_worker_and_never_resuming` now
  expects 403 for a viewer's `checkpoint_now` over REST, both while running and while suspended. It checks that no
  checkpoint carries the viewer's tag and that the run is not resumed; the path through `Run.command` is kept.
  - The player sends no `stop` through `/command`: there is no stop in `player.js` or `catalog.js`.

## Verification runs (final)

See «Final runs» at the end of `../2026-11-11_internal_LB1-p02-ux/RESPONSE_framework.md`: the same runs answer both
files.

## Changes for the integrator

The texts for RULES, the owner guide and STATUS are in «Changes for the integrator» of
`../2026-11-11_internal_LB1-p02-ux/RESPONSE_framework.md` (one set for both reviews).
