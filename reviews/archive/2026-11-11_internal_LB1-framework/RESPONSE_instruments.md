# Response (instruments part) to the review LB1-framework

**Responder:** the instruments processing agent (prefix `lf-lpi-`). It did not write the review and did not write the
code under review. **Date:** 2026-11-11/12.

**Scope of this response:** F1, F2, F3, F4, F6, F7, F8, F9, F10, F11, F12, and the instruments part of F16. F5, F13,
F14, F15 and the framework part of F16 are answered by the framework processor (`RESPONSE_framework.md`).

**Environment.** Image `light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`), everything in Docker from `engine/`.
- Private server `lf-lpi-srv` (port 8611, `--memory=6g`, 3 workers, `LFVIZ_PLAYGROUND_CKPT=6`, `LFVIZ_EXTRA` holding
  both fixture folders, as the review used).
- A second one, `lf-lpi-srv2` (port 8619), identical except `LFVIZ_SWEEP_BUDGET_S=20`, for c03/c13.
- For one negative control, `lf-lpi-srvold` (port 8620) served the panel's original `instruments.js` over the new
  server code.
- All three servers were stopped by name; `docker ps -a` shows no `lf-lpi-*` container.
- Browser checks: Playwright 1.58.2 Chromium (swiftshader), `--shm-size=2g --init --network host`.

**Evidence** is in `response_checks_instruments/`.
- `before/`: the reviewer's scripts run on the code as it was.
- `after/`: the same scripts on the processed code, plus our own checks `rc_*`.
- `lbrf_client.py` is the reviewer's client, its port changed and marked `[response]`. `run_check.sh` runs a script
  against the private server; the review's own outputs are never overwritten.

## Summary

| | count | findings |
|---|---|---|
| fixed | 9 | F1, F2, F3, F6, F7, F8, F9, F10, F12 |
| partly fixed, the rest → STATUS | 2 | F4 (the idle wait is gone; the frame's own cost still counts as advance), F11 (off the event loop; a smaller stall remains from the interpreter lock) |
| fixed (tests) | 1 | F16, instruments part |
| rejected | 0 | |

**Two corrections to the review's evidence, both measured:**
- **F8.** The «column jumps 1032 → 445» came from Playwright's `click()`, which scrolls the box into view first. With
  the box's own click, the original panel kept the scroll (1073 → 1073). Its other losses were real and are fixed: the
  focus, the folded groups, the rebuilt rows and the form.
- **F11.** Moving the formatting into a thread does not remove the stall: the thread shares the interpreter lock with
  the event loop. It shrinks it, measured from another process (rc_c05c).

**R12 of the review [error in earlier].** The instruments agent proposed the STATUS item «a run deleted during a sweep
ends that process within ~1 s». That was not so before this processing (c03). It is now, by the server's watch (F3).
The proposal is replaced by the text in «Changes for the integrator» below.

**Other agents' files.** None were edited. One effect on them: PF's `tests/test_manipulation.py`
(`test_checkpoint_now_through_a_worker_and_never_resuming`, its last REST post) asserts HTTP 200 for a client's
`checkpoint_now`. After F6 it gets 403. PF was told through main on 2026-11-11.

## Findings

### F1 — an object-parameter sweep did not apply a value equal to the stored one — **fixed** [useful]

**Fix.** `server/lfviz/sweep.py` (`apply_change`, `_again`), `player/js/instruments.js` (`showCur`), and the fixture
`tests/instruments_worlds/p97_osc` (new type `ball` with handles and `at`). Every value of an object's parameter is now
applied, the stored one too:
- **A handle parameter** (a position or a velocity) goes through the scene's `edit`. The framework's `edit` applies
  equal values (`old[k] = None`).
- **Any other parameter** goes through `set`. When the value equals the stored one, the section's `on_set` receives in
  `old` a stand-in for the stored value: the same number or text for anything computed with it, but equal to nothing.
  So the parameter counts as changed and is applied again, as every other value of the sweep is.
  - Not `None`: p03's `on_set` computes with `old` for non-handle parameters, e.g. `float(old["mass"])` and
    `"xyz".index(old["axis"])`.
  - The stand-in exists only in the swept world's `old`. A refused change restores the stored value.
- **A flag (`bool`)** cannot have such a stand-in. Its row says «равно заданному значению флажка: мир без изменения».
- **The result.** Each row records how the value was applied (`how`: `set`, `set_again`, `edit`, `set_same`). It notes
  a value the world changed, such as a throw clamped to `velocity_max`.
- **The panel** shows «Задано: …»:
  - for a handle's position, also «объект сейчас в … (последний кадр)» from the frame's `at`;
  - for a velocity, that it is the last throw's;
  - for any other parameter, that it is the object's parameter, not necessarily its state now.

No framework change was needed.

**Verification.**
- `tests/test_sweeps.py::test_an_object_parameter_equal_to_the_stored_one_is_applied_again`. On p97 at t = 0.5 s: the
  oscillator's `x` and `v` (through `set`), and the ball's `x` and `vy` (through `edit`), each over {a, stored, b}.
  - Every value matches the closed form of «set to that value at t0» to 1e-12.
  - Negative control: at the stored value, the closed form of «left as it was» is off by more than 1e-3.
  - Negative control of the test itself: with `_again` disabled, the stored value's row equals the old defect.
  - The flag row says «без изменения».
- `after/c01_sweep_closed_form.out`: rows (b) x = 1 and (c) v = 0 are now «set»; before they were «NO CHANGE»
  (`before/`).
- Browser: `tests/browser/instruments_checks.mjs`, «F1 «Задано» and where the object is now» — the shown position equals
  the record's last o2.x.

### F2 — the budget was not enforced inside one advance — **fixed** [useful]

**Fix.** `server/lfviz/sweep.py`: `Clock`, `run_value`, `SweepManager._watch`; the panel's default duration in
`player/js/instruments.js`.
- **In pieces.** The process advances along the world's own steps (`Runner._advance` with a wall budget of
  `CHUNK_S` = 0.25 s, repeated). Between pieces it looks at its clock and stops in two cases:
  - its wall time passes `OVERRUN` × the budget;
  - after `PROBE_S` = 3 s of advancing, the cost it measured projects the whole sweep beyond that. The rate is the
    larger of the whole sweep's and the current value's, so a swept value that costs more, such as a finer step, is
    seen.
