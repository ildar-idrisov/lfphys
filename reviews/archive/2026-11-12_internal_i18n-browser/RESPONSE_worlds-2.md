# Response (worlds-2 part) to the review i18n-browser, 2026-11-12

**Responder:** PR-C2, the agent processing worlds v10–v17 and p01–p04 (container prefix `lf-pc2-`). It did not write the
review. **Date:** 2026-11-13.

**Scope.** The findings visible in p01_gravity, p02_quantum, p03_molecules, p04_fluids and v10–v17 whose cause is in the
worlds' own files (`viz.py`, `web/view.js`, `locales/`). The player, catalogue, top bar and number fields are PR-A's
(`RESPONSE_framework.md`). The framework's names are PR-D's (`RESPONSE_framework-language.md`). The engine's texts are
PR-B's.

| Finding | Outcome in these worlds |
|---|---|
| F5 two names for the playground | fixed in p01–p04: titles "Laboratory: …" / «Лаборатория: …», summaries "A … laboratory" / «Лаборатория …», the view.js headings and the READMEs. No «Плейграунд»/«Песочница» is left in these worlds' texts |
| F6 year forms | p01 fixed (below). No year read-out exists in v10–v17. v09 is PR-C1's |
| F7 «а. е.» | already right in p01 («а. е.» through the framework's `au`). These worlds write no other spelling |
| F8 hyphen-minus in tick labels | v16 fixed: a raw `${b.l}` number became `t("{l:d}, {kind}")`, formatted by `fmt`. The other views' ticks already go through `fmt()`/`num()` (v17's integer 130…180° ticks are always positive) |
| F9 hand-written decimal points | none left in these catalogues. Checked by regex; p03's and v10's Latin «K» was also replaced by «К» |
| F12 raw preset ids, F13 clipping, F1–F4, F10, F11 | not in these worlds' files (PR-A) |
| F14 engine English under «подробности» | p02's engine text is PR-B's (now a translated T with a code). Two world-side cases fixed: p03's Verlet failure no longer puts the engine's English reason into the Russian sentence, and p02's/p04's refusals are now chosen by the engine's code (code review F5) |
| F15 case after a preposition | fixed in p01 and p02 (below) |

## F6 — p01 «1,00002 годы»
**Fixed.** The period read-out no longer puts a unit after the number, where Russian would need «года»/«лет» chosen by a
fractional value. The unit is in the label instead, in the nominative: "“{label}”: period (two-body problem), years" /
«…, годы». The number stands alone and is formatted by the player. The msgid "years", used as a unit after the number,
is removed.

## F15 — «к «Солнце»», «поглотил из «Электрон»»
**Fixed.** The quoted name now follows a noun, so it stays in the nominative:
- p01: «точка {p} слишком близко к объекту «{label}»», «рядом с точкой {p}», «у тела «{label}»».
- p02: «поглощено из частицы «{particle}»». The row key "absorbed from" is now «поглощено (по частицам)».

Language-review F11 used the same method for every verb or preposition after a label in p01–p04 and v10
(`RESPONSE_worlds-2.md` in the language review folder).

## Tests

All runs are against a private server, `lf-pc2-srv` on port 8675:
- `--memory=8g`, CPU (`LFPHYS_NO_GPU=1`), the repository mounted read-only;
- runs in a scratch folder;
- `LFVIZ_PLAYGROUND_CKPT=6`;
- `LFVIZ_EXTRA` = both fixture folders.

Browser: Playwright 1.58.2 (`mcr.microsoft.com/playwright:v1.58.2-jammy`, `--memory=4g`). The shared server on 8479 was
not touched.

| Check | Worlds | Result |
|---|---|---|
| `i18n_checks.mjs` en,ru | p01–p04, v10–v17 | all passed (72 checks; no Cyrillic in EN; RU pages translated; no page errors) |
| `keyframes.mjs`, `LFVIZ_LANG=en` | p01–p04, v10–v17 | all equal |
| `keyframes.mjs`, `LFVIZ_LANG=ru` | p01–p04, v10–v17 | all equal |
| `manipulation.mjs`, `LFVIZ_LANG=en` | p99_toy, p01–p04 (1600×1000, 1280×800) | 82 of 86 passed. Every p01–p04 check passed (handles, drags, throws, the selection ring, no page errors). The 4 failures are all the toy section's (p99_toy, framework) Shift-throw speed checks at both sizes: the measured speed was 0.2–0.6 of the expected one, and once 0. The test read the playback rate as `null` from `#speedv`, so either PR-A's player changes now landing (number fields, top bar) or the timing on a loaded host. These are PR-A's files |
| `manipulation.mjs`, `LFVIZ_LANG=ru` | the same | 84 of 86 passed; every p01–p04 check passed. The 2 failures are the same p99_toy throw-speed checks, at 1600×1000 only |
| `tests/test_i18n.py` (full) | all catalogues | 86 passed, 1 failed. The failure was a conflict on "View along the x axis" between v09 «Вид…» and v10 «Взгляд…». v10 was set to «Вид вдоль оси x»; after that the static tests gave 64 passed, 0 failed, and every world's dynamic test had already passed in the full run |
| world tests, `-k` framework tests | p01–p04, v10–v17 | see the code review folder's `RESPONSE_worlds-2.md`; all pass |
