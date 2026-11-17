# Review EX1-worlds (R-W): S03 and u32 as a teacher and a student use them

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it wrote none of the code under review) |
| Date | 2026-11-17 (batch EX1 of 2026-11-14, commit 507c059, tree clean) |
| Scope | `visualizations/s03_projectile/**` and `visualizations/u32_double_slit/**`: `viz.py` (screens, recordings, captions, lab steps, worksheet), `web/view.js`, `locales/`, `README.md` / `README.ru.md`, tests. The player's screens were used as a teacher (lesson and ФРП lab), a grade 9–10 student (the lab alone) and a university student (the double slit) would use them. |
| Not in scope | The atlas framework and the player's code as such (R-F, R-P), the engine's mechanics and the fit (R-E). Where a player defect shows on these two worlds, it is reported here with its place in the player, so that it can be deduplicated. |
| Environment | `lfphys-viz` image, CPU. Private server `lf-rvw-srv` on 127.0.0.1:8703 (`--memory=6g`, the repository mounted read-only, runs in scratch), with the repository's recordings and atlases (`site/plan.py`: all present). Own site build (`site/build.py --base /lfphys/` into scratch; `site/check.py`: 0 failures, 4 accepted warnings), served under `/lfphys/` inside the Playwright container's network namespace. Playwright 1.58.2 Chromium. EN and RU, 1280 × 860 and 390 × 844. |

The scripts are in `evidence/scripts/` (`t1`…`t16` browser, `recompute.py`, `u32_atlas.py`, `u32_story2.py`), with
short logs and cropped screenshots in `evidence/`.

## Summary

There are 18 findings: **3 errors**, **10 should-fix**, **5 nits**.

What works: the physics. Every number I recomputed in Docker against the engine agrees with the worlds, the
captions, the README and the teacher's notes, with one exception (F7a). The checks are listed below. The lab can be
done end to end on the public site in EN and RU: 17 + 13 + 8 set-ups, «Measure», the table, the plot, the fit and
«Check against the law». Each part agrees with its law:

| part | measured | law |
|---|---|---|
| 1 | k = 0.67687 ± 0.00065 m^½ | 0.6774 |
| 2 | slope 2.54901 ± 0.00050 m | 2.549 |
| 3 | θ* = 42.03 ± 0.18° | 41.9° (engine); 41.887° (hodograph, my run) |

The ФРП, AP, AQA and IB anchors are right, verified against the documents. Off-grid points are computed live on a
server. No console errors and no failed request appeared in any run, and nothing scrolls sideways at 390 px.

What does not yet answer the owner's complaint (unclear recordings, overloaded and non-interactive screens):
- **F3, error.** S03's Watch scales every world to fit. The earlier throw disappears, so «twice as far» and «four times
  higher» look the same on screen: only the axis numbers change. The story's comparisons are not visible.
- **F1, error.** In S03 Explore, pressing «▶ Launch» again on the same set-up draws a fan of straight lines across the
  scene. This is the most common action a student takes.
- **F2, error.** u32 shows |γ₁₂| with a bootstrap error that is wrong by up to ×50 either way. Examples:
  «1.055 ± 0.000» at 662 hits for 3 s of the story, and «1.005 ± 0.431» at 5160 hits in Explore. A university student
  reads the first as a 180σ violation of |γ| ≤ 1.
- **F5.** «Check against the law» ignores the axes the student plotted:
  - the vacuum (grey) ball's correct 45° is marked ✗ against the air optimum;
  - part 2's 45° maximum cannot be checked at all.
- **F6.** The stopwatch's reading goes nowhere: there is no column for it.
- **F7.** The worksheet:
  - one wrong teacher's answer;
  - 8 blank rows for 17 and 13 set-ups;
  - no grade-7 variant (it asks grade 7 for √h);
  - a page that prints a single line;
  - raw ids (Latin «FRP-OOO-2025-base» in the Russian text).
