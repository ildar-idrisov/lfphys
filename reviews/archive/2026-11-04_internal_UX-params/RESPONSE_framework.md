# Response (framework and player) to review UX-params (2026-11-04)

Processed on 2026-11-05 by a subagent (Claude) that did not write the review. This file covers the findings assigned to
the framework and the player: **P1, P2, P3, P20, P22, P23** and the framework parts of **P4** and **P8**. On the
integrator's request it also covers the framework part of **P17** (choices shown per option) and, because the code is
the framework's, the framework part of **P28** (an atomic «Очистить сцену»). The world-specific causes are the world
agents' (P5–P7, P9–P16, P18, P19, P21, P24–P33 and the world halves of P4, P8, P17, P28); their responses are their own
files in this folder. The review text is unchanged.

**Environment.**
- A private server: `lf-uxf-srv`, port 8572, `--memory=12g`, CPU only (`LFPHYS_NO_GPU=1`), `LFVIZ_PLAYGROUND_CKPT=6`,
  `--max-workers 2`, image `light-funnel-viz`.
- Chromium of Playwright 1.58.2 with SwiftShader, at 1600×1000 and 1280×800.
- The other agents worked on the same tree at the same time. Where a world changed under a reproduction, that is
  noted below.

**Evidence.** In `response_checks_framework/`:
- `fw_ui.mjs`, `cases_extra.mjs`: the browser checks, run before and after the fixes;
- `out_before.json`, `out_after.json`: their outputs;
- `shots/`: screenshots, looked at;
- `peakmem.py`, `peakmem.jsonl`: the peak memory of every world;
- `tests.out`: the framework tests.

## Decisions

