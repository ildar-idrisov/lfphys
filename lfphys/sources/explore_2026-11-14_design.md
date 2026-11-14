# Interactive explorations and lab work on precomputed atlases: design (2026-11-14)

The owner's direction of 2026-11-14 is quoted in `../../AGENTS.md` §1 («Interactive explorations and lab work for
school and university»), with his answers of the same day: sliders snap only to computed points; the pilots and the
rework of the existing worlds come before AB1 in full; quality over quantity. This document is the design only. It
changes no code. It settles the atlas, the registry and world contract, the player, engine M1 for S03, the S03 world,
the u32 rework, the audit of the other demonstrations, the tests and the implementation plan.

Pilots (integrator's decision): **S03** «Движение тела, брошенного горизонтально и под углом» (school: Watch,
Explore, Lab work; needs M1) and the rework of **u32** «Двойная щель» (university: Watch with captions, Explore).

Numbers marked *measured* were measured for this design in Docker (`lfphys-viz`, CPU, memory-capped containers;
Appendix A). Numbers marked *estimate* are computed from measured parts and say so.

## 0. Decisions in brief

1. **Three screens on one model.** A demonstration may have Watch (a captioned recording, only for phenomena that
   develop in time), Explore (an atlas of computed points on a grid of 2–4 controls) and Lab work (steps on their own
   atlases with instruments, a table, a plot, a fit and «Check against the law»). The current player stays as
   «▶ Compute live» on a server and as the only interface of research worlds and laboratories.
2. **An atlas point is a short recording.** Each point is the world's own `Simulation`, run headless at the grid
   values by the same runner as the site's recordings. Its stream is an ordinary `LFVREC1` stream of the world's own
   messages. So the world's own view draws a point with no new drawing path, and rules 2–3 hold by construction.
3. **Compact by packing, not by a new format.** A point file differs from a recording only in three ways. Its header
   is a delta against the screen's base header. Selected arrays are quantised by a protocol-level descriptor
   (`q` on a blob), which both decoders undo. The message types and frame blobs a screen does not draw are dropped.
   Quantisation is allowed only below what is displayed or measured, and the loss is measured and written into the
   manifest. Events, measurables and checks stay in full float64 JSON.
4. **One file per point, lazy.** Points are loaded on demand, with neighbours prefetched and an LRU cache. Each
   atlas has a manifest. Keys, staleness, CI caching and the site build reuse the recordings' machinery: the atlas
   key covers the spec, the recorder version and hash, and the world's code hash.
5. **Sliders snap to the grid** on the site. On a server the same screen also computes an off-grid point on demand
   (`POST /api/atlas/…/point`): the same recipe in a memory-limited process, labelled «computed live».
6. **Stochastic worlds** store one seeded sample (u32: 5000 hits) and the run's own computed distribution (the
   ensemble expectation), with the run's χ² of the sample against it. Another sample is drawn only by a live
   computation.
7. **Registry:** a new `VIZ["screens"]` (watch / explore / lab). The recording specs gain `captions`, `quantize` and
   `speed` in scripts. The lab gains `instruments`, `steps` and `worksheet`. School worlds need Explore and Lab work;
   the former `guide` is replaced by the lab's steps. Every text is a `T`. `registry.check` and the completeness
   tests validate all of it.
8. **Player:** one page per demonstration (`run.html?demo=<world>&screen=…`) with tabs and a PhET-like layout: the
   phenomenon in the centre, 3–5 controls at the side, time at the bottom. Checks, «Physics of this world», events and
   the passport fold into one link, «How we know this is right». New modules: `record_core.js` (extracted from
   `player.js`), `demo.js`, `atlas.js`, `explore.js`, `lab.js`, `fit.js`, `watch.js`, `worksheet.js`. The layout
   works at 390 px.
9. **Lab measurement** reads a computed value at the cursor through a declared instrument. The reading is rounded to
   the division and carries the declared error. The manual stopwatch measures the student's own reaction. The fit is
   a weighted least-squares fit with effective variance, its errors scaled by the Birge ratio when χ²/dof > 1, and is
   tested against `lfphys.tools.stats.linear_fit`. The reference for «Check against the law» comes from the world's
   own check, computed at build time.
10. **Engine M1 (first scope for S03):** `lfphys.core.mechanics` (point bodies in a uniform field, DOP853 with event
    location, energy bookkeeping, closed-form references), linear Stokes drag in the core, and the quadratic
    constant-C_d drag as a model in `theories.models.drag_quadratic`. The latter carries the hodograph quadrature as
    the second method. Air properties come from `core.data` (moved there from `core.fluids.lbm`).
11. **S03** (`s03_projectile`) has all three screens. Watch: yes. The two-ball strobe shows the independence of
    the motions, a cause → effect story that one projectile at a time does not show. Explore: height × speed × angle
    × air, 1130 points, about 4.4 MB *estimate*. Lab work in three parts: L(h) → L ∝ √h; L(θ) → maximum at 45° and
    L ∝ sin 2θ; the shift of the maximum in air.
12. **u32**: Watch («the double slit, step by step»: build-up, fringes, one slit, a which-path detector, back);
    Explore over λ × d × a, 48 points, 5.16 MB *measured*. The rest of today's interface folds into «How we know this
    is right» or stays in «▶ Compute live» unchanged, with all 19 presets (one more, `story`, is added) and every check.
13. **Budgets:** a point at most 150 kB target and 400 kB limit; an atlas 6 / 12 MB; a world, recordings and atlases
    together, 12 / 25 MB (unchanged); the site 600 / 900 MB (unchanged). S03 is about 5 MB, u32 about 8.2 MB.
14. **Plan:** batch **EX1** = framework (atlas + player screens), S03 with M1, u32 rework. Agents and file ownership
    are in §9; independent reviews and their processing come before the report.

---

## 1. The atlas

### 1.1 What a point is, and what it stores

An **atlas** is the set of computed points of one screen (or of one lab step) on a grid of its controls. A **point** is
the world's own run at the grid values: the screen's preset, then the grid values on top, the screen's seed. It is
run from t = 0 until the screen's stop rule (§1.2). It stores exactly what the world emits for its view, filtered and
packed:

| content | S03 point (a flight) | u32 point (a build-up) |
|---|---|---|
| header | delta: the launcher's pose, the values, the scene box | delta: geometry, particle, the screen grid `x` (u16) |
| what the view draws | `traj` chunks: t, x, y, vx, vy, ax, ay and the drag work W, sampled every 1/120 s of world time (u16) | `segment`: the near-field map (u8 of √(I/peak)), its z and w (f4), the expectation curves (f4), 20 flow lines (u16); `detections`: t, x (u16), y, flags (u8) |
| measurables | frames' `meas` (t, x, y, v, E_k, E_p, W_drag, Re) in full JSON | frames: hits so far, χ² and p of the sample against the run's expectation, |γ₁₂| with its error |
| events | apex and landing with their data (H, T, L, v at landing) in full JSON | none (the segment's start) |
| checks | energy balance; vacuum: T, L, H against the closed forms; air: L, T against the hodograph quadrature; the Reynolds range of the C_d model | the world's own (wavelength, fringe period, paraxial accuracy against Rayleigh–Sommerfeld, …) |
| dropped | nothing | `stories` (the chain of causes: Watch and Live only); the frame blob `flight` (particles in flight) |

A point is a **world**, not a picture. The player feeds its messages to the view up to the cursor's time (§1.5), so
the landing mark appears when the time reaches the landing, and the hits appear in the order they were detected.

### 1.2 How a point is computed: the world's own simulation, headless

The recorder's `record()` (`visualizations/site/record.py`) is generalised into one function used by recordings,
atlas points and the server's live points: `run_spec(viz_id, base, values, seed, clock, stop, script, emit)` in a new
`server/lfviz/headless.py`. It lives on the server side, so the server can import it; `site/record.py` and
`site/atlas.py` call it. It does what `record()` does today. It resolves the preset and the values through the schema,
checks `check_params` and `estimate_bytes`, builds `viz["simulation"]`, drives `lfviz.sim.Runner` on its own frame
clock with no wall-time budget, drops `checkpoint`, `command`, `resumed`, `record_segment` and `busy`, and strips the
frames' timing fields. Two additions:

- **clock:** either the recordings' `fps × speed` (played seconds), or `frame_dt` in world seconds (atlas points).
- **stop:** `{"seconds": s}` (recordings), `{"world_s": t}` (u32: 5.25 s at 1000 particles/s), or
  `{"event": "landing", "after_s": 0.3, "max_world_s": 12}` (S03: a flight ends 0.3 s after its landing event; a
  point that reaches `max_world_s` first fails, see below).

A point **fails** when a recording would: an error message, an exception, or a check whose last state is ✗ and not
`expected`. A failed point fails the atlas build, which is the honest outcome: the author changes the grid or the world.
A point the world **refuses** (`check_params` raises `Refusal`, e.g. h = 0 with θ = 0 in S03) is not a failure. Its
manifest entry says `refused` with the refusal's `T`, and the slider shows that text at that combination.

**Seeds.** Every point of a screen uses the screen's seed (default 1). The seed is in the manifest and in the passport.

**Determinism.** The same spec, code and recorder give the same bytes for every point, as for recordings (integrator
D6). This is tested.

### 1.3 File format

**Point file** `<point>.<hash8>.lfpt.gz`. It is gzip -9 (`mtime=0`) of an `LFVREC1` stream, the same container as a
recording:

1. `header` with `"$delta": true`: only the top-level keys whose JSON differs from the base header, plus the point's
   own header blobs. The player rebuilds the header as `{...base, ...delta}`, not recursively: a top-level key is
   replaced whole. The base header is the header of the screen's default point.
2. The world's messages in order. Frames come at the screen's `frame_dt`. A frame's dropped blobs are absent, and the
   view must cope with that (§2.4).
3. `end {reason: "atlas"}`.

**Quantised blobs** (a protocol change, small and backwards compatible). A blob's descriptor in `meta.blobs` may carry
`q: {enc: "lin" | "sqrt", lo, hi}` (scalars, or arrays per column for a 2-D blob). The stored dtype is `u1` or `u2`.
`protocol.decode` (Python) and `api.js decode` (JS) return a float array: lin gives `lo + v / max · (hi − lo)`, sqrt
gives `hi · (v / max)²` (`max` = 255 or 65535). Nothing else changes. A view receives a `Float32Array` where it used to
receive a `Float64Array` or a `Float32Array`. Encoding is done only by the packer (`headless.pack`), which reads a
screen's `quantize` map (`{"<message type>.<blob>": "u8sqrt" | "u16"}`). The packer measures the largest error of each
quantised blob over the atlas and writes it into the manifest (`quant`). The registry refuses a quantisation the
world's view does not declare as safe (§2.4). Recordings may use the same `quantize` (u32's Watch: §6.1).

