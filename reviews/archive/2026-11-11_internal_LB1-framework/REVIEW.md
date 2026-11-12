# Review LB1: the framework (direct manipulation, carry-over, instruments and sweeps)

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the code under review) |
| Date | 2026-11-11 |
| Scope | Batch LB1 of the laboratory plan (`lfphys/PLAN.md` § «The laboratory (P16)»), framework part. P16.2: `server/lfviz/playground.py` (handles, the `edit` op, measurables in `scene`), `sim.py` (`checkpoint_now`), `player/js/playground.js`, `scene3d.js`, `slices.js`, `player.js`, `player/run.html`. P16.1: carry-over (`new_world {carry}`). P16.3: `server/lfviz/instruments.py`, `sweep.py`, the routes in `app.py`, `player/js/instruments.js`. Tests: `tests/test_manipulation.py`, `test_carryover.py`, `test_instruments.py`, `test_sweeps.py`, the fixtures `p99_toy` and `p97_osc`, `tests/browser/manipulation.mjs`, `instruments_checks.mjs`. |
| Not in scope | The engine physics of the sections (review LB1-physics). `p02_quantum` is still being edited by another agent: it was not exercised here. |
| Environment | `light-funnel-viz` image, CPU only (`LFPHYS_NO_GPU=1`). Private server `lf-lbrf-srv` on port 8601: `--memory=6g`, 3 workers, `LFVIZ_EXTRA` holding both fixture folders (colon-separated, `os.pathsep`, `registry.roots`). A second private server `lf-lbrf-srv2` (port 8602) is identical except `LFVIZ_SWEEP_BUDGET_S=20`, so that the self-stop (1.5 × budget = 30 s) can be watched. Client scripts run in the same image with `--network host`. Browser checks run in Playwright 1.58.2 Chromium (swiftshader). The commands are in `lbrf_client.py` and in each script's header. |

The scripts and their outputs are in this folder: `c01`–`c13` (Python, against the server) and `b01`, `b02` (Chromium). Each
`.py`/`.mjs` has a `.out`, and most have a `.json`. Screenshots: `b01_manipulation_end.png`, `b02_instruments_panel_end.png`.

## Summary

There are 16 findings: **3 errors**, **8 should-fix**, **5 nits**.

The core machinery checks out:
- The law sweeps match the closed form.
- At the current value, a sweep's restored world equals the live world bit for bit (p03, p04).
- A carried world rebuilt by replay equals the original bit for bit, edits included.
- A throw's units scale as 1/rate.
- A refused drag leaves the world untouched.

The errors:
1. **F1.** An object-parameter sweep silently does not apply the value equal to the stored parameter. For a position or a velocity, that row reports the unchanged world.
2. **F2.** The sweep budget is not enforced inside one advance. A sweep started on a world that has not computed yet, or one whose cost is underestimated, runs without bound. Example: the panel's defaults on p03 ask for 1 s of molecular dynamics.
3. **F5.** «Перенести сцену» promises the objects' state, but the state is not carried in two cases:
   - p03 regenerates every atom from its parameters;
   - p04 restarts its flow from rest.

   In both, the world time continues and the notice says «все объекты».

The should-fix items cluster around four areas:
- resource safety on the shared host (F3, F6, F9, F11);
- the cost estimate (F4);
- what the sweep states (F7);
- the «Приборы» panel, which jumps and loses focus — the class of behaviour the owner complained about (F8).

## Results with their status

