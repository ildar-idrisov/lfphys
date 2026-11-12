# Response to review B8 / P1 — the FDTD solver (F1–F20)

Processed 2026-11-04 by a subagent that did not write the review nor the code under review (`reviews/README.md`). The
review text and the reviewer's scripts are unchanged. Every reviewer script that was re-run was run from a copy in the
session scratchpad (`b8/proc_fdtd/rev/`, `rev_mod/`; one copy changed: `s09_tfsf_mod.py` catches the new F7 refusal in
its part (1), marked in its first line). Every finding with a script was first reproduced on the reviewed code (the
five original modules, md5 as in `reviewed_files.md5`, mounted over the package; outputs in `out/rev_orig/`): the
numbers below marked "reproduced" are from those runs; they equal the reviewer's except the id-cache count of F1 (24 of
200 here, 9 there: it depends on memory reuse). All runs in Docker: `light-funnel-viz` (CPU, `LFPHYS_NO_GPU=1`),
`light-funnel-ext-meep` (Meep 1.35.0) and GPU 0 through the session's `gpu_run.sh` (every job under 5 minutes). No
e-mail address or personal identifier was sent with any external request (arXiv abstract pages and one Crossref record
were fetched with plain requests).

**Counts: 18 fixed, 1 partly fixed (F6), 1 open → owner (F14), 0 rejected.** Each finding's heading carries its
status tag ([error in earlier] where a stated property or number of the engine was wrong). Parts of two recommendations were not
followed, with the reason given (F7: doubling the window does not reduce the leak; F13: the Kashiwa-type update is
recorded as an option, not implemented). Found while processing: three [errors in earlier] beyond the review (the PEC
cylinder's stated numbers, two test pulses whose spectra reached a Bloch cut-off, and the pre-review planar numbers
that contained the monitor's bias) and one integrator note on `make_results.py` (end of this file).

Files changed (all owned by this processing):
`lfphys/lfphys/core/em/fdtd.py`, `fdtd_geometry.py` (docs), `fdtd_sources.py` (docs), `fdtd_tfsf.py`,
`fdtd_monitors.py` (docs); `lfphys/tests/test_fdtd_grid.py`, `test_fdtd_api.py`, `test_fdtd_media.py`,
`test_fdtd_boundaries.py`, `test_fdtd_scattering.py`; `lfphys/tests/external/test_ext_fdtd_meep.py`,
`tests/external/RESULTS_meep.md` (new, generated in `light-funnel-ext-meep`), the Meep row, the FDTD tolerance text
and the Meep run time in `tests/external/README.md`, the Meep basis keys in `tests/external/make_results.py`;
`lfphys/sources/verification_2026-11-04_p1_fdtd.md`. Not changed: `core/optics/cylinder.py`,
`test_cylinder_series.py`, `docker/meep/*` (no finding needed it).

Final verification (2026-11-04, after the last change):
* CPU, `light-funnel-viz`: `tests/test_fdtd_*.py tests/test_cylinder_series.py tests/test_boundary.py
  tests/test_layers.py tests/test_licences.py tests/test_backend.py` — **366 passed, 9 skipped** (the tests that need
  GPU 0), 100 s.
* GPU 0 (`gpu_run.sh`): `test_fdtd_api.py::test_gpu_equals_cpu` (GPU = CPU: real fields bit for bit, Bloch fields to
  round-off), `test_fdtd_scattering.py::test_sphere_against_mie_converges_gpu` and the new
  `::test_te_high_contrast_cylinder_is_first_order_gpu` — **3 passed**, 105 s; `tests/test_backend.py` on GPU 0 —
  **16 passed**.
* Meep, `light-funnel-ext-meep`: `tests/external/test_ext_fdtd_meep.py` — **25 passed, 1 xfailed (strict)**, 141 s;
  `make_results.py --only test_ext_fdtd_meep --out tests/external/RESULTS_meep.md`: 20 comparisons, 0 problems.

Measurement records (session scratchpad `b8/proc_fdtd/out/`, outside the repository): `m_media.txt` (planar R, both
normalisations, the monitor factor), `m_scatter_cyl.txt`, `m_scatter_sph16.txt`, `gpu_sphere.txt`, `gpu_order_te.txt`,
`pec_noderule.txt`, `meep_diag.txt`, `tail_vs_M2.txt`, `quotes_check.txt`, and the reviewer's scripts re-run after the
fixes in `rev_after/`.

---

## Errors

### F1 — the stability check cached by `id(Medium)` accepted unstable media — **fixed** [error in earlier]

* Reproduced: `s07c_idcache.py` (copy) on the reviewed code: 24 of 200 trials accepted eps = 0.3 at S = 0.6 (the
  first accepted world blew up at step 512).
* Fix (`fdtd.py`): the cache key is the medium's value, `_medium_key` (its parameters without the label, as sorted
  JSON) with dt; `_medium_radius` computes or looks up the radius, `_check_medium` decides every time (also the
  background's own condition, which the old early return could skip). `checks()["stability"]` now reports the radius of
  the world's current media, not of everything ever cached.
* Verified: the copy of `s07c_idcache.py` after the fix: **0 of 200** (`rev_after/s07c_idcache.out`);
  `test_fdtd_api.py::test_stability_cache_is_by_value_not_by_id` (the 200-trial pattern; equal media share one entry).

### F2 — hard magnetic sources imposed after the E update diverged — **fixed** [error in earlier]

* Reproduced: `s10_walls_sources.py` (2): hard H_z at the magic step 3.8e36; `s10b_hard_h.py`: TE/TM mismatch 0.86.
* Fix (`fdtd.py`, `_apply_hard(kind, t)`): a hard H is set right after the H update (and the H walls and soft M
  sources), at t_{n+1/2}, before the E update uses it; a hard E right after the E update and the walls, at t_{n+1}, and
  now before the Debye trapezoid takes E^{n+1} (it took the pre-overwrite value). Docstring `fdtd_sources.py` restated.
* Verified: copies after the fix: hard H_z at the magic step **8.9e-16**, hard E_z 1.5e-8 (the profile's own jump at
  its 6-width cut-off; `rev_after/s10_walls_sources.out`); `s10b`: 4.6e-2, which is the half-step shift between the
  dual problems. Tests `test_fdtd_grid.py::test_hard_sources_are_exact_at_the_magic_time_step` (both < 1e-7) and
  `::test_hard_h_is_the_dual_of_hard_e_2d` (TE hard H_z against TM hard E_z of the profile delayed by dt/2: measured
  3.2e-5 of the peak, the absorbing layers' echo, which is not dual; asserted < 1e-4; was 0.86).

### F3 — polarization kept or dropped by position in the media list — **fixed** [error in earlier]

* Reproduced: `s08_edits.py` (1) Lorentz P carried into a Drude pole (0.459), (2) an unchanged body's P zeroed after an
  earlier body was removed.
* Fix (`fdtd.py`, `_build_materials`): P is kept where the node's medium before and after the edit is the same **by
  value** (`_medium_key`); a different medium starts from 0. Value rather than identity, so a GUI that recreates an
  equal `Medium` keeps the polarization. The rebuild is now all or nothing: the media list and index are committed only
  after the node maps and the new stability bound (F11) pass.
* Verified: copy of `s08_edits.py`: (1) **0** carried, (2) **0.459 kept** (`rev_after/s08_edits.out`); test
  `test_fdtd_api.py::test_polarization_is_kept_by_medium_not_by_position` (both cases, and an equal new object keeps P).

### F4 — a plane wave added mid-run had its incident spectrum numbered from step 1 — **fixed** [error in earlier]

* Reproduced: `s09_tfsf.py` (2): Q_sca/Q_sca(step 0) = 0.96–1.015 (added at step 100), 1e23 (step 400).
* Fix (`fdtd_tfsf.build_tfsf` records `ref_step0`, the step at which the wave was added; `fdtd.py._incident_dft`
  numbers the series from it; `state_dict` / `from_state_dict` save and restore it).
* Verified: the processing copy `rev_mod/s09_tfsf_mod.py` (2): ratios **1, 1, 1**; test
  `test_fdtd_api.py::test_plane_wave_added_during_the_run` (added at step 0, 100, 400, and saved/restored mid-run:
  measured 9.4e-10, the two runs' incident series coming from FFT windows of different lengths; asserted 1e-8).

## Should-fix

### F5 — cross sections and R divided a monitor-biased flux by an exact intensity — **fixed** [error in earlier]

* Reproduced: the flux of the incident wave alone is low by cos(k_x dx/2) cos²(k_y dx/2) (TM); with it the 1-D Meep
  rows agree to ≤ 2.1e-5 (`s09_tfsf.py` (5), `s14b`).
* Fix:
  * `fdtd_tfsf.monitor_factor` and `FDTD.monitor_factor(freqs, axis)`: the closed form of how the face operator sees the
    grid's own plane wave (a term E_t1 H_t2 times cos(k_v dx/2) cos²(k_t2 dx/2); 2-D TM cos(k_v) cos²(k_t), TE
    cos(k_v) alone — the reviewer's single TM form does not hold for TE), from the wave's discrete k, E and H.
  * `incident_intensity(..., normalisation="exact" | "monitor", axis)`, `cross_sections(..., normalisation=)` and
    `far_field(..., normalisation=)`; `cross_sections` also returns `normalisation` and `monitor_factor`. The default
    stays "exact" (no silent change of meaning); "monitor" is Meep's convention.
  * Docstrings (`fdtd_monitors` module text and ABOUT, `fdtd.py`): I_inc is the true intensity, *not* what the monitor
    measures; "monitor" cancels the bias exactly for reflection and transmission along the incidence axis; for
    scattering neither choice removes the bias on the scattered waves (TM −(k dx)²(1 + sin²θ)/8, TE −(k dx)² cos²θ/8
    per wave at angle θ to a face's normal), which is of the size of the scheme's own error.
* Verified: `test_fdtd_media.py::test_monitor_factor_is_what_the_monitor_measures` — the measured flux equals
  `incident_intensity("monitor")` times the discrete direction cosine to **5e-11 … 1.6e-9** (TM and TE, 0°, 30°, 45°,
  10 and 20 cells; the reviewer's continuum prediction was off by up to 5.6e-4 at 10 cells); the planar tests now take
  the monitor normalisation from the engine, not a factor written in the test.
* Re-measured, every number that depended on the normalisation (restated in the tests' docstrings, `fdtd.py`,
  `fdtd_geometry.py` and the verification file; "exact" / "monitor"):

  | quantity | before (as stated) | now |
  |---|---|---|
  | planar R vs the grid's exact R | 2e-4 (with the factor written in the test) | monitor-normalised 2e-6 … 9.6e-5 (engine's factor); exact-normalised low by the factor, −0.3 … −2.8 % at 20 cells |
  | n = 2 at 10 cells per wavelength in the medium, vs Fresnel | −11 % (E node) / +9 % (H node) | +10.7 % (H) / −10.3 % (E) — the scheme's own; the old numbers contained the monitor's −2.4 % [error in earlier] |
  | planar Fresnel error at 40 cells (monitor) | "below 7 %", ratio 3.3–4.8 | n = 2 ±0.6…5.8 %, conductor +0.4…+4.0 %, Drude +0.12…+0.22 %, Debye +0.6…+4.7 %, Lorentz +0.5…+3.1 %; ratio 3.8–4.6 |
  | oblique s / p at 40 cells | below 5 % | s 1.0–3.8 %, p 2.9–4.9 % (monitor) |
  | dielectric cylinder m = 1.5, 40 cells | 0.03–0.3 % | TM +0.03…+0.06 % (exact) / +0.10…+0.37 % (monitor); TE −0.12…+0.29 % / −0.07…+0.60 % |
  | sphere vs Mie, 32 cells (GPU 0) | 0.01–0.8 % | −0.01…+0.76 % (exact) / +0.16…+0.84 % (monitor); 16 cells +0.33…+1.66 % / +1.03…+2.47 % |
  | Meep 1-D rows | diff 6e-4 … 6e-3, "engine nearer in 13 of 18" | like-normalised: slab 1.6e-7 … 1.1e-6, Drude 1.6e-7 … 6.3e-6 (F8) |

  The "0.03–0.3 %" and "0.01–0.8 %" were the exact normalisation, whose smaller numbers come from the monitor's bias
  cancelling part of the scheme's positive error (the reviewer's reading, confirmed: the monitor-normalised errors are
  larger and still second order for TM, ratios 3.9–4.0). "The engine nearer in 13 of 18" is withdrawn [error in
  earlier]. Status tags: the closed-form factor [useful]; the restated accuracies [weakens] the earlier claims.

### F6 — the averaging is the diagonal-only VP-EP scheme, first order on curved surfaces — **partly fixed** [weakens], [error in earlier]

* Reproduced on GPU 0 (`gpu_order_te.txt`): TE cylinder ε = 6, f = 0.5: Q_sca +2.62 / +1.44 / +0.77 % (exact), +2.70 /
  +1.46 / +0.78 % (monitor) at 40 / 80 / 160 cells: ratios 1.83, 1.86 — first order; f = 0.6, 0.8 not monotone.
  The quotations were grepped in the paper (`quotes_check.txt`): "the VP-EP scheme, which is exactly the diagonal
  part of Eq. (1) for s = 1", "do not satisfy the perturbation criterion for diagonal interfaces", "are therefore
  expected to have only linear convergence in general".
* Done: the scheme is named as Farjadpour et al. classify it, and its order stated with the numbers
  (`fdtd_geometry.py` docstring and ABOUT, `fdtd.py` ABOUT and accuracy paragraph, the verification file §3, §8): second
  order for flat surfaces along the axes and for E along a cylinder's axis (TM, where the diagonal is the full tensor:
  m = 1.5 ratios 3.3–4.0), first order in general for in-plane E on curved surfaces, not monotone at weak contrast
  (TE m = 1.5, f = 0.4: −0.02, −0.12, −0.09 %). "Between first and second order" withdrawn [error in earlier]. A GPU
  regression test pins it: `test_fdtd_scattering.py::test_te_high_contrast_cylinder_is_first_order_gpu` (ratio
  1.5–2.3; a full-tensor averaging would make it fail and force the validity to be restated). The Meep comparison
  records the consequence (the engine's TE error at f = 0.4 is not monotone: a strict xfail of its convergence test).
* Not done: the off-diagonal terms (averaged D at the E point). They need a D-based E update on both devices, a CPML
  for D, and a new stability analysis (the averaged off-diagonal coupling is not symmetric) — beyond a review fix.
  → STATUS V43 (b), via the integrator.

### F7 — the Bloch-slab plane wave leaked up to 6e-6 near its cut-off — **fixed** (the recommended remedy did not work; the cause was different) [error in earlier]

* Reproduced: `s09b_slab_leak.py` (copy, before the fix): leak 5.9e-6 at k_par = 2π·0.6, pulse 1.2 ± 0.15.
* Cause found: not the window's length. `tail_vs_M2.txt`: the window tail is **1.91e-5, 1.84e-5, 1.83e-5 at M = 4096,
  16384, 65536** — independent of M — and equals the series' value at the first samples (1.6e-5): the incident wave of
  the grid is non-zero at the start of the run. Its spectrum is cut sharply where the propagating band ends (frequencies
  below the Bloch cut-off are left out), and a sharp spectral edge has a long precursor; the injection begins abruptly
  at t = 0 inside it. The same floor, ~1e-8, comes from the profile's own cut-off at 6 widths. So "double M until the
  tail < 1e-9" cannot work (not followed, with this measurement as the reason).
* Fix (`fdtd_tfsf._build_series`): (1) the group-delay spread is estimated over the whole propagating part of the band
  (power > 1e-16 of the peak), not at three frequencies with the diverging delay replaced by the continuum's; (2) the
  window is doubled only while that lowers the tail by at least 2× (a real wrap-around), within the memory cap; (3) a
  tail above `TAIL_MAX` = 1e-6 is refused, with the reason (spectrum at a cut-off or band edge; narrow the band, move
  the frequency, or delay the pulse). The omitted-energy check now runs before any doubling. Claims restated: leak
  ≈ 0.3–0.4 × the window tail (the reviewer's measured relation), 2–3e-9 away from a cut-off (`fdtd_sources`,
  `fdtd_tfsf`, `fdtd.py` docs). 1e-6 rather than 1e-9: the profile's own cut-off already gives ~1e-8 to 1e-7 for
  narrow-band pulses (Brewster's test pulse: 9.5e-8), and a leak of ≤ 4e-7 is reported, not hidden (`checks()`).
* Verified: copies after the fix (`rev_after/s09b_slab_leak.out`): k_par = 0, 0.3: leak 1.8–2.5e-9 (unchanged); 0.5:
  tail 9.1e-7 accepted, leak 3.4e-7; **0.6 refused**; 0.6 with ± 0.08: 2.3e-9. Test
  `test_fdtd_scattering.py::test_bloch_slab_leak_near_the_cut_off` (two finite faces). Two test pulses of the suite
  reached a cut-off and are now refused: `test_oblique_incidence_s_and_p` (1.2 ± 0.12, tail 1.3e-6 → ± 0.1) and the
  `_busy` Bloch world of `test_fdtd_api.py` (± 0.15 at k_par = 2, tail 1.6e-6 → ± 0.1); Brewster's pulse (± 0.03) was
  narrowed to ± 0.025 for margin [error in earlier: their incident waves leaked ~5e-7 unnoticed].
* Not done: a smooth spectral taper at the cut-off would admit such pulses with a precursor below 1e-9 — an option,
  → STATUS V43 (e).

### F8 — the Meep tolerance assumed second order; three rows tested R = 0 — **fixed** [error in earlier]; the new rows [useful]

* Reproduced (`meep_diag.txt`): the engine's like-normalised R and Meep's both equal the grid's exact discrete R; the
  engine's TE row at f = 0.4 is not monotone (now with the monitor normalisation: +0.18 / −0.067 / −0.079 % at
  20 / 40 / 80 cells).
* Fix (`tests/external/test_ext_fdtd_meep.py`, rewritten; README §2–§4 text; basis keys in `make_results.py`):
  * Both codes like-normalised (the engine by `incident_intensity("monitor")`).
  * 1-D rows at f = 0.6, 0.75, 0.9, 1.1, 1.25, 1.4 (off the slab's Fabry–Pérot zeros), 40 cells; the exact reference
    is the grid's discrete R_d, computed by the transfer recursion of the frequency-domain Yee equations over the
    engine's node profile (with eps_d(f)); both codes reproduce it (engine 1.0–1.8e-6, Meep 0.3–1.0e-6 for the slab).
    The half-space's interface node is wholly Drude in both codes (an averaged node would move R by 3e-3; checked).
  * Tolerance "one discrete problem": 2(A_eng + A_meep) + W_eng + W_meep, A each code's absorbing-layer reflection
    amplitude measured in the module by a control (a source and a probe 3 cells from the layer against a run ten times
    longer: −110 dB / −130 dB), derived as |ΔR| ≤ 2|r|(|r|² + |t|²)A ≤ 2A; W the change of R when the run is extended.
    Drude rows: plus Meep's 20-cell distance to R_d, because Meep's Drude update differs from the engine's at second
    order (2.4e-5 → 5.4e-6 from 20 to 40 cells; `test_meep_drude_difference_converges` checks the fall).
  * Cylinder rows: tolerance "coarser-grid errors, monotone" — each side's 20-cell error against the series, valid
    where its error falls monotonically over 20, 40, 80 cells, checked per side (`test_cylinder_convergence_is_monotone`;
    the engine's TE at f = 0.4 is a strict xfail with its numbers, F6). No order is assumed.
* Verified: 25 passed, 1 xfailed (strict); `RESULTS_meep.md` (20 rows): slab diff 1.6e-7 … 1.1e-6 against tol 7.1e-6;
  Drude 1.6e-7 … 6.3e-6 against 1.1–2.5e-5; cylinders 2e-4 … 6.4e-3 against 4e-3 … 0.14; largest diff/tol 0.32.

### F9 — an axis with a PEC (or PML) and a PMC side was dx/2 longer — **fixed** [error in earlier]

* Reproduced: `s10_walls_sources.py` (1): (pec, pmc), (pmc, pec), (pml, pmc), (pmc, pml) realised 0.625 for 0.6.
* Fix (`fdtd.py`, the grid set-up): the realisable length nearest to the request — between a PEC and a PMC wall an odd
  number of half cells (ties up); next to a PML side the interior's edge is put half a cell from the layer so the
  length is exact. `describe()["size_requested"]`, `checks()["geometry"]` (requested, realised, `ok`, a note), and
  the state keep the request. Docstring: "each length the realisable one nearest to the request".
* Verified: copy after the fix: (pml, pmc) and (pmc, pml) **0.6**, (pec, pmc) 0.625 flagged
  (`rev_after/s10_walls_sources.out`); tests `test_axis_lengths_with_pec_and_pmc_walls` (all eight pairs: lengths and
  the walls' own positions), `test_saved_world_keeps_the_requested_length`; `test_pec_pmc_waveguide_modes_2d` now asks
  for the realisable 0.625 [error in earlier: it asserted the realised length and so could not see the 0.025 change].

### F10 — "CPML −88…−95 dB at 10 cells" holds only up to ~70° — **fixed** [weakens]

* Reproduced: the reviewer's numbers (s11 (2)) are the basis; the new test measures them again.
* Fix: the validity and the module text state the angular range, the grazing numbers and the recommendation (16–20
  cells for grazing geometries); the σ_max estimate gained an open secondary source (F19).
* Verified: `test_fdtd_boundaries.py::test_cpml_at_grazing_incidence` (10 cells worse than −65 dB at 85.7° and 87.1°,
  better than −45 dB; 20 cells below −105 dB).

### F11 — stability was checked per medium; mixed E/H nodes could be unstable — **fixed** [error in earlier]

* Reproduced: `s07_stability.py` (d) on the reviewed code: accepted at S = 0.5, NaN after 500 steps (and its part (b):
  no medium accepted at 257 sampled spatial frequencies is unstable at 20001, 0 of 300).
* Fix (`fdtd.py`, `_node_courant_bounds`, called by every material rebuild before anything is committed): two
  sufficient bounds over the actual node maps (nodes held at zero by PEC or walls left out): S ≤ S_vac
  √(min_E ε · min_H μ) (exact for a uniform medium) and Gershgorin's bound on ε^-1/2 Cᵀ μ^-1 C ε^-1/2 (local; equal to
  the vacuum limit in 2-D, 3/4 of it in 3-D, so it is used only when the first fails); the world is refused unless one
  holds. Sufficient for nodes without poles and conductivity; nodes with poles enter with ε∞ and keep the per-medium
  check. `checks()["courant"]["node_limit"]`. The docstring states both checks and what they do not see.
* Verified: `test_fdtd_grid.py::test_mixed_nodes_are_checked_for_stability`: the reviewer's world **refused** at
  S = 0.5, accepted at 0.24 and its energy conserved to 1e-10 over 4000 steps; a single medium with ε < 1 keeps its own
  limit (accepted at 0.45, refused at 0.55).

### F12 — plane-wave faces and monitor boxes were not checked — **fixed** [useful]

* Reproduced: `s09_tfsf.py` (3): a slab across two faces accepted without a word.
* Fix: `checks()["tfsf_<id>"]` counts the correction nodes whose medium (index, ε or μ value) is not the background's,
  recomputed from the current maps, so bodies added or moved later are seen (`foreign_nodes_at_faces`, `ok`, a note);
  `checks()["monitor_<id>"]` says where each flux or near-to-far box lies ("sf", "tf", "mixed", with a cell's margin);
  `cross_sections` refuses a scattered box not wholly in the scattered-field region or a total box not wholly inside,
  `far_field` refuses a near-to-far box not in the scattered-field region. Bodies at faces are flagged, not refused:
  a live edit may move a body across a face on purpose (to watch it), and the flag says that the injected wave is then
  wrong there; the TF/SF validity says so.
* Verified: processing copy of `s09_tfsf.py` (3): `foreign_nodes_at_faces` 50, `ok` False; test
  `test_fdtd_api.py::test_bodies_at_the_plane_wave_faces_and_misplaced_monitors` (a body added, moved across, removed;
  good, inside, crossing and misplaced near-to-far boxes, the refusals).

### F13 — the pole schemes and their stability had no source; the refusal hint was not the published condition — **fixed** [error in earlier]

* Checked against the paper (arXiv:math/0506289; the journal reference SIAM J. Numer. Anal. 46(5), 2551–2566 (2008),
  doi 10.1137/060671255, from arXiv's abstract page and Crossref): the engine's Lorentz/Drude update is her
  "Lorentz–Young model", eq. (15) (Young, IEEE TAP 43, 422 (1995)); the Debye trapezoid her "Debye–Joseph et al."
  eq. (10) (Joseph, Hagness & Taflove, Opt. Lett. 16, 1412 (1991)). Her conditions for Young's scheme: "ω < 2/(2ε′s
  − 1)" and "q ≤ 2 instead of q ≤ 4", in 2-D "k ≤ h/(2c∞)"; for Joseph's "q ≤ 4". All grepped (`quotes_check.txt`).
  Her polynomial was evaluated here: the conditions are sufficient, not necessary (ε′s = 2.25, ω = 0.05: all roots on
  the closed unit disk up to q = 3.5), which is why the engine admits more by its computed radius.
* Fix: `fdtd.py` ABOUT `basis` cites Young 1995, Joseph et al. 1991 (both not fetched: their schemes as she gives
  them) and Bidégaray-Fesquet 2008; the module text names the schemes; the refusal hint quotes her sufficient
  conditions in the engine's terms (c∞Δt/dx ≤ 1/√2 in 1-D, 1/2 in 2-D; ω0Δt ≤ 2/√(2εs/ε∞ − 1); for a Drude pole
  ωpΔt ≤ √(2ε∞), derived here as her condition's limit, marked so; Debye: the vacuum condition); the old hint "ω0Δt
  < 2, ωpΔt < 2√ε∞" is withdrawn [error in earlier]. The limitation the reviewer named (a double root on the unit
  circle, linear growth, is not detected by ρ ≤ 1 + 1e-6) is stated in the code and the docstring; the finiteness
  check now also runs at the end of every `advance` (F20).
* Verified: `test_fdtd_grid.py::test_published_pole_conditions_are_sufficient_for_the_engine` (60 random Lorentz
  media satisfying her conditions and 60 Debye media at or below the vacuum limit all admitted; a pole beyond the ω condition
  refused, the refusal naming the paper); the verification file §6a.
* Not done: the Kashiwa-type Lorentz update she recommends (the vacuum Courant range) — the explicit scheme is kept,
  admitted by its exact radius, and is the form Meep uses (its Drude rows compare it); → STATUS V43 as an option.

### F14 — the licence of the Meep test module — **open → owner** (no change made to the file's licence) [neutral]

Facts: `lfphys/tests/external/test_ext_fdtd_meep.py` carries the project's SPDX line
(`LicenseRef-lfphys-Research-1.0`). It imports Meep (pymeep 1.35.0, GPL-2.0-or-later) and only calls Meep's documented
Python API (`mp.Simulation`, `mp.Source`, `mp.GaussianSource`, `mp.Medium`, `mp.DrudeSusceptibility`, `mp.Block`,
`mp.Cylinder`, `mp.PML`, `mp.FluxRegion`, `add_flux`, `get_fluxes`, `get_flux_data`, `load_minus_flux_data`, `run`,
`stop_when_fields_decayed`, `at_every`, `get_field_point`, `verbosity`); no Meep code is copied into it or into the
engine, and the engine never imports Meep. The module runs only in the image `light-funnel-ext-meep`, which is never
pushed, exported or distributed (`sources/dependencies.md` §10.5). The question is whether distributing this source
file (without Meep) under the project's noncommercial licence is compatible with Meep's GPL. The FSF's reading (GPL
FAQ, #IfLibraryIsGPL, grepped): "Yes, because the program actually links to the library. As such, the terms of the GPL
apply to the entire combination. The software modules that link with the library may be under various GPL compatible
licenses, but the work as a whole must be licensed under the GPL"; the project's licence is not GPL-compatible (it
forbids commercial use). The FAQ is the FSF's reading, not a court's; whether it reaches a source file distributed
without the library is the grey zone the review names. The owner chooses:

* **(a) keep the file under the project's licence.** Consequences: nothing changes; the risk is the FSF's reading
  that a program written to use a GPL library forms a combination under the GPL, so a recipient (or Meep's copyright
  holders) could argue that distributing the file under a noncommercial licence is not allowed; the risk exists only
  once the repository is distributed, and grows if the image (Meep inside) ever ships with it. Lowest effort, legal
  uncertainty kept.
* **(b) license this one file GPL-2.0-or-later, with an SPDX header** (`SPDX-License-Identifier: GPL-2.0-or-later`,
  the owner as the copyright holder). Consequences: compatible with Meep in any reading; anyone may copy, modify and
  redistribute that file (also commercially) under the GPL, which is acceptable only because it holds no engine code
  — but it must stay that way (helpers it imports, `_common.py` and the engine, stay under the project's licence and
  are only called); `test_licences.py`, `NOTICE`, `dependencies.md` and the external README must list the exception;
  the repository is no longer under one licence.
* **(c) keep the Meep test outside the distributed tree** — e.g. a folder excluded from the future engine repository
  (`.gitattributes export-ignore` or a separate private repository), or not committed at all. Consequences: no
  distribution, so no licence question; the comparison is no longer reproducible by recipients, and `RESULTS_meep.md`
  and the README's claims would rest on a file they cannot see (they would need to say so); the file and its image
  must still be kept and run somewhere for the regression value.
* **(d) ask a lawyer** (add it to the questions of STATUS V20). Consequences: a reliable answer for the jurisdictions
  that matter (Cyprus, the EU) before publication; costs time and money; until then (a) applies de facto, which is
  harmless while the repository is private.

The processing changes nothing here; the integrator records it in STATUS (below).

## Nits

### F15 — `energy()` "exactly conserved" was wrong for lossless dispersive media — **fixed** [error in earlier]

* Fix: the docstring says the sum is conserved for non-dispersive, non-conducting media and leaves out the poles'
  energy (`fdtd.py`); the module text says so too.
* Verified: copy of `s08_edits.py` (3) unchanged (0.17–1.00, as documented now); test
  `test_fdtd_grid.py::test_field_energy_is_not_conserved_with_a_lossless_pole` (conserved to 1e-12 without the pole,
  below 0.5 of its start with it).

### F16 — a 3-D polarization along the direction gave a silent zero wave — **fixed** [useful]

* Fix (`fdtd_tfsf._check_polarization`): refused when the polarization's component across the grid's K is below
  `POL_MIN` = 1e-3 at any frequency of the band (pulses) or at the frequency (continuous wave).
* Verified: processing copy of `s09_tfsf.py` (4): refused; test
  `test_fdtd_api.py::test_3d_polarization_along_the_direction_is_refused` (pulse and continuous wave; a polarization
  with a component along k is still accepted and projected).

### F17 — the continuous-wave ramp described two ways — **fixed** [neutral]

* `fdtd_sources.py` now says "the discrete group delay (dk/dω of the grid's wave)", as the code and `fdtd_tfsf` do.

### F18 — cost estimate and footprint — **fixed** [useful]

* Fix: `other_device_per_step_s` carries the complex factor; `_footprint` adds the plane waves' tables and correction
  lists, the current sources' index arrays, every DFT accumulator (DFT monitors, flux and near-to-far faces) and the
  dispersive nodes' arrays.
* Verified: `test_fdtd_api.py::test_cost_estimate_and_footprint`.

### F19 — records — **fixed** [error in earlier]

* arXiv:2606.06910: by V. C. Obieke (Oregon State University; title page and arXiv's metadata), an acoustic
  pressure–velocity FDTD whose CPML recursion is the same — the verification file says so ("names not legible"
  [error in earlier]). Corbino, arXiv:2603.19056, eq. (29), "A common estimate for the maximum conductivity is [2]",
  [2] = Taflove & Hagness 3rd ed., added as the open secondary source for σ_max (`fdtd.py`, verification §2). Grepped.
* `tests/external/RESULTS_meep.md` generated in `light-funnel-ext-meep` (20 rows, F8).
* "13 of 18 nearer" withdrawn (F5).

### F20 — a blown-up world could return NaN without `Unstable` — **fixed** [useful]

* Fix: `advance` checks finiteness at the end of every call too (one reduction per component per call).
* Verified: `test_fdtd_grid.py::test_fields_are_checked_at_the_end_of_every_advance`.

## Found while processing

* **The PEC cylinder's stated accuracy was not this test's** [error in earlier]: the test's docstring and the
  verification file said TM −2.7…−4.0 % / −1.5…−1.9 % / −0.8 % and TE −0.3…+6.4 % / −1.2…+1.4 % / −0.7…+0.6 % at
  20 / 40 / 80 cells; the reviewed (original) code gives TM −3.2…−4.6 % / −1.6…−2.0 % / −0.78…−0.90 % and TE
  −0.5…+9.0 % / −1.7…+1.0 % / −0.8…+0.4 % (`pec_origcode.txt`); the node rule's largest errors, 30 % / 6.8 % / 3.8 %
  (`pec_noderule.txt`: +10…+30 % / +2.8…+6.8 % / +1.6…+3.8 %), match the stated ones. Restated in the test, the
  verification file and the `_assign` comment; the test's assertions (40-cell bounds, first-order ratio) hold.
* **Two test pulses and a test world had spectra at a Bloch cut-off** (F7, above) [error in earlier].
* **`make_results.py` in the Meep image** lists pymeep as "not installed", version "-": conda's Meep has no pip
  metadata (`importlib.metadata` finds neither `pymeep` nor `meep`; `meep.__version__` is "1.35.0"), and the generated
  file's header names `light-funnel-ext` for every image. Not this processing's part of the shared file; for its owner
  (below).

## Reviewer's "checked and holds" items

All taken as stated; two were re-confirmed by this processing: GPU = CPU (the GPU run above) and the near-to-far
transform (the cylinder and sphere far fields, both normalisations, within the stated bounds).

---

## Changes for the integrator

### 1. `engine/STATUS.md`, row V43 — replace the FDTD part

In the gap column, replace the text from "**FDTD** (`core.em.fdtd*`): (a)" up to (not including) "**Charges**" with:

> **FDTD** (`core.em.fdtd*`; review B8-fdtd processed, `reviews/2026-11-04_internal_B8-fdtd/RESPONSE.md`): (a) PEC is
> staircase, first order (TM cylinder −1.6…−2.0 % at 40 cells); (b) sub-pixel averaging keeps only the diagonal of
> Farjadpour's tensor — their VP-EP scheme, first order in general for in-plane E on curved surfaces (TE cylinder
> ε = 6: +2.6, +1.4, +0.8 % at 40/80/160 cells; not monotone at m = 1.5, f = 0.4); second order for TM; (c) dispersive
> and conducting bodies are staircase only; (d) a continuous wave's ramp leaks up to 4e-4 (ramp 6) or 2.4e-3 (ramp 2)
> through the TF/SF boundary; (e) TF/SF: oblique Bloch incidence only as a slab, 3-D oblique pulses capped at 512 MB of
> tables, faces need a homogeneous lossless background (bodies at faces are counted in `checks()`, not refused); a
> pulse whose spectrum reaches a Bloch cut-off is refused (window tail > 1e-6: the precursor of the sharp spectral cut);
> (f) not modelled: magnetic dispersion and conductivity, anisotropy, nonlinearity, moving bodies; (g) no fp32; (h) the
> Yee interface error on coarse grids is large and inherent (n = 2: +10.7 % / −10.3 % of R at 10 cells per wavelength
> in the medium, interface on an H / E node); (i) `energy()` leaves out the poles' energies; (j) the near-to-far
> transform uses the continuum k; (k) CPML for evanescent and late-time fields untested; at grazing incidence (81–87°)
> 10 cells give only −75…−52 dB (16–20 cells needed); (l) the GPU crossover (128²) measured on a bare world; (m) not
> fetched: Yee 1966, Roden & Gedney 2000 (its formulas checked through two open papers), Taflove & Hagness (σ_max
> default; an open secondary source: Corbino, arXiv:2603.19056), Young 1995 and Joseph et al. 1991 (their schemes as
> Bidégaray-Fesquet 2008 gives them), Jackson; (aa) the flux monitor sees every plane wave weaker by 1 − O((k dx)²),
> depending on its direction; the "monitor" normalisation cancels it for R and T along the incidence axis only, and for
> scattering neither normalisation separates the scheme's error from the monitor's on the scattered waves (the same
> size: dielectric cylinder TM +0.03…+0.06 % exact / +0.10…+0.37 % monitor at 40 cells); (ab) stability: the node-map
> bounds are sufficient for nodes without poles and conductivity (dispersive nodes enter with ε∞); a double root on the
> unit circle (linear growth) is not detected; (ac) the Lorentz/Drude update is Young's explicit scheme (published
> sufficient condition c∞Δt/dx ≤ 1/2 in 2-D and ω0Δt ≤ 2/√(2εs/ε∞ − 1); admitted by its exact radius); the Kashiwa-type
> update, stable over the vacuum range, is not implemented; (ad) the licence of the Meep comparison test
> (`lfphys/tests/external/test_ext_fdtd_meep.py`, under the project's licence, imports GPL-2.0-or-later Meep through its
> API only) awaits the owner's decision: options (a)–(d) in the review's RESPONSE.md, F14.

In the plan column, replace the FDTD part, from "(a) conformal PEC" up to (not including) "(n) Landau–Lifshitz", with:

> (a) conformal PEC tested on the cylinder series; (b) the full tensor with averaged D (a D-based E update on both
> devices, CPML for D, its stability) and a convergence test that turns `test_te_high_contrast_cylinder_is_first_order_gpu`
> into a second-order one; (c) fill-fraction averaging of the poles, tested on a Drude cylinder; (d) the ramp built by
> FFT, like pulses; (e) layered-background incident fields; a smooth spectral taper at a Bloch cut-off (would admit such
> pulses with a precursor below 1e-9); (f) as the optics playground (P15.5, B9) needs them; (g) a validation table for
> display-only use; (h) `checks()` reporting cells per wavelength in the densest medium; (i) the pole energies and a
> Poynting balance test with dispersive media; (j) a discrete-Green's-function variant if needed; (k) a
> waveguide-below-cutoff test; (l) calibration on a typical scene; (m) the texts; (aa) an energy-consistent flux
> (products of E and H at their common nodes, no transverse averaging) or a direction-resolved correction, tested on
> the cylinder series; (ab) a node-map bound that includes the poles; a Jordan-block test of the amplification matrix;
> (ac) the Kashiwa et al. Lorentz/Drude update as an option, with its own closed-form and Meep tests; (ad) the owner
> chooses (a)–(d) of F14; for (d) the question joins V20's list.

(Letters (n)–(z) of the row belong to the other B8 parts and stay as they are; the new FDTD letters start at (aa).)

### 2. `engine/STATUS.md`, row V20 — add to the gap column, after "**no lawyer has checked them**"

> ; the comparison test `lfphys/tests/external/test_ext_fdtd_meep.py` imports Meep (GPL-2.0-or-later) and is under the
> project's licence — the owner's decision is pending (review B8-fdtd F14, options (a)–(d); STATUS V43 (ad))

and to the plan column, after "`COMMERCIAL.md` and `PUBLICATIONS.md`;":

> if the owner chooses F14 (d): whether a source file that only calls a GPL library's API may be distributed under the
> project's licence (the FSF's "combination" reading; the file is distributed without Meep);

### 3. `engine/lfphys/README.md`, "Electrodynamics", the row `core.em.fdtd` — replace the third cell with

> (P1, B8) Maxwell's equations in time on the Yee grid: 2-D TM/TE/both and 3-D, normalized units (c = ε0 = μ0 = 1);
> CPML (Roden–Gedney, graded σ, κ, α), PEC, PMC, periodic with Bloch phase; media ε, μ, σ, Drude/Lorentz (Young's
> scheme)/Debye (Joseph et al.'s trapezoid) poles, PEC (edge rule); sub-pixel averaging (the diagonal of Farjadpour's
> tensor, their VP-EP scheme: first order in general for in-plane E on curved surfaces) or staircase; soft/hard J and M
> sources; TF/SF plane wave as an exact plane wave of the grid (leak 2–3e-9 away from a Bloch cut-off; 2-D any angle,
> 3-D any direction, Bloch slabs); probes, DFTs, Poynting flux with its closed-form monitor factor, energy (conserved
> discrete form without poles), absorption, cross sections with the exact or the monitor's ("like") normalisation,
> near-to-far field (2-D/3-D); edits at any moment (polarization kept by medium value; bodies at plane-wave faces and
> misplaced monitor boxes reported or refused); stability checked per medium and over the node maps; bit-identical
> state; CPU NumPy or GPU 0 CuPy kernel (bit-identical). Tests: dispersion relation to 6e-15, magic step (also hard
> sources), PEC cavity modes, CPML −88…−95 dB to ~70° (grazing: 16–20 cells), R = the grid's exact closed form
> (Schneider 7.72/7.90) to 1e-4 and Fresnel at second order (incl. Drude/Debye/Lorentz, Brewster), dipole and
> line-source power, cylinder series (m = 1.5 at 40 cells: TM +0.03…+0.06 % exact / +0.10…+0.37 % monitor-normalised;
> TE to 0.3 % / 0.6 %), sphere vs `core.optics.mie` (−0.01…+0.76 % / +0.16…+0.84 % at 32 cells), Meep 1.35 (20 rows,
> like-normalised: the same discrete R to 1e-6 – 6e-6; `tests/external`)

### 4. `engine/lfphys/README.md`, "CPU and GPU" — in the GPU sentence, replace

> the FDTD stepper (B8) from 128² cells (×2.3) to ×67 at 4096² in 2-D and from ×6 at 32³ to ×76 at 256³ in 3-D,
> bit-identical to the CPU for real fields.

with

> the FDTD stepper (B8) from 128² cells (×2.3) to ×67 at 4096² in 2-D and from ×6 at 32³ to ×76 at 256³ in 3-D,
> bit-identical to the CPU for real fields (its device choice counts the plane waves' tables, the DFT accumulators and
> the dispersive nodes, review B8-fdtd F18).

### 5. `tests/external/make_results.py` (the shared part, not changed here)

For its owner: in `light-funnel-ext-meep` the Libraries table shows pymeep "not installed", version "-" (conda's Meep
has no pip metadata; `meep.__version__` = "1.35.0"), and the header says "in the image light-funnel-ext" for
`RESULTS_meep.md` too. A fallback to the module's `__version__` (and the image's name passed by an option) would fix
both; `RESULTS_meep.md` should then be regenerated.

### 6. Registry and archive

After the integration, the review folder moves to `reviews/archive/` with a registry row, e.g.: "`archive/2026-11-04_internal_B8-fdtd/` | internal (Opus subagent) | P1: `core.em.fdtd*`, `core.optics.cylinder`, the Meep comparison, 20 scripts | 2026-11-04 | `RESPONSE.md` (processed 2026-11-04: 18 of 20 fixed, F6 partly (the full tensor → V43 b), F14 open → owner (V43 ad, V20) — hard H sources diverged, unstable media slipped through an id cache, polarizations moved between media, a plane wave added mid-run broke cross sections; the flux monitor's −(k dx)²/8 had been counted as the scheme's accuracy and made "the engine nearer than Meep in 13 of 18" [error in earlier]: now a closed-form monitor factor and like-normalised Meep rows that agree with the grid's exact discrete R to 1e-6; the averaging named VP-EP and first order [error in earlier]; Bloch-slab pulses at the cut-off refused (a precursor, not the window); PEC/PMC lengths; mixed-node stability; +3 found: the PEC cylinder's stated numbers and two test pulses [error in earlier])". Archiving is the responder's step after integration (README, lifecycle 5); this processing leaves the folder in place.
