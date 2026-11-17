# Review R-F (EX1-atlas): the atlas framework, the live point, the site's build and check, CI (batch of 2026-11-14)

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the code under review) |
| Date | 2026-11-17 (the work of 2026-11-14) |
| Commit | 507c059 «EX1: …», clean |
| Scope | `visualizations/server/lfviz/headless.py`, `protocol.py` (quantised blobs), `registry.py` (`VIZ["screens"]`, `check_screens`, `screens_of`, `atlases_of`, `view_declarations`), `atlas_live.py`, the new routes in `app.py`; `visualizations/site/{atlas,record,plan,build,check,readme,sitelib}.py`; the changes to `.github/workflows/pages.yml`; their tests and fixtures (`test_headless.py`, `test_atlas.py`, `test_atlas_live.py`, `test_protocol_quant.py`, `test_site_build.py`, `test_site_registry.py`, `tests/site_worlds/`, `player/js/tests/{quant,atlas}.test.mjs`). |
| Not in scope | The engine's mechanics and the fit (R-E), the screens in a browser (R-P), S03 and u32 as used (R-W). Player code is touched only where it consumes a live point (F2). |
| Known items not repeated | `STATUS.md` V52 (a)–(r), in particular (g): a live point is not fetched from the public site. |
| Environment | `lfphys-viz` image (Python 3.11.17, numpy 2.4.6), CPU (`LFPHYS_NO_GPU=1`), the repository mounted read-only. Private servers `lf-rvf-srv*` on 127.0.0.1:8701 with their runs in scratch. Code edits (F1, F2) were made only in a scratch copy of HEAD (`git archive 507c059`); the previous tree is `git archive ee6da3f`. Node tests in `node:20-slim`; `actionlint` 1.7.7. Host: i9-9900K (AVX2, no AVX-512). |

Evidence is in `evidence/`: the outputs `eNN_*.out` and the scripts in `evidence/tools/` (`<repo>` and `<scratch>` stand for the
local paths).

## Summary

There are 14 findings: **0 errors**, **5 should-fix** and **9 nits**.

What works, measured:
- **Tests.** The eight framework test files pass (158 tests); the Node tests of the decoder, the atlas, the captions,
  the fit and the lab pass (24 of 24); `actionlint` is clean (`e00`).
- **An atlas point is the world's own run, and it is reproducible.** I rebuilt S03's four atlases and u32's Explore
  atlas into scratch. All 1026 point files and the 5 bases are byte-identical to the local ones (`e02`). An on-grid
  point computed live, in a fresh process with 2 BLAS threads, is byte-identical to the site's file for six points,
  u32 included (`e03`). So no state leaks from one point into the next in a build process.
- **Recordings of the worlds without screens.** I re-recorded 39 recordings of 15 worlds with HEAD and with ee6da3f
  (r12 was left out: 21 CPU minutes).
  - HEAD reproduces all 39 local files byte for byte.
  - Between the two commits, 28 are byte-identical. The other 11 (u36, u41, u42, u44) differ only in the header's
    `engine` entry of `core.data`, whose `ABOUT` gained the air data in this batch (`e13`, `e14`). That is expected.
- **The site's check fails as it should.** A clean build passes (0 failures, 65.6 MB). The check fails on each of these
  (`e12`):
  - a manifest that counts a failed check;
  - a stale key;
  - a removed atlas folder;
  - an index without the atlas;
  - one deleted point.

  The unit tests cover the budgets.
- **The live point endpoint holds up.** (`e04`–`e07`, `e19`)
  - **Refusals and bad requests.** A refusal by `check_params` is 400 with its text and hint. Bad seeds, bodies and
    controls are 400.
  - **Unknown or hostile paths.** An unknown world or atlas is 404. Path traversal is refused on the POST route and on
    the nested `/recordings/<world>/atlas/…` route.
  - **Queue.** One point is computed and four wait; the rest get 429.
  - **Limits.** A 1 s CPU limit gives 503, and the server goes on. 0.25 GB of memory gives 503. A point needing more
    than 1.8 GB gives 503 with the memory text.
  - **Client disconnects.** A client that hangs up leaves no orphan process. Only one point process runs at a time.

