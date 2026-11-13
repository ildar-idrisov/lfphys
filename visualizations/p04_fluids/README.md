# p04 — the fluids laboratory

**English** | [Русский](README.ru.md)

A laboratory section (plan P15.7; framework P15.0: `../RULES.md` §6), on the engine's lattice Boltzmann solver
`lfphys.core.fluids.lbm` (P8, batch B7; the owner's subset of 2026-10-29: «молекулярную динамику, решёточный метод
Больцмана и FLRW» — "molecular dynamics, the lattice Boltzmann method and FLRW"). The flow is built by hand —
obstacles, inlets and outlets, moving walls, dye, probes — changed at any moment in the inspector, saved to a file and
started again from it.

## The laws of a world

World parameters (a change is a new world; "carry the scene over" carries the objects over):

| parameter | meaning |
|---|---|
| fluid at the start | the DFG benchmark fluid (ν = 10⁻³ m²/s, ρ = 1 kg/m³; the default), water or air at 20 °C (density and viscosity from `lbm.fluid_properties`: water from the NIST WebBook's IAPWS-95 / IAPWS 2008 isobar, air from the U.S. Standard Atmosphere 1976 with Sutherland's viscosity), or ρ and ν of one's own; it sets ρ and ν at the start (both live afterwards) |

Live laws (review 2026-11-04 UX-ui U12: "Set-up — changes at once", changed at the current moment, the flow kept; plan P16.1, batch
LB1: the bench never restarts):

