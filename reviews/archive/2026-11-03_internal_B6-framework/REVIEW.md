# Review B6 — the playground framework (P15.0), its users p01/p02, and the backend temperature guard

**Status: awaiting processing.**
Type: internal (Claude Opus subagent; did not write the code). Delivered 2026-11-03.
Base: git HEAD `1a9c32a` plus the uncommitted B6 changes in the working tree (files as of 20:51 local time; one file
changed while this review ran: `p01_gravity/web/view.js` at 20:21, re-read — the findings and the browser runs are on
the newer version).

Scope (as asked): `server/lfviz/playground.py`, `runs.py` (the buffered record), `sim.py`, `app.py`, `registry.py`,
`params.py`; `player/js/playground.js`, `catalog.js`, `player.js`, `ui.js`, `scene3d.js` (`setSpheres`), `index.html`,
`chrome.css`; `p01_gravity` and `p02_quantum` as users of the framework (hooks, messages, key frames, determinism,
sizes; not their physics); the toy `tests/playgrounds/p99_toy`; the tests; `lfphys/lfphys/core/backend.py` (THERMAL).

Environment: Docker image `light-funnel-viz` (CPU only, `LFPHYS_NO_GPU=1`, engine mounted read-only), Playwright image
`mcr.microsoft.com/playwright:v1.58.2-jammy`, a private server on port 8531 (container `lf-b6rf-srv`, its runs in
`runs_browser/`, stopped and removed after use). No GPU was touched (the thermal checks replace CuPy's availability
and the temperature reader in-process). Every script states its exact command in its header; each `*.out` is its
output. Bulky run records in `runs_browser/` were deleted after `s08`/`s12` measured them (77 MB); `meta.json` and
`worker.log` are kept.

Baseline (all pass): `tests/test_playground.py` 5/5 (`00_baseline_test_playground.out`); `test_restore.py` and
`test_checkpoint.py` for p01/p02 6/6, `lfphys/tests/test_backend.py -k hot` 1 passed, 1 skipped (GPU)
(`00_baseline_restore_checkpoint_backend.out`); `tests/browser/keyframes.mjs p01_gravity,p02_quantum`: all equal
(`b02_keyframes_playgrounds.out`; note F23: those records are 21 s long and never cross a segment).

## Summary

| # | severity | one line |
|---|---|---|
| F1 | error | A resume by replay is accepted for a record with a trimmed hole (recording on, then off): the world is rebuilt without the lost commands — silently another world |
| F2 | error | When the checkpoint does not load in the worker, it falls back to "replay from the start" even when the start left the window: silently another world |
| F3 | error | A world whose header left the window takes `t_end` over the kept entries of earlier worlds: the resumed world jumps to world 1's time (2.25 s → 87.7 s) |
| F4 | error | A segment is not drawable on its own: the Kerr hole's horizon/ergosphere/orbits, the grown box and the Newtonian-hole approximation flag are never re-emitted (RULES §2.6 flag lost after a trim) |
| F5 | error | p01: every checkpoint (60 s of play, a pause, a suspension) resets every viewer's trails (11 004 points → 36 in the browser) |
| F6 | error | A `frame()` exception makes the runner loop without pause: 8 139 errors in 2 s, 3.4 MB/s into the record; reachable from the inspector (p01 x = 1.7e308) |
| F7 | error | Thermal guard: a hot reading followed by an unreadable sensor makes every GPU-wanting `choose()` raise `TypeError` |
| F8 | should-fix | p01's `rekey` changes the world's state at wall-clock moments: a world restored by replay emits different messages afterwards |
| F9 | should-fix | The history (and the download) races with trimming: `FileNotFoundError` kills the viewer's pump (no `history_end`, no live tail); segment 0 emptied in place sends corrupt messages |
| F10 | should-fix | The window counts wall time including pauses and suspensions: after a 20-min pause, 1 min of play drops 9 of the 10 computed minutes |
| F11 | should-fix | The record panel shows the record's state as of the cursor and posts it back: changing the window's minutes in the past switched recording on |
| F12 | should-fix | `POST /record`: `on` omitted switches recording off, `"false"` switches it on, a list body or list value gives 500 |
| F13 | should-fix | The tab keeps every accumulative message of a session (p02 waves ≈ 22–33 MB/min, p01 every trail generation): the window bounds the server, not the browser |
| F14 | should-fix | p02: a world from a scene file saved at t > 0 integrates the whole span in its header's advance (4 889 steps, 18 s blocked on 128²) |
| F15 | should-fix | Finite values that overflow in the engine's units are accepted: p02 barrier V = 1e308 eV → NaN potential → the particle's norm NaN for good |
| F16 | should-fix | p02: changing only a particle's Bohm count replaces its wave by the starting packet (⟨x⟩ 1.48 → −20 nm) |
| F17 | should-fix | Scene files: a non-object scene/objects gives a raw `AttributeError`; `t` = "inf", "nan", −1e300 accepted |
| F18 | should-fix | The player's «Новый мир» panel sends the hidden initial scene along: switching p01's laws is refused («нет объектов «star»») |
| F19 | should-fix | A thermal switch to the CPU in the middle of a world is reported nowhere (only the header carries `backend`), contrary to RULES §5 |
| F20 | nit | A scene of 1–2 M characters is accepted by `POST /api/runs` but closes the player's socket (1009) when loaded there; meta.json keeps two copies of it |
| F21 | nit | Checkpoints every 60 s: p02 3-D 128³ writes 117 MB per electron per minute; the window's size bound excludes them; two segments, not one, exceed it |
| F22 | nit | Docs: RULES §3 omits `scene` and `/record`; docstrings; "60 s of computation"; claims contradicted by F1–F5, F10, F19 |
| F23 | nit | Test gaps: the toy has no `rekey`; the browser jobs never cross a segment; no test of protected holes, earlier worlds, races, hot → unreadable |
| F24 | nit | Small code points: `export` recorded as a world-changing command; `code_hash` with an outside `LFVIZ_EXTRA`; repeated protected ranges; a broken `pNN_` card under «Демонстрации» |

