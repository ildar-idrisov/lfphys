# Review P17-site: the offline recorder, the static site, its CI and the generated README (2026-11-13)

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the code under review) |
| Date | 2026-11-13 |
| Scope | `git diff f3d137d..1f4ceac`, the site part: `visualizations/site/` (`record.py`, `plan.py`, `build.py`, `check.py`, `readme.py`, `sitelib.py`, `posters.mjs`, `ci/pages.yml`); the server routes `/recordings`, `/api/recordings`, `/images`, `/api/audiences` (`server/lfviz/app.py`); `registry.code_hash`/`SERVER_ONLY`; the generated catalogue of `README.md` and `README.ru.md`; `docs/images/`; `tests/browser/site_smoke.mjs`; `test_recorder.py`, `test_site_build.py`, `test_site_registry.py`, `test_code_hash.py`. |
| Not in scope | The start page and the player's recording mode (other reviewer), except one-line notes at the end. |
| Environment | `lfphys-viz` image, CPU (`LFPHYS_NO_GPU=1`), worktree mounted read-only. Site built into a scratch folder with `--base /lfphys/` from `visualizations/recordings/` (44 recordings, made 2026-11-13) and served by `python:3.11-slim` `http.server` from a parent folder (sub-path `/lfphys/`). Private live server `lf-rv-s-viz` (port 8681, docker network only, runs in scratch). Playwright 1.58.2 Chromium. The shared server on 8479 and the owner's copy were not touched. |

Evidence is in `evidence/`: the outputs `eNN_*.out` (Python), `bNN_*.out` (Chromium), `cNN_*.out` (CI), the scripts in
`evidence/tools/`, and two phone screenshots.

## Summary

There are 13 findings: **0 errors**, **7 should-fix** and **6 nits**. There is also one out-of-scope note that looks
should-fix.

What works, measured:
- **Tests.** The four test files pass (99 tests).
- **Build and check.** The build of the real recordings has 44 of 44 present. `check.py` gives 0 failures and 4
  accepted warnings, and the site is 53 MB.
- **Smoke test.** The smoke test passes under `/lfphys/` in EN and RU.
- **Every recording plays.** I played all 44 recordings, and the old id `v04_orbits`, under the sub-path. Each one:
  - loads in under 0.7 s;
  - has exactly the index's frame count;
  - lands on `poster_t` exactly at `poster_frame`;
  - makes no request outside `/lfphys/` and no failed request.
- **Fidelity to live.** A recording matches a live run of the same preset and seed, as far as a different frame clock
  allows. u34 has the same 22 events, apsides and checks in the same order. u37 has the same sequence. u32 has the same
  statistics: about 570 hits at t = 0.6 s in both.
- **Determinism.** Re-recording gives the same physics, message by message.
- **Routes.** No probe of the new routes for path traversal got through.
- **The workflow.** The pinned action SHAs are the tagged commits. `actionlint` is clean, and the permissions are
  minimal.
- **The README.** It lists each of the 21 worlds exactly once in both languages, and every link target exists.

What is weak:
1. **The recording files.**
   - They carry state that leaks from the recorder process (F1) and CPU timings (F2), so they are not reproducible
     byte for byte, contrary to `RULES.md` §9.
   - Their key does not cover the recorder itself or the image's dependencies (F3).
2. **Gates before publishing.**
   - Nothing stops a recording with a failed check, or code with failing physics tests (F4).
   - `check.py` and the smoke test do not cover the module graph, so a missing view or vendor module ships (F5).
3. **The README links to the site.**
   - The RU README opens the site in English (F6).
   - All 44 links are dead until the first deployment (F7).

## Findings

### F1. The header's `backend.used` leaks from one recording into the next (should-fix)
- **Where:** `visualizations/site/record.py:239-259`. The header takes `backend.used` from the process-global
  `lfphys.core.backend._USED` (`sim.py:156`). The recorder never calls `backend.reset_used()`
  (`lfphys/lfphys/core/backend.py:421`), although a worker starts as a fresh process.
