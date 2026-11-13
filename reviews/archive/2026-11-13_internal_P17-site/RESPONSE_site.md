# Response to review P17-site: the recorder, the static site, its CI and the generated README

**Responder:** PA, the processing agent for the site and the recorder (container prefix `lf-pa2-`, private port 8683).
It wrote neither the review nor the code under review. **Date:** 2026-11-13.

**Scope.** Every finding of this review (F1–F13), the review's two out-of-scope notes, and the start-page review's F12
(server-only addresses on the site), all under the integrator's decisions D1–D8 (the processing brief). The start page
and the player are PB's (`../2026-11-13_internal_P17-start-page/RESPONSE_start-page.md`). The player's side of the
phone layout (D8), the unknown recording's message (D4) and the start-page F12 text are PB's code; this part tests them
on the built site.

**Counts:** 13 findings: 12 fixed, 1 partly (F10: the text is fixed, the thinning of snapshots is not built); none
rejected. The engine needed no change: `lfphys.core.backend.reset_used()` already existed.

**Environment.** Image `lfphys-viz`, CPU (`LFPHYS_NO_GPU=1`), containers `lf-pa2-*` with `--memory` ≤ 12g, the worktree
mounted read-only for tests. The site was built under `/lfphys/` into scratch and served by `python:3.11-slim`
`http.server` on 127.0.0.1:8683. Playwright 1.58.2 Chromium. The shared server on 8479 and the owner's copy were not
touched.

