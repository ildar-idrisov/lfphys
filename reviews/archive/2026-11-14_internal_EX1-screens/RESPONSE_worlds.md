# Response to review R-P (EX1-screens), part "worlds": what of the screens' findings is in S03's and u32's own files

**Responder:** QW, the processing agent for the worlds `s03_projectile` and `u32_double_slit` (containers `lf-qw-*`,
private port 8707). It wrote neither the review nor the code under review. **Date:** 2026-11-17.

**Scope.** The review is the player's (QP, `RESPONSE_player.md`) and the framework's (QF). This part answers what lies
in the two worlds' files: F7's world units (assigned), and the world sides of F8 (S03's trace label, drawn by
`s03_projectile/web/view.js`), F16 (the doubled «our translation») and F17 (`core.data`'s whole description on a
school projectile), which the integrator routed to this agent through D10 and D13, and F18's binding of part 3's
grey-ball tape to its landing (asked by QP through the integrator).

**Counts:** 5 world parts: 5 fixed. None rejected.

| # | finding (world part) | outcome | where | test |
|---|---|---|---|---|
| F7 | English leaks into Russian pages: the laws' units | **fixed** (world side). The units of S03's laws and references are translatable texts now: `T("m^½")` (RU «м^½»), `T("m")` (RU «м»); «°» stays a plain symbol. The quantity is named by the law's own label (`label`, a T: «the slope of L against sin 2θ», «θ* of the largest range in air», …), not by the id `slope`/`vertex`. Rendering them with `t()` in `lab.js`/`worksheet.js`, and the 429 message, are QP's | `s03_projectile/viz.py` (`STEPS[*].laws[*].unit`, `lab_reference`), `locales/ru.json` | `test_s03_physics.py::test_lab_reference_of_every_law_against_an_independent_computation` (`unit.msgid` is "m^½" / "m"); `tests/test_i18n.py` (every text the world sends is translated) |
| F8 | a live point's labels: the trace's «computed live» runs off the canvas | **fixed** (the drawing; the label's text and the passport are QP's). A trace's label is drawn above its landing mark, right-aligned when it would pass the right edge, clamped inside the canvas and moved by a line until it overlaps no other label of the frame (the current landing's «L = …, T = …», «H = …», the ball's name, the other traces); the same placement serves the Watch's earlier throws | `s03_projectile/web/view.js` (`freeSpot`, `placeLabel`, `drawTraces`) | browser: S03 Explore EN/RU at 1280 and 390 px, three launches (screenshots in the agent's notes) |
| F16 | «(our translation)» doubled on the worksheet | **fixed** (world side): the FRP names' English msgids no longer carry «(our translation)»; the worksheet's own marking («translated; the programme's own wording: «…»») stays the one note. Each FRP entry also carries `programme`, a display name per language («Russian federal programme, basic level, grades 7–9 (2025)» / «ФРП ООО, базовый уровень, 2025»), for QP to print instead of the raw id. The space before «°» is QP's | `s03_projectile/viz.py` (`WORKSHEET["frp"]`), `locales/ru.json` | `tests/test_i18n.py` |
| F17 | «Physics of this world» on S03 opens with the PDG masses and Planck cosmology | **fixed** (D10, world side, on QE's new data-set entries): `engine_modules()` names `core.data:air`, the one data set S03 reads, instead of `core.data`; the drawer now lists the U.S. Standard Atmosphere 1976 only. The «tol» column of the standard table is QP's | `s03_projectile/viz.py` (`engine_modules`) | `test_s03_physics.py::test_the_engine_modules_and_the_events_reveal_no_lab_value` (the header's engine list holds `core.data:air` and no other data entry) |
| F18 | (world part) part 3's grey-ball tape reads before the grey ball lands | **fixed**: `tape_grey` declares `"event": "companion_landing"`, the event the world emits when the grey (vacuum) ball lands; before it the tape says «Nothing to measure yet» (QF validates the field, `lab.js` reads it) | `s03_projectile/viz.py` (`INSTRUMENTS["tape_grey"]`) | `test_s03_physics.py::test_the_worksheets_numbers_are_the_engines` (the field, and one `companion_landing` event in an `air_max` run) |
