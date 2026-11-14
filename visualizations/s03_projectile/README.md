# s03 — Projectile motion: thrown horizontally and at an angle

**English** | [Русский](README.ru.md)

A school demonstration (grades 7 and 10). A ball is launched from a height h above the floor at a speed v₀ and an
angle θ to the horizontal, in vacuum or in air. The run computes its flight with the engine `lfphys` and shows it as
the world's time reaches it; the range L, the flight time T and the highest point H are the run's measurements.
There are no law parameters: the air is a medium (a switch), not a modification of physics.

## 1. The screens

The demonstration has three tabs: **Watch · Explore · Lab work**.

* **Watch** — the recording "Two balls at the same moment: one dropped, one thrown sideways" (40 s, slow motion),
  with captions over the time line:
  1. "Two balls start at the same moment: one is dropped, the other is thrown sideways." (a steel ball from 1.25 m,
     2 m/s sideways; the time runs at 0.1 of real time);
  2. "The dots are the positions every 0.1 s. At every moment both balls are at the same height.";
  3. "Twice the sideways speed: the ball lands twice as far, at the same moment as the dropped one." (4 m/s);
  4. "Four times higher: the flight lasts twice as long, and the range doubles: L grows as √h." (5 m);
  5. "In air a light ball falls short of the same throw in vacuum (grey)." (the light ball at 20 m/s and 45° from
     the floor, the time at 0.5 of real time).

  Why a Watch screen: the decisive fact of the topic (the grade-10 demonstration of the FRP, the Russian federal programme) is a comparison in time — a
  dropped ball and a ball thrown sideways are at the same height at every moment. Explore launches one ball at a
  time, so the story is told here.
* **Explore** — a light ball (67 mm, 58 g) launched from a height. The controls stop only at computed points:
  "Launch height, m" (0, 1, 2, 5, 10), "Launch speed, m/s" (5, 10, 15, 20, 25), "Launch angle, °" (0, 5, …, 90) and
  "Air resistance" (off, on): 950 combinations, of which 10 are refused (from the floor at 0°: "The ball starts on
  the floor and does not move upwards: there is no flight") and 940 computed. "▶ Launch" throws the chosen point; a
  change of a control prepares the next throw while the earlier ones fly on. The last five throws stay as faded
  traces with their values ("Clear traces" removes them). "Show": "path", "dots every 0.1 s", "velocity",
  "velocity components", "forces", "energy". The readouts "Range", "Flight time" and "Highest point" appear when the
  time reaches them ("—" before).
* **Lab work** — three parts, each on its own computed points, with the instruments "Ruler" (division 0.01 m, error
  ±0.005 m), "Measuring tape" (0.001 m, ±0.0005 m), "Protractor" (1°, ±0.5°) and "Stopwatch" (division 0.01 s, error
  ±0.1 s: "your reaction: a start and a stop by hand scatter by about 0.1 s"). A reading is rounded to the division.
  1. "Height and range" (part 1 of 3) — a steel ball (20 mm, 32.9 g) rolls off a chute on a table, h = 0.20, 0.25, …,
     1.00 m (17 points), in air. Columns "h, m", "L, m", "√h, m^½"; the plot L against √h with a line through the
     origin; "Check against the law": the slope "k = L / √h" against k = v₀·√(2/g). The chute's speed (1.5 m/s) is
     not shown: the student finds it from the slope. Grade 7 checks the hypothesis "the higher, the farther" on L(h);
     grade 10 plots L(√h).
  2. "Angle and range" — a ballistic launcher on the floor, v₀ = 5 m/s, θ = 15°, 20°, …, 75° (13 points),
     without air, so that the law can be checked exactly. Columns "θ, °", "L, m", "sin 2θ"; L against sin 2θ, the
     slope against v₀²/g; a parabola through L(θ) gives the 45° maximum.
  3. "Air moves the maximum (beyond the basic programme)" — the light ball at 20 m/s in air, θ = 25°, 30°,
     …, 60° (8 points), and the same throw computed in vacuum (the grey ball). Columns "θ, °", "L, m", "L in vacuum,
     m"; a parabola through L(θ) gives the angle of the largest range, compared with the engine's own optimum (41.9°,
     found among 110 computed flights at 1° and then 0.1° steps; there is no closed form). The grey ball's parabola
     peaks at 45°.

  The worksheet (EN and RU, printable) has the FRP items, the equipment, seven questions and, behind "For the
  teacher", the answers and the teacher's notes.

## 2. The model and what the run computes

* **The flight** (`engine/shot.py` over `lfphys.core.mechanics.fly`): Newton's second law for a point ball in a
  uniform field, m·dv/dt = m·g + F_drag, integrated by DOP853 (rtol 10⁻¹¹) with the landing (y = 0, downwards) and the
  top of the path (v_y = 0) located by the integrator; the work of the drag is carried in the state, so the heat Q
  given to the air is computed along the path. g = 9.80665 m/s² (the standard gravity; a local g differs by up to
  0.3 %).