What is weak:
1. **The live point's provenance.**
   - Its cache key uses the server's code hash, computed once per process, while the point's process runs the code on
     disk. So the cache can serve another code's output under this code's key (F1).
   - Its header is a delta against the server's base, but the player merges it with the local atlas's base, even when
     that atlas is stale (F2).
2. **`protocol.quantize` can loop forever** on a blob whose values differ by a few ulps (F3).
3. **A world that refuses in its constructor (u32: d ≤ a) is not treated as a refusal.** An atlas build would count
   the point as failed, and the live endpoint answers 500 with an English technical string (F4).
4. **CI never runs the Node tests**, so the JS decoder's bit-equality with Python is not gated (F5).

## Findings

### F1. The live-point cache is keyed with the server's once-per-process code hash; the point's process runs the code on disk (should-fix)
- **Where:**
  - `visualizations/server/lfviz/atlas_live.py:274-276` and `:282`:
    `code = registry.code_hash_cached(world)` (`registry.py:823`, «computed once per process … a file edited while the
    process runs is not seen»);
  - `_spawn` (`:300-316`) runs `python -m lfviz.atlas_live`, which imports the world and the engine fresh from disk
    and writes the point under the server's key, and also the base (`base-<base_key>.lfpt.gz`, `compute()` `:183-194`).
- **Evidence:** `evidence/e08_cache_poison.out`, from a scratch copy of HEAD served by `lf-rvf-srvC`.
  1. The server starts, and h = 1.5 is computed.
  2. With the server still running, `s03_projectile/viz.py` gets a probe that marks every frame. h = 1.7 is computed by
     the edited code (its frames carry the mark) and stored as `78d9e82336124a7a`.
  3. The edit is reverted and the server restarted:
     ```
     [reverted] h=1.7: 200 src=cache 0.0s <gzip 5489 B>
        X-LF-Key 78d9e82336124a7a; frames carry the edited code's mark: True
     ```
  - Also, while the server runs after the edit, h = 1.5 (old code) and h = 1.7 (new code) are served under keys
    computed from the same code hash.
  - `local_point` has the same blind spot. It compares the index's key with a key built from the stale hash, so it
    serves the old atlas's on-grid points as `atlas`, and computes the off-grid ones with the new code.
- **What is wrong:** the key is meant to cover the code (`RULES.md` §10 «Cache … The key covers the atlas key without
  its grid»), but the code it names is not the code that ran. The owner's server runs for days while code is edited
  (`lf-viz` up 3 days now). The wrong points stay for `keep_days`. A poisoned base also skews the deltas of every
  later point.
- **Fix:** let the point's process compute `registry.code_hash(world)` itself. It already imports everything. It then
  writes the point and the base under the key it computes, and returns that key. Or the server compares it with its
  own key and does not cache when they differ. Use `code_hash` (not `_cached`) for `local_point`'s comparison, or
  re-hash when a file's mtime changed. Test: edit a world file in a tmp copy between two requests, and assert that the
  second point is not stored under the first code's key.

### F2. A live point is a delta against the server's base, but the player merges it with the local atlas's base, even a stale one; its passport names the atlas's key, code and date (should-fix)
- **Where:**
  - `atlas_live.compute()` packs against the base it computes (or caches) with the server's code
    (`atlas_live.py:176-200`).
  - `player/js/atlas.js:108-120` takes the base from the local manifest (`openAtlas`), and `:171` merges every point,
    live ones included, with `this.base`.
  - Neither `/api/recordings` (`app.py:152-168`, the local `index.json` as it is) nor the player compares the local
    atlas's key, so a stale local atlas still opens Explore on a server.
  - `explore.js:331-332`: the passport of a live point shows the manifest's `key`, `code_hash` and `made`.
- **Evidence:** `evidence/e09_live_base_mismatch.out`. The scratch copy has `G = 9.81` in
  `s03_projectile/engine/shot.py`, so the local atlas (built with G = 9.80665) is stale. A live point h = 1.5 m:
  ```
  delta's keys: ['$delta', 'launcher', 'params', 'scene', 't', 'type']
  header the player shows (local atlas base): g = 9.80665  weight = 0.5687857
  header the server computed with (its base): g = 9.81  weight = 0.56898
  local atlas key in index: 641ab5d011d20d4e | X-LF-Key: c16df14152740a2f
  ```
  The drawn flight was computed with 9.81 m/s², while the header shown with it says 9.80665.
