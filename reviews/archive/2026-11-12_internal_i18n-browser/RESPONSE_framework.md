# Response to review i18n-browser — the framework part

**Responder:** PR-A, the framework-code processing agent (prefix `lf-pa-`). It wrote neither the review nor the code
under review. **Date:** 2026-11-13.

**Scope.** F1–F4 and the player's nits (F8 in `imagewin.js`, F11, F12, F13, F14). F5 (the name of the laboratories),
F6, F7, F9 and F15 are catalogue and msgid work (PR-D for the framework, PR-C1/C2 for the worlds), F10 and the v07 and
v06 parts of F8 and F13 are world code (PR-C1/C2). The code review's findings in the same files are answered in
`../2026-11-12_internal_i18n-code/RESPONSE_framework.md`.

**Counts (this file):** 9 findings in the framework part — 7 fixed, 2 partly (F3: labels of old records translate,
their sentences with numbers stay as recorded; F13: the badges and the 3-D axis name, v06's axis is world code), F14
kept on purpose.

**Environment.** As in the code response: `lfphys-viz`, CPU only, private server `lf-pa-srv` on port 8671, Playwright
1.58.2 Chromium. For F3, three old records were copied into the private server's runs folder (2026-11-11 p01 and p03,
2026-10-28 v10; from earlier reviews' scratch folders).

## Findings

### F1 — error — a decimal comma typed into a number field is dropped (650,5 → 6505)

**Status:** fixed [error in earlier] (also `RULES.md` §7, which prescribed `type=number`).

- Every number field of the framework is `ui.js numberInput()`: a text field with `inputmode="decimal"` (the number
  keyboard on a phone), never `type=number`: the forms' controls (`control`, `paramForm`: the set-up, «New world», the
  catalogue's forms, the inspector, the placement form, the actions' arguments), the throw scale and the record's window
  (`playground.js`), the slice planes (`env3d.js`), the retention period (`catalog.js`), and the sweep form
  (`instruments.js`, which already used text fields but showed `0,5` with a comma also in English).
- `i18n.js parseNum()` reads a decimal comma or point; thousands as spaces (also the narrow spaces the read-outs use),
  or commas / points in groups of three (`1,234,567`, `1.234,5`, `1,234.5`); the minus signs `-` and `−`; exponents
  `1e-5`, `1,5·10⁻⁵`, `1.5×10^-5`. An ambiguous text is refused with both readings: in English a single comma before
  exactly three digits (`1,500`: "the comma may separate thousands or decimals — type 1500 or 1.500"); in Russian a
  comma is always decimal. `checkNumber` gives the refusal in the field's words as before.
- ArrowUp / ArrowDown step a field where a step was given (the slice planes, the retention period, the record's
  window), as the spinner did.
- Regression: `i18n_checks.mjs` types `<n>,5` into v02's live wavelength field in each language and expects the field to
  show the value applied (`<n>,5` in Russian, `<n>.5` in English) with no refusal, and the field to be
  `type=text`/`inputmode=decimal`. Unit tests in `i18n.test.mjs` (both languages, round trips of `fmtField` →
  `parseNum`).
- Not done: v02's own phase-window fields (`v02_double_slit/web/view.js:40-41`) are world code; PR-C1 was told to use
  `numberInput`.

### F2 — should-fix — the number fields keep the English format in Russian

**Status:** fixed. `fmtField()` shows a field's number in the viewer's format: the decimal comma and `−`, 7 significant
digits, m·10ⁿ as the read-outs; thousands grouped in Russian (narrow spaces) and not in English (where a comma would be
read as a decimal comma). Ad-hoc check at 1280 and 1600 px in Russian, v02: every field (`632,8`, `50 000`, `473,6`,
`1 000`, …) without a decimal point or a hyphen-minus.

### F3 — should-fix — records written before the commit are not translated

**Status:** partly — the labels are translated, the sentences with numbers stay as recorded, and the page says so.

- `player/legacy/ru-2026-11-12.json`: the Russian strings of that time → their msgids, from the Russian catalogues of
  the translation's commit `d9da7cb` (4 578 strings; frozen: the records hold these strings whatever the catalogues say
  now, and the language review has since changed many translations). `i18n.js legacy(x)` loads it once, only in a
  language other than Russian and only when the run's passport or the run list holds a plain Cyrillic string; `t()`,
  `el()` and `fill()` then show such a string as its msgid in the language in force.
- The run page of an old record shows a note for 12 s: "Recorded before the interface was translated (12 November
  2026): its sentences with numbers are shown as they were recorded".
- Ad-hoc check, English: the run list shows the old runs' titles in English («Частицы и молекулы» → "Particles and
  molecules", «Плейграунд: частицы и молекулы» → "Playground: particles and molecules", the msgid of that time); on the
  run pages the 3-D view buttons, the palette, the panels' labels are English. What stays Russian: names the owner gave
  objects («На ISCO-близкой орбите»), labels composed with a number or a unit in the old code («Импульс системы Px,
  u·m/s», «Неподвижный на r = 4»), formatted sentences (approximation notes with numbers, events) and v10's composed
  scene title: 10, 44 and 5 Cyrillic lines in the three records (p03, p01, v10), down from 40+ per page.
- In Russian, the sentences that Python formatted before the commit keep `.` and `-`; they are not rewritten (a record
  is not edited).

