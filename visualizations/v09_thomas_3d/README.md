# v09 — Thomas–Wigner precession in 3-D

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.1, on P9 and P10) and the second world of the player's 3-D
environment (`../RULES.md` §2.10). A craft starts at rest and flies a manoeuvre; its gyroscopes are carried without
rotation; when it is back at rest they are turned. The run computes by how much, in SO(3) and in SU(2), how much fuel
it took, and compares both with closed forms and with the isoperimetric bound of the hyperbolic plane.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.spin_transport` | core | the manoeuvre: Fermi–Walker transport of the gyroscope frame along burns (thrust of fixed direction in the craft's frame) and turns (thrust turning at a constant rate about an axis fixed in the craft's frame), each piece exact by matrix exponentials in the Lorentz group and, independently, in SL(2, C); proper and lab time, position, velocity, fuel; the holonomy; velocity-space geometry (distances, angles, Gauss–Bonnet areas, circles, the isoperimetric bound) |
| `core.lorentz` | core | boosts, the decomposition into boost and rotation, velocity addition, the Thomas–Wigner rotation (matrices and closed form), SO(3) axis–angle, SU(2) axis–angle |
| `core.geometry` | core | the slice planes (`Plane.horizontal`, `plane_cut`) |

The apparatus (`engine/loops.py`, no physics of its own): the loops built from the world's parameters, their
references, the field of three-burn loops.

## The physics

* **Velocity space.** The velocities of a body form the hyperbolic space of curvature −1 in rapidity units; the scene
  draws it as the ball of β = v/c (the Beltrami–Klein picture: a burn of fixed direction runs along a straight
  chord; light is the boundary sphere |β| = 1). The fuel of a manoeuvre is the length of its path there: the sum of
  the burns' rapidities, ∫|a| dτ / c.
* **Fermi–Walker transport.** The gyroscope frame M(τ) (its basis in lab coordinates) obeys dM/dτ = M Ξ(τ), Ξ the
  boost generator of the proper acceleration in the craft's own frame. A burn is exp(η K·n); a turn (thrust direction
  a(s) = R(ω, κ s) a₀) is exp(s(K·a₀ + κ J·ω)) R(ω, −κ s) — exact (`spin_transport._advance`). The same pieces in
  SL(2, C) carry the spinor.
* **Holonomy.** Back at rest the gyroscope axes are turned by R (Thomas precession). For a loop in one plane of
  velocity space R is a rotation about that plane's normal by the enclosed area A, against the sense of the loop
  (Gauss–Bonnet; Aravind, Am. J. Phys. 65, 634 (1997)); uniform circular motion at γ gives 2π(γ − 1) per revolution
  (Thomas, 1927). SU(2) keeps the angle mod 4π: a loop of area 2π leaves the gyroscopes as they were and the spinor
  with the sign −1.
* **The isoperimetric bound.** Among closed curves of length L in the hyperbolic plane the circle encloses the most:
  L² ≥ 4πA + A², i.e. A ≤ √(4π² + L²) − 2π (Osserman, Bull. AMS 84, 1182 (1978), eq. (4.23), K = −1; equality only
  for circles). For planar loops this bounds the rotation per fuel; for loops that leave every plane it is shown as a
  comparison line only — no bound for them is claimed here.

## The loops

| loop | what | reference |
|---|---|---|
| `thomas` | out to rapidity ρ, uniform circular motion (`turns` revolutions), back | Thomas: 2π(γ − 1) per revolution, γ = cosh ρ |
| `circle` | the circle of velocity space of radius ρ through rest (thrust turning at coth ρ per unit rapidity from the start) | the circle's area 2π(cosh ρ − 1); equality in the isoperimetric bound |
| `triangle` | burn ρ along e₁, burn ρ turned by α, back to rest | the Wigner angle of the two boosts = the triangle's area (L'Huilier from its sides) |
| `polygon` | the regular n-gon through rest with circumradius ρ (burns) | (n − 2)π − n α, cosh ρ = cot(π/n) cot(α/2) |
| `crown` | the n-gon with its vertices lifted alternately by ±χ out of the plane | none: the two representations agree; at χ = 0 the polygon |
| `helix` | thrust turning about an axis tilted by χ (a helix of velocity space), then back | none; at χ = 0 the circle |
| `seam` | a tennis-ball seam (latitude χ sin 2t) on the velocity-space sphere of radius ρ through rest, by 96 burns | none; at χ = 0 the regular 96-gon; the smooth seam is the limit (the difference to 192 burns is shown) |

The loop's plane is set by its normal (θ, φ); everything is checked in any orientation.

## The scene

* **Velocity space**: the light sphere |β| = 1, rest, the path (revealed as lab time runs), the gyroscope triads along
  it (red, green, blue: the gyroscope axes 1–3 relative to the frame a single boost from rest would reach), the craft
  with its gyroscopes, its spin (yellow: the axis that starts along e₁) and its thrust (orange), the rotation axis
  when the loop closes; the vertices of polygons; the **field** (a volume) and the rotation axes of that field
  (arrows, off at start). Every element switches off on its own.
* **The field**: for every velocity w of the ball, the gyroscopes' rotation θ after the loop rest → u → w → rest
  (u along e₁ at rapidity η_u): the Thomas–Wigner angle of the boosts u and v′ (w seen from u), computed by the
  engine's matrices at every point; or θ divided by the isoperimetric bound at that loop's fuel (always below 1:
  triangles are planar). Blank where |β| > 0.999.
* **Slices**: up to three planes of any orientation through the ball (the shared environment: gizmo, parameters,
  kept in a new world, "auto-shift along the normal" optional — its speed in c per year of world time). Each is computed by the run at
  160 × 160 points for its plane and checked at three of its points against the triangle's area by Gauss–Bonnet.
* **Ordinary space**: the craft's trajectory (light-years), the gyroscope triads along it, the craft, the rotation
  axis at the end. No field, so no slices. The region starts at the input scale c²/a and doubles whenever the revealed
  path nears its edge (a `box` message), so the framing never shows where the craft will go.
* **What is shown when** (RULES.md §2.2): at the start only the programme (the pieces, the fuel they plan, the loop's
  closed form as a description); while time runs the path, the triads, the current t, τ, β, γ and the largest γ so
  far; at the closure the rotation (SO(3), SU(2)), the accumulated angle, the duration in lab and proper time, the
  largest γ, the comparison with the bound, and the checks.
* Time: the world clock counts lab seconds (the manoeuvre takes years at 1 g; the player shows years); the default
  speed comes from the programme's own clock (fuel / thrust, an input): about 20 s of play per year of proper time
  per (c/a), longer when γ is large.

## Checks

| id | quantity | reference | tolerance |
|---|---|---|---|
| `field_exact` | θ of the field at 300 points of the volume | Gauss–Bonnet: the triangle's area from its sides (L'Huilier) | 64 ε γ_u² γ_w² at each point (the matrices' round-off) |
| `plane_exact_N` | θ at three points of slice N | the same | the same |
| `roundoff` | the round-off of this run, measured: the disagreement of the two independent representations (4 × 4 Lorentz matrices by Padé exponentials; SL(2, C) by closed-form 2 × 2 exponentials) and the final state's distance from the Lorentz group | an alarm level, empirical (not derived): 1e-11 cosh²(η_max) (pieces + 1 + Σ s·max(1, κ)) — exponentials with entries up to cosh(η_max), exponents of norm s·max(1, κ) | the alarm (measured ≥ 46× below it over 640 random worlds of the schema) |
| `closed` | \|β\| at the end | 0 | 8 × the measured round-off |
| `holonomy` | the SO(3) rotation (planar loops: against R(n, −A)) | the loop's closed form above | 8 × the measured round-off (+ the reference's own rounding) |
| `holonomy_accumulated` | (planar loops) the accumulated angle computed along the run: the gyroscopes' angle about the loop's normal, unwrapped over the samples (it may exceed 2π) | the area (the closed form above) | the same |
| `holonomy_su2` | (planar loops) the spinor against exp(+iA σ·n/2) — its sign after every 2π | the same | the same |
| `fuel_bound` | rotation per the planar bound at the same fuel: the accumulated angle of a planar loop; for a non-planar loop the SU(2) angle of one loop (its first flight) at that loop's fuel | information | — |
| `seam_convergence` | the seam by 96 against 192 burns | information | — |

## Approximations and limits

* Special relativity, flat space-time; the thrust is given in the craft's frame, of constant magnitude (it sets only
  the time and length scales); the craft is a point with ideal gyroscopes (no torque).
* The burns of polygons (triangle, polygon, crown, seam) are built in extended precision (64-bit mantissa) and rounded
  to float64 as they are flown: built in float64, the next vertex seen from the comoving frame lost up to ε cosh²(η)
  and bent large loops in tilted planes out of their plane by more than the flight's round-off (review B2-1). So the
  measured round-off of the flight bounds the comparisons.
* A manoeuvre that reaches rapidity above 7 (γ ≈ 550) is refused: float64 would lose the rotation there (a helix with
  a nearly axial thrust axis runs off towards light). At rapidity 6 with six repetitions the measured round-off is
  ~5e-7 (shown in `roundoff`).
* The seam is a polygon of 96 burns (a manoeuvre in its own right); the smooth seam is its limit, the difference shown.
* The isoperimetric bound is a theorem for planar loops; for the others it is a comparison line.
* The world clock counts seconds; the speed of a plane's auto-shift is in c per year of world time.

## Tests

`tests/test_v09_thomas3d.py`: every preset builds, closes and passes its checks; nothing about the result appears
before the closure and the path is revealed only up to the run's time; planar loops (Thomas's, the circle, the
pentagon) in three orientations against their closed forms in SO(3) and SU(2); the edges of the schema (ρ = 3, six
repetitions, 24 sides, χ = 80°) and the smallest (ρ = 0.05): refused with the reason or passing, the measured
round-off far below the alarm, repeated loops through rest between the repetitions; large triangles and polygons
(ρ 2 – 3, repeated) in tilted planes; the lab box grows only with the revealed path; nothing of the result (nor the
duration, the proper time at the end, the largest γ) in the header; the rotation per fuel of a repeated non-planar
loop is that of one loop; the triangle is the Wigner rotation
(matrices and the closed form); the double cover (area 2π: gyroscopes back, spinor −1; twice: spinor back); crown,
helix and seam at χ = 0 are planar loops, and out of the plane their axis leaves the normal; the seam converges; the
Thomas loop in ordinary space is uniform circular motion (speed tanh ρ, radius sinh²ρ c²/a) after hyperbolic motion;
the field and three slices against Gauss–Bonnet, the ratio below 1; planes kept in a new world, auto-shifted slices coarse, none
in ordinary space; frames carry an orthonormal gyroscope frame. The engine's own tests: `../../lfphys/tests/test_lorentz_3d.py`,
`test_spin_transport.py`. The page: headless Chromium (WebGL by SwiftShader), presets thomas, crown, spin_flip, lab and
v08's gauss after the shared environment was factored out (2026-10-27, no page errors).

Open items: `../../STATUS.md`.
