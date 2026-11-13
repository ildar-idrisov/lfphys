# Review i18n-code: the translation mechanism and its use (commit d9da7cb)

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the code under review) |
| Date | 2026-11-12/13 |
| Scope | Local commit `d9da7cb` («Interface in English and Russian (i18n)…»), code correctness only. The renderers `lfphys/lfphys/i18n.py`, `visualizations/server/lfviz/i18n.py`, `visualizations/player/js/i18n.js`. Their use: `server/lfviz/{app,errors,sweep,instruments,playground}.py`, the player's JS, the worlds' text matching (p02, p03, p04, v05, v15). The tests `visualizations/tests/test_i18n.py` + `i18n_tools.py`, `lfphys/tests/test_i18n_engine.py`, `player/js/tests/i18n.test.mjs`, `tests/browser/i18n_checks.mjs`. Spec: the integrator's `SPEC.md` (scratchpad `i18n/SPEC.md`). Rules: `AGENTS.md` §1 and §3, rules 12–16. |
| Not in scope | The quality of the Russian translations. The docs pass (READMEs, guides, `RULES.md`), which the commit message defers to the next commit. Physics. |
| Environment | `lfphys-viz` image (Python 3.11.17), CPU only (`LFPHYS_NO_GPU=1`), `--memory=6g`, repository mounted read-only. JS in `node:20`. Browser checks in Playwright 1.58.2 Chromium (`mcr.microsoft.com/playwright:v1.58.2-jammy`). Private server `lf-rv18c-srv` on port 8651 (2 workers, `LFVIZ_EXTRA` = both fixture folders, runs in `evidence/srv_runs`). The shared server on 8479 was not touched. |

The scripts and their outputs are in `evidence/`. Each check `cNN_*` (Python, Node or shell) and `b01_*` (Chromium) has a `.out`; `out/c04_dynamic_scan.json` holds the extended dynamic scan.

## Summary

There are 15 findings: **2 errors**, **7 should-fix**, **6 nits**.

The core mechanism works:
- `T` survives pickle, copy, `dataclasses.asdict` and JSON (the repo test proves it, and checkpoints use it).
- The two renderers agree on placeholders, nested `T`, lists, `None`, `cap`, `unit`, the period-dropping rule, missing arguments, the sign flag and the Russian CLDR plurals for integers (`c01`).
- The catalogues are complete for what the worlds actually send. `c04` ran **all** presets of all 23 worlds, 12 steps each, and set every live parameter to its min and max: zero `T` msgids were missing from `ru`.
- In a real browser in Russian, the catalogue and the run page of every world show no English prose. The Latin words left are key names (Shift, F) and code identifiers (`b01`).
- `/api/i18n/<lang>` answers 304 to a matching `If-None-Match` and 404 with an `{error: T, text}` body for an unknown language. The HTTP error bodies have the `{error, text, …}` shape the spec asks for (`c07`).

The two errors are both cases where server code compares texts by `str()`. Since texts became `T`, these comparisons silently stopped working:
1. **F1.** The series CSV header names the probe twice: `Probe 1: “Probe 1”: to the nearest particle`. The sweep's measure label does the same.
2. **F2.** The sweep CSV header names the unit twice: `Hold memory, MB, MB`. After a JSON round trip, `str()` of a text is the dict's repr.

The should-fix items fall into three groups:
- **Wrong text in the player:** counts over 10⁶ are rounded (F3), and `?lang=` is lost on the next page (F7).
- **Untranslated or fragile text:** plain-English engine messages still reach the owner (F4), and five worlds match engine messages by their English text (F5).
- **Tests and design:** the tests let several kinds of defect through (F6, F8), and there is no way to serve the catalogue to the static public site (F9).

## Results with their status

