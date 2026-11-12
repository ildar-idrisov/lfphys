# Response (demonstration worlds v01, v02, v06, v07, v08, v13–v17) to review UX-params (2026-11-04)

Processed on 2026-11-05 by a subagent (Claude) that did not write the review (agent H of the processing). This file
covers the findings in the demonstration worlds v01, v02, v06, v07, v08, v13, v14, v15, v16, v17 and their causes in
the engine: **P5, P6, P7, P8 (world part), P9, P10, P11, P12, P14, P15, P16, P17 (world part), P18, P21, P26**, the
world parts of **P3** and **P4**, and, because the framework's mechanism was in place and the texts are the worlds',
the world part of **P23** for v02 and v06. The framework parts (P1–P4, P8, P17, P20, P22, P23) are in
`RESPONSE_framework.md`; the other worlds' in their agents' files. The review text is unchanged. UX-ui U13 and U19
for these worlds: `../2026-11-04_internal_UX-ui/RESPONSE_v-worlds.md`.

The owner's words that set the goal (2026-11-04, verbatim): «при выборе опреледенных комбинаций, если ошибки, … должно
быть все понятно и удобно и подготовлено для визуализации и исследований». The integrator's rule for this pass: a
choice the form offers must either work or not be offered.

**Environment.** Docker image `light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`) except one timing on GPU 0
(`gpu_run.sh`, P26); a private server `lf-uxh-srv` (port 8575, `--max-workers 2`, `--memory=12g`); Chromium of
Playwright 1.58.2 with SwiftShader at 1600×1000. Other agents changed the framework, the player and other worlds at the
same time; the framework's `Refusal`, `check_params`, option-level `show_if` and `expected` were used once they were in
place (the world code detects option-level `show_if` and falls back to pairs without it).

