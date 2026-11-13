# Response (worlds-2 part) to the review i18n-language, 2026-11-12

**Responder:** PR-C2, the agent processing worlds v10–v17 and p01–p04 (container prefix `lf-pc2-`). It wrote neither
the review nor the catalogues under review. **Date:** 2026-11-13.

**Scope.** Every finding and read-through row that concerns the catalogues of p01_gravity, p02_quantum, p03_molecules,
p04_fluids and v10–v17 (`visualizations/<world>/locales/ru.json`, and the `en.json` files), their English msgids in each
world's `viz.py`, `engine/` and `web/view.js`, and the documents that quote them: each world's `README.md` and
`README.ru.md`, and the lines about these worlds in the root `README.md` and `README.ru.md`. The engine catalogue is
answered by PR-B (`RESPONSE_engine.md`), the framework catalogue by PR-D (`RESPONSE_framework-language.md`), and v01–v09
by PR-C1 (`RESPONSE_worlds-1.md`).

This response also applies the owner's decisions of 2026-11-13 and the integrator's glossary:
- the laboratory rename ("Laboratory" / «Лаборатория»);
- погрешность for a numerical error;
- аналитическое решение / в замкнутом виде;
- «против» rendered by its sense;
- запуск / запись;
- 2D/3D in Russian, 2-D/3-D in English;
- ПН;
- «а. е.», «а. е. м.»;
- decimal comma, Cyrillic «К»;
- the names Мархевка, Буррау, Бусси, Ганкель;
- British spelling;
- plural forms for every count phrase;
- no "{k}th".

**Method.**
- The catalogues were edited by scripts. Each script read a table of msgid → new msgid / new Russian, re-read each file
  just before writing it, and kept the catalogue's sort and format.
- An English msgid was changed together with:
  - the `T("…")`/`t("…")` literal;
  - the catalogue key (the stale key removed);
  - `en.json`;
  - the tests that assert the text;
  - the READMEs that quote it.
- Before the Russian of a msgid was changed, the msgid was looked up in every catalogue. A msgid shared with a catalogue
  of another part was aligned with that part's decision; such cases are listed below.

## Summary

