# u34 — Orbits and clocks: general relativity and Newton

**English** | [Русский](README.ru.md)

One test body orbits a central mass. The run computes the orbit from the body's initial data under the world's law
of gravity, reveals it as the world's time reaches it, and measures on its own orbit what the owner wants to see:
the advance of the periapsis (Mercury's 43″ per century, strong precession near a neutron star, the instability
inside the ISCO), the fall through the horizon, and the body's clock against the clock of a distant observer.
The visualization is a wrapper over the engine `lfphys` (`lfphys/LAYERS.md`): its own code is the time line,
the segments, the measurements and the drawing.

## 1. World, live parameters, actions

| kind | parameter | meaning |
|---|---|---|
| world (law) | `gravity` | `GR` — Schwarzschild geodesics (core, standard); `newton` — Newtonian gravity (approximation outside the core; the world is flagged "MODIFIED PHYSICS") |
| world | `mass_msun` | central mass, 1 … 10⁹ M☉ (GM☉ = 1.3271244·10²⁰ m³/s², IAU 2015 B3). It sets the units: M = GM/c² (length), GM/c³ (time) |
| world | `radius_km` | radius of the central body; 0 = black hole (GR) or point mass (Newton). In GR it must exceed 2M |
| live | `r0` | launch radius in M (2.1 … 10⁸; the upper end admits Mercury, r ≈ 3.1·10⁷ M) |
| live | `speed` | launch speed as a fraction of the local circular speed (0 … 1.6) |
| live | `angle` | direction of the launch velocity from the tangential direction, −90 … 90° (+ outward) |
| live | `ghost` | show the other theory's orbit from the same initial data (display; does not change the world) |
| live | `time_units` | times on the panels in seconds or in GM/c³ (display) |
| action | "Push" (`boost`, `dv`) | at the current moment, the speed measured by the static observer is multiplied by 1 + dv along the motion (−1 ≤ dv ≤ 1); the body's clock runs on |
| action | "New launch of the body" (`relaunch`) | the body is launched again from the live initial data at the current moment; its clock starts from zero |

A change of `r0`, `speed` or `angle` applies at once: the body is launched again at the current world time, at
radius r₀ on the current direction from the centre to the body (φ₀ = the body's current polar angle; 0 at the start
of the world). The computed future of the previous orbit is withdrawn; its revealed past stays (a faded trail).
Every launch or boost starts a new **segment**; checks are grouped per segment.

**Initial data.** In GR the launch velocity is what the static observer at r₀ measures, v = k·v_ref with
v_ref = √(M/(r₀ − 2M)) (the local speed of the circular geodesic) for r₀ > 3M and v_ref = c below 3M (there is no
circular timelike orbit there; at 3M both are c). Components: v_r = v sin α, v_φ = v cos α (|v_φ| ≤ 10⁻¹²·v is set
to 0: a radial launch; |v_r| ≤ 10⁻¹²·v is set to 0: a start at a turning point — the state of a boosted circular orbit
carries v_r ~ 10⁻¹⁷ from rounding). Then (`lfphys.core.gravity.orbits.from_local_velocity`)

    e = γ √(1 − 2M/r₀),   e² − 1 = γ² (v² − 2M/r₀)   (written so, without cancellation),   l = γ v_φ r₀.

In a Newton world v_ref = √(GM/r₀) and the same numbers are the Newtonian velocity. The ghost uses the same r₀, φ₀
and velocity vector (in units of c) in the other theory; in GR this requires v < c.

## 2. What the run computes

**GR (core): `lfphys.core.gravity.orbit_stream`** (new engine module of this visualization, tested in
`lfphys/tests/test_orbit_stream.py`). Non-radial orbits: the Binet equation in the swept angle ψ for u = M/r, scaled
by the launch value u_s (y = u/u_s) so that a weak-field orbit keeps the relative tolerance 10⁻¹² (Mercury's
general-relativistic term 3u_s y² is 10⁻⁷ of the others):

    y'' = A − y + 3 u_s y²,  A = 1/(l² u_s);   dt/dψ = e r²/(|l| (1 − 2M/r)),   dτ/dψ = r²/|l|.

