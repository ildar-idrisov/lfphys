# Review: the player and the playgrounds as the owner uses them (UX-ui)

**Status: awaiting processing.** Reviewer: an internal subagent (Claude), 2026-11-04. The reviewer does not process
this review (`../README.md`).

**Scope.** The owner's note of 2026-11-04 (verbatim, the part this review covers):

> - орбиты отрисованы ломаными,
> - в плейграунде, не выставляются часть объектов,
> - при прокрутке происходит какое-то обновление и экран сдвигается в первоначальное положение,
> - плейграунд должен быть больше похож на плейграунд, где я могу ставить эксперименты в рамках одного мира, а не
>   перезапускать его постоянно и должно быть больше интерактива, когда я что=то добавляю, меняю условия и вижу
>   результат в реальном времени, должно быть больше возможностей по изменения нужных и важных параметров и добавлению
>   новых объектов для проверки взаимодействия … должно быть все понятно и удобно и подготовлено для визуализации и
>   исследований

Checked: the interface of the player (`visualizations/player/js/`), the placement of objects in the playgrounds
p01–p04 (`server/lfviz/playground.py`, `pNN_*/viz.py`, `pNN_*/web/view.js`), the scroll and view behaviour, how
curves are drawn, the usability of all 21 worlds at 1600×1000 and 1280×800, and the facts that decide how far the
playground can become a laboratory. Not checked: the physics (other reviews), the 3-D rendering and camera as such
(sibling review `2026-11-04_internal_UX-3d`), launch errors and parameter combinations of the demonstrations (sibling
review `2026-11-04_internal_UX-params`). Nothing in the engine was changed.

**Environment.** A private server (`lf-uxb-srv`, port 8562, `LFPHYS_NO_GPU=1`, `OMP_NUM_THREADS=2`, `--max-workers 2`,
code as on disk 2026-11-04, code hash `cc2c5dd45cd5`), Chromium of Playwright 1.58.2 with SwiftShader, the harness
`visualizations/tests/harness.py` in the `light-funnel-viz` image. **CPU only**; the host carried the sibling audits
at the same time (load average 50–60 on 16 cores), so every wall-clock number here is an upper bound for this host
and is not the GPU server's figure. Counts, sampling densities and code paths do not depend on the load.

**Evidence.** `scripts/` (every script named below; the `.mjs` ones run in the Playwright image with `/pw` = their
folder, the `.py` ones in the `light-funnel-viz` image with `/aui` = a folder holding `py/` and `out/`), `out/` (raw
outputs, JSON lines), `shots/` (screenshots, JPEG, each < 300 KB). Reproduction at the end.

## Summary

| | count |
|---|---|
| error | 8 |
| should-fix | 12 |
| nit | 4 |

Ranked by how much each hurts the owner's use:

