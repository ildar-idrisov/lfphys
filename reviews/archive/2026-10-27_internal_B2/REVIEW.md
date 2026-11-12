# Review of batch B2 (P9, P14.1, P13, the shared 3-D environment)

Status: **awaiting processing**

Reviewer: internal (subagent, not the author of the batch), 2026-10-27.

Scope: `lfphys/lfphys/core/lorentz.py`, `lfphys/lfphys/core/spin_transport.py` and their tests;
`visualizations/v09_thomas_3d/`; `lfphys/tests/external/` (P13) with `lfphys/sources/dependencies.md` §10 and
`lfphys/tests/conftest.py`; the shared 3-D parts (`visualizations/server/lfviz/planes3d.py`,
`visualizations/player/js/env3d.js`, `scene3d.js`, `slices.js`, `lfphys/lfphys/core/geometry.py` `plane_cut` /
`plane_points` / `inside_box`) and v08 moved onto them. The batch is uncommitted; the diff is against 188bb08.

Environment: Docker images `light-funnel-viz:latest` (959a1b91570e) and `light-funnel-ext:latest` (428f06b70151), CPU
(v08's tests on GPU 0 only). Scripts in this folder mount `engine/` at `/lf` (each script's header has its command);
their outputs are in `out/`. Line numbers refer to the working tree on 2026-10-27.

## Summary

