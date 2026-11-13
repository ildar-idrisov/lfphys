# p03 — the particles-and-molecules playground

**English** | [Русский](README.ru.md)

A playground section (plan P15.4; framework P15.0: `../RULES.md` §6), on the engine's molecular dynamics
`lfphys.core.md` (P8, batch B7; the owner's subset of 2026-10-29: «молекулярную динамику, решёточный метод Больцмана и
FLRW» — "molecular dynamics, the lattice Boltzmann method and FLRW") with the interatomic potentials of
`lfphys.theories.models.interatomic` (models, injected). The owner's example (2026-10-28): «частицы и молекулы
взаимодействующие» ("particles and molecules interacting"). Matter is built by hand — gas, crystal, atoms, molecules,
walls, a piston, thermostats — changed at any moment, saved to a file and started again from it.

## The laws of a world

A bench that never restarts (LB1, plan P16.1, owner's go 2026-11-11): every law the engine can change at the current
moment is live, changed in "Laws of the world — change at once" with the world kept. World parameters (a change is a new world,
whose scene can be carried over: below):

| parameter | meaning |
|---|---|
| space | a plane or the volume: another world (a plane has no z) |
| boundaries at the start | periodic everywhere, walls everywhere, or walls below and above (periodic sideways); later a "Wall (kind)" or the piston on a periodic axis makes that axis walled at the current moment (below) |

Live laws (review 2026-11-04 UX-ui U12; LB1):

| law | engine | what a change does to the state |
|---|---|---|
| dynamics: continuous forces ↔ hard disks / spheres | `core.md.hard.hard_from_md`, `md_from_hard` | the same atoms (keys), species, positions, velocities, walls and time in the other solver. To hard spheres only when the scene has nothing the hard solver lacks (molecules, a piston, thermostats, a field, soft walls, charges: refused naming the objects), no pair of atoms is nearer than σ_ij (refused with the counts and the closest r/σ; the way out: a lower density — the box is live — or a lower temperature: the turning point of a collision, σ(4ε/E)^{1/12}, comes closer as the collision's energy E rises, so heating makes overlaps deeper; or another moment). The walls act on the atoms' centres in both dynamics (`HardSpheres(walls_on="centre")`, review LB1-physics P4: before, the hard walls acted on the surfaces, so the switch was refused whenever a centre lay within σ/2 of a wall — 170 of 200 moments of a 20-atom gas in a 20σ box — and when made, the region of the centres shrank by σ per walled axis, 7–11 % denser, unstated [error in earlier]): the box is the same region of the centres, the density does not change (said in the event). The potential energy disappears (said in the event). A change of the box still running stops first (said). Back to forces always (the pairs of hard bodies are at or beyond contact, where the pair models are finite): the potential energy appears and the event states the jump; the time step must resolve the temperature present. The palette is the same in both dynamics: what the hard spheres have not is disabled with the reason (`palette_state`); the checks of the other solver are marked "not computed with the dynamics of …" |
| interaction: Lennard-Jones 12-6 or the purely repulsive WCA | `MD.set_pair` | the same atoms, positions and velocities; the potential energy jumps by the difference of the models (the first-law balance moves E₀ by it, as for every edit: its residual is continuous); the conservation references, the MSD origin and the check counters restart; the approximations follow. In the hard world kept and used after a switch to forces |
| cutoff (σ) and shift (force / energy) of Lennard-Jones | `MD.set_pair` | as above; a cutoff with its skin beyond half a periodic box is refused |
| time step (fs) | `MD.set_dt` | the state as it is, the following steps with the new step (the time origin of the steps restarts); a step that the hottest motion present (each species' kinetic temperature, the baths' and thermal walls' temperatures) cannot resolve is refused (below) |
| box sizes Lx, Ly (, Lz), "How to change the box size" and "Time of the size change, ps (0: at once)" | `MD.ramp_box`, `MD.deform`, `HardSpheres.deform` | **affine over a time** (default, 50 ps; review LB1-physics P3): the box goes linearly in time to the new size, by a small affine step after every step of the integrator (`MD.ramp_box`: at most 0.1 % of a length per step, else refused with the shortest time), each step's energy change booked as work — the work is exact and integrated, −∫P dV (the trapezoid of the affine stress over the steps) shown beside it; the event says the faces' speed against the atoms' thermal speed, the view gets the region the change spans, the frames the box reached, and an event at the end the work, −∫P dV and the temperature; a new size or the switch to hard spheres stops a change still running where it is (said). The slower, the nearer the quasi-static adiabat: the argon gas of the Maxwell preset (300 atoms, 300 K) compressed 12 → 11 nm and returned keeps as heat 0.13 ± 0.02 ε per atom (≈ 16 K) by jumps, 0.006 ± 0.005 (≈ 0.7 K) over 10 ps each way, 0.005 ± 0.002 (≈ 0.6 K) over 50 ps, 0.000 ± 0.001 over 200 ps (4 seeds; `proc_p03` measurement in the review's response). Refused also where the end would pack the atoms beyond close packing at contact σ, and stopped where the compression heats beyond what the time step resolves (said). **affine by a jump** (time 0): one canonical affine map — the positions x → λx (the lower face stays at 0) and the velocities relative to the centre of mass (along the axes whose momentum is conserved) v → v/λ: for the motion relative to the centre of mass the canonical point transformation x → λx, p → p/λ (along a conserved axis the centre of mass itself is moved by λ with its momentum kept: the Jacobian of the whole map is λ per such axis; review P9), the volume step of Andersen's barostat in its scaled variables and of the MTK barostat (scaling the positions only, Berendsen's barostat, is not canonical and does no work on an ideal gas). Its energy change is the work; to first order it is −S_aa ΔV with the affine stress S = (2K + W^aff)/V (`MD.affine_stress`: W^aff the virial of every force the map moves — pairs, bonds, Coulomb, the soft walls' z F_z, the field's m g x, frozen atoms included), which is the virial pressure only without a field, soft walls across the axis and frozen atoms (review P2: before, −P ΔV with the virial pressure was shown in all cases and missed by −61 % with a field, +19 % with soft walls, −36 % with frozen atoms [error in earlier]); an ideal gas follows the adiabat exactly (T V^{2/d} = const). A jump is not quasi-static: the matter is out of equilibrium after it and heats irreversibly (above), said in the event. The work is booked in the first law as W (with the piston's), not absorbed in E₀; the event states W, −P·ΔV (or −∫S dV where they differ), the change of the kinetic energy and of the temperature. **wall**: on a walled axis the upper wall (on the piston's axis: the piston's upper stop) moves over empty space at once — a free expansion (Joule), irreversible; no work at specular and thermal walls; next to a soft wall its energy under the atoms changes, which is work, stated in the event (review P8: the event said "no work" with W = +1.15 ε [error in earlier]); space can be removed only where there are no atoms. Refused, with the reason and what fits: a jump that would overlap atoms (the per-atom energy above 50 ε, as for an insertion: the size reachable now is found by bisection with the same 10 % bond limit, review P13, and named), a jump changing a molecule's bond by more than 10 % (the atoms move with the box, so do the bonds: change in steps, or over a time), the cutoff beyond half a periodic box, the piston's axis affinely (move the piston), a wall on a periodic axis, Lz in a plane, a temperature the step cannot resolve after a compression. The hard world: only by a wall — an instantaneous affine jump of hard bodies changes only their kinetic energy (as for an ideal gas) and does none of the work of the collisional pressure. The view gets the new box (a `box` message); the MSD and the hard world's pressure blocks restart; thermostats' regions and thermometers stay where they are in the box's frame |

Scene files and runs written before the split of 2026-11-05 (one world parameter `model` = lj | wca | hard) still load
with the same laws: `"model": "hard"` is read as `dynamics = hard`, lj and wca as the forces with that pair model, and
the world says so in a notice ("a file of the old format …"; `_Schema.resolve`, `legacy_note`).

**A new world takes the scene over** (the framework's "carry the scene over", RULES §6; LB1): each object is placed again
from its parameters (`place`, then the add path): a plane → a volume takes z from the defaults (a region along the
whole z); a volume → a plane drops z, its size and speed (`_import_values`), and a wall or a piston across z is refused
("a plane has no axis z: …"; the framework names what was not carried). The objects' atoms are made anew (a scene keeps
the set-up, not the atoms).

Units: the engine's reduced units with argon's parameters (σ = 3.405 Å, ε/k = 119.8 K, m = 39.948 u; τ = 2.156 ps:
`interatomic.argon_units`, sources in `lfphys/sources/verification_2026-11-04_p8_md.md`); shown in nm, ps, K, bar (in a
plane the pressure is a force per length, mN/m), kJ/mol.

## The palette (all changed at the current moment)

| object | engine | parameters |
|---|---|---|
| gas | `MD.fill(..., arrangement="random")` (random places, none nearer than σ to another atom: random sequential insertion; Maxwellian velocities at T, the gas's momentum removed; or equal speeds) | number, temperature, region, the centre-of-mass velocity (a throw), the substance (argon or σ, ε, mass, charge relative to argon) |
| crystal | `MD.fill(density=…)` (`crystal_sites`: a perfect triangular / fcc lattice with the spacing of that density, whole cells in the region; along a periodic axis the block spans, the cells are fitted to the box and the actual density and strain are shown in the inspector) | density ρσ^d, temperature, region, centre-of-mass velocity, substance |
| atom | `MD.add` | position, velocity, substance |
| molecules | `MD.add_molecule` with harmonic bonds and angles (two-atom, bent three-atom, chains; random places and orientations, each atom's energy at insertion below 2kT); start "everything at T (translation, rotation, vibration)" (each atom Maxwellian, bond lengths and angles drawn with their Boltzmann spread) or "translation only at T (rotation and vibration cold)" (each molecule moves as a whole at T, rotation and vibration cold); the object's momentum removed | count, start, bond length and stiffness, angle and stiffness, temperature, region, centre-of-mass velocity, substance |
| wall | `MD.set_wall` (specular, soft Lennard-Jones 9-3 / 10-4, thermal: re-emits atoms at its temperature — a heat bath) | axis, side, kind, temperature |
| piston | `MD.set_piston` (the upper wall of an axis moves: its mass and the external pressure, or driven at a speed) | axis, position, mass, pressure, speed |
| thermostat | `MD.add_thermostat` (CSVR or Langevin, everywhere or in a region) | kind, temperature, relaxation time or friction, region |
| field | `MD.set_gravity` (a model field: Earth's gravity is ~10⁻¹³ in argon's units) | g in ε/(mσ) |
| thermometer | `probe`: the number, the density (over the ball's part inside the walls) and the temperature of the atoms in a ball (periodic faces wrapped) | centre, radius |

**Where a new object lands** (review UX-ui U4–U8; the framework's `place`, asked for every palette object, and the
section's checks at every add and edit): an atom goes to the nearest free spot (no atom nearer than σ_ij, inside the
walls by σ/2, below the piston; a fine grid around the asked point, then a coarser one over the box), a copy (⧉) of an
atom likewise; a crystal fills the free sites of its lattice and leaves those nearer than σ_ij to atoms already present
empty (`MD.fill(..., skip_occupied=True)`; the count is in the inspector and a note); a piston goes above the highest
atom on its axis; a clicked point is an atom's place, a region's centre (a third of the box when no size is set), or
the nearest face for a wall or a piston. A wall or the piston on a periodic axis makes it walled (`MD.set_boundary`:
specular walls at 0 and L; the pairs across the faces stop interacting, an edit booked in the first-law balance); when
the last wall or piston on that axis goes, the axis is periodic again (or stays walled, with a note, when atoms across
the joined faces would overlap). A gas or molecules denser than random insertion can place (covered fraction above
0.50 / 0.35 for atoms, 0.40 / 0.28 for molecules, in a plane / the volume, with the atoms already in the region) are
refused at once with the count that fits. An atom moved by hand onto another or outside the walls is refused with the
nearest free spot.

**Temperatures the time step resolves** (UX-params P32): the rms step v dt must stay within Q_MAX = 0.4 of the distance
r_t / 12 in which the 12-6 repulsion rises by kT near its turning point r_t = σ (4ε/kT)^(1/12) (q = 12 v dt / r_t);
measured on an LJ gas (2-D and 3-D, 200 atoms, 10 fs, three seeds, 3000 steps): q ≤ 0.36 keeps the energy error below
0.6 % of kT per atom, q ≈ 0.45 gives 0.02–5 %, at q = 0.58 two of three 2-D runs crashed, as did every run at 10⁵ K
(q ≈ 3.5). An object (gas, crystal, molecules, an atom's speed, a thermostat, a thermal wall) beyond it is refused with
the largest temperature at this step and the step for this temperature; at 10 fs argon is resolved up to about 2400 K
(2-D). Hard spheres have no step.

**Molecules in one edit** (U5, P33): the candidates for all the molecules still missing are drawn at once (random
places, orientations, Boltzmann bond lengths and angles) and inserted in one engine edit (`MD.add_molecules`: a
candidate closer than 0.9 σ_ij to an earlier one is left out, then every candidate over the energy bound 2kT, the first
ones in order kept), repeated until all are placed (at most 200 tries per molecule); a removal takes all the object's
atoms in one edit. The gas's random sequential insertion is vectorised in the engine (`random_sites`: the same points as
one at a time). An advance call is cut to the steps the modelled cost (`md_step_model`) allows in 40 ms, so a large
scene keeps the frames and the commands flowing.

**Refusals in the owner's terms** (U13, P4, P31): the engine's refusals (overlap, jammed placement, a periodic cutoff,
charges with a periodic axis, the region, the walls) are rewritten at the section's boundary as translated texts with
what to change, shown in the viewer's language (`lfviz.errors.Refusal`; the engine's sentence kept as the detail).

A change of an object's substance keeps its atoms (the same atoms with new parameters at the current moment, at the
same temperature: a mass change rescales the velocities by √(m/m′); a larger σ that makes atoms overlap is refused);
a change of their number, region, temperature or shape makes them anew. Every change is all or nothing: when the engine
refuses any part of it, the world is put back bit for bit as it was (the engine's state and the wrapper's maps are
saved before the change). A piston's edit acts on the piston where it is (its position only when "Position, nm" itself is
edited). Charges are only allowed in a box with walls on every
side (the engine sums the Coulomb forces directly; it refuses them with a periodic axis). Molecules, pistons,
thermostats and fields are not in the hard-sphere world (that engine has none of them): their palette buttons are
disabled there with the reason (switch the dynamics to forces), and the switch to hard spheres names them.

## Direct manipulation (LB1, plan P16.2)

Handles (`ObjectType(handles=…)`; the player's drag and throw, sent as the scene op `edit`): a gas, a crystal block, a
molecule object and an atom have a position (x, y, z) and a throw (`throw_vx`, `throw_vy`, `throw_vz`: hidden parameters
in the world's units, nm per second of world time, as the player computes a throw from `at` and the time; the object's
velocity vx, vy, vz in m/s is set from them — review LB1-p02-ux X4: the player's 1.9·10¹² nm/s had been taken for m/s and
refused [error in earlier]) with the largest throw `velocity_max` = 500 m/s (5·10¹¹ nm/s): about the speed of sound of
argon gas at room temperature, above its thermal speed; the default step (10 fs) resolves a 300 K argon group thrown at
it (q = 12 v dt / r_t = 0.34 in a plane, 0.37 in a volume against Q_MAX = 0.4; tested), a hotter, lighter or faster one is
refused by the step with what to change; a thermometer a position and its
radius for picking; the piston one coordinate along its own axis (its "Position, nm"). Every positioned object is in the
frame's `at` (nm, three numbers; a plane at z = 0): a group's centre — the mean along a walled axis, the circular mean
along a periodic one (the middle of the box when the group spreads over the whole axis) —, an atom's place, a
thermometer's centre, the middle of the piston's face, a regional thermostat's region centre.

* A drag of a group translates all its atoms as a whole so that its centre is at the new place (along the coordinates
  sent; computed from the atoms now, never from the stored values: the stored place is where the group was set); its
  velocities are kept. Refused, all or nothing, where an atom would leave the walls (with the centre's range that fits)
  or come nearer than σ_ij to an atom of another object (an atom: with the nearest free spot); the engine checks the
  energies too. A drag of an atom moves it and keeps its velocity.
* A throw sets the group's centre-of-mass velocity (one species per object: equal masses; the motion about the centre
  kept); an atom's velocity likewise, its place kept; a speed the time step cannot resolve (the thermal speed plus the
  centre's) is refused. New groups take vx, vy, vz from their form (default 0: at rest as a whole).
* Each is one engine edit (cheap: measured below); the first-law counters restart as at every scene change.

## Instruments: measurables (LB1, plan P16.3)

`measurables()` (sent by the framework in every `scene` message) and every frame's `meas` (`meas_note` for a value that
is undefined now; NaN travels as null), also `measure()` for the sweeps: the world's temperature (K), pressure (bar;
mN/m in a plane: the virial, for hard spheres the collisions' since the last change), energy per atom (kJ/mol), the
number of atoms, the number density (nm⁻³ / nm⁻²) and ρσ^d, the box's volume (area), the first law since the last change
of the scene (Q, W — the piston's and the box's work —, E − E₀ and the residual, kJ/mol of the whole system), the total
momentum (u·m/s), the bond-orientational order (|⟨ψ6⟩| or Q6; it costs 1–3 MD steps, so it is computed once per
picosecond of world time — by time, not by frames, so that a frame drawn again at the same moment shows the same — and
is NaN with a note in the frames between) and the mean-square displacement (nm²); per thermometer the atoms, the density and the temperature in its
ball; per piston its position (nm), the gas's mean force on it since the last change (pN) and its speed (m/s); per
molecule object the temperatures of its modes (translation, rotation, vibration, bonds, angles); per particle object its
atoms' temperature. Cost: a 2-D gas of 2000 atoms, 1.7 ms per frame for all of them (one MD step of it 0.8 ms; a frame
advances up to 400 steps in at most 40 ms).

## What the player shows

The 3-D scene: the atoms as spheres of radius σ/2 of their substance (positions from the run, 16-bit over the box:
drawing only), the molecules' bonds, the piston's face, the walled faces ("Walls of the box"). "Statistics": the velocity components divided by √(kT/m) of
their own mass against the standard Gaussian (the Maxwell–Boltzmann distribution), the radial distribution function
g(r), the density along y (the field's axis, slabs of about σ), the temperature, the pressure (MD: the instantaneous
virial; hard disks: the collision virial since the last change) and the energy per atom in time, the
bond-orientational order (|⟨ψ6⟩| in a plane, Steinhardt's Q6 in the volume, neighbours nearer than 1.5σ) and the
mean-square displacement since the last change (a crystal against a liquid), the molecules' mode temperatures
(translation, rotation, the vibration's kinetic energy, the bonds' and angles' potential energy: `MD.molecule_modes`;
also in the inspector).

## What the presets show (measured, review B7-md)

| preset | what the run shows |
|---|---|
| maxwell | 300 atoms at random places with one speed: the velocity components become Gaussian (KS within the DKW bound by 20 ps) |
| melting | a perfect triangular crystal of ρσ² = 0.85 (the box holds 25 × 15 cells) heated by CSVR to 120 K = 1.00 ε/k, where the 2-D LJ (2.5σ) fluid exists below ρ ≈ 0.896 (Li & Pica Ciamarra 2020): |⟨ψ6⟩| 1 → 0.44 at 20 ps → 0.07–0.29 later, the MSD 1.4–1.9 σ² per 20 ps (diffusion). At 20 K the crystal stays (0.92, 0.02 σ²); at 80 K (0.67 ε/k) it does not melt in 600 ps (0.61–0.75; the reviewed preset's bath) |
| piston | a free piston compresses the gas against the external pressure while a thermal wall exchanges heat: Q and W in the first-law check |
| liquid_vapour | 3-D (slab, field 0.02 ε/(mσ)) at 90 K = 0.751 ε/k, inside the coexistence region of the force-shifted model (T_tr 0.560, T_c 0.937: Errington et al. 2003): the density profile settles into a liquid of ρσ³ ≈ 0.69 (NIST 0.693) under a vapour of ≈ 0.02 (NIST 0.032 without the field), the interface a few σ wide, Q6 ≈ 0.04 (a liquid). At 120 K (supercritical) a graded fluid without a plateau. In a plane 90 K = 0.75 ε/k lies far above the 2-D critical temperatures found (0.515 full, 0.459 energy-shifted), and the reviewed 2-D preset showed a graded fluid |
| molecules | 150 dimers (k = 50 ε/σ², ħω/k = 35 K) start with translation only at 400 K: within 10–20 ps translation, rotation, the vibration's kinetic and the bonds' potential energy all settle near 199 K (equipartition: 3 + 2 + 1 + 1 quadratic terms) |
| hard_disks | 400 disks (ρσ² = 0.322): Z of the run against Kolafa & Rottner's equation of state with the ensemble correction for N = 400 (1.8045); measured 1.807 over 100 ps, within 5 block SE |

## Running checks

The first law (`energy_balance`) since the last change of the scene: E − E₀ = Q + W + the residual, Q the heat from
the baths and thermal walls, W the work done on the system — the piston's and the box's affine changes' (`W_box`: a
change of the box goes on in the balance, it does not restart it) — (an edit of the scene moves E₀ by the energy it
changes); in the hard world E is the kinetic energy and E − E₀ = Q to rounding; the residual is the
integrator's error (information, with the companion's estimate for a deterministic world): O(dt²) with continuous
forces; at hard walls and the piston with interacting atoms an impulse inside the step leaves an error of order F v dt
per hit that accumulates: first order in dt (the piston preset: a residual of 1–14 ε over its first stroke at 2.5–10
fs, at most about 1.5 % of the work; an LJ gas in a walled box: 0.6 / 0.33 / 0.19 ε at 10 / 5 / 2.5 fs against 0.06 /
0.02 / 0.006 ε when periodic; exact for an ideal gas). The total momentum along the axes where it is conserved (periodic, no field along them, no thermal wall, no
Langevin or local bath, no frozen atoms): its change since the last change of the scene against a worst-case bound of
its rounding (`MD.momentum_drift`; pass/fail). The Kolmogorov–Smirnov distance of all velocity components, each divided
by √(kT/m) of its own mass, from the standard Gaussian with its DKW bound (in equilibrium within it). The virial
pressure against the momentum given to the walls (with frozen atoms the virial is defined along walled axes only).
Hard disks / spheres in a periodic box of one species: Z against the equation of state of the fluid (Kolafa & Rottner
2006 for disks up to ρσ² = 0.88, Kolafa, Labík & Malijevský 2004 for spheres up to ρσ³ = 0.90) with the ensemble
correction for the run's N, from blocks of at least 2.2 ps after 10.8 ps (pass/fail from 10 blocks: 5 standard
errors + 1e-4). The cost per step (per event for hard spheres).

