# Visualizations of the consequences of hypotheses: rules, folder contract and the one API

This file applies to every visualization in `visualizations/` and to every agent that builds or changes one.
Owner guide: `README.md` (English) and `README.ru.md` (Russian). Rules for the whole of `engine/`: `../AGENTS.md` (§3
points here). This file and the other developer texts are in English; the interface and the user documents exist in
every language of `../LANGUAGES.md` (§7).

## 0. The owner's directions (verbatim, 2026-10-22)

> создай отдельную папку с визуализациями для отображения следствий по гипотезам, пропиши это в инструкциях. в ней по
> моему запросу должна создаваться подпапка и делаться визуализация в виде плеера как в проекте
> [путь к другому проекту владельца — опущен при публикации, 2026-11-12]
> с одним общим сервером для запуска разных визуализаций и вещанием в локальной сети, чтобы я мог зайти на отдельный
> порт со своего ноубтука [адрес в локальной сети]:port, выбрать одну из визуализаций и в интерактивном режиме поиграться с ней.
> плеер и сервер один в докере и единым api для всего проекта
>
> все визуализации поднимаются по запросу с браузера мною. все визуализации должны быть точно выверены и согласованы с
> общепринятой физикой, допускается только вносить изменение для исследования какого-то эффекта, например если я получил
> новое доказательство и хочу его проверить или я хочу намеренно изменить какое-нибудь известное правило/закон, чтобы
> посмотреть как все будет работать без него.
> все визуализации должны отображать результат из расчетов текущего запуска, а не из известного факта, т.е. если свет
> формирует дифракционную решетку, то она должна рисоваться как следствие запуска, а не просто появляться, потому что
> это известный факт, т.е. визуализации должны иметь четкие прифинно-следственные связи в запуске.

## 1. Folder contract

```
visualizations/
  README.md              owner guide (English; README.ru.md: Russian): start, open from the laptop, use the player
  RULES.md               this file
  locales/               the framework's catalogues (server, player, catalogue, instruments): <lang>.json (§7)
  docker/                Dockerfile, docker-compose.yml, requirements.lock (pinned)
  server/                serve.py + package lfviz (protocol, params, runner, worker, run manager, HTTP/WS API; the
                         slice planes of 3-D worlds: lfviz/planes3d.py)
  player/                the one player: catalogue (index.html), run page (run.html), shared JS/CSS, the 3-D
                         environment (js/env3d.js over js/scene3d.js and js/slices.js; the camera window
                         js/imagewin.js); vendor/: third-party modules, unmodified (three.js r185.1, MIT;
                         vendor/README.md)
  tests/                 server/API tests and the test harness
  runs/                  run records (git-ignored; limits: keep days, quota; "keep" protects a record)
  pNN_<slug>/            ONE FOLDER PER PLAYGROUND SECTION (plan P15; §6): the same files, VIZ["kind"] = "playground"
  vNN_<slug>/            ONE FOLDER PER VISUALIZATION, created on the owner's request
    __init__.py
    viz.py               VIZ = {id, title, summary, purpose, version, schema, simulation}
    engine/              the apparatus logic over lfphys (Python), no drawing; physics itself lives in ../lfphys
    web/view.js          the drawing (ES module, createView(ctx)), no physics
    tests/               physics tests: every route against a closed form or a second method
    locales/             the world's catalogues: <lang>.json, msgid -> translation (§7)
    README.md            the model in full: equations, what is computed, checks, approximations, sources
    README.<lang>.md     the same in every other language of ../LANGUAGES.md (README.ru.md)
```

A new visualization is a new `vNN_<slug>/` folder; the server and the player pick it up without changes
(`registry.py` discovers folders, the catalogue lists them, the run page loads `web/view.js`).

**The physics engine.** Since 2026-10-23 the physics of all visualizations lives in one library, `../lfphys/`
(owner: «выделяй в отдельную библиотеку движок для физики … а отдельная симуляции или визуализации должна быть
оберткой над этим движком»). Its core holds established physics only; approximations, interpretations, models and
alternatives are separate layers (`../lfphys/LAYERS.md`, `../lfphys/README.md`). A visualization is a wrapper: its
`engine/` keeps the apparatus and the orchestration, imports the physics from `lfphys`, and lists the modules a world
uses in `Simulation.engine_modules()`; the player shows them with their layer. Physics a visualization needs and the
engine lacks is added to the engine, with its tests, not to the visualization.

## 2. Physics rules (owner's directions made operational)

1. **Computed in the run, never drawn from a known result.** Every visible consequence (a wavefront, a delay, an
   interference pattern, a clock reading, a measured speed) is the output of the run's own computation from its
   inputs. Closed-form results of the known theory may appear only as **references in the checks panel**, next to
   the computed value, never in place of it.
2. **Causality inside the run.** The world advances in simulation time. A consequence is revealed to the viewer only
   when the run's time reaches it. An action changes the world at the current event; pending (future) consequences
   that depended on what was changed are withdrawn and recomputed; the past is never rewritten.
3. **Accepted physics by default.** Every law parameter has a `standard` value (`params.Param.standard`). A run whose
   world parameters differ is flagged "modified physics" in its header, record and the player's top bar, with the
   list of modifications. Modifications exist only as explicit, named law parameters (for example: ether or
   ballistic kinematics, Newtonian corpuscles, the Born-rule exponent, a collapse model). A hidden fudge is forbidden.
4. **World parameters, live parameters, actions** (owner, 2026-10-23: "если я вношу изменение, то оно сразу
   применяется и меняет поведение, как в жизни. если часть параметров менять нельзя во время запуска, то их оставляем
   в стартовых настройках. при создании нового мира в уже запущенном, нужно создавать в рамках текущего запуска").
   * World parameters (`Param`, `live=False`): laws, constants, fixed fields and initial conditions that nothing
     inside the world can change. They are fixed for a world; changing them starts a NEW WORLD inside the same run
     (command `new_world`), because a history computed under different laws is a different history. The previous
     worlds stay in the run's record.
   * Live parameters (`Param`, `live=True`): the set-up an experimenter can change while the world runs (source,
     slits, screen, observer, elements). A change applies at once, at the current moment (command `set`), without an
     "apply" button; consequences propagate from that event, particles or signals already under way are treated
     causally (they fly on, or are lost when the path they need is rebuilt, and this is counted). A refused change
     leaves the world as it was and the player rolls the control back. In a playground the laws the engine can
     change at the current moment are live parameters too (§6). A demonstration's state that an experimenter can prepare
     (v13, v14: an ideal preparation at the current moment, the former state discarded) is live in the same way; a law
     or a system that no operation changes (the atom, the quark pair) stays a world parameter.
   * Actions: one-off events done by an agent (boost an observer, emit a flash, start a measurement), applied at the
     current event. An action that sets a state continuously (the speed of an observer) is declared `mode: "live"`
     and applies on each committed value.
5. **Checks are part of the visualization.** Each visualization emits `check` messages: a computed value, its
   reference (closed form of accepted physics or of the declared modification), the relative difference and the
   tolerance the numerics justify (or an explicit `ok`). A computed value without a closed form is shown with
   reference "—". A check that fails is shown failed, never hidden.
6. **Approximations are stated.** Every approximation (paraxial optics, a 2-D geometry, a local frame, a boundary
   condition) is named in the visualization's README, and where it can fail the run says so (a failing check or a
   notice). An approximation a world chooses (e.g. a reduced 2-D model of one slice; owner, 2026-10-24: «помечать
   там, где это приближение») is listed in the header's `approximations` (one line each); the run list, the passport
   and the top bar show it like a modification. Numerical errors (grid, window) are measured by the run and shown in
   its checks.
7. **Tests before use.** Each route of the engine is tested against a closed form or an independent second method
   (`vNN_*/tests/`), all tests pass in the Docker image before the visualization is reported, and a physics review
   by a different agent is processed under `../reviews/README.md`.
8. **Reproducible runs.** A run records its parameters, seed, code hash, every command with wall time, and every
   message it emitted (`runs/<id>/stream.lfrec`, `meta.json`). Randomness comes only from the run's seeded generator.