| ID | severity | where | one line |
|---|---|---|---|
| B2-1 | error | `v09_thomas_3d/viz.py:325-344` | the `holonomy` / `holonomy_su2` tolerance "8 × the two representations' disagreement" misses the error of building the burns: correct runs are shown **failed** (23 of 80 triangle / polygon worlds at ρ ∈ [2, 3] in a tilted plane) |
| B2-2 | error | `v09_thomas_3d/viz.py:518-521`, `web/view.js:25-35`, `viz.py:130-134` | causality: the header at t = 0 reveals the manoeuvre's lab duration, the craft's proper time at the end and the largest γ; view.js shows them before the run's time reaches them |
| B2-3 | should-fix | `viz.py:352-354, 451-454`, `web/view.js:42-45` | the "accumulated angle = area" shown as the result of planar loops (and "area / bound") is the closed form, not computed by the run; for non-planar loops the ratio uses the SU(2) angle mod 4π |
| B2-4 | should-fix | `player/js/env3d.js:147-149` | a drag preview from the volume reads values with the last slice's peak while the volume is normalised to the field's global peak: v09's readout is off by the ratio of the two peaks (×0.60 in an example) |
| B2-5 | should-fix | `lfphys/tests/test_lorentz_3d.py:189-207` | the Penrose test cannot detect a wrong size or position of the outline (coplanarity only; the "grazing point" part is a tautology). The code itself is right (brute force, c02) |
| B2-6 | nit | `v09_thomas_3d/README.md` (Checks, Tests), `viz.py:304-308`, `tests/test_v09_thomas3d.py:101` | "measured ≥ 3× below the a priori bound over the schema's range" is not true (2.78 found); the bound's coefficient is empirical; the edge test covers one corner of the schema only |
| B2-7 | nit | `lfphys/lfphys/core/geometry.py:312-335`, `player/js/scene3d.js:41-56` | `plane_cut` (and the player's `planeBox`) drop the corner (x_max, y_max, z_max) when the plane passes through it and repeat other corners: face and diagonal planes are outlined as triangles |
| B2-8 | nit | `lfphys/lfphys/core/lorentz.py:163-170, 333-348` | `add_velocities` can return \|w\| ≥ c for near-c inputs without notice; `apparent` returns NaN without notice for a point at the observer |
| B2-9 | nit | `lfphys/tests/test_spin_transport.py:262` | the BMT longitudinal-rate test lists the same case twice ((2.6, "E") and (2·(1 + 0.3), "E")) |
| B2-10 | nit | `lfphys/PLAN.md:104` | "1138 comparisons": the suite has 1121 comparison rows and 17 supporting tests |

What was verified and found right is listed after the findings ("Checked and found correct"), with the scripts.

## Findings

### B2-1 (error) v09: the holonomy checks fail on correct runs; the tolerance does not bound the error it is meant to

**Where.** `visualizations/v09_thomas_3d/viz.py:325` (`tol = max(8 * est, ...)` for `closed`), `:333` (the same for
`holonomy` and `holonomy_su2`), `:310-315` (`_round_est`: the disagreement of the 4 × 4 and the SL(2, C)
representations). README "Checks": "`holonomy` ... 8 × the measured round-off".

**What is wrong.** The measured quantity `est` is the disagreement of two representations that fly **the same pieces**.
It measures the error of flying them. It cannot see an error common to both: the pieces of the triangle and polygon
loops are built in float by `spin_transport.polygon_burns` from 4 × 4 matrices with entries up to cosh(2ρ) (≈ 200 at
ρ = 2.7). Their rounding makes the flown loop a slightly different (slightly non-planar, when the plane is tilted so
that its vertices have rounding in all three components) loop, and its rotation differs from R(n, −A) by much more than
the flying error. The check then shows **failed** although the physics and the engine are right. The tests do not see
it: `test_the_edges_of_the_schema` runs the corner ρ = 3 only in the default plane (normal along y, vertices exactly in
the xz-plane, so no out-of-plane rounding), and `test_planar_loops_in_any_plane` tilts the plane only at ρ ≤ 1.1.

**Evidence.**
* `c03_v09_grid.py` → `out/c03_v09_grid.txt`: 280 random points of the schema, 255 ran; 3 failed `holonomy` (two
  triangles at ρ = 2.69 and 2.97, a polygon at ρ = 3), one of them `holonomy_su2` as well.
* `c06_v09_grid_planar_large.py` → `out/c06_v09_grid_planar_large.txt`: the planar loops at ρ ∈ [2, 3] in random planes:
  23 of 160 worlds fail — 9 of 40 triangles, 14 of 40 polygons (Thomas loops and circles, which are turns, pass).
* `c05_holonomy_tolerance.py` → `out/c05_holonomy_tolerance.txt`, the attribution in 40-digit mpmath (the burns v09
  built, flown exactly):

  | case | dR (what the check compares) | tol = 8 est | engine vs exact flight of its own burns | exact flight vs R(n, −A) of the float vertices | closed form vs exact area |
  |---|---|---|---|---|---|
  | triangle ρ = 2.69, 3 turns | 1.50e-10 | 7.08e-11 | 5.0e-12 | **1.5e-10** | 7e-14 |
  | polygon ρ = 3, 24 sides, 4 turns | 5.83e-8 | 4.26e-8 | 2.6e-9 | **5.8e-8** | 1.9e-11 |
  | triangle ρ = 2.97, 2 turns | 2.43e-10 | 1.75e-10 | 1.3e-11 | **2.5e-10** | 1e-13 |

  `est` describes the flight well (5e-12 against est 8.9e-12); the error is in the burns' construction, outside what
  `est` measures. The a priori bound of the same run (2.9e-7, 1.2e-5, 9.1e-7) would have covered it.

**Fix (suggestions).** Either (a) take the tolerance from an error model that includes the construction of the
pieces (the a priori bound `_round_bound()` covers all cases found; or a term like c ε cosh²(η_max) per built burn,
measured over tilted planes at ρ ∈ [2, 3]), or (b) measure the construction error too: rebuild the burns by a second
route (e.g. `polygon_burns` from SL(2, C) matrices, or from the exact geodesic directions by `relative_velocity` and
the transported frame) and take the disagreement of the two sets of burns into `est`, or (c) compare the run against the
closed form of the loop actually flown (the vertices recomputed from the flown states). Add a test with tilted planes
at ρ ∈ [2, 3] for triangle and polygon. The same reasoning applies to `closed` (tol 8 est, also `polygon_burns`), which
did not fail in 565 worlds (c03 + c06 + c07) but has no margin argument. How a failed row reads in the panel
(`c13_failed_row.py` → `out/c13_failed_row.txt`): `holonomy` value 147.66002551787°, ref 147.66002550708°, rel 7.3e-11
against tol 7.08e-11, ✗; `holonomy_su2` 9.4e-11 against 7.08e-11, ✗; `closed` and `roundoff` pass.

### B2-2 (error) v09: the header reveals results of the run at t = 0 (causality, RULES.md §2.2)

**Where.** `viz.py:518-521` (header `loop`: `T_end`, `tau_end`, `eta_max`), `web/view.js:25-35` (`drawLoop()` on the
header: «время манёвра: T_end лет по часам покоя, tau_end лет по часам корабля», «наибольшая γ»); lab space: `viz.py:130-134`
(`scene3d.box` from the whole future trajectory).

**What is wrong.** The craft's proper time at the end of the manoeuvre (a clock reading — the example RULES.md §2.1
names), its lab duration and the largest γ it will reach are consequences computed from the whole manoeuvre; they are
shown in the panel «Манёвр и голономия» as soon as the world starts, before the run's time reaches the end. The
README and `test_the_result_waits_for_the_closure` claim "nothing about the result appears before the closure", but
the test checks only the `holonomy` message, the check and the arrow. In lab space the scene's box is the bounding box
of the whole future trajectory (its extent is revealed by the framing at t = 0; a minor point of the same kind).

