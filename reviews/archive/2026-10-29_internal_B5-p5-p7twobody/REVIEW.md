# Review B5 (internal): P5 open quantum systems and P7 two-body GR and gravitational waves

**Status: awaiting processing.** The reviewer does not process this review (`../README.md`, owner 2026-10-15).

* Delivered: 2026-10-29. Reviewer: internal, an independent Claude Opus subagent (not the author of B5).
* Scope (as assigned): P5 — `lfphys/core/quantum/open_systems.py`, `two_level.py`, `jumps.py`, `decoherence.py`,
  `lfphys/theories/alternatives/collapse_baseline.py`, `tests/test_open_systems.py`,
  `tests/external/test_ext_open_qutip.py` (+ its rows in `tests/external/RESULTS.md`),
  `sources/verification_2026-10-29_p5.md`. P7 two-body half — `lfphys/core/gravity/pn_binary.py`, `gw_quadrupole.py`,
  `lfphys/theories/approx/peters_mathews.py`, the PSR B1913+16 constants of `lfphys/core/data.py`,
  `tests/test_pn_binary.py`, `test_gw_quadrupole.py`, `test_peters_mathews.py`,
  `sources/verification_2026-10-29_p7.md`. Not in scope: the Kerr half of P7, P14.3 / v15 (other reviewers).
* Environment: Docker only, engine mounted read-only. Runtime image `light-funnel-viz:latest` (959a1b91570e: Python
  3.11.17, numpy 2.4.6, scipy 1.17.1, mpmath 1.3.0); comparison image `light-funnel-ext:latest` (428f06b70151, QuTiP
  5.3.1). CPU only. Run any check from this folder: `sh scripts/run.sh sNN_name.py` (writes `out/sNN_name.txt`);
  sources: `sh scripts/s00_sources.sh <empty dir>` (fetches the arXiv texts and Steck's notes with no contact
  parameter, writes the quoted passages to `out/00_quotes.txt`). Negative controls mutate a copy of the engine inside
  the container (`/tmp/mut`); nothing in the repository was changed.

## Summary

The physics of both items is right where I could check it against the sources: every coefficient of the PN equations
of motion (1PN, 2PN, 2.5PN, 3.5PN), the conserved 2PN E and J, the gauge-invariant references, the quadrupole
waveforms and fluxes, Peters–Mathews, the post-Keplerian formulas, the Lindblad form, the optical Bloch equations and
their steady state, Torrey's forms, the waiting-time law, Magnus-4, the GRW term and the decoherence rates; and the
PSR B1913+16 numbers are quoted correctly. All 109 in-scope engine tests and all 93 QuTiP comparison tests pass on
re-run. P5 is clean of errors; its error estimates are honest on harder problems than the tests use.

The problems are in P7's **initial data** and in **test power**:

| ID | sev. | where | one line |
|---|---|---|---|
| E1 | **error** | `pn_binary.state_from_invariants` | Newton without damping or convergence check: for ordinary inputs (eps = 0.01, j = 0.5, r_p ≈ 29 Gm/c²) it returns r_p = 3.3e36 with eps = −0.009, j = −8.5e68 and no error; on a 12 × 13 grid 9 cells garbage, 20 an apoapsis instead of the periapsis, 31 refused inside the PN domain |
| S1 | should-fix | `pn_binary.circular_state(quasi=True)` | the Eq. (227a) radial velocity does not match the engine's own inspiral in strong field: at r0 = 10 the "quasi-circular" start is *more* eccentric (2.6e-3) than a plain circular one (1.9e-3); at r0 = 12, 8.5e-4 where 1.5e-5 is reachable |
| S2 | should-fix | `tests/test_pn_binary.py` | the 3.5PN coefficients are tested only through orbit averages and the circular limit: 4 of 6 single-coefficient mutations pass all tests; also the 1PN coefficient of Eq. (227a) |
| S3 | should-fix | `open_systems.evolve` | cost ∝ ‖𝓛‖·span for stiff generators (the step guard h‖𝓛‖_F ≤ 1 binds, not the error): Γ = 1e4 over 10 time units takes 2 min and 351 k step attempts; Γ ≳ 1e5 exceeds `max_steps`; not stated anywhere |
| S4 | should-fix | `open_systems.evolve`, `propagate`, `jumps.trajectories` | unsorted or negative times accepted silently; `evolve` then labels the t = 2 state as t = 1 with err = 6e-14 (true error 0.35) |
| S5 | should-fix (doc) | `jumps.Trajectories.stderr` | the sample standard error is meaningless for rare-event observables: Λ system, t = 40: stderr 2.3e-9, true error 1.4e-6 (z = 592) |
| S6 | should-fix | `pn_binary.state_from_invariants` | j ≤ 1 excludes the low-eccentricity PN orbits: at eps = 0.01 nothing below e ≈ 0.156; the docstring says "slightly above 1" |
| N1–N12 | nit | various | silent NaN of `circular_speed`; plunges without `r_stop`; a test docstring's "O(x²) ~ 1e-11" (measured 2.4e-10); `binary_waveform` with PN kinematics; Newtonian elements as PN data; weak `n(ε, j)` check; loose tolerances; a docstring restriction; STATUS V33(f) misattributes a CSL feature to GRW; layering of γ; `peters_mathews.evolve` default stop; Cartesian route for B1913 without a warning |

