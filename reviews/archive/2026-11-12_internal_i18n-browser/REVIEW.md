# Review i18n-browser: the interface in English and Russian, in a real browser

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the code under review) |
| Date | 2026-11-12 (runs finished 2026-11-13) |
| Scope | Commit `d9da7cb` («Interface in English and Russian (i18n)…»): the player's catalogue, settings and legal pages, the help dialogs, every world v01–v17 and p01–p04 in both languages, the language switch (stored choice, `?lang=`, a switch during a recording), records written before the commit replayed in both languages. What a viewer reads: wrong language, raw `$t` / `[object Object]` / `{placeholders}`, untranslated msgids, number formats, truncation and overflow, page errors, consistency of names. |
| Not in scope | The physics; the translations' wording beyond what a reader would trip over; the README and the user guides; the public site. |
| Environment | `lfphys-viz` image, CPU only (`LFPHYS_NO_GPU=1`). Private server `lf-rv18b-srv` on port 8652: `--memory=6g`, 3 workers, the repository mounted read-only, the runs folder in the scratch directory, `--keep-days 60` (so that the copied old records are not removed). Seven records from 2026-10-28 and 2026-11-11 (v01, v02, v04, v07, v10, p01, p03) copied into its runs folder. Browser: Playwright 1.58.2 Chromium (swiftshader) in `mcr.microsoft.com/playwright:v1.58.2-jammy`, `--memory=4g`, through `run_pw.sh`. Viewports 1600×1000 and 1280×800/1000. |

