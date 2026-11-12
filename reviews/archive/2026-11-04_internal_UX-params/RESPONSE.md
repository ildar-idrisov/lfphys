# Response to review UX-params (2026-11-04): index

Processed 2026-11-05 by four processing agents, none of whom wrote the review (`../README.md`). This file is only the
index, written by the integrator's assistant when the folder was archived: the decisions, the fixes and their
verification are in the part files. The review text is not edited.

**Part files.**
- `RESPONSE_framework.md`: the framework and the player — P1, P2, P3, P4, P8, P20, P22, P23 and the framework parts of
  P17 and P28; the API for the world agents; the changes for the integrator for both UX reviews (STATUS V45, V37 (d),
  (h), RULES §3 and §6, the owner guide).
- `RESPONSE_p01-p02-v03.md`: v03 and p02 with their engine modules — P13, P19, P28, P29, P30 and their parts of P4.
- `RESPONSE_p03-p04.md`: p03 and p04 with their engine modules — P24, P25, P27, P31, P32, P33 and their parts of P4;
  its changes for the integrator are in `../2026-11-04_internal_UX-ui/RESPONSE_p03-p04.md`.
- `RESPONSE_v-worlds.md`: the demonstrations v01, v02, v06, v07, v08, v13–v17 — P5–P7, P9–P12, P14–P16, P18, P21, P26
  and the world parts of P3, P4, P8, P17, P23; F1–F5 found while processing.

## Decisions

| ID | severity | one line | decision | STATUS | part file |
|---|---|---|---|---|---|
| P1 | error | a world refused at its start was never explained | fixed (a failed start had counted as resumable [error in earlier]) | — | framework |
| P2 | should-fix | a typed or emptied number refused in English with the id | fixed | — | framework |
| P3 | error | an exception in `after_header` killed the worker | fixed | — | framework; v-worlds (v13's zero scale) |
| P4 | should-fix | any exception became a refusal text or a traceback | fixed | — | framework; the world causes: v-worlds (P5–P8, P17, P18), p01-p02-v03 (v03, p02), p03-p04 (p03, p04) |
| P5 | should-fix | v06: α_s(M_Z) = 0.19 refused with «RG integration failed» | fixed (in the core) | — | v-worlds |
| P6 | should-fix | v15: the Johannsen metric refused in English; one combination crashed | fixed (the crash [error in earlier]) | — | v-worlds |
| P7 | should-fix | v01: walkers faster than this world's light: «worldline is not timelike» | fixed | — | v-worlds |
| P8 | error | v02: «Темновые отсчёты» near 10¹² 1/с took 31 GB | fixed (a memory budget per worker; v02 bounded per step) | V45 (f): the budget with CUDA on GPU 0, closed 2026-11-05 | framework; v-worlds |
| P9 | error | v01: a flash inside a rod «measured» c = 5.6·10⁸ … 7.8·10⁹ м/с | fixed [error in earlier] | — | v-worlds |
| P10 | should-fix | v13/v14: «Суперпозиция» from the defaults refused; l ≥ n, \|m\| > l | fixed | — | v-worlds |
| P11 | should-fix | v16: «Голограмма-вилка» from the defaults refused | fixed | — | v-worlds |
| P12 | should-fix | v01: one law changed from the defaults refused | fixed | — | v-worlds |
| P13 | should-fix | v03 «Ступенька»: 52–88 s and two failed checks | fixed [error in earlier] | V15 (stated limits) | p01-p02-v03 |
| P14 | should-fix | v01 «Андромеда»: checks failed by round-off of absolute times | fixed [error in earlier] | — | v-worlds |
| P15 | should-fix | v02: \|γ₁₂\| = 1.108 shown failed with one slit dark | fixed [error in earlier] | — | v-worlds |
| P16 | should-fix | v17: index-matched drop NaN, failed Debye check; «⏭» stalled | fixed; a remainder found while processing (F2) | V47 (a) | v-worlds |
| P17 | should-fix | v02: choices always refused were offered; ids in texts | fixed (options shown per choice; Russian refusals) | — | framework; v-worlds |
| P18 | should-fix | v02: «λ зонда» at its minimum allocated 2 GiB; GRW overflow | fixed | — | v-worlds |
| P19 | should-fix | v03: a wide sharp barrier gave T 55× off; wording | fixed [error in earlier] | V15 (stated limits) | p01-p02-v03 |
| P20 | nit | refusal prefixes used internal names | fixed | — | framework |
| P21 | nit | v07: the reversal-speed reference lost precision at extreme settings | fixed | — | v-worlds |
| P22 | nit | a slice plane moved past the box showed an empty window | fixed | — | framework |
| P23 | nit | honest failing checks with no word about why | partly | V45 (e) | framework (the mechanism; partly); v-worlds (v02, v06: `expected` and the presets' notes set; v16's failures at random extremes stay failures). V45 (e) says no world emits `expected` yet; `RESPONSE_v-worlds.md`, P23, reports that v02 and v06 do |
| P24 | should-fix | p04: every fluid other than «dfg» refused from the defaults | fixed | V42 (e) closed | p03-p04 |
| P25 | error | p04: a thin or tall domain allocated without a limit | fixed | — | p03-p04 |
| P26 | should-fix | v08: a source from the defaults refused only after a minute | partly | V47 (c) | v-worlds |
| P27 | nit | p04: a probe inside a body read NaN without a word | fixed | — | p03-p04 |
| P28 | error | p02: a refused removal half-removed the object | fixed [error in earlier] | V37 (h) closed | framework (`clear` all or nothing); p01-p02-v03 (p02's order) |
| P29 | should-fix | p02: extreme edits made the wave NaN | fixed [error in earlier] | — | p01-p02-v03 |
| P30 | should-fix | p02: tens of seconds per scene change | fixed (with UX-ui U3) | — | p01-p02-v03 |
| P31 | should-fix | p03: «Стенка», «Поршень» refused in English in the default box | fixed | — | p03-p04 |
| P32 | should-fix | p03: edits that crash the world | fixed | — | p03-p04 |
| P33 | should-fix | p03: counts at their maxima stall the world | fixed | — | p03-p04 |

Found while processing (`RESPONSE_v-worlds.md`): F1 v16's fork orders' charge checks → V47 (b); F2 v17's nearly
index-matched drops → V47 (a); F3 v15's notice in English — fixed with P6; F4 v01's lens of radius 0 without GR —
fixed with P12; F5 v14's continuity tolerance → V47 (d).

## Totals

33 findings (6 errors, 22 should-fix, 5 nits):
- **31 fixed**, 9 of them with a withdrawn statement or result [error in earlier] (P1, P6, P9, P13, P14, P15, P19,
  P28, P29);
- **2 partly fixed**, the remainders in STATUS: P23 → V45 (e), P26 → V47 (c);
- **0 rejected, 0 deferred**;
- 5 more found while processing: F1, F2, F5 → V47 (b), (a), (d); F3, F4 fixed.

By part file, as each states it: framework — 10 rows, P23 partly, the rest fixed; p01-p02-v03 — 6 of 6 fixed;
p03-p04 — 7 of 7 fixed; v-worlds — 18 rows, P26 partly, the rest fixed.

STATUS items opened, extended or closed by this review: V15 (text), V37 (h) closed, V42 (e) closed, V45 (e), V45 (f)
closed, V47 (a)–(d).