**Evidence.** `response_checks_v-worlds/`: the check scripts (`*.py`) and their outputs (`*.out`); `pw_final/forms.mjs`
(the owner's path in the catalogue: «Параметры…», a field changed, «▶ Запустить», then commands), `pw_final/stats.mjs`,
`pw_final/cases.json`, `pw_final/out.json` and `pw_final/shots/*.png` (looked at), re-run at 07:52–08:05 on the code as
it was after the framework and the 3-D agents had finished (server restarted); `pw_final/kf_out.txt` (key frames);
`pw/` keeps the first runs' cases and outputs (02:15–02:40).

## Default-refused choices, now

| world | choice from the defaults | before | now |
|---|---|---|---|
| v01 | «Кинематика» = эфир / баллистика, «Гравитация» = Ньютон | refused (hidden by P1) | **works**: the world takes the law that goes with it and says so (P12) |
| v13 | «Состояние» = суперпозиция | refused «второе состояние совпадает с первым» | **works**: 2p_z + 1s (the second state defaults to 1s); a default second state equal to the first is replaced (P10) |
| v16 | «Источник вихря» = голограмма-«вилка» | refused for every Λ | **works**: the world takes the smallest waist the orders separate with, 4 µm at Λ = 2.5 µm, and says so (P11) |

Two changed laws that do not go together (v01: ether + Newtonian corpuscles with a body) and a second state chosen
equal to the first by hand (v13/v14) stay refused, in Russian, saying what to change.

## Decisions

| ID | one line | decision | status tag | where | verified by |
|---|---|---|---|---|---|
| P3 (world part) | v13/v14: the continuity check divided by a zero scale (2p_z + 2s: j = 0, ∂ρ/∂t = 0) | **fixed** | [useful] | `server/lfviz/orbitals3d.py` | `test_superposition_from_the_defaults_and_a_current_free_one` (v13) |
| P4 (world parts) | engine failures shown as refusals in these worlds | **fixed** at their causes: P5, P6, P7, P8, P17, P18 below | [useful] | see those | see those |
| P5 | v06: α_s(M_Z) = 0.19 refused with «RG integration failed» | **fixed** in the core | [useful] | `lfphys/core/qcd/running.py`, `v06_qcd/viz.py` | `test_landau_pole_reached_through_a_threshold_matching`, `test_coupling_with_its_pole_at_a_threshold_builds` |
| P6 | v15: Johannsen metric refused in English; one combination crashed (complex E) | **fixed** | [error in earlier] (crash) | `theories/alternatives/johannsen_metric.py`, `v15_kerr_shadow/viz.py` | `test_circular_orbits_where_omega_squared_is_negative`, `test_admissible_intervals`, v15 `test_refusals_of_the_what_if_metric_name_the_values_it_takes`, `test_a_what_if_metric_with_a_band_without_circular_orbits_builds` |
| P7 | v01: walkers faster than this world's light: «worldline is not timelike» | **fixed** | [useful] | `v01_light_travel/viz.py` | `test_walkers_faster_than_this_worlds_light_are_refused_in_russian` |
| P8 (world part) | v02: «Темновые отсчёты» near 10¹² 1/с drew ~2·10⁹ events per frame (31 GB) | **fixed** (bounded per step; refused far above the source) | [useful] | `v02_double_slit/viz.py` | `test_dark_counts_are_bounded_per_step_and_refused_far_above_the_source` |
| P9 | v01: a flash inside another observer's rod «measured» c = 5.6·10⁸ … 7.8·10⁹ м/с | **fixed** | [error in earlier] | `v01_light_travel/engine/world.py`, `engine/apparatus.py` | `test_a_flash_between_the_ends_of_a_rod_is_not_a_speed` (4 presets; second route by positions) |
| P10 | v13/v14: «Суперпозиция» from the defaults refused; l ≥ n, \|m\| > l refused (102 combinations) | **fixed** | [useful] | `v13_hydrogen_3d/viz.py`, `v14_quarkonium_3d/viz.py` | v13 `test_quantum_numbers_the_form_cannot_bound_are_fitted_and_said`, `test_superposition_from_the_defaults_…`; v14 `test_m_beyond_L_is_fitted_…` |
| P11 | v16: «Голограмма-вилка» from the defaults refused for every Λ, advice not followable | **fixed** | [useful] | `v16_optical_vortices/viz.py`, `engine/apparatus.py` | `test_fork_from_the_defaults_takes_a_waist_its_orders_separate_with` |
| P12 | v01: one law changed from the defaults refused | **fixed** | [useful] | `v01_light_travel/viz.py` | `test_one_law_changed_from_the_defaults_works_and_two_incompatible_are_refused`; browser |
| P14 | v01 «Андромеда»: self-consistency checks failed by round-off of absolute times | **fixed** in the core (flight time) and the world (tolerance) | [error in earlier] | `lfphys/core/worldlines.py`, `v01_light_travel/engine/world.py` | `test_flight_times_far_from_the_time_origin_keep_their_precision` (negative control: the old difference fails) |
| P15 | v02: \|γ₁₂\| = 1.108 shown failed with one slit dark | **fixed** | [error in earlier] | `v02_double_slit/viz.py`, `web/view.js` | `test_coherence_is_undefined_when_a_slit_is_dark`; browser |
| P16 | v17: index-matched drop NaN / failed Debye; «⏭» stalled 20–40 s, > 2 min for 1 mm drops | **fixed**; a remainder found while processing → STATUS (a) | [useful] | `v17_mie_scattering/viz.py` | `test_index_matched_drop_is_refused_and_next_event_is_one_wavelength` |
| P17 (world part) | v02: choices always refused for the particle offered; ids in texts | **fixed** (option-level `show_if` filled; Russian refusals with labels) | [useful] | `v02_double_slit/viz.py` | `test_refusals_name_the_choice_and_what_to_take`; browser (the forms' options for a photon and an electron) |
| P18 | v02: «λ зонда» at its minimum allocated 2 GiB; GRW extremes overflowed numpy | **fixed** | [useful] | `v02_double_slit/viz.py` | `test_probe_recoil_and_grw_kicks_beyond_the_screen_are_refused_with_the_threshold` |
| P21 | v07: the reversal-speed reference lost precision at τ = min, L = max | **fixed** (the reference made exact, not the tolerance widened) | [useful] | `v07_bell_test/viz.py` | `test_reversal_speed_reference_at_extreme_settings` (negative control: the old route misses) |
| P23 (world part) | honest failures of v02 «triple_mod», «vector_narrow», v06 «strong» and the changed Cornell model | **fixed** with the framework's `expected` and preset notes | [useful] | `v02_double_slit/viz.py`, `v06_qcd/viz.py` | `test_honest_failures_are_marked_expected` (v02, v06) |
| P26 | v08: «Круглое отверстие» from the defaults refused only after the window search | **partly fixed**: the refusal says what to change with a working example; on GPU 0 it comes after 11 s (90 s on the CPU); an a-priori bound → STATUS (c) | [neutral] | `v08_wave_3d/viz.py` | `test_a_refused_window_says_what_to_change_with_a_working_example`; `v08_gpu.out`, `v08_rows_ref.out` |

Found while processing: **F1** v16's fork orders' charge checks fail for |l| ≥ 3 at short periods and for l = 6 at
every period → STATUS (b); **F2** v17's Debye and energy checks fail for nearly index-matched drops (|m − 1| up to ~10⁻⁴;
refused below 10⁻³, the cause open) → STATUS (a); **F3** v15's notice and inclination refusal carried the engine's English text (fixed in
P6); **F4** v01's lens of radius 0 without GR was a point that did nothing (fixed in P12); **F5** v14's continuity
check failing in three random superpositions of the review's list «Failed checks» (residual ~7·10⁻⁵ of the scale
against a tolerance ~10⁻⁶): the residual does not fall with the step, so it is not truncation; the radial functions are
the solver's tabulated eigenfunctions, which satisfy the Schrödinger equation only to the solver's accuracy, and the
tolerance does not include it → STATUS (d).

