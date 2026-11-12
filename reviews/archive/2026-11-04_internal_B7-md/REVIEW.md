# Review B7 — molecular dynamics (plan P8: `core.md`, `theories.models.interatomic`) and the playground `p03_molecules` (P15.4)

**Status: awaiting processing.** Internal review by a subagent that did not write the code (2026-11-04). Rules:
`../README.md`. The reviewer does not process this review, writes no `RESPONSE.md` and does not archive it.

**Scope.** `lfphys/lfphys/core/md/{system,hard,observables,cells,units}.py`, `lfphys/lfphys/theories/models/interatomic.py`,
`lfphys/tests/test_md_{core,thermo,lj,hard,bonds,gpu}.py`, `lfphys/sources/verification_2026-11-04_p8_md.md`, the four
MD rows of `lfphys/README.md`, `STATUS.md` V41 (a)–(l); `visualizations/p03_molecules/{viz.py, web/view.js, README.md,
tests/test_p03_molecules.py}` on the framework `server/lfviz/playground.py` (`RULES.md` §6). Hashes of the reviewed
files: `reviewed_files.sha256` (unchanged at the end of the review).

**Environment.** Docker image `light-funnel-viz` (Python 3.11.17, NumPy 2.4.6, SciPy 1.17.1), CPU only
(`LFPHYS_NO_GPU=1`), `engine/` mounted read-only. Every script runs as `./run.sh <name>` (one container
`lf-b7rm-<name>`) and writes `<name>.out` here; `common.py` sets the paths; playground scripts drive a world with
`visualizations/tests/harness.py`, without the server. Two scripts wrap an engine method at run time to record what
it does (r13); no engine file was changed.

**Baseline.** The engine's MD tests pass (`tests_engine.out`: 56 passed, 4 skipped — the GPU ones —, 287 s); p03's
pass (`tests_p03.out`: 13 passed).

## Summary

| id | severity | where | one line |
|---|---|---|---|
| M1 | error | `hard.py:21-22, 163, 410-421` | a periodic axis with three cells (3σ ≤ L < 4σ, allowed): the collision is predicted with the minimum image at prediction time, which is not the colliding image when partners are > L/2 apart; the collision is missed and the disks overlap by 0.1σ (r01) |
| M2 | error | `viz.py:93-101` (preset `liquid_vapour`) | "liquid and vapour" at 90 K = 0.751 ε/k in 2-D: the 2-D LJ critical temperature is ≈ 0.50 ε/k (60 K), lower still with the force shift: the run is a supercritical fluid with a smooth barometric profile; at 45 K the same scene gives a liquid layer under vapour (r09) |
| M3 | error | `viz.py:79-83` (preset `melting`) | the crystal at 80 K does not melt in 1000 ps (orientational order \|⟨ψ6⟩\| 0.64–0.70, MSD 1.1–1.8 σ² per 200 ps; at 120 K it melts within 200 ps); the test checks only T (r10, r10b) |
| M4 | error | `system.py:593-650` (`:639`), `viz.py:300, 334-369` (preset `molecules`) | molecules "at T" start with no translation (each molecule's momentum removed) and half the kinetic energy of T, and are placed with overlaps up to 50 ε per atom: the 200 K preset starts at 84 K and settles at ~105 K; the claimed sharing of energy between rotation and vibration is not shown by anything (r05, r05b) |
| M5 | error | `viz.py:552, 578-617, 268, 293`; `hard.py:265` | the hard-disk world: the pressure is never shown (key `"collision"` does not exist), no equation-of-state check exists although the preset promises one, every change of a hard object is refused (`species exists`) and leaves the world without its atoms, a crystal in a region is always refused (n counted over the whole box) (r06) |
| M6 | error | `viz.py:431-441`; `playground.py:209-222` | a refused change of a particle object (number, region, T) deletes its atoms: the scene still lists the object with its old values, the world has 0 atoms (r08; RULES §6: "a refused change … leaves the scene as it was") |
| M7 | error | `viz.py:569, 602`; `observables.py` `ks_gaussian` | removing the first particle object while others remain crashes every following frame (KS of an empty species: `zero-size array`); the KS check and statistic use only the first species anyway (r07) |
| M8 | error | `viz.py:594-601` | the one pass/fail check of p03 tests \|P\| ≈ 0, not that P is conserved: an atom launched at 400 m/s into the NVE preset `maxwell` keeps P to 7·10⁻¹⁴, yet the check fails (r04) |
| M9 | should-fix | `system.py:1428-1436, 1449, 1536-1552` | a global CSVR with P ≠ 0: `momentum_conserved()` stays True and N_f = dN − d while the bath rescales P (P_x 128 → 115.6…142.0) and the reported temperature settles 8.6 % below the bath's (r02; STATUS V41 (j) names the cause, not these consequences) |
| M10 | error | `system.py:723-727` | `set_piston` removes a thermal hi wall without carrying its heat into the first-law balance (`set_wall` and `remove_thermostat` do): the residual jumps from 10⁻¹³ to the wall's heat, 507 (r03) |
| M11 | should-fix | `viz.py:584-585`; `system.py:50-51`; STATUS V41 (e) | the first-law residual of an interacting gas at a hard piston is not "the Verlet error O(dt²)" as the check says: 14.0 / 1.93 / 1.22 ε at dt 10 / 5 / 2.5 fs (≈ 1.5 % of W in the preset), up to 40× the same gas's NVE error (r15, r16) |
| M12 | should-fix | `viz.py:393-402` | editing any piston parameter (e.g. p_ext) puts the piston back at its initial 'position': 3.89 → 10.00 nm in one step (r15) |
| M13 | should-fix | `system.py:60-63, 1060-1090, 1573-1593` | the virial pressure sums frozen–frozen pairs and the forces on frozen atoms: a frozen block alone gives p = 1.10; with a gas the virial says 1.45 where the walls feel 0.39 (r12) |
| M14 | should-fix | `system.py:414-424`; `viz.py:437-438` | `set_species` is not overlap-checked: σ 1 → 1.4 in a dense fluid is accepted (U = 3.4·10⁴) and T goes 1 → 48 in 20 steps; p03's substance change uses it, and a mass change silently changes T (velocities kept) (r17, r14) |
| M15 | should-fix | `test_md_hard.py:100-106`; STATUS V41 (g) | the recorded "+0.39 % at N = 500, a finite-size effect beyond 1/N" is not reproduced: 12 runs give Z = 3.2647 ± 0.0039 against 3.2673 (−0.08 %, −0.7 SE); also Z_vir = Z_rate and no overlaps (r11) |
| M16 | should-fix | `viz.py:645-658`; p03 README "Approximations" | the approximations understate: quantum effects "below ~20 K" — solid argon's C_v at 20 K is 0.47 of the classical value (Θ_D = 85 K), the preset bond has ħω/k = 100 K; and the cut, force-shifted LJ is a different substance (3-D T_c 112 K, 2-D ≈ 60 K against argon's 150.7 K) while presets speak of argon at given K (r19) |
| M17 | should-fix | `system.py:233-262, 490`; `viz.py:142-143, 185`; p03 README | "crystal at density ρ": a lattice whose spacing is set by the box (here ρ_local = 0.904 for ρ = 0.85) with a 1.7σ empty strip; "gas at random places": the atoms are on a lattice (r10, r14) |
| M18 | nit | `viz.py:496, 508-514, 563`; hard `cost_estimate` | hard world: velocity histogram with m = 1 for every species, all disks drawn with species 0's radius and colour, probes show the global T; probes measure T over the cube c ± r and the density over the ball; the hard cost note reads "None атомов" |
| M19 | nit | `viz.py:179` | field help: "the unit ≈ 9·10¹¹ m/s²" — it is ε/(mσ) = 7.32·10¹³ m/s² (r14) |
| M20 | nit | `viz.py:584-585`; p03 README "Running checks" | "W = the work of the piston and of the edits": edits move E₀, W stays 0 (r14) |
| M21 | nit | `system.py:1536-1541` | a slab (walls in y, periodic in x), NVE: P_x is conserved but N_f = dN (O(1/N)) (r14) |
| M22 | nit | `hard.py:28-30, 603-617` | `HardSpheres.pressure()["pressure"]` in a walled box is 7 % below the walls' pressure (factor (L − σ)/L per walled axis); "the mechanical pressure of this finite system" does not say which (r17) |
| M23 | nit | `observables.py:31`; `hard.py:53-69`; `LAYERS.md` | layers: KS / DKW / block averages are "statistics of simulated data" (`tools` by LAYERS.md) but sit in the core; the hard-sphere interaction — a model of atoms like WCA, which lives in `theories.models` — is in the core with `conflicts: []` |