| Finding | In these worlds | Outcome |
|---|---|---|
| F1 meaning | p02 R04-075, R04-076; p03 R05-035, R05-041/042, R05-047; p04 R05-097, R05-103; v12 R08-087; v15 R09-036 | fixed, all 9 |
| F2 agreement | p01 R04-022/023; v14 R09-019; v17 R09-070 | fixed |
| F3 names | Буррау (p01), Бусси, Малиевский (p03), Мархевка, Кийовский (v12), Ганкеля (v16, v17), Шефер и Турек, Гиа (p04) | fixed |
| F4 terms | разрешает, трубка магнитного потока, наклонение, экваториальная плоскость, инфинитное движение (p01, p02); краситель, сила тяжести, сеточное число Рейнольдса (p04); время распространения света, лабораторная система отсчёта (v10); приготовление, число оборотов фазы, показатель преломления (v13–v17) | fixed |
| F5 «против» | every entry of these 12 catalogues | fixed by sense. «против» is kept only for real opposition: «против вращения», «против часовой стрелки», and «Против направления оси z» for a view direction |
| F6 closed form | v10, v11, v12, v13, v15, v16 | fixed: «аналитическое выражение/решение», «в замкнутом виде» |
| F7 «ошибка» | p01 6, p02 5, p03 6, p04 8 entries, and v10–v17 | fixed: «погрешность». «ошибка» is kept for faults («это не ошибка», «ошибка чтения»), and «стандартная ошибка» is kept as the statistical term |
| F8 laboratory | p01–p04: titles, summaries, the view.js headings, the READMEs | fixed by the owner's decision |
| F9 terms | «запуск» for the run (v11, v12; «прогон» only for the companion run and the soft detector's second run); «первичная», «выберите» (v15–v17); «удалённый наблюдатель» (p01); «свип» → «перебор параметра» (p01, p02 READMEs, root README.ru) | fixed |
| F10 Latin, decimal point | Latin «K» (p03 18 entries, v10, v17), Latin names in prose (p04, v10, v12, v15–v17), the p04 field names `speed \| vorticity \| …` | fixed. Bibliographic keys stay in Latin; v13–v17 use one rule for them: "et al." and "&" |
| F11 placeholders | p01, p02, p03, p04, v10 | fixed (details below) |
| F12 plurals | appendix C rows of these worlds; `en.json` one-forms for v13, v16, v17 (F12.3); the v17 Debye count (F12.4); "{k}th" (p01) | fixed. Four rows are not applied because their count is a constant (below) |
| F13 calques, spelling | p01 ~20, p02 ~12, p03/p04 ~20 msgids; v11/v12 "Trajectories of them to draw"; v13/v14 "Second state: real"; v15 "disk" → "disc" (29 msgids); "polarisation", "localisation", "3-D", "cross-sections", "eq." | fixed |
| F14 label length, bare genitive | "Number of …" labels (v10, v11, v12, v15, v17, p03, p04); «Второе состояние: вещественное»; `time t (lab)` | fixed. `time t (lab)` is partly applied (below) |
| F15 style | «рассчитывается» in place of «считается»; «при r = …», «при t = …», «при z = 0», «при {lam} нм»; «Что, если»; «ожидание…» | fixed |

**Rows.** The appendix has 354 rows for these worlds:
- p01: 54
- p02: 41
- p03: 66
- p03/p04: 3
- p04: 40
- v10: 20
- v11: 24
- v12: 12
- v13–v17: 94 (R09-001…094), including the shared sections

Outcomes:
- **Applied as proposed or with a variant:** 340.
- **Applied in part:** 5 (R04-093, R05-049, R09-005, R09-012, R09-013).
- **Not applied, with a reason:** 9.

Every row that is not applied, or not applied in full, is listed below. All the others are fixed.

## Rows not applied, or applied in part

| Row | World | Outcome | Reason |
|---|---|---|---|
| R04-044 | p01 | not applied | "set the velocity measured…" and "set vx, vy, vz" are options of a select (the velocity mode), not hints. The infinitive is right for an option. |
| R04-052 | p01 | not applied | "mass, M☉", "speed, km/s" are plot-axis and read-out labels. They are lowercase by design and consistent among themselves. |
| R04-053 | p01 | not applied | "Newtonian gravity of point masses" is an item of the approximations list. The list items are lowercase, like their siblings (the review's R12). |
| R04-093 | p02 | partly | Russian «3D: …» applied. English keeps "3-D" (the glossary) and "ball" (the palette object is "Ball"). |
| R05-031 | p03 | not applied | "Maxwellian" is a proper adjective and is capitalised in English. Its siblings start with common words. |
| R05-049 | p03 | partly | Generic nouns are added where a quote followed a verb: «переключите параметр «Динамика»», «меньше значение «Радиус обрезки»», «параметр «Положение, нм»». Quotes after «=» are kept, which the review accepts. |
| R05-069 | p04 | not applied | «Гуо» is the rendering used in Russian LBM texts. «Го» would not be recognised. |
| R05-074 | p04 | not applied | C_D/C_L are the DFG benchmark's own symbols, used in all its notes. Renaming two labels would make them disagree with the notes. |
| R08-049 | v10 | not applied | An option among lowercase siblings. The English is capitalised only by a proper name, and the review's R12 says lowercase is right here. |
| F14 `time t (lab)` | v10 | partly | «время t (лабораторное)» is used rather than «(лаб.)», which reads as "the room" again (R08-051). |
| R08-075 | v11 | not applied | `{back_label}` is filled only with neuter labels («отражено пластиной», «ушло назад», `BACK_LABEL`). «отражены» is a legend label of the particle counts, never this placeholder. |
| R09-005 | v13, v14, v16 | partly | «становятся видны» applied. The label `phases revealed` is the framework's msgid (`player/js/orbitview.js`). PR-D set it to «Раскрытые фазы», and v16's copy now matches. |
| R09-012, R09-013 | v13 | partly | The Russian is fixed. The English msgids are emitted by `visualizations/server/lfviz/orbitals3d.py` (PR-A's file) and translated in v13's catalogue. The English rewording ("choose states with at most two distinct energies", "growing fourfold when the step is doubled") is left to PR-A. |
| R09-071 | v17 | fixed differently | The text pointed at "New world", a button that does not exist. It now names the framework's button: "change with “▶ Start a new world”" / «меняются кнопкой «▶ Начать новый мир»». |
| R09-076 | v17 | not applied | «фазовая функция» is the accepted rendering and matches the English and the other entries. «индикатриса» would be a world-wide term change that needs the owner's choice. |
| App. C `{px} pixel` | p01 | not applied | px = 0.25, a constant. «меньше 0,25 пикселя» is correct (genitive after «меньше»). |
| App. C `a grid of {n:d} points` | p02 | not applied | Genitive after «из»; grid sizes never end in 1. |
| App. C `{tight:d} times` | p02, v11 | not applied | tight = 4, a constant: «в 4 раза» is correct. |
| App. C `{f} times coarser/finer` | v11 | not applied | f = COMP_GRID = 1.2, a constant: «в 1,2 раза» is correct. |

## Details by finding

### F1 — meaning
- **p02:** «Более быструю волну сетка здесь и сейчас не разрешит (…)» (R04-075). "unchanged to within round-off" / «не изменилась с точностью до округления» (R04-076); two test assertions were updated.
- **p03:** «только флюид и кристалл» and «флюид при ρσ^{d}» (R05-035), «законы изменены на ходу» (R05-041/042), «нет эталона» (R05-047).
- **p04:**
  - «…зависит от реального времени по часам компьютера — она показана у ползунка скорости» (R05-097).
  - "the cause is an open question" / «причина не выяснена (STATUS)» (R05-103).
- **v12:** «(поперечный пакет в расчёте не участвует)» (R08-087).
- **v15:** "The disc counter-rotates with respect to the hole" / «Диск вращается навстречу вращению дыры» (R09-036).

### F8 — laboratory (owner's decision)
- **Titles.** "Playground: space and gravity / quantum particles / particles and molecules / fluids" → "Laboratory: …" / «Лаборатория: …». p01's laws titles: "Laboratory: the Newtonian N-body problem" (with R04-005), "Laboratory: a binary in GR (m = …)", "Laboratory: bodies and light near a Kerr–Newman black hole (…)".
- **Summaries.**
  - EN: "A gravity laboratory", "A quantum mechanics laboratory", "A molecular-dynamics laboratory", "A flow laboratory".
  - RU: «Лаборатория гравитации», «… квантовой механики», «Лаборатория молекулярной динамики», «Лаборатория течений».
- **Also changed:** the view.js headings, and both READMEs of each lab.
- **Kept:** the owner's quoted words («в плейграунде», v11 README) stay verbatim as quotations, and so do the internal ids (`kind: "playground"`, `pNN`).

### F11 — placeholders (gender, case, English ids)
- **p01:**
  - «{label}»: пересечение горизонта — для удалённого наблюдателя никогда…
  - «{label}»: уход на r = …, дальше не прослеживается
  - «…, остаётся объект «{kept}»»
  - «{label}»: не удалось поставить — {why}
  - «новый запуск с прежнего места», «новый запуск по своим параметрам»
  - «у тела «{label}»»
- **p02:**
  - «{label}»: обнаружение в точке {at} нм
  - «объект «{label}» оказался бы…», «объект «{label}» частично за краем…: за краем он не действует», «объект «{label}» целиком вне окна»
  - «с объектом «{label}» …»; statuses «регистрация: {where}», «бросок: v = …»
  - «(внутри {where} или у края окна)» (case, R04-079)
- **p03:**
  - «{what:cap} — заново по параметрам: {why}» (R05-059)
  - «{what} в области {area}: занятая доля составила бы {frac}»
  - The Verlet failure used to insert the engine's English reason («шаг Верле не удался (non-finite forces)»). It now gives the world's own text; test `test_a_failed_verlet_step_names_the_reason_in_the_owners_words`.
- **p04:** «…— объект «{type}» поставлен на сторону «{free}»» (R05-099), «объект «{label}» оказался бы…» (R05-100).
- **v10:** «{body}: в лабораторной системе сейчас (лоренцево сокращение)» (R08-054).
- **No other agreement depends on a label:** no other text in v10–v17 has a verb whose gender depends on a placeholder.
- **API identifiers:** `no action “{name}”` and `no object “{type}”` (p02) carry an API client's own unknown name. That is code, as F10's last bullet allows.

### F12 — plurals
- **p01:** "every {k}th interval" → "one interval in {k}, scaled to all the intervals passed" / «один интервал из {k}, с пересчётом на все пройденные». "{f:.4g} times slower" → «медленнее, множитель {f:.4g}», with no counted noun.
- **p02:**
  - Grid counts in the label form: «точек по оси: {n:d}», «сетка {n:d}², точек: {pts:d}»; 128² = 16384 had given «16384 точек».
  - `every {n:d} steps` (n = 64): ru one/few/many/other, and a new `p02_quantum/locales/en.json`.
- **p03:**
  - Plural entries: «не больше {n:d} атома/атомов», «…молекулы/молекул», «только {k:d} из {n:d} …», «из {n:d} блока/блоков», «за {n:d} шаг/шага/шагов», «({n:d} компонента/…)».
  - The bare `T("{n} atoms")` became the plural msgid `{n:d} atoms`. `{n:d} atoms, {e:d} events` is new (code-review F12).
  - English one/other forms in `p03_molecules/locales/en.json`.
- **p04:** the grid is named «сетка N × M», with no counted noun. A new `p04_fluids/locales/en.json` has `St = f D / U ({n:d} periods of C_L)` and `{n:d} nodes where the previous world had a body start at rest`.
- **v10:** «в {n:d} пикселе/пикселях» (ru and en). **v12:** `A train of {n:d} packets…` and `{n:d} particles of {N:d}…` (ru, and en where English needs it).
- **v13, v16, v17:** new `en.json` files (F12.3: 2, 5 and 2 msgids). v17 F12.4: "the Debye series diverges for {n:d} multipole orders (…)" / «…для {n:d} мультипольного порядка / порядков», with the view.js variant likewise.
- **v15:** "{p}th percentile" → "percentile {p}". «идёт расчёт: строк {k:d} из {n:d}», «ломаная, число точек которой — {pts:d}».

### F13 — English
- **p01:** "Closer in, … breaks down"; "Initial black hole mass / charge / spin"; "Feels gravity but does not itself attract"; "Instruments: distance to"; "Scene carried over to a world with different laws: … (whatever made sense was converted; see the scene)"; "inside the horizon"; "equatorial plane"; "companion run".
- **p02:** "Atomic mass, u"; "localisation"; "3-D" (5 msgids); "changes, as it should"; "The reason is the location / speed"; "requested".
- **p03:** "instantaneously"/"instantaneous" (7 msgids); "carried over"; "penetrate each other"; "as the simulation runs".
- **p04:** "can handle"/"must withstand"/"contain" for "carries"; "is being accumulated"; "Smooth start-up time, s"; "Tangential wall velocity, m/s".
- **v10:** "polar angle θ from the z axis", "View: elevation, °", "at zero velocities … the identity".
- **v11:**
  - "Packet: width along x σx, λ"
  - "make the slit width a smaller than … or the distance d larger than …"
  - "the reflection x → −x"
  - "compared with the overlap of the path marks"
  - "Trajectories to draw"
- **v12:** "Trajectories to draw"; "switch on “Soft detector” in the new-world form".
- **v13–v17:**
  - "Second state: real"
  - "n (principal, n ≥ 1)"
  - "the cloud is smaller by a factor Z = …"
  - v15 "disc" everywhere in user text (the mesh id `"disk"` stays an id)
  - "the “Convergence” check" word order
  - "Refractive index of the surrounding medium"
  - v17 presets "drops of radius …", "nearly equal drops"
  - "eq."/"eqs." as the engine writes them
  - "cross-sections"
- **Quotation marks:** English «…» became “…” in every msgid touched.

## Cross-catalogue decisions (one msgid, one translation)

| msgid | Catalogues | Decision |
|---|---|---|
| "Mass, u" | p03, v02 | «Масса, а. е. м.» (glossary; the integrator's ruling); all p03 entries now «а. е. м.» |
| "Where it was computed" | v08, v10, v15 | «Где рассчитано» in all three (the integrator's ruling) |
| "View along the x axis" | v09, v10 | «Вид вдоль оси x» (a camera view, as v09) |
| "phases revealed" | framework, v16 | «Раскрытые фазы» (PR-D) |
| "points" | framework, p02 | p02's entry removed; the framework's «точки» applies |
| "running" | framework, p01 | «идёт расчёт» |
| "a smaller spin or charge" | engine, p01 | the engine's «спин или заряд меньше» kept |
| "⁴He atom" | engine, p02 | p02's entry removed; the engine's text applies |
| "Show the 3-D view alongside" | p02, p04 | one msgid, «Показать 3D-вид рядом» (docs pass) |
| "Computation: seconds per step ({device}, estimate)" | p02, p03, p04 | «Счёт: …» kept in all three. R04-063's «Расчёт: …» can be applied later in all three together. |

## Docs pass (label mismatches)
- **p01:** the hint now quotes the option's real label, "start farther or choose the orders “Newton + radiation reaction {a}PN”" / «… «Ньютон + реакция излучения {a}ПН»».
- **p01, p02 clear-scene:**
  - **What exists:** the player has no clear-scene button. Objects are removed one by one with ✕ or Delete, and the API's scene command `clear` exists.
  - **What was wrong:** the world help never named a button, but the READMEs described clearing the scene as an interface action.
  - **Change:** both READMEs of each world now say what exists. No button was added.
- **p02, p04:** "Show the 3-D view alongside" is now one msgid. p02's other 3-D texts also say "3-D".
- **p03:** the help quotes “Wall (kind)” and “Position, nm”. The box-mode help no longer quotes labels that do not exist (“Affinely”, “Wall”); it quotes the option "compress or stretch together with the matter".
- **v13:** the help quoted “Superposition”, which is the group, while the user picks the option “a superposition of two states” / «суперпозиция двух состояний». The help and both READMEs now quote the option.

## Documents
- **World READMEs.** Every changed label, title, preset and term is updated in both READMEs of each world: the laboratory rename, «против», «погрешность», «в замкнутом виде», Мархевка, Кийовский, Буррау, «спин-зависимых», "disc", the v13 quote.
- **Not updated:** prose in the v13–v17 READMEs that quotes no label (some «против», «ошибка» in running text) was not rewritten. The READMEs were outside this review's scope.
- **Root README.md / README.ru.md.** The lines about these worlds were checked by a script against the presets and titles the worlds render now, in each language. Changed:
  - EN:
    - p03 "A 2-D crystal … the order parameter ψ6 vanishes …"
    - p02 "Tunnelling: a packet hitting a thin barrier higher than its energy" and "… by half a period"
    - v13 "… the cloud is smaller by a factor Z = 2"
    - v15 "The disc edge-on …"
    - v10 "A sky of 4000 K …"
    - v17: all seven presets say "drops of radius …" / "nearly equal drops"
    - v15/v16 prose "disc"
  - RU:
    - p01 «Буррау», «массой 1000 M☉», «(спиральное сближение)»
    - p02 the tunnelling, trap, Aharonov–Bohm and 3D presets; «перебор параметров»
    - p03 «Двумерный кристалл … 120 К», «Аргон с одинаковыми начальными скоростями атомов…», «90 К», «Твёрдые диски: давление в сравнении с…»
    - p04 «(Пуазейля, …)», «…в сравнении с таблицами Гиа, Гиа и Шина, 1982»
    - v10 «4 000 К», «проверка трассировщика», «лоренцево сокращение», «Поезд проезжает мимо столбов при β = 0,8…»
    - v12 «первые приходы частиц Бома»
    - v13 «облако меньше в Z раз (Z = 2)»
    - v15 the title «Тень чёрной дыры Керра и её фотонные кольца», «на радиусе 6 M», «Что, если: …»
    - v17 «капли радиусом …», «первичная и вторичная дуги»
    - prose «против» → «в сравнении с» in 8 lines (v14, v15 ×3, v16, v17 ×2, p03 alt text)
- **Records.** A record written between `d9da7cb` and now that holds a renamed msgid shows that text in English in the Russian view, because the catalogue no longer has the old msgid. This affects only the renamed labels and help, check and refusal texts above.

## Tests
- **World tests** (Docker `lfphys-viz`, CPU, `--memory=4g`):

  | Worlds | Result |
  |---|---|
  | p01 | 42 passed, 1 skipped |
  | p02 | 52 passed |
  | p03 + p04 | 145 passed, then the one test that fed a plain English string was switched to a coded exception and passes |
  | v10 | 20 passed |
  | v11 | 28 passed, 1 skipped |
  | v12 | 18 passed, 1 skipped |
  | v13–v17 | 133 passed |

- **`tests/test_checkpoint.py`, `test_restore.py`, `test_carryover.py`, `test_manipulation.py`** with `-k` for these worlds: v10–v12 9 passed; v13–v17, p01, p02 21 passed; p03, p04 6 passed.
- **`tests/test_i18n.py`** and the browser checks: see `RESPONSE_worlds-2.md` in the code and browser review folders, which give the final runs.
