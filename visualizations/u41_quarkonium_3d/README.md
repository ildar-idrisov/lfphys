# v14 — quarkonium in 3-D: wave functions of a heavy quark pair (Cornell model)

**English** | [Русский](README.ru.md)

A wrapper over the engine `lfphys` (plan item P14.9). A charm–anticharm (cc̄) or bottom–antibottom (bb̄) pair bound by
the Cornell potential V(r) = −κ/r + r/a², in the 3-D environment of the player: the cloud |ψ|² of the vector between
the quarks, the probability current, slice planes with |ψ|² and the phase of ψ, the level diagram of the model against
the measured spin-averaged masses. The states 1S, 2S, 3S, 1P, 2P, 3P, 1D, 2D, 3D (real or complex angular parts) and
superpositions of two. **The physics is a fitted model**: the world is flagged as such (header `approximations`, the
engine panel shows `theories.models.cornell` outside the core).

## What the run computes (engine modules)

| module | layer | role |
|---|---|---|
| `theories.models.cornell` | model | the potential and its fitted parameters κ = 0.52, a = 2.34 GeV⁻¹, m_c = 1.84 GeV, m_b = 5.18 GeV (Eichten & Quigg 1995 quoting Eichten et al. 1980); the box a state needs |
| `core.quantum.radial` | core | the radial functions: sine DVR on N and 2N + 1 points; energies extrapolated (Richardson); u(r) extrapolated for L = 0 (the 1/r term), the fine grid's for L ≥ 1 (`wavefunctions`, accuracy measured on hydrogen) |
| `core.quantum.central3d` | core | the radial table (a spline of R/r^L, its value at the origin by a least-squares cubic), ψ = R·Y_lm, superpositions, the current, quadratures, ⟨T⟩ + ⟨V⟩, matrix elements |
| `core.data` | core | the measured masses (PDG 2024) spin-averaged per multiplet |
| `core.geometry` | core | the slice planes |

The apparatus (`engine/pair.py`): the solves per L with their box, the tables, the independent route of the checks.
The server part and the view are shared with v13 (`../server/lfviz/orbitals3d.py`, `../player/js/orbitview.js`).

## The model

* **Units.** GeV and GeV⁻¹ (ħ = c = 1), reduced mass μ = m_q/2; the scene in femtometres (ħc = 0.19733 GeV·fm),
  energies in MeV, the world clock in seconds (ħ/GeV = 6.58·10⁻²⁵ s).
* **What the model predicts.** Splittings M(n, L) − M(1S) (2–10 % from the measured spin-averaged ones), not absolute
  masses (with these parameters 2m_c + E(1S) is 870 MeV above the measured 1S; STATUS V17). The panel "State"
  gives M − M(1S) and the energy E in the potential; the level diagram draws the model's splittings (solid) and the
  data's (dashed, where PDG lists the multiplet: 1S, 1P, 2S for charmonium; 1S, 1P, 2S, 3S for bottomonium). No spin
  forces, no relativistic corrections, no coupling to open-flavour channels: the states above the D D̄ / B B̄
  threshold (cc̄ 2P, 3S, 1D…) are the model's, not nature's.
* **The radial functions** are numerical: the drawn ones from N = 800, the checks' from a second solve at N = 1200.
  Their accuracy is a check of every world ("Convergence: R(r) of the grid N = 800 against N = 1200": the two differ by less than half a quantisation step of the 8-bit image;
  measured below). The cloud, the current, the time, the phases of a superposition and the slices are those of v13
  (see its README, section "The model").
* **The cloud** is the distribution of r = r_q − r_q̄; each quark's own distribution about the centre of mass is the
  same cloud halved in size.

## Live and world parameters (review UX-ui U12)

As v13's (its README, section "Live and world parameters"): the state — single or superposition, n, L, m, the kind of the
angular part, the second state, |c₂|² and the phase of c₂ — is **live**: an ideal preparation of the new state at the
current moment t_p (the former one discarded, no transition dynamics modelled), in the same world with its clock, record
and slice planes; the box, cloud, current, slices and the state's checks (convergence, energy, nodes, the model's
splittings against data as information) are made for it at t_p, a superposition's period is counted from t_p, the
former state's checks it does not give are retired as information. The cloud grid is **live** (the same state at the
same t_p resampled). The quark pair (cc̄ / bb̄) stays a world parameter: it is the system (the quark mass, the levels of
the model); another pair is a new world in the same run. The title names the pair, not the state.

