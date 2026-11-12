# Internal physics review: visualizations/v04_orbits and lfphys.core.gravity.orbit_stream

**Status: awaiting processing** (by a participant other than the reviewer; `reviews/README.md`).

Reviewer: Claude (Opus subagent, independent of the session that built v04), 2026-10-23.

## Scope

* `visualizations/v04_orbits/` — `viz.py`, `engine/body.py`, `web/view.js`, `README.md`, `tests/test_v04_orbits.py`.
* `lfphys/lfphys/core/gravity/orbit_stream.py` and `lfphys/tests/test_orbit_stream.py` (engine module added for v04),
  with the references it relies on (`lfphys.core.gravity.orbits`, `kerr`, `theories.approx.newton.integrate_body`,
  `theories.approx.ppn`).
* Not in scope: the server/player (except where v04 depends on them), other visualizations. The view was reviewed by
  reading `web/view.js` (no screenshots were taken).

## Environment

Docker image `light-funnel-viz` (numpy, scipy, mpmath, python-flint 0.9.0), CPU only, run as

    docker run --rm --user "$(id -u):$(id -g)" -v /home/ildar/hdd/projects/i/light-funnel:/lf \
      -w /lf/reviews/2026-10-23_internal_viz-v04_physics \
      -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests \
      light-funnel-viz python3 NN_<name>.py

Each check is one numbered script `NN_*.py`; its output is `out/NN_*.txt`. `out/00_baseline_tests.txt`: the
existing tests pass (23 engine tests, 27 v04 tests). Reference values are computed in the scripts with mpmath at
40–50 digits from the same float launch data the run uses, without the project's orbit code.

Sources fetched for this review (no identifiers sent): NASA NSSDCA Mercury Fact Sheet
(https://nssdc.gsfc.nasa.gov/planetary/factsheet/mercuryfact.html, "Last Updated: 11 January 2024, DRW", sha256
170d9f2d…3f) — "Semimajor axis (AU) 0.38709893", "Orbital eccentricity 0.20563069"; C. M. Will, Living Rev.
Relativ. 17, 4 (2014), arXiv:1403.7377v1 (sha256 87b6db17…cf), Sec. 4.2, Eq. (65): "ω̃̇ = 42.″98 [⅓(2 + 2γ − β) +
3 × 10⁻⁴ (J₂/10⁻⁷)]". Both as cited in `viz.py`.

## Summary

| ID | severity | one line |
|---|---|---|
| V4-1 | error | `_classify` brackets the start by comparing re-found roots with 1 ± 1e-12: tangential launches near circular speed (20/64) and boosts of circular orbits — the ±5 % buttons — (32/48) get the wrong kind (plunge → «escape», eccentric → «circular») or wrong turning points |
| V4-2 | error | an outward unbound launch with no inner turning point is classified «падение на центр» (GR and Newton) and then escapes |
| V4-3 | error | radial fall from r₀ ≳ 10⁶ M: the horizon stop is not resolved in s = τ/r₀^{3/2}; at 10⁸ M the run shows r = 1.99974 M, v = 1.0000655 c, dτ/dt < 0, and the cycloid check passes |
| V4-4 | error | Newton track: on eccentric orbits (from −85°) `unwrap` loses 2π per periapsis → «advance» −360°/orbit, the closed-ellipse check fails; apsides missed at −89.99°; energy drift up to 9.8e-7 (abs. tolerance 1e-12 r₀) |
| V4-5 | should-fix | «circular» is granted at 1e-6 but the circle rows use 1e-10/1e-8: nearly circular inputs and unstable circles fail; `fall_tau` from an unstable circle uses a divergent quadrature (rel 1.07–1.11) |
| V4-6 | should-fix | a bound orbit with r_apo > 1000 r₀ ends as «уход на бесконечность» |
| V4-7 | should-fix | `orbits.elements/turning_points` take e and form e·e − 1: Mercury reference 1e-8…6e-8 off, tolerance 1.7e-7 self-inflicted (em1 gives 3e-14); near the ISCO the reference is off by 5.3e-9 > tol 1.9e-9 → a correct run fails |
| V4-8 | should-fix | weak field: second-scheme drift rows (e, norm < 1e-9) admit 4–8 % of the binding energy |
| V4-9 … V4-15 | nit | closed form shown as Mercury «measurement»; 6πM/p row could be second order; radial period lacks its quadrature reference; ISCO row cannot fail; Newton tol shown ≠ verdict; ghost end events duplicated; «за горизонтом» label |
| V4-16 | should-fix | switching the ghost on late blocks the worker 10–60 s (catch-up from the segment start in one command) |

