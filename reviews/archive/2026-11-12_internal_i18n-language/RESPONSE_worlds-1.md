# Response to review i18n-language: worlds v01–v09 (PR-C1)

Processed 2026-11-13 by the worlds-1 agent of the integration (not the review's author). The part covers the catalogues
`visualizations/v01_light_travel … v09_thomas_3d/locales/ru.json` (and the new `locales/en.json` of v02, v07, v08,
v09), the English msgids in these worlds' `viz.py`, `engine/` and `web/view.js`, and both READMEs of each world. The
owner's decisions and the integrator's glossary of 2026-11-13 were applied to **every** entry of these nine catalogues,
not only to the read-through rows. Msgids were renamed in the code by the syntax tree (every string constant equal to
the old msgid in the world's Python, every literal in its JavaScript; literals spanning lines re-wrapped), with the
catalogue key moved in the same step and the placeholders of every translation checked against the msgid. Where a label
changed, the world's README.md / README.ru.md and the lines of the root README.md / README.ru.md that quote it were
updated.

Summary: **171 read-through rows in these worlds (R06 v01–v03, R07 v04–v07, R08 v08–v09): 164 fixed, 3 partly, 2 not
applied, 2 not in this part** (R08-033's rows for v10–v12 → PR-C2). Appendix C/D/E/F rows of these worlds: processed
(plural entries or count-neutral wording; three D rows and some C rows are false positives, reasons below).

| # | finding (v01–v09 part) | decision | verification |
|---|---|---|---|
| F1 | meaning reversed or lost | fixed: v02 «через них ничего не проходит» (and EN "passes through them") | catalogue diff |
| F2 | agreement errors | fixed: v07 «оба выбора … независимы от испускания пары»; v08 «…2D-модель среза … в сравнении с точной»; v09 «буст v′ — скорость w, видимая из u» | catalogue diff |
| F3 | names | fixed: v05 «закон Снеллиуса» (4 entries, README.ru, root README.ru); no other misspelt name in these worlds | grep |
| F4 | non-standard terms | fixed in every entry of these worlds: v05 title «Оптическая скамья» (also README.ru and the root README.ru), «показатель преломления»; v01 «статический наблюдатель/часы»; v02 «локализации GRW», «невозможность передачи сигнала», «аппроксимация»; v03 «коэффициент прохождения», «Надбарьерное отражение (E > V₀)», «интерпретация»; v04 «момент импульса», «последняя устойчивая круговая орбита», «падение на центр»; v06 «оператор Казимира», «с усреднением по спину»; v07 «световой конус будущего», «ожидаемое значение / предсказание»; v08 «экран с отверстием»; v09 «изопериметрическое неравенство / оценка», «разгон» | catalogue diff; READMEs |
| F5 | "against" → «против» | fixed by sense in all nine catalogues and Russian READMEs: «в сравнении с», «в зависимости от», «↔», «относительно»; «против» kept only for a real opposition of directions (v09 «Вид против направления оси z», the button «против z»; v01 «навстречу» for "against the light") | scan of the catalogues |
| F6 | "closed form" | fixed: «в замкнутом виде», «формула/выражение в замкнутом виде», «аналитическое решение» | scan |
| F7 | numerical error → «погрешность» | fixed (v02 7, v03, v04, v05 4, v07, v08, v09 entries); «ошибка» kept for a fault | scan |
| F8 | the playground's name | nothing in these worlds: no "playground"/"sandbox"/«плейграунд»/«песочница» in their texts or READMEs (v01's lowercase "laboratory" «лабораторная» is the lab frame, not the mode) | grep |
| F9 | inconsistent terms | fixed in these worlds: «2D/3D» in Russian (v02, v08 catalogues; v08, v09 README.ru), «удалённый наблюдатель», «выберите/задайте» instead of «возьмите», «рассчитан» for "computed", «запуск» for the run, «ППН» for PPN in Russian prose, «а. е.», «а. е. м.» | scans |
| F10 | Latin and English notation | fixed: decimal comma (v01 «r ≤ 1,5 rs»), «ревью R15» (v02), «(пункты V в STATUS)» (v01). Appendix D rows of v04 and v05 not applied: their «K» is the elliptic integral K(m) and the condition number K, not the kelvin | scans |
| F11 | placeholders carrying English, gender after a label | no English identifier inside a Russian sentence in these worlds (the arguments are `T` or symbols; "unknown action {name}" names a code identifier). Gender/case made independent of the label: v01 «объект «{obj}» … двигался бы», «у объекта «{obj}»», «от источника «{src}»»; v02 «элемент «{elem}» у щели … снят». No other gender agreement on a placeholder in v03–v09 | read of every entry with a text placeholder |
| F12 | plural and ordinal forms | fixed: plural entries keyed on `n` (Russian one/few/many/other; English one/other in new `en.json` of v02, v07, v08, v09) in v02, v03, v04, v05, v07, v08, v09, or count-neutral wording («частиц: {n:d}», «число мод на щель …»); arguments renamed to `n` in the code where needed; no "{k}th" ordinal in these worlds. Not applied where the count is a fixed constant whose form is right («30 пар», «из 10 щелей», «до 4096 точек») or the word is a unit («частиц/с», «фотон/с») | `test_i18n.py` (placeholders, plural forms) |
| F13 | English calques and spelling | fixed: v01 "at t = 0", "At rest", "A multiplier on c"; v03 "Interpretation" (6 msgids), k₀ − 3/(2σ) (the dimension slip; the code computes this); v04 "keeps running"; v05 "its fate is drawn", "with the expected values"; v07 "space-like / time-like separated from"; v08/v09 "the “X” preset/panel/check"; British spelling in the English READMEs (polarisation, polariser, analyser, spacetime) | grep |
| F14 | label length | count labels made explicit: «Число лучей во вспышке», «Число частиц в секунду (время мира)», «Число слоёв», «Число траекторий Бома в ансамбле», «Число вершин многоугольника», «Число повторов петли» | — |
| F15 | Russian style | applied: «рассчитан/рассчитывается» for «посчитан/считается», «при r = …», «Что, если» (v06 preset, README.ru, root README.ru) | scan |

Not applied, with reasons:
- **R06-037** (v02 «поток Ааронова–Бома» → capitalised): the text is one item of the set-up description joined by "; "
  (`v02_double_slit/engine/experiment.py`), whose siblings are lowercase; the English capital is only the proper name.
- **R08-036** (v09 «св. лет» → «св. г.»): the msgid "ly" is the framework's (`visualizations/locales/ru.json`, PR-D);
  v09 only repeats its value, and a different one would be a conflict. Passed to PR-D.
- **Partly:** R07-046/058 (EN "expectation" kept: it is the statistical expected value; RU «предсказание»/«ожидаемое»);
  R08-008 ("Energy flux" not adopted: the world calls j the energy current throughout); R08-030 («Погрешность
  округления» instead of the proposed «Ошибка округления», by the glossary).

Shared msgids decided jointly (PR-D, PR-B, the integrator): "Set-up: changes at once (the same as in the panel on the left)" is «Установка: меняется сразу (то же, что в панели слева)» in v02, v03, v05 and v07 (the framework's «Установка — меняется сразу»); "a potential step" «ступенька потенциала» (engine) in v03; "au" «а. е.» (framework) replaces v04's own "AU"; v09 uses the framework's plural "{x} yr". The badge «МОДИФИЦИРОВАННАЯ ФИЗИКА» is quoted in full in the v04 and v07 Russian READMEs.

## Rows, world by world



## v01_light_travel
- R06-001 applied: EN "A multiplier on c …", RU «Множитель при c …»; hint "raise the factor" → "raise the multiplier" for consistency.
- R06-002 applied: EN "without GR the body is given the horizon radius of a black hole of the same mass … (capped at the form's maximum …)", RU «радиус горизонта чёрной дыры той же массы … (ограничен максимумом формы, …)» (both variants).
- R06-003 applied (RU): «Угол поворота луча b = … rs (Рунге–Кутта в сравнении с квадратурой)»; EN kept ("swept", "RK against quadrature" is idiomatic English).
- R06-004 applied: «Эффект Доплера и красное смещение».
- R06-005 applied: EN "Einstein's (light exchange)".
- R06-006 applied: RU «Сколькими лучами рисуется фронт … события рассчитываются отдельно»; EN "computed separately".
- R06-007 applied: EN "the observer receives the images the run found, at the moments it found them"; RU matched, «Каждый луч рассчитывается».
- R06-008 applied: EN "when the light now reaching the observer left them", "projected onto the x axis".
- R06-009 applied: «наблюдатели со скоростями ±… м/с», «пешеходы со скоростью … м/с» (preset labels; root README.ru quotes the second).
- R06-010 applied: «световые конусы».
- R06-011 applied: «рассчитанных лучей», «рядом с эталонными значениями».
- R06-012 applied: "set the gravity to GR or “No gravity”".
- R06-013 applied: "Stands" → "At rest" / «Покоится».
- R06-014 applied: «статический наблюдатель», «статические часы», «локального статического наблюдателя» (4 entries).
- R06-015 applied: "at moment 0" → "at t = 0" (3 texts), "at the moment {tf}" → "at time {tf}", "at the moment of the flash" → "at the time of the flash"; labels "Time of the event on Andromeda (lab), days", "Time of the flash of the sources, ms"; RU «в момент t = 0».
- R06-016 applied: «рассчитанные».
- R06-017 applied: «невязка уравнения», «время полёта отсчитывается от события вспышки».
- R06-018 applied: EN "the time of flight is solved for starting from the flash event".
- R06-019 applied: «выражения в замкнутом виде нет», «для этого движения нет выражения в замкнутом виде», «эталон — радиальное время в замкнутом виде».
- R06-020 applied: EN "as its length → 0 the speed derived from it → c"; RU «скорость, найденная по нему, → c».
- R06-021 applied: EN "pedestrians cannot be faster … (in SR a body cannot reach the speed of light)"; RU «(в СТО тело не может достичь скорости света)». Test updated.
- R06-022 applied: "choose a slower observer or faster light".
- R06-023 applied: EN "weak-field limit 2rs/b", RU «в пределе слабого поля».
- R06-024 applied: «свободная камера».
- R06-025 applied: «произошла»; plus F11 case: «вспышка источника «{src}»».
- R06-026 applied: EN "dashed part of a line", RU «пунктирная часть линии».
- R06-027 applied: «(пункты V в STATUS)»; with appendix E / browser F9: «r ≤ 1,5 rs».

## v02_double_slit
- R06-028 applied: EN "A fit of the histogram to the computed slit functions …", "fit of the computed pattern to the slit basis …".
- R06-029 applied: «Фит» → «аппроксимация» (3 entries).
- R06-030 applied: «Ожидаемое распределение — оценка методом Монте-Карло (частиц: {n:d})» (also appendix C).
- R06-031 applied: «Ширина щели меньше 10 длин волн: …» (2 entries).
- R06-032 applied: EN "the individual slits (grid step …)"; RU count-neutral «(их число: {n:d})».
- R06-033 applied: «Экран-проводник/экран-проводник» → «Проводящий экран/проводящий экран» (9 entries) + «отражено/отражена … проводящим экраном».
- R06-034 applied: «читается/чтение» → «считывается/считывание» (8 entries).
- R06-035 applied: «щели шириной {a} мкм с периодом {d} мкм, экран на расстоянии {L} м» («с периодом» instead of the proposed «на расстоянии», which would repeat).
- R06-036 applied: GRW «удары» → «локализации» (4 entries; counter row «локализации GRW», label «локализаций GRW: {n}»). EN "hits" kept (standard GRW term).
- R06-037 not applied: the text is one item of the set-up description joined by "; " (engine/experiment.py:110) whose siblings are lowercase («щель 1: …», «анализатор …»); the English capital is the proper name only. «поток Ааронова–Бома» stays lowercase.
- R06-038 applied (error): «Невозможность передачи сигнала: … со считыванием детектора = без считывания».
- R06-039 applied: «ожидаемое распределение не рассчитывается».
- R06-040 applied: EN "… |γ₁₂| in the run's expected pattern", RU «в ожидаемой картине запуска».
- R06-041 applied: «базис с условием на ребре» (3 entries).
- R06-042 applied: EN "nothing passes through them", RU «через них ничего не проходит».
- R06-043 applied: «испускает», «пролетевшие через щели».
- R06-044 applied: «рассчитывается по правилу Борна с учётом их перекрытия».
- R06-045 applied: «картина разрешена недостаточно», «недостаточно разрешает полосы».
- R06-046 applied: «Интенсивность источника», «интенсивность источника должна быть больше 0».
- R06-047 applied: EN "Stokes parameters (…)", RU «Параметры Стокса (…)».
- R06-048 applied: «(в остальном он не используется)».
- R06-049 applied: EN "measured from the exit face" (2 texts) + README.md.
- R06-050 applied: «прошла через щели, но пролетела мимо экрана».
- R06-051 applied: «увеличьте λ зонда, ослабьте коллапс GRW, сузьте источник».
- R06-052 applied: «не рассчитывается (слишком затратно)».
- R06-053 applied: «считывание детектора меняло бы картину (передача сигнала)», «полнота базиса считывания».
- R06-054 applied: «неполяризованная».
- R06-055 applied: «(ревью R15)».

## v01 and v02: appendix C (plurals), D, E, F
- C v01 `a pulse train needs … from {lo} to {hi} pulses`: applied, count-neutral «а число импульсов — от {lo:d} до {hi:d}».
- C v02 Born-rule Monte Carlo «по {n} частицам»: applied (count-neutral, see R06-030).
- C v02 map cross-section «по {n} точкам»: applied (count-neutral, R06-032).
- C v02 dark counts «при {r:g} частиц/с»: not applied — «частиц/с» is a unit (like «1/с»), not an inflected count.
- C v02 Fullerenes «решётка из {n:d} щелей»: not applied — a preset label with n = 10 fixed; «из 10 щелей» is correct.
- C v02 `Screen grid: {p:.1f} points …`: not applied — .1f is always fractional («5,0 точки» is the correct form); wording fixed (R06-045).
- C v02 `the speed at which the pattern builds up (≈{n:d} particles per second)`: applied — plural forms ru {one,few,many,other} and a new v02 `locales/en.json` {one, other}.
- C v02 edge basis «от {a} до {b} функций»: applied, count-neutral «при числе функций на щель {a:d} → {b:d}».
- C v02 `difference vector − scalar (±{d} counts)`: applied, «(отсчёты: ±{d:.3g})».
- C v02 `the particles are shifted … a grid of {n:.3g} points`: not applied — genitive after «из» with a count ≥ 10⁶; correct.
- C v02 `the screen grid does not resolve the fringes ({p:.2g} points …)`: applied, «(точек на самую частую полосу: {p:.2g} < 8, …)».
- C v02 Richardson «по {a}, {b}, {c} модам … в {f1}–{f2} раза»: applied, «по числу мод на щель {a}, {b}, {c}; … оценка / истинная погрешность = {f1}–{f2}».
- C v02 dark counts per particle «{r:.3g} ложных отсчётов»: applied, «ложных отсчётов на одну частицу: {r:.3g}».
- C v02 `{how}; … (≈ {px:d} px)`: not applied — «пикс.» is an abbreviation; also «кривой ожидания» → «ожидаемой кривой».
- D (Latin K): no v01/v02 entries.
- E v01 «r ≤ 1.5 rs»: applied («1,5»).
- F v02 «Плоская (2-D) геометрия» → «(2D)»: applied.

## v01 and v02: grouped findings, glossary pass
- F1 (v02 «за ними ничего нет»): applied (R06-042).
- F4 v01/v02 rows (статический, удары GRW, сигнализация, фит): applied (above).
- F5 «против»: v01 «RK против квадратуры» and v02 «T_{pol} против предела Рэлея» → «в сравнении с»; v02 README.ru (6 places) too. v01 «навстречу» (Measuring c … against it) is the correct sense, kept.
- F6 closed form: v01 3 entries applied; READMEs.ru of both worlds («замкнутая форма/формула» → «в замкнутом виде», 9 places).
- F7 «ошибка» → «погрешность»: v02 7 entries applied (method error, truncation error, true error). README.ru «[ошибка в прежнем]» is the status tag (a mistake), kept.
- F9: «возьмите» → «выберите/задайте» (v01 scenario hint; v02 probe hint, EN "take" → "choose"/"set … to"); «а. е. м.» spelt like «а. е.».
- F10: no Latin K, no "review" left (R06-055), no Latin names in prose found.
- F11 (placeholders / gender / case), applied in v01: «объект «{obj}» … двигался бы» (was masculine for any {obj}, e.g. «Ракета»); «Частота у объекта «{obj}»», «до объекта «{obj}»», «от источника «{src}»» (4 arrival events + rod pass), «у объекта «{obj}» нет прибора», «вспышка источника «{src}»». v02: «элемент «{elem}» у щели … снят / не действует» (was «снят» for «пластинка», «заслонка»); counter table made one grammatical class: «темновые отсчёты», «с рассеянием фотона», «переходные (…)», «локализации GRW» (were «темновых», «рассеяли фотон», «переходных», «ударов GRW»). No English ids found inside Russian sentences in v01/v02 (the {p}, {elem}, {who}, {pol} args are T or symbols).
- F12: one plural entry added (above); no "{k}th" ordinals in v01/v02.
- F13 EN calques: "at moment" (R06-015), "take the scenario/probe" → "choose/set"; spelling: v02 README.md analyzer/polarization/polarizer → analyser/polarisation/polariser (msgids were already British).
- F14: «Лучей во вспышке» → «Число лучей во вспышке» (v01); «Частиц в секунду (время мира)» → «Число частиц в секунду (время мира)» (v02) and its two quotes in hints.
- F15: «посчитанные/считается» → «рассчитанные/рассчитывается» (v01 3, v02 4).
- «ожидание» (bare, for the expected distribution, R06-030/039 pattern): prose entries → «ожидаемое распределение» (9 entries); the short checkbox label «ожидание» kept.

## v01 and v02: browser review
- F7 (v01 «а.е.»): applied — label msgid "Distance to the Earth, AU" → "Distance to the Earth, au", RU «Расстояние до Земли, а. е.»; the canvas axes already use the framework msgid "au".
- F9 (v01 «(r ≤ 1.5 rs)»): applied.
- F8-type hyphen-minus: checked v01/v02 view.js — all canvas numbers go through fmt()/num()/t() (lenFmt uses t("{v:.3g} m")); nothing to fix.
- Others (F1–F4 framework, F6 v09/p01, F10 v05, F13, F15 p01/p02): not in these worlds.

## v01 and v02: code review
- F4–F15: no finding names v01 or v02 files (F5 lists p02/p03/p04/v05/v15; F8's shadowing list has no v01/v02 entry). Nothing to do.

## v03_quantum_1d
- R06-058 applied («коэффициент прохождения» in the thick-barrier preset, help text, reference note, sharp-edge refusal; EN "transmission coefficient" where T(E)); bar/detector label «прохождение» kept (a fraction, not T(E)).
- R06-057 applied: preset EN "Over-barrier reflection (E > V₀)", RU «Надбарьерное отражение (E > V₀)».
- R06-059 applied: "Fraction transmitted (particles: {n:d})" / «Доля прошедших (частиц: {n:d})».
- R06-061 applied: group "Interpretation of the outcome" / «Интерпретация исхода» (F13 EN calque too).
- R06-063 applied: «Копенгагенская: щелчок и коллапс».
- R06-066 applied: k₀ − 3/(2σ) in both languages (code computes k0 − 3/(2σ)), "an energy of at least".
- R06-062 applied: "reading" → "interpretation" in all 6 msgids (EN and RU), READMEs prose updated in both languages.
- R06-056 applied («прошедшей волны»).
- R06-060 applied: "Outcomes (particles: {n:d}); bars: fractions, dashes: probability from the wave. …".
- R06-064 applied, then aligned with the engine: the msgid "a potential step" is shared with the engine catalogue, whose text is «ступенька потенциала» (PR-B); v03 uses the same, so the merged catalogue has no conflict.
- R06-065 applied: "The computation was stopped early: the budget ran out." / «Счёт остановлен досрочно: исчерпан бюджет.»
- R06-067 applied + appendix C ({k:.3g} раза): arg renamed k → n, plural entry «в {n:.3g} раз/раза»; «ошибка схемы» → «погрешность схемы» (F7).
- R06-068 applied ("so the run has to wait for it", both variants).
- R06-069 applied + appendix C: «слишком затратен», «с вычислений», plural «сетка из {n:d} точки/точек».
- R06-070 applied ("starting points distributed as |ψ|²").
- Appendix C `the grid would need {n:d} points` applied (plural «из {n:d} точки/точек»).
- Glossary: «против» → «в сравнении с» (1); «посчитанной» → «рассчитанной»; «запуск считает» → «рассчитывает» (2); F14 count label «Число траекторий Бома в ансамбле»; R07-010 twin: «Установка: меняется сразу (то же, что в панели слева)», the text the integrator chose for all four worlds that use this msgid.

## v04_orbits
- R07-001 applied («в сравнении со временем удалённого наблюдателя»); README.ru intro likewise.
- R07-002 applied: «далёкий» → «удалённый» (5 entries) and in README.ru.
- R07-003 applied: «Момент импульса h …», «l (момент импульса, M·c)».
- R07-004 applied: «при r = …» (ghost note, push event, «при этом r»).
- R07-005 + R07-006 applied: EN list punctuated ("the marginally bound circular orbit 4M, the ISCO 6M (innermost stable circular orbit)"), RU «ISCO 6M (последняя устойчивая круговая орбита)».
- R07-007 applied (periapsis and apoapsis checks: «r в точке орбиты, где du/dφ = 0, ↔ …»).
- R07-008 applied: «падение на центр», «упало на центр»; the predicted kind "a plunge into the centre" already «падение на центр» — kept (predicted vs observed then read alike, which is the intent of the outcome check).
- R07-009, R07-010, R07-011, R07-012 applied.
- R07-013 applied (EN "an instability; the circular-orbit checks stop here", RU «проверки круговой орбиты»).
- R07-014 applied (EN "the roots of the cubic to 30 significant digits", RU «корни кубического уравнения с 30 значащими цифрами»).
- R07-015 applied («не налагаются»). R07-016 applied (ratio named; "closed-form expression" / «формула в замкнутом виде»). R07-017 applied («1,5 × третий член плюс численная погрешность»). R07-018 applied («в этой точке»).
- Appendix C (×2, «в {ratio} раз/раза»): args renamed ratio → n, plural entries.
- Appendix D (v04 periapsis-advance note): not applied — the «K» is the elliptic integral K(m), not kelvin (false positive).
- Browser F7 applied: v04's own msgid "AU" dropped; the Mercury semi-major-axis check uses the framework's "au" (ru «а. е.»); Mercury preset note "a = {a:.8g} au" / «а. е.».
- Glossary: «считается» → «рассчитывается»; «Замкнутые формулы ОТО» → «Формулы ОТО в замкнутом виде»; «ошибки округления» → «погрешности округления» (2); PPN in Russian prose → «ППН» (2; module names kept).
- MODIFIED PHYSICS: not a v04 msgid (framework "MODIFIED PHYSICS: " → PR-D).

## v06_qcd
- R07-036 applied: short labels «4/3·α_s(1/⟨r⟩) ↔ κ», «{a} ↔ {k}»; prose «в сравнении с измеренными» (3), «κ модели в сравнении с 4/3·α_s ядра».
- R07-037 applied: «Оператор Казимира C_A/C_F …», «цветовые операторы Казимира».
- R07-039 applied: «с усреднением по спину» (2).
- R07-038 applied: «Что, если …» (preset; README.ru quote updated), «(что, если)».
- R07-040, R07-041, R07-042, R07-043 applied.
- Glossary: «посчитанная» → «рассчитанная»; «не посчитано» → «не рассчитано»; «решение в замкнутой форме» → «аналитическое решение»; «Меняется сразу» → «Изменения применяются сразу»; count labels «петли», «число активных ароматов n_f» (F14).
- Code review F15 applied: the label "α_s(M_Z), the coupling constant" (the text after the comma is not a unit; empty in RU) → "Coupling constant α_s(M_Z)" / «Константа связи α_s(M_Z)». Its `{label:unit}` use is latent (playgrounds only); the reword removes it.
- Browser F13 applied: the energy-axis labels are centred on their ticks and kept inside the canvas (the last "10 TeV"/«10 ТэВ» was drawn from X−10 at the right edge and cut) — v06/web/view.js drawRun.
- Browser F9 (v06 «μ ≳ 1.5 ГэВ»): not in v06 — the text is the engine's ABOUT note (lfphys/lfphys/locales/ru.json, "the perturbative region μ ≳ 1.5 GeV…") → PR-B.

## v05_optics_bench
- R07-019 (F4) applied: title «Оптическая скамья: границы сред и покрытия», «Оптическая скамья: {structure}»; README.ru title already «Оптическая скамья»; root README.ru updated (3 rows).
- R07-020 (F3) applied: «закон Снеллиуса (закон преломления)», «косинусы по закону Снеллиуса» (4 entries) and in README.ru (4 places). Root README.ru «закон Снелла» → «закон Снеллиуса».
- R07-021 applied: «больше критического угла» (preset, tirnow), «При углах больше критического R = 1 …» (+ plural, below); «граница, за которой» → «граница, после которой» (2). Root README.ru preset quote updated.
- R07-022 applied: «ожидается …» (4), «с ожидаемыми значениями», «ожидаемые значения запуска», legend «ожидаемое значение запуска».
- R07-023 applied in EN and RU ("its fate is drawn by the Born rule" / «судьба … разыгрывается по правилу Борна») in the help and the summary; RU «Источник испускает».
- R07-024 applied: «граница без покрытия» (2 entries; README.ru 3 places).
- R07-025, R07-026, R07-027 applied («оптически менее плотная среда», «распространяющейся волны: волна неоднородная», «Интенсивность источника»).
- R07-030 applied: EN "The multilayer's spectrum …", RU «Спектр многослойной структуры очень изрезан: {n} точки/точек может не хватить …» (+ appendix C plural; arg m → n).
- R07-029 applied: «показатель преломления» in Film index ×2, High/Low index, and the metal's real part.
- R07-028, R07-031, R07-032 applied («Поверхностный плазмонный резонанс (схема Кречмана)» — root README.ru preset quote updated; «Брэгговское зеркало»; «(плечо — примерно за {s} с)»).
- R07-033 applied (EN "grazes along the face").
- R07-034 applied: EN "whisker: ±2σ", RU «планка — ±2σ».
- R07-035 applied («подкоренное выражение»).
- R07-001 (v05 part) applied: «в сравнении с вероятностями по правилу Борна».
- R07-010 twin: «Установка: меняется сразу (то же, что в панели слева)» (the integrator's choice for v02, v03, v05, v07).
- Appendix C: `{k:d} angles` applied (arg k → n, plural «угол/угла/углов»); `≈ {n:d} photons per second` applied (plural); `{m:d} points` applied (above); `{v:.4g} photons/s` → «фотон/с» NOT applied: a unit notation (like «имп./с»), not a counted noun.
- Appendix D (v05 evanescent note): not applied — «K» is the condition number K, not kelvin (false positive).
- Glossary: «оценки ошибки округления» → «погрешности» (4); «считаются/считает» → «рассчитываются/рассчитывает» (5); F14 count labels «Число слоёв», «переходные (выпущены до изменения)».
- Browser F10 applied: the legend under the photon bars is word-wrapped to the box width (`wrapWords`), and the bar rows leave room for its extra lines (v05/web/view.js drawCounters). The counts beside the bars now use fmt(…, "d") (grouping in RU).
- Code review F8 applied: locals named T renamed to Tr in `_at_structure` (viz.py) and `born_probs` (engine/bench.py), so a later T("…") there cannot raise UnboundLocalError.
- Code review F4/F5 (airy matching): switched to the engine's codes, see the code review's RESPONSE_worlds-1.md.

## v07_bell_test
- R07-054 (F2) applied: «оба выбора … независимы от испускания пары»; singular sibling «независим от испускания пары».
- R07-044 applied: «световые конусы будущего» (both entries).
- R07-045 applied with the review's merged F4 term: «Невозможность передачи сигнала» (3 check labels, summary, group reference); «маргинальная вероятность»; «против» → «в зависимости от».
- R07-050 applied.
- R07-055 / R07-048 / F13 applied, EN too: "space-like separated from", "time-like separated from"; RU «разделены пространственноподобным/времениподобным интервалом», «отделён … пространственноподобным интервалом».
- R07-056 applied («в конусе будущего/прошлого события испускания»).
- R07-057 applied: «в сравнении с границами», «относительно закона мира», «cτ ↔ 2L».
- R07-049 applied (+ sibling "it reverses in no inertial frame" → «не меняется на обратный», «система отсчёта»).
- R07-051 applied («что, если»). R07-059 applied.
- R07-046 / R07-058 applied in RU («предсказание», «ожидаемое |S|», «квантовое предсказание»); EN "expectation" kept (it is the statistical expected value; correct English) → partly.
- R07-047 applied: «вылет» → «испускание» everywhere; «выпускает/выпущено» → «испускает/испущено».
- R07-052, R07-053 applied.
- R07-060 applied, EN too: "the world lines of light are (not) at 45°" / «мировые линии света идут (не) под 45°».
- Appendix C v07: `{need:.0f} pairs` → plural entry keyed on n = round(need) (ru one/few/many/other + en.json one/other), viz.py passes n. The other four rows count NMIN = 30 / 2000 (constants): «30 пар», «меньше 30 пар», «≈2 000 пар» are correct → not applied (constant counts).
- Glossary: numerical «ошибка» → «погрешность» (S's error, E's errors); «замкнутая форма» → «формула в замкнутом виде» / «аналитическое решение»; «посчитанные» → «рассчитанные».
- Browser F8 applied: x ticks of E(Δ) through fmt(d, "d") (minus sign U+2212, both languages), web/view.js:352.
- Docs pass «фиксированная/фиксированный» applied: the bare msgid "fixed" (a station's setting shown on the canvas, «фиксированная» = настройка) next to the mode «фиксированный» was one English word with two genders; it is now "set by the mode “fixed”" / «задана режимом «фиксированный»», so the mode is always «фиксированный» (as in README.ru.md and the option «фиксированный: Алиса a, Боб b»).
- README.ru.md: glossary pass (против → в сравнении с / и; замкнутые формулы → формулы в замкнутом виде; «запрет сигнализации» → «невозможность передачи сигнала»; излучение → испускание where the pair's emission event; «МОДИФ. ФИЗИКА» → «МОДИФИЦИРОВАННАЯ ФИЗИКА»). README.md: British spelling outside code (polarisation, polariser, analyser), "spacetime", "space-like separated from".

## v08_wave_3d
- R08-001 (F2) applied: «…2D-модель среза … в сравнении с точной».
- R08-002 applied: every «против» → «в сравнении с» (energy current, P(z), slice field, fp32 picture).
- R08-003 (F4) applied: «заслонка» → «экран с отверстием» (summary, help, the scene object «Экран с отверстием (z = 0)», overview text).
- R08-004 applied: «2-D модель» → «2D-модель» (4 entries); README.ru.md «2-D/3-D» → «2D/3D».
- R08-005 applied: «считается/посчитан» → «рассчитывается/рассчитан» (6 entries + «Где рассчитано», «рассчитан на {device}»).
- R08-006 applied: «от пиковой амплитуды», «оценка погрешности … от пика», «доля пиковой амплитуды».
- R08-007 / R08-008 applied (EN too): "its error is given in the “APPROXIMATION” check", "the error of the approximation is given in the checks", "Energy current (direction and magnitude)", "below 1e-6 of their amplitude". "Energy flux" (proposed) not adopted: the world calls j the energy current throughout (labels, README) → partly.
- R08-009 applied (EN): names before the noun with “…” quotes: the “whole volume” mode, the “Scene layers” panel, the “Slice: position and tilt” panel, the “APPROXIMATION” check, the “{preset}” preset; «defaults» → “default” (the framework button's label).
- R08-010 applied: "The picture in fp32 compared with …", "(the picture)".
- R08-011 applied: "at depth z_max", "at depth z_near".
- R08-012 applied (EN + RU).
- R08-013 applied: «производные в замкнутом виде (… круглое отверстие на оси)»; EN "the closed-form Rayleigh–Sommerfeld solution on the axis" / «формула Рэлея–Зоммерфельда в замкнутом виде на оси»; P(z): "against the closed form from the spectrum" / «в сравнении с формулой в замкнутом виде по спектру».
- R08-014 applied («точек по каждой оси», both entries).
- R08-015 applied. R08-016 applied (EN + RU). R08-017 applied («амплитуды при z = 0», «осциллирует (явление Гиббса)»; «ошибка на z_max» → «погрешность при z_max»). R08-018 applied. R08-019 applied («W / E — переключение между ними», «перетаскивают», «рассчитывает»). R08-020 applied (EN + RU). R08-021 applied (EN "the engine's two methods", RU «два способа расчёта движка … при …»).
- Appendix C v08: «поле в {n:d} точках» and P(z) «на {n:d} глубинах» → plural entries (ru one/few/many/other, en.json one/other). «при окне до {m:d} точек»: m = M_MAX/2 = 4096 (constant power of two) → genitive plural correct, not applied.
- Glossary: «ошибка окна/эталона» → «погрешность»; "turned source" → "rotated source" (EN, R08-022 related).
- README.ru.md: glossary pass (против, замкнутая форма/формулы, ошибка → погрешность, «на ось», «3-D/2-D» → «3D/2D», «на z_max» → «при z_max»). README.md: "the engine's two methods".

## v09_thomas_3d
- R08-032 (F2) applied: «буст v′ — скорость w, видимая из u» + «в сравнении с площадью»; R08-038 applied («θ из матриц Лоренца в сравнении с …»).
- R08-023 (F4) applied: «импульс» (rocket burn) → «разгон» in every entry (summaries, crown/seam/ball presets, rapidity of the first burn, burns between turns, piece texts, error estimate, last burn, help); README.ru.md already said «разгон».
- R08-024 (F4) applied: «изопериметрическая граница» → «изопериметрическое неравенство» (equality cases) / «оценка» (the bound): summaries, help, checks, panel rows («оценка для плоских петель», «угол / оценка», «θ / оценка(L)»).
- R08-033 / R08-029 applied: «Число вершин многоугольника», «Число повторов петли», «число участков тяги» (R08-033's v10–v12 rows belong to PR-C2).
- R08-022 applied (EN): "are found to be rotated", "the loop its velocity traces" (+ README.md prose); RU «описывает».
- R08-025 applied (EN + RU): "opposite to the sense in which it is traversed" / «в направлении, противоположном обходу петли» (Now panel help, the accumulated-angle check, the Velocity-space help).
- R08-026 applied («Неплоскостность χ, °»). R08-027 applied (EN + RU).
- R08-030 applied with the glossary (numerical error → «погрешность»): EN "Round-off error: … (Lorentz 4×4 matrices and SL(2, C))", RU «Погрешность округления: … (матрицы Лоренца 4×4 и SL(2, C))» — the review's «Ошибка округления» replaced by «Погрешность» per the owner's glossary.
- R08-031 applied (EN + RU, preset label and its quote in the help): "a rotation by 2π" / «поворот на 2π».
- R08-034 applied («собственной системы отсчёта корабля»). R08-035 applied («по покоящимся часам»), together with browser F6.
- R08-028 applied («Винтовая линия», also the option and the helix reference; README.ru.md «спираль» → «винтовая линия»).
- R08-036 «св. лет» → «св. г.»: NOT applied — the msgid "ly" is the framework's (visualizations/locales/ru.json, PR-D); v09's catalogue only repeats it (same value), and a different value would be a conflict. Proposed to PR-D.
- R08-037 applied. R08-039 applied («оценка погрешности округления»). R08-040 applied (EN "this is how the picture is constructed"). R08-041 applied («Вид вдоль оси …»; the shared msgid "View along the x axis" now reads «Вид вдоль оси x» in v09 and v10 alike, «Вид против направления оси z/βz»; the short button "against z" «против z» kept: real opposition of directions).
- Appendix C v09: «{n:d} импульсов/точках» → plural entries keyed on n for the crown, the seam, the ball's seam, the seam reference, the field's and the slice's θ checks (ru one/few/many/other; en.json one/other); the two «лет» rows → browser F6 below.
- Browser F6 applied: the year read-outs are now the framework's plural "{x} yr" with n = the number as shown (5 significant digits): «1,4794 / 1,2379 года», «… года по покоящимся часам, … года по часам корабля»; msgids "{t:.5g} / {tau:.5g} yr" and "{T:.5g} yr by the clocks at rest, …" replaced by "{T} by the clocks at rest, {tau} by the craft's clock" (web/view.js `years()`).
- Browser F9 «4.23»: NOT applied — it is the equation number «(4.23)» of Osserman 1978 (the source's numbering, an identifier), not a decimal number (the language review's appendix E also excludes equation numbers).
- Glossary: «против» by sense (17 entries → «в сравнении с», «в направлении, противоположном обходу», «Вид против направления оси»); «замкнутая формула» → «выражение/формула в замкнутом виде» (EN "closed formula" → "closed form"); «ошибка» → «погрешность»; «считается» → «рассчитывается»; «точек на ось» → «точек по каждой оси».
- README.ru.md glossary pass (замкнутые формулы, изопериметрическая граница → оценка/неравенство, против, «округление» → «погрешность округления», спираль → винтовая линия, «w, видимая из u» → «скорость w, видимая из u»).

## Tests (2026-11-13, Docker `lfphys-viz`, CPU, `--memory=7g`; private server on port 8674)

- The worlds' own tests: v01–v07 and v09, **392 passed**; v08, **24 passed, 1 skipped** (the GPU test). The new tests of the code review's F5 mappings (v01 3, v05 7, v06 2) are among them.
- `tests/test_checkpoint.py` and `tests/test_restore.py` with `-k` for v01–v09: **all passed** (27).
- `tests/test_i18n.py`: **87 passed**. The first run reported one conflict, "View along the x axis" («Вид» in v09,
  «Взгляд» in v10); PR-C2 aligned v10 and the rerun passed.
- Browser (Playwright 1.58.2 Chromium): `i18n_checks.mjs` for v01–v09 in EN and RU, **62 checks, all passed**;
  `keyframes.mjs` for v01–v09, **all equal** in EN and in RU.