The scripts and their outputs are in this folder:
- `r_lib.mjs`: shared helpers, among them `scan()`, which reads every visible text node, tooltip, placeholder and list option, and flags Cyrillic in EN, Latin words in RU, `[object Object]`, `$t`, `{name}`, `undefined`/`NaN`, a decimal point in RU, a hyphen-minus before a digit, and clipped or overflowing elements.
- `w00_pages.mjs`: catalogue (both modes, both widths, every card's parameter form), catalogue help, settings, legal; the language switch.
- `w01_worlds.mjs`: every world in each language — a preset, ⏺ for 4 s, a live change, a refusal (−1·10¹²), an action, the help, every panel opened (Physics of this world, checks, instruments with a quantity ticked, events with a click on the first, About the run), the «New world» form with a second scenario; in the playgrounds also the palette's placement form → «Place», the inspector (an edit and a refusal) and «New world» with «carry the scene over». Light worlds also start the new world.
- `w02_records.mjs`: the old records, at the end of the record, all panels, the history from the start, the help.
- `w03_misc.mjs`: page titles, whether `?lang=` follows the links, four worlds at 1280 px.
- `w04_v01_refusal.mjs`: v01 (whose only live control sits in «Actions»): a speed of 2 c refused.
- `w05_comma_input.mjs`, `w05b_comma_applied.mjs`: a decimal comma typed into a number field.
- `agg.py`, `sumlog.py`: summaries of the logs.

Logs are in `logs/` (`*.jsonl`, one record per step), screenshots in `shots/`. Screenshot names are
`w01_<world>_<lang>_<step>.png`; step 1 = after recording, 2 = after the live change and the refusal, 3 = help,
4 = each panel (`left00`…, `right00`…), 5 = placement form, 6 = inspector, 8 = after the new world.

## Summary

There are 15 findings: **1 error**, **4 should-fix**, **10 nits**.

The translation itself is thorough. In 42 world walks (21 worlds × 2 languages), the four static pages and the help
dialogs, the scanner found:
- no `[object Object]`, no raw `$t`, no unreplaced `{placeholder}`, no `undefined`/`NaN`;
- no Cyrillic in English pages of runs recorded after the commit;
- in Russian, no untranslated English msgid (the only Latin text is module names, citations, the licence texts that
  the page itself labels «на английском», and one engine exception text — F14);
- no page errors and no console errors or warnings.

Refusals, toasts, the carry-over notices, the placement form's head, the inspector's refusals and the checks are all in
the viewer's language, with the Russian number format (`1 000`, `0,01`, `−1·10¹²`). The switch EN | RU is on every
page, it is stored, `?lang=` overrides it, and a switch during a recording keeps the run recording (frames 81 → 171,
`playing` true before and after, same world).

The error:
1. **F1.** A decimal comma typed into any number field is silently dropped by the browser: «650,5» in v02's
   wavelength became **6505 nm** and was applied without a word. The Russian interface shows every number with a comma,
   so this is the input a Russian reader will type.

The should-fix items:
- the number fields show `632.8`, `-8.1`, `4000000000` next to read-outs `632,8`, `−8,1`, `4 000 000 000` (F2);
- records written before the commit play in English with Russian everywhere — and in Russian with points and
  hyphen-minus in their events and check notes; the run list shows their Russian titles in English (F3);
- `?lang=` is lost at the first link: a shared `…?lang=ru` link opens the catalogue in Russian, then the run or the
  settings in English (F4);
- the same concept has two Russian names in the same view: «Плейграунд» on the mode button, «Песочница…» in the help
  line under it and in the cards (F5).

## Results with their status

| # | check | result | status |
|---|---|---|---|
| R1 | `w01`: 21 worlds × EN/RU, 8 steps each, `scan()` after each step (`logs/w01_A.jsonl`, `w01_B.jsonl`; v01 again in `w01_v01.jsonl`, since its only live field sits in «Actions» and the first walk stopped there) | no `[object Object]`/`$t`/`{…}`/`undefined`; no Cyrillic in EN; in RU only module names, citations, version numbers and one exception text in Latin | [useful] |
| R2 | `w01`, `w04`: refusals of live fields, inspector fields, v01's speed | all in the viewer's language; RU uses `1 000`, `0,01`, `−1·10¹²`, «…» quotes (e.g. «Длина волны λ, нм»: −1·10¹² — меньше наименьшего 300; можно от 300 до 1 600) | [useful] |
| R3 | `w01`: toasts (placement moved to a free spot, a refused regrid in p02, carry-over notices in p01–p04) | translated, numbers localised, object names in «» | [useful] |
| R4 | `w00`: default EN; click RU stores `lfviz.lang=ru` and reloads; stored language holds on /settings; `?lang=en` overrides a stored `ru` without changing it; `?lang=de` falls back to the stored one; the switch on a `?lang=` page drops the parameter | as specified | [useful] |
| R5 | `w00`: v04 recording, switch EN → RU in the middle | the page reloads in Russian; the run is still recording (frames 81 → 171, `playing` true, `sim_t` 0.046 → 0.098 s, 1 world) | [useful] |
| R6 | page errors and console errors/warnings in every script | none (the only one seen was my own init script's, fixed before the runs) | [useful] |
| R7 | `w03`: `document.title` of the four pages | translated in both languages; a run page's title is the world's translated title even for an old record | [useful] |
| R8 | `w02`: 7 old records × 2 languages | F3 | [weakens] |
| R9 | `w05`, `w05b`: a comma typed into a number field | F1 | [weakens] |
| R10 | `w03`: `?lang=ru` (stored `en`) → run link; run `?lang=ru` → «← Каталог» | F4 | [weakens] |

## Findings

### F1 — error — a decimal comma typed into a number field is dropped, and the tenfold value is applied

**Where.** Every number field built by `control()`: the set-up, the «New world» form, the catalogue's parameter
forms, the playground's inspector and placement form, the speed field in v01's «Actions» (reproduced in v02 and v05; the other forms use the same control). Both languages; it matters in
Russian, where every number on the page is written with a comma.

**Steps.** `w05b_comma_applied.mjs`: v02, `?lang=ru`, browser locale ru-RU. In «Длина волны, нм» select the value,
type `650,5`, Enter.

**What happens.** The field becomes `6505`; no refusal; the world applies it. The event log says
`Длина волны, нм: 632,8 → 6 505`. The same with the browser locale en-US (`w05_comma_input.mjs`: v05's wavelength,
`600,5` → `6005`, refused here only because 6005 is above the maximum 1 600). Typing `600.5` works.

**Evidence.** `logs/w05b_comma_applied.jsonl`, `logs/w05_comma_input.jsonl`; screenshot
`shots/w05b_comma_applied_v02_ru.png`.

**Likely code.** `player/js/ui.js:225` (and `:310`): the field is `<input type="number">`. Chromium sanitises what is
typed into such a field by the browser's own locale, not the page's `lang`, and gives `input.value === "6505"` to the
script. `checkNumber()` (`ui.js:160`) already replaces a comma, but never sees one. The same input type is used in
`playground.js:710` (throw scale), `playground.js:888` (record window), `env3d.js:88` and `catalog.js:47`. Note that
`instruments.js:488` (`numIn`, the sweep form) uses text fields and accepts a comma — the two forms of the same panel
behave differently.

**Fix.** Text fields with `inputmode="decimal"`, parsed by `checkNumber()` (which should also accept `−` U+2212 and
the narrow no-break space that `fmt()` writes, so that a value copied from a read-out parses). Regression test: in
Russian, type `650,5` into a number field and expect 650.5 applied.

Not verified: a browser whose own UI language is Russian may accept the comma; the failure was reproduced with both
`en-US` and `ru-RU` page locales in headless Chromium.

### F2 — should-fix — the number fields keep the English format in Russian

**Where.** Every number field in RU (e.g. v05 set-up, v02 set-up, p02 inspector, the catalogue's parameter forms).

**Steps.** Open any world with `?lang=ru`.

**What happens.** Fields show `632.8`, `0.52`, `-8.1`, `4000000000`; the read-outs next to them show `632,8`, `0,52`,
`−8,1`, `4 000 000 000`. In the p02 inspector the same quantity appears twice, in two formats: the field «Центр при
приготовлении: x, нм» = `-8.1` above «⟨x⟩, нм −8,1».

**Evidence.** `shots/w01_p02_quantum_ru_6_inspector.png`, `shots/w01_v05_optics_bench_ru_2_refusal.png` (top bar and
left column), `shots/w00_catalogue_demo_forms_ru.png`.

**Likely code.** `player/js/ui.js` `fmtInput()` and the `type="number"` fields (F1). The fix of F1 (text fields
formatted by `fmt()`) fixes this.

### F3 — should-fix — records written before the commit are not translated, in either direction

**Where.** Catalogue run list; the run page of any record from before `d9da7cb` (here: 2026-10-28 v10; 2026-11-11 v01,
v02, v04, v07, p01, p03).

**Steps.** `w02_records.mjs`: open each with `?lang=en` and `?lang=ru`; also the catalogue in EN.

**What happens.**
- **EN.** Large parts of the page are Russian. In p01 (`shots/w02_20261111_p01_en_end.png`) the scene name, the
  approximation badge, the 3-D view buttons («Изо», «С полюса», «С ребра»), the palette («＋ Пробное тело»…), the scene
  objects, the checks, the instruments and the events. The scanner counts 40+ Russian lines per page in every old
  record. The catalogue's run list in EN shows these runs' titles, scenes and approximation tooltips in Russian
  (`shots/w00_catalogue_playground_en_1280.png`), while the same run's page title is English («The double-slit
  experiment · 20261111-…», `logs/w03_misc.jsonl`).
- **RU.** The texts that were formatted by Python before the commit keep `.` and `-`: «зарегистрирована в x =
  -1.54e+04 мкм», «Первая пара зарегистрирована: … (полёт 1.668e-06 с)», «Боб: настройка b, °: 22.5 → 30»,
  «Горизонт r₊ = 1.43589 G M/c²» (3-D layer), check tooltips «P_прош = 1.05602e-06…» (`logs/w02_records.jsonl`; e.g.
  `shots/w02_20261111_v02_ru_end.png`).

Old records stay on a server until the removal period ends, and records marked ★ stay for good. A viewer cannot
tell from the page that the record is older than the translation.

**Likely code.** The record keeps strings where new records keep T objects: `server/lfviz/runs.py:218, :239, :891`
(meta `title`/`scene`), the record's header and frames (labels, palette, checks, events). The player renders a plain
string unchanged (`i18n.js` `t()`).

**Fix.** At least: the run list and the run page take the title from the world's registry (`t(viz.title)`) rather
than the stored string, and an old record carries a visible note («recorded before the interface was translated; its
texts are in Russian»). Better: when a record is loaded, map each plain string that is exactly a Russian catalogue
value back to its msgid (a reverse lookup over `locales/ru.json`), so the static labels of old records translate; the
formatted strings stay as they are.

### F4 — should-fix — `?lang=` does not survive a link

**Where.** All pages.

**Steps.** `w03_misc.mjs`, `w00_pages.mjs`: stored language `en`; open `/?lang=ru`; click a run in the list; or open
`/run?id=…&lang=ru` and click «← Каталог»; or `/?lang=ru` → «⚙ Устройства».

**What happens.** The next page is in English (`lang` = `en`, URL without `lang`). Someone who received a `?lang=ru`
link reads one page in Russian and then the interface switches language under them.

**Evidence.** `logs/w03_misc.jsonl` («catalogue ?lang=ru → run link»: `lang: en`; «run ?lang=ru → ← Catalogue»:
`lang: en`), `logs/w00_pages.jsonl`; screenshot `shots/w03_lang_lost_on_run_link.png`.

**Likely code.** `player/js/i18n.js` `chosenLang()`: `?lang=` is read but neither stored nor carried; the links are
plain (`catalog.js:270` run link, `run.html` and `index.html` top-bar links).

**Fix.** Either store a valid `?lang=` in `localStorage` like the switch does (simplest; the address then wins only
once), or have `translateDom()` add the page's `lang` to same-origin links while the override is in force.

### F5 — should-fix — two Russian names for the playground

**Where.** Catalogue (RU), mode «Плейграунд»; run pages of p01–p04; settings page.

**What happens.** The mode button, the run list badge and the run page's scene say «Плейграунд» («Плейграунд:
частицы и молекулы»); the line directly under the mode button says «Песочница по разделам физики…»; the four cards
say «Песочница гравитации», «Песочница квантовой механики», «Песочница молекулярной динамики», «Песочница течений»; the
settings page says «(песочница «Электричество и магнетизм», …)» and «(плейграунд «Жидкости»)». A reader cannot tell
whether these are two things.

**Evidence.** `shots/w00_catalogue_playground_ru_1280.png` (both words in the first 200 px), `shots/w00_settings_ru.png`.

**Likely code.** `visualizations/locales/ru.json` («Playground» → «Плейграунд», «A sandbox by section of physics…» →
«Песочница…»), `p0*/locales/ru.json` (card summaries), `lfphys/lfphys/locales/ru.json` (kernel notes). In English the
same split exists («Playground» / «A … sandbox»), but there it reads as a description; in Russian «плейграунд» is a
loan word that a reader will not connect to «песочница».

**Fix.** One term in Russian (e.g. «Песочница» everywhere, or «Лаборатория» as the owner's own word «песочницы-
лаборатория» suggests), and a glossary entry in `RULES.md` «Languages and i18n» so that new texts keep it.

### F6 — nit — year forms in Russian: «1,00002 годы», «1,4794 / 1,2379 лет»

**Where.** p01 instruments (period of an orbit); v09 panel «Сейчас» and the result line.

**What happens.**
- p01: «Солнце»: период (задача двух тел), годы … `1,00002 годы` — the unit taken from the label (`{x:unit}`) keeps
  the nominative plural; correct is «года». EN shows «1.00002 years» while the time read-outs elsewhere say «yr».
- v09: «время t / τ  1,4794 / 1,2379 лет» — correct is «года» for a fractional number; the bottom bar of the same page
  says «t = 1,48043076 года» (`fmt` + plural rules are right there).

**Evidence.** `shots/w01_p01_gravity_ru_1_run.png`, `shots/w01_p01_gravity_en_1_run.png`,
`shots/w01_v09_thomas_3d_ru_1_run.png`.

**Likely code.** `p01_gravity/locales/ru.json` «years» → «годы» (used as the unit of a read-out);
`v09_thomas_3d/locales/ru.json` «{t:.5g} / {tau:.5g} yr» and «{T:.5g} yr by the clocks at rest, …» have no plural
forms (a plural entry needs `n`, `i18n.js` `lookup()`). Use the unit symbol «г.»/«лет» with plural forms keyed on `n`,
or the abbreviation used elsewhere.

### F7 — nit — the astronomical unit is «а. е.» and «а.е.» (and «au» / «AU» in English)

**Where.** v01 (same world: the catalogue form «Расстояние до Земли, а.е.», the canvas axes «0,9358 а. е.»), v04
(«а.е.»), p01 and the framework («а. е.»).

**Evidence.** `shots/w00_catalogue_demo_forms_ru.png` (v01 card), `shots/w04_v01_refusal_ru.png` (axes).

**Likely code.** Two msgids for one unit: `visualizations/locales/ru.json` «au» → «а. е.»; `v01_light_travel` «Distance
to the Earth, AU» → «…, а.е.», `v04_orbits` «AU» → «а.е.». One msgid («au») and one spelling.

### F8 — nit — hyphen-minus in some canvas tick labels

**Where.** v07 correlation plot (x ticks `-90°`, `-45°` next to y ticks `−0,5`); the image windows' angular ticks
(`-180°`, `-90°`). Both languages.

**Evidence.** `shots/w01_v07_bell_test_ru_2_refusal.png` (bottom of the correlation plot).

**Likely code.** `v07_bell_test/web/view.js:352` (`${d}°`), `player/js/imagewin.js:64-65`
(`${-180 + 90 * q}°`, `${90 - 90 * q}°`): raw template numbers instead of `fmt()`/`num()`.

### F9 — nit — numbers written by hand inside Russian texts keep the decimal point

**Where.** Physics of this world (v06: «пертурбативная область μ ≳ 1.5 ГэВ»), v01 notice «(r ≤ 1.5 rs)», engine theory
notes («γ − 1 = (2.1 ± 2.3)·10⁻⁵», «(−1.6 ± 1.5)·10⁻⁴», «42.98″/век», «3.046», «93.14», «0.17, 3.6, 5.9»), v09 «4.23»;
the settings page writes «2·10^4», «3·10^5» next to «10⁻⁵».

**Evidence.** `logs/w01_B.jsonl` (v06 «4 all panels»), `shots/w00_settings_ru.png`. About 12 catalogue entries; the
list is reproducible with the snippet in this review's notes (search `locales/ru.json` for `\d\.\d` outside citations
and equation numbers).

