# Response to review LB1-p02-ux — the p02 part (Q1–Q11, X5, X10, X11, X12 p02)

**Responder:** a processing subagent (Claude) that wrote neither the review nor the code. **Date:** 2026-11-12.
The other findings (X1–X4, X6–X9, X13, X14, X12's framework part) are answered by the framework, instruments and
p01/p03/p04 processing agents in their own `RESPONSE_*.md`.

**Environment.** Docker image `light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`), containers `lf-lpq-*` with
`--memory=10g` (`response_checks_p02/run.sh.txt`); a private server `lf-lpq-srv` on port 8613 (`--memory=6g`, runs in a
scratch folder, `LFVIZ_PLAYGROUND_CKPT=6`); Playwright 1.58.2, Chromium with SwiftShader. The shared server on 8479
was not used.

**What is in `response_checks_p02/`.**
- `before/`: the reviewer's `a3`, `a4` run on the code as delivered (the reproductions; `a4` case 6 then also met a
  framework file in mid-edit — the reviewer's own `a4_p02_wrapper.out` is the reproduction of Q4).
- `after/`: the reviewer's `a1`–`a5` run on the fixed code (`a3`, `a3b` catch the new refusals and print them), and
  `r5_drag_open_edges_after.py`, `r5b_leak.py` (the a5 grid with the decision now taken).
- `engine/`: the physics checks of the fix (`e1` closed form against quadrature, `e2*` the move against the reviewer's
  cases and a second method, `s1_smoke.py`, `d1_throw.py` the diagnosis of Q5); their outputs in `engine/outputs.txt`.
- `browser/`: `fix_tour.mjs`, `fix_tour1.mjs` (the visible fixes on the private server), their logs and screenshots.

## Summary

| ID | summary | decision |
|---|---|---|
| Q1 | a drag next to an AB tube cut phase lines into the wave, announced as «та же волна» | **fixed** [error in earlier] |
| Q2 | in a non-uniform field the drag changed the kinetic energy silently | **fixed** [error in earlier] |
| Q3 | `measure()` returned a tuple; every p02 sweep failed | **fixed** [error in earlier] |
| Q4 | 2-D → 3-D carry-over broke on walls, steps, flux planes; contradicting notices | **fixed** (p02's part; the form's grid and window are X3, framework) [error in earlier] |
| Q5, X5 | the throw limit ignored the wave; a throw clamped to it was refused | **fixed** [error in earlier] |
| Q6 | a window change moved the absorbing layers over the wave silently | **fixed** [error in earlier] |
| Q7 | the grid's help promised one rule of three; a wrong refusal for a free packet | **fixed** [error in earlier] |
| Q8 | a drag with open edges refused for wave already inside the absorber | **fixed** |
| Q9 | a same-window change moves the cell and the layers by up to d/2 | **fixed** (stated; keeping the cell fixed declined, reason below) |
| Q10 | the "regrid" bank can be negative but was labelled «отброшено» | **fixed** |
| Q11 | the handle, λ and the drag reference are means, which may mean nothing for a split wave | **fixed** (labelled; «где волна сейчас») |
| X10 | any coarsening of a preset was blocked by the automatic edges | **fixed** |
| X11 | «Центр пакета» was not where the packet is | **fixed** |
| X12 (p02) | p02's own event texts | **fixed** (the framework's edit event is the framework's) |

Counts: 14 fixed, 0 partly, 0 rejected, 0 deferred. Found while processing: E1–E4 below.

## Findings

### Q1 — fixed — a drag next to a flux tube is now the magnetic translation, or refused
**Reproduced.** `before/a3_drag_kick.out` case 4: ⟨π⟩ (0.97157, 0.00035) → (0.99412, 0.04801), ⟨π²⟩/2m +3.06 %;
`before/a4_p02_wrapper.out` case 3 (the AB preset, (0, 4) after the wall): ⟨k − qA⟩ (−1.94821, 0) → (−1.94268, 0.00359),
the outer third of the spectrum 4.4e-9 → 6.6e-6, event «та же волна перенесена».

**Cause.** The gauge factor took straight-line integrals of the whole A from the wave's mean position c. For a tube,
Λ_c(r) jumps by Φ on the ray from the tube away from c, and so the factor had two rays of phase jump qΦ wherever the
wave had amplitude there.

