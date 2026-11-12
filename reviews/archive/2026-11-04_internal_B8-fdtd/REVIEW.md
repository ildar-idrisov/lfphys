# Review B8 / P1 — the FDTD solver (`core.em.fdtd` and its four helper modules, `core.optics.cylinder`, tests, Meep comparison)

**Status: awaiting processing.** Internal review by a subagent that did not write the code (2026-11-04). Per
`reviews/README.md`, the author of this review does not process it.

## 0. Scope, versions, environment

* Code under review (md5 in `reviewed_files.md5`; read 2026-11-04 between 18:15 and 18:40):
  * `lfphys/lfphys/core/em/fdtd.py`, `fdtd_geometry.py`, `fdtd_sources.py`, `fdtd_tfsf.py`, `fdtd_monitors.py`;
  * `lfphys/lfphys/core/optics/cylinder.py`;
  * `lfphys/tests/test_fdtd_{grid,boundaries,media,scattering,api}.py`, `test_cylinder_series.py`;
  * `lfphys/tests/external/test_ext_fdtd_meep.py` and `docker/meep/{Dockerfile,meep-explicit.lock}`;
  * `lfphys/sources/verification_2026-11-04_p1_fdtd.md`;
  * the `("em.fdtd", "em.fdtd")` entry of `_KERNEL_MODULES` in `lfphys/lfphys/core/backend.py`.
* `tests/external/README.md` and `sources/dependencies.md` changed during the review (18:34). This review describes
  the state after that change.
* Environment:
  * CPU: image `light-funnel-viz` with the engine mounted read-only and `LFPHYS_NO_GPU=1`.
  * GPU: GPU 0 only, through the session's `gpu_run.sh` (lock, wait until cool, 83 °C guard), every job under 5 minutes.
  * Meep: image `light-funnel-ext-meep` (Meep 1.35.0), engine mounted read-only.
  * Each script runs with `run.sh <name> <script>` from this folder. Its output sits next to it as `<script>.out`.
* The existing suite passes:
  * CPU (`run_tests.out`): 87 passed, 2 skipped (the GPU tests), in 63 s.
  * GPU 0 (`run_tests_gpu.out`): `test_gpu_equals_cpu` and `test_sphere_against_mie_converges_gpu` pass.
