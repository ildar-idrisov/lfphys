# Review: checkpoints of the world's state and key frames of the player (the owner's request of 2026-10-29)

Status: **awaiting processing**

Reviewer: internal (subagent, Opus), independent of the author. Scope: the uncommitted working tree under
`engine/visualizations` against commit `39dc5d4`: `server/lfviz/checkpoint.py` (new), `server/lfviz/sim.py`,
`server/lfviz/worker.py`, `server/lfviz/runs.py`, `docker/docker-compose.yml`, `tests/test_checkpoint.py` (new),
`tests/test_server.py`, `player/js/player.js`, `player/js/env3d.js`, `player/js/scene3d.js`, `snapshot()`/`restore()` in
`v01`–`v12` `web/view.js`, and the documentation (`RULES.md` lifecycle paragraph and "The player shows the record at the
cursor", `README.md`, `engine/STATUS.md` V32). The owner's words (2026-10-29): «самое главное, чтобы сама запись
работала корректно, при воспроизведении не было пересчетов, при добавлении записи без изменения параметров, она должна
продолжаться как-будто это одна запись. для воспроизведения назад давай как в видео добавлять ключевые кадры. для
добавления записи последний кадр должен быть достаточен для полного точного воспроизведения с последнего состояния в виде
продолжения эксперимента, а не нового запуска.»

Environment: Docker image `light-funnel-viz` (Python 3.11.17, NumPy 2.4.6), `engine/` mounted read-only at `/lf`,
`LFPHYS_NO_GPU=1` except where GPU 0 is named (through the scratchpad's `gpu_run.sh`); two private servers with temporary
runs folders: port 8510 (the code as it is) and port 8511 (the same code with one file replaced for a negative control,
`neg/`); headless Chromium from `mcr.microsoft.com/playwright:v1.58.2-jammy` with SwiftShader. Scripts `c*` (Python) and
`k*` (browser / node) are in this folder, their outputs in `out/`. Other agents were editing `engine/lfphys/` during the
review (the code hashes changed between runs); the results are for the tree as it was at each run. Containers stopped and
temporary runs folders removed at the end.

**In short.** The checkpoint itself is sound: a world continued from its checkpoint in a new process emitted exactly the
original's bytes for all 14 visualizations also with live changes, actions, slice planes, `step` and `next_event` before
the checkpoint and a new world after it (c01, CPU; v08 / v11 / v12 also with every kernel on GPU 0), and through the
server's real suspend → ⏺ path the replay of the whole record and the checkpoint + tail give the same world (c04). The
findings are around it: two views are not brought back correctly through a key frame (CK-1, CK-2, reproduced), the
key-frame cap thins away the start of long sessions (CK-3), ⏺ pressed while a run is being suspended is acknowledged and
lost (CK-4, reproduced), the code hash both misses code a world runs (v12 → v11) and discards every checkpoint on any
unrelated edit (CK-5), and the tests — including the browser check the documentation cites, which is not in the
repository — do not notice regressions of the kinds found (CK-6, negative controls).

## Findings

### CK-1 (error) v09 in ordinary space: the craft's size depends on how the cursor got there

**Location.** `player/js/scene3d.js:423` `setBody` (the craft's sphere is built once, `size = S.size * 0.016`, at the
first call, and never rebuilt); `v09_thomas_3d/web/view.js:80` (render calls `setBody` every frame);
`player/js/env3d.js:182` `restore` (re-applies the key frame's box: `S.size` changes, the craft layer stays).

**Scenario.** v09 preset «Обычное пространство» (`space = lab`; here `loop = circle`, `rho = 2`): the scene's box doubles
nine times as the path is revealed (box messages, review B2-2). Record ~20 s at 10⁹ s/s, pause, open the run (the page is
opened at the end, so the craft is first built with the final box, 1984 ly), step back. Through a key frame the craft
keeps the radius it was built with; the view rebuilt from the record at the same cursor builds it with the box of that
time. At p = 0.5 % of the record: key frame radius 31.7 against 0.124 rebuilt (box 7.75: the craft drawn 256 times too
large, covering the scene); at p = 2 %, 5 %, 10 %, 20 %, 40 % the key-frame radius is each time the radius left by the
previous step (0.124 / 0.496, 0.496 / 0.992, …): never the one of the time shown. This breaks RULES' "a view must be a
function of the messages it has been fed"; the same defect was fixed in this change for v10's observer (`setObserver`
rebuilt when the box changes, `scene3d.js:497`) but not for `setBody`. The author's browser check used v09's default
(velocity space, a fixed box), where it cannot appear.

**Evidence (reproduced).** `k01_v09_body.mjs` → `out/k01_v09_body.txt`: six cursor positions, `same: false` at all six.

**Fix.** In `setBody`, rebuild the layer when `(S.size || 1) * 0.016` differs from the size it was built with (as in
`setObserver`), or size the sphere by a scale set on every call. Add v09 `lab` with a growing box to the browser check.

### CK-2 (error) A slice plane removed after a key frame comes back without its slice (empty plane, empty window)

**Location.** `player/js/env3d.js:182–204` `restore`: line 198 re-applies the key frame's objects whose latest message
differs from the present one (`last.get(key) !== m`) — the `planes` message among them —, and only those.
`scene3d.setPlanes` (`scene3d.js:735`) deletes a removed plane with its image (`P.data`), `slices.sync`
(`slices.js:60`) deletes its window; re-adding the plane makes both anew, empty.

**Scenario.** v09 (velocity space, SMALL grid): play; add plane 2 (`view plane`); move plane 1 a few times; remove plane
2 (`view remove`); move plane 1 again; pause; open; step to a time between the addition and the removal. The key frame
(taken while plane 2 existed) holds `slice:2` = S2; the present state's `last` still holds the same S2 (the removal sends
only a new `planes` message), so S2 is not applied again, while the key frame's `planes` message (with plane 2) is, and
recreates plane 2 and window 2 empty. The view rebuilt from the record at that cursor shows plane 2 with S2.

**Evidence (reproduced).** `k02_plane_removed.mjs` → `out/k02_plane_removed.txt`: via the key frame plane 2
`hasImage: false`, window 2 empty (pixel sum 14 371 632, no CSV / ✕ in its header); rebuilt: `hasImage: true`, pixel sum
48 354 861. The same in the broader scenario `k06_scenarios.mjs` (v09, p = 0.6: `P2:false` against `P2:true`, `W2`
differs) → `out/k06_scenarios_8510.txt`.

**Fix.** When the `planes` message is re-applied, re-apply every `slice:id` of the key frame for the planes it lists (not
only those whose message changed), or mark a plane/window recreated by `setPlanes`/`sync` so its slice is set again. Add
"plane removed after the key frame" to the browser check.

### CK-3 (error) The key-frame cap drops the OLDEST key frames: the start of a long session has none

**Location.** `player/js/player.js:425` (`W.keys.filter((k, j) => j % 2 === 1 || last)`), with new keys still taken every
`KEY_EVERY` (`player.js:421–424`); documented as "at most 256 key frames per world (beyond, every other one is dropped)"
(`RULES.md:216`), STATUS V32 (b) "at most 256 per world".

**Scenario.** The rule keeps the odd indices, so the first key is dropped at every overflow and the old keys halve again
at each overflow while new ones come at the full rate: the old part empties. With the rule copied verbatim (`k03`):
overflow starts at 25 600 view messages; at 72 000 messages the first key is at message 1 600; at 144 000 at 51 200 (the
first 36 % of the record has no key frame); at 300 000 at 204 800 (68 %); at 1 000 000 at 908 800 (91 %): a step back to
the middle of such a record is a rebuild from the record start, as before the change. Measured rates (k06): v02 ~30 view
messages/s, v04 ~23/s while recording — overflow after ~15–20 min, the first third without key frames after ~1.5 h (the
playground mode's long sessions are the stated target of V32 (b)). C1-12 found and fixed the same pattern for the
frames.

**Evidence (reproduced in simulation of the exact rule).** `k03_key_thinning.mjs` → `out/k03_key_thinning.txt`.

**Fix.** Thin uniformly, as the frames do since C1-12: keep a per-world stride; on overflow double it and keep the keys
whose message index is a multiple of `KEY_EVERY · stride`, and take new keys only on that grid. Correct RULES and STATUS.

### CK-4 (should-fix) ⏺ pressed while a run is being suspended is answered «ok» and lost

**Location.** `server/lfviz/runs.py:323` `command_resuming` (forwards to the worker while `running` is still true),
`runs.py:304` `command` (writes to a stdin that `_stop` has already closed: asyncio drops it silently), `runs.py:397`
`_stop` (holds the run's lock until the worker process exits; with `checkpoint: true` the worker now writes its state
before exiting, so the window is the checkpoint's time, up to the new 60 s wait).

**Scenario.** A run is being suspended (POST `/stop`, `_make_room` for another run, the idle suspension, server
shutdown) and ⏺ (`play`) arrives within the time the worker needs to write its checkpoint and exit. The reply is
`{"ok": true}`, nothing happens, the run ends «приостановлен»; the experimenter must press ⏺ again. With v07 (checkpoint
~10 ms) the window was ~0.1 s; with v08 / v11 at default parameters the write alone takes 0.5–0.8 s (CK-12).
Related risk (code reading, NOT reproduced): `_stop` returns after `proc.wait()` without awaiting the reader task
(`run._reader`, `read_worker`), which may still be ingesting the worker's last messages (the suspension's checkpoint,
`end`); a `resume` waiting on the lock would then read `_latest_world` without that checkpoint, open a new record file
handle, and the old reader's tail (`read_worker`: `self.file.close()`, `meta["state"] = "suspended"`) would close the
new handle and overwrite the new worker's state.

**Evidence (reproduced).** `c05_suspend_resume_race.py` on the private server → `out/c05_suspend_resume_race.txt`: 36
rounds of [suspend, ⏺ after 0–0.2 s]: ⏺ lost in 28 (every round with delay ≤ 0.05 s, 3 of 4 at 0.08 s, 1 of 4 at
0.12 s, none at 0.2 s); in the 8 rounds where the resume happened it continued correctly from the suspension's checkpoint
(no wrongly resumed round: the reader race above did not show).

**Fix.** Mark a run as stopping in `_stop`; `command_resuming` on a stopping run awaits the run's lock and then resumes
(or `command` raises when `proc.stdin.is_closing()`, answered 409 "запуск приостанавливается — ⏺ ещё раз"). In `_stop`,
after `proc.wait()`, `await self._reader` before releasing the lock, so the record, `self.file` and the meta are final.

### CK-5 (should-fix) The code hash both misses code a world runs and discards every checkpoint on any edit

**Location.** `server/lfviz/registry.py:46` `code_hash` (the visualization's folder `*.py` + `*.js`, `server/lfviz`,
all of `lfphys`), used by `runs.py:369` to accept a checkpoint; `checkpoint.py:43–51, 86–90` (closures pickled as
`marshal`led bytecode); `RULES.md:185` ("the code changed since — any file of the visualization, the server or the
engine").

**Scenarios.** (a) v12 imports v11 (`v12_arrival_times_2d/viz.py:44`: `from v11_double_slit_2d import viz as V11`);
v11's folder is not in v12's hash: an edit of v11 leaves v12's checkpoints "of the same code", and a v12 run resumes from
objects pickled under the old v11 code into the new one (an attribute added in `__init__` and used in `advance` → the
resumed run fails at its first frame, after the load succeeded, so the replay fallback is not taken). Reproduced: with
`v11_double_slit_2d/viz.py` edited (mounted copy, `neg/v11_viz_edited.py`) v11's hash changes, v12's stays
`076f254c81d1` (`out/c06_code_hash_v12_v11.txt`). (b) The interpreter and the libraries are not in the hash, while
closures travel as bytecode: v03 (`Simulation._build.<locals>.<lambda>`, `step_fn`), v08 (`rect_spectrum.<locals>.<lambda>`
from lfphys) and v13 (`hydrogen.orbital.<locals>.<lambda>`) take that route (`c03`, "special"). The image follows
`python:3.11-slim` (minor version pinned, patch floating): a later base or `requirements.lock` change keeps the hash and
loads 3.11 bytecode / old library pickles into the new interpreter, which `marshal` does not check. (c) The other way:
any edit of any `lfphys` module (also one the world does not import) or of the view's JS changes the hash and every
checkpoint of every run of that visualization is refused: the resume recomputes the whole record — exactly what the
owner asked to stop. The hashed code changed in 1–4 commits a day this week (git log), plus the uncommitted edits other
agents make during the day.

**Fix.** At checkpoint time record what the world actually runs: the files of the modules loaded in the worker
(`sys.modules[*].__file__` under the engine and the visualizations, so v12 → v11 is included and unrelated modules and
JS are not) with their hash, plus `sys.version_info`, `importlib.util.MAGIC_NUMBER` and the NumPy / SciPy / CuPy
versions; at load, compare those. Correct RULES.md:185.

### CK-6 (should-fix) The tests would not notice regressions of the kinds found; the browser check is not in the repository

**Location.** `tests/test_checkpoint.py` (only plain play before and after the checkpoint, one tail test with one live
change, no new world, no `step` / `next_event`, no view requests, CPU only); the browser check RULES.md:221 and STATUS V32
(b) cite ("tested in the browser for every visualization") is `scratchpad/pw/keyframes.mjs`, outside the project (copied
here verbatim as `dev_keyframes.mjs`, only the output path changed): it plays 25 s with no live change, action, plane
change or box growth, and compares canvases, the 3-D layers' geometry and panel texts — not plane images, slice windows,
sphere radii or volume textures.

**Negative controls (reproduced).** (1) `checkpoint_state` without the world number (`"world": 1`,
`neg/sim_checkpoint_world_always_1.py` mounted over `sim.py`): `tests/test_checkpoint.py` + `tests/test_server.py` →
39 passed (`out/neg_world_always_1_tests.txt`); in use, a run resumed from a checkpoint of world n ≥ 2 would number its
next new world 2 again. (2) v04's `restore()` without its live values (`neg/v04_view_restore_without_liveVals.js` on the
private server 8511): the author's browser check reports `same: true` at all five cursors on both servers
(`out/dev_keyframes_out_8510.txt`, `out/dev_keyframes_out_8511.txt`); `k05_live_change_control.mjs` (a live change of the
time units mid-record, then a step back) reports the clock panel in GM/c³ through the key frame against ms rebuilt on
8511, and equality on 8510 (`out/k05_live_change_control.txt`). CK-1 and CK-2 also pass the author's check.

**Fix.** Put the browser check into the repository (e.g. `player/js/tests/keyframes.mjs`, documented with its command)
with the scenarios of `k06_scenarios.mjs` (live changes and actions mid-record, planes added / moved / removed, the page
opened at the end, v09 `lab` with a growing box) and the richer fingerprint (plane images, windows' pixels, sphere radii).
Extend `test_checkpoint.py` with `c01`'s scenario (set / action / view / step / next_event before the checkpoint, a new
world after it, the header's `world` compared) for every visualization.

### CK-7 (nit) Documentation against the code

- `sim.py:31` and `sim.py:142` name `checkpoint.EVERY` / `lfviz.checkpoint.EVERY`: there is no such name; the constant is
  `sim.CHECKPOINT_EVERY` (as `checkpoint.py:15` says).
- `RULES.md:216`, STATUS V32 (b): "every other one is dropped" — the oldest are dropped (CK-3).
- `RULES.md:217`: v07 is the only view named whose `restore` throws; v11 and v12 also refuse every key frame from before
  their first live set-up change (`v11_double_slit_2d/web/view.js` restore: "the set-up was changed after this key
  frame"), and env3d refuses a target set / a slice computed after a key frame; each refusal writes a `console.error`
  (k06: v11, v12) and falls back to the rebuild. README's «Назад по истории плеер идёт от ближайшего ключевого кадра»
  does not say that v13, v14, v07 after its cap and these cases rebuild from the start.
- `RULES.md:185`: "any file of the visualization, the server or the engine" (CK-5 a, b).
- `RULES.md:221`, STATUS V32 (b) "tested in the browser for every visualization": the check is not in the repository
  (CK-6), and CK-1 / CK-2 fail it in scenarios it does not cover; v01 cannot be compared by canvas in any scenario that
  rebuilds (its diagram is fitted again, V32 (f): in k06 v01 differs also between a forward feed and a rebuild).
- `RULES.md:184` "also on GPU 0": the test does not select the GPU; c01 confirms the claim for v08, v11, v12 with every
  kernel on GPU 0 — say how it was run.

### CK-8 (nit) A failed checkpoint disables checkpoints for the rest of the world; its temporary file stays

**Location.** `sim.py:396, 404` (`ckpt_failed = self.world`: never retried for that world), `checkpoint.py:126–139`
(`.tmp` written, not removed on failure), `runs.py:143` `disk_size` (counts `*.pkl` only).

**Scenario.** A transient I/O error (a full disk for a moment, a quota) during one periodic checkpoint: no further
checkpoint for that world, including at suspension; every later resume loads an older checkpoint and repeats the whole
tail, or replays from the start. A write killed mid-way (the 60 s timeout, a container killed) leaves `w<n>-<ns>.tmp`
(up to ~100 MB for v08) that is never removed and not counted in the run's size or the quota.

**Fix.** Treat only pickling errors as permanent; retry I/O errors at the next trigger; unlink the `.tmp` on failure and
count / clean `*.tmp` in `disk_size` and at start.

### CK-9 (nit) `ckpt_dirty` misses `next_event` at the current instant; a dead term in `restore_from`

**Location.** `sim.py:256–266` (`next_event` with `te <= t` calls `self.sim.advance(self.sim.t)` directly: no
`ckpt_dirty`), `sim.py:431` (`t_end > self.sim.t` evaluated after `_advance(t_end)`: always false).

**Scenario (code reading, not reproduced).** Paused right after a checkpoint (pause or suspension), the experimenter
presses «⏭ событие» on an event at the current instant and the suspension's `stop` arrives in the same batch: the world
revealed the event (it is in the record) but no checkpoint is written (not dirty), and no frame follows; the resume loads
the earlier state and reveals the event again (twice in the record).

**Fix.** Set `ckpt_dirty` for every handled command except `play`, `pause`, `speed`; compute `restore_from`'s flag
before the advance.

### CK-10 (nit) The checkpoint's file name is taken from the record unchecked and loaded by an unrestricted unpickler

**Location.** `runs.py:369` (`self.ckpt_dir / str(m.get("file"))`: an absolute name or `../` leaves the run's folder),
`worker.py:108`, `checkpoint.py:94–102` (no `find_class` restriction); `checkpoint.py:20` says "nothing else is ever
loaded".

**Scenario.** Anything that can put a line into a record (today only the worker's own messages) chooses which file the
worker unpickles, i.e. which code it runs. Low risk now; the docstring overstates it.

**Fix.** Accept only `^w\d+-\d+\.pkl$` names inside `ckpt_dir` (resolve and check the parent).

### CK-11 (nit) What the record and the passport say about a resume can differ from what happened

**Location.** `runs.py:588–589` (`resumes[-1]["from"] = "checkpoint"` whenever the server chose a checkpoint, also when
the worker failed to load it and replayed — `worker.py:113–116`), `sim.py:423` (`restore_from` replaces this worker's
`backend_notes`, from this start's `configure`, by the checkpoint's).

**Scenario.** A checkpoint that does not load (another GPU state, a missing module): the passport says "checkpoint", the
record says «Сохранённое состояние не загрузилось … пересчитывается». A run resumed after the GPU became unavailable keeps
the old notes, so the next new world's header does not say «GPU выбран, но недоступен → CPU».

**Fix.** Set `from` from the worker's own report (its notice, or a `restored` message with `how`); keep the current
worker's `backend_notes`.

### CK-12 (nit) Checkpoints are written synchronously in the frame loop

**Location.** `sim.py:484–485` (periodic), `sim.py:244–245` (pause), `checkpoint.py:126` (`fsync`).

**Measured** (`c03`, default parameters, written to a folder on the same HDD as `runs/`): v08 99.5 MB (pickle 45 ms,
write + fsync 797 ms, load 102 ms), v11 72.7 MB (38 / 535 / 57 ms), v12 32.1 MB (13 / 266 / 30 ms), v13 / v14 8.0 MB
(~0.1–0.2 s); the rest < 4 MB. So a recording of v08 / v11 stalls ~0.5–0.8 s every 2 min (and at a pause), and keeps up
to 200 MB per v08 run (two files) against the 5 GB quota.

**Fix.** Pickle in the loop (tens of ms) and write + fsync the bytes in a background thread (emit the `checkpoint`
message when the file is in place; the next stop waits for a pending write).

### CK-13 (nit) env3d's restore applies changed objects in the key frame map's order, not in the record's order

**Location.** `env3d.js:198` (iteration over `k.last`, a `Map` ordered by each key's FIRST message).

**Scenario (latent, code reading).** Objects sized by the scene's box at the moment they are applied (`setMarks`,
`setArrow`, labels, points: `S.size`) and re-applied before a changed `box` is re-applied get the present box's size,
while the rebuild gives them the box of their time. No current world re-sends such an object after a box change (v09 lab
sends its arrow once, v10's meshes are not box-sized), so it does not show today.

**Fix.** Re-apply `box` first, or re-apply the changed objects sorted by their message's index in the record.

### CK-14 (nit) v08's view writes into the header object the player keeps; its restore does too

**Location.** `v08_wave_3d/web/view.js:57` (onMessage) and `:52` (restore): `H.modelling = …` where `H` is the header
the player passes (`W.header`); RULES: a view rebuilt at an earlier time starts "from the header as recorded" (the same
reason `setScene` now copies its description).

**Scenario.** A rebuild from the record starts from the modelling of a LATER time (whatever was written last). v08's world
time stays at 0, so no history shows it today; a time-dependent slices world built on this view would.

**Fix.** Keep the modelling in a view variable (header value as its initial value), snapshot / restore that.

### CK-15 (nit) Pickling separates arrays that share memory

**Location.** `checkpoint.py` (plain pickling of NumPy arrays).

**Observation.** `c02`: in v11 and v12, `sim.W` and `sim.prop.H.W` (and `W_c` / `W_d` with the companion's and the
detector's) share memory in the running world and are separate arrays after a checkpoint is loaded. Nothing writes into
them in place today (`c01`: continuation identical), but a world that wrote into one and read the other would continue
silently differently after a resume; the loaded state also holds those arrays twice.

**Fix.** State the rule in RULES ("a world must not rely on two attributes viewing one buffer") and add `c02` as a test
that fails on such sharing.

## Checked, without a finding

- **The checkpoint's completeness and exactness** (`c01_checkpoint_scenarios.py`, one process per visualization,
  `c01_run_each.sh`): for all 14, set / action / view (planes) / `step` / `next_event` before the checkpoint and the same
  plus a new world after it, irregular frame steps, compared byte for byte with the uninterrupted world in two fresh
  processes: identical for all 14 (`out/c01_checkpoint_scenarios.txt`); on GPU 0 with every kernel on the GPU for v08,
  v11, v12: identical (`out/c01_checkpoint_scenarios_gpu.txt`). In ONE process running several visualizations the new
  world's header differed in `backend.used` (`lfphys.core.backend._USED` is per process,
  `out/c01_checkpoint_scenarios_one_process.txt`); within one visualization's worker the kernels recorded do not change after the world's
  header (`c07_backend_used.py` → `out/c07_backend_used.txt`: v08–v12 the same after 40 frames), so no difference
  arises there.
- **The server's path** (`c04_server_resume.py`, v02, v05, v07, v04): live change, two steps (the second sent together
  with the suspension: a checkpoint in the middle of a batch), suspend, ⏺, record, suspend: resumed «с сохранённого
  состояния»; offline, the world replayed from the whole record and the world loaded from the last checkpoint plus the
  record after it emit identical bytes in the same steps (`out/c04_server_resume.txt`): the record holds what the
  checkpointed world went through, so the replay fallback continues the same world.
- **Stale checkpoints and crashes**: only checkpoints after the latest header are considered (`runs.py:337–375`), the
  file is written atomically, the two newest are kept; module-level caches in `lfphys` are pure (`lru_cache` of weights);
  no world uses a global random generator.
- **The player's key-frame logic** (`player.js:381–447`): the `prefix` / `nOn` / `maxOn` bookkeeping keeps key frames
  correct when messages arrive out of time order; world switches and reconnection rebuild (`viewOwner`). In `k06`
  (live changes or actions mid-record, the page opened at the end) v02, v03, v04, v05, v10, v11, v12 were equal through
  key frames at every cursor; v07's two differences did not repeat in a control (`k07_v07_probe.mjs`: key frame, rebuild
  and a second rebuild equal at the same cursors), so they were screenshot timing, not the key frames.
- **The key frames' memory** (track colours copied per key frame, `scene3d.snapshotAppends`): v11 / v12 records are
  short (k06: ~130 view messages, a key frame or two at the default spacing); `k04` was inconclusive (its runs were
  paused by the server after 60 s without viewers).

## Scripts and outputs

| script | what | output |
|---|---|---|
| `c01_checkpoint_scenarios.py`, `c01_run_each.sh` | checkpoint continuation vs uninterrupted, richer scenario, all 14; `LF_GPU=1` on GPU 0 | `out/c01_*` |
| `c02_aliasing.py` | arrays sharing memory before / after a checkpoint | `out/c02_aliasing.*` |
| `c03_checkpoint_cost.py` | checkpoint size, pickle / write+fsync / load time at default parameters; special pickling routes | `out/c03_checkpoint_cost.*` |
| `c04_server_resume.py` | server suspend → ⏺ → suspend; replay vs checkpoint + tail offline | `out/c04_server_resume.*` |
| `c05_suspend_resume_race.py` | ⏺ during a suspension (CK-4) | `out/c05_suspend_resume_race.*` |
| (inline command: `registry.code_hash` with `neg/v11_viz_edited.py` mounted over v11's `viz.py`) | v12's code hash with v11 edited (CK-5 a) | `out/c06_code_hash_v12_v11.txt` |
| `c07_backend_used.py` | `lfphys.core.backend`'s per-process record of kernels during a world | `out/c07_backend_used.txt` |
| `k_common.mjs` | helpers of the browser checks | — |
| `k01_v09_body.mjs` | CK-1 | `out/k01_v09_body.txt` |
| `k02_plane_removed.mjs` | CK-2 | `out/k02_plane_removed.txt` |
| `k03_key_thinning.mjs` | CK-3 (node, the rule verbatim) | `out/k03_key_thinning.txt` |
| `k04_key_memory.mjs` | key frames' memory (inconclusive) | `out/k04_key_memory_v11_double_slit_2d.txt` |
| `k05_live_change_control.mjs`, `dev_keyframes.mjs`, `neg/v04_view_restore_without_liveVals.js` | CK-6 negative control (browser) | `out/k05_*`, `out/dev_keyframes_out_*` |
| `neg/sim_checkpoint_world_always_1.py` | CK-6 negative control (pytest) | `out/neg_world_always_1_tests.txt` |
| `k06_scenarios.mjs` | the author's comparison with live changes, planes, page opened at the end, richer fingerprint | `out/k06_*` |
| `k07_v07_probe.mjs` | control for v07's k06 differences | `out/k07_v07_probe.txt` |
| `out/00_test_checkpoint_baseline.txt` | `tests/test_checkpoint.py` as shipped: 18 passed | — |

Commands: Python checks `docker run --rm --name lf-rev-<x> -v <engine>:/lf:ro -v <this folder>/out:/out -e
LFPHYS_NO_GPU=1 -w /lf/visualizations light-funnel-viz python3 /lf/reviews/<this folder>/<script>` (c04 / c05 also
`--network host -v <private runs dir>:/runs:ro` and the private server's port); browser checks `docker run --rm --init
--shm-size=2g --network host -v <playwright node_modules>:/pw/node_modules:ro -v <this folder>:/pw/rev -w /pw/rev
mcr.microsoft.com/playwright:v1.58.2-jammy node <script> <port>` against a private server started as in the task
(`… -p 8510:8479 light-funnel-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 3`; for 8511 with
`neg/v04_view_restore_without_liveVals.js` mounted over `v04_orbits/web/view.js`).

## Summary

| ID | severity | reproduced | one line |
|---|---|---|---|
| CK-1 | error | yes (k01) | v09 lab: the craft's size through a key frame is the size it was first built with |
| CK-2 | error | yes (k02, k06) | a plane removed after a key frame comes back with no slice and an empty window |
| CK-3 | error | yes (k03, the exact rule) | the key-frame cap drops the oldest keys: long sessions lose key frames from the start |
| CK-4 | should-fix | yes (c05, 28 of 36); reader race not reproduced | ⏺ during a suspension is answered ok and lost |
| CK-5 | should-fix | (a) yes (hash); (b), (c) code reading + c03 | the code hash misses v12 → v11 and the interpreter, and drops every checkpoint on any edit |
| CK-6 | should-fix | yes (two negative controls) | tests and the (unversioned) browser check miss the regressions found |
| CK-7 | nit | — | documentation against the code |
| CK-8 | nit | code reading | a failed checkpoint is never retried; `.tmp` files stay, uncounted |
| CK-9 | nit | code reading | `next_event` at the current instant does not mark the state changed |
| CK-10 | nit | code reading | checkpoint file name from the record unchecked, unrestricted unpickler |
| CK-11 | nit | code reading | passport's `from` and the backend notes after a resume |
| CK-12 | nit | measured (c03) | synchronous 0.3–0.8 s writes in the frame loop for v08 / v11 / v12 |
| CK-13 | nit | code reading (latent) | env3d re-applies changed objects out of record order |
| CK-14 | nit | code reading | v08's view writes into the player's header |
| CK-15 | nit | c02 (harmless today) | pickling separates arrays that share memory (v11, v12) |