### F4 — should-fix — `?lang=` does not survive a link

**Status:** fixed (as code F7). Checked in `i18n_checks.mjs` 1b (catalogue `?lang=ru` → ⚙ Devices: Russian, the
stored choice untouched; a run `?lang=ru` → ← Catalogue: Russian; the switch ends it) and ad hoc: a `?lang=ru` run page
→ ⚙ (opens in a new tab): `/settings?lang=ru`, Russian.

### F8 — nit — hyphen-minus in canvas tick labels

**Status:** fixed in `player/js/imagewin.js` (the sky window's angular ticks through `num()`: `−180°`). v07's plot is
world code (PR-C1).

### F11 — nit — numbers and units break across lines in the run list

**Status:** fixed. `ui.js` `time()` and `length()` put a no-break space between a number and its unit, `{m:d} min
{sec:.2f} s` is one msgid (its Russian with no-break spaces), and the run list's time and size cells do not wrap.

### F12 — nit — the run list's «Scenario» column shows raw preset ids

**Status:** fixed. The column shows the preset's label from the world's catalogue entry (`t(p.label)`); an id the
world no longer has is shown as it is.

### F13 — nit — Russian unit labels clipped by narrow canvases and the top bar

**Status:** partly (the framework's part fixed).

- Top bar (also the integrator's request of 2026-11-13 after the longer «МОДИФИЦИРОВАННАЯ ФИЗИКА: …»): the physics
  badges keep their width (`flex: none`; each is still capped by its own max-width with an ellipsis and its full text
  in the tooltip), the scene and then the title shrink first, with an ellipsis and the full text in a tooltip
  (`#title`, `#scene` get `title`). The badge's label and its value keep the `" "` PR-D put between them. Ad-hoc check
  in Russian at 1280 and 1600 px (v02 with a modified Born rule): the bar does not overflow, «МОДИФИЦИРОВАННАЯ
  ФИЗИКА: Показатель в правиле Борна P ∝ |ψ|^p = …» stands whole up to its own ellipsis, the title is not cut.
- The 3-D view's axis names are kept inside the canvas (`scene3d.js`: a name that would cross the left or right edge
  is anchored inside), and they are one msgid `{name}, {unit}`.
- v06's energy axis («10 Т») is world code (PR-C1).

### F14 — nit — the engine's own exception text is English under «подробности»

**Status:** kept, as the review proposes: the translated head says what the viewer needs, the folded detail is for the
developer. Code F4's fallback now also keeps a plain English sentence out of the head.

## Also asked of PR-A (integrator, 2026-11-13)

- **manipulation.mjs, p99's Shift-throw checks** (PR-C2: EN 82/86, RU 84/86, `rate` null). Not caused by the player's
  changes: (1) `rate` was always null — the check read `Number("2 s / s")`, in the committed version too; it is only
  printed in the report, and now it parses the leading number (`rate: 2`); (2) the throw checks measure the pointer's
  speed over the last 0.1 s of wall time, so they fail when the host is loaded: on the committed tree `d16e752`, served
  by a private server under the same load, p99 at 1600 px failed the same two throw checks (2 of 24). At load ≈1 the
  current tree passes everything: EN 86/86, RU 86/86 (all five laboratories, 1600×1000 and 1280×800).
- **Top bar** (PR-D's request): see F13.
- PR-C2 changed the framework's "ly" to «св. г.»; `locales/ru.json` was re-read before every later edit (PR-A only
  inserts its own new lines).

## Tests

Docker, CPU, private server `lf-pa-srv` on 8671, Playwright 1.58.2 Chromium, 2026-11-13; most runs on a host loaded by
the other agents (load 10–17).

| run | result | status |
|---|---|---|
| `i18n_checks.mjs` EN+RU, every page and all 23 worlds | first run: 113 passed, 5 failed — the comma check picked v02's `lam_nm` range (10⁻⁶–10⁹; the typed value was applied, 3.7·10⁸, but shown in m·10ⁿ: the check now types the review's 650,5) and three Russian lines the new English-prose detector took for prose (module paths, `arctg`, a citation; the detector now skips identifiers, names and mathematical functions); rerun of v02, v04, v05, v15: 42 passed. Full rerun: 116 passed, 2 failed — the Russian run list held a v05 run that had failed to build during PR-C1's edit, whose owner text carries an English exception (v05's `viz.py:161`: world code). Final rerun on a clean runs folder (load ≈1): **all 118 passed** | [useful] |
| `instruments_checks.mjs` EN / RU | 24/24 and 24/24 | [useful] |
| `keyframes.mjs` EN / RU (all 23 runs) | RU all equal; EN all equal but v05 (a timeout while PR-C1's v05 did not build); v05 again in EN: equal | [useful] |
| `manipulation.mjs` EN / RU (5 laboratories, 2 sizes) | at load 10–15: only p99's throw checks failed (3–5 of 86), as the committed tree under the same load; at load ≈1: 86/86 and 86/86 | [useful] |
| ad hoc (`pra_extra.mjs`, scratch): old records in EN; the top bar in RU at 1280 and 1600 px; number fields in RU; a `?lang=ru` link opened in a new tab | as written under F2, F3, F4, F13; the run-list check of old records fails by design of the data (v10's composed scene title is not a catalogue string) | [useful] / [neutral] |
