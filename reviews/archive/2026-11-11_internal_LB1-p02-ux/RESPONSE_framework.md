# Response to review LB1-p02-ux — the framework part (X2, X3, X4 fw, X6, X8, X12 fw, X13 fw)

**Responder:** the framework processing agent of LB1 (lf-lpf-, a different agent from the reviewer and from the authors of
the code). **Date:** 2026-11-11/12. Part A (Q1–Q11), X5, X10, X11 and the p02 part of X12 are answered by the p02 agent
(`RESPONSE_p02.md`); X1, X7, X9 by the instruments agent; the p03 and p01 parts of X4 and X14 by their agents.

**Counts (this file):** 7 findings — 6 fixed, 1 partly fixed (X3: the form shows the new world's laws; defaults derived
from what the carried scene needs are p02's knowledge, left to the p02 agent), 0 rejected, 0 deferred.

**Environment.** As in `../2026-11-11_internal_LB1-framework/RESPONSE_framework.md`: CPU only, private server
`lf-lpf-srv` on port 8612 (`--memory=6g`, 3 workers), Playwright 1.58.2 Chromium with SwiftShader, 1600×1000 and 1280×800.
The browser check of this response is `response_checks_framework/ux_fw.mjs`. It was run on the code before the fixes
(`ux_fw_before.out`: 18 of 20 checks failed) and after (`ux_fw_after.out`). Screenshots `before_*.png` / `after_*.png`
are in the same folder (looked at; described below).

## Findings

### X2 — error — Delete did not delete in p02's plane window; it showed «Срез не построен»

**Status:** fixed [error in earlier] — the panel's help says «Delete — удалить».

**Reproduced** (`ux_fw_before.out`, both sizes): the detector picked in the window (`sel o2`, `slice 1`), Delete →
0 scene removes, 2 view commands, the toast «Срез не построен: у этого мира нет запросов просмотра». A Delete with
nothing of the scene selected also sent a view remove.

**Cause.** One gesture selected two things.
- The press on the object was the manipulator's: it selected the object and deselected the plane.
- The window's own `click`, after the release, selected the window again: plane 1, the 2-D world's own plane.
- The playground then gave the key to the selected plane.
- `env3d` sent `view {op: remove}` for a plane that the world never accepts removing.

**Fix.**
- `player/js/slices.js`: a gesture the manipulator took does not also select the window; `isFixedWindow(id)` tells the
  world's own window (`meta.fixed`).
- `player/js/env3d.js`: Delete never sends a remove for a fixed window.
- `player/js/playground.js`: Delete is the object's, unless a removable slice plane was selected after it.

**Verification** (`ux_fw_after.out`, 1600×1000 and 1280×800):
- the object picked in the window: 1 scene remove, 0 view commands, no «Срез не построен»;
- negative control, a Delete with only the world's window selected: nothing removed, nothing sent;
- `manipulation.mjs`: Delete in the toy's 3-D view still removes.

**Screenshots.** `before_X2_delete_*.png`: the toast «Срез не построен», the detector still there.
`after_X2_delete_*.png`: the detector gone, «Удаляется «Экран»…».

### X3 — should-fix — «Новый мир» into the other dimension offered no grid or window

**Status:** partly fixed.
- Fixed: the form shows the new world's laws.
- Not done here: proposing grid values from what the carried scene needs (the same step, a cube over the scene). That
  is p02's knowledge of its grid; it is left to the p02 agent (PQ), who can also make the carry-over refusals name the
  value to choose.

**Reproduced** (`ux_fw_before.out`): with «объём» chosen, the form's labels were only «Сценарий, перенести сцену,
Пространство, Затравка случайных чисел». The live laws were hidden but were still sent with the current world's values.

**Fix** (`player/js/player.js` `renderWorldPanel`).
- One form holds every law of the new world. The laws that also change on the go start at their values in this world
  now, and their group is marked «— меняются и на ходу (сейчас как в этом мире)».
- One form is used so that a law shown only for some values of another law appears: the 3-D grid appears when the
  space is chosen.
- Exactly the form's values are sent, with or without a scenario.

**Verification** (`ux_fw_after.out`, both sizes): with «объём (x, y, z)» chosen, the form shows «Точек сетки по оси»,
«Размер окна, нм», «Края окна». `after_X3_form_*.png` and `after_X8_new_world_1280x800.png` show the form.

### X4 (framework part) — should-fix — the default throw was absurd, and nothing said «уменьшите масштаб броска»

**Status:** fixed (framework part). The sections declare `velocity_max` (p03, p01: their agents).

**Fix** (`player/js/playground.js`).
- **The automatic scale** comes from the world's own scale. A brisk flick (the view's width in a wall second) throws
  across the world's region in 2 wall seconds at the current playback rate, never above half a declared
  `velocity_max`. Before, it was ×1 without `velocity_max`, and half the ceiling with it (LB1-framework F14).