## Findings

Status tags (AGENTS.md §7): V4-1 … V4-7 and V4-16 **[error in earlier]** (the run shows or checks something wrong);
V4-8 **[weakens]** (a verification row is weaker than it reads); V4-9 … V4-15 **[neutral]** (presentation).

### V4-1 (error) — the orbit kind and the turning points are wrong when a segment starts at a turning point

Location: `lfphys/lfphys/core/gravity/orbit_stream.py:116–172` (`_roots`, `_classify`; lines 148–160).

What is wrong. `_classify` re-finds the turning points as roots of F(y) = 2u_s y³ − y² + 2Ay + B and brackets the
start y = 1 by comparing roots with 1:
* start with v_r = 0 exactly (a tangential launch): the root that *is* the start is recovered by `np.roots` + Newton
  only to ~eps/|F′(1)|; near the circular speed F′(1) is small and the recovered root is off by 1e-12…3e-10
  (`out/13_root_at_start.txt`), i.e. outside the `tol = 1e-12` window, so it is taken as the *other* turning
  point (r_apo = r₀(1 + 1e-11)) and the orbit is declared **circular**;
* start with v_r ≈ 1e-17 (any boost of a circular orbit — the «толчок ±5 %» buttons — since the dense-output state
  never has v_r exactly 0): the general branch `lo = max(y ≤ 1)`, `hi = min(y ≥ 1)` lets the rounding of the root at
  y = 1 ± 1e-15 decide the bracket: a plunge becomes **escape**, an eccentric orbit becomes **circular**, or a bound
  orbit gets the inner barrier root as its periapsis (r_peri = 2.43 M instead of the true 20 M) — and once an unbound
  orbit **bound** (r₀ = 8, dv = +0.3).

The integrator itself is unaffected, but the kind decides what the run does and shows: «circular» switches off the
periapsis/apoapsis events (no advance is measured on an eccentric orbit), fires the circle checks (which then fail,
V4-5) and the notice «Тело ушло с круговой орбиты … неустойчивость» on a stable orbit; «escape» suppresses all
advance checks and labels a falling body «уход на бесконечность»; wrong r_peri/r_apo appear in the panel «Орбита», the
segment text and the plot window.

Evidence.
* `11_classify_scan.py` → `out/11_classify_scan.txt`: tangential launches at r₀ ∈ {6.01 … 10⁴} M, k = 1 ± {1e-6 …
  1e-3}: **20 of 64 kinds wrong** (e.g. r₀ = 6.01, k = 1 + 1e-5: run «circular», r_apo = 6.0100000000325; truth
  bound, r_apo = 6.05113430713; r₀ = 10, k = 1 − 1e-5: run «circular», truth bound with r_peri = 9.99920002).
  Boosts of circular orbits (v_r = ±3e-17), dv ∈ {±1e-3, ±0.05, ±0.3} at r₀ ∈ {6.2, 8, 20, 10³}: **32 of 48 wrong**
  (kind or turning points).
* `06_turning_point_start.py` → `out/06_turning_point_start.txt`: through the run (Harness), presets `bh_isco` and
  `default` (r₀ = 20, speed 1): «−5 %» at 6.2 M → run «escape», truth: one real turning point (the start), the body
  plunges; «+5 %» at 6.2 M → «circular» / «bound» / «bound with r_peri = 3.697 M» depending on the moment; «+5 %» at
  20 M → r_peri 2.4297 M (true 20 M), r_apo 20 M (true 26.02 M); «−5 %» at 20 M → «circular» or «escape» (true bound,
  15.506–20 M).
* `out/05_nearly_circular.txt`: r₀ = 20, k = 1.0000001 → «circular» with failing circle checks.