- **Evidence:** `evidence/e06_header_backend_used.out`, the header of every recording made by one `--all` process:
  ```
  u37_bell_test chsh used: ['gravity.kerr_shadow', 'optics.angular_spectrum', 'relativity.raytrace'] …
  u34_orbits rosette used: ['quantum.split_operator'] …
  u31_light_travel sun_earth used: ['quantum.split_operator'] …
  ```
  - A Bell test does not call the Kerr ray tracer, and the orbits do not call the split-operator kernel. A live run of
    u34 has `used: {}` (`evidence/e05_live_vs_rec_u34_orbits.out`, line `HEADER keys differing: {'backend': …}`).
  - The same world recorded alone gives another header (`e07_rerecord_diff.out`: `('header', ('backend',), ())`).
  - So a recording made locally with `--all` and one made per world in CI differ. Even in CI, the 2nd and 3rd
    recordings of a world inherit the kernels of the 1st.
- **What is wrong:** the metadata of a published record is false (the passport of a downloaded `.lfrec` would list the
  wrong kernels), and the content depends on what the process recorded before.
- **Fix:** call `backend.reset_used()` (and `configure` with the same settings) at the start of `record()`. Better still,
  run each recording in a fresh subprocess, as the server runs each run in a worker. Then add a test that a world's
  recording is byte-identical whether it is recorded alone or after another world.

### F2. A recording is not byte-reproducible, because every frame carries the recorder's `cpu_ms` (should-fix)
- **Where:**
  - `record.py:276-281` passes the measured process time to `Runner._frame`;
  - `RULES.md` §9 claims "no wall-time budget (the same file on any CPU)";
  - `site/README.md` claims "the result is the same on any CPU".
- **Evidence:** `evidence/e07_rerecord_diff.out` re-recorded u32 in a fresh container. Compared message by message with
  only `cpu_ms` excluded, there were no differences, yet the files differ:
  ```
  u32_double_slit young files differ msgs 3315 3315 diff kinds: {}
  ```
  `grep -n cpu_ms visualizations/player/js/*.js` finds nothing: the player never reads it.
- **What is wrong:**
  - every re-recording makes a new `sha256`, file name and Pages URL for the same content;
  - two recordings cannot be compared by hash (CI against local, or a check that a re-record changed nothing);
  - the documents claim a property that does not hold.
- **Fix:** write `cpu_ms: 0` (or leave the key out) in recorded frames. Keep the measured CPU time only as the index's
  `cpu_s`. Then add a test that two recordings of the toy world are byte-identical. Together with F1, the
  documents' claim then holds.

### F3. A recording's key covers neither the recorder nor the image's dependencies (should-fix)
- **Where:**
  - `sitelib.py:61-69` (`spec_key`);
  - `registry.py:266-283` (`code_hash`: the world folder, `lfviz/*.py`, `lfphys/lfphys/*.py`);
  - `sitelib.py:27` (`RECORDER_VERSION = "1"`, raised by hand).
- **Evidence:** reading the code. `site/record.py`, `site/sitelib.py`, `visualizations/docker/Dockerfile` and
  `visualizations/docker/requirements.lock` are not hashed.
  - The budgets (`BUDGET`, `MIN_KEPT_FPS`, `STRIDES`) decide the stride.
  - `DROP` decides which messages are kept.
  - The locked numpy/scipy versions decide the numbers.
  - None of these is part of the key.
- **What is wrong:**
  - a change of the recorder or of a dependency leaves every recording `present`;
  - the CI cache (`rec-<world>-<key>`) then serves recordings made by the old recorder or the old libraries;
  - nothing reminds the editor to raise `RECORDER_VERSION` (`test_code_hash.py` does not cover it).
