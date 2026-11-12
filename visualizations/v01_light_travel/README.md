# v01 — Light over large distances

Finite speed of light from the Sun to the Earth, light cones, gravitational bending and delay, the speed of light
measured by observers at rest and moving along or against the light, synchronisation of clocks, relativity of
simultaneity (the Andromeda paradox), Doppler and gravitational redshift. Owner guide: `../README.md`; rules:
`../RULES.md`.

## What a run computes (and nothing else is drawn)

| what you see | how it is computed | file |
|---|---|---|
| the front of a flash | positions at the current slice of N rays traced from the emission event under the run's laws | `engine/light.py` |
| delay and bending near a mass, the shadow, loops at the photon sphere | null geodesics of Schwarzschild, RK4 in the affine parameter: d²x/dλ² = −(3/2) rs h² x/r⁵, c dt/dλ = 1/(1 − rs/r) | `engine/light.py` |
| "light reached X after …" | exact arrival events: quadratic solve (flat); quadrature + root finding on the impact parameter (GR) and exact Kepler hyperbolae (Newtonian corpuscles) for the primary and the secondary image (the lowest-order path on each side of the body; higher-order windings are not solved); moving receivers by bracketed root finding on t − t₀ − Δt(x(t)) | `engine/arrivals.py`, `engine/schwarzschild.py`, `engine/kepler.py` |
| clocks τ | proper time along each worldline from the metric of the laws (SR: √(1−v²/c²); GR: √(f − (v_r²/f + v_t²)/c²); Galilean: τ = t) | `engine/worldlines.py` |
| a rod with clocks at both ends | the rest-frame rod transformed by the laws' frame matrix (Lorentz in SR — length contraction comes out of it); B's clock set by a simulated Einstein light exchange (or, for comparison, by lab simultaneity) | `engine/apparatus.py` |
| measured speed of light | L₀ / (difference of clock readings at the computed events of passage); the result reaches the observer only when B's reading has travelled to A | `engine/apparatus.py`, `engine/world.py` |
| an observer's "now", the spacetime diagram in its coordinates | the laws' frame matrix (Lorentz / Galilean) applied to the run's events; slices c t′ = const | `engine/laws.py`, `web/view.js` |
| what an observer sees | the event on each worldline on the observer's past light cone (law-dependent: emission theory adds the source's velocity) | `engine/world.py` (`_seen`) |
| local light cone on the diagram | the laws' light velocities along ±x at the observer's event (GR: radial coordinate speed c(1 − rs/r)) | `engine/world.py` (`_cone`) |
| frequency at a receiver | ratio of the source's proper period to the received proper interval of consecutive pulses | `engine/world.py` (`_train_arrival`) |

The browser (`web/view.js`) only interpolates along the computed polylines, finds where they cross the chosen
slice and applies the matrices the run sends.

## Laws

| parameter | standard | modifications (flagged) |
|---|---|---|
| kinematics | SR (Lorentz transformations, c in every inertial frame) | `ether`: Galilean, light at c relative to the lab (ether) frame; `emission`: Galilean, light at c relative to its source (Ritz) |
| gravity | GR (Schwarzschild exterior of one body at the origin) | `newton`: light as Newtonian corpuscles (Soldner), only with `emission`; `none`: bodies absorb light but do not attract it |
| c | 299 792 458 m/s | `c_factor` ≠ 1 |

GR requires SR and Newtonian corpuscles require the emission theory (`Laws.validate`). When one law is changed and the
other is left at its standard value, the world takes the nearest law that goes with it and says so (a notice, the
scenario's text; the header's parameters and the "modified physics" list are the ones in force; review UX-params P12,
2026-11-05): ether + GR → ether without gravity (the body only absorbs light); emission + GR → emission + Newtonian
corpuscles; Newtonian corpuscles + SR → emission. In a scene without a gravitating body (measuring c, Andromeda) the
gravity law has nothing to act on and is set to «Без гравитации». Two changed laws that do not go together (ether +
Newtonian corpuscles with a body) are refused, saying what to change. A lens of radius 0 (a black hole) is GR's object:
without GR it is given the horizon's radius 2GM/c² of its mass (the preset «lensing_newton»'s choice), said too.
Walkers faster than this world's light (Andromeda, SR) are refused with the numbers to change (P7).

