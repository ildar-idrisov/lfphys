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

1. **All three worlds get all three screens.** u34: Watch (a rosette, Newton's closed ellipse beside it, the clock,
   a plunge), Explore (r₀ × speed, 35 points), Lab work (Kepler's third law and the clock; the periapsis advance in
   two parts). u35: Watch **[error in earlier: EX1 §7 said «no»]**, Explore «Boundary» (media × θ × polarisation,
   138 points) and Explore «Coatings» (λ × coating, 65 points), Lab work (Fresnel's formulae: the index of a glass
   from R_s and from R_p, and Brewster's angle). u37: Watch (pairs, S passes 2, then a local model), Explore (the CHSH
   angle Δ × the law, 26 points), Lab work (Dehlinger and Mitchell's E(α, β), the CHSH test, and the same test in a
   world of local hidden variables, flagged).
2. **The time scale of a screen is the world's own.** EX1 played world seconds as wall seconds; u34's orbit lasts
   0.05 s, u35's photon 1 ns and u37's pair 2 µs. A screen gets a playback `speed` (world seconds per played second, or
   `"world"`: the point's own default speed) and its atlas may take frames per played second (`fps`) instead of
   `frame_dt` (§5 F1). The time label states the world's time and the factor, as Watch does (EX1 D8).
3. **Stop rules count events** (`events: {kind: n}`), so an orbit stops after three radial periods, three turns or
   its fall, whatever its period (§5 F2).
4. **A control may set several parameters** (a compound control): u37's Δ sets a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ; u35's
   «media» sets n₀ and n_s (§5 F3).
5. **Lab work counts.** A `counter` instrument reads a count with its Poisson error, a `readout` may carry the run's
   own standard error, and a column may be a formula of earlier columns with the errors propagated (§5 F4, F5). This
   replaces any new special operation: E = (N₊₊ + N₋₋ − N₊₋ − N₋₊)/N, R = N_R/(N_R + N_T), the Fresnel linearisations
   and S = E₁ − E₂ + E₃ + E₄ are formulas.
6. **Lab work does not give the answer away.** In Lab work the drawer shows each check's label and verdict, not its
   values, references or notes, and the events by kind without their texts (EX1 D10, extended); each world's view
   draws, with `ctx.screen = "lab"`, no curve or expectation that a step asks the student to find (§5 F6).
7. **Model choice is physics, and it is flagged.** u34: GR against Newton's ghost, and the leading order of GR against
   the next; u37: quantum mechanics against a local model in its own world, marked «MODIFIED PHYSICS» in Lab work too.
8. **Every lab is founded on a real course or manual**, quoted verbatim: Taylor, Wheeler & Bertschinger, *Exploring
   Black Holes*, ch. 10 (u34, the advance); the CLEA lab «The Revolution of the Moons of Jupiter» (u34, Kepler's third
   law); the Carnegie Mellon 33-353 «Intermediate Optics» Lab 1 and the Rutgers handout «Fresnel Equations and
   Electromagnetic Boundary Conditions» (u35); Dehlinger & Mitchell, Am. J. Phys. 70, 903 (2002) (u37).
9. **Every verdict was simulated before it was designed.** The grids, the instruments' divisions and the number of
   photons or pairs were chosen so that the law agrees within the declared errors in about 95 % of samples, and so
   that where a law must fail (u34's leading order at high precision) it fails for the stated reason (Appendix A.3).
   One candidate was rejected on that evidence: a parabola through R_p(θ) near Brewster's angle is biased by
   −0.2° to −1.0° (3.7 to 33 standard errors) because R_p is not symmetric about θ_B.
10. **Malus's law is not a u35 lab**: u35 has no analyser; adding one is a new optical element of the world, not a
    screen (question 2 in §9).
11. **Sizes** (*estimate* from measured points): u34 4.4 MB, u35 7.6 MB, u37 2.3 MB (the targets are 12 MB per
    world); the largest point 168 kB (u34's zoom-whirl, over the 150 kB target, accepted with its reason). The site
    grows by about 13 MB, from 65.6 MB to about 79 MB.
12. **Framework changes**: eight, all in one step before the worlds (§5), because each changes every recording's key.
    They close STATUS V52 (l), (m) and the first half of (n).
13. **Plan**: step F (framework), then W34, W35, W37 in parallel, then I (integration); four independent reviews (R2-E
    physics, R2-F framework, R2-P screens, R2-W worlds), processed by other agents (§8).

---

## 1. What is common to the three worlds

### 1.1 Time on a screen

| world | one event of interest lasts (world time) | playback (world s per played s) | atlas clock |
|---|---|---|---|
| u34 | a radial period: 116 GM/c³ (circle at 7 M) to 1 705 GM/c³ (r₀ 30 M, speed 1.1); 5.7 ms–84 ms for 10 M☉ | `"world"`: the point's own default speed, a Kepler period in 8 played s | `fps: 8` |
| u35 | a photon's flight: 2 ns; 2 000 photons at 4·10⁹ s⁻¹: 0.5 µs | build-up in 10 played s: 5·10⁻⁸ | `frame_dt` = the stop time / 20 |
| u37 | a pair's flight: 1.67 µs (L = 500 m); 4 000 pairs at 10⁶ s⁻¹: 4 ms | build-up in 10 played s: 4·10⁻⁴ | `frame_dt` = the stop time / 20 |

So u34 needs both the per-point speed and the frames per played second (§5 F1): with a fixed `frame_dt` its points
differ 15× in frames and size, and a fixed window that holds three radial periods of the slowest orbit holds 44 turns
of the circle at 7 M (from the world's own periods, Appendix A.1; *measured* at fps 15: a point grows with its frames,
0.38–0.43 kB per frame).
The «normal / slow» buttons stay: «slow» is a quarter of the screen's speed.

### 1.2 What a university screen shows, and what folds away

As EX1 §3.3 for `ui: "standard"`: the screen keeps the phenomenon, 2–3 controls, the overlays, the readouts and the
time bar; the world's own panels (`rightPanels`) fold into «How we know this is right», as u32's did (EX1 §6.3); the
quick set-up bar, the left form of live parameters, the actions and the toolbars are hidden in Watch, Explore and Lab
work and stay unchanged in «▶ Compute live». The per-world tables are §2.5, §3.5 and §4.5.

### 1.3 The views

Each of the three views gains what EX1 §2.4 lists and u32 has: `ctx.screen` (hide the quick bar, the toolbars and the
actions outside `live` and `recording`), `OVERLAYS`, `QUANT_SAFE`, `setOverlay`, tolerance of dropped blobs, a fixed
caption band in Watch (EX1 D8: a caption never covers what it describes), `setStory` (Watch keeps one scale for the
whole recording), and, in Lab work, no drawing of what a step asks the student to find (§5 F6). Below 1000 px each
view shows one picture at the top and folds its second picture under it (as u32 did on 2026-11-18, V52 (b)): u34 the
orbit plane (the plots folded), u35 the bench with its counters (the curves folded), u37 the statistics (the
set-up line folded to a strip). Each view exposes its layout boxes (`canvas.__layout`, as S03's view does) for the
browser tests (§7).

### 1.4 Lab work at university

- **Sources.** A university worksheet names its course or manual instead of a school programme: `worksheet.basis`
  `[{text: T, source: "<citation>", quote?: "<verbatim>"}]` replaces `frp` at `ui: "standard"` (§5 F8). The quotation
  is printed verbatim, in its language, and marked as such.
- **Grading.** Each worksheet has `grading: [{item: T, points}]`, printed on the teacher's pages.
- **Errors that matter.** Every step's errors come from an instrument's division or from counting, never from the
  scatter alone; the fit is York's line (EX1 D3) or the power law in log–log; χ² and the Birge ratio are shown; the
  student chooses the model and the plot (the step's laws say which plot each law is about, EX1 D4).
- **CSV.** The lab's table exports as in EX1; Explore exports the shown point's series (§5 F7, V52 (m)).
- **Seeds.** Lab steps use seed 2, so a lab's sample is not the Explore sample of the same set-up (seed 1).
- **The teacher's switch.** At university the switch reads «For the instructor» / «Для преподавателя» (school keeps
  «For the teacher» / «Для учителя»): a glossary addition to `RULES.md` §7, made in step I.

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

### 2.3 Lab work: «Kepler's third law and the clock» and «The advance of the periapsis»

The two works are the three parts of one Lab work screen; the worksheet's `variants` print them separately (A: part
1; B: parts 2 and 3). They are computational labs: no laboratory measures orbits near a black hole, and university
courses do these as exercises on computed or tabulated orbits.

**Basis** (`worksheet.basis`, quoted verbatim; Appendix B):
- part 1: the CLEA laboratory «The Revolution of the Moons of Jupiter» (Gettysburg College, student manual v1.1.1):
  «Kepler’s Third Law is the one that applies to this lab.» and «You will determine Jupiter’s mass using measurements of
  each of the four moons; there will be errors of measurement associated with each moon, and therefore your Jupiter
  masses may not be exactly the same.» Here the moons are test bodies on circular orbits of a black hole, and the
  second clock is the new part.
- parts 2–3: Taylor, Wheeler & Bertschinger, *Exploring Black Holes*, 2nd ed. (draft of 2020-03-31), ch. 10 «Advance
  of Mercury's Perihelion»: «According to Einstein, the advance of Mercury’s perihelion springs from the difference
  between the frequency with which the planet sweeps around in its orbit and the frequency with which it oscillates in
  and out in r. In Newton’s analysis these two frequencies are equal (for the interaction between Mercury and the
  Sun).» Its eq. (23), ω_φ − ω_r ≈ (3M/r₀)ω_φ, gives the advance per orbit 6πM/r₀, and its Query 11 asks the student
  to «Compare the JPL-computed advances of the perihelia of Venus, Earth, and Mars in Table 10.1 with approximate
  results calculated using equation (23).» Part 3 goes one step further: the next order.

**Instruments** (`lab.instruments`; every set-up value exact, written without «± 0»):

| id | kind | reads | division | error |
|---|---|---|---|---|
| `radius` | readout | `control:r0` | 1 M | 0 (the console sets r₀) |
| `clock_far` | readout | `T_turn`: the distant observer's time per turn, the mean over the turns done | 0.1 GM/c³ | 0.05 |
| `clock_body` | readout | `tau_turn`: the body's proper time per turn | 0.1 GM/c³ | 0.05 |
| `protractor` | readout | `peri_shift`: the angle from the first periapsis ray to the latest | 0.1° | 0.05° |
| `fine_scale` | readout | `peri_shift` | 0.01° | 0.005° |
| `peri_count` | counter | `n_peri`: periapses passed, the launch included | 1 | 0 (an exact count) |
| `r_peri_scale`, `r_apo_scale` | readout | `r_peri`, `r_apo` measured at the apsis events | 1 M | 0.5 M |

**Part 1, «Circular orbits: the period and the clock»** — preset `default`, fixed `{ghost: false, speed: 1.0, angle:
0, time_units: "geo"}`; r₀ {7, 8, 10, 12, 15, 20, 30, 50, 100} M (9 points); stop `{events: {turn: 4}}`; `fps: 4`.

| columns | laws (x, y, model → quantity = reference) |
|---|---|
| r (`radius`), T (`clock_far`), τ (`clock_body`), x = 1/r (`expr`), q = (τ/T)² (`expr`) | (r, T, power → exponent) = 3/2: `kepler_exponent`, closed form (T = 2π√(r³/GM) is exact for a circular geodesic in the distant observer's time; the world's check «Orbital period (t) ↔ 2π√(r³/GM)»); (x, q, line → intercept) = 1: `clock_intercept`; (x, q, line → slope) = −3: `clock_slope`, closed form (dτ/dt = √(1 − 3M/r), the world's check «dτ/dt on a circular orbit») |

*Simulated* with the engine's fit on the instruments' readings of the closed-form periods (the world's circular
orbits agree with them to 10⁻¹⁰, its own check): exponent 1.500014 ± 0.000022
✓ (A = 6.2828 ± 0.0006, 2π); τ's power law: exponent 1.535, χ²/dof 7·10⁴, no verdict (the body's clock does not
follow Kepler's law); q against 1/r: intercept 0.999988 ± 0.000034 ✓, slope −2.9990 ± 0.0022 ✓.

**Part 2, «The advance after one orbit»** — fixed `{ghost: true, speed: 1.1, angle: 0}`; r₀ {300, 500, 700, 1000,
1500, 2000, 3000} M (7 points; M/p from 2.75·10⁻⁴ to 2.75·10⁻³, ε 0.210–0.213); stop `{events: {periapsis: 2}}`;
`fps: 4`. Columns: r₀, n (`peri_count`), shift (`protractor`), r_p, r_a, N = n − 1, Δφ = shift·π/180/N (rad),
x = M/p = (r_p + r_a)/(2 r_p r_a). Law: (x, Δφ, line0 → slope) = 6π: `advance_leading`, closed form (PPN, γ = β = 1;
`theories.approx.ppn`). *Simulated*: 19.04 ± 0.24 against 18.850 ✓ (z 0.76; χ²/dof 0.18, since rounding scatters by
a division/√12, not by the declared half division). The dashed Newton ellipse closes: Δφ = 0.

**Part 3, «Ten orbits with a fine scale: the next order»** — as part 2 with `fine_scale`, the ghost off, stop
`{events: {periapsis: 11}}`, `fps: 2`. Columns as part 2, plus y = Δφ/x. Laws: (x, Δφ, line0 → slope) = 6π
(`advance_leading`); (x, y, line → intercept) = 6π (`advance_leading`); (x, y, line → slope) = 6π(18 + ε²)/4:
`advance_next`, from `orbits.advance_series` (order 2), ε the mean of the step's orbits (85.03; the step's ε spread
0.2103–0.2129 changes it by 0.006 %). *Simulated*: the line through the origin gives 18.947 ± 0.023 with χ²/dof 14.9,
Birge ratio 3.86 > 3: no verdict, «the points scatter more than three times their errors»; y against x gives the
intercept 18.846 ± 0.012 (z −0.31 ✓) and the slope 89.2 ± 9.5 (z 0.43 ✓). The third order, (5/12)(54 + 9ε²)(M/p)²,
stays below the errors on this range (χ²/dof 0.22). This is the lesson: data a hundred times more precise need the next
order of the theory.

**Worksheet** (EN / RU; the answers are «For the instructor»; every number is tested against the atlas, §7):

| # | question | answer |
|---|---|---|
| 1 | What exponent did you find for T against r? Is Kepler's third law exact here? / Какой показатель степени получился для T в зависимости от r? Точен ли здесь третий закон Кеплера? | 1.50001 ± 0.00002: T = 2π√(r³/GM) holds exactly for circular orbits when T is a distant observer's time. / 1,50001 ± 0,00002: T = 2π√(r³/GM) выполняется точно для круговых орбит, если T — время далёкого наблюдателя. |
| 2 | Why does the body's own period τ not follow a power law? / Почему собственный период тела τ не подчиняется степенному закону? | τ = T·√(1 − 3M/r): the body's clock is slowed by gravity and by its speed, and the factor changes fast near 6 M, so ln τ against ln r is curved (χ²/dof about 7·10⁴). / τ = T·√(1 − 3M/r): часы тела замедлены тяготением и скоростью, а множитель быстро меняется вблизи 6 M, поэтому ln τ в зависимости от ln r — кривая (χ²/dof около 7·10⁴). |
| 3 | What are the intercept and slope of (τ/T)² against M/r, and what would Newton's mechanics give? / Каковы свободный член и наклон (τ/T)² в зависимости от M/r и что дала бы механика Ньютона? | 1.0000 and −2.999 ± 0.002: (τ/T)² = 1 − 3M/r. Newton: τ = T, intercept 1, slope 0, rejected by about 1 400 errors. / 1,0000 и −2,999 ± 0,002: (τ/T)² = 1 − 3M/r. У Ньютона τ = T: свободный член 1, наклон 0 — отвергнуто примерно на 1 400 погрешностей. |
| 4 | Where would a circular orbit's clock stop, and why is there no such orbit? / Где часы на круговой орбите остановились бы и почему такой орбиты нет? | At r = 3 M, the photon sphere: only light circles there; a massive body has no circular orbit at or inside 3 M, and no stable one inside 6 M. / При r = 3 M — на фотонной сфере: там по кругу движется только свет; у массивного тела нет круговой орбиты при 3 M и ближе, а устойчивой — ближе 6 M. |
| 5 | From your slope, predict Mercury's advance per Julian century (M/p = 2.662·10⁻⁸, 415.20 orbits per century). / По своему наклону предскажите смещение перигелия Меркурия за юлианское столетие (M/p = 2,662·10⁻⁸, 415,20 оборота за столетие). | slope × M/p × 415.20: with 19.04 ± 0.24, 43.4″ ± 0.5″; with 6π exactly 42.98″ (Will 2014: 42.98″). / наклон × M/p × 415,20: при 19,04 ± 0,24 — 43,4″ ± 0,5″; при 6π точно — 42,98″ (Will 2014: 42,98″). |
| 6 | What advance does Newton's dashed orbit show, and why? / Какое смещение показывает пунктирная орбита Ньютона и почему? | 0: for one point mass Newton's radial and angular frequencies are equal, so the ellipse closes. / 0: для одной точечной массы у Ньютона частоты радиальных колебаний и обращения равны, и эллипс замыкается. |
| 7 | Why does the line through the origin fail in part 3 but not in part 2? / Почему прямая через начало координат не проходит в части 3, а в части 2 проходит? | Ten orbits and the fine scale make Δφ 100 times more precise (±0.05° → ±0.0005° per orbit), and the next order, up to 1.2 % of Δφ at 300 M, becomes larger than the errors. / Десять оборотов и точная шкала делают Δφ в 100 раз точнее (±0,05° → ±0,0005° за оборот), и следующий порядок — до 1,2 % от Δφ при 300 M — становится больше погрешностей. |
| 8 | What do the intercept and the slope of Δφ·p/M against M/p measure? / Что измеряют свободный член и наклон Δφ·p/M в зависимости от M/p? | The intercept is Einstein's leading coefficient 6π (in the PPN form (2 + 2γ − β)/3·6π with γ = β = 1); the slope is the next order, 6π(18 + ε²)/4 ≈ 85. / Свободный член — главный коэффициент Эйнштейна 6π (в форме ППН (2 + 2γ − β)/3·6π при γ = β = 1); наклон — следующий порядок, 6π(18 + ε²)/4 ≈ 85. |

Grading (`grading`, 10 points per variant): A — the table complete with errors 2; the two plots with their fits 3;
the three laws checked and the χ² of τ's power law explained 3; questions 1–4: 2. B — the tables of parts 2 and 3 with
errors 2; the plots and fits 3; the leading order checked in part 2 and its failure in part 3 explained with χ² 3;
questions 5–8: 2. The teacher's notes say that the orbits are computed, that the errors are the instruments'
divisions, and why χ²/dof is about 0.2 (rounding).

### 2.4 Sizes and cost of u34

| item | grid | size | CPU |
|---|---|---|---|
| Watch `story` | 40 s, 20 fps | **0.32 MB** *measured* (trails u16) | 0.5 s |
| more: `rosette`, `mercury`, `plunge` | as today, with captions | 0.51 MB *measured* today (0.27 + 0.17 + 0.07) | 1.6 s |
| Explore | 7 × 5 = 35 | **2.8 MB** *estimate* (points measured 25–194 kB at fps 10) | ~7 s |
| Lab part 1 | 9 | 0.18 MB (20 kB per point *measured*) | 0.5 s |
| Lab part 2 | 7 | 0.17 MB (24 kB *measured*) | 0.7 s |
| Lab part 3 | 7 | 0.46 MB *estimate* (196 kB *measured* at fps 4 with the ghost; 65 kB at fps 2 without it) | 2.5 s |
| **u34 world** | | **4.4 MB** (target 12) | ~15 s |

### 2.5 What folds away at `ui: "standard"`

| today | Watch, Explore, Lab work | «▶ Compute live» |
|---|---|---|
| the orbit plane, the plots r(t) and 1 − dτ/dt | stay (the plots folded under the plane below 1000 px, except in Watch) | unchanged |
| quick bar: r₀, speed, angle, ghost, «push ±5 %», «↻ launch» | Explore: the atlas sliders r₀ and speed; the ghost an overlay; push and relaunch absent | unchanged |
| toolbar: earlier segments, GR radii, periapses, follow, «plots: whole segment», ⌖ orbit, ⌖ centre | overlays: Newton's orbit, GR radii, periapses, plots, follow; ⌖ orbit stays as a button | unchanged |
| left form (law, mass, radius, r₀, speed, angle, ghost, time units), actions | hidden | unchanged |
| right: «Orbit», «Clocks» | into «How we know this is right» (Explore keeps three readouts) | unchanged |
| the checks, «Physics of this world», events | the drawer; in Lab work verdicts only (§5 F6) | unchanged |

### 2.6 What the world gains (W34)

Measurables in the header (`measurables`) and per frame (`meas`): `adv_deg` with `adv_ref_deg`, `T_r` with
`T_r_ref`, `tau_over_t` (with `rate_ref` on circles), `T_turn`, `tau_turn`, `peri_shift`, `n_peri`, `r_peri`,
`r_apo` — each the run's own measurement from its events, the references the ones its checks use. An `event` of kind
`periapsis` for every periapsis up to the 12th (today up to the 3rd, then every 100th) and of kind `turn` for every
turn of a circular orbit up to the 12th, so the stop rules can count them (live runs keep the sparse rule beyond 12).
`lab_reference` for `kepler_exponent`, `clock_intercept`, `clock_slope`, `advance_leading`, `advance_next`. The view:
§1.3, plus `setTraces` (earlier orbits faded, labelled), and in Lab work no «exact formula» label on the plane.
`version` 1.0 → 1.1.

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
| 17 | `set` θ 56.31° | «The table turns to Brewster's angle, 56.3° = arctan 1.5: p-polarised photons (blue) are not reflected at all, and every reflected photon is s-polarised (orange). Reflection polarises light.» / «Столик поворачивается к углу Брюстера, 56,3° = arctg 1,5: фотоны с поляризацией p (синие) совсем не отражаются, и у каждого отражённого фотона поляризация s (оранжевые). Отражение поляризует свет.» | the new segment, 17 s |
| 27 | `set` n₀ 1.5, n_s 1, θ 30°, structure `tir`, gap 0 | «Now the light goes from inside the glass into air, at 30°: about 5.5 % is reflected.» / «Теперь свет идёт изнутри стекла в воздух, под углом 30°: отражается около 5,5 %.» | the new segment, 27 s |
| 34 | `set` θ 45° | «At 45°, beyond the critical angle of 41.8°, no photon gets out: total internal reflection.» / «При 45°, за критическим углом 41,8°, наружу не выходит ни один фотон: полное внутреннее отражение.» | the new segment, 34 s |
| 41 | `set` gap 200 nm | «A second glass block 200 nm behind the face: now about half of the photons cross the air gap. This is frustrated total reflection: the photons tunnel.» / «Второй стеклянный блок в 200 нм за гранью: теперь примерно половина фотонов пересекает воздушный зазор. Это нарушенное полное внутреннее отражение: фотоны туннелируют.» | the new segment, 41 s |

Each `set` of the media, the angle or the gap loses the photons in flight (7–14 each, with the world's notice), as
the world's README says. **More recordings**: `tir`, `brewster`, `spr`, with captions written by W35 by the same rule.

### 3.2 Explore «Boundary» (`explore`): media × θ × polarisation (138 points)

| field | value | why |
|---|---|---|
| preset, fixed | `brewster`; `{structure: "interface", lam_nm: 633, rate: 4e9}` | one boundary; the spectrum is flat without dispersion |
| controls | media (compound, §5 F3): «air → water» (n₀ 1, n_s 1.33), «air → glass» (1, 1.5), «glass → air» (1.5, 1) × θ {0, 4, …, 88}° (23) × polarisation {s, p} | defaults: air → glass, 32°, s |
| time, acts, traces | `buildup`, `now`, 0 | the cursor is the count; the computed curves already show the dependence on θ |
| speed, clock, stop | 5·10⁻⁸ (2 000 photons in 10 played s); `frame_dt` 25.2 ns; `{world_s: 5.04·10⁻⁷}` | §1.1 |
| quantize | `segment.Rs\|Ts\|As\|Rp\|Tp\|Ap\|Rc\|Tc\|Ac: u16`, `segment.E2: u16`, `clicks.t\|te: u16`, `frame.fl: u16` | drawn only; *measured* largest error 7.6·10⁻⁶ of each range; θ_B, θ_c, R, T and the counts stay float64 |
| drop | `blobs: ["segment.lam", "segment.lR*", "segment.lT*", "segment.lA*"]` (§5 F8) | the flat spectrum |
| overlays | beams (on), photons in flight (on), the field \|E\|² (on), the curves R(θ), T(θ) for s and p with θ_B and θ_c (on; folded under the bench below 1000 px) | the view's drawing today |
| readouts | reflected fraction R̂ ± its binomial error (ref: R of the segment), transmitted fraction T̂ ± error (ref: T), photons detected | §5 F7 |

What changes visibly: the beams turn with θ and their brightness follows R and T; the counts follow the curve; with
p photons the reflection vanishes at θ_B (53.1° water, 56.3° glass); from glass into air, from 44° on, nothing is
transmitted (θ_c = 41.8°) and the field decays beyond the face.

**[error in earlier]** EX1 §7: «angle θ (0–89°, 2°) × index n (1.33, 1.5, 1.7, 2.0) × polarisation (s, p,
unpolarised)». That is 540 points; at the *measured* 30–34 kB per point it is 17 MB, over the 12 MB atlas limit. And
an exit index alone never shows total internal reflection, which needs the light to come from the denser side: hence
the compound «media» control. The 4° steps lose nothing the curves do not show: the run computes them at 360 angles
plus its own θ_B and θ_c, and draws those exactly; the slider moves the beams and the counts. Unpolarised light is the
subject of Watch (Brewster) and stays in «▶ Compute live».

*Measured*: 30–34 kB per point (the curves u16; 44–52 kB with them f8), 0.02–0.04 s of CPU (0.35 s for the first
point of a process, the imports). *Estimate*: 138 × 32 kB = **4.4 MB**.

### 3.3 Explore «Coatings» (`coatings`): λ × coating (65 points)

| field | value |
|---|---|
| preset, fixed | `ar_mgf2`; `{theta_deg: 0, pol: "s", rate: 4e9}` (normal incidence: s and p are the same) |
| controls | λ {400, 425, …, 700} nm (13; the slider coloured by λ, as u32's) × coating (compound): «bare glass» (interface, n_s 1.5), «λ/4 layer, n_f 1.38 (like MgF₂)», «ideal λ/4 layer, n_f = √1.5», «Bragg mirror (H L)×4», «Bragg mirror (H L)×8» (n_H 2.3, n_L 1.45 on glass 1.52; λ₀ = 550 nm) |
| time, acts, speed, stop | as «Boundary» |
| quantize, drop | the spectrum `segment.lR*\|lT*\|lA*: u16`, `segment.E2: u16`, the clicks and packets as above; `drop.blobs` the angle curves `segment.th`, `segment.Rs` … `segment.Ac` |
| overlays | the spectrum R(λ), T(λ) with λ₀ (on), the field \|E\|² in the layers (on), beams and photons (on) |
| readouts | R̂ ± error (ref R), T̂ ± error (ref T) |

What changes visibly: at 550 nm the λ/4 layer reflects 1.4 % (computed 1.411 %) against 4.0 % of bare glass, and
the ideal one nothing; away from 550 nm the layer's R rises; the Bragg mirror reflects 93.7 % (×4) and 99.8 % (×8) of
the photons at 550 nm and almost nothing outside its band; the standing wave in the layers.

*Measured*: 25–29 kB per point, 0.02–0.2 s of CPU. *Estimate*: 65 × 28 kB = **1.8 MB**. (This is EX1 §7's «coatings as
a second Explore screen», with λ for «layer thickness × λ»: the thickness is λ₀/(4n) by design, and λ shows its
effect.)

### 3.4 Lab work: «Fresnel's formulae: the index of a glass and Brewster's angle»

**Basis** (`worksheet.basis`; Appendix B): Carnegie Mellon University, 33-353 «Intermediate Optics», «Lab 1:
FRESNEL RELATIONS and SNELL’S LAW» (Fall 2010): «Find Brewster's angle, the angle for which there is no reflected beam
for light polarized in the plane of reflection.», «Measure Brewster's angle and use it to determine the index of
refraction of the plexiglass.» and «Plot reflected power versus angle for each polarization and compare to theory.»;
and the Rutgers handout «Fresnel Equations and Electromagnetic Boundary Conditions»: «By fitting your data with
Fresnel’s equations you will obtain the following: i) the index refraction ii) the critical angle iii) Brewster’s
angle.» Here the reflected «power» is a count of photons, and the student finds n twice, from s and from p light.

**The linearisations** (derived for this design; W35 tests them against the engine's `interfaces.stack` and against
an independent 30-digit evaluation of Fresnel's formulae). For light from n₁ = 1 into n, with sin θ = n sin θ_t:
√R_s = (n cos θ_t − cos θ)/(n cos θ_t + cos θ) at every θ, so

  y_s ≡ (cos θ · (1 + √R_s)/(1 − √R_s))² = n² cos²θ_t = n² − sin²θ,

a straight line in x = sin²θ with intercept n² and slope −1. For p light below Brewster's angle, √R_p = (n cos θ −
cos θ_t)/(n cos θ + cos θ_t) ≥ 0, so

  y_p ≡ (cos θ · (1 − √R_p)/(1 + √R_p))² = cos²θ_t/n² = 1/n² − sin²θ/n⁴,

a line with intercept 1/n² and slope −1/n⁴. Both are exact for a lossless boundary. Above θ_B, r_p changes sign and
the second form needs −√R_p (question 3).

**Rejected on evidence**: the vertex of a parabola through R_p(θ) near θ_B, the obvious way to «find Brewster's
angle». *Simulated* with Poisson counts (Appendix A.3): over 50–63° the vertex is biased by −0.40° (−3.7σ at 20 000
photons per angle, −18σ at 400 000), over 52–61° by −0.21° (−1.7σ to −8σ), over 46–66° by −1.0°: R_p is not symmetric
about θ_B. The linearised line has no such bias.

**The sample** is a new preset `lab_glass`: a single boundary, air → glass n_s = 1.515 (like a BK7 glass at 633 nm,
illustrative), λ 633 nm, 4·10⁹ photons per second. In Lab work the view names it «a glass of unknown index» and does
not print n_s (§5 F6); the teacher's pages give it.

**Instruments**:

| id | kind | reads | division | error |
|---|---|---|---|---|
| `table` | readout | `control:theta_deg` | 1° | 0 (the rotary table is set at its marks) |
| `det_R` | counter | `n_R`: photons counted by the reflection detector in this run | 1 | Poisson, √N (1 for N = 0) |
| `det_T` | counter | `n_T`: photons counted by the transmission detector | 1 | Poisson |

**Part 1, «s photons»** — preset `lab_glass`, fixed `{pol: "s"}`; θ {0, 10, …, 80}° (9 points); 20 000 photons per
point (stop `{world_s: 5.004·10⁻⁶}`), `frame_dt` a tenth of it; seed 2. Columns: θ, N_R, N_T, R = N_R/(N_R + N_T),
x = sind(θ)², y = (cosd(θ)·(1 + sqrt(R))/(1 − sqrt(R)))². Laws: (x, y, line → intercept) = n² (`n_squared`,
2.2952, closed form from the world's n_s); (x, y, line → slope) = −1 (`minus_one`, exact). *Simulated* (600 samples):
intercept 2.2944 ± 0.0183 (scatter 0.0166), slope −1.0002 ± 0.0298; within two errors in 96.8 % and 96.2 % of
samples; χ²/dof 0.96.

**Part 2, «p photons below Brewster's angle»** — fixed `{pol: "p"}`; θ {0, 5, …, 50}° (11 points; R_p ≥ 0.0037,
at least ~70 photons counted). Columns as part 1 with y = (cosd(θ)·(1 − sqrt(R))/(1 + sqrt(R)))². Laws: intercept =
1/n² (`inv_n_squared`, 0.43569); slope = −1/n⁴ (`minus_inv_n4`, −0.18982). *Simulated*: intercept 0.4353 ± 0.0030
(scatter 0.0028), slope −0.1888 ± 0.0089; within two errors in 96.7 % and 96.0 %; χ²/dof 1.02. So n = 1.515 ± 0.006
(part 1) and 1.516 ± 0.005 (part 2), and θ_B = arctan n = 56.57° ± 0.10°.

**Worksheet**:

| # | question | answer |
|---|---|---|
| 1 | What index n do you get from part 1 and from part 2? Do they agree? / Какой показатель преломления n получается из части 1 и из части 2? Согласуются ли они? | About 1.515 ± 0.006 and 1.516 ± 0.005 (the glass: 1.515); they differ by less than one combined error. / Около 1,515 ± 0,006 и 1,516 ± 0,005 (у стекла 1,515); различие меньше одной общей погрешности. |
| 2 | What is Brewster's angle of this glass, and why is no p light reflected there? / Каков угол Брюстера для этого стекла и почему p-свет там не отражается? | arctan n ≈ 56.6°. There θ + θ_t = 90°, so r_p = tan(θ − θ_t)/tan(θ + θ_t) = 0: the reflected direction is along the oscillation of the dipoles excited in the glass, and a dipole does not radiate along its axis. / arctg n ≈ 56,6°. Там θ + θ_t = 90°, и r_p = tg(θ − θ_t)/tg(θ + θ_t) = 0: направление отражения совпадает с направлением колебаний диполей в стекле, а диполь не излучает вдоль своей оси. |
| 3 | Why does part 2 stop at 50°? / Почему часть 2 заканчивается на 50°? | r_p changes sign at θ_B; the counts give only \|r_p\| = √R_p, and beyond θ_B the formula would need −√R_p. / r_p меняет знак при θ_B; счёт фотонов даёт только \|r_p\| = √R_p, а за θ_B в формулу нужно подставлять −√R_p. |
| 4 | Each detector's count has the Poisson error √N. Show that the error of R = N_R/(N_R + N_T) is then the binomial √(R(1 − R)/N). / У счёта каждого детектора пуассоновская погрешность √N. Покажите, что погрешность R = N_R/(N_R + N_T) тогда биномиальная, √(R(1 − R)/N). | σ_R² = (N_T/N²)²N_R + (N_R/N²)²N_T = N_R N_T/N³ = R(1 − R)/N. / σ_R² = (N_T/N²)²N_R + (N_R/N²)²N_T = N_R N_T/N³ = R(1 − R)/N. |
| 5 | How many photons per angle would halve the error of n? / Сколько фотонов на угол нужно, чтобы погрешность n уменьшилась вдвое? | Four times as many, 80 000: the errors fall as 1/√N. / Вчетверо больше, 80 000: погрешности убывают как 1/√N. |
| 6 | Compare your count at θ = 0 with ((n − 1)/(n + 1))². / Сравните свой счёт при θ = 0 с ((n − 1)/(n + 1))². | 0.0419 for n = 1.515; N_R/N ≈ 0.042 ± 0.0014 at 20 000 photons. / 0,0419 при n = 1,515; N_R/N ≈ 0,042 ± 0,0014 при 20 000 фотонов. |

Grading (10 points): the two tables with errors 2; the two linearised plots with their lines 3; the four laws checked,
n twice and θ_B with errors 3; questions 2.

### 3.5 Sizes and cost of u35

| item | grid | size | CPU |
|---|---|---|---|
| Watch `story` | 50 s, 20 fps | **0.87 MB** *measured* (clicks' times u16) | 0.6 s |
| more: `tir`, `brewster`, `spr` | as today, with captions | 0.43 MB *measured* today | 0.6 s |
| Explore «Boundary» | 3 × 23 × 2 = 138 | **4.4 MB** *estimate* (30–34 kB *measured*) | ~6 s |
| Explore «Coatings» | 13 × 5 = 65 | **1.8 MB** *estimate* (25–29 kB *measured*) | ~4 s |
| Lab parts 1 and 2 | 9 + 11 = 20 | 0.14 MB *estimate*: 29–31 kB *measured* with the curves dropped, of which 22–24 kB are the clicks, which a lab does not draw (`drop.types: ["clicks"]`) | ~1 s |
| **u35 world** | | **7.6 MB** (target 12) | ~12 s |

### 3.6 What folds away at `ui: "standard"`

| today | Watch, Explore, Lab work | «▶ Compute live» |
|---|---|---|
| the bench (beams, photons, detectors, the structure to scale, \|E\|²) and the curves panel (R(θ), R(λ), counters) | stay; below 1000 px the bench with its counters on top, the curves folded under it | unchanged |
| quick bar: λ, θ, polarisation, structure, «▷ photon flight», «▷▷ collect statistics» | Explore: the atlas sliders; the two speeds become the screen's «normal / slow» | unchanged |
| left form: 18 parameters of six structures; actions «Emit one photon», «Reset the counters» | hidden | unchanged |
| right: «Set-up of this segment», «Photons», «Approximations» | into «How we know this is right» | unchanged |
| in Lab work: the curves, the expectation ticks and σ whiskers of the counters, the indices of the sample | not drawn (§5 F6) | — |

### 3.7 What the world gains (W35)

Measurables: `n_R`, `n_T`, `n_A`, `n` (the segment's counts), `R_frac` and `T_frac` with their binomial errors and
the segment's computed R and T as references. The preset `lab_glass`. `lab_reference` for `n_squared`, `minus_one`,
`inv_n_squared`, `minus_inv_n4`. `QUANT_SAFE` for the curves, the field, the clicks' times and the packets. The view:
§1.3; in Lab work no curves, no expectation ticks or whiskers, no indices of the sample. `version` 1.0 → 1.1.

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

### 4.2 Explore: the CHSH angle Δ × the law (26 points)

| field | value | why |
|---|---|---|
| preset, fixed | `photon_chsh`; `{switch: "random", tau_ns: 100, L_m: 500, rate: 1e6}` | the loophole-free arrangement the world models |
| controls | Δ (compound, §5 F3: a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ) {0, 7.5, …, 90}° (13) × law {quantum mechanics, local hidden variables} | the law control is allowed at `standard` and flagged at the control and in the bar (EX1 §2.1); default 22.5°, quantum |
| time, acts, traces | `buildup`, `now`, 5 | earlier Δ's S stay on the S(Δ) plot, faded |
| speed, clock, stop | 4·10⁻⁴ (4 000 pairs in 10 played s); `frame_dt` 0.2 ms; `{world_s: 4.0033·10⁻³}` | §1.1 |
| overlays | the set-up line with the stations and the flashes (on), the spacetime diagram of the last pair (on; folded below 1000 px), E(Δ) with the measured cells (on), S(Δ) with the measured S and its traces (on), the other law's curves (on) | the S(Δ) plot is new (§4.6) |
| readouts | S ± σ (ref: S of the world's law at these settings), (\|S\| − 2)/σ, pairs counted | §5 F7 |

What changes visibly: S(Δ) = 3 cos 2Δ − cos 6Δ for the quantum law (2 at 0°, 2√2 at 22.5°, 0 at 45°, −2√2 at 67.5°)
and half of it for the local polarisation model (at most √2); with 4 000 pairs the measured S carries ±0.04–0.06.

**[error in earlier]** EX1 §7: «analyser angle b (0–90°, 5°) × law → E(a, b) … S». With a, a′ and b′ fixed, b alone
moves one cell of S and does not show the CHSH curve, whose maximum needs all four angles in step; the compound Δ does.

*Measured*: 18–30 kB per point, 0.02–0.04 s of CPU. *Estimate*: 26 × 28 kB = **0.73 MB**.

### 4.3 Lab work: «Entangled photons and the Bell inequality»

**Basis** (`worksheet.basis`; Appendix B): D. Dehlinger and M. W. Mitchell, «Entangled photons, nonlocality, and Bell
inequalities in the undergraduate laboratory», Am. J. Phys. 70, 903 (2002) (arXiv:quant-ph/0205171): «The experiments
described can be performed in an afternoon.» Their E(α, β) comes from four coincidence counts and S from sixteen, the
error of each count is taken from counting statistics («To be sure of the result, we compute its statistical
uncertainty.»), and they conclude «We have violated the Bell inequality.» with S = 2.307 ± 0.035. Here the source and
the detectors are ideal (the world's README), so the quantum S reaches 2√2.

**Instruments**:

| id | kind | reads | division | error |
|---|---|---|---|---|
| `pol_A`, `pol_B` | readout | `control:a_deg`, `control:b_deg` | 1° | 0 (the polarisers are set at their marks) |
| `delta` | readout | `control:delta` (the compound control) | 0.5° | 0 |
| `c_pp`, `c_pm`, `c_mp`, `c_mm` | counter | `n_pp`, `n_pm`, `n_mp`, `n_mm`: coincidences of the setting pair (a, b) in this run | 1 | Poisson, √N (1 for N = 0) |
| `E_1` … `E_4` | readout | `E_ab`, `E_ab2`, `E_a2b`, `E_a2b2`: the run's E of each setting pair from its coincidence counts | 0.0001 | the run's own standard error √((1 − E²)/N) (`sigma`: `E_ab_se` …; §5 F4) |

**Part 1, «The correlation E(α, β)»** — preset `scan` (fixed settings); a {0, 45}° × b {0, 15, …, 90}° (14 points);
1 000 pairs per point (stop `{world_s: 1.0033·10⁻³}`); seed 2. Columns: a, b, N₊₊, N₊₋, N₋₊, N₋₋,
E = (N₊₊ + N₋₋ − N₊₋ − N₋₊)/(N₊₊ + N₋₋ + N₊₋ + N₋₊) (Dehlinger and Mitchell's eq. (25), here with two-channel
analysers: + and − are α and α⊥), c = cosd(2(b − a)). Law: (c, E, line0 → slope) = 1: `visibility`, closed form
(E = cos 2(β − α) for |Φ⁺⟩; the world's check against the engine's trace). *Simulated* (300 samples): 1.0001 ±
0.0017 (scatter 0.0003: the one-count floor at E = ±1 dominates, question 2).

**Part 2, «The CHSH test»** — preset `photon_chsh`; Δ {7.5, 15, …, 82.5}° (11 points: at 0° and 90° all four cells are
±1 and the run's error of S is 0, which a weighted fit cannot take); 4 000 pairs per point; seed 2. Columns: Δ,
E₁ … E₄, S = E₁ − E₂ + E₃ + E₄ (the cells are independent samples, so the propagation is exact), x = 3 cosd(2Δ) −
cosd(6Δ). Law: (x, S, line0 → slope) = 1: `chsh_quantum`. *Simulated*: 0.9996 ± 0.0057 (within two errors in 96 %),
χ²/dof 1.02; at 22.5° S = 2.83 ± 0.045, 18.6 errors above 2.

**Part 3, «The same test in a world of local hidden variables»** — preset `photon_lhv` (the law parameter `lhv`:
Lab work shows «MODIFIED PHYSICS» in its bar and on the step card, §5 F6); the same columns and grid. Law: (x, S, line0
→ slope) = ½: `chsh_local`, from the model's exact E = ½ cos 2(β − α) (`theories.alternatives.local_hidden`).
*Simulated*: 0.5003 ± 0.0085; at 22.5° S = 1.417 ± 0.059, 9.9 errors below 2; the largest S at 22.5° in 300 samples
1.57.

**Worksheet**:

| # | question | answer |
|---|---|---|
| 1 | What slope V of E against cos 2(β − α) did you find, and what does the local model of part 3 predict? / Какой наклон V зависимости E от cos 2(β − α) у вас получился и что предсказывает локальная модель из части 3? | 1.000 ± 0.002: E = cos 2(β − α). The local polarisation model gives E = ½ cos 2(β − α), V = ½. / 1,000 ± 0,002: E = cos 2(β − α). Локальная поляризационная модель даёт E = ½ cos 2(β − α), V = ½. |
| 2 | At β = α every pair agrees and N₊₋ = N₋₊ = 0. Why is the error of E not 0? / При β = α все пары совпадают и N₊₋ = N₋₊ = 0. Почему погрешность E не равна 0? | A count of 0 carries the error of one count: a finite sample cannot exclude a rare disagreement; σ_E ≈ 2√2/N = 0.003 for 1 000 pairs. / Нулевой счёт несёт погрешность в один отсчёт: конечная выборка не исключает редкого несовпадения; σ_E ≈ 2√2/N = 0,003 при 1 000 пар. |
| 3 | What S did you find at Δ = 22.5°, and by how many errors does it exceed 2? / Какое S получилось при Δ = 22,5° и на сколько погрешностей оно больше 2? | About 2.83 ± 0.045; (S − 2)/σ ≈ 18. / Около 2,83 ± 0,045; (S − 2)/σ ≈ 18. |
| 4 | Dehlinger and Mitchell found S = 2.307 ± 0.035. Why is your S larger? / Делингер и Митчелл получили S = 2,307 ± 0,035. Почему ваше S больше? | Their source and detectors are real: accidental coincidences and imperfect entanglement lower \|S\|; this world's source and detectors are ideal, so S = 2√2 at 22.5°. / У них настоящие источник и детекторы: случайные совпадения и неидеальная запутанность уменьшают \|S\|; здесь источник и детекторы идеальны, и при 22,5° S = 2√2. |
| 5 | Why is each setting chosen just before the photon arrives (τ = 100 ns), and what does cτ < 2L ensure? / Зачем установка выбирается незадолго до прихода фотона (τ = 100 нс) и что обеспечивает условие cτ < 2L? | The choice is then space-like to the other side's detection (cτ = 30 m < 2L = 1 000 m): no signal from it can reach the other measurement (the locality loophole is closed). / Тогда выбор пространственноподобен регистрации на другой стороне (cτ = 30 м < 2L = 1 000 м): никакой сигнал от него не успевает к другому измерению (лазейка локальности закрыта). |
| 6 | Why can no local model give \|S\| > 2? / Почему никакая локальная модель не даёт \|S\| > 2? | Each outcome is ±1, fixed by the hidden variable λ and the own setting: A(a)[B(b) − B(b′)] + A(a′)[B(b) + B(b′)] = ±2 for every λ, so the average \|S\| ≤ 2. / Каждый исход ±1 определяется скрытым параметром λ и своей установкой: A(a)[B(b) − B(b′)] + A(a′)[B(b) + B(b′)] = ±2 при каждом λ, поэтому среднее \|S\| ≤ 2. |

Grading (10 points): the three tables with errors 2; the plots and the three fits 3; the slopes checked, S at 22.5°
with its error and (S − 2)/σ, part 3 compared with part 2 3; questions 2.

### 4.4 Sizes and cost of u37

| item | grid | size | CPU |
|---|---|---|---|
| Watch `story` | 50 s, 20 fps, two worlds | **0.64 MB** *measured* | 0.7 s |
| more: `chsh`, `local_model`, `scan` | as today, with captions | 0.13 MB *measured* today | 1.5 s |
| Explore | 13 × 2 = 26 | **0.73 MB** *estimate* (18–30 kB *measured*) | ~1 s |
| Lab part 1 | 14 | 0.14 MB (9–10 kB *measured*) | 0.3 s |
| Lab parts 2 and 3 | 11 + 11 | 0.62 MB *estimate* (28–30 kB *measured* for these set-ups at 4 000 pairs) | 0.8 s |
| **u37 world** | | **2.3 MB** (target 12) | ~5 s |

### 4.5 What folds away at `ui: "standard"`

| today | Watch, Explore, Lab work | «▶ Compute live» |
|---|---|---|
| the set-up line and the spacetime diagram; the statistics (the cells, S, E(Δ)) | stay; below 1000 px the statistics on top, the set-up line a strip, the spacetime diagram folded | unchanged |
| quick bar: a, a′, b, b′, choice, τ, L; toolbar: «▷ flight», «▷▷ collect statistics», «⟲ reset the statistics», light cones, the other law's curve | Explore: the atlas sliders Δ and law; light cones and the other law's curve become overlays; the speeds the screen's «normal / slow» | unchanged |
| left form: pairs, the particles' speed, law, L, rate, choice, τ and the four angles | hidden | unchanged |
| right: «Set-up and spacetime», «Counters», «Last pairs» | into «How we know this is right» | unchanged |
| in Lab work: the law's curves, the cells' expected E, S of the law | not drawn (§5 F6) | — |

### 4.6 What the world gains (W37)

Frames get `meas` (u37 has none today) and the header `measurables`: `n_pp`, `n_pm`, `n_mp`, `n_mm` of the pair (a, b),
`E_ab` … `E_a2b2` with their errors, `S` with its error and the law's S as its reference, the pairs counted. A header
blob of the law's S(Δ) in the CHSH geometry for both laws, computed with the world's own `Law.E` (as its E(Δ) curves
are), for the new S(Δ) plot. `lab_reference` for `visibility`, `chsh_quantum`, `chsh_local`. The view: §1.3, the S(Δ)
plot with traces, and in Lab work no law curves, no expected E and no S of the law. `version` 1.0 → 1.1.

---

## 5. The framework changes (step F, before the worlds)

Eight changes, each general, each needed by at least one world and named by its reason. They touch `server/lfviz/`
and `site/`, which every key covers, so all of them land in one step and every world is recorded again once (in CI by
its matrix entry, as after EX1).

| # | change | files | reason |
|---|---|---|---|
| F1 | **The screen's time scale.** An Explore screen or a lab step may declare `speed`: world seconds per played second, or `"world"` (the point's own default speed, from its `state` message, which the packed point keeps). Its atlas takes either `frame_dt` (world seconds) or `fps` (frames per played second at the world's default speed; `headless.run_spec` already has this clock). «normal / slow» multiply the screen's speed by 1 and ¼; the time label states «world 0.0123 s · ×1/120 · 3.1 s / 24.0 s» (in the world's time unit: u34 GM/c³). | `registry._check_atlas_common` (exactly one of `frame_dt`, `fps`; `speed` > 0 or `"world"`), `atlases_of` (the clock), `site/atlas.py run_point`, `atlas_live.py`, `player/js/explore.js`, `lab.js`, `demo.js` (bar) | §1.1: u34 0.05 s per orbit, u35 1 ns per photon, u37 2 µs per pair; u34's periods differ 15× |
| F2 | **Stop by counted events.** `stop: {events: {<kind or name>: n, …}, after_s?, max_world_s}`: the point stops `after_s` after the first kind that has occurred n times; `{event: k}` stays as the shorthand of `{events: {k: 1}}`. | `headless.run_spec` (counts in `keep`), `registry` (the stop's form) | u34: three radial periods (`periapsis: 4`), three turns (`turn: 3`) or the fall (`horizon: 1`) |
| F3 | **Compound controls.** `{id, label, unit?, values, labels?, sets: {<param>: [one value per grid value], …}}`: one slider (or select) sets several parameters. The manifest records the sets; `control:<id>` reads the shown point's grid value (its manifest index); a trace label and the passport name the control's value and, in the passport, the parameters it set. On a server a compound control takes grid values only (the live endpoint answers 400 off the grid). | `registry.check_screens` (the params exist, the lists align with `values`, every combination resolves, no `param` with `sets`), `screens_of`, `site/atlas.py` (grid → parameter values), `atlas_live.py`, `explore.js`, `lab.js` | u37's Δ (a = 0, b = Δ, a′ = 2Δ, b′ = 3Δ); u35's media (n₀, n_s) and coatings (structure and its parameters) |
| F4 | **Counting instruments and the run's own errors.** `kind: "counter"` reads an integer measurable; `error: "poisson"` gives √N (1 for N = 0, said in the instrument's line: «a count of 0 has the error of one count») or a number (0: an exact count). A `readout` may declare `sigma: "<measurable>"`: its error is the run's own standard error at the cursor; its division is then only the display precision. | `registry.INSTRUMENT_KINDS`, `_check_lab`, `site/atlas.py check_declarations` (`sigma` names a declared measurable), `lab.js` (`reading`, `readingText`, `instrumentText`), `worksheet.js` (the instrument line) | u35's detectors, u37's coincidences (Dehlinger and Mitchell's √N), u37's E with the error of `tools.bell_stats` |
| F5 | **Formula columns.** `{id, label, expr}`: numbers, earlier column ids, + − * / ^, unary −, parentheses, `sqrt ln exp abs sin cos tan asin acos atan` (radians), `sind cosd tand asind acosd atand` (degrees), `pi`. Errors: σ_f² = Σ(∂f/∂x_i·σ_i)² + ½Σ(∂²f/∂x_i²)²σ_i⁴ over independent inputs (EX1's rule for one variable, extended), the derivatives exact by hyper-dual numbers, never finite differences. An undefined value (√ of a negative, a division by 0) leaves the cell empty with the reason. No `eval`: a small parser of this grammar only; the formulas come from the registry, never from the viewer. `of` + `op` stay (S03). | new `player/js/expr.js` and `server/lfviz/expr.py` (the same grammar; the registry parses every formula and checks that it names earlier columns only; Python evaluates for the tests and the worksheets' answers), `lab.js`, a shared fixture `player/js/tests/fixtures/expr_cases.json` (values and errors to 1e-12 in Node) | E from four counts, R from two, the Fresnel linearisations, S from four E, Δφ from a shift, M/p from two radii: no new special operation |
| F6 | **Lab work does not give the answer away, and flags modified physics.** In Lab work the drawer lists each check's label and verdict (✓, ✗, ≈, —) without its value, reference or note, and the events by kind, without text or time (EX1 D10, extended); a check that fails still shows ✗. The view's contract: with `ctx.screen = "lab"` a view draws nothing a step asks the student to find (each world names what, §2.6, §3.7, §4.6; checked from `canvas.__layout` in the browser). A step whose points carry `modifications` shows «MODIFIED PHYSICS: …» on its step card and in the bar, as Explore does; a law parameter in a step's preset or `fixed` is allowed at `standard` only. | `demo.js howWeKnow` (the lab mode), `lab.js` (the band), `registry._check_lab`, `RULES.md` §10 | u35's Brewster check names n; u37's checks name E and S; u34's segment event names the exact advance; u37's part 3 is a modified world |
| F7 | **Readouts with an error and a reference; the CSV of the shown point.** A measurable may declare `sigma` and `ref` (ids of other measurables of the same frame) and `ref_label` (a T): Explore prints «advance per orbit 52.155° (formula 52.155°)», «S 2.864 ± 0.040 (law 2.828)». At `standard`, «CSV of this point» exports one row per frame up to the time shown: t and every declared measurable with its σ, built in the browser from the decoded point. | `explore.js`, `registry` and `site/atlas.py check_declarations` (`sigma`, `ref` name declared measurables) | V52 (m); the first half of V52 (n) (the mechanism; u32's own fringe-period readout and its log scale stay open there) |
| F8 | **Packing and the registry's details.** `drop.blobs: ["<type>.<blob>", …]` (a `*` at the end of a blob name allowed) drops blobs of any message type (`frame_blobs` stays as the shorthand for `frame.*`). `worksheet.basis: [{text, source, quote?}]` replaces `frp` at `standard`; `worksheet.grading: [{item, points}]`; at `standard` the answers' switch reads «For the instructor» / «Для преподавателя». `anchors()` is required of a 2-D view only when a lab step uses a `ruler` or a `protractor` (read from the view's source like `OVERLAYS`). | `headless.Packer`, `registry` (`_check_worksheet`, the anchors rule), `worksheet.js`, `RULES.md` §7 glossary (step I) | u35's flat spectrum and its labs' curves (25 of 31 kB per lab point); university sources and grading; V52 (l) |

What does not change: the atlas format (`ATLAS_VERSION` 2: a compound control is a control; the clock and the stop
are in the spec and so in the key), quantisation, the live endpoint's limits, the budgets, the fit (`fit.js` and
`linear_fit` as after EX1's D3).

---

## 6. Atlases and budgets

Budgets as EX1 §1.8 (`sitelib.BUDGET`): a point 150 kB / 400 kB, an atlas 6 / 12 MB, a world 12 / 25 MB, the site 600 /
900 MB; at most 6 controls and 1 500 / 3 000 points per atlas at `standard`.

| world | atlas | grid | points | per point | atlas | CPU |
|---|---|---|---|---|---|---|
| u34 | `explore` | r₀ 7 × speed 5 | 35 | 25–194 kB *measured* (fps 10), largest 168 kB *estimate* at fps 8 | **2.8 MB** *estimate* | ~7 s |
| u34 | `lab.circles` | r₀ 9 | 9 | 20 kB *measured* | 0.18 MB | 0.5 s |
| u34 | `lab.advance1` | r₀ 7 | 7 | 24 kB *measured* | 0.17 MB | 0.7 s |
| u34 | `lab.advance10` | r₀ 7 | 7 | 65 kB *estimate* (196 kB *measured* at fps 4 with the ghost; the ghost's trail 67 kB of it) | 0.46 MB | 2.5 s |
| u35 | `explore` | media 3 × θ 23 × pol 2 | 138 | 30–34 kB *measured* | **4.4 MB** *estimate* | ~6 s |
| u35 | `coatings` | λ 13 × coating 5 | 65 | 25–29 kB *measured* | **1.8 MB** *estimate* | ~4 s |
| u35 | `lab.s`, `lab.p` | θ 9; θ 11 | 20 | ~7 kB *estimate* (29–31 kB *measured* with the clicks) | 0.14 MB | ~1 s |
| u37 | `explore` | Δ 13 × law 2 | 26 | 18–30 kB *measured* | **0.73 MB** *estimate* | ~1 s |
| u37 | `lab.correlation` | a 2 × b 7 | 14 | 9–10 kB *measured* | 0.14 MB | 0.3 s |
| u37 | `lab.chsh`, `lab.local` | Δ 11; Δ 11 | 22 | 28–30 kB *measured* | 0.62 MB | 0.8 s |

| world | recordings (Watch and more) | atlases | **world** | target / limit |
|---|---|---|---|---|
| u34 | 0.32 + 0.51 MB | 3.6 MB | **4.4 MB** | 12 / 25 MB |
| u35 | 0.87 + 0.43 MB | 6.3 MB | **7.6 MB** | 12 / 25 MB |
| u37 | 0.64 + 0.13 MB | 1.5 MB | **2.3 MB** | 12 / 25 MB |

The site: 65.6 MB (*measured* 2026-11-17), of which the three worlds' present recordings are 1.1 MB; with the 14.3 MB
above, about 79 MB. Every atlas is far inside 1 500 points and 6 MB; one point (u34's zoom-whirl) is over the 150 kB
target and is accepted with its reason. CPU per world under a minute (the first point of a process 0.3–0.5 s for the
imports).

**Stochastic points** (EX1 §1.6): u35 and u37 store one seeded sample (seed 1 in Explore, seed 2 in Lab work) and the
run's computed probabilities (u35's R, T, A of the segment; u37's E and S of the law), with the run's own statistical
checks; «Another sample» on a server draws the next seed.

---

## 7. Tests

**Framework (step F).** `test_headless.py`: the `fps` clock; stops by counted events (the first kind to reach its
count; `after_s`; `max_world_s` failing; the shorthand). `test_atlas.py`: the toy world `s98_atlas_toy` gains a
compound control, a counter measurable, a measurable with `sigma` and `ref`, a step with formula columns and a stop by
counted events, and `drop.blobs`; its committed fixture is remade and compared byte for byte. `test_expr.py` and
`expr.test.mjs`: the shared fixture (values and both error terms against mpmath-differentiated references, to 1e-12);
refused inputs (an unknown name, a later column, bad syntax, `constructor`, `__proto__`, a call of anything not in the
grammar). `lab.test.mjs`: counters (√N, the floor at 0, an exact count), readouts with the run's σ, formula columns,
the CSV. `test_site_registry.py`: compound controls, counters, `sigma`, `basis` and `grading` at `standard`, the anchors
rule, a law parameter in a school step refused. `test_atlas_live.py`: a compound control off the grid → 400.

**The worlds.** Each world's `tests/test_<world>_screens.py`:
- every grid point of every atlas builds with all checks ✓ and stops by its own rule (u34: the counted events);
- every new lab law's reference against an independent computation: u34 — the exponent and the clock law against a fit
  of the world's own measured turns, 6π against `ppn.periapsis_advance`/(M/p) in the limit, the next order against a
  fit of the exact elliptic integral `orbits.periapsis_advance` at small M/p (not `advance_series`, which gives the
  reference); u35 — both linearisations against the engine's R at 1 000 random (n, θ) to 1e-12 and against a 30-digit
  mpmath evaluation of Fresnel's formulae; u37 — E from four counts against `bell_stats.correlation`, S(Δ) against
  the engine's `Law.E`, the local model's ½ against `local_hidden`'s exact E;
- the worksheet's numbers against the atlas: the readings of every lab atlas, fitted by `linear_fit`, reproduce the
  numbers the answers state. u34's are deterministic and must equal this design's (19.04 ± 0.24, …); u35's and u37's
  come from one seeded sample, so W35 and W37 replace this design's simulated means with the built sample's values
  and the test checks those, and also that they lie within the simulated spread (Appendix A.3);
- the Watch captions' numbers against the recording (u34: 52°, 156°, 120°, 8 %, 17.5 %, 2.6 ms; u35: 4 %, 96 %,
  56.3°, 5.5 %, 41.8°, half; u37: 2.86 ± 0.04 after about 5 000 pairs, 1.4) and every caption no later than its event.

**Browser** (EN and RU; 1280 × 800 and 390 × 844, also 390 × 700 for V52 (ab); a private server, never 8479; the
recordings and atlases built by the code under test, `site/fixtures.py --world …`):
- `demo_screens.mjs` for u34, u35 and u37: Watch (captions, chapters, a hold, the time label with the factor);
  Explore (grid values only on the site, the compound controls' labels, readouts with their references and errors,
  overlays, traces, the CSV); Lab work (every set-up of every part measured, the fits, the verdicts as simulated —
  including u34 part 3's «no verdict» for the line through the origin — the drawer without values, «MODIFIED PHYSICS»
  in u37 part 3, the worksheet in EN and RU with and without the instructor's pages, one A4 sheet per part);
- each world's `<world>_screens.mjs`, from its view's `canvas.__layout`: a caption's band never covers what it
  describes at that caption's time (u34 the periapsis marker and the clock plot; u35 the detectors and the counters; u37
  the S readout and the stations); in Lab work no curve or expectation is drawn; at 390 px the view, the step's control
  and «Measure» are on screen together; no horizontal scroll; no text out of its box;
- `site_smoke.mjs` (every screen of the three worlds on the built site under `/lfphys/`), `start_page.mjs` (the cards'
  buttons), `i18n_checks.mjs` (no Latin words in the Russian lab texts; commands in `<code>` skipped, V52 (ad)).

**Site.** `site/check.py` on the new atlases (keys, budgets, files); `site/build.py`; CI's matrix unchanged.

---

## 8. Implementation plan

Batch **EX2** (`lfphys/PLAN.md` P17.5, continued). Every agent works in Docker (`--memory` ≤ 8g, `LFPHYS_NO_GPU=1`,
containers named `lf-ex2-<step>-*`), on its own private port (never 8479), stops containers by name (never `pkill -f`
or `pgrep -f`), puts no e-mail address or personal identifier in an external request, and keeps its notes in the
scratchpad so a cut-off loses nothing. The contract between F and the worlds is §5; a change to it is made here first.

| step | agent | owns (only these files) | done when |
|---|---|---|---|
| **F** framework (first) | 1 | `server/lfviz/{registry,headless}.py`, `server/lfviz/expr.py` (new), `server/lfviz/atlas_live.py`, `site/{atlas,check}.py`, `player/js/{explore,lab,demo,worksheet}.js`, `player/js/expr.js` (new), `player/assets/demo.css`, `tests/test_{headless,atlas,expr,site_registry,atlas_live}.py`, `tests/site_worlds/**`, `player/js/tests/**`, `tests/browser/demo_screens.mjs` (the toy), the framework's msgids in `visualizations/locales/` | the suites pass in Docker; the toy's screens work in EN and RU at 1280 and 390 px; `test_recorder.py` unchanged and passing |
| **W34**, **W35**, **W37** (in parallel, after F is merged) | 3 | each only its own `visualizations/u3x_*/**` (`viz.py`, `engine/`, `web/view.js`, `locales/`, `README.md`, `README.ru.md`, `tests/`) | the world's tests and browser checks; its recordings and atlases built with every check ✓ and within budget; the measured sizes replace this design's estimates |
| **I** integration (last) | the lead | `visualizations/RULES.md` (§7 glossary, §10), `STATUS.md` (V52 (l), (m), (n); a new V53 for EX2's open items), `lfphys/PLAN.md`, this design (notes after the implementation), `visualizations/README.md`, `README.ru.md`, the READMEs' catalogue (`site/readme.py`), `docs/images/` (`site/posters.mjs`), `tests/browser/{site_smoke,start_page,i18n_checks}.mjs` | the full suites green; the site built and checked locally; the browser checks in EN and RU |

Order: F; then W34, W35, W37 together; then I. The shared `visualizations/locales/*.json` are merged by a
load-merge-sorted-write right before writing; each world's own catalogues are its own.

Then four independent reviews, each by an agent that wrote none of the part; the author of a review never processes
it (`AGENTS.md` rule 6):

| review | scope |
|---|---|
| R2-E | the physics: u34's lab laws and GR numbers, u35's linearisations and counting statistics, u37's statistics and CHSH; the simulated verdicts reproduced on the built atlases |
| R2-F | the framework F1–F8: keys and determinism, the formula parser's safety and its Python–JS parity, compound controls on the live endpoint, the stop rules |
| R2-P | the screens in a browser, EN and RU, 1280 and 390 px: concealment in Lab work, captions against the layout, the phone layout, the CSV |
| R2-W | the three worlds as an instructor and a student would use them: the captions true to the screen, the worksheets, the answers, the sources and their quotations |

Each review is processed finding by finding in its `RESPONSE_*.md` by agents other than its author, then integrated.
The report to the owner (in Russian) gives the status per item ([useful] / [neutral] / [weakens] / [error in
earlier]), the measured sizes, and the links on the local server; the site is deployed only on the owner's go.

---

## 9. Risks and questions

**Questions for the owner** (the design takes the recommended answer; the owner may change it at the report):

1. **The checks' values in Lab work** (§5 F6). «How we know this is right» shows every computed check with its value;
   in Lab work it would show the verdicts only, because several values are the answers (u35's Brewster check names the
   index; u37's checks name E and S; u34's events name the advance). Recommended: verdicts only, in Lab work only;
   Explore keeps the values. The alternative, keeping the values and choosing set-ups no check reveals, is not possible
   for u35 and u37.
2. **Malus's law in u35.** It needs a new element of the bench, a rotatable analyser before the detectors, with its own
   check (a physics change of the world, not a screen). Recommended: not in EX2; recorded in STATUS as a proposal for
   the batch that extends the bench. The alternative: W35 adds it with a third lab part (about 0.2 MB, one more item
   for R2-E).

**Risks, decided here:**
- *Computational labs for u34.* No laboratory measures orbits near a black hole; the labs follow a textbook's exercises
  (*Exploring Black Holes*, ch. 10) and an astronomy laboratory (CLEA), and the worksheet says they are computational.
  Their errors are the instruments' divisions; the lesson that more precision needs the next order of the theory is
  real.
- *This design's linearisations of Fresnel's formulae* are derived here, not quoted; W35 tests them to 1e-12 against
  the engine and a 30-digit evaluation, R2-E reviews them, and the worksheet says «derived for this lab».
- *A law that fails by design* (u34 part 3's line through the origin): the verdict is «no verdict» with the reason
  (χ²/dof 14.9), and the step's hint names the next order; the browser test expects it.
- *The u34 zoom-whirl point* (168 kB) is over the 150 kB target: accepted with its reason.
- *The formula parser* is new code that runs in every lab: a grammar of its own, no `eval`, shared Python–JS fixtures,
  hostile inputs in the tests, and R2-F's review.
- *Concealment could hide a failure*: it does not; a ✗ stays visible, only the numbers are folded.
- *The CLEA manual* was checked in a third-party copy (Appendix B); the official file was not found online.
- *Determinism* holds on the same CPU type only (EX1, review R-F F8).

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
| u34 advance, ten orbits, 0.01° | 300–3 000 M | line0 18.947 ± 0.023, χ²/dof 14.9, Birge 3.86 (no verdict); Δφ·p/M: 18.846 ± 0.012 (z −0.31), slope 89.2 ± 9.5 (85.03, z 0.43); χ²/dof 0.22 |
| u37 correlation | a {0, 45}° × b 7, 1 000 pairs, 300 samples | quantum 1.0001 ± 0.0017 (scatter 0.0003); local 0.5008 ± 0.0114, coverage 94.7 % |
| u37 CHSH | Δ 7.5–82.5°, 4 000 pairs | quantum 0.9996 ± 0.0057 (96 %), S(22.5°) 2.83 ± 0.045 (18.6σ above 2); local 0.5003 ± 0.0085, S(22.5°) 1.417 ± 0.059 (9.9σ below 2) |

**A.4 Recordings**: §2.1, §3.1, §4.1 (sizes, CPU, events and probed frames at their played times).

## Appendix B. Sources checked for this design

Each file was downloaded into its own scratch folder (no e-mail or personal identifier in the requests), converted
with `pdftotext`, and every quotation above was found verbatim in the text (line breaks and the PDF's line numbers
removed).

| source | file | sha256 (first 16) | quotations |
|---|---|---|---|
| E. F. Taylor, J. A. Wheeler, E. Bertschinger, *Exploring Black Holes*, 2nd ed., ch. 10 «Advance of Mercury's Perihelion» (draft 2020-03-31) | `eftaylor.com/exploringblackholes/Ch10AdvanceOfMercurysPerihelion200331v1.pdf` | 73d57c95076952c7 | §10.6 (two sentences), eq. (23), Query 11 |
| CLEA, «The Revolution of the Moons of Jupiter», Student Manual v1.1.1, Gettysburg College | a third-party copy, `old.gml.cz/prof/benes/JupMoons/Jupit_sm.pdf` (the official file not found) | 6a9a7c8658442cfa | two sentences |
| Carnegie Mellon University, 33-353 «Intermediate Optics», Lab 1 «FRESNEL RELATIONS and SNELL’S LAW» (Fall 2010) | `cmu.edu/biolphys/smsl/teaching/IntermedOptics/IntOptics_data/lab manuals/Lab1 - Fresnel.pdf` | 2db1054b3a6b5856 | three sentences |
| Rutgers, «Fresnel Equations and Electromagnetic Boundary Conditions» | `physics.rutgers.edu/~eandrei/389/fresnel.pdf` | 7458ae60bf892c07 | one sentence |
| D. Dehlinger, M. W. Mitchell, Am. J. Phys. 70, 903 (2002) | `arxiv.org/pdf/quant-ph/0205171` | 205531334f0d5625 | three sentences; S = 2.307 ± 0.035 |
