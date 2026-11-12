# Response to review B7-md (molecular dynamics `core.md`, `theories.models.interatomic`, playground `p03_molecules`)

Processed 2026-11-04 by a session that wrote neither the review nor the code under review. Rules: `../README.md`. The
review text and the reviewer's scripts are unchanged; copies of the scripts were re-run against the processed code from
the session's scratch directory (a copy of `run.sh` pointing there; containers `lf-b7pm-*`, CPU, `LFPHYS_NO_GPU=1`).
Measurements quoted below come from those re-runs and from the processing's own scripts (scratch `b7/proc_m/s/`); the
literature added for M2, M3 and M16 is quoted in `lfphys/sources/verification_2026-11-04_p8_md.md` §8.

**Counts: 23 findings — 21 fixed, 2 partly fixed (M11, M23), 0 rejected, 0 only deferred; the remainders of M11 and
M23 and two items found while processing go to `STATUS.md` through the integrator (last section).**

Status tags: [useful] a fix or a confirmed claim; [error in earlier] a statement withdrawn.

## Findings

### M1 — hard disks/spheres: a periodic axis with three cells misses collisions — **fixed** [useful]
`hard.py`: a periodic axis now needs at least four cells (L ≥ 4 σ_max); partners in adjacent cells are then at most
2w ≤ L/2 apart, so the minimum image of the prediction stays the colliding one until a cell crossing predicts again
(docstring says why). Verification: r01 — L = 3 is now refused (the script stops at construction: expected); the new
tests `test_md_hard.py::test_periodic_axis_needs_four_cells` (L = 4: the pair collides at t = 0.80 at contact;
negative control: the reviewed cell grid with three cells, kept in the test, loses the collision — centres 0.90 σ) and
`test_no_overlap_in_a_small_periodic_box` (12 disks in 4.2 × 4.2, four cells, 200 time units sampled every 0.02:
closest centres ≥ σ − 1e-9, > 1000 collisions).