## Scenarios (presets)

* **Sun → Earth.** A flare on the solar surface at t = 0; Earth on its circular orbit (Kepler's law, exact for
  circular orbits in Schwarzschild coordinates), a station at rest where Earth was at t = 0, a rocket at 0.5 au.
  Light needs (1 au − R☉)/c ≈ 496.68 s plus the Shapiro excess ≈ 53 µs. Earth moves ~15 000 km during the flight.
* **Measuring c.** Three observers meet at the origin at t = 0 with velocities 0, +0.5c, −0.5c (parameters),
  carry rods of rest length L₀ along x (or y) and synchronise their B clocks by light; a source on the axis flashes.
  Variants: lab-simultaneity clocks; ether; emission theory; a transverse arm in the ether (Michelson–Morley).
* **Lensing.** A black hole (or a star of given radius) between a source and an observer; a flash and a parallel beam.
  The capture boundary of the beam is compared with b_c = 3√3/2 rs, the traced paths with exact quadrature, the
  infinite-path deflection with Darwin's closed form. The observer receives two images of the flash at different times.
* **Andromeda.** Three observers pass each other on Earth at t = 0 (walking ±1.4 m/s, or ±0.5c); an event at
  Andromeda at lab time 0. Their simultaneity lines differ by v·D/c² ≈ ±4.26 days at 2.5 Mly; the diagram button
  "у Андромеды ±10 сут" shows it. Light from the event reaches Earth 2.5 Myr later for everybody.

## Actions (in the run)

Flash from any object; boost an observer (any speed and direction; its apparatus is dismantled and re-assembled and
re-synchronised in the new rest frame); round-trip measurement with the apparatus (flat runs) or a local measurement
with a short radial rod (GR runs, static observers); a train of pulses with a given proper period (Doppler,
gravitational redshift).

## Checks emitted by the run

