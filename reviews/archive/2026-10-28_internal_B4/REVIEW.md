# Internal review of batch B4 (P14.6, P14.5, P14.9, v11 changes, the owner's corrections of 2026-10-28)

**status: awaiting processing**

Reviewer: an internal subagent that did not write the code. Delivered 2026-10-28. The scope is the brief of
2026-10-28: the uncommitted working tree under `engine/` against commit a43a8a3 (B3). The author changed the tree
during the review (frame field `rate` → `speed_actual`; device-aware v12 tests). The findings below are for the
**current** tree. Each one says what was already different in the tree as delivered.

Environment: Docker image `light-funnel-viz` (CPU, OMP 4), the engine mounted read-only at `/lf`. There were two
short GPU 0 runs (`out/gpu_tests.txt`, 3.7 s, 40–43 °C, while none of the author's GPU jobs was running). Browser
checks used the reviewer's own server on port 8502 (read-only mount, scratch runs folder, stopped afterwards) and
`mcr.microsoft.com/playwright:v1.58.2-jammy`. Every script names its root path in its header; the scripts and their
outputs are in this folder and in `out/`. Script numbers skip c02, which was planned and then dropped.

Sources used for the formulas, read from the downloaded texts and the rendered PDF pages: arXiv:2105.14744 (Das &
Struyve, PRA 104, 042214), arXiv:2102.02661 (Das & Nöth), arXiv:1601.03715 (Tumulka), arXiv:2211.13362 (Das,
Deckert, Kellers, Krekels, Struyve).

## Summary of findings

| id | severity | one line |
|---|---|---|
| B4-1 | error (fixed mid-review, verified) | the runner's new frame field `rate` overwrote v04's own `rate` (dτ/dt): v04's «dτ/dt сейчас» showed the playback speed |
| B4-2 | error | v12's semiclassical curve and its «Итоги» totals are aliased for longer trains (total 0.73–1.17 instead of 1 in worlds the cost guard accepts) |
| B4-3 | should-fix | v11/v12 observer and mark: at the nominal θ = 180° the visibility is 0.25. The scan shows the angle is miscalibrated (minimum ≈ 0.08 near 150°). The texts and the preset say «полос нет» / «путь известен полностью» |
| B4-4 | should-fix | the Marchewka–Schuss intensity in `detection.py` misquotes Das & Struyve Table I (ψ̄ of the Dirichlet problem and λ′ε: a factor 4ε); the paper is Das **& Struyve** |
| B4-5 | should-fix | v12 reveals at t = 0 the observation window computed from the closed-form leave time: the header field, the chart's time axis, «окно наблюдения 1,7 t₀» |
| B4-6 | should-fix (fixed mid-review, verified) | v12's tests failed on a CPU-only host (cost bound of GPU 0, GPU test without skip) |
| B4-7 | nit | v12's Bohm first-arrival law and its KS reference use a rectangle sum: shifted by dt/2 (3·10⁻³ of probability) |
| B4-8 | nit | v12's joint distribution J(x, t) shows rows up to half a bin into the future when scrolled back; the last partial bin is dropped |
| B4-9 | nit | checks that cannot fail on wrong physics: `dipole` (passes with a wrong radial function), `period`, `arr_abr_identity` |
| B4-10 | nit | orbitals3d reveals at t = 0 the largest density over the whole period (the brightness scale of the cloud and the slices) |
| B4-11 | nit | the runner's `lag` stays false when a single step overruns the frame (the measured speed is right); «факт» stays visible on an archived world |
| B4-12 | nit | text and number inconsistencies: STATUS V31 (0.9 % at 1000×), v12 README `arr_state` tolerance, Tumulka eq. numbers, the record's growth per plane placement |

---

## B4-1 (error; fixed mid-review, verified): the runner overwrote v04's `rate` field

[error in earlier] **Location.** As delivered, `visualizations/server/lfviz/sim.py` `_frame` set
`meta["rate"] = self.rate()` after the world's `frame()`. In v04, `viz.py:843` puts the body's dτ/dt into the frame as
`rate`, and `web/view.js:398` shows it as «dτ/dt сейчас».

**Claim.** RULES.md §3 (frame row, as delivered): the runner adds `rate`, the world's measured speed.

**Evidence.** `out/c04_speed_rate_as_delivered.txt`: on the delivered tree the v04 frames' `rate` is the playback
speed, 0.0116 s/s at the default speed, where dτ/dt ≈ 0.98. On the current tree, `out/c04_speed_rate.txt`, the field
is `speed_actual` and v04's `rate` is 0.975–0.982. The author found this through v04's tests during the review. The
rename was checked: `out/world_tests_after_rename_cpu.txt` (v12, v04 and server tests: 84 passed, 1 skipped). A scan
of all `frame()` bodies finds no other top-level key that collides with `t`, `cpu_ms`, `lag` or `speed_actual`. v07
has a `rate` key, but nested in `settings`.

**Fix.** Done (rename; RULES.md now says that a world must not use these keys). Suggested addition: an assertion in
the runner, or a test over every world, that `frame()` returns none of the runner's keys, so that the next added key
cannot collide silently.

## B4-2 (error): v12's semiclassical curve and its totals are aliased for longer trains

**Location.** `visualizations/v12_arrival_times_2d/viz.py:48` (`CURVE_N = 1501`), `:298-316`
(`_initial_state_rules`), `:381-387` (`_rule_stats`); drawn in `web/view.js:78-82`.

**Claim (README).** The curves from the initial state are drawn up to the time shown and summarised in «Итоги по
правилам»: the probability within the window and the mean time.

**Evidence.** Π_SC(t) = (mD/ħt²)|ψ̃(mD/ħt)|² of a train carries the comb |Σⱼ e^{ik·j·sep}|² in k = mD/ħt (Das &
Struyve eq. 43). Its fringes are about 2πD/(sep·k₀²) apart in t, while v12 samples the whole window, (N − 1)·sep/v₀
long and more, with 1501 points.
* `c03_train_curve_sampling.py` → `out/c03_train_curve_sampling.txt`. For N = 8, sep = 60 λ the sample step is
  1.09·10⁻² t₀ against a fringe spacing of 1.67·10⁻² t₀. The total is 0.2738 on v12's grid and 1.000000 on a fine
  grid. The largest sampled value is 14.0, against 200.5 between samples.
* `c03b_train_worlds_build.py` → `out/c03b_train_worlds_build.txt` reads the world's own `Simulation.curves`. The
  semiclassical «P за окно» is:

  | N | sep | total |
  |---|---|---|
  | 4 | 60 λ | 1.1744 |
  | 8 | 30 λ | 0.7272 |
  | 4 | 90 λ | 0.8323 |
  | 5 | 60 λ | 0.9607 |

  The exact value is 1.0000 in each case, and all four worlds pass the cost guard on GPU 0. The mean time is off as
  well.
* The preset `train` (N = 4, sep = 30 λ) is resolved (1.000000), and so are ABK and the absorbing boundary in every
  case.

No check covers the semiclassical rule, so the run reports the wrong numbers as results.

**Fix.** Compute the semiclassical rule in k, where it is exact:
* F_SC(t) = ∫_{k > mD/ħt} |ψ̃|² dk;
* total = F_SC(t_obs);
* mean = ∫ (mD/ħk)|ψ̃|² dk / total over k > mD/ħt_obs.

Draw the bin average [F_SC(t_{i+1}) − F_SC(t_i)]/Δt per drawn sample, which cannot alias. Add a check of the curve's
total against F_SC(t_obs).

## B4-3 (should-fix): the observer and the mark at θ = 180° do not mark the path fully; the angle is miscalibrated

[error in earlier] **Location.**
* `visualizations/v11_double_slit_2d/engine/apparatus.py:124` (`marker_angle_to_coupling`: θ = 2b₀w/(ħv₀), first
  order, free mean speed).
* `viz.py:90` (help: «интерференция гаснет как |cos(θ/2)|»), `:99` («180° — путь известен полностью»), `:110` (preset
  `observer`: «— полос нет»).
* `visualizations/README.md:80` (owner guide: «180° — известен полностью»).
* `v11_double_slit_2d/README.md:62` and the «Measured» paragraph ("the mark's residual coherence is not understood …
  candidates are the field's edges … and the channel's transverse modes", STATUS V26).

**Claim.** The observer added for the owner's correction 2 (a two-level which-path detector at slit B, any particle)
turns its state by θ while the particle is in slit B. At 180° the path is fully marked and the fringes vanish.

**Evidence.** The author's own measurement on the presets is visibility 0.25 at 180° for `mark180` and `observer`.
`c08_v11_observer_angle.py` → `out/c08_v11_observer_angle.txt`, `out/c08b_v11_observer_angle.txt` scans the
visibility check against the nominal θ on the tests' small geometry (He-4 observer, a = 1.5 λ, w = 1 λ, edges 0.2 λ):

| θ | 130° | 140° | 145° | 150° | 155° | 165° | 180° |
|---|---|---|---|---|---|---|---|
| visibility | 0.201 | 0.127 | 0.098 | **0.082** | 0.087 | 0.143 | 0.257 |

The minimum lies near θ ≈ 150°, not at 180°. The rotation the coupling actually makes is about 1.2 times the nominal
one, so the nominal 180° turns the detector by about 210°, and |cos(105°)| ≈ 0.26. That matches the residual. [useful]

Why (a hypothesis consistent with the scan): b₀ is set from the first-order formula for the free mean speed. Inside
the channel the longitudinal wavenumber is lower, because the transverse mode carries energy
E⊥ = (π/a)²/2 = 0.11 E₀ here. b₀ itself is not small: 0.5 E₀ at w = 1 λ, 0.25 E₀ at the presets' w = 2 λ. The
lowest-mode estimate (k₋ − k₊)w = 3.49 rad, against the designed π, already moves the minimum to about 162°. The
tanh edges narrow the effective opening further. The remaining floor of about 0.08 at the minimum is what the other
candidates may explain: unequal transmission of the ±b₀ components, the speed spread, edge forces.

So the open item V26 is mostly a calibration of θ, not an unknown residual coherence. The same holds for the spin mark.

**Fix.**
* Calibrate b₀ by the channel. Either use 1-D transfer matrices of the ±b₀ profile at the longitudinal energy of the
  channel's lowest mode, or measure in the run the reduced state of the mark behind slit B,
  θ_actual = 2 arccos|⟨m_A|m_B⟩|. Show θ_actual and use it as the reference of `visibility`.
* Alternatively keep b₀ ≪ E₀, for example with a longer marking region.
* Until then, the help texts, the owner guide and the `observer` preset label should state that the nominal θ is a
  first-order angle and that 180° leaves visibility of about 0.25.

The observer box itself is drawn correctly. In both the 3-D scene and the plane window it sits in slit B's channel
(x = +d/2, width a, thickness w, opacity 0.12 + 0.5 sin²(θ/2)); see the screenshot `out/c05_v11_observer.png`.

## B4-4 (should-fix): the Marchewka–Schuss intensity misquotes Das & Struyve, Table I (a factor 4ε)

**Location.** `lfphys/lfphys/theories/models/detection.py:14-16` (module docstring), `:38` (ABOUT statement),
`:100-102` (`marchewka_schuss_intensity`); `visualizations/v12_arrival_times_2d/README.md:52`.

**Claim.** λ_MS = (λ₀/π)|∂ψ/∂x(L, t)|² "with ψ the free wave" (Das 2021, Table I).

**Evidence.** Table I of arXiv:2105.14744 (rendered page 2) reads (λ′ε/π)|∂ₓψ̄(L, t)|² with ε = ħ/m. Sec. III.B
(eq. 27) defines ψ̄(x, t) = ψ(x, t) − ψ(2L − x, t), the Dirichlet solution on (−∞, L], and states
∂ₓψ̄(L, t) = 2∂ₓψ(L, t) (eq. 28; the bar and the prime are lost in the text dump, lines 266–273).

`c01_ms_intensity_source.py` → `out/c01_ms_intensity_source.txt`:
* |∂ₓψ̄|²/|∂ₓψ_free|² = 3.99984 on the paper's Fig. 3 train (finite difference).
* With the paper's λ′ = 0.01, the engine's formula gives P(∞) = 0.000000; Table I gives 0.2799.
* The paper's eq. 31 at t = τ₀ (0.014367) agrees with Table I using ψ̄ (0.014364), not with the engine (0.359).

v12 is not affected physically, because it rescales the strength anyway: λ_MS = λ₀(v₀/k₀²)∫|∂ψ/∂z|²dx, which is
Table I with λ′ = πλ₀v₀/(4εk₀²) = λ₀/8 in v12's units. But the engine function advertises Table I, and a caller who
passes the paper's λ′ gets 1/(4ε) times the paper's rate.

**Fix.**
* Implement Table I as written, for example `marchewka_schuss_intensity(dpsi_free_L, lam_prime, eps)` =
  (λ′ε/π)·4|∂ₓψ_free(L)|², or take ∂ₓψ̄ and say so.
* Correct the docstring and ABOUT.
* State the relation of v12's λ₀ to λ′ in its README.

**Also (nit, same place).** arXiv:2105.14744 = PRA 104, 042214 is by S. Das **and W. Struyve**. This is on its title
page (lines 3, 6) and in ref. [24] of arXiv:2211.13362 ("S. Das and W. Struyve, … Phys. Rev. A 104, 042214 (2021)").
B4 cites it as "Das, Phys. Rev. A 104, 042214 (2021)" or "Das 2021": `arrival_times.py:20, 48`,
`detection.py:14, 44, 96, 101`, v12 README:31, 47, 51, 90 and `viz.py:21, 69, 104, 484, 498`,
`test_arrival_times.py`.

## B4-5 (should-fix): v12 reveals the window computed from the closed-form leave time at t = 0

**Location.** `visualizations/v12_arrival_times_2d/viz.py:134` (`t_obs` = 1.02 × the closed-form leave time),
`:543` (header `arrival.tau_obs`); `web/view.js:65` (the chart's time axis ends at `tau_obs` from the first frame),
`:170` (info panel «окно наблюдения … t₀»).

**Claim.** RULES §2.2 / AGENTS §3.3: a consequence is revealed when the run's time reaches it.

**Evidence.**
* `c07_v12_small_runs.py` (c) → `out/c07_v12_small_runs.txt`: at t = 0 the header carries tau_obs = 1.70 t₀ (gauss)
  and 10.94 t₀ (backflow). That is the time by which all but 10⁻⁴ of the probability has crossed the plane, computed
  from FreeGaussians, which is the arrival itself.
* `out/c05_browser.txt` (current tree): at t = 0 the panel shows «окно наблюдения 1,7 t₀».
* `out/c05_v12_t0_chart.png`: the empty chart's axis already ends at 1.7 t₀.

The precedent is review B2, where the header revealed the duration [error in earlier there]. The ABK, semiclassical
and absorbing-boundary curves are also sent whole at t = 0 (`arrival_ref`), but the view clips them to the time shown,
which is correct.

**Fix.** Keep `t_obs` inside the run. Let the chart's axis grow with the run's time, or use a set-up scale (multiples
of t₀ = D/v₀), and show the window's length only in the final result.

## B4-6 (should-fix; fixed mid-review, verified): v12's tests failed on a CPU-only host

**Location.** `v12_arrival_times_2d/tests/test_v12_arrival_times_2d.py:45` (as delivered:
`assert 0 < est_cost < 600`, GPU 0's limit) and `:134` (the GPU = CPU test had no `skipif`).

**Evidence.** On the delivered tree, `out/world_tests_b4_cpu.txt` shows 4 failed: `test_presets_build[train]`,
`[backflow]`, `[slits]` (CPU estimates of 929 s and 727 s against 600) and `test_gpu_equals_cpu`. The owner guide
documents a CPU profile (`viz-cpu`).

The current tree bounds the cost by `COST_LIMIT[device]` and skips without a GPU: `out/world_tests_after_rename_cpu.txt`
shows 84 passed, 1 skipped. Both GPU = CPU tests pass on GPU 0 (`out/gpu_tests.txt`).

## B4-7 (nit): v12's Bohm first-arrival law is shifted by half a step

**Location.** `v12_arrival_times_2d/viz.py:265-268` (`bohm_law`) and `:428-429` (the KS reference):
`C = np.cumsum(J) * dt`.

**Evidence.** `out/c07_v12_small_runs.txt` (b): the world's law differs from the exact one,
F(0) − min_{s ≤ t} F(s) from the closed-form P(z < D, t), by up to 3.1·10⁻³ (gauss) and 2.5·10⁻³ (backflow). That is
J_max·dt/2, a time shift of dt/2, while the flux itself agrees with the exact free current to 3·10⁻⁶. The KS check is
not affected at its tolerance (D = 0.045 against 0.11).

**Fix.** Use `cumulative_trapezoid(J, tau, initial=0)` (with J(0) = 0 at t = 0), or the engine's
`bohm_first_arrival`.

## B4-8 (nit): the joint distribution J(x, t) runs half a bin ahead when scrolled back

**Location.** `v12_arrival_times_2d/web/view.js:136`: `while (nr > 0 && (nr − 0.5)·tbin·tu > nowT) nr −= 1`.

**Evidence.** A row covers [i, i + 1]·tbin and is drawn up to (i + 1)·tbin (`:148`), but it is shown once the time
passes (i + 0.5)·tbin. In live play this is causal, because rows are sent only when complete. Scrolled back, up to
half a bin of the future is shown. Also, `viz.py:229-233` appends a row only when `tbin` steps have accumulated, so
the last partial bin is never sent.

**Fix.** Use `nr·tbin·tu > nowT`, and flush the partial bin in `_finish`.

## B4-9 (nit): checks that cannot fail on wrong physics

**`dipole` (`server/lfviz/orbitals3d.py:355-377`).** Labelled "⟨x⟩ … по облаку этого запуска против
2Re(c₁*c₂⟨1|r|2⟩e^(−iωt))". Both sides come from the same `Orbital` objects: the quadrature of sp.psi on the one
side, `C.dipole` of the same radial functions and the same energies on the other. The drawn cloud is not used.

`c06_orbitals.py` (c) → `out/c06_orbitals.txt`: with R₃₁ replaced by R₂₁ (a normalised, wrong state 2 in 2s + 3p_z),
`dipole` still passes (value −1.534 Å = ref). `energy_1`, `r_1`, `nodes_1`, `continuity` and `slice_1` fail, so the
world is protected, but `dipole` adds nothing.

Fix: for hydrogen pairs, use the closed-form radial integrals (Gordon's formula), as already done for 1s–2p₀.
Otherwise label it as a consistency check of the superposition's time dependence.

**`period` (`:379-389`).** The cloud at T equals the cloud at 0 by construction of e^{−iE_k t}; the check cannot fail.
It is not wrong, but it should be described as an identity.

**`arr_abr_identity` (`v12 viz.py:412-419`).** Both sides come from the image formula: ∫Π_ABR dt over the window
against ∫|ψ̃|²(1 − R_k)dk. This tests the time and k quadrature, not the absorbing boundary rule. The rule itself is
verified independently in `lfphys/tests/test_arrival_times.py` against Crank–Nicolson with the Robin condition.
Suggestion: say so in the check's note.

## B4-10 (nit): orbitals3d reveals the future maximum density at t = 0

**Location.** `server/lfviz/orbitals3d.py:78` (`peak` = the largest density over all 24 phases, computed ahead),
`:128` and `:264` (sent at t = 0 with the first cloud and in every slice as the scale). RULES.md documents the field.

**Evidence and claim.** For a superposition the brightness at t = 0 is drawn against a maximum the cloud reaches only
later, which tells the viewer that a brighter configuration is coming. This is the same kind of issue as B2's "box
framed on the future path".

**Fix.** Use a scale that is time-independent and needs no future, for example the bound max (Σ_k|c_k||ψ_k|)² over
the grid, from the stationary parts. Or use a running maximum of the revealed phases.

## B4-11 (nit): the speed bar's edge cases

The `speed_actual` measurement itself is sound. On v04 at the default speed it is 100.0 % of the chosen speed, about
99–101 % at 10× and 100×, 87.9 % with lag at 1000× and 8.0 % with lag at 10⁴× (`out/c04_speed_rate.txt`). It is
null for the first 0.75 s after play or a speed change, and «факт» is cleared on pause (`out/c05_browser.txt`). The
ticks sit under the thumb: the measured thumb centre is 7.5/371.5 px against the 8/372 px assumed; the «1 с» tick is
at 138.0 px and the thumb at 1 s/s at 137.5 px. Narrow ranges (v11, v12, v13) get decade ticks.

Two small edges:
* **`lag` stays false.** In `sim.py:186-191`, `lag` is set only when the advance stops short inside one frame. A world
  whose single step is longer than the frame interval (dt capped at 0.25 s, `:340`) runs at half speed with `lag`
  false. `out/c04_speed_rate.txt`, synthetic world: speed_actual 0.50, lag in 0/3 frames. RULES describes `lag` as
  "the computation could not keep up". Fix: set `lag` from `speed_actual < 0.97·speed` as well.
* **Stale «факт» on an archived world.** `player.js` updates «факт» only for frames of the latest shown world, so after
  switching to a world from the record the last live «факт» stays on screen. Fix: clear it in `showWorld` when the
  world is archived.

## B4-12 (nit): text and number inconsistencies

* `engine/STATUS.md:42` (V31): "at 1000 × it reaches 0.9 % of it (~10 world-s per s on the CPU)". The two numbers
  contradict each other (0.9 % of 11.6 s/s is 0.1 s/s). Measured: 1000× → 81–88 %, 10⁴× → 8–9 %, with about 9–10
  world-s per s at the ceiling (`out/c04_speed_rate*.txt`). [error in earlier]
* `v12_arrival_times_2d/README.md:81`: `arr_state` tolerance "10⁻⁶ of the peak". The code (`viz.py:332`) and its note
  use 10⁻³.
* `detection.py:8` and v12 README:48 cite "Tumulka, eqs. 3-4" for the click density (ħκ/m)|ψ|². Eq. 3 is the
  boundary condition and eq. 4 gives the density as n·j. The form (ħκ/m)|ψ|² is eq. 7.
* Each placement of a slice plane in a superposition world adds 1.60 MB to the record, because all 24 phases are
  re-sent (`out/c06_orbitals.txt` (d): +8.0 MB for five placements after 2.4 MB for the first period). The v13 and v14
  READMEs give 1.47 MB per plane. The claim "the record stops growing after one period" holds for time, not for
  exploring planes. Suggestion: send the other phases of a re-placed plane on demand, or coarser.

---

## What was checked and found sound

**Formulas against the sources.** [useful]
* **ABK.** `arrival_times.kijowski` is Das & Nöth eq. 5 with ħ and m restored. The prefactor ħ/(2πm) and the phase
  e^{ikL − iħk²t/2m} were rederived: ∫Π dt = ∫|ψ̃|²dk. The negative-time weight is read as non-detection per eq. 7.
* **Semiclassical.** Das & Struyve eq. 3.
* **Exponential rules.** Eq. 5 (Π = λe^{−∫λ}), eqs. 6–7 (P(∞)), and Włodarz's intensity as in Table I.
* **Absorbing boundary rule.** Tumulka eq. 3 (∂ₙψ = iκψ) and eq. 12 (R_k). The image solution
  ψ(L, t) = (2π)^{-1/2}∫ψ̃·2k/(k + κ)·e^{ikL − iħk²t/2m} dk was rederived from ψ = e^{ikx} + c_k e^{ik(2L−x)}. The
  click total is ∫|ψ̃|²(1 − R_k).
* **The absorbing step.** R = |(k − q)/(k + q)|², q = √(k² + 2imW₀/ħ²).
* **Bohm.** First arrival in 1-D: P(T ≤ t) = F(0) − min F. The reduction for separable states, where each rule for a
  plane is the 1-D rule of φ(z), holds; the transverse kinetic phase drops out of the ABK modulus.
* **The train.** Its phases follow Das & Struyve eq. 18: v12's packet j is the translate of packet 0.
* **Backflow.** The timing is exact, both centres reaching the plane at 4D/v₀.
* **`FreeGaussians`.** The closed-form evolution, the overlap normalisation and the momentum amplitude were checked;
  the engine tests compare them with quadrature too.

**v12's recorded inputs against closed forms its checks do not use.** [useful] (`out/c07_v12_small_runs.txt`)
* ∫|∂ψ/∂z|²dx on the plane, the Marchewka–Schuss input that has no check of its own: within 1.9–2.0·10⁻⁵ of the peak.
* The flux: within 3–12·10⁻⁶.
* Backflow: 0.01535 in the run against exact 0.01535.
* The Bohm hits against the exact first-arrival law: KS 0.042 and 0.058, against critical values 0.11 and 0.098.

**v12 set-up.** [neutral]
* The soft detector's reference profile is identical to the run's potential: the tanh step plus the screen layer
  from SCREEN_GAP on, the same width.
* The screen layer choice samples both ends of the spectrum, where R and T are largest.
* The cost estimate includes the soft run.
* The view clips every curve, series and hit to the time shown, apart from B4-5 and B4-8.

**v13 and v14.** [useful]
* R_nl against mpmath at 50 digits, n ≤ 12, all l, over v13's whole r_max: 6.6·10⁻¹⁵ of max|R| (`out/c06_orbitals.txt`).
* Y_lm against mpmath.spherharm, l ≤ 11: 1.5·10⁻¹⁵, the same Condon–Shortley convention.
* The real orbitals equal the Cartesian p_x, p_y, d_xy, d_z², d_x²−y² with positive lobes along the positive axes.
* 2p_x + i·2p_y is −√2·Y₁₁, a stationary m = +1 state.
* ⟨r^k⟩ closed forms, the 1s–2p₀ dipole 2⁷√2/3⁵ and the reduced-mass units were checked.
* The `continuity` check is sensitive: it fails on a wrong state, with value 1.0 against 1.8·10⁻⁶ for the correct one.
* The slice checks of v13 are independent of the drawn route.
* v14's model is flagged in the header's approximations and in the engine panel.

**v11 after the changes.** [neutral]
* Its tests pass on the CPU: 20 passed, 1 skipped (`out/v11_tests_cpu.txt`).
* The order-32 flux stencil (16 samples × h ≤ 0.24 λ on the coarse grid and its companion) stays inside the 4 λ gap.
* The `flux_absorbed` tolerance gains what the face's cells hold, a fair bound for a plane through cell centres.
* `bohm_fraction`'s clipped binomial spread is sensible at p ≈ 1.
* The observer box is placed where the coupling acts.

**The engine's own tests pass** (`out/engine_tests_b4.txt`: 75 passed, 2 skipped).