## Checks

| id | what | reference | tolerance |
|---|---|---|---|
| `norm_k` | ∫\|ψ_k\|² dV of the spline | 1 | the solver's error estimate (grids N and 2N + 1) |
| `conv_k` | max\|R_N − R_1200\| / max\|R\| | 0 | half a quantisation step of the 8-bit image, 1/510 |
| `energy_k` | ⟨T⟩ + ⟨V⟩ of the drawn wave function (the spline's derivative) | the solver's (extrapolated) eigenvalue | 3 × (the change of both from N to N = 1200) |
| `nodes_k` | sign changes of R(r) | n − 1 | exact |
| `split_k` | the model's M(n, L) − M(1S) | PDG spin-averaged | information (a model against data) |
| `slice_p` | ψ at points of plane p | the second solve × scipy's Y_lm | 3 × the largest difference of the two radial solves × \|Y\|, plus the harmonics' round-off: the radial part is bounded by construction, so this tests the angles, phases and plane geometry; the radial accuracy is `conv_k` |
| `current`, `continuity`, `dipole`, `period`, `box` | as in v13 | | |

## Measured

Measured 2026-10-28 in the Docker image (CPU, OMP 2), every preset built by the test harness; a superposition run through one period and then to 3 T; then a tilted plane placed. Deviations: |value − reference| in the check's unit (MeV) or the fraction the check states; tolerances as above. Records without frames.

Build times: the first world of a process solves the radial equation for L = 0, 1, 2 on N = 800 and 1200 points (1.6–2.6 s); later worlds of the same system reuse the solves (0.1–0.2 s). The server runs every run in its own process, so a new run pays the first figure.

| preset | grid | build s (+ one period) | record MB (start → 1 T → 3 T) | + a plane, MB | checks: deviation / tolerance |
|---|---|---|---|---|---|
| cc_1S | 96³ | 2.51 | 0.28 | 0.17 | conv_0 1.17e-05/0.00196078; current 0 ✓; energy_0 1.36e-04/2.93e-04; nodes_0 0 ✓; norm_0 3.85e-09/1.25e-04; slice_1 1.20e-05/3.69e-05; slice_2 1.20e-05/3.69e-05 |
| cc_1P | 96³ | 1.69 | 0.32 | 0.17 | conv_0 1.03e-04/0.00196078; current 0 ✓; energy_0 4.42e-05/9.34e-05; nodes_0 0 ✓; norm_0 7.66e-13/3.10e-05; slice_1 1.31e-07/3.08e-04; slice_2 4.79e-08/1.82e-04 |
| cc_2S | 96³ | 0.12 | 0.28 | 0.17 | conv_0 1.20e-05/0.00196078; current 0 ✓; energy_0 8.35e-05/1.91e-04; nodes_0 1 ✓; norm_0 3.38e-09/1.30e-04; slice_1 7.42e-06/3.88e-05; slice_2 7.09e-07/3.88e-05 |
| cc_1D | 96³ | 1.78 | 0.33 | 0.17 | conv_0 1.34e-09/0.00196078; current 0 ✓; energy_0 2.51e-08/1.10e-07; nodes_0 0 ✓; norm_0 7.08e-12/1.00e-09; slice_1 2.35e-11/4.03e-09; slice_2 3.53e-12/2.01e-09 |
| cc_1P_m1 | 96³ | 0.17 | 0.34 | 0.17 | conv_0 1.03e-04/0.00196078; current 3.82e-11/3.68e-09; energy_0 4.42e-05/9.34e-05; nodes_0 0 ✓; norm_0 7.66e-13/3.10e-05; slice_1 1.70e-07/3.08e-04; slice_2 9.20e-08/3.08e-04 |
| bb_1S | 96³ | 2.63 | 0.27 | 0.17 | conv_0 5.47e-05/0.00196078; current 0 ✓; energy_0 0.00389629/0.00825909; nodes_0 0 ✓; norm_0 9.10e-08/9.15e-04; slice_1 5.70e-05/1.77e-04; slice_2 5.81e-05/1.77e-04 |
| bb_1P | 96³ | 1.60 | 0.31 | 0.17 | conv_0 2.06e-04/0.00196078; current 0 ✓; energy_0 2.47e-04/5.24e-04; nodes_0 0 ✓; norm_0 2.51e-10/1.01e-04; slice_1 5.48e-06/6.19e-04; slice_2 3.45e-07/3.64e-04 |
| bb_2S | 96³ | 0.12 | 0.27 | 0.17 | conv_0 1.06e-04/0.00196078; current 0 ✓; energy_0 0.00150341/0.00330446; nodes_0 1 ✓; norm_0 6.35e-08/9.34e-04; slice_1 3.95e-05/3.61e-04; slice_2 4.81e-05/3.61e-04 |
| bb_1D | 96³ | 1.63 | 0.32 | 0.17 | conv_0 1.07e-08/0.00196078; current 0 ✓; energy_0 1.10e-08/1.39e-07; nodes_0 0 ✓; norm_0 1.03e-10/5.81e-09; slice_1 4.13e-11/3.21e-08; slice_2 2.75e-11/1.60e-08 |
| cc_super | 64³ | 0.19 + 1.75 | 0.12 → 2.75 → 2.75 | 1.47 | continuity 2.21e-06/8.20e-06; conv_0 1.17e-05/0.00196078; conv_1 1.03e-04/0.00196078; dipole 4.23e-14/2.06e-10; energy_0 1.36e-04/2.93e-04; energy_1 4.42e-05/9.34e-05; nodes_0 0 ✓; nodes_1 0 ✓; norm_0 3.85e-09/1.25e-04; norm_1 7.66e-13/3.10e-05; period 3.72e-16/1.00e-12; slice_1 6.39e-07/1.65e-04; slice_2 3.31e-07/1.13e-04 |

"+ a plane": the first placement of a tilted plane. In a superposition every new placement re-sends the plane's 24 phases (1.6 MB each, measured by review B4-12: +8.0 MB for five placements after 2.4 MB for the first period): the record stops growing with time after one period, not with exploring planes. Since review B4-10 the cloud's brightness scale is (Σ_k |c_k||ψ_k|)² over the grid (a bound known without evolving), so a superposition's cloud never reaches the full scale exactly; the numbers above were measured with the former scale (the largest density over the period).

## Approximations and limits

* A fitted, non-relativistic, spin-averaged model (above); κ and a are not parameters of QCD
  (`core.qcd` holds the running coupling).
* Numerical radial functions (measured above); the cloud's 8-bit amplitude and the 10⁻³ outside the drawn sphere, as
  in v13.
* Open items: `../../STATUS.md` (section V; V17 for the model's absolute scale).

## Tests

`tests/test_v14_quarkonium3d.py`: every preset builds and passes its checks (the superposition through one period),
is flagged as a model and shows the model–data splittings as information; the world's levels equal
`cornell.splittings` within 0.05 MeV; the decoded cloud equals |ψ|² of the independent route within half an 8-bit
step; bottomonium is smaller than charmonium and ⟨r⟩ grows 1S < 1P < 2S; the superposition's period is 2πħ/ΔE and it
passes the period, dipole and continuity checks; |m| > L is fitted to the nearest allowed m and said (UX-params
P10), a default second state equal to the first is replaced by 1S, equal states chosen by hand and non-orthogonal states
are refused with a reason; the highest states (3D of both systems) build and pass; 1P_z set live in a running 1S world
is prepared in the same world, its cloud bit for bit a world built with 1P_z, its checks passing, and the quark pair is
refused as a live change (review UX-ui U12).

## Sources

* E. Eichten, K. Gottfried, T. Kinoshita, K. D. Lane, T.-M. Yan, Phys. Rev. D 17, 3090 (1978); D 21, 203 (1980).
* E. J. Eichten, C. Quigg, Phys. Rev. D 52, 1726 (1995) (the parameters as quoted; `lfphys/sources/verification_2026-10-23.md`).
* Particle Data Group, Review of Particle Physics (2024): the charmonium and bottomonium masses.
* D. T. Colbert, W. H. Miller, J. Chem. Phys. 96, 1982 (1992): the sine DVR of the radial solver.
