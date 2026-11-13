# u40 — the hydrogen atom in 3-D: orbital clouds, currents, superpositions

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.5). The exact bound states of a hydrogen-like atom — an electron and
a nucleus of charge Z (hydrogen, deuterium, He⁺) or positronium — in the 3-D environment of the player: the cloud
|ψ|² of the relative coordinate, the probability current, up to three slice planes of any orientation with |ψ|² and
the phase of ψ, and the panels "State", "Radial distribution r²|R(r)|²" and "Energy levels". A single stationary state
(real orbital or complex state of definite m) or a superposition of two; a superposition of two levels oscillates
at the Bohr frequency and is revealed phase by phase as the world's time runs.

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `core.quantum.hydrogen` | core | R_nl(r) (the generalised Laguerre polynomial by its three-term recurrence, the product N e^{−ρ/2} ρ^l L formed in logarithms: no overflow for any n), the closed-form moments ⟨r^k⟩, the energies −μc²(Zα)²/2n² with the reduced mass, the Bohr radius and Hartree energy of μ |
| `core.quantum.central3d` | core | Y_lm (normalised associated Legendre recurrences, Condon–Shortley phase) and the real orbitals, ψ = R·Y on points, two-state superpositions and their Bohr frequency, the probability current j = (ħ/μ) Im(ψ*∇ψ) (centred differences; the closed form (ħm/μ)\|ψ\|²φ̂/ρ for a state of definite m), quadratures (radial Gauss–Legendre panels, the exact angular product rule), ⟨T⟩ + ⟨V⟩ of a wave function, dipole matrix elements |
| `core.geometry` | core | the slice planes and their cut by the scene's box |

The apparatus (`engine/atoms.py`, no physics of its own): the atoms (Z, the nucleus's mass from CODATA through
`scipy.constants`), their units, and the independent route of the checks. The shared server part of the 3-D
wave-function worlds is `../server/lfviz/orbitals3d.py`, the shared view `../player/js/orbitview.js` (both also used by
u41).

## The model

* **Units.** The run computes in the reduced Bohr radius a_μ = ħ/(μcα) and the reduced Hartree energy E_h(μ) = μc²α²
  (ħ = μ = 1), μ = m_e M/(m_e + M); the scene is in ångströms, energies in eV, the world clock in seconds (one unit
  of time is ħ/E_h(μ) = 2.42·10⁻¹⁷ s for hydrogen).
* **The state.** ψ_nlm = R_nl(r) Y_lm(θ, φ), 1 ≤ n ≤ 12. Real orbitals: √2(−1)^m Re Y_l|m| (m > 0, cos mφ),
  √2(−1)^m Im Y_l|m| (m < 0, sin|m|φ): p_x, p_y, d_xy, d_z², … with positive lobes along the positive axes. A
  superposition c₁ψ₁e^{−iE₁t/ħ} + c₂ψ₂e^{−iE₂t/ħ} of two orthogonal states (|c₂|² and the relative phase set at the
  preparation; t counted from it, section "Live and world parameters"); two states of the same (n, l) whose angular parts overlap are refused (one is a combination of the
  other). The form cannot bound l by n and m by l: the world takes the nearest allowed numbers (n first, then
  0 ≤ l < n, then |m| ≤ l) and says so; the second state defaults to 1s, so "a superposition of two states" alone is 2p_z + 1s, and a
  default second state equal to the first is replaced (1s → 2p_z) with a notice; one chosen equal by hand is refused
  (review UX-params P10, 2026-11-05).
* **The cloud.** |ψ|² on a cube that holds the sphere with 1 − 10⁻³ of the probability (the radius found by quadrature
  of r²R²), 64³ or 96³ nodes. Sent as the 8-bit amplitude √(|ψ|²/peak), deflated (the 3-D texture has 8 bits anyway);
  |ψ|² below 1.5·10⁻⁵ of the peak is drawn as zero (the log scale starts there); the slices carry the exact values.
* **The current.** j at the points of a 10 × 10 × 10 lattice that lie inside that sphere (552; none at the
  nucleus, where ψ has a cusp). Real orbitals and m = 0 states
  carry none (Im ψ*∇ψ ≡ 0): no glyphs. Complex states with m ≠ 0: rings around z. A superposition: a flow that sloshes
  with the cloud.
