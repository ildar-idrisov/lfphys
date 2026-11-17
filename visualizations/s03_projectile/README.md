# s03 — Projectile motion: thrown horizontally and at an angle

**English** | [Русский](README.ru.md)

A school demonstration (grades 7 and 10). A ball is launched from a height h above the floor at a speed v₀ and an
angle θ to the horizontal, in vacuum or in air. The run computes its flight with the engine `lfphys` and shows it as
the world's time reaches it; the range L, the flight time T and the highest point H are the run's measurements.
There are no law parameters: the air is a medium (a switch), not a modification of physics.

## 1. The screens

The demonstration has three tabs: **Watch · Explore · Lab work**.

* **Watch** — the recording "Two balls at the same moment: one dropped, one thrown sideways" (30 s, slow motion),
  with captions over the time line:
  1. "Two balls start at the same moment: one is dropped, the other is thrown sideways." (a steel ball from 1.25 m,
     2 m/s sideways; the time runs at 0.1 of real time; the playback waits 2.5 s here, before the balls move);
  2. "The dots are the positions every 0.1 s. At every moment both balls are at the same height." (at 1 s, while the
     balls fall: 0.1 s of world time after the start, the landing is at 0.505 s);
  3. "Twice the sideways speed: the ball lands twice as far, at the same moment as the dropped one." (4 m/s);
  4. "Four times higher: the flight lasts twice as long, and the range doubles: L grows as √h." (5 m).

  The scene keeps one scale for the whole recording: the box over the three throws' computed paths (from a table,
  h ≤ 5 m, L ≤ 4.1 m), and each earlier throw stays as a faded path with its landing mark and "L = … m", so that "twice
  as far" and "four times higher" are seen on the screen, not only in the axis numbers. The time label says the world's
  time and how much the playback is slowed down (the Watch screen's own label). On a wide screen the caption lies over the bottom of the scene, and the
  view leaves room for it there, so it never covers a landing. "More recordings" has "A light ball at 20 m/s in air,
  and the same throw in vacuum" (9 s, half of real time; a 40 m scale of its own): "A light ball is thrown at 20 m/s and
  40° in air; the grey ball is the same throw computed without air." and "The air takes speed away all the time: the
  ball in air rises lower and falls short of the grey one."

  Why a Watch screen: the decisive fact of the topic (the grade-10 demonstration of the FRP, the Russian federal
  programme) is a comparison in time — a dropped ball and a ball thrown sideways are at the same height at every
  moment. Explore launches one ball at a time, so the story is told here.
* **Explore** — a light ball (67 mm, 58 g; named in the top left corner of the view) launched from a height. The
  controls stop only at computed points: "Launch height, m" (0, 1, 2, 5, 10), "Launch speed, m/s" (5, 10, 15, 20, 25),
  "Launch angle, °" (0, 5, …, 90) and "Air resistance" (off, on): 950 combinations, of which 10 are refused (from the
  floor at 0°: "The ball starts on the floor and does not move upwards: there is no flight") and 940 computed.
  "▶ Launch" throws the chosen point; a change of a control prepares the next throw while the earlier ones fly on. The
  last five throws stay as faded traces, each labelled above its landing mark with the values that differ from the
  shown point, kept inside the view and clear of the other labels ("Clear traces" removes them). "Show": "path", "dots
  every 0.1 s", "velocity", "velocity components", "forces", "energy". The readouts "Range", "Flight time" and "Highest
  point" appear when the time reaches them ("—" before). From the floor the launcher's barrel lies on its mount above
  the floor.
* **Lab work** — three parts, each on its own computed points, with the instruments "Height scale of the stand"
  (division 0.01 m, no error: "the stand sets the chute's height exactly at its marks: the height has no reading
  error"), "Measuring tape" (0.001 m, ±0.0005 m), "Protractor" (1°, ±0.5°) and "Stopwatch" (division 0.01 s, error
  ±0.1 s: "your reaction: a start and a stop by hand scatter by about 0.1 s"). A reading is rounded to the division.
  "Check against the law" judges a fit only when the plotted columns and the model are one of the part's laws.
  1. "Height and range" (part 1 of 3) — a steel ball (20 mm, 32.9 g) rolls off a chute on a stand, h = 0.20, 0.25, …,
     1.00 m (17 points), without air: with the heights exact and the tape reading to 1 mm the bench would see the air
     (computed: in air the range would be 0.09 mm shorter at 0.20 m and 0.54 mm at 1.00 m, more than the tape's error
     from h = 0.95 m on), so the law L ∝ √h is checked exactly, as the part's goal says. Columns "h, m", "L, m",
     "√h, m^½" and "T, s" (the hand-timed flight, with no law: its scatter against √(2h/g) is a worksheet question); the plot L against √h with a line through the origin; the law: the slope "k = L / √h" against
     k = v₀·√(2/g). The chute's speed (1.5 m/s) is not shown: the student finds it from the slope; the events in "How we
     know this is right" carry no measured values. Grade 7 checks the hypothesis "the higher, the farther" on L(h)
     (the worksheet's grade-7 variant); grade 10 plots L(√h).
  2. "Angle and range" — a ballistic launcher on the floor, v₀ = 5 m/s, θ = 15°, 20°, …, 75° (13 points),
     without air, so that the law can be checked exactly. Columns "θ, °", "L, m", "sin 2θ"; two laws: "the slope of L
     against sin 2θ" against v₀²/g, and the vertex of a parabola through L(θ) ("θ* of the largest range") against 45°.
  3. "Air moves the maximum (beyond the basic programme)" — the light ball at 20 m/s in air, θ = 25°, 30°,
     …, 60° (8 points), and the same throw computed in vacuum (the grey ball). Columns "θ, °", "L, m", "L in vacuum,
     m" (the grey ball's tape reads once the grey ball has landed); two laws: a parabola through L(θ) gives "θ* of the largest range in air", compared with the engine's optimum
     with this world's drag model (41.9°, the largest range among 110 computed flights at 1° and then 0.1° steps; there
     is no formula), and a parabola through the grey ball's ranges gives "θ* of the largest range of the grey ball
     (vacuum)", compared with 45°. The reference says plainly that the optimum depends on the drag model: with the
     measured drag curve the same search gives 42.3°; the check is against the world's model.

  The worksheet (EN and RU, printable) has the FRP items (by their programmes' names), the equipment, eight questions
  and, behind "For the teacher", the answers, the teacher's notes and the laws' references. Its grade-7 variant has
  part 1 only, L plotted against h with no fitted curve, and four questions of its own (the hypothesis tested by the
  sign of the change and the shape of the graph: four times higher, 0.25 → 1.00 m, the range only doubles,
  0.339 → 0.677 m). Every number the answers and the notes state is asserted against the engine in the tests.

## 2. The model and what the run computes

* **The flight** (`engine/shot.py` over `lfphys.core.mechanics.fly`): Newton's second law for a point ball in a
  uniform field, m·dv/dt = m·g + F_drag, integrated by DOP853 (rtol 10⁻¹¹) with the landing (y = 0, downwards) and the
  top of the path (v_y = 0) located by the integrator; the work of the drag is carried in the state, so the heat Q
  given to the air is computed along the path. g = 9.80665 m/s² (the standard gravity; a local g differs by up to
  0.3 %).
* **The air** (`lfphys.theories.models.drag_quadratic`, a model outside the core): F_drag = −½·ρ·C_d·A·|v|·v with
  C_d = 0.47 (a smooth sphere; Hoerner 1965, checked by the engine's step), A = πd²/4, the air at 20 °C and
  101 325 Pa (ρ = 1.204 kg/m³, μ = 1.813·10⁻⁵ Pa·s; U.S. Standard Atmosphere 1976, the data set `core.data:air`). For the
  light ball k = ρC_dA/(2m) = 0.01720 1/m, for the steel ball 0.002702 1/m.
* **The balls**: steel, 20 mm, 32.9 g (steel at 7.85 g/cm³); light, 67 mm, 58 g — the size and mass of a tennis
  ball (ITF Rules of Tennis, Appendix I: 6.54–6.86 cm, 56.0–59.4 g) but a smooth sphere's drag (a real tennis ball's
  felt has its own).
* **The second ball** ("Ball for comparison"): "a ball dropped at the same moment from the same point", or "the same
  throw in vacuum (grey)". Each is computed by the engine on its own; it does not affect the first ball.
* **What is sent**: the samples t, x, y every 1/60 s of world time (every 6th is a multiple of 0.1 s: the dots),
  revealed when the time reaches them, in pieces of at least three samples (the newest piece of the path is drawn up
  to the ball's computed position in the frame); the top of the path and the landing as events (H; T, L, the landing
  speed and angle); each frame carries the ball's position and velocity, the drag force, the energies E_k, E_p and Q,
  and the measurables (range, flight time, highest point) once reached. What is only drawn is rounded to 6
  significant digits (4 for the energy bars and the force arrows): far below a pixel.

## 3. Checks ("How we know this is right")

| check | computed | reference | tolerance |
|---|---|---|---|
| flight time T | the engine's landing time | vacuum: T = (v₀y + √(v₀y² + 2gh))/g; air: the hodograph quadrature (below); a vertical throw in air: the closed forms of vertical motion | 10⁻⁹ |
| range L | the engine's landing point | vacuum: v₀x·T; air: the hodograph; vertical: 0 | 10⁻⁹ of max(h, v₀²/g) |
| highest point H (upward launches) | the engine's apex | vacuum: h + v₀y²/(2g); air: the hodograph | 10⁻⁹ of max(h, v₀²/g) |
| energy balance E_k + E_p + Q = E₀ | the largest deviation along the path | 0 | 10⁻⁹ of E₀ |
| the drag model's range of validity (Re) | the share of the drag's work done at Reynolds numbers outside 10³–2·10⁵, where the model uses its constant | — | under 1 % |
| range with the measured drag curve (information) | the same throw computed with the measured C_d(Re) of a smooth sphere (`drag_quadratic.CurveDrag`, Morrison 2016) | the world's range with the constant 0.47 | — (the difference is shown: the drag model's own uncertainty) |
| fall time of the dropped ball | the engine's | √(2h/g); in air the closed form of a fall with quadratic drag | 10⁻⁹ |
| both balls at the same height (vacuum) | the largest difference of the heights at the same moments | 0 | 10⁻⁹·h |
| the same throw in vacuum (grey) | T, L, H, energy | the closed forms in vacuum | as above |

**The second method in air** (`drag_quadratic.hodograph`): with u = v·cos θ and p = tan θ, the exact first integral
1/u² = 1/u₀² + (k/g)·(F(p₀) − F(p)), F(p) = p·√(1 + p²) + asinh p, and t, x, y as quadratures in p; no integration in
time. A vertical throw: v(t) = v_t·tan(arctan(v₀/v_t) − g·t/v_t) up, the fall from rest t = (v_t/g)·arccosh(e^{gH/v_t²}),
v_t = √(g/k). The range's and the height's tolerance is the engine's 10⁻⁹ of the flight's length scale, because a
range or a rise much shorter than the flight (a steep or a flat throw) carries the absolute error of the whole flight
(measured: 7·10⁻¹⁰ m on a 2.55 m scale).

The check "the drag model's range of validity (Re)" tests where the model is used, not how good its constant is: near a
slow top the Reynolds number falls below 10³, but the drag does almost no work there, so a check on Re alone would fail
for no physical reason. On the measured curve of a smooth sphere C_d runs from 0.39 to 0.50 over 10³–2·10⁵ (Morrison
2016), so the constant 0.47 errs by +21 % / −7 % of the measured value there. How much that moves the result is the
next row, computed: the same throw with the measured curve flies 3–5 % farther (28.24 m against 27.22 m at 20 m/s and
40°, 37.89 m against 36.23 m at 25 m/s and 45°; review R-E F1), and part 3's optimum moves from 41.9° to 42.3°.

**The laws of the lab** ("Check against the law"; each law names its columns x and y and its model, review D4),
computed by the world when the atlas is built: part 1 k = v₀·√(2/g) (the formula; the part runs without air, and the
air's effect is computed for each of the step's heights and stated); part 2 v₀²/g and the 45° maximum (formulas, no
air); part 3 the engine's optimum in air with the constant C_d (no formula; the measured curve's optimum stated beside
it) and the grey ball's 45°. The tests check each against an independent computation (part 3: the hodograph's range
maximised by Brent's method agrees to 0.05°; the measured curve's optimum by a bounded search) and run the lab's
measurement and fit on the computed points: each law agrees within two errors (part 3: 42.03° ± 0.18° against 41.9°).
They also show why part 1 runs without air: with the air on, the exact heights and the 1 mm tape give
k = 0.67692 ± 0.00016 m^½ against 0.67740, 3.1 errors away.

