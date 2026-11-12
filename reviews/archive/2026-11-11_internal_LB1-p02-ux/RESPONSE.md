# Response to review LB1-p02-ux (2026-11-11): index

Processed 2026-11-11/12 by five processing agents, none of whom wrote the review or the code under review
(`../README.md`). This file is only the index, written by the integrator's assistant when the folder was archived: the
decisions, the fixes and their verification are in the part files. The review text is not edited.

**Part files.**
- `RESPONSE_p02.md`: p02 and `core.quantum` — Q1–Q11 (Q3's p02 side), X5, X10, X11 and X12's p02 part; found while
  processing E1–E4.
- `RESPONSE_framework.md`: the framework and the player — X2, X3, X4 (framework part), X6, X8, X12 (framework part) and
  X13 (framework part). Its «Changes for the integrator» hold the texts for this review and for LB1-framework F5,
  F13–F15; its «Final runs» answer both reviews.
- `RESPONSE_instruments.md`: the sweeps — Q3 (the sweep's side), X1, X7, X9. Its texts for the integrator are in
  `../2026-11-11_internal_LB1-framework/RESPONSE_instruments.md`.
- `RESPONSE_p03.md`: X4's p03 part (its checks in `../2026-11-11_internal_LB1-physics/response_checks_p03/`).
- `RESPONSE_p04-p01.md`: X4's p01 Kerr part and X14 (their checks in
  `../2026-11-11_internal_LB1-physics/response_checks_p04-p01/`).

## Decisions

| ID | severity | one line | decision | STATUS | part file |
|---|---|---|---|---|---|
| Q1 | error | a drag next to a flux tube cut the wave's phase; the event said «та же волна» | fixed (the magnetic translation, or refused) [error in earlier] | — | p02 |
| Q2 | should-fix | in a non-uniform field the drag changed the kinetic energy silently | fixed (refused, with the kinetic change) [error in earlier] | — | p02 |
| Q3 | error | p02's `measure()` returned a tuple; every p02 sweep failed | fixed [error in earlier] | — | p02 (the dict); instruments (the contract checked and named) |
| Q4 | error | the 2-D → 3-D carry-over broke on walls, steps and flux planes; contradicting notices | fixed (p02's part; the form's grid and window are X3) [error in earlier] | — | p02 |
| Q5 | should-fix | the throw limit ignored the wave's spectrum, so a clamped throw was refused | fixed (with X5; the root cause in the engine, E1) [error in earlier] | V39 (l) (the limit shown is an isotropic bound) | p02 |
| Q6 | should-fix | a window change with open edges moved the absorbing layers over the wave silently | fixed [error in earlier] | — | p02 |
| Q7 | should-fix | the grid's help promised one rule of three; a wrong refusal for a free packet | fixed [error in earlier] | — | p02 |
| Q8 | should-fix | with open edges, a drag refused for wave already inside the absorber | fixed | — | p02 |
| Q9 | nit | a same-window change moves the cell and the layers by up to d/2 | fixed (stated; keeping the cell fixed declined, with the reason) | — | p02 |
| Q10 | nit | the "regrid" bank can be negative but was labelled «отброшено» | fixed | — | p02 |
| Q11 | nit | for a split wave the handle, λ and the drag reference are means that may mean nothing | fixed (with X11: labelled; «где волна сейчас») | — | p02 |
| X1 | error | sweeps over an object's parameter were refused in every playground | fixed | — | instruments |
| X2 | error | Delete did not delete in p02's plane window; it showed «Срез не построен» | fixed [error in earlier] | — | framework |
| X3 | should-fix | «Новый мир» into the other dimension offered no grid or window | partly fixed (the form shows every law of the new world; no values proposed from what the carried scene needs) | V39 (n) | framework |
| X4 | should-fix | in p03 and in p01's Kerr world the default throw was absurd and refused | fixed (framework: the automatic scale, the clamp and refusal texts, `velocity_display`; p03: throws in nm/s shown in m/s, `velocity_max` 500 m/s [error in earlier]; p01: `velocity_max` half of c) | — | framework; p03; p04-p01 |
| X5 | should-fix | in p02 the throw limit shown was not the limit applied | fixed (with Q5) | — | p02 |
| X6 | should-fix | velocity units and number formats were inconsistent | fixed in the player's and the framework's formatting (`ui.js` `num`, `lfviz.playground.fmt`); the sections' parts were left to their agents: p02's events now give km/s (X12), but no part file answers p02's velocity unit in the readout or p01's event numbers | — | framework |
| X7 | should-fix | the sweep form for a femtosecond world | fixed | — | instruments |
| X8 | should-fix | the top bar wrapped, and toasts covered each other | fixed | — | framework |
| X9 | should-fix | «Что менять» doubled units and listed the hidden law | fixed | — | instruments |
| X10 | should-fix | any coarsening of a preset was blocked by the automatic edges | fixed («Огрубить сетку с краями по ней») | — | p02 |
| X11 | should-fix | «Центр пакета» was not where the packet is | fixed (with Q11) | — | p02 |
| X12 | nit | event texts | fixed | — | framework (the edit and set lines, no empty events); p02 (its own texts) |
| X13 | nit | axes | fixed in the framework part (round 1-2-5 ticks, the last label inside the window); the instruments part (an empty plot's time unit in «Приборы») was left to the instruments agent and is not answered by a part file | — | framework |
| X14 | nit | p04's message after a change of the largest speed reported a 2 % mass change | fixed (the message attributes it to the scheme's compressibility) | — | p04-p01 |

Found while processing (`RESPONSE_p02.md`): E1 [error in earlier] the boosted wave's spectral model doubled a split
wave's reach (the root cause of Q5); E2 [error in earlier] a move's gauge factor could push a charged wave's canonical
spectrum past the band unchecked; E3 [neutral] a moved packet equals a packet prepared there only up to its own tail at a
tube; E4 [neutral] the split operator is not covariant between scenes related by a singular gauge → V39 (m).

## Totals

25 findings (Part A: 3 errors, 5 should-fix, 3 nits; Part B: 2 errors, 9 should-fix, 3 nits):
- **22 fixed**: Q1–Q11, X1, X2, X4, X5, X7–X12, X14;
- **1 partly fixed**: X3 → V39 (n);
- **2 fixed in their framework parts**, their other parts not answered by a part file: X6 (p02's velocity unit in the
  readout, p01's event numbers), X13 (an empty plot's time unit in «Приборы»);
- **0 rejected, 0 deferred**; found while processing E1–E4.

By part file, as each states it: p02 — Q1–Q11, X5, X10, X11 and X12 (p02) fixed (its own count: 14 fixed); framework —
6 fixed, X3 partly; instruments — 4 fixed (Q3's sweep side, X1, X7, X9); p03 — X4 (p03) fixed; p04-p01 — 2 of 2 fixed
(X4's p01 Kerr part, X14).

STATUS items opened by this review: V39 (k)–(n) (the p02 item: (l) from Q5, (m) from E4, (n) from X3); V48's
instruments items cite X6.
