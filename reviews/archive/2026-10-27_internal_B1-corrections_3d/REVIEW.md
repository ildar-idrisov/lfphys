# Review of the B1 corrections: the 3-D environment (planes of any orientation, the current, v08 rebuilt, the player's 3-D scene, three.js)

**Status: awaiting processing.** (Reviewer: an independent internal subagent; it does not process this review —
`../README.md`, `../../AGENTS.md` §3 rule 6.)

Delivered: 2026-10-27.

## Scope

The uncommitted working tree against commit a7b5561 (`git diff --stat -- engine`, `git status -- engine`):

* Engine: `lfphys/lfphys/core/optics/angular_spectrum.py` (`propagate_plane`, `propagate_current`, `flux_of_spectrum`,
  `Spectral` sources on the device), `aperture_fields.py` (`gaussian_field(deriv=)`, xp-agnostic spectra, `rotated`),
  `core/geometry.py` (`Plane.horizontal`, `_label`); tests `test_planes_and_current.py`, `test_aperture_fields.py`,
  `test_backend.py`.
* v08: `viz.py`, `engine/apparatus.py` (plane_box, compute_slice, reduced_slice, verify_slice, window_for_plane,
  preview_volume, flux_glyphs; view ops plane / remove / preview; "auto" in `advance()`; its checks); the runner's `view`
  command (`server/lfviz/sim.py`).
* Player: `player/js/scene3d.js`, `player/js/slices.js`, `v08_wave_3d/web/view.js`, `player.js`, `run.html`; vendored
  three.js r185.1 (`player/vendor/`, `lfphys/sources/dependencies.md` §7, `NOTICE`).
* Docs: v08 README, `visualizations/RULES.md` §2.10 and §3, the owner guide `visualizations/README.md`,
  `lfphys/PLAN.md` (§0, P10, P14 note, §4), `STATUS.md` V22–V24.

## Environment

* Image `light-funnel-viz:latest` (959a1b91570e): Python 3.11, numpy 2.4.6, scipy, mpmath, CuPy 14.2.0 (CUDA 12.9
  runtime on driver 12.4). GPU scripts with `--gpus '"device=0"'`, `CUDA_DEVICE_ORDER=PCI_BUS_ID`,
  `LFPHYS_GPU_PCI=0000:01:00.0` (RTX 2080 Ti, PCI 0000:01:00.0); each GPU run took seconds, GPU 0 stayed ≤ 62 °C.
* Every Python script runs from `engine/` mounted at `/lf`, working directory this folder:
  `docker run --rm --user 1000:1000 -e PYTHONDONTWRITEBYTECODE=1 -v <engine>:/lf -w /lf/reviews/2026-10-27_internal_B1-corrections_3d -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server light-funnel-viz python3 NN_<name>.py`
  (outputs in `out/NN_<name>.txt`); `common_rev.py` is this review's helper (a brute-force, point-by-point evaluation of
  the angular-spectrum sum: no FFT, no recurrence, no modulo reading).
* Browser: the reviewer's own server instance (`rev-viz8498`, port 127.0.0.1:8498, engine mounted read-only, runs in
  `./runs`; stopped after use, the run records removed after their metadata was saved in `out/07_runs_meta.txt`);
  Playwright 1.58.2, Chromium with SwiftShader WebGL (`--init --shm-size=2g --network host`). The shared server
  `lf-viz` was not used; no settings were written anywhere. Every run started was stopped.

## Findings