## 4. Approximations and limits

* A point ball: no spin (no Magnus force), no buoyancy (of order ρ_air/ρ_ball: 1.5·10⁻⁴ for steel, 3.3·10⁻³ for the
  light ball), no rolling on the chute (part 1's v₀ is the chute's end speed).
* A uniform field; the decrease of g with height and the Earth's rotation (10⁻⁶ and 10⁻⁴ of the range) are
  neglected; the floor is a horizontal plane; the ball stops where it lands (no bounce).
* The air: a constant C_d (a model; where it is used is checked along each path, and each air flight is also
  computed with the measured drag curve for comparison). Above Re ≈ 2·10⁵ (the light ball faster than about 45 m/s)
  the drag crisis would begin; the schema allows up to 40 m/s.
* The lab's instruments round a computed value; they add no scatter. So the virtual bench is more precise than a
  real one: parts 1 and 2 are therefore computed without air (in air part 1's range would be up to 0.54 mm shorter,
  more than the tape's error at the largest heights, and part 2's slope 0.5 % lower, which the virtual tape detects).

## 5. Sizes and cost (measured 2026-11-17, Docker, CPU)

| item | points | size (gzip) | CPU of the points |
|---|---|---|---|
| Watch: recording `independence` (30 s × 20 fps) | 600 frames | 0.03 MB | 0.3 s |
| Watch: recording `air` (9 s × 20 fps) | 180 frames | 0.02 MB | 0.1 s |
| Explore | 940 (+10 refused) | 5.85 MB (largest point 12.9 kB) | 11–12 s |
| Lab, part 1 (`lab.heights`) | 17 | 0.04 MB | 0.1 s |
| Lab, part 2 (`lab.angles`) | 13 | 0.05 MB | 0.1 s |
| Lab, part 3 (`lab.air`) | 8 | 0.09 MB | 0.2 s |
| the world | | 6.11 MB | `site/record.py --world s03_projectile`: 23–32 s wall |