**Evidence.** `c08_v09_reveal_and_preview.py` → `out/c08_v09_reveal_and_preview.txt` (a): at t = 0 the header carries
`T_end` = 8.95 yr, `tau_end` = 6.96 yr, `eta_max` = 0.8 for the preset thomas; the lab preset's box at t = 0 is the
trajectory's. As rendered at t = 0 in the browser: section "Browser check" below (`out/browser/c10_v09_thomas_t0.png`).

**Fix.** Keep in the header only the planned programme (pieces, planned fuel); show the lab and proper time and the
largest γ so far from the frames (they already carry t, τ and γ) and the totals in the closing `holonomy` message.
For the lab box, frame by a bound from the inputs, or grow the box as the path is revealed. Extend the test to the
header's fields.

### B2-3 (should-fix) v09: the "accumulated angle" of planar loops is the closed form, shown as the result

**Where.** `viz.py:451-454` (the `holonomy` message: `reference` and `per_bound = reference / bound` for planar
loops), `:352-354` (`fuel_bound`: `acc = info["reference"]` for planar loops, `h["su2_angle"]` otherwise),
`web/view.js:42-45` («накопленный угол = площадь», «площадь / граница» in the result panel).

**What is wrong.** RULES.md §2.1: closed forms may appear only as references next to the computed value, never in its
place. The run computes the SO(3) rotation (angle in [0, π]) and the SU(2) element (angle in [0, 2π]); the accumulated
angle (e.g. 16.99 rad for two circles of ρ = 1.5) is never computed by the run, but the result panel shows the closed
form under «накопленный угол = площадь» and the ratio «площадь / граница» built from it, as results. For non-planar
loops the ratio uses the SU(2) angle in [0, 2π]: for a loop flown m ≥ 2 times it is the accumulated angle mod 4π
against the bound at m times the fuel, which is not a meaningful comparison (it is marked "information", but the
number is shown).

**Evidence.** `out/c08_v09_reveal_and_preview.txt` (c): circle ρ = 1.5, two turns: computed SO(3) angle 1.8547, SU(2)
angle 4.4285; shown "accumulated" 16.9949 = the closed form (16.9949 mod 4π = 4.4285).

**Fix.** Compute the accumulated angle in the run: the gyroscope frame relative to the pure-boost frame, `Track.O`,
is continuous along the samples and, for a planar loop, is a rotation about the fixed normal at every sample, so its
signed angle about n unwrapped along the samples ends at the accumulated −A (the samples are ≤ 0.02 of fuel apart; for
non-planar loops the SU(2) path can be unwrapped the same way). Show that as the result and the closed form as its
reference in the checks.

