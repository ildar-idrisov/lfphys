# Response to the internal review of batch B1 (P10, P11, P12, v08), delivered 2026-10-27

Processed by the coordinating session, which did not write the review (`../../README.md`, rule 1). Every finding was
reproduced with the reviewer's numbers before it was fixed. Decision for all 18 findings: **fixed**; the gaps the
review lists against the owner's items 10 and 11 are partly closed here and the rest is staged in `../../../STATUS.md`
V22 and V23. The reviewer's inputs re-run on the processed code: `response_checks/rc_b1.py` → `response_checks/rc_b1.txt`.

Two changes go beyond the review's suggestions, because the measurements while fixing B1-1 and B1-2 showed them
necessary:

* **The source enters by its exact spectrum** (`core.optics.aperture_fields`: closed-form transforms of rectangles,
  the disc, the Gaussian; `angular_spectrum.Spectral`). With area-weighted samples the drawn field of the default world
  stayed 6e-3 of the peak off the exact field however wide the window (the staircase of the edges on the λ/4 grid);
  with the exact spectrum it is 5e-5 at a wide window (`visualizations/v08_wave_3d/README.md`, "Accuracy").
* **Exact references without FFTs for every v08 source** (B1-2's second method): the Rayleigh–Sommerfeld integral over
  unions of rectangles reduced to one integral over the angle (the radial integral is closed), the disc's closed form,
  the Gaussian's Hankel integral; tested against scipy's 2-D quadrature and mpmath.

| ID | decision | files | verified by |
|---|---|---|---|
| B1-1 [error in earlier] | fixed: the window is chosen by measurement on z_max (pad p against 2p, plain and band-limited sum, estimate 1.5·max\|U_p − U_2p\|, tolerance 2e-3 of the peak amplitude; the factor calibrated against the exact field: true error ≤ 1.25 × the difference over seven worlds, `tests/window_estimate_table.py`); a world needing more than 4096 points per axis is refused with the reason; new checks `window` and `exact_i_j` compare what is drawn (fp64) with the exact field; the README sentence on the window withdrawn | `v08_wave_3d/engine/apparatus.py`, `viz.py`, `README.md`; `lfphys/core/optics/angular_spectrum.py` (`band_limit`) | `test_v08_wave3d.py::test_window_estimate_bounds_the_true_error[3 worlds]`, `::test_a_world_whose_window_is_not_enough_is_refused`, `::test_presets_build_and_checks_pass`; `test_aperture_fields.py::test_band_limit_keeps_everything_at_z0_and_converges_faster_in_the_window`; rc_b1 B1-1 |
| B1-2 | fixed: exact source (no staircase), an exact reference at up to three points of z_max for every source (rectangles: the axis, the slit's centre line, a point near the window edge), the zone next to the aperture (z < 1.27 λ, the band-limited field) named in the check `near` and hatched in the view; «точно» replaced by the measured accuracy in the help and the header | `aperture_fields.py`, `v08_wave_3d/engine/apparatus.py`, `viz.py`, `web/view.js` | `test_aperture_fields.py::test_exact_source_equals_samples_for_a_smooth_field_and_the_exact_field_for_sharp_ones`, `::test_rectangle_equals_the_2d_rayleigh_sommerfeld_integral[3]`; rc_b1 B1-2 |
| B1-3 [error in earlier] | fixed: buffer offset m//2 − n//2 per axis; `Grid.uniform` puts node i at (i − n//2)·d for odd and even n | `angular_spectrum.py` (`_setup`), `geometry.py` | `test_geometry_3d.py::test_slices_for_odd_and_even_n_against_an_independent_reference[65,2; 64,2; 65,1; 63,(2,3)]` (Hankel integral, off the nodes), `::test_geometry_edge_cases`; rc_b1 B1-3 |
| B1-4 [error in earlier] | fixed: `used()[kernel] = {"drawn": …, "check": …}` with device, precision, reason, size; the header, the player's info row and v08's `device` check show the drawn one | `backend.py`, `player/js/player.js`, `viz.py`, `web/view.js` | `test_backend.py::test_auto_takes_the_cpu_for_small_problems_and_checks_are_fp64`; `test_v08_wave3d.py::test_fp32_drawing_keeps_every_check_passing` |
| B1-5 [error in earlier] | fixed: `slice_route` compares two fp64 routes; with fp32 drawing a separate check `fp32` compares the drawn data with fp64 under the kernel's declared bound | `viz.py`, `visualizations/RULES.md` §5 | `test_v08_wave3d.py::test_fp32_drawing_keeps_every_check_passing` (full volume and slices) |
| B1-6 [error in earlier] | fixed: the phase factor e^{i k_z z} is formed in fp64 and cast; the domain of the fp32 bound is stored with it ("k·z ≤ 2000 рад, до 1024 точек на ось") and tested at k·z = 2000 for fields, 2-D and slices | `angular_spectrum.py` (`_phase`, KernelSpec) | `test_backend.py::test_angular_spectrum_fp32_within_its_bound[cpu, gpu]`; rc_b1 B1-6 |
| B1-7 | fixed: "auto" compares the footprint (7 arrays of the padded size) with 80 % of the free GPU memory; an out-of-memory error frees the pool and redoes the call on the CPU, the reason recorded; the pool is returned after every GPU call | `backend.py` (`choose(footprint, force, why)`, `is_out_of_memory`, `release`), `angular_spectrum.py` (`_run`) | `test_backend.py::test_gpu_out_of_memory_falls_back_to_the_cpu_and_the_pool_is_released` (pool limited to 1 MiB) |
| B1-8 | fixed: `CUDA_DEVICE_ORDER=PCI_BUS_ID` set when unset; with `LFPHYS_GPU_PCI` a device 0 on another bus is refused; the compose service sets both (0000:01:00.0); `devices()` reports the bus id (shown on the settings page) | `backend.py`, `docker-compose.yml`, `player/js/settings.js` | `test_backend.py::test_gpu_is_pinned_by_its_pci_bus_id` |
| B1-9 | fixed: `ENV CUPY_CACHE_DIR=/tmp/cupy-kernel-cache` | `Dockerfile` (image rebuilt) | `docker run --user 1234:1234 --gpus '"device=0"'`: GPU available, PCI 0000:01:00.0, kernel drawn on the GPU (before: `PermissionError: '/.cupy'`) |
| B1-10 | fixed: the server checks the shape (kernels: object of objects with string fields; crossover: integer > 0, not bool, or null; no unknown keys) and answers 400 with the reason; bodies over 64 KB get 413; the engine gets the JSON on stdin (`--configure -`), answers malformed input with exit 2 and a message; tracebacks go to the server log only | `devices.py` (`shape_error`, `update`, `_backend`), `app.py`, `backend.py` (`configure`, `_main`) | `test_server.py::test_device_settings_are_validated_serialised_and_overridable_per_run` (the reviewer's seven bodies and a 200 kB body); `test_backend.py::test_malformed_settings_are_refused_and_unusable_gpu_is_noted` |
| B1-11 | fixed: one `asyncio.Lock` around load → validate → save and around the calibration's merge (measured outside the lock); the page sends one change at a time, each carrying all changes so far | `devices.py`, `player/js/settings.js` | same server test: a slow PUT, a fast PUT and a calibration in flight — the newest choice and the calibration both end in the file |
| B1-12 [error in earlier] | fixed: `Modelling` holds one `Slice(plane, exact, reason)` per plane; `approximations()` lists only the approximate ones; v08's slice message carries its route (`volume` / `slice` / `plane` / `axial` / `reduced`) with a label; the header's `approximations` reaches the passport, the run list («приближение») and the player's top bar («ПРИБЛИЖЕНИЕ: …») | `geometry.py`, `viz.py`, `web/view.js`, `runs.py`, `catalog.js`, `player.js`, `RULES.md` §2.6 | `test_geometry_3d.py::test_each_slice_carries_its_own_exactness`; `test_v08_wave3d.py::test_slices_mode_explores_only_the_computed_planes_and_flags_the_approximate_one`, `::test_approximation_flag_reaches_the_run_record` |
| B1-13 | fixed: the Gaussian's Hankel integral in panels of a quarter oscillation with an error estimate (engine); the tolerance is derived (window estimate × peak + the reference's error + 1e-9); the Gaussian enters by its exact spectrum, so it is never truncated by the window | `aperture_fields.py` (`gaussian_field`), `apparatus.py`, `viz.py` | `test_aperture_fields.py::test_gaussian_reference_converged_at_large_kz` (λ = 0.3, w = 0.5, z = 80: against Gauss–Legendre 4000/8000 panels and mpmath, 1e-12), `::test_gaussian_reference_equals_mpmath_off_axis[3]`; rc_b1 B1-13 (the reviewer's eight worlds) |
| B1-14 | fixed: z < 0 refused | `angular_spectrum.py` | `test_geometry_3d.py::test_negative_distance_is_refused` |
| B1-15 | fixed: "exact for the given source on the grid; the accuracy against the physical field is that of the window and of the source, which runs measure" (module docstring, `propagate_slice`, v08 README and view) | `angular_spectrum.py`, `geometry.py`, v08 | reading |
| B1-16 | fixed: a plane's name follows its axes ("custom" otherwise); `slice_field` needs two nodes per axis, with a message | `geometry.py` | `test_geometry_3d.py::test_geometry_edge_cases` |
| B1-17 [error in earlier] | fixed: `configure` notes "GPU выбран, но недоступен (…) → считается на CPU" | `backend.py` | `test_backend.py::test_malformed_settings_are_refused_and_unusable_gpu_is_noted` (`LFPHYS_NO_GPU=1`) |
| B1-18 | fixed: the references live in `lfphys.core.optics.aperture_fields` with tests; v08's apparatus in `v08_wave_3d/engine/apparatus.py` | as named | `test_aperture_fields.py` (15 tests) |

## Gaps against the owner's items 10 and 11

Closed here: chosen positions of the slices (y = c, x = c, z = c) and planes through the axis at any azimuth, in both
modes (item 10: «моделирование в выбранном 2-D срезе»); per-run device and precision from the catalogue (PLAN P11:
"global defaults and per-run overrides"); the validation domain of fp32; GPU memory shared with other services; the
CUDA 12.9 runtime on the 12.4 driver recorded (`lfphys/README.md`: minor-version compatibility, quoted from NVIDIA's
guide and CuPy's documentation, fetched 2026-10-27). Staged, with what would close them: `STATUS.md` V22 (the other
modules in 3-D, the plane choice for the existing 2-D worlds, tilted planes) and V23 (more GPU kernels, measured
CPU-only reasons, a power-limit guard for long GPU jobs).

The reviewer's note on the platform-runtime exception of `AGENTS.md` §3 rule 8 (the NVIDIA CUDA libraries) is put to
the owner in the B1 report for an explicit confirmation.

## Before → after (the reviewer's inputs; `response_checks/rc_b1.txt`)

| finding | reviewer (before) | processed code (after) |
|---|---|---|
| B1-1 wide-angle world (double, a 0.2 µm, λ 1.5 µm, n 128, z_max 80 µm) | built, plane z_max off by 31 % of the peak, every check passing | refused: «окно расчёта мало для глубины z_max = 80 мкм …» with the best window reached and the advice |
| B1-1 default world `double`, plane z_max | ×4 window; plane z_max 5.2e-3 of the peak intensity off a ×16 window, 13.9 % of the log-view pixels off by more than 0.1 decade (worst 2.5 decades); against the exact field 6.2e-3 of the peak amplitude (area-sampled source, measured while processing) | ×8 window chosen by measurement (estimate 1.1e-3); against the exact field 3.9e-4 at 21 points; against a ×32 window 8.3e-4 of the peak intensity; 0.1 % of pixels above 1e-6 off by more than 0.1 decade (none above the view's log floor 1e-5) |
| B1-1 other presets | circle: plane z_max 4.9e-3 off, 4.0 % of log pixels off by > 0.1 decade | circle ×4 band-limited: 2.2e-5 against the closed form on the axis; square_big ×4: 6.1e-4 against the exact field at 21 points, 1.5 % of pixels above 1e-6 off by > 0.1 decade (none above the log floor); gauss 2.4e-14 |
| B1-2 grid error (n against 2n, same window), y = 0 slice | double 2.5e-2, square 1.6e-2 of the peak | 2.0e-11 and 1.2e-11 for z ≥ z_near = 0.63 µm; inside the hatched zone z < z_near (the plane z = 0, the band-limited aperture) 0.17 and 0.085 — named in the check `near` and hatched |
| B1-3 n = 65, pad 2, slice x = 0 against the Hankel integral | 3.6e-2 | 1.6e-8 |
| B1-6 fp32, double slit, k·z = 1676 | 1.2e-5 (bound 1e-5) | 1.5e-7 |
| B1-9 container as UID 1234 with GPU 0 | `PermissionError: '/.cupy'`, GPU lost | GPU available (PCI 0000:01:00.0), the kernel ran on it |
| B1-13 the reviewer's eight Gaussian worlds | five FAIL (reference 2.9e-6 off; truncated or wrapped beams 0.027–0.29) | seven built with every check passing (largest relative error 4.0e-6 against a derived tolerance 1.9e-5 at λ 0.3, w 0.5, z 80); λ 1.5, w 0.5, z 80, n 128 (w < λ: light at all angles) refused for its window |

## Tests (Docker image, GPU 0)

Run 2026-10-27 in the rebuilt image (`light-funnel-viz`, `CUPY_CACHE_DIR` set), with `--gpus '"device=0"'`:

* `lfphys/tests`: 441 passed (B1 files: `test_aperture_fields.py` 15, `test_backend.py` 11, `test_geometry_3d.py` 19 collected tests);
* `visualizations/` (all visualizations and the server): 335 passed in 370 s, then after the last fixes `v08_wave_3d/tests` +
  `tests/` 25 passed;
* the player's changed modules pass `node --check`; screenshots of `double_slices`, `double` (plane through the axis at
  30°, log scale) and `square_big` on a private server instance (port 8499, engine mounted read-only, temporary runs
  folder, stopped after use): no page errors; the top bar shows «ПРИБЛИЖЕНИЕ: срез y = 0: …» only for the world with the
  reduced model (a stray «null» there for worlds without approximations was found on the screenshot and fixed).

The reviewer's scripts are kept as delivered; run them from `/lf/reviews/archive/2026-10-27_internal_B1` now. Several of
them call v08 internals that the processing replaced (`_aperture`, `_gauss_on_axis`, `Simulation.pad`, `used()[k]["device"]`)
and no longer run unchanged; `response_checks/rc_b1.py` re-runs their inputs on the processed code. The two web pages
the reviewer saved (`out/eula/cuda129_eula.html`, `out/cuda_env/environment-variables.html`, NVIDIA's text) are kept
locally and not committed (third-party copyright; the quoted sentences are in `out/08b_eula_web.txt` and
`out/12_cuda_device_order_doc.txt`).
