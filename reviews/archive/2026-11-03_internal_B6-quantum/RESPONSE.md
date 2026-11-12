# Response to the review B6, quantum part (P15.3: `core.quantum.scene`, the 3-D sampling fix, `p02_quantum`)

Processed 2026-11-03/04 by a Claude subagent that wrote neither the review nor the code under review. The review text
and the reviewer's scripts are unchanged; my scripts and outputs are in the session's scratch folder
(`b6/proc_q/`, re-runs of the reviewer's scripts against the processed code in `b6/proc_q/rerun/*.after.out`), and
every number below that a test does not assert comes from one of them. Environment: image `light-funnel-viz`
(Python 3.11, NumPy 2.4, SciPy 1.17), CPU (`LFPHYS_NO_GPU=1`); one GPU 0 = CPU check through the session's GPU guard.

## Summary

| ID | decision | tag |
|---|---|---|
| Q1 | fixed: demodulated interpolation of ψ (engine default), Bohm checks in the run (control + absorption statistics) | [weakens] → fixed |
| Q2 | fixed: refused with the reason (closed axis + charged particle + any vector potential) | [weakens] → fixed |
| Q3 | fixed: a uniform field's change under a charged wave is refused with the reason; a flux tube's switch is kept (it is physical); the physical switch of a uniform field → STATUS | [weakens] → fixed |
| Q4 | fixed: the local-wavenumber rule (2/3 of the band next to anything that acts) at every change, packet and measurement; the step re-tuned after a measurement; the pass/fail grid check rejected with reason | [weakens] → fixed |
| Q5 | fixed (with absorption at the rate 2W, see P1) | [weakens] → fixed |
| Q6 | fixed: the step is shortened in the same change | [error in earlier] → fixed |
| Q7 | fixed: the companion sampled every 64 scene steps by the scene itself; "rigorous" withdrawn | [error in earlier] → fixed |
| Q8 | fixed: the check shows the flux-weighted angular average, normal and 60°; W₀ chosen for normal and 60°; 3-D layers 15 % of the window | [weakens] → fixed |
| Q9 | fixed: the marker fills the upper slit's channel; visibility 0.94 → 0.18; label says «почти гаснут» | [error in earlier] → fixed |
| Q10 | fixed: the tube inside a 3-nm wall between the slits; ideal half shift to 3.4·10⁻⁴ | [neutral] → fixed |
| Q11 | fixed: README numbers replaced by reproduced ones (STATUS V39 by the integrator, below) | [error in earlier] → fixed |
| Q12 | fixed | [neutral] → fixed |
| Q13 | fixed | [neutral] → fixed |
| Q14 | fixed: a ball below 1.45 edges refused (derived), the reached height in the inspector, the gradient's label | [neutral] → fixed |
| Q15 | fixed: the negative control replaced by an independent route; the joint unravelling, 3-D patches and p02's Bohm statistics tested | [neutral] → fixed |

Counts: 15 fixed, 0 partly, 0 rejected, 0 deferred as findings. Two of the reviewer's suggested remedies were not taken,
with reasons: Q4's pass/fail grid check (no derivable threshold, below) and Q3's physical switching impulse (not cheap:
refused instead, as the processing brief allows; the construction is recorded for STATUS). Seven items found while
processing (P1–P7). Tests for the framework review's F14–F16 (fixes by the integrator) were added to
`p02_quantum/tests/test_p02_quantum.py`.

---

## Q1 (error) — Bohm points inaccurate at admitted k d; p02 had no Bohm check

**Reproduced** with a copy of `s04` (`b6/proc_q/q1_kd.py`, `demodulate=False`): 6.5e-4, 3.3e-2, 0.43, 2.19, 7.89 nm
at k d = 0.5 … 2.5, the review's numbers to the digit. Higher orders do not cure it (plane-wave remainder of the
gradient at k d = 2: 0.13 for order 8, 2.7e-2 for 16, 5.7e-3 for 24: `pw_err.py`).

