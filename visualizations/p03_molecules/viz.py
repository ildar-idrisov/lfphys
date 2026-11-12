# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p03: the particles-and-molecules playground (plan P15.4; owner, 2026-10-28: «например частицы и молекулы
взаимодействующие»). A wrapper over the engine's molecular dynamics (``lfphys.core.md``: Newton's equations by velocity
Verlet, thermostats, walls and a piston, statistical-mechanics observables; event-driven hard spheres in
``core.md.hard``) with the interatomic potentials of ``lfphys.theories.models.interatomic`` (Lennard-Jones, WCA, bonds
and angles: models, injected); the framework is ``lfviz.playground``.

The laws of the world. World parameters (a change starts a new world, which can take the scene over): the space (a plane
or the volume) and the boundaries at the start. Live laws (review 2026-11-04 UX-ui U12; LB1, plan P16.1, a bench that
never restarts: changed at the current moment, the world kept): the dynamics (continuous forces ↔ hard spheres by
events: the same atoms handed to the other solver, ``core.md.hard.hard_from_md`` / ``md_from_hard``), the pair model
(Lennard-Jones or the purely repulsive WCA, through ``MD.set_pair``), its cutoff and shift, the time step
(``MD.set_dt``) and the box (``MD.deform``: an affine deformation with its work in the first law, or a wall moved over
empty space). Objects have handles (LB1, P16.2: a drag moves a group as a whole, a throw gives it a centre-of-mass
velocity), every positioned object is in the frames' ``at`` and the world's measurables in their ``meas`` (P16.3).
Inside it the
experimenter places, at any moment, a gas or a crystal block of atoms, single atoms, molecules (bonded atoms with
angles), walls (specular, soft, or thermal: a heat bath; on a periodic axis a wall makes the axis walled), a piston,
thermostats (CSVR or Langevin, everywhere or in a region), a field and thermometers; a new object lands where it can
exist (``place``: the nearest free spot, a crystal around the atoms already there) or is refused with what to
change (reviews UX-ui U4–U8, U13; UX-params P31–P33); the engine computes the motion and measures
the temperature, the pressure, the energy balance (heat and work), the velocity distribution against Maxwell–Boltzmann,
the radial distribution function, the density along the field, the bond-orientational order and the mean-square
displacement, and for molecules the temperature of each kind of motion.

Every change of the scene is all or nothing (review B7-md M6): the engine's state and the wrapper's maps are saved
before it and put back bit for bit when the engine refuses any part of it.