- **A clamp** says so in the readout («— ограничено до 12 м/с: уменьшите масштаб броска») and in the log.
- **A throw the world refuses** is followed by a notice: «Бросок не принят. Бросьте медленнее или уменьшите масштаб
  броска (сейчас ×…) — поле «Бросок (Shift): масштаб ×» в панели «Объекты сцены»».

**Verification.**
- `manipulation.mjs` 4b: the automatic throw matches the rule at both sizes.
- `manipulation.mjs` 4c, 4d: the clamp texts; a resting pointer does not keep a stale clamp.
- The p01–p04 drags and throws in `manipulation.mjs` (final run below): applied or refused, with the ghost snapping
  back.
- Added at the integrator's request (2026-11-12) for p03, whose throws arrive in nm/s while its parameters read m/s: an
  optional handle `velocity_display = {"unit", "factor"}`.
  - It is validated when the palette is built: the two keys only, a short non-empty unit, a finite factor > 0, and a
    velocity handle.
  - The factor turns the world-unit velocity into the shown one, in the readout and in the log line, the clamp included.
    The edit, the world and `velocity_max` stay in world units.
  - Tests: `test_handles_are_checked_against_the_type_and_sent_in_the_palette` (10 malformed declarations refused);
    `test_a_throw_is_logged_in_the_unit_the_type_shows` (negative control: a type without it logs its parameter's
    unit); `manipulation.mjs` 4e on the toy's cloud (in cm/s): readout «(−249; 135) см/с» against the sent
    `vx = −2,49` m/s, at both sizes.

### X6 — should-fix — velocity units and number formats were inconsistent (the player's formatting)

**Status:** fixed (the player's and the framework's formatting).
- p02's choice of «нм/с» for its velocity parameters is p02's (its agent).
- p01's own event texts are p01's; they can use `lfviz.playground.fmt`, below.

**Fix.**
- `player/js/ui.js` `num`: one Russian form everywhere — a decimal comma also in the mantissa of m·10ⁿ, the minus sign
  −, a mantissa rounded to 10 carried into the exponent. «Приборы», the readouts and the windows all use it.
- `server/lfviz/playground.py` `fmt`: the same rule on the server, for the framework's log lines and the sections'
  texts. «9.98·10¹³», «1e+14» and «-1,5» become «9,98·10¹³», «1·10¹⁴» and «−1,5».
- The throw readout shows as 0 a component below a millionth of the vector's length (the arithmetic's round-off).
  Before, the readout showed «(3.25·10¹³; −9.76·10¹²; −0,137)».
- The readout's unit is the velocity parameter's (or the one its label carries).

**Verification.**
- `test_the_log_lines_and_numbers_are_in_the_players_form`: `fmt` against the player's form, with a negative control.
- The throw readouts in `manipulation.mjs` («бросок: v = (−0,128; −0,0341; 0,103) м/с (×1,5)»).

### X8 — should-fix — the top bar wrapped, and toasts covered each other

**Status:** fixed.

**Reproduced** (`ux_fw_before.out`):
- the bar was 77 px high in 4 rows after «Новый мир» added the world selector, at both sizes;
- three toasts had 3 overlaps;
- the carry-over's two notices were drawn on top of each other (`before_X8_new_world_1280x800.png`).