The state (y, y′) is carried exactly from chunk to chunk; t and τ are integrated with it (the absolute tolerance of
y, y′ is scaled by the smallest y the orbit reaches, so a far apoapsis keeps its relative precision). Radial orbits
(l = 0): r̈ = −M/r² in proper time (exact for radial geodesics) with dt/dτ = e/(1 − 2M/r); every chunk is integrated
in units of its own start radius and ends when r has fallen to a quarter (or grown fourfold) of it, so the end of a
fall from 10⁸ M is resolved (review V4-3). Events are located on the DOP853 dense output: periapsis and apoapsis
(zeros of du/dψ), each full turn, the horizon, the body's surface, escape, and the requested coordinate time (end of
a chunk).

**Kind of orbit** (shown, and deciding which checks run): the turning points are found as offsets z = y − 1 from the
start, as the real roots (30 digits, mpmath) of F(1 + z) = 2u_s z³ + (6u_s − 1)z² + F′(1) z + y′(0)², whose constant
term is the integrator's own first integral at the start; a start at a turning point is an exact root and is never
re-found (review V4-1). Bound: turning points on both sides; circular: their relative spread s = (r_apo − r_peri)/r_peri
≤ 10⁻⁶ (no apsis events, circle checks with a tolerance that includes s); plunge: no periapsis above the stop (up to
the apoapsis first if moving out); escape: no apoapsis, or no turning point at all and moving outward (review V4-2).
An orbit with an apoapsis is followed out to it: the escape radius is max(1000 r₀, 1.5 r_apo) (review V4-6).

**Horizon.** In the coordinate time t of the distant observer the body only approaches r = 2M (t grows
logarithmically); the integration stops at r = 2M/(1 − 10⁻⁶) ≈ 2M + 2·10⁻⁶ M, where the event "a fall through the horizon"
is revealed. Going much closer costs ~10⁶ steps in double precision (measured: 10⁻⁸ takes seconds); the proper time
to that point is reported and checked.