Totals: **7 errors, 12 should-fix, 5 nits.**

---

## The record as a moving window: resume after trimming

### F1 — error — a resume by replay across a trimmed hole is accepted

Location: `server/lfviz/runs.py:416-419` (`complete = True` whenever the latest world's header is among the entries),
`runs.py:785` (the refusal tests only `complete`), `runs.py:505-510, 563-571` (protected ranges).

When recording is switched on while the world's first segment is still kept, that segment (with the header) is
protected; when it is switched off and play goes on, the unprotected segments after it are trimmed. The header is then
in the record, so `_latest_world()` says `complete = True` although the commands of the trimmed segments are gone.
Without a usable checkpoint (code or library versions changed — the case the refusal message describes) the server
starts a replay of a script with a hole, and nothing says so.

Evidence: `s01_resume_trimmed.py` scenario A (`s01_resume_trimmed.out`): protected `[[0, 2]]`, the scene change
(`o1.vx = 5`) recorded in segment 4, segments kept `[0, 1, 2, 7, 8]`;
`_latest_world: complete = True  checkpoint = None  script commands = []`; `POST command play (resumes) -> 200`,
`resumed how: replay`; `after resume: t = 3.5564, o1 x = 2.5564; expected about 9.7699`.

Fix: `complete` must mean "every entry of this world since its header is kept": segment numbers are consecutive, so
require the kept segments from the header's segment to the last to be contiguous (or keep `dropped` in
`meta.buffer` and test membership). Refuse the replay otherwise, with the same message. Test: scenario A as a
regression test (toy, `P99_CKPT`).

### F2 — error — the worker falls back to a replay "from the start" that no longer exists

Location: `server/lfviz/worker.py:105-125` (any exception while loading the checkpoint → notice → line 133-147,
`runner.restore` from the world's start), `runs.py:804-808` (`init.restore` does not say whether the record is
complete).

The server only checks that the checkpoint file exists, has the right name, code hash and runtime. If it then fails to
load in the worker — a damaged file, or (a hypothesis, not reproduced in this CPU-only review)
`checkpoint._cupy_array` failing to put a GPU array back because GPU 0's memory is taken by a neighbour or CuPy is not
available at the resume — the worker rebuilds the world from its
parameters and replays the kept tail, which starts in the middle of the world. The run continues with a wrong state;
the only trace is a notice that says it was "recomputed from the start".

