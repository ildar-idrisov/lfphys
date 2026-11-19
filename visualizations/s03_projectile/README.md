# s03 — Projectile motion: thrown horizontally and at an angle

**English** | [Русский](README.ru.md)

A school demonstration (grades 7 and 10). A ball is launched from a height h above the floor at a speed v₀ and an
angle θ to the horizontal, toward the east, in vacuum or in air. The run computes its flight with the engine `lfphys`
with the real forces — the Earth's rotation always, and with the air on the measured drag of a smooth sphere, the
air's buoyancy, the air the ball carries along, and for a ball rolling off the chute the Magnus force of its spin —
and shows it as the world's time reaches it; the range L, the flight time T and the highest point H are the run's
measurements. There are no law parameters: the air is a medium (a switch) and the Earth's rotation is the place of the
bench (45.5° N), not modifications of physics. The interface stays simple: the forces are no new controls; what each
of them does is stated in "How we know this is right".

## 1. The screens

The demonstration has three tabs: **Watch · Explore · Lab work**.

* **Watch** — the recording "Two balls at the same moment: one dropped, one thrown sideways" (30 s, slow motion),
  with captions over the time line:
  1. "Two balls start at the same moment: one is dropped, the other is thrown sideways." (a steel ball rolls off a
     chute 1.25 m high at 2 m/s; the time runs at 0.1 of real time; the playback waits 2.5 s here, before the balls
     move);
  2. "The dots are the positions every 0.1 s. At every moment both balls are at the same height, to 0.03 mm: the
     Earth's rotation lifts the ball thrown east a little." (at 1 s, while the balls fall: 0.1 s of world time after
     the start, the landing is at 0.505 s; computed: the thrown ball is at most 0.026 mm higher, the Eötvös effect);
  3. "Twice the sideways speed: the ball lands twice as far, at the same moment as the dropped one." (4 m/s; ×2.0000,
     the two landings 10 µs apart);
  4. "Four times higher: the flight lasts twice as long, and the range doubles: L grows as √h." (5 m; ×2.0000 each).

  The scene keeps one scale for the whole recording: the box over the three throws' computed paths (from a table,
  h ≤ 5 m, L ≤ 4.1 m), and each earlier throw stays as a faded path with its landing mark and "L = … m", so that "twice
  as far" and "four times higher" are seen on the screen, not only in the axis numbers. The time label says the
  world's time and how much the playback is slowed down. On a wide screen the caption lies over the bottom of the
  scene, and the view leaves room for it there, so it never covers a path or a landing. "More recordings" has "A light
  ball at 20 m/s in air, and the same throw in vacuum" (9 s, half of real time; a 40 m scale of its own): "A light ball
  is thrown at 20 m/s and 40° in air; the grey ball is the same throw computed without air." and "The air takes speed
  away all the time: the ball in air rises lower and falls short of the grey one."

  Why a Watch screen: the decisive fact of the topic (the grade-10 demonstration of the FRP, the Russian federal
  programme) is a comparison in time — a dropped ball and a ball thrown sideways are at the same height at every
  moment. Explore launches one ball at a time, so the story is told here.
