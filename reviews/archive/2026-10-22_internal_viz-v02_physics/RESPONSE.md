# Response to the physics review of v02 (2026-10-22)

Processed by the main session (Claude Opus), which built v02 but did not write this review (the review is by a
separate subagent). Every finding was checked against the code first; all 28 were confirmed. The engine was then
reworked rather than patched. The main changes:

* an exact ensemble (`engine/ensemble.py`) in place of the Monte-Carlo expectations;
* a three-stage fate of every particle: emission → slits (apparatus at that time) → screen (apparatus at that time);
* a constrained Poisson maximum-likelihood coherence estimator;
* server-side curves per readout and per class.

**Verification:**

* the project's tests: `visualizations/v02_double_slit/tests/test_v02_physics.py`, now 66 tests, 21 of them
  regressions for this review or for this response; the full visualization suite passes in the Docker image;
* the reviewer's scripts re-run on the reworked code, where they still run, into `response_checks/`;
* the reviewer's key probes re-done against the current API: `response_checks/rc_v02.py` → `rc_v02.txt` (written by
  the processing session).

**Reviewer scripts on the reworked code:**

| script | status |
|---|---|
| `01_fresnel_rs.py` | runs. Fresnel and Parseval unchanged. The RS kernel ratio is now +1.0000 at x = 0 and 1 mm. The line "rs.py uses −(ikz/2)…" is a fixed text in the script. |
| `04_particles_ab_probe.py` | §1–2 run: λ to ≤ 1.7·10⁻¹⁶ against 50 digits, and the run's λ check passes. §3 stops because `ab_phases` now takes the apparatus (the phase belongs to the apparatus at slit time). The same probe is re-done in `rc_v02.txt` (R6). |
| `02_marks.py`, `03_grw.py`, `06_viz_consistency.py` | stop at removed internals (`_state_label`, `_grw_weights`, `ensemble_marks`). Their probes are covered by the regression tests and by `rc_v02.txt`, as listed per finding below. |
| `05_statistics.py`, `05c_seed_check.py`, `05d_expected_fit_stability.py`, `07_numerics.py` | re-run, see `response_checks/` (outputs end with the exit code). |
| `05b_statistics_fit.py` | not re-run: it calls the removed `coherence_fit`. Its probes are in `rc_v02.txt` (R2, R8). |
| `07b_map_vs_rs.py` | not re-run: it calls the removed `fresnel.near_field_map`. The map is now checked against RS in the run itself (R13). |

## Findings