Evidence: `s01` scenario B: header not in the record, `complete = False`, the checkpoint replaced by 64 zero bytes
(name and code hash unchanged); notices: «Сохранённое состояние не загрузилось (UnpicklingError…); мир
пересчитывается от начала по записи», «Мир восстановлен: пересчитан от начала по записи (0 изменений установки)»;
`before suspension: o1 x = 8.4176; after resume: o1 x = 1.2042; expected about 8.4179`.

Fix: pass `complete` in `init["restore"]`; when the checkpoint does not load and the record is not complete, try the
other kept checkpoint file (`checkpoint.KEEP = 2`, the record's previous `checkpoint` message, with its own script
tail), else emit an error and end (the run stays suspended with `resume_error`, as for other failed rebuilds).

### F3 — error — `t_end` is taken over entries of earlier worlds

Location: `server/lfviz/runs.py:420-430` (`head = -1`: the loop runs over all entries of all worlds), then
`sim.Runner.restore_from` advances the world to `t_end` (`sim.py:469-470`).

If an earlier world's segments are protected and the latest world's header has left the window, the script, `t_end`
and the frame list include the earlier world's entries. With a checkpoint the script tail is right (it starts at the
latest world's checkpoint), but `t_end` is the maximum time of all kept entries.

Evidence: `s01` scenario C: world 1 recorded (to t ≈ 72.6 s), world 2 started later, its header trimmed;
`world 2 last frame t = 2.2540; _latest_world: world 2, t_end = 87.6636, checkpoint t = 2.2540`;
`first frame after the resume: t = 87.6637 (world 2 was at 2.2540)` — 85 s of world time computed silently.

Fix: when the header is not in the entries, take only the entries of segments whose `world` (in `meta.buffer.segs`)
is the latest world (a segment that started in an earlier world would contain the new header). Test: scenario C.

### F4 — error — a segment is not drawable on its own