Not addressed (no finding of the review names them): v02's slow edits at extremes in the review's «Every distinct
outcome» (a live change to an electron at 2.99·10⁸ м/с, 31 s; random builds of 93 s; «Очистить экран» of 35 s); v02's
`per*`, `nosig*`, `grid`, `rs*` failures at extreme wavelengths and v16's at random extremes are honest failures (P23).

---

### P3 (world part) — the continuity check at a zero scale (v13, v14)

**Reproduced.** v13, «Суперпозиция» with «Второе состояние: l» = 0 (2p_z + 2s): `ZeroDivisionError` at
`orbitals3d.py:345`, the worker died (`v13_check.out`).

**Cause.** Two real states of one energy with real coefficients carry no current and ∂ρ/∂t = 0 everywhere; the check
reported its residual as a share of `scale = max(max|∂ρ/∂t|, max|j|/⟨r⟩) = 0`.

**Fix.** When the scale is zero the identity holds term by term: the check reports the residual itself, which must be
exactly 0, with a note («ток равен нулю всюду и ∂ρ/∂t = 0 …»). The framework now also turns an exception after the
header into a refusal (its P3), but this world's cause is removed.

**Verified.** 2p_z + 2s builds, the continuity check passes with residual 0; negative control: the same pair at phase
90° carries a current and is checked by the share of the scale as before (v13 test above).

### P5 — α_s(M_Z) = 0.19 (v06)

**Reproduced** (`p5_probe*.py`): at 4 loops α_s runs to 2.9 just above m_b; the 3-loop decoupling there multiplies it
by 1 + c₂a² + c₃a³ ≈ 1.68, to 4.89 > ALPHA_MAX = 3, so the next segment started past the pole event (which fires only
on a crossing), and DOP853 failed on the overflow: `ValueError("RG integration failed")`.

**Fix (core, `running.py`).** A start at or past the bound is the pole at the start; a coupling past the bound after a
threshold's matching is the pole at that threshold; a failed integration whose last state is past the bound is the
pole there; only a genuine failure stays a `ValueError` (with the scale and the integrator's message). v06 translates
a non-pole failure into Russian.

**Verified.** `test_qcd.py::test_landau_pole_reached_through_a_threshold_matching`: the pole at m_b for μ = 1, 1.5,
m_c and at the threshold itself; `_evolve` from a start past the bound; negative controls: the world average stays
finite, α_s(M_Z) = 0.25 is met by the event inside n_f = 5; the review's scan (0.11–0.30, ±PDG error, 1–4 loops) gives
only poles. v06: the world builds, its curve is NaN below m_b and finite above (`test_coupling_with_its_pole_…`); the
browser shows the notice «Ниже μ ≈ 4.02 ГэВ α_s расходится» (`pw_final/shots/v06_alpha019.png`).

### P6 — the Johannsen metric (v15) [error in earlier: a crash]

**Reproduced** (`p6_probe.py`, `p6_world.py`): the six English refusals of the review; and #92 (the preset «whatif»
with α₁₂ = −3, α₁₃ = −1.399, α₂₂ = 3.612, a = 0): between 2.1 M and 4.6 M Ω² < 0 (no circular geodesics: the
effective gravity repels), a real r gave a complex Ω, the ISCO search took a complex E, `float()` crashed.