- **F8.** The school drawer lists PDG quark masses and Planck cosmology as "Physics of this world" for a thrown ball.
  It also gives away the chute speed the lab hides.
- **F9.** u32's «one slit … with no bands» contradicts its own expectation curve, which has the single slit's dark
  minima at ±32 mm.
- **F10.** At 390 px the view and the controls never share the screen. On a phone the manual stopwatch cannot be
  stopped while the ball is visible.
- **F13.** Russian:
  - English leaks: «m^½», «slope», «χ²/dof», «FRP-OOO-2025-base»;
  - calques: «ожидание запуска», «в замкнутом виде» for school, «экран начинается заново».

The answers to the brief's questions, in one place:

| question | answer |
|---|---|
| Essence on each screen | S03 Explore: yes. u32 Watch and Explore: yes. S03 Watch: only in numbers (F3). u32's top pane distorts geometry, and its explanation is lost at 390 px (F10). |
| Captions true to the screen | All S03 statements are true. F3 and F4 cover what the screen fails to show. u32: F9. |
| Misleading | F2, F3, F5, F8, F9. |
| Lab doable | Yes on a desktop. Weak points: F5, F6, F10. |
| Worksheets and answers | The answers are right except Q1 (F7a); the form needs work (F7). |
| Anchors | Right. |
| Russian and English | English: fine (British spelling). Russian: F13. |
| What a teacher would miss compared with PhET | See the last section. |

## Findings

### F1 (error): re-launching the same Explore set-up draws a fan of lines over the scene