**Fix (engine).** `schrodinger_nd.sample(..., carrier=)` and `demodulated`: ψ is interpolated as e^{iκx} times the
Lagrange interpolant of ψ e^{−iκx} — exact at the samples, with the remainder of k − κ instead of k (the weights
w_j e^{iκ(x−x_j)}, derivative (w'_j + iκ w_j) e^{iκ(x−x_j)}). `bohm.carriers`: κ per point and axis from the phase
steps of the samples around the nearest node (unique for |k| d < π), applied in full where it makes the samples clearly
smoother and scaled down to none where it does not (near a node the plain interpolant of a locally polynomial ψ is
better; the continuous scaling is P3). `advance_ensemble(demodulate=True)` uses it (default); `_Patches` takes the
carrier and a patch wide enough for a higher order. Verified (same script, `demodulate=True`): 2.5e-4, 3.0e-5,
1.7e-5, 8.9e-5, 2.1e-5 nm at k d = 0.5 … 2.5 (the integrator's tolerance), and faster (k d = 2: 0.8 s instead of
9.6 s: fewer sub-steps).

**Fix (p02).** Two running checks per particle with Bohm points (group «Бом», as v11): (1) a control — the first 8
points integrated again with order-16 interpolation and 4× tighter time tolerances; the median distance of the pairs
in the same state must be below half a grid step (the scale on which the grid knows |ψ|²), at most one pair absorbed
elsewhere; the largest deviation is in the note (near the wall's node lattice single trajectories diverge by up to
0.24 nm without any error: sensitivity, hence the median); (2) the absorption statistics — the count absorbed by each
absorber against Σ_epochs m ΔA_k/N (binomial, Poisson for small counts), 5σ two-sided. The double slit with 300 points
(seed 3): screen 67 vs 55.5 ± 6.7, control median 0.05 nm; over ten seeds the screen count averages 56.8 (no bias;
seed 4 gives 77, 3.2σ).

**Verification.** `test_schrodinger_nd.py::test_demodulated_sampling_is_exact_on_the_samples_and_for_its_carrier`
(plane wave at k d = 2.5 to 1e-12; samples returned exactly; the plain gradient errs by > 0.1 — negative control);
`test_bohm_nd.py::test_demodulated_interpolation_keeps_trajectories_at_any_admitted_k_d` (< 1e-3 nm at k d = 1, 2,
2.5; plain at 2: > 1 nm); `test_p02_quantum.py::test_bohm_registrations_follow_the_absorbed_probabilities` (negative
control: half the velocity fails the statistics) and `::test_bohm_control_catches_an_inaccurate_interpolation`
(λ = 1 nm, k d = 1.96: passes; the ensemble's plain interpolation fails the control). The existing vortex and patch
tests pass. GPU 0 = CPU (`b6/proc_q/q_gpu.out`): demodulated sampling on the device 2.9e-15 / 3.2e-14, carriers 1e-14,
3-D Bohm 3e-15 / 4e-15, p02's double slit with Bohm points to t = 20: wave 6.6e-15, points 1.9e-11 nm, the same
absorbers. The engine default changes v11/v12 too: their tests pass (32 passed, 2 skipped: GPU) — see "Changes for
the integrator".

## Q2 (error) — closed edges, a charged particle and a vector potential

**Fix.** `Scene._gauge_reason`: on every axis not covered by absorbing edges, A must be periodic across the window's
face and q∮A_i dx_i a multiple of 2π; otherwise a charged particle next to the field (or a field next to it, or a
change of the edges) is refused with the reason (both the Landau strip and the flux tube fail it; so does any
whole-window field). p02's approximations say so for a closed world; README.

**Verification.** `test_quantum_scene.py::test_a_closed_window_refuses_a_charged_particle_next_to_a_field`: refused
with closed edges and with edges on one axis only, either order, for a field and a tube; open edges accept; negative
control (the refusal bypassed, the review's s09b): ⟨v_y⟩ = −0.748 for the packet that never meets the field, −0.009
with open edges. `test_p02_quantum.py::test_a_field_is_not_changed_under_a_charged_packet`: the cyclotron preset with
closed edges is refused. The reviewer's `s09b` now stops with the refusal (`rerun/s09b_closed_edges_sheet.after.out`).

## Q3 (error) — a field changed under a charged packet

**Decision.** Refuse, with the reason, a change of a uniform field's (Landau-gauge) vector potential while a charged
particle's probability where ΔA ≠ 0 exceeds the balance's round-off (`Scene._switch_reason`). Reason: keeping ψ makes
the kinetic momentum jump by −qΔA; Faraday's law fixes the induced field only for a given magnet (for a z-invariant
field with E → 0 far away: the Coulomb gauge); the Landau gauge's reference is an implementation detail, and a
whole-window field has no defined axis at all. A flux tube's A is the Coulomb gauge of a thin solenoid
(Φ/(2πr) outside), so its switch is physical and kept (docstring corrected: the old text called the tube's case
Faraday's and the strip's merely "gauge-dependent", and suggested placing packets after fields). A correct
construction for a uniform field (the Coulomb gauge of the region's shape, a 2-D Poisson problem, plus the gauge
transformation of ψ at the change) is not cheap: recorded for STATUS. In p02 «Очистить» removes particles first (P5).

**Verification.** `test_quantum_scene.py::test_a_uniform_field_is_not_changed_under_a_charged_wave`: refused for both
set-ups of s15; allowed for a tube's change and for a field whose ΔA lies away from the packet; negative control (the
refusal bypassed): the two set-ups identical in the window give kinetic momenta 2.89/nm apart right after the change
(q ΔB · 38 nm, as the review found 29 nm apart later). `test_p02_quantum.py::test_a_field_is_not_changed_under_a_charged_packet`
(the inspector's change refused with the reason, the value rolled back; clear still works). `rerun/s15...after.out`:
both changes refused, the runs stay 0.00 nm apart.

## Q4 (error) — grid resolution checked only for the initial packet

**Reproduced** (`well_res.py`): 0.92337 vs 0.99730 at −3 eV; the transition with the well's depth: transmission errors
6e-7, 1.5e-4, 8e-4, 4.3e-3, 7.4e-2 at K_loc d = 1.78, 2.11, 2.40, 2.65, 3.10 (K_loc = sqrt((|k| + 6σ_k)² + 2mΔV)) —
the jump is at the 2/3 bound of pseudo-spectral products (2.09), not at π: the reviewer's rule with π/d would have
admitted the s18 case (3.10 < π). Barriers too: 0.3 % at K d = 2.38, 14 % at 2.77 (`barrier_res.py`).

**Fix (engine).** `Scene._resolution_reason` / `_excess`: along the axes where something acts on the particle
(`_scatter_axes`: potentials, detectors, its A, its spin's field, a marker; an environment: all) its largest wavenumber
K = |k| + 6σ_k (`k_spread`: widened in quadrature by every measurement, 1/(4s²), and jump, 1/(2a²); one jump included
for an environment's admission), raised by the convertible potential energy (`_convertible`: V + |b| where the packet
started or averaged over the wave now, minus the lowest V − |b|), must stay within 2/3 π/d; along free axes the packet
rule. Checked at every change of the set-up (not for a change of the step alone, P7), for every new packet, and before
a measurement: `Scene.measure_min_sigma` (bisection; a refusal names the smallest σ, the generator untouched). p02
re-tunes the step after a measurement (σ_k widened). Derivation in `sources/verification_2026-11-03_p15_3.md` §8 (b).

**Not taken:** a pass/fail grid check. The band-edge content a correct run carries — the potential's own edge spectrum
(admitted at 1e-3 by the edge rule) and the unresolved evanescent tail inside high walls — overlaps what an
under-resolved run shows: the spectral power at the band's faces is 1.6e-7 of its peak in the double slit and 1.1e-6
with a 30 eV wall (whose wave errs only 6e-4, s07b), above the packet rule's e^{−18} = 1.5e-8 the reviewer proposed;
the outer-third probability is 4e-5 and 1.7e-4 there (`face_power.py`). The check stays information, its note states
the rule and these numbers; what it guarded is now refused at the source.

**Verification.** `test_quantum_scene.py::test_the_grid_must_hold_a_wave_in_a_well` (quasi-1-D against transfer
matrices: refused on the 0.31-nm grid; bypassed it errs by 7.4e-2 — negative control; admitted grids 2.4e-6 and 2e-7;
measurement: s = `measure_min_sigma` puts the 6σ point exactly at π/d, 0.99 of it is refused and changes nothing).
`test_p02_quantum.py::test_a_position_measurement_collapses_the_wave_to_its_outcome` (0.5 nm refused, min 0.85 nm).
`rerun/s18...after.out`, `s10...after.out` (σ = d and 2d refused, σ = 1 nm accepted). Consequences: p02's 3-D preset
moved from λ = 3 to 4 nm (3.59/nm exceeded 2/3 of the 64³ band, 3.35/nm); two engine tests had set-ups the rule now
refuses (the state round trip's He atom after a jump of a = 0.6 nm on a 0.25-nm grid: grid made 0.15 nm; the absorbed-
outcome measurement at s = 0.3 < 0.52: now 0.6).

## Q5 (should-fix) — Bohm hits discarded after a jump

**Fix.** At a jump (`_redraw_flight`) the points already absorbed stay; those not absorbed are drawn again from the wave
now, their number unchanged, with new absorption clocks; the epoch closes and a new one opens (the statistics check
adds the epochs). A position measurement still re-draws the whole ensemble (it conditions on "not absorbed"). This
needed P1 (absorption at the rate 2W instead of registration on entry).

**Verification.** `test_p02_quantum.py::test_a_jump_keeps_the_registered_bohm_points` (the review's s06 set-up: 4
jumps; at the re-draw the absorbed points and their keys are unchanged, the in-flight count unchanged; two epochs; the
statistics check passes: screen 239 vs 235.5 ± 6.2, edges 61 vs 86.4 ± 7.8).

## Q6 (should-fix) — a strong environment refused

**Fix.** `Scene.add(obj, dt=)` / `update(oid, dt=, ...)` change the step in the same atomic change; p02's `_dt_with`
computes it (`_dt_target`: the step for the particles within λ dt ≤ 0.05, also with no particle). README now true.

**Verification.** `test_p02_quantum.py::test_a_strong_environment_shortens_the_step` (1000/ps added and set from 10/ps:
dt = 2^⌊log2(0.05/λ)⌋; the neutron's 16-unit step shortened for the default environment). `rerun/s17*.after.out`:
λ dt = 0.0337 and 0.0432, no errors.

## Q7 (should-fix) — the companion's accumulated error is an estimate

**Fix.** `Scene.error_every`: the companion estimate every that many steps of each particle inside `advance`,
independent of who reads the checks (in the state dict); p02 sets 64 and no longer forces an estimate per check.
Wording: "a leading-order estimate of a bound, as good as its sampling" (scene docstring, `step_error`), the energy
bound "a bound given that estimate" (p02 check note, README, verification file §7 [error in earlier]).

**Verification.** `test_quantum_scene.py::test_the_companion_is_sampled_by_steps` (a packet crossing a barrier
between free stretches; Chebyshev reference: true error 5.5e-4; start/end only 1.3e-4 < true — negative control; every
64 steps 8.6e-3, within 1 % of every 10). `rerun/s19...after.out`: 3.75e-3 for estimates every 0.25, 2.55 and 25.5
units (it was 7.9e-5 for the last); the true error 2.55e-4.

## Q8 (should-fix) — the edges' reflection at normal incidence only

**Fix (p02).** The check's value is the flux-weighted average over directions (`_edge_RT`: isotropic, weight cos θ in a
plane, cos θ sin θ in space), the note gives normal incidence, 60° and the leak. W₀ is chosen for the normal
wavenumbers |k|, |k| ± 2σ_k and for |k| at 60° (optimizing the isotropic average instead is dominated by grazing waves,
which any layer reflects, and weakened the double slit's layer at normal incidence). In 3-D the layers are 15 % of the
window (6 nm in the 40-nm preset; they were 4 nm, one wavelength). Numbers (`q8_edges.out`): plane edges R = 1.4e-7
normal, 5.0e-5 at 60° (was 8.1e-4), 7.8e-3 averaged; volume 2.2e-5, 2.1e-2, 4.0e-2; the review's s14 route (40- vs
60-nm window, same step): the probability inside |x_i| < 14 nm agrees to 2e-5 / 3e-5 at t = 18 / 22 (it was 9.5e-4 /
5.4e-4 for λ = 3 with 4-nm layers; 1.3e-3 / 7e-4 for λ = 4 with 4-nm layers). Detectors stay at normal
incidence (a screen is met head-on; labelled so). What remains in 3-D (a few per cent at 60° for slow waves) is shown by
the check and goes to STATUS.

**Verification.** `test_quantum_scene.py::test_oblique_incidence_on_the_edge_layers` (a packet at 60° against
`edge_reflection` at k cos θ: within 2 % of R; the layer model's limitation is P2).

## Q9 (should-fix) — the which-path preset

**Fix.** The slits are 12-nm channels and the marker fills the upper one: 10 nm along the beam, edges across inside the
wall (no lens), c = 0.032 rad/fs = 0.021 eV = 5.6 % of E (calibrated by `q9_design.py`: the transmitted marker of the
upper slit alone P(1) = 0.95, |coherence| 0.04). Measured on the screen: visibility near the centre 0.94 without the
marker, 0.18 with it (`rerun/s21_which_path.after.out`: 0.949 / 0.176). The label says so: «Метка пути в верхней
щели: полосы почти гаснут (видность 0,94 → 0,18)»; the residue is the packet's spread of speeds (the turn is c times
the time spent in the marker). README section "Presets that demonstrate an effect".

**Verification.** `test_p02_quantum.py::test_the_presets_show_their_effects` (visibility < 0.25 with the marker,
> 0.9 without).

## Q10 (nit) — the Aharonov–Bohm preset

**Fix.** The tube (half a flux quantum, R = 0.5 nm) at (0, 0) inside a 3-nm wall between the slits (its field is e^{−9}
of the peak at the wall's faces); label «в стенке между щелями». The reviewer's s02 against the new preset
(`b6/proc_q/q10_ab.out`, `rerun/s02_ab_preset.after.out`): the pattern equals the ideal half shift 2(S₁ + S₂) − P₀ to
3.4e-4 of its peak (was 5.6 %), symmetric; the field felt rounds to 0.0000.

**Verification.** `test_the_presets_show_their_effects` (central minimum < 1e-3 of the peak, mirror symmetric to 1e-3).

## Q11 (nit) — numbers not reproduced

**Fix.** README: "4 times more steps"; true errors at t = 12 2.6e-4 (this step) and 1.6e-5 (suggest_dt's), companion
estimates 3.7e-3 and 2.3e-4, 30/300 eV walls 6.0e-4 / 1.1e-3 (the review's s07/s07b outputs; its s19 re-run here
reproduces this step's 2.55e-4 and 3.75e-3; also in `_dt_target`'s docstring); the absorbers' numbers re-measured after Q8 (above) with what each is; the screen's
"10⁻¹¹" and "1.6 %" replaced (R ≤ 1.2e-6, leak ≤ 6e-9 at the new W₀; the 1-nm-edge figure quoted with its W₀ from
the review's s08b). All tagged [error in earlier]. STATUS V39 (c), (d): text for the integrator below.

## Q12 (nit) — stale snapshots

**Fix.** `p.snaps = None` in `measure`, `set_wave`, every `_commit` (replace_particle makes a new particle).
**Verification.** `test_quantum_scene.py::test_snapshots_are_dropped_by_every_break_of_the_interval`; `rerun/s20`: None.

## Q13 (nit) — the energy reference's time

**Fix.** `t_ref` is set when E_ref is taken (first `checks()` after a change); p02's note says «против ⟨H⟩ в t = …».
**Verification.** `test_quantum_scene.py::test_the_energy_reference_is_dated_when_it_is_taken` (since = 3, not 0);
`rerun/s20`: since = 3.0.

## Q14 (nit) — thin shapes, the gradient's label

**Fix.** `Ball.check` refuses R < 1.45 w: the kink at the centre has slope exp(−R²/ε²) of the edge's steepest, kept
≤ EDGE_TOL (derived, verification §8 (c)). `Shape.peak` (closed forms for box, ball, wall, step); p02's inspector shows
"наибольшая высота" next to the nominal one (the tunnel barrier: 0.4733 of 0.5 eV). The label: «Bx = Bx₀ − g·(x − x_c),
By = By₀ + g·(y − y_c)» with the centre explained in the help.
**Verification.** `test_quantum_scene.py::test_a_shapes_peak_and_the_balls_kink`,
`test_p02_quantum.py::test_the_inspector_shows_a_shapes_actual_height`.

## Q15 (nit) — tests

* The tautological negative control is removed; `test_each_detectors_share_against_its_absorption_rate` compares each
  detector's attributed share with ∫2W_k|ψ|² dt (trapezoid per step) for two detectors overlapping each other and an
  edge layer: O(dt²) (1.85e-5 → 4.6e-6, ratio 4.0); negative control: attribution by W_k alone misses by 0.43.
* `test_jumps_and_a_detector_together_reproduce_the_master_equation` (the review's s11: 12 z-scores < 5; 0.7 W
  rejected).
* `test_bohm_nd.py::test_patches_in_three_dimensions_and_for_a_spinor` (s12).
* p02's Bohm statistics: Q1's two tests.

## Tests for the framework review's F14–F16 (fixes by the integrator)

`test_a_scene_file_saved_later_starts_the_engines_clock_at_its_time` (steps = 0, t = the file's; negative control:
the clock at 0 integrates ≥ t/dt steps), `test_overflowing_values_are_refused_and_the_waves_stay_finite` (1e308 eV
refused by the schema; `_finite` refuses an infinite height; the wave stays finite),
`test_changing_only_the_bohm_count_keeps_the_wave` (the same wave array and ⟨x⟩; a width change replaces the packet).

## Found while processing

* **P1** [weakens → fixed] Registering a Bohm point when it *enters* an absorber cannot survive a jump: probability
  inside an absorber but not yet absorbed is counted by points as registered, and after the jump re-localizes the wave
  the in-flight points stood for the wrong probability (first implementation of Q5: screen 175 against 322 expected,
  more than the 300 points). Now (p02 `_absorb`) points move with Bohm's velocity also inside absorbers and are absorbed
  at the rate 2W (an Exp(1) threshold per point, the absorber drawn by W_k/W): the survivors stay |ψ|²/N-distributed
  (continuity with the sink −2Wρ), so each absorber takes the share of points it takes of the probability, exactly in
  expectation (verification §8 (f)). Drawn where absorbed; README and approximations say so (STATUS V39 (e) text below).
* **P2** [neutral] `layer_reflection` models an edge layer as a ramp ending abruptly; on the periodic grid a wave that
  passes it meets the opposite face's mirrored ramp. With a leak comparable to R the model's R (mostly from the abrupt
  end) is larger than what a run returns (×14 at a leak of 0.38): conservative; the playground's strengths keep the leak
  below 1e-5 (docstring of the oblique test, verification §8 (g)).
* **P3** [neutral → fixed] A binary carrier choice made v12's own control (`bohm_accuracy`) fail
  (`test_through_the_slits_a_slit_closed_in_flight_acts_on_both_runs`): ensemble and control points on either side of
  the choice used different interpolants. The carrier is now scaled continuously; v11/v12 pass.
* **P4** [useful → fixed] Found by the GPU check: `carriers` brought a CuPy gather to the host through
  `backend.to_numpy`, which fails while the backend has not loaded CuPy itself; now `.get()`.
* **P5** [neutral] The framework's `clear` stops midway when an `on_remove` refuses (the objects before it are deleted,
  no scene message is emitted): p02 now orders particles first (the only refusal it can meet there), the framework
  item is for the integrator.
* **P6** [neutral] The resolution rule refuses set-ups that ran before: p02's 3-D preset and two engine tests were
  adjusted (Q4); the reviewer's s10 at σ = 2 d is now refused in the double slit (needs ≥ 0.90 nm next to the wall).
* **P7** [neutral] A change of the time step alone no longer re-runs the set-up's checks (a measurement's re-tuned step
  must not be refused by a position the outcome drew).

## Test runs (final)

Engine: `test_quantum_scene.py`, `test_schrodinger_nd.py`, `test_bohm_nd.py`, `test_boundary.py`, `test_layers.py`,
`test_licences.py`; visualizations: `p02_quantum/tests` and `tests/test_restore.py tests/test_checkpoint.py -k "p02 or
shared"`; plus v11/v12 (`32 passed, 2 skipped`, GPU-only). Results in "Final runs" at the end.

## Changes for the integrator

1. **`engine/STATUS.md`, row V39** — replace items (c)–(f) and the plan column by:

   > (c) the energy bound 2‖Hψ‖e + e²‖H‖ is a bound given the companion's estimate e, and e (one step dt against two
   > dt/2 every 64 scene steps, `Scene.error_every`, whatever the playback speed) is a leading-order estimate of the
   > global error, not a bound (review B6-Q7 [error in earlier]: "rigorous"; with estimates only around a wall
   > interaction it fell 3× below the true error); loose where sampled (×15 on the double slit: 3.7·10⁻³ against
   > 2.6·10⁻⁴); the flux-plane balance and the grid check are information only (no derived tolerance: B6-Q4); (d) the
   > time step is chosen from the particles' kinetic energy (σ_k widened by measurements and jumps) and the potential
   > they can convert, not from barriers above them (measured: the double slit's true wave error 2.6·10⁻⁴ against
   > 1.6·10⁻⁵ at a 4 times smaller step; 30/300 eV walls 6.0·10⁻⁴/1.1·10⁻³; B6-Q11 [error in earlier]: "8 times",
   > "1.0·10⁻³ → 6·10⁻⁵"); next to anything that acts on a particle its wavenumbers must stay within 2/3 of the grid's
   > band (refused otherwise, also measurements finer than `measure_min_sigma`; jumps of an environment widen the
   > spectrum as a run goes, checked at admission for one jump only); (e) Bohm points: an interpretation, interpolated
   > with each point's carrier (B6-Q1); inside absorbers absorbed at the rate 2W (equivariance with absorption; the
   > run checks the counts against the absorbed probabilities and a control of 8 points); redrawn from |ψ|² after a
   > measurement, only the unabsorbed ones after a jump; on the GPU many small device calls; (f) a packet needs 7.4 σ to
   > the window's faces (periodic grid), so windows are large; a charged particle next to a vector potential needs open
   > edges on every axis (B6-Q2); a uniform field cannot be changed while a charged particle's wave is where its A
   > changes (refused: the switch's induced field depends on the magnet; a flux tube's switch, a thin solenoid's, is
   > kept; B6-Q3); (h) the open edges in 3-D (15 % of the window) still reflect a few per cent of slow waves at 60°
   > (the 3-D preset: 2·10⁻² at 60°, 4·10⁻² averaged over directions; shown in the run)

   and the plan column by:

   > (b) a compressed wave in the file (or a reference to the record); (c) a sharper energy bound (phase-insensitive),
   > a derived flux tolerance; (e) Bohm points batched on the device or on the host by patches; (f) the physical switch
   > of a uniform field under a charged wave: the Coulomb gauge of the region's shape (a 2-D Poisson problem) and the
   > gauge transformation of ψ at the change; (g) keep the pictures thinned beyond a budget, decoded on demand; (h) wider
   > or adaptive layers for slow waves in 3-D (or a larger window)

   (item (a) and (g) unchanged).
2. **`engine/STATUS.md`, row V37** (framework) — add: "(f) a scene command `clear` that meets a refused `on_remove`
   stops midway: the objects removed before it stay removed and no scene message is emitted (found while processing
   review B6-quantum, P5; p02 removes its particles first); plan: check every removal first, or roll back".
3. **`engine/lfphys/README.md`**:
   * row `core.quantum.schrodinger_nd`: "ψ and ∇ψ at any point (symmetric Lagrange stencils)" → "ψ and ∇ψ at any point
     (symmetric Lagrange stencils; optionally demodulated by a carrier per point: exact on the samples, the remainder
     of k − κ: review B6-Q1)";
   * row `core.quantum.scene`: after "the window's open edges;" insert "the grid's band enforced for every wave (next to
     anything that acts on it, its wavenumbers with the convertible energy within 2/3 of π/d; measurements no finer than
     the post-measurement wave allows); a charged particle next to a vector potential only with open edges; a uniform
     field not changed under a charged wave;", and replace "running checks (energy of a closed scene, flux through
     planes, the time step by a companion, grid resolution)" by "running checks (energy of a closed scene, flux through
     planes, the time step by a companion sampled every N steps — an estimate, grid resolution)";
   * row `theories.interpretations.copenhagen, bohm, everett`: after "error-controlled Dormand–Prince 5(4) steps per
     particle (also near nodes)" insert "with ψ interpolated around each point's local wavevector (B6-Q1)".
4. **`visualizations/v11_double_slit_2d/README.md`** (and v12's, if it repeats it): the engine's default changed —
   "with ψ and ∇ψ interpolated from the grid (degree 8, …)" → "with ψ and ∇ψ interpolated from the grid (degree 8 …;
   since review B6-Q1 around each particle's local wavevector, which removes the remainder of k d)". Their tests pass
   unchanged (32 passed, 2 skipped).
5. **`engine/reviews/README.md`**: move this folder to `reviews/archive/` and add the registry row:

   > | `archive/2026-11-03_internal_B6-quantum/` | internal (Claude subagent) | batch B6, quantum part: P15.3
   > (`core.quantum.scene`, the 3-D sampling fix, `p02_quantum`), its scripts and outputs, a GPU check | 2026-11-03 | `RESPONSE.md`
   > (processed 2026-11-04: 15 of 15 fixed — Bohm points off by 2 nm at k d = 2: ψ now interpolated around each point's
   > local wavevector, p02's Bohm points checked in the run (control, absorption statistics) and absorbed at the rate
   > 2W; closed edges with a charged particle and a field refused (a false field sheet); a uniform field's change under
   > a charged wave refused; the grid's band enforced next to potentials (a −3 eV well erred 7 %) and for measurements;
   > a jump keeps absorbed Bohm points; strong environments shorten the step; the companion sampled by steps
   > ("rigorous" [error in earlier]); edges' reflection over angles, 3-D layers wider; which-path preset rebuilt
   > (visibility 0.94 → 0.18; it was 0.61 [error in earlier]); AB tube inside the wall; README numbers [error in
   > earlier]; while processing: the stop-on-entry Bohm registration fails at jumps, a GPU host transfer, v12's
   > control and the carrier's continuity, the framework's partial `clear` → STATUS V37 (f)) |
6. The engine default `bohm.advance_ensemble(demodulate=True)` is new behaviour for every caller (v11, v12): mention it
   in the batch report.
7. **`visualizations/tests/test_restore.py` and `test_checkpoint.py` (framework tests, not mine) must change**, or their
   p02 cases fail: their fast p02 world is the tunnel preset on a 128-point grid (d = 0.625 nm), where the λ = 2 nm
   electron next to the barrier reaches K d = 2.71, beyond 2/3 of the band — under-resolved (a barrier at K d = 2.77
   erred by 14 %, Q4), and now refused by the scene. Exact replacements, verified on copies in the scratch folder
   (`b6/proc_q/shared/`: `-k "p02 or shared"` → 4 passed in 112 s):
   * `test_restore.py`, in `SMALL`: `"p02_quantum": {**registry.load("p02_quantum")["schema"].presets["tunnel"]["params"], "n2": "128"},`
     → `"p02_quantum": {**registry.load("p02_quantum")["schema"].presets["tunnel"]["params"], "n2": "192"},`
   * `test_checkpoint.py`, in `PLAN`: `"p02_quantum": (None, None, ("measure", {"particle": "o3", "sigma": 1.0}), False),`
     → `"p02_quantum": (None, None, ("measure", {"particle": "o3", "sigma": 2.5}), False),` (on the 192-point grid the
     post-measurement wave needs σ ≥ 2.06 nm next to the barrier; 1.0 would be refused, so the session would carry an
     error instead of a measurement).
   The browser check `tests/browser/keyframes.mjs` was not run here; its p02 plan (the trap preset, a measurement at
   σ = 1.0 nm, then a packet at x = −8 nm, λ = 4 nm) is still accepted by the processed code (checked with the harness:
   the smallest σ there is 0.85 nm, no errors).

## Final runs

* Engine (`lfphys/`): `tests/test_quantum_scene.py tests/test_schrodinger_nd.py tests/test_bohm_nd.py
  tests/test_boundary.py tests/test_layers.py tests/test_licences.py` — **265 passed, 3 skipped** (GPU-only tests) in
  246 s.
* `visualizations/p02_quantum/tests` — **25 passed** in 543 s.
* `visualizations/tests/test_restore.py tests/test_checkpoint.py -k "p02 or shared"` — **4 failed** with the framework
  tests as they are (the p02 world they build is refused: item 7 above); **4 passed** with item 7's two replacements
  (copies, 112 s). The other visualizations' cases were not affected by my files except through the Bohm default:
* `v11_double_slit_2d/tests v12_arrival_times_2d/tests` — **32 passed, 2 skipped** (GPU) in 678 s.
* GPU 0 = CPU: `b6/proc_q/q_gpu.out` (through the session's GPU guard, 44 s).
* The reviewer's scripts re-run against the processed code (copies; outputs `b6/proc_q/rerun/*.after.out`): s01
  unchanged (0.13213), s02 3.4e-4, s09b and s15 and s18 refused with the reasons, s10 σ = d, 2d refused and 1 nm taken,
  s17/s17b no refusals, s19 3.75e-3 at every sampling, s20 (a) None, (b) since 3.0, s21 visibility 0.176 / 0.949.
