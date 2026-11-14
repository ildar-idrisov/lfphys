# p01 — the gravity laboratory (space and gravity)

**English** | [Русский](README.ru.md)

A laboratory section (plan P15.1; framework P15.0: `../RULES.md` §6). The owner's words (2026-10-28): «в плейграунде
можно добавлять в мир разные объекты, менять параметры, смотреть за их изменением и взаимодействием, все должно быть не
задано заранее, а просчитываться в реалтайме, чтобы можно было задать комбинацию и силумировать поведение например
черной дыры или исследовать гравитацию» ("in the playground one can add different objects to the world, change
parameters, watch how they change and interact; nothing should be set in advance, everything computed in real time, so
that one can set up a combination and simulate the behaviour of, for example, a black hole or study gravity"). The scene is built by hand from the palette, changed at any moment in the
inspector, saved to a file and started again from it; its record is the last minutes unless "● Keep the record".

## The laws of a world (one family of solvers and of conservation laws each; a change of the laws is a new world)

**Live** (review UX-ui U12): the collisions of Newtonian bodies (merge / pass) change at the current moment with the
world kept (``nbody.NBody.set_collisions``): to "pass through each other", bodies already touching pass on; to "merge (momentum
and mass conserved)", a pair
touching then merges at once (mass and momentum kept); the scene file takes the law in force.

**Masses as properties of the objects** (plan P16.1, batch LB1: the bench never restarts):

* **The Kerr–Newman hole is an object of its world** ("Kerr–Newman black hole", the last object of the scene; a world
  always has one, made from the world's parameters when the scene has none; it cannot be removed (✕ and Delete are refused; the
  API's scene command `clear` empties the scene but keeps the hole; the player has no clear-scene button) — nor doubled). Its **mass** changed at the current moment is **a change of units**: the metric is G = c = M
  = 1, so every body keeps its state in units of M (place, momentum, E, L, K) and the world's seconds per unit of M
  change from then on (``Clock``: the geometric time goes on from where it is); proper times (``Geodesics.
  rescale_proper_time``) and the observers' clocks are kept in seconds; lengths in metres scale with M (a body at r = 6 M
  is twice as far in kilometres after M × 2). The event says so. It is not a mass that changed under the bodies (no
  established dynamics for that); it is the same solution read for another mass — after Δs seconds the bodies are where
  a world that kept the old M has them after Δs·M₀/M (test).
* Its **spin and charge** change only as a declared **"what if" model** (recommended over refusing: it keeps the bench
  running and is flagged everywhere): no established dynamics changes a metric under moving bodies. The rule is the
  engine's declared alternative `lfphys.theories.alternatives.kn_change_whatif` (its ABOUT, conflicts and tests; listed
  in "Physics of this world"; review LB1-physics P5): each body keeps its Boyer–Lindquist coordinates (r, θ, φ), its proper
  time and the momentum its local ZAMO measures (the frame energy from the mass shell, so its ZAMO-measured velocity is
  kept with no limit below c — a body falling at γ ≈ 22 near the horizon keeps γ; before, speeds above 0.999 c were cut
  to it without a word [error in earlier], review P6), a ray its direction and its ZAMO-measured frequency (before, it
  was reset to 1 [error in earlier]); E, L and Carter's K follow in the new metric (their drift accounting restarts).
  **The rule depends on the coordinates**: BL coordinates of different (a, Q) do not label the same physical places (at
  the same r the circumferential radius, the distance to the horizon and the area of the r-sphere change), and keeping
  the circumferential radius, or E, L and K, would be equally defensible and give a different world. The event names
  the body whose E changed most (before → after), the largest change of the circumferential radius at the bodies, and
  the largest γ kept; the approximations say "“WHAT IF” MODEL" with the module's name. Refused (the world as it was) when a body
  or a ray would be inside the new capture radius, a static observer inside the new ergosurface, a circular one inside
  the new ISCO, any observer inside the new horizon. A captured body stays captured (at r₊ + 10⁻⁴ of the new hole if
  that is outside where it was stopped).
