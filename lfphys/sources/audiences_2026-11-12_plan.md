# lfphys: demonstrations for four audiences — a plan for approval item by item

Date: 2026-11-12. Written for `AGENTS.md` §3 rule 14 (four audiences, one audience per visualization) and rule 15
(registry → README → site), on the owner's direction of 2026-11-12 (quoted in `AGENTS.md` §1). Accepted parts are
item **P17** ("Audiences") of `lfphys/PLAN.md`.

**The owner's decisions (2026-11-12, answers to §8):**
- school demos on the public site: recordings over value grids («Записи по сетке значений»; §5.4 option a);
- order: «Школа AB1–AB3, потом RB1»;
- folder ids: «Префиксы s/u/r/p», with aliases for the old ids (§5.3 option A);
- school scope: «Только базовый ФРП сейчас» (the углублённый programme and IB-only topics later);
- not chosen, so not in the plan now: the benches p08 (mechanics) and p09 (circuits); showing the planar fuel bound of
  R07 in v09. Questions 5 (ranking), 6 (language of terms) and 8 (data sources) stay open and are settled at the
  batch discussions.

**The owner's decisions (2026-11-13, on the start-page design):**
- ids: the folder number is the plan id («Номер = id в плане»): today's university worlds take U31–U44 in §2.1 order,
  the research worlds R11–R13; S01–S45, U01–U30 and R01–R10 keep their ids as folder numbers; the old `vNN` ids stay
  valid as aliases (`visualizations/server/lfviz/registry.py` `ALIASES`);
- the free labs are named «Лаборатория» / "Laboratory" in every user-facing text (internal `playground` and `pNN` stay);
- the site's recordings are made in CI (GitHub Actions); the site is deployed only on the owner's go.

The mapping of today's worlds (2026-11-13):

| old id | new id | plan id | audience |
|---|---|---|---|
| `v01_light_travel` | `u31_light_travel` | U31 | University |
| `v02_double_slit` | `u32_double_slit` | U32 | University |
| `v03_quantum_1d` | `u33_quantum_1d` | U33 | University |
| `v04_orbits` | `u34_orbits` | U34 | University |
| `v05_optics_bench` | `u35_optics_bench` | U35 | University |
| `v06_qcd` | `u36_qcd` | U36 | University |
| `v07_bell_test` | `u37_bell_test` | U37 | University |
| `v08_wave_3d` | `u38_wave_3d` | U38 | University |
| `v10_fast_observer` | `u39_fast_observer` | U39 | University |
| `v13_hydrogen_3d` | `u40_hydrogen_3d` | U40 | University |
| `v14_quarkonium_3d` | `u41_quarkonium_3d` | U41 | University |
| `v15_kerr_shadow` | `u42_kerr_shadow` | U42 | University |
| `v16_optical_vortices` | `u43_optical_vortices` | U43 | University |
| `v17_mie_scattering` | `u44_mie_scattering` | U44 | University |
| `v09_thomas_3d` | `r11_thomas_3d` | R11 | Research |
| `v11_double_slit_2d` | `r12_double_slit_2d` | R12 | Research |
| `v12_arrival_times_2d` | `r13_arrival_times_2d` | R13 | Research |
| `p01_gravity` … `p04_fluids` | unchanged | — | Laboratories |

The rest of this plan is kept as written on 2026-11-12, with the old ids.

How to approve: every item has an id (S01…, U01…, R01…, PL…, F…, M…, AB…). The owner can answer per id
("S03 да", "R05 нет", "AB2 после RB1").

Sources used for this plan, and what they are good for:
- **[F79]** ФРП ООО «Физика» 7–9, базовый уровень (edsoo.ru, «Москва – 2025»):
  https://edsoo.ru/wp-content/uploads/2025/07/2025_ooo_frp_fizika-7-9_baz.pdf — fetched 2026-11-12. Every school anchor
  below quotes its section names and its lists «Демонстрации» and «Лабораторные работы и опыты» from this text.
- **[F1011]** ФРП СОО «Физика» 10–11, базовый уровень:
  https://edsoo.ru/wp-content/uploads/2025/07/2025_soo_frp_fizika_10_11_baz.pdf — fetched 2026-11-12; quoted sections,
  «Демонстрации», «Ученический эксперимент, лабораторные работы».
- **[AP]** College Board AP Physics 1, 2, C (2024–25 framework), unit numbers as verified in the curriculum research
  (`curriculum_2026-11-12_textbooks.md` Appendix A §9b; course pages apstudents.collegeboard.org/courses/ap-physics-1-algebra-based
  and siblings). **[IB]** IB DP Physics, first assessment 2025, topic codes A.1–E.5 (same file §9a; subject brief via
  the Internet Archive). **[AQA]** AQA A-level 7408, sections 3.1–3.13 (same file §9c).
- University anchors: the textbook tables of contents verified in `curriculum_2026-11-12_textbooks.md` Appendices B and C (HRW 12th,
  Young & Freedman 16th, OpenStax UP, Griffiths, Griffiths & Schroeter, Jackson, Goldstein, Hecht, Schroeder, Kittel,
  Савельев, Сивухин, Ландау–Лифшиц).
- Research prior art: three literature checks made for this plan, with every reference and the URL it was verified
  from: `priorart_2026-11-12_A_marking.md`, `priorart_2026-11-12_B_arrival_geometry.md`,
  `priorart_2026-11-12_C_relativity_gravity_qcd.md` (all in `lfphys/sources/`).
- The repository: `AGENTS.md`, `STATUS.md`, `lfphys/README.md` (modules, incl. those no world uses: `core.em.fdtd`,
  `core.em.charges`, `core.cosmology.flrw`, `core.quantum.compton`, `two_level`, `open_systems`, `jumps`),
  `lfphys/PLAN.md` (P15, P16, LB2, B9–B11), `visualizations/README.md`, `RULES.md` §1, §4, `server/lfviz/registry.py`.