Negative controls (s04): 27 of 32 meaningful mutations are caught (P5: 10 of 10; P7: 17 of 22); the five that pass are
S2's. Reproduced: every finding below was reproduced by a script in `scripts/` with its output in `out/`.

## What was checked and holds

Status tags as in `../../AGENTS.md` §3 rule 11.

* [useful] **Sources against the code** (passages in `out/00_quotes.txt`). Blanchet 2014 (arXiv:1310.1528v3)
  Eq. (219), (220a, b): every 1PN, 2PN, 2.5PN and 3.5PN coefficient of A and B in `pn_binary.coefficients` matches;
  the engine's 3.5PN grouping is exactly Blanchet 2024 (v6) Eqs. (358e), (359e) (B14 groups them differently: the
  sources note "checked by hand" — I confirm it). Eqs. (226), (227a), (228), (232), (345), (346e), (348a, b), (350),
  (358), (359a, b) match the reference functions; I re-derived the 1PN coefficient −1751/336 − 7ν/4 of (227a) from
  (232), (231) and the 1PN flux. Kidder 1995 Eqs. (2.2a, b, d, f), (2.7a, b, d), (2.9b, d) match `_kidder_a`,
  `energy`, `angular_momentum`; Kidder's a_RR is the Iyer–Will (α, β) = (4, 5) member and B14's harmonic term is
  (−1, 0), as the sources say (checked against the family's form as I recall it — not fetched; both assignments fit
  every coefficient; and the general-frame 2.5PN term of B14 Eq. (203) reduces to the engine's relative term to
  1e-15 at 200 random states and mass ratios, s14). Sec. 9.4 of B14: (N, P, Q) right-handed, P toward
  the node where the bodies move toward the observer — `observer_triad` follows it; (322a), (323a) reproduced by hand.
  Eqs. (2)–(5), (10)–(13) as quoted. Steck rev. 0.16.11 (5.25)–(5.27), (5.124), (5.126), (5.127), (5.132), (5.133),
  (5.556); Castin–Dalibard–Mølmer (2), (4); Plenio & Knight (30), (66), (67); Manzano (92), (93) (the typo L L† in
  (93) is real), (101) and Evans' theorem; Blanes et al. (252)–(254); Bassi et al. (19), (21), (22) and the N λ_GRW
  sentence; Hornberger (5.170), (5.171) and F(∞) = ⟨σ v n_gas⟩; QuTiP 5.3.1's `mcsolve` draws a target norm and
  collapses when ‖ψ‖² reaches it (`_find_collapse_time`, read in the image).