| # | finding | outcome | where | test |
|---|---|---|---|---|
| F1 | `backend.used` leaks from one recording into the next | **fixed** [error in earlier]: `record()` calls `backend.reset_used()` before `configure({})`, so a header names this recording's own kernels | `site/record.py` | `test_recorder.py::test_a_recording_is_byte_identical_alone_or_after_another_world` (records another world first and plants a fake kernel in `backend._USED`; the header must not name it and the bytes must be equal) |
| F2 | every frame carries the recorder's `cpu_ms` | **fixed** (D6): `emit()` drops `cpu_ms` and `speed_actual` (both from the runner's clocks) from every recorded frame; the CPU time of the whole recording stays the index entry's `cpu_s`. `RECORDER_VERSION` = 2 | `site/record.py`, `site/sitelib.py`; `RULES.md` §9 and `site/README.md` now say "the same bytes for the same spec and code", which holds | the same test (no frame holds a `FRAME_TIMING` key; two recordings are byte-identical); on the real worlds see "Re-recording" below |
| F3 | the key covers neither the recorder nor the image's dependencies | **fixed**: `sitelib.recorder_hash()` = sha256 over `site/record.py`, `docker/requirements.lock`, `docker/Dockerfile` and the budgets that decide the thinning (`BUDGET` file and world, `MIN_KEPT_FPS`); it is part of `spec_key` and of each world's plan (`recorder_hash` in the index). `RECORDER_VERSION` stays for a deliberate format change | `site/sitelib.py`, `site/record.py` | `test_code_hash.py::test_the_key_covers_the_recorder_its_budgets_and_the_images_dependencies` (an edit of each file, of `BUDGET`, of `MIN_KEPT_FPS`, of the version changes the key; the same bytes keep it) |
| F4 | nothing stops a failed check or failing physics tests | **fixed** (D5): (1) a recording fails when a check of the world **ends** failed, judged as the player judges it (`ok`, else `rel` against `tol`; `info` and `expected` do not fail); a ✗ corrected later is logged as a note; (2) each index entry counts the checks' last states, `checks: {ok, failed, expected, info, na}`, and `check.py` fails a site whose entry counts a failed one (or has no count: an old recording); (3) the workflow runs `viz-tests` (the whole visualizations suite in three shards) and `engine-tests` (the engine's suite) in parallel with `check`; `record` needs all three | `site/record.py`, `site/check.py`, `site/ci/pages.yml` | `test_recorder.py::test_a_check_that_ends_failed_fails_the_recording`, `::test_a_check_failed_on_purpose_or_corrected_later_does_not_fail`; `test_site_build.py::test_the_check_fails_a_recording_with_a_failed_check_and_warns_on_extras` |
| F5 | `check.py` and the smoke test miss the module graph | **fixed**: `check.py` requires `viz/<id>/view.js` for every catalogue world and `images/<id>.jpg` for every named `picture`, and scans `static/**/*.js` and `viz/**/*.js` for absolute server addresses in string literals (`/api`, `/run`, `/runs`, `/settings`, `/legal`, `/recordings`, `/images`, `/ws`; comments left out; `/static/` and `/viz/` are the import map's). `site_smoke.mjs` plays **every** recording of `api/recordings.json` in each language, plus an old id: the player's frame count must be the index's `frames` and `goTo(poster_frame)` must show `poster_t`; the existing request, page-error and console checks cover them. `ALL_RECS=0` keeps the quick run | `site/check.py`, `tests/browser/site_smoke.mjs` | `test_site_build.py::test_the_check_catches_a_missing_view_picture_or_absolute_address_in_a_script` (the reviewer's mutations: a missing view, a missing picture, `fetch("/api/runs")` in `start.js`; plus the scanner's unit cases); the smoke run below |
| F6 | the RU README opens the site in English | **fixed** (D7), effective when links are shown: `readme.py` adds `&lang=<code>` to every site link in a README of a language other than the default; the player still does not follow the browser's language | `site/readme.py` | `test_site_registry.py::test_the_readme_links_to_the_site_follow_its_setting[published=True]` (every recording linked once; `&lang=ru` in RU, no `lang=` in EN) |
| F7 | 44 dead links until the first deployment | **fixed** (D3): `visualizations/site/site.json` = `{"published": false, "url": "https://ildar-idrisov.github.io/lfphys/"}`. While false, the generated catalogue has no link to the site; each world names its recordings without links (so the *(modified physics)* flag stays visible), and one line at the top says, in each language, «The public site with the recordings is being prepared; until then the recordings play on a local server (Quick start)». `published: true` plus `site/readme.py` brings the links back. The server's `/api/recordings` and the site's `api/recordings.json` carry `published` (agreed shape with PB: `{worlds, site, published}`), and the player falls back to the public site only when it is true (D4). The hand-written paragraphs of both root READMEs and `site/README.md` say this instead of "the links do not open" | `site/site.json`, `site/readme.py`, `server/lfviz/app.py` (`site_setting`, `recordings_list`), `site/check.py`, `README.md`, `README.ru.md`, `locales/ru.json` (one msgid) | `test_site_registry.py::test_the_readme_links_to_the_site_follow_its_setting` (both states × both languages), `::test_the_committed_readme_matches_the_committed_site_setting`; `test_site_build.py::test_the_site_setting_reaches_the_player_and_the_check` (`site_setting`, `LFVIZ_SITE_URL` overriding on the server only, an unreadable file meaning not published, `check.py` failing when `api/recordings.json` disagrees with `site.json`) |
| F8 | the workflow deploys on every push to `main` | **fixed** (D2): `deploy` runs only `if: github.event_name == 'workflow_dispatch' && inputs.deploy` (a new boolean input, default false); a push checks, records and builds. Written in the workflow's header and in `site/README.md` | `site/ci/pages.yml`, `site/README.md`, `RULES.md` §9 | actionlint (below) |
| F9 | a kept old entry gets the index's new `code_hash`, `version`, `made` | **fixed**: each entry carries its own `version`, `code_hash` and `made`; an entry not recorded now is kept only when its key is the current one (so its code and version are today's), else it is dropped with its file and the log says so. PB's player prefers the entry's fields (agreed through the integrator) | `site/record.py` | `test_recorder.py::test_a_kept_old_entry_is_current_or_dropped` |
| F10 | r12's reason in the wrong unit; its snapshots are not thinned | **partly**: the text now says "~5 per **played** second". Thinning `wave` snapshots with the frames is not built: it is the review's optional part, r12 stays within the hard limit (8.0 MB of 10 MB) with the integrator's accepted exception, and it needs the player to show the latest snapshot at or before the cursor (PB's player). It stays open as `STATUS.md` V51 (a) | `site/sitelib.py` | — |
| F11 | a seeded stochastic recording is not what a live run with that seed shows | **fixed** (documents): `RULES.md` §9 and `site/README.md` say that a recording is one realisation and a live run with the same seed draws another with the same statistics. The sentence in the player's passport is not added (PB's file; optional) | `RULES.md` §9, `site/README.md` | — |
| F12 | small CI points | **fixed**, each: `python:3.11-slim` and the Playwright image pinned by `@sha256:` (`env.PY_SLIM`, `env.PLAYWRIGHT`; digests from `docker image inspect` of the images pulled by tag, the date in the header); `rerecord` and the world go to the shell through `env:` (`RERECORD`, `WORLD`, `SHARD`); `actions/cache/restore` + `actions/cache/save` (same pinned SHA), so a forced re-record is saved under its key; `CITATION.cff` in `push.paths`; `test_code_hash.py` in the check job; `deploy` has `timeout-minutes: 20` | `site/ci/pages.yml` | actionlint (below) |
| F13 | the site ships entries the registry does not ask for | **fixed**: `build.py` copies only the entries the registry's plan names (and says what it left out); `check.py` warns on an index entry or a file in `recordings/<world>/` outside the plan | `site/build.py`, `site/check.py` | `test_site_build.py::test_the_check_fails_a_recording_with_a_failed_check_and_warns_on_extras` |
| out of scope | the player on a phone | PB's (D8); screenshots there | — | — |
| out of scope | an unknown recording id says «No recording for this version» | PB's player code (D4: «No such recording», with a link to the start page). `site_smoke.mjs` now checks it on the site in EN and RU | `tests/browser/site_smoke.mjs` | smoke run |
| start-page F12 | server-only addresses on the site give raw errors | PB's player code (msgid «This site plays recordings; runs are computed by a local server», with links to the start page and the quick start). `site_smoke.mjs` checks `run.html?id=…` and a bare `run.html` in EN and RU: the text through the catalogue, no "Unexpected token", no "/run?id=" | `tests/browser/site_smoke.mjs` | smoke run |

