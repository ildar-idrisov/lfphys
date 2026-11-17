# Review EX1-screens (R-P): the screens Watch, Explore and Lab work in a browser

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it wrote none of the code under review) |
| Date | 2026-11-17, on commit 507c059 (EX1, 2026-11-14), clean tree |
| Scope | The player's screens: `visualizations/player/js/{demo,atlas,explore,lab,fit,watch,worksheet,record_core,api,base,start}.js`, `player/run.html`, `player/worksheet.html`, `player/assets/demo.css`; the browser tests `tests/browser/demo_screens.mjs`, `start_page.mjs`, `site_smoke.mjs`. Used on `s03_projectile`, `u32_double_slit` and the toy world `tests/site_worlds/s98_atlas_toy`. |
| Not in scope | The engine's mechanics and the fit's statistics as a method (R-E), the atlas framework, keys and the live endpoint's process limits (R-F), the worlds' content as a teacher sees it (R-W). The views' own drawing (`s03_projectile/web/view.js`, `u32_double_slit/web/view.js`) only where a screen depends on it. Open items STATUS V52 (a)–(r) are not repeated. |
| Environment | `lfphys-viz` image, CPU only. Private server `lf-rvp-srv` on 127.0.0.1:8702 (`--memory=6g`, the repository read-only, a scratch copy of `visualizations/recordings/` plus the toy's fixture as `LFVIZ_RECORDINGS`; once with an empty recordings folder). The site built by `site/build.py --base /lfphys/` into scratch and checked by `site/check.py` (0 failures, 4 accepted warnings), served inside the Playwright container's own network (`evidence/pwsite.sh`). Playwright 1.58.2 (Chromium), EN and RU, 1280×800 and 390×844. |

The probes are in `evidence/` (`rp_*.mjs` in the browser; `py_hash.py`, `js_hash.mjs`, `lab_points.py`,
`lab_fit.mjs`, `fit_parity.*` outside it), with short logs and the screenshots cited below. `<repo>` and `<scratch>`
stand for the local paths.

## Summary

There are 19 findings: **2 errors**, **9 should-fix**, **8 nits**.

The answers to the questions:

- **Rule 2 in Explore and Lab work.** Yes, it holds. The browser shows only computed frames, the one at or before the
  cursor, and the readouts are the frames' `meas`. On the site the sliders take grid indices only. On a server a value
  off the grid is never drawn: it is computed when the slider is released. Lab sliders stay on the grid on a server too.
  One exception is a drawing, not physics: the lab's plot extends the fitted curve outside the measured range (F11).
- **Dequantisation** is bit-exact. All 38,591 quantised blobs in 1,041 recording and atlas files decode to the same
  float32 bytes in `api.js` as in `protocol.decode`.
- **Lab measurements.** The arithmetic is right:
  - the rounding to the division and the declared errors;
  - the |f′|·σ propagation;
  - `fit.js` against `linear_fit` (≤ 1.3·10⁻¹² relative; 1.7·10⁻¹¹ on an intercept near 0);
  - the verdict on full data: part 1 −0.81σ, part 2 −0.57σ, part 3 +0.74σ, all ✓.

  The bench around the arithmetic is not honest in four ways:
  - **F1, error.** A measurement can pair one set-up's ruler reading with another point's range.
  - **F4.** Repeated presses of «Measure» on one set-up count as independent points, so a diligent student turns part 1
    into ✗.
  - **F3.** «Check against the law» judges any plotted pair of columns against the step's law.
  - **F5.** A pause removes the reaction time from the manual stopwatch.
- **Worksheet.** The content is complete: the programme's lines, the steps, the blank tables, the questions, and the
  teacher's answers, notes and laws' references. But it is not «one A4 page per part», and the credit line is missing
  on 2 to 3 printed pages per copy, which RULES §10 claims for every page (**F6**). Russian copies carry Latin units
  (**F7**).
- **Captions** follow the timeline in EN and RU: the chapters, ◀◀ / ▶▶, and the earlier caption just before a caption's
  frame. A `hold` stops the playback as declared: 1018 ms for a 1 s hold, 2948 ms for a 3 s hold. A ▶ pressed during a
  hold is ignored until the hold ends, while the button still shows ▶ (**F12**).
- **«Compute live» on the server** does compute (`X-LF-Source: computed`), marks the off-grid value, says «computed
  live» in the passport, and refuses with the world's text and hint. Three things are wrong:
  - the «computed live» label on the trace runs off the canvas (**F8**);
  - the passport mixes in the atlas's key and build date (**F8**);
  - a full queue (429) is reported in English on a Russian page (**F7**).
- **«How we know this is right»** holds what the design asks for:
  - the checks as of the time shown (none before the launch);
  - the school list or the standard table;
  - the engine's modules;
  - u32's panels as folds;
  - the events and the passport.

  Two nits: the school projectile lists the whole `core.data` description, and the standard table has no «tol» column
  (**F17**).
- **Start page.** S03's three buttons open their tabs on the site (390 and 1280 px, EN and RU), and `start_page.mjs`
  passes in EN and RU. On a server without local recordings, every S03 screen is greyed although the site is published
  (**F9**).
- **Sub-path.** No request leaves `/lfphys/`. There were no 4xx responses and no page errors, both in `site_smoke.mjs`
  (EN and RU) and in a walk by hand through every screen at 390 and 1280 px in both languages.
- **Keyboard and accessibility** are the weakest part:
  - **F2, error.** Space and ←/→ are taken by the screen on every focused button and slider.
  - **F10.** The sliders tell assistive technology the grid index. The closed drawer sits in the tab order. Toggles do
    not expose their state.
  - **F15.** The detents are 18 px wide at phone width.

## Findings

### F1 (error): a lab measurement can pair the ruler's reading of one set-up with the range of another point

- **Where:** `player/js/lab.js:147-158` (`pick`: `s.values` is set at once, `s.cur` when the point arrives, with no
  sequence check and no error handling), `lab.js:195-197` (`readAll`: a `control:` instrument reads `s.values`, the
  slider, not the point shown). Compare `explore.js:162-175`, which guards the same race with `E.seq`.
- **Evidence:** `evidence/rp_lab.mjs`, `evidence/lab_en.log`, `evidence/ev_lab_race_en.jpg`. The point file of
  h = 0.30 m is delayed by 2.5 s, then the 0.30 and 0.80 detents are clicked one after the other. The result:
  - the slider says 0.8 and the view shows the 0.30 m point (`{"slider":0.8,"shown":0.3}`);
  - after the landing «Measure» adds the row `h = 0.80 ± 0.005, L = 0.371 ± 0.0005`;
  - 0.371 m is the range from 0.30 m; from 0.80 m it is 0.605 m (the atlas's points: 0.370890 and 0.605468,
    `evidence/lab_points.log`).

  The prefetch makes this realistic without any delay injection. A detent two steps away is not prefetched while its
  neighbour is, so on a slow phone network the slower, earlier request lands last.
- **What is wrong:** a row of the table, its CSV and the fit mix two set-ups, and the student cannot see it. The same
  mismatch follows a refused pick (`pick` returns after `say(refusal)` with `s.values` changed and `s.cur` kept). The
  S03 lab steps have no refused points, but the code is general. An unhandled rejection (a point that fails to load)
  also leaves the controls ahead of the view.
- **Fix:**
  - in `pick`, a sequence number as in `explore.js`, and an error message instead of an unhandled rejection;
  - read every `control:` instrument from the point shown (`s.cur.pt.values`) or the manifest's `fixed`, never from the
    slider;
  - disable «Measure» while `s.values` and `s.cur.pt.values` differ.

### F2 (error): Space and the arrow keys are taken by the screen on every focused button and slider

- **Where:** `player/js/demo.js:97-103` (the keydown handler skips text inputs, selects and textareas only; a range
  input and every button go to the screen's `key`), `explore.js:311-316`, `lab.js:430-438`, `watch.js:140-145` (Space →
  play, ←/→ → a frame, with `preventDefault`).
- **Evidence:** `evidence/rp_keys.mjs`, `evidence/keys_en.log`, `evidence/lab_en.log`. On S03 Explore, at 1280 and
  390 px:
  - the angle slider is focused and → pressed twice: the value stays 45° and the shot is launched instead (`clock`
    0 → 0.067, `launchedAt` null → 0);
  - Space on the focused «on» button of Air starts the playback (`playing: true`) and Air stays off, while Enter works;
  - Space on the focused «Explore» tab leaves the page on Watch;
  - in the lab, Space on the focused «Measure» adds no row;
  - Space on the focused «⏱ Stop» does not stop the stopwatch (`evidence/rp_swspace.mjs`,
    `evidence/stopwatch_space_en.log`). During the flight it pauses the flight and freezes the stopwatch (F5). After
    the landing it launches the ball again and restarts the stopwatch from 0: 1.63 s running becomes 0.295 s 0.3 s
    later, with `playing: true`. The student's timing is lost.
- **What is wrong:**
  - a keyboard user cannot move a control's slider with the arrows, the standard slider interaction;
  - Space, the standard activation key of a button, does something else on every button of the screens, «Measure»,
    «⏱ Stop», «Check against the law», the tabs and the toggles included.

  This fails WCAG 2.1.1 and makes the lab unusable by keyboard alone. Only Enter and Tab to the detents remain, and
  the help does not say so.
- **Fix:** handle Space and ←/→ only when the focus is on the page body, the stage or the timeline. Leave them alone on
  a focused button, checkbox, select or control slider. Add a keyboard pass to `demo_screens.mjs` (arrows move a
  control slider; Space on «Measure» measures).

### F3 (should-fix): «Check against the law» judges whatever is plotted against the step's law, under the law's name

- **Where:** `player/js/lab.js:268-280` (`checkLaw` uses `s.res`, the fit of the columns chosen in the plot's x and y
  selects, without comparing them with `step.plot.x` / `step.plot.y`), `lab.js:241-244` (any column on either axis).
- **Evidence:** `evidence/rp_labfull.mjs`, `evidence/labfull_en_ru.log`, and the same through `fit.js` alone in
  `evidence/lab_fit.log`:
  - Part 3, with y = «L in vacuum», does what the step's hint says («compare with 45° for the grey ball») and gets
    «θ* of the largest range = 44.97 ± 0.20 ° — law: 41.9 ° (computed by the engine…) ✗ does not agree: fit the parabola
    to the points near the top; compare with 45° for the grey ball». The student did exactly that and is told it fails.
  - Part 1, with x = h, gets «k = L / √h = 0.797 ± 0.035 m^½ — law: 0.6774 m^½ ✗». The value is the slope of L(h), not
    k.
  - Part 2's worksheet answer expects «the vertex of the parabola fitted to L(θ) … at 45° within its error». The tool
    can fit it (vertex 45.0), but «Check» answers «This fit gives no “slope”».
- **What is wrong:** the verdict names a quantity that was not measured and compares it with the wrong reference. A
  student following the hint is failed.
- **Fix:** check only the step's own pair of columns and its fit. Otherwise say «plot L against √h with the line through
  the origin to check the law». Alternatively, give each reference its columns, so that part 3 also checks the grey
  ball against 45° and part 2's L(θ) vertex against 45°.

### F4 (should-fix): repeated «Measure» on one set-up adds identical rows that the fit counts as independent; the table outlives the atlas

- **Where:** `player/js/lab.js:209-220` (`measureNow` appends every press), `lab.js:69` (the table's key
  `lfviz.lab.<world>.<step>` has no atlas key or version).
- **Evidence:** `evidence/lab_en.log` («five «Measure» on one point»: five rows 0.6/0.524, «Measured: row 6»).
  `evidence/lab_fit.log` runs part 1 over all 17 heights:

  | each height measured | k ± σ (m^½) | deviation from v₀·√(2/g) | verdict |
  |---|---|---|---|
  | once | 0.67687 ± 0.00065 | −0.81σ | ✓ |
  | 5 times | 0.67687 ± 0.00029 | −1.81σ | ✓ |
  | 20 times | 0.67687 ± 0.00015 | −3.62σ | ✗ |

  The 0.08 % is the air's real effect, which the bench computes and the vacuum law leaves out.
- **What is wrong:** the bench repeats exactly, so a repeated reading carries no new information. Its error is the
  instrument's rounding, the same every time. The weighted fit treats n copies as n independent points and shrinks σ as
  1/√n. A student who repeats measurements, as labs teach, is told that the law does not hold. The teacher's note says
  «it shortens the range by less than 0.1 %, below the tape's error, so the law without air agrees». That holds only
  for one row per height.

  The rows also survive reloads and rebuilds of the atlas (`localStorage`), so rows of an older bench mix into the fit.
- **Fix:**
  - one row per set-up: a repeat replaces the row or is refused with «already measured: the bench repeats exactly»;
  - or fit the distinct set-ups only;
  - put the atlas key into the storage key and drop rows from another key.

### F5 (should-fix): a pause freezes the manual stopwatch, so it reads the world time without the reaction

- **Where:** `player/js/lab.js:419` (the stopwatch advances only `if (… && !L.paused)`), `lab.js:323` (▶/Space during
  a flight sets `L.paused`), `lab.js:115` (only «slow» is refused for a manual stopwatch).
- **Evidence:** `evidence/lab_en.log`, «stopwatch: paused at the landing». The ball is launched from 0.60 m and Space
  pressed at the landing (T = 0.3499 s). «⏱ Stop» pressed 1.5 s later reads «0.36 s», the world time shown
  (0.3633 s), with no reaction in it. After such a pause, frame steps with ←/→ keep it frozen too, so a student can
  step to the landing frame and then stop the watch.
- **What is wrong:** the design and RULES §10 give the manual stopwatch one purpose, to measure the student's reaction
  («at real speed only … so the reaction is real»). Pause and frame-stepping defeat it as surely as «slow» would. The
  worksheet's first question is built on that ±0.1 s.
- **Fix:** keep the stopwatch running in wall time while it runs, whatever the playback does. Or refuse pause and
  frame steps until it is stopped, with the same reason «slow» gives.

### F6 (should-fix): the worksheet is not one A4 page per part, and the credit line is not on every printed page

- **Where:** `player/js/worksheet.js:56-73` (each part one `section`, the credit at its end), `player/worksheet.html:26-28`
  (a page break before each part, nothing to keep a part on one page). [error in earlier] RULES §10: «every printed
  page carries the attribution line»; design §2.3 and RULES: «one A4 page per part».
- **Evidence:** `evidence/rp_ws.mjs`, `evidence/worksheet_pages.log`, `evidence/worksheet_en_ru.log`,
  `evidence/ev_ws_s03_en.pdf`, `evidence/ev_ws_ru_p-3.jpg`, `evidence/ev_ws_ru_p-4.jpg`.
  - At the printable size (178 × 265 mm), parts 1–3 are 1512, 922 and 1578 px high in EN and 1535, 992 and 1625 px in
    RU, against about 1001 px per page.
  - EN prints 5 pages for 3 parts, and the teacher's copy 7. RU prints 6 and 8.
  - Pages without the credit: EN 1, 4 (and 6 with the teacher's page); RU 1, 5 (and 7).
  - RU page 4 holds only the credit's last line, «изменённые копии распространяйте под той же лицензией».
  - `demo_screens.mjs` checks only that the teacher's copy has more pages.
- **What is wrong:**
  - the licence response's condition (the line on every printed page) is not met;
  - a part split over two sheets is awkward in a classroom;
  - a page with one stray line wastes paper.
- **Fix:**
  - print the credit in a running footer (`position: fixed; bottom: 0` in print CSS repeats on every page in Chromium);
  - make a part fit one page: 8 blank rows → 6 at print, a smaller axes box, the programme's lines only on part 1;
  - or drop the claim and say «per part».

  Then let the test count pages per part and pages with the credit (pdftotext or the PDF's text objects).

### F7 (should-fix): English leaks into Russian pages: units of the laws, a law's id, the live endpoint's messages

- **Where:**
  - `player/js/lab.js:274-277` (`unit = law.unit || ref.unit`, a plain "m^½", "m" or "°", put into the text without
    `t()`);
  - `player/js/worksheet.js:81` (`${r.unit || st.law.unit}`, the same);
  - `lab.js:272` («This fit gives no “{q}”» with `q = law.quantity`, the id "slope" or "vertex");
  - `player/js/atlas.js:206` (on any status but 400, the error is `j.text`, the server's English text, not
    `t(j.error)`), shown by `explore.js:172` and `explore.js:210`.
- **Evidence:**
  - `evidence/labfull_en_ru.log` (RU): «k = L / √h = 0,67687 ± 0,00065 m^½ — закон: 0,6774 m^½», «… = 2,54901 ±
    0,00050 m — закон: 2,549 m»;
  - `evidence/worksheet_text.log` (RU teacher page): «k = L / √h = 0,6774 m^½», «= 2,549 m»;
  - `evidence/live_en_ru.log` (RU, u32, seven concurrent off-grid points then one from the UI; statuses
    200×5, 429, 429): «Эту точку не удалось загрузить: the server computes other points now; try again in a moment».
  - The table's headers on the same page say «h, м», «√h, м^½».
- **What is wrong:** rule 13: no words of another language in a user's text. The units are inconsistent within one
  page, and a Russian error message carries an English sentence.
- **Fix:**
  - pass the units through `t()`, adding "m^½" to the catalogues, or make law units `T`;
  - name the quantity by `law.label`;
  - in `atlas.js`, throw `apiError(j, r.statusText)` (`t(j.error)`) as `api.js` does.

  Add the 429 message and a law's check to `i18n_checks` or to the RU run of `demo_screens.mjs`.

### F8 (should-fix): a live point's labels: the trace's «computed live» runs off the canvas; the passport describes the atlas

- **Where:**
  - `player/js/explore.js:261` (the trace label: all values plus «· computed live»), drawn by
    `s03_projectile/web/view.js:228` from the trace's landing point, to the right;
  - `explore.js:330-334` (the passport of a live point: «Atlas · key <atlas key>», «Made <atlas build date>»,
    «Computed live on this server at» with the browser's clock, `toISOString`, without a zone);
  - `atlas.js:208-210` (`source` and `key` from `X-LF-Source` / `X-LF-Key` are kept but never shown).
- **Evidence:** `evidence/ev_live_trace_label_clipped_en.jpg`: the 37.3° trace's label shows «Launch heig» at the
  canvas edge at 1280 px, and «computed live» is not visible. `evidence/live_en_ru.log` (the drawer of the 37.3°
  point): «Computed live on this server at 2026-11-17 15:16:08. | … Atlas | explore · key 641ab5d011d20d4e | … Made |
  2026-11-14 13:37:11». `evidence/live_headers.log`: the server answers the same value from its cache
  (`X-LF-Source: cache`), and the passport would still say «computed live … at <now>».
- **What is wrong:** RULES §10 promises «labelled «computed live» in the passport and on its trace». On the trace the
  label is unreadable whenever the trace lands near the canvas's right edge. That is where S03's view puts the
  landings: in the evidence the axis ends at 25 m, and the two shots land at about 23.5 and 23.9 m. The passport of a point computed today shows the atlas's key and date from 2026-11-14. A cached point
  is dated now.
- **Fix:**
  - draw the trace's label inside the canvas (right-aligned when it would overflow) and short (the varied values only);
  - for a live point, show the point's key, «from the server's cache, computed at …» when `X-LF-Source` is `cache`, and
    the time with its zone;
  - omit «Made» or label it «the atlas was built».

### F9 (should-fix): on a server without local recordings, every screen of S03 is greyed although the site is published

- **Where:** `player/js/start.js:346-365` (`screenButtons` reads only `D.rec`, the local index, never `D.siteRec`, while
  `recsOf` at `start.js:82-89` falls back to the site), `player/js/demo.js:48-50` (only `apiGet("recordings")`). The
  comment at `start.js:345` says «not made yet (here, or on the site)».
- **Evidence:** `evidence/rp_norec.mjs`, `evidence/norec_en.log`. The server runs with an empty `LFVIZ_RECORDINGS`
  (`/api/recordings`: `{"worlds": {}, "published": true}`); requests to the public site are blocked in the browser.
  - S03's card shows «▷ Watch», «◎ Explore» and «✎ Lab work», all greyed with «Not made yet: build it locally
    (site/record.py) or compute live»;
  - `/run?demo=s03_projectile&screen=explore` shows «No atlas of this screen yet».

  By the code, u34's «▷ Recording» on the same server is taken from the site when it is reachable.
- **What is wrong:** recordings and atlases are git-ignored, so this is every fresh checkout. The school audience's only
  ready world is then unusable on the owner's own server, though the site serves the same atlases. Design §3.7
  promised «fetched from the public site when published and of the same version, as recordings are». STATUS V52 (g)
  covers only the live endpoint's on-grid point, not the screens, the Watch recording or the start page's buttons.
- **Fix:** in `start.js` and `demo.js`, fall back to `D.siteRec` / the site's `api/recordings.json` and the site's
  `recordings/<world>/…` files for a world whose local entry is missing and whose version matches, as `recsOf` and
  `player.js` do. Or widen V52 (g) to say so, and make the greyed buttons' reason true («not on this server; the public
  site has it: <link>»).

### F10 (should-fix): accessibility of the screens

- **Where:**
  - `player/js/explore.js:66-67` (the site's slider is `min 0, max n−1`, no `aria-valuetext`);
  - `explore.js:52-58, 77-79`, `demo.js:300-302`, `lab.js:123-124` (toggles, detents, speed and step buttons, with
    state only as the class `on`);
  - `player/assets/demo.css:92-94` and `demo.js:150-155` (the closed drawer is moved off-screen with `aria-hidden` but
    stays focusable; opening it leaves the focus behind the scrim; no `role="dialog"`);
  - `demo.js:72-73` (tabs without `aria-controls`; the screens without `role="tabpanel"`);
  - `demo.js:290-293`, `:77-79`, `:92` (▶/❚❚, ⟲, ✕, ◐, ?, ☰ named only by their symbol, with a `title`).
- **Evidence:** `evidence/a11y2_en.log`, `evidence/keys_en.log`:
  - with h = 5 m the site's slider reports `value "3"` and `aria-valuetext` null;
  - no `aria-pressed` on «on/off», the detents or «normal/slow»;
  - Tab after «slow» lands on `button.dm-close` inside the closed drawer (`aria-hidden="true"`, off-screen);
  - after Enter on «How we know this is right» the focus stays on that button behind the scrim;
  - the tab order passes all 5 + 5 + 19 detents before ▶.
- **What is wrong:** a screen reader announces the index, not the value, and cannot tell which toggle is on. Keyboard
  users tab into an invisible panel, and the open drawer is not a dialog they are placed into.
- **Fix:**
  - `aria-valuetext` = the value with its unit;
  - `aria-pressed` on toggles, detents and the speed buttons;
  - `visibility: hidden` (or `inert`) on the closed drawer; `role="dialog"`, focus to its heading on open and back to
    the opener on close;
  - `aria-controls` / `role="tabpanel"`;
  - `aria-label` on the symbol buttons;
  - `tabindex="-1"` on the detents, since the slider covers them for the keyboard once F2 is fixed.

### F11 (should-fix): the lab's plot draws the fitted curve outside the measured range, from 0

- **Where:** `player/js/lab.js:290-292` (the axes always include 0), `lab.js:304-309` (the fitted curve is drawn over the
  whole axis, `x0 … x1`).
- **Evidence:** `evidence/ev_lab_part3_plot_ru.jpg` (part 3, RU). The parabola fitted over 25–60° is drawn from θ = 0,
  where it reads L ≈ 3 m: `c0 = 2.99 ± 0.96`, from a throw along the floor. The teacher's note says «the parabola of
  part 3 is a model of L(θ) near its top only».
- **What is wrong:** the plot shows a statement nothing measured or computed, and a wrong one: a throw along the floor
  from h = 0 has range 0. It also teaches reading a fit beyond its data.
- **Fix:** draw the fitted curve over the measured x-range only (`line0` may keep the origin). Let the axes start at
  the data when 0 is far from them.

### F12 (nit): a ▶ pressed during a caption's hold is ignored while the button shows ▶

- **Where:** `player/js/watch.js:126` (`if (now < V.holdUntil) return;` before `this.dirty` is handled).
- **Evidence:** `evidence/watch_en.log`. Pause then ▶ (Space) at the held caption: `playing: true` while the button
  still reads «▶». The playback starts only when the old hold ends, 2.2 s later on u32. A second press, the natural
  reaction, pauses.
- **Fix:** end the hold on any user action (pause, play, scrub), and render while held.

### F13 (nit): Watch's «▶ Compute live» starts the recording's first world, whatever world is shown

- **Where:** `player/js/watch.js:171-174` (`liveBody` returns the recording's `preset` and `seed`).
- **Evidence:** `evidence/live_en_ru.log`, «from Watch at its 4th world»: S03 is shown at the 4th world (the 67 mm ball,
  20 m/s, 45°, air, the vacuum companion). The live run gets `story` with h 1.25 m, v₀ 2 m/s and `companion: drop`.
- **Fix:** send the shown world's set-up (its header's parameters), or label the button «compute the start of this
  story live».

### F14 (nit): the lab table's numbers

- **Where:** `player/js/lab.js:42` (|f′|·σ is 0 at a stationary point), `lab.js:62-67` (`pm` with 12 decimals for
  e → 0), `lab.js:225-229` (a reading to its division, its error finer).
- **Evidence:** `evidence/site_lfphys_ru_en.log`:
  - part 2 at 45°: «sin 2θ = 1.000000000000 ± 0.000000000000» (the second-order spread is ≈ 1.5·10⁻⁴);
  - part 1: «0.60 ± 0.005».
  - Part 1 lists the stopwatch and shows its widget, but no column takes its reading, so it never reaches the table or
    the CSV.
- **Fix:**
  - at a stationary point, use the second-order term or show «1.0000»;
  - write a reading with as many decimals as its error («0.600 ± 0.005»);
  - add a «T, s» column fed by the stopwatch to part 1, or drop the stopwatch from the step's instruments.

### F15 (nit): touch targets under 44 px at phone width

- **Where:** `player/assets/demo.css:49-53, 165` (detents 30 px high, their width the label's), `demo.css` for the step
  buttons, the topbar's language links and the back link.
- **Evidence:** `evidence/keys_en.log` and `evidence/lab_en.log` at 390 px:
  - detents 18×30 and 23×30;
  - step buttons 32×44;
  - EN|RU 15×16;
  - «← School» 55×18.

  ▶ (96×44), ⟲, «Measure» and the slider (44 high) meet the target. Design §3.9 lists «tap on a detent» among the
  touch actions.
- **Fix:** give the detents and step buttons a 44 px hit area (padding or `::after`) without changing the look.

### F16 (nit): wording and typography

- **Where:** `player/js/worksheet.js:96-98`, `lab.js:276-277`, `worksheet.js:81`.
- **Evidence:** `evidence/worksheet_text.log`:
  - «“Research to test the hypothesis: …” (our translation) (translated; the programme's own wording: «…»)»: the T
    already says «our translation» and the page adds «translated»;
  - «θ* of the largest range = 41.9 °» and «42.03 ± 0.19 °»: a space before the degree sign, in EN and RU.
- **Fix:** drop one of the two notes; no space before «°» (`unit === "°"`, as `valuesText` does).

### F17 (nit): «How we know this is right» on a school projectile

- **Where:** `player/js/demo.js:261-272` («Physics of this world» from the header's `engine` list), `demo.js:257-260`
  (the standard table).
- **Evidence:** `evidence/misc_srv_site.log` (S03 Explore after a landing, every fold open). «Physics of this world»
  opens with `lfphys.core.data`'s whole description: «α_s(M_Z), M_Z, the heavy quark masses, the charmonium and
  bottomonium masses (PDG 2024); the orbital elements of Mercury …; the Planck 2018 cosmological parameters …». S03
  uses the air's data only. u32's table has the columns check, computed, reference, rel and ✓, but no «tol» (design
  §3.3: «computed ↔ reference, rel, tol»).
- **Fix:** let a world name the parts of `core.data` it uses (or the header list the data module's relevant line).
  Add the tolerance column at `standard`.

### F18 (nit): documents and code disagree on two details

- **Where:**
  - RULES §10, Lab work: «`event` binds the instrument … (S03 part C: the grey ball's tape after
    `companion_landing`)», but `s03_projectile/viz.py:352-353` declares `tape_grey` without `event`; the world's
    `meas.range_vacuum` is None until the grey ball lands, which does the job;
  - RULES §10, Compute live: «a value within a tenth of a step of a detent snaps to it», but `explore.js:63, 71` snaps
    within a tenth of the smallest step of the control. For S03's height (0, 1, 2, 5, 10 m) that is 0.1 m also between
    5 and 10.
- **Fix:** correct the two sentences (or declare `event` in S03 and use the local step).

### F19 (nit): what the browser tests do not cover

- **Where:** `tests/browser/demo_screens.mjs`, `start_page.mjs`, `site_smoke.mjs`, `player/js/tests/lab.test.mjs`.
- **What is missing:**
  - **`demo_screens.mjs`** has no keyboard check (F2) and no `hold` check, though the toy declares one at 1.5 s.
  - It runs the lab on its first step only, so these are never exercised in a browser: part 2's `sin2` column, part 3's
    quadratic, vertex, engine reference and second tape.
  - It does not test a race between two picks (F1), the 429 message in RU (F7), the trace label (F8), or the
    worksheet's pages per part and credit per page (F6).
  - Its «as the site» mode serves at `/`, not under a sub-path.
- **`start_page.mjs`** clicks only the first enabled screen button of each card.
- **`site_smoke.mjs`** opens each screen but does not use it: no launch, no measure, no chapter.
- **`lab.test.mjs`** uses hand-computed cases, while design §2.3 says the instrument model is «tested against Python
  fixtures».
- **Fix:** add these checks. The probes in `evidence/` can serve as a start.

## What was checked and found fine

- [useful] Rule 2 in Explore and Lab work (code and browser):
  - every screen shows the frame at or before its time (`frameIndexAt`), and the view is fed the point's messages up to
    it (`record_core.showAt`);
  - the readouts are the frames' `meas`, «—» before their event;
  - the S03 view draws the arrows from frame values, and its only formula is an arrow's display scale;
  - traces fly on their own launch times;
  - the derived columns and the fit are arithmetic on readings.
- [useful] Sliders on the site: all S03 and u32 Explore sliders are `0..n−1` with step 1. Detents give grid values, and
  `demo_screens.mjs` checks this.
- [useful] Sliders on a server:
  - steps of 0.05 m, 0.25 m/s and 0.25°;
  - a value near a detent snaps to it, an off-grid one is computed only on release and its output is marked
    (`dm-off-grid`);
  - lab sliders stay on the grid on a server (`controlRow(…, {server: false})`).
- [useful] Dequantisation: 38,591 quantised blobs in 1,041 files, all recordings and atlas points (S03, u32, the toy),
  have equal sha256 of their float32 bytes from `api.js` and `protocol.decode` (`evidence/dequant.log`). The node tests
  pass (35 of 35).
- [useful] The rounding to the division and the declared errors: 0.524413 → 0.524 ± 0.0005 m, 27.222191 → 27.222,
  40.168977 → 40.169; the ruler ±0.005 m; the protractor ±0.5°; the stopwatch ±0.1 s, with its note
  (`evidence/site_lfphys_ru_en.log`).
- [useful] Error propagation |f′|·σ: √h at 0.60 m gives 0.7746 ± 0.0032; `lab.test.mjs` covers sqrt, square, sin2,
  inverse and log.
- [useful] `fit.js` against `lfphys.tools.stats.linear_fit` on S03's own readings, 9 cases (`line0`, `line`,
  `quadratic` with its vertex, `power`): ≤ 1.3·10⁻¹² relative; 1.7·10⁻¹¹ on an intercept of 0.0023, an absolute
  4·10⁻¹⁴ (`evidence/fit_parity.log`). The browser's fit equals it.
- [useful] «Check against the law» over each step's whole grid, in the browser:
  - part 1: 0.67687 ± 0.00065 against 0.67740, ✓;
  - part 2: 2.54901 ± 0.00050 against 2.54929, ✓;
  - part 3: 42.03 ± 0.18–0.19° against 41.9°, ✓;
  - the reference and how it was obtained are in the text (`evidence/labfull_en_ru.log`).
- [useful] Captions:
  - placed at `at × fps` (toy 0, 15, 30; u32 0, 160, 320, 440, 520, 720, 960);
  - one chapter tick each; ◀◀ / ▶▶; the earlier caption one frame before;
  - RU texts (`demo_screens.mjs` EN and RU passed);
  - `hold` 1 s → 1018 ms and 3 s → 2948 ms at the caption's frame (`evidence/watch_en.log`).
- [useful] «Compute live»:
  - an off-grid 37.3° is computed (`X-LF-Source: computed`), and the server's cache and the atlas answer
    (`cache`, `atlas`);
  - a refusal shows the world's text and «What to change: …» with ▶ off;
  - «Another sample» gives seed 2, marked live;
  - «▶ Compute live» from Explore (h 5 m, v₀ 12.5 m/s off-grid, 30°, air) and from Lab part 2 (60°, v₀ 5, air off)
    opens a run with exactly that set-up (`evidence/live_en_ru.log`).
- [useful] «How we know this is right»:
  - before the launch «No checks up to this moment»; after the landing «✓ 4 checks agree with the laws» as a plain
    list at school;
  - u32 gets the table and its own panels as folds («Particle», «Model of the slit screen», «Counters and statistics»,
    «Approximations of this segment»);
  - events; the passport with the atlas, key, code, seed, date and the point's index, or «World k of n» on Watch.
- [useful] The worksheet's content in EN and RU:
  - the programme's lines with the Russian original;
  - the equipment, the conventions, each part's goal, instruments, blank table, plot and law, the questions;
  - «For the teacher»: the answers, notes and the laws' references from the manifests;
  - u32 says «This demonstration has no lab work.»; an unknown id says so; no horizontal scroll at 390 px.
- [useful] Start page:
  - S03's «▷ Watch 0:40», «◎ Explore» and «✎ Lab work» open their tabs on the site (390 and 1280 px, EN and RU);
  - `start_page.mjs` EN and RU: 87 checks each, all passed.
- [useful] Sub-path:
  - no request outside `/lfphys/`, no 4xx and no page error in `site_smoke.mjs` (EN and RU, 94 checks);
  - the same in a walk by hand at 390 and 1280 px (start page → each screen, launches, overlays, the drawer, the help,
    three lab parts measured, the worksheet link, u32's «More recordings», back to the start page;
    `evidence/site_lfphys_ru_en.log`);
  - no «▶ Compute live» and no «Another sample» on the site.
- [useful] Addresses: `?demo=v02_double_slit` opens u32 on the server and on the site; `?demo=u34_orbits` (no screens)
  goes to its first recording; an unknown world says «No such demonstration»; an unknown screen opens the first.
- [useful] u32 Explore (`buildup`, `acts: now`): the cursor stays at 2.00 s across a change of d, the frames are exact
  multiples of 0.25 s, and the previous point becomes a trace (`evidence/u32_explore.log`).
- [useful] 390 px:
  - `scrollWidth` ≤ 390 on every screen (toy, S03, u32, EN and RU) and on the worksheet;
  - a sticky time bar;
  - ▶ 96×44, ⟲ 44×44, «Measure» 362×44, «Check against the law» 370×44.
- [neutral] The suites as delivered pass on this host: `demo_screens.mjs` toy EN 102, S03 EN 106 and RU 105, u32 EN
  and RU 75 each; the site build (1,237 files, 65.4 MB, 46/46 recordings, 5/5 atlases) and `check.py`
  (`evidence/suites.log`).
