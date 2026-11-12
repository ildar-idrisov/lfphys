# Response to review UX-ui (2026-11-04): index

Processed 2026-11-05 by four processing agents, none of whom wrote the review (`../README.md`); the camera part of U1
by the 3-D agent of the sibling review UX-3d. This file is only the index, written by the integrator's assistant when
the folder was archived: the decisions, the fixes and their verification are in the part files. The review text is not
edited.

**Part files.**
- `RESPONSE_framework.md`: the framework and the player — U1 (except the 3-D camera), U4 (UI side), U9, U10, U13
  (framework part), U14, U16, U17, U20–U24, and UX-3d A6's playground part; its changes for the integrator are written
  once, for both reviews, in `../2026-11-04_internal_UX-params/RESPONSE_framework.md`.
- `RESPONSE_p01-p02-v03.md`: p01, p02, v03 and their engine modules — U2 (with UX-3d A13), U3, U4 (world side), U5, U7,
  U8, U12, U13, U18, U19.
- `RESPONSE_p03-p04.md`: p03, p04 and their engine modules — U4 (world side), U5, U6, U7, U8, U12, U13, U15, U19; its
  changes for the integrator also serve UX-params P24–P33.
- `RESPONSE_v-worlds.md`: the demonstrations v01, v02, v06, v07, v08, v13–v17 — U13, U19 (the work itself is in
  `../2026-11-04_internal_UX-params/RESPONSE_v-worlds.md`).
- U1's camera part: `../2026-11-04_internal_UX-3d/RESPONSE.md`, section «UX-ui U1 (camera part)».
- `RESPONSE_leftovers.md`: the parts no other part file took — U12 for v11–v14, U15 for p02, U19 for v11/v12; found
  while processing L1 (v12's «Начать новый мир» without a scenario, fixed), L2 (a numeric select sent as text, fixed by
  the integrator in `params._coerce`, test `tests/test_params_select_text.py`), L3 (the `views` case of
  `scene3d_checks.mjs` and p04's hidden 3-D view, fixed by the integrator).

## Decisions

| ID | severity | one line | decision | STATUS | part file |
|---|---|---|---|---|---|
| U1 | error | the view and the object list jump back to where they started | fixed | — | framework (the box's repeats, v04's refit, the object list); `../2026-11-04_internal_UX-3d/RESPONSE.md` (the camera) |
| U2 | error | p01's orbits drawn from one point per frame | fixed [error in earlier] | — | p01-p02-v03 |
| U3 | error | p02 froze for 18–30+ s on every scene change | fixed [error in earlier] | — | p01-p02-v03 |
| U4 | error | the palette places only with defaults, at a fixed spot | fixed | — | framework (the pre-placement form, the click in the scene); p01-p02-v03 (p01, p02 `place`); p03-p04 (p03, p04 `place`) |
| U5 | error | palette and inspector actions block the world for 30–40 s | partly | V38 (g) (p01's companion check re-integrates its interval at once) | p01-p02-v03 (partly); p03-p04 (p03: fixed) |
| U6 | error | palette actions that break the world (p03 hard disks + «＋ Атом») | fixed | — | p03-p04 |
| U7 | error | objects the palette offers that the world can never accept | partly | V39 (i) (p02 in space: only the field's reason computed) | p01-p02-v03 (partly); p03-p04 (fixed) |
| U8 | error | values far outside the world accepted without a word | fixed (p02's NaN packet [error in earlier]) | — | p01-p02-v03 (p02); p03-p04 |
| U9 | should-fix | no feedback while a scene command is computed | fixed, with a cancel | V45 (c), (d) (the limits of cancel and of holding) | framework |
| U10 | should-fix | the inspector loses the focus after every change | fixed | — | framework |
| U11 | should-fix | no direct manipulation in the scene | deferred | V45 (b) | no part file has a decision row for U11: placing at a clicked point and setting the parameters before placing are U4 (framework); picking, dragging and velocity handles are open in V45 (b) (also `../2026-11-04_internal_UX-3d/RESPONSE_framework.md`, last line) |
| U12 | should-fix | laws the engine can change now are world parameters | fixed (p01–p04, v11–v14) | V39 (j), V42 (l) (laws the engine cannot change now) | p01-p02-v03 (p01 collisions, p02 window edges); p03-p04 (p03, p04); v11–v14: `RESPONSE_leftovers.md` (the plate, v12's detectors, v13/v14's state as a preparation) |
| U13 | should-fix | refusals speak the engine's language | fixed | V42 (k) (found while testing: p03's insertion bound counts the Coulomb energy) | framework (texts, prefixes, `Refusal`); p01-p02-v03; p03-p04; v-worlds |
| U14 | should-fix | «События» rebuilt on every drawn frame | fixed | — | framework |
| U15 | should-fix | 2-D sections: the computed field is a side window | fixed (p02, p04) | — | p03-p04; p02: `RESPONSE_leftovers.md` |
| U16 | should-fix | the checks panel is a wall of notes, cut at 1280 px | fixed | — | framework |
| U17 | should-fix | «Прежние группы проверок» closes itself | fixed | — | framework |
| U18 | should-fix | the Newtonian black hole cannot be seen | fixed | — | p01-p02-v03 |
| U19 | should-fix | units missing on primary parameters | p01/p02/v03: rejected (not reproduced); p03/p04: fixed (one unit added); v01–v17 parts: checked, none missing (v06's κ label made explicit); v11/v12: fixed (units in the labels) | — | p01-p02-v03; p03-p04; v-worlds; v11/v12: `RESPONSE_leftovers.md` |
| U20 | should-fix | at 1280×800 the demonstrations are cramped | partly | V45 (a) (v07's own 2×2 layout) | framework |
| U21 | nit | slice tools in worlds without slices | fixed | — | framework |
| U22 | nit | a disabled palette button does not say why | fixed | — | framework |
| U23 | nit | an empty «Действия» first; «Новый мир» open | fixed | — | framework |
| U24 | nit | 9 px speed labels; the bottom bar wraps | fixed | — | framework |

Also processed in this folder: UX-3d A6, the playgrounds' part («◎ Центрировать», «👁 Следить»): fixed
(`RESPONSE_framework.md`; recorded in `../2026-11-04_internal_UX-3d/RESPONSE_framework.md`); UX-3d A13 (p01's trails
sampled per frame): with U2.

## Totals

24 findings (8 errors, 12 should-fix, 4 nits):
- **20 fixed**: U1–U4, U6, U8–U10, U12–U19, U21–U24 (U12, U15 and U19 completed by `RESPONSE_leftovers.md`);
- **3 partly fixed**, the remainders in STATUS: U5 → V38 (g), U7 → V39 (i), U20 → V45 (a);
- **1 deferred**: U11 (direct manipulation in the scene) → V45 (b), and the owner's laboratory plan;
- **0 rejected** as a whole (U19's p01/p02/v03 part rejected: not reproduced);
- found while processing the leftovers: L1–L3, all fixed.

By part file, as each states it: framework — 12 fixed, U20 partly (and UX-3d A6's playground part fixed);
p01-p02-v03 — 10 findings: 7 fixed, 2 partly, 1 rejected; p03-p04 — 9 fixed; v-worlds — U13 fixed, U19 checked;
leftovers — U12 (v11–v14), U15 (p02), U19 (v11/v12) fixed, L1–L3 fixed.

STATUS items opened or extended by this review: V38 (g), V39 (i), (j), V42 (k), (l), V45 (a)–(d).
