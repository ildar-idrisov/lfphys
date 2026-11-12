# Response (framework and player) to review UX-3d: the playground's part of A6

Processed on 2026-11-05 by the subagent that processed the framework's findings of the sibling reviews UX-ui and
UX-params. It wrote neither this review nor the code under review. The review text is unchanged. The rest of A6, and
A1–A19, are in `RESPONSE.md` (the 3-D agent's). This file adds only what A6 asks of the playgrounds' panels: «a «◎» button
"centre on the selected object" and a "follow" toggle», built on the scene's own `scene3d.centerOn(p)` that the 3-D
agent left for it.

| ID | one line | decision | where | verified by |
|---|---|---|---|---|
| A6 (playgrounds) | No "centre on the selected object" and no "follow" in the playgrounds | **fixed** | see below | see below |

**Changes.**
- **The object list** («Объекты сцены»): every row gets «◎», which puts the 3-D view's centre of rotation on that object
  and keeps the direction of view. A «👁» mark shows which object the view follows.
- **The inspector:** «◎ Центрировать» and the «👁 Следить» toggle, which keeps the centre on the object while it moves,
  live and when the history is scrubbed.
- **When following stops:**
  - the owner turns or pans the view by hand (a toast says so); a wheel zoom keeps following;
  - the object is removed;
  - another object is selected;
  - another world is shown.
- **Where an object is**, in order:
  1. the frame's `at[id]` when the section sends it;
  2. else the frame's `ids` with its array `pos`, one point per id, as p01's bodies;
  3. else the object's set x, y, z.
  The world agents may add `at` for objects whose moving centre is known only to them, e.g. p02's packets; see
  «API for the world agents» in `../2026-11-04_internal_UX-params/RESPONSE_framework.md`.
- The player gives the views the arrays of the frame shown (`ctx.frameBlobs()`).
- `scene3d.js`, `env3d.js` and `chrome.css` are not touched; the controls' styles are in `run.html`.

**Files.** `visualizations/player/js/playground.js`, `player.js`; `visualizations/player/run.html`.

**Verified.** In the browser (`response_checks_framework/cases_extra.mjs`, case `a6_center_follow`; output
`out_a6.json`; screenshot `shots/after_a6_follow_p01_1600.jpg`, looked at: the Earth at the view's centre, the «👁»
mark, «Следить» on). The world is p01 «Солнце и Земля», recording at 1 year per second.
- «◎ Центрировать» on «Земля» moved the pivot from (0.01, −0.20, −0.29) to (0.32, 0.95, 0): 1.000 а.е. from the Sun.
- With «Следить» on, six samples 0.7 s apart stayed 1.000 а.е. from the Sun at different angles.
- A wheel zoom (camera distance 6.42 → 5.23) kept following.
- A drag that turned the view switched it off, with the toast «Слежение за объектом выключено: вид повернули или
  сдвинули вручную».
- Switched on again, then the Earth removed: it stopped, with no «👁» left.

Not covered here, as in the 3-D agent's STATUS text: dragging objects, and velocity handles (UX-ui U11).