| ID | severity | tag | in one line |
|---|---|---|---|
| C1 | error | [error in earlier] | window error measured on z_max only: with the band-limited sum the drawn field is up to 4.5× the estimate at mid-depth (circle preset 3.9e-3 > TOL 2e-3); every check and the slice's point check pass |
| C2 | should-fix | [weakens] | slice windows: tick values are s / t, not coordinates — wrong after any in-plane move of the origin (gizmo arrow, centre fields), mirrored for v = −y and for u = −x on non-longitudinal planes |
| C3 | should-fix | [weakens] | origin clipped to the box: an "auto" tilted plane stalls at the faces (0.019 instead of 0.5 per step) and lands off after a wrap; an origin outside the box silently gives another plane (d 12.02 → 9.10) |
| C4 | should-fix | [weakens] | the check "поток энергии сохраняется" is the Parseval identity of the discrete sum: passes at 4e-16 with the field 530 % off; it cannot fail |
| C5 | should-fix | [weakens] | «＋ Срез» is not at 90° to a turned plane (\|n₁·n₂\| = 0.5); RULES, READMEs and the owner guide say "perpendicular" |
| C6 | should-fix | [weakens] | "auto" floods the record: 0.53 MB per slice message (n = 256), ~1.5 per s at speed 1 → ~2.9 GB/h against the 5 GB quota |
| C7 | should-fix | [weakens] | hand-placed planes are discarded by every new world (every parameter change of v08): plane 1 back at the default |
| C8 | nit | [neutral] | one check id `plane_exact` for all planes: earlier planes' results leave the check list; stale after removal |
| C9 | nit | [neutral] | "как дал бы объём на этой сетке" / "Identical to what the volume gives" is false for turned planes (6e-4 of the peak at 30°, within the estimate) |
| C10 | nit | [neutral] | gizmo: the ring about the normal is undone by the server, the in-plane arrows only shift the origin (recompute + C2) |
| C11 | nit | [neutral] | labels and flags: normal +y plane "произвольная плоскость"; reduced plane unmarked in 3-D; run list keeps «приближение» after removal; 3-D log floor ≠ window's; hatch only on longitudinal windows |

### C1 — error — v08's window estimate is measured on z_max only; the band-limited sum's error peaks at mid-depth

* **Location:** `visualizations/v08_wave_3d/engine/apparatus.py:127-155` (`choose_window`: both sums compared on the plane
  z_max only), `:201-223` (`window_for_plane`: likewise), `viz.py:195` (`tol = win.est * self.peak_amp + 1e-9`, the
  tolerance of every slice at every depth), `viz.py:323` (`exact_i_j` at z_max only); README `:62-77` and
  `apparatus.py:13-19` (the calibration "the true error was at most 1.25 × max|U_p − U_2p|" — 21 points of z_max).
* **What is wrong.** The estimate assumes the drawn field's window error is largest on the deepest plane. That holds
  for the plain sum (error grows with z), not for the band-limited sum: its mask depends on z and removes the
  periodic-copy error at z_max while leaving it at smaller depths, where the mask is lenient. So when the run picks
  the band-limited sum (the circle preset does), the volume, the target and every slice carry errors above the stated
  estimate and above TOL = 2e-3, and nothing reports it: the `window` check, `exact_i_j` (z_max) and the slice's
  three-point check all pass. This undermines the fix of B1-1 ("window chosen and checked by measurement") in shipped
  presets.
* **Evidence.**
  * `03b_error_vs_depth.py` → `out/03b_error_vs_depth.txt`, preset `circle` (window ×4, band-limited, estimate
    8.8e-4): the drawn y = 0 slice on the axis against the closed form e^{ikz} − (z/R)e^{ikR}: **3.79e-3 of the peak
    at z = 4.55 µm** (2.2e-5 at z_max); 41 % of 251 depths above the estimate; against a ×16 window 4.04e-3 at
    z = 5.18. The real run of the preset: no failed check; slice 1 point check 1.086e-3 ≤ 1.137e-3 ✓ (5 % margin).
  * `03c_bandlimit_depth_sweep.py` → `out/03c_…txt`, whole drawn volume (96 planes) against a 4× wider window, ten
    worlds: every band-limited world peaks below z_max — circle a = 3: 3.93e-3 at z = 5.1 (**4.5× the estimate**);
    circle a = 5, λ = 0.8: 3.34e-3 (2.2×); square a = 3: 2.18e-3 (1.6×); double a = 1: 7.6e-4 (1.1×); slit a = 2:
    0.7×. All plain-sum worlds peak at z_max, ratio 0.7. The plain sum at the circle's pad: 4.32e-3 at mid-depth,
    3.72e-3 at z_max — the band limit hides at z_max what remains elsewhere.
  * `03_turned_window.py`: the turned slit at 30°: 1.11e-3 against its estimate 7.9e-4.