| ID | one line | decision | where | verified by |
|---|---|---|---|---|
| P1 | A world refused at its start was never explained | **fixed** | see «P1» below | see «P1» below |
| P2 | A typed or emptied number was refused as `lam_nm: 0.0 < min 300.0` | **fixed** | see «P2» below | see «P2» below |
| P3 | An exception in `after_header` killed the worker; every ⏺ repeated «Мир не восстановлен» | **fixed** (framework); v13's zero-scale check is the v13 agent's | see «P3» below | see «P3» below |
| P4 | Any exception became a refusal text or a whole traceback in a toast | **fixed** (framework); the world causes P5–P7, P18 are the world agents' | see «P4» below | see «P4» below |
| P8 | No memory limit: one combination took 31 GB of the shared host | **fixed** (framework); v02's dark counts and the other world guards are the world agents' | see «P8» below | see «P8» below |
| P17 | Choices always refused for the chosen particle were offered | framework part **fixed** (on the integrator's request); filling v02's options is the v-worlds agent's | see «P17» below | see «P17» below |
| P20 | «Действие boost: …» used the action's id | **fixed** | `sim.py` | see «P20» below |
| P22 | A slice plane moved past the box showed an empty window | **fixed** | `planes3d.py` | see «P22» below |
| P23 | Honest failing checks with no word about why | **partly fixed**: the framework's mechanism is in place; the presets' texts are the world agents' | see «P23» below | see «P23» below |
| P28 | A refused removal half-removed an object; «Очистить сцену» was not atomic | framework part **fixed**; the order in p02's `on_remove` is the p02 agent's | `playground.py` | `test_place_palette_state_and_removals_asked_first` |

### P1 — a refused start is said where the owner set the parameters

**Changes.**
- **Server.** A run whose first world was never built is no longer counted as resumable. Before, `history_end` counted
  `failed` as resumable [error in earlier], so the page said «приостановлен — ⏺ продолжит».
- `history_end` carries `start_error`, and the run list carries `error` (the reason).
- Before a worker is spawned, the server asks the world's optional `check_params` and `estimate_bytes`. A refusal answers
  400 with the reason and the refused fields.
- **Player.** Errors and notices that arrive before any world are kept, shown in «События» and as a toast. The status
  reads «мир не создан — причина в «Событиях»», and ⏺ says why instead of «старая запись».
- **Catalogue.** A start waits up to 8 s for the world to be built or refused. A refusal is shown on the card, next to «▶
  Запустить», and the owner stays on the form. A world that takes longer opens in the player, which says why if it is
  refused later. The run list shows «мир не создан» with the reason.

**Files.** `server/lfviz/runs.py`, `app.py`, `sim.py`, `worker.py`; `player/js/player.js`, `catalog.js`;
`player/index.html`.

**Verified.**
- `test_server.py::test_worker_reports_refused_laws` was rewritten. The old trigger, v01 «эфир» with GR, is no longer
  refused after the v01 agent's P12. The new trigger is v04 with the start inside the body. The test checks:
  - the run is `failed`;
  - the error starts with «Мир не создан: »;
  - the run list has the same `error`;
  - `history_end` has `resumable: false` and `start_error`;
  - nothing of a world is recorded.
- `test_a_check_refusal_of_parameters_is_said_at_the_start` (400 with the reason, and with `fields`).
- In the browser (`p1_v13_super`, now on v04 because v13's defaults no longer refuse, and `p2_catalogue.refused_start`):
  - the page says «мир не создан — причина в «Событиях»»;
  - «События» shows «⚠ Мир не создан: r₀ = 2.1M внутри тела (радиус 67.722M)», also as a toast;
  - the catalogue row reads «мир не создан» with the reason;
  - started from the form, the catalogue stays on the form and shows the same reason under the button
    (`shots/after_p1_refused_start_1600.jpg`, `after_p2_catalogue_refused_start.jpg`; before: the review's
    `pw/shots/P1_v13_refused_start.png`).

### P2 — numbers refused in the owner's words, at the field

**Changes.**
- `params._coerce` answers with the label and unit, the value and the allowed range:
  - «Длина волны λ, нм»: 2000 — больше наибольшего 1600; можно от 300 до 1600;
  - «…: поле пустое — введите число от 300 до 1600»;
  - «…: «abc» — не число»;
  - «нет варианта «x»; можно: …»;
  - «нет сценария «x»; есть: …».
- Each error carries the parameter's id (`ParamError.pid`), and `POST /api/runs` returns `fields`.
- In the player (`ui.js`), a live control checks a typed number before sending it. It refuses it under the control, in
  the same words, and goes back to the value in force. A form keeps an emptied field's value and says what to type. A
  value out of range is marked at its field, and the catalogue refuses to start with it.

**Files.** `server/lfviz/params.py`, `app.py`, `runs.py`; `player/js/ui.js`, `catalog.js`.

**Verified.**
- `test_parameter_refusals_are_in_the_owners_words`: no `max`, `min`, `cannot`, `unknown` or id remains in the texts.
- Browser `p2_catalogue` at 1600 and 1280: the start is refused on the card, and the field is marked. An emptied field
  keeps 2000 and says «поле пустое — введите число от 300 до 1 600» (`after_p2_catalogue_above_*`,
  `after_p2_catalogue_empty_*`).
- Browser `p2_live`: the inline note is shown, the value 633 is kept, and nothing is sent (`after_p2_live_1600.jpg`).
- Before (`out_before.json`): the toast «Изменение не применено: lam_nm: 2000.0 > max 1600.0».

### P3 — a world that fails to show itself

**Changes.**
- `Runner._start_world` no longer swallows failures, and `after_header` and the t = 0 advance are inside it.
- `Runner.start()` reports a first world that fails as «Мир не создан: …» (the owner's text, `lfviz.errors`). The worker
  then ends with the reason `world not built`, and the server keeps that run `failed`, never resumable. The first world
  is not held back: a world that takes long to show itself (v08's slices on the CPU) is drawn as it comes.
- A **new** world that fails so is refused as a whole. Its messages are held while the command runs and dropped, the
  previous world goes on, and the text says «Новый мир не создан: … Прежний мир продолжается».
- The cause in v13 (a continuity check divided by a zero scale) is for the v13 agent.

**Files.** `server/lfviz/sim.py`, `worker.py`, `runs.py`.

**Verified.** `test_a_world_that_fails_to_show_itself_is_not_built`:
- the toy section with an `after_header` that raises gives «Мир не создан: внутренняя ошибка мира — деление на ноль
  (ZeroDivisionError) …» and `end: world not built`;
- a new world failing so leaves the old world and its number unchanged and records no header;
- a real worker whose run ends so is `failed`, and its `history_end` has `resumable: false` and `start_error`.

### P4 — no raw exceptions or tracebacks to the owner

**Changes.**
- New `lfviz/errors.py`: `Refusal(text, hint)` (a `ValueError`; the integrator's API) and `owner_text(exc, context)`
  for every path: set, action, scene, view, new world, the first world, restore, and a failure while computing. It
  works as follows:
  - a `Refusal` is shown with «Что изменить: …»;
  - a plain `ValueError` keeps its own text, as before;
  - known English library sentences are put into the owner's terms («Unable to allocate…», «Probabilities contain
    NaN», division by zero, «worldline is not timelike»);
  - any other exception reads «…: внутренняя ошибка мира — <что> (<Тип>) — запуск сохранён, можно вернуться назад или
    изменить параметры» (for a first world: «измените параметры и запустите снова»).
- The exception's own one-line text goes into the message's `detail`, which the player folds under «подробности» in
  «События». The traceback goes only to the run's `worker.log`.
- A failure while computing reads «Расчёт мира остановился на t = …: … Мир на паузе; ⏺ продолжит.» It is no longer
  a traceback in a toast.

**Files.** `server/lfviz/errors.py` (new), `sim.py`, `worker.py`, `app.py`; `player/js/player.js`.

**Verified.**
- `test_owner_text_of_refusals_and_failures`: no traceback reaches the text or the detail, and the detail is one line.
- The world tests that inject failures still pass. v05's injected `ZeroDivisionError` still appears, by type, in the
  set refusal; that test was not changed.
- Before (UX-ui review, `shots/err_p03_hard_atom.jpg`): the whole traceback was in a toast. The p03 trigger of that
  shot is gone: the p03 agent removed the «hard» option from the start form, and the server now answers it with the
  Russian field error «нет варианта «hard»».

### P8 — a memory budget for the workers

**Changes.**
- New `lfviz/limits.py`. Every worker gets a budget and sets it as its own hard `RLIMIT_DATA` before it builds a world.
  `RLIMIT_DATA` counts private writable memory (NumPy arrays) and not the address space a CUDA driver reserves, unlike
  `RLIMIT_AS`.
- The budget is `--worker-mem-gb` (new option of `serve.py`). By default it is 60 % of the memory the server may use —
  the container's limit, else the host's — at least 1 GB and at most 8 GB. On the owner's compose (6 GB) that is
  3.6 GB per worker.
- Measured peaks of every world's defaults and three presets on the CPU are below 1.75 GB (v08), so no world of today
  is refused by it (`peakmem.jsonl`).
- An allocation beyond the budget fails inside the worker. It is reported as «не хватает памяти (запрошено …), а
  вычислителю отведено …. Что изменить: …» and the host is never touched.
- A world's `estimate_bytes(params)` (the integrator's API) is checked before it is built: at `POST /api/runs`
  (400 with the numbers) and in the worker for a new world.
- `limits.require(nbytes, what, change)` refuses a large allocation while a world runs.
- The guards of v02's dark counts, p04's grid and p03's cells are the world agents' (P8, P25, P33).

**Files.** `server/lfviz/limits.py` (new), `worker.py`, `runs.py`, `sim.py`, `errors.py`; `server/serve.py`.

**Verified.** `test_workers_hold_a_memory_budget`:
- a process with a 600 MiB budget gets `MemoryError` for a 2 GiB array, reported in Russian;
- an estimate of 80 GB is refused at the start with «Сетка 440 × 180 400 000 узлов потребует около 80 ГБ памяти, а
  вычислителю отведено 1,5 ГБ. Что изменить: уменьшите nx», and nothing is started;
- `/proc/<worker>/limits` of a real worker shows `Max data size` = the budget.

Not verified here: the limit with CUDA on GPU 0 (CPU only in this session). This goes to STATUS, item (f) of the
integrator's section.

### P17 — choices shown per option (framework)

**Changes.**
- An option may be `(value, label, show_if)`, and `to_json` emits its `show_if`.
- The forms (`paramForm`: catalogue and «Новый мир») hide options that do not apply. When the current value is hidden,
  the first shown option is chosen and a note under the field says so.
- The live set-up hides them too, but only flags a value in force that does not apply; it does not change the world
  by itself.
- `Schema.resolve` does not enforce it: the world refuses in Russian.

**Files.** `server/lfviz/params.py`; `player/js/ui.js`, `player.js`.

**Verified.** `test_parameter_refusals_are_in_the_owners_words` (to_json, and the modified-physics label with a triple).
A browser check waits for a world that uses it (v02).

### P20 — action refusals by the action's label

**Changes.**
- The runner keeps the header's action labels. A refused action reads «Действие «Толчок» не выполнено: …».

**Files.** `server/lfviz/sim.py`; `v04_orbits/tests/test_v04_orbits.py:126` (the assertion of the old wording, changed
on the integrator's permission).

**Verified.** `v04_orbits/tests` pass.

### P22 — a slice plane past the box stays a grid step inside

**Changes.**
- `planes3d._canonical` clamps the plane's distance to the box shrunk by `plane_min_step`.
- The view's text says «дальше края области срез пуст — плоскость поставлена у края, внутри области».

**Files.** `server/lfviz/planes3d.py`.

**Verified.** `test_a_slice_plane_asked_beyond_the_box_stays_a_step_inside`.

### P23 — honest failures said as such (framework part)

**Changes.**
- A check message may carry `expected` (why its failure is expected here), and `running_check(..., expected=…)` sets
  it for playgrounds. The player draws such a failure as an amber «✗» with «Ожидаемо: …» and counts it apart («N ✗
  ожид.»).
- A preset's `note` is now shown under the scenario selector in the catalogue and in «Новый мир».

**Not done here.**
- Writing the notes and `expected` for v02 «triple_mod», «vector_narrow», v06 «strong» and v16 is the world agents'.
- No world emits `expected` yet, so the drawing is checked by reading the code, not in a browser. This goes to STATUS,
  item (e) of the integrator's section.

**Files.** `server/lfviz/playground.py`; `player/js/player.js`, `catalog.js`; `player/run.html`.

### P28 — «Очистить сцену» all or nothing (framework part)

**Changes.**
- `scene clear` first asks the section's optional `can_remove(obj)` for every object. A refusal names the objects and
  removes nothing.
- `remove` asks it too.
- p02's own order (popping `ref` before the engine refuses) is the p02 agent's.

**Files.** `server/lfviz/playground.py`.

**Verified.** `test_place_palette_state_and_removals_asked_first`.

## Tests run

All in the image, CPU (`response_checks_framework/tests.out`).

- **Final run** (2026-11-05, 08:10): `tests/test_server.py`, `test_playground.py`, `test_restore.py`,
  `test_checkpoint.py` and `v04_orbits/tests` → **172 passed**.
- **After the last framework change** (`_placed` keeps a scalar `position`; see the UX-ui response, U4):
  `test_server.py` and `test_playground.py` were run in full, and the playgrounds' cases of `test_restore.py` and
  `test_checkpoint.py` (`-k p0`) again.
- **An earlier long run** (02:10–02:32) had 141 passed and 2 failed: `test_a_session_around_a_checkpoint_continues_as_the_original[p04_fluids]`
  and `[v06_qcd]`.
  - Cause: their agents changed `p04_fluids/viz.py` and `v06_qcd/viz.py` during the run (02:30, 02:26), so the test's
    child process ran newer code than the original.
  - Run again on the files as they then were: 2 passed. Both pass in the final run.
- `tests/browser/keyframes.mjs`, all worlds, on the private server with the final code: «all equal». The output is in
  the UX-ui folder's `response_checks_framework/keyframes.out`.

## API for the world agents

The integrator's decision of 2026-11-05, as implemented. Everything is optional and compatible: worlds without these
hooks behave as before.

1. **Refusals.** `from lfviz.errors import Refusal`; `raise Refusal(text, hint=None, detail=None)`.
   - It is a `ValueError`. `text` is what is wrong and `hint` is what to change, both Russian; the object or the
     parameter is named by its label, and numbers carry their units.
   - The page shows «<что не сделано>: text. Что изменить: hint» in the toast, «События», the status, and the catalogue
     card or run list.
   - `detail` is optional: the engine's own one-line sentence, folded under «подробности».
   - A plain `ValueError` keeps its own text. Translate the engine's English refusals at your boundary.
2. **Check before building.**
   - `@classmethod check_params(cls, params)` raises `Refusal` for a combination that cannot be built; it must be
     cheap. The server calls it before a run starts (the catalogue shows the reason on the form, with the field when
     it is one parameter) and the worker before a new world.
   - `estimate_bytes(params) -> int | (int, what, change)`, preferably a `@classmethod`, gives the memory the world will
     allocate. Above the worker's budget the world is refused before it is built.
   - While running, call `lfviz.limits.require(nbytes, "что занимает", "что изменить")` before a large allocation.
3. **Playgrounds** (`PlaygroundSimulation`).
   - `place(self, kind, values) -> values` is called on every palette add. `values` is what the owner set in the
     pre-placement form, plus `position: [x, y, z]` when he clicked a point. Return the completed values (a free spot, a
     free side), or raise `Refusal`. A `position` left in the result goes to the type's `x`, `y`, `z`. It must be
     deterministic, because a restore repeats it.
   - `palette_state(self) -> {kind: None | "причина"}` is sent in every `scene` message. The player disables those
     buttons and shows the reason as the tooltip and under the button.
   - `can_remove(self, obj) -> None | "причина"` is asked before a removal and for every object before «Очистить
     сцену».
   - `running_check(..., expected="почему")` marks a failure that is the point of a scene.
   - All of these are cheap and never change the world's state.
4. **Checks and events.**
   - `"expected": "почему провал ожидаем"` in a check marks an honest failure (P23).
   - `"notify": true` in an `event` is shown as a toast when it happens (e.g. «Звезда 2 слилась с Солнцем через 0,05
     года после добавления»; UX-ui U4 (3)).
   - A preset's `note` is shown with the scenario in the catalogue and in «Новый мир».
5. **Options shown per choice.** `Param.options` may hold `(value, label, show_if)`. Code that does `dict(p.options)` must
   become `{o[0]: o[1] for o in p.options}`; v05's `viz.py:824` does that today.
6. **Live laws in playgrounds.** A `live=True` law is shown in «Законы мира — меняются сразу» and applied by the
   section's `set_live` / `live_values`, as in demonstrations. A scene file takes the live values in force.
7. **Where an object is** (the playgrounds' «◎ Центрировать» / «👁 Следить», UX-3d A6): the frame's optional
   `at: {id: [x, y, z]}` is used first. Without it, the frame's `ids` with an array `pos` of one point per id (as p01)
   are used, else the object's set x, y, z. Add `at` for objects whose moving centre only the section knows, e.g. p02's
   packets.
8. **Placing by a click.** The pre-placement form takes its point from a slice window, always, and from the 3-D scene:
   the plane z = the middle of the box under the pointer. A view may pass its environment,
   `createPlayground(ctx, { …, env })`; without it the page's 3-D view is found by itself.
9. **Busy and cancel** (the framework's, nothing to implement).
   - Every computing command (step, ⏭ событие, set, action, view, scene, new world) is announced, held, and written as
     one piece.
   - The player shows what is being computed and for how many seconds, and offers «✕ отменить», which puts the world
     back to just before the command.
   - A world's command must therefore not write files or other state outside the world that a cancel could not undo.

## Changes for the integrator

**`engine/STATUS.md`** — a new item after V44 (exact text):

> | V45 | The player and the framework after the UX reviews of 2026-11-04 (`reviews/2026-11-04_internal_UX-ui/RESPONSE_framework.md`, `…_UX-params/RESPONSE_framework.md`). Open: (a) v07's 2×2 panels print their labels over each other below ~900 px of centre width (UX-ui U20: the view's own layout); (b) the 3-D click of the pre-placement form gives a point of the plane z = the middle of the region only; picking objects, dragging them and velocity handles (U11) are not done; (c) a cancel resumes the world from its last checkpoint and repeats the record after it, so a slow command earlier in that tail is computed again, and the first world's build («строится мир») cannot be cancelled from the player; (d) a computing command's messages are held in the worker's memory until it is done (a new v08 world holds its volumes, ~100 MB, before they are written); (e) checks marked `expected` and the presets' notes are drawn by the player, but no world emits them yet (UX-params P23: v02, v06, v16); (f) the workers' hard memory limit (`RLIMIT_DATA`) was tested on the CPU only: with CuPy on GPU 0 it must be checked on the owner's server (expected to work: the driver's reservations are not private writable memory). | (a) the v07 view lays its panels out by the width it gets (2×1 below 900 px); (b) picking in `scene3d` (the 3-D environment's own work); (c) a checkpoint before a command that is expected to be slow, a cancel of the first build that leaves the run «not started»; (e) the world agents fill them; (f) one run of v08, v11 and v12 on GPU 0 with `--worker-mem-gb 3.6` | open |

Also V37 (h) closes: «(h) [closed 2026-11-05: `clear` asks every object's `can_remove` before it removes any (UX-params
P28)]». V37 (d) gains the sentence «a command still being computed can be cancelled (UX-ui U9); a change already
applied cannot be undone».

**`visualizations/RULES.md`** — exact additions.

1. §3, the REST table, after the row of `/resume`:

   > | POST | `/api/runs/{id}/cancel` | cancel the command the worker is computing now: the worker is ended, nothing of the command is recorded (it is announced by `busy` and written only when done), and the run is resumed from its record — the world as just before the command; 409 when nothing is being computed |

2. §3, after the WebSocket paragraph:

   > **Busy.** Every computing command (`step`, `next_event`, `set`, `action`, `view`, `scene`, `new_world`) and the
   > first world's build are announced by the worker with `busy {on: true, cmd, what, wall}` before they start and
   > `busy {on: false}` when they end; the command's own messages are held and written after that end, as one piece
   > (`lfviz.worker.Output`). `busy` is forwarded to the viewers and never recorded; a late viewer gets the current one
   > after `history_end` with its `elapsed` seconds. The player shows what is being computed, for how long, and «✕
   > отменить» (`/cancel`). A world's command must therefore change nothing outside the world's state.

3. §3, a new paragraph «Refusals and failures» before «Message format»:

   > **Refusals and failures (owner, 2026-11-04: «если ошибки … должно быть все понятно и удобно»; reviews UX-params P1–P4,
   > UX-ui U13).**
   > - What the owner reads is Russian and says what to change; it is never a traceback.
   > - A world refuses with `lfviz.errors.Refusal(text, hint)`: the object or the parameter by its label, numbers with
   >   units, and in `hint` the change that makes it work. A plain `ValueError` keeps its own text.
   > - Any other exception is shown as «<что не сделано>: внутренняя ошибка мира — <что> (<Тип>) — запуск сохранён,
   >   можно вернуться назад или изменить параметры». Its one-line text goes into the message's `detail` (folded under
   >   «подробности»), and its traceback only into the run's `worker.log`.
   > - Parameters are refused by the schema with their label, unit and range, and each error carries the parameter's id
   >   (`ParamError.pid`; `POST /api/runs` answers `{error, fields}`).
   > - A combination a world cannot build is refused before anything is started: `Simulation.check_params(params)`
   >   (cheap), asked by the server at the start and by the worker for a new world.
   > - A first world that fails to show itself (its header, `after_header`, the t = 0 advance) is reported «Мир не
   >   создан: …» and ends with `end {reason: "world not built"}`. Such a run is failed, never resumable. `history_end`
   >   says why (`start_error`), and so do the run list (`error`) and the catalogue's card.
   > - A new world that fails so is refused as a whole, and the previous world goes on.

4. §3, a new paragraph «Memory budget» after «Refusals and failures»:

   > **Memory budget (review UX-params P8: one world took 31 GB of the shared host).**
   > - Every worker holds a budget as its hard limit of private writable memory (`RLIMIT_DATA`, `lfviz.limits`). The
   >   server option is `--worker-mem-gb`. By default it is 60 % of the server's memory (its container's limit, else
   >   the host's), from 1 to 8 GB.
   > - An allocation beyond it fails inside the worker and is reported in Russian. The host and the other runs are not
   >   touched.
   > - A world says what it will allocate: `estimate_bytes(params)` before it is built (checked by the server at the
   >   start and by the worker for a new world), and `lfviz.limits.require(nbytes, what, change)` before a large
   >   allocation while it runs. An estimate above the budget is refused at once, with the numbers and what to change.

5. §3, the message table:
   - the `check` row gains «`expected?` (why a failure is expected here: drawn as an expected ✗ with the reason)»;
   - the `event` row gains «`notify?` (shown as a toast when it happens)»;
   - the `notice`, `error` row reads «text for the owner (Russian, §3 «Refusals and failures»); `detail?` the
     exception's own one line».

6. §1 or §3 on parameters, one sentence:

   > A select's option may be `(value, label, show_if)`: the forms show it only when `show_if` holds (the schema does not
   > enforce it; the world refuses in Russian).

7. §6, the playground's bullets, a new bullet after «The scene»:

   > * **Placing and the palette** (reviews UX-ui U4, U7, U22; UX-params P28):
   >   - a palette button opens a pre-placement form with the type's parameters; the point is typed, or clicked in the
   >     3-D scene (the plane z = the middle of the region) or in a slice window;
   >   - the section's optional `place(kind, values)` completes the values (a free spot, a free side; `position` [x, y,
   >     z] is the clicked point) or refuses;
   >   - `palette_state()` names the types the world cannot take now (the buttons are disabled with the reason);
   >   - `can_remove(obj)` is asked before a removal and for every object before `clear`, which removes all or nothing;
   >   - these hooks are cheap, deterministic and never change the world;
   >   - the latest set-like messages repeated at a segment's start carry `repeat: true`, and a viewer holding the same
   >     message ignores them (UX-ui U1).
   >
   > A playground's laws marked `live` are shown and applied at the current moment as in demonstrations.

**Owner guide** (`visualizations/README.md`, Russian; optional, for the integrator), a paragraph in the part on the player:

> Если мир долго считает изменение (сцена, установка, новый мир), вверху видно, что именно и сколько секунд; «✕ отменить»
> вернёт мир в момент перед этим изменением. Если мир с выбранными параметрами создать нельзя, каталог скажет почему прямо
> под кнопкой «▶ Запустить», а поле с неподходящим значением подсвечивается. В плейграунде кнопка палитры открывает
> параметры объекта; место можно задать числами или щелчком в сцене («⌖ Указать место в сцене»), затем «Поставить».
> ⇤ и ⇥ вверху (клавиши [ и ]) прячут боковые колонки. Каждому вычислителю отведена своя память
> (`--worker-mem-gb`, по умолчанию 60 % памяти сервера, не больше 8 ГБ): мир, которому её не хватит, откажет с объяснением,
> а не займёт память всего компьютера.
