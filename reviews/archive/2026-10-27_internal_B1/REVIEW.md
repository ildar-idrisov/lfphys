# Review of batch B1 (plan items P10, P11, P12 and the demonstration v08_wave_3d)

**Status: awaiting processing.** (Reviewer: an independent internal subagent; it does not process this review —
`../README.md`, `../../AGENTS.md` §3 rule 6.)

Delivered: 2026-10-27.

## Scope

* P10 — `lfphys/lfphys/core/geometry.py`, `lfphys/lfphys/core/optics/angular_spectrum.py`, `lfphys/tests/test_geometry_3d.py`.
* P11 — `lfphys/lfphys/core/backend.py`, `lfphys/tests/test_backend.py`, `visualizations/server/lfviz/devices.py`, the
  settings routes in `visualizations/server/lfviz/app.py`, `runs.py`, `worker.py`, `sim.py`, `player/settings.html`,
  `player/js/settings.js`, the run-info row of `player/js/player.js`, `visualizations/docker/*`.
* P12 — `lfphys/sources/dependencies.md`, `lfphys/tests/test_licences.py`, `../../AGENTS.md` §3 rule 8.
* The demonstration `visualizations/v08_wave_3d/` (viz.py, web/view.js, tests).

## Environment

* Image `light-funnel-viz:latest` (a2b648cf48c7), Python 3.11, numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0, CuPy 14.2.0
  with the NVIDIA CUDA 12.9 wheels; host driver 550, RTX 2080 Ti.
* Every script here runs in that image from `engine/` mounted at `/lf`, working directory this folder:
  `docker run --rm --user 1000:1000 -v <engine>:/lf -w /lf/reviews/2026-10-27_internal_B1 -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests light-funnel-viz python3 NN_<name>.py`;
  GPU scripts add `--gpus '"device=0"'` (GPU 0 only, runs of seconds). Outputs are in `out/NN_<name>.txt`.
* The shared server `lf-viz` was only read (GET). The settings API was exercised in-process with
  `aiohttp.test_utils.TestClient` and `lfviz.devices.SETTINGS_FILE` patched to a temporary file.

## Findings

(IDs B1-1, B1-2, …; severity error / should-fix / nit; status tag as `../../AGENTS.md` §3 rule 11 asks.)

| ID | severity | tag | in one line |
|---|---|---|---|
| B1-1 | error | [error in earlier] | v08 window too small: allowed world off by 31 % of the peak at z_max, defaults 0.4–0.6 % (14 % of log-view pixels > 0.1 decade); no check sees it; README claim false |
| B1-2 | should-fix | [weakens] | default `double` and all slit/square worlds have no accuracy check (grid error 2.5 % on the y = 0 slice); help says «точно» |
| B1-3 | error | [error in earlier] | `propagate_slice` one sample off for odd n with padding (4e-2 error); test not independent; `Grid.uniform` convention differs for odd n |
| B1-4 | error | [error in earlier] | header and `device` check report fp64 while the drawn volume is fp32 (`used()` keeps only the last call) |
| B1-5 | error | [error in earlier] | with the offered fp32, `slice_route` compares fp32 data at fp64 tolerance and fails in every full-volume world |
| B1-6 | should-fix | [error in earlier] | fp32 bound 1e-5 exceeded in v08's range (1.2e-5 at k·z = 1676); phase in fp64 gives 1.6e-7 |
| B1-7 | should-fix | [weakens] | GPU out of memory → world not built, no CPU fallback; pool held per worker (0.27–0.65 GiB) |
| B1-8 | should-fix | [weakens] | GPU-0-only outside the container relies on FASTEST_FIRST order; set `CUDA_DEVICE_ORDER=PCI_BUS_ID`, check PCI id |
| B1-9 | should-fix | [weakens] | any UID ≠ 1000 → CuPy cache `/.cupy` unwritable → GPU silently lost |
| B1-10 | should-fix | [weakens] | `PUT /api/settings`: 500 with traceback, `kernels: []` wipes settings, `true` accepted as crossover, 150 kB → 500 E2BIG |
| B1-11 | nit | [neutral] | settings writes not serialised: older PUT can win; a PUT in flight drops a calibration |
| B1-12 | should-fix | [error in earlier] | approximate slice labelled «точный срез без объёма»; `Modelling` cannot mark one plane approximate; run list/top bar do not flag approximations |
| B1-13 | should-fix | [weakens] | Gaussian reference off by 2.9e-6 (290× its 1e-8 tolerance) at λ = 0.3, w = 0.5, z = 80; tolerance not derived; truncated beams drawn as Gaussian |
| B1-14 | nit | [neutral] | z < 0 accepted, evanescent part amplified ×884 |
| B1-15 | nit | [neutral] | "exact" wording for the slice route (exact only for the sampled band-limited field) |
| B1-16 | nit | [neutral] | `Plane(...)` default name 'xy' for any axes; `slice_field` IndexError on a one-node axis |
| B1-17 | nit | [error in earlier] | `configure()` never notes "GPU asked for but not usable", as its docstring and the player promise |
| B1-18 | nit | [neutral] | v08 holds physics references (Gaussian, RS-I circle) that belong in the engine; no `engine/` folder |

