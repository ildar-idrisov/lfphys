# Review i18n-language: the language of the English msgids and the Russian catalogues

**Status: awaiting processing.**

| | |
|---|---|
| Type | internal (independent subagent; it did not write the catalogues under review) |
| Date | 2026-11-12 |
| Scope | Commit `d9da7cb` («Interface in English and Russian (i18n)»). The Russian catalogues: `lfphys/lfphys/locales/ru.json` (engine, 962 entries), `visualizations/locales/ru.json` (framework and player, 1066), and `visualizations/<world>/locales/ru.json` for the 21 worlds that exist (p01–p04, v01–v17: 4840 entries). The English overrides `visualizations/locales/en.json`, `p01_gravity/locales/en.json`, `p03_molecules/locales/en.json`. The English msgids, as the source text. In all: 6868 entries. |
| Rules | `AGENTS.md` §1 (the owner's directions of 2026-11-12: «все тексты пиши на своем языке, консистентно»; the interface is English by default with switchable languages), §3 rules 12–16, `LANGUAGES.md`. |
| Not in scope | The READMEs and guides; only a spot check that their quoted UI labels match the catalogue. The completeness tests. Rendering in the browser. |
| Method | 1. Every entry was read once by one of nine readers. Each reader took one chunk: engine ×2, framework, p01+p02, p03+p04, v01–v03, v04–v07, v08–v12, v13–v17. The reader checked Russian grammar and terminology (Сивухин, Ландау–Лифшиц; school terms by the school textbooks), the English msgid, Latin left in the Russian, and the grammar around placeholders. Rows: `readthrough/reader_chunk_*.tsv`. 2. Scripts compared the catalogues with each other and with the code; they are listed below. 3. The reviewer verified the reported errors and a sample of the should-fix rows against the catalogues. Several reader rows were overruled; see the section «Reader rows overruled». |
| Environment | Host Python 3, `python3 -I`, read-only. The only git command was `git diff 88e7811 d9da7cb`, which reads. No container was needed. |

Files in this folder:

| File | What it does |
|---|---|
| `r00_load.py` | Loads all catalogues. |
| `r01_mechanical` | Identity entries, Latin tokens, placeholder sets, first-letter case, cross-catalogue conflicts, plural objects, American spellings, quotes, ё. |
| `r02_plurals` | Plural agreement (its counted-noun list is appendix C). |
| `r03_chunks` | Splits the entries into the readers' chunks. |
| `r04_terms` | Term renderings per catalogue. |
| `r05_drift` | Russian literals removed by the conversion that do not reappear in the catalogues. |
| `r06_english` | English spelling variants and label case. |
| `r07_placeholder_args` | Placeholders filled with plain strings in the code. |
| `r08_owner_labels` | Quoted Russian labels in the documents, checked against the catalogue. |
| `r09_owner_quotes` | Owner quotes next to `T()`/`t()` calls. |
| `r10_label_length` | Short labels whose Russian is long. |
| `r11_appendix` | Builds `APPENDIX.md`. |

Each checking script (r01, r02, r04–r10) writes its `.out` file; r03 wrote the chunks to a scratch folder and r11 writes the appendix. **`APPENDIX.md` holds the full lists:** all 756 read-through rows with ids `R<chunk>-<row>`, the plural list, the Latin «K», the decimal points, and the 2-D/2D counts.

## Summary

The conversion is sound in its mechanics:
- No placeholder is lost or renamed. One entry differs from its msgid in a JSON-schema text, which is correct.
- No msgid is translated differently in two catalogues; the merged catalogue has no conflicts.
- No Russian entry is a leftover identity copy.
- The English labels are consistently in sentence case.
- The Russian is mostly correct and readable.

The findings are about language.

**Counts.** The review groups its findings into 15 items:
- **3 errors:** F1–F3.
- **10 should-fix:** F4–F13.
- **2 nits:** F14–F15.

Behind them are 756 read-through rows (11 error, 395 should-fix, 350 nit) and 151 mechanical rows; all are in the appendix. The 756 rows break down by kind as follows:

| Kind | Rows |
|---|---|
| Russian style | 201 |
| Patterns | 136 |
| English style | 114 |
| Russian terms | 97 |
| Russian grammar | 78 |
| Russian meaning | 65 |
| English calques | 19 |
| Latin in Russian | 18 |
| Placeholder grammar | 13 |
| Typos | 9 |
| English spelling | 4 |
| English case | 2 |

**The most important:**
1. **F1. Meaning reversed or lost in single entries.** Fourteen entries; examples:
   - "present window" became «прежнего окна» (previous).
   - "agree … to 2–10 %" became «совпадают на 2–10 %».
   - "fluid" in "no liquid and vapour, only fluid and crystal" became «жидкость», so the sentence says "no liquid, only liquid".
   - "wall clock" became «часы стены».
   - "the cause is open" became «причина открыта» (found).
   - "spectator" became «наблюдатель».
   - "flat space-time" became «плоское пространство».
2. **F2. Agreement errors** that make a sentence ungrammatical:
   - «оба выбора … независим»
   - «против точного» for «модель»
   - «увиденная» with no noun
   - «каждый {k}-й интервал, отнесённая»
3. **F3. Misspelt names:** «Томно» (Tiomno), «Буччи»/«Буси» (Bussi), «Маркевка» (Marchewka), «Бурау» (Burrau), «Закон Снелла» (Snell), «Ганкель/Ханкель» side by side.
4. **F5, F6, F7. Three calques across almost every catalogue:**
   - "against" → «против»: 161 entries in 23 catalogues.
   - "closed form" → «замкнутая форма/формула»: 49.
   - numerical "error" → «ошибка»: 107, against «погрешность»: 4.
5. **F8. The playground's name.** EN has "playground" ×16 and "sandbox" ×6; RU has «Плейграунд» ×15 and «Песочница» ×7. The owner himself uses «плейграунд» (2026-11-04, 2026-11-12) and «песочницы-лаборатория» (2026-11-12). This needs the owner's choice, not a translator's.
6. **F11. Placeholders that carry English identifiers into Russian:** «добавлен slit_wall #3», «тело формы sphere». Several verbs after «{label}» or «{type}» have a fixed gender that breaks for half the labels.
7. **F12. Plural forms:**
   - «все 1 вычислитель занят … закройте вкладку одного из них»: the one-form of a plural entry.
   - 110 count phrases without plural forms.
   - English "every 2th/3th frame".
   - 11 entries with Russian plurals but no English override ("over 1 readings").
   - The Debye entry counts orders but reads as "at order n".
8. **F13. English msgids with calques from Russian:**
   - "Going on", "goes on" for resume
   - "the run's passport"
   - "the GPU gains"
   - "dearer than the budget"
   - "at the moment 0"
   - "Trajectories of them to draw"
   - "space-like to"

   The spelling is British, but it mixes polarisation ×55 with polarization ×11 (engine), disc with disk (v16 against v15), and 3-D with 3D.

No meaning drift was found between the owner's quoted phrases and the msgids (R10), with one exception: F8.

## Results with their status

| # | Check | Result | Status |
|---|---|---|---|
| R1 | `r01` C: placeholder sets of msgid vs. every Russian form (6868 entries, 23 catalogues) | 1 difference, a literal `{device: string, …}` JSON shape, correctly translated | [useful] |
| R2 | `r01` E: the same msgid in several catalogues with different translations (one wins in the merged catalogue) | none | [useful] |
| R3 | `r01` A: identity entries (ru = msgid) with Latin words | 1 (`DFG 2D-2: {what}`, a benchmark name): correct | [useful] |
| R4 | `r06` §4: Title Case among labels | none; labels are sentence case throughout | [useful] |
| R5 | `r04`: renderings of the key terms across catalogues | consistent: detector (151 → «детектор»), slice (130 → «срез»), probe (measurement «датчик», which-path particle «зонд»: two concepts, consistently kept apart), tolerance, packet, flux, screen, observer, reference («эталон» 95/102), check, throw, segment, inspector. Inconsistent: F5–F9 | [useful] / [weakens] |
| R6 | `r08`: Russian labels quoted in `README.ru.md` and the world READMEs vs. the catalogue | 43 quotes not found verbatim; all are either headings of curricula, measured values, or the same label with a placeholder (`«Отрезок N: …»` = `Отрезок {seg:d}: …`). No README names a label the interface does not have | [useful] |
| R7 | `r05`: 6928 Russian string literals removed from the code by the commit vs. the new catalogues | 774 do not reappear verbatim. A sample of 60 (framework, p01, v02): numbers moved into placeholders, decimal point → comma, small grammar fixes («Начать с сцены» → «со сцены»). No meaning drift in the sample | [neutral] |
| R8 | `r10`: short labels (≤ 4 words) whose Russian is ≥ 1.6× the English and ≥ 20 characters | 19, none clearly too long for its element (F14) | [neutral] |
| R9 | Reader rows overruled by the reviewer | 4 groups (section below) | [error in earlier] (in the read-through rows, not in the repository) |
| R10 | `r09`, AGENTS.md §1: owner quotes that became msgids | the six msgids next to the owner's «помечать там, где это приближение» (`APPROXIMATION:`, `Modified physics:`, …) keep its meaning; the owner's «срез», «автосмещение (по умолчанию выключено)», «Перенести сцену», «Демонстрации» are kept. The owner's «плейграунд» is mixed with «песочница» (F8) | [useful] / [weakens] |
| R11 | Verification of the 11 reader errors against the catalogue | all 11 confirmed (F1–F3) | [useful] |
| R12 | `r01` D: 62 entries whose Russian starts lowercase where the English is capitalised only by a proper name (`Bohr radius` → «боровский радиус», `Bohr period T` → «период Бора T», `Gaussian beam`) | checked in context for a sample (e.g. `player/js/orbitview.js:101`: the siblings are «time», «phase in the picture»): the Russian lowercase follows the lowercase class of the siblings, which is right. Only «а.е.» should be «а. е.», as the engine writes it | [neutral] |

## Findings

Locations are given as catalogue (`engine` = `lfphys/lfphys/locales/ru.json`, `framework` = `visualizations/locales/ru.json`, a world name = `visualizations/<world>/locales/ru.json`) and msgid (cut with … where long). Ids `Rnn-nnn` point to the appendix.

### F1 — error — meaning reversed or lost in single entries

| Catalogue | msgid | Now | Problem | Proposed | Id |
|---|---|---|---|---|---|
| engine | `particle {pid}: at the faces of the present window ({cells} outermost cells) lies …` | у граней прежнего окна ({cells} крайние ячейки) | "present" = current, not previous; case of «крайние» | у граней текущего окна ({cells} крайних ячеек) | R02-045 |
| engine | `fitted parameters (κ, a, m_q); predicts the level splittings … agree with experiment to 2–10 %` | расщепления совпадают с опытом на 2–10 % | says "differ by"; meaning is the accuracy | согласуются с опытом с точностью 2–10 % | R02-014 |
| engine | `flat space-time or the exterior of Schwarzschild`; `Bundles of rays … in flat space-time …`; `Light rays: flat space-time and Schwarzschild` | плоское пространство; внешность Шварцшильда | space-time lost; «внешность» is a calque | плоское пространство-время; внешняя область метрики Шварцшильда | R01-050, R02-015 |
| p03_molecules | `hard disks / spheres, a model (… no liquid and vapour, only fluid and crystal)`; also `… the fluid at ρσ^{d} …` | нет жидкости и пара, только жидкость и кристалл | self-contradictory | только флюид и кристалл | R05-035 |
| p04_fluids | `{nx:d}×{ny:d} nodes, step {dt:.3g} s; the real-time limit … depends on the wall clock …` | зависит от часов стены | literal | зависит от реального времени (по часам компьютера) | R05-097 |
| p04_fluids | `the engine's test (Ma 0.1, …): … the cause is open: STATUS` | причина открыта | says "found" | причина не выяснена (STATUS) | R05-103 |
| v12_arrival_times_2d | `ABK, the semiclassical rule … (the transverse packet is a spectator)` | (поперечный пакет — наблюдатель) | «наблюдатель» is the path detector in these worlds: the opposite | (поперечный пакет в расчёте не участвует) | R08-087 |
| p02_quantum | `The grid would not resolve a faster wave here and now (…)` | Быстрее сетка не передаст волну… | reads "will not pass it faster" | Более быструю волну сетка здесь и сейчас не разрешит (…) | R04-075 |
| framework | `Against the axis {a}` | Навстречу оси {a} | means "towards the axis" | Против направления оси {a} | R03-009 |
| v02_double_slit | `both slits are dark: nothing passes them` | за ними ничего нет | "nothing is behind them" | через них ничего не проходит | R06-042 |
| p02_quantum | `unchanged to round-off` | не изменилась до округления | "before rounding" | не изменилась с точностью до округления | R04-076 |
| p03_molecules | `laws changed while the world runs: {laws}` (+ the variant with the energy) | законы на ходу: {laws} | verb lost | законы изменены на ходу: {laws} | R05-041, R05-042 |
| p03_molecules | `no reference` | нет отсчёта | «отсчёт» is a reading; the catalogue says «эталон» | нет эталона | R05-047 |
| v15_kerr_shadow | `The disk rotates against the hole` | Диск вращается против дыры | counter-rotation relative to the spin | Диск вращается навстречу вращению дыры | R09-036 |

The rest of this kind (48 should-fix rows, e.g. «Из-за наблюдателя» for "From behind the observer", «облако — расстояние r» for a vector, «только кеплеровский вне ISCO», «Чтение исхода» for the interpretation): appendix, kind `RU-meaning`.

### F2 — error — agreement errors

| Catalogue | msgid | Now | Proposed | Id |
|---|---|---|---|---|
| v07_bell_test | `both choices outside the other side's cone; independent of the emission` | оба выбора … независим от вылета | …независимы от испускания пары | R07-054 |
| v08_wave_3d | `APPROXIMATION: the reduced 2-D model of slice {pid} ({plane}) against the exact one` | …модель среза … против точного | …в сравнении с точной | R08-001 |
| v09_thomas_3d | `θ from Lorentz matrices (the boost u, then the boost v′ = w as seen from u) …` | буст v′ = w, увиденная из u | буст v′ — скорость w, видимая из u | R08-032 |
| p01_gravity | `every {k}th interval, scaled to all the intervals passed` | каждый {k}-й интервал, отнесённая ко всем пройденным | каждый {k}-й интервал, пересчитанный на все пройденные (and EN, F12) | R04-022/023 |
| engine | `Classical MD in 2-D and 3-D: …` | термостаты … и Ланжевен (BAOAB) | …и Ланжевена (BAOAB) | R01-010 |
| engine | (Schott harmonics) | гармоники Шотта — точно | …точны | R02-001 |
| v13–v17 | `… less than half a step` / `Energy: scattered …` | меньше полшага; Энергия: рассеянное | меньше полушага; рассеянная | R09-019/020, R09-070 |

Further rows: 60 should-fix `RU-grammar` in the appendix. Examples:
- «Визуализация не сообщила модули движка» should be «не сообщила, какие модули движка использует».
- «Центр вращения — на объект».
- «Из них рисовать траекторий».

### F3 — error — names misspelt or declined wrongly

| Now | Proposed | Where | Id |
|---|---|---|---|
| Бому–Шиллеру–Томно | Бому–Шиллеру–Тиомно | engine | R01-001 |
| Буччи–Донадио–Парринелло / Буси | Бусси–Донадио–Парринелло | engine, p03 | R01-010, R05-009 |
| Маркевка | Мархевка (Marchewka) | engine, v12 | R01-024, R08-085/088 |
| Киёвский | Кийовский (Kijowski) | v12 | R08-086 |
| Бурау | Буррау (Burrau) | engine, p01 | R01-045, R04-008 |
| Малиевский / Malijevský in Russian prose | Малиевский consistently (or Latin only in references) | p03 | R05-020 |
| Ганкеля and Ханкеля | Ганкеля (the textbook form: функции Ганкеля) | engine, v16 | R02-063, R09-058 |
| закон Снелла, косинусы Снелла | закон Снеллиуса (закон преломления) | v05 | R07-020 |
| Форест–Рут–Йошиды | Фореста–Рута–Йошиды | engine | appendix R01 |

### F4 — should-fix — non-standard physics terms

The readers' 66 should-fix `RU-term` rows are all in the appendix. The terms that recur or that a physicist would stumble on:

| Now | Textbook term | Where | Id |
|---|---|---|---|
| Оптический стол (title of v05) | Оптическая скамья | v05 | R07-019 |
| статичный наблюдатель / статичные часы (GR) | статический | v01, p01 | R06-014 |
| время света | время распространения света | engine, v10 | R01-051, R08-052 |
| краска (passive dye) | краситель | engine, p04 | R01-052 |
| сетка передаёт волну (~20) | сетка разрешает волну | p02 | R04-074 |
| удары GRW | (спонтанные) локализации GRW | engine, v02 | R06-036 |
| подготовка состояния | приготовление состояния | v13, v14 (p02 already «приготовление») | R09-001 |
| прохождение (the coefficient) | коэффициент прохождения; Over-barrier → надбарьерное отражение | v03 | R06-058, R06-057 |
| Без сигнала; сигнализация; маргинал | невозможность передачи сигнала (no-signalling); маргинальное распределение | v02, v07, engine | R06-038, R07-045 |
| Казимир C_A, цветовые казимиры | оператор Казимира C_A | v06 | R07-037 |
| Момент h | момент импульса | v04 | R07-003 |
| в экваторе | в экваториальной плоскости | p01, v15 | R04-006, R09-029 |
| трубка потока (Aharonov–Bohm) | трубка магнитного потока | p02 | R04-055 |
| внутренняя устойчивая круговая орбита (ISCO) | последняя (внутренняя) устойчивая круговая орбита | v04 | R07-005 |
| падение в центр | падение на центр (Ландау т. I §18) | v04 | R07-008 |
| дисперсные узлы | диспергирующие | engine | R02-066 |
| сжимаемость CPTP-эволюции | сжимающее свойство (контрактивность) | engine | R02-061 |
| изопериметрическая граница | изопериметрическое неравенство / оценка | v09 | R08-024 |
| импульс (rocket burn) | разгон, включение двигателя | v09 | R08-023 |
| заслонка (screen with apertures) | экран с отверстиями | v08 | R08-003 |
| в лаборатории (frame) | в лабораторной системе отсчёта | v10 | R08-051 |
| показатель (index) | показатель преломления | v05, v17 | R07-029, R09-074 |
| обход фазы (winding) | число оборотов (набег) фазы при обходе оси | v13, v16 | R09-057 |
| будущий световой конус | световой конус будущего | v07 | R07-044 |
| ожидание (bare, for expected value) | ожидаемое значение / предсказание | v05, v07 | R07-022, R07-046 |
| спин-усреднённо | с усреднением по спину | v06 | R07-039 |
| Фит | аппроксимация (подгонка) | v02 | R06-029 |
| прочтение Бома / Эверетта | интерпретация | v03 | R06-062 |
| Игрушка (toy model) | упрощённая (модельная) задача | framework | R03-047 |
| (тяжесть) | сила тяжести | p04 | R05-072 |
| ступенька (FDTD staircase) | ступенчатая аппроксимация | engine | R01-054 |

### F5 — should-fix — "against" → «против» (161 entries, 23 catalogues)

**Location.** Engine 17, v09 17, v15 17, v17 17, v11 13, v12 12, … (`r04_terms.out`, TERM `against`). Only 40 entries use «в сравнении с», «сверка с» or «в зависимости от».

**Problem.** In Russian, «X против Y» reads as opposition («поле против точного», «вириал против стенок», «Диск вращается против дыры», «цвет против угла рассеяния»). The English "against" has three senses here, and each needs its own Russian rendering:

| Sense | Example msgid | Proposed |
|---|---|---|
| compared with a reference (most) | `… |E|² at {n} points against the direct calculation` | «в сравнении с прямым расчётом» / «сверка с …» |
| a plot of y over x | `Sky: colour against the scattering angle` | «в зависимости от угла рассеяния» |
| a short label in a table | `cτ against 2L` | «cτ ↔ 2L» / «cτ и 2L» |

The English is acceptable ("plotted against", "checked against"). The Russian needs a pass by sense. Reader patterns: R01-056, R02-039, R03-066, R04-019, R05-015/033/078, R07-001/036/057, R08-002, R09-004.

### F6 — should-fix — "closed form" → «замкнутая форма / формула / решение» (49 entries)

Russian has «в замкнутом виде» (expression), «аналитическое выражение», «точное решение». The noun «замкнутая формула» is a calque.

| Example | Proposed |
|---|---|
| `closed forms exist only for k = −2, −1, 1, 2` → «замкнутые формулы есть…» | «выражения в замкнутом виде есть…» |
| `This quantity has no closed reference` | EN: "no closed-form reference"; RU «эталона в замкнутом виде нет» |

Ids: R01-048, R02-009, R03-046, R06-019, R09-003.

### F7 — should-fix — numerical "error" → «ошибка» (107) against «погрешность» (4)

The textbook term for a numerical or estimated error is «погрешность» (Бахвалов «Численные методы»; ГОСТ for measurements). The catalogues use it in 4 entries and «ошибка» in 107.

Proposal:
- «погрешность» for an error of a scheme, a step, an estimate or a measurement: «погрешность шага», «оценка погрешности».
- «ошибка» only for a mistake or failure: «ошибка загрузки», «ошибка в данных».

Ids: R01-049, R02-091. All entries with "error" are listed in `r04_terms.out`.

### F8 — should-fix — the name of the playground: one word per language, the owner's choice

**Location.**
- EN uses "Playground" ×16 (`framework` `Playground`, `p01`–`p04` titles `Playground: …`, engine) and "sandbox" ×6 (`framework` `A sandbox by section of physics: …`, `A sandbox for research: …`, every playground description).
- RU follows with «Плейграунд» ×15 and «Песочница» ×7.
- The engine translates the same English word both ways: `(the “Fluids” playground)` → «плейграунд», `(the playground “Electricity and magnetism”, optics)` → «песочница».

**Problem.** One mode carries two names in each language.

The owner's own words:
- 2026-11-04 (RULES.md): «плейграунд для исследований … в плейграунде можно добавлять».
- 2026-11-12 (AGENTS.md §1): «песочницы-лаборатория» as the name of the fourth audience, and «плейграунд должен быть отмечен серым», «плейграунды для изучения сложных физических законов».

Four readers (R01-036, R04-004, R05-082, R03-025) propose «Песочница» everywhere as the Russian word. That is a reasonable language choice, but it overrides the owner's term.

**Proposed.** Ask the owner. Then use one word per language:
- EN: "playground", with "sandbox" removed.
- RU: either «Плейграунд», the owner's word for the mode, or «Песочница», the owner's word for the audience and a Russian word. Rule 13 «no words of another language leaking in» argues for «песочница».

Then apply it to every entry and to `README.ru.md`, which has «(плейграунд)» ×11.

### F9 — should-fix — other inconsistent terms across catalogues

| English | Renderings (count, where) | Proposed |
|---|---|---|
| run (the visualization's run) | «запуск» 135 (framework, most worlds); «прогон» 22 (v11, v12: `The run solves the Schrödinger equation …` → «Прогон решает…», `computed on … as the main run`) | «запуск» for the run; «прогон» only for the auxiliary computations (`a parallel run on the grid …`) |
| sweep | «свип» ×44 (framework only; lab slang) | «перебор параметра» / «серия расчётов» (R03-024) |
| worker | «вычислитель» ×12, «рабочий процесс» ×1 | one term; «вычислительный процесс» or «вычислитель» (R03-044) |
| preparation (of a state) | «приготовление» 22, «подготовка» 9 | «приготовление» (F4) |
| distant observer | «далёкий» / «удалённый» | «удалённый наблюдатель» (R07-002) |
| click | «щелчок» / «клик» | «щелчок» (R03-045) |
| 2-D, 3-D in Russian | «2-D/3-D» 90 (engine 74), «2D/3D» 65 (worlds), «двумерный» 14 | «2D/3D» (the Russian norm) or the words; one form (R03-050, R08-004, appendix F) |
| post-Newtonian orders | «2,5PN» and «2.5ПН», «ПН/PN» mixed, even inside one entry | «2,5ПН» throughout (R02-056) |
| equation in references | «ур.» and «Eq./eqs.» | «ур.» in Russian (R01-057) |
| primary bow | «первичная» / «основная» | «первичная радуга» (R09-075) |
| choose | «выберите» / «возьмите» | «выберите» (R09-064) |

### F10 — should-fix — Latin and English notation left in Russian

- **Latin «K» for the kelvin: 31 entries** (p03 18, e.g. `Heating to {T} K` → «Нагрев до {T} K»). The Russian unit is «К»: appendix D.
- **Decimal point in Russian prose: 9 entries** (engine 8, v01 1). Examples: «42.98″/век», «γ − 1 = (2.1 ± 2.3)·10⁻⁵», «|δ| ≤ 0.17», «μ ≳ 1.5 ГэВ», «r ≤ 1.5 rs». Appendix E; R02-030.
- **"review B8-fdtd F12", "review R15", "review B4-3" left in English: 7 entries** (engine, v02, v11, v13). One entry already has «ревью». Use «ревью B8-fdtd F12» (R02-068).
- **p04 `the picture's field: speed | vorticity | pressure | dye` → «поле картины: speed | vorticity | pressure | dye».** If these are option identifiers, mark them as code (backticks); if the user sees them, translate them as «скорость | завихренность | давление | краситель» (R05-098).
- **Author and experiment names in Latin inside Russian prose**, outside references: «Michelson–Morley, Kennedy–Thorndike, Ives–Stilwell», «Drude, Lorentz или Debye», «Chael и др.». Write them in Cyrillic in prose, «Майкельсона–Морли, Кеннеди–Торндайка, Айвса–Стилуэлла», and keep Latin only in the bibliographic references (R02-073, R05-077, R09-048).
- **API messages that list identifiers** (`fluid {name}: 'water' or 'air'`, `boundary {kind}: pml, pec, pmc or periodic`, `unknown particle {name}: electron, neutron, …`) are correct as they are: the identifiers are code. This is [neutral].

### F11 — should-fix — placeholders that carry English or break Russian grammar

1. **English identifiers inside Russian.**
   - `lfphys/lfphys/core/quantum/scene.py:1710, 1717, 1727`: `T("added {type} #{oid}", type=obj.TYPE)`. Here `TYPE` is `"box"`, `"slit_wall"`, `"harmonic_trap"`, `"flux_tube"`, `"detector"`, `"localization"`. The Russian «добавлен {type} #{oid}» then reads «добавлен slit_wall #3», and the masculine «добавлен / убран / изменён» does not fit «стенка». Proposed: pass a translatable name, `type=T(...)` per class, and write the Russian without gender: «добавлено: {type} #{oid}».
   - `fdtd.py:992`: `T("a body of shape {kind}", kind=b["shape"].kind)` gives «тело формы sphere». Same remedy.
   - These are engine events, `Scene.events` and the commit text. The reviewer did not find `visualizations/p02_quantum/viz.py` reading them, so they reach API clients and logs today, and the player only if a world displays them later.

2. **Gender fixed after a label of any gender.** Examples:
   - p01: «{label}» пересёк / ушёл / остался.
   - p02: «{label}»: найдена / оказалась бы; «за краем он не действует».
   - p04: `“{type}” is placed on the side…` → «поставлен», which breaks for «Подвижная стенка», «Периодичность».
   - p03: `{what:cap} started anew…` → «начаты», which breaks for «поршень».
   - v10: `{body}: in the lab now (contracted)` → «(сокращён)», which breaks for «улица», «столбы».

   Proposed: a construction without gender. Examples:
   - «{label}: пересечение горизонта»
   - «{label}: обнаружение в {at} нм»
   - «(лоренцево сокращение)»

   The same can be done with the noun «объект»: «объект «{label}» пересёк…». Ids: R04-039, R04-080, R05-059, R05-099, R08-054.

3. **Case around a placeholder.**
   - p02 «({where} или край окна)»: `{where}` is filled in the genitive (R04-079).
   - Quoted labels after a verb stay in the nominative, «выберите для «Элемент у щели {j:d}» одно из» (R05-049). This is acceptable with quotation marks, so it is a nit.

### F12 — should-fix — plural and ordinal forms

1. **framework** `all {n:d} workers are busy with open runs: close the tab of one of them (…)`. The Russian "one" form, «все {n:d} вычислитель занят открытыми запусками: закройте вкладку одного из них», is used for n = 1, 21, 31. For n = 1 it reads «все 1 вычислитель занят … одного из них». English has its own text for one worker; Russian cannot express that through CLDR "one" because the category also covers 21. **Proposed:** the same text for every form, «Заняты все вычислители ({n:d}): закройте вкладку одного из запусков (…)». Alternatively, the server could send a separate msgid when n = 1.
2. **English ordinals.** `t, {unit} (every {k:d}th frame of the record: …)` (framework) and `every {k}th interval, …` (p01) give "2th", "3th", "21th". **Proposed:** "one frame in {k:d}", "one interval in {k}" (R03-063, R04-022).
3. **English plural overrides missing for 11 msgids** that have Russian plural forms (`r01`/appendix):
   - `the maximum over {n:d} readings {dt} apart`, `the minimum …`
   - `Slice {id} ({plane}): ψ at {n} points …` ×2 (v13)
   - `… |E|² at {n} points …`, `a grid of {n:d} points …`, `… the last {n} samples …`, `{n:d} samples …` ×2 (v16)
   - `the Debye series diverges at {n:d} orders …` (v17)
   - `{x} yr`, which is fine, since "yr" does not inflect

   Add the "one" forms to the `en.json` of the framework, v13, v16 and v17.
4. **v17** `the Debye series diverges at {n:d} orders (…)`. `viz.py:228` counts the multipole orders n at which the series diverges. The Russian «расходится на {n:d} порядке/порядках» reads as "at order n". **Proposed:** EN "the Debye series diverges for {n:d} multipole orders (…)"; RU «ряд Дебая расходится для {n:d} мультипольного порядка / порядков (…)».
5. **110 count phrases without plural forms** (appendix C). Most are genitive after «из», «по», «в» or large grid sizes, and harmless. The ones in the nominative or accusative are wrong for counts ending in 1 or 2–4:
   - «в сцене уже {n:d} объектов»
   - «{points:d} точек, шаг …»
   - «по y {ny:d} узлов»
   - «{C:d} точек ансамбля проинтегрированы»
   - «{n:d} частиц из {N:d}»
   - «{T:.5g} лет» (1,5 лет)
   - «в {f} раза» for integer f (в 5 раза)

   **Proposed:** a plural entry («{n:d} объект / объекта / объектов»), or the label form «объектов: {n:d}». The framework's abbreviations used to avoid plurals («точк.», «замер.», «знач.», «кадр.») should become plural entries as well (R03-072).

### F13 — should-fix — English msgids: calques from Russian and mixed spelling

**Calques**, with proposed English:

| Now | Proposed |
|---|---|
| "Going on: the world is recomputed…", "Going on failed", "⏺ goes on", "it cannot go on" (~12, framework) | "Resuming: …", "Resuming failed", "it cannot be resumed" (R03-017, R03-056) |
| "the run's passport (JSON)" | "the run's record card / metadata (JSON)" (R03-067) |
| "the GPU gains", "does not gain on the GPU" | "the GPU is faster", "is not faster on the GPU" (R03-021) |
| "dearer than the budget" | "over budget" (R03-076) |
| "A sandbox by section of physics" | "… by branch of physics" (F8) |
| "at moment 0", "Event on Andromeda at the moment (lab), days" (v01) | "at t = 0", "Time of the event on Andromeda (lab), days" (R06-015) |
| "Playground: Newtonian N bodies" | "Newtonian N-body problem" (R04-005) |
| "in the equator" (p01, v15) | "in the equatorial plane" (R04-006, R09-029) |
| "Trajectories of them to draw" (v11, v12) | "Trajectories to draw" (R08-069/070) |
| "choice space-like to the emission", "time-like to" (v07) | "space-like separated from" (R07-055) |
| "Reading the outcome" (v03, a choice of interpretation) | "Interpretation" (R06-061) |
| "Second state real" (v13, v14) | "Second state: real" |
| "the scheme carries" (p04), "by a jump" (p03) | "the scheme supports / contains", "instantaneously" (R05-090, R05-032) |
| "the check “Convergence”", "the panel «Scene layers»" | "the “Convergence” check" (R09-068) |
| "lawfully" (p01) | "legitimately" (R04 appendix) |
| "Maxwellian at T" among lowercase options (p03) | "maxwellian at T" or capitalise the siblings (R05 EN-case) |
| "the packet's slow edge (k₀ − 3·ħ/(2σ))" (v03) | dimension mixes a wave number with a momentum: k₀ − 3/(2σ) in both languages (R06 appendix) |

**Spelling.** The project is British (Licence ×12, centre ×90, colour ×40, metre, grey, cancelled, normalised), but the British spelling is mixed with these variants:

| British | Other variant | Where | Proposed |
|---|---|---|---|
| polarisation ×55 | polarization ×11 | engine, all 11 | one form; the catalogue mostly writes -ise (normalised, polarisation, localisation), so polarisation (R02-032) |
| localisation | localization ×7 | engine, p02 | localisation |
| polariser | polarizer | engine | polariser |
| disc ×13 | disk ×49 | v15 39 against v16 8; engine both | disc for the accretion disc and the optics disc. "hard disks" in p03 is the established term of statistical mechanics and may stay (R01-059, R09) |
| 3-D ×90 | 3D ×8 | engine, p02, v13 | 3-D (R01-060) |
| space-time ×5 | spacetime ×11 | — | one form |
| cross-section ×9 | cross section ×2 | — | one form |
| Eq./Eqs. | eq./eqs. | — | one form (R01-058) |

"visualization" may stay: it is the folder and product name, and -ize is also Oxford British.

### F14 — nit — label length

`r10` found 19 short labels whose Russian is ≥ 1.6× the English. None is in a fixed-width element that would overflow (parameter labels in a form, legend lines, options). Candidates for shortening:

| Label | Proposed |
|---|---|
| `Random seed` → «Затравка случайных чисел» | «Затравка ГСЧ» |
| `time t (lab)` → «время t (лаборатория)» | «время t (лаб.)» |
| `Second state real` → «Второе состояние вещественное» | «2-е состояние: вещественное» |

The count labels in the bare genitive («Точек», «Замеров», «Звёзд», «Пакетов в цепочке») read as fragments. «Число точек» etc. is clearer; the English has the same gap: "Rays in 3-D" should be "Number of rays in 3-D" (R05-080, R08-033, R09-087).

### F15 — nit — recurring Russian style

- **«считается / посчитан»** for "is computed". This is colloquial and ambiguous («мир считается вокруг неё»); use «рассчитывается», «рассчитан» (R04-001, R08-005).
- **First-person statuses next to impersonal ones**: «Измеряю…», «ждём…». Use «Измерение…», «ожидание…» (R03-073).
- **Prepositions:**
  - «на r = …», «у r = …», «в t = …», «на z = 0», «на {lam} нм» should be «при r = …», «при t = …», «при z = 0», «при {lam} нм» (R04-033, R07-004, R09-002, R09-066, R09-089).
  - «Что если» should be «Что, если».
- **The remaining nits**, 134 `RU-style` and 84 `EN-style` rows, are in the appendix.

## Reader rows overruled

| Rows | Verdict |
|---|---|
| R01-036, R03-025, R04-004, R05-082 («Плейграунд» → «Песочница») | Not adopted as they stand: the owner's own term. Reframed as the decision F8. |
| R02-011, R02-018 ("fluid" → «среда» in `fluid {name}: 'water' or 'air'` and the p04 texts) | Overruled. In hydrodynamics «жидкость» covers gases too (Ландау–Лифшиц т. VI §1), so «жидкость» stays in p04. The statistical-physics «флюид» in p03 (F1) is a different sense and stands. |
| R07-045 («отсутствие сигнализации») against R06-038 and R01-025 («сигнализация» = alarm) | Merged. The proposal is «невозможность передачи сигнала (no-signalling)», used everywhere (F4). |
| R01-049 and R02-091 rate «ошибка» as nit or should-fix differently | Merged as F7, should-fix for consistency. |

Every other reader row is kept as reported. The reviewer checked all error rows and about 60 should-fix rows against the catalogues; no other false positive was found. Row-level judgement calls the readers flagged themselves, such as the genitive count labels or the gender of `{back_label}`, are marked nit in the appendix.