**Likely code.** `lfphys/lfphys/locales/ru.json`, `v01_light_travel/locales/ru.json`, `v09_thomas_3d/locales/ru.json`,
`v06_qcd/locales/ru.json`, and the kernel notes behind `/settings`. Either write them with a comma in the Russian text,
or make them placeholders formatted by `fmt()`.

### F10 — nit — v05: the Russian legend under the photon bars is cut at the canvas edge

**Where.** v05, RU, the «Photons of this segment» canvas.

**What happens.** «полоса — доля среди зарегистрированных; черта — ожидание запуска; отрезок» — the «: ±2σ» part
is outside the canvas. The English line fits.

**Evidence.** `shots/w01_v05_optics_bench_ru_2_refusal.png` vs `shots/w01_v05_optics_bench_en_2_refusal.png`.

**Likely code.** `v05_optics_bench/web/view.js:432`: one `text()` call without wrapping. Wrap to the canvas width (or
put the legend in HTML under the canvas).

### F11 — nit — catalogue run list: numbers and units break across lines

**Where.** Catalogue, run list, 1280 px; both languages, more in RU.

**What happens.** «0,229 / МБ», «6 мин 18,93 / с», «4,01442 / года» and «own / parameters» wrap inside their cells.

**Evidence.** `shots/w00_catalogue_playground_ru_1280.png`, `shots/w00_catalogue_playground_en_1280.png`.

