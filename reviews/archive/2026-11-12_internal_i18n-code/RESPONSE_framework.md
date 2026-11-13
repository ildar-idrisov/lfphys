# Response to review i18n-code — the framework part

**Responder:** PR-A, the framework-code processing agent (prefix `lf-pa-`). It wrote neither the review nor the code
under review. **Date:** 2026-11-13.

**Scope.** Every finding of this review that falls in the framework's files: `visualizations/server/**`,
`visualizations/player/**`, `visualizations/tests/**` (the worlds' own tests aside), the test worlds p97 and p99, and
`lfphys/lfphys/i18n.py`. The engine's side of F4 and F5 is answered by PR-B (`RESPONSE_engine.md`), the worlds' side of
F5 and the shadowing locals in world code by PR-C1/PR-C2, the msgids and the catalogue entries (F12's count msgids) by
PR-D. The browser review's findings in the same files are answered in
`../2026-11-12_internal_i18n-browser/RESPONSE_framework.md`.

**Counts (this file):** 15 findings — 11 fixed in the framework part, 4 partly (F4, F5, F12, F14: the rest is another
agent's or kept on purpose, see each), 0 rejected.

**Environment.** Image `lfphys-viz`, CPU only (`LFPHYS_NO_GPU=1`), containers `lf-pa-*` with `--memory` ≤ 8g, the
repository mounted read-only. JS unit tests in `node:24`. Browser checks: Playwright 1.58.2 Chromium
(`mcr.microsoft.com/playwright:v1.58.2-jammy`) against the private server `lf-pa-srv` on port 8671 (3 workers,
`LFVIZ_EXTRA` = both fixture folders). The shared server on 8479 was not touched.

## Findings

### F1 — error — `display_label` names the object twice

**Status:** fixed [error in earlier].

- `lfphys.i18n.mentions(outer, inner)`: whether a text is the other or one of its arguments at any depth, compared by
  msgid and arguments (`same_text`), for live `T` and for decoded dicts alike. `instruments.display_label` adds the
  object's name only when the quantity does not mention it.
- Test `test_texts_are_compared_by_msgid_and_arguments_also_after_json`: the p99 probe quantity's CSV header is
  `“Probe 1”: to the nearest particle, m [near.o1]` (the name once), live and after a JSON round trip; a quantity that
  does not name its object still gets the prefix.

### F2 — error — decoded texts are dicts; `str()` of them is a repr

**Status:** fixed [error in earlier].

- **Never `str()`, compare structurally.** `lfviz.i18n.names_unit(label, unit)` (moved there from `sweep.has_unit`):
  the unit is one of the label's arguments, or the English msgid of the label or of one of its parts names the unit's
  msgid. Used by `sweep.with_unit` (sweep CSV), `playground._setting` (the scene's log) and `params` (a refusal's field
  name, which had the same `str(unit) not in str(lab)`).
- **Texts back as `T` on load.** `lfphys.i18n.json_hook` / `revive`; `protocol.decode` and `peek_meta`, the record's
  JSON reader of the instruments (`read_json`), the run's `meta.json`, and every sweep spec reader load with it, so
  `str()` is the English rendering again.
- `errors.owner_text` matches library sentences on the English rendering of the exception's text (`_english`), never
  on `str()` of a decoded text.
- **Lint test** `test_the_server_never_turns_a_text_into_a_string_by_str`: a `str()` of a name holding a label, unit,
  text, note, title or hint in `server/lfviz` must sit on a line that checks `is_t` first, or carry `i18n-str-ok` (two
  such lines: a label the owner typed, and `render_in`'s plain-string branch).
- Regression in the same test: `with_unit` of `Hold memory, MB` / `MB` after JSON, and of `{label} ({stat})` around it
  (the sweep CSV's shape), returns the label unchanged.

### F3 — should-fix — integers rounded to 6 digits in the player

**Status:** fixed [error in earlier].

`fmt(x, "")` shows a whole number below 2⁵³ exactly with the language's grouping (`12,345,678`, `12 345 678`); a
non-integer keeps 6 significant digits. Python's `_local` (the files' renderer, below) does the same.
`i18n.test.mjs`: `{n} atoms, {e} events` with 12 345 678 events.

### F4 — should-fix — plain-English engine messages reach the owner

**Status:** partly — the framework's part fixed; the engine's messages and codes are PR-B's.

`errors.owner_text`: a plain (untranslated) English `ValueError` that matches no known library sentence is no longer
shown in English: the owner reads `the computation refused this; its own reason (in English) is under “details”`
(«расчёт отказался это выполнить; его собственная причина (на английском) — в «подробностях»») and the sentence goes
to the detail. A plain Russian text (a record from before the translation) is shown as before. A coded engine exception
(`lfphys.codes`, PR-B) is recognised by its code where the framework words it itself (`BY_CODE`: `gr.not_timelike`,
which replaced the English regex). Tests `test_a_plain_english_refusal_is_not_shown_in_english`,
`test_an_engine_refusal_is_recognised_by_its_code`. The fuzz of every world's schema that the review proposes is not
added: the dynamic test now runs every preset, action and palette type (F6), and PR-B made the engine's
user-reachable messages texts with codes.

### F5 — should-fix — worlds match engine messages by English text

**Status:** not in the framework's files — PR-B (codes) and PR-C1/C2 (worlds). The framework's own matching
(`errors.KNOWN`) now uses the engine's code where one exists (F4).

### F6 — should-fix — the completeness tests miss three classes of texts and check only names

**Status:** fixed.

- **Plain-string fields.** The dynamic test also collects plain strings under the user-facing keys (`label`, `unit`,
  `help`, `group`, `title`, `summary`, `purpose`, `note`, `text`, `hint`, `statement`, `validity`, `reason`, `what`,
  `button`, `mode_label`, …) that contain a word of prose (three lower-case letters), and requires their translation.
- **Non-literal msgids.** `msgids_py` reads a module constant and a choice between literals (`T(MSG)`,
  `T("a" if c else "b")`), `msgids_js` reads `t(c ? "a" : "b")` (also nested). A msgid built at run time
  (`"a" + b`, a template with `${}`, a `.join`) must carry a comment `i18n-msgids: "…" "…"` that names its msgids,
  which the static test then checks (`composed_py`, `composed_js`; test
  `test_a_msgid_built_at_run_time_names_its_msgids`). The five such calls of the framework carry it now
  (`errors._size`, `limits.fmt_bytes`, `sweep` time units, two placeholder-only joins in `playground`, `join`).
- **Dynamic run.** Every preset of every world is built and stepped (the first two 3 steps, the others 1); on the first
  preset each declared action runs with its default arguments and each palette type is placed.
- **Formats.** A translation keeps each placeholder's format (`placeholder_specs`; a plural form too), and every
  format of a msgid, a translation or a code literal is one the player renders (`bad_specs`: nothing, `.Ng`, `.Nf`,
  `.Ne`, `g`, `d`, each with `+`; `cap`, `unit`). Braces of a text such as `{kind: law, id}` are not placeholders.

### F7 — should-fix — `?lang=` holds for one page only

**Status:** fixed. A valid `?lang=` (also `RU`, `ru-RU`) is kept for the tab in `sessionStorage`; the pages reached
from it stay in that language; a link opened in a new tab (no shared `sessionStorage`) gets `?lang=` added when it is
pressed (pointer, keyboard, context menu); `catalog.js`'s navigation by code uses `withLang()`. The stored choice is not
changed; the switch EN | RU ends the link's language. Browser checks in `i18n_checks.mjs` (section 1b): catalogue →
settings, run → catalogue, and the switch; the ad-hoc check of a new tab is in the browser response.

### F8 — should-fix — the guard tests let shadowing, escapes and English-in-Russian through

**Status:** fixed (the guards; the renames in world code were done by PR-C1 and PR-C2).

- **JS.** `shadowed_t` rewritten without the regex over parameter lists: string contents blanked, every bracketed list
  followed by `=>` or `{` split at its top-level commas (defaults with calls, destructuring, rest), declarations split
  the same way (a later name without `=`, `for (const { t } of …)`), `function t`, `catch (t)`. All the review's
  constructed cases are caught (`test_the_guards_catch_shadowing_escapes_and_markers_in_strings`). No module of the
  player is hit.
- **Python.** `shadowed_T`: a function that binds `T` in its own scope — a parameter, an assignment, a loop target,
  `except … as T`, `def T`, `class T`, `import … as T` — in a module that imports `T`; test
  `test_no_function_of_the_visualizations_makes_T_a_local` over the visualizations (not their tests). It first failed on
  `p01_gravity/viz.py` (4 functions), `p03_molecules/viz.py` (5) and v05 (2), reported to the integrator at the start;
  PR-C1 and PR-C2 renamed them, and it passes now.
- **Cyrillic guard.** Python string tokens are decoded (`\uXXXX`, `\N{…}`); JS lines with an escaped Cyrillic letter are
  caught; the marker `i18n-ok` counts only in a comment. Three framework lines that hold an escaped «с» or a Cyrillic
  range now say why in a comment.
- **Browser, Russian.** `i18n_checks.mjs` fails a Russian page (the licence page aside, whose texts are labelled
  English) on a visible line with two or more English words outside the review's allow-list of names, symbols and
  key names (identifiers such as `v01_light_travel` are not prose).

### F9 — should-fix — the catalogue only behind the server, 1.3 MB uncompressed

**Status:** fixed.

- The player loads `../locales/<lang>.json` relative to its own module. The server answers there
  (`/static/locales/<lang>.json`, registered before `/static/`) with the same body as `/api/i18n/<lang>`; a static copy
  of the player (the public site) carries the files written by `python -m lfviz.i18n --export DIR` (`<lang>.json` and
  `<lang>.json.gz`, the exact bytes the server sends). There is no site build in the repository yet; its build is to
  call the export.
- Gzip: the gzipped body is made once per catalogue version (447 kB instead of 1.34 MB for Russian), sent with
  `Content-Encoding: gzip` when the client takes it, with its own ETag and `Vary: Accept-Encoding`.
- A catalogue that cannot be loaded leaves the English texts and marks the switch (⚠, the tooltip says the translation
  could not be loaded).
- Tests: `test_the_catalogue_is_compressed_cached_and_served_where_a_static_copy_has_it`,
  `test_the_engines_english_catalogue_is_merged_and_exported` (PR-B's new engine `en.json` is merged and exported).

### F10 — nit — the renderers disagree at the edges; Python crashes on NaN/∞ plurals

**Status:** fixed (all rows of the table but the ones kept on purpose).

- `plural_category` is total (non-finite, non-numeric, a bool, a missing `n` → "other", as the player); English −1 is
  "one" as `Intl.PluralRules`.
- `{n:d}` of a float rounds in Python too; a bool is `true` / `false` in both; NaN and ∞ are `—` and `∞` in both.
- JS `render` uses `hasOwnProperty` (`{constructor}` stays a placeholder).
- Formats the player cannot render (`{x:8.3f}`, `{x:,}`, `{x:.1%}`) are refused by the test (F6).
- Kept: Python's English rendering (logs, tests, the API's `text`) keeps Python's number format (`1e-05`,
  hyphen-minus); a file for the owner in another language gets the player's format (`render(..., numbers=True)` through
  `render_in`: `1,23·10⁻⁵`, `−15 000`).
- Tests: `test_the_renderers_agree_at_the_edges`, `i18n.test.mjs` (F3, F10, F11 cases).

### F11 — nit — the plural form chosen from the unrounded value

**Status:** fixed in both renderers: the form follows `n` as its placeholder shows it (`{n:d}` of 4.6 → «5 дней»,
21.4 → «21 день»; `{n:.3g}` of 1.0004 → "1 year"; `{n:.2f}` → decimals shown → "other").

### F12 — nit — `en.json` plural forms ignored by `str(T)` and the API

**Status:** partly. `error_body`'s English `text` is rendered through `render_in(text, "en")` with the English
catalogue (test `test_errors_for_api_clients_use_the_english_plural_forms`). `str(T)` stays the plain English
rendering (the engine has no access to the merged catalogue; logs and tests rely on it). The count msgids (`{n}
readings`, `{n} atoms`) are PR-D's and PR-C2's.

### F13 — nit — `/api/i18n`: conditional requests and language codes

**Status:** fixed. `If-None-Match` by the weak comparison (a list, `W/`, `*`); the code lower-cased, its primary
subtag taken (`RU`, `ru-RU` → `ru`). Tested in the endpoint test above.

### F14 — nit — operations on rendered text in the player and the server

**Status:** partly.

- `ui.js` `pName` uses a token-based `labelHasUnit` (shared with `instruments.hasUnit`); `playground._setting` and
  `params` use `names_unit` (F2). A one-letter unit is no longer found inside another word (tested).
- The world selector no longer cuts the rendered title at its first colon: it shows `header.short_title` when a world
  sends one, else the whole title (the select has a tooltip and an ellipsis).
- Glued phrases made msgids: `{m:d} min {sec:.2f} s` (`ui.time`), `{name}, {unit}` (3-D axis names), `{label},
  {unit}` and `{label} ({stat})` (instruments), `{label}: {option}` (action buttons' tooltips).
- Kept: `orbitview.js` writes `ħω = … unit` around a translated period (a formula, no word order).

### F15 — nit — `{label:unit}` takes whatever follows the last comma

**Status:** fixed as a guard. The labels the review lists (v06, v13, v17) are not reached by `unit_of` (only the
laboratories' handle vectors are). Test `test_a_unit_taken_from_a_label_survives_the_translation`: for every palette
parameter `unit_of` reaches (no explicit unit, a comma in the msgid), the translation keeps a unit after its last comma
(none fails today).

## Also done in the framework files (integrator's requests of 2026-11-13)

- **Language review R09-012, R09-013** (PR-C2's request; the English source is `server/lfviz/orbitals3d.py`): "choose
  two states of two energies at most" → "choose states with at most two distinct energies"; the continuity check's note
  "(growing fourfold with the step) … + round-off" → "(growing fourfold when the step is doubled) … + the round-off
  error". The two keys of `v13_hydrogen_3d/locales/ru.json` renamed with them (their Russian, already PR-C2's: «…с двумя
  различными энергиями», «…при удвоении шага… + погрешность округления»).
- **Engine codes** (PR-B): `errors.py` imports `lfphys.codes.code_of`; the engine's `en.json` is merged and exported
  (above).
- **`test_run_list_follows_the_worlds_approximations`** timed out (120 s for v08's first slice at its defaults) in the
  committed tree `d16e752` and in the current one alike under the host's load (≈10–17; both 182 s, failed): a flake of
  load, not a slowdown. The test now runs v08 with its small grid (`n` 128, `zmax` 10, as `test_i18n`'s SMALL): 51 s on
  the loaded host.
- New framework msgids (their Russian added to `locales/ru.json` one line each, PR-D informed): the ambiguous-number
  refusal (two), `{m:d} min {sec:.2f} s`, the record window's and the retention period's ranges, the catalogue-load
  failure, the old-record note, the plain-English refusal.

## Tests

Docker, CPU, `--memory` ≤ 8g, 2026-11-13; the host was loaded by the other agents (load 10–17 for most of the runs).

| run | result | status |
|---|---|---|
| Full `visualizations` pytest, 1 065 tests in three shards (`tests/`; v01–v09; v10–v17 + p01–p04) | `tests/`: 215 passed, 25 failed — 23 the new dynamic test with its first plain-string rule (ids such as "step", "strip" taken for prose; the rule fixed), 1 a conflict of the v09 and v10 catalogues (PR-C, resolved since), 1 the approximations timeout above (fixed). v01–v09: 403 passed, 1 skipped, 1 failed: `v08…test_a_refused_window_says_what_to_change_with_a_working_example` expects «the preset «…»», the msgid now says "the “…” preset" (v08's test, PR-C1/PR-D). v10–v17 + p01–p04: 417 passed, 3 skipped | [useful] |
| `tests/test_i18n.py` + `tests/test_server.py` after the fixes | 116 passed (87 + 29) | [useful] |
| `test_i18n.py` and v13 after R09-012/013 (`-k` catalogue, msgid, conflict, v13) | 80 passed | [useful] |
| `node --test player/js/tests/*.test.mjs` (`node:24`) | 6 passed (3 new: F3/F10/F11, number fields, old records) | [useful] |
| Browser checks: see `../2026-11-12_internal_i18n-browser/RESPONSE_framework.md` | i18n_checks, instruments_checks, keyframes, manipulation in EN and RU | [useful] |

## Open points for the integrator

- PR-C1: `v05_optics_bench/viz.py:161, 214` put the exception's English text into the owner's text
  (`T("internal error of the world: {err}", err=…)`); the Russian browser check flags it (a v05 run that failed to build
  with `NameError: name 'lossless' is not defined` during PR-C1's edit). Use `errors.owner_text` or keep the text in
  `detail`.
- PR-C1: v02's phase-window fields (`web/view.js:40-41`) are still `type: "number"`: use `numberInput`.
- A worlds' header may send `short_title` for the world selector (F14); none does yet.
- The public site's build (not in the repository yet) is to copy `player/` and run `python -m lfviz.i18n --export
  <copy>/locales`.