| # | check | result | status |
|---|---|---|---|
| R1 | `c01` (a): sweep of the law k against x(t0+T) = x0 cos ωT + v0/ω sin ωT (p97, base taken live by `checkpoint_now`) | \|err\| ≤ 8.9e-16 for k = 1, 4, 9 | [useful] |
| R2 | `c10`: one-value sweep at the law's current value vs. the live world advanced by `step {dt: T}` (p03 MD `e`, p04 LBM `mass_res`) | equal bit for bit. The final reading is the same for 1 and 201 readings | [useful] |
| R3 | `c02` (a), (c): `mean_last` over the whole duration and a 1e-6 window; undefined readings (`x_first` in an empty scene); window > duration | trapezoid rel. error 4e-6 to 9e-6 (n = 200). Undefined → None with the note. Refused 400 | [useful] |
| R4 | `c06`: p99 3-D → 2-D carry (2 objects refused and named), edits and a throw in world 2, suspension, checkpoint files deleted, resume by replay | the first frame after the resume equals the last before it (t, `at`, `meas`) bit for bit | [useful] |
| R5 | `b01` (1): the same Shift-drag at rate 0.5 and at rate 4 (scale 1) | \|v\| ratio 6.4 (expected 8; within the headless timing jitter). Each \|v\| is 0.75–0.87 of Δx_world/(Δt_wall·rate). The readout carries «м/с» and «×1» | [useful] |
| R6 | `b01` (2)–(4): refused drag outside ±5 m; selection while playing; Delete in the read-only history | Russian text + toast + snap-back, object on its unchanged line to 1e-16. The ring follows the object. Delete sends nothing, says «прошлое» | [useful] |
| R7 | `c12`: ids in series/sweep routes (`..%2F`, Unicode digits, non-numeric world) | no traversal: the run id is a dict key, the sweep number digits only. One 500 (F12) | [useful] |
| R8 | `c01` (b), (c), `b02` #5 | F1 | [weakens] |
| R9 | `c03`, `c13` | F2, F3 | [weakens] |
| R10 | `c07`, `c07b`, `c07c` | F5 | [weakens] |
| R11 | `c08` | the estimate is 57× to 2600× too high for a cheap world (F4) | [weakens] |
| R12 | the instruments agent's proposed STATUS item (d): «a run deleted during a sweep ends that process within ~1 s» | not so while the process is inside an advance (`c03`: alive after 68 s, uncancellable, holding a slot) | [error in earlier] (in the proposal; not yet in STATUS.md) |

## Findings

### F1 — error — an object-parameter sweep does not apply the value equal to the stored parameter

**Location.**
- `server/lfviz/sweep.py:730`: `run_value` applies an object target as `scene {op: "set"}`.
- `server/lfviz/playground.py:395-399`: `set` computes `changed` against the *stored* values and returns `""` when nothing differs, so `on_set` is never called.
- `player/js/instruments.js:360`: «Сейчас» shows `o.values[p.id]`.

**What happens.** The stored value of a moving object's position or velocity is where it was set, not where the object is now. The framework knows this, which is why the `edit` op applies equal values (`playground.py:454-458`; `test_an_edit_applies_a_value_equal_to_the_stored_one`). The sweep does not use that path.

So in a sweep of x over {0.5, 1.0, 1.5}, where 1.0 is the stored x:
- 0.5 and 1.5 set the position;
- 1.0 leaves the oscillator where it was.

The table then mixes two different experiments with no mark. The panel makes the trap likely, because «Сейчас: 1 м» suggests 1.0 is the current position (it was at −0.75 m).

**Evidence.** `c01_sweep_closed_form.out`, p97 stepped to t0 = 0.5. For each value: the measurement, the closed form of «set to the value», and the closed form of «unchanged»:

```
(b) x =  0.5: measured -0.744243783322  if set -0.744243783322  if unchanged -0.737393715541  -> set
(b) x =    1: measured -0.737393715541  if set -0.659260211872  if unchanged -0.737393715541  -> NO CHANGE
(b) x =  1.5: measured -0.574276640422  if set -0.574276640422  if unchanged -0.737393715541  -> set
(c) v =    0: measured -0.737393715541  if set 0.0918336392308  if unchanged -0.737393715541  -> NO CHANGE
```

`b02_instruments_panel.out` #5: `"shown":"Сейчас: 1 м","position_now":-0.7496`.