* **Explore** — a light ball (67 mm, 58 g; named in the top left corner of the view) launched from a height. The
  controls stop only at computed points: "Launch height, m" (0, 1, 2, 5, 10), "Launch speed, m/s" (5, 10, 15, 20, 25),
  "Launch angle, °" (0, 5, …, 90) and "Air resistance" (off, on): 950 combinations, of which 10 are refused (from the
  floor at 0°: "The ball starts on the floor and does not move upwards: there is no flight") and 940 computed.
  "▶ Launch" throws the chosen point; a change of a control prepares the next throw while the earlier ones fly on. The
  last five throws stay as faded traces, each labelled above its landing mark with the values that differ from the
  shown point. "Show": "path", "dots every 0.1 s", "velocity", "velocity components", "forces", "energy". With the air
  on, "forces" draws the air's forces on a scale of their own: enlarged ×m against the weight's scale (m is 1, 2 or
  5 × 10ⁿ, chosen from the largest air force of the flight, computed by the run), so that they stay visible at the top
  of the path; the arrow says "drag ×m" and the legend gives its scale ("drag, enlarged ×m: … N", or "drag, on the
  weight's scale: … N" when m = 1). "energy" shows the kinetic and the potential energy and the "heat (air)", the drag's
  work alone. The readouts "Range", "Flight time", "Highest point" and "To the right, Earth's rotation" (mm) appear when
  the time reaches them ("—" before). The light ball is launched by the launcher, never rolled off a chute: its barrel
  lies along the launch direction (on its mount from the floor), and "h = … m" stands beside the table, clear of it. A
  ball thrown straight up lands west of the launch point (10.9 mm at 25 m/s from 10 m without air), a dropped one east
  of it: the Earth's rotation.
* **Lab work** — a narrow bench, not a test (the owner, 2026-11-18): nothing is hidden, the app judges nothing, and
  the task can be done in several ways, some right and some wrong (below). Its drawer "How we know this is right" is
  Explore's: every check with its value, the events with their times and values ("the ball lands: range 0.5244 m,
  flight time 0.3499 s"), and "Computed for this bench", the world's own values for the bench. The view draws what it
  draws in Explore (the height, the landings with their values, the top of the path; only the floor's numbers give way
  to the lab's measuring tape). The instruments: "Height scale of the stand" ("division 0.01 m; exact: the stand sets
  the chute's height at its marks"), "Measuring tape" (0.001 m, ±0.0005 m), "Protractor" (1°, ±0.5°), "Stopwatch"
  (division 0.01 s, error ±0.1 s: "your reaction: a start and a stop by hand scatter by about 0.1 s") and "Manometer of
  the chamber" (0.1 kPa, exact: "the chamber is open to the room's air or pumped out"; it reads 101.3 kPa with the air
  on and 0 kPa without, so each row of a table says which it was). The fit prints its parameters with their errors
  (no χ² at school); the table, its CSV and the plot are conveniences, as in a laboratory; the students record and hand
  in their own measurements, and the teacher judges them.
  1. "Height and range" — a steel ball (20 mm, 32.9 g) rolls off a chute at 1.5 m/s (the step's goal says so; the
     launch event too), h = 0.20, 0.25, …, 1.00 m (17 points), with the air off or on (34 points). Columns "h, m",
     "L, m", "√h, m^½", "T, s" (the hand stopwatch), "T = L / v₀, s" (the time from the tape) and "p, kPa"; the plot L
     against √h with a line through the origin (or a line). Computed for this bench: "k = v₀·√(2/g)" (0.67740 m^½;
     the Earth's rotation lengthens the vacuum ranges by 0.004–0.021 mm), "k in air (line through the origin)"
     (0.67615 m^½, 8.0σ below) and "T / √h" (√(2/g) = 0.45160 s/m^½).
  2. "Angle and range" — a ballistic launcher on the floor, v₀ = 5 m/s, θ = 15°, 20°, …, 75° (13 points), with the air
     off or on (26 points). Columns "θ, °", "L, m", "sin 2θ", "p, kPa"; the plot L against sin 2θ with a line through
     the origin (or a line, or a parabola). Computed: "the slope of L against sin 2θ" v₀²/g = 2.5493 m (the rotation
     moves the ranges by −0.063 to +0.089 mm), "θ* of the largest range" 45°, "slope of L against sin 2θ in air"
     2.5383 ± 0.0007 m (15σ below v₀²/g) and "θ* of the largest range in air" 45.0°.
  3. "Air moves the maximum (beyond the basic programme)" — the light ball at 20 m/s in air, θ = 20°, 25°, …, 70°
     (11 points), and the same throw computed in vacuum (the grey ball). Columns "θ, °", "L, m", "L in vacuum, m" (the
     grey ball's tape reads once it has landed); the plot L against θ with a parabola. Computed: "θ* of the largest
     range in air" 42.3° (the engine's search with this world's forces among 110 flights; with the constant C_d = 0.47
     of earlier versions it gives 41.9°) and the grey ball's 45°.

  **The ways of the bench and their outcomes on the built atlas** (the readings as the instruments make them, fitted
  as the player fits them; `tests/test_s03_screens.py` reproduces each):

  | part | way | outcome | |
  |---|---|---|---|
  | 1 | L against √h, a line through the origin, air off | k = 0.67743 ± 0.00016 m^½ (0.2σ from 0.67740); v₀ = 1.5001 ± 0.0003 m/s | right |
  | 1 | L against h (grade 7) | the range grows with the height, but four times higher (0.25 → 1.00 m) gives 0.339 → 0.677 m, ×1.997, not ×4; a line through the origin misses (χ²/ν ≈ 3.5·10⁴) | the hypothesis right, a proportion wrong |
  | 1 | the hand stopwatch against T = L / v₀ | neighbouring heights' flights differ by 0.011–0.024 s, a hand scatters by 0.1 s: over 4 000 simulated classes the slope of T against √h is 0.452 ± 0.031 s/m^½ (7 %); T = L / v₀ agrees with √(2h/g) to 0.32 ms | the stopwatch too coarse, the tape right |
  | 1 | the air on, L against √h through the origin | the ranges 0.23–1.73 mm shorter (beyond the tape from h = 0.40 m): k = 0.67629 ± 0.00016 m^½, 7.1σ below, v₀ = 1.4975 m/s; χ²/ν 0.51 does not show it | wrong with the law of vacuum |
  | 1 | the rows with and without air in one table | k = 0.67686 ± 0.00012 m^½, 4.4σ below, χ²/ν 1.24 | wrong |
  | 2 | L against sin 2θ through the origin, air off | 2.5490 ± 0.0007 m (0.4σ from v₀²/g = 2.5493 m) | right |
  | 2 | the same with the air on | 2.5380 ± 0.0007 m, 15.4σ below v₀²/g; χ²/ν 0.006 | wrong: a law of vacuum in air |
  | 2 | the largest range by eye, a parabola through L against θ | 45° by eye (air off and on); the parabola 45.00 ± 0.14° (off), 44.97 ± 0.14° (on) | right within the steps |
  | 3 | a parabola through the six points 30–55° | 42.36 ± 0.20° (0.3σ from 42.3°) | right |
  | 3 | a parabola through all eleven points 20–70° | 42.52 ± 0.15° (1.5σ above; 25–60°: 42.41 ± 0.18°) | biased, under 2σ at this tape |
  | 3 | the largest range by eye; the grey ball's parabola | 40° (28.352 m against 28.323 m at 45°); the grey ball 45.00 ± 0.16° | coarse; right |

  **The task sheet** (EN and RU, printable; `worksheet.html?demo=s03_projectile`): the FRP items (by their
  programmes' names), the goal, the bench (what it is and what can be set on it, with the instruments generated from
  the parts), one suggested procedure that names the ways, what to record and hand in, blank tables of 17 rows and plot
  frames; no questions, answers or teacher's pages. The teacher may edit the goal, the procedure, the record list and a
  free field "Task from the teacher" before printing, or choose a variant computed in the atlases (`&variant=`):
  "grade7" — "Grade 7: the higher the launch, the farther the ball flies" (part 1 with the air off, L against h without
  a line, 0.25 m against 1.00 m), and "air" — "Grade 10: the same bench in air" (parts 1 and 2 with the air on, then
  off). `&computed=1` prints "Computed for this bench" on a page of its own.

## 2. The model and what the run computes

* **The flight** (`engine/shot.py` over `lfphys.core.mechanics.fly`): Newton's second law for a point ball in a
  uniform field with declared forces, integrated by DOP853 (rtol 10⁻¹², § 4) with the landing (y = 0, downwards) and the
  top of the path (v_y = 0) located by the integrator; the work of every force is carried in the state. g = 9.80665 m/s².
* **The rotating Earth** (`lfphys.core.mechanics.earth_frame`): the bench stands at sea level at 45.4996° N ("45.5° N"),
  where the WGS 84 normal gravity equals the standard g the engine uses, and every throw goes toward the east. Each
  flight carries the Coriolis force's part in the throw's vertical plane, 2m·Ω_z·(−v_y, v_x) (it lightens a throw to the
  east: the Eötvös effect); the offset out of the plane, to the right (south), is computed along the flight by its own
  first-order equation (its feedback into the plane is of order (ΩT)²).
* **The air** (when it is on): the measured drag curve of a smooth sphere at the ball's own Reynolds number
  (`theories.models.drag_quadratic.CurveDrag`, Morrison 2016: C_d 0.39–0.44 on these flights), and the ball as a body in
  the air at rest (`core.mechanics.particle.Medium`): the buoyancy ρ·V·g and the added mass C_A·ρ·V with C_A = ½.
  Dry air at 20 °C and 101 325 Pa (ρ = 1.204 kg/m³, μ = 1.813·10⁻⁵ Pa·s; U.S. Standard Atmosphere 1976, the data set
  `core.data:air`).
* **The spin** (`theories.models.magnus`): the steel ball launched horizontally from a height leaves a chute rolling
  without slipping, with topspin ω = v₀/R (150 rad/s at 1.5 m/s). In air it feels the Magnus force F = ½·ρ·C_L·A·v²
  (down for a topspin) and the spin's increase of its drag, C_D(S, Re) = f(S)·C_D(Re), from the measurements of Zhou,
  Zhang & Xu (2022) up to Re 3 472 (the chute's ball: Re 2.0·10³ at the launch to 6.2·10³ at 1 m), cross-checked at
  10⁴ against Muto et al. (2012); the stated band C_L × [0.825, 1.230] and the drag's factor × [0.917, 1.084] is the
  uncertainty of the chute's ranges in air. The data cover Re ≤ 10⁴, so a rolling ball in air that would fly faster
  than 7.5 m/s is refused ("A ball rolling off the chute spins, and the measured data of a spinning ball cover speeds up
  to 7.5 m/s for this ball: …"). The launcher, a throw, a drop and the light ball leave without spin.
* **The balls**: steel, 20 mm, 32.9 g (steel at 7.85 g/cm³); light, 67 mm, 58 g — the size and mass of a tennis ball
  (ITF Rules of Tennis, Appendix I: 6.54–6.86 cm, 56.0–59.4 g) but a smooth sphere's drag.
* **The second ball** ("Ball for comparison"): "a ball dropped at the same moment from the same point", or "the same
  throw in vacuum (grey)". Each is computed by the engine on its own; it does not affect the first ball.
* **What is sent**: the samples t, x, y every 1/60 s of world time (every 6th is a multiple of 0.1 s: the dots),
  revealed when the time reaches them; the launch (its speed, angle and spin), the top of the path and the landing as
  events with their values; each frame carries the ball's position and velocity, the drag and the Magnus force, the
  energies E_k, E_p and Q, the chamber's pressure, and the measurables (range, flight time, highest point, the offset to
  the right) once reached. What is only drawn is rounded to 6 significant digits (4 for the energy bars and the force
  arrows): far below a pixel.

## 3. Checks ("How we know this is right")

| check | computed | reference | tolerance |
|---|---|---|---|
| flight time T, range L, highest point H | the engine's (`fly`, in time) | the second method: the flight's equations in the velocity's angle (`drag_quadratic.angle_flight`: the drag curve, the spin's drag, the buoyancy, the added mass, the Magnus force and the Coriolis force's planar part, assembled on their own; no integration in time) | 10⁻⁹ (lengths: of the flight's length scale max(h, v₀²/g)) |
| a vertical flight (straight up, or dropped): T and H | the engine's | in vacuum the closed forms of a fall, which the rotation changes only at second order; in air no second method exists in the engine ("—": the energy balance checks it) | 10⁻⁹ + (Ω_z·T)² |
| a vertical flight: the drift east of the launch point | the engine's landing point | the drift by its own first-order equation along the same flight computed in the north–south plane (`earth_frame.sideways`) | 10⁻⁹ of the length scale + (2Ω_z·T)² |
| energy balance E_k + E_p + Q = E₀ along the path | the largest deviation | 0 (with the buoyancy's and the added mass's work; the Magnus and Coriolis forces do none) | 10⁻⁹ of E₀ |
| the drag curve covers this flight | Re along the path, C_d there | the curve holds to 10⁶ | ✓ / ✗ |
| the spinning ball's data cover this flight | Re and S = Rω/v along the path | the model's domain Re ≤ 10⁴, S ≤ 6 (measured to 3 472) | ✓ / ✗ |
| what the air does to the range (information) | against the same throw in vacuum: the drag, the buoyancy and the air carried along, the Magnus force, the spin's extra drag, each on its own | — | — |
| range within the Magnus force's stated band (information) | the ranges at the band's edges | the model's range | — |
| range with a constant drag coefficient (information) | the same throw with C_d = 0.47 of earlier versions | this world's range | — |
| the Earth's rotation (information) | the landing's shift to the east and to the south | — | — |
| the history force's upper bound (information) | Basset's kernel along the flight (`core.mechanics.drag.history_bound`, 500 steps; 2 000 agree to 10⁻⁴) | — | — |
| how much higher the thrown ball is (the dropped ball, information) | the largest difference of the two heights | — | — |

The second method is tested against the engine on every grid point of every atlas (agreement 10⁻¹⁵–10⁻¹⁰). The world's
effects are tested against the engine step E03's references (`lfphys/sources/s03_forces_2026-11-18.md` §7): part 1
(the chute, h 0.20–1.00 m), the Magnus force −0.134 to −1.083 mm (band −0.110 to −0.893 / −0.165 to −1.332), the spin's
drag −0.046 to −0.242 mm, the air's whole effect −0.227 to −1.734 mm (beyond the tape's 0.5 mm from h = 0.40 m); part
2 the curve against the constant +0.459 to +2.053 mm, the buoyancy and the added mass +0.291 to +0.582 mm; part 3 the
curve against the constant +0.492 to +1.087 m, the optimum 42.3° (41.9° with the constant); the history force's bound
≤ 0.037, 0.357 and 61.5 mm; the rotation's shift +0.004 to +0.021 mm along and 0.003–0.016 mm to the right (part 1),
−0.062 to +0.088 and 0.017–0.103 mm (part 2), +2.84 to −1.64 and 1.35–3.73 mm (part 3), +2.42 and 7.30 mm on Explore's
longest throw.

**The bench's computed values** ("Computed for this bench", `Simulation.lab_reference`), computed when the step's
atlas is built, are tested against independent computations: the formulas; the slopes in air fitted over the second
method's ranges; the optimum in air by Brent's method on the second method's range (within 0.05°).

## 4. Approximations and limits

* A point ball with the real forces above. Its spin is taken as constant: the air's torque on a spinning sphere at
  these Reynolds numbers has no checked data; an estimate puts the loss below 7 % over the flight, which moves a range
  by at most 0.010 mm. The added mass's C_A = ½ is checked only to Re 300 (Magnaudet et al. 1995); a change of 0.5 would
  move the ranges by 0.026 mm (the chute, 1 m), 0.195 mm (the launcher, 45°) and 46 mm of 28.4 m (the light ball).
* The history force (the air's unsteady flow around an accelerating ball) is not part of the flight: at these
  Reynolds numbers (2·10³–1.1·10⁵) no established law exists; its upper bound by Basset's kernel is in the checks
  (≤ 0.037 mm in part 1, ≤ 0.36 mm in part 2, ≤ 62 mm of 28 m in part 3).
* The rotating Earth: the Coriolis force on the ball's own mass; the air carried along and the rotating air add terms
  of order ρ_air/ρ_ball of it (3·10⁻³ for the light ball), left out. The flight is computed in its vertical plane; the
  offset out of it to first order. The field is uniform (its decrease with height, 2h/R_Earth, left out); the floor is
  a horizontal plane; the ball stops where it lands. A real place's g differs from g_n by up to 0.3 %.
* The light ball is a smooth sphere: a real tennis ball's felt has its own drag. The drag crisis (Re ≈ 3·10⁵) lies
  beyond every flight of the screens; the curve includes it.
* A vertical flight in air has no second method in the engine (its T and H are checked by the energy balance only).
* The flights shown are integrated at rtol 10⁻¹² instead of the engine's default 10⁻¹¹: with the medium and the drag
  curve the energy balance at 10⁻¹¹ reached 1.16·10⁻⁹ on Explore's grid, above the engine's stated 10⁻⁹ (the light ball
  from the floor at 5 m/s and 60°); at 10⁻¹² the worst is 1.0·10⁻¹⁰.
* The lab's instruments round a computed value; they add no scatter (the stopwatch's way simulates the hand's scatter
  only in the tests).

## 5. Sizes and cost (measured 2026-11-19, Docker, CPU)

| item | points | size (gzip) | CPU of the points |
|---|---|---|---|
| Watch: recording `independence` (30 s × 20 fps) | 600 frames | 0.04 MB | 0.2 s |
| Watch: recording `air` (9 s × 20 fps) | 180 frames | 0.02 MB | 0.1 s |
| Explore | 940 (+10 refused) | 6.63 MB (largest point 14.1 kB) | 67 s |
| Lab, part 1 (`lab.heights`) | 34 | 0.13 MB (largest point 5.2 kB) | 4.0 s |
| Lab, part 2 (`lab.angles`) | 26 | 0.13 MB (largest point 6.6 kB) | 1.1 s |
| Lab, part 3 (`lab.air`) | 11 | 0.14 MB (largest point 15.0 kB) | 2.3 s |
| the world | | 7.09 MB | `site/record.py --world s03_projectile`: 98 s wall |

The Explore atlas is over its 6 MB target (under the 12 MB limit): it grew from 5.85 MB (2026-11-17) by the drawer's
values of the real forces in every point (each force's share, the stated band, the constant C_d's comparison, the
Earth's rotation, the history force's bound: about 1 MB of check messages), and its CPU from 11 s by the comparisons
and the second method, computed for every point (about 60 ms a point in air).

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

* `viz.py` — the parameters, the world (`Simulation`: messages, checks, `lab_reference`), the screens, the task sheet.
* `engine/shot.py` — one ball's flight over the engine with the real forces, its samples, its second method and the
  comparisons the drawer states; `optimum_angle`.
* `web/view.js` — the side view (drawing only), the overlays, the traces, `worldToPx`/`pxToWorld`/`anchors` for the
  lab's instruments, `canvas.__layout` for the browser checks.
* `tests/test_s03_physics.py` — every preset, events, causality, refusals, the companions, vertical flights, the
  second method, each force against E03's references, the drawer's values, the bench's computed values.
* `tests/test_s03_screens.py` — every grid point of every atlas, the task sheet, every way of the bench on the built
  atlas, the Watch's captions against the recordings.
* `tests/s03_screens.mjs` — the browser checks of the view (Explore's labels and the air's arrows; Watch's captions;
  Lab work's drawing; the phone; no overflow).
* `locales/ru.json`, `locales/en.json` — the texts.

## 8. Sources

* The stopwatch's error: D. A. Faux, J. Godolphin, "Manual timing in physics experiments: Error and uncertainty",
  Am. J. Phys. 87, 110–115 (2019), doi:10.1119/1.5085437 (the authors' accepted manuscript read): the reaction times
  of 4304 timekeepers, N(0.11 s, (0.07 s)²) each; a start and a stop by hand, N(0, (0.10 s)²).
* The forces, through the engine, each checked on its source's text (`lfphys/sources/s03_forces_2026-11-18.md`): the
  drag curve, F. A. Morrison, "Data Correlation for Drag Coefficient for Sphere" (2016); the spinning sphere, S. Zhou,
  G. Zhang, X. Xu, Water 14, 2593 (2022), and M. Muto, M. Tsubokura, N. Oshima, Phys. Fluids 24, 014102 (2012); the
  added mass, J. Magnaudet, M. Rivero, J. Fabre, J. Fluid Mech. 284, 97 (1995); the normal gravity, NIMA TR8350.2 (WGS
  84, 3rd ed., 2000); the history force, A. Daitche, J. Comput. Phys. 254, 93 (2013), and D. Jaganathan et al., Front.
  Phys. 11, 1167338 (2023).
* The tennis ball: ITF Rules of Tennis 2026, Appendix I.
* The curriculum documents: § 6.