* **The air** (`lfphys.theories.models.drag_quadratic`, a model outside the core): F_drag = −½·ρ·C_d·A·|v|·v with
  C_d = 0.47 (a smooth sphere; Hoerner 1965, checked by the engine's step), A = πd²/4, the air at 20 °C and
  101 325 Pa (ρ = 1.204 kg/m³, μ = 1.813·10⁻⁵ Pa·s; U.S. Standard Atmosphere 1976 through `lfphys.core.data`). For the
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
| the constant drag coefficient holds | the share of the drag's work done at Reynolds numbers outside 10³–2·10⁵ | — | under 1 % |
| fall time of the dropped ball | the engine's | √(2h/g); in air the closed form of a fall with quadratic drag | 10⁻⁹ |
| both balls at the same height (vacuum) | the largest difference of the heights at the same moments | 0 | 10⁻⁹·h |
| the same throw in vacuum (grey) | T, L, H, energy | the closed forms in vacuum | as above |

**The second method in air** (`drag_quadratic.hodograph`): with u = v·cos θ and p = tan θ, the exact first integral
1/u² = 1/u₀² + (k/g)·(F(p₀) − F(p)), F(p) = p·√(1 + p²) + asinh p, and t, x, y as quadratures in p; no integration in
time. A vertical throw: v(t) = v_t·tan(arctan(v₀/v_t) − g·t/v_t) up, the fall from rest t = (v_t/g)·arccosh(e^{gH/v_t²}),
v_t = √(g/k). The range's and the height's tolerance is the engine's 10⁻⁹ of the flight's length scale, because a
range or a rise much shorter than the flight (a steep or a flat throw) carries the absolute error of the whole flight
(measured: 7·10⁻¹⁰ m on a 2.55 m scale).

The "the constant drag coefficient holds" check: near a slow top the Reynolds number falls below 10³, but the drag
does almost no work there; a check on Re alone would fail for no physical reason. On the measured curve of a smooth
sphere C_d runs from 0.39 to 0.50 over 10³–2·10⁵ (Morrison 2016), so the constant 0.47 errs by up to −18 % / +7 %
there; the check's note shows the curve's range over the path.

**The laws of the lab** ("Check against the law"), computed by the world when the atlas is built:
part 1 k = v₀·√(2/g) (closed form without air; the engine's air effect over the step's heights, at most 0.08 %, is
stated, below the tape's error); part 2 v₀²/g (closed form, no air); part 3 the engine's optimum in air (no closed
form). The tests check each against an independent computation (part 3: the hodograph's range maximised by Brent's
method agrees to 0.05°) and run the lab's measurement and fit on the computed points: each law agrees within two
errors (part 3: 42.03° ± 0.18° against 41.9°).

## 4. Approximations and limits

* A point ball: no spin (no Magnus force), no buoyancy (of order ρ_air/ρ_ball: 10⁻⁴ for steel, 0.01 for the light
  ball), no rolling on the chute (part 1's v₀ is the chute's end speed).
* A uniform field; the decrease of g with height and the Earth's rotation (10⁻⁶ and 10⁻⁴ of the range) are
  neglected; the floor is a horizontal plane; the ball stops where it lands (no bounce).
* The air: a constant C_d (a model; its validity is checked along each path). Above Re ≈ 2·10⁵ (the light ball
  faster than about 45 m/s) the drag crisis would begin; the schema allows up to 40 m/s.
* The lab's instruments round a computed value; they add no scatter. So the virtual bench is more precise than a
  real one: part 2 is therefore computed without air (in air its slope would be 0.5 % lower, which the virtual tape
  detects).

## 5. Sizes and cost (measured 2026-11-14, Docker, CPU)

| item | points | size (gzip) | CPU of the points |
|---|---|---|---|
| Watch: recording `independence` (40 s × 20 fps) | 800 frames | 0.05 MB | 0.3 s |
| Explore | 940 (+10 refused) | 5.70 MB (largest point 12.6 kB) | 11–21 s (host load) |
| Lab, part 1 (`lab.heights`) | 17 | 0.05 MB | 0.2 s |
| Lab, part 2 (`lab.angles`) | 13 | 0.05 MB | 0.2 s |
| Lab, part 3 (`lab.air`) | 8 | 0.09 MB | 0.3 s |
| the world | | 5.94 MB | `site/record.py --world s03_projectile`: 24–47 s wall |

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
  the lab's laws and the lab's measurement and fit, the Watch's statements.
* `locales/ru.json`, `locales/en.json` — the texts.

## 8. Sources

* The stopwatch's error: D. A. Faux, J. Godolphin, "Manual timing in physics experiments: Error and uncertainty",
  Am. J. Phys. 87, 110–115 (2019), doi:10.1119/1.5085437 (the authors' accepted manuscript read): the reaction times
  of 4304 timekeepers, N(0.11 s, (0.07 s)²) each; a start and a stop by hand, N(0, (0.10 s)²).
* C_d of a sphere and the drag curve: S. F. Hoerner, Fluid-Dynamic Drag (1965), p. 3-7; F. A. Morrison, "Data
  Correlation for Drag Coefficient for Sphere" (2016) — through the engine (`lfphys/theories/models/drag_quadratic.py`).
* The tennis ball: ITF Rules of Tennis 2026, Appendix I.
* The curriculum documents: § 6.
