# Physics review of `visualizations/v03_quantum_1d`, `v05_optics_bench`, `v06_qcd`, `v07_bell_test` (internal)

**Status: awaiting processing.** Reviewer: Claude (Opus) subagent, physics lens, 2026-10-23. The reviewer does not
process this review, writes no `RESPONSE.md` and does not archive it (`reviews/README.md`).

## Summary verdict

The physics engines these four visualizations wrap are right where they were tested independently: the Abelès
`stack` (equal to a Rouard recursion to 1e-13, regular at grazing), the thin-film closed forms, the split-operator
Schrödinger stepper and the stationary transfer-matrix reference, the 4-loop running (α_s(m_τ) = 0.3135 from 0.1173
against PDG 2024's 0.314 ± 0.014), the Bell correlations and the LHV models, the space-time conditions of v07.

The visualizations do **not yet meet** the owner's rule "точно выверены" over their own parameter ranges. The
problems are in run control, checks and ranges, not in the laws:

| ID | severity | one line |
|---|---|---|
| V3-1 | error | step with E just above V₀: the run stops while 46 % of the wave is in the window; T shown 0.26 instead of 0.60, outcomes drawn from it |
| V3-2 | should-fix | stop at norm < 1e-5 cuts slow transmitted parts: thick barrier T −55 %, the absolute tolerance 1e-4 lets it pass |
| V3-3 | should-fix | low energy: reference drops k < 0, run time floor v/4, detector reflection 4e-3…0.17 below 0.05 eV; checks fail on legal inputs |
| V3-4 | should-fix | live rebuilds take up to 349 s; trap at x0 = 60 nm OOM (dense 16384² Hamiltonian) or silent grid cap with aliasing |
| V3-5 | nit | energy label is not the mean energy (+19 %); "exact solution"; Bohm "exactly" with absorbing edges; spectrum drawn without Jacobian |
| V5-1 | error | θ exactly at the critical angle: ZeroDivisionError inside `set`, world half-changed, no rollback message |
| V5-2 | should-fix | `evan`/`film` checks ill-conditioned: fail at typed angles like θ_c + 1e-7°, 41.8103149° |
| V5-3 | should-fix | `joule` check: 2001 Simpson points cannot resolve a 1.2 nm skin depth (2e-8 > 1e-8) |
| V5-4 | nit | README still says grazing angles are refused; `stat` checks only R |
| V6-1 | error | α_s(M_Z) ≥ 0.205 (range allows 0.3): the world cannot be built (LandauPole in the closed-form checks) |
| V6-2 | should-fix | "κ vs 4/3 α_s", declared "not a check", is painted ✗ by the player |
| V6-3 | should-fix | omitted decoupling is 3.8e-3 at m_c (note says < 1e-3); continuity check is an identity; 4-loop running with LO matching |
| V6-4 | should-fix | changing the sweep speed throws the probe from 316 GeV back to 10 GeV |
| V6-5 | should-fix | fixed radial box: 150–390 MeV level errors for light quarks inside the ranges, silent |
| V6-6 | nit | α_s above 0.5 drawn as a flat line at the top (looks like freezing) |
| V7-1 | error | ~half of a = b (and anti-correlated) settings make `rng.choice` raise on −1e-17 probabilities; the run stops (e.g. a = b = 30°) |
| V7-2 | nit | a′ = a or b′ = b double-counts pairs; σ(S) off by ×1.55 |
| V7-3 | nit | LHV `nosig_law` compares 0.5 with 0.5; `tsir_law` implied there |

Presentation of models and interpretations is honest throughout (Cornell model outside the core with its 1S anchor;
LHV worlds flagged "modified physics"; Bohm/Everett/Copenhagen as readings with the same statistics; loopholes and
idealisations stated in v07; illustrative material values in v05). Nothing shown as measured in a run was found to
come from a closed form instead of the run's computation.

## Scope

* `visualizations/v03_quantum_1d/` (wave packet scattering, Copenhagen/Bohm/Everett readings),
  `v05_optics_bench/` (Fresnel, thin films, TIR/FTIR, Bragg, Fabry–Pérot, single photons),
  `v06_qcd/` (running α_s to 4 loops, thresholds, Cornell quarkonium), `v07_bell_test/` (CHSH, LHV models):
  `viz.py`, `engine/`, `web/view.js`, `tests/`, `README.md` of each;
* the `lfphys` modules they use (`core.quantum.{schrodinger1d,transfer,qubits,radial}`,
  `core.optics.{interfaces,thin_films}`, `core.qcd.{running,su3}`, `core.{data,causality}`,
  `theories.interpretations.{bohm,copenhagen,everett}`, `theories.models.cornell`,
  `theories.alternatives.local_hidden`, `theories.approx.ray_optics`, `tools.bell_stats`);
* the server pieces they rely on (`server/lfviz/{sim,params}.py`, `player/js/player.js` check rendering) and the test
  harness `visualizations/tests/harness.py`.
* Not reviewed: `v04_orbits` (being built by someone else), the server transport.

SHA-256 of the files as reviewed: `out/00_sha256_reviewed_files.txt` (snapshot at the start, 20:43). Several files
(v05 `viz.py`, `README.md`, `engine/bench.py`, `lfphys/core/optics/{interfaces,thin_films}.py`) were modified minutes
before the snapshot; line numbers refer to that snapshot. A second snapshot at the end is in
`out/99_sha256_at_end.txt`. Changed during the review (by someone else): `lfphys/core/optics/interfaces.py` and
`thin_films.py` (21:29: overflow-safe `stack`, logarithmic `ftir_T`), `lfphys/core/quantum/transfer.py` (21:31:
scaled transfer product), `server/lfviz/sim.py` and `v03/tests` (20:54: engine modules in the `live` message),
`compton.py`, `hydrogen.py` (not used here). The v05 scripts and script 01 were re-run after these changes; every
finding below reproduces unchanged (first outputs kept as `out/*__before_*.txt`). The visualizations' own `viz.py`
files did not change during the review.

## Environment

Docker image `light-funnel-viz:latest` (Python 3.11, numpy, scipy), CPU only, no GPU. Every script runs as

```
docker run --rm --user "$(id -u):$(id -g)" -v /home/ildar/hdd/projects/i/light-funnel:/lf \
  -w /lf/reviews/2026-10-23_internal_viz-v03-v07_physics \
  -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
  light-funnel-viz python3 <NN_script>.py
```

Outputs are in `out/`. The project's own suites pass: `out/00_pytest_viz.txt` (83 passed, 102 s).

## Findings

Severity: **error**: on a legitimate input, a wrong number or picture shown as the run's result, a world that cannot
be built or stops, or a half-applied change (broken owner rule). **should-fix**: misleading, unreliable or unguarded
(including checks that fail or pass for numerical reasons of the check itself), but not wrong in the default use.
**nit**: labels, conventions, documentation. Line numbers: snapshot `out/00_sha256_*`.

### v03 — quantum particle in 1-D

#### V3-1. error: the step potential with E slightly above V₀ — half of the wave is never detected, and the outcome statistics are wrong by ×2.3

* **Location.** `v03_quantum_1d/viz.py:182-188` (`_evolve`: the run time `t_end`).
* **What is wrong.** `t_end = 1.3 (L/v_in + L/max(min(v_in, v_out), 0.2 v_in))` with `v_in = max(v − 3ħ/(2mσ), v/4)`
  and `e_out = ½ m v_in² − V(L)`; when the slowest considered component cannot pass the step (`e_out ≤ 0`) the code
  falls back to `v_out = v_in`, i.e. it assumes the transmitted wave moves as fast as the incident one. For E − V₀
  small the transmitted wave is several times slower (v ∝ √(E − V₀)), so the run stops while most of it is still in
  the window. Then `PR/(PL + PR)` (`viz.py:303, 388`) is the transmitted fraction *of what happened to be absorbed*;
  every particle's outcome is drawn from it, the statistics check compares the counts with the same truncated
  number (so it passes), and only the `abs`/`T` checks fail.
* **Evidence** (`01_v03_transmission_reference.py`, `out/01_*.txt`; `03_v03_stop_criterion.py`, `out/03_*.txt`).
  Step V₀ = 0.75 eV, E = 0.8 eV (the `step` preset has V₀ = 0.6): absorbed 0.542 (46 % still in the window),
  T_run = 0.2585 vs the stationary reference 0.5982. With `t_end` ×4 and the stop threshold 1e-9 (patched in-process):
  T_run = 0.5914, absorbed 0.988 — the run converges to the reference only when it is given the time.
* **Fix.** Estimate the exit speed from the slow edge of the *transmitted* spectrum (E − V_out of the components with
  T(E) above a threshold, from the run's own T(E)), or integrate until the norm left in the window is below a
  threshold tied to the check tolerance (with a cap and a notice when the cap is hit). Do not draw outcomes from
  `PR/(PL+PR)` while the absorbed total is far from 1 (refuse the set-up or say so in a notice).

#### V3-2. should-fix: the stop criterion `norm < 1e-5` makes small transmissions wrong by 55 % (and the check cannot see it)

* **Location.** `viz.py:213` (`if not osc and norm[-1] < 1e-5: break`), `viz.py:390` (tolerance `1e-4 + 1e-3·T`).
* **What is wrong.** The integration stops when 1e-5 of the probability is still in the window. For a thick barrier
  the transmission (~1e-6) is carried by components near the barrier top, which are slow inside the barrier and
  arrive late: they are cut off. The `T` check has an absolute tolerance 1e-4, larger than T itself, so it passes.
  The README says "the time-dependent result agrees to ~1e-5 for the presets" — an absolute statement that hides
  the relative error.
* **Evidence.** `out/01_*`: width 5 nm, T_run = 7.13e-7 vs reference 1.603e-6 (−55 %), check `ok = True`.
  `out/02_*`: halving the time step twice changes T_run by < 1e-11 (not a time-step error). `out/03_*`: stop at 1e-9 and
  `t_end` ×4 → T_run = 1.6022e-6 (−2.9e-4). Width 3 nm: −0.37 % (passes, but also cut).
* **Fix.** Stop on a threshold relative to the smaller detector total (e.g. leftover < 1e-3·min(PL, PR) and absolute
  1e-9), and use a relative tolerance for T (e.g. `1e-3·T + 1e-7`), so that a factor-2 error fails.

#### V3-3. should-fix: low energies — the check's reference drops the k < 0 part of the packet, and slow parts are cut or reflected by the detectors

* **Location.** `viz.py:344-354` (`_expected_T`: `ks` from `max(k0 − 8 s_k, 1e-6)`, normalised by `Σ w` over k > 0
  only); `viz.py:184` (`v_in` floor `0.25 v`); `viz.py:163-168` (detector ramp W = 2 eV (d/15 nm)²);
  README "the detectors ... their reflection is below the checks' tolerance".
* **What is wrong.** (a) A packet with k₀ < ~3 s_k (E near 0.05 eV with σ near 1 nm, both inside the ranges) has a
  part with k < 0 that moves away from the potential and is counted as reflected; the run's reference renormalises it
  away, so the reference is too large by 1/(1 − P(k<0)). (b) The run time ignores components slower than v/4, and
  (c) the detector ramp reflects slow electrons far above the tolerances (the box is periodic: the reflected part
  ends in the opposite detector, i.e. as the wrong outcome).
* **Evidence.** `out/01_*`: free particle, E = 0.05 eV, σ = 1 nm: P(k<0) = 1.09e-2; T_run = 0.9664, the run's
  reference 1.0000, the full-distribution reference 0.9891; checks `T` and `abs` (0.973) fail. Well V₀ = −5 eV,
  E = 0.05, σ = 1 and step V₀ = −5, E = 0.05, σ = 1: `T` fails (3.80e-1 vs 3.70e-1; 5.29e-1 vs 5.13e-1).
  `out/03_*`: with ×4 run time the free case still gives 0.957 (detector reflection). `out/04_*` (own stationary
  transfer-matrix computation of the absorbing ramp): R = 4.0e-3 at 0.05 eV, 6.4e-2 at 0.02 eV, 0.17 at 0.01 eV
  (vs 4e-6 at 0.1 eV).
* **Fix.** Use the whole Gaussian in the reference (k < 0 with T = 0); lengthen or adapt the absorbing ramp to the
  slowest relevant wavelength (reflection ∝ exp(−(k·DET)…); a longer ramp or a lower W gradient), or restrict the
  energy range and say so; state the detector reflection as a function of energy in the README.

#### V3-4. should-fix: the cost of a world is unbounded over the allowed ranges; live changes freeze the world for minutes, the trap can run out of memory or alias silently

* **Location.** `viz.py:247-269` (`set_live` rebuilds synchronously: `_build` + `_evolve`), `viz.py:157-158`
  (grid size, silently capped at 32768), `viz.py:400` (`g.eigenstates` → `schrodinger1d.Grid.hamiltonian`: dense
  n × n matrices, several temporaries of 8 n² bytes).
* **What is wrong.** (a) Every live change (except the reading) recomputes the whole wave before the world goes on;
  there is no estimate, cap or notice. (b) In the trap the dense sinc-DVR Hamiltonian for the level check needs tens of
  GB at the larger grids. (c) When the grid needs more than 32768 points it is capped without a word, and the packet's
  momentum can exceed the grid's Nyquist limit (aliasing: wrong dynamics, no check aimed at it).
* **Evidence.** `13_v03_rapid_sets.py` (`out/13_*`): `set(scenario="step", V0=10)` at E = 0.05 eV, σ = 15 nm: 349 s;
  `set(scenario="well", V0=−5, edge=0.02, energy=20)`: 136 s (32768 points); `out/01_*`: well V₀ = −5, E = 0.05,
  σ = 1: 128 s. `05_v03_oscillator_limits.py` (`out/05_*`): hw = 0.05 eV, x0 = 60 nm (both inside the ranges) → 16384
  points, one n² array 2.1 GB, the world was OOM-killed in a 6 GB container after 125 s (exit 137); hw = 1 eV,
  x0 = 60 nm → grid capped (65536…262144 needed), π/dx = 711 nm⁻¹ < packet k_max 823 nm⁻¹, 2.5e6 time steps; stopped
  by the reviewer after 24.5 min still integrating.
* **Fix.** Estimate n and the number of steps before building and refuse (or ask for confirmation) above a budget;
  refuse instead of capping the grid; compute the 4 lowest trap levels with a sparse/banded method (e.g. a
  finite-difference or Fourier Hamiltonian with `scipy.sparse.linalg.eigsh`, or the DVR on a window around the trap
  only); build the new set-up in the background while the old one keeps running.

#### V3-5. nit: wording and drawing

* `viz.py:57` help of `energy`: "средняя кинетическая энергия ħ²k₀²/2m". The mean kinetic energy of the packet is
  ħ²k₀²/2m + ħ²/(8mσ²) (the run's own `E` check uses exactly that); at E = 0.05 eV, σ = 1 nm the mean is 0.0595 eV
  (+19 %). Call it "энергия центральной компоненты ħ²k₀²/2m".
* `viz.py:496-497` header "Волна каждой — точное решение уравнения Шрёдингера", README "the exact solution … on a
  grid": in view of V3-1…V3-3 say "numerical solution (split-operator), converged to …; detectors are a model".
* README (Bohm): "it is exactly the q-quantile of |ψ(t)|², with the absorbed mass counted beyond the edges". With an
  absorbing potential the quantile is conserved only outside the detector ramps; inside them the construction is a
  model of detection (fine, but not "exactly").
* `viz.py:3` docstring "Electrons (or protons)" vs README "Electrons only" and the view's fixed "частица: электрон".
* `web/view.js:181-183`: the grey "спектр энергий пакета" is the k-space weight w(k) drawn against E without the
  Jacobian dk/dE; for wide packets its shape is not the energy distribution.

### v05 — optical bench

#### V5-1. error: the exact critical angle of the bare face makes `set` raise inside the segment computation; the world is left half-changed

* **Location.** `v05_optics_bench/viz.py:186-190` (`set_live` assigns `self.params`, `self.st` and then calls
  `_new_segment`), `viz.py:346-352` (`evan` check: `dmeas = 2 (z2 − z1)/log(I1/I2)`), `thin_films.evanescent_length`
  (raises for q ≤ 0); `server/lfviz/sim.py` `Runner.handle` catches only ValueError/KeyError/TypeError.
* **What is wrong.** At θ = θ_c (as `math.degrees(math.asin(n_s/n₀))` gives it, a value the owner can type) the
  run's bisection puts θ_c a few ulp below θ, so `th > th_c` holds, but the evanescent decay constant is 0: |E|² is
  the same at both depths and `log(I1/I2) = 0` → `ZeroDivisionError`. A few ulp further, `evanescent_length` can
  raise `ValueError` for q ≤ 0 in its own rounding. In both cases the exception leaves `set_live` *after* the new
  parameters and structure were installed and the new segment (curves, expectation) was emitted, but before its
  checks: the "refused change leaves the world as it was" rule (RULES §2.4) is broken; for the ZeroDivisionError the
  runner's `handle` does not catch it, the play loop reports a traceback and pauses, and the `live` message that rolls
  the player's control back is never sent.
* **Evidence** (`07_v05_adversarial_angles.py`, `out/07_*.txt`, part B/C): preset `tir`, `set(theta_deg =
  41.810314895778596)` → `UNCAUGHT ZeroDivisionError: float division by zero`; afterwards `params.theta_deg` is the new
  value, `seg = 1`, 2 segments emitted. Same at θ_c + 1e-14°.
* **Fix.** Compute everything of the new segment into locals first and commit only at the end (as v03/v07 do with a
  try/rollback); make the evanescent checks conditional on q > ε (ε relative, see V5-2); catch arithmetic errors in
  `Runner.handle` like the other refusals.

#### V5-2. should-fix: the `evan` and `film` checks are ill-conditioned near θ_c / the grazing angle and fail on typed angles

* **Location.** `viz.py:346-352` (`evan`, tol 1e-8), `viz.py:372-389` (`film`, tol 1e-12, grazing switch only for
  |cos θ₁| < 1e-6), `thin_films.evanescent_length` (q = n₁² sin²θ − n₂² by subtraction).
* **What is wrong.** Near θ_c both the run's decay length (through `cmath.sqrt(1 − (n₀ sin θ/n)²)` in the engine) and the
  reference lose digits as eps/q; near the grazing angle inside a single layer the Airy sum is 0/0 with relative
  error ~eps/|cos θ₁|². The tolerances do not scale with these condition numbers, so the checks fail for physically
  ordinary angles that differ from θ_c in the 8th–10th digit (what one types after reading θ_c off the plot or the
  checks panel).
* **Evidence** (`out/07_*.txt`). Bare face (`tir`): θ = θ_c + 1e-7° → `evan` rel 2.8e-8 > 1e-8 (fails);
  θ_c + 1e-9° → rel 2.8e-6; θ_c + 1e-12° → rel −2.8e-3; in a scan of θ_c + k·1e-14°, 18 of 39 values above θ_c fail.
  Prism + 200 nm gap (`ftir`): θ = 41.8103149° (θ_c + 4.2e-9°) → `film` = 4.1e-12 > 1e-12 (fails); θ_c ± 1e-9° → 9.6e-12,
  7.6e-12. The engine itself is right there (V5 "verified": the Abelès product equals an independent Rouard
  recursion to 1e-13 and stays regular exactly at grazing, `out/06_*`, part B).
* **Fix.** Compute q as (n₁ sin θ − n₂)(n₁ sin θ + n₂) and give `evan` a tolerance ∝ eps·n²/q (or skip it with a note
  for q < 1e-6); for `film` widen the grazing switch to |cos θ₁| < 1e-3 (compare at θ ∓ 1e-3 rad there) or use a
  tolerance ∝ eps/|cos θ₁|².

#### V5-3. should-fix: the `joule` check fails for strongly absorbing, thick metal films (quadrature, not physics)

* **Location.** `viz.py:317-322`, `thin_films.joule_absorption_s(points=2001)` (Simpson, fixed number of points per
  layer).
* **What is wrong.** The |E|² decay length λ/(4πκ) is 1.2 nm for κ = 20 at 300 nm; 2001 points over 500 nm (0.25 nm
  spacing) resolve it to ~2e-8, above the tolerance 1e-8. All parameters are inside their ranges.
* **Evidence.** `11_v05_fuzz.py` (`out/11_*`): 300 random live changes, the only failed check is `joule` (2×), e.g.
  n₀ = 4, metal 0.2 + 20i, 500 nm, λ = 300 nm, θ = 70.24°. `12_v05_joule_and_rate.py` (`out/12_*`): R + T + A_J − 1 =
  +2.1e-8 / +8.2e-11 / −5.1e-13 with 2001 / 8001 / 32001 points (normal incidence, same film).
* **Fix.** Choose the points from the skin depth (≥ 20 per decay length of |E|², capped), or integrate |E|² in each
  homogeneous layer in closed form (it is a sum of four exponentials of the forward/backward amplitudes).

#### V5-4. nit: README out of date and the photon statistics check covers only R

* `README.md:63-66` still says a change "is refused … when the angle falls within 1e-7 rad of an angle at which the
  wave inside an inner layer grazes its boundaries", while the code accepts it (`tests/test_v05_optics.py:209`
  `test_grazing_angle_of_an_inner_layer_is_accepted`, and README "Numerics" says the same). Remove the sentence.
* `viz.py:419-429` (`stat`): only the reflected fraction is tested (binomial z); a swap of T and A would pass. A
  multinomial χ² over (R, T, A) (2 degrees of freedom) is the natural check; the note already prints the T and A
  counts.

### v06 — QCD

#### V6-1. error: worlds with α_s(M_Z) ≥ 0.205 cannot be created, although the parameter allows up to 0.3

* **Location.** `v06_qcd/viz.py:31` (range 0.05–0.3), `viz.py:127-138` (`one`/`two` checks call `running.alpha_s`
  directly, without the NaN guard of `_alpha`); `server/lfviz/worker.py` (`sim = viz["simulation"](...)` for the first
  world is not guarded).
* **What is wrong.** The one-loop closed-form check at 2 GeV with n_f = 5 meets the Landau pole for α_s(M_Z) ≳ 0.205;
  `LandauPole` propagates out of the constructor. As a `new_world` the run answers "Новый мир не создан: полюс
  Ландау …"; as the first world of a run (POST /api/runs) the worker process dies with a traceback. The README presents
  α_s(M_Z) as a "what if" world parameter; the modified worlds the owner can ask for stop at 0.2.
* **Evidence** (`08_v06_qcd.py`, `out/08_*`, part A): 0.05–0.20 build; 0.205, 0.21, 0.22, 0.25, 0.3 →
  `CONSTRUCTION FAILED LandauPole: … μ ≈ 2.2 … 7.8 ГэВ`.
* **Fix.** Guard the closed-form checks like `_alpha` (skip with a note "below the Landau pole of the closed form"),
  or move their scales above the pole; or restrict the range and say why.

#### V6-2. should-fix: the "κ vs 4/3 α_s" comparison is displayed as a failed check

* **Location.** `viz.py:170-174` (`kap` check: `ok=None`, `ref` set, default `tol=1e-9`); `player/js/player.js:489-494`
  (with `ok` absent and `rel` present the player shows ✓ only if |rel| ≤ tol).
* **What is wrong.** The note says "сравнение двух слоёв, не проверка", but the player renders a red ✗ whenever the
  comparison is emitted. The project's own test excludes it from "bad" by name (`tests/test_v06_qcd.py`), i.e. the
  test knows the panel shows it as failed.
* **Evidence** (`out/08_*`, part B): preset `bottom`: κ = 0.52 vs 4/3 α_s(1/⟨r⟩) = 0.5725, rel −0.092, tol 1e-9 →
  shown ✗.
* **Fix.** Emit it with `ref` but an explicit neutral state (e.g. `ok` omitted and `tol=None` handled by the player
  as "—", or a separate message type "comparison"), so that a model-vs-core comparison is never painted as a failure.

#### V6-3. should-fix: threshold matching — the stated size of the omitted term is wrong at m_c, and the continuity check cannot fail

* **Location.** `lfphys/core/qcd/running.py:14-16` (docstring), `v06_qcd/README.md` ("leading-order (continuous)
  matching"), `viz.py:139-144` (`thr` checks, note "член (11/72)(α_s/π)² не учтён, < 1e-3").
* **What is wrong.** (a) The omitted NNLO decoupling (PDG 2024 Eq. (9.4): c₂₀ = −11/(72π²) for the MS-bar mass at m_h,
  checked in the PDF) is 7.8e-4 relative at m_b but 3.8e-3 at m_c, so "< 1e-3" is false at the charm threshold.
  (b) With continuous matching, α(m(1+1e-9)) = α(m(1−1e-9)) is true by construction: the check tests the bookkeeping,
  not physics, and would pass unchanged if the decoupling were implemented wrongly. (c) Running at 4 loops with
  continuous matching mixes orders: below m_b the omitted 2- and 3-loop decoupling terms (−4.9e-4 in α_s(m_τ),
  −2.2e-3 just below m_c) are a third of the whole 3→4-loop difference at m_τ (1.7e-3) that the `conv` check reports.
* **Evidence** (`08_v06_qcd.py` part C, own 4-loop integration; `08b_v06_alpha_tau_vs_pdg.py`):

  | scale | engine | + c₂ (NNLO) | + c₂ + c₃ (N³LO) |
  |---|---|---|---|
  | m_τ | 0.31910 | 0.31948 | 0.31959 |
  | 0.999 m_c | 0.38647 | 0.38795 | 0.38864 |

  (c₃ = 564731/124416 − 82043/27648 ζ₃ − 2633/31104 n_l as implemented in RunDec, quoted from memory, not verified
  in this review; c₂ verified against PDG Eq. (9.4).)
* **Fix.** Implement the decoupling to the order consistent with the running (n−1 loops for n-loop running, as
  RunDec/PDG do) and make the threshold check compare the jump with the closed-form decoupling relation; or keep
  continuous matching, correct the "< 1e-3" statement (it is ~4e-3 at m_c) and present the `thr` entries as
  identities.

#### V6-4. should-fix: changing the sweep speed throws the probe back to the start scale

* **Location.** `viz.py:212-214` (`set_live`: `mu_t0 = t` for `mu` or `sweep`), `viz.py:225-230` (`mu_now` starts from
  `params["mu"]`).
* **What is wrong.** A live change of the speed should change the rate from the current probe position; instead the
  probe jumps back to the `mu` parameter (a discontinuity not caused by any physics).
* **Evidence** (`out/08_*`, part D): preset `standard`, t = 3 s at 0.5 decade/s from 10 GeV → probe at 316.2 GeV;
  `set(sweep=0.6)` at the same t → 10 GeV.
* **Fix.** On a `sweep` change, store the current log μ as the new origin (only a `mu` change should reposition).

#### V6-5. should-fix: the quarkonium levels use a fixed box (R = 25 GeV⁻¹) that is too small for light quarks in the allowed range

* **Location.** `lfphys/theories/models/cornell.py:40-49` (`spectrum`, R = 25, N = 700), `viz.py:89, 100-101`;
  ranges `m_q` 0–10 GeV, κ 0–1.5, a 1–5 GeV⁻¹.
* **What is wrong.** For a light quark and a weak string the excited states reach the wall; the levels are then box
  levels, silently (the only signal is the model-vs-PDG check, which the owner reads as a model failure).
* **Evidence** (`out/08_*`, part E; R = 60, N = 1700 as reference): m_q = 0.3 GeV, κ = 0.52, a = 5: worst splitting
  error 152 MeV (3D: 1016 vs 864 MeV); m_q = 0.2, κ = 0, a = 5: 393 MeV. Default parameters: < 1e-3 MeV.
* **Fix.** Choose R from the size of the highest state (e.g. ≥ 8 ⟨r⟩ of n = 3) or check the levels at two box sizes
  and emit a numerical check; or restrict m_q.

#### V6-6. nit: the α_s plot clips values above 0.5 to a flat line at the top (looks like a frozen coupling)

* **Location.** `v06_qcd/web/view.js:35-37` (`Y(a) = … Math.min(a, amax)`, amax = 0.5).
* **Evidence** (`out/08_*`, part F): preset `strong` reaches α_s = 1.02 (1 loop) … 2.07 (2 loops) on the drawn curves;
  above 0.5 they are drawn as a horizontal segment along the top edge, which resembles the "freezing" of α_s
  discussed in the literature rather than the approach to the pole the run computes. Clip the path at the frame
  (or switch to a log axis / auto-scale) and mark "off scale".

### v07 — Bell test

#### V7-1. error: about half of all perfectly (anti)correlated settings stop the run (negative round-off probability)

* **Location.** `lfphys/core/quantum/qubits.py:125-129` (`sample_pairs`: `rng.choice(len(P), p=P/P.sum())`), called from
  `v07_bell_test/engine/experiment.py:97-101, 227-233` in every `advance` that detects pairs.
* **What is wrong.** At settings where one joint Born probability is exactly 0 (photons: a − b = 0 or 90° mod 180°;
  spins: a − b = 0 or 180° mod 360°) the trace Tr(ρ Π⊗Π) comes out as ±1e-17. When it is negative, numpy's
  `Generator.choice` raises `ValueError: Probabilities are not non-negative`; `advance` fails; the runner pauses with a
  traceback; every further play fails again. Equal settings are the textbook first experiment (perfect correlation).
* **Evidence** (`09_v07_bell.py`, `09c_v07_zero_cells_map.py`, `out/09*_*.txt`): over half-degree settings in [0, 360°)
  with a = b, 371 of 720 (photons) and 378 of 720 (spins) give a negative cell; integer examples a = b = 1°, 2°, 5°, 30°…
  The run with fixed settings: photons a = b = 30° → `advance RAISES ValueError`; spins a = b = 30° → raises; spins
  a = 50°, b = 230° → raises (min P = −3.1e-33). With a = 0 and b ∈ {0, 90, 180, 270, 360}° the zero cells happen to
  come out non-negative (`out/09b_*`), which is why the presets (a = 0) and the tests pass.
  The same unclipped pattern exists in `qubits.measure` and `copenhagen.measure_and_collapse` (not exercised here).
* **Fix.** Clip in the engine: `P = np.clip(P, 0, None)` (and renormalise) in `sample_pairs` (and wherever probabilities
  from traces are sampled: `copenhagen.measure_and_collapse`, `qubits.measure`), with a test at a = b = 30°.

#### V7-2. nit: degenerate settings (a′ = a or b′ = b) double-count pairs; the error of S is then wrong

* **Location.** `engine/experiment.py:268-299` (`Store` keys by angle pair), `viz.py:289-297` (`_S`),
  `tools/bell_stats.chsh` (Var S = Σ Var E_k for four independent cells).
* **What is wrong.** With a′ = a the cells (a,b) and (a′,b) are the same counts, so S = 2E(a,b) and the reported σ is
  too small or too large depending on the other settings; the 5σ checks on S are then miscalibrated.
* **Evidence** (`out/09_*`, part B; 60 seeds × ~4000 pairs): a = a′ = 0, b = 45°, b′ = 0: empirical SD of S 0.049,
  reported σ 0.032 (ratio 1.55: a "5σ" check is effectively 3.2σ); a = a′ = 0, b = 0, b′ = 45°: SD 0, reported 0.032.
  Calibration of the non-degenerate presets is fine (part C: SD of z 0.91–1.13 over 60 seeds).
* **Fix.** Refuse or flag coinciding settings in the CHSH panel (S is not a CHSH test then), or count the cells by
  setting label (x, y) rather than by angle pair.

#### V7-3. nit: two "checks" that cannot fail

* `viz.py:204-205`: in LHV worlds `nosig_law` compares the constant 0.5 with 0.5 ("P(+) = 1/2 … closed form of the
  model"); nothing of the run enters. Either compute the marginal from the model's sampler/closed form at the
  current settings or show it as information.
* `viz.py:206-207`: `tsir_law` in LHV worlds (|S_law| ≤ 2√2 when |S_law| ≤ 2 is already checked) is implied by
  `chsh_law`. Harmless; mention in the README that it is an identity there.

## Verified correct

Each item states what was compared with what; numbers are in the outputs named.

**v03.**
* Units: ħ = 0.6582 eV·fs, m_e = 5.686 eV·fs²/nm² (ħ²/2m = 0.0381 eV·nm² = (ħc)²/(2mc²)); the world clock in seconds
  with FS = 1e-15 is used consistently (clicks at `t0 + t_snap·FS`).
* The mean-energy check reference ħ²k₀²/2m + ħ²/(8mσ²) is the right value for a Gaussian whose |ψ|² has variance σ²
  (`out/01_*`: rel ≤ 4e-14).
* The stationary reference itself (transfer matrices + Richardson) agrees with an independent 4001-point,
  full-distribution reference wherever P(k<0) = 0 (default: 0.2028044 vs 0.2028075); the time-dependent route
  converges to it when given the time and a small stop threshold (thick barrier −2.9e-4, `out/03_*`); halving the
  time step changes T by < 1e-11 (`out/02_*`). The physics of the engine is right; V3-1…V3-3 are run-control and
  reference issues.
* The three readings give the same outcome statistics by construction (Bohm side ⇔ q vs PL(t), 1 − PR(t);
  Copenhagen/Everett draw with PR/(PL+PR)), as the project's tests show; the Bohm quantile rule is the exact 1-D
  no-crossing construction outside the detectors.
* Trap: levels ħω(n + ½) to 1e-12 (`out/05_*_run_0.05_15.txt`); the packet oscillates between ±15 nm and returns
  after 2π/ω (float64 return error 1.7e-13 nm; the check's equality to all digits comes from the float32 snapshots,
  `10_v03_oscillator_period.py`, `out/10_*`).

**v05.**
* `interfaces.stack` (Abelès, rewritten today) equals an independent Rouard recursion written for this review to
  ≤ 1.7e-13 (r, t, R, T) on 4000 random stacks (1–6 layers, a quarter absorbing, 0–89.9°, s and p), and stays
  regular exactly at grazing inside a layer (R + T − 1 ~ 1e-16) where the recursion is 0/0 (`06_*`, `out/06_*`).
* Fresnel conventions are those of Born & Wolf: r_p = tan(θi − θt)/tan(θi + θt), r_s = −sin(θi − θt)/sin(θi + θt),
  r_p = −r_s at normal incidence; T with Re(n cos θ) (s) and Re(n cos θ*) (p).
* Closed forms of `thin_films` against Rouard: Bragg R for both layer orders (the README remark on the order is right),
  FTIR for s and p (1e-12 relative), the Airy intensity formula including n₀ ≠ n_s (1e-14), Brewster |r_p| = 7e-17 at
  arctan 1.5, θ_c = arcsin(n_s/n₀).
* Joule heating (Poynting's theorem) for s converges to 1 − R − T (5e-13 with enough points, `out/12_*`).
* Photon bookkeeping (emitted = R + T + A + lost + in flight) held after each of 300 random live changes across all
  ranges; no non-finite blob (`out/11_*`). The 1e15/s rate runs.

**v06.**
* β₀…β₃ (MS-bar, a = α_s/4π) as in the engine agree with the coefficients written independently for this review
  (the standard van Ritbergen–Vermaseren–Larin values); the two-loop implicit solution used in `two` is correct
  (re-derived).
* α_s(m_τ): the engine gives 0.3135 from α_s(M_Z) = 0.1173, PDG 2024 Sec. 9.4.1 states "α_s(m_Z²) = 0.1173 ± 0.0017
  … corresponds to α_s(m_τ²) = 0.314 ± 0.014" (text checked in the downloaded PDF); with N³LO decoupling 0.3139
  (`08b_*`). From the world average 0.1180 the engine gives 0.3191 (PDG band ±0.0009 → [0.3119, 0.3266]).
* α_s(M_Z) = 0.1180 ± 0.0009 is Eq. (9.25) of the 2024 review (the PDF labels it "(PDG 2023 average)"); M_Z, m_c(m_c),
  m_b(m_b), m_t and the quarkonium masses in `core.data` agree with the PDG 2024 values as far as the reviewer knows
  them (not re-checked line by line against the listings in this review).
* C_F = 4/3 and C_A = 3 from the matrices; (2J+1) spin averaging; the Cornell parameters as quoted (κ = 0.52,
  a = 2.34 GeV⁻¹, m_c = 1.84, m_b = 5.18 GeV); the fixed box is converged for the default parameters (< 1e-3 MeV).

**v07.**
* E = cos 2(α − β) for |Φ+⟩ with polarizers and E = −cos(θ_A − θ_B) for the singlet; the LHV models' E
  (½cos 2Δ; −1 + 2θ/π) and their maximal |S| (√2; 2); locality is by construction in the LHV samplers.
* The space-time conditions: locality cτ < 2L; freedom of choice |L/v − τ|c < L; both only for v > c/3; the
  order-reversal speed β* = cτ/(2L) (re-derived).
* Statistics: z of S over 60 seeds × 4000 pairs has mean ≈ 0 and SD 0.91–1.13 for the four CHSH presets
  (`out/09_*`, part C): the 5σ tolerances are calibrated (outside the degenerate case V7-2).
* The README states the loopholes honestly: ideal detectors (detection loophole not modelled), the measurement as an
  instant, a seeded pseudo-random choice ("freedom of choice" = space-time relation only).

## Scripts

| script | what | output |
|---|---|---|
| `01_v03_transmission_reference.py` | packet T vs the run's and a full-distribution reference, 10 legitimate set-ups | `out/01_*` |
| `02_v03_thick_barrier_convergence.py` | time-step convergence of the 5 nm case | `out/02_*` |
| `03_v03_stop_criterion.py` | stop threshold and run time patched in-process | `out/03_*` |
| `04_v03_detector_reflection.py` | own transfer matrices for the absorbing ramp | `out/04_*` |
| `05_v03_oscillator_limits.py` | grid, steps, Hamiltonian size; real runs in a 6 GB container | `out/05_*` |
| `06_v05_engine_independent.py` | Rouard recursion vs `stack`; closed forms | `out/06_*` |
| `07_v05_adversarial_angles.py` | angles near θ_c / grazing through the harness | `out/07_*` |
| `08_v06_qcd.py`, `08b_v06_alpha_tau_vs_pdg.py` | α_s(M_Z) range, `kap`, matching, sweep, box, view scale; α_s(m_τ) vs PDG | `out/08*_*` |
| `09_v07_bell.py`, `09b_*`, `09c_*` | zero cells, degenerate settings, z calibration, pairs in flight | `out/09*_*` |
| `10_v03_oscillator_period.py` | the period check | `out/10_*` |
| `11_v05_fuzz.py` | 300 random live changes | `out/11_*` |
| `12_v05_joule_and_rate.py` | Joule quadrature, rate 1e15 | `out/12_*` |
| `13_v03_rapid_sets.py` | successive live changes, their wall time | `out/13_*` |

The v05 scripts were run twice: against the snapshot of 20:43 (outputs kept as `out/*__before_2129_engine_change.txt`)
and again after `interfaces.py`/`thin_films.py` changed at 21:29 (`out/06_*`, `07_*`, `11_*`, `12_*`).
Containers were started under names `rev-v03v07-*` and removed by name; the shared `lf-viz` server was not used.
Not done: headless screenshots of the views (the views were read in full instead).