## Approximations and limits

* Classical mechanics of atoms: solid argon is quantum below its Debye temperature Θ_D = 85 K (the Debye heat capacity
  at 20 / 40 / 80 K is 0.47 / 0.81 / 0.95 of the classical one); a bond with ħω ≳ kT is quantum (the approximations
  give ħω/k of each molecule object: 100 K for k = 400 ε/σ², 35 K for k = 50 ε/σ²).
* The interactions are models: Lennard-Jones with argon's parameters cut at r_c is another substance than argon — the
  force-shifted 2.5σ model has T_c = 0.937 ε/k = 112 K and its triple point at 0.560 ε/k = 67 K in 3-D (the full
  12-6: 1.312 = 157 K; argon 150.7–150.9 K); in a plane the full 12-6 has T_c = 0.515 ε/k = 62 K, the energy-shifted
  2.5σ model 0.459 = 55 K with its triple point near 0.42 ε/k = 50 K: liquid and vapour coexist in a plane only in a
  narrow window; for the force-shifted model in a plane no value was found (sources:
  `lfphys/sources/verification_2026-11-04_p8_md.md` §1, §8).
  Harmonic bonds and angles; hard disks / spheres have no attraction (no liquid and vapour).
* A plane is two-dimensional matter (its phases and its equation of state are two-dimensional).
* A scene file keeps the set-up, not the atoms: a world started from a file makes them anew. A scene carried into a new
  world (`carry_state` / `carry_world`, review LB1-framework F5) takes them over where the space is the same: every
  atom's position and velocity, the molecules whole (one that crossed a periodic face now a wall is moved inside as a
  whole, said), the piston's face and velocity, and the random generators (the thermostats', the thermal walls', the
  hard spheres' draws continue); in a box of another size the atoms stay where they are when they fit; otherwise, and
  from a plane into a volume or back, the object is made again from its parameters and the notice says why (before, every
  carried object was regenerated while the notice said "all objects" [error in earlier]). The first law's balance, the
  momentum reference and the MSD count from the new world's start (its laws may give another energy). A world starts
  its solver at its scene's time (before, at 0: the first advance computed the whole interval up to the scene's time
  over the scene's atoms [error in earlier], found while processing F5).