* [useful] **PSR B1913+16** (Weisberg & Huang 2016, arXiv:1606.02744v1): Table 2 x = 2.341776(2) s, e = 0.6171340(4),
  P_b = 0.322997448918(3) d, ⟨ω̇⟩ = 4.226585(4) deg/yr, γ printed "(ms) 0.004307(4)", Ṗ_b^obs = −2.423(1)e-12; Sec. 3.1
  T_⊙ = 4.925490947 µs; Sec. 4.1 Ṗ_b^gal = −(0.025 ± 0.004)e-12, Ṗ_b^intr = −(2.398 ± 0.004)e-12, Eq. (15); Sec. 4.3
  Eqs. (16), (17), m1 = 1.438 ± 0.001, m2 = 1.390 ± 0.001, sin i = 0.7327 ± 0.0004; Sec. 5.1 Eq. (22),
  Ṗ_b^GR = (−2.40263 ± 0.00005)e-12, Eq. (23) 0.9983 ± 0.0016. All constants in `core/data.py` lines 74–97 agree; the
  reading of γ in seconds is forced by Eq. (17) (the masses), as the module says. Eqs. (19) (ė^GW) and (16)–(17) are
  the formulas of `peters_mathews`.
* [useful] **Re-runs.** 109 in-scope tests pass (`out/00_engine_tests.txt`); `test_ext_open_qutip.py` 93 passed
  (`out/07_ext_open_qutip.txt`); `test_layers.py`, `test_boundary.py` 149 passed (`out/08_layers_boundary.txt`).
* [useful] **P5 on harder cases** (s01–s03). Adaptive Magnus on a strong linear drive (Ω = 0.8 ω0, counter-rotating
  terms, damped), a damped Landau–Zener sweep and a 4-level random generator with a two-tone drive: measured
  trace-norm error / returned estimate ≤ 0.30 at tol 1e-6…1e-11 against a Richardson-extrapolated fixed-step reference
  self-consistent to 5e-14. `expm_error_bound` respected on stiff (Γ = 1e4), long (t = 1e4) and d = 8 cases (ratios
  2e-6 … 7e-3). `steady_state`'s Wedin bound respected down to s_next/s_max = 7e-12 (error 2.2e-6 ≤ bound 1.6e-3);
  thermal ladders N = 20, 30 exact to 1e-14. Jumps: tens of jumps inside one output interval (thermal oscillator, two
  channels, 77 per trajectory over two intervals), a dark-state Λ system (P_g1), Γ·dt = 3000 (norm underflow inside the interval), H_eff near its exceptional point on
  the `eig` route (cond(V) 2.2e2) and output grids of 2, 5, 401 points all agree with the master equation / closed
  forms within 5σ or the DKW bound.
* [useful] **P7 on harder cases** (s05–s08). Cartesian vs elements routes agree to 8e-11 … 8e-9 of r_apo after three
  periods in strong field (r_p = 8 … 10, e up to 0.95, ν = 1e-3 … 0.25). `averaged_dissipation` (Newton + 2.5PN)
  equals Peters–Mathews to 5e-12 at e = 0.99. `coalescence_time` equals a 30-digit quadrature to 1e-12 up to
  e0 = 0.9999; `evolve` keeps c0 of a(e) to 1e-12 and t + T_rest to 5e-11 down to a = 1e-3 a0, and resolves e = 1e-10
  to 6e-12. For B1913+16 the elements route gives Peters–Mathews to 6e-12; the Cartesian route is 96 % off, exactly
  as the docstring warns.
* [neutral] STATUS V34(f) (2PN term of ω̇ shifts Ṗ_b^GR by ~3σ of its published uncertainty): my estimate with
  Damour–Schäfer's f0 as I recall it (not fetched: Δω̇/ω̇ = f0 β0² = 10.8 × 2.14e-6 = 2.3e-5, mass shift −3.5e-5)
  agrees in size with the STATUS numbers; both remain hypotheses until checked against the timing literature.

## Findings

Lengths in the P7 findings are in units of G m/c² (m the total mass), as in `pn_binary`, unless SI is stated.

### E1 (error, reproduced) — `state_from_invariants` returns diverged states without an error

*Location.* `lfphys/core/gravity/pn_binary.py:352–383` (Newton loop 369–380; the only check, 381, is r_p > 0 and
v_p > 0).