Suggested fix. Use what is known about the start instead of re-finding it: (i) snap |v_r| ≤ 1e-12·v to 0 in the boost
(as is done for v_φ) or in `OrbitStream`; (ii) when y′(0) = 0, F(1) = 0 by construction — divide F by (y − 1)
synthetically, F = (y − 1)(2u_s y² + (2u_s − 1)y + (2u_s − 1 + 2A)) + F(1), and take the other two turning points from
the quadratic, so no root is compared with 1 ± tol; the sign of y″(0) then says whether the start is the periapsis or
the apoapsis; (iii) for y′(0) ≠ 0 choose the bracket by the sign of F between consecutive roots (F ≥ 0 on the allowed
interval) and the direction of motion; (iv) tests: the two grids of `11_classify_scan.py` against 40-digit roots.

### V4-2 (error) — an outward unbound launch without an inner turning point is classified «падение на центр»

Location: `orbit_stream.py:164–171` (`elif r_peri is None: kind = "plunge"` precedes the escape case regardless of the
direction of motion); `visualizations/v04_orbits/engine/body.py:190–197` (Newton: `r_peri <= r_stop → "plunge"`
regardless of direction).

What is wrong. A body moving outward on an unbound orbit (e ≥ 1, no apoapsis) never comes back, whether or not a
periapsis root exists behind it. The run labels it «падение на центр» and then ends it with «уход на бесконечность».

Evidence: `08_outward_unbound_kind.py` → `out/08_outward_unbound_kind.txt`: GR r₀ = 3.5, k = 0.95, angle +45°
(e² − 1 = 0.076) → kind «plunge», end of the run: escape at 3500 M; GR r₀ = 20, k = 1.6, +89° → «plunge», escape;
Newton r₀ = 20, k = 1.6, +89.9999° and k = 1.5, +89.99999° → «plunge», escape.

Suggested fix: if v_r > 0 and there is no outer turning point (r_apo None, or E ≥ 0 in Newton), the kind is escape;
«plunge» needs an inward motion or a bound orbit. (Related, nit: for an outward escape the segment text quotes the
periapsis of the hyperbola behind the body, «перицентр 3.7441M», which the body never passes.)

### V4-3 (error) — a radial fall from r₀ ≳ 10⁶ M does not stop at the horizon; at 10⁸ M the run shows r < 2M and v > c

Location: `orbit_stream.py:301–358` (`_advance_radial`, the scaled proper time s = τ/r₀^{3/2}); the cycloid check
`visualizations/v04_orbits/viz.py:686–693`.

What is wrong. The radial scheme integrates ρ = r/r₀ in s = τ/r₀^{3/2} with s ≈ 1 over the whole fall. The last
stretch to the stop (r − 2M from ~10⁻⁴ M to 2·10⁻⁶ M) lasts ~10⁻⁴ M of proper time, i.e. Δs ~ 10⁻⁴/r₀^{3/2}, which
for r₀ ≳ 10⁶ M approaches the spacing of doubles near s ≈ 1: the stop event cannot be located. The cycloid check is
evaluated at the radius where the integrator happened to stop, so it passes (6e-14) and nothing flags the error.

Evidence: `07_horizon_stop_large_r0.py` → `out/07_horizon_stop_large_r0.txt`. Stop radius r − 2M (nominal
2.000002e-6 M): r₀ = 10⁶: 1.568e-6; 10⁷: 4.47e-6; 3·10⁷: 4.80e-5; 10⁸: 3.51e-4 (engine, one call). Through the run
(preset «radial», r₀ = 10⁸, chunks ended by the time event): the stop event at **r = 1.99974 M** and the frame shows
**v = 1.0000655 c, dτ/dt = −1.3·10⁻⁴, 1 − dτ/dt = 1.00013**, «гравитация» and «движение» factors 0; the event text
reads «Падение за горизонт: r = 1.9997379M»; check `fall_tau` rel 6e-14. `out/03_engine_vs_mp.txt` (plunges): the
non-radial (Binet) scheme stops exactly at 2.000002e-6 M from r₀ = 10⁸ too, so only the radial scheme is affected.