- **Where:** S03 Explore, any point: «▶ Launch», wait for the landing, «▶ Launch» again. The cause is in the player:
  - `player/js/explore.js:223-224`: `pushTrace(c); E.cur = { ...c, launchedAt: E.clock }`. The trace and the new
    shot share one decoded world `pt.W`.
  - `player/js/record_core.js:158-230`: the feed state lives on `W`, not per view (`W.maxOn`, `W.scan`, `W.prefix`,
    `W.keys`, the messages' `on` marks).
  - So the trace's view and the screen's view rebuild each other's record every frame.
- **Evidence:** `evidence/f2_s03_relaunch_fan.jpg` (script `t3_relaunch.mjs`; log `{"traces":1,"same":true}`).
  - A straight line runs from the trace's landing point (23.9 m) to every computed sample of the new flight.
  - This happens with the strobe on and with it off.
  - It also appeared in `t2` after «air on» and two launches.
- **What is wrong:** launching the same throw again is the first thing a student does («again, slower»). The picture
  then shows a dense fan of lines that are not computed paths, which breaks rule 2 ("only what the run computed").
- **Fix:**
  - Keep the feed state per view: a `WeakMap(view → {maxOn, scan, prefix, nOn, keys})` in `record_core`.
  - Or make a re-launched trace use its own copy of the decoded world.
  - Test: two launches of one point; the trace's pixels equal those of a trace of a different point of the same path.

### F2 (error): u32's |γ₁₂| error is unreliable, from 30× too small to 50× too large

- **Where:**
  - the readout line of Watch and Explore (`u32_double_slit/web/view.js:636-649`);
  - the value comes from `viz.py:1202` `_coherence_err` → `lfphys/lfphys/tools/stats.py:75` `coherence_boot_err`
    (60 parametric-bootstrap refits).
- **Evidence:**
  - `evidence/u32_story_gamma.log` (decoded `story` recording). All 60 frames 361–420 (played 18–21 s, the caption
    «Ten times faster…») show |γ₁₂| = 1.05–1.08 with an error of 0.0003, at 575–1130 hits. Consecutive frames, about
    10 hits apart, jump by 0.01–0.02, 30–60× the stated error. Earlier frames show 1.018 ± 0.022 at 344 hits.
  - In the browser: «|γ₁₂| 1.055 ± 0.000» at 662 hits.
  - `evidence/u32_atlas_gamma.log` (all 48 Explore points):
    - most points end with ± 0.003–0.011 at 3700–5200 hits;
    - λ 500 nm, d 50 µm: a 40 µm gives **1.005 ± 0.431** at 5160 hits, a 10 µm gives 1.003 ± 0.198 at 4477;
    - λ 600, d 100, a 10 has 20 frames with ± 0.0005–0.0023 at 191–3810 hits.
  - `evidence/f5_u32_gamma_readout.jpg` (Explore on the server, λ 500, d 50, a 40, after the build-up).
  - The eraser recording ends with «1.020 ± 0.008» at 566 hits.
- **What is wrong:** the line is the quantitative statement a university student reads. «1.055 ± 0.000» (expectation
  1.000) says the sample violates |γ| ≤ 1 by ~180σ, while χ² says the sample agrees (p 0.22). «± 0.431» says nothing
  was measured. Both are artefacts of the error estimate. EX1 newly shows them on the public site's Watch and Explore.
- **Fix:**
  - Bootstrap from a model constrained to |γ| ≤ 1, so that μ ≥ 0 with no clipped bins.
  - Take a robust spread (the 16–84 % half-width) and require most refits to succeed.
  - Show «—» with a reason when it is unreliable.
  - Drop the √(n_then/n) rescaling across a regime change.
  - Test: over seeds, the stated error stays within ×2 of the scatter of |γ̂|, for the 48 Explore points and for the
    story at 200, 600 and 2000 hits.

### F3 (error): S03 Watch, the story's comparisons are not visible

- **Where:** S03 Watch, captions 3 and 4 (`s03_projectile/viz.py:494-513`). The view's box fits the current world
  (`web/view.js` `sceneBox`). Each `new_world` resets the view, and the earlier throw is gone.
- **Evidence:** `evidence/f1_s03_watch_three_worlds.jpg`, the three first worlds after their landings
  (`t16_landed.mjs`).
  - Measured on the 1280 px screenshots:
    - World 3 (h 5 m) is drawn pixel for pixel like world 1 (h 1.25 m). The table is 586 px high in both, and the
      landing is 475 px from the table's edge in both.
    - World 2 lands 762 px out, 1.6× world 1, not 2×, because its scale changed too.
    - Only the axis ticks tell the difference: steps of 0.2 m, 0.2 m and 1 m.
  - So «Four times higher: the flight lasts twice as long, and the range doubles» shows the same picture as world 1.
  - «Twice the sideways speed: the ball lands twice as far» shows a landing 1.6× as far on screen, with the table drawn
    lower.
- **What is wrong:** the owner's complaint, «по записи непонятно что за эффект показан», applies here exactly. The
  statements are true (recomputed: L = 1.0098, 2.0196, 4.0392 m; T = 0.5049, 0.5049, 1.0098 s). The viewer can see
  them only by comparing numbers across scenes that are no longer on screen.
- **Fix:**
  - Worlds 1–3 on one fixed box (h ≤ 5 m, x ≤ 4.1 m), declared by the recording or the Watch screen.
  - The earlier worlds' paths kept as faded traces with their «L = …» marks. The Watch screen can pass the story's
    earlier worlds to `view.setTraces`.
  - Test: world 2's landing is drawn twice as far from the table edge as world 1's, in pixels.

### F4 (should-fix): S03 Watch, slow motion unstated; caption timing; the caption hides the dropped ball's landing

- **Where:** S03 Watch (`player/js/watch.js:117`, the time label; the recording's speed 0.1 and 0.5).
- **Evidence:** `t1_s03_watch.mjs` logs and `evidence/f4_s03_watch_caption_landing.jpg`.
  - The time label reads «6.50 s / 39.95 s» while the view says «T = 0.505 s». Nothing says «×0.1». The side box says
    only «40 s at 20 frames per second».
  - Caption 2 («… At every moment both balls are at the same height») arrives at played 4 s = world 0.40 s, 0.1 s
    before the landing.
  - At 1280 px the caption box covers the dropped ball's landing at x = 0: the event that captions 2 and 3 compare.
- **What is wrong:**
  - A student sees a 1.25 m fall lasting 5 s and reads «T = 0.505 s» beside it.
  - The statement about every moment comes when the balls are almost down.
  - STATUS V52 (d) records only the axis numbers; this is worse, because the compared event is hidden.
- **Fix:**
  - Show the world time and the factor: «world 0.42 s · slow motion ×0.1».
  - Move caption 2 to 0.5–1 s, or give it a `hold`.
  - V52 (d)'s fix: a margin for the strip.

### F5 (should-fix): «Check against the law» ignores the axes and the column plotted

- **Where:** `player/js/lab.js:268-280` (`checkLaw` takes `law.quantity` of whatever is plotted); S03 `STEPS` (one law
  per step).
- **Evidence:** `evidence/lab_law_axes_en.log` and `_ru.log` (`t5_labaxes.mjs`, all set-ups measured).
  - **Part 3, y = «L in vacuum, m».** The parabola gives x* = **44.98 ± 0.19°**. The check reports «θ* of the largest
    range = 44.98 ± 0.19 ° — law: 41.9 ° … ✗ does not agree». The grey ball's correct 45° is judged against the air
    optimum, and the hint («compare with 45° for the grey ball») contradicts the verdict.
  - **Part 2, x = θ, parabola.** It gives **x* = 45.00 ± 0.14°**, the result that README §1 and question 5 name.
    «Check» answers «This fit gives no “slope”: choose the step's fit». In RU this reads «Эта аппроксимация не даёт
    «slope»».
  - **Part 1, x = h.** The verdict is labelled «k = L / √h = 0.797 ± 0.035 m^½».
- **What is wrong:** the check decides on the fit's numbers alone, not on what was plotted. A student who studies the
  grey ball is told he is wrong. Part 2's main result, «the maximum is at 45°», cannot be checked.
- **Fix:**
  - A law names its `x`, `y` and `fit`. A step may have several laws:
    - part 2: slope of L(sin 2θ), and the vertex of L(θ) = 45°;
    - part 3: L → θ* in air, L_vac → 45°.
  - For other axes, refuse with the reason («the law is about L against √h»).
  - Translate the quantity's name.

### F6 (should-fix): Lab part 1, the stopwatch measures into nothing

- **Where:** `s03_projectile/viz.py:376-379`. The part's instruments are ruler, tape and stopwatch; the columns are h,
  L and √h only.
- **Evidence:** `t4_lab.mjs`. The CSV header is `"h, m","σ h, m","L, m","σ L, m","√h, m^½","σ √h, m^½"`. The stopwatch
  shows «0.73 s» and the row keeps nothing of it. «slow» is disabled for the whole part because a manual stopwatch is
  present (`lab.js:115`).
- **What is wrong:** worksheet question 1 asks why a hand stopwatch fails. The student can time the flight but can
  neither record nor compare the times (T measured against √(2h/g)). The part also loses slow motion for a 0.2–0.45 s
  flight, for an instrument with no use.
- **Fix:**
  - Add a column «T, s» from the stopwatch, and a derived «√(2h/g)» or a plot T against √h. The scatter then shows the
    reaction error.
  - Or drop the stopwatch from the part and keep it as a question.

### F7 (should-fix): the worksheet, one wrong answer and gaps a teacher will hit

- **Where:** `player/js/worksheet.js:66, 68, 96`; `s03_projectile/viz.py:416-473`.
- **Evidence:** `t6_ws.mjs` (text, PDFs, `evidence/f9_ws_ru_page4.png`); `evidence/recompute.log`.
  - **(a) Wrong answer.** Q1 says the hand scatter of 0.1 s is «a third or more of the whole flight». The flights last
    0.2020–0.4519 s (recomputed), so 0.1 s is **22–50 %**. For h > 0.44 m (9 of 17 heights) it is less than a third.
    Say «from a fifth to a half».
  - **(b) Too few rows.** The blank tables have 8 rows (`length: 8`); parts 1 and 2 have 17 and 13 set-ups. Use the
    step's number of grid values.
  - **(c) Part 3.** «Plot L, m against θ, ° and draw the best line through the points»: part 3 fits a parabola.
  - **(d) No grade-7 variant.** README §1 says grade 7 checks «the higher, the farther» on L(h). The worksheet asks
    every student to plot L(√h) and find k. Square roots come in grade-8 algebra, and the ФРП grade-7 item is a
    qualitative hypothesis test.
  - **(e) Printing.**
    - Part 1's table breaks across pages 1–2 (EN and RU).
    - RU page 4 holds only the last line of part 2's licence notice («изменённые копии распространяйте под той же
      лицензией»): RU prints 8 pages, EN 7.
    - The design wants one A4 page per part.
  - **(f) Missing lines.** There are no «Conclusion» («Вывод») lines and no name, class and date lines. A Russian lab
    report ends with «Вывод».
  - **(g) Raw ids and English text.**
    - The heading shows «FRP-OOO-2025-base, 7 класс» in the Russian text (also EN «FRP-SOO-2025-base, grade 10»).
    - EN marks the translation twice: «… (our translation) (translated; the programme's own wording: «…»)».
    - EN «find slope of L against sin 2θ» needs «the slope».
- **Fix:** as in each item. The system id needs a display name per language («ФРП ООО, базовый уровень, 2025» /
  «Russian federal programme, basic level, grades 7–9»).

### F8 (should-fix): the school drawer, quark masses for a thrown ball, and the hidden v₀ given away

- **Where:**
  - `s03_projectile/viz.py:155-159`: `engine_modules` returns `"core.data"`, whose catalogue entry
    (`lfphys/lfphys/core/data.py:19`) lists every data set;
  - `player/js/demo.js:275`: the events as «349.937 ms …».
- **Evidence:** `evidence/drawer_s03_lab.txt` (`t11_drawer.mjs`, EN and RU).
  - On every S03 screen, "Physics of this world" opens with «Measured and reference values (with sources): α_s(M_Z),
    M_Z, the heavy quark masses, the charmonium and bottomonium masses (PDG 2024); the orbital elements of Mercury …
    the Planck 2018 cosmological parameters …».
  - In Lab work part 1 the events show «landing: range 0.5244 m, flight time 0.3499 s», so v₀ = L/T = 1.4987 m/s.
- **What is wrong:**
  - For a grade 9–10 student this is noise of exactly the kind the owner calls overloaded, and it is false for this
    world: it uses only the air's data.
  - The teacher's note says the chute's speed «is not told» and is found from the slope. The drawer tells it, on the
    public site too.
  - School times read «349.937 ms», though the design says «0.45 s», never «451.6 ms».
- **Fix:**
  - Give the air's data its own catalogue entry (or name the data set used).
  - In Lab work, leave the measurables' values out of the events, or say in the teacher's notes that they are there.
  - Show school times in seconds.

### F9 (should-fix): u32 story, a single slit «with no bands», and «thousands» at 204 hits

- **Where:** `u32_double_slit/viz.py:1590` (26 s) and `:1585` (16 s).
- **Evidence:**
  - `evidence/f6_u32_single_slit.jpg` (at 28.5 s): the run's own expectation for one slit has its dark minima at
    ±λL/a = ±31.6 mm, with side lobes beyond, on the ±50 mm screen.
  - Hits at the captions (`t7_u32_watch.mjs`): 204 at 16 s, 1320 at 22 s, about 2000 at 26 s.
- **What is wrong:** for a university course, «the spread of a single slit, with no bands» is wrong. Single-slit
  diffraction has bands, wider and weaker, and the orange curve on screen shows them. «Thousands of hits» is said at
  204.
- **Fix:**
  - «Slit 2 is closed: the narrow two-slit fringes vanish; what remains is one slit's broad diffraction maximum (its
    first dark minima at ±32 mm).»
  - «Ten times faster: hundreds, then about two thousand hits …».

### F10 (should-fix): at 390 px the phenomenon and its controls never share the screen

- **Where:** the screens' phone layout with S03 and u32 (player CSS). V52 (b) covers only the height of u32's top pane.
- **Evidence:**
  - `evidence/f8_s03_lab_390.jpg`, `t15_lab390.mjs`: in Lab part 1 with «Измерить» on screen, the view's canvas is at
    y = −458…−190.
    - The «⏱ Стоп» of the manual stopwatch is ~555 px below the canvas's bottom. With the 268 px canvas and the
      100 px header, the two need ≥ 960 px on an 844 px screen.
    - The student cannot watch the ball and stop the watch.
  - `t3_relaunch.mjs`, S03 Explore at 390 px scrolled to «Сопротивление воздуха» and «Запуск»: canvas at
    y = −102…166 under a ~100 px header. The flight runs off screen.
  - u32 Explore: only «Длина волны» fits under the view, and d and a need scrolling.
  - `evidence/f7_u32_390_caption_cut.jpg`, `t9_capclip.mjs`: u32's caption 4 (RU) runs 30 px under the sticky bar,
    its top under the histogram (EN 7 px; RU caption 6, 7 px).
  - At 390 px the u32 note loses the sentence «The distance is on a log scale and the width is rescaled at each
    distance, so the beams seem to bend», while the distorted map stays. Compare `t10` at 390 with 1280.
- **What is wrong:** a phone is the site's main audience (rule 16). Exploring means changing a control and watching
  the effect, and here the two exclude each other. The u32 map without its explanation looks like curved photon
  paths.
- **Fix:**
  - A sticky view, or the controls in a sheet over the lower part of the view.
  - The stopwatch's Stop in the sticky bar.
  - The caption in its own space above the bar.
  - The distortion sentence kept, folded but present.
  - Test: at 390 × 844 the canvas and each control are visible together.

### F11 (should-fix): S03 Explore, trace labels unreadable

- **Where:** `s03_projectile/web/view.js:228`. The label is `valuesText` of all controls («Launch height 10 m, Launch
  speed 10 m/s, Launch angle 0°, Air resistance off»), drawn 20 px under the landing mark.
- **Evidence:** `evidence/f3_s03_trace_labels.jpg` (`t13_edges.mjs`: three horizontal throws from 10 m). The labels
  overprint one another and the axis numbers, and run off the right edge (`t2`: «Launch he…»).
- **What is wrong:** the design's "small label of its values" is what lets a student compare traces. As drawn, no
  trace can be identified.
- **Fix:**
  - Label only what differs from the current point («v₀ 10»), above the mark, with collision avoidance.
  - Or a legend in the side column.

### F12 (should-fix): S03 Explore, which ball flies is not stated

- **Where:** the Explore screen (preset `field`: the 67 mm, 58 g light ball).
- **Evidence:** `t2_s03_explore.mjs`, the side column's whole text: heights, speeds, angles, «Air resistance», «Show»,
  readouts, «Clear traces». No line names the ball; the view draws it with no label.
- **What is wrong:** the air's effect depends on the ball. Recomputed: for this light ball at 25 m/s from the floor θ*
  is 40.7°; for the steel ball at 5 m/s θ* stays at 45.0°. A teacher asking «why does the air matter so much here?»
  has nothing on screen to point at.
- **Fix:** a line under the controls («A light ball, 67 mm, 58 g: the size of a tennis ball»). A ball control would
  double the atlas (5.7 → 11.4 MB), so name the ball at least.

### F13 (should-fix): Russian, English leaking in, and calques

- **Where:**
  - `player/js/lab.js:272-276`: `law.quantity` and the raw `law.unit` / `ref.unit` are not translated;
  - `u32_double_slit/web/view.js:642, 649`; `worksheet.js:96`; `s03_projectile/locales/ru.json`;
    `u32_double_slit/locales/ru.json`; `README.ru.md`.
- **Evidence:** `evidence/lab_law_axes_ru.log`; `t7`, `t10` logs.
- **English inside the Russian UI:**
  - «закон: 0,6774 **m^½**», «2,549 **m**» (the rest of the UI says «м»);
  - «не даёт «**slope**»»;
  - «χ²/**dof**» (u32 readout; teacher's note «при χ²/dof больше 1»);
  - «**FRP-OOO-2025-base**» (F7g).
- **Calques and unnatural phrases:**
  - «(**ожидание запуска** 1,000)» means "waiting for the launch"; say «(расчёт: 1,000)» or «(ожидается 1,000)».
  - «в **замкнутом виде** k = v₀·√(2/g)» at school; say «по формуле».
  - «экран **начинается заново**»; say «счёт на экране начинается заново».
  - «Попаданий **в этом отрезке**»; say «на этом этапе».
  - «движок заранее рассчитал каждую **установку**» (after «на рассчитанной установке»).
  - «погрешность — **заявленная**».
- **One term for one thing:**
  - «аппроксимация» (UI) and «подгонка» (teacher's note);
  - «затравка» (UI; u32 README.ru lines 287–289) and «зерно» (u32 README.ru lines 48, 54);
  - part 3's light ball is «мяч» and its grey twin «шарик».
- **Fix:** translate units and quantity names through `T`, then the replacements above. A check in `i18n_checks.mjs`
  for Latin words in RU texts of the lab's verdict and the readout lines.

### F14 (nit): u32 «shutter 0°»

`u32_double_slit/web/view.js:326` draws «{elem} {a:g}°» for every element. The closed slit reads «shutter 0°» on the
map and «Set-up: slit 2: shutter 0°» («заслонка 0°») in the note. A shutter has no angle. Leave out the angle for
`block`.

### F15 (nit): S03 energy bars, labels on the next bar

`s03_projectile/web/view.js:244`: bars at 28 + 22j with 12 px height, labels at y + 22. Each label («kinetic energy
2.75») is printed over the next bar's outline (`evidence/f10_s03_energy_labels.jpg`). Use a row height of ~30 px, or
put the label to the right of the bar.

### F16 (nit): S03 launcher barrel under the floor

`s03_projectile/web/view.js:169` draws the barrel backwards from the launch point. From the floor (h = 0: Explore,
Watch world 4, Lab part 2) it sticks into the ground, and at 90° straight down (`evidence/f11_s03_barrel.jpg`). Draw
the barrel above the floor (breech at the floor, muzzle at the launch point).

### F17 (nit): number formats

- S03 readouts: «Range 23.9 m» (23.90) next to «18.51 m»: `num(…, 4)` drops trailing zeros.
- u32 check table (standard): «170.583333333», «0.00039459470394», «6,000.00119143 µm».
- EN «± 1,043» for a parabola's x* error (`t4` part 2; also a meaningless offer there, see F5).

Fix: fixed decimals for readouts, 4 significant digits in the check table.

### F18 (nit): READMEs against the screen and the numbers

- u32 README (EN §"The screens", RU §«Экраны»): «the time bar is the number of hits so far». The bar shows world
  seconds («5.25 s / 5.25 s»).
- S03 README §4: buoyancy «0.01 for the light ball». ρ_air/ρ_ball = 1.204/368.3 = **0.0033** (`recompute.log`).

## Checked and found fine

- S03 physics recomputed in Docker against the engine (`recompute.log`):
  - k_ref = 0.67740 m^½; air effect in part 1 at most 0.080 % (README 0.08 %);
  - part 2 in air 0.497 % lower slope (note: «about 0.5 %»); part 2 vacuum parabola vertex 45.000°;
  - θ* in air 41.887° by scan and by hodograph (world: 41.9 at 0.1°); the grey ball's parabola over 25–60° gives 44.97°;
  - steel at 5 m/s: θ* 45.0° («the shift is tiny»);
  - Watch L and T as above;
  - 25 m/s from the floor: 63.732 m in vacuum, 36.542 m at 40° and 36.234 m at 45° in air;
  - k = 0.017201 and 0.002702 1/m; Re = 2.0·10⁵ at 45 m/s; the steel ball's 32.9 g.
- My own fit of the virtual readings (1 mm, 1 cm, effective variance) gives the same 0.67687 ± 0.00065 as `fit.js`.
- S03 captions' statements and u32's young / eraser / Aharonov–Bohm captions are physically right (½ h/e → π shift,
  dark centre).
- Teacher's answers Q2–Q7 are right, including v₀ = k·√(g/2) = 1.5000 m/s.
- Anchors, checked against the documents:
  - ФРП ООО 2025, p. 6, grade 7, «Лабораторные работы и опыты»; ФРП СОО 2025, p. 7 (demonstration) and p. 8 (lab):
    my own downloads from edsoo.ru, sha256 identical to step S's;
  - AQA 7408 3.4.1.4, both quotations (the v1.3 file I got; v1.4 per step S's copy);
  - AP Physics 1 CED (Fall 2024), Topic 1.5, 1.5.B.2, and «air resistance is assumed to be negligible»;
  - IB A.1 «the qualitative effect of fluid resistance…» (step S's school-hosted copy).
- Refusals: h 0 with θ 0 gives a clear reason, ▶ is disabled with that reason, in EN and RU. Part 1 «Measure» before
  the landing says what is missing.
- Server mode: an off-grid S03 angle (42°) is computed live in 3.6 s and marked live. «▶ Compute live» opens the full
  player with the screen's set-up.
- Site under `/lfphys/`: every screen of both worlds opened. No console error and no failed request in any run;
  `scrollWidth` ≤ 390 everywhere; the worksheet works on the site and on the server.
- English user texts use British spelling («grey», «metre», «centimetre», «programme», «analyser», «polariser»).
  README labels match the UI labels in EN and RU («Сверить с законом», «▶ Запуск», «Убрать следы», «Почему этому
  можно верить», …).
- u32 Explore: fringe-period check 6000.0012 µm against λL/d = 6000 µm; 3713–5196 hits per point, as README says;
  χ²/dof 0.8–1.1.
- Tests: `test_s03_physics.py` and `test_u32_screens.py` pass (33 tests).

## What a teacher would miss compared with a good PhET-style simulation (concrete; no copying)

**S03**
1. **A probe on the path.** Click a point or a strobe dot to read t, x, y, v_x, v_y. «x grows evenly, y as t²» is
   the quantitative core of the independence of motions, and Explore gives only L, T and H.
2. **The second ball in Explore.** A «drop a ball at the same moment» toggle would let students test the topic's key
   fact instead of only watching it.
3. **The ball as a choice** (steel and light), so the air's effect can be compared by mass and size (F12).
4. **A movable tape and a target.** The student lays the tape and reads it (today «Measure» reads to 1 mm by itself),
   and a «hit the target at 15 m» task with v₀ and θ.
5. **Live graphs of the shown shot.** x(t), y(t), v_x(t), v_y(t) at school level. The live player has them under
   «Instruments», Explore has none.
6. **Visible step buttons.** «◀ 0.1 s ▶» for pausing at a strobe instant; now only the ← → keys.

**u32**
1. **A ruler or cursor on the screen axis**, and the distance to the screen (1 m) on the Explore screen. The student
   could then measure the fringe spacing and check Δy = λL/d (V52 (n) records only the missing readout).
2. **Explore of the quantum lesson.** The which-path detector on and off, with its strength θ; one slit closed; the
   particle (electrons with energy → λ). Today Explore varies only λ, d and a, classical wave optics, so the story's
   main point, that marking the path removes the fringes, can be watched but not explored.
3. **A finer λ** (4 values now) and an intensity view next to single hits.
4. **The eraser as a sequence.** Marks without the analyser (no bands), then +45° (bands), then −45°
   (anti-bands): today the recording shows only the erased state.
