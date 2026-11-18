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
                         slice planes of 3-D worlds: lfviz/planes3d.py; the headless runner of recordings and atlases:
                         lfviz/headless.py; «compute live» of an atlas point: lfviz/atlas_live.py)
  player/                the one player: start page (index.html, js/start.js), runs page (runs.html), run page
                         (run.html; also a saved recording, ?rec=, and a demonstration's screens, ?demo=: js/demo.js,
                         watch.js, explore.js, lab.js, atlas.js, fit.js, record_core.js, assets/demo.css; §10), the
                         worksheet page (worksheet.html, js/worksheet.js), js/base.js (MODE, BASE, url, page: the same files
                         on the server and on the public site, §9), shared JS/CSS, the 3-D environment (js/env3d.js over js/scene3d.js and js/slices.js; the camera window
                         js/imagewin.js); vendor/: third-party modules, unmodified (three.js r185.1, MIT;
                         vendor/README.md)
  tests/                 server/API tests and the test harness
  runs/                  run records (git-ignored; limits: keep days, quota; "keep" protects a record)
  site/                  the public site's scripts (§9; site/README.md): record.py (the offline recorder), atlas.py
                         (the screens' atlases, §10), plan.py, build.py, check.py, readme.py (the root READMEs'
                         catalogue), posters.mjs, sitelib.py; its
                         workflow is .github/workflows/pages.yml
  recordings/            the recordings of the demonstrations (git-ignored; made by site/record.py): <world>/index.json
                         and <world>/<rec>.<hash8>.lfrec.gz; the atlases <world>/atlas/<atlas>/ (manifest, base,
                         points; §10); served at /recordings/ (LFVIZ_RECORDINGS overrides it)
  planned.json           the planned items of every audience (S01–S45, U01–U30, R01–R10, benches p05–p07): id,
                         audience, section, title (an English msgid), grades/curriculum, batch, state, related
  pNN_<slug>/            ONE FOLDER PER LABORATORY (playground section, plan P15; §6): the same files,
                         VIZ["audience"] = "playground" (kind "playground")
  sNN_ uNN_ rNN_<slug>/  ONE FOLDER PER VISUALIZATION, created on the owner's request; the prefix is the audience
                         (school, university, research; AGENTS.md rule 14) and the number the item's id in the plan
                         (lfphys/sources/audiences_2026-11-12_plan.md: u32_double_slit is U32). The old ids vNN_<slug>
                         (before 2026-11-13) are aliases: registry.ALIASES
    __init__.py
    viz.py               VIZ = {id, title, summary, purpose, version, schema, simulation, audience, section, ui,
                         teaser, related, recordings, screens; school: curriculum; university: courses; research:
                         question, prior_art, status} (§8)
    engine/              the apparatus logic over lfphys (Python), no drawing; physics itself lives in ../lfphys
    web/view.js          the drawing (ES module, createView(ctx)), no physics
    tests/               physics tests: every route against a closed form or a second method
    locales/             the world's catalogues: <lang>.json, msgid -> translation (§7)
    README.md            the model in full: equations, what is computed, checks, approximations, sources
    README.<lang>.md     the same in every other language of ../LANGUAGES.md (README.ru.md)
```

A new visualization is a new `sNN_`/`uNN_`/`rNN_<slug>/` folder (a laboratory `pNN_<slug>/`), its number the plan's
id of the item; the server and the player pick it up without changes (`registry.py` discovers folders and checks
their `VIZ`, §8; the start page lists them, the run page loads `web/view.js`). When the item lands, its entry in
`planned.json` is left to the site's build, which drops a planned id that exists as a folder.

**The physics engine.** Since 2026-10-23 the physics of all visualizations lives in one library, `../lfphys/`
(owner: «выделяй в отдельную библиотеку движок для физики … а отдельная симуляции или визуализации должна быть
оберткой над этим движком»). Its core holds established physics only; approximations, interpretations, models and
alternatives are separate layers (`../lfphys/LAYERS.md`, `../lfphys/README.md`). A visualization is a wrapper: its
`engine/` keeps the apparatus and the orchestration, imports the physics from `lfphys`, and lists the modules a world
uses in `Simulation.engine_modules()`; the player shows them with their layer. `engine_modules()` names modules, or one
dataset of a module as `module:part` (e.g. `core.data:air`, an entry of the module's `DATASETS`), so that the panel
lists only what the world uses (review R-W F8, integrator D10). Physics a visualization needs and the
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
     (u40, u41: an ideal preparation at the current moment, the former state discarded) is live in the same way; a law
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
   (`<id>/tests/`), all tests pass in the Docker image before the visualization is reported, and a physics review
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
    the camera window `player/js/imagewin.js` (B3, u39). A world adds only its own objects, panels and checks.
    A **2-D world** whose plane is the exact reduction of a 3-D set-up (B3: r12, slits long along y) uses the same
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
| GET | `/api/health` | version, visualizations, running workers; `restart_needed` and `changed` (the files of the engine or the framework edited on disk since the server started, §9) |
| GET | `/api/viz`, `/api/viz/{viz}` | catalogue: id, title, summary, purpose, version, `code_hash` (`registry.code_hash_current`: the world's code hash as its files are now, recomputed when a file's size or modification time changes; §9), kind, audience, section, ui, teaser, related, recordings, `screens` (`registry.screens_of`: each screen with its `atlas` id, its controls with their labels, units and kinds, a lab's instruments, steps (each with its `atlas`) and worksheet; §10), aliases, picture, the audience's anchors (curriculum / courses / question, prior_art, status), schema (params + presets) (§8); `{viz}` may be an old id (`registry.ALIASES`): the renamed world's entry; a world that does not load is `{id, title, kind, error, detail}` in the list, and `{error, text, detail}` with 500 (503: the server must be restarted, §9) for `{viz}` |
| GET | `/api/audiences` | `{audiences: [{id, prefix, label, description, ui}], sections: [{id, label}]}` from `registry.AUDIENCES` and `registry.SECTIONS`, in their order (labels and descriptions are `T`); the start page's audiences and sections (§9) |
| GET | `/api/planned` | the planned items of `planned.json` not yet built (an entry whose id names an existing folder, S02 ↔ `s02_*`, is dropped; §8) |
| GET | `/api/recordings` | `{worlds: {<world>: <its index.json>}, site: <LFVIZ_SITE_URL or https://ildar-idrisov.github.io/lfphys/>, published, expected: {<world>: {version, code_hash, recordings: {id: key}, atlases: {id: key}}}}`: the local recordings (§9), whether the public site is published (`site/site.json`), and the keys the code on this server gives (`app.expected_keys`): a screen uses only an atlas with that key (§10, integrator D11) |
| GET | `/viz/{viz}/{path}` | a world's `web/` files (its view); an old id answers 301 to the new address |
| GET | `/recordings/{world}/{file}`, `/recordings/{world}/atlas/{atlas}/{file}` | a recording file or a world's `index.json` from `visualizations/recordings/` (`LFVIZ_RECORDINGS`), or an atlas's manifest, base header or point file (§10); a `.gz` goes as `application/gzip` without a Content-Encoding (the player inflates it); `Access-Control-Allow-Origin: *`; an old id names the new folder |
| GET | `/images/{file}` | the pictures of the cards and the README, `../docs/images/` (`.jpg`, `.jpeg`, `.png`, `.webp`) |
| GET | `/`, `/runs`, `/run?id={run}`, `/run?rec={world}/{rec}`, `/run?demo={world}&screen={id}`, `/worksheet?demo={world}[&teacher=1]`, `/settings` | the pages: the start page (§9), the runs and their removal period, the player on a run, the player on a saved recording (an old world id works), a demonstration's screens (Watch, Explore, Lab work; `screen` is the tab, by default the first; §10), a lab's printable worksheet (`teacher=1`: with the teacher's answers; §10), the devices (§5) |
| POST | `/api/atlas/{world}/{atlas}/point` | «▶ Compute live» of one atlas point (§10): `{values: {param: value}, seed?, full_header?}` → `200 application/gzip`, the point's file, as a site build packs it for those values and that seed on the same CPU type; its header is a delta naming its base (`$base`, the base file's sha256), or whole with `full_header: true`; headers `X-LF-Source` (`atlas`: an on-grid value from the local atlas whose key is current; `cache`; `computed`), `X-LF-Key` (the point's key), `X-LF-Code` (the world's code hash that computed it) and `X-LF-Made` (when it was computed, ISO 8601 in UTC: a cached point's original time, an atlas's build time); a control left out takes its default; `400 {error, hint?}` for a body that is not `{values, seed?, full_header?}`, a value outside the control's span (a slider's lowest to highest value, a toggle's or select's own values) or one the schema or the world refuses (`check_params`, its memory estimate, its constructor: the refusal's texts; integrator D14); `409 {error}` when the world's checks end ✗ at those values (naming the checks); `429` beyond a queue of `atlas_live.QUEUE` (4) waiting requests; `503 {error}` when the point's process ran out of memory or time, or the server's code changed while the point was computed (`lfviz.atlas_live`) |
| GET | `/api/runs` | runs, newest first: state, sim time, size, keep, modifications, approximations, `devices_override` |
| POST | `/api/runs` | `{viz, preset?, params?, seed?, label?, backend?}` → `{id}`: starts a run (its first world; `viz` may be an old id); `backend` = `{kernels: {name: {device, precision}}}` overrides the device settings for this run only (§5) |
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
r13 includes r12, and their hash — and the runtime: Python version, bytecode magic number, NumPy, SciPy and CuPy
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
kernel on GPU 0 for u38, r12 and r13). A world's state must not rely on two attributes viewing one buffer: pickling
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
a run open in a tab is never removed. The period (whole days, 3 by default, `--keep-days`) is set on the page "My runs"
(`/runs`; owner, 2026-10-29) and kept in the runs folder (`runs/settings.json`, which wins over the option); it applies at once,
and a period that would remove runs at once is refused with their list (409) until exactly those runs are confirmed.