| law | engine | what an edit does to the state |
|---|---|---|
| viscosity ν | `Flow2D.set_viscosity` | τ changes, the time step stays; the populations (density ratio and velocity of every node) are kept: mass and momentum do not jump; the viscous stress carried by the populations' non-equilibrium part is the old τ's and adapts within a few steps; refused below what the grid carries (τ − ½ ≥ 10⁻³, the cell Reynolds limit), with the smallest ν |
| density ρ | `Flow2D.set_density` | the lattice state is kept, the velocities are the same; pressures, forces, mass and momentum change their physical scale by ρ′/ρ (a flow given ρ′ half-way equals one that had it from the start, bit for bit: engine test); the balances' relative residuals do not change |
| collision operator TRT / BGK | `Flow2D.set_collision` | the populations kept, the next steps relax with the other odd-moment rate (same equilibrium, same viscosity) |
| dye on / off, its diffusivity | `enable_dye` / `disable_dye` / `set_dye_diffusivity` | off: the dye field goes, its amount booked as removed (the dye balance closes again when it is switched back on, zero); refused while dye sources are in the scene; "0: as the viscosity" follows ν |
| nodes along x (nx) | `Flow2D.remap` | the spacing dx = Lx / nx changes (ny follows: the same spacing along y); the flow is moved to the new grid: the next step's streaming is done on the old grid, its pre-collision populations split into the equilibrium of their density and velocity and the non-equilibrium rest; the pressure (kept as a physical pressure: the lattice density deviation scales by (c/c′)²), the velocity and the non-equilibrium part are interpolated (four-point cubic where its 4 × 4 stencil is fluid, bilinear near bodies; beyond the sides quadratic ghosts: a Poiseuille profile is carried exactly), the non-equilibrium part rescaled with the relaxation times and the time step (Dupuis & Chopard 2003 — the grid-refinement transfer of the pre-collision populations, which has no singularity at τ = 1, unlike the post-collision rescaling of Filippova & Hänel 1998; their factor τ′dt′/(τ dt) for the symmetric part, τ₋′dt′²/dx′ / (τ₋dt²/dx) for TRT's antisymmetric part — derived here, the same in their convective scaling), and the new grid's collision completes the step (the change takes one step of the old grid); bodies and dye sources are re-voxelised; the time step follows u_max as for a new world |
| domain length Lx, height Ly | `Flow2D.remap` | the spacing kept, cells added or cut on the side "The domain grows or shrinks" names (right and top: the objects keep their coordinates; left and bottom, or both sides: the objects move with the fluid and their coordinates change by the shift, the scene says so); a new part of the domain is fluid at rest (the pressure of the nearest node and the body force's hydrostatic part) or moving with the first inlet's velocity ("New part of the domain"); a crop that would cut a body or a dye source, or leave a probe or a dye drop outside, is refused with the object named; a whole-cell shift at the same spacing copies the fluid exactly |
| largest expected speed u_max | `Flow2D.remap` | the time step from the lattice Mach number (0.1 at u_max, capped at τ ≤ 1) and with it the scheme's sound speed; the fields are carried node by node, the non-equilibrium part rescaled; refused when the grid does not resolve it (the cell Reynolds limit) or the scheme cannot carry the speeds in the scene (Mach 0.3) |

Every grid change is all or nothing (a refused one leaves the flow, the time and the books as they were), is checked
against the memory budget first (the new grid's steady size against the worker's budget, then the remap's peak,
`Flow2D.remap_memory_estimate`, through `lfviz.limits.require`), and is a recorded command, so a world rebuilt by replay
repeats it bit for bit (test). Its event states the grids, the time steps and τ before and after, the mass and momentum
before and after, and what the transfer itself changed, with its parts (review LB1-p02-ux X14): the scheme's
compressibility — the pressure is kept, so a new time step changes the scheme's density p/c_s² and with it the lattice
mass (u_max 0.6 → 0.15 m/s: c_s ÷ 4, the density deviation × 16, +1.9 % of the mass: not a change of the fluid; the
event computes it from the pressure integral and gives the incompressible fluid's mass ρ·S), the fluid of a new part of
the domain, the interpolation and re-voxelisation. A new nx that does not fit a whole number of cells into Ly changes the
height: the event gives the new height and the nx that keep both lengths, and says when the DFG set-up is no longer
recognised (review LB1-physics P14; before, the 0.39 mm change at nx 333 went unsaid). The transfer is booked as
`remap`, so the running balances close **by construction** across it and cannot see an error of the transfer itself
(review LB1-physics P7: a velocity transferred 1 % wrong passed every running check; before, this README and the test
cited those checks as evidence for the transfer [error in earlier]); the event says so. The transfer is checked by the
engine's tests against closed forms and, in a world, by "Benchmarks": the body-force Poiseuille channel (below) stays on its
parabola to round-off across nx, Lx, Ly and u_max changes and is off by ~10⁻² after a wrong transfer (test). Each live
change restarts the
force record's window and re-emits the approximations. Measured latency of a change on the CPU (the whole command in the
world, its picture included; 2026-11-11): nx 440 → 880 on the DFG channel (36 k → 144 k nodes) 0.20 s, back 0.19 s,
u_max 34 ms, the domain grown or cropped 90–100 ms; in the browser the event is shown 0.2 s after the command. A body
dragged 27 ms, a probe 1 ms.

**A fluid the grid cannot resolve** (UX-params P24): water and air on the default 2.2 m channel at 0.45 m/s were refused
(τ − ½ = 8·10⁻⁵, a cell Reynolds number of 149). The world now lowers the largest expected speed to what the grid
resolves, u_max = 0.9 · 10 ν / dx (cell Reynolds number 9, below the open-domain limit 10), says so in a notice and in
the approximations, and records the lowered value as the world's law; the palette's speeds follow (a fifth of u_max):
water on the 5 mm grid runs at speeds up to 1.8 mm/s (the default 8 cm cylinder at the default inlet speed 0.4 mm/s: Re ≈ 33), air up to 2.7 cm/s. The trade-off:
for faster flows a smaller domain or more nodes — the presets "Water: …" (a 22 × 4.1 mm channel, D = 1 mm, 3 cm/s) and
"Air: …" (22 × 4.1 cm, D = 1 cm, 4.55 cm/s) are the DFG 2D-1 set-up at Re = 20 in these fluids.

**The grid's memory** (UX-params P25): a thin or tall domain made grids of 8·10¹⁰ nodes (591 GiB) that the worker tried
to allocate. The world estimates its peak memory before anything is allocated (`Flow2D.memory_estimate`: 1000 B per node
with the dye, 800 without — measured 840 / 632 B at 10⁶ nodes) and refuses above the worker's budget (the framework's,
or 6 GiB) with the nodes, the memory and what to change (the largest nx, the smallest Lx); the framework asks the same
estimate (`estimate_bytes`). A grid that fits but is slow keeps its frames short: an advance call is cut to the steps the
CPU's rate table allows in 0.1 s (one step for 4·10⁶ nodes), and a step above 0.25 s is named in the approximations.