*What is wrong.* The solve for the periapsis state with prescribed gauge-invariant (ε, j) is an undamped Newton
iteration started from the Newtonian periapsis, with no test that it converged. For eccentric orbits the 1PN + 2PN
energy at the periapsis is comparable with the binding energy itself, so the start is far from the root in the
normalised residual: for ε = 0.01, j = 0.5, ν = 0.25 the start has F = (−0.857, −0.819) and the first Newton step
takes r_p from 29.3 to −14.3 (s10b, iterate by iterate). After 60 iterations the function returns whatever iterate it
has:

    state_from_invariants(0.01, 0.5, 0.25) -> r_p = 3.273e36, and its invariants eps = -8.9e-3, j = -8.5e68

On a grid ε ∈ [1e-4, 0.05] × j ∈ [0.05, 1] (156 cells, ν = 0.25; s10): 96 correct, **9 silently wrong** (r_p ~ 1e34 …
1e37: ε = 0.01, j = 0.4 and 0.5; ε = 0.02, j = 0.6; ε = 0.03, j = 0.1, 0.2, 0.7, 1.0; ε = 0.05, j = 0.2, 0.4),
**20 apoapsis states** returned as "the periapsis state" (e.g. ε = 1e-3, j = 0.05; every ε ≤ 3e-3 at j = 1), and 31
refused with "no periapsis state found … outside the PN domain" although they are inside it (e.g. ε = 0.015, j = 0.5:
r_p ≈ 20; ε = 3e-4, j = 0.1). ν = 0.1 and 0.01: 6 silent failures each. The tests only use ε ≤ 4e-3 and
j ∈ {0.5, 0.75, 0.95}, where it works.