**Manifest** `atlas.<hash8>.json`, one per atlas:

```json
{"world": "s03_projectile", "atlas": "explore", "atlas_version": "1", "key": "<16 hex>", "version": "1.0",
 "code_hash": "<12 hex>", "recorder_hash": "<16 hex>", "made": "2026-…Z", "seed": 1,
 "controls": [{"param": "h_m", "values": [0, 1, 2, 3, 5, 10], "default": 1},
              {"param": "v0", "values": [5, 10, 15, 20, 25], "default": 15},
              {"param": "angle_deg", "values": [0, 5, …, 90], "default": 45},
              {"param": "air", "values": [false, true], "default": false}],
 "base": {"file": "base.<hash8>.lfpt.gz", "bytes_gz": 2950, "sha256": "…"},
 "points": [["p0.<hash8>.lfpt.gz", 4380, 0], …],     // flattened row-major over controls; [file, bytes_gz, state]
 "refusals": [{"$t": "The ball starts on the ground moving along it: no flight", "a": {}}],  // state k ≥ 1 → refusals[k-1]
 "checks": {"ok": 5650, "failed": 0, "expected": 0, "info": 0, "na": 0},
 "quant": {"traj.s": {"enc": "u16", "max_err": [1.2e-3, 6.1e-4, …], "unit": ["s", "m", …]}},
 "references": {…},                                    // lab steps only: §2.3 "law"
 "cpu_s": 61.0, "bytes_gz": 4.4e6, "frame_dt": 0.0333, "stop": {…}}
```

A point's file is found by its flattened index. `base` is the base header (one message), loaded once per screen. The
manifest is small: about 40 B per point, 45 kB for S03's 1130 points before Pages' gzip.

**Where the files live:**

```
visualizations/recordings/<world>/index.json                      + "atlases": [{id, file, key, points, bytes_gz, checks, cpu_s}]
visualizations/recordings/<world>/<rec>.<hash8>.lfrec.gz          (unchanged)
visualizations/recordings/<world>/atlas/<atlas>/atlas.<hash8>.json
visualizations/recordings/<world>/atlas/<atlas>/base.<hash8>.lfpt.gz
visualizations/recordings/<world>/atlas/<atlas>/p<i>.<hash8>.lfpt.gz
```

`<atlas>` is the screen id (`explore`) or `lab.<step>` (`lab.heights`). The site copies the same tree under
`recordings/`. A one-file-per-point layout is chosen over chunks along an axis: S03's points are 3–7 kB and u32's
about 110 kB, so one request per point is cheap. Prefetching the neighbours (±1 along each control) hides the latency
of dragging a slider.

### 1.4 Index, keys and staleness (the recordings' machinery, extended)

- **Atlas key** = `sha256(atlas spec + ATLAS_VERSION + recorder_hash + code_hash(world))[:16]`. The atlas spec covers
  the preset, controls and values, seed, `frame_dt`, stop, keep and drop, quantize, and for a lab step its fixed values
  and the law reference's id. `sitelib.RECORDER_FILES` gains `site/atlas.py` and `server/lfviz/headless.py`.
- `plan.py` lists every atlas with its key and state, `present | stale | missing`, as for recordings. The **world key**
  (the CI cache key) covers its recordings' and its atlases' keys. `--stale` re-records a world whose recordings or
  atlases are not all present.
- `index.json` gains `atlases` (one entry per atlas: id, manifest file, key, points, refused, bytes_gz, checks, cpu_s,
  version, code_hash, made). An atlas not built now keeps its old entry only while its key is current (review F9's
  rule, as for recordings).
- `/api/recordings` and `api/recordings.json` carry the `atlases` of each world through `index.json` with no change of
  route. The player finds a manifest there.

### 1.5 How a view renders a point without the server

`player.js` keeps a world's record (`W`: header, frames, accumulative messages, key frames) and feeds the view up to
the cursor (`newWorld`, `onMessage`, `feedView`, `rebuildView`, `keyBefore`, `asOf`). This part is extracted, unchanged
in behaviour, into `player/js/record_core.js`: `makeWorld(header, blobs)`, `ingest(W, msg)`,
`showAt(view, W, t)`. Both the live player and the screens use it. A point is decoded (`decode`, quantised blobs
included), its header merged with the base, and its messages ingested into a fresh `W`. The view is then shown at the
point's time. The view is the world's ordinary `web/view.js`, imported through the import map, so it is the same file
on the server and on the site. Key frames work as in the player (points are short; S03 has 60–170 frames).
`keyframes.mjs` guards the extraction.

### 1.6 Stochastic worlds (u32's hits)

A stochastic point stores **one sample**: 5000 detections, drawn by the world's seeded generator in its own order and
times. It also stores **the distribution**: the run's computed ensemble expectation (`c_all`, and `c_cl`, the curve
without interference) on the screen's bins, in the same `segment` message the live world sends. Its frames carry the
run's χ² and p of the sample so far against that expectation. Explore draws the histogram of the hits up to the cursor
and, as an overlay, the expectation scaled to the count. The passport says «one sample of 5000 particles (seed 1); the
curve is the run's expectation». The live run with the same seed gives another realisation with the same statistics
(review P17-site F11). On a server, «Another sample» computes the point live with the next seed (§3.7). The site
stores no second sample.

### 1.7 How the atlas is made: offline, locally and in CI

- `site/atlas.py --world <id> [--atlas <id>] [--out DIR]` builds every atlas of a world through `headless.run_spec`,
  point by point, and writes the files and manifest. `site/record.py --world <id>` calls it after the recordings, so
  one command (and one CI matrix entry per world) makes everything the site needs for that world. `--stale` and
  `--all` behave as now.
- Locally: the command of `RULES.md` §9 (Docker, `--memory`, CPU, `LFPHYS_NO_GPU=1`). The site's recordings folder is
  git-ignored, as now.
- CI (`.github/workflows/pages.yml`): no new job. The `record` job's matrix entry per world builds recordings and
  atlases, cached by the world key. CPU time *measured*: u32's 48 points take 47 s, at 0.90–1.12 s per point; S03's
  1130 integrations take 1.7 s, at 1.5 ms each. With the runner and the packing per point, S03 is well under 2 min
  (*estimate*: 1130 × ~50 ms). Both are far inside the 300-minute job limit.
- Budgets are checked when the atlas is built (§1.8) and again by `site/check.py`.

### 1.8 Budgets and sizes

Budgets (`sitelib.BUDGET`, decimal units, gzip):

| item | target | hard limit | over the target |
|---|---|---|---|
| one point file | 150 kB | 400 kB | the build fails over the limit; over the target it warns (a world may be accepted with a reason, `sitelib.ACCEPTED`) |
| one atlas (screen or lab step) | 6 MB | 12 MB | warns; fails over the limit: fewer values, a coarser display grid, or more quantisation |
| one world: recordings + atlases | 12 MB | 25 MB | unchanged; atlases now count |
| the site | 600 MB | 900 MB | unchanged |
| controls per atlas | — | 5 (school), 6 (standard) | registry |
| points per atlas | 1500 | 3000 | registry (the product of the value counts) |

Sizes of the pilots:

| item | content | size (gzip) | source |
|---|---|---|---|
| u32 point, as emitted today | map f4 260 × 300, 40 flow lines f8, 5000 hits with 7 columns | 0.62–0.64 MB | measured, 3 points |
| u32 point, packed (§1.3) | map u8 √, 20 flow lines u16, hits t, x u16 and y, flags u8, curves f4, header delta | **94–121 kB, median 110 kB** | measured, 168 points |
| — of which | map 42 kB; flow lines 15 kB; hits t 10 + x 10 + y 5 kB; screen grid 4 kB; curves 1.7–8.7 kB | | measured, typical point |
| u32 Explore atlas | λ {400, 500, 600, 700} nm × d {50, 100, 200, 300} µm × a {10, 20, 40} µm = 48 points | **5.16 MB**, CPU 47 s | measured (sum of the packed points) |
| u32 Watch («story», 60 s × 20 fps, 4 segments) | as emitted today | 2.48 MB, CPU 6.1 s | measured |
| u32 Watch with quantised segments | segments' map and flow lines quantised as in Explore | ≈ 0.9 MB | estimate from the measured parts |
| u32 recordings kept (young, eraser, Aharonov–Bohm) | unchanged | 0.74 + 0.65 + 0.68 MB | measured (local index) |
| **u32 world** | Watch + 3 recordings + Explore | **≈ 8.2 MB** (target 12) | estimate |
| S03 point, typical (h 1 m, v0 15 m/s, 45°, air) | frames 30 per world second, samples 120 per world second | 7.0 kB f4; **4.5 kB u16** | measured on a stand-in stream (Appendix A) |
| S03 point, longest (h 10 m, 25 m/s, 90°, 5.47 s) | same | 12.7 kB f4; 7.3 kB u16 | measured, stand-in |
| S03 Explore atlas | 6 × 5 × 19 × 2 − 10 refused = 1130 points | 7.25 MB f4; **≈ 4.4 MB u16** | f4 measured; u16 estimate (ratio 0.57–0.64 measured on two points) |
| S03 lab atlases | parts A, B, C (§5.3): 17 + 13 + 22 points | ≈ 0.2 MB | estimate from measured stand-ins (27 points 44 kB; 60 points 0.34 MB f4) |
| S03 Watch | 40 s × 20 fps, two balls | ≈ 0.2 MB | estimate (S03 frames are a few hundred bytes) |
| **S03 world** | | **≈ 5 MB** | estimate |

The stand-in S03 stream is the integrator's output put into protocol messages: one `traj` chunk and one frame per
frame, the events and four checks. The real world adds per-frame `meas`, about +40 % before gzip and much less after;
the S03 agent measures it and updates this table.

