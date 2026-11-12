# Review UX-3d — the player's 3-D scenes as a user sees them: depth, flat objects, camera

**Status: awaiting processing.** Internal review (Claude Opus subagent), delivered 2026-11-04. The reviewer did not
write the code under review and does not process this review (`reviews/README.md`). Nothing in the engine was changed.

**Why.** The owner wrote on 2026-11-04 (verbatim, the relevant part):

> в 3D объекты спереди не всегда отображаются спереди, иногда перекрываются оюъектами сзади, как будто это псевдо 3D,
> - некоторые объекты в 3D отрисовываются как 2D, хотя должно быть полное 3D,
> - при кручении сцены в 3D часть сцен расположена некорректно и ею сложно управлять и крутить,
> … должно быть все понятно и удобно и подготовлено для визуализации и исследований

**Scope.** The shared 3-D player code `visualizations/player/js/scene3d.js`, `env3d.js`, `orbitview.js` (and how
`player.js`, `playground.js`, `imagewin.js` place the 3-D view), the vendored three.js r185.1 `OrbitControls`, and every
world that has a `.s3d-view`: v08–v17 and the playgrounds p01–p04 (v12 draws through v11's view; v01–v07 have no 3-D
view). Each finding is either **shared** (one fix in `scene3d.js` / `env3d.js` fixes many worlds) or **world** (one
world's server or view). Not reviewed: physics, the slice windows' 2-D drawing, the page layout outside the 3-D view
(another reviewer: `2026-11-04_internal_UX-ui`), launch errors (`2026-11-04_internal_UX-params`).

**Environment.** A private server `lf-uxa-srv` (image `light-funnel-viz`, CPU only, `LFPHYS_NO_GPU=1`, `engine/`
mounted read-only, runs in a scratch folder), port 8561, `--max-workers 2`; Playwright 1.58.2 in
`mcr.microsoft.com/playwright:v1.58.2-jammy` (containers `lf-uxa-pw-*`), Chromium with
`--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`, page 1600 × 1000 CSS px, device pixel
ratio 1, the player's default (light) theme. The browser drives the page as a user does: left-button drags, the
wheel, the right button, the keys and the view buttons. For measurement only, the scripts patch the served
`scene3d.js` **in the browser** (Playwright `page.route`) so that the scene's api also exposes its `camera`, `orbit`,
`renderer` and `scene`; probe objects are added through the scene's own api (`setSpheres`), and the A/B variants
change materials in the browser. All containers were stopped by name and checked gone.

**Software GL.** Swiftshader renders on the CPU. Its frame times are far longer than on a GPU, and only their
**ratios** mean anything; the frame-rate findings rest on those ratios and on what scales with pixels and steps.

**How to reproduce.** `scripts/` holds the scripts as run (`lib.mjs`, `tour.mjs`, `probe.mjs`, `lanes.sh`,
`montage.py`); `scripts/README.md` gives the commands. `tour.mjs <port> <viz> <preset> <tag>` starts a run, opens its
page, takes the default view, rotates (300 px right), tilts (220 px up), drives over the pole (700 px down), presses F,
zooms in (2500 px of wheel), presses F, zooms out (6000 px of wheel), pans (right button), presses every view button, and
measures the render (draw calls, triangles, ms per frame) and the frame rate while the mouse keeps rotating; it writes
`tour.json` (camera, box on screen, every layer's materials). `probe.mjs <port> <case>` runs the depth and flatness
probes named in the findings. The figures in this folder are montages of their screenshots (`fNN_*.jpg`, each under
300 KB).

## Summary

| severity | count | findings |
|---|---|---|
| error | 5 | A1–A5 |
| should-fix | 10 | A6–A13, A17, A19 |
| nit | 4 | A14–A16, A18 |

**The owner's three complaints are real and come from a few places in the shared code.**

1. *"Objects in front are drawn behind objects at the back, as if pseudo-3D."* Two mechanisms, both in
   `scene3d.js`:
   - the volume (light, clouds, waves) is ray-marched through the whole box without the depth buffer, so any opaque
     object inside the box punches a hole through the whole cloud, the part in front included (A1);
   - slice planes, panels and translucent bodies are drawn in a fixed order without writing depth: a slice plane hides
     the half of the cloud in front of it, and of two crossing planes one is drawn whole over the other (A2).
   Labels are drawn over everything (A9); coplanar faces z-fight (A19).
2. *"Some objects are drawn as 2-D."* Everything except v08/v11's plate is unlit. Spheres are flat discs that merge
   into blobs, arrows are flat triangles on 1-px shafts, lines have no thickness, and particles are squares (A5). In
   p02, p03 and p04 the 2-D worlds are also *shown* edge-on by default (A3).
3. *"When the scene is turned, parts of it are placed wrongly and it is hard to control."* The causes:
   - the view buttons ignore the world's "up", so in p02/p03/p04 «Изо» looks from below at 15° and «Сверху» looks from
     the side (A3);
   - the first view is fitted before a side window (a slice, v11/v12's plane, v17's sky) takes its place, so it opens
     cropped: 3–7 of the box's 8 corners are on screen (A4);
   - the orbit pivots only about the box's centre, the wheel zooms only toward it, and F fits the box, not what is in
     it (A6);
   - the camera snaps back whenever a run widens its box (A7);
   - zooming out ~20× blanks the view (A8).

In v13 (one page, the same camera, software GL) the ray-marched cloud takes 98 % of a frame's render time; that is what
makes turning a volume world sluggish (A11).

**Ranking by harm to the owner's use** (✱ = shared code: one fix covers all the worlds listed):

| rank | ID | severity | where | one line |
|---|---|---|---|---|
| 1 | A1 | error | ✱ `scene3d.js` volume | the cloud is cut away wherever any object stands, even an object behind it |
| 2 | A2 | error | ✱ `scene3d.js` planes/panels/meshes | a slice plane hides the cloud in front of it; crossing planes hide each other wholesale |
| 3 | A3 | error | ✱ `view()` + p02, p03, p04 headers | 2-D playgrounds open edge-on or from below; «Сверху» is not from above |
| 4 | A4 | error | ✱ fit on resize / `view()` | every world with a side window opens cropped; long boxes become slivers |
| 5 | A5 | error | ✱ materials | spheres = discs, arrows = flat triangles, lines 1 px, particles squares |
| 6 | A6 | should-fix | ✱ orbit controls | no pivot on an object, zoom only to the box centre, F = the box, not the content |
| 7 | A7 | should-fix | ✱ `setBox` | the camera jumps to «Изо» whenever the box grows (p01, v09 lab, v10) |
| 8 | A11 | should-fix | ✱ volume | full-resolution, 160-step march on every orbit event: ~98 % of a frame; ×3.4 on HiDPI |
| 9 | A9 | should-fix | ✱ labels | labels drawn through objects; wrong places with z up; too small or huge |
| 10 | A8 | should-fix | ✱ near/far | zoom out ~20× → empty view |
| 11 | A10 | should-fix | ✱ volume opacity | the same density means different things per world; v13 1s nearly invisible |
| 12 | A12 | should-fix | v10 | the floor's checkerboard drawn as zig-zag bands |
| 13 | A13 | should-fix | p01 | trails sampled per frame: orbits drawn as polygons with chords |
| 14 | A17 | should-fix | ✱ `addLayer`, `paintVolume` | the layers panel is rebuilt while the run plays (a dragged slider is replaced); v13's superposition: 76 % of the main thread in scripts while turning |
| 15 | A19 | should-fix | ✱ plate / volume faces | coplanar faces z-fight: a dot grid over v08's screen, broken slit outlines |
| 16 | A14 | nit | ✱ `view()` | «Сверху» turned 90° against the slice window of the same plane |
| 17 | A15 | nit | ✱ | no colour legend in the 3-D view |
| 18 | A16 | nit | ✱ keys | Backspace removes the selected slice from anywhere; Shift-drag pan not in the hint |
| 19 | A18 | nit | ✱ renderer | `preserveDrawingBuffer` kept for every frame for the snapshot only |

## Findings

Line numbers are of the files as of 2026-11-04 (`git` HEAD a55d0fc plus the working tree the server mounted).

### A1 — error, shared: the ray-marched volume ignores what is in front of it; anything opaque inside the box cuts a hole through the whole cloud

**Worlds.** Every world with a volume layer: v08 (light), v09 (field of rotations), v11/v12 (wave |ψ|²), v13/v14
(cloud), v16 (|E|²), v17 near field, p02 3-D (wave). Seen worst in p02 «Шар в 3D», v17 `near`, v11/v12 (plate,
tracks), v13/v14 with the current arrows.

**What the user sees.** An object *behind* the cloud is drawn crisp and in front of it, with the cloud cut away along
its outline. In p02 `ball_3d` the potential ball sits behind the wave packet (the camera is at physics x ≈ −105, the
ball at x ≈ +5, the packet at x ≈ −3), yet the ball covers the packet and the packet ends sharply at the ball's edge
(`f01_volume_depth_real.jpg`, first two panels). In v11 the wave packet on the source side ends sharply at the
silhouette of the plate *behind* it, while the Bohm tracks (lines) run on over the plate (third panel). In v17 `near`
the near field is cut along every line of the polar plot's wireframe (fourth panel). The probe (`probe.mjs volsphere`, `f02_volume_depth_probe.jpg`): v13 2p_z with the density
slider at 80 %; two opaque probe spheres on the lines of sight through the two lobes' densest points, one 0.15 box
sizes *in front of* the right lobe (the larger, nearer sphere) and one 0.15 *behind* the left lobe (the smaller one). At
the back sphere's pixel the cloud alone is RGB (92, 28, 104); with the sphere there it is (51, 255, 77), **exactly
the sphere's own colour with no cloud at all**: the lobe in front of it is gone, and the two spheres look equally
"in front".

**Cause.** `scene3d.js:118-144` (`VOL_VERT`/`VOL_FRAG`) marches each ray from the camera through the whole box
(`a0 … a1`, the box's entry and exit) and never reads the depth buffer. The volume is drawn as the box's back faces
(`setVolume`, `scene3d.js:612-619`: `side: BackSide, transparent, depthWrite: false, renderOrder 2`). Its fragments
therefore pass the depth test only where nothing opaque lies between the camera and the box's *far* face. Any
depth-writing object inside the box — the plate (v08, v11), the target and screen, arrows and cones
(`setVectors` 662-691, `ArrowHelper`), spheres (`setSpheres` 1072-1095, `setMarks`, `setBody`), paths and tracks (lines
write depth), and even the faint wireframe overlay of a translucent mesh (`setMesh` 473: `LineBasicMaterial`
transparent 0.12 but `depthWrite` left on) — removes the *whole* column of the volume at its pixels, the part in front
of it included.

**Fix (one place, `scene3d.js`).** Give the march the scene's depth:
1. render everything but the volume into a `WebGLRenderTarget` with a `DepthTexture` (or a depth-only pre-pass);
2. in `VOL_FRAG` convert the depth at `gl_FragCoord` to a distance along the ray and end the march at
   `min(a1, t_scene)`; draw the volume with `depthTest: false` (its box faces must not be culled by objects inside);
3. composite. The volume then covers what is behind it and stays behind what is in front.
Cost: the (light) geometry is drawn twice; the march is unchanged or shorter. Until then, at least turn off
`depthWrite` on the wireframe overlays of translucent meshes (`setMesh` 473), which cut the largest holes (p02 ball,
p01 ergosphere, v10 bodies).

### A2 — error, shared: slice planes, panels and translucent meshes are drawn in object order, not by depth

**Worlds.** Slice planes: v08, v09, v13, v14, v16, v17 near (every world with `planes.max > 0`). Panels: v11/v12 (the
wave panel, off by default), p02 2-D and p04 (the field panels). Translucent meshes: v10 (bodies 0.35, floor 0.5,
static 0.85), v15 (disk 0.55, ergosphere 0.18), v16 (helix 0.62, plate, rotor), v17 (polar plots 0.55), p01 (ergosphere
0.18), p02 (potentials 0.35, detectors 0.25, flux planes 0.20), p04 (obstacles 0.85), v11 (observer box 0.62).

**What the user sees.**
- *A slice plane hides the volume in front of it.* v13 2p_z with its default plane y = 0: with the plane on, the upper
  halves of both lobes — the halves between the camera and the plane — vanish; the plane reads as an opaque sheet laid
  over the cloud (`f03_plane_hides_volume.jpg`, `probe.mjs planevol`). The same in v08 (the light above the default
  plane y = 0), v09 (the field above βy = 0), v16, v17.
- *Two planes that cross: one is drawn whole over the other.* v13 1s with planes y = 0 and x = 0 (as «＋ Срез» adds
  them), recoloured flat for the measurement: plane 2 is drawn over all of plane 1, including the half of plane 1 that
  lies in front of it; with depth writing on, plane 1 shows on 17 664 px instead of 2 281 px in the same view — **87 %
  of what should be visible of plane 1 is hidden** (`f04_two_planes.jpg`, `probe.mjs twoplanes`).
- *Translucent bodies are ordered per object, not per pixel* (from the code; not isolated by a probe): three.js sorts
  transparent objects by the distance of their origins, so intersecting or nested ones are wrong over part of the view
  and swap as it turns — v10's bodies and the floor, v15's disk through the ergosphere, p02's walls, detectors and flux
  planes (`setMesh` gives absolute vertices, so all of them have the origin as their position), v17's polar plot around
  the drop; within one mesh (v16's helices) the triangles are drawn in index order.
- *The volume paints over a translucent surface in front of it*: v17 `near`'s field over the polar plot (`f01`, right),
  v11/v12's wave over its panel when the panel is switched on.

**Cause.**
- Planes: `planeMaterial`, `scene3d.js:695-704` (`transparent: true, depthWrite: false`, opacity 0.92) with
  `rect.renderOrder = 3` (709): always drawn after the volume (`renderOrder 2`) and after every other transparent object,
  and never written to the depth buffer, so they neither hide each other nor stop the volume.
- Panels: `panelObj`, 936-948 (`transparent`, `depthWrite: false`, renderOrder 0): drawn *before* the volume, which then
  paints its whole column over the panel.
- Meshes: `setMesh` 469 (`depthWrite: opacity >= 1`, `side: DoubleSide`), `boxObj` 532, `incident` 311, `sphere` 342.

**Fix.**
- Draw slice-plane images opaque (opacity 1, `depthWrite: true`, `transparent: false`; keep the dimming of the planes not
  pointed at as a darker colour, not as alpha). Crossing planes are then right at every pixel (`f04`, right panel: the
  same scene with `depthWrite` on), and with A1 the volume in front of a plane is drawn over it.
- Panels: `depthWrite: true` with `alphaTest` (≈ 0.05) for the faded weak values, so that what is behind shows through
  the transparent parts only.
- Translucent meshes: write depth for the near surface (a depth-only pre-pass, then the colour pass with
  `depthFunc: LessEqualDepth`), or render them opaque and lit (A5); three's two-pass back/front rendering of
  `DoubleSide` transparent materials helps only convex shapes (it does not fix v16's helices).

### A3 — error, shared + p02, p03, p04: the view buttons and the default «Изо» ignore the scene's "up"; 2-D worlds open edge-on

**Worlds.** Every world whose header sets `up` but no `views`: p02 (2-D and 3-D presets), p03 (3-D presets; its 2-D
presets keep y up but have the same problem through their plane), p04. p01, v15, v17 define their own views and are
not affected.

**What the user sees.**
- p02 `double_slit` (a 2-D world in the plane z = 0, `up` = z): «Изо» looks at the plane from **below**, 15° under it,
  along the beam (the camera at physics (−0.88, 0.37, −0.26) × distance); «Сверху» and «Сбоку» both show the plane
  edge-on as a thin strip; «С источника» / «С мишени» look along z, i.e. from above (`f05_views_ignore_up.jpg`,
  `p02_dslit` tour).
- p03 `maxwell` (2-D gas in the x–y plane, `up` = y): «Изо» shows the gas as a thin slab seen 15° from its plane
  (`f05`, `p03_maxwell` tour). p03 `liquid_vapour` (3-D, `up` = z): the axis label «z, нм →» points right on the
  vertical edge.
- p04 (2-D flow in z = 0, `up` = z): the same as p02 (`p04_*` tours).

**Cause.** `view()`, `scene3d.js:867-892`: the preset directions `dirs` (871) are fixed vectors in three.js
coordinates written for y-up (`top: [0.001, 1, 0]` is "along three's Y"), and `VIEWS` (170-172) names them "side",
"top", "beam". `setUp` (858-864) turns the camera's up to the world's `up` but the directions are not turned with it.
p02 (`viz.py:1079`), p03 (`viz.py:908`) and p04 (`viz.py:913`) set `up` and give no `views`.

**Fix.** In `view()`, rotate the preset direction by the rotation that takes three's Y to `camera.up`
(`d.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(Y, camera.up))`), so that "top" is always along `up`; for
2-D worlds (p02 2-D, p03 2-D, p04) give `views` whose «Изо» looks down on the plane from 55–65° with x to the right (as
the slice window shows it), and «Сверху» straight down with x right and y up.

### A4 — error, shared: the first view is fitted before the layout settles, and by the bounding sphere: scenes open cropped or tiny

**Worlds.** Every world whose side window appears after the first frame: the slice windows (v08, v09, v13, v14, v16,
v17 `near`), v17's sky image (`rainbow`: 4 of 8 corners), v11/v12's plane window, p02/p04's field window. (v10 and v15, whose camera window is there from the start,
open fitted: 8 of 8 corners.) Every elongated box: tiny content.

**What the user sees.** At the first frame the 3-D canvas is wide; when the first slice (or the camera image) arrives,
the window takes 40–50 % of the centre and the canvas becomes a narrow portrait (470–564 × ~900 px at a 1600-px page),
but the camera keeps the distance fitted for the wide canvas. Box corners on screen in the view as opened (of 8): v08
6 (the screen and the target are cut; F moves the camera from 93 to 146), v09 6, v11 4, v12 3, p02 4, p04 6
(`f06_first_view_cropped.jpg`; the full table below). After F every box fits, but by its bounding sphere, so a box
fills 60–70 % of the narrower side (v08 after F: 71 %); a long box in the portrait canvas is a sliver (v10 «улица», 32 × 18 × 186 m: 87 % of
the width, 11 % of the height).

**Cause.** `scene3d.js:204-210`: the `ResizeObserver` fits the view only once (`if (S.box && !S.fitted)`); `setScene`
(577) fits when the box changes. `view()` (884-886) fits the box's bounding sphere in the narrower field of view.
`chrome.css:170-171` gives the windows `flex: 0 0 min(40%, 420px)` / `min(50%, 640px)`.

**Fix.** Refit on every resize **until the user moves the camera** (set a flag on the orbit controls' `start` event,
clear it in `view()`); when the user has moved it, keep the direction and target and only update the aspect. Fit the
box's eight corners to the frustum (the distance at which each projected corner is inside both half-angles), not its
bounding sphere (a sphere around a box, with a 1.12 margin, leaves 30–40 % of the narrow side empty); for long boxes give the world a view along the long axis (v10 «улица»).

### A5 — error, shared: almost everything is drawn unlit; spheres look like discs, arrows like flat triangles, lines have no thickness

**Worlds.** All. Worst: p03 (atoms), p01 (bodies), p02 (Bohm points), v11/v12 (particles as squares), v13/v14 and v08
(current cones; v08's are off by default), v09 (craft, triads), v17/v09 (the sphere as a wire globe)
(`f07_flat_vs_lit.jpg`, `f16_flat_glyphs.jpg`).

**What the user sees.**
- Spheres are flat discs of one colour. Atoms of one species that touch on screen merge into one blob: p03
  `liquid_vapour`'s liquid slab is a single blue shape; the same atoms drawn lit (A/B, only the material changed) show
  each atom and the slab's depth (`f07_flat_vs_lit.jpg`, `probe.mjs flat`).
- Arrows (vector glyphs, `ArrowHelper`) are a one-pixel shaft and an unshaded cone: a cone seen from its side is a
  flat triangle; its direction toward or away from the viewer cannot be read.
- Paths, trails, tracks, orbits and rays are one-pixel lines whatever the distance (WebGL ignores `linewidth`); near
  and far lines look the same.
- Particles (`setPoints`, v11/v12) are screen-aligned squares.
- The sphere object (`sphere()`: v09's light sphere, v17's drop) is a wire globe whose near and far meridians are equally
  bright: front and back cannot be told apart (the Necker-cube effect).
Only the plate (`MeshStandardMaterial`, `scene3d.js:270`) uses the scene's lights (ambient 0.7 + directional 1.6,
184-185).

**Cause.** `MeshBasicMaterial` in `point` 348, `setMarks` 406, `setBody` 432, `setObserver` 506, `setVectors` 669,
`setMesh` 469, `setSpheres` 1077, `boxObj` 532, `imagePlane` 286; `LineBasicMaterial` in `appendPath` 363, `addTriads`
401, `appendTracks` 991, `setLines` 1043, `sphere` 331; `PointsMaterial` in `setPoints` 1053; `ArrowHelper` in
`incident` 314, `arrowObj` 413, `setBody` 433-435, `ensurePlane` 711.

**Fix.** Lit materials (`MeshStandardMaterial` or `MeshLambertMaterial`, `vertexColors`/instance colours kept) for
spheres, cones, bodies, meshes of solid objects, with a light that moves with the camera (a `DirectionalLight` added to
the camera) so that they stay shaded from every side; arrows as a lit cylinder + cone; points as round shaded impostors
(a small point-sprite shader: discard outside the disc, shade by the sphere normal from `gl_PointCoord`); paths and
trails as screen-space thick lines (`Line2`/`LineMaterial` from three's `examples/jsm/lines`, MIT, vendored next to
`OrbitControls`) or tubes for short paths, optionally fading with distance; the sphere object with a faint lit surface
that writes depth so that its far half is hidden. Data surfaces (slices, panels, targets, images) stay unlit — their
colour is the value. Keep these as intended 2-D: slice planes, panels, the target/screen images, the incident wave's
sheets (a picture of plane wave fronts), labels.

### A6 — should-fix, shared: the camera turns about the box's centre only; zoom goes to the centre; F shows the box, not the content

**Worlds.** All; worst where the content is small or off-centre in its box: p01 (`pythagorean`: the box grows to 32 au
while the bound pair moves within ~2 au; `kerr_orbits`: a box of 64 G M/c² around a hole of radius 1.4), v10 (bodies
along a 186-m street), v09 lab (the path fills a part of the box), p04 (the obstacle sits near the inlet, the wheel
zooms into the empty middle of the channel: `f08`, right).

**What the user sees.** To look at a body or a detail away from the centre, the user must pan (right button), zoom, pan
again; the wheel zooms toward the box's centre, not toward the pointer, and stops there (a multiplicative dolly never
crosses the target). «F» returns to the box's iso view (`f08_content_small_in_box.jpg`: p01 pythagorean, p01 Kerr,
v10 city). There is no "centre on this object", no "follow the selected body" in the playgrounds, no double-click to set
the pivot. Over the pole the image spins about the view axis (`OrbitControls` clamps the polar angle; `3_pole.jpg` of
every tour). A wheel notch moves the camera 5 % in Chromium (measured: 25 notches, distance × 0.277 = 0.95²⁵); Firefox
reports lines, which `OrbitControls` turns into 2.4 % per notch. Shift + left drag pans (checked in p04: the target
moves, the distance stays; `scripts/shiftpan.mjs`), but nothing on the page says so. On a touchpad two-finger
scrolling zooms and never turns or pans (from the vendored `OrbitControls.js`; not tested on a real touchpad).

**Cause.** `scene3d.js:187-188` (default `OrbitControls`: `zoomToCursor = false`, `minDistance = 0`,
`maxDistance = ∞`), `view()` 890 (`orbit.target.copy(c)`, the box's centre), the key F → `view("iso")` (913).

**Fix.** `orbit.zoomToCursor = true` (three r185 has it); double-click → raycast the visible meshes, spheres and planes
(and, for a volume, the densest point along the ray from `sampleVolume`) → move the orbit target there; F → fit the
visible content (the union of the visible layers' bounding boxes, the spheres' positions), Shift+F → the whole box; in
the playgrounds a «◎» button "centre on the selected object" and a "follow" toggle; `orbit.zoomSpeed` ≈ 2 (Firefox,
touchpads); an optional free-rotation mode without the pole (three's `TrackballControls`/`ArcballControls`, MIT) for
inspecting a cloud from every side. Mention Shift + left drag (pan on a touchpad) in the hint.

### A7 — should-fix, shared: the camera jumps back to the default view whenever the run widens its box, and when the history is scrubbed across such a change

**Worlds.** p01 (Newton: the box doubles as bodies go out, `viz.py:509-513`; PN, Kerr: 894, 1069), v09 «обычное
пространство» (`viz.py:446-453`), v10 (`viz.py:305-319`).

**What the user sees.** The user turns and zooms to look at something; the run emits `box`; the view snaps back to
«Изо» at the new box's distance. Measured in p01 `pythagorean` (`probe.mjs boxjump`, `f09_camera_reset_on_box.jpg`):
the user's camera at distance 13.7 from the centre, turned to (−4.0, −5.2, 12.0); about 12 s later the box grows from ±4 to
±16 au and the camera is at (41.5, −58.1, −41.5), distance 82.6 — the default «Изо». Scrolling the time cursor back
across that moment snaps it again (env3d restores the header's box). This is the "controls fight the scene" the owner
describes.

**Cause.** `setBox`, `scene3d.js:582-588`, ends with `view(S.lastView || "iso")`; `env3d.js:194` calls `setBox` on a
key-frame restore.

**Fix.** In `setBox`, rebuild the frame and update near/far, but move the camera only if the user has not moved it since
the last fit (the flag of A4); otherwise show a small notice "область расширилась — F: показать всё".

### A8 — should-fix, shared: near and far are fixed when the view is fitted; zooming out ~20× blanks the scene

**What the user sees.** v08: 60 wheel notches out (×21.7 in distance) and the 3-D view is empty — the camera is 3177
units away, `far` is 2927 (`f10_zoom_out_blank.jpg`). The same in p01 (distance 1792 > far 1651). On a touchpad, many
small wheel events reach this quickly. Zooming in very close to a small object (p01 Kerr) brings `near` (fit
distance / 200) close to it.

**Cause.** `view()`, `scene3d.js:889`: `camera.near = dist / 200; camera.far = dist * 20` only when a view is fitted;
`orbit.maxDistance = ∞`.

**Fix.** On every orbit `change`, set `near`/`far` from the current distance and the box's bounding radius
(`far = d + 2R`, `near = max(d − 2R, d / 1000)`); set `orbit.maxDistance` ≈ 8 × the fitted distance and `minDistance`
≈ 1e-3 × the box size.


### A9 — should-fix, shared: labels are drawn through everything, sit in the wrong place when "up" is not y, and scale with the zoom

**What the user sees.**
- Every label (axis names and ticks, object labels such as «падающая волна (задана)», «детектор: θ = 180°», the slice
  planes' numbers, arrow captions) shows through opaque objects: in v08 «С источника» the far side's axis labels and
  the incident wave's caption are printed over the screen, which hides them (`f11_labels.jpg`, `v08_double` tour);
  v11's detector caption shows through the plate when the camera is behind it.
- In worlds with `up` ≠ y the frame's labels are placed for a y-up box: «z, а.е. →» stands beside a **vertical** edge
  with an arrow pointing right (p01, p02, p03 3-D, p04); «y, …» lands in the middle of the picture (p01
  `sun_earth`, `f11`).
- Labels are sprites sized in scene units: at the fitted distance the tick numbers are 8–9 px high (hard to read in
  v09, v13, v15), and after zooming in they grow to tens of pixels and cover the scene (p01 zoom-in: «y, а.е.» over the
  orbit). Tick labels of two axes overlap at the box's corner («-16 -16», «-2,97 -2,97»); on a short edge they pile up
  into one blot (p04: the five z ticks on its 0.18-m edge, `f11`).

**Cause.** `labelSprite`, `scene3d.js:107-116` (`depthTest: false`, `renderOrder = 10`, size in scene units with size
attenuation); `buildFrame`, 232-253 (positions written for y up and z to the right: 241-251).

**Fix.** `depthTest: true` for frame and object labels (keep `false` only for the selected plane's number and the
gizmo); `sizeAttenuation: false` with a size in pixels (e.g. 12 px for ticks, 14 px for axis names); place the axis
names along the box's edges chosen in the camera's `up` frame (the edge whose screen direction matches the axis), with
the arrow only on the axis that is horizontal on screen; skip a tick label that would overlap another (screen-space
test).

### A10 — should-fix, shared: the volume's look depends on the world's length unit; the same slider is 16× denser in one world than in another

**What the user sees.** v13 «1s» opens with an almost invisible cloud: a small glow on the slice plane in a dark box,
while its slice window shows a cloud filling a third of the plane (`f12_volume_units.jpg`, first two panels). With
the slice hidden, the cloud alone is a faint dot at the default look (density 0.9, `probe.mjs faint`); only with the
density slider at its top does the 1s cloud appear as a cloud (last two panels). v14 «1S» (femtometres) is fainter
still. The same slider position means a different optical depth in every world.

**Cause.** `VOL_FRAG`, `scene3d.js:130,139`: the opacity per step is `1 − exp(−v²·uDensity·dt)` with `dt` the step in
**scene units** (the box's length unit). With 160 steps, `dt` = box diagonal / 160: 0.064 Å in v13 1s (box ±2.97 Å),
0.34 µm in v08, 0.022 in v09 (box ±1 in β), 0.52 M in v15. The worlds compensate by hand (`look.density` 0.35…3.0 in
v09, v11, v13/v14, v16, v17, p02), which cannot follow a change of box within a world (by the code: v13's box is
sized per state — ±3.0 Å for 1s, ±14.3 Å for 3d, more for n = 10 — with one `look`).

**Fix.** Use the step as a fraction of the box's diagonal (`dt / length(uMax − uMin)`), so that `uDensity` is an
optical depth per box; set the worlds' `look.density` again once (one value per world, then the slider means the same
everywhere).

### A11 — should-fix, shared: the volume is marched at full resolution and 160 steps on every frame, also while the view is being turned

**What the user sees (measured in software GL; ratios only).** In one page with one camera (`probe.mjs volcost`, v13
1s, 564 × 917 px): 836 ms per frame with the cloud, 15 ms without it — the cloud is 98 % of the frame; 64 steps instead
of 160 take 477 ms. At pixel ratio 2 (1128 × 1834 px, a HiDPI laptop: the renderer uses `min(devicePixelRatio, 2)`,
`scene3d.js:182`) the cloud costs 2835 ms, 3.4× more. Across the tours, the volume worlds draw the scene 4–10 times a
second while the mouse keeps turning (v08 9.2, v11 8.9, v12 8.0, p02 3-D 9.5, v16 4.3), against 20–29 for light scenes
(v09 lab 22, p01 `pythagorean` 29, p04 27) on the same software GL (the table under *Measurements*). Heavy plain
geometry costs too (p03's 300–400 atoms at 520 triangles each: 4.5–6 draws per second), so the sphere tessellation of
`setSpheres` (20 × 14) is also worth an instanced low-poly or impostor version (A5).

**Cause.** `VOL_FRAG` 132-142 (`uSteps` 160, `setVolume` 616), `draw()` 197-201 renders the full scene for every orbit
`change` event; nothing lowers the cost while the user interacts.

**Fix.** Adaptive quality: on the orbit controls' `start`, render at pixel ratio 0.5–1 and 48–64 steps; on `end` (and
when idle 150 ms) render once more at full quality. Add a per-pixel random offset of the first step (jitter) to remove
the banding that fewer steps produce. Skip empty space (stop when the ray leaves a precomputed bounding box of
voxels above the threshold).

### A12 — should-fix, world v10: the floor's checkerboard is drawn as diagonal zig-zag stripes

**What the user sees.** In v10 «Террелл» and «улица» the floor «пол (в покое)» is a field of dark and light
saw-tooth bands that run diagonally and change with the view; the checkerboard that the camera image shows is not
visible in 3-D (`f13_v10_floor.jpg`).

**Cause.** `v10_fast_observer/viz.py:190-204` (`mesh_of`, a panel): the vertices are spaced exactly one checker cell
apart (`ku = 2·round(hu/cell) + 1`), and each vertex takes the temperature at its own point
(`RT.surface_temperature`, 203), which lies on a cell boundary; the colours are interpolated across each two-triangle
quad by the player (`setMesh`, vertex colours), which turns the checker into saw-teeth.

**Fix.** Build the panel's mesh with vertices at cell corners duplicated per cell and the colour taken at the cell's
centre (flat colour per quad), or with 2–4 vertices per cell; or send the pattern as a texture.

### A13 — should-fix, world p01: a trail is one point per drawn frame, so fast orbits are drawn as polygons with chords

**What the user sees.** p01 «Солнце и Земля»: the Earth's trail is a circle crossed by a polygon of straight chords
(≈ 10 sides) (`f14_p01_trail_chords.jpg`, `p01_sun_earth` tour).

**Cause.** `p01_gravity/viz.py:491-495`: `advance()` appends one trail point per call, i.e. per frame, whatever the
distance travelled in that frame; at the page's 1 year per second a ten-sided polygon means ~36° of orbit between two
points (the smooth parts of the trail come from slower stretches of the run).
The view draws them as straight segments (`web/view.js:43-57` → `setLines`).

**Fix.** Sample the trail by arc length or by angle (e.g. a point every 2° of turning or every 1/200 of the box), taken
from the integrator's dense output within the frame; or at least several points per frame when the step covers a
large angle.

### A14 — nit, shared: «Сверху» turns the picture by 90° against the slice window of the same plane

v08: the window «Срез 1: y = 0» shows z to the right and x up; «Сверху» shows the same plane with z running **down**
the screen (`f15_top_view.jpg`). Cause: `dirs.top = [0.001, 1, 0]` (`scene3d.js:871`), a tilt toward +X in three
coordinates. Fix: for "top", set the tilt so that the scene's depth axis runs to the right (the window's convention),
e.g. a tilt toward three's −Z, or set `camera.up` temporarily.

### A15 — nit, shared: no colour legend in the 3-D view

The volume, the slice planes, the panels and the targets share one colour map and one scale (амплитуда /
интенсивность / логарифм with its floor), but the 3-D view shows neither the map nor what its ends mean; the slice
windows do not either. Fix: a small colour bar in a corner of `.s3d-view` with the scale's name, 0, the peak and, for
the log scale, the floor.

### A16 — nit, shared: keys and hints

- Backspace removes the selected slice plane from anywhere on the page outside an input (`env3d.js:167-170`), a key
  users press by habit; keep Delete only, or ask.
- The hint (`scene3d.js:176`) does not mention Shift + left drag (pan on a touchpad without a right button) or that F
  resets the camera.

### A17 — should-fix, shared: replacing a layer rebuilds its whole geometry and the panel «Слои сцены» while the run plays

**What the user sees.** While a world plays, the panel «Слои сцены» is rebuilt again and again (`probe.mjs
layerspanel`, a `MutationObserver` on the panel for 10 s of play): p01 `sun_earth` 40 child-list changes, its inputs
replaced; v16 `lg3` 7 changes, its inputs replaced — including the light volume's density and threshold sliders, so a
drag on them is cut off under the pointer; p02 `ball_3d` 0 (its layers are updated in place). The 3-D view's main-thread script
time while the user turns the view and data arrive reaches 30–32 % in v16 and v12 and **76 % in v13's superposition**
(`super_1s2p`: the cloud changes phase as the time runs, and each phase is repainted voxel by voxel in JavaScript; CDP
`ScriptDuration`, the table under *Measurements*).

**Cause.** `addLayer`, `scene3d.js:213-222`, calls `layersChanged()` → `env3d.js:48-74` `drawLayers()` rebuilds the
panel's DOM for every layer set again. Layers set again on every data message: p01's trails (`setLines`, a new
`BufferGeometry` and `LineSegments` each time, `p01_gravity/web/view.js:43-57`), v16's equiphase sheets (`setMesh` per
phase bin, including a new `WireframeGeometry`, `scene3d.js:473`), p02/p04 meshes, v13/v14 current arrows
(`setVectors` per phase, `orbitview.js:50-57`), v10's meshes. A new phase of a cloud goes through `updateVolume` →
`paintVolume` (`scene3d.js:627-639`): `transfer()` for each of 96³ ≈ 885 000 voxels on the main thread, then a
885-KB texture upload.

**Fix.** Call `layersChanged()` only when the set of layers (ids, labels) changes, not when a layer's object is replaced;
update geometry in place (resize a preallocated `BufferAttribute`, `setDrawRange`) instead of building a new object;
build a mesh's wireframe once per topology, not per frame; apply the scale (sqrt / lin / log) to the volume in the
shader (one uniform) instead of repainting every voxel, so that a new phase is only a texture upload.

### A18 — nit, shared: `preserveDrawingBuffer: true` for the snapshot only

`scene3d.js:180` keeps the drawing buffer for every frame; the 📷 button (928) already calls `draw()` right before
`toDataURL`, which works without it. On integrated and mobile GPUs a preserved buffer costs a copy per frame. Drop it
(or set it only around the snapshot).

### A19 — should-fix, shared (seen in v08): coplanar surfaces z-fight — the light over the screen turns into a dot grid, the slit outlines break up

**What the user sees.** v08 seen from behind the screen (camera at z > 0 looking back at it through the light, the
target and the slice hidden; `probe.mjs zfight`, `f17_zfight.jpg`): where the light lies over the screen it is
covered by a regular grid of dark dots, and the outlines of the slits are broken into dashes. With the screen hidden the
light is smooth; with the light hidden the screen is uniform: the pattern exists only where both meet.

**Cause.** The screen's face toward +z lies exactly on the box's face z = 0 (`plate`, `scene3d.js:272-273`: the
extrusion spans `[z − thick, z]`; v08's box starts at z = 0), and the volume is drawn on the box's back faces with the
depth test (`setVolume` 612-619): the two coplanar faces win pixel by pixel. The slit outlines are lifted by a fixed
`1e-3` physics units (276), which in µm is about the depth buffer's resolution at the fitted distance.

**Fix.** With A1's depth-aware march the volume no longer depth-tests its box faces, which removes the dot grid. Give
the plate's material `polygonOffset` (factor 1, units 1) and draw the outlines with an offset relative to the box
size (or with `polygonOffset` on the plate and the outlines on top), not a fixed physics length.

## Every layer type of the scene: how it is drawn, its depth, and whether its flatness is intended

From `scene3d.js` and the materials each tour reported (`tour.json` → `layers[].parts`).

| layer (function, line) | drawn as | depth test / write | looks | verdict |
|---|---|---|---|---|
| the box frame (`buildFrame` 232) | `Box3Helper`, 1-px lines | yes / yes | lines | fine (there is no grid) |
| axis names, ticks, object captions (`labelSprite` 107) | sprites, `renderOrder 10` | **no** / no | text over everything, sized in scene units | A9 |
| plate with holes (`plate` 256) | extruded solid, **lit**, two-sided | yes / yes | 3-D | fine — the only lit object |
| target, screen, waist disk (`imagePlane` 282, `disk` 319) | textured quad, unlit | yes / yes | an image | intended (a detector shows its picture) |
| incident wave (`incident` 305) | 4–25 sheets at opacity 0.06, `ArrowHelper`, caption | yes / no | wave fronts | intended |
| sphere object (`sphere` 329: v09's light, v17's drop) | 19 lines at 0.35 + a faint back-face surface | yes / lines yes, surface no | wire globe, near and far halves alike | A5 |
| point (`point` 346) | small unlit sphere + caption | yes / yes | disc | A5 |
| box object (`boxObj` 529: v11's observer) | translucent box + edges | yes / no | — | A2 |
| panel (`panelObj` 936: v11, p02 2-D, p04) | translucent textured quad, drawn before the volume | yes / no | an image | intended (a computed field on its plane); its order is A2 |
| volume (`setVolume` 599) | ray march on the box's back faces | against the far face only / no | 3-D glow | A1, A10, A11, A19 |
| vectors (`setVectors` 662) | instanced cones, unlit | yes / yes | flat triangles; cut the volume | A5, A1 |
| path, tracks, lines, triads (`appendPath` 356, `appendTracks` 983, `setLines` 1030, `addTriads` 385) | 1-px lines (tracks at 0.85) | yes / yes | no thickness; cut the volume | A5, A1 |
| marks (`setMarks` 404) | unlit spheres | yes / yes | discs | A5 |
| arrow (`arrowObj` 410), body (`setBody` 425), observer (`setObserver` 499) | `ArrowHelper` (1-px shaft, unlit cone), unlit ball | yes / yes | flat | A5 |
| mesh (`setMesh` 458: v10, v15, v16, v17, p01, p02, p04) | unlit vertex colours, two-sided; translucent below opacity 1 (no depth write) + wireframe overlay at 0.12 that **does** write depth | yes / opaque only (+ the wire) | flat colour | A2, A5, A1 |
| points (`setPoints` 1048: v11/v12 particles) | `PointsMaterial` | yes / yes | squares | A5 |
| spheres (`setSpheres` 1072: playground bodies, atoms, Bohm points) | instanced unlit spheres | yes / yes | discs, merging blobs | A5 |
| slice plane (`ensurePlane` 705) | shader quad at 0.92, `renderOrder 3`; outline; `ArrowHelper` normal; number label | yes / **no** | an image | intended (a slice is a plane); its depth is A2 |
| gizmo (`TransformControls`) | three's helper, always on top | — | — | fine |

## Per world: what the tour showed

Every world was opened with its first preset (the catalogue's default) and one or two more. Status tags per item:
[useful] — the finding stands and matters there; [neutral] — checked, nothing wrong beyond the shared findings;
[weakens] — a shared finding matters less there than elsewhere.

| world (tours) | what the tour showed | findings |
|---|---|---|
| v08 (`double`, `double_slices`) | opens cropped (6/8, 7/8 corners); the light above the default slice y = 0 is hidden by it; far-side labels on the screen; zooming out ~20× empties the view; «Сверху» rotated against the window; seen from behind, the light over the screen z-fights into a dot grid [useful] | A1, A2, A4, A8, A9, A14, A19 |
| v09 (`thomas`, `lab`) | velocity ball as a wire globe (front/back ambiguous); the slice βy = 0 hides the field above it; opens cropped (6/8); in ordinary space the box doubles as the path grows, and `setBox` resets the camera each time (A7, measured in p01); tick labels ~8 px [useful] | A2, A4, A5, A7, A9 |
| v10 (`terrell`, `city`) | opens fitted (8/8: its camera window is there from the start); floor as zig-zag bands; translucent bodies against the translucent floor; the street a sliver in a portrait canvas [useful] | A2, A4, A12 |
| v11 (`narrow`, `observer`) | opens cropped (4/8); the plate behind the packet cuts the packet's cloud (`f01`); tracks and particles always over the cloud; particles are squares; the detector's caption shows through the plate [useful] | A1, A4, A5, A9 |
| v12 (`gauss`, `slits`) | v11's view: the same; opens cropped (3/8) [useful] | A1, A4, A5 |
| v13 (`1s`, `3d_m2`, `super_1s2p`) | 1s: the cloud nearly invisible in 3-D (a dot on the slice) while its window shows it clearly; the slice y = 0 hides the half of the cloud above it; 3d m=2: the current arrows are flat white shards over the cloud; the superposition spends 76 % of the main thread in scripts while the view is turned; opens cropped (6/8); over the pole the picture spins [useful] | A1, A2, A4, A5, A10, A17 |
| v14 (`cc_1S`, `cc_1P`) | the orbit view of v13 in femtometres: the clouds are even fainter (box ±1.02 / ±1.34 fm, a step of 0.022 / 0.029 fm); only the slice is really seen, and it hides the upper half of the cloud; opens cropped (7/8); the caption «cc̄» shows a missing-glyph box for the combining bar in the label canvas (font-dependent, seen in the test browser) [useful] | A2, A4, A9, A10 |
| v15 (`m87`, `edge_on`) | fits (8/8; its own views); the disk (0.55) and the ergosphere (0.18) cross and are sorted per object; tick labels unreadable at the fitted distance [weakens A4] | A2, A9 |
| v16 (`lg3`, `fork`) | the slice plane covers the beam's volume in front of it; translucent helices (0.62), rotor and hologram sorted per object; the panel «Слои сцены» rebuilt with every phase, its density slider included; opens cropped (6/8); the slowest scene to turn (4.3 draws/s in software GL) [useful] | A1, A2, A4, A11, A17 |
| v17 (`rainbow`, `near`) | the drop as a wire globe inside the translucent polar plot (0.55, with a depth-writing wireframe); captions printed over both; opens cropped (4/8, 5/8); `near`: the near field (a volume) is cut along every line of the polar plot's wireframe and painted over the plot's translucent surface that is in front of it (`f01`, right) [useful] | A1, A2, A4, A5, A9 |
| p01 (`sun_earth`, `pythagorean`, `kerr_orbits`) | bodies as flat dots; the Earth's trail with chords; after the box grows the bound pair is a small knot in a 32-au box; Kerr: a 1.4-M hole in a 64-M box; «z →» on a vertical edge; zooming out 21× empties the view [useful] | A5, A6, A7, A8, A9, A13 |
| p02 (`double_slit`, `ball_3d`) | «Изо» from below the plane at 15°, «Сверху»/«Сбоку» edge-on; opens cropped (4/8); the potential ball behind the packet cuts it away; walls, detectors and flux planes (all translucent, all centred at the origin) sorted per object [useful] | A1, A2, A3, A4, A5 |
| p03 (`maxwell`, `liquid_vapour`) | the 2-D gas edge-on; atoms as flat discs that merge into one blob; «z, нм →» on a vertical edge [useful] | A3, A5, A9 |
| p04 (`cylinder_re20`, `karman`) | the channel seen from below at a grazing angle, its field panel nearly invisible; «Сверху» edge-on; the wheel zooms into the empty middle of the channel; z ticks piled up [useful] | A3, A4, A6, A9 |

## Measurements

### The camera and the box as opened, and after F

From each tour's `tour.json` (page 1600 × 1000, device pixel ratio 1). "Corners on screen" counts the box's eight corners
that project inside the 3-D canvas in the view as opened. "Up" is the scene's up axis in physics coordinates.

| tour | canvas px | box corners on screen (of 8) | camera distance: opened → after F | up | volume | lines/paths | spheres/points | translucent meshes |
|---|---|---|---|---|---|---|---|---|
| p01_kerr | 940×887 | 8 | 190.7 → 190.7 | z | — | 4 | 1 | 1 |
| p01_pyth | 940×916 | 8 | 82.56 → 82.56 | z | — | 1 | 1 | 0 |
| p01_sun_earth | 940×916 | 8 | 7.74 → 7.74 | z | — | 1 | 1 | 0 |
| p02_ball3d | 470×916 | 4 | 117.3 → 219.8 | z | yes | 1 | 1 | 1 |
| p02_dslit | 470×890 | 4 | 195.1 → 355.4 | z | — | 3 | 1 | 4 |
| p03_lv | 940×916 | 8 | 12.72 → 12.72 | z | — | 0 | 1 | 0 |
| p03_maxwell | 940×916 | 8 | 29.26 → 29.26 | y | — | 0 | 1 | 0 |
| p04_cyl | 470×916 | 6 | 3.861 → 7.233 | z | — | 1 | 0 | 2 |
| p04_karman | 470×916 | 6 | 3.861 → 7.233 | z | — | 1 | 0 | 2 |
| v08_double | 564×916 | 6 | 93.14 → 146.4 | y | yes | 2 | 0 | 1 |
| v08_slices | 564×877 | 7 | 93.14 → 140.2 | y | — | 2 | 0 | 1 |
| v09_lab | 940×877 | 8 | 23.09 → 23.09 | y | — | 3 | 1 | 0 |
| v09_thomas | 564×916 | 6 | 5.958 → 9.363 | y | yes | 5 | 1 | 1 |
| v10_city | 470×916 | 8 | 610.8 → 610.8 | y | — | 3 | 0 | 2 |
| v10_terrell | 470×877 | 8 | 84.44 → 80.87 | y | — | 6 | 0 | 3 |
| v11_narrow | 470×861 | 4 | 301.1 → 530.6 | y | yes | 2 | 1 | 0 |
| v11_observer | 470×861 | 4 | 301.1 → 530.6 | y | yes | 3 | 1 | 1 |
| v12_gauss | 470×851 | 3 | 166.2 → 298.1 | y | yes | 1 | 1 | 0 |
| v12_slits | 470×851 | 4 | 226.2 → 405.9 | y | yes | 2 | 1 | 0 |
| v13_1s | 564×916 | 6 | 17.71 → 27.82 | y | yes | 0 | 0 | 0 |
| v13_3dm2 | 564×916 | 6 | 85.49 → 134.3 | y | yes | 0 | 0 | 0 |
| v13_super | 564×916 | 6 | 46.69 → 73.37 | y | yes | 0 | 0 | 0 |
| v14_cc1P | 564×877 | 7 | 8.01 → 12.06 | y | yes | 0 | 0 | 0 |
| v14_cc1S | 564×877 | 7 | 6.094 → 9.177 | y | yes | 0 | 0 | 0 |
| v15_edge | 470×877 | 8 | 267.9 → 256.6 | z | — | 6 | 0 | 2 |
| v15_m87 | 470×877 | 8 | 267.9 → 256.6 | z | — | 6 | 0 | 2 |
| v16_fork | 564×887 | 8 | 355.1 → 540.5 | y | yes | 1 | 0 | 1 |
| v16_lg3 | 564×887 | 6 | 60.83 → 92.59 | y | yes | 4 | 0 | 3 |
| v17_near | 564×887 | 5 | 14.9 → 22.68 | x | yes | 5 | 0 | 2 |
| v17_rainbow | 470×887 | 4 | 14.9 → 27.02 | x | — | 5 | 0 | 2 |

### Render cost (software GL; compare ratios only)

"ms per frame": six renders of the scene as opened, after F. "rAF/s" and "scene draws/s": over 4 s while the mouse keeps
turning the view (the page's animation frames, and the scene's actual renders). "script share": the fraction of those
4 s the main thread spent in scripts (CDP `Performance.getMetrics`). The machine was shared with two other reviews'
browsers and servers, so single numbers are noisy (p01 `sun_earth` 165 ms against `pythagorean` 14 ms with the same
content type); the within-page probe below is not.

| tour | draw calls | triangles | lines | ms per frame (software GL) | rAF/s while rotating | scene draws/s while rotating | script share |
|---|---|---|---|---|---|---|---|
| p01_kerr | 21 | 15240 | 18768 | 541 | 15.2 | 9.8 | 0.12 |
| p01_pyth | 15 | 1584 | 309 | 14.1 | 60.1 | 28.9 | 0.03 |
| p01_sun_earth | 15 | 1064 | 1704 | 164.7 | 56.1 | 26.4 | 0.13 |
| p02_ball3d | 18 | 17684 | 1519 | 341.8 | 25.9 | 9.5 | 0.03 |
| p02_dslit | 25 | 31348 | 102 | 238.7 | 24 | 12.3 | 0.16 |
| p03_lv | 14 | 208024 | 12 | 1883.9 | 8.5 | 4.5 | 0.05 |
| p03_maxwell | 14 | 156024 | 12 | 1451.7 | 13.3 | 6.1 | 0.07 |
| p04_cyl | 18 | 412 | 300 | 29.6 | 59.7 | 26.5 | 0.07 |
| p04_karman | 18 | 412 | 300 | 25.4 | 59.3 | 24.6 | 0.08 |
| v08_double | 46 | 152 | 28 | 597.4 | 18.7 | 9.2 | 0.02 |
| v08_slices | 45 | 140 | 28 | 174.6 | 35.4 | 17.7 | 0.08 |
| v09_lab | 35 | 780 | 899 | 37.8 | 51.3 | 22.2 | 0.05 |
| v09_thomas | 91 | 3016 | 4941 | 1411.6 | 15.8 | 6 | 0.05 |
| v10_city | 23 | 34562 | 25857 | 614.3 | 23.5 | 11 | 0.05 |
| v10_terrell | 27 | 17080 | 12488 | 93.1 | 47.6 | 20.2 | 0.03 |
| v11_narrow | 20 | 86 | 8422 | 469.6 | 21.6 | 9.9 | 0.05 |
| v11_observer | 24 | 112 | 2914 | 299.4 | 22.9 | 8.9 | 0.04 |
| v12_gauss | 17 | 38 | 9423 | 5623.8 | 15.1 | 8 | 0.32 |
| v12_slits | 20 | 86 | 5662 | 506.9 | 18.4 | 8.2 | 0.03 |
| v13_1s | 21 | 404 | 17 | 1546.5 | 14.6 | 6.4 | 0.04 |
| v13_3dm2 | 22 | 11444 | 17 | 2157.2 | 14.3 | 6.7 | 0.01 |
| v13_super | 22 | 11444 | 17 | 1058.3 | 8.8 | 4.9 | 0.76 |
| v14_cc1P | 21 | 404 | 17 | 654.7 | 21.4 | 12.7 | 0.01 |
| v14_cc1S | 21 | 404 | 17 | 1313 | 15.8 | 8.3 | 0.01 |
| v15_edge | 26 | 25092 | 25213 | 573.6 | 22.5 | 10.8 | 0.08 |
| v15_m87 | 26 | 25092 | 25213 | 431.7 | 27.3 | 13.8 | 0.03 |
| v16_fork | 22 | 36150 | 27282 | 2313.8 | 8.8 | 5.8 | 0.06 |
| v16_lg3 | 30 | 32536 | 28560 | 2173.8 | 4.5 | 4.3 | 0.3 |
| v17_near | 49 | 28202 | 20739 | 2251.8 | 12.1 | 5.6 | 0.01 |
| v17_rainbow | 43 | 28176 | 20734 | 429.4 | 18.1 | 10.3 | 0.07 |

**The volume's share of a frame** (`probe.mjs volcost`, v13 1s, the same page, the same camera, one render after
another):

| canvas (device px) | cloud on, 160 steps | cloud on, 64 steps | cloud off |
|---|---|---|---|
| 564 × 917 (pixel ratio 1) | 835.7 ms | 476.8 ms | 15.2 ms |
| 1128 × 1834 (pixel ratio 2, a HiDPI laptop) | 2834.5 ms | 1160.4 ms | 62.4 ms |

The volume is 98 % of the frame; a HiDPI screen multiplies it by 3.4; 64 steps take 57 % of the time of 160. On a GPU all of these
are far smaller, but the ratios carry over: the march, not the geometry, is what makes turning a volume world sluggish.

## What was verified, and how (status per item)

- [useful] Every 3-D world (v08–v17, p01–p04) opened from its default preset and at least one more, turned, tilted,
  over the pole, F, zoomed in and out, panned, every view button; screenshots looked at one by one (30 tours,
  `scripts/lanes.sh`). v01–v07 have no `.s3d-view` (checked in their `web/view.js`).
- [useful] Depth: three probes with numbers (A1 `volsphere`, A2 `twoplanes`, `planevol`) and the real cases they
  explain (p02 ball, v11 plate, v17 near field, v13 2p_z slice).
- [useful] Flatness: an A/B with only the material changed (A5 `flat`).
- [useful] The camera: the box's corners on screen as opened and after F, the distance, near/far after zooming out
  (A4, A8); the view buttons in every up-z world (A3); the box growing under a moved camera (A7 `boxjump`).
- [useful] Cost: the volume's share of a frame within one page (A11 `volcost`).
- [neutral] Themes: the 3-D view keeps its dark background and its own toolbar colours in the light (default) and the
  dark theme; nothing in it became unreadable (`probe.mjs theme`, v09 in both; screenshots in the scratch run, not
  copied here).
- Not checked: a real GPU, a real touchpad, Firefox and Safari (the wheel and touchpad notes in A6 are from the vendored
  `OrbitControls.js`); the slice gizmo (W/E), plane picking and «＋ Срез» as interactions (only the depth of the planes
  they place, A2); the 2-D windows' own drawing; the physics.