| # | check | result | status |
|---|---|---|---|
| R1 | `t1_baseline_tests.out`: `test_i18n.py` (61) and `test_i18n_engine.py` (126) | all pass; 17 entries of `visualizations/locales/ru.json` reported "unused statically", among them `World {n:d} (current): {title}`, which **is** used (`player.js:589` through a ternary: F6) | [useful] |
| R2 | `c01`: 26 shared cases, Python `render` and JS `t()` | agree on placeholders, nested T, lists, None → «—», cap, unit, period-drop, missing args, sign flag. Disagree on bool, float with `:d`, ints without spec, plurals without `n` or with n = −1, 1.0004, NaN/∞, unsupported specs (F3, F10) | [useful] / [weakens] |
| R3 | `c04`: every preset of every world, 12 steps, each live parameter at min and max | 0 `T` msgids without a `ru` entry in any world. Plain strings found are option ids, proper names, formulas | [useful] |
| R4 | `b01`: RU catalogue (demo and playground) and a run page of each of 23 worlds in Chromium | no English prose. Leftovers are key names and code identifiers. No page errors | [useful] |
| R5 | `b01` (1): `/?lang=ru` without a stored choice, then `/settings` | `ru` → `en` (F7) | [weakens] |
| R6 | `c07`: `/api/i18n` | 200 + ETag, 304 on exact match, 404 for `xx`, `RU`, `ru-RU`. Weak/list/`*` validators give 200. RU body 1 338 263 bytes, uncompressed (F13) | [useful] / [weakens] |
| R7 | `c08`: series CSV with `lang=en/ru/xx/""` | headers translated in `ru`, English otherwise | [useful] |
| R8 | `c10`, `c15`: series and sweep CSV headers | object name twice (F1), unit twice (F2) | [weakens] |
| R9 | `c03`: plain-string raises in the engine | 458 (md 140, gravity 113, optics 42, core 35, em 33, quantum 27 …) | [weakens] |
| R10 | The engine agent's claim: the remaining optics messages report programming errors | false for `thin_films.airy`: v05 catches its three ValueErrors at run time and translates them by English substrings (`v05_optics_bench/viz.py:556-565, 876-888`). Several more are input-dependent limits (F4). `c14`: 160 random schema sets of v05, v16, v17, v08 → 0 English owner texts today, held off by world-side copies of the engine's thresholds and by matching | [error in earlier] |
| R11 | `c05`, `c17`: constructed cases against the test tools | 3 of 5 shadowing forms missed, escaped Cyrillic passes, non-literal msgids invisible, 11 local `T` in worlds unguarded (F6, F8) | [weakens] |
| R12 | The commit message: «every user-facing text is a translatable T» | not so for plain engine ValueErrors that reach the owner (F4), nor for the plain-string labels the spec allows | [error in earlier] |

## Findings

### F1 — error — the server's `display_label` names the object twice for every probe or object quantity

**Location.**
- `visualizations/server/lfviz/instruments.py:209-219`.
- Used for the series CSV header (`column_title`, `:222-226`), the series JSON `title`, and the sweep's `measure_label` (`sweep.py:350`, then the sweep CSV and the refusal "the world does not measure …").

**What happens.** `display_label` prefixes the object's label to the quantity's label unless the quantity already contains it:

```python
if ol and not (isinstance(ol, str) and isinstance(lab, str) and ol in lab):
    return T("{object}: {label}", object=ol, label=lab)
```

Before i18n both were strings. Now both are `T`, so the containment test is skipped and the prefix is always added. A world that names its object inside the quantity's label gets the name twice. The p99 toy does this (`T("“{label}”: to the nearest particle", label=o["label"])`), and so does p02's per-particle quantities.

The player does it right: `instruments.js:84-89` compares the rendered strings. So the panel and the downloaded file now disagree.

**Evidence.** `evidence/c10_display_label.out` (p99, one probe added):

```
== CSV header lang=en
"t, s","Probe 1: “Probe 1”: to the nearest particle, m [near.o1]"
== CSV header lang=ru
"t, с","Датчик 1: «Датчик 1»: до ближайшей частицы, м [near.o1]"
```

**Fix.**
- Compare renderings: `render(ol) in render(lab)`. A structural check is better: whether `lab`'s args contain `ol` (`ol in msgids-walk of lab`).
- Regression test: the p99 probe quantity's CSV header contains its object's name once.

### F2 — error — texts read back from JSON are plain dicts; `str()` of them is a repr, and `sweep.with_unit` compares those reprs

**Location.**
- `visualizations/server/lfviz/sweep.py:163-177` (`with_unit` → `has_unit(str(label), str(unit))`).
- Called by `table_csv` (`:885-887`) on a spec read from disk (`:778`).
- The same root cause lurks wherever server code does `str(x)` on a text taken from a record or a spec file: the decoded record holds plain dicts, not `T`. Examples: `playground._setting` `str(p.unit) not in str(lab)`, and `errors.owner_text` on an exception carrying a decoded text.

