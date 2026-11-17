# Response to review R-F (EX1-atlas): the atlas framework, the live point, the site's build and check, CI

**Responder:** QF, the processing agent for the framework and the site (containers `lf-qf-*`, private port 8705). It
wrote neither the review nor the code under review. **Date:** 2026-11-17.

**Scope.** Every finding of this review (F1–F14), under the integrator's decisions of the processing brief: D13 (live
points, server side), D14 (a constructor's refusal), D15 (CI). Also processed here, as they touch the same files: R-P F9
on the server side (D11), R-P F8 on the server side (D13: the point's own key, code and time), and the registry's lab-law
fields of D4 (see `RESPONSE_framework.md` in the folders of R-E, R-P and R-W). The player's side of D11 and D13 (merging
only with the named base, the passport, the greyed screens) is QP's (`RESPONSE_player.md`).

**Counts:** 14 findings: 13 fixed, 1 partly (F10: the builders' device is fixed here; the Dockerfile's `FROM` pin is not
in this part's files and is left to the integrator, below). None rejected.

**Environment.** Image `lfphys-viz` (Python 3.11), CPU (`LFPHYS_NO_GPU=1`), containers `lf-qf-*` with `--memory` ≤ 8g.
Other agents edited the engine and the worlds at the same time, so the test runs used a read-only snapshot of the
working tree (rsync without git, recordings and runs) to keep the code hash still during a run. Node tests in
`node:24@sha256:e7add2a4…` (24.22.2); `actionlint` 1.7.7. A private server `lf-qf-srv` on 127.0.0.1:8705 with an empty
`LFVIZ_RECORDINGS` for the probes; port 8479 was not touched.

## Contracts agreed during processing (sent to the integrator, QP and QW)

* **Live point (D13).** Response headers `X-LF-Source` (`atlas` | `cache` | `computed`), `X-LF-Key` (the point's key),
  `X-LF-Code` (the world's code hash that computed it), `X-LF-Made` (ISO 8601 in UTC: a cached point's original time, an
  atlas's build time). Every packed point's delta header (live and site builds) names its base: `"$base"` = the hex
  sha256 of the base file, which every manifest already has as `base.sha256`. A player merges only when they are equal;
  otherwise it posts the same request with `"full_header": true` and gets the same point (same key) with a full header,
  no `$`-keys. `ATLAS_VERSION` is 2.
* **Expected keys (D11).** `GET /api/recordings` and the site's `api/recordings.json` carry `expected: {<world>:
  {version, code_hash, recordings: {id: key}, atlases: {id: key}}}` for every world with recordings, from the code on
  that server (`lfviz.app.expected_keys`). A server's player takes the site's atlas only when the site is published, the
  version is the same and the site's atlas key is the expected one; the same comparison shows a stale local atlas.

## Findings

| # | finding | outcome | where | test |
|---|---|---|---|---|
| F1 | the live cache's key uses a hash computed once per process; the point's process runs the code on disk | **fixed** [error in earlier] (D13). `registry.code_hash_current` (also the old name `code_hash_cached` and the catalogue's `code_hash`) is cached by the code files' paths, sizes and `mtime_ns`: an edit, a new file or a removed one is seen at the next call; the files are only listed and stat'ed when nothing changed (all 25 worlds in 0.12 s). The server keys a request with it, `local_point` compares the local atlas's key with it. The point's process hashes the code itself (world code, recorder, `atlas_live.py`) **before and after** it computes; the point is cached under the key of the code it ran, and a point computed while the code changed is neither cached nor served (`503` «the server's code changed while the point was computed: try again»), its new base not kept | `server/lfviz/registry.py`, `server/lfviz/atlas_live.py` | `test_atlas_live.py::test_the_cache_follows_the_code_on_disk` (the reviewer's e08 on a temporary copy of the toy world: an edit between two requests is computed by the edited code under its own key; after the revert the first code's point comes from the cache, without the edit's mark); `::test_a_point_computed_while_the_code_changed_is_not_kept`; `test_code_hash.py::test_the_current_hash_sees_an_edit_a_new_file_and_a_removed_one` |
| F2 | a live point's header is a delta against the server's base, merged with the local (maybe stale) base; the passport names the atlas | **fixed, server side** (D13): `$base` in every delta header (`headless.Packer(base_sha=…)`, `site/atlas.py`, the live points), `full_header: true` (`atlas_live.with_full_header`: the header merged with its base, the rest of the stream byte for byte; for a point from the cache, the local atlas or a fresh computation), the headers `X-LF-Code` and `X-LF-Made`; `expected` in `/api/recordings` lets the player see a stale local atlas (D11). The player's merge rule and passport are QP's | `server/lfviz/headless.py`, `server/lfviz/atlas_live.py`, `server/lfviz/app.py`, `site/atlas.py`, `site/sitelib.py` (`ATLAS_VERSION` 2) | `test_atlas_live.py::test_a_live_point_names_its_base_its_key_code_and_time_and_comes_whole_on_request`; `test_atlas.py::test_the_grid_the_manifest_and_the_index` (every point's `$base` is its manifest's `base.sha256`); `test_headless.py::test_a_delta_names_its_base_and_the_merge_drops_the_name`; probe on 8705: u32 λ 550 nm `computed`, then with `full_header` `cache`, same key and time |
| F3 | `protocol._short` loops forever on a range a few ulps wide | **fixed** [error in earlier]: `_short_range` keeps a range exact when its step would be below `SHORT_MIN_ULPS` = 64 ulps of its values (as a zero span), and `_short`'s correction is bounded (4 steps, else the value itself); a sanity bound keeps a widening under 4·10⁻³ of the span. The reviewer's minimal case `[1000.1, 1000.1 + 2 ulp]` returns at once | `server/lfviz/protocol.py` | `test_protocol_quant.py::test_a_nearly_constant_range_ends_and_contains_its_values` (805 ranges: the reviewer's cases, 600 two-value ranges of 1–3000 ulps at offsets 10⁻³…10¹², 200 ordinary spans at large offsets; under `SIGALRM`, each contains its values and a quantised pair decodes within its stated error) |
| F4 | a world's refusal in its constructor fails the atlas and is a 500 live | **fixed** (D14). `headless.run_spec` turns a `Refusal` from the memory estimate, from the world's constructor and from its first showing (`Runner._start_world`) into `PointRefused` with its text and hint: a refused grid point in an atlas, `400 {error, hint}` live. A run whose checks end ✗ raises `RunFailed` with the checks' labels; live it is `409` «the world's checks fail at these values: {checks}». The optional part too: a value outside a control's span (a slider below its lowest or above its highest value; a toggle's or select's value not among the screen's) is `400` with the control's label, so u32's d ≤ a and λ = 10⁹ nm of the evidence are now refused at the door with «“Slit period d” = 15 is outside this screen's range 50 … 300» | `server/lfviz/headless.py`, `server/lfviz/atlas_live.py`; the test world `tests/site_worlds/u97_atlas_hog` (modes `refuse`, `fail`, a `faults` screen) | `test_headless.py::test_a_refusal_while_the_world_is_built_is_a_refused_point`; `test_atlas.py::test_a_refusal_of_the_worlds_constructor_is_a_refused_point` (2 of 4 grid points refused, the atlas built); `test_atlas_live.py::test_refusals_of_the_constructor_failed_checks_spans_and_huge_numbers` (400 with text and hint, 409 naming the check, the span refusals); probe on 8705 (u32, the evidence's two bodies: 400 with the span texts) |
| F5 | CI never runs the Node tests | **fixed** (D15): the `check` job runs `node --test player/js/tests/*.test.mjs` in `node:24`, pinned by digest (`env.NODE`), with `--memory=1g` and the tree read-only | `.github/workflows/pages.yml` (and its header), `site/README.md` | `actionlint` clean; the step's command run locally: see «Test results» |
| F6 | `atlas_status` and `--stale` look only at the manifest | **fixed**: `sitelib.atlas_files_ok` stats the base and every point the manifest names with their sizes; an atlas missing any is `stale`, so `plan.py`, `record.py --stale` and `atlas.py --stale` rebuild it | `site/sitelib.py` | `test_atlas.py::test_a_missing_point_or_base_makes_the_atlas_stale` (a deleted point, a point of another size, a deleted base) |
| F7 | the manifest is not byte-reproducible (`made`, `cpu_s`) | **fixed**: the manifest holds neither; they stay in the index entry (`made`, `cpu_s`), where the player already reads `made` (QP) and `X-LF-Made` of an on-grid live point takes it | `site/atlas.py`, `site/README.md` | `test_atlas.py::test_the_same_bytes_twice_the_header_merge_and_the_quantisation_error` (two builds: the same manifest bytes and name); `::test_the_grid_the_manifest_and_the_index` |
| F8 | «the same bytes a site build makes» holds only on the same CPU's SIMD path | **fixed in this part's documents**: the endpoint's docstring and `site/README.md` say «on the same CPU type», with the reviewer's measurement. `RULES.md` §3 and §10 and the design §1.2 are the integrator's (text below). With `$base` the player no longer depends on the claim: a base built on another CPU has another sha256, and the point comes with its full header | `server/lfviz/atlas_live.py`, `site/README.md` | — |
| F9 | the quantisation guard: `:all` passes where per-column ranges were declared; a check's or event's blob is quantisable; ±inf becomes NaN | **fixed**: `_quant_safe` ranks the range suffixes (`:all` < none < `:col`) and accepts only a request at least as fine as declared; `_check_quantize` refuses keys of `end`, `check`, `event`, `error`, `notice`, `caption`, `state`, `live` (`registry.QUANT_TYPES_REFUSED`); `protocol.quantize` refuses ±inf (`ValueError`; NaN keeps its code), and `site/atlas.py` reports a point it cannot pack as a problem of the atlas | `server/lfviz/registry.py`, `server/lfviz/protocol.py`, `site/atlas.py` | `test_protocol_quant.py::test_the_registry_knows_the_encodings_and_the_keys`, `::test_infinities_are_refused_nan_is_coded` |
| F10 | the key covers neither the base image nor the device | **partly**: `site/record.py` and `site/atlas.py` set `LFPHYS_NO_GPU=1` in their `main` (as CI and the live points do), so a local build is on the CPU like the site's. **Not done:** `visualizations/docker/Dockerfile:12` `FROM python:3.11-slim` → `FROM python:3.11-slim@sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8` (the workflow's `PY_SLIM`, the same digest as the local image): the Dockerfile is not in this part's files, and its text is in `recorder_hash`, so the pin re-records every world once; the integrator's call | `site/record.py`, `site/atlas.py` | — |
| F11 | `atlas_live.py` is inside `code_hash` | **fixed**: `registry.SERVER_ONLY` = {`app.py`, `runs.py`, `atlas_live.py`}; the module's own hash (`atlas_live.live_hash`) is in the live key (`point_key`) | `server/lfviz/registry.py`, `server/lfviz/atlas_live.py` | `test_code_hash.py::test_the_server_only_modules_are_app_runs_and_the_live_points`, `::test_an_edit_of_a_server_only_module_keeps_the_code_hash[atlas_live.py]` |
| F12 | an integer of more than 4300 digits is a 500 | **fixed**: `app._body` reads every JSON body and turns any `ValueError` (malformed, not UTF-8, the digit limit) into `400` «the request body is not JSON» (`runs_start`, `run_command`, `run_keep`, which now also refuses a body that is not an object,, `run_record`, `api_settings_put`, `api_runs_settings_put`); the live route catches `ValueError` | `server/lfviz/app.py`, `server/lfviz/atlas_live.py` | `test_atlas_live.py::test_refusals_of_the_constructor_failed_checks_spans_and_huge_numbers` (5000 digits: 400); probe on 8705 |
| F13 | the live cache's housekeeping | **fixed**: the cache is capped (`LFVIZ_POINT_CACHE_MB`, 512 MB by default; the oldest files go first) besides the runs' period; the leftovers of a killed process (`*.part`, `*.tmp`, `*.json`) older than 10 minutes are removed; `point.log` holds the last point's log only. A capped folder was chosen over the runs' quota: the cache is rebuilt on demand, the runs are not | `server/lfviz/atlas_live.py` | `test_atlas_live.py::test_the_cache_housekeeping` |
| F14 | the toy fixture is not guarded against drift; a stale reference | **fixed**: a test rebuilds the toy world into `tmp_path` and compares every recording, base and point file by name and bytes, and the manifests but for their keys; the docstrings name `tests/site_worlds/make_fixture.py`. The fixture is remade (ATLAS_VERSION 2, `$base`; the recordings and bases are byte-identical to the old ones) | `tests/site_worlds/s98_atlas_toy/viz.py`, `tests/site_worlds/make_fixture.py`, `tests/site_worlds/recordings/s98_atlas_toy/` | `test_atlas.py::test_the_committed_fixture_is_what_the_builder_makes_now` |

## Also done

* **D4, the registry's lab laws** (R-E F9, R-P F3, R-W F5): see `RESPONSE_framework.md` in those folders. The toy world's
  lab step has two laws (the slope of L against √h, and the zero intercept of the line through the same points), so the
  player's tests have several laws per step.
* **Worksheet fields** asked by the integrator during processing: every `frp` entry needs `programme` (a T);
  `variants` are validated (`registry._check_variants`: id, grade 1–12, label, steps of the lab, a plot per step with
  its columns and a fit among the step's or none, questions). The toy world has a grade-7 variant.
* `tests/test_aliases.py::test_an_old_record_opens_plays_and_resumes_by_replay` failed from 2026-11-17 on: its fixture's
  last action is of 2026-11-13, and the default removal period of 3 days removed it at load. The test now starts its
  server with `keep_days=365`.
* `locales/ru.json`: 16 msgids added (the live endpoint's new refusals; the test worlds' texts), one removed (the old
  body message), with a load-merge-sorted-write script run right before writing.

* **Browser tests and the committed fixture** (integrator, during processing): a server's player now refuses a stale
  atlas (D11), and every key covers the code, so the committed toy fixture serves only the player's Node tests. A new
  `site/fixtures.py --out DIR [--world …]` builds what a browser test needs now (by default the toy world, its
  recordings and atlases), and the workflow's `build` job runs `tests/browser/demo_screens.mjs` for the toy world in
  EN and RU on a server serving that folder. `tests/test_atlas.py` checks the committed fixture's format versions, its
  bytes against a fresh build (F14), and that `site/fixtures.py` builds everything present with the expected keys.
* Worksheet variants may also carry `goals: {step id: T}` (a step's goal on that variant's sheet), validated.

## Test results

On a read-only snapshot of the working tree (2026-11-17, 18:4x), image `lfphys-viz`, CPU:

* `visualizations/tests/` (the CI's `tests` shard, whole): **421 passed, 4 failed**. The 4 are the README checks
  (`test_site_registry.py::test_the_readme_catalogue_is_the_registrys_in_every_language[en, ru]`,
  `test_site_build.py::test_readme_generation_is_idempotent_and_up_to_date[en, ru]`): the committed READMEs predate
  S03's new recording and screens (QW). After `site/readme.py` on a copy of the snapshot all 11 README tests pass; the
  integrator runs it when the worlds are final.
* The files touched here, again on a later snapshot (`test_atlas`, `test_atlas_live`, `test_headless`,
  `test_protocol_quant`, `test_code_hash`, `test_site_registry`, `test_site_build`, `test_aliases`): 165 passed, the
  same 4 README failures.
* `s03_projectile/tests`, `u32_double_slit/tests`, `tests/test_i18n.py`: 219 passed, 1 failed:
  `test_u32_physics.py::test_coherence_error_is_calibrated_at_full_coherence`, D9's coherence error, being reworked
  by QE and QW at the time.
* `tests/test_i18n.py` alone on the later snapshot (with every msgid added here): 90 passed.
* Node (`node:24`, the CI step's command): 45 of 45 on the working tree (the last run).
* `actionlint` 1.7.7: clean.
* Browser: `tests/browser/demo_screens.mjs` on the toy world built by `site/fixtures.py`, served on 127.0.0.1:8705 as
  the new CI step serves it: «all passed» in EN (127 checks) and RU (131), 1280×800 and 390×844, the live point's
  passport with the point's own key, code and time included.
* Probes on a private server (127.0.0.1:8705, an empty `LFVIZ_RECORDINGS`): u32 `{d_um: 15, a_um: 20}` and `{lam_nm:
  1e9}` (the evidence's e10) → 400 with the span texts; u32 λ 550 nm → 200 `computed`, then `full_header` → 200
  `cache`, the same key and time; S03 37.3° → 200 `computed`; a 5000-digit integer → 400; `GET /api/recordings` →
  `{worlds, site, published, expected}` with S03's four atlas keys.

## For the integrator

* `RULES.md` §3, the `POST /api/atlas/…/point` row: «{values, seed?, full_header?} -> the point's file, as a site build
  packs it on the same CPU type; headers X-LF-Source, X-LF-Key, X-LF-Code, X-LF-Made; 400 {error, hint?} (a refusal, a
  value outside the control's span), 409 (its checks end ✗), 429, 503».
* `RULES.md` §10 «The atlas»: «The same spec and code give the same bytes, the manifest included (it holds no build or
  CPU time: the index entry's `made` and `cpu_s`), on the same CPU type (numpy's SIMD paths can change the last bits of
  a world's computed values). A point's header delta names its base (`$base`, the base file's sha256): a reader merges
  it only with that base. A point the world refuses in `check_params`, its memory estimate or its constructor is
  `refused`.» «Compute live»: «Its key follows the code on disk (`registry.code_hash_current`, by the files' times); the
  point's process hashes the code before and after it computes, and a point computed while the code changed is not
  kept. The response names the point's key, code and time; `full_header: true` gives the point with a full header. A
  value outside a control's span is refused. Cache: at most `LFVIZ_POINT_CACHE_MB` (512 MB).» «Lab work»: the `laws`
  list (see the D4 response). The design §1.2 «Determinism»: «on the same CPU type».
* `RULES.md` §9 / §10 and `STATUS.md` V52 (g): the server's player falls back to the site's atlas when published, of
  the same version and with the expected key (D11; the client side is QP's).
* The Dockerfile pin of F10 (above).