| check | reference (closed form) |
|---|---|
| flight time to a receiver (flat SR/ether) | \|Δx\|/c |
| radial flight time (GR) | c t = r₂ − r₁ + rs ln((r₂ − rs)/(r₁ − rs)) |
| clock rates (GR) | static √(1 − rs/r); circular geodesic √(1 − 3GM/(rc²)) |
| measured one-way speed (passing flash, own light; a flash that goes off between the ends of a rod reaches A and B running in opposite directions: no speed, the run says so — review UX-params P9 [error in earlier]: it was shown as c = 5.6·10⁸ … 7.8·10⁹ m/s) | SR+Einstein: c; SR+lab clocks: c/(1 + sβ); ether: c(1 − β²) (Einstein) or c − sv (lab); emission: c + s(u − v) |
| round-trip speed | SR, emission: c; ether: c(1 − β²) (along), c√(1 − β²) (across) |
| Doppler ratio (collinear) | SR γ_r(1 − sβ_r)/(γ_s(1 − sβ_s)); ether (1 − sβ_r)/(1 − sβ_s); emission 1 − s(β_r − β_s) |
| gravitational redshift (static ends) | √(f_e/f_r) as a frequency ratio |
| capture boundary of the beam (revealed when the bracketing rays have reached the horizon or left the scene) | b_c = 3√3/2 rs (tolerance = the beam's ray spacing) |
| swept angle of a traced ray | exact quadrature over the same finite path |
| deflection at infinity | Darwin (1959) elliptic-integral form |
| simultaneity at Andromeda | v·D/c² (SR), 0 (absolute time) |
| local speed of light (GR, static observer, rod of 10⁻³ r) | the same finite radial rod in closed form (→ c as the rod shrinks); the coordinate speed c(1 − rs/r) is shown next to it |
| flight time in flat runs; clock rate of the static station | marked "Самосогласованность": residuals of the solved equations, not independent checks; the flight time is summed from the solved interval (not a difference of absolute times, which at t ~ 4·10¹¹ s lost 3·10⁻⁸ of it: review UX-params P14 [error in earlier]), and the tolerance adds the round-off of the receiver's position taken at the absolute time, 4ε(\|v\|\|t\| + \|x\|)/(cΔt) |

## Approximations and limits (stated, not hidden)

* Space is a plane (x, y) + time; GR uses one spherical body at the origin (exact exterior Schwarzschild metric).
  Other objects have no gravity of their own (test bodies; Earth's own field is neglected).
* In GR runs the space map uses Schwarzschild coordinates; an observer's own frame (simultaneity slices of a moving
  observer) is available only in flat runs; GR slices are the static ones (t = const).
* The time-of-flight apparatus exists only in flat runs; in GR the speed of light is measured locally by a static
  observer with a short radial rod (round trip over exact geodesics).
* An apparatus is re-assembled after a boost (an instant change of velocity of an extended rigid rod is not
  defined). **This is an explicit idealisation:** a new mirror B′ is taken to be at rest at L₀ in the new frame from
  the boost on, as if prepared in advance (it is not a causal process); the old mirror goes on inertially, light
  already sent goes on, and measurements under way are completed with the readings already taken (a round trip in
  which A changed velocity has no closed-form reference). The re-synchronisation by light then takes real time.
* In GR a boost sets a constant **coordinate** velocity in Schwarzschild coordinates (a powered motion, not a free
  fall); the local speed seen by a static observer is (v_r/f, v_t/√f). A boost whose straight path would cross the
  body, or would become faster than local light, is refused with the reason.
* Arrival texts in GR give Schwarzschild coordinate time; the receiver's own clock reading is given next to it.
* Emission theory: a moving mirror re-emits light at c relative to itself (one of the historical variants).
* Earth keeps its prescribed Kepler orbit when the gravity of light is switched off.
* In an observer's frame the slice "now" reaches into the lab future, which the run has not computed yet: those
  parts are drawn faded and labelled (an action may still change them); events planned in the initial data are shown
  in advance as hollow markers.
* Receivers inside the photon sphere (r ≤ 1.5 rs) get no arrival events (the run says so).
* The ether is at rest in the lab frame; Newtonian corpuscles leave a static source with speed √(c² + 2GM/r₀)
  (speed c far away).
* Drawn polylines store a vertex at every 0.25° change of direction (or 64 steps); event times never come from them.

Open items: `../../STATUS.md`, "V. Visualizations — open items".

## Tests

`tests/test_v01_physics.py` (Docker: `docker compose -f visualizations/docker/docker-compose.yml run --rm viz-test`):
Lorentz matrices preserve the metric; aberrated light keeps speed c; quadrature deflection = Darwin (1e-10); weak
field 2rs/b + 15π/16 (rs/b)²; radial time; symmetric lens gives two simultaneous images; every RK vertex lies on the
exact geodesic (time to 1e-9); capture below b_c; Kepler crossing = RK corpuscle; Newtonian half deflection; every
preset runs and all its checks agree; SR measured c for all observers; round trip and re-synchronisation after a
boost; Michelson–Morley arms in the ether; Doppler and gravitational redshift trains; Andromeda offsets ±4.264 d;
Sun–Earth light time and Shapiro excess; events are revealed only when time reaches them; one changed law is
completed by the world, two incompatible ones refused; walkers faster than light refused; a flash inside a rod is
not a speed (the flagged flashes are exactly those between the ends, by positions); flight times far from t = 0 keep
their precision (negative control: the old difference fails).

## Sources of the reference formulas

Darwin, C., Proc. R. Soc. A 249, 180 (1959), doi:10.1098/rspa.1959.0015 (exact Schwarzschild deflection);
IAU 2012 Resolution B2 (au, via scipy.constants); IAU 2015 Resolution B3, arXiv:1510.07674 (nominal R☉ = 6.957×10⁸ m,
(GM)☉ = 1.3271244×10²⁰ m³ s⁻², R⊕ = 6.3781×10⁶ m, (GM)⊕ = 3.986004×10¹⁴ m³ s⁻²; values grepped from the text
2026-10-22); standard special relativity for Doppler, aberration and simultaneity; Soldner (1801) for the Newtonian
deflection 2GM/(c²b). Bibliographic data checked on Crossref 2026-10-22.
