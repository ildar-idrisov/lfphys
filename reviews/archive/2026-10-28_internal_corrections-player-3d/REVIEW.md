# Review: the owner's corrections of 2026-10-28 (player history, restore / suspend, v11 / v12 in 3-D)

Status: **awaiting processing**

Reviewer: internal (subagent, Opus), independent of the author. Scope: the uncommitted working tree against commit
`4840bcf` (B4) under `engine/`, plus the later additions (scene3d `disposeTree`, camera kept on rebuild, user layer
visibility kept, relative time tolerance in the player, `api.gpuInfo()`).

Environment: Docker image `light-funnel-viz`, engine mounted read-only at `/lf`; own server on port 8502 with a
temporary runs dir; headless Chromium (Playwright 1.58.2, SwiftShader). Scripts `cNN_*` in this folder, outputs in
`out/`.

## Findings

### C1-1 (error) Two ⏺ on a suspended run at once start two workers; one is orphaned for the server's lifetime

**Location.** `server/lfviz/runs.py`: `Run.command_resuming` → `RunManager.resume` → `_spawn`.

**Claim.** `resume` checks `run.running` once at its start and sets `run.proc` only after `await
asyncio.create_subprocess_exec(...)` inside `_spawn`. A second resuming command (a second viewer's ⏺, a REST command,
the same owner in two tabs) that arrives during that await passes the same check: both spawn a worker, both write the
"Продолжение…" notice, the second overwrites `run.proc`, `run.file` and `run._reader`. The first worker is then tracked
by nothing: `n_running()` does not count it (the `max_workers` limit no longer holds), nothing reads its stdout (if it
were playing it would block on a full pipe), `stop`/`suspend`/`shutdown` never reach it, and it lives until the server
process ends. The first reader task reads `self.proc` afresh in every iteration, so for a moment two readers may read
the same pipe (a corrupted record if both get data).

**Evidence.** `c02_server_races.py` T1 → `out/c02_server_races.txt`, `out/c02_T1_processes.txt`: two concurrent
`play` on a suspended v01 run → both 200, `resumed: 2`, two "Продолжение" notices and two `state: start` in the record;
after `POST /stop` the tracked worker (pid 16) ended, worker pid 14 stayed alive (`/proc` listing) while
`/api/health` reported `running: 1`. The server log (`out/c02_T1_server_log.txt`) shows the two readers colliding on
one pipe: `Run.read_worker()` died with «readexactly() called while another coroutine is already waiting for incoming
data» (here the surviving reader kept the framing; with another interleaving one reader takes a message's length and
the other its body).

**Fix.** Make resuming exclusive per run: an `asyncio.Lock` (or a `run.resuming` future) taken in `resume` before the
`running` check and held until `run.proc` is set; a second caller awaits it and then just forwards its command. Same
for `start`'s `_make_room` (two starts can both see a free slot). A test: two concurrent resuming commands → one
worker, one notice.

### C1-2 (should-fix) A command accepted during a rebuild is silently lost when a suspension arrives; the suspension then waits 5 s and kills the worker

**Location.** `runs.py` `Run.stop` (used by `suspend`), `worker.py` (commands are queued but not read during
`Runner.restore`), `Run.command_resuming`.

**Claim.** While a resumed worker rebuilds its world it does not read its command queue; a `set`/`action`/`view`
sent meanwhile is acknowledged (`{"ok": true}`, nothing returned to the viewer) and queued. If the run is suspended
before the rebuild ends (housekeeping, `_make_room` for another run, `POST /stop`, server shutdown), `stop` writes
`stop` after it, the worker cannot answer within 5 s, it is terminated (returncode −15) and the queued command is never
applied nor recorded. The player that sent a `set` keeps «перестраивается установка…» until reload. Also: a run
resumed through REST (`POST /resume`, scripts) has no viewer and keeps its old `last_viewer_time`, so housekeeping
suspends it again at its next tick if it was idle for more than `idle_suspend` before — typically in the middle of its
rebuild.

**Evidence.** `c02_server_races.py` T2 (`out/c02_server_races.txt`): a v04 run recorded for 12 s at 10⁹ s/s (228
frames, ~100 orbits; its rebuild takes longer than 5 s on this CPU), `POST /resume`, then a `set` (200 ok) and
`POST /stop` 0.3 s later → state suspended, returncode −15; resumed again and stopped: "commands recorded []" — the
`set` is in neither the world nor the record. `out/c02b_rest_resume_resuspended.txt`: `POST /resume` of a run idle
for longer than `idle_suspend` → «running» at 2 and 4 s, «suspended, no viewers» from 6 s on (the housekeeping tick).

**Fix.** Refuse world-changing commands while a rebuild is under way (409 «мир ещё пересчитывается»), or make `stop`
wait for the rebuild (and do not suspend a run that is rebuilding; `_make_room` and housekeeping should skip it); reset
`last_viewer_time` on every resume; report a command that was not applied (a `closed` with the reason, an error to the
viewer).