**What happens.**
- `T.__str__` is the English rendering.
- `json.loads` gives a plain `dict`, whose `str()` is `{'$t': 'Hold memory, MB'}`.
- So `has_unit` never finds the unit, and the CSV header repeats it.

The spec promises "a msgid translated … T survives JSON". It does survive as data, but every string comparison on it breaks.

**Evidence.**
- `evidence/c15_sweep_csv.out`: a real sweep of p97's `alloc_mb` on the private server:

  ```
  "Hold memory, MB, MB","Total energy (at the end (1 reading)), J",note
  "Занять память, МБ, МБ","Полная энергия (в конце (1 замер)), Дж",примечание
  ```

- `evidence/c12_json_roundtrip.out`: `live : Window size, nm` / `disk : Window size, nm, nm`; `str(after JSON): {'$t': 'Window size, nm'}`.

**Fix.**
- Never `str()` a text. Use `lfphys.i18n.english(x)` (or `render`), which handles both live `T` and decoded dicts, in `has_unit`, `_setting`, `display_label` and `owner_text`.
- Rebuild `T` on load in `protocol.decode` and in the sweep spec reader (`T(d)` for every `is_t(d)`), so that `str()` is English again.
- Add a lint test: no `str(` applied to a name that holds a label, unit, text or note in `server/lfviz`.

### F3 — should-fix — the player rounds integers without a format to 6 significant digits (and to m·10ⁿ from 10⁷)

**Location.** `visualizations/player/js/i18n.js:121` (`arg` → `fmt(v, "")`) and `:169-189` (`fmt`: the default is `g` with 6 digits).

**What happens.**
- A placeholder without a format (`{n}`, `{e}`, `{total}`) formats an integer like a float.
- Python's `_fmt` keeps integers exact (`str(v)`).
- So a count over 999 999 is wrong on screen, and the CSV and the screen disagree.

1866 placeholders have no format. Among them:
- p03's cost note `T("{n} atoms, {e} events")`. The hard-sphere event count passes 10⁷ in a long run.
- `{n} coordinates`, `{n} samples`, `{n} readings`.

The framework already works around this for seeds by hand (`catalog.js:278`, `player.js:391`: `String(seed)`), a sign that the default is wrong.

**Evidence.** `evidence/c19_js_specifics.out`:

```
en p03 cost note, 12 345 678 events: 400 atoms, 1.23457·10⁷ events
en {n} with n = 1234567: 1,234,570 coordinates
ru p03 cost note: атомов: 400, событий: 1,23457·10⁷
```

`c01`: `"big int default"` Python `12345678`, JS `1.23457·10⁷`.

**Fix.**
- In `fmt` with an empty spec, render `Number.isInteger(x) && Math.abs(x) < 2**53` as an integer with the language's grouping: `local(x, {maximumFractionDigits: 0})`.
- Add a case to `i18n.test.mjs`.

### F4 — should-fix — plain-English engine messages still reach the owner; the «programming errors» claim does not hold for optics

**Location.**
- `visualizations/server/lfviz/errors.py:141-149`: a plain `ValueError` becomes the owner's text as it is. Only eight library sentences are recognised (`KNOWN`).
- `lfphys/lfphys/core/**`: 458 raises with a plain string (`evidence/c03_plain_raises.out`).
- `v05_optics_bench/viz.py:876-888`.
- `v17_mie_scattering/viz.py:153`.
- `lfphys/lfphys/core/optics/{thin_films,mie,beams}.py`.

