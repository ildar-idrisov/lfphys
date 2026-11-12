# Internal review: physics and numerics of the `lfphys` engine

**Status: awaiting processing.**

- Reviewer: internal (Claude subagent, independent of the session that wrote `lfphys`).
- Date delivered: 2026-10-23.
- Scope: `lfphys/lfphys/` (core, theories, laws, tools) and `lfphys/tests/`, as of 2026-10-23.
  Priorities: (1) physics correctness of core formulas/algorithms; (2) layering honesty (core vs theories);
  (3) independent verification of the strongest numerical claims; (4) constants/PDG data; (5) missing physics (short).
- Out of scope: `visualizations/` (not touched), papers, STATUS.

## Environment

All checks run in Docker, CPU only, image `light-funnel-viz` (numpy, scipy, python-flint 0.9.0, mpmath, pytest):

```
docker run --rm --user "$(id -u):$(id -g)" -v /home/ildar/hdd/projects/i/light-funnel:/lf \
  -w /lf/reviews/2026-10-23_internal_lfphys-engine_physics -e PYTHONPATH=/lf/lfphys light-funnel-viz python3 NN_*.py
```

Each check is a numbered script `NN_*.py` in this folder (all accept `--help`); its output is saved in
`out/NN_*.txt`. `out/00_pytest.txt` is the engine's own test suite (280 passed). `11_pdg_spotcheck.sh` runs on the
host (curl + pdftotext, anonymous requests, no identifiers). Sources fetched for the review are cited where used.

## Findings

Summary (severity; status tag per AGENTS.md §7: [error in earlier] = an error in the engine as delivered,
[weakens] = weakens a stated claim or rule without a wrong number):

| ID | severity | tag | one line |
|---|---|---|---|
| E1 | error | [error in earlier] | hydrogen: documented ~1e-6 agreement false; `dirac_level` (no recoil) off by 5.5e-4, `schrodinger_level` by 9.3e-6 |
| E2 | should-fix | [error in earlier] | Klein–Nishina σ_tot only ~4 significant digits (6e-5) for 1e-4 ≤ E/mc² < 1e-3 (`log(1+2x)`) |
| E3 | should-fix | [error in earlier] | `interfaces.stack`, `ftir_T` raise OverflowError for κd ≳ 710 (opaque gap/film) |
| E4 | should-fix | [error in earlier] | `transfer.transmission` OverflowError, `transmission_profile` NaN for a barrier at x ≈ 1000/κ |
| E5 | should-fix | [weakens] | radial Coulomb accuracy after Richardson is 2e-4 at defaults, not the documented ~1e-6 |
| E6 | nit | [error in earlier] | Wigner rotation: returned sign opposite to the docstring; sign untested |
| E7 | should-fix | [weakens] | α_s: 4-loop running with LO threshold matching; omitted decoupling 1e-3 (m_b) … 5.6e-3 (m_c) |
| E8 | should-fix | [weakens] | refuted emission-theory front computed and stated in core `gravity.arrivals` |
| E9 | should-fix | [weakens] | core/approx boundary inconsistent (NR QM, LO QED in core; Newton out); Newtonian light is an alternative |
| E10 | should-fix | [weakens] | Bohm: conflict with relativity (nonlocality, foliation) missing; slit starts not \|Ψ\|²-distributed |
| E11 | nit | [neutral] | Lüders update both in core and in `copenhagen`; clarify ownership |
| E12 | nit | [weakens] | `certified`: two "independent" routes re-evaluate the same formula; deflection ball not rigorous |
| E13 | nit | [neutral] | pulsar/Cassini/VLBI/Bell data unused; cited basis not computed |
| E14 | nit | [error in earlier] | edge cases: near-circular advance raises, invalid Dirac j accepted, deflection at b ≳ 1e8 r_s, γ near 1, scipy pin |
| E15 | nit | [error in earlier] | CMB 5e-5 figure attributed to Mather 1994 (it is Fixsen 1996) |

### E1 (error) — hydrogen levels: the stated ~1e-6 agreement with measurement is false for both shipped functions

