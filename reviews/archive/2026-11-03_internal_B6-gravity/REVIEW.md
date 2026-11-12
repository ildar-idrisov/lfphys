# Review B6 — gravity physics (plan P15.1): `core.gravity.nbody`, `core.gravity.kerr_newman`, the charge in `kerr_geodesics`, the playground `p01_gravity`

**Status: awaiting processing.** Internal review by a subagent that did not write the code (2026-11-03). Rules:
`../README.md`. The reviewer does not process this review, writes no `RESPONSE.md` and does not archive it.

Scope: `lfphys/lfphys/core/gravity/nbody.py`, `kerr_newman.py`, the diff of `kerr_geodesics.py` against HEAD,
`lfphys/tests/test_nbody.py`, `test_kerr_newman.py`, `lfphys/sources/verification_2026-11-03_p15_1.md`, the two new
rows of `lfphys/README.md`, `visualizations/p01_gravity/{viz.py, README.md, tests/test_p01_gravity.py}` (framework
`server/lfviz/playground.py`). The framework itself is reviewed in `../2026-11-03_internal_B6-framework/`; overlaps
are cross-referenced below, not repeated.

Environment: Docker image `light-funnel-viz` (Python 3.11.17, NumPy 2.4.6, SciPy 1.17.1, mpmath), CPU only
(`LFPHYS_NO_GPU=1`), `engine/` mounted read-only; every script runs through `run.sh <name> python3 /out/<name>.py`
and writes `<name>.out` here. The files reviewed and their hashes: `reviewed_files.sha256`. `viz.py` and
`playground.py` were changed by another session during this review (trail handling, framework review F5/F8, 21:00);
every wrapper script was re-run on the changed files with identical output.

Baseline: the engine's new tests pass (`tests_engine.out`: 57 passed, 117 s) and so do p01's (`tests_p01.out`: 13
passed, 1 skipped).

## Summary

| id | severity | where | one line |
|---|---|---|---|
| G1 | error | p01 PN mode (`viz.py:838-847`, `:1009-1034`), README | below r ≈ 9.4 M the default equations (2.5PN + 3.5PN reaction) GAIN energy: the preset binary never reaches `r_stop`, stalls near r ≈ 9 and is ejected to r > 1000 M; the balance check passes through the stall (tolerance 100 x² ≥ 1) |
| G2 | error | `nbody.py:302-324`, p01 duplicate | duplicating a massive body: the refused change leaves an extra body inside the engine; the next frame crashes the world |
| G3 | error | `viz.py:498-499` | Newton energy check divides by E_ref: a star at rest with test bodies (E = 0) raises `ZeroDivisionError` at the first running check after the reference |
| G4 | error | `viz.py:335-385`, `:387-` | a merged body keeps its pre-merger mass and radius in the scene: a scene file loses the merged mass (1.6 → 1.1 M☉), a colour change resets its radius |
| G5 | error | `nbody.py:904` + p01 holes | a Newtonian "black hole" that swallows a star takes the star's radius (235 × its Schwarzschild radius): the declared capture model breaks after the first capture |
| G6 | error | `viz.py:307-323` | "circular orbit" velocity ignores the new body's mass and the others' reflex: e = m/(M + m) (0.5 for equal stars), the scene drifts (12.6 m/s in preset `inner`); off the plane e = 0.41 |
| G7 | should-fix | `viz.py:767-785`, `test_p01_gravity.py:30-31` | Kerr checks fail correct runs: the mass shell for 1–5 M before every capture (up to 59 × the tolerance), Carter's K after ~3e5 steps (linear drift vs a √steps tolerance); the p01 test reads only the last message |
| G8 | should-fix | `nbody.py:33-41, 235`; `test_nbody.py:188-206` | default `dt_rtol = 1e-3` leaves a secular energy drift (e = 0.999: −2.2e-6 per orbit, 4.5e-4 → −8.5e-4 in 600 orbits; none at 1e-8) — "no secular growth" holds only for a tighter rule |
| G9 | should-fix | `nbody.py:722`; `test_nbody.py:188-206` | `max_passes = 1` silently makes the step P(EC)¹ whatever `n_iter` is; the negative control attributes the drift to the missing symmetrization alone |
| G10 | should-fix | `viz.py:480-486, 501` | the companion's note: "half the step, 16 times smaller error" — η/2 shortens the step by √2, the error falls 4 × (measured 4.05–4.11) |
| G11 | should-fix | `viz.py:676-686, 929-, 895`; p01 README | scene files: a captured Kerr body or a stopped binary makes the file unloadable; observers' clocks are not saved (README says they are) |
| G12 | should-fix | `viz.py:648-655` | Kerr: an observer added at t > 0 is drawn at φ + Ω t, as if placed at t = 0 (36.8° off at t = 500 M) |
| G13 | should-fix | `viz.py:664-674` | Kerr: any edit of a body or ray (its colour too) restarts it from its initial set-up and zeroes its proper time |
| G14 | should-fix | `nbody.py:84-110`, `LAYERS.md` §1 | Newtonian gravity in `core` with no conflict, while LAYERS.md names it the example of `theories/approx` and `theories.approx.newton` stays there |
| G15 | nit | `viz.py:227, 229` | `G_AU` "= 4π² to 6e-6" is 3.78e-5; GM_E 3.986004418e14 called "IAU 2015 nominal" (it is 3.986004e14 = `K.GM_EARTH`) |
| G16 | nit | `nbody.py:62-65` | the merger's energy change also contains the pair's potential in the other bodies' field (the code is right, the text is not complete) |
| G17 | nit | `kerr_geodesics.py` ABOUT | title and statement still "Kerr" only; kind "exact solution" for an integrator |
| G18 | nit | `test_kerr_newman.py:201-206, 355, 562-575` | tolerances and texts: a Mino-time rate used as a coordinate-time rate (no effect), an arbitrary 1e3 bound, "divided by D" where the code multiplies |
| G19 | nit | p01 | circular observers accepted inside the ISCO; Newton box grows without bound after an ejection; the plan's "symplectic" Newton integrator not offered; the preset test runs too briefly to reach G1/G7 |

