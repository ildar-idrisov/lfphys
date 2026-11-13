# Review P17-start-page: the start page by audience, the player on a recording, the aliases of the old ids

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the code under review) |
| Date | 2026-11-13 |
| Scope | `git diff f3d137d..1f4ceac` on branch `p17-landing`, the "start page" part: `player/index.html`, `js/start.js`, `js/runs.js`, `runs.html`; the recording mode (`js/player.js` `?rec=`, `js/api.js` `openRecording`/`apiGet`, `js/base.js` `url`/`page`, `js/instruments.js` CSV on a recording); read-only behaviour on a recording including the views' own buttons; `registry.ALIASES`, the 301 routes, old run records; the registry's new fields and `check()`; the new EN/RU texts; `tests/browser/start_page.mjs`, `record_mode.mjs`. |
| Not in scope | The recorder, the site build and `check.py` (the "site" review); the physics of the worlds beyond what a recording shows. |
| Environment | `lfphys-viz` image, CPU only. Private server `lf-rv-p-srv` on 127.0.0.1:8682 (`--memory=8g`, the worktree mounted read-only, a scratch runs folder with 8 records made before the rename: v01, v02, v04, v07, v10, p01 from 2026-10-28/11-11 and v09, v12 from 2026-10-29), once with the fresh recordings of `visualizations/recordings/` and once with none (`LFVIZ_RECORDINGS` pointing at an empty path). Own site build (`site/build.py --base /lfphys/` into scratch, `check.py`: 0 failures, 4 accepted warnings) served by `python -m http.server` under `/lfphys/` on the same port. Playwright 1.58.2 Chromium (swiftshader) in `mcr.microsoft.com/playwright:v1.58.2-jammy`, `--memory=4g`. Viewports 1280×900, 390×900/844, 1600×1000. |

The scripts are in `evidence/` (`e1_start.mjs` … `e7_cont.mjs`), with short logs and the screenshots cited below.

## Summary

There are 14 findings: **1 error**, **7 should-fix**, **6 nits**.

The start page itself meets rule 16 well. It leads by audience, frames everything as learning materials, and keeps
school cards free of parameters and devices. Server cards offer «▶ Compute live» and «▷ Recording m:ss». On the
site, cards offer only «▷ Watch the recording», and the laboratories are greyed with «Works only with a running server»
and a quick-start link in the viewer's language. Every path worked under `/lfphys/` with no request outside the
sub-path, and at `/` on the server. Old `/viz/v02_…` URLs answer 301. Old `?rec=v04_orbits/…` links play on both the
server and the site. Eight records from before the rename open, and two of them were resumed (replay route).

The weak points are in what a viewer meets after the start page:
- **F1, error.** At 390 px the player on a recording does not work: the page overflows, the view's canvas has zero size
  (console errors), and the RECORDING badge falls out of the top bar. The public site offers only this player, and the
  start page sends phone visitors straight to it.
- **F2.** On a recording, the views' own speed buttons do nothing and say nothing: u32 «▷ flight» and «▷▷ build-up»,
  u37 «▷ flight» and «▷▷ collect statistics», u35 «▷ photon flight» and «▷▷ collect statistics». STATUS V51 (f) does
  not cover these.
- **F3.** "recording" names both a live computing run and a saved recording. A saved recording's tab title reads
  «… · запись идёт» ("recording in progress"), and the start page's «Continue» strip uses "· recording" for a live run.
- **F4.** The help (?) on a recording describes the live run: ⏺, «Set-up — changes at once», "there is no stop".
- **F5.** On a server with no local recordings (every fresh clone), all 17 «▷ Recording» buttons are enabled. Every
  click ends at «No recording for this version…», which gives a false reason.
- **F6–F8.** The label «Already there at university level» also lists research worlds. The focus ring on the audience
  tiles is barely visible. The greyed laboratory text and two audience colours fail the AA contrast ratio.

## Findings

### F1 (error): the player on a recording is unusable at phone width