* **The binary's total mass is a property of the binary** (its parameter "Total mass m, M☉"; the world's "Total mass of a
  new binary, M☉" only gives the default): a change of the mass alone is a change of units G = c = m = 1 — the orbit
  goes on in units of m, its accumulated phase too; the waves' frequency (∝ 1/m) and their strain at a detector (∝ m)
  follow at once; any other parameter starts the binary anew as before.

Measured latency (CPU, the whole command, 2026-11-11): the hole's mass 1 ms, its spin "what if" 0.1 s (the preset
"Near a black hole (a = 0.9): …"), the binary's mass under 1 ms, a Newtonian throw 1.4 ms; in the browser the event is shown 0.07–0.12 s
after the command.

The laws (Newton / PN binary / Kerr–Newman) stay new worlds; "carry the scene over" carries over what makes sense
(``prepare_scene``): Newton → Kerr–Newman: the most massive Newtonian hole becomes the hole (its mass, the new world's
spin and charge); Kerr–Newman → Newton: the hole becomes a Newtonian hole at the origin; the PN binary → Newton: its two
bodies as Newtonian holes (masses m₁, m₂, positions and velocities about the Newtonian centre of mass); Newton → PN: the
two most massive bodies as the binary when their separation lies in its range (8 … 2000 G m/c²: an au is ~10⁶ of it,
so practically never). The rest is listed in a notice with the reason (the scales do not meet; light, clocks and wave
detectors have no counterpart).

Within the same laws (review LB1-framework F5): Newtonian bodies and the binary carry their state (positions,
velocities, masses; the binary's orbit); Kerr–Newman bodies and rays carry theirs in units of M with the metric they were
in (`object_state` holds a, Q and M). A new hole of another mass only: the same state in units of M (a change of units;
proper times and observers' clocks kept in seconds); of another spin or charge: each body starts where it was (the same
r, θ, φ) with the momentum its local ZAMO measured (energy from the mass shell; ZAMO velocity kept to 1e-12), E, L and
K new — the new world's initial condition, not a change under moving bodies; a body whose state lies under the new
horizon starts anew from its parameters, or is refused when they lie there too. The carry-over's notice says each of
these per object.

| laws | objects (palette) | engine | what is checked live |
|---|---|---|---|
| **Newton: N bodies** | stars (M☉, R☉), planets (M⊕, R⊕), black holes as Newtonian masses with the Schwarzschild radius as a capture radius (an approximation, flagged; what touches a hole is absorbed and its radius stays the Schwarzschild radius of its mass), massless test bodies, field-and-tide probes | `core.gravity.nbody`: time-symmetric 4th-order Hermite with a shared adaptive step (close encounters), collisions merge (mass and momentum kept) or pass (a law of the world) | momentum (exact to rounding: pairwise forces), energy within three times the error a companion measures (the same interval again with half the accuracy parameter η: the step is ∝ √η, so the companion's error is about 4 times smaller and the run's error at most 4/3 of their difference), relative to kinetic + \|potential\| energy (the total may be 0), the companion's position error, angular momentum (information) |
| **GR: a binary** | one binary (mass ratio, start: quasi-circular or Newtonian ellipse, the orders of the equations, the separation where it stops), wave detectors (distance, inclination, azimuth) | `core.gravity.pn_binary` (1PN, 2PN, radiation reaction 2.5PN, 3.5PN; harmonic gauge), `core.gravity.gw_quadrupole` (h₊, h× at the detector) | the energy balance: the orbit's loss of the 2PN energy against the 1PN flux of a circular orbit in the invariant x = (mΩ)^(2/3) (Blanchet 2014 Eq. 314 without the tail), tolerance \|c₁\| x/(1 + c₁x), c₁ = −1247/336 − 35ν/12, x the largest of the run (the reaction series' ordering, below; a binary gaining energy fails it); for eccentric starts the loss against the quadrupole formula (information); without radiation reaction the 2PN energy conserved |
| **GR: near a Kerr–Newman black hole** | test bodies (circular equatorial orbits or a velocity measured by the ZAMO), light rays (a direction measured by the ZAMO), observers with clocks (static, ZAMO, on a circular orbit not inside the ISCO) | `core.gravity.kerr_newman` (geodesics in Boyer–Lindquist coordinates, the distant observer's time, each body's proper time; horizons, ergosurface, circular orbits, ISCO) | Carter's constant and the mass shell of every body (E and L exact: cyclic coordinates), each against its own drift budget: the sum over its accepted steps of the local error DOP853 allows, carried into K and μ² by their gradients (√6·rtol·Σ\|∂/∂yₖ\|·scaleₖ; it grows as 1/Δ near the horizon with the shell's terms), plus rounding; the observers' clock rates from the metric |