Suggested fix: integrate the radial fall in a variable that resolves its end — for the inward leg r itself (dτ/dr =
−1/√R, dt/dr = −e/(f√R), with the turning-point substitution used in `proper_time_between`), or the cycloid parameter
η for e < 1; alternatively restart s at every chunk and shorten the chunks geometrically before the stop. Add a check
(engine test and run) that the stop event lies at 2/(1 − HORIZON_GAP) to ~1e-12 and that frames never show r ≤ 2M or
v ≥ c.

### V4-4 (error) — Newton world: eccentric orbits lose 2π per periapsis passage, apsides are missed, energy drifts

Location: `visualizations/v04_orbits/engine/body.py:215–263` (swept angle by `np.unwrap` of atan2 between samples,
4000 samples per period; apsides as sign changes of r·v on those samples), `body.py:327–349` (`_refine`),
`lfphys/lfphys/theories/approx/newton.py:321–323` (`atol = 1e-12·max(1, |r₀|)`, i.e. 1e-12 of r₀ in the scaled
units of `NewtonTrack`).

What is wrong. Near a deep periapsis the angle swept between two stored samples exceeds π (at −85°: ~9 rad per
sample), so `unwrap` takes the wrong branch and ψ loses 2π per passage; the run then measures a periapsis «advance»
of −360° per orbit and the check «эллипс замкнут» fails — the opposite of what the Newton world is there to show. For
r_peri/r₀ ≲ 10⁻⁸ no apsides are found at all. The fixed absolute tolerance (1e-12 of r₀) is too coarse for the
periapsis radius, so the energy drifts beyond the check's 1e-8. A radial fall into the point mass (speed 0, or a
boost of −100 %) fails the energy check as well.

Evidence: `09_newton_track.py` → `out/09_newton_track.txt` (preset `newton_ellipse`, speed 1, angle varied):
−80°: correct; −85°: `adv` −1 296 000″ (−360°/orbit), FAIL; −89°: same, and energy drift 1.1e-8 FAIL; −89.9°: same,
period rel −5.6e-7 (tol 1e-8) FAIL, energy 6.6e-7 FAIL; −89.99°: no periapsis detected, energy 5.9e-7 FAIL.
`out/04_adversarial_live.txt` (`newton_radial_and_eccentric`, `boost_stop_body`): radial fall from rest: energy
9.8e-7 FAIL; boost dv = −1: energy 6.7e-7 FAIL. All inputs are inside the schema's ranges.

Suggested fix: carry the swept angle as an integrated quantity (dψ/dt = h/r², a fifth component of the ODE in
`integrate_body`, or atan2 of the cross and dot products of consecutive positions on an adaptive grid), locate apsides
with solve_ivp events on r·v on the dense output (as the GR stream does), and use a tolerance relative to the local r
(or regularised Kepler variables). State in the README what the point-mass stop at 10⁻⁶ r₀ does to the conservation
check, or stop earlier.

### V4-5 (should-fix) — the circle checks assume an exact circle; «circular» is granted at 1e-6

Location: `orbit_stream.py:164–165` (circular if |r_apo − r_peri| ≤ 1e-6 r_peri); `body.py:190` (Newton: ecc < 1e-6);
`viz.py:636–668` (rate and period tol 1e-10, Newton period 1e-8, `circ2` 1e-9; the guard |r − r₀| ≤ 1e-6 r₀);
`viz.py:695–704` (the quadrature reference of the fall time).

What is wrong.
* An orbit classified circular may be eccentric up to ~5e-7 (GR) or 1e-6 (Newton); its azimuthal period and mean
  dτ/dt then differ from 2π r₀^{3/2} and √(1 − 3M/r₀) by up to ~1e-6, 10⁴ times the tolerance: legitimate inputs
  fail. `out/05_nearly_circular.txt`: GR r₀ = 20, k = 1.0000001: rate rel 2.3e-8, period 3.9e-7, `circ2` 5.1e-7 —
  all FAIL; k = 0.9999998: same; launch angle 1e-5°: rate 2.8e-9, period 4.7e-8 FAIL; `bh_isco` + boost 1e-9: FAIL;
  Newton r₀ = 50, k = 1.0000001 and 1.0000004: period rel 3.0e-7 and 1.2e-6 (tol 1e-8) FAIL.