What this means for the site: today's 17 demonstrations' recordings take 47 MB (the local index). With atlases,
an average of 5–8 MB per world is affordable for about 80–100 demonstrations inside 600 MB. The levers are written in
§10, and the budget check enforces them, so nothing exceeds the limit unnoticed.

---

## 2. The registry and the world contract

### 2.1 `VIZ["screens"]`

A list, in tab order. Each entry has `id`, `kind` (`watch` | `explore` | `lab`) and `label` (a `T`; the default
label is the kind's). Example for S03 (abridged; the full one is in §5):

```python
"screens": [
  {"id": "watch", "kind": "watch", "recording": "independence"},          # a recording of VIZ["recordings"] with captions
  {"id": "explore", "kind": "explore", "preset": "field", "fixed": {},   # fixed: values on top of the preset, not controls
   "controls": [{"param": "h_m", "values": [0, 1, 2, 3, 5, 10], "default": 1},
                {"param": "v0", "values": [5, 10, 15, 20, 25], "default": 15},
                {"param": "angle_deg", "values": list(range(0, 91, 5)), "default": 45},
                {"param": "air", "values": [False, True], "default": False, "label": T("Air resistance")}],
   "acts": "next",                       # a change acts on the next launch ("next") or at once, the cursor kept ("now")
   "time": "flight",                     # "flight": ▶ launches from t = 0; "buildup": the cursor is the count; "none": static
   "frame_dt": 1 / 30, "stop": {"event": "landing", "after_s": 0.3, "max_world_s": 12},
   "drop": {"types": [], "frame_blobs": []}, "quantize": {"traj.s": "u16"},
   "overlays": ["trace", "strobe", "v", "v_parts", "a", "energy"],         # ids the view declares (§2.4); defaults there
   "traces": 5,                          # at most 5 earlier points kept, fading
   "readouts": ["range", "flight_time", "apex_h"]},                      # measurables shown when the time reaches them
  {"id": "lab", "kind": "lab", "instruments": {...}, "steps": [...], "worksheet": {...}},
]
```

Rules for every field:

- `controls[].param` is a parameter of the schema. Its values are valid for it (type, range, options). Each grid point
  is resolved through `schema.resolve(preset, values)` at build time, and a refusal there is a registry error unless
  the world's `check_params` refuses it (then the point is `refused`, §1.2). `label` defaults to the parameter's
  label; `kind: "toggle"` is implied for two boolean values.
- A school screen has no law parameter among its controls (rule 4: no modified physics at school). A standard screen
  may have one. The player then flags it, as the live player does («MODIFIED PHYSICS: …»), at the control and in the
  top bar while a modified point is shown.
- A **Watch** screen exists only when the phenomenon develops in time (owner's concept). Its recording names a
  `VIZ["recordings"]` entry, and that entry must have `captions`.
- `acts`, `time`, `traces` (0–5), `overlays` (ids the view declares) and `readouts` (measurables the world declares in
  its header) are checked against the world's own declarations.

### 2.2 Recordings: captions, speed in scripts, quantisation

The recording spec (`RULES.md` §8) gains:

- `captions: [{"at": seconds, "text": T, "hold": seconds?}]`: texts over the played time, «what to look at». The
  recorder writes each one into the stream as an accumulative message `caption {t, text, n}` at its frame, with the
  world time of that frame. So a caption keeps its place under frame thinning and under the script's speed changes,
  the player shows it as of the cursor like an event, and key frames hold it. The captions are part of the spec and
  therefore of the key.
- `speed` among the script's commands (`RECORDING_LIMITS["commands"]`): it changes no world state (the runner's
  playback speed only), and `record()` already advances by `runner.speed / fps`. It lets a story go from one particle
  at a time to thousands.
- `quantize`: as for atlases (§1.3).

### 2.3 Lab work: instruments, steps, the table, the plot, the fit, the law, the worksheet

```python
"instruments": {
  "tape": {"kind": "ruler", "label": T("Measuring tape"), "unit": "m", "division": 0.001, "error": 0.0005,
           "reads": "range"},                         # a measurable of the world, read at the cursor
  "ruler": {"kind": "ruler", "label": T("Ruler"), "unit": "m", "division": 0.01, "error": 0.005,
            "reads": "control:h_m"},                  # a set-up value, read as the instrument shows it
  "protractor": {"kind": "protractor", "label": T("Protractor"), "unit": "°", "division": 1, "error": 0.5,
                 "reads": "control:angle_deg"},
  "stopwatch": {"kind": "stopwatch", "label": T("Stopwatch"), "unit": "s", "division": 0.01, "error": 0.2,
                "manual": True, "error_note": T("your reaction time, about 0.2 s")}},
"steps": [{"id": "heights", "title": T("Height and range"), "goal": T("…"), "preset": "chute",
           "controls": [{"param": "h_m", "values": [0.20, 0.25, …, 1.00], "default": 0.5}],
           "fixed": {"v0": 1.5},                      # the chute's speed: part of the step's set-up, shown, not a control
           "instruments": ["ruler", "tape", "stopwatch"],
           "columns": [{"id": "h", "label": T("h, m"), "from": "ruler"},
                       {"id": "L", "label": T("L, m"), "from": "tape"},
                       {"id": "sqrt_h", "label": T("√h, m^½"), "of": "h", "op": "sqrt"}],
           "plot": {"x": "sqrt_h", "y": "L", "fit": "line0", "fits": ["line0", "line"]},
           "law": {"quantity": "slope", "label": T("k = L / √h"), "unit": "m^½", "reference": "k_horizontal"},
           "frame_dt": 1 / 120, "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 3}, "quantize": {...}}],
"worksheet": {"frp": [...], "equipment": [T], "questions": [{"q": T, "answer": T}], "teacher": [T]}
```

- **Instruments** (`lab.js`). A reading is `division × round(value / division)`, and its error is the declared
  `error`, by default half a division (ФРП 7: «погрешность измерений»; the worksheet says which convention is used).
  `reads` names a measurable (read at the cursor; «Nothing to measure yet: the ball has not landed» before its event)
  or a set-up value (`control:<param>`). A manual stopwatch starts with the launch and stops when the student presses
  it: the reading is the world time at the press, at the playback speed in force (1× by default, and «slow» is
  refused for a manual stopwatch, so the reaction is real). The instrument model is not physics: it rounds a computed
  value. It is declared data, tested against Python fixtures.
- **Columns**: `from` an instrument, or derived `of` + `op`: `sqrt`, `square`, `sin2` (sin 2θ, θ in degrees),
  `inverse`, `log`. An error is propagated as |f′(x)|·σ_x. The table keeps rows per step in the browser
  (`localStorage`, wrapped in try/catch; a convenience only). It can be cleared, a row deleted, and the table exported
  as CSV with the errors.
- **Plot**: any two columns (school: the step's default, changeable), with error bars.
- **Fit** (`fit.js`): `line0` (y = b·x), `line` (y = a + b·x), `quadratic` (its vertex x* with σ from the covariance:
  a maximum found from points), and at `standard` also `power` (a line in log–log). It is a weighted least squares with
  effective variance σ_i² = σ_y,i² + (b·σ_x,i)², iterated three times (Orear, Am. J. Phys. 50, 912 (1982); to be
  checked against the text before it is cited in a user document, AGENTS rule 11). The parameters' σ come from the
  covariance, scaled by √(χ²/dof) when that ratio exceeds 1 (the Birge ratio, as the PDG scales errors). The reason:
  the virtual bench repeats exactly, so the scatter of the points comes only from rounding, and the errors must come
  from the instruments. A real bench scatters, and the scaling then takes the scatter into account. The Python
  reference is the new `lfphys.tools.stats.linear_fit(x, y, sx, sy, model)`. `fit.test.mjs` compares the two on
  fixtures to 1e-12.
- **Law** (`«Check against the law»`): the reference is computed **by the world** when the step's atlas is built. The
  world provides `Simulation.lab_reference(step_id, fixed, values) -> {"value", "unit", "label": T, "how": T, "kind":
  "closed form" | "engine"}`, using its own checks' references (closed forms of accepted physics are allowed there,
  rule 2). The reference is stored in the manifest's `references`. The check is shown as «k = 0.452 ± 0.004 m^½ —
  law: 0.4518 m^½ (closed form k = v₀·√(2/g)) ✓ agrees within two errors» or «✗ does not agree: look at …» with the
  step's hint. When there is no closed form (the optimum angle in air), the reference is the engine's own computed
  value, labelled so («computed by the engine at 0.1° steps; there is no closed form»).
- **Worksheet**: data, not a separate document. The ФРП lab's name is verbatim in Russian, with the English version
  marked as a translation. The goal and the steps come from `steps`. The equipment list, the questions with the
  teacher's answers, and the teacher's notes are all `T` in the i18n catalogues, so the completeness tests cover them
  (rule 13). `player/worksheet.html` + `js/worksheet.js` render it printable (print CSS, one A4 page per part), in the
  viewer's language. The teacher's answers print on a separate page, behind a «For the teacher» switch (question 2 in
  §10).

### 2.4 The view's contract (optional additions; old views keep working)

| addition | meaning |
|---|---|
| `ctx.screen` | `"live"`, `"recording"`, `"watch"`, `"explore"` or `"lab"`; a view hides what the screen does not need (u32: its quick set-up bar and its set-up panels in Explore) |
| `ctx.ui` | `"school"`, `"standard"` or `"full"` |
| `view.overlays` | `[{id, label: T, default}]`: what the view can toggle; `view.setOverlay(id, on)` |
| `view.setTraces(list)` | earlier points to draw faded: `[{key, label, W, t, alpha}]`, `W` a decoded world from `record_core`; the view draws each up to its own `t` |
| `view.worldToPx(p)`, `view.pxToWorld(q)` | 2-D views: the mapping the lab's instruments overlay uses (a ruler on the ground, a protractor at the launcher) |
| `view.quantSafe` | the blobs the view accepts quantised, `{"traj.s": "u16"}`: the registry refuses a `quantize` the view does not declare |
| tolerance of absent blobs | a frame without its dropped blobs is drawn without them (u32: no particles in flight in Explore) |

The view still computes no physics. It draws computed polylines, interpolates along them (allowed, `RULES.md` §4) and
places a body on its computed path at the cursor's time.

### 2.5 Validation

`registry.check` extended:

- `screens`: kinds, ids, labels as `T`; a Watch only with a recording that has captions; controls as above; grid
  size and control count within the limits; `acts`, `time`, `traces`, `frame_dt` > 0; the stop rule's form;
  `quantize` keys of the form `type.blob` with encodings `u8sqrt` | `u16`.
- School: `screens` must have Explore and Lab work (Lab work may be absent only with `lab_absent: T(reason)` when the
  ФРП has no lab for the topic); no law parameter in any screen; Watch optional by the rule above. `guide` is retired
  (its role is the lab's steps), and the check that asked for it is replaced.
- University: `screens` optional until the world is reworked (§7). Research and laboratories: none required.
- Lab: steps with goal, controls, instruments that exist, columns with sources that exist (instrument ids, earlier
  columns), plot columns that exist, a fit model allowed at the level (`power` only at standard), a law with a
  reference id that the world's `lab_reference` answers (called once per step by the test), a worksheet with the ФРП
  item, the questions and the answers.

`tests/test_site_registry.py` extended: every `T` of the screens, captions, instruments, steps and worksheet is
translated in every language; every screen's atlas is in `plan.py`; the README catalogue lists the screens; a related
world's screens exist. `tests/test_i18n.py` picks up the new msgids through its static scan, which already reads
`viz.py`.

---

## 3. The player

### 3.1 One page per demonstration, screens as tabs

- Address: `run.html?demo=<world>&screen=watch|explore|lab` on the site and `/run?demo=…` on the server
  (`page("run", {demo, screen})`). `?id=` (a live run) and `?rec=` (a recording) keep working. An old world id works
  (aliases). A world without screens opens its first recording, as now.
- The tabs are «Watch · Explore · Lab work». The RU labels are proposed as «Демонстрация · Исследование ·
  Лабораторная работа» (question 1 in §10). Switching tabs keeps each screen's state: the cursor, the controls, the
  traces, the table. The tab is part of the address (`history.replaceState`), so a link opens the same screen.
- On a server the top bar also has «▶ Compute live» (a live run of the screen's preset with the controls' current
  values: `POST /api/runs`, then `/run?id=`, the full player).
- The start page's card shows the screens as its buttons («▷ Watch m:ss», «◎ Explore», «✎ Lab work»), then on a
  server «▶ Compute live». A school card has nothing else. `start.js` reads `screens` from the catalogue.

### 3.2 The layout (PhET-like) for `ui: "school"` and `"standard"`

Desktop (≥ 1000 px):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ ← School · Projectile motion        [ Watch | Explore | Lab work ]   How we know this is right │ EN|RU ◐ ? │
├────────────────────────────────────────────────────────────────┬─────────────────────────────┤
│                                                                │ Height, m      ●──○──○──○  │
│                    the phenomenon (the world's view)           │ Speed, m/s     ○──●──○──○  │
│                                                                │ Angle, °       ────●────   │
│      overlays drawn here; readouts appear when reached         │ Air resistance  [off|on]   │
│                                                                │ ─────────────────────────── │
│                                                                │ Show: ☑ path ☐ strobe      │
│                                                                │       ☐ velocity ☐ forces  │
│                                                                │ Range  —   Time  —          │
│                                                                │ [ Clear traces ]            │
├────────────────────────────────────────────────────────────────┴─────────────────────────────┤
│ ▶ Launch   ⟲   ──────────●──────────────────────────  0.62 s / 1.43 s   speed: [normal|slow]  │
│ (Watch: the caption strip sits above this bar, its chapters are ticks on the timeline)        │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

Lab work replaces the right column with the step card. It shows «Part 1 of 3: Height and range», the goal, the step's
controls (at most 5), the instruments, and «Measure». Under the view are the table, the plot with its fit, and «Check
against the law». The worksheet link sits in the step card.

Phone (390 px wide; one column, no horizontal scroll):

```
┌──────────────────────────────┐
│ ← Projectile motion   ☰  EN │   ☰: How we know this is right, theme, help
│ [Watch|Explore|Lab work]     │   a segmented control, full width
├──────────────────────────────┤
│  the view, full width,       │   aspect kept, at least 360 × 220 px
│  readouts over its corner    │
├──────────────────────────────┤
│ Height, m    ●──○──○──○──○   │   each slider full width, thumb ≥ 44 px
│ Speed, m/s   ○──●──○──○      │
│ Angle, °     ──────●──       │
│ Air          [off | on]      │
│ Show ▾ (overlays fold)       │
├──────────────────────────────┤
│ caption (Watch)              │
├──────────────────────────────┤
│ ▶  ⟲  ─────●──────  0.6 s    │   sticky at the bottom
└──────────────────────────────┘
```

Lab work at 390 px: the view, then the step card, then the table (scrolls inside its own box), then the plot. «Measure»
and «Check against the law» are full-width buttons.

### 3.3 What is shown, folded or hidden by `ui`

| part | school | standard (university) | full (research, laboratories) |
|---|---|---|---|
| screens | Watch, Explore, Lab work | Watch, Explore (Lab work when a world has it) | today's player only |
| controls | ≤ 5 per screen or step; grid values only on the site | ≤ 6; «More» folds secondary overlays; a law control flagged | all |
| transport | ▶/❚❚, ⟲, timeline, speed normal/slow | ▶/❚❚, ⟲, timeline, the log speed scale | as now |
| checks | «How we know this is right»: «✓ 6 checks agree with the laws», the list in plain words | the full table (computed ↔ reference, rel, tol) in the same drawer | the right column, as now |
| «Physics of this world», events, passport (recording or atlas: key, code, seed, date) | in the drawer | in the drawer | as now |
| parameters form, seed, devices, precision, slice gizmos, «Instruments» with sweeps, world switch | hidden | hidden (in «▶ Compute live») | as now |
| CSV | the lab's table | the lab's table; the shown point's series (built in the browser from the decoded point) | as now |
| modified physics | never | allowed in Explore when the world declares it, flagged in red at the control and in the bar | as now |

### 3.4 `explore.js`

- It loads the manifest (from `apiGet("recordings")` → the world's `atlases`) and the base header, then the default
  point.
- **Sliders** have detents at the grid values only. A value between detents cannot be chosen on the site, and on a
  server it can (§3.7). A slider's tooltip names the value. A refused combination shows its refusal under the
  controls, and ▶ is disabled with that reason.
- **Loading**: `fetch(url(...))` → `DecompressionStream("gzip")` → decode → `record_core.makeWorld`. The LRU holds
  24 points or 40 MB. After each load the neighbours (±1 along every control) are prefetched at low priority, at most
  two requests at a time. A point slower than 300 ms shows «loading…» over the controls, never a blank view.
- **Time**: `time: "flight"`: «▶ Launch» starts the armed point at t = 0. Every launched shot keeps its own launch
  time on one shared playback clock, so up to `traces` shots fly or lie on the ground together. The timeline shows the
  latest shot and scrubbing moves the shared clock. `time: "buildup"`: the cursor is the world time of the point
  (u32: hits so far), and a change of control keeps it (`acts: "now"`), so two points are compared at equal counts.
  `time: "none"`: no time bar.
- `acts: "next"`: a change arms the next point. The view shows the new set-up at once (the launcher at the new angle,
  from the new point's header) while shots already launched go on. `acts: "now"`: the shown point is replaced and the
  cursor kept.
- **Traces**: the last `traces` points launched (or, for `acts: "now"`, the last points shown), fading, each with a
  small label of its values. «Clear traces» removes them. A trace is drawn by the view from its own messages up to its
  own time (`setTraces`).
- **Overlays**: the view's `overlays`, toggled. The defaults come from the screen.
- **Readouts**: a measurable is shown once the shown point's time has reached the event that defines it, and as «—»
  before that.
- **Passport** (in the drawer): the atlas key, the code hash, the seed, the point's values and its index, «computed
  by the engine when the site was built» or «computed live on this server at …».

### 3.5 `lab.js` (and `fit.js`)

The step card, the instruments drawn over the view through `worldToPx` (an SVG layer: the tape on the ground with its
divisions, the protractor at the launcher, the stopwatch as a widget), «Measure» (one row: every instrument of the
step read at the cursor, with errors; refused with a reason when an instrument has nothing to read), the table, the
plot with the selected fit and its line, the fit's result with σ and, at standard, χ²/dof, and «Check against the law»
(§2.3). The steps run in order, and a step can be revisited: each step keeps its own table. Lab work uses the step's
atlas (`lab.<step>`) exactly as Explore uses its own, so it works on the public site.

### 3.6 `watch.js`: captions over the recording

The Watch screen is the recording mode of the player (`?rec=`), embedded, with two additions. The **caption strip**
shows the latest `caption` message as of the cursor, in large type at school; it sits over the view's lower edge on a
desktop and under the view at 390 px. The **chapters** are the captions as ticks on the timeline: a click jumps there,
and ◀◀ / ▶▶ go to the previous or next chapter. The playback starts at the beginning and pauses at the end. A
recording without captions (today's) plays as now. «More recordings» (u32's young, eraser, Aharonov–Bohm) is a select
in the Watch screen.

### 3.7 Server mode: «compute live»

- `POST /api/atlas/<world>/<atlas>/point {values, seed?}` → `200 application/gzip`: the point's stream, the same
  bytes a site build would make for those values. A `400 {error, hint}` (`Refusal`) comes back for values the schema or
  `check_params` refuses. `lfviz/app.py` routes it, and a new `lfviz/atlas_live.py` runs `headless.run_spec` in a
  separate process (the sweep's pattern: `RLIMIT_DATA` from `LFVIZ_POINT_MEM_GB`, by default half a worker's budget;
  `oom_score_adj` 1000; a CPU-time limit `LFVIZ_POINT_TIMEOUT_S`, 120 s by default). One point at a time per server;
  `429` beyond a queue of four.
- **Cache**: `runs/atlas-live/<world>/<atlas>/<key16>.lfpt.gz` (git-ignored, under the runs' removal period). The key
  covers the atlas key without its grid, plus the values and the seed. An on-grid value is served from the local
  atlas when present; otherwise it is computed (or fetched from the public site when published and of the same
  version, as recordings are, `RULES.md` §9).
- In the player, on a server: the sliders also move freely between the detents. Releasing at an off-grid value
  computes the point. It is drawn when it arrives and labelled «computed live» in the passport and on its trace.
  «Another sample» on a stochastic point asks for the next seed.

### 3.8 Sub-path and static-site compatibility

Every fetch goes through `url()`: the manifest and the point files under `recordings/<world>/atlas/…`, the worksheet
page through `page("worksheet", {demo, lang})` (`base.js` `SITE_FILES` gains `worksheet`). The live-point POST is
built only when `MODE === "server"`. The views are imported through the import map, as now. `apiGet` is unchanged:
the manifest's path comes from `api/recordings.json`. `site/check.py` already fails on an absolute path in a string
literal. It is extended to every atlas file: the manifest against its files (size, sha256), the base, the budgets and
the keys. `site_smoke.mjs` serves the site under `/lfphys/` and opens every screen of both pilots.

### 3.9 Phone width (390 px)

- Below 1000 px: one column (§3.2). The view gets the full width and a world-declared aspect ratio. The time bar is
  sticky. The tabs become a segmented control. «How we know this is right», the theme and help go under ☰.
- Touch targets are at least 44 × 44 px (sliders' thumbs, ▶, «Measure»). Sliders move by drag and by tap on a
  detent. Labels never shrink below 14 px.
- The table scrolls inside its box, and the page never scrolls sideways. The browser test checks
  `document.scrollingElement.scrollWidth ≤ 390` on every screen of both pilots, in EN and in RU (Russian labels are
  longer).

### 3.10 The start page and the READMEs

The card's buttons as in §3.1. The generated README catalogue (`site/readme.py`) lists each world's screens with links
(«Watch · Explore · Lab work») when the site is published, as it does for recordings. The school banner on `#school`
(«until AB1 …») gives way to S03's card once it lands.

---

## 4. Engine M1 for S03

The layers rule (`LAYERS.md`) places it so:

| module | layer | content | references for the tests |
|---|---|---|---|
| `lfphys.core.mechanics` (`__init__`, `particle.py`) | core | point bodies in a uniform gravitational field with any declared force per body; integration by `scipy.integrate.solve_ivp` DOP853 (rtol 1e-11, atol by scale) with dense output; event location (landing on y = y_ground, apex vy = 0, and any declared event) by the integrator's events; sampling at a fixed Δt (1/120 s by default, so that strobe times of 0.1 s fall on samples); the drag's work W carried as a fifth state, so that E_k + E_p − W = E₀ is a running check; `g` from `scipy.constants.g` (the conventional standard gravity, 9.80665 m/s²; a world states that local g differs by up to 0.3 %) | no drag: x(t), y(t), T, L, H in closed form; linear drag: x(t), y(t) and the landing time from a height h in closed form, T = τ·[c + h′ + W₀(−c·e^{−(c+h′)})] with c = (v₀y + gτ)/(gτ), h′ = h/(gτ²) (Lambert W, principal branch; derived and checked for this design to 5e-15–8e-13, Appendix A); energy bookkeeping |
| `lfphys.core.mechanics.drag` | core | linear (Stokes) drag F = −3πμ·d·v of a sphere, with its validity Re ≲ 1 stated and the Reynolds number computed along the path; the air's density and viscosity from `core.data` | Stokes's law; terminal speed v_t = mg/(3πμd) in closed form; the run's own Re |
| `lfphys.theories.models.drag_quadratic` | theories/models | F = −½·ρ·C_d·A·|v|·v with a constant C_d. A model with a fitted parameter: it conflicts with the real C_d(Re) (the drag crisis near Re ≈ 3·10⁵, rough or felt surfaces, the Magnus force of a spinning ball). Its validity is computed along the path (the Reynolds number against the stated range of the constant C_d). It also provides the **second method**: the hodograph quadrature | vertical motion: up v(t) = v_t·tan(arctan(v₀/v_t) − g·t/v_t), down v(t) = v_t·tanh(g·t/v_t); 2-D: (1) the hodograph's exact first integral 1/u² = 1/u₀² + (k/g)·(F(θ₀) − F(θ)), F(θ) = sin θ/cos²θ + ln tan(θ/2 + π/4), u = v·cos θ, k = ρC_dA/(2m), with t, x, y as quadratures in θ (derived here from dv_x/dθ = k·v_x³/(g·cos³θ); measured agreement with DOP853 1.4e-12 in T and 1.3e-12 in L); (2) an independent integrator, Radau IIA (implicit, another family), measured 1.5e-12 |
| `lfphys.core.data.fluid_properties` | core (data) | moved from `core.fluids.lbm` (one place for the data: water, IAPWS through the NIST WebBook; air, the U.S. Standard Atmosphere 1976), with `lbm` re-exporting it | its existing tests move with it |
| `lfphys.tools.stats.linear_fit` | tools | the lab's fit (§2.3): `line0`, `line`, `quadratic`, `power`, effective variance, Birge scaling | closed forms on exact data; Monte Carlo coverage of σ (95 % intervals cover in 95 ± 1 % of 20 000 draws) |

**Constants and data with sources:** C_d = 0.47 for a smooth sphere at 10³ < Re < 2·10⁵, a textbook value. It is to
be checked against a named drag-curve source (e.g. White, *Fluid Mechanics*, the sphere's drag curve) before it is
quoted (AGENTS rule 11), and is labelled «illustrative» until then (`RULES.md` §2 rule 9). The air at 20 °C and
101 325 Pa has ρ = 1.204 kg/m³ from the USSA 1976 formula already in the engine.

**Accuracy** *measured* with a stand-in of exactly this design (Appendix A): no drag against the closed form 8e-16;
linear drag 1.3e-13; quadratic drag against the hodograph 1.4e-12 and against Radau 1.5e-12; energy balance 1.7e-12.
The module's stated error is 1e-9 relative, which leaves room for event location and sampling. The tests assert 1e-9.

**Scope.** This is the projectile part of M1 only: point bodies, uniform field, drag. Springs, constraints,
collisions, friction and rigid bodies stay for AB1 and AB2 (`audiences_2026-11-12_plan.md` §6.1). The package is laid
out so they add modules (`constraints.py`, `contact.py`) without changing `particle.py`'s interface.

**Reviews.** The engine part gets an independent physics review (rule 6) before S03 is reported.

---

## 5. The S03 world: `visualizations/s03_projectile/`

### 5.1 Identity and anchors

- `id` `s03_projectile`; title «Projectile motion: thrown horizontally and at an angle» / «Движение тела, брошенного
  горизонтально и под углом к горизонту»; `audience: "school"`, `section: "mechanics"`, `ui: "school"`; no law
  parameters (rule 4); `related`: `S02`, `S09`, `U01` (planned) and `p08` (planned).
- `curriculum` (from the plan's row S03, to be checked word for word against the ФРП PDFs before commit, AGENTS rule
  11):
  - FRP-OOO-2025-base, grade 7, the research lab «Проведение исследования по проверке гипотезы: дальность полета
    шарика, пущенного горизонтально, тем больше, чем больше высота пуска»;
  - FRP-SOO-2025-base, grade 10, the demonstration «Наблюдение движения тела, брошенного под углом к горизонту и
    горизонтально» and the lab «Изучение движения тела, брошенного горизонтально»;
  - AP1 unit 1; IB-2025 A.1; AQA 3.4.1 (projectiles).

### 5.2 The model (`viz.py`, `engine/`)

- Parameters: `object` (a steel ball 20 mm, 32.9 g; a ball 67 mm, 58 g «like a tennis ball», C_d 0.47,
  illustrative); `h_m` (0–20 m); `v0` (0–40 m/s); `angle_deg` (−30° to 90°); `air` (bool: vacuum or air at 20 °C,
  101 325 Pa); `companion` (none | «a ball dropped at the same moment» | «the same throw in vacuum, for comparison»).
  The comparison is a second body computed without air, labelled as a comparison like u34's ghost. It is not a
  modification, because the world's own ball flies in the chosen medium.
- `engine/`: the launcher and the scene (a table of height h, the floor, a tape along it); the flight from
  `core.mechanics`. The world emits `traj` chunks per frame, `meas` per frame, `event` apex and landing (with T, L, H
  and v at landing), and the checks.
- Checks: energy balance (running); in vacuum T, L, H against the closed forms; in air L and T against the hodograph
  quadrature («second method»); the validity of the constant C_d: the share of the drag's work done at Reynolds
  numbers outside its range must stay under 1 % (near a slow apex Re drops below 10³, but there the drag is
  negligible, so a check on Re alone would fail for no physical reason); the drop companion's landing time against
  √(2h/g) when relevant.
- Refusals (`check_params`): h = 0 with θ ≤ 0 («the ball starts on the ground moving along it or into it: no flight»).
- The view (`web/view.js`): a 2-D side view. The box fits the current shot and the traces; once the experimenter
  zooms, it stays. Overlays: path (on), strobe dots every 0.1 s (from samples at exactly those times), velocity (total
  or components), forces (gravity, drag; arrows scaled for visibility with the scale written: «1 cm = 5 m/s»), energy
  bars (E_k, E_p, the heat W). Readouts: range, flight time, apex height. It also provides the lab's
  `worldToPx`/`pxToWorld`, and `overlays` and `quantSafe` as in §2.4.

### 5.3 Screens

**Watch: yes.** The flight develops in time, and the decisive fact of the topic (ФРП 10's demonstration) is a
comparison in time: a dropped ball and a ball thrown horizontally at the same moment are at the same height at every
moment, so the vertical motion does not depend on the horizontal one. Explore launches one ball at a time, and its
strobe only hints at this. The story makes it the point. Recording `independence`: 40 s, 20 fps, slow motion
(speed 0.1: the 0.50 s flight from 1.25 m lasts 5 s on screen), `companion: drop`, h 1.25 m, v₀ 2 m/s. Each later
flight ends before the next row: from 5 m it lasts 1.01 s (10 s on screen), and the last throw lasts 2.9 s at speed
0.5 (5.8 s on screen):

| at, s | script | caption |
|---|---|---|
| 0 | — | «Two balls start at the same moment: one is dropped, the other is thrown sideways.» |
| 4 | — | «The dots are positions every 0.1 s. At every moment both balls are at the same height.» |
| 12 | `new_world`, params `{v0: 4}` | «Twice the sideways speed: the ball lands twice as far, at the same moment as the dropped one.» |
| 22 | `new_world`, params `{h_m: 5}` | «Four times higher: the flight lasts twice as long, and the range is doubled: L grows as √h.» |
| 32 | `new_world`, params `{companion: vacuum, object: ball67, v0: 20, angle_deg: 45, h_m: 0, air: true}`; `speed 0.5` | «In air a light ball falls short of the same throw in vacuum (grey).» |

**Explore** (`explore`, the preset `field`: the 67 mm ball): h {0, 1, 2, 3, 5, 10} m × v₀ {5, 10, 15, 20, 25} m/s ×
θ {0°, 5°, …, 90°} × air {off, on} = 1140 combinations, of which 10 are refused (h 0 with θ 0) and 1130 computed.
`acts: "next"`, `time: "flight"`, 5 traces. Overlays: path (on), strobe, velocity, components, forces, energy.
Readouts: range, flight time, apex height. *Measured* in the stand-in: in vacuum at 25 m/s the range peaks at 63.73 m
at 45°; with air it is 36.47 m at 40° (36.16 m at 45°). So the shift is visible on the 5° grid.

**Lab work** (`lab`), three parts:

| part | ФРП / AP | set-up (atlas) | measure | plot and fit | «Check against the law» |
|---|---|---|---|---|---|
| A. Height and range | ФРП 7 hypothesis lab; ФРП 10 lab | steel ball 20 mm off a chute, v₀ 1.5 m/s (the chute's, not told to the student), h {0.20, 0.25, …, 1.00} m, air on: 17 points | h with the ruler (1 cm, ±0.5 cm), L with the tape (1 mm, ±0.5 mm); optionally T with the manual stopwatch | grade 7: L(h), the hypothesis «higher → further» seen; grade 10: L(√h), `line0` | k = v₀·√(2/g) (closed form; the engine's air effect here is 0.1 %, *measured* 0.097 % at 2 m/s from 1 m, below the tape's error) |
| B. Angle and range | ФРП 10 demonstration; AP1 U1 | the ballistic launcher on the floor (h 0), steel ball, v₀ 5 m/s, θ {15°, 20°, …, 75°}: 13 points | θ with the protractor (1°), L with the tape | L(sin 2θ) `line0` → slope v₀²/g; L(θ) `quadratic` → θ* | slope v₀²/g; θ* = 45° (closed form, no drag) |
| C. Air moves the maximum | extension (ФРП 10–11 «сопротивление среды»; AP1 U1) | the 67 mm ball, v₀ 20 m/s, h 0, θ {20°, 25°, …, 70°} with and without air: 22 points | θ, L | L(θ) `quadratic` in each medium → θ* | vacuum: 45° (closed form); air: the engine's optimum at 0.1° steps, labelled «computed by the engine; no closed form» |

The worksheet questions (with the teacher's answers) include: why the stopwatch cannot measure a 0.45 s flight to
better than ±0.2 s, and what to do instead (compute T = L/v₀ or measure L); which angles give equal ranges without air
and why; why the maximum moves below 45° in air; why the chute's v₀ is found from the slope rather than measured.

### 5.4 Size and cost

About 5 MB for the world and under 2 min of CPU in CI (§1.8; the S03 agent replaces these estimates with the measured
numbers).

---

## 6. The u32 rework

### 6.1 Watch: «The double slit, step by step» (recording `story`)

60 s at 20 fps on a new preset `story` (`photon_young` with 20 flow lines; a recording spec names a preset), with
the segments' map and flow lines quantised (§1.3). The script and captions use only the existing live parameters and
the speed (the script's new `speed`):

| at, s | script | caption |
|---|---|---|
| 0 | speed 0.002 (2 photons per second) | «The source sends one photon at a time. Each lands at one point on the screen.» |
| 8 | speed 0.02 | «No single hit shows a pattern, and where the next one lands cannot be predicted.» |
| 16 | speed 0.2 | «Thousands of hits: bright and dark bands appear. The curve is the run's computed expectation.» |
| 22 | — | «The bands are interference: each photon's wave goes through both slits.» |
| 26 | `set {el2: "block"}` | «Slit 2 is closed: the bands vanish; only one slit's broad spread remains.» |
| 36 | `set {el2: "none", wp_mode: "qubit", wp_theta: 90}` | «Both slits open, with a which-path detector at slit 1: no bands, although both slits are open.» |
| 48 | `set {wp_mode: "none"}` | «The detector is removed: the bands come back.» |

*Measured* as emitted today: 2.48 MB gzip, CPU 6.1 s. Quantised, about 0.9 MB (*estimate*). Each change of the set-up
starts a new segment, so the view's «current segment» shows each stage on its own, as the captions say. The existing
recordings `young`, `eraser`, `aharonov_bohm` stay under «More recordings» and get short captions in the same pass.

### 6.2 Explore: λ, d, a → the pattern and the hit histogram

- The preset `photon_young` (photons, plane wave, L₂ = 1 m) with `fixed: {n_bohm: 20}`; controls λ {400, 500, 600, 700} nm
  (the slider coloured by the wavelength), d {50, 100, 200, 300} µm, a {10, 20, 40} µm: 48 points, all with d > a.
- `time: "buildup"`, `stop {world_s: 5.25}` (5000 hits at 1000 per second; *measured* 5193–5196 detected), `frame_dt
  0.25`, `acts: "now"`, 3 traces (earlier points' expectation curves, faded, labelled «λ 500 nm, d 100 µm, a 20 µm»).
- `drop`: `stories`; frame blob `flight`. `quantize`: `segment.map: u8sqrt`, `segment.bohm_x: u16`,
  `detections.t|x: u16`, `detections.y|f: u8`, `header.x: u16`. *Measured* loss: x is quantised in steps of at most
  0.023 of a detector pixel, below what the detector resolves.
- Overlays: the expectation curve (on), «without interference» (the `cl` curve), the wave behind the slits (on), flow
  lines, log scale of the wave.
- Readouts (from the world's checks and frames): the fringe period as computed by the run, next to λL/d as the check's
  reference; hits so far; χ²/dof of the sample.
- 5.16 MB, 47 s CPU (*measured*).

### 6.3 What of today's interface stays at `ui: "standard"`

| today | in Watch and Explore | in «▶ Compute live» (server) |
|---|---|---|
| the top view (wave, particles in flight, flow lines) and the screen with its histogram | stay: the centre of both screens | unchanged |
| quick set-up bar (observer, θ, screen, slit, period) | Explore: replaced by the atlas sliders (λ, d, a); Watch: absent (recorded) | unchanged |
| left «Set-up — changes at once» (47 live parameters), «Actions», «New world: laws…» | hidden | unchanged |
| screen filter (all / detector 0 / 1 / no scattered photon / phase window / dark counts) | hidden in Explore (no marks there); Watch: «all» | unchanged |
| toggles: expectation, wave, flow lines, log scale, current segment | Explore: overlays; «current segment» always on | unchanged |
| ▷ flight, ▷▷ build-up speeds | Watch: chapters; Explore: speed normal / slow | unchanged |
| right: «Checks», «Physics of this world», «Particle», «Model of the slit screen», «Approximations of this segment» | in «How we know this is right» | unchanged |
| right: «Counters and statistics» | one readout line: hits, χ²/dof, p (and |γ₁₂| ± error at standard) | unchanged |
| right: «Latest particles: the chain of causes» | Watch only (a fold under the view) | unchanged |
| «Events», «About the run» | in the drawer | unchanged |

### 6.4 What does not change

The physics, the schema, the 19 presets (one is added: `story`), the checks and the live behaviour of u32 do not
change. Its `Simulation` gains nothing. The view gains `ctx.screen` handling, `overlays`, `setTraces`, `quantSafe` and tolerance of the dropped
frame blob. `test_u32_physics.py`, `test_restore.py`, `test_checkpoint.py` and `keyframes.mjs` keep passing
unchanged. The world's `version` goes 1.2 → 1.3, since the recordings' specs change.

---

## 7. The rework of the other demonstrations (later; not in this step)

One row each. «Watch» means the phenomenon develops in time. «Explore» lists 2–3 controls on an atlas. «Clutter»
names what overloads the page today. Cost is the CPU of today's recordings (local index), which bounds a point's cost;
an atlas for the heavy ones keeps only fixed slices or images, never volumes.

| world | Watch | Explore (controls → what is seen) | clutter today | atlas cost and note |
|---|---|---|---|---|
| u31 light travel | yes: light from the Sun reaches the Earth in 8 min; measuring c from moving frames | split by scenario. «Measuring c»: observer's speed (−0.9 … 0.9 c, 7) × kinematics (SR / ether / ballistic; standard ui flags the last two) → the measured c. «Lensing»: impact parameter × mass → images, deflection | 28 parameters of five scenarios in one form; modifications next to standard presets | cheap (0.6–9.8 s per recording) |
| u33 quantum 1-D | yes: a packet meets the barrier, parts go both ways, single detections | energy E (0.2–1.6 eV, 8) × barrier width (0.2–1.2 nm, 6) → transmitted fraction, detection histogram (sample + the run's probabilities) | interpretation selector (Copenhagen / Bohm / Everett) at the same level as the barrier; ρ in every frame (3 MB recordings) | ρ quantised u8; 48 points |
| u34 orbits | yes: the rosette builds, the clock lags | periapsis r₀ (6–30 M, 7) × speed (0.9–1.3, 5) → the orbit, precession per turn; Newton's ghost as an overlay | units, ghost and gravity law beside the orbit's set-up | cheap (0.2–0.9 s) |
| u35 optics bench | no (a steady split; the photon counting is statistics, not a process) | angle θ (0–89°, 2°) × index n (1.33, 1.5, 1.7, 2.0) × polarisation (s, p, unpolarised) → R and T with photon counts; coatings as a second Explore screen (layer thickness × λ) | 18 live parameters for 6 structures in one form | cheap (0.2 s) |
| u36 QCD | no (static curves) | scale μ (1–100 GeV, log 9) × loops (1–4) → α_s(μ); a second screen: the system (cc̄, bb̄) × κ → levels against PDG | two topics in one world; the sweep parameter | cheap; a standard-ui law control (α_s(M_Z)) flagged |
| u37 Bell test | yes: pairs accumulate, S passes 2; a local model stays below | analyser angle b (0–90°, 5°) × law (quantum / local model, flagged) → E(a, b) with the sample and the run's expectation, S | locality parameters (L, τ, switching) beside the angles | cheap (0.5 s) |
| u38 wave in 3-D | no (a stationary field; today's recording is a static result) | slit width × separation × λ (3 × 3 × 2) → two fixed slices and the screen, not the volume | slice gizmos and layers for a university page | heavy (146 s per world, a 6.3 MB volume); ≤ 18 points of slices (~150 kB each) |
| u39 fast observer | yes: the cube and the ball pass; the Terrell rotation | speed β (0, 0.5, 0.8, 0.9, 0.95, 0.99) × the camera's yaw (5) → the seen image | camera, exposure, EV, resolution beside the scene | one image per point (50–150 kB); 30 points |
| u40 hydrogen 3-D | only the superposition (it sways at the Bohr frequency) | the state (n ≤ 4, l, m: 30) × real/complex → the cloud and its current | the second state's five parameters always shown | cloud u8 per point (~150 kB); 30–60 points |
| u41 quarkonium 3-D | only the superposition | system (cc̄, bb̄) × state (1S, 1P, 2S, 1D) → the cloud and the levels against experiment | as u40 | 7.5 s per point; 8 points |
| u42 Kerr shadow | no (a still image) | spin χ (0, 0.5, 0.9, 0.99) × inclination (17°, 60°, 90°, 163°) → the shadow and the rings | emitter, profile, resolution and ray count beside the physics; the «what if» metric at standard flagged | 3.7–4 s per image; 16 points |
| u43 optical vortices | only the rotating disc (the beat) | l (−3 … 3) × p (0–2) → intensity, phase, angular momentum | six generators (mode, plate, fork, Dove …) and two models in one form | 4–10 s per point; 21 points; generators as screens |
| u44 Mie scattering | no (a still bow; today's recording is static) | drop radius (8 µm … 0.3 mm, 6) × width (0.5–15 %, 3) → the bow's image and I(θ) | light, λ, number of wavelengths, temperature, index beside the drop | heavy (up to 48 s per point); 18 points ≈ 10 min |
| r11 Thomas 3-D | yes: after the loop the gyroscopes are turned | research (`ui: full`): Watch with captions only | — (research-grade) | — |
| r12 double slit 2-D | yes: the wave passes the slits, Bohm paths build the pattern | research: Watch with captions only (≈ 1 s per frame, 0.6–1.4 h per recording: no atlas) | — | — |
| r13 arrival times | yes: the rules diverge near the source | research: Watch with captions only | — | — |

Proposed order after the pilots, in batches of three (rule 10): **EX2** u34, u35, u37 (cheap, clear stories);
**EX3** u33, u31, u44; **EX4** u40/u41 (one template), u42, u43; **EX5** u38, u39, u36; research captions alongside.
The owner confirms the order (question 4 in §10).

---

## 8. Tests and checks

**Engine** (`lfphys/tests/`):
- `test_mechanics_projectile.py`: no drag against the closed forms (x(t), y(t), T, L, H), ≤ 1e-9; linear drag
  against x(t), y(t) and the Lambert-W landing time from h, ≤ 1e-9; quadratic drag: vertical up (tan) and down
  (tanh); 2-D against the hodograph quadrature and against Radau, ≤ 1e-9; energy balance ≤ 1e-9; events: apex and
  landing against the closed forms; sampling on exact multiples of Δt; refusals (h < 0, m ≤ 0, d ≤ 0, NaN); the Reynolds
  range reported.
- `test_layers.py` (existing) covers the new modules' `ABOUT` and their translations; `test_licences.py` is unchanged
  (no new dependency).
- `test_stats_fit.py`: `linear_fit` for every model on exact data; the effective variance against a hand-computed
  case; coverage of σ by Monte Carlo.

**Framework** (`visualizations/tests/`):
- `test_headless.py`: `run_spec` reproduces today's recordings byte for byte (`test_recorder.py`'s fixtures); the
  stop rules (`world_s`, `event` with `after_s`, `max_world_s` failing).
- `test_atlas.py`, on a toy world in `tests/site_worlds/` with a 2 × 3 grid and one refused point: flattening and
  manifest; the same bytes twice; header delta merge equals the full header; quantisation round trip within the
  manifest's stated `max_err`; budgets (over the target warns, over the limit fails); keys and states in `plan.py`;
  a failing check fails the atlas.
- `test_protocol_quant.py`: Python's decode of quantised blobs equals JS's on shared fixtures (u1 and u2, lin and sqrt,
  per-column ranges).
- `test_site_registry.py` (extended, §2.5) and `test_i18n.py` (static scan of the new texts).
- `test_site_build.py`: atlases copied, in `site-manifest.json`; `check.py` fails on a missing or changed point, a
  manifest that disagrees, a stale key, an atlas over its limit.
- `test_atlas_live.py`: the live point endpoint (off-grid value; a refusal is 400 with its `T`; the cache hit; the
  memory limit and the timeout end the process, not the server; 429 beyond the queue).

**Worlds**:
- `s03_projectile/tests/test_s03_physics.py`: every check ✓ at the corners of every atlas grid; the events'
  data against the engine; refusals; the companion's landing time; `lab_reference` for every step against an
  independent computation.
- u32: the existing tests unchanged; `test_u32_screens.py`: the Watch spec's commands apply, and every Explore grid
  point builds with all checks ✓ (in CI the atlas build does this anyway).

**Player** (Node, `player/js/tests/`):
- `fit.test.mjs` against Python fixtures; `atlas.test.mjs` (flattening, snapping, LRU, header merge, dequantisation);
  `lab.test.mjs` (instrument rounding, error propagation of derived columns, CSV); `captions.test.mjs` (the caption
  as of the cursor, chapters under thinning).

**Browser** (Playwright; EN and RU; a private server, never port 8479; and the built site under `/lfphys/`):
- `demo_screens.mjs`: the tabs of both pilots. Watch: captions change with the cursor, chapters jump, the recording
  plays. Explore: sliders take only grid values on the site; the network log shows only the needed point files and
  their prefetched neighbours; overlays toggle; traces ≤ N and fading; a readout is «—» before its event and filled
  after; a refused combination says why; on the server an off-grid value computes and is labelled. Lab work: launch,
  measure, a row with ±, plot, fit, «Check against the law» ✓ on the reference data. The worksheet prints in EN and
  RU (`page.pdf()`), with and without the teacher's answers.
- Phone: the same at 390 × 844. `scrollWidth ≤ 390` on every screen; the time bar is visible; touch targets
  ≥ 44 px; the table scrolls inside its box.
- `i18n_checks.mjs`, `keyframes.mjs` (u32 Live unchanged, and a point world through `record_core`) and
  `start_page.mjs` (the card's screen buttons), all extended.
- `site_smoke.mjs`: every screen of both pilots on the built site; no request leaves the sub-path or goes to `/api/`.

**Site and CI**: `site/check.py` (atlases, budgets, keys) and the `record` job building atlases. No new workflow job.

---

## 9. Implementation plan

The batch is **EX1** (PLAN.md P17, a new item P17.5 «Watch, Explore, Lab work on atlases; pilots S03 and u32»): the
framework, S03 with M1, u32. Every agent works in Docker with `--memory`, on private ports (never 8479), stops
containers by name or PID (never `pkill -f`), and puts no e-mail address in an external request. The contract
between F and P is §1.3 and §2 of this document. Any change to it is made here first.

| step | agent | owns (only these files) | done when |
|---|---|---|---|
| **E** engine M1 (first) | 1 | `lfphys/lfphys/core/mechanics/**`, `lfphys/lfphys/theories/models/drag_quadratic.py`, `lfphys/lfphys/core/data.py` (fluid properties moved in), `lfphys/lfphys/core/fluids/lbm.py` (re-export only), `lfphys/lfphys/tools/stats.py` (`linear_fit`), `lfphys/lfphys/locales/*`, `lfphys/tests/test_mechanics_*.py`, `test_stats_fit.py`, `lfphys/README.md` catalogue rows | engine tests pass in Docker; `ABOUT` and translations complete |
| **F** atlas framework (with E) | 2 | `server/lfviz/headless.py` (new), `server/lfviz/atlas_live.py` (new), `server/lfviz/protocol.py` (`q`), `server/lfviz/registry.py` (screens, limits, `speed` in scripts, `guide` retired), `server/lfviz/app.py` (nested `/recordings/…`, `POST /api/atlas/…/point`), `site/record.py`, `site/atlas.py` (new), `site/sitelib.py`, `site/plan.py`, `site/build.py`, `site/check.py`, `site/readme.py`, `tests/site_worlds/**`, `tests/test_headless.py`, `test_atlas.py`, `test_protocol_quant.py`, `test_atlas_live.py`, `test_site_registry.py`, `test_site_build.py`, the framework's server-side msgids in `locales/` | `test_recorder.py` unchanged and passing; a toy world's atlas builds, checks and is served |
| **P** player (with F, on F's fixtures) | 3 | `player/js/record_core.js` (extracted), `player/js/player.js` (uses it), `player/js/{demo,atlas,explore,lab,fit,watch,worksheet}.js` (new), `player/js/api.js` (decode `q`), `player/js/base.js` (`worksheet`), `player/js/start.js` (screen buttons), `player/run.html` (screens shell), `player/worksheet.html` (new), `player/assets/demo.css` (new), `player/js/tests/*.test.mjs`, `tests/browser/demo_screens.mjs` (new), player-side msgids in `locales/` | node tests pass; `keyframes.mjs` and `record_mode.mjs` unchanged and passing; the toy world's screens work in EN/RU and at 390 px |
| **S** the S03 world (after E's API is merged) | 4 | `visualizations/s03_projectile/**` (viz.py, engine/, web/view.js, tests/, locales/, README.md, README.ru.md), `visualizations/planned.json` (left to the build), `docs/images/s03_projectile.jpg` (posters.mjs) | the world's tests; its atlases within budget with every check ✓; the real sizes replace §1.8's estimates |
| **U** the u32 rework (after F and P) | 5 | `visualizations/u32_double_slit/{viz.py (screens, recordings), web/view.js, locales/*, README.md, README.ru.md}` | u32's existing tests unchanged and passing; its Watch and Explore within budget |
| **I** integration and documents (last) | 6 or the lead | `visualizations/RULES.md` (new §10 «Screens and atlases»; §3 API rows; §8 fields; §9 recordings), `visualizations/README.md`, `README.ru.md` (the owner guide), the root READMEs' hand-written parts, `AGENTS.md` §2 layout row (`atlas/`), `STATUS.md`, `lfphys/PLAN.md` (P17.5 and its status), `lfphys/sources/audiences_2026-11-12_plan.md` (§5.2 and §5.4 pointing here), `tests/browser/site_smoke.mjs`, `i18n_checks.mjs`, `start_page.mjs` | the full suites green in Docker; the site built and checked locally; the browser checks in EN and RU |

Order and parallelism: E and F start together. P starts on F's fixtures (a toy atlas committed under
`tests/site_worlds/`). S starts when E's API is merged. U starts when F and P are merged. I comes last. Merge order:
E, F, P, S, U, I. F and P both add msgids to `visualizations/locales/`, each in its own block, and I merges them.

Then the reviews, each by an agent that wrote none of the part (rule 6). The author of a review never processes it:

| review | scope | folder |
|---|---|---|
| R-E | M1's physics and tests, the drag model's layer and validity, the fit's statistics | `reviews/2026-…_internal_EX1-mechanics/` |
| R-F | the atlas framework: determinism, keys, quantisation losses, the live endpoint's limits, site build and check | `…_EX1-atlas/` |
| R-P | the screens in a browser, EN and RU, desktop and 390 px; rules 2–3 in Explore and Lab work; the lab's measurement and fit | `…_EX1-screens/` |
| R-W | S03 and u32 as a teacher and a student would use them: what each screen shows, captions, worksheets | `…_EX1-worlds/` |

Each review is processed finding by finding in its `RESPONSE.md` by agents other than its author. The folders then
move to `reviews/archive/`. The report to the owner (in Russian) gives the status per item ([useful] / [neutral] /
[weakens] / [error in earlier]), the measured sizes, and links to the screens on the local server and, after his go to
deploy, on the site.

---

## 10. Risks and open questions

Questions for the owner, **decided by the integrator on 2026-11-14** under the owner's «решай сам … и делай» (the owner may
change any of them at the report):
- 1 → EN «Watch · Explore · Lab work», RU «Наблюдение · Исследование · Лабораторная работа». «Демонстрация» is not used for a
  screen because the whole item is already called a demonstration in the catalogue, the READMEs and the site.
- 2 → the answers are on the public site behind the «For the teacher» switch; the repository is public, so hiding them
  elsewhere would only pretend.
- 3 → part C stays, marked «beyond the basic programme».
- 4 → the order as proposed.

The questions as they were put:

1. **The screens' names.** EN «Watch · Explore · Lab work»; RU «Наблюдение · Исследование · Лабораторная работа»
   («Смотреть» was the alternative for Watch, rejected because the other two are nouns). They become glossary terms
   (`RULES.md` §7). Agreed?
2. **The teacher's answers on the public site.** The worksheet prints with or without them behind a «For the teacher»
   switch, so anyone, students included, can open them (PhET publishes its teacher tips openly). The alternative is
   answers only in the repository and on a local server. Which one?
3. **The S03 Lab's part C** (air moves the maximum) goes beyond the ФРП базовый lab list. It is included as an
   extension marked «beyond the basic programme» (AP/IB cover drag qualitatively). Keep it, or leave S03's Lab to parts
   A and B?
4. **The order of the rework** after the pilots (§7: EX2 u34, u35, u37; EX3 u33, u31, u44; EX4 u40/u41, u42, u43; EX5
   u38, u39, u36). Confirm or reorder.

Risks (decided here, no owner action needed):

- **Site size at scale.** Atlases add 5–9 MB per world. The budgets (§1.8) make an overrun fail the build, not pass
  unnoticed. The levers, in order: coarser display grids computed by the engine (u32's map at 130 × 150 saves
  30 kB per point, *measured* 12 kB against 42 kB); byte-shuffled float blobs (landing design §4.4); fewer values per
  control. Moving the site off Pages would be an owner's decision, and the numbers do not call for it before about
  80 demonstrations.
- **Coarse grids feel less free than PhET.** S03 has 5° steps and u32 4 × 4 × 3. This is the owner's rule («only
  computed points»). On a server the same screen computes any value. Prefetching keeps dragging immediate.
- **The extraction of `record_core.js`** touches the player's most delicate code (key frames, history). It is a pure
  extraction, guarded by the existing `keyframes.mjs`, `record_mode.mjs` and `i18n_checks.mjs`, and done first in P.
- **Quantisation must not leak into physics.** Only drawn arrays are quantised, with the loss measured and recorded.
  Measurables, events and checks stay float64. The registry accepts only the quantisations a view declares safe.
- **CI time** grows by about 1 min for S03 and 1 min for u32 (*measured* and *estimated*). Heavy worlds (u38, u44, r12)
  get atlases of slices or images only, or none (§7).
- **The C_d value, the stopwatch's 0.2 s reaction time, Orear's effective variance and the ФРП quotations** are
  unverified until checked against their sources (AGENTS rule 11).
  They are labelled «illustrative» or «to be checked» until then. The S, E and I agents verify them.

---

## Appendix A. Measurements made for this design (2026-11-14)

Docker image `lfphys-viz` (the repository's), CPU only (`LFPHYS_NO_GPU=1`), `--memory` 2–6 GB, 1–2 CPUs, containers
named `lf-xd-*`. The scripts were kept outside the repository, in the integrator's notes.

1. **u32, one point as emitted today** (photon 632.8 nm, d 100 µm, a 20 µm, L₂ 1 m; run until 5000 hits, 4 frames per
   world second; three points). Build 0.48–0.59 s CPU, advance 0.48–0.66 s. The stream is 0.82–0.88 MB, 0.58–0.64 MB
   gzip. The `segment` message is 0.62–0.65 MB raw: the near-field map is f4 260 × 300, 210 kB gzip, and the 40 flow
   lines are f8 901 × 40, 273 kB gzip. The detections are 172 kB raw for 5196 hits (7 columns).
2. **u32, packed as in §1.3, 168 points** (λ 400–700 nm by 50, d 50–300 µm by 50, a 10–40 µm by 10; 20 flow lines).
   94–121 kB gzip per point (median 110 kB); CPU 0.90–1.12 s per point; 18.3 MB in all. The subset of §6.2 (4 × 4 × 3 =
   48 points) totals 5.16 MB. The parts of a typical point: map u8 42 kB (12 kB at half resolution); flow lines u16
   15 kB; hits t u16 10 kB, x u16 10 kB, y u8 5 kB, flags 40 B; the screen grid u16 4 kB; the header JSON 11 kB before
   the delta; checks 2.4 kB. The x quantum is at most 0.023 of the detector pixel.
3. **u32 Watch** (§6.1's script through the recorder's `record()`, `speed` allowed): 1200 frames, 4 segments, 2.48 MB
   gzip (4.74 MB raw: segments 2.49 MB, `stories` 0.86 MB, detections 0.75 MB, frames 0.57 MB), CPU 6.1 s, checks 16
   ok, 1 info, 1 without a reference.
4. **M1 stand-in** (a point projectile with `solve_ivp` DOP853, rtol 1e-11, events for landing and apex; drag work as
   a fifth state). No drag against the closed form: 8.1e-16 (T), 8.3e-16 (L). Linear drag against x(t), y(t):
   1.3e-13, 6.5e-14. Lambert-W landing time: 1.7e-14, 5.0e-15, 8.0e-13 in three cases (h 0, 10, 2 m). Quadratic drag
   (67 mm, 58 g, C_d 0.47, ρ 1.204 kg/m³: k = 0.01729 1/m) against the hodograph quadrature: 1.4e-12 (T), 1.3e-12 (L);
   against Radau: 1.4e-12, 1.5e-12. Energy balance 1.7e-12. CPU 1.5 ms per trajectory over 1130 grid points. The
   longest flight is 5.47 s and the largest range 73.0 m. Steel 20 mm at 2 m/s from 1 m: air shortens the range by
   0.097 %.
5. **S03 point stand-in** (frames every 1/30 s; samples t, x, y, vx, vy, W every 1/120 s in `traj` chunks; the apex
   and landing events; four checks): typical 255 samples, 65 frames, 19.0 kB raw, 7.0 kB gzip f4, 4.5 kB u16; the
   longest 658 samples, 166 frames, 12.7 kB f4, 7.3 kB u16; the whole 1130-point grid 7.25 MB f4. Lab stand-ins: 27
   points (h 0.2–1.0 × 3 speeds, steel) 44 kB; 60 points (θ 10–80° × 2 speeds × air on/off, 67 mm ball) 0.34 MB f4.
6. **Today's recordings** (the local `visualizations/recordings/*/index.json`): u32 young 0.74 MB, eraser 0.65 MB,
   Aharonov–Bohm 0.68 MB; the CPU per recording for §7's costs (u38 146 s, u44 rainbow 48 s, r12 619–1425 s, u41
   7.5 s, u43 4.1–10.5 s, u42 0.4–4.0 s).

## Appendix B. The rules this design keeps

| rule | how |
|---|---|
| 2 computed, not drawn | every point is the world's own run; the browser draws, rounds instrument readings and fits measured data; closed forms appear only as check references and lab references computed by the world |
| 3 causality | a point is fed to the view up to the cursor; readouts and events appear when its time reaches them; traces are earlier experiments, each on its own clock |
| 4 accepted physics | school screens have no law controls; standard screens flag one; drag is a medium, not a modification |
| 5 engine, verified | M1 in the engine with closed forms and two second methods; the quadratic drag as a model with its conflicts |
| 10 batches of three | EX1 = framework, S03 + M1, u32 |
| 11 practice | measured numbers marked; C_d and ФРП quotations to be verified; status tags in the report |
| 12 documents current | the I step's list (§9) |
| 13 languages | every text a `T`; worksheets from the catalogues; EN and RU tested in the browser |
| 14 audiences | school and university screens differ by `ui` (§3.3); research keeps its full player |
| 15 site and registration | atlases built in CI by the world's matrix entry, keyed and checked; the README and the cards list the screens |
| 16 simpler for lower levels | school: ≤ 5 controls, no parameters, seeds, devices or modifications; one drawer for the checks |