### B2-4 (should-fix) the drag preview reads volume values with a slice's peak (shared env3d.js; visible in v09)

**Where.** `visualizations/player/js/env3d.js:142-149`; read out by `slices.js:202-210` (`v * q.peak`).

**What is wrong.** While a plane is dragged and a volume exists, `preview()` samples the volume (values normalised to
the field's global peak, v09 `viz.py:168-169`) and passes `quantity: last?.quantity`, whose `peak` is the last full
slice's own peak (v09 `viz.py:236-244`). The window's readout multiplies the two: it shows θ × (slice peak / volume
peak). The preview is labelled «приближённо», but this is a scale error, not an interpolation error.

**Evidence.** `out/c08_v09_reveal_and_preview.txt` (b): preset thomas, a plane βx = −0.6: slice peak θ = 0.5406 rad,
volume peak 0.9081 rad → the readout during a drag shows 0.595 × the value. (Derived from the code and the computed
peaks; not reproduced by hovering in the browser.)

**Fix.** Give the preview the volume's own scale: e.g. `quantity: {...last.quantity, peak: H.field.peak * scale}`, or
let the `volume` message carry its `quantity` and use it in `preview()`.

### B2-5 (should-fix) the Penrose test does not test the outline's size or position

**Where.** `lfphys/tests/test_lorentz_3d.py:189-207`.

**What is wrong.** The test checks that the outline directions are coplanar (a circle on the celestial sphere) and that
each direction d is the light-time image of the point s(d + v) at t = 0 — which holds for any d and any s by
construction (a point at s d at time −s is seen along d). It never checks that this point lies on the body. Since
`sphere_outline` is the aberration of a rest-frame circle (circles map to circles), a wrong radius, a wrong contraction
factor in T, or a wrong centre would still pass.

**Evidence.** `c02_lorentz_edges.py` → `out/c02_lorentz_edges.txt` (1): a brute-force check — 200 000 points of the
body's surface (contracted in the lab), each imaged by `apparent` with light time — finds the outline right (no image
outside the circle; the farthest at its rim to 1e-13…6e-12) for the test's three cases and one more. So the code is
correct; the test would not have caught an error.

**Fix.** Add the brute-force check (or check that the grazing point s(d + v) − (centre at −s) lies on the
ellipsoid |x⊥|² + γ²x∥² = r², i.e. on the sphere in the rest frame).

### B2-6 (nit) v09: the stated margin of the a priori round-off bound is not what is measured

**Where.** `v09_thomas_3d/README.md` (Checks: "measured ≥ 3× below it over the schema's range"; Tests: "the measured
round-off ≥ 3× below the bound"), `viz.py:304-308` (docstring), `tests/test_v09_thomas3d.py:101` (the assertion, at
one corner ρ = 3).

**What is wrong.** Over random points of the schema the smallest bound / est is 2.78 (`out/c03_v09_grid.txt`, circle
ρ = 0.05, 5 turns, plane (110°, 1°)) and 2.95 (`out/c07_v09_grid_small_rho.txt`); the corner ρ = 0.05, 6 turns in the
default plane has 33. The roundoff check itself did not fail anywhere (565 worlds), but the margin claim is false and
the coefficient 1e-12 of the "a priori" bound is an empirical fit, not derived. The edge test covers only the ρ = 3
corner in the default plane.

**Fix.** State the measured margin (≥ 2.7 over N random points) and call the bound empirical, or derive it; test the
ρ = 0.05 corner and tilted planes.

### B2-7 (nit) `plane_cut` loses a corner and repeats others when the plane passes through corners

**Where.** `lfphys/lfphys/core/geometry.py:312-335` (moved here from v08 in this batch) and the player's twin
`player/js/scene3d.js:41-56` (`planeBox`).

