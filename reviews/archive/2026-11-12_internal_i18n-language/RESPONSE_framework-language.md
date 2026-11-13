# Response (framework-language part) to the review i18n-language, 2026-11-12

**Responder:** PR-D, the framework-language processing agent (prefix `lf-pd-`). It wrote neither the review nor the
catalogues under review. **Date:** 2026-11-13.

**Scope.** Every finding and read-through row of the framework catalogue (`visualizations/locales/ru.json`, `en.json`)
and the framework's msgids in `visualizations/server/**`, `visualizations/player/**` and the framework's test worlds
(p97, p99), with the documents that quote them: the root `README.md`/`README.ru.md`, `visualizations/README.md`/
`README.ru.md` and `visualizations/RULES.md`. The engine catalogue is answered by PR-B (`RESPONSE_engine.md`), and the
world catalogues by PR-C1 and PR-C2 (`RESPONSE_worlds-1.md`, `RESPONSE_worlds-2.md`). This response also applies:
- the owner's decisions of 2026-11-13 and the integrator's glossary (laboratory, «МОДИФИЦИРОВАННАЯ ФИЗИКА», погрешность,
  перебор параметра, «в сравнении с», plural forms, British spelling);
- the docs pass's label mismatches: the "New world" button that does not exist, and the padded " APPROXIMATION: ";
- code-review F12's framework count msgid.

**Method.** The changes were written as one table of msgid → new msgid / new Russian, applied by a script. The script
re-read each catalogue and code file right before writing it (PR-A edits the same files at the same time) and checked:
- each old literal was present exactly as often as expected;
- every translation had its msgid's placeholders;
- every plural form was well formed.

Only msgid string literals were changed in the code, together with the three test asserts and the one browser-check
msgid that quote them.

## Summary

| Finding | Framework part | Outcome |
|---|---|---|
| F1 meaning | `Against the axis {a}` | fixed |
| F2 agreement | none in the framework | — |
| F3 names | none in the framework | — |
| F4 terms | «Игрушка» (R03-047) | fixed |
| F5 «против» | 3 entries | fixed |
| F6 closed form | 2 entries (R03-046) | fixed, EN and RU |
| F7 «ошибка» | 3 numerical entries | fixed; the faults keep «ошибка» |
| F8 playground | the framework's 8 entries, the docs | fixed by the owner's decision: "laboratory" / «лаборатория» |
| F9 terms | sweep, worker, click, 2-D, run | fixed |
| F10 Latin, decimal point | no framework entry has a Latin «K» or a decimal point in prose | nothing to do (checked) |
| F11 placeholders | R03-079 (gender after «{label}») | fixed |
| F12 plurals | items 1–3 and 5, framework | fixed |
| F13 calques, spelling | the framework calques | fixed; spelling: no variant in the framework (checked) |
| F14 label length | `Random seed`, the bare-genitive labels | fixed |
| F15 style | statuses, «считается», prepositions, «клик» | fixed in the framework |
| R12 | «а. е.» | already right in the framework (`au` → «а. е.») |

The appendix lists 79 framework rows. 77 are applied as proposed or with a variant; the variants are named below.
- **R03-011 is not applied.** «период Бора T» stays lowercase: the reviewer's own R12 checked the siblings in
  `orbitview.js`, and they are lowercase.