**What happens.**
- Any plain-string `ValueError` that a world does not wrap reaches a Russian viewer in English, capitalised by `{body:cap}`.
- The engine agent kept the optics messages untranslated on the claim that they report programming errors. For several of them the claim does not hold:
  - **`thin_films.airy`'s three ValueErrors** (`:194, :199, :213`). They are runtime conditions of the owner's set-up: total reflection, grazing incidence, absorbing indices. v05 catches them on purpose (`viz.py:556-565`) and recognises them by English substrings (`"total reflection" in s`, `"grazes"`, `"real positive"`). Anything else falls into `T("the engine's reason: {err}", err=s)`: an English sentence inside the Russian text.
  - **`mie.coefficient_bound`** («no tested bound above x = 2e4», `:104`) and **`mie._D_start`** («|m x| = … too large», `:201`). Both depend on the drop radius, the index and λ. Only v17's own pre-check prevents them, and it copies the engine's constant: `v17/viz.py:153`, `> 2e4`. If either constant changes, the English message leaks.
  - **`VortexBeam._guard`** (`beams.py:299-303`, «… elements (~… GB) > max_elements …: fewer points, a smaller region or a larger budget»). A resource limit that depends on the owner's region and |l|. v16 pre-empts it with its own budget (`engine/apparatus.py:130-138`), again by duplicating the arithmetic.
- The fuzz (`c14`) found no leak through the parameter forms of v05, v16, v17 and v08 today. The protection is the duplicated thresholds and the substring matching above, so a change to an engine constant or sentence would leak English with no test failing.
- The engine's own `CYR`-based "old Russian text" branches (`errors.py:28, 142, 166`) treat any non-Cyrillic plain text as a library message. A plain English engine message that is not in `KNOWN` is shown as it is.

**Evidence.**
- `c03_plain_raises.out`: the list of plain raises, with the per-directory counts above.
- `c14_fuzz_optics.out`: 160 random parameter sets of v05, v16, v17 and v08 within their schemas, built and stepped; every exception put through `owner_text`. Result: 0 plain-English owner texts in 160 sets (see «Fuzz result» below).
- v05's source is the direct proof that the airy messages reach the owner.