### C1-3 (error) The checks panel hides every check that was recomputed later: before its last version, the check disappears

**Location.** `player/js/player.js`: `W.checks` is a `Map` by check id (the latest version only); `renderChecks` and the
"what depends on the time shown" key in `loop()` skip a check whose `t` is after the cursor.

**Claim.** RULES §3 (new): «checks computed later … are shown as of that time». A check that a world re-emits as the run
goes on (v04: the periapsis, apoapsis, e² − 1, the advance per orbit, the PPN comparison and the radial period — once
per orbit) has an earlier version at almost every moment of the history, but the player keeps only the latest one and
hides it while the cursor is before that one's time. So anywhere in the history except the last orbit those checks
are missing from the panel — not shown "as of that time", not shown at all.

**Evidence.** `c06_checks_at_cursor.mjs` on a recorded v04 run (record t = 0 … 108 s; each of the six checks re-emitted
up to t = 100.2 s) → `out/c06_checks_at_cursor.txt`: at 25 %, 50 % and 75 % of the history 4 rows are shown of the 10
checks computed by then (the six missing are listed with their values at that time); at the end, all 10.

**Fix.** Keep every version of a check (`W.checks: Map<id, [versions sorted by t]>`) and show, per id, the latest
version with `t ≤` the cursor (binary search). The panel's change key should then count versions, not ids.

### C1-4 (should-fix) The restore ignores the recorded time of a command: a command handled after a `step` / `next_event` in the same batch is replayed before that advance

**Location.** `server/lfviz/sim.py` `Runner.restore` (commands: `self.handle(...)` at whatever time the rebuilt world
has reached); `Runner.run` (a batch of queued commands is handled before the frame is drawn).

**Claim.** The script repeats "every frame's advance and every command, in order", but the advances of `step` and
`next_event` are not in it — they are recovered from the next frame's time. When a world-changing command is handled
in the same batch after a `step`/`next_event` (paused world: `step`, then `set` already queued; a script sending
`POST step` and `POST set`), its `command` message carries the time after the advance, while no frame lies between
them; the restore applies it at the earlier time and only then advances. The recorded `t` of every command is
available and unused.

**Evidence.** `c01b_restore_commands.py` [C] → `out/c01b_restore_commands.txt`: v11, `step` then `set slit_b=False` in
one batch: recorded at t = 1.4796e-16 s, applied by the restore at 8.4549e-17 s; the continuations differ (Bohm track
positions by 0.5 λ in the first message). Without such a batch the restore is exact for every visualization
(`c01_restore_all_messages.py` [A]: every message after the suspension point identical, 14 of 14).

**Fix.** In `restore`, `if c["t"] > self.sim.t: self._advance(c["t"])` before handling a command (the substeps of the
live run's `step` are reproduced since it advanced from the same time to the same target); and/or let `Runner.run`
draw a frame right after `step`/`next_event` before handling further commands. A test with `step`+`set` in one batch.

### C1-5 (should-fix) A restored world n ≥ 2 loses the slice planes it took over from the previous world

**Location.** `Runner.restore` / `worker.py` (the world is built from its header's parameters and seed; `adopt_view`
is not called); `Runner._new_world` (`sim.adopt_view(self.sim.view_state())`); `server/lfviz/planes3d.py`.

**Claim.** RULES §2.10: «a new world of the run keeps them (`Simulation.view_state` / `adopt_view`)». After a resume
the latest world is rebuilt from scratch, so the planes the experimenter placed in an earlier world and carried into
this one are back at the default (plane 1, y = 0) and planes 2–3 are gone; the planes the owner sees in the player
(from the record) no longer exist in the world. The next view command shows it: moving plane 2 recreates it at its
default, and the next `planes` message removes the others from the scene.

**Evidence.** `c01b_restore_commands.py` [D]: v08, plane 1 tilted (n = (0.5, 0, 0.866)) and plane 2 (n = (0, 1, 0))
placed in world 1, then `new_world`: world 2 as it ran has both; world 2 restored has `{1: (0, −1, 0)}` only.

**Fix.** Record the handed-over view state as part of the new world (e.g. a `command {cmd: "adopt_view", args:
state}` emitted right after the header, or a `view_state` field in the header) and apply it in `restore` before
`_start_world`. Extend `tests/test_restore.py` to a world n ≥ 2 with planes.

### C1-6 (should-fix) "The same result frame for frame" is not true for v10 and v02 on a live server: their computation depends on wall time

**Location.** `v10_fast_observer/viz.py` `advance` (an image is rendered when `time.monotonic() - last_img_wall >=
IMG_PERIOD`, 0.35 s wall; the image counter `seq` and the "heavy" checks every 20th image follow it);
`v02_double_slit/viz.py` `_coherence_err` (the bootstrap error of |γ₁₂| recomputed at most once per wall second,
cached and scaled in between). STATUS V32 (a) names only v04's ghost; RULES §3 «A world must therefore be
deterministic …»; README (owner guide): «тот же результат кадр в кадр».

**Claim.** `tests/test_restore.py` drives the original world without wall time between its frames, exactly as the
restore does, so it cannot see a dependence on wall time. On the server frames are 50 ms apart and a rebuild replays
them in a burst: v10 renders far fewer images during the rebuild, so after a resume its images come at other world
times, its `seq` restarts below the record's (duplicate `seq` numbers in one record; `imagewin`/the view key images by
`seq`) and its heavy checks fall on other images; v02's error of the histogram's |γ₁₂| (shown in the frames) comes out
different.