- **What is wrong:** a header key that is the same for every point of the new code is left out of the delta, so the
  player shows the stale base's value. This hits whenever the engine or the world changes and the local atlases are
  not rebuilt yet (every key goes stale at once: V52 (p)).
- **Fix:** answer a live point with a full header (no `$delta`; `mergeHeader` already passes a full header through),
  or send its base key in a header (`X-LF-Base`) and let the player refuse to merge with another base. Show the live
  point's own key (`pt.key`, from `X-LF-Key`) and the server's code in its passport. Test it in
  `test_atlas_live.py`, and in `atlas.test.mjs` for a delta with another base.

### F3. `protocol._short` loops forever when a quantised blob's values differ by a few ulps (should-fix)
- **Where:** `visualizations/server/lfviz/protocol.py:196-203` (from `_short_range`, `:206-217`, from `quantize`,
  `:170`).
  - For a span of a few ulps, `q = 10**(floor(log10(span)) - 3)` is far below the ulp of the values.
  - So `v = round(v ± q, nd)` never moves, and `while (v < x) if up else (v > x)` never ends.
- **Evidence:** `evidence/e15_quantize_hang.out`, `e16_quantize_hang_where.out`.
  - 46 of 400 two-value blobs `[x, x + k·ulp]` (1 ≤ k ≤ 8, |x| log-uniform in 1e-3…1e12) never return, for example
    x = 0.0485 with 7 ulps, and x = −1921.12 with 2 ulps.
  - The stack is at `protocol.py, line 202 in _short`.
  - A minimal case: `protocol.quantize(np.array([1000.1, 1000.1 + 2*np.spacing(1000.1)]), "u16")`.
- **What is wrong:** a nearly constant column is common: a conserved quantity, a velocity in vacuum, two detections at
  "the same" time, a flow line on the axis.
  - **In a build** `headless` has no time limit, so `site/atlas.py` and `site/record.py` would hang, and the CI's record
    job would run to its 300-minute timeout.
  - **In a live point** the process is killed at 120 s of CPU with a 503 that blames time or memory.
  - The pilots do not hit it today: the builds finished.
- **Fix:** keep the range exact (as for a zero span) when `q` is below a few ulps of `max(|lo|, |hi|)`, and bound the
  loop. Add a property test of `_short_range` over near-constant and large-offset ranges to `test_protocol_quant.py`.

### F4. A world's refusal from its constructor is a failure for `headless`: the atlas fails, the live endpoint answers 500 with an English technical text (should-fix)
- **Where:**
  - `headless.run_spec` turns only `check_params` into `PointRefused` (`headless.py:177-180`). The world's constructor
    (`:191`) and `limits.check_estimate` (`:181`, a `Refusal` too) are outside it.
  - u32 refuses d ≤ a in its constructor (`u32_double_slit/viz.py:349-351`, `_build`). Its `check_params` checks only
    the rates.
  - `site/atlas.py:219-222` counts any `ValueError` as a failed point.
  - `atlas_live.main` (`:231-236`) and `_spawn` (`:343-346`) turn the `Refusal` into `500 {error: "the point was not
    computed: Refusal: …"}`, a plain English string.
  - A run whose check ends ✗ is also a 500 with the internal message.
  - `RULES.md` §3 (`POST /api/atlas/…`) promises 400 for a refusal.
- **Evidence:**
  - `evidence/e10_live_failing.out`:
    ```
    {'d_um': 15.0, 'a_um': 20.0}: 500 … "the point was not computed: Refusal: the slit period must be larger than the slit width. What to change: …"
    {'lam_nm': 1000000000.0}: 500 … "RunFailed: u32_double_slit/explore: 2 check(s) end failed: coh0 (world 1), per0 (world 1)"
    ```
  - `evidence/e11_ctor_refusal.out`: the same values through `atlas.run_point` (a grid with d = 15 µm) give
    `Refusal`, not `PointRefused`, so the atlas build fails instead of marking the point refused.
