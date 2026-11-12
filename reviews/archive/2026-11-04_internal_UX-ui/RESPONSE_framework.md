# Response (framework and player) to review UX-ui (2026-11-04)

Processed on 2026-11-05 by a subagent (Claude) that did not write the review. This file covers the findings assigned to
the framework and the player UI:

- **U1** except the 3-D camera's own refit in `scene3d.js`, which is the 3-D agent's;
- the UI side of **U4**;
- **U9, U10, U13, U14, U16, U17, U20, U21, U22, U23, U24**.

The other findings (U2, U3, U5–U8, U11, U12, U15, U18, U19 and the worlds' halves of U4, U13) are the world agents' and
the 3-D agent's, in their own response files in this folder. The review text is unchanged.

**Environment, evidence and tests** are the same as in `../2026-11-04_internal_UX-params/RESPONSE_framework.md`: a
private server on port 8572 (CPU, `LFVIZ_PLAYGROUND_CKPT=6`, segments every 6 s), and Chromium with SwiftShader at
1600×1000 and 1280×800. `response_checks_framework/` holds the browser script (`fw_ui.mjs`, `cases_extra.mjs`), its
outputs before and after (`out_before.json`, `out_after.json`) and the screenshots (`shots/before_*`, `shots/after_*`,
looked at). The **API for the world agents** and the **changes for the integrator** (STATUS V45, RULES §3 and §6) are
in that file and cover both reviews.

## Decisions

| ID | one line | decision | where | verified by (`out_after.json`, `shots/after_*`) |
|---|---|---|---|---|
| U1 | Things jump back to where they started | **fixed** (the three parts assigned here); the camera's refit on a grown box is the 3-D agent's (A7) | `playground.py`, `player.js`, `playground.js`, `v04_orbits/web/view.js` | see «U1» below |
| U4 | The palette places only with defaults, at a fixed spot | UI side **fixed**; free spots and sides are the world agents' (`place`) | `playground.js`, `slices.js`, `playground.py`, `run.html` | see «U4» below |
| U9 | No feedback while a scene command computes | **fixed**, with a cancel | `sim.py`, `worker.py`, `runs.py`, `app.py`, `player.js`, `playground.js`, `run.html` | see «U9» below |
| U10 | The inspector loses the focus after every change | **fixed** | `playground.js`, `ui.js` | see «U10» below |
| U13 | Refusals speak the engine's language | framework part **fixed**; each section's own English refusals are its agent's (they raise `Refusal`) | `params.py`, `errors.py` (new), `sim.py`, `worker.py`, `app.py` | see «U13» below |
| U14 | «События» rebuilt on every drawn frame | **fixed** | `player.js` | see «U14» below |
| U16 | The checks panel is a wall of notes; cut at 1280 px | **fixed** | `player.js`, `run.html` | see «U16» below |
| U17 | «Прежние группы проверок» closes itself | **fixed** | `player.js` | see «U17» below |
| U20 | At 1280×800 the demonstrations are cramped | **partly fixed**: the frame is done; v07's own 2×2 layout → STATUS V45 (a) | `run.html`, `player.js` | see «U20» below |
| U21 | Slice tools in worlds without slices | **fixed** | `player.js`, `run.html` | see «U21» below |
| U22 | A disabled palette button does not say why | **fixed** | `playground.js`, `run.html` | see «U22» below |
| U23 | An empty «Действия» first; «Новый мир» open | **fixed** | `player.js` | see «U23» below |
| U24 | 9 px speed labels; the bottom bar wraps | **fixed** | `run.html` | see «U24» below |
| UX-3d A6 (playgrounds) | No «centre on the selected object» and no «follow» | **fixed** (on the integrator's request) | `playground.js`, `player.js`, `run.html` | see «UX-3d A6» below |

### U1 — the view and the list stay where the owner put them

1. **A playground re-sent an unchanged `box` every segment.** The segment must stay drawable on its own, so the box is
   still repeated. The base's repetitions are now marked `repeat: true` (`playground.segment_start`). The player
   (`player.js`, `sameAsHeld`) does not give a view a repeat equal to the message of the same type and id that the
   world's record already holds; a viewer whose record starts at that segment has none and gets it.
   - Browser `u1_repeat`, p01 «inner» with segments every 6 s: after a wheel zoom from 34.0 to 121.1 px/а.е., 20 samples
     over 20 s stayed 121.1. 12 repeats were dropped (before: back to 28.2 at the next segment, review `camera.jsonl`).
   - `test_a_segment_start_repeats_what_a_view_holds_and_changes_nothing` checks the mark.
2. **v04 refitted after a step back.** `fittedSeg` is kept through `reset` and `restore` of the same world. The plane is
   fitted once, when a new launch first appears; a new world fits again.
   - Browser `u1_v04`: after a wheel zoom, ⏮, ⏭, a click on the timeline and ⏭, `Plane.fit` was called 0 times.
   - Before: refitted (the review's `camera_v04_after_scrub.jpg`).
3. **The object list jumped to its top.** The list is kept and its rows are updated in place (added, removed,
   reordered, relabelled). A selection made from the scene scrolls its row into view; one made in the list does not.
   - Browser `u1_u10_u21_u23`, p01 with 20 more bodies: `scrollTop` 419 before the click, 419 after it, and 419 after
     another body was added. Before: 419 → 0.

### U4 — set the parameters and the point before placing

**Changes.**
- A palette button now opens a pre-placement form: the type's parameters, with their `show_if`; «Поставить»; «Отмена».
  Shift+click places at once with the defaults, as before.
- «⌖ Указать место в сцене» arms a one-shot pick:
  - a click in the 3-D view gives the point of the plane z = the middle of the region under the pointer. The plane's
    image is a homography of four of its points, through `scene3d.screenOf`, inverted;
  - a click in a slice window gives that point of its plane (`slices.armPick`).
- The point fills x, y, z and is sent as `position` to the section's `place(kind, values)`, the integrator's API. The
  section moves it to a free spot or refuses, in Russian. Without `place` the values are used as they are.
- The free spots, free sides and the toast on a merge are the world agents' (`place`, `notify`).

**Verified.**
- Browser `u4_place` (p01): the clicked point drawn back by the scene lands within 1 px of the click (883,454 →
  882,453 at 1600; 706,383 → 706,383 at 1280). The placed «Пробное тело» has those coordinates in the inspector
  (`after_u4_place_form_p01_1600.jpg`, `_1280.jpg`, `after_u4_placed_p01_1600.jpg`).
- p02's form is in `after_u4_place_form_p02_1600.jpg`.
- Python: `test_place_palette_state_and_removals_asked_first` (`place`, `position`, a refusal adds nothing).

### U9 — what is being computed, for how long, and a way out

**Changes.**
- Every computing command (step, ⏭ событие, set, action, view, scene, new world) and the first world's build are
  announced by the worker with `busy` (what, when). These notices are not recorded; a late viewer gets the current one
  with its elapsed seconds.
- The command's messages are held and written after the end notice, as one piece.
- The player shows «⟳ <что> · N с» after 0.3 s, and «✕ отменить» after 1 s. While the world computes, the palette and
  the copy and remove buttons wait, so repeated clicks no longer queue. The inspector stays editable (U10).
- A cancel (`POST /api/runs/{id}/cancel`) ends the worker. Everything it writes after the cancel is decided is dropped,
  so the command leaves nothing in the record. The run is then resumed from its record, i.e. the world as it was just
  before the command, and «Отменено: …» is said.

**Verified.**
- `test_a_computing_command_is_announced_and_written_as_one_piece`, and `test_cancel_puts_the_world_back_to_just_before_the_command`
  (the run is resumed, no new header, the notice).
- Browser `u9_cancel_v08`, a new v08 world, tens of seconds on the CPU:
  - «создаётся новый мир · 4 с ✕ отменить»; after ✕ the run still has one world, the notice «Отменено: …», and the
    world resumed (`after_u9_busy_v08_1600.jpg`, `after_u9_after_cancel_v08_1600.jpg`);
  - the first build is shown as «строится мир · N с».
- Before (`out_before.json`, u9_p02): nothing was shown for 12.8 s while recording, and the status said «запись идёт ·
  вживую». p02's palette additions are now fast (the p02 agent's U3), which is why the slow v08 new world serves as the
  demonstration.

### U10 — editing several fields in a row

**Changes.**
- The inspector is rebuilt only when another object, its type or what may be edited changes. Otherwise its controls
  take the new values in place, and a rebuild gives the focus back to the same field.
- Sliders are out of the tab order (`ui.js`), so Tab goes from field to field.

**Verified.** Browser: «Масса» = 2, then Tab → the focus is on «Радиус» (a number field), and it is still there after
the world's scene message (`focus_after_tab`, `focus_after_scene_msg`). Before: the slider, then `BODY`.

### U13 — refusals in the owner's terms (framework part)

**Changes.**
- The schema's texts name the parameter by its label and unit, give the allowed range, and say «поле пустое…».
  Live refusals are said under the control before anything is sent.
- The runner's prefixes say what was not done: «Изменение не применено», «Сцена не изменена», «Действие «Толчок» не
  выполнено», «Срез не построен», «Новый мир не создан», «Мир не создан».
- Other exceptions become one Russian sentence with the integrator's wording. The engine's own sentence is kept as the
  folded `detail`, and the traceback only in `worker.log`.
- Known English library sentences are translated.
- `Refusal(text, hint)` is the helper the sections use for their own refusals. p03's English wall and piston refusals,
  p02's «яма −3 эВ» and p04's dt advice are their agents'.

**Verified.** `test_parameter_refusals_are_in_the_owners_words`, `test_owner_text_of_refusals_and_failures`, and browser
`p2_live` and `p2_catalogue`. Before: «Изменение не применено: lam_nm: 2000.0 > max 1600.0».

### U14 — clicks on «События» while recording

**Changes.** «События» is rebuilt only when its list changes: a new world, or the list trimmed. New events are appended,
and the «будущее» marks are toggled in place.

**Verified.** Browser `u14_u17`, v04 at 0.1 s/s while recording: 0 rebuilds per second (before: 14), and 4 of 4 human
clicks (150 ms) jumped (before: 0 of 4).

### U16 — one line per check

**Changes.**
- Each check is one line: the label wraps, the value has its reference under it, and the ✓ / ✗ column is fixed-width.
  The note is behind «ⓘ» and in the line's tooltip.
- Each group has a summary («3 ✓ · 1 ✗»). A group folds; it is open when it is the newest or has a failure, and an
  owner's choice is kept.
- The table has fixed column widths and does not scroll sideways.

**Verified.** Browser `u16_u20`:
- v04's checks panel is 218 px at 1600 (587 before) and 268 px at 1280 (654 before);
- the right column is 299/299 px at 1280 (309/299 before: the ✓ column was cut), and v07 is 299/299 (306/299 before)
  (`after_u20_v04_orbits_1280.jpg`, `before_u20_v04_orbits_1280.jpg`).

### U17 — «Прежние группы проверок» stays open

**Changes.** Its open state is kept across renders.

**Verified.** Browser: sampled every 250 ms for 4 s, `1111111111111111` (before: `1111110000000000`).

### U20 — room at 1280×800

**Changes.**
- ⇤ and ⇥ in the top bar, and the keys [ and ], fold the side columns away; the centre takes the room. The choice is
  kept per browser.
- The modified-physics and approximation badges are cut to one line, with the full list on hover. The run's id is
  hidden below 1500 px (it is in «О запуске»).
- The bottom bar fits in one line at 1280 and 1600 px (43 px; before 67 px at 1280, and wrapped at 1600 in p02 and p04).
- The right column fits its table (U16).

**Verified.** Browser `u16_u20`:
- the bottom bar is 43 px everywhere;
- v04's main canvas at 1280 is 431×581, 24.5 % (431×557, 23.4 % before), and both columns folded give the measurements
  in `out_after.json` (`*_1280_folded`);
- `after_u20_*` screenshots.

**Left open.** v07's 2×2 panels print their labels over each other at narrow widths. That is the view's own layout (the
v-worlds agent) → STATUS V45 (a).

### U21 — no slice tools without slices

**Changes.**
- A 3-D world whose header has `planes.max = 0` gets the class `no-slices`: «✥ Двигать» and «⟳ Наклонять» are hidden.
- One that has, besides, no volume, vectors, target or panel to scale gets `no-field`: the brightness-scale selector is
  hidden.
- The rules are in `run.html`, and `scene3d.js` and `env3d.js` are not touched. The hint no longer speaks of slices (the
  3-D agent's text).

**Verified.** Browser: p01's toolbar is «Изо, Сверху, Сбоку, 📷» at both sizes. Before: «амплитуда…, ✥ Двигать, ⟳
Наклонять, Изо, Сверху, Сбоку, 📷».

### U22 — why a palette button is off

**Changes.**
- A button disabled at its limit says «не больше N в сцене» (or «в сцене уже 300 объектов»).
- A type the world cannot take now (the section's `palette_state`) is disabled with the world's reason, as the tooltip
  and in small text under the button.

**Verified.** Python: `test_place_palette_state_and_removals_asked_first`. The browser rendering is in `playground.js`
`typeWhy`. No section emits `palette_state` yet, so the browser check waits for the world agents.

### U23 — the playground's left column

**Changes.**
- «Действия» is hidden when the world has no actions at the cursor.
- «Новый мир» is closed in playgrounds.
- A playground's live laws appear first, as «Законы мира — меняются сразу» (integrator, 2026-11-05).

**Verified.** Browser: p01 shows «Законы мира — меняются сразу», «Палитра», «Объекты сцены», «Инспектор» …, «▸ Новый
мир». «Действия» is present in the DOM but hidden: the panel list in `out_after.json` lists it, and the screenshot
`after_u4_place_form_p01_1280.jpg` does not show it.

### U24 — readable labels, one bottom line

**Changes.** The speed scale is 11 px (9 px before). The bottom bar's minimum widths are smaller and it does not wrap
(U20).

**Verified.** Browser: `tick_font` is 11px in all four worlds at both sizes.

### UX-3d A6 (the playgrounds' part, on the integrator's request): centre on and follow the selected object

**Changes.**
- The object list gets «◎» per row, and the inspector gets «◎ Центрировать» and the «👁 Следить» toggle, on the
  3-D agent's `scene3d.centerOn(p)`.
- Following stops when the view is turned or panned by hand (a wheel zoom keeps it), when the object is removed, when
  another object is selected, or when another world is shown.
- The position comes from the frame (`at[id]`, or `ids` with `pos`), else from the object's set x, y, z.
- Recorded in `../2026-11-04_internal_UX-3d/RESPONSE_framework.md`.

**Verified.** Browser `a6_center_follow` (p01 «Солнце и Земля»): the pivot goes to the Earth (1.000 а.е. from the Sun)
and follows it around the orbit. A zoom keeps following; a turn by hand stops it, with a toast; so does a removal
(`shots/after_a6_follow_p01_1600.jpg`).

## Tests run

- Framework tests: `tests/test_server.py`, `test_playground.py`, `test_restore.py`, `test_checkpoint.py` and
  `v04_orbits/tests`, 172 passed, on the final code. `response_checks_framework/tests.out` and the UX-params response
  give the details and one earlier run that met two worlds being edited.
- `tests/browser/keyframes.mjs` for all 21 worlds and the extra runs (v02 vector, v09 lab) on the private server with
  the final code: **«all equal»** (`response_checks_framework/keyframes.out`). The playgrounds were run again after the
  last change to `playground.py` (see below).
- The browser checks of this response, all run once more on the final code: `response_checks_framework/out_final.json`.

**Found while the worlds were being fixed** (reported by the p03 agent): a clicked point arrives as
`values.position`, and `_placed` took any `position` for one, so p03's piston lost its own scalar «Положение». Now only
a list of 2–3 numbers is a clicked point (`playground._is_point`). Test: `test_a_parameter_named_position_is_kept`.

## API for the world agents

The same as in `../2026-11-04_internal_UX-params/RESPONSE_framework.md`, section «API for the world agents».

The parts that serve this review:
- `place(kind, values)`, with `position` from a click (U4);
- `palette_state()` (U7, U22);
- `can_remove(obj)`;
- `Refusal(text, hint)` (U13);
- `"notify": true` on an event (U4 (3): a body that merged right after it was added);
- `createPlayground(ctx, { …, env })`: optional, for the 3-D click.

## Changes for the integrator

The STATUS item V45, the closure of V37 (h), and the RULES §3 and §6 texts for both reviews are written once, in
`../2026-11-04_internal_UX-params/RESPONSE_framework.md`, section «Changes for the integrator». The parts that come
from this review:
- V45 (a): v07's layout;
- V45 (b): picking and dragging in the scene;
- V45 (c), (d): the limits of cancel and of holding;
- RULES §3 «Busy» and the `/cancel` row;
- RULES §6 «Placing and the palette», with the `repeat` mark of a segment's start.