**Evidence.** `c01_restore_all_messages.py` [B] (`out/c01_restore_all_messages.txt`): the original advanced with wall
time between frames, the restore without: v10 — the original's continuation emits an `image` the restored one does not
(7 vs 6 messages); v02 — `frame.coh.err` 0.0440 vs 0.0649 in the first frame after the suspension point. (v04 with its
ghost off: identical.)

**Fix.** Drive these schedules by world time or by frame count (v10: an image every k frames or every Δt of world
time; v02: recompute the bootstrap when the count grew by 10 %, without the wall-clock gate, or seed it by the count
only), or record their decisions (`image` messages already carry `t`: the restore could render exactly at those
times). List every wall-clock dependence in STATUS V32 and soften the guide's «кадр в кадр» until they are gone; add a
restore test with wall time between frames (as c01 [B]).

### C1-7 (should-fix) Slice planes edited while the cursor is in the history: nothing happens at the cursor, and on a suspended run the whole world is rebuilt for it

**Location.** `player/js/env3d.js` (`sendPlane`, `addPlane`, the gizmo; read-only only for an archived world), the
`view` command (applied at the world's current time, the end of the record), `player.js` `feedView` (messages after
the cursor are not fed), `runs.py` `RESUMING` (contains `view`).

**Claim.** RULES §3: «The set-up and actions can be changed only at the end of the history» — the planes are not
covered. In a time-dependent 3-D world (v09, v13, v14) a plane added or moved with the cursor in the middle is computed
by the run at the end time; its `planes`/`slice` answers carry that time and are not fed to the view, so the scene and
the windows do not change at all (no message says why); the plane appears when the cursor reaches the end. On a
suspended run the `view` resumes it: a full rebuild of the world (as long as the original computation, STATUS V32
(c)), for a change the owner does not see.

**Evidence.** `c07_planes_in_history.mjs` → `out/c07_planes_in_history.txt`: v13, cursor at 111/222, «＋ Срез» → after
6 s planes in the scene `[1]`, one window; after ⏭ `[1, 2]`, two windows. Suspended run, cursor at 1/3, «＋ Срез» →
server state `running`, `resumed: 1`, scene and windows unchanged.

**Fix.** Treat plane edits like the set-up: disabled away from the end (or the cursor jumps to the end with a notice),
and never resume a run for a view request — answer it only for a running world.

### C1-8 (should-fix) ⏺ refused (all workers busy) leaves «продолжение: мир пересчитывается по записи…» on screen

**Location.** `player/js/player.js` `onMessage` case `"error"` (clears only the pending `"world"`), `toggleRecord`,
`$("step")`, `$("next")` (set the pending `"resume"`).

**Claim.** When the server refuses to resume (`OverflowError`: every worker serves a viewed run; `RuntimeError`: an old
record, a failed run), the WebSocket text error becomes an `error` message: a toast for 9 s, but the busy label
«продолжение: мир пересчитывается по записи…» stays until the page is reloaded or a later resume succeeds, while
nothing is being computed. The error is also pushed into the latest world's events with no `t` (shown as «—», never
"in the future").

**Evidence.** `c08_transport_edges.mjs` (c) → `out/c08_transport_edges.txt`: v04 suspended, two v01 runs open in
other tabs (max_workers = 2): ⏺ → the toast «все 2 вычислителя заняты…» and the busy label; 13 s later the label is
still there, the toast gone.

**Fix.** Clear the pending `resume` on any error (and on `closed`), and give the WebSocket text errors a `t` (the time
shown) or keep them out of the event log.

### C1-9 (should-fix) Removal by quota ignores the last action and removes runs that are open; a visit to a suspended run is not saved

**Location.** `server/lfviz/runs.py` `RunManager.cleanup`, `Run.touch`, `_load_existing`.

**Claim.** The owner asked for removal «по времени последнего действия». (Q1) Over the quota, runs are removed oldest
*created* first, so a run created long ago but used a minute ago goes before runs untouched for days. (Q2) `cleanup`
skips running runs only: a suspended run that a viewer has open right now is removed by the quota (or after 3 days in
an open tab) — the record and folder vanish under the player. (Q3) `touch()` changes only the in-memory meta of a run
that is not running (opening a suspended run to look at it, or a `speed` sent to it); `save_meta` is never called for
it, so after a server restart its last action is the old one again and it is removed earlier than 3 days after the
visit. (Q4) Records from before `last_action` fall back to `meta.json`'s mtime, but `_load_existing` rewrites every
`meta.json` at start, so they are removed only after 3 days of uninterrupted uptime.