* **Time.** A stationary state's density does not change (only its phase turns). A superposition of two levels is
  periodic with T = 2πħ/|E₂ − E₁| (1s + 2p: 0.405 fs). The run computes the cloud, the current and the slices at 24
  phases of T and reveals phase k when the world's time reaches kT/24 (accumulative messages with `bin`); a frame names
  the phase it shows — the last one reached, never a later one. After one period the density repeats exactly (checked
  when the time reaches T), so nothing new is sent and the record stops growing; a viewer who scrolls back sees the
  cloud of that moment. Two states of one energy (2p_x + i·2p_y) are stationary.
* **Slices.** |ψ|² (as a fraction of the cloud's peak: one scale for the windows and the 3-D scene) and arg ψ on each
  plane, computed for the plane itself (160 points on its longer side; 96 per phase for a superposition, at every
  phase reached), NaN outside the box. Each placement is checked at the brightest point and four more points with
  ≥ 5 % of its density, drawn by the run's seeded generator.

## Live and world parameters (review UX-ui U12)

The owner (2026-11-04): «плейграунд должен быть больше похож на плейграунд, где я могу ставить эксперименты в рамках
одного мира, а не перезапускать его постоянно» ("a playground should be more like a playground, where I can set up
experiments within one world instead of restarting it all the time"). Every parameter, and whether the world takes it at the current moment:

| parameter | | what an edit does to the state; or why it stays a world parameter |
|---|---|---|
| the state: single / superposition, n, l (L), m, real or complex, the second state's numbers and kind, \|c₂\|², the phase of c₂ | **live** (U12) | an ideal preparation of the new state at the current moment t_p: ψ(t) = Σ c_k e^{−iE_k(t − t_p)/ħ} ψ_k from then on, the former state discarded — how the system gets there (a photon absorbed, a measurement) is not modelled, no transition dynamics is claimed. The world, its clock, the record and the slice planes the experimenter placed stay; the box, the cloud and the current of the phases reached, the slices on those planes (clamped into the new box, computed and checked again), the radial distribution and the state's checks are made for the new state at t_p; a superposition's phases are revealed at t_p + kT/24 and the period checked at t_p + T. The checks of the former state that the new one does not give at once are retired ("… — former state", information; their values stay in the record before t_p). The run sends `prepared` (the header's description of the new state) before the rest, and frames carry t_p; numbers the form cannot bound are fitted and said, a second state equal to the first chosen by hand or not orthogonal to it is refused with the world unchanged. The camera is refitted only when the box changed (the view of a new scene) |
| cloud grid (64 / 96 points per axis) | **live** (U12) | the same state at the same t_p resampled on the new grid: the phases reached are computed again |
| atom (H, D, He⁺, positronium) | world | the nucleus and the reduced mass are the system: no operation turns one atom into another keeping its electron's state; another atom is a new world in the same run (the slice planes are taken over, the state in force too) |

The title names the atom, not the state (the panel "State" names the state in force).

## Checks

| id | what | reference | tolerance |
|---|---|---|---|
| `norm_k` | ∫\|ψ_k\|² dV by quadrature | 1 | 10⁻¹² + 10 × the change when the panels are doubled |
| `r_k` | ⟨r⟩ by quadrature of the run's R | a/(2Z)[3n² − l(l+1)] | 10⁻¹⁰ |
| `energy_k` | ⟨T⟩ + ⟨V⟩ of the wave function (R′ by fourth-order differences) | −μc²(Zα)²/2n²; the virial ratio −⟨V⟩/⟨T⟩ = 2 in the note | 10⁻⁹ |
| `nodes_k` | sign changes of R(r) | n − l − 1 | exact |
| `slice_p` | ψ at points of plane p | the power series of the Laguerre polynomial (exact integer coefficients) × scipy's Y_lm, with the same time phases | the bound on both routes' round-off: the series' 64ε Σ\|terms\|, the log route's ~(S + 4n)ε, the harmonics' 64(l+1)ε |
| `current` | the drawn current (differences) | 0 (real orbitals, m = 0) or (ħm/μ)\|ψ\|²φ̂/ρ | the truncation estimated by the steps h and 2h, plus round-off |
| `continuity` | ∂ρ/∂t + ∇·j at the glyph points away from the nucleus (superpositions; ∇·j for one energy) | 0 | the residual must be a truncation error: \|residual(2h) − residual(h)\| + round-off |
| `dipole` | ⟨r⟩(t) at each phase reached, by 3-D quadrature of the run's \|ψ(t)\|² | 2Re(c₁*c₂⟨1\|r\|2⟩e^{−iωt}); ⟨1s\|z\|2p₀⟩ = 2⁷√2/3⁵ a (Bethe & Salpeter) for that pair, otherwise the matrix element by quadrature | 10⁻⁹ of the oscillation's amplitude |
| `period` | the cloud at T | the cloud at 0 | 10⁻¹² of the peak |
| `box` | the probability inside the sphere the scene's cube holds | — (information) | — |

Measured values per preset: see section "Measured" below.

## Measured

Measured 2026-10-28 in the Docker image (CPU, OMP 2), every preset built by the test harness; a superposition run through one period and then to 3 T; then a tilted plane placed. Deviations: |value − reference| in the check's unit (eV, Å) or the fraction the check states; tolerances as above. Records without frames.

| preset | grid | build s (+ one period) | record MB (start → 1 T → 3 T) | + a plane, MB | checks: deviation / tolerance |
|---|---|---|---|---|---|
| 1s | 96³ | 0.14 | 0.26 | 0.17 | current 0 ✓; energy_0 2.76e-12/1.36e-08; nodes_0 0 ✓; norm_0 3.33e-16/1.00e-12; r_0 2.22e-16/7.94e-11; slice_1 2.18e-16/4.50e-14; slice_2 2.18e-16/4.46e-14 |
| 2pz | 96³ | 0.14 | 0.29 | 0.17 | current 0 ✓; energy_0 1.41e-13/3.40e-09; nodes_0 0 ✓; norm_0 6.66e-16/1.00e-12; r_0 2.22e-15/2.65e-10; slice_1 5.71e-16/7.71e-14; slice_2 2.85e-16/6.22e-14 |
| 3dz2 | 96³ | 0.14 | 0.30 | 0.17 | current 0 ✓; energy_0 2.66e-14/1.51e-09; nodes_0 0 ✓; norm_0 8.88e-16/1.00e-12; r_0 7.11e-15/5.56e-10; slice_1 5.04e-16/1.14e-13; slice_2 3.78e-16/8.71e-14 |
| 2px_real | 96³ | 0.15 | 0.29 | 0.17 | current 0 ✓; energy_0 1.41e-13/3.40e-09; nodes_0 0 ✓; norm_0 6.66e-16/1.00e-12; r_0 2.22e-15/2.65e-10; slice_1 3.81e-16/7.71e-14; slice_2 5.71e-16/7.56e-14 |
| 2p_m1 | 96³ | 0.16 | 0.31 | 0.17 | current 6.18e-11/3.09e-09; energy_0 1.41e-13/3.40e-09; nodes_0 0 ✓; norm_0 6.66e-16/1.00e-12; r_0 2.22e-15/2.65e-10; slice_1 4.02e-16/7.68e-14; slice_2 2.77e-16/7.66e-14 |
| 3d_m2 | 96³ | 0.16 | 0.32 | 0.17 | current 8.94e-11/1.62e-08; energy_0 2.66e-14/1.51e-09; nodes_0 0 ✓; norm_0 8.88e-16/1.00e-12; r_0 7.11e-15/5.56e-10; slice_1 8.20e-16/1.23e-13; slice_2 9.67e-16/1.23e-13 |
| super_1s2p | 64³ | 0.21 + 2.02 | 0.10 → 2.42 → 2.42 | 1.47 | continuity 3.69e-07/1.51e-06; dipole 5.55e-17/3.81e-10; energy_0 2.78e-12/1.36e-08; energy_1 1.41e-13/3.40e-09; nodes_0 0 ✓; nodes_1 0 ✓; norm_0 1.11e-16/1.00e-12; norm_1 6.66e-16/1.00e-12; period 5.34e-16/1.00e-12; r_0 3.33e-16/7.94e-11; r_1 2.22e-15/2.65e-10; slice_1 1.99e-16/5.27e-14; slice_2 1.99e-16/4.69e-14 |
| px_ipy | 64³ | 0.15 | 0.26 | 0.17 | continuity 2.88e-07/2.94e-06; energy_0 1.41e-13/3.40e-09; energy_1 1.41e-13/3.40e-09; nodes_0 0 ✓; nodes_1 0 ✓; norm_0 6.66e-16/1.00e-12; norm_1 6.66e-16/1.00e-12; r_0 2.22e-15/2.65e-10; r_1 2.22e-15/2.65e-10; slice_1 4.04e-16/1.18e-13; slice_2 2.78e-16/1.30e-13 |
| n10 | 96³ | 0.20 | 0.30 | 0.17 | current 0 ✓; energy_0 4.08e-14/1.36e-10; nodes_0 6 ✓; norm_0 3.33e-15/1.00e-12; r_0 2.56e-13/7.62e-09; slice_1 4.56e-14/1.38e-11; slice_2 2.82e-14/1.87e-11 |
| he_3dxy | 96³ | 0.16 | 0.30 | 0.17 | current 0 ✓; energy_0 1.04e-13/6.05e-09; nodes_0 0 ✓; norm_0 8.88e-16/1.00e-12; r_0 2.22e-15/2.78e-10; slice_1 6.83e-32/6.98e-14; slice_2 2.05e-16/1.20e-13 |

"+ a plane": the first placement of a tilted plane. In a superposition every new placement re-sends the plane's 24 phases (1.6 MB each, measured by review B4-12: +8.0 MB for five placements after 2.4 MB for the first period): the record stops growing with time after one period, not with exploring planes. Since review B4-10 the cloud's brightness scale is (Σ_k |c_k||ψ_k|)² over the grid (a bound known without evolving), so a superposition's cloud never reaches the full scale exactly; the numbers above were measured with the former scale (the largest density over the period).

## Approximations and limits

* Non-relativistic, spinless: the Schrödinger levels (no fine structure, Lamb shift or hyperfine structure;
  `core.quantum.hydrogen` has the Dirac levels, this world does not use them). The nucleus is a point charge.
* The cloud is the relative coordinate (the centre of mass is separated; for positronium the "nucleus" is the
  positron).
* The cloud's 8-bit amplitude and the 10⁻³ of the probability outside the drawn sphere are the picture's limits; the
  slices are exact.
* Superpositions of two states only (one Bohr frequency); three or more levels would need a common period of many
  Bohr periods.
* The current's glyph lengths are scaled to the largest |j| of their phase (comparable within a phase, not across
  phases).
