# Review: batch B6, quantum part (plan P15.3) — `core.quantum.scene`, the 3-D sampling fix, the playground `p02_quantum`

**Status: awaiting processing.**
Reviewer: internal (Claude subagent, 2026-11-03). I did not write the code under review. Per `reviews/README.md` I do
not write `RESPONSE.md` and I do not move this folder.

## Scope

1. `lfphys/lfphys/core/quantum/scene.py` (new) and `lfphys/tests/test_quantum_scene.py`.
2. `lfphys/sources/verification_2026-11-03_p15_3.md`, the `core.quantum.scene` row of `lfphys/README.md`.
3. The einsum fix in `schrodinger_nd.sample` and `bohm._Patches.sample` (diff against HEAD, read-only git) and
   `test_sample_in_three_dimensions_and_for_a_spinor`.
4. The wrapper `visualizations/p02_quantum/` (viz.py, README.md, tests) on `visualizations/server/lfviz/playground.py`.

## Environment and how to re-run

Image `light-funnel-viz` (Python 3.11.17, NumPy 2.4.6, SciPy 1.17.1; `s00_env.out`), engine mounted read-only, CPU
(`LFPHYS_NO_GPU=1`) except `s13` (GPU 0 through the session's GPU guard, `s13_gpu.sh`). Every script is in this
folder with its output (`<name>.out`): `./run.sh <suffix> <script.py>` runs one in a container `lf-b6rq-<suffix>`.
The batch's own tests: `t01_tests.sh` → `t01_tests.out` (engine: 36 passed, 1 skipped (GPU); p02: 15 passed).
Source quotations: `v01_sources.sh <download dir>` → `v01_sources.out`.

## Summary

| ID | severity | finding | tag |
|---|---|---|---|
| Q1 | error | Bohm points err by up to 26 % of their travel at wavenumbers the scene admits (8th-order spatial interpolation, k d up to 2.8); p02 has no Bohm accuracy check (v11 has three) | [weakens] |
| Q2 | error | Closed (periodic) edges + a charged particle + a vector potential: the Landau gauge leaves a field sheet of flux −Φ at the window's face that deflects packets which never approach the field; nothing refuses it | [weakens] |
| Q3 | error | A live change of B while a charged packet flies gives a kick that depends only on the hidden gauge reference: two set-ups identical inside the window end 29 nm apart; not flagged in the run | [weakens] |
| Q4 | error | Grid resolution is enforced only for the initial packet: a −3 eV well transmits 0.923 instead of 0.997 (finer grid) with only an "info" grid check (tail 25 %); a measurement at σ = d leaves an under-resolved wave | [weakens] |
| Q5 | should-fix | After a localization jump the wrapper discards the Bohm points already registered by absorbers and re-seeds all of them into the in-flight wave: the Bohm counts stop estimating the absorbed probabilities | [weakens] |
| Q6 | should-fix | An environment with λ·dt > 0.05 is refused although the wrapper would shorten dt; with a neutron even the palette's default environment is refused (README: "the bound is kept") | [error in earlier] |
| Q7 | should-fix | The companion's accumulated error is not a bound: sampled only when the checks run (once per wall second), it misses the wall interaction at 10× speed (7.9e-5 vs true 2.55e-4); "rigorous" in README / test / STATUS V39 (c) | [error in earlier] |
| Q8 | should-fix | The edges' reflection check is normal incidence at |k| only; in the 3-D preset the faces return ~1e-3 of the wave (10× the 1.3e-4 shown), R = 6.6e-2 at 60° | [weakens] |
| Q9 | should-fix | Preset "which_path" ("интерференция гаснет"): the visibility drops from 0.95 to 0.61 only; the 3 × 3 nm marker turns by ~48°, not ~86° (it acts as a ±0.12 eV lens) | [error in earlier] |
| Q10 | nit | Preset "aharonov_bohm": the tube is not between the slits but behind the wall in the beams' overlap; the half-fringe shift holds to 5.6 % of the peak, left-right asymmetric | [neutral] |
| Q11 | nit | README / STATUS numbers not reproduced as stated (dt "8 times", "1.0e-3 → 6e-5"; screen "1e-11", "1 nm edge 1.6 %"); the time-step argument itself holds | [error in earlier] |
| Q12 | nit | `Scene.snapshots` returns the stale pre-measurement interval after `measure()` (docstring: None) | [neutral] |
| Q13 | nit | The energy check's "since" is the time of the change, but E_ref is taken at the first `checks()` after it | [neutral] |
| Q14 | nit | Shapes thinner than their edge do not reach their nominal height (tunnel preset 0.947; a 0.5 nm ball 0.90 with a cone at its centre); the gradient label omits B0 and the centre | [neutral] |
| Q15 | nit | Tests: a tautological negative control; the joint localization + detector unravelling, the 3-D patch path and p02's Bohm statistics are untested (here reproduced: all three correct) | [neutral] |

Verified without a finding (details at the end): the sources' quotations; units; the tunnelling preset against
transfer matrices; the joint jump + detector unravelling against the master equation; the 3-D patch path; GPU 0 =
CPU; the time-step argument for high walls; the 8-step Bohm interval near walls; Bohm hit fractions at the presets'
k d; the layer placement.

---

## Q1 (error) — Bohm points are inaccurate at admitted wavenumbers; p02 has no Bohm accuracy check

**Location.** `lfphys/lfphys/core/quantum/schrodinger_nd.py:321-364` (`sample`: tensor Lagrange interpolation of
order 8), used by `lfphys/lfphys/theories/interpretations/bohm.py:250-323` (`advance_ensemble`, whose error control
covers only the time integration); the admission rule `scene.py:175` / `1308-1311` (`|k| + 6σ_k ≤ π/d`, i.e.
k d up to ≈ 2.8 for σ = 3 nm on the presets' grids); the wrapper `visualizations/p02_quantum/viz.py:507-566`
(`_seed_bohm`, `_bohm_step`) and its checks `viz.py:702-789` (no Bohm check).

**Evidence.** `s03_bohm_chunk.py` → `s03_bohm_chunk.out`: a free packet on the double-slit grid (k d = 0.98) gives
the same error, 4.1e-2 nm over 37.6 nm (1.1e-3), for Bohm intervals of 2, 8 and 16 steps — the error is spatial, not
temporal. `s04_bohm_kd.py` → `s04_bohm_kd.out` (exact trajectories `bohm.gaussian_trajectory`, wrapper's dt rule,
8-step intervals, all packets admitted by the scene):

| k d | λ (nm) | max \|X − exact\| over ~30 nm | relative | derivative remainder 576 (k d)^8/9! |
|---|---|---|---|---|
| 0.5 | 3.93 | 6.5e-4 nm | 2.2e-5 | 6.2e-6 |
| 1.0 | 1.96 | 3.3e-2 nm | 1.1e-3 | 1.6e-3 |
| 1.5 | 1.31 | 0.43 nm | 1.4e-2 | 4.1e-2 |
| 2.0 | 0.98 | 2.19 nm | 7.3e-2 | 0.41 |
| 2.5 | 0.79 | 7.89 nm | 0.26 | 2.4 |

The growth follows the interpolation remainder that `sample`'s own docstring states. At k d = 2 the hits are off by
~2 nm, a third of the double slit's fringe spacing (~5.8 nm); at k d = 2.5 by more than a fringe. The engine test
(`test_bohm_trajectories_from_the_scene_follow_the_exact_free_ones`) runs at k d = 0.4 with 2-step intervals and
cannot see this. v11 measures its Bohm points in the run (`v11_double_slit_2d/viz.py:681-718`: hits against the
pattern, a tighter control integration, the fraction on the screen against the probability); p02 measures nothing,
and its test `test_bohm_points_are_registered_by_the_detectors_they_enter` only counts points. In a well (Q4) the
local k d is larger still.

**Fix.** Either interpolate ψ and ∇ψ at the points spectrally (the grid's own band-limited representation: exact for
what the grid holds, independent of k d), or refuse/flag Bohm points when the wave's largest k d exceeds a value
derived from the remainder (e.g. 576 (k d)^8/9! ≤ 1e-3 → k d ≤ 0.95); and add v11's running checks to p02 (the
fraction registered by each absorber against its absorbed probability with a binomial bound — see `s05` — and a
control subset integrated with a finer interpolation).

## Q2 (error) — closed edges with a charged particle next to a vector potential: a spurious field sheet at the face

**Location.** `scene.py:39-49` (docstring: "psi must vanish at those edges (the open edges absorb: EdgeLayers)"),
`scene.py:709-737` (`vector_potential`, Landau gauge), `_commit` `scene.py:1233-1236` and `_prepare`
`scene.py:1318-1325` (no check of the edges); the wrapper offers closed edges as a law
(`viz.py:60-62`) together with `bfield` and `flux` (`viz.py:322-331`).

**Evidence.** `s09b_closed_edges_sheet.py` → `s09b_closed_edges_sheet.out`. A field Bz in x ∈ [−5, 5], y ∈ [5, 15]
(1.5 h/e); an electron at (12, 10) moving along +x crosses the face x = 30 → −30 and stops near x = −24: it never
enters the field. Closed edges: without the field ⟨y⟩ = 10.000, ⟨v_y⟩ = 0.0000; with it ⟨y⟩ = 7.592,
⟨v_y⟩ = −0.748/unit time — the kick q ΔA_y of A_y = B g(y) F(x) dropping from B W g(y) to 0 at the face (a field
sheet of flux −Φ, which the torus needs for zero net flux). With open edges the packet is absorbed first
(⟨v_y⟩ = −0.009 of the 4 % left). `s09_closed_edges_gauge.out`: across the y-face the same gauge only twists the
boundary condition (no density change for a packet that does not meet itself), and a flux tube's x-dependent twist
gives a small effect (1.5e-6) — the strong case is the x-face.

**Fix.** Refuse (with the reason) a charged particle next to a vector potential whose line integral across the window
does not vanish unless absorbing layers cover the faces it reaches (both the Landau field — confined or over the whole
window — and the flux tube); in p02 disable charged particles with `bfield`/`flux` in a closed world or say why.
State it in the approximations shown in the run.

## Q3 (error) — a live change of B while a charged packet flies: a gauge-dependent kick, not flagged

**Location.** `scene.py:50-53` (docstring: "the impulse of the induced field −dA/dt in this gauge ... gauge-dependent
in the Landau strip"), `scene.py:709-737` (Landau gauge: reference at the region's `lo` edge or at `center`),
`scene.py:1219-1255` (`_commit` keeps ψ); the wrapper's inspector `viz.py:435-449` (`on_set` → `qs.update`) and
README `visualizations/p02_quantum/README.md:74` ("place packets after fields"); `_approx()` `viz.py:823-840` does
not mention it.

**Evidence.** `s15_live_field_change.py` → `s15_live_field_change.out`. The cyclotron preset (Bz = 100 T over the whole
window, A_y = B x) and the same field as a 76 × 76 nm region centred at 0 (A_y = B (x + 38) inside) give the same
orbit (difference 2.8e-14 nm). At t ≈ T/4 the inspector sets Bz = 50 T; half a period later the two electrons are
29.1 nm apart (kick difference q ΔB · 38 nm = 2.89/nm against k = 1.57/nm). The kick is not limited to the Landau
strip (as the docstring says): it is −q ΔA everywhere in a gauge whose reference is an implementation detail, and
the Landau form has ∇·A ≠ 0 at the region's edges, i.e. it corresponds to an induced field with sources, which a
magnet does not produce. The README states the effect, but the run (the playground's main interaction: changing a
field in the inspector) neither refuses nor flags it.

**Fix.** Make the switching impulse physical and explicit: transform ψ at the change with the gauge function that
turns the scene's ΔA into the Coulomb (symmetric) gauge about the region's centre — the induced field of a magnet
centred there (Faraday) — and state that geometry; or refuse a change of a field's A while a charged particle is in
the window, or at least emit an event and an approximation line ("a field changed while a charged particle flies:
the induced impulse depends on the magnet, modelled as ...").

## Q4 (error) — the grid's resolution is checked only for the initial packet

**Location.** `scene.py:1308-1311` (packet admission only), `scene.py:1599-1601` (measurement: σ ≥ max d, a rule for
the outcome density, not for the post-measurement wave), `scene.py:1838-1844` (`spectral_tail`); the wrapper reports
it as information (`viz.py:743-746`), the action's minimum is d (`viz.py:852-853`), `_tune_dt` already computes the
largest local kinetic energy (`viz.py:466-481`) but not the matching wavenumber.

**Evidence.** `s18_well_resolution.py` → `s18_well_resolution.out`: the tunnel preset's electron (k d = 0.98) with a
−3 eV well 4 nm wide (local k d = 3.0): the probability past the well at t = 14 is 0.92337 on the preset's grid and
0.99730 on a grid twice as fine (same dt): a 7.4 % error, while the only signal is the information check
(probability in the outer third of k-space 0.251, against 4.5e-6 on the finer grid). The scene admits the well, the
wrapper shortens dt for it (2^-9) but does not check the grid. `s10_measure_resolution.py` → `.out`: a measurement
at σ = d leaves a wave whose width (0.31 nm) fails the scene's own packet rule (outer-third tail 1.3e-2 against
4.5e-17 before); at σ = 2 d the tail is 7.3e-6 and the rule holds.

**Fix.** Apply the admission rule to the local wavenumber, not only the free one: refuse a well/step change (and a
packet) for which sqrt(2 m E_max) + 6σ_k > π/d, with the E_max that `_tune_dt` already computes (kinetic plus the
convertible potential energy); make the grid check pass/fail with a threshold derived from the same rule (the admitted
packet has |φ|² ≤ 1.5e-8 of its peak at π/d); require for a measurement the σ whose post-measurement width passes the
packet rule (σ_post ≥ 3/(π/d − |k|)), and re-run `_tune` after an action.

## Q5 (should-fix) — Bohm hits are discarded after a localization jump

**Location.** `viz.py:548-551` (`_bohm_step`: `snaps is None` → `_seed_bohm`) and `viz.py:508-521` (`_seed_bohm`
creates `{"X": n new points, "hits": []}`).

**Evidence.** `s06_bohm_reseed_after_jump.py` → `.out` (`_seed_bohm` traced): the double-slit preset with 300 Bohm
points and an environment (20/ps): at the jump (t = 16.625) the absorbed probability is 0.5208 and 187 points have
been registered; after it the hits are 0 and all 300 points are re-drawn into the in-flight wave of norm 0.4792.
The engine keeps the absorbed probabilities across a jump (it acts on the in-flight branch), so from then on the
Bohm counts shown («Бом: зарегистрировал ... k из n», «в полёте») contradict the absorbed probabilities next to them.
(After a position measurement the full re-seed is right: the outcome conditions on "not absorbed".)

**Fix.** On a jump keep `hits` and re-draw only the points still in flight (their number unchanged) from |ψ|²/N;
keep the full re-seed for a position outcome.

## Q6 (should-fix) — a strong environment is refused instead of shortening the step

**Location.** `viz.py:409-422` (`on_add`: `qs.add` before `_tune`), `viz.py:435-449` (`on_set`), `viz.py:482-484`
(`_tune_dt` would set dt ≤ 0.05/λ); README `p02_quantum/README.md:42-43` ("The environment's bound λ·dt ≤ 0.05 is
kept").

**Evidence.** `s17_env_rate.py` → `.out`: in the tunnel preset an environment of 1000/ps (λ dt = 0.0675) is refused
with «уменьшите шаг по времени до 0.00579» — a step the playground offers no control for — both when added and when
changed from 10/ps. `s17b_env_neutron.py` → `.out`: with a neutron (λ = 2 nm: dt = 16 units = 138 fs) the palette's
default environment (10/ps, λ dt = 1.38) is refused.

**Fix.** Compute the environment's bound before handing it to the scene (set dt = 2^⌊log2 min(dt, 0.05/λ)⌋ first,
then add/update), as `_tune_dt` intends.

## Q7 (should-fix) — the companion's accumulated error is an estimate, not a bound

**Location.** `scene.py:1772-1795` (`step_error`: local estimates combined by a trapezoid over the steps since the
last estimate); the wrapper calls it only with the running checks (`viz.py:706`, every `CHECK_FRAMES` = 20 frames at
20 fps, `playground.py:71`, `sim.py:151`), i.e. once per wall second whatever the playback speed; the energy check
(pass/fail, `viz.py:719-724`) uses it. Wording: README `p02_quantum/README.md:53` ("the rigorous bound"),
`test_quantum_scene.py:508`, STATUS V39 (c) ("rigorous but loose").

**Evidence.** `s19_companion_sampling.py` → `.out` (double-slit preset, true error from a Richardson reference):
true global error at t = 12: 2.55e-4; accumulated estimate with estimates every 0.25 and 2.55 units (default speed):
3.75e-3, 3.74e-3; every 25.5 units (10× speed: only at the start and the end, the wall interaction falls between):
7.9e-5 — three times below the true error. In the other direction it is very loose with high walls
(`s07b_dt_high_wall.out`: 2.1e-2 and 0.21 against true 6.0e-4 and 1.1e-3 for 30 and 300 eV walls).

**Fix.** Take the local estimate on a schedule in scene steps (e.g. every K steps, independent of frames and speed),
or bound the integrand between estimates; call it a leading-order estimate, and the energy bound "a bound given
that estimate".

## Q8 (should-fix) — the edges' reflection check shows normal incidence only

**Location.** `viz.py:751-759` (`edgeR`: `qs.edge_reflection([|k|])`), `viz.py:374-398` (`_auto_W` over normal
incidence of |k|, |k| ± 2σ_k); README `p02_quantum/README.md:46-47` ("edges 4·10⁻⁷ (plane) and 1.3·10⁻⁴ (volume)"),
the run's approximation line «их отражение для каждой частицы — в проверках» (`viz.py:831`).

**Evidence.** `s08_absorbers.py` → `.out`: the numbers 4.0e-7 and 1.3e-4 are reproduced at normal incidence; the same
layers reflect 8.1e-4 / 6.6e-2 at 60°, 8.2e-2 / 0.28 at 75° (plane / volume preset), and the worst over the
packet's own normal waves is 6.4e-3 in the volume. `s14_ball3d_edges.py` → `.out`: the 3-D preset against the same
scene in a 60-nm window (same grid step): the probability inside |x_i| < 14 nm at t = 18 is 1.86e-3 against 9.1e-4,
at t = 22 5.7e-4 against 3.0e-5 — about 1e-3 of the wave comes back from the faces, ~10× the number shown.

**Fix.** Report a flux-weighted average of R over incidence angles (or R at, say, 60° next to normal), choose W₀
against it, and say "normal incidence" in the README's numbers; for 3-D, consider wider layers (the preset's are
4 nm, one λ-and-a-third).

## Q9 (should-fix) — the which-path preset does not erase the interference

**Location.** `viz.py:81-90` (preset «Метка пути в одной щели: интерференция гаснет»: a 3 × 3 nm marker at the upper
slit, 0.18 rad/fs).

**Evidence.** `s21_which_path.py` → `.out`: fringe visibility near the centre 0.613 with the marker, 0.953 without.
`s21c_marker_one_slit.out`: with only the marked slit open the transmitted wave's marker P(1) = 0.551 (≈ 48°),
coherence 0.399, and the slit transmits 0.0658 against 0.0817 for the unmarked one. `s21b_marker_1d.out`: as a 1-D
slab the same marker turns by 86° (P(1) = 0.995; 80° for the slit's longitudinal k). `s21d_marker_no_wall.out`:
without the wall the 3 × 3 nm box gives P(1) = 0.486 behind its centre, the same marker as a slab uniform in y 0.986 —
a marker region comparable to λ = 2 nm acts on |±y⟩ as a ±0.118 eV lens (the marker's coupling is 31 % of the
electron's energy), so the components diffract differently and the record is partial. The engine's marker is right
(its slab test and this slab reproduce the transfer matrices); the preset's parameters do not do what its label says.

**Fix.** Use a marker that is long along the beam and wider than it (e.g. a slab across the upper half-plane behind
the wall, or a longer region with a smaller rate, c ≪ E), check in the run the measured visibility against
|⟨m₁|m₂⟩| of the two paths' marker states, and word the label by what the run shows.

## Q10 (nit) — the Aharonov–Bohm preset's tube is behind the wall, in the beams' overlap

**Location.** `viz.py:91-100` (tube at (4, 0) nm, R = 1 nm; the wall spans x ∈ [−1, 1]).

**Evidence.** `s02_ab_preset.py` → `.out` (+ `s02_ab_profiles.npz`): the screen's pattern against the ideal two-path
half shift 2(S₁ + S₂) − P₀ built from single-slit runs: the shift holds (central minimum 0.0003 of the peak) to 5.6 %
of the peak, asymmetric (y = −8.12: 0.720 vs 0.667; +8.12: 0.659); the field felt is small (∫∫(B/Φ)|ψ|² dt = 4e-4)
— the deviation is the AB scattering of waves passing on both sides of the tube within one beam. The label says
«между щелями».

**Fix.** Put the tube inside a wall thick enough to hold it (as `test_aharonov_bohm_shift_of_the_fringes`: R = 0.25 in
a 1.6 nm wall), or say "behind the wall" and expect a few per cent from paths on both sides.

## Q11 (nit) — numbers in README / STATUS not reproduced as stated

**Location.** `p02_quantum/README.md:40-42`, STATUS V39 (d); `p02_quantum/README.md:46-48`.

**Evidence.** `s07_dt_choice.out`: the engine's `suggest_dt` rounded to a power of two as the wrapper rounds is 4×
smaller, not 8× (5.5× unrounded); the true global error at t = 12 is 2.55e-4 (wrapper) against 1.59e-5 (4× steps),
the companion's estimates 3.75e-3 against 2.35e-4 — neither pair is "1.0·10⁻³ → 6·10⁻⁵". (The argument itself
holds — `s07b`: a 30 eV and a 300 eV wall raise the true error only to 6.0e-4 and 1.1e-3 at the same dt.)
`s08b_screen.out`: the screen's "10⁻¹¹" is R at the fastest wave only; over the packet's waves R reaches 7.2e-8 and
the leak 1.85e-5; with a 1 nm edge (the same W₀ = 0.381 eV, which the preset keeps from its "no particles" default)
R ≤ 3.0e-3, not 1.6 %.

**Fix.** Replace by the reproduced numbers and state what each one is (true vs estimated error; worst over the waves).

## Q12 (nit) — stale snapshots after a measurement

**Location.** `scene.py:1561-1564` (docstring: None "when a jump or a measurement broke the interval"),
`scene.py:1628` (`measure` sets `snap_ok = False`, which the next `advance` overwrites, and leaves `p.snaps`).

**Evidence.** `s20_small_checks.out` (a): after `measure` `snapshots()` returns the pre-measurement interval (the same
object). The wrapper is not affected (it consumes snapshots right after `advance`), a library user is.

**Fix.** `p.snaps = None` in `measure`, `set_wave`, `replace_particle` and `_commit`.

## Q13 (nit) — the energy reference's time

**Location.** `scene.py:1392-1394` (`_reset_refs`: `t_ref = now`, `E_ref = None`), `scene.py:1820-1825` (E_ref taken
at the first `checks()`); `viz.py:723` («с t = ... с»).

**Evidence.** `s20_small_checks.out` (b): a change at t = 0, first check at t = 3.00: `since` = 0.0, but E_ref is
the energy at t = 3.00 (drift 0 by construction).

**Fix.** Store `t_ref` when E_ref is taken (or compute E_ref at the change).

## Q14 (nit) — shapes thinner than their edge; a field label

**Location.** `scene.py:441-478` (`Ball`), `scene.py:405-438` (`Box`), checks of size against edge absent;
`viz.py:192` (label «Bx = −g·x, By = B_y + g·y»).

**Evidence.** `s20_small_checks.out` (c): a ball of R = 0.5 nm with a 1 nm edge peaks at 0.90 of its height and has a
cone at its centre (|dV/dr| = 0.45 height/nm); R = 0.25: 0.74. `s01_tunnel_preset.out`: the tunnel preset's barrier
(1.5 nm, edge 0.995 nm) peaks at 0.473 eV, not 0.5 eV. The field is B = B0 + G (r − c) with c the region's centre
(`viz.py:324-329`), the label drops B0_x and c.

**Fix.** Show the actual peak in the inspector (or refuse sizes below ~2 edges), and write the field as
B_x = B_x0 − g (x − x_c), B_y = B_y0 + g (y − y_c).

## Q15 (nit) — tests that do not test, and untested parts

**Location / evidence.**
* `test_norm_plus_absorbed_is_one_and_detectors_share_it` (`test_quantum_scene.py:239-257`): the negative control
  (leaving one detector out of a sum breaks the sum) cannot fail; the attribution itself (W_k / W_tot per point) has
  no independent check.
* The localization unravelling together with a detector (the loss split W_k : Γ/2, the hazard ln((n₀ − ΔA)/n₁),
  verification file §3 (b)) is tested only by the balance. Reproduced here against the master equation with −iW in
  H_eff (`s11_jumps_with_detector.py` → `.out`): 12 z-scores (norm, P_left, x², cos 5x, cat fidelity, absorbed) max
  1.39; a reference with 0.7 W is rejected (max |z| 18.4) — correct, worth keeping as a test.
* `bohm._Patches.sample` in 3-D (the other half of the B6 fix, used whenever ≤ 64 points remain) has no test.
  Reproduced (`s12_bohm_3d_patches.out`): patches = device path to 4.4e-16, a spinor through the patches too.
* p02's Bohm test counts points only (Q1).

**Fix.** Add `s11` and `s12` as tests; replace the negative control by one that breaks the attribution (e.g.
attribute by W_k alone without W_tot) and compare per-detector shares with ∫2W_k|ψ|² dt summed per step.

---

## Verified without a finding

* **Sources** [useful] (`v01_sources.out`): Jacobs & Steck eq. (22) (A(α) = (4kΔt/π)^{1/4} ∫ e^{−2kΔt(x−α)²}|x⟩⟨x|dx:
  with 2kΔt = 1/(4s²) this is the scene's K_x), Bassi et al. eqs. (17), (18), (22) and "Poissonian process", Castin
  et al. eqs. (4), (8), (10), (11) and its publication line ("Published in AIP Conference Proceedings 275"), Plenio &
  Knight eqs. (30), (66), (67) and "just the delay function", Paiva et al. ("relative phase φAB = qΦB/ħ"), Planelles
  et al. ("Φ0 = 2πħ/|e| the flux unit") are in the texts as quoted. The derivations I re-did agree: K(r, r′) and Γ for
  a region (completing the square), the jump density |ψ|² ∗ N(0, a²/2), the post-measurement width
  (1/s₀² + 1/s²)^{−1/2}, the Landau gauge's curl, the Euler–Maclaurin end term, the companion's 4/3.
* **Units** [useful]: TU = m_e nm²/ħ = 8.64 fs, ħ²/(m_e nm²) = 0.0762 eV, ħ/(e nm²) = 658 T, the marker's rad/fs →
  c, λ in 1/ps, flux in h/e → 2π, ħω in meV → ω; −μ_e B equals the Pauli coupling with |g_e|.
* **Tunnelling preset** [useful] (`s01`): the run's transmitted probability 0.13213 against 0.13214 from transfer
  matrices of the same profile over the packet's spectrum; 89 % of it from E_x below the barrier's top — it is a
  tunnelling demonstration.
* **Time step ignoring barriers above E** [useful] (`s07`, `s07b`): sound for walls — the true error grows from
  2.6e-4 to 1.1e-3 when the wall rises 100× at the same dt.
* **Bohm interval of 8 steps** [useful] (`s16`): near the 3 eV and a 30 eV wall the 8-step and 2-step intervals give
  trajectories within 0.07 nm (none above 0.5 nm of 300).
* **Bohm hits at the presets' k d** [neutral] (`s05`): the screen's fraction 67/300 against its probability 0.1844
  (z = +1.74); the hits' y against the screen's record: KS 0.114 < 0.238.
* **Joint jumps + detector** [useful] (`s11`, see Q15); **3-D patches** [useful] (`s12`).
* **GPU 0 = CPU** [useful] (`s13_gpu.out`): the engine test's scene for 400 steps: waves within 2e-14, the same jump
  time, the same absorbed probabilities, balance 2.4e-15 on the GPU; 3-D `sample` on the device 2.6e-15; 3-D Bohm
  points (patches and device path) 5e-15; the wrapper's double slit with its 60 Bohm points to t = 20: wave 6.5e-15,
  points 1.7e-12 nm, the same 59 hits.
* **The batch's tests** [neutral] (`t01_tests.out`): engine 36 passed, 1 skipped (GPU, covered by `s13`); p02 15 passed.
* **Layers** [neutral]: `core.quantum.scene` imports only the core; Bohm stays in `theories.interpretations` and is
  listed by the wrapper; the localization is presented as an environment model (not GRW collapse), the marker as a
  detector model — both admissible in the core.