| id | severity | one line |
|---|---|---|
| U1 | error | Things jump back to where they started — the owner's «экран сдвигается в первоначальное положение»: every `box` message refits the 3-D camera and a playground re-sends its `box` at every record segment (60 s); v04 refits after any step back in the history; the playground's object list jumps to its top when an object is selected or the scene changes |
| U2 | error | p01's orbits are drawn from one point per frame: at the default speed Mercury is a pentagon (4.8 points per orbit), at ×10 the Earth's orbit is a line (2 points); the solvers' own dense points are thrown away |
| U3 | error | p02: in the double-slit preset every palette click freezes the world for 18 s to over 30 s with no sign of it, objects appear one click late, 3 of 12 are refused; an inspector edit takes ~9 s even on a 128² grid |
| U4 | error | The palette places only with default values at a fixed spot: a second star or hole is refused, a star merges into the Sun unseen, a black hole swallows the Sun, a particle lands inside the slit wall and is refused |
| U5 | error | Palette and inspector actions that block the world for more than 30–40 s with no way out (p03 molecules: shape, copy, count; large gas in 3-D) |
| U6 | error | Palette actions that break the world: p03 hard disks + «＋ Атом» → `ZeroDivisionError`, a hot gas → `FloatingPointError`; the player shows Python's traceback and the world stops |
| U7 | error | Objects the palette offers that the world can never accept with their defaults: p04 «Объёмная сила» in every world, p03 «Стенка» and «Поршень» in the default (periodic) box, p03 «Кристалл» in any non-empty scene; the buttons stay enabled |
| U8 | error | Values far outside the world are accepted without a word: a p02 packet at x = 10⁶ nm becomes NaN (probability «—»), potentials, fields and detectors far outside the window, a p04 probe 10 km from a 0.41 m channel |
| U9 | should-fix | No feedback while a scene command is computed: the status says «запись идёт · вживую», the clicked button does not change, repeated clicks queue |
| U10 | should-fix | The inspector is rebuilt after every change it sends: the focus is lost (Tab from «Масса» lands on its slider, then on nothing), so several fields cannot be edited in a row |
| U11 | should-fix | No direct manipulation: objects cannot be picked, placed or dragged in the scene; parameters cannot be set before an object is placed |
| U12 | should-fix | Laws the engine can already change at the current moment are world parameters (p04 viscosity and dye, p03 interaction model, cut-off and time step, p01 collisions); in v13/v14 choosing a state restarts the world |
| U13 | should-fix | Refusals speak the engine's language: English messages (`random placement jammed…`, `axis y is periodic`, `0 < x_min <= X <= L, mass > 0, finite p_ext and V`), numerical jargon, and a p02 refusal that cites a «яма −3 эВ» that is not in the scene |
| U14 | should-fix | «События» is rebuilt on every drawn frame, so a click on an event while the world records does nothing (0 of 8 human clicks jumped; paused: 8 of 8) |
| U15 | should-fix | The 2-D sections (p02, p04) show the computed field in a side window; the 3-D view of a flat slab takes the main area (p04 at 1280×800: the flow is a 330×140 px picture) |
| U16 | should-fix | The checks panel is a wall of reviewer notes (6–15 lines of numerical detail under every check); at 1280 px its ✓/✗ column is cut off and the panel scrolls sideways |
| U17 | should-fix | «Прежние группы проверок», once opened, closes itself within a second (re-created closed whenever a check arrives) |
| U18 | should-fix | p01's Newtonian black hole is drawn near-black (0.1, 0.1, 0.12) on the 3-D view's near-black background: in «Чёрная дыра 1000 M☉ и звёзды» the hole the stars orbit cannot be seen |
| U19 | should-fix | Units missing on primary parameters (v11/v12 lengths «в λ» only in another parameter's help; «Длина волны де Бройля λ» without a unit; v12 W₀, κ, V₀) |
| U20 | should-fix | At 1280×800 the demonstrations are cramped: the main drawing gets 16–23 % of the window, the top bar wraps to two or three lines, and v07's 2×2 panels print their labels over each other |
| U21 | nit | The 3-D toolbar offers slice tools («✥ Двигать», «⟳ Наклонять», the scale, the hint about slices) in worlds without slices (p01–p04, v10, v11, v12, v15) |
| U22 | nit | A palette button disabled at its limit does not say why; buttons stay enabled where the world refuses the object |
| U23 | nit | Playground's left column starts with an empty «Действия — Нет действий»; «Новый мир» is open by default |
| U24 | nit | 9 px labels under the speed slider; the bottom bar wraps to two lines even at 1600 px in p02 and p04 |

Checked and found working: the scroll position of the page and of every scroll container (catalogue, side panels,
events, scene list, slice windows) while data arrive — kept in all six worlds tried at both sizes (details under
U1); v04's orbit sampling (240 points per turn, 1.5°); v09's paths (0.13–0.2° between segments; the 90° corners of the
Thomas loop are the loop's own corners).

---

## U1 (error). The view and the object list jump back to where they started

**Worlds.** Every 3-D world that sends `box` — p01 (Newton, Kerr, PN: `p01_gravity/viz.py:510-513`, `:891-894`,
`:1069`), v09 «обычное пространство» (`v09_thomas_3d/viz.py:453`), v10 (`v10_fast_observer/viz.py:319`) — and every
playground, whose record re-sends the latest `box` at each segment start; v04 (2-D) after any step back in the
history.

**What the owner sees.** He turns or zooms the scene with the mouse (the wheel: «при прокрутке»), and some seconds
later the camera snaps back to the initial iso view at the initial distance.

**Overlap.** The sibling review `2026-11-04_internal_UX-3d` (A7) reports the camera reset when the box *grows*. This
finding adds what makes it periodic in the playgrounds — the record's segment start re-sends an unchanged `box` every
60 s — and the two other jumps the owner can meet: v04's 2-D refit and the playground's object list.

**Evidence** (`scripts/camera.mjs`, `out/camera.jsonl`, `shots/camera_p01_inner_zoomed.jpg`,
`shots/camera_p01_inner_reset.jpg`, `shots/camera_v04_zoomed.jpg`, `shots/camera_v04_after_scrub.jpg`). The zoom is
measured as the screen distance of two physics points (`scene3d.screenOf`), sampled every second while the world
records; `setBox` calls counted.

| world | zoom before → after the wheel | reset | `setBox` calls at the reset |
|---|---|---|---|
| p01 «Солнце, Меркурий … Юпитер» | 28.2 → 59.9 px/а.е. | back to 28.2 at +28 s (the next periodic checkpoint) | 1 |
| p01 «Чёрная дыра 1000 M☉ и звёзды» | 28.2 → 59.9 | back to 28.2 at +55 s | 1 |
| v09 «обычное пространство» | 49.1 → (wheel) | the zoom was overwritten while the box grew: 40.7 right after the wheel | 2 |
| v04 (2-D) | wheel ×5 in | refitted by a step back along the timeline and back to the end | `Plane.fit` 1 |

Scrolling itself is not the cause: the page and every scroll container keep their position (`scripts/scroll.mjs`,
`out/scroll.log`: `#left`, `#right`, `.events`, `.pg-list`, `.s3d-windows` in v04, v02, v08, p01, p03, p04 at
1600×1000 and 1280×800, and the catalogue in both modes: 0 resets in 8 s of live data each; every programmatic
`scrollTop` write logged — the only one is `renderEvents` pinning «События» to its bottom when the owner is already
there, `player.js:784`).

**Cause.**
1. `scene3d.js:582-588` `setBox` rebuilds the frame and then calls `view(S.lastView || "iso")`, which puts the camera
   back to the preset view at the distance that fits the box (`scene3d.js:867-890`). Any `box` message therefore
   discards the owner's orbit, pan and zoom, even when the box did not change.
2. `playground.py:114` lists `box` in `SET_LIKE`; `segment_start` (`playground.py:289-301`) re-emits the latest one at
   every record segment, i.e. at each periodic checkpoint, 60 s of wall time after the previous one while the world
   computes (`playground.py:110`, `sim.py:548-550`, the clock reset at `sim.py:466`).
   p01 always has one: its header box is the initial ±1.5 а.е. (`viz.py:288`, `:603-606`), so the first frame of any
   larger scene grows it (`viz.py:510-513`) and from then on it is re-sent every minute.
3. Going back in the history re-applies the header's box (`env3d.js:194`) and `setScene` refits when the box differs
   from the one it fitted (`scene3d.js:577`).
4. v04 resets `fittedSeg = -1` in `reset()` and `restore()` (`v04_orbits/web/view.js:425`, `:437`), so the next draw
   refits the plane to the segment (`view.js:146`); a key-frame restore is any step back along the timeline.

**The playground's object list** (`scripts/inspector.mjs`, `out/inspector.json`): p01 «Солнце … Юпитер» with 20
test bodies added, recording; the list «Объекты сцены» scrolled down by the wheel to `scrollTop` 393, the last body
clicked: the list is rebuilt and comes back at `scrollTop` 0 — the selected body is out of sight. Cause:
`playground.js:72` builds a new `.pg-list` (a new scroll container, `scrollTop` 0) in `drawObjects`, called on every
selection (`select`, `:84-88`) and on every scene message whose revision or length changed (`drawAll`, `:207-208`) —
i.e. after every add, edit, copy, removal and merge. The inspector is rebuilt at the same moments (see U10).

**Suggested fix.** Separate "the region changed" from "frame the camera": `setBox` rebuilds the frame and the far
plane only; the camera is refitted only when the owner has not moved it since the last fit (a flag set by
OrbitControls' `change` event) or on «F» / the view buttons; a `box` equal to the current one is ignored. The
playground's segment start may still repeat the `box` (the segment must be drawable alone) — with the rule above it no
longer moves the camera. In v04 keep `fittedSeg` (and the plane's centre and scale) through `reset`/`restore` within
the same world, as v01 already does («v01 set up its frame, camera and zoom again on every rebuild (now only for a
new world)», STATUS V32). A browser test: zoom, record past a segment start and a box growth, step back and forth —
the camera must not move. The object list: update the rows in place (or keep the container and its `scrollTop`), and
scroll the selected row into view only when the selection came from the scene, not from the list.


## U2 (error). p01's orbits and trails are polylines with one point per frame

**Worlds.** p01 in all three laws; the owner's «орбиты отрисованы ломаными». The sibling review `2026-11-04_internal_UX-3d`
(A13) finds the same cause from the chords on the screen; the numbers below measure it in every p01 mode and point to
the dense data the solvers already have.

**Evidence** (`scripts/polylines.py`, `out/polylines.txt`: 200–400 frames through the runner at the world's default
speed, 20 frames per second as `Runner.run`; the turning angle between consecutive segments, 360° / angle = points
per orbit; screenshots from above, `scripts/polyshot.mjs`: `shots/curve_p01_inner_default.jpg` — Mercury a scribble,
Venus and the Earth polygons with crossing chords; `shots/curve_p01_inner_tenth.jpg` — the same preset at a tenth of
the speed, smooth circles; `shots/curve_p01_hole_default.jpg` — the stars around the 1000 M☉ hole as zigzag stars).

| world, speed | body | points per orbit | angle between segments |
|---|---|---|---|
| p01 «Солнце … Юпитер», 1 year/s (default) | Меркурий | 4.8 | 74.8° |
| | Венера | 12.3 | 29.3° |
| | Земля | 20.0 | 18.0° |
| | Марс | 37.6 | 9.6° |
| same, 10 years/s | Земля | 2.0 | 180° (a line back and forth) |
| | Венера | 5.4 | 67° |
| same, 0.1 year/s | Меркурий | 48 | 7.5° |
| p01 «Чёрная дыра 1000 M☉ и звёзды», default | Звезда 1 | 2.3 | 157° |
| | Звезда 2 | 4.1 | 87° |
| p01 Kerr (default 10 G M/c³ per s) | ISCO-close orbit | 77 | 4.7° (max 4.7°) |
| | light ray near the photon orbit | — | max 8.6° |
| p01 PN binary, start (r = 20 G m/c²) | each body | 57 | 6.3° (falls as the binary shrinks) |
| v04, all presets (control) | — | 240 | 1.5° |
| v09 (control) | path | — | 0.13–0.2° (the Thomas loop's 90° corners are the loop's) |

**Cause.** The trail gets one point per `advance` call: `NewtonMode.advance` (`p01_gravity/viz.py:491-495`),
`KerrMode.advance` (`:840-845`), `PNMode.advance` → `_trail_append` (`:1107-1154`); p01's `max_step()` is `None`
(`:488`, `:837`, `:1104`), so the runner calls `advance` once per frame with a step of `speed × wall dt`
(`sim.py:541`, ≈ speed / 20). Points per orbit = 20 × period / speed: the faster the owner runs the world, the
coarser the orbit. The view joins the points by straight segments (`p01_gravity/web/view.js:43-56` → `setLines`).
The solvers have the dense data and drop it: the Hermite N-body commits its own steps inside `advance`
(`lfphys/core/gravity/nbody.py:470-490`, with a continuous output `_dense`, `:832`); the PN integration of each
`advance` already returns 65 dense samples (`viz.py:1116`, `n_out=65`) of which the trail keeps the last.
Also: the trail is sent every third frame (`TRAIL_EVERY = 3`, `viz.py:36`, `:56-58`) and the points pending at a
pause are not sent, so a paused body sits ahead of its trail's end (Jupiter in `curve_p01_inner_default.jpg`).

**Suggested fix** (in order of fidelity).
1. Send the exact orbit: sample inside the solver by geometry, not by frame — keep a point whenever the direction of
   motion has turned by more than ~2° (or the chord's sagitta exceeds a fraction of the scene's size) since the last
   kept point: N-body — at committed steps or from `_dense` within a step; PN — from the 65 samples already computed
   (`res["x"]`); Kerr — from the geodesic integrator's dense output. Cap the points per frame (e.g. 400 per body) so
   the record stays bounded at high speed; above the cap thin uniformly in angle, not in time.
2. As a stop-gap in the view: a cubic Hermite curve between consecutive frame points from their positions and
   velocities (the frame has both, `viz.py:501-525`) — "interpolation along computed data" (`RULES.md` §4.2) but not
   reliable when the chord turns by more than ~60° (Mercury at the default speed) and wrong at 180° (the Earth at ×10).
   Mark it as interpolated.
3. Whatever the fix, a test: points per orbit ≥ 120 and turning angle ≤ 3° for every preset at its default speed and
   at ×10.


## U3 (error). p02: every scene change freezes the world, silently

**Worlds.** p02 (both 2-D and 3-D); the owner's «не выставляются часть объектов» and «вижу результат в реальном
времени».

**Evidence.**
* In the browser (`scripts/palette.mjs`, `out/palette.log`, `shots/palette_p02_slit_toast.jpg`): the preset
  «Двухщелевой опыт», recording; each palette button clicked once, the object list watched for 30 s + 6 s:

  | button | what the owner sees |
  |---|---|
  | ＋ Частица | refused at once (U4: the default packet lands in the wall) |
  | ＋ Барьер или яма | nothing for 30 s |
  | ＋ Шар | the *box* of the previous click appears |
  | ＋ Стенка со щелями, ＋ Ступенька | each shows the previous click's object after ≥ 30 s |
  | ＋ Гармоническая ловушка | refused (grid) after ≥ 30 s |
  | ＋ Магнитное поле | refused («поле нельзя менять, пока заряженная частица … в окне») |
  | ＋ Трубка потока, ＋ Среда, ＋ Детектор, ＋ Метка пути, ＋ Плоскость потока | ≥ 18–30 s each, appearing one click late |

  The status line said «запись идёт · вживую» the whole time.
* With the harness (`scripts/place.py`, `out/place.jsonl`), no browser: adding to the same preset with defaults — box
  18.2 s, ball 29.5 s; wall with slits, step, flux tube, detector, marker, environment, flux plane > 30 s (the
  script's limit); in an empty 128² world every inspector edit of a packet 8.8–20 s, a copy 28 s, a removal 19 s; in
  the 3-D preset «электрон рассеивается на шаре» 13–15 s per object. Again in the double-slit preset
  (`scripts/p02_time.py`, `out/p02_time.txt`, load average 49): the packet's x changed 33.1 s, a box added in a corner
  far from everything 33.0 s, a new wavelength 31.9 s.
* Profile (`scripts/p02_prof.py`, `out/p02_prof.txt`): a change of the packet's x in the double-slit preset — 32–37 s
  under cProfile (two runs), all in
  `_tune_dt` → `_auto_W` (`p02_quantum/viz.py:565`, `:424`) → `transfer.transmission_profile` 154 calls →
  `transfer._step` 440 154 calls in pure Python (`lfphys/core/quantum/transfer.py:33`, `:89`); a change of a
  detector's edge 58 s (220 profiles).

**Cause.** After *every* scene change p02 re-tunes the open edges' absorber and the automatic detectors over a
log-spaced set of strengths (`viz.py:424-440`, `:565-580`), each evaluation a stationary transfer-matrix sweep over
4000 slices for 24 angles plus extra wavenumbers (`ANGLES = 24`, `viz.py:48`, `:417`), all in a Python loop — whatever
the change was (a colour-free label, a box far from the edges). The runner computes the command synchronously
(`sim.py:325-334`), so no frame is sent meanwhile; the player gets no "pending" state for a scene command (U9).

**Suggested fix.** (a) Vectorise `transfer._step` over slices and angles (NumPy; it is a product of 2×2 matrices);
(b) cache the absorber's reflection table by (layer width, strength, mass, k) and re-tune only when what it depends on
changed (the particles' energies, masses or the detectors' boxes) — a box in the middle of the window changes neither;
(c) do the re-tuning after the change is applied and shown, in the next frames, or in a worker thread, with the
check marked "being tuned"; (d) a pending indicator (U9). Target: a palette click visible within 0.5 s.


## U4 (error). The palette places only with defaults, at a fixed spot

**Worlds.** All playgrounds; most visible in p01 and p02.

**Evidence** (`scripts/place.py`, `out/place.jsonl`; `scripts/p01_merge.py`; `scripts/palette.mjs`, `out/palette.log`).

| section, scene | click | result the owner sees |
|---|---|---|
| p01 empty, a star placed | ＋ Звезда again | refused: «тело оказалось бы точно в той же точке, что и другое …» |
| p01 empty, a planet placed | ＋ Планета again | refused: «круговая орбита: тело на оси z, проходящей через центр масс остальных тел …» — the owner asked for no orbit |
| p01 «Солнце … Юпитер» | ＋ Звезда | appears and vanishes within one frame: «"Солнце" и "Звезда 2" столкнулись и слились» — only a line in «События», no toast (browser: the list never shows it) |
| p01 «Солнце … Юпитер» | ＋ Чёрная дыра | the hole lands on the Sun and swallows it: the Sun disappears from the scene |
| p02 «Двухщелевой опыт» | ＋ Частица | refused (grid band; the default packet sits at (0, 0), inside the 3 eV wall) |
| p03, an atom already at the default spot | ＋ Атом again, ⧉ copy of an atom | refused: `refused: two interacting particles at the same point` / `overlap: … 1.4e+35 exceeds max_insert_energy = 50` |
| p03 «Газ аргона…», «Газ под поршнем» | ＋ Кристалл | refused: `overlap: … 7.5e+27 exceeds max_insert_energy = 50` (the default crystal fills the whole box) |
| p04 «Обтекание цилиндра» | ＋ Вход потока / Выход / Периодичность | refused: «сторона «слева» уже занята …» (the side cannot be chosen before placing) |
| any | ⧉ copy of a massive body / an atom / a crystal | refused (a copy lands on its original) |

In the browser (`out/palette.log`): «Газ под поршнем» — 4 of the 9 enabled buttons refused with defaults (gas
«random placement jammed: 152 of 200…», crystal «overlap…», atom «a particle outside the walls on axis y», molecules
«не удалось разместить 20 молекул… размещено 6»); «Обтекание цилиндра» — 4 of 10 refused (inlet, outlet,
periodicity: the side is taken; body force, U7); «Двухщелевой опыт» — 3 of 12 refused, the rest late (U3).

**Cause.** The palette sends `{op: "add", type, values: {}}` (`player/js/playground.js:63`): the object is created with
its schema's defaults — p01 star and hole at (0, 0, 0) (`p01_gravity/viz.py:235-237`, `:256-263`), planet at x = 1,
test body at x = 2; p02 every object at the window's centre; p03 the crystal over the whole box; p04 inlets on the
left. A copy is placed on its original "in the current moment" by design (`playground.py:199-203`). Merging
(`collisions = merge`, the default) then removes a body without a toast; only `notice` and `error` toast
(`player.js:573-589`).

**Suggested fix.** (1) «Place» mode: a click on a palette button opens the type's parameters (prefilled, the position
already moved to a free spot) with «Поставить» — or places at the point the owner clicks in the scene (U11); (2)
defaults that never land on an occupied place: offset the position to the nearest free spot (bodies: outside every
radius and outside the capture radius; atoms: the nearest site with insertion energy below the bound; a copy: shifted
by a few radii), choose the first free side for inlets/outlets; (3) a toast when an object just added is merged,
captured or absorbed within a few frames («Звезда 2 слилась с Солнцем через 0,05 года после добавления»).


## U5 (error). Palette and inspector actions that block the world with no way out

**Worlds.** p03 (2-D and 3-D, molecules and gas).

**Evidence** (`out/place.jsonl`, limit 30–40 s per command): «Молекулы» — `set shape` (bent, chain), `set start`,
⧉ copy, `set sz` in 3-D: > 30 s each; `count` = 2000: > 40 s; 2-D: `set sy = 1` 21.7 s then refused, `shape` 15–23 s
then refused. «Газ» `n` = 20 000 in 3-D: > 40 s. During that time the worker's loop handles nothing: no frames, no
pause, no other command (`sim.py:251-334` runs the command inline).

**Cause.** `_molecules` retries random placements up to `200 × count` times, each try an `md.add_molecule` with its
energy test (`p03_molecules/viz.py:453-505`); the gas's random fill similarly jams before it refuses.

**Suggested fix.** Estimate the packing fraction before placing and refuse at once what cannot fit; bound the
placement by wall time (≤ 1 s) with a vectorised trial (all candidates' insertion energies at once), and report how
many fit; never let a scene command block the loop longer than a frame budget without a progress notice.


## U6 (error). Palette actions that break the world and show a Python traceback

**Worlds.** p03.

**Evidence** (`out/place.jsonl`; in the browser `scripts/polyshot.mjs`, `out/polyshot.json`,
`shots/err_p03_hard_atom.jpg`: «Новый мир» → твёрдые диски, «＋ Атом», ⏺ — a toast with the whole traceback
«Traceback (most recent call last): File "/lf/visualizations/server/lfviz/sim.py", line 544 … File
"/lf/lfphys/lfphys/core/md/hard.py", line 731, in pressure … ZeroDivisionError: float division by zero», the same in
«События», the status «пауза · конец записи»):

| scene | action | then |
|---|---|---|
| p03, «твёрдые диски», empty box | ＋ Атом (defaults) | the next frame raises `ZeroDivisionError: float division by zero` in the pressure, `Z = 1 + W/(dim·n·T·dt)` with T = 0 (`lfphys/core/md/hard.py:731`, called from `p03_molecules/viz.py:698`, `:734`) |
| same | ＋ Атом at any x, y, σ, mass; ＋ Газ / ＋ Кристалл with T = 0 | the same |
| p03 Леннард-Джонс, periodic | ＋ Газ / ＋ Кристалл with T = 10⁵ K (the field's maximum) | `FloatingPointError: two interacting particles at the same point` |
| p03 Леннард-Джонс, walls | same | `FloatingPointError: a particle crossed the walls more than 64 times in one drift (dt too large)` |

**Cause.** The add is accepted (`on_add` validates placement only), the failure comes in the next step or frame; the runner
then emits `traceback.format_exc()` as the error's text, pauses the world (`sim.py:551-558`) and the player shows the
text in a toast and in «События» (`player.js:573-583`). Every ⏺ repeats it (the same traceback is not re-sent,
`sim.py:555`, so after the first the owner sees the world refuse to run without a new message).

**Suggested fix.** Validate in `on_add`/`on_set` what the step needs (the hard world: a single particle or zero
temperature — define the event queue's "no next event" instead of dividing; a temperature above what the time step
can resolve: refuse with the largest admissible T, or shorten the step); in the runner, show the owner a short Russian
sentence («шаг мира не удался: …; мир на паузе; последнее изменение можно отменить …») with the traceback folded under
«подробности»; offer to undo the last scene change (STATUS V37 d).


## U7 (error). Objects offered by the palette that the world can never accept with their defaults

**Worlds.** p03, p04, p02.

**Evidence** (`out/place.jsonl`):

| section | object | world | refusal |
|---|---|---|---|
| p04 | «Объёмная сила (тяжесть)» | the default world and every preset | «объёмная сила (0, −9.81) м/с² (гидростатический перепад g·L/c_s² = 0.2): плотность покоя схемы отклонилась бы от ρ0 на 0.0999 > 0.045 … её скорость звука c_s = 4.5 м/с — свойство счёта, не жидкости» |
| p03 | «Стенка (тип)» | the default box (periodic) | `axis y is periodic` (2-D Леннард-Джонс), `a periodic axis has no walls` (твёрдые диски) |
| p03 | «Поршень» | the default box, «Жидкость и пар» | `a piston needs a walled axis`; `0 < x_min <= X <= L, mass > 0, finite p_ext and V` |
| p03 | «Кристалл» | any scene with atoms | overlap (U4) |
| p02 | «Гармоническая ловушка» | «Двухщелевой опыт», «шар 3-D» | the grid band |
| p02 | «Магнитное поле» | any scene with a charged particle | «поле нельзя менять, пока заряженная частица … в окне» |

The buttons are enabled (`playground.js:60-61` disables only at the type's limit), so the owner learns it only by
the refusal. The p04 case needs a new world (a larger `u_max`, i.e. a smaller time step) to accept any gravity at all;
nothing tells him so.

**Suggested fix.** Each section reports, per palette type, whether the current world can take it and why not
(`palette_state()` in the header and after each change); the player disables the button with that reason as its
tooltip and, where a world parameter would make it possible, names it («нужны стенки: Новый мир → Границы»). For p04,
derive gravity's default from the world (the largest g the scheme accepts, or g scaled to the box) and say what the
owner must change for 9.81 m/s².


## U8 (error). Values far outside the world are accepted without a word

**Worlds.** p02, p04 (p03 refuses: «a particle outside the walls on axis x» — in English, U13).

**Evidence** (`out/place.jsonl`, `scripts/p02_far.py`): p02 2-D: a packet at x = ±10⁶ nm or y = ±10⁶ nm is accepted;
its probability in the window is then NaN (the inspector shows «—»; `viz.py:902` warns `invalid value encountered
in cast` while the picture is made). Boxes, balls, walls, steps, traps, fields, flux tubes, detectors and markers at
±10⁶ nm (window ±40 nm) are accepted in 2-D and 3-D. p04: disks, rectangles, airfoils, dye sources and probes at x or
y = ±10⁴ m (the channel is 2.2 × 0.41 m): accepted, nothing appears.

At the edge (`scripts/edges.py`, `out/edges.txt`): a p02 packet 5 nm or 1 nm from the window's edge is refused with a
clear reason («пакет не помещается в окно по оси 0: до края 5, нужно ≥ 22.3»); a p02 box centred on the window's edge
(half outside), a p04 disk centred on the outflow edge or on the bottom wall (half inside the wall) are accepted
without a note.

**Suggested fix.** Each `on_add`/`on_set` checks the object's extent against the world's region: refuse what lies
wholly outside (and a packet whose norm on the grid is not 1 within tolerance), warn for what is partly outside.


## U9 (should-fix). No feedback while a scene command is computed

**Worlds.** All playgrounds; worst in p02 (U3) and p03 (U5).

**Cause.** `playground.js:38-43` sends the command and returns; the player's pending indicator (`#busy`, «⟳ …») is set
only for `set`, `new_world` and a resume (`player.js:213-235`, `:336`). The status keeps «запись идёт · вживую»
(browser: `out/palette.log`, every row of p02). Repeated clicks queue further adds (U3's table).

**Suggested fix.** `setPending("scene")` («⟳ меняется сцена…») from the send until the `scene` message or the error
arrives; disable the palette and the inspector meanwhile (or mark the clicked button); show the elapsed seconds after
1 s.


## U10 (should-fix). The inspector loses the focus after every change

**Worlds.** All playgrounds.

**Evidence** (`scripts/inspector.mjs`, `out/inspector.json`, `shots/inspector_p01.jpg`; p01 «Солнце … Юпитер»,
recording): «Земля» selected;
«Масса, M⊕» set to 2 and Tab pressed — the focus moves to the same parameter's slider (`type: range`), then, when the
world's `scene` message arrives (the inspector is rebuilt), to `BODY`; a following keystroke goes nowhere.

**Cause.** `drawInspector` (`playground.js:90-108`) is called from `drawObjects` on every scene message with a new
revision (`:207-208`), replacing every input; `control()` puts the slider after its number field in the tab order
(`ui.js:168-178`).

**Suggested fix.** Update the inspector's controls in place (`c.set(value)`, as `refreshLive` does for live
parameters, `player.js:171-187`) and rebuild only when the selected object or its type changed; take the sliders out
of the tab order (`tabIndex = -1`) or put them before the field.


## U11 (should-fix). No direct manipulation in the scene

**Worlds.** All playgrounds.

**Evidence.** The views have no picking, placing or dragging of objects: no pointer handlers in `pNN_*/web/view.js`;
`scene3d.js` picks only slice planes (`:793-852`). An object is selected only in the list, positioned only by typing
coordinates in the inspector, and placed only with defaults (U4).

**Suggested fix** (the owner's «больше интерактива»): click an object in the scene to select it (the inspector
follows); drag it in the view plane (a `set` on release, as the sliders do); place a palette object at the clicked
point; a velocity arrow handle for bodies and packets; keyboard nudges. All of these send the existing `scene`
commands, so recording and restore are unchanged.


## U12 (should-fix). Laws the engine can already change now are "new world" parameters

**Worlds.** p01, p03, p04; v13, v14 among the demonstrations. Details in «Laboratory: facts and constraints».

**Evidence.** The engine has setters that act at the current moment, unused by the playgrounds:
`lfphys/core/fluids/lbm.py:2198` `set_viscosity` («Change the viscosity now (tau changes; the time step stays)»),
`:2209` `enable_dye`, `:2218` `set_dye_diffusivity`; `lfphys/core/md/system.py:979` `set_pair` (the interaction model
and its cut-off and shift), `:985` `set_dt`; `NBody.collisions` is a plain attribute read at each contact
(`nbody.py:283`, `:713`, `:928`, `:963`). All of them are world parameters (`p04_fluids/viz.py` SCHEMA `nu`, `rho`,
`fluid`, `dye`, `dye_D`; `p03_molecules/viz.py` `model`, `cutoff`, `shift`, `dt_fs`; `p01_gravity/viz.py`
`collisions`), so each change starts a new world with an empty or preset scene. In v13 and v14 all 13 parameters
(`atom`/`system`, `n`, `l`, `m`, the superposition) are world parameters: choosing an orbital starts a new world.
In v11 (and v12) the slits' width a, their distance d, the plate's thickness w and the wall's height V₀ are world
parameters, while closing a slit is live and goes through `set_live` → `_hamiltonian` → `prop.rebuild(V, W, A, b)` at
the current moment (`v11_double_slit_2d/viz.py:306-312`, `:340-361`): the same rebuild would take a new plate inside
the same grid (the grid and window, set from λ, a, d and L at construction, bound how far they may change).

**Suggested fix.** Make these live (with their change recorded as an event and the conservation references
restarted, as an object change already does): p04 ν, ρ, the dye and its diffusion; p03 the model, cut-off, shift, dt;
p01 collisions; v11/v12 a, d, w, V₀ within the grid's limits. In v13/v14 the state is a preparation: an action
«приготовить состояние n, l, m» at the current moment.


## U13 (should-fix). Refusals speak the engine's language

**Worlds.** p03 (English), p02 and p04 (numerical jargon).

**Evidence** (`out/place.jsonl`, `out/palette.log`; the toasts as shown: `shots/palette_p02_slit_toast.jpg`,
`shots/palette_p03_piston_toast.jpg`, `shots/palette_p04_cyl_toast.jpg`):
* English, passed through `sim.py:329` («Сцена: {e}»): `random placement jammed: 61 of 300 placed without overlaps;
  fewer particles, a larger region or a lattice`; `overlap: an inserted particle's potential energy 3.501e+28 exceeds
  max_insert_energy = 50`; `refused: two interacting particles at the same point`; `overlapping hard particles`;
  `axis y is periodic`; `a periodic axis has no walls`; `a piston needs a walled axis`; `0 < x_min <= X <= L, mass >
  0, finite p_ext and V`; `a thermal wall needs a temperature T > 0`; `charges in a box with a periodic axis: the
  Coulomb lattice sum (Ewald) is not implemented; use walls on every axis`.
* p02's refusal of a packet in the double-slit preset: «сетка не передаёт волну частицы 2: её волновые числа доходят
  до 9.752 (|k| + 6σ_k и энергия 38.98, которую потенциал может перевести в движение), а сетка рядом с тем, что
  действует на частицу, передаёт ≤ 6.702 (2/3·π/d: … — яма −3 эВ шириной 4 нм на сетке 0,31 нм пропускала 0,923
  вместо 0,997); сделайте сетку мельче, частицу медленнее или потенциал мельче» — the scene has no well; the cause the
  owner needs («пакет попал внутрь стенки: сдвиньте его по x») is not said; «сетку мельче» is a new world.
* A refused live change names the parameter's internal id and says «max» in English (`server/lfviz/params.py:184`,
  `:186`): «Изменение не применено: obs_beta: 1.0 > max 0.99» (v10, typing 1 for the observer's speed), «Изменение не
  применено: incl: 179.3 > max 179.0» (v15) — `out/use.log`, the first live control of each world changed by 10 %.
* p04's gravity (U7) and outlet pressure: «плотность покоя схемы отклонилась бы от ρ0 на 0.0494 > 0.045 (масштаб
  давления схемы c_s²ρ(dx/dt)² = 20.25 Па …)».

**Suggested fix.** At each section's boundary translate the engine's refusals into the owner's terms: what is wrong
in the scene, which object, and which change of the object or of the world fixes it (with the number to use); keep
the engine's sentence under «подробности».


## U14 (should-fix). «События» is rebuilt on every drawn frame

**Worlds.** All.

**Cause.** `player.js:703` sets `S.eventsDirty = true` on every render, so `renderEvents` (`:776-785`) replaces up to
400 rows 20 times a second while the world records, whether or not an event arrived. A click needs the press and the
release on the same element; a human click (~100–150 ms) spans two or three rebuilds. Text in «События» cannot be
selected for the same reason.

**Evidence** (`scripts/clicks.mjs`, `out/clicks.json`: the list was rebuilt 6 times a second while recording — under
the host's load; 20 at the full frame rate. `scripts/clicks_control.mjs`, `out/clicks_control.json`: v04 at 0.1 s/s,
the first line of «События» scrolled into view and clicked with the button held 150 ms, alternately while recording
and while paused, 8 times each: the cursor went to the event 0 of 8 times while recording and 8 of 8 while paused).
The click entries of `out/clicks.json` were taken with the line below the fold and are superseded by the control.

**Suggested fix.** Rebuild «События» only when the list or the cursor's position relative to its items changed
(a key like the checks'), append new rows instead of replacing all, and toggle the `future` class in place.


## U15 (should-fix). 2-D sections: the computed field is a side window

**Worlds.** p02 (2-D), p04.

**Evidence** (`scripts/usability.mjs`, `out/use.log`, `shots/use_p04_fluids_cylinder_re20_1280.jpg`,
`shots/use_p02_quantum_double_slit_1600.jpg`): at 1280×800 the p04 flow picture is ≈ 330×140 px in the slice window,
the 3-D view of the flat channel 360×659 px; at 1600×1000 the p02 wave window is 430×420 px while the 3-D view of a
±40 nm × ±6 nm slab shows mostly empty space. The 3-D view's toolbar also offers «С источника», «С мишени» (U21).

**Suggested fix.** For a world whose physics lives in one plane, make the plane's window the main view (the 3-D
scene a toggle or a small inset), at the full centre size; keep the 3-D view for 3-D worlds.


## U16 (should-fix). The checks panel is a wall of reviewer notes; cut off at 1280 px

**Worlds.** All; most in v04, v02, p01–p04.

**Evidence** (`scripts/usability.mjs`, `out/use.log`, `shots/use_v04_orbits_default_1280.jpg`,
`shots/camera_p01_inner_zoomed.jpg`): every check prints its note in full under the value — in v04 the first three
checks take the whole right column at 1600×1000 («эталон — lfphys.core.gravity.orbits.elements от e² − 1 (без потери
точности), корни кубики с 30 знаками; допуск 10⁻¹¹ + 4ϵ·κ + 2·s·δ: κ = Σ|членов f|/(|f′(u)|·u) = 4.55 …»); p01's four
conservation checks fill 1600×1000 to the bottom, pushing «Датчики» and «Слои сцены» out of sight. At 1280×800 the
right column is 300 px and v04's table 309 px: the ✓ column is cut by 8–10 px and the column scrolls sideways (`#right`
scrollWidth 309 > 299; the group title «Отрезок 0 (ОТО, связанная (эллипс с прецессией))» overflows by 10 px); v07's
table needs 321 px, v15's 361 px (U20's table).

**Cause.** `player.js:761-764` renders `c.note` as a block under the label; `player/assets/chrome.css:146`
(`.main` 260 / 1fr / 300 px at ≤ 1280 px) against the table's minimum width.

**Suggested fix.** One line per check (label, value, reference, ✓) with the note behind a disclosure or a tooltip;
group summaries («все 7 ✓») that expand; keep the ✓ column fixed-width and wrap the label instead.


## U17 (should-fix). «Прежние группы проверок» closes itself

**Worlds.** All with more than four check groups (v04 after live changes, v02, v11, v12 …).

**Cause.** `renderChecks` builds a new `<details class="older">` (closed) on each call (`player.js:742-744`), called
whenever a check arrives or the cursor's check count changes (`:709-717`).

**Evidence** (`scripts/clicks.mjs`, `out/clicks.json`): v04 with six «толчок» actions (seven segments, seven check
groups) while recording; `details.older` opened, its state sampled every 250 ms: `1111000000000000…` — closed again
after one second and stayed closed.

**Suggested fix.** Keep the `details` element (or its `open` state) across renders.


## U18 (should-fix). The Newtonian black hole cannot be seen

**Worlds.** p01 (Newton laws), «Чёрная дыра 1000 M☉ и звёзды» and any scene with «＋ Чёрная дыра».

**Evidence.** `shots/curve_p01_hole_default.jpg`: the two stars' orbits around an empty centre; the hole is not
visible at any zoom of that shot.

**Cause.** `p01_gravity/viz.py:508` sends the colour (0.1, 0.1, 0.12) for holes; the 3-D view clears to `#0b0e14`
(`scene3d.js:181`, `chrome.css:159`); its radius is the Schwarzschild radius (3 km for 1000 M☉ is 2·10⁻⁸ а.е.), so even
the size gives nothing to see.

**Suggested fix.** Draw a hole as a marker of fixed screen size with a light rim (as v04 draws a point mass with a
fixed-size marker, `v04_orbits/web/view.js:154-157`) and label it.


## U19 (should-fix). Units missing on primary parameters

**Evidence** (schemas, `GET /api/viz`): v11 and v12 «Ширина щели a», «Расстояние между щелями d», «Толщина пластины»,
«Расстояние до экрана/детектора», «σx», «σz», «σy», «Ширина краёв…», «Расстояние между пакетами» — in units of λ,
said only in the help of «Длина волны де Бройля λ» («все длины опыта — в λ»), which itself has no unit in its label
(its id `lam_pm`); v12 «Высота стенки» (in units of the kinetic energy: said in v11's help, not in v12's), «Мягкий
детектор: W₀», «Поглощающая граница: κ» without unit or help.

**Suggested fix.** Put the unit in every label («Ширина щели a, λ», «Длина волны де Бройля λ, пм», «Высота стенки V₀,
в E»).


## U20 (should-fix). At 1280×800 the demonstrations are cramped

**Worlds.** All demonstrations at a laptop's 1280×800; worst v07, v03, v02.

**Evidence** (`scripts/usability.mjs`, `out/use.log`, `shots/use_v07_bell_test_spin_lhv_1280.jpg`,
`shots/use_v04_orbits_default_1280.jpg`): the largest canvas of the centre and its share of the window:

| world (preset) | main canvas at 1600×1000 | at 1280×800 | top / bottom bar at 1280 | right column at 1280 |
|---|---|---|---|---|
| v07 (`photon_chsh`, `spin_lhv`) | 502×779, 24 % | 384×434–454, 16–17 % | 81–102 / 67 px | table 306–321 px in 299: ✓ and references cut |
| v02 (`photon_young`) | 502×778, 24 % | 384×520, 20 % | 42 / 67 px | — |
| v03 (`tunnel`) | 940×470, 28 % | 720×305, 21 % | 81 / 67 px | — |
| v05, v06, v01 | 502×817–849, 26–27 % | 384×549–591, 21–22 % | 42–81 / 67 px | — |
| v04 (`default`) | 563×810, 29 % | 431×557, 23 % | 42 / 67 px | table 309 px in 299: ✓ cut by 8 px |
| v15 (`m87`, `ring`) | 470×877, 26 % | 360×661, 23 % | 71 / 67 px | 361 px in 299 |
| v10, v11, v12, v17, p02, p04 (3-D view + a window) | 470×851–917, 25–27 % | 360×661, 23 % | 71 / 67–69 px | window titles cut |
| v08, v09, v13, v14, v16 | 564×877–917, 31–32 % | 432×661–691, 28–29 % | 42–71 / 67 px | slice titles cut |
| p01, p03 | 940×917, 54 % | 720×659, 46 % | 71 / 67–69 px | — |

v07 «спин, знаковая модель Белла»: the top bar takes three lines (102 px: the «МОДИФИЦИРОВАННАЯ ФИЗИКА: …» badge alone
fills one), and in the centre's 2×2 panels labels overlap («только квантовая» over the scale's end, the two «выбрана
для следующей частицы» under the stations over each other, the column «z» of the pair table cut).

**Cause.** Fixed side columns (260 px and 300 px at ≤ 1280 px, `player/assets/chrome.css:146`), the top bar's badges
(the modified-physics badge is not shortened, `player.js:635-637`, unlike the approximations, `:640-641`), the bottom
bar's fixed minimum widths (`chrome.css:115` `.speedbox` min 220 px, `run.html:44` `#speedv` 110 px, `chrome.css:112-113`
`.timeline` min 200 px and `.time` min 210 px).

**Suggested fix.** Side columns that fold away (a key and a button; the centre takes the room), badges shortened to one
line with the list on hover, the bottom bar in one line (the speed's scale on hover, the time inside the timeline);
the views' panels laid out by the space they get (v07: 2×1 below 900 px of centre width).


## U21 (nit). Slice tools in worlds without slices

**Worlds.** Every 3-D world whose header says `planes.max = 0`: p01, p02, p03, p04, v10, v11, v12, v15
(`p01_gravity/viz.py:607`, `p02_quantum/viz.py:1080`, `p03_molecules/viz.py:910`, `p04_fluids/viz.py:919`,
`v10_fast_observer/viz.py:685`, `v11_double_slit_2d/viz.py:981`, `v15_kerr_shadow/viz.py:601`).

**Cause.** `scene3d.js:919-925` always adds «✥ Двигать» and «⟳ Наклонять», env3d its scale selector, and the hint
line (`scene3d.js:176`) speaks of slices; env3d hides only «＋ Срез» when `planes.max = 0` (`env3d.js:217-218`).

**Suggested fix.** Hide the gizmo modes, the scale selector and the slice part of the hint when the world has no
planes and no volume.


## U22 (nit). Palette buttons do not say why they are disabled

**Cause.** `playground.js:60-62`: disabled at the type's limit or at `max_objects`, with the type's help as the
tooltip. Conversely enabled where the world refuses (U7).

**Suggested fix.** Tooltip «не больше 1 в сцене» / the world's reason (U7).


## U23 (nit). The playground's left column

`player.js:101-105`: «Действия» comes first even when it says «Нет действий» (p01, p03, p04), and «Новый мир» is open
by default in the playgrounds (`closed: liveParams().length > 0`, playgrounds have no live parameters). The palette and
the objects — what the owner uses most — start below. Suggested: hide an empty «Действия»; «Новый мир» closed.


## U24 (nit). Small labels and wrapping bars

The speed slider's scale is 9 px (`player/assets/chrome.css:117`; the wrapping bars at 1280 px are in U20); at 1600 px
in p02 and p04 the bottom bar wraps too (the world time on its own line,
`shots/use_p02_quantum_double_slit_1600.jpg`). Suggested: 11 px scale; a shorter bottom bar (the speed's scale under the
slider only on hover, or a narrower slider).

---

## Laboratory: facts and constraints

The owner's direction: experiments within one world, without restarting; add objects, change conditions and see the
result at once; more parameters; objects to test interactions; one place for research. Below: what the code allows
today, per playground, then what a shared laboratory would need. Facts with locations; no wishes.

### Which parameters start a new world, and could each be live with the engine as it is

Rules in force: a law is a world parameter (`RULES.md` §2.4); `new_world` builds a new `Simulation`
(`sim.py:361-378`); a playground's new world without a scenario starts empty (`player.js:330-332`).

**p01 «Космос и гравитация»** (`p01_gravity/viz.py:86-101`)

| parameter | live today? | could be live with the engine as it is | constraint |
|---|---|---|---|
| `laws` (Newton / PN binary / Kerr–Newman) | no | no | three different solvers and palettes (`viz.py:172-176`); the states do not map (N bodies with self-gravity ↔ one binary ↔ test bodies in a fixed metric) |
| `collisions` (merge / pass) | no | **yes** | `NBody.collisions` is read at each contact (`nbody.py:713`, `:928`, `:963`); switching to "pass" needs `_update_overlap()` once |
| `m_hole` (Kerr) | no | yes, as an event | the solver works in G = c = M = 1; a new M rescales seconds and metres; positions in metres would have to be re-expressed in M (a physical mass change, flagged) |
| `spin`, `charge` (Kerr) | no | not without a model | `KN.Geodesics(a, q)` fixed at construction (`viz.py:661`); a change of the metric under moving bodies has no established dynamics (it would be a declared "what if": keep each body's local ZAMO velocity and recompute E, L, Q) |
| `m_total` (PN) | no | yes, as a parameter of the binary object | the binary is integrated in G = c = m = 1 (`viz.py:1018-1021`), m only scales seconds and metres; the binary's own parameters already restart it from the current moment (its palette help: «изменение параметров начинает двойную заново с текущего момента») |

**p02 «Квантовые частицы»** (`p02_quantum/viz.py:57-71`)

| parameter | live today? | could be live | constraint |
|---|---|---|---|
| `dim` (2-D / 3-D) | no | no | a 2-D wave has no z profile; a 3-D world would need one chosen (as v11's free factor η(y, t)) |
| `n2`, `n3` (grid), `size` (window) | no | possible, not in the engine | the grid is fixed when the scene is built (`QS.Scene`, no regrid method among `scene.py`'s methods); a band-limited ψ can be resampled exactly onto a finer grid by Fourier padding and onto a larger window by zero padding where ψ ≈ 0; the absorbers and the time step re-tuned (today 18–60 s on the CPU, U3) |
| `edges` (open / closed) | no | yes in principle | the open edges are complex absorbing layers (`QS.EdgeLayers`, `viz.py:286`, `:577`); switching changes only the potential; a wave inside a layer is part-absorbed at the switch (to be counted) |

**p03 «Частицы и молекулы»** (`p03_molecules/viz.py:62-85`)

| parameter | live today? | could be live | constraint |
|---|---|---|---|
| `model` lj ↔ wca | no | **yes** | `md.set_pair` (`system.py:979`) inside a transaction; the energy jumps by the difference of the potentials (record it, restart the energy reference) |
| `model` ↔ hard | no | no | the hard model is an event-driven solver (`core/md/hard.py`), another integrator; positions closer than σ cannot be taken over |
| `cutoff`, `shift` | no | **yes** | `set_pair` with the new term |
| `dt_fs` | no | **yes** | `md.set_dt` (`system.py:985`) restarts the drift reference |
| `Lx`, `Ly`, `Lz` | no | possible, not in the engine | a box change is a deformation (affine rescale, as a barostat) or an added empty slab; `System(box=…)` fixed at construction (`system.py:448`); the piston already moves one wall |
| `boundary` | no | per axis, partly | walls ↔ periodic per axis: walls → periodic always; periodic → walls only when no particle crosses the new wall; the playground's «Стенка» object only changes the kind of a wall on an axis that is already walled (`md.set_wall`, `system.py:890`) — boundaries as per-axis objects would remove this world parameter |
| `dim` | no | no | |

**p04 «Жидкости»** (`p04_fluids/viz.py:49-76`; the solver `lfphys.core.fluids.lbm.Flow2D`)

| parameter | live today? | could be live | constraint |
|---|---|---|---|
| `nu` (and `fluid` = custom) | no | **yes** | `Flow2D.set_viscosity` (`lbm.py:2198`) — «Change the viscosity now» |
| `rho` | no | yes (no setter yet) | in the incompressible regime ρ only scales the pressures and forces reported (`Flow2D(…, rho=…)`, `lbm.py:1058`); the velocity field does not depend on it |
| `dye`, `dye_D` | no | **yes** | `enable_dye` (`lbm.py:2209`), `set_dye_diffusivity` (`:2218`) |
| `collision` (TRT / BGK) | no | yes (no setter yet) | read when the relaxation times are set (`lbm.py:1146-1149`, `_relax`), which `set_viscosity` already re-runs; both operators share the equilibrium, so a switch at the current state is consistent |
| `u_max` (sets the time step through the lattice Mach number) | no | possible, not in the engine | a new dt rescales the lattice velocities and the non-equilibrium part (as in grid refinement); refused gravity (U7) depends on it |
| `Lx`, `Ly`, `nx` | no | possible, not in the engine | regridding of f (macroscopic fields + rescaled non-equilibrium part); obstacles re-voxelised |
| `fluid` water / air | no | as `nu`, `rho` | the engine refuses water and air at these scales («не разрешаются сеткой», SCHEMA help) |

### Objects and interactions a researcher would want and the palettes lack

From the palettes (`viz.py` `palette()` of each section) and PLAN P15 (`lfphys/PLAN.md:152-159`):

* p01: extended bodies and tides on them (only point masses and a tidal probe), rings / disks of test particles in
  one click (a "cloud" object), a rocket or thrust (no action changes a body's velocity except editing it), charged
  test particles near the Kerr–Newman hole (STATUS V38 c), what an observer near the hole sees (`trace_sky`, V38 d), a
  probe of orbital elements (a, e, period) per body; mixing Newtonian bodies with a relativistic hole is impossible
  (separate laws).
* p02: interacting particles (each packet has its own wave; «частицы не взаимодействуют», `p02_quantum/viz.py:13`, `:230`), a time-varying
  potential (a moving barrier, a pulsed field), a free-form potential (drawn or imported), a measurement other than
  position (momentum, spin along an axis), an absorbing screen that records hits as clicks (only integrated
  probability).
* p03: chemistry (bond formation/breaking: bonds are fixed harmonic springs), external flow or shear, a velocity
  probe / flux through a plane, charged particles in a periodic box (Ewald missing: refused), mixtures by palette
  rather than per-object species.
* p04: free surface or two fluids, heat (temperature as a field), moving bodies with their own dynamics (bodies are
  prescribed; «"moving" bodies did not move (relabelled)», review B7-lbm), 3-D flow, compressible flow (the Euler shock
  tube is left, STATUS V41 x).

### One shared laboratory: what it would take

Facts that constrain it:

1. **One section = one solver = one set of units.** p01 Newton: а.е., years, M☉ (`p01_gravity/viz.py:226-231`); Kerr:
   G = c = M = 1; PN: G = c = m = 1; p02: nm, m_e, ħ = 1, a time unit of 8.6·10⁻¹⁵ s (`p02_quantum/viz.py:32-34`), steps
   ~0.07 fs; p03: argon's reduced units, nm, ps, K, steps of 10 fs (`p03_molecules/viz.py:21-41`); p04: SI metres with
   lattice units, steps ~1.6 ms at 256 nodes. The scales span more than twenty orders of magnitude in time and in length (femtoseconds to
   years, nanometres to astronomical units): no single integrator advances them together, and the engine has no coupling layer between `core.gravity`, `core.quantum`, `core.md` and
   `core.fluids` (PLAN P15.0 asks for "a solver interface per section", `PLAN.md:152`, not across sections).
2. **The framework holds one `PlaygroundSimulation` per world with one `PALETTE`** (`playground.py:100-128`), chosen
   when the world is built (p01 picks the palette from `laws`, `p01_gravity/viz.py:176`); a scene file is refused by another
   section (`playground.py:73-74`). Several sections in one scene would need a composite simulation that owns several
   solvers, a common clock with sub-stepping, and a declared coupling for every pair it claims (e.g. a body in a flow:
   force from the fluid's momentum exchange, which `lbm.py` computes for obstacles, but obstacles are prescribed).
3. **Physically meaningful cross-section couplings exist only at matching scales**, e.g. p03 atoms ↔ p02 packets (both
   nm, but MD is classical: a quantum particle in a classical bath is a model — decoherence is already offered as
   «Среда»); p04 flow ↔ p03 particles (Brownian motion: scales differ by 10⁶; a coarse-grained model); p01 ↔ others: no
   shared scale. Each such coupling is a model outside the engine's core (`lfphys/LAYERS.md`) and would be flagged.
4. **"One world per section that never restarts"** is reachable with the engine largely as it is: the laws marked
   **yes** above become live parameters (or properties of objects: the hole's mass, the binary's mass, the boundary per
   axis), and the rest (grids, windows, boxes, time steps) need regridding/rescaling in the engine (p02 resampling, p03
   box deformation, p04 regridding). Until then a change that needs a new world could carry the scene over: today a
   new world without a scenario starts empty (`player.js:330-332`, review B6-F18), although the scene can be exported
   and re-imported by hand (`playground.py:252-263`).
5. **Responsiveness is the binding constraint now**: a live laboratory needs a scene change to show within a frame or
   two; today p02 takes 18–60 s (U3), p03's molecule edits block for > 30 s (U5), and every command blocks the worker's
   loop (`sim.py:251-334`). Any shared or never-restarting world inherits this unless scene commands become
   incremental and the expensive re-tuning is cached or deferred.

---

## Reproduction

Server (CPU, private):

```
docker run -d --name lf-uxb-srv -p 8562:8479 -v <engine>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
  -e LFPHYS_NO_GPU=1 -e PYTHONDONTWRITEBYTECODE=1 -e OMP_NUM_THREADS=2 -w /lf/visualizations light-funnel-viz \
  python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
```

Browser scripts (`scripts/*.mjs`; copy them next to a `node_modules/playwright` 1.58.2; `PORT` defaults to 8562):

```
docker run --rm --init --shm-size=2g --network host -v <dir with the scripts and node_modules>:/pw -w /pw \
  mcr.microsoft.com/playwright:v1.58.2-jammy node /pw/<script>.mjs [cases]
```

Harness scripts (`scripts/*.py`; put them in `<dir>/py/`, outputs go to `<dir>/out/`):

```
docker run --rm -v <engine>:/lf:ro -v <dir>:/aui -e LFPHYS_NO_GPU=1 -w /lf/visualizations light-funnel-viz \
  python3 /aui/py/<script>.py [sections]
```

| script | what |
|---|---|
| `scroll.mjs`, `sum_scroll.py` | scroll positions under live data (U1, the "checked and working" part) |
| `camera.mjs` | 3-D zoom kept or not; v04's refit (U1) |
| `polylines.py`, `polyshot.mjs` | sampling of the curves; zoomed screenshots (U2); the hard-disk traceback (U6) |
| `place.py`, `p01_merge.py`, `p02_far.py`, `edges.py` | every palette object through the scene command: defaults, twice, in a preset, at the limits and the region's edge, edits, copy, removal (U3–U8, U13) |
| `palette.mjs` | every palette button clicked in the browser (U3, U4, U7, U9, U13) |
| `p02_prof.py`, `p02_time.py` | profile and wall time of p02 scene changes (U3) |
| `usability.mjs` | all worlds at 1600×1000 and 1280×800; the first live control of each changed by hand (U13, U15, U16, U19, U20, U24) |
| `clicks.mjs`, `clicks_control.mjs` | a human click on «События» while recording and while paused; «Прежние группы проверок» (U14, U17) |
| `inspector.mjs` | editing, removing and selecting objects in the browser while recording (U1's object list, U10) |