* Open items: `../../STATUS.md` (section V).

## Tests

`tests/test_u40_hydrogen3d.py`: every preset builds and passes its checks (a superposition run through one period);
the decoded cloud equals |ψ|² of the independent route at every node within half an 8-bit step; a superposition's
phases are revealed only when the time reaches them, frames never show a later phase, the record does not grow after
one period and the frame at 3.5 T shows phase 12; real orbitals have no current, the m = +1 state's rings turn
counter-clockwise about z; 2p_x + i·2p_y has the density of 2p, m = +1; the reduced mass and Z scale energies and
sizes; the slice planes (any orientation, a fourth refused, removal, kept in a new world, coarse unchecked slices while
moving, reset); a plane placed mid-period gets the phases reached and the rest later; l ≥ n and |m| > l are fitted
and said, two equal states chosen by hand and two non-orthogonal states are refused with a reason; "a superposition of two states" from
the defaults builds; 2p_z + 2s (j = 0, ∂ρ/∂t = 0 everywhere) passes the continuity check with a zero residual (it
divided by a zero scale and killed the worker: UX-params P3); the largest states (n = 12, l = 11 and
l = 0; a superposition of n = 12 and 11) build and pass. The live state (review UX-ui U12): 3d_z² set in a running
superposition is prepared in the same world (`prepared` first; the cloud bit for bit a world built with 3d_z²; its checks
pass; the superposition's checks retired as information; frames carry t_p); a superposition prepared at t_p (not on a
phase step) reveals its phases at t_p + kT/24, each the cloud of a world that started with it (bit for bit), while
phases counted from t = 0 would differ (the negative control), and its period is checked at t_p + T; a refused
preparation (an equal second state chosen by hand) leaves the state, t_p, the planes and the parameters as they were and
emits only the refusal and the live values; a slice plane placed before a preparation is placed and checked again; the
cloud grid sent as text ("96") resamples the same state at the same t_p; the atom is refused as a live change; a
preparation before and after a checkpoint continues byte for byte in a new process. The engine's tests: `../../lfphys/tests/test_central3d.py`,
`test_hydrogen_wavefunctions.py`.

## Sources

* E. Schrödinger, Ann. Phys. 79, 361 (1926).
* H. A. Bethe, E. E. Salpeter, *Quantum Mechanics of One- and Two-Electron Atoms* (Springer, 1957): R_nl, ⟨r^k⟩,
  the 1s–2p dipole matrix element.
* E. U. Condon, G. H. Shortley, *The Theory of Atomic Spectra* (Cambridge, 1935): the phases of Y_lm.
* S. A. Holmes, W. E. Featherstone, J. Geodesy 76, 279 (2002): the normalised recurrences of P_l^m.
* CODATA through `scipy.constants`: α, m_e, the masses of the proton, deuteron and α particle.