**Decision: the physically right move, and a refusal where none exists.**
- A move by s keeps "the same wave" exactly when ψ'(r) = e^{iqχ(r)} ψ(r − s) with ∇χ = A(r) − A(r − s) on the wave's
  support: then |ψ|², the current and the whole kinetic distribution are carried along. Past a flux tube such a χ
  exists exactly when the path the tube takes relative to the wave, [c₀, c₀ + s], misses the wave: then the flux every
  loop of the wave's support encloses is unchanged.
- **The factor per source** (`Scene._move_gauge`): for a tube, χ(r) = ∫ A·dl along the segment from r − s to r, in
  closed form (`schrodinger_nd.flux_tube_segment`, Owen's T function for the Gaussian core). Its gradient is
  A(r) − A(r − s) + s × ⟨B⟩ over the segment (an identity), so it is exact wherever the segment misses the tube's field.
  That is everywhere except next to [c₀, c₀ + s], also for a wave that went round the tube on both sides. For a field
  (`MagneticField`), the straight-line integrals from c as before: exact in a uniform field.
- **The test** (`Scene._moved`): the share of the kinetic field (p − qA)ψ not carried along,
  ‖(p − qA)ψ' − f·[(p − qA)ψ](r − s)‖² / ‖(p − qA)ψ‖², by spectral derivatives on the grid. It is zero for the exact
  magnetic translation. A phase cut, a field that differs between r − s and r, and a factor that pushes the canonical
  spectrum out of the band all count. Above 10⁻⁶ (`REGRID_TOL`) the move is refused (what="gauge") with the kinetic
  energy's change and the tubes (probability on their path) and fields that cause it. p02 says it in Russian («путь
  трубки «Трубка потока» относительно волны проходит через неё (там 0,008 её вероятности): поток, который охватывают
  части волны, изменился бы…») and points to «Приготовить пакет заново».
- «та же волна» is now said only for a move that passed this test; a charged particle's event adds «магнитный перенос:
  кинетическая часть волны сохранена» and the kinetic energy ⟨(p − qA)²⟩/2m before and after. The docstrings of
  `transform_particle` and `VectorPotential.gauge`'s use are restricted accordingly.

**Verification.**
- `engine/e1`: the closed form against 400-node quadrature, to 1.3e-14.
- `engine/e2` A3 = the reviewer's a3 case 4: refused (misfit 0.103, 0.18 of the wave on the tube's path); flux 0: taken,
  misfit 5e-30, T unchanged. `after/a3b_ab_cut.out`: refused, the wave unchanged.
- **Second method** (`engine/e2` B): a wave scattered round a tube shielded by a hard post, moved so that the tube's path
  stays in the post. Taken, with misfit 6e-10 to 2e-9. It is compared with the same packet evolved in a scene whose tube
  stands at c₀ − s, then translated by s (no move code). They agree to 3.3e-4 to 8.5e-4; the old factor is off by
  8.8e-3 to 0.24. The agreement's floor belongs to the reference, not to the move: the two scenes' own evolutions differ
  by 2.7e-4 with no move at all (`engine/e2f`, 7.7e-8 at step 0). The singular gauge between them puts a phase step on
  grid rows across the post, and the spectral kinetic step couples it.
- In the AB preset the reviewer's own drag (a4 case 3) is now exact (`after/a4_p02_wrapper.out`: ⟨k − qA⟩ −1.94821 →
  −1.94822, outer third 4.40e-9 → 4.97e-9): the tube's path stays inside the wall between the slits.
- In a browser, the drag across the lower slit while the wave is in it is refused with the tube named
  (`browser/fix2_ab_drag_across_slit_refused.jpg`, looked at). After the wave has passed, the drag along the wall is
  taken as the magnetic translation (`fix2b`).
- Tests: `lfphys/tests/test_quantum_scene_live.py::test_flux_tube_segment_is_the_line_integral_of_the_tubes_potential`
  (closed form, the gradient = A(r) − A(r − s) away from the path; negative control: the earlier factor is not),
  `…::test_a_move_whose_tube_path_crosses_the_wave_is_refused` (with the flux-0 control),
  `…::test_a_move_past_a_shielded_tube_is_the_magnetic_translation` (second method; negative control: the earlier
  factor > 1e-2); `visualizations/p02_quantum/tests/test_p02_quantum.py::test_a_drag_in_the_aharonov_bohm_preset_keeps_the_wave_or_is_refused`.