* A live box change over a time is a uniform strain rate applied by small affine steps between the integrator's steps
  (the face of the box is not a moving wall: the matter is strained everywhere at once, as by a barostat); its
  quasi-static limit is the adiabat, a finite rate dissipates (measured above). A jump (time 0) is irreversible; the wall
  mode is a free expansion. Molecules are scaled atom by atom (a jump: at most 10 % per change; a slow change: the bonds
  relax as it goes).
* The switch to hard spheres needs every pair at or beyond contact: a liquid near its triple point rarely allows it
  (there are always pairs inside σ); a dilute or cold gas does.
* Open items: `../../STATUS.md`.

## Latency of the live changes (worker side, CPU, measured 2026-11-11)

| change | 2-D gas 200 | 2-D gas 2000 | 2-D gas 8000 | other |
|---|---|---|---|---|
| Lx affine (−3 %) | 2.5 ms | 4.5 ms | 10.9 ms | 3-D gas 3000 walled: 26 ms; 3-D 150 dimers +4 %: 4 ms |
| Lx by a wall | | | | 3-D gas 3000: 21 ms |
| drag of a gas | 2.0 ms | 4.6 ms | 13.6 ms | 150 dimers: 7 ms; hard disks 400 / 4000: 50 / 330 ms |
| throw of a gas | 1.6 ms | 3.3 ms | 9.3 ms | |
| pair model | 1.8 ms | 3.2 ms | 7.9 ms | |
| hard → forces | | | | 400 / 4000 disks: 4 / 13 ms |
| forces → hard | refused (pairs inside σ) in 9 / 6 / 23 ms | | | 400 / 4000 disks just back from hard: 59 / 400 ms |

