# Response to UX-ui (part): the worlds p01, p02, v03 and their engine modules

Processed 2026-11-05 by a working session that did not write the review (`../README.md`). Scope of this part, as
assigned: U2 (with UX-3d A13), U3, U4 (the world side), U5, U7, U8, U12, U13 for p01/p02, U18, U19 for p01/p02/v03.
The framework's parts (the pre-placement form, the scene clicks, the palette's disabled buttons, the toasts of
`notify` events, `Refusal`, live laws in the playgrounds' panels) are the framework's response; this part uses their
API (integrator's decision of 2026-11-05: `place`, `palette_state`, `can_remove`, `estimate_bytes`, `Refusal`,
events with `notify`).

Evidence: `response_checks_p01-p02-v03/` (scripts, outputs, screenshots before and after). Environment: Docker image
`light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`, `OMP_NUM_THREADS=2`), the shared host under load 6–34 from other
sessions (every wall-clock number states it); a private server on port 8573 (`lf-uxg1-srv`, the tree after the fix)
and one on 8577 (`lf-uxg1-srvb`, a snapshot of the tree taken before any change of this session) for the before/after
pictures and timings.

| | fixed | partly fixed | rejected | open → STATUS |
|---|---:|---:|---:|---:|
| this part (10 findings) | 7 | 2 | 1 | 0 (the remainders of the 2 partly fixed → STATUS rows below) |

## U2 (error) — p01's orbits are polylines with one point per frame [error in earlier]

**Fixed.** Reproduced: Mercury 4.9 points per orbit and 74.8° between chords at ×1, the Earth a line back and forth
(180°) at ×10 (`out/trail_accuracy.jsonl`, «former_*»; screenshots `shots/before_inner_x1.jpg`,
`before_inner_x10.jpg`, `before_hole_x1.jpg`). Cause as the review says: one trail point per `advance`, i.e. per frame.

What changed:
* **Engine** `core.gravity.nbody`: `NBody.advance(t, samples=Samples(turn, dspeed, length))` returns points of the
  integrator's own continuous output on a grid inside every step, fine enough that no body's direction of motion turns
  by more than `turn` between two of them; the grid belongs to the step, so the points do not depend on how the caller
  slices time (a merger adds the touching state and the merged one, marked). Also `step_size`, `step_count` (cheap;
  the frame no longer calls the O(N²) `diagnostics()`), and `set_collisions` (U12).
* **p01** (`viz.py`, class `Trails`): every mode offers candidates at most 10° of turn (and 10 % of speed) apart —
  Newton from `Samples`, the PN binary from its step's dense solution (`res["at"]`, stepped by the relative velocity's
  turn rate; body velocities by `pn_binary.directional` of `body_positions`), Kerr in sub-steps sized by each body's
  measured turn (Cartesian velocities from `kerr_newman.rhs_mino` on the bodies' public state). A trail keeps a point
  (position, velocity, time) when the direction has turned by more than 20° since the last kept one (the candidate
  before it is kept first, so kept points are never farther apart) or the speed changed by 20 %. A kink (an edit that
  moves or kicks a body, a merger) breaks the trail there; a merged body's trail stays (latest 32). Trail messages go
  out every frame with new points (`hermite: true`, blobs `pts`, `vel`, `tt`); at most 300 points per trail per frame.
* **p01 view**: each piece between two kept points is the cubic Hermite curve of their positions and velocities in
  chords of ≤ 2° of turn; the last piece runs to the body's position and velocity in the frame shown (frames carry
  `vel` and `trail_ids`); points later than the frame's time are not drawn (a cursor between thinned frames).

Stated tolerance (README p01): on a circle the Hermite curve is off by r θ⁴/384 = 3.9·10⁻⁵ r at θ = 20° and a 2° chord
by 1.5·10⁻⁴ r: under 2·10⁻⁴ of the local radius of curvature, below 0.25 px for any orbit up to ~1200 px in radius on
the screen, at any speed of the world.