**Evidence.** `c04_cleanup.py` → `out/c04_cleanup.txt` (fake records in a temporary folder, RunManager only): Q1
removed the run used a minute ago; Q2 removed the viewed run (folder gone); Q3 in memory 0 d, on disk and after a
restart 2.000 d, removed by the next cleanup at 1.9 days' limit; Q4 mtime refreshed by the start, nothing removed.

**Fix.** Order the quota removal by `last_action` (falling back to `created`); skip runs with viewers (and runs
resuming); `save_meta()` in `touch()` when the run is not running (or in `add_viewer`/`remove_viewer`); give records
without `last_action` one from their stream file's mtime once, at load, before saving.

### C1-10 (error) A record cut by a crash is resumed by appending after the cut; at the next start the server does not come up

**Location.** `runs.py` `RunManager.resume` (`open(stream, "ab")`, `run.size` = the file's length including a cut
tail), `_load_existing` (stops at a cut message, keeps the file as it is; `protocol.peek_meta` on every message, no
error handling), `protocol.iter_stream`.

**Claim.** A server killed mid-write (`docker kill`, the OOM killer, a power cut; also `docker stop` when shutting the
workers down takes longer than its 10 s grace: `stop` waits up to 5 s per run, in turn) leaves the last message of a
record cut. Before this change such a record was read-only: the loader ignored the cut tail. Now the run is
"suspended" (restorable) and a ⏺ appends new messages *after* the cut bytes, so the cut message's length prefix covers
part of the new data. That session looks fine (its index was built before); at the next start `_load_existing` decodes
garbage, `peek_meta` raises, `RunManager()` fails and **the whole server does not start** — every run is unavailable
until someone removes the folder by hand. (Independently of the append, a record ending in zero bytes — a filesystem
can leave them after a power cut — also makes `peek_meta` raise at start: `c04_cleanup.py`'s first version did exactly
that with a zero-filled fake stream.)

**Evidence.** `c09_partial_tail.sh` → `out/c09_partial_tail.txt`: v01 run recorded and suspended (71 messages), the
record cut by 10 bytes while the server was stopped, server started (70 messages loaded), ⏺ → resumed, 158 messages;
`docker restart` → «SERVER DID NOT COME UP», the container exited with `UnicodeDecodeError` in
`_load_existing → peek_meta` (traceback appended to the same file); parsing the file stops at message 70, the end
message whose JSON now runs into the appended data.

**Fix.** At load, truncate a record to its last complete message (or mark it read-only) before it can be appended to;
in `resume`, `seek`/truncate to the indexed end before writing; make `_load_existing` skip (and report) a record it
cannot parse instead of failing the server; optionally `os.fsync` the stream at suspension.

### C1-11 (should-fix) The new check «Попадания частиц Бома по y против картины P(x, y)» cannot fail for a wrong y-motion

**Location.** `v11_double_slit_2d/viz.py` `_y_checks` (check `bohm_y`, also run by v12), its note, the README's
"checks" list.