### Q2 — fixed — a move across a field's edge is refused, with the kinetic change
**Reproduced.** `before/a3_drag_kick.out` case 3: ⟨π²⟩/2m −9.7 %.

**Decision.** No translation keeps a wave whose field differs between r − s and r: ∇χ = A(r) − A(r − s) has no solution
there. The same kinetic-field test refuses it (what="gauge", with the field named and ΔT/T): «поле «Поле Bz» там, куда
переносится волна, не то, что там, где она была. Её кинетическая энергия изменилась бы на −9,66 %…». A move inside the
uniform part is exact.

**Verification.** `engine/e2` A2: refused, ΔT/T −0.0966, `fields=[1]`; along the strip, misfit 4e-30. Test:
`…::test_a_move_across_a_fields_edge_is_refused_and_inside_it_exact` (B = 0 control).

### Q3 — fixed — `measure()` returns the dict of the API
**Reproduced** from the review's log, and in the test's negative control. **Fix.** `measure()` returns
`{id: number}`. The frame uses `_measure()`, which also gives the NaN reasons (`meas_note`).

**Verification.** `test_a_sweep_of_p02_measures_the_free_packets_closed_form` drives `sweep.run_value` with a checkpoint
and a fresh restored world, over a free packet's wavelength. It measures ⟨x⟩ after T = x₀ + (h/mλ)·T for each value,
to 1e-8 nm. Negative control: the earlier tuple fails the value, with AttributeError or the sweep's own contract check.

### Q4 — fixed — walls, steps, flux planes and tubes go into space; one notice; same-space waves carried
**Reproduced.** The reviewer's `a4_p02_wrapper.out` case 6: 0 of 4 carried, «Нет параметра «z»».

**Fix** (`viz.py` `_carried`, `carry_state`, `_carry_packet`, `carry_world`; engine `Scene.adopt_wave`).
- `z` and `sz` are set only for the kinds whose schema has them.
- Walls, steps and flux planes across x or y, and tubes, go into space as they are. They are unbounded along z, and the
  tube runs along z.
- Each adaptation is said through the framework's `carry_note`, from `place`. The framework drops it when the object is
  then refused, so no change is noted for an object that was not carried. The framework's carry hooks (LB1-F5) replace
  p02's own second notice.
- Across dimensions a packet is prepared afresh and marked `restarted` («волна приготовлена заново из параметров:
  другая размерность»), and so are the world's random generators and measured points.
- In the same dimension the wave itself goes: `carry_state` gives the samples, the records by object id and the
  spectral model; `Scene.adopt_wave` resamples them exactly to the new grid. It refuses as a live change of the grid
  refuses (then the packet is prepared afresh, said), and keeps the absorbed records. A detector that was not carried
  becomes «в прежнем мире». The random generators and the measured points go along.

**Verification.**
- `test_a_new_world_carries_walls_tubes_planes_into_space_and_waves_in_the_same_space`: all 5 objects of a wall, tube,
  plane, detector and packet carried into space. In the same space on a finer grid, the wave equals
  `schrodinger_nd.resample` of the old one (1e-15), absorbed kept, checks pass.
- The updated `test_a_new_world_of_the_other_dimension_takes_over_what_makes_sense` reads the notice's `carry` data.
- `engine::test_a_wave_carried_into_another_scene_is_the_same_wave`.
- In a browser: `browser/fix3_carry_into_space.jpg` (looked at): the 3-D scene with the wall, the tube as a cylinder,
  the planes, the packet, and the single notice.
