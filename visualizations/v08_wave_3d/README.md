# v08 — a wave in 3-D: diffraction by an aperture, in the 3-D environment

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` and the reference world of the player's 3-D environment (owner, 2026-10-27;
`../RULES.md` §2.10). Monochromatic scalar light behind an aperture in the plane z = 0 — a Gaussian field, a circle, a
square, a slit or a double slit of finite length — propagated into the half-space z > 0.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.optics.angular_spectrum` | core | propagation by the angular spectrum: the volume on 96 planes, a slice on a plane of any orientation (`propagate_plane`: the same sum, no interpolation), the energy current Im(U*∇U)/k and the power through each plane (`propagate_current`); plain or band-limited sum |
| `core.optics.aperture_fields` | core | the exact spectra of the sources (closed forms) and the exact fields without FFTs that the checks compare with: rectangles anywhere, the disc on its axis, the Gaussian anywhere, and its derivatives |
| `core.geometry` | core | planes (`Plane.horizontal`: u horizontal, v towards the depth), the modelling mode with per-slice exactness |
| `core.backend` | core | where the propagation runs (CPU or GPU 0) and in which precision |

The apparatus (`engine/apparatus.py`, no physics of its own): the source as an exact spectrum, the window chosen by
measurement, the cut of a plane by the computed region, the slice and its check at points, the preview volume, the
current's glyphs.

## The scene

* **Objects:** the screen with its aperture at z = 0 (for the Gaussian: the given field on z = 0), the incident plane
  wave (given, before the screen), the target at z_max showing the computed intensity there.
* **Fields:** the light behind the screen (the computed volume as a glowing cloud: |U|², averaged 2 × 2 across for
  n = 256 — a preview; exact values are in the slices) and the energy current (arrows on 10 planes × 16 × 16 points,
  direction of j, length ~ √|j|; off at start). Only in full 3-D.
* **Every element switches off on its own** ("Scene layers"), with the cloud's density and threshold and the arrows'
  threshold.