**Claim.** The check is presented as testing the Bohm y-motion («y траектории — y₀·σy(t)/σy (точное движение Бома в
свободном множителе η) … (эквивариантность вдоль y)»). Over a flight to the screen η spreads little at the shipped
parameters (σy(t_hit)/σy0 ≈ 1.02 small geometry, 1.22 v11 defaults, 1.04 v12 defaults), so the Kolmogorov–Smirnov test
at 99.9 % with a few hundred to 2000 hits cannot tell the right motion from no motion at all, nor from twice the
spreading: what it tests is that the y starts were drawn from |η₀|². (The physics of the extension itself is right:
the potentials, absorbers, plate, spin/detector mark and flux tube do not depend on y, so ψ = ψ(x, z, t)·η(y, t)
exactly; J_z = J₂|η|², so P(x, y) = ∫J₂(x, t)|η(y, t)|²dt as accumulated; η and σ(t) = σ₀√(1 + (t/2σ₀²)²) in the
solver's units ħ = m = 1, λ = 1 match `FreeGaussians` and `bohm.gaussian_trajectory`.)

**Evidence.** `c05_bohm_y_power.py` (worlds run to the end offline; the check's own statistic recomputed for the same
hits under wrong y-motions) → `out/c05_bohm_y_power_{small,default,v12}.txt`: v11 defaults, n = 373, critical 0.101:
as shipped D = 0.024, «no spreading y = y0» D = 0.043, «double spread» D = 0.070 — all pass; small geometry and v12
defaults the same (every alternative passes). The shipped check values agree with the recomputation.

**Fix.** Either state what it tests («старты по y — из |η₀|²; движение по y этой проверкой не различимо: η за полёт
расплывается на N %») or make it a test with power: compare each hit's y with an independent integration of
dy/dt = (ħ/m) Im(∂_yη/η) from the run's η (a second method, deterministic, per particle), or move the comparison to
a σy where the spreading is large (σy ≲ 0.5 λ) in the tests.

### C1-12 (should-fix) The player's thinning of a long history is geometric, not uniform: the early history of a long session shrinks to a handful of frames

**Location.** `player/js/player.js` `thinFrames` / `MAX_FRAMES` (comment: «beyond it the history keeps every second
frame (uniformly), never only the latest»); `server/lfviz/runs.py` `HISTORY_FRAMES` (4000, uniform stride on a
(re)connection).

**Claim.** Each time the frames exceed 20 000 the player keeps every second one of *all* frames, including those
already thinned, while new frames keep arriving at full rate. After k thinnings the oldest part is at 2⁻ᵏ of its
density: at 20 frames/s a thinning happens every ~500 s of recording, so after two hours the first fifth of the
history has almost no frames — the timeline cannot be placed there and ◀/▶ jump over it — while the last tenth is
dense. The same run reloaded shows a uniform 4000 frames instead (another density, another index for the same time).

**Evidence.** `c12_thinning.mjs` (the function copied as logic) → `out/c12_thinning.txt`: frames kept per second of
recording, by tenths of the history, oldest first — 0.5 h: 5 … 20; 2 h: 0.00 0.00 0.01 0.03 0.08 0.23 0.58 1.70 4.17
12.6; 6 h: zero in the first seven tenths, 5.3 in the last. After a reload: uniform 2.2 / 0.56 / 0.19.

**Fix.** Keep a global stride: give each frame its arrival number, double the stride when the limit is passed, keep
the frames whose number is a multiple of the stride (and the last one), and append a new frame only if it is one of
them — uniform density at any length; use the same limit as the server's history so a reload does not change it.

### C1-13 (should-fix) Going back costs a replay of the whole record up to the cursor; for v11/v12 it is already seconds per step and grows with the record

**Location.** `player.js` `syncView` / `rebuildView` (every step back past a message replays all messages from the
world's start); `v11_double_slit_2d/web/view.js` `onMessage` case `"wave"` (after `reset()` `nowT = Infinity`, so
every wave image fed during a rebuild is shown: decoded again into three arrays, turned into a 96×96×48 volume, uploaded
as a 3-D texture, and set into the panel and the window — only the last one is needed).

**Claim.** STATUS V32 (b) says backward play «shows fewer frames per second» for heavy worlds. Measured, the cost of one
step back is O(the record up to the cursor), and for the two worlds of the owner's complaint it is large already for
short records on a coarse grid: the owner's ◀ is a slide show there, and a full experiment (V26 (c): ~14 MB of wave
images) will be worse. The other worlds are fine at these lengths (v01, v04, v09 ≤ 0.1 s per step at 90 s).

**Evidence.** `c10_rebuild_cost.mjs` → `out/c10_rebuild_cost.txt` (one step, median of 5, SwiftShader): v12 (coarse,
300 particles) one step back at 90 % of the history after 15 / 45 / 90 s of recording: 155 / 535 / 1992 ms, against
~30 ms forward; at 50 %: 122 / 314 / 623 ms. `c03_player_history.mjs` (`out/c03_player_history_batch2.txt`, `_batch3`):
◀ shows 2.2 (v12), 2.4–2.8 (v11), 1.0–1.6 (v09) distinct frames per second against ▶ 4.0, 3.2–3.6, 3.2–3.4.
(`out/c10_rebuild_cost_at_end.txt`: the first version measured only at the end, where a finished experiment has no
messages between its last frames, so no rebuild — those small numbers are not the cost.)

**Fix.** In the views: feed during a rebuild without drawing (v11: keep decoded wave images in a cache that survives
`reset()`, show the wave only in `render`); in the player: periodic snapshots of a view's state (or a `seek(t)` contract
for the heavy views: time-indexed draw ranges, as v11's own 2-D overlay already does with `trackT`), so a step back
replays from the nearest snapshot, not from the start.

### C1-14 (should-fix) One failed rebuild makes a run unresumable for good, and the player calls it «старая запись»

**Location.** `runs.py` `Run.read_worker` (a worker ending with a non-zero code while the state is "running" → "failed"),
`RunManager.resume` (refuses "failed"), `player.js` (`closed`/`history_end` → `S.ended` → «старая запись — продолжить
нельзя»).

**Claim.** A rebuild can fail for reasons that pass: memory (three workers rebuilding at once in a 6 GB container, a
busy GPU), a parameter renamed in code and renamed back, a bug fixed since. The worker then exits with code 4 (or 2),
the run becomes "failed", and every later ⏺ or `POST /resume` is refused («запуск завершился сбоем: продолжить нельзя»)
although its record is intact and the cause may be gone. The player shows such a run as «старая запись — продолжить
нельзя», the words for a record from before this version; the error itself is logged at «0 с», and the worker's
`error`/`end` messages at t = 0 also set the run's `sim_t` to 0 (catalogue and passport). The same happens to a run
whose worker crashed while computing (it was resumable a moment before).