- The reviewer's case 6 with the default 64³ over 80 nm still refuses the detector and the electron for the grid. That
  is X3 (the form's grid and window: framework).

### Q5, X5 — fixed — the throw's limit is the scene's; a throw is clamped by the world, never refused for speed
**Reproduced and diagnosed** (`engine/d1_throw.py`): the root cause was in the engine.
- After the double slit's wall the wave is reflected and transmitted (⟨k⟩ = −1.94).
- The boosted wave's model read its spectrum as one Gaussian about the mean (σ_k = (reach − |mean|)/z). For a wave in
  parts the mean is near 0, so |mean| + 6σ_k came to about twice its real reach (10.7 against 6.7).
- Every throw was refused, even one that stopped the wave, while the same wave unthrown was judged by its packet model.
  [error in earlier]

**Fix.**
- `Scene._spec_model(psi, s0)` with the packet's own spread: σ_k = (reach − |mean| + (6 − z) s0)/6. That is σ_k for a
  Gaussian, and the outer part's own |k| + 6σ_k for a wave in parts (two packets at ±3: exactly 4).
- `Scene.kick_limit` finds by bisection, on the very tests the boost applies, the largest fraction of a throw the scene
  takes.
- p02 clamps a drag's throw (op «edit») to it and says so: «бросок ограничен: просили 38,71 км/с, быстрее 14,25 км/с
  в этом направлении сетка здесь и сейчас не передаёт волну». A velocity typed in the inspector (op «set») is refused,
  with that limit.
- The limit shown (`v_max`) is `Scene.kick_reach`, a bound the boost's tests pass in every direction, computed from the
  measured spectrum. It follows the wave: checked every 20 frames, the scene message sent again when it moved by more
  than 25 %.
- The refusals say which test failed and whether the place or the speed is the cause («Причина — скорость: в этом
  направлении сейчас можно не быстрее …»; «Причина — место: туда волну не перенести даже покоящейся»).

**Verification.**
- `test_a_throw_after_the_wall_is_clamped_by_the_world_not_refused`: the limit drops to < 0.5 of the fresh packet's
  after the wall and is re-sent. A throw at it is taken in all 4 axis directions. A throw at the stale fresh limit is
  clamped and said. A typed one is refused with the limit.
- `engine::test_the_throws_limit_is_the_scenes_and_a_split_wave_can_be_thrown`: stopping a split wave is taken
  (negative control: the earlier model refuses it); a throw just beyond the limit is refused; `kick_reach` at p02's 2 %
  margin passes in 4 directions. It is up to 1.2 % over the exact limit in one direction, within a grid wavenumber step:
  the two reads of the reach interpolate differently.
- The updated `test_the_throws_limit_is_the_speed_the_grid_carries_here`.
- In a browser: `browser/fix_tour1.log` shows the clamp event above; `fix1_throw_after_wall_clamped.jpg` (looked at)
  shows no refusal.

### Q6 — fixed — the layers' move is measured, refused when it covers the wave, and said
**Reproduced.** `before`: the tunnel's window 80 → 56 nm taken, «отброшено 3,6·10⁻¹⁰», with 2.68e-5 under the new layers.

**Fix.** `Scene.regrid` measures the share of the wave under the new window's layers (`in_new_layers`) and the part of
it that was outside the old layers (`exposed`). It refuses above 10⁻⁶ (what="layers", also when edges are opened in
the same change). The p02 event says both, and for a larger window what was inside the old layers («эта часть, уже
ослабленная слоями, теперь внутри окна»).

**Verification.**
- `after/a4_p02_wrapper.out` case 2: refused, 2.37e-5 exposed.
- Tests `engine::test_a_smaller_window_does_not_move_the_absorbing_layers_over_the_wave` (closed-edges control) and
  `test_a_smaller_window_is_refused_where_its_layers_would_cover_the_wave`.

### Q7 — fixed — the help names the three rules; the refusal says which
**Fix.**
- The help of «Точек сетки по оси» names: the 10⁻⁶ spectrum rule; the resolution rule (|k| + 6σ_k ≤ π/d, next to what
  acts ≤ ⅔·π/d); the objects' edges, including the frozen «0» and the coarsen action.
- The engine's resolution refusal carries its flags (`_resolution_info`: inter, conv, K, lim). p02 says «волна мельче,
  чем передаёт новая сетка» for a free packet and «рядом с тем, что на неё действует» only next to a potential or field.

**Verification.** `test_refusal_and_label_texts_say_which_rule` (a free packet at k₀ + 5σ_k < π/d < k₀ + 6σ_k).

### Q8 — fixed — with open edges only wave that lands inside the window counts
**Reproduced.** The reviewer's `a5`: 17–60 % of the wave in the layers, 3–5 nm drags refused.

**Fix.**
- `wrap_fraction(…, margin)`: what a move carries across a face counts only when it lands beyond the far side's layer.
- What lands in that layer is reported (`far_layer`). p02 bounds what the layer would let back inside as that part goes
  inward from where it lands (`_far_leak`: WKB attenuation of the ramp at normal incidence, the least absorbed). It
  refuses above 10⁻⁶ and says the bound in the event, along with the share of the wave that was in the layers.

**Verification.**
- `after/r5_drag_open_edges_after.out`: every drag of the a5 grid lands nothing inside directly.
- `after/r5b_leak.out`: leaks 1e-25 to 2.4e-7, all taken.
- Tests `engine::test_a_move_with_open_edges_counts_only_what_wraps_into_the_window` and
  `test_a_late_drag_with_open_edges_is_taken_and_says_what_was_in_the_layers`.
- In a browser, a 13-nm Shift-drag at 1.33e-13 s was refused for a leak of 0.037 (`browser/fix_tour.log`, step 1),
  correctly.

### Q9 — fixed — stated
`schrodinger_nd.window` and `Scene.regrid` now say it: on the same window length the cell moves by (d − d₂)/2, exact for
the wave, while the drawn window and the layers shift by up to half a step. The p02 README says it too.

**Declined, with reason:** keeping the cell fixed. That would put a sample other than n//2 at the centre, against the
grid convention the engine shares (`Grid`, the angular spectrum, `resample`), for a shift below half a step of an
absorber whose own width is ten steps.

### Q10 — fixed
The measurable is now «Изменение нормы сменой сетки или окна: отброшено (минус — прибавилось от квадратуры новой сетки;
сумма по частицам)». The absorbed key is «смена сетки или окна (отброшено; минус — прибавилось от квадратуры)».
Test: `test_refusal_and_label_texts_say_which_rule`.

### Q11, X11 — fixed — the centre at preparation, and «где волна сейчас»
**Reproduced.** The reviewer's `a4` case 5: the fresh packet went to x = −19.17 with the wave at −12.57.

**Fix.**
- The packet's x, y (z) are labelled «Центр при приготовлении», with help saying that a drag writes there and that ⟨x⟩
  in the inspector is where the wave is, a mean which for a wave in parts may lie between them.
- The wavelength's help says that after a throw it is 2π/|⟨k⟩| of the whole wave.
- «Приготовить пакет заново» has «Где»: from the parameters, or where the wave is now (⟨r⟩ and ⟨p − qA⟩ written into
  the parameters, then prepared).

**Verification.** `test_prepare_where_the_wave_is_and_coarsen_with_the_edges`.

### X10 — fixed — «Огрубить сетку с краями по ней»
**Fix.**
- The refusal of an object whose «0» edge the coarser grid cannot resolve now says the width it was frozen at, and
  points to the new action.
- The action widens every such edge to 1.05 × the new grid's narrowest edge (the potential changes: said, with old →
  new widths), coarsens, and sends the live values.