**Likely code.** `player/js/catalog.js:283-288` (`t("{n:.3g} MB")`, `time()`): a plain space between number and unit.
Use a no-break space in the templates (and in `ui.js time()`), or `white-space: nowrap` on those cells.

### F12 — nit — the run list's «Scenario» column shows raw preset ids

**Where.** Catalogue, run list, both languages.

**What happens.** «brewster», «sun_earth», «kerr_orbits», «maxwell», «vector_narrow», «rest» — internal ids among
translated text. The run page and the «New world» form show the scenario's translated name.

**Evidence.** `shots/w00_catalogue_playground_ru_1280.png`.

**Likely code.** `player/js/catalog.js:283` (`r.preset || t("own parameters")`). Look up the preset's label in
`vizList` (`schema.presets`) and render it with `t()`.

### F13 — nit — Russian unit labels clipped by narrow canvases and the top bar

**Where.** p01 3-D view (the y-axis unit «а. е.» at the left edge shows as «е.»; EN «au» fits); the top bar at
1600 px: the «стандартная физика» badge is cut to «станда…» in v11, v12, v14, v15, v16, v17 (in English «standard
physics» is cut in v11, v15, v16, v17 — so Russian adds v12 and v14); p01 after a new world: «Космос и гравитация» cut.
Also, not language-specific: v06's energy axis ends in «10 Т» / «10 Te».