**Fix.**
- `player/run.html`: the bar keeps one row. The title, the subtitle, the badges and the world selector shrink with an
  ellipsis (the full text in their tooltips), and the buttons never shrink.
- `player/assets/chrome.css` and `player/js/ui.js` `toast`:
  - one stack at the bottom right, the newest on top, 6 px apart, at most 6;
  - each toast stays at least its time and about 70 ms per character, and longer while the pointer is on it;
  - ✕ or a click closes it.

**Verification** (`ux_fw_after.out`, both sizes):
- the bar is 42 px in one row in p02, with the world selector, and in p01, with nothing pushed out;
- injected toasts and the carry-over's notices have 0 overlaps.
- Screenshots:
  - `after_X8_new_world_*.png`: the bar in one row with «Мир 2 (текущий): кван…». p02 now reports its adaptations
    through the framework's one notice, which is fully readable.
  - `after_X8_toasts_*.png`: four toasts stacked, the newest on top.
  - `before_X8_*.png`: the bar in two rows and the toasts piled on each other.

### X12 (framework part) — nit — event texts

**Status:** fixed (framework part). p02's own texts («(не изменилась (до округления))», «волна пересчитана точно») are
the p02 agent's.

**Fix.**
- `server/lfviz/playground.py`:
  - the edit line is «Электрон»: перемещение в (−10,81; 8,378) нм; бросок: v = (…) нм/с» (no labels with their help
    inside the brackets; a noun, so no gender to agree);
  - the set line is «Стенка 1»: Положение = −1,5·10⁻⁵ м; Ось: y» (the label without its bracketed explanation, a
    select by its option's name, the unit when the label lacks it).
- `server/lfviz/sim.py`: a `set` or an `action` that returns no text makes no empty line in «События». Scene changes
  already skipped them.

**Verification.** `test_manipulation.py`: exact lines, and a no-op set logs nothing.

### X13 (framework part) — nit — axes

**Status:** fixed (framework part). The time unit of an empty plot in «Приборы» is `instruments.js`, the instruments
agent's.

**Fix.**
- `player/js/slices.js`, the windows' axes: ticks at round values (steps 1, 2, 5 × 10ⁿ, rounded up so that labels are
  never closer than 64 px across and 36 px up). Every label stays inside the window; the last one is shifted left
  instead of being clipped («39,»).
- `player/js/scene3d.js`, the 3-D box: its two ends and, between them, round values (before: −20,3; −0,625; 19,1).

**Verification** (`ux_fw_after.out`): window 1 of p02 has 1-2-5 ticks on both axes (e.g. −40 … 30 by 10 at 1280×800),
and the last label's right edge is inside the window. `after_X8_new_world_1280x800.png` shows the window's round ticks.

## Final runs