**Newton (approximation): `lfphys.theories.approx.newton.integrate_body`**, every chunk in units of its own start
radius r_c (GM = 1, time unit r_c^{3/2}), so that the engine's tolerance (relative 10⁻¹², absolute 10⁻¹² of the
position scale) is uniform in position and velocity at every depth of an eccentric orbit; a chunk ends when the body
has fallen to r_c/4 (the engine's stop radius) or after half a local dynamical time, ~640 samples per local time unit
(review V4-4). The run's own measurements on this output: the swept angle from the angle between successive samples
(atan2 of their cross and dot products), apsides as zeros of r·v (located on a second, 1000× finer integration by the
engine from the bracketing sample), full turns, the energy E = v²/2 − GM/r and the angular momentum along every
sample. Same kinds as in GR (an outward unbound body escapes even if the conic's periapsis behind it lies below the
surface).

**Time line and causality.** The orbit is computed ahead in chunks; samples, apsides, turns and the end are revealed
only when the world time reaches them (`engine/body.py`, `Track.take`). The trail is thinned for drawing (≈240
samples per turn plus a geometric approach to the horizon). A live change or an action withdraws the computed
future and starts a new segment at the current moment; the state at that moment is the exact dense-output state
(GR) or, in Newton, a short re-integration by the engine from the nearest fine sample (frames use the cubic Hermite
interpolant, velocity from its derivative). **The ghost** switched on late is computed from the segment's start in
slices of 0.03 s of wall time per world step, so the worker never blocks (review V4-16); a notice says so until it
has caught up.

**Clock.** The body's proper time τ is integrated with the orbit (τ = t in Newton). The panel "Clocks" shows t, τ,
their ratio since the launch, and dτ/dt = (1 − 2M/r)/e = √(1 − 2M/r) · √(1 − v²) (gravitational factor of the static
clock at r times the factor of the speed relative to it). The plot shows 1 − dτ/dt along the revealed orbit.

**Special radii** drawn in the plane (GR): horizon 2M, photon sphere 3M, marginally bound orbit 4M, ISCO 6M, from
`lfphys.core.gravity.kerr` at zero spin.

## 3. Checks (panel "Checks: computed ↔ reference")

Each row: the value computed in this run from its own events, the reference, the relative difference, the tolerance.

| check | computed | reference | tolerance |
|---|---|---|---|
| advance per orbit (GR, bound) | mean over n orbits of (ψ of periapsis k+1 − ψ of periapsis k − 2π) | exact elliptic integral `orbits.periapsis_advance` from e² − 1 itself | max(10⁻⁸, (2·10⁻¹¹ + 10⁻¹⁴/s) rad/Δφ): the phase floor ~10⁻¹² rad, and the apsis of an orbit with spread s located to ~10⁻¹⁴/s rad |
| same vs the weak-field series (M/p ≤ 0.02) | same | 6πM/p·[1 + (18 + ε²)/4·M/p]: the first term from `theories.approx.ppn` (γ = β = 1), the second from `orbits.advance_series` (verified against the exact integral, `test_relativity_gravity.py`) | 1.5 × the third term (5/12)(54 + 9ε²)(M/p)² + the numerical tolerance (review V4-10); for M/p > 0.02 an informative row (no verdict) |
| periapsis, apoapsis | r at the event du/dψ = 0 | the turning points of f(u) (`orbits.elements` from e² − 1, roots at 30 digits) | 10⁻¹¹ + 4ε·κ + 2·s_e·δ: κ = Σ\|terms of f\|/(\|f′(u)\|u) — the conditioning of the root (grows near the ISCO), δ — the measured drift of e² − 1 at that event, s_e — how it moves the turning point (review V4-7; before: e·e − 1 cost Mercury 10⁻⁸) |
| first integral | e² − 1 from the state (u, du/dψ) at each turning point | the initial e² − 1 | 10⁻⁹ |
| radial period (GR) | time between periapses | quadrature 2∫e dr/((1 − 2M/r)√R) by the smooth χ-substitution (`orbits.radial_period`) | 10⁻⁹ + 2·10⁻¹⁴/s (review V4-11) |
| second scheme | advance over the first orbit from the geodesic equations x″ = −Γx′x′ in τ (`orbit_stream.geodesic_tau`) | the main scheme | 2 × the advance tolerance; drifts of e² and of the norm along it relative to the binding energy \|e² − 1\| below max(10⁻⁹, 100ε/\|e² − 1\|) (review V4-8; Mercury: 8.6·10⁻⁷), of l below 10⁻⁹ |
| Mercury (preset only, unchanged initial data) | advance per Julian century = advance per orbit × 36525 d / the run's radial period | 42.98″/century | 2·10⁻⁴ (the reference is given to 0.01″) |
| Mercury elements | a = (r_peri + r_apo)/2 and ε = (r_apo − r_peri)/(r_apo + r_peri) from the run's first periapsis and apoapsis events (review V4-9) | 0.38709893 AU, 0.20563069 | 10⁻⁶ |
| circular orbit | Δτ/Δt over n turns; the time per turn | √(1 − 3M/r); 2π√(r³/GM) (exact for circular geodesics in Schwarzschild t) | 10⁻¹⁰ + 3s (s ≤ 10⁻⁶: the spread of the turning points); on an unstable circle laps are checked only while the largest departure from r₀ seen stays below 1.5s + 2·10⁻¹¹ (review V4-5) |
| radial fall from rest | τ to the stop radius | cycloid τ = √(r₀³/8M)(η + sin η), r = r₀(1 + cos η)/2 | 10⁻⁹ |
| any other fall | τ to the stop radius | quadrature τ = ∫dr/√R(r), R = e² − (1 − 2M/r)(1 + l²/r²) (`orbit_stream.plunge_proper_time`, no differential equation); none ("—") when the start is on a (nearly) double root of R — an unstable circle, where the integral diverges and the fall time is set by rounding (review V4-5) | 10⁻⁹ |
| impact on the surface | the static observer's speed from the integrator's state at r = R | √(1 − (1 − 2M/R)/e²) | 10⁻⁹ |
| outcome | the end the run observes (horizon / surface / centre / escape) | the kind predicted from the turning points at the segment start; a circle inside the ISCO may end either way | ✓/✗ (review V4-12; replaces the ISCO statement) |
| Newton: advance | as above, apsides as zeros of r·v | 0 (closed ellipse) | 10⁻⁹ + 2·10⁻¹³/s rad |
| Newton: period | time between periapses (or per turn on a circle) | Kepler 2π√(a³/GM), a = −GM/(2E) | 10⁻⁸ + 2×(measured energy drift) + 4·10⁻¹³/s (circle: 10⁻⁸ + 3s) |
| Newton: conservation | maximal relative drift of E and of h over all samples | — | E: 10⁻⁹ of the largest term v²/2 + GM/r on the orbit (relative to \|E\|: grows ~1/r_peri on very eccentric orbits, review V4-4); h: 10⁻⁹; the row shows the tolerance of its verdict (V4-13) |

Rows with no closed form show the reference "—" (the advance per century outside the Mercury preset, the fall time
from an unstable circle).

Typical values in the presets (2026-10-24): advance vs exact 10⁻¹³ (strong field), 1.5·10⁻⁶ (Mercury, absolute
~10⁻¹² rad); Mercury 42.9805″/century; turning points vs reference ≤ 10⁻¹² (Mercury 7·10⁻¹⁶); radial period vs
quadrature ~4·10⁻¹³; circular dτ/dt 5·10⁻¹⁵; cycloid 6·10⁻¹⁴ (also from 10⁸ M); plunge vs quadrature 4·10⁻¹¹;
Newton advance ≤ 10⁻¹¹ rad (also at −89.9° launch angles), period 2·10⁻¹¹, energy drift 10⁻¹⁰ of |E|.

## 4. Approximations and limits (stated)

* **Test body:** its mass and its own field are neglected (Mercury: the mass ratio GM_Mercury/GM☉ = 1.7·10⁻⁷, from the same fact sheet, is not
  modelled; the reference 42.98″ is the same test-body value).
* **Equatorial plane** of a non-rotating, spherical central body: the exterior Schwarzschild metric (Birkhoff's
  theorem). No rotation (no Lense–Thirring, no quadrupole J2: the Sun's J2 = 2.2·10⁻⁷ adds ≈0.03″/century to
  Mercury by Will's Eq. (65), not modelled), no tidal forces, no other bodies (the planetary perturbations of
  Mercury's orbit are not modelled; only the general-relativistic part of its perihelion advance is).
* **No radiation reaction** (no gravitational waves): orbits do not decay.
* **Interior of the body is not modelled:** the orbit ends on the surface (r = R). In GR R > 2M is required; for a
  static star R > 9M/4 (Buchdahl) — not enforced.
* **Horizon:** the coordinate-time integration stops at r − 2M = 2·10⁻⁶ M (see §2).
* **Newton:** an approximation of weak fields and low speeds; no limit on speed; the GR special radii have no
  meaning there (drawn only for a GR ghost). A point mass (R = 0) stops a body only at r = 10⁻⁶ r₀; on the way
  there the kinetic and potential terms grow ~1/r, and the integration (relative tolerance 10⁻¹² of the local terms)
  keeps E only to ~10⁻¹² of them, i.e. 10⁻⁶ of |E| for a fall from r₀ — hence the energy tolerance relative to the
  largest term (§3). The same limits the period of extremely eccentric orbits (a launch at −89.9°, r_peri = 1.5·10⁻⁶ r₀:
  period error 3·10⁻⁶ at a measured energy drift of 1.2·10⁻⁵, which the period tolerance includes).
* **Escape:** the run follows an unbound body to 1000 r₀; an orbit with an apoapsis to 1.5 r_apo.

## 5. Files

* `viz.py` — schema, presets, the `Simulation` (segments, live changes, actions, the time line, checks).
* `engine/body.py` — the tracks: chunking of the engine's integrators, the reveal in time, the Newtonian apsides
  and conservation measurements, states at a given time.
* `web/view.js` — the drawing: orbit plane (pan, zoom), plots r(t) and 1 − dτ/dt, panels "Orbit" and "Clocks".
* `tests/test_u34_orbits.py` — the run as a whole: all presets with all checks passing, measured advance vs exact,
  Mercury 42.98″/century, causality (nothing revealed ahead of the world time), live change restarts the body and
  withdraws the old future, a refused change, a boost keeps the clock, the Newton world is flagged and its
  ellipse closed while the GR ghost precesses, ISCO, cycloid, circular dτ/dt, ghost toggle, impact, new worlds.
* Engine: `lfphys/lfphys/core/gravity/orbit_stream.py` and `lfphys/tests/test_orbit_stream.py` (added for u34).

## 6. Sources

* Mercury: NASA NSSDCA Mercury Fact Sheet (a = 0.38709893 AU, e = 0.20563069, J2000 mean elements); the GR
  perihelion advance 42.98″/century: C. M. Will, Living Rev. Relativ. 17, 4 (2014), Sec. 4.2, Eq. (65), γ = β = 1.
  Both checked against the fetched texts: `lfphys/sources/verification_2026-10-23.md`, items 1 and 2.
* Orbits, special radii, PPN: the ABOUT entries of `lfphys.core.gravity.orbits`, `kerr`, `theories.approx.ppn`.
* The next-order term (18 + ε²)/4 · M/p of the advance: verified numerically against the exact elliptic integral
  (`test_ppn_next_order_term`); used only as the tolerance of the leading-order reference.

Open items of this visualization go to `../../STATUS.md`, section "V. Visualizations — open items".