- A refusal undoes the widened edges.

**Verification.** In the same test: the double slit 256 → 192, the wall's edge 0.995 → 1.33 nm, then the checks pass.
In a browser the action shows in «Действия» (`fix3`).

### X12 (p02's part) — fixed
p02's own texts:
- no doubled parentheses («(не изменилась до округления)»);
- no «волна пересчитана» in a world without waves («волн в окне нет»);
- the move and throw events in short form, with speeds in km/s («брошена: v = (14,23; 0,813) км/с → k₀ = …»);
- round-off coordinates shown as 0 (`_pt`);
- the velocity labels shortened («Скорость: vx, нм/с», help «= ħk₀/m; задаётся броском»).

The framework's edit event («перемещение в (…) нм; бросок: v = …») is the framework agent's.

## Found while processing

- **E1 [error in earlier]** (the root cause of Q5): the boosted wave's spectral model doubled a split wave's reach. See
  Q5.
- **E2 [error in earlier]**: a move's gauge factor could push a charged wave's canonical spectrum past the band, with
  nothing checking it. The kinetic-field test of Q1 now catches it.
- **E3 [neutral]**: "a packet just prepared and moved equals the packet prepared at the new place" was a property of the
  earlier construction near a tube. Under the magnetic translation it holds up to the packet's own tail at the tube,
  where a prepared packet carries its convention's cut: 2.3e-4 of the peak with the tube 7 nm from the packet, 1e-7
  at 12.7 nm. The engine test now places the tube outside the tail and says so.