* Unstable circles (r₀ < 6M): rounding grows, the guard 1e-6 r₀ lets laps with a visible departure through: r₀ = 4
  (marginally bound): rate and period rel 2.1e-10 FAIL; 4.5 M: rate −6.0e-9, period −9.0e-9 FAIL; 5 M: −1.6e-10,
  −3.1e-10 FAIL; 3.0001 M: rate 6.8e-8 FAIL (`out/04_adversarial_live.txt`).
* After such an orbit falls, `fall_tau` compares with `plunge_proper_time` from r₀, where R(r) has a double zero:
  the integral diverges, `quad` stops at its subdivision limit (IntegrationWarning) and returns a finite number:
  5 M: rel 1.07, 4.5 M: rel 1.11 — FAIL, although the run is right (the fall time of a body on an unstable circle is
  set by rounding and has no reference).

Suggested fix: grant «circular» only to the tolerance the circle checks use (or give the circle checks a tolerance
from the measured eccentricity: |Δ|/period ≈ 1.5·ecc); for r₀ < 6M check only laps with |r − r₀|/r₀ below what
keeps the rate within tol (along the orbit dτ/dt = (1 − 2M/r)/e, so a mean departure δr shifts it by
≈ 2M/(r − 2M)·δr/r₀ — up to 2·10⁻⁶ at 3M under the present 1e-6 guard); for a start on a double root of R give `fall_tau` no
reference («—») and say why.

### V4-6 (should-fix) — a bound orbit with apoapsis beyond 1000 r₀ ends as «уход на бесконечность»

Location: `orbit_stream.py:93` (r_far = 10³ r₀), `orbit_stream.py:161–171`; `body.py:177`; `viz.py:109–110`
(`END_RU`).

Evidence: `out/04_adversarial_live.txt`, `bound_beyond_r_far`: GR r₀ = 20, k = 1.3416: kind «связанная (эллипс с
прецессией)», r_apo = 2.96·10⁵ M; the run ends with «уход на бесконечность» at r = 2·10⁴ M. Newton k = 1.4141:
«связанная (эллипс Кеплера)», r_apo = 1.25·10⁵ M, same end. (A radial throw with apex ≥ r_far is classified
`radial_escape`, so the two routes disagree.)

Suggested fix: for a bound orbit call the end «вышло за край расчёта (1000 r₀); орбита связана, апоцентр … M» (or
extend r_far past r_apo for bound orbits); make the radial and non-radial routes consistent.

### V4-7 (should-fix) — the turning-point reference loses accuracy by taking e instead of e² − 1; its tolerance is self-inflicted and too small near the ISCO

Location: `lfphys/lfphys/core/gravity/orbits.py:69–99` (`turning_points`, `elements`, via `periapsis_advance`:
`(e * e - 1.0) / l**2`); `viz.py:589–597` (tolerance max(1e-9, 4ε/(|e² − 1|·ecc))).

What is wrong. The run's own events are accurate to ~1e-13; the reference recomputes e² − 1 with cancellation.
* Mercury (`02_mercury.py` → `out/02_mercury.txt`): e·e − 1 is off by 5.7e-9 relative; `orbits.elements` gives
  r_peri off by 1.1e-8, r_apo by 1.7e-8, ecc by 6.4e-8 (40-digit truth), while the run's periapsis is off by 4.6e-13.
  The 1.68e-7 tolerance is therefore not a limitation of the problem: `np.roots` on the same cubic with e² − 1 from
  `local_velocity_to_constants` (no cancellation) gives 2.8e-14 and 2.7e-14.
* Near the ISCO the conditioning of close roots is not captured by 1/(|e² − 1|·ecc): `bh_isco` + boost 1e-7 at 0.37
  turn (`out/05_nearly_circular.txt`): `r_apo` FAILS with rel −5.3e-9 vs tol 1.9e-9 — the event is right
  (6.200052076055417; 40-digit 6.200052076, `out/06_turning_point_start.txt`), the reference is off by +5.3e-9.
  `10_turning_point_reference_near_isco.py` → `out/10_…txt`: near the ISCO the reference errs by 3e-12 … 1.3e-9, the
  events by ≤ 5.2e-14.
* `merc_e` displays this reference's eccentricity (6.4e-8 off), see V4-9.

