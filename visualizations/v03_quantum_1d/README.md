# v03 — a quantum particle in one dimension

**English** | [Русский](README.ru.md)

A wrapper over the physics engine `lfphys` (`../../lfphys`). Electrons are sent one by one as wave packets at a
potential (rectangular barrier, double barrier, step, well) or released in a harmonic trap.

## What the run computes (engine modules)

* `lfphys.core.quantum.schrodinger1d`: the wave of every particle, the numerical solution of the time-dependent
  Schroedinger equation on a grid (Strang split-operator, unitary; 6 grid points per shortest half-wave and a phase step
  below 0.1 rad, both measured to converge the transmission below 1e-4). **Sharp edges** (review UX-params P19
  [error in earlier]: a 10 nm barrier with δ = 0.02 nm transmitted 7.7·10⁻⁵ against the stationary 1.38·10⁻⁶, 55
  times too much, and the check showed it failed): the splitting error at an edge of width δ is set by the edge's
  kinetic energy ħ²/(2mδ²) (95 eV at 0.02 nm), not by the particle's; it puts a spurious ~7.5·10⁻⁵ above the barrier
  at the phase step's dt whatever the width (measured at 0.6, 3 and 10 nm; the grid twice as fine changed nothing,
  the time step four times shorter brought it to 2.3·10⁻⁷). Where the expected transmission is below 0.1 the step
  also keeps φ = dt ħ/(2mδ²) ≤ 0.25 (measured: φ = 2.96 → 7.5·10⁻⁵, 1.48 → 8.2·10⁻⁶, 0.74 → 2.3·10⁻⁷); with the
  default δ = 0.1 nm this changes nothing (φ = 0.12), with δ = 0.05 nm it halves the step, and at δ = 0.02 nm such a
  world costs too much and is refused with the δ that would do. Detectors are absorbing ramps at the edges
  (a complex absorbing potential W0 (d/D)^2, a model of a detector); the run integrates how much probability each one
  absorbs, and when. The ramp is chosen per set-up from (D, W0) = (15 nm, 2 eV), (30, 2), (60, 0.5), (120, 0.5):
  the first whose reflection averaged over the packet's spectrum is below 1e-6 and whose leak through the ramp (the
  grid is periodic) is below 1e-8, both from a stationary transfer-matrix calculation of the ramp (shown as a
  check). The run integrates until the probability whose fate is still open is below 1e-3 T + 1e-9 and 1e-3 R + 1e-6,
  not for a fixed time: slow transmitted waves (a step just below the energy) are waited for. Behind a raised step the
  transmitted spectrum is that of the stationary reference, w(k) T(k): the expected time includes its slowest part
  that still carries 10⁻³ of T, and the right detector is chosen for that spectrum (review UX-params P13 [error in
  earlier]: with the energy below the step only the fast tail of the packet passes, just above the threshold and
  slowly; the run waited for it until its budget, 52–88 s, and ended with T 8 % low — partly reflected back by a
  ramp chosen for the incident spectrum — and two failed checks; now ≈ 18 s, every check passing). Probability already
  beyond the potential and moving away from it in a region of constant potential (from its momentum spectrum) reaches
  its detector for sure and is assigned to it at the end of the computed time (its later click time is not
  computed; it is ~1e-3 of the total at most).
* `lfphys.core.quantum.transfer`: the independent reference — the stationary transmission T(E) of the same potential
  (transfer matrices over a fine staircase, two resolutions and Richardson extrapolation), averaged over the
  packet's whole momentum distribution (components with k <= 0 count as reflected). The check's tolerance is
  1e-7 + 1e-3 T + the leftover + the detectors' reflection; the presets agree to ~1e-5.
* The outcome of each particle in the reading chosen by the owner ("Interpretation (does not change the predictions)";
  live; it does not change predictions): `theories.interpretations.copenhagen` (a click at a random moment drawn from
  the detector's absorption rate, then collapse), `theories.interpretations.bohm` (a trajectory from a
  |psi|^2-distributed start q, guided by j/|psi|^2; in one dimension trajectories do not cross, so outside the
  detector ramps it is the q-quantile of |psi(t)|^2, with the absorbed mass counted beyond the edges; inside the ramps
  this construction is the model of detection; the guidance equation integrated step by step agrees with this rule in
  the engine tests), `theories.interpretations.everett` (both branches with their weights; the observer is in one of
  them).

## Checks emitted by the run

Absorbed probability (the leftover below what changes the result); the detectors' reflection and leak; packet
transmission vs the stationary reference; mean energy of the packet vs hbar^2 k0^2/2m + hbar^2/(8 m sigma^2); the counted outcomes vs the
probability (z-score); in the trap: levels hbar omega (n + 1/2) by the spectral method, the period 2 pi/omega, the norm.

## Approximations and limits

* Barrier edges are smooth, (1 + tanh(x/delta))/2 with delta = 0.1 nm by default (live): the rectangle is the limit
  delta -> 0 for delta much smaller than the wavelength; the reference uses the same smooth potential.
* Electrons only: heavier particles need a far finer grid (the wavelength scales as 1/sqrt(m)).
* One dimension; the detectors are a model (absorbing edges) with the reflection and leak stated above.
* Set-ups the run cannot do well are refused with the reason, before anything changes: a packet whose slow edge
  (k0 - 3 hbar/(2 sigma)) is below 0.01 eV (slower electrons are reflected by any ramp of this size, and part of
  the packet would stand still or fly back); a grid above 32768 points; an estimated cost above 6e8 point-steps
  (~25 s; the run stops at twice that and says so). The refusals name what this scenario can change (the trap: ħω and
  x₀; sharp edges: the δ that would do; a step above the energy: the energy, the step or σ). A live change is computed
  before the world goes on (up to that time). A barrier as wide as 10 nm with T ~ 10⁻⁶ settles slowly (its
  above-barrier part dwells in the barrier): it may reach the budget, with T within its tolerance and the absorption
  check saying the run stopped early.
* The energy parameter is that of the central component, hbar^2 k0^2/2m; the mean kinetic energy is larger by
  hbar^2/(8 m sigma^2) (checked). The grey curve in the panel "Outcomes" is the packet's distribution per unit energy.
* The trap's levels come from a 256-point sinc DVR on a window around the trap (turning point of the 4th level plus
  8 ground-state widths).
* A packet of a fixed shape is sent each cycle; outcomes differ by the random draw of the reading.

Open items: `../../STATUS.md`, section V.

## Tests

`tests/test_v03_quantum.py`: every preset runs with all checks passing; the packet transmission equals the
stationary reference to 1e-4; the three readings give the same statistics; clicks are revealed only when reached;
a reading change keeps the wave, a set-up change rebuilds it; trap levels and period; a step above the packet's energy
runs to its transmission without the budget, every check passing (P13); sharp edges shorten the step where T is small
(a 3 nm barrier with δ = 0.05 nm within 1e-4 of the reference; δ = 0.02 nm refused at once with what to change;
negative control: without it T is 8 times too large, P19); the refusals name what the scenario can change.
