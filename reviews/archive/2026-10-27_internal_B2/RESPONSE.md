# Response to the review of batch B2 (P9, P14.1, P13, the shared 3-D environment)

Responder: the working session (not the reviewer), 2026-10-28. Every finding was checked against the code and the
reviewer's scripts and outputs. The reviewer's scripts were rerun after the fixes; their outputs and the responder's
own checks are in `response_checks/`. The review text is unchanged.

| ID | severity | decision | where |
|---|---|---|---|
| B2-1 | error | **fixed** (cause removed, not the tolerance widened) | `lfphys/lfphys/core/spin_transport.py` (`polygon_burns`), v09 tests |
| B2-2 | error | **fixed** | `v09_thomas_3d/viz.py`, `web/view.js`, `player/js/scene3d.js` (`setBox`), `player/js/env3d.js`, `RULES.md` §3 |
| B2-3 | should-fix | **fixed** | `v09_thomas_3d/viz.py` (`_accumulated`, `_per_fuel`, check `holonomy_accumulated`), `engine/loops.py`, `web/view.js` |
| B2-4 | should-fix | **fixed** | `player/js/env3d.js`, `v09_thomas_3d/viz.py` (the volume's `quantity`) |
| B2-5 | should-fix | **fixed** | `lfphys/tests/test_lorentz_3d.py::test_penrose_circle` |
| B2-6 | nit | **fixed** (reframed and measured) | `v09_thomas_3d/viz.py` (`_round_bound`), README, tests |
| B2-7 | nit | **fixed** (engine and player) | `lfphys/lfphys/core/geometry.py` (`plane_cut`), `player/js/scene3d.js` (`planeBox`), `lfphys/tests/test_geometry_3d.py` |
| B2-8 | nit | **fixed** | `lfphys/lfphys/core/lorentz.py` (`add_velocities`, `apparent`), `lfphys/tests/test_lorentz_3d.py` |
| B2-9 | nit | **fixed** | `lfphys/tests/test_spin_transport.py` |
| B2-10 | nit | **fixed** | `lfphys/PLAN.md` (P13 row) |
| R-1 | found while processing [error in earlier] | **fixed** | `v09_thomas_3d/web/view.js` (the result block and the legend were never shown) |

## B2-1 (error) — holonomy checks failed on correct runs: fixed at the cause

Agreed with the diagnosis: the measured round-off (the disagreement of the two representations) measures the flight
of the given burns, not their construction. `polygon_burns` built the next burn from the next vertex seen in the
comoving frame, `M⁻¹ U(w)`: a difference of products of entries up to cosh η, i.e. a cancellation of ~ε cosh²η, which
in a tilted plane bends a large loop out of its plane by more than the flight's own round-off.

Fix: `polygon_burns` now works in extended precision (numpy `longdouble`, 64-bit mantissa on x86-64: resolution 1e-18),
the comoving frame advanced by the closed-form boost of each burn **as rounded to float64 for the flight**, so each
next burn makes up for the rounding of the previous ones and the last returns to rest. The construction error drops
~2000× below the flight's; the comparisons keep their tolerance of 8 × the measured round-off of the flight, which now
bounds what they compare. (Widening the tolerance to the a priori bound, the review's option (a), was not taken: it
would have hidden real errors of 1e-9 behind a bound of 1e-5.)

Verified:
* the reviewer's grids rerun: `c06` (planar loops, ρ ∈ [2, 3], random planes): **160 of 160 pass** (before: 23 failed);
  `c03` (the whole schema): **255 ran, 25 refused** (helices too close to light, by design), **0 failed** (before: 3);
  `c07` (small ρ): 200 of 200 pass (`response_checks/c03_…_after.txt`, `c06_…_after.txt`, `c07_…_after.txt`);
* the reviewer's attribution `c05`: polygon ρ = 3, 4 turns: dR = 2.6e-9 against tol 4.3e-8 (was 5.8e-8 against
  4.3e-8); the triangle ρ = 2.97: 4.1e-12 against 1.0e-10 (`response_checks/c05_…_after.txt`);
* new test `test_large_planar_loops_in_tilted_planes` (triangles and polygons, ρ 2 – 3, repeated, random tilted
  planes), with the accumulated angle of B2-3 against the area.

## B2-2 (error) — the header revealed results at t = 0: fixed

* The header keeps only the programme: the pieces, the fuel they plan, the loop's closed form as a description. The
  lab duration, the proper time at the end and the largest γ are sent at the closure (in the `holonomy` message) and
  shown in the result panel; the frames carry the largest γ so far (`gamma_so_far`), shown in «Сейчас».
* Found on the way, the same kind: the default speed and the speed range were derived from the computed duration.
  They now come from the programme's own clock, fuel / thrust (an input).
* Ordinary space: the box starts at the input scale c²/a and doubles whenever the revealed path nears its edge (a new
  accumulative message `box`, drawn by `scene3d.setBox`; `RULES.md` §3). It never frames the future trajectory.
* Tests: `test_the_result_waits_for_the_closure` now checks the header's fields and the speed;
  `test_the_lab_box_grows_with_the_path` (the revealed path fits and the box is not larger than needed). Browser
  (`response_checks/rc_browser*.mjs`, `rc_browser.txt`): at t = 0 the panel shows the programme and «Итог появится,
  когда петля замкнётся»; at the end the durations and γ; the lab box grew 0.97 → 3.87 ly while the run played.

