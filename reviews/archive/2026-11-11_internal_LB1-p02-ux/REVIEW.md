# Review LB1-p02-ux: p02's live grid, drag and throw physics; the laboratory as the owner uses it

**Status: awaiting processing.** Reviewer: an independent subagent (Claude). It did not write the code. It is not
the responder.

**Date:** 2026-11-11.

**Scope.**
- **Part A.** The new quantum physics of LB1 in p02:
  - `lfphys/lfphys/core/quantum/scene.py`: `regrid`, `transform_particle` / `move_particle` / `boost_particle`,
    `observables`, `__getstate__`;
  - `lfphys/lfphys/core/quantum/schrodinger_nd.py`: `resample`, `regrid_losses`, `translate`, `wrap_fraction`;
  - `visualizations/p02_quantum/viz.py`: handles, `measurables` / `measure`, carry-over, «Приготовить пакет заново»;
  - their tests.
- **Part B.** p01–p04 used in a browser the way the owner would. This covers only the user's view; the physics of
  p01, p03 and p04 belongs to the other reviewers.

## Environment

**Engine scripts.** Image `light-funnel-viz`, CPU only (`LFPHYS_NO_GPU=1`), in containers `lf-lbrx-*` with
`--memory=8g`. The engine is mounted read-only at `/lf` and this folder at `/out`. The exact command is in each
script's header.

**Server.** A private server `lf-lbrx-srv` on port 8603, `--memory=6g --max-workers 3`, with runs in a scratch folder.
It has been stopped and removed; `docker ps -a` shows no `lf-lbrx-*` container. The shared server on port 8479 was not
used.

**Browser.** Playwright 1.58.2, Chromium with SwiftShader, `--shm-size=2g --init --network host`, run through
`runb.sh.txt`.

**What is in this folder.**
- Engine and wrapper checks (`a*`): `a1_regrid_free_gaussian`, `a2_refusal_numbers`, `a3_drag_kick`, `a3b_ab_cut`
  (writes `a3b_ab_cut.png`), `a4_p02_wrapper`, `a5_drag_wrap_open_edges` — each a `.py` script with its `.out` output.
- Browser tours (`b*`): `b0_catalogue`, `b1_p02`, `b2_p02_delete_world`, `b3_worlds`, `b4_instruments`, `b6_p02_3d`,
  with the shared helpers in `b_lib.mjs`. Their logs are in `logs/`.
- HTTP-API probes: `b5_sweep_api.py` and `b7_p04_umax_api.py` (host Python, stdlib only, talking to the private server),
  with their `.out` outputs.
- Screenshots in `shots/`: JPEG, each under 300 KB.

## Summary