### M2 — the preset "liquid and vapour" was a supercritical fluid — **fixed** [error in earlier]
Sources fetched and grepped (§8): the force-shifted LJ at 2.5σ — the playground's default — has T_c = 0.937 and T_tr
= 0.560 in 3-D (Errington, Debenedetti & Torquato 2003, Table 1; NIST SRS) with ρ_liq = 0.693, ρ_vap = 0.032 at 0.75;
in 2-D the full 12-6 has T_c = 0.515, the energy-shifted 2.5σ one 0.459 with a triple point near 0.42 (Smit & Frenkel
1991; Li & Pica Ciamarra 2020): a plane admits liquid–vapour coexistence only in a narrow window, none known for the
force shift. So the preset became 3-D: a slab (walls in y, periodic x, z: 5 fcc cells of the liquid's density
across), a liquid block of ρσ³ = 0.693 at 90 K = 0.751 ε/k, a CSVR bath at 90 K, the field 0.02 ε/(mσ). Its label
says what the run shows; the player now draws the density profile along y (new chart) and the order Q6. Measured
(processing script `m_presets.py lv`, 300 ps; the reviewer's r09 re-run on the new preset, 431 + 431 ps): a liquid
plateau 0.66–0.70 (r09: 0.700), the interface 3–4 σ wide, a vapour of 0.013–0.029 (r09: 0.021 over the top 5 σ;
NIST 0.032 without a field — the field thins it by e^(−mgh/kT) ≈ 0.77 per 10 σ and it holds ~25 atoms), Q6 = 0.04
(not a crystal), steps up to 0.28 per σ-slab; at 120 K (above T_c) a graded fluid, max 0.47, top third 0.14, steps
≤ 0.10. Test `test_p03_molecules.py::test_liquid_and_vapour_coexist_at_90_K_not_at_120_K` (plateau within 10 % of
0.693, vapour < 0.06, a step > 0.15, Q6 < 0.1; negative control 120 K).

### M3 — the preset "melting" did not melt — **fixed** [error in earlier]
Cause: the bath (80 K = 0.668 ε/k) and the crystal (M17: denser than asked, a vacancy strip). Now the crystal is a
perfect triangular lattice of ρσ² = 0.85 in a box that holds 25 × 15 cells (9.9216 × 10.3108 nm; strain 4e-6) and the
bath is at 120 K = 1.00 ε/k, where the 2-D LJ (2.5σ) fluid exists below ρ ≈ 0.896 (Li & Pica Ciamarra 2020, "At high
temperature, T = 1.0 … ρ = 0.90 … solid-hexatic", "hexatic-fluid coexistence … ρ = 0.896"). The player shows the
order |⟨ψ6⟩| (new `observables.bond_order`; Q6 in 3-D) and the mean-square displacement since the last change.
Measured (`m_presets.py melt`, 20 ps windows): at 120 K |⟨ψ6⟩| 1.00 → 0.44 (0–20 ps) → 0.07–0.29 later, MSD 1.3–1.9 σ²
per window (diffusion); control 20 K: 0.92, 0.02 σ²; the reviewed bath 80 K with the perfect crystal: 0.61–0.75 and
0.04–0.28 σ² over 600 ps (no melting, as the review found). Tests `test_the_crystal_melts_at_120_K_and_stays_at_20_K`
(mean |⟨ψ6⟩| over 40–60 ps < 0.3, MSD over the last 30 ps > 1 σ², T within 15 K of 120 K; control 20 K: ψ6 > 0.85,
MSD < 0.1 σ²); `test_bond_order_closed_forms` (triangular ψ6 = 1; fcc Q6 = 0.57452 equal to the addition theorem's
Σ P6(cos γ)/N_b², a second method; random < 4/√N).

### M4 — molecules "at T" started at half that temperature, without translation, with overlaps — **fixed** [error in earlier]
Engine: `add_molecule(..., T)` gives each atom its Maxwell velocity (the canonical momentum distribution of a flexible
molecule: translation, rotation and vibration at T); the per-molecule momentum removal is now an option
(`zero_momentum`); `max_energy` per call; new `MD.molecule_modes` (translation of the centre of mass, rotation L·ω/2
with ω = I⁻¹L about it, vibration the rest; bonds' and angles' potential energy; each as 2E/terms). p03: a start
option — "всё при T" (each atom Maxwellian, bond lengths and angles drawn with their Boltzmann spread √(kT/k)) or
"только поступательное" (each molecule moves as a whole at T, rest geometry); placement with each atom's insertion
energy below 2kT (≥ 0.1 ε); the object's momentum removed; the mode temperatures in the inspector and a chart. The
preset now starts 150 dimers (k = 50 ε/σ², ħω/k = 35 K) with translation only at 400 K and its label says the run
shows equipartition being established. Measured (r05/r05b re-run on the new preset; `m_presets.py mol`): t = 0
translation 424 K, rotation and vibration 0; at 10 ps 198 / 186 / 213 K (bonds 173 K); second half of 300 ps 198 /
198 / 195 / 202 K (SD 10–16 K); the placement: per-atom potential energy at most 3.9 ε (2kT = 6.7 ε at 400 K; the
review found 23 ε), LJ pair energy −67 ε. With "всё при T" at 200 K the kinetic temperature at t = 0 is 194 K
(the review: 84 K). Tests: `test_md_thermo.py::test_molecule_modes_closed_forms_and_equipartition` (pure rotation,
stretch, translation each in its own mode exactly; ⟨K_trans⟩ = (3/2)T per molecule over 1500 dimers; under Langevin
every mode at T within 4 block SE, negative control: three rotations for a linear dimer rejected);
`test_p03_molecules.py::test_molecules_share_their_energy_among_the_modes` (control: the start's 0 K modes),
`test_molecules_start_at_their_temperature`.

### M5 — the hard-disk world: no pressure, no EOS check, edits failed and deleted atoms — **fixed** [error in earlier]
(a) the pressure is read from `pressure` (the collision virial since the last change; the chart's label says so).
(b) a running check of Z against Kolafa & Rottner (disks, ρσ² ≤ 0.88) or Kolafa–Labík–Malijevský (spheres, ρσ³ ≤ 0.90)
with the ensemble correction for the run's N, in a periodic box of one species: the reference functions moved into
the engine (`hard.z_reference`, `hard.ensemble_correction`, equal to the test file's), blocks of ≥ 1 τ after 5 τ from
the last change, pass/fail from 10 blocks at 5 SE + 1e-4; new `HardSpheres.accumulators`. (c) the hard world reuses
its species (`set_species`); the substance change keeps the atoms there too; with M6 a refused change no longer loses
atoms. (d) `HardSpheres.fill(density=…)` builds the crystal of M17 over the region (kept σ/2 from walls). Measured
(r06 re-run): pressure values present (18.0–21.1 mN/m), "set n = 300" accepted (300 atoms), a 4 × 4 nm crystal at 0.7
gets 90 atoms (whole cells; the LJ world the same). The preset over 100 ps: Z = 1.807 against 1.8045 (25 blocks,
tolerance 0.029); over 200 ps 1.806 ± 0.0036. Tests `test_hard_disks_against_the_equation_of_state` (passes; negative
control: the reference at a 5 % higher density, 1.8686, fails), `test_the_hard_world_edits_and_its_crystal`,
`test_md_hard.py::test_fill_by_density_counts_the_region_and_random_fill`, `test_reference_eos_in_the_engine_and_pooled_ks`.

### M6 — a refused change deleted the object's atoms — **fixed**
p03 makes every scene change all or nothing: before `on_add`, `on_remove` or `on_set` it saves the engine's
`state_dict`, its maps (parts, kinds, species, lattice info, pressure blocks) and its generator; when any part raises,
the engine is rebuilt with `from_state_dict` (the engine's bit-for-bit continuation) and the maps put back. Found while
fixing: `_molecules` raised after placing some molecules, which stayed in the engine (same class; now refused as a
whole). Verification: r08 re-run (n 300 → 5000 refused: atoms 300, parts {'o1': 300}, kind kept). Tests
`test_a_refused_set_leaves_the_world_bit_for_bit[count|region]` (two kinds of refusal — the random insertion jams; a
crystal enlarged over a gas overlaps it —: the engine's state dict equal array by array, the parts equal, and the world
equal to a twin that never saw the command after 1 ps), `test_refused_molecules_leave_none_behind`. The framework
(`playground.py`) still restores only the values; a framework-wide snapshot is not needed for p03 and is left to the
framework's owner (no STATUS item: the rule of RULES §6 holds for p03 now).

### M7 — removing the first particle object crashed every frame — **fixed**
`MD.velocity_ks` / `HardSpheres.velocity_ks` pool every mobile species, each component divided by √(T/m) of its own
mass (T: the pooled sample's), and return D = None for no particles; `ks_gaussian`, `ks_cdf`, `dkw_bound` accept an
empty sample. The histogram uses each particle's own mass. Verification: r07 re-run (KS on 400 of 400 components;
after removing o1 no errors). Tests `test_removing_the_first_object_keeps_the_world_running`,
`test_reference_eos_in_the_engine_and_pooled_ks` (a 1 : 9 mass mixture within the DKW bound pooled; an empty species
gives None).

### M8 — the momentum check tested |P| ≈ 0, not conservation — **fixed**
New `MD.momentum_drift`: P_ref is taken at every edit and counter reset (state-saved), and |P − P_ref| per conserved
axis is compared with a derived worst-case rounding bound, steps × ε [h (k + 3) S_w + h S_f + 4 S_v] × 2 plus the
measurement of P (S_w the gross sum of all force terms, k the most terms of one particle, S_f = Σ|f|, S_v = Σ m|v|;
derivation in the docstring). p03 shows drift/bound with tolerance 1, pass/fail, the reference named in the note.
Verification: r04 re-run (an atom at 400 m/s: ok True, ratio 2.0e-4; P constant to 7.6e-14). Tests
`test_md_core.py::test_momentum_drift_against_its_rounding_bound` (600 steps: drift < 1e-11, ratio ≤ 1; negative
control: a velocity changed by 1e-7 behind the engine's back gives a ratio > 10; a field drops its axis; Langevin
gives no ratio) and `test_p03_molecules.py::test_the_momentum_check_tests_conservation` (with the same control). The
bound is a worst case (~4e-10 here against a measured drift < 1e-13).

### M9 — a global CSVR with P ≠ 0 rescaled P and reported T 8.6 % low — **fixed**
`_o_csvr`: a global bath rescales only the velocities relative to the centre of mass along the axes whose momentum is
conserved (K_int with N_f = dN − (those axes)); P is left as it is and the heat is ΔK_int. Verification: r02 re-run
(drift 0.5: P_x 128.0000 throughout, reported T 0.9961 ± 0.0051 against the bath's 1.0). Test
`test_md_thermo.py::test_global_csvr_keeps_a_nonzero_momentum` (P_x to 1e-11 relative; T within 4 block SE; negative
control: the reviewed value 0.918 rejected). STATUS V41 (j) is closed by this (integrator).

### M10 — `set_piston` lost a thermal wall's heat — **fixed**
The popped wall's heat goes to the balance's Q. Verification: r03 re-run (residual −1.1e-13 → −0.000000 after
set_piston; Q kept 507.293484). Test `test_piston_keeps_the_heat_of_the_wall_it_replaces` (residual < 1e-10 Q after
the change and 500 steps later).

### M11 — the first-law residual at a hard piston is not O(dt²) — **partly fixed** (texts and a test; a second-order treatment → STATUS)
Measured in this processing: an LJ gas (100–200 atoms, T = 2.5) in a walled box has a first-order energy error —
the largest |E − E0| over 9.3 τ 0.6 / 0.33 / 0.19 ε at dt = 0.0046 / 0.0023 / 0.0012 τ (three seeds), against 0.06 /
0.02 / 0.006 in the same box made periodic (`nve_dt.py`); the piston preset's residual over its first 20 ps (r16
re-run, random start) 2.4 / 2.7 / 3.1 ε (mean |·|) at 10 / 5 / 2.5 fs, the review's 14.0 / 1.9 / 1.2 ε (lattice
start): not O(dt²) and noisy. The texts now say so: the module docstring ("first order in dt" with the numbers),
the energy check's note in p03 (for worlds with walls or a piston: "ошибка первого порядка по dt … 1–14 ε за первый
ход"), the p03 README, the engine's `validity` ("O(dt²) при непрерывных силах … первого порядка" at hard walls and
the piston). Test
`test_md_core.py::test_hard_walls_make_the_energy_error_first_order` (six seeds, dt 0.004 → 0.001: the walled box's
error falls by < 8 — measured 3.1 —, the periodic control's by > 8 — measured 14.7). Not done: a soft piston face
(the soft LJ wall exists for the fixed sides) and a companion with random walls (the two copies draw at different
steps: no meaningful comparison) → STATUS V41 (e) (integrator text).

### M12 — a piston edit moved the piston back to its initial position — **fixed**
`_piston(v, old)`: X only when "position" (or the axis) changed, V only when the driven speed or the mass changed (a
driven piston made free starts at rest); the field's help says so. Verification: r15 re-run (p_ext 50 → 40 mN/m:
piston at 3.738 nm, was 3.738). Test `test_a_piston_edit_leaves_the_piston_where_it_is` (and an edit of the position
moves it to 11.0 nm).

### M13 — the virial pressure with frozen atoms — **fixed**
Frozen–frozen pairs are no longer listed (a constant energy; less work). With frozen atoms the virial is Clausius'
for the moving atoms, W_aa = Σ_mobile x_a F_a (pair, Coulomb, bonded forces), defined along walled axes (equal to the
pressure on the hi wall, origin at the lo wall) and None along periodic ones; `pressure()` returns None for the mean
then. Verification: r12 re-run — (B0) the frozen block alone 1.0974 → 0.0000; (B) virial (0.3719, 0.3857) against the
hi walls (0.3746, 0.3894) (it was 1.45). Test `test_frozen_atoms_virial_is_the_walls_pressure` (12 blocks of 10 τ,
with the exact boundary term Δ Σ m x v: equal to the hi walls within 4 SE per axis; negative control: the reviewed
all-pairs virial rejected; a slab gives None along x).

### M14 — `set_species` admitted overlaps; a mass change changed T — **fixed**
`set_species` checks every particle of the species against `max_insert_energy` (or `max_energy`) when σ, ε or the
charge change. p03 rescales the velocities by √(m_old/m_new) on a mass change (the same atoms at the same
temperature; the inspector's help says so). Verification: r17 (a) re-run (σ 1 → 1.4 refused: "overlap … 319.9");
r14 (d) re-run (E₀ moves only by the integrator's drift since t = 0: 625.080 → 625.102). Tests
`test_set_species_refuses_overlaps` (state bit for bit; σ 1.02 accepted),
`test_a_substance_change_keeps_the_atoms_and_their_temperature` (K equal to 1e-12).

### M15 — "+0.39 % at N = 500" for hard spheres is not reproduced — **fixed** [error in earlier]
Twelve independent runs of the test's own estimator (seeds 101–112, 10 blocks of 3 τ after 5 τ, `m15.py`): Z =
3.2649 ± 0.0032 against the corrected reference 3.2673 (−0.08 %, −0.8 SE); per-run spread 0.0111, mean block SE
0.0095 (14 % low); all twelve within 4 block SE. The test's docstring now gives these numbers and withdraws the
finite-size claim; the tolerance (4 block SE ≈ 3.4 run spreads) is kept: the 2 % control lies 0.088 above the
reference (8 run spreads). `sources/verification_2026-11-04_p8_md.md` §8 records it. STATUS V41 (g) (integrator).

### M16 — the approximations understated quantum effects and the model's thermodynamics — **fixed**
p03's approximations per world: solid argon quantum below Θ_D = 85 K with the Debye heat capacity at 20 / 40 / 80 K
(0.47 / 0.81 / 0.95: `viz.debye_cv_fraction`, as r19); the cut LJ is another substance than argon with the model's T_c
(3-D force shift 2.5σ: 0.937 ε/k = 112 K; full 12-6 1.312 = 157 K; argon 150.7–150.9 K, NIST WebBook 150.65 /
150.86 K; 2-D full 0.515 = 62 K, energy shift 0.459 = 55 K; no value found for the 2-D force shift); every molecule
object's ħω/k with the quantum heat-capacity fraction at its T (100 K for k = 400, 35 K for the preset's k = 50). The
p03 README and `interatomic.ABOUT["conflicts"]` (2-D numbers, the triple points, argon's T_c from the WebBook) say the
same. Sources §8. Test `test_texts_state_the_limits`.

### M17 — what the crystal's "density" and the gas's "random places" were — **fixed** [error in earlier]
New `system.crystal_sites` (a perfect lattice with the spacing of the requested density: whole cells centred in a
region; cells fitted to a periodic box the block spans, the actual density and the strain reported) used by
`MD.fill(density=…)` and `HardSpheres.fill(density=…)`; new `system.random_sites` (random sequential insertion, none
nearer than σ_ij, from the system's generator inside the transaction; refused when it jams) used by p03's gas
(`arrangement="random"`). Verification: r14 (c) re-run (300 distinct x and y coordinates); r10's setting now has
density 0.8500 and strain 4e-6 (the preset box), a periodic 29.37 box at 0.85 gets 0.8695 (25 × 15 cells, reported)
and no strip (largest gap 0.59 σ, was 1.69 σ). Tests `test_crystal_sites_random_sites_and_probe`,
`test_equal_speeds_become_maxwellian` (no shared coordinates, none nearer than σ).

### M18 — hard world and probes: what is drawn and measured — **fixed**
The histogram uses each particle's mass in both worlds; hard disks get their species' index (colour, radius) from the
new `HardSpheres.particles`; probes use the new `probe(center, radius)` of both engines (count, density over the ball's
part inside the walls, 2K/(dn) of the same atoms, minimum image); the hard world's cost check shows seconds per event
and the number of atoms. Test `test_crystal_sites_random_sites_and_probe` (count equal to a direct minimum-image
count; a ball half outside a wall has half the volume).

### M19 — the field's unit — **fixed**
Help text: "единица ε/(mσ) ≈ 7,3·10¹³ м/с² (земное g ≈ 1,3·10⁻¹³ в этих единицах)". Test `test_texts_state_the_limits`
(the text and σ/τ² = 7.32e13 m/s²).

### M20 — "W includes the edits" — **fixed**
The note: "работа поршня W … (правки сдвигают E₀ на изменённую ими энергию)"; README the same.

### M21 — degrees of freedom in a slab — **fixed**
New `MD.momentum_conserved_axes` (periodic, no field along it; no Langevin, local or species bath, thermal wall or
frozen atom); `dof` = dN − (conserved axes), `temperature` and `kinetic_tensor` subtract the centre of mass along
them; `momentum_conserved()` = all axes. Verification: r14 (e) re-run (slab: dof 99 for 50 atoms, P_x constant). Test
`test_degrees_of_freedom_by_axis` (slab 2N − 1; a y-field keeps it; a thermal wall gives 2N).

### M22 — `HardSpheres.pressure()` in a walled box — **fixed**
Per axis: periodic (2K_a + W_a/Δt)/V; walled (2K_a + W_a/Δt)/(A (L_a − σ_eff)) with σ_eff the impulse-weighted diameter
of the particles that hit the walls (Clausius with the contact planes; per-axis kinetic energy and collision virial
now accumulated; `tensor` returned). Verification: r17 (b) re-run: 1.2361 against the walls 1.2316–1.2399 (was 1.1537).
Test `test_walled_box_pressure_is_the_walls` (12 blocks: equal within 4 SE; negative control: the old (2K + W)/V,
7 % low, rejected).

### M23 — layer placement — **partly fixed** (the move of the statistics → STATUS)
`core.md.hard` now names its conflict as a model of atoms (no attraction: no liquid–vapour transition; no softness).
The move of KS / DKW / block averages to `tools` is not done here: `MD.velocity_ks` uses them and the core may not
import `tools` (LAYERS rule 2), so the move changes the core's API (the core would return the scaled sample and the
caller test it) and touches `tools/` and `LAYERS.md`, outside this processing's files → STATUS (integrator).

## Found while processing

* p03's molecules: a refused placement after some molecules were added left them in the engine — fixed with M6.
* The random insertion stops after 20 000 failures in a row (a filled box used to take 10⁶ tries).
* Hard walls with interacting atoms make the energy error first order (M11) — documented and tested.

## Tests run (all pass, after the last change of code)

* `lfphys`: `tests/test_md_core.py test_md_bonds.py test_md_lj.py test_md_thermo.py test_md_hard.py test_md_gpu.py
  test_boundary.py test_layers.py test_licences.py` on the CPU — 283 passed, 4 skipped (the GPU ones), 522 s
  (the review's baseline: 56 MD tests; 15 new: 5 in `test_md_hard.py`, 7 in `test_md_core.py`, 3 in
  `test_md_thermo.py`; the rest of the 283 are the boundary, layer and licence tests); `tests/test_md_gpu.py` on GPU 0
  through the guard — 4 passed, 16 s.
* `visualizations`: `p03_molecules/tests tests/test_restore.py tests/test_checkpoint.py -k "p03 or shared or
  molecules"` — 29 passed, 230 s (p03: 25 tests, 13 before).
* A browser check of p03 (a private server on port 8517, Playwright 1.58.2; scratch `b7/proc_m/s/p03_browser.mjs`):
  every preset played 9 s — no page errors, the nine charts drawn (the molecules' mode chart only where there are
  molecules), the stat box with the order and the MSD, the pressure chart labelled "по столкновениям" in the hard
  world. `node --check` on `web/view.js`.

## Changes for the integrator

**`STATUS.md` (exact text).** In row V41 (the MD part; LBM and FLRW letters untouched):

1. replace "(e) hard walls, thermal walls and the piston act inside the Verlet drift: with stiff forces a stroke's
   first-law residual is noisy in dt (exact, 10⁻¹⁴, for ideal gases);" by "(e) hard walls, thermal walls and the
   piston act inside the Verlet drift: with interacting atoms the energy error is first order in dt (an LJ gas in a
   walled box 0.6 / 0.33 / 0.19 ε at dt = 0.0046 / 0.0023 / 0.0012 τ against 0.06 / 0.02 / 0.006 ε when periodic;
   the piston preset's residual 1–14 ε over its first stroke; review B7-md M11); exact, 10⁻¹⁴, for ideal gases;"
2. replace "at ρ = 0.5 (spheres) N = 500 lies 0.39 % above Kolafa–Labík–Malijevský (N = 2048 agrees);" by "a periodic
   axis needs L ≥ 4 σ_max (B7-md M1) [error in earlier: "N = 500 lies 0.39 % above Kolafa–Labík–Malijevský" — twelve
   independent runs give −0.08 ± 0.10 % (B7-md M15)];"
3. replace "(j) a global CSVR with non-zero total momentum thermostats the centre of mass too;" by "(j) closed
   2026-11-04 (B7-md M9: a global CSVR rescales only the motion relative to the centre of mass along the conserved
   axes; P stays, T is the bath's);"
4. after "(l) sources not fetched: … Rahman 1964." insert " (ad) the pure statistics of a run (KS distance, DKW
   bound, block averages) sit in `core.md.observables`, where LAYERS.md puts them in `tools`; `MD.velocity_ks` uses
   them and the core may not import `tools` (B7-md M23); (ae) no published critical point found for the 2-D
   force-shifted LJ, the playground's default in a plane (the energy-shifted 2.5σ model: 0.459, triple point near
   0.42; B7-md M2, M16)." (Letters (y), (z), (ab), (ac) are taken by the LBM / FLRW items as of this writing; take the
   next free ones if they changed.)
5. in the plan column of V41, replace "(a) Ewald (3-D and slab);" by "(a) Ewald (3-D and slab); (e) a soft piston face
   (an LJ wall term moving with the piston) or the forces split at the collision times;" and append "; (ad) move the
   statistics to `tools`, `velocity_ks` returning the scaled sample; (ae) a slab-coexistence or Gibbs-ensemble
   measurement".

In row V42 (the p03 part): replace "(c) the energy balance is shown as information (the residual and the companion's
estimate; the engine's tests check its O(dt²) law);" by "(c) the energy balance is shown as information (the residual
and the companion's estimate; the engine's tests check its O(dt²) law with continuous forces and its first order at
hard walls and the piston, V41 (e));" and after "(d) Earth's gravity is ~10⁻¹³ in argon's units: the field is a model
field in ε/(mσ)." (before "**p04 «Жидкости»**") insert " (j) the hard world's equation-of-state check covers one
species in a periodic box (no reference for mixtures or walls)." (plan column: append "; (j) a mixture equation of
state, e.g. Boublík–Mansoori–Carnahan–Starling–Leland, checked against a second method"; letters (e)–(i) are taken by
p04 as of this writing).

**`lfphys/README.md` (exact text, the MD rows).**

* Row `core.md.system`: replace "particles with stable keys," by "particles with stable keys (crystals of a given
  density — a perfect lattice of that spacing — and random gases by random sequential insertion),"; replace "velocity
  Verlet (NVE; energy error O(dt²) for continuous forces, exactly time-reversible, momentum to round-off)" by "velocity
  Verlet (NVE; energy error O(dt²) for continuous forces, first order at hard walls and the piston with interacting
  atoms, exactly time-reversible, momentum to round-off along every conserved axis)"; replace "CSVR (Bussi et al.
  2007, exact Eq. A7)" by "CSVR (Bussi et al. 2007, exact Eq. A7; a global bath about the centre of mass)"; replace
  "temperature with its degrees of freedom stated, virial pressure tensor (tail correction separately)" by
  "temperature with its degrees of freedom stated (per conserved momentum axis), virial pressure tensor (tail
  correction separately; with frozen atoms Clausius' virial of the moving ones, along walled axes)"; replace "velocity
  KS against Maxwell with the DKW bound," by "velocity KS against Maxwell with the DKW bound (all species pooled, each
  by its mass), the momentum's change against its rounding bound, molecules' mode temperatures (translation,
  rotation, vibration, bonds, angles), a probe ball,".
* Row `core.md.hard`: replace "event calendar with cell crossings and wall contacts," by "event calendar with cell
  crossings and wall contacts (a periodic axis at least four diameters long),"; replace "pressure from the collision
  virial (the NVT compressibility factor of the NVE run) and on the walls," by "pressure from the collision virial
  per axis (walled axes with the walls' contact planes: equal to the walls' pressure) and the NVT compressibility
  factor of the NVE run, the published equations of state of one-component disks and spheres with the ensemble
  correction (`z_reference`, `ensemble_correction`), the pressure on the walls,".
* Row `core.md.observables, …`: replace "the canonical Gamma law of the kinetic energy," by "the canonical Gamma law of
  the kinetic energy, the bond-orientational order (ψ6 in 2-D, Steinhardt's Q6 in 3-D),".

**Shared framework tests.** No change needed: `SMALL["p03_molecules"]` (the piston preset's params) and the empty
`PLAN` entry still fit (the piston preset's laws are unchanged; its gas is now placed at random from the world's own
generator, so replays and checkpoints stay deterministic: `test_restore`, `test_checkpoint` pass).

**`reviews/README.md` registry line (proposed, when the folder moves to `archive/` after the STATUS edits):** "|
`archive/2026-11-04_internal_B7-md/` | internal (subagent) | batch B7, molecular dynamics: P8 (`core.md`,
`theories.models.interatomic`) and P15.4 (`p03_molecules`), 19 scripts | 2026-11-04 | `RESPONSE.md` (processed
2026-11-04: 21 of 23 fixed, M11 and M23 partly with their remainders in STATUS V41 (e), (ad) — the liquid–vapour preset
was supercritical (now 3-D at 0.75 ε/k inside the force-shifted model's coexistence, NIST) [error in earlier], the
melting preset did not melt (now a perfect crystal at 120 K: ψ6 1 → 0.1) [error in earlier], molecules started at
half their temperature [error in earlier], the hard-disk world had no pressure nor EOS check, a refused change deleted
atoms (now all or nothing), a three-cell periodic axis lost hard-sphere collisions, the +0.39 % hard-sphere offset not
reproduced [error in earlier]; CSVR with P ≠ 0, frozen-atom virial, slab degrees of freedom, walled hard-sphere
pressure) |"