9. **Numbers and sources.** Constants come from `scipy.constants` (CODATA) or named nominal values (IAU). Presets
   that imitate published experiments are labelled "illustrative" unless their numbers were checked against the
   source text (`../AGENTS.md` §3 rule 11).

10. **3-D worlds: the 3-D scene is the view, slices are planes in it** (owner, 2026-10-27, verbatim in
    `../AGENTS.md` §1). A world modelled in 3-D shows the whole scene in 3-D (the apparatus, e.g. a screen with its
    slits, the beams, the target; the computed fields: a volume, vector glyphs of currents or forces) through the
    shared environment `player/js/scene3d.js` + `player/js/slices.js`:
    * **every element can be switched off on its own** (a layer per object and field), so that the rest stays
      visible;
    * **slices are planes placed in the scene at any orientation**, up to three, each with its own window next to the
      3-D view and its own colour; selecting or pointing at a window highlights its plane; a plane is moved along its
      normal and tilted by hand (a gizmo with only these handles, keys W / E) and by parameters (centre; normal by its
      two angles; presets); a new plane is placed through the middle of the region, perpendicular to those already
      there (turned ones included); a plane is fixed by its normal and its distance, its centre is its point closest
      to the region's centre;
    * **slices stay where they are put**: nothing moves a plane but the experimenter, and a new world of the run keeps
      them (`Simulation.view_state` / `adopt_view`); moving a plane by itself (e.g. along its normal while world time
      runs) is an option per plane, off by default, with coarse, rate-limited slices while it moves (the record's
      size) and the full slice when it stops; this holds for every visualization;
    * the windows' axes are physical coordinates (or the distance from the plane's centre along a stated direction),
      and one log-scale floor serves the windows and the 3-D scene;
    * what a plane shows is computed by the run for that plane (view command `view`, §3), never interpolated by the
      player; a preview while a plane is dragged (from a volume already computed) is labelled as a preview;
    * each slice states how it was computed and, where the physics has an independent reference, is checked against
      it at points of the plane.
    Every 3-D world uses the shared parts, not its own copies (B2, 2026-10-27): on the server
    `server/lfviz/planes3d.py` (`SlicePlanes`: the planes, the view command, keeping them in a new world, "auto"),
    in the player `player/js/env3d.js` (the scene and the windows side by side, the panels "Scene layers" and "Slice:
    position and tilt", "＋ Slice", previews, the 3-D messages) and, for a world that computes what an observer sees,
    the camera window `player/js/imagewin.js` (B3, v10). A world adds only its own objects, panels and checks.
    A **2-D world** whose plane is the exact reduction of a 3-D set-up (B3: v11, slits long along y) uses the same
    environment: the apparatus in 3-D, the computed field on its plane as a `panel` in the scene, the plane's own
    window (fixed: its plane is the world's, not the experimenter's, `planes.max = 0`), the computed paths in both.
    **The rendering contract of the 3-D view** (review UX-3d, 2026-11-04; `player/js/scene3d.js`):
    * *depth for volumes and planes*: everything opaque (solids, lines, slice planes) writes depth; the volume's ray
      march ends at the depth of the opaque scene and is split at the nearest translucent surface, so that a cloud in
      front of an object covers it and a cloud behind it is hidden; slice planes are opaque; translucent surfaces show
      their nearest layer and are drawn far to near by their nearest point;
    * *lit materials*: solids (spheres, arrows, glyphs, bodies, meshes of the run) are lit by a light that moves with
      the camera, spheres are exact, lines have a width in pixels, particles are round; data surfaces (slices, panels,
      targets, camera images) are not lit — their colour is the value;
    * *views by "up"*: the view buttons are built from the world's `up` (U up, R right, F toward the viewer); a view
      along `up` keeps the slice window's axes; a 2-D world declares its plane (`createEnv3D(ctx, {plane2d})`) and opens
      looking at it from above;
    * *fit after layout*: a view fits the corners of the region and the apparatus inside the canvas, again on every
      resize and box change until the experimenter moves the camera; after that only the experimenter moves it (a
      wider or repeated `box`, a step back in the history: the camera stays, a notice offers F);
    * labels have a size in pixels and are hidden behind solids; the frame's labels stand on the box's outer edges;
    * the volume's density is the optical depth τ of its densest line of sight along an axis of the region (the same
      meaning in every world); while the camera moves the volume is drawn at half the pixels and fewer steps.
    `visualizations/tests/browser/scene3d_checks.mjs` checks this contract in a browser.

## 3. The one API

Server: `server/serve.py` (aiohttp), port 8479, one process for all visualizations; each run is a separate worker
process (`python -m lfviz.worker --viz <id>`) speaking length-prefixed binary messages over stdin/stdout.

REST (JSON):