Units inside: au, years and solar masses (Newton); G = c = m = 1 with m the binary's mass (the binary); G = c = M = 1
(the hole). The world's time is in seconds everywhere, so the speed slider means the same in every world.

## Handles and instruments (plans P16.2, P16.3)

**Handles.** Newton: stars, planets, holes and test bodies are dragged (x, y, z: the velocity kept) and thrown (the
throw's velocity, in the scene's au per world second, becomes the body's own, written into its vx, vy, vz in km/s with
"set vx, vy, vz"; the player clamps a throw to 0.05 c and says so; the world accepts typed or thrown velocities up to 0.1 c —
Newtonian mechanics then errs by v²/c² ≤ 1 % — and refuses from 0.1 c; review LB1-physics P15); field probes are
dragged. Kerr–Newman: test bodies, rays
and observers are dragged in the drawing coordinates (x + i y = √(r² + a²) sin θ e^{iφ}, z = r cos θ: hidden parameters x,
y, z turned into r, θ, φ; a circular orbit or observer goes to the equator under the point; under the horizon refused);
a body thrown starts with the ZAMO-measured velocity of the throw (the drawn velocity through the inverse Jacobian of
the drawing map into dr/dt, dθ/dt, dφ/dt, then the ZAMO's frame; 0.99 c and more refused). The throw's limit for the
player (`velocity_max`, review LB1-p02-ux X4): half the speed of light in the drawing coordinates, 0.5 G M/c² per
G M/c³ (the hidden parameter `tv_max`, in (G M/c²)/s, set from the hole's mass and renewed when it changes), so a brisk
flick gives a quarter of c; near the hole the ZAMO-measured speed of the same drawn velocity is larger (by 1/α), and a
throw at 0.99 c or more by it is still refused with the advice to lower the throw scale. The hole sits at the origin.
The binary sits at its centre of mass (no handle). Every frame carries `at[id]` for every positioned object.

**Measurables** (`measurables()`, every frame's `meas`, `meas_note` for what is undefined, `measure()` for the sweeps):
Newton — the system's energy (J) and angular momentum (kg·m²/s) and their drifts since the scene's last change; per
body its distance to the chosen reference (its parameter "Instruments: distance to": the most massive other body, the
centre of mass, the origin), its speed (km/s) and its osculating two-body elements about the most massive other body
(a in au, e, the period in years, named in the quantity's label; undefined when unbound); per probe g and the tidal stretch. Kerr–Newman — the largest
drift of Carter's K and of the mass shell; per body r (G M/c² and km), its ZAMO-measured speed, E, L, the turning points'
semi-axis (r_p + r_a)/2 and eccentricity (r_a − r_p)/(r_a + r_p) (the roots of the radial potential R(r) = P² − Δ(K + r²)
around r), the radial period measured between two periapsis passages (p_r from − to +; the passages kept in world
seconds as they happen and cleared when the hole's mass, spin or charge changes — before, passages recorded in units
of M were read with the new seconds per M, and the "measured" period doubled at a mass change without a new passage
[error in earlier], review LB1-physics P10); per observer its clock and its
rate. The binary — r (km and G m/c²), the accumulated orbital phase (the angle swept, summed between the trail's points
at most ~10° apart), the waves' frequency, the osculating eccentricity, E/μ, the energy lost since the start, |x × v|;
per detector h₊ and h×.

## What the player shows

The 3-D scene (spin axis or orbital angular momentum up): the bodies as spheres (drawn at least 0.6 % of the scene so
that a star much smaller than its orbit stays visible), their trails (sent as accumulating messages; a segment of the
record starts with full trails), the hole's horizon, ergosurface and equatorial circular orbits; the panels of the
laboratory (palette, objects, inspector with the selected object's state "now:", probes, the scene's changes, the
file, the record's window). A Newtonian black hole is drawn light (its Schwarzschild radius is far below a pixel) with
a marker and its name (review UX-ui U18: near-black on the dark scene, the hole the stars orbit could not be found).

**Trails are the computed orbits, smooth at any speed** (review UX-ui U2, UX-3d A13 [error in earlier]: one point per
frame joined by chords drew Mercury at the default speed as a pentagon, 4.8 points per orbit, and the Earth at ×10 as
a line). The solvers offer points of their own continuous output — the N-body Hermite steps' continuous output on a
grid inside every step (``nbody.Samples``: the grid belongs to the step, so the points do not depend on how time is
sliced), the binary's dense solution, the Kerr geodesics in sub-steps sized by each body's measured turn — at most 10°
of turn of the direction of motion (and 10 % of speed) apart; a trail keeps a point (position, velocity, time) when the
direction has turned by more than 20° since the last kept one (or the speed changed by 20 %), and the view draws each
piece between two kept points as the cubic Hermite curve of their positions and velocities in chords of at most 2° of
turn, the last piece to the body's state in the frame shown. On a circle the curve is off by r θ⁴/384 = 3.9·10⁻⁵ r at
θ = 20° and a 2° chord by 1.5·10⁻⁴ r: under 2·10⁻⁴ of the local radius of curvature, below 0.25 px for any orbit up to
~1200 px in radius on the screen (measured in the tests against the solver's dense trajectory at ×1 and ×10:
≤ 2.5·10⁻⁴ r; one point per frame was off by > 0.1 r). A body's state jumping (an edit, a merger) breaks its trail
there; a body that merged keeps its trail (the latest 32 such). At a very high speed a trail gets at most 300 points
per frame (the latest, after a break).

**Placing** (review UX-ui U4): a palette body goes where the form or a click puts it; if another body is there or
within three sums of their radii (or the capture radius of a hole), or a circular orbit has no plane there, it goes to
the first free point along +x (steps of an eighth of the scene) and a toast says so; a copy of a massive body goes next
to the original with its velocity (before, a second star, a copy, a hole on the Sun were refused, or a star landed in the
Sun and merged unseen, or a hole swallowed the Sun). Every merger is a toast too, with the time since the body was
added when that is under a year. The Newtonian world advances in chunks of 16 integrator steps, so a high speed lags
("actual: …" below the chosen speed) instead of stalling a frame (review UX-ui U5).

## Approximations and limits

* Newton: point masses (the radius only for collisions), no relativity; a "black hole" here is a Newtonian mass. A
  body "on a circular orbit" is on the two-body circle with the others (their mass at their centre of mass): the
  others get the reflex and the system's centre of mass keeps its velocity (before review B6-G6 the start was circular
  only for a test body: e = m/(M + m), and the scene drifted [error in earlier]). A copy of a massive body at the
  current moment would lie on the original and is refused. The frame grows with the bodies up to 64 times the scene's
  size at its last change: a body flung out leaves it.
* The binary: no spins, no tides; the waveform is the leading quadrupole of the computed orbit; the 1.5PN tail of the
  flux is absent from local equations of motion. **Where the full equations end** (review B6-G1): their radiation
  reaction (2.5PN + 3.5PN, harmonic gauge) is accurate to relative 1PN; its remainder against the 1PN flux grows as
  −35.5 x² and beyond (the 2PN-relative reaction, Gopakumar, Iyer & Iyer 1997, is not in the engine), cancels the
  reaction at r ≈ 9.1 G m/c² for every mass ratio, and inside it the orbit gains energy: the default binary stalled
  near r ≈ 9 and flew apart instead of reaching r_stop = 6, while the balance check (tolerance 100 x², above 1 for
  r < 10) passed [error in earlier]. Since then the run computes, at the binary's start, the separation where the
  remainder equals the 1PN correction the reaction carries (the first neglected order larger than the last kept one:
  r = 10.59 for q = 1, 11.69 for q = 0.25, 13.01 for q = 0.05) and stops there with an event that says why; the
  inspiral from r₀ = 20 (q = 1) takes 2·10⁴ G m/c³. The last orbits, the plunge and the merger are not shown: no PN
  equation of motion in the engine describes them (`../../STATUS.md` V34). Closer starts or stops are possible with
  the orders "Newton + radiation reaction 2.5PN" (self-consistent, not accurate there).
* The hole: a fixed background (test bodies have no field and no charge); bodies are stopped at r₊ + 10⁻⁴ (the
  distant observer never sees them cross); a body that leaves beyond 2000 G M/c² is no longer followed.
* A scene file keeps the objects with their parameters and dynamic state: Newtonian bodies' positions, velocities,
  masses and radii (after a merger the kept body's parameters show the merged mass and radius where their ranges
  allow); Kerr bodies' and rays' momenta, proper times, status (captured, escaped) and drift accounting; observers'
  clock readings and azimuths; the binary's state and status (stopped). Before review B6-G11 a captured body or a
  stopped binary made the file unloadable and the observers' clocks restarted at 0 [error in earlier]. The
  integrator's internal step history is not part of it (a world started from a file is a new start at that state).
* Kerr: a change of a body's or ray's start (place, velocity, direction) starts it anew at the current moment; a change
  of colour does not; an observer moved keeps its clock and its azimuth (unless the azimuth was changed).
* Open items: `../../STATUS.md`.

## Tests

`tests/test_p01_lab.py` (LB1): the hole an object of every Kerr–Newman world (not removable, not doubled, kept by a
`clear`); its mass as a change of units (state untouched, proper times and clocks continuous in seconds, the evolution
after Δs that of the unchanged world after Δs/2); spin and charge as the flagged "what if" (place, proper time and ZAMO
velocity kept to round-off, E and L recomputed, "“WHAT IF” MODEL" and the engine module in the approximations and the event, the
checks passing, a body under the new horizon refused with the world as it was, a body near the horizon keeping γ, the
radial period cleared at a change of the hole; the rule itself is tested in the engine,
`lfphys/tests/test_kn_change_whatif.py`); the binary's mass (no restart, the phase going on, the
frequency halved and the strain doubled); the Newtonian drag (velocity kept) and throw (velocity set, 0.1 c refused);
the Kerr drag (to the point, a circular orbit to the equator) and throw (the drawn velocity right after = the throw's,
1e-9; the throw limit declared and renewed with the hole's mass); the measurables (the Earth's a, e and Kepler's period, the energy drift; a far Kerr orbit's measured radial period
against Kepler's within 2 %; the binary's phase against ∫Ω dt); carry-over across the laws; a Kerr world with the mass,
the spin, a drag and a throw rebuilt by replay bit for bit.

`tests/test_p01_gravity.py`: every preset builds and keeps its conservation laws; Mercury's drawn orbit within
2.5·10⁻⁴ of its radius of the dense computed trajectory at ×1 and ×10 (negative control: one point per frame, > 0.1),
every mode's trail points within the turn limit; collisions changed at the current moment with the world kept; palette
bodies at free spots, copies next to their originals, mergers toasted (every check message is read, not
the last of each); a body "on a circular orbit" is on the two-body circle for any mass (equal stars, a planet off the
plane; Kepler's 29.78 km/s at 1 au), the preset with five planets does not drift; a change at the current moment,
then a fall into the Sun merges the two bodies (mass and momentum kept, the scene loses one); the scene file restores
the bodies exactly, also after a merger, a capture and a stop, with the observers' clocks; the binary loses energy
against the waves' flux, runs to where its reaction series ends and stops there (controls: without that stop, and with
a 3.5PN term 1.5 times too strong, the balance fails), the reaction's work D against a short integration; its
detector's strain matches the circular-orbit quadrupole amplitudes; without radiation reaction the energy is
conserved; a refused copy leaves the engine as it was; the energy check of a world whose energy is 0; a Newtonian
hole keeps its Schwarzschild radius after swallowing a star; the clocks of a static observer (√(1 − 2r/Σ)) and of a
circular orbit (Bardeen, Press & Teukolsky 1972) against their closed forms, a falling body captured with every check
passing, a circular orbit kept, an observer added later placed where it was put, a colour change that restarts
nothing, a circular observer refused inside the ISCO; the Newtonian frame stops growing when a body is flung out;
Burrau's three bodies through their first close encounters. The shared tests continue a world from its checkpoint
byte for byte (`../tests/test_checkpoint.py`) and rebuild it by replay (`../tests/test_restore.py`).