The Explore atlas grew from 5.70 MB (2026-11-14) by the information row of the measured drag curve in every air point.

## 6. Curriculum

* FRP OOO 2025 (the Russian federal programme for grades 7–9, basic level), grade 7, the laboratory work «Проведение исследования по проверке гипотезы:
  дальность полета шарика, пущенного горизонтально, тем больше, чем больше высота пуска» ("Research to test the
  hypothesis: the higher the launch, the farther a ball launched horizontally flies", our translation) — part 1.
* FRP SOO 2025 (grades 10–11, basic level), grade 10, Mechanics, Kinematics: the demonstration «Наблюдение движения тела,
  брошенного под углом к горизонту и горизонтально» ("Observing the motion of a body thrown at an angle to the horizontal and
  horizontally", our translation; Watch, Explore) and the laboratory work «Изучение движения тела, брошенного
  горизонтально» ("Studying the motion of a body thrown horizontally"; part 1). Part 3 goes beyond the basic programme.
* AP Physics 1 (CED effective fall 2024), Unit 1 "Kinematics", Topic 1.5 "Vectors and Motion in Two Dimensions"
  (air resistance neglected).
* IB Physics (first assessment 2025), A.1 Kinematics: projectiles without fluid resistance, and "the qualitative effect
  of fluid resistance on projectiles, including time of flight, trajectory, velocity, acceleration, range and terminal
  speed".
* AQA A-level Physics 7408, 3.4.1.4 Projectile motion: "Independent effect of motion in horizontal and vertical
  directions of a uniform gravitational field"; "Qualitative understanding of the effect of air resistance on the
  trajectory of a projectile".

The quotations were checked against the source texts on 2026-11-14: edsoo.ru (`2025_ooo_frp_fizika-7-9_baz.pdf` p. 6,
`2025_soo_frp_fizika_10_11_baz.pdf` pp. 7–8), the College Board's AP Physics 1 CED, the IB guide (a school-hosted copy
of the official PDF; the IB's own site needs a login) and AQA's specification 7408 version 1.4.

## 7. Files

* `viz.py` — the parameters, the world (`Simulation`: messages, checks, `lab_reference`), the screens, the worksheet.
* `engine/shot.py` — one ball's flight over the engine, its samples and references; `optimum_angle`.
* `web/view.js` — the side view (drawing only), the overlays, the traces, `worldToPx`/`pxToWorld`/`anchors` for the
  lab's instruments.
* `tests/test_s03_physics.py` — every preset, the corners of every atlas, events, causality, refusals, companions,
  the drag model's checks, the engine modules, the lab's laws and the lab's measurement and fit for every law, the
  worksheet's numbers, the Watch's statements.
* `locales/ru.json`, `locales/en.json` — the texts.

## 8. Sources

* The stopwatch's error: D. A. Faux, J. Godolphin, "Manual timing in physics experiments: Error and uncertainty",
  Am. J. Phys. 87, 110–115 (2019), doi:10.1119/1.5085437 (the authors' accepted manuscript read): the reaction times
  of 4304 timekeepers, N(0.11 s, (0.07 s)²) each; a start and a stop by hand, N(0, (0.10 s)²).
* C_d of a sphere and the drag curve: S. F. Hoerner, Fluid-Dynamic Drag (1965), p. 3-7; F. A. Morrison, "Data
  Correlation for Drag Coefficient for Sphere" (2016) — through the engine (`lfphys/theories/models/drag_quadratic.py`).
* The tennis ball: ITF Rules of Tennis 2026, Appendix I.
* The curriculum documents: § 6.
