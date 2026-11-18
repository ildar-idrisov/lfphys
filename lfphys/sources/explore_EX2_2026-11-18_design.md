# EX2: Watch, Explore and Lab work for u34, u35 and u37 — design (2026-11-18)

This document supplements the EX1 design `explore_2026-11-14_design.md` (below «EX1»). It says only what is new or
different for the three university worlds of batch EX2 (EX1 §7, the order the owner confirmed): **u34** «Orbits and
clocks», **u35** «Optical bench» and **u37** «The Bell test». Everything not mentioned here is as in EX1 (§1–§3 the
atlas, the registry and the player; §10 the decisions) and as the code keeps it (`visualizations/RULES.md` §10). The
owner's direction of 2026-11-14 is in `../../AGENTS.md` §1; the owner's go for EX2 of 2026-11-18: «закрывай u32 (b) и
(c) и потом переходи к EX2». This is the design only: it changes no code.

Numbers marked *measured* were measured for this design in Docker (image `lfphys-viz`, CPU, `LFPHYS_NO_GPU=1`,
`--memory` 2–4 GB, containers `lf-x2d-*`) with the code of HEAD 545939a: the worlds run headless by
`lfviz.headless.run_spec` and packed by `headless.Packer`, as `site/atlas.py` and `site/record.py` do (Appendix A).
Numbers marked *estimate* are computed from measured parts and say how. The lab works' statistics were checked by
Monte Carlo with the engine's own fit (`lfphys.tools.stats.linear_fit`, York for lines) on the engine's own values
(Appendix A). Quotations from courses and lab manuals were checked word for word in the downloaded texts (Appendix B).

Where EX1 or its audit row (§7) was wrong or incomplete, this document says so: **[error in earlier]**.

## 0. Decisions in brief

**Revised on 2026-11-18 after the owner's two answers (quoted in §9).** Lab work is a narrow experimental bench that
can be used in several ways, some leading to right results and some to wrong ones; nothing is hidden and the app
judges nothing; the worksheet is a task sheet the teacher may change. u35 gets Malus's law, strictly computed. The
whole design was audited for simplifications (§11). What the first version said differently is marked
**[error in earlier]** where it stands.

1. **All three worlds get all three screens.** u34: Watch (a rosette beside Newton's closed ellipse, the clock, a
   fall), Explore (r₀ × speed, 35 points), Lab work, a bench with two parts (periods and clocks; the advance of the
   periapsis). u35: Watch **[error in earlier: EX1 §7 said «no»]**, three Explore screens («Boundary», «Coatings»,
   «Polarisation»), and Lab work, a bench with three parts (Fresnel's reflection, Malus's law, polarisation by
   reflection). u37: Watch, Explore (pair × Δ × τ × law), and Lab work, a bench with three parts (E(α, β), the CHSH
   test, the same test in a local world, flagged).
2. **Lab work is a bench, not a test** (the owner, answer 1). Every check, value, reference and event is shown, as in
   Explore; overlays and readouts are available; the app gives no verdict on the student's data: the fit is a tool
   that prints its parameters, χ², p and the Birge ratio. The world's computed values for the bench are listed openly
   in the drawer. **[error in earlier]** The first version hid the checks' values, the events' texts and the answers,
   and judged the student's fit. (§1.4, §5 F6.)
3. **Several ways on every bench**, each inside the computed atlases, each with its computed outcome: u34 (§2.3)
   eleven, u35 (§3.4) thirteen, u37 (§4.3) ten, S03 (§10) nine. A wrong way goes wrong for a computed reason: a sign
   branch, a wrong angle law, too few counts, a coarse instrument, an approximation outside its range, a wrong angle
   set, an eccentric orbit where Kepler's law needs a circle, an open loophole.
4. **The task sheet** (§5 F8): the goal, the bench, the instruments, one suggested procedure, what to record and hand
   in, and the course it is based on, with verified quotations. No questions, answers, grading or teacher's pages
   **[error in earlier]**. The teacher changes the task by a variant computed in the atlases (`&variant=` in the
   address: another glass, another orbit family, another analyser or pair) and by editing the sheet in the browser
   before printing; both work on the static site.
5. **Malus's law in u35, strictly computed** (the owner, answer 2; §3.5): the polarisation through the bench by Jones
   matrices and density matrices with Fresnel's complex coefficients (TIR's phase makes the light elliptical), a
   source at any linear polarisation or unpolarised, a rotatable analyser before each detector with its principal
   transmittances as a stated device property (ideal by default, not modified physics), photons by the Born rule on
   the density matrix. A new core module `lfphys.core.optics.polarization`, tested against closed forms. The lab is
   founded on the University of Toronto's PHY293/PHY294 «Polarization of light».
6. **The time scale of a screen is the world's own** (§5 F1), stops count events (F2), one control may set several
   parameters (F3), counters and formula columns process the readings (F4, F5): as built in step F.
7. **Two packing changes keep the benches within budget**: a lab step may use an Explore screen's atlas (F9), and an
   atlas stores blobs shared by its points once (F10; *measured* −37 % for u35).
8. **Every lab is founded on a real course or manual**, quoted verbatim (Appendix B): *Exploring Black Holes* ch. 10
   and the CLEA lab «The Revolution of the Moons of Jupiter» (u34); Carnegie Mellon 33-353 Lab 1, the Rutgers Fresnel
   handout and Toronto's PHY293/PHY294 «Polarization of light» (u35); Dehlinger & Mitchell, Am. J. Phys. 70, 903 (2002)
   (u37).
9. **Every way's outcome was computed before it was designed**, with the engine's values and its fit (Appendix A.3,
   A.5): e.g. u35's p light read past Brewster's angle with the wrong sign gives n = 1.42 instead of 1.515 (χ²/dof
   59); u34's leading-order law fitted from 20 M gives 20.0 ± 0.3 instead of 6π (χ²/dof 17).
10. **S03 follows the same concept** (§10): its concealment, its questions and answers and its verdict go; it gains
    the bench's wrong ways it lacked (air in part B, a wide angle range in part C); the school level stays simpler.
11. **Sizes** (*estimate* from measured points): u34 5.3 MB, u35 11.9 MB, u37 4.8 MB (targets 12 MB per world); the
    site from 65.6 MB to about 87 MB.
