# r12 — the double slit with long slits, in 3-D: the exact Schrödinger equation and Bohm trajectories

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.4, on P6 and P10). A wave packet of a massive particle runs at a
plate with two slits and on to a detecting screen. The run solves the time-dependent Schrödinger equation on the whole
plane of the experiment — no paraxial approximation, no Kirchhoff boundary values: the plate is a wall of finite
height and thickness, and the wave reflects from it, runs through the slits as through short channels and spreads to
any angle. An ensemble of particles follows the Bohm trajectories of the same wave. The set-up is live: a slit can be
closed, a which-path mark in slit B turned (the particle's spin, or an observer: a two-level which-path detector at
slit B), an Aharonov–Bohm flux set between the slits, the plate itself changed (the slits' width and distance, its
thickness and height); each change acts from its moment on.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.quantum.schrodinger_nd` | core | the wave on the grid: Strang split operator (spectral kinetic step; the flux tube's vector potential by gauge phases along the axes; the spin's coupling by an exact 2 × 2 exponential per point), the absorbing layers and the probability they take point by point, the current through the screen's face, ψ and ∇ψ at the particles |
| `core.quantum.transfer` | core | the reflection and leak of the absorbing layers (stationary transfer matrices of −iW) |
| `core.quantum.particles` | core | the particle's de Broglie wavelength, energy, speed (the physical scale) |
| `core.backend` | core | where the wave is stepped: GPU 0 from 128×128 points (measured), the CPU otherwise |
| `theories.interpretations.bohm` | interpretation | the trajectories: dr/dt = (ħ/m) Im(ψ†∇ψ)/(ψ†ψ) − (q/m)A, error-controlled Dormand–Prince 5(4) steps per particle |
| `theories.approx.paraxial`, `theories.approx.kirchhoff` | approximation | the patterns of the approximate theories for the comparison at the end (information) |

The apparatus (`engine/apparatus.py`, no physics of its own): the plate, the slits' channels, the absorbers and their
regions, the packet, the mark's coupling, the references.

## The model

* **Units.** Lengths in the de Broglie wavelength λ of the packet's mean momentum, ħ = m = 1: k₀ = 2π, v₀ = 2π λ per
  unit time, E₀ = 2π². One unit of time is mλ²/ħ of the chosen particle (an electron at λ = 100 pm: 8.6·10⁻¹⁷ s); the
  world clock counts seconds.
* **The plane and the third dimension.** The slits are long along y, so nothing depends on y: the Schrödinger
  equation is solved in the plane (x, z), and a packet localised in y stays the exact product
  ψ(x, y, z, t) = ψ(x, z, t)·η(y, t), η a free Gaussian of width σy (world parameter, zero mean momentum; closed form,
  `core.quantum.schrodinger1d.FreeGaussians`). Its Bohm trajectories move along y exactly as y₀·σy(t)/σy
  (`bohm.gaussian_trajectory`), independently of x and z; their y starts are drawn from |η|² after the x, z starts
  (which therefore do not depend on σy). Since the owner's correction of 2026-10-28 («в 3D моделируется все, но
  отображается только в виде плоскости» — "everything is modelled in 3-D, but shown only as a plane") the run
  sends the third dimension and the scene draws it: |η(y, t)|² on 48 points across the scene with every image of
  the wave (the view draws the volume |ψ(x, z)|²|η(y)|², the outer product, ray-marched), the particles' and
  trajectories' y, the hits' y, and the screen as P(x, y) = Σ_t J(x, t)|η(y, t)|² dt on 48 bins of y (the flux of the product state through the screen's face). The scene's y
  extent is a set-up estimate: four widths of η at twice the time the wave needs to cross the window at the mean speed
  (or a quarter of the window's length, whichever is larger). Before, the scene showed only the plane y = 0 (it is
  still a layer, off by default, and the window on the right).
* **The plate.** A potential V₀ (in units of E₀) where the plate is solid: thickness w around z = 0, slits of width a at
  x = ∓d/2 (A at −d/2, B at +d/2); its edges rise over a stated length (the world parameter "Width of the wall's and the mark field's edges, λ", default
  0.2 λ, a tanh profile), the same on every grid and never narrower than the grid step (refused otherwise). Until the
  review the edges were one grid step wide, so the grid choice changed the wall itself: the pattern moved by 10–20 % of
  its peak between λ/6 and λ/8 (review B3-2). The wave decays in the wall as e^(−κs), κ = √(2(V₀ − E₀)); the grid
  resolves it (checked).
* **The packet.** A Gaussian, spread σx across and σz along the beam, mean wavenumber k₀ along z, starting 4.5σz before
  the plate (its tail at the plate < 10⁻⁴); with a flux, multiplied by the gauge factor exp(iqΛ) (Λ = ∫A·dl from its
  centre), so that its kinetic momentum is ħk₀ along z in every gauge (without it the same Gaussian is another state).
* **Detectors.** Absorbing layers W = 2E₀ (s/6λ)²: the screen (from 4λ behind its face z = L on), the source side
  (what the plate reflects) and both sides (what flies past the screen). "reflected by the plate" is what is absorbed before the
  plate's middle (z < 0), whichever layer takes it (review B3-13). The screen's face z = L is a sample of every grid.
  The screen's pattern is the probability that flows through its face, ∫ j_z(x, L) dt (the current by a 32nd-order
  centred difference: error (16!)²/33!·(k dz)³² ≤ 3·10⁻⁶ at the top of a packet's spectrum on the coarse grid λ/5);
  the layers' probability is accumulated point by point (norm + absorbed = 1 to round-off). The 4λ of free space
  between the face and the layer (B4, found with r13): W'' of the layer jumps at its inner face, so the wave is only
  C³ there, and a difference stencil centred on it errs by ~h⁴ — the flux of a free packet came out 1.2·10⁻⁴ too
  large at λ/5 when the layer began at the face; now the stencil (16 samples each side, 3.2λ at λ/5) lies in free
  space and the flux agrees with the exact free evolution to 3·10⁻⁶ (r13, `arr_flux_exact`). Order 16 lost ~10⁻³ at
  the top of the spectrum on λ/5.
* **The path mark and the observer.** The world parameter "Path mark in slit B" gives the wave a second component:
  * "the particle's spin: …" — the particle's own spin ½ (spin up along z). A coupling b·σ with b = b₀ e_y inside slit B's
    channel (edges as the wall's) turns the spin by θ = 2b₀w/(ħv₀) for the mean speed (b₀ set from θ). For an electron
    or a neutron this is a magnetic field in the slit (b = −μB); particles without spin ½ in the engine (⁴He, C₆₀) are
    refused this mark (review B3-7);
  * "an observer: a path detector at slit B (…)" (B4, the owner's request of 2026-10-28) — an external two-level which-path
    detector at slit B (Englert's model, as u32's detector qubit): the second component is the detector's state, which
    the same coupling turns by θ while the particle is in slit B. Any particle, also one without spin.

  θ itself is live ("Mark in slit B: turn θ, °"): 0 — the paths cannot be told apart, 180° — fully marked. Since B4
  (review B4-3) b₀ is calibrated on slit B's channel (`MarkCalibration`): the lowest transverse mode of the slit
  (the plate's profile across x, sinc-DVR) carries E⊥; the ±b₀ eigenstates of b·σ cross the plate's profile along z
  with (E⊥ ± b₀c_x)s(z), and their complex transmission amplitudes (`core.quantum.transfer.staircase_amplitudes`)
  differ by the phase arg(t₋/t₊), the rotation; b₀(θ) by interpolation. Until B4 b₀ came from the first-order
  θ = 2b₀w/(ħv₀) for a free particle, which turned the mark by ~1.2θ: the "residual visibility 0.25" at 180° was
  mostly this miscalibration [error in earlier]. What the calibration leaves: the higher transverse modes of a narrow
  slit and the speed spread (candidates for what remains). The run measures the share of the down component in the
  flux just behind slit B (information in `visibility`'s note): 0.86–0.93 at most in a slit of 1.5 λ, not 1, at any
  θ — the wave leaving the slit is not turned uniformly. The mark is computed, not imposed: what the coupling does to each part of the wave (its speed, the channel's modes, the
  potential steps ±b₀ at the ends) is in the result. The 3-D scene draws the mark as an orange box in slit B's channel
  (the observer, or the spin's field), more opaque the more the path is marked (0.12 + 0.5 sin²(θ/2)); the plane's
  window shades the same region.
* **The Aharonov–Bohm flux.** A tube of flux Φ inside the plate between the slits, with a Gaussian field profile of
  radius R = min(w, (d − a)/2)/6 (its field ≤ e⁻⁹ of the peak at the plate's faces): the wave never meets the field,
  only the vector potential. Charged particles only. A flux switched while the wave is on its way gives it the kick of
  the induced electric field (−qΔA at the moment of the change): the physics of switching a solenoid, computed.
* **Numerical error.** E₀ dt = 0.1 rad. A companion runs the same experiment alongside on a neighbouring grid with
  twice the time step: 1.2 times coarser, or 1.2 times finer when a coarser grid would not resolve the edges (the
  coarse grid's step is the default edge width); the largest difference of the two patterns on the screen (as
  densities, the companion's by a cubic spline) estimates the run's error with a margin (`numerics`: measured 4–6·10⁻⁴
  of the peak on λ/6, where the difference to λ/8 is 0.8–1.4·10⁻⁴). Until the review only the time step was measured
  (review B3-2).
* **Bohm trajectories.** N particles start at positions drawn from |ψ₀|² (seeded). Each pair of steps they move by RK4
  with ψ and ∇ψ interpolated from the grid (degree 8, the 9 samples around the nearest one: the stencils are mirror
  images, so a symmetric wave keeps v_x = 0 exactly on its axis; since review B6-Q1 around each particle's local
  wavevector, which removes the remainder of k d), ψ quadratic in time through the wave's three
  snapshots of the pair. Each particle has its own error-controlled steps (Dormand–Prince 5(4)): a step is accepted
  when its error estimate is at most 10⁻⁶ grid steps + 10⁻⁵ of the step's own displacement and the particle moved at
  most one grid step. A particle in smooth flow takes one step per pair; one circling a node of the wave (where Bohm's
  velocities grow without bound) takes as many as it needs and keeps the same relative accuracy on every turn (the
  2-D oscillator's vortex in `lfphys/tests/test_bohm_nd.py`: 30 turns at r = 0.05 with the radius kept to 10⁻⁴). A
  control of 100 particles is integrated four times more tightly in the same wave; the difference of their hits is the
  measured accuracy (`bohm_accuracy`, review B3-4; the former rule — sub-steps only when a particle outran one grid step
  per pair — left a few per cent of the trajectories unconverged). A particle is labelled by the slit through which
  it crosses z = 0 and stops at the screen's face (a hit), in the side layers or in the source-side layer.

## Live and world parameters (review UX-ui U12)

The owner (2026-11-04): «плейграунд должен быть больше похож на плейграунд, где я могу ставить эксперименты в рамках
одного мира, а не перезапускать его постоянно» ("a playground should be more like a playground, where I can set up
experiments within one world instead of restarting it all the time"). For every parameter: whether the engine applies it at the current
moment keeping the world, and what an edit does to the state — or why it stays a world parameter (a change of it starts
a new world in the same run, with the set-up in force carried over).

| parameter | | what an edit does to the state; or why it stays a world parameter |
|---|---|---|
| slit A, slit B open; the mark's turn θ; the flux Φ/Φ₀ | live | the potentials of the run and of the companion are rebuilt at the current moment (`SplitOperator.rebuild`); the wave is kept; a flux switched while the wave is on its way gives it the induced field's kick |
| slit width a, distance d, thickness w, wall height V₀ | **live** (U12) | the plate is rebuilt at the current moment inside the grid, window, screen and absorbers the world was built with (`_live_geometry`: the apparatus's plate for the new a, d, w; V₀ its height), for the run and the companion, with the mark's channel and its calibration (`MarkCalibration`) when the path is marked; the wave is kept as it is. The part of the wave that is where the potential (or the mark's field) changed by more than 10⁻⁶ E₀ feels the change at once — a sudden change of the Hamiltonian, its probability said in the event; the rest meets the new plate later. A change at t = 0 is the experiment with the new plate from the start (for V₀ bit for bit a world built with it; a, d, w keep the window built for the old ones). Refused in the owner's terms, the world unchanged: slits beyond the screen (d/2 + a/2 + 3 edge widths beyond its half-width), a plate whose faces come within 3 edge widths of the source's layer or of the screen, merged slits (a ≥ d, the rule of the world's construction). `grid_wall` is computed again for the new wall; the mark's share is measured anew behind the new plate. As for every live change after t = 0, the comparisons that assume one set-up for the whole run (`symmetry`, `no_crossing`, `visibility`, `ab_phase`, the approximate theories) are not made |
| edge width | world | the companion's grid is chosen from it when the world is built (1.2 times coarser only while that grid resolves the edges); a narrower edge later could leave the companion unable to resolve the wall, and its error estimate (`numerics`) would no longer hold |
| screen distance L | world | the grid's length, the screen's face (a sample of the grid), the screen's half-width (from L·tan θ) and the absorbers are built from it: a screen moved inside the window would mix two faces in the detectors' bookkeeping (`flux_absorbed`), and beyond it there is no grid |
| particle, λ | world | the packet in flight is this particle with this momentum; λ is the unit of every length of the computation, mλ²/ħ of its time |
| σx, σz, σy | world | the initial packet: the wave at t = 0, the Bohm starts drawn from it |
| path mark (none, spin, detector) | world | it decides whether the wave has one component or two: the engine's propagator does not turn a scalar wave into a spinor at a moment (`SplitOperator.rebuild` refuses it) |
| grid | world | regridding the wave is not in the engine |
| Bohm particles, tracks drawn | world | the ensemble is drawn from \|ψ₀\|² at the start; a particle added later would have no history (no slit, no start from ψ₀) |

## What is shown when

At the start: the plate, the screen, the packet (the wave in 3-D: the volume ψ(x, z)·η(y)), the particles at their
starts (in x, y, z). While time
runs: the wave (images every 16 pairs of steps, kept in the record, so that a viewer who scrolls back sees the wave of
that moment), the particles and their trajectories (colour: the slit), the hits on the screen and the pattern the flux
builds there; nothing is drawn on the screen while its accumulated probability is below 10⁻¹⁰ (round-off of either
sign, review B3-5). At the end (all probability absorbed, < 10⁻⁴ left): the fractions detected, reflected and lost,
the checks, and the approximate theories' patterns for comparison. Scrolled back, the plane's window and "Screen" show
that moment (review B3-10); the trajectories and the screen in the 3-D scene keep all that was revealed.

## Checks

| id | quantity | reference | tolerance |
|---|---|---|---|
| `grid_k` | k_max / k₀ of the grid | ≥ 2.4 (the packet's spectrum and the decay in the wall) | — |
| `grid_wall` | κ / k_max (the decay in the wall resolved) and V₀ < E_max of the grid | < 1 | — |
| `absorbers` | reflection and leak of the screen's layer over the packet's spectrum (k ∈ [0.9, 1.1] k₀), normal and at the screen's widest angle | transfer matrices | < 10⁻³ |
| `norm` | norm + absorbed − 1 | 0 | 10⁻⁹ |
| `numerics` | the pattern's numerical error: max difference of the densities, run against the companion (a neighbouring grid ×1.2, step ×2), in units of the peak | an estimate with a margin | < 1 % |
| `flux_absorbed` | ∫∫ j_z through the screen's face (all x) | the probability absorbed behind it (and left there) | the layers' reflection + 3 × `numerics` + what the face's own cells hold (half before, half beyond the face: 0 once the wave has gone) |
| `bohm_born` | Kolmogorov–Smirnov distance of the hits' x from the flux pattern | equivariance | 1.95/√n (99.9 %) |
| `bohm_fraction` | fraction of the particles on the screen | the flux into the screen | 3.3σ binomial |
| `bohm_accuracy` | the 95th percentile of the hits' difference between the ensemble and a control integrated four times more tightly (and the number whose fate differs) | the trajectories' integration error | 95 % < 0.05 λ, fates ≤ 2 % |
| `symmetry` | max |P(x) − P(−x)| (symmetric set-up) | 0 | 10⁻⁸ (the grid is symmetric in x) |
| `symmetry_ab` | the same at an integer or half-integer Φ/Φ₀ | 0 (mirror turns the flux over; Φ and Φ − Φ₀ are the same physics) | 10⁻⁴ (the gauge identity on the grid: ~10⁻⁵) |
| `no_crossing` | trajectories crossing x = 0 behind the plate (symmetric set-up) | 0 (v_x = 0 on the axis) | exact |
| `screen_y` | max \|Σ_y P(x, y) Δy − P(x)\| over the peak | 0 (the product state's flux; the y bins resolve \|η\|² and the scene holds it) | 10⁻³ |
| `bohm_y` | Kolmogorov–Smirnov distance of the hits' y from the screen's y-marginal Σ_x P(x, y) | the y starts drawn from \|η₀\|² (η spreads by only a few per cent over the flight, so this cannot tell the y-motion: review C1-11) | 1.95/√n (99.9 %) |
| `bohm_y_motion` | max \|y_hit − y\| in widths of η at the hit: the hits' y (y₀σy(t)/σy₀) against dy/dt = j/\|η\|² integrated by RK4 in the run's η from each start to its hit time (a second method) | the guidance equation along y | 10⁻⁶ (RK4 error ≤ 3·10⁻⁸ for σy 0.5–40 λ) |
| `ref_paraxial`, `ref_kirchhoff` | max difference from the paraxial (Fresnel–Kirchhoff) and the exactly propagated Kirchhoff patterns, both with the two-path marks and AB phases | information | — |
| `visibility` | fringe visibility near the axis (Fourier component at the fringe frequency, Hann window ±2 periods) | the two-path value \|cos(θ/2)\| | information |
| `ab_phase` | the fringes' phase near the axis minus 2πΦ/Φ₀·sign(q), mod 2π | 0 (two paths) | information |

The third dimension (σy = 3λ, measured on every preset, GPU 0, 2026-10-28, 86–112 s per experiment): `screen_y`
≤ 6·10⁻¹³ of the peak, `bohm_y` 0.020–0.039 against 1.95/√n ≈ 0.10; the 2-D results below are unchanged (the x, z
starts and the wave do not depend on σy). These were measured before `bohm_y_motion` existed: it found that every hit
of a step had its y at the first hit's time [error in earlier], 2.8·10⁻⁴ of η's width in the tests' geometry (fixed;
now 5·10⁻¹⁴ there). After the fix, preset `narrow` (GPU 0, 92 s): `screen_y` < 10⁻⁶, `bohm_y` 0.021, `bohm_y_motion`
< 10⁻⁶ of η's width (passes; η spreads by 21 % over the flight, median).

Measured on the presets (GPU 0, 2026-10-28, after B4's changes — the screen's layer 4λ behind its face, the flux of
order 32; edges 0.2 λ): every check passes; `numerics` 3.6·10⁻⁴ – 6.2·10⁻⁴ of the peak; `bohm_accuracy` 95 % of the
control's hits within 3·10⁻⁴ – 3.8·10⁻³ λ, no fate changed; 82–124 s per experiment. `narrow` (a = 2λ) — the
paraxial and Kirchhoff patterns differ by 0.33 and 0.35 of the peak (Kirchhoff's boundary values fail for slits of two
wavelengths in a wall of two); `wide` (a = 6λ, thin high wall) — 0.24 and 0.23; `ab` — the fringes' phase +π, equal
to 2πΦ/Φ₀ to 2.5·10⁻⁸ rad, the pattern symmetric to 3·10⁻⁶; `mark180` — visibility 0.20 against the two-path 0 (`mark90`: 0.66 against 0.71); `observer` (He-4, the detector at
slit B, θ = 180°) — the same 0.20: the same 2 × 2 coupling, now on the detector's states. Before the channel
calibration (review B4-3) these were 0.25 and 0.64: the first-order coupling turned the mark by ~1.2θ, which was most
of the residual first called "not understood" [error in earlier]. What remains: the share of the down component just
behind slit B is 0.87 at 180° and 0.57 at 90° (a pure rotation: 1 and 0.5): the wave leaving the slit is not turned
uniformly. Candidates, not yet separated (B3 withdrew a mode explanation of the whole residual): the slit's higher
transverse modes, which the calibration of the lowest one does not fit, and the speed spread (STATUS V26). In `lfphys/tests/test_schrodinger_nd.py` the same
solver, with a thin high wall (edges 1/8 λ), approaches Kirchhoff's pattern as the slits widen: 0.50 of the peak at
a = 2.5λ, 0.19 at 5λ, 0.078 at 10λ (at least first order in λ/a).

## Approximations and limits

* Non-relativistic: the Schrödinger equation with the de Broglie wavelength of the chosen particle; lengths and the
  pattern are exact for that wavelength, times carry an error ~β²/2 (stated in the header when β > 0.01).
* Two dimensions: slits infinitely long along y (exact for that set-up; finite slits are 3-D).
* The wall is a smooth potential of finite height and thickness (a model of a material wall); the detectors are
  absorbing layers (their reflection and leak are checked).
* The geometry is in wavelengths and must fit the grid: slits of 0.5–20 λ, screens up to 200 λ; real experiments with
  slits of 10³–10⁵ λ are the paraxial regime of u32.
* The comparison with the approximate theories (`ref_*`) is information: they are approximations of this computation,
  not references for it.
* Cost: the presets take 82–124 s on GPU 0 (4.8·10⁵ – 5.5·10⁵ grid points, ~2000 pairs of steps, the companion run,
  2000 Bohm particles and the control of 100); the tests' small geometry ~1 min on the CPU. Every world estimates its
  cost when it is built (measured rates × grid points × the pairs to the end estimated from the geometry, an upper
  estimate) and is refused above 10 min on GPU 0 (the host hangs after ~18 min of full load) or an hour on the CPU,
  with the estimate and what to change (review B3-6: corners of the schema would have run ~29 min). The record grows
  by ~14 MB per experiment (the wave's images).
* Open items: `../../STATUS.md` (V26).

## Tests

`tests/test_r12_double_slit_2d.py` (a small geometry, so that the CPU runs them in a few minutes): every preset
builds and passes its static checks; the third dimension is the exact product (η's width and profile in closed form
with every image, y in tracks, hits and frames, P(x, y) on the screen, the x, z starts unchanged by σy, `screen_y`,
`bohm_y` and `bohm_y_motion` pass, and `bohm_y_motion` fails every wrong y-motion: none, twice the spreading, 0.1 %
more of it, every hit at the earliest hit's time); a symmetric experiment runs to its end and passes every check (no trajectory
across the axis, the Bohm accuracy, the numerical error); nothing reaches the screen before the packet's front can,
and the screen stays empty until then; slit B closed after the packet has left the plate changes the pattern by
< 2·10⁻³ of its peak, closed before it changes it by > 0.2; the half flux quantum gives a symmetric pattern with the
fringes moved by half a period; a quarter quantum of either sign moves the run, the reference and the approximate
theories' curves the same way; λ/6 and λ/8 give the same pattern within 3·10⁻³ of its peak; a 180° mark lets
trajectories cross the axis; the observer at slit B marks the path of a particle without spin (⁴He: the fringes go,
trajectories cross the axis), is drawn in 3-D and follows a live θ; refusals (a mark switched off, a spin mark for
⁴He and C₆₀, a flux for a neutral
particle, edges narrower than the grid, an experiment over its cost limit) leave the world as it was; GPU = CPU. The
live plate (review UX-ui U12): V₀ set at t = 0 is a world built with it, bit for bit (another V₀ is not: the negative
control); a, d, w set live are the apparatus's plate in the same window for the run and the companion, and the set-up
message carries the plate in force; a plate beyond the screen or the window and merged slits are refused with the world
unchanged; widened after the packet passed, the pattern changes by < 2·10⁻³ of its peak and the checks pass, widened at
t = 0 it changes (> 0.05); a wall thickened under the wave says the probability it changed at once; a live plate before
and after a checkpoint continues byte for byte in a new process, and a restore by replay rebuilds it; every parameter
with a unit names it in its label (U19). The
engine's own tests: `../../lfphys/tests/test_schrodinger_nd.py`, `test_bohm_nd.py` (with the error-controlled steps
round a vortex and the host patches).

## Sources

* E. Schrödinger, Ann. Phys. 79, 361 (1926); W. Pauli, Z. Phys. 43, 601 (1927).
* M. D. Feit, J. A. Fleck, A. Steiger, J. Comput. Phys. 47, 412 (1982) — the split operator.
* Y. Aharonov, D. Bohm, Phys. Rev. 115, 485 (1959).
* D. Bohm, Phys. Rev. 85, 166 (1952); D. Bohm, R. Schiller, J. Tiomno, Nuovo Cimento Suppl. 1, 48 (1955) (spin).
* C. Philippidis, C. Dewdney, B. J. Hiley, Nuovo Cimento B 52, 15 (1979) — Bohm trajectories behind two slits.
* B.-G. Englert, Phys. Rev. Lett. 77, 2154 (1996) — distinguishability and visibility.