* **Fix.** Measure the estimate where it is used: over depths, not at z_max. Cheap options: (a) the two longitudinal
  planes y = 0 and x = 0 at p and 2p with `propagate_slice` (all depths, two slices); (b) the whole drawn volume at 2p
  (one more volume on the GPU); (c) for each slice, the same slice at 2p (one more `propagate_plane`) and its own
  max|U_p − U_2p| as its tolerance. Re-derive SAFETY over depths (`tests/window_estimate_table.py` at many z), and
  correct the README/apparatus calibration text. Until then, the README must not state that the estimate bounds the
  drawn error.

### C2 — should-fix — slice windows label s / t as coordinates

* **Location:** `visualizations/player/js/slices.js:123-124` (tick values `m.s`, `m.tt`), `:143-144` (axis names: "x"
  whenever |u_x| > 0.999, "y" whenever |v_y| > 0.999, regardless of sign; for longitudinal planes `axisName(u)` with
  values s). The server measures s and t from the plane's origin (`viz.py:179`, `apparatus.plane_box`).
* **What is wrong.** The ticks are the in-plane parameters s, t (offsets from the origin along u, v), but the axes are
  named as coordinates. They agree only when the origin's coordinate along that axis is 0 and the in-plane axis points
  along +x / +y. Any in-plane move — dragging the gizmo's u/v arrow, typing the centre, or the origin clipping of C3 —
  shifts the ticks; a transverse plane with normal −z (θ = 180) or a tilted plane with u = −x is mirrored.