**Counts: 9 error, 8 should-fix, 6 nit.**

Checked and found in order (section at the end): CSVR's Eq. (A7) and its degrees of freedom, BAOAB's order, the
thermal wall's flux-weighted re-emission (sampled directly, MD 2-D/3-D and hard disks), the virial pressure against
the walls for an LJ liquid, the tail corrections in 2-D and 3-D, the 9-3 / 10-4 walls, the hard-sphere dynamics
(no overlap, Z_vir = Z_rate), bit-identical restores with thermal walls, a driven piston, a local Langevin bath and
molecules, the units (τ, 419 bar, 14.27 mN/m), the quotations of the source file that I re-fetched.

---

## Errors

### M1 — error — hard disks/spheres: a periodic axis with three cells misses collisions

Location: `lfphys/lfphys/core/md/hard.py:21-22` ("A periodic axis needs at least three cells (L_a >= 3 max sigma)"),
`:163` (refusal only for `nc < 3`), `:402-427` (`_predict`: `r[:, a] -= L[a] * rint(r[:, a] / L[a])` at the
prediction time).

Mechanism: cells have width w = L/nc ≥ σ_max; partners in adjacent cells can be up to 2w apart along an axis. With
nc = 3, L/2 = 1.5 w < 2 w, so the minimum image at the prediction time can be the other image than the one that will
collide; the pair is then predicted to separate (b > 0), and nothing re-predicts when the minimum image flips (only a
cell crossing does). If the contact comes before the crossing, the collision is lost.

Evidence `r01_hard_three_cells.py/.out`: σ = 1, L_x = 3 (three cells), i at x = 0.1, j at x = 1.9 moving at −1.
Contact is at t = 0.8; the run shows no collision then and the centres reach 0.9000 (a 10 % overlap) at t = 0.9, when
j enters i's cell and an immediate "collision" at overlap is processed:

    Lx = 3.0: collisions 2, smallest centre distance seen 0.9000 (sigma = 1)
       t = 0.80  |r_ij| = 1.0000  collisions = 0
       t = 0.90  |r_ij| = 0.9000  collisions = 1
    Lx = 4.0: collisions 1, smallest centre distance seen 1.0000 (sigma = 1); first sample after a collision (np.float64(0.8), np.float64(1.0000000000000002))