**Fix.**
- Raise the input-dependent optics refusals as `ValueError(T(...))` with a machine-readable code (see F5): the airy trio, the Mie bounds, `VortexBeam._guard`, `thin_films.joule_absorption_s`'s node limit, and `angular_spectrum`'s `z >= 0`.
- Export the thresholds (`mie.X_MAX`, the guard's element count) so that worlds do not copy numbers.
- In `owner_text`, show a plain engine `ValueError` as `T("the engine refused: {what}", …)` with the English sentence moved to `detail`, so that no English prose appears in a Russian toast.
- Add a test that fuzzes each world's schema (as `c14` does) and fails on an owner text that holds a plain English string.

### F5 — should-fix — five worlds recognise engine messages by their English text; most of these mappings have no test

**Location.**
- `p02_quantum/viz.py:368-372` (`_mid`), `:1083-1096` (`_refusal`: two `startswith` prefixes), `:1098-1105`, `:1463-1468`.
- `p04_fluids/viz.py:403-421` (`_LBM_REFUSALS`: five fragments), `:560-591`.
- `p03_molecules/viz.py:2024, 2044` (`"overlap"`, `"non-finite"`, `"outside the walls"` in `str(e)`).
- `v05_optics_bench/viz.py:882-886`.
- `v15_kerr_shadow/viz.py:319-322` (`"photon orbit"`, `"stable"` in `english(text_of(e))`).

**What happens.**
- The worlds put engine refusals into their own terms by matching a fragment of the engine's English msgid.
- The i18n made this somewhat safer: msgids are stable English, not rendered Russian.
- It is still coupled to wording. A reworded engine msgid (the engine agent just rewrote hundreds) silently drops the world's explanation, and the owner gets the engine's generic sentence.
- None of p04's five mapped refusals has a test that checks the world's wording: no test contains «a velocity above what the weakly compressible scheme», «too small for this grid and time step», and so on. Neither do p02's `_refusal` branches.
- `p04._lbm_refusal` takes the numbers from the *outer* text's args when the fragment matched the English rendering instead of the msgid. If the engine ever wraps the message (`T("{what}: …")`), the result is `Mach number nan`.
- The engine already attaches structure that p02 ignores: `scene._refusal(info["text"], what="resolution", pid=…)` (`lfphys/core/quantum/scene.py:1987-1993`), plus `K`, `lim` and `dV` in `_resolution_reason`.

**Evidence.**
- The `grep` of the tests (none hit).
- The code cited above.

**Fix.**
- Give engine refusals a code: `e.code = "lbm.mach"`, `"qscene.resolution"`, `"airy.total_reflection"` and so on (an attribute, or a `Refusal`-like engine class), with the numbers as attributes.
- Match on the code in the worlds.
- Until then, add one test per mapping that triggers the engine condition and asserts the world's msgid. A reword then fails in CI.

### F6 — should-fix — the completeness tests miss three classes of texts and check only placeholder names

**Location.**
- `visualizations/tests/test_i18n.py:101-137` (static), `:173-213` (dynamic).
- `i18n_tools.py:216-255` (`msgids_py`, `msgids_js`), `:323-329` (`placeholders`).
- `lfphys/lfphys/i18n.py:184-197` (`msgids` collects only `T`).

**What happens.** A missing translation slips through when:
1. **The text is a plain string.** The spec allows «a plain msgid string where a schema field is static». The player then calls `t("…")`, but the dynamic test collects only `T` objects (`msgids()`) and the static test only `T("literal")`.
   - `c05`: `msgids({"label": "Plain string label nobody translated", "unit": T("nm")})` → `{'nm'}`.
   - A new world with `Param("w", "Width", …)` passes every test and shows «Width» in Russian.
2. **The msgid is not a literal.** Python examples: `T(MSG)`, `T("a" + b)`, `T(cond and "a" or "b")`; the code base has 18 such calls (`c02`). JS examples: `t(cond ? "a" : "b")`, `t(LABELS[i])`, `t(\`…${x}…\`)`. `c05` shows that `msgids_py` and `msgids_js` return `[]` for all of them. R1's "unused" warning lists `World {n:d} (current): {title}`, which `player.js:589` does use.
3. **The text appears only after an action, a scene operation, a refusal or a long run.** The dynamic test runs only `presets[:2]` × 3 steps (`test_i18n.py:183, 194`).
   - `c04` shows that the current state is complete for all presets and the live min/max.
   - The scenes, actions and refusals of the playgrounds are still not exercised.

In addition:
- `test_a_catalogue_is_a_flat_object_of_translations` compares placeholder **names** only (`:80`). A translation `{x:.2f}` for a msgid `{x:.3g}` passes, and the Russian shows another precision. The engine test compares (name, format); the framework test should too. `c16`: no such mismatch exists today.
- The visualizations' msgids are not checked for formats the player cannot render. The engine test has `SPEC` (`test_i18n_engine.py:25`). `c01` shows the JS ignores widths (`{x:8.3f}`) and `,` (`{x:,}` → «1,234,570»).

**Evidence.** `c05_tests_bypass.out`, `c02_nonliteral_T.out`, `c16_spec_mismatch.out`, `t1_baseline_tests.out`.

**Fix.**
- **Plain-string fields.** Make `msgids()` (or a test-only walker) also collect plain strings under the user-facing keys of a schema or message (`label`, `unit`, `help`, `group`, `title`, `note`, `text`, `options[].label`, …), as `c04` does. Alternatively, forbid plain strings there: a schema check that every such field is `T` or a neutral symbol.
- **Non-literal msgids.** Fail the static test on any non-literal `T()`/`t()` argument unless the line carries a marker naming the msgids it can produce.
- **Dynamic run.** Run all presets, and the palette's `add` and each action with defaults.
- **Formats.** Compare (name, format) in the framework test, and apply the engine's `SPEC` check to all msgids.

### F7 — should-fix — `?lang=` holds for one page only

**Location.** `visualizations/player/js/i18n.js:39-47` (`chosenLang` reads `?lang` but does not store it), `:77-84`.

**What happens.**
- A shared link `/?lang=ru` (or `/run?id=…&lang=ru`) opens in Russian.
- The next click on any internal link loads a page without `?lang`, which falls back to the stored choice or English.
- A Russian reader sent a Russian link lands in English after one click.

The browser test checks only that `?lang` *overrides* a stored choice. It never checks navigation.

**Evidence.** `b01_ru_english_leaks.out`: `{"check":"?lang=ru then another page without ?lang","first":"ru","next":"en"}`.

**Fix.** Either store a valid `?lang` in `localStorage` (as an explicit choice), or carry it on internal links. Storing it is simpler and matches "switching reloads the page". Add the navigation case to `i18n_checks.mjs`.

### F8 — should-fix — the guard tests let shadowed `t`/`T`, escaped Cyrillic and English-in-Russian through

**Location.**
- `i18n_tools.py:297-320` (`shadowed_t`), `:59-76`, `:164-167` (Cyrillic guard).
- `test_i18n_engine.py:136-165` (`_shadowing`).
- `tests/browser/i18n_checks.mjs:103`.

**What happens.**
- **Shadowed `t` (JS).** The regexes miss three forms. In each, a later `t("…")` in that scope calls a local value: the bug the test was written for (`orbitview.js`'s `drawPhase(meta, t)`).
  - a later name in a declaration list without `=`: `let x, t;`
  - a parameter after a default value with a call: `function a2(meta, cb = make(), t)`
  - a method with such defaults: `draw(meta, opts = f(1), t)`
- **Shadowed `T` (Python).**
  - No test covers the visualizations at all. 11 functions there already make `T` a local, as a parameter or by assignment, in modules that import `T`: `p01_gravity/viz.py:243, 252, 2186, 2188`, `p03_molecules/viz.py:448, 458, 1203, 1271, 2015`, `v05_optics_bench/viz.py:702`, `v05/engine/bench.py:112`. A future `T("…")` in any of them raises `UnboundLocalError`.
  - The engine's own check misses `except … as T`, a nested `def T` and `import … as T`.
- **Cyrillic.**
  - Escaped Cyrillic (`"Ши…"`, `"\N{CYRILLIC …}"` in Python) passes.
  - The opt-out marker `i18n-ok` is honoured anywhere on the line, including inside the string literal itself: `"Ширина i18n-ok"` passes.
- **Browser, Russian.** A Russian page passes as soon as it shows any Cyrillic (`CYR.test(r.text)`). An untranslated English label on a Russian page is never caught. `b01` adds a Latin-prose detector; today it finds no English prose, so a stricter check could be adopted without new failures.

**Evidence.**
- `c05_tests_bypass.out`: `shadowed_t(shadow.js) lines: [8, 9]`. The constructed cases are on lines 3, 4, 7 and 8; line 9 is the control. Escaped Cyrillic and the in-string marker are not reported.
- `c17_T_shadow_viz.out`: the 11 functions, and `engine _shadowing on a snippet with except-as-T, nested def T, import-as-T: []`.

**Fix.**
- **JS.** Replace the regex `shadowed_t` with a real parse. `acorn` is small and could be vendored for the test. Or run the modules under `node --check` with an ESLint `no-shadow` rule restricted to `t`.
- **Python.** Apply the engine's `_shadowing` to the visualizations, and extend it to `ExceptHandler.name`, `FunctionDef.name` and `alias.asname`. Rename the 11 locals (`T_K`, `temp`).
- **Cyrillic guard.** Decode string tokens (`ast.literal_eval`) before the check, and accept `i18n-ok` only inside a comment token.
- **Browser.** In Russian, fail on visible lines with two or more English words outside a short allow-list.

### F9 — should-fix — the catalogue exists only behind the server: the public site cannot be Russian, and every page waits for 1.3 MB

**Location.**
- `player/js/i18n.js:58-71` (the catalogue only from `GET /api/i18n/<lang>`; on failure, silently English), `:238` (top-level `await init()`).
- `server/lfviz/app.py:419-428`.

**What happens.**
- **The public site.** Rules 13 and 15 require the public site (GitHub Pages, from recordings, no server) to exist in every language. A static copy has no `/api/i18n`, so it is always English, with the switch still offered. The code comment accepts this («no server (a static copy): the English source texts»).
- **First load.** The Russian catalogue is 1 338 263 bytes of JSON, served without compression. Every page's modules wait for it (top-level await) before anything renders. Revalidation (304) makes repeat loads cheap. The first load on a slow link, and every load of the static site if it gets the same design, are not cheap.
- **No failure signal.** A failed fetch silently shows English with the RU switch marked on. The viewer cannot tell that the translation failed.

**Evidence.** `c07_http.out`: `Content-Length: 1338263`, no `Content-Encoding` with `Accept-Encoding: gzip`.

**Fix.**
- Generate the merged catalogues as static files (`player/locales/<lang>.json`, built by the same merge as `catalogue()`, checked by a test that they are current). Load them by a relative URL; the endpoint can serve the same bytes.
- Compress: `web.Response(..., zlib_executor_size=…)` / `enable_compression()`, or a pre-gzipped static file.
- Mark the switch when the catalogue could not be loaded.

### F10 — nit — the two renderers still disagree at the edges; Python's Russian plural crashes on NaN/∞

**Location.**
- `lfphys/lfphys/i18n.py:70-92` (`_fmt`), `:105-120` (`plural_category`), `:129-130`.
- `player/js/i18n.js:84-95` (`lookup`), `:110-124`.

**What happens.** All from `evidence/c01_parity_{py,js}.out`. Python is used for logs, the API's English `text` and the CSV files; JS for the screen.

| case | Python | JS |
|---|---|---|
| `True` | `True` | `true` |
| float 2.6 with `{n:d}` | `2.6` | `3` |
| plural msgid without `n` (ru) | `many` | `other` |
| plural n = −1 (en) | `other` | `one` |
| plural n = 1.0004 with `.3g` (en) | `other` | `one` (Intl rounds to 3 decimals) |
| NaN, ∞ | `nan`, `inf` | `—`, `∞` |
| `{x:8.3f}`, `{x:,}`, `{x:.1%}` | honoured | width dropped, `,` ignored, `12.3 %` |
| `np.float32` with `.2f` | spec ignored: `0.123456` | (cannot arrive: `protocol.clean`) |
| `{constructor}` absent from args | `{constructor}` | `function Object() { [native code] }` (`name in args` sees the prototype) |
| ru plural with n = NaN / ∞ | **`ValueError` / `OverflowError`** (`int(x)` outside the `try`) | `— дня`, `∞ дня` |

Python formats a number with a spec through `format(v, spec)`, so a Russian CSV header has a decimal point and `1e-05`. The docstring says this is deliberate.

**Fix.**
- Make `plural_category` total: `math.isfinite` first, and the integer test inside the `try`.
- Use `Object.prototype.hasOwnProperty.call(args, name)` in `render`.
- Format `bool` the same way in both renderers.
- Have the engine test's `SPEC` check also reject the formats the player cannot render (F6).
- Choose the plural form from the number as displayed (see F11).

### F11 — nit — the plural form is chosen from the unrounded value

**Location.** `player/js/i18n.js:89-91` (`lookup` selects on `args.n`); the number is then shown by `{n:d}` or `{n:.3g}`.

**Evidence.** `c19_js_specifics.out`: `ru {n:d} days, n = 4.6: 5 дня` (should be «5 дней») and `n = 21.4: 21 дня` (should be «21 день»). `catalog.js:42` renders the retention period through `{n:d} days`, and `keep_days` is a float on the server (`runs.py:762`, `--keep-days`).

**Fix.** Select the plural form on the value after the placeholder's format (round for `d`, `toPrecision` for `.Ng`), or pass `n` as an integer.

### F12 — nit — English plural forms (`en.json`) are ignored by `str(T)` and by the API's `text`

**Location.** `lfphys/lfphys/i18n.py:56-57` (`__str__` = `render(self, {})`), `visualizations/server/lfviz/i18n.py:130-133` (`error_body`).

**Evidence.** `c18_english_plurals.out`:
- `str(T)` / `error_body text`: «all 1 workers are busy with open runs …».
- `render_in(x, 'en')`: «the only worker is busy with an open run …».

Also: `{n} readings` and `{n} atoms` are bare msgids without plural forms. The sweep CSV says «1 readings» (`c15`).

**Fix.** Render English through `render_in(text, "en")` in `error_body` and the server's logs. Give count msgids `{n:d}` and an `en.json` entry.

### F13 — nit — `/api/i18n`: conditional requests and language codes

**Location.** `visualizations/server/lfviz/app.py:419-428`.

**What happens.**
- `If-None-Match` is compared by string equality. A weak validator (`W/"…"`), a list (`"x", "…"`) or `*` gets a full 200 (`c07`). Browsers send the exact tag, so this costs nothing today; proxies may not.
- `RU` and `ru-RU` give 404. The player never sends them, but an API client might.

**Fix.** Parse `If-None-Match` per RFC 9110 (weak comparison), lower-case the code and take its primary subtag.

### F14 — nit — operations on rendered text that remain in the player and the server

**Location.**
- `player/js/ui.js:150-153`: `pName` uses the substring test `!t(lab).includes(t(u))`. `instruments.js:93-97` already has a token-based `hasUnit`.
- `server/lfviz/playground.py:1018`: `str(p.unit) not in str(lab)`.
- `player/js/player.js:589`: `t(W.header.title).replace(/^[^:]*:\s*/, "")` cuts the rendered title at its first colon, in whatever language.
- Glued phrases with fixed word order and punctuation:
  - `orbitview.js:101`;
  - `ui.js:60` (`${m} ${t("min")} ${…} ${t("s")}`);
  - `scene3d.js:813` (`${t(name)}, ${t(units)}`);
  - `instruments.js:98, 766`;
  - `player.js:354`.

**What happens.**
- A one-letter unit («с», «м», "s", "m") is found inside any word that contains the letter, and is then not shown.
- `c06` checked the 55 parameters that have a unit: none is affected today, in either language. This is latent.
- The title cut depends on where each translation puts its colon.

**Fix.**
- Use the token-based `hasUnit` in `pName` and in `_setting` (via `english()`; see F2).
- Send the short title as a separate field instead of cutting the rendered one.
- Make the glued phrases msgids («{m} min {s} s», «{name}, {unit}»).

### F15 — nit — `{label:unit}` takes "whatever follows the last comma" of the rendered label

**Location.** `lfphys/lfphys/i18n.py:68-74`, `player/js/i18n.js:117-118`, used by `playground.unit_of` (`playground.py:268-280`).

**What happens.**
- The "unit" is the text after the last comma of the label *in the viewer's language*.
- Labels whose comma introduces a phrase yield a phrase. Translations that replace the comma by a dash yield nothing in Russian.
- `c11` checked 139 parameters. 13 give a phrase or a language-dependent result. Examples:
  - v06 `alpha_mz`: «the coupling constant» in English, empty in Russian;
  - v17 `n_re`, `n_im`;
  - v13 `real`: «…) instead of a complex one with e^{imφ}».
- Today `unit_of` reaches only the playgrounds' handle vectors, where none of these occur. Latent.

**Fix.** Give such parameters an explicit `unit` (or `unit=""` with a flag) instead of parsing labels. Have the completeness test require, for a msgid used with `:unit`, that its translation keep a comma-separated unit.

## Fuzz result (`c14`, v05, v16, v17, v08)

The fuzz built and stepped 160 random parameter sets (40 per world, seed 1). Each set took schema bounds and options, with a 40 % weight on the extremes. **It found 0 owner texts with a plain English string** (`evidence/c14_fuzz_optics.out`).

So at the level of parameter forms, the worlds' own pre-checks and text matching keep the optics engine's English sentences away from the owner. That protection is:
- duplicated thresholds (v17's `2e4`, v16's budget arithmetic);
- substring matching (v05).

F4 therefore stands as a robustness defect, not as a leak observed today. The engine agent's claim «programming errors» is still wrong for the airy trio: they are runtime conditions that a world has to catch.

## What was not checked

- The quality and consistency of the Russian wording (a language review).
- The docs pass promised by the commit message (rule 12): READMEs, guides and `RULES.md` «Languages and i18n».
- Fuzzing of the playgrounds' scene operations (add, edit, carry) for plain-English refusals. `c14` covers only schema parameters of four worlds; the md and gravity engines (253 plain raises) were checked only by reading.
- Records made before the commit. None exists in this clone (`visualizations/runs/` holds only `settings.json`). Compatibility was checked by reading:
  - the player and the server pass plain Russian strings through (`t()`, `render_in`, `t_unit_of`, `_is_seconds` with «с»);
  - checkpoints of older code are not used, because the code hash differs (`checkpoint.py`, `runs.py:990`), so a resumed old run is replayed;
  - replayed commands carry ids and values, not texts.

  No defect was found. A run recorded by the shared server, if one exists elsewhere, would be the test.
- GPU paths.

## Clean-up

- Private server `lf-rv18c-srv` (port 8651) stopped by its container name. Its runs (70 MB of records and checkpoints) were not kept in the repository.
- All other containers were `--rm` and named `lf-rv18c-*`.
- No repository file outside this folder was changed, and no git command that changes the repository was run.
- The Playwright `node_modules` copy is in the scratchpad (`rv18c_pw/`), not in the repository.
