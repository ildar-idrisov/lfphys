# Response to review i18n-browser: worlds v01–v09 (PR-C1)

Processed 2026-11-13 by the worlds-1 agent of the integration (not the review's author). The part covers the nits that
live in the code or catalogues of `visualizations/v01_light_travel … v09_thomas_3d`; the player, the catalogue page,
the number fields' control and the records are PR-A's (`RESPONSE_framework.md`), the framework texts PR-D's.

| # | finding (v01–v09 part) | decision | verification |
|---|---|---|---|
| F1 / F2 | number fields drop a decimal comma (`type=number`) | the world's own fields: v02's phase window (φ₀, width; `web/view.js`) now uses the framework's `numberInput` and `parseNum` (comma or point; a non-number refused, the field reset to the value in use). No other `type: "number"` in v01–v09; the set-up and action fields are the framework's `control()` (PR-A) | browser checks below |
| F6 | v09 «1,4794 / 1,2379 лет» | fixed: the year read-outs use the framework's plural "{x} yr" with the form chosen on the number as shown (5 significant digits): «1,4794 года»; the two v09 msgids without plural forms were replaced by "{T} by the clocks at rest, {tau} by the craft's clock" (`web/view.js` `years()`) | browser checks below |
| F7 | «а. е.» and «а.е.» (v01, v04) | fixed: one unit msgid, the framework's "au" «а. е.»: v04's own "AU" removed (Mercury check and preset note); v01's label "Distance to the Earth, au" / «Расстояние до Земли, а. е.» | grep: no «а.е.» in v01–v09 |
| F8 | v07 x ticks `-90°` with a hyphen-minus | fixed: `fmt(d, "d")` (the minus sign U+2212, both languages; `v07_bell_test/web/view.js`) | browser checks below |
| F9 | decimal points in Russian prose | v01 «(r ≤ 1,5 rs)» fixed. v09 «4.23» not changed: it is the equation number (4.23) of Osserman 1978, an identifier. v06 «μ ≳ 1.5 ГэВ» is the engine's ABOUT note, not a v06 text (PR-B) | — |
| F10 | v05 legend under the photon bars cut in Russian | fixed: the legend is word-wrapped to the box width and the bar rows leave room for its lines (`v05_optics_bench/web/view.js` `drawCounters`); the counts beside the bars are formatted by `fmt(…, "d")` (digit grouping in Russian) | browser checks below |
| F13 | v06's energy axis ends in «10 Т» / «10 Te» | fixed: the axis labels are centred on their ticks and kept inside the canvas (the last label was drawn from 10 px left of the right edge and cut) | browser checks below |
| F3, F4, F5, F11, F12, F14, F15 and the rest of F13 | player, catalogue, records, framework and engine texts, p01/p02 | not in this part | — |

## Tests (2026-11-13, Docker `lfphys-viz`, CPU, `--memory=7g`; private server on port 8674)

- The worlds' own tests: v01–v07 and v09, **392 passed**; v08, **24 passed, 1 skipped** (the GPU test). The new tests of the code review's F5 mappings (v01 3, v05 7, v06 2) are among them.
- `tests/test_checkpoint.py` and `tests/test_restore.py` with `-k` for v01–v09: **all passed** (27).
- `tests/test_i18n.py`: **87 passed**. The first run reported one conflict, "View along the x axis" («Вид» in v09,
  «Взгляд» in v10); PR-C2 aligned v10 and the rerun passed.
- Browser (Playwright 1.58.2 Chromium): `i18n_checks.mjs` for v01–v09 in EN and RU, **62 checks, all passed**;
  `keyframes.mjs` for v01–v09, **all equal** in EN and in RU.