- **Where:** `player/run.html` and `player/assets/chrome.css` (the player's three-column layout); reached from
  `js/start.js:81` `recHref` (server) and every «▷ Watch the recording» on the site.
- **Evidence:** `evidence/e2_u32_ru_390.jpg` (`/run?rec=u32_double_slit/young&lang=ru` at 390×844). The page is 405 px
  wide (`scrollWidth` 405 > 390). Only the left panel, the centre's control rows and the transport are visible, and the
  picture is not. The top bar shows «← Университет ⇤ Двухще… стандартная физика»: the badge «ЗАПИСЬ · …» is not
  visible. The console logs `InvalidStateError: Failed to execute 'drawImage' … canvas element with a width or height
  of 0 at drawScreen (…/viz/u32_double_slit/view.js)` (`evidence/e2_recording.log`, the line `ru 390 u32`).
- **What is wrong:** rule 16 and the owner's 2026-11-12 words make the site a learning resource, so phones are a primary
  audience. The start page works at 390 px, but its only action on the site opens a page where the demonstration cannot
  be seen. The RECORDING badge, which tells the viewer what this is, is also cut off.
- **Fix:** give `run.html` a narrow layout (for example under 700 px):
  - the centre first, with a minimum height;
  - the side columns folded below it, or behind ⇤/⇥, folded by default;
  - a top bar that wraps and keeps the badge.

  Add a 390 px pass with a not-blank canvas check to `record_mode.mjs` and `site_smoke.mjs`.

### F2 (should-fix): the views' own speed buttons are dead on a recording

- **Where:**
  - `u32_double_slit/web/view.js:85-86`, `u37_bell_test/web/view.js:48-49` and `u35_optics_bench/web/view.js:68-69` call
    `ctx.send("speed", …)`;
  - `player/js/player.js:351-353` `send()` passes the command to `S.conn.send`;
  - on a recording that is `openRecording`'s `send() { /* a recording takes no commands */ }` (`js/api.js:144`).
- **Evidence:** `evidence/e2_recording.log`. After each click the speed read-out did not change («40 ms / s» → «40 ms /
  s» on u32; «834 ns / s» on u37; «1.25 ns / s» on u35) and no toast appeared. The buttons are enabled
  (`disabled: false`).
- **What is wrong:** these controls look live and do nothing. They are exactly what a viewer of a recording needs: the
  double slit's «▷▷ build-up» is the way to watch the pattern build up. STATUS V51 (f) lists only the action buttons
  (u34 push, u37 reset), which at least answer with a toast.
- **Fix:** in `send()`, when `S.recording` and `cmd === "speed"`, set `S.speed` from `args.value` (clamped to
  `S.speedRange`) and call `updateTransport()`, as `$("speed").onchange` does for a recording (`player.js:1234`). Any
  other command on a recording should give the read-only toast instead of a silent no-op. Add a click on these buttons
  to `record_mode.mjs`.

### F3 (should-fix): "recording" is both a live run and a saved recording; a saved one is titled "recording in progress"

- **Where:**
  - `player/js/player.js:81`: `document.title = … · ${S.recording ? t("recording") : runId}`;
  - the same msgid «recording» is the live state (`player.js:1317`, `start.js:570` «Continue», `runs.js:72`);
  - `ru.json` gives "recording" as «запись идёт».
- **Evidence:**
  - `evidence/e2_recording.log`, the lines `ru 1280 u32` and `ru 390 u32`: the tab title is «Двухщелевой опыт · запись
    идёт» on a saved recording;
  - `evidence/e7_continue.log` and `evidence/e7_continue_en.jpg`: the home page's strip reads «Continue: Light over
    large distances · recording» for a live computing run, on the same page whose cards say «▷ Recording 0:40» for a
    saved file;
  - the live player says «запись идёт · вживую», «⏸ запись».
- **What is wrong:** the brief asks that "nothing that looks live is live, and it says what it is". In Russian the
  saved recording's tab title says it is being recorded now. In both languages, «Continue · recording» means
  computing, while «▷ Recording» on the cards means a file. The glossary in `RULES.md` §7 has no entry for the two
  senses.
- **Fix:**
  - give the title its own msgid (for example «{title} · saved recording» / «{title} · запись»);
  - in «Continue», use «computing» / «считается» (or «live»);
  - add a glossary line to `RULES.md` §7: the saved demonstration is "recording" / «запись», the ⏺ state is
    "computing" / «расчёт идёт», and keep it in both READMEs.

### F4 (should-fix): the help on a recording describes a live run

- **Where:** `player/js/player.js:1337-1350` (`showHelp`), which has no branch for `S.recording`.
- **Evidence:** `evidence/e5_site.log`, the line `site help on recording` (served from the static site). It says:
  - «There is no stop: a run nobody watches pauses by itself … ⏺ continues it…»;
  - «“Set-up — changes at once”… A change applies when you release the slider…»;
  - «“▶ Start a new world” …»;
  - «Keys: Space — record/pause».

  None of this holds on a recording; on the site there is no run, worker or ⏺. The same help also says «the period is
  set in the catalogue», which is stale on the server too: the retention moved to «My runs» in this change (rule 12).
- **Fix:** a recording branch: what a recording is (made by the recorder, plays without computing, the badge), the
  transport and its keys (Space plays), what is read-only, and where to compute live (the server's «▶ Compute this
  scenario live», or on the site the README quick-start link). Fix «set in the catalogue» → «on the “My runs” page».

### F5 (should-fix): with no local recordings, every «▷ Recording» leads to a dead end with a false reason

- **Where:**
  - `js/start.js:349-360`: the button is enabled whenever the world declares a recording spec, with the title «Play
    the recording of this scenario from the public site»;
  - `js/player.js:146-153`: the fallback fetch to the site, and the same message for "site unreachable", "no such
    recording" and "another version".
- **Evidence:**
  - `evidence/e4_no_local_recordings.log` and `evidence/e4_click_norec_en.jpg`. A server with an empty recordings
    folder, the state of every fresh clone because `visualizations/recordings/` is git-ignored: 14 of 14 university
    buttons are enabled; clicking u32's opens «No recording for this version: record it locally or compute live».
  - The real reason is a 404 from `https://ildar-idrisov.github.io/lfphys/recordings/u32_double_slit/index.json`
    (the site is not deployed); the version is not the problem.
  - A mistyped id gives the same text on the server and on the site, where «record it locally» means nothing
    (`evidence/e5_site.log`, `run.html?rec=u32_double_slit/nope`).
  - `visualizations/README.ru.md` says «если записи нет, кнопка серая, с подсказкой…», which never happens on a server.
- **What is wrong:** the start page shows something as available that is not, and the refusal names a wrong cause.
  This holds even after deployment for any recording the site lacks.
- **Fix:**
  - separate messages: «This recording does not exist», «The public site could not be reached; record it locally
    (`site/record.py`) or compute live», «The site's recording was made by version X of this world; this server runs
    Y». On the site, only the first, with a link to the start page.
  - On the start page, either mark site-backed buttons differently («▷ Recording (from the site)») or check the site's
    `index.json` once per world before enabling them.
  - Align the README sentence with the behaviour.

### F6 (should-fix): «Already there at university level» lists research worlds

- **Where:** `js/start.js:267-270`: `there` takes `university` and `research` worlds, and the label is a fixed
  «Already there at university level:».
- **Evidence:** `evidence/e1_school_en_1280.jpg`, School › Optics: «Already there at university level: Research ·
  Double slit (long slits, 3-D): the exact Schrödinger equation and Bohm trajectories · University · The double-slit
  experiment …». The README's generated catalogue says «Already there at another level:» (`site/readme.py:44`), so
  the page and the documents differ (rule 12).
- **Fix:** use the README's msgid «Already there at another level:» (translation already in `ru.json`), or split the
  line by audience.

### F7 (should-fix): keyboard focus on the audience tiles is nearly invisible; chips do not expose their state

- **Where:**
  - `player/assets/chrome.css:233`: `.st-tile:focus-visible { border-color: var(--aud); outline: none; }`. The top
    border is already `--aud`, so only the two 1-px side borders and the bottom one change colour.
  - `js/start.js:169, 209`: the section chips and the «By:» toggle are toggle buttons with no `aria-pressed`.
- **Evidence:**
  - `evidence/e1_focus_tile_en.jpg`: the University tile is focused, and it is hard to tell which one.
  - `evidence/e1_contrast_focus.log`: the chips report `pressed: null`.

  The tab order itself is sensible: title, top-bar links, the four tiles, the footer; on an audience page, back, the
  chips, search, then the cards.
- **Fix:** `outline: 2px solid var(--aud); outline-offset: 2px` on `:focus-visible`; set `aria-pressed` on the chips
  and the «By:» toggle.

### F8 (should-fix): contrast below AA in the greyed laboratories and two audience colours

- **Where:**
  - `player/assets/chrome.css:238`: `.st-tile.off, .card.off { filter: grayscale(1); opacity: .72; … }`;
  - `chrome.css:218`: `--aud-school: #2b8a3e`, `--aud-labs: #c25e00` (light theme).
- **Evidence:** `evidence/e1_contrast_focus.log`, computed from the page's own colours:
  - greyed muted text (the tile's «4 benches», the cards' purpose text) is 2.93:1 on its card;
  - the tile names «SCHOOL» and «LABORATORIES» (13 px bold, not large text) are 4.37:1 and 4.29:1 on the panel;
  - the disabled «▷ Recording» link is 2.78:1.

  See `evidence/crop_site_labs_ru.jpg`. DESIGN §1.3 asks that the laboratories "stay readable".
- **Fix:** keep the text at full opacity and grey only the pictures (or the border and background). Darken
  `--aud-school` (≈ #237a35) and `--aud-labs` (≈ #a85100) to reach 4.5:1.

### F9 (nit): Russian wording

- **Where:** `visualizations/locales/ru.json`.
- **What is wrong, with a fix for each:**
  - «“▶ Compute live” starts a run…» → «… запускает запуск…». Use «начинает расчёт на этом сервере».
  - «Start a run of this world and scenario on this server…» → «Запустить запуск…». Use «Начать на этом сервере
    расчёт этого мира и сценария…».
  - «hypotheses, marked as such» → «гипотезы, отмеченные как гипотезы» (tautology). Use «всё новое помечено как
    гипотеза».
  - «In preparation: {next:d} next, {n:d} planned» → «Готовятся: {next:d} ближайших…» has no plural forms («1
    ближайших»). Use «Готовятся ближайшие: {next:d}; всего в плане {n:d}», or plural entries (`RULES.md` §7: "every
    count phrase has plural forms").

### F10 (nit): the school tile has no picture block; two tile pictures are nearly blank

- **Where:**
  - `chrome.css:240` sizes only `img.pic` (`aspect-ratio`), so the placeholder `div.pic.ph` (`start.js:144`,
    `chrome.css:290`) collapses to zero height;
  - `start.js:131` takes the tile's picture from the first world that has one.
- **Evidence:** `evidence/e1_home_en_1280.jpg`. «SCHOOL» sits at the top of its tile while the others sit under a
  picture, and the school tile is a large empty box. The University tile shows u31's poster (grey-level standard
  deviation 17 of 255, almost white). The Laboratories tile shows p01's (deviation 9, almost black).
- **Fix:** add `.pic.ph { aspect-ratio: 2 / 1; }`. Name the tile's picture per audience (a field in `AUDIENCES`, for
  example u32 and p04).

### F11 (nit): the badge is cut at 1280 px; the site's read-only note points to a live run that does not exist there

- **Where:** `player.js:194-198` (the badge in a flex top bar) and `player.js:221-224` (`rec-note`).
- **Evidence:**
  - `evidence/e2_u32_ru_1280.jpg`: «ЗАПИСЬ · 2026-11-13 · к…», so the code is cut;
  - on the site the note ends «Change them in a live run.» with no button or link (`evidence/e5_site.log`, `note`).
- **Fix:** let the badge keep its width (`flex: none`; shorten the title first). On the site, append the quick-start
  link («run lfphys locally → how») as the start page does.

### F12 (nit): server-only addresses on the site give raw errors

- **Where:** `player.js:69, 79`.
- **Evidence:** `evidence/e5_site.log`:
  - `/lfphys/run.html?id=20261111-170830-v04-2ca9` → «Run not found: Unexpected token '<', "<!DOCTYPE "... is not
    valid JSON»;
  - `/lfphys/run.html` → «No run given: /run?id=…» (a server address on the site).
- **Fix:** in static mode, any `?id=` or empty query says «This site plays recordings; runs are computed by a local
  server» with links to the start page and the quick start.

### F13 (nit): a malformed hash breaks the whole start page

- **Where:** `js/start.js:85` `decodeURIComponent(location.hash…)` runs inside `load().then(...)` (`start.js:586`).
- **What is wrong (code read, not run):** an address such as `/#%E0` throws `URIError`, so the catch shows «Catalogue: URI malformed»
  instead of the page. In the `hashchange` handler it throws uncaught.
- **Fix:** wrap the decode in `try` and fall back to the raw hash.

### F14 (nit): gaps in the two browser tests

- **Where:** `tests/browser/record_mode.mjs`, `start_page.mjs`.
- **What is wrong:**
  - `record_mode.mjs` «the set-up is read-only» is `every(disabled)` over `#left .ctl` controls, so it passes
    vacuously for worlds without live controls (u38, r11).
  - It does not check the views' own buttons (F2), the title (F3), 390 px (F1), the old `?rec=v04_…` link that the
    README promises, or the no-local-recording path (F5).
  - `start_page.mjs` has no keyboard or focus check (F7). It ends its live run with `POST /api/runs/<id>/stop`, a route
    the owner removed (2026-10-28: "there is no stop").
- **Fix:** add these checks; finish the run as the other scripts do, or leave it to suspend.

## What was checked and found fine

- [useful] Home, School, University, Research and Laboratories at 1280 and 390 px in EN and RU, server and site (40
  screenshots): no horizontal scroll, no page or console errors, page titles per audience in the viewer's language.
- [useful] Rule 16:
  - audience first, framed as learning materials; research says «hypothesis» on every card, with its question and prior
    art;
  - school shows an honest «Ready: 0 of 45», the AB1 items next, and nothing startable;
  - school cards have no «▸ More»;
  - university folds «▸ More», research opens it;
  - on the site: only «▷ Watch the recording», and «Compute live or change the set-up: run lfphys locally → how».
- [useful] The site under `/lfphys/`:
  - every link is `/lfphys/…` or `#…`, with no request outside the sub-path and none to `/api/`;
  - the back link of a recording returns to `/lfphys/?lang=ru#university/u34_orbits` with the card focused;
  - «My runs» and «⚙ Devices» are absent on the site;
  - «Licence» goes to `legal.html`.
- [useful] The server at `/`: `/`, `/runs`, `/run`, `/settings`, `/legal`, `/api/audiences`, `/api/planned`,
  `/api/recordings`, `/recordings/<w>/index.json` and `/images/<id>.jpg` all answer 200. `/recordings/../viz.py` gives
  404.
- [useful] Aliases:
  - `/viz/v02_double_slit/view.js` → 301 to `u32` (query kept);
  - `/api/viz/v02_double_slit` → the new entry;
  - `POST /api/runs {viz: "v04_orbits"}` starts `u34`;
  - `/run?rec=v04_orbits/mercury` and `v02_double_slit/young` play on the server and on the site (`aliases.json`).
- [useful] Old records:
  - 8 records from before the rename list under their new ids and open with their views and the "recorded before the
    translation" note;
  - v04 and v02 resumed with ⏺ (frames 405 → 428, 339 → 373, state running, no resume error);
  - `evidence/e6_old_records_resume.log`.
- [useful] On a recording:
  - no WebSocket and no non-GET request;
  - ⏺, ☆ and ⚙ are hidden;
  - the left panel's controls are disabled (u32, u31, u39);
  - «▶ Compute this scenario live» is present on the server and absent on the site;
  - the badge carries the date and code;
  - «About the recording» and «Download the recording (.lfrec.gz)» with the site-relative path;
  - the remaining centre controls (screen filter, frame, camera, slice layer) are display-only.
- [useful] The CSV on a recording is built in the browser; its time-column header says «from the recording: every frame /
  one frame in k» (code read; the integrator's `record_mode` runs also exercised it).
- [useful] Registry:
  - `check()` refuses a wrong prefix, an unknown section, `ui` against the audience, a missing teaser, courses,
    question, prior art or status, recordings outside the limits, unknown script commands, and modified physics in a
    school world;
  - `ALIASES` resolve, and no alias equals a folder (`test_site_registry.py`, `test_aliases.py` read).
- [neutral] DESIGN departures:
  - no «By course» toggle at university (recorded in STATUS V51 (b));
  - on the server the recording button is never grey (see F5);
  - `/api/audiences` was added instead of hard-coded labels: reasonable.
- [useful] The quick-start links: `README.md#quick-start` and `README.ru.md#быстрый-старт` exist; the default branch is
  `main`.
- [useful] Language: no Cyrillic in EN and no untranslated msgid in RU on the pages walked. The glossary is followed on
  the start page («Лаборатории», «перебор» not used here, «затравка»), and the labels match `visualizations/README.ru.md`
  («▶ Рассчитать вживую», «▷ Запись м:сс», «ЗАПИСЬ · дата · код», «О записи»), except F5's «кнопка серая».
- [neutral] The first `/api/viz` after a server start takes 1.2 s (`code_hash_cached` over 21 worlds), then 13 ms.