* **Evidence** (`07_browser.mjs` → `out/07_browser.txt`, `07c_window_axes.mjs` → `out/07c_window_axes.txt`, screenshots):
  * plane z = 15 after centre x = 5: horizontal axis «x, мкм» with ticks −21 … 10.875; the true x of those points
    −16 … 15.875 (the window's own readout at its left edge: x = −15.63) — `out/07e_window3_after_x5.png`;
  * plane y = 0 dragged by its gizmo: origin → (−3.466, 0, 15), same plane; its window's «x» ticks run −12.5 (bottom)
    … 19.3 (top) for true x −16 … 15.875 —
    `out/07h_flux_on_light_off.png` (top window);
  * normal −z: vertical axis «y» with ticks −7.875 (bottom) … 8 (top); readout at the top edge y = −7.875 (mirrored);
  * y = 0 with origin x = 3: «x» ticks −11 … 4.875; readout at the top x = 7.75.
  The CSV export and the readout compute x, y, z correctly; only the axes are wrong.
* **Fix.** Draw ticks in physical coordinates: for an axis along ±x (±y) use x = o_x + s u_x (y = o_y + t v_y), with
  the direction of increase following the sign; otherwise name the axis "s от центра плоскости" and show the centre.
  Projecting the box centre onto the plane as the origin (C3) keeps s = 0 on the centre line.

### C3 — should-fix — the plane's origin is clipped to the box (auto stalls; a requested plane is replaced)

* **Location:** `viz.py:179` and `:264` (`o = np.clip(origin, lo, hi)`), `viz.py:412-432` (`advance`: the new origin is
  `o + (d_new − d) n`, then clipped by `_set_plane`), `scene3d.js:555` (the gizmo's pose clipped the same way).
* **What is wrong.** Clipping a point of a tilted plane to the box moves it off the plane, so the computed plane is
  another one. For "auto" with a normal not along an axis, the origin leaves the box long before the plane does; each
  step then slides along a face and the distance d advances by only n_z²·step, so the plane slows down near the faces
  and the jump of a wrap (origin moved by −span along n, then clipped) does not land at d_min. A user's origin outside the box (typed, or dragged) silently gives a
  different plane.
* **Evidence** (`04_v08_paths.py` → `out/04_v08_paths.txt`, harness = the server's Runner):
  * auto, speed 1, normal (0, −1, 0): uniform 0.500 per 0.5 s, 4 wraps in 60 s (3.8 expected) — correct;
  * normal (1, 0, 0.2): mean advance 0.445, **minimum 0.019** per 0.5 s (expected 0.5), 3 wraps in 60 s (3.4
    expected); normal (0.6, 0, 0.8): mean 0.419, minimum 0.180;
  * normal (1, 0, 1)/√2 with origin (12, 0, 5): asked d = 12.02 (inside the box's range [−5.66, 12.64]); computed
    d = 9.10, origin clipped to (7.875, 0, 5).
* **Fix.** Never clip the origin; take o = c + (d − c·n) n, the projection of the box centre c onto the plane, with d
  the requested o·n clamped to [d_min, d_max] (refuse with a reason outside it). Use the same in `advance` and in the
  gizmo's pose.

### C4 — should-fix — the energy-flux check cannot fail (Parseval identity)

* **Location:** `viz.py:370-388` (`_check_flux`, label «Поток энергии через каждую плоскость z сохраняется»),
  `angular_spectrum.py:317-358` (`propagate_current`, `flux_of_spectrum`), README `:87`.
* **What is wrong.** Σ_x Im(U* ∂_zU) over the window equals (1/M) Σ_q Re k_z |B_q|², and |B_q| = |A_q| for propagating
  q, for any spectrum on any window; `flux_of_spectrum` evaluates the same sum. The check therefore confirms the FFT
  normalisation only; it is insensitive to the window, the source and to a common error of the 1/k normalisation. It
  is shown with ✓ next to the physics checks. (The note says "Парсеваль", which is honest, but the label claims a
  physical verification.)
* **Evidence** (`02_current.py` → `out/02_current.txt` (d)): a Gaussian w = 0.35 µm at z = 40 µm: with pad 1 the field
  is **off by 5.33 of its peak** (530 %), pad 2 by 1.89; the check value is 3.9e-16 and 2.0e-16 ("ok"). Even P against
  the continuous closed form (1/k)∫Re k_z|Â|²d²q/(2π)² differs only by 7e-5 at pad 1: a total power cannot see the
  window. The current itself is right (Verified).
* **Fix.** Make the flux check local: j at the reference points against the exact current from the references
  (`gaussian_field(..., deriv="z"/"r")` exists; for rectangles d/dz and d/dx of the RS-I integral are closed-form in
  g(t)), with the window estimate as tolerance. Keep P(z) = const as information ("тождество суммы, проверка кода").
  Optionally label the layer «поток энергии скалярной волны».

### C5 — should-fix — a new plane is not at 90° to a turned plane

* **Location:** `v08_wave_3d/web/view.js:119-128` (`addPlane`: the first default normal not parallel, |n·t| ≤ 0.99, to
  the planes there); docs: v08 README `:30`, `RULES.md:112`, owner guide `README.md:70` («перпендикулярно уже стоящим»).
* **What is wrong.** The owner: «срезы автоматически располагай в середине визуализации под углами 90 градусов». The
  rule only avoids parallel planes; after the owner turns a plane, the next one is a fixed default.
* **Evidence:** `out/07_browser.txt` (10): plane 1 turned to θ = 90°, φ = 300° (n = (0.5, −0.866, 0)); two «＋ Срез»
  give n₂ = (1, 0, 0), n₃ = (0, 0, 1): |n₁·n₂| = **0.500** (60°). Screenshot `out/07i_add_after_turn.png`. (With the
  default planes all three are mutually perpendicular: 0.000, `out/07_browser.txt` (3).)
* **Fix.** One plane present: n₂ = normalise(n₁ × e) with e the axis least parallel to n₁; two present: n₃ = n₁ × n₂
  (when n₁ ⊥ n₂; else the component of the default orthogonal to both). Same in the docs.

### C6 — should-fix — "auto" fills the run record and the quota

* **Location:** `viz.py:412-432` (a full slice each time the plane moves by max(dx, span/48)), `viz.py:226-240` (each
  slice message carries I and phase as float32), RULES §3 (everything except `frame` is recorded and replayed to late
  viewers); the quota 5 GB (`server/lfviz/runs.py:237`).
* **Evidence:** `out/04_v08_paths.txt` (2), (2b): n = 128, normal y, speed 1: 122 slice messages, 32.1 MB in 60 s of
  world time; at the default n = 256 one slice message is 0.53 MB. With the default box (span 31.9 µm → a recompute per
  0.66 µm) that is ~1.5 messages/s at speed 1, ≈ 0.8 MB/s ≈ **2.9 GB per hour** (plus a `plane_exact` check and a
  `planes` message each time); the panel allows 100 µm/s and the world speed 20. On the CPU each step costs ~12 s
  (`out/04_v08_paths.txt` (8)), with a full three-point RS-I check every step.
* **Fix.** Treat auto-moved slices like frames (droppable, thinned in the record), or record the pose only and
  recompute on replay; send the full-resolution slice and its point check when the plane stops; cap the rate.

### C7 — should-fix — a new world discards the planes the owner placed

* **Location:** `viz.py:115` (a world starts with plane 1 at the default), `view.js:166` (`reset`); v08 has no live
  parameters, so every change of λ, a, z_max, the source or the grid is a new world.
* **Evidence:** `out/04_v08_paths.txt` (1): after a new world only plane 1 at (0, 0, z_max/2), normal (0, −1, 0);
  plane 2 of the previous world is gone; same in the browser, `out/07_browser.txt` (11).
* **What is wrong.** The owner: «срез … должен быть зафиксирован … место среза задаю руками». Changing any parameter
  moves his slices back to the default.
* **Fix.** Carry the planes (pose, auto, speed) into the new world through `new_world` (projected into the new box as
  in C3); a «срезы по умолчанию» button resets them.

### C8 — nit — one `plane_exact` check for all planes

* **Location:** `viz.py:209`. **Evidence:** `out/04_v08_paths.txt` (7): after plane 2 the check is «Срез 2 …»; after
  plane 3 it is «Срез 3 (z = 6) …» and plane 2's result is no longer in the check list; after removing plane 3 the
  check still names it. **Fix.** One id per plane (`plane_exact_{pid}`), removed with the plane.

### C9 — nit — "as the volume would give" for turned planes

* **Location:** `viz.py:42` (route label «точно для этой плоскости (как дал бы объём на этой сетке)»),
  `angular_spectrum.py:248` («Identical to what the volume gives at those points on the same grid»).
* **What is wrong.** A plane whose u is not along ±x, ±y turns the source; the sum is then over the turned lattice of
  copies (a different periodisation), not the volume's.
* **Evidence:** `01c_turned_vs_volume_v08.py` → `out/01c_…txt`, v08 default world: slice at azimuth 30° against the
  volume's own sum at the same 755 points: **6.1e-4 of the peak** (45°: 1.4e-4; 90°: 5e-14); both equally close to the
  exact field (2.4e-4 and 4.8e-4). `out/01_plane_vs_routes.txt` (c): at pad 4, 2.0e-3 … 3.9e-3. Within each window's
  estimate, so a wording issue. **Fix.** "точно для этой плоскости (окно — для повёрнутого источника)" where the source
  is turned; the docstring: identical to the volume when u is along ±x, ±y.

### C10 — nit — gizmo handles that do nothing physical

* **Location:** `scene3d.js:527-557` (`groupPose` returns origin and normal only), `viz.py` → `Plane.horizontal`.
* **What is wrong.** Rotating with the ring about the plane's own normal is undone after release (u is forced
  horizontal); the two in-plane arrows move only the origin, which recomputes the same plane and shifts the window's
  ticks (C2). Evidence: `out/07_browser.txt` (8): a drag moved plane 1's origin from (0, 0, 15) to (−3.466, 0, 15),
  normal and label unchanged («y = 0»), the slice recomputed. **Fix.** Hide the normal ring in rotate mode and the
  in-plane arrows in translate mode (TransformControls `showX/showY/showZ`), or document them.

### C11 — nit — labels and flags

* `geometry._label`: the plane y = 1 with normal +y is «произвольная плоскость» (with −y: «y = 1»), `out/04_v08_paths.txt`
  (5); the same for x = c with normal −x.
* The reduced (approximate) plane is marked in its window, the checks and the top bar, but not on the plane in the 3-D
  scene (`out/07l_slices_only.png`).
* The run list keeps «приближение» after the reduced plane is removed (`runs.py:137` takes it from the header):
  `out/07_browser.txt` (12) — conservative, but stale.
* Log scale: windows start at max(1e-6, (3·window_est)²) (`slices.js:101`), the 3-D plane and the cloud at 1e-6
  (`scene3d.js:30`), so the 3-D view shows a decade the windows hide as unreliable.
* The near zone is hatched only in longitudinal windows (`slices.js:130`); a tilted (|v_z| ≤ 0.5) or transverse plane
  with points at z < z_near is not hatched.

## Verified correct

* **`propagate_plane` = the volume where they overlap.** At grid nodes, against `propagate_field` columns: four
  families (u = +x, −x, +y, −y, i.e. turns by 0°, 180°, 90°, 270°), tilts 90° (longitudinal), 60°, 30°, 1°, 0.01°
  (nearly transverse), even and odd n (128, 97), plain and band-limited, Spectral and sampled (odd and even n)
  sources: **≤ 7.1e-14 of the peak**; points before z = 0 exactly NaN (`out/01_plane_vs_routes.txt` (a)(b)).
* **= the same sum at any orientation:** against the brute-force sum in the turned frame (no FFT, no recurrence, no
  modulo) at azimuths −150°, −117°, −43°, 30° and tilts 20°–89°: 2.0e-14 … 7.3e-14; planes half before the source,
  14° and 0.008° from transverse, transverse with normal −z: ≤ 7.0e-14; an origin at a box corner with s over almost
  a whole period (read modulo): 5.2e-14 (pad 2), 8.2e-14 (pad 1); an s range longer than the period is refused
  (`out/01_…` (c)(d)(e)).
* **Against the exact field without FFTs** (rectangles_field) on planes at arbitrary azimuths: the error is the
  window's (5e-4 … 1.1e-3 at pad 4; `out/01_…` (c)), not the route's.
* **The recurrence of e^{ik_z z}:** 4000 uniform steps over t ∈ [−1, 79] (k z up to 1000 rad) and a 0.6 µm range
  dominated by evanescent components: 3.4e-14 and 1.2e-15 against brute force (`out/01_…` (g)); the per-row
  fallback (t jittered by 1e-13) agrees to the jitter's own effect (5e-11).
* **90° turns:** the turned spectrum A(Rq) differs from the volume's only on the Nyquist line (fftfreq is
  asymmetric), i.e. next to the aperture: 6.9e-4 at z = 0, 6.4e-10 at z_near, 7e-16 at 2 z_near, for an asymmetric
  source; none for sources even in x (all of v08's) (`out/01b_turn90_nyquist.txt`). The claim "turns by multiples of
  90° map the lattice onto itself" is right beyond the hatched zone.
* **Turned windows** (`window_for_plane`): measured on the turned crop, but the box corners outside it are no worse
  (azimuths 30°, 45°, five worlds: corners 9.1e-5 … 1.1e-3, inside the crop 1.1e-4 … 3.9e-3; `out/03_turned_window.txt`), so
  the crop does not matter at these pads; the failures there are C1's (band-limited worlds).
* **Band-limit mask** of `propagate_plane` = the volume's at the same z (plain and band-limited agree to 7e-14 in
  (a)(b)).
* **fp32:** a turned tilted plane 5.5e-8; at windows of 1024, 2048, 4096 points per axis (k z ≈ 1000): plane
  ≤ 5.6e-8, transverse plane ≤ 3.5e-7, current ≤ 2.7e-7, power ≤ 1.3e-7 of the peak — inside the declared 1e-5 also
  beyond the declared "до 1024 точек" (`out/01_…` (f), `out/01d_fp32_large_windows.txt`).
* **GPU 0 = CPU:** spectra evaluated on the device vs the host: rect 7e-17, Gaussian 2e-17, disc (cupyx `j1`) and a
  turned disc 1.7e-14; `propagate_plane` 3.7e-16 … 4.4e-13, `propagate_current` j 5.9e-13, P 1.7e-14; a NumPy-only
  Spectral fn falls back to the host (5.7e-17); the pool is returned (0 MB used after). Timings: a 256-row tilted
  slice at pad 4: GPU 0.08–0.9 s, CPU 3–5.5 s (`out/05_gpu.txt`).
* **`propagate_current` is right:** two interfering plane waves against the closed form: 1.0e-14, P exact (1.7e-16);
  propagating + evanescent (q = 1.5 k): 4.9e-15, P = L² exactly (no net flux from the evanescent part); the Gaussian
  against Im(U*∂U)/k from the exact Hankel integral and its exact derivatives at z = 0.05, 0.4, 3: ≤ 9.8e-8, j_r
  outward; the band-limited sum loses power with depth (P(40)/P(0) = 0.72), which v08 shows as information
  (`out/02_current.txt`). Sign and normalisation: a unit plane wave along n has j = n. For light this is the
  scalar-theory energy flux, as the README states.
* **v08 paths:** planes stay fixed under play, step, next_event (harness: 0 slice messages over 35 s of world time;
  browser: 6 s of play, 130 frames, 0 `slice` and 0 `planes` messages); "auto" along an axis normal moves 0.500 per
  0.5 s and wraps (4 wraps in 60 s, 3.8 expected); at most three planes, five malformed requests refused with
  reasons; removal and re-adding; the preview op changes no plane, slice or check (it adds one recorded `slice`
  message and updates the backend's "drawn" record); the reduced model only for |n_y| = 1 (a tilt of 0.05 → exact
  route), flagged in the header, the `modelling` message, the top bar (cleared when the plane is removed), the window
  (red) and the `reduced` check; NaN exactly outside the box (tests) (`out/04_v08_paths.txt`, `out/07_browser.txt`).
* **Player:** the scene shows the screen with its slits, the incident wave, the light behind the screen (two beams
  from the slits, their interference from above, the Fresnel fringes of the slit length from the side — consistent
  with windows 1–3), the energy current and the target (`out/07m_cloud_*.png`, `out/07h_…png`); five layers and each
  plane switch off one by one (`out/07_browser.txt` (9)); pointing at window 2 sets plane 2's highlight (1) and dims the
  others (opacity 0.45); a gizmo drag recomputes the slice; θ, φ by numbers give an exact checked slice (point check
  6.3e-5 ≤ 5.8e-4); a world from the record is read-only (plane controls disabled, no command sent after a drag and
  Delete; `out/07b_browser_views.txt`); no page errors.
* **Licence:** the five vendored files are byte-identical to the npm package `three@0.185.1` (tarball sha512 equal to
  the registry's integrity; published 2026-07-01T14:04:30Z as recorded; MIT); no other files in the vendor folder; both
  NOTICE files name it; no third-party licence markers in the player's own files; the colour-map stops in
  `scene3d.js` predate this pass (v02, v03, v05 at HEAD) (`out/06_licence.txt`).
* **Docs:** the owner's quote is identical in `AGENTS.md` §1 and `PLAN.md` §0; the CUDA decision is recorded in
  AGENTS §3 rule 8, `dependencies.md` §3 and PLAN; B2 not started; P14 and B2 notes added.
* **Tests in the image:** CPU — `test_planes_and_current`, `test_aperture_fields`, `test_backend`,
  `test_geometry_3d`, `test_licences`, `test_boundary`, v08's tests and the server's view test: 109 passed, 6 skipped
  (GPU-only) in 201 s (`out/08_test_suite_cpu.txt`); GPU 0 — `test_backend`, `test_planes_and_current`, v08's GPU
  test: 21 passed (`out/08_test_suite_gpu.txt`). The defects above pass these suites.

## Gaps against the owner's corrections (2026-10-27, verbatim in `../../AGENTS.md` §1)

| requirement | state | evidence |
|---|---|---|
| slices fixed; moving by itself only as an option, off by default; for all visualizations | **met**, with C3 (auto stalls on tilted planes) and C7 (a new world resets the planes) | 0 slice messages during play; `auto` false by default; RULES §2.10 for every visualization (v08 is the only 3-D world) |
| full 3-D: the screen with its slits, the beams, the target | **met** | `out/07m_cloud_iso/side/top/beam.png`; with three planes the cloud is mostly hidden behind them (`out/07b_three_planes.png`), the layers fix that |
| a window with the slice next to the 3-D view; appears at once when a plane is added | **met** | three windows beside the scene, «считается…» then the slice |
| a plane in 3-D at any angle, not three fixed projections | **met** | `propagate_plane` exact for any orientation (≤ 7e-14 against the volume and the same sum) |
| turned by hand like in 3-D editors and by parameters | **met**, with C10 (roll ring undone, in-plane arrows) and C2 (labels after a move) | gizmo drag recomputes; θ, φ, centre by numbers |
| up to three planes, each with its own window | **met** | ids 1–3, the fourth refused |
| selecting a window highlights its plane | **met** | hover: highlight 1, others dimmed |
| every element switched off on its own | **met** | 5 layers + each plane |
| new slices in the middle at 90° to each other | **partly** (C5) | perpendicular only to the default planes |
| learn from similar products, copy nothing restricted | **met** | three.js MIT unmodified and recorded; UI conventions described, not copied |
| convenient, informative, a full 3-D research environment | **partly** | C1 (stated accuracy not reached in band-limited worlds), C2 (axes), C6 (record), C7; only v08 uses the environment (STATUS V24 e) |
| CUDA libraries allowed | **recorded** | AGENTS §3 rule 8, `dependencies.md` §3, PLAN §0 |

## Scripts and outputs

| script | device | what | output |
|---|---|---|---|
| `common_rev.py` | — | helper: brute-force sum point by point, turned frames | — |
| `01_plane_vs_routes.py` | CPU (~4 min) | propagate_plane vs the volume at nodes (4 families, 5 tilts, even/odd n, both sums, sampled sources); vs brute force at any azimuth; corners and modulo; NaN; fp32; the recurrence | `out/01_plane_vs_routes.txt` |
| `01b_turn90_nyquist.py` | CPU | 90° turn vs the volume by depth, symmetric and asymmetric apertures (the Nyquist line) | `out/01b_turn90_nyquist.txt` |
| `01c_turned_vs_volume_v08.py` | GPU 0 | v08 default: turned slice vs the volume's own sum and vs exact (C9) | `out/01c_turned_vs_volume_v08.txt` |
| `01d_fp32_large_windows.py` | GPU 0 | fp32 vs fp64 at 1024–4096 points per axis | `out/01d_fp32_large_windows.txt` |
| `02_current.py` | CPU | current vs closed forms and exact derivatives; the flux check against a wrong window (C4) | `out/02_current.txt` |
| `03_turned_window.py` | GPU 0 | turned windows: inside the crop vs the box corners, vs a 4× window and exact | `out/03_turned_window.txt` |
| `03b_error_vs_depth.py` | GPU 0 + CPU | presets: the drawn slice's error by depth vs exact, the real run's checks (C1) | `out/03b_error_vs_depth.txt` |
| `03c_bandlimit_depth_sweep.py` | GPU 0 | ten worlds: which sum, error by depth vs the z_max estimate (C1) | `out/03c_bandlimit_depth_sweep.txt` |
| `04_v08_paths.py` | CPU (~35 min) | Runner: fixed planes, auto and clipping, limits, preview, reduced flags, origin outside, check ids, record size | `out/04_v08_paths.txt` |
| `05_gpu.py` | GPU 0 | spectra on the device, plane and current GPU vs CPU, host fallback, timings | `out/05_gpu.txt` |
| `06_licence.py` | network (npm registry, no contact parameters) | vendored three.js vs the published package, NOTICE, markers | `out/06_licence.txt` |
| `07_browser.mjs` | own server, Chromium | layers, fixed planes in play, adding, highlight, centre by numbers, θ/φ, gizmo drag, each layer off, removal, add after a turn, new world and the archived one, slices-only flags | `out/07_browser.txt`, `out/07a…07l_*.png`, `out/07_runs_meta.txt` |
| `07b_browser_views.mjs` | own server, Chromium | the cloud alone from four views; the archived world's controls | `out/07b_browser_views.txt`, `out/07m_cloud_*.png`, `out/07n_archived_selected.png` |
| `07c_window_axes.mjs` | own server, Chromium | window axis names and ticks vs the readout (C2) | `out/07c_window_axes.txt`, `out/07o_axes_case*.png` |
| test suites | CPU, GPU 0 | `pytest -p no:cacheprovider` in the image | `out/08_test_suite_cpu.txt`, `out/08_test_suite_gpu.txt` |

Browser runs: `docker run --rm --init --shm-size=2g --network host --user 1000:1000 -e HOME=/tmp -v <playwright node_modules>:/pw:ro -v <this folder>:/rev mcr.microsoft.com/playwright:v1.58.2-jammy node /rev/07_browser.mjs`
against the reviewer's server started as in "Environment".