| method | path | meaning |
|---|---|---|
| GET | `/api/health` | version, visualizations, running workers |
| GET | `/api/viz`, `/api/viz/{viz}` | catalogue: id, title, summary, purpose, version, schema (params + presets) |
| GET | `/api/runs` | runs, newest first: state, sim time, size, keep, modifications, approximations, `devices_override` |
| POST | `/api/runs` | `{viz, preset?, params?, seed?, label?, backend?}` → `{id}`: starts a run (its first world); `backend` = `{kernels: {name: {device, precision}}}` overrides the device settings for this run only (§5) |
| GET | `/api/runs/{id}` | the run's passport: current params and seed, `worlds` (each: n, preset, seed, params, modifications), code hash, commands, errors |
| POST | `/api/runs/{id}/command` | `{cmd, args}` (same as over WebSocket); a suspended run is resumed first by a command that computes or changes the world (`play`, `step`, `next_event`, `set`, `action`, `view`, `scene`, `new_world`); the server's own worker commands (`checkpoint_now`, `stop`) are refused, 403, here and over the WebSocket (review LB1-framework F6); a body that is not `{cmd, args}` is 400 |
| POST | `/api/runs/{id}/record` | a playground's record window (§6): `{on?: bool, window_s?: number, window_mb?: number}`; `on` absent leaves recording as it is; 400 for anything else; 409 for a demonstration |
| POST | `/api/runs/{id}/resume` | rebuild a suspended run's world from its record and let it compute (see below) |
| POST | `/api/runs/{id}/cancel` | cancel the command the worker is computing now: the worker is ended, nothing of the command is recorded (it is announced by `busy` and written only when done), and the run is resumed from its record — the world as just before the command; 409 when nothing is being computed |
| POST | `/api/runs/{id}/stop`, `/keep` | release the worker (the run is "suspended", resumable; not in the player); keep `{keep: bool}` |
| DELETE | `/api/runs/{id}` | delete a run that no tab has open, with its record (one still computing is suspended first) |
| GET | `/api/runs/{id}/stream` | the raw record (`.lfrec`) |
| GET | `/api/runs/{id}/series?ids=a,b[&from=t0][&to=t1][&world=n][&format=csv][&max_points=k]` | the recorded values of a world's measurables (`lfviz.instruments`), the latest world or world n, the frames with t0 ≤ t ≤ t1; an id named twice counts once. JSON `{run, world, worlds, t_unit, ids, measurables (with title), t, values, n_frames, n, stride, cap, notes}`: at most `max_points` rows (default 5000, ≤ 50 000), every stride-th frame and the last. CSV: streamed, each batch read and formatted in a thread; one header line `t, <unit>` then `<label>, <unit> [<id>]`; an undefined value is an empty cell; every frame up to 2·10⁶ rows and 2·10⁷ cells, beyond them a stride named in the time column's header |
| POST | `/api/runs/{id}/sweep` | a parameter sweep from the current moment (`lfviz.sweep`, §6 «Instruments»): `{target {kind: law, id} \| {kind: object, obj, param}, values (≤ 50), duration, measure, stat final \| mean_last \| max \| min, window?, n_samples? (200, ≤ 2000), estimate?}` → `{n, state, estimate, base, labels}`; `estimate: true` only estimates; an object's parameter is checked against the palette in the world's header (review LB1-p02-ux X1), the measure against what the world measures now; 400 `{error, hint, estimate?}` when refused or above the budget; 409 when the run already has a sweep, two run on the server, the world gave no state, or the sweep's memory does not fit |
| GET | `/api/runs/{id}/sweeps`, `/api/runs/{id}/sweeps/{n}[?format=csv]` | the run's sweeps; one sweep's state and results; its table as CSV, three «#» lines first (the sweep, the base moment and its source, the duration, the readings and their spacing, the sampler; then the same as `key=value`) |
| POST | `/api/runs/{id}/sweeps/{n}/cancel` | stop a running sweep, what it computed kept (state `cancelled`); a sweep not running answers 200 `{already: true, state}`; also for a run deleted meanwhile (review F10, F3) |
| DELETE | `/api/runs/{id}/sweeps/{n}` | remove a finished sweep with its results; 409 while it runs (review F10) |
| GET, PUT | `/api/settings/runs` | the removal period `{keep_days}` (whole days, 1–3650); PUT `{keep_days, confirm?: [id]}` saves and applies it at once, or answers 409 `{would_remove: [id]}` when it would remove runs not all in `confirm` |
| GET | `/api/i18n/{lang}` | the merged catalogue of a language, `{lang, messages}` (ETag; 304 when unchanged; 404 for a language not in `LANGS`; §7) |
| GET | `/legal`, `/legal/{name}` | the licence page (a summary in the viewer's language, the disclaimer) and its full texts from a fixed list: `LICENSE.md`, `NOTICE`, `PUBLICATIONS.md`, `COMMERCIAL.md`, `LICENSE-DOCS.txt`, `three.js-LICENSE` (review of 2026-10-29, R4, R8); linked from every page |

WebSocket `/ws/runs/{id}`: server → browser binary messages (`history_start {frame_stride}`, the record so far with its
frames thinned to 4000 by that uniform stride, `history_end {live, state, resumable, rebuilding, resume_error}`, then
the live tail; `closed {state, resume_error}` when the worker ends); browser → server text `{cmd, args}`; a command
the server refuses comes back as text `{error}` (not part of the record).

**Busy.** Every computing command (`step`, `next_event`, `set`, `action`, `view`, `scene`, `new_world`) and the
first world's build are announced by the worker with `busy {on: true, cmd, what, wall}` before they start and
`busy {on: false}` when they end; the command's own messages are held and written after that end, as one piece
(`lfviz.worker.Output`). `busy` is forwarded to the viewers and never recorded; a late viewer gets the current one
after `history_end` with its `elapsed` seconds. The player shows what is being computed, for how long, and "✕
cancel" (`/cancel`). A world's command must therefore change nothing outside the world's state.

Commands: `play`, `pause`, `speed {value}` (simulation seconds per wall second), `step {dt?}`, `next_event`,
`action {name, args}`, `set {values}` (live parameters; consecutive `set` commands are merged), `new_world {preset?,
params?, seed?, carry?}` (a new world in the same run: defaults, then the preset, then params; `carry: true` in a
playground: the current world's scene (its objects with their state, and its time) becomes the new world's initial
scene, §6), `view {op, ...}` (a view
request that needs the engine, e.g. a slice plane of a 3-D world: `Simulation.view(args)` computes and emits what the
view shows; it never changes the world's physics and is recorded like every command; worlds without views refuse it),
`scene {op, ...}` (a playground's scene changed by hand, §6; `edit {id, values}`: a drag, the type's handles only, §6;
`op: "export"` is not recorded: it changes nothing), `stop` (the worker ends; sent by the server), `checkpoint_now {tag}`
(the server's, for the instruments' sweeps; not a change of the world: never recorded as a `command`, never resumes a
run): answered by a `checkpoint` message carrying `tag` — a fresh file of the current state, or the latest file's
message again when nothing changed; `error` instead of a file when none can be given. The file is written in the
background: the asker waits for it. `stop` and `checkpoint_now` are the server's own: a client's, through `/command` or
the WebSocket, is refused (403 over REST, a text `{error}` over the WebSocket; review LB1-framework F6).

**Runs are recorded or paused, never stopped (owner, 2026-10-28).** The player's ⏺ sends `play` / `pause`. A run
without viewers is paused after `--idle-pause` s (60) and suspended after `--idle-suspend` s (1800): its worker is
released, the record stays. When all workers are busy, the run idle longest without viewers is suspended to make room.
A suspended run is resumed by the next command that computes or changes the world, **from its world's last saved
state** (owner, 2026-10-29: «для добавления записи последний кадр должен быть достаточен для полного точного
воспроизведения с последнего состояния в виде продолжения эксперимента, а не нового запуска»). The worker writes a
checkpoint of its world's whole state (`server/lfviz/checkpoint.py`: the simulation object and the runner's state of its
world, pickled; GPU arrays as NumPy arrays put back on the GPU; the worker's output function as a reference; modules
by name; closures by value) when the run is suspended (the server's `stop` carries `checkpoint: true`), when it pauses
(at most once per 10 s) and every 2 min (`sim.CHECKPOINT_EVERY`) while it computes, each recorded by a `checkpoint`
message (world, time, file; the code the world ran — the files under `engine/` of the modules loaded in the worker, so
v12 includes v11, and their hash — and the runtime: Python version, bytecode magic number, NumPy, SciPy and CuPy
versions): its place in the record is the state's place. The state is pickled in the loop and written by a background
thread (the next stop waits for it); a failed write is retried at the next occasion and its temporary file removed
(and any left by a killed worker at the next start). The files are in `runs/<id>/checkpoints/` (the two newest kept;
counted in the run's size and quota); only names `w<world>-<n>.pkl` inside that folder are ever loaded. A resume loads
the last checkpoint of the latest world whose files and runtime are unchanged and repeats only what the record holds
after it (`Runner.restore_from`: nothing after a suspension, the tail after a periodic checkpoint when a worker
crashed); the worker reports which way it went (`resumed {how: checkpoint | replay}`), and the run's passport says so.
For every visualization the world continued from a checkpoint in a new process emits exactly what the original emits,
byte for byte (`tests/test_checkpoint.py`: also a session with live changes, actions, slice planes, `step` and
`next_event` before the checkpoint and a new world after it; on the CPU — review CK's `c01` ran it also with every
kernel on GPU 0 for v08, v11 and v12). A world's state must not rely on two attributes viewing one buffer: pickling
separates them (the known ones, which nothing writes in place, are listed in that test). Without a usable checkpoint
(a file the world loaded or the runtime changed since, or the checkpoint is missing or unreadable) a new worker builds
the latest world from its parameters and seed and repeats, in the order of
the record, every frame's advance (the frame clock's steps, so that worlds whose random draws depend on them come out
the same) and every `command` message (the world-changing commands with their world times), with nothing emitted
(`Runner.restore`), then goes on from the end of the record (`tests/test_restore.py` checks every visualization frame
for frame). A notice says which way the run was continued. A command is
repeated at its recorded time (a `set` handled after a `step` of the same batch has the time after that step, with no
frame between them); a world n ≥ 2 first takes over the view state it took over from the previous world (the slice
planes; `adopted_view` in its header). A world must therefore be deterministic given its parameters, seed and that
sequence: no wall-clock dependence of what it computes (schedules by frames or world time, not by wall seconds;
review C1-6; the one left is STATUS V32 a). The record is the truth and `meta.json` a cache of it: the latest world,
its parameters, seed and preset and the world time it reached are read from the record (a crash within seconds of a
new world left a stale meta), and a record whose last message a crash cut is cut back to its last whole message at the
next start (the cut bytes kept in `stream.cut-tail.bin`; a record that cannot be read is skipped, never the server).
Resuming is exclusive per run (one worker, whoever asks at the same moment); while the world is being rebuilt the run
is never suspended for room or idleness, and a world-changing command other than the one that resumed it is refused
(409: it could not be applied before the rebuild ends). A worker that ends by itself (a failed rebuild, a crash) leaves
the run suspended with the reason (`resume_error`): its record is whole and ⏺ tries again. Records from before this
version (no `restorable` flag) can be watched, not resumed. Runs whose last action (a viewer came or left, a command)
is older than the removal period are removed unless marked "keep"; beyond the quota the oldest last action goes first;
a run open in a tab is never removed. The period (whole days, 3 by default, `--keep-days`) is set on the catalogue page
(owner, 2026-10-29) and kept in the runs folder (`runs/settings.json`, which wins over the option); it applies at once,
and a period that would remove runs at once is refused with their list (409) until exactly those runs are confirmed.

**The player shows the record at the cursor (owner, 2026-10-28).** ⏮ ◀ ▶ ⏭ and the timeline move along the history
(◀ / ▶ play it at the chosen speed); with the cursor at the end a recording is shown live. Whatever is shown is the
state at the cursor's time: the view is fed the record's messages up to that time and, when the cursor goes back,
brought back from its nearest **key frame** before the cursor (owner, 2026-10-29: «для воспроизведения назад давай как в
видео добавлять ключевые кадры»): every 100 messages fed in order the player asks the view for `snapshot()` (the lengths
of its growing lists, references to the latest values, copies of small changing state) and, going back, calls
`restore(snapshot)` on the view's present state and feeds only the messages after the key frame; at most 256 key
frames per world: beyond, the step between them doubles and the key frames on the coarser grid are kept (uniform over
the whole record at any length). A view without `snapshot`/`restore` (v13, v14: their clouds are decoded
asynchronously), or a `restore` that cannot cut back (it throws: v07 once its cap dropped the oldest detections; v11 and
v12 for a key frame from before their latest change of the set-up; the 3-D environment for a target set or a slice
computed after the key frame), is rebuilt from the record (`reset` → `onHeader` with the header as recorded → the
messages up to the time). The 3-D environment's part (`env3d.snapshot`/`restore`): the latest message that set each
object (re-applied in the record's order, the box first; the slices of the planes re-applied with them), and the
lengths of the appending layers (paths, tracks with their segments' colours, triads), cut back by
`scene3d.restoreAppends`. Tested in the browser for every visualization by `tests/browser/keyframes.mjs` (key frames
every 3 messages; live changes, actions, slice planes added and removed in the middle of the record, the page opened at
its end, v09 also in ordinary space where the box grows): the view brought back through a key frame equals the view
rebuilt from the record at the same cursor (the 2-D canvases' pixels, drawn in software and once more before they are
read; the 3-D scene's layers, sphere radii, slice planes and their images, the scene's box; the panels' and overlays'
texts). The scene keeps a copy of the header's scene description (`setBox`, `setObject` change it), so that a view
rebuilt at an earlier time starts from the header as recorded; a view rebuilt for the same world keeps what the
experimenter chose in it (v01: the frame, the camera, the zoom). Every
version of a check is kept and the latest one computed by the cursor's time is shown; events ahead, the set-up, the
actions, the approximations and the engine modules in force are shown as of that time. A view must therefore be a
function of the messages it has been fed (no state from messages it has not seen; a 2-D canvas starts every frame from
the default drawing state, `ui.js` `fresh2d`, since what one frame leaves in the context would change the next until a
resize), `reset()` must clear everything,
and heavy work for a message only the last of which is shown (a wave image) is done when it is drawn, not when it is
fed. The set-up, actions and slice planes can be changed only at the end of the history of the current world
(`ctx.readOnly()` gives the reason otherwise; the event `editablechange` says when it changed). A long history keeps
the frames whose arrival number is a multiple of a stride that doubles beyond 20 000 frames: uniform at any length.
While the record is replayed on a (re)connection nothing is drawn (every render redraws the whole scene); the view is
drawn once at `history_end`.

**Refusals and failures (owner, 2026-11-04: «если ошибки … должно быть все понятно и удобно»; reviews UX-params P1–P4,
UX-ui U13).**
- What the owner reads is a translatable text (`T`, §7), shown in the viewer's language, and says what to change; it
  is never a traceback.
- A world refuses with `lfviz.errors.Refusal(text, hint)` (`ValueError(T(...))` for a plain refusal): `text` and
  `hint` are `T`; the object or the parameter by its label, numbers with units as arguments, and in `hint` the change
  that makes it work. The player shows `T("{text}. What to change: {hint}")`. A plain `ValueError` keeps its own text.
- Any other exception is shown as "<what was not done>: internal error of the world — <what> (<Type>) — the run is
  saved; you can go back or change the parameters" (`lfviz.errors.owner_text`, which returns the `T` and the detail).
  Its one-line English text goes into the message's `detail` (folded under "details"), and its traceback only into the
  run's `worker.log`.
- Parameters are refused by the schema with their label, unit and range, and each error carries the parameter's id
  (`ParamError.pid`; `POST /api/runs` answers `{error, fields}`).
- A combination a world cannot build is refused before anything is started: `Simulation.check_params(params)`
  (cheap), asked by the server at the start and by the worker for a new world.
- A first world that fails to show itself (its header, `after_header`, the t = 0 advance) is reported "World not
  created: …" and ends with `end {reason: "world not built"}`. Such a run is failed, never resumable. `history_end`
  says why (`start_error`), and so do the run list (`error`) and the catalogue's card.
- A new world that fails so is refused as a whole, and the previous world goes on.

**Memory budget (review UX-params P8: one world took 31 GB of the shared host).**
- Every worker holds a budget as its hard limit of private writable memory (`RLIMIT_DATA`, `lfviz.limits`). The
  server option is `--worker-mem-gb`. By default it is 60 % of the server's memory (its container's limit, else
  the host's), from 1 to 8 GB.
- An allocation beyond it fails inside the worker and is reported to the owner as a translatable text (sizes by
  `lfviz.limits.fmt_bytes`, itself a `T`). The host and the other runs are not touched.
- A world says what it will allocate: `estimate_bytes(params)` before it is built (checked by the server at the
  start and by the worker for a new world), and `lfviz.limits.require(nbytes, what, change)` before a large
  allocation while it runs. An estimate above the budget is refused at once, with the numbers and what to change.
- A sweep process (§6 «Instruments») has its own hard limit, `LFVIZ_SWEEP_MEM_GB` (by default half a worker's budget,
  at least 512 MB), and `oom_score_adj` 1000, so that the kernel ends a sweep before a live world.

A select's option may be `(value, label, show_if)`: the forms show it only when `show_if` holds (the schema does not
enforce it; the world refuses with a translatable text).

Message format (`server/lfviz/protocol.py`, `player/js/api.js`): `u32 json_len | JSON | pad to 8 | arrays`, arrays
8-byte aligned and described in `JSON.blobs`. Message types emitted by every simulation:

| type | when | content |
|---|---|---|
| `header` | first in every world | scene, actions (forms), modifications, approximations (optional, list of strings), units, anything static; added by the runner: `world`, `params`, `preset`, `seed`, `live`, `engine` (the lfphys modules of the world, `engine_modules()` with their ABOUT), `backend` (the device settings in force, what each engine kernel ran on so far — `used[kernel].drawn` for the results drawn, `used[kernel].check` for references and checks — and the engine's notes about adjusted settings; plan P11) |
| `live` | after every `set` | `{values, engine}`: the live parameters in force (also after a refused change) and the engine modules in force (a live change may bring one in or out) |
| `state` | on change | playing, speed, speed range |
| `command` | with every world-changing command | `{cmd, args}` at the world time it was applied (`set`, `action`, `view`, `scene`, `new_world`): what a restore repeats; the player does not show it |
| `frame` | ~20/s while playing | the current state (droppable for slow viewers); added by the runner (a world must not use these keys): `t`, `cpu_ms`, `lag` (this frame's advance stopped short of the chosen speed: the computation could not keep up) and `speed_actual` (B4: world seconds per wall second actually reached over the last 1.5 s of play, null before; the player shows it next to the chosen speed when it falls below 97 % of it — the owner's note of 2026-10-28: at high speeds the black-hole world ran at 1 % of the label); a playground's frame may carry `meas {id: number \| null}` (the declared display units) and `meas_note {id: text}` (why a value is undefined; P16.3) |
| `event` | when the run's time reaches it | `{kind, text, obj?, data?}`; actions appear as `kind: action`; `notify?` (shown as a toast when it happens) |
| `check` | when computed | `{id, label, value, ref, unit, rel, tol, ok?, info?, group, note}`; `ok` overrides the tolerance test; `info: true` marks a comparison shown for information (a model against the core, say), drawn as ≈ and never as a pass or a failure; `expected?` (why a failure is expected here: drawn as an expected ✗ with the reason) |
| `actions` | after a change | new action forms (defaults) |
| `notice`, `error` | as needed | a text for the owner (a `T`, §3 "Refusals and failures", §7); `detail?` the exception's own one line (English) |
| others | per visualization | accumulative data (e.g. `pulse`, `worldline`, `signal`, `segment`, `detections`); any accumulative message (a playground's `scene` always; a demonstration's header or another message) may carry `measurables [{id, label, unit, of, group}]` (P16.3); a playground's latest scene message is the list it measures now |

Everything except `frame` is accumulative: never dropped, recorded, replayed to late viewers in order.

### 3-D worlds (rule 2.10; `v08_wave_3d` and `v09_thomas_3d` are the reference implementations)

The header carries `scene3d`: `box` [[xmin, ymin, zmin], [xmax, ymax, zmax]] (physics coordinates, z the depth),
`units`, `coord_names` (optional, e.g. ["βx", "βy", "βz"]), `views` (optional camera buttons `[name, label, title]`,
names iso / side / top / beam / back), `objects` (each `{id, label, kind, visible, ...}`: `plate` with `holes`
(`rect` / `circle`), `disk`, `incident`, `target`, `sphere` (`center`, `radius`), `point` (`pos`, `text`), `panel` (B3, v11: a computed field on a rectangle of any orientation, `origin` (a corner), `u`, `v` (its edges), `opacity?`; its image is set by the world's view, `scene3d.setPanelImage`), `box` (B4, v11: a translucent box with edges, `center`, `size` [sx, sy, sz], `color?`, `opacity?`, `text?`, `text_size?` — e.g. the observer at slit B; a world replaces it with `scene3d.setObject`); the player
draws them; `box` is the region at the start — never framed on consequences still to come), `layers` (computed fields: `{id, label, kind: "volume" | "vectors", visible, look?}`, `look` = the volume's starting `{tau?, threshold}`: τ the optical depth of the volume's densest line of sight along an axis
of the region (the density slider); without `tau` the player keeps the world's former look, `density` (the old value per
length unit, 0.6 when absent) times the densest column of the world's first volume), `planes` (`max` ≤ 3, 0 when the world has no field to slice; `center`;
`defaults`: the normals for planes 1–3, mutually perpendicular; `time_unit`: the unit of an auto plane's speed when it
is not the second). Messages:

| type | content |
|---|---|
| `volume` | `id`, `dims` [nz, nx, ny], blob `data` (float32, values 0..1, index iz·nx·ny + ix·ny + iy) |
| `vectors` | `id`, `count`, blobs `pos`, `vec` (float32, count × 3) |
| `target` | `id` (an object), `shape` [nx, ny], blob `img` (float32 0..1) |
| `path` | `id`, `from`, `count`, `label?`, blob `pts` (float32 count × 3): points [from, from + count) of a computed path, sent as the run's time reaches them (accumulative) |
| `triads` | `id`, `count`, `label?`, blobs `pos` (count × 3), `mats` (count × 9: 3 × 3 row-major, its columns the axes) |
| `marks` | `id`, `count`, `label?`, blob `pos` (count × 3) |
| `arrow` | `id`, `from`, `vec`, `label` (drawn next to it), `layer?` (the layer's name), `color` |
| `box` | `box`: a wider region for a world whose extent is revealed as its time runs (e.g. a trajectory); the frame is redrawn, the objects keep their coordinates; an equal box changes nothing; the camera is refitted only if the experimenter has not moved it |
| `planes` | the planes in force: `{id, origin, normal, u, v, auto, speed, polygon (the cut by the box in (s, t)), label}` |
| `slice` | `id`, the plane (`origin`, `u`, `v`, `normal`), `s` [s0, s1, ns], `tt` [t0, t1, nt], `route`, `route_label`, `exact`, `approximation`, `reason`, `verify` {points, max_err, tol, ok}, `verify_title?`, `z_near?`, `window_est?`, `units?` (default µm), `coord_names?`, `depth?` (false: no axis is the depth), `quantity?` (`{label, unit, peak}`: a field that is not a wave, value = I · peak); blobs `I` (float32 nt × ns, value / peak, NaN outside the region) and `phase` (waves) |
| `mesh` | (B3, v10) a surface computed by the run: `id`, `label`, `count`, `opacity?`, `visible?`, `base` ("lab": absolute vertices; "rest": offsets placed by an affine map from the frames, `scene3d.transformMesh(id, A, b)`); blobs `pos` (float32 count × 3), `idx` (uint32 triangles), `rgb` (uint8 count × 3, sRGB); a world may replace a "lab" mesh's vertices and colours later (`scene3d.updateMesh`) |
| `image` | (B3, v10; drawn by the shared camera window `player/js/imagewin.js`, not by env3d) what an observer sees: `seq`, `shape` [H, W], `camera` {kind, fov, forward}, `mode`, `mode_label` (a mode that is not what is seen is marked in the window), `codec: "deflate"` and `filter` (fields sent as row differences); blobs deflated: `rgb` (uint8 H × W × 3) and the world's per-pixel fields for the readout (v10: `D`, `delay`, `T`, `body`); frames name the image they show (`img_seq`) |
| `wave` | (B3, v11) a 2-D world's wave on its plane: `shape` [nx, nz], `peak`, `ds` (grid steps per pixel), `tau`; blobs `amp` (uint16, √(\|ψ\|²/peak)·65535) and `phase` (uint8, (arg ψ + π)/2π·255); accumulative, so that the record keeps every image and a viewer who scrolls back sees the wave of that moment (frames are thinned); drawn on a `panel` object and in a slice window marked `fixed` (not removable; `meta.fixed`, `meta.title`) with the world's overlay (`slices.setOverlay(id, fn(ctx, map))`: computed polylines drawn in the plane's coordinates) |
| `cloud` | (B4, v13/v14; server `lfviz/orbitals3d.py`, view `player/js/orbitview.js`) a probability cloud \|ψ\|² for the scene's volume: `id`, `bin`, `nb`, `t_bin`, `dims` [nz, nx, ny], `peak` (one scale for all phases: (Σ_k \|c_k\|\|ψ_k\|)² maximised over the grid, a bound of \|ψ(t)\|² at every t known without evolving; review B4-10), `enc: "sqrt-u8"`, `codec: "deflate"`; blob `data` (deflated uint8 √(\|ψ\|²/peak)·255, index as `volume`). A time-dependent cloud that repeats with a period T comes in `nb` phases, each revealed when the run's time reaches it; `vectors` and `slice` messages of such a world carry the same `bin` (and slices a `rev` per placement of their plane); frames name the phase they show (`bin`: the last one reached), so the record stops growing after one period and a viewer who scrolls back sees that moment's cloud. Shown with `scene3d.updateVolume(id, data)` (same dims: texture and mesh kept) |
| `prepared` | (v13, v14) a state prepared at the current moment: `t_prep`, `keep_time`, `header` (the header's parts that describe the state: title, states, levels, period, nb, scene3d …); the view starts its state from the world's header with them; frames carry `t_prep`, the period's phases count from it |

Since B3 the scene also draws many computed polylines at once (`scene3d.appendTracks(id, xyz, colours)`, NaN where a
track has ended; `setTrackColors` recolours whole tracks, e.g. when a Bohm particle's slit becomes known), a point
cloud replaced on every frame (`setPoints`) and an object rebuilt after a live change of the apparatus (`setObject`,
e.g. v11's plate when a slit is closed); v11's own messages (`tracks`, `hits`, `screen`, `result`, `setup`) feed them.
A moving body (e.g. v09's craft: its position, gyroscope frame, spin, thrust) is drawn by the world's view from the
frames (`scene3d.setBody`); an observer (a marker, its velocity, the lab directions of its field of view) by
`scene3d.setObserver` (v10). View commands: `view {op: "plane", id, origin?, normal?, auto?, speed?}` places or moves
plane `id` (1–3); `view {op: "remove", id}` removes it; `view {op: "reset"}` restores the default planes; `view {op:
"preview", id, origin, normal}` (while a plane is dragged and no volume was computed) answers with a coarse `slice`
marked `preview` that changes nothing (not kept, not checked). A plane's in-plane axes are the engine's
(`lfphys.core.geometry.Plane.horizontal`: u horizontal, v towards the depth); its cut by the box is
`lfphys.core.geometry.plane_cut`. The player sends `view` only for the current world (a world from the record is
read-only).

## 4. How to add a visualization (checklist for agents)

1. Create `vNN_<slug>/` with the files of §1. `viz.py`: a `Schema` of world parameters (laws marked `standard`),
   presets, and a `Simulation` subclass of `lfviz.sim.Simulation` implementing `header`, `advance`, `frame`,
   `action`, `next_event_time` (and `after_header` if it emits messages while constructing the world).
2. Physics from the engine `../lfphys/` (add what is missing there, in the right layer, with tests); the
   visualization's `engine/` holds the apparatus logic, `engine_modules()` lists what a world uses; drawing only in
   `web/view.js`. The view may interpolate along computed polylines and apply matrices the run sent; it computes no
   physics.
3. Emit checks for every quantity that has a closed form; state approximations; flag modifications.
4. Tests in `vNN_<slug>/tests/`; run all tests in Docker (`README.md`); look at the pages in a browser (headless
   screenshots are fine). The browser regressions `tests/browser/keyframes.mjs` (key frames, §3),
   `tests/browser/scene3d_checks.mjs` (the 3-D view's rendering contract, §2 rule 10), `tests/browser/manipulation.mjs`
   (direct manipulation in the playgrounds, §6), `tests/browser/instruments_checks.mjs` (the panel "Instruments" and
   the sweeps, §6) and `tests/browser/i18n_checks.mjs` (every page and world in every language, §7) run against a
   private server in Playwright's image, each with the commands in its header.
5. Every text the owner reads is a `T` with an English msgid, translated in the world's `locales/<lang>.json` for every
   language of `../LANGUAGES.md`; the README exists in every language (`README.md`, `README.<lang>.md`); the world is
   registered everywhere it belongs (`../AGENTS.md` §3 rules 13, 15; §7).
6. A different agent reviews the physics into `../reviews/`; the review is processed (RESPONSE.md) before the
   visualization is reported as done.
7. Open problems of a visualization go to `../STATUS.md`, section "V. Visualizations — open items" (one place).

## 5. Devices and precision (plan P11, 2026-10-27)

The engine's heavy kernels (`lfphys.core.backend`) run on the CPU or on GPU 0. The owner's choice per kernel —
auto (the default: the GPU where it is faster, by measurement), CPU or GPU, and fp64 or a validated lower precision —
is made on the settings page `/settings` and saved at once in `settings.local.json` (per machine, git-ignored). A run
takes the settings in force at its start, or those with the start form's overrides for that run (catalogue: "For this
run:"); they are recorded in its passport (`backend_settings`, with `override` when the run chose its own) and its
header (`backend`). REST: `GET /api/devices` (devices and kernels as the engine reports them, from a subprocess: the
server never holds the GPU), `GET`/`PUT /api/settings` (the shape is checked by the server — a malformed body gets
400 with the reason, a body over 64 KB 413 — then the engine validates the values from stdin; writes of the file are
serialised), `POST /api/settings/calibrate` (measures the CPU/GPU crossover sizes). References and checks always run
in fp64, whatever the setting; a check never compares fp32 data at an fp64 tolerance (the drawn fp32 data are
compared with fp64 under the kernel's declared bound). A visualization does not choose devices itself; it calls the
engine's kernels. Tests never write the owner's `settings.local.json` (they patch `lfviz.devices.SETTINGS_FILE`).
**Temperature** (STATUS V23 c): before a kernel takes the GPU the engine reads its temperature (NVML, read only, at
most every 2 s); from 82 °C on the kernels run on the CPU until the GPU has cooled to 70 °C, and the reason in the
run's header and `used()` says so (`lfphys.core.backend.THERMAL`). A playground session can run for hours: this keeps
the GPU below the temperature where this host once hung, whatever power limit is set.

## 6. The playground (plan P15.0; owner, 2026-10-28)

> визуализации вынеси в отдельный режим - это подготовленных демонстраций. плейграунд для исследований. плейграунд
> должен быть разбит на разделы по темам физики … в плейграунде можно добавлять в мир разные объекты, менять
> параметры, смотреть за их изменением и взаимодействием, все должно быть не задано заранее, а просчитываться в
> реалтайме

Two modes in the catalogue: **Demonstrations** (the `vNN_` folders: prepared set-ups with their checks and story) and
**Laboratories** (the `pNN_` folders, one per branch of physics). The interface calls a playground a *laboratory*
(«лаборатория»; owner, 2026-11-13: «Лаборатория / Laboratory»); the code keeps the identifier `playground`
(`kind: "playground"`, `lfviz.playground`, the ids `pNN`). Every rule of §2 holds in the playground: what is shown
is computed by the run; accepted physics by default, a changed law is a named world parameter and is flagged; the
consequences of a change start at the moment it is made.

* **A section** subclasses `lfviz.playground.PlaygroundSimulation`: a `PALETTE` of object types (`ObjectType`: label,
  kind, a schema of parameters), the hooks `on_add`, `on_remove`, `on_set`, `object_state`, its `advance` (the
  section's solver), `frame` (the bodies' or fields' state and the probes' readings; `now[id]` is the selected object's
  state shown in the inspector), running checks of its conservation laws (`running_check`, every `CHECK_FRAMES`
  frames by count), and `rekey` (what a view needs from a segment's start on besides what the base repeats; it must
  not change the world's state: a world rebuilt by replay has no segment starts). The laws are world parameters,
  except the laws the engine can change at the current moment: these are live (integrator, 2026-11-05; review
  UX-ui U12). p02's grid and window are such laws: the waves are resampled exactly at the current moment, and a
  change that would drop or misplace more than 10⁻⁶ of a particle's norm, or put it under the open edges' moved
  layers, is refused with the number (`Scene.regrid`). A drag of a wave is a re-preparation of the same wave only
  where a translation keeps it (for a charged particle, the magnetic translation); elsewhere it is refused with the
  reason. A playground's law that only sets its units is a property of the object that carries it and is live (p01:
  the hole's mass M, the binary's mass m: G = c = M = 1, so a change is a change of units at the current moment — the
  dimensionless state is kept, seconds and metres rescaled, proper times and clocks kept in seconds; said in the
  event). A change of a metric's other parameters under moving bodies, which has no established dynamics, is offered
  only as a declared "what if" (p01: spin and charge), flagged in the approximations ("“WHAT IF” MODEL …") and the event, with
  its rule stated and the checks restarted. A grid, a domain or a time step is live where the engine transfers the
  state with a stated error and closed books (p04: `Flow2D.remap`). A playground's laws marked `live` are shown and
  applied at the current moment as in demonstrations. The initial scene is the hidden world parameter `scene`
  (`scene_param`): a preset's scene or a file's.
* **The scene** is changed by hand at the current moment with the command `scene` (`op`: add, remove, set, edit (a drag: the handles only), duplicate,
  label, clear; export): recorded with its time like every world-changing command, so a restore repeats it; a
  refused change is reported and leaves the scene as it was. After every change the world emits `scene` (the whole
  object list); the scene's changes are events of kind `scene` (the panel "Scene changes").
* **A new world that keeps the scene** (plan P16.1, "carry the scene over"; reviews LB1-F5, LB1-F15): `new_world` with
  `carry` re-adds the current world's objects in the new world under their ids, through `place` and the add path, at
  the current world time; an object the new world refuses is skipped. The panel "New world: …" has "carry the scene
  over" (on; off with a scenario); `new_world {carry: true}` puts the current world's export into the new world's `params.scene`; the
  carried scene is the new world's parameter, held in its header, so a restore rebuilds the same world (the `command`
  keeps only `carry`). A scene file holds only what `object_state` gives as JSON. A section whose state is large gives
  it for a carry through `carry_state() -> {"objects": {id: state}, "world": state}` (plain data and NumPy arrays of
  numeric or bool type) and takes it in `on_add(obj, state)` and `carry_world(state, laws)` (called once in every
  carried world, `state` None when the old world gave none; raising starts the world's own state afresh);
  `carry_note(text, obj=None, restarted=False)` says what was adapted or started afresh, and `self.carrying` holds the
  old world's laws during the carry. The runner writes the heavy state once into the run's checkpoint folder as
  `carry-w<N>-<ns>.npz` (read with `allow_pickle=False`, never unpickled) and names it with its SHA-256 in the new
  world's `params["scene"]["carry_file"]`: a restore by replay reads the same state and refuses when the file is
  missing or changed; a scene file never names one; only the latest world's file is kept. The notice of a carry
  (recorded) says object by object what went with its state, what was rebuilt from its parameters (no state of its
  own — `ObjectType.stateful`, by default the types with a velocity handle — or a state not carried, with the
  reason), which values the new world changed (hidden parameters are not listed:
  `test_hidden_parameters_are_not_listed_as_changed_by_a_carry`), what it refused, and what happened to the world's
  own state; its `carry` field holds the same as data. The "New world: …" form shows every law of the new world, the live
  ones at their current values. A world accepts objects across a law change where physics allows; its `place` may
  adapt values (drop a coordinate the new dimension lacks) and must refuse the rest with `Refusal`. A playground whose
  state is a field (p04's flow) carries it into a new world through `carry_state` and `carry_world`. On the same grid
  it is copied as it is; otherwise the engine's own transfer moves it first (the live grid change's). What starts
  afresh is said with `carry_note(…, restarted=True)`. Kerr bodies (p01) carry the metric and unit their state is in.
  Another hole of the same laws takes them as an initial condition (the same place and ZAMO momentum), said per
  object. Tests: `tests/test_carryover.py`.
* **Direct manipulation** (P16.2; the integrator's decision of 2026-11-11, as written here). A palette type may declare `handles` (checked when the palette
  is built): `position` (2–3 parameter ids, or `{param, axis_param}` with the axis as x|y|z, 0|1|2 or "0"|"1"|"2"),
  `velocity` (as many ids; not with the axis form), `size` (for picking), `velocity_max` (a number in world length per
  world time, or an own parameter's id). Every positioned object is in the frame's `at[id]` on every drawn frame.
  Player: click picks from `at` and `size` (else 9 px; smallest wins) in the scene and in slice windows; a drag moves
  a ghost in the plane through the object across the view (a plane world or a window: its plane; the axis form: along
  the axis); release sends one `edit` in raw world units (never display-scaled; positions on a 10⁻⁵-of-region grid);
  Shift throws: velocity = world displacement over the last 100 ms ÷ (wall time × the speed control's rate) × the
  throw scale (its automatic value and the clamp: the next bullet); Delete removes, Esc cancels; selection and ghost
  are the viewer's (never recorded, never scene layers). Server: `edit` changes only the handles, through `on_set`,
  rolled back on a raise; every sent handle is applied (`old[k]` is None for one equal to its stored value: a world
  must not do arithmetic on `old` of a handle); a throw above `velocity_max` is clamped and logged (the next bullet);
  edits follow the read-only history and busy. Tests: `tests/test_manipulation.py`, `tests/browser/manipulation.mjs`.
* **Direct manipulation: the throw and Delete** (plan P16.2; reviews LB1-F13, LB1-F14, LB1-p02-ux X2, X4): the
  automatic throw scale makes a brisk flick (the view's width in a wall second) cross the world's region in 2 wall
  seconds at the current playback rate, never faster than half the `velocity_max` a type declares (which clamps); a
  clamp and a refused throw say "reduce the throw scale". The scene's log names an edit as "‹label›: move to (…)
  ‹unit›; throw: v = (…) ‹unit›" and says a clamp only when one happened. A type whose throws are better read in
  another unit than the world's declares `velocity_display = {"unit", "factor"}` (factor × world velocity = shown; the
  readout and the log only, the edit stays in world units). Delete removes the selected object also when it was picked
  in a 2-D world's own window (that window is never removed).
* **Numbers in the owner's texts** (review LB1-p02-ux X6; §7): a number is always an argument of a `T`, never
  formatted into a string on the server; the player formats it in the viewer's language (`i18n.js` `fmt`: a decimal
  comma in Russian, also in the mantissa of m·10ⁿ, the minus sign −). `lfviz.playground.fmt` is deprecated: it remains
  only for the worlds' older texts and the tests.
* **Placing and the palette** (reviews UX-ui U4, U7, U22; UX-params P28):
  - a palette button opens a pre-placement form with the type's parameters; the point is typed, or clicked in the
    3-D scene (the plane z = the middle of the region) or in a slice window;
  - the section's optional `place(kind, values)` completes the values (a free spot, a free side; `position` [x, y,
    z] is the clicked point) or refuses;
  - `palette_state()` names the types the world cannot take now (the buttons are disabled with the reason);
  - `can_remove(obj)` is asked before a removal and for every object before `clear`, which removes all or nothing;
  - these hooks are cheap, deterministic and never change the world;
  - the latest set-like messages repeated at a segment's start carry `repeat: true`, and a viewer holding the same
    message ignores them (UX-ui U1).
* **The scene as a file** (`lfscene`): the section, its laws, the time and the objects with their parameters and
  their dynamic state as plain JSON (`scene_export`, forwarded to the viewers and never recorded); loading one starts a
  new world (in the catalogue: a new run) with `params = laws + {"scene": file}`.
* **The record is a moving window** (owner, 2026-10-29: «автозапись всех последних N кадров, старые вышедшие из
  окна удалять, сохранять все только если нажата запись вручную»; the scheme agreed then: the button keeps the window
  and records on, checkpoints in the window, the window by time or size): `lfviz.runs` splits a playground's record into
  segments at its checkpoints (every `checkpoint_every` = 60 s of wall time while playing, and at a pause or a
  suspension; each segment starts with `record_segment`, the scene, what `rekey` emits and the latest value of every
  set-like message — `SET_LIKE`: box, meshes, lines, marks, shapes, actions, approximations — then the `checkpoint`:
  a segment is drawable on its own), deletes the segments that left the window — `buffer.window_s`, 10 min by
  default, counted as the time the world was shown computing (frames flowing: a pause or a suspension does not age
  the record), and `buffer.window_mb`, counting the checkpoint files too; never the newest two segments, so the
  bound may be exceeded by up to two segments — keeps the worlds' headers apart and sends a world's header before its
  first kept message; not while a history or a download is being read. `POST /api/runs/{id}/record {on}`
  ("● Keep the record"): what the window holds and everything after it is kept until switched off; the record's state
  (`record_state`) is the run's, sent to the viewers, not recorded. A resume continues from a checkpoint; a world whose
  start left the window, or whose kept record has a hole (recording switched on and off), is not rebuilt by replay
  (the resume, or the worker when the checkpoint does not load, says so: start again from a scene file).
* **The player's panels** (`player/js/playground.js`): the palette, the scene's objects, the inspector, the probes,
  the scene's changes, the file, the record's window. Views draw with the 3-D environment (`env3d`, `scene3d`;
  `setSpheres` for bodies) and keep the key-frame contract of §3.
* **Measurables** (P16.3, framework part): `measurables()` in every `scene` message when non-empty; malformed entries
  dropped to the worker log, never breaking the scene.
* **Instruments (plan P16.3; owner, 2026-11-04 and 2026-11-11; `lfviz.instruments`, `lfviz.sweep`,
  `player/js/instruments.js`).**
  - **The panel "Instruments"** lists a world's measurables by group, plots the values the run recorded at its frames'
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
  - **Nothing measured** is state `failed`, "not computed".
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
* **The framework's tests** run on a toy section found only by the tests (`tests/playgrounds/p99_toy`, through the
  environment variable `LFVIZ_EXTRA`): `tests/test_playground.py`, `tests/test_manipulation.py`,
  `tests/test_carryover.py`.

## 7. Languages and i18n (owner, 2026-11-12)

> для всего фронта сделай i18n переводы на русский и английский, по дефолту английский и переключением языка.

The rule for the whole repository is `../AGENTS.md` §3 rule 13; the languages are listed in `../LANGUAGES.md`. This
section is how the visualizations keep it.

* **Languages.** English is the source language and the default; Russian is the second. Every page (catalogue, run,
  settings, licence) has the switch EN | RU in its top bar (`player/js/i18n.js`, added to the first `.topbar`); the
  choice is stored in `localStorage` under `lfviz.lang`, and `?lang=xx` in the address overrides it for that tab: the
  pages reached by its links keep the link's language (`sessionStorage`; a link opened in a new tab carries `?lang=`)
  without changing the stored choice, and the switch ends it (review i18n-code F7).
* **Texts on the server (Python).** A user-facing text is never a ready string in one language: it is
  `T("English msgid {arg}", arg=value)` from `lfviz.i18n` (the engine's `lfphys.i18n`, re-exported). Numbers are
  always arguments, never formatted into the msgid. The formats are `{x}`, `{x:.3g}`, `{x:.2f}`, `{x:.2e}`, `{x:d}`
  (each optionally with the sign flag `+`), `{x:cap}` (a text argument with its first letter capitalised) and
  `{x:unit}` (the unit a label carries after its last comma). A list argument is joined by ", ". A catalogue entry may
  hold plural forms `{one, few, many, other}`, chosen by the argument `n`. A `T` may contain other `T`s. It serialises
  to JSON as `{"$t": msgid, "a": {...}}` and survives `dataclasses.asdict`, `copy`, pickling and a JSON round trip, so
  a run's record is language-neutral and is read in any language later; records made before 2026-11-12 keep their
  Russian strings: in another language their labels are shown by a reverse lookup of the Russian catalogue (a string
  that is exactly a translation shows its msgid's text), their sentences with numbers as recorded, with a note
  (`i18n.js` `legacy`). `str(T(...))` is the English rendering (logs, tests). The server compares texts by msgid and
  arguments (`same_text`, `mentions`, `names_unit`), never by `str()` or a rendering, and reads records and sweep
  specs back with their texts as `T` (`json_hook`); a file for the owner (a CSV's header) is rendered by `render_in`
  in the language asked, with its number format.
* **Errors.** A refusal is `ValueError(T(...))` or `Refusal(T, hint=T)`, which the player shows as
  `T("{text}. What to change: {hint}")` (§3 "Refusals and failures"). `owner_text(exc)` gives the owner's `T` and the
  English one-line detail; a plain (untranslated) English `ValueError` is shown as a translated head with the sentence
  under "details". HTTP errors are `{"error": <T>, "text": <English>}` (`error_body`, with `en.json`'s plural forms). Sizes in bytes come from
  `lfviz.limits.fmt_bytes`, a `T`. `lfviz.playground.fmt` is deprecated (§6 "Numbers in the owner's texts").
* **Catalogues.** `<lang>.json` maps msgid → translation. They are merged in this order: the engine's
  (`../lfphys/lfphys/locales/`), the framework's (`locales/`), then each world's (`<world>/locales/`, also the folders
  of `LFVIZ_EXTRA`). `en.json` holds only plural forms and overrides. One msgid never gets two translations:
  `tests/test_i18n.py` reports a conflict, and the fix is to reuse the framework's msgid with its translation or to
  choose another msgid. `GET /api/i18n/<lang>` serves the merged catalogue (§3: ETag with the weak comparison, 304,
  gzip, 404 for an unknown language; "ru-RU" is "ru"); the player loads it from `/static/locales/<lang>.json`, the same
  body, relative to its modules, so that a static copy of the player (the public site) carries the files written by
  `python -m lfviz.i18n --export <player copy>/locales` (run from `server/`). A catalogue that cannot be loaded leaves
  the English texts and marks the switch (⚠).
* **The player (JS).** `import { t, fmt, lang } from "/static/js/i18n.js";`. Every text from the server goes through
  `t()`; `el`, `fill`, `panel` and `toast` render a `T` themselves. A static text is a literal `t("…")`, so that the
  completeness test finds it. Numbers are formatted by `fmt(x, spec)` in the viewer's language (a decimal comma in
  Russian, the minus sign −, m·10ⁿ). In HTML, `data-t`, `data-t-title` and `data-t-placeholder` mark the texts to
  translate. A local or a parameter is never named `t` (it would hide the translator). A number field is
  `numberInput()` of `ui.js`, never `type=number` (Chromium drops a typed decimal comma there: 650,5 became 6505,
  review i18n-browser F1): a text field (`inputmode=decimal`) that shows the value in the viewer's format (`fmtField`)
  and is read by `parseNum`, which takes "," and "." as the decimal separator, spaces and groups of three as thousands,
  − and m·10ⁿ, and refuses an ambiguous text ("1,500" in English) with both readings. A whole number without a format
  is shown exactly; a plural form follows the number as shown. Toasts and event rows capitalise their first letter. A
  CSV download takes `?lang=` for its column headers. A msgid built at run time names its msgids in a comment
  `i18n-msgids: "…" "…"` (none for one made of placeholders only).
* **Tests.** `tests/test_i18n.py` checks the catalogues' format and conflicts, static and dynamic completeness (every
  msgid of the code and every text a world sends is translated), a guard against Cyrillic in code lines (a line that
  needs it carries the marker `i18n-ok` in a comment; escapes are decoded), that no local is named `t` (JavaScript) or
  `T` (Python), that every placeholder format is one the player renders and a translation keeps it, that a run-time
  msgid carries its marker, and that no server code `str()`s a text. `tests/i18n_pending.txt` lists files not yet
  converted and must be empty at a commit. `tests/i18n_tools.py --lines FILE… | --pending | --shadow` shows what the
  guard refuses and where a local hides `t()`. In a browser, `tests/browser/i18n_checks.mjs` opens every page and
  every world in English and in Russian. The other browser scripts take the language from `-e LFVIZ_LANG=en|ru`; they
  import `lfi18n.mjs`, so they are copied together (`cp /t/*.mjs /pw/`). The player's JS unit tests:
  `node --test player/js/tests/*.test.mjs` (from `visualizations/`, Node 22 or newer, e.g. the `node:24` image).
* **Glossary (owner and integrator, 2026-11-13).** One word per concept in each language, in the interface and in the
  user documents: the free labs are "laboratory" / «лаборатория» (never "playground", "sandbox", «плейграунд»,
  «песочница» in a user text); "MODIFIED PHYSICS" / «МОДИФИЦИРОВАННАЯ ФИЗИКА» in full; a parameter sweep is «перебор
  параметра»; a worker is «рабочий процесс»; a numerical error is «погрешность» (a fault stays «ошибка»); "closed form"
  is «в замкнутом виде»; "against" is rendered by sense («в сравнении с», «в зависимости от», «↔»), not «против»;
  «2D»/«3D» and the decimal comma in Russian; British spelling and "2-D"/"3-D" in English. Every count phrase has
  plural forms (`{n:d}` and the catalogue's plural entry; English one/other in `en.json` where English needs it), and
  no ordinal is built as "{k}th". A button is named by its label ("▶ Start a new world", not "New world").
* **User documents.** A world's README and the owner guide exist as `README.md` (English) and `README.<lang>.md` for
  every other language, each linking the other at the top. A document names a part of the interface by its label in
  the document's language: the msgid in an English document, its translation from the catalogues in another.
* **Adding a language.** A row in `../LANGUAGES.md`; its code in `LANGS` of `lfviz/i18n.py` and of
  `player/js/i18n.js`; a `locales/<code>.json` next to every catalogue (`tests/test_i18n.py` lists what is missing);
  and `X.<code>.md` for every user document.