Suggested fix: let `turning_points`/`elements`/`periapsis_advance` take e² − 1 (computed as in
`local_velocity_to_constants`) and polish the roots (Newton on the cubic, or arb via python-flint, which is in the
image); then a tolerance of ~1e-12 relative to the root separation is justified everywhere.

### V4-8 (should-fix) — in a weak field the second scheme's conservation checks do not test the binding energy

Location: `viz.py:627–634` (`drift_e` relative to e, `drift_n` = |u·u + 1|, both < 1e-9);
`orbit_stream.py:483–495`.

What is wrong. For Mercury |e − 1| = 1.27e-8 and |e² − 1| = 2.55e-8 (`out/02_mercury.txt`). A drift of e of 1e-9
(relative to e ≈ 1) is 8 % of the binding energy; a norm drift of 1e-9 is 4 % of e² − 1. The rows pass (measured
4.4e-16 and 8.9e-16), but their tolerance admits a wrong orbit; in these variables the double-precision scheme can
resolve the binding energy only to ~eps/|e − 1| ≈ 1e-8 relative.

Suggested fix: report both drifts relative to |e² − 1| (and the attainable floor eps/|e − 1| in the note), or carry
e − 1 and the norm in cancellation-free form.

### V4-9 (nit) — Mercury rows show a closed form as the «measured» value

Location: `viz.py:601–606`. `merc_a` and `merc_e` («по точкам поворота») take a and ε from `orbits.elements` (the
closed-form roots, with V4-7's 6.4e-8 error in ε), not from the run's measured periapsis and apoapsis. Suggest: use
the first periapsis and apoapsis events of the segment (both are in `self.S`), so the row is a run measurement.

### V4-10 (nit) — the 6πM/p row could be a second-order verdict

Location: `viz.py:539–554`. The coefficient is right (see «Verified correct»), but the band ±1.5·(18 + ε²)/4·M/p also
accepts a value with no next-order term at all (exactly 6πM/p). With the verified next term the row could compare
with 6πM/p·[1 + (18 + ε²)/4·M/p] and tolerate 1.5·(5/12)(54 + 9ε²)(M/p)² + the integration tolerance.

### V4-11 (nit) — the GR radial period has no reference although a quadrature reference is at hand

Location: `viz.py:567–568` (ref «—», note «замкнутой формулы … нет»). t_r = 2∫ e dr/(f√R) over [r_peri, r_apo] with
the turning-point substitution (the same machinery as `proper_time_between`) is a reference without differential
equations; in `out/03_engine_vs_mp.txt` the stream's radial periods in t and τ agree with it to ≤ 1.6e-12 (1.2e-9
next to the separatrix).

### V4-12 (nit) — the «ISCO» row cannot fail

Location: `viz.py:710–715`: emitted with `ok=True` only after a fall has happened. It is a statement, not a check;
present it as an event/notice, or compare the observed outcome with the kind predicted from the turning points.

### V4-13 (nit) — Newton conservation rows show a tolerance different from their verdict

Location: `viz.py:672–675`: verdict `ok = drift < 1e-8`, but the row carries the default `tol = 1e-9`.

### V4-14 (nit) — ghost end events are repeated after toggling the ghost

Location: `viz.py:340–351`, `viz.py:449–461`. Switching the ghost off and on rebuilds it from the segment start and
re-reveals its past, including its end event: `out/04_adversarial_live.txt` (`ghost_toggles`, preset «radial»):
`ghost@0.004893` twice; the same in `ghost_superluminal_newton`.

### V4-15 (nit) — the view says «за горизонтом» at a finite world time

Location: `web/view.js:410`. At the stop (r − 2M = 2·10⁻⁶ M) the body is outside the horizon, and for the distant
observer whose time is on the axes it never crosses; the event text in `viz.py:509–511` says so. A label such as «у
горизонта (r − 2M = 2·10⁻⁶ M; дальше t → ∞)» would agree with it.

### V4-16 (should-fix) — switching the ghost on late blocks the worker for up to a minute

Location: `viz.py:340–348` (`set_live` → `_make_track` from the segment start → `_reveal_ghost(now)` inside one
command); `body.py:296–314` (`_thin`, a Python loop over every fine sample, 4000 per period), `body.py:327–349`
(a second fine integration per apsis).