**What is wrong.** A corner on the plane is added only when it is the first corner of an edge pair (`abs(da) < 1e-12`
tests corner a only), so the corner with index 7 (x_max, y_max, z_max) is never added, and corners that start two or
three edges are added two or three times. A plane at a face of the box (reachable: the plane's distance is clamped to
the box) or through a diagonal (x = y) gets a triangle as its outline instead of a rectangle. The slice itself is right
(it uses the s and t ranges and `inside_box`), but the drawn outline is not.

**Evidence.** `c09_plane_cut_edges.py` → `out/c09_plane_cut_edges.txt`: face x = 1 → 3 distinct vertices; diagonal
x − y = 0 → 3 distinct; face x = −1 → 8 vertices for 4 corners. The new test `test_plane_cut_by_a_box` uses random
normals only (it would fail its `np.diff(ang) > 0` on repeated vertices).

**Fix.** Collect the corners on the plane in a separate loop over the 8 corners, take strict sign changes on the edges,
and deduplicate; test a face plane and a diagonal plane.

### B2-8 (nit) `add_velocities` and `apparent` at their edges

**Where.** `lfphys/lfphys/core/lorentz.py:163-170`, `:333-348`.

**What is wrong.** (a) `add_velocities((1 − 1e-9) x̂, (1 − 1e-9) x̂)` returns |w| = 1 + 2.2e-16 (a velocity at or above
c) without notice; the next call that takes it (`gamma_of`, `boost`) raises. For inputs near c the composition is
better done in rapidity (tanh of the sum for collinear parts) or the result checked. (b) `apparent` for a point that is
at the observer at the observation time divides by |x_e| = 0 and returns NaN directions with a RuntimeWarning only.
Neither is used at those edges by v09; P14.2 (B3) will build on both.

**Evidence.** `out/c02_lorentz_edges.txt` (4, 5).

**Fix.** Raise or clamp with a message; document the domain.

### B2-9 (nit) a duplicated test case

**Where.** `lfphys/tests/test_spin_transport.py:262`: `(2.6, "E")` and `(2 * (1 + 0.3), "E")` are the same float and
both take the magic momentum (`:270`). One E-field case at a general momentum and g ≠ 2 is missing; perhaps intended.

### B2-10 (nit) the count of comparisons in the plan

**Where.** `lfphys/PLAN.md:104` ("1138 comparisons"). The suite has 1121 comparison rows plus 17 supporting tests
(README §2; the run: 1126 passed, 12 xfailed = 1138 tests).

## Checked and found correct

Physics and conventions (`c01_conventions.py` → `out/c01_conventions.txt`; `c02`, `c04`):
* **Wigner rotation, axis and sense; R vs Rᵀ.** boost(v) boost(u) = diag(1, R_W) boost(u ⊕ v) with R_W = rot3(n, θ),
  n ∥ u × v (u along x, v along y → n = +z). The gyroscopes after the burn loop rest → u → w → rest are turned by
  R_Wᵀ (max deviation 4e-14 over 200 random loops); v09's field rotation vector −nθ equals the transported holonomy
  (3.6e-14). The loop rest → (0.6, 0, 0) → … is anticlockwise about +z and the gyroscopes turn about −z: retrograde.
* **Thomas precession, retrograde.** An independent integration of the 4-D Fermi–Walker equation for uniform circular
  motion at β = 0.5 gives −0.972012150 rad per revolution about +z; −2π(γ − 1) = −0.972012150; the engine's Thomas
  loop gives the same signed angle.
* **Field transformation.** `transform_fields` agrees with the force on a charge at rest in the moving frame
  (q E′ = F_rest built from the lab Lorentz force, ≤ 1e-15) — an independent check of Jackson's 11.149 and the sign of
  `field_tensor`; the engine's test adds Λ F Λᵀ and the invariants.
* **Searchlight.** D⁴ per unit reception time, D³/γ per unit lab time of emission: ⟨D³⟩ over the sphere = γ, so D³/γ
  averages to 1 (derived by hand; checked to 4e-8 at η = 6 with 4000 Gauss–Legendre nodes).