The hard solver's edits rebuild its event calendar from every particle (a Python loop): they cost 0.1 ms per particle.

## Tests

`tests/test_p03_lab.py` (LB1): the box changed affinely by a jump (positions × λ, velocities about the centre ÷ λ, W = ΔE
in the first law, the residual kept, the event's texts, the `box` message, the world running on) and over a time (the
start's event, the region, an intermediate box mid-way, the end's event with its work equal to the booked W_box, the
final box; a new size stops a change running, a too fast one and one beyond close packing are refused; the switch to
hard spheres stops it); the wall mode next to a soft wall states its work (a specular control says none); the
bisection's trials carry the bond limit (the control without it names 30 %); the switch in a walled box with an atom
0.05 nm from a wall keeps every position (walls on the centres); the largest throw resolved by the default step in a
plane and a volume, three times as fast refused; a scene carried into a new world of the same space with its atoms
(positions, velocities, kinetic energy and the generator bit for bit), molecules and the piston with their state, a
plane ↔ volume and a smaller box made again with the reason (controls); the refusals (overlap with
the size that fits, bonds beyond 10 %, a wall on a periodic axis, Lz in a plane, the piston's axis, below the piston,
atoms beyond a moved wall) leaving the world bit for bit with the live value rolled back; the wall mode as a free
expansion; the hard world only by a wall; the dynamics hard → forces → hard (keys, positions, velocities, time, the
jump; or the refusal with its count); the blockers named (molecules, a thermostat); a dense liquid refused with the
count; the handles in the palette; a gas dragged and thrown (rigid translation, centre-of-mass velocity), refused onto
other atoms and through a wall; an atom dragged (velocity kept) and thrown (place kept); the thermometer and the piston
dragged; `at` for every positioned object and `meas` for every measurable (NaN only with a note), their values against
the engine; the cost of `meas`; a scene carried from a volume into a plane (the z-wall refused) and back; a restore
repeating a box change, a switch, a drag and a change of the box still running: the whole engine state bit for bit (a
velocity one unit in the last place off is seen: the control; review LB1-physics P11). `tests/test_p03_ux.py` (reviews 2026-11-04 UX-ui and UX-params): the hard world with one atom at rest runs (pressure 0,
no Z); equal speeds with one atom or at 0 K; a temperature beyond the step refused, a control taken, a shorter step
(live) takes it, a longer one refused again; a wall and a piston on the default periodic box (the axis walled and back);
atoms on free spots, an occupied or outside place refused with the nearest free one; a crystal around a gas; molecule
edits within time bounds (and dense ones refused at once); a large gas refused with the count that fits; the live pair
model, cutoff and step with the first-law residual kept; a cutoff beyond half the box; charges refused in the owner's terms
(every part translated) and taken once walled; live laws and placements rebuilt by replay; the palette's state.
`tests/test_p03_molecules.py`: every preset builds, runs and keeps its laws, and shows what its label says (the table
above, each with a negative control: 20 K for melting, 120 K for liquid and vapour, the start for the molecules, a 5 %
denser reference for the hard disks); argon's units (τ = 2.156 ps, the pressure unit 418.9 bar); equal speeds become
Maxwellian by collisions; the molecules start at T; the molecules' bonds; a substance change keeps the atoms and their
temperature; a refused change leaves the world bit for bit (two kinds of refusal, a twin compared after it); refused
molecules leave none; removing the first object; the momentum check and its negative control; the piston kept where it
is; the hard world's edits and crystal; the texts; the scene file. The physics: `lfphys/tests/test_md*.py` (the box
and the switch: `test_md_deform.py`). The shared tests continue a world from its
checkpoint byte for byte and rebuild it by replay.