Reach: periodic boxes with 3 σ_max ≤ L < 4 σ_max; in p03's hard world box sides of 1.02–1.36 nm (the parameter's
minimum is 0.5 nm). It breaks the module's statement "the dynamics is exact up to the rounding of the collision times".

Fix: require nc ≥ 4 on periodic axes (L ≥ 4 σ_max; then 2w ≤ L/2), or, for nc = 3, predict with both images
(r and r ∓ L) and keep the earliest root. Add r01's pair as a regression test.

### M2 — error — the preset "liquid and vapour" is a supercritical fluid

Location: `visualizations/p03_molecules/viz.py:93-101` ("Жидкость и пар в поле: капля оседает, над ней пар": 2-D, LJ
force-shifted at 2.5σ (the default), CSVR at 90 K = 0.751 ε/k, field 0.02).

Literature (arXiv:2606.08178v3, Table II, quoted from the fetched text): "Jiang&Gubbins, N=8000 … 0.498 ± 0.002" and
"Smit&Frenkel, N=512 … 0.515 ± 0.002" for the 2-D LJ critical temperature, and "There is an obvious trend in the
finite-size estimate of the critical temperature … Tc ≈ 0.50"; their data note "the truncated potential is used in MC
simulations, affecting the critical point locus". The force shift lowers T_c further (3-D: 1.312 full, 0.937 for LFS
2.5σ — NIST, quoted below). So 0.751 ε/k is about 1.5 T_c: no coexistence exists.

Evidence `r09_p03_liquid_vapour.py/.out` (the preset as given, 431 ps + 431 ps averaged; density per 1σ slab from the
bottom):

    thermostat 90.0 K = 0.751 eps/k: 0.197 0.224 0.231 0.220 … 0.123 0.107 … 0.082 0.076 0.073
       largest jump between neighbouring slabs 0.026; max rho 0.231, min rho 0.073
    thermostat 45.0 K = 0.376 eps/k: 0.374 0.563 0.638 0.660 0.660 0.631 0.580 0.499 0.372 0.209 0.101 0.045 0.023 … 0.003
       largest jump between neighbouring slabs 0.189; max rho 0.660, min rho 0.003

At 90 K the "drop" spreads into a smoothly graded fluid (a barometric profile of a supercritical fluid); at 45 K the
same scene gives a condensed layer with an interface 4–5σ wide under a vapour of ρ ≈ 0.003–0.02. What the preset
promises is a known fact asserted by its label, not a consequence of this run (AGENTS.md §3 rule 2).