| ID | summary | decision | where | verification |
|---|---|---|---|---|
| R1 | GRW hits counted over the flight but applied at the slit plane | **fixed** as proposed. Each hit is a kick q ~ N(0, 1/(2r_C²)) at z′ ~ U(0, L₂), entering as the slit-plane kick q(1 − z′/L₂); the kicks are summed per particle and go through the `kappa` path. The ensemble uses the exact characteristic function exp(−Λ[1 − √π erf(a)/(2a)]). The check's reference is the reviewer's closed form. STATUS V5 is narrowed to hits before the slits. | `engine/experiment.py` (`at_slits`), `engine/ensemble.py` (`Model._grw`, `cf`), `viz.py` (`_segment_checks`) | `test_R1_grw_coherence_exact_kick_model`. c60_grw: run 0.35138 vs closed form 0.35155. The preset's λ was changed to 3.0 so that the effect is visible with the exact model. |
| R2 | ill-conditioned 4-parameter coherence fit | **fixed** as proposed. Three parameters μ = c₀(G₁₁b₁₁ + G₂₂b₂₂) + c₃Re b₁₂ + c₄Im b₁₂, with the slit weights from the run's own marks. Poisson ML on histograms, least squares on smooth curves, the dark-count term as a known background, error from the Fisher matrix; the error shown in the player is a parametric bootstrap (see "Further changes"). The same estimator serves the expected curve. | `engine/stats.py` (`coherence_ml`), `viz.py` (`_coherence`) | `test_R2_coherence_estimator_unbiased_on_samples`. `rc_v02.txt` R2 (200 multinomial samples each): electron_weak (0.866): N = 100 → 0.881 ± 0.097 (median reported error 0.088), N = 1000 → 0.863 ± 0.028, no failures. photon_young (1.0): mean 1.0004 at N = 20 000; values above 1 are not clipped (the estimator is unbiased around 1, and each value is shown with its error). Not done: a bias-corrected magnitude at γ = 0. The remaining bias there is the Rice bias of a magnitude (0.19 at N = 100, 0.057 at N = 1000, 0.012 at N = 20 000), always below the reported error (0.14, 0.046, 0.010). |
| R3 | near-field map and flow lines ignore decoherence | **fixed**. The map is the exact ensemble \|Ψ\|² per column: per-slit fields convolved with the characteristic functions of the shifts (source, microscope, GRW), Gauss–Hermite nodes over the spectrum. With decoherence, the flow lines are lines of the averaged current. They are not drawn for GRW (STATUS V6). | `engine/ensemble.py` (`near_field`, `flow_lines`), `viz.py` | `test_R3_map_shows_the_decoherence`. `rc_v02.txt` R3: the map's last column and the run's screen curve agree under the same centre-contrast metric (0.195/0.186, 0.487/0.478, 0.465/0.450). That metric differs from \|γ\| (0.152, 0.351, 0.461) because of the envelope within ±1 fringe. |
| R4 | analyzer inserted while particles fly does not act on them | **fixed** as proposed. The fate is split. At the slit plane: elements, detector qubit, microscope and Aharonov–Bohm phase, with the apparatus present then. At the screen: analyzer and readout basis, with the apparatus present at t_det. Particles that passed the slits under an earlier segment are flagged "transitional" and are kept out of the segment's histogram. | `engine/experiment.py` (`at_slits`, `at_screen`, `gram`), `viz.py` (`advance`) | `test_R4_analyzer_inserted_in_flight_acts_on_flying_particles`. `rc_v02.txt` R4: before 19 108/s; in the first flight after insertion 9851/s; afterwards 9435/s (the filter passes ½). |
| R5 | λ from E_k loses up to 3·10⁻⁴ | **fixed** as proposed: p = √(E_k² + 2E_k mc²)/c. | `engine/particles.py` | `test_R5_slow_neutron_by_kinetic_energy`, `test_slow_neutron_kinetic_energy_has_no_cancellation`. `response_checks/04_particles_ab_probe.txt` §1–2: ≤ 1.7·10⁻¹⁶ against 50 digits; the neutron's λ check passes. |
| R6 | Aharonov–Bohm phase ignores \|q\| | **fixed**: 2π·(q/e)·Φ/(h/e). | `engine/experiment.py` (`ab_phases`) | `test_R6_ab_phase_scales_with_charge`. `rc_v02.txt` R6: all five charges equal qΦ/ħ to 4·10⁻¹⁶. |
| R7 | no-signalling check blind to the modified Born rule | **fixed**: the check compares the sampled marginals born(I_r) with and without reading. Under the Born rule it is grouped as an identity. Under the modification a violation is reported as a computed consequence (failed check with a note). | `viz.py` (`_segment_checks`) | `test_R7_signalling_under_modified_born_rule_is_reported`. `rc_v02.txt` R7: electron_eraser at p = 2.4 gives 0.0741, ok = False, matching the reviewer's 7.4 %. |
| R8 | dark counts in the histogram but not in the expectation | **fixed**: the dark density per emitted particle is added to every server curve (also per readout), χ² uses it, and the coherence fit has the known dark background. | `viz.py` (`_new_segment`, `frame`), `engine/stats.py` | `test_R8_dark_counts_in_the_expectation`. `rc_v02.txt` R8 (seed 4): 50/s, 30 s gives χ² 353/287 (p = 0.005). Investigated: over 8 seeds the p-values are 0.001–0.82. At 10× the counts (3·10⁵ detections, 300 s) χ² is 300/287 (p = 0.29) at 50/s and 322/287 (p = 0.07) at 500/s. So no mismatch grows with the counts, and the low p-values are fluctuations. Multinomial draws from the expectation give false-alarm rates of 4.5–7 % at α = 0.05 (bins with 5–6 expected counts). 500/s: \|γ\| 0.9947 ± 0.0057 (the reviewer's fit failed). |
| R9 | browser rebinning sawtooth | **fixed**: the server sends its trapezoid-binned curves (`c_<name>` blobs). The view only scales them to the shown count. | `viz.py`, `web/view.js` | `test_R10_R9_server_curves_per_class` |
| R10 | "без рассеянного фотона" filter draws the whole ensemble | **fixed**: the server computes the class curve `noscat` (the ensemble without a scattering, weighted by 1 − p). | `viz.py`, `web/view.js` | `test_R10_R9_…`. `rc_v02.txt` R10: \|γ\| of the noscat curve 1.0000, of the whole ensemble 0.4242. |
| R11 | probe polarised along its own direction | **fixed**: rejected with a reason (mic_pol ≠ mic_dir). | `viz.py` (`_apparatus`) | `test_R11_R24_probe_rules` |
| R12 | Monte-Carlo expectations; tolerances that cannot fail | **fixed** as proposed. The expectation is exact: source points, microscope and GRW by convolution with their closed-form characteristic functions (the dipole marginal f(u) = (3/8)[(1 + p_x²) + (1 − 3p_x²)u²]); the spectrum by Gauss–Hermite in ln λ; the internal states through ρ. Only the Born-exponent modification keeps a Monte-Carlo expectation, and it is labelled. Tolerances against the closed-form references are 0.02, which covers the references' own approximation (the envelope shift); the expectation itself has no noise. | `engine/ensemble.py`, `viz.py` | `test_ensemble_matches_monte_carlo_with_shifts`, `test_presets_checks_agree`. `rc_v02.txt` R12: the expected \|γ\| is identical to 12 digits over seeds. References: VCZ 0.46069 vs 0.46081; Chapman 0.15217 vs 0.15198; GRW 0.35138 vs 0.35155. |
| R13 | near-field map paraxial where it fails, unmarked | **fixed**: the run finds the first map column where the paraxial field agrees with the exact RS integral to 1 % (bisection over columns). The deviation is not monotonic in z (the reviewer's `07_numerics.py`: 0.098, 0.044, 0.106 at z = 2a, 5a, 20a), so three later columns are checked after the bisection and the search continues beyond any that fails. The region before the boundary is hatched, and the approximations panel says so. In this response: the exact per-slit fields are computed once per run and reused by every segment (see "Further changes"). | `viz.py` (`_map_paraxial_start`), `web/view.js` | `test_R13_R15_reported`, `test_rs_fields_cached_across_segments` |
| R14 | RS quadrature O(n³) | **fixed**: composite 32-node Gauss–Legendre panels. In this response the panel rule was also corrected (see "Further changes"). | `engine/rs.py` | `test_paraxial_matches_rayleigh_sommerfeld`, `test_rs_exact_for_wide_slit_in_near_field` |
| R15 | grid cap undersamples without a warning | **partly fixed**: the grid cap is raised to 32 768 points. The check "points per finest fringe" fails below 8 and comes with a notice and a line in the approximations panel. The sampler is piecewise-linear (R26). Sampling inside cells from the analytic amplitude is **not** done → STATUS V11. | `viz.py` | `test_R13_R15_reported`. `rc_v02.txt` R16: the reviewer's 12-slit electron geometry gives 3.7 points per fringe and grid ok = False. |
| R16 | 10–12 slits unusable in real time | **partly fixed**. The reviewer's two geometries (their `07_numerics.py` §4, re-run): first segment 100 s → 3.8 s and 167 s → 0.5 s; 500 particles 15 s → 8.0 s and 27 s → 15.0 s. A heavier variant (12-slit electrons with the microscope, d = 10 µm, 32 768 points): first segment 8.9 s, later segments 0.9 s, 500 particles 27 s. All presets run at 1300–34 000 particles per wall-clock second at rate 1000/s. The per-particle cost remains, because each particle with its own kick, source point or λ gets exact amplitudes on the whole grid → STATUS V12. | `engine/ensemble.py`, `engine/rs.py`, `viz.py` | `response_checks/07_numerics.txt` §4; `rc_v02.txt` R16 |
| R17 | limitations not visible in the player | **fixed**: a per-segment panel "Приближения этого отрезка" lists the active approximations, generated by the run (`approx` in the segment message). It covers 2-D geometry, Kirchhoff, the hatched map, grid resolution, the microscope model, GRW, the Born-exponent conventions, averaged-current flow lines, the spectrum, and the analyzer/readout timing. Notices are emitted for narrow slits and grid resolution. The help text says "линии тока", with the pure-state Bohm case named separately. | `viz.py` (`_approximations`), `web/view.js` | code reading; screenshot after the server restart |
| R18 | RS kernel sign | **fixed**: +(ikz/2)H₁⁽¹⁾/R. | `engine/rs.py` | `response_checks/01_fresnel_rs.txt` §4: ratio +1.0000; `test_rs_exact_for_wide_slit_in_near_field` checks the phase of the incident wave |
| R19 | S₃ sign and the custom χ against the engine's own R/L | **fixed**: S₃ = +2 Im(a b*) (R → +1). The custom state is R(ψ)(cos χ, −i sin χ), so χ = +45° is R. The conventions (time dependence, fast axis, R and L) are stated in `engine/marks.py` and the README. | `engine/experiment.py` (`state_label`), `engine/marks.py`, README | `test_R19_right_circular_has_s3_plus_one` |
| R20 | identities shown as physics checks | **fixed**: grouped as "Отрезок N: согласованность (тождества)". The independent checks (RS, VCZ, Chapman, GRW, period, λ) are in the segment group. | `viz.py` | code reading; `test_presets_checks_agree` |
| R21 | one flight time under a spectral width; reflected Gaussian | **fixed**: log-normal spectrum (σ of ln λ ≤ 0.3) and per-particle group velocity in t_det and in the GRW hit count. | `engine/experiment.py` (`emit`, `v_of_lam`) | `test_R21_per_particle_flight_time` |
| R22 | GRW silent for electrons | **fixed**: rate λ·(m/u), mass-proportional; electrons get m_e/u. | `engine/experiment.py` (`grw_rate`) | `test_R22_grw_acts_on_electrons` |
| R23 | current segment's curve over a multi-segment histogram | **fixed** (the reviewer's second option): with "текущий отрезок" off, no expectation curve is drawn and the overlay says why. | `web/view.js` | code reading |
| R24 | "cone" recording meaning; dipole pattern for neutral species | **fixed**: the microscope is offered only for charged or polarisable massive species (electron, He-4, C60, custom). Photons and neutrons are rejected with a reason. "Recording the direction" is stated as a detector in the back focal plane. | `viz.py` (`MIC_SPECIES`, `_approximations`), README | `test_R11_R24_probe_rules` |
| R25 | analyzer absorption labelled as slit absorption | **fixed**: separate counters `absorbed_slits` and `absorbed_an`, and separate story texts. | `engine/experiment.py`, `viz.py`, `web/view.js` | `test_absorption_fractions` |
| R26 | sampler (grid point + jitter) vs trapezoid rebinning | **fixed**: positions are drawn from the piecewise-linear density on the grid, exactly the density the trapezoid rebinning integrates. | `engine/experiment.py` (`_sample`) | `test_histogram_agrees_with_expectation_and_coherence`; R8 investigation above (no χ² growth at 3·10⁵ detections) |
| R27 | minor code and labels | **fixed**: `visibility()` removed. The frequency is labelled "Частота де Бройля E/h (с энергией покоя)" for massive particles. The source-width help says it is not used for a plane wave. The README links resolve. | `engine/stats.py`, `web/view.js`, `viz.py` | code reading |
| R28 | Born-exponent conventions not stated | **fixed**: stated in the README ("Conventions") and in the approximations panel. | README, `viz.py` | code reading |

## Further changes made while processing (not findings of the review)

* **RS reference silently inexact for wide slits** [error in earlier]. The composite rule took about 1 rad of phase
  per 32-node panel, capped at 2000 panels. Measured: a 32-node panel integrates exp(iφ) to 10⁻¹⁵ up to about 56 rad,
  and to 3·10⁻¹¹ at 72 rad. For k·a above about 1.1·10⁵, the cap therefore left too many radians per panel near the
  slits. Example: an electron slit of 1 µm at z = 2 µm gives 260 rad per panel and a field error of 0.83. The presets
  stayed just inside the limit (about 60 rad per panel).
  * Now: at most 32 rad per panel, no cap, the phase bound taken to the far slit edge and including the incident
    tilt, and chunking over nodes as well as screen points.
  * Without the cap, very wide slits become unaffordable. A 1 u particle at 10⁵ m/s through 20 µm slits has
    k·a = 3·10⁷ and would need about 10⁶ panels per slit next to the slits. The old cap was fast there only because
    it was wrong. Now a column whose exact integral exceeds 2·10⁷ kernel evaluations (about 1 s) is not computed. It
    is reported as not verified: the hatch is labelled «не сверено с точным решением», the approximations panel
    gives k·a, and the screen check is shown as not computed. The paraxial boundaries of all presets are unchanged.
    Test: `test_rs_budget_marks_unaffordable_columns_unverified`.
  * `test_rs_exact_for_wide_slit_in_near_field`: inside the geometric projection the exact field equals the incident
    wave to 0.0016 in magnitude and phase. With the old rule the error is 0.83.
* **Segment latency.** Every apparatus change or screen clear rebuilt the exact near-field check. It took 30 s for
  c60 and 5.7 s for the electron presets; 27 s and 5 s of that went into the Hankel kernel.
  * The map's columns depend only on the geometry and the particle. The exact and paraxial per-slit fields of each
    visited column, and of the screen, are therefore kept for the run, and a new segment only recombines them with
    its Gram matrix.
  * The column next to the slits is tried first. If it passes, the whole map passes; otherwise the worst case is one
    such column plus columns near the boundary.
  * First segment / later segments: c60 4.1 s / 1.5 s; electron presets 6.1 s / 0.45 s; photon_young 0.5 s / 0.4 s;
    12-slit electrons (d = 10 µm) 9.0 s / 0.9 s. The paraxial boundaries of all presets are unchanged
    (c60 4.549·10⁻⁵ m, electron 1.267·10⁻⁶ m, photon_young 1.404·10⁻³ m).
  * `test_rs_fields_cached_across_segments`: no new RS integral on a new segment.
* **The error shown for the histogram's |γ₁₂| was too small at small counts** [error in earlier]. `rc_v02.txt` R2:
  for photon_young (|γ| = 1) at N = 100, the median Fisher error was 0.0028 against a real scatter of 0.039. With
  full coherence the expected minima are ~0, the Fisher information there diverges, and the asymptotic error does not
  hold at small N.
  * The error shown is now a parametric bootstrap from the fitted model (60 refits). It is recomputed when the count
    grows by 10 %, at most once per second, and scaled by √(n_then/n) in between.
  * Calibration over 60 samples each, ratio of the median bootstrap error to the real scatter: 0.96 (|γ| = 1,
    N = 100), 0.92 (N = 1000), 1.36 and 0.97 (|γ| = 0.87, N = 100, 1000), 1.11 and 1.26 (|γ| = 0). The Fisher error
    gave 0.07 at |γ| = 1, N = 100.
  * `test_coherence_error_is_calibrated_at_full_coherence`.
* **The map showed fringes that the analyzer creates only at the screen** [error in earlier]. Found on a headless
  screenshot of the eraser preset (polarizers at 0° and 90° at the slits, analyzer at 45° in front of the screen).
  The map and the flow lines used the marks after the analyzer. Between the slits and the analyzer the marks are
  orthogonal, so there are no fringes there.
  * Now the map, the flow lines and the map's RS check use the marks before the analyzer, and the approximations
    panel says so when an analyzer is present.
  * The Englert check notes that its marks are taken at the screen, after the analyzer.
  * `test_map_shows_the_wave_before_the_analyzer`: the centre contrast of the last map column was 0.969 and is now
    0.061, while the screen curve keeps full fringes.
* **Map resolution at the slit plane.** For wide multi-slit geometries the 300-point map column next to the slits
  cannot resolve the slits; the reviewer's 12-slit case has a step of 0.55 µm for 0.1 µm slits. The run now states
  this in the approximations panel. The paraxial-start check samples 61 points per column and is resolved no better
  there → STATUS V12.

## Open items entered in STATUS.md (section V)

* V11: positions inside grid cells from the analytic amplitude (R15).
* V12: per-particle cost for many slits with per-particle kicks, source points or wavelengths. Also the one-time
  exact near-field check (up to about 10 s), and the 61-point sampling of that check (R16, and the further changes
  above).
* V5 and V6 narrowed (R1, R3).

## What the review confirmed (kept as is)

* the closed-form Fresnel amplitudes, their derivative, and the point-source, tilt and kick terms (1e-13);
* Parseval and the absorbed and missed fractions built on it;
* the Hankel asymptotics;
* Jones and spin matrices, state sampling, Englert D and V, readout completeness;
* microscope momentum transfer and dipole sampling;
* the Chapman and VCZ references;
* the multi-component current;
* kinematics by λ and by speed;
* segments and stories revealed at t_det;
* the absence of any "observed → no fringes" rule.