- **What is wrong:**
  - The design's rule «a point the world refuses is `refused`, with its text shown at that combination» (§1.2) holds
    only for the worlds that refuse in `check_params`. The rework of the other demonstrations (design §7) will meet
    worlds that refuse as u32 does.
  - On a server, the player (`atlas.js:201-206`) shows a 500 as an error, in English in a Russian interface.
  - The endpoint also accepts any schema value, not only the slider's span, so a request outside the span reaches
    failing checks.
- **Fix:**
  - In `run_spec`, catch `lfviz.errors.Refusal` from the constructor and from `check_estimate`, and raise
    `PointRefused(text, hint)`.
  - In the live endpoint, answer a point whose checks end ✗ with a 4xx and a `T`, for example «the world's checks fail
    at these values: …» with the failing checks' labels.
  - Optionally refuse values outside the control's span.
  - Tests: a toy world refusing in its constructor gives a `refused` grid point, and a 400 with the hint live.

### F5. CI never runs the Node tests, so the JS decoder's bit-equality with Python, the header merge and the fit's parity are not gated (should-fix)
- **Where:** `.github/workflows/pages.yml`. There is no `node --test` step: `evidence/e00_tests.out`, «CI steps that
  run node: 0».
  - `test_protocol_quant.py` checks only the Python half of the shared fixture.
  - The JS half (`player/js/tests/quant.test.mjs`, «which `player/js/api.js decode` must give bit for bit») runs only by
    hand.
  - So do `atlas.test.mjs` (`mergeHeader`, flattening, LRU) and `fit.test.mjs` (against `lfphys.tools.stats.linear_fit`).
- **Evidence:** 24 of 24 Node tests pass locally (`e00`), but nothing in CI would notice a decoder or a fit that drifts
  from Python. The design §8 and `RULES.md` §10 «Tests» rely on that parity.
- **Fix:** add a step to the `check` job, for example `docker run --rm --memory=1g -v "$PWD:/lf:ro" -w /lf/visualizations
  node:24@sha256:… node --test player/js/tests/*.test.mjs`, pinned by digest as the other images are.

### F6. `atlas_status` and `--stale` look only at the manifest: a missing point or base keeps the atlas "present", and `--stale` does nothing (nit)
- **Where:** `visualizations/site/sitelib.py:195-210`.
  - `status()` checks a recording's file size (`:190`).
  - `atlas_status` checks only that the manifest exists.
- **Evidence:** `evidence/e21_stale_misses_deleted_point.out`. With `p500.*` of S03 Explore deleted, `atlas_status`
  gives `explore: present`, and `record.py --stale` prints «nothing to record». Meanwhile the build leaves the whole
  atlas out, and the check fails «s03_projectile/atlas explore: missing» (`e12`, case `nopoint`).
- **Fix:** check that the base and every named point exist with their sizes (cheap: about 1000 `stat` calls), as
  `status()` does for recordings.

### F7. An atlas's manifest is not byte-reproducible: `made` and `cpu_s` change its bytes and its hashed name on every build (nit)
- **Where:** `visualizations/site/atlas.py:254-267`. `made` and `cpu_s` go into the manifest, and
  `atlas.<sha8>.json` is named by its content.
- **Evidence:** `evidence/e02_atlas_bytes_vs_local.out`. Every point and base is equal, but the manifests differ only
  in `cpu_s` and `made` (`atlas.45aa6b34.json` vs `atlas.555cf51b.json`).
- **What is wrong:** `RULES.md` §10 and `site/README.md` say «the same spec and code give the same bytes». The
  recordings keep `made` and `cpu_s` in `index.json`, not in a served, hash-named file. Each CI cache miss renames the
  manifest.
- **Fix:** move `made` and `cpu_s` to the index entry only (where they already are), or name the manifest by the key.
  Or say in the RULES that the manifest is the exception.

### F8. «The same bytes a site build makes» holds only on the same CPU's SIMD path: all 48 u32 points differ between numpy's X86_V2 and X86_V3 dispatch (nit)
- **Where:**
  - `RULES.md` §3, `POST /api/atlas/…`: «the same bytes a site build makes»;
  - `atlas_live.py:8`;
  - the design §1.2 «Determinism».
  - The site's atlases are built on GitHub's runners, while live points are computed on the owner's CPU.