**Evidence.** `shots/w01_p01_gravity_ru_1_run.png` (left edge of the 3-D view at mid-height),
`shots/w01_v11_double_slit_2d_ru_1_run.png`, `shots/w01_v16_optical_vortices_ru_2_refusal.png`,
`shots/w01_p01_gravity_ru_8_newworld.png`; the `over` lists in `logs/w01_B.jsonl` (`span.badge.std`).

**Likely code.** `player/js/scene3d.js` axis label placement; `run.html` top-bar flex rules (`#title` and `#physics
.badge` shrink first). The badges' full text is in the tooltip, so this is cosmetic; the «standard physics» badge
could keep its width (it is short and important), and `#scene` could shrink first.

### F14 — nit — the engine's own exception text is English in a Russian event

**Where.** p02, RU, events: a refused regrid shows «Изменение не применено: …» and, under «подробности», the engine's
text «object #1 on the new grid: wall (across): the edge 0.995 is narrower than a grid of step 0.3438 can carry…»;
the old p03 record shows «axis y is periodic: it has no wall to move».

**Evidence.** `logs/w01_A.jsonl` («p02_quantum_ru 2 after live change + refusal»).

**Note.** The player folds an error's own text under «подробности» on purpose (`player/js/player.js:967`, review
UX-params P4); the translated summary is above it. This is
acceptable as long as the translated head says everything a viewer needs — here it does. Listed so that the decision is
explicit.

### F15 — nit — Russian case after a preposition: «к «Солнце»», «поглотил из «Электрон»»

**Where.** p01 placement toast («точка (0; 0; 0) а. е. слишком близко к «Солнце»»), p02 instruments («Экран»: поглотил
из «Электрон»).

**Evidence.** `logs/w01_A.jsonl` (p01_gravity_ru palette toast), `shots/w01_p02_quantum_ru_4_right01.png`.

**Likely code.** Templates in `p01_gravity/locales/ru.json`, `p02_quantum/locales/ru.json` put an object's name (a
nominative) after a preposition. Rephrase so the name stays nominative: «слишком близко к объекту «Солнце»»,
«поглощено из частицы «Электрон»».

## What was not covered

- The playground scene file round trip (💾 / 📂) was not exercised (it needs a file chooser); the carry-over was.
- Sweeps in «Instruments» were opened (the form), not run.
- The public site and the README are out of scope.
- A browser with a Russian UI locale (F1's last paragraph).