* **BMT and Thomas–BMT (SI).** From Jackson 3rd ed. eqs. 11.164, 11.170, 11.171 (Gaussian) by e/(mc) → q/m,
  B_G → c B, E_G → E: the code's forms match; S·U = 0 is conserved by the covariant form (shown by hand). I did not have
  the book's text at hand: the equations are compared from memory of their standard forms, and the engine's tests
  check the covariant form against the 3-vector form numerically (independent formulas).
* **Penrose's outline**: right, by brute force (B2-5).
* **Hyperbolic geometry**: hyperbolic L'Huilier, the regular n-gon (cosh ρ = cot(π/n) cot(α/2)), the circle's area
  2π(cosh ρ − 1) and length 2π sinh ρ, geodesic curvature coth ρ of a circle; the isoperimetric bound
  A ≤ √(4π² + L²) − 2π (K = −1); it also holds for the m-fold circle (L² − 4πA − A² = 8π²m(m − 1)(cosh ρ − 1) ≥ 0).
  The framing is honest everywhere I looked: a theorem for planar loops, a comparison line otherwise (engine docstring,
  v09 README, check notes, help text).
* **Exactness of the pieces.** The turn trick: with n(s) = R(s) n₀, N = M R(s) satisfies dN/ds = N (K·n₀ + κ J·ω), so
  M(s) = M₀ exp(s G) R(−κ s) exactly; the position needs only column 0, which R(−κ s) leaves unchanged, so
  ∫exp(σG)dσ from Van Loan's block exponential is exact. A turn's curvature per unit rapidity coth ρ for circular
  motion follows from the FW rate (γ ω per lab time over the rapidity rate γ v ω).
* **Field tolerance.** v09's field θ (matrices) and its reference (L'Huilier) against 40-digit mpmath at η_u = 1 and 3,
  |w| up to 0.999, including nearly antiparallel w: both within 0.13 of the tolerance 64 ε γ_u² γ_w² (`c04`). The field
  check is sound (unlike B2-1, both sides are computed from the same w with no construction step).
* **The Wigner angle at the edges** (`c02` 2): the closed form is accurate to 5e-14 even at rapidities 7 + 7; the
  matrix route loses 4e-8 there (why `ETA_LIMIT` = 7 exists).

Tests (independence): the engine's tests are mostly independent (closed form vs matrices vs SL(2, C) vs Gauss–Bonnet
vs L'Huilier; a direct ODE integration of dM/dτ; Jackson's ω_T integrated in lab time; covariant BMT vs Thomas–BMT).
Weak spots: B2-5; `test_light_time_image`'s observer direction repeats the code's own transformation (`k4 @ boost(u).T`);
the "two representations" of a manoeuvre share the generator trick and the pieces (fine for flying, see B2-1).

v09 causality and computation otherwise: the path, triads and burn events are revealed by the run's time; the result,
its checks and the arrow come at the closure; frames carry only the current state; the field and each slice are
computed by the engine at every point of the plane (160 × 160), not interpolated; checks are shown failed when they
fail (that is how B2-1 shows).