- **Evidence:** `evidence/e17_atlas_cpu_v2.out`. I rebuilt with `NPY_DISABLE_CPU_FEATURES=X86_V3` on the same machine:
  - S03: 978 of 978 points are identical;
  - u32: 48 of 48 points differ, in the frames' `coh` (up to 4.1e-10 relative) and in the checks' `value` and `rel`
    (up to 3.7e-13); the quantised blobs are identical.

  An AVX-512 runner takes yet another path.
- **What is wrong:** nothing a viewer sees, but the claim is unconditional, and the cache key cannot cover the CPU.
- **Fix:** say «on the same CPU type» in the RULES, the design and the endpoint's docstring. Or round such meta values
  in the world, as S03 rounds what is only drawn.

### F9. The registry's quantisation guard: `:all` passes where the view declared a per-column range, and a check's or an event's blob is quantisable when declared (nit)
- **Where:** `registry.py:437-443`. `_quant_safe` drops the suffix before comparing. `_QKEY` (`:317`) accepts any
  message type.
- **Evidence:** `evidence/e18_registry_quant_guards.out`:
  ```
  u16:all accepted where the view declared u16: True
  check./event. keys refused: none (accepted when the view declares them)
  ```
  - For S03's `traj.s` (t 0–5.5 s, x 0–60 m), `u16:all` would widen t's step about tenfold.
  - `RULES.md` §10 says «never measurables, events or checks». Today that holds because no check or event carries a
    blob, not because anything refuses it.
  - Also, `quantize` stores ±inf as the NaN code and leaves it out of `max_err` (`protocol.py:152`, `:182`, `:187`).
- **Fix:**
  - Treat a missing suffix as `:col` for 2-D tables in `_quant_safe`, or require the same suffix.
  - Refuse quantize keys whose type is in `UNDROPPABLE` other than `header` and `frame`.
  - Count non-finite values as an error, or refuse them.

### F10. The key does not cover the base image or the GPU environment (nit)
- **Where:**
  - `visualizations/docker/Dockerfile:12` `FROM python:3.11-slim` (no digest), while `sitelib.recorder_hash` covers
    only the Dockerfile's text. The workflow pins its other images by digest.
  - `site/record.py` and `site/atlas.py` neither set nor check `LFPHYS_NO_GPU`, while the image has `cupy-cuda12x`. The
    live point's process sets it (`atlas_live.py:306`).
- **Evidence:** `docker run … python3 -c "import cupy"` gives `cupy yes`; Dockerfile line 12. The image matches
  `requirements.lock` exactly (no package differs).
- **Fix:** pin `FROM python:3.11-slim@sha256:…` (the same digest as `PY_SLIM`), and set `LFPHYS_NO_GPU=1` in the
  builders, or put `backend.settings()` into the key.

### F11. `atlas_live.py` is inside `code_hash`: an edit of the live endpoint re-records every world (nit)
- **Where:** `registry.py:797`. `SERVER_ONLY = {"app.py", "runs.py"}`. `atlas_live.py` is imported only by `app.py` and
  run only as the live point's own process. A site build's bytes come from `site/atlas.py` (in `recorder_hash`).
- **What is wrong:** an edit of the endpoint stales all 46 recordings and 5 atlases of the 18 worlds. In CI that is a
  cache miss everywhere, r12 alone 21 CPU minutes. This is what `SERVER_ONLY` exists to avoid.
- **Fix:** add `atlas_live.py` to `SERVER_ONLY`, and put its own hash into the live key (`point_key`) instead.

### F12. A JSON body with an integer of more than 4300 digits is an unhandled `ValueError` (500 and a traceback) (nit)
- **Where:** `atlas_live.py:363-366` catches `JSONDecodeError` and `UnicodeDecodeError` only. The same pattern is in
  `app.py:237`, `:455` and `:481`.
- **Evidence:** `evidence/e04_live_probes.out` («huge int value: 500 … Server got itself in trouble»). The server log
  has `ValueError: Exceeds the limit (4300 digits) for integer string conversion`. The server goes on.
- **Fix:** catch `ValueError` (its parent) where the body is read, as `sweep.py:923` does.

