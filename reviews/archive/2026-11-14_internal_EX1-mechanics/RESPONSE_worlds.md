# Response to review R-E (EX1-mechanics), part "worlds": S03's use of the mechanics and the fit

**Responder:** QW, the processing agent for the worlds `s03_projectile` and `u32_double_slit` (containers `lf-qw-*`,
private port 8707). It wrote neither the review nor the code under review. **Date:** 2026-11-17.

**Scope.** The findings of this review that concern the world S03, under the integrator's decisions D1, D2 and D4
(`PROCESS_BRIEF.md`): F1 (D1), F4 (D2), F6 (the README's numbers) and F11 (a test of the worksheet's numbers). The
engine's side of F1 (the measured-curve drag `drag_quadratic.CurveDrag`), F2, F3, F5, F6 (the engine's texts), F7, F8
and F10 are QE's (`RESPONSE_engine.md`); F9 (the verdict, D4) is QP's and QF's; this part declares S03's laws in QF's
D4 schema.

**Counts:** 4 findings: 4 fixed. None rejected.

**Environment.** Image `lfphys-viz` (Python 3.11), CPU (`LFPHYS_NO_GPU=1`), the repository mounted read-only for the
tests; the recordings and atlases built into the agent's scratch folder (`site/record.py --out`), served by a private
server on 127.0.0.1:8707; Playwright 1.58.2 Chromium.

| # | finding | outcome | where | test |
|---|---|---|---|---|
| F1 | the C_d "validity" check cannot fail on S03; the model's real error is not shown where it matters | **fixed** (D1) [weakens → resolved]. (1) The check is now «the drag model's range of validity (Re)»; its note says what it tests: where the model uses its constant (the share of the drag's work outside 10³–2·10⁵), «not how close its constant is to the measured C_d (the next row)». (2) Next to it every air flight carries a computed information row, «range with the measured drag curve» (a vertical throw: «flight time with the measured drag curve»): the same launch flown by the engine with QE's `CurveDrag` (C_d(Re) of Morrison 2016 at every instant), against the world's range, with the difference in % and the curve's C_d along the path. Reproduced: 28.2371 m against 27.2222 m at 20 m/s and 40° (+3.73 %), 37.8905 m at 25 m/s and 45°. (3) Lab part 3's reference says plainly that the optimum depends on the drag model: «… the constant C_d = 0.47: … 41.9° … with the measured drag curve the same search gives 42.3° …», both computed (`optimum_angle(…, curve=True)`); the verdict stays against the world's model (41.9°). The teacher's note says the same. The schema's help and the header's approximation no longer say «its validity is checked along the path» but «the run compares it with the measured drag curve» | `s03_projectile/engine/shot.py` (`curve_flight`, `optimum_angle(curve=)`), `s03_projectile/viz.py` (`_flight_checks`, `lab_reference`, `WORKSHEET`), `locales/ru.json`, `README.md`, `README.ru.md` | `test_s03_physics.py::test_the_drag_model_is_checked_where_it_is_used_and_compared_with_the_measured_curve` (the review's 28.2371 / 27.2222 m; the note's % equals the values'; a vertical throw compares T); `::test_lab_reference_of_every_law_against_an_independent_computation` (41.9° against the hodograph's Brent maximum; 42.3° against a bounded search over `CurveDrag` flights) |
| F4 | lab part A: the stated reason the law agrees is false; the agreement rests on a declared error the bench does not have | **fixed** (D2). The heights are set exactly: a new instrument «Height scale of the stand» with error 0 («the stand sets the chute's height exactly at its marks: the height has no reading error»); the tape measures L. With σ_h = 0 the bench resolves the air: air on, k = 0.676920 ± 0.000157 against 0.677401 (z = −3.07, the review's number reproduced); so part A now runs **without air**, like part B (integrator's acceptance, with the condition that the student sees it: the goal says «In this part the air is switched off, so the law L ∝ √h can be checked exactly; how much the air would change the range is computed below, and part 3 studies it.», EN and RU). Air off: k = 0.677434 ± 0.000157, z = +0.21. The reference's «how» is computed per height and true at every height: «In air the range would be shorter by 0.09 mm at h = 0.20 m to 0.54 mm at h = 1.00 m (computed by the engine for each height): more than the tape's error of ±0.5 mm from h = 0.95 m on, so the bench would see the air» (three variants: none, from a height on, at some heights). The teacher's note and both READMEs say why: «with an exact tape the bench resolves the air at the larger heights» | `s03_projectile/viz.py` (`INSTRUMENTS["stand"]`, `STEPS[0]`, `lab_reference`), `locales/ru.json`, READMEs | `::test_lab_reference_of_every_law_against_an_independent_computation` (the «how»'s numbers against the engine at every height; the effect grows with h, so «from h = 0.95 m on» is exact); `::test_the_lab_measurement_and_fit_on_the_computed_points_agree_with_every_law[heights]` (σ_h = 0 in every row); `::test_part_1_with_air_would_be_seen_by_the_exact_bench` (z < −2.5 with the air on) |
| F6 | documentation numbers | **fixed** (the README part; the engine's texts are QE's). «−18 % / +7 %» → «+21 % / −7 % of the measured value» (QE's wording) in `README.md` and `README.ru.md`; the light ball's buoyancy ratio 0.01 → 3.3·10⁻³ (and steel 10⁻⁴ → 1.5·10⁻⁴) | `s03_projectile/README.md`, `README.ru.md` | — (text) |
| F11 | the worksheet's numbers are not tested | **fixed**. Every number the answers and the teacher's notes state is asserted against the engine: «0.2–0.45 s», «from a fifth to a half» (0.1 s against 0.2020–0.4516 s), «near 42°», «up to 0.54 mm (0.08 %, at 1 m), more than the tape's error … at the largest heights», «about 0.5 % lower» (the line-through-origin slope in air, 0.497 %), «41.9° … 42.3°», «within one error» (the parabola's vertex on the student's table), «peaks at 45°», the grade-7 answers' «0.339 m to 0.677 m» and «four times higher … twice the range», the stopwatch question's «0.01–0.02 s» and «about 0.03 s». The fourth claim of the review (F4's) is gone with F4 | `s03_projectile/viz.py` (`WORKSHEET`) | `::test_the_worksheets_numbers_are_the_engines` |

## Notes for the integrator

- **The laws (D4).** S03 declares, in QF's schema: part 1 `k_horizontal` (√h, L, line0, slope); part 2 `v2_over_g` (sin
  2θ, L, line0, slope) and `theta_max_vacuum` (θ, L, quadratic, vertex: 45° by the formula from the floor, else the
  engine's scan); part 3 `theta_max_air` (θ, L, quadratic, vertex) and `theta_max_vacuum` (θ, L in vacuum, quadratic,
  vertex). `lab_reference(step_id, fixed, values, reference=None)`; without a reference the step's first law answers.
  `::test_the_lab_measurement_and_fit_on_the_computed_points_agree_with_every_law` fits every law on the student's
  table and checks it within two errors.
- **Sizes after F1.** The information row adds one more engine flight per air point: the Explore atlas grew from 5.70
  to 5.85 MB (target 6 MB), its CPU stayed 12 s.
- Text for `STATUS.md`: none needed from this part (nothing left open).