*Effect.* A researcher who sets up an orbit by its invariants (one of the three documented ways, and the only one
that fixes the PN orbit itself; `periapsis_state`'s Newtonian elements are far from the PN orbit, N5) gets a state
1e36 away, or an apoapsis, or a false "outside the PN
domain". Anything downstream (`integrate`, `averaged_dissipation` — which then raises "unbound orbit") is wrong or
fails far from the cause.

*Fix.* (1) After the loop, require |F| ≤ a few u and raise otherwise; (2) globalise the solve: the targets decouple,
E = −ε/2 and J = sqrt(j/ε) (j = εJ² in these units), so either a damped Newton that keeps r_p, v_p > 0 and decreases
|F|, or continuation in ε from a small ε (the reviewer's prototype `scripts/s10c_continuation_prototype.py`: damped
Newton + continuation + convergence check reaches the periapsis on 127 of 156 cells, raises on 22 and lands on the
apoapsis on 7, hence (3)); (3) a converged turning point may be the apoapsis (same invariants): test x·a + v² > 0
and otherwise integrate the conservative orbit to the next periapsis; (4) a test over a grid of (ε, j, ν) up to ε = 0.05 that asserts the
invariants to 1e-12 and the periapsis property. Correct the "outside the PN domain" message.

### S1 (should-fix, reproduced) — the quasi-circular start of `circular_state` is inconsistent with the engine's own inspiral in strong field

*Location.* `pn_binary.py:401–408` (uses `circular_inspiral_rate`, 282–286, Blanchet Eq. (227a)); docstring: "which
suppresses the eccentricity a purely circular start would get".

*What is wrong.* Eq. (227a) is the re-expanded 1PN-corrected rate, 1 + γ(−1751/336 − 7ν/4); at r = 10 the bracket is
0.43 and the truncation is poor. Scanning the initial radial velocity vr = k · vr_227a and measuring the residual
radial oscillation over three orbits (ν = 0.25, s05b):

| r0 | vr = 0 | k = 1 (engine) | best k | residual at best k |
|---|---|---|---|---|
| 40 | 3.6e-4 | 3.7e-6 | 0.990 | 2.6e-7 |
| 20 | 1.8e-3 | 9.7e-5 | 0.950 | 7.3e-6 |
| 12 | 2.5e-3 | 8.5e-4 | 0.750 | 1.5e-5 |
| 10 | 1.9e-3 | **2.6e-3** | 0.420 | 2.5e-5 |

So at r0 = 10 the "quasi-circular" start is more eccentric than no radial velocity at all, and at r0 = 12 it is 60×
above what the equations allow. This is the regime of a late inspiral, where a waveform visualization would start.

*Fix.* Use the engine's own adiabatic rate: vr = (∂E_2PN/∂v · a_RR) / (dE_circ/dr), with a_RR the 2.5 + 3.5PN
perturbation at the circular state (complex step, as in `averaged_dissipation`) and E_circ(r) the 2PN energy along
`circular_speed` (s05c): k = 0.991, 0.956, 0.794, 0.49 at r0 = 40, 20, 12, 10 against the optimal 0.990, 0.950,
0.750, 0.42; one eccentricity-reduction iteration (measure the oscillation, correct vr) would close the rest. State
the residual eccentricity in the docstring and test the start at r0 = 12–15.

### S2 (should-fix, reproduced) — the 3.5PN coefficients and the 1PN coefficient of Eq. (227a) are not pinned by any test

*Location.* `tests/test_pn_binary.py`: the 3.5PN terms (`pn_binary.py:127–137`) are tested only by
`test_circular_radiation_reaction_matches_eq_226` (ṙ = 0: the A₃.₅ terms, all ∝ ṙ, vanish) and
`test_reaction_at_3p5pn_gives_the_1pn_eccentric_flux` (an orbit average whose acceptance is a halving ratio in
[0.2, 0.7]); `circular_inspiral_rate` only by the inspiral test's ratios.

*What is wrong.* Single-coefficient mutations that pass every in-scope test (s04): A₃.₅ 112 ṙ⁴ → 113; 3956/35 →
3946/35; 184ν/5 → 180ν/5; B₃.₅ (678/5 + 12ν/5) → (678/5 + 13ν/5); and (227a) −1751/336 → −1700/336. Their effect
(s04b): the orbit-averaged loss of E_2PN changes by 8e-7 … 7e-5 at ε = 1e-3 … 1e-2 (up to 4e-4 of its 3.5PN part),
the inspiral 20 → 10 by ≤ 2e-7. Small, but these are wrong coefficients the suite cannot see; and an error that
amounts to a change of gauge at 3.5PN (a total time derivative in the energy balance) leaves every orbit average
unchanged by construction, while the module claims the harmonic gauge. The coefficients themselves are right (checked against
B14 Eq. (220) and B24 Eqs. (358e), (359e)).

*Fix.* A second-transcription test as for 2PN with Kidder: type B14 Eq. (220a, b)'s 1/c⁷ terms in B14's grouping
(different from the engine's B24 grouping) and compare at random states to rounding; and derive (227a)'s 1PN
coefficient in a test from E(x) (Eq. (232)), γ(x) (Eq. (231)) and the 1PN circular flux (it follows exactly:
dx/dt = (64/5)νx⁵[1 + x(−743/336 − 11ν/4)], then ṙ = −(64/5)νγ³[1 + γ(−1751/336 − 7ν/4)]).

### S3 (should-fix, reproduced) — `evolve` is impractical for stiff generators, and this is not stated

*Location.* `open_systems.py:342–346` (the guard h·max‖A_i‖_F ≤ 1), 357–358 (growth ×4 after an accepted step),
docstring line 41, `ABOUT["validity"]`, STATUS V33.

*What is wrong.* The guard applies to the whole generator, including a constant stiff dissipator for which the
exponential in the Magnus step is exact anyway. For a two-level atom with Γ ≫ drive (Ω(t) = cos(0.1 t), span 10,
tol 1e-8; s01): Γ = 1e2: 1753 accepted steps, 1 s; Γ = 1e3: 17 570 accepted + 17 567 rejected, 11 s; Γ = 1e4:
175 684 + 175 681, 123 s, h_max = 0.57/Γ — the error control never binds; Γ ≳ 1e5 needs ~1.7e6 steps and raises
"too many steps". Every second attempt is a guard rejection right after the step was grown ×4. A Rb atom (Γ ≈ 3.8e7
1/s) driven by a 1 ms adiabatic passage is Γ·span ≈ 4e4: minutes, near the step limit. The validity says only "4th
order, error ≤ tol".

*Fix.* State the cost (∝ ‖𝓛‖_F · span) in `validity` and STATUS V33; better, apply the convergence guard to the
time-dependent part only (e.g. the Magnus step in the interaction picture of the constant part 𝓛_c, or the guard on
‖A_i − 𝓛_c‖), leaving accuracy to the step doubling; at least cap the post-acceptance growth at 0.9/‖A‖ so that half
of the attempts are not rejections.

### S4 (should-fix, reproduced) — unsorted or negative times are accepted and give wrong results with confident errors

*Location.* `open_systems.py:293–364` (`evolve`), 184–205 (`propagate`); `jumps.py:173–241` (`trajectories`). The
docstrings say "increasing" but nothing checks it.

*What is wrong* (s12). `evolve(H, c, ρ0, [0, 2, 1])` returns three states; the one labelled t = 1 is the t = 2 state
(trace-norm distance to the true ρ(1): 0.35) with **err = 6.2e-14**. `evolve(..., [0, −1])` returns one state for two
requested times. `propagate(𝓛, ρ0, [−3])` returns a matrix with eigenvalue −3.99 (exp(𝓛t) is not CPTP for t < 0).
`trajectories(..., [0, −2])` returns ⟨P_e(−2)⟩ = 0.947 and no jumps.

*Fix.* Validate: finite, non-decreasing times, t ≥ times[0] (and t ≥ 0 for `propagate`); raise ValueError.

### S5 (should-fix, documentation; reproduced) — `Trajectories.stderr` is not an error bar for rare-event observables

*Location.* `jumps.py:24–27` ("unbiased estimates … with standard error s/sqrt(N)"), 79–82.

*What is wrong.* Not an engine error: the estimator is unbiased, but the sample standard error is only meaningful
when many trajectories contribute. A Λ system (Ω1 = 1.1, Ω2 = 0.7, decay 0.6 and 0.9 into g1, g2) pumped into its dark
state: at t = 40 the exact P_e is 1.38e-6, carried by a ~1e-5 fraction of still-bright trajectories; with N = 4000
(s03b) the four seeds give mean (stderr) 2.1e-8 (1.5e-8), 6.6e-8 (4.8e-8), 3.0e-9 (2.3e-9), 1.47e-6 (1.45e-6): z = 93,
28, 592, 0.06. A researcher estimating a small population, a tail or a rare channel from the returned stderr is
misled by orders of magnitude.

*Fix.* Say it in the module docstring and in `stderr`: the CLT error bar needs N·p ≫ 1 contributing trajectories;
for a bounded observable report also the number of trajectories that contribute (or a binomial / Bernstein bound
with the range of A).

### S6 (should-fix, reproduced) — `state_from_invariants` cannot make low-eccentricity PN orbits

*Location.* `pn_binary.py:352–358` ("0 < j ≤ 1 (Newtonian range; PN orbits reach slightly above 1 near circular)").

*What is wrong.* For a PN orbit e_t² ≈ 1 − j + (ε/4)(−8 + 8ν + j(17 − 7ν)) (B14 Eq. (346e)), so j = 1 is an orbit with
e_t ≈ sqrt(ε(9 + ν)/4): every orbit less eccentric is refused. Measured (s05 (b)): ε = 0.01, j = 1: r between 82.9 and
113.7, e ≈ 0.156; ε = 0.005, j = 0.9995: e ≈ 0.11. "Slightly above 1" in j hides "nothing below e ≈ 0.15" at
ε = 0.01 (0.05 at ε = 1e-3, 0.34 at ε = 0.05).

*Fix.* Allow 0 < j ≤ j_circ(ε) (from the 2PN circular sequence, `circular_speed` + `gauge_invariants`), or accept a
time eccentricity e_t instead of j; together with E1.

### Nits

* **N1** (reproduced, s05 (a)) `pn_binary.circular_speed` (`pn_binary.py:386–398`) returns NaN without an error at
  r ≤ 2.5 (ν = 0.25), and never checks that the 200 fixed-point iterations converged. Raise when not converged or
  non-finite. (At r = 3 it returns v = 0.909: inside the documented "series converges poorly" region, fine.)
* **N2** (reproduced, s05 (c2)) A plunging orbit without `r_stop` ends in scipy's "Required step size is less than
  spacing between numbers" RuntimeError (`pn_binary.py:539–540`); a start with r0 < r_stop is not flagged (the stop
  then never fires). Give a physical message (plunge / PN breakdown at r ≈ …) and check r0 > r_stop.
* **N3** (reproduced, s05 (e), s11) `tests/test_peters_mathews.py:234–249`: the docstring says the 1PN flux agrees
  "to O(x²) ~ 1e-11 relative"; measured −2.40e-10 (−52 x²; with the 2PN forms of x(ε, j) and e_t(ε, j), Eqs. (350),
  (351), −7.9e-10: a genuine O(x²) remainder with a large coefficient, not the 1PN truncation of the maps). The
  tolerance 0.01·x I1/I0 = 2.4e-8 is 100× the measurement. State the measured value; a tolerance of ~1e-3 · x I1/I0 would still pass.
* **N4** (reproduced, s07) `gw_quadrupole.binary_waveform` (`gw_quadrupole.py:164–172`) invites passing
  "pn_binary.acceleration and jerk". That is neither the leading-order formula nor the 1PN waveform: face-on amplitude
  relative to 4νx (x = (mΩ)^{2/3}, 2PN circular orbits, ν = 0.25) at r = 10: default −2.6 %, with PN a, j −11.6 %,
  1PN (B14 Eqs. (322c), (323c) at i = 0: factor 1 + x(−13/6 + ν/6)) −20.0 %; at r = 30: −1.3 %, −5.5 %, −6.9 %. Say
  that PN kinematics change the amplitude at O(x) without making it 1PN-accurate.
* **N5** (reproduced, s13) `periapsis_state(a, e)` (`pn_binary.py:345–349`) as PN initial data: the docstring is
  literally right (osculating elements), but the PN orbit can be far from (a, e): ν = 0.25, e = 0.7 is unbound for
  a < 81.8 (r_p < 24.6); e = 0.3, a = 24 gives e_t = 0.58 and half the Newtonian binding energy; even a = 600, e = 0.3
  has 2 % less binding. Warn in the docstring and point to `state_from_invariants` (after E1).
* **N6** (reproduced, s09) The n(ε, j) check of `test_periastron_advance_and_mean_motion_…` (`test_pn_binary.py:142–157`)
  has little power: |D| = |residual|/ε³ of n is 1e2 … 1e4 in five of the six cases (presumably the truncated
  equations' 3PN-order residual, amplified at the periapsis), so a wrong 2PN constant 555 → 556 (a 1/128 ε² error)
  is caught only at (ν, j) = (0.25, 0.95) of the six cases. Add smaller ε or a circular-limit check (K·n against Eq. (353) / x(ε) of Eq. (350)).
* **N7** (reproduced, s02 (a), s04) Tolerances that are derived but far from the measurement, so the tests have
  little power below them: `expm_error_bound` is 1.5e2 … 4e5 × the measured error (d = 8: ratio 2.4e-6); the QuTiP
  lab-frame rows 3.2e-8 for a 3.5e-12 difference (QuTiP's side); `test_secular_decay_matches_peters_orbit_by_orbit`
  tolerance ε_rr where 0.6 ε_rr² is measured (~1e4×); `test_psr_b1913_decay_through_the_equations_of_motion` bound
  100 GM/(c²a) — the 100 is not derived. Not wrong; worth stating per test what it can and cannot detect.
* **N8** `decoherence.py:14`: "V² + D² = 1 for equal weights" — for pure probe states it holds for any weights
  (`probe_visibility`, and the test at w1 = 0.2 asserts it). Drop "for equal weights".
* **N9** STATUS V33 (f) "GRW for objects larger than r_C not modelled": in GRW every constituent is localised
  independently, so a rigid displacement d of N nucleons decoheres at N λ [1 − e^{−d²/4r_C²}] whatever the size;
  Bassi et al. state the N λ_GRW rate for the centre of mass without a size condition ("the collapse rate entering
  the definition of the operator T[·] is NλGRW, with N the total number of particles making up the object"). The size
  dependence is a CSL feature (mass-density coupling). The listed limitation is misattributed; if CSL is meant, say
  CSL.
* **N10** Layering (LAYERS §1: `theories/approx` holds a simplified form of a law the engine *also* has in fuller
  form): the 1PN ⟨ω̇⟩ qualifies (the core has K(ε, j) at 2PN), the Einstein delay γ does not — the engine has no
  fuller pulsar-timing model. Harmless; state it in `peters_mathews.ABOUT` or the README.
* **N11** (reproduced, s06 (d)) `peters_mathews.evolve` stops by default at a = 1e-6 a0 (for a0 = 2e9 m: 2 km, below
  GM/c² = 4 km of a 2.7 M⊙ binary), far past where orbit averaging holds (|da/dt| P_b/a = 0.5 at a = 3e5 m for
  e = 0.9). Return a validity indicator (ε_rr, a/(GM/c²)) or stop by default at a multiple of GM/c².
* **N12** (reproduced, s08) `integrate` / `step` default to `method="cartesian"`, which gives Ṗ_b of B1913+16 96 % off
  (the docstring says the Cartesian route cannot resolve it). A warning when |f| r² per orbit falls below ~1e3 rtol
  would catch the misuse.

## Scripts and outputs

| script | output | what |
|---|---|---|
| `scripts/run.sh` | — | runs one script in `light-funnel-viz` with the engine read-only |
| `scripts/s00_sources.sh` | `out/00_quotes.txt` | fetches the cited texts, extracts the compared passages |
| (pytest) | `out/00_engine_tests.txt`, `out/07_ext_open_qutip.txt`, `out/08_layers_boundary.txt` | re-runs |
| `s01_magnus_hard.py` | `out/s01_magnus_hard.txt` | Magnus error estimate on hard drives; stiffness (S3) |
| `s02_expm_bound_and_steady.py` | `out/s02_…` | expm bound, eig route near the EP, steady-state bound (N7) |
| `s03_jumps_hard.py`, `s03b_lambda_detail.py` | `out/s03_…`, `out/s03b_…` | jumps on hard cases; rare events (S5) |
| `s04_negative_controls.py` | `out/s04_negative_controls.txt`, `…_triad.txt` | 33 mutations in the full run (one, P → −P, is a no-op: h₊, h× are invariant under a rotation of the basis by π); the handedness control Q = P × N run separately (`--match triad`) (S2) |
| `s04b_uncaught_effects.py` | `out/s04b_…` | effect size of the uncaught mutations (S2) |
| `s05_pn_hard.py`, `s05b_quasicircular.py`, `s05c_selfconsistent_vr.py` | `out/s05*` | strong field, routes, quasi-circular data (S1, S6, N1, N2) |
| `s06_peters_hard.py` | `out/s06_…` | Peters–Mathews at high/low e, averaging validity (N11) |
| `s07_waveform_pn_kinematics.py` | `out/s07_…` | waveform with PN kinematics vs 1PN (N4) |
| `s08_b1913_routes.py` | `out/s08_…` | B1913+16 through both routes (N12) |
| `s09_test_margins.py` | `out/s09_…` | power of the K, n convergence test (N6) |
| `s10_state_from_invariants_map.py`, `s10b_newton_trace.py`, `s10c_continuation_prototype.py` | `out/s10*` | E1: map, trace, fix prototype |
| `s11_b1913_1pn_flux_residual.py` | `out/s11_…` | N3 |
| `s12_time_grid_validation.py` | `out/s12_…` | S4 |
| `s13_periapsis_state_binding.py` | `out/s13_…` | N5 |
| `s14_general_frame_2p5pn.py` | `out/s14_…` | the 2.5PN term from B14 Eq. (203) reduced to the relative motion |