- Location: `lfphys/lfphys/core/quantum/hydrogen.py:8-9` (docstring "Transition frequencies from these formulas
  therefore differ from measured ones at the 1e-6 level"), `:22` (ABOUT.validity "отличие от измерений ~10⁻⁶ отн."),
  `:36-40` (`dirac_level`, infinite nuclear mass).
- What is wrong: `dirac_level` has no reduced mass / recoil, so every transition frequency it gives is off by
  m_e/m_p ≈ 5.4e-4; `schrodinger_level` has the reduced mass but no fine structure (~1e-5). Neither reaches the
  documented 1e-6. The 1e-6 level (really ~3e-6, the Lamb shift) needs the Dirac factor *with* the reduced mass and
  the leading recoil term (Barker–Glover).
- Evidence: `02_hydrogen.py` → `out/02_hydrogen.txt`. 1S–2S against Parthey et al., PRL 107, 203001 (2011)
  (arXiv:1107.3101 abstract, fetched: "f_1S-2S = 2 466 061 413 187 035 (10) Hz for the hyperfine centroid"):
  `schrodinger_level` −9.3e-6, `dirac_level` **+5.48e-4**, independent Dirac + recoil (mpmath) +2.9e-6.
  2P3/2–2P1/2 from `dirac_level`: 10 949.66 MHz vs 10 943.69 MHz with recoil (ratio 5.46e-4 = m_e/m_p).
- Fix: add the recoil-corrected Dirac level E = μc²(f−1) − μ²c²(f−1)²/(2(m+M)) (Eides, Grotch, Shelyuto, Phys. Rep.
  342, 63 (2001), Eq. 2.5) with a nuclear-mass argument, and state per function what it omits (Lamb shift ~3e-6 of
  1S–2S, hyperfine). Correct the validity text to the per-function numbers above.

### E2 (should-fix) — Klein–Nishina total cross-section is accurate to only ~4 significant digits for 1e-4 ≤ E/mc² < 1e-3

- Location: `lfphys/lfphys/core/quantum/compton.py:41-47` (`total_cross_section`).
- What is wrong: above the series switch at x = 1e-4 the closed form computes `math.log(1 + 2 * x)`; the rounding of
  `1 + 2x` (~1.1e-16 absolute in the log) is multiplied by (1+x)/x³ and compared with σ/(2πr_e²) ≈ 4/3, so the
  relative error is ≈ 1e-16/x³, i.e. up to ~1e-4 at the switch (measured 6e-5).
  The tests sample x = 1e-5 (series branch), 1e-3·mc² (numeric quad at rel 1e-6), 0.01, 1, 30 and miss the window.
- Evidence: `03_compton.py` → `out/03_compton.txt` (50-digit mpmath reference of the same closed form, 409 points):
  max rel. error 1.3e-11 for x < 1e-4, **5.9e-5** for 1e-4 ≤ x < 1e-3 (at x = 1.0e-4: 5.9e-5; 1.12e-4: 5.1e-5),
  7.0e-8 for 1e-3 ≤ x < 0.1, 7e-14 above. With `math.log1p(2*x)`: 2.5e-8 and 2.7e-10 in the two windows.
- Fix: use `log1p`, and use a longer series (σ_T(1 − 2x + 26/5 x² − 133/10 x³ + …), enough terms) up to x ≈ 1e-2,
  or evaluate the bracket 2x(1+x)/(1+2x) − ln(1+2x) by its own series for small x; add a test in the window.


### E3 (should-fix) — `interfaces.stack` and `thin_films.ftir_T` raise `OverflowError` for thick evanescent layers

- Location: `lfphys/lfphys/core/optics/interfaces.py:87-93` (`_layer`: `cmath.cos/sin(delta)` with Im δ = κd),
  `:120,126` (`abs(den)**2` overflows to inf before it), `lfphys/lfphys/core/optics/thin_films.py:138`
  (`math.sinh(kap*d)`).
- What is wrong: the physical answer for an opaque gap is T → 0, R → 1, but once κd ≳ 710 the characteristic matrix
  elements cosh(κd) overflow and the call raises; between κd ≈ 355 and 710 it emits overflow warnings and returns
  T = 0 through `inf`. A gap slider in a visualization (FTIR, a metal film of a few µm) reaches this.
- Evidence: `06_optics_stack.py` → `out/06_optics_stack.txt`: n = 1.5 | 1.0 (d) | 1.5 at 60°, λ = 633 nm:
  d = 80 µm (κd = 658) "RuntimeWarning: overflow encountered in scalar power", T = 0; d = 100 µm (κd = 823) and
  300 µm: `OverflowError: math range error` from both `stack` and `ftir_T`, s and p.
- Fix: carry the growth factor separately (normalise each layer matrix by e^{|Im δ|} and accumulate the exponent),
  or switch to the scattering-matrix (S-matrix) recursion, which is unconditionally stable; in `ftir_T` use
  `1/(1 + X)` with X formed in logs (or return 4·…·e^{−2κd} asymptotically) when κd > ~300.

### E4 (should-fix) — `transfer.transmission` overflows / `transmission_profile` returns NaN for a barrier away from x = 0

- Location: `lfphys/lfphys/core/quantum/transfer.py:34-41` (`transmission`) and `:79-91` (`transmission_profile`).
- What is wrong: the plane waves are referenced to the absolute origin (e^{±ik_j x} at the edge position x), so an
  evanescent region at |x| ≳ 700/κ overflows although T is translation invariant. `transmission` raises
  `OverflowError`; `transmission_profile` silently returns `nan` (with RuntimeWarnings).
- Evidence: `08_quantum_numerics.py` → `out/08_quantum_numerics.txt`: V0 = 1, a = 2, E = 0.5 (ħ = m = 1):
  x0 = 0…600 gives T = 0.0706508248531644(5) (closed form 0.07065082485316446); x0 = 1000:
  `transmission` → `OverflowError: math range error`, `transmission_profile` → `nan`.
- Fix: reference the waves of region j at its own left edge (local coordinate x − x_j) so each interface matrix only
  contains e^{±ik_j d_j}; for thick barriers additionally use the S-matrix recursion (as for E3).

### E5 (should-fix) — radial solver: the documented Coulomb accuracy (~1e-6 after Richardson) is not reached at the defaults

- Location: `lfphys/lfphys/core/quantum/radial.py:7-9` ("the error then falls as dr² … `richardson=True` … removes
  that term (Coulomb test: 1e-4 -> ~1e-6 relative)"), `:41` (default `N=800`).
- What is wrong: for l = 0 the extrapolated error falls only like dr³ (ratio ≈ 8 per halving), and at the default
  N = 800 (R = 100) it is 2e-4, not 1e-6. The test uses N = 1600 and rtol = 5e-5, i.e. it does not test the claim.
- Evidence: `08_quantum_numerics.py` → `out/08_quantum_numerics.txt`, −1/r, ħ = μ = 1, max over n = 1…3:
  l = 0: N = 800: 2.4e-3 → 2.1e-4 (Richardson); N = 1600: 6.3e-4 → 2.6e-5; N = 3200: 1.6e-4 → 3.2e-6.
  l = 1: 5–8e-7 at N ≥ 1600 (Richardson does not help, the cusp error is absent).
- Fix: state the measured accuracy per l and N; for 1/r potentials use a grid that resolves the origin (e.g. a
  mapped/Laguerre DVR, or r = x² substitution) or a second Richardson stage (dr³); add a test of the stated number.

### E6 (nit) — `wigner_rotation_angle`: the returned sign is opposite to the documented one; the sign is untested

- Location: `lfphys/lfphys/core/relativity.py:127-137`; tests `lfphys/tests/test_relativity_gravity.py:63-81`
  compare only `abs(th)` (the docstring of the test says "swapping the order flips the sign", which is not asserted).
- What is wrong: the docstring says lab→F2 = R(θ)B(w) with "R a rotation of the spatial axes by θ
  (counter-clockwise positive)". The code returns the angle of the *coordinate* matrix R; F2's axes, seen in the
  frame reached by the single boost B(w), are then rotated by −θ.
- Evidence: `05_relativity.py` → `out/05_relativity.txt`: u = 0.5c x̂, v = 0.5c ŷ (u×v ∥ +z): returned θ = +0.143348,
  F2's x axis seen in W at −0.143348 rad (clockwise). The finding is about code vs its own docstring; the clockwise
  sense itself is what the standard Thomas-precession result (retrograde to the turning of the velocity) leads one
  to expect — reviewer's recollection, not re-checked against a text here.
- Fix: document θ as the angle of the coordinate rotation (axes rotated by −θ, i.e. clockwise for u×v ∥ +z) or
  flip the sign; assert the sign in the test.

### E7 (should-fix) — α_s: four-loop running with leading-order (continuous) threshold matching is inconsistent; the omitted decoupling is as large as the β₃ term

- Location: `lfphys/lfphys/core/qcd/running.py:14-16` (docstring: "leading-order matching; the two-loop decoupling
  term (11/72)(alpha_s/pi)^2 is omitted, a relative change of < 1e-3 at m_b"), `:18-20` ("The truncation of the
  beta function at a given order is the theoretical uncertainty of this module (estimate it by comparing loop
  orders)"), `:86-105` (`alpha_s`).
- What is wrong: with an N+1-loop β function, consistency needs N-loop decoupling (RunDec, arXiv:hep-ph/0004189,
  p. 11: "If the evolution … is to be performed at N + 1 loops … consistency requires the matching conditions to be
  implemented in terms of N-loop formulae"). The engine runs at 4 loops but matches at LO. The omitted decoupling
  shift is of the same order as the β₃ effect (at m_b nearly equal to it) that the docstring offers as the
  uncertainty estimate, so comparing loop orders understates the error. At m_c it is 0.56 % (about a quarter of the
  PDG uncertainty of α_s(M_Z) propagated there, δα/α ∝ α: 0.76 % × 0.386/0.118 ≈ 2.5 %).
- Evidence: `09_qcd.py` → `out/09_qcd.txt`. Independent mpmath (Taylor ODE) 4-loop running with the MS-bar
  decoupling at μ = m_h(m_h), RunDec Eq. (20) (verified in the fetched text: 1 + 11/72 a² + (564731/124416 −
  82043/27648 ζ₃ − 2633/31104 n_l) a³). PDG 2024 inputs (α_s(M_Z) = 0.1180, m_b = 4.183, m_c = 1.273):
  | μ (GeV) | engine | ref, 3-loop decoupling | engine − ref (abs., rel.) | β₃ effect: engine 4-loop − 3-loop |
  |---|---|---|---|---|
  | 4.183 | 0.224568 | 0.224795 | −2.3e-4, −1.0e-3 | +2.8e-4 |
  | 2.0 | 0.301077 | 0.301507 | −4.3e-4, −1.4e-3 | +1.3e-3 |
  | 1.777 | 0.319107 | 0.319595 | −4.9e-4, −1.5e-3 | +1.7e-3 |
  | 1.273 | 0.386189 | 0.388356 | −2.2e-3, −5.6e-3 | +4.0e-3 |
  The engine with LO matching reproduces the reference with LO matching to all printed digits (the threshold walk
  itself is right).
- Fix: apply the decoupling relation at each threshold (downward Eq. 20 / upward Eq. 23 of RunDec at μ = m_h(m_h),
  three loops for four-loop running), and state the residual (matching-scale dependence) as the uncertainty.

### E8 (should-fix) — a refuted kinematics lives in the core: the emission-theory light front in `core.gravity.arrivals`

- Location: `lfphys/lfphys/core/gravity/arrivals.py:6-7` ("flat, SR or ether … flat, emission: |x_R(t) − origin −
  w (t − t0)| = c (t − t0) (front centred on the moving source)"), ABOUT.statement `:32-35` ("…или, по выбору набора
  законов, на движущемся источнике"), `front_arrival(c, t0, origin, w, …)` `:42`; also `core/gravity/rays.py:9-10`
  (docstring lists ether and emission), `core/worldlines.py:11` ("Galilean: dtau/dt = 1").
- What is wrong: LAYERS.md admits to the core only laws of accepted physics; emission (Ritz) kinematics is refuted
  (the module `theories.alternatives.kinematics` says so itself). The core still states and computes it as one of its
  own results, selected by a parameter `w` that `laws.light.Laws.front_velocity` sets for the emission world.
  `tests/test_layers.py::test_core_imports_only_core` cannot catch this because nothing is imported.
- Evidence: `13_layers.py` → `out/13_layers.txt` part (1) lists the lines.
- Fix: keep in the core only the SR front (w = 0); move the moving-centre front into
  `theories.alternatives.kinematics` (it may call a neutral geometric helper "first meeting of a worldline with a
  sphere of radius c(t − t0) about a moving centre" placed in `core.numerics`, documented as geometry, not physics);
  same for the docstrings of `rays.py` and `worldlines.py`.

### E9 (should-fix) — the core/approximation boundary is applied inconsistently; Newtonian light is filed as an "approximation"

- Location: `lfphys/LAYERS.md` §1 (approx = "controlled approximations with a domain of validity: Newtonian gravity,
  paraxial and ray optics, weak-field expansions"); core modules `quantum/schrodinger1d.py`, `quantum/radial.py`,
  `quantum/transfer.py` (non-relativistic limit), `quantum/compton.py` (lowest-order QED), `quantum/hydrogen.py`
  (Dirac without QED), `quantum/scattering.py` (dipole approximation), `quantum/marks.py` (paraxial polarisation);
  `theories/approx/newton.py:23-32` (kind "approximation", `:24`).
- What is wrong: (a) Newtonian gravity is moved out of the core as an approximation of GR, while the non-relativistic
  Schrödinger equation, lowest-order QED and the Dirac equation without radiative corrections — controlled limits
  of a deeper accepted theory with known, measured corrections, i.e. the same epistemic status — are in the core.
  Their own validity texts say so (`out/13_layers.txt` part (2)): "нерелятивистская частица", "поправки КЭД высших
  порядков ~α/π", "без лэмбовского сдвига", "дипольное приближение", "в параксиальном приближении". The Dirac level
  predicts 2S1/2 = 2P1/2 exactly, which the Lamb shift (1057.8 MHz, quoted in the module docstring) contradicts; the
  module declares the omission, i.e. by its own text it is an approximation, like Newtonian gravity. (b) For light, the Newtonian corpuscle is not a controlled approximation: it
  is off by a factor 2 at every impact parameter (its own ABOUT: "противоречит наблюдениям") — that is a refuted
  alternative, not an approximation with a domain of validity.
- Evidence: `13_layers.py` → `out/13_layers.txt`; `02_hydrogen.py` (E1).
- Fix: make the rule explicit and uniform, e.g. core = accepted theory *or a controlled limit of it*, each function
  with a stated error bound against the fuller theory (then Newtonian gravity of slow bodies with its O(GM/(c²r))
  bound could equally stay); or move all limits to `theories/approx`. In either case split `newton.py`: the light
  part (Soldner corpuscles, emission kinematics) to `theories/alternatives`, the slow-body Kepler part to
  `approx` (or core under the uniform rule).

### E10 (should-fix) — de Broglie–Bohm: the declared conflicts omit the conflict with relativity, and the slit trajectories do not start |Ψ|²-distributed as the ABOUT states

- Location: `lfphys/lfphys/theories/interpretations/bohm.py:16-24` (ABOUT: "начальные положения распределены по
  |Ψ|²"; conflicts (`:23`) list only Copenhagen and Everett), `:27-42` (`slit_trajectories`: starts uniform across
  each slit on ±0.48a at z0 = 2a, `:39`, `:42`).
- What is wrong: (1) The best-known tension of Bohmian mechanics is with the core's relativity: the guidance law
  for entangled many-particle states is explicitly nonlocal and needs a preferred foliation of space-time (no
  Lorentz-invariant trajectories), although its predictions agree with the core (standard in the literature, e.g.
  Bell's papers collected in *Speakable and Unspeakable in Quantum Mechanics*; reference not re-fetched here). This
  is precisely the kind of "несоответствие" the owner asked to be recorded. (2) The slit routine does not sample
  |Ψ(x, z0)|²: at z0 = 2a the paraxial field in a slit is strongly rippled.
- Evidence: `12_misc.py` → `out/12_misc.txt` (λ = 633 nm, single slit, the engine's own `paraxial.slit_amplitudes`):
  a = 5 µm: |Ψ|² varies by ×7.9 inside the start window, 10.7 % of |Ψ|² lies outside ±0.48a, Kolmogorov–Smirnov
  distance of the uniform start from |Ψ|² = 0.081; a = 20 µm: ×4.3, 6.2 %, 0.045; a = 100 µm: ×3.6, 3.7 %, 0.014.
  (The 1-D routines `advance_1d`/`quantile_positions` are fine: equivariance is tested.)
- Fix: add the relativity/nonlocality conflict (pointing to `core.relativity`, `core.causality`); place the start
  points by the inverse CDF of |Ψ(x, z0)|² summed over slits (as `quantile_positions` does in 1-D).

### E11 (nit) — the Lüders state update is in the core and again in `copenhagen`; say which layer owns it

- Location: `lfphys/lfphys/core/quantum/qubits.py:5,64-71` (`measure(..., rng)` returns Π_k ρ Π_k / P(k)),
  `lfphys/lfphys/theories/interpretations/copenhagen.py:1-3,21-27` ("…the state is replaced by the projected state
  (collapse). It adds no prediction to the core's Born rule").
- What is wrong: the same projection is offered as core physics and as the content of the Copenhagen
  interpretation. Operationally the conditional (Lüders) state is shared by all interpretations (Everett: the
  relative state of the branch; Bohm: the effective wave function), so it can stay in the core, but then the
  core docstring should say "conditional state for later predictions (interpretation-neutral)" and `copenhagen`
  should say that what it adds is the reading (a physical collapse), not a different computation.
- Evidence: code reading (both functions return Π_k ψ/‖Π_k ψ‖ for a pure state).
- Fix: wording only.

### E12 (nit) — `certified`: two "independent routes" are re-evaluations of the same closed form, and one ball is not a rigorous enclosure

- Location: `lfphys/lfphys/core/certified.py:6-12` ("Independent routes, not re-evaluations of the same float code:
  periapsis advance: the elliptic integral K in Arb; … Dirac levels"), `:46-54` (`periapsis_advance`), `:137-143`
  (`dirac_level`), `:64-74` (`schwarzschild_deflection`: `u0 = arb(u0.mid())` after each Newton step);
  tests `lfphys/tests/test_certified.py:19-23, 82-85`.
- What is wrong: (1) the Arb periapsis advance and Dirac level evaluate exactly the formula the float code
  evaluates; they certify the floating-point evaluation (useful: the weak-field cancellation), not the physics. The
  independent physics checks are elsewhere (`test_periapsis_advance_elliptic_vs_quadrature`, the Sommerfeld
  expansion test). (2) In `schwarzschild_deflection` the turning point is refined on midpoints and its radius is
  discarded, so the returned ball encloses the deflection for an impact parameter b′ with
  1/b′² = u0² − r_s u0³, not for the given b. The difference is ~2⁻¹²⁸ relative (numerically irrelevant), but the
  module's claim "a ball [m ± r] contains the exact value" does not hold for this function.
- Evidence: code reading; numerically the float results are right (`04_gravity.py`: advance_from_turning vs the
  defining integral 1e-17…4e-10; deflection 1e-15…1e-10 for b/r_s ≤ 1e7).
- Fix: relabel these two as "float-evaluation certificates"; for the deflection, enclose u0 by an interval Newton
  step (Krawczyk) and keep its radius.

### E13 (nit) — reference data that no code uses; experimental "basis" items are not computed anywhere

- Location: `lfphys/lfphys/core/data.py:66-72` (`CASSINI_GAMMA_MINUS_1`, `VLBI_GAMMA_MINUS_1`,
  `PSR_B1913_PERIASTRON_DEG_PER_YR`, `PSR_B1913_PBDOT_RATIO`, `HENSEN_2015_S`); `core/gravity/orbits.py:36-38`
  (ABOUT.basis cites the PSR B1913+16 periastron advance).
- What is wrong: `grep` over the project finds no use of these constants outside `data.py`; the binary-pulsar
  numbers would need two-body (1PN periastron advance with M_total) and radiation-reaction (Peters–Mathews Ṗ_b)
  formulas, which the engine does not have, so the cited "basis" of `orbits` is not checked by any test.
- Evidence: `grep -rn "PSR_B1913\|CASSINI_GAMMA\|VLBI_GAMMA\|HENSEN_2015_S"` → only `data.py`.
- Fix: either add the two-body 1PN advance and the quadrupole Ṗ_b (then test against the stored values) or drop the
  unused constants and say in `basis` that the pulsar tests GR's two-body dynamics, not the test-particle orbit.

### E14 (nit) — small numerical edge cases

- `core/gravity/orbits.py:69-99` `periapsis_advance(e, l)` and `elements(e, l)`: for a nearly circular orbit np.roots
  returns the double root as a complex pair (|Im| above the 1e-12 cut) and the call raises "not a bound orbit",
  although the limit 2π/√(1−6M/r) − 2π is regular (`12_misc.py`: r = 10 M, ε = 1e-8 raises; ε = 1e-6 gives
  3.6514029586 = limit). `orbit_stream` already uses a looser cut (1e-6) plus Newton polishing; use the same here.
- `core/quantum/hydrogen.py:36-40` `dirac_level(n, j)` accepts j > n − 1/2 (`dirac_level(1, 1.5)` returns
  −2.18e-18 J); raise instead.
- `core/gravity/schwarzschild.py:267-274` `deflection_from_quadrature`: 2Δφ − π cancels; relative error 1.1e-11 at
  b = 1e5 r_s, 9.3e-11 at the solar limb (2.36e5 r_s), 1.3e-10 at 1e7 r_s, 1.4e-7 at 1e9 r_s (`04_gravity.py`).
  Fine for the Sun; state the range or integrate the deflection directly (e.g. the regularised integrand of
  `certified.schwarzschild_deflection` minus its flat-space part).
- `core/relativity.py:27-31` `gamma`: 1 − β² in float; relative error up to 2.8e-10 near β = 1 − 1e-8
  (`05_relativity.py`); (1 − β)(1 + β) gives ≤ 1e-16.
- `lfphys/pyproject.toml`: `scipy>=1.13` admits scipy < 1.15, which ships CODATA 2018 (constants differ by
  1e-9 relative, e.g. m_e 1.4e-9, α 6.9e-10, `01_constants.py`); the docstring relies on "the pinned scipy"
  (the Docker image has scipy 1.17.1 = CODATA 2022). Pin `scipy>=1.15` or assert the CODATA edition at import.

### E15 (nit) — black-body module: the 5·10⁻⁵ CMB figure is attributed to the wrong FIRAS paper

- Location: `lfphys/lfphys/core/optics/radiation.py:23-24` (validity "спектр реликтового фона — планковский с
  точностью 5·10⁻⁵ (COBE/FIRAS)", basis "Mather et al., ApJ 420, 439 (1994)").
- What is wrong: Mather et al. 1994 give "deviations … less than 0.30% of the peak brightness, with an rms value of
  0.01%" (NASA NTRS record 19950040015, abstract, fetched 2026-10-23). The 50-ppm figure is Fixsen et al., ApJ 473,
  576 (1996), arXiv:astro-ph/9605054 (abstract, fetched): "The RMS deviations are less than 50 parts per million of
  the peak of the CMBR."
- Fix: cite Fixsen et al. 1996 for 5·10⁻⁵ (rms, relative to the peak), or quote Mather 1994's 1e-4 rms.

## Missing physics (secondary; by priority)

1. **High.** Hydrogen-like atoms with recoil (reduced-mass Dirac, Barker–Glover) and the leading QED terms (Lamb
   shift, hyperfine/21 cm) — without them no hydrogen line is "very accurate" (E1).
2. **High.** QCD: threshold decoupling to three loops (E7); running quark masses m_q(μ) and Λ_MS-bar(n_f) —
   needed whenever α_s or the Cornell/heavy-quark sector is compared with data.
3. **High.** GR beyond test-particle orbits in the equatorial plane: two-body 1PN periastron advance and the
   quadrupole orbital decay (the PSR B1913+16 numbers in `data.py` are otherwise unused, E13); exact Shapiro delay
   and gravitational redshift in Schwarzschild (only PPN expansions exist, in `theories`); Kerr null geodesics /
   shadow (the Kerr ABOUT cites EHT, the module has equatorial circular orbits only).
4. **Medium.** Optics: material dispersion (Sellmeier/Drude–Lorentz with Kramers–Kronig-consistent n(λ)),
   anisotropic layers (4×4 Berreman), vector/3-D diffraction and Mie scattering, partial coherence.
5. **Medium.** Quantum: driven two-level dynamics (Rabi, optical Bloch equations with T1/T2), partial-wave 3-D
   scattering, Zeeman/spin–orbit; decoherence models (they would also give the GRW alternative a core baseline).
6. **Low.** SR in 3+1 dimensions (the core is 2+1), charged-particle motion in fields and spin precession (BMT,
   which would turn the Wigner rotation of E6 into an observable Thomas precession).

## Verified correct

Each item: what was checked, by which route, and the precision reached.

- **Constants** (`01_constants.py`): the image's scipy 1.17.1 ships CODATA 2022 (α, m_e, m_p, m_n, u, r_e, R∞, G,
  σ_T equal to CODATA 2022 to all digits; CODATA 2018 differs by ~1e-9). IAU 2015 B3 nominal values and the exact
  AU (IAU 2012 B2) match.
- **PDG 2024 data** (`11_pdg_spotcheck.sh`, independent anonymous download of the PDG 2024 summary tables):
  m_c(m_c) = 1.2730 ± 0.0046, m_b(m_b) = 4.183 ± 0.007, m_t direct 172.57 ± 0.29, m_t from σ 162.5 (+2.1 −1.5),
  M_Z = 91.1880 ± 0.0020 GeV and all 16 quarkonium masses in `data.py` agree with the tables character by
  character. (α_s(M_Z) = 0.1180 ± 0.0009 not re-fetched here; it is consistent with the RunDec-level check below.)
- **Schwarzschild periapsis advance** (`04_gravity.py`, 40-digit mpmath quadrature of the defining integral):
  `advance_from_turning` rel. error 1e-17…1e-15 (r ≲ 1e3 M), 9e-13 (r ~ 1e5 M), 4.2e-10 for Mercury (the documented
  float cancellation); `periapsis_advance(e, l)` the same except near-circular orbits (E14).
- **Light deflection** (`04_gravity.py`, mpmath, independent turning point): `deflection_from_quadrature` 1.9e-12 at
  b = b_c(1 + 1e-6), ≤ 1e-14 for 2.6 ≤ b/r_s ≤ 50, 9e-11 at the solar limb.
- **Kerr** (`04_gravity.py`): ISCO located independently as dE/dr = 0 with (E, L) solved numerically from R = R′ = 0
  (no closed form used): rel. error ≤ 2.4e-16 for χ = 0, 0.5, 0.9, 0.998, pro- and retrograde; efficiencies agree
  to 12 digits (e.g. 0.320994165616 at χ = 0.998 prograde).
- **Hankel functions** (`07_hankel_kernels.py`, mpmath J + iY): max rel. error 6.3e-16 (ν = 1) and 4.8e-16 (ν = 0)
  over x ∈ [1e-3, 1e12], including both sides of the 1e4 switch — far better than the documented 1e-10.
- **Rayleigh–Sommerfeld kernel**: the plane-wave identity ∫K dx′ = e^{ikz} holds to 1.3e-10 (limited by the
  reviewer's tapered aperture), confirming sign and normalisation.
- **Paraxial slit closed form** (theories): ≤ 4.6e-14·a against mpmath quadrature of the defining integral
  (near and far field, point source with kick).
- **Multilayer optics after the Abelès rewrite** (`06_optics_stack.py`): 2000 random stacks (0–5 layers,
  absorbing and lossless, incidence up to 89.9°, evanescent layers), s and p, against an independent
  boundary-value solution with Poynting-flux T: max |Δr| 3.9e-13, |Δt| 8.5e-14, |ΔR| 6.7e-13, |ΔT| 8.0e-14. Born &
  Wolf p sign confirmed (1 → 1.5, normal incidence: r_s = −0.2, r_p = +0.2). `ftir_T` agrees with the reference to
  ≤ 1e-10 off the critical angle and with `stack` exactly at θ_c (T_s = 0.265177915502342, T_p = 0.646258464852599;
  the closed-form value at κ = 0 checked by hand: 1/(1 + (k_z d/2)²) = 0.2652 for s).
- **Split-operator Schrödinger** (`08_quantum_numerics.py`, quartic oscillator against a dt/16 reference): global
  error ratio 4.00 per halving (second order, as stated). **Sinc-DVR**: harmonic levels to ≤ 4e-14 with 64–128
  points (exponential convergence, as stated).
- **Transfer matrices** near the origin: rectangular barrier T = 0.07065082485316448 vs closed form
  0.07065082485316446; T + R − 1 ≤ 4e-16.
- **α_s running** (`09_qcd.py`): with n_f = 5 fixed and α_s(91.18) = 0.118 the engine reproduces RunDec's
  AlphasExact (Table 1(c) and Out[2]/Out[6]) at 1, 2, 3 and 4 loops: α_s(4.7) = 0.2059144 / 0.2160558 / 0.2167125 /
  0.2169467 (RunDec 0.2059 / 0.2161 / 0.216712 / 0.2169467), α_s(1 GeV) = 0.3369 / 0.3965 / 0.4029 / 0.4065 (all
  equal). β₀…β₃ therefore correct; the threshold walk with LO matching equals an independent mpmath integration to
  6 digits.
- **Cornell model** (`10_cornell.py`, independent shooting solution, DOP853 + node counting): engine levels (sine
  DVR, N = 700) equal the shooting eigenvalues to < 1 keV (charmonium) and ≤ 6 keV (bottomonium). Charmonium
  2S−1S = 590.7 MeV vs 605.3 MeV spin-averaged PDG (−2.4 %), 1P−1S = 428.4 vs 456.6 MeV (−6.2 %); bottomonium
  2S−1S +2.3 %, 1P−1S +9.6 %, 3S−1S +2.9 % — the module's numbers ("591 vs 605", "2–10 %") are right. (Remark:
  for bottomonium 2S and 3S only the Υ states are in `data.py`, so "spin-averaged" there means Υ(nS) alone;
  `spin_averaged` documents that it averages over the states present.)
- **Formulas checked by derivation** (no finding): Lorentz boost, velocity composition, aberration, Doppler factor,
  Schwarzschild clock rate; null-geodesic quadratures and the r = r_tp + s² regularisation; turning point
  (trigonometric cubic root); static-frame direction conversions (E = 1 normalisation); timelike f(u), u″, dt/dφ,
  dτ/dφ, the scaled Binet system and the Christoffel symbols of `geodesic_tau`; radial infall r̈ = −M/r²; Kerr
  r_±, ergosphere, r_ph, r_mb, ISCO, E and L of circular orbits, R(r) and its derivatives; Fresnel s/p (B&W),
  Abelès matrices for e^{−iωt} with the sinc form, p power factor Re(n cos θ*); Airy sum and intensity formula;
  quarter-wave stack admittance; FTIR s/p factors (a² + b²)/(2ab) with b = κ/n_gap² for p; Joule absorption
  k₀ Im(n²)∫|E|²/Re(n₀cosθ₀); Planck, Wien (Lambert W), σ; Klein–Nishina dσ/dΩ and σ_tot closed form; Dirac
  fine-structure formula; Colbert–Miller kinetic matrix; Wootters concurrence; Gell-Mann matrices and f, d
  definitions; GRW kick distribution N(0, 1/(2r_C²)) and the shift characteristic function √π erf(a)/(2a); the
  dipole-pattern marginal f(u) used by `paraxial_ensemble`; Gaussian-beam q parameter; PPN deflection, one-way
  Shapiro delay and periapsis factor (2 + 2γ − β)/3; Brans–Dicke γ; local-hidden-variable E(θ) of both models.
- **Tests**: the suite passes (280 tests, `out/00_pytest.txt`). Most tests compare against an independent route;
  the exceptions are listed in E12 (float vs Arb of the same formula) and the untested sign in E6.