## B2-3 (should-fix) — the accumulated angle was the closed form: fixed

* The run computes the accumulated angle of a planar loop: the gyroscopes' angle about the loop's normal, unwrapped
  along the samples (`viz._accumulated`; steps ≤ 0.1 of fuel, rotation per unit fuel < 1). The result panel shows it;
  the closed form is its reference in a new check `holonomy_accumulated` (tolerance 8 × the measured round-off + the
  reference's own rounding). Example (thomas preset): 2.1201662968 rad computed, 2.1201662968 the area.
* A non-planar loop flown m times is compared with the bound by ONE loop: the SU(2) angle at the end of the first
  flight (an exact piece end) against the bound at that loop's fuel (`viz._per_fuel`, `info.loop_pieces`); test
  `test_rotation_per_fuel_of_repeated_nonplanar_loops` (crown, m = 1 and 3: the same ratio).

## B2-4 (should-fix) — the drag preview read the volume with a slice's scale: fixed

`env3d.js` keeps the `quantity` of the `volume` message and uses it for previews sampled from the volume (v09 sends
the volume's own peak, `field_peak × scale`); the slice's quantity is no longer used there. Test: the volume message
carries its quantity (`test_field_and_slices_against_gauss_bonnet`). As in the review, the drag itself was not
scripted in the browser; the code path is the evidence.

## B2-5 (should-fix) — the Penrose test did not test size or position: fixed

`test_penrose_circle` now checks (1) coplanarity, (2) that each outline ray's grazing point lies on the body (the
contracted ellipsoid |x⊥|² + γ²x∥² = r² about the centre at the emission time, to 1e-10), and (3) by brute force that
the light-time images of 40 000 points of the body's surface fall inside the circle and reach its rim. Mutation check
(`response_checks/rc_mutate_penrose.py`): a missing contraction and a radius 1 % too large both make the test fail.

## B2-6 (nit) — the stated margin of the a priori bound: fixed

The quantity is an alarm level, empirical, and now says so (docstring, check note, README). Its model includes a
turn's exponent norm s·max(1, κ) (small circles have κ = coth ρ ≫ 1), and its coefficient is 1e-11. Measured over the
reviewer's grids rerun (640 worlds): the round-off stays ≥ 46× below it (Thomas loops at ρ = 3), ≥ 140× for the other
loops. The comparisons do not use it; they use the measured round-off. The edge test covers both corners (ρ = 3 and
ρ = 0.05, tilted) and asserts a margin of 20.

## B2-7 (nit) — `plane_cut` lost a corner: fixed

Corners on the plane are collected once each in their own loop, then only strict crossings inside the edges; the same
in the player's `planeBox`. Test `test_plane_cut_through_corners` (faces, diagonal planes, a hexagon, a plane touching
one corner refused). Reviewer's `c09` rerun: faces and diagonals 4 distinct corners
(`response_checks/c09_…_after.txt`); browser: the diagonal plane's outline has 4 vertices.

## B2-8 (nit) — `add_velocities` and `apparent` at their edges: fixed

`add_velocities` refuses a sum that rounds to |w| ≥ c (with the advice to compose by rapidities) and states its
domain; `apparent` refuses a point at the observer. Test `test_edges_are_refused_not_silent`.

## B2-9, B2-10 (nits): fixed

The duplicated BMT case is replaced by g = 2.3 in E at a general momentum; the plan states 1121 comparisons (12 of
them known library-side errors kept as strict xfails) and 17 supporting tests.

## R-1 (found while processing) [error in earlier]: v09's result panel was never shown

`panel(title, body)` takes one body; v09's view passed the result block and the legend as a third argument, which was
ignored: the holonomy result and the colour legend never appeared on the page. Neither the tests (Python) nor the
first browser checks (they read layers and windows, not this panel) nor the review caught it. Fixed (one body element
per panel); browser check `rc_browser_panel.mjs` (before / after in `rc_browser.txt`).

## Not changed

* The reviewer's notes "checked and found correct" (conventions, Thomas precession sign, field transformation,
  searchlight, BMT forms, hyperbolic geometry, exactness of the pieces, the field tolerance, P13's xfail claims and
  licences, the v08 refactor) — nothing to do.
* The reviewer could not fetch Osserman 1978; the responder had verified the quotation against the text on 2026-10-27
  (the Washington mirror of the paper, eq. (4.23) and "with equality in each case only for geodesic circles", Schmidt
  1940 for K = −1), as the docstring says.
* `test_light_time_image`'s observer direction reuses the code's transformation (noted by the reviewer as a weak spot):
  it is covered independently by the aberration closed forms and the Terrell check of the same function; left as is.

## Test runs after processing (2026-10-28, Docker, GPU 0)

* engine `lfphys`: **497 passed** (with the GPU tests);
* visualizations (all, v08 on GPU 0): **384 passed** (v09: 39);
* the comparison suite in `light-funnel-ext`: **1126 passed, 12 xfailed** (the known library-side errors);
* the reviewer's scripts rerun (`response_checks/*_after.txt`): `c03` 255 ran / 25 refused / 0 failed; `c06` 160 / 0
  / 0; `c07` 200 / 0 / 0; `c05` the attribution within tolerance; `c09` faces and diagonals with 4 corners; `c02`
  the edges now refused with their reasons (B2-8);
* browser (own server, port 8499, engine read-only; stopped and checked gone): no page errors; `rc_browser.txt`.