Location: the contract `server/lfviz/playground.py:19-21, 101-102`, `runs.py:28-30`, RULES §6 ("each segment starts
with `record_segment`, the scene and what `rekey` emits"); `p01_gravity/viz.py:150-151` (`rekey` emits only trails),
`p01_gravity/viz.py:786-815` (Kerr: horizon, ergosphere and orbit lines only in `after_header`), `:400-404` (`box` only
when the extent grows), `:337-343` (`approx` only on a change).

After the window drops a world's first segment, a viewer (and the downloaded record, `app.py` `run_stream`) gets the
header and the segments from a marker on. p01 never re-emits what it sent once: the Kerr hole's surfaces and circular
orbits disappear from the 3-D scene; the scene box falls back to the header's (Jupiter outside it); and the
approximation "чёрная дыра — ньютоновская точечная масса … (не ОТО)" disappears from the top bar — RULES §2.6 requires
it to be shown while the world uses it. (p02's `rekey`/`emit_scene` re-emit shapes, actions, approximations, marks and
the wave: complete for p02 as far as I could see.)

Evidence: `s10_segment_self_contained.py` (`.out`): kerr_orbits — never reaches the joining viewer
`['event', 'lines:orbits', 'mesh:ergo', 'mesh:horizon']`; inner — box `[[-1.5, …], [1.5, …]]` instead of
`[[-8, …], [8, …]]` with a body at 5.23 au; hole_stars — approximations `['ньютоновская гравитация точечных масс']`
instead of the two flags.

Fix: make the segment start carry every "latest-value" message the view holds: in the framework, after `rekey`,
re-emit the latest message of each set-like type the world has emitted (`box`, `mesh:id`, `lines:id`, `approx` /
anything with `approximations`, `actions`, `live`) — e.g. the base class keeps the last such message per key in
`self.emit` — or require sections to do it in `rekey` and test it. Test: for every section, the set of set-like keys and
their latest values after (header + record from a segment marker) equals that of the whole record (the s10 check as a
parametrized test).

### F5 — error — p01's trails restart at every checkpoint, for every viewer

Location: `p01_gravity/viz.py:150-151, 380-390, 688-699` (`rekey` → `emit_trails(full=True)`: the points since the
last trail message with `reset: true`), `p01_gravity/web/view.js:25-26, 38-51` (a reset starts a new generation;
`drawTrails` draws only the current one), `sim.py:425-432`.

The segment start's trail message carries only the points since the last trail message (often none: `counts = []`),
and the view starts a new generation on `reset`. So every live viewer's trails vanish every 60 s of play, at every pause
after 10 s and at every suspension; a viewer replaying a kept record sees the same cuts. RULES §6/`playground.py` say
`rekey` emits "e.g. full trails"; PNMode's docstring admits it "starts the trails afresh".

Evidence: `s02_rekey_trails.py` (a): after 1200 frames the view holds `{'o1': 1201, 'o2': 1201}` points; rekey's
message `reset = True counts = []`; right after `{}`. Browser `b01_browser.mjs` b1 (`b01_browser_b1_b2.out`, current
view.js): trail points 11 004 at 57 s, **36** at 60 s when the record's second segment appears, then growing again.

Fix: keep in the world the last `TRAIL_SHOWN` points of each trail (bounded) and let `rekey` emit them with `reset`; the
view then replaces its trails by the same points (no visible change, bounded memory, and F13's generations are no
longer needed); or mark the message `rekey: true` and apply it only when the view holds nothing of that world yet.
Test: the browser check across a segment boundary (F23).

### F6 — error — a failing `frame()` floods the record

Location: `server/lfviz/sim.py:523-532` (when `_frame` raises, `dirty` stays set, `playing` becomes False and the loop
neither waits for a command nor sleeps), `p01_gravity/viz.py:190-192` (positions without bounds), `:400-404`
(`2 ** ceil(log2(1.15 · |x|))` overflows).

`x = 1.7e308` is finite, so the schema accepts it from the inspector's number field; `frame()` then raises
`OverflowError` on every iteration. The record grows by error + state pairs as fast as the CPU allows; the window
cannot trim (no checkpoints while not playing); `meta["errors"]` grows without bound and is rewritten every 10 s; the
player toasts every error.

Evidence: `s03_frame_error_flood.py`: in 2 s after the change `{'error': 8139, 'state': 8139, …}`,
`bytes emitted into the record in those 2 s: 6.8 MB (3.4 MB/s)`.

Fix: in `Runner.run`, clear `dirty` (or wait one period) after an exception and suppress repeats of the same error
(count them); cap `meta["errors"]`; in p01, bound positions and velocities in the schemas and guard `_box` against a
non-finite extent; generally the playground hooks should refuse values whose engine state is not finite (F15).

### F7 — error — thermal guard: hot, then an unreadable sensor → `TypeError` in every GPU kernel choice

Location: `lfphys/lfphys/core/backend.py:296-310` (a failed or `None` reading keeps `hot = True` and sets
`temp = None`), `:340-343` (`f"{_THERMAL['temp']:.0f}"`).

After a reading ≥ 82 °C, if the next reading returns `None` (NVML error — plausible exactly when an overheated card
misbehaves) or raises, `_gpu_hot()` still returns True and the reason formats `None` with `:.0f`; `choose()` raises for
every kernel that wanted the GPU, i.e. the world's computation fails. The test only covers "unreadable" after a cool
state (`set_temperature_reader` resets `hot`).

Evidence: `s11_thermal_guard.py` (a): `second call raises TypeError: unsupported format string passed to
NoneType.__format__; thermal() = {… 'hot': True, 'temp': None …}` for both cases.

Fix: keep the last valid temperature apart (`last_temp`) and use it in the reason, or treat "unreadable while hot" as
hot with its own reason («температура не читается — CPU»); never format `None`. Test: hot → None and hot → raise
through `choose` with a stubbed `_cupy`.

## Determinism, races and the window

### F8 — should-fix — `rekey` changes p01's state at wall-clock moments; a replay continues differently

Location: `p01_gravity/viz.py:390, 699` (`trail_new[k] = [last]` after a full emission, `[]` otherwise),
`sim.py:425-432` (rekey runs inside `checkpoint`, at 60 s of wall time / a pause / a suspension), `sim.py:476-489`
(the replay script has no rekey).

A world restored by replay (no usable checkpoint, F1/F2's paths when they are legitimate) never repeats the rekeys,
so its trail state differs from the original's and its next trail messages differ (RULES §3: byte for byte). It also
makes the recorded trail messages depend on when checkpoints happened in wall time.

Evidence: `s02_rekey_trails.py` (b): original with a suspension checkpoint at the end vs `Runner.restore` of the same
record: `first difference at message 4: type trail; original counts [2, 2, 2], replayed counts [3, 3, 3]`.

Fix: make `rekey` free of side effects (emit a copy of the kept trail; F5's fix does that), and state it in the
contract (`playground.py` docstring). Test: test_restore for playgrounds with a checkpoint in the middle of the record.

### F9 — should-fix — the history and the download race with trimming

Location: `server/lfviz/runs.py:309-345` (`send_history` reads segment files lazily between awaits), `:537-541`
(`_trim` unlinks files; segment 0 is emptied in place with `write_bytes`), `:110-123` (`Viewer.pump` catches only
`ConnectionError, RuntimeError, CancelledError`), `app.py:220-235` (`run_stream`, same reads).

A segment marker ingested while a long history is being sent (a 1 GB window to a laptop takes tens of seconds; markers
come every 60 s) runs `_trim`. (1) With protected segments first, the trim deletes unprotected segments the history has
not opened yet → `FileNotFoundError` → the pump task dies: no `history_end` (the player stays at «загрузка записи…»),
no live messages, the socket stays open. (2) Segment 0 is truncated under its open handle → buffered partial reads →
corrupt or empty messages are sent.

Evidence: `s05_history_trim_race.py` (real `Run`/`Viewer`, fake socket): case 1 `exception: FileNotFoundError …
history_end sent: False`; case 2 `corrupt or empty messages sent: 26 ['<corrupt: 52 bytes>', '<corrupt: 0 bytes>', …]`.

Fix: defer trimming while a history or a download is being sent (a reader count on the `Run`; `_trim` retries at the
next marker), or open every segment of the snapshot before the first await and never truncate a file in place (unlink
and recreate segment 0); in `pump`, catch `OSError` and close the socket so that the player reconnects.

### F10 — should-fix — the window counts wall time, pauses and suspensions included

Location: `server/lfviz/runs.py:499, 752` (`wall0 = time.time()`), `:531` (`now - end_wall > window_s`).

The owner's words were «автозапись всех последних N кадров» (RULES §6, `runs.py` docstring), and the owner guide says
«запись держит последние 10 минут». A pause or a suspension longer than the window, followed by one minute of play,
deletes the minutes computed before the pause — the dashcam would have kept them. Typical case: a long look at an
effect (paused), then play to see what follows.

Evidence: `s04_window_wall_clock.py` (real `Run`, controlled clock): 9 min of play, a pause, 20 min away, 1 min of play
→ `segments [10, 11]  record from world time 540.0 of 600.6`; kept 60.6 s of the 10 computed minutes.

Fix: trim by the time the run spent playing (accumulate per segment the wall seconds while `playing`, or count frames),
not by wall-clock age; keep `wall0` for display only. State the rule in RULES §6 and the owner guide.

### F11 — should-fix — the record panel shows (and posts) the record's state as of the cursor

Location: `player/js/playground.js:223-224` (`rec` in `snapshot`/`restore`), `:244` (`record_state` fed with the
record's messages up to the cursor), `:173, 177` (`postRec({on: rec.recording, …})`), `:227-230` (the passport as
loaded is used only when `rec` is empty).

`record_state` is recorded as an accumulative message, so the panel shows what the recording state was at the time of
the cursor, while the button acts on the run now. Looking at a moment between "on" and "off", the button says
«■ Сохраняется — только окно» although recording is off, and changing the window's minutes posts `on: true`.
`kept_from_t` and the size are also never refreshed: no `record_state` is emitted when the window trims.

Evidence: `b01_browser.mjs` b2 (`b01_browser_b1_b2.out`): server before `{"recording": false, "window_s": 600}`;
button at the end «● Сохранять запись», at the cursor (t = 1.43e8 s, between on and off) «■ Сохраняется — только
окно»; after changing the minutes to 15 there: server `{"recording": true, "window_s": 900, "protected": [[0,0],[0,null]]}`
— recording switched on unintentionally.

Fix: the record's state is the run's, not the world's: keep `rec` outside the key frames (always the latest
`record_state` received or the passport), and emit `record_state` from `_new_segment` when the window trims (or
refresh the passport). The window's input should send only `window_s` (with F12's fix).

### F12 — should-fix — `POST /api/runs/{id}/record` validation

Location: `server/lfviz/app.py:238-252` (`bool(body.get("on"))`, no type checks), `runs.py:546-580`.

Evidence: `s06_record_api.py` (`.out`): `{"window_s": 300}` → 200 and recording **off**; `{"on": "false"}` → 200 and
recording **on**; a JSON list body → 500; `{"window_s": [60]}` → 500.

Fix: require an object; `on` a JSON boolean when present and unchanged when absent; `window_s`/`window_mb` numbers;
400 otherwise. Add these to `test_playground.py`.

## The browser

### F13 — should-fix — the tab keeps a playground session's every accumulative message

Location: `player/js/player.js:546, 590` (`W.viewMsgs.push` for every non-frame message, never dropped),
`p02_quantum/web/view.js:181-182` (`waves`, `vols`), `p01_gravity/web/view.js:18, 26` (`gens`: every trail
generation kept for key frames).

The window bounds the server's record; a live tab keeps everything since it opened. A p02 2-D world sends a
`wave` picture (131 KB) every 5 frames; p01 now keeps every generation of trails. STATUS V39 (g) estimates "~300 MB
for a 10-minute window", but for a live viewer the amount is not bounded by the window: it grows with the session,
which is meant to last hours (RULES §5).

Evidence: `b01_browser.mjs` b3 (`b01_browser_b3.out`): renderer RSS 138 → 188 MB in 90 s of p02 double_slit (≈ 33
MB/min ≈ 2 GB/h) while the frames kept were bounded; `s08_record_by_type.out`: of that run's record, `wave` 273
messages = 35.9 MB, all accumulative.

Fix: drop from `viewMsgs` (and the key frames before them) what lies before the server's window (`kept_from_t`), at
least for playgrounds; keep pictures thinned beyond a budget (V39 g's plan); for p01 see F5 (no generations needed).

## Scene command, hooks and scene files

### F14 — should-fix — p02: a scene file saved at t > 0 re-integrates the whole span in the new world's header

Location: `server/lfviz/playground.py:114` (`self.t = float(scene["t"])`), `p02_quantum/viz.py:266` (the engine's
scene starts at `qs.t = 0`), `:571` (each advance integrates from `qs.t`).

p01's modes sync their clocks to the world's time (`_sync`); p02 does not. The first advance after the header
(`Runner._start_world`, `sim.advance(sim.t)`) integrates every step from 0 to t in one blocking call: the worker
processes no command meanwhile (a 256² world saved after ten minutes of real-time play blocks for a comparable time),
and the result is not "each particle restarts from its packet" (STATUS V39 b, the owner guide) but the packets evolved
for t in the loaded potentials.

Evidence: `s07_scene_hooks_and_files.py` (a): `original: … 4889 scene steps computed over 300 frames (17.0 s)`; the
loaded world `right after its header: … engine steps already computed: 4889 (18.2 s blocking in the header's advance)`.

Fix: set the engine scene's clock to the file's time when a p02 world starts from a file (or ignore `t` for p02); test
`qs.steps == 0` after the header of a world built from a file.

### F15 — should-fix — finite values that overflow in the engine's units are accepted

Location: `p02_quantum/viz.py:166, 168` (`V` without bounds; `_object` divides by `EV`), the hooks' contract
`playground.py:14-16` ("raise ValueError to refuse").

`V = 1e308` eV is a finite value of the schema, `inf` in the scene's units; the box's smooth profile gives `inf · 0 =
NaN`. The change is accepted and the particle's wave becomes NaN for good (removing the barrier does not bring it back).
The same class as F6 (p01 positions).

Evidence: `s07` (b): `accepted: True`, `potential on the grid: NaN points 3968 of 16384`, 20 frames later `norm: nan`,
balance check `{'value': nan, 'ok': False}`.

Fix: bounds on every parameter whose conversion can overflow (V, fields, ħω, positions, velocities), and a
section-level check after `on_add`/`on_set` that refuses non-finite engine data before it is used (the base can call a
`validate()` hook and roll back with `on_remove`/`on_set(old)`).

### F16 — should-fix — p02: changing only the Bohm count replaces the particle's wave

Location: `p02_quantum/viz.py:435-440` (`on_set` of a particle always calls `qs.replace_particle` with its starting
packet).

Evidence: `s07` (c): `⟨x⟩ of the packet before the change 1.4795 nm, right after it -20.0000 nm`.

Fix: replace the wave only when a value that defines the packet changed (species, mass, centre, wavelength,
direction, widths, spin); for `bohm` only re-seed the ensemble. The inspector's help should say which changes restart
the packet.

### F17 — should-fix — scene-file validation

Location: `server/lfviz/playground.py:105-120`, `params.py:172-177` (any JSON is accepted for `scene`).

Evidence: `s07` (d): a list instead of an object → `AttributeError: 'list' object has no attribute 'get'` (through
`POST /api/runs` a "failed" run with that text instead of a 400); objects that are not objects → `AttributeError`;
`t = 'inf'`, `'nan'`, `-1e300` → worlds built at those times (a non-finite `t` is encoded as `null`, which the player
reads as 0).

Fix: in `start_scene`, check the types (`dict`, `list` of `dict`s, `type` a string) and `t` a finite number ≥ 0 with
an upper bound, raising `ValueError`; validate in `POST /api/runs` before a worker is spawned (a static check of the
section) so the catalogue gets a 400.

### F18 — should-fix — the player's «Новый мир» panel carries the hidden initial scene

Location: `player/js/player.js:298-332` (`values = {...header.params}`; `worldParams()` includes the hidden
`scene`, line 325).

Without a preset, the body is `{...params, ...live, ...non-live form values}`, so the current world's initial scene
goes along. Changing p01's laws there (Newton → the post-Newtonian binary) is refused, because the Newtonian objects
are not in the new palette; with the same laws the "new world" restarts the initial scene, not the current one. The
form does not show this.

Evidence: `s13_new_world_panel.py`: `scene objects carried over: ['star', 'planet', 'field']`, `new world refused:
ValueError в этом разделе нет объектов «star»`.

Fix: for a playground, drop `scene` from that body unless a preset is chosen (or offer "the scene now" through
`export`), and say in the panel what the new world starts from.

### F19 — should-fix — a mid-world thermal switch is not reported

Location: `server/lfviz/sim.py:132-139, 329` (the backend's report is emitted only with a header); RULES §5 ("the
reason in the run's header and `used()` says so").

A playground world lasts hours; when the guard moves its kernels to the CPU (slower; GPU = CPU only within tolerance),
the record and the player do not learn it until a new world. `s11_thermal_guard.out` (b) lists where the report is
emitted.

Fix: after each frame (cheap), compare `B.thermal()["hot"]` and the kernels' devices in `B.used()` with the last
reported ones and emit a notice and an updated backend report (a message the player shows in «Устройства»).

## Nits

### F20 — nit — scene size limits do not match

Location: `server/lfviz/params.py:30` (`JSON_MAX = 2 000 000` characters), `app.py:259` (`max_msg_size=1 << 20`),
`player/js/playground.js:153` (the in-player load sends `new_world` over the socket).

Evidence: `s12_ws_size.py` (`.out`): a 1.41 M-character scene starts a run from the catalogue (200) but loading it in
the player closes the socket with code 1009 and no message. The run started from it has a 2.9 MB `meta.json`
(`params` and `worlds[0].params` each hold the scene), rewritten every 10 s while running.

Fix: one limit (e.g. 900 000 characters), checked in the player before sending; keep the scene out of `meta.json`
(a hash or "from file, N objects").

### F21 — nit — checkpoint cadence and the size bound

Location: `server/lfviz/playground.py:73` (`checkpoint_every = 60.0`, half the demonstrations'), `runs.py:523-525`
(the size bound counts only unprotected record files), `:527` (the newest two segments are never dropped).

Evidence: `s09_checkpoint_size_3d.out`: p02 checkpoint 4.8 MB (2-D 256²), 14.7 MB (3-D 64³), 117.5 MB (3-D 128³,
one electron) — up to six electrons on this host's HDD every minute, two files kept, outside `window_mb`. STATUS V37 (c)
says the bound may be exceeded by one segment; it is two. If a world's state cannot be pickled
(`Runner.checkpoint` sets `ckpt_failed`), no further segments start and the record has no window at all (code reading).

Fix: decouple segment boundaries from full checkpoints (a marker + rekey every 60 s, a checkpoint every 120 s or by
size), count checkpoint files in the bound, correct V37 (c).

### F22 — nit — documentation

* RULES §3: the API table and the command list omit `POST /api/runs/{id}/record` and the command `scene`; the
  resuming commands (line 151) and the `command` message (line 262) list `set, action, view, new_world` only; the
  docstrings of `sim.py` (lines 22-24) and `worker.py` (lines 14-15) likewise.
* RULES §6 line 377: segments "every 60 s of computation" — it is wall time since the last checkpoint while playing
  (and pauses after 10 s also start a segment).
* Statements that F1–F5, F10, F19 contradict: RULES §6 line 382 and the owner guide («если начало мира уже вышло из
  окна, пересчёт с начала невозможен — так и пишется»: F1, F2); `runs.py:28-30` "every segment can be shown from its
  first message" (F4); «запись держит последние 10 минут» (F10); RULES §5 on the reason in the header (F19).

### F23 — nit — test coverage

* The toy section implements no `rekey`, so `test_a_checkpoint_continues_the_scene_exactly` cannot see F5/F8; give
  the toy a rekey with state (a trail) or run the session tests on p01.
* `tests/browser/keyframes.mjs` records 21 s per playground job, below `checkpoint_every` (60 s): no segment, no
  reset, no trimmed history is ever drawn. An environment override of `checkpoint_every` (as `P99_CKPT`) for p01/p02
  in tests would let it cross segments.
* No test of protected holes (F1), earlier worlds (F3), a checkpoint that fails to load in a trimmed record (F2),
  history/trim concurrency (F9), the API bodies (F12), or the thermal guard's hot → unreadable path (F7).

### F24 — nit — small code points

* `scene {op: "export"}` is recorded as a world-changing `command`, replayed by restores, and marks the checkpoint
  dirty (`sim.py:234-237`), though it changes nothing.
* `registry.code_hash` uses `f.relative_to(ROOT.parent)`: an `LFVIZ_EXTRA` folder outside `engine/` raises
  `ValueError` (tests only today).
* Switching recording on, off and on again appends overlapping protected ranges (`[[0, 0], [0, null]]` in F11's
  evidence) — harmless, but the list grows with every toggle.
* `catalog.js` shows a `pNN_` folder that fails to load as an error card under «Демонстрации» (the error entry has no
  `kind`).

---

## Checked and found in order (no finding)

* The scene command refuses schema-invalid values, unknown types, ids and operations, and the limits, leaving the
  scene as it was; every change is recorded with its time and repeated by restores (`test_playground.py`, rerun).
* `scene_export` is not recorded; only the tab that asked downloads the file (`exportAsked`).
* p02's `rekey` and `emit_scene` have no side effects on the world's state; p02's and p01's `snapshot`/`restore`
  cover what they draw (the repository's key-frame check passes on records without segments).
* The static files of `pNN_` folders keep the path-traversal check (`app.py`, `registry.folder`).
* `json` parameters reject NaN/Infinity (`allow_nan=False`) and are size-bounded.
* `setSpheres` keeps the experimenter's layer visibility through a rebuild (`addLayer` uses `S.userVis`).
* The thermal guard's hysteresis and its 2-s cache behave as stated; NVML is addressed by the same PCI id as CuPy
  (`docker-compose.yml`: `LFPHYS_GPU_PCI`).

## Files

| file | what |
|---|---|
| `s01_resume_trimmed.py` / `.out` | F1, F2, F3 (real server, real workers, toy section) |
| `s02_rekey_trails.py` / `.out` | F5 (a), F8 (b) |
| `s03_frame_error_flood.py` / `.out` | F6 |
| `s04_window_wall_clock.py` / `.out` | F10 |
| `s05_history_trim_race.py` / `.out` | F9 |
| `s06_record_api.py` / `.out` | F12 |
| `s07_scene_hooks_and_files.py` / `.out` | F14 (a), F15 (b), F16 (c), F17 (d) |
| `s08_record_by_type.py` / `.out` | F13 (the record of b3 by message type) |
| `s09_checkpoint_size_3d.py` / `.out` | F21 |
| `s10_segment_self_contained.py` / `.out` | F4 |
| `s11_thermal_guard.py` / `.out` | F7, F19 |
| `s12_ws_size.py` / `.out` | F20 (needs the private server) |
| `s13_new_world_panel.py` / `.out` | F18 |
| `b01_browser.mjs`, `b01_browser_b1_b2.out`, `b01_browser_b3.out` | F5 (b1), F11 (b2), F13 (b3) in Chromium |
| `b02_keyframes_playgrounds.out` | the repository's `keyframes.mjs` for p01/p02 on the private server |
| `00_baseline_*.out` | the repository's tests rerun |
| `runs_browser/` | `meta.json` and `worker.log` of the private server's runs (records removed after measuring) |