P13 (`out/run_external_suite.txt`: 1126 passed, 12 xfailed in the image `light-funnel-ext`):
* **xfail claims.** tmm: the installed `tmm_core.coh_tmm` resets `delta[i].imag > 35` to 35 ("allowing 1 photon in
  10^30 to pass through"; read in the image); measured t = 6.1e-16 ≈ e^−35 against the exact 2.65e-29. CRunDec: the
  short-range overshoot is asserted against the library itself (`test_crundec_short_range_lands_at_its_first_step`:
  the result equals the exact α_s at μ₀e^±1e-4 to 1e-15); the claim "also in CRunDec 3.1.3" I could not check.
* **Tolerances** are derived (running error bounds checked bit for bit, mpmath references, stated error controls).
  One caveat for the record: the integrator rows rest on the libraries' local error *estimates* (Cash–Karp, DOP853),
  which are not rigorous bounds; the exact references (eng_err, lib_err) make the attribution solid regardless.
* **Licences**: the pinned set matches §10 of `dependencies.md`; the tmm opaque cap and the rundec metadata read in the
  image agree with it. The plan's correction of CRunDec's licence ("GPL-3" → MIT since 2019) is consistent with the
  quoted header (not re-fetched by me).
* **Runtime image unaffected**: none of the five libraries is importable in `light-funnel-viz`; `pytest
  tests/external` there collects nothing; the main suite (490 passed, 5 skipped) does not collect the folder.

Refactor (v08 onto `planes3d.py` / `env3d.js` / `plane_cut`): the server side was compared line by line with the
removed code (`_set_plane`, `_canonical`, `view`, `view_state` / `adopt_view`, auto planes, reset, remove): the same
validation, the same order of messages and the same defaults (the plane centre (0, 0, z_max/2), the default normals,
the auto step and interval; `_update_modelling` after every placement and removal); I found no behavioural
difference. A view state that a new world cannot adopt (v09 velocity → lab) ends in the runner's notice, as designed.
The player side keeps v08's behaviour; the
volume sliders now start where the scene is (before: fixed 50 / 10). v08's tests and the shared visualization tests
pass on GPU 0 (`out/run_v08_and_shared_tests_gpu0.txt`: 35 passed); v09's tests pass (`out/run_v09_tests.txt`: 35
passed); the engine's (`out/run_engine_tests_all.txt`: 490 passed, 5 skipped).

## What I could not check

* Jackson's text (eqs. 11.119, 11.149, 11.164, 11.170, 11.171) was not available to me; the forms are compared from
  their standard statements and by the independent numerical checks above.
* CRunDec 3.1.3's source (the claim that its `AlphasExact` is the same as 3.1's).
* The quotation of Osserman, Bull. AMS 84, 1182 (1978), eq. (4.23) in `spin_transport.isoperimetric_bound`'s
  docstring ("for all surfaces of constant curvature, with equality in each case only for geodesic circles"): the AMS
  server answered with a bot check / HTTP 403. The inequality itself is the standard one for K = −1, and its equality
  for circles is checked numerically by the engine's test.
* B2-4 in the browser: a drag of the gizmo with the readout hovered could not be scripted reliably; the finding rests
  on the code path and the computed peaks.

## Browser check

`c10_browser.mjs` → `out/c10_browser.txt`, screenshots `out/browser/`. My own server instance on port 8501
(`light-funnel-viz`, `engine/` mounted read-only, runs in this folder's `runs/`, which I deleted afterwards: 33 MB of
records, not needed as evidence; the container was stopped by name and checked gone); headless Chromium 1.58.2 with
SwiftShader. The shared server on 8479 was not touched.
* v09 thomas, paused at t = 0 (`c10_v09_thomas_t0.png`): «Сейчас: время t / τ 0 / 0 лет, топливо 0», and in the same
  view «Манёвр и голономия: время манёвра 8,95 лет по часам покоя, 6,956 лет по часам корабля; наибольшая γ 1,337»
  (B2-2, as rendered).
* v09, plane 2 with normal (1, −1, 0)/√2 through the centre (`c10_v09_diagonal_plane.png`): the plane's outline in the
  3-D view is a triangle; the polygon the page received has 6 entries, 3 distinct (B2-7, as rendered). Its slice
  window and its check are right (θ against Gauss–Bonnet in 3 points, ✓).
* v09 presets thomas, triangle, crown, helix, seam, spin_flip, lab played to the end, and v08 gauss with a second
  plane: no page errors, no console errors. v08's planes and outlines as before (4-vertex polygons).

## Other scripts

* `c11_ext_licences.py` → `out/c11_ext_licences.txt`: the installed licence metadata of the 19 packages of
  `light-funnel-ext`, matching `dependencies.md` §10.
* `c12_seam_order.py` → `out/c12_seam_order.txt`: the seam's holonomy converges as 1/N² (ratios 3.96, 3.99, 4.00 for
  N = 48 … 384), as the `seam_convergence` note says; the 96-burn seam is ≈ 1.6e-3 from the smooth one.