- **R03-012 and R03-060 are applied** (with R03-026's column header «точки», and «идёт расчёт» for "running"). These four
  msgids are shared with other catalogues: «Только CPU» with the engine, «Раскрытые фазы» with v16, «точки» with p02,
  «идёт расчёт» with p01. They were changed on the integrator's decision of 2026-11-13, and the integrator asked PR-B,
  PR-C1 and PR-C2 to set the same text. Until they do, `test_no_msgid_is_translated_differently_in_two_catalogues`
  reports these four msgids.

## Findings

### F1 — error — `Against the axis {a}` (R03-009)
**Fixed.** «Навстречу оси {a}» → «Против направления оси {a}». This is the review table's proposal. The appendix
proposes «Против оси», but «против направления» names the direction and is not the «против» calque of F5.

### F4 — should-fix — «Игрушка» for the toy model (R03-047, R03-034)
**Fixed.**
- `Toy (tests)` → «Упрощённая модель (тесты)».
- `Toy: free particles` → «Упрощённая модель: свободные частицы».
- The toy's region → «точка вне области модели».
- EN `The plane z = 0 (toy: no field is computed)` → `(toy model: no field is computed)`, RU «(упрощённая модель: поле не
  рассчитывается)».

### F5 — should-fix — "against" → «против»
**Fixed, all 3 framework entries.** Each is rendered by its sense:
- «поле в точках плоскости в сравнении с точным полем без БПФ»;
- «сверка с общепринятой физикой» (R03-029);
- «отклонение fp32 от fp64» (R03-027).

No «против» is left in the framework catalogue, apart from «Сопротивление».

### F6 — should-fix — closed form (R03-046)
**Fixed in both languages.**
- `This quantity has no closed reference` → `This quantity has no closed-form reference`, «Для этой величины нет эталона
  в замкнутом виде».
- `… the closed formula of accepted physics …` → `… the closed-form expression …`, «справа — формула общепринятой физики
  в замкнутом виде …».
- In the same entry, «в пределах численной точности» became «… погрешности».

### F7 — should-fix — «ошибка» for a numerical error
**Fixed.**
- `a numerical error` → «численная погрешность».
- `fp32: error ≤ …` → «fp32: погрешность ≤ …».
- The precision note: «относительная погрешность БПФ … около 10⁻³».

«ошибка» stays for faults («внутренняя ошибка мира», «ошибка мира, а не выбранных значений», «могут содержать ошибки»).

### F8 — should-fix — the playground's name
**Fixed by the owner's decision of 2026-11-13.** The name is «Лаборатория / Laboratory», and the section is
"Laboratories" / «Лаборатории».

| msgid before | msgid now | Russian |
|---|---|---|
| `Playground` (the catalogue's mode button) | `Laboratories` | «Лаборатории» |
| `playground` (run-list badge) | `Laboratory` | «Лаборатория» |
| `playground · being kept` | `Laboratory · being kept` | «Лаборатория · сохраняется» |
| `Playground: the record holds a window …` | `Laboratory: …` | «Лаборатория: запись хранит окно …» |
| `this is not a scene file of this playground …` | `… of this laboratory …` | «… этой лаборатории …» |
| `this run is recorded whole: only a playground has a record window` | `… only a laboratory …` | «… только у лаборатории» |
| `A sandbox by section of physics: …` | `A laboratory for each branch of physics: …` (also F13) | «Лаборатория для каждого раздела физики: …» |
| `A sandbox for research: …` | `A laboratory for research: …` | «Лаборатория для исследований: …» |

- **Badge msgid.** The badge uses the capitalised msgids `Laboratory` and `Laboratory · being kept`. The lowercase
  `laboratory` is v01's msgid for the lab frame («лабораторная»), and reusing it was a conflict (found by the conflict
  check).
- **Internal identifiers stay:** `kind: "playground"`, `lfviz.playground`, the `pNN` ids.
- **Documents.**
  - The root README.md and README.ru.md: the section «Лаборатории», the switch, the "(laboratory)" tags, the image alts,
    "a laboratory is planned".
  - `visualizations/README(.ru).md`: the section "Laboratories (B6, 2026-11-03)", the switch and the player's left
    column.
  - RULES.md §6: the interface name next to the code identifier.
  - RULES.md §7: a new **Glossary** entry, so that new texts keep the terms (the browser review F5's fix).
- **Not in this part.** The world titles `Playground: …`, the card summaries, and the engine's «(плейграунд «Жидкости»)»
  belong to PR-C2 and PR-B.

### F9 — should-fix — inconsistent terms
**Fixed in the framework.**
- **sweep → «перебор параметра» (44 entries).**
  - «Перебор параметра», «Перебор № {n:d} запущен», «Переборы этого запуска:», «▶ Запустить перебор», «Процесс
    перебора …», etc.
  - The verb «перебирать» stays where it fits: «В этом мире нечего перебирать».
  - The tautologies are rephrased: «законы, которые меняет только новый мир, в переборе не участвуют», «такие параметры
    не перебираются».
- **worker → «рабочий процесс»** everywhere (it was «вычислитель» ×14 and «рабочий процесс» ×1; R03-044).
- **click → «щелчок»** (R03-045).
- **2-D/3-D → «2D»/«3D»** in Russian, e.g. «2D: плоскость z = 0», «в 3D-мир», «2D-мира» (R03-050).
- **run.** «запуск» was already used throughout the framework, so there was nothing to change.

### F10 — should-fix — Latin and notation left in Russian
**Nothing to do in the framework.** It has:
- no Latin «K» for the kelvin;
- no decimal point in Russian prose (the only matches are «r185.1», «Licence 1.0», «BY-NC-SA 4.0», «P16.3»: version
  numbers and identifiers).

R03-002 is applied: «… но это не открытое ПО (не open source)».

### F11 — should-fix — placeholders and gender
**Fixed for the framework row R03-079.** The entry now reads «{label}» лежит в плоскости z = const: перетаскивайте объект в
окне этой плоскости или в 3D-сцене». «лежит» has no gender, and «объект» replaces «его».

R03-071 is also fixed: «ось {axis} пересекает плоскость этого окна: перетащите «{label}» …».

### F12 — should-fix — plural and ordinal forms
**Fixed.**
1. **`all {n:d} workers are busy …`.** The Russian now has one text for every n: «заняты все рабочие процессы ({n:d}):
   закройте вкладку одного из запусков (он приостановится и продолжится, …)». The English "one" form is kept.
2. **Ordinal.** `t, {unit} (every {k:d}th frame of the record: a limit of {cap:d} rows)` → `t, {unit} (one frame in
   {k:d} of the record: a limit of {cap:d} rows)`. The Russian keeps «каждый {k:d}-й кадр» (correct for every k) and
   puts the limit as a label: «строк — не больше {cap:d}».
3. **English one-forms added to `en.json`:**
   - the maximum and the minimum over readings;
   - `At most {n:d} plots at once`;
   - `Cancelled: {k:d} of {n:d} values computed…`;
   - `Done: …`;
   - both `None of the {n:d} values…`;
   - both `undefined in {bad:d} of … readings`;
   - both `the scene already holds {n:d} objects…`;
   - `{k:d} of {n:d} values`;
   - `{name}: {n:d} characters…`;
   - `verified at {n:d} points…`;
   - `a period of {n} days…`;
   - the two cost-estimate texts.

   `en.json` now has 26 entries; it had 8.
4. *(v17, not in the framework.)*
5. **Count phrases, appendix C framework list (19 entries) and R03-072.**
   - **Plural entries (ru one/few/many/other)** where the count is `n`: plots, values (Cancelled, Done, None ×2,
     `{k:d} of {n:d} values`), readings (undefined ×2), objects (the scene already holds ×2), characters, points
     (verified), days (a period).
   - **Label forms** where the counted number is not `n`, or two numbers meet:
     - «объектов перенесено {n:d} из {total:d}»;
     - «файл сцены длиннее допустимого: символов {n:d}, предел {max:d}»;
     - «значений {values:d} × замеров {n:d}»;
     - «кадров записи: {frames:d}»;
     - «№ {n:d} · {target} · значений: {k:d}» (here n is the sweep's number, not a count);
     - «GPU — при числе точек от {size}».
   - **The abbreviations are gone:** «знач.», «замер.», «кадр.», «точк.».
   - **`… runs {k:.2g} times slower`.** The form «в {k} раза» is wrong for whole numbers (it gives «в 5 раза»), so the
     text is now «мир идёт медленнее, коэффициент {k:.2g}».
6. **Code review F12, framework part.** The sweep CSV's `… each value — {duration} of the world; {n} readings` (which
   gave «1 readings») → `{n:d} readings` with plural forms in both languages (`server/lfviz/sweep.py`). p03's
   `{n} atoms` was reported to the integrator for PR-C2.

### F13 — should-fix — English calques and spelling
**Fixed (framework).**

| Calque | Now |
|---|---|
| "Going on…", "Going on failed", "Go on: …", "⏺ goes on", "it cannot go on", "nothing to go on with", "It could not go on at once", "suspended and go on" (R03-017, R03-056) | "Resuming…", "Resuming failed", "Resume: … and continues", "⏺ resumes", "it cannot be resumed", "nothing to resume", "It could not be resumed at once", "suspended and resume" |
| "the record goes on" (restoring statuses, restore notices, the cancel notice, "World restored … going on from") | "the record resumes" / "continues", "continuing from"; "The previous world continues." |
| "the run's passport (JSON)" (R03-067) | "the run's metadata (JSON)", «метаданные запуска (JSON)» |
| "does not gain on the GPU", "the GPU gains", "the GPU does not gain", "kernels do not gain from the GPU" (R03-010, R03-021) | "is not faster on the GPU", "the GPU is faster", "the GPU is not faster", "kernels are not faster on the GPU" |
| "dearer than the budget" (R03-062, R03-076) | "stopped: over budget" («превышен предел»), "stops if it exceeds {limit}" |
| "A sandbox by section of physics" (R03-007) | "A laboratory for each branch of physics" |
| "There is nothing to go over", "a sweep does not go over" (R03-040) | "nothing to sweep", "a sweep does not vary" |
| "while it played", "the world has not played ⏺ yet" (R03-075) | "while it was running", "the world has not yet been run with ⏺" |
| "Noticed an effect — press …; the record goes on whole" (R03-023) | "If you notice an effect, press …: the window with it is kept, and from then on the record is kept in full." |
| "are what holds" (R03-041) | "are binding" |
| "also by commercial publishers", "also under CC BY", "needs an agreement" (R03-003, R03-004) | "including those from commercial publishers", "including under CC BY", "requires an agreement" (the Russian follows) |
| "not the correctness of any task" (R03-033) | "not that any given problem is solved correctly" |
| "Fold the group" (R03-015) | "Collapse the group" |
| "Reset to the recommended" (R03-030) | "Reset to recommended settings" |
| "take k at most 100 N/m" (R03-064, p97) | "set k to at most 100 N/m", «задайте k …» |
| "the grid of visits {old} is not the one here {new}" (R03-069, p99) | "the visit grid {old} differs from this world's grid {new}" |
| "repeat the cancel in a second" (R03-070) | "try cancelling again in a second" |
| "by the measured cost of computing the whole sweep …" (R03-057) | "at the measured cost of computing, the whole sweep …" |
| "one equal to the set value too" ×3 (R03-031) | "including one equal to the set value"; RU «Каждое значение, в том числе равное заданному, …» |
| "the laws of the form below" ×4 (R03-042) | "the laws set in the form below" |
| "(the direction of view the same)" (R03-032) | "Move the 3-D view's centre of rotation to the object (the direction of view unchanged)" |
| "the common memory" (R03-078) | "main memory", «основную память» |
| "lose about 10⁻³" (R03-028) | "have relative errors of about 10⁻³" |

**Spelling.** The framework's msgids have no -ize/-or/center/3D/spacetime variant. The one "disk" ("on the disk {mb} MB")
is the storage device, where "disk" is the British spelling too.

### F14 — nit — label length
**Fixed.**
- `Random seed` → «Затравка ГСЧ».
- `Points` → «Число точек».
- `Readings` → «Число замеров», with its title «Число замеров за время расчёта …».
- `threads` → «потоки».
- `phases revealed` → «Раскрытые фазы» (shared with v16; see the summary).

### F15 — nit — Russian style
**Fixed in the framework.**
- **Statuses.** «ожидание расчёта/изображения/запуска/мира…», «Идёт замер…», «идёт расчёт…» (R03-022, R03-073).
- **«считается / посчитан» → «рассчитывается / рассчитан».** Applied in every framework entry where it meant
  computation: the record button, the help, the device page, the sweep texts, «Путь (рассчитан)», «не рассчитан», …
- **Prepositions.** «на t =» → «при t =» in 5 entries.
- **«Что если».** None in the framework.

### Other read-through rows (framework), all applied

| Row | Now |
|---|---|
| R03-001 | «(штриховая — ⟨r⟩)» |
| R03-005 | «тот, кто даёт пользоваться … обязан показывать пользователям …» |
| R03-006 | `… the other laws change with “▶ Start a new world”.`, «… остальные законы меняются кнопкой «▶ Начать новый мир».» |
| R03-008 | «… всё рассчитывается движком по его законам …» |
| R03-013 | «Выберите срез: щёлкните по его плоскости в 3D или по его окну.» |
| R03-014 | «Всё, что было в окне, и всё последующее хранится, пока вы не выключите запись.» |
| R03-016 | «… вдоль самого плотного луча зрения, параллельного оси области …» |
| R03-018 | «… не удалять ни через {days} без действий, ни по квоте» |
| R03-019 | «N — к следующему событию» |
| R03-020 | «Клавиши: T — тема, ? — справка.» |
| R03-035 | «Вид на плоскость {a}–{b} по нормали, {a} вправо — как в окне» (variant: «анфас» is not used for planes) |
| R03-036 | «Вид следует за этим объектом …» |
| R03-037 | «Визуализация не сообщила, какие модули движка использует.» |
| R03-038 | «Мир восстанавливается: срезы и сцену можно будет менять, когда запись продолжится.» (and the two siblings: «новый мир можно будет начать», «действия будут доступны») |
| R03-039 | «нет ни законов …, ни объектов» |
| R03-043 | «контракт приборов» |
| R03-048 | «Область применимости: {validity}» |
| R03-049 | «логарифмическая шкала значений» |
| R03-051 | «видеокарта» (and «вторая видеокарта» in the GPU 0 note) |
| R03-052 | «свечение» |
| R03-053 | «пересчитать его не из чего» |
| R03-054 | «расчёт шёл уже {t}» |
| R03-055 | «фактически: {speed}» |
| R03-058 | «… за пределы представимого диапазона» |
| R03-059 | «наведите курсор на изображение / срез» |
| R03-061 | «за краем области» |
| R03-065 | «движок не сообщил, какие у него устройства: {error}» |
| R03-066 | see F5 |
| R03-068 | «отметки — …» |
| R03-074 | «потоки» |
| R03-077 | «больше максимума / меньше минимума …; допустимо: …» (also «нет варианта …; допустимо:») |

In the same style, «цена счёта» → «стоимость расчёта» (`Cost of computing`, `First “Estimate”`, the estimates).

## The docs pass's label mismatches (brief)

- **"New world" button.** No button is labelled "New world". The panel is "New world: …" and its button is "▶ Start a new
  world". Four msgids named a "New world" button; they now name "▶ Start a new world" / «▶ Начать новый мир»:
  - `player.js` (the laboratory's live-laws help, R03-006);
  - `catalog.js` (the catalogue's help);
  - `runs.py` (an old record's refusal);
  - `player.js` (the help's "“New world” means …", now "“▶ Start a new world” starts a world with other laws …").
- **Padded badges.** `" APPROXIMATION: "` → `"APPROXIMATION:"` and `"MODIFIED PHYSICS: "` → `"MODIFIED PHYSICS:"`; the
  code adds the space (`player.js` `renderPhysics`).
  - The Russian is now the owner's wording in full: «МОДИФИЦИРОВАННАЯ ФИЗИКА:», «ПРИБЛИЖЕНИЕ:», and the catalogue mark
    `modified physics` → «модифицированная физика».
  - The root README.ru.md and `visualizations/README.ru.md` quote it.
  - v04's and v07's README.ru.md still say «МОДИФ. ФИЗИКА». These are world files; they were reported to the integrator
    for PR-C1.

## Documents updated

- **`README.md`, `README.ru.md` (root):**
  - laboratories: the intro, the table of contents, the section heading and its text, the switch, the tags, the image
    alts, "planned";
  - «МОДИФИЦИРОВАННАЯ ФИЗИКА»;
  - «Перебор параметра».
- **`visualizations/README.md`:**
  - "resuming failed — ⏺ tries again" ×2, "resuming: the world is being restored…", "the world is being restored — the
    recording resumes by itself";
  - the section "Laboratories" and its text;
  - "exceed the limit".
- **`visualizations/README.ru.md`:**
  - «МОДИФИЦИРОВАННАЯ ФИЗИКА: …»;
  - «рабочий процесс» (the worker's memory, suspension, the troubleshooting row «заняты все рабочие процессы (3): …»);
  - the section «Лаборатории»;
  - the sweep paragraphs → «перебор», «рядом с «Число замеров»», «не рассчитан», «если превысит предел»;
  - «Если мир долго рассчитывает изменение».
- **`visualizations/RULES.md`:**
  - §6, the interface name (laboratory) next to the code identifier;
  - §7, the Glossary entry.

## Code touched (msgid literals only)

- **Server:** `server/lfviz/runs.py`, `worker.py`, `sweep.py`, `instruments.py`, `errors.py`, `playground.py`.
- **Player:** `player/js/player.js` (and the two `+ " " +` of the badges), `catalog.js`, `settings.js`, `legal.js`,
  `instruments.js`, `playground.js`, `player/settings.html`.
- **Test worlds:** `tests/playgrounds/p99_toy/viz.py` and `web/view.js`, `tests/instruments_worlds/p97_osc/viz.py`.
- **Tests:** `tests/test_sweeps.py` (one assert: "at the measured cost of computing, …"), `tests/test_server.py` (three asserts: "Resuming", "Resuming from the world's saved state", "The previous
  world continues"), `tests/browser/instruments_checks.mjs` (the "Set: …" msgid).

## Tests

All runs used Docker, CPU (`LFPHYS_NO_GPU=1`) and `--memory=6g`. The private server was `lf-pd-srv` on port 8673; the
shared 8479 was not used. The containers were stopped by name. These are the runs of 2026-11-13, while the other
processing agents were still editing their files.

- **`tests/test_i18n.py`: the parts of this response pass.**
  - Catalogue format, sorted keys and placeholders pass for every catalogue.
  - Static completeness passes: every framework msgid in the code is translated.
  - The dynamic per-world test passed for all worlds in the full run.
  - The conflict test fails on msgids outside the framework catalogue: world/world pairs (`Mass, u`, `Where it was
    computed`) and the engine's new `a step` («ступенька», a potential step), which clashes with the framework's
    computation step `a step` («шаг»). The clash was reported to the integrator with a proposed engine msgid,
    `a potential step`.
  - It will also fail on the four agreed shared entries until PR-B, PR-C1 and PR-C2 set the same text.
  - `test_no_function_of_the_visualizations_makes_T_a_local` is PR-A's new test and fails on PR-A's work in progress.
- **The framework tests touched by the msgid changes** (`test_server.py`, `test_sweeps.py`, `test_instruments.py`,
  `test_playground.py`, `test_carryover.py`): 65 passed; two asserts that quoted the old texts were updated.
  - `test_sweeps.py::test_the_budget_holds_inside_one_advance` quoted "by the measured cost …"; it was updated and now
    passes.
  - `test_sweeps.py::test_sweeps_through_the_server` passed on the rerun; its first failure was transient (a refused
    POST).
  - `test_server.py::test_run_list_follows_the_worlds_approximations` times out waiting for v08's first slice. It
    asserts no text and does not involve the changed msgids. It is left to the integrator's full run, since v08 is
    being edited by PR-C2.
- **Browser, `tests/browser/i18n_checks.mjs` 8673 en,ru** (all pages, all worlds): **all passed**, 87 checks, no page
  errors.
- **JS unit tests, `node --test player/js/tests/*.test.mjs`:** 2 of 3 pass. The failing one expects a plain space in
  «1 234 570» where the renderer now writes a narrow no-break space (PR-A's browser F11 work in `i18n.js`); it is not a
  catalogue text.