Not verified, and so not used as an anchor (kept from the curriculum research's list):
- the chapter lists of the current Перышкин–Иванов 7–9 and Мякишев 10–11 textbooks (publisher pages behind a sign-in);
  the ФРП stands in for them, because the publisher states that the books follow it — that is an inference;
- the IB guide's sub-topic wording (only the public subject brief was read);
- the College Board "revisions 2024–25" page (403); the unit lists themselves are verified;
- Иродов «Основные законы» contents; ЛЛ V chapter titles in Russian; the Feynman Lectures chapter list;
- the лабораторные работы of the **углублённый** ФРП (only its section titles and hours were verified; this plan quotes
  the базовый lists only).

Status tags for results, as the project uses them: [useful] / [neutral] / [weakens] / [error in earlier].

---

## 0. Summary

| audience | today | in this plan | new visualizations | engine physics needed |
|---|---|---|---|---|
| School (S) | none of its own (7 worlds have one school preset each) | **45** demonstrations S01–S45 in ФРП order, cross-checked with AP/IB | 45 | 8 new modules or extensions (M1–M8) |
| University (U) | — | **14 existing worlds** + **30 new** U01–U30 = **44** | 30 | mostly existing modules (several unused today) + M1–M5 + P4, P3 subsets |
| Research (R) | — | **3 existing worlds** (v09, v11, v12) + **10 research set-ups** R01–R10 (8 new worlds, 2 as research presets/sweeps of v09 and v11); **5 candidates declined** after the prior-art check | 8 | extensions of the 2-D/3-D Schrödinger bench (time-dependent A and spin rotations, per-axis masses), a non-Kerr null-geodesic tracer |
| Playgrounds (PL) | p01–p04 | **9 benches** (p01–p04 + p05 optics and waves, p06 electricity and magnetism, p07 relativity from B9, + p08 mechanics, p09 circuits) | 5 | the same modules |

Main findings:
- [weakens] The present catalogue cannot be split into audiences as it is: no world exists for the first two thirds of
  any school programme (mechanics, heat, electricity, magnetism, optics of lenses). In the ФРП ООО базовый these take
  most of the 238 h (curriculum research §3.3). So the school set is almost entirely new, and it needs engine physics
  the engine does not have: classical mechanics of macroscopic bodies, circuits, electro- and magnetostatics,
  induction, geometric optics, macroscopic heat, nuclear decay.
- [useful] Today's worlds fit the university audience well (14 of 17). The 2-D double-slit bench (v11), the arrival
  times (v12) and Thomas–Wigner (v09) are the research audience's base.
- [weakens] The prior-art check removed or narrowed most of the obvious research ideas. Of fifteen candidates, none is
  "untouched": the best are narrow, concrete set-ups with no paper found (time-dependent Aharonov–Bohm flux in a real
  double slit; a delayed which-path mark and erasure for massive particles in a spatial double slit; Sorkin's parameter
  for matter waves with thick slits and wall tunnelling). "No paper found" means two or three targeted searches per
  item, not a survey: every novelty statement below is a hypothesis to recheck before anything is claimed in print.
- [useful] The registry already has `kind` and `section`; adding `audience`, curriculum anchors and prior-art fields
  to `VIZ` lets the README in both languages and the site be generated from it (rule 15).

---

## 1. School (S): 45 demonstrations by the curriculum

### 1.1 Principles

1. **Order and scope = ФРП.** The order follows the ФРП ООО 7–9 (7: structure of matter, motion and forces, pressure,
   energy; 8: heat, electricity and magnetism; 9: mechanics proper, oscillations and waves, EM waves, light, quantum
   phenomena) and continues with the ФРП СОО 10–11 (mechanics again at a higher level, MKT and thermodynamics,
   electrodynamics, oscillations and waves, optics, SR, quantum physics, astronomy). Where grades 7–9 and 10–11 treat
   the same topic, **one school visualization carries both levels as presets** («9 класс», «10 класс»); grades are one
   audience. Each item is checked against AP 1/2 and IB 2025 (and AQA where useful); topics that AP/IB add and the
   ФРП базовый lacks (torque and rotation in AP 1 U5–6, the Doppler effect in IB C.5) are covered inside the nearest
   item.
2. **The ordinary lab experiment, computed.** Each demonstration is the experiment of the ФРП's
   «Лабораторные работы и опыты» or «Демонстрации», done on a virtual bench. AGENTS rules 2–4 hold: the cart, the spring,
   the circuit, the rays are computed by the engine from their laws; the student's numbers come from the run, never
   from a formula; the closed form appears only in the final «Сверка с законом».
3. **Measurement as in the lab.** Instruments have a scale division (цена деления) and an error, as the ФРП 7 asks
   («Физические величины. Измерение … Погрешность измерений»); readings go into a table; a plot with a straight-line
   fit gives the law's constant (k, g, R, n, f) with its uncertainty.
4. **Simple interface** (the "school mode", §5.2): one scene, at most five controls per step, guided steps, the
   measurement table and one plot; no laws editor, devices, slice planes or 3-D gizmos.
5. **One visualization per demonstration**, even when it reuses an engine module that a university world also uses.

Legend for the "engine" column: **exists** = the module is in `lfphys` and tested; **ext** = an extension of an
existing module; **new M#** = a new module of §6.1. "Steps" = the guided steps in the school mode; "T/P" = the
measurement table's columns and the plot.

### 1.2 Mechanics (ФРП 7 «Движение и взаимодействие тел», «Работа и мощность. Энергия»; 9 «Механические явления»; 10 «Механика»; AP 1 U1–U6; IB A.1–A.4)

| id | demonstration | curriculum anchor | the lab experiment → what the student changes and measures | school interface | engine physics | reuse |
|---|---|---|---|---|---|---|
| S01 | Прямолинейное движение: равномерное и равноускоренное | [F79] 7 «Движение и взаимодействие тел», лаб. «Определение скорости равномерного движения (шарика в жидкости, модели электрического автомобиля…)», «Определение средней скорости скольжения бруска или шарика по наклонной плоскости»; 9 лаб. «Определение ускорения тела при равноускоренном движении по наклонной плоскости», «Проверка гипотезы: … пути относятся как ряд нечетных чисел…»; [F1011] 10 «Кинематика», лаб. «Исследование соотношения между путями, пройденными телом за последовательные равные промежутки времени…»; AP1 U1; IB A.1 | a ball on an incline with light gates; changes the angle and the start; measures times and distances → v(t), s(t), a, the odd-number rule | 3 controls (angle, gate positions, start); steps: uniform (horizontal track) → incline → odd-number test; T/P: t, s, v; s(t²) fit → a | new M1 (rolling ball on an incline; gates as probes) | M1 |
| S02 | Свободное падение и опыты Галилея | [F79] 9 «Ускорение … Свободное падение. Опыты Галилея»; [F1011] 10 демонстрации «Падение тел в воздухе и в разреженном пространстве», «Измерение ускорения свободного падения»; лаб. «Изучение движения шарика в вязкой жидкости»; AP1 U1; IB A.1 | Newton's tube (feather and coin with and without air), strobe photo of a falling ball, a ball in oil reaching terminal speed; changes air pressure, mass, shape, liquid; measures g and the terminal speed | 3 controls; steps: vacuum → air → oil; T/P: t, h; h(t²) → g; v(t) → v_term | new M1 (linear and quadratic drag; Stokes drag with the fluid's viscosity data) | M1; fluid data in `core.data` (water, air exist) |
| S03 | Движение тела, брошенного горизонтально и под углом | [F79] 7 лаб. «Проведение исследования по проверке гипотезы: дальность полета шарика, пущенного горизонтально, тем больше, чем больше высота пуска»; [F1011] 10 демонстрация «Наблюдение движения тела, брошенного под углом к горизонту и горизонтально», лаб. «Изучение движения тела, брошенного горизонтально»; AP1 U1; IB A.1; AQA 3.4.1 (projectiles) | a launcher on a table; changes height, speed, angle, air drag on/off; measures range and flight time; finds the 45° maximum and how drag shifts it | 3 controls; steps: horizontal launch vs height → angle scan → drag; T/P: θ, v₀, L, t; L(θ) | new M1 | M1 |
| S04 | Движение по окружности | [F79] 9 «Равномерное движение по окружности. Период и частота обращения. Линейная и угловая скорости. Центростремительное ускорение»; [F1011] 10 демонстрация «Направление скорости при движении по окружности»; AP1 U2 (circular motion inside forces), IB A.2 | a puck on a string on a table, a conical pendulum; changes radius, period, mass; measures the string's tension; cutting the string shows the tangent velocity | 3 controls; steps: T vs v at fixed r → T vs r → cut the string; T/P: v², r, F; F(v²/r) → m | new M1 (string as a constraint with its tension) | M1 |
| S05 | Законы Ньютона | [F79] 9 «Первый закон Ньютона. Второй … Третий…», демонстрации «Зависимость ускорения тела от массы тела и действующей на него силы», «Наблюдение равенства сил при взаимодействии тел», «Изменение веса тела при ускоренном движении»; [F1011] 10 «Динамика», демонстрации «Второй закон Ньютона», «Невесомость. Вес тела при ускоренном подъеме и падении»; AP1 U2; IB A.2 | a cart pulled by a hanging load over a pulley (Atwood); two carts pushing apart with force sensors; a scale in a lift; changes mass and force; measures a, F, the scale reading | 3 controls; steps: a(F) at fixed m → a(1/m) → action–reaction → lift; T/P: F, m, a; a(F) → 1/m | new M1 (strings, pulleys, normal forces) | M1 |
| S06 | Сила упругости, закон Гука, вес и невесомость | [F79] 7 лаб. «Опыты, демонстрирующие зависимость растяжения (деформации) пружины от приложенной силы»; 9 лаб. «Определение жесткости пружины»; [F1011] 10 лаб. «Исследование зависимости сил упругости, возникающих в пружине и резиновом образце, от их деформации»; AQA 3.4.2 (Young modulus) | weights on a spring and on a rubber band; changes the load; measures extension; springs in series and parallel; the rubber's non-linearity and hysteresis | 2 controls; steps: spring → two springs → rubber; T/P: F, x; F(x) → k | new M1 (springs; rubber as a stated model with hysteresis in `theories.models`) | M1 |
| S07 | Сила трения; брусок на наклонной плоскости | [F79] 7 лаб. «Опыты, демонстрирующие зависимость силы трения скольжения от веса тела и характера соприкасающихся поверхностей»; 9 лаб. «Исследование зависимости силы трения скольжения от силы нормального давления», «Определение коэффициента трения скольжения»; [F1011] 10 демонстрация «Сравнение сил трения покоя, качения и скольжения», лаб. «Изучение движения бруска по наклонной плоскости»; AP1 U2 | a block pulled by a dynamometer, then on a tilting plane; changes load, surface pair, angle; measures the force at the start of sliding and while sliding; the angle of sliding gives μ_s | 3 controls; steps: F(N) → static vs kinetic → incline angle; T/P: N, F; F(N) → μ | new M1 (Coulomb friction with static/kinetic coefficients; surface pairs as data with sources) | M1 |
| S08 | Рычаг, блоки, наклонная плоскость; момент силы | [F79] 7 «Простые механизмы: рычаг, блок, наклонная плоскость… КПД простых механизмов», лаб. «Исследование условий равновесия рычага», «Измерение КПД наклонной плоскости»; 9 «Момент силы. Центр тяжести», лаб. «Определение работы силы упругости при подъеме груза с использованием неподвижного и подвижного блоков»; [F1011] 10 лаб. «Исследование условий равновесия твердого тела, имеющего ось вращения»; AP1 U5–U6; IB A.4 (HL) | a lever with hooks, pulleys, an inclined plane with a cart; changes loads and arms; measures forces, work in and out, efficiency; the "golden rule" | 3 controls; steps: lever balance → pulleys → incline efficiency; T/P: F₁l₁, F₂l₂; A_useful, A_total, η | new M1 (rigid bodies on a fixed axis; friction in the incline) | M1 |
| S09 | Работа, кинетическая и потенциальная энергия, закон сохранения | [F79] 7 «Механическая энергия. Кинетическая и потенциальная энергия… Закон сохранения энергии в механике», лаб. «Изучение закона сохранения механической энергии», «Определение работы силы трения при равномерном движении тела по горизонтальной поверхности»; 9 демонстрации «Сохранение механической энергии при свободном падении», «… при движении тела под действием пружины»; [F1011] 10 лаб. «Исследование связи работы силы с изменением механической энергии тела на примере растяжения резинового жгута»; AP1 U3; IB A.3 | a cart on a track with hills and a loop, a spring launcher, friction on/off; changes height, spring compression, friction; measures speed at gates; bars E_k, E_p, heat | 3 controls; steps: no friction → friction (heat bar) → spring launcher; T/P: h, v, E_k, E_p, Q; v²(h) → 2g | new M1 (track as a constraint curve; energy bookkeeping as a running check) | M1 |
| S10 | Импульс, столкновения, реактивное движение | [F79] 9 «Импульс тела… Закон сохранения импульса. Реактивное движение», демонстрации «Сохранение импульса при неупругом взаимодействии», «… при абсолютно упругом взаимодействии», «Наблюдение реактивного движения»; [F1011] 10 «Упругие и неупругие столкновения», лаб. «Изучение абсолютно неупругого удара с помощью двух одинаковых нитяных маятников»; AP1 U4; IB A.2 | air-track gliders with springs or clay, two pendulums, a balloon rocket; changes masses, speeds, the restitution; measures speeds before and after, p and E_k | 3 controls; steps: inelastic → elastic → 2-D pucks → rocket; T/P: m, v, p, E_k before/after | new M1 (impacts with a restitution coefficient; variable-mass body for the rocket) | M1; `core.md.hard` collisions as the second route for elastic disks |
| S11 | Всемирное тяготение, спутники, первая космическая скорость | [F79] 9 «Сила тяжести и закон всемирного тяготения… Движение планет вокруг Солнца. Первая космическая скорость. Невесомость и перегрузки»; [F1011] 10 «Закон всемирного тяготения… Первая космическая скорость», «движение искусственных спутников»; IB D.1; AP1 U2 | Newton's cannon on a mountain; changes launch speed and height; measures the orbit's period; finds v₁ and the escape speed; g on other planets | 2 controls; steps: speeds → circular orbit → period vs radius (Kepler's third law); T/P: r, T; T²(r³) | exists `core.gravity.nbody` | nbody (school scene and units; separate from p01) |
| S12 | Маятник и груз на пружине; затухание, вынужденные колебания, резонанс | [F79] 9 «Механические колебания и волны», лаб. «Исследование зависимости периода колебаний подвешенного к нити груза от длины нити», «… пружинного маятника от массы груза», «Проверка независимости периода … от массы груза», «Измерение ускорения свободного падения», демонстрация «Наблюдение вынужденных колебаний и резонанса»; [F1011] 11 лаб. «Исследование зависимости периода малых колебаний груза на нити от длины нити и массы груза», демонстрации «Наблюдение затухающих колебаний», «Наблюдение резонанса»; AP1 U7; IB C.1 | a pendulum and a spring oscillator with a stopwatch; changes length, mass, amplitude (large amplitudes: the period grows), damping, drive frequency; measures T and the resonance curve | 3 controls; steps: T(l) → T(m) → large amplitude → drive; T/P: l, T; T²(l) → g; amplitude(f) | new M1 (the exact large-amplitude period through `core.elliptic` K(m) as the reference) | M1, `core.elliptic` |

### 1.3 Waves and sound (ФРП 9 «Механические колебания и волны»; 11 «Механические и электромагнитные волны»; AP 2 U14; IB C.2–C.5)

| id | demonstration | curriculum anchor | experiment → change / measure | interface | engine | reuse |
|---|---|---|---|---|---|---|
| S13 | Механические волны: шнур и волновая ванна | [F79] 9 «Механические волны… Продольные и поперечные волны. Длина волны и скорость ее распространения», демонстрация «Распространение продольных и поперечных волн (на модели)»; [F1011] 11 «Интерференция и дифракция механических волн», демонстрации «Наблюдение отражения и преломления механических волн», «Наблюдение интерференции и дифракции механических волн»; IB C.2–C.4; AP2 U14 | a rope with a vibrator (standing waves), a ripple tank with one or two dippers, a barrier with a gap, a shallow region (refraction); changes frequency, gap, depth; measures λ, v = λf, the node lines | 3 controls; steps: travelling wave → standing waves → two sources → gap; T/P: f, λ; λ(1/f) → v | new M6 (1-D string; 2-D scalar waves) | M6 (built on `core.em.fdtd`'s Yee update for the 2-D scalar case) |
| S14 | Звук: высота, громкость, резонанс, эффект Доплера | [F79] 9 «Звук. Громкость звука и высота тона. Отражение звука. Инфразвук и ультразвук», демонстрации «Наблюдение зависимости высоты звука от частоты», «Акустический резонанс»; [F1011] 11 «Звук. Скорость звука. Громкость звука. Высота тона. Тембр звука», «Звуковой резонанс»; IB C.5 (Doppler); AP2 U14 | a tuning fork and a resonance tube (closed pipe), an oscilloscope of a microphone, a moving siren; changes the water level in the tube, the source's speed; measures the resonance lengths (→ speed of sound), the shifted frequency | 3 controls; steps: pitch and loudness → resonance tube → moving source; T/P: L₁, L₂, λ/2; f′(v_s) | new M6 (1-D acoustic tube; 2-D acoustics with a moving source) | M6; audio output optional (display only) |

### 1.4 Pressure and fluids (ФРП 7 «Давление твердых тел, жидкостей и газов»; AP 1 U8)

| id | demonstration | curriculum anchor | experiment → change / measure | interface | engine | reuse |
|---|---|---|---|---|---|---|
| S15 | Давление в жидкости и газе; Паскаль, сообщающиеся сосуды, гидравлический пресс, атмосферное давление | [F79] 7 «Давление… Закон Паскаля… Зависимость давления жидкости от глубины. Гидростатический парадокс. Сообщающиеся сосуды. Гидравлические механизмы», «Опыт Торричелли», демонстрации «Передача давления жидкостью и газом», «Сообщающиеся сосуды», «Гидравлический пресс», «Проявление действия атмосферного давления»; AP1 U8 | a manometer probe in a tank, connected vessels with two liquids, a press, Torricelli's tube; changes depth, liquid, piston areas, altitude; measures p(h), forces | 3 controls; steps: p(h) → vessels → press → Torricelli; T/P: h, p; p(h) → ρg | new M1 ext (hydrostatics of a resting liquid; the standard atmosphere's p(h) as data, U.S. Standard Atmosphere 1976 exists in `core.fluids.lbm` data) | M1, data |
| S16 | Закон Архимеда; плавание тел | [F79] 7 «Выталкивающая (архимедова) сила. Закон Архимеда. Плавание тел. Воздухоплавание», лаб. «Исследование зависимости веса тела в воде от объема погруженной в жидкость части тела», «Определение выталкивающей силы…», «Проверка независимости выталкивающей силы … от массы тела», «Опыты, демонстрирующие зависимость выталкивающей силы … от объема погруженной … части тела и от плотности жидкости», «Конструирование ареометра или конструирование лодки и определение ее грузоподъемности»; AP1 U8 | a dynamometer with bodies lowered into water, oil, brine; a boat loaded with weights; changes immersion depth, body, liquid, load; measures the weight in liquid and the buoyant force; the boat's capacity | 3 controls; steps: F_A(V_sub) → F_A(ρ) → independence of mass → boat; T/P: V, ρ, F_A | new M1 ext (buoyancy as the integral of the computed pressure over the wetted surface; floating rigid bodies with damping) | M1 |

### 1.5 Heat and molecular physics (ФРП 7 «Первоначальные сведения о строении вещества»; 8 «Тепловые явления»; 10 «Молекулярная физика и термодинамика»; AP 2 U9; IB B.1–B.4)

| id | demonstration | curriculum anchor | experiment → change / measure | interface | engine | reuse |
|---|---|---|---|---|---|---|
| S17 | Броуновское движение и диффузия | [F79] 7 «Броуновское движение, диффузия», демонстрации «Наблюдение броуновского движения», «Наблюдение диффузии»; 8 the same демонстрации; [F1011] 10 демонстрации «Модель броуновского движения», «Модель опыта Штерна», «Опыты по диффузии жидкостей и газов» | a heavy particle among gas atoms; two gases mixing; Stern's rotating drums; changes temperature and mass; measures the mean square displacement and the speed of the atoms | 3 controls; steps: Brownian → diffusion vs T → Stern; T/P: t, ⟨r²⟩; ⟨r²⟩(t) | exists `core.md` | core.md (a school scene; not p03) |
| S18 | Теплопередача, количество теплоты, уравнение теплового баланса | [F79] 8 «Виды теплопередачи: теплопроводность, конвекция, излучение. Количество теплоты. Удельная теплоемкость… Уравнение теплового баланса», лаб. «Исследование явления теплообмена при смешивании холодной и горячей воды», «Определение количества теплоты, полученного водой при теплообмене с нагретым металлическим цилиндром», «Определение удельной теплоемкости вещества»; [F1011] 10 лаб. «Измерение удельной теплоемкости»; IB B.1 | a calorimeter, a heated cylinder, rods of different metals between hot and cold, a cooling cup; changes masses, temperatures, materials; measures the final temperature and the cooling curve | 3 controls; steps: mixing → metal cylinder (c) → conduction in rods → cooling; T/P: m, t, Q; t(τ) | new M7 (lumped calorimetry, 1-D conduction, Newton's cooling and radiation; material data with sources) | M7 |
| S19 | Плавление, кипение, испарение, влажность | [F79] 8 «Плавление и отвердевание… Удельная теплота плавления. Парообразование… Кипение… Влажность воздуха», лаб. «Определение удельной теплоты плавления льда», «Исследование процесса испарения», «Определение относительной влажности воздуха», демонстрации «Наблюдение кипения», «Наблюдение постоянства температуры при плавлении»; [F1011] 10 «Агрегатные состояния вещества. Фазовые переходы», лаб. «Измерение относительной влажности воздуха» | ice heated to steam on a burner of known power; a psychrometer; changes power and mass; measures the plateaux and latent heats; reads humidity | 3 controls; steps: heating curve → latent heat of ice → psychrometer; T/P: τ, t; plateau length → λ | new M7 (enthalpy method for phase change; water's data from IAPWS, already a source of `core.data`) + an atom view from `core.md` (melting of a crystal) as a second panel | M7, core.md |
| S20 | Газовые законы: изотерма, изобара, изохора | [F79] 8 демонстрация «Изменение давления газа при изменении объема и нагревании или охлаждении», лаб. «Опыты, демонстрирующие зависимость давления воздуха от его объема и нагревания или охлаждения»; [F1011] 10 «Газовые законы. Уравнение Менделеева–Клапейрона… Изопроцессы», лаб. «Исследование зависимости между параметрами состояния разреженного газа», «Определение массы воздуха в классной комнате…»; IB B.3; AP2 U9 | a cylinder with a piston, a manometer and a thermometer, the gas computed from atoms; changes V or T with the other fixed; measures p | 2 controls; steps: Boyle → Charles → Gay-Lussac; T/P: V, p, T; p(1/V), V(T) | exists `core.md` (piston, thermal walls, counters) | core.md |
| S21 | Первый закон термодинамики и тепловые машины | [F79] 8 «Принципы работы тепловых двигателей. КПД теплового двигателя»; [F1011] 10 «Первый закон термодинамики… Графическая интерпретация работы газа… Цикл Карно и его коэффициент полезного действия», демонстрация «Опыт по адиабатному расширению воздуха (опыт с воздушным огнивом)»; IB B.4 (HL); AP2 U9 | a gas under a piston taken through a cycle with a hot and a cold bath; a fast compression (fire piston); changes the bath temperatures and the cycle; measures Q, A, η on a P–V diagram | 3 controls; steps: adiabatic jump → isotherm → full cycle; T/P: Q₁, Q₂, A, η; P–V loop | exists `core.md` + ext (baths switched by a script inside a cycle; a P–V plot — gap "C" of the curriculum research) | core.md |

### 1.6 Electricity and magnetism (ФРП 8 «Электрические и магнитные явления»; 9 «Электромагнитное поле и электромагнитные волны»; 10 «Электродинамика»; 11 «Магнитное поле. Электромагнитная индукция», «Колебания и волны»; AP 2 U10–U12; IB B.5, D.2–D.4)

| id | demonstration | curriculum anchor | experiment → change / measure | interface | engine | reuse |
|---|---|---|---|---|---|---|
| S22 | Электрические заряды и поле | [F79] 8 «Электризация тел… Закон Кулона… Электрическое поле… Принцип суперпозиции», демонстрации «Устройство и действие электроскопа», «Электростатическая индукция», «Моделирование силовых линий электрического поля», лаб. «Опыты по наблюдению электризации тел индукцией и при соприкосновении», «Исследование действия электрического поля на проводники и диэлектрики»; [F1011] 10 «Закон Кулона… Линии напряженности… Потенциал», демонстрации «Электрическое поле заряженных тел», «Проводники в электростатическом поле», «Электростатическая защита»; AP2 U10; IB D.2 | charged balls on threads, an electroscope, a probe of the field; changes charges and distances; measures the force (Coulomb's 1/r²), field lines, the shielding inside a metal box | 3 controls; steps: F(r) → field lines of 1, 2 charges → conductor and Faraday cage; T/P: r, F; F(1/r²) | exists `core.em.charges` (points) + new M3 (conductors) | charges, M3 |
| S23 | Конденсатор | [F1011] 10 «Электроемкость. Конденсатор. Электроемкость плоского конденсатора. Энергия заряженного конденсатора», демонстрации «Зависимость электроемкости плоского конденсатора от площади пластин, расстояния между ними и диэлектрической проницаемости», «Энергия заряженного конденсатора», лаб. «Измерение электроемкости конденсатора»; AP C U10; AQA 3.7.4 | a plate capacitor with movable plates and a dielectric slab, an electrometer; charging through a resistor; changes area, gap, dielectric; measures C and the RC curve | 3 controls; steps: C(S) → C(1/d) → dielectric → charging; T/P: S, d, C; C(S/d) → ε₀ | new M3 (Laplace with conductors and dielectrics, capacitance incl. fringing) + M2 (RC) | M3, M2 |
| S24 | Сила тока, напряжение, закон Ома, сопротивление проводника | [F79] 8 «Сила тока. Электрическое напряжение. Сопротивление проводника. Удельное сопротивление… Закон Ома для участка цепи», лаб. «Сборка и проверка работы электрической цепи постоянного тока», «Измерение и регулирование силы тока», «… напряжения», «Исследование зависимости силы тока, идущего через резистор, от сопротивления резистора и напряжения на резисторе», «Опыты, демонстрирующие зависимость электрического сопротивления проводника от его длины, площади поперечного сечения и материала»; [F1011] 10 «Постоянный электрический ток»; AP2 U11; IB B.5 | a breadboard: source, rheostat, wires of different length, cross-section and metal, ammeter, voltmeter (with their own resistances); measures I(U), R(l, S, ρ) | 4 controls; steps: assemble → I(U) → R(l) → R(S), material; T/P: U, I; I(U) → R | new M2 (modified nodal analysis; meters with internal resistance; wire resistivity data with sources) | M2 |
| S25 | Последовательное, параллельное и смешанное соединение | [F79] 8 лаб. «Проверка правила сложения напряжений при последовательном соединении двух резисторов», «Проверка правила для силы тока при параллельном соединении резисторов»; [F1011] 10 «Последовательное, параллельное, смешанное соединение», лаб. «Изучение смешанного соединения резисторов»; AP2 U11 | two and three resistors connected in different ways; measures currents and voltages at every element | 3 controls; steps: series → parallel → mixed; T/P: U₁, U₂, U, I₁, I₂, I | new M2 | M2 |
| S26 | Работа и мощность тока, закон Джоуля–Ленца, лампа, нагреватель | [F79] 8 «Работа и мощность электрического тока. Закон Джоуля–Ленца… Короткое замыкание», лаб. «Определение работы электрического тока…», «Определение мощности…», «Исследование зависимости силы тока, идущего через лампочку, от напряжения на ней», «Определение КПД нагревателя»; [F1011] 10 «Закон Джоуля–Ленца. Мощность электрического тока» | a resistor in water (calorimeter), a lamp; changes voltage; measures P, Q, the lamp's non-linear I(U), the heater's efficiency | 3 controls; steps: Q = I²Rt → lamp I(U) → kettle efficiency; T/P: U, I, P; I(U) of the lamp | new M2 + M7 (the heat goes to the calorimeter); the lamp's filament R(T) as a model with tungsten data | M2, M7 |
| S27 | ЭДС и внутреннее сопротивление; закон Ома для полной цепи | [F1011] 10 «Электродвижущая сила и внутреннее сопротивление источника тока. Закон Ома для полной (замкнутой) электрической цепи. Короткое замыкание», демонстрация «Прямое измерение электродвижущей силы. Короткое замыкание гальванического элемента и оценка внутреннего сопротивления», лаб. «Измерение электродвижущей силы источника тока и его внутреннего сопротивления»; AQA 3.5.1; IB B.5 | a battery with a rheostat; changes the load; measures U(I) | 2 controls; steps: U(I) → short circuit → power to the load; T/P: I, U; U(I) → ℰ, r | new M2 | M2 |
| S28 | Ток в различных средах: металлы, полупроводниковый диод, электролит | [F1011] 10 «Токи в различных средах… Зависимость сопротивления металлов от температуры… Свойства p–n-перехода… Электролиз», демонстрации «Зависимость сопротивления металлов от температуры», «Односторонняя проводимость диода», «Проводимость электролитов», лаб. «Наблюдение электролиза»; [F79] 8 «Электрический ток в жидкостях и газах» | a metal wire heated, a diode, an electrolytic cell; changes T, polarity, current; measures R(T), the diode's I(U), the deposited mass (Faraday's law) | 3 controls; steps: R(T) → diode → electrolysis; T/P: t, R; I(U); m(It) | new M2 ext (the diode as the Shockley model in `theories.models`; Faraday's law of electrolysis) | M2 |
| S29 | Магнитное поле магнитов и токов; опыт Эрстеда; электромагнит | [F79] 8 «Постоянные магниты… Магнитное поле. Магнитное поле Земли… Опыт Эрстеда. Магнитное поле электрического тока», демонстрации «Моделирование магнитных полей постоянных магнитов», «Опыт Эрстеда», «Магнитное поле тока. Электромагнит», лаб. «Исследование магнитного взаимодействия постоянных магнитов», «Изучение магнитного поля постоянных магнитов при их объединении и разделении», «Исследование действия электрического тока на магнитную стрелку», «Опыты, демонстрирующие зависимость силы взаимодействия катушки с током и магнита от силы тока и направления тока в катушке»; [F1011] 11 «Магнитное поле проводника с током… катушки с током», лаб. «Изучение магнитного поля катушки с током»; AP2 U12; IB D.2 | bar magnets with iron filings and a compass, a wire through a card, a coil; changes current and turns; measures B with a probe; field lines | 3 controls; steps: magnets → wire (Oersted) → coil, B(I, n); T/P: I, B; B(I) | new M3 (Biot–Savart; permanent magnets as magnetized bodies) | M3 |
| S30 | Сила Ампера, электродвигатель, сила Лоренца | [F79] 8 «Действие магнитного поля на проводник с током. Электродвигатель постоянного тока», лаб. «Изучение действия магнитного поля на проводник с током», «Конструирование и изучение работы электродвигателя», «Измерение КПД электродвигательной установки»; [F1011] 11 «Сила Ампера… Сила Лоренца… Движение заряженной частицы в однородном магнитном поле», демонстрации «Отклонение электронного пучка магнитным полем», «Взаимодействие двух проводников с током», лаб. «Исследование действия постоянного магнита на рамку с током»; AP2 U12; IB D.3 | a swinging wire between magnet poles, a loop on an axle (motor), two parallel wires, an electron beam tube; changes current, field, direction; measures force and torque, the beam's radius | 3 controls; steps: F(I, B, l) → motor → beam; T/P: I, F; F(I) → Bl | new M3 (forces and torques on currents) + exists `core.spin_transport` (charge in a uniform field) | M3, spin_transport |
| S31 | Электромагнитная индукция; правило Ленца; генератор | [F79] 8 «Опыты Фарадея. Явление электромагнитной индукции. Правило Ленца. Электрогенератор», лаб. «Опыты по исследованию явления электромагнитной индукции: исследование изменений значения и направления индукционного тока»; [F1011] 11 «Закон электромагнитной индукции Фарадея. Вихревое электрическое поле… Правило Ленца. Индуктивность. Явление самоиндукции», демонстрации «Зависимость электродвижущей силы индукции от скорости изменения магнитного потока», «Явление самоиндукции», лаб. «Исследование явления электромагнитной индукции»; AP2 U12; IB D.4 (HL) | a magnet pushed into a coil with a galvanometer, a rod on rails, a rotating loop, a ring jumping off a coil; changes speed, direction, turns; measures the EMF and its sign | 3 controls; steps: magnet in coil → speed → Lenz (ring) → generator; T/P: v, ℰ; ℰ(dΦ/dt) | new M5 (quasi-static induction coupled with M2 and the mechanics of M1) | M5, M2, M1, M3 |
| S32 | Колебательный контур, переменный ток, резонанс, трансформатор | [F1011] 11 «Колебательный контур… Формула Томсона… Переменный ток… Трансформатор», демонстрации «Свободные электромагнитные колебания», «Осциллограммы…», «Резонанс при последовательном соединении резистора, катушки индуктивности и конденсатора», «Модель линии электропередачи», лаб. «Исследование переменного тока в цепи из последовательно соединенных конденсатора, катушки и резистора»; AQA 3.7.5 (AC, transformer) | an LC circuit on an oscilloscope, an RLC circuit with a generator, a transformer and a transmission line; changes L, C, R, frequency, turns; measures T, the resonance curve, U₂/U₁, the line's losses | 3 controls; steps: LC (T vs √LC) → RLC resonance → transformer and line; T/P: C, T; I(f) | new M2 (transients, AC) + M5 (coupled coils) | M2, M5 |
| S33 | Электромагнитные волны: излучение, отражение, поляризация, шкала волн | [F79] 9 «Электромагнитное поле. Электромагнитные волны. Свойства… Шкала электромагнитных волн… Скорость света», демонстрация «Свойства электромагнитных волн», лаб. «Изучение свойств электромагнитных волн с помощью мобильного телефона»; [F1011] 11 «Условия излучения электромагнитных волн. Взаимная ориентация векторов E, B, v… отражение, преломление, поляризация, дифракция, интерференция… Принципы радиосвязи», демонстрация «Исследование свойств электромагнитных волн…» | a microwave transmitter and receiver (school kit: λ ≈ 3 cm), a metal sheet, a grid polarizer, a paraffin prism, a phone in a metal box; changes angle and orientation; measures the received signal | 3 controls; steps: radiation of a dipole → reflection, standing wave → polarizer → shielding; T/P: angle, signal | exists `core.em.fdtd`, `core.em.charges` (unused today) | fdtd, charges |

### 1.7 Light (ФРП 9 «Световые явления»; 11 «Оптика»; AP 2 U13–U14; IB C.3)

| id | demonstration | curriculum anchor | experiment → change / measure | interface | engine | reuse |
|---|---|---|---|---|---|---|
| S34 | Отражение света; плоское и сферические зеркала | [F79] 9 «Прямолинейное распространение света… Отражение света. Плоское зеркало. Закон отражения света», демонстрации «Получение изображений в плоском, вогнутом и выпуклом зеркалах», лаб. «Исследование зависимости угла отражения светового луча от угла падения», «Изучение характеристик изображения предмета в плоском зеркале»; [F1011] 11 «Отражение света. Законы отражения света. Построение изображений в плоском зеркале»; AP2 U13 | a ray box on an optical disc, mirrors, shadows and eclipses; changes angles and positions; measures angles and image distances | 3 controls; steps: shadows → law of reflection → plane mirror image → curved mirrors; T/P: α, β | new M4 (2-D ray tracer: exact intersections and reflection) | M4 |
| S35 | Преломление света, полное внутреннее отражение, световод | [F79] 9 «Преломление света. Закон преломления света. Полное внутреннее отражение света. Использование … в оптических световодах», демонстрации «Преломление света», «Оптический световод», лаб. «Исследование зависимости угла преломления светового луча от угла падения на границе «воздух–стекло»»; [F1011] 11 «Абсолютный показатель преломления. Полное внутреннее отражение. Предельный угол…», лаб. «Измерение показателя преломления стекла»; AP2 U13; IB C.3 | a ray on a glass half-cylinder, a plate (lateral shift), a fibre; changes angle and glass; measures α, γ, the critical angle; brightness of the reflected and refracted rays from the Fresnel coefficients | 3 controls; steps: α → γ → sin α / sin γ = n → critical angle → fibre; T/P: sin α, sin γ; slope → n | new M4 + exists `core.optics.interfaces` (Fresnel brightness) | M4, interfaces |
| S36 | Линзы, построение изображений, оптические приборы, глаз | [F79] 9 «Линза. Ход лучей в линзе. Оптическая система фотоаппарата, микроскопа и телескопа. Глаз как оптическая система. Близорукость и дальнозоркость», демонстрации «Ход лучей в собирающей линзе», «… в рассеивающей линзе», «Получение изображений с помощью линз», «Модель глаза», лаб. «Получение изображений с помощью собирающей линзы», «Определение фокусного расстояния и оптической силы собирающей линзы»; [F1011] 11 «Формула тонкой линзы. Увеличение…», лаб. «Исследование свойств изображений в линзах»; AP2 U13 | an optical bench with a candle, lens and screen; a model eye with glasses; changes object distance, lens; measures the image distance and size; 1/d + 1/f = 1/F from the data | 3 controls; steps: image on a screen → d, f table → glasses for the eye → telescope/microscope; T/P: 1/d, 1/f; fit → D | new M4 (thick and thin lenses as surfaces; images where the computed rays meet) | M4 |
| S37 | Дисперсия света, спектр, цвет; радуга | [F79] 9 «Разложение белого света в спектр. Опыты Ньютона. Сложение спектральных цветов. Дисперсия света», демонстрации «Разложение белого света в спектр», «Получение белого света при сложении света разных цветов», лаб. «Опыты по разложению белого света в спектр», «Опыты по восприятию цвета предметов при их наблюдении через цветовые фильтры»; [F1011] 11 «Дисперсия света. Сложный состав белого света. Цвет», демонстрация «Получение спектра с помощью призмы», лаб. «Наблюдение дисперсии света» | a prism and a slit, a second prism recombining, filters; a water drop; changes the prism's glass and angle, filters; measures the deviation per colour; sees the rainbow's 42° | 3 controls; steps: prism → recombination → filters → drop and rainbow; T/P: λ, deviation | new M4 + glass dispersion data (Sellmeier; refractiveindex.info database, CC0 1.0: https://github.com/polyanskiy/refractiveindex.info-database) + exists water n(λ) (IAPWS), `theories.approx.rainbow`, `tools.colour` | M4, rainbow, colour |
| S38 | Интерференция и дифракция света; дифракционная решетка; поляризация | [F79] 9 «Волновые свойства света», демонстрация «Волновые свойства света»; [F1011] 11 «Интерференция света. Когерентные источники… Дифракционная решетка… Поляризация света», демонстрации «Наблюдение интерференции света», «Наблюдение дифракции света», «Получение спектра с помощью дифракционной решетки», «Наблюдение поляризации света», [F1011] 11 «Строение атома», демонстрация «Определение длины волны лазера»; IB C.3; AP2 U14 | a laser on two slits, a grating and a ruler, a thin film (soap), two polaroids; changes slit spacing, grating period, angle between polaroids; measures fringe spacing and λ, Malus's law | 3 controls; steps: two slits → grating (λ = d sin φ / k) → soap film → polaroids; T/P: k, x_k; cos²φ | exists `core.optics.scalar`, `aperture_fields`, `thin_films`; Malus by Jones matrices (new, small, in M4) | optics.* |

### 1.8 Relativity, quantum, atom and nucleus, astronomy (ФРП 9 «Квантовые явления»; 11 «Основы СТО», «Квантовая физика», «Элементы астрономии и астрофизики»; AP 2 U15; IB A.5, E.1–E.5)

| id | demonstration | curriculum anchor | experiment → change / measure | interface | engine | reuse |
|---|---|---|---|---|---|---|
| S39 | Основы СТО: относительность одновременности, замедление времени, сокращение длины, E = mc² | [F1011] 11 «Основы специальной теории относительности: … инвариантность модуля скорости света… Относительность одновременности. Замедление времени и сокращение длины. Энергия и импульс релятивистской частицы»; IB A.5 (HL); AQA 3.12 (option); AP2 U15 (E = mc² only) | a light clock on a train, two flashes and two observers, muons from the upper atmosphere; changes the speed; measures the ticks of both clocks and the rod's length; the muon count at sea level | 2 controls; steps: light clock → simultaneity → muons → E = mc²; T/P: β, γ, Δt′/Δt | exists `core.relativity`, `core.worldlines`, `core.causality` | relativity (school scene; v01 stays university) |
| S40 | Фотоэффект: опыты Столетова, законы, уравнение Эйнштейна | [F1011] 11 «Открытие и исследование фотоэффекта. Опыты А.Г. Столетова. Законы фотоэффекта. Уравнение Эйнштейна… «Красная граница»», демонстрации «Фотоэффект на установке с цинковой пластиной», «Исследование законов внешнего фотоэффекта»; AP2 U15; IB E.2 (HL); AQA 3.2.2 | a vacuum photocell with a monochromator and a retarding voltage; a zinc plate on an electroscope under UV and visible light; changes λ, intensity, voltage; measures I(U), the stopping voltage; U_stop(ν) → h/e, A | 3 controls; steps: zinc plate → I(U) at two intensities → U_stop(ν); T/P: ν, U_stop; slope → h/e | new M8a (photons as a Poisson stream; emission by Einstein's relation with the metal's work function; electrons in the gap's field; the emitted-energy spread as a stated model in `theories.models`) | M8a |
| S41 | Опыт Резерфорда и модель атома | [F79] 9 «Опыты Резерфорда и планетарная модель атома»; [F1011] 11 «Модель атома Томсона. Опыты Резерфорда по рассеянию α-частиц. Планетарная модель атома», демонстрация «Модель опыта Резерфорда» | α particles on a gold foil; Thomson's model as the "what if" alternative; changes energy and target; counts per angle | 2 controls; steps: Thomson vs nucleus → counts vs angle → energy; T/P: θ, N(θ) | new M8b (Coulomb scattering: exact hyperbolae; the Thomson atom flagged as an alternative model) | M8b |
| S42 | Линейчатые спектры, уровни энергии, постулаты Бора | [F79] 9 «Модель атома Бора. Испускание и поглощение света атомом. Кванты. Линейчатые спектры», демонстрации «Спектры излучения и поглощения», «Спектры различных газов», «Спектр водорода», лаб. «Наблюдение сплошных и линейчатых спектров излучения»; [F1011] 11 «Постулаты Бора. Излучение и поглощение фотонов… Спектр уровней энергии атома водорода», демонстрация «Наблюдение линейчатых спектров излучения», лаб. «Наблюдение линейчатого спектра»; IB E.1; AQA 3.2.2 | a gas-discharge tube viewed through a grating spectroscope; hydrogen, helium, neon, sodium; white light through cold gas (absorption); changes gas and temperature; measures line wavelengths | 2 controls; steps: continuous vs line spectra → hydrogen's Balmer lines and the level diagram → absorption; T/P: n, λ; 1/λ(1/n²) → R | exists `core.quantum.hydrogen` (levels), `central3d` (dipole matrix elements → line strengths); other gases need line data (NIST ASD, public domain to verify) | hydrogen, central3d |
| S43 | Радиоактивность: α, β, γ, период полураспада, фон | [F79] 9 «Радиоактивность. Альфа-, бета- и гамма-излучения… Период полураспада», демонстрации «Наблюдение треков в камере Вильсона», «Работа счетчика ионизирующих излучений», лаб. «Исследование треков: измерение энергии частицы по тормозному пути (по фотографиям)», «Измерение радиоактивного фона»; [F1011] 11 «Закон радиоактивного распада»; IB E.3; AP2 U15; AQA 3.8 | a Geiger counter with sources and absorbers (paper, aluminium, lead), a sample decaying, a cloud chamber; changes absorber, distance, source; measures counts, N(t), the half-life | 3 controls; steps: absorbers → counts vs time → half-life from the log plot; T/P: t, N; ln N(t) | new M8c (Monte Carlo decays, Bateman chains — part of P3; half-lives from NUBASE2020, Chin. Phys. C 45, 030001 (2021), open access, CC BY 3.0 to verify per article; ranges in matter from a stated model) | M8c |
| S44 | Ядерные реакции, энергия связи, деление и синтез | [F79] 9 «Ядерные реакции… Энергия связи атомных ядер. Связь массы и энергии. Реакции синтеза и деления ядер. Источники энергии Солнца и звезд. Ядерная энергетика»; [F1011] 11 «Энергия связи нуклонов в ядре… Дефект массы… Деление и синтез ядер. Ядерный реактор»; IB E.4, E.5 | a table of nuclides with the binding-energy curve; a chain reaction in a block of fissile material with a moderator and absorbers; changes size, enrichment, absorbers; measures k and the energy released | 3 controls; steps: binding energy from masses → fission and fusion energy → chain reaction: sub-/super-critical | new M8c (AME2020 masses, Chin. Phys. C 45, 030003 (2021); a neutron multiplication Monte Carlo as a flagged model) | M8c |
| S45 | Расширение Вселенной: закон Хаббла | [F1011] 11 «Элементы астрономии и астрофизики: … Расширение Вселенной. Закон Хаббла. Разбегание галактик. Теория Большого взрыва. Реликтовое излучение» | galaxies at different distances with their spectra; changes the epoch; measures redshift and distance → H₀ and the age; the CMB temperature falling with time | 2 controls; steps: redshifts → Hubble plot → age; T/P: d, v; v(d) → H₀ | exists `core.cosmology.flrw` (unused today) + `core.data` Planck 2018 | flrw |

Not given its own school item (folded in or left out, with the reason):
- «Физика и ее роль … Погрешность измерений» (7): measurement and uncertainty are part of every school demo's
  instruments and table, not a separate demo.
- «Строение вещества … размеры атомов» (7) and «Модели твердого, жидкого и газообразного состояний» (8): a school preset
  of S17 (atoms of a gas, a liquid, a crystal from `core.md`).
- IB B.2 "Greenhouse effect": a later school item if the owner wants an IB-specific set (needs a radiative-balance model).
- The ФРП 11 astronomy items «звезды, диаграмма спектральный класс–светимость, эволюция звезд»: need stellar physics the
  engine does not have (curriculum research §4.1, "D"); not planned now.

---

## 2. University (U): 44 demonstrations

### 2.1 Today's worlds that belong here, and their level-specific changes

| world | course and anchor | as it is, or the change for this level |
|---|---|---|
| v01 light travel | SR/GR intro: Taylor & Wheeler *Spacetime Physics* (CC BY 4.0); Hartle; HRW 37; Сивухин IV ch. IX | as it is; the ether, ballistic and corpuscle worlds stay (history of relativity). The school SR is S39 |
| v02 double slit | QM and optics: Feynman III-1; Griffiths & Schroeter; HRW 35, 38; Hecht ch. 9 | as it is. Its school preset «Фотоны 633 нм, две щели» stays as the university's opening preset (single photons build the pattern); school Young's experiment is S38. The research versions are R01, R02, R05, R08, R09 (§3); the declined "vector slits as a polarisation mark" (§3.4) becomes a v02 preset next to `vector_narrow` |
| v03 quantum 1-D | Griffiths & Schroeter ch. 2; HRW 39; Y&F 40 | as it is |
| v04 orbits | GR course: Hartle ch. 9–10; *Exploring Black Holes* (CC BY 4.0) | as it is; the school gravitation is S11 |
| v05 optics bench | Hecht ch. 4, 9; Сивухин IV ch. V | as it is; the school refraction is S35 |
| v06 QCD | particle physics: Griffiths *Elementary Particles*; PDG | as it is. The prior-art check found no research-grade question for a running-coupling + Cornell engine (§3.4, T3) |
| v07 Bell test | QM foundations: Sakurai ch. 3; Griffiths & Schroeter ch. 12; Bell 2004 | as it is |
| v08 wave in 3-D | Fresnel diffraction: HRW 36; Hecht ch. 10 | as it is |
| v10 fast observer | SR: Terrell 1959, Penrose 1959; Feynman I-34 | as it is. Not research: the Terrell–Penrose effect was photographed in an analogue experiment (Hornof et al., Commun. Phys. 8, 161 (2025), https://arxiv.org/abs/2409.04296); a preset reproducing their frames would be a good benchmark |
| v13 hydrogen 3-D | Griffiths & Schroeter ch. 4; Y&F 41; Сивухин V | as it is; school spectra and Bohr levels are S42 |
| v14 quarkonium 3-D | Griffiths *Elementary Particles* ch. 5 | as it is (upper undergraduate; a flagged model) |
| v15 Kerr shadow | graduate GR: Hartle ch. 15; Chandrasekhar; EHT 2019 | as it is, as a graduate GR world. Its «что если: Йоханнсен» preset stays here until R10 exists, then moves there |
| v16 optical vortices | modern optics: Allen et al. 1992; Hecht | as it is (upper undergraduate) |
| v17 Mie scattering | optics: Bohren & Huffman; Hecht | as it is; the school rainbow is a step of S37 |

### 2.2 New university demonstrations (course order)

Priority: **A** = the physics exists in the engine (several modules are unused today): cheap, high value; **B** = needs
a school module (M1–M5) at university depth; **C** = needs new physics from P3/P4 or a new module.

| id | demonstration | course anchor (verified TOCs) | what the student does and sees | engine | prio |
|---|---|---|---|---|---|
| U01 | Лагранжева механика и хаос: двойной маятник, фазовый портрет, сечения Пуанкаре, показатель Ляпунова | Goldstein ch. 11; ЛЛ I; Сивухин I | two nearby starts diverge; the Poincaré section changes from tori to chaos with energy; the energy check runs live | M1 (+ symplectic integrator) | B |
| U02 | Твёрдое тело: уравнения Эйлера, эффект Джанибекова, прецессия и нутация гироскопа | ЛЛ I ch. VI; Goldstein ch. 5; HRW 11; AP C U5–6 | a free asymmetric top flips about its middle axis; a heavy top precesses and nods; L and E conserved | M1 (3-D rigid bodies) | B |
| U03 | Неинерциальные системы: маятник Фуко, сила Кориолиса | Ландсберг т. 1 гл. VI; Сивухин I; Goldstein ch. 4 | the plane of a pendulum turns at Ω sin φ; a puck on a turntable seen from both frames | M1 | B |
| U04 | Связанные осцилляторы, нормальные моды, биения, резонансная кривая и добротность | Berkeley vol. 3 (Crawford); HRW 15; Feynman I-21–25 | two and N coupled pendulums, energy transfer, the spectrum by FFT, amplitude and phase vs drive frequency | M1 | B |
| U05 | Кинетическая теория из атомов: Максвелл–Больцман, барометрическая формула, длина свободного пробега, перенос | Schroeder ch. 6; Савельев т. 1 ч. 2; Сивухин II | distributions measured from the MD run against the closed forms; diffusion, viscosity and heat conduction coefficients | exists `core.md` | A |
| U06 | Тепловые машины и энтропия: цикл Карно и Отто из МД, P–V и T–S, необратимость | Schroeder ch. 4; Сивухин II | a cycle of an atomic gas, efficiency against Carnot's bound, free expansion and mixing | exists `core.md` + bath switching (the S21 extension) | A |
| U07 | Модель Изинга и фазовые переходы | Schroeder ch. 8; ЛЛ V ch. XIV | magnetization, susceptibility and the critical temperature against Onsager | P4 (B10) | C |
| U08 | Излучение чёрного тела: моды полости, Рэлей–Джинс против Планка, Вин, Стефан–Больцман | Schroeder ch. 7; Сивухин V ch. I | mode counting in an FDTD cavity, the spectrum with thermal occupation, the ultraviolet catastrophe as the classical "what if" | exists `core.optics.radiation`, `core.em.fdtd` (cavity modes tested) | A |
| U09 | Электростатика: краевые задачи, изображения, мультиполи, ёмкость, диэлектрики | Griffiths ch. 2–4; Jackson ch. 1–4; Сивухин III | charges near conductors, images vs the computed solution, the multipole expansion of a computed potential | M3 | B |
| U10 | Магнитостатика и индуктивность: Био–Савар, катушки Гельмгольца, теорема о циркуляции, взаимная индукция | Griffiths ch. 5, 7; Сивухин III | field maps, Ampère's loop integral, the mutual inductance of two loops (elliptic integrals) | M3, M5 | B |
| U11 | Заряженные частицы в полях: циклотрон, масс-спектрометр, дрейф E×B, магнитная ловушка, эффект Холла | Griffiths ch. 5; Jackson ch. 12 | relativistic orbits in uniform and computed non-uniform fields; the adiabatic invariant | exists `core.spin_transport` + M3 | B |
| U12 | Цепи: переходные процессы RLC, векторные диаграммы, резонанс, фильтры, длинная линия | HRW 31; Сивухин III | transients, Bode plots, reflections on a line | M2 | B |
| U13 | Излучение зарядов: поле ускоренного заряда (излом линий), диполь, Лармор, синхротронное излучение | Griffiths ch. 11; Jackson ch. 14 | the radiation kink, a dipole antenna's pattern by FDTD, the synchrotron cone and spectrum | exists `core.em.charges`, `core.em.fdtd` (both unused) | A |
| U14 | Волны в веществе и волноводах: моды волновода, резонатор, затухающая волна, одномерный фотонный кристалл | Jackson ch. 8; Griffiths ch. 9 | cut-off frequencies, cavity Q, the evanescent tail at TIR, a band gap | exists `core.em.fdtd` | A |
| U15 | Интерферометры и когерентность: Майкельсон, Маха–Цендер, Фабри–Перо, фурье-спектроскопия | Hecht ch. 9, 12; Сивухин IV | fringes vs path difference, coherence length of a broad source, a spectrum from an interferogram | exists `core.optics.*` | A |
| U16 | Фурье-оптика: дифракция Фраунгофера как преобразование Фурье, 4f-фильтрация, разрешение решётки, Аббе | Hecht ch. 11; Goodman (not verified here) | spatial filtering of an image; grating resolving power | exists `core.optics.angular_spectrum` | A |
| U17 | Поляризация и кристаллооптика: Джонс и Мюллер, фазовые пластинки, двулучепреломление | Hecht ch. 8; ЛЛ VIII ch. XI | wave plates on the Poincaré sphere; a calcite crystal | new (crystal optics) | C |
| U18 | Опыт Штерна–Герлаха и спин: последовательные приборы, прецессия Лармора | Sakurai ch. 1; Griffiths & Schroeter ch. 4 | a spin-½ packet split by a field gradient; z → x → z; precession in a uniform field | exists `core.quantum.scene` (spin coupling −μ·B for any field) + `qubits` | A |
| U19 | Двухуровневый атом: Раби, Рамси, сфера Блоха, оптические уравнения Блоха, спонтанное излучение, квантовые скачки | Foot ch. 7 (not re-verified); Sakurai ch. 5 | Rabi flopping with detuning, Ramsey fringes, damped Bloch vector, single trajectories with jumps averaging to the master equation | exists `two_level`, `open_systems`, `jumps` (two_level and open_systems unused) | A |
| U20 | Фотоны: фотоэффект (h/e по Милликену), эффект Комптона | HRW 38; Сивухин V ch. I | U_stop(ν) slope; the Compton shift vs angle and the Klein–Nishina distribution from scattered photons | exists `core.quantum.compton` (unused) + M8a | A |
| U21 | Дифракция электронов на кристалле: Дэвиссон–Джермер, кольца Дебая–Шеррера, закон Брэгга | HRW 38; Kittel ch. 2 | Bragg peaks vs voltage; rings from a powder | new (structure factor; scalar diffraction exists) | C |
| U22 | Атом: серии водорода, тонкая структура, эффект Зеемана, правила отбора | Griffiths & Schroeter ch. 7; Bethe–Salpeter | line positions and strengths from computed matrix elements; Zeeman splitting | exists `hydrogen` (Schrödinger and Dirac levels), `central3d` + new perturbations | B |
| U23 | Зоны: Кронига–Пенни, сильная связь, блоховские осцилляции | Kittel ch. 7; Ashcroft–Mermin | bands from transmission windows and from the Bloch eigenproblem; an electron oscillating in a tilted lattice | `core.quantum.transfer` + P4 | C |
| U24 | Рассеяние Резерфорда и сечение | Goldstein ch. 3; Griffiths & Schroeter ch. 10 | dσ/dΩ histogrammed from many computed hyperbolae against Rutherford's formula | M8b | B |
| U25 | Ядро: цепочки распадов (Бейтман), α-распад как туннелирование (Гамов), формула Вайцзеккера | Krane ch. 3, 6, 8 | decay chains in equilibrium; Geiger–Nuttall from computed tunnelling | M8c + exists `core.quantum.transfer` (P3 subset) | C |
| U26 | Релятивистская кинематика: инвариантная масса, распады, пороги реакций | Griffiths *Elementary Particles* ch. 3; HRW 37 | thresholds and decay kinematics in different frames | exists `core.lorentz` | A |
| U27 | Диаграммы Минковского и парадокс близнецов | *Spacetime Physics*; HRW 37 | worldlines, proper times, Doppler signals between twins | exists `core.relativity`, `worldlines`, `causality` | A |
| U28 | Гравитационные волны от двойной: чирп, h₊ и h×, пульсар Халса–Тейлора | Hartle ch. 23; Maggiore vol. 1 | the inspiral, the waveform at a detector, Ṗb of PSR B1913+16 reproduced | exists `pn_binary`, `gw_quadrupole`, `peters_mathews` | A |
| U29 | Космология: история расширения, диаграмма Хаббла, расстояния, возраст, горизонты | Weinberg *Cosmology*; Dodelson–Schmidt | D_L, D_A, a(t) for Planck 2018 and for "what if" parameter sets | exists `core.cosmology.flrw` (unused) | A |
| U30 | Режимы течения: Пуазейль, Бернулли и Вентури, число Рейнольдса от ползущего течения до дорожки Кармана | Kundu ch. 9–10; ЛЛ VI | profiles and drag against references; the wake changing with Re | exists `core.fluids.lbm` | A |

---

## 3. Researchers (R): research set-ups not done before, with the prior-art check

### 3.1 What the research audience is

A research demonstration is a **set-up that the literature has not computed or measured**, built on the engine's exact
solvers, with: the open question stated in one line; the prior art (references with DOIs/arXiv ids and the URL each
was verified from); the rival predictions it separates; the measurable it outputs (a table and a sweep, exportable);
its approximations; and a "hypothesis" status until reproduced (AGENTS rule 11). Its audience is a researcher who wants
to design an experiment: every research world exposes the parameters an experiment would control (packet length,
plate thickness, switching times, detector models) and reports the effect size against the error of the method.

The owner's example — "разные постановки двухщелевого эксперимента для постановки новых экспериментов на той же базе"
— is taken literally: **v11's exact 2-D/3-D double-slit bench is the shared base**, and most research worlds are new
set-ups on it.

### 3.2 Today's research-grade worlds (assigned to Research only)

| world | why research | research additions in this plan |
|---|---|---|
| v11 double slit 2-D/3-D | exact non-paraxial Schrödinger–Pauli solution with real plates, Bohm trajectories labelled by slit, spin marks, AB flux, live edits — the base bench | becomes the bench of R01, R02, R03, R05, R06, R08, R09 (shared engine part, §6.3 RB1) |
| v12 arrival times 2-D | QM does not fix the arrival time; seven rules and detector models on the same run | R04 extends it |
| v09 Thomas–Wigner 3-D | holonomy of 3-D manoeuvres; its open part is narrow (R07) | R07: research presets and a sweep |

### 3.3 Research set-ups, ranked by novelty and value

Novelty and value were judged from the prior-art files named at the top; the ranking weighs (1) how narrow the gap
is, (2) what a result would teach or which experiment it would inform, (3) whether the engine can compute it with
existing or small extensions. "No paper found" = two or three targeted searches; recheck before any claim.

| rank | id | set-up | done (closest prior art; verified URLs) | open (what the world computes) | novelty / value | engine |
|---|---|---|---|---|---|---|
| 1 | **R01** | **Time-dependent Aharonov–Bohm flux in a real double slit.** The flux tube between the slits is switched or ramped at a chosen moment while the packet is passing; the induced electric field outside the solenoid, E = −∂A/∂t, is included | theory only, and in dispute: cancellation — Singleton & Vagenas, PLB 723, 241 (2013), https://arxiv.org/abs/1305.1498; Macdougall & Singleton, JMP 55, 042101 (2014), https://arxiv.org/abs/1312.1405; Macdougall, Singleton & Vagenas, PLA 379, 1689 (2015), https://arxiv.org/abs/1505.01510 (calls for an experiment); frequency-dependent phase — Choudhury & Mahajan, PLA (2019), https://arxiv.org/abs/1903.04138; the effect exists — Wakamatsu 2024–25, https://arxiv.org/abs/2406.18046, https://arxiv.org/abs/2511.07775; Gao, Found. Phys. 55, 85 (2025), https://arxiv.org/abs/2601.17659. No experiment and no full time-dependent wave-packet solution found | the fringe shift against the switching time and the ramp time (sweep), from the exact wave through a finite-thickness plate; which of the published predictions (shift ∝ flux at passage, at detection, time average, cancellation) the Schrödinger equation gives in each regime; the Bohm trajectories' re-routing | **medium–high** / settles a live dispute inside quasistatic QM (stated limit: no field quantization, no radiation); electrons are the clean case | ext: time-dependent vector potential A(t) in `schrodinger_nd` (gauge phases recomputed per step) and the scalar potential of the induced field; checks: the static AB shift (exists) as the limit, gauge invariance under A → A + ∇χ(t) |
| 2 | **R02** | **Delayed which-path mark and erasure with massive particles in a spatial double slit.** A spin rotation in one slit (the mark) is switched on, or the spin analyser's basis is chosen, after the wave has passed the slits | photons: Kim et al. 2000, Walborn et al. 2002, Jacques et al. 2007; review Ma, Kofler & Zeilinger, RMP 88, 015005 (2016) — lists matter-wave erasers (Eichmann 1993, Dürr 1998, Weisz 2014), none delayed; massive delayed choice only in Wheeler's interferometer form: Manning et al., Nat. Phys. 11, 539 (2015); free-electron path–photon entanglement: Henke et al., https://arxiv.org/abs/2504.13047 (2025; not delayed). No spatial-slit massive delayed eraser found (searches 2016–2026) | spin-resolved screen patterns, Bohm re-routing and arrival times when the mark or the analyser basis is set at t after the slits; the physics point the world must show: a unitary "unmark" works only while the beams are separate, after overlap erasure is by spin-resolved post-selection | **medium** as numerics, **high** as an experiment proposal / designs a He* or electron experiment; check the Henke/Ropers follow-ups before claiming | ext: time-dependent spin rotation in a region (Pauli step exists); spin-resolved detector records (exist per point) |
| 3 | **R03** | **Higher-order interference in real slits: Sorkin's κ for matter waves with thick slits, and wall tunnelling as a third path** | experiments: Sinha et al., Science 329, 418 (2010); Kauten et al., NJP 19, 033017 (2017); Cotter et al., Sci. Adv. 3, e1602478 (2017) (molecules) — metadata only; theory: Sawant et al., PRL 113, 120406 (2014), https://arxiv.org/abs/1308.2022 (thin slits, Fraunhofer); De Raedt, Michielsen & Hess, PRA 85, 012101 (2012) (FDTD, photons); da Paz et al., PRA 93, 033621 (2016), https://arxiv.org/abs/1510.04186 and Vieira et al., https://arxiv.org/abs/1705.07156 (Gaussian slits); Quach, PRA 95, 042129 (2017), https://arxiv.org/abs/1610.06401 (detectors); de Almeida, Lewenstein & Quach, PRA 102, 042225 (2020), https://arxiv.org/abs/2007.05279; Magaña-Loaiza et al., Nat. Commun. 7, 13987 (2016). No exact time-dependent matter-wave κ with hard finite-thickness slits found; no paper on wall tunnelling as a third aperture | κ from seven runs (all closures) of the exact solution, near to far field, for electrons, neutrons, He, C₆₀; its dependence on how a slit is closed (absorbing vs reflecting plug); a plate of finite barrier height (BEC behind optical barriers, gated 2DEG) where tunnelling through the wall is a third path, separated from the looped-path κ | **medium** / sets the systematic floor experiments must beat (snippets suggest κ ~ 1e-8 for electrons — not verified); the tunnelling part is physical mainly for BECs and 2DEGs | ext: N-slit plates (exist in `core.quantum.scene`), closure modes, a closure sweep |
| 4 | **R04** | **Arrival-time discrimination behind a real plate** (extends v12): all rules and detector models on one exact geometry, including the horizontal screen proposed for He* | multi-rule with Gaussian sources and no plate: Ayatollah Rafsanjani et al., Commun. Phys. 6, 195 (2023), https://arxiv.org/abs/2301.02641; exact plate with Bohm and flux only: Das, Deckert, Kellers, Krekels, Struyve, "Double-slit experiment revisited", Ann. Phys. 479, 170054 (2025), https://arxiv.org/abs/2211.13362; Das & Struyve, PRA 104, 042214 (2021), https://arxiv.org/abs/2105.14744; Cavendish & Das, PRA 112, 062217 (2025) (absorbing boundary rule vs scattering theory), https://journals.aps.org/pra/abstract/10.1103/332p-4nl1; spin-dependent arrival: Das & Dürr, Sci. Rep. 9, 2242 (2019), https://arxiv.org/abs/1802.07141, solved with detector models by Jozani & Tumulka, Phys. Rev. Research 8, 033072 (2026), https://arxiv.org/abs/2603.22044; backflow unobserved for matter waves: Paterek & Goussev, PRL 136, 090202 (2026), https://arxiv.org/abs/2511.10155. No experiment with time-resolved double-slit arrivals found | does the up-to-~40 % discrimination of the horizontal screen survive a real finite-thickness plate and real detector models? maps of negative flux (backflow) behind real slits, where the flux rule fails and Bohm/absorbing rules do not; the spin-dependent rule as a preset (low novelty) | **medium–low** / informs the He* proposal directly | exists v12 + v11 machinery; ext: a horizontal screen plane, detector-model sweep |
| 5 | **R05** | **Pulsed scalar (electric) Aharonov–Bohm effect: design numerics** — a potential pulse on one slit's channel while the packet is inside a field-free region | done for neutral particles: neutrons — Allman et al., PRL 68, 2409 (1992); Badurek et al., PRL 71, 307 (1993); cold Na atoms — Shinohara et al., PRA 66, 042106 (2002); gravitational — Overstreet et al., Science 375, 226 (2022); static electrostatic with fields — Matteucci & Pozzi 1985; time delay — Hilbert, Caprez & Batelaan, NJP 13, 093025 (2011). Charged pulsed version untested; proposals: Schütz et al., Ultramicroscopy 158, 65 (2015), https://arxiv.org/abs/1303.7140; Bachlechner & Kleban, PRB 101, 174504 (2020); Chiao et al., PRA 107, 042209 (2023), https://arxiv.org/abs/2212.03437; Vieira dos Santos, https://arxiv.org/abs/2605.08148 (2026: "never been experimentally tested in its original formulation") | fringe shift and visibility against pulse timing, packet length and edge sharpness; pulsed vs static (which adds a delay) | **low** as physics, **medium** as design numerics for the electron and ion proposals | ext: time-dependent scalar potential in a region (smooth edges exist) |
| 6 | **R06** | **The recoiling slit (Einstein–Bohr) as an exact two-body problem**: the plate as a quantum degree of freedom with a mass comparable to the projectile's, finite thickness and transit time | experiments: Liu et al., Nat. Photon. 9, 120 (2015); Fedoseev et al. (MIT), PRL 135, 043601 (2025), https://arxiv.org/abs/2410.19671; Zhang et al. (USTC), PRL 135, 230202 (2025), https://arxiv.org/abs/2410.10664; theory: Lin et al., PRA 113, 022219 (2026), https://arxiv.org/abs/2507.19801. No exact two-body computation beyond the impulse/overlap approximation found | visibility vs plate mass and the plate's momentum spread; Bohm trajectories of both bodies in configuration space | **low–medium** / bridges the 2025 experiments to the heavy-slit limit | ext: per-axis masses in `schrodinger_nd` (configuration space x, z, X as a 3-D grid with V(x − X, z)) |
| 7 | **R07** | **Thomas–Wigner rotation per rapidity budget** (v09): the planar bound and whether a non-planar manoeuvre beats the circle | the area law: Aravind, AJP 65, 634 (1997) (metadata only); Rhodes & Semon, AJP 72, 943 (2004), https://arxiv.org/abs/gr-qc/0501070; O'Donnell & Visser, EJP 32, 1033 (2011), https://arxiv.org/abs/1102.2001; Berry & Visser, https://arxiv.org/abs/2002.10659; Palge & Pfeifer, PRA 109, 032206 (2024), https://arxiv.org/abs/2310.08121; optical Lorentz-group phase observed: Kitano & Yabuzaki, PLA 142, 321 (1989) (metadata only); isoperimetric inequality: Osserman, Bull. AMS 84, 1182 (1978); minimal surfaces in H³: Choe & Gulliver, Invent. Math. 109, 495 (1992) (hypotheses not checked). The bound Θ ≤ √(L² + 4π²) − 2π (equality only for the circle) was not found in print but follows from known results | a numerical search over non-planar loops of fixed rapidity length L: does any beat the circle? (a proof would need the sharp isoperimetric inequality for minimal surfaces in H³) | **low–medium** (note-level) / a math-physics curiosity; the planar bound is a teaching note. Boundary: only published results enter the engine (AGENTS §4) | exists v09 (`core.spin_transport`); ext: an optimizer over loops |
| 8 | **R08** | **Graded which-path mark and the crossing of Bohm trajectories** (v11 sweep): the share of trajectories that cross the symmetry axis vs the mark angle, from the exact Pauli current in thick slits | photons with partial which-way and weak-measurement trajectories: Xiao, Wiseman et al., Sci. Adv. 5, eaav9547 (2019), https://arxiv.org/abs/1805.02059; atoms with graded distinguishability: Dürr, Nonn & Rempe, PRL 81, 5705 (1998); matter-wave crossing trajectories under decoherence: Sanz & Borondo, EPJD 44, 319 (2007), https://arxiv.org/abs/quant-ph/0310096; CPL 478, 301 (2009), https://arxiv.org/abs/0803.2581; the "surreal" debate: Englert, Scully, Süssmann, Walther 1992 | crossing fraction vs θ for He, C₆₀, electrons with real slits | **low–medium** / concept covered; exact numerics new | exists v11 (presets `mark90`, `mark180`) + a sweep |
| 9 | **R09** | **Time-modulated slit**: one slit's height or width oscillates; Floquet sidebands mark the path in energy; interference lost in the time-integrated pattern and recovered by time-resolved detection | neutrons: Badurek, Rauch & Tuppinger, PRA 34, 2600 (1986) (quantum beats); Geppert-Kleinrath et al., PRA 97, 052111 (2018); light: Fernandez-Guasti, Front. Phys. 9, 813565 (2022), https://www.frontiersin.org/articles/10.3389/fphy.2021.813565; diffraction in time: Moshinsky 1952, Szriftgiser et al. 1996, Lindner et al. 2005, Tirole et al. 2023 | a spatial matter-wave double slit with a modulated slit, computed exactly, including the non-adiabatic regime (modulation period ~ transit time), benchmarked against the J₀(β) visibility of pure phase modulation | **low–medium** | ext: a periodic potential change per step |
| 10 | **R10** | **Non-Kerr photon rings, a reproduction benchmark**: n = 1, 2 rings, Lyapunov exponent, time delay and rotation for the Johannsen metric at inclined observers | Johannsen, PRD 88, 044002 (2013); Psaltis et al., PRL 125, 141104 (2020), https://arxiv.org/abs/2010.01055; EHT Sgr A* VI, ApJL 930, L17 (2022); Johnson et al., Sci. Adv. 6, eaaz1310 (2020), https://arxiv.org/abs/1907.04329; Staelens et al., PRD 107, 124026 (2023), https://arxiv.org/abs/2303.02111 (the Johannsen ring shape and Lyapunov exponent — essentially this set-up); Wielgus, PRD 104, 124058 (2021); Ayzenberg, CQG 39, 105009 (2022), https://arxiv.org/abs/2202.02355; Cárdenas-Avendaño & Held, PRD 109, 064052 (2024), https://arxiv.org/abs/2312.06590; Walia et al., PRD 111, 104074 (2025), https://arxiv.org/abs/2411.15119; Ben Achour et al., JCAP 10 (2025) 012, https://arxiv.org/abs/2506.09882 (shape alone degenerate). BHEX: concept, Pre-Phase A, to be proposed as a NASA SMEX in mid-2026 (https://www.haystack.mit.edu/news/bhex-test-001/); no selection found | first reproduce Staelens et al.; then a table of γ, δ, τ for inclined observers at M87* and Sgr A* with a degeneracy check against BHEX precisions (no such table found) | **low** (crowded field) / value as a benchmark of the engine | new: a null-geodesic tracer for the Johannsen metric (only its shadow edge exists) |

### 3.4 Candidates declined after the prior-art check

| candidate | why declined | where it goes instead |
|---|---|---|
| Vector vs scalar slits as a polarisation which-path mark (TE cut-off of unequal slits, analyser as eraser) | low–medium novelty; mainly teaching; a perfect conductor has no plasmons, so it is quantitative only for microwaves/THz; single photons add nothing beyond classical vector coherence. Prior: Schouten et al., PRL 94, 053901 (2005); Kuzmin et al., Opt. Lett. 32, 445 (2007); Gan, Gbur & Visser, PRL 98, 043908 (2007); Norrman et al., PRL 119, 040401 (2017) | a v02 preset (University) |
| QCD running scenarios (α_s(M_Z) "what if", quarkonium with a running coupling) | textbook: five-loop running known since 2017 (Baikov, Chetyrkin & Kühn, PRL 118, 082002); α_s from the lattice static energy (Bazavov et al., PRD 100, 114511 (2019), https://arxiv.org/abs/1907.11747); varying Λ_QCD studied (Jaffe, Jenkins & Kimchi, PRD 79, 065014 (2009); Epelbaum et al., PRL 110, 112502 (2013)). The engine's four loops are one order behind | v06 stays University |
| Spin-dependent arrival times (Das–Dürr) as a separate world | solved with detector models: Jozani & Tumulka (2026), above | a preset of R04 |
| Breakdown of the truncated post-Newtonian radiation reaction | studied: Yunes & Berti, PRD 77, 124006 (2008), https://arxiv.org/abs/0803.1853; Blanchet, Living Rev. Relativ. 27, 4 (2024); the flux is known to 4PN (PRD 108, 064041 (2023)) | U28 teaching plot |
| Terrell–Penrose rotation | photographed in an analogue (Hornof et al. 2025) | v10 (University) with a benchmark preset |

---

## 4. Playgrounds (PL): free laboratories

### 4.1 What every bench offers (by P15, P16 and LB1 already, plus what this plan adds)

- An empty or saved scene; the palette of the field's objects; the inspector; direct manipulation (P16.2); laws live
  where the engine can change them (P16.1); the never-restarting world; save and load.
- Instruments and sweeps (P16.3): every measurable as a time series and CSV; parameter sweeps in a separate process.
- Running checks of the field's conservation laws and invariants (energy, momentum, charge, norm, Gauss/Ampère on probe
  surfaces), so that a free experiment still shows whether the numbers can be trusted.
- **Libraries (LB2, P16.4)** per bench: real objects with data and sources, plus **"lab set-ups" shelves** that
  reproduce the school and university experiments as editable starting scenes (the S-table's lab kit as a shelf of
  the mechanics bench, the U-table's as another), so a student can go from a guided demo to the free bench with the same
  apparatus. A shelf is data, not a separate audience.
- **Palette depth** chosen by the user: "basic" objects (school lab kit) or "full" (everything the solver has). The
  bench stays one visualization of one audience (the playgrounds); the depth is a filter.
- Units and scales of the field shown with the world's validity (the 20 orders of magnitude between sections are why
  benches are separate: P16 plan, facts of the UX audits of 2026-11-04).

### 4.2 Benches

| id | bench | status | what it offers | needs |
|---|---|---|---|---|
| p01 | Космос и гравитация | exists | Newton N bodies, PN binary with waves, Kerr–Newman geodesics and observers; LB2: 1PN (EIH) N bodies live | LB2 |
| p02 | Квантовые частицы | exists | packets, potentials, slits, fields, flux tubes, detectors, marks, measurement, decoherence | — |
| p03 | Частицы и молекулы | exists | MD and hard spheres, walls, piston, baths, phases | bath switching (S21) adds cycles |
| p04 | Жидкости | exists | 2-D LBM flows, bodies, dye, forces | moving bodies (for floating) would need an LBM extension — not planned |
| p05 | Оптика и волны (B9, P15.2) | planned | rays (M4) where valid, scalar waves (angular spectrum), FDTD fields; sources, apertures, lenses, mirrors, prisms, gratings, films, detectors | M4, existing optics, FDTD |
| p06 | Электричество и магнетизм (B9, P15.5) | planned | charges, conductors, dielectrics, currents, magnets; statics (M3), induction (M5), charges' motion and radiation, FDTD | M3, M5, charges, FDTD |
| p07 | Теория относительности (B9, P15.6) | planned | observers, rods, clocks, light signals, rockets; Minkowski diagrams, what each observer sees, gyroscopes | existing relativity modules |
| p08 | Механика (new) | proposed | particles and rigid bodies, springs, strings and pulleys, inclines, tracks, friction, collisions, drag, liquids at rest (buoyancy); force and energy probes; "lab kit" shelf from S01–S16 | M1 |
| p09 | Электрические цепи (new) | proposed | a breadboard with sources, R, C, L, diodes, lamps, switches, transformers, meters, an oscilloscope; coupled to coils and magnets of p06 through M5 where the scales match (LB3) | M2, M5 |

Not proposed now: a nuclear and radiation bench (after P3 in B11) and a quantum-optics bench (level schemes driven by
lasers, from `open_systems`) — both are natural later benches; the owner decides.

---

## 5. The catalogue's structure

### 5.1 Four sections

The catalogue, the README (each language) and the site get four top sections in this order: **School · University ·
Research · Laboratories (playgrounds)** (RU: «Школа · Университет · Исследования · Лаборатории»). Inside each, the
physics sections in teaching order (mechanics → fluids → waves → heat → electricity and magnetism → optics → relativity
→ quantum → atom → condensed matter → nucleus → particles → astrophysics and cosmology; curriculum research §2), each
heading with a count. School can also be browsed by grade (7, 8, 9, 10, 11) with the ФРП section names; University
by course. Each card: picture, title, one line "what you will see", the anchors (ФРП grade and section / AP-IB unit,
or the textbook chapters), "run" (site: recording; local: live), and **"the same topic at other levels"** links
(S38 ↔ v02 ↔ R02, S35 ↔ v05, S11 ↔ v04 ↔ p01 …), so a topic ladder is visible without one world serving two
audiences.

### 5.2 The school mode of the player (`VIZ["ui"] = "school"`)

> **Superseded on 2026-11-14** by the screens Watch, Explore and Lab work (design `explore_2026-11-14_design.md`,
> plan P17.5, batch EX1; what the code keeps: `../../visualizations/RULES.md` §10). The guided steps became the lab's
> steps; `VIZ["guide"]` is retired. The text below is the plan as written on 2026-11-12.

- One scene (2-D by default; 3-D only where the experiment is 3-D), large labels, SI units with school prefixes;
  works at tablet and Chromebook widths; keyboard and colour-blind-safe palette.
- **Guided steps** («Шаг 1 из 4»): each step names the goal, enables its controls (≤ 5), and says what to measure; the
  student can leave the guide ("свободный режим") within the same demo.
- **Instruments with a scale division and an error** (ruler, stopwatch with reaction time, dynamometer, ammeter,
  voltmeter, thermometer, protractor); readings are taken by «Измерить» into a **table**; the table plots any two
  columns; **a straight-line fit** (`tools.stats`) gives the slope with its uncertainty.
- **«Сверка с законом»** at the end: the measured constant against the law's value computed by the run (the run's check,
  shown simply). The full checks, the laws editor, devices, slice planes and «Физика этого мира» are hidden (one
  collapsed "Как это посчитано" paragraph).
- A **worksheet** per demo, both languages: goal, the ФРП lab's name, steps, questions, answers for the teacher
  (PhET's "Teacher Tips" pattern, curriculum research Appendix D).
- The guide is data in `viz.py` (`GUIDE = [{step, text key, controls, instruments, columns, plot}]`), translated through
  the i18n catalogues (rule 13).

### 5.3 How a visualization declares its audience (registry → README → site, rule 15)

Today `VIZ` has `id, title, summary, purpose, version, schema, simulation[, kind, section]`, and `registry.py` accepts
folders `^[vp]\d{2}_…`. Proposed additions to `VIZ` (all keys translated through i18n where they are text):

```python
VIZ = {
    "id": "s35_refraction",
    "audience": "school",                 # school | university | research | playground (must match the prefix)
    "section": "optics",                  # one of the teaching-order sections of §5.1
    "ui": "school",                       # school | full
    "curriculum": [                       # school: required — at least one ФРП anchor and one of AP/IB/AQA
        {"system": "FRP-OOO-2025-base", "grade": 9, "section": "Световые явления",
         "item": "Лабораторная: Исследование зависимости угла преломления светового луча от угла падения на границе «воздух–стекло»",
         "url": "https://edsoo.ru/wp-content/uploads/2025/07/2025_ooo_frp_fizika-7-9_baz.pdf"},
        {"system": "FRP-SOO-2025-base", "grade": 11, "section": "Оптика", "item": "Лабораторная: Измерение показателя преломления стекла"},
        {"system": "AP2", "unit": 13}, {"system": "IB-2025", "topic": "C.3"}],
    "related": ["v05_optics_bench"],      # the same topic at other levels (checked to be symmetric)
    "guide": GUIDE,                       # school only
    # university: "courses": [{"text": "Hecht, Optics, 5th ed.", "chapters": "4"}]
    # research:  "question": "...", "prior_art": [{"ref": "...", "doi": "...", "url": "...", "verified": "abstract"}],
    #            "rank": 1, "status": "hypothesis"
    ...
}
```

A completeness test (next to the i18n tests) fails when: an entry has no audience or its audience does not match the
folder prefix; a school entry lacks a ФРП anchor or an AP/IB/AQA anchor, a guide, or a worksheet; a research entry
lacks its question, prior art or status; a `related` link is one-sided; an entry is missing from the generated
README sections in any language, from the site index, or has no picture or recording. The README's catalogue sections
and the site's index are generated from `registry.describe` (rule 15), never edited by hand.

**Folder ids.** Two-digit `vNN` ids cannot hold ~100 demonstrations. Option A (recommended): per-audience prefixes
`sNN_` (school), `uNN_` (university), `rNN_` (research), `pNN_` (playgrounds); today's `vNN` worlds are renamed
(`v02_double_slit` → `u02_double_slit`, `v11_double_slit_2d` → `r01_…`, …) and `registry.py` keeps an alias map so
that existing run records, links and checkpoints still open. Option B: keep `vNN`, add `audience` only, and widen the
regex to three digits. A is clearer for users and makes the prefix check trivial; B avoids renaming. The owner decides
(open question 2).

### 5.4 The public site and school demos

> **Decided on 2026-11-14** (owner, `../../AGENTS.md` §1): way (a), recorded parameter lattices, as the atlases of the
> screens Explore and Lab work (design `explore_2026-11-14_design.md` §1; `../../visualizations/RULES.md` §10); the
> sliders stop only at computed points, and a server computes any value live. The text below is the plan as written on
> 2026-11-12.

The site plays recordings (rule 15). A school lab is interactive by nature (the student changes the length and
measures). Two ways, for the owner to choose (open question 3):
- **(a) Recorded parameter lattices**: each guided step records the runs over its control values (e.g. pendulum
  lengths 0.2 … 1.0 m in nine steps); on the site the student picks among recorded values; the table and fit work on
  recorded readings. Fully within rule 15; coarse.
- **(b) In-browser engine for light school modules** through Pyodide (licence MPL-2.0 — to verify; numpy, scipy BSD):
  M1, M2, M4 and M7 are cheap enough to run live in the browser. Changes rule 15 for school demos (live on the site,
  no server) and needs a build and test of the engine under Pyodide.

---

## 6. Batches (three items each, AGENTS rule 10)

### 6.1 New engine modules (layer: core unless stated; every one tested against closed forms or a second method, reviewed by another agent)

| id | module | first scope | references for the tests | used by |
|---|---|---|---|---|
| M1 | `core.mechanics` | classical 2-D (then 3-D) particles and rigid bodies: uniform gravity, springs, strings and pulleys (constraints with their tensions), inclines and track curves, contact with Coulomb friction (static/kinetic), impacts with restitution, linear and quadratic drag, variable mass; fixed-axis and free rigid bodies; hydrostatics and buoyancy as the integral of the computed pressure over wetted surfaces; symplectic and event-located integrators; energy and momentum bookkeeping | closed forms: projectile with no, linear, vertical quadratic drag (tanh); Atwood; block on an incline (threshold); pendulum period through `core.elliptic` K; 1-D/2-D collisions; rolling a = g sin θ/(1 + I/mr²); Euler top (Jacobi functions, `core.elliptic`); Archimedes ρgV_sub; comparison candidates: Box2D or pymunk (MIT — licences to verify) | S01–S16, U01–U04, p08 |
| M2 | `core.circuits` | modified nodal analysis: DC, transients (R, L, C, switches, sources), AC phasors, meters with internal resistance; diode (Shockley) and lamp filament R(T) as `theories.models`; Faraday's law of electrolysis | Kirchhoff and Thévenin closed forms, RC/RL/RLC transients and resonance, Tellegen's power balance as a running check; comparison candidate: ngspice (core modified BSD = BSD-3-Clause; some files under other licences — per-file check, https://ngspice.sourceforge.io/faq.html) | S23–S28, S32, U12, p09 |
| M3 | `core.em.statics` | electrostatics: Poisson/Laplace in 2-D and 3-D with conductors (fixed potential or charge), dielectrics, capacitance, field lines traced from the computed field; magnetostatics: Biot–Savart for wires, loops, coils, magnetized bodies; forces and torques on currents (the static half of P15.5) | images (plane, sphere), sphere and coaxial capacitance, dielectric sphere in a uniform field, plate capacitor with fringing (conformal map), infinite wire, loop on axis and off axis (elliptic integrals), finite solenoid, Helmholtz pair, ∮B·dl = μ₀I, Gauss on probe surfaces | S22, S23, S29, S30, U09–U11, p06 |
| M4 | `core.optics.rays` | 2-D/3-D geometric ray tracing: plane and spherical surfaces, thin and thick lenses, mirrors, prisms, fibres; Snell with dispersion (Sellmeier data), TIR, Fresnel brightness from `core.optics.interfaces`; image location from computed ray bundles; Jones matrices for polarizers | ABCD (`theories.approx.ray_optics`) in the paraxial limit, exact spherical mirror/lens intersections, prism minimum deviation, critical angle, Malus; data: refractiveindex.info database (CC0 1.0, verified) | S34–S38, p05 |
| M5 | `core.em.induction` | quasi-static induction: flux through moving, rotating, deforming loops, EMF and induced currents coupled with M2 and the mechanics of M1 (Lenz forces, eddy-free first scope), self and mutual inductance, transformer | rod on rails, rotating loop (generator), mutual inductance of coaxial loops (elliptic integrals), energy balance mechanical ↔ electrical ↔ heat | S31, S32, U10, p06, p09 |
| M6 | `core.waves` | 1-D string and acoustic tube, 2-D scalar waves (ripple tank, sound) with moving sources, on the Yee update of `core.em.fdtd` | grid dispersion relation, standing-wave frequencies, Doppler closed form, two-source interference | S13, S14 |
| M7 | `core.thermal` | lumped calorimetry, 1-D conduction (Fourier), Newton cooling and radiation, phase change by the enthalpy method; material data with sources | erf solution of conduction, exponential cooling, heat balance, Stefan problem (Neumann's solution) | S18, S19, S26 |
| M8 | a: `theories.models.photoemission`; b: Coulomb scattering in `core`; c: `core.nuclear.decay` + data (a P3 subset) | a: Einstein relation with a stated energy-spread model; b: exact hyperbolae, dσ/dΩ; c: Monte Carlo decays, Bateman chains, NUBASE2020 half-lives and AME2020 masses (Chin. Phys. C 45, 030001 and 030003 (2021), open access; CC BY 3.0 to verify per article) | Einstein's line, Rutherford's formula, Bateman closed forms, exponential law (DKW bound on samples) | S40, S41, S43, S44, U20, U24, U25 |

### 6.2 The first three batches (school foundations, as asked)

**AB1 — the school framework, mechanics, the first mechanics labs.**

| item | content | tests and references | size |
|---|---|---|---|
| F1 | audience registry (§5.3: `audience`, `section`, `ui`, `curriculum`, `related`, `guide`; the folder-id decision; today's worlds tagged as in §7; generated README sections in both languages and site index; the completeness test) and the school mode of the player (§5.2: guided steps, instruments with divisions, table, plot with fit, «Сверка», worksheet template, i18n) | registry and i18n completeness tests; browser tests of the school mode (Playwright, as the existing `tests/browser/*`); anchors: [F79], [F1011], AP, IB | L (framework + player) |
| M1 | `core.mechanics` (first scope of §6.1 without 3-D rigid bodies and buoyancy) | the closed forms of §6.1; an independent review | M–L |
| SF1 | S01 straight-line motion, S02 free fall, S03 projectile, S09 energy conservation | per demo: the measured constant (a, g, range maximum, v²(h) slope) against the run's check; worksheet RU/EN | M (4 school demos on one template) |

**AB2 — the rest of school mechanics, circuits.**

| item | content | tests and references | size |
|---|---|---|---|
| SF2 | S05 Newton's laws, S06 Hooke, S07 friction and incline, S10 momentum and collisions (M1 extended: restitution, variable mass, Coulomb friction pairs data) | Atwood, incline threshold, collision closed forms; `core.md.hard` as the second route for elastic disks | M |
| M2 | `core.circuits` | Kirchhoff/Thévenin, transients, Tellegen; one-off comparison with ngspice if its per-file licences allow | M |
| SF3 | S24 Ohm's law and resistance, S25 series/parallel/mixed, S26 work and power of current, S27 EMF and internal resistance | measured R, ℰ, r against the circuit's values; lamp model data with sources | M |

**AB3 — statics of fields, rays.**

| item | content | tests and references | size |
|---|---|---|---|
| M3 | `core.em.statics` (electro- and magnetostatics, forces on currents) | §6.1 closed forms; an independent review | L |
| SF4 | S22 charges and field, S23 capacitor, S29 magnetic field of magnets and currents, S30 Ampère force, motor, electron beam | F(1/r²), C(S/d), B(I), F(I) fits against the run's values | M |
| M4 | `core.optics.rays` + glass dispersion data + **S35 refraction and TIR** as its proof (the owner named «преломление света») | §6.1; Snell, critical angle, n from the fit | M |

### 6.3 Later batches (proposed order by value; the owner may reorder at each discussion)

| batch | items | why | size |
|---|---|---|---|
| RB1 | R01 time-dependent AB, R02 delayed mark/erase, R03 higher-order interference | the three best research set-ups; one shared extension of the v11 bench (time-dependent A and spin rotations, N-slit closures, sweeps) | L |
| AB4 | SF5 optics (S34, S36, S37, S38), M5 induction with S31 and S32, SF6 (S04, S08, S11, S12) | completes school optics, electromagnetism and mechanics | L |
| UB1 | U19 two-level atom, U13 radiation of charges, U29 cosmology | physics exists and is unused today: cheapest university value | M |
| AB5 | M6 waves with S13, S14, S33; M7 thermal with S18, S19; SF7 heat from atoms S17, S20, S21 | school waves and heat | L |
| AB6 | buoyancy and hydrostatics (M1 ext) with S15, S16; SF8 modern physics S39, S40, S41, S42; M8c nuclear with S43, S44, S45 | completes the school set (S28 joins the batch that has room) | L |
| UB2 | U18 Stern–Gerlach, U20 photons, U28 gravitational waves | existing physics | M |
| RB2 | R04 arrival-time discrimination, R05 pulsed scalar AB, R06 recoiling slit | the next research set-ups | L |
| UB3 | U01–U04 (mechanics, M1 3-D rigid bodies), U12 circuits, U09–U10 statics | university depth on the school modules | L |
| UB4–UB6 | U05, U06, U08, U14; U15, U16, U17; U21, U22, U24, U26, U27, U30, U11 | by course | M each |
| RB3 | R07, R08, R09 | v09 and v11 sweeps, the modulated slit | M |
| with B10 / B11 | U07, U23 (P4); U25 (P3) | need the large fields | — |
| later | R10 (non-Kerr tracer) | low novelty; a benchmark | M |
| playgrounds | B9 re-scoped onto M3, M4, M5 (p05, p06, p07); a new batch for p08 mechanics and p09 circuits after AB2–AB4; LB2 libraries with the "lab set-ups" shelves | the benches reuse the school modules | — |

Relation to the existing plan: LB2 waits for the owner's go; B9's optics and E&M benches need P1 (done in B8) and,
with this plan, M3–M5 and M4, so B9 is best placed after AB3/AB4. The P3 subset M8c (decay chains, data) is pulled
forward from B11 for the school.

Sizes are rough: S ≈ one agent-day of implementation with tests; M ≈ two to three; L ≈ a full batch pass with several
agents, as LB1 was. They are guesses until the first batch is measured.

---

## 7. Moving today's worlds (each to exactly one audience)

| world | audience | the same topic at another level (separate visualizations) |
|---|---|---|
| v01 light travel | University | S39 (school SR) |
| v02 double slit | University | S38 (school wave optics); R01, R02, R05, R08, R09 (research on the v11 bench) |
| v03 quantum 1-D | University | — |
| v04 orbits | University | S11 (school gravitation); p01 (laboratory) |
| v05 optics bench | University | S35 (school refraction and TIR) |
| v06 QCD | University | — (research version declined, §3.4) |
| v07 Bell test | University | — |
| v08 wave in 3-D | University | S38 |
| v09 Thomas–Wigner 3-D | **Research** | U27 (spacetime diagrams) for the university SR basics |
| v10 fast observer | University | S39 |
| v11 double slit 2-D/3-D | **Research** (the bench) | v02 (University), S38 (School) |
| v12 arrival times 2-D | **Research** | — |
| v13 hydrogen 3-D | University | S42 (school spectra) |
| v14 quarkonium 3-D | University | — |
| v15 Kerr shadow | University (graduate GR) | R10 (research benchmark; the «что если» preset moves there when R10 exists) |
| v16 optical vortices | University | — |
| v17 Mie scattering | University | S37 (school dispersion and rainbow) |
| p01–p04 | Playgrounds | p05–p09 |

Per-world preset changes are small: no world loses physics; school-level presets stay where they serve as a
university opening (v02, v13), and the research versions are separate worlds.

---

## 8. Open questions for the owner

1. **Scope of the school set.** 45 demonstrations to the ФРП базовый (with AP/IB cross-checks). Also the углублённый
   programme's extra content (статика, полупроводники, ультразвук, ядерная энергетика) and IB-only topics (greenhouse
   effect)? Its lab lists were not checked for this plan.
2. **Folder ids**: per-audience prefixes `s/u/r/p` with aliases for old ids (A), or `vNN` with three digits and an
   `audience` field (B)? (§5.3)
3. **School demos on the public site**: recorded parameter lattices (a, within rule 15) or the engine in the browser via
   Pyodide (b, changes rule 15 for school demos)? (§5.4)
4. **Order**: the school foundations first (AB1–AB3), then RB1, as proposed; or RB1 earlier, given the owner's wish for
   a much stronger research section? And LB2 before or after AB1?
5. **Research framing**: research worlds carry "hypothesis" status and a prior-art list; publication claims only after
   reproduction and a fuller literature survey (AGENTS rule 11; the owner's 2026-10-16 bar for papers). Is the ranking
   of §3.3 right? In particular, R07 touches the owner's own research line on Thomas–Wigner rotation: only published
   results may enter the engine (AGENTS §4) — confirm that the planar fuel bound, which follows from published
   results (Aravind 1997 + Osserman 1978), may be shown in v09.
6. **Language of terms**: school RU terms by the ФРП; EN by AP/IB — confirm, and whether a third language is planned
   soon (rule 13 then multiplies the worksheets).
7. **New benches p08 (mechanics) and p09 (circuits)** — add to the plan?
8. **Data sources** to confirm: refractiveindex.info (CC0, verified), NUBASE2020/AME2020 (open access, CC BY 3.0 to be
   checked per article), NIST ASD line data (public domain — not verified here), tungsten and material data for lamps
   and calorimetry (sources to choose).