| part | errors | should-fix | nits |
|---|---|---|---|
| A (physics of p02's live changes, its wrapper) | 3 | 5 | 3 |
| B (the laboratory in a browser) | 2 | 9 | 3 |

**What hurts the owner most, in order.**
1. **The parameter sweep of P16.3 is unusable** (Q3, X1):
   - every sweep in p02 fails at every value with «Внутренняя ошибка мира — AttributeError»;
   - in every playground, p01–p04, a sweep over an object's parameter is refused («нет параметра … есть: нет»),
     although the panel offers these parameters.
2. **A drag next to an Aharonov–Bohm tube cuts the wave's phase** (Q1). The event still says «та же волна». This
   happens in the AB preset itself.
3. **«Новый мир» with «перенести сцену» from the plane into space** (Q4, X3):
   - it carries 0 of 4 objects of the double slit;
   - the wall and the flux plane fail with «Нет параметра «z»»;
   - the form offers no grid or window for the new dimension;
   - two notices contradict each other.
4. **Delete does not delete in p02's plane window** (X2). It answers «Срез не построен: у этого мира нет запросов
   просмотра».
5. **Throws are refused.**
   - In p02, a throw clamped to the shown limit `v_max` is then refused (Q5, X5).
   - In p03 and in p01's Kerr world, the default throw scale gives 10¹² m/s or 2.33 c (X4).

**What works well** (verified, see "Verified" below):
- the resampling is exact on every route;
- the norm bookkeeping is honest;
- the magnetic translation is exact in a uniform field;
- the throw is the kinetic momentum;
- live changes are fast: 0.02–0.4 s, and 1.8 s for a 2-D grid of 384²;
- the selection survives drags and the camera does not move;
- most refusals say what to change.

---

## Verified (Part A), status per item

**V1 [useful] — the resampling is exact for band-limited waves.** Checked against the closed-form free Gaussian
(`a1_regrid_free_gaussian.out`):
- **Odd counts.** 191 → 287 → 190 → 257 → 191 points. The periodic cell moves by (d − d2)/2, e.g. [−47.75, 47.75)
  → [−48.001, 47.499). The error is ≤ 1.2e-14 of the peak before and after each change. The norm stays at 1 − 6e-15.
  ⟨H⟩ is identical to 12 digits.
- **A packet near the band edge.** |k| + 6σ_k = 5.0 against π/d = 6.28; refined and back. After the refinement the
  error is 9.4e-14, which is the reference's own alias at the old band, exp(−σ²(π/d − k)²) ≈ 4e-13. After going back
  it is 4.3e-15.
- **A chain with open edges.** Refine, enlarge, both changed, shrink: ≤ 8e-15.
- **3-D.** 64³ → 80³ → 96³ → 72³ × 0.5 → 64³: the error after each change equals the error before it, 1.7e-11 to
  5.2e-11. That residual is the reference's tail at the 32-nm faces, not the resampling.

The half-step offset between grids is handled correctly. The function is periodic, and `regrid_losses` skips the
face test on a same-window change.

**V2 [useful] — the norm bookkeeping is honest** (`a2_refusal_numbers.out`, `a1`).
- The banked "regrid" equals the measured loss: 1.480705e-2 outside the window, banked 1.480705e-2. Afterwards
  norm + absorbed − 1 = −3.4e-15.
- The window's "outside" fraction agrees with the closed form to 1–3 %: 3.818e-6 measured against 3.916e-6, and
  1.481e-2 against 1.493e-2. The remainder is the closed form's continuous integral against the grid's cells.
- The "spectrum" fraction is the exact discrete fraction. It is 2–2.5 times the continuous Gaussian tail, because the
  boundary bin is counted whole. This is correct for what is actually dropped.
- The enlargement's "face" test is conservative.
  - At face 8.45e-6, the true ‖ψ − ψ_free‖² on the larger window is 1.03e-6, and the change is refused.
  - At face 1.02e-2 it is 4.65e-3.

**V3 [useful] — the gauge factor is exact for a uniform field, also for an evolved wave.** This goes beyond the
repository's test, which moves a packet only right after it is prepared. The case: B everywhere, the wave evolved for
a quarter of a cyclotron period, moved by (3, 4) and back (`a3_drag_kick.out` case 2).
- ⟨π⟩ and the kinetic energy ⟨π²⟩/2m are unchanged to 4e-16.
- Analytically: ∇_r Λ_c(r) = A(r) − ½B×(r − c) for any gauge of a uniform B, so the code's
  χ = Λ_{c+s}(r) − Λ_c(r − s) has ∇χ = A(r) − A(r − s) — the magnetic translation, for any wave and any reference
  point c.

**V4 [useful] — k₀ = m v/ħ is the kinetic momentum, which is the right one.**
- `_set_packet` takes `dk = m v/ħ − ⟨p − qA⟩/ħ`.
- `exp(i dk·r)` shifts the kinetic momentum in any gauge.
- **Engine check** (`a3` case 5). After a throw in a uniform field, the kinetic wavenumber equals the target to 1e-6,
  and d⟨r⟩/dt over two steps is (1.2017, −0.697) against the target (1.2, −0.7). The canonical ⟨p⟩ is (1.2035, −2.2)
  — a choice of canonical momentum would have been wrong.
- **Through p02** (`a4` case 4). A throw of (1, 2)·10¹⁴ nm/s in the cyclotron preset reads |⟨v⟩| = 223.607 km/s
  afterwards, exactly the thrown speed.

**V5 [neutral] — `observables` and the `__getstate__` cache.** No defect found.
- `observables` agrees with `checks` and `Grid.mean_x` / `mean_p`; the repository's test covers this.
- `__getstate__` drops `_obj_cache`. The cached arrays shared with `_arr["W_parts"]` therefore do not travel twice in a
  checkpoint. A restored scene rebuilds the cache on its next change.

---

## Part A findings

### Q1 — error — A drag next to a flux tube cuts the wave's phase; the event says «та же волна»

**Location.** `scene.py:2075-2081` (`transform_particle`, gauge factor), docstring `scene.py:2034-2040`;
`viz.py:777-792` (the event text).

**What happens.** The factor `exp(i q [Λ_{c+s}(r) − Λ_c(r − s)])` uses straight-line integrals of A from the wave's
mean position c.
- When a segment from c (or c + s) to a point of the wave crosses a flux tube, Λ jumps by the flux.
- For a wave that has gone round the tube, the moved wave therefore gets cut lines of phase qΦ where it has amplitude.
  That is a spurious sheet of field — the same class of defect as review B6-Q2.
- The docstring's claim holds only for a packet that has just been prepared.

**Evidence.**
- **`a3b_ab_cut.out` / `a3b_ab_cut.png`.** Flux h/2e, a post around the tube, the wave past it, moved by (0, 6):
  - links with a phase step > 1 rad: unchanged;
  - spectrum in the outer third of the band: 3.2e-11 → 2.0e-7;
  - control with flux 0: unchanged, 2.4e-12;
  - the image shows two cut lines from the tube (left panel) and none in the control (right panel).
- **`a3_drag_kick.out` case 4:** ⟨π⟩ (0.97157, 0.00035) → (0.99412, 0.04801) and ⟨π²⟩/2m +3.06 %. With flux 0
  both are unchanged.
- **In the AB preset itself** (`a4_p02_wrapper.out` case 3): the electron dragged by 4 nm after the wall.
  - Outer-third spectrum 4.4e-9 → 6.6e-6.
  - ⟨k − qA⟩ (−1.94821, 0) → (−1.94268, 0.00359). A pure y-move cannot change k_x without the factor.
  - The event says «та же волна перенесена».

**Suggested fix.**
- After the move, measure what the gauge factor did to the kinetic distribution, e.g. ⟨π²⟩ before and after, or the
  spectrum in the outer third against `REGRID_TOL`.
- Refuse a "same wave" move when it changes beyond a tolerance, saying why: «у трубки потока перенос меняет волну».
- Otherwise state in the event that this is not the same wave.
- Restrict the docstring's claim to the uniform field and to a freshly prepared packet.

### Q2 — should-fix — In a non-uniform field the drag changes the kinetic energy silently

**Location.** `scene.py:2075-2081`; the event `viz.py:788-792`.

**Evidence.** `a3_drag_kick.out` case 3. A charged wave evolved inside a field region with edges, x ∈ [−6, 6] and
B = 0.5, is moved out by (12, 0).
- ⟨π²⟩/2m 1.378396 → 1.245253, i.e. −9.7 %.
- ⟨π_y⟩ 1.02105 → 1.02291.
- The control with B = 0 is exact.

Physically there is no unique "same wave" across a field boundary: ∇χ = A(r) − A(r − s) is impossible where
B(r) ≠ B(r − s). The code's choice is the straight-line (Poincaré) gauge about ⟨r⟩. That is a reasonable choice, but
it is an approximation the owner is not told about.

**Suggested fix.** When B differs between r and r − s where the wave lives:
- say so in the event, e.g. «поле неоднородно: кинетическая энергия изменилась на −9,7 %»;
- or refuse above a tolerance.

Report ⟨π²⟩/2m before and after, in addition to ⟨H⟩, which also mixes in V and the spin energy.

### Q3 — error — p02's `measure()` returns a tuple; every p02 sweep fails

**Location.** `viz.py:1747-1819` (`return m, note`) against `server/lfviz/sweep.py:757`
(`meas, mn = measure() or {}, {}`, then `meas.get(...)`). The sweep expects `measure()` to return a dict, as p01, p03
and p04 do (`p01_gravity/viz.py:507`, `p03_molecules/viz.py:1777`, `p04_fluids/viz.py:1322`).

**Evidence.** `logs/b4_instruments.log` and `shots/b4_p02_quantum_1600x1000_04_sweep_done.jpg`. A sweep of the window
76 / 80 / 84 nm in the double slit — 80 being the current value — fails at all three values:
- «✗ Расчёт остановился на t = 1,70239e-13: Внутренняя ошибка мира — AttributeError — запуск сохранён…»;
- detail: `AttributeError: 'tuple' object has no attribute 'get'`;
- the panel nevertheless shows «Свип № 2: готово … измерено 0 из 3 значений».

No test of a p02 sweep exists. `test_measurables_are_cheap` says "the sweeps call measure alone" but never runs one.

**Suggested fix.**
- Return the dict from `measure()` and keep the notes in a second method, or let the sweep accept `(meas, notes)`.
- Add a p02 sweep test to `test_p02_quantum.py` with a closed-form-checkable target, e.g. the free packet's ⟨x⟩ after
  T for a list of λ.

### Q4 — error — The 2-D → 3-D carry-over breaks on walls, steps and flux planes, and its notices contradict each other

**Location.**
- `viz.py:1010`: `v.setdefault("z", 0.0)` runs for every kind, including `slit_wall`, `step` and `plane`, which have no
  `z`.
- `viz.py:1022` and `1053`: the notes are appended before the add is attempted.

**Evidence.**
- **`a4_p02_wrapper.out` case 6**, and the browser in `logs/b2_p02_delete_world.log` with
  `shots/b2_1600x1000_04_3d_world.jpg`. The double slit carried into space:
  - «Сцена перенесена в новый мир: 0 из 4 объектов; не перенесены: «Стенка с двумя щелями» — Нет параметра «z»; …
    «Поток за щелями» — Нет параметра «z»; …»;
  - then a second notice, «Перенесено … с изменениями: Частица (волновой пакет): … пакет приготовлен заново», about
    the packet that the first notice says was not carried.
- The repository test (`test_a_new_world_of_the_other_dimension_takes_over_what_makes_sense`) covers only a box, a
  ball and a detector.

**Suggested fix.**
- Set `z` / `sz` only for the kinds whose schema has them.
- A wall, a step or a plane across x or y goes into space unchanged.
- Append a carry note only after the object was added. Collect the refusals and the changes into one notice.
- Add the wall and the plane to the test.

The grid and window part of the problem is X3.

### Q5 — should-fix — The throw limit `v_max` ignores the wave's actual spectrum, so a clamped throw is refused

**Location.** `viz.py:612-631` (`_set_vmax`). It uses σ_k = 1/(2 σ) of the packet's initial values. The scene judges
the thrown wave by its measured spectrum (`scene.py:2085-2100`: alias test, `_spec_model`, `_resolution_reason`).

**Evidence.** `logs/b1_p02.log` and `shots/b1_1600x1000_05_hard_throw.jpg`. After the electron reached the double
slit's wall:
- A throw at the automatic scale, 9.98·10¹³ nm/s and far below the limit, is refused: «там или с этой скоростью сетка …
  не передаёт волну частицы рядом с тем, что на неё действует».
- A throw clamped to the limit — readout «ограничено до 6.04·10¹⁴ нм/с» — is refused: «за её полосой оказалось бы
  0,113 спектра волны».
- In space (`logs/b6_p02_3d.log`), after scattering on the ball, the automatic scale's throw of 3.25·10¹³ nm/s is
  refused with an alias fraction of 1.65e-5.

The player's limit and the world's refusal contradict each other.

**Suggested fix.**
- Compute `v_max` from the current wave: the largest |dk| along the throw that passes the alias test and
  `_resolution_reason` on `_spec_model`, e.g. by bisection on the same functions.
- Make the refusal say which test failed. «там или с этой скоростью» leaves the owner guessing whether to move or to
  slow down.

### Q6 — should-fix — A window change with open edges moves the absorbing layers over the wave without saying so

**Location.** `scene.py:1894, 1917`: `in_layers` measures the probability inside the **old** layers. `viz.py:1137-1211`
(`_regrid`) does not show `in_layers` at all.

**Evidence.**
- **Shrinking.** `a4_p02_wrapper.out` case 2, the tunnel preset, window 80 → 56 nm: 2.68e-5 of the probability then
  sits inside the new 5.6-nm layers and will be absorbed. The event says only «отброшено 3,6·10⁻¹⁰».
- **Enlarging.** The part of the wave that was being absorbed in the old layers, with an attenuated profile, becomes
  interior wave. Its share is measured but never shown.

**Suggested fix.**
- Report both shares in the event, refusing above a tolerance or at least warning:
  - the probability inside the new layers;
  - the probability that was inside the old layers.
- Measure `in_layers` on the new layers too.

### Q7 — should-fix — The grid's help promises the 10⁻⁶ rule; other rules refuse first, and one message is wrong for a free packet

**Location.** `viz.py:77-79` (help of «Точек сетки по оси»); `viz.py:1246` (the refusal of `_regrid_refusal`).

**What the help promises.** «грубее — только когда за новой полосой волновых чисел меньше 10⁻⁶ нормы волны».

**What actually refuses first.**
- **The resolution rule.** |k| + 6σ_k ≤ π/d for a free packet, and 2/3 of the band next to anything.
  `a2_refusal_numbers.out`: coarsening refused from 76 points with a spectrum fraction of 4.2e-9. The 10⁻⁶ rule only
  takes over at 70 points (2.4e-6).
- **The objects' physical edges.** Any coarsening of the double slit is refused because of the wall's edge (X10).

**The wrong message.** For the resolution case, p02's refusal says «новая сетка не передаёт волну частицы рядом с тем,
что на неё действует» even when nothing acts on the particle. The engine's own text adds «или потенциал ниже» for a
free packet.

**Suggested fix.**
- Name all three rules in the help.
- Choose the refusal text by the engine's `inter` / `conv` flags.

### Q8 — should-fix — With open edges, a drag of a scattered wave is refused for "crossing the face" while that part is already in the absorber

**Location.** `scene.py:2066-2071` with `schrodinger_nd.wrap_fraction`; `viz.py:794-800` (hint).

**Evidence.** `a5_drag_wrap_open_edges.out`, the double slit:
- At t ≥ 1.3·10⁻¹³ s, 17–60 % of the remaining probability is inside the edge layers.
- Most moves of 3–5 nm are refused, e.g. (−5, 0): 9.9e-3 and (0, 5): 3.2e-5. One of 1 nm is refused at
  t = 1.76·10⁻¹³ s.
- In `a3_drag_kick` a move of (0, 6) was refused for 1.34e-6.

The hint «увеличьте окно» barely helps, because the layers grow with the window (10 % of it, `EDGE_FRAC`).

**Suggested fix.** With open edges, measure only the part of the wave outside the layers' inner faces, or bank what
lies beyond the inner faces as absorbed by "edges" before the move. Say in the event how much of the wave is in the
layers.

### Q9 — nit — A same-window change moves the periodic cell and the edge layers by up to d/2

**Location.** `schrodinger_nd.py:832-836` (`window`); `absorbing_layer`.

**Evidence.** `a1` (odd counts, even counts). The cell [x₀ − d/2, x₀ − d/2 + n d) moves by (d − d2)/2. For even n the
window is asymmetric about its centre, so refining 256 → 512 moves the high layer by d/2. This is exact for the wave,
but the drawn window and the layers shift slightly.

**Suggested fix.** State it in the docstring. Optionally keep the cell fixed by choosing which sample sits at the
centre.

### Q10 — nit — The "regrid" bank can be negative but is labelled «отброшено» / «поглощено»

**Location.** `scene.py` regrid commit (`p.banked["regrid"] += n0 − n1`); `viz.py:1821-1831` (`_det_label`);
measurables «Изменение нормы … отброшено».

**Evidence.** A window change through the "both changed" route gains 1.3e-12 from the quadrature
(`logs/b1_p02.log`: «больше на 1,3·10⁻¹²»). The measurable then shows −1.2963·10⁻¹²
(`shots/b1_1600x1000_08_live_size_100.jpg`).

**Suggested fix.** Use a neutral label, e.g. «изменение нормы сменой сетки (+ — прибавилось от квадратуры)».

### Q11 — nit — For a split wave, the handle, the "λ" and the drag reference are ⟨r⟩ and ⟨k⟩, which may be empty or mean nothing

**Location.** `viz.py:1656-1680` (`_positions`), `viz.py:597-610` (`_set_momentum`), `viz.py:767-776`.

**Description.** After a wall, ⟨r⟩ of the reflected plus transmitted wave can sit where there is no probability.
2π/|⟨k⟩| after a throw is not the de Broglie wavelength of either part. «Приготовить пакет заново» then uses it.

**Suggested fix.** Label the handle and the λ written by a throw «среднее» in the inspector. Optionally offer «взять
пакет из текущего состояния» (centre ⟨r⟩, k ⟨k⟩).

---

## Part B findings (the laboratory in a browser)

### X1 — error — Sweeps over an object's parameter are refused in every playground

**Location.** `server/lfviz/sweep.py:147`: `pal = getattr(viz["simulation"], "PALETTE", {})` reads the **class**
attribute. p01–p04 set `self.PALETTE` per instance (`p01_gravity/viz.py:475`, `p02_quantum/viz.py:373`,
`p03_molecules/viz.py:545`, `p04_fluids/viz.py:529`). The base class has `PALETTE: dict = {}`. Only the test fixture
p97_osc has a class-level palette, so `instruments_checks.mjs` passes.

**Evidence.**
- `b5_sweep_api.out`: p03 «у «Аргон» нет параметра «T»; есть: нет»; p04 «у «Цилиндр» нет параметра «radius»; есть:
  нет».
- In the browser, p02 (`logs/b4_instruments_width.log`): «у «Стенка с двумя щелями» нет параметра «width»; есть:
  нет». The panel's «Что менять» offers exactly these parameters.
- A sweep over a law works in p04: ν 0.001 / 0.002 → Mach 0.04837 / 0.04944 (`b5_sweep_api.out`).

**Suggested fix.**
- Validate against the palette of the world's last scene. The record has the objects. The palette can be rebuilt by
  the worker, or the run's header carries it (`playground.palette`).
- Add a sweep test over an object parameter on a real playground.

### X2 — error — Delete does not delete in p02's plane window; it shows «Срез не построен»

**Location.** `player/js/playground.js:658-661`: `if (sc && sc.state && sc.state.selected) return;`. Then
`player/js/env3d.js:172-176` sends `view {op: remove}` for the selected window. The plane world's window 1 is always
"selected" — it has the orange frame.

**Evidence.** `logs/b2_p02_delete_world.log` and `shots/b2_1600x1000_01_delete.jpg`.
- The detector was clicked in the window: `sel o2`, `sliceSel 1`.
- Delete gave 0 scene removes, 1 view command, and the toast «Срез не построен: у этого мира нет запросов просмотра».
- The same happened on a second try, and with the flux plane (`logs/b1_p02.log`).
- In p01's 3-D view Delete works (`logs/b3_worlds.log`: «scene removes 1»).

The panel's help says «Delete — удалить».

**Suggested fix.**
- When the world has no view requests, or the selected object belongs to the scene, give the key to the object.
- Do not mark the 2-D world's main window as a selected slice.

### X3 — should-fix — «Новый мир» into the other dimension offers no grid or window; the carried scene does not fit

**Location.** `player/js/player.js:381`: `paramForm(…, { only: (p) => !p.live })` hides `n3`, `size` and `edges`,
which are live. `player.js:410-412` then sends the current world's `size` with the old `params.n3`.

**Evidence.** `shots/b2_1600x1000_03_new_world_3d_chosen.jpg`: the form has only «Пространство» and the seed. The 3-D
world gets 64³ over the 80-nm window, a step of 1.25 nm. So:
- the detector's 3-nm edge is refused (it needs ≥ 3.79 nm);
- the electron's λ = 2 nm is refused («нужно λ больше 4,78 нм»).

The owner must start an empty world, fix the grid live and rebuild by hand — the opposite of P16.1's «a new world
that is unavoidable … takes the scene over».

**Suggested fix.**
- Show the new dimension's grid and window in the form when «перенести сцену» is on.
- Default them to what the carried scene needs: the same step as now and a cube over the scene's extent.
- Or try the carried objects against the proposed grid and say what to change before the world starts.

### X4 — should-fix — In p03 and in p01's Kerr world, the default throw is absurd and refused, without saying "lower the throw scale"

**Location.** The playgrounds' handles: p03 (`p03_molecules/viz.py:370-385`) and p01 Kerr bodies
(`p01_gravity/viz.py:1391`) declare no `velocity_max`, so the scale «авто» = ×1 (`player/js/playground.js`).

**Evidence.** `logs/b3_worlds.log` and `shots/b3_p03_1600x1000_02_end.jpg`.
- **p03.** A modest flick gives «бросок: v = (1.88·10¹²; −6.03·10¹¹) м/с (×1, авто)». The refusal speaks of the
  schema: «Скорость центра масс vx, м/с: 1,263·10¹² — больше наибольшего 100000».
- **p01 Kerr.** «бросок: v = (31 100; 19 800; −7 270)   (×1, авто)», with no unit in the readout. The refusal:
  «скорость броска … 2.33 c — не меньше 0,99 c». This refusal does say «уменьшите масштаб броска».

**Suggested fix.**
- Declare `velocity_max`: for p03, e.g. a few times the thermal speed; for p01 Kerr, 0.99 c in the world's units.
- Show units in the readout.
- In p03 translate the schema's range error into «бросьте медленнее или уменьшите масштаб броска».

### X5 — should-fix — In p02 the throw limit shown is not the limit applied

This is the browser symptom of Q5; the fix is there.

**Location.** The player's clamp readout and the world's refusal.

**Evidence.**
- `shots/b1_1600x1000_05_hard_throw.jpg`: the readout says «ограничено до 6.04·10¹⁴ нм/с», and then the toast refuses
  it.
- `logs/b6_p02_3d.log`: a 3-D throw at the automatic scale is refused.

### X6 — should-fix — Velocity units and number formats are inconsistent

**Location.** `viz.py:186-188` (`vx`, `vy`, `vz`, `v_max` in «нм/с»), `viz.py:783`; `player/js/playground.js` (the
throw readout); `player/js/instruments.js` (numbers in scientific notation); p01's events.

**Evidence.**
- p02's throw readout and events give «9.98·10¹³ нм/с», «1e+14 нм/с». The same world's instruments give
  «363,695 км/с».
- **Mixed decimal separators**, comma and point in one line:
  - «бросок: v = (3.25·10¹³; −9.76·10¹²; −0,137) нм/с (×0,0424, авто)»;
  - in «Приборы»: «−3.09193·10⁻¹⁷ нм», «5.03297·10⁻⁶⁸»;
  - in a sweep: «5·10⁻¹⁴ с мира от t = 1.20239·10⁻¹³»;
  - in p01's events: «G M/c² = 14.7663 → 29.5325 км», «спин 0.9 → 0.5».
- Round-off is shown as data: ⟨y⟩ = −3·10⁻¹⁷ nm.

**Suggested fix.**
- Use km/s (or m/s) for p02's velocities in the readout and the events, in step with «Приборы».
- Use one Russian number formatter everywhere: a comma, including in the mantissa of x·10ⁿ.
- Show values below the reading's own resolution as 0.

### X7 — should-fix — The sweep form for a femtosecond world

**Location.** `player/js/instruments.js:415`: `F.duration` defaults to `"1"` in the world's time unit «с».
`instruments.js:483-493`: «Запустить» is disabled after a run or a cancel, while the old estimate stays shown.

**Evidence** (`logs/b4_instruments_size1s.log`, `logs/b4_instruments.log`):
- **Estimate.** With the default «Сколько считать, с» = 1 in p02, whose history is 10⁻¹³ s, the estimate reads «≈
  2818381528 ч 21 мин». The owner must type «5e-14».
- **Cancel.** «✕ отменить» works: «Отменено: посчитано 0 из 3 значений». But «▶ Запустить свип» then stays disabled
  under the previous estimate's text. The reason appears only after another field changes.
- **A failed sweep.** It shows «готово» with «измерено 0 из 3 значений» (Q3).

**Suggested fix.**
- Give the duration in the world's display unit (ps or fs for p02), with a default taken from the record, e.g. a tenth
  of the world's span.
- After a run, replace the estimate's text with «Сначала «Оценить»».
- Show «не посчитан» or «ошибки во всех значениях» when nothing was measured.

### X8 — should-fix — Layout: the top bar wraps, and toasts cover each other

**Location.** `player/run.html` top bar (`.topbar`); the toast stack.

**Evidence.**
- **The top bar wraps to two rows**, so the column heights jump:
  - at 1600×1000 in p01 (`shots/b3_p01k_1600x1000_fail.jpg`);
  - in any world after «Новый мир», where the world selector is added (`shots/b2_1600x1000_04_3d_world.jpg`);
  - at 1280×800 (`shots/b6_1280x800_06_plane_dark.jpg`).
- **Toasts are drawn on top of each other.** After a carry-over, the notice that lists what was **not** carried is
  covered by the second notice (`shots/b6_1280x800_06_plane_dark.jpg`). Refusals pile up over the instruments panel
  (`shots/b1_1600x1000_08_live_size_100.jpg`).

**Suggested fix.**
- Let the subtitle and the badges shrink with an ellipsis before anything wraps, and move the world selector into the
  shrinking part.
- Stack toasts vertically with a gap, newest on top. Keep the error and notice texts readable until they are dismissed.

### X9 — should-fix — The sweep's «Что менять» doubles units and lists the hidden law

**Location.** `player/js/instruments.js:398`: `x.label + ", " + x.p.unit`. p02's labels already contain the unit.

**Evidence.** `logs/b4_instruments.log`:
- «Закон: Размер окна, нм, нм», «Высота, эВ, эВ», «Число щелей, щелей», «Центр: x, нм, нм»;
- «Закон: Точек сетки по оси» appears twice, for `n2` and `n3`, in a plane world where `n3` does not apply.

**Suggested fix.**
- Do not append the unit when the label already ends with it, or drop the units from the labels and use `Param.unit`.
- Hide laws whose `show_if` is false for the world.

### X10 — should-fix — Any coarsening of a preset is blocked by the default automatic edges, with no bulk action

**Location.** `viz.py:400-414` (`_edge`, `_keep_edge`): an edge of 0 freezes at 1.05 × 3.03 steps of the grid it was
added on.

**Evidence.**
- The double slit cannot go 256 → 192: the repository test asserts this, and the browser showed the same refusal for
  the window change.
- Each such refusal names the object and the needed width, which is good. But the owner must edit every object's edge
  by hand before coarsening.
- Owners set 0 to mean «самый резкий край, который передаёт сетка».

**Suggested fix.** In the refusal, offer one action: «сделать края всех объектов с автоматическим краем по новой сетке
(потенциал изменится: края станут шире на …)». Or explain at the parameter that 0 means "the sharpest of the grid at
the moment of adding".

### X11 — should-fix — The packet's «Центр пакета» in the inspector is not where the packet is

**Location.** `viz.py:712-792` (`_set_packet` writes the drag's target into `x`, `y`); `viz.py:2083-2098`
(«Приготовить пакет заново» uses `values`).

**Evidence.** `a4_p02_wrapper.out` case 5. After a drag and a throw, the wave moved on to ⟨x⟩ = −12.57 nm. The
inspector still shows x = −19.17. «Приготовить пакет заново» puts a fresh packet back at −19.17, 6.6 nm behind.

**Suggested fix.** Label the fields «Центр при приготовлении». Show the current ⟨r⟩ and ⟨k⟩ (the «сейчас» line)
next to them. Or offer «приготовить там, где волна сейчас».

### X12 — nit — Event texts

**Location.** The framework's edit event (`server/lfviz/playground.py`) and p02 / p03 texts.

**Evidence** (`logs/b1_p02.log`, `logs/b3_worlds.log`, `logs/b2_p02_delete_world.log`):
- **Full labels inside the events:**
  - ««Электрон» перемещён в (Центр пакета: x, нм = −10,81, Центр пакета: y, нм = 8,378)»;
  - «(Центр области: x, нм (0 и размер 0 — весь ящик) = 6,975, …)»;
  - «брошен со скоростью (Скорость vx, нм/с (= ħk₀/m; задаётся броском) = 1e+14, …)».
- **Gender:** ««Стенка с двумя щелями» перемещён».
- **An empty event «»** for a no-op set in p03.
- **Double parentheses:** «(не изменилась (до округления))».
- **«волна пересчитана точно»** in a world without particles.

**Suggested fix.**
- Use short forms such as «перемещён в (−10,8; 8,38) нм» and «брошен: v = (…) км/с».
- Use neutral wording: «объект «…» перемещён».
- Skip events with no text.

### X13 — nit — Axes

**Location.** The 2-D window's axes (`player/js/slices.js` / canvas); `player/js/instruments.js` plots.

**Evidence** (`shots/b0_p02_double_slit_1600x1000.jpg`, `shots/b2_1600x1000_04_3d_world.jpg`):
- ticks at −20,1; −0,156; 19,8; 39,7 instead of round values;
- the last x label is clipped («39,»);
- a new world's empty plots show «200 мс … 800 мс» while the world runs in ps.

**Suggested fix.** Round ticks with a 1–2–5 rule. Leave room for the last label. Use the record's time unit for an
empty plot.

### X14 — nit — p04: the message after a change of the largest speed reports a 2 % mass change

**Location.** p04's `set_live` message. Its physics belongs to the p04 reviewer; this is only the user's view.

**Evidence.** `b7_p04_umax_api.out`: u_max 0.6 → 0.15 m/s gives «перенос изменил массу на 0,0171 кг/м» of
0.895 kg/m, i.e. 1.9 %. The text says «учтено в балансах», but not whether the fluid really changed.

**Suggested fix.** Say in one phrase what the owner should conclude, e.g. «перенос на новую сетку исказил массу на 1,9
% (погрешность пересчёта, не физика)». Let the p04 reviewer judge whether it should be refused.

---

## Other observations from the browser (no finding)

**Timings** [useful]:
- a drag or a throw is applied in about 0.5 s (p01–p04);
- p02 grid changes: 1.8 s in 2-D at 256² → 384² or for an 80 → 100 nm window; 0.35 s in 3-D at 64³ ↔ 96³;
- p01 hole mass, spin and charge: 0.05–0.4 s; binary mass: 0.03 s;
- p03 box: 0.35 s; p04 grid, domain and u_max: 0.3 s.

**Selection and camera** [useful]. The selection survives a drag, the camera does not move during a drag, and the
view follows the window change without jumping.

**Refusals that say what to change** [useful]:
- p03, forces → hard: «… 13 пар атомов ближе σ … уменьшите плотность … либо попробуйте в другой момент»;
- p03, wall mode on a periodic axis;
- p02's spectrum, outside and face refusals;
- p01's 0.99 c refusal.

**Messages that explain the physics** [useful]: p01's mass and spin changes (scale, ZAMO, «модель «что если»») and
p03's affine box change («работа над системой W = +126,3 кДж/моль … температура 297,9 → 329 K»).

**Dark theme** [neutral]. Readable in p02 and in «Приборы»; no contrast problem seen.

**CSV** [useful]. Header «t, с» plus the labels and ids; full precision; one row per frame.

**3-D drag in space** [neutral]. A 3-D drag moves in the plane perpendicular to the view, as the help says, and so
also in z. A packet dragged to z = −4.2 nm was then not carried into the plane (`logs/b6_p02_3d.log`; the refusal says
why).
