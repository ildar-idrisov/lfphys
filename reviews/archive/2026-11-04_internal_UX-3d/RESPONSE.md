# Response to review UX-3d (2026-11-04): the player's 3-D scenes — depth, flat objects, camera

**Processed 2026-11-05** by a Claude Opus subagent that wrote neither the review nor the code under review
(`../README.md`). The review text is not edited. Also processed here: **the camera part of UX-ui U1** (sibling review
`../2026-11-04_internal_UX-ui/`, nothing written in its folder). The rest of U1 (the playground re-sending its box,
v04's refit, the object list) and A13 belong to other agents.

**Result.** Of A1–A19: **17 fixed, 1 partly fixed (A6), 1 handed over (A13 → processed with UX-ui U2), 0 rejected**;
the A6 remainder and four limits of the new renderer are deferred to STATUS (text at the end). UX-ui U1, camera part:
fixed. The full-quality frame got cheaper, not dearer, in all three heaviest worlds (§ Performance).

**A6, the playgrounds' part** («◎ Центрировать», «👁 Следить» on `centerOn`): processed afterwards by the framework agent, fixed — `RESPONSE_framework.md` in this folder.

**Where.** All fixes are in the shared 3-D code, so every world benefits:

| file | change |
|---|---|
| `visualizations/player/js/scene3d.js` | the rendering contract (below): depth pass and depth-aware, split volume march; opaque slice planes; translucent surfaces with depth-only twins, ordered by their nearest point; own lit shaders (solids, value surfaces, arrows, vector glyphs), sphere impostors, wide lines, round points; views in the frame of "up" and for 2-D worlds; corner fit, refit until the user moves, `setBox` that never moves a moved camera, near/far per frame; pixel-size labels on the box's outer edges; optical depth per densest column; adaptive quality; colour bar; double-click pivot, F / Shift+F; test hooks (`pixelAt`, `cameraState`, `frameStats`, `pick`, `centerOn`) |
| `visualizations/player/js/env3d.js` | `createEnv3D(ctx, {plane2d})` for 2-D worlds; Delete only (no Backspace); the density slider's title |
| `visualizations/player/js/orbitview.js` | v13/v14 clouds kept as sent (8-bit amplitudes) and painted through a 256-entry table; τ = 4; no double dispose of the current glyphs |
| `visualizations/player/assets/chrome.css` | `.s3d-legend`, `.s3d-note` (3-D view rules only) |
| `visualizations/v10_fast_observer/web/view.js` | A12: a panel body's mesh drawn with one colour per checker cell |
| `visualizations/p02_quantum/web/view.js`, `p03_molecules/web/view.js`, `p04_fluids/web/view.js` | A3: each declares its 2-D plane (`plane2d`); p04's obstacles opaque (solid, lit) |
| `visualizations/tests/browser/scene3d_checks.mjs` (new) | the browser regression of this contract, 12 cases |
| `reviews/2026-11-04_internal_UX-3d/response_checks/` (new) | the review's scripts copied and changed to run the code before ("orig", git HEAD a55d0fc) and after ("new") in one environment at one time; their outputs' summary; the figures `figs/r*.jpg` |

`imagewin.js`, `keyframes.mjs`, `player.js`, `playground.js`, the server and every `viz.py` are unchanged. No
third-party code was added: the wide lines and the impostors are written here from the usual screen-space and
ray–sphere constructions (no `Line2`/`LineMaterial` vendored), so `dependencies.md` and `vendor/README.md` need no change.

## The rendering contract (what the code now guarantees)

1. **Depth.** Everything opaque writes depth: solids, lines, slice planes. Each frame with a visible volume first draws
   the opaque scene (three.js layer 0) into a render target with a depth texture; the volume's ray march ends at that
   depth (converted to a distance along the ray), and the volume is drawn on the box's back faces without a depth
   test. The cloud in front of an object therefore covers it, the cloud behind it is hidden (A1, A19).
2. **Translucent surfaces** (run meshes below opacity 1, boxes, panels, the waist disk, the sphere object's surface)
   show their nearest layer: each has a depth-only twin drawn just before it (a flat one's twin only for the split
   below: a plane has one layer); they are ordered far to near by their
   nearest point (distance to the bounding sphere minus its radius), so an enclosed surface is drawn before the one
   around it. A second depth pass of the twins splits the volume at the nearest translucent surface: the cloud behind it
   is drawn before the translucent objects, the cloud in front after them (A2).
3. **Lit materials.** Solids are lit by a light that moves with the camera (view space: from the viewer, up-left):
   spheres as exact ray-traced impostors (one quad per sphere, true depth written), arrows as a lit shaft and cone,
   vector glyphs the same (instanced), run meshes lit with their colour kept where they face the viewer, lines 1.5–2.5 px
   wide with round ends, particles round and shaded; the wire globe dims its far half. Data surfaces (slice planes,
   panels, targets, images) are not lit: their colour is the value (A5).
4. **Views by "up".** The presets live in a frame U (up), R (screen right), F (toward the viewer) built from the world's
   `up`; a view along U takes its screen-up from the frame (v08 «Сверху» shows z right, x up, as the slice window). A 2-D
   world declares its plane (`plane2d`) and opens looking at it from above (A3, A14).
5. **Fit after layout.** A view fits the 8 corners of the region (the box and the apparatus objects) inside the canvas
   less the toolbar and the hint; it is fitted again on every resize and every box change until the experimenter
   moves the camera (OrbitControls' `start`); after that nothing but the experimenter moves it (A4, A7, U1).

## Findings

Status tags (AGENTS.md §3.11): [useful] the fix verified and it matters; [neutral] checked, no effect beyond the
finding; [weakens] the finding mattered less than stated; [error in earlier] a statement of ours withdrawn.

### A1 — error: the volume ignored what is in front of it — **fixed** [useful]

Fix as proposed, in `scene3d.js`: the depth pass and the depth-aware march (contract item 1); the volume mesh has
`depthTest: false`. Verified with the review's own probe run on both versions (`response_checks/probe_ab.mjs volsphere`,
v13 2p_z, density slider at 80 %, two opaque probe spheres): at the **back** sphere's pixel, before = (51, 255, 77),
exactly the sphere's own colour with no cloud; after = (175, 86, 116), the cloud's colour there (174, 83, 115) — the lobe
in front covers it. At the **front** sphere: after = (81, 254, 98) against the sphere alone (81, 255, 98). Regression:
`scene3d_checks.mjs depth` (the same geometry, asserted). Figures `figs/r01_volume_depth.jpg`, `figs/r20_translucent.jpg`
(p02 «Шар в 3D»: the potential ball no longer cuts the packet in front of it; v17 `near`: no wireframe cuts).

### A2 — error: planes, panels and translucent meshes drawn in object order — **fixed** [useful]

Slice planes are opaque and write depth; a plane not pointed at is darkened (`uDim`), not made transparent. Panels and
translucent meshes follow contract item 2. The wireframe overlay of translucent meshes (it also cut the volume, A1) is
gone: the meshes are lit instead. Verified: crossing planes painted flat (plane 1 red, plane 2 green), v13 1s with
planes y = 0 and x = 0, at 8 points of plane 2 where the line of sight crosses plane 1 inside the box (and where it does
not): the nearer plane is seen at all 8 (`scene3d_checks.mjs planes`). In the review's flat-coloured screenshots the
ratio of plane 1's to plane 2's visible pixels is 2 408 / 71 445 = 0.034 before, 0.32 with the review's proposed depth
writing (17 918 / 55 541), and 0.32 after (38 123 / 119 137; the box is larger on screen, A4). The review's two-point check (`probe.mjs
twoplanes`) reads one point whose line of sight passes beside plane 1 (it crosses y = 0 outside the box), so its
"plane 2 should lose" there is not a test of the order; the 8-point check replaces it. The cloud in front of a plane: v13
1s, plane 1 painted one colour, a point above its middle: pixel (162, 50, 115) with the cloud, (200, 64, 114) without —
the cloud is drawn over the plane. Figures `figs/r02_plane_and_volume.jpg`, `figs/r03_two_planes.jpg`.

Limit (deferred, STATUS text below): the volume is split at the **nearest** translucent surface only; a second
translucent layer inside the cloud is composited as if it were behind the cloud's front part.

### A3 — error: the views ignored "up"; 2-D worlds opened edge-on — **fixed** [useful]

`view()` now builds its presets in the frame of contract item 4: for z-up worlds (p02 3-D, p03 3-D) «Изо» looks from the
−y side and above, «Сбоку» is the x–z plane, «Сверху» looks down z with x right and y up. 2-D worlds declare their
plane in their views (the only change there): p02 (`grid.ndim == 2`), p03 (`md.ndim == 2`), p04 (always); their views
are «Изо» (the plane from above at ≈ 58°, x right), «Сверху» (p02, p04: the plane lying, x right, y up) or «Спереди»
(p03 2-D: the plane standing, y up) and «С ребра». The frame's labels follow the same axes. Verified: p04 opens with the
camera above the plane, and «Сверху» has +x to the right and +y up on screen (`scene3d_checks.mjs views`); tours
`final/p02_dslit_*`, `final/p04_cyl_*`, `final/p03_maxwell_*`. Figure `figs/r04_views_2d.jpg`.

### A4 — error: the first view fitted before the layout settled, by the bounding sphere — **fixed** [useful]

`fitTo()` fits the 8 corners of the region (box ∪ apparatus objects: v08's screen is wider than its box) into the
canvas less 44 px (toolbar) at the top, 26 px (hint) at the bottom and 10 px at the sides — the distance and a lateral
shift of the target, iterated; the `ResizeObserver` refits while the user has not moved the camera. Box corners on screen
as opened, before → after (tours and looks of this processing, same page size 1600 × 1000): v08 6 → 8, v09
«обычное пространство» 8 → 8, v09 «Томас» 6 → 8, v10 8 → 8, v11 4 → 8, v12 2 → 8, v13 6 → 8, v14 7 → 8, v15 8 → 8, v16 6 → 8,
v17 «Радуга» 4 → 8, v17 `near` 5 → 8, p01 8 → 8, p02 «Двойная щель» 4 → 8, p02 «Шар в 3D» 4 → 8, p03 8 → 8, p04 6 → 8. After a resize to
1280 × 800: 8 of 8; after the user's drag and a resize: the camera unchanged (`scene3d_checks.mjs fit`). Figure
`figs/r05_first_view.jpg`. A view along the long axis for v10 «улица» would be a view of its `viz.py` (not changed
here); the corner fit already fills the portrait canvas with it.

### A5 — error: everything unlit; spheres as discs, arrows flat, lines without width — **fixed** [useful]

Contract item 3. Own shaders, no vendored code: `LIT_*` (ambient + diffuse + specular from a view-space light; value
surfaces keep their colour where they face the viewer: 0.6 + 0.45 N·L), `SPH_*` (impostors), `WIDE_*` (each segment a
quad in screen space — four vertices carrying both ends, clipped at the near plane, with round ends; drawn as a child of
the data line, whose geometry, draw range and colours stay as before, so the key frames' fingerprint still reads them;
appended paths and tracks fill only their new segments), `PTS_*` (round points). The segments are deliberately not
instanced: software GL drew v15's 3 900 ray segments as instances in ≈ 50 ms and as plain quads in ≈ 1.6 ms.
`ArrowHelper` is replaced everywhere (incident beam, arrows, the craft's axes, spin and thrust, the observer's velocity,
the slice planes' normals) by a lit shaft and cone with the same methods. Verified: p03 «жидкость и пар», the atom
nearest the camera: rim/centre luminance 0.64 (a disc is 1.0) (`scene3d_checks.mjs lit`); figures
`figs/r06_lit.jpg` (p03 atoms, the review's A/B probe; v13 3d m=2 current arrows), `figs/r20_translucent.jpg`.
p03's 300–400 atoms now cost 2 triangles each instead of 520 (156 024 → 622 triangles in «Максвелл»).

### A6 — should-fix: pivot only on the box centre, zoom to the centre, F = the box — **partly fixed** [useful]

Done: `orbit.zoomToCursor = true` and `zoomSpeed = 2` (≈ 10 % per Chromium notch, ≈ 5 % per Firefox notch); a double
click puts the centre of rotation on the point under the pointer — a surface, a sphere (exact), a plane, or the volume's
densest point along the ray — keeping the direction of view (`scene3d_checks.mjs pivot`: p03, the target lands on the
clicked atom's surface, 0.170 from its centre, radius 0.170); **F** frames the visible content (the run's drawn paths,
bodies, meshes, the volume's non-empty box) from the current direction, **Shift+F** the whole region; the hint names
Shift + left drag (pan) and both keys. Deferred (STATUS): a «◎ к объекту» / «следить» control in the playgrounds — the
scene's `centerOn(p)` is ready, the control belongs in `playground.js` (another agent's file); a free-rotation mode
(would need vendoring three's `TrackballControls`/`ArcballControls`; the turntable is kept because it keeps the
world's up up, which the owner needs for orientation).

### A7 — should-fix: the camera jumped back when the run widened its box — **fixed** [useful]

`setBox` ignores a box equal to the current one, rebuilds the frame for a new one, and refits only while the user has not
moved the camera; otherwise it shows «Область расширилась — F: показать содержимое, Shift+F: всю область». A step back in
the history goes through the same `setBox` (env3d restores the header's box), so it does not move a moved camera either.
Verified with the review's probe on both versions (p01 «пифагорова задача», the user turns and zooms, the box grows from
±4 to ±16 au, then the history is scrolled back to 2 %): before, the camera's distance 13.69 → 82.56 (the default «Изо»)
→ 20.64 after the scroll; after, 7.551 → 7.551 → 7.551 (`response_checks/probe_ab.mjs boxjump`). `scene3d_checks.mjs box`:
a repeated and a four times wider box leave the camera exactly where the user put it; with the camera not moved, a
wider box refits. Figure `figs/r07_box_growth.jpg`.

### A8 — should-fix: near/far fixed at the fit — **fixed** [useful]

Every frame: far = d + 2.5 R, near = max(d − 2.5 R, far · 2·10⁻⁴), d the camera's distance to the region's centre,
R its half diagonal; `maxDistance` = 10 × the fitted distance (and ≥ 4 R), `minDistance` = 10⁻⁴ × the box size.
Verified: v08, 60 wheel notches out: d = 412, R = 12.3, near 381, far 443 — the scene drawn (`scene3d_checks.mjs clip`;
figure `figs/r08_zoom_out.jpg`).

### A9 — should-fix: labels through everything, misplaced with z up, sized in scene units — **fixed** [useful]

Labels are sprites with a size in CSS pixels (ticks 14 px, names and captions 16 px; `sizeAttenuation: false`, scale
kept on resize), depth-tested against solids (the selected plane's number excepted). The frame's ticks and names stand
on an outer edge of the box as seen now (an edge between a face toward the camera and one away from it; for an axis
running across the screen the lowest, for one running up it the leftmost), chosen every frame and pushed outward on
screen, so nothing inside the box covers them; labels that would overlap on screen are hidden (names first, then end
ticks, then middle ticks); no ticks along a thin axis (a 2-D slab). Object captions are placed along "up". The axis
names have no arrow (the ticks give the direction in every view). Verified: v13 1s, 14 frame labels, 12 shown, height
on screen / asked = 1.00, flags as stated, 0 overlaps (`scene3d_checks.mjs labels`). Figure `figs/r09_labels.jpg`
(v08 «С источника»: before, the far side's labels printed over the screen; p01: «z» on a vertical edge).

### A10 — should-fix: the volume's look depended on the length unit — **fixed** (differently from the proposal) [useful]

The proposal (opacity per fraction of the box diagonal) would still make the look depend on how much of the box a cloud
fills (a compact 1s against a spread 3d). Instead the density slider is now **τ, the optical depth of the volume's
densest line of sight along an axis of the region**: the march's step is weighted by 1 / (that column's ∫v² ds),
computed when a volume is first shown or the scale changes (not for each phase of the same volume: phases stay on one
scale). The slider means the same in every world and every box. Each world's start look is kept: τ₀ = the header's
`look.tau` if given, else its `look.density` (the old per-length value; 0.6 when absent) times the densest column of its
first volume — the look it was tuned to — held for the world's later volumes; v13/v14 set τ₀ = 4 in their view
(`orbitview.js`), so every state's cloud is visible (the review's example). Measured τ₀: v08 4.74, v09 0.30 (its faint
field, paths visible), v11 40 (the upper clamp; dense as before), v16 10.0, v17 `near` 0.32, p02 «Шар в 3D» 15.2,
v13/v14 4. Figure `figs/r10_volume_units.jpg` (v13 1s and v14 1S: before a dot, after a cloud).

### A11 — should-fix: full resolution and 160 steps on every frame — **fixed** [useful]

While the orbit controls move the camera (`start` … 180 ms after `end`) and a volume is visible, the frame is drawn at
half the pixel ratio and the march takes 56 steps; then once more at full quality. The step length is now one length
for every ray (the content box's diagonal / steps): a short ray takes fewer steps. The march is clipped to the box of
the voxels above the threshold (it skips the others anyway; recomputed when the threshold slider moves), and its first
step is offset per pixel (no banding at few steps). Verified: during a drag
`frameStats().quality` = 0.5, after it 1 (`scene3d_checks.mjs quality`); frame times in § Performance.

### A12 — should-fix: v10's floor drawn as zig-zag bands — **fixed** [useful]

Cause confirmed in the engine: the run colours each vertex of the panel by `raytrace._pattern` at q·(1 − 10⁻⁹), i.e. by
the cell between the vertex and the panel's centre; blending those across a cell made the saw-teeth.
`v10_fast_observer/web/view.js` (`flatCells`) re-meshes a panel body's grid with four vertices per cell, all coloured by
the cell's corner farthest from the centre (which is the cell's own colour by the same rule); the environment stores the
re-meshed message, so a key frame sets it again as drawn. Figure `figs/r12_v10_floor.jpg`.

### A13 — should-fix: p01's trails sampled per frame — **→ processed with UX-ui U2**

Not processed here (p01's files belong to the agent processing UX-ui U2). The shared code draws whatever points a world
sends, now with 2 px lines.

### A14 — nit: «Сверху» turned 90° against the slice window — **fixed** [useful]

A view along "up" takes its screen-up from the frame (−F): v08 «Сверху» shows z to the right and x up, as the window of
the plane y = 0 (`scene3d_checks.mjs views`; figure `figs/r14_top_view.jpg`).

### A15 — nit: no colour legend in the 3-D view — **fixed** [useful]

A colour bar at the lower right of the 3-D view, shown when something is drawn with the map (a volume, a slice with its
image, a target, a panel): the scale's name (амплитуда √(I/Iмакс), интенсивность I/Iмакс, логарифм), 0 or the log
floor, and «1 (пик)». (The slice windows' own drawing, `slices.js`, is outside this processing.)

### A16 — nit: Backspace removed the selected slice; Shift-drag not in the hint — **fixed** [useful]

Only Delete removes it (`env3d.js`); verified: Backspace leaves 1 plane, Delete removes it (`scene3d_checks.mjs keys`).
The hint: «ЛКМ — повернуть · ПКМ или Shift+ЛКМ — сдвинуть · колесо — к курсору · двойной щелчок — центр вращения ·
F — всё содержимое, Shift+F — вся область», and the slice keys only in worlds with slices.

### A17 — should-fix: layers panel rebuilt while playing; v13's superposition repainted voxel by voxel — **fixed** [useful]

`addLayer` calls `layersChanged()` only when a layer is new or its label or kind changed; `setLines` refills its
buffers in place; `setVectors` updates the glyphs in place when their number is kept; the per-mesh wireframe is gone;
v13/v14 clouds are kept as the 8-bit amplitudes the run sends and painted through a 256-entry table (a plain copy on the
amplitude scale) instead of two float passes per phase. Verified with the review's probe on both versions
(`probe_ab.mjs layerspanel`, 10 s of play, child-list changes of the panel): p01 «Солнце и Земля» 188 → 0, v16 «LG₀³»
18 → 0 (its density slider no longer replaced under the pointer), p02 «Шар в 3D» 2 → 1 (a layer the world adds: the set
changed); `scene3d_checks.mjs panel` (p01: 0 changes, the first
input never replaced); v13 superposition (`perf_ab.mjs`, 6 s of play, the view still), the main thread's script share:
0.94 / 0.98 before → 0.08 / 0.10 after (two runs each).

### A18 — nit: `preserveDrawingBuffer` for the snapshot only — **fixed** [useful]

Dropped; the 📷 button draws and reads in one task. Verified `getContextAttributes().preserveDrawingBuffer === false`
(`scene3d_checks.mjs keys`); `pixelAt` (tests) reads the same way.

### A19 — should-fix: coplanar faces z-fought — **fixed** [useful]

The volume no longer depth-tests its box faces (A1); the plate has `polygonOffset` (factor 1, units 2), so a slice plane
or an outline on its face is drawn over it; the slit outlines are lifted by 2·10⁻³ × the box size instead of 10⁻³
physics units. Verified with the review's probe on both versions (`probe_ab.mjs zfight`; figure `figs/r19_zfight.jpg`).

## UX-ui U1 (camera part) — **fixed** [useful]

U1's cause 1 (`setBox` → `view()`) and cause 3 (a step back re-applies the header's box, `setScene` refits when the box
differs) for the camera: `setBox` ignores an equal box and never moves a camera the user moved (A7); a step back goes
through it; `setScene` keeps the camera when the rebuilt scene has the box it was fitted to (unchanged). With this, the
playground's segment start may keep repeating its `box` (U1 cause 2, `playground.py`, another agent): it no longer moves
the camera. Verified: `probe_ab.mjs boxjump` (the scroll back) and `scene3d_checks.mjs box` (the repeated box). v04's 2-D
refit and the object list are not 3-D view code and are left to the agent processing the rest of U1.

## Performance (same environment, same time, software GL)

Software GL (SwiftShader) on a host shared with other agents' work: compare ratios only. `response_checks/perf_ab.mjs`,
each world twice, before and after interleaved, the world paused at the same moment, the default view; "full frame" = a
frame at full quality (6 frames, the GPU waited for); "turning" = the scene's frames per second while the mouse keeps
turning the view for 4 s (the test's mouse moves cap it near 30).

| world | full frame, ms: before | after | frames/s while turning: before | after |
|---|---|---|---|---|
| v13 «1s» | 376 / 480 | 79 / 88 | 8.4 / 9.1 | 30.0 / 29.7 |
| v13 «1s + 2p» (superposition) | 397 / 301 | 73 / 86 | 8.4 / 9.2 | 29.5 / 28.7 |
| v17 `near` | 381 / 342 | 85 / 103 | 9.9 / 8.8 | 24.5 / 26.6 |
| p03 «жидкость и пар» | 99 / 153 | 49 / 33 | 18.0 / 15.7 | 30.0 / 29.7 |
| v11 «узкие щели» | 200 / 223 | 31 / 47 | 10.5 / 10.4 | 29.8 / 29.8 |
| v16 «LG₀³» | 496 / 344 | 306 / 154 | 8.4 / 8.8 | 22.3 / 22.3 |

The three heaviest worlds the task named (v13, v17 `near`, p03 liquid) are 3–6× (v13), 3.4–4.5× (v17) and 2–4.6× (p03)
cheaper at full quality and turn 2–3.5× more smoothly. Where the gain comes from: the volume's step is one length for
every ray and the march is clipped to the voxels above the threshold (most rays are short or empty), the half-resolution
frames while turning, sphere impostors (2 triangles per atom instead of 520), no wireframe overlays. The single-sample
tours (`SUMMARY.md`) agree except for noise; one outlier was checked by repeated timing: v10 «Террелл», 9 × 5 frames,
median 39 / 88.7 ms before and 22.7 / 24.8 ms after (after a change made then: the depth-only twin of a **flat**
translucent surface — v10's floor — now serves only the volume's split, since a plane has one layer). Two costs found
on the way and removed: drawing lines as instanced quads (SwiftShader: 50 ms for v15's 3 900 segments, now 1.6 ms) and
drawing a flat translucent surface twice. (The table was measured before that last change, which only removes draws;
the regression and the key frames below ran on the final code.)

## Verification runs

- `visualizations/tests/browser/scene3d_checks.mjs` on a private server, final code: **all passed** (12 of 12: depth, planes,
  views, fit, box, clip, labels, lit, pivot, quality, panel, keys).
- `visualizations/tests/browser/keyframes.mjs`, all worlds, on a private server (`-e LFVIZ_PLAYGROUND_CKPT=6`):
  **all equal** on the final code (23 jobs: v01–v17, v02 vector, v09 in ordinary space, p01–p04; six cursors each, key frame
  against the rebuild from the record). An earlier run on intermediate code was also all equal.
- On the final code: `visualizations/tests/test_server.py`: 29 passed (21 at the start; other agents added tests meanwhile);
  `node --test visualizations/player/js/tests/*.mjs`: 1 passed;
  `lfphys/tests/test_licences.py` + `test_boundary.py`: 42 passed (the new test file carries its SPDX lines).
- Before/after: `response_checks/tour_ab.mjs` (the review's tour) for v08, v11, v12, p02 «Двойная щель», p04, p01
  «Солнце и Земля», v10 «Террелл», v15 «M87», v17 «Радуга», p03 «Максвелл», v09 «обычное пространство»;
  `look_ab.mjs` for every volume world; `probe_ab.mjs` for the review's probes; `perf_ab.mjs`. Every screenshot pair was
  looked at; `response_checks/SUMMARY.md` lists the numbers.
- Bugs found and fixed while processing (none reached the repository's history): the impostor quads were wound away
  from the eye (culled), `projectionMatrix` was not declared in the impostor's fragment shader, `screenOf` used the
  camera's matrix of the last frame right after a programmatic view.

## Changes for the integrator

No other file was edited. Proposed text, exact:

**1. `visualizations/RULES.md` §2 rule 10, append after "…the computed paths in both.":**

```
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
```

**2. `visualizations/RULES.md`, "3-D worlds", in the header's description**, replace
"`look` = the volume's starting `{density, threshold}`)" by:

```
`look` = the volume's starting `{tau?, threshold}`: τ the optical depth of the volume's densest line of sight along an axis
of the region (the density slider); without `tau` the player keeps the world's former look, `density` (the old value per
length unit, 0.6 when absent) times the densest column of the world's first volume)
```

and in the message table, row `box`, replace "the frame is redrawn, the objects keep their coordinates" by:

```
the frame is redrawn, the objects keep their coordinates; an equal box changes nothing; the camera is refitted only if the
experimenter has not moved it
```

**3. Owner guide `visualizations/README.md`**, the row «повернуть / сдвинуть / приблизить вид», replace its right cell by:

```
левая кнопка мыши — повернуть; правая (или Shift + левая) — сдвинуть; колесо — приблизить к точке под курсором; двойной щелчок — сделать точку под курсором центром вращения; F — показать всё нарисованное, Shift+F — всю область; кнопки «Изо», «Сбоку», «Сверху», «С источника», «С мишени» (у плоских миров — «Изо», «Сверху»/«Спереди», «С ребра»). Пока вид не двигали руками, он подстраивается под размер окна и под расширение области; после — остаётся, где его поставили
```

and in the row «выключить часть сцены» replace «у света — плотность и порог» by:

```
у света — плотность (оптическая толщина самого плотного луча вдоль оси области, одинаково во всех мирах) и порог; цветовая шкала — в правом нижнем углу 3D
```

and in the slice section add (where removing a slice is described, or as a row):

```
| убрать выбранный срез | клавиша Delete (Backspace срез не удаляет) или «убрать» в панели среза |
```

**4. `engine/STATUS.md`**, a new row (the next free V number; written here as V45):

```
| V45 | The 3-D view after review UX-3d (2026-11-04, `reviews/archive/2026-11-04_internal_UX-3d/RESPONSE.md`): (a) A6 rest: a «◎ к объекту» / «следить» control in the playgrounds (`playground.js`; the scene's `centerOn(p)` exists) and an optional free-rotation mode (needs three's Trackball/ArcballControls vendored, MIT); (b) the volume is split at the nearest translucent surface only: a second translucent layer inside a cloud is composited as if behind the cloud's front part (exact: depth peeling or weighted blended order-independent transparency); (c) the depth pass has no multisampling: at an object's silhouette the cloud may end one pixel early or late; (d) the headers' `look.density` (`viz.py` of v09, v11, v16, v17, p02, `server/lfviz/orbitals3d.py`) is now only the start look's legacy value: give each world `look.tau` (v13/v14 set τ = 4 in their view); (e) a view along the long axis for v10 «улица» (its `viz.py` views) |
```

**5. `lfphys/sources/dependencies.md`: no change** (no third-party code added).

**6. Registry** (`reviews/README.md`), when the folder is archived:

```
| `archive/2026-11-04_internal_UX-3d/` | internal (Claude Opus subagent) | the player's 3-D scenes as a user sees them: depth, flat objects, camera (shared `scene3d.js`, `env3d.js`, `orbitview.js`; every world with a 3-D view), 10 probes and 30 tours, Chromium | 2026-11-04 | `RESPONSE.md` (processed 2026-11-05: 17 of 19 fixed, A6 partly (rest → STATUS V45 a), A13 → UX-ui U2 — the volume ignored the depth of what is in front of it, slice planes and translucent surfaces were drawn in object order, views ignored "up", the first view was fitted before the layout settled, everything was unlit; now a depth-aware split volume march, opaque planes, nearest-layer translucency, lit solids and impostors, wide lines, views by up, corner fit kept until the user moves, pixel-size labels on outer edges, τ per densest column, adaptive quality; also UX-ui U1's camera part; `tests/browser/scene3d_checks.mjs`) |
```