Verification:
* `p01_gravity/tests/test_p01_gravity.py::test_orbits_are_drawn_smoothly_at_any_speed[1.0, 10.0]`: Mercury's kept
  points ≤ 20° apart and ≥ 18 per orbit, each the solver's own position (≤ 1e-6 r: the message's float32), the drawn
  line (the view's tessellation, ported) within 2.5·10⁻⁴ r of the dense computed trajectory at 3000 times;
  **negative control**: the former trail, one point per frame, > 0.1 r. Measured (`out/trail_accuracy.jsonl`):
  Mercury 22 points per orbit, 16.2° at most, deviation 1.40·10⁻⁴ r at ×1 and ×10; the Earth 19 per orbit, 19.5°,
  1.78·10⁻⁴ r.
* `test_trail_velocities_are_the_derivatives_of_the_positions` (Kerr's drawing-coordinate velocities and the binary's
  bodies' against second-order differences of the positions: 1e-5 and 1e-6).
* `test_trail_points_of_every_mode_are_within_the_turn_limit[kerr_orbits, pn_inspiral, hole_stars]` at ×1 and ×10
  (≤ 26° where a Kerr sub-step turned more than the turn measured before it; bodies nearly at rest excluded).
* `lfphys/tests/test_nbody.py::test_samples_are_the_continuous_output_and_do_not_depend_on_slicing` (the same points in
  4 or 200 calls, bit for bit; the motion with samples bit for bit the motion without; within 10° on an e = 0.6 orbit;
  negative control: one point per call turns > 60°), `test_a_merger_appears_in_the_samples_with_its_restart`.
* Browser (Chromium/SwiftShader, `curves.mjs`, looked at): `shots/after_inner_x1.jpg`, `after_inner_x10.jpg` — smooth
  circles at both speeds where the «before» shots show pentagons, crossing chords and lines; `after_hole_x1.jpg`.
* Cost: `out/p01_frame_cost.txt`: per frame 65 ms (×1) / 275 ms (×10) for «inner» against 58 / 271 ms before; the
  Newtonian integration dominates as before.
* Key frames: `keyframes.mjs` on the private server, p01, p02, v03: all equal (`out/keyframes.txt`; re-run on the
  current player after the 3-D agent's changes). The browser checks above were re-run on that code too.

## U3 (error) — p02 froze for 18–30+ s on every scene change [error in earlier]

**Fixed.** Reproduced with the review's own change list on the snapshot of before (`p02_latency.py`,
`out/latency_before.jsonl`). Cause confirmed: `_auto_W` → `SND.layer_reflection` / `Detector.reflection` →
`transfer.transmission_profile`, a Python loop over 2000–4000 slices per call, ~100 calls per change, whatever the
change.

What changed:
* **Engine** `core.quantum.transfer`: `chain` multiplies the slices' 2×2 matrices pairwise in log₂ n vectorised
  levels, each partial product normalised (the growth exponent kept apart as before); `staircase_transmission` takes
  any number of energies and potentials at once; `transmission_profile` uses them (equal to the sequential route to
  rounding: 2·10⁻¹³ measured). `core.quantum.scene`: `Detector.reflection(…, strengths=)` and
  `EdgeLayers.reflection(…, strengths=)` evaluate a whole set of absorber strengths in one call.
* **p02**: all 22 candidate strengths of an absorber in one call per mass; every reflection and chosen strength kept
  by what it depends on (a pure function of the waves and the absorber: `_cache`, 256 entries), so a change that
  touches neither re-tunes nothing.

Measured, server side (the same host; before at load 6.5–34, after at 11.8; the review measured 33 s at load 49):

| change in a running preset | before, s | after, s |
|---|---:|---:|
| double slit: packet x | 17.2 | 0.05 |
| double slit: a box far away | 26.7 | 0.05 |
| double slit: new wavelength (re-tunes two absorbers) | 26.9 | 0.48 |
| double slit: a new detector | 44.2 | 0.20 |
| double slit: the screen's edge | 64.8 | 0.24 |
| double slit: a which-path marker | 51.6 | 0.10 |
| double slit: a flux plane | 38.8 | 0.09 |
| tunnel: the barrier's height / the packet's x | 5.4 / 5.0 | 0.05 / 0.03 |
| 3-D ball: its height / a new detector | 6.1 / 15.5 | 0.08 / 0.19 |

(the «after» column includes the palette's state, U7, computed after every change). In the browser (time from the
command to the new object in the page's list, SwiftShader rendering included; `p02lat.mjs`): before 21–37 s, after
0.14–1.2 s (on the current player, with the 3-D agent's scene changes; 0.6–1.9 s in an earlier run under more load).
The review's extremes that were killed after 2 min (UX-params P30: a plane's axis, a marker's edge 10⁶, a
detector at y = ±10⁶): 0.04–0.16 s (`out/p30_extremes_after.jsonl`).

Verification: `p02_quantum/tests/test_p02_quantum.py::test_scene_changes_are_fast_and_retune_only_what_they_change`
(five changes each < 1 s; **negative control**: the cache emptied gives the same strength — the cache changes the
time, not the result); `lfphys/tests/test_transfer_chain.py` (the vectorised route against the former sequential loop,
kept in the test as the second method, on a rectangular barrier, Pöschl–Teller, an absorbing ramp, a 2000-length
barrier and the v03 wide barrier; the closed form; the chain against an explicit ordered product including a product of
1e600 000; strengths at once against one call each; edge layers against `schrodinger_nd.layer_reflection`; **negative
control**: a product in the wrong order differs far beyond the tolerance; and the speed itself).

## U4 (error), the world side — placing at the default spot

**Fixed** for p01 and p02 (the pre-placement form and the click in the scene are the framework's).
* **p01** `place` (called on every palette add): the form's or the clicked point if free; if another body is there or
  within three sums of their radii (or a hole's capture radius), or a circular start has no plane there, the first free
  point along +x in steps of an eighth of the scene, with a toast saying where and why. A copy of a massive body goes
  next to its original with the same velocity (it was refused). Every merger is a toast (`notify`), naming the time
  since the body was added when under a year. Stars and holes now start on the circular orbit by default (in an empty
  scene: at rest), so a palette star no longer falls into the Sun; the Pythagorean preset states its rest explicitly.
  A body that would start inside another without `place` (a file) is refused with the coordinates to use.
* **p02** `place`: a clicked point as the centre (or a wall's, step's, plane's position along its axis); a packet the
  scene cannot take there goes to the nearest point where it can — upstream first, in steps of its width, its core
  (±2σ) clear of potential above its kinetic energy, checked by the engine's own dry run (`Scene.particle_reason`) —
  with a toast; one that fits nowhere is refused with what to change (the wavelength it needs).

Verification: `test_palette_places_at_a_free_spot_and_merges_are_toasted` (inner Solar System: star, hole, planet and
test body from the palette — the Sun stays, every body clear of it; **negative control**: the free-spot test switched
off, the star lands in the Sun and merges, with the toast), `test_a_copy_or_a_body_put_on_another_lands_next_to_it_and_says_so`,
the circular-orbit test (a planet asked for on the z-axis goes to a free point, with the reason);
`test_a_packet_from_the_palette_lands_outside_the_wall`. Browser (`pgui.mjs`, `out/pgui.json`, looked at
`shots/after_p01_palette_star.jpg`, `after_p02_palette_packet.jpg`): «＋ Звезда» → «Поставить» in «Солнце … Юпитер»:
«точка (0; 0; 0) а.е. слишком близко к «Солнце» (касание сразу) — поставлено в ближайшее свободное место (1; 0; 0)
а.е.»; the star then circles the system and, a second sun 1 au away, scatters the inner planets — each merger a toast
(«Меркурий» и «Звезда 2» столкнулись и слились через 0,139 года после добавления «Звезда 2» …): physics, now said;
«＋ Чёрная дыра» → «Поставить»: the Sun stays. «＋ Частица» in the double slit: listed after 1.2–1.8 s with «в (0; 0) нм
сцена пакет не берёт («Стенка с двумя щелями» или край окна) — поставлен в ближайшее свободное место (−9; 0) нм»; the
palette shows «Гармоническая ловушка» and «Магнитное поле» disabled with their reasons.

## U5 (error) — actions that block the world (p01, p02)

**Partly fixed** (the remainder below → STATUS V38). p02's blocking was U3 (now ≤ 0.5 s, the review's 2-min extremes ≤ 0.16 s). p01: the
Newtonian world advanced one frame in one call (max_step None): at a high speed one frame ran for seconds (`hole_stars`
×10: worst frame 12.6 s before); it now advances in chunks of 16 integrator steps (`NewtonMode.max_step`), so the
runner keeps its frame budget and the world lags («факт» below the chosen speed) instead of stalling; the motion and
the trail points do not depend on the chunks (continuous output, the samples' grid belongs to the step). The Kerr world
likewise (4 sub-steps per call). The companion check every 20 frames still re-integrates its interval at once (≤ ~1 s
at the extreme speeds; noted in STATUS V38, below).

## U7 (error) — palette objects the world cannot take (p01, p02)

**Partly fixed.** `palette_state` (sent in every scene message; the player disables the button with the reason):
p02 tests the default object of every type with the engine's dry run (`Scene.addition_reason`, nothing changed; also
`removal_reason`, `edges_reason`, `particle_reason`, from `_validate`, the checks `_commit` ran), e.g. in the cyclotron
«Магнитное поле»: «пока в окне заряженная частица, поле не добавить: задайте поле до частицы или уберите её», «Стенка
со щелями»: the grid would no longer hold the particle's wave. p01 has no type it cannot take (placement finds a spot).
Remainder: in 3-D only the field's reason is computed (one dry run costs ~0.1 s on 64³, too much after every change)
→ STATUS V39 (below). Browser: `out/pgui.json` «p02_cyc» (both buttons disabled with these reasons).

## U8 (error) — values far outside the world (p01, p02)

**Fixed** for p02: an object wholly outside the window is refused in words (box, ball, wall, detector, marker, flux
tube by their bounding boxes; a trap by its centre), one partly outside is taken with a toast; a packet centred outside
the window is refused by the engine — the window test squared a negative distance and let it through, and the wave was
0/0 = NaN [error in earlier] (UX-params P29). p01 has no window: positions to 10⁶ au are valid and bounded by the
schema. Verification: `test_objects_wholly_outside_the_window_are_refused_and_far_packets_too`;
`lfphys/tests/test_quantum_scene.py::test_a_packet_centred_outside_the_window_is_refused` (**negative control**: the
former test alone lets 10⁶ nm through).

## U12 (should-fix) — laws the engine can change now are world parameters (p01, p02)

**Fixed** for the laws with an engine setter: p01 «Столкновения тел» (`NBody.set_collisions`: to «проходят» the pairs
already touching pass on; to «сливаются» a touching pair merges at that moment) and p02 «Края окна» (`Scene.set_edges`;
what the layers absorbed stays absorbed; refused, nothing changed, while a charged particle is next to a field). Both
are `live`, applied at the current moment with the world kept, recorded as `set` commands (restore repeats them), and
the scene file takes the law in force. The rest stay world parameters with the reason (README p01, p02): the solver,
the hole's mass, spin and charge, the binary's total mass (they set the units or the metric the bodies move in), p02's
space, grid and window (the engine has no regridding; the review's lab plan). Verification:
`test_collisions_change_at_the_current_moment_with_the_world_kept` (**negative control**: kept on «проходят», two stay
two), `lfphys/tests/test_nbody.py::test_the_collision_law_changes_at_the_current_moment`,
`test_the_window_edges_change_at_the_current_moment`; browser: the live control changed in the page, event
«Столкновения тел: сливаются … → проходят друг сквозь друга» (`out/pgui.json`).

## U13 (should-fix) — refusals in the engine's language (p01, p02)

**Fixed** for these worlds. p02 translates the engine's refusals at its boundary (`Refusal` with what to change, the
engine's sentence as `detail`): a packet inside a wall («центр пакета (…) нм внутри «Стенка с двумя щелями»: там
потенциал 3 эВ при кинетической энергии частицы 0,38 эВ … Что изменить: поставьте пакет в свободное место, например
(…) нм»), a wave finer than the grid (the λ it needs), the grid band next to an object, a field under a charged
particle, an object outside the window; the engine's own band refusal no longer cites the «яма −3 эВ» measurement (it
moved to the docstring) and the window refusal names the axis by letter and the fix. p01's refusals were Russian; the
«same point» refusal is replaced by placement. Verification: the U4 and U8 tests check the texts (no «яма»,
«Что изменить» present).

## U18 (should-fix) — the Newtonian black hole cannot be seen

**Fixed.** The hole is drawn light (`HOLE_RGB`) with a marker of the scene's size and its name (`point` object, placed
again only when it moved by 0.4 % of the scene). Browser: `shots/after_hole_x1.jpg` (the label «Чёрная дыра» at the
centre the stars orbit; before: `before_hole_x1.jpg`, nothing visible at the centre).

## U19 (should-fix) — units on primary parameters (p01, p02, v03)

**Rejected for these worlds (not reproduced).** Every world and object parameter of p01, p02 and v03 carries its unit
or is a pure number by name (a count, an angle in °, a ratio m₂/m₁, an eccentricity, a/M, Q/M, v/c); v03's view and
live controls name their units. The review's evidence is v11/v12 (the other agent's).

## Files

`lfphys/lfphys/core/gravity/nbody.py`; `lfphys/lfphys/core/quantum/transfer.py`, `scene.py`;
`lfphys/tests/test_nbody.py`, `test_quantum_scene.py`, new `test_transfer_chain.py`;
`visualizations/p01_gravity/{viz.py, web/view.js, README.md, tests/test_p01_gravity.py}`;
`visualizations/p02_quantum/{viz.py, web/view.js (the playground gets the 3-D environment for clicks), README.md,
tests/test_p02_quantum.py}`; `visualizations/v03_quantum_1d/*` (UX-params part).

## Changes for the integrator

**STATUS.md**, section V, row V38 (p01) — append to its text:
> (g) since review UX-ui (2026-11-05): trails are points of the solvers' continuous output kept at most 20° of turn
> apart and drawn as Hermite pieces (≤ 2·10⁻⁴ of the radius of curvature); placement at a free spot and merger toasts;
> the collision law is live; the Newtonian world advances in chunks of 16 steps — the companion check every 20 frames
> still re-integrates its interval at once (≤ ~1 s at the highest speeds)

and to its «to close»: «(g) a companion check spread over frames».

**STATUS.md**, row V39 (p02) — append:
> (h) since review UX-ui (2026-11-05): scene changes 0.03–0.5 s (vectorised transfer matrices, absorbers kept by what
> they depend on); placement of packets at a free spot; objects outside the window refused; «Края окна» live; the
> palette's state computed by the engine's dry run in a plane only (in space only the field's reason: one dry run costs
> ~0.1 s on 64³) — (i) the grid, the window and the space stay world parameters (no regridding in the engine)

and to its «to close»: «(h) the palette's state in space (an incremental dry run); (i) regridding of a scene
(Fourier padding)».

**lfphys/README.md** (catalogue), rows:
* `core.gravity.nbody`: add «; drawing samples of the continuous output (`Samples`: within a stated turn, independent of
  how time is sliced); the collision law changed at the current moment (`set_collisions`)».
* `core.quantum.transfer`: add «; the slices' matrices multiplied pairwise in vectorised levels (`chain`), many energies
  and potentials at once (`staircase_transmission`): 3–14× faster, equal to the sequential product to rounding».
* `core.quantum.scene`: add «; dry runs of a change (`addition_reason`, `removal_reason`, `edges_reason`,
  `particle_reason`); absorbers' reflection over a set of strengths at once».