**Evidence.** `c14_failed_resume.sh` → `out/c14_failed_resume.txt`: a suspended v01 run whose latest world's parameters
gained an unknown key (as after a rename) → ⏺ → «failed», error «unknown parameter …»; the key removed and the server
restarted → still «failed», ⏺ and `POST /resume` refused; its `sim_t` is now 0.0 (it was ~60 s). `c15_catalogue_and_failed.mjs` (1) →
`out/c15_catalogue_and_failed.txt`: the page says «старая запись — продолжить нельзя», ⏺ disabled, the error at «0 с».

**Fix.** A failed rebuild leaves the run "suspended" with the reason (`resume_error`), so ⏺ can retry; reserve
«старая запись» for records without `restorable`, and say «продолжение не удалось: …» otherwise; give the worker's
error the record's end time.

### C1-15 (should-fix) A run that was just used cannot be deleted for half an hour

**Location.** `player/js/catalog.js` (the delete button only when `state !== "running"`; the stop button removed),
`runs.py` `RunManager.delete` («запуск сейчас считается: удалить его можно, когда он приостановлен (закройте его
вкладку)»), the idle limits (pause after 60 s, suspension after 1800 s without viewers).

**Claim.** With «Стоп» gone, a run keeps its worker for 30 minutes after its last viewer left. In that time the
catalogue offers no ✕ for it and the server refuses to delete it, with advice («закройте его вкладку») that the owner
has already followed. A trial run the owner wants gone right away stays (and holds a worker) for half an hour. (The
row also says «идёт запись» for up to a minute after the tab was closed: the run computes on until the idle pause.)

**Evidence.** `c15_catalogue_and_failed.mjs` (2): v01 recorded, its tab closed → catalogue row «идёт запись … ☆» with
the ☆ button only; `DELETE` → 409 with the message above.