* Sources downloaded to the session scratchpad, outside the repository. No contact parameter, e-mail address or
  personal identifier was sent with any request. Every quotation below was grepped in them (`quotes_check.out`):
  * Schneider, *Understanding the FDTD Method* (author's PDF);
  * Farjadpour et al., Opt. Lett. 31, 2972 (2006) (author's copy);
  * Oskooi et al., Comput. Phys. Commun. 181, 687 (2010) (author's copy);
  * Bidégaray-Fesquet, "Stability of FD–TD schemes for Maxwell–Debye and Maxwell–Lorentz equations",
    arXiv:math/0506289 (SIAM J. Numer. Anal. 46, 2551 (2008));
  * arXiv:2304.00233 (libEMM); arXiv:2606.06910; arXiv:2603.19056;
  * the GNU GPL FAQ.
* Sources not obtained:
  * Yee 1966, Roden & Gedney 2000, Taflove & Hagness: paywalled or books.
  * Young 1995 (IEEE TAP 43, 422), Joseph, Hagness & Taflove 1991 and Kashiwa et al. 1990 are known here only as
    Bidégaray-Fesquet describes them.

Severity counts: **4 errors, 10 should-fix, 6 nits** (F1–F20). Section 2 lists what was checked and holds.

## 1. Findings

### F1 (error) — The stability check is cached by `id(Medium)`, so an unstable medium can be accepted

* **Location:** `fdtd.py:706-723`. The check stores `key = (id(m), self.dt)` in `_media_check_cache` and returns
  early on a hit.
* **Cause:** CPython reuses a freed object's address. When a checked `Medium` is freed (an `update_body`, a
  `remove_body`), a later, different `Medium` can get the same `id`. Its check is then skipped: it is neither refused
  nor computed.
* **Evidence:** `s07c_idcache.py` / `.out`.
  * Pattern: a body's medium edited live, a new `Medium` object for each edit, eps stepped 2.0 → 1.5 → 0.3, at S = 0.6
    in 2-D. eps = 0.3 needs S ≤ 0.39.
  * The unstable `Medium(eps=0.3)` was **accepted in 9 of 200 trials**.
  * The first accepted world blew up: «поля стали нечисловыми к t = 15.36 (шаг 512)».
  * A fresh world refuses the same medium (the control).
* **Fix:**
  * Key the cache by the medium's value, e.g. `(json.dumps(m.params(), sort_keys=True), dt)`.
  * Or keep a strong reference to the checked object in the cache, so that its id cannot be reused.
  * Add a regression test that repeats the edit pattern above.

### F2 (error) — Hard magnetic sources are imposed after the E update, so the E update never sees them

* **Location:**
  * `fdtd.py:1640` (`_apply_hard(t_e)` runs after the E update and the Debye step);
  * `fdtd.py:1895-1901` (H values at t − dt/2);
  * docstring `fdtd_sources.py:20-21`.
* **Cause:** the H value is overwritten after the curl update that the E update has already used. The next H update
  then starts from the imposed value plus a curl increment. The result is neither a hard nor a soft source.
* **Evidence:** `s10_walls_sources.py` / `.out` (2) and `s10b_hard_h.py` / `.out`.
  * 1-D at the magic time step, where a hard source of f(t) radiates exactly f(t − |x − x0|/c):
    * hard Ez: error 1.5e-8;
    * the dual hard Hz: **3.8e+36** (diverges).
  * 2-D, S = 0.5: hard Hz radiates a peak of 0.035 at 0.8 from the source; its dual hard Ez gives 0.197. They should
    be equal up to the half-step time shift.
* **Fix:**
  * Impose hard H right after the H update, before the soft sources and the E update, at t_{n+1/2}. Impose hard E
    after the E update, as now.
  * Add the dual test (hard Hz against hard Ez at the magic step).

### F3 (error) — On an edit, polarization is kept or dropped by the index into the rebuilt media list, not by medium

* **Location:**
  * `fdtd.py:977-987`: `same = mids[ia] == o_mid[ib]` compares positions in `self._media`, which is rebuilt from the
    body set on every edit.
  * The docstring `fdtd.py:55-56` promises "a polarization is kept at nodes that keep the same medium".
* **Evidence:** `s08_edits.py` / `.out`.
  1. `update_body(bid, medium=Drude)` on a body that was Lorentz: the nodes and the medium index are unchanged, so the
     Lorentz P (|P| = 0.459) is **carried into the Drude pole**. The arrays are identical, now advanced with the
     Drude coefficients.
  2. Bodies E (Debye, index 1) and D (Lorentz, index 2). Removing E shifts D to index 1. **D's polarization is zeroed
     (0.459 → 0)** although D did not change.
* **Effect:** an edit injects or removes polarization energy that nothing physical accounts for. A Lorentz state
  driving a Drude update is not a state of either medium.
* **Fix:**
  * Map the old index to the old `Medium` object and keep P only where `old_media[o_mid] is new_media[mid]`. The pole
    layout then matches automatically.
  * Test both cases above.

### F4 (error) — The incident spectrum assumes the plane wave existed from step 1

* **Location:**
  * `fdtd.py:1359-1368`: `_incident_dft` sets `n = np.arange(1, len(g) + 1)` and `keep = n > start_step`.
  * The series `ref_series` starts when the wave is added (`fdtd.py:1903-1907`, `add_source`).
* **Affected:**
  * `incident_intensity(start_step > 0)`;
  * `cross_sections` (it uses the monitor's `start`);
  * the normalisation in `far_field`.
* **Cause:** for a plane wave added at step s0 > 0 (an edit at a running moment), samples s0+1… are numbered 1….
  Monitors that start at step s0 then drop the first s0 samples of the pulse.
* **Evidence:** `s09_tfsf.py` / `.out` (2). The same dielectric cylinder and pulse, with only the step at which the
  plane wave and the flux box are added changed:
  * added at step 100: Q_sca / Q_sca(step 0) = 0.959, 1.010, 1.015;
  * added at step 400: **9e22 … 3e23** (the incident spectrum is ≈ 0).
* **Fix:**
  * Record `rec["ref_step0"] = sim.steps` when the wave is added, and number the samples from it. This number must
    also go into `state_dict`.
  * Test with a plane wave added mid-run against the same run from step 0.

### F5 (should-fix) — Cross sections and R divide a monitor-biased flux by an exact intensity

* **Locations:**
  * `fdtd_monitors.py:15-19` ("I_inc … exact for the grid's plane wave");
  * `fdtd.py:1370-1408` (`incident_intensity`, `cross_sections`);
  * the comparison `tests/external/test_ext_fdtd_meep.py`.
* **The two quantities:**
  * The face operator averages H across the plane and E/H along the face. For the grid's own plane wave it measures
    I·cos(k_n dx/2)·cos²(k_t dx/2), not I.
  * `incident_intensity` returns the exact (1/2)|G|²√(ε/μ).
  * The planar tests know this: `test_fdtd_media.py` multiplies its reference by the factor.
  * The cross sections and the Meep rows do not use the factor.
* **Evidence:**
  * `s09_tfsf.py` (5): the flux of the incident wave alone through a plane inside the total-field box, P/(I·L·cos θ) − 1:

    | incidence | cells per wavelength | P/(I·L·cos θ) − 1 | face factor |
    |---|---|---|---|
    | normal | 20 | −0.0124 | the factor to 8e-5 (to 4e-6 at 40 cells) |
    | 30° | 20 | −0.0159 | |
    | 45° | 20 | −0.0184 | |
    | (all three) | 40 | 1/4 of the 20-cell value | |

  * `s14_meep.py`, `s14b_like_normalised.py` — the Meep comparison re-run in `light-funnel-ext-meep`:
    * In the 7 one-dimensional rows with R of 0.35–0.9 (slab f = 0.75, 1.25; the five Drude rows), the engine–Meep
      difference as the test takes it is 6.2e-4 … 6.0e-3.
    * After the engine's R is divided by cos(k dx/2) (Meep normalises by its own measured incident flux), the
      difference is **≤ 2.1e-5** in all 10 one-dimensional rows. That is the rounding of the printed values: the two
      codes compute the same discrete R.
    * So the whole engine–Meep disagreement in these rows is this normalisation.
    * The claim "the engine nearer the exact value in 13 of 18 rows" (`verification_…_p1_fdtd.md:143`) is an artefact
      of it in the 1-D rows. The −(k dx)²/8 bias happens to cancel part of the scheme's error.
  * `s12_scattering.py` (1), the sphere at 16 cells per unit: Q_sca/Q_Mie − 1 = +1.66 / +0.33 / +1.20 %. With the
    normal-face factor removed: +1.97 / +1.03 / +2.46 %.
  * The claimed accuracies (cylinder 0.03–0.3 %, sphere 0.01–0.8 %) are of the same size as this bias. They
    therefore rest partly on cancellation.
* **Fix:**
  * Provide a like-normalised incident intensity: the incident grid wave measured by the same face operator. The
    factor is known in closed form for each face orientation; alternatively, offer an empty normalisation run as
    Meep does. Report both numbers.
  * Correct the docstring: I_inc is exact, but it is not what the monitor measures for that wave.
  * In the Meep test, compare like-normalised R (agreement ~1e-5), which is a far sharper test (see F8).

### F6 (should-fix) — The sub-pixel averaging is the diagonal-only (VP-EP) scheme, first order on curved surfaces

* **Locations:**
  * `fdtd_geometry.py:19-31` and ABOUT `:45-56`;
  * `fdtd.py:888-906` (`eff = 1/(n_a² <1/ε> + (1 − n_a²)/<ε>)`);
  * `README.md:91` ("diagonal of Farjadpour's tensor").
* **What the cited paper says:** the docs attribute the averaging to Farjadpour et al. eq. (1) and Kottke et al., and
  call the error "between first and second order". The paper itself classifies exactly this diagonal-only variant
  among the schemes that converge linearly:
  * "We also consider the VP-EP scheme, which is exactly the diagonal part of Eq. (1) for s = 1. Both Kaneda and VP-EP
    are equivalent to Eq. (1) for flat interfaces oriented along the grid (xyz) directions, but they do not satisfy
    the perturbation criterion for diagonal interfaces";
  * "Previous smoothing schemes do not satisfy this criterion and are therefore expected to have only linear
    convergence in general".
* **Evidence:**
  * `s17c_order_gpu.py` / `s17c_order_gpu_te.out` (GPU 0): TE, ε = 6 cylinder, a = 0.5, run until the field decays.
    Q_sca/Q_exact − 1:

    | frequency | 40 cells/unit | 80 | 160 | error ratio per doubling |
    |---|---|---|---|---|
    | f = 0.5 | 2.62 % | 1.44 % | 0.77 % | 1.83, 1.86: **first order** |
    | f = 0.8 | −0.18 % | +1.11 % | +0.88 % | non-monotone |

  * At 160 cells, staircase is *better* at f = 0.5 (0.40 %).
  * In TM the diagonal is the full tensor, because E_z is tangential everywhere. TM at ε = 2.25 converges at second
    order (`s17_subpixel_order.out`, ratios 3.7–4.2).
  * The tests use only ε = 2.25, where the first-order term is still small.
  * `s17.out`'s ε = 6 rows are invalid. Their time window was too short (`s17b_ringdown.out`: the TM ε = 6 resonance
    at f = 0.8 still rings at 10 % after 30 time units; −15 % at the window of s17, −7.3 % once converged in time).
* **Fix:** either:
  * implement the off-diagonal terms (Farjadpour: "we obtain Dy and Dz at the Ex point by simply averaging the Dy and
    Dz components from their four adjacent Yee points"), or
  * name the scheme correctly (VP-EP, as Farjadpour et al. classify it) and state "first order in general for
    in-plane E on curved surfaces", with the ε = 6 numbers in the validity.

### F7 (should-fix) — The Bloch-slab plane wave leaks up to 6e-6 near the cut-off, and the window tail is not enforced

* **Locations:**
  * `fdtd_tfsf.py:357-371`: the group-delay spread is estimated from three frequencies (min, max, median), and
    `dk = np.where(ok1 & ok2, dk, nb)` replaces the diverging delay near the cut-off by the continuum's.
  * `fdtd_tfsf.py:395-396, 410`: `tail` is only recorded and shown in `checks()`.
  * The claims of exactness: `fdtd_sources.py:35-37`, its ABOUT (statement: «утечка через границу — на уровне
    округления»), and `README.md:91` ("leak 2–3e-9; … Bloch slabs").
* **Evidence:** `s09b_slab_leak.py` / `.out`. A slab wave with two finite faces (x = 2, 4) in a periodic strip, so
  that only leak can reach the scattered-field side. Pulse 1.2 ± 0.15:

  | k_par | leak | window tail |
  |---|---|---|
  | 0, 2π·0.3 | 1.8–2.5e-9 | |
  | 2π·0.5 | 3.4e-7 | 9e-7 |
  | 2π·0.6 | **5.9e-6** | 1.7e-5 |
  | 2π·0.6, a narrower pulse | 2.3e-9 | |
  | 2π·0.9 | refused (omitted energy) | |

  * At k_par = 2π·0.6 the omitted energy is only 5.8e-9: accepted.
  * The leak tracks the tail.
  * Not detected by the tests: the oblique tests check R/R_d to 2e-4. With a single finite face, the earlier
    measurement in `s09_tfsf.py` (1) also mixes in the right layer's reflection.
* **Fix:**
  * Double M until `tail` < ~1e-9, or refuse with the reason.
  * Estimate the spread from the lowest propagating frequency of the band.
  * Add a two-face slab leak test near the cut-off.

### F8 (should-fix) — The Meep comparison's tolerance rests on an assumption that one row violates, and its rows test little

* **Location:** `tests/external/test_ext_fdtd_meep.py:23-29, 157-190`.
* **The assumption:** "both codes are second order in the cell". So each side's error at 40 cells would be within
  2|v40 − v20|/3.
* **Evidence:** `s14_meep.out`. Re-run: all 18 rows pass, the largest diff/tol is 0.83, as claimed.
  * But in the row **cylinder TE, f = 0.4** the engine's own error (6.4e-4) is outside its own bound (3.7e-4). Its
    convergence is non-monotone (−9e-5 at 20 cells, −6.4e-4 at 40; cf. F6). The row passes only because Meep's bound
    is wide.
  * The rows at f = 0.5, 1.0, 1.5 of the slab are Fabry–Pérot minima: exact R = 0, both codes ≤ 4e-3. They agree to
    3e-9 … 2.5e-5 against tolerances 1e-4 … 6e-2.
  * Like-normalised (F5), the 10 one-dimensional rows agree to ≤ 2e-5. The test accepts 6e-3.
* **Fix:**
  * Since an exact value exists for every row, bound each side by its distance to it at two or three resolutions,
    checking monotonicity, instead of assuming the order.
  * Compare the like-normalised discrete answers with a tight tolerance (a few 1e-5 here).
  * Give the R ≈ 0 rows an absolute tolerance, or replace them with off-resonance frequencies.

### F9 (should-fix) — An axis with a PEC (or PML) side and a PMC side is dx/2 longer than requested

* **Location:** `fdtd.py:609-621`. `n = ceil(m + elo + ehi)` with `elo`/`ehi` = 0.5 for PMC. The docstring `:23-24`
  says "The interior (the user's domain) is [0, Lx]".
* **Evidence:** `s10_walls_sources.py` (1). Size 0.6, dx = 0.05:
  * (pec, pec), (pmc, pmc), (pml, pec), (pml, pml): the interior is 0.6.
  * **(pec, pmc), (pmc, pec), (pml, pmc), (pmc, pml): the interior is 0.625.**
  * The lowest mode of the PEC/PMC box is at the grid frequency of Ly = 0.625 (FFT peak 0.6401). The requested 0.6
    gives 0.6507. That is a 1.6 % first-order geometric error in a solver documented as second order.
  * `test_pec_pmc_waveguide_modes_2d` asserts the realised length, so it cannot see this.
* **Cause:** on one Yee grid, an E-plane wall and an H-plane wall are an odd number of half cells apart.
* **Fix:**
  * Choose m so that (m + 1/2)·dx is the realisable length nearest to L.
  * Report "interior ≠ requested" in `describe()` and `checks()`, or refuse unless L/dx is a half-integer.
  * Correct the docstring.

### F10 (should-fix) — "CPML −88…−95 dB at 10 cells" holds only up to ~70°

* **Locations:** `fdtd.py:35, 69, 106` (ABOUT validity); `README.md:91`.
* **Evidence:** `s11_dispersion_cpml.py` / `.out` (2).
  * The tests' geometry is reproduced: −87.8…−95.1 dB.
  * Grazing incidence along a long boundary, against a reference in a 24 × 24 domain; image-path angles 81.5°, 85.7°,
    87.1°:

    | layer | 81.5° | 85.7° | 87.1° |
    |---|---|---|---|
    | the default 10 cells (κ = 1, α = 0) | **−74.5 dB** | **−57.6 dB** | **−52.4 dB** |
    | κ = 5, α = 0.2 | | | −60.4 dB at worst |
    | 20 cells | −114…−136 dB | | |

* **Fix:** state the angular range of the claim and the grazing numbers in the validity. Add a grazing-incidence row
  to the tests or recommend 16–20 cells for grazing geometries.

### F11 (should-fix) — Stability is checked per medium; mixed nodes can be unstable

* **Locations:** `fdtd.py:706-723` and the docstring `:25-28` ("checked by the von Neumann amplification matrix of each
  medium … a world beyond it is refused").
* **Evidence:** `s07_stability.py` (d).
  * E nodes take ε = 0.25 from medium A (ε 0.25, μ 4). H nodes take μ = 0.25 from medium B (ε 4, μ 0.25). Each medium
    alone has n = 1.
  * The world is accepted at S = 0.5. The local wave speed is 4, so the 1-D limit is S = 0.25.
  * The fields are NaN after 500 steps.
  * This needs media with ε < 1 or μ < 1, so it is rare. The documented guarantee still fails.
* **Fix:** for plain nodes, add a sufficient global bound from the actual node maps, S ≤ √(min_E ε · min_H μ)/√D
  (or the per-axis form). It is cheap and closes the gap.

### F12 (should-fix) — Plane-wave faces and monitor boxes are not checked against bodies and regions

* **Locations:**
  * `fdtd_tfsf.py:59-152`: `build_tfsf` checks only absorbing layers and walls. Its ABOUT validity requires
    «однородный фон без потерь у граней».
  * `fdtd.py:1223-1231, 1384-1408`: a near-to-far or scattered-flux box is not checked to lie in the scattered-field
    region.
* **Evidence:** `s09_tfsf.py` (3). A dielectric slab crossing two TF/SF faces is accepted without a word.
  `checks()` shows only `window_tail` and `omitted_energy`. Bodies added later are not checked either.
* **Fix:** on `add_source`, and on every later body edit, refuse or flag in `checks()` any correction node whose
  medium is not the background. Flag a near-to-far or `scattered` box that intersects the total-field box.

### F13 (should-fix) — The pole updates and their stability analysis have no named source; the refusal hint is not the published condition

* **Locations:**
  * `fdtd.py:39-46` and the ABOUT `basis` `:109-113` (no source for the ADE forms);
  * `fdtd.py:303-345` (`amplification_radius`);
  * the hint in the refusal message `:722` («у полюсов: ω0·Δt < 2 и плазменная частота·Δt < 2·√ε∞»).
* **What the schemes are:**
  * The Lorentz/Drude update (explicit central differences in P at t_n) is the scheme Bidégaray-Fesquet calls the
    "Lorentz–Young model" (Young, IEEE TAP 43, 422 (1995)), her eq. (15).
  * The Debye update is the trapezoidal "Joseph et al." scheme.
* **The engine's matrix is right.** `s07b_young_matrix.py` / `.out`: its amplification matrix equals her printed
  matrix G for the Young scheme to 12 digits. Examples: 1.830181974192 = 1.830181974192; 5.036184618253 =
  5.036184618253 [useful].
* **The published conditions differ from the hint:**
  * She states: "there is an extra condition on the time step: ω < 2/(2ε′s − 1)", with ω = ω1²k²/2.
  * And: "as for the Lorentz–Joseph et al. scheme we need a twice smaller k than for raw Maxwell equations: q ≤ 2
    instead of q ≤ 4".
  * And she recommends Kashiwa et al.'s scheme ("the Kashiwa et al. model seems to overcome others for Lorentz
    material"), stable for q < 4 with no extra condition.
  * The engine's message suggests ω0Δt < 2 instead. For Δε = 5 the published bound is ω0Δt ≤ 2/√11 ≈ 0.6.
* **A limitation of the check:** it uses ρ ≤ 1 + 1e-6. It cannot see defective roots on the unit circle (her
  "eigenvectors → unstable" rows), which give polynomial growth.
* **Note:** her q ≤ 2 is a sufficient condition. The engine admits by the computed radius, and its long runs in
  `s07.out` (a) stay bounded up to S = 0.99 for small ω1Δt.
* **Fix:**
  * Cite Young 1995, Joseph et al. 1991 and Bidégaray-Fesquet 2008 in `basis` and in the sources file.
  * Replace the hint by the published conditions.
  * Consider the Kashiwa-type (trapezoidal) Lorentz/Drude update. It keeps the vacuum Courant range.

### F14 (should-fix) — Licence hygiene of the Meep test module itself

* **The image is fine:**
  * `light-funnel-ext-meep` is separate, pinned by digest and by 124 md5-pinned packages, and documented as never
    distributed (`dependencies.md` §10.5).
  * The engine never imports Meep: `grep` finds `import meep` only in `tests/external/test_ext_fdtd_meep.py:44`.
* **The open question:** that test module is part of the repository under `LicenseRef-lfphys-Research-1.0`, and it
  imports a GPL-2.0-or-later library.
  * The FSF's reading (GPL FAQ, "If a library is released under the GPL …"): "Yes, because the program actually links
    to the library. As such, the terms of the GPL apply to the entire combination."
  * Whether distributing the test's source alone (without Meep) is affected is a legal grey zone.
  * The noncommercial licence is not GPL-compatible.
* **Fix:** either:
  * license this one file under a GPL-compatible licence (e.g. MIT or GPL-2.0-or-later — it contains no engine code),
    or
  * keep it out of the distributed tree, or
  * add the question to the lawyer's list (STATUS V20).

### F15 (nit) — `energy()` "exactly conserved … in a closed lossless box" is wrong for lossless dispersive media

* **Location:** `fdtd.py:1434-1436`; the module docstring `:66-68`.
* **Evidence:** `s08_edits.py` (3). With a γ = 0 Lorentz body in a closed PEC box, `energy()["total"]` ranges over
  0.17–1.00 of its start: the polarization's energy is not counted.
* **Fix:** say "non-dispersive, non-conducting", or add the pole energy.

### F16 (nit) — A 3-D polarization parallel to the direction gives a silent zero wave

* **Location:** `fdtd_tfsf.py:302-305`.
* **Evidence:** `s09_tfsf.py` (4). With direction (0, 0, 1) and polarization (0, 0, 1) the wave is accepted, and max|E|
  is 0 after 80 steps.
* **Fix:** refuse when |p × k̂| is ≈ 0.

### F17 (nit) — The continuous-wave ramp is described two ways

* **Location:** `fdtd_sources.py:37-38` ("the ramp travels with the continuum group delay") against `fdtd_tfsf.py:11`
  and the code `:326-334` (the *discrete* group delay from the grid's k).
* **Fix:** make the first say "discrete".

### F18 (nit) — Cost estimate and memory footprint

* **Location:** `fdtd.py:1910-1915, 1989-1997`.
* **The rates hold.** `s15_bench.out` and `s15_bench_gpu.out` measure the CPU rates at 0.95–1.5× the table (host
  shared with other jobs) and the GPU rates at 0.92–1.01×; GPU and CPU break even at 64², and the GPU is ×2.4 faster
  at 128² [useful].
* **But:**
  * `other_device_per_step_s` omits the complex factor that `per_step_s` applies.
  * `_footprint` (used to choose the device) leaves out:
    * the TF/SF tables, up to `MAX_TABLE_BYTES` = 512 MB, and their device copy;
    * the DFT accumulators and the dispersive arrays.
* **Fix:** add the complex factor to `other_device_per_step_s`, and add these arrays to `_footprint`.

### F19 (nit) — Records

* `verification_2026-11-04_p1_fdtd.md:53` on arXiv:2606.06910:
  * It says "the authors' names are not legible". The title page reads Victory Obieke, Oregon State University.
  * The paper is an acoustic pressure–velocity FDTD. The CPML recursion is the same, but say so.
* An open secondary source for σ_max = 0.8(p + 1)/(η Δx) exists: Corbino, arXiv:2603.19056, eq. (29), "A common
  estimate for the maximum conductivity is [2]". Its form has η, the vacuum case of the engine's 1/√(εμ).
* `tests/external/RESULTS.md` still has **0 Meep rows**. The 18-row result exists only as numbers in the verification
  file; `RESULTS_meep.md`, named in the README, has not been generated.
* The "13 of 18 nearer" claim: see F5.

### F20 (nit) — A blown-up world can return NaN fields without `Unstable`

* **Location:** `fdtd.py:1585`. Health is checked only when `steps % 256 == 0`.
* **Evidence:** `s07_stability.py` (d). Ten calls of `advance(50)` ended with NaN fields and no exception.
* **Fix:** also check at the end of each `advance`. One reduction per call is cheap.

## 2. Checked and holds

| item | evidence | status |
|---|---|---|
| Yee dispersion relation | `s11` (1): measured ω/ω_Yee − 1 ≤ 5e-10 (FFT-peak fit, independent of the tests' recurrence) at 4 wavevectors × 2 grids. The continuum is off by 3e-4 … 1.1e-1. `yee_wavenumber` inverts `yee_frequency` to 9e-16 | [useful] |
| CPML in the tests' geometry | `s11` (2): −87.8…−95.1 dB (default), −84…−89 dB (CFS) | [useful] (range of validity: F10) |
| Conserved discrete energy | `s16`: ½Σε\|Eⁿ\|² + ½Σμ H^{n−½}·H^{n+½} is the leapfrog invariant (derivation in the script header). Drift 1.7–4.1e-16 with PEC/PMC/periodic sides, both polarisations, Bloch complex fields, a PEC body (edge rule), 3-D; a lossy Debye body changes it by 45 % (control) | [useful] (wording: F15) |
| Planar R and Fresnel convergence | the suite passes. The Meep re-run shows the engine's discrete R equals Meep's to ≤ 2e-5 once like-normalised (F5) — an independent confirmation of the media and interface implementation | [useful] |
| Sphere vs `core.optics.mie` | `s12` (1): +1.66 / +0.33 / +1.20 % at 16 cells, as claimed; dσ/dΩ within 0.03–5.9 %. GPU 0 at 32 cells: +0.76 / +0.01 / +0.30 % (`run_tests_gpu.out`), as claimed | [useful] (normalisation: F5) |
| Dipole power, 3-D | `s12` (2): +1.7 / +2.7 / +4.1 % at 10 cells per unit, +0.4 / +0.7 / +1.0 % at 20; second order | [useful] |
| Near-to-far normalisation | `s12` (3), no scatterer. 3-D z-dipole \|A_θ\| against \|I l sin θ\|: 0.03–1.2 % at 20 cells, cross-polarisation ≤ 0.14 %. 2-D line current against the Hankel asymptote: ≤ 0.9 % (20 cells), ≤ 0.22 % (40). The far-zone formulas E_θ = ik g(ηN_θ + L_φ), E_φ = ik g(ηN_φ − L_θ) and the 2-D TM/TE forms were re-derived from the vector potentials with exp(−iωt) and agree | [useful] |
| Cylinder series conventions | re-derived from the boundary conditions (TM, TE, PEC); exp(−iωt), Im m ≥ 0 absorbing, as in `core.optics.mie`. Q_abs > 0 for m = 1.5 + 0.1i and 2 + i, negative for conj(m) (`s12` (4)). The TE Rayleigh limit Q_sca → (π²x³/4)\|(m² − 1)/(m² + 1)\|², not in the tests, converges as x² (4.6e-4, 1.4e-4, 4.2e-5 at x = 0.02, 0.01, 0.005) | [useful] |
| TF/SF fixed family | the suite's 2-D (0°, 30°, 57°) and 3-D oblique leak tests pass; the construction (H = K × E/(Ωμ), K·E = 0, every component at its own node and time, corrections with the target node's cb/db, consistent inside/outside per node) is exact for a homogeneous lossless background | [useful] (slabs: F7) |
| ADE algebra | Lorentz/Drude coefficients, the Debye trapezoid, `epsilon_discrete` and the E update re-derived. The amplification matrix equals the published one (F13) | [useful] |
| Stability sampling (257 points) | `s07` (b): 300 random media; no case is accepted at 257 points and unstable at 20001 | [neutral] |
| PEC/PMC placement | PEC on the E plane (index 0, and the wrap to index 0 at the far side), PMC on the H plane half a cell in; correct except the mixed length (F9) | [neutral] |
| The PEC edge rule | an empirical choice (an E component is zeroed only if its whole Yee edge is in the conductor), documented with its measured effect; no literature source given; first order like any staircase | [neutral] |
| Edits: ½Δε\|E\|² | holds by construction (E kept); tested | [neutral] (polarizations: F3) |
| State round trips | `s13` (1): bit-identical after 150 further steps (fields, ψ, P, monitors) in four worlds the tests do not build — a ramped continuous plane wave + conductor + edits + a plane wave added mid-run; a Bloch TE slab + Drude; PEC/PMC/PML both polarisations + Lorentz + hard source; 3-D oblique plane wave + sphere + near-to-far | [useful] |
| GPU = CPU | `s13_state_gpu_gpu.out`: real fields bit for bit in three worlds; complex 6.3e-15; the suite's GPU test passes | [useful] |
| Layers | `core` placement is right (Maxwell's equations solved with stated, tested error; pole parameters are the user's model); the kernel is registered in `_KERNEL_MODULES` and imports cleanly | [neutral] |
| Meep image hygiene | separate image, base by digest, 124 packages by URL + md5, never distributed per README/dependencies §10.5, engine never imports Meep | [neutral] (F14) |

## 3. Files in this folder

* **Scripts, each with its `.out`:**
  * `s07_stability.py`: amplification vs runs, sampling, id cache, mixed media;
  * `s07b_young_matrix.py`: the published G against the engine;
  * `s07c_idcache.py`;
  * `s08_edits.py`;
  * `s09_tfsf.py`: slab, late plane wave, body at faces, polarization, monitor bias;
  * `s09b_slab_leak.py`;
  * `s10_walls_sources.py`, `s10b_hard_h.py`;
  * `s11_dispersion_cpml.py`;
  * `s12_scattering.py`: sphere, dipole, near-to-far, cylinder;
  * `s13_state_gpu.py`, plus `s13_state_gpu_gpu.out`;
  * `s14_meep.py`, `s14b_like_normalised.py`;
  * `s15_bench.py`, plus `s15_bench_gpu.out`;
  * `s16_energy.py`;
  * `s17_subpixel_order.py`, `s17b_ringdown.py`, `s17c_order_gpu.py`, plus `s17c_order_gpu_te.out`.
* **Runs and records:**
  * `run.sh`: the CPU runner;
  * `run_tests.out`, `run_tests_gpu.out`: the suite;
  * `quotes_check.out`: the grep of every quotation;
  * `reviewed_files.md5`.
