# Review UX-params: launch and run errors under parameter combinations a user would choose

**Status: awaiting processing.** Internal review by an independent subagent (Claude Opus), delivered on 2026-11-04.
The reviewer did not write the code under review. Under `reviews/README.md` the reviewer does not process this review:
there is no RESPONSE.md, no archiving and no edits outside this folder.

The owner's words that set the goal (2026-11-04, verbatim): «при выборе опреледенных комбинаций, если ошибки … должно
быть все понятно и удобно».

## In short

**3903 combinations** over the 21 worlds (CPU, 2026-11-04): (a) ok 2918; (b) clean refusal 215; (c) crash 65; (d) hang or stall 115 (29 of them v08's CPU builds, 38 v03's under the host's load of 30–40); (e) wrong-looking output 16; (f) raw, English or wrong refusal 178; (h) a clean refusal of the first world that the player never shows (P1) 396. Per world below.

Findings: 33 — **6 errors** (P1, P3, P8, P9, P25, P28), **22 should-fix**, **5 nits** (P20, P21, P22, P23, P27). Ranked by how likely the owner meets them (defaults and presets first, then common edits, then
extremes); the IDs are those of the section «Findings»:

| rank | ID | severity | where | one line |
|---:|---|---|---|---|
| 1 | P1 | error | framework | A world refused at its start is never explained: the player drops the reason, says «старая запись — продолжить нельзя»; the run list says «сбой» |
| 2 | P9 | error | v01 | Preset «Измерение c» + «Вспышка» by an observer: another observer «measures» c = 5.6·10⁸ … 7.8·10⁹ м/с (flash inside its rod) |
| 3 | P2 | should-fix | framework | A typed out-of-range number or an emptied field is refused as «lam_nm: 0.0 < min 300.0» (id, English; the empty field is sent as 0) |
| 4 | P24 | should-fix | p04 | «Жидкость» = вода / воздух / своя from the defaults is refused; the advice «увеличьте dt» names a step the owner cannot set |
| 5 | P31 | should-fix | p03 | «Стенка» and «Поршень» from the palette in the default box are refused in English («axis y is periodic») |
| 6 | P10 | should-fix | v13, v14 | «Суперпозиция» from the defaults is refused (second state = first); the form allows l ≥ n, \|m\| > l |
| 7 | P11 | should-fix | v16 | «Голограмма-вилка» from the defaults is refused for every Λ; the advice cannot be followed |
| 8 | P12 | should-fix | v01 | One law changed from the defaults (эфир, баллистика, Ньютон) is refused — invisible because of P1 |
| 9 | P26 | should-fix | v08 | «Круглое отверстие» (or a = min, z_max = max) from the defaults is refused only after a minute of trial computation |
| 10 | P13 | should-fix | v03 | «Ступенька» from the defaults: 52–88 s of computation, then two failed checks |
| 11 | P14 | should-fix | v01 | Preset «andromeda» + «Вспышка»: two self-consistency checks fail by round-off of absolute times |
| 12 | P15 | should-fix | v02 | Crossed polarisers in the slits: \|γ₁₂\| = 1.108 shown failed |
| 13 | P28 | error | p02 | A refused removal (field with a charged particle) half-removes the object; «Очистить сцену» → «Сцена: 'o1'» |
| 14 | P30 | should-fix | p02 | Each scene change in a running preset takes 30–44 s; some extreme edits over 2 min |
| 15 | P32 | should-fix | p03 | «Газ» n = 1 with equal speeds, hard disks at T = 0, a crystal at 10⁵ K crash the world |
| 16 | P3 | error | framework, v13 | An exception in `after_header` kills the worker; ⏺ repeats «Мир не восстановлен: float division by zero» (v13 2p_z + 2s) |
| 17 | P8 | error | v02 | «Темновые отсчёты» near 10¹² 1/с allocates tens of GB per frame (took the host's memory in this audit) |
| 18 | P25 | error | p04 | A thin or tall domain allocates the grid without a limit (591 GiB, 6.6 GiB, 74 TiB) or stalls a frame for minutes |
| 19 | P4 | should-fix | framework | Any exception becomes a refusal text («RG integration failed», «Unable to allocate…»); a crash in play is a whole traceback in a toast |
| 20 | P5 | should-fix | v06 | α_s(M_Z) = 0.19 refuses the world with «RG integration failed» |
| 21 | P6 | should-fix | v15 | Johannsen–Psaltis deviations refused in English; one combination crashes on a complex number |
| 22 | P16 | should-fix | v17 | Index-matched drop: NaN and failed checks; «⏭ событие» stalls 20–40 s, large drops over 2 min |
| 23 | P29 | should-fix | p02 | Extreme edits make the wave NaN; the next Bohm change → «Probabilities contain NaN»; a packet added outside the window is accepted |
| 24 | P33 | should-fix | p03 | Counts at their maxima (20 000 atoms, 2000 molecules, 50-atom chains) stall one edit for minutes |
| 25 | P17 | should-fix | v02 | Options always refused for the particle are offered; texts with ids («элемент 'rot_y'…») |
| 26 | P7 | should-fix | v01 | Walkers faster than this world's c: «worldline is not timelike» |
| 27 | P18 | should-fix | v02 | «λ зонда» at its minimum allocates 2 GiB; GRW extremes overflow numpy (raw texts) |
| 28 | P19 | should-fix | v03 | A wide sharp barrier: T 55× off; oscillator refusal advises absent parameters; «(review V3-3)» in a text |
| 29 | P27 | nit | p04 | A velocity probe inside a body reads NaN without a word |
| 30 | P20 | nit | framework | «Действие boost: …» — the action's id instead of its label |
| 31 | P21 | nit | v07 | The reversal-speed reference loses precision at τ = min, L = max |
| 32 | P22 | nit | 3-D worlds | A slice plane moved past the box shows an empty window |
| 33 | P23 | nit | v02, v06, v16 | Honest failing checks (a preset outside its approximation, a «what if» preset): a note in the preset would help |

Not found: no crash on any default world or preset, and no hang there except v08's builds on the CPU (77–177 s; GPU 0
on the owner's server) and «⏭ событие» in v17's «big_drops» (38 s, P16); the failing checks on presets are honest
(P23); v05, v07, v10
had no crash, hang or raw refusal in any combination; v04, v09, v11, v12, v14 and p01 refuse cleanly in Russian (their
refusals at the start are hidden only by P1).

## Scope

Every world: the demonstrations v01–v17 and the playgrounds p01–p04, through their schemas (`viz.py`: world and live
parameters, laws, presets, actions from the header, slice-plane views) and, for the playgrounds, their palettes
(`server/lfviz/playground.py`, each section's `palette()`), together with the shared path a run takes
(`server/lfviz/params.py`, `sim.py`, `worker.py`, `runs.py`, `app.py`) and what the player shows
(`player/js/player.js`, `catalog.js`, `ui.js`). Physics correctness was not reviewed except where an output is plainly
wrong (a measured speed of light of 7.8·10⁹ м/с, |γ| > 1).

## Method

**Driver** (`scripts/audit.py`). For each world it generates combinations from the schema and runs each one in a
forked process through the same calls the worker makes: `Schema.resolve` (the server's 400), the playground scene
check, the `Simulation` constructor (the worker's «Мир не создан»), `Runner._start_world` (header, `after_header`, the
t = 0 advance), then the operations: frames as the run loop plays them (`Runner._advance` with the loop's wall budget,
then `_frame`), `step`, `next_event`, `set`, `action`, `view`, `scene`, `new_world`, and a checkpoint round trip for
presets. Every message goes through `protocol.encode`. The command methods of the world are wrapped to learn the
exception type and the raising line behind each refusal.

**Combinations per world** (`kinds_table` below):

- *default*; *single*: each shown parameter at its minimum, its maximum and every other choice of a select or bool, one
  at a time from the defaults (its `show_if` parents set so that it takes effect); for live parameters also as a live
  change of a running default world (*live*);
- *pair*: groups of interacting extremes chosen from the schemas and READMEs (species × wavelength, grid × size, slit
  width × period, quantum numbers, metric deviations × spin, …), at the start and, when all are live, as live changes;
- *all*: all numeric parameters at their minima, and at their maxima;
- *preset*: each preset, played, `next_event`, `step`, checkpoint; *preset_live*: every live parameter swept over its
  extremes/choices from two presets in turn; *preset_action*: every action of each preset's own form with its default
  arguments and every argument at its extremes; *preset_view* / *view_extreme*: slice planes added, tilted, moved, set
  to auto, removed, reset, and planes outside the box; *new_world*: a world parameter changed in a running world;
- *random*: a seeded sample (`random.Random(20261104 + world)`), 25–60 per world, with 30 % of the values at an edge,
  two random live changes and a random action of the current form;
- playgrounds: each law parameter, each preset (played, exported, checkpointed), every preset object edited to each
  parameter's extremes while running, duplicated and removed, every palette type added to each preset; each palette type
  of each mode of the laws added alone with its defaults and with each parameter at its extremes, then edited to the
  extremes while running and duplicated/removed; random scenes of 2–6 objects with random values, random edits and
  removals while running.

**Reduced where the CPU cost forbade the full set:** v08 without its random sample and the per-preset slice-plane runs
(one build takes 1–3 min on the CPU); p02 with 15 random scenes instead of 50 and its per-parameter palette sweep in 2-D
only; p03's sweep in 2-D LJ and 2-D hard spheres (the 3-D and WCA palettes were added and edited, not swept). Two
early runs were discarded because of faults of the driver, not of the worlds: v10's first run (the driver replaced the
world's `scene` attribute by a wrapper) and v01's first run (actions taken from the default world's form instead of the
preset's own); both worlds were run again.

**Budgets and classification.** A world that takes more than 60 s to build, or a frame or command that takes more
than 30 s, is counted as a hang (d) (killed after 240 s / 120 s; a combination after 600 s). Outcomes: (a) ok; (b) a
clean refusal — a Russian `ValueError` raised by the project with a text that names the problem; (c) a crash — any
other exception type, a traceback in the player, a worker that dies; (d) a hang or stall as above; (e) wrong-looking
output — a check that fails on a default or preset world, NaN/inf in a check or frame, an all-NaN image; (f) a refusal
whose text is raw (English, Python, internal ids) or wrong; and a separate column **(h)**: a clean refusal of the first
world, which the player never shows (finding P1). Failing checks at extremes are listed (section «Failed checks») but
not counted as (e): a failing check there is what RULES.md §2.5 asks for. A combination counts once, by its worst
outcome in the order c, d, e, f, h, b. Refusal texts were read by hand: `scripts/analyze.py` `OVERRIDES` lists the
reclassifications (internal ids → f; operations the player never sends → a).

**Server and browser.** A private server (`lf-uxc-srv`, port 8563, the same image, `LFPHYS_NO_GPU=1`) confirmed a
sample of the (c)–(f) and (h) cases through the HTTP API (`scripts/srvcheck.py`), and Playwright (Chromium, SwiftShader)
recorded what the page shows — toasts, «События», the status line, the checks panel — with screenshots
(`pw/see.mjs`, `pw/typed.mjs`, `pw/catalogue.mjs`).

## Environment

Docker image `light-funnel-viz` (the project's), `engine/` mounted read-only, CPU only (`LFPHYS_NO_GPU=1`,
`OMP_NUM_THREADS=2` as the server's workers), 5 worker processes per container (2–4 for v08, v11, v12, p02–p04). The
shared host carried 30–40 of load from other sessions during the first batch (v03–v15) and ~3 later: the times
measured then are inflated up to ~3×; the timings quoted in the findings come from one process when the host was
quieter (`repro/r_v03_timing.out`). v08 and v11–v12 would run their kernels on GPU 0 on the owner's server («авто»);
their CPU build times (v08 ~80 s) are not a finding by themselves.

**Incident.** The first batch ran without a memory limit. Combination v02 #133 (`dark_rate = 10¹²`) grew to 31 GB and the
kernel's OOM killer fired on the shared host at 23:55 (host time); it killed two of this audit's processes and two
`chrome-headless` processes of another session (`dmesg`: «Out of memory: Killed process … (python3) … anon-rss:31255656kB»,
«… (chrome-headless) …»). From then on every container ran with `--memory=14–16g` and every combination with
`RLIMIT_AS` = 8 GB (6 GB for v08/v11/v12), so that the same combinations end in a `MemoryError` inside the audit. This is
the cause of finding P8, and the reason it is an error: the server's workers have no such limit.

## Summary per world

(Generated by `scripts/report.py` from `results/*.jsonl`; the full list of combinations with their outcome is
`results/combinations.jsonl`.)

| world | combinations | (a) ok | (b) clean refusal | (c) crash | (d) hang / slow | (e) wrong output | (f) raw / unclear refusal | (h) clean refusal never shown (P1) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| p01_gravity | 270 | 209 | 54 | 0 | 0 | 0 | 0 | 7 |
| p02_quantum | 253 | 194 | 37 | 7 | 11 | 4 | 0 | 0 |
| p03_molecules | 400 | 262 | 7 | 38 | 14 | 0 | 79 | 0 |
| p04_fluids | 207 | 109 | 22 | 8 | 2 | 5 | 58 | 3 |
| v01_light_travel | 285 | 249 | 1 | 0 | 0 | 0 | 1 | 34 |
| v02_double_slit | 513 | 342 | 58 | 10 | 4 | 4 | 19 | 76 |
| v03_quantum_1d | 173 | 102 | 7 | 0 | 38 | 0 | 8 | 18 |
| v04_orbits | 218 | 150 | 24 | 0 | 0 | 0 | 0 | 44 |
| v05_optics_bench | 234 | 234 | 0 | 0 | 0 | 0 | 0 | 0 |
| v06_qcd | 136 | 132 | 0 | 0 | 0 | 1 | 1 | 2 |
| v07_bell_test | 139 | 139 | 0 | 0 | 0 | 0 | 0 | 0 |
| v08_wave_3d | 40 | 9 | 0 | 0 | 29 | 0 | 0 | 2 |
| v09_thomas_3d | 120 | 113 | 1 | 0 | 0 | 1 | 0 | 5 |
| v10_fast_observer | 151 | 151 | 0 | 0 | 0 | 0 | 0 | 0 |
| v11_double_slit_2d | 98 | 61 | 2 | 0 | 0 | 0 | 0 | 35 |
| v12_arrival_times_2d | 100 | 61 | 0 | 0 | 0 | 0 | 0 | 39 |
| v13_hydrogen_3d | 121 | 54 | 0 | 1 | 0 | 0 | 0 | 66 |
| v14_quarkonium_3d | 114 | 78 | 0 | 0 | 0 | 0 | 0 | 36 |
| v15_kerr_shadow | 130 | 117 | 0 | 1 | 0 | 0 | 12 | 0 |
| v16_optical_vortices | 114 | 87 | 2 | 0 | 0 | 0 | 0 | 25 |
| v17_mie_scattering | 87 | 65 | 0 | 0 | 17 | 1 | 0 | 4 |
| **total** | **3903** | **2918** | **215** | **65** | **115** | **16** | **178** | **396** |

Combinations per kind:

| world | default | single | live | pair | pair_live | all | preset | preset_live | preset_action | preset_view | view_extreme | new_world | palette | palette_param | palette_edit | preset_edit | preset_remove | preset_add | random |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p01_gravity | 1 | 11 | 0 | 5 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 10 | 145 | 10 | 7 | 7 | 7 | 60 |
| p02_quantum | 1 | 11 | 0 | 4 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 24 | 146 | 24 | 7 | 7 | 7 | 15 |
| p03_molecules | 1 | 16 | 0 | 7 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 46 | 240 | 46 | 6 | 6 | 6 | 20 |
| p04_fluids | 1 | 26 | 0 | 10 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 10 | 90 | 10 | 5 | 5 | 5 | 40 |
| v01_light_travel | 1 | 53 | 0 | 20 | 0 | 2 | 10 | 0 | 148 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 50 |
| v02_double_slit | 1 | 122 | 114 | 43 | 38 | 2 | 19 | 94 | 19 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v03_quantum_1d | 1 | 25 | 25 | 15 | 15 | 2 | 9 | 22 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 50 |
| v04_orbits | 1 | 13 | 8 | 15 | 8 | 2 | 7 | 35 | 28 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100 |
| v05_optics_bench | 1 | 39 | 39 | 15 | 15 | 2 | 9 | 36 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v06_qcd | 1 | 15 | 13 | 8 | 4 | 2 | 4 | 28 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v07_bell_test | 1 | 19 | 15 | 8 | 5 | 2 | 6 | 16 | 6 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v08_wave_3d | 1 | 20 | 0 | 10 | 0 | 2 | 5 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| v09_thomas_3d | 1 | 28 | 0 | 11 | 0 | 2 | 8 | 0 | 0 | 8 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v10_fast_observer | 1 | 31 | 22 | 10 | 5 | 2 | 7 | 22 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 50 |
| v11_double_slit_2d | 1 | 37 | 6 | 11 | 0 | 2 | 7 | 8 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| v12_arrival_times_2d | 1 | 47 | 2 | 13 | 0 | 2 | 5 | 4 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 25 |
| v13_hydrogen_3d | 1 | 23 | 0 | 13 | 0 | 2 | 10 | 0 | 0 | 10 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v14_quarkonium_3d | 1 | 21 | 0 | 8 | 0 | 2 | 10 | 0 | 0 | 10 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v15_kerr_shadow | 1 | 22 | 11 | 11 | 2 | 2 | 6 | 14 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 60 |
| v16_optical_vortices | 1 | 25 | 2 | 12 | 0 | 2 | 9 | 2 | 0 | 9 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 50 |
| v17_mie_scattering | 1 | 19 | 3 | 10 | 0 | 2 | 7 | 4 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 40 |

## Findings

The sections follow the IDs; the ranking by how likely the owner meets them is the table in «In short». One cause counts
once; the worlds it affects are listed with it. Paths of code are relative to `engine/`, paths of evidence to this
folder. Line numbers are those of the tree on 2026-11-04.

### P1 — error — a world refused at its start is never explained to the user (framework)

**Worlds:** every demonstration and playground; met most often in v02, v04, v11, v12, v13, v14, v01, v16, v03 (column
(h) of the table: 396 combinations; the refusals at the start counted under (c) and (f) are hidden the same way).

**What the user sees.** The owner changes one parameter in the catalogue (for example «Кинематика» → «Галилей + эфир»
in v01, «Режим» → «Суперпозиция» in v13, «Генератор» → «Голограмма-вилка» in v16, «n» → 1 in v13) and presses
«▶ Запустить». The server accepts the start (200); the catalogue goes to the run page at once
(`visualizations/player/js/catalog.js:148`); the worker refuses the world with a clean Russian reason («Мир не создан:
ОТО требует СТО…», «Мир не создан: второе состояние совпадает с первым», …; `visualizations/server/lfviz/worker.py:134-140`).
The player drops that message: every message before the first `header` is discarded
(`visualizations/player/js/player.js:546-547`, `const W = S.worlds[latest()]; if (!W) return;`). The page shows an
empty scene, «Событий пока нет», «ждём запуск…», «Мир строится…» and the status «старая запись — продолжить нельзя»
(`player.js:942`). Opened again later, the same run says «приостановлен — ⏺ продолжит» (`server/lfviz/runs.py:363-367`
counts a `failed` run as resumable), and ⏺ answers «в записи нет ни одного мира: продолжать нечего» (`runs.py:429`).
The catalogue's run list shows «сбой» with no reason (`catalog.js:211-218`). The reason exists only in
`GET /api/runs/{id}` → `errors`.

**Minimal reproduction:** `POST /api/runs {"viz": "v13_hydrogen_3d", "params": {"mode": "super"}}`, then open
`/run?id=…`. Equally `{"viz": "v01_light_travel", "params": {"kinematics": "ether"}}`,
`{"viz": "v16_optical_vortices", "params": {"gen": "fork"}}`, `{"viz": "v04_orbits", "params": {"radius_km": 1000,
"r0": 2.1}}`, `{"viz": "v13_hydrogen_3d", "params": {"n": 2, "l": 2}}`.

**Evidence:** `pw/cases0.json` → `pw/out0.json`, `pw/shots/P1_v13_refused_start.png`, `pw/shots/v04_r0_inside_body.png`;
`pw/catalogue.mjs` → `pw/catalogue_out.json`, `pw/shots/P1_catalogue_failed_runs.png`,
`pw/shots/P1_v13_refused_reopened.png`; `server/srv_out1.json` (state «failed», `errors` with the reason).

**Suggested fix.** (1) Player: handle `error` and `end` before any world — keep them in a run-level list, show them in
«События» and as a toast, and set the status to «мир не создан: <причина>» instead of «старая запись». (2) Catalogue:
after `POST /api/runs`, wait for the first `header` or the run's end (poll `/api/runs/{id}` for a few seconds); on
`failed` stay on the form and show `errors[-1]` next to it, so that the owner changes the refused parameter where he set
it. (3) Do not count a run without any world as resumable (`runs.py:366`); show the reason in the run list.

### P2 — should-fix — a number typed outside its range, or an emptied field, is refused in English with the internal id (framework)

**Worlds:** all (every numeric parameter, in the start form and in the live controls).

**What the user sees.** `<input type="number">` does not enforce `min`/`max` (`visualizations/player/js/ui.js:222-225`,
`:158-161`), and the start form sends `Number(input.value)`, so an emptied field becomes 0 (`ui.js:228`). The schema
answers with `_coerce`'s texts (`visualizations/server/lfviz/params.py:154-187`): «параметры: lam_nm: 2000.0 > max
1600.0»; «параметры: lam_nm: 0.0 < min 300.0» for a field the owner only cleared; «Изменение не применено: lam_nm:
2000.0 > max 1600.0» for a live control; «параметры: speed: cannot read 'abc' as float»; «unknown preset …» — the id
instead of the label, English words, no unit.

**Minimal reproduction:** v05 card → «Параметры…» → «Длина волны λ, нм» = 2000 (or empty) → «▶ Запустить»; or the live
control of the same parameter = 2000 ↵.

**Evidence:** `pw/typed.mjs` → `pw/typed_out.json`, `pw/shots/P2_catalogue_typed_above_max.png`,
`pw/shots/P2_catalogue_field_cleared.png`, `pw/shots/P2_live_typed_above_max.png`; `typed.out` (every world).

**Suggested fix.** Russian texts with the label and unit: «Длина волны λ, нм: 2000 — больше предела 1600», «… поле
пустое — введите число от 300 до 1600». In `paramForm`, treat an emptied field like the live control does
(`ui.js:164`: restore the value), and mark an out-of-range value in the field before sending.

### P3 — error — an exception while a world shows itself kills the worker; the player then repeats «Мир не восстановлен: float division by zero» (framework; found in v13)

**What happens.** `Runner.run()` calls `_start_world()` before its `try` (`visualizations/server/lfviz/sim.py:511-513`),
and `_start_world()` calls `self.sim.after_header()` outside its own `try` (`sim.py:355`). An exception there ends the
worker (traceback only in `worker.log`). The header is already in the record, so the run becomes «suspended», and every
⏺ rebuilds the world and fails again: «Мир не восстановлен: float division by zero» (`worker.py:143-149`), status
«продолжение не удалось — ⏺ повторит» — a loop with a raw Python message, «не восстановлен» for a world that never ran.

**The trigger in v13:** «Режим» = суперпозиция, «Второе состояние: l» = 0 (the rest default: 2p_z + 2s). The two states
have the same energy and are real, so the probability current is zero everywhere and ∂ρ/∂t = 0; the continuity check
divides by `scale = max(max|∂ρ/∂t|, max|j|/⟨r⟩) = 0` (`visualizations/server/lfviz/orbitals3d.py:342-345`) →
`ZeroDivisionError`. The same code serves v14.

**Evidence:** `results/v13_hydrogen_3d.jsonl` #14; `server/srv_out1.json` («v13_super_l2_0_crash»: state «suspended»,
`resume_error` «Мир не восстановлен: float division by zero»); `pw/out1.json`,
`pw/shots/c_v13_super_l2_0_after_header_crash.png`.

**Suggested fix.** Framework: run `after_header()` and the t = 0 advance under the `try` that reports a refused world
(«Мир не создан: …», then `end`), and say «не создан», not «не восстановлен», for a world that never started. v13/v14:
when `scale == 0` the identity holds trivially — report the check as passed with a note («ток равен нулю всюду:
вещественные вырожденные состояния»).

### P4 — should-fix — internal exceptions reach the user as refusal texts or as whole tracebacks (framework; world causes in P5–P8, P18)

**Worlds:** v01, v02, v06, v15 here; any world can hit it.

**What happens.** Every command path turns *any* exception into a refusal text with `str(e)`: actions (`sim.py:293-296`),
live changes (`sim.py:303-306`), views (`sim.py:316-319`), scenes (`sim.py:326-329`), new worlds (`sim.py:366-369`), the
first world (`worker.py:134-138`). Deliberate refusals (Russian `ValueError`s of the visualizations) and failures of the
library or numpy («RG integration failed», «Unable to allocate 2.03 GiB for an array…», «float() argument must be a
string or a real number, not 'complex'», «worldline is not timelike…») look the same. A failure inside `advance` while
playing shows the whole traceback as a toast and as «ОШИБКА: Traceback (most recent call last): …» in «События»
(`sim.py:551-558`, `:359`; `player.js:580-582`).

**Suggested fix.** A dedicated refusal type (or the convention «Russian `ValueError` raised by the visualization») shown
as is; anything else shown as «Внутренняя ошибка расчёта (<тип>): мир не изменён — подробности в журнале запуска», with
the traceback in `worker.log` and the record but not in a toast. The world-specific causes below are still to be fixed
at their source.

### P5 — should-fix — v06: α_s(M_Z) = 0.19 refuses the world with «RG integration failed»

**Where:** `lfphys/lfphys/core/qcd/running.py:91-95` raises `ValueError("RG integration failed")` when `solve_ivp` fails
near the Landau pole before the pole event fires; `visualizations/v06_qcd/viz.py:72-78` (`_alpha`) catches only
`LandauPole`.

**Minimal reproduction:** v06, «α_s(M_Z)» = 0.19 (loops 4, the rest default). Also the audit's random #26
(`alpha_mz` 0.1389, `mu` 10000, `system` bottom, `kappa` 0.655, preset «strong»). The scan `repro/r_v06_rg.py`
(α_s(M_Z) from 0.11 to 0.30 in steps of 0.005, loops 1–4, ± the PDG uncertainty) finds only 0.19 at 4 loops: a narrow
band next to the pole.

**Evidence:** `results/v06_qcd.jsonl` #102; `repro/r_v06_rg.out`; `server/srv_out1.json`; `pw/out1.json`,
`pw/shots/f_v06_newworld_rg_failed.png` (toast «Новый мир не создан: RG integration failed»).

**Suggested fix:** treat a failed integration that ends with α growing towards `ALPHA_MAX` like the pole (raise
`LandauPole`, so the curve ends with the existing notice «полюс Ландау»), or make the pole event fire first (a smaller
`ALPHA_MAX` margin or `max_step`).

### P6 — should-fix — v15: the Johannsen–Psaltis metric is refused in English, and one combination crashes

**Where:** `visualizations/v15_kerr_shadow/viz.py:119-123` passes the English `ValueError`s of
`lfphys/lfphys/theories/alternatives/johannsen_metric.py:126` (`check_regular`) and `:179` (`photon_shell`) to the user;
`circular_orbits` (`:262`) calls `float()` on a complex E when Ω of `_circular` (`:218`) is complex at the ISCO.

**What the user sees** (metric «JP», one deviation slider at its end, the rest default): «Мир не создан: the metric is
not regular outside the horizon (Johannsen 2013a Eqs. 72, 76-78): A1 reaches -2.38, det_eq72 reaches -7.64, ctc_eq76
reaches -0.941» for a13 = −10; likewise a22 = −3, a22 = 10, a12 = −3; «the photon shell is not a single band between r+
and 12 M for these parameters» for a13 = 10 with χ = 0.998; `TypeError` «float() argument must be a string or a real
number, not 'complex'» for a13 = −1.399, a22 = 3.612, a12 = −3 (χ = 0.9).

**Evidence:** `results/v15_kerr_shadow.jsonl` #2, #4, #5, #6, #34, #92; `pw/out1.json`,
`pw/shots/f_v15_newworld_jp_a13_min_english.png`.

**Suggested fix:** translate in v15 («Метрика Йоханнсена–Псалтиса с такими отклонениями не регулярна вне горизонта
(A₁ < 0 при r = …): уменьшите |a13|…»); in the library, test the discriminant of Ω and report «нет круговых орбит»
instead of a complex number; state the admissible region next to the sliders.

### P7 — should-fix — v01: walkers faster than this world's light are refused with «worldline is not timelike»

**Where:** `visualizations/v01_light_travel/viz.py:367-378` (`_scn_andromeda`) builds the walkers at «Скорость
пешеходов» (up to 2.9·10⁸ м/с) without comparing it with c × «Скорость света, × c»; the library refuses in English
(`lfphys/lfphys/core/relativity.py:83`).

**Minimal reproduction:** v01, scenario «Андромеда», «Скорость света, × c» = 0.5, «Скорость пешеходов» = 2·10⁸.

**Evidence:** `results/v01_light_travel.jsonl` (random #42 there); `server/srv_out1.json`; `pw/out1.json`,
`pw/shots/f_v01_newworld_walk_faster_than_c.png`.

**Suggested fix:** «пешеходы быстрее света этого мира (2·10⁸ м/с ≥ c × 0.5): уменьшите скорость или увеличьте
множитель c».

### P8 — error — v02: «Темновые отсчёты» near its maximum exhausts memory

**Where:** `visualizations/v02_double_slit/viz.py:1031-1036` draws every dark count of a step as an event of its own
(`rng.random(nd)` and five more arrays of length `nd`); `dark_rate` goes up to 10¹² 1/с (`viz.py:107`), so one frame at
the default speed needs ~2·10⁹ events × ~40 bytes.

**What happened in this audit:** see «Incident» above — 31 GB and the host's OOM killer, before the per-process limit;
with the limit, `MemoryError: Unable to allocate 14.9 GiB …` as a traceback. Found from the defaults (single and live),
from the presets «triple» and «triple_mod» while running, and in random combinations with `dark_rate` ≥ 4·10¹¹.

**Evidence:** `results/v02_double_slit.jsonl` #133, #134 (worker killed, exit −9), #412, #413, #461, #467, #496, #510
(MemoryError).

**Suggested fix:** draw dark counts per screen pixel per frame (Poisson per bin) instead of as individual events, or cap
the events per frame and say so; a cost guard for every rate-like parameter; workers with a memory limit
(`RLIMIT_AS` or a cgroup), so that no world can take the host's memory.

### P9 — error — v01: in «Измерение c» an observer's flash makes another observer measure c = 5.6·10⁸ … 7.8·10⁹ м/с

**Where:** `visualizations/v01_light_travel/engine/world.py:335-361` with `engine/apparatus.py:131` (`passing`). The
one-way speed is computed from the first arrivals at the rod's ends A and B; the test at `world.py:348`
(`abs(abs(res["cos"]) - 1.0) > 1e-6`) only asks that the light runs along the rod. When the flash is emitted *between* A and B, the light reaches the two ends running in opposite directions, and
`L/(t_B − t_A)` is not a speed of light.

**Minimal reproduction:** preset «measure_c» (SR, Einstein synchronisation), play 8 frames, action «Вспышка» by
«Наблюдатель 1»: «Наблюдатель 3: свет от «Наблюдатель 1» прошёл стержень A→B, измерено c = 556780400 м/с», later «B→A,
измерено c = 1.93788891e+09 м/с»; checks `pass_p1_obs3_1`, `pass_p2_obs3_1` fail (rel 0.86 and 5.5). In
«measure_c_lab» the same action gives 7.8·10⁹ м/с. Observer 3 moves at −0.5c from the origin with a 300 km rod, so
observer 1 (at rest at the origin) stays inside that rod for the first ~2 ms.

**Evidence:** `repro/r_v01_flash.py` → `repro/r_v01_flash.out`; `results/v01_light_travel.jsonl` #146, #157; the page
shows these event texts (`pw/out2.json`: there the flash came later and the values were plausible — the result depends
on the moment).

**Suggested fix:** no one-way speed when the source event lies between the ends at emission (the two first arrivals
run in opposite directions): «вспышка внутри стержня: скорость по двум концам не измеряется».

### P10 — should-fix — v13: «Суперпозиция» from the defaults is refused; v13/v14: the form allows l ≥ n and |m| > l

**Where:** `visualizations/v13_hydrogen_3d/viz.py:47-49`: the second state's defaults (n2 = 2, l2 = 1, m2 = 0) equal the
first state's (`:41-43`), so choosing «Суперпозиция» alone is refused «второе состояние совпадает с первым» (`:103`) —
and with P1 the owner sees nothing. Likewise «n» = 1 with the default l = 1, any l ≥ n, |m| > l (`v13 viz.py:84, :86`;
`v14 viz.py:74`): 102 of v13's and v14's 235 combinations end so.

**Suggested fix:** a second-state default that differs (e.g. 2s or 1s); with P1 fixed the other refusals become
visible; better, the form clamps l and m to the current n and l, or the server answers before the run starts (P1 (2)).

### P11 — should-fix — v16: «Голограмма-вилка» from the defaults is refused, and its advice cannot be followed

**Where:** `visualizations/v16_optical_vortices/viz.py:176-180`. With the defaults (w0 = 1.5 мкм, Λ = 2.5 мкм,
λ = 1 мкм) the fork's orders do not separate; the preset «fork» uses w0 = 4 (`viz.py:96-97`). With w0 = 1.5 every Λ is
refused: Λ = 1 «период голограммы меньше длины волны», Λ = 2.5 … 8 «порядки голограммы не разойдутся: уменьшите
период Λ или увеличьте перетяжку w0».

**Suggested fix:** when the generator changes, start from the generator's own values (w0 = 4 for the fork), and name the
admissible Λ for the current w0 and λ in the refusal.

### P12 — should-fix — v01: changing one law from the defaults is refused (ether, emission, Newtonian gravity)

**Where:** `visualizations/v01_light_travel/viz.py:136-141` (`Laws.validate`): «Кинематика» = эфир or баллистика with the
default «Гравитация» = ОТО, and «Гравитация» = Ньютон with the default kinematics, are refused. The texts are good, but
P1 hides them; the presets that show these laws («measure_c_ether», «measure_c_emission», «lensing_newton») work.

**Suggested fix:** with P1 fixed this becomes a visible refusal; better, when one law changes in the form, set the other
to the nearest compatible value and say so.

### P13 — should-fix — v03: «Ступенька» from the defaults computes for 1–1.5 min and ends with two failed checks

**Where:** `visualizations/v03_quantum_1d/viz.py:231-247` (`_t_end`), `:265-303` (`_evolve`), `:197-201` (cost guard).
With E = 0.8 эВ below the step V0 = 1 эВ the transmitted part is the slow high-energy tail of the packet; the stop
criterion waits for it, the run reaches `COST_MAX` (twice the guard's limit), and «Волна поглощена детекторами» (`abs0`)
and «Прохождение волнового пакета» (`T0`: 2.36·10⁻⁶ against 2.56·10⁻⁶) fail. One process: 87.7 s to build, 51.9 s as a
live change; the guard estimated less than 25 s.

**Evidence:** `repro/r_v03_timing.py` → `repro/r_v03_timing.out`; `results/v03_quantum_1d.jsonl` #11, #12.

**Suggested fix:** for E below the step (total reflection) stop when the reflected wave is absorbed and assign the
evanescent remainder, or refuse «энергия ниже ступеньки — прохождения нет: поднимите E выше V0»; base the guard on the
cap actually used (COST_MAX, not COST_MAX/2). The synchronous live change itself is STATUS V15.

### P14 — should-fix — v01 «Андромеда»: a flash fails two self-consistency checks at 10⁻⁸

**Where:** `visualizations/v01_light_travel/engine/world.py:244-247` (`flat_*`): the solved flight time `dt` is compared
with |Δx|/c at the default tolerance 10⁻⁹. In this scenario the events happen at t ≈ 4·10¹¹ s and later 8·10¹³ s, and
`dt` is a difference of such absolute times: the shown values (1867.9589233398438 s, 368426.875 s) are exact integer
multiples of the spacing of doubles at those times (6.1·10⁻⁵ s, 0.0156 s), i.e. 3.3·10⁻⁸ and 4.2·10⁻⁸ of `dt` — larger
than the tolerance; rel −9.9·10⁻⁹ … −1.4·10⁻⁸.

**Minimal reproduction:** preset «andromeda», a few frames, «Вспышка» by «Земля» (the form's first choice):
`flat_p2_walk_to`, `flat_p2_walk_from`, later `flat_p3_*` fail.

**Evidence:** `repro/r_v01_flash.out`; `results/v01_light_travel.jsonl` #116, #215–#217.

**Suggested fix:** a tolerance that includes the round-off of the absolute times (~4ε·|t|/dt), or solve for the flight
time relative to the emission event instead of subtracting absolute times.

### P15 — should-fix — v02: the slits' coherence is shown as |γ₁₂| = 1.108 when one slit is dark

**Where:** `visualizations/v02_double_slit/viz.py:880-898` (`coh*`). A polariser at 0° in slit 1 and one at 90° in slit 2
(source H: slit 2 passes nothing) — the classic which-path demonstration — gives |γ| = 1.108 against the identity's
reference 6·10⁻¹⁷, a red check. Similar failures with the eraser presets after changing «Поляризация» or an element
(`coh3`, `coh5`, `coh7`).

**Evidence:** `results/v02_double_slit.jsonl` #302, #303, #378, #379, #436, #437; `pw/out3.json` (the checks panel),
`pw/shots/e_v02_crossed_polarizers_gamma.png`.

**Suggested fix:** when a slit's amplitude is zero or below the fit's resolution, report γ as undefined («одна щель
тёмная: γ₁₂ не определена») instead of fitting.

### P16 — should-fix — v17: an index-matched drop shows a NaN check and a failed Debye check; «⏭ событие» and large drops stall the world

**Where:** `visualizations/v17_mie_scattering/viz.py:312-316` divides by S11² = 0 when the drop does not scatter
(m = 1): NaN, shown as «—» with ✗; the Debye check (`:297`) fails at 1163 against 0. «⏭ событие» (to the scan at
t = 12 s) takes ~20 s on the defaults, 36–39 s with «Ширина распределения» or «n среды» at the maximum, and more than
2 min with «Радиус капли» = 1000 мкм (killed) — the world does not move meanwhile.

**Minimal reproduction:** «Показатель» = свой, n = 1, κ = 0, «n среды» = 1; and «Радиус капли» = 1000, then ⏭.

**Evidence:** `results/v17_mie_scattering.jsonl` #28, #2, #4, #13; `pw/out3.json`, `pw/shots/e_v17_index_matched_nan_check.png`.

**Suggested fix:** refuse m = 1 («капля неотличима от среды: рассеяния нет») or mark the identities trivially true;
bound the cost of a scan (the guard at `viz.py:117` covers only x > 2·10⁴) or compute it in parts across frames.

### P17 — should-fix — v02: the forms offer choices that are always refused, and the texts use internal ids

**Where:** v02's selects do not depend on the particle: «Метод отметки пути» = микроскоп for photons and neutrons
(refused «рассеяние фотона-зонда здесь задаётся дипольной диаграммой…», `viz.py:376`), «Энергия задана через» =
скорость for photons, the elements «rot_y», «filter», «hwp», «qwp», «polarizer» for particles they do not act on —
refused as «элемент 'rot_y' не подходит для этой частицы» (`lfphys/lfphys/core/quantum/marks.py:89`), with the id
instead of the label; «wp_slit» > «n_slits» gives «щели №5 нет».

**Suggested fix:** `show_if` per species for these options (option-level `show_if` in the schema), and labels in the
texts («элемент «поворот спина» не действует на фотон»).

### P18 — should-fix — v02: «λ зонда» at its minimum allocates 2 GiB; GRW extremes overflow numpy

**Where:** `lfphys/lfphys/theories/approx/paraxial.py:64` (the microscope's kick spectrum): «Изменение не применено:
Unable to allocate 2.03 GiB for an array with shape (136214374,) and data type complex128» (presets «electron_eraser»,
«electron_microscope», `mic_lambda_nm` = 0.001); `lfphys/lfphys/theories/approx/paraxial_ensemble.py:151`: «Мир не
создан: array is too big; `arr.size * arr.dtype.itemsize` is larger than the maximum possible size» (`collapse` = grw,
λ_GRW = 10¹², r_C = 0.001 нм, C60). Without a memory limit the first allocates on the server.

**Suggested fix:** cost guards in v02 with Russian texts («λ зонда меньше … нм: спектр отдачи требует … ГБ»).

### P19 — should-fix — v03: a wide, sharp barrier gives a transmission 55× off; refusals with wrong or internal wording

**Where:** `visualizations/v03_quantum_1d/viz.py:536-543`: «Ширина» = 10 нм with «Размытие краёв δ» = 0.02 нм gives
T = 7.66·10⁻⁵ against the stationary reference 1.38·10⁻⁶ (shown failed, after 50 s). The cost refusal
(`viz.py:197-201`) advises «уменьшите ширину пакета, энергию или высоту потенциала» also in the oscillator scenario,
where only ħω and x₀ are shown (`hw` = 1 эВ, `x0` = 60 нм); the momentum refusal (`viz.py:165-170`) ends with «(review
V3-3)».

**Evidence:** `repro/r_v03_timing.out`; `results/v03_quantum_1d.jsonl` #61, #37, #38, #41, #42, #81.

**Suggested fix:** a grid or time-step criterion that resolves the evanescent decay across the whole barrier (or
refuse); scenario-aware advice; no review ids in user texts.

### P20 — nit — refusal prefixes use internal names (framework)

`visualizations/server/lfviz/sim.py:296`: «Действие boost: …», «Действие flash: …» — the action's id instead of its
label («Толчок», «Вспышка»).

### P21 — nit — v07: the reversal-speed reference loses precision at extreme settings

`visualizations/v07_bell_test/viz.py:257-260`, `:596-615`: at τ = 0.001 нс and L = 10⁵ м the bisection on Lorentz
matrices (cancellation of ~L against cτ) is off by 1.2·10⁻⁸ relative while the tolerance is 10⁻⁹, so `st_rev` fails.
Fix: a tolerance from ε·L/(cτ).

### P22 — nit — 3-D worlds: a slice plane moved past the box stays on its face and shows an empty window

`visualizations/server/lfviz/planes3d.py:57-64` clamps the plane's distance to the box; on the face the slice is all
NaN (v09 #58, «view_extreme»). Fix: clamp to the box shrunk by a grid step, or refuse «плоскость вне области».

### P23 — nit — failing checks that are honest

No change needed, or a note in the preset: v02 «triple_mod» fails `sork0` (the Sorkin parameter is not zero under
P ∝ |ψ|^2.4 — the point of the preset); v02 «vector_narrow» starts with `rs0` failed (0.41 > 1 %: the preset is
outside the paraxial domain by design; its label could say so); v06 «strong» fails `conv0` (the series does not converge
at α_s(M_Z) = 0.15 — the point of the preset); v06's level checks fail when κ or a_conf leave the fit (live parameters
without `standard`); v02 `grid`/`rs*` at extreme wavelengths; v16 `am_L`, `plane_1`, `table` in random extremes.

### P24 — should-fix — p04: every fluid other than «dfg» is refused from the defaults, and the advice names a step the owner cannot set

**Where:** `lfphys/lfphys/core/fluids/lbm.py:1188-1189` («неустойчиво: τ = 0.50008 слишком близко к 1/2 …; увеличьте
вязкость или уменьшите dx, или увеличьте dt»), `:1205-1206` («число Маха … уменьшите dt (или скорость)»), `:1210`
(«число Рейнольдса ячейки u·dx/ν = 149 > 25 …»), passed through by `visualizations/p04_fluids/viz.py` (the world chooses
dx = Lx/nx and dt from «u_max»; there is no dt parameter). «Жидкость» = вода, воздух or своя with the other defaults
(Lx = 2.2 м, nx = 440, u_max = 0.45 м/с) is refused at the start — invisible because of P1 — and the same refusals
come back as scene edits (inlet speed, lid speed) with «уменьшите dt».

**Evidence:** `results/p04_fluids.jsonl` #1, #2, #3 (single), #38 and the other `preset_edit` rows.

**Suggested fix:** translate the advice into the world's parameters («уменьшите «u_max» или увеличьте ν; больше
узлов nx»), and when the fluid changes in the form, propose a consistent set (e.g. scale u_max to a lattice Mach number
and Re of the cell within the limits), or show the admissible u_max for the chosen fluid and grid.

### P25 — error — p04: a thin or tall domain allocates the grid without a limit

**Where:** `lfphys/lfphys/core/fluids/lbm.py:1092-1093` (the arrays of the grid) with p04's ny = nx·Ly/Lx: «Lx» =
10⁻⁶ м with the default Ly gives 440 × 180 400 000 nodes — «Мир не создан: Unable to allocate 591. GiB for an array with
shape (440, 180400000) and data type float64»; «Ly» = 10⁴ м allocates 6.56 GiB per array (refused here only because of
the audit's 8 GB limit; the server's worker would try it); with nx = 1024 and Lx = min, Ly = max, 74.5 TiB.

A grid that fits in memory can still stall the world: random #21 (nx = 768, Ly/Lx = 6.8 → ~4·10⁶ nodes) spent more
than 2 min in one frame (killed).

**Evidence:** `results/p04_fluids.jsonl` #8, #11, #31 (and random rows with `MemoryError` at `lbm.py:1092/1093/1422`),
#188 (the stalled frame).

**Suggested fix:** a guard on the number of nodes (and on Ly/Lx) before allocating, in Russian: «область 10⁻⁶ × 0.41 м
на сетке nx = 440 — это 8·10¹⁰ узлов; при этом отношении сторон возьмите nx ≤ … или Lx ≥ …», with the limit set by
the time per frame as well as by memory.

### P27 — nit — p04: a velocity probe inside a body reads NaN without saying why

`visualizations/p04_fluids/viz.py` (probes in `frame()`): a «Датчик скорости» placed inside an obstacle (its default
position (0.1, 0.1) is inside a «Цилиндр» added with its defaults) sends NaN for ux, uy, |u| and p; the player shows
«—». Seen when every palette type is added to a preset (`results/p04_fluids.jsonl` #40, #44, #48, #56) and in random
scenes. Fix: «датчик внутри тела» in the inspector, or refuse placing it there.

### P26 — should-fix — v08: a source chosen from the defaults is refused after a minute of trial computation

**Where:** `visualizations/v08_wave_3d/engine/apparatus.py:223` (`choose_window`). «Источник» = круглое отверстие (or
«a» = 0.2, or «z_max» = 80) with the other defaults is refused — «окно расчёта мало для глубины z_max = 30 мкм … Уменьшите
z_max или возьмите источник шире» — but only after the window search has run (71–93 s on the CPU with 5 runs in
parallel; the owner's GPU is faster). The preset «circle» uses a = 3, z_max = 40. With P1 the owner waits and then sees
nothing. The texts themselves are good.

**Evidence:** `results/v08_wave_3d.jsonl` #2, #9, #16, #22, #27.

**Suggested fix:** an a-priori bound from the source's angular spectrum (a closed form for the circle) before the
search, so the refusal comes at once; or start from the preset's values when the source changes.

### P28 — error — p02: a refused removal leaves the object half-removed; «Очистить сцену» then fails with «Сцена: 'o1'»

**Where:** `visualizations/p02_quantum/viz.py:480-489` (`on_remove`) pops `self.ref[obj["id"]]` first and calls
`self.qs.remove(qid)` after; when the engine refuses (removing the magnetic field while a charged particle is in the
window: «поле нельзя менять, пока заряженная частица 1 в окне…», `lfphys/lfphys/core/quantum/scene.py:1508`), the
object stays in the scene (`server/lfviz/playground.py:204-208` deletes it only after `on_remove` returns) but is gone
from `ref`. Every later removal of it and «Очистить сцену» raise `KeyError` → toast «Сцена: 'o1'». This breaks the
contract of `playground.py:15-16` («raise ValueError to refuse: the scene is then left as it was»). `clear`
(`playground.py:228-232`) is also not atomic: a refusal in the middle leaves the scene half-cleared.

**Minimal reproduction:** p02 preset «cyclotron», play 3 s, remove «Магнитное поле» (refused, correctly), then «Очистить
сцену».

**Evidence:** `results/p02_quantum.jsonl` #38; `pw/cases4.json` → `pw/out4.json` (toasts «Сцена: поле нельзя менять…»,
then «Сцена: 'o1'»), `pw/shots/c_p02_cyclotron_remove_field_then_clear.png`.

**Suggested fix:** in `on_remove`, read `self.ref[...]`, call the engine, and delete the entry only after it succeeded;
in the framework's `clear`, check every removal first (or roll back), so that a refused clear leaves the scene whole.

### P29 — should-fix — p02: extreme edits make the wave NaN, and the next Bohm change crashes with «Probabilities contain NaN»

**Where:** after a series of edits to the extremes in the presets «trap» (the trap and the packet) and «tunnel», the
particle's probability in the window, the wave image and the checks become NaN (`balance_o2`, `energy_o2` = NaN, shown
as «—»); then «Траектории Бома» (or the packet's x) changes re-seed the Bohm points from |ψ|²
(`visualizations/p02_quantum/viz.py:496` → `_seed_bohm` `:608` → `_draw` `:621`, `rng.choice(p=w/w.sum())`) and numpy
raises «Probabilities contain NaN», shown as «Сцена: Probabilities contain NaN». The guard `_finite` (`viz.py:378-385`)
checks the objects' values on the grid, not the wave after the change. Related: a packet *added* at x = ±10⁶ нм (far
outside the 80 нм window) is accepted and its check «норма + поглощённое» is NaN from the first frame, while the same
position set as an *edit* is refused («пакет не помещается в окно по оси 0 …») — the two paths validate differently.

**Evidence:** `results/p02_quantum.jsonl` #33 (the sequence of edits is in its `ops` and `events`), #29, #51, #52, #70.

**Suggested fix:** after an accepted change, check that the wave stays finite (else roll back with «после этого
изменения волна перестала быть конечной: …»); in `_draw`, refuse with a Russian text when the weights are zero or not
finite («частица уже поглощена — нечего засевать»).

### P30 — should-fix — p02: each scene change in a running preset takes tens of seconds

Adding a «Детектор», «Метка пути», «Плоскость потока» or «Среда», or duplicating a packet or detector, in the presets
«double_slit», «which_path», «aharonov_bohm» took 30–44 s per change (8 runs in parallel on 16 cores; the scene
rebuilds its absorbers and the detectors' reflection by transfer matrices after every change, `viz.py:297-298`,
`:521-522`). The world does not move meanwhile and the change shows no progress. Some single edits to an extreme took
more than 2 min and were killed: «Плоскость потока» axis, «Метка пути» edge = 10⁶, «Детектор» y = ±10⁶ in the presets'
edit runs. Evidence: `results/p02_quantum.jsonl` #18, #19, #22, #23, #26 and the `preset_edit` rows (`slow`). Fix: compute the absorbers incrementally or in the background, and say «пересчёт
поглотителей…» while it runs.

### P31 — should-fix — p03: palette objects offered in the default (periodic) box are refused in English

**Where:** `visualizations/p03_molecules/viz.py:534` (`set_wall`) and `:554` (`set_piston`) pass the MD engine's English
`ValueError`s through (`lfphys/lfphys/core/md/system.py:895`, `:905`, `:930`, `:937`, `:1089`, `:1130`, `:1141`, `:372`;
`lfphys/lfphys/core/md/hard.py:338`, `:385`, `:455`). With the default «Границы» = периодические, adding «Стенка» from
the palette gives «Сцена: axis y is periodic», adding «Поршень» gives «Сцена: a piston needs a walled axis»; a charged
custom substance gives «charges in a box with a periodic axis: the Coulomb lattice sum (Ewald) is not implemented; use
walls on every axis»; crowded placements give «random placement jammed: 200 of 400 placed without overlaps; fewer
particles, a larger region or a lattice», «overlap: an inserted particle's potential energy … exceeds max_insert_energy»,
«overlapping hard particles», «region: hi > lo inside the walls», «a particle outside the walls on axis y». The palette
offers both objects in every box; only the presets with walls («piston») can take them.

**Evidence:** `results/p03_molecules.jsonl` (`palette`, `palette_param`, `preset_add` rows; the list «Every distinct
outcome» below).

**Suggested fix:** translate in p03 («у периодической оси нет стенок: выберите «Границы» = стенки (новый мир)», «поршню
нужна ось со стенками», «заряды в периодическом ящике не поддерживаются (нет суммы Эвальда): границы — стенки»), and
grey out or explain the palette entries that the current box cannot take.

### P32 — should-fix — p03: some edits crash the world (division by zero, overlapping atoms)

**Where and minimal reproductions:**
- `visualizations/p03_molecules/viz.py:441-449`: «Газ» with «Старт» = одинаковая скорость and T = 0, or with a single
  atom (after `vel -= vel.mean()` the velocities are all zero) → `speed / sqrt(mean(v²)) = 0/0` → «Сцена: float division by
  zero» (preset «piston», gas start → same_speed after T → 0; on the server, in the empty default world: add «Газ» with
  n = 1 and «Старт» = одинаковая скорость — `server/srv_out3.json`, which also shows the English wall and piston refusals
  of P31);
- `lfphys/lfphys/core/md/hard.py:731` (`pressure`): hard disks at T = 0 («Газ» T = 0 in the model «твёрдые шары») →
  `ZeroDivisionError` in every frame, shown as a traceback, the world pauses;
- `lfphys/lfphys/core/md/system.py:1231` and `:1551`: «Кристалл» T = 10⁵ K in the presets «melting» and «liquid_vapour»,
  or «Газ» added at T = 10⁵ K in the default box → «two interacting particles at the same point» / «a particle crossed the
  walls more than 64 times in one drift (dt too large)» as tracebacks; the time step is the world's (`dt_fs`), the
  temperature range goes to 10⁵ K.

**Evidence:** `results/p03_molecules.jsonl` #33, #247 (and 21 more rows at `hard.py:731`), #29, #37, #52.

**Suggested fix:** guard T = 0 and a single atom in `_gas` (no rescaling when the kinetic energy is zero); give the hard
model's pressure at T = 0 as undefined; refuse a temperature (or speed) whose displacement per step exceeds a fraction of
σ for the world's dt, in Russian («при T = 10⁵ K шаг 10 фс слишком велик: уменьшите T или dt_fs (новый мир)»).

### P33 — should-fix — p03: counts at their maxima stall the world for minutes

Setting «Газ» n = 20 000, «Молекулы» count = 2000 or «атомов в цепочке» = 50 in a running world (3-D LJ box, preset
«molecules») took more than 2 min for the one edit (killed), and adding 2000 molecules or 50-atom chains 38 s or more;
a 3-D hard-sphere random scene stalled a frame for more than 2 min; one random 3-D scene asked for an allocation of
several GiB in the cell list (`lfphys/lfphys/core/md/cells.py:132`, «Сцена: Unable to allocate … GiB»). The palette's
limits (n ≤ 20 000, count ≤ 2000) are not tied to the box or to the time per frame. Evidence:
`results/p03_molecules.jsonl` #335, #193, #41, #155, #157, #387, #386. Fix: a cost estimate per edit (particles ×
neighbours × steps per frame) with a Russian refusal, or placement in the background with progress.

## Every distinct outcome per world

Each line: the outcome class, how many combinations, the exception type and the raising line, the normalised text, one
example (combination id in `results/<world>.jsonl`, its description, the operation).

### p01_gravity

- **(h)** ×7 `ValueError` `visualizations/p01_gravity/viz.py:658 (__init__)` «Мир не создан: a² + Q² должно быть меньше #: иначе у дыры нет горизонта (голая сингулярность)» — e.g. #10 charge=max (+{'laws': 'kerr'}) · build ({'single': 1, 'pair': 2, 'random': 4})
- **(b)** ×22 `ValueError` `visualizations/p01_gravity/viz.py:713 (on_add)` «Сцена: круговая орбита — только в экваторе (θ = #°)» — e.g. #34 preset kerr_orbits: edit each object at extremes · op1:edit_all_extremes set body.theta=1.0 ({'preset_edit': 6, 'palette_param': 2, 'palette_edit': 2, 'random': 12})
- **(b)** ×21 `ValueError` `visualizations/p01_gravity/viz.py:722 (on_add)` «Сцена: скорость не меньше скорости света» — e.g. #34 preset kerr_orbits: edit each object at extremes · op1:edit_all_extremes set body.v_r=-0.99 ({'preset_edit': 12, 'palette_param': 4, 'palette_edit': 4, 'random': 1})
- **(b)** ×17 `ValueError` `visualizations/p01_gravity/viz.py:353 (_engine_edit)` «Сцена: тело оказалось бы точно в той же точке, что и другое: две точечные массы в одной точке (бесконечная сила) — так нельзя (копия массивного тела «в текущий » — e.g. #19 preset sun_earth: remove / duplicate each object while running · op1:dup_remove_all dup star ({'preset_remove': 14, 'palette_edit': 3})
- **(b)** ×16 `ValueError` `visualizations/server/lfviz/playground.py:178 (_add)` «Сцена: «Двойная (две компактные массы)»: не больше # в сцене» — e.g. #39 preset pn_inspiral: remove / duplicate each object while running · op1:dup_remove_all dup binary ({'preset_remove': 2, 'preset_add': 2, 'palette_edit': 1, 'random': 11})
- **(b)** ×10 `ValueError` `visualizations/p01_gravity/viz.py:709 (on_add)` «Сцена: r = # G M/c² — под горизонтом (r₊ = #)» — e.g. #34 preset kerr_orbits: edit each object at extremes · op1:edit_all_extremes set body.r=1.0 ({'preset_edit': 5, 'palette_param': 2, 'palette_edit': 2, 'random': 1})
- **(b)** ×9 `ValueError` `visualizations/p01_gravity/viz.py:738 (_observer_check)` «Сцена: круговая орбита — только в экваторе (θ = #°)» — e.g. #34 preset kerr_orbits: edit each object at extremes · op1:edit_all_extremes set observer.theta=1.0 ({'preset_edit': 4, 'palette_edit': 2, 'random': 3})
- **(b)** ×7 `ValueError` `visualizations/p01_gravity/viz.py:1060 (_start)` «Сцена: начальное расстояние не больше «остановить при» (# G m/c²)» — e.g. #155 [laws=pn] add binary r_stop=max · op0:scene ({'palette_param': 1, 'random': 6})
- **(b)** ×6 `ValueError` `visualizations/p01_gravity/viz.py:733 (_observer_check)` «Сцена: наблюдатель под горизонтом» — e.g. #34 preset kerr_orbits: edit each object at extremes · op1:edit_all_extremes set observer.r=1.0 ({'preset_edit': 2, 'palette_param': 1, 'palette_edit': 1, 'random': 2})
- **(b)** ×5 `ValueError` `visualizations/p01_gravity/viz.py:1057 (_start)` «Сцена: начальное расстояние не больше # G m/c²: ближе реакция излучения полных уравнений (#ПН + #ПН) уже не упорядоченный ряд, а у r ≈ # она меняет знак — начни» — e.g. #38 preset pn_inspiral: edit each object at extremes · op1:edit_all_extremes set binary.r0=8.0 ({'preset_edit': 2, 'palette_param': 1, 'palette_edit': 1, 'random': 1})
- **(b)** ×1 `ValueError` `visualizations/p01_gravity/viz.py:338 (_start_velocity)` «Сцена: круговая орбита: тело на оси z, проходящей через центр масс остальных тел, — плоскость орбиты не определена; сдвиньте его по x или y» — e.g. #245 random scene #35 [laws=newton] · op1:scene ({'random': 1})

### p02_quantum

- **(c)** ×17 `ValueError` `visualizations/p02_quantum/viz.py:621 (_draw)` «Сцена: Probabilities contain NaN» — e.g. #33 preset trap: edit each object at extremes · op1:edit_all_extremes set packet.bohm=300 ({'preset_edit': 15, 'random': 1, 'palette_edit': 1})
- **(c)** ×1 `KeyError` `visualizations/p02_quantum/viz.py:481 (on_remove)` «Сцена: 'o#'» — e.g. #38 preset cyclotron: remove / duplicate each object while running · op2:scene ({'preset_remove': 1})
- **(d)** ×18 `slow` `edit_all_extremes`  — e.g. #17 preset double_slit: edit each object at extremes · op1:edit_all_extremes set slit_wall.offset=1000000.0 31.6 s ({'preset_edit': 18})
- **(d)** ×15 `slow` `add_each_type`  — e.g. #23 preset which_path: add each palette type (defaults) · op1:add_each_type add detector 41.3 s ({'preset_add': 15})
- **(d)** ×6 `slow` `dup_remove_all`  — e.g. #18 preset double_slit: remove / duplicate each object while running · op1:dup_remove_all dup detector 41.6 s ({'preset_remove': 6})
- **(d)** ×1   «no progress for # s in op#:edit_all_extremes set plane.axis=# (killed; combination # s)» — e.g. #17 preset double_slit: edit each object at extremes · op1:edit_all_extremes set plane.axis=1 ({'preset_edit': 1})
- **(d)** ×1   «no progress for # s in op#:edit_all_extremes set marker.edge=# (killed; combination # s)» — e.g. #21 preset which_path: edit each object at extremes · op1:edit_all_extremes set marker.edge=0.0 ({'preset_edit': 1})
- **(d)** ×1   «no progress for # s in op#:edit_all_extremes set detector.y=# (killed; combination # s)» — e.g. #25 preset aharonov_bohm: edit each object at extremes · op1:edit_all_extremes set detector.y=1000000.0 ({'preset_edit': 1})
- **(b)** ×29 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1508 (_commit)` «Сцена: сетка не передаёт волну частицы #: её волновые числа доходят до # (|k| + #σ_k и энергия # которую потенциал может перевести в движение), а сетка рядом с » — e.g. #23 preset which_path: add each palette type (defaults) · op1:add_each_type add env ({'preset_add': 29})
- **(b)** ×17 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1586 (_prepare)` «Сцена: пакет: |k| + #σ_k = # по оси # больше π/d = # — сетка не передаёт волну (мельче сетку или меньше импульс)» — e.g. #33 preset trap: edit each object at extremes · op1:edit_all_extremes set packet.sx=0.001 ({'preset_edit': 9, 'palette_param': 2, 'palette': 1, 'palette_edit': 3, 'random': 2})
- **(b)** ×14 `ValueError` `lfphys/lfphys/core/quantum/scene.py:2033 (add_plane)` «Сцена: плоскость потока слишком близко к краю окна» — e.g. #29 preset tunnel: edit each object at extremes · op1:edit_all_extremes set plane.position=-1000000.0 ({'preset_edit': 2, 'palette_param': 2, 'palette_edit': 4, 'random': 6})
- **(b)** ×12 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1508 (_commit)` «Сцена: поле нельзя менять, пока заряженная частица # в окне там, где меняется векторный потенциал (вероятность #): импульс индукционного поля при переключении м» — e.g. #23 preset which_path: add each palette type (defaults) · op1:add_each_type add bfield ({'preset_add': 7, 'preset_remove': 2, 'preset_edit': 3})
- **(b)** ×11 `ValueError` `lfphys/lfphys/core/quantum/scene.py:505 (check)` «Сцена: шар: радиус # меньше # ширины края #: в центре у профиля излом (конус, наклон # от наибольшего) и он не достигает высоты (только # её); сделайте шар боль» — e.g. #90 [dim=2d] add ball radius=min · op0:scene ({'palette_param': 2, 'palette_edit': 3, 'palette': 1, 'random': 3, 'preset_edit': 2})
- **(b)** ×10 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1590 (_prepare)` «Сцена: пакет не помещается в окно по оси #: до края # нужно ≥ # (сетка периодична)» — e.g. #29 preset tunnel: edit each object at extremes · op1:edit_all_extremes set packet.sx=1000000.0 ({'preset_edit': 7, 'preset_add': 1, 'palette_param': 2})
- **(b)** ×7 `ValueError` `lfphys/lfphys/core/quantum/scene.py:608 (check)` «Сцена: щели перекрываются: расстояние между центрами должно быть больше полусуммы ширин» — e.g. #108 [dim=2d] add slit_wall width=max · op0:scene ({'palette_param': 2, 'palette_edit': 4, 'random': 1})
- **(b)** ×7 `ValueError` `lfphys/lfphys/core/quantum/scene.py:823 (check)` «Сцена: трубка потока: радиус # меньше # шага сетки — поле в трубке не разрешено» — e.g. #161 [dim=2d] add flux radius=min · op0:scene ({'palette_param': 1, 'palette_edit': 2, 'palette': 1, 'random': 3})
- **(b)** ×5 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1508 (_commit)` «Сцена: сетка не передаёт волну частицы #: её волновые числа доходят до # (|k| + #σ_k и энергия #, которую потенциал может перевести в движение), а сетка рядом с» — e.g. #33 preset trap: edit each object at extremes · op1:edit_all_extremes set trap.x=-1000000.0 ({'preset_edit': 5})
- **(b)** ×5 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1590 (_prepare)` «Сцена: пакет не помещается в окно по оси #: до края #, нужно ≥ # (сетка периодична)» — e.g. #33 preset trap: edit each object at extremes · op1:edit_all_extremes set packet.sx=1000000.0 ({'preset_edit': 2, 'random': 1, 'palette_edit': 2})
- **(b)** ×4 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1645 (replace_particle)` «Сцена: сетка не передаёт волну частицы #: её волновые числа доходят до # (|k| + #σ_k и энергия # которую потенциал может перевести в движение), а сетка рядом с » — e.g. #29 preset tunnel: edit each object at extremes · op1:edit_all_extremes set packet.species=neutron ({'preset_edit': 4})
- **(b)** ×4 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1501 (_commit)` «Сцена: на сцене заряженная частица: поле не вдоль одной оси сетки: для заряда строится только поле вдоль оси» — e.g. #37 preset cyclotron: edit each object at extremes · op1:edit_all_extremes set bfield.Bx=-100000.0 ({'preset_edit': 4})
- **(b)** ×3 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1621 (add_particle)` «Сцена: сетка не передаёт волну частицы #: её волновые числа доходят до # (|k| + #σ_k и энергия # которую потенциал может перевести в движение), а сетка рядом с » — e.g. #23 preset which_path: add each palette type (defaults) · op1:add_each_type add packet ({'preset_add': 3})
- **(b)** ×3 `ValueError` `lfphys/lfphys/core/quantum/scene.py:946 (check)` «Сцена: среда: длина локализации a = # меньше # шага сетки — гауссов скачок не разрешён» — e.g. #195 [dim=2d] add env length=min · op0:scene ({'palette_param': 1, 'palette_edit': 2})
- **(b)** ×3 `ValueError` `visualizations/server/lfviz/playground.py:178 (_add)` «Сцена: «Среда (декогеренция)»: не больше # в сцене» — e.g. #208 [dim=2d] env: edit every param to min/max while running · op3:dup_remove_all dup env ({'palette_edit': 2, 'random': 1})
- **(b)** ×3 `ValueError` `lfphys/lfphys/core/quantum/scene.py:1501 (_commit)` «Сцена: на сцене заряженная частица: у поля с градиентом орбитальная связь заряда не строится (нужен векторный потенциал вне плоскости)» — e.g. #243 random scene #5 [dim=2d] · op2:scene ({'random': 1, 'preset_edit': 2})

### p03_molecules

- **(c)** ×22 `ZeroDivisionError` `lfphys/lfphys/core/md/hard.py:731 (pressure)` «Traceback (most recent call last): File "/out/audit.py", line # in frames runner._frame((time.time() - a) * #) File "/lf/visualizations/server/lfviz/sim.py", li» — e.g. #247 [dim=2d,model=hard] add gas T=min · op1:frames ({'palette_param': 18, 'palette': 2, 'palette_edit': 2})
- **(c)** ×8 `FloatingPointError` `lfphys/lfphys/core/md/system.py:1231 (_pair_terms)` «Traceback (most recent call last): File "/out/audit.py", line # in frames runner._advance(runner.sim.t + runner.speed / FPS, budget=# / FPS) File "/lf/visualiza» — e.g. #29 preset melting: edit each object at extremes · op1:edit_all_extremes after crystal.T=100000.0 ({'preset_edit': 2, 'palette_param': 2, 'palette_edit': 4})
- **(c)** ×7 `ZeroDivisionError` `visualizations/p03_molecules/viz.py:449 (_gas)` «Сцена: float division by zero» — e.g. #33 preset piston: edit each object at extremes · op1:edit_all_extremes set gas.start=same_speed ({'preset_edit': 4, 'palette_edit': 3})
- **(c)** ×1 `FloatingPointError` `lfphys/lfphys/core/md/system.py:1551 (_walls_drift)` «Traceback (most recent call last): File "/out/audit.py", line # in frames runner._advance(runner.sim.t + runner.speed / FPS, budget=# / FPS) File "/lf/visualiza» — e.g. #37 preset liquid_vapour: edit each object at extremes · op1:edit_all_extremes after crystal.T=100000.0 ({'preset_edit': 1})
- **(c)** ×1 `FloatingPointError` `lfphys/lfphys/core/md/system.py:1231 (_pair_terms)` «Traceback (most recent call last): File "/out/audit.py", line # in frames runner._frame((time.time() - a) * #) File "/lf/visualizations/server/lfviz/sim.py", li» — e.g. #52 [dim=2d,model=lj] add gas T=max · op1:frames ({'palette_param': 1})
- **(c)** ×1 `MemoryError` `lfphys/lfphys/core/md/cells.py:132 (_emit)` «Сцена: Unable to allocate # GiB for an array with shape (#) and data type int#» — e.g. #386 random scene #6 [dim=3d,model=lj] · op0:scene ({'random': 1})
- **(d)** ×15 `slow` `edit_all_extremes`  — e.g. #335 [dim=3d,model=lj] gas: edit every param to min/max while running · op2:edit_all_extremes set gas.n=20000 120.1 s (killed) ({'palette_edit': 13, 'preset_edit': 2})
- **(d)** ×4 `slow` `scene`  — e.g. #155 [dim=2d,model=lj] add molecule atoms=max · op0:scene 38.3 s ({'palette_param': 2, 'random': 2})
- **(d)** ×4   «no progress for # s in op#:edit_all_extremes set molecule.count=# (killed; combination # s)» — e.g. #193 [dim=2d,model=lj] molecule: edit every param to min/max while running · op2:edit_all_extremes set molecule.count=2000 ({'palette_edit': 4})
- **(d)** ×3   «no progress for # s in op#:scene (killed; combination # s)» — e.g. #157 [dim=2d,model=lj] add molecule count=max · op0:scene ({'palette_param': 1, 'random': 2})
- **(d)** ×3   «no progress for # s in op#:edit_all_extremes set gas.n=# (killed; combination # s)» — e.g. #335 [dim=3d,model=lj] gas: edit every param to min/max while running · op2:edit_all_extremes set gas.n=20000 ({'palette_edit': 3})
- **(d)** ×1   «no progress for # s in op#:edit_all_extremes set molecule.atoms=# (killed; combination # s)» — e.g. #41 preset molecules: edit each object at extremes · op1:edit_all_extremes set molecule.atoms=50 ({'preset_edit': 1})
- **(d)** ×1   «no progress for # s in op#:frames frame # (killed; combination # s)» — e.g. #387 random scene #7 [dim=3d,model=hard] · op4:frames frame 0 ({'random': 1})
- **(d)** ×1 `slow` `frames`  — e.g. #387 random scene #7 [dim=3d,model=hard] · op4:frames frame 0 120.4 s (killed) ({'random': 1})
- **(d)** ×1   «no progress for # s in op#:edit_all_extremes after crystal.T=# frame # (killed; combination # s)» — e.g. #373 [dim=3d,model=hard] crystal: edit every param to min/max while running · op2:edit_all_extremes after crystal.T=100000.0 frame 0 ({'palette_edit': 1})
- **(f)** ×25 `ValueError` `lfphys/lfphys/core/md/system.py:930 (set_piston)` «Сцена: a piston needs a walled axis» — e.g. #27 preset maxwell: add each palette type (defaults) · op1:add_each_type add piston ({'preset_add': 3, 'palette': 4, 'palette_param': 9, 'palette_edit': 4, 'random': 5})
- **(f)** ×21 `ValueError` `lfphys/lfphys/core/md/system.py:895 (set_wall)` «Сцена: axis y is periodic» — e.g. #27 preset maxwell: add each palette type (defaults) · op1:add_each_type add wall ({'preset_add': 3, 'palette': 4, 'palette_param': 5, 'palette_edit': 4, 'random': 5})
- **(f)** ×19 `ValueError` `lfphys/lfphys/core/md/system.py:1130 (_derived)` «Сцена: charges in a box with a periodic axis: the Coulomb lattice sum (Ewald) is not implemented; use walls on every axis» — e.g. #69 [dim=2d,model=lj] add gas charge=min · op0:scene ({'palette_param': 6, 'palette_edit': 12, 'random': 1})
- **(f)** ×12 `ValueError` `lfphys/lfphys/core/md/system.py:372 (random_sites)` «Сцена: random placement jammed: # of # placed without overlaps; fewer particles, a larger region or a lattice» — e.g. #33 preset piston: edit each object at extremes · op1:edit_all_extremes set gas.n=20000 ({'preset_edit': 3, 'palette_param': 4, 'palette_edit': 3, 'preset_add': 1, 'random': 1})
- **(f)** ×11 `ValueError` `lfphys/lfphys/core/md/system.py:1089 (_transaction)` «Сцена: overlap: an inserted particle's potential energy # exceeds max_insert_energy = #» — e.g. #30 preset melting: remove / duplicate each object while running · op1:dup_remove_all dup crystal ({'preset_remove': 2, 'preset_add': 8, 'palette_param': 1})
- **(f)** ×11 `ValueError` `lfphys/lfphys/core/md/hard.py:385 (set_wall)` «Сцена: a periodic axis has no walls» — e.g. #47 preset hard_disks: add each palette type (defaults) · op1:add_each_type add wall ({'preset_add': 1, 'palette': 2, 'palette_param': 5, 'palette_edit': 2, 'random': 1})
- **(f)** ×7 `ValueError` `lfphys/lfphys/core/md/hard.py:455 (_check)` «Сцена: overlapping hard particles» — e.g. #47 preset hard_disks: add each palette type (defaults) · op1:add_each_type add crystal ({'preset_add': 2, 'palette_param': 2, 'palette_edit': 3})
- **(f)** ×6 `ValueError` `lfphys/lfphys/core/md/hard.py:338 (fill)` «Сцена: region: hi > lo inside the walls» — e.g. #45 preset hard_disks: edit each object at extremes · op1:edit_all_extremes set gas.sx=1000.0 ({'preset_edit': 2, 'palette_edit': 4})
- **(f)** ×4 `ValueError` `lfphys/lfphys/core/md/system.py:895 (set_wall)` «Сцена: axis x is periodic» — e.g. #136 [dim=2d,model=lj] add wall axis=x · op0:scene ({'palette_param': 1, 'random': 3})
- **(f)** ×4 `ValueError` `lfphys/lfphys/core/md/system.py:1117 (_derived)` «Сцена: the pair cutoff + skin # exceeds half a periodic box length #» — e.g. #392 random scene #12 [dim=3d,model=lj] · op0:scene ({'random': 4})
- **(f)** ×3 `ValueError` `lfphys/lfphys/core/md/system.py:937 (set_piston)` «Сцена: # < x_min <= X <= L, mass > # finite p_ext and V» — e.g. #39 preset liquid_vapour: add each palette type (defaults) · op1:add_each_type add piston ({'preset_add': 1, 'preset_edit': 2})
- **(f)** ×3 `ValueError` `lfphys/lfphys/core/md/system.py:1141 (_check_inside)` «Сцена: a particle outside the walls on axis y» — e.g. #33 preset piston: edit each object at extremes · op1:edit_all_extremes set gas.y=-1000.0 ({'preset_edit': 3})
- **(f)** ×3 `ValueError` `lfphys/lfphys/core/md/system.py:1141 (_check_inside)` «Сцена: a particle outside the walls on axis x» — e.g. #33 preset piston: edit each object at extremes · op1:edit_all_extremes set gas.sx=1000.0 ({'preset_edit': 2, 'random': 1})
- **(f)** ×2 `ValueError` `lfphys/lfphys/core/md/hard.py:221 (_grid)` «Мир не создан: a periodic box length must be >= # times the largest diameter (#)» — e.g. #385 random scene #5 [dim=3d,model=hard] · build ({'random': 2})
- **(f)** ×1 `ValueError` `lfphys/lfphys/core/md/system.py:905 (set_wall)` «Сцена: the hi side of this axis is the piston» — e.g. #33 preset piston: edit each object at extremes · op1:edit_all_extremes set wall.side=hi ({'preset_edit': 1})
- **(b)** ×7 `ValueError` `visualizations/server/lfviz/playground.py:178 (_add)` «Сцена: «Поле (тяжесть)»: не больше # в сцене» — e.g. #38 preset liquid_vapour: remove / duplicate each object while running · op1:dup_remove_all dup gravity ({'preset_remove': 1, 'preset_add': 1, 'palette_edit': 4, 'random': 1})
- **(b)** ×4 `ValueError` `visualizations/p03_molecules/viz.py:479 (_molecules)` «Сцена: не удалось разместить # молекул без перекрытий: размещено #; уменьшите число или увеличьте область» — e.g. #184 [dim=2d,model=lj] add molecule charge=min · op0:scene ({'palette_param': 3, 'preset_add': 1})
- **(b)** ×2 `ValueError` `visualizations/server/lfviz/playground.py:178 (_add)` «Сцена: «Поршень»: не больше # в сцене» — e.g. #34 preset piston: remove / duplicate each object while running · op1:dup_remove_all dup piston ({'preset_remove': 1, 'preset_add': 1})

### p04_fluids

- **(c)** ×5 `MemoryError` `lfphys/lfphys/core/fluids/lbm.py:1093 (__init__)` «Мир не создан: Unable to allocate # GiB for an array with shape (# #) and data type float#» — e.g. #8 Lx=min · build ({'single': 2, 'random': 3})
- **(c)** ×1 `MemoryError` `lfphys/lfphys/core/fluids/lbm.py:1092 (__init__)` «Мир не создан: Unable to allocate # TiB for an array with shape (#) and data type int#» — e.g. #31 Lx=min, Ly=max, nx=1024 · build ({'pair': 1})
- **(c)** ×1 `MemoryError` `lfphys/lfphys/core/fluids/lbm.py:1092 (__init__)` «Мир не создан: Unable to allocate # GiB for an array with shape (#) and data type float#» — e.g. #186 random scene #19 [default] · build ({'random': 1})
- **(c)** ×1 `MemoryError` `lfphys/lfphys/core/fluids/lbm.py:1422 (_build)` «Мир не создан: Unable to allocate # MiB for an array with shape (# #) and data type int#» — e.g. #190 random scene #23 [default] · build ({'random': 1})
- **(d)** ×4 `slow` `frames`  — e.g. #188 random scene #21 [default] · op5:frames frame 0 120.3 s (killed) ({'random': 4})
- **(d)** ×1   «no progress for # s in op#:frames frame # (killed; combination # s)» — e.g. #188 random scene #21 [default] · op5:frames frame 0 ({'random': 1})
- **(f)** ×55 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1205 (_check_numbers)` «Сцена: число Маха # > #: ошибка сжимаемости O(Ma²) слишком велика (и схема неустойчива); уменьшите dt (или скорость)» — e.g. #38 preset cylinder_re20: edit each object at extremes · op1:edit_all_extremes set inlet.speed=-10000.0 ({'preset_edit': 10, 'palette_param': 14, 'palette_edit': 4, 'random': 27})
- **(f)** ×21 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1188 (_check_numbers)` «Мир не создан: неустойчиво: τ = # слишком близко к #/# (нужно τ − #/# ≥ #); увеличьте вязкость или уменьшите dx, или увеличьте dt» — e.g. #1 fluid=water · build ({'single': 7, 'pair': 5, 'random': 9})
- **(h)** ×3 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1210 (_check_numbers)` «Мир не создан: число Рейнольдса ячейки u·dx/ν = # > #: сетка не разрешает течение (неустойчиво); уменьшите dx или скорость, или увеличьте вязкость» — e.g. #2 fluid=air · build ({'single': 1, 'random': 2})
- **(b)** ×26 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:2131 (change)` «Сцена: интерполированные стенки — только у неподвижной поверхности (подвижная — по Ладду)» — e.g. #38 preset cylinder_re20: edit each object at extremes · op1:edit_all_extremes set disk.vx=-10000.0 ({'preset_edit': 16, 'palette_edit': 10})
- **(b)** ×12 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «справа» уже занята объектом «Выход»» — e.g. #39 preset cylinder_re20: remove / duplicate each object while running · op1:dup_remove_all dup outlet ({'preset_remove': 4, 'preset_add': 4, 'preset_edit': 4})
- **(b)** ×9 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «слева» уже занята объектом «Вход (парабола, # м/с)»» — e.g. #39 preset cylinder_re20: remove / duplicate each object while running · op1:dup_remove_all dup inlet ({'preset_remove': 3, 'preset_add': 6})
- **(b)** ×9 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1267 (_check_densities)` «Сцена: объёмная сила (# #) м/с² (гидростатический перепад g·L/c_s² = #): плотность покоя схемы отклонилась бы от ρ# на # > # (в точке (# #) м; масштаб давления » — e.g. #40 preset cylinder_re20: add each palette type (defaults) · op1:add_each_type add gravity ({'preset_add': 1, 'palette_param': 4, 'palette': 1, 'palette_edit': 1, 'random': 2})
- **(b)** ×9 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1267 (_check_densities)` «Сцена: давление выхода (right) # Па: плотность покоя схемы отклонилась бы от ρ# на # > # (масштаб давления схемы c_s²ρ(dx/dt)² = # Па, её скорость звука c_s = #» — e.g. #131 [default] add outlet pressure=min · op0:scene ({'palette_param': 2, 'random': 5, 'preset_edit': 2})
- **(b)** ×6 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1267 (_check_densities)` «Сцена: давление выхода (bottom) # Па: плотность покоя схемы отклонилась бы от ρ# на # > # (масштаб давления схемы c_s²ρ(dx/dt)² = # Па, её скорость звука c_s = » — e.g. #38 preset cylinder_re20: edit each object at extremes · op1:edit_all_extremes set outlet.pressure=-1000000000.0 ({'preset_edit': 6})
- **(b)** ×6 `ValueError` `visualizations/p04_fluids/viz.py:391 (on_add)` «Сцена: в этом мире нет красителя (законы мира: «Краситель — есть»)» — e.g. #176 random scene #9 [default] · op1:scene ({'random': 6})
- **(b)** ×5 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «слева» уже занята объектом «Поток»» — e.g. #55 preset airfoil: remove / duplicate each object while running · op1:dup_remove_all dup inlet ({'preset_remove': 1, 'preset_add': 2, 'preset_edit': 2})
- **(b)** ×4 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «слева» уже занята объектом «Периодичность #»» — e.g. #176 random scene #9 [default] · op3:scene ({'random': 4})
- **(b)** ×3 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Вход (парабола, # м/с)»» — e.g. #38 preset cylinder_re20: edit each object at extremes · op1:edit_all_extremes set outlet.side=top ({'preset_edit': 3})
- **(b)** ×3 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «снизу» уже занята объектом «Сверху и снизу — периодичность (решётка профилей)»» — e.g. #55 preset airfoil: remove / duplicate each object while running · op1:dup_remove_all dup periodic ({'preset_remove': 1, 'preset_edit': 2})
- **(b)** ×3 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Сверху и снизу — периодичность (решётка профилей)»» — e.g. #56 preset airfoil: add each palette type (defaults) · op1:add_each_type add lid ({'preset_add': 1, 'preset_edit': 2})
- **(b)** ×3 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:1267 (_check_densities)` «Сцена: давление выхода (top) # Па: плотность покоя схемы отклонилась бы от ρ# на # > # (масштаб давления схемы c_s²ρ(dx/dt)² = # Па, её скорость звука c_s = # м» — e.g. #133 [default] outlet: edit every param to min/max while running · op2:edit_all_extremes set outlet.pressure=-1000000000.0 ({'palette_edit': 2, 'random': 1})
- **(b)** ×2 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Крышка»» — e.g. #47 preset cavity: remove / duplicate each object while running · op1:dup_remove_all dup lid ({'preset_remove': 1, 'preset_add': 1})
- **(b)** ×2 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «справа» уже занята объектом «Периодичность #»» — e.g. #205 random scene #38 [default] · op4:scene ({'random': 2})
- **(b)** ×2 `ValueError` `lfphys/lfphys/core/fluids/lbm.py:2102 (change)` «Сцена: интерполированные стенки — только у неподвижной поверхности (подвижная — по Ладду)» — e.g. #194 random scene #27 [default] · op0:scene ({'random': 2})
- **(b)** ×1 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «слева» уже занята объектом «Вход потока #»» — e.g. #48 preset cavity: add each palette type (defaults) · op1:add_each_type add periodic ({'preset_add': 1})
- **(b)** ×1 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Вход потока #»» — e.g. #126 [default] inlet: edit every param to min/max while running · op3:dup_remove_all dup inlet ({'palette_edit': 1})
- **(b)** ×1 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Выход (давление) #»» — e.g. #133 [default] outlet: edit every param to min/max while running · op3:dup_remove_all dup outlet ({'palette_edit': 1})
- **(b)** ×1 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «снизу» уже занята объектом «Периодичность #»» — e.g. #143 [default] periodic: edit every param to min/max while running · op3:dup_remove_all dup periodic ({'palette_edit': 1})
- **(b)** ×1 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Подвижная стенка #»» — e.g. #140 [default] lid: edit every param to min/max while running · op3:dup_remove_all dup lid ({'palette_edit': 1})
- **(b)** ×1 `ValueError` `visualizations/p04_fluids/viz.py:355 (_claim)` «Сцена: сторона «сверху» уже занята объектом «Периодичность #»» — e.g. #187 random scene #20 [default] · op1:scene ({'random': 1})

### v01_light_travel

- **(f)** ×1 `ValueError` `lfphys/lfphys/core/relativity.py:83 (metric_clock_rate)` «Мир не создан: worldline is not timelike (moves at or faster than local light)» — e.g. #277 random #42 · build ({'random': 1})
- **(h)** ×14 `ValueError` `visualizations/v01_light_travel/viz.py:141 (__init__)` «Мир не создан: ОТО требует СТО: метрика Шварцшильда локально лоренцева. Для эфира или баллистики выберите «Без гравитации» или «Ньютон» (только баллистика).» — e.g. #4 kinematics=ether · build ({'single': 2, 'pair': 4, 'random': 8})
- **(h)** ×11 `ValueError` `visualizations/v01_light_travel/viz.py:191 (_scn_sun_earth)` «Мир не создан: радиус Солнца меньше # rs: возьмите сценарий «линза»» — e.g. #8 c_factor=min · build ({'single': 3, 'pair': 2, 'all': 1, 'random': 5})
- **(h)** ×9 `ValueError` `visualizations/v01_light_travel/viz.py:141 (__init__)` «Мир не создан: Ньютоново притяжение света имеет смысл только для корпускул, то есть для баллистической кинематики.» — e.g. #6 gravity=newton · build ({'single': 1, 'random': 8})
- **(b)** ×2 `ValueError` `visualizations/v01_light_travel/engine/world.py:532 (_validate_path)` «Действие boost: при постоянной координатной скорости «Наблюдатель» через # с двигался бы быстрее света для местного статичного наблюдателя; в ОТО «скорость» — к» — e.g. #205 preset lensing: action boost v=max · op1:action_pick boost v=max ({'preset_action': 2})

### v02_double_slit

- **(c)** ×6 `MemoryError` `visualizations/v02_double_slit/viz.py:1034 (advance)` «Traceback (most recent call last): File "/out/audit.py", line # in frames runner._advance(runner.sim.t + runner.speed / FPS, budget=# / FPS) File "/lf/visualiza» — e.g. #412 preset triple: set dark_rate over [0.0, 1000000000000.0] · op4:frames ({'preset_live': 2, 'random': 4})
- **(c)** ×2   «worker process died (exit code #)» — e.g. #133 dark_rate=max · op0:frames frame 0 ({'single': 1, 'live': 1})
- **(c)** ×2 `MemoryError` `lfphys/lfphys/theories/approx/paraxial.py:64 (slit_amplitudes)` «Изменение не применено: Unable to allocate # GiB for an array with shape (#) and data type complex#» — e.g. #424 preset electron_eraser: set mic_lambda_nm over [0.001, 1000000000.0] · op2:set ({'preset_live': 2})
- **(d)** ×4 `slow` `set`  — e.g. #242 set species=electron, energy_by=speed, speed_ms=max · op1:set 30.8 s ({'pair_live': 1, 'random': 3})
- **(d)** ×3 `slow` `build`  — e.g. #461 random #8 · build 93.3 s ({'random': 3})
- **(d)** ×2 `slow` `action_pick`  — e.g. #469 random #16 · op5:action_pick clear default 35.4 s ({'random': 2})
- **(d)** ×1   «no progress for # s in build (killed; combination # s)» — e.g. #491 random #38 · build ({'random': 1})
- **(f)** ×4 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Мир не создан: элемент 'rot_y' не подходит для этой частицы» — e.g. #185 el1=rot_y · build ({'single': 2, 'random': 2})
- **(f)** ×4 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Мир не создан: элемент 'filter' не подходит для этой частицы» — e.g. #187 el1=filter · build ({'single': 2, 'random': 2})
- **(f)** ×4 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Изменение не применено: элемент 'rot_y' не подходит для этой частицы» — e.g. #186 set el1=rot_y · op1:set ({'live': 2, 'preset_live': 2})
- **(f)** ×4 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Изменение не применено: элемент 'filter' не подходит для этой частицы» — e.g. #188 set el1=filter · op1:set ({'live': 2, 'preset_live': 2})
- **(f)** ×2 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Изменение не применено: элемент 'polarizer' не подходит для этой частицы» — e.g. #440 preset electron: set el2 over ['none', 'polarizer', 'hwp', 'qwp', 'rot_y', 'filter', 'phas · op3:set ({'preset_live': 2})
- **(f)** ×2 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Изменение не применено: элемент 'hwp' не подходит для этой частицы» — e.g. #440 preset electron: set el2 over ['none', 'polarizer', 'hwp', 'qwp', 'rot_y', 'filter', 'phas · op5:set ({'preset_live': 2})
- **(f)** ×2 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Изменение не применено: элемент 'qwp' не подходит для этой частицы» — e.g. #440 preset electron: set el2 over ['none', 'polarizer', 'hwp', 'qwp', 'rot_y', 'filter', 'phas · op7:set ({'preset_live': 2})
- **(f)** ×1 `ValueError` `lfphys/lfphys/theories/approx/paraxial_ensemble.py:151 (_extended)` «Мир не создан: array is too big; `arr.size * arr.dtype.itemsize` is larger than the maximum possible size.» — e.g. #297 collapse=grw, grw_lambda=max, grw_rc_nm=min, species=c60 · build ({'pair': 1})
- **(f)** ×1 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Мир не создан: элемент 'qwp' не подходит для этой частицы» — e.g. #455 random #2 · build ({'random': 1})
- **(f)** ×1 `ValueError` `lfphys/lfphys/core/quantum/marks.py:89 (element_matrix)` «Мир не создан: элемент 'hwp' не подходит для этой частицы» — e.g. #483 random #30 · build ({'random': 1})
- **(h)** ×22 `ValueError` `visualizations/v02_double_slit/viz.py:269 (_build)` «Мир не создан: период щелей должен быть больше ширины щели» — e.g. #103 a_um=max · build ({'single': 2, 'pair': 3, 'random': 17})
- **(h)** ×18 `ValueError` `visualizations/v02_double_slit/viz.py:376 (_apparatus)` «Мир не создан: рассеяние фотона-зонда здесь задаётся дипольной диаграммой: она есть у заряженных (томсоновское) и поляризуемых (рэлеевское) частиц; для фотона и» — e.g. #137 wp_mode=microscope · build ({'single': 13, 'pair': 2, 'random': 3})
- **(h)** ×9 `ValueError` `lfphys/lfphys/core/quantum/particles.py:98 (make)` «Мир не создан: для фотона задайте длину волны, энергию или частоту» — e.g. #13 energy_by=speed · build ({'single': 3, 'pair': 1, 'random': 5})
- **(h)** ×7 `ValueError` `visualizations/v02_double_slit/viz.py:382 (_apparatus)` «Мир не создан: щели №# нет» — e.g. #141 wp_slit=max (+{'wp_mode': 'qubit'}) · build ({'single': 1, 'pair': 2, 'random': 4})
- **(h)** ×5 `ValueError` `visualizations/v02_double_slit/viz.py:1183 (_vector_check)` «Мир не создан: экран-проводник (векторная дифракция) задан только для фотонов» — e.g. #295 screen_model=pec, species=electron · build ({'pair': 1, 'random': 4})
- **(h)** ×4 `ValueError` `visualizations/v02_double_slit/viz.py:1190 (_vector_check)` «Мир не создан: экран-проводник: щель шире # λ (k·a = # > #) — векторное решение здесь не считается (дорого); скалярная модель для таких щелей отличается от вект» — e.g. #121 screen_model=pec · build ({'single': 3, 'random': 1})
- **(h)** ×4 `ValueError` `lfphys/lfphys/core/quantum/particles.py:118 (make)` «Мир не создан: для массивной частицы задайте длину волны, кинетическую энергию или скорость» — e.g. #453 random #0 · build ({'random': 4})
- **(h)** ×3 `ValueError` `visualizations/v02_double_slit/viz.py:1187 (_vector_check)` «Мир не создан: экран-проводник: источник должен быть монохроматическим (ширина спектра #)» — e.g. #470 random #17 · build ({'random': 3})
- **(h)** ×3 `ValueError` `visualizations/v02_double_slit/viz.py:1185 (_vector_check)` «Мир не создан: экран-проводник: падающая волна должна быть плоской (расстояние источника #)» — e.g. #487 random #34 · build ({'random': 3})
- **(h)** ×1 `ValueError` `visualizations/v02_double_slit/viz.py:373 (_apparatus)` «Мир не создан: у этой частицы нет внутреннего состояния: анализатор не на что действовать» — e.g. #489 random #36 · build ({'random': 1})
- **(b)** ×24 `ValueError` `visualizations/v02_double_slit/viz.py:376 (_apparatus)` «Изменение не применено: рассеяние фотона-зонда здесь задаётся дипольной диаграммой: она есть у заряженных (томсоновское) и поляризуемых (рэлеевское) частиц; для» — e.g. #138 set wp_mode=microscope · op1:set ({'live': 13, 'pair_live': 2, 'preset_live': 9})
- **(b)** ×9 `ValueError` `visualizations/v02_double_slit/viz.py:269 (_build)` «Изменение не применено: период щелей должен быть больше ширины щели» — e.g. #104 set a_um=max · op1:set ({'live': 2, 'pair_live': 3, 'preset_live': 4})
- **(b)** ×6 `ValueError` `lfphys/lfphys/core/quantum/particles.py:98 (make)` «Изменение не применено: для фотона задайте длину волны, энергию или частоту» — e.g. #14 set energy_by=speed · op1:set ({'live': 3, 'pair_live': 1, 'preset_live': 2})
- **(b)** ×6 `ValueError` `visualizations/v02_double_slit/viz.py:1183 (_vector_check)` «Изменение не применено: экран-проводник (векторная дифракция) задан только для фотонов» — e.g. #296 set screen_model=pec, species=electron · op1:set ({'pair_live': 1, 'preset_live': 5})
- **(b)** ×5 `ValueError` `visualizations/v02_double_slit/viz.py:382 (_apparatus)` «Изменение не применено: щели №# нет» — e.g. #142 set wp_slit=max (+{'wp_mode': 'qubit'}) · op2:set ({'live': 1, 'pair_live': 2, 'preset_live': 2})
- **(b)** ×3 `ValueError` `visualizations/v02_double_slit/viz.py:1190 (_vector_check)` «Изменение не применено: экран-проводник: щель шире # λ (k·a = # > #) — векторное решение здесь не считается (дорого); скалярная модель для таких щелей отличаетс» — e.g. #122 set screen_model=pec · op1:set ({'live': 3})
- **(b)** ×2 `ValueError` `lfphys/lfphys/core/quantum/particles.py:118 (make)` «Изменение не применено: для массивной частицы задайте длину волны, кинетическую энергию или скорость» — e.g. #368 preset electron_microscope: set freq_thz over [1e-06, 1000000000000.0] · op1:set ({'preset_live': 2})
- **(b)** ×2 `ValueError` `visualizations/v02_double_slit/viz.py:380 (_apparatus)` «Изменение не применено: поляризация (ось диполя) зонда не может совпадать с направлением его распространения» — e.g. #429 preset c60_grw: set mic_dir over ['x', 'y', 'z'] · op6:set ({'preset_live': 2})
- **(b)** ×1 `ValueError` `visualizations/v02_double_slit/viz.py:373 (_apparatus)` «Изменение не применено: у этой частицы нет внутреннего состояния: анализатор не на что действовать» — e.g. #447 preset c60: set analyzer_angle over [-180, 180] · op1:set ({'preset_live': 1})

### v03_quantum_1d

- **(d)** ×40 `slow` `set`  — e.g. #2 set energy=min · op1:set 54.8 s ({'live': 4, 'pair_live': 4, 'preset_live': 7, 'random': 25})
- **(d)** ×15 `slow` `build`  — e.g. #25 width=max · build 76.4 s ({'single': 2, 'pair': 2, 'random': 11})
- **(d)** ×8   «no progress for # s in op#:set (killed; combination # s)» — e.g. #12 set scenario=step · op1:set ({'live': 1, 'pair_live': 2, 'random': 5})
- **(f)** ×5 `ValueError` `visualizations/v03_quantum_1d/viz.py:201 (_build)` «Изменение не применено: этот опыт слишком дорог для живого мира: сетка # точек × # шагов (≈ # с счёта); уменьшите ширину пакета, энергию или высоту потенциала» — e.g. #38 set hw=max (+{'scenario': 'oscillator'}) · op2:set ({'live': 2, 'preset_live': 3})
- **(f)** ×3 `ValueError` `visualizations/v03_quantum_1d/viz.py:201 (_build)` «Мир не создан: этот опыт слишком дорог для живого мира: сетка # точек × # шагов (≈ # с счёта); уменьшите ширину пакета, энергию или высоту потенциала» — e.g. #37 hw=max (+{'scenario': 'oscillator'}) · build ({'single': 2, 'random': 1})
- **(h)** ×15 `ValueError` `visualizations/v03_quantum_1d/viz.py:201 (_build)` «Мир не создан: этот опыт слишком дорог для живого мира: сетка # точек × # шагов (≈ # с счёта); уменьшите ширину пакета, энергию или высоту потенциала» — e.g. #51 energy=min, V0=max, width=max · build ({'pair': 5, 'all': 1, 'random': 9})
- **(h)** ×2 `ValueError` `visualizations/v03_quantum_1d/viz.py:167 (_build)` «Мир не создан: пакет слишком широк по импульсу: при E = # эВ нужна σ ≥ # нм — медленный край пакета (k₀ − #·ħ/(#σ)) должен иметь не меньше # эВ: более медленные» — e.g. #81 all numeric at min · build ({'all': 1, 'random': 1})
- **(h)** ×1 `ValueError` `visualizations/v03_quantum_1d/viz.py:182 (_build)` «Мир не создан: нужна сетка из # точек (больше #): уменьшите смещение x₀ или ħω ловушки» — e.g. #69 scenario=oscillator, hw=max, x0=max, energy=max · build ({'pair': 1})
- **(b)** ×9 `ValueError` `visualizations/v03_quantum_1d/viz.py:201 (_build)` «Изменение не применено: этот опыт слишком дорог для живого мира: сетка # точек × # шагов (≈ # с счёта); уменьшите ширину пакета, энергию или высоту потенциала» — e.g. #52 set energy=min, V0=max, width=max · op1:set ({'pair_live': 5, 'preset_live': 2, 'random': 2})
- **(b)** ×1 `ValueError` `visualizations/v03_quantum_1d/viz.py:182 (_build)` «Изменение не применено: нужна сетка из # точек (больше #): уменьшите смещение x₀ или ħω ловушки» — e.g. #70 set scenario=oscillator, hw=max, x0=max, energy=max · op1:set ({'pair_live': 1})

### v04_orbits

- **(h)** ×34 `ValueError` `visualizations/v04_orbits/viz.py:198 (_launch_data)` «Мир не создан: r₀ = #M внутри тела (радиус #M)» — e.g. #5 radius_km=max · build ({'single': 1, 'pair': 2, 'random': 31})
- **(h)** ×6 `ValueError` `visualizations/v04_orbits/viz.py:160 (__init__)` «Мир не создан: радиус # км не больше #M = # км: такое тело — чёрная дыра (задайте радиус #)» — e.g. #22 mass_msun=max, radius_km=max · build ({'pair': 1, 'all': 1, 'random': 4})
- **(h)** ×4 `ValueError` `visualizations/v04_orbits/viz.py:204 (_launch_data)` «Мир не создан: локальная скорость # c не меньше скорости света» — e.g. #6 r0=min · build ({'single': 1, 'pair': 2, 'random': 1})
- **(b)** ×7 `ValueError` `visualizations/v04_orbits/viz.py:407 (action)` «Действие boost: тела на орбите нет (падение за горизонт)» — e.g. #54 preset default: action boost dv=min · op4:action ({'preset_action': 7})
- **(b)** ×5 `ValueError` `visualizations/v04_orbits/viz.py:204 (_launch_data)` «Изменение не применено: локальная скорость # c не меньше скорости света» — e.g. #7 set r0=min · op1:set ({'live': 1, 'pair_live': 2, 'preset_live': 2})
- **(b)** ×5 `ValueError` `visualizations/v04_orbits/viz.py:407 (action)` «Действие boost: тела на орбите нет (уход на бесконечность)» — e.g. #55 preset default: action boost dv=max · op4:action ({'preset_action': 5})
- **(b)** ×3 `ValueError` `visualizations/v04_orbits/viz.py:198 (_launch_data)` «Изменение не применено: r₀ = #M внутри тела (радиус #M)» — e.g. #58 preset mercury: set r0 over [2.1, 100000000.0] · op1:set ({'preset_live': 2, 'random': 1})
- **(b)** ×2 `ValueError` `visualizations/v04_orbits/viz.py:407 (action)` «Действие boost: тела на орбите нет (удар о поверхность тела)» — e.g. #64 preset mercury: action boost dv=min · op4:action ({'preset_action': 2})
- **(b)** ×2 `ValueError` `visualizations/v04_orbits/viz.py:407 (action)` «Действие boost: тела на орбите нет (падение в центр)» — e.g. #114 preset newton_ellipse: action boost dv=min · op4:action ({'preset_action': 1, 'random': 1})
- **(b)** ×1 `ValueError` `visualizations/v04_orbits/viz.py:423 (action)` «Действие boost: после толчка скорость # c — не меньше c» — e.g. #95 preset plunge: action boost dv=max · op1:action ({'preset_action': 1})

### v06_qcd

- **(f)** ×1 `ValueError` `lfphys/lfphys/core/qcd/running.py:95 (_evolve)` «Мир не создан: RG integration failed» — e.g. #102 random #26 · build ({'random': 1})
- **(h)** ×2 `ValueError` `visualizations/v06_qcd/viz.py:83 (_recompute)` «Мир не создан: масса кварка # ГэВ: модель Корнелла нерелятивистская и описывает тяжёлые кварки (c, b); для m_q < # ГэВ энергия связи сравнима с массой, и её уро» — e.g. #93 random #17 · build ({'random': 2})

### v08_wave_3d

- **(d)** ×29 `slow` `build`  — e.g. #2 source=circle · build 75.4 s ({'single': 14, 'default': 1, 'pair': 7, 'preset': 4, 'all': 1, 'new_world': 1, 'view_extreme': 1})
- **(d)** ×1   «no progress for # s in op#:new_world (killed; combination # s)» — e.g. #44 new_world source=double · op1:new_world ({'new_world': 1})
- **(d)** ×1 `slow` `new_world`  — e.g. #44 new_world source=double · op1:new_world 120.5 s (killed) ({'new_world': 1})
- **(d)** ×1 `slow` `view`  — e.g. #43 slice planes at the box's edge and outside · op3:view 73.5 s ({'view_extreme': 1})
- **(h)** ×6 `ValueError` `visualizations/v08_wave_3d/engine/apparatus.py:223 (choose_window)` «Мир не создан: окно расчёта мало для глубины z_max = # мкм: свет, ушедший под большими углами, возвращается периодическими копиями источника; лучшее, что достиж» — e.g. #2 source=circle · build ({'single': 3, 'pair': 3})
- **(h)** ×2 `ValueError` `visualizations/v08_wave_3d/viz.py:94 (__init__)` «Мир не создан: весь объём на сетке # занял бы ~# ГБ: для # выберите «только срезы»» — e.g. #18 n=512 · build ({'single': 1, 'pair': 1})

### v09_thomas_3d

- **(h)** ×5 `ValueError` `visualizations/v09_thomas_3d/engine/loops.py:58 (check_reach)` «Мир не создан: манёвр подходит к скорости света ближе, чем позволяет точность расчёта (γ > #): уменьшите ρ, χ или число повторов» — e.g. #35 loop=helix, chi=max, turns=max · build ({'pair': 1, 'random': 4})
- **(b)** ×6 `ValueError` `visualizations/v09_thomas_3d/viz.py:296 (view)` «Просмотр: в обычном пространстве срезов нет: поле считается в пространстве скоростей» — e.g. #57 preset lab: slice planes · op1:view ({'preset_view': 6})

### v11_double_slit_2d

- **(h)** ×9 `ValueError` `visualizations/v11_double_slit_2d/viz.py:300 (_cost_guard)` «Мир не создан: опыт слишком тяжёл: ~# мин счёта на CPU (предел # мин; сетка #×# ~# пар шагов): уменьшите экран, пакет или выберите сетку грубее» — e.g. #17 L=max · build ({'single': 3, 'pair': 2, 'random': 4})
- **(h)** ×8 `ValueError` `visualizations/v11_double_slit_2d/viz.py:138 (__init__)` «Мир не создан: поток Ааронова–Бома действует только на заряженные частицы (электрон)» — e.g. #78 random #5 · build ({'random': 8})
- **(h)** ×7 `ValueError` `visualizations/v11_double_slit_2d/engine/apparatus.py:51 (__init__)` «Мир не создан: щели перекрываются: ширина щели должна быть меньше расстояния между ними» — e.g. #7 a=max · build ({'single': 2, 'pair': 1, 'random': 4})
- **(h)** ×6 `ValueError` `visualizations/v11_double_slit_2d/viz.py:141 (__init__)` «Мир не создан: метка пути выключена: выберите в «Метка пути в щели B» спин частицы или детектор» — e.g. #56 all numeric at max · build ({'all': 1, 'random': 5})
- **(h)** ×3 `ValueError` `visualizations/v11_double_slit_2d/viz.py:147 (__init__)` «Мир не создан: края стенки (# λ) уже шага сетки (# λ): сетка их не разрешает — выберите сетку мельче или края шире» — e.g. #14 edge=min · build ({'single': 1, 'all': 1, 'random': 1})
- **(h)** ×1 `ValueError` `visualizations/v11_double_slit_2d/viz.py:143 (__init__)` «Мир не создан: у частицы «Фуллерен ¹²C₆₀» нет спина ½ (внутреннего состояния в движке нет): метка пути спином для неё не определена — выберите электрон или нейт» — e.g. #52 mark=spin, particle=c60 · build ({'pair': 1})
- **(h)** ×1 `ValueError` `visualizations/v11_double_slit_2d/engine/apparatus.py:53 (__init__)` «Мир не создан: экран должен стоять за пластиной» — e.g. #87 random #14 · build ({'random': 1})
- **(b)** ×2 `ValueError` `visualizations/v11_double_slit_2d/viz.py:347 (set_live)` «Изменение не применено: метки пути в этом мире нет: выберите спин или детектор в «Метка пути в щели B» (новый мир)» — e.g. #39 set mark_deg=max (+{'mark': 'spin'}) · op2:set ({'live': 1, 'preset_live': 1})

### v12_arrival_times_2d

- **(h)** ×15 `ValueError` `visualizations/v12_arrival_times_2d/viz.py:130 (__init__)` «Мир не создан: детектор слишком близко: # вероятности уже за его плоскостью в начале (допустимо #); отодвиньте плоскость или сузьте пакет» — e.g. #7 L=min · build ({'single': 2, 'pair': 1, 'all': 1, 'random': 11})
- **(h)** ×13 `ValueError` `visualizations/v11_double_slit_2d/viz.py:300 (_cost_guard)` «Мир не создан: опыт слишком тяжёл: ~# мин счёта на CPU (предел # мин; сетка #×# ~# пар шагов): уменьшите экран, пакет или выберите сетку грубее» — e.g. #18 n_train=max (+{'state': 'train'}) · build ({'single': 2, 'pair': 2, 'all': 1, 'random': 8})
- **(h)** ×4 `ValueError` `visualizations/v11_double_slit_2d/engine/apparatus.py:51 (__init__)` «Мир не создан: щели перекрываются: ширина щели должна быть меньше расстояния между ними» — e.g. #22 a=max (+{'scene': 'slits'}) · build ({'single': 2, 'pair': 1, 'random': 1})
- **(h)** ×3 `ValueError` `visualizations/v11_double_slit_2d/engine/apparatus.py:53 (__init__)` «Мир не создан: экран должен стоять за пластиной» — e.g. #54 scene=slits, w=max, L=min · build ({'pair': 1, 'random': 2})
- **(h)** ×2 `ValueError` `visualizations/v12_arrival_times_2d/engine/apparatus.py:42 (packets)` «Мир не создан: пакеты цепочки перекрываются: расстояние # λ меньше #σz = # λ» — e.g. #19 sep=min (+{'state': 'train'}) · build ({'single': 1, 'pair': 1})
- **(h)** ×1 `ValueError` `visualizations/v11_double_slit_2d/viz.py:147 (__init__)` «Мир не создан: края стенки (# λ) уже шага сетки (# λ): сетка их не разрешает — выберите сетку мельче или края шире» — e.g. #29 edge=min · build ({'single': 1})
- **(h)** ×1 `ValueError` `visualizations/v12_arrival_times_2d/engine/apparatus.py:96 (screen_layer)` «Мир не создан: нет поглотителя для спектра [#; #] λ⁻¹: волна слишком медленная» — e.g. #90 random #15 · build ({'random': 1})

### v13_hydrogen_3d

- **(c)** ×1 `ZeroDivisionError` `visualizations/server/lfviz/orbitals3d.py:345 (_check_current)` «Traceback (most recent call last): File "/out/audit.py", line # in child runner._start_world() File "/lf/visualizations/server/lfviz/sim.py", line # in _start_w» — e.g. #14 l2=min (+{'mode': 'super'}) · header ({'single': 1})
- **(h)** ×32 `ValueError` `visualizations/v13_hydrogen_3d/viz.py:84 (_spec)` «Мир не создан: нужно # ≤ l < n (n = # l = #)» — e.g. #5 n=min · build ({'single': 4, 'pair': 2, 'random': 26})
- **(h)** ×26 `ValueError` `visualizations/v13_hydrogen_3d/viz.py:86 (_spec)` «Мир не создан: нужно |m| ≤ l (l = # m = #)» — e.g. #9 m=min · build ({'single': 4, 'pair': 2, 'all': 1, 'random': 19})
- **(h)** ×7 `ValueError` `visualizations/v13_hydrogen_3d/viz.py:103 (__init__)` «Мир не создан: второе состояние совпадает с первым» — e.g. #4 mode=super · build ({'single': 5, 'pair': 2})
- **(h)** ×1 `ValueError` `visualizations/v13_hydrogen_3d/viz.py:113 (__init__)` «Мир не создан: состояния #p_z и #p, m = # не ортогональны (перекрытие #): одно выражается через другое; выберите другое m или вид орбитали» — e.g. #18 real2=False (+{'mode': 'super'}) · build ({'single': 1})

### v14_quarkonium_3d

- **(h)** ×34 `ValueError` `visualizations/v14_quarkonium_3d/viz.py:74 (_spec)` «Мир не создан: нужно |m| ≤ L (L = # m = #)» — e.g. #7 m=min · build ({'single': 4, 'pair': 3, 'all': 1, 'random': 26})
- **(h)** ×2 `ValueError` `visualizations/v14_quarkonium_3d/viz.py:96 (__init__)` «Мир не создан: второе состояние совпадает с первым» — e.g. #12 l2=min (+{'mode': 'super'}) · build ({'single': 1, 'pair': 1})

### v15_kerr_shadow

- **(c)** ×1 `TypeError` `lfphys/lfphys/theories/alternatives/johannsen_metric.py:262 (circular_orbits)` «Мир не создан: float() argument must be a string or a real number, not 'complex'» — e.g. #92 random #22 · build ({'random': 1})
- **(f)** ×7 `ValueError` `lfphys/lfphys/theories/alternatives/johannsen_metric.py:126 (check_regular)` «Мир не создан: the metric is not regular outside the horizon (Johannsen #a Eqs. # ##): A# reaches # det_eq# reaches # ctc_eq# reaches #» — e.g. #2 a13=min (+{'metric': 'jp'}) · build ({'single': 2, 'pair': 1, 'random': 4})
- **(f)** ×2 `ValueError` `lfphys/lfphys/theories/alternatives/johannsen_metric.py:126 (check_regular)` «Мир не создан: the metric is not regular outside the horizon (Johannsen #a Eqs. # ##): det_eq# reaches #» — e.g. #5 a22=max (+{'metric': 'jp'}) · build ({'single': 1, 'random': 1})
- **(f)** ×1 `ValueError` `lfphys/lfphys/theories/alternatives/johannsen_metric.py:126 (check_regular)` «Мир не создан: the metric is not regular outside the horizon (Johannsen #a Eqs. # ##): A# reaches #» — e.g. #4 a22=min (+{'metric': 'jp'}) · build ({'single': 1})
- **(f)** ×1 `ValueError` `lfphys/lfphys/theories/alternatives/johannsen_metric.py:179 (photon_shell)` «Мир не создан: the photon shell is not a single band between r+ and # M for these parameters» — e.g. #34 metric=jp, a13=max, chi=max · build ({'pair': 1})
- **(f)** ×1 `ValueError` `lfphys/lfphys/theories/alternatives/johannsen_metric.py:126 (check_regular)` «Мир не создан: the metric is not regular outside the horizon (Johannsen #a Eqs. # ##): A# reaches # A# reaches # det_eq# reaches # ctc_eq# reaches #» — e.g. #37 metric=jp, a22=min, a12=min, chi=max · build ({'pair': 1})

### v16_optical_vortices

- **(h)** ×14 `ValueError` `visualizations/v16_optical_vortices/viz.py:180 (_init_fork)` «Мир не создан: порядки голограммы не разойдутся: уменьшите период Λ или увеличьте перетяжку w#» — e.g. #2 gen=fork · build ({'single': 4, 'pair': 1, 'random': 9})
- **(h)** ×5 `ValueError` `visualizations/v16_optical_vortices/engine/apparatus.py:121 (__init__)` «Мир не создан: точная модель не может представить этот источник: # % мощности перетяжки LG (w# = # мкм при λ = # мкм) приходится на q > k — это затухающие волны» — e.g. #7 w0=min · build ({'single': 1, 'pair': 2, 'random': 2})
- **(h)** ×3 `ValueError` `visualizations/v16_optical_vortices/engine/apparatus.py:128 (__init__)` «Мир не создан: мир слишком дорог: таблица поля # радиусов × # узлов квадратуры — ~# млн вычислений функций Бесселя (~# с; предел ~# с) и матрица ~# ГБ (предел #» — e.g. #29 l=max, p=max, w0=max, lam=min · build ({'pair': 1, 'random': 2})
- **(h)** ×2 `ValueError` `visualizations/v16_optical_vortices/viz.py:176 (_init_fork)` «Мир не создан: период голограммы меньше длины волны: первый порядок не распространяется» — e.g. #16 period=min (+{'gen': 'fork'}) · build ({'single': 1, 'pair': 1})
- **(h)** ×1 `ValueError` `visualizations/v16_optical_vortices/engine/apparatus.py:116 (__init__)` «Мир не создан: падающий гауссов пучок с w# = # мкм при λ = # мкм — не пучок: # % его мощности на z = # приходится на затухающие волны (q > k; предел # %): увели» — e.g. #85 random #21 · build ({'random': 1})
- **(b)** ×2 `ValueError` `visualizations/v16_optical_vortices/viz.py:608 (_fork_slice)` «Просмотр: у голограммы срезы считаются только вдоль осей: z = c, y = c или x = c» — e.g. #59 preset fork: slice planes · op1:view ({'preset_view': 2})
- **(b)** ×1 `ValueError` `visualizations/v16_optical_vortices/viz.py:180 (_init_fork)` «Новый мир не создан: порядки голограммы не разойдутся: уменьшите период Λ или увеличьте перетяжку w#» — e.g. #63 new_world gen=fork · op1:new_world ({'new_world': 1})

### v17_mie_scattering

- **(d)** ×17 `slow` `next_event`  — e.g. #4 width=max · op1:next_event 36.0 s ({'single': 4, 'pair': 3, 'preset': 1, 'preset_live': 1, 'random': 8})
- **(d)** ×2   «no progress for # s in op#:next_event (killed; combination # s)» — e.g. #2 radius_um=max · op1:next_event ({'single': 1, 'pair': 1})
- **(h)** ×4 `ValueError` `visualizations/v17_mie_scattering/viz.py:117 (__init__)` «Мир не создан: капли слишком крупные: x > #·#⁴ на # нм (предел проверенной точности ряда)» — e.g. #23 radius_um=max, n_lam=32, width=max · build ({'pair': 1, 'all': 1, 'random': 2})

## Failed checks

Checks that fail in some combination (latest version of each check per combination). On a default or preset world they
are counted as (e) above; elsewhere they are listed only.

### p02_quantum

- `balance_o1`  ×5: #51 [dim=2d] add packet x=min: «Частица (волновой пакет) 1»: норма + поглощённое (= 1) = nan (эталон 1.0)
- `balance_o2`  ×3: #33 preset trap: edit each object at extremes: «Электрон»: норма + поглощённое (= 1) = nan (эталон 1.0)
- `energy_o1`  ×1: #70 [dim=2d] packet: edit every param to min/max while running: «Частица (волновой пакет) 1»: энергия ⟨H⟩ (замкнутая система) = nan (эталон nan)
- `energy_o2`  ×2: #33 preset trap: edit each object at extremes: «Электрон»: энергия ⟨H⟩ (замкнутая система) = nan (эталон nan)

### p04_fluids

- `compressibility`  ×2: #126 [default] inlet: edit every param to min/max while running: Перепад плотности (мера ошибки сжимаемости) = 0.15314043978341374 (эталон None)

### v01_light_travel

- `flat_p2_earth`  ×2: #215 preset andromeda: action flash obj=walk_to: Невязка решения: время полёта до «Земля» и |Δx|/c = 1867.9589233398438 (эталон 1867.9589331096515)
- `flat_p2_stay`  ×2: #215 preset andromeda: action flash obj=walk_to: Невязка решения: время полёта до «Стоит» и |Δx|/c = 1867.9589233398438 (эталон 1867.9589331096515)
- `flat_p2_walk_from`  ×3: #116 preset andromeda: action #0 default: Невязка решения: время полёта до «Идёт от Андромеды» и |Δx|/c = 1867.9589233398438 (эталон 1867.9589418328278)
- `flat_p2_walk_to`  ×3: #116 preset andromeda: action #0 default: Невязка решения: время полёта до «Идёт к Андромеде» и |Δx|/c = 1867.9589233398438 (эталон 1867.9589418328278)
- `flat_p3_earth`  ×2: #215 preset andromeda: action flash obj=walk_to: Невязка решения: время полёта до «Земля» и |Δx|/c = 368660.375 (эталон 368660.3733180052)
- `flat_p3_stay`  ×2: #215 preset andromeda: action flash obj=walk_to: Невязка решения: время полёта до «Стоит» и |Δx|/c = 368660.375 (эталон 368660.3733180052)
- `pass_p1_obs3_1`  ×2: #146 preset measure_c_lab: action flash obj=obs1: Наблюдатель 3: односторонняя скорость (внешний свет) = 7799110015.60631 (эталон 599584916.0)

### v02_double_slit

- `coh0`  ×1: #302 el1=polarizer, el2=polarizer, el1_angle=0.0, el2_angle=90.0: Степень когерентности щелей |γ₁₂| ожидаемой картины запуска = 1.1078969781102477 (эталон 6.123233995736766e-17)
- `coh1`  ×6: #303 set el1=polarizer, el2=polarizer, el1_angle=0.0, el2_angle=90.0: Степень когерентности щелей |γ₁₂| ожидаемой картины запуска = 1.1078969781102477 (эталон 6.123233995736766e-17)
- `coh3`  ×2: #372 preset c60_grw: set mass_u over [1e-06, 1000000000.0]: Степень когерентности щелей |γ₁₂| ожидаемой картины запуска = 0.6020726140002635 (эталон 0.0)
- `coh5`  ×1: #437 preset photon_eraser_minus: set el1 over ['none', 'polarizer', 'hwp', 'qwp', 'ro: Степень когерентности щелей |γ₁₂| ожидаемой картины запуска = 0.9582459417429715 (эталон 1.0000000000000002)
- `coh7`  ×2: #378 preset photon_pol_marks: set pol_state over ['H', 'V', 'D', 'A', 'R', 'L', 'cust: Степень когерентности щелей |γ₁₂| ожидаемой картины запуска = 1.1078969781102477 (эталон 6.123233995736766e-17)
- `grid`  ×37: #17 lam_nm=min: Разрешение экрана: точек на самую частую полосу = 0.0022754804224114416 (эталон None)
- `nosig0`  ×1: #469 random #16: Без сигнала: распределение на экране с чтением детектора = без чтения = 9.287091391103692e-10 (эталон 0.0)
- `nosig1`  ×1: #469 random #16: Без сигнала: распределение на экране с чтением детектора = без чтения = 7.309417182540765e-10 (эталон 0.0)
- `per0`  ×1: #21 ekin_ev=min (+{'energy_by': 'ekin'}): Период полос (по рассчитанной картине) = 1.250621044019005e+16 (эталон 1.2398419843320028e+16)
- `per2`  ×3: #22 set ekin_ev=min (+{'energy_by': 'ekin'}): Период полос (по рассчитанной картине) = 1.250621044019005e+16 (эталон 1.2398419843320028e+16)
- `rs0`  ×25: #19 lam_nm=max: Параксиальное приближение на экране: отличие от точного интеграла Рэле = 29.035351636235948 (эталон 0.0)
- `rs0` **on a default or preset world** ×1: #350 preset vector_narrow: Параксиальное приближение на экране: отличие от точного интеграла Рэле = 0.41200198072849686 (эталон 0.0)
- `rs1`  ×30: #20 set lam_nm=max: Параксиальное приближение на экране: отличие от точного интеграла Рэле = 29.035351636235948 (эталон 0.0)
- `rs2`  ×15: #30 set freq_thz=min (+{'energy_by': 'freq'}): Параксиальное приближение на экране: отличие от точного интеграла Рэле = 29.036204009391515 (эталон 0.0)
- `rs3`  ×7: #372 preset c60_grw: set mass_u over [1e-06, 1000000000.0]: Параксиальное приближение на экране: отличие от точного интеграла Рэле = 1.1208489390979952 (эталон 0.0)
- `rs4`  ×2: #366 preset electron_weak: set speed_ms over [1e-06, 299000000.0]: Параксиальное приближение на экране: отличие от точного интеграла Рэле = 8.611066511388103 (эталон 0.0)
- `sork0`  ×7: #355 preset triple_mod: action #0 default: Параметр Соркина ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ = 0.1327074568904497 (эталон 0.0)
- `sork0` **on a default or preset world** ×1: #354 preset triple_mod: Параметр Соркина ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ = 0.1327074568904497 (эталон 0.0)
- `sork1`  ×6: #355 preset triple_mod: action #0 default: Параметр Соркина ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ = 0.1327074568904497 (эталон 0.0)
- `sork2`  ×4: #355 preset triple_mod: action #0 default: Параметр Соркина ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ = 0.1327074568904497 (эталон 0.0)
- `sork3`  ×4: #375 preset triple_mod: set charge_e over [-100, 100]: Параметр Соркина ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ = 0.1327074568904497 (эталон 0.0)
- `sork4`  ×2: #375 preset triple_mod: set charge_e over [-100, 100]: Параметр Соркина ∫|I_ABC − I_AB − I_BC − I_AC + I_A + I_B + I_C| / ∫I_ = 0.1327074568904497 (эталон 0.0)

### v03_quantum_1d

- `T0`  ×3: #11 scenario=step: Прохождение волнового пакета (вычислено по времени) = 2.3590500899798224e-06 (эталон 2.5579433627711566e-06)
- `abs0`  ×3: #11 scenario=step: Волна поглощена детекторами (остаток не меняет результат) = 0.9999999675917046 (эталон 1.0)

### v06_qcd

- `conv0`  ×14: #69 preset strong: set mu over [1.0, 10000.0]: Сходимость ряда: α_s(2 ГэВ) в 3 и 4 петли = 0.9962323629010517 (эталон 0.8546806865942081)
- `conv0` **on a default or preset world** ×1: #67 preset strong: Сходимость ряда: α_s(2 ГэВ) в 3 и 4 петли = 0.9962323629010517 (эталон 0.8546806865942081)
- `conv1`  ×10: #68 preset strong: set loops over [1, 4]: Сходимость ряда: α_s(2 ГэВ) в 3 и 4 петли = 0.9962323629010517 (эталон 0.8546806865942081)
- `conv2`  ×8: #68 preset strong: set loops over [1, 4]: Сходимость ряда: α_s(2 ГэВ) в 3 и 4 петли = 0.9962323629010517 (эталон 0.8546806865942081)
- `conv3`  ×2: #72 preset strong: set kappa over [0.0, 1.5]: Сходимость ряда: α_s(2 ГэВ) в 3 и 4 петли = 0.9962323629010517 (эталон 0.8546806865942081)
- `lev0_11`  ×57: #17 kappa=min: Модель: расщепление 1P − 1S = 268.76808779161274 (эталон 456.60666666666657)
- `lev0_20`  ×54: #17 kappa=min: Модель: расщепление 2S − 1S = 459.66181454756685 (эталон 605.2977500000002)
- `lev0_30`  ×13: #33 system=bottom, m_q=max, kappa=max: Модель: расщепление 3S − 1S = 5255.908742022669 (эталон 910.1250000000018)
- `lev1_11`  ×65: #18 set kappa=min: Модель: расщепление 1P − 1S = 268.76808779161274 (эталон 456.60666666666657)
- `lev1_20`  ×62: #18 set kappa=min: Модель: расщепление 2S − 1S = 459.66181454756685 (эталон 605.2977500000002)
- `lev1_30`  ×21: #34 set system=bottom, m_q=max, kappa=max: Модель: расщепление 3S − 1S = 5255.908742022669 (эталон 910.1250000000018)
- `lev2_11`  ×27: #48 preset standard: set kappa over [0.0, 1.5]: Модель: расщепление 1P − 1S = 1082.261427955517 (эталон 456.60666666666657)
- `lev2_20`  ×26: #48 preset standard: set kappa over [0.0, 1.5]: Модель: расщепление 2S − 1S = 1190.9580989275664 (эталон 605.2977500000002)
- `lev2_30`  ×10: #57 preset bottom: set a_conf over [1.0, 5.0]: Модель: расщепление 3S − 1S = 517.3950621181316 (эталон 910.1250000000018)

### v07_bell_test

- `st_rev`  ×2: #39 switch=random, tau_ns=min, L_m=max: Порядок «выбор у A → регистрация у B» обращается в системе, летящей от = 1.4989622840104423e-09 (эталон 1.4989623014116663e-09)

### v11_double_slit_2d

- `absorbers`  ×2: #16 L=min: Детекторы: отражение и утечка поглощающих слоёв = 0.08804790462679232 (эталон None)

### v12_arrival_times_2d

- `soft_grid`  ×2: #39 W0=max: Мягкий детектор разрешён сеткой: |q|/k_max = 0.8245432390552156 (эталон None)

### v14_quarkonium_3d

- `continuity`  ×3: #88 random #34: Уравнение непрерывности ∂ρ/∂t + ∇·j = 0 в узлах стрелок = 6.988318664034949e-05 (эталон 0.0)

### v16_optical_vortices

- `am_L`  ×2: #66 random #2: Орбитальный момент L_z на фотон на единицу длины (измерен по полю на п = 1.9886234457984406 (эталон 2)
- `beat`  ×1: #31 l=0, p=0, pol=lin: Биения на детекторе: глубина модуляции (их нет) = 0.0017924753308974377 (эталон 0.0)
- `plane_1`  ×4: #66 random #2: Срез 1 (z = 78.317): |E|² в 3 точках против прямого расчёта = 0.003140887629599706 (эталон 0.0)
- `shift`  ×1: #31 l=0, p=0, pol=lin: Сдвиг частоты света на оси (по комплексной амплитуде) = 5.432302890659361e-05 (эталон 0.0)
- `table`  ×5: #66 random #2: Таблица поля против прямого расчёта (24 точки + 18 на ярком кольце) = 0.0005803924500551646 (эталон 0.0)

### v17_mie_scattering

- `debye`  ×1: #28 index=custom, n_re=1.0, n_im=0.0, n_medium=1.0: Ряд Дебая: сумма всех p против коэффициентов Ми (второй путь счёта) = 1163.57191607505 (эталон 0.0)
- `mueller`  ×1: #28 index=custom, n_re=1.0, n_im=0.0, n_medium=1.0: Матрица Мюллера: S11² = S12² + S33² + S34² (тождество) = nan (эталон 0.0)

## Files in this folder

- `REVIEW.md` — this file.
- `scripts/audit.py` — the driver (combinations, forked runs, budgets); `scripts/analyze.py` — the classification;
  `scripts/report.py` — the tables of this review; `scripts/srvcheck.py` — the server confirmations; `scripts/typed.py`
  — the framework's answers to typed out-of-range values; `scripts/batch*.sh` — the container runs.
- `results/<world>.jsonl` — one line per combination: parameters, operations, events with the exception type and line,
  errors and notices, failed checks, non-finite values, timings. `results/combinations.jsonl` — the classified list.
- `repro/` — the targeted reproductions: `r_v03_timing.py/.out` (P13, P19), `r_v06_rg.py/.out` (P5), `r_v01_flash.py/.out`
  (P9, P14).
- `server/srv_cases1.json`, `server/srv_out1.json` — runs on the private server; `pw/` — the Playwright scripts, cases,
  outputs (`out*.json`, `typed_out.json`, `catalogue_out.json`) and `pw/shots/*.png`.
- `typed.out` — the schema's texts for typed out-of-range values and emptied fields, every world.
- `schemas.json` (every world's schema and presets) and `probe.json` (default worlds: build time, actions, slice planes,
  speed), the inputs of the generator; `scripts/assemble.py` fills the generated tables into this file.
- `server/srv_cases2.json`, `server/srv_out2.json` (p04 water, v16 fork, v03 step on the server) and
  `server/srv_cases3.json`, `server/srv_out3.json` (p03 wall, piston, one-atom gas).

How to rerun one world (from `engine/`, CPU only, with the limits used here):

```
docker run --rm --name lf-uxc-x --memory=14g --memory-swap=14g -v $PWD:/lf:ro -v <this folder>:/out \
  -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -e OMP_NUM_THREADS=2 -w /lf/visualizations light-funnel-viz \
  python3 /out/scripts/audit.py v02_double_slit --out /out/results-rerun
python3 scripts/report.py results-rerun /tmp/frag   # tables
```