- **E4 [neutral]**: the split operator is not covariant between two scenes related by a singular gauge, even where ψ ≈ 0
  on the gauge's cut. It differed by 2.7e-4 after 750 steps (`engine/e2f`). A single scene's A is smooth, so its physics
  is unaffected. This only bounds comparisons of the kind made in Q1's second method.

## Tests and checks run (2026-11-12)

All runs were in Docker on the CPU. Every run passed.

| run | result |
|---|---|
| `lfphys`: `test_quantum_scene_live.py test_quantum_scene.py test_schrodinger_nd.py test_transfer_chain.py test_quantum.py test_boundary.py test_layers.py test_licences.py` | 367 passed, 4 skipped (GPU) |
| `visualizations/p02_quantum/tests/test_p02_quantum.py` | 51 passed (8 new, 4 changed) |
| `visualizations/tests/test_checkpoint.py test_restore.py -k p02`, twice | 3 passed, 3 passed |
| `visualizations/tests/test_carryover.py test_manipulation.py test_sweeps.py` (the framework's; they touch p02's paths) | 35 passed |
| `tests/browser/keyframes.mjs 8613 p02_quantum` (private server) | all equal (6 cursors, 39 key frames; `browser/keyframes_p02.out`) |
| `tests/browser/manipulation.mjs 8613 1600x1000,1280x800 p02_quantum` | all passed (12; `browser/manipulation_p02.out`) |
| the reviewer's `a1`–`a5` on the fixed code | `after/` (a1, a2 unchanged; a3, a3b, a4 as said above) |
| browser tour of the visible fixes | `browser/fix_tour*.log`, 4 screenshots looked at, no page errors |

**New tests.**
- Engine (`test_quantum_scene_live.py`), 8 new:
  - `…flux_tube_segment_is_the_line_integral…`
  - `…tube_path_crosses_the_wave_is_refused`
  - `…shielded_tube_is_the_magnetic_translation`
  - `…across_a_fields_edge…`
  - `…split_wave_can_be_thrown`
  - `…absorbing_layers_over_the_wave`
  - `…counts_only_what_wraps_into_the_window`
  - `…carried_into_another_scene…`