Evidence: `12_long_runs_and_ghost_catch_up.py` → `out/12_long_runs_and_ghost_catch_up.txt`: Mercury after 415 orbits
(one century) — the `set ghost=True` command takes 9.6 s; after 2000 orbits — 58 s; preset «default» after 1000
orbits — 24 s; Newton world after 1000 orbits — 11 s, after 3000 orbits — 48 s. During this time the real-time
runner neither draws nor accepts commands (the command handler is synchronous). No error, no wrong number: a hang as
seen from the player.

Suggested fix: compute the ghost's past in bounded slices across steps (reveal it progressively, with a notice), or
keep the ghost running in the background from the segment start whenever a segment begins (it costs as much as the
body), or limit the catch-up to the drawn window (the last turns) and say so.

## Verified correct (with the precision reached)

Each item: state **useful** (confirms a claim), **neutral** (no claim depended on it).

1. **Equations (useful).** Checked by hand: e = γ√(1 − 2M/r), e² − 1 = γ²(v² − 2M/r), l = γ v_φ r from the static
   observer's velocity; dr/dτ = e v_r; the scaled Binet form y″ = A − y + 3u_s y² with A = 1/(l²u_s),
   B = (e² − 1)/(l²u_s²), dT_t/dψ = e/(L y²(1 − 2u_s y)), dT_τ/dψ = 1/(L y²), L = |l|√u_s, y′(0) = −e v_r/(|l|u_s);
   the first integral e² − 1 = l²u_s²(y′² − 2u_s y³ + y² − 2Ay); the radial form ρ″ = −1/ρ², dT/ds = e/f; the
   velocity at a state v_r = (dr/dτ)/e, v_φ = l u√(1 − 2u)/e; dτ/dt = (1 − 2M/r)/e = √(1 − 2M/r)·√(1 − v²); the
   clock deficit (e − 1 + 2M/r)/e with e − 1 = (e² − 1)/(e + 1); the cycloid τ = √(r₀³/8M)(η + sin η); the impact
   speed √(1 − (1 − 2M/R)/e²); circular dτ/dt = √(1 − 3M/r) and period 2π√(r³/GM) in t; the geodesic equations of
   `geodesic_tau`.