**Fix (engine, `johannsen_metric.py`).** `_circular` returns NaN where Ω² < 0; the complex-step derivative reads NaN
there; the ISCO is defined as the inner edge of the stable circular orbits connected to infinity — where dE/dr = 0
(`isco_kind` "stability", Kerr and small deviations, unchanged) or the outer edge of a band without circular geodesics
(Ω² = 0, a static orbit; "existence"). New: `shadow_computable(chi, dev)` (regular and one photon band) and
`admissible_intervals(chi, param, others, lo, hi)` (the values of one deviation, the others fixed, for which it holds).

**Fix (v15).** The refusal is Russian (`Refusal`): what fails (A₁ ≤ 0, det g = 0, closed timelike curves, or the photon
orbits not one band) and, for each deviation with the others as they are, the values the world takes («α₁₃ — от −2.11
до 10; α₂₂ — никакое значение … не помогает; α₁₂ — от 5.5 до 10»). The help next to the sliders states the intervals at
a = 0.9 (tested against the engine). An inclination at which no spherical photon orbit is visible, and a metric without
circular orbits, are said in Russian.

**Verified.** The 40-digit root of g_tt′ = 0 (a = 0: Ω = 0, E = √(−g_tt)) equals the existence-edge ISCO to 1e-13
(E too); Kerr and the earlier deviations keep "stability" and their values (the existing 30-digit test). Each named
interval's ends are edges of `shadow_computable` (inside builds, 1e-3 outside does not); the world: a value in the
middle of a named interval builds, one just beyond its end is refused; no English word in the texts. Browser:
`pw_final/shots/v15_jp_refused.png`.

### P7 — walkers faster than light (v01)

**Fix.** In a relativistic world the Andromeda scenario refuses walkers at or above c × factor before the core is
called: «пешеходы не быстрее света этого мира: … Уменьшите скорость пешеходов ниже 1.499e+08 м/с или увеличьте
множитель … выше 0.6671». A Galilean world (ether) takes them (no speed limit there). **Verified** by the test above
(the named factor 0.6672 builds) and in the browser (`pw_final/shots/v01_walkers_refused.png`).

### P8 (world part) — dark counts (v02)

**Cause.** Every dark count of a step was an event of the record (time, place, flags), and the world's step was set by
the source alone (4000/rate): at 10¹² 1/с a frame drew ~2·10⁹ of them.