### B1-1 — error — v08 draws materially wrong fields in allowed worlds, and no check sees it (window / periodic copies)

* **Location:** `visualizations/v08_wave_3d/viz.py:149` (pad 2 or 4 from `half >= 0.6·z_max`), `viz.py:242-281`
  (checks), `v08_wave_3d/README.md:45` («The window is padded … so that the periodic copies of the field do not reach
  the region shown»).
* **What is wrong.** The angular spectrum on a padded grid gives the field of the *periodic* array of apertures (period
  = padded window). Wide-angle light from sharp edges reaches the neighbouring copies long before the geometric rule
  `half >= 0.6 z_max` says. The drawn field carries that error, and none of the checks can see it: `slice_route`
  compares two routes with the **same** padding (common-mode), `gauss_axis` and `circle_axis` are separate
  computations (pad 4, `check=True`; the circle only at z ≤ 0.6·half), and slit / double slit / square worlds have no
  accuracy check at all (B1-2).
* **Evidence.**
  * `03d_extreme_unchecked.py` → `out/03d_extreme_unchecked.txt`: an allowed world (double slit, a = 0.2 µm,
    λ = 1.5 µm, n = 128, z_max = 80 µm; pad 4 chosen by the run): the plane z = z_max differs from the same
    propagation in a ×16 window by **31 % of its peak** (drawn peak 1.166 × the true one); every check passes
    (`slice_route` 1.2e-15).
  * `03_v08_drawn_vs_wide_window.py` → `out/03_…txt`, presets as shipped: linear errors 3.5e-3 … 6.4e-3 of the peak
    (double, circle); on the player's six-decade log scale, for the default preset `double`, **13.9 % of the pixels**
    of the plane z = z_max (above 1e-6 of the peak) are off by more than 0.1 decade, worst 2.5 decades.
    `03b_window_convergence.py`: the ×16 reference is converged (pad 16 vs 32: 6.4e-5; pad 8 vs 32: 6.6e-4; pad 4 vs
    32: 5.2e-3, 14 % of log pixels off).
* **Fix.** Choose the window from the angular content, not from geometry: the propagating spectrum reaches angles up
  to ~90°, so either (a) use the band-limited angular spectrum (Matsushima & Shimobaba, Opt. Express 17, 19662 (2009):
  zero the transfer function beyond the frequency whose sampled phase aliases for the given window and z), or (b) grow
  the pad until a cheap window check passes. In any case emit a check on what is drawn: the deepest drawn plane
  against the same plane with the pad doubled (one extra FFT pair), tolerance = the drawing's needs (e.g. 1e-3 of the
  peak for the linear view; state that the log view is reliable only above that level). Withdraw the README sentence.

### B1-2 — should-fix — the default world (`double`) and all slit / square worlds have no accuracy check; the help says «точно»

* **Location:** `viz.py:242-281` (checks exist only for `gauss`, `circle`, the route equality and the reduced-model
  information), `web/view.js:145` («Поле посчитано точно»), `viz.py:345-348`.
* **What is wrong.** The rules require a check for every quantity with a closed form or a second method
  (`RULES.md` §2.5, §2.7). For sharp apertures the result's accuracy is limited by the staircase / sampling of the
  edges (n = 256, dx = λ/4); the circle check measures it (≈ 1–3 % on the axis, `out/02_v08_circle_check.txt`), but
  the default preset and the square / slit sources carry the same error unmeasured.
* **Evidence.** `03c_grid_error_double.py` → `out/03c_grid_error_double.txt`: the default `double` world against the
  same window with half the step (both padded ×8): plane z = z_max 3.6e-3 of the peak, **y = 0 slice 2.5e-2**; square
  (a = 2, n = 256): 1.0e-3 and 1.6e-2.
* **Fix.** Generalise `circle_axis`'s measured tolerance to every source: emit "grid error" = 2·|U_n − U_2n| on a few
  points of the drawn slices (cheap at a single z) and show it; for the rectangle-type apertures a second method exists
  (the RS-I integral over the rectangle on the axis by 2-D quadrature). Replace «точно» by the measured accuracy.

### B1-3 — error — `propagate_slice` returns the wrong plane for an odd number of points when the window is padded

* **Location:** `lfphys/lfphys/core/optics/angular_spectrum.py:79` (`off = (m - n) // 2`), used by `propagate_slice`
  at an absolute position `at` (`:110-127`); docstring `:14` («as `Grid.uniform`»).
