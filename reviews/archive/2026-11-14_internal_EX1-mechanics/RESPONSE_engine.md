# Response to R-E (EX1-mechanics): the engine and statistics part (QE, 2026-11-17)

This file covers the findings the integrator assigned to the engine (`PROCESS_BRIEF` 2026-11-17): F2, F3, F5 (decision
D3), F6 (the engine's texts), F7, F8 and F10. It also covers the engine support for F1 (decision D1). F1's world side,
F4, F6's README numbers and F11 are answered in `RESPONSE_worlds.md`; F9 is in `RESPONSE_player.md`.

Every number below was re-measured or re-derived here before use (AGENTS rule 11). Engine tests run in Docker
(`lfphys-viz`, `--memory` capped, containers `lf-qe-*`).

| # | summary | decision | files | verified by |
|---|---|---|---|---|
| F1 (engine side) | a second drag model is needed: the measured C_d(Re) as a declared force | **fixed (engine part)**: `CurveDrag` | `theories/models/drag_quadratic.py` | `test_curve_drag_*` (4 tests, below) |
| F2 | the Lambert-W landing time loses accuracy as ~1e-16/s², not 1e-16/s | **fixed** [error in earlier]: Newton polish; docstring and design corrected | `core/mechanics/drag.py`; design §4 table | `test_lambert_landing_time_is_exact_also_for_weak_drag` (28 cases) |
| F3 | Stokes's law states the unsteady forces as O(ρ_f/ρ_p); the Basset force is O(√(ρ_f/ρ_p)) | **fixed** [error in earlier]: the text and ABOUT state both sizes, computed | `core/mechanics/drag.py` (+ ru) | `test_the_stated_size_of_the_history_force` |
| F5 | the effective variance is not the least-squares line and is inconsistent with random x errors | **fixed** (D3): York (2004) for the straight lines; the effective variance kept for the parabola only, stated as an approximation | `tools/stats.py`, `codes.py`, design §2.3 and §4 (dated notes), `lfphys/README.md`; the spec for fit.js | `test_stats_fit.py` (31 tests) |
| F6 (engine texts) | "the constant 0.47 errs by up to −18 % / +7 %" has the wrong sign and base | **fixed** [error in earlier]: "+21 % / −7 % of the measured value" | `drag_quadratic.py` docstring and ABOUT, engine `ru.json` | `test_i18n_engine` |
| F7 | "1e-9 relative in the range" fails for near-vertical throws | **fixed**: the error of lengths is stated against the flight's length scale | `core/mechanics/particle.py` (+ ru), `lfphys/README.md` | `test_a_near_vertical_range_is_accurate_to_the_flight_s_length_scale` |
| F8 | `linear_fit` does not refuse a singular design | **fixed**: the same QR test as fit.js; a translatable refusal with the code `fit.singular` | `tools/stats.py`, `codes.py` | `test_a_singular_design_is_refused` (5 designs × with/without errors), `test_codes::test_fit_codes` |
| F10 | `linear_drag_landing_time` refuses c ≤ 0, where its formula is exact | **fixed**: the refusal is removed | `core/mechanics/drag.py` (+ ru: the msgid removed) | `test_lambert_landing_time_downwards_beyond_the_terminal_speed` |

## Details

### F1, engine side: `CurveDrag` [useful]

- **What.** `drag_quadratic.CurveDrag.sphere(d, medium=None, curve=None)` is F = −½ρ·C_d(Re)·A·|v|·v.
  - C_d is `cd_standard` (Morrison 2016, eq. (1), 0 < Re ≤ 10⁶), taken at the body's own Re at every instant.
  - It has the interface of `QuadraticDrag` (`force`, `reynolds`, `label`) plus `cd_at(speed)`.
  - At Re ≪ 1 it is Stokes's law.
  - Re > 10⁶ is refused.
- **Overflow fix.** `cd_standard`'s third term was rewritten from a^−7.94/(1 + a^−8) to a^0.06/(1 + a^8). This is the
  same number, without the overflow at Re < 1e-36.
- **ABOUT.** The statement and the validity name the curve, its range and its source.
- **Tests.**
  - Radau IIA (rtol 1e-13) with Morrison's formula written out independently, in 6 cases including a roll-off that
    starts at Re = 222. T, L, H agree within 2e-11; the 1.6 cm range of the roll-off within 3e-10.
  - A constant curve against `QuadraticDrag` (to round-off) and against the hodograph.
  - The Stokes limit at Re = 1e-6.
  - The review's independent numbers: 28.2371 m (20 m/s, 40°) and 37.8905 m (25 m/s, 45°) against 27.2222 m and
    36.2338 m with the constant.
- **Who uses it.** The world's check and the optimum comparison are QW's (`RESPONSE_worlds.md`).

### F2: the weak-drag landing time [error in earlier]

- **The review is confirmed.** With W alone, the relative error grows as 1e-16/s²: 2e-9 to 1e-8 at k = 1e-4 1/s and up
  to 7.3e-7 at k = 1e-5 1/s, against a 50-digit bisection. These are the review's numbers.
- **The fix.** Newton's method on f(s) = h′ + c₁(1 − e^{−s}) − (s − (1 − e^{−s})), with c₁ = v_y0/(gτ) formed
  directly and the last bracket by its series.
  - f is concave for c > 0 and convex for c < 0, and decreasing at the landing.
  - So iterates converge monotonically from k·T_vacuum, which is used as the start when W's value is not on the
    descending branch.
- **Measured.** ≤ 7.8e-16 relative in all 28 cases, k = 3 … 1e-5 1/s, h = 0, 2 and 10 m, upward, level and downward
  launches.
- **Texts.** The docstring now states the old error and the polish. The design's §4 table row has a dated note.

### F3: the unsteady forces left out of Stokes's law [error in earlier]

- **The review's set-up re-derived.**
  - The Maxey–Riley history term is 6a²√(πμρ_f)∫(dv/ds)/√(t − s) ds.
  - In units of τ_p and gτ_p its coefficient is (3/2)√(2/π)·√R = 1.197√R, with R = ρ_f/ρ_p.
  - It was integrated independently by product integration: implicit in the newest step, steps 2e-3, 1e-3 and 5e-4,
    all agreeing to 3 digits.
- **Results at t = τ_p.**
  - Steel in air: the speed is 1.440 % below the steady law (1.42 % from the history term alone).
  - A water droplet: 4.035 % (3.89 %).
  - At 6τ_p the distance fallen is 1.163 % and 3.280 % short.
- **The texts.**
  - The module docstring now gives the equation, the numbers, the t^(−1/2) decay and the source (Maxey & Riley 1983,
    not read; the coefficient was derived from its stated form).
  - The ABOUT validity, with ru, says: added mass and buoyancy ~ρ_f/ρ_p; the Basset history force ~√(ρ_f/ρ_p) while
    accelerating, 1.4 % for steel and 4 % for droplets.
  - The droplet test's docstring now says it checks the law, not the droplet's real fall.
- **Not done.** The history force as a declared force (the review's second option) is a new feature. Proposed for
  STATUS (below).

### F5: York's line (decision D3) [error in earlier]

- **Verified on the paper.** York, Evensen, Martínez López & De Basabe Delgado, Am. J. Phys. 72, 367 (2004), was read
  on 2026-11-17 from the AIP PDF (a course copy, downloaded outside the repository; quotations in the QE notes).
  - Table I gives W_i, X̄, U_i, V_i, β_i and S.
  - Eqs. (13a)–(13d), the iteration steps (1)–(10) of §III ("one part in 10^15") and cov(a, b) = −x̄σ_b² (§II).
  - Table II, data set 3 (Pearson's data with York's weights): S/(n − 2) = 1.483, a = 5.47991, b = −0.480533. The
    analytic σ_a = 0.294970 and σ_b = 0.057985 follow from the table's Monte Carlo σ and its Δ.
  - The implementation reproduces these: a = 5.479910, b = −0.480533, σ_a = 0.294971, σ_b = 0.057985,
    S/(n − 2) = 1.4833, in 9 iterations.
- **What changed in `linear_fit`.**
  - `line`, `line0` and `power` (a line in log–log) use York's eqs. (13) with r_i = 0, iterated to |Δb| ≤
    1e-14·(|b| + √(ΣWV²/ΣWU²)), at most 200 iterations. Otherwise the code is `fit.no_convergence`.
  - `line0` uses the same equations with the intercept fixed at 0: X̄ = Ȳ = 0, σ_b² = 1/ΣW·x̂². This is derived here,
    not taken from the paper:
    - the stationarity of S(b) is York's b with U = X, V = Y;
    - σ_b is the inverse profiled Fisher information.
  - `quadratic` keeps three re-weightings of the effective variance. It is stated as an approximation in the code, the
    ABOUT, the README and the design.
  - The output gains `method` ("york" / "effective_variance" / "ols") and `iterations`.
- **Tests.** `test_stats_fit.py` has 31 tests:
  - the Pearson–York benchmark to the printed digits, and cov(a, b) = −x̄σ_b²;
  - York = the minimum of S: Nelder–Mead on Pearson–York, and a scalar search on 50 random sets for line and line0;
  - the closed form of the major axis for equal errors (line and line0);
  - the parabola's effective variance against the normal equations;
  - NIST StRD Norris, NoInt1 and Pontius, unchanged;
  - power = York on the logs;
  - Monte Carlo coverage: 95.0 % with x errors (20 000 sets). The review's attenuation cases, which the effective
    variance covered at 54 % and 36 %, now give median slope 1.994 and 2.004 against the true 2, with coverage 93.4 %
    and 91.5 %. `line0` gives 2.005 and 94.6 %;
  - line0's σ_b against Monte Carlo around the adjusted points (York's Appendix E): ratio 0.9994.
- **The player.**
  - The exact spec for `fit.js` (QP) is `lfphys/sources/verification_2026-11-17_york_fit.md`. It covers the start, the singular test,
    the iteration, the convergence rule, the final pass, the OLS fallback, χ² and Birge, and fixture notes.
  - The parity fixture must be regenerated by QP with the new Python.
- **S03.** The review measured S03 as not affected (≤ 0.001 σ). The S03 tests pass with York (see the test list at
  the end).

### F6, engine texts [error in earlier]

The constant's error is now stated as **+21 % / −7 % of the measured value**, i.e. (0.47 − 0.387)/0.387 and
(0.47 − 0.504)/0.504. It appears in `drag_quadratic.py` (docstring and ABOUT validity) and in the engine's `ru.json`.

The same figure in `visualizations/locales/ru.json` and the S03 READMEs, and the buoyancy ratio 3.3e-3, are QW's
(`RESPONSE_worlds.md`). The engine's own text now also gives the buoyancy ratio 3.3e-3 of the 67 mm, 58 g ball.

### F7

- **The new statement** (docstring and ABOUT validity, with ru): 1e-9 relative in times and the energy balance; 1e-9 of
  the flight's length scale max(h, v₀²/g) in lengths.
- **Re-measured** against the hodograph at 25 m/s:
  - relative to L: 1.04e-9 at 88°, 1.74e-8 at 89.9°, 1.38e-7 at 89.99°;
  - relative to v₀²/g: 3–4e-11.
- **Test.** The new test asserts the scale-relative bound at all three angles.

### F8

- **The refusal.** `_wls` refuses |R_jj| ≤ 1e-14·|R_00| on the column-scaled design, as fit.js does. The refusal is
  a `ValueError` with a T text and the code `fit.singular`; both are added to `CODES` and to the frozen list.
- **Every model is covered.** The start fit of every model goes through `_wls`, so York's path is covered too.
- **Tests.** The tests cover all x equal (line, power), x = 0 throughout (line0), a parabola on two distinct x, and
  x equal to 1e-15. Each is refused with and without errors.

### F10

The c ≤ 0 refusal and its msgid are removed.
- c = 0 gives T = h/v_t exactly.
- c < 0 agrees with the 50-digit reference to round-off and with DOP853 within 1e-9.

## Open points for the integrator (proposed STATUS lines)

- **F3 follow-up.** Basset's history force as a declared force for creeping-flow worlds. Not needed by S03, whose
  balls are in the quadratic regime.
- **D3 follow-up.** A York-type minimum of S for the parabola, e.g. a Newton step on S as the review suggested. Today
  the parabola keeps the stated effective-variance approximation.

## Tests run

All in Docker, CPU, `--memory` 4g:
- `test_stats_fit.py`: 31 passed.
- `test_mechanics_projectile.py`, `test_mechanics_air.py`, `test_layers.py`, `test_codes.py`, `test_i18n_engine.py`,
  `test_boundary.py`: 486 passed together with `test_stats_fit.py`.
- The full engine suite (`lfphys/`, `LFPHYS_NO_GPU=1`): **2152 passed, 23 skipped** (28 min). After the last
  docstring edits the touched files were re-run: 499 passed.
- `visualizations/s03_projectile/tests` and `u32_double_slit/tests/test_u32_physics.py`: 114 passed, 1 failed. The
  failure is u32's bootstrap test at 100 hits, below the new threshold (R-W F2, `RESPONSE_engine.md` there).
- `visualizations/tests/test_i18n.py`: 88 passed, 2 failed. Both failures come from S03's registry validation
  ("worksheet: variant 'grade7': unknown fields ['goals']"), work in progress of the worlds/framework, not the engine.