The engine refuses a world it cannot run stably and says why (Mach > 0.3, τ − ½ < 10⁻³, a cell Reynolds number
u·dx/ν above 25 in a closed or periodic domain or above 10 with an inlet or an outlet — stability edges, not accuracy:
the cavity at Re 1000 on 64² is accepted at 15.6 and lies 0.017 of the lid speed off Ghia's table). It also refuses an
outlet pressure or a body force whose rest state would make the scheme's density deviate from ρ0 by more than 0.045
(the pressure scale is c_s²ρ: 20 Pa in the default world). The section puts these refusals in its own terms: the speed
limit of this world, the smallest ν, the u_max that would carry a force (never `dt`, which is not a parameter here).

## The palette (all changed at the current moment)

| object | engine | parameters |
|---|---|---|
| cylinder, rectangle, NACA four-digit wing profile | `add_obstacle(Disk / Rect / Polygon)` (half-way bounce-back, or Bouzidi's interpolated walls for a fixed surface); **the bodies stay where they are**: a "surface velocity" is imposed on the fixed shape (Ladd) — its part normal to the surface makes the front a source and the back a sink; a turning disk's surface is tangential (a rotating cylinder) | position, size, angle (the profile: code, chord, leading edge, angle of attack), the wall (staircase or interpolated), surface velocity, surface rotation, the length and speed for the coefficients (0: the width across the flow; a value set back to 0 returns to it) |
| inlet, outlet, moving wall, periodic sides | `set_sides` (velocity inlet uniform or parabolic with a ramp and dye — a ramp per side, which blends from the side's former velocity to the new one; an edit of the dye alone keeps the inflow; pressure outlet, its pressure at the middle of its side plus the hydrostatic part of a body force along it; a wall moving along itself; a periodic pair) | side, speed, profile, pressure |
| body force | `set_gravity` (Guo's forcing; the fluid takes the hydrostatic pressure at once) | g |
| dye | `add_dye_source` (keeps a concentration) or `add_dye` (a drop once) | position, radius, concentration |
| velocity probe | the fields at the nearest node | position |

**Handles** (plan P16.2): cylinders, rectangles, wing profiles (by the leading edge), dye sources and drops, and probes are
dragged in the plane (their x, y; a cylinder and a dye spot also picked by their radius); a body dragged is re-voxelised at
once (the nodes it leaves start as fluid at their neighbours' density, the ones it covers book their fluid as in any
edit), a dye drop dragged falls again at the new place. Every frame carries `at[id]` = (x, y, 0) of each of them.

**Where a new object lands** (UX-ui U4, U7, U8; UX-params P27; the framework's `place`, asked for every palette
object): the defaults are made for the world (a body a tenth of the shorter side, a quarter along x on the centre line;
speeds a fifth of u_max; the body force the largest the scheme carries up to 9.81 m/s², `Flow2D.gravity_limit` — in
the default world 4.3 m/s² (with walls on every side), and a note names the u_max that would carry 9.81); a side object takes its side when free,
else the first free one (a note says so), a periodic pair the free pair; a body that would cover another moves to the
nearest place where it does not (a copy ⧉ likewise); a clicked point is the object's place (a side object's nearest
side); a probe or a dye spot asked inside a body goes to the nearest fluid node; speeds above what the world resolves are
reduced to it with a note. An edit by hand is checked as it is: a body wholly outside the domain, a probe or a dye spot
outside it, a body covering 90 % of it, a side already taken (the free sides named), a force or a speed beyond the
scheme are refused in the owner's terms with what to change; a body partly outside is accepted with a note (the wall cuts it). A
probe inside a body says "inside the body “…”: there is no fluid here; move the probe" instead of NaN.

One condition per side; removing an inlet, an outlet, a moving wall or a periodic pair gives the walls back. The NACA profile is the four-digit series of Abbott & von Doenhoff (1959) with the closed trailing
edge; a positive angle of attack lowers the trailing edge for a stream along +x.

## Presets

| preset | set-up | what to compare |
|---|---|---|
| cylinder, Re 20 | the DFG 2D-1 channel (Schäfer & Turek 1996), interpolated disk, D = 20 cells, inflow ramped over 3 s, u_max = Um (as the engine's test) | the mean C_D, C_L over a sound period against Table 3 (5.5700–5.5900, 0.0104–0.0110): the start's ringing decays by ≈ 40 % per period (2.93 s), so the one-period mean still strays up to ±0.007 at 14 s and ±0.002 at 20 s; settled, 5.5895 / 0.01050 — inside, at the upper edge (D = 40, 880 nodes: 5.5791 / 0.01077); the staircase disk at this grid lies outside (≈ 5.637 / 0.0113) |
| Kármán street, Re 100 | the DFG 2D-2 channel, interpolated disk, 880 nodes (D = 40 cells; the developed flow's cell Reynolds number ≈ 5.6, below the open limit 10) — heavy on the CPU, about real time on GPU 0 | St, C_D max, C_L max against Table 4: St inside; C_D max (3.248) and C_L max (0.980) outside at this grid, the cause open (STATUS V41 p) |
| cavity, Re 100 | lid-driven square, 192² | the centre-line profiles against Ghia, Ghia & Shin's tables (0.005 / 0.008 of the lid speed once steady, ≈ 25 s) |
| channel and plate | a parabolic inlet, a plate across 40 % of the channel, a probe 2.5 H upstream | the probe column's profile against the inflow's parabola (the difference holds the scheme's compressibility error, shown next to it) |
| wing profile | NACA 2412 at 8° with periodic top and bottom: **a cascade** of profiles 2 chords apart, not an isolated wing | the forces of a cascade |
| water, air | the DFG 2D-1 set-up at Re = 20 in water (22 × 4.1 mm, D = 1 mm, Um = 3 cm/s) and in air (22 × 4.1 cm, D = 1 cm, Um = 4.55 cm/s), 440 nodes, interpolated disk | the same flow in units of D and U (the benchmark's check appears only for its own fluid and metres) |

## What the player shows

The window of the plane is the main view (UX-ui U15: it was a side window next to a 3-D view of the flat slab): the
field chosen across the whole centre; the 3-D scene beside it on request ("Show the 3-D view alongside"). The 3-D scene (z up): the field chosen ("Flow picture": speed, vorticity — signed, zero in the middle of the scale —,
pressure, dye) as an image on the plane, the velocity arrows, the obstacles as prisms; the window of the plane with
the obstacles' outlines, the sides' conditions (inlets green, outlets orange, moving walls violet, periodic dashed), the
dye sources and the probes; the laboratory's panels. The picture averages the fluid only over each of its points, each
point covering an equal share of the domain (beyond 512 points per axis); the window marks it as an approximation. The
field shown is a view request (`view` op `field`): it never changes the world's physics.

## Instruments (plan P16.3)

`measurables()`: per body the drag and lift coefficients over the last step (with the scheme's standing sound wave)
and averaged over the domain's slowest sound period (undefined, with the reason, until the window has filled), and its
forces along x and y (N/m); per probe u_x, u_y, |u| (m/s) and the pressure (Pa) at its node (undefined inside a body);
per inlet, outlet or moving wall the mass flow into the domain through its side (kg/(s·m)); for the world the net
inflow, the mass and momentum balances' residuals, Re and the largest lattice Mach number. Every frame carries `meas`
(and `meas_note` for what is undefined); `measure()` gives the same values without the picture (the sweeps).

## Running checks

From the engine (`Flow2D.checks`): the mass, momentum and dye balances including the inflow, outflow, wall and body
forces (to round-off: 2 ulps of the total per step — not a proven worst case [error in earlier]: the engine's per-link
books used to round like n² and failed correct runs after ~10⁴ steps, review LB1-physics P1; they are compensated now,
and long runs stay ~500 times inside the bound); the lattice Mach number and the cell Reynolds number
against their (stability) limits; the density range (the measure of the compressibility error). Per obstacle: the drag
and lift coefficients (momentum exchange at its wall) **averaged over the domain's slowest sound period** (the engine's
force record, 64 blocks of whole steps per period; the window and the period, 4L/c_s or 2L/c_s, are shown) — and over
the last step, labelled as such: those carry the standing sound wave of the weakly compressible scheme (±13 % of the
drag after an impulsive start). Where the scene is a published benchmark's set-up (detected from the laws and the
objects, and shown only while it is: the DFG 2D-1 and 2D-2 channels, Ghia's cavity at Re 100, a Poiseuille channel
with a probe 2 H away from the inlet and the bodies, a channel driven by a body force along periodic ends between fixed
walls (u = g_x y (H − y)/(2ν); review LB1-physics P7), plane Couette flow between a moving and a fixed wall with periodic
ends), the group "Benchmarks" puts the benchmark's range or closed form next to the computed number, with what the
agreement needs (grid, wall, a developed flow) and the engine's own test results at that grid. The estimated
cost per step on the device in use.

## Approximations and limits

* A 2-D incompressible flow per metre of depth (no 3-D effects: a real cylinder's wake becomes three-dimensional at
  moderate Reynolds numbers, which a plane flow cannot show); the lattice Boltzmann method's compressibility error ~ Ma²
  and its sound waves (O(Ma²), larger after sudden changes); no turbulence model (the grid must resolve the vortices,
  or the world stops with the reason).
* Walls are staircase half-way bounce-back (curved walls to first order in position) or, per body, interpolated.
* Bodies do not move through the grid (surface velocities on fixed shapes); periodic sides repeat the bodies.
* The scene file keeps the set-up, not the flow: a world started from a file starts from rest at the file's time (the
  engine counts its steps from there). A new world with "carry the scene over" keeps the flow (review LB1-framework F5;
  before, it restarted from rest while the dialog promised the state [error in earlier]): the engine's state goes with
  the carry-over (`carry_state`), and the new world continues it (`carry_world` → `Flow2D.adopt`) — on the same grid and
  time step as it was (bit for bit); on another grid, domain or time step moved there first by the engine's transfer
  (`Flow2D.remap`, as a live change; the domain grows or is cut on the right and the top), with this world's fluid,
  sides, bodies, dye and force from then on; nodes that were a body start at rest, an inlet of the same velocity
  continues its ramp; the balances count from the carried state. What cannot be taken (a transfer the new grid refuses,
  no flow given) starts from rest, and the carry-over's notice says so ("the flow restarted from rest: …"), as it says
  every adaptation (another viscosity or density, the dye, a ramp started anew).
* A live grid, domain or time step (P16.1): the transfer is second order in the fluid away from bodies and exact for a
  Poiseuille profile; next to a curved or interpolated wall it is first order (the ghost of a solid node is the linear
  reflection through a half-way wall); the non-equilibrium part is rescaled at the first order of the Chapman–Enskog
  expansion (its force-dependent part and higher orders as they are), so a short transient of the viscous stress
  follows a change; the change takes one step of the old grid. A new part of the domain starts in equilibrium (rest or
  the inflow) and meets the old flow with a jump that sound waves of the scheme carry away.
* Open items: `../../STATUS.md` (V41, V42).

## Tests

`tests/test_p04_lab.py` (LB1): nx 440 → 880 → 440 and u_max changed on the DFG channel, the world going on with every
check passing and the cylinder's drag within 5 % across the refinement, the event's mass and momentum; the domain grown
on the right with the inflow, cropped back, grown on the left (the objects' coordinates move with the fluid), a crop
through a body, past a dye source and past a probe refused with the world as it was; a grid beyond the budget refused
before anything is allocated; the live grid repeated by replay bit for bit (populations, scene, live values,
measurables); the handles (`at` in every frame, a body's drag re-voxelised in well under a second); the measurables (ids,
translated labels and units, a value for each in every frame, the averaged coefficients undefined with the reason until
their window fills, the probe's values the fields at its node, the inlet's flow the engine's, `measure()` = the frame).
Review LB1 processing: the body-force Poiseuille channel stays on its parabola across nx and u_max changes, and a
wrong transfer (velocity × 1.01) is seen there while the momentum balance passes (documented); a new nx states the new
height and the nx that keep both lengths; a new u_max attributes the mass change to the scheme's compressibility (equal
to the pressure integral's prediction to 1 %); a new world keeps the flow (same grid: bit for bit; another grid: by
the transfer; no flow given: from rest, said). The engine: `lfphys/tests/test_lbm_remap.py` (also `Flow2D.adopt`,
the dye's second moment across a refinement, the remap's memory estimate against the measured peak) and
`test_lbm.py::test_the_running_check_holds_on_long_runs`.

`tests/test_p04_ux.py` (reviews 2026-11-04 UX-ui and UX-params): water and air from the defaults run (u_max lowered to
the cell Reynolds number 9, the notice, every check passing; the DFG fluid untouched); grids beyond the budget refused
before they are built (three domains; `estimate_bytes`); a large grid's advance cut to one step; the body force placed in
every preset and an explicit 9.81 refused with the u_max that, as a new world, carries it; side objects on free sides
and the palette's state with all sides taken; bodies placed free, outside refused or brought in, a body covering the
domain refused; a probe inside a body; the live ν, ρ (pressures × ρ′/ρ), BGK and the dye off / on, a too small ν
refused; live laws and placements rebuilt by replay (populations bit for bit); the engine's refusals in the world's
terms. `tests/test_p04_fluids.py`: every preset builds, runs and keeps its balances, and the default laws build; the NACA
profile's thickness (12 % at x ≈ 0.3 c for 0012) and the angle of attack's sense; the Reynolds numbers of the cylinder
(100 in the Kármán preset) and of the lid (100 in the cavity); one condition per side and the wall given back; dye only
in a world with dye; the field on request; an obstacle added while the flow runs keeps the balances; the scene file,
advanced twice after loading; an edit of an inlet's dye and a second inlet keep the inflow; a coefficient length set
back to 0; the forces' mean over the sound period equals the engine's mean over the same steps; the benchmark
comparisons appear for their set-ups only (and Couette's steady profile is met to 1e-6); the surface velocity is labelled as one; the picture averages the fluid only
and keeps the domain's size; the Kármán preset stays below its cell-Reynolds limit past its ramp (and, on GPU 0, in the
developed street). The flow itself: the engine's tests (`lfphys/tests/test_lbm*.py`: Poiseuille, Couette,
Taylor–Green, the DFG cylinder, Ghia's cavity, the inlet ramps, the hydrostatic rest state, the acoustic period, the
force record). The shared tests continue a world from its checkpoint byte for byte and rebuild it by replay.