* **What is wrong.** The buffer index j sits at x = (j − m//2)·d after `ifftshift`; sample i of U0 is put at
  j = off + i. For odd n and even m (any pad > 1), off = (m − n − 1)/2, so sample i sits at (i − n//2 − 1)·d, one
  sample away from the stated convention x_i = (i − n//2)·d. `propagate_field` / `propagate_volume` are unaffected
  (output is cropped back the same way); `propagate_slice(at=…)` evaluates the plane one step off. v08 uses even n, so
  it is not affected; the engine API is. The test `test_slices_without_the_volume_equal_the_volume_and_interpolate_exactly`
  re-implements the same placement, so it cannot catch this (not independent), and it uses even n only.
  Also, `Grid.uniform` for odd n puts nodes at half-integers ([-2.5 … 1.5] for n = 5), unlike the convention the
  angular-spectrum docstring says it shares (`out/10_geometry_edges.txt` (a)).
* **Evidence.** `01_as_conventions.py` (a) → `out/01_as_conventions.txt`: n = 65, pad 2: max |slice(x = 0) − volume
  column x = 0| = **4.1e-2**, error against an independent Hankel quadrature (mpmath, J0) **3.6e-2**, while the volume
  route is right to 9.6e-9; n = 64 or pad 1: 1e-16 / 3e-8. `01b_odd_n_fix.py`: with `off = m//2 − n//2` the slice is
  right to 9.6e-9.
* **Fix.** `off = m // 2 - n // 2` per axis; add odd-n cases and an independent off-axis reference (as in script 01)
  to the tests; make `Grid.uniform` and the angular-spectrum convention agree (or state the difference).

### B1-4 — error — the run's header and the `device` check misreport the precision (and can misreport the device) of what is drawn

* **Location:** `lfphys/lfphys/core/backend.py:220` (`_USED[name] = …`: one entry per kernel, overwritten by every
  call), `visualizations/server/lfviz/sim.py:103-110, 228` (header takes `used()` after the world is built),
  `v08_wave_3d/viz.py:277-280` (`device` check reads `used()` after the checks).
* **What is wrong.** v08 computes the drawn volume with the owner's precision and then its checks with `check=True`
  (fp64). `used()` keeps only the last call, so the header (P11: "every run records its devices and precisions in its
  header") and the `device` check report fp64 while the drawn field is fp32. The same overwrite hides the device of
  the drawn data whenever a check runs elsewhere (e.g. the reduced 1-D model in `double_slices` runs on the CPU, the
  later checks on the GPU; only the last is recorded).
* **Evidence.** `04_fp32.py` (b) → `out/04_fp32.txt`, settings fp32 / CPU: header `backend.used` =
  `{'device': 'cpu', 'precision': 'fp64', …}`, check label «Угловой спектр считался на CPU (fp64)», drawn volume dtype
  `complex64` (presets `double` and `gauss`).
* **Fix.** Record every call with its purpose (`check=True` → "check", else "drawn") and size, e.g.
  `used()[kernel] = {"drawn": {…}, "check": {…}}` (or a list), and show the drawn one in the header, the info row and
  the `device` check.

### B1-5 — error — fp32 enters a check: with the offered fp32 every full-volume v08 world fails `slice_route`

* **Location:** `v08_wave_3d/viz.py:265-270`; policy text `backend.py:13-15`, `RULES.md` §5 («References and checks
  always run in fp64»), `lfphys/PLAN.md` P11 («fp32 … only where a validation table shows that the kernel's checks
  still hold»).
* **What is wrong.** `slice_route` compares the fp64 slice (`check=True`) with the drawn volume, which is fp32 when the
  owner picks fp32, under the fp64 tolerance 1e-9. So an fp32 operand enters a check, and the check fails for a setting
  the settings page offers as validated.
* **Evidence.** `out/04_fp32.txt` (b): `slice_route` value 4.8e-7 (double) / 2.9e-7 (gauss), tol 1e-9, ok = False.
* **Fix.** Either compare two fp64 routes (recompute the compared row with `propagate_field(…, check=True)` at a few
  z), or compare the drawn data against fp64 with the kernel's declared fp32 bound as tolerance and say so in the
  note. Add a v08 test with fp32 settings (all non-info checks pass).

### B1-6 — should-fix — the declared fp32 bound (1e-5) does not hold over v08's own range; the error grows with k·z

* **Location:** `angular_spectrum.py:58-60` (bound 1e-5, evidence `test_angular_spectrum_fp32_within_its_bound`),
  `:96-98, 123` (phase `kz * zz` formed in the working precision), `lfphys/tests/test_backend.py:92-108` (validated
  only at λ = 1, z ≤ 8, i.e. k·z ≤ 50 rad).
* **What is wrong.** In fp32 the phase k_z·z carries a relative error ~6e-8, i.e. an absolute phase error ∝ k·z.
  v08 allows λ = 0.3 µm and z = 80 µm (k·z = 1676 rad).
* **Evidence.** `out/04_fp32.txt` (a): double slit, λ = 0.3, z = 80: **1.2e-5** (CPU); `out/05_gpu.txt` (d): **1.2e-5**
  on the GPU; the error rises 9.5e-8 → 1.1e-6 → 3.3e-6 → 1.2e-5 for k·z = 21 → 209 → 628 → 1676.
  `04b_fp32_phase_in_fp64.py`: forming exp(i k_z z) in fp64 and casting it to complex64 (FFTs still fp32) gives
  **1.6e-7**, independent of z (kernel's way: 1.8e-5).
* **Fix.** Build the phase factor in fp64 and cast (cost: one fp64 exp per z on the device); validate the bound over
  the domain the kernel is offered for and store that domain next to the bound (`precisions["fp32"]["domain"]`).

### B1-7 — should-fix — no fallback when GPU memory runs out; each worker keeps its CuPy pool for its lifetime

* **Location:** `backend.py:193-221` (`choose`), `angular_spectrum.py:67-127` (no `OutOfMemoryError` handling, no
  pool release), `visualizations/server/lfviz/worker.py:79-86`.
* **What is wrong.** GPU 0 is shared with the owner's services (`PLAN.md` P11 names this constraint). When the card is
  full, the kernel raises `OutOfMemoryError` and the world is not built («Мир не создан»), although the CPU could do
  it. The pool is never released, so an idle run keeps its memory.
* **Evidence.** `05_gpu.py` (e) → `out/05_gpu.txt`: with the CuPy pool limited to 64 MiB the default world raises
  `OutOfMemoryError … allocating 16,777,216 bytes` (no fallback). (b): per worker, the CUDA context adds 162 MiB;
  after the full-volume world (n = 256, pad 4) the GPU holds +266 MiB (pool 97 MiB, 0 in use); after the 512-grid
  slices world +650 MiB (pool 481 MiB, 0 in use). So 3 concurrent runs (`--max-workers 3`) need ≈ 0.8–2 GiB: they fit
  today (GPU 0: 217 MiB used of 11 GiB), not when the owner's ComfyUI holds most of the card. Observed independently
  at the end of the review (read-only `nvidia-smi --query-compute-apps`): a `lfviz.worker --viz v08_wave_3d` of the
  shared server (not started by this review) held 650 MiB on GPU 0 thirteen minutes after its start.
* **Fix.** In the kernel: on `cupy.cuda.memory.OutOfMemoryError` free the pool and redo the call on the CPU, recording
  the reason in `used()`; call `free_all_blocks()` after a kernel (or set a per-worker pool limit); in "auto", compare
  the kernel's footprint (≈ 6 × m × 16 B for complex128) with `memGetInfo()` before choosing the GPU.

### B1-8 — should-fix — "GPU 0 only" outside the container rests on CUDA's default device order, which is not the PCI order

* **Location:** `backend.py:108-109` (sets only `CUDA_VISIBLE_DEVICES=0`), docstring `:17-18`.
* **What is wrong.** `CUDA_VISIBLE_DEVICES` indexes CUDA's enumeration, whose default is FASTEST_FIRST. NVIDIA, CUDA
  Programming Guide §5.2.1.2 (fetched 2026-10-27, `out/12_cuda_device_order_doc.txt`): «FASTEST_FIRST : The available
  devices are enumerated from fastest to slowest using a simple heuristic (default). PCI_BUS_ID : The available devices
  are enumerated by PCI bus ID in ascending order.» The documentation does not say how the heuristic orders two
  identical RTX 2080 Ti, so nothing guarantees that CUDA's device 0 is nvidia-smi's GPU 0; on a bare host or in a
  container started with `--gpus all` the faulty card (nvidia-smi index 1, PCI 0000:03:00.0) may be used. Inside the shipped compose service (`device_ids: ["0"]`) and with
  `--gpus '"device=0"'` the right card is used: CUDA device 0 has PCI bus id 0000:01:00.0 (`out/05_gpu.txt` (a)),
  which is nvidia-smi's GPU 0. (Not demonstrated on the host: the review did not touch GPU 1.)
* **Fix.** Also set `CUDA_DEVICE_ORDER=PCI_BUS_ID` when unset, and before use compare `Device(0).pci_bus_id` with an
  expected id (e.g. `LFPHYS_GPU_PCI`, default 0000:01:00.0 on this host); refuse the GPU otherwise.

### B1-9 — should-fix — the GPU is silently lost when the container runs as a user without a home directory

* **Location:** `visualizations/docker/Dockerfile` (no `CUPY_CACHE_DIR`), `docker-compose.yml` (`user:
  "${UID:-1000}:${GID:-1000}"`).
* **What is wrong.** CuPy compiles its elementwise kernels and caches them under `$HOME/.cupy`. For any UID other than
  1000 the image has no passwd entry, `HOME=/`, the cache cannot be created, and the backend's probe reports the GPU as
  unavailable; everything runs on the CPU with no notice except the reason string.
* **Evidence.** `06_cpu_fallback.py`, case 3 → `out/06_cpu_fallback.txt`: `--gpus '"device=0"' --user 1234:1234` →
  `PermissionError: [Errno 13] Permission denied: '/.cupy'`, GPU unavailable.
* **Fix.** `ENV CUPY_CACHE_DIR=/tmp/cupy-kernel-cache` in the Dockerfile (or a git-ignored folder in the mount).

### B1-10 — should-fix — `PUT /api/settings` does not validate the shape of its input

* **Location:** `visualizations/server/lfviz/app.py:220-236`, `devices.py:71-78` (settings passed as one argv
  string), `backend.py:144-173` (`configure`).
* **Evidence.** `07_settings_api.py` part 1 → `out/07_settings_api.txt` (in-process, temporary settings file):
  * `{"kernels": {"optics.angular_spectrum": "gpu"}}` → **HTTP 500** whose error text is a Python traceback;
  * `{"kernels": []}` → HTTP 200 and **all kernel settings silently wiped** (file: `kernels={}`);
  * `{"crossover": {"optics.angular_spectrum": true}}` → accepted and saved (`isinstance(True, int)`): "auto" then
    takes the GPU from size 1; `-5` and `"big"` are dropped without a note;
  * a 150 kB body (allowed up to 4 MB) → HTTP 500 «Argument list too long» (one argv string is limited to 128 KiB).
* **Fix.** Validate in the server before the subprocess (kernels: object of objects with string `device` /
  `precision`; crossover: positive int, not bool, or null) and answer 400 with the reason; pass the JSON to the engine
  on stdin; never return a traceback to the browser.

### B1-11 — nit — settings writes are not serialised (lost updates)

* **Location:** `app.py:220-243`, `devices.py:81-92`, `player/js/settings.js:109-119` (each change sends a PUT built
  from the state before the previous answer arrived).
* **Evidence.** `out/07_settings_api.txt` part 2 (engine subprocess stubbed with controlled delays; the real one takes
  a variable 0.3–1 s): (a) PUT gpu (slow) then PUT cpu (fast) → file ends with **gpu**, the older choice; (b) a PUT in
  flight while «Измерить заново» completes → the calibration and its crossovers are **lost** (`crossover = {}`,
  `calibration` gone).
* **Fix.** An `asyncio.Lock` around load → validate → save in `devices` (and around calibrate); the page sends one
  change at a time.

### B1-12 — should-fix — approximation flagging in v08: the approximate slice is labelled "exact route"; per-plane exactness is not representable

* **Location:** `v08_wave_3d/viz.py:226` (`"exact_route": self.vol is None`), `web/view.js:134`;
  `lfphys/lfphys/core/geometry.py:206-241` (`Modelling` has one `exact` flag for all planes); the run list
  (`/api/runs` entries carry `modifications` but nothing about approximations).
* **What is wrong.** (a) In the world `double_slices` the y = 0 slice is the reduced 2-D model, yet the «Срез» panel
  says «маршрут: точный срез без объёма» next to the red «ПРИБЛИЖЕНИЕ» banner (screenshot
  `out/v08_double_slices.png`, own server instance on port 8499, CPU). (b) The «Моделирование» note says all chosen
  slices are computed «упрощённой моделью», though x = 0 and z = z_max are exact: `Modelling` cannot say which plane is
  approximate. (c) The owner asked «помечать там, где это приближение»: a run with an approximate slice is not flagged
  in the run list, the passport or the top bar (which shows «стандартная физика»).
* **Fix.** `Modelling.planes` as a list of (plane, exact, reason); `exact_route` true only for slices computed by
  `propagate_slice`/the volume; an `approximations` list in the header and the passport, shown in the run list and the
  top bar like `modifications`.

### B1-13 — should-fix — v08's Gaussian reference is not converged at large k·z, and its tolerance is not derived

* **Location:** `v08_wave_3d/viz.py:119-126` (`mp.quad(f1, [0, k/2, k])`), `:246-251` (fixed `tol=1e-8`); the same
  reference in `lfphys/tests/test_geometry_3d.py:82-91` (used there only at k·z ≤ 63, where it is fine).
* **Evidence.** `11b_gauss_reference.py` → `out/11b_gauss_reference.txt`, λ = 0.3, w = 0.5, z = 80 (allowed):
  v08's split is off by **2.9e-6** (290× the tolerance) against both composite Gauss–Legendre (4000 vs 16000 panels
  agree to 8e-15) and mpmath on 64 panels (1.0e-14). In that world the FFT route with pad 4 is also off by 4.1e-6
  (window, B1-1; pad 16: 1.9e-12), so the check's FAIL is right for a mixed reason. `11_gauss_check_sweep.py`:
  further allowed worlds fail because the Gaussian is truncated by the window (amplitude 0.53, 0.17, 0.077 at the edge)
  or wrapped (λ = 1.5, w = 0.5, z = 80, n = 128: error 0.29) — honest failures, but the run still draws and labels the
  field as a Gaussian beam.
* **Fix.** Split the quadrature into panels per oscillation of z(k − k_z) (or `mp.quad(…, error=True)` and refuse a
  reference whose error estimate exceeds tol/10); derive the tolerance (pad doubling, as for the circle); refuse
  worlds whose Gaussian exceeds ~1e-12 at the window edge (as n = 512 full 3-D is refused).

### B1-14 — nit — negative z is accepted and amplifies evanescent components

* **Location:** `angular_spectrum.py:84-85, 90-99`.
* **Evidence.** `out/01_as_conventions.txt` (d): slit, z = −λ: max |U| = **884** (|U(0)| ≤ 1), no error.
* **Fix.** Refuse z < 0, or drop |k_t| > k for z < 0 and say so (back-propagation is then not exact).

### B1-15 — nit — "exact" wording of the slice route

* **Location:** `angular_spectrum.py:16-19, 35-38, 112-113` («exact … which is exact», «точные продольные срезы»),
  `geometry.py:15-16`, v08 README («each exact»).
* **What is wrong.** Between nodes the slice is the trigonometric interpolant of the sampled field: exact for a
  band-limited periodic field, not for the physical field of a sharp aperture near the aperture. Mode (b) is "exact" in
  the sense "identical to mode (a) on the same grid", which is what v08 means; the wording suggests more.
* **Evidence.** `out/01_as_conventions.txt` (b): band-limited Gaussian, off-node: 1.7e-8 … 3.4e-8 against the
  independent reference (good); (c): slit edge at z = 0, half a step outside the edge: |U| = 0.18 where the field is 0
  (Gibbs), at z = λ/4 differences 1–3e-2 against the twice finer grid.
* **Fix.** «exact for the sampled, band-limited field; identical to the volume route; accuracy against the physical
  field = the grid and window errors (measured by …)».

### B1-16 — nit — geometry edge cases

* **Location:** `geometry.py:46-52, 160-198`.
* **Evidence.** `out/10_geometry_edges.txt`: (b) `Plane((0,0,0), (1,0,0), (0,0,1))` keeps the default name `'xy'`
  although it is the xz plane (the view labels planes by name); (c) `slice_field` on a grid with one node along an
  axis raises `IndexError` (`ax[1] - ax[0]`).
* **Fix.** Default `name="custom"` (or derive it from the axes); require ≥ 2 nodes per axis with a clear message.

### B1-17 — nit — `configure()` never gives the note "GPU asked for but not usable" that its docstring and the player promise

* **Location:** `backend.py:144-173` (docstring: «notes about … a GPU asked for but not usable»), `player/js/player.js:294`.
* **Evidence.** `out/06_cpu_fallback.txt`, all three set-ups (no GPU; `LFPHYS_NO_GPU=1`; unwritable CuPy cache):
  `configure(device = gpu)` → notes `[]`, header `backend.notes` `[]`; only `used().reason` says it.
* **Fix.** In `configure`, when device is "gpu" and `_cupy()` reports no GPU, add the note.

### B1-18 — nit — v08 holds physics references the engine should own, and has no `engine/` folder

* **Location:** `v08_wave_3d/viz.py:119-126` (`_gauss_on_axis`, a copy of the one in `lfphys/tests/test_geometry_3d.py`),
  `viz.py:255-256` (RS-I on-axis closed form); `RULES.md` §1 (folder contract with `engine/`; «Physics a visualization
  needs and the engine lacks is added to the engine, with its tests»).
* **Fix.** Move the two on-axis references into `lfphys.core.optics` with tests; keep the aperture sampling in
  `v08_wave_3d/engine/`.

## Verified correct (with the precision reached)

* **Angular spectrum, conventions and exactness on the grid.** k_z = √(k² − k_t²) with Im k_z ≥ 0 (decay for z > 0),
  e^{+i k_z z} with e^{−iωt}; the forward/inverse FFT pair normalises correctly; given values on z = 0 this is the
  Rayleigh–Sommerfeld-I (Dirichlet) solution. Against independent quadratures (no FFT): Gaussian on the axis
  1.5e-14 (λ = 0.5, w = 1.5, z = 30, n = 256, pad 4; `out/11_…`), 1.9e-12 for the hard case λ = 0.3, w = 0.5, z = 80
  once the window is wide enough (pad 16; `out/11b_…`); Gaussian off the axis (Hankel, J0) 3e-8 … 2e-7 on a 64-point
  grid (`out/01_…` (a)); between nodes 1.7e-8 … 3.4e-8 for a band-limited field (`out/01_…` (b)). Slice route = volume
  route to 1e-16 for even n (and for odd n with pad 1).
* **The circle check is honest.** The RS-I on-axis form e^{ikz} − (z/R) e^{ikR} is the exact solution for these
  boundary values (unit field on the disc, zero outside, given on z = 0), which is what the angular spectrum solves. In
  8 configurations over the schema's range the true error |U_n − ref| (2.6e-4 … 2.6e-2) stays below the run's
  tolerance 2|U_n − U_2n| + 1e-6; the observed ratio err/|U_n − U_2n| = 1.3–1.5 means convergence of order ≈ 1.3–1.6,
  for which the factor 2 (valid for order ≥ 1) is justified; the periodic-copy part (pad 4 vs 16) is 3e-4 … 2e-3,
  below the tolerance at the check's depth (`out/02_v08_circle_check.txt`). Its weakness is coverage, not honesty
  (B1-1, B1-2).
* **Reduced 2-D model** of a finite slit: the error is measured against the exact slice and falls with the slit length
  (tests pass; the preset shows 0.155 of the peak for L = 8 µm, flagged ≈ «ПРИБЛИЖЕНИЕ» in the checks, a red banner and
  a red plane in the sketch: `out/v08_double_slices.png`), apart from the labels in B1-12.
* **Geometry.** Presets, `from_normal`, `to3d`/`to2d`, `rotation_between` (R u1 = u2, R n1 = n2, det 1) and
  `angle_between` are correct; `same_as` ignores in-plane orientation as documented. The trilinear bound
  Σ h_d² max|∂_d² f|/8 is right (tensor-product argument with the integral form of the remainder, valid for complex
  fields) and nearly tight: complex plane wave on a tilted plane, error 2.600e-2 against bound 2.625e-2
  (`out/10_geometry_edges.txt` (d)).
* **GPU = CPU** in fp64: v08 volumes 6.1e-16 (double), 3.8e-16 (circle) of the peak (`out/05_gpu.txt` (c)).
* **GPU 0 in the container:** with `--gpus '"device=0"'` (and the compose service's `device_ids: ["0"]`) CUDA device 0
  is PCI 0000:01:00.0 = nvidia-smi GPU 0 (`out/05_gpu.txt` (a)).
* **CPU fallback:** a container without `--gpus`, `LFPHYS_NO_GPU=1`, and an unusable CuPy all build v08 worlds on the
  CPU with every check passing (`out/06_cpu_fallback.txt`).
* **"Auto" and the calibration.** Calibration takes 1.5 s (no thermal concern; GPU 0 rose from 39 to 44 °C over
  script 05); crossover 16384 points (128²), speed-ups ×2.1 at 128² to ×8.8 at 2048², as the kernel's note states
  (`out/05_gpu.txt` (f)). The benchmark counts the field's transfers both ways; the k_z array's transfer is not in it
  (≈ 0.04 ms at the crossover against 0.28 ms of GPU time), which does not change any decision at the measured sizes.
  "auto" is applied to the padded size, which is what the FFTs cost.
* **References and checks forced to fp64:** every call with `check=True` runs in fp64 whatever the setting
  (`test_backend.py`, and the v08 calls at `viz.py:246, 257, 259, 266, 272`); the only leak is B1-5.
* **Settings page** (own server instance on port 8499, CPU, read-only engine mount; `out/settings_no_gpu.png`): renders
  with no page errors; "GPU" is disabled when no GPU is usable; CPU-only kernels offer only CPU / fp64; fp32 is offered
  only for the angular spectrum. Malformed JSON and a non-object body get 400 (`out/07_…`).
* **Licences** (`out/08_licences.txt`, `out/08b_eula_web.txt`): numpy, scipy, python-flint (MIT AND LGPL-3.0-or-later
  with FLINT 3.6.0, GMP 6.3.0, MPFR 4.2.2 in `python_flint.libs`), cupy-cuda12x (MIT, no foreign shared library),
  mpmath, cuda-toolkit (no licence, no code) are as `dependencies.md` states; all eight NVIDIA `License.txt` files are
  identical (one MD5) and contain the quoted §1.1.1, §1.1.2, §1.2, §1.6, §2.1, §2.3 sentences and the 2018 release
  dates; the CUDA 12.9 web EULA (fetched 2026-10-27) contains the OSI sentence and lists `libnvJitLink.so`, while the
  2018 text does not; neither lists `libcusolverMg` or `libnvrtc*.alt`. So the audit's §3.4 and STATUS V21 are right.
  **Platform-runtime category vs the owner's words:** the owner forbids libraries «с лицензиями закрытыми для
  коммерческого применения»; the CUDA EULA has no noncommercial or field-of-use limit (only «systems with NVIDIA GPUs»),
  and the engine's code contains no NVIDIA code and runs without it, so the exception is consistent with the verbatim
  rule (and needed for item 11's GPU). Note for the report: rule 8's "So: … One category is admitted as a platform
  runtime" is the implementer's reading written under the owner's heading; the owner has not stated it — worth one
  explicit confirmation in the B1 discussion.
* **Boundary and headers:** all 15 B1 source files carry the PolyForm SPDX line; no B1 file refers to research code,
  notes or knowledge-base items.
* **Tests in the image:** GPU subset (`--gpus '"device=0"'`): `lfphys/tests/test_backend.py` + `test_geometry_3d.py`
  20 passed; v08 tests + the server's device/settings tests 10 passed (`out/09_test_suite_gpu.txt`). Full CPU suites
  (no GPU given): `lfphys/tests` all passed (no failure, `-qq`), `visualizations/` 326 passed, 1 skipped (the GPU test)
  in 409 s (`out/09_test_suite_cpu.txt`). The defects above pass these suites: none of them is covered by a test.

## Gaps against the owner's request (items 10 and 11, verbatim in `lfphys/PLAN.md` §0)

**Item 10** — «возможность всех расчетов в 2-D и 3-D, для 2-D должна быть возможность выбора плоскости моделирования,
для 3-D возможность моделирования в выбранном 2-D срезе».

* Delivered: the geometry layer (`Plane`, `Grid`, `slice_field`, `Modelling`) and **one** computation that runs in
  2-D and 3-D, the scalar angular spectrum (transverse planes, the volume, longitudinal planes x = c / y = c), shown in
  one world (v08).
* Not delivered: «всех расчетов» — no other engine module is 2-D/3-D-capable or uses `Plane` (only v08 imports
  `core.geometry`); the existing 2-D worlds (v01, v02, v04, …) offer no choice of plane; PLAN P10's own verification
  «the existing 2-D results reproduced in every plane orientation» is not done (the tests check `Plane` round trips
  only).
* «для 2-D … выбор плоскости моделирования»: the `Plane` object exists, no model or world uses it to place a 2-D model
  (v08's reduced model is fixed in y = 0).
* «для 3-D … моделирование в выбранном 2-D срезе»: v08 offers three fixed planes (y = 0, x = 0, z = z_max), not a chosen
  one; the engine computes x = c, y = c, z = c directly but has no route for an oblique plane without the volume; in
  full 3-D v08 offers coordinate planes snapped to grid nodes only, although `slice_field` (oblique, with the error
  bound) exists — it is unused. Per-plane exactness cannot be expressed (B1-12).

**Item 11** — CPU and GPU, optimal by default, a settings page for devices and precision.

* Delivered: the backend (per-kernel auto / CPU / GPU, fp64 / fp32, calibration, CPU fallback), the settings page,
  the GPU-capable image and compose service, settings recorded in the passport and the header (with defect B1-4).
* Not delivered or not as planned: **per-run overrides** (PLAN P11: «global defaults and per-run overrides») — a run
  takes only the global file; the **validation table per precision** — one bound per kernel, validated in a narrow
  domain (B1-6) and contradicted by v08's own check (B1-5); **one GPU kernel only** — other heavy parts (v02's
  per-particle exact Fresnel amplitudes, STATUS V12: ≈ 18 particles/s; the ray fans of v01/v04) are neither GPU kernels
  nor listed as CPU-only with a measured reason; the CPU-only reasons are asserted, not measured (e.g.
  `quantum.schrodinger1d`: «на GPU медленнее»), and those four entries never call `choose()`, so their selects on the
  settings page change nothing; **GPU memory shared with other services** — not handled (B1-7); **a lowered power
  limit for long runs** — not implemented (no GPU job is long yet); fp16 not offered, with a stated but unmeasured
  reason (acceptable under «только необходимое»).
* Image: PLAN P11 named CUDA 12.6; the image has the CUDA 12.9 runtime wheels on the host's driver 550 (CUDA 12.4,
  `driver: 12040` in `out/05_gpu.txt`), i.e. it relies on CUDA minor-version compatibility. It works (all GPU tests
  pass), but the constraint is not recorded anywhere.

## Scripts and outputs

| script | device | what | output |
|---|---|---|---|
| `01_as_conventions.py` | CPU | grid convention (even/odd n, pad), off-node slice vs Hankel quadrature, Gibbs at a sharp edge, z < 0 | `out/01_as_conventions.txt` |
| `01b_odd_n_fix.py` | CPU | the suggested offset fix on a copy of the slice route | `out/01b_odd_n_fix.txt` |
| `02_v08_circle_check.py` | CPU | honesty of `circle_axis` over 8 configurations | `out/02_v08_circle_check.txt` |
| `03_v08_drawn_vs_wide_window.py` | CPU | drawn slices of the presets vs a ×16 window | `out/03_v08_drawn_vs_wide_window.txt` |
| `03b_window_convergence.py` | CPU | pad 4/8/16 vs 32 for the plane z = z_max of `double` | `out/03b_window_convergence.txt` |
| `03c_grid_error_double.py` | CPU | grid error n vs 2n of `double` and a square | `out/03c_grid_error_double.txt` |
| `03d_extreme_unchecked.py` | CPU | an allowed wide-angle world: drawn vs ×16 window, its checks | `out/03d_extreme_unchecked.txt` |
| `04_fp32.py` | CPU | fp32 error vs k·z; v08 worlds with fp32 settings (header, checks) | `out/04_fp32.txt` |
| `04b_fp32_phase_in_fp64.py` | CPU | source of the fp32 error; phase formed in fp64 | `out/04b_fp32_phase_in_fp64.txt` |
| `05_gpu.py` | GPU 0 (~20 s) | PCI id, memory per worker, GPU vs CPU, fp32 on GPU, OOM, calibration | `out/05_gpu.txt` |
| `06_cpu_fallback.py` | CPU / GPU 0 | no GPU, `LFPHYS_NO_GPU=1`, UID without home | `out/06_cpu_fallback.txt` |
| `07_settings_api.py` | CPU | PUT validation (real engine), concurrent writes (stubbed delays), temp settings file | `out/07_settings_api.txt` |
| `08_licences.py` | CPU | installed licence metadata, bundled libraries, NVIDIA `License.txt` quotes | `out/08_licences.txt` |
| (inline, `out/08b_eula_web.txt`) | — | the CUDA 12.9 web EULA, fetched 2026-10-27, grepped for the quoted sentences | `out/eula/cuda129_eula.html` |
| (inline, `out/12_cuda_device_order_doc.txt`) | — | CUDA Programming Guide §5.2.1.2, fetched 2026-10-27 | `out/cuda_env/environment-variables.html` |
| `10_geometry_edges.py` | CPU | Grid convention, Plane name, one-node axis, trilinear bound for a complex field | `out/10_geometry_edges.txt` |
| `11_gauss_check_sweep.py`, `11b_gauss_reference.py` | CPU | `gauss_axis` over the schema's range; which reference is right | `out/11_…txt`, `out/11b_…txt` |
| test suites | CPU, GPU 0 | `pytest` in the image | `out/09_test_suite_cpu.txt`, `out/09_test_suite_gpu.txt` |
| screenshots | CPU | own server instance (port 8499, engine mounted read-only, temp runs dir; stopped after use), Playwright 1.58.2 | `out/settings_no_gpu.png`, `out/v08_double_slices.png`, `out/catalogue_runs.png` |