Units: the engine's reduced units with argon's 12-6 parameters (σ = 3.405 Å, ε/k = 119.8 K, m = 39.948 u;
``argon_units``); the playground speaks nm, ps, K, bar (in 3-D; in a plane the pressure is a force per length, mN/m).
"""

from __future__ import annotations

import copy
import math

import numpy as np

from lfphys.core.md import observables as OB
from lfphys.core.md.system import MD, free_sites
from lfphys.i18n import T, is_t, join, text_of
from lfphys.theories.models import interatomic as IA
from lfviz.errors import Refusal  # the framework's refusal (reviews UX-params P4, UX-ui U13): shown with what to change
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param, scene_time

try:
    from lfviz.limits import require as _require
except ImportError:
    _require = None


def refusal(text, hint=None, detail=None):
    """A refusal for the owner: what is wrong and what to change (texts: ``T``)."""
    return Refusal(text, hint=hint, detail=detail)

U = IA.argon_units()
NM = U.to_angstrom(1.0) / 10.0          # nm per reduced length
PS = U.to_ps(1.0)                       # ps per reduced time
KELVIN = U.to_kelvin(1.0)               # K per reduced temperature
STATS_EVERY = 10                        # frames between two statistics messages (by count)
ORDER_EVERY_PS = 1.0                    # world time between two values of the order parameter in ``meas`` (ps)
MAX_STEPS = 400                         # integrator steps per advance call
ORDER_RCUT = 1.5                        # neighbours for the bond-orientational order: nearer than 1.5 sigma
Z_BLOCK = 1.0                           # the hard world's pressure blocks: at least one time unit (2.16 ps) each
Z_EQUIL = 5.0                           # ... counted from five time units after the last change of the scene
Z_MIN_BLOCKS = 10
HBAR_OVER_K = 1.054571817e-34 / 1.380649e-23   # s K (CODATA 2018 exact k, ħ)
COLORS = ["#74c0fc", "#ff922b", "#8ce99a", "#f783ac", "#ffd43b", "#b197fc", "#e9ecef", "#ff6b6b"]
# the time step must resolve the repulsive core (review UX-params P32): the rms step v dt over the distance r_t / 12 in
# which the 12-6 repulsion rises by kT near its turning point r_t = sigma (4 eps / kT)^(1/12), q = 12 v dt / r_t, at
# most Q_MAX. Measured (2-D and 3-D LJ gas, 200 atoms, dt = 10 fs, 3 seeds, 3000 steps; the response's checks): q <= 0.36
# keeps the energy error below 0.6 % of kT per atom; at q = 0.44-0.46 it is 0.02-5 %; at q = 0.58 two of three 2-D runs
# crashed («two interacting particles at the same point»), as did every run at 10^5 K (q = 1.8). Argon at 300 K: q =
# 0.12 (2-D); an atom of 4 u at 300 K: 0.38
Q_MAX = 0.4
FRAME_S = 0.04          # the modelled computing time of one advance call (the runner interleaves commands and frames)
# random sequential insertion jams near these covered fractions (equal disks / spheres); refused at once above
JAM = {2: 0.50, 3: 0.35}
MOL_JAM = {2: 0.40, 3: 0.28}
PAIR_BYTES = 120        # bytes per pair of the neighbour list while it is built (indices, separations, terms)

# the critical temperature of the pair model, eps/k (sources: lfphys/sources/verification_2026-11-04_p8_md.md §8):
# 3-D: the full 12-6 1.3120 (NIST SRS, Potoff & Panagiotopoulos 1998), linear force shift at 2.5 sigma 0.937 (NIST
# SRS, Errington, Debenedetti & Torquato 2003); 2-D: full 0.515, truncated and energy-shifted at 2.5 sigma 0.459 (Smit
# & Frenkel 1991)
TC = {(3, "full"): 1.3120, (3, 2.5, "force"): 0.937, (2, "full"): 0.515, (2, 2.5, "energy"): 0.459}


def _p(*a, **k):
    return Param(*a, **k)


BOX_HELP = T("Changed at the current moment (see “How to change the box size” and “Time of the size change”). Affinely: the "
           "atoms' coordinates along the axis are multiplied by L′/L, their velocities relative to the centre of mass by "
           "L/L′ (for the motion relative to the centre of mass a canonical transformation, the volume step of "
           "Andersen's barostat). The work done on the system is the change of its energy, counted in the first law. "
           "Over a given time (a step at every computing step) the compression is the closer to quasi-static the slower "
           "it is: the work tends to −∫P dV along the adiabat, compression and return hardly heat; at once (time 0) it is "
           "irreversible: the matter is out of equilibrium after the jump and heats up (argon gas, 300 atoms at 300 K, "
           "12 → 11 → 12 nm: at once ≈ 16 K, over 10 ps ≈ 0.7 K, over 50 ps ≈ 0.6 K, over 200 ps 0 ± 0.2 K; see the "
           "README). Refused with the reason when atoms would overlap (a jump), a molecule's bond would change its "
           "length by more than 10 % (a jump), the cutoff radius would exceed half the box, the axis is the piston's "
           "(move the piston), or the time step does not resolve the collisions (compression heats)")
BOX_TIME_HELP = T("The time in which the box reaches its new size (affinely): the size changes uniformly, by a small affine "
                  "step at every computing step, the work of each step counted. The longer (the slower the box's faces "
                  "compared with the speed of sound, ≈ 320 m/s in argon gas at 300 K), the closer to the quasi-static "
                  "adiabat: argon gas (300 atoms, 300 K) compressed 12 → 11 nm and returned heats by ≈ 16 K at once, by "
                  "≈ 0.7 K over 10 ps, by ≈ 0.6 K over 50 ps, by 0 ± 0.2 K over 200 ps (measured, 4 runs). 0: at once "
                  "(irreversible). While the size changes, the current size is in the frame; the end of the change is an "
                  "event with the work")


class _Schema(Schema):
    """p03's schema: laws written before the split of 2026-11-05 (review UX-ui U12) still resolve. Then ``model`` held
    lj | wca | hard as one world parameter; now ``dynamics`` (forces | hard) is the world's and ``model`` (lj | wca) a live
    law. An old ``"model": "hard"`` (from a scene file's laws or a stored run) becomes ``dynamics = hard``; old lj / wca
    are valid as they are (the default dynamics is the forces). The world says so in a notice (``legacy_note``)."""

    def resolve(self, preset, values):
        return super().resolve(preset, legacy_laws(values))


def legacy_laws(values):
    """The laws of the old combined ``model`` in the new split (a copy; other values untouched)."""
    if isinstance(values, dict) and values.get("model") == "hard":
        values = {**values, "dynamics": "hard", "model": "lj"}   # the live model is unused by hard spheres
    return values


def legacy_note(scene):
    """The notice for a scene file of the old format (its laws carry ``model`` and no ``dynamics``), or None."""
    laws = scene.get("laws") if isinstance(scene, dict) else None
    if not isinstance(laws, dict) or "dynamics" in laws or "model" not in laws:
        return None
    old = laws["model"]
    if old == "hard":
        what = T("“Interaction” = hard disks / spheres became “Dynamics” = hard disks / spheres")
    else:
        lab = {"lj": T("Lennard-Jones"), "wca": T("repulsion only (WCA)")}.get(old, str(old))
        what = T("“Interaction” = {model} became “Dynamics” = continuous forces and “Interaction” = {model}, now a law "
                 "that changes while the world runs", model=lab)
    return T("a file of the old format (before 2026-11-05): {what}; the scene was loaded with the same laws", what=what)


SCHEMA = _Schema([
    _p("dim", T("Space"), "select", "2d", group=T("Laws"),
       options=[("2d", T("plane")), ("3d", T("volume"))],
       help=T("A plane or a volume is another world (a new world); the scene can be carried over: the objects are made "
              "anew from their parameters, the z coordinate is dropped or takes its default; a wall or a piston across "
              "z is not carried into a plane")),
    _p("dynamics", T("Dynamics"), "select", "forces", group=T("Laws (live)"), live=True,
       options=[("forces", T("continuous forces (Lennard-Jones or WCA)")),
                ("hard", T("hard disks / spheres (event-driven dynamics)"))],
       help=T("Switched at the current moment: the same atoms with the same positions and velocities. To hard spheres "
              "only if no pair of atoms is closer than σ and no atom closer than σ/2 to a wall, and the scene has no "
              "molecules, piston, thermostats, field, soft walls or charges (hard spheres have none of them). Back "
              "always: the pairs' potential energy appears (the jump of the energy is stated in the event); the time "
              "step must resolve the collisions")),
    _p("model", T("Interaction"), "select", "lj", group=T("Laws (live)"), live=True,
       show_if={"dynamics": ["forces"]},
       options=[("lj", T("Lennard-Jones (attraction and repulsion; a model)")),
                ("wca", T("repulsion only (WCA; a model)"))],
       help=T("Changed at the current moment: the same atoms with a new law of interaction; the energy changes by the "
              "difference of the potentials (counted in the energy balance), the checks start counting anew")),
    _p("cutoff", T("Cutoff radius, σ"), "float", 2.5, group=T("Laws (live)"), min=1.2, max=6.0, live=True,
       show_if={"dynamics": ["forces"], "model": ["lj"]},
       help=T("The Lennard-Jones potential is cut at this distance; the shift removes the jump. The cutoff changes the "
              "substance: its critical point and triple point differ from those of the full potential (see the "
              "approximations). Changed while the world runs (at most half the periodic box)")),
    _p("shift", T("Shift at the cutoff"), "select", "force", group=T("Laws (live)"), live=True,
       show_if={"dynamics": ["forces"], "model": ["lj"]},
       options=[("force", T("force and energy continuous (only the scheme's error O(dt²))")),
                ("energy", T("energy continuous only (a jump of the force: an energy error O(dt))"))]),
    _p("dt_fs", T("Time step, fs"), "float", 10.0, group=T("Laws (live)"), min=0.1, max=50.0, live=True,
       show_if={"dynamics": ["forces"]},
       help=T("Verlet scheme: the energy error ~ dt² with continuous forces; for argon 10 fs ≈ 0.005 τ. Changed while "
              "the world runs (the same state, the next steps with the new step); an atom must move at most 0.1 σ in a "
              "step")),
    _p("Lx", T("Box size along x, nm"), "float", 12.0, group=T("Box (live)"), min=0.5, max=1e3, log=True, live=True,
       help=BOX_HELP),
    _p("Ly", T("Box size along y, nm"), "float", 12.0, group=T("Box (live)"), min=0.5, max=1e3, log=True, live=True,
       help=BOX_HELP),
    _p("Lz", T("Box size along z, nm"), "float", 6.0, group=T("Box (live)"), min=0.5, max=1e3, log=True, live=True,
       show_if={"dim": ["3d"]}, help=BOX_HELP),
    _p("box_mode", T("How to change the box size"), "select", "affine", group=T("Box (live)"), live=True,
       options=[("affine", T("compress or stretch together with the matter (affinely; work on the system)")),
                ("wall", T("move the upper wall: add or remove empty space"))],
       help=T("“Affinely”: all the matter is compressed or stretched with the box (as a barostat does) over the “Time "
              "of the size change”: a slow compression approaches the adiabatic one, a jump is irreversible; the work "
              "on the system is counted in the first law. “Wall” (an axis with walls only; on the piston's axis its "
              "upper stop): the wall moves over empty space at once, an expansion into vacuum (Joule's experiment, "
              "irreversible), no work for specular and thermal walls, for a soft wall the work is the change of its "
              "energy under the atoms (stated in the event); space can be removed only where there are no atoms. Hard "
              "spheres: “wall” only")),
    _p("box_time_ps", T("Time of the size change, ps (0: at once)"), "float", 50.0, group=T("Box (live)"), min=0.0,
       max=1e4, live=True, show_if={"box_mode": ["affine"]}, help=BOX_TIME_HELP),
    _p("boundary", T("Boundaries at the start"), "select", "periodic", group=T("Box"),
       options=[("periodic", T("periodic (infinite matter)")), ("walls", T("walls on all sides")),
                ("slab", T("walls at the bottom and the top (along y), periodic at the sides"))],
       help=T("A “Wall” or a “Piston” from the palette on a periodic axis makes it an axis with walls (live)")),
    scene_param(),
], presets={})

LIVE = ("dynamics", "model", "cutoff", "shift", "dt_fs", "Lx", "Ly", "Lz", "box_mode", "box_time_ps")
BOX_KEYS = ("Lx", "Ly", "Lz")
MAX_BOND_STRAIN = 0.10   # an affine change of the box stretches the molecules' bonds with it: at most 10 % per change


def _scene(objs):
    return {"format": "lfscene", "version": 1, "objects": objs}


# the melting preset's box holds a whole triangular lattice of density 0.85 (25 x 15 rectangular cells of a x a√3,
# a = (2/(√3 · 0.85))^½ σ = 0.39685 nm): the crystal fills it without strain or a vacancy strip (review B7-md M17)
_A085 = math.sqrt(2.0 / (math.sqrt(3.0) * 0.85)) * NM
# the liquid-vapour preset's box: 5 fcc cells of the liquid's density 0.693 (NIST, LFS 2.5σ at 0.75 ε/k) across x and z
_AFCC = (4.0 / 0.693) ** (1.0 / 3.0) * NM

SCHEMA.presets.update({
    "maxwell": {"label": T("Argon gas started with equal speeds: the Maxwell distribution sets in by itself"),
                "params": {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic",
                           "scene": _scene([{"type": "gas", "label": T("Argon"), "values": {
                               "n": 300, "T": 300.0, "start": "same_speed"}}])}},
    "melting": {"label": T("A plane crystal (ρσ² = {rho}) is heated by a thermostat to {T} K: the order ψ6 vanishes, the "
                           "atoms start to diffuse — melting", rho=0.85, T=120),
                "params": {"dim": "2d", "model": "lj", "Lx": round(25 * _A085, 4),
                           "Ly": round(15 * math.sqrt(3.0) * _A085, 4), "boundary": "periodic",
                           "scene": _scene([
                               {"type": "crystal", "label": T("Crystal"), "values": {"density": 0.85, "T": 20.0}},
                               {"type": "thermostat", "label": T("Heating to {T} K", T=120),
                                "values": {"T": 120.0, "tau": 2.0}}])}},
    "piston": {"label": T("Gas under a piston: compression by the piston and heat exchange with a wall (the first law)"),
               "params": {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 16.0, "boundary": "walls",
                          "scene": _scene([
                              {"type": "gas", "label": T("Argon"), "values": {"n": 200, "T": 300.0, "sy": 8.0,
                                                                              "y": 4.5}},
                              {"type": "piston", "label": T("Piston"), "values": {"position": 10.0, "mass": 4000.0,
                                                                                 "p_ext": 50.0}},
                              {"type": "wall", "label": T("Warm bottom"), "values": {"axis": "y", "side": "lo",
                                                                                    "kind": "thermal", "T": 300.0}}])}},
    "liquid_vapour": {"label": T("Liquid and vapour in a volume at {T} K in a field: the liquid (ρσ³ ≈ {rl}) below, the "
                                 "vapour (≈ {rv}) above it — the density profile along the height", T=90, rl=0.69,
                                 rv=0.03),
                      "params": {"dim": "3d", "model": "lj", "Lx": round(5 * _AFCC, 4), "Ly": 6.0,
                                 "Lz": round(5 * _AFCC, 4), "boundary": "slab",
                                 "scene": _scene([
                                     {"type": "crystal", "label": T("Liquid (from a lattice)"),
                                      "values": {"density": 0.693, "T": 90.0, "y": 1.3, "sy": 2.6}},
                                     {"type": "thermostat", "label": T("Thermostat {T} K", T=90),
                                      "values": {"T": 90.0, "tau": 5.0}},
                                     {"type": "gravity", "label": T("Field"), "values": {"g": 0.02}}])}},
    "molecules": {"label": T("Diatomic molecules start with translation only: collisions hand energy to rotation and "
                             "vibration (equipartition sets in)"),
                  "params": {"dim": "3d", "model": "lj", "Lx": 5.0, "Ly": 5.0, "Lz": 5.0, "boundary": "periodic",
                             "scene": _scene([{"type": "molecule", "label": T("Molecules X₂"), "values": {
                                 "shape": "dimer", "count": 150, "T": 400.0, "bond": 1.1, "k_bond": 50.0,
                                 "start": "translation"}}])}},
    "hard_disks": {"label": T("Hard disks: the pressure against the equation of state (Kolafa and Rottner)"),
                   "params": {"dim": "2d", "dynamics": "hard", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic",
                              "scene": _scene([{"type": "gas", "label": T("Disks"), "values": {
                                  "n": 400, "T": 300.0}}])}},
})


def _xyz(ndim, d=(6.0, 6.0, 3.0)):
    return [_p(c, T("Centre: {c}, nm", c=c), "float", float(d[i]), min=-1e3, max=1e3) for i, c in enumerate("xyz"[:ndim])]


def _region(ndim):
    return [*[_p(c, T("Centre of the region: {c}, nm (0 and size 0: the whole box)", c=c), "float", 0.0, min=-1e3,
                 max=1e3) for c in "xyz"[:ndim]],
            *[_p(f"s{c}", T("Size of the region along {c}, nm (0: the whole box)", c=c), "float", 0.0, min=0.0, max=1e3)
              for c in "xyz"[:ndim]]]


def _subst(model):
    out = [_p("substance", T("Substance"), "select", "argon",
              options=[("argon", T("argon (σ = {s} Å, ε/k = {e} K, m = {m} u)", s=3.405, e=119.8, m=39.948)),
                       ("custom", T("custom"))],
              help=T("A change of the substance gives the same atoms new parameters at the current moment; the "
                     "temperature is kept (the velocities rescaled by √(m/m′)); overlaps at the new σ are refused")),
           _p("sigma", T("Size σ, fraction of argon's"), "float", 1.0, min=0.3, max=3.0, show_if={"substance": ["custom"]}),
           _p("mass", T("Mass, u"), "float", 39.948, min=1.0, max=1e4, log=True,
              show_if={"substance": ["custom"]})]
    if model != "hard":
        out[2:2] = [_p("epsilon", T("Well depth ε, fraction of argon's"), "float", 1.0, min=0.0, max=20.0,
                       show_if={"substance": ["custom"]})]
        out.append(_p("charge", T("Charge, e (only in a box with walls)"), "float", 0.0, min=-5.0, max=5.0,
                      show_if={"substance": ["custom"]}))
    out.append(_p("color", T("Colour"), "select", "0", options=[(str(i), c) for i, c in enumerate(
        [T("light blue"), T("orange"), T("green"), T("pink"), T("yellow"), T("violet"), T("white"), T("red")])]))
    return out


SP_KEYS = {"substance", "sigma", "epsilon", "mass", "charge", "color"}
POS_KEYS = ("x", "y", "z")
CARRIED = {"gas": T("the gas's atoms"), "crystal": T("the crystal's atoms"), "atom": T("the atom"),
           "molecule": T("the molecules"), "piston": T("the piston")}
VEL_KEYS = ("vx", "vy", "vz")
AXIS_KEYS = {"z", "sz", "vz", "throw_vz"}   # the keys of the axis a plane has not (a 3-D scene carried into a plane)


def _vcom(ndim):
    return [_p(f"v{c}", T("Centre-of-mass velocity v{c}, m/s", c=c), "float", 0.0, min=-1e5, max=1e5,
               help=T("The object moves as a whole with this velocity (a throw with the mouse sets it); the atoms' "
                      "thermal motion follows the temperature")) for c in "xyz"[:ndim]]


# a throw (LB1, P16.2) comes in the world's units - nm per second of world time (the frames' ``at`` and ``t``); the
# objects' velocities are in m/s: the throw's own hidden parameters carry it, ``_set_obj`` turns it into vx, vy, vz
# (review LB1-p02-ux X4: a throw of 1.9·10¹² nm/s was taken for 1.9·10¹² m/s and refused)
THROW_KEYS = ("throw_vx", "throw_vy", "throw_vz")
NM_PER_S = 1e9            # nm/s per m/s
THROW_MAX_M_S = 500.0     # the largest throw (m/s): see palette()


def _throw(ndim):
    return [_p(f"throw_v{c}", T("Throw: centre-of-mass velocity v{c}, nm/s", c=c), "float", 0.0, min=-1e15, max=1e15,
               hidden=True, help=T("set by a throw with the mouse (in the world's units: nm per second of its time); "
                                   "the object gets this centre-of-mass velocity (shown in m/s in the inspector)"))
            for c in "xyz"[:ndim]]


def _ot(typ, label, kind, schema, handles=None, **kw):
    """A palette type with its handles for direct manipulation (LB1, P16.2: the params a drag or a throw changes) and
    whether it has a dynamic state (``stateful``: the carry-over says whether it went along); a framework without them
    takes the type without them."""
    tries = [dict(kw, handles=handles)] if handles else []
    if handles and "velocity_display" in handles:   # a framework without the display unit: the rest of the handles
        tries.append(dict(kw, handles={k: v for k, v in handles.items() if k != "velocity_display"}))
    tries += [dict(kw)] + ([{k: v for k, v in kw.items() if k != "stateful"}] if "stateful" in kw else [])
    for i, k in enumerate(tries):
        try:
            return ObjectType(typ, label, kind, schema, **k)
        except (TypeError, ValueError):
            if i == len(tries) - 1:
                raise


def palette(ndim: int, model: str = "lj") -> dict:
    """The palette: one for both dynamics (LB1: the dynamics is a live law; what the hard spheres have not is disabled
    by ``palette_state`` with the reason). ``model`` is kept for the callers of before."""
    Tp = _p("T", T("Temperature, K"), "float", 300.0, min=0.0, max=1e5)
    SUBST = _subst("lj")
    gas = Schema([_p("n", T("Number of atoms"), "int", 200, min=1, max=20000), Tp,
                  _p("start", T("Initial velocities"), "select", "maxwell",
                     options=[("maxwell", T("Maxwellian at T")), ("same_speed", T("all with one speed (as at T)"))]),
                  *_region(ndim), *_vcom(ndim), *_throw(ndim), *SUBST])
    crystal = Schema([_p("density", T("Lattice density ρσ^d"), "float", 0.9, min=0.05, max=1.3,
                         help=T("A lattice (2-D triangular, 3-D fcc) of this density: whole cells in the region; along "
                                "a periodic axis the block fills entirely the cells are fitted to the box (the actual "
                                "density is in the inspector). Close packing: ρσ² ≈ {d2}, ρσ³ ≈ {d3}", d2=0.9, d3=1.0)),
                      Tp, *_region(ndim), *_vcom(ndim), *_throw(ndim), *SUBST])
    atom = Schema([*_xyz(ndim), *[_p(f"v{c}", T("Velocity v{c}, m/s", c=c), "float", 0.0, min=-1e5, max=1e5)
                                  for c in "xyz"[:ndim]], *_throw(ndim), *SUBST])
    mol = Schema([_p("shape", T("Molecule"), "select", "dimer",
                     options=[("dimer", T("diatomic")), ("bent", T("triatomic, bent")), ("chain", T("chain"))]),
                  _p("atoms", T("Atoms in the chain"), "int", 6, min=3, max=50, show_if={"shape": ["chain"]}),
                  _p("count", T("Number of molecules"), "int", 20, min=1, max=2000), Tp,
                  _p("start", T("Initial motion"), "select", "maxwell",
                     options=[("maxwell", T("everything at T (translation, rotation, vibration)")),
                              ("translation", T("translation only at T (rotation and vibration cold)"))],
                     help=T("“Everything at T”: each atom's velocity Maxwellian at T, bond lengths and angles "
                            "Boltzmann-distributed around equilibrium (a canonical start); “translation only”: the "
                            "molecule moves as a whole with a speed at T for its mass, bonds and angles at equilibrium")),
                  _p("bond", T("Bond length, σ"), "float", 1.0, min=0.5, max=2.0),
                  _p("k_bond", T("Bond stiffness, ε/σ²"), "float", 400.0, min=1.0, max=1e4, log=True),
                  _p("angle", T("Bond angle, °"), "float", 105.0, min=30.0, max=180.0,
                     show_if={"shape": ["bent", "chain"]}),
                  _p("k_angle", T("Angle stiffness, ε/rad²"), "float", 50.0, min=0.0, max=1e4,
                     show_if={"shape": ["bent", "chain"]}),
                  *_region(ndim), *_vcom(ndim), *_throw(ndim), *SUBST])
    axes = [(c, c) for c in "xyz"[:ndim]]
    wall_kinds = [("specular", T("specular (elastic reflection)")),
                  ("thermal", T("thermal (returns atoms with the wall's temperature: a heat bath)")),
                  ("soft", T("soft (a Lennard-Jones wall potential; not for hard spheres)"))]
    wall = Schema([_p("axis", T("Wall across the axis"), "select", "y", options=axes),
                   _p("side", T("Side of the box"), "select", "lo", options=[("lo", T("lower / left")), ("hi", T("upper / right"))]),
                   _p("kind", T("Wall"), "select", "thermal", options=wall_kinds),
                   _p("T", T("Wall temperature, K"), "float", 300.0, min=0.0, max=1e5, show_if={"kind": ["thermal"]})])
    piston = Schema([_p("axis", T("Piston across the axis"), "select", "y", options=axes),
                     _p("position", T("Position, nm"), "float", 10.0, min=0.0, max=1e3,
                        help=T("Set when it is placed; changing other parameters does not move the piston")),
                     _p("mass", T("Piston mass, u (0: moves as prescribed)"), "float", 4000.0, min=0.0,
                        max=1e9),
                     _p("p_ext", T("External pressure, bar (in a plane: mN/m)"), "float", 50.0, min=0.0, max=1e6),
                     _p("speed", T("Speed (if the mass is 0), m/s"), "float", 0.0, min=-1e4, max=1e4)])
    thermo = Schema([_p("kind", T("Thermostat"), "select", "csvr",
                        options=[("csvr", T("CSVR (Bussi–Donadio–Parrinello): canonical, gentle")),
                                 ("langevin", T("Langevin (friction and noise)"))]),
                     _p("T", T("Temperature, K"), "float", 300.0, min=0.0, max=1e5),
                     _p("tau", T("Relaxation time, ps"), "float", 2.0, min=1e-3, max=1e6, show_if={"kind": ["csvr"]}),
                     _p("gamma", T("Friction γ, 1/ps"), "float", 1.0, min=1e-6, max=1e4, show_if={"kind": ["langevin"]}),
                     *_region(ndim)])
    field = Schema([_p("g", T("Field g (down along y), ε/(mσ)"), "float", 0.02, min=-10.0, max=10.0,
                       help=T("For argon the unit ε/(mσ) ≈ {u:.2g} m/s² (the Earth's g ≈ {g:.2g} in these units): the "
                              "Earth's field is imperceptible on the scale of atoms; here a strong model field shows the "
                              "stratification", u=7.3e13, g=1.3e-13))])
    probe = Schema([*_xyz(ndim), _p("r", T("Radius, nm"), "float", 2.0, min=0.1, max=1e3)])
    pos = list(POS_KEYS[:ndim])
    # the throw: in the world's units (nm/s), at most THROW_MAX_M_S (review LB1-p02-ux X4): about the speed of sound of
    # argon gas at room temperature and above its thermal speed; the default step (10 fs) resolves the collisions of a
    # 300 K argon group thrown at it (q = 12 v dt / r_t at 500 m/s plus the thermal speed: 0.34 in a plane, 0.37 in a
    # volume, the limit Q_MAX = 0.4; tests/test_p03_lab.py);
    # faster, or hotter, or lighter, is refused by the step with what to change
    group = {"position": pos, "velocity": list(THROW_KEYS[:ndim]), "velocity_max": THROW_MAX_M_S * NM_PER_S,
             # the throw read and logged in m/s (the framework's velocity_display: shown = factor × world units); the
             # unit is a plain msgid (check_handles takes a str), translated by the player
             "velocity_display": {"unit": "m/s", "factor": 1.0 / NM_PER_S}}
    pal = {
        "gas": _ot("gas", T("Gas (atoms)"), "particle", gas, handles=group, color=COLORS[0],
                   help=T("Atoms at random places (no closer than σ to each other and to those already there: random "
                          "sequential insertion), velocities at the temperature T; the gas's total momentum removed, "
                          "then the centre-of-mass velocity added. A drag moves all its atoms, a throw (Shift) sets the "
                          "centre-of-mass velocity")),
        "crystal": _ot("crystal", T("Crystal (a lattice of atoms)"), "particle", crystal, handles=group, color=COLORS[2]),
        "atom": _ot("atom", T("Atom"), "particle", atom, handles=group, color=COLORS[4]),
        "wall": _ot("wall", T("Wall (kind)"), "field", wall, limit=6, color="#adb5bd",
                    help=T("Changes one of the box's walls (at boundaries with walls)")),
        "probe": _ot("probe", T("Thermometer (region)"), "probe", probe, handles={"position": pos, "size": "r"}, limit=6,
                     color="#ffd43b",
                     help=T("The number of atoms, their density and temperature in a sphere around a point (periodic "
                            "faces taken into account)")),
        "molecule": _ot("molecule", T("Molecules"), "particle", mol, handles=group, color=COLORS[1],
                        help=T("Atoms bound by springs (and angles): a model of a molecule; placed without overlaps "
                               "(each atom's energy at insertion at most 2kT); not for hard spheres")),
        "piston": _ot("piston", T("Piston"), "body", piston, handles={"position": {"param": "position", "axis_param": "axis"}},
                      limit=1, color="#868e96", stateful=True,
                      help=T("The upper wall of the axis is movable: a mass and an external pressure; the work is "
                             "counted; not for hard spheres")),
        "thermostat": _ot("thermostat", T("Thermostat"), "field", thermo, limit=4, color="#ff6b6b",
                          help=T("Holds the temperature (the whole region or a part of it); the heat is counted; not "
                                 "for hard spheres")),
        "gravity": _ot("gravity", T("Field (gravity)"), "field", field, limit=1, color="#868e96",
                       help=T("A uniform field down along y; not for hard spheres")),
    }
    return pal


def _hex(c):
    h = c.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def debye_cv_fraction(T, theta):
    """C_v / (3 N k) of the Debye model at T (Θ_D = theta): 3 (T/Θ)^3 ∫_0^{Θ/T} x^4 e^x/(e^x - 1)^2 dx."""
    if T <= 0:
        return 0.0
    xm = theta / T
    x = np.linspace(1e-9, xm, 4001)
    f = x ** 4 * np.exp(-x) / (-np.expm1(-x)) ** 2
    return float(3.0 / xm ** 3 * np.trapezoid(f, x))


def einstein_cv_fraction(T, theta):
    """C / k of one quantum harmonic oscillator of ħω/k = theta at T (1 classically)."""
    if T <= 0:
        return 0.0
    x = theta / T
    return float(x * x * math.exp(-x) / (-math.expm1(-x)) ** 2)


def _charged(s):
    return s is not None and any(d.get("charge", 0.0) for d in s.md.species())


_EN = [  # the engine's refusals (core.md, English) in the owner's terms (reviews UX-ui U13, UX-params P31)
    (r"random placement jammed: (\d+) of (\d+)", lambda m, s: (
        T("only {k:d} of {n:d} atoms could be placed without overlaps", k=int(m.group(1)), n=int(m.group(2))),
        T("fewer atoms or a larger region; denser: “Crystal”"))),
    (r"overlap: an inserted particle's potential energy ([-\d.e+]+)", lambda m, s: (
        (T("the insertion energy of a new atom {e:.3g} ε exceeds the limit {lim:.3g} ε: with charges the Coulomb "
           "repulsion of distant atoms sets it too", e=float(m.group(1)), lim=float(getattr(s.md, "max_insert_energy", 50)))
         if _charged(s) else
         T("the new atoms would lie on those already there (insertion energy {e:.3g} ε at the limit {lim:.3g} ε)",
           e=float(m.group(1)), lim=float(getattr(s.md, "max_insert_energy", 50)))),
        (T("a smaller charge or fewer atoms") if _charged(s) else
         T("move the object to a free place or decrease the size σ")))),
    (r"two interacting particles at the same point|two bonded atoms at the same point", lambda m, s: (
        T("two atoms would be at the same point"), T("move the object"))),
    (r"overlapping hard particles", lambda m, s: (
        T("hard disks (spheres) would overlap"), T("move the object to a free place or decrease σ"))),
    (r"region: hi > lo", lambda m, s: (
        T("the object's region lies outside the box (nothing of it is left inside the walls)"),
        T("the region's centre and sizes inside the box (size 0: the whole box)"))),
    (r"a particle outside the walls on axis (\w)", lambda m, s: (
        T("an atom would be beyond the wall on the axis {a}", a=m.group(1)),
        T("coordinates inside the box (and below the piston)"))),
    (r"the pair cutoff \+ skin ([\d.e+-]+) exceeds half a periodic box length ([\d.e+-]+)", lambda m, s: (
        T("the cutoff radius with its margin ({rc:.3g} nm) exceeds half the periodic box ({half:.3g} nm)",
          rc=float(m.group(1)) * NM, half=float(m.group(2)) * NM),
        T("a smaller “Cutoff radius” or a larger box (both change while the world runs)"))),
    (r"charges in a box with a periodic axis", lambda m, s: (
        T("charges in a box with a periodic axis are not supported (the Ewald sum is not implemented)"),
        T("put a “Wall” on every periodic axis (the axis gets walls) or start a new world with “Boundaries at the "
          "start” = walls"))),
    (r"a periodic box length must be >= 4 times the largest diameter \(([\d.e+-]+)\)", lambda m, s: (
        T("the periodic box is shorter than four diameters of the largest atom ({d:.3g} nm)", d=float(m.group(1)) * NM),
        T("a smaller σ of the atoms or a larger box (while the world runs, with continuous forces)"))),
    (r"the piston's axis (\w)", lambda m, s: (
        T("along the axis {a} the piston sets the volume: the box does not change affinely along it", a=m.group(1)),
        T("move the piston (its “Position”), or “How to change the box size” = move the upper wall: then the piston's "
          "upper stop changes"))),
    (r"the piston's face ([\d.e+-]+) lies beyond", lambda m, s: (
        T("the piston stands at {x:.4g} nm, above the new upper wall", x=float(m.group(1)) * NM),
        T("a size along the piston's axis of at least {x:.4g} nm, or lower the piston first", x=float(m.group(1)) * NM))),
    (r"axis ([xyz, ]+) is periodic: it has no wall", lambda m, s: (
        T("the axis {a} is periodic: there is no wall to move", a=m.group(1)),
        T("“How to change the box size” = affinely, or first put a “Wall” on this axis"))),
    (r"a bond would change its length by ([\d.e+-]+) \(limit ([\d.e+-]+)\)", lambda m, s: (
        T("the molecules' bonds would stretch or shrink by {p:.3g} % (the limit is {lim:.3g} % per change: the atoms move "
          "with the box, and so do the bonds)", p=100 * float(m.group(1)), lim=100 * float(m.group(2))),
        T("change the size in steps of at most {lim:.3g} %", lim=100 * float(m.group(2))))),
    (r"the hi side of this axis is the piston", lambda m, s: (
        T("the upper side of this axis is the piston"), T("choose the lower side or another axis"))),
    (r"no free lattice site", lambda m, s: (
        T("all the crystal's sites are taken by atoms already there"),
        T("give the crystal a free region (centre and size)"))),
    (r"the region is smaller than one lattice cell", lambda m, s: (
        T("the crystal's region is smaller than one lattice cell at this density"),
        T("a larger region or a higher density"))),
    (r"0 < x_min <= X <= L", lambda m, s: (
        T("the piston's position is outside the box"), T("a position from the lower wall to the box's upper face"))),
    (r"non-finite forces|non-finite", lambda m, s: (
        T("the forces became infinite (atoms too close)"), T("move the object or lower the temperature"))),
    (r"a thermal wall needs", lambda m, s: (
        T("a thermal wall needs a temperature above 0 K"), T("a wall temperature > 0 K"))),
]


def _is_owner_text(e):
    """An exception that already speaks to the owner: a Refusal, or an error raised with a translatable text."""
    return isinstance(e, Refusal) or is_t(text_of(e))


def _owner(e, sim=None):
    """An engine exception in the owner's terms (a Refusal with what to change), the engine's sentence as the detail."""
    import re
    s = str(e)
    for rx, fn in _EN:
        m = re.search(rx, s)
        if m:
            text, hint = fn(m, sim)
            return refusal(text, hint=hint, detail=s)
    if isinstance(e, ValueError):
        return refusal(T("the engine refused this change"), hint=T("other values of the object"), detail=s)
    return e


def _val(k, v):
    p = SCHEMA.by_id.get(k)
    if p is not None and p.type == "select":
        return dict(p.options).get(v, v)
    return v


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p03_molecules"
    speed_range = (1e-3, 1e5)  # ps of the world per second (the world's time is in seconds: ×1e-12 below)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.ndim = 2 if params["dim"] == "2d" else 3
        self.hard = params.get("dynamics", "forces") == "hard"
        self.live = {k: params[k] for k in LIVE}      # the live laws in force (review UX-ui U12)
        self.model = "hard" if self.hard else self.live["model"]
        box = [params["Lx"], params["Ly"], params["Lz"]][:self.ndim]
        self.box = [float(b) / NM for b in box]  # reduced
        bd = params["boundary"]
        boundary = ["periodic", "walls", "periodic"][:self.ndim] if bd == "slab" else [bd] * self.ndim
        self.boundary = list(boundary)      # at the start; walls and pistons may make a periodic axis walled
        self.rng = np.random.default_rng(seed)
        self._ramp_seen, self._ramp_T0 = 0, None   # the last change of the box over a time announced; T at its start
        # the solver starts at the scene's time (a file's, a carried scene's): before, it started at 0 and the first
        # advance computed the whole interval up to the scene's time over the scene's atoms (found processing review
        # LB1-framework F5: the carried atoms moved before the new world's first frame)
        t0 = scene_time(params) * 1e12 / PS
        if self.hard:
            from lfphys.core.md import hard as HD
            # the walls act on the atoms' centres, as the forces' walls do: the box is the same region of the centres in
            # both dynamics (review LB1-physics P4)
            self.md = HD.HardSpheres(self.ndim, self.box, boundary, seed=int(seed), walls_on="centre", t=t0)
        else:
            self.md = MD(dim=self.ndim, box=self.box, boundary=boundary, pair=self._pair_term(),
                         dt=float(self.live["dt_fs"]) * 1e-3 / PS, seed=int(seed), t=t0)
        self.PALETTE = palette(self.ndim)
        self._kcache = {}   # object id -> its atoms' keys (derived; cleared at every change)
        # the order parameter for ``meas``, the world time it was computed at and its period's number (ORDER_EVERY_PS)
        self._order, self._order_t, self._order_bucket = None, None, None
        self.parts = {}     # object id -> np.array of particle keys (atoms, gas, crystal) or molecule keys
        self.kind = {}      # object id -> what the engine holds for it
        self.species = {}   # object id -> species name in the engine
        self.info = {}      # object id -> what the engine reported when it was made (a crystal's lattice)
        self.conv = {}      # axis -> ids of the walls / the piston that made that periodic axis walled (review U7)
        self.n_stats = 0
        self._dup = False
        self._piston_pos = None
        self._zb = {"blocks": [], "prev": None, "t_change": 0.0}
        self.start_scene()
        self._after_change()
        self.default_speed = 2.0e-12  # 2 ps of the world per second
        self.legacy = legacy_note(params.get("scene"))

    def after_header(self):
        super().after_header()
        if self.legacy:   # a scene file of the old format, read with the same laws (said once, at the start)
            self.emit({"type": "notice", "t": self.t, "text": self.legacy})

    def _pair_term(self):
        if self.live["model"] == "wca":
            return IA.WCA()
        return IA.LennardJones(float(self.live["cutoff"]), shift=self.live["shift"])

    # --- conversions -----------------------------------------------------------------------------------------------
    def _len(self, nm):
        return float(nm) / NM

    def _region_of(self, v):
        c = [float(v.get(c, 0.0)) for c in "xyz"[:self.ndim]]
        s = [float(v.get(f"s{c}", 0.0)) for c in "xyz"[:self.ndim]]
        if not any(s):
            return None
        lo = [self._len(c[i] - 0.5 * s[i]) if s[i] > 0 else 0.0 for i in range(self.ndim)]
        hi = [self._len(c[i] + 0.5 * s[i]) if s[i] > 0 else self.box[i] for i in range(self.ndim)]
        return (lo, hi)

    def _subst_values(self, v):
        if v.get("substance", "argon") == "argon":
            return 1.0, 1.0, 1.0, 0.0
        q = U.from_elementary_charge(float(v.get("charge", 0.0)))
        return U.from_amu(float(v["mass"])), float(v["sigma"]), float(v.get("epsilon", 1.0)), q

    def _species(self, obj):
        """One engine species per particle object (its own parameters): argon or the given ones, in reduced units; an
        existing one (the object made again) is changed in place in both worlds."""
        oid = obj["id"]
        m, s, e, q = self._subst_values(obj["values"])
        exists = oid in self._sp_names()
        if self.hard:
            if exists:
                self.md.set_species(oid, mass=m, sigma=s)
            else:
                self.md.add_species(oid, mass=m, sigma=s)
        elif exists:
            self.md.set_species(oid, mass=m, sigma=s, epsilon=e, charge=q)
        else:
            self.md.add_species(oid, mass=m, sigma=s, epsilon=e, charge=q)
        self.species[oid] = oid
        return oid

    def _sp_names(self):
        return [d["name"] for d in self.md.species()]

    def _sp(self, name):
        return next((d for d in self.md.species() if d["name"] == name), None)

    def _xs(self):
        """The particles' positions (wrapped on periodic axes) and diameters (reduced)."""
        md = self.md
        x = np.asarray(md.positions(), float).reshape(-1, self.ndim).copy()
        per = np.flatnonzero(md.periodic)
        L = np.array(self.box)
        for a in per:
            x[:, a] -= L[a] * np.floor(x[:, a] / L[a])
        sig = {d["name"]: float(d.get("sigma", 1.0)) for d in md.species()}
        names = md.particles()["species"] if md.n else []
        return x, np.array([sig[q] for q in names], float)

    def _hi(self, a):
        """The upper end of axis a for the particles: the piston's face on its axis, else the box."""
        if not self.hard:
            p = self.md.piston()
            if p is not None and "xyz".index(p["axis"]) == a:
                return float(p["X"])
        return self.box[a]

    # --- placement (reviews UX-ui U4, U8; the integrator's API of 2026-11-05) -----------------------------------
    def _import_values(self, kind, values):
        """An object's values as this world takes them (LB1, P16.1: a scene carried over into a new world of the other
        space): in a plane the keys of z (its coordinate, region size, speed) are dropped; a wall or a piston across z
        is refused (a plane has no z). Values of the plane in a volume take z's defaults. A copy."""
        values = dict(values or {})
        if self.ndim == 2:
            if kind in ("wall", "piston") and values.get("axis") == "z":
                if kind == "wall":
                    raise refusal(T("a plane has no axis z: a wall across z cannot be carried over"),
                                  hint=T("put it across x or y, or go back to the volume (“Space”)"))
                raise refusal(T("a plane has no axis z: a piston across z cannot be carried over"),
                              hint=T("put it across x or y, or go back to the volume (“Space”)"))
            for k in AXIS_KEYS:
                values.pop(k, None)
        return values

    def _values(self, ot, values):
        # every path that adds an object (a palette form, a scene file, a scene carried over) takes the values so
        return super()._values(ot, self._import_values(ot.type, values))

    def place(self, kind, values):
        """A palette object's values before it is added: the defaults completed, a clicked point (``position``, nm)
        taken as the object's place (a region's centre, the nearest face for a wall or a piston), an atom moved to the
        nearest free spot inside the box, a piston above the atoms below it; what cannot fit is refused at once with
        the numbers (a gas or molecules denser than random packing allows, a temperature the time step cannot
        resolve). Deterministic: it reads the state, never changes it."""
        ot = self._type(kind)
        values = self._import_values(kind, values)
        # a clicked point is a list; the piston's own "position" is a number
        pos = values.pop("position") if isinstance(values.get("position"), (list, tuple)) else None
        v, errors = ot.schema.resolve(None, values)
        if errors:
            raise refusal(join(errors))
        v = dict(v)
        nd = self.ndim
        if pos is not None:
            pos = [float(q) for q in list(pos)[:nd]]
            if kind in ("atom", "probe"):
                for i, c in enumerate("xyz"[:nd]):
                    v[c] = pos[i]
            elif kind in ("gas", "crystal", "molecule", "thermostat"):
                for i, c in enumerate("xyz"[:nd]):
                    v[c] = pos[i]
                    if not float(v.get(f"s{c}", 0.0)):
                        v[f"s{c}"] = round(self.box[i] * NM / 3.0, 4)
            elif kind in ("wall", "piston"):
                a, side = self._nearest_face(pos)
                v["axis"] = "xyz"[a]
                if kind == "wall":
                    v["side"] = side
                else:
                    v["position"] = round(min(max(pos[a], 0.0), self.box[a] * NM), 4)
        carrying = getattr(self, "carrying", None) is not None   # its atoms come with their places (on_add)
        if kind == "atom" and not carrying:
            sig = self._subst_values(v)[1]
            x = self._free_spot(sig, [self._len(v[c]) for c in "xyz"[:nd]])
            for i, c in enumerate("xyz"[:nd]):
                v[c] = round(x[i] * NM, 6)
        elif kind == "probe":
            for i, c in enumerate("xyz"[:nd]):
                v[c] = round(min(max(float(v[c]), 0.0), self.box[i] * NM), 6)
            per = [i for i in range(nd) if self.md.periodic[i]]
            if per:
                v["r"] = min(float(v["r"]), round(0.5 * min(self.box[i] for i in per) * NM, 6))
        elif kind == "piston" and not carrying:
            v["position"] = self._piston_position(v)
            # the framework takes a returned "position" for a clicked point and drops a number: kept here for on_add
            self._piston_pos = v["position"]
        elif kind in ("gas", "molecule") and not carrying:
            self._pack_check(kind, v)
        self._check_temperature(kind, v)
        return v

    def _nearest_face(self, pos):
        best = None
        for a in range(self.ndim):
            L = self.box[a] * NM
            for side, d in (("lo", abs(pos[a])), ("hi", abs(L - pos[a]))):
                if best is None or d < best[0]:
                    best = (d, a, side)
        return best[1], best[2]

    def _allowed(self, sig):
        """Per axis the interval a particle's centre of diameter ``sig`` may take (reduced)."""
        lo, hi = [], []
        for a in range(self.ndim):
            if self.md.periodic[a]:
                lo.append(0.0)
                hi.append(self.box[a])
            else:
                lo.append(0.5 * sig)
                hi.append(self._hi(a) - 0.5 * sig)
        return np.array(lo), np.array(hi)

    def _is_free(self, sig, x):
        lo, hi = self._allowed(sig)
        x = np.asarray(x, float)
        if np.any((x < lo) | (x > hi)):
            return False
        X, S = self._xs()
        xw = x.copy()
        for a in np.flatnonzero(self.md.periodic):
            xw[a] -= self.box[a] * math.floor(xw[a] / self.box[a])
        return bool(free_sites(xw[None], sig, X, S, self.box, self.md.periodic)[0])

    def _free_spot(self, sig, x0, refuse=True):
        """The free point nearest to x0 (reduced): no particle nearer than sigma_ij, inside the walls (sigma/2 from
        them) and below the piston; first on a fine grid around x0, then on a coarser one over the whole box. None
        (or a refusal) when there is none."""
        lo, hi = self._allowed(sig)
        L = np.array(self.box)
        per = np.asarray(self.md.periodic, bool)
        if np.any(hi < lo):
            if not refuse:
                return None
            raise refusal(T("an atom of diameter {d:.3g} nm does not fit between the box's walls", d=sig * NM),
                          hint=T("a smaller size σ of the atom, or a larger box (while the world runs)"))
        x0 = np.asarray(x0, float).copy()
        for a in range(self.ndim):
            x0[a] = x0[a] - L[a] * math.floor(x0[a] / L[a]) if per[a] else min(max(x0[a], lo[a]), hi[a])
        X, S = self._xs()

        def nearest(points):
            pw = points.copy()
            for a in np.flatnonzero(per):
                pw[:, a] -= L[a] * np.floor(pw[:, a] / L[a])
            ok = np.all((pw >= lo - 1e-12) & (pw <= hi + 1e-12), axis=1)
            pw = pw[ok]
            if not len(pw):
                return None
            free = free_sites(pw, sig, X, S, L, per)
            if not free.any():
                return None
            pw = pw[free]
            dx = pw - x0
            for a in np.flatnonzero(per):
                dx[:, a] -= L[a] * np.rint(dx[:, a] / L[a])
            d2 = np.einsum("ij,ij->i", dx, dx)
            return pw[int(np.argmin(d2))]

        h = 0.2 * sig
        g = np.arange(-20, 21) * h
        local = np.stack(np.meshgrid(*([g] * self.ndim), indexing="ij"), -1).reshape(-1, self.ndim) + x0
        got = nearest(local)
        if got is None:
            span = hi - lo
            step = max(0.3 * sig, float((np.prod(np.maximum(span, sig)) / 3e5) ** (1.0 / self.ndim)))
            axes = [np.linspace(lo[a], hi[a], max(2, int(span[a] / step) + 1)) for a in range(self.ndim)]
            got = nearest(np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, self.ndim))
        if got is None and refuse:
            raise refusal(T("the box has no free place for an atom of diameter {d:.3g} nm", d=sig * NM),
                          hint=T("remove some atoms, decrease the atom's σ or make the box larger (while the world runs)"))
        return got

    def _piston_position(self, v):
        """The piston's face in nm: as asked, but above every atom's centre on its axis (the gas side is below the face;
        the face, like a wall, reflects the centres)."""
        a = "xyz".index(v["axis"])
        X = self._len(v["position"])
        L = self.box[a]
        x, sig = self._xs()
        need = float(np.max(x[:, a])) * (1 + 1e-9) if len(x) else 0.0
        X = min(max(X, need, 1e-3 * L * 1.01), L)
        return math.ceil(X * NM * 1e6) / 1e6 if X < L else round(L * NM, 9)

    def _pack_check(self, kind, v):
        """Refuse at once what random placement cannot fit (review UX-ui U5, UX-params P33): the covered fraction of the
        region with the atoms already in it and the new ones, against where random sequential insertion jams."""
        nd = self.ndim
        reg = self._region_of(v)
        lo = np.array(reg[0]) if reg else np.zeros(nd)
        hi = np.array(reg[1]) if reg else np.array([self._hi(a) for a in range(nd)])
        lo, hi = np.maximum(lo, 0.0), np.minimum(hi, [self._hi(a) for a in range(nd)])
        if np.any(hi <= lo):
            raise refusal(T("the object's region lies outside the box"),
                          hint=T("the region's centre and sizes inside the box {size} (size 0: the whole box)",
                                 size=self._size([b * NM for b in self.box])))
        V = float(np.prod(hi - lo))
        sig = self._subst_values(v)[1]
        v1 = (math.pi / 4 * sig ** 2) if nd == 2 else (math.pi / 6 * sig ** 3)
        X, S = self._xs()
        inside = np.all((X >= lo) & (X <= hi), axis=1) if len(X) else np.zeros(0, bool)
        vs = (math.pi / 4 * S ** 2) if nd == 2 else (math.pi / 6 * S ** 3)
        have = float(np.sum(vs[inside])) if len(X) else 0.0
        if kind == "gas":
            per, n, lim = 1, int(v["n"]), JAM[nd]
        else:
            per = 2 if v["shape"] == "dimer" else 3 if v["shape"] == "bent" else int(v["atoms"])
            n, lim = int(v["count"]), MOL_JAM[nd]
        eta = (have + n * per * v1) / V
        if eta > lim:
            n_max = max(0, int((lim * V - have) / (per * v1)))
            area = self._size([(h - l) * NM for l, h in zip(lo, hi)])
            what = T("{n:d} atoms", n=n) if kind == "gas" else T("{n:d} molecules", n=n)
            frac = (T("{p:.0f} % of the area", p=100 * eta) if nd == 2 else T("{p:.0f} % of the volume", p=100 * eta))
            raise refusal(T("{what} in the region {area} would cover {frac} (with the atoms already there): random "
                            "placement without overlaps fits at most ≈ {lim:.0f} %", what=what, area=area, frac=frac,
                            lim=100 * lim),
                          hint=(T("at most {n:d} atoms, or a larger region; denser: “Crystal”", n=n_max) if kind == "gas"
                                else T("at most {n:d} molecules, or a larger region; denser: “Crystal”", n=n_max)))
        if _require is not None:
            n_all = len(X) + n * per
            rl = (float(self.live["cutoff"]) if self.live["model"] == "lj" else 1.13) * max(sig, float(S.max())
                                                                                            if len(S) else 1.0) + 0.3
            vol = float(np.prod(self.box))
            ball = (math.pi * rl ** 2) if nd == 2 else (4.0 / 3.0 * math.pi * rl ** 3)
            pairs = 0.5 * n_all * min(n_all, n_all / vol * ball * max(1.0, eta / max(n_all * v1 / vol, 1e-9)))
            _require(int(pairs * PAIR_BYTES), T("the list of neighbouring pairs of atoms"),
                     T("fewer atoms or a smaller cutoff radius"))

    def _lightest(self):
        ms = [float(d["mass"]) for d in self.md.species() if math.isfinite(d["mass"])]
        return min(ms) if ms else 1.0

    def _smallest(self):
        ss = [float(d.get("sigma", 1.0)) for d in self.md.species()]
        return min(ss) if ss else 1.0

    def _step_q(self, vel, energy, sig, eps, dt):
        """q = 12 v dt / r_t: the step against the steepness of the repulsion at the collision energy ``energy``."""
        if vel <= 0 or eps <= 0:
            return 0.0
        r_t = sig * min((4.0 * eps / energy) ** (1.0 / 12.0), 2.0 ** (1.0 / 6.0)) if energy > 0 else sig
        return 12.0 * vel * dt / r_t

    def _check_temperature(self, kind, v, dt=None):
        """Refuse a temperature (or a speed) the time step cannot resolve (q > Q_MAX; review UX-params P32: at 10^5 K
        the Verlet step let atoms pass into each other and the world stopped with a traceback), with the largest
        temperature at this step and the step for this temperature."""
        if self.hard or kind not in ("gas", "crystal", "molecule", "atom", "thermostat", "wall"):
            return
        if kind == "wall" and v.get("kind") != "thermal":
            return
        nd = self.ndim
        dt = self.md.dt if dt is None else dt
        dt_fs = dt * PS * 1e3
        own = kind in ("gas", "crystal", "molecule", "atom")
        m, sig, eps, _ = self._subst_values(v) if own else (self._lightest(), self._smallest(), 1.0, 0.0)
        if kind == "atom":
            vel = math.sqrt(sum((float(v.get(f"v{c}", 0.0)) / U.velocity_m_s) ** 2 for c in "xyz"[:nd]))
            q = self._step_q(vel, 0.5 * m * vel * vel, sig, eps, dt)
            if q <= Q_MAX:
                return
            # v^(7/6) (m/2)^(1/12) = Q_MAX sigma (4 eps)^(1/12) / (12 dt)
            v_ok = (Q_MAX * sig * (4.0 * eps) ** (1 / 12) / (12.0 * dt) / (0.5 * m) ** (1 / 12)) ** (6 / 7)
            raise refusal(T("an atom with the speed {v:.3g} m/s: the step {dt:.3g} fs does not resolve its collisions (in "
                            "a step it travels {q:.2g} of the thickness of the steep part of the repulsion, at most "
                            "{qmax:.3g} is allowed)", v=vel * U.velocity_m_s, dt=dt_fs, q=q, qmax=Q_MAX),
                          hint=T("a speed of at most {v:.3g} m/s, or a “Time step” of at most {dt:.2g} fs (changes while "
                                 "the world runs, in the “Set-up”)", v=v_ok * U.velocity_m_s, dt=dt_fs * Q_MAX / q))
        Tr = float(v.get("T", 0.0)) / KELVIN
        vc = math.sqrt(sum((float(v.get(f"v{c}", 0.0)) / U.velocity_m_s) ** 2 for c in "xyz"[:nd])) if own else 0.0
        if vc > 0:
            # a thrown group: its atoms meet the others at the thermal speed plus the centre's (LB1, P16.2)
            vel = math.sqrt(nd * Tr / m) + vc
            q = self._step_q(vel, 0.5 * m * vel * vel, sig, eps, dt)
            if q > Q_MAX:
                v_ok = max(0.0, (Q_MAX / q) ** (6.0 / 7.0) * vel - math.sqrt(nd * Tr / m))
                raise refusal(T("a centre-of-mass speed of {v:.3g} m/s at {T:.4g} K: the step {dt:.3g} fs does not resolve "
                                "the atoms' collisions (in a step an atom travels {q:.2g} of the thickness of the steep "
                                "part of the repulsion, at most {qmax:.3g} is allowed)", v=vc * U.velocity_m_s,
                                T=float(v.get("T", 0.0)), dt=dt_fs, q=q, qmax=Q_MAX),
                              hint=T("a centre-of-mass speed of at most ≈ {v:.2g} m/s, or a “Time step” of at most "
                                     "{dt:.2g} fs (while the world runs)", v=v_ok * U.velocity_m_s, dt=dt_fs * Q_MAX / q))
        if Tr <= 0:
            return
        q = self._step_q(math.sqrt(nd * Tr / m), Tr, sig, eps, dt)
        if q <= Q_MAX:
            return
        # q ∝ T^(1/2 + 1/12): the largest T at this step, and the step for this T (q ∝ dt)
        T_ok = Tr * (Q_MAX / q) ** (12.0 / 7.0)
        raise refusal(T("at {T:.4g} K the step {dt:.3g} fs does not resolve the atoms' collisions (in a step an atom travels "
                        "{q:.2g} of the thickness of the steep part of the repulsion, at most {qmax:.3g} is allowed): the "
                        "atoms would pass into each other", T=float(v["T"]), dt=dt_fs, q=q, qmax=Q_MAX),
                      hint=T("a temperature of at most {T:.3g} K at this step, or a “Time step” of at most {dt:.2g} fs "
                             "(changes while the world runs, in the “Set-up”)", T=T_ok * KELVIN, dt=dt_fs * Q_MAX / q))

    def palette_state(self):
        """The palette types the world cannot take now (review UX-ui U7, U22): what the hard spheres have not
        (molecules, the piston, thermostats, the field: LB1, one palette for both dynamics), and, in a box already
        packed beyond random insertion, a gas or molecules; walls and the piston work on every axis (a periodic one
        becomes walled)."""
        out = {}
        if self.hard:
            for k in ("molecule", "piston", "thermostat", "gravity"):
                out[k] = T("{what}: switch “Dynamics” to continuous forces (while the world runs, in the “Laws”)",
                           what=self._hard_lacks(k))
        X, S = self._xs()
        if not len(X):
            return out
        nd = self.ndim
        vs = (math.pi / 4 * S ** 2) if nd == 2 else (math.pi / 6 * S ** 3)
        eta = float(np.sum(vs)) / float(np.prod([self._hi(a) for a in range(nd)]))
        if eta > JAM[nd]:
            out["gas"] = T("the box is already {p:.0f} % full: random placement fits no more atoms; remove some atoms",
                           p=100 * eta)
        if eta > MOL_JAM[nd] and "molecule" in self.PALETTE and "molecule" not in out:
            out["molecule"] = T("the box is already {p:.0f} % full: molecules do not fit; remove some atoms", p=100 * eta)
        return out

    def _hard_lacks(self, kind):
        """What hard disks or spheres have not, for the palette's reason and a refusal."""
        if self.ndim == 2:
            return {"molecule": T("hard disks have no molecules (bonds)"), "piston": T("hard disks have no piston"),
                    "thermostat": T("hard disks have no thermostats"), "gravity": T("hard disks have no field")}[kind]
        return {"molecule": T("hard spheres have no molecules (bonds)"), "piston": T("hard spheres have no piston"),
                "thermostat": T("hard spheres have no thermostats"), "gravity": T("hard spheres have no field")}[kind]

    # --- all-or-nothing changes (review B7-md M6) -----------------------------------------------------------------
    _MAPS = ("parts", "kind", "species", "info", "_zb", "conv", "live", "model", "box", "hard", "_ramp_seen", "_ramp_T0")

    def _snapshot(self):
        # the solver's class too: a refused switch of the dynamics puts the other solver back (LB1)
        return (type(self.md), self.md.state_dict(), {k: copy.deepcopy(getattr(self, k)) for k in self._MAPS},
                copy.deepcopy(self.rng.bit_generator.state))

    def _restore(self, snap):
        cls, st, maps, rng = snap
        self.md = cls.from_state_dict(st)
        for k, v in maps.items():
            setattr(self, k, v)
        self.rng.bit_generator.state = rng
        self._kcache = {}

    def _atomic(self, fn, *a):
        snap = self._snapshot()
        try:
            fn(*a)
            self._after_change()
        except BaseException as e:
            self._restore(snap)
            if isinstance(e, Exception) and not _is_owner_text(e):
                raise _owner(e, self) from e
            raise

    def _after_change(self):
        """A change of the scene: the counters (heat, work, impulses, the first-law balance), the momentum's
        reference, the mean-square displacement and the hard world's pressure blocks restart now."""
        self.md.reset_counters()
        self.md.msd_origin()
        self._zb = {"blocks": [], "prev": None, "t_change": float(self.md.t)}
        self._kcache = {}

    # --- the framework's hooks -------------------------------------------------------------------------------------
    def scene(self, args):
        # a copy lands on its original by design (lfviz.playground): this section moves it to a free spot (U4)
        self._dup = args.get("op") == "duplicate"
        self._piston_pos = None
        try:
            return super().scene(args)
        finally:
            self._dup = False
            self._piston_pos = None

    def on_add(self, obj, state):
        if state is not None and getattr(self, "carrying", None) is not None and obj["type"] in CARRIED:
            # a carry-over into a new world (review LB1-framework F5): the atoms with their positions and velocities
            why = self._carry_mismatch(state)
            if why is None:
                try:
                    self._atomic(self._add_carried, obj, state)
                    return
                except Exception as e:  # noqa: BLE001 - started again from the parameters, said in the notice
                    why = text_of(e)
            self._carry_note(T("{what:cap} started anew from the parameters: {why}", what=CARRIED[obj["type"]], why=why),
                             obj, restarted=True)
        self._atomic(self._add_obj, obj)

    def on_remove(self, obj):
        self._atomic(self._remove_obj, obj)

    def on_set(self, obj, old):
        self._atomic(self._set_obj, obj, old)

    def _note(self, text):
        """A short note for the owner about what an edit did (shown at once: ``notify``)."""
        if not self._loading:
            self.emit({"type": "event", "kind": "scene", "t": self.t, "text": text, "notify": True})

    def _add_obj(self, obj):
        t, v, md = obj["type"], obj["values"], self.md
        oid = obj["id"]
        if self.hard and t in ("molecule", "piston", "thermostat", "gravity"):   # (a scene file or a carry-over)
            raise refusal(self._hard_lacks(t), hint=T("“Dynamics” = continuous forces (while the world runs)"))
        if t in ("gas", "crystal", "atom", "molecule", "thermostat", "wall"):
            self._check_temperature(t, v)
        if t in ("gas", "crystal", "atom", "molecule"):
            if t in ("gas", "molecule"):
                self._pack_check(t, v)
            sp = self._species(obj)
            Tred = float(v.get("T", 0.0)) / KELVIN
            if t == "gas":
                keys = self._gas(sp, int(v["n"]), self._region_of(v), Tred, v["start"])
            elif t == "crystal":
                inf = {}
                keys = md.fill(sp, density=float(v["density"]), region=self._region_of(v), T=Tred, info=inf,
                               skip_occupied=True)
                self.info[oid] = inf
                if inf.get("skipped"):
                    self._note(T("“{label}”: {n:d} lattice sites are taken by atoms already there and were left empty",
                                 label=obj["label"], n=int(inf["skipped"])))
            elif t == "atom":
                keys = self._atom(obj, sp)
            else:
                keys = self._molecules(obj, sp, Tred)
            self.parts[oid] = np.asarray(keys)
            self.kind[oid] = "molecules" if t == "molecule" else "particles"
            self._kcache.pop(oid, None)
            vc = np.array([float(v.get(f"v{c}", 0.0)) / U.velocity_m_s for c in "xyz"[:self.ndim]])
            if t != "atom" and np.any(vc):      # the group's centre-of-mass velocity (a throw, LB1)
                ak = self._atom_keys(oid)
                if len(ak):
                    md.set(ak, v=md.particles(ak)["v"] + vc)
        elif t == "wall":
            self._make_walled("xyz".index(v["axis"]), oid)
            self._wall(v)
            self.kind[oid] = "wall"
        elif t == "piston":
            if getattr(self, "_piston_pos", None) is not None:
                v["position"] = self._piston_pos
            a = "xyz".index(v["axis"])
            self._make_walled(a, oid)
            self._check_piston(v)
            self._piston(v)
            self.kind[oid] = "piston"
        elif t == "thermostat":
            self._region_inside(v)
            self.parts[oid] = md.add_thermostat(v["kind"], float(v["T"]) / KELVIN, region=self._region_of(v),
                                                **self._bath_args(v))
            self.kind[oid] = "thermostat"
        elif t == "gravity":
            md.set_gravity(self._gvec(v))
            self.kind[oid] = "gravity"
        elif t == "probe":
            self._point_inside(v)
            self.kind[oid] = "probe"

    def _point_inside(self, v):
        """A probe's centre inside the box along its walled axes (review UX-ui U8: far outside it was accepted)."""
        for i, c in enumerate("xyz"[:self.ndim]):
            if not self.md.periodic[i] and not (0.0 <= float(v[c]) <= self.box[i] * NM):
                raise refusal(T("the thermometer's centre along the axis {c} ({x:.4g} nm) is outside the box", c=c,
                                x=float(v[c])),
                              hint=T("{c} from 0 to {L:.4g} nm", c=c, L=self.box[i] * NM))

    def _region_inside(self, v):
        reg = self._region_of(v)
        if reg is None:
            return
        for i in range(self.ndim):
            if not self.md.periodic[i] and (reg[1][i] <= 0.0 or reg[0][i] >= self.box[i]):
                raise refusal(T("the thermostat's region along the axis {c} lies outside the box", c="xyz"[i]),
                              hint=T("the region's centre and sizes inside the box (size 0: the whole box)"))

    def _atom(self, obj, sp):
        """One atom: at its place when that is free; a copy (⧉) goes to the nearest free spot; an occupied or outside
        place is refused with the nearest free one (review UX-ui U4, U8)."""
        v = obj["values"]
        x = np.array([self._len(v[c]) for c in "xyz"[:self.ndim]])
        sig = self._sp(sp)["sigma"]
        if not self._is_free(sig, x):
            spot = self._free_spot(sig, x)
            if self._dup:
                x = spot
                for i, c in enumerate("xyz"[:self.ndim]):
                    v[c] = round(spot[i] * NM, 6)
            else:
                lo, hi = self._allowed(sig)
                out = [c for i, c in enumerate("xyz"[:self.ndim]) if not (lo[i] <= x[i] <= hi[i])]
                where = (T("beyond the box's wall along the axis {a}", a=", ".join(out)) if out
                         else T("closer than σ to another atom (the atoms would overlap)"))
                raise refusal(T("the atom at the point {at}: {where}", at=self._point([q * NM for q in x]), where=where),
                              hint=T("the nearest free place is {at}", at=self._point([q * NM for q in spot])))
        vel = np.array([float(v[f"v{c}"]) / U.velocity_m_s for c in "xyz"[:self.ndim]])
        return self.md.add(sp, x, v=vel)

    def _check_piston(self, v):
        a = "xyz".index(v["axis"])
        X = self._len(v["position"])
        x, sig = self._xs()
        need = float(np.max(x[:, a])) if len(x) else 0.0
        if X > self.box[a] * (1 + 1e-12) or X <= 0:
            raise refusal(T("the piston at {x:.3g} nm is outside the box (along the axis {a} it is {L:.4g} nm)",
                            x=float(v["position"]), a=v["axis"], L=self.box[a] * NM),
                          hint=T("a position from {lo:.4g} to {hi:.4g} nm", lo=need * NM, hi=self.box[a] * NM))
        if X < need:
            raise refusal(T("the atoms do not fit under the piston at {x:.3g} nm: the highest along the axis {a} reaches "
                            "{top:.4g} nm", x=float(v["position"]), a=v["axis"], top=need * NM),
                          hint=T("a piston position of at least {x:.3g} nm", x=math.ceil(need * NM * 1e4) / 1e4))

    def _make_walled(self, a, oid):
        """A wall or the piston on a periodic axis makes it walled at the current moment (review UX-ui U7, UX-params
        P31); the axis returns to periodic when the last such object goes."""
        if self.md.periodic[a]:
            try:
                self.md.set_boundary(a, "walls")
            except ValueError as e:
                raise refusal(T("the axis {a} is periodic and there are atoms at its faces: a wall cannot be put there "
                                "without moving them", a="xyz"[a]),
                              hint=T("remove the atoms at the faces or start a new world with “Boundaries at the start” "
                                     "= walls"), detail=str(e)) from e
            self.conv[a] = set()
            self._note(T("the axis {a} now has walls (specular walls at its faces); when the last wall or piston on it "
                         "goes, it becomes periodic again", a="xyz"[a]))
        if a in self.conv:
            self.conv[a].add(oid)

    def _release_axis(self, oid, a=None):
        for ax in [a] if a is not None else list(self.conv):
            ids = self.conv.get(ax)
            if ids is None:
                continue
            ids.discard(oid)
            if not ids:
                del self.conv[ax]
                try:
                    self.md.set_boundary(ax, "periodic")
                    self._note(T("the axis {a} is periodic again (its walls removed)", a="xyz"[ax]))
                except ValueError as e:
                    self._note(T("the axis {a} keeps its (specular) walls: atoms at the opposite faces would overlap "
                                 "if it were periodic ({why})", a="xyz"[ax], why=text_of(_owner(e, self))))

    def _gas(self, sp, n, region, T, start):
        keys = self.md.fill(sp, n=n, region=region, T=T, arrangement="random")
        if start == "same_speed" and len(keys):
            # every atom with the speed of the mean kinetic energy at T, in random directions (not Maxwellian); with one
            # atom or T = 0 there is nothing to rescale (review UX-params P32: 0/0)
            m = self._sp(sp)["mass"]
            speed = math.sqrt(self.ndim * T / m)
            d = self.rng.normal(size=(len(keys), self.ndim))
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            vel = speed * d
            if len(keys) > 1:
                vel -= vel.mean(axis=0)
            ms = math.sqrt(float(np.mean(np.sum(vel * vel, axis=1))))
            if ms > 0 and speed > 0:
                vel *= speed / ms
            self.md.set(keys, v=vel)
        return keys

    def _molecules(self, obj, sp, Tr):
        """``count`` molecules at random places and orientations, each atom's potential energy at insertion below
        2kT (at least 0.1 ε); "maxwell": every atom's velocity Maxwellian at T and the bond lengths and angles drawn
        about their rest values with the Boltzmann spread √(kT/k) (harmonic terms: each starts with about kT/2), the
        canonical start; "translation": every molecule moves as a whole with a Maxwellian velocity of its mass at T,
        rest geometry (no rotation, no vibration). The object's total momentum is removed (review B7-md M4).

        Placed in batches (review UX-ui U5: one engine edit per try took minutes): candidates for all the molecules
        still missing are drawn at once and inserted in one edit (``MD.add_molecules``: candidates over the energy
        bound left out, the first ones in order kept), until all are placed or 200 tries per molecule were spent."""
        v, md, oid = obj["values"], self.md, obj["id"]
        shape = v["shape"]
        na = 2 if shape == "dimer" else 3 if shape == "bent" else int(v["atoms"])
        b0, kb = float(v["bond"]), float(v["k_bond"])
        md.set_bond_type(f"{oid}-b", IA.HarmonicBond(kb, b0))
        th0 = math.radians(float(v.get("angle", 180.0))) if na >= 3 else math.pi
        ka = float(v.get("k_angle", 0.0))
        if na >= 3:
            md.set_angle_type(f"{oid}-a", IA.HarmonicAngle(ka, th0))
        bonds = [(i, i + 1, f"{oid}-b") for i in range(na - 1)]
        angles = [(i, i + 1, i + 2, f"{oid}-a") for i in range(na - 2)]
        thermal = v.get("start", "maxwell") == "maxwell" and Tr > 0
        m_atom = self._sp(sp)["mass"]
        reg = self._region_of(v) or ([0.0] * self.ndim, [self._hi(a) for a in range(self.ndim)])
        lo, hi = np.array(reg[0]), np.array(reg[1])
        e_max = max(2.0 * Tr, 0.1)
        count = int(v["count"])
        mks, tries = [], 0
        while len(mks) < count:
            need = count - len(mks)
            k = min(4 * need + 16, 4096, 200 * count - tries)
            if k <= 0:
                raise refusal(T("{n:d} molecules could not be placed without overlaps: {k:d} placed", n=count, k=len(mks)),
                              hint=T("fewer molecules or a larger region"))
            tries += k
            X = self._mol_candidates(k, na, b0, kb, th0, ka, thermal, Tr, lo, hi)
            vel = None
            if not thermal:
                vc = (self.rng.normal(size=(k, 1, self.ndim)) * math.sqrt(Tr / (na * m_atom)) if Tr > 0
                      else np.zeros((k, 1, self.ndim)))
                vel = np.broadcast_to(vc, (k, na, self.ndim))
            _, mk, _ = md.add_molecules(sp, X, bonds=bonds, angles=angles, v=vel, T=Tr if thermal else None,
                                        max_energy=e_max, limit=need)
            mks.extend(int(q) for q in mk)
        keys = np.concatenate([md.molecules()[mk] for mk in mks])
        if len(keys) > 1:
            vel = md.particles(keys)["v"]
            md.set(keys, v=vel - vel.mean(axis=0))   # one species: equal masses
        return mks

    def _mol_candidates(self, k, na, b0, kb, th0, ka, thermal, T, lo, hi):
        """k candidate molecules (k, na, d): a planar zigzag with this molecule's bond lengths and angles (Boltzmann
        spreads at a thermal start), turned at random, centred at random in [lo, hi]."""
        nd = self.ndim
        bl = b0 + (self.rng.normal(size=(k, na - 1)) * math.sqrt(T / kb) if thermal else 0.0)
        bl = np.maximum(np.broadcast_to(bl, (k, na - 1)), 0.3 * b0)
        if na >= 3:
            th = th0 + (self.rng.normal(size=(k, na - 2)) * math.sqrt(T / ka) if thermal and ka > 0 else 0.0)
            th = np.clip(np.broadcast_to(th, (k, na - 2)), 0.05, math.pi)
        pts = np.zeros((k, na, 3))
        pts[:, 1, 0] = bl[:, 0]
        heading = np.zeros(k)
        for j in range(1, na - 1):
            heading = heading + (math.pi - th[:, j - 1]) * (1 if j % 2 else -1)
            pts[:, j + 1, 0] = pts[:, j, 0] + bl[:, j] * np.cos(heading)
            pts[:, j + 1, 1] = pts[:, j, 1] + bl[:, j] * np.sin(heading)
        tpl = pts[:, :, :nd]
        tpl = tpl - tpl.mean(axis=1, keepdims=True)
        if nd == 2:
            a = 2 * math.pi * self.rng.random(k)
            R = np.stack([np.stack([np.cos(a), -np.sin(a)], -1), np.stack([np.sin(a), np.cos(a)], -1)], -2)
        else:
            q = self.rng.normal(size=(k, 4))
            q /= np.linalg.norm(q, axis=1, keepdims=True)
            w, x, y, z = q.T
            R = np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                          np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                          np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)
        c = lo + (hi - lo) * self.rng.random((k, nd))
        return np.einsum("kij,knj->kni", R, tpl) + c[:, None, :]

    def _wall(self, v, reset=False):
        kind = "specular" if reset else v["kind"]
        args = {}
        if kind == "thermal":
            Tr = float(v["T"]) / KELVIN
            if not Tr > 0:
                raise refusal(T("a thermal wall needs a temperature above 0 K"),
                              hint=T("a wall temperature > 0 K, or a specular wall"))
            args["T"] = Tr
        if self.hard and kind == "soft":
            raise refusal(T("hard spheres have no soft wall"), hint=T("a specular or a thermal wall"))
        if kind == "soft":
            args["term"] = IA.LJWall(self.ndim)
        self.md.set_wall(v["axis"], v["side"], kind, **args)

    def _piston(self, v, old=None):
        """Put the piston or change it. Its position is set when it is put or when "position" itself is edited; its
        velocity when it is put or its mass or driven speed is edited (review B7-md M12): an edit of the pressure
        acts on the piston where it is."""
        p = float(v["p_ext"])
        p_red = U.from_bar(p) if self.ndim == 3 else p * 1e-3 / U.pressure_Pa(2)
        m = float(v["mass"])
        kw = {"p_ext": p_red}
        if old is None or old.get("position") != v["position"] or old.get("axis") != v["axis"]:
            kw["X"] = self._len(v["position"])
        if m > 0:
            kw["mass"] = U.from_amu(m)
        else:
            kw["mass"] = math.inf
            if old is None or old.get("speed") != v["speed"] or old.get("mass") != v["mass"]:
                kw["V"] = float(v["speed"]) / U.velocity_m_s
        if old is not None and m > 0 and float(old.get("mass", 0.0)) == 0.0:
            kw["V"] = 0.0      # a driven piston made free starts at rest
        self.md.set_piston(v["axis"], **kw)

    def _bath_args(self, v):
        if v["kind"] == "csvr":
            return {"tau": float(v["tau"]) / PS}
        return {"gamma": float(v["gamma"]) * PS}

    def _gvec(self, v):
        g = [0.0] * self.ndim
        g[1] = -float(v["g"])
        return g

    def _remove_obj(self, obj):
        oid, md = obj["id"], self.md
        mol_atoms = self._atom_keys(oid) if self.kind.get(oid) == "molecules" else None
        k = self.kind.pop(oid, None)
        if k == "particles":
            md.remove(self.parts.pop(oid))
        elif k == "molecules":
            self.parts.pop(oid)
            if len(mol_atoms):
                md.remove(mol_atoms)  # all the molecules' atoms, bonds and angles in one edit (U5)
        elif k == "wall":
            self._wall(obj["values"], reset=True)
            self._release_axis(oid, "xyz".index(obj["values"]["axis"]))
        elif k == "piston":
            md.remove_piston()
            self._release_axis(oid, "xyz".index(obj["values"]["axis"]))
        elif k == "thermostat":
            md.remove_thermostat(self.parts.pop(oid))
        elif k == "gravity":
            md.set_gravity([0.0] * self.ndim)
        self.info.pop(oid, None)

    def _set_obj(self, obj, old):
        oid, k, v = obj["id"], self.kind.get(obj["id"]), obj["values"]
        md = self.md
        thrown = [a for a in range(self.ndim) if THROW_KEYS[a] in v and v[THROW_KEYS[a]] != old.get(THROW_KEYS[a])]
        if thrown:
            # a throw in the world's units (nm/s) becomes the object's velocity in m/s (review LB1-p02-ux X4); it is
            # applied even when equal to the stored one (the stored velocity is the last one set, not the motion now)
            old = dict(old)
            for a in thrown:
                v[VEL_KEYS[a]] = float(v[THROW_KEYS[a]]) / NM_PER_S
                old[VEL_KEYS[a]] = None
        if obj["type"] in ("gas", "crystal", "atom", "molecule", "thermostat", "wall"):
            self._check_temperature(obj["type"], v)
        if k in ("particles", "molecules"):
            # a handle param sent by a drag or a throw counts as changed even when equal to the stored one (old[k] is
            # None then: the stored place is where the object was last set, not where it is): never used here
            changed = {key for key in v if v.get(key) != old.get(key)}
            pos = [a for a in range(self.ndim) if POS_KEYS[a] in changed]
            vel = [a for a in range(self.ndim) if VEL_KEYS[a] in changed]
            other = changed - SP_KEYS - set(POS_KEYS) - set(VEL_KEYS) - set(THROW_KEYS)
            if other:  # a new set of atoms (count, region size, temperature, shape) at the current moment
                self._remove_obj({**obj, "values": old})
                self._add_obj(obj)
                return
            if changed & SP_KEYS:
                # the substance changed: the same atoms with new parameters now, at the same temperature (a mass
                # change rescales the velocities by sqrt(m_old/m_new); review B7-md M14)
                m_old = self._sp(oid)["mass"]
                self._species(obj)
                m_new = self._sp(oid)["mass"]
                if m_new != m_old:
                    keys = self._atom_keys(oid)
                    if len(keys):
                        md.set(keys, v=md.particles(keys)["v"] * math.sqrt(m_old / m_new))
            if pos:      # a drag: the group (or the atom) moved as a whole, its centre to the new place (LB1, P16.2)
                self._move_group(obj, pos)
            if vel:      # a throw: the group's centre-of-mass velocity (an atom's velocity)
                self._throw_group(obj, vel)
        elif k == "wall":
            if (old["axis"], old["side"]) != (v["axis"], v["side"]):
                self._wall(old, reset=True)
                if old["axis"] != v["axis"]:
                    self._release_axis(oid, "xyz".index(old["axis"]))
                    self._make_walled("xyz".index(v["axis"]), oid)
            self._wall(v)
        elif k == "piston":
            if old["axis"] != v["axis"]:
                md.remove_piston()
                self._release_axis(oid, "xyz".index(old["axis"]))
                self._make_walled("xyz".index(v["axis"]), oid)
                self._check_piston(v)
                self._piston(v)
            else:
                if old.get("position") != v["position"]:
                    self._check_piston(v)
                self._piston(v, old)
        elif k == "thermostat":
            self._region_inside(v)
            if old["kind"] != v["kind"]:
                md.remove_thermostat(self.parts[oid])
                self.parts[oid] = md.add_thermostat(v["kind"], float(v["T"]) / KELVIN, region=self._region_of(v),
                                                    **self._bath_args(v))
            else:
                md.set_thermostat(self.parts[oid], T=float(v["T"]) / KELVIN, region=self._region_of(v),
                                  **self._bath_args(v))
        elif k == "gravity":
            md.set_gravity(self._gvec(v))
        elif k == "probe":
            self._point_inside(v)

    def _atom_keys(self, oid):
        if self.kind.get(oid) == "molecules":
            if not hasattr(self, "_kcache"):
                self._kcache = {}
            got = self._kcache.get(oid)
            if got is None:
                mol = self.md.molecules()
                ks = [mol[int(mk)] for mk in self.parts[oid] if int(mk) in mol]
                got = np.sort(np.concatenate(ks)) if ks else np.zeros(0, np.int64)
                self._kcache[oid] = got
            return got
        return np.asarray(self.parts.get(oid, []), np.int64)

    # --- direct manipulation (LB1, P16.2): a group moved or thrown as a whole -----------------------------------
    def _centre(self, X):
        """The centre of a group of positions (reduced): the mean along a walled axis; along a periodic axis the
        circular mean (the angle of the mean of exp(2 pi i x / L)), or the middle of the box when the group spreads
        over the whole axis (the mean vector shorter than 0.15: no centre to speak of)."""
        c = np.zeros(self.ndim)
        for a in range(self.ndim):
            if self.md.periodic[a]:
                L = self.box[a]
                th = 2.0 * math.pi * X[:, a] / L
                C, S = float(np.mean(np.cos(th))), float(np.mean(np.sin(th)))
                c[a] = (math.atan2(S, C) / (2.0 * math.pi) * L) % L if math.hypot(C, S) > 0.15 else 0.5 * L
            else:
                c[a] = float(np.mean(X[:, a]))
        return c

    def _group(self, oid):
        """The keys, positions (wrapped) and velocities of an object's atoms (reduced)."""
        keys = self._atom_keys(oid)
        if not len(keys):
            return keys, np.zeros((0, self.ndim)), np.zeros((0, self.ndim))
        p = self.md.particles(keys)
        X = np.asarray(p["x"], float)
        for a in np.flatnonzero(self.md.periodic):
            X[:, a] -= self.box[a] * np.floor(X[:, a] / self.box[a])
        return keys, X, np.asarray(p["v"], float)

    def _move_group(self, obj, axes):
        """Translate an object's atoms so that their centre is at the object's x, y, z along ``axes`` (the others
        stay): refused with the reason where an atom would leave the walls (with the shift that fits) or come nearer
        than σ to an atom of another object; the engine checks the energies too. Cheap: one engine edit."""
        oid, v = obj["id"], obj["values"]
        keys, X, _ = self._group(oid)
        if not len(keys):
            return
        c = self._centre(X)
        d = np.zeros(self.ndim)
        for a in axes:
            d[a] = self._len(v[POS_KEYS[a]]) - c[a]
        if not np.any(d):
            return
        new = X + d
        sig = float(self._sigma_of(self.species[oid]))
        lo, hi = self._allowed(0.0)       # the walls act on the centres in both dynamics (review LB1-physics P4)
        for a in range(self.ndim):
            if self.md.periodic[a]:
                new[:, a] -= self.box[a] * np.floor(new[:, a] / self.box[a])
            elif np.any(new[:, a] < lo[a]) or np.any(new[:, a] > hi[a]):
                dmin, dmax = lo[a] - float(np.min(X[:, a])), hi[a] - float(np.max(X[:, a]))
                text = (T("“{label}”: the atom would be beyond the wall along the axis {a}", label=obj["label"],
                          a="xyz"[a]) if len(keys) == 1 else
                        T("“{label}”: atoms would be beyond the wall along the axis {a}", label=obj["label"], a="xyz"[a]))
                raise refusal(text, hint=T("the centre along {a} from {lo:.4g} to {hi:.4g} nm", a="xyz"[a],
                                           lo=(c[a] + dmin) * NM, hi=(c[a] + dmax) * NM))
        Xall, Sall = self._xs()
        allk = np.asarray(self.md.particles()["keys"])
        others = ~np.isin(allk, keys)
        if np.any(others):
            free = free_sites(new, sig, Xall[others], Sall[others], np.array(self.box), self.md.periodic)
            bad = int(np.sum(~free))
            if bad:
                hint = T("move it to a free place")
                if obj["type"] == "atom":
                    spot = self._free_spot(sig, new[0], refuse=False)
                    if spot is not None:
                        hint = T("the nearest free place is {at}", at=self._point([z * NM for z in spot]))
                raise refusal(T("“{label}”: {n:d} atoms would come closer than σ to atoms of other objects (they would "
                                "overlap)", label=obj["label"], n=bad), hint=hint)
        self.md.set(keys, x=new)

    def _throw_group(self, obj, axes):
        """Give an object's atoms the centre-of-mass velocity vx, vy, vz along ``axes`` (one species: equal masses);
        their motion about the centre stays."""
        oid, v = obj["id"], obj["values"]
        keys, _, V = self._group(oid)
        if not len(keys):
            return
        vc = V.mean(axis=0)
        new = V.copy()
        for a in axes:
            new[:, a] += float(v[VEL_KEYS[a]]) / U.velocity_m_s - vc[a]
        self.md.set(keys, v=new)

    def object_state(self, obj):
        # the atoms' positions and velocities are not kept in a scene file: an object starts again from its values (a
        # carry-over into a new world takes them: ``carry_state``)
        return None

    # --- the scene carried into a new world (review LB1-framework F5; the framework's hooks of 2026-11-11) -----------
    def carry_state(self):
        """What a new world takes over: per particle object its atoms' positions and velocities (molecules: per
        molecule, unwrapped, in the molecule's atom order), a crystal's lattice note; the piston's face and velocity;
        the world's box, space and random generators. Plain data and NumPy arrays; never changes the world."""
        md, nd = self.md, self.ndim
        L = np.asarray(md.L, float).copy()
        objs = {}
        for oid, k in self.kind.items():
            if k in ("particles", "molecules"):
                ak = self._atom_keys(oid)
                q = md.particles(ak) if len(ak) else {"x": np.zeros((0, nd)), "v": np.zeros((0, nd))}
                st = {"dim": nd, "box": L, "x": np.asarray(q["x"], float), "v": np.asarray(q["v"], float)}
                if k == "molecules" and len(ak):
                    mol = md.molecules()
                    groups = [np.sort(mol[int(mk)]) for mk in self.parts[oid] if int(mk) in mol]
                    keys = np.concatenate(groups)
                    pq = md.particles(keys)
                    na = len(groups[0])
                    st["xm"] = np.asarray(pq["x_unwrapped"], float).reshape(-1, na, nd)
                    st["vm"] = np.asarray(pq["v"], float).reshape(-1, na, nd)
                if self.info.get(oid):
                    st["info"] = {kk: (float(vv) if isinstance(vv, (float, np.floating)) else int(vv))
                                  for kk, vv in self.info[oid].items() if isinstance(vv, (int, float, np.number))}
                objs[oid] = st
            elif k == "piston" and not self.hard and md.piston() is not None:
                p = md.piston()
                objs[oid] = {"dim": nd, "box": L, "X": float(p["X"]), "V": float(p["V"])}
        def rng(g):   # PCG64's 128-bit integers as decimal text (plain JSON everywhere)
            st = g.bit_generator.state
            return {"state": str(st["state"]["state"]), "inc": str(st["state"]["inc"]),
                    "has_uint32": int(st["has_uint32"]), "uinteger": int(st["uinteger"])}
        world = {"dim": nd, "box": L, "rng_md": rng(md.rng), "rng": rng(self.rng),
                 "ramp": bool(not self.hard and getattr(md, "ramp_running", lambda: False)())}
        return {"objects": objs, "world": world}

    def _carry_note(self, text, obj=None, restarted=False):
        note = getattr(self, "carry_note", None)
        if note is not None:
            note(text, obj, restarted=restarted)

    def _carry_mismatch(self, st):
        """Why a carried state cannot go into this world as it is (None: it can)."""
        if int(st.get("dim", 0)) != self.ndim:
            return T("another dimension (plane ↔ volume): the atoms' positions cannot be continued in it")
        return None

    def _add_carried(self, obj, st):
        """An object with its carried state: the same atoms at the same places with the same velocities (a box of
        another size: as they were, where they fit; refused - then started from the parameters - where an atom would
        be outside a wall or on another one)."""
        t, v, oid, md = obj["type"], obj["values"], obj["id"], self.md
        L_old = np.asarray(st["box"], float)
        other_box = L_old.shape != np.asarray(md.L).shape or not np.allclose(L_old, md.L, rtol=1e-12, atol=0.0)
        if t == "piston":
            v["position"] = round(float(st["X"]) * NM, 9)
            self._piston_pos = None
            self._add_obj(obj)
            p = md.piston()
            md.set_piston(p["axis"], X=float(st["X"]), V=float(st["V"]), mass=p["M"], p_ext=p["p_ext"],
                          x_min=p["x_min"])
            self._carry_note(T("the piston carried to its place with its velocity"), obj)
            return
        sp = self._species(obj)
        if t == "molecule":
            if self.hard:
                raise refusal(T("hard spheres have no molecules"))
            na = int(np.asarray(st["xm"]).shape[1])
            b0, kb = float(v["bond"]), float(v["k_bond"])
            md.set_bond_type(f"{oid}-b", IA.HarmonicBond(kb, b0))
            if na >= 3:
                md.set_angle_type(f"{oid}-a", IA.HarmonicAngle(float(v.get("k_angle", 0.0)),
                                                               math.radians(float(v.get("angle", 180.0)))))
            bonds = [(i, i + 1, f"{oid}-b") for i in range(na - 1)]
            angles = [(i, i + 1, i + 2, f"{oid}-a") for i in range(na - 2)]
            X = np.array(st["xm"], float)
            moved, most = 0, 0.0
            for a in np.flatnonzero(~np.asarray(md.periodic)):
                # a walled axis here: each molecule whole, by its centre, in the box; one that crossed a periodic face
                # of the old world (now a wall) is moved inside as a whole, by the least shift (said)
                La = float(md.L[a])
                X[:, :, a] -= La * np.floor(X[:, :, a].mean(axis=1) / La)[:, None]
                lo, hi = X[:, :, a].min(axis=1), X[:, :, a].max(axis=1)
                sh = np.where(lo < 0.0, -lo, np.where(hi > La, La - hi, 0.0))
                X[:, :, a] += sh[:, None]
                moved += int(np.count_nonzero(sh))
                most = max(most, float(np.max(np.abs(sh))) if len(sh) else 0.0)
            _, mks, _ = md.add_molecules(sp, X, bonds=bonds, angles=angles, v=np.asarray(st["vm"], float),
                                         keep_all=True)
            if moved:
                self._carry_note(T("{n:d} molecules crossed a face that became a wall: moved inside as a whole (by at most "
                                   "{d:.3g} nm)", n=moved, d=most * NM), obj)
            self.parts[oid] = np.asarray(mks)
            self.kind[oid] = "molecules"
        else:
            x, vel = np.asarray(st["x"], float), np.asarray(st["v"], float)
            self.parts[oid] = np.asarray(md.add(sp, x, v=vel) if len(x) else np.zeros(0, np.int64))
            self.kind[oid] = "particles"
        if st.get("info"):
            self.info[oid] = dict(st["info"])
        self._kcache.pop(oid, None)
        if other_box:
            self._carry_note(T("another box ({old} → {new}): the atoms left at their places",
                               old=self._size([q * NM for q in L_old]), new=self._size([q * NM for q in md.L])), obj)

    def carry_world(self, state, laws):
        """The world's own state from the previous world: its random generators (the thermostats', the thermal walls'
        and the hard spheres' draws continue the same sequence); the first law's balance, the momentum's reference and
        the mean-square displacement count from the new world's start (a world with other laws has another energy
        function); a change of the box still running there is not continued (the new world's box is its target)."""
        if state is None:
            raise refusal(T("the previous world gave no state: the random sequence started anew"))
        for g, key in ((self.md.rng, "rng_md"), (self.rng, "rng")):
            d = state[key]
            g.bit_generator.state = {"bit_generator": "PCG64", "state": {"state": int(d["state"]), "inc": int(d["inc"])},
                                     "has_uint32": int(d["has_uint32"]), "uinteger": int(d["uinteger"])}
        self._carry_note(T("the random sequence (thermostats, thermal walls, hard spheres) continues that of the previous "
                           "world; the first law's balance, the momentum and the mean-square displacement count from the "
                           "new world's start"))
        if state.get("ramp"):
            self._carry_note(T("the change of the box under way in the previous world is not continued: the new world's "
                               "box is {size} at once", size=self._size([q * NM for q in self.md.L])))
        self._after_change()

    # --- live laws (review UX-ui U12) ------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        """The live laws at the current moment (review UX-ui U12; LB1, P16.1: a bench that never restarts), all or
        nothing (a refusal puts the world back bit for bit):

        * the pair model, its cutoff and shift (``MD.set_pair``) and the time step (``MD.set_dt``): the same atoms,
          positions and velocities; the potential energy changes by the difference of the models (the first-law
          balance moves E0 by it) and the conservation references restart; a time step the hottest atoms cannot
          resolve is refused. In the hard world they are kept for the forces (they act after a switch);
        * the dynamics: continuous forces ↔ hard spheres (``core.md.hard.hard_from_md``, ``md_from_hard``): the same
          atoms with their positions and velocities; to hard spheres only without what they have not (named) and
          with no pair inside contact; back always, the potential energy appearing (stated);
        * the box, Lx, Ly, Lz (``MD.deform``): affine (the box with the matter, its work booked in the first law) or a
          wall moved over empty space (``box_mode``)."""
        new, errors = SCHEMA.coerce_live(self.live, values or {})
        if errors:
            raise refusal(join(errors))
        changed = {k: v for k, v in new.items() if self.live.get(k) != v}
        if not changed:
            return ""
        if self.ndim == 2 and "Lz" in changed:
            raise refusal(T("a plane has no axis z: the box size along z does not apply here"),
                          hint=T("change Lx and Ly"))
        snap = self._snapshot()
        parts = []
        laws = {"model", "cutoff", "shift", "dt_fs"} & set(changed)
        box = [k for k in BOX_KEYS if k in changed]
        try:
            self.live = dict(new)
            if "dynamics" in changed:
                parts.append(self._switch_to_hard() if new["dynamics"] == "hard" else self._switch_to_soft())
            elif laws and self.hard:
                parts.append(T("the force laws are kept: {laws}; they act after the switch to continuous forces",
                               laws=self._law_list(laws, changed)))
            elif laws:
                E0 = self.md.energy()
                self.model = self.live["model"]
                if {"model", "cutoff", "shift"} & laws:
                    self.md.set_pair(self._pair_term())
                if "dt_fs" in laws:
                    dt = float(self.live["dt_fs"]) * 1e-3 / PS
                    self._check_dt(dt)
                    self.md.set_dt(dt)
                dE = self.md.energy() - E0
                de = U.to_kJ_mol(dE / max(self.md.n, 1))
                labels = self._law_list(laws, changed)
                parts.append(T("laws changed while the world runs: {laws}; the energy changed by {de:+.4g} kJ/mol per atom "
                               "(the difference of the potentials; counted in the balance)", laws=labels, de=de)
                             if abs(dE) > 0 else T("laws changed while the world runs: {laws}", laws=labels))
            self.model = "hard" if self.hard else self.live["model"]
            if "dynamics" in changed or (laws and not self.hard):
                self._after_change()
            if box:
                parts.append(self._set_box())
            elif "box_mode" in changed:
                parts.append(T("from now on the box size changes affinely (the matter with the box)")
                             if new["box_mode"] == "affine" else
                             T("from now on the box size changes by moving the upper wall over empty space"))
            if "dynamics" in changed or laws:
                parts.append(T("the checks count from this moment"))
        except BaseException as e:
            self._restore(snap)
            if isinstance(e, Exception) and not _is_owner_text(e):
                raise _owner(e, self) from e
            raise
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})
        if "dynamics" in changed:
            self._stale_checks()
        return join(parts)

    def _law_list(self, laws, changed):
        """«label = value» of the changed laws, joined."""
        return join([T("{label} = {value}", label=SCHEMA.by_id[k].label, value=_val(k, changed[k]))
                     for k in sorted(laws)], ", ")

    def _sub_seed(self):
        """A seed for a solver built at the current moment (the switch of the dynamics), from the world's generator:
        deterministic, as a restore repeats it."""
        return int(self.rng.integers(0, 2 ** 62))

    def _switch_to_hard(self):
        from lfphys.core.md import hard as HD
        block = []
        for o in self.objects.values():
            t, v = o["type"], o["values"]
            what = {"molecule": T("molecules “{label}”", label=o["label"]),
                    "piston": T("the piston “{label}”", label=o["label"]),
                    "thermostat": T("the thermostat “{label}”", label=o["label"]),
                    "gravity": T("the field “{label}”", label=o["label"])}.get(t)
            if t == "wall" and v.get("kind") == "soft":
                what = T("the soft wall “{label}”", label=o["label"])
            if t in ("gas", "crystal", "atom") and v.get("substance") == "custom" and float(v.get("charge", 0.0)):
                what = T("the charge of “{label}”", label=o["label"])
            if what:
                block.append(what)
        if block:
            raise refusal(T("hard disks have none of this: {what}", what=join(block, ", ")) if self.ndim == 2 else
                          T("hard spheres have none of this: {what}", what=join(block, ", ")),
                          hint=T("remove them (make the soft wall specular or thermal), then switch “Dynamics”"))
        p = self.md.particles()
        sig = np.array([self._sigma_of(q) for q in p["species"]], float)
        cv = HD.contact_violations(p["x"], sig, self.md.L, self.md.periodic, walls_on="centre")
        if cv["pairs"] or cv["walls"]:
            what = []
            if cv["pairs"]:
                what.append(T("pairs of atoms closer than σ to each other: {n:d} (the closest at {d:.3g} σ)",
                              n=int(cv["pairs"]), d=float(cv["closest"])))
            if cv["walls"]:
                what.append(T("atoms beyond a wall: {n:d}", n=int(cv["walls"])))
            raise refusal(T("hard disks would overlap: {what}", what=join(what)) if self.ndim == 2 else
                          T("hard spheres would overlap: {what}", what=join(what)),
                          hint=T("lower the density (a larger box, while the world runs) or the temperature (the weaker "
                                 "the impact, the less the atoms enter each other), or try at another moment: such pairs "
                                 "appear and part"))
        n = max(self.md.n, 1)
        stopped = self._stop_ramp("other dynamics")
        Ep = self.md.energy() - self.md.kinetic_energy()
        self.md = HD.hard_from_md(self.md, seed=self._sub_seed(), walls_on="centre")
        self.hard = True
        self.model = "hard"
        de = U.to_kJ_mol(Ep / n)
        txt = (T("dynamics: hard disks (event-driven), the same atoms, positions and velocities; the potential energy "
                 "({de:+.4g} kJ/mol per atom) vanished: the energy is now only kinetic", de=de) if self.ndim == 2 else
               T("dynamics: hard spheres (event-driven), the same atoms, positions and velocities; the potential energy "
                 "({de:+.4g} kJ/mol per atom) vanished: the energy is now only kinetic", de=de))
        if not all(self.md.periodic):
            txt = join([txt, T("the walls act on the atoms' centres, as with continuous forces: the centres' region and "
                               "the density did not change")])
        return join([stopped, txt])

    def _switch_to_soft(self):
        from lfphys.core.md import hard as HD
        K = self.md.kinetic_energy()
        extra = {}
        for oid, k in self.kind.items():
            if k in ("particles", "molecules"):
                _, _, e, q = self._subst_values(self.objects[oid]["values"])
                extra[self.species[oid]] = {"epsilon": e, "charge": q}
        dt = float(self.live["dt_fs"]) * 1e-3 / PS
        self.md = HD.md_from_hard(self.md, self._pair_term(), dt, seed=self._sub_seed(), species_extra=extra)
        self.hard = False
        self.model = self.live["model"]
        self._check_dt(dt)
        n = max(self.md.n, 1)
        de = U.to_kJ_mol((self.md.energy() - K) / n)
        lab = _val("model", self.live["model"])
        return T("dynamics: continuous forces ({model}), the same atoms, positions and velocities; the pairs' potential "
                 "energy appeared: a jump of the energy of {de:+.4g} kJ/mol per atom", model=lab, de=de)

    def _box3d(self, L=None):
        b = [x * NM for x in (self.box if L is None else L)] + [0.0] * (3 - self.ndim)
        if self.ndim == 2:
            b[2] = 0.05 * max(b[:2])
        return [[0.0, 0.0, -b[2] if self.ndim == 2 else 0.0], b]

    @staticmethod
    def _size(L_nm):
        """A box's or a region's sizes, «a × b (× c) nm»."""
        L = [float(x) for x in L_nm]
        if len(L) == 2:
            return T("{a:.4g} × {b:.4g} nm", a=L[0], b=L[1])
        if len(L) == 3:
            return T("{a:.4g} × {b:.4g} × {c:.4g} nm", a=L[0], b=L[1], c=L[2])
        return T("{a:.4g} nm", a=L[0])

    @staticmethod
    def _point(x_nm):
        """A point, «(x, y (, z)) nm»."""
        x = [float(q) for q in x_nm]
        if len(x) == 2:
            return T("({x:.4g}, {y:.4g}) nm", x=x[0], y=x[1])
        if len(x) == 3:
            return T("({x:.4g}, {y:.4g}, {z:.4g}) nm", x=x[0], y=x[1], z=x[2])
        return T("{x:.4g} nm", x=x[0])

    def _set_box(self):
        """The box to the live Lx, Ly (, Lz) at the current moment: ``MD.deform`` (a jump: affine, or a wall over empty
        space) or ``MD.ramp_box`` (affine over “Time of the size change”: a small affine step after every step of the
        integrator, the work of each booked; review LB1-physics P3) with its work in the first law; the hard world
        only by a wall. A change still running is stopped where the box is (its work stays). The view gets the new box
        (a ``box`` message: for a ramp the region it spans, then the final box at its end); the mean-square
        displacement and the hard world's pressure blocks restart; the first-law balance goes on (its W has the box's
        work). Refusals in the owner's terms, with the size that fits."""
        nd = self.ndim
        L_nm = [float(self.live[k]) for k in BOX_KEYS[:nd]]
        L = np.array(L_nm) / NM
        mode = self.live["box_mode"]
        tau_ps = float(self.live.get("box_time_ps", 0.0) or 0.0)
        if self.hard and mode == "affine":
            raise refusal(T("for hard disks an affine compression by a jump does no work of the collision pressure: even "
                            "a slow one would follow the adiabat of an ideal gas, which is wrong") if nd == 2 else
                          T("for hard spheres an affine compression by a jump does no work of the collision pressure: "
                            "even a slow one would follow the adiabat of an ideal gas, which is wrong"),
                          hint=T("“How to change the box size” = move the upper wall (an axis with walls; on a periodic "
                                 "axis put a “Wall” first), or “Dynamics” = continuous forces, the box, and back"))
        before = self._stop_ramp("new size")
        old_nm = [b * NM for b in self.box]
        if not self.hard and mode == "affine" and tau_ps > 0 and np.any(L != np.asarray(self.md.L)):
            return join([before, self._start_ramp(L, L_nm, old_nm, tau_ps)])
        T0 = self._T_kelvin()
        try:
            o = self.md.deform(L, mode="wall") if self.hard else self.md.deform(
                L, mode=mode, max_bond_strain=MAX_BOND_STRAIN)
        except ValueError as e:
            raise self._box_refusal(e, L, mode) from e
        self.box = [float(b) for b in self.md.L]
        if not self.hard:
            self._check_dt(self.md.dt)        # a compression heats: the step must still resolve the collisions
        else:
            self.md.reset_counters()          # the collision pressure's sums belong to one box
        self.md.msd_origin()
        self._zb = {"blocks": [], "prev": None, "t_change": float(self.md.t)}
        self.emit({"type": "box", "t": self.t, "box": self._box3d()})
        size = T("{old} → {new}", old=self._size(old_nm), new=self._size(L_nm))
        if mode == "wall" or self.hard:
            W = float(o.get("dE", 0.0))
            if W != 0.0:      # a soft wall's energy under the atoms near it changed (review LB1-physics P8)
                Wk = U.to_kJ_mol(W)
                return join([before, T("box {size}: a wall moved (empty space added or removed); the soft wall moved under "
                                       "the atoms near it: the work on the system W = {W:+.4g} kJ/mol (the change of the "
                                       "wall's energy), counted in the first law", size=size, W=Wk)])
            return join([before, T("box {size}: a wall moved (empty space added or removed), no work on the system "
                                   "(specular and thermal walls over empty space); an expansion into vacuum is "
                                   "irreversible", size=size)])
        n = max(self.md.n, 1)
        W = U.to_kJ_mol(o["dE"])
        T1 = self._T_kelvin()
        lam = max(abs(x - 1.0) for x in o["lambda"])
        txt = [T("box {size}, affinely by a jump (by {p:.3g} %): the work on the system W = {W:+.4g} kJ/mol", size=size,
                 p=100 * lam, W=W)]
        if o.get("pdv") is not None:
            pdv = U.to_kJ_mol(o["pdv"])
            txt.append(T("−P·ΔV by the virial before and after: {pdv:+.4g}", pdv=pdv) if o.get("virial_is_affine") else
                       T("−∫S dV by the affine stress before and after (with a field, soft walls or frozen atoms this is "
                         "not the virial pressure): {pdv:+.4g}", pdv=pdv))
        txt.append(T("coordinates ×L′/L, velocities relative to the centre of mass ×L/L′: the kinetic energy {dk:+.4g} "
                     "kJ/mol per atom", dk=U.to_kJ_mol(o["dK"] / n)))
        if T0 is not None and T1 is not None:
            txt.append(T("temperature {T0:.4g} → {T1:.4g} K", T0=T0, T1=T1))
        txt.append(T("the work is counted in the first law. A jump is not quasi-static: the matter is out of equilibrium "
                     "after it and, relaxing, heats irreversibly (slowly: “Time of the size change” above 0)"))
        return join([before, *txt])

    def _start_ramp(self, L, L_nm, old_nm, tau_ps):
        """An affine change of the box over tau_ps (``MD.ramp_box``): refused where the end would pack the atoms beyond
        close packing at contact σ, or a step would change a length by more than the engine's limit (then a longer time
        or a jump), or as the jump would be (the piston's axis, the cutoff); the view gets the region the change spans."""
        nd = self.ndim
        X, S = self._xs()
        if len(X):
            vs = (math.pi / 4 * S ** 2) if nd == 2 else (math.pi / 6 * S ** 3)
            eta = float(np.sum(vs)) / float(np.prod(L))
            eta_max = (math.pi / (2 * math.sqrt(3.0))) if nd == 2 else (math.pi / (3 * math.sqrt(2.0)))
            if eta > eta_max:
                cap = (float(np.sum(vs)) / eta_max / float(np.prod(np.asarray(self.md.L)))) ** (1.0 / nd)
                raise refusal(T("the atoms would cover {frac}, denser than the close packing of spheres of diameter σ "
                                "({lim:.0f} %)", lim=100 * eta_max,
                                frac=(T("{p:.0f} % of the area", p=100 * eta) if nd == 2 else
                                      T("{p:.0f} % of the volume", p=100 * eta))),
                              hint=T("sizes of at least ≈ {p:.3g} % of the present ones (now {size}), or remove some "
                                     "atoms", p=cap * 100, size=self._size(old_nm)))
        tau = tau_ps / PS
        try:
            r = self.md.ramp_box(L, tau)
        except ValueError as e:
            msg = str(e)
            import re
            m = re.search(r"changes a length by ([\d.e+-]+) per step \(limit ([\d.e+-]+)\)", msg)
            if m:
                need = tau_ps * float(m.group(1)) / float(m.group(2))
                raise refusal(T("in {tau:.3g} ps the box would change too fast: {p:.2g} % of a length per computing step "
                                "(the limit is {lim:.2g} %)", tau=tau_ps, p=100 * float(m.group(1)),
                                lim=100 * float(m.group(2))),
                              hint=T("“Time of the size change” at least {tau:.3g} ps, or 0: by a jump",
                                     tau=math.ceil(need * 100) / 100), detail=msg) from e
            raise self._box_refusal(e, L, "affine") from e
        self._ramp_T0 = self._T_kelvin()
        self.emit({"type": "box", "t": self.t, "box": self._box3d(np.maximum(np.asarray(self.md.L), L))})
        dL = max(abs(a - b) for a, b in zip(L_nm, old_nm))
        v_face = dL * 1e-9 / (tau_ps * 1e-12)                 # m/s
        Tk = self._T_kelvin()
        ms = self._masses()
        m_mean = float(np.mean(ms[np.isfinite(ms)])) if len(ms) and np.any(np.isfinite(ms)) else 1.0
        txt = [T("box {old} → {new} affinely in {tau:.3g} ps (until t = {t_end:.6g} ps): the box's faces move at up to "
                 "{v:.3g} m/s", old=self._size(old_nm), new=self._size(L_nm), tau=tau_ps,
                 t_end=(self.t + tau_ps * 1e-12) * 1e12, v=v_face)]
        if Tk is not None and Tk > 0:
            u = math.sqrt(nd * (Tk / KELVIN) / m_mean) * U.velocity_m_s
            txt.append(T("the atoms' thermal speed ≈ {u:.3g} m/s; quasi-static when the faces are much slower", u=u))
        txt.append(T("the size changes at every computing step, the work of each step counted in the first law; the end "
                     "is an event with the work"))
        return join(txt)

    def _stop_ramp(self, why):
        """Stop a change of the box still running (another box, the other dynamics): the text for the event."""
        if self.hard or not hasattr(self.md, "ramp_running") or not self.md.ramp_running():
            return ""
        self.md.stop_box_ramp(why)
        self.box = [float(b) for b in self.md.L]
        return self._ramp_text(self.md.box_ramp())

    def _ramp_text(self, r):
        """What a change of the box over a time did (its end, or where it was stopped)."""
        self._ramp_seen = r["n"]
        L0 = [x * NM for x in r["L0"]]
        L1 = [x * NM for x in r["L"]]
        W = U.to_kJ_mol(r["W"])
        pdv = U.to_kJ_mol(r["pdv"])
        dur = (r["t_end"] - r["t0"]) * PS
        if r["done"]:
            head = T("the change of the box finished")
        else:
            why = {
                "new size": T("a new size was set"),
                "other dynamics": T("the switch to hard spheres"),
                "step": T("the compression heated the matter: the time step would not resolve the collisions"),
                "cutoff": T("the cutoff radius would exceed half the box"),
            }.get(r["stopped"], T("a force would become infinite") if str(r["stopped"]).startswith("refused") else
                  str(r["stopped"]))
            head = T("the change of the box stopped ({why})", why=why)
        txt = [T("{head}: {old} → {new} in {dur:.4g} ps, {n:d} steps; the work on the system W = {W:+.4g} kJ/mol (by "
                 "steps, exact; −∫{P} dV by steps: {pdv:+.4g}), counted in the first law", head=head,
                 old=self._size(L0), new=self._size(L1), dur=dur, n=int(r["steps"]), W=W,
                 P="P" if r.get("virial_is_affine") else "S", pdv=pdv)]
        T0, T1 = getattr(self, "_ramp_T0", None), self._T_kelvin()
        if T0 is not None and T1 is not None:
            txt.append(T("temperature {T0:.4g} → {T1:.4g} K", T0=T0, T1=T1))
        return join(txt)

    def _follow_ramp(self):
        """After an advance: the box the engine's ramp has reached (frames, measurables), the time step against the
        heating it brings (stopped where the step would not resolve the collisions), and its end announced once."""
        r = self.md.box_ramp()
        if r is None:
            return
        self.box = [float(b) for b in self.md.L]
        if r["running"]:
            try:
                self._check_dt(self.md.dt)
            except Exception:  # noqa: BLE001 - the heating outran the step: stop here, said in the event
                self.md.stop_box_ramp("step")
                r = self.md.box_ramp()
        if not r["running"] and r["n"] != getattr(self, "_ramp_seen", 0):
            self.emit({"type": "event", "kind": "action", "name": "box", "t": self.t, "text": self._ramp_text(r),
                       "notify": True})
            self.emit({"type": "box", "t": self.t, "box": self._box3d()})
            self.md.msd_origin()

    def _T_kelvin(self):
        T = self.md.temperature().get("T") if self.md.n else None
        return float(T) * KELVIN if T is not None and math.isfinite(T) else None

    def _box_refusal(self, e, L, mode):
        """A refused change of the box in the owner's terms, with what fits now."""
        msg = str(e)
        nd = self.ndim
        names = [k for k, a, b in zip(BOX_KEYS, L, self.box) if a != b]
        if "overlap" in msg or "non-finite" in msg or "same point" in msg:
            # the largest part of the way to the asked size that the engine takes (bisection on copies of the system)
            cls, st = type(self.md), self.md.state_dict()
            L0 = np.array(self.box)
            lo_t, hi_t = 0.0, 1.0
            for _ in range(10):
                mid = 0.5 * (lo_t + hi_t)
                try:
                    # with the same bond limit as the change itself (review LB1-physics P13)
                    cls.from_state_dict(st).deform(L0 + mid * (L - L0), mode=mode,
                                                   **({} if self.hard else {"max_bond_strain": MAX_BOND_STRAIN}))
                    lo_t = mid
                except ValueError:
                    hi_t = mid
            ok = (L0 + lo_t * (L - L0)) * NM
            fit = join([T("{k} ≈ {L:.4g} nm", k=k, L=float(ok[BOX_KEYS.index(k)])) for k in names], ", ")
            return refusal(T("at such a compression the atoms would overlap (an atom's energy above the limit {lim:.3g} "
                             "ε)", lim=float(getattr(self.md, "max_insert_energy", 50))),
                           hint=T("now it can go to {fit}; further in steps, letting the matter spread out", fit=fit),
                           detail=msg)
        if "outside the walls" in msg or "particle outside" in msg:
            X = np.asarray(self.md.positions(), float)
            need = join([T("{k} at least {L:.4g} nm", k=k, L=float(np.max(X[:, BOX_KEYS.index(k)])) * NM * 1.0001)
                         for k in names if len(X)], ", ")
            return refusal(T("atoms would be left behind the moved wall: only empty space can be removed"),
                           hint=T("{need}, or “affinely”", need=need or T("a larger size")), detail=msg)
        return _owner(e, self)

    def _check_dt(self, dt):
        """A new time step must resolve the hottest motion present: the kinetic temperature of each species and the
        temperatures the baths and thermal walls impose (``_check_temperature``)."""
        for d in self.md.species():
            if not math.isfinite(d["mass"]):
                continue
            Tsp = self.md.temperature(species=d["name"]).get("T")
            if Tsp is not None and math.isfinite(Tsp) and Tsp > 0:
                obj = self.objects.get(d["name"])
                vals = {**(obj["values"] if obj else {}), "T": Tsp * KELVIN}
                self._check_temperature("gas", vals, dt=dt)
        for o in self.objects.values():
            if o["type"] in ("thermostat", "wall"):
                self._check_temperature(o["type"], o["values"], dt=dt)

    # --- time ----------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        tr = t_target * 1e12 / PS  # reduced
        if tr > self.md.t:
            try:
                self.md.advance(tr)
            except FloatingPointError as e:   # review UX-params P4: the owner's words, not the engine's
                raise RuntimeError(T("the Verlet step failed ({why}): atoms came together to one point or flew through a "
                                     "wall; the time step is too large for these speeds; decrease the “Time step” "
                                     "(while the world runs) or the temperature, and remove or change the last object",
                                     why=str(e))) from e
        self.t = max(self.t, t_target)
        if not self.hard and getattr(self.md, "_ramp", None) is not None:
            self._follow_ramp()

    def max_step(self):
        """At most MAX_STEPS steps per advance call, fewer when the modelled cost of a step (``md_step_model``: the
        atoms and the pairs; deterministic) would make one call longer than FRAME_S: a large scene keeps the frames and
        the commands flowing (review UX-params P33). The result does not depend on the cut: the engine steps to the
        last step time before each target."""
        if self.hard:
            return MAX_STEPS * 0.01 * PS * 1e-12
        c = self.md.cost_estimate()
        per = OB.md_step_model(c["n"], c["pairs"], self.ndim)
        k = int(min(MAX_STEPS, max(1, FRAME_S / per)))
        return k * self.md.dt * PS * 1e-12

    # --- frames ----------------------------------------------------------------------------------------------------
    def _colors(self):
        out = {}
        for oid, k in self.kind.items():
            if k in ("particles", "molecules"):
                out[oid] = COLORS[int(self.objects[oid]["values"].get("color", 0) or 0) % len(COLORS)]
        return out

    # --- measurables (LB1, P16.3) ---------------------------------------------------------------------------------
    def measurables(self):
        """The quantities this world measures as time series (the frames' ``meas``): of the world (temperature,
        pressure, energy per atom, density, the first law's Q, W, E − E₀ and residual, the momentum, the order
        parameter, the mean-square displacement), of every thermometer (atoms, density, temperature in its ball), of
        the piston (position, the gas's mean force on it, speed), of every molecule object (its modes' temperatures)
        and of every particle object (its temperature). Translatable labels, display units."""
        nd = self.ndim
        E, G1, G2 = T("kJ/mol"), T("Substance"), T("First law (since the last change of the scene)")
        K_, PCS, DL = T("K"), T("pcs"), T("dimensionless")
        rho_u = T("nm⁻²") if nd == 2 else T("nm⁻³")
        out = [{"id": "T", "label": T("Temperature"), "unit": K_, "of": None, "group": G1},
               {"id": "p", "label": T("Pressure (virial; for hard spheres from the collisions since the change)"),
                "unit": T("bar") if nd == 3 else T("mN/m"), "of": None, "group": G1},
               {"id": "e", "label": T("Energy per atom"), "unit": E, "of": None, "group": G1},
               {"id": "N", "label": T("Number of atoms"), "unit": PCS, "of": None, "group": G1},
               {"id": "rho", "label": T("Number density of the atoms"), "unit": rho_u, "of": None, "group": G1},
               {"id": "rho_red", "label": T("Density ρσ² (argon's σ)") if nd == 2 else T("Density ρσ³ (argon's σ)"),
                "unit": DL, "of": None, "group": G1},
               {"id": "V", "label": T("Box volume") if nd == 3 else T("Box area"),
                "unit": T("nm²") if nd == 2 else T("nm³"), "of": None, "group": G1},
               {"id": "Q", "label": T("Heat Q from the baths and the thermal walls"), "unit": E, "of": None, "group": G2},
               {"id": "W", "label": T("Work W on the system (the piston and changes of the box)"), "unit": E, "of": None,
                "group": G2},
               {"id": "dE", "label": T("Change of the energy E − E₀"), "unit": E, "of": None, "group": G2},
               {"id": "resid", "label": T("Balance residual E − E₀ − Q − W"), "unit": E, "of": None, "group": G2},
               *[{"id": f"P{c}", "label": T("System momentum P{c}", c=c), "unit": T("u·m/s"), "of": None,
                  "group": T("Momentum")} for c in "xyz"[:nd]],
               {"id": "order", "label": T("Order |⟨ψ6⟩| (once per {dt} ps)", dt=ORDER_EVERY_PS) if nd == 2 else
                T("Order Q6 (once per {dt} ps)", dt=ORDER_EVERY_PS), "unit": DL, "of": None, "group": T("Structure")},
               {"id": "msd", "label": T("Mean-square displacement (since the last change)"), "unit": T("nm²"),
                "of": None, "group": T("Structure")}]
        for oid, o in self.objects.items():
            lab, t = o["label"], o["type"]
            if t == "probe":
                g = T("Thermometers")
                out += [{"id": f"{oid}.N", "label": T("“{label}”: atoms in the ball", label=lab), "unit": PCS,
                         "of": oid, "group": g},
                        {"id": f"{oid}.rho", "label": T("“{label}”: density", label=lab), "unit": rho_u, "of": oid,
                         "group": g},
                        {"id": f"{oid}.T", "label": T("“{label}”: temperature", label=lab), "unit": K_, "of": oid,
                         "group": g}]
            elif t == "piston":
                g = T("Piston")
                out += [{"id": f"{oid}.X", "label": T("“{label}”: position", label=lab), "unit": T("nm"), "of": oid,
                         "group": g},
                        {"id": f"{oid}.F", "label": T("“{label}”: the gas's force (mean since the last change)",
                                                       label=lab), "unit": T("pN"), "of": oid, "group": g},
                        {"id": f"{oid}.V", "label": T("“{label}”: speed", label=lab), "unit": T("m/s"), "of": oid,
                         "group": g}]
            elif t == "molecule":
                for part, nm in (("tr", T("translational")), ("rot", T("rotational")),
                                 ("vib", T("vibrational (kinetic)")), ("bond", T("of the bonds (potential)")),
                                 ("ang", T("of the angles (potential)"))):
                    out.append({"id": f"{oid}.T_{part}", "label": T("“{label}”: mode temperature, {mode}", label=lab,
                                                                     mode=nm),
                                "unit": K_, "of": oid, "group": T("Molecules")})
            if t in ("gas", "crystal", "atom", "molecule"):
                out.append({"id": f"{oid}.Tobj", "label": T("“{label}”: temperature of the atoms", label=lab),
                            "unit": K_, "of": oid, "group": T("Objects")})
        return out

    def measure(self):
        """The current values of the measurables (``meas``), everything computed now (sweeps)."""
        return self._readings(full=True)["meas"]

    def _readings(self, full):
        """What a frame shows of the objects (``now``, the probes) and the measurables' values with the notes for the
        undefined ones, and every positioned object's place (``at``, nm; groups: their centre). ``full``: the order
        parameter too (else it is computed with the statistics, every STATS_EVERY frames)."""
        md, nd = self.md, self.ndim
        p = md.particles()
        X = np.asarray(p["x"], float)
        keys_all = np.asarray(p["keys"])
        n = len(X)
        nan = float("nan")
        meas, notes, at, now, probes, ids = {}, {}, {}, {}, {}, []

        def put(mid, val, why=""):
            ok = val is not None and math.isfinite(float(val))
            meas[mid] = float(val) if ok else nan
            if not ok and why:
                notes[mid] = why

        def nm3(c):
            c = [float(z) * NM for z in c]
            return c + [0.0] * (3 - nd)

        Tsys = md.temperature().get("T") if n else None
        no_atoms = T("no atoms")
        put("T", Tsys * KELVIN if Tsys is not None else None, no_atoms)
        P = md.pressure() if n else {}
        pv = P.get("virial") if not self.hard else P.get("pressure")
        put("p", (U.to_bar(pv) if nd == 3 else pv * U.pressure_Pa(2) * 1e3) if pv is not None else None,
            no_atoms if not n else (T("for hard spheres: after the first collisions since the change") if self.hard
                                    else T("the virial is undefined (frozen atoms)")))
        Etot = md.energy() if not self.hard else md.kinetic_energy()
        put("e", U.to_kJ_mol(Etot / n) if n else None, no_atoms)
        meas["N"] = float(n)
        V = float(md.volume())
        put("V", V * NM ** nd)
        put("rho", n / (V * NM ** nd))
        put("rho_red", n / V)
        b = md.energy_balance()
        for mid, k in (("Q", "Q"), ("W", "W"), ("dE", "dE"), ("resid", "residual")):
            val = b.get(k, 0.0 if k == "W" else None)
            put(mid, U.to_kJ_mol(val) if val is not None else None)
        mom = md.momentum() if n else np.zeros(nd)
        for a, c in enumerate("xyz"[:nd]):
            put(f"P{c}", float(mom[a]) * U.to_amu(1.0) * U.velocity_m_s)
        try:
            put("msd", md.msd()["msd"] * NM * NM)
        except (RuntimeError, ValueError):
            put("msd", None, T("no reference"))
        if full:      # a sweep's reading: computed now, the frames' schedule untouched
            put("order", self._order_value(), no_atoms)
        else:
            # by world time, not by frame count (a frame drawn again at the same moment shows the same): computed when a
            # new ORDER_EVERY_PS of world time begins, shown in that frame only
            b = math.floor(self.t * 1e12 / ORDER_EVERY_PS + 1e-9)
            if b != getattr(self, "_order_bucket", None):
                self._order_bucket = b
                self._order, self._order_t = self._order_value(), self.t
            if getattr(self, "_order_t", None) == self.t and getattr(self, "_order", None) is not None:
                put("order", self._order)
            else:
                put("order", None, T("computed once per {dt} ps of world time (costly: like 1–3 steps)",
                                     dt=ORDER_EVERY_PS))
        names = np.asarray(p["species"], dtype=object)
        for oid, k in self.kind.items():
            o = self.objects.get(oid)
            if o is None:
                continue
            if k in ("particles", "molecules"):
                Tsp = md.temperature(species=self.species[oid])
                Tk = float(Tsp["T"]) * KELVIN if Tsp.get("T") is not None and math.isfinite(Tsp["T"]) else None
                # the inspector's rows: plain English msgids as keys (the player translates them), numbers or T values
                d = {"atoms": int(np.count_nonzero(names == self.species[oid])), "temperature, K": Tk}
                put(f"{oid}.Tobj", Tk, no_atoms)
                inf = self.info.get(oid)
                if inf:
                    d["lattice density ρσ²" if nd == 2 else "lattice density ρσ³"] = inf["density"]
                    d["cell strain"] = inf["strain"]
                    if inf.get("skipped"):
                        d["sites left empty (taken)"] = inf["skipped"]
                ak = self._atom_keys(oid)
                if len(ak):
                    rows = np.searchsorted(keys_all, ak)
                    c = self._centre(X[rows])
                    at[oid] = nm3(c)
                    d["centre"] = self._point(at[oid][:nd])
                if k == "molecules":
                    mm = md.molecule_modes(self.parts[oid]) if not self.hard else None
                    for part, key, row in (("translation", "tr", "T translational, K"),
                                           ("rotation", "rot", "T rotational, K"),
                                           ("vibration", "vib", "T vibrational (kin.), K"),
                                           ("bonds", "bond", "T bonds (pot.), K"),
                                           ("angles", "ang", "T angles (pot.), K")):
                        Tm = mm[part]["T"] * KELVIN if mm and mm[part]["T"] is not None else None
                        put(f"{oid}.T_{key}", Tm, T("no such modes"))
                        if Tm is not None:
                            d[row] = Tm
                now[oid] = d
            elif k == "piston":
                pist = md.piston()
                if pist is not None:
                    a = "xyz".index(pist["axis"]) if isinstance(pist["axis"], str) else int(pist["axis"])
                    c = [0.5 * L for L in self.box]
                    c[a] = pist["X"]
                    at[oid] = nm3(c)
                    put(f"{oid}.X", pist["X"] * NM)
                    dt = md.t - pist["t0"]
                    put(f"{oid}.F", pist["impulse"] / dt * U.force_N * 1e12 if dt > 0 else None,
                        T("measured from the next step"))
                    put(f"{oid}.V", pist["V"] * U.velocity_m_s if math.isfinite(pist["V"]) else None)
            elif k == "thermostat":
                reg = self._region_of(o["values"])
                if reg is not None:
                    at[oid] = nm3([0.5 * (lo + hi) for lo, hi in zip(*reg)])
        for oid, o in self.objects.items():
            if o["type"] == "probe":
                v = o["values"]
                c = [self._len(v[cc]) for cc in "xyz"[:nd]]
                at[oid] = nm3(c)
                try:
                    pr = md.probe(c, self._len(v["r"]))
                except ValueError:
                    pr = {"n": None, "density": None, "T": None}
                probes[oid] = {"temperature, K": pr["T"] * KELVIN if pr["T"] is not None else None,
                               "atoms": pr["n"], ("density ρσ²" if nd == 2 else "density ρσ³"): pr["density"]}
                ids.append(oid)
                why = T("the ball is outside the box or its radius exceeds half the periodic box")
                put(f"{oid}.N", pr["n"], why)
                put(f"{oid}.rho", pr["density"] / NM ** nd if pr["density"] is not None else None, why)
                put(f"{oid}.T", pr["T"] * KELVIN if pr["T"] is not None else None,
                    T("no atoms in the ball") if pr["n"] == 0 else why)
        return {"meas": meas, "notes": notes, "at": at, "now": now, "probes": probes, "ids": ids, "p": p, "X": X}

    def _order_value(self):
        """The bond-orientational order (|⟨ψ6⟩| in a plane, Q6 in a volume) of all atoms now (None without atoms)."""
        md = self.md
        if md.n == 0:
            return None
        X = np.asarray(md.positions())
        sig = np.array([self._sigma_of(q) for q in md.particles()["species"]])
        bo = OB.bond_order(X, self.box, [bool(b) for b in md.periodic], ORDER_RCUT * float(np.mean(sig)))
        return bo.get("psi6_global") if self.ndim == 2 else bo.get("Q6")

    def frame(self):
        md = self.md
        R = self._readings(full=False)
        p, X = R["p"], R["X"]
        n = len(X)
        # the particles: positions quantized to 16 bits over the box (drawing only), the species index of each
        span = np.array(self.box)
        q = np.clip(np.round(X / span * 65535), 0, 65535).astype(np.uint16) if n else \
            np.zeros((0, self.ndim), np.uint16)
        sp_names = list(self.species.values())
        spec = np.array([sp_names.index(s) if s in sp_names else 0 for s in p["species"]], np.uint8)
        now, probes, ids = R["now"], R["probes"], R["ids"]
        if self.check_due():
            self.checks()
        if self.n_stats % STATS_EVERY == 0:
            self.emit_stats()
        self.n_stats += 1
        pist = md.piston() if self.model != "hard" else None
        bonds = None
        if self.model != "hard" and any(k == "molecules" for k in self.kind.values()):
            topo = md.topology()
            bonds = np.array([[a, b] for a, b, *_ in topo.get("bonds", [])], np.int32).reshape(-1)
        meta = {"ids": ids, "now": now, "probes": probes, "n": n, "box_nm": [b * NM for b in self.box],
                "at": R["at"], "meas": R["meas"], "meas_note": R["notes"],   # always present: a frame's keys never vary
                "species_colors": [self._colors().get(s, COLORS[0]) for s in sp_names],
                "species_radius_nm": [0.5 * NM * self._sigma_of(s) for s in sp_names],
                "piston_nm": (pist["X"] * NM if pist else None),
                "walled": [a for a in range(self.ndim) if not md.periodic[a]],
                "piston_axis": ("xyz".index(pist["axis"]) if pist and isinstance(pist.get("axis"), str)
                                else int(pist["axis"]) if pist and pist.get("axis") is not None else 1)}
        blobs = {"q": q.reshape(-1), "sp": spec}
        if bonds is not None:
            keys = list(p["keys"])
            index = {int(k): i for i, k in enumerate(keys)}
            blobs["bonds"] = np.array([index[int(k)] for k in bonds], np.int32)
        return meta, blobs

    def _sigma_of(self, sp):
        d = self._sp(sp)
        return float(d.get("sigma", 1.0)) if d else 1.0

    def _masses(self):
        ms = {d["name"]: d["mass"] for d in self.md.species()}
        return np.array([ms[s] for s in self.md.particles()["species"]], float)

    def emit_stats(self):
        """Statistics for the charts (accumulative: every message is a point of the time series, the latest also the
        distributions)."""
        md = self.md
        if md.n == 0:
            return
        Tm0 = md.temperature()
        Tk = float(Tm0["T"]) * KELVIN if Tm0.get("T") is not None and math.isfinite(Tm0["T"]) else None
        P = md.pressure()
        # MD: the instantaneous virial pressure; hard spheres: the collision virial since the last change
        p_val = P.get("virial") if self.model != "hard" else P.get("pressure")
        p_phys = (U.to_bar(p_val) if self.ndim == 3 else p_val * U.pressure_Pa(2) * 1e3) if p_val is not None \
            else None
        e = (md.energy() / md.n) if self.model != "hard" else md.kinetic_energy() / md.n
        # the velocity components scaled by sqrt(kT/m) of each particle's own mass: one standard Gaussian
        # (Maxwell-Boltzmann); T of the sample, as in the KS check
        V = np.asarray(md.velocities())
        m = self._masses()
        mob = np.isfinite(m)
        hist = None
        if np.any(mob):
            Ts = float(np.sum(m[mob, None] * V[mob] ** 2)) / V[mob].size
            if Ts > 0:
                z = (V[mob] * np.sqrt(m[mob] / Ts)[:, None]).reshape(-1)
                hist, _ = np.histogram(z, bins=40, range=(-4.0, 4.0), density=True)
        ks = md.velocity_ks()
        r_max = min(0.5 * min(self.box), 5.0)
        r, g, _ = md.rdf(r_max, nbins=80)
        X = np.asarray(md.positions())
        # the density along y (the field's axis), in slabs of about one sigma
        Ly = self.box[1] if self.model == "hard" or md.piston() is None else md.piston()["X"]
        nb = int(min(max(round(Ly), 8), 100))
        cnt, _ = np.histogram(X[:, 1], bins=nb, range=(0.0, Ly))
        area = float(np.prod(np.delete(np.array(self.box), 1)))
        rho_y = cnt / (area * Ly / nb)
        order = self._order if getattr(self, "_order_t", None) == self.t else self._order_value()
        msd = md.msd()["msd"] * NM * NM
        modes = None
        if self.model != "hard" and any(k == "molecules" for k in self.kind.values()):
            mm = md.molecule_modes()
            if mm:
                modes = {part: (mm[part]["T"] * KELVIN if mm[part]["T"] is not None else None)
                         for part in ("translation", "rotation", "vibration", "bonds", "angles")}
        self.emit({"type": "stats", "t": self.t, "T_K": Tk, "p": p_phys,
                   "p_unit": T("bar") if self.ndim == 3 else T("mN/m"),
                   "p_kind": T("virial (instantaneous)") if self.model != "hard" else
                   T("from the collisions (since the change)"),
                   "e_kJ_mol": U.to_kJ_mol(e), "ks": {k: ks.get(k) for k in ("D", "bound", "within", "n")},
                   "order": order, "order_kind": "|⟨ψ6⟩|" if self.ndim == 2 else "Q6", "msd_nm2": msd,
                   "modes": modes, "rho_y_nm": Ly * NM},
                  {"rdf_r": np.asarray(r, np.float32) * NM, "rdf_g": np.asarray(g, np.float32),
                   "rho_y": rho_y.astype(np.float32),
                   **({"vh": hist.astype(np.float32)} if hist is not None else {})})

    # --- checks ------------------------------------------------------------------------------------------------------
    def checks(self):
        md = self.md
        if md.n == 0:
            return
        if self.model != "hard":
            b = md.energy_balance()
            stiff = any(o["type"] in ("piston",) or (o["type"] == "wall") for o in self.objects.values()) or \
                not all(md.periodic)
            kj = U.to_kJ_mol
            note = [T("E − E₀ = Q + W + residual since the last change of the scene: the heat from the baths and walls Q = "
                      "{Q:.4g}, the work W = {W:.4g} kJ/mol (the piston {Wp:.4g}, changes of the box {Wb:.4g}; edits of "
                      "the scene shift E₀ by the energy they change); the residual is the error of the Verlet scheme: "
                      "O(dt²) with continuous forces", Q=kj(b["Q"]), W=kj(b["W"]), Wp=kj(b.get("W_piston", b["W"])),
                      Wb=kj(b.get("W_box", 0.0)))]
            if stiff:
                note.append(T("impacts on rigid walls and the piston inside a step with interacting atoms give an error "
                              "of the order of F·v·dt per impact, accumulating with the impacts: an error of the first "
                              "order in dt (the piston preset: a residual of 1–14 ε over the first stroke at 2.5–10 fs, at "
                              "most ~1.5 % of the work; for an ideal gas the balance is exact)"))
            if not self._baths():
                try:
                    se = md.step_error(n_steps=10)
                    note.append(T("the companion's estimate (dt against dt/2) over 10 steps: {dE:.3g}",
                                  dE=kj(se["dE_estimate"])))
                except ValueError:
                    pass
            self.running_check("energy", T("Energy: the first law (balance residual), kJ/mol"),
                               kj(b["residual"]), 0.0, 0.0, info=True, group=T("Conservation laws"), note=join(note))
            dr = md.momentum_drift()
            if dr["ratio"] is not None:
                ax = ", ".join("xyz"[a] for a in range(self.ndim) if dr["axes"][a])
                self.running_check("momentum", T("System momentum along {ax}: conserved (pairwise forces)", ax=ax),
                                   dr["ratio"], 0.0, 1.0, group=T("Conservation laws"), ok=dr["ratio"] <= 1.0,
                                   note=T("|P − P₀| / the rounding bound over {n:d} steps (P₀ the momentum at the last "
                                          "change of the scene; the bound ε·steps·(sums of |m v|, |F|): the engine's "
                                          "momentum_drift); conserved along periodic axes without a field, thermal "
                                          "walls, Langevin baths and local baths, frozen atoms", n=int(dr["steps"])))
        else:
            b = md.energy_balance()
            self.running_check("energy", T("Energy: the first law (balance residual), kJ/mol"),
                               U.to_kJ_mol(b["residual"]), 0.0, 0.0, info=True, group=T("Conservation laws"),
                               note=T("hard spheres: the energy is only kinetic, the impacts elastic: E − E₀ = Q (the heat "
                                      "of the thermal walls {Q:.4g} kJ/mol) up to rounding", Q=U.to_kJ_mol(b["Q"])))
        ks = md.velocity_ks()
        if ks.get("D") is not None:
            self.running_check("maxwell", T("Velocities against the Maxwell distribution (KS distance)"), ks["D"], None,
                               ks.get("bound") or 0.0, info=True, group=T("Statistics"),
                               note=(T("within the DKW bound {b:.3g} at the level {lvl} ({n:d} velocity components of all "
                                       "atoms, each divided by √(kT/m) of its mass): in equilibrium, within",
                                       b=ks.get("bound"), lvl=0.01, n=int(ks.get("n") or 0)) if ks.get("within") else
                                     T("outside the DKW bound {b:.3g} at the level {lvl} ({n:d} velocity components of "
                                       "all atoms, each divided by √(kT/m) of its mass): in equilibrium, within",
                                       b=ks.get("bound"), lvl=0.01, n=int(ks.get("n") or 0))))
        P = md.pressure()
        if self.model != "hard" and P.get("walls"):
            walls = join([T("{k}: {v:.4g}", k=k, v=v) for k, v in P["walls"].items() if v is not None], ", ")
            note = T("the pressure on the walls is the momentum given to them per time: {walls}", walls=walls)
            if P.get("virial") is None:
                note = join([note, T("with frozen atoms the virial is defined only along the axes with walls")])
            self.running_check("pressure", T("Pressure: the virial against the walls (reduced units)"),
                               P.get("virial"), None, 0.0, info=True, group=T("Statistics"), note=note)
        if self.model == "hard":
            self._z_check()
        c = md.cost_estimate()
        if self.model == "hard":
            self.running_check("cost", T("Computation: seconds per event (CPU, measured)"), c.get("s_per_event"), None,
                               0.0, info=True, group=T("Computation"), unit=T("s"),
                               note=T("{n} atoms, {e} events", n=c.get("n"), e=c.get("events")))
        else:
            self.running_check("cost", T("Computation: seconds per step ({device}, estimate)",
                                         device=str(c.get("device", "cpu")).upper()),
                               c.get("per_step_s"), None, 0.0, info=True, group=T("Computation"), unit=T("s"),
                               note=T("{n} atoms", n=c.get("n")))

    def _stale_checks(self):
        """After a switch of the dynamics: the checks the other solver computed and this one does not are marked so
        (the panel keeps every check's latest version)."""
        if self.hard:
            gone = (("momentum", T("System momentum: conserved (pairwise forces)"), T("Conservation laws")),
                    ("pressure", T("Pressure: the virial against the walls (reduced units)"), T("Statistics")))
            note = T("not computed with the dynamics of hard spheres (switched while the world runs)")
        else:
            gone = (("eos", T("Compressibility factor Z against the equation of state"), T("Statistics")),)
            note = T("not computed with the dynamics of continuous forces (switched while the world runs)")
        for cid, label, group in gone:
            self.running_check(cid, label, None, None, 0.0, info=True, group=group, note=note)

    def _z_check(self):
        """Hard disks / spheres in a periodic box, one species: the compressibility factor Z of the run (mean of blocks
        of at least Z_BLOCK time units, from Z_EQUIL after the last change) against the equation of state of the
        fluid (Kolafa & Rottner 2006 / Kolafa, Labík & Malijevský 2004) with the ensemble correction for this N;
        pass/fail from Z_MIN_BLOCKS blocks with the tolerance 5 standard errors of the block mean + 1e-4 (review
        B7-md M5)."""
        from lfphys.core.md import hard as HD
        md, zb = self.md, self._zb
        a = md.accumulators()
        if a["t"] < zb["t_change"] + Z_EQUIL:
            zb["prev"] = None
            return
        if zb["prev"] is None:
            zb["prev"] = a
            return
        dt = a["t"] - zb["prev"]["t"]
        if dt >= Z_BLOCK:
            dK = a["Kdt"] - zb["prev"]["Kdt"]
            if dK > 0:
                Tb = 2.0 * dK / dt / a["dof"]
                zb["blocks"].append(1.0 + (a["W"] - zb["prev"]["W"]) / (self.ndim * a["n"] * Tb * dt))
            zb["prev"] = a
        names = {s for s in md.particles()["species"]}
        if not all(self.md.periodic) or len(names) != 1 or md.n < 2:
            return
        sig = self._sigma_of(next(iter(names)))
        rho = md.n * sig ** self.ndim / float(np.prod(self.box))
        z_inf = HD.z_reference(self.ndim, rho)
        if z_inf is None:
            return
        ref = z_inf - HD.ensemble_correction(self.ndim, rho, md.n)
        bl = np.array(zb["blocks"])
        src = (T("Kolafa and Rottner 2006 (disks)") if self.ndim == 2 else
               T("Kolafa, Labík and Malijevský 2004 (spheres)"))
        label = T("Compressibility factor Z against the equation of state")
        if len(bl) < Z_MIN_BLOCKS:
            self.running_check("eos", label, None, ref, 0.0, info=True, group=T("Statistics"),
                               note=T("accumulating: {k:d} of {n:d} blocks of {b:.2g} ps after {eq:.2g} ps since the "
                                      "change of the scene; the reference {ref:.5f} ({src})", k=len(bl), n=Z_MIN_BLOCKS,
                                      b=Z_BLOCK * PS, eq=Z_EQUIL * PS, ref=ref, src=src))
            return
        z = float(bl.mean())
        se = float(bl.std(ddof=1) / math.sqrt(len(bl)))
        tol = 5.0 * se + 1e-4
        self.running_check("eos", label, z, ref, tol, group=T("Statistics"), ok=abs(z - ref) <= tol,
                           note=T("Z = 1 + Σ r·Δp / (d N T Δt) over the collisions, the mean of {k:d} blocks ± {se:.2g}; "
                                  "the reference: the fluid at ρσ^{d} = {rho:.4f} in the limit N → ∞ {zinf:.5f} ({src}) "
                                  "minus the ensemble correction for N = {N:d}: {ref:.5f}; the tolerance 5 standard errors "
                                  "+ 1e-4", k=len(bl), se=se, d=self.ndim, rho=rho, zinf=z_inf, src=src, N=int(md.n),
                                  ref=ref))

    def _baths(self):
        return any(k == "thermostat" for k in self.kind.values()) or any(
            o["type"] == "wall" and o["values"]["kind"] == "thermal" for o in self.objects.values())

    # --- header --------------------------------------------------------------------------------------------------------
    def header(self):
        box = self._box3d()
        b = box[1]
        return {
            "title": T("Playground: particles and molecules"),
            "text": T("Atoms and molecules move by Newton's laws with a model interatomic interaction; the temperature, "
                      "the pressure, heat and work, the velocity distribution and the structure of the matter are "
                      "measured as the computation goes."),
            "actions": [],
            "approximations": self._approx(),
            # the axis unit stays a plain msgid: the 3-D environment puts it into its own strings
            "scene3d": {"box": box, "units": "nm",
                        "up": [0, 1, 0] if self.ndim == 2 else [0, 0, 1], "objects": [], "layers": [],
                        "coord_names": ["x", "y", "z"],
                        "planes": {"max": 0, "center": [0.5 * x for x in b], "defaults": {"1": [0, 0, 1]}}},
            "md": {"ndim": self.ndim, "model": self.model, "box_nm": [x * NM for x in self.box],
                   "boundary": ["periodic" if b else "walls" for b in self.md.periodic],
                   "units": {"nm": NM, "ps": PS, "K": KELVIN}},
            "playground": self.playground_header(),
            "modifications": SCHEMA.modifications(self.params),
        }, {}

    def _approx(self):
        """The approximations of this world (review B7-md M16), with the numbers that set their limits."""
        a = [T("classical mechanics of the atoms: in solid argon quantum effects matter below the Debye temperature "
               "Θ_D = {th} K (the Debye heat capacity at 20 / 40 / 80 K is {c20:.2f} / {c40:.2f} / {c80:.2f} of the "
               "classical one)", th=85, c20=debye_cv_fraction(20, 85), c40=debye_cv_fraction(40, 85),
               c80=debye_cv_fraction(80, 85))]
        if self.model == "lj":
            rc, sh = float(self.live["cutoff"]), self.live["shift"]
            a.append(T("the interatomic interaction is the Lennard-Jones (12-6) model with argon's parameters, cut at "
                       "{rc:.3g} σ (the force shifted): a substance other than argon", rc=rc) if sh == "force" else
                     T("the interatomic interaction is the Lennard-Jones (12-6) model with argon's parameters, cut at "
                       "{rc:.3g} σ (the energy shifted): a substance other than argon", rc=rc))
            tc = TC.get((self.ndim, rc, sh))
            full = TC[(self.ndim, "full")]
            if tc is not None:
                a.append(T("the critical temperature of this model is {tc:.3g} ε/k = {tcK:.0f} K (of the full 12-6 "
                           "{full:.3g} ε/k = {fullK:.0f} K, of argon ≈ 150.7–150.9 K): above it there are no separate "
                           "liquid and vapour", tc=tc, tcK=tc * KELVIN, full=full, fullK=full * KELVIN))
            elif self.ndim == 3:
                a.append(T("the critical temperature depends on the cutoff and the shift (of the full 12-6 in a volume "
                           "{full:.3g} ε/k = {fullK:.0f} K; with the force shifted at 2.5σ, 0.937 ε/k = 112 K); no "
                           "value is known for this cutoff", full=full, fullK=full * KELVIN))
            else:
                a.append(T("the critical temperature depends on the cutoff and the shift (of the full 12-6 in a plane "
                           "{full:.3g} ε/k = {fullK:.0f} K; cut at 2.5σ with the energy shifted, 0.459 ε/k = 55 K, the "
                           "triple point near 0.42 ε/k); no value is known for this cutoff", full=full,
                           fullK=full * KELVIN))
        elif self.model == "wca":
            a.append(T("repulsion only (WCA), a model: without attraction there are no liquid and vapour"))
        else:
            a.append(T("hard disks / spheres, a model (infinitely stiff repulsion, no attraction: no liquid and vapour, "
                       "only fluid and crystal)"))
        if self.ndim == 2:
            a.append(T("a plane: two-dimensional matter (its phases and equation of state are two-dimensional)"))
        mols = [o for o in self.objects.values() if o["type"] == "molecule"]
        for o in mols:
            v = o["values"]
            m = self._subst_values(v)[0]
            w = math.sqrt(float(v["k_bond"]) / (0.5 * m))                 # homonuclear bond: mu = m/2
            hw = w * HBAR_OVER_K / (PS * 1e-12)                            # ħω/k in K (ω in 1/τ)
            Tk = float(v["T"])
            frac = einstein_cv_fraction(Tk, hw) if Tk > 0 else 0.0
            a.append(T("“{label}”: the bonds are harmonic springs (they do not break, no anharmonicity), ħω/k = {hw:.0f} "
                       "K; at kT ≲ ħω the vibrations are quantum (the vibration's heat capacity at {T:.3g} K is {frac:.2f} "
                       "of the classical one), here they are classical", label=o["label"], hw=hw, T=Tk, frac=frac))
        return a

    def engine_modules(self):
        mods = ["lfphys.core.md.system", "lfphys.core.md.cells", "lfphys.core.md.observables", "lfphys.core.md.units",
                "lfphys.theories.models.interatomic"]
        return mods + (["lfphys.core.md.hard"] if self.model == "hard" else [])


VIZ = {
    "id": "p03_molecules",
    "title": T("Particles and molecules"),
    "summary": T("A molecular-dynamics sandbox: gas, crystal, molecules, walls, a piston, thermostats; the temperature, "
                 "the pressure, heat and work, the Maxwell distribution as the computation goes."),
    "purpose": T("Build matter from atoms and see how thermal properties arise from Newton's laws: the velocity "
                 "distribution, pressure, melting, liquid and vapour, the heat and the work of a piston."),
    "version": "0.2",
    "schema": SCHEMA,
    "simulation": Simulation,
    "kind": "playground",
    "section": "molecules",
}