* **Slices:** up to three planes of any orientation, each with its own window in its colour. "＋ Slice" places the next
  plane through the middle of the region, perpendicular to the planes there, turned ones included (one plane: its
  default if perpendicular, else n₁ × the axis least along n₁; two planes: n₁ × n₂). A plane is moved and tilted by
  hand — click it; the arrow moves it along its normal, the two rings tilt it (W / E switch; moves within the plane
  and the roll about the normal are not offered: they would not change the plane) — or by parameters (centre; the
  normal by θ from the z axis and azimuth φ; presets y = c, x = c, z = c; "default" returns one plane y = 0). Pointing
  at a window highlights its plane; clicking selects it. **Planes stay where they are put**, and are kept in a new
  world of the run (any change of the world's parameters); "auto-shift along the normal" (per plane, off by default)
  moves a plane along its normal while world time runs: then the slice is coarse (64 rows, not checked, at most twice
  per world second, no phase in the record: ~50 kB per message at n = 256) and the full slice returns when the
  auto-shift is switched off.
* **A plane's position:** a plane is fixed by its normal n and its distance d = o·n; the run takes its point closest
  to (0, 0, z_max/2) as its centre, with d clamped to the region (a centre given outside the region still gives the
  same plane, never another one).
* **What a plane shows** is computed by the run when the plane is put down (`view` command): exactly for that plane,
  by the same sum as the volume (`propagate_plane`), on the grid step along the plane's horizontal axis and 256
  samples along the other; points outside the computed region are blank. While a plane is dragged, its window shows a
  preview, labelled as such: sampled from the volume (full 3-D) or a coarse slice from the run (48 rows, not checked;
  slices only).
* Windows: intensity, amplitude, log or phase; axes in physical coordinates (x, y or z when the plane's axis runs along
  one, increasing to the right and upwards; otherwise the distance from the plane's centre along the stated
  direction); the depth horizontally for longitudinal planes; the coordinates and values under the cursor; CSV
  export; the zone next to the aperture hatched in every window that reaches it. The log scale starts at
  (3 × the window's error)² of the peak in the windows and in the 3-D scene alike. An approximate (reduced-model)
  slice is red in its window and on its plane in 3-D.
* Camera: orbit, pan, zoom; views from the side, from above, from the source, from the target, isometric; a PNG
  snapshot.

Interface conventions adopted from common 3-D and slicing tools (not copied): a slice plane defined by an origin and a
normal with axis presets (as in scientific visualization tools), colour-coded slice windows linked to their planes
(as in medical image viewers), move/rotate gizmos with W / E and per-element visibility toggles (as in 3-D editors).

## Modelling (world parameters; owner, 2026-10-24)

* **Full 3-D** ("Modelling" = "whole volume: light and energy current in 3-D, any slices"): the volume on 96 planes
  z ∈ [0, z_max] is computed once (the cloud, the current); slices on any plane are computed when placed. Grid ≤ 256.
* **Slices only** ("slices only (faster): only the planes placed are computed"): no volume, nothing but the slices
  placed (faster; the scene shows the apparatus, the target and the slices). For a slit or a double slit, planes with
  the normal along y (y = c) can be computed by the **reduced 2-D model** (the slit taken as infinitely long): an
  approximation, flagged per plane (`Modelling` keeps exactness per slice), in the header's `approximations`, the run
  list, the top bar, the window (red) and the checks, where its size is measured against the exact slice.

## Accuracy, measured by every run

* **Source.** The aperture enters by its exact Fourier transform at the grid's frequencies, so sharp edges carry no
  staircase. Left out are the components beyond the grid's band, |q_i| ≥ π/dx: evanescent; their factor
  exp(−√((π/dx)² − k²) z) is 1e-6 at z_near = 1.27 λ (dx = λ/4) or 0.57 λ (dx = λ/8); closer to the aperture the field
  is the band-limited one (ringing next to the edges on z = 0), hatched and named in the check `near`.
* **Window.** The field is computed with the window padded p and 2p times, for the plain and the band-limited sum, on
  the plane z_max and on the two central longitudinal planes y = 0 and x = 0 at 12 depths beyond z_near (review C1:
  the band-limited sum removes the copies' error on z_max but not at mid-depth — in the circle preset the drawn
  field was 3.8e-3 off at z ≈ 4.6 µm while the estimate on z_max said 8.8e-4); the estimate is
  1.5·max|U_p − U_2p| / max|U| for each of these planes against its own peak (what a window or the target shows: a deep
  plane where the beam has spread is dim, and a global peak would hide its error), the largest of them, never below
  1e-12 (the rounding of the sums); in field units the same estimate is the tolerance of the checks at points. The
  smallest window (the plain sum when both pass) with the estimate ≤ 2e-3 is used (below one of 256 colour levels); at
  most 4096 points per axis are computed, a world that needs more is refused with the reason, what to change and a
  scenario that works for that source (review UX-params P26: the refusal comes after the search — 11 s on GPU 0,
  ~90 s on the CPU; no a-priori bound yet, STATUS). The factor 1.5: against
  the exact field at points of z_max and of the central planes at every measured depth, each against its plane's
  peak, the true error was at most 1.12 × the difference over twelve worlds of the schema's range (presets,
  z_max = 80 µm, a = 0.2 µm at λ = 0.3 µm, circles of a = 1–5 µm, squares, slits, Gaussians of waist λ), both sums,
  pads 2–16 (`tests/window_estimate_table.py`, 2026-10-27, GPU 0;
  `tests/test_v08_wave3d.py::test_window_estimate_bounds_the_true_error`, `::test_the_circle_preset_is_within_its_estimate_at_every_depth`).
  Neither sum is better everywhere, hence both are measured. A plane whose horizontal axis is not along x or y turns
  the source (the copies' lattice turns with it): the window is measured again for the turned source in the same way,
  once per azimuth, and widened if needed; the window used is stated under the slice.
* **Slices.** Each slice is compared at up to three of its own points (the brightest and two with ≥ 5 % of its
  intensity, deeper than z_near) with the exact field without FFTs (rectangles: everywhere; the Gaussian:
  everywhere; the circle: on its axis only); the window's error is the tolerance; the result is under the window and
  in the check `plane_exact_N` of that plane.

## Checks

| id | quantity | reference | tolerance |
|---|---|---|---|
| `window` | error of the drawn field on z_max from the window | 1.5·max\|U_p − U_2p\| | 2e-3 of the peak |
| `exact_i_j` | the field (fp64, the drawn window and sum) at grid nodes of z_max | the exact field without FFTs | the window estimate × peak + the reference's own error + 1e-9 |
| `plane_exact_N` | slice N (one row per plane; "Slice N: removed" when removed), at up to three of its points | the exact field without FFTs | the window estimate × peak |
| `slice_route` | the plane y = 0 by `propagate_plane` against the transverse planes' rows, at z_max/2 and z_max | the engine's two methods, fp64 | 1e-12 of the peak |
| `flux_exact` | (full 3-D) the energy current j = Im(U*∇U)/k at the reference points of z_max | Im(U*∇U)/k of the exact field: closed-form derivatives (the Gaussian, the circle on its axis) or five-point differences of the exact field (rectangles; step 1e-3 µm, error < 1e-8) | the window estimate × peak × (\|U\| + \|∇U\|/k) at the point |
| `flux` | (full 3-D) the power through 10 planes z, Σ j_z dx dy over the whole window, against the spectrum's closed form | information: Parseval's identity of the discrete sum (a check of the code and its normalisation, not of the window or the physics; review C4); for the band-limited sum the power it removes at depth | — |
| `fp32` | (fp32 drawing) the drawn data against the same computation in fp64 | fp64 | the kernel's declared bound (1e-5) |
| `reduced` | (reduced model) the reduced 2-D slice against the exact slice | information (≈) | — |
| `near` | depth of the zone next to the aperture | information | — |
| `device` | where the drawing's angular spectrum ran, in which precision, why | information; checks are always fp64 | — |

## Approximations and limits

* Scalar diffraction: one Cartesian component of the field obeys the Helmholtz equation exactly; the aperture sets
  that component on z = 0 (Rayleigh–Sommerfeld boundary values; the field just behind a real screen differs near the
  edges, which needs a vector solver: plan P1). The current Im(U*∇U)/k is the energy flux of this scalar wave.
* The 3-D cloud is a preview (2 × 2 averaged across, 96 depth planes, trilinear in the shader); numbers come from the
  slices and the checks.
* Timing (2026-10-27, this host, window measured over depth): GPU 0 — a world 0.6 s (gauss) to 6.7 s (double,
  window ×8, with the current), a tilted slice 0.04–0.36 s (the first at a new azimuth 0.1–1.3 s: the window measured
  for the turned source); CPU (two threads) — 4 s to 79 s per world, a tilted slice 0.5–12 s (the first at a new
  azimuth up to 49 s). GPU 0 is the intended device for this world.
* The page needs WebGL 2 (any current browser).

## Tests

`tests/test_v08_wave3d.py` (Docker; with `--gpus '"device=0"'` the GPU test runs too): every preset builds with all
checks passing, its scene and an exact reference; planes stay where they are put and move only with the auto-shift; a
tilted plane moves uniformly with the auto-shift and a centre given outside the region keeps its plane; auto-moving slices are coarse
and rate-limited, and the full slice returns; planes carry over to a new world and "default" restores the
default; planes of any orientation, up to three, each with its own check, every point on its plane and NaN outside
the region; labels follow the normal; a slice equals the volume on its grid points; the slices mode computes no
volume and flags the reduced plane alone; a dragged plane in "slices only" gets a coarse preview that changes
nothing; the reduced model's error shrinks with the slit's length; the energy current against the exact current; the
window estimate bounds the true error over depth, and the circle preset is within it at every depth; a world needing
too wide a window is refused; fp32 drawing keeps every check passing; the GPU gives the same world and slices as the
CPU. The page itself: headless Chromium (WebGL by SwiftShader) — the presets, a plane dragged by its gizmo and
recomputed by the run, windows highlighting their planes, layers switched off, the axes of the windows after moves and
for the normal −z, three mutually perpendicular planes after the first was turned, the gizmo's handles, the red
approximate plane (2026-10-27, no page errors).

Open items: `../../STATUS.md`.