**Fix.** Let ✕ (and `DELETE`) suspend a run that has no viewers and then delete it; or pause at once when the last
viewer leaves (the owner's wording «если я вышел в каталог, то эксперимент в паузе») and suspend runs without viewers
when asked to delete them.

### C1-16 (error) After a crash, a world started shortly before is resumed with the previous world's parameters

**Location.** `runs.py` `_load_existing` (takes `worlds`, `params`, `sim_t`, `preset` from `meta.json`, which a
running run saves only every 10–15 s), `RunManager.resume` (`world = meta["worlds"][-1]`, but the script is cut after
the stream's last header).

**Claim.** If the server dies without its shutdown (SIGKILL, OOM, power, `docker stop` past its grace period) less than
~15 s after a «Новый мир», `meta.json` does not know the new world yet. The resume then builds the *previous* world
from its parameters and seed, numbers it with the previous number, and drives it through the *new* world's frames and
commands: the record goes on, under the new world's header and title in the player, with frames computed by the other
world (other laws or initial conditions) — silently, with the notice «Мир восстановлен…». The notice's «до t = …» is
the stale `sim_t` of the old world.

**Evidence.** `c16_kill_after_new_world.sh` → `out/c16_kill_after_new_world.txt`: v01, world 1 «measure_c» for 12 s,
`new_world` «sun_earth», 3 s later `docker kill` of the review server; after the start `meta.worlds = [(1,
'measure_c')]` and `sim_t` 0.0059 s while the stream holds the headers of worlds 1 and 2; ⏺ → «Продолжение … до t =
0.0059 с», «Мир восстановлен … продолжается с t = 60.14 с» (world 2's time) — the world rebuilt is world 1's.
(`c16b_restart_after_new_world.sh`: with a graceful `docker restart` the meta is saved and the resume is right.)

**Fix.** At load (or in `resume`), take the latest world's parameters, seed, preset and number from the last `header`
in the stream, and `sim_t` from the last message — the stream is the record; `meta.json` is a cache. Save the meta at
every header (a new world) as well.

### C1-17 (nit) v11/v12: the «Опыт» panel can show another frame than the cursor

**Location.** `v11_double_slit_2d/web/view.js` `render` (the panels are redrawn at most every 250 ms: `now - lastPanels
> 250`).

**Claim.** When the cursor stops less than 250 ms after the previous render (stepping with |▶, a short drag of the
timeline), the last render skips the panels and nothing redraws them later: «Опыт» (τ, norm, counts) shows the
previous frame while the clock and the scene show the cursor's.

**Evidence.** `c03_player_history.mjs`, `out/c03_player_history_batch2.txt` and `_batch3.txt`: v11 reached frame by frame
(A) and by a jump (B) — identical scenes and clocks, but «Опыт» shows «0,6789 ед.» in A and «0,7194 ед.» in B (one
frame apart).

**Fix.** Redraw the panels when the frame shown changed and no render follows (a trailing `later(...)`), or key the
throttle on the frame, not on wall time.

### C1-18 (nit) What the top bar and two panels show is the latest, not as of the cursor

**Location.** `player.js` `onMessage`: `W.header.approximations = meta.approximations`, `W.header.engine =
meta.engine` (on `live`), `W.header.actions = meta.actions`; `rebuildView` passes this mutated `W.header` to
`view.onHeader`.

**Claim.** RULES §3: «Whatever is shown is the state at the cursor's time … a view must be a function of the messages
it has been fed». The approximations badge, «Физика этого мира» and the action forms (e.g. the current speed of each
observer in a live action) are overwritten by later messages and not rolled back with the cursor; and since the
mutated header is what a rebuilt view receives in `onHeader`, a view that read those fields would see the future.
No visible error found in the current views (they do not read them).

**Fix.** Keep these as time-indexed lists like `liveHist` and render them for the cursor's time; pass the original
header to `onHeader`.

### C1-19 (nit) During a rebuild the page says «приостановлен — ⏺ продолжит»

**Location.** `player.js` `updateTransport` (`S.suspended` stays true until the first `state` message after the
rebuild).

**Claim.** While a resumed world is rebuilt (13.6 s for a 30-s v04 record here; minutes for long v11 records, V32 (c))
the ⏺ button looks idle and the status invites pressing it again, next to the busy label «продолжение: мир
пересчитывается по записи…». A second press is harmless (a queued `play`) but the page contradicts itself and gives no
progress.

**Evidence.** `c08_transport_edges.mjs` (d), `out/c08_transport_edges.txt`: 0.5 s → «⏺ | приостановлен — ⏺ продолжит
· история | продолжение: мир пересчитывается по записи…»; 13.6 s → «⏸ запись | запись идёт».

Similarly, an archived world at its end is labelled «мир из записи · вживую» while the current world records
(`out/c17_archived_world.txt`): «вживую» follows the current world's ⏺, not the world shown.

**Fix.** A state «пересчитывается» between ⏺ and the first `state` (button pressed, status «мир пересчитывается по
записи до t = …»); optionally the worker can report progress (frames replayed / total) through a non-recorded message.
Say «конец записи» for an archived world.

### C1-20 (nit) Small inconsistencies of a resumed run's identity

**Location.** `worker.py` (`seed0 = init["seed"]`, the latest world's seed), `runs.py` `resume` (`meta["code"]` is
never updated).

**Claim.** (a) After a resume, a later «Новый мир» without a seed uses the restored world's seed, not the run's first
seed as the same run without a suspension would (they differ when a world was started with its own seed). (b) A run
continued under changed code keeps the old code hash in its passport; the notice «Код визуализации изменился…» is the
only trace, and it is repeated at every later resume.

**Fix.** Pass the run's first seed separately in `init` for `make_world`; record each resume (`resumes: [{wall, t,
code}]`) in the passport.

## What I found sound

* **The restore is exact when nothing depends on wall time** [useful]. `c01_restore_all_messages.py` [A]: for all 14
  visualizations, every message emitted after the suspension point (frames, checks, tracks, waves, screens, targets,
  detections, pairs, paths, triads, apsides, trails …) is identical bit for bit between the original world and the one
  rebuilt from the server's script, including a live change (v04, v10, v11), a view command (v08) and the particle
  sources whose draws depend on the frame split (v02, v05, v07). The design — repeat the very same frame advances and
  the recorded commands, muted — is the right one; the gaps are C1-4 (command times), C1-5 (adopted planes), C1-6
  (wall-clock schedules), C1-16 (stale meta after a crash).
* **Suspend / resume basics** [useful]: an idle run is suspended and resumed by ⏺ with one header in its record and its
  time going on (`out/c02_server_races.txt` T3 after a worker was freed; `out/c08_transport_edges.txt` (c)); a graceful
  restart keeps the latest world (`out/c16b_restart_after_new_world.txt`); restorable runs are "suspended" after a
  restart, older ones "interrupted" and read-only; `history_end`/`closed` carry the state the player needs.
* **The player rebuilds the views correctly** [useful]. `c03_player_history.mjs`: the same middle frame reached forward
  (fed message by message, many renders) and backward (rebuilt from the record) gives pixel-identical centres for v02,
  v04, v08, v09, v10, v11, v12, v13 and ≤ 17 px of anti-aliasing for v01; identical checks, events, set-up and right
  panels except C1-17 (batch 2's v09 difference was the test stepping one frame too far, fixed and re-run in batch 3).
  The 3-D trajectories, particles, wave volume and screen rewind with the cursor (STATUS V26 (e) is indeed closed); the
  camera, the layers switched off and the volume look survive a rebuild; `disposeTree` holds the GPU objects constant
  over 40 rebuilds of v09, v10, v11, v13 (`out/c13_gpu_objects.txt`; STATUS V29's closure holds).
* **The transport the owner asked for is there** [useful]: ⏺ / pause, ⏮ ◀ ▶ ⏭, no «вживую» and no «Стоп», the cursor
  at the end follows a recording live, ⏺ in the middle adds frames while the cursor stays, controls of the set-up and
  actions disabled away from the end, Space on a focused ⏺ toggles once (`out/c08_transport_edges.txt` (a)), an
  archived world has its own timeline and refuses ⏺ (`out/c17_archived_world.txt`).
* **The physics of the third dimension** [useful]: the potentials, absorbers, plate, spin field / detector and flux
  tube do not depend on y, so ψ(x, y, z, t) = ψ(x, z, t)·η(y, t) holds exactly for a product start; J_z = J₂|η|², so
  P(x, y) = ∫J₂(x, t)|η(y, t)|²dt is what the run accumulates and its x-marginal is the old P(x) (`screen_y` ≤ 4·10⁻¹³ at
  v11's defaults, `out/c05_bohm_y_power_default.txt`); η, σ(t) and y(t) = y₀σ(t)/σ₀ are the engine's closed forms in the
  solver's units (ħ = m = 1, λ = 1), y₀ is drawn from |η₀|² after the x, z starts (the 2-D results are unchanged);
  every y drawn — the volume's profile, the tracks', the particles', the screen's bins — is sent by the run at its time;
  the scene's y extent is a set-up estimate, nothing from the future. The screen's P(x, y) is oriented right (fringes
  along x, the Gaussian along y: `out/c11_v11_end_default.png`, `c11_v11_end_top.png`). The only weakness is the
  power of `bohm_y` (C1-11).
* **Removal by last action** works as specified for runs that are not open (`tests/test_server.py`; C1-9 lists the
  gaps); "keep" protects a run.

## Scripts and outputs

Python scripts run in `light-funnel-viz` with `engine/` mounted read-only at `/lf` and this folder at `/rev`; browser
scripts (`.mjs`) in `mcr.microsoft.com/playwright:v1.58.2-jammy` against the reviewer's own server (127.0.0.1:8502,
`--max-workers 2 --idle-pause 20 --idle-suspend 90`, temporary runs folder; copied as `c1rev_*.mjs` next to the
scratch `node_modules`); shell scripts drive that server's container (`lf-c1rev-srv`) only. The shared server `lf-viz`
was not used; no GPU was used.

| script | checks | output |
|---|---|---|
| `c01_restore_all_messages.py` | restore vs original, every message after suspension; wall time between frames | `out/c01_restore_all_messages.txt` |
| `c01b_restore_commands.py` | `step`+`set` in one batch; planes adopted by world 2 | `out/c01b_restore_commands.txt` |
| `c02_server_races.py` | concurrent ⏺; suspension and a `set` during a rebuild; ⏺ with no free worker (02b: a REST resume, by hand with curl) | `out/c02_*.txt`, `out/c02b_*.txt` |
| `c03_player_history.mjs` | forward vs backward to the same frame (9 visualizations); ◀ / ▶ rates; GPU objects | `out/c03_*` (batch 1: v01, v04, v02; batch 2: the 3-D worlds; batch 3: v09, v11 re-run with the corrected stepping) |
| `c04_cleanup.py` | quota order, viewed runs, saving a visit, old records | `out/c04_cleanup.txt` |
| `c05_bohm_y_power.py` | power of `bohm_y` against wrong y-motions | `out/c05_bohm_y_power_*.txt` |
| `c06_checks_at_cursor.mjs` | checks shown at the cursor (v04) | `out/c06_checks_at_cursor.txt` |
| `c07_planes_in_history.mjs` | «＋ Срез» in the history and on a suspended run (v13) | `out/c07_*` |
| `c08_transport_edges.mjs` | Space on ⏺, ⏺ refused, a long rebuild seen in the page | `out/c08_transport_edges.txt` |
| `c09_partial_tail.sh` | a cut record resumed, then a restart | `out/c09_partial_tail.txt` |
| `c10_rebuild_cost.mjs` | one step back vs forward as the record grows | `out/c10_rebuild_cost*.txt` |
| `c11_v11_3d_look.mjs` | v11 in 3-D at the end and at 40 % | `out/c11_*` |
| `c12_thinning.mjs` | the player's thinning of long histories | `out/c12_thinning.txt` |
| `c13_gpu_objects.mjs` | GPU objects over 40 rebuilds | `out/c13_gpu_objects.txt` |
| `c14_failed_resume.sh` | a failed rebuild and a retry | `out/c14_failed_resume.txt` |
| `c15_catalogue_and_failed.mjs` | the failed run in the player; deleting a just-used run | `out/c15_catalogue_and_failed.txt` |
| `c16_kill_after_new_world.sh`, `c16b_restart_after_new_world.sh` | SIGKILL / graceful restart after a new world | `out/c16*.txt` |
| `c17_archived_world.mjs` | an archived world in the player | `out/c17_archived_world.txt` |

Not covered: GPU runs (the review server ran on CPU), v14 in the browser, v03/v05/v06/v07 in the browser (their restore
is covered by c01), the owner's full-size v11/v12 experiments (the costs in C1-13 are for coarse grids and short
records and will be larger), and real browsers with a GPU (SwiftShader inflates WebGL drawing, not the JavaScript of a
rebuild).

status: awaiting processing
