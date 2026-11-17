# Response to review R-W (EX1-worlds), part "worlds": S03 and u32 in their own files

**Responder:** QW, the processing agent for the worlds `s03_projectile` and `u32_double_slit` (containers `lf-qw-*`,
private port 8707). It wrote neither the review nor the code under review. **Date:** 2026-11-17.

**Scope.** The findings of this review that lie in the two worlds' files, under the integrator's decisions
(`PROCESS_BRIEF.md`): F2 (u32's `_coherence_err`, D9 world side), F3 and F4 (D8), F6 (the column, the integrator's
decision of 17 November), F7 (the content: the answers, a grade-7 variant), F8 (D10 world side: `engine_modules`, the
events), F9, F10 (the worlds' parts), F11, F12, F13 (the worlds' texts, EN and RU) and the nits F14–F18 as far as they
are the worlds'. The player's parts are QP's (`RESPONSE_player.md`: F1, F5, F7's layout, F10, the player's msgids), the
engine's QE's (`RESPONSE_engine.md`: F2's `stats.coherence_boot`, F8's `core.data:<set>`), the framework's QF's.

**Counts:** 16 findings with a world part: 14 fixed, 2 partly (F10: the worlds' parts only; F17: the S03 view's
numbers, the readouts and the check table are the player's). None rejected.

**Environment.** Image `lfphys-viz` (Python 3.11), CPU (`LFPHYS_NO_GPU=1`), containers `lf-qw-*` with `--memory` ≤ 10g,
the repository mounted read-only for the tests and the builds. The recordings and atlases of both worlds were rebuilt
by `site/record.py --world … --out <scratch>` and served by a private server (`server/serve.py`, 127.0.0.1:8707,
`LFVIZ_RECORDINGS` = that folder). Playwright 1.58.2 Chromium, EN and RU, 1280 × 860 and 390 × 844; screenshots and
logs in the agent's notes, outside the repository.

| # | finding | outcome | where | test |
|---|---|---|---|---|
| F2 | u32's \|γ₁₂\| error unreliable (×30 too small to ×50 too large) | **fixed** (D9, world side; the estimator is QE's `stats.coherence_boot`) [error in earlier]. `_coherence_err` calls `coherence_boot` and returns (err, why); the frame carries `err`, `err_why` and `min_hits`. The `√(n_then/n)` rescaling is dropped (the error does not scale as 1/√n near \|γ\| = 1), and so is the throttle of 20 frames, which let a fast build-up show an error computed at a much smaller count: the error is recomputed whenever the count has grown by 10 % (and while it is below the threshold, where the call is cheap); in between the value is shown as computed. The count alone decides, so a rebuilt world shows the same errors. The readout shows \|γ₁₂\| with its error only when there is one; otherwise «\|γ₁₂\| —» with «from 300 hits on» (below `stats.COH_BOOT_MIN_HITS`) or the reason. The error is printed to 2 significant digits («± 0.0003» could no longer read «± 0.000») | `u32_double_slit/viz.py` (`_coherence_err`, `frame`), `web/view.js` (`drawReadouts`), `locales/*.json`, READMEs | `test_u32_screens.py::test_the_coherence_error_is_the_scatter_of_the_fitted_coherence_and_absent_below_its_hit_count` (Poisson histograms from the run's own expectation at 200, 600, 2000 hits: None with a reason at 200; stated/scatter within ×2), `::test_the_coherence_error_is_kept_unchanged_between_its_recomputations`; `test_u32_physics.py::test_coherence_error_is_calibrated_at_full_coherence` («—» with the reason at N = 100; ×2 at N = 300 and 1000). Measured ratios below |
| F3 | S03 Watch: the story's comparisons are not visible | **fixed** (D8). The view takes Watch's `setStory({worlds, w})` (QP's hook) and keeps one scene box for the whole recording, the union of its worlds' computed `scene.box`; the earlier worlds' throws stay as faded paths with their landing marks and «L = … m», read from the recording's own messages. The story is split so that one box stays readable: «independence» (worlds 1–3, from a table, h ≤ 5 m, L ≤ 4.04 m, 30 s) and «air» (the light ball, a 40 m scale, 9 s) under «More recordings». On the 1280 px screenshot of world 3 the landings lie about 95, 190 and 382 px from the launch point (1 : 2.0 : 4.0), and world 3's table is four times as high as the earlier launch points. On a phone the earlier throws' ranges go into one line under the ball's name («earlier throws: L = 1.01 m; L = 2.02 m»), where three labels would not fit between the marks | `s03_projectile/web/view.js` (`setStory`, `throwOf`, `drawStory`, `sceneBox`), `viz.py` (`recordings`, `screens`) | `test_s03_physics.py::test_the_watch_story_says_what_the_run_computes` (three throws within one box; each flight ends before the next world; the air recording's statements); browser: Watch EN/RU at 1280/390 |
| F4 | S03 Watch: slow motion unstated; caption timing; the caption hides a landing | **fixed** (D8). The playback factor is stated by QP's time label («world 0.70 s · slow motion ×10»). Caption 2 («… At every moment both balls are at the same height.») now comes at 1 s played (world 0.1 s, the landing at 0.505 s), and caption 1 holds the start 2.5 s so it is read before the balls move; captions 3 and 4 come with their worlds. On a wide screen, where Watch lays its caption over the stage, the view keeps a band of fixed height under the floor (the caption's bottom offset, its padding, two lines of its text, three on a narrower stage, and the floor's numbers), so the scale does not change from caption to caption and no landing is covered; on a phone the caption has its own place and no band is kept | `s03_projectile/viz.py`, `web/view.js` (`captionRoom`) | `::test_the_watch_story_says_what_the_run_computes` (caption 2 before a quarter of the flight; caption 1 held); browser |
| F6 | lab part 1: the stopwatch measures into nothing | **fixed** (integrator's decision): part 1 has the column «T, s» from the stopwatch, with no law; the default plot and the laws are unchanged. A new worksheet question asks why the hand-timed T barely helps (0.1 s scatter against 0.2–0.45 s flights and 0.01–0.02 s between neighbouring heights; 10 runs averaged give about 0.03 s) and how the time could still be measured. «slow» stays refused by the manual stopwatch (QP's) | `s03_projectile/viz.py` (`STEPS[0].columns`, `WORKSHEET`), `locales/ru.json`, READMEs | `::test_the_worksheets_numbers_are_the_engines` (the answer's numbers; the column list) |
| F7 | the worksheet: a wrong answer and gaps | **fixed** (content; the layout — rows per set-up, one page per part, «Conclusion» and name lines, part 3's «best line» wording — is QP's). (a) Q1: «… scatters by about 0.1 s: from a fifth to a half of the whole flight» (0.1 s against 0.2020–0.4516 s). (d) A grade-7 variant in QP's shape, `WORKSHEET["variants"]`: part 1 only, L against h with no fitted curve, its own goal (no √h; «the air is switched off»), four questions of its own (the hypothesis by the table and the graph's shape: four times higher, 0.25 → 1.00 m, the range only doubles, 0.339 → 0.677 m); the teacher's note says why grade 7 does not plot √h (square roots come in grade 8 algebra). (g) The FRP entries carry `programme`, a display name per language («ФРП ООО, базовый уровень, 2025»), for QP to print instead of the raw id; the names no longer carry «(our translation)»; «find the slope of L against sin 2θ» | `s03_projectile/viz.py` (`WORKSHEET`), `locales/ru.json` | `::test_the_worksheets_numbers_are_the_engines` |
| F8 | the school drawer: quark masses for a thrown ball; the hidden v₀ given away | **fixed** (D10, world side). `engine_modules()` names `core.data:air` (QE's new data-set entry): «Physics of this world» lists the U.S. Standard Atmosphere 1976 only. The events' texts carry no measured value: «the ball lands», «the ball at the top of its path», «the dropped ball lands», «the grey ball (vacuum) lands»; the values stay the events' data, the readouts and the checks. What remains is the player's: the drawer prints each event's own time, and the landing's time is T; the integrator passed that to QP | `s03_projectile/viz.py` (`engine_modules`, `_landing_main`, `_landing_other`, `advance`) | `::test_the_engine_modules_and_the_events_reveal_no_lab_value` |
| F9 | u32 story: a single slit «with no bands»; «thousands» at 204 hits | **fixed**. 16 s: «Ten times faster: hundreds of hits, then about two thousand. …». 26 s: «Slit 2 is closed, and the count starts again. The two-slit fringes are gone: one slit gives a broad diffraction maximum, its first dark minima at ±31.6 mm.» (kept short: a long caption is cut at 390 px until QP's D12 lands) The number is λL/a computed from the story's preset (Fraunhofer: a²/(λL) = 6·10⁻⁴) | `u32_double_slit/viz.py` (`STORY_CAPTIONS`, `_story_single_slit_minimum_mm`), `locales/ru.json`, READMEs | `test_u32_screens.py::test_the_story_s_hit_counts_and_the_single_slit_minima_are_the_run_s` (the run's counts at 17 s and 26 s; the minima of the run's own expectation for that stage within one bin of ±31.6 mm) |
| F10 | at 390 px the view and its controls never share the screen | **partly** (the worlds' parts; the layout, the sticky bar and the stopwatch's Stop are QP's, D12). u32: the distortion sentence is kept on narrow screens in a short form («Log scale of the distance, widths rescaled: the beams only seem to bend.»). S03 Watch on a phone folds its overlays under «Show», so the scene keeps the height | `u32_double_slit/web/view.js`, `s03_projectile/web/view.js` | browser at 390 px |
| F11 | S03 Explore: trace labels unreadable | **fixed** (the drawing; the text, only the values that differ, is QP's in `explore.js`): above the landing mark, right-aligned at the right edge, inside the canvas, moved clear of the other labels | `s03_projectile/web/view.js` (`placeLabel`) | browser |
| F12 | S03 Explore: which ball flies is not stated | **fixed**: the view names the ball in its top left corner on every screen («light ball, 67 mm, 58 g (the size of a tennis ball)»; where that does not fit, «ball 67 mm, 58 g») | `s03_projectile/web/view.js` | browser |
| F13 | Russian: English leaking in, calques, one term per thing | **fixed** (the worlds' texts; `lab.js`, `worksheet.js` and the framework catalogue are QP's). Units of the laws are T (RU «м^½», «м»); u32's «χ²/dof» is `t("χ²/dof")`, RU «приведённый χ²»; «(ожидание запуска …)» → «(расчёт запуска: …)»; «экран начинается заново» → «счёт начат заново»; S03's school texts say «по формуле(ам)» instead of «в замкнутом виде»; «подгонка» → «аппроксимация» in S03's note and README; «зерно» → «затравка» in u32's README; part 3's grey twin of the light ball is «серый мяч» everywhere (was «серый шарик»); u32's «segment» is «этап» throughout (catalogue and README), which gives the readout «Попаданий на этом этапе:». The raw FRP id: see F7(g). Left to QP: «каждую установку», «погрешность — заявленная» and «зерно» in the framework's catalogue | `*/locales/ru.json`, `u32_double_slit/web/view.js`, READMEs | `tests/test_i18n.py` |
| F14 | u32 «shutter 0°» | **fixed**: a shutter is drawn and described without an angle («slit 2: shutter») | `u32_double_slit/engine/experiment.py` (`Apparatus.describe`), `web/view.js` | `test_u32_screens.py` (the story's segments) |
| F15 | S03 energy bars: labels on the next bar | **fixed**: rows of 34 px, each label under its own bar | `s03_projectile/web/view.js` | browser |
| F16 | S03 launcher barrel under the floor | **fixed**: when the barrel drawn back from the launch point would go below the floor, it lies forward on a mount above the floor | `s03_projectile/web/view.js` | browser |
| F17 | number formats | **partly** (the view's own labels): S03's «L = …» to the centimetre and «T = …» to the millisecond with fixed decimals («L = 23.90 m, T = 2.254 s»), «H = …» to the centimetre. The readouts (`explore.js`) and the check table (`demo.js`) are QP's | `s03_projectile/web/view.js` | browser |
| F18 | READMEs against the screen and the numbers | **fixed**: u32's time bar is the world's time of the build-up (the hits are in the readout line), EN and RU; S03's buoyancy ratio 3.3·10⁻³ (and 1.5·10⁻⁴ for steel) | READMEs | — |

## F2: measured on the worlds

- **The story as recorded** (the review's evidence was «1.055 ± 0.000» at 662 hits and ± 0.0003 at 575–1130): the
  re-recorded story reads «|γ₁₂| — from 300 hits on» at 179 hits (15 s), «1.007 ± 0.035» at 569 hits (18 s),
  «1.003 ± 0.022» at 1130 (21 s), «1.000 ± 0.012» at 2065 (26 s), «1.009 ± 0.011» at 2230 (59 s); Explore's default
  point «0.992 ± 0.0072» at 4732 hits (browser log, EN and RU).
- **Stated error against the real scatter**, the world's own path (`Simulation._coherence`, `_coherence_err`) on 60
  Poisson histograms drawn from the run's expectation per row (`evidence/processing_d9/d9_ratio.py`,
  `d9_ratio_final.out`):

  | Explore point | 300 hits | 600 | 2000 | 5000 |
  |---|---|---|---|---|
  | λ 600, d 100, a 20 (default) | 0.97 (31 of 60 below 300: «—») | 0.99 | 0.95 | 0.99 |
  | λ 500, d 50, a 40 (the review's «± 0.431») | 0.98 (25 «—») | 0.81 | 1.08 | 1.16 |
  | λ 600, d 100, a 10 | 0.88 (34 «—») | 1.01 | 1.04 | 1.05 |
  | λ 400, d 300, a 10 | 1.21 (26 «—») | 0.88 | 1.05 | 0.86 |

  (median stated error / standard deviation of the fitted |γ₁₂|; the true |γ| is 1 at every point.)
- **Cost.** Recomputing on every 10 % growth with QE's 100 refits (doubled near |γ| = 1) raised the Explore atlas's
  build from 53 s to 131 s of CPU (48 points); the story's recording stayed at 7 s.

## Sizes (re-measured, Docker, CPU, `site/record.py --world …`)

Built by `site/record.py --world s03_projectile --world u32_double_slit --out <scratch>` on 2026-11-17 (2 min 13 s wall):

| world | item | size (gzip) | CPU | before (2026-11-14) |
|---|---|---|---|---|
| S03 | Watch `independence` (30 s × 20 fps, 600 frames) | 0.03 MB | 0.3 s | 0.05 MB (40 s, four worlds) |
| S03 | Watch `air` (9 s × 20 fps, 180 frames) | 0.02 MB | 0.1 s | — (was world 4 of the story) |
| S03 | Explore (940 points + 10 refused) | 5.85 MB, largest point 12.9 kB | 11 s | 5.70 MB |
| S03 | Lab parts 1–3 | 0.04 + 0.05 + 0.09 MB | 0.4 s | 0.05 + 0.05 + 0.09 MB |
| S03 | the world | 6.11 MB (target 12) | 23–32 s wall | 5.94 MB |
| u32 | Watch `story` / `young` / `eraser` / `aharonov_bohm` | 0.60 / 0.73 / 0.64 / 0.67 MB | 7 / 4 / 2 / 11 s | 0.61 / 0.74 / 0.65 / 0.68 MB |
| u32 | Explore (48 points) | 5.50 MB, largest point 132.7 kB | 88–131 s | 5.50 MB, 45–57 s |
| u32 | the world | 8.15 MB (target 12) | 107–151 s wall | 8.17 MB |

The S03 Explore atlas grew by the computed information row (F1 of R-E) in its 470 air points; u32's Explore CPU grew by
the bootstrap on every 10 % growth of the hits (F2). Every budget holds (atlas target 6 MB, point 150 kB, world 12 MB).

## Text for the integrator (STATUS.md / RULES.md)

- `RULES.md` §10, "Budgets": the measured line becomes "Measured on 2026-11-17 (local build): S03 Explore 940 points, 10 refused, 5.85 MB (largest point 12.9 kB), labs 39, 46 and 89 kB, Watch 0.03 + 0.02 MB, its world 6.11 MB; u32 Explore 48 points, 5.50 MB (largest point 132.7 kB), Watch 0.60 MB, its world 8.15 MB.".
- `RULES.md` §10, the view's contract: add "`setStory({worlds, w, fps})` (optional; Watch: the recording's decoded
  worlds and the one shown; S03 keeps one scene box for the whole recording and draws the earlier worlds faded)".
- The root READMEs' generated catalogue lists S03's recordings, and S03 now has a second one («air»):
  `tests/test_site_registry.py::test_the_readme_catalogue_is_the_registrys_in_every_language` fails until
  `python3 site/readme.py` is run (the root READMEs are not this agent's files).
- On the private server the worksheet asks the public site for `recordings/s03_projectile/index.json` (404: S03 is not
  published yet): the D11 fallback's request, QF's/QP's.
- `STATUS.md`: nothing left open from this part. Open elsewhere: the drawer's event times in Lab work (QP); u32's
  check-table number format (QP).