- **Fix:** add `sha256(record.py + sitelib.py)` and `sha256(requirements.lock + Dockerfile)` to `spec_key`, or derive
  `RECORDER_VERSION` from them. Then test that an edit of `sitelib.BUDGET` changes the key.

### F4. Nothing stops a recording with a failed check, or code whose physics tests fail, from being published (should-fix)
- **Where:**
  - `record.py:225-237, 284-285`: a recording fails only on an `error` message or an exception;
  - `ci/pages.yml:67-71`: the `check` job runs only `test_site_registry.py`, `test_i18n.py`, `test_recorder.py` and
    `test_site_build.py`, not the worlds' and the engine's tests.
- **Evidence:** `evidence/e11_check_status_in_recordings.out`.
  - Today no recording has a `check` with `ok: false` (only `True` or `None`), so this is latent.
  - But nothing in `record.py`, `check.py` or the workflow looks at `ok`.
  - A regression that turns a check red, or breaks a physics test, would be recorded and deployed with a red ✗ on the
    public site.
- **What is wrong:** `AGENTS.md` rule 5 asks that physics be verified before use. The public site is the most visible
  use of the physics.
- **Fix:**
  - make `record()` fail, or at least list as a problem, any `check` message with `ok is False`;
  - write the counts of checks (ok, failed, info) into the index entry, and let `check.py` fail on a failed one;
  - in `pages.yml`, run the whole suite (`python3 -m pytest -q tests/ ../lfphys/tests/` or the project's usual set)
    before recording.

### F5. `check.py` and the smoke test do not catch a missing view, vendor module or absolute address in JS (should-fix)
- **Where:**
  - `check.py:64-112`: absolute addresses are checked only in the three HTML pages, completeness only for the catalogue,
    locales and recordings;
  - `tests/browser/site_smoke.mjs:69-74`: one recording plays, u34's first.
- **Evidence:** `evidence/e09_check_mutations.out`. I mutated copies of the built site and rebuilt the manifest, as a
  regression of the build would produce it:
  ```
  absolute /api and /run in static/js/start.js (manifest rebuilt): exit 0; []
  viz/u34_orbits/ (the view module) missing, manifest rebuilt: exit 0; []
  images/u34_orbits.jpg missing while api/viz.json names its picture (manifest rebuilt): exit 0; []
  static/vendor/.../OrbitControls.js missing (manifest rebuilt): exit 0; []
  static/locales/ru.json missing: exit 1; ['FAIL static/locales/ru.json is missing']
  ```
  - `build.py` already drops a folder the player fetches from at run time. `SKIP` contains `legacy`, and
    `player/js/i18n.js:166` fetches `static/legacy/ru-2026-11-12.json` when a record holds plain Cyrillic strings.
  - Today no recording triggers that fetch (no failed request in `b02`), but this is exactly the kind of gap the check
    does not see.
  - `evidence/b02_every_recording_under_subpath.out` shows that playing **all** 44 recordings under the sub-path costs
    0.1–0.7 s each.
- **Fix:**
  1. In `check.py`, require `viz/<id>/view.js` for every catalogue world, and `images/<id>.jpg` for every `picture`.
  2. Scan `static/**/*.js` and `viz/**/*.js` for absolute `"/(api|run|runs|settings|legal|recordings|images)…"` literals
     outside `url()`.
  3. Have `site_smoke.mjs` (or a second script in the build job) play every recording of `api/recordings.json`. Fail on
     a frame count that differs from the index, any request outside the base, any failed request, or any page error. My
     `evidence/tools/allrecs.mjs` does this.

### F6. The RU README's «Смотреть на сайте» links open the site in English (should-fix)
- **Where:**
  - `visualizations/site/readme.py:155`: `[{label}]({SITE_URL}run.html?rec={vid}/{rec['id']})` is the same URL in every
    language;
  - the player chooses `?lang=`, then the tab's link language, then the stored choice, then English
    (`player/js/i18n.js:59-70`), never the browser's language.
- **Evidence:** `evidence/b03_ru_readme_link_in_ru_browser.out`. I opened a README.ru link in a `ru-RU` browser
  (`navigator.language = ru-RU`) with no stored choice:
  ```
  {"lang":"en","nav":"ru-RU","head":"← University\n⇤\nThe double-slit experiment\n…"}
  ```
  `grep -c "lang=ru" README.ru.md` gives 0.
- **What is wrong:** a Russian reader of the Russian README lands on an English page. That breaks `AGENTS.md` rule 13
  (each document consistent in its language).
- **Fix:** for a language other than `i18n.DEFAULT`, `readme.py` appends `&lang=<code>` to every site link, and the test
  checks it. Do the same for any other site link in a localized document.

### F7. Once merged, the public README carries 44 dead links to a site that does not exist yet (should-fix; the owner decides the order)
- **Where:** the generated catalogue of `README.md`/`README.ru.md` (44 `https://ildar-idrisov.github.io/lfphys/run.html?rec=…`
  links), and `site/README.md` («until then the README's links to the site are dead»).
- **Evidence:** reading the code. The workflow is a draft, and deployment waits for the owner's go. A merge of
  `p17-landing` to `main` of the public repository therefore publishes the links before the site.
- **What is wrong:** a visitor of the public repository follows «▷ Watch on the site» and gets a 404 from github.io. The
  catalogue looks broken.
- **Fix:** let the owner choose one of these:
  - deploy the site in the same step as the merge;
  - generate the links only when a committed setting says the site is live (e.g. a `SITE_LIVE` constant next to
    `SITE_URL`), and until then show «site: coming» in every language.

### F8. Once activated, the workflow deploys on every push to `main` (nit; confirm with the owner)
- **Where:** `ci/pages.yml:26-36` (`on: push: branches: [main]` with `paths`) and `173-184` (`deploy`, unconditional).
- **Evidence:** reading the workflow.
- **What is wrong:** the owner's decision of 2026-11-13 is "deployment happens only on the owner's go". After the
  workflow is copied, every push that touches `visualizations/**` deploys at once.
  - That is acceptable if a push to `main` itself counts as the go (pushes already need it).
  - Otherwise the second go is lost.
- **Fix:** gate the deploy with one of these:
  - `if: github.event_name == 'workflow_dispatch'`, so a push only builds and checks;
  - a required reviewer on the `github-pages` environment.
  Write down which of the two the owner chose.

### F9. A kept old index entry gets the index's new `code_hash`, `version` and `made` (nit)
- **Where:** `record.py:389-411`. An entry not re-recorded (`--rec` subset, or a recording that failed now) is copied
  from the old index with its old `key`. The index's top level is rewritten with the current `code_hash`, `version` and
  `made`.
- **Evidence:** reading the code. The player's passport and badge read `ix.code_hash` and `ix.made`
  (`player/js/player.js:983-986`).
- **What is wrong:** on a local server, a stale file plays under a passport that names the current code and today's
  date. The site is protected only because `check.py` fails on the key.
- **Fix:** put `code_hash`, `version` and `made` in each entry (the player reads the entry's), or drop old entries whose
  key differs from the current one.

### F10. r12's accepted reason is wrong in its units, and the bulk of r12 is droppable snapshots the recorder cannot thin (nit)
- **Where:** `sitelib.py:48-52` («~5 per world second»), and `record.py:297-309` (only `frame` messages are thinned).
- **Evidence:** `evidence/e10_r12_mark180_anatomy.out`.
  - `wave` makes up 101 messages and 9.42 MB of the 12.6 MB stream; `frame` makes up 200 messages and 0.42 MB.
  - The world time spans 1.4·10⁻¹⁵ s, so it is about 5 snapshots per **played** second.
  - `mark180` is 8.04 MB gzip, within 20 % of the 10 MB hard limit.
- **What is wrong:**
  - the text is wrong;
  - the budget is near its limit, while the large messages are full-field snapshots that are as droppable as frames
    (each replaces the last).
- **Fix:**
  - correct the text;
  - optionally let a world declare snapshot message types that the recorder may thin with the frames (keep the first
    and the last), which would bring r12 to its target.

### F11. A seeded stochastic recording is not what a live run with the same seed shows (nit)
- **Where:** the recording's passport shows «Seed 1» (`player.js:987`), and `RULES.md` §9 «the same file on any CPU».
- **Evidence:** `evidence/e05_live_vs_rec_u32_double_slit.out`. With the same preset and seed, the live run's
  `detections` and screen counts differ from the recording's: the random draws follow the advance steps, which follow
  the frame clock. The statistics agree, e.g. `n_seg` 567 against 570 at t = 0.6 s in an earlier run. u37 (`pairs`,
  `cells`) is similar.
- **What is wrong:**
  - nothing is wrong with the physics;
  - a reader who presses «▶ Compute live» with seed 1 expects the same hits and gets another realisation.
- **Fix:** add one sentence in the passport or `RULES.md` §9: «a live run with this seed is another realisation: the
  random draws follow the frame clock».

### F12. Small CI points (nit)
- **Where:** `ci/pages.yml`.
- **Evidence:** reading the workflow; `evidence/c01_actionlint.out` is clean.
- **What is wrong, with the fix for each:**
  - `python:3.11-slim` and `mcr.microsoft.com/playwright:v1.58.2-jammy` are pulled by tag, not by digest, unlike the
    actions. Pin them by `@sha256:`.
  - `${{ inputs.rerecord || 'stale' }}` is interpolated into the shell (line 77). It is a choice input, but the safe
    pattern is `env: RERECORD: …` and `"$RERECORD"`.
  - With `force` (`--rerecord all`) the cache step is skipped, so the fresh recordings are never saved under their key.
    Save explicitly with `actions/cache/save`.
  - `push.paths` misses `CITATION.cff`. The site's `api/health.json` and the licence page carry the citation from it,
    so a version bump would not rebuild the site.
  - `test_code_hash.py` is not in the `check` job's list, although it guards the key the cache relies on.
  - `deploy` has no `timeout-minutes`.

### F13. The site ships index entries and files the registry does not ask for (nit)
- **Where:** `build.py:160-183` copies every entry of a world's index, and `check.py` iterates only the registry's
  recordings.
- **Evidence:** `evidence/e09_check_mutations.out` gives `an extra index entry the registry does not know: exit 0`.
- **What is wrong:** a recording whose spec was removed from `VIZ["recordings"]` stays on the site, unlisted, with a
  passport for a scenario the registry no longer offers.
- **Fix:** have `build.py` copy only the entries of the current plan, and have `check.py` warn on any index entry or
  file outside the plan.

## Outside the scope (one line each)
- **The player on a phone, on the site (looks should-fix).** At 390 px the side panels and the controls overlap the
  centre view of `run.html?rec=u32_double_slit/young`, and the double-slit picture is not visible. RU also scrolls
  sideways (`scrollWidth` 405 > 390). See `evidence/run_u32_phone_en.png` and `evidence/run_u32_phone_ru.png`.
- **The message for an unknown recording id on the site.** `run.html?rec=u34_orbits/nope` says «No recording for this
  version: record it locally or compute live». On the public site that names actions the visitor cannot take, and the
  cause is not a version (`b02`, last line).

## Checked and found fine
| # | check | result | status |
|---|---|---|---|
| R1 | `e01_tests.out`: `test_site_registry`, `test_recorder`, `test_site_build`, `test_code_hash` | 99 passed | [useful] |
| R2 | `e02_check_built_site.out`: `build.py` + `check.py` on the 44 real recordings, base `/lfphys/` | 44 of 44 present; 0 failures; 4 warnings, all `ACCEPTED` (r12 ×3, u38); 53 MB | [useful] |
| R3 | `b01_site_smoke.out`: `site_smoke.mjs` under `/lfphys/`, EN and RU | all passed; no request outside the sub-path; no API call or WebSocket | [useful] |
| R4 | `b02_every_recording_under_subpath.out`: every recording and the alias `v04_orbits/rosette` | all load (0.1–0.7 s); frames = index `frames`; `goTo(poster_frame)` gives `poster_t` exactly; no failed request; no page error | [useful] |
| R5 | `e05_live_vs_rec_u34_orbits.out`: rosette, live (15 s wall) against the recording | same 22 events, apsides and checks in the same order; frame t = 0 identical; later frames differ by the frame-time offset only | [useful] |
| R6 | `e05_live_vs_rec_u37_bell_test.out`, `…u32_double_slit.out` | same message kinds and counts (u37); u32 is a different realisation with the same statistics (F11) | [neutral] |
| R7 | `e07_rerecord_diff.out`: u32, u37, u34, u42 recorded again in fresh containers | the physics is identical message by message (the NaN-only "differences" are equal arrays); only the header (F1) and `cpu_ms` (F2) differ | [useful] |
| R8 | `e08_traversal.out`: 20 probes (`..%2F`, `%2E%2E`, `%5C`, double encoding, NUL, `posters.json`, aliases) | only the legitimate files are served; everything else gives 404; `/images` serves only image suffixes | [useful] |
| R9 | `c02_action_shas.out`: `git ls-remote` of the 8 pinned actions | every SHA is the commit its tag names | [useful] |
| R10 | `c01_actionlint.out`: actionlint 1.7.7 (with shellcheck) | no findings | [useful] |
| R11 | the workflow's safety | top-level `contents: read`; `pages: write`/`id-token: write` only in `deploy`; no `pull_request` trigger; nothing pushes; a failed record job skips its upload, so `check.py` fails and nothing deploys; containers have `--memory`; job timeouts 40/300/40 min | [useful] |
| R12 | `SERVER_ONLY`: does any worker-side module import `app` or `runs`? | none (`worker.py`, `sim.py`, `instruments.py`, `sweep.py`, `checkpoint.py`, `playground.py`) | [useful] |
| R13 | the engine and world folders: data files that `code_hash` would miss | only `lfphys/lfphys/locales/*.json` (texts, not physics) | [neutral] |
| R14 | the generated README, EN and RU | 21 worlds, each exactly once, in its one audience; 44 recording links, all to existing recordings; every picture and README link target exists; the quick-start anchor exists in both; no English in the RU link labels; research «Status: hypothesis» is enforced by `registry.check` | [useful] |
| R15 | `readme.py --check` and idempotence (in `e01`) | both READMEs are up to date | [useful] |
| R16 | posters: `docs/images/*.jpg` and `posters.json` | 21 posters, 1200×635, 31–130 kB; every key equals the current recording key. Seen myself: u32 fringes with the histogram on the expectation; u42 the shadow with the critical curve; u44 the primary bow near 42° and the secondary bow outside it | [useful] |
| R17 | `check.py` fails where it must (`test_site_build`, `e09`) | a changed file, a missing recording, a stale key, a budget, the wrong base, a missing locale | [useful] |
| R18 | thinning (`test_recorder`, reading `pack`/`thin_to`/the world loop) | correct: poster, first and last frame kept, every other message kept, at least 2 frames per played second. No real recording is thinned today (all stride 1), so the player's stride > 1 path has no browser check | [neutral] |
| R19 | the recording's view controls on the site (u32) | disabled in recording mode | [useful] |
| R20 | desktop 1280 px, EN and RU: `run.html?rec=…`, the start page, `legal.html` | no horizontal scroll; recording badge, read-only notice and checks present | [useful] |