**Fix.** (1) The step holds at most ~4000 events, signal and dark (`max_step = 4000/(rate + dark_rate)`); (2) more than
100 dark counts per emitted particle is refused — at the start (`check_params`, shown on the catalogue's form), as a
live change (rolled back) and in a new world — with the numbers to change («уменьшите «Темновые отсчёты» до 1e+05 1/с
или увеличьте «Частиц в секунду» до 1e+10»). At 100 per particle the dark counts per bin already exceed the pattern's
peak tenfold; the help of the parameter says so. The worker's memory limit is the framework's.

**Verified.** The test above: the refusal on all three paths; at the limit the detections per step stay below 1.2 ×
4000 (Poisson); negative control: the old step would have held 100 times more. `v02_check.out`: peak RSS 108 MB at
1e12/1e10 (dark/rate). Browser: `pw_final/shots/v02_dark_refused.png`.

### P9 — a flash inside a rod (v01) [error in earlier]

**Reproduced** (the review's `r_v01_flash.py` sequence, `v01_check.py`): the measured c = 5.6·10⁸ and 1.94·10⁹ м/с
(measure_c), 7.8·10⁹ м/с (measure_c_lab), failed checks.

**Cause.** The one-way speed took the first arrivals at A and B; for a flash between the ends they are two different
rays running in opposite directions, and L₀/(τ_B − τ_A) is not a speed. The direction test only asked that light run
along the rod.

**Fix.** When the arrival directions at A and B are opposite (dot product < 0), the observer is told, at the time it
could know both readings, «вспышка … случилась между концами стержня — свет прошёл A и B в разные стороны, скорость по
двум концам не измеряется», and no speed or check is reported. A flash exactly at an end (direction 0 there) is still
a one-way passage. (`Apparatus.known_time` factored out of `passing`.)

**Verified.** `test_a_flash_between_the_ends_of_a_rod_is_not_a_speed` for measure_c, measure_c_lab, measure_c_ether,
measure_c_emission: every flagged (observer, pulse) is exactly one whose emission point lies strictly between the
rod's ends at the emission time (a second route: positions of the worldlines), no flagged pulse has a speed, every
speed shown equals the closed form `checks.one_way_speed` to 1e-9. Browser: «measure_c», a flash by observer 1 at
0.4 ms — «Наблюдатель 3: вспышка «Наблюдатель 1» случилась между концами стержня …» at 2.58 ms, observer 2 measures
299 792 458 м/с (`pw_final/out.json`, `pw_final/shots/v01_measure_c_flash_inside.png`).

### P10 — quantum numbers and the superposition (v13, v14)

**Fix.** The form cannot bound l by n and m by l, so the world takes the nearest allowed numbers — n first, then
0 ≤ l < n, then |m| ≤ l (v14: |m| ≤ L) — and says what it changed and how to get what was asked («l = 2 при n = 2
невозможно … — взято l = 1; для l = 2 выберите n ≥ 3»); the header carries the state shown, so a resumed run rebuilds
the same world (idempotent, tested). v13's second state defaults to 1s, so «Суперпозиция» alone is 2p_z + 1s (it
oscillates at the 2p–1s frequency). A second state left at its defaults but equal to the first (e.g. the catalogue's
first scenario 1s + «Суперпозиция») is replaced (1s → 2p_z in v13, → 1S in v14) with a notice; one chosen equal by hand,
and two non-orthogonal states, are refused in Russian with what to change.

**Verified.** The tests above; `v13_check.out` (every review case); browser: 1s + «Суперпозиция» from the catalogue
builds 1s + 2p_z with the notice (`pw_final/shots/v13_super_from_defaults.png`; all its checks pass).

### P11 — the fork hologram (v16)

**Cause.** The orders separate when tan θ₁ > 4.5 w0/z_R = 9/(k w0); the default waist (1.5 µm, the LG modes') is too
narrow for every Λ of the form; the advice «уменьшите Λ» could not reach it, «увеличьте w0» did not say to what.

**Fix.** With «Голограмма-вилка» the world takes the smallest waist ≥ the one given, in 0.1 µm steps, with a 20 % margin
over that bound and a region that fits the 512-point grid (the conditions of `apparatus.Fork`, checked before the mask
is built), and says why and what it costs («Мир взял w0 = 4 мкм …: пучок шире, область длиннее (до z = 90.2 мкм).
Меньший период Λ позволяет более узкий пучок.»). Λ ≤ λ, or a period no waist up to 6 µm can take, is refused naming the
largest period that works (found by the same test over Λ; e.g. 3.63 µm at λ = 1 µm, 1.97 µm at λ = 0.4 µm).

**Verified.** The test above (the chosen waist equals ⌈1.2·9/(k tan θ₁)⌉ at Λ = 2.5: the preset's 4 µm; its checks
pass; a wide enough waist is kept with no notice; the named period builds); `v16_check.out`, `v16_scan.out`; browser:
`pw_final/shots/v16_fork_from_defaults.png`, `v16_fork_period8_refused.png`.

### P12 — one law changed from the defaults (v01)

**Fix.** When one law is changed and the other left at its standard value, the world takes the law that goes with it
(`Laws.validate`: GR only with SR, Newtonian corpuscles only with emission): ether + GR → ether without gravity (the body
only absorbs light; the Earth's orbit stays prescribed); emission + GR → emission + Newtonian corpuscles (half the
deflection, no Shapiro delay); Newtonian corpuscles + SR → emission. In a scene without a gravitating body the gravity
law is set to «Без гравитации» (nothing changes). Ether + Newtonian corpuscles with a body is refused, saying which
choice to make. A lens of radius 0 (GR's black hole) without GR is given the horizon's radius of its mass (the preset
«lensing_newton»'s choice; within the form's range). Everything changed is said in a notice and in the scenario's text;
the header carries the laws in force, so «модифицированная физика» lists them and a resumed run rebuilds the same world.

**Verified.** The test above (every scenario × kinematics × gravity in `v01_check.out`: 34 of 36 build and pass their
checks, the 2 refused are ether + Newton with a body); browser: `pw_final/shots/v01_ether_from_defaults.png`,
`v01_newton_from_defaults.png`, `v01_ether_newton_refused.png`.

### P14 — flight times far from t = 0 (v01) [error in earlier]

**Cause.** The flight time was a difference of absolute times; at t ≈ 4·10¹¹ s the spacing of doubles is 6·10⁻⁵ s, 3·10⁻⁸
of an 1868 s flight, above the check's 10⁻⁹.

**Fix.** `worldlines.sphere_meeting` returns `dt`, the flight time summed from the solved interval (on an inertial
piece: the piece's offset from the emission plus the root), used by v01 for the time shown and checked. The residual
check's tolerance adds what the absolute time's rounding moves a fast receiver: 4ε(|v||t| + |x|)/(cΔt).

**Verified.** The test above: every flat residual ≤ 10⁻¹⁴ in «andromeda»; negative control: the old difference exceeds
the tolerance (it is what failed). `v01_check.out`: «andromeda_fast» too.

### P15 — |γ₁₂| with a dark slit (v02) [error in earlier]

**Cause.** With crossed polarisers (source H) slit 2 passes cos² 90° = 3.7·10⁻³³ of slit 1: |γ₁₂| = |G₁₂|/√(G₁₁G₂₂)
is 0/0, and the constrained fit returned rounding noise (1.108; with the eraser presets 0.958, 0.589, 1.102).

**Fix.** |γ₁₂| is not fitted where it is undefined — a slit passing less than 10⁻¹⁰ of the other's, or a screen grid
that does not resolve the fringes (< 8 points on the finest one, the existing «Разрешение экрана» check; the review's
coh3 with a 10⁹ u particle) — and the check says why (information); the frame's histogram fit says it too.

**Verified.** The test above (the review's case, the frame); negative controls: two open slits give 1, the same
polarisers with D light give 0, both checked; `v02_check.out` (the review's sequences 379, 436, 437, 372: no failed
coherence check left); browser: «— ≈» with the reason in the checks panel (`pw_final/shots/v02_crossed_polarisers.png`),
and after 162 hits the statistics panel says «Степень когерентности щелей |γ₁₂| не определена: щель 2 тёмная …»
(`pw_final/shots/v02_crossed_polarisers_stats.png`).

### P16 — the index-matched drop and the sky's cost (v17)

**Reproduced** (`v17_m1.py`, `v17_m1b.py`, `v17_cost.py`): m = 1: Mueller NaN, Debye 1163 against 0; nearly matched
drops fail the series' checks too — the Debye route up to |m − 1| ~ 3·10⁻⁵, the energy identity of a 150 µm drop up to
~10⁻⁴ (0.058 against 1.1·10⁻¹¹ at 10⁻⁴), all pass from 3·10⁻⁴; one wavelength of the sky costs ~1.4 ns × nodes × terms × angles (3 s for the rainbow preset
at 380 nm, 19 s for 1 mm drops); «⏭» computed all 24 wavelengths at once.

**Fix.** (1) |m − 1| < 10⁻³ at the display wavelength is refused (also by `check_params` and as a live change of the
wavelength): the drop scatters almost nothing and the checks do not hold there; the refusal says what to change. (2) «⏭» goes to the next wavelength. (3) The size nodes of one wavelength are
capped so that its step takes about 10 s at most on the CPU (the presets are unchanged; 1 mm drops become coarse, which
the sky's check and the README state).

**Verified.** The test above (refusals at m = 1 and 1.0001; m = 1.0015 builds and passes; one wavelength per «⏭»;
1 mm drops capped and coarse, one «⏭» bounded); browser: `pw_final/shots/v17_matched_refused2.png`. **Remainder (F2, found
while processing):** why the checks fail for nearly matched drops (the Debye route's tolerance, the energy identity's
quadrature or the coefficients' cancellation) is not found; a tolerance derived for m → 1 would let such drops in →
STATUS (a).

### P17 (world part) — choices per particle (v02)

**Fix.** The options carry their own `show_if` (the framework's, 2026-11-05): polariser, λ/2, λ/4 for photons; spin
rotation and filter for spin ½; «скорость» for massive particles, «частоту» for photons; the microscope for electron,
⁴He, C₆₀ and a custom particle. A choice made anyway (a request through the API, a value kept from another particle) is
refused naming the element by its label, the particle, and what does act on it (««поворот спина вокруг y» у щели 1 не
действует на фотон … выберите … одно из: «поляризатор», …»); the analyzer, the microscope, the detector's slit number
(«детектор пути у щели №5, а щелей 2 … от 1 до 2») and the energy's input likewise; a removed element names itself. The
world detects whether the framework takes option triples and falls back to pairs.

**Verified.** The test above (each named alternative builds; the schema's options per species); browser: the forms
offer exactly the options of the particle (`pw_final/out.json`: photon — no spin elements, no «скорость», no microscope;
electron — no polarisation elements, no «частоту»), `pw_final/shots/v02_options_*_form.png`.

### P18 — the probe's recoil and GRW's kicks (v02)

**Cause.** The screen's expectation is computed on the screen grid extended by the largest shift a particle gets on
its way (`paraxial_ensemble.Model.max_shift`): a probe photon of 0.001 nm kicks 50 keV electrons by ±10.7 m against a
screen of ±161 µm (1.4·10⁸ points); GRW at λ = 10¹², r_C = 10⁻³ nm by ±3.9·10¹¹ km.

**Fix.** Before anything is allocated (at the start, and before a live change is committed) the world estimates the
bytes of that computation; above 1 GB it refuses with the shift, the grid, the size and what to change — for the
microscope the probe wavelength that fits («возьмите длину волны фотона-зонда не меньше ~0.0402 нм»); below it the
framework's budget (`limits.require`) applies.

**Verified.** The test above (the named wavelength builds; a refused live change leaves the world as it was).

### P21 — the reversal speed's reference (v07)

**Cause.** The reference boosted the two events apart and subtracted their transformed times, terms of the size of
c t ~ L: the root lost ~ε L/(c τ), 1.2·10⁻⁸ at τ = 1 ps, L = 10⁵ m.

**Fix.** The Lorentz matrix acts on the separation (the transformation is linear): the same matrices, no cancellation.
The tolerance stays 10⁻⁹.

**Verified.** The test above: the world's check passes; the new route equals c Δt/(2L) to 10⁻¹²; negative control: the
old route misses by more than 10⁻⁹.

### P23 (world part) — failures that are the point (v02, v06)

The framework's `expected` is set where a failure is what the world shows: v02's Sorkin parameter under a changed Born
rule; v02's paraxial-vs-exact comparison in the vector mode (the world's answer there is the vector solution); v06's
convergence check at a changed α_s(M_Z); v06's levels when the Cornell parameters differ from the fit. The presets
«triple_mod», «vector_narrow» and «strong» carry a note. Under accepted physics none is set (negative controls in
`test_honest_failures_are_marked_expected`, v02 and v06). v16's failures at random extremes (the review's last line of
P23) are not by design and stay failures.

### P26 — the circle from the defaults (v08): partly

**Measured.** The refusal comes after the whole window search: 88–93 s on the CPU (`v08_rows_ref.out`), **11.3 s on
GPU 0** (`v08_gpu.out`), which runs v08's kernels on the owner's server («авто»); the accepted circle preset takes
2.6 s there.

**Tried and rejected.** An early refusal extrapolating the measured errors to the largest window: the fall per doubling
of the window varies from 0.95 to 0.095 (the plain sum at z_max = 80 µm fell 10-fold in one doubling; the square's
plain sum 0.10–0.12), so no extrapolation is safe, and one that would refuse the circle early would also refuse worlds
the full search accepts. Not adopted.

On the owner's path the framework now shows that the world is being built and then the refusal on the form (its P1).

**Done.** The refusal now says what to change and names a scenario that works for that source («работающий пример —
сценарий «Круглое отверстие» (a = 3 мкм, z_max = 40 мкм)»). An a-priori bound for the circle (the field of the nearest
copies by the radial integral of the disc's exact spectrum) → STATUS (c).

## Changes for the integrator

**STATUS.md** — a new item (the next free number; written here as V45):

```
| V45 | Review UX-params (2026-11-04), the demonstration worlds (processed 2026-11-05, `reviews/…/RESPONSE_v-worlds.md`): (a) v17: the series' checks fail for nearly index-matched drops — the Debye route up to |m − 1| ~ 3·10⁻⁵, the energy identity of large drops up to ~10⁻⁴ (r = 150 µm: 0.058 against 1.1·10⁻¹¹ at 10⁻⁴); such drops (|m − 1| < 10⁻³) are refused, the cause is not found; (b) v16: the fork's orders' charge checks fail for |l| ≥ 3 at short periods and for l = 6 at every period (the measuring disc of 1.3 w(z) misses vortices of the split high-charge core; independent of the waist; `response_checks_v-worlds/v16_scan.out`); (c) v08: a refused aperture is known only after the whole window search (11 s on GPU 0, ~90 s on the CPU); no a-priori bound; (d) v14: the continuity check's tolerance does not include the radial solver's error (three random superpositions of the review fail at ~7·10⁻⁵ of the scale against ~10⁻⁶; the residual does not fall with the step) | (a) the cause found (the coefficients' cancellation as m → 1, the Debye tolerance, or `mie.angular_integrals`), tolerances derived for m → 1, then the refusal lowered; (b) a disc scaled with the order's charge, and the separation criterion with it, tested against the closed form of the thin mask's orders; (c) a lower bound of the window error from the nearest copies' exact field (the circle: the radial integral of the disc's spectrum; rectangles: `aperture_fields.rectangles_field`), refusing at once only below it; (d) the solver's error of the tabulated R_nl (its residual in the radial equation) added to the tolerance, with a negative control | open |
```

**lfphys/README.md** (the module catalogue; exact lines to add to the entries of the modules):

- `core.qcd.running`: «A coupling past ALPHA_MAX at the start of a segment or after a threshold's matching is reported
  as the Landau pole there (`LandauPole`), not as an integration failure (review UX-params P5).»
- `core.worldlines`: «`sphere_meeting` also returns `dt`, the flight time summed from the solved interval (exact to
  round-off of dt itself; review UX-params P14).»
- `theories.alternatives.johannsen_metric`: «`shadow_computable`, `admissible_intervals` (the values of one deviation
  the shadow edge can be computed for, the others fixed); `circular_orbits` reads NaN where Ω² < 0 and gives the ISCO's
  kind ("stability" or "existence"; review UX-params P6).»

No change to `RULES.md` or the owner guide is needed from this part; the worlds' own READMEs are updated (v01, v02,
v06, v07, v08, v13, v14, v15, v16, v17).

## Tests run (CPU, Docker, 2026-11-05, final run 07:52–08:30 on the code after the other agents had finished)

| what | result |
|---|---|
| engine: `test_qcd.py`, `test_johannsen_metric.py`, `test_relativity_gravity.py`, `test_relativity_signs.py`, `test_causality.py`, `test_kerr_shadow.py`, `test_boundary.py`, `test_layers.py`, `test_licences.py` | 382 passed, 1 skipped |
| worlds v01, v02, v06, v07, v13, v14, v15, v16, v17 | 323 passed |
| world v08 | 24 passed, 1 skipped (the GPU test, CPU-only container) |
| shared: `tests/test_restore.py`, `tests/test_checkpoint.py` for these worlds | 30 passed |
| `tests/browser/keyframes.mjs` for these ten worlds (private server, restarted on the final code) | «all equal» (`pw_final/kf_out.txt`) |
| the owner's path in the catalogue, 16 cases (`pw_final/forms.mjs`) | as described above; no page errors (`pw_final/out.json`) |