All on the CPU in Docker, after the last code change of this processing. Other agents were editing p01–p04 at the same
time. Outputs are in `response_checks_framework/` (the browser check of this file) and
`../2026-11-11_internal_LB1-framework/response_checks_framework/` (the sections' carry-over).

| run | result | status |
|---|---|---|
| `tests/test_server.py test_playground.py test_restore.py test_checkpoint.py test_manipulation.py test_carryover.py` | 128 of 131 passed in one run (17 min) beside the browser suite. The 3 others passed alone: `test_run_list_follows_the_worlds_approximations` (v08 takes 92 s alone, against its 120 s per-message timeout, so it times out under the parallel load); `test_checkpoint` p02 and p03 (both pass; the earlier diff came while those sections' files were being edited, as seen before in this batch). After the last change (`velocity_display`): `test_playground`, `test_restore`, `test_manipulation`, `test_carryover` re-run, all passed | [useful] |
| `tests/browser/manipulation.mjs` p99_toy, 1600×1000 and 1280×800 | 48 of 48 | [useful] |
| `tests/browser/manipulation.mjs` p01–p04, both sizes | 38 of 38 | [useful] |
| `tests/browser/keyframes.mjs` (every visualization and playground) | all equal | [useful] |
| `tests/browser/scene3d_checks.mjs` | all passed | [useful] |
| `response_checks_framework/ux_fw.mjs`, both sizes | before the fixes: 18 of 20 failed (`ux_fw_before.out`); after: 20 of 20 (`ux_fw_after.out`) | [useful] |
| `../2026-11-11_internal_LB1-framework/response_checks_framework/f5_carry_sections.py` (p03, p04) | each object and the world's state said as it went (see that file's RESPONSE) | [useful] |

One run of `manipulation.mjs` beside the full pytest failed 4 checks: the two timing-based throw speeds on the toy, at
both sizes. That run took 1.85 s for 14 pointer moves, so the pointer rested longer than the 100 ms window between
moves and the measured throw was near zero. The same checks passed in the quiet runs (46/46, then 48/48). The sent
velocity does not depend on the readout's refresh. [neutral]

## Changes for the integrator

One set for both reviews (LB1-framework F5, F13, F14, F15; LB1-p02-ux X2, X3, X4, X6, X8, X12, X13). I did not edit
STATUS, RULES, PLAN or the owner guide. The texts below are exact.

### 1. `visualizations/RULES.md` §6 — three bullets after the bullet «**The scene** is changed by hand …»

```
* **A new world that keeps the scene** (plan P16.1, «перенести сцену»; reviews LB1-F5, LB1-F15): `new_world` with
  `carry` re-adds the current world's objects in the new world under their ids, through `place` and the add path, at
  the current world time; an object the new world refuses is skipped. A scene file holds only what `object_state`
  gives as JSON. A section whose state is large gives it for a carry through `carry_state() -> {"objects": {id:
  state}, "world": state}` (plain data and NumPy arrays of numeric or bool type) and takes it in `on_add(obj, state)`
  and `carry_world(state, laws)` (called once in every carried world, `state` None when the old world gave none;
  raising starts the world's own state afresh); `carry_note(text, obj=None, restarted=False)` says what was adapted or
  started afresh, and `self.carrying` holds the old world's laws during the carry. The runner writes the heavy state
  once into the run's checkpoint folder as `carry-w<N>-<ns>.npz` (read with `allow_pickle=False`, never unpickled) and
  names it with its SHA-256 in the new world's `params["scene"]["carry_file"]`: a restore by replay reads the same
  state and refuses when the file is missing or changed; a scene file never names one; only the latest world's file is
  kept. The notice of a carry (recorded) says object by object what went with its state, what was rebuilt from its
  parameters (no state of its own — `ObjectType.stateful`, by default the types with a velocity handle — or a state
  not carried, with the reason), which values the new world changed, what it refused, and what happened to the
  world's own state; its `carry` field holds the same as data. The «Новый мир» form shows every law of the new world,
  the live ones at their current values.
* **Direct manipulation: the throw and Delete** (plan P16.2; reviews LB1-F13, LB1-F14, LB1-p02-ux X2, X4): the
  automatic throw scale makes a brisk flick (the view's width in a wall second) cross the world's region in 2 wall
  seconds at the current playback rate, never faster than half the `velocity_max` a type declares (which clamps); a
  clamp and a refused throw say «уменьшите масштаб броска». The scene's log names an edit as «‹label›: перемещение в
  (…) ‹unit›; бросок: v = (…) ‹unit›» and says a clamp only when one happened. A type whose throws are better read in
  another unit than the world's declares `velocity_display = {"unit", "factor"}` (factor × world velocity = shown; the
  readout and the log only, the edit stays in world units). Delete removes the selected object also when it was picked
  in a 2-D world's own window (that window is never removed).
* **Numbers in the owner's texts** (review LB1-p02-ux X6): one form, `lfviz.playground.fmt` on the server and `ui.js`
  `num` in the player — a decimal comma also in the mantissa of m·10ⁿ, the minus sign −. Sections format the numbers
  of their events and refusals with `fmt`.
```

### 2. `visualizations/README.md` (owner guide) — the section «Плейграунд: исследовательские песочницы», two items added to the list «В плеере плейграунда слева» after «**Объекты сцены**»

```
* **Перетаскивание и бросок** — объект выбирается щелчком в сцене или в окне среза, перетаскивается мышью (изменение
  применяется при отпускании, в текущий момент мира); Shift + перетащить — бросок. Масштаб броска «авто» подобран по
  самому миру: быстрый взмах (ширина вида за секунду) бросает объект через всю область мира примерно за 2 секунды при
  текущей скорости воспроизведения, но не быстрее половины наибольшей скорости, которую мир объявил. Если бросок
  ограничен этой скоростью или мир его не принял, плеер так и пишет: «уменьшите масштаб броска». Delete удаляет
  выбранный объект, в том числе выбранный в окне плоского мира; Esc отменяет перетаскивание;
* **Новый мир с переносом сцены** — в форме «Новый мир» видны все законы нового мира, в том числе меняющиеся на ходу
  (сетка, окно, края — с их текущими значениями). С галочкой «перенести сцену» объекты переходят в новый мир с теми же
  номерами, время продолжается. Сообщение после переноса говорит по каждому объекту: перенесён с состоянием, по
  параметрам (своего состояния у него нет), состояние не перенесено и начато заново из параметров (с причиной),
  что изменено при переносе, что новый мир не принял — и что стало с состоянием самого мира (например, течение
  перенесено или начато заново из покоя);
```

and one sentence at the end of the paragraph «Справа — проверки законов сохранения …»:

```
Сообщения и отказы появляются справа внизу стопкой, новое сверху; каждое держится, пока на нём курсор, и закрывается
щелчком.
```

### 3. `STATUS.md`

Nothing to defer from this file. One remainder goes to the p02 agent, not to STATUS: X3's grid defaults from what the
carried scene needs. If the p02 agent leaves it open, this is the text for its open list:

```
p02, «Новый мир» in the other dimension with «перенести сцену»: the form shows the grid and the window (review
LB1-p02-ux X3, framework part fixed), but proposes no values from what the carried scene needs (the same step as now, a
cube over the scene's extent); the owner sets them by hand from the refusals' texts.
```

### 4. What the integrator must know

- The carry-over hooks were sent to the section agents on 2026-11-11, and their shape did not change after that.
  - p03 and p04 use them already (`../2026-11-11_internal_LB1-framework/response_checks_framework/f5_carry_sections.out`).
  - p02 uses `carry_note` and `carry_world`: its adaptations and its random stream appear in the one notice
    (`response_checks_framework/after_X8_new_world_*.png`).
  - p01's bodies carry through `object_state` as before.
- The optional handle `velocity_display` was added on 2026-11-12 at the integrator's request for p03. Its shape was
  sent to the coordinator.
- The notice's wording changed: the parts are sentences («С состоянием — …», «По параметрам (своего состояния нет) —
  …», «Не перенесены: …», «Состояние мира перенесено: …» / «Состояние мира: …»). No section test asserted the old one;
  the toy's tests and `manipulation.mjs` assert the new one.
- The toy section `tests/playgrounds/p99_toy` gained a type «cloud» and a world measurable «visits». It is the
  reference of the hooks; only the framework's tests use the toy.
- `ui.js` `toast()` now puts the toasts in one `.toasts` stack and returns the element. A toast's `textContent` begins
  with «✕» (its close mark); tests that compare whole texts must allow for it, and those in the repository match with
  regular expressions.
- Test hooks: `window.__lfManip.released()` (the throw readout at the last release); `.s3d-windows.__slices.ticks(id)`
  and `.isFixed(id)`.
- F6 (instruments agent's change): `test_checkpoint_now_through_a_worker_and_never_resuming` now expects 403. The
  player sends no `stop` through `/command`.
- Carried state files live in each run's `checkpoints/` folder (`carry-w<N>-<ns>.npz`) and count in the run's disk size
  and the record window's size.