### F13. The live-point cache's housekeeping (nit)
- **Where:** `atlas_live.py:255-266` and `:307-318`.
  - The cache is not counted in the runs' quota (`runs.py` counts only runs).
  - `point.log` is opened for append in every point's folder and never trimmed.
  - `<key>.json` failure files, `.tmp` and `.part` left by a killed process are not removed (`_cleanup` takes only
    `*.lfpt.gz`).
- **What is wrong:** a client can fill the disk at about 130 kB per u32 point, one every 2–3 s, for `keep_days`. The
  server is local, so the risk is small.
- **Fix:** count `atlas-live/` in the quota, or give it a cap; rotate or drop `point.log`; clean the leftovers in
  `_cleanup`.

### F14. The toy fixture is not guarded against drift from the builder; a stale reference in its world (nit)
- **Where:**
  - `tests/test_atlas.py:229-249` checks only that `tests/site_worlds/recordings/s98_atlas_toy/` decodes. Its keys are
    already stale at this commit.
  - `tests/site_worlds/s98_atlas_toy/viz.py:6` names `tests/make_atlas_fixture.py`. The script is
    `tests/site_worlds/make_fixture.py`.
- **Evidence:** `evidence/e20_toy_fixture.out`. A fresh `record.py --world s98_atlas_toy` gives the same bytes for all
  14 point, base and recording files; only the two manifests differ (F7).
- **What is wrong:** the Node tests and the browser tests read this fixture. A change of the header delta or of the
  packing would leave them testing an old format.
- **Fix:** a test that rebuilds the toy into `tmp_path` and compares every point, base and recording file with the
  committed ones (cheap: about 1 s). Correct the docstring.

## Areas checked and found fine

- **Tests:** 158 framework tests pass; Node 24 of 24; `actionlint` clean (`e00`).
- **An atlas point is the world's own run:** the world's `Simulation` through `lfviz.sim.Runner`, on a frame clock,
  with no wall-time budget. Timing fields are stripped, and `lag` is always false. The kernels are reset per run.
- **A point built twice:** 1026 points and 5 bases are byte-identical across builds (`e02`), and across a build and a
  live process with other thread counts (`e03`).
- **Keys:**
  - the spec (values, defaults, fixed, seed, `frame_dt`, stop, drop, quantize, the law's id);
  - `ATLAS_VERSION`;
  - `recorder_hash` (record.py, atlas.py, headless.py, the lock, the Dockerfile);
  - the world's code hash.

  An edit of `readouts` or `instruments` changes `viz.py`, hence the code hash. No non-code file (only locales and
  READMEs) enters a point's bytes. The world key of the CI cache covers the atlases' keys. `check.py` re-checks the
  point and atlas budgets, so `recorder_hash` need not cover them.
- **Quantisation:**
  - Only blobs are quantised, never the JSON meta, where the measurables, events and checks live.
  - `max_err` is measured against the float32 decode, over every point; the base header is covered by the default
    point.
  - Measured: S03's `traj.s` max_rel ≤ 5.5e-4, set by float32 and not by u16; u32's map (u8 √) 0.0039 of the peak;
    hits' x 4.6e-7 m.
  - The JS decoder is bit-equal on the shared fixture (Node).
- **Header delta:** Python's `merge_header` and JS `mergeHeader` agree, with `$drop` and `$drop_blobs` included.
- **Live endpoint:** validation, 404s, traversal, the queue, the CPU and memory limits, disconnects and the cache hit
  are all as described above (`e03`–`e07`, `e19`).
- **Site build and check:** `check.py` fails on a failed check, a stale key, a missing folder, a missing index entry
  and a missing point (`e12`); on a changed point and on budgets in `test_site_build.py`. `build.py` copies only the
  registry's atlases whose files are all there.
- **CI:**
  - atlases are built in the world's record matrix entry and cached under the world key;
  - the artifact includes `atlas/`;
  - build → check → smoke test;
  - the new test files are in the check job, and `test_atlas_live.py` is in the `tests` shard;
  - a failed atlas leaves the world's cache unsaved and makes the check fail.
- **Recordings of the worlds without screens:** unchanged apart from the expected `core.data` entry of the header's
  engine list (`e13`, `e14`); HEAD reproduces the local files.
- **`readme.py` and `plan.py`:** the screens' links and the atlases' states. The README test passes.
