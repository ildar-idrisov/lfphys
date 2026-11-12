# Response to review LB1-framework (2026-11-11): index

Processed 2026-11-11/12 by four processing agents, none of whom wrote the review or the code under review
(`../README.md`). This file is only the index, written by the integrator's assistant when the folder was archived: the
decisions, the fixes and their verification are in the part files. The review text is not edited.

**Part files.**
- `RESPONSE_instruments.md`: the instruments and the sweeps — F1–F4, F6–F12 and the instruments part of F16. Its
  «Changes for the integrator» also hold the texts for review LB1-p02-ux's Q3 (the sweep's side), X1, X7 and X9.
- `RESPONSE_framework.md`: the framework — F5 (its framework part: the carry hooks, the stored state, the notice, the
  checkbox's title), F13, F14, F15 and the framework part of F16. Its texts for the integrator and its final runs are in
  `../2026-11-11_internal_LB1-p02-ux/RESPONSE_framework.md` (one set for both reviews).
- `RESPONSE_p03.md`: F5's p03 part (atoms, molecules and the piston carried with their state; the world's random
  streams; p03's solver started at the scene's time).
- `RESPONSE_p04-p01.md`: F5's p04 part (the flow carried, `Flow2D.adopt`) and its p01 part (Kerr bodies' states across
  compatible laws).

## Decisions

| ID | severity | one line | decision | STATUS | part file |
|---|---|---|---|---|---|
| F1 | error | an object-parameter sweep did not apply the value equal to the stored one | fixed | V48 (i) (a flag equal to its stored value is not applied again; its row says so) | instruments |
| F2 | error | the sweep budget was not enforced inside one advance | fixed | — | instruments |
| F3 | should-fix | a deleted run's sweep kept running, could not be cancelled and held a server-wide place | fixed | — | instruments |
| F4 | should-fix | the cost estimate counted the runner's idle wait | partly fixed (the idle wait is gone; a frame's own cost still counts as advance: an upper bound) | V48 (c) | instruments |
| F5 | error | carry-over promised the state; objects without `object_state` and the world's own state restarted silently | fixed [error in earlier] | V42 (a), (f) updated | framework (hooks, storage, notice); p03; p04-p01 (p04, p01) |
| F6 | should-fix | any viewer could force `checkpoint_now` | fixed (403 over REST, refused over the WebSocket; the framework's test now expects 403) | — | instruments; framework (F16) |
| F7 | should-fix | a sweep did not state its sampling; the table's CSV omitted the base moment | fixed (the review's optional warning against a reported period not done: no world reports one) | — | instruments |
| F8 | should-fix | the «Приборы» panel lost focus, folds, scroll and form values | fixed (the column's jump was Playwright scrolling the clicked box into view: measured) | — | instruments |
| F9 | should-fix | sweeps sat outside the worker accounting | fixed (the GPU part not measured; a sweep not counted as a worker) | V48 (g) | instruments |
| F10 | should-fix | a double «✕ отменить» deleted what the first one kept | fixed (`POST …/sweeps/{n}/cancel`; `DELETE` only a finished sweep) | — | instruments |
| F11 | should-fix | a series CSV was formatted in the server's event loop | partly fixed (formatted in a thread; a smaller stall remains from the interpreter lock) | V48 (d) | instruments |
| F12 | nit | malformed request values gave 500 | fixed | — | instruments |
| F13 | nit | the edit's log line: no units, wrong gender; `asked` unvalidated; a «clamped» readout that did not clamp | fixed [error in earlier] | — | framework |
| F14 | nit | the automatic throw scale was anchored to the ceiling `velocity_max` | fixed (anchored to the scene's scale; ×1 not taken, with the reason) | — | framework |
| F15 | nit | carried objects were renumbered | fixed | — | framework |
| F16 | nit | test gaps | fixed | — | framework (F5, F13, F6's test); instruments (F1–F4, F6, F7, F9–F12) |

Also in this review: **R12** [error in earlier] — the instruments agent's proposed STATUS item «a run deleted during a
sweep ends that process within ~1 s» was not so before the processing; it is now (F3), and the proposal was withdrawn
(`RESPONSE_instruments.md`, «Changes for the integrator»).

Found while processing:
- p03's solver started at time 0 in a world built from a scene with a later time, so its first advance computed the
  whole interval [error in earlier]; a hard-sphere world given a molecule, a piston, a thermostat or a field through a
  file or a carry raised an `AttributeError`, now refused in Russian (`RESPONSE_p03.md`);
- a new Kerr–Newman world of another spin or charge refused every carried body, and one of another mass kept the proper
  times in the old unit of M without a word (`RESPONSE_p04-p01.md`);
- the hand's speed is named also when the player's rounded speed is clamped again by a hair (F13, found by the browser
  run).

## Totals

16 findings (3 errors, 8 should-fix, 5 nits):
- **14 fixed**: F1–F3, F5–F10, F12–F16;
- **2 partly fixed**, the remainders in STATUS: F4 → V48 (c), F11 → V48 (d);
- **0 rejected, 0 deferred**; also recorded in STATUS: F9's untested CPU default on a GPU host → V48 (g), F1's flag
  case → V48 (i).

By part file, as each states it: instruments — 9 fixed (F1, F2, F3, F6, F7, F8, F9, F10, F12), F4 and F11 partly, F16
(instruments part) fixed; framework — 5 fixed (F5 framework part, F13, F14, F15, F16 framework part); p03 — F5 (p03)
fixed; p04-p01 — F5 (p04 and p01) fixed.

STATUS items opened or changed by this review: V48 (c), (d), (g), (i) (with (e), (f), (h) from the implementation);
V42 (a), (f) (scenes carried into a new world with their state).