Counts: 6 error, 8 should-fix, 5 nit.

Checked and found in order: see the last section (the Kerr–Newman geometry to 1e-14 against a 40-digit route, the
Hamiltonian, the Hermite and Forest–Ruth formulas, the momentum floor, the quotations).

---

## Errors

### G1 — error — the PN binary gains energy below r ≈ 9.4 M; the default preset never reaches its stop and flies apart; the balance check cannot see it

Location: `visualizations/p01_gravity/viz.py:838` (`r0` min 8), `:847` (`r_stop` default 6, min 2.5), `:1019-1026`
(balance check, tolerance `100 x²`), the preset `pn_inspiral` (r0 = 20, all orders, r_stop 6); p01 README ("the PN
expansion fails near r ≈ 6–10 G m/c² (the run stops at the chosen distance)"); the root is in
`core.gravity.pn_binary` (B5), whose validity says only that the series "converges poorly" at r ≲ 10.

Evidence:
* `r06d_pn_instant_balance.out` — on circular states, without any time integration, −dE₂PN/dt along the full
  acceleration (1PN, 2PN, 2.5PN, 3.5PN) divided by the 1PN flux of Blanchet 2014 Eq. (314) [verified in
  `sources/1310.1528v4.txt`: "F = 32c⁵/5G ν² x⁵ {1 + (−1247/336 − 35/12 ν) x + 4πx^{3/2} …}"]: 0.99999604 at r = 3000,
  0.870 at r = 20, 0.534 at r = 12, 0.236 at r = 10, **−0.480 at r = 8** (ν = 1/4; ν = 0.16 and 0.045 the same within
  3 %). (ratio − 1)/x² → −35.5 as x → 0 for every ν, while the physical 2PN flux coefficient is −0.10 (ν = 1/4) …
  −4.09 (ν = 0.045): the residual is the 2PN-relative mismatch of the truncated equations (no radiation reaction
  beyond 3.5PN), and it flips the sign of the energy loss near r ≈ 9.3.
* `r06c_pn_onset.out` — integrated, quasi-circular starts, mean dr/dt over 1000 m: r0 = 8: +5.8e-4 (q = 1), +6.6e-4
  (q = 0.25), +3.8e-4 (q = 0.05) — outward, the 2PN energy rising (+2.1e-3) — while the engine's own adiabatic rate
  is −1.8e-3; r0 = 9: still outward; r0 ≥ 10 inward.
* `r06e_pn_stall.out` — from r0 = 11 the binary stalls at r ≈ 9.1, then becomes eccentric and is ejected (r up to 685 by
  t = 4e4, E/μ → −5e-4). **The preset `pn_inspiral` itself**, through the wrapper: r = 10.78 at t = 2e4 m, 11.13 at
  4e4, **305 at 6e4, 1250 at 8e4**, no `merger` event; the balance check reads `0.0886 ok True tol 1.24` at 4e4 (the
  binary already gaining energy) and fails only at r = 305. At the default speed (200 m per second of wall time) this
  is 2–5 minutes of watching the owner's own preset.
* `r06_pn_balance.out` — a binary started at r0 = 8.5 (q = 0.05) shows ratio −0.24 … −0.16 for 3000 m (orbital energy
  rising) with every check `ok`: the tolerance 100 x² is 1.38 there. The tolerance exceeds 1 for every x > 0.1
  (r < 10), so in that range a check of a balance can pass a sign error.
* The README's "measured −40 x² at x = 0.01 … −70 x² at 0.065" agrees with r06d (−39.1 at x = 0.0099, ≈ −61 at 0.065)
  [neutral]; the margin of the tolerance is 1.3 × at r = 10 and negative at r = 8.

Fix: (a) in p01, keep the full-order binary where its own equations dissipate: refuse r0 and r_stop below the radius
where −dE/dt along the equations falls to, say, half of F₁PN (≈ 12 M for every ν, r06d), or stop the run there with
an event that names the reason; (b) make the balance check one-sided first (the orbital energy must decrease while
waves are emitted; fail at once if it rises) and keep the relative tolerance below 1 (e.g. the measured −35.5 x²
residual's curve plus a margin, not a free 100 x²); (c) record in `../../STATUS.md` (V34) that the harmonic 2.5 + 3.5PN
equations without the 4.5PN reaction gain energy below r ≈ 9.3 M for all mass ratios, and say so in `pn_binary`'s
validity instead of "converges poorly"; (d) a p01 test that runs `pn_inspiral` to its end.

### G2 — error — a refused "duplicate" leaves an extra body in the engine; the next frame crashes the world

Location: `lfphys/lfphys/core/gravity/nbody.py:302-324` (`add` appends the body to `_keys`, `_x`, `_v`, `_m`, `_R`
before `_edited()` computes the forces, which raise for two bodies at one point); `viz.py:335-354` (`on_add` with
the duplicate's `state` = the source's current x, v: the copy is placed exactly on the source); the framework's
contract "raise ValueError to refuse: the scene is then left as it was" (`playground.py:14-16`).

Evidence: `r10_duplicate_and_refusals.out` (1): preset `sun_earth`, duplicate the Earth: the player gets
"two bodies at the same point (exact collision of point masses)"; afterwards the scene has o1, o2, o3, but the engine
has keys `['o1', 'o2', 'o4']` with 3 position rows and 2 acceleration rows; the next frame raises
`ValueError: operands could not be broadcast together with shapes (3,3) (2,3)` — the world stops in error, and the
engine's arrays stay inconsistent, so a resume cannot recover it (not tested here: how often the framework then
repeats the error, cf. its review's F6).

Fix: make `NBody.add` / `set` transactional (build the new arrays, compute forces on them, commit only on success;
or roll back in a `try`); raise `ValueError` (the framework's refusal type) for coincident points; in p01, a duplicate
of a body is not a physical event at the same point — offset it (the inspector's `x, y, z` of the copy) or refuse
it with a clear message before touching the engine.

### G3 — error — the Newtonian energy check divides by the reference energy; E = 0 scenes crash

Location: `viz.py:498-499` (`(E - self.ref["E"]) / abs(self.ref["E"])` and `tol=tolE / abs(self.ref["E"])`).

Evidence: `r02_scene_file_after_events.out`, first block: a star at rest (1 M☉) and a test body at 2 au — total
energy exactly 0 (test bodies carry none) — `the frame raised: ZeroDivisionError float division by zero` at the
second check. Any scene of one massive body at rest plus test bodies does this (also a lone body at rest after
mergers). The momentum check already guards its scale (`or 1.0`); the energy check does not.

Fix: normalise by a scale that cannot vanish, e.g. Σ ½ m v² + Σ G mᵢ mⱼ / rᵢⱼ at the reference, falling back to an
absolute display when it is 0; never divide in a running check without a guard (a running check must not stop a
world).

### G4 — error — a merged body keeps its pre-merger mass and radius in the scene: files and edits undo the merger

Location: `viz.py:373-385` (`object_state` returns only x, v), `:335-354` (`on_add` takes m, R from the object's
parameters), `:356-371` (`on_set` always passes `radius=R` from the parameters), `:387-` (`_events` deletes the
absorbed object but does not update the kept one's parameters).

Evidence: `r02_scene_file_after_events.out`, second block: stars A (1 M☉) and B (0.5 M☉) merge (engine mass 1.6
with a third star C 0.1 M☉, radius of the merged body 0.00586 au); the exported file lists A with `mass 1.0`;
reloaded, **the engine mass is 1.1 M☉** and the radius 0.00465 au. In the running world, changing only A's colour
resets its radius 0.00586 → 0.00465 au; a duplicate of A gets mass 1.0, not 1.5.

Fix: on a merge, write the merged mass (in the object's units) and radius into the kept object's `values` and emit the
scene; or keep `m` and `radius` in `object_state` and prefer the state on load; in `on_set` change only what changed.

### G5 — error — a Newtonian "black hole" grows to the radius of the star it swallows

Location: `nbody.py:904` (equal-density radius `(R_i³ + R_j³)^(1/3)`, the kept key the heavier body's), p01's
holes (`viz.py:325-333`: radius = Schwarzschild radius, "a Newtonian mass with its Schwarzschild radius as a capture
radius"), `_events`.

Evidence: `r12_hole_radius_after_merger.out`, preset `hole_stars`: before, the hole's radius 1.974e-5 au (its
Schwarzschild radius); after it captures the falling star, mass 1001 M☉, **radius 4.65e-3 au = 235 × its
Schwarzschild radius** — from then on it captures every star whose surface comes within one solar radius of it, and
the player draws a "black hole" the size of the Sun.

Fix: in p01, after any merge that keeps a hole, set its radius to 2 G M/c² of the new mass (`nb.set(key, radius=…)`)
and keep the object's type; or give `NBody` a per-body radius rule (equal density / fixed / Schwarzschild).

### G6 — error — the "circular orbit" start is circular only for a test body

Location: `viz.py:307-323` (`_velocity`): the new body gets `cv + sqrt(G M / r)` about the centre of mass of the
others (M their mass, r the distance in the xy-plane), the others keep their velocities. The option is labelled
«круговая орбита вокруг центра масс остальных (в плоскости xy)»; planets use it by default; stars may choose it.

Evidence: `r01_circular_velocity.out`: a second star of mass m at 1 au from a 1 M☉ star: relative orbit e = 0.5000
(m = 1), 0.0909 (m = 0.1), 0.000999 (m = 1e-3), exactly m/(M + m), a = 2/3 au instead of 1 au for equal stars, and the
pair's centre of mass moves at 14.9 km/s (m = 1). Preset `inner`: Jupiter e = 9.2e-4, the whole scene drifts at
12.6 m/s (2.7 au per 1000 yr; the box keeps growing). A planet placed at z = 1 au: e = 0.414 (the cylindrical
radius is used in the speed). `test_p01_gravity.py:66-77` encodes the eccentric start ("within m_earth/m_sun of
1 au").

Fix: the two-body circular start — relative speed sqrt(G (M + m)/d) with d the 3-D distance, the new body
`cv + M/(M+m) v_rel ê` and the others shifted by `−m/(M+m) v_rel ê` (total momentum unchanged), ê ⊥ d in the plane
through the centre of mass; or relabel the option honestly ("speed of a circular orbit of a test body") and say what
it does to massive bodies. Test with equal masses.

## Should-fix

### G7 — should-fix — the Kerr running checks fail correct runs (shell near the horizon, K on long runs); the p01 test cannot see it

Location: `viz.py:767-785` (`dmu2` absolute, `dK` relative to max(|K₀|, 1), both against `10 · rtol · √steps`),
`test_p01_gravity.py:30-31` (`failed()` reads `h.checks()`, the last message of each check only).

Evidence:
* `r05_kerr_check_tolerances.out` (2), `r05c_shell_window.out`: the mass-shell error of a falling body grows like
  1/Δ (its terms P²/Δ do): a = 0.9, q = 0.3, radial fall from r = 12: |δμ²| = 7.96e-7 against the tolerance 1.36e-8
  (**58.7 ×**) at r − r₊ = 1.1e-4; the preset's own body "Падает" (a = 0.9): above the tolerance for the last 1.1 M
  before capture; q = 0.4: 5.3 M; a = 0: 1.9 M. At the default speed (10 M per second) and a check every 20 frames, a
  red check appears or not depending on timing.
* `r05b_kerr_checks_in_playground.out` (b): one inclined orbit at r ≈ 20 (a = 0.9, q = 0.3): K drifts linearly,
  1.96e-12 per step, while the tolerance grows as √steps: they cross at 2.7e5 steps (t = 4e6 M), and the check fails
  from then on (1.07e-6 against 7.4e-7 at 5.5e5 steps). `r05` (1): the other orbits stay well inside up to 1e6 M.
* `r05b` (a): in a 200 M run of `kerr_orbits` with 2000 frames no message failed — the window is short; the p01 test
  would not see a failed message anyway.
* The engine's own budget is linear and scaled by the gradient (`test_kerr_newman.py:272-300`: steps · √6 · rtol ·
  |∇K| · scale), and `Geodesics._shell` already returns the shell's term scale.

Fix: report δμ² relative to the shell's term scale (`_shell(...)[2]`) and use a budget linear in steps (the engine
test's form, per body); in the p01 tests, assert on every `check` message, not on the last.

### G8 — should-fix — the default symmetrization tolerance leaves a secular energy drift

Location: `nbody.py:235` (`dt_rtol=1e-3`), docstring `:33-41` ("NOT symplectic: with time-symmetric steps and enough
iterations the energy error of periodic orbits oscillates without secular growth"), README row ("time-symmetric");
`test_nbody.py:188-206` (e = 0.9, 100 orbits, factor 2).

Evidence: `r08b_secular_drift_default_rtol.out`, e = 0.999, η = 0.02 (the regime of HMM95 / KYM98): signed dE/E at
apoapsis with the defaults +4.463e-4 (1 orbit), +2.502e-4 (100), +4.50e-5 (200), −3.946e-4 (400), **−8.531e-4
(600)** — linear, −2.2e-6 per orbit; with `dt_rtol = 1e-8` +4.488e-4 … +4.477e-4 (no drift). `r08`: e = 0.9 drifts
−1e-8 per orbit (2.75e-6 → 2.30e-6 in 50 orbits), e = 0.99 −2e-7; no step was left unconverged in any run (the
symmetric rule always met 1e-3, it is the 1e-3 itself). The strict rule costs 4.0 passes per step instead of 2.1
(×3 wall time here).

Fix: a default that makes the claim true (measure 1e-5 … 1e-8 for cost), or state the residual drift ∝ dt_rtol per
orbit in the docstring and the README; a test at e = 0.999 over a few hundred orbits with the default.

### G9 — should-fix — `max_passes = 1` silently means P(EC)¹; the negative control mixes two causes

Location: `nbody.py:722` (`n = 1 if (p == 0 and self.n_iter > 1) else self.n_iter`), `test_nbody.py:188-192`
("Negative control: without step symmetrization (max_passes = 1) the same orbit drifts linearly").

Evidence: `r03_hermite_controls.out` (a): `n_iter=3, max_passes=1` and `n_iter=1, max_passes=1` give bit-identical
positions after 5 orbits (853 force evaluations each). (b), e = 0.9, |dE| after 1 → 100 orbits: A default 1.37e-9 →
9.45e-10; B PEC with symmetric steps 1.79e-8 → 4.37e-7 (×18.7); C P(EC)³ with the usual
non-symmetric step 2.37e-9 → 6.93e-8 (×8.2; P(EC)¹⁰ identical); D the test's control 3.0e-9 → 1.53e-6. Both
ingredients are needed (as KYM98 says: `sources/1998MNRAS_297_1067K.txt`, "the time-symmetry of the scheme achieved
by the iteration of EC steps", and the abstract's "with time-symmetric time-steps"); the control as written removes
both.

Fix: take the cheap first pass only when `max_passes > 1` (or document that `max_passes = 1` means PEC); in the test,
two controls — symmetric steps without iteration, iteration without symmetric steps.

### G10 — should-fix — the companion's text: η/2 is not "half the step", and the error falls 4 ×, not 16 ×

Location: `viz.py:480` (label «против расчёта с вдвое меньшим шагом»), `:482-485` («пересчитан с шагом вдвое мельче … с
шагом вдвое мельче ошибка в 16 раз меньше»), `:501`; README "half the accuracy parameter" is right.

Evidence: `r03_hermite_controls.out` (c): Kepler e = 0.5, 10 orbits: err(η)/err(η/2) = 4.11 (η = 0.02), 4.05
(η = 0.005); err(η)/err(η/16) = 262, 273 — Aarseth's step ∝ √η, as `test_nbody.py`'s docstring itself says. The
energy tolerance (3 × the companion difference) remains safe for a ratio of 4 (|E − E_true| ≤ 4/3 |E − E_c|).

Fix: say "η/2 (step ≈ 1/√2, error ≈ ¼)" or use η/4 if a halved step is meant.

### G11 — should-fix — scene files after terminal events cannot be loaded; observers' clocks are not saved

Location: `viz.py:676-686` (Kerr `object_state`: no status), `:594-626` (`add_state` refuses r ≤ r₊ + capture_eps),
`:929-` and `:895` (PN: no status; a start at r ≤ r_stop is refused), observers (`object_state` None, `on_add` sets
τ = 0); p01 README "A scene file keeps … dynamic state (positions, velocities, momenta, clocks)".

Evidence: `r02_scene_file_after_events.out`: after "Падает" is captured its saved r is 1.4359898943540668 <
r₊ + 1e-4 = 1.4359898943540672 → `reloading the scene FAILED: ValueError start outside the capture radius`;
observers: before export τ = 0.010449 s at t = 0.014776 s, after reload τ = 7.1e-10 s at t = 0.014776 s.
`r14_pn_file_after_stop.out`: a binary stopped at r_stop = 12 → `reloading the scene FAILED: ValueError начальное
расстояние не больше «остановить при»`. An escaped body would come back active.

Fix: save each object's status and clock (Kerr bodies: captured/escaped; PN: stopped; observers: (t₀, τ₀)) and
recreate them as they were (inactive, or omitted with a note in the file); README.

### G12 — should-fix — an observer added later is drawn where it would be had it been placed at t = 0

Location: `viz.py:648-655` (`ph += ω · t_m` and `Ω · t_m` with the world time, not the time since placement; its
clock in `obs_tau` does use the placement time).

Evidence: `r02_scene_file_after_events.out`, last block: a circular observer added at t = 500 M with φ = 0° is drawn
at φ = 36.76° (= Ω t mod 360°, Ω = 0.064115).

Fix: keep the placement time (or φ at placement) per observer and use t − t₀.

### G13 — should-fix — a colour change restarts a Kerr body or ray from its initial set-up

Location: `viz.py:664-674` (`on_set`: remove and `on_add(obj, None)` for any change).

Evidence: `r10_duplicate_and_refusals.out` (3): body o2 at (r, θ, φ) = (11.687, 1.832, 1.860), τ = 40.71 → after
changing only its colour (8.0, 1.222, 0.0), τ = 0. The same class as the framework review's F16 (p02).

Fix: restart only when a parameter that defines the start changed (position, velocity mode, velocities, direction);
say in the inspector which changes restart the body.

### G14 — should-fix — layer: Newtonian N-body gravity is in `core` with no conflict

Location: `nbody.py:84-110` (`"layer": "core"`, `"conflicts": []`, validity "для N ≥ 3 это самая полная форма в
движке"), `lfphys/LAYERS.md` §1 ("theories/approx: a simplified form of a law the engine also has in fuller form …:
**Newtonian gravity of slow bodies** against the exact Schwarzschild orbits"), `theories/approx/newton.py:29-36`
(the same law for two bodies, layer theories, conflict "ОТО даёт прецессию перицентра …").

The same law now sits in two layers. The engine does have the fuller law for every situation p01 shows with it:
two bodies (`pn_binary`, Schwarzschild/Kerr test bodies), and a planet about a star (preset `inner` has Mercury, whose
43″ per century the module omits). In the player, "Физика этого мира" lists `core.gravity.nbody` as core with no
conflict; only p01's approximation message flags it.

Fix: either move `nbody` to `theories/approx` with its conflict (perihelion advance, no radiation, the 1PN EIH terms
for N ≥ 3) — p01 already flags the approximation — or amend LAYERS.md (core = the most complete form for that N) and
then move or justify `theories.approx.newton`; in either case name the conflict.

## Nits

### G15 — nit — two unit comments

`viz.py:227`: `G_AU` "= 4 pi^2 to 6e-6" — it is −3.777e-5 off (the square of the Julian/Gaussian year ratio,
`r11_units.out`). `viz.py:229`: GM_E = 3.986004418e14 "IAU 2015 nominal" — the nominal value is 3.986 004 × 10¹⁴
(`sources/1510.07674.txt:103`), which the engine already has as `core.constants.GM_EARTH`; use it (1.05e-7).

### G16 — nit — the merger's energy change, as described

`nbody.py:62-65`: "the energy change of the merger (kinetic energy of the relative motion and the pair's potential
energy …)". `_pair_energy` (`:919-934`) also counts the change of the pair's potential energy in the other bodies'
field when the two are replaced by one body at their centre of mass — correctly (the test with a third body checks
E_after = E_before + ΔE to 64 u). Say so.

### G17 — nit — `kerr_geodesics` passport

The diff adds `q` to every function and to the docstring, but `ABOUT["title"]` («Геодезические Керра») and
`statement` («Метрика Керра …») still name Kerr only, and `kind` is "exact solution" for a DOP853 integrator
(pre-existing). The "q = 0 unchanged bit for bit" claim holds by inspection: (2a)·r = a·(2r) exactly, + 0.0 exact.

### G18 — nit — test texts and tolerances in `test_kerr_newman.py`

* `:201-206`: `drdt` is |dr/dλ| (Mino time) used as |dr/dt|, a factor dt/dλ ≈ 30–110 too large, and also for θ and
  φ. No effect: the x2 term carries every assertion (`r09_kerr_generic_test_terms.out`: the loose term ≤ 4.5e-12
  against x2 terms 1e-12 … 2.7e-9) — but the bound is not what it says.
* `:355`: `(1e-6) ** 2 * 1e3` bounds |d²τ/dr²| by 1e3; at the horizon of the r0 = 10 fall it is ≈ 0.35. Derive it or
  say it is a generous constant.
* `:562-565`: "E (= ν∞/ν_obs) is divided by the Doppler factor D"; the code asserts E_obs = E_ZAMO · D, D = ν_ZAMO/ν_obs
  (`lorentz.aberrate`'s convention) — the code is right, the sentence is not.

### G19 — nit — p01 odds and ends

* `viz.py:627-646`: a "circular orbit (free fall)" observer is accepted inside the ISCO (a = 0.9, r = 2: rate 0.2802;
  ISCO 2.32, `r13_observer_inside_isco.out`): it is not integrated, so it stays on an unstable orbit forever; refuse
  or label it.
* Newton's box (`frame`) grows with every body without a cap; after an ejection (the Pythagorean preset) the scene
  shrinks to a point — the Kerr mode caps at 4096 and ignores light for the same reason (also framework F6's overflow).
* PLAN P15.1 says "Newtonian N-body (symplectic, with close encounters)"; p01 always uses Hermite — Yoshida-4 is not
  offered for long quiet systems.
* `test_p01_gravity.py:34-42` runs each preset for 4 × its default speed (800 m of the binary, 40 M of the hole): none
  of G1, G5, G7 is reached; a longer, coarser run of each preset would have found them.

---

## Checked and found in order

* [useful] Kerr–Newman geometry against an independent 40-digit route (`r07_kn_circular_independent.out`): the metric
  written from Adamo & Newman, Ω solved from the geodesic condition, E, L from u_t, u_φ, the photon orbit as the zero
  of the normalisation, the ISCO as the minimum of E(r), for 8 (a, q) incl. a = 0.998 and q = 0.99, both directions:
  Ω, E, L to 7e-16, photon orbits to 1.6e-15, ISCO to 1.1e-14; a third route, the closed equatorial photon-orbit
  equation r² − 3r + 2q² ± 2a√(r − q²) = 0 (prograde +), agrees to 1e-45 with the 40-digit root.
* [useful] The separated Hamiltonian (`kerr_newman.py:311-331`): dp_r/dλ and dp_θ/dλ re-derived by hand from
  K_sep (the θ-part: −∂/∂θ ½(W²/sin²θ + μ²a²cos²θ) = c s (L²/s⁴ − a²E² + μ²a²) = the code's
  `c s (W/s² (2aE + W/s²) + μ² a²)`); Θ in the K form equals Carter's Q form; ZAMO α, ω, ϖ, the tetrad and
  `momentum_from_zamo` (E − ωL = αγ); the ergosurface and horizons; the camera's aberration direction and
  E_obs = E_ZAMO · D with `aberrate`'s D = ν_ZAMO/ν_obs (an observer moving towards what it looks at sees it
  blueshifted).
* [useful] DOP853's combined error norm equals SciPy's `_estimate_error_norm` (|h| e5 / sqrt(n (e5 + 0.01 e3))), the
  13th weights zero, exponent −1/8.
* [useful] Hermite: predictor, the implicit corrector KYM98 (7)-(8), a⁽²⁾, a⁽³⁾ (KYM98 (5)-(6)), the continuous output
  ending on the committed state (the algebra of `verification_…_p15_1.md` §1 redone: both give
  x0 + v0 h + (7a0 + 3a1) h²/20 + (j0/20 − j1/30) h³), Aarseth's criterion (NM08 (15)), the symmetric rule's
  reversal symmetry; the quintic Hermite basis and its derivatives; the velocity Forest–Ruth coefficients (Omelyan
  et al. Eq. 8, "velocity FR counterpart"); the tidal tensor's sign; the merger's ΔE bookkeeping with a third body.
* [useful] Momentum floor (`r04_momentum_floor.out`): |ΔP|/Σ|m v| grows like √steps, 8.6e-15 after 1e5 steps
  (`inner`), 1.3e-14 (`hole_stars`): the playground's fixed 1e-12 is safe for ~1e9 steps. [neutral]
* [useful] The symmetric step rule converged in every step of every run here (0 unconverged, ~2.1 passes per step;
  `r08`); P(EC)³ is converged to round-off with Aarseth steps (P(EC)¹⁰ bit-identical, `r03`).
* [useful] Units: KMS, Earth's 29.785 km/s, R_S of the Sun 2953 m, G M/c³ and G M/c² of the modes, 1 Mpc
  (`r11_units.out`); the 1PN flux in p01 (`viz.py` PN `advance`) equals Blanchet 2014 Eq. (314) without the tail; the
  GW frequency 2Ω/2π; the strain scale G m/(c² R).
* [neutral] p01's Kerr clocks (static √(−g_tt), ZAMO α, circular dτ/dt) and circular-orbit ZAMO velocity
  ϖ(Ω − ω)/α are correct; the Newtonian tidal probe converts 1/yr² → 1/s² correctly.

## Quotations checked against the sources (`sources/`, fetched 2026-11-03, no contact parameter sent)

Verified by grep in the downloaded text: NM08 (`0708.0738.txt`: Eqs. (1), (2), (5), (15), "Usually, a value around
0.02 is used for η", "time-symmetric, when used with the correct-to-convergence mode"); KYM98 (ADS scan with a text
layer, `1998MNRAS_297_1067K.txt`: the abstract sentence, "results for n = 3 and 4 are still indistinguishable", "the
necessary times of the EC iteration to achieve the time-symmetry increase", "with a sufficiently small value of ηs";
note that its Fig. 3 discussion says P(EC)³ "shows no secular error for e ≲ 0.1" at constant steps — the engine's
adaptive steps make n = 3 sufficient, r03); Omelyan et al. (`cond-mat_0110585.txt`: θ = 1/(2 − ∛2) ≈ 1.3512, the
"velocity FR counterpart (VFR)"); Chenciner & Montgomery (`math_0011268.txt`: x1 = −x2 = 0.97000436 − 0.24308753i,
V = ẋ3 = −2ẋ1 = −0.93240737 − 0.86473146i, T = 6.32591398); Szebehely & Peters (ADS scan OCR, `1967AJ_…876S.txt`:
"t10=15.8299236", "769/60", "permanent binary", "approximately 0.9", "hyperbolic velocities"); Boekholt et al.
(`2109.07013.txt`: "small perturbations grow by about 9 orders of magnitude"); Adamo & Newman (`1410.6626.txt`: Δ ≡
r² + a² − 2Mr + Q², (3.18), (3.23)); Hackmann & Xu (`1304.2142.txt`: (11)-(16), C̄ = K̄ − (āE − L̄)²); Pugliese et al.
(`1103.1807.txt`: (36)); Morales-Herrera et al. (`2401.07112.txt`: (20)); Keeton & Petters (`gr-qc_0511019.txt`:
(51), (53)); Blanchet LRR 17, 2 (2014) Eq. (314) (`1310.1528v4.txt`; the current arXiv version renumbers it, so
"Eq. 314" must be read in v4); IAU 2015 B3 (`1510.07674.txt`: (GM)ᴺ_E = 3.986 004 × 10¹⁴).
Not obtained as text: Hut, Makino & McMillan 1995 (the ADS scan has no text layer; the quoted drift numbers
"Δa/a ≃ 10⁻⁶ … 2 × 10⁻¹⁰" were not checked by this reviewer).

## Files

| file | what it shows |
|---|---|
| `run.sh` | the Docker wrapper (read-only engine, CPU, container `lf-b6rg-<name>`) |
| `tests_engine.out`, `tests_p01.out` | the new tests pass (baseline) |
| `r01_circular_velocity.{py,out}` | G6 |
| `r02_scene_file_after_events.{py,out}` | G3, G4, G11, G12 |
| `r03_hermite_controls.{py,out}` | G9, G10, P(EC)ⁿ convergence |
| `r04_momentum_floor.{py,out}` | the momentum check's floor (no finding) |
| `r05_kerr_check_tolerances.{py,out}`, `r05b_kerr_checks_in_playground.{py,out}`, `r05c_shell_window.{py,out}` | G7 |
| `r06_pn_balance.{py,out}`, `r06b_pn_outspiral.{py,out}`, `r06c_pn_onset.{py,out}`, `r06d_pn_instant_balance.{py,out}`, `r06e_pn_stall.{py,out}` | G1 |
| `r07_kn_circular_independent.{py,out}` | the 40-digit Kerr–Newman route (no finding) |
| `r08_symmetrization_convergence.{py,out}`, `r08b_secular_drift_default_rtol.{py,out}` | G8 |
| `r09_kerr_generic_test_terms.{py,out}` | G18 |
| `r10_duplicate_and_refusals.{py,out}` | G2, G13 |
| `r11_units.{py,out}` | G15 |
| `r12_hole_radius_after_merger.{py,out}` | G5 |
| `r13_observer_inside_isco.{py,out}` | G19 |
| `r14_pn_file_after_stop.{py,out}` | G11 |
| `sources/` | downloaded texts (arXiv PDFs and ADS scans with `pdftotext -layout`), untrusted data, not executed |
| `reviewed_files.sha256` | the versions reviewed |