12. **The audit** (§11) lists 25 places where the design or the worlds simplify; 6 are fixed in EX2 (u35's field
    profile for p light, the photons' polarisation colours and the material names, u37's source visibility, u34's Newton
    integrator, the first version's concealment), 2 go to the owner (real detectors in u37, real materials in u35), the
    others are justified or recorded.
13. **Plan** (§8): F (with the revised F6, F8 and F9, F10), E35 (the polarisation module) in parallel; then W34, W35,
    W37 and WS03 (S03's rework); then I; then four independent reviews and their processing.

---

## 1. What is common to the three worlds

### 1.1 Time on a screen

| world | one event of interest lasts (world time) | playback (world s per played s) | atlas clock |
|---|---|---|---|
| u34 | a radial period: 116 GM/c³ (circle at 7 M) to 1 705 GM/c³ (r₀ 30 M, speed 1.1); 5.7 ms–84 ms for 10 M☉ | `"world"`: the point's own default speed, a Kepler period in 8 played s | `fps: 8` |
| u35 | a photon's flight: 2 ns; 2 000–100 000 photons at 4·10⁹ s⁻¹: 0.5–25 µs | the build-up in 10 played s (5·10⁻⁸ to 2.5·10⁻⁶) | `frame_dt` = the stop time / 5 (the benches) or / 20 («Coatings») |
| u37 | a pair's flight: 1.67 µs (L = 500 m); 1 000–4 000 pairs at 10⁶ s⁻¹: 1–4 ms | the build-up in 10 played s: 1–4·10⁻⁴ | `frame_dt` = the stop time / 10 |

So u34 needs both the per-point speed and the frames per played second (§5 F1): with a fixed `frame_dt` its points
differ 15× in frames and size, and a fixed window that holds three radial periods of the slowest orbit holds 44 turns
of the circle at 7 M (from the world's own periods, Appendix A.1; *measured* at fps 15: a point grows with its frames,
0.38–0.43 kB per frame).
The «normal / slow» buttons stay: «slow» is a quarter of the screen's speed.

### 1.2 What a university screen shows, and what folds away

As EX1 §3.3 for `ui: "standard"`: the screen keeps the phenomenon, 2–3 controls, the overlays, the readouts and the
time bar; the world's own panels (`rightPanels`) fold into «How we know this is right», as u32's did (EX1 §6.3); the
quick set-up bar, the left form of live parameters, the actions and the toolbars are hidden in Watch, Explore and Lab
work and stay unchanged in «▶ Compute live». The per-world tables are §2.5, §3.7 and §4.5.

### 1.3 The views

Each of the three views gains what EX1 §2.4 lists and u32 has: `ctx.screen` (hide the quick bar, the toolbars and the
actions outside `live` and `recording`), `OVERLAYS`, `QUANT_SAFE`, `setOverlay`, tolerance of dropped blobs, a fixed
caption band in Watch (EX1 D8: a caption never covers what it describes), `setStory` (Watch keeps one scale for the
whole recording), and in Lab work the same drawing as in Explore (§5 F6). Below 1000 px each
view shows one picture at the top and folds its second picture under it (as u32 did on 2026-11-18, V52 (b)): u34 the
orbit plane (the plots folded), u35 the bench with its counters (the curves folded), u37 the statistics (the
set-up line folded to a strip). Each view exposes its layout boxes (`canvas.__layout`, as S03's view does) for the
browser tests (§7).

### 1.4 Lab work: a narrow bench (all levels, S03 included)

The owner, 2026-11-18 (§9, answer 1): a lab work is «аналог плейграундов, только по очень узному направлению, что-то
вроде стенда для проведения эксперимента, который можно проводить разными путями, часть из которых приведут к
правильным результатам, часть к неправильным». So:

- **The bench** is the world itself on a narrow topic: the set-ups the student chooses (the step's controls, on the
  atlas's grid), the instruments (their divisions, counters with √N), the moment of reading (the time cursor: a
  counting experiment can be stopped early, an orbit read after one turn or ten), the processing (several formula
  columns of the same readings), the plot and the model (any two columns, any fit model at the level). Every way a
  student can take on the bench is inside the computed atlases; each world lists its ways with their computed
  outcomes (§2.3, §3.4, §4.3, §10).
- **Nothing is hidden.** The drawer of Lab work is Explore's; the set-up values are shown (u35's glass index, S03's
  chute speed); the world's computed values for the bench are listed under «Computed for this bench» (§5 F6).
  **[error in earlier]** The first version's «glass of unknown index», its concealed checks and events, and its seed 2
  (to keep the lab's sample from the Explore's) are withdrawn: one sample per set-up (seed 1), shared where an Explore
  screen and a step are the same experiment (§5 F9).
- **The app judges nothing.** There is no «Check against the law»; the fit prints its output (§5 F6). The table, its
  CSV, the plot and the fit stay as conveniences, as a spreadsheet and a fitting program are in any laboratory; the
  students record and hand in their own measurements, and the teacher judges them («он уже сам проверяет и говорит у
  кого правильно получилось, у кого неправильно»).
- **The task sheet and the teacher's variants** (§5 F8). The teacher gets nothing beyond what everyone sees: the bench
  is open, the computed values are in the drawer and can be printed on a page of their own; a key of answers would be
  a test, which the owner excluded.
- **The level.** At school the fit prints the parameters with their errors only (χ², p and the Birge ratio at
  `standard`), the plot's default is the step's, and the ways are fewer and named in the procedure's hints; at
  university every column, plot and model is the student's choice.
- **Glossary.** «Task sheet» / «бланк задания» replaces «worksheet» / «рабочий лист» for Lab work's printable sheet
  (`RULES.md` §7, step I). **[error in earlier]** The first version's «For the instructor» / «Для преподавателя» is
  withdrawn with the teacher's pages.

---

## 2. u34 «Orbits and clocks»

### 2.1 Watch: yes — «A rosette, a closed ellipse and a fall» (recording `story`)

The phenomenon develops in time: the periapsis comes back later each turn (the rosette builds turn by turn), and the
body's clock falls behind. The cause → effect that one orbit does not show: Newton's orbit from the same start closes;
a launch closer to the hole turns faster; a little less speed near the hole and there is no orbit at all.

Recording `story`: the preset `default` (10 M☉, a black hole) with r₀ 20 M, speed 1.1 of the circular one, the ghost
on; 40 s at 20 fps; the script's speed 8.33·10⁻³ world s per played s (a radial period of 1 015 GM/c³ = 0.050 s in
6 s: slow motion ×1/120), then ×1/720 for the fall. The view keeps one scale for the whole recording (`setStory`: the
union of the story's trails, ±42 M, Newton's ellipse from 20 M reaching 41.0 M) and never refits at a new launch. The
plots are not folded in Watch, also at 390 px (Watch has no controls), so the clock caption describes something shown.

*Measured* (the script below, run headless): 800 frames, 0.43 MB (0.32 MB with the trails quantised u16), 0.5 s of CPU,
22 checks (20 ✓, 2 without a reference). Events at played time: periapsis 2 at 6.0 s (φ = 52.155°), 3 at 12.0 s, 4 at
18.0 s (156.47°); the relaunch at 19.0 s, its periapsis 2 at 22.05 s (120.36°); the fall from 7 M starts at 29.0 s and
crosses the stop above the horizon at 32.75 s, after τ = 2.59 ms of the body's clock. 1 − dτ/dt at the periapsis:
0.0838 at 20 M, 0.175 at 10 M.

| at, s | script | caption (EN / RU) | its event |
|---|---|---|---|
| 0 (hold 3) | `speed` 0.00833 | «A small body is launched from 20 M (M = GM/c² ≈ 14.8 km for this black hole of 10 M☉) at 1.1 times the circular speed. Solid: its orbit by general relativity; dashed: Newton's orbit from the same start.» / «Небольшое тело запущено с расстояния 20 M (M = GM/c² ≈ 14,8 км для этой чёрной дыры в 10 M☉) со скоростью в 1,1 раза больше круговой. Сплошная линия — его орбита по общей теории относительности, пунктир — орбита Ньютона из того же начала.» | the launch, 0 s |
| 3.5 | — | «Watch the closest point, the periapsis (diamond). Newton's ellipse comes back to it after one turn and closes on itself.» / «Следите за ближайшей точкой — перицентром (ромб). Эллипс Ньютона возвращается в неё через один оборот и замыкается.» | Newton's periapsis, 6.3 s |
| 5.5 | — | «In general relativity the body comes back to its closest point about 52° further on: the orbit turns.» / «По общей теории относительности тело возвращается в ближайшую точку примерно на 52° дальше: орбита поворачивается.» | periapsis 2, 6.0 s |
| 10 | — | «Each turn adds the same advance: after three turns the periapsis has moved by about 156°, and the orbit draws a rosette.» / «Каждый оборот добавляет то же смещение: через три оборота перицентр сдвинется примерно на 156°, и орбита рисует розетку.» | periapsis 4, 18.0 s |
| 19 | `set` r₀ 10 | «Launched again, closer: from 10 M at the same 1.1 of the circular speed. The advance grows to about 120° per turn.» / «Новый запуск ближе — с 10 M, с той же скоростью 1,1 от круговой. Смещение растёт примерно до 120° за оборот.» | periapsis 2, 22.05 s |
| 25 | — | «The plot 1 − dτ/dt is the body's clock: how much slower it runs than a distant clock. At the periapsis about 8 % at 20 M and 17.5 % at 10 M, from gravity and speed together.» / «График 1 − dτ/dt — это часы тела: насколько медленнее они идут, чем далёкие часы. В перицентре — около 8 % на 20 M и 17,5 % на 10 M, из-за тяготения и скорости вместе.» | the plot, shown since 0 s |
| 29 | `set` r₀ 7, speed 0.95; `speed` 0.00139 | «Now from 7 M with 5 % less than the circular speed, six times slower: this orbit has no closest point outside the horizon, and the body falls in. Newton's body, from the same start, keeps orbiting.» / «Теперь с 7 M и скоростью на 5 % меньше круговой, в шесть раз медленнее: у этой орбиты нет ближайшей точки вне горизонта, и тело падает. Тело Ньютона из того же начала продолжает обращаться.» | the fall, 29–32.75 s |
| 31.5 | — | «For a distant observer the body only approaches the horizon (the computation stops 2·10⁻⁶ M above it). By the body's own clock the fall from 7 M lasts 2.6 ms.» / «Для далёкого наблюдателя тело лишь приближается к горизонту (расчёт останавливается в 2·10⁻⁶ M над ним). По собственным часам тела падение с 7 M длится 2,6 мс.» | the stop, 32.75 s |

**More recordings** (`more`): `rosette`, `mercury`, `plunge`, each with captions, written and timed by W34 against
their own events by the same rule (the rosette: r₀ 20 M at 1.2, 40.9° per turn, apoapsis 69.7 M; Mercury: 0.1035″
per orbit, invisible on the drawing, 42.98″ per Julian century measured from the periapses; the plunge: a circle at
5.5 M, inside the ISCO, slowed by 0.5 %).

### 2.2 Explore: r₀ × speed (35 points)

| field | value | why |
|---|---|---|
| preset, fixed | `default`; `{ghost: true, time_units: "geo"}` | Newton's orbit from the same start is the comparison (an overlay, not a law control: the world stays accepted physics); times in GM/c³ so that the numbers do not depend on the mass |
| controls | r₀ {7, 8, 10, 12, 15, 20, 30} M («Start radius r₀», unit M) × speed {0.9, 0.95, 1.0, 1.05, 1.1} («Speed, × circular») | defaults 20 M, 1.1 (the story's start) |
| time, acts, traces | `flight`, `next`, 3 | ▶ launches; earlier orbits stay faded, labelled with what differs («r₀ 10 M») |
| speed, clock | `"world"`, `fps: 8` | a Kepler period in 8 played s, 64 frames per period |
| stop | `{events: {periapsis: 4, turn: 3, horizon: 1}, max_world_s: 1}` | three radial periods (3.5 from an apoapsis), three turns of a circle, or the fall (§5 F2; the world emits these events, §2.6) |
| quantize | `trail.t\|x\|y\|r\|lag: u16`, `gtrail.t\|x\|y\|r: u16` | drawn only; the apsides, measurables and checks stay float64 |
| overlays | Newton's orbit (on), GR radii 2M, 3M, 4M, 6M (on), periapses and their rays (on), the plots r(t) and 1 − dτ/dt (on at ≥ 1000 px, folded below), follow the body (off) | the view's own toggles today, minus «earlier segments» (one segment per point) |
| readouts | advance per orbit (mean of the observed orbits, °), ref: the exact elliptic integral; radial period (GM/c³), ref: the quadrature; τ/t since the launch, ref √(1 − 3M/r) on circles | from the checks `adv`, `period`, `rate` (§5 F7); the kind of orbit («bound», «plunge», «circular») is the view's text in the plane |

What changes visibly, *measured* (the world's own segment data for every grid point, Appendix A.1): the advance per
radial period grows from 33° (30 M, 1.1) to 256° (7 M, 1.05); the eccentricity and the apoapsis grow with the speed
(30 M: 30–49 M); every start below the circular speed at 7 and 8 M, and at 0.9 at 10 and 12 M, falls in, while Newton's
ghost stays on an ellipse; at 10 M and 0.95 the body dips to 6.13 M and whirls 438° per radial period (zoom-whirl);
at speed 1 the orbit is a circle, with no apsides (its turns are counted).

**[error in earlier]** EX1 §7: «periapsis r₀ (6–30 M, 7) × speed (0.9–1.3, 5)». *Measured*: from 6 to 12 M the fast
starts escape (from 1.2 on at 6 and 7 M, from 1.25 at 8 M, at 1.3 at 10 and 12 M); at 6 M, 1.15 is almost parabolic
(apoapsis 485 M, a radial period of 24 600 GM/c³, which no atlas can show in a few turns); and 6 M at speed 1 is the
marginally stable circle, where rounding decides the outcome. The grid starts at 7 M and stops at 1.1. EX1 also missed
the time scale (§1.1).

*Measured* points (fps 10, three radial periods; Appendix A.2): 119 kB (20 M, 1.1), 115 kB (30 M, 1.1), 158 kB (7 M,
1.05), 194 kB (10 M, 0.95), 64 and 69 kB (circles at 7 and 15 M), 25 kB (the fall from 7 M at 0.9); 0.04–0.28 s of
CPU each. *Estimate* at fps 8 (0.41 kB per frame, frames = 3 radial periods × 64 per Kepler period, from the survey):
**2.8 MB**, the largest point 168 kB (10 M, 0.95: three radial periods are 6.3 Kepler periods), accepted over the
150 kB target with that reason (`sitelib.ACCEPTED`).

### 2.3 Lab work: the bench «Orbits and clocks» (two parts)

**[error in earlier]** The first version made these two «lab works» with fixed procedures, hidden answers, questions
and a verdict on the student's fit. Revised as a bench (§1.4): the student chooses the orbits, the instrument, the
moment of reading, the plot and the model; the ways and their computed outcomes are listed below. The labs are
computational: no laboratory measures orbits near a black hole; the task sheet says so.

**Basis** (`worksheet.basis`, quoted verbatim; Appendix B):
- part 1: the CLEA laboratory «The Revolution of the Moons of Jupiter» (Gettysburg College, student manual v1.1.1):
  «Kepler’s Third Law is the one that applies to this lab.» and «You will determine Jupiter’s mass using measurements of
  each of the four moons; there will be errors of measurement associated with each moon, and therefore your Jupiter
  masses may not be exactly the same.» Here the moons are test bodies around a black hole, and the body's own clock is
  the new instrument.
- part 2: Taylor, Wheeler & Bertschinger, *Exploring Black Holes*, 2nd ed. (draft of 2020-03-31), ch. 10 «Advance
  of Mercury's Perihelion»: «According to Einstein, the advance of Mercury’s perihelion springs from the difference
  between the frequency with which the planet sweeps around in its orbit and the frequency with which it oscillates in
  and out in r. In Newton’s analysis these two frequencies are equal (for the interaction between Mercury and the
  Sun).» Its eq. (23), ω_φ − ω_r ≈ (3M/r₀)ω_φ, gives the advance per orbit 6πM/r₀, and its Query 11 asks the student
  to «Compare the JPL-computed advances of the perihelia of Venus, Earth, and Mars in Table 10.1 with approximate
  results calculated using equation (23).»

**The bench.** Two atlases (the stops differ from Explore's, so they are their own):

| part | atlas | grid | stop | clock |
|---|---|---|---|---|
| 1 «Periods and clocks» | preset `default`, fixed `{ghost: false, angle: 0, time_units: "geo"}` | r₀ {7, 8, 10, 12, 15, 20, 30, 50, 100} M × speed {1.0, 1.1} = 18 | `{events: {turn: 4, periapsis: 5}, max_world_s: 3}` (four turns of a circle, four radial periods of an ellipse) | `fps: 4`, `speed: "world"` |
| 2 «The advance of the periapsis» | fixed `{ghost: true, speed: 1.1, angle: 0}` | r₀ {20, 30, 50, 100, 150, 200, 300, 500, 700, 1000, 1500, 2000, 3000} M = 13 | `{events: {periapsis: 11}, max_world_s: 1000}` (ten radial periods) | `fps: 2`, `speed: "world"` |

**Instruments** (every set-up value exact, written without «± 0»):

| id | kind | reads | division | error |
|---|---|---|---|---|
| `radius` | readout | `control:r0` | 1 M | 0 (the console sets r₀) |
| `clock_far` | readout | `T_turn`: the distant observer's time per turn in φ, the mean over the turns so far | 0.1 GM/c³ | 0.05 |
| `clock_radial` | readout | `T_r`: the distant observer's time from periapsis to periapsis, the mean so far | 0.1 GM/c³ | 0.05 |
| `clock_body` | readout | `tau_turn`: the body's proper time per turn | 0.1 GM/c³ | 0.05 |
| `turns`, `peri_count` | counter | `n_lap`, `n_peri` (the launch's periapsis included) | 1 | 0 (exact counts) |
| `r_peri_scale`, `r_apo_scale` | readout | `r_peri`, `r_apo` at the apsis events | 1 M | 0.5 M |
| `protractor` | readout | `peri_shift`: the angle from the first periapsis ray to the latest | 0.1° | 0.05° |
| `fine_scale` | readout | `peri_shift` | 0.01° | 0.005° |
| `protractor_newton` | readout | `ghost_peri_shift`: the same angle on Newton's dashed orbit | 0.1° | 0.05° |

**Columns.** Part 1: r, T, T_r, τ, r_p, r_a, a = (r_p + r_a)/2, x = 1/r, q = (τ/T)². Part 2: r₀, n, N = n − 1,
Δφ = shift·π/180/N, Δφ_fine, Δφ_Newton (rad), r_p, r_a, x = M/p = (r_p + r_a)/(2 r_p r_a), y = Δφ_fine/x. Any two
columns can be plotted, with any fit model (line through 0, line, parabola, power law). **Computed for this bench**
(the drawer, §5 F6): the exponent 3/2 of T and the clock law (τ/T)² = 1 − 3M/r (the world's checks); the advance's
leading coefficient 6π and its next order 6π(18 + ε²)/4 = 85.03 for these orbits (`orbits.advance_series`); Newton's 0.

**The ways** (the readings rounded by the instruments' divisions and fitted by the engine's `linear_fit`, Appendix
A.3, A.5; deterministic, so the numbers are what every student gets):

| # | what the student does | what follows | why |
|---|---|---|---|
| 1 | circles (speed 1), T against r, power law | exponent 1.500014 ± 0.000022, the factor 6.2828 ± 0.0006 (2π) | Kepler's third law is exact for circular orbits in the distant observer's time |
| 2 | circles, τ against r, power law | exponent 1.535, χ²/dof 7·10⁴ | wrong clock: the body's clock runs slower by √(1 − 3M/r), which changes fast near 6 M |
| 3 | circles, (τ/T)² against M/r, line | intercept 0.999988 ± 0.000034, slope −2.9990 ± 0.0022 | the clock law, with Newton's τ = T (slope 0) rejected |
| 4 | eccentric orbits (speed 1.1), T_r against a = (r_p + r_a)/2, power law | exponent 1.423 ± 0.013, χ²/dof 5.6 (from 30 M on: 1.456 ± 0.014) | in general relativity the radial period of an eccentric orbit is not 2π a^{3/2}; Kepler's law needs a circle (or a weak field) |
| 5 | circles read after one turn instead of four | the same result with errors four times larger | a coarser measurement of a period |
| 6 | part 2, the 0.1° protractor after one orbit, r₀ ≥ 300 M, Δφ against M/p, line through 0 | 19.04 ± 0.24 (6π = 18.850) | the leading order holds within these errors |
| 7 | the same from r₀ = 20 M | 20.00 ± 0.27, χ²/dof 16.6 | an approximation outside its range: at 20 M the advance is 22 % above 6πM/p |
| 8 | the fine scale after ten orbits, line through 0 | 18.947 ± 0.023, χ²/dof 14.9 | data 100 times more precise show the next order |
| 9 | the same data, Δφ·p/M against M/p, line, r₀ ≥ 300 M | intercept 18.846 ± 0.012, slope 89.2 ± 9.5 (85.03) | the leading coefficient and the next order |
| 10 | the same from r₀ = 20 M | intercept 18.839 ± 0.008, slope 94.1 ± 3.7, χ²/dof 0.45 | the third order bends the line in the strong field: the slope drifts 2.5σ while χ² stays small |
| 11 | Newton's dashed orbit with its protractor | 0.0° at every r₀ | Newton's radial and angular frequencies are equal for one point mass |

**Variants** (`&variant=`; nothing is locked): A «Kepler with circles» (part 1, speed 1.0), B «Kepler with
eccentric orbits» (part 1, speed 1.1), C «The advance in a weak field» (part 2 from 300 M), D «The advance from
20 M» (part 2 from 20 M).

**Task sheet** (EN / RU):

| field | part 1 | part 2 |
|---|---|---|
| goal | Find how the period of an orbit around a black hole depends on its size, by the distant observer's clock and by the body's own clock. / Найти, как период орбиты вокруг чёрной дыры зависит от её размера, — по часам далёкого наблюдателя и по собственным часам тела. | Measure the advance of the periapsis per orbit and compare it with Einstein's formula 6πM/p. / Измерить смещение перицентра за оборот и сравнить его с формулой Эйнштейна 6πM/p. |
| bench | A test body around a black hole of 10 M☉, launched at r₀ from 7 to 100 M with the circular speed or 1.1 of it; the distant observer's clock, the body's clock, radius scales, a turn counter. Lengths in M = GM/c², times in GM/c³. / Пробное тело вокруг чёрной дыры в 10 M☉, запущенное с r₀ от 7 до 100 M с круговой скоростью или в 1,1 раза большей; часы далёкого наблюдателя, часы тела, шкалы радиусов, счётчик оборотов. Длины в M = GM/c², времена в GM/c³. | The same hole; orbits launched at r₀ from 20 to 3 000 M at 1.1 of the circular speed, followed for ten orbits; a protractor (0.1°) and a fine scale (0.01°) on the orbit's diagram, Newton's orbit from the same start (dashed) with its own protractor. / Та же дыра; орбиты, запущенные с r₀ от 20 до 3 000 M со скоростью 1,1 от круговой, на десять оборотов; транспортир (0,1°) и точная шкала (0,01°) на чертеже орбиты, орбита Ньютона из того же начала (пунктир) со своим транспортиром. |
| procedure (one suggestion) | For each r₀ launch a circular orbit and read both clocks after four turns. Plot T against r₀ on logarithmic axes and fit a power law; do the same for τ; then plot (τ/T)² against M/r₀. / Для каждого r₀ запустите круговую орбиту и снимите показания обоих часов после четырёх оборотов. Постройте T в зависимости от r₀ в логарифмических осях и аппроксимируйте степенным законом; то же для τ; затем постройте (τ/T)² в зависимости от M/r₀. | For each r₀ from 300 M read the periapsis shift after one orbit with the protractor and plot Δφ against M/p. Then read it after ten orbits with the fine scale and plot again; try Δφ·p/M against M/p. / Для каждого r₀ от 300 M снимите сдвиг перицентра после одного оборота по транспортиру и постройте Δφ в зависимости от M/p. Затем снимите его после десяти оборотов по точной шкале и постройте снова; попробуйте Δφ·p/M в зависимости от M/p. |
| record and hand in | the table of your readings with their errors; each fit: the model, the points used, the parameters with errors, χ²; your conclusion and why you chose these orbits. / таблицу своих отсчётов с погрешностями; для каждой аппроксимации — модель, использованные точки, параметры с погрешностями, χ²; свой вывод и почему выбраны эти орбиты. | the same / то же |

### 2.4 Sizes and cost of u34

| item | grid | size | CPU |
|---|---|---|---|
| Watch `story` | 40 s, 20 fps | **0.32 MB** *measured* (trails u16) | 0.5 s |
| more: `rosette`, `mercury`, `plunge` | as today, with captions | 0.51 MB *measured* today (0.27 + 0.17 + 0.07) | 1.6 s |
| Explore | 7 × 5 = 35 | **2.8 MB** *estimate* (points *measured* 25–194 kB at fps 10) | ~7 s |
| Lab part 1 | 9 × 2 = 18 | 0.36 MB *estimate* (20 kB per circle *measured*; ellipses alike) | 1 s |
| Lab part 2 | 13 | 1.3 MB *estimate* (196 kB *measured* for ten orbits at fps 4 with the ghost; fps 2 halves the frames) | 5 s |
| **u34 world** | | **5.3 MB** (target 12) | ~15 s |

### 2.5 What folds away at `ui: "standard"`

| today | Watch, Explore, Lab work | «▶ Compute live» |
|---|---|---|
| the orbit plane, the plots r(t) and 1 − dτ/dt | stay (the plots folded under the plane below 1000 px, except in Watch) | unchanged |
| quick bar: r₀, speed, angle, ghost, «push ±5 %», «↻ launch» | Explore: the atlas sliders r₀ and speed; the ghost an overlay; push and relaunch absent | unchanged |
| toolbar: earlier segments, GR radii, periapses, follow, «plots: whole segment», ⌖ orbit, ⌖ centre | overlays: Newton's orbit, GR radii, periapses, plots, follow; ⌖ orbit stays as a button | unchanged |
| left form (law, mass, radius, r₀, speed, angle, ghost, time units), actions | hidden | unchanged |
| right: «Orbit», «Clocks» | into «How we know this is right» (Explore keeps three readouts) | unchanged |
| the checks, «Physics of this world», events | the drawer, in Lab work as in Explore (§5 F6) | unchanged |

### 2.6 What the world gains (W34)

Measurables in the header (`measurables`) and per frame (`meas`): `adv_deg` with `adv_ref_deg`, `T_r` with
`T_r_ref`, `tau_over_t` (with `rate_ref` on circles), `T_turn`, `tau_turn`, `n_lap`, `n_peri`, `peri_shift`,
`ghost_peri_shift`, `r_peri`, `r_apo` — each the run's own measurement from its events, the references the ones its
checks use. An `event` of kind `periapsis` for every periapsis up to the 12th (today up to the 3rd, then every 100th)
and of kind `turn` for every turn of a circular orbit up to the 12th, so the stop rules can count them (live runs keep
the sparse rule beyond 12). `lab_reference` for the computed values of §2.3. The Newton ghost on the regularised
integrator (§11, item 10). The view: §1.3, plus `setTraces` (earlier orbits faded, labelled). `version` 1.0 → 1.1.

---

## 3. u35 «Optical bench»

### 3.1 Watch: yes — «One photon at a time at a surface» (recording `story`)

**[error in earlier]** EX1 §7 said «no (a steady split; the photon counting is statistics, not a process)». The
split is steady, but what the world shows of it develops in time and is not seen in any single picture: each photon's
wave leaves the surface on both arms (the frame's packets, weighted R/(R + T) and T/(R + T)), one detector clicks
and the other packet is gone (the null result), and the counts build up to R and T as u32's hits build up to the
fringes. The cause → effect a static curve does not show: at Brewster's angle the p photons stop being reflected;
from inside the glass, beyond the critical angle, none gets out; a second prism 200 nm away lets half of them
through.

Recording `story`: the preset `brewster` with θ 30°, unpolarised photons, 5·10⁸ photons per second; 50 s at 20 fps;
the script's speed 8.34·10⁻¹⁰ world s per played s (an arm of 0.30 m in 1.2 s), then from 9 s 4·10⁹ photons per
second at 5·10⁻⁷ (2 000 photons per played second). The bench's drawing does not move, so its scale is fixed anyway.

*Measured*: 1 000 frames, 1.58 MB (0.87 MB with the clicks' times quantised u16), 0.6 s of CPU, 37 checks ✓. The
first photon is emitted between 2 and 3 s, the first is detected between 5 and 6 s, the first reflected between 7
and 8 s; by 17 s 15 876 photons, 683 reflected (4.30 %, computed 4.152 %); at Brewster's angle unpolarised light gives
R = 7.396 %, all of it s; from glass into air at 30° R = 5.519 %; at 45° R = 1; with the 200 nm gap T = 49.876 %.

| at, s | script | caption (EN / RU) | its event |
|---|---|---|---|
| 0 (hold 3) | `speed` 8.34·10⁻¹⁰ | «Photons leave the source one at a time and fall on glass (n = 1.5) at 30°. Past the surface, each photon's wave goes both ways: the two faint marks show where it may be found.» / «Фотоны по одному вылетают из источника и падают на стекло (n = 1,5) под углом 30°. За поверхностью волна каждого фотона идёт в обе стороны: две бледные метки показывают, где его можно обнаружить.» | the first photon at the surface, ~4 s |
| 4 | — | «Watch the detectors: one of them clicks, and the photon is found in one place only, reflected or transmitted. Which one is random; the run computes only the probabilities R and T, from Maxwell's equations.» / «Следите за детекторами: срабатывает один из них, и фотон обнаруживается только в одном месте — отражённым или прошедшим. Какой — случайно; расчёт даёт лишь вероятности R и T, из уравнений Максвелла.» | the first click, 5–6 s |
| 9 | `set` rate 4·10⁹; `speed` 5·10⁻⁷ | «Much faster: thousands of photons. The fractions settle at the computed probabilities: about 4 % reflected and 96 % transmitted (the black ticks).» / «Гораздо быстрее: тысячи фотонов. Доли устанавливаются около рассчитанных вероятностей: примерно 4 % отражённых и 96 % прошедших (чёрные риски).» | the counts, 9–17 s |
| 17 | `set` θ 56.31°, the analyser before the reflection detector in, along p (α = 0°) | «The table turns to Brewster's angle, 56.3° = arctan 1.5, and an analyser is put before the reflection detector, along p (in the plane of incidence): no reflected photon passes it.» / «Столик поворачивается к углу Брюстера, 56,3° = arctg 1,5, и перед детектором отражённого света ставится анализатор вдоль p (в плоскости падения): ни один отражённый фотон через него не проходит.» | the new segment, 17 s |
| 22 | `set` the analyser to α = 90° (s) | «The analyser turned along s: every reflected photon passes. At Brewster's angle reflection polarises light completely.» / «Анализатор повёрнут вдоль s: проходит каждый отражённый фотон. При угле Брюстера отражение полностью поляризует свет.» | 22 s |
| 27 | `set` n₀ 1.5, n_s 1, θ 30°, structure `tir`, gap 0, the analyser out | «Now the light goes from inside the glass into air, at 30°: about 5.5 % is reflected.» / «Теперь свет идёт изнутри стекла в воздух, под углом 30°: отражается около 5,5 %.» | the new segment, 27 s |
| 34 | `set` θ 45° | «At 45°, beyond the critical angle of 41.8°, no photon gets out: total internal reflection.» / «При 45°, за критическим углом 41,8°, наружу не выходит ни один фотон: полное внутреннее отражение.» | the new segment, 34 s |
| 41 | `set` gap 200 nm | «A second glass block 200 nm behind the face: now about half of the photons cross the air gap. This is frustrated total reflection: the photons tunnel.» / «Второй стеклянный блок в 200 нм за гранью: теперь примерно половина фотонов пересекает воздушный зазор. Это нарушенное полное внутреннее отражение: фотоны туннелируют.» | the new segment, 41 s |

**Revised for the analyser (§3.5)**: the rows from 17 s are designed, not yet measured (the analyser does not exist
yet); W35 records them and replaces the times by the measured events. Unpolarised photons are drawn grey, not as s or
p: an unpolarised source is the density matrix I/2, and labelling each photon s or p is one of its decompositions, not
something the run measures (§11, item 1; **[error in earlier]**: the first caption at 17 s said that p photons
«(blue)» are not reflected). Each `set` of the media, the angle or the gap loses the photons in flight (7–14 each,
with the world's notice), as the world's README says. **More recordings**: `tir`, `brewster`, `spr`, with captions
written by W35 by the same rule.

### 3.2 Explore «Boundary» (`explore`): the reflection bench (444 points, shared with Lab work, §5 F9)

| field | value | why |
|---|---|---|
| preset, fixed | `brewster`; `{structure: "interface", lam_nm: 633, rate: 4e9}` | one boundary at one wavelength |
| controls | sample and side (compound, §5 F3): glass A (n 1.515), B (1.620), C (1.750), each «from air» (n₀ 1, n_s = n) and «from inside the glass» (n₀ = n, n_s 1): 6 × θ {0, 10, 20, 30, 34, 35, …, 62, 66, 70, 80, 85}° (37: 1° steps where Brewster's angles, 56.6°, 58.3°, 60.3°, and the critical angles, 41.3°, 38.1°, 34.8°, lie) × polarisation {s, p} | defaults: A from air, 30°, s; the glasses are the teacher's variants |
| time, acts, traces | `buildup`, `now`, 0 | the cursor is the count (a fifth, two fifths, … of the photons) |
| speed, clock, stop | 5·10⁻⁷ (20 000 photons in 10 played s); `frame_dt` a fifth of the run; `{world_s: 5.004·10⁻⁶}` | the lab's precision (§3.4); 20 000 photons per set-up |
| quantize | the angle curves, `segment.z\|E2`, `clicks.t`, `frame.fl`: u16 | drawn only; θ_B, θ_c, R, T and the counts stay float64 |
| drop | `blobs`: the flat spectrum (`segment.lam`, `segment.lR*`, `lT*`, `lA*`) and the clicks' `te`, `seg` (the view draws the clicks from `t`, `det`, `pol` only, `web/view.js pushClicks`) | |
| pool | the angle curves, the same for every θ and polarisation of a sample and side (§5 F10) | |
| overlays | beams, photons in flight, the field \|E\|², the curves R(θ), T(θ) for s and p with θ_B and θ_c (all on; the curves folded under the bench below 1000 px) | the view's drawing |
| readouts | reflected fraction R̂ ± its binomial error (ref: R of the segment), transmitted T̂ ± error (ref: T), photons detected | §5 F7 |

**[error in earlier]** EX1 §7: «angle θ (0–89°, 2°) × index n (1.33, 1.5, 1.7, 2.0) × polarisation (s, p,
unpolarised)»: 540 points, 17 MB at the *measured* 30–34 kB, over the 12 MB atlas limit, and an exit index alone never
shows total internal reflection. This design's first version (air → water, air → glass, glass → air; 4° steps; 2 000
photons) is replaced too: the bench needs the lab's precision and 1° steps where θ_B and θ_c lie.

*Measured* (Appendix A.6; 20 000 photons, six frames, z and the field u16): 15.2–18.4 kB per point; with the curves in
the pool 9.8–10.8 kB. *Estimate*: 444 × 10.3 kB = **4.6 MB**, the pool 6 × ~6 kB.

### 3.3 Explore «Coatings» (`coatings`): λ × coating (65 points)

As the first version (λ {400, 425, …, 700} nm × five coatings at normal incidence, 2 000 photons), with the coatings
named for what they are (§11, item 3): «bare glass (n 1.5)», «λ/4 layer, n_f 1.38», «ideal λ/4 layer, n_f = √1.5»,
«Bragg mirror (H L)×4» and «(H L)×8» (n_H 2.3, n_L 1.45 on glass 1.52; λ₀ = 550 nm), each a medium of constant index,
said so on the screen. **[error in earlier]** The first version kept the world's «like MgF₂» and «like TiO₂/SiO₂»,
which compare a constant index with real, dispersive materials. The spectrum curves of a coating are the same for every
λ, so they go to the pool. *Measured* 25–29 kB per point with the angle curves dropped; *estimate* with the pool about
15 kB: **1.0 MB**.

### 3.4 Lab work: the bench «Reflection and polarisation» (three parts)

**[error in earlier]** The first version was one fixed procedure on a hidden «glass of unknown index», with questions,
answers and a verdict. Revised as a bench (§1.4), with Malus's law added (the owner, answer 2; §3.5).

**Basis** (`worksheet.basis`; Appendix B):
- part 1: Carnegie Mellon University, 33-353 «Intermediate Optics», «Lab 1: FRESNEL RELATIONS and SNELL’S LAW» (Fall
  2010): «Find Brewster's angle, the angle for which there is no reflected beam for light polarized in the plane of
  reflection.», «Measure Brewster's angle and use it to determine the index of refraction of the plexiglass.», «Find
  the critical angle for total internal reflection.» and «Plot reflected power versus angle for each polarization and
  compare to theory.»; the Rutgers handout «Fresnel Equations and Electromagnetic Boundary Conditions»: «By fitting
  your data with Fresnel’s equations you will obtain the following: i) the index refraction ii) the critical angle iii)
  Brewster’s angle.»
- parts 2 and 3: University of Toronto, PHY293/PHY294 lab course, «Polarization of light»: «Exercise 1: Two
  Polarizers, verify Malus’ law», «This equation is known as Malus Law after its discoverer, E.L. Malus (1775-1812).»,
  «It applies to any two polarizing elements whose transmission directions make an angle θ with each other.»,
  «Exercise 3: Polarization by Reflection and Brewster’s angle», «When light is reflected from a flat surface, the
  reflected light is partially polarized.» and «For the experiment 3, state the obtained Brewster’s angle, find the
  refractive index of acrylic and compare your value with any reported in the literature.»

**The bench.**

| part | atlas | grid | photons per set-up |
|---|---|---|---|
| 1 «Fresnel's reflection» | Explore «Boundary» (§3.2, F9) | 6 samples and sides × 37 θ × {s, p} = 444 | 20 000 |
| 2 «Malus's law» | own: the structure «none» (no boundary: the beam goes straight to the transmission arm), the source linear at ψ {0°, 30°, 60°}, the analyser before the transmission detector at α {0°, 10°, …, 180°}, the analyser «ideal» or «real: k₁ 0.90, extinction ratio 10⁻²» | 3 × 19 × 2 = 114 | 20 000 |
| 3 «Polarisation by reflection» | own: unpolarised source, glass A, B or C from air, θ {40, 45, 50, 54, 55, 56, 57, 58, 59, 60, 62, 66, 70}°, the ideal analyser before the reflection detector at α {0°, 15°, …, 90°} | 3 × 13 × 7 = 273 | 100 000 (so that the p counts near θ_B resolve) |

**Instruments**: `table` (readout, `control:theta_deg`, 1°, exact: the rotary table is set at its marks); `det_R`,
`det_T` (counters, Poisson: photons counted by the reflection and the transmission detectors); `ana_angle` (readout,
`control:ana_deg`, 1°, exact); `det_pass`, `det_reject` (counters, Poisson: the two ports of the analyser, a rotatable
polarising beam splitter with a detector on each port, §3.5). The source's ψ, the sample's index and the analyser's
device are set-up values, shown.

**Columns.** Part 1: θ, N_R, N_T, R = N_R/(N_R + N_T), x = sind(θ)², y_s = (cosd(θ)·(1 + sqrt(R))/(1 − sqrt(R)))²,
y_p = (cosd(θ)·(1 − sqrt(R))/(1 + sqrt(R)))². Part 2: α, ψ, N_pass, N_reject, I = N_pass/(N_pass + N_reject),
c2 = cosd(α − ψ)², c1 = cosd(α − ψ). Part 3: θ, α, N_pass, N_reject, f = N_pass/(N_pass + N_reject), P = 1 − 2f (the
degree of polarisation when α = 0°, along p). **Computed for this bench** (the drawer): n², 1/n², −1/n⁴, θ_B = arctan n,
θ_c = arcsin(1/n) of the sample; Malus's I = k₁cos²(α − ψ) + k₂sin²(α − ψ) of the analyser; the degree of polarisation
(R_s − R_p)/(R_s + R_p) of the reflected light.

**The linearisations** of part 1 (derived for this design; W35 tests them against the engine and a 30-digit evaluation
of Fresnel's formulae): for light from air into n, √R_s = (n cos θ_t − cos θ)/(n cos θ_t + cos θ), so
y_s = n² − sin²θ, a line in x = sin²θ with intercept n² and slope −1; below Brewster's angle √R_p = (n cos θ − cos
θ_t)/(n cos θ + cos θ_t) ≥ 0, so y_p = 1/n² − sin²θ/n⁴. Both are exact for a lossless boundary; above θ_B, r_p changes
sign and y_p would need −√R_p.

**The ways** (glass A, n = 1.515; Monte Carlo with Poisson counts and the engine's fit, Appendix A.3, A.5; the analyser
parts from the closed forms of §3.5, *estimate* until W35's atlas exists):

| # | what the student does | what follows | why |
|---|---|---|---|
| 1 | s light from air, all θ, y_s against sin²θ, line | intercept 2.2944 ± 0.0183 (n = 1.515 ± 0.006), slope −1.000 ± 0.030 | right |
| 2 | p light from air below θ_B (θ ≤ 52°), y_p, line | intercept 0.4356 ± 0.0033 (n = 1.515 ± 0.006), slope −0.1896 | right |
| 3 | p light through 62°, past θ_B, with the same formula | intercept 0.497 ± 0.019 (n = 1.42), χ²/dof 59 | a wrong sign branch: r_p < 0 above θ_B |
| 4 | a parabola through R_p(θ) near θ_B, its vertex | over 50–63°: 56.17–56.19°, 0.4° below 56.57° (3.7σ at 20 000 photons, 18σ at 400 000); over 52–61°: 56.36–56.38° (1.7σ to 8σ) | an approximation: R_p is not symmetric about θ_B |
| 5 | the angle of the smallest p count, 1° steps | none at 56° and 57° (expected 0.7 and 0.4 photons), about 5 at 55° and 58°: θ_B = 56.5° ± 1°, n = tan θ_B to ±0.06 | right, coarse |
| 6 | from inside the glass: the last angle with transmitted photons | between 41° and 42°: n = 1/sin θ_c between 1.494 and 1.524 | right, coarse |
| 7 | inside data with the formula y_s (made for light from air) | from θ_c on R = 1, and the cell is empty («division by zero»); below θ_c the formula has no meaning for this geometry | a formula used outside its derivation |
| 8 | the cursor at a fifth of the run (4 000 photons) | the same n with errors √5 larger (± 0.0075 on 1/n²) | too few counts |
| 9 | part 2, ideal analyser: I against cos²(α − ψ), line through 0 | slope 1.00000 ± 0.00005, χ²/dof 1.0 (*simulated* on the closed form) | Malus's law |
| 10 | I against cos(α − ψ) | the points lie on x², not on a line | a wrong angle law |
| 11 | the real analyser with a line through 0 | slope 0.9026 ± 0.0010, χ²/dof 17.9: at α − ψ = 90° I = k₂ = 0.009, 13 errors above the line's 0; a line with an intercept gives 0.009 and the slope k₁ − k₂ = 0.891 (*simulated* on the closed form) | an ideal model for a real device |
| 12 | part 3, analyser along p: P against θ | P ≈ 1 at 56° and 57° for A (expected p counts 1.8 and 1.1 of 7 500 reflected), at 58° for B, at 60° for C: θ_B to ±1°, n to ±0.06 | polarisation by reflection: right, coarse |
| 13 | part 3, both ports added (the analyser ignored): the angle of the weakest reflection | none near θ_B: the unpolarised reflectance (R_s + R_p)/2 rises monotonically, from 4.2 % at 0° to 7.7 % at 56.6° | Brewster's angle is not where the reflection is weakest |

**Variants**: the glass (A, B, C) for parts 1 and 3; the source's ψ and the analyser device for part 2.

**Task sheet** (EN / RU):

| field | text |
|---|---|
| goal | Find the refractive index of a glass from the reflection of s and p light, and check Malus's law and the polarisation of reflected light. / Определить показатель преломления стекла по отражению света с поляризацией s и p, проверить закон Малюса и поляризацию отражённого света. |
| bench | A glass block on a rotary table (1° marks), light from air or from inside the glass; a source of single photons (633 nm), polarised s, p, linearly at an angle or unpolarised; detectors of reflected and transmitted photons; a rotatable analyser (a polarising beam splitter with a detector on each port), ideal or real. / Стеклянный блок на поворотном столике (деления 1°), свет из воздуха или изнутри стекла; источник одиночных фотонов (633 нм) с поляризацией s, p, линейной под углом или неполяризованный; детекторы отражённых и прошедших фотонов; поворотный анализатор (поляризационный делитель с детектором на каждом выходе), идеальный или реальный. |
| procedure (one suggestion) | 1. For s light from air, count reflected and transmitted photons at angles from 0° to 80° and plot y_s against sin²θ. 2. Repeat for p light below the angle where the reflection vanishes, with y_p. 3. Set the source at ψ and record the analyser's counts from 0° to 180°; plot them against cos²(α − ψ). 4. With unpolarised light, set the analyser along p and find the angle of complete polarisation. / 1. Для света с поляризацией s из воздуха посчитайте отражённые и прошедшие фотоны при углах от 0° до 80° и постройте y_s в зависимости от sin²θ. 2. Повторите для света p при углах меньше того, где отражение исчезает, с y_p. 3. Поставьте источник под углом ψ и запишите отсчёты анализатора от 0° до 180°; постройте их в зависимости от cos²(α − ψ). 4. С неполяризованным светом поставьте анализатор вдоль p и найдите угол полной поляризации. |
| record and hand in | the counts with their errors, the plots and fits (model, points used, parameters with errors, χ²), the index n found in each way and Brewster's angle, and why you chose these angles. / отсчёты с погрешностями, графики и аппроксимации (модель, использованные точки, параметры с погрешностями, χ²), показатель n, найденный каждым способом, и угол Брюстера, а также почему выбраны эти углы. |

### 3.5 Polarisation through the bench, strictly computed (the owner, answer 2)

**The state.** Each beam carries a 2 × 2 polarisation density matrix ρ in its own basis (p̂, ŝ), p̂ in the plane of
incidence, ŝ normal to it, (p̂, ŝ, k̂) right-handed; a pure state is a Jones vector J, ρ = JJ†. The source: linear at
ψ from p̂ (ψ any angle; s and p are ψ = 90° and 0°), or unpolarised, ρ = I/2. Nothing else is assumed: no s and p
labels on photons of an unpolarised source.

**The boundary.** From `interfaces.stack` (the engine's transfer matrices, unchanged), the reflection matrix
M_R = diag(r_p, r_s) and the transmission matrix M_T = diag(η_p t_p, η_s t_s), η the power factors (√(Re(n_out cos
θ_t)/Re(n_in cos θ)) for s and its p counterpart, as `stack` defines T_s and T_p), each in the outgoing beam's basis
under the engine's sign convention, which the module states and tests. Then ρ_R = M_R ρ M_R† and ρ_T = M_T ρ M_T†, their
traces the probabilities P_R and P_T, and P_A = 1 − P_R − P_T. Beyond the critical angle |r_s| = |r_p| = 1 with
different phases, so a linear input comes back elliptical, with the phase difference δ = δ_p − δ_s given by
tan(δ/2) = cos θ √(sin²θ − n²)/sin²θ (n = n_out/n_in < 1): the bench draws the reflected polarisation ellipse from ρ_R.

**The analyser** in each detector arm: a rotatable polarising beam splitter at angle α from p̂, with the principal
transmittances k₁ (along its axis) and k₂ (across), a stated device property: ideal k₁ = 1, k₂ = 0 by default; a real
one is a device, not modified physics (no `standard` flag; the schema's group «Devices»). Its pass port has the
operator A = R(−α) diag(√k₁, √k₂) R(α), its reject port the complementary one, diag(√(1 − k₁), √(1 − k₂)) in the same
frame, so that the two ports' probabilities add to 1 (an ideal beam splitter loses nothing). Malus's law follows:
for a linear input at ψ, P_pass = k₁ cos²(α − ψ) + k₂ sin²(α − ψ).

**The photons.** Each photon's outcome is drawn by the Born rule from ρ: {reflected and passed, reflected and
rejected, transmitted and passed, transmitted and rejected, absorbed in the structure}, the five probabilities
tr(A_R ρ_R A_R†), … (an arm without an analyser has one detector, as today). The fate is revealed at the detector, as
today; an unpolarised photon is drawn grey.

**Where in the engine** (`lfphys/LAYERS.md`): a **new core module** `lfphys.core.optics.polarization` — Jones vectors
and matrices, density matrices, Stokes parameters and Mueller matrices, rotations, the polariser and polarising beam
splitter devices with k₁ and k₂, the reflection and transmission matrices of a planar structure built from
`interfaces.stack`, the degree of polarisation and the ellipse's parameters. Core, because it is the exact classical
optics of plane waves in linear media and the same two-dimensional Hilbert space for one photon; its validity: plane
waves, isotropic planar structures (no s ↔ p mixing), linear media. **An extension** of `core.optics.interfaces`:
`field_profile` for p light (E_x and E_z from H_y, which the transfer matrix carries), and the field of any Jones
state (§11, item 2).

**Tests** (`lfphys/tests/test_polarization.py`, against closed forms and second methods): Malus's cos² for ideal and
real analysers at random ψ, α (1e-14); at θ_B the reflected light is pure s for any input (ρ_R ∝ ŝŝ†; its degree of
polarisation 1 to 1e-12) and P = (R_s − R_p)/(R_s + R_p) for unpolarised light at every θ; TIR's δ against the closed
form above at 1 000 random (n, θ) (1e-12) and against 30-digit Fresnel coefficients; energy: P_R + P_T + P_A = 1 and
the two ports of an analyser add to the incoming probability, for random ρ (1e-14); Mueller against Jones (the same
Stokes vector by two routes); an analyser is passive (the eigenvalues of A†A ≤ 1); the p field profile against the
Joule check for p (as `joule_absorption_s` does for s) and the continuity of the tangential fields. The world's checks
add: Malus's law against the closed form; the reflected degree of polarisation against (R_s − R_p)/(R_s + R_p); TIR's δ
against the closed form; the probabilities' sum; and the photon counts of all five outcomes against the Born
probabilities (the exact binomial tails with Bonferroni, failing below 5σ, as `stat` does for three).

**Explore «Polarisation»** (`polarisation`): TIR's phase. Glass A from inside × θ {42, 45, 48, 51, 54, 57, 60, 65, 70,
80}° × the analyser α {0°, 15°, …, 165°}, the source linear at 45°: 120 points, 20 000 photons. What changes visibly:
below θ_c the reflected light is linear and the analyser finds a zero; beyond it the light is elliptical, the
analyser's minimum rises, largest at θ = 51.2° where δ is largest, 46.3° for n = 1.515 (the principle of
Fresnel's rhomb). *Estimate* 1.2 MB.

### 3.6 Sizes and cost of u35

| item | grid | size | CPU |
|---|---|---|---|
| Watch `story` | 50 s, 20 fps | 0.87 MB *measured* without the analyser; ~0.9 MB with it | 0.6 s |
| more: `tir`, `brewster`, `spr` | as today, with captions | 0.43 MB *measured* today | 0.6 s |
| Explore «Boundary» = Lab part 1 | 444 | **4.6 MB** *estimate* (9.8–10.8 kB *measured* with the pool emulated) | ~10 s |
| Explore «Coatings» | 65 | 1.0 MB *estimate* | ~4 s |
| Explore «Polarisation» | 120 | 1.2 MB *estimate* | ~3 s |
| Lab part 2 «Malus» | 114 | 1.1 MB *estimate* | ~3 s |
| Lab part 3 «Polarisation by reflection» | 273 | 2.7 MB *estimate* (100 000 photons; the clicks do not grow with the count) | ~15 s |
| **u35 world** | | **11.9 MB** (target 12) | ~40 s |

The estimates for the analyser's points take the *measured* pooled point (about 10 kB) as their size: the analyser
adds two outcomes to the clicks' codes and a few numbers to the frames. W35 measures them.

### 3.7 What folds away at `ui: "standard"`

| today | Watch, Explore, Lab work | «▶ Compute live» |
|---|---|---|
| the bench (beams, photons, detectors, the structure to scale, \|E\|²) and the curves panel (R(θ), R(λ), counters) | stay; below 1000 px the bench with its counters on top, the curves folded under it | unchanged |
| quick bar: λ, θ, polarisation, structure, «▷ photon flight», «▷▷ collect statistics» | Explore and Lab work: the atlas's sliders; the two speeds become the screen's «normal / slow» | unchanged |
| left form: the parameters of six structures, the source and the analysers; actions «Emit one photon», «Reset the counters» | hidden | unchanged |
| right: «Set-up of this segment», «Photons», «Approximations» | into «How we know this is right» | unchanged |

### 3.8 What the world gains (W35, after E35)

The source's linear polarisation at ψ; an analyser (a polarising beam splitter with two detectors) before each
detector, in or out, at α, with k₁ and k₂ as device parameters; the structure «none»; the five outcomes and their
counts; the polarisation ellipse of each beam drawn from its ρ; unpolarised photons grey. Measurables: `n_R`, `n_T`,
`n_A`, `n`, the analysers' `n_pass` and `n_reject`, `R_frac` and `T_frac` with their binomial errors and the computed R
and T as references. Presets `malus` and `brewster_analyser`. `lab_reference` for the computed values of §3.4.
`QUANT_SAFE` for the curves, the field, the depth grid, the clicks' times and the packets. The coatings' labels (§3.3).
`version` 1.0 → 1.1.

---

## 4. u37 «The Bell test»

### 4.1 Watch: yes — «Pairs, S above 2, and a local model» (recording `story`)

The pairs arrive one by one and S emerges from their counts: a statistical build-up with a threshold (2) that the
quantum world crosses and a local world does not. Recording `story`: the preset `photon_chsh` (random choice τ = 100 ns
before arrival, L = 500 m, 10⁶ pairs per second); 50 s at 20 fps; the script's speed 8.34·10⁻⁷ world s per played s
(a flight in 2 s, about one pair per played second), from 10 s 2·10⁻⁴ (200 pairs per played second); at 34 s a new
world, `photon_lhv` (flagged «MODIFIED PHYSICS» by the player for the rest of the recording), at the same speed.

*Measured*: 1 000 frames, two worlds, 0.64 MB, 0.7 s of CPU; 45 check rows: 36 ✓, 7 without a reference, 2 for
information. The first pair is detected at 3.3 s; the world's event «Violation of the CHSH inequality by 6.2σ: S =
3.077 ± 0.175 (204 pairs)» comes at 10.9 s (an early fluctuation 1.4σ above 2√2); at 33.9 s S = 2.864 ± 0.040 after
4 938 pairs, 21.8σ above 2; in the local world at 49.9 s S = 1.458 ± 0.066 after 3 217 pairs (the model's √2 = 1.414).

| at, s | script | caption (EN / RU) | its event |
|---|---|---|---|
| 0 (hold 3) | `speed` 8.34·10⁻⁷ | «A source in the middle sends pairs of polarisation-entangled photons to Alice (left) and Bob (right), 500 m away on each side, one pair at a time.» / «Источник в середине посылает по одной паре запутанных по поляризации фотонов к Алисе (слева) и Бобу (справа); каждый из них в 500 м от источника.» | the first emission |
| 3 | — | «Shortly before each photon arrives, its station picks one of its two polariser settings at random (Alice a or a′, Bob b or b′). Each photon then gives + or −.» / «Незадолго до прихода фотона его станция случайно выбирает одну из двух установок поляризатора (Алиса — a или a′, Боб — b или b′). Каждый фотон даёт + или −.» | the first detection, 3.3 s |
| 10 (hold 4) | `speed` 2·10⁻⁴ | «Much faster: thousands of pairs. From the counts the run computes the correlations E and S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′). No local theory allows S above 2; here S passes 2 and settles near 2√2 ≈ 2.83.» / «Гораздо быстрее: тысячи пар. По счёту совпадений расчёт находит корреляции E и S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′). Никакая локальная теория не допускает S больше 2; здесь S переходит через 2 и устанавливается около 2√2 ≈ 2,83.» | the violation event, 10.9 s |
| 20 | — | «The error of S shrinks as 1/√N: after about 5 000 pairs S = 2.86 ± 0.04, more than 20 standard errors above 2.» / «Погрешность S убывает как 1/√N: после примерно 5 000 пар S = 2,86 ± 0,04 — больше чем на 20 стандартных погрешностей выше 2.» | 33.9 s |
| 34 | `new_world` `photon_lhv`; `speed` 2·10⁻⁴ | «The same experiment in a world of local hidden variables, a deliberately changed law: each pair carries a common hidden polarisation, and each outcome depends only on it and on its own polariser.» / «Тот же опыт в мире локальных скрытых параметров — намеренно изменённом законе: каждая пара несёт общую скрытую поляризацию, и каждый исход зависит только от неё и от своего поляризатора.» | the new world, 34 s |
| 44 | — | «Here S stays below 2: about 1.4, the most this model gives at any settings (√2).» / «Здесь S остаётся ниже 2: около 1,4 — больше эта модель не даёт ни при каких установках (√2).» | 49.9 s |

**More recordings**: `chsh`, `local_model`, `scan`, with captions by W37.

### 4.2 Explore: the CHSH bench (156 points, shared with Lab work, §5 F9)

| field | value | why |
|---|---|---|
| preset, fixed | `photon_chsh`; `{switch: "random", L_m: 500, rate: 1e6}` | random choice before each arrival |
| controls | pair {photons, spin ½} × Δ (compound, §5 F3: a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ) {0, 7.5, …, 90}° (13) × τ {100 ns, 5 µs} × law and source (compound): «quantum, ideal source», «quantum, source visibility 0.85» (a stated source property, §11 item 14), «local hidden variables» (a law control: «MODIFIED PHYSICS» at `standard`, EX1 §2.1) | defaults: photons, 22.5°, 100 ns, quantum ideal |
| time, acts, traces | `buildup`, `now`, 5 | earlier Δ's S stay on the S(Δ) plot, faded |
| speed, clock, stop | 4·10⁻⁴ (4 000 pairs in 10 played s); `frame_dt` a tenth of the run; `{world_s: 4.0033·10⁻³}` | §1.1 |
| overlays | the set-up line with the stations and the flashes, the spacetime diagram of the last pair (folded below 1000 px), E(Δ) with the measured cells, S(Δ) with the measured S and its traces, the other law's curves (all on) | the S(Δ) plot is new (§4.6) |
| readouts | S ± σ (ref: S of the world's law and source at these settings), (\|S\| − 2)/σ, pairs counted, the fraction of pairs whose choices are space-like to the other detection | §5 F7 |

What changes visibly: S(Δ) = 3 cos 2Δ − cos 6Δ for photons (2√2 at 22.5°), −(3 cos Δ − cos 3Δ) for spins (−2√2 at
45°), times the visibility for the imperfect source, half for the local polarisation model; with τ = 5 µs (cτ =
1.5 km > 2L) no choice is space-like to the other detection.

**[error in earlier]** EX1 §7: «analyser angle b (0–90°, 5°) × law». With a, a′ and b′ fixed, b alone moves one cell of
S and does not show the CHSH curve. This design's first version (Δ × law, 26 points) lacked the spins, the choice's
timing and a real source, without which the bench has no wrong ways.

*Measured*: 16.9 kB per point at 4 000 pairs and ten frames (photons; 27.7–29.3 kB at twenty frames for spins and for
τ = 5 µs). *Estimate*: 156 × 17 kB = **2.7 MB**.

### 4.3 Lab work: the bench «Entangled photons and the Bell inequality» (three parts)

**[error in earlier]** The first version had fixed procedures, questions, answers and verdicts. Revised as a bench
(§1.4).

**Basis** (`worksheet.basis`; Appendix B): D. Dehlinger and M. W. Mitchell, «Entangled photons, nonlocality, and Bell
inequalities in the undergraduate laboratory», Am. J. Phys. 70, 903 (2002) (arXiv:quant-ph/0205171): «The experiments
described can be performed in an afternoon.» Their E(α, β) comes from four coincidence counts and S from sixteen, the
error of each count from counting statistics («To be sure of the result, we compute its statistical uncertainty.»), and
they conclude «We have violated the Bell inequality.» with S = 2.307 ± 0.035.

**The bench.**

| part | atlas | grid | pairs per set-up |
|---|---|---|---|
| 1 «The correlation E(α, β)» | own: fixed settings (preset `scan`) | pair {photons, spin ½} × a {0°, 45°, 90°} × b {0°, 7.5°, …, 180°} = 2 × 3 × 25 = 150 | 1 000 |
| 2 «The CHSH test» | Explore's (§4.2, F9) | 156 | 4 000 |
| 3 «The same test in a local world» | Explore's, the law «local hidden variables» (flagged) | (within the 156) | 4 000 |

**Instruments**: `pol_A`, `pol_B` (readouts of `control:a_deg`, `control:b_deg`, 0.5°, exact); `delta`, `tau` (readouts
of the compound Δ and of τ, exact); `c_pp`, `c_pm`, `c_mp`, `c_mm` (counters, Poisson: the coincidences of the setting
pair (a, b)); `E_1` … `E_4` (readouts of the run's E of each setting pair, with the run's own standard error √((1 −
E²)/N), F4); `local_frac` (a readout of the fraction of pairs whose choices are space-like to the other detection,
the run's `st_frac`). **Columns**: part 1: a, b, N₊₊, N₊₋, N₋₊, N₋₋, E = (N₊₊ + N₋₋ − N₊₋ − N₋₊)/(N₊₊ + N₋₋ + N₊₋ +
N₋₊) (Dehlinger and Mitchell's eq. (25) with two-channel analysers), c2 = cosd(2(b − a)), c1 = cosd(b − a); parts 2–3:
Δ, τ, E₁ … E₄, S = E₁ − E₂ + E₃ + E₄, x_ph = 3 cosd(2Δ) − cosd(6Δ), x_sp = −(3 cosd(Δ) − cosd(3Δ)), the space-like
fraction. **Computed for this bench**: E and S of the world's law and source at each setting; the bounds 2 and 2√2.

**The ways** (Monte Carlo of the Born rule on the closed forms with the engine's fit, Appendix A.3; the world's own
statistics are tested against the same forms):

| # | what the student does | what follows | why |
|---|---|---|---|
| 1 | part 1, photons: E against cos 2(b − a), line through 0 | slope 1.0001 ± 0.0017 | right: a polariser's outcome depends on 2(β − α) |
| 2 | photons: E against cos(b − a) | the points lie on 2x² − 1, not on a line | a wrong angle law: a polariser's axis has no direction (period 180°) |
| 3 | spins: E against cos(b − a); against cos 2(b − a) | slope −1; a curve, not a line | right; the photons' law used for spins is wrong |
| 4 | the cursor at a tenth of the run (100 pairs) | σ_E about 0.1 instead of 0.03 | too few pairs |
| 5 | the four E at a ∈ {0°, 45°}, b ∈ {22.5°, 67.5°} from part 1 (fixed settings, one after another) | S = 2.83 ± 0.045 | the right value, but the settings were set long before each pair: the run's spacetime check says time-like; not a test of locality |
| 6 | part 2, photons, Δ = 22.5°, τ = 100 ns, ideal source | S = 2.83 ± 0.045, (S − 2)/σ ≈ 18, every choice space-like to the other detection | right |
| 7 | photons at Δ = 45°; spins at Δ = 22.5° | S = 0; \|S\| = 2.39 | the wrong angle set (the spins' optimum is 45°, their \|S\| = 2√2 there) |
| 8 | τ = 5 µs | S = 2.83 as before, but no choice space-like to the other detection (cτ = 1.5 km > 2L = 1 km) | the locality loophole open |
| 9 | 400 pairs (a tenth of the run); the source of visibility 0.85 | σ_S about 0.14, (S − 2)/σ ≈ 6; S = 2.40 (Dehlinger and Mitchell's 2.307 corresponds to a visibility of about 0.82) | too few pairs; a real source |
| 10 | S against x_ph over Δ, line through 0, quantum; then the local world | slope 0.9996 ± 0.0057; local 0.5003 ± 0.0085 with \|S\| ≤ √2 at every Δ | the quantum law; a local model never passes 2 |

**Variants**: the pair (photons, spins), τ, the source; part 1's set of a.

**Task sheet** (EN / RU):

| field | text |
|---|---|
| goal | Measure the polarisation correlation of entangled photons and test the CHSH form of Bell's inequality. / Измерить корреляцию поляризаций запутанных фотонов и проверить неравенство Белла в форме CHSH. |
| bench | A source of entangled pairs (photons \|Φ⁺⟩ or spin-½ singlets) between two stations 500 m away on each side; at each station an analyser with two outputs and two detectors, set by hand or chosen at random τ before each arrival; coincidence counters; a source of ideal or imperfect visibility; a world with local hidden variables for comparison (modified physics). / Источник запутанных пар (фотоны \|Φ⁺⟩ или синглеты спина ½) между двумя станциями в 500 м по обе стороны; на каждой станции анализатор с двумя выходами и двумя детекторами, установка задаётся вручную или выбирается случайно за τ до прихода частицы; счётчики совпадений; источник с идеальной или неполной видностью; для сравнения — мир локальных скрытых параметров (модифицированная физика). |
| procedure (one suggestion) | 1. With fixed settings, count the four coincidences for α = 0° and β from 0° to 180°; compute E and plot it against cos 2(β − α). 2. With random settings at Δ = 22.5°, read E of the four setting pairs and compute S with its error. 3. Repeat at other Δ and in the local world. / 1. При фиксированных установках посчитайте четыре числа совпадений для α = 0° и β от 0° до 180°; вычислите E и постройте его в зависимости от cos 2(β − α). 2. При случайных установках и Δ = 22,5° снимите E четырёх пар установок и вычислите S с погрешностью. 3. Повторите при других Δ и в локальном мире. |
| record and hand in | the counts and E with their errors, S with its error and (S − 2)/σ, the fits (model, points, parameters, χ²), the settings and τ you used, and your conclusion. / числа совпадений и E с погрешностями, S с погрешностью и (S − 2)/σ, аппроксимации (модель, точки, параметры, χ²), использованные установки и τ, свой вывод. |

### 4.4 Sizes and cost of u37

| item | grid | size | CPU |
|---|---|---|---|
| Watch `story` | 50 s, 20 fps, two worlds | **0.64 MB** *measured* | 0.7 s |
| more: `chsh`, `local_model`, `scan` | as today, with captions | 0.13 MB *measured* today | 1.5 s |
| Explore = Lab parts 2 and 3 | 2 × 13 × 2 × 3 = 156 | **2.7 MB** *estimate* (16.9 kB *measured* at ten frames) | ~6 s |
| Lab part 1 | 150 | 1.35 MB *estimate* (9–10 kB *measured*) | ~3 s |
| **u37 world** | | **4.8 MB** (target 12) | ~12 s |

### 4.5 What folds away at `ui: "standard"`

| today | Watch, Explore, Lab work | «▶ Compute live» |
|---|---|---|
| the set-up line and the spacetime diagram; the statistics (the cells, S, E(Δ)) | stay; below 1000 px the statistics on top, the set-up line a strip, the spacetime diagram folded | unchanged |
| quick bar: a, a′, b, b′, choice, τ, L; toolbar: «▷ flight», «▷▷ collect statistics», «⟲ reset the statistics», light cones, the other law's curve | Explore and Lab work: the atlas's sliders; light cones and the other law's curve become overlays; the speeds the screen's «normal / slow» | unchanged |
| left form: pairs, the particles' speed, law, L, rate, choice, τ, the four angles, the source's visibility | hidden | unchanged |
| right: «Set-up and spacetime», «Counters», «Last pairs» | into «How we know this is right» | unchanged |

### 4.6 What the world gains (W37)

Frames get `meas` (u37 has none today) and the header `measurables`: `n_pp`, `n_pm`, `n_mp`, `n_mm` of the pair (a,
b), `E_ab` … `E_a2b2` with their errors, `S` with its error and the law's S as its reference, the pairs counted, the
space-like fraction. The source's visibility V as a world parameter (§11, item 14): the pair's state ρ = V|ψ⟩⟨ψ| + (1 −
V) I/4, sampled by the Born rule (`qubits` already samples density matrices), with the checks' references times V; V
= 1 is the standard, and V < 1 is a stated source property, not modified physics. A header blob of the law's S(Δ) in
the CHSH geometry for both laws, computed with the world's own `Law.E`. `lab_reference` for the computed values of
§4.3. The view: §1.3 and the S(Δ) plot with traces. `version` 1.0 → 1.1.

---

## 5. The framework changes (step F, before the worlds)

**Revised on 2026-11-18 after the owner's answers (§9).** Lab work is a narrow experimental bench, not a test: nothing
is hidden, the app judges nothing, and the worksheet becomes a task sheet the teacher may change. So F6 and F8 are
rewritten, and two packing changes are added: F9 (one atlas for an Explore screen and lab steps) and F10 (a pool of
blobs shared by an atlas's points). F1–F5 and F7 stand as built. All of them touch `server/lfviz/`, `site/` or the
player, which every key covers, so they land in one step and every world is recorded again once.

| # | change | files | reason |
|---|---|---|---|
| F1 | **The screen's time scale.** An Explore screen or a lab step may declare `speed`: world seconds per played second, or `"world"` (the point's own default speed, from its `state` message, which the packed point keeps). Its atlas takes either `frame_dt` (world seconds) or `fps` (frames per played second at the world's default speed). «normal / slow» multiply the screen's speed by 1 and ¼; the time label states the world's time and the factor (details as built, below). | `registry`, `atlases_of`, `site/sitelib.py`, `site/atlas.py`, `atlas_live.py`, `player/js/{atlas,explore,lab,demo}.js` | §1.1: u34 0.05 s per orbit, u35 1 ns per photon, u37 2 µs per pair; u34's periods differ 15× |
| F2 | **Stop by counted events.** `stop: {events: {<kind or name>: n, …}, after_s?, max_world_s}`: the point stops `after_s` after the first kind that has occurred n times; `{event: k}` is the shorthand of `{events: {k: 1}}`. | `headless.run_spec`, `registry` | u34: turns, radial periods or the fall, whatever the period |
| F3 | **Compound controls.** `{id, label, unit?, values, labels?, sets: {<param>: [one value per grid value], …}}`: one slider or select sets several parameters (form as built, below). | `registry`, `screens_of`, `sitelib`, `site/atlas.py`, `atlas_live.py`, `explore.js`, `lab.js` | u37's Δ (a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ); u35's glass and side (n₀, n_s), its coatings and its analyser devices |
| F4 | **Counting instruments and the run's own errors.** `kind: "counter"` reads an integer measurable; `error: "poisson"` gives √N (1 for N = 0, said in the instrument's line) or a number (0: an exact count). A `readout` may declare `sigma: "<measurable>"`: its error is the run's own standard error at the cursor. | `registry`, `site/atlas.py`, `lab.js`, `worksheet.js` | u35's detectors, u37's coincidences (Dehlinger and Mitchell's √N), u37's E with the error of `tools.bell_stats` |
| F5 | **Formula columns.** `{id, label, expr}` over earlier columns (grammar, errors and refusals as built, below). A step may offer several formula columns of the same readings, and the student plots whichever (§1.4: the ways). | `server/lfviz/expr.py`, `player/js/expr.js`, `registry`, `lab.js`, the shared fixture | E from four counts, R from two, the Fresnel linearisations, Malus's cos², S from four E, Δφ from a shift |
| F6 | **Lab work is a bench: nothing hidden, nothing judged.** (a) Lab work's drawer is Explore's: every check with its computed value, reference, relative difference, tolerance and note; the events with their texts and times; «Physics of this world»; the passport. **[error in earlier]** The concealment this row first specified (verdicts only, events by kind) and EX1's D10 (the events' times left out in Lab work) are withdrawn. (b) A step may declare `overlays` and `readouts` exactly as an Explore screen does, the view's defaults otherwise; a view draws in Lab work what it draws in Explore. **[error in earlier]** The contract «draw nothing a step asks the student to find» is withdrawn. (c) **No verdict on the student's data.** «Check against the law» goes, with its ✓/✗, its bound of k errors or Student's t and its «no verdict» (EX1 D4). The fit is a tool: for the model the student chooses it prints the parameters with their σ from the declared errors, χ², the degrees of freedom, χ²/dof, the p-value of χ², and the Birge ratio √(χ²/dof); when χ²/dof > 1 it prints, on a second line, the σ scaled by that ratio, and the student decides which to report (**[error in earlier]** EX1's D3 scaled them silently); without declared errors it says that the σ come from the scatter. (d) A step's `laws` stay as data, optional: the world's computed values for the bench (`lab_reference`, unchanged), listed in the drawer under «Computed for this bench» with the quantity and the columns they belong to («slope of L against √h: 0.6774 m^(1/2); formula k = v₀·√(2/g)»), never set beside the student's fit; the registry no longer requires the step's plot to be one of its laws. (e) The table (one row per set-up, EX1 D5), its CSV, the plot and the fit stay as conveniences; the students record and hand in their own measurements. (f) «MODIFIED PHYSICS» in Lab work stays (as built). | `player/js/lab.js`, `fit.js` (output only; the algorithms unchanged), `demo.js howWeKnow`, `registry._check_lab`, `_check_laws`, `RULES.md` §10 | the owner, 2026-11-18 (§9): «это не проверочная работа, учащиеся не отвечают на вопросы и от них ничего не нужно скрывать … он уже сам проверяет и говорит у кого правильно получилось» |
| F7 | **Readouts with an error and a reference; the CSV of the shown point.** A measurable may declare `sigma`, `ref` and `ref_label`; «CSV of this point» at `standard` (as built, below). | `explore.js`, `registry`, `site/atlas.py` | V52 (m); the mechanism of V52 (n) |
| F8 | **The task sheet, the teacher's variants, and the packing details.** (a) `worksheet` becomes a task sheet: `basis` (as built: required at `standard`, `frp` at school), `goal: T`, `bench: [T]` (what the bench is and what can be set on it), `procedure: [T]` (one suggested procedure, not the only one), `record: [T]` (what to record and hand in), `record_rows` (blank rows per step, default 10), `variants`. **[error in earlier]** `questions` with their answers, `teacher` notes, `grading` and the «For the teacher» / «For the instructor» pages and switch are removed (EX1 §2.3 and this row's first form). The sheet prints the head (name, group, date), the basis with its quotations, the goal, the bench with its instruments (generated from the steps), the procedure, the record list, blank tables and plot frames, the attribution line on every page. (b) **The teacher changes the task**, on the static site too: `variants: [{id, label, grade?, steps?, values?: {<step>: {<control id>: value}}, text?: {goal?, procedure?, record?}}]` are tasks computed in the atlases (several glasses, several orbit families, several analyser settings); `&variant=<id>` on `run.html` (Lab work) and on `worksheet.html` preselects the controls (nothing is locked: the bench stays whole) and prints that variant's sheet with its id. `worksheet.html` makes the goal, the procedure, the record list and a free field «Task from the teacher» editable before printing (contenteditable, «Restore the original»; kept in `localStorage` per world and variant, a convenience); nothing is sent anywhere. (c) «Computed for this bench» can be printed on a page of its own (`&computed=1`): the same values the drawer shows, for the teacher's convenience. The teacher gets nothing else: the bench is open, and judging is the teacher's (§1.4). (d) `drop.blobs: ["<type>.<blob>", …]` (`*` at the end of a blob name) drops blobs of any message type; `anchors()` and `worldToPx` are required of a view only when a lab step uses a `ruler` or a `protractor` (both as built). | `registry` (`_check_worksheet`, `_check_variants`), `player/js/worksheet.js`, `worksheet.html`, `demo.js` and `lab.js` (`variant`), `headless.Packer`, `RULES.md` §7 (glossary: «task sheet» / «бланк задания»), §10 | the owner: «задачу преподаватель может изменить, замеры и записи студенты делают отдельно и сдают преподавателю» |
| F9 | **One atlas for an Explore screen and its lab steps.** A lab step may declare `atlas: "<Explore screen id>"`: its points are that screen's (preset, fixed values, controls, clock, stop, seed); the step adds its own instruments, columns, plot, laws and overlays. The shared atlas's spec covers the laws of every step that uses it (so its key does), and its manifest's `references` holds them as `<step>/<law>`. | `registry` (`atlases_of`: no atlas of its own for such a step; the screen must exist and have no law the step contradicts), `site/atlas.py` (the references), `lab.js` (opens the screen's manifest) | u35: the reflection bench is Explore «Boundary» (one atlas of 444 points, not two); u37: the CHSH bench is Explore (156 points) |
| F10 | **A pool of blobs shared by an atlas's points.** After every point of an atlas is computed, each packed blob (after quantisation) whose bytes occur in two or more points is stored once in `pool.<hash8>.lfpt.gz` (one message whose blobs are named by the first 16 hex digits of their sha256, in the order of first use) and replaced in the points by a descriptor `{pool: "<sha16>"}`; the manifest names the pool (`{file, bytes_gz, sha256}`) as it names the base; a reader fetches it once per atlas; a missing pool, or one of another size, makes the atlas `stale`. Live points are never pooled. `ATLAS_VERSION` 2 → 3. | `headless.Packer` (a second pass), `site/atlas.py` (keeps an atlas's packed messages in memory: u35's largest, 444 points, about 30 MB), `sitelib`, `protocol.decode`, `player/js/{api,atlas}.js`, `site/check.py`, `tests/test_atlas.py`, `test_protocol_quant.py` | u35's angle curves are the same for every θ and polarisation of a glass and side: *measured* 15–18 kB per point → 9.8–10.8 kB (−37 %); u35's world about 18 MB → 11.9 MB (§6) |

**As built in step F (2026-11-18), the contract's details** (from step F's notes; the code is the reference:
`server/lfviz/registry.py`, `headless.py`, `expr.py`, `site/atlas.py`, `player/js/{explore,lab,demo,worksheet,expr}.js`;
the toy worlds `tests/site_worlds/s98_atlas_toy` (school) and `u96_lab_toy` (university) use every feature):

- **[error in earlier] The files.** F1 and F3 also need `site/sitelib.py` (`atlas_spec_of`: the key covers `fps` and a
  compound control's `sets`; the playback `speed` is not in it, it changes no byte) and F1 `player/js/atlas.js` (a point
  keeps its first `state` message's speed as `pt.speed`); §8's row F did not list them.
- **F1.** The catalogue gives every Explore screen and lab step `frame_dt` and `fps` (one of them null) and `speed` (a
  number, `"world"` or null). With `fps`, a frame comes every `default_speed / fps` of world time and, with a `world_s`
  or event stop, the last one at the stop time; a stop inside an event's own frame step ends at that step (so `after_s`
  should exceed a frame). A screen without `speed` keeps EX1's time label; one with `speed` writes it as Watch does
  (**[error in earlier]**, not «×1/120»): «world 0.0123 s · slow motion ×120 · 3.10 s / 24.00 s», the world's time on a
  human scale (ns … s) or in the world's own unit when its header says `units.t_show: {unit: T, s: <world seconds per
  unit>}` (u34: GM/c³), the factor including «slow». The view's `ctx.speed()` is world seconds per played second. A lab
  step with a manual stopwatch declares no `speed` (the registry refuses it). A world whose default speed differs per
  point (u34) sets `self.default_speed` in its constructor.
- **F2.** `max_world_s` is required with `events`, as with `event`. **[error in earlier]** §2.3's first stops for u34's
  labs had none; the revised §2.3 has them. `n` is a whole number ≥ 1; an event counts once for each key its `kind` or
  `name` is.
- **F3.** The catalogue's and the manifest's form: `{param: <id>, id, compound: true, values, default, sets, labels?,
  label, unit, kind: slider | select, law}`. Its `id` is a slug that is no parameter of the schema; a parameter it sets
  is no other control, no fixed value and set by no other compound control; `law` is true when it sets a law parameter
  (refused at school). `lab_reference`'s `values` hold the compound id's values and each set parameter's list. A trace's
  label names the control's value («Δ 22.5°»); the passport adds the parameters it set. Off the grid the live endpoint
  answers 400: «“{label}” sets several parameters at once: it takes only its own values».
- **F4.** A counter's `division` is 1; its `error` is required: `"poisson"` or a number ≥ 0; it reads a measurable whose
  value in every frame is a whole number ≥ 0 or null (`site/atlas.py` fails the atlas otherwise). A readout with `sigma`
  declares no `error`. A counter prints «838 ± 29» («0 ± 1»; «11» exact), a readout with the run's σ «0.7071 ± 0.011»;
  the instrument line says «counts; error √N (a count of 0 has the error of one count)».
- **F5.** A column is exactly one of `from`, `of` + `op`, `expr`. A column's id may not be a name of the grammar or a
  property every JavaScript object has. An undefined cell carries its reason code (`expr.REASONS`: `sqrt_negative`,
  `division_by_zero`, `log_nonpositive`, `asin_domain`, `acos_domain`, `power`, `not_finite`, `missing`,
  `error_undefined`); an input with σ = 0 adds nothing. Python: `lfviz.expr.evaluate(text, {column: (v, σ)})` →
  `(value, sigma, t1, t2)`.
- **F6.** As built before the owner's answers, Lab work's drawer showed verdicts only and the events by kind; step F
  reverted that on 2026-11-18 (its notes): the drawer is Explore's, EX1's D10 is gone. The step card's «MODIFIED
  PHYSICS» band and the top bar's mark follow the shown point's header `modifications` and stay. «Check against the
  law» (EX1's code, untouched by step F) is removed by step F's second part, with the fit's output of row F6 (c).
- **F7.** A readout with `sigma` prints value and error to the error's two digits, the unit once, its reference to the
  same decimals; with `ref` alone both to 5 significant digits; a whole number without a unit, `sigma` or `ref` is a
  count; the reference's default label is «reference». «CSV of this point» (`ui: "standard"`): «t, s», then every
  declared measurable but those that serve as another's `sigma` (they are its «σ …» column), one row per frame up to
  the time shown.
- **F8.** `basis: [{text: T, source: <a string or a T>, quote?: <verbatim>, quote_lang?: "en"}]` is required at
  `standard` and `frp` refused there. **[error in earlier]** A variant's `grade` was required everywhere; it is required
  at school only. The grading and the instructor's switch that step F first built were removed on 2026-11-18 (step F's
  notes).
- **Open, not in step F's files:** Watch (`player/js/watch.js`) still writes the world's time with two decimals in
  seconds and a large factor as a whole number («world 0.00 s · slow motion ×1199040767» for u35 and u37);
  `explore.js` exports `worldTime` and `factorText`, which `watch.js rateText` should use (step I, before W35's and
  W37's Watch).

What does not change: quantisation, the live endpoint's limits, the budgets, the fit's algorithms (`fit.js` and
`linear_fit`, York for lines, the effective variance for the parabola, as after EX1's D3).

---


## 6. Atlases and budgets

Budgets as EX1 §1.8 (`sitelib.BUDGET`): a point 150 kB / 400 kB, an atlas 6 / 12 MB, a world 12 / 25 MB, the site 600 /
900 MB; at most 6 controls and 1 500 / 3 000 points per atlas at `standard`. Revised for the benches (§2.3, §3.4,
§4.3); every number is *measured* or an *estimate* from measured points (Appendix A.2, A.6).

| world | atlas | grid | points | per point | atlas | CPU |
|---|---|---|---|---|---|---|
| u34 | `explore` | r₀ 7 × speed 5 | 35 | 25–194 kB *measured* at fps 10; largest 168 kB at fps 8 | **2.8 MB** | ~7 s |
| u34 | `lab.periods` | r₀ 9 × speed 2 | 18 | 20 kB *measured* | 0.36 MB | 1 s |
| u34 | `lab.advance` | r₀ 13 | 13 | ~100 kB (196 kB *measured* at fps 4) | 1.3 MB | 5 s |
| u35 | `explore` = `lab.fresnel` (F9) | sample 6 × θ 37 × pol 2 | 444 | 9.8–10.8 kB *measured* with the pool emulated | **4.6 MB** | ~10 s |
| u35 | `coatings` | λ 13 × coating 5 | 65 | ~15 kB | 1.0 MB | ~4 s |
| u35 | `polarisation` | θ 10 × α 12 | 120 | ~10 kB | 1.2 MB | ~3 s |
| u35 | `lab.malus` | ψ 3 × α 19 × device 2 | 114 | ~10 kB | 1.1 MB | ~3 s |
| u35 | `lab.reflection` | glass 3 × θ 13 × α 7 | 273 | ~10 kB | 2.7 MB | ~15 s |
| u37 | `explore` = `lab.chsh`, `lab.local` (F9) | pair 2 × Δ 13 × τ 2 × law and source 3 | 156 | 16.9 kB *measured* | **2.7 MB** | ~6 s |
| u37 | `lab.correlation` | pair 2 × a 3 × b 25 | 150 | 9–10 kB *measured* | 1.35 MB | ~3 s |

| world | recordings (Watch and more) | atlases | **world** | target / limit |
|---|---|---|---|---|
| u34 | 0.32 + 0.51 MB | 4.5 MB | **5.3 MB** | 12 / 25 MB |
| u35 | 0.9 + 0.43 MB | 10.6 MB | **11.9 MB** | 12 / 25 MB |
| u37 | 0.64 + 0.13 MB | 4.05 MB | **4.8 MB** | 12 / 25 MB |

The site: 65.6 MB (*measured* 2026-11-17), of which the three worlds' present recordings are 1.1 MB; with these 22.0
MB and S03's rework (+0.1 MB, §10), about 87 MB. Every atlas is inside 1 500 points and 6 MB; u34's zoom-whirl point
(168 kB) is over the 150 kB target and accepted with its reason; u35 is at its world target, held there by the pool
(without it about 18 MB: 16 kB per point, still under the 25 MB limit). CPU per world under a minute.

**Stochastic points** (EX1 §1.6): u35 and u37 store one seeded sample per set-up (seed 1, shared by Explore and Lab work
where the atlas is shared) and the run's computed probabilities; «Another sample» on a server draws the next seed.
**[error in earlier]** The first version's seed 2 for Lab work served the concealment and is withdrawn.

---

## 7. Tests

**Framework (step F).** As built for F1–F5 and F7 (`test_headless.py`, `test_atlas.py` on the toy worlds
`s98_atlas_toy` and `u96_lab_toy`, `test_expr.py` and `expr.test.mjs` on the shared fixture, `lab.test.mjs`,
`test_site_registry.py`, `test_atlas_live.py`). Revised and new:
- F6: Lab work's drawer has the same content as Explore's for the same point (values, references, notes, events with
  their texts and times), in EN and RU; no «Check against the law» and no ✓/✗ about the student's data anywhere in Lab
  work; the fit prints its parameters with σ, χ², dof, χ²/dof, p, the Birge ratio and, when χ²/dof > 1, the scaled σ
  on its own line, against `linear_fit` on the shared fixtures (`fit.test.mjs`); «Computed for this bench» lists the
  manifest's references with their columns; «MODIFIED PHYSICS» in a modified step.
- F8: the registry refuses `questions`, `teacher` and `grading` and checks `goal`, `bench`, `procedure`, `record` (T),
  `variants[].values` (controls and values of the step's grid); `&variant=` preselects the controls on `run.html` and
  prints that variant on `worksheet.html`; the sheet's editable fields print as edited and «Restore the original»
  restores them; `&computed=1` prints the computed values; every page one A4 sheet with the attribution line.
- F9: a step with `atlas: <screen>` builds no atlas of its own, opens the screen's points and finds its references
  in the screen's manifest; the key covers the steps' laws.
- F10: an atlas with a pool rebuilds byte for byte; a point decoded with the pool equals the same point packed without
  it, in Python and in JS (`atlas.test.mjs`); a missing pool, or one of another size, makes the atlas `stale`
  (`site/check.py`); live points have no pool.

**Engine (step E35).** `lfphys/tests/test_polarization.py` (§3.5: Malus for ideal and real analysers, Brewster's
reflected state, the reflected degree of polarisation, TIR's phase difference against its closed form and 30-digit
Fresnel coefficients, energy, Jones against Mueller, passivity); `test_interfaces.py` extended (the p field profile:
the Joule balance for p, the continuity of the tangential fields); `test_layers.py` (the new module's `ABOUT` and its
translations).

**The worlds.** Each world's `tests/test_<world>_screens.py`:
- every grid point of every atlas builds with all checks ✓ and stops by its own rule;
- every computed value of a bench against an independent computation (u34: the exponent and the clock law against
  a fit of the world's own turns, 6π against `ppn.periapsis_advance`/(M/p) in the limit, the next order against a fit
  of `orbits.periapsis_advance` at small M/p; u35: the linearisations against the engine's R at 1 000 random (n, θ) to
  1e-12 and against 30-digit Fresnel formulae, Malus's and the reflected polarisation's values against
  `core.optics.polarization`; u37: E from four counts against `bell_stats.correlation`, S(Δ) against `Law.E`, the
  visibility's S against V·S);
- **every way of the bench against the atlas**: the readings of the built atlas, processed as the way says and fitted
  by `linear_fit`, reproduce the way's outcome (u34's are deterministic and equal §2.3's; u35's and u37's come from one
  seeded sample, so W35 and W37 write the sample's values into §3.4 and §4.3 and the test checks those, and that they
  lie within the simulated spread of Appendix A.3, A.5);
- the Watch captions' numbers against the recording and every caption no later than its event (u35's analyser rows
  measured anew).

**Browser** (EN and RU; 1280 × 800, 390 × 844 and 390 × 700; a private server, never 8479; the recordings and atlases
built by the code under test): `demo_screens.mjs` for u34, u35, u37 and S03 (Watch; Explore; Lab work: the drawer as
Explore's, the overlays, at least one right and one wrong way of each bench carried out through the table, the plot and
the fit, the fit's output without a verdict, a variant from the address, the task sheet printed in EN and RU, edited
and restored); each world's `<world>_screens.mjs` from its view's `canvas.__layout` (captions clear of what they
describe; at 390 px the view, the step's control and «Measure» on screen together; no horizontal scroll; no text out of
its box; five tabs of u35 fit the phone's tab bar); `site_smoke.mjs`, `start_page.mjs`, `i18n_checks.mjs`.

**Site.** `site/check.py` on the new atlases and pools; `site/build.py`; CI's matrix unchanged.

---

## 8. Implementation plan

Batch **EX2** (`lfphys/PLAN.md` P17.5, continued). Every agent works in Docker (`--memory` ≤ 8g, `LFPHYS_NO_GPU=1`,
containers named `lf-ex2-<step>-*`), on its own private port (never 8479), stops containers by name (never `pkill -f`
or `pgrep -f`), puts no e-mail address or personal identifier in an external request, and keeps its notes in the
scratchpad. The contract between F and the worlds is §5; a change to it is made here first.

| step | agent | owns (only these files) | done when |
|---|---|---|---|
| **F** framework (in progress; finishes F6 (c)–(d), F8, F9, F10) | 1 | `server/lfviz/{registry,headless,expr,atlas_live,protocol}.py`, `site/{atlas,check,sitelib}.py`, `player/js/{explore,lab,fit,demo,worksheet,atlas,api,expr}.js`, `player/worksheet.html`, `player/assets/demo.css`, the framework's tests, `tests/site_worlds/**`, `player/js/tests/**`, `tests/browser/demo_screens.mjs` (the toys), the framework's msgids | the suites pass; the toys' screens work in EN and RU at 1280 and 390 px; `test_recorder.py` unchanged and passing |
| **E35** engine (in parallel with F) | 2 | `lfphys/lfphys/core/optics/polarization.py` (new), `lfphys/lfphys/core/optics/interfaces.py` (the p field profile, the power factors), `lfphys/tests/test_polarization.py`, `test_interfaces.py`, `lfphys/locales/*`, `lfphys/README.md` catalogue rows | the engine's suite passes; `ABOUT` and translations complete |
| **W34**, **W35** (after E35), **W37**, **WS03** (in parallel, after F) | 4 | each only its own world folder: `visualizations/u34_orbits/**`, `u35_optics_bench/**`, `u37_bell_test/**`, `s03_projectile/**` (`viz.py`, `engine/`, `web/view.js`, `locales/`, `README.md`, `README.ru.md`, `tests/`) | the world's tests and browser checks; its atlases and recordings built with every check ✓ and within budget; the measured sizes and the stochastic ways' numbers written into this design |
| **I** integration (last) | the lead | `visualizations/RULES.md` (§7 glossary: «task sheet» / «бланк задания»; §10: the bench, F6, F8–F10), `STATUS.md` (V52 (l), (m), (n); a new V53 for EX2 with the audit's open items, §11), `lfphys/PLAN.md`, this design (notes after the implementation), the READMEs and their catalogue, `docs/images/`, `tests/browser/{site_smoke,start_page,i18n_checks}.mjs`, `player/js/watch.js` (§5's open item) | the full suites green; the site built and checked locally; the browser checks in EN and RU |

Then four independent reviews, each by an agent that wrote none of the part (`AGENTS.md` rule 6):

| review | scope |
|---|---|
| R2-E | the physics: `core.optics.polarization` and the p field profile (a new core module: rule 5), u34's GR numbers, u35's linearisations and counting, u37's statistics, CHSH and the visibility; every way's outcome reproduced on the built atlases |
| R2-F | the framework F1–F10: keys, determinism and the pool, the formula parser's safety and parity, compound controls on the live endpoint, the stop rules, the task sheet and the variants on the static site |
| R2-P | the screens in a browser, EN and RU, 1280 and 390 px: Lab work as a bench (nothing hidden, no verdict), captions against the layout, the phone layout (u35's five tabs), the CSV, the editable sheet |
| R2-W | the four worlds (S03 included) as a teacher and a student would use them: the benches' ways, the captions true to the screen, the task sheets, the sources and their quotations |

Each review is processed finding by finding in its `RESPONSE_*.md` by agents other than its author, then integrated.
The report to the owner (in Russian) gives the status per item, the measured sizes and the links on the local server;
the site is deployed only on the owner's go.

---

## 9. Decisions of the owner, and what the owner still decides

**The owner's answers of 2026-11-18** (verbatim), now decisions of this design:

1. On Lab work: «лабораторные работы - это аналог плейграундов, только по очень узному направлению, что-то вроде
   стенда для проведения эксперимента, который можно проводить разными путями, часть из которых приведут к правильным
   результатам, часть к неправильным. это не проверочная работе, учащиеся не отвечают на вопросы и от них ничего не
   нужно скрывать. например если нужно собрать электрическую цепь и измерить напряжение в определенных точках, то они
   просто ее собирают и измеряют. задачу преподаватель может изменить, замеры и записи студенты делают отдельно и сдают
   преподавателю, а он уже сам проверяет и говорит у кого правильно получилось, у кого неправильно.» → §1.4, §2.3,
   §3.4, §4.3, §5 F6 and F8, §10. **[error in earlier]** The first version's question 1 (hide the checks' values in Lab
   work) and its concealment, questions, answers, grading and verdicts.
2. On Malus's law: «если закон Малюса нужен для u35, то нужно добавлять, мы делаем достоверные и точные симуляции. это
   суть движка и всего проекта. это не анимация и не упрощения, все должно строго считаться и соответствовать
   известным законам физики» → §3.5, and the audit of §11. **[error in earlier]** The first version's question 2
   recommended leaving Malus's law out of EX2.

**What the owner still decides** (the design takes the recommended answer until then):

1. **Real detectors in u37** (STATUS V18). With detection efficiency below 1 the CHSH test needs the fair-sampling
   assumption, and a strict test needs the CH or Eberhard inequality: a physics extension of the world and its checks,
   not a screen. Recommended: a batch of its own after EX2 (the engine's `bell_stats` gains CH/Eberhard, the world
   gains efficiency and losses as device properties); EX2 states «ideal detectors» on the bench, and adds the source's
   visibility (§11, item 14), which needs no new inequality. The alternative: W37 does both now (about a day more and
   an R2-E item).
2. **Real, dispersive materials in u35** (STATUS V16). Constant indices are exact media for Maxwell's equations, but no
   real material has one over 400–700 nm. Recommended: in EX2 the coatings and glasses are named as constant-index
   media (§11, item 3); real materials (Sellmeier and tabulated data, each checked against its source) as an engine
   item after EX2. The alternative: E35 adds them now for the coatings screen.

**Risks, decided here:**
- *u34's benches are computational*: they follow a textbook's exercises and an astronomy laboratory; the task sheet
  says so.
- *The linearisations of Fresnel's formulae* are derived here; E35 and W35 test them to 1e-12; R2-E reviews them.
- *Ways that fail by design* are the bench's point; each is tested against the atlas, so a way that stopped failing
  (or started) is a failed test.
- *u35 at its world budget*: held by the pool (F10); without it about 18 MB, under the 25 MB limit.
- *u35's five tabs on a phone*: R2-P checks the tab bar at 390 px; the fallback is a select for the Explore screens.
- *The formula parser and the pool* are new framework code: shared fixtures, hostile inputs, byte-identical rebuilds,
  R2-F.
- *The CLEA manual* was checked in a third-party copy (Appendix B).
- *Determinism* holds on the same CPU type only (EX1, review R-F F8).

---

## 10. S03: the same concept at school (WS03)

S03's Lab work (EX1 §5.3) becomes a bench as in §1.4, kept simpler for school. Owner of the step: **WS03**, an agent
of its own, in parallel with W34, W35 and W37 after F, owning only `visualizations/s03_projectile/**`.

| today (EX1, after its reviews) | after WS03 |
|---|---|
| the drawer of Lab work: verdicts and events without times (EX1 D10); the events carry no measured value (QW's change for D10) | Explore's drawer (F6); the events carry their values again («landing: range 0.5244 m, flight time 0.3499 s»); **[error in earlier]** EX1 D10 withdrawn |
| the chute's speed «not told to the student» | shown with the set-up (1.5 m/s); finding it from the slope stays the task |
| «Check against the law» with its ✓/✗ | removed; the fit prints the parameters with their errors (no χ² at school) |
| the worksheet's questions, answers, teacher's notes, «For the teacher» | a task sheet: goal, bench, instruments, procedure, record (EN, RU); the grade-7 variant stays as a variant (part 1, L against h, no fit) |
| part 1: no air (EX1 D2) | an air toggle: in air the range is 0.09–0.54 mm shorter, from 0.95 m on more than the tape's ±0.5 mm (EX1, measured): the bench can see the air if the student looks |
| part 2: vacuum only | an air toggle: with air on, the slope of L against sin 2θ misses v₀²/g by 27 errors at the tape's resolution (EX1 step S, measured): a wrong way («a law of vacuum applied in air») |
| part 3: θ 25–60° | θ 20–70° by 5°: a parabola over 20–70° is biased by 1.8σ, over 25–60° by 0.8σ (EX1 step S, measured): a wrong way («a parabola fitted too far from the top») |

The school's ways (simpler, named in the procedure's hints): part 1 — L against √h (right), L against h (a curve: the
hypothesis «higher → farther» holds but not linearly), the hand stopwatch (±0.1 s on flights of 0.20–0.45 s) against T
from the tape, air on or off (0.09–0.54 mm, the tape's ±0.5 mm); part 2 — L against sin 2θ in vacuum (right), with air
(wrong), the angle of the largest range by eye on 5° steps; part 3 — the parabola near the top (right), over the whole
range (biased). Sizes: part 1 + 17 points (~39 kB), part 2 + 13 points (~46 kB), part 3 + 3 points (~33 kB); S03's
world 6.11 → about 6.2 MB. Tests: `test_s03_physics.py` (each way against the atlas, as §7), `s03_screens.mjs` and
`demo_screens.mjs` (the bench in EN and RU at 1280 and 390 px).

---

## 11. The audit: simplifications, omissions and their fixes

In the spirit of the owner's answer 2, every place where the design or the worlds as the screens use them simplify,
with its fix in EX2, its justification (why it is not a simplification of a law), or its record for later. Status:
**fix** (in EX2, by the named step), **justified**, **record** (STATUS V53), **owner** (§9).

| # | where | what | status |
|---|---|---|---|
| 1 | u35 | an unpolarised photon was drawn as s or p: one decomposition of ρ = I/2, not a measured property; the first Watch caption at 17 s relied on it | **fix** (W35): the density matrix throughout, unpolarised photons grey, Brewster's polarisation shown with the analyser (§3.1, §3.5) |
| 2 | u35 | the field \|E\|² is computed for s light only (V16) | **fix** (E35): `field_profile` for p and for any Jones state |
| 3 | u35 | constant indices named «like MgF₂, TiO₂/SiO₂, gold» (V16) | **fix** of the names (W35, §3.3): constant-index media said so; real dispersive materials: **owner** (§9, 2) |
| 4 | u35 | ideal detectors (efficiency 1, no dark counts) | **justified**: a stated ideal device, as the analyser's default; nothing on the benches depends on a detector's noise except at zero counts, where the counting floor is stated; real detectors **record** |
| 5 | u35 | the time inside the structure is neglected | **justified**: ≤ 15 fs in a 2 µm film against 1 ns on an arm (1.5·10⁻⁵), below every time shown |
| 6 | u35 | the beams are drawn by Snell's law with the real part of the index in absorbing layers | **justified**: drawing only; R, T, A and the field come from the complex transfer matrices |
| 7 | u35 | plane monochromatic waves: no beam width (no Goos–Hänchen shift), no bandwidth | **justified** as the model the Fresnel and Malus labs assume; stated on the bench; finite beams **record** |
| 8 | u35 | the analyser as an ideal or a two-number device (k₁, k₂) | **justified**: the principal transmittances define a linear partial polariser exactly; angle-of-incidence dependence of a real device **record** |
| 9 | u34 | the body is a test body: no radiation reaction, no self-force | **justified**: the limit m/M → 0, stated («a small body»); the advance at first order does not depend on m |
| 10 | u34 | Newton's ghost by `integrate_body` in coordinate time: an energy error up to 10⁻⁵ near deep periapses (V19 e) | **fix** (W34): the regularised integrator the engine has (10⁻⁹), with the Newton checks re-derived |
| 11 | u34 | the computation stops 2·10⁻⁶ M above the horizon | **justified**: the distant observer's time diverges there; the body's proper time to that point is checked |
| 12 | u34 | equatorial orbits of a non-rotating hole; Kerr only as radii (V19 d) | **justified** as the world's model (Schwarzschild is exact for it); Kerr orbits **record** (V19 d) |
| 13 | u34 | a star's radius checked only against 2M, not Buchdahl's 9M/4 (V19 b) | not used by EX2 (black holes only); **record** (V19 b) |
| 14 | u37 | the source is ideal (visibility 1) | **fix** (W37): the visibility V as a source property, the Born rule on the mixed state (§4.6) |
| 15 | u37 | ideal detectors: no losses, no dark counts, no detection loophole (V18) | **owner** (§9, 1) |
| 16 | u37 | pseudo-random setting choices | **justified**: statistically equivalent for the run's counts; stated |
| 17 | u37 | one local model of the class bounded by \|S\| ≤ 2 | **justified**: the bound is a theorem (the task sheet says so); the bench shows one model, named; the optimal local model **record** (V18) |
| 18 | u37 | one line, a symmetric source, an instantaneous measurement | **justified**: a chosen geometry, stated; the measurement's duration enters the locality condition through τ |
| 19 | framework | a count of 0 carries the error of one count | **justified** as a stated convention (F4); a Poisson-likelihood fit for counts near zero **record** |
| 20 | framework | the parabola is fitted by the effective variance (V52 (v)) | **justified** for EX2's benches, whose x are exact set-ups (then it is weighted least squares exactly); S03's protractor (±0.5°) keeps V52 (v) open |
| 21 | design | the first version's «unknown glass», concealed checks and seed 2 | **fix** (§1.4, §5 F6): withdrawn |
| 22 | design | the grids' steps (θ, Δ, r₀) | **justified**: the bench's set-up marks; the curves are computed at full resolution with their exact θ_B, θ_c and optima |
| 23 | framework | drawn arrays quantised | **justified**: below the display, the loss measured and stated (EX1) |
| 24 | design | the stories' slow motion and photon rates | **justified**: playback, stated by the time label |
| 25 | S03 | the air's drag by a constant C_d, the history force not computed (V52 (u)) | **justified** as a stated school model with the measured drag curve computed beside it (EX1 D1); the history force **record** (V52 (u)) |

Fixed in EX2: items 1, 2, 3 (the names), 10, 14 and 21; for the owner: 3 (real materials) and 15; the others justified
or recorded in STATUS V53 by step I.

---

## Appendix A. Measurements made for this design (2026-11-18)

Docker image `lfphys-viz`, CPU (`LFPHYS_NO_GPU=1`), `--memory` 2–4 GB, containers `lf-x2d-*`, the repository mounted
read-only at HEAD 545939a. The scripts are kept outside the repository, in the integrator's notes: `measure.py` (one
point: `headless.run_spec` with the screen's preset, fixed values, clock and stop, packed by `headless.Packer` with
the screen's quantisation and a header delta against the first point, gzip -9, as `site/atlas.py` does), `story.py`
(a recording through `run_spec` with `fps`, `speed`, the script and the captions, as `site/record.py` does; events and
probed frames with their played times), `u34_survey.py` (the world's own segment data over a grid), the lab
simulations (`u35_labsim.py`, `u35_labsim2.py`, `u34_labsim1.py`, `misc_sim.py`).

**A.1 u34 grid** (the world's segment data, speed × circular, r₀ in M; radial period in GM/c³): from 6 to 12 M the
speeds escape from 1.2 on at 6 and 7 M, from 1.25 at 8 M and at 1.3 at 10 and 12 M, and the bound speeds just below
are nearly parabolic (8 M at 1.2: apoapsis 141 M; 10 M at 1.25: 331 M; 12 M at 1.25: 148 M); 6 M at 1.15: apoapsis
485 M, period 24 590; plunges at 7 and 8 M below speed 1, at 10 and 12 M at 0.9; advance per radial period 33.0° (30 M,
1.1), 52.2° (20 M, 1.1), 120.4° (10 M, 1.1), 255.7° (7 M, 1.05), 438.5° (10 M, 0.95). Weak field at speed 1.1: 300 M
3.006°, 1 000 M 0.895°, 3 000 M 0.298° per orbit; ε 0.2103–0.2129.

**A.2 Points** (size gzip, CPU, frames):

| world | point | size | CPU | frames | checks |
|---|---|---|---|---|---|
| u34 Explore (fps 10, three radial periods, the ghost, trails u16) | 20 M, 1.1 / 30 M, 1.1 / 7 M, 1.05 / 10 M, 0.95 / 7 M, 1.0 / 15 M, 1.0 / 7 M, 0.9 | 119 / 115 / 158 / 194 / 64 / 69 / 25 kB | 0.21 / 0.21 / 0.24 / 0.28 / 0.10 / 0.09 / 0.04 s | 274 / 262 / 390 / 507 / 242 / 242 / 59 | all ✓ (one row without a reference) |
| u34 Explore (fps 15; fps 8; four radial periods) | 20 M, 1.1 | 210; 135 kB | 0.28; 0.24 s | 546; 292 | ✓ |
| u34 Lab, circles (fps 4, four turns) | 7, 20, 100 M | 21, 20, 20 kB | 0.05 s | 130 | 6 ✓ |
| u34 Lab, advance (fps 4, the ghost) | 300 M and 3 000 M, one orbit / ten orbits | 24, 24 / 197, 196 kB | 0.10 / 0.36 s | 34 / 324 | ✓ |
| u35 «Boundary», 2 000 photons (curves f8; u16) | air → glass 56° unpol. / glass → air 40° s / 60° unpol. / air → water 0° p | 52 / 44 / 46 / 44 kB; 34 / 30 / 32 / 31 kB | 0.02–0.04 s (0.35 the first) | 21 | 5–9 ✓ |
| u35 «Boundary», 20 000 photons (curves f8) | the same | 57–65 kB | 0.02–0.03 s | 21 | ✓ |
| u35 «Coatings» (angle curves dropped, spectrum u16) | λ/4 at 550 and 400 nm / Bragg ×8 / bare | 29 / 29 / 29 / 25 kB | 0.04–0.2 s | 21 | 4–5 ✓ |
| u35 Lab (20 000 photons, curves dropped) | four set-ups | 29–31 kB (clicks 22–24 kB) | 0.02–0.03 s | 21 | ✓ |
| u37 Explore (4 000 pairs, random) | Δ 22.5°, 0°, 45°, 67.5° × quantum, local | 28.5, 18.0, 28.5, 28.6 / 30.3, 22.2, 30.3, 30.3 kB | 0.02–0.04 s | 21 | ✓ |
| u37 Lab, correlation (1 000 pairs, fixed) | (0°, 0°), (0°, 30°), (45°, 90°) | 8.9, 9.6, 9.9 kB | 0.02 s | 11 | ✓ |

**A.3 Lab simulations** (the engine's values; Poisson counts or the instruments' rounding; `linear_fit`):

| lab | set-up | result |
|---|---|---|
| u35 s, linearised | 0–80° by 10°, 20 000 photons, 600 samples | intercept 2.2944 ± 0.0183 (n² 2.2952), slope −1.0002 ± 0.0298; coverage 96.8 / 96.2 %; χ²/dof 0.96 (5 000 photons: ± 0.037; 50 000: ± 0.012) |
| u35 p, linearised | 0–50° by 5°, 20 000 photons | intercept 0.4353 ± 0.0030 (1/n² 0.43569), slope −0.1888 ± 0.0089 (−0.18982); coverage 96.7 / 96.0 %; χ²/dof 1.02 |
| u35 parabola near θ_B (rejected) | 50–63° by 1° / 52–61° / 46–66° by 2°; 2·10⁴–4·10⁵ photons | vertex 56.17–56.19° / 56.36–56.38° / 55.57–55.60° against 56.573°: −3.7σ to −33σ |
| u34 circles | 9 radii, clocks to 0.1 GM/c³ | T: exponent 1.500014 ± 0.000022, A 6.2828 ± 0.0006; τ: exponent 1.535, χ²/dof 71 000; (τ/T)²: 0.999988 ± 0.000034, −2.9990 ± 0.0022 |
| u34 advance, one orbit, 0.1° | 300–3 000 M | line0 19.04 ± 0.24 (6π 18.850), z 0.76; χ²/dof 0.18 |
| u34 advance, ten orbits, 0.01° | 300–3 000 M | line0 18.947 ± 0.023, χ²/dof 14.9, Birge 3.86; Δφ·p/M: 18.846 ± 0.012 (z −0.31), slope 89.2 ± 9.5 (85.03, z 0.43); χ²/dof 0.22 |
| u37 correlation | a {0, 45}° × b 7, 1 000 pairs, 300 samples | quantum 1.0001 ± 0.0017 (scatter 0.0003); local 0.5008 ± 0.0114, coverage 94.7 % |
| u37 CHSH | Δ 7.5–82.5°, 4 000 pairs | quantum 0.9996 ± 0.0057 (96 %), S(22.5°) 2.83 ± 0.045 (18.6σ above 2); local 0.5003 ± 0.0085, S(22.5°) 1.417 ± 0.059 (9.9σ below 2) |

**A.4 Recordings**: §2.1, §3.1, §4.1 (sizes, CPU, events and probed frames at their played times).

**A.5 The ways** (2026-11-18, revised design; the engine's values, the instruments' rounding or Poisson counts,
`linear_fit`):

| bench | way | result |
|---|---|---|
| u34 periods | eccentric orbits (speed 1.1), T_r against a, power law, readings to 0.1 GM/c³ and 1 M | exponent 1.423 ± 0.013, χ²/dof 5.6; from 30 M on 1.456 ± 0.014, χ²/dof 2.3 |
| u34 advance | 0.1°, one orbit, r₀ 20–3 000 M, line through 0 | 20.00 ± 0.27, χ²/dof 16.6 (z 4.2 from 6π); r₀ 20–200 M: 20.07 ± 0.42, χ²/dof 36 |
| u34 advance | 0.01°, ten orbits, Δφ·p/M against M/p from 20 M | 18.839 ± 0.008 (z −1.36), slope 94.1 ± 3.7 (z 2.5 from 85.03), χ²/dof 0.45 |
| u34 advance | 0.1°, three orbits, r₀ ≥ 300 M, line through 0 | 19.00 ± 0.08 (z 1.8) |
| u35 Fresnel | p light on the bench's grid up to 52° | 1/n²: 0.4356 ± 0.0033, slope −0.1896, χ²/dof 0.99 (400 samples) |
| u35 Fresnel | p light through 62° with +√R | 0.497 ± 0.019 (n = 1.418), slope −0.351, χ²/dof 59 |
| u35 Fresnel | p light up to 52°, 4 000 photons | 0.4354 ± 0.0075 |
| u35 counts near θ_B | glass A, B, C; 20 000 and 100 000 photons | expected p counts at 1° steps: A 0.7 (56°), 0.4 (57°), 5 (55°, 58°); B 0.3 (58°), 1.4 (59°); C 0.2 (60°), 2.1 (61°) at 20 000 |
| u35 Malus | ψ 30°, α 0–180° by 10°, 20 000 photons, 300 samples (closed form) | ideal: slope 1.00000 ± 0.00005, χ²/dof 1.0; k₁ 0.90, k₂ 0.009 with a line through 0: 0.9026 ± 0.0010, χ²/dof 17.9 |
| u35 unpolarised reflectance | n 1.515, 0–89° | rises monotonically from 4.19 % to 7.72 % at θ_B and on |

**A.6 Bench points** (2026-11-18, the working tree with step F in progress; the packing as in A.2):

| world | point | size | CPU | frames |
|---|---|---|---|---|
| u35 bench, 20 000 photons, the curves, z and the field u16, clicks `t` only | A from air 30° s / 56° unpolarised / A inside 40° p / C from air 60° p / A inside 50° s (TIR) | 16.1 / 18.4 / 15.2 / 16.1 / 15.6 kB | 0.02–0.04 s | 6 |
| the same, the curves in a pool (emulated: left out) | the same | 9.8 / 10.4 / 10.3 / 9.8 / 10.8 kB | | 6 |
| the same with eleven frames (z f8) | the same | 22.3–25.8 kB; pooled 16.9–18.0 kB | | 11 |
| u37 spins, 4 000 pairs, random | Δ 45° and 22.5° × τ 100 ns and 5 µs | 29.0–29.3 kB | 0.06–0.07 s | 21 |
| u37 photons | Δ 22.5°, τ 5 µs / τ 100 ns with ten frames | 27.7 / 16.9 kB | 0.03–0.04 s | 21 / 11 |

## Appendix B. Sources checked for this design

Each file was downloaded into its own scratch folder (no e-mail or personal identifier in the requests), converted
with `pdftotext`, and every quotation above was found verbatim in the text (line breaks and the PDF's line numbers
removed).

| source | file | sha256 (first 16) | quotations |
|---|---|---|---|
| E. F. Taylor, J. A. Wheeler, E. Bertschinger, *Exploring Black Holes*, 2nd ed., ch. 10 «Advance of Mercury's Perihelion» (draft 2020-03-31) | `eftaylor.com/exploringblackholes/Ch10AdvanceOfMercurysPerihelion200331v1.pdf` | 73d57c95076952c7 | §10.6 (two sentences), eq. (23), Query 11 |
| CLEA, «The Revolution of the Moons of Jupiter», Student Manual v1.1.1, Gettysburg College | a third-party copy, `old.gml.cz/prof/benes/JupMoons/Jupit_sm.pdf` (the official file not found) | 6a9a7c8658442cfa | two sentences |
| Carnegie Mellon University, 33-353 «Intermediate Optics», Lab 1 «FRESNEL RELATIONS and SNELL’S LAW» (Fall 2010) | `cmu.edu/biolphys/smsl/teaching/IntermedOptics/IntOptics_data/lab manuals/Lab1 - Fresnel.pdf` | 2db1054b3a6b5856 | four sentences |
| Rutgers, «Fresnel Equations and Electromagnetic Boundary Conditions» | `physics.rutgers.edu/~eandrei/389/fresnel.pdf` | 7458ae60bf892c07 | one sentence |
| D. Dehlinger, M. W. Mitchell, Am. J. Phys. 70, 903 (2002) | `arxiv.org/pdf/quant-ph/0205171` | 205531334f0d5625 | three sentences; S = 2.307 ± 0.035 |
| University of Toronto, PHY293/PHY294 lab course, «Polarization of light» | `physics.utoronto.ca/~phy293lab/experiments/polarization.pdf` | 6596b875c4af22c5 | six sentences (§3.4) |
