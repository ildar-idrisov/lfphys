# Response to review i18n-language: the engine part (PR-B)

Processed 2026-11-13 by the engine agent of the integration (not the review's author). The part covers the engine
catalogue `lfphys/lfphys/locales/ru.json` (962 entries at review time) and the engine's English msgids in
`lfphys/lfphys/**`. The read-through rows of the two engine chunks (R01-xxx, R02-xxx: 152) were processed in two halves
of the sorted catalogue; the owner's decisions and the integrator's glossary of 2026-11-13 were applied to **every** entry
of the engine catalogue, not only to the rows. Msgids were renamed in the code by the syntax tree (every `T(...)` /
`i18n.T(...)` whose first argument is the old msgid; several literals span lines), so code and catalogue stay in step.

Summary: **230 Russian entries changed, 66 msgids renamed (with their Russian), 8 English plural overrides added in a
new engine `locales/en.json`; rows: 147 fixed, 1 partly, 4 not applied (reasons below).** The new texts added for the
code review's F4 (≈200 raises made translatable) were written to the same glossary.

| # | finding (engine part) | decision | verification |
|---|---|---|---|
| F1 | meaning reversed or lost | fixed: R02-045 «у граней текущего окна ({cells} крайних ячеек)»; R02-014 «согласуются с опытом с точностью 2–10 %»; R01-050/R02-015 «плоское пространство-время», «внешняя область метрики Шварцшильда» (and EN "flat spacetime or the Schwarzschild exterior") | catalogue diff; `test_i18n_engine.py` |
| F2 | agreement errors | fixed: R01-010 «термостаты … и Ланжевена (BAOAB)»; R02-001 «гармоники Шотта точны» | as F1 |
| F3 | names | fixed in the whole engine catalogue: Тиомно, Бусси, Мархевка, Буррау, Ганкеля (one form, the glossary's; R02-063 proposed «Ханкеля» — the glossary wins), Фореста–Рута–Йошиды, Петерса–Мэтьюза, Кийовский | grep of the catalogue |
| F4 | non-standard terms | fixed in the engine entries: «время распространения света», «краситель», «спонтанные локализации GRW», «диспергирующие», «сжимающее свойство (контрактивность)», «ступенчатая аппроксимация», «трубка магнитного потока» (8), «момент импульса», «экваториальная плоскость», «удалённый наблюдатель», «невозможность передачи сигнала»; the grid "carries" a wave → EN "resolves", RU «разрешает» (6 msgids, see the msgid references below) | as F1 |
| F5 | "against" → «против» | fixed by sense in every engine entry (17): «в сравнении с», «сверка с», «в зависимости от», «относительно»; «против» is left only in a benchmark («0,46 против 0,76 мс») | scan of the catalogue: no other «против» |
| F6 | "closed form" | fixed: «в замкнутом виде», «формула в замкнутом виде», «аналитическое решение» (16 entries) | scan: «замкнут» left only in literal senses (a closed box, closed edges, closed timelike curves) |
| F7 | numerical error → «погрешность» | fixed (32 entries); «ошибка» kept for a fault, for «ошибка округления» (the review accepts it) and for the statistical «стандартная ошибка» | scan |
| F8 | the playground's name | fixed per the owner's decision: "laboratory" / «лаборатория» in the two engine kernel labels (lbm, fdtd: "(the “Fluids” laboratory)", "(the “Electricity and magnetism” laboratory, optics)"); no user-facing "playground"/"sandbox"/«плейграунд»/«песочница» left in the engine catalogue or msgids (code docstrings and identifiers unchanged) | grep |
| F9 | inconsistent terms | fixed in the engine: «2D»/«3D» in Russian (every «1-D/2-D/3-D» in 44 entries → «1D/2D/3D»), «ПН» with a decimal comma («2,5ПН»), «ур.» for equations, «радиационное торможение» one term, «запуск» for a run, «контрольный прогон» for a companion run | scan: no «2-D» in Russian, no «PN» |
| F10 | Latin and English notation | fixed: kelvin «К»; decimal commas in Russian prose (scan: no decimal point outside references, equation numbers and identifiers); «ревью» for "review"; «а. е.», «а. е. м.». R02-073 not applied (Drude, Lorentz, Debye are the class names the API accepts); identifiers in API messages stay as the review says | scans |
| F11 | placeholders carrying English | fixed in code (engine side): the quantum scene's events pass a translatable object name (`NAME` per class: "a box" «ящик», "a potential step" «ступенька потенциала», "a wall with slits", "a flux tube" …) and the Russian is gender-free («добавлено/удалено/изменено: {type} #{oid}»); "added particle {pid} ({species})" passes the species' label; the regrid loss passes a translatable `{kind}`; FDTD shapes have `NAME` and "a body of shape {kind}" became "a body ({kind})" «тело ({kind})» | `test_i18n_engine.py`, the full suite |
| F12 | plural and ordinal forms | fixed in the engine: count phrases got Russian plural forms where the count is `n` (the new F4 texts too: «узел/узла/узлов квадратуры», «конечного/конечных чисел», …) or a label form («молекул: {n:d}»); 8 English "one" forms in the new `lfphys/lfphys/locales/en.json` ("{n} coordinates needed, {m} given", "probe point: {n} coordinates", …); no "{k}th" ordinal in the engine | `test_i18n_engine.py` (placeholders of every form) |
| F13 | English calques and spelling | fixed in the engine msgids: polarisation (all), localisation, polariser, disc (the accretion disc and the shapes; "hard disks" of statistical mechanics kept, R01-059 partly), spacetime, cross-section, 3-D, "eq."/"eqs." (the majority form); calques: "a different model from", "for long runs of quiet systems", "the admissible range" (was "healthy"), "does not pay off" | `renames_applied` (66), grep |
| F14 | label length | nothing in the engine (its labels are short) | — |
| F15 | Russian style | applied where the rows name engine entries (the RU-style rows of R01/R02) | rows |

## Msgid references outside the engine

Checked with a scan of every string literal in `visualizations/**` (worlds, framework, tests) and `lfphys/tests/**`
against the old and new msgids; sent to the integrator:
- `p02_quantum/viz.py:380`: the prefix "the grid does not carry the wave" — the engine's three resolution msgids and the
  packet check now say "resolve"; p02 should switch to `code_of(e)` (`qscene.resolution`, `qscene.packet_band`) or
  `Scene.addition_check` / `particle_check`.
- v15: its own msgids say "disk" ("a Keplerian disk", "Cunningham's disk", "thin equatorial disk") and "(Eq. 76)" while
  the engine now says "disc" and "eq." (PR-C2's choice to align).
- "a potential step": the engine's msgid (renamed from "a step", which the framework uses for a computation step) is
  «ступенька потенциала» by the integrator's decision; v03's catalogue has «потенциальная ступенька» for the same msgid —
  one of the two must change (open point for PR-C1).
- "CPU only" → «Только CPU» (decided jointly with PR-D).
- The engine texts that worlds still match by fragment were **not** reworded: the LBM refusals (p04), the md texts (p03),
  the airy texts (v05), "the field cannot be changed while the charged particle" (p02). They now carry codes.
- Engine tests that asserted reworded text were updated (`test_quantum_scene*.py`, `test_fdtd_api.py`, `test_beams.py`,
  `test_fdtd_scattering.py`, `test_hydrogen_wavefunctions.py`, `test_lbm_remap.py`).

## Rows

Fixed (147): R01-001, R01-002, R01-003, R01-004, R01-005, R01-006, R01-007, R01-008, R01-009, R01-010, R01-011, R01-012, R01-013, R01-014, R01-015, R01-016, R01-017, R01-018, R01-019, R01-020, R01-021, R01-022, R01-023, R01-024, R01-025, R01-026, R01-027, R01-028, R01-029, R01-030, R01-031, R01-032, R01-033, R01-034, R01-035, R01-036, R01-037, R01-038, R01-039, R01-040, R01-041, R01-042, R01-043, R01-044, R01-045, R01-047, R01-048, R01-049, R01-050, R01-051, R01-052, R01-053, R01-054, R01-055, R01-056, R01-057, R01-058, R01-060, R02-001, R02-002, R02-003, R02-004, R02-005, R02-006, R02-007, R02-008, R02-009, R02-010, R02-011, R02-012, R02-013, R02-014, R02-015, R02-016, R02-017, R02-019, R02-020, R02-021, R02-022, R02-023, R02-024, R02-025, R02-026, R02-027, R02-028, R02-029, R02-030, R02-031, R02-032, R02-033, R02-034, R02-035, R02-036, R02-037, R02-038, R02-039, R02-040, R02-041, R02-042, R02-043, R02-044, R02-045, R02-046, R02-047, R02-048, R02-049, R02-050, R02-051, R02-052, R02-053, R02-054, R02-055, R02-056, R02-057, R02-058, R02-059, R02-060, R02-061, R02-062, R02-063, R02-064, R02-065, R02-066, R02-067, R02-068, R02-069, R02-070, R02-071, R02-072, R02-074, R02-075, R02-076, R02-077, R02-078, R02-079, R02-080, R02-081, R02-082, R02-083, R02-084, R02-086, R02-087, R02-088, R02-089, R02-090, R02-091, R02-092.

| row | outcome | note |
|---|---|---|
| R01-039 | fixed | fixed in code (F11): the shape is a translatable `NAME`; msgid "a body ({kind})" «тело ({kind})» |
| R01-042 | fixed | fixed: Russian gender-neutral («добавлено: {type} #{oid}») and `{type}` is now the object's translatable `NAME` |
| R01-046 | not applied | the msgid “box” is shared by the ray tracer's body (a cuboid) and the quantum scene's potential box (a rectangle in 2-D, where «потенциальный ящик» is the textbook term); «ящик» fits both, «параллелепипед» does not fit 2-D; the FDTD texts “box corners…”, “box: hi > lo…” already say «параллелепипед» |
| R01-059 | partly | disc for the accretion disc and the shape (4 renames); «hard disks» of statistical mechanics kept (Hard disks and spheres…, Kolafa & Rottner Z of disks, Perfectly elastic smooth hard disks…, as a model of atoms… for disks) as the review allows |
| R02-018 | not applied | not applied: the review overrules it (REVIEW «Reader rows overruled»: «жидкость» covers gases in hydrodynamics, Landau–Lifshitz VI §1) |
| R02-048 | fixed | fixed: `{kind}` is now a translatable text ("beyond the grid's band", "outside the window", "at the window's faces") |
| R02-053 | fixed | fixed: «удалено: {type} #{oid}» with the translatable `NAME` |
| R02-073 | not applied | not applied: Drude, Lorentz, Debye here are the class names the API accepts (fdtd.py: isinstance(p, (Drude, Lorentz, Debye))) |
| R02-085 | not applied | not applied: the subject is an observer (kn_change_whatif.observer_refusal), «наблюдатель» is masculine, so «оказался бы» is right |

## Tests

Docker `lfphys-viz`, CPU (`LFPHYS_NO_GPU=1`), `--memory=12g`, repository mounted read-only:
- **Full engine suite** `lfphys/tests`: first run 1988 passed, 7 failed, 23 skipped. Six of the failures were tests that
  asserted reworded texts; they were updated, with code assertions added. The seventh was a real bug: a closure calling
  `T` under a temperature `T` in `MD.add_molecules`, fixed and now caught by the guard test. **Final run: 1994 passed,
  23 skipped, 0 failed (41 min).**
- `lfphys/tests/test_codes.py` (new, 10 tests) and `test_i18n_engine.py`: all pass.
- `visualizations/tests/test_i18n.py` (with the merged catalogues): 62 passed, 24 failed. None of the failures is in
  the engine's files:
  - every world's dynamic scan fails on the plain string `step` sent through the framework (PR-A);
  - v02 sends `strip`; v06 sends `Σ f_acd f_bcd = C_A δ_ab` (PR-C1/PR-C2);
  - the msgid "Set-up: changes at once (the same as in the panel on the left)" is translated differently in the
    v02/v08 and v10 catalogues (PR-C1/PR-C2).

  The engine catalogue causes no clash: it was checked against every other catalogue after the conflict notes of the
  integrator ("a potential step", "⁴He atom", "CPU only").