- **Unknown cost.** A world whose cost is unknown is not refused. The sweep measures itself in its first seconds: this
  is the review's «probe value», done in the process.
- **The server's watch.** It ends a process still running `WATCH_GRACE_S` = 30 s after `OVERRUN` × the budget (one
  step of the world longer than the budget). The values computed are kept, and the state is `over_budget`, «Остановлено
  сервером».
- **The panel's default duration** is five wall seconds of the world at its chosen speed (X7).
- **The same numbers.** The pieces follow the world's own steps, so the swept world's numbers do not change: c10 is
  still bit for bit.

**Verification.**
- `test_the_budget_holds_inside_one_advance`:
  - a one-reading sweep of 10⁷ s of p97 (≈ 50 min per value) with a 20 s budget stops by itself in under
    `PROBE_S` + 15 s, as `over_budget`, with the projection in the message;
  - negative control: 50 s of world time is done.
- `test_lb1_server_side`: a swept value that makes one step cost 20 s is ended by the server within 1.5 × 2 + 2 + 5 s
  (budget 2 s, grace shortened to 2 s).
- `after/rc_c03b_budget_and_deleted_run.out` (the reviewer's c03 on the budget-20 server): (a) `over_budget` after
  3.3 s, «весь свип занял бы около 13 мин 41 с». Before, the review found it still running at 45 s.
- `after/rc_c13b_default_sweep_p03.out` (p03, the old default of 1 s of world time): `over_budget` after 3.7 s. Before,
  it was still running at 60 s.
- `after/c10_sweep_vs_live.out`: p03 and p04 still equal the live world bit for bit, and the final reading still does
  not depend on the number of readings.

### F3 — a deleted run's sweep kept running — **fixed** [useful]

**Fix.** `server/lfviz/sweep.py`: `_watch`, `Clock.check`, `main`, and the cancel route.
- **The server's watch.** Once a second it looks at whether the run is still the manager's and its folder still
  exists. If not, it ends the process. That covers `DELETE /api/runs/{id}` and the retention clean-up (`_remove`): both
  take the run out of `RunManager.runs` and remove the folder.
- **The process itself** exits quietly when its folder is gone: it checks at most once a second between pieces of an
  advance, and before every write.
- **`POST /sweeps/{n}/cancel`** cancels an active sweep by its key even when the run is gone, and answers 404 once it
  has ended.

No `runs.py` hook was needed.

**Verification.**
- `test_lb1_server_side`: after `DELETE /api/runs/{id}` the sweep's process ends in under 5 s and its server-wide
  place is free.
- `after/rc_c03b_budget_and_deleted_run.out` (b): a sweep still running when its run is deleted is gone. A second and
  a third run's sweeps are both accepted; before, the third got 409, «на сервере уже идут 2 свипа». The process list at
  the end shows no process of the deleted run.

### F4 — the cost estimate counted the runner's idle wait — **partly fixed; the rest → STATUS** [useful]

**Fix.** `server/lfviz/sweep.py`: `measured_cost`, `estimate`.
- **Which frames count.** Only frames computed while the world played: `speed_actual` set, so at least 0.75 s at one
  speed, and no recorded command or checkpoint since the previous frame. Their `cpu_ms` is the advance plus the frame;
  no queue wait. A world only stepped has no measured cost, and its sweep measures itself (F2).
- **What remains.** Every frame of a playing world advances, so the frame's own cost (`frame()`) cannot be separated
  from the advance. The estimate is therefore an upper bound, and it says so.
  - For a world whose cost is its advance, it is within 5 %.
  - For p97, whose 10 oscillators cost less than their frame, it is about 13 times too high. Before: 57 times played,
    2600 times stepped.
- The full fix needs the advance's own time in each frame. That is the runner's (`sim.py`, framework), hence STATUS.

**Verification.**
- `test_the_estimate_counts_computation_only`. On p97 with `cost_ms` = 40, a fixture law that makes the advance cost
  40 ms per world second:
  - a stepped-only record: the estimate is «unknown»;
  - played: within a factor 3 of the advance the sweep then measures;
  - negative control: the old estimator, every frame's `cpu_ms` over its world time, is more than 3 times off on the
    stepped record.
- `after/c08_sweep_estimate.out`:

  | case | before | after |
  |---|---|---|
  | (A) stepped | 830 ms per world second, 2600× too high | unknown |
  | (B) played | 17.8 ms per world second, 57× too high | 4.8 ms per world second, 13× too high, an upper bound |

  The sweep itself measured 0.30–0.37 ms per world second.

### F6 — any viewer could force `checkpoint_now` — **fixed** [useful]

**Fix.** `server/lfviz/app.py` (`SERVER_ONLY`, `client_command`) and `sweep.py` (the tag).
- `POST /api/runs/{id}/command` and the WebSocket refuse the server's own worker commands `checkpoint_now` and `stop`:
  403 over REST, a text `{error}` over WebSocket.
- A body that is not an object `{cmd, args}` is 400.
- Only the sweep code sends `checkpoint_now`, through `Run.command`. Its tag is made by the server: «sweep-» and
  12 hexadecimal digits. Since no client can send the command, the tag is bounded by construction.

**Verification.**
- `test_lb1_server_side`: REST `checkpoint_now` and `stop` give 403 «посылает только сам сервер». The WebSocket answers
  the same text. No checkpoint is added to the record, and the run goes on.
- `after/c04_checkpoint_now_from_a_viewer.out`:

  | | before | after |
  |---|---|---|
  | HTTP status | 200 | 403 |
  | checkpoints written | 41 | 1 (the world's own periodic one) |
  | viewer tags answered | 41 | 0 |

### F7 — a sweep did not state its sampling; the CSV omitted the base moment — **fixed** [useful]

**Fix.** `server/lfviz/sweep.py` (`sampling`, `stat_text`, `table_csv`, `fmt_t`) and `player/js/instruments.js`.
- **`stat_text`** names the readings and their spacing: «максимум по 201 замеру через 1,5 с», «среднее за последние
  300 мс (31 замер через 10 мс)», «в конце (1 замер)».
- **The result header** says «каждое значение — 300 с мира от t = 2,95671 с».
- **The form** shows the spacing next to «Замеров»: «201 замеров через 1,5 с».
- **The table's CSV** starts with three «#» lines:
  - the sweep in words;
  - the base moment, its source, the duration, the readings, their spacing and the sampler (`measure()` or `frame()`);
  - the same as `key=value`;
  then the header line.
- **Not done:** the review's optional warning against a period the world reports. No world reports one; the spacing
  is shown instead (the review's minimum).

**Verification.**
- `test_sweeps.py::test_sweeps_through_the_server`: the CSV's «#» lines carry `base_t`, `readings` and `sampler`; the
  mean's `stat_text` gives 31 readings at 10 ms.
- Browser: «F7 the result states the sampling and the base moment», «F7 the table's CSV states them too», «F7 the
  readings' spacing next to their number».
- `after/b02_instruments_panel.out`: the review's checks 9 and 10 now pass.

### F8 — the «Приборы» panel lost focus, folds, scroll and form values — **fixed** [useful]

**Fix.** `player/js/instruments.js`. Nothing the owner is using is rebuilt under him:
- **The quantities' list.** The groups and rows live in maps by id and are updated in place. A node is moved only when
  it is out of order. A group's folded state is the owner's, kept per run in this browser. Ticking a quantity changes
  only the plots.
- **The plots** are kept by id.
- **The sweep form** is built once per world. Its lists of targets and measures are refreshed in place, keeping the
  choice and everything typed.
- **A sweep's result block** is built once per sweep. The state, the progress bar and the message are updated; the
  table grows by rows; the plot is redrawn on the same canvas.
- **The sweeps' list** is rebuilt only when it changed.

**Verification.** `tests/browser/instruments_checks.mjs` part 2, at 1280×800 on p97 «ball» with 8 more oscillators:
- the focus stays on a quantity ticked with Space;
- a folded group stays folded;
- the rows are the same nodes and the column's scroll is kept (1010 → 1010) after a tick;
- the form keeps «1; 2; 3» across folding;
- during a running sweep the table, the canvas and the first row are the same nodes, and the scroll is kept.

All pass (`after/instruments_checks.out`, 24 of 24).

**Negative control.** The same checks against the original panel (`lf-lpi-srvold`), in
`before/instruments_checks_old_js.out`:
- the focus goes to BODY;
- the group reopens;
- the rows are rebuilt;
- the form is emptied;
- the units are doubled (X9).

**Correction to the evidence.** With the box's own `click()` the original panel kept the scroll (1073 → 1073). The
review's 1032 → 445 was Playwright scrolling the clicked box into view. The reviewer's own `b02` therefore still
reports that check after the fix (`after/b02_instruments_panel.out`, 7 of its 9 checks pass). Its other «failure»
parses the old «Сейчас: …» of p97's oscillator `x`, which is not a handle. The panel now says that this is the object's
parameter, not necessarily its state now.

**Screenshots** (looked at):
- `before/panel_sweep_old_js.png`: after a run, the old estimate stays under a disabled «Запустить»; «Сейчас: 4 Н/м».
- `after/panel_sweep.png`: «один замер в конце»; «Сначала «Оценить»» after the run; the header with the sampling and
  the base moment.
- `after/b02_instruments_panel_end.png`, `after/panel_page.png`.

### F9 — sweeps outside the worker accounting — **fixed (GPU part not measured)** [useful]

**Fix.** `server/lfviz/sweep.py`: `sweep_mem`, `memory_need`, `container_free`, `_spawn`, `_lower_priority`.
- **Memory budget.** A sweep process has its own hard limit (`RLIMIT_DATA`): `LFVIZ_SWEEP_MEM_GB`, by default half a
  worker's budget, at least 512 MB.
- **Refused before the start** (409, in Russian) when what it will hold — 2.2 × the state's bytes + 300 MB — does not
  fit that budget, or the memory the container has free now. Nothing is left behind.
- **OOM priority.** The process writes 1000 to `/proc/self/oom_score_adj`, so the kernel ends a sweep before a live
  world (0).
- **Device.** It runs on the CPU unless `LFVIZ_SWEEP_GPU=1`.
- **Not done:** counting a sweep as a worker for `max_workers`. The free-memory check covers its purpose.

**Verification.**
- `test_lb1_server_side`, read from `/proc` of the running sweep:
  - `oom_score_adj` 1000;
  - `Max data size` 512 MB, with a worker's 1 GB;
  - with `LFVIZ_SWEEP_MEM_GB=0.1`: 409 «свипу отведено 102 МБ», no base file left.
- `after/rc_c03b_budget_and_deleted_run.out`: the process list shows the sweep at `oom_adj 1000` and the workers at 0.
- **Not checked:**
  - the kernel's OOM kill itself (the host's swap is shared), as in the review;
  - the CPU default on a GPU host (this host's checks are CPU-only).

### F10 — a double «✕ отменить» deleted what the first one kept — **fixed** [useful]

**Fix.** `server/lfviz/sweep.py` (`cancel`, `remove`, the routes) and `player/js/instruments.js`.
- New route `POST /api/runs/{id}/sweeps/{n}/cancel`. It is idempotent: a sweep not running answers 200
  `{already: true, state}`.
- `DELETE /api/runs/{id}/sweeps/{n}` removes only a sweep that is not running; a running one gives 409 «сначала
  «✕ отменить»».
- The button is disabled at the first click.

**Verification.**
- `test_sweeps_through_the_server`: DELETE of a running sweep → 409; cancel → 200; a second cancel → `already`, the
  state still `cancelled`; then DELETE → removed.
- `after/rc_c11b_cancel_twice.out`: two cancels 0.3 s apart give 200 and 200 «уже остановлен», with 2 results kept.
- `after/c11_cancel_twice.out` (the reviewer's double DELETE): 409, 409, and the sweep goes on. Before: «cancelled»,
  then «removed», then 404.
- Browser: «F10 one click cancels, the button is off at once, the sweep is kept».

### F11 — CSV formatted in the event loop — **partly fixed; the rest → STATUS** [useful]

**Fix.** `server/lfviz/instruments.py` (`csv_batch`, `parse_query`, `series`):
- each batch is read and formatted in a thread;
- an id named twice counts once;
- a CSV is bounded by cells too: `CSV_MAX_CELLS` = 2·10⁷. Beyond that it takes every stride-th frame, and the time
  column's header says so.

**Measured effect.** `after/rc_c05c_csv_ab.out`: the server in a child process, `/api/health` asked every 20 ms from
another process, the CSV of 82 distinct quantities (2.1 MB), five downloads each way, twice.

| way | p95 stall of the other requests | max |
|---|---|---|
| the old way (formatted in the loop) | 0.17–0.19 s | 0.18–0.30 s |
| now (in a thread) | 0.06–0.11 s | 0.13–0.18 s |

- **Not zero.** The thread shares the interpreter lock with the loop.
- **Tried and dropped:** giving the lock away every 64 rows (`time.sleep(0)`) changed nothing measurable
  (`after/rc_c05c_csv_ab_yield.out`).
- **Not used:** the in-process A/B we tried first was discarded. A poller inside the blocked loop cannot see the block.
- **The full fix** — formatting in a separate process — goes to STATUS.

**Verification.**
- `tests/test_instruments.py::test_csv_is_formatted_off_the_event_loop`:
  - `csv_batch` never runs in the main thread;
  - `ids=E,E,o1.x,E` gives two columns, and the JSON gives `["E"]`;
  - a 3-column CSV with a 30-cell cap has at most 10 rows, «предел 10 строк», and a stride.
- `after/c05_series_load.out`: the review's 100 copies of one id are now one column (155 KB).

### F12 — malformed values gave 500 — **fixed** [useful]

**Fix.** `server/lfviz/sweep.py` (`_ident`, `validate`, `n_of`, the routes) and `instruments.py` (`WorldInfo.current`).
- The ids of `target`, `obj`, `param`, `measure` and `stat` must be strings: 400 in Russian otherwise.
- A sweep number must be ASCII digits: «²» and «١» are 404.
- A body that is not JSON or not UTF-8 is 400.
- **The remark about removed measures.** A measurable declared once whose object was removed since is refused, «мир
  сейчас не измеряет: её объекта больше нет в сцене». The list is the playground's latest scene message. «Что измерять»
  offers only what the world measures now.

**Verification.**
- `test_malformed_requests_are_400_not_500`: lists as ids, a list as the stat, and a removed object's measure.
- `test_lb1_server_side`: «²» and «١» are 404 on GET, DELETE and cancel.
- `after/rc_c12b_ids.out` (the reviewer's c12 on our server, plus the cancel route and a list as the target id): no
  500. The list id gives 400 ««target.id» — идентификатор (строка)».

### F16 (instruments part) — the tests did not cover the findings — **fixed** [useful]

**New tests**, each with a negative control:

| file | test | finding |
|---|---|---|
| `tests/test_sweeps.py` | `test_an_object_parameter_equal_to_the_stored_one_is_applied_again` | F1 |
| | `test_the_budget_holds_inside_one_advance` | F2 |
| | `test_lb1_server_side` | F2 (the server's kill), F3, F6, F9, F12 |
| | `test_the_estimate_counts_computation_only` | F4 |
| | `test_a_contract_breaking_measure_is_named` | LB1-p02-ux Q3 |
| | `test_nothing_measured_is_not_done` | LB1-p02-ux X7 |
| | `test_object_parameters_of_a_real_playground_are_validated_from_its_header` | LB1-p02-ux X1 |
| | `test_malformed_requests_are_400_not_500` | F12 |
| `tests/test_instruments.py` | `test_csv_is_formatted_off_the_event_loop` | F11 |
| `tests/browser/instruments_checks.mjs` | part 2: 16 checks | F1, F7, F8, F10, X7, X9 |

**Changed tests:** `test_sweeps_through_the_server` covers F7 and F10.

**Fixture changes** in `tests/instruments_worlds/p97_osc`:
- a live law `cost_ms` (busy CPU per world second; the computed state does not depend on it);
- a type `ball` with handles and `at`;
- `P97_MEASURE=tuple`;
- `alloc_mb`'s label naming its unit;
- a live law `damp`, hidden by `show_if` (X9).

**Final run.**
- `tests/test_sweeps.py`, `tests/test_instruments.py` and `tests/test_server.py`: 48 passed.
- `instruments_checks.mjs`: 24 of 24.
- `keyframes.mjs` for p01–p04 on the private server: «all equal» (`after/keyframes_p01-p04.out`).

## Changes for the integrator

These are the texts for files this agent may not edit (RULES, STATUS, the owner guide). They replace the instruments
agent's proposals in `lb1/instr/REPORT_saved_by_main.md`; its STATUS item (d) is withdrawn [error in earlier]. They also
cover the p02-ux findings X1, X7, X9 and Q3; `../2026-11-11_internal_LB1-p02-ux/RESPONSE_instruments.md` points here.

### 1. `visualizations/RULES.md` §3, the REST table: the row of `POST /api/runs/{id}/command` (replace)

| method | path | meaning |
|---|---|---|
| POST | `/api/runs/{id}/command` | `{cmd, args}` (same as over WebSocket); a suspended run is resumed first by a command that computes or changes the world (`play`, `step`, `next_event`, `set`, `action`, `view`, `scene`, `new_world`); the server's own worker commands (`checkpoint_now`, `stop`) are refused, 403, here and over the WebSocket (review LB1-framework F6); a body that is not `{cmd, args}` is 400 |

### 2. `visualizations/RULES.md` §3, the REST table: new rows (after `/api/runs/{id}/stream`)

| method | path | meaning |
|---|---|---|
| GET | `/api/runs/{id}/series?ids=a,b[&from=t0][&to=t1][&world=n][&format=csv][&max_points=k]` | the recorded values of a world's measurables (`lfviz.instruments`), the latest world or world n, the frames with t0 ≤ t ≤ t1; an id named twice counts once. JSON `{run, world, worlds, t_unit, ids, measurables (with title), t, values, n_frames, n, stride, cap, notes}`: at most `max_points` rows (default 5000, ≤ 50 000), every stride-th frame and the last. CSV: streamed, each batch read and formatted in a thread; one header line `t, <unit>` then `<label>, <unit> [<id>]`; an undefined value is an empty cell; every frame up to 2·10⁶ rows and 2·10⁷ cells, beyond them a stride named in the time column's header |
| POST | `/api/runs/{id}/sweep` | a parameter sweep from the current moment (`lfviz.sweep`, below): `{target {kind: law, id} \| {kind: object, obj, param}, values (≤ 50), duration, measure, stat final \| mean_last \| max \| min, window?, n_samples? (200, ≤ 2000), estimate?}` → `{n, state, estimate, base, labels}`; `estimate: true` only estimates; an object's parameter is checked against the palette in the world's header (review LB1-p02-ux X1), the measure against what the world measures now; 400 `{error, hint, estimate?}` when refused or above the budget; 409 when the run already has a sweep, two run on the server, the world gave no state, or the sweep's memory does not fit |
| GET | `/api/runs/{id}/sweeps`, `/api/runs/{id}/sweeps/{n}[?format=csv]` | the run's sweeps; one sweep's state and results; its table as CSV, three «#» lines first (the sweep, the base moment and its source, the duration, the readings and their spacing, the sampler; then the same as `key=value`) |
| POST | `/api/runs/{id}/sweeps/{n}/cancel` | stop a running sweep, what it computed kept (state `cancelled`); a sweep not running answers 200 `{already: true, state}`; also for a run deleted meanwhile (review F10, F3) |
| DELETE | `/api/runs/{id}/sweeps/{n}` | remove a finished sweep with its results; 409 while it runs (review F10) |

### 3. `visualizations/RULES.md` §3, the message table (add to the rows)

- `frame`: may carry `meas {id: number | null}` (the declared display units) and `meas_note {id: text}` (why a value is
  undefined).
- Any accumulative message (a playground's `scene` always; a demonstration's header or another message) may carry
  `measurables [{id, label, unit, of, group}]`. A playground's latest scene message is the list it measures now.

### 4. `visualizations/RULES.md` §6: new paragraph after «The player's panels» — «Instruments (plan P16.3)»

* **Instruments (plan P16.3; owner, 2026-11-04 and 2026-11-11; `lfviz.instruments`, `lfviz.sweep`,
  `player/js/instruments.js`).**
  - **The panel «Приборы»** lists a world's measurables by group, plots the values the run recorded at its frames'
    world times, and downloads them as CSV. Nothing it shows is computed by the player.
  - **Nothing the owner is using is rebuilt under him** (review LB1-framework F8): the list, the folded groups (kept per
    run in the browser), the plots, the sweep form (once per world, what was typed kept), and a sweep's result (the
    table grows by rows, the plot is redrawn on the same canvas).
  - **The base state.** A sweep starts from the world as it is now: the server's `checkpoint_now`, sent only by the
    server. A suspended run starts from its latest usable checkpoint, and the result says so. A code or runtime change
    since the world started is refused. The file is linked into `runs/<id>/sweeps/`.
  - **The process.** `python -m lfviz.sweep`:
    - its own memory budget as its hard limit: `LFVIZ_SWEEP_MEM_GB`, by default half a worker's, at least 512 MB;
    - refused before the start when 2.2 × the state's bytes + 300 MB does not fit that budget or the container's free
      memory;
    - `oom_score_adj` 1000, so the kernel ends a sweep before a live world;
    - `nice` 10;
    - the CPU unless `LFVIZ_SWEEP_GPU=1`; otherwise the run's device settings.
  - **Each value.** The process restores a fresh world and applies the change as the live world would:
    - a law by `set`;
    - an object's handle parameter by the scene's `edit`;
    - any other parameter by the scene's `set`.

    A value equal to the stored one is applied too. For a handle that is `edit`; for any other parameter, the section's
    `on_set` gets an always-unequal copy of the stored value in `old`. Only a flag equal to its stored value cannot be
    applied again, and its row says so. Every row is therefore the same experiment (review F1). A refusal is that
    value's result.
  - **The readings.** The process reads the measure at `n_samples` equal steps — over the window for `mean_last`, over
    the duration for `max` / `min`, the end only for `final` — and the result names the readings and their spacing
    (F7). It reads through the world's `measure()` when there is one, which must return a dict {id: number}: anything
    else is reported as the world breaking the instruments' contract, and the sweep stops (review LB1-p02-ux Q3).
    Otherwise it reads `frame()`'s `meas`.
  - **The live world is untouched.** The same state gives the same numbers, and the advance follows the world's own
    steps (a sweep at the current value equals the live world bit for bit).
  - **Nothing measured** is state `failed`, «не посчитан».
  - **The cost.** It is estimated from the record before the start:
    - only frames computed while the world played, with no command since the previous frame, count — an upper bound,
      the frame's own cost counted as advance;
    - a world only stepped has no estimate.

    A sweep above `LFVIZ_SWEEP_BUDGET_S` (600 s) is refused. The process holds the budget inside every advance: it
    advances in pieces of at most 0.25 s of wall time and stops beyond 1.5 × the budget, or as soon as, after 3 s of
    advancing, its measured cost projects the sweep beyond that. The server ends a process still running 30 s later
    (F2). Computed values are always kept.
  - **Limits.** One sweep per run, two on the server. A run deleted or removed during its sweep ends that process
    within about a second: the server's watch, and the process's own check of its folder (F3).
  - **Files.** Results in `sweeps/<n>.json`, written atomically at most once a second and after each value.

### 5. `engine/STATUS.md`: the item «The instruments (P16.3)» (new; open)

**The instruments (P16.3) — open.** Concerns `lfviz.instruments`, `lfviz.sweep`, `player/js/instruments.js` (reviews
LB1-framework F4, F9, F11; LB1-p02-ux X6).

(a) **The cost estimate is an upper bound.**
- Every frame of a playing world advances, so a frame's own cost (`frame()`) is counted as advance.
- Measured on p97 (10 oscillators, frame-dominated): 13 times too high. For an advance-dominated world: within 5 %.
- A world only stepped has no estimate; its sweep measures itself.
- To close: the runner records the advance's own time in each frame (`sim.py`, framework; the key excluded from the
  byte-for-byte checkpoint comparison).

(b) **A large CSV or series still slows the server's other requests.**
- Each batch is read and formatted in a thread, but the thread shares the interpreter lock with the event loop.
- Measured (82 columns, 2.1 MB): p95 0.06–0.11 s against 0.17–0.19 s formatted in the loop.
- To close: read and format in a separate process.

(c) **A sweep advances to its own sampling moments.** A world whose numbers depend on how time is split into steps gives
the sweep's own deterministic numbers, not what a live run would give. The sections' advances step on their own grid,
and p03 and p04 equal the live world bit for bit.

(d) **`runs/<id>/sweeps/` is not counted** in the run's size and quota: 0.12 MB measured for 40 values, at most about
0.5 MB per sweep (50 values × 200 trace points); the base link is removed when the sweep ends. To close: count it in
`runs.py` (framework).

(e) **The sweeps' CPU default on a GPU host is untested.** Sweeps run on the CPU unless `LFVIZ_SWEEP_GPU=1`; the checks
of this host were CPU-only, as was the kernel's OOM kill of a sweep (`oom_score_adj` 1000). To close: a GPU-host check
of both.

(f) **The panel keeps at most 20 000 points per world in the browser**; the CSV has every frame.

(g) **A flag (`bool`) equal to its stored value is not applied again by a sweep** (said in its row). A framework-level
«apply again» for `set` would remove it.

[error in earlier] The instruments agent's proposed item said «a run deleted during a sweep ends that process within
~1 s». That was not so before this processing (review LB1-framework R12/F3); it is now, and it is not an open item.

### 6. The owner guide (`visualizations/README.md`): section «Приборы и свип параметра» (replace the proposed text)

> **Приборы и свип параметра.** Если мир сообщает измеряемые величины, справа появляется панель «Приборы»: величины по
> группам и значение каждой на момент бегунка. Отметьте величину — появится её график по записи (у каждой свой): до
> бегунка ярко, после — бледно (будущее записи), черта — бегунок; наведите указатель, чтобы прочитать значение.
> Свёрнутые группы и выбор величин запоминаются для этого запуска. «⤓ CSV» — отмеченные величины из записи, все кадры,
> полная точность («только до бегунка» обрезает); в первой строке — единица времени и подписи с единицами.
>
> «Свип параметра»: тот же опыт от текущего момента мира повторяется для каждого значения закона (из «Законы мира —
> меняются сразу») или параметра объекта, и для каждого измеряется величина — в конце, среднее за последние N, максимум
> или минимум. Под «Что менять» написано, что задано сейчас; для положения объекта — ещё и где он сейчас. Каждое
> значение применяется заново, и равное заданному тоже: положение и скорость — как перетаскивание и бросок в момент
> свипа. Значения — через «;» или пробел (десятичная точка или запятая), или рядом «от … до …». Время счёта — в единицах
> масштаба мира (например, фс), по умолчанию — пять секунд мира при выбранной скорости; рядом с «Замеров» видно, через
> сколько времени мира берутся замеры. Сначала «Оценить» (сколько займёт счёта; предел 10 мин), потом «▶ Запустить
> свип»; после запуска оценку нужно сделать заново.
>
> Свип считается в отдельном процессе и идущий мир не меняет: у свипа своя, меньшая доля памяти, и если памяти не хватит,
> система первым остановит свип, а не мир. Свип сам остановится, если окажется дороже предела. «✕ отменить» останавливает
> его, посчитанное остаётся; «удалить» убирает законченный свип с результатами. Результат — таблица, график и «⤓ CSV
> таблицы» (в первых строках CSV — с какого момента, сколько и как часто мерили); отказ мира — в таблице с причиной, а
> если не измерено ни одно значение, свип помечен «не посчитан». Тот же свип от того же состояния даёт те же числа; у
> приостановленного запуска — от последнего сохранённого состояния (сказано над результатом).

### 7. Other notes for the integrator

- **API.md §4.** The cancel route moved from `DELETE` to `POST /sweeps/{n}/cancel`, and `DELETE` only removes (F10). A
  client of the old form gets 409 on a running sweep and loses nothing. The player is the only client and is updated.
- **PF's test.** `tests/test_manipulation.py` (PF's) must expect 403 for a client's `checkpoint_now` (F6); relayed
  2026-11-11.
- **New environment variables:** `LFVIZ_SWEEP_MEM_GB` and `LFVIZ_SWEEP_GPU` (`LFVIZ_SWEEP_BUDGET_S` existed). Defaults
  need nothing in `docker-compose.yml`.