Also asked by the integrator during processing: `app.audiences_list()` passes the audiences' `picture` (start-page
F10; `test_code_hash.py` and `test_site_build.py` compare it), and `test_site_registry.py::test_the_audiences_tiles_name_their_own_worlds`
asserts `registry.check_audiences() == []`.

## Re-recording

The key changed for every recording: `RECORDER_VERSION` 2, the recorder's hash (F3), and the code of both processing
agents (PB's `registry.py` and player edits are inside `code_hash`). After both agents' code was final, all 17 worlds
(44 recordings) were recorded again on the CPU in three containers `lf-pa2-rec-g1..g3` (`--memory=12g`), into scratch,
then put into `visualizations/recordings/` in one step.

| # | result | status |
|---|---|---|
| R1 | `plan.py`: 44 recordings in 17 worlds, 44 present, 0 stale, 0 missing; every recording within its hard limit; r12 6.62 / 8.03 MB and u38 6.43 MB over target as accepted (unchanged) | [useful] |
| R2 | the checks' last states over all 44: ok 267, failed 0, expected 0, info 57, na 42; no check flipped from ✗ during a recording | [useful] |
| R3 | determinism on the real worlds: u32 (stochastic; 3 recordings), u34 (3) and u42 (3, uses the engine's kernels), each recorded alone in a fresh container, are byte-identical to the same recordings made in a group run after other worlds (`cmp`) | [useful] |
| R4 | the 17 demonstration posters remade once from the new recordings (`site/posters.mjs` on a private server, port 8683; the laboratories' posters kept, their keys unchanged); 58–130 kB, 1200×635; `docs/images/posters.json` holds the new keys | [neutral] |

## Tests (2026-11-13, Docker `lfphys-viz`, CPU)

| # | test | result | status |
|---|---|---|---|
| T1 | my four files and `test_i18n.py` (`test_site_registry`, `test_recorder`, `test_site_build`, `test_code_hash`, `test_i18n`), after the posters | 200 passed | [useful] |
| T2 | the full visualizations suite in three shards: `tests/` · `u3*/` · `u4*/ r1*/ p0*/` | 358 passed · 397 passed, 1 skipped · 458 passed, 3 skipped | [useful] |
| T3 | the engine's suite (`lfphys/`, as the CI's `engine-tests` job runs it) | 1994 passed, 23 skipped | [useful] |
| T4 | `site/build.py` + `site/check.py` on the 44 new recordings, base `/lfphys/` | 44 of 44 present; 0 failures; 4 accepted warnings; 53.0 MB | [useful] |
| T5 | `site_smoke.mjs`, EN and RU, the site served under `/lfphys/` by `http.server` (127.0.0.1:8683), every recording played | 68 checks, all passed: in each language 45 recordings (44 + the old id `v04_orbits`) with the index's frames and `poster_t`; the unknown id «No such recording» / «Такой записи нет» with the start page's link; `run.html?id=…` and `run.html` with «This site plays recordings; …»; no request outside the sub-path, no failed request, no page or console error | [useful] |
| T6 | the same smoke test, quick (`ALL_RECS=0`), after the rebuild with the new posters | all passed | [useful] |
| T7 | `actionlint` 1.7.7 (with shellcheck) on `site/ci/pages.yml` | no findings | [useful] |
| T8 | the reviewer's mutations of F5 and F13 (in `test_site_build.py`) | each now fails or warns as it should | [useful] |
| T9 | D8 on the built site: `run.html?rec=u32_double_slit/young` and `u34_orbits/rosette` at 390×844 and 1280×860, EN and RU (PB's layout) | 8 of 8: no horizontal scroll (`scrollWidth` = viewport), the view full width at 390 px, the badge in the bar, no page error. Screenshots: `scratchpad/landing/proc_pa/shots_d8/d8_<world>_<rec>_<390\|1280>_<en\|ru>.png` | [useful] |

## Open points for the integrator

- **F10**: thinning r12's `wave` snapshots needs the player (PB's) to show the latest snapshot at or before the cursor;
  it stays `STATUS.md` V51 (a).
- **F11**: the passport sentence (PB's `player.js`) is optional; the documents carry it.
- **D8 screenshots** (PB's layout, seen here): at 390 px a view's own controls come before its picture, so in u32 the
  picture starts about 450 px down; a view's label at the canvas's left edge («плоская волна») is cut and a stray orange
  dot sits at the left edge. In u34 the view's buttons «толчок +5 %», «−5 %», «↻ запуск» look enabled on a recording
  (start-page F2, PB's).
- **Dockerfile** `FROM python:3.11-slim` is not pinned by digest (not my file). The workflow pins the image it pulls
  itself; the recorder's hash covers the Dockerfile's text, not the pulled base image.
- **When the owner publishes**: set `"published": true` in `visualizations/site/site.json`, run `site/readme.py`, and
  start the workflow by hand with `deploy: true`.