**Fix.**
- Apply an object target through a path that always applies. For a handle parameter, use `op: "edit"`. For any other parameter, use `set` with a flag such as `force: true` that marks the sent keys in `old` as `None`, as `_edit` does.
- Show the current state next to «Сейчас» for handle parameters (from the latest frame's `at`, `now` or `meas`), and say that the stored value is the set-point.
- Regression test: p97, sweep x and v over {a, stored, b} against the «set» closed form.

### F2 — error — the sweep budget is not enforced inside one advance; a sweep can run without bound

**Location.**
- `server/lfviz/sweep.py:747-768`: the budget check sits after `runner._advance(tgt)` and the reading.
- `sweep.py:859`: the check after each value.
- `sweep.py:255-260`: an unknown cost starts the sweep.
- `sim.py:257-269`: `_advance` with `budget=None` loops until the target.
- `instruments.js:415`: the default duration is «1».

There is no wall-clock limit on the server side: `SweepManager._watch` only waits.

**What happens.** The documented guarantee is: «свип начнётся и остановится сам, если первое значение покажет, что он дороже предела», and «stops by itself at 1.5 × the budget». It holds only between readings. With `stat: final` there is one reading, so the whole duration is a single `Runner._advance`. Two cases reach it:
1. **Unknown cost.** The world has not computed yet, so no frame pair has dt > 0. The sweep starts and is never stopped.
2. **Underestimated cost.** The cost of a swept value differs from the record's. Sweeping p04's `nx`, or p03's `dt_fs` downwards, changes the cost per world second by orders of magnitude.

The panel's own defaults reach case 1 on p03:
- p03's world time is in seconds, and its header has no `units.t`.
- So «Сколько считать, с = 1» asks for 1 s of molecular dynamics: 10¹⁴ steps of 10 fs.

Such a sweep holds one of the server's two sweep places and a CPU until someone cancels it.

**Evidence.**
- `c03_sweep_budget_and_deleted_run.out` (budget 20 s): `after 45 s (budget 20 s, self-stop at 30 s): state=running … frac 0.0`. The process was still alive and computing at 68 s of CPU.
- `c13_default_sweep_p03.out` (p03 maxwell, defaults, budget 20 s): `estimate … False | … свип начнётся и остановится сам …` → `after 60 s: state running, active True, … frac 0.0`.

**Fix.**
- **Server.** Kill the process at OVERRUN × budget of wall time from `_watch` (an `asyncio.wait_for` around `proc.wait()`), keep the computed values, and mark the state `over_budget`.
- **Sweep process.** Advance in chunks (for example `n_samples` sub-targets even for `final`, or a wall-time `budget` passed to `Runner._advance`) and check the clock between them.
- **Unknown cost.** Refuse a sweep whose cost is unknown until a probe value has been measured: run the first value for a short stretch and extrapolate.
- **Panel.** Default the duration to the world's scale, such as the record's last world-time span or its speed × 10 s.

### F3 — should-fix — a deleted run's sweep keeps running, cannot be cancelled and holds a server-wide place

**Location.**
- `server/lfviz/runs.py:994-1005`: `delete` and `_remove` stop the worker and `rmtree` the folder, but know nothing of `SweepManager`.
- `server/lfviz/sweep.py:595-597, 639-645`: a cancel first resolves the run, so it answers 404 for a deleted run.

The retention clean-up (`_remove`) has the same gap.

**Evidence.** `c03` (b), after deleting the run:
- `cancel the deleted run's sweep: 404 {'error': 'нет такого запуска'}`;
- then a second run's sweep was accepted, and a third was refused: `409 … на сервере уже идут 2 свипа`.

So the server counted the orphan as one of the two places. The orphan's process (pid 15) was alive at 68 s. It ends only when its first value is done and its next write fails on the deleted folder.

**Fix.**
- In `RunManager.delete` and `_remove`, cancel the run's sweeps: kill the process and await the task, through a hook the sweep module registers.
- Let `DELETE /api/runs/{id}/sweeps/{n}` cancel an active entry by key even when the run is gone.
- Have the sweep process exit when its spec folder disappears, checked between chunks once F2 is fixed.

### F4 — should-fix — the cost estimate counts the runner's idle wait as computation

**Location.**
- `server/lfviz/sim.py:630, 653`: a frame's `cpu_ms` is the loop iteration's time from its start. When paused, that start includes `q.get(timeout=period)`, the wait for the next command of up to 50 ms.
- `server/lfviz/sweep.py:228-236`: `measured_cost` sums `cpu_ms − min(cpu_ms)` over the frames' dt.

**What happens.** A world advanced by `step` or edited while paused gets frames with `cpu_ms` ≈ the wait. One such frame after a `play` (about 50 ms) dominates a cheap world's sum.

**Evidence.** `c08_sweep_estimate.out` (p97, 10 oscillators; the sweep's own measurement is 0.31 ms per world second):

| record | estimated ms per world second | overestimate |
|---|---|---|
| (A) stepped | 830 | ~2600× |
| (B) played 3 s | 17.8 | ~57× |

`b02`'s first attempt: a 40-value sweep that takes about 4 s was refused as «≈ 2 ч 36 мин счёта — больше предела 10 мин».

In the other direction the estimate cannot see a state-dependent cost, which leads to F2. The test checks only `0 < total_s < budget` (`test_sweeps.py:212`), so neither direction is caught.

**Fix.**
- Record a frame's pure compute time, for example `adv_ms` (the `_advance` time and the frame's own time, excluding the queue wait), and estimate from that, dropping frames that follow a command.
- Better: measure the cost in the sweep process itself on a short probe advance of the first value (see F2), and use the record only as a hint.
- Add a test that bounds the estimate against the measured `advance_s`, say within ×3.

### F5 — error — carry-over promises the state, but objects without `object_state` and the world's own state restart silently

**Location.**
- `server/lfviz/playground.py:310-336`: `_carry_scene` and its notice count only refused objects.
- `player/js/player.js:389`: the checkbox's title says «Объекты текущей сцены с их состоянием (положения, скорости) переходят в новый мир».
- The proposed owner-guide text: «объекты с положениями и скоростями, время продолжается».

**What happens.** The export carries `values`, plus `state` only where the section's `object_state` returns one. Three kinds of state are dropped without a word:
- **p03.** It returns `None` for every object (`p03_molecules/viz.py:1449-1451`), so every gas, crystal and molecule group is regenerated from its parameters, with new random positions and velocities.
- **Fields.** A world's state that is not an object's — p04's flow field — starts again from rest.
- **Randomness.** The random stream restarts from the seed instead of continuing.

Meanwhile:
- the new world starts at the same world time;
- the notice says «Сцена перенесена в новый мир: все объекты (1)»;
- the dialog says the state goes with the objects.

`place` and `_import_values` may also adapt values (p03 drops z, sz and vz; a free spot may be chosen), and the notice does not say so either.

**Evidence.**
- `c07b_notice.out`, p03, 12 000 atoms, 3-D, boundary periodic → walls:
  - `carried object has a state: False`;
  - `T: 300.4579 → 300.2395` and `e: 3.68769 → 3.68834` at the same t = 1e-13 s;
  - notice `['Сцена перенесена в новый мир: все объекты (1)']`.
- `c07c_carry_p04.out`, p04, fluid dfg → water at t = 1.0 s: `q_net: 0.01784 → 0.0`, `mass_res: 7.7e-16 → 0.0`. The notice names only the refused inlet.
- `c07` (a) is a fair refusal: 150 dimers do not fit the 2-D box, and the notice says so.

**Fix.**
- The framework knows which exported objects have no `state`. The notice should list them: «состояние не перенесено — начато заново из параметров: «Аргон» (12 000 атомов)».
- Add a section hook `carry_notes()` (p02 already has its own `_carry_notes`) for world-level state that does not carry («течение начато заново из покоя», «случайная последовательность начата заново»).
- Have `_carry_scene` report value adaptations by diffing the carried values against the values added.
- Correct the checkbox title and the guide: the state is carried only where the section exports it.
- Optionally offer «время с нуля» when nothing dynamic is carried.

### F6 — should-fix — any viewer can force checkpoints and record segments through `checkpoint_now`

**Location.**
- `server/lfviz/app.py:168-176` (REST) and `app.py:298-300` (WebSocket) forward any command name.
- `server/lfviz/runs.py:429-447`: `command_resuming` filters nothing for a running run.
- `server/lfviz/sim.py:374-378`.

**What happens.** The command is meant for the server's sweeps, but any page or script on the LAN can send it. While a world plays, every call is dirty, so each call:
- pickles the whole world in the worker's loop, which stalls the frames for the pickling time (seconds for a large p02 or p04 state);
- writes a file;
- starts a new record segment, repeating the scene, `rekey` and every set-like message.

`args.tag` is any JSON and goes into the record.

**Evidence.** `c04_checkpoint_now_from_a_viewer.out`: 41 REST calls in 4 s gave 41 pickles written and 41 `record_segment`. The largest checkpoint message was 301 652 characters (a 300 000-character tag).

**Fix.**
- Refuse `checkpoint_now` (and `stop`, which is also forwarded) in `Run.command_resuming` and in the WebSocket path. Let only `SweepManager` send it, through `Run.command` directly.
- Validate `tag` as a short token.
- Optionally rate-limit forced checkpoints per run, at most one per N seconds; the sweep can reuse the last one.

### F7 — should-fix — a sweep result does not state its sampling; the table's CSV omits the base moment

**Location.**
- `server/lfviz/sweep.py:68` (`STAT_RU`) and `sweep.py:562-574` (`table_csv`).
- `player/js/instruments.js:549-551`: the result header shows the duration and the base t, not `n_samples`.

**What happens.**
- «максимум», «минимум» and «среднее» are taken over `n_samples + 1` readings at equal steps, but the result says only «максимум». With `n_samples = 1`, «максимум» is max(x(t0), x(t0+T)).
- A maximum between readings is missed by up to (ωΔt/2)²/2 relative, and an oscillation faster than the readings aliases.
- The CSV's header line has only the target, the measure with the stat, and «примечание». There is no base t, duration, window, n_samples or sampler (`measure()` or `frame()`).

**Evidence.** `c02_sweep_stats_edges.out` (b): the true maximum of x over 3 s is 1.0. With `n_samples` 1 and 4 the table says «максимум» = 0.754. With 200 it says 0.999995.

`b02` checks 9 and 10 fail:
- header: `…(максимум); 300 с мира от t = 2,95553`;
- CSV first line: `"Жёсткость пружины, Н/м","Полная энергия (максимум), Дж",примечание`.

**Fix.**
- Put the sampling into `stat_text` («максимум по 201 замеру через 1,5 с»).
- Put base t, duration, window, n_samples, sampler and source (now or latest) into the CSV as `#` comment lines or extra header cells.
- Warn when the step between readings exceeds a period the world can report. At least show Δt between readings next to «Замеров».

### F8 — should-fix — the «Приборы» panel loses focus, unfolds groups, jumps the column and forgets the sweep form

**Location.**
- `player/js/instruments.js:169-203`: `refreshLists` rebuilds the list with `fill`, groups `open: true`, on every tick.
- `instruments.js:193`: every checkbox change calls `refreshLists`.
- `instruments.js:137`: every unfold of «Свип параметра» calls `drawSweepForm()`, which rebuilds the form.
- `instruments.js:530-556`: `renderSweep` replaces the table and the canvas every 700 ms while a sweep runs.

**Evidence.** `b02_instruments_panel.out` (1280×800, p97 with ten oscillators):
- Ticking with Space moves the focus to `BODY`.
- The folded group «Мир» reopens.
- The right column jumps from scrollTop 1032 to 445.
- «1; 2; 3» typed in «Значения» is gone after folding and unfolding.
- During a sweep the table and plot nodes are new at every poll. The scroll is kept here, but a selection or hover in the table is lost.

**Fix.**
- Update rows in place, as `playground.js` does for its object list (review UX-ui U1): keep a `Map` id → row, add and remove rows, and keep each group's `open` state.
- Build the sweep form once per world and keep its inputs.
- In `renderSweep`, update the progress bar, append table rows and redraw the same canvas.
- Add a browser check of focus, fold state and scroll, as `b02` does.

### F9 — should-fix — sweeps sit outside the worker accounting: full budget each, same OOM priority as live worlds

**Location.**
- `server/lfviz/sweep.py:451-462` (`_spawn`: `env[limits.ENV] = self.mgr.worker_mem`).
- `sweep.py:792-800` (`main`: RLIMIT and nice, no OOM adjustment).
- `server/lfviz/limits.py:90-97` (the default budget, 60 % of the container, whatever the worker count).

**What happens.** In the shared configuration (a 6 GB container, 3 workers), each worker may hold 3.6 GB, which is already 10.8 GB of budgets. Two sweeps add 2 × 3.6 GB.

Each sweep also holds its checkpoint's bytes and a whole unpickled world: about 2× the live world's state. A world near its budget can therefore never be swept; it fails on MemoryError, which is reported correctly.

A sweep has `oom_score_adj` 0 like a live worker, so when the cgroup fills the kernel picks by size. A sweep's allocation can thus end a live world, against PLAN P16.3's «the live world unaffected». On a GPU host, sweeps also share GPU 0 with no budget, and the thermal guard's state is per process. The instruments agent's notes list this as (e).

**Evidence.** `c09_limits.out` (`lf-lbrf-srv2`): each worker and the sweep show `RLIMIT_DATA soft/hard 3865470566`, `oom_score_adj 0`, `oom_score 667`; the server shows 666. The cgroup OOM itself was not provoked: the host's swap is shared, and only about 700 MB of it was free.

**Fix.**
- Write `1000` to `/proc/self/oom_score_adj` in the sweep process (allowed without privileges), so that the kernel ends a sweep first.
- Give sweeps a smaller budget, for example the worker budget minus the checkpoint size, or a separate `--sweep-mem-gb`.
- Count a running sweep as a worker for `max_workers`, or refuse a sweep when free container memory is below its estimate (`checkpoint bytes × 2` plus the world's `estimate_bytes`).
- Default sweeps to the CPU on GPU hosts unless the run asks otherwise.

### F10 — should-fix — «✕ отменить» twice deletes what the first cancel kept

**Location.**
- `server/lfviz/sweep.py:528-547`: one `DELETE` both cancels a running sweep and removes a finished one with its results.
- `player/js/instruments.js:536-538`: the cancel button stays until the next poll.

**Evidence.** `c11_cancel_twice.out`: a 6-value sweep was cancelled after 2 values, with two DELETEs 0.3 s apart (a double click, or two tabs). The responses were `first: 200 {'cancelled': 1}`, `second: 200 {'removed': 1}`, and then `404 нет такого свипа`. The kept values were lost.

**Fix.**
- Separate the operations: `POST /sweeps/{n}/cancel` (idempotent: 200 «уже остановлен» when not active) and `DELETE` (remove only when not active and asked explicitly).
- Disable the button after the first click.

### F11 — should-fix — a series CSV is formatted in the server's event loop

**Location.**
- `server/lfviz/instruments.py:360-368`: `read_rows` runs in a thread, but the `csv.writer` loop over each 4000-row batch runs in the event loop.
- `instruments.py:274-279`: `MAX_IDS` counts copies, so `ids=E,E,…` (100 copies) is accepted.

**Evidence.** `c05_series_load.out`. A p97 record of 4793 frames was read while `/api/health` was asked every 20 ms:

| request | size | time | longest `/api/health` latency during it |
|---|---|---|---|
| CSV of 100 ids | 8.9 MB | 0.57 s | 0.361 s (baseline 0.0012 s) |
| JSON | 0.20 MB | — | 0.078 s |

The JSON stays small because duplicate ids collapse into one key. At the CSV cap of 2·10⁶ rows such a download is about 3.7 GB and blocks every viewer about 0.36 s per batch for minutes. With realistic 10–40 distinct quantities the stall is proportionally shorter, but it repeats on every batch.

**Fix.**
- Format each batch in the thread: make `read_rows` return the CSV text.
- De-duplicate `ids`.
- Optionally cap the cells per CSV, not only the rows.

### F12 — nit — malformed request values give 500 instead of 400

**Location.**
- `server/lfviz/sweep.py:136, 144, 171`: dict lookups with an unhashable `id`, `obj` or `measure` raise TypeError.
- `sweep.py:598-601, 639-645`: `'²'.isdigit()` is True, and `int('²')` raises ValueError, which `delete` does not catch.

**Evidence.** `c02` (d): `target id a list`, `obj id a list` and `measure a list` each give `HTTP 500`. `c12_ids.out`: `DELETE /sweeps/%C2%B2 -> 500`.

**Fix.**
- Check `isinstance(…, str)` before the lookups.
- Use `s.isascii() and s.isdigit()` in `n_of`.

A measure declared once and later removed (an object deleted) is still accepted: `w.decl` keeps it, and the sweep then reports «не определена ни в одном замере». The panel could list only the current measurables.

### F13 — nit — the edit's log line: no units, wrong gender; `asked` unvalidated; a «clamped» readout that does not clamp

**Location.**
- `server/lfviz/playground.py:466-480`.
- `player/js/playground.js:543-561`.

**What happens.**
- The «Изменения сцены» line reads ««Частица 1» перемещён в (x = 2, y = -1,5, z = 0,75)» and «брошен со скоростью (vx = …)». It has no units: for p01 these are а.е. and а.е./с, which the owner cannot guess. The participle also disagrees with the noun's gender (Частица → перемещена).
- `asked` from a REST edit is taken as is. A throw below `velocity_max` with `asked` above it is logged «ограничено до … (бросок дал …)» though nothing was clamped, and `asked = inf` is accepted.
- In `b01` the readout said «— ограничено до 12 м/с» two moves before the release, but the throw sent at the release was 8.6 m/s and unclamped, because the last 100 ms included the still pointer.

**Fix.**
- Take units from the schema (`p.unit`).
- Phrase the line as ««Частица 1»: перемещение в (…)».
- Log a clamp only when `_clamp_throw` clamped, or when `asked` is finite and the sent speed equals `velocity_max`.
- Recompute the readout's clamp text at the release, or drop it once the pointer stops.

### F14 — nit — the automatic throw scale is anchored to the ceiling `velocity_max`, not to the hand

**Location.** `player/js/playground.js:436-440`. It was decided by the integrator: «a flick gives half of `velocity_max`».

**What happens.** p01's `velocity_max` is 0.05 c expressed in а.е./с (`p01_gravity/viz.py:666`). A brisk flick (the view's width per second) therefore throws a body at about 0.025 c ≈ 7500 km/s, about 250× Earth's orbital speed, whatever the playback rate and the zoom. Almost every throw is an escape.

With scale 1 the throw is the hand's own world velocity at the playback rate, which matches what the owner sees move on the screen. The clamp already guards the ceiling.

**Suggestion.**
- Make «авто» = 1, and keep the clamp to `velocity_max` with its notice.
- Or anchor «авто» to a characteristic speed of the scene (the RMS speed of the objects in the frame) rather than to the ceiling.

### F15 — nit — carried objects are renumbered

**Location.** `server/lfviz/playground.py:355`: `_add` assigns `o{next_id}` from 1 in the new world.

**Evidence.** `c06_carry_replay.out`: «Частица 4» (o6 in world 1) became o4.

**Why it matters.** Anything that names an object by id is silently re-pointed at another object (or at nothing) after a carry:
- the instruments' selection, kept per run in localStorage by measurable id such as `o6.speed`;
- a sweep target;
- a measurable's `of`;
- a future cross-object reference.

**Fix.**
- Carry the ids: export them, and let `_add` accept an id when the scene is carried and the id is free; advance `next_id` past them.
- Or map old ids to new ones in the notice and in the instruments panel.

### F16 — nit — test gaps (the existing tests do test what they claim, with negative controls)

`test_manipulation`, `test_carryover`, `test_instruments` and `test_sweeps` check what their docstrings claim, and most have negative controls. Examples:
- the unchanged law must not fit the swept values;
- `set` with a stored value changes nothing;
- another base moment gives other numbers;
- a refused new world stays refused through a restore.

They do not cover the cases where the findings above live:
- a sweep of a handle parameter including its stored value (F1);
- the self-stop inside one advance (F2): the cancel test sets the budget to 100 000 s;
- a deleted run with an active sweep (F3);
- the estimate's accuracy (F4);
- `checkpoint_now` sent by a viewer (F6);
- a carry from a section whose objects export no state (F5): only `p99_toy` is used, and it exports everything;
- the panel's focus, folding and scroll (F8): `instruments_checks.mjs` checks values only.

Each fix above names its regression test.

## What was not checked

- `p02_quantum` was not exercised (it is being edited by another agent). Its `frame()` is heavy, and the instruments agent notes that a sweep pays for it per reading.
- GPU: everything here ran on the CPU. The CPU/GPU difference of a swept world, and the thermal guard per process, are not measured.
- The cgroup OOM itself was not provoked (F9), because the host's swap is shared.
- Key frames with the new markers (the playground's selection and ghost are «never layers, never in key frames») were not re-run. The framework agent reports `keyframes.mjs` equal.

## Clean-up

The private servers `lf-lbrf-srv` and `lf-lbrf-srv2` were stopped by name after the checks (verified with `docker ps`). Their runs folders are in the session's scratch directory. Nothing outside this folder was written.