- Engine, 2 changed: `…keeps_its_kinetic_momentum_in_a_field` (the tube moved out of the packet's tail, E3) and
  `…boosted_wave_is_its_spectrum` (with the packet's spread).
- p02, 8 new:
  - `…sweep_of_p02…`
  - `…aharonov_bohm_preset…`
  - `…throw_after_the_wall…`
  - `…carries_walls_tubes_planes…`
  - `…its_layers_would_cover_the_wave`
  - `…late_drag_with_open_edges…`
  - `…prepare_where…coarsen…`
  - `…say_which_rule`
- p02, 4 changed: the throw's limit; the carry test reads the notice's data; the regrid wording; the new limit's numbers.

Every new test has a negative control or a control world, named in its docstring.

**Latencies** (whole commands, CPU, 2 threads, shared host):
- the AB electron dragged: 0.11 s;
- a throw clamped by the world: 0.29 s;
- the limit's refresh: 5.5 ms every 20 frames;
- a carry with the wave to 384²: 0.21 s.

They are also in the p02 README. Containers `lf-lpq-*` were stopped by name and checked with `docker ps -a`.

## Changes for the integrator

These are texts for files this processing does not own. Insert them exactly.

**1. `engine/STATUS.md`** — the p02/LB1 item (replaces the p02 agent's proposed LB1 text):

> LB1 (P16.1–P16.3) for p02 and core.quantum (review LB1-p02-ux processed, `reviews/…/RESPONSE_p02.md`): grid and window
> live via `Scene.regrid` (exact resampling; refused above `REGRID_TOL` = 1e-6 of a particle's norm dropped, misplaced
> or put under the new open edges' layers); an edge set to 0 keeps the width it was resolved with (the action
> «Огрубить сетку с краями по ней» widens such edges for a coarser grid); a packet's drag is the magnetic translation
> (`Scene.transform_particle`, `schrodinger_nd.flux_tube_segment`; refused where none keeps the wave: a flux tube's path
> across it, a field that differs), its throw the kick k0 = m v/ħ, clamped by the world to the fastest the grid takes
> there (`Scene.kick_limit`); instruments from `Scene.observables`; a new world of the same dimension carries the waves
> (`carry_state`, `Scene.adopt_wave`). Open: (a) `measure()` costs one FFT per wave per frame, about 4 % of the
> stepping at the default speed; (b) the throw limit shown (`v_max`, `Scene.kick_reach`) is an isotropic bound,
> conservative for a wave in parts (the world applies the exact limit per direction and says so); (c) the split
> operator is not covariant between scenes related by a singular gauge (2.7e-4 after 750 steps; review LB1-p02-ux E4):
> it bounds comparisons across scenes only.

**2. `engine/visualizations/RULES.md` §6**, after «The laws are world parameters, except…»:

> p02's grid and window are such laws: the waves are resampled exactly at the current moment, and a change that would
> drop or misplace more than 10⁻⁶ of a particle's norm, or put it under the open edges' moved layers, is refused with
> the number (`Scene.regrid`). A drag of a wave is a re-preparation of the same wave only where a translation keeps it
> (for a charged particle, the magnetic translation); elsewhere it is refused with the reason.

**3. Owner guide `engine/visualizations/README.md`**, the p02 row, append:

> ; сетка и окно меняются на ходу (волна пересчитывается точно; окно не сдвинет поглощающие края на волну); пакет можно
> перетащить — та же волна в новом месте (у трубки потока, если её путь относительно волны пересекает волну, и на краю
> поля такой волны нет — перенос не принимается, с объяснением) — и бросить (k₀ = m v/ħ; слишком быстрый бросок мир
> ограничит до наибольшей скорости, которую сетка передаёт, и скажет об этом); «Приготовить пакет заново» — из
> параметров или там, где волна сейчас; «Огрубить сетку с краями по ней»; «Новый мир» того же пространства переносит
> саму волну; приборы: вероятность, энергия, ⟨x⟩, ⟨p⟩, поток, поглощённое

**4. `engine/lfphys/PLAN.md`**, the LB1 row:

> p02 part implemented 2026-11-11; review LB1-p02-ux processed 2026-11-12 (`RESPONSE_p02.md`: Q1–Q11, X5, X10, X11, X12 p02
> fixed).

**5. `engine/lfphys/README.md`** (the catalogue):
- in the row of `schrodinger_nd`, append «; exact resampling of a wave to another grid or window (`resample`,
  `regrid_losses`), translation (`translate`, `wrap_fraction` with the open edges' margin), the gauge factor of a move
  past an Aharonov–Bohm tube in closed form (`flux_tube_segment`)»;
- in the row of `scene`, append «; live grid and window (`regrid`, with the open edges' layers), a wave moved by the
  magnetic translation or kicked (`transform_particle`, refused where no translation keeps it; `kick_limit`,
  `kick_reach`), a wave taken over from another scene (`adopt_wave`), readings (`observables`), each object's arrays
  cached by its parameters».

**6. `engine/reviews/README.md`**, registry: when every `RESPONSE_*.md` of this review is in, the row of
`2026-11-11_internal_LB1-p02-ux` should name, for p02: «Q1–Q11, X5, X10, X11, X12 (p02) fixed — the AB drag cut phase
lines into the wave as «та же волна» and a field's edge changed its kinetic energy by −9.7 % (now the magnetic
translation, refused where none) [error in earlier]; p02 sweeps failed (`measure()` a tuple) [error in earlier]; walls,
steps, flux planes refused into space [error in earlier]; a split wave's boosted model doubled its reach, so every throw
after a wall was refused [error in earlier]; the window's layers moved over the wave silently [error in earlier]; +4
found (E1–E4)».

**7. For the framework agent** (not a text to insert):
- The carry notice's «изменено при переносе» lists p02's hidden `v_max` («v_max 5,003·10¹⁴ → 3,062·10¹⁴»), which the
  new world recomputes. The framework might skip hidden parameters in that diff.
- p02 now calls `carry_note` from `place` (obj None = the object being carried) and from `on_add` / `carry_world`. It
  relies on the framework dropping `place`'s notes for an object that is then refused, which it does today.