**The player shows the record at the cursor (owner, 2026-10-28).** ⏮ ◀ ▶ ⏭ and the timeline move along the history
(◀ / ▶ play it at the chosen speed); with the cursor at the end a recording is shown live. Whatever is shown is the
state at the cursor's time: the view is fed the record's messages up to that time and, when the cursor goes back,
brought back from its nearest **key frame** before the cursor (owner, 2026-10-29: «для воспроизведения назад давай как в
видео добавлять ключевые кадры»): every 100 messages fed in order the player asks the view for `snapshot()` (the lengths
of its growing lists, references to the latest values, copies of small changing state) and, going back, calls
`restore(snapshot)` on the view's present state and feeds only the messages after the key frame; at most 256 key
frames per world: beyond, the step between them doubles and the key frames on the coarser grid are kept (uniform over
the whole record at any length). A view without `snapshot`/`restore` (u40, u41: their clouds are decoded
asynchronously), or a `restore` that cannot cut back (it throws: u37 once its cap dropped the oldest detections; r12 and
r13 for a key frame from before their latest change of the set-up; the 3-D environment for a target set or a slice
computed after the key frame), is rebuilt from the record (`reset` → `onHeader` with the header as recorded → the
messages up to the time). The 3-D environment's part (`env3d.snapshot`/`restore`): the latest message that set each
object (re-applied in the record's order, the box first; the slices of the planes re-applied with them), and the
lengths of the appending layers (paths, tracks with their segments' colours, triads), cut back by
`scene3d.restoreAppends`. Tested in the browser for every visualization by `tests/browser/keyframes.mjs` (key frames
every 3 messages; live changes, actions, slice planes added and removed in the middle of the record, the page opened at
its end, r11 also in ordinary space where the box grows): the view brought back through a key frame equals the view
rebuilt from the record at the same cursor (the 2-D canvases' pixels, drawn in software and once more before they are
read; the 3-D scene's layers, sphere radii, slice planes and their images, the scene's box; the panels' and overlays'
texts). The scene keeps a copy of the header's scene description (`setBox`, `setObject` change it), so that a view
rebuilt at an earlier time starts from the header as recorded; a view rebuilt for the same world keeps what the
experimenter chose in it (u31: the frame, the camera, the zoom). Every
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
  says why (`start_error`), and so do the run list (`error`) and the start page's card.
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
| `header` | first in every world | scene, actions (forms), modifications, approximations (optional, list of strings), units, anything static; added by the runner: `world`, `params`, `preset`, `seed`, `live`, `engine` (the lfphys modules of the world, `engine_modules()` with their ABOUT; a `module:part` name gives that dataset's own entry), `backend` (the device settings in force, what each engine kernel ran on so far — `used[kernel].drawn` for the results drawn, `used[kernel].check` for references and checks — and the engine's notes about adjusted settings; plan P11) |
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

### 3-D worlds (rule 2.10; `u38_wave_3d` and `r11_thomas_3d` are the reference implementations)

The header carries `scene3d`: `box` [[xmin, ymin, zmin], [xmax, ymax, zmax]] (physics coordinates, z the depth),
`units`, `coord_names` (optional, e.g. ["βx", "βy", "βz"]), `views` (optional camera buttons `[name, label, title]`,
names iso / side / top / beam / back), `objects` (each `{id, label, kind, visible, ...}`: `plate` with `holes`
(`rect` / `circle`), `disk`, `incident`, `target`, `sphere` (`center`, `radius`), `point` (`pos`, `text`), `panel` (B3, r12: a computed field on a rectangle of any orientation, `origin` (a corner), `u`, `v` (its edges), `opacity?`; its image is set by the world's view, `scene3d.setPanelImage`), `box` (B4, r12: a translucent box with edges, `center`, `size` [sx, sy, sz], `color?`, `opacity?`, `text?`, `text_size?` — e.g. the observer at slit B; a world replaces it with `scene3d.setObject`); the player
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
| `mesh` | (B3, u39) a surface computed by the run: `id`, `label`, `count`, `opacity?`, `visible?`, `base` ("lab": absolute vertices; "rest": offsets placed by an affine map from the frames, `scene3d.transformMesh(id, A, b)`); blobs `pos` (float32 count × 3), `idx` (uint32 triangles), `rgb` (uint8 count × 3, sRGB); a world may replace a "lab" mesh's vertices and colours later (`scene3d.updateMesh`) |
| `image` | (B3, u39; drawn by the shared camera window `player/js/imagewin.js`, not by env3d) what an observer sees: `seq`, `shape` [H, W], `camera` {kind, fov, forward}, `mode`, `mode_label` (a mode that is not what is seen is marked in the window), `codec: "deflate"` and `filter` (fields sent as row differences); blobs deflated: `rgb` (uint8 H × W × 3) and the world's per-pixel fields for the readout (u39: `D`, `delay`, `T`, `body`); frames name the image they show (`img_seq`) |
| `wave` | (B3, r12) a 2-D world's wave on its plane: `shape` [nx, nz], `peak`, `ds` (grid steps per pixel), `tau`; blobs `amp` (uint16, √(\|ψ\|²/peak)·65535) and `phase` (uint8, (arg ψ + π)/2π·255); accumulative, so that the record keeps every image and a viewer who scrolls back sees the wave of that moment (frames are thinned); drawn on a `panel` object and in a slice window marked `fixed` (not removable; `meta.fixed`, `meta.title`) with the world's overlay (`slices.setOverlay(id, fn(ctx, map))`: computed polylines drawn in the plane's coordinates) |
| `cloud` | (B4, u40/u41; server `lfviz/orbitals3d.py`, view `player/js/orbitview.js`) a probability cloud \|ψ\|² for the scene's volume: `id`, `bin`, `nb`, `t_bin`, `dims` [nz, nx, ny], `peak` (one scale for all phases: (Σ_k \|c_k\|\|ψ_k\|)² maximised over the grid, a bound of \|ψ(t)\|² at every t known without evolving; review B4-10), `enc: "sqrt-u8"`, `codec: "deflate"`; blob `data` (deflated uint8 √(\|ψ\|²/peak)·255, index as `volume`). A time-dependent cloud that repeats with a period T comes in `nb` phases, each revealed when the run's time reaches it; `vectors` and `slice` messages of such a world carry the same `bin` (and slices a `rev` per placement of their plane); frames name the phase they show (`bin`: the last one reached), so the record stops growing after one period and a viewer who scrolls back sees that moment's cloud. Shown with `scene3d.updateVolume(id, data)` (same dims: texture and mesh kept) |
| `prepared` | (u40, u41) a state prepared at the current moment: `t_prep`, `keep_time`, `header` (the header's parts that describe the state: title, states, levels, period, nb, scene3d …); the view starts its state from the world's header with them; frames carry `t_prep`, the period's phases count from it |

Since B3 the scene also draws many computed polylines at once (`scene3d.appendTracks(id, xyz, colours)`, NaN where a
track has ended; `setTrackColors` recolours whole tracks, e.g. when a Bohm particle's slit becomes known), a point
cloud replaced on every frame (`setPoints`) and an object rebuilt after a live change of the apparatus (`setObject`,
e.g. r12's plate when a slit is closed); r12's own messages (`tracks`, `hits`, `screen`, `result`, `setup`) feed them.
A moving body (e.g. r11's craft: its position, gyroscope frame, spin, thrust) is drawn by the world's view from the
frames (`scene3d.setBody`); an observer (a marker, its velocity, the lab directions of its field of view) by
`scene3d.setObserver` (u39). View commands: `view {op: "plane", id, origin?, normal?, auto?, speed?}` places or moves
plane `id` (1–3); `view {op: "remove", id}` removes it; `view {op: "reset"}` restores the default planes; `view {op:
"preview", id, origin, normal}` (while a plane is dragged and no volume was computed) answers with a coarse `slice`
marked `preview` that changes nothing (not kept, not checked). A plane's in-plane axes are the engine's
(`lfphys.core.geometry.Plane.horizontal`: u horizontal, v towards the depth); its cut by the box is
`lfphys.core.geometry.plane_cut`. The player sends `view` only for the current world (a world from the record is
read-only).

## 4. How to add a visualization (checklist for agents)

1. Create `<a>NN_<slug>/` (§1: the audience's prefix and the plan's id) with the files of §1 and the fields of §8. `viz.py`: a `Schema` of world parameters (laws marked `standard`),
   presets, and a `Simulation` subclass of `lfviz.sim.Simulation` implementing `header`, `advance`, `frame`,
   `action`, `next_event_time` (and `after_header` if it emits messages while constructing the world).
2. Physics from the engine `../lfphys/` (add what is missing there, in the right layer, with tests); the
   visualization's `engine/` holds the apparatus logic, `engine_modules()` lists what a world uses; drawing only in
   `web/view.js`. The view may interpolate along computed polylines and apply matrices the run sent; it computes no
   physics.
3. Emit checks for every quantity that has a closed form; state approximations; flag modifications.
4. Tests in `<id>/tests/`; run all tests in Docker (`README.md`); look at the pages in a browser (headless
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
8. A demonstration declares its recordings (§8 `recordings`), records them (`site/record.py --world <id>`, §9), gets
   its picture (`site/posters.mjs`) and its rows in the root READMEs (`site/readme.py`); `tests/test_site_registry.py`
   fails until all of that is in place.
9. A school demonstration (and a university one when it is reworked) declares its screens (§10: Watch only for a
   phenomenon that develops in time, Explore, Lab work), builds their atlases with its recordings, and passes
   `tests/browser/demo_screens.mjs <port> [sizes] <world>` in EN and RU at 1280 and 390 px.

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

The start page has the demonstrations by audience (the `sNN_`, `uNN_`, `rNN_` folders: prepared set-ups with their
checks and story) and the **Laboratories** (the `pNN_` folders, one per branch of physics; `/#labs`; §9). The interface calls a playground a *laboratory*
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
  - **Nothing is rebuilt while the owner is using it** (review LB1-framework F8): the list, the folded groups (kept per
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
  msgid carries its marker, and that no server code `str()`s a text. The static scan also takes the msgids of the data files
  (`planned.json`: `title`, `text`) and those named in an `i18n-msgids:` marker list, so that the warning about the
  catalogue entries no code uses lists none, or only the few it explains; an entry no longer used is removed. `tests/i18n_pending.txt` lists files not yet
  converted and must be empty at a commit. `tests/i18n_tools.py --lines FILE… | --pending | --shadow` shows what the
  guard refuses and where a local hides `t()`. In a browser, `tests/browser/i18n_checks.mjs` opens every page and
  every world in English and in Russian. The other browser scripts take the language from `-e LFVIZ_LANG=en|ru`; they
  import `lfi18n.mjs`, so they are copied together (`cp /t/*.mjs /pw/`). The player's JS unit tests:
  `node --test player/js/tests/*.test.mjs` (from `visualizations/`, Node 22 or newer, e.g. the `node:24` image).
* **Glossary (owner and integrator, 2026-11-13).** One word per concept in each language, in the interface and in the
  user documents: the free labs are "laboratory" / «лаборатория» (never "playground", "sandbox", «плейграунд»,
  «песочница» in a user text); a saved file that plays without computing is a "recording" / «запись» (its tab «… ·
  запись»); a live computation is a "run" / «запуск», its state while it computes "computing" / «идёт расчёт» (its tab
  «… · идёт расчёт», the «Continue» strip and "My runs" say so), and what ⏺ adds to is the run's "record" / «запись
  запуска» — never "recording" for a live run (integrator D1, 2026-11-13; review P17-start-page F3); "MODIFIED PHYSICS" / «МОДИФИЦИРОВАННАЯ ФИЗИКА» in full; a parameter sweep is «перебор
  параметра»; a worker is «рабочий процесс»; a numerical error is «погрешность» (a fault stays «ошибка»); "closed form"
  is «в замкнутом виде» (in a school text «по формуле»); a random seed is «затравка» (never «зерно»); the lab's fit
  of the measured points is «аппроксимация» (not «подгонка»; 2026-11-17, review R-W F13); "against" is rendered by sense («в сравнении с», «в зависимости от», «↔»), not «против»;
  «2D»/«3D» and the decimal comma in Russian; British spelling and "2-D"/"3-D" in English. Every count phrase has
  plural forms (`{n:d}` and the catalogue's plural entry; English one/other in `en.json` where English needs it), and
  no ordinal is built as "{k}th". A button is named by its label ("▶ Start a new world", not "New world"). The screens
  of a demonstration (2026-11-14, §10) are "Watch" / «Наблюдение», "Explore" / «Исследование» and "Lab work" /
  «Лабораторная работа» — never «Демонстрация» or «Смотреть» for a screen (the whole item is a demonstration); the
  precomputed points are an "atlas" / «атлас»; a point computed on a server is "computed live" / «расчёт вживую» and
  "▶ Compute live" / «▶ Рассчитать вживую» starts one; the drawer is "How we know this is right" / «Почему этому можно
  верить»; the printable sheet is a "worksheet" / «рабочий лист», its answers "For the teacher" / «Для учителя».
* **User documents.** A world's README and the owner guide exist as `README.md` (English) and `README.<lang>.md` for
  every other language, each linking the other at the top. A document names a part of the interface by its label in
  the document's language: the msgid in an English document, its translation from the catalogues in another. A quoted
  label is quoted exactly as the interface shows it, its unit included: "Position, nm", not "Position" (owner,
  2026-11-14).
* **Adding a language.** A row in `../LANGUAGES.md`; its code in `LANGS` of `lfviz/i18n.py` and of
  `player/js/i18n.js`; a `locales/<code>.json` next to every catalogue (`tests/test_i18n.py` lists what is missing);
  and `X.<code>.md` for every user document.

## 8. Audiences, the registry's fields and the planned items (owner, 2026-11-12 and 2026-11-13)

Four audiences, one per visualization (`../AGENTS.md` §3 rule 14): **school** (`sNN_`), **university** (`uNN_`),
**research** (`rNN_`), **laboratories** (`pNN_`, internally `playground`). The number is the item's id in the plan
(`../lfphys/sources/audiences_2026-11-12_plan.md`; owner, 2026-11-13: «Номер = id в плане»): today's university worlds
are U31–U44, the research worlds R11–R13; S01–S45, U01–U30 and R01–R10 keep their plan ids when they land. The old
ids (`v01_light_travel` … `v17_mie_scattering`) are aliases (`registry.ALIASES`): `registry.folder/load/describe`,
`/viz/<old>/…` (301), `/api/viz/<old>`, `POST /api/runs {viz: <old>}` and the run records (`runs.py` maps
`meta.json`'s `viz` at load and notes `viz_alias`; such a run resumes by replay, its checkpoints naming the old
folder's files). The archived reviews keep the old ids as written.

| old | new | old | new | old | new |
|---|---|---|---|---|---|
| v01_light_travel | u31_light_travel | v07_bell_test | u37_bell_test | v14_quarkonium_3d | u41_quarkonium_3d |
| v02_double_slit | u32_double_slit | v08_wave_3d | u38_wave_3d | v15_kerr_shadow | u42_kerr_shadow |
| v03_quantum_1d | u33_quantum_1d | v10_fast_observer | u39_fast_observer | v16_optical_vortices | u43_optical_vortices |
| v04_orbits | u34_orbits | v13_hydrogen_3d | u40_hydrogen_3d | v17_mie_scattering | u44_mie_scattering |
| v05_optics_bench | u35_optics_bench | v09_thomas_3d | r11_thomas_3d | v11_double_slit_2d | r12_double_slit_2d |
| v06_qcd | u36_qcd | v12_arrival_times_2d | r13_arrival_times_2d | | |

`VIZ` declares, besides §1, and `registry.load` checks (`registry.check`; `tests/test_site_registry.py`):

| field | meaning |
|---|---|
| `audience` | `school` \| `university` \| `research` \| `playground`; it agrees with the prefix; `kind` follows from it |
| `section` | one of `registry.SECTIONS` (the teaching order of the plan's §5.1: mechanics … astrophysics and cosmology) |
| `ui` | `school` \| `standard` \| `full`, by default the audience's (`registry.AUDIENCES`); `school` for the school only |
| `teaser` | a `T`: one line, what you will see |
| `related` | the same topic at other levels: world ids or planned ids (`S38`, `U27`, `R10`, `p05`); mutual between them |
| school | `curriculum` (an FRP anchor and an AP/IB/AQA anchor: `{system, grade \| unit \| topic \| section}`); `screens` with Explore and Lab work (or `lab_absent`: a `T`, why the programme has no lab for the topic); no law parameters (no modified physics). The former `guide` (guided steps) is retired: the lab's steps replace it (2026-11-14) |
| university | `courses`: `[{text: T(the book), chapters}]` |
| research | `question` (a `T`), `prior_art` (`[{ref, url}]`), `status: "hypothesis"` until reproduced (`../AGENTS.md` rule 11) |
| `recordings` | not for the laboratories, at least one: what the public site plays (`[{id, preset, seconds, fps, speed?, seed?, script?, poster?, captions?, quantize?}]`; `registry.RECORDING_LIMITS`: 1–180 s, 1–30 fps, ≤ 3600 frames, script commands `set`, `action`, `view`, `new_world`, `speed` (the playback speed only; a `new_world` resets the speed to the world's default, so a `speed` after it at the same `at`); `captions` `[{at, text: T, hold?}]` and `quantize` as in §10); chosen so that each file stays within the site's budget (3 MB target, 10 MB limit; a world 12 MB, 25 MB limit, its atlases included) at the measured rates (`tests/test_site_registry.py` `RATE_KB`) |
| `screens` | school and university (optional for a university world until it is reworked; none for research and the laboratories): the demonstration's Watch, Explore and Lab work in tab order, `[{id, kind: watch \| explore \| lab, label?, …}]`; their fields, limits and checks are §10 (`registry.check_screens`, catalogue form `screens_of`, atlases `atlases_of`) |

`planned.json` lists the items not built yet (school S01–S45, university U01–U30, research R01–R10, the benches
p05–p07): `id`, `audience`, `section`, `title` (an English msgid translated in `locales/`), and per audience `grades`
and `curriculum`, `priority`, `rank` and `status`, `text`; `batch` and `state` (`next` for the batch in work,
`planned` for the rest); `related`. The start page and the site show them as planned, never as startable; the site's
build drops an entry whose id exists as a folder.

## 9. The start page, the recordings and the public site (owner, 2026-11-12 and 2026-11-13; plan P17.1)

The rules for the whole repository are `../AGENTS.md` §3 rules 14–16 (one audience per item; learning materials by
audience; demonstrations on the public site from recordings), with the owner's words in `../AGENTS.md` §1; the plan is
`../lfphys/PLAN.md` P17.1 and `../lfphys/sources/audiences_2026-11-12_plan.md`. This section is what the code keeps.

**The start page** (`player/index.html`, `player/js/start.js`). One page with hash routes, the same files on the
server and on the site:

| route | shows |
|---|---|
| `#` | the four audiences (`/api/audiences`), each with its count and a picture of one of its worlds; on the server "Continue" (the last runs open or paused) |
| `#school` | the school course by section or by grade: the ready worlds (S03 since 2026-11-14) with their screens, and the planned items (`/api/planned`), honestly («Ready: k of n»), with the worlds of another level on the same topic |
| `#university`, `#research` | the worlds by section in teaching order, section chips with counts, a search box; the planned items folded at the end of their section, or under "Planned in other sections"; a research card shows its question, "Status: hypothesis" and its prior art |
| `#labs` | the laboratories: on the server today's cards ("▶ Begin", "Laws…", "📂 From a scene file…"); on the site greyed with "Works only with a running server"; the old `#playground` is redirected here |
| `#<audience>/<id>` | the same page with that card in view |

A card's buttons: "▶ Compute live" (server: `POST /api/runs`, then the player) and "▷ Recording m:ss", enabled only
for a local recording or, when `site/site.json` says `"published": true`, for the public site's recording of the same
world `version` (`start.js` reads `<site>api/recordings.json` once); otherwise it is disabled with "No recording yet:
record it locally (site/record.py) or compute live" (integrator D4). "No recording for this scenario: compute it live"
is only for a preset with no recording spec. A world with screens (§10) shows them first, in tab order: «▷ Watch m:ss»,
«◎ Explore», «✎ Lab work» (`page("run", {demo, screen})`, class `st-screen`), each greyed with "Not built here: run
site/record.py --world <id>" while its recording or atlases are missing here or not of the key this server expects (and
not on the published site with that key; §10, integrator D11); a school card has only these
and, on a server, «▶ Compute live» of its Explore screen's set-up. The lower the level, the simpler the card (rule 16):
school cards have no parameters, seed or devices; university cards fold them under "More: parameters, seed, device,
precision"; research cards show them open. The runs are not on the start page: `/runs` (`player/runs.html`,
`js/runs.js`) has the list and the removal period. The audiences' and sections' labels come from the registry through
`apiGet("audiences")`; nothing in the player repeats them.

**The code the server process holds (2026-11-18; the owner's server, started before S03 existed, listed it as "Not
loaded: … AttributeError: module 'lfphys.core.data' has no attribute 'P_ATM'").** Workers, sweeps and live points are
new processes and run the code on disk; the server process imports the engine and the framework at its start and a
world's `viz.py` when it is first asked for. `RunManager.viz` (`runs.py`) keeps a loaded world while its own Python files
and those of the worlds it imports (r13 imports r12) keep their paths, sizes and times; when they change, it drops those
packages from `sys.modules` (`<id>`, `<id>.*`) and imports them anew, so the catalogue follows a world's edit without a
restart (the expected keys of `/api/recordings` and «Compute live» read the world through it too). The engine
(`lfphys/lfphys/**/*.py`), the framework (`server/lfviz/*.py`, its server-only modules included: their edits also take
effect only after a restart), `server/serve.py` and `site/sitelib.py` cannot be imported again in place: their
signature is taken when the server starts and compared at every `/api/health` and at every world that fails to load
(`RunManager.code_changed`). When it differs, `/api/health` says `restart_needed: true` and lists the files (`changed`),
the start page shows the banner "The server's code changed on disk after it started: restart the server (docker
restart lf-viz)." (from `/api/health`, polled every 3 s), and a world that fails to load is listed under "Not loaded:"
with "the visualization does not load: the server's code changed on disk after it started: restart the server" (a `T`;
`runs.NotLoaded`) and the exception's own line in `detail`, folded under "details" (`/api/viz/<id>` and `POST
/api/runs`: 503 with the same). Any other failure keeps its own text, the exception's line also in `detail`. Tests:
`tests/test_server_reload.py`.

**Ids and aliases.** §8: the prefix is the audience, the number the plan's id; the old `vNN_` ids are aliases
everywhere an id is taken (URLs, `/api/viz/<old>`, `?rec=<old>/<rec>`, run records). The site carries `aliases.json`
(`registry.ALIASES`) for the player's `?rec=` with an old id.

**Recordings.** A demonstration's `VIZ["recordings"]` (§8) lists what the site plays. `site/record.py` runs each spec
headless (`lfviz.sim.Runner`) on a frame clock of its own: exactly `seconds × fps` frames, the script's commands at
their frames, no wall-time budget, `checkpoint`/`command`/`resumed`/`record_segment` dropped. **The same spec recorded
by the same code gives the same bytes** (integrator D6; `tests/test_recorder.py`): the frames carry no `cpu_ms` and no
`speed_actual` (the CPU time is the index entry's total `cpu_s`), and the header's kernels (`backend.used`) are reset
for each recording. A seeded stochastic recording is one realisation: a live run with the same seed draws on its own
frame clock and shows another realisation with the same statistics (review P17-site F11). **A recording fails** on an
error of the world, an exception, or a check whose last state is ✗ (as the player draws it; a check marked
`expected` is a ✗ on purpose and does not fail); its index entry counts the checks' last states (`checks`: ok, failed,
expected, info, na) and `site/check.py` fails a site whose entry counts a failed one (integrator D5); over the target size the frames are thinned by a stride (the first, the last and the poster frame always
kept, never under 2 frames per played second), over the hard limit the recording fails (`sitelib.BUDGET`: a file 3 MB
target / 10 MB limit, a world 12 / 25 MB, gzip, decimal; the exceptions accepted over target with their reasons are
`sitelib.ACCEPTED`). Output per world: `recordings/<world>/<rec>.<hash8>.lfrec.gz` and `index.json` (`{world, version,
recorder, recorder_hash, code_hash, made, recordings: [{id, preset, label, file, seconds, fps, frame_stride, frames,
frames_recorded, bytes, bytes_gz, poster_t, poster_frame, worlds, checks, cpu_s, sha256, key, version, code_hash,
made, …}]}`; `site/README.md`). Each entry carries its own `version`, `code_hash` and `made` (the player prefers them);
a recording not made now keeps its old entry only when its key is still the current one (review F9). After the
recordings, `site/record.py` builds the world's atlases (`site/atlas.py`, §10) into `recordings/<world>/atlas/` and
lists them in the same `index.json` (`atlases`); `--stale` re-records a world whose recordings or atlases are not all
present, and the world's budget counts both.

* **The key** of a recording is `sha256(spec + RECORDER_VERSION + sitelib.recorder_hash() +
  registry.code_hash(world))[:16]`; `recorder_hash` covers `site/record.py`, the image's
  `docker/requirements.lock` and `Dockerfile` (whose base image is pinned by digest, the same as the workflow's
  `PY_SLIM`: review R-F F10, 2026-11-17), and the budgets that decide the thinning (review F3); `plan.py` marks
  each `present`, `stale` or `missing`. `code_hash` covers the world's folder (`*.py`, `*.js`, not its `tests/`),
  `server/lfviz/` and the engine, except `registry.SERVER_ONLY` (`app.py`, `runs.py`, `atlas_live.py`: the server
  process's own modules, which no worker imports; the live points' key covers `atlas_live.py` itself, §10), so an edit
  of an HTTP route, of the runs' bookkeeping or of the live endpoint re-records nothing; an edit of
  `sim.py`, of the engine or of a world's file makes that world's (or every world's) recordings stale.
* **Recording locally** (Docker, CPU, a memory cap; at most a few containers at once on a shared host):
  `docker run --rm --memory=12g -e LFPHYS_NO_GPU=1 --user "$(id -u):$(id -g)" -v "$PWD:/lf" -w /lf/visualizations
  lfphys-viz python3 site/record.py --stale` (or `--world <id>`, `--all`, `--rec <id>`, `--out DIR`). Then
  `site/posters.mjs` remakes the pictures whose recording's key changed (`../docs/images/posters.json`), and
  `site/readme.py` the READMEs' catalogue.
* **On the server**, `/recordings/…` serves `visualizations/recordings/` (git-ignored; `LFVIZ_RECORDINGS` points
  elsewhere) and `/api/recordings` lists it with the public site's address, whether it is published and the keys the
  code on this server gives (`{worlds, site, published, expected}`; **`site/site.json`** `{"published": false, "url": …}`, committed; `LFVIZ_SITE_URL`
  overrides the address). Without a local recording of a world the player falls back to the public site's (Pages sends
  `Access-Control-Allow-Origin: *`) only when `published` is true and that index's `version` equals the local world's
  (integrator D3, D4); a screen's atlas is taken from there only with the key this server expects (§10, integrator
  D11). The player's refusals: "No such recording" (an unknown world or recording; the only one on the
  site), "No recording yet: …", "The public site could not be reached: …", and "No recording for this version: …"
  only for a real version mismatch.
* **The player on a recording** (`/run?rec=<world>/<rec>`; `api.js openRecording`, the handler interface of
  `connectRun`): the file's messages are wrapped in the player's own `history_start {frame_stride}` / `history_end`,
  so it is an ended record. `S.recording` hides ⏺, "Keep" and "⚙"; `editBlock()` and the views' `ctx.readOnly()`
  give the reason "a recording: this needs a live run" (the set-up, the actions, new worlds, adding slice planes); the
  passport ("About the recording") is built from the index entry; the instruments' CSV is made in the browser from
  the kept frames, and the sweeps are absent. The badge "RECORDING · date · code X" compares the index's `code_hash`
  with this server's (`describe()["code_hash"]`, `registry.code_hash_current`, by the code files' sizes and times) and, when they
  differ, its tooltip says "recorded with code X; this server runs Y" (design §4.6); the badge prefers the index
  entry's own `code_hash` and `made`. A view's `ctx.send("speed")` sets the player's own speed; any other view command
  gives the read-only toast. Below 1000 px the player is one scrolling column: the view first, the side columns under
  it, a sticky transport, and a wrapping top bar that keeps the badge (integrator D8). The tab title is "{title} ·
  recording" (D1). On the server "▶ Compute this scenario live" starts a run of the same scenario. In static mode,
  `?id=…` or no query says "This site plays recordings; runs are computed by a local server", with the ways to the
  start page and the quick start (start-page F12).

**The same files on the server and on the site** (`player/js/base.js`, re-exported by `api.js`). Every player page
carries `<meta name="lf-mode" content="server">`, `<meta name="lf-base" content="/">` and one import map (`three`,
`/static/`, `/viz/`); stylesheets and entry scripts are relative (`static/assets/…`, `static/js/…`). `MODE`, `BASE`,
`url(path)` and `page(name, query)` build every fetch, href and location: `page("run", {rec})` is `/run?rec=…` on the
server and `<base>run.html?rec=…` on the site. `apiGet(name)` reads `/api/<name>` on the server and
`<base>api/<name>.json` on the site for `viz`, `viz/<id>`, `audiences`, `planned`, `recordings` and `health`. A link
in a page's HTML names its target by `data-page`; one marked `data-server-only` (the runs, the devices) is removed on
the site. A view never writes an absolute path: it imports through the import map (`/static/js/…`) and links with
`page()`; a server-only link (the views' "⚙ Devices") is shown only when `MODE === "server"`.

**The site build** (`site/build.py --recordings DIR --out DIR --base /lfphys/`) writes `index.html`, `run.html`,
`legal.html`, `worksheet.html`, `404.html` (the metas set to `static` and the base, the import map's targets relative), `static/` (the
player and `static/locales/<lang>.json`), `viz/<id>/` (each world's `web/`), `api/viz.json`, `api/viz/<id>.json` (also
under each old id), `api/audiences.json`, `api/planned.json`, `api/recordings.json`, `api/health.json` (the citation),
`aliases.json`, `recordings/` (the atlases under `recordings/<world>/atlas/`), `images/`, `legal/<name>` and
`site-manifest.json` (every file's size and sha256; every world, recording and atlas with its key). `site/check.py SITE
--base /lfphys/` fails on a world, recording or atlas missing or stale (an atlas's manifest against its files: sizes,
sha256, the base, the refusals; a point or an atlas over its hard limit; a check that ends failed),
a file that differs from the manifest, a page without its metas or import map or with an absolute `/static`, `/api` or
`/viz` outside the map, a missing catalogue, audiences or i18n file, or a hard limit exceeded; over a target it warns
(the accepted ones say so). `tests/browser/site_smoke.mjs` serves the built site with `python -m http.server` under
`/lfphys/` and checks that no request leaves the sub-path or goes to `/api/`, that the start page and an audience page
render in EN and RU, that a recording plays (the timeline moves, the checks appear, the canvas is drawn), that the
laboratories are greyed with their note, the school banner is honest, every screen of every world with screens opens
(§10) and a lab's worksheet renders, and `legal.html` shows the texts.

**What `site/check.py` also checks** (review F5, F13): every catalogue world's `viz/<id>/view.js` and every named
picture's `images/<id>.jpg`; no absolute server address (`"/api…"`, `"/run…"`, `"/runs…"`, `"/settings…"`,
`"/legal…"`, `"/recordings…"`, `"/images…"`, `"/ws…"`) in a string literal of `static/**/*.js` or `viz/**/*.js`;
`api/recordings.json` agrees with `site/site.json`. It warns on an index entry or a file the registry does not ask
for; `build.py` copies only the entries the registry asks for. `site_smoke.mjs` plays **every** recording (its frames
are the index's, the poster frame shows `poster_t`), an old id, an unknown id (said, with a link to the start page),
and `run.html?id=…` (the site says it plays recordings only).

**The README's links to the site** (integrator D3, review F6, F7). While `site/site.json` says `"published": false`
the generated catalogue names each world's recordings without links, and one line says, in the README's language,
that the public site is being prepared and the recordings play on a local server. When the owner publishes the site
he sets `"published": true` and runs `site/readme.py`: every recording is linked, `run.html?rec=<world>/<rec>`, with
`&lang=<code>` in a README of a language other than the default (the player does not follow the browser's language;
integrator D7). `tests/test_site_registry.py` checks both states and that the committed READMEs match the committed
setting.

**CI and publication.** `.github/workflows/pages.yml` is the site's workflow (check → record per world, cached by the key → build,
check, smoke test → deploy to GitHub Pages), every action pinned to a commit SHA with its tag in a comment, recording
in CI on the CPU. It is active since 2026-11-14, on the owner's go, with Pages' source "GitHub Actions". Whether the site is
published, and so whether the README links to it, is `site/site.json`. In the workflow (integrator D2, D5): `check`, `viz-tests` (the whole visualizations
suite, in shards) and `engine-tests` (the engine's suite) run in parallel; `record` runs only after all three; a push to
`main` checks, records and builds, and **the deploy job runs only when the workflow is started by hand
(`workflow_dispatch`) with `deploy: true`**, the owner's go.

**Tests.** `tests/test_site_registry.py` (the registry's fields, aliases, recording specs within limits, related links,
translations of every `T`, the READMEs' generated sections up to date, a picture per world; `registry.SERVER_ONLY`
kept out of `code_hash`), `tests/test_recorder.py`, `tests/test_site_build.py`, `tests/test_aliases.py`; in a browser
`tests/browser/start_page.mjs` (with the cards' screen buttons), `record_mode.mjs`, `demo_screens.mjs <port> [sizes]
[world]` (a world's screens: the toy `s98_atlas_toy`, `s03_projectile`, `u32_double_slit`; §10) (against a private server
with the local recordings) and `site_smoke.mjs` (on a built site); `node --test player/js/tests/*.test.mjs` (`record.test.mjs`: a gzip fixture
decoded through `openRecording`).

## 10. Screens and atlases (owner, 2026-11-14; plan P17.5, batch EX1)

The owner's words are in `../AGENTS.md` §1 («Interactive explorations and lab work for school and university»), with the owner's
answers of the same day: sliders snap only to computed points, nothing between them is drawn; the pilots and the
rework of the existing worlds come before AB1; quality over quantity. The design and its measurements:
`../lfphys/sources/explore_2026-11-14_design.md`. The pilots: `s03_projectile` (all three screens) and
`u32_double_slit` (Watch and Explore). This section is what the code keeps.

**Three screens on one model.** A school or university demonstration may have, as tabs of one page
(`run.html?demo=<world>&screen=<id>` on the site, `/run?demo=…` on a server; `player/js/demo.js`):

* **Watch** («Наблюдение»): a recording of `VIZ["recordings"]` with captions, only for a phenomenon that develops in
  time. The caption strip shows the latest caption as of the cursor; each caption is a chapter tick on the timeline,
  ◀◀ / ▶▶ go to the previous or next one; the screen's `more` recordings are a select («More recordings»;
  `player/js/watch.js`). Its time label states the world's time and the playback factor («world 0.42 s · slow motion
  ×10 · 6.50 s / 39.95 s»), so a view does not repeat it (integrator D8).
* **Explore** («Исследование»): an **atlas**, the world's own runs computed beforehand on a grid of a few controls. The
  sliders stop only at the grid's values on the site; the world's own view draws the point (`player/js/explore.js`,
  `atlas.js`, `record_core.js`).
* **Lab work** («Лабораторная работа»): steps, each on its own atlas, with instruments, «Measure», a table, a plot, a
  fit and «Check against the law», and a printable worksheet (`player/js/lab.js`, `fit.js`, `worksheet.js`).

Checks, «Physics of this world», events and the passport fold into one drawer, «How we know this is right» (a view's
`rightPanels`, u32's «Particle», «Model of the slit screen» …, fold into it too). On a server the top bar also has
«▶ Compute live»: a live run of the screen's preset with the controls' current values, in the full player (on Watch,
of the world shown: its preset, parameters and seed from that world's header; review R-P F13). A world
without screens opens its first recording, as before. School worlds need Explore and Lab work (or `lab_absent`);
a university world's screens are optional until it is reworked; research worlds and the laboratories have none and
keep the full player only. The layout is PhET-like and works at 390 px (one column, touch targets ≥ 44 px, no
horizontal scroll). Below 1000 px the top bar scrolls away; Explore's and Lab work's view stays at the top (sticky)
while the controls scroll under it, the time bar stays at the bottom, and in Lab work «Measure», the stopwatch's
«⏱ Stop» and the last message sit in a sticky dock above it; the page's scroll padding equals the sticky parts'
heights, so a control the focus or a tap scrolls into view is not hidden under them (integrator D12). **Keys:** Space,
← / → and Home are the screen's shortcuts only when the focus is not on an interactive control (a button, a slider, an
input, a select, a tab, a link); on a button Space presses it, on a slider the arrows move it, and the tabs move with
← / → among themselves (ARIA tabs); T, ? and Escape work anywhere but in a text field (integrator D7).

**`VIZ["screens"]`** (`registry.check_screens`; the catalogue's form `screens_of`; every text a `T`):

| kind | fields |
|---|---|
| all | `id` (a slug, unique), `kind`, `label?` (by default «Watch», «Explore», «Lab work») |
| `watch` | `recording`: a recording id whose spec has `captions`; `more?`: other recording ids for «More recordings» |
| `explore` | `preset`, `fixed?` (values on top of the preset, shown, not controls), `controls` (below), `acts` (`next`: a change arms the next launch; `now`: the shown point is replaced, the time kept), `time` (`flight`: ▶ Launch from t = 0; `buildup`: the cursor is the build-up, u32's hits; `none`: static), `frame_dt` (world seconds between frames), `stop` (`{event, after_s, max_world_s}` or `{world_s}`), `drop?` (`{types, frame_blobs}`: what the screen does not draw), `quantize?`, `overlays?` (ids the view declares), `traces` (0–5 earlier points kept, fading), `readouts?` (measurables of the world's header, shown once their event is reached, «—» before), `seed?` (1) |
| `lab` | `instruments`, `steps`, `worksheet` (below) |

A **control** is `{param, values, default, label?, unit?}`: a parameter of the schema and its grid values (2–… per
control, at most 5 controls at school and 6 at standard, at most 1500 points as the target and 3000 as the limit per
atlas: `registry.ATLAS_LIMITS`); two booleans make a toggle, other non-numbers a select. Its own `label` and `unit` (a
`T`, or a plain symbol such as "nm") win over the parameter's, so that a schema label carrying its unit ("Wavelength,
nm") becomes «λ 600 nm» (u32's λ, d, a). A school screen has no law parameter among its controls (rule 4); a standard
screen may have one, flagged at the control and in the top bar while a modified point is shown.

**Captions.** A recording spec's `captions: [{at, text, hold?}]` (`at` in played seconds) are written by the recorder
as accumulative messages `caption {t, text, n, at, hold?}` at their frames, with the world time of that frame, so a
caption keeps its place under frame thinning and speed changes and is part of the recording's key. `hold` (seconds):
while the story plays, the playback stops at that caption's frame and waits `hold` seconds before it goes on, so the
text can be read (`watch.js`; the registry checks only that it is a number > 0), also at the recording's first frame;
any action (▶ / ❚❚, a scrub, a chapter) ends a hold, and scrubbing, the chapter ticks and ◀◀ / ▶▶ are not held. A script's `speed` command changes only the playback speed; a
`new_world` resets the speed to the world's default, so a script that wants another speed in the new world puts a
`speed` command after the `new_world` at the same `at`.

**The atlas** (`site/atlas.py`, `lfviz/headless.py`; design §1). One per Explore screen (its id is the screen's) and one
per lab step (`<screen>.<step>`). A point is the world's own `Simulation` run headless by `headless.run_spec`, the one
runner of the recordings, the atlases and the server's live points: the screen's preset, its `fixed` values and the
grid values on top, the screen's seed, frames every `frame_dt` from t = 0 until the stop rule. A point the world refuses
(`check_params`, its memory estimate, its constructor or its first showing: `headless.PointRefused`; integrator D14) is
`refused`, with its text and hint shown at that combination; a point that fails (an error, an exception, a check ending
✗, a stop event not reached by `max_world_s`, a value that cannot be packed, such as ±inf in a quantised blob) fails the
atlas. Files, per world:
`recordings/<world>/atlas/<atlas>/atlas.<hash8>.json` (the manifest), `base.<hash8>.lfpt.gz` (the default point's
header, loaded once) and `p<i>.<hash8>.lfpt.gz` (the point with the flattened index `i`, row-major, the last control
fastest: its header as a delta against the base, the world's messages, `end {reason: "atlas"}`); the world's
`index.json` lists them under `atlases`. The **key** is `sha256(atlas spec + ATLAS_VERSION + recorder_hash +
code_hash(world))[:16]` (`ATLAS_VERSION` 2 since 2026-11-17); `plan.py` marks each atlas `present`, `stale` or
`missing`, and an atlas whose manifest names a base or a point that is missing or of another size is `stale`
(`sitelib.atlas_files_ok`), so `--stale` rebuilds it; `RECORDER_FILES` covers `site/atlas.py` and `lfviz/headless.py`.
The same spec and code give the same bytes, the manifest included (it holds no build or CPU time: those are the index
entry's `made` and `cpu_s`), on the same CPU type (numpy's SIMD paths can change the last bits of a world's computed
values). A point's header delta names its base (`"$base"`, the base file's sha256, which the manifest has as
`base.sha256`): a reader merges it only with that base and drops `$base` from the merged header, as it drops `$delta`
(review R-F F2, integrator D13). The player loads points on demand
(an LRU of 24 points or 40 MB), prefetches the neighbours (±1 along every control, two requests at a time) and shows
«loading…» after 300 ms, never a blank view.

**Stochastic points** store one seeded sample and the run's own computed distribution (u32: about 5000 hits and the
expectation curves, with the sample's χ² against them); another sample is drawn only by «Another sample» on a server.

**Quantisation** (`lfviz/protocol.py`, «Quantised blobs»; `api.js decode`). A blob's descriptor may carry `q: {enc: lin
| sqrt, lo, hi, nan?}` with a stored `u1` or `u2`; both decoders return float arrays (lin `lo + v/top·(hi − lo)`, sqrt
`hi·(v/top)²`). A screen's or a recording's `quantize` map `{"<type>.<blob>[|<blob>…]": "u8" | "u16" | "u8sqrt" |
"u16sqrt"[":col" | ":all"]}` names what is packed; the registry refuses a quantisation the view does not declare safe
in its `QUANT_SAFE` (or `quantSafe`) object literal, or one coarser than declared there (the range suffixes rank
`:all` < none < `:col`); only drawn arrays are quantised, never measurables, events or checks (the registry refuses the
blobs of `end`, `check`, `event`, `error`, `notice`, `caption`, `state` and `live`: `registry.QUANT_TYPES_REFUSED`);
±inf is refused (NaN keeps its code); a range a few ulps wide is kept exact (`protocol.SHORT_MIN_ULPS`, 64 ulps); and
the largest error of each quantised blob is measured and written into the manifest (`quant`) or the index entry.

**The view's contract, extended** (optional; old views keep working): `ctx.screen` (`live`, `recording`, `watch`,
`explore`, `lab`) and `ctx.ui`; `OVERLAYS` (an array literal of `{id, label, default}`, read by
`registry.view_declarations`) with `setOverlay(id, on)`; `setTraces(list)` (earlier points, each a decoded world drawn
up to its own time; a trace's `label` names only the values that differ from the point shown, with « · computed live»
and `live: true` for a live point, and the view keeps the label inside the canvas, clear of its other labels);
`setStory({worlds, w, fps})` (optional; Watch: called when the world shown changes, with the recording's decoded worlds,
the index of the one shown and the frames per played second: S03 keeps one scene box for the whole recording and draws
the earlier worlds' throws faded, integrator D8); `worldToPx` / `pxToWorld` (2-D views: where the lab's instruments are drawn); `anchors()`
(optional: where the tape, the ruler and the protractor sit); tolerance of a frame without its dropped blobs. The view
still computes no physics.

**Lab work** (design §2.3).

* `instruments: {id: {kind: ruler | protractor | stopwatch | readout, label, unit, division, error?, reads | manual,
  event?, error_note?}}`. A reading is `division × round(value / division)` with the declared `error` (by default half
  a division), written to the decimals of its division or of its error, whichever is finer («0.600 ± 0.005»); an
  `error` of 0 declares an exact set-up, with its reason in `error_note` (S03's «Height scale of the stand»: the stand
  sets the chute's height exactly at its marks; integrator D2): its reading is written to its division's decimals without
  «± 0» («0.20»), a column derived from it to four significant digits with their zeros («1.000», `lab.js sig4`), and the
  step's list of instruments gives the reason in place of an error («division 0.01 m; exact: the stand sets the chute's
  height at its marks»; V52 (y)); the CSV keeps plain numbers and the error 0. `reads` names a measurable of the world, read at the
  cursor («Nothing to measure yet: …» before it is reached), or `control:<param>`, a set-up value: the shown point's own
  (its header's `params`, then its grid values, then the atlas's `fixed`), never the slider's (integrator D6). `event`
  binds the instrument to an event of the point (its kind or name, as a stop rule matches it): it reads only once that
  event has happened by the frame shown (S03 part 3: `tape_grey` declares `event: "companion_landing"`, so the grey
  ball's tape reads only after the grey ball lands; review R-P F18). A `manual` stopwatch starts with the launch and
  stops on the student's press, on the wall clock (`performance.now()`) whatever the playback does; while it runs,
  ▶ / ❚❚, a scrub of the time bar and ← / → are refused, and «slow» is refused for a step with one: it measures the
  reaction, as a hand-held one does (review R-P F5). «Measure» puts its reading into the step's stopwatch column when
  it was stopped for the shown launch; otherwise the cell stays empty («—», empty in the CSV, never 0), and the plot and
  the fit skip it (review R-W F6).
* `steps: [{id, title, goal, hint?, preset, fixed?, controls, instruments, columns, plot, laws, frame_dt, stop,
  quantize?, drop?}]`: `columns` `[{id, label, from: <instrument>}` or `{id, label, of: <column>, op: sqrt | square |
  sin2 | inverse | log}]` (errors propagated as σ_f² = f′²σ² + ½f″²σ⁴, so sin 2θ at 45° keeps an error); `plot {x, y,
  fit, fits}` with fits `line0`, `line`, `quadratic` (its vertex with σ) and, at standard, `power`; `laws: [{x, y,
  model, quantity, label, unit, reference}, …]`, several per step (`registry._check_laws`; integrator D4): `x` and `y`
  are two columns of the step, `model` one of its plot's fits, `quantity` one the model gives (`registry.LAW_MODELS`:
  slope ← `line0` or `line`, intercept ← `line`, vertex ← `quadratic`, exponent ← `power`), `label` a `T` naming the
  quantity, `unit` a `T` or a plain symbol, `reference` an id unique in the step; the step's own plot is one of its
  laws, and the former single `law` is refused. The fit (`fit.js`, mirroring `lfphys.tools.stats.linear_fit` step by
  step; shared fixture `player/js/tests/fixtures/fit_cases.json`, Pearson–York included, to 1e-12) is York's line (York
  et al. 2004, eqs. (13), with errors in both x and y) for `line0`, `line` and `power` (on the logs), and the effective
  variance (three re-weightings, a stated approximation) for `quadratic`; both refuse a singular design (`fit.singular`;
  review R-E F5, F8; integrator D3). Its errors are scaled by the Birge ratio when χ²/dof > 1, and the scaling is shown.
  Each law's reference is computed **by the world** when the step's atlas is built (`Simulation.lab_reference(step,
  fixed, values, reference) -> {value, unit, label, how, kind: "closed form" | "engine"}`; without `reference`, the
  step's first law) and stored in the manifest's `references` under the law's id. «Check against the law» applies only
  when the plot is one of the step's laws' (x, y, fit); otherwise it is off with the reason, and the part's laws are
  listed with their plots («plot it»). It compares that law's quantity with its reference: ✓ within k errors, or ✗ with
  the step's hint, where k = 2 when the errors are the instruments' declared ones, and Student's t quantile with the
  same coverage (95.45 %) for n − p degrees of freedom when they come from the scatter (no declared errors, or the
  Birge scaling applied); a fit whose √(χ²/dof) exceeds 3 (`fit.js BIRGE_MAX`) gives no verdict, with the reason. One
  row per set-up: «Measure» on a set-up already in the table replaces its row and says so (the bench repeats exactly,
  so a repeat is not a new independent point; integrator D5). A point's reply is applied only when it is still the one
  asked for, and «Measure» is refused while the slider's set-up is not the one shown (loading, refused or failed;
  integrator D6). The drawer of Lab work lists the events without their times, since a landing's time would give a
  hidden value away (integrator D10). The table is kept per step in the browser (`localStorage`, a convenience) with
  its atlas's key, dropped with a message when the atlas is rebuilt, and exported as CSV with the errors.
* `worksheet: {frp: [{name, programme, …}], equipment: [T], questions: [{q, answer}], teacher: [T], variants?}`: data,
  not a document. Every `frp` entry names its `programme` (a `T`: the programme's name to print, never its raw id).
  `variants: [{id, grade, label, steps, plot: {step: {x, y, fit}}, goals?: {step: T}, questions}]` are other sheets of
  the same lab (`registry._check_variants`: a unique slug, a grade 1–12, a `T` label, distinct steps of the lab, per step
  two of its columns and a fit among its plot's fits or none, questions of two `T`), chosen on the page
  (`&variant=<id>`, a select): S03's grade-7 variant has part 1 only, L against h with no fitted curve, its own goal and
  questions. `worksheet.html?demo=<world>` (`/worksheet?demo=…`) prints it in the viewer's language. Every printed page
  is one sheet, a fixed A4 page box with the attribution line at its foot: the head («Name», «Class», «Date») and part
  1, one sheet per part, the questions, the teacher's sheets; no part is split and no page carries a single line. A
  part has one blank row per set-up of the step, the plots of its laws (or the variant's), the curve each law fits named
  in its instruction, and «Conclusion» lines. The ФРП lab's name is quoted verbatim in Russian, with the translation
  marked once in another language. The laws' references come from the steps' atlases with the key the server expects
  (the published site's is asked for only when a step has none here). «For the teacher»
  (`&teacher=1`) shows the answers, the teacher's notes and the laws' references on pages of their own; they are public
  (the design's §10, question 2: the repository is public anyway). The texts of `STEPS` and `WORKSHEET` and their
  translations are Site Materials under CC BY-NC-SA 4.0 (`../LICENSE.md` §1 item 8, §9): a world with them carries the
  three-line comment of the licence response (`s03_projectile/viz.py`, above `STEPS = [`), and every printed page
  carries the attribution line.

**Compute live** (`lfviz/atlas_live.py`; §3's `POST /api/atlas/…/point`). On a server the sliders also move between
the detents: a value within a tenth of the local step of a detent (the gap from the nearest detent to its neighbour on
that side) snaps to it, any other is computed live when released and drawn when it arrives. It is labelled «computed
live» on its trace (inside the canvas) and in its own passport: the point's key, the code that computed it and the
time with its zone (`X-LF-Key`, `X-LF-Code`, `X-LF-Made`), and whether it was computed now, taken from the server's
cache, or is the atlas's own on-grid point (integrator D13). A value outside a control's span is refused (400). The
point's key follows the code on disk (`registry.code_hash_current`, by the code files' sizes and times) and covers
`atlas_live.py` itself (`atlas_live.live_hash`); the point's process hashes the code before and after it computes, and
a point computed while the code changed is neither cached nor served (503: try again; review R-F F1, F11). Its header
is a delta naming its base (`$base`): the player merges it only when that is the manifest's `base.sha256`, and
otherwise posts the same request with `full_header: true` and gets the same point (the same key) with a whole header.
The point runs in a separate process with its own memory limit (`LFVIZ_POINT_MEM_GB`, by default half a worker's
budget, at least 512 MB; `oom_score_adj` 1000, `nice` 10) and CPU-time limit (`LFVIZ_POINT_TIMEOUT_S`, 120 s); one at a
time per server, four waiting, then 429 (in the viewer's language). Cache: `runs/atlas-live/<world>/<atlas>/<key16>.lfpt.gz`,
removed with the runs' period and capped at `LFVIZ_POINT_CACHE_MB` (512 MB; the oldest files go first); a killed
process's leftovers older than 10 minutes are removed, and `point.log` holds the last point's log only. An on-grid
value is served from the local atlas when its key is current; when the screen uses the published site's atlas (below),
an on-grid value comes from the site's files, and the server computes only the off-grid ones. The site never posts:
there the sliders take grid values only.

**Atlases on a server** (integrator D11). A screen uses an atlas only with the key the server would build now
(`GET /api/recordings` → `expected`, from the code on that server): the local one when its key is current, else, when
the public site is published, the site's of the same world version and the same key (its files read from
`<site>recordings/<world>/`); otherwise the screen is greyed with «Not built here: run site/record.py --world <id>».
A stale local atlas is not opened. Watch plays the local recording, else the published site's of the same version.
The worksheet takes the laws' references from the same atlases. The site is asked only when a screen (or a worksheet's
step) has nothing current here, and through its `api/recordings.json` (every world's index), so a world not yet
published there logs no 404 (`demo.js`, `worksheet.js`). So a browser test needs recordings and atlases built by
the code under test (`site/fixtures.py`, below); `site/check.py` fails when the site's `expected` is missing or differs
from the registry's keys.

**Budgets** (`sitelib.BUDGET`, gzip, decimal; design §1.8): a point 150 kB target / 400 kB limit; an atlas 6 / 12 MB;
a world, recordings and atlases together, 12 / 25 MB; the site 600 / 900 MB. `site/atlas.py` and `site/check.py` fail
over a limit and warn over a target (`sitelib.ACCEPTED` names the accepted ones with their reasons). Measured on
2026-11-17 (local build, Docker, CPU, the pinned image): S03 Explore 940 points, 10 refused, 5.85 MB (largest point
12.9 kB; 11 s of CPU), labs 39, 46 and 89 kB, Watch `independence` 0.03 MB and `air` 0.02 MB, its world 6.11 MB; u32
Explore 48 points, 5.50 MB (largest point 132.7 kB; 93 s of CPU), Watch `story` 0.60 MB (`young`, `eraser`,
`aharonov_bohm` 0.73, 0.64, 0.67 MB), its world 8.15 MB.

**Making them.** `site/record.py --world <id>` (or `--stale`, `--all`) records a world's recordings, then builds its
atlases; `site/atlas.py --world <id> [--atlas <id>]` builds only the atlases. Locally as in §9 (Docker, CPU,
`--memory`); in CI the `record` job's matrix entry per world makes both, cached by the world key, which covers the
recordings' and the atlases' keys (`.github/workflows/pages.yml`). `site/build.py` copies the atlases under
`recordings/<world>/atlas/`; `site/check.py` checks every manifest against its files (size, sha256), the base, the keys,
the budgets and the checks.

**Tests.** Engine: `lfphys/tests/test_mechanics_projectile.py`, `test_mechanics_air.py`, `test_stats_fit.py` (York's
line against York et al. 2004 and Pearson–York, the minimum of S, NIST StRD, Monte Carlo coverage),
`test_stats_coherence.py` (u32's |γ₁₂| bootstrap against the scatter of Monte Carlo histograms), `test_layers.py` (a
dataset of a module, `core.data:air`, is its own entry), `test_codes.py` (the refusals' machine codes `mechanics.*`,
`fit.*`). Framework: `tests/test_headless.py`, `test_atlas.py` (on the toy world `tests/site_worlds/s98_atlas_toy`: its
committed fixture in `tests/site_worlds/recordings/`, remade by `tests/site_worlds/make_fixture.py`, is compared byte
for byte with a fresh build, and `site/fixtures.py` builds everything present with the expected keys),
`test_protocol_quant.py` (shared fixtures `tests/site_worlds/quant/`), `test_atlas_live.py`, `test_code_hash.py`,
`test_site_registry.py`, `test_site_build.py`. Worlds: `s03_projectile/tests/test_s03_physics.py` (every law's
reference and every number of the worksheet against the engine), `u32_double_slit/tests/test_u32_screens.py`. Player
(Node, `node --test player/js/tests/*.test.mjs`, also in CI): `quant`, `fit` (the shared fixture
`fixtures/fit_cases.json` made by `fixtures/make_fit_cases.py`, and Student's t against SciPy,
`fixtures/t_quantiles.json`), `atlas`, `lab`, `captions`, `record`, `i18n`, `decode`; the instrument model is tested on
hand-computed cases (there is no Python one). Browser (EN and RU, 1280 and 390 px, a private server, never port 8479):
the committed toy fixture's keys are not current once any code changes, so a server's player greys its screens (D11);
`site/fixtures.py --out DIR [--world …]` builds what a browser test needs now (by default the toy world's recordings
and atlases) into a folder served with `LFVIZ_RECORDINGS=DIR`. `tests/browser/demo_screens.mjs <port> [sizes] [world]`
for the toy, S03 and u32 (with the recordings and atlases built by the code under test; CI's `build` job runs it for
the toy in EN and RU), `u32_double_slit/tests/u32_screens.mjs` (what is u32's own: the readout line, the folded panels,
«▶ Compute live» from Explore, the explanations never over the pictures and the phone's map height, also at 1024 px and
in the full player: V52 (b), (c); the screens switched back and forth without a console error),
`s03_projectile/tests/s03_screens.mjs` (S03's Explore: «h = … m» clear of the
launcher at every computed point, the drag on its own scale and the legend saying so: V52 (e), (f); from the view's
`canvas.__layout`), `start_page.mjs` (the cards' screen buttons, each enabled one clicked) and
`site_smoke.mjs` (every screen used and the worksheet on the built site).