Fix: in 2-D use T ≤ 0.40 ε/k (≈ 45–48 K; r09's control), or make the preset 3-D, where 0.75 ε/k is inside the LFS
coexistence region (NIST SAT-TMMC LFS 2.5σ, row "0.75 3.18771E-02 … 6.93338E-01": ρ_vap 0.032, ρ_liq 0.693); show the
consequence in the run (a density profile along the field or a histogram of local densities). State T_c of the model
in the approximations (M16).

### M3 — error — the preset "melting" does not melt

Location: `viz.py:79-83` ("Кристалл аргона нагревают термостатом: плавление": crystal object at density 0.85, 20 K,
CSVR at 80 K = 0.668 ε/k, 2-D, 10 × 10 nm periodic); `tests/test_p03_molecules.py`
`test_a_thermostat_brings_the_crystal_to_its_temperature` checks only T.

Evidence `r10_p03_melting.out`, `r10b_p03_melting_long.out` (global bond-orientational order \|⟨ψ6⟩\| — ≈ 1 for a
single crystal, ≈ N^-1/2 = 0.04 for a liquid —, the mean local \|ψ6\|, the mean-square displacement per window):

    bath 80.0 K (0.668 eps/k):
         0- 200 ps: T =  80.2 K, |<psi6>| = 0.645, <|psi6|> = 0.748, MSD in the window = 1.846 sigma^2
       …
       800-1000 ps: T =  79.1 K, |<psi6>| = 0.668, <|psi6|> = 0.764, MSD in the window = 1.759 sigma^2
    bath 120.0 K (1.002 eps/k):
         0- 200 ps: T = 126.4 K, |<psi6>| = 0.045, <|psi6|> = 0.644, MSD in the window = 21.471 sigma^2

At 80 K the orientational order persists over 1000 ps (8 minutes of watching at the default 2 ps/s) and the atoms
diffuse ~12 × less than in the melted state; what moves is the defect strip of M17. At 120 K the same atoms melt in
< 200 ps. (20 K, the start, gives \|⟨ψ6⟩\| = 0.93, MSD 0.025 σ².)

Fix: bath ≥ 1.0 ε/k (120 K), or a lower density; show a computed order measure (ψ6 or the diffusion coefficient from
the MSD) so that melting is a consequence of the run; let the test assert the drop of ψ6 / a non-zero D, not only T.

### M4 — error — molecules "at T" start at half that temperature, without translation

Location: `lfphys/lfphys/core/md/system.py:593-650` (`add_molecule(..., T)`: Maxwell velocities per atom, then
`vv[fin] -= (m vv).sum(0) / m.sum()` at `:639` removes each molecule's own momentum); `viz.py:288-300, 334-369`
(the palette's "Температура, K" passed as that T); preset `molecules` `viz.py:102-105` (60 dimers, 200 K).

Evidence `r05_p03_molecule_temperature.out` (per dimer, the temperature of each mode: 3 translational, 2 rotational, 1
vibrational kinetic and 1 potential quadratic term):

    t = 0:      T_measured 84.3, trans 0.0, rot 155.2, vib_kin 191.4, vib_pot 0.0
    t = 100 ps: T_measured 103.1, trans 101.9, rot 96.3, vib_kin 115.2, vib_pot 123.9
    t = 700 ps: T_measured 104.9, trans 104.8, rot 117.8, vib_kin 74.2, vib_pot 95.1

A dimer starts with (dn − d)/(dn) = 1/2 of the kinetic energy of T and no translation. The kinetic energy alone
would equilibrate at 72 K over the 357 + 60 quadratic terms; the run ends near 105 K because the random placement
also put in potential energy: `r05b_p03_molecule_placement_energy.out` — "LJ pair energy 35.22 eps … per-atom
potential energy: max 23.16 eps, atoms above 1 eps: 2" at t = 0, −24.1 ε at 300 ps. `add_molecule` accepts an
insertion up to `max_insert_energy` = 50 ε per atom (6000 K for argon), which the README calls "placed … without
overlaps". The object's "200 K" is not the gas's temperature at any time. The preset's claim (rotation and vibration
share the energy) does hold roughly in r05, but no message of the run shows mode energies: the player cannot show it.

Fix: give each molecule a centre-of-mass velocity drawn at T with its total mass plus internal velocities at T (or
keep the atoms' Maxwell velocities and remove only the object's total momentum), and say so in the docstring; place
molecules with a threshold of a few kT (or relax the overlaps before giving velocities); add a per-mode energy readout
(translation / rotation / vibration with the equipartition reference) for molecule objects.

### M5 — error — the hard-disk world: no pressure, no EOS check, edits fail and delete atoms

Location: `viz.py:552` (`P.get("collision")`), `:578-617` (checks), `:264-273` (`_species`: `add_species(oid)` always
in the hard world, `:268`), `:290-294` (crystal); `hard.py:256-266` (`fill(density)`: `n = density * prod(L)` at `:265`).

Evidence `r06_p03_hard_world.out`:

    (a) stats messages: 6 ; pressure values p: ['None']
        engine pressure(): {'pressure': 1.357…, 'T': 2.42…, 'Z': 1.743…}
    (b) checks: {'maxwell': (…, None, True, 0.030…), 'cost': (…, None, True, None)}
    (c) set n = 300: ['Сцена: "species \'o1\' exists"'] ; atoms now 0
    (d) hard crystal 4 x 4 nm at density 0.7 in a 12 x 12 nm box: ['Сцена: overlapping hard particles'] ; atoms 0 ; expected about 97
        control, the same with LJ: [] ; atoms 97

(a) `HardSpheres.pressure()` has keys `pressure`, `Z`, `T`, `collision_rate`, not `collision`: the pressure chart is
empty. (b) The preset is titled "Твёрдые диски: давление против уравнения состояния", but no check compares anything
with an equation of state; `test_every_preset_builds_runs_and_keeps_its_laws` passes because no check can fail.
(c) Any change of number / T / region of a hard object is refused, and (M6) the atoms are gone. (d) A crystal in a
region gets the atom count of the whole box.

Fix: read `pressure`/`Z`; add a running check of Z against Kolafa & Rottner (disks) or Kolafa–Labík–Malijevský
(spheres) with the ensemble correction for the run's N and a tolerance from the run's block errors (as
`test_md_hard.py` does), shown for a periodic box only; reuse an existing species (`set_species`) in the hard world;
`HardSpheres.fill(density=…)` counts over the region (and keeps σ/2 from walls inside a given region).

### M6 — error — a refused change deletes the object's atoms

Location: `viz.py:431-441` (`on_set` = `on_remove(old)` + `on_add(new)`), framework `playground.py:209-222` (on failure
restores `obj["values"]` only).

Evidence `r08_p03_refused_set.out` (preset `maxwell`, number 300 → 5000, which does not fit):

    before: atoms 300 ; scene {'o1': 300} ; parts {'o1': 300}
    refused: ["Сцена: overlap: an inserted particle's potential energy 2.146e+04 exceeds max_insert_energy = 50"]
    after: atoms 0 ; scene {'o1': 300} ; parts {} ; kind {}
    then removing the object: []

The scene (and a scene file exported now) lists 300 atoms that the world no longer has; RULES.md §6: "a refused
change is reported and leaves the scene as it was"; `test_a_refused_change_leaves_the_scene_as_it_was` only tests
`op=add`.

Fix: make the replacement all-or-nothing — snapshot the engine (`state_dict`) and the wrapper's maps before
`on_remove`, restore them when `on_add` raises (or let the framework do this for every `on_set`); add r08 as a test.

### M7 — error — removing the first particle object stops the world

Location: `viz.py:569` (`emit_stats`), `:602` (`checks`): `md.velocity_ks()` with its default, the engine's first
species; `observables.ks_gaussian` / `dkw_bound` with n = 0.

Evidence `r07_p03_remove_first_object.out`:

    KS uses species: o1 ; n = 200 of 400
    after removing o1 : exception ValueError zero-size array to reduction operation maximum which has no identity

The empty species stays first, so every later frame raises; the runner reports and pauses the world
(`server/lfviz/sim.py:551`). Before that, the KS statistic and the "maxwell" check describe only the first object's
atoms (here 200 of 400 velocity components), while their labels speak of "the velocities".

Fix: pool all mobile species, each component divided by its own √(T/m) (as the histogram already does), skip
species without atoms, and return "no data" for n = 0 in `ks_gaussian`/`dkw_bound`.

### M8 — error — the momentum check fails correct runs

Location: `viz.py:594-601`: `ok = max|P| / Σ|v| ≤ 1e-10` — the value of P, not its change.

Evidence `r04_p03_momentum_check.out` (preset `maxwell`, periodic, NVE; one atom added at 400 m/s):

    momentum check after: {'ok': False, 'value': 0.0030706725175521405, 'tol': 1e-10}
    P during the run (NVE, periodic: conserved): ['2.533156435809', '2.533156435809', … ]
    max |P(t) - P(add)| = 7.460698725481052e-14

This is the only pass/fail check of p03; it reports a broken conservation law where the engine conserves P to
round-off. (With a global CSVR the check then tests a quantity the bath does change: M9.)

Fix: store P at the last edit / counter reset and check \|P(t) − P_ref\| against a round-off bound (e.g. the number
of steps × ε_mach × Σ\|F\| dt); describe the reference in the note.

### M10 — error — `set_piston` loses a thermal wall's heat from the first law

Location: `system.py:723-727` (`self._walls.pop(f"{_AX[a]}-hi", None)`), compare `set_wall` `:689-692` and
`remove_thermostat` `:838-840`, which move the removed heat into `_balance["Q"]`.

Evidence `r03_piston_drops_wall_heat.out` (ideal gas, exact bookkeeping):

    before: Q = 507.293484  W = 0.000000  residual = -1.137e-13
    after set_piston: Q = 0.000000  W = 0.000000  residual = 507.293484  (the y-hi wall's heat was 507.293484)
    control (set_wall to specular): residual = -1.137e-13

p03 hides it (every `on_add` resets the counters), but the engine's `energy_balance` is documented as exact for ideal
gases.

Fix: add the popped wall's heat to `_balance["Q"]` in `set_piston`'s `apply`; a test like r03.

## Should-fix

### M9 — should-fix — a global CSVR with non-zero momentum

Location: `system.py:1428-1436` (`momentum_conserved` ignores P under a global CSVR), `:1449` (N_f = dN − d),
`:1536-1552` (`dof`, `temperature`). STATUS V41 (j) says only "a global CSVR with non-zero total momentum thermostats
the centre of mass too".

Evidence `r02_csvr_nonzero_momentum.out` (LJ, N = 256, periodic, CSVR τ = 0.05 at T = 1):

    drift 0.0: … P_x min -0.0000 max 0.0000; reported T 0.9961 +- 0.0052 (bath 1.0)
    drift 0.5: momentum_conserved() = True, dof = (765, …)
       P_x at start 128.0000; during the run min 115.5590 max 141.9513 (constant if conserved)
       reported T (centre-of-mass frame): mean 0.9138 +- 0.0046 (bath 1.0); expected low by 2 <P^2/2M>/N_f = 0.0823

Bussi et al. assume the momentum is fixed ("Since the rescaling procedure does not change these quantities, our
algorithm samples only the corresponding slice of the canonical ensemble"); with P ≠ 0 the rescaling does change it.
In p03 P ≠ 0 arises from a single atom launched with a velocity (r04).

Fix: rescale only the velocities relative to the centre of mass (K_int with N_f = dN − d) and leave P alone, so that
P stays conserved and T is the bath's; or refuse a global CSVR while P ≠ 0.

### M11 — should-fix — the first law at a hard piston with an interacting gas is not O(dt²)

Location: `viz.py:584-585` (note: "остаток — ошибка схемы Верле (O(dt²))"), `system.py:50-51` ("energy error O(dt^2),
bounded (no drift)"), STATUS V41 (e) ("noisy in dt").

Evidence `r15_p03_piston.out` (preset `piston` at the default 10 fs):

    t =  10.0 ps: piston at  7.088 nm, V = -2.219, …, T =  752.8 K; Q = -1.440, W = +809.764, residual = +2.700e-01
    t =  20.0 ps: piston at  3.684 nm, V = -0.856, …, T = 1115.1 K; Q = -850.626, W = +2254.276, residual = +2.485e+01
    t =  60.0 ps: … residual = +3.262e+01

and `r16_piston_residual_scaling.out` (first 20 ps, three seeds):

    dt = 10.0 fs: residuals [24.851, -3.145, -14.125] (mean |.| 14.040); NVE gas without piston: [-0.1166, 0.3559, 0.8093]
    dt =  5.0 fs: residuals [-2.583, 1.922, 1.27]   (mean |.| 1.925);  NVE gas without piston: [0.0138, 0.0636, 0.306]
    dt =  2.5 fs: residuals [2.408, -1.186, 0.052]  (mean |.| 1.215);  NVE gas without piston: [0.0038, -0.0166, 0.0713]

Halving dt from 5 to 2.5 fs divides the residual by 1.6, not 4; at 2.5 fs the piston adds ~40× the gas's own NVE error.
A reflection inside the drift is an impulsive force that the Verlet splitting does not resolve: an error of order
F v dt per hit, accumulating with the hits. The companion estimate (dt/2) is not shown here because the preset has a
thermal wall.

Fix: state it (note, docstring, README: "with interacting atoms at hard walls or the piston the residual is O(dt) per
hit, see …"); offer a soft piston face (a wall potential moving with the piston) where a clean balance matters; allow
the companion when randomness is present by fixing the generator's state in both copies.

### M12 — should-fix — a piston edit moves the piston back to its initial position

Location: `viz.py:393-402`: `kw = {"X": self._len(v["position"]), …}` on every `on_set`.

Evidence `r15_p03_piston.out`: "after setting p_ext 50 -> 40 mN/m: piston at 10.000 nm (was 3.891); errors []" — a
free expansion of the compressed gas by an edit of the pressure.

Fix: pass X only when "position" changed (likewise keep V unless mass/speed changed).

### M13 — should-fix — virial pressure with frozen atoms

Location: `system.py:60-63` (docstring: with walls the virial equals the wall pressure), `:1060-1090` (all pairs in
the list, frozen–frozen included, enter `vir`), `:1573-1593`.

Evidence `r12_virial_walls_frozen.out` (2-D, 20 × 20, specular walls, force-shifted LJ):

    (A) LJ, walls: virial tensor (x, y) = (0.1979, 0.2008); walls {'x-lo': 0.2015, 'x-hi': 0.2038, 'y-lo': 0.1999, 'y-hi': 0.1986}
    (B0) frozen block only (no mobile atoms): virial = 1.0974
    (B) LJ + frozen block, walls: virial tensor (x, y) = (1.4512, 1.4596); walls {'x-lo': 0.3883, 'x-hi': 0.3746, 'y-lo': 0.395, 'y-hi': 0.3894}

(A) confirms the docstring without frozen atoms. Clausius' theorem for the moving atoms contains Σ_mobile x_i·F_i, not
the r_ij·F_ij of pairs with a frozen partner (that adds x_j·F_j of the frozen atom) nor frozen–frozen pairs at all.

Fix: drop frozen–frozen pairs from the pair list (also saves work), use x_i·F_i of the mobile atom for mobile–frozen
pairs in walled boxes, or say that the virial pressure is not defined with frozen atoms and report the walls'.

### M14 — should-fix — `set_species` admits overlaps; a mass change silently changes T

Location: `system.py:414-424` (`_transaction(apply)` without `new_keys`: no insertion-energy check, `:864`);
`viz.py:437-438` (p03's substance change).

Evidence `r17_engine_edges.out`: "(a) set_species(sigma 1 -> 1.4) accepted: potential energy 3.374e+04, largest |F|
4033 … after 20 steps: max |v| 24.83, T = 48.49" (from T = 1). `r14_units_and_texts.out` (d): the substance change
of preset `maxwell` to 80 u (velocities kept) moves E₀ from 735 to 1574 — the gas's temperature doubles.

Fix: apply the `max_insert_energy` test to every particle of a changed species (refuse with the overlap message);
in p03 either keep T on a mass change (rescale velocities by √(m_old/m_new)) or say in the inspector that the
temperature changes.

### M15 — should-fix — "+0.39 % at N = 500" for hard spheres is not reproduced

Location: `lfphys/tests/test_md_hard.py:100-106` ("N = 500 runs lie 0.39 % above the corrected reference (four
longer runs: 3.2800 +- 0.0034) … a finite-size effect beyond the 1/N correction"), STATUS V41 (g).

Evidence `r11_hard_spheres_consistency.out` (ρ = 0.5, N = 500, 12 independent runs of 25 τ after 5 τ):

    mean Z_vir 3.26471 +- 0.00391 (12 runs); mean Z_rate 3.26498 +- 0.00321; mean Z_vir - Z_rate -0.00027 +- 0.00179
    reference Z_NVT(500) = 3.2693735 - 1.02068/500 = 3.26733; Z_vir - ref = -0.00262 (-0.08 %, -0.7 SE)

The single-run spread is 0.0135 (Z from 3.233 to 3.280); the recorded 3.2800 ± 0.0034 is 2.9 combined standard errors
from this mean. The authors' readme ("For too small N even this is not enough.") is a general caution, not a measured
size at N = 500. The same runs check the dynamics: no centres closer than 1.00000004 σ (sampled every 0.05 τ) and the
virial and collision-rate routes agree.

Fix: re-measure with ≥ 12 independent runs and give the per-run spread; until then write the offset as unexplained
and unconfirmed (a hypothesis), not as a finite-size effect; derive the test's tolerance from the per-run spread
(4 block SE of one 30 τ run is ≈ 1.5 %, weak against a 2 % density control). Tag `[error in earlier]` if it holds.

### M16 — should-fix — the playground's approximations understate quantum effects and the model's thermodynamics

Location: `viz.py:645-658` (`"классическая механика атомов (без квантовых эффектов: для аргона заметны ниже ~ 20 K)"`,
`"… модель Леннард-Джонса (12-6) с параметрами аргона, обрезка на … σ"`), p03 README "Approximations and limits".

(a) Solid argon: "For solid argon, which forms FCC structure below the melting temperature of 84 K, the Debye
temperature is ΘD =85 K" (arXiv:1304.2049); path integrals are needed "at temperatures lower than the Debye
temperature ΘD, where the quantum nature of the atomic nuclei is relevant" (arXiv:cond-mat/0606142).
`r19_quantum_thresholds.out`: Debye C_v/(3Nk) = 0.467 at 20 K (the melting preset's start), 0.806 at 40 K, 0.946 at
80 K. Bonds: ħω/k = 100 K for the preset's k_bond = 400 ε/σ² (5–501 K over the parameter's range 1–10⁴); the
molecules preset runs at ~105 K (M4), where a quantum oscillator's heat capacity is ~0.9 of the classical one.

(b) The cut and force-shifted LJ (the default) is another substance than "argon": NIST, "For the Lennard-Jones fluid,
linear force shifted at 2.5σ, the critical properties are T c *=0.937" (112 K) against the full potential's 1.3120
(157 K) and argon's 150.7 K; in 2-D T_c ≈ 0.50 ε/k (60 K; M2). `interatomic.ABOUT["conflicts"]` says the 3-D part,
the playground does not, while its presets and inputs are in kelvin of "argon".

Fix: approximations per world: "classical: solid argon below ~80 K (Θ_D = 85 K) and bonds with ħω ≳ kT (ħω/k = … K
for this bond) are quantum"; "the cut potential shifts the phase diagram: T_c = … K here (3-D) / ≈ 60 K in a plane".

### M17 — should-fix — what the crystal's "density" and the gas's "random places" really are

Location: `system.py:233-262` (`lattice`: the smallest lattice with ≥ n sites of the region, the first n sites),
`:490`; `viz.py:142-143` (crystal "Плотность ρσ^d (решётка)"), `:185` (gas help "Атомы в случайных местах без
перекрытий"); p03 README palette rows.

Evidence `r10_p03_melting.out` (1): "atoms 733 = round(0.85 x 862.5); nearest-neighbour distance 1.1296..1.1302
sigma -> lattice density … 0.904; sites of that lattice in the box 780; the widest empty strip across x: 1.694
sigma". `r14_units_and_texts.out` (c): "preset 'maxwell' gas, 300 atoms: distinct x coordinates 30, distinct y
coordinates 20".

The crystal is a lattice of the box's cell counts, denser than asked, with a vacancy strip (what M3's crystal does
at 80 K); the gas starts on a lattice.

Fix: build the lattice with the spacing of the requested density (2-D triangular a = (2/(√3 ρ))^½, fcc
a = (4/ρ)^⅓) in whole cells of the region, or describe it as it is; for the gas either random sequential insertion
without overlaps or the words "on a lattice (it melts by itself)".

## Nits

### M18 — nit — hard world and probes: what is drawn and measured

`viz.py:563`: the velocity histogram uses m = 1 for every hard species (wrong scale for a custom mass); `:496`: all
hard particles get species 0's colour and radius; `:509`: a probe in the hard world shows the global temperature;
`:508-514`: a probe's temperature is taken over the cube c ± r, its density over the ball of radius r (and neither
wraps across periodic faces); `hard.cost_estimate` has no `per_step_s`/`n`, so the cost check shows None and the note
"None атомов". By reading.

### M19 — nit — the field's unit in the help text

`viz.py:179`: "Для аргона единица ≈ 9·10¹¹ м/с²". `r14_units_and_texts.out` (a): "acceleration unit eps/(m sigma) =
7.323e+13 m/s^2 … Earth's g = 1.34e-13 reduced" (the README's 10⁻¹³ is right).

### M20 — nit — "W includes the edits"

`viz.py:584-585` ("работа поршня и правок W") and the p03 README ("W the work of the piston and of the edits"): edits
move E₀ (`system.py:870-871`), W is only the piston's. `r14_units_and_texts.out` (d): "E0 734.9777 -> 1574.4718, W
0.0000 -> 0.0000".

### M21 — nit — degrees of freedom in a slab

`system.py:1536-1541`: `r14_units_and_texts.out` (e): "slab, NVE: P_x -1.332e-15 -> -1.332e-15 (conserved); dof() =
(100, 'd·N: …')". N_f = dN − (number of periodic axes without a field or Langevin bath along them); a 1/(2N) effect
on T (0.2 % for the 233 atoms of `liquid_vapour`).

### M22 — nit — `HardSpheres.pressure()` in a walled box

`hard.py:28-30, 603-617`. `r17_engine_edges.out` (b): "pressure() = 1.1537; walls {'x-lo': 1.2399, 'x-hi': 1.2354,
'y-lo': 1.2365, 'y-hi': 1.2316}". Clausius with the walls' contact planes at σ/2 gives the wall pressure from the
same sums with the length L − σ on each walled axis (1.1537 · 15/14 = 1.236). Say "periodic boxes only" or use the
accessible length.

### M23 — nit — layer placement

`LAYERS.md` §1: `tools` — "not physics: statistics of simulated data". `core.md.observables` (`"layer": "core",
"kind": "statistics"`) holds KS, the DKW bound and block averages next to g(r) and the MSD; the other statistics
modules are `tools.stats` and `tools.bell_stats`. `core.md.hard` carries its interaction (rigid spheres — "as a picture
of real atoms it is a model", its own docstring) inside the core with `conflicts: []`, while the comparable WCA and LJ
terms live in `theories.models`. Move the pure statistics to `tools`, and either name the hard-core model's conflict
(no softness, no attraction: e.g. its phase diagram has no liquid–vapour transition) or keep a `HardCore` term in
`theories.models` that the event engine takes.

---

## Checked and found in order

* **CSVR** (`system.py:1438-1465`) is Bussi et al.'s Eq. (A7) as printed in arXiv:0803.4060 ("α² = e^{−Δt/τ} +
  K̄/(N_f K)(1 − e^{−Δt/τ})(R_1² + Σ_{i=2}^{N_f} R_i²) + 2e^{−Δt/2τ} √(K̄/(N_f K)(1 − e^{−Δt/τ})) R_1"), with
  Σ R_i² drawn as χ²(N_f − 1); half steps at both ends compose to whole steps between consecutive Hamiltonian steps.
  The paper allows local baths: "The formalism can also be trivially extended to thermalize independently different
  parts of the system" (the text interleaves Eq. 11). N_f choices (dN − d only for a global bath in a periodic box)
  are right given P = 0 (M9 otherwise). The arXiv text says nothing about the sign of α; the positive root is the
  common choice and leaves the K distribution exact.
* **BAOAB** (`_step`): B(h/2) A(h/2) O(h) A(h/2) B(h/2) with c = e^{−γh}, √((1 − c²) kT/m) — Leimkuhler & Matthews'
  appendix as quoted in the source file; "For small δt the method is always eventually second order." (grepped).
* **Thermal walls** (`r13_thermal_wall_maxwell.out`, re-emitted velocities recorded from the engine's own
  `_wall_event`/`_process`): normal speed against 1 − exp(−mv²/2T_w): D = 0.0040 / 0.0046 / 0.0241 within the DKW
  bounds 0.0117 / 0.0116 / 0.0279 (MD 2-D, MD 3-D, hard 2-D); against the half-Gaussian D = 0.30 (rejected);
  tangential components within their bounds; mean emitted energy 1.490 T_w (2-D) and 1.994 T_w (3-D) against (d+1)/2.
* **Virial against hard walls** for an LJ liquid: equal within 2.5 % over 160 τ (M13 (A); y 0.2008 against 0.1993,
  x 0.1979 against 0.2027 — presumably the averages' scatter: x-lo and x-hi differ by 1 %).
* **Tail corrections** (`LennardJones.tail`): 3-D U/N = (8/3)πρεσ³[(1/3)x⁹ − x³], p = (16/3)πρ²εσ³[(2/3)x⁹ − x³];
  2-D from ∫r u dr = 4εσ²(x¹⁰/10 − x⁴/4) and p = −(π/2)ρ²∫r²u′dr = πρ²εσ²[(12/5)x¹⁰ − 3x⁴] — derived by hand, equal to
  the code and the test.
* **LJ walls**: the line integrals ∫(1 + t²)^{−6}dt = 63π/256 and ∫(1 + t²)^{−3}dt = 3π/8 give the 10-4 prefactor
  21/80 and ε_w = (3π/8)ρ_wεσ²; the 9-3 form is Steele's (2π/3)ρεσ³[(2/15)(σ/z)⁹ − (σ/z)³]; minima (2/5)^{1/6} and
  (21/32)^{1/6}. Bonded-term derivatives (FENE, harmonic and cosine angles, soft repulsion) checked by hand.
* **Hard-sphere dynamics** (M15's runs): no overlap in 12 × 25 τ, Z_vir = Z_rate (Kolafa & Rottner's Eq. Zrate with
  γ(N)), Z against the corrected KLM reference within 0.7 SE. The estimator Z = 1 + Σr·Δp/(dNTΔt), T = 2K/(dN − d) is
  exactly canonical for hard spheres in NVE (the relative velocity's second moment is 2T/m with this T; the
  configuration distribution is uniform), consistent with Kolafa & Rottner's Eq. (Zvir).
* **Bit-identical restore** (`r18_restore_bit_identical.out`): hard disks with a thermal wall and two species; MD
  with a soft LJ wall, a driven piston, a local Langevin bath, molecules, energy-shifted LJ — positions, velocities,
  counters and the balance equal after continuing.
* **Units**: τ = 2.156 ps, ε/σ³ = 419 bar, ε/σ² = 14.27 mN/m, q0 = e/20.2, ε N_A = 0.996 kJ/mol; the preset piston's
  50 mN/m = 3.5 reduced, ~6 × the gas's own ideal pressure (r14 (b)): a strong compression, as intended.
* **Exclusions, Coulomb refusals, Verlet-list validity (skin/2 on unwrapped displacements), transactions of MD
  edits**: read, no defect found beyond M10 and M14.

## Sources (fetched 2026-11-04 to the session scratchpad, not to this folder; quotations grepped in the text)

* Bussi, Donadio & Parrinello, arXiv:0803.4060 (PDF → text): Eq. (A7); "Since the rescaling procedure does not change
  these quantities, our algorithm samples only the corresponding slice of the canonical ensemble."; "The formalism can
  also be trivially extended to thermalize independently different parts of the system".
* Leimkuhler & Matthews, arXiv:1203.5428: "is always eventually second order".
* Kolafa & Rottner, arXiv:cond-mat/0608356 (LaTeX source; `hdeos.tex`): Eqs. (Zvir), (Zrate), γ(N), (Zenscorr), "the
  first step is already included in formulas (Zvir) and (Zrate)".
* Kolafa, Labík & Malijevský, `hsmd.zip` from old.vscht.cz (text files only, nothing compiled or run): readme "The
  ensemble-corrected Z is ZMD+enscorr/N", "For too small N even this is not enough."; `zfinal.res` "0.50 3.2693735
  0.0000236 0.26179939"; `src/enscorr.c` (`corr`), giving enscorr = 1.02068 at ρ = 0.5 with `zB6_11348`.
* NIST SRS, mmlapps.nist.gov/srs/LJ_PURE/sattmmc_rc25LFS.htm: "For the Lennard-Jones fluid, linear force shifted at
  2.5σ, the critical properties are T c *=0.937, ρ c *=0.320, and p c *=0.0820"; the row "0.75 3.18771E-02 …
  6.93338E-01 …"; index.htm: "T c * = 1.3120(7)".
* Shevchenko & Kulinskii, arXiv:2606.08178v3, Table II and text (the 2-D LJ critical temperatures quoted in M2; a
  secondary source for Smit & Frenkel, J. Chem. Phys. 94, 5663 (1991) and Jiang & Gubbins (1995), which were NOT
  FETCHED).
* arXiv:1304.2049 (Θ_D = 85 K, quoted in M16); arXiv:cond-mat/0606142 (path integrals below Θ_D, quoted in M16).
* Argon's parameters re-checked: arXiv:2511.14399 Table 1 "Ar 6.634 × 10−26 119.8 3.405 × 10−10"; arXiv:cond-mat/0212198
  Eq. (84) "ε1 = 0.01034 eV and σ 1 = 3.405 Å".

No e-mail address or personal identifier was sent with any request (generic user agent).