2. **Bound orbits vs 40-digit references** (`out/03_engine_vs_mp.txt`, ten orbits from r₀ = 4.6 M to 10⁸ M; useful):
   advance per radial period 8e-14 … 3e-12 relative in the strong field, 3e-11 at 10³ M, 5e-9 at 10⁶ M, 6.5e-6 at
   10⁸ M (absolute 8.5e-13 rad, i.e. the integrator's phase floor ~1e-12 rad, as the README states); radial period in
   t and τ ≤ 1.6e-12 (1.2e-9 next to the separatrix, r₀ = 4.6, k = 1.0005); turning points ≤ 9.2e-13 (3.3e-11 next to
   the separatrix); first integral ≤ 2.2e-12; e² − 1 from the launch data ≤ 5e-16.
3. **Plunges (Binet route) to the horizon stop** vs 40-digit quadrature (useful): τ ≤ 2.6e-13, t ≤ 2e-11; the stop
   at r − 2M = 2.000002e-6 M exactly, from r₀ = 2.1 M to 10⁸ M. Radial from rest at 20 M: τ 6.9e-14, t 2.5e-12
   (the radial route fails only from r₀ ≳ 10⁶ M, V4-3).
4. **Clock deficit** 1 − dτ/dt vs mp over r ∈ [2.000002 M, 10 r₀]: ≤ 1.5e-14 relative, also for Mercury (~5e-8)
   (useful).
5. **Mercury** (`out/02_mercury.txt`; useful): for the preset's own initial data the exact Schwarzschild advance per
   Julian century is **42.9804718″** (40 digits: χ-integral advance 5.018654046e-7 rad per orbit, radial period
   87.96936116 d by quadrature); the run measures 42.9805386″ (rel 1.55e-6; per-orbit values +1.26e-6 … +1.82e-6, a
   systematic phase error ≈ 7e-13 rad per orbit); vs Will's 42.98″ rel 1.25e-5, as claimed. 1PN with the NSSDCA a, e
   and GM☉ (IAU 2015 B3 nominal 1.3271244e20) per Kepler period gives 42.980473″ — Will's rounded 42.98 is consistent.
   Unit conversion (36525 d of 86400 s, arcsec) and the use of the radial (anomalistic) period are right. The run's
   a = 0.387098943 AU and ε = 0.2056307164 (40-digit, from its turning points) differ from NSSDCA by 3.3e-8 and
   1.3e-7, i.e. by O(M/r), as the comment at `viz.py:41` says.
6. **The next-order coefficient (18 + ε²)/4** (`out/01_next_order_coefficient.txt`; useful): derived from the exact
   χ-integral Δ = ∫₀^{2π} dχ/√(1 − 2μ(3 + ε cos χ)) − 2π (μ = M/p, p and ε from the turning points as in
   `orbits.elements`) by the binomial series: Δ = 6πμ[1 + (18 + ε²)/4·μ + (5/12)(54 + 9ε²)μ² + …]; confirmed at 50
   digits to 1e-7 (p = 10⁷) for ε = 0 … 0.99. With it the «ppn» band 1.5·(18 + ε²)/4·M/p (M/p ≤ 0.02) has a margin
   1.33–1.49 over the true deviation — justified.
7. **`orbits.advance_from_turning`** given exact turning points: ≤ 1e-13 relative for p ≤ 10⁵, 6e-10 … 1.3e-9 at
   p = 3·10⁷ (cancellation 4K/√… − 2π, absolute ~4e-16 rad) — adequate for the `adv` row (useful).
8. **Boost continuity** (`out/09_newton_track.txt`, dv = 0; useful): the new segment's constants equal the old ones to
   3.5e-14 (GR, dense-output state) and 8.5e-12 (Newton, Hermite state).
9. **Robustness without wrong numbers** (`out/04_adversarial_live.txt`; neutral): r₀ = 2.1 M (speed 1.2 refused
   «не меньше скорости света», speed 0.9 and 0 plunge correctly), r₀ = 3.0001 … 3.1 M circles (γ up to 100), 4 M, 6 M
   (exact ISCO), 6 ± 1e-4 M (the failing circle rows at 3.0001 M and 4 M are V4-5), r₀ = 10⁸ M bound/circular/escape (except the radial fall, V4-3), repeated boosts (25 × +5 %,
   40 × −5 %, ending in escape or the horizon; boosts after the end refused), dv = −1 (GR; Newton:
   V4-4), relaunch during and after a
   plunge, boost near the horizon refused (v ≥ c), ghost on/off in five presets, new worlds (Newton with R, 10⁹ M☉,
   1 M☉ with R = 3M = 4.43 km, and R = 2.95 km < 2M — refused), launch angles ±90° and ±(90° − 1e-5 … 1e-10°): no
   exceptions, no NaN or inf in any message or blob, no timeouts (all scenarios < 6 s).
10. **Causality and records** (neutral): the existing tests (nothing revealed ahead of the world time, the old future
    withdrawn on a live change, a refused change leaves the world unchanged) pass; I found no counter-example.
11. **Honesty of presentation** (useful): the Newton world is flagged «модифицированная физика» (law parameter with
    `standard = "GR"`); `theories.approx.ppn` and `theories.approx.newton` are listed in the world's engine modules
    with their layer; 6πM/p is labelled leading order and becomes an informative row (no verdict) for M/p > 0.02; the
    ghost is labelled as the other theory from the same initial data and does not touch the world; the horizon stop
    and its meaning for the distant observer are stated in the event text and the README; the sources of a, ε and
    42.98″ match the fetched texts.
12. **View** (`web/view.js`, read; neutral): axes «r, M», «1 − dτ/dt», world time t; the scale bar and grid in M with
    metres/AU; the clock panel's factors √(1 − 2M/r) and √(1 − v²) multiply to the displayed dτ/dt; apsides, apsidal
    lines and the ghost are drawn as the help text describes; no physics is computed in the view. The only
    mislabelling found is V4-15 (and the wrong kind/turning points it receives from V4-1/V4-2).
