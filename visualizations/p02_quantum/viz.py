# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p02: the quantum playground (plan P15.3; owner, 2026-10-28). A wrapper over the engine's quantum scene
(``lfphys.core.quantum.scene``); the framework is ``lfviz.playground``.

The laws of the world: the dimension (a plane or the space) is a world parameter (another dimension is a new world,
which takes over the objects that make sense in it: ``place``); the grid (points per axis), the window's size and its
edges, open (absorbing) or closed (periodic), are live (plan P16.1: the waves resampled exactly at the current moment,
``Scene.regrid``; refused with the measured fraction where a coarser grid or a smaller window would drop more than
``QS.REGRID_TOL`` of a particle's norm). Inside it the experimenter
places, at any moment, particles as wave packets (electron, neutron, 4He, C60, an atom of any mass; spin 1/2 where the
species has one), potentials with smooth edges (box barriers and wells, balls, walls with slits, steps, a harmonic
trap), magnetic fields (uniform or with a gradient, in a region or everywhere) and Aharonov–Bohm flux tubes,
absorbing detectors, a which-path marker, an environment that localizes (decoherence), planes that measure the
probability flux; and measures a particle's position (an action). Every particle obeys its own Schrödinger or Pauli
equation; the particles do not interact. Bohm trajectories (an interpretation, flagged) can be attached to a particle.

Units of the scene: hbar = 1, the length 1 nm, the mass m_e; the world's time in seconds. Every change acts from the
current moment (the scene banks what the detectors absorbed and restarts the energy reference).

Direct manipulation (plan P16.2): the palette's types declare handles (``ObjectType.handles``); every positioned object
is reported in the frame's ``at`` (a packet at the mean position of its wave). A packet's position or velocity edit
prepares the same wave anew at the current moment — moved (``Scene.move_particle``: psi(r - s), the norm kept) or given a
momentum (``Scene.boost_particle``: exp(i dk.r) psi; a thrown velocity v becomes k0 = m v / hbar, i.e. lambda and the
direction) — any other change of a packet prepares a fresh packet. Moving a potential, a field, a detector or a probe
moves it at the current moment. Instruments (plan P16.3): ``measurables`` and every frame's ``meas``.
"""

from __future__ import annotations

import math

import numpy as np
import scipy.constants as sc

from lfphys.core.quantum import scene as QS
from lfphys.i18n import T, is_t, join, text_of
from lfphys.theories.interpretations import bohm
from lfviz import limits
from lfviz.errors import Refusal
from lfphys.codes import code_of
from lfviz.params import Param, Schema
from lfviz import playground as PG
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param, scene_time

UNITS = QS.Units(length=1e-9, mass=sc.m_e)
TU = UNITS.time                 # seconds per unit of scene time (m_e nm^2 / hbar = 8.64e-15 s)
EV = UNITS.energy / sc.e        # eV per unit of energy (hbar^2 / (m_e nm^2) = 0.0762 eV)
TESLA = UNITS.field             # tesla per unit of magnetic field (hbar / (e nm^2) = 658 T)
FS = 1e-15 / TU                 # units of scene time per femtosecond
WAVE_EVERY = 5                  # frames between two pictures of the wave (by count: the same in a restored world)
IMG_MAX = 256                   # points per axis of the plane's picture (block-averaged beyond)
VOL_MAX = 48                    # points per axis of the volume's picture
BOHM_CHUNK = 8                  # scene steps per Bohm interval (the wave is interpolated quadratically across it)
MAX_STEPS = 64                  # scene steps per advance call (the runner interleaves commands and frames)
PHASE_PER_STEP = 0.1            # the time step turns the largest relevant energy by at most this phase (rad)
ERROR_EVERY = 64                # the companion's step-error estimate every this many scene steps (review B6-Q7)
CONTROL_N = 8                   # Bohm points of each ensemble integrated again as a control (review B6-Q1) ...
CONTROL_ORDER = 16              # ... with Lagrange interpolation of this order ...
CONTROL_TIGHT = 4               # ... and this many times tighter tolerances of the time integration
BOHM_P = 5.733e-7               # the registration counts fail below this two-sided p-value (5 sigma)
ANGLES = 24                     # Gauss-Legendre nodes of the edges' reflection over the angle of incidence
EDGE_FRAC = {2: 0.10, 3: 0.15}  # the open edges' layers: this share of the window per side (3-D: wider, review B6-Q8)
W_SET = np.logspace(-1.5, 2.0, 22)  # the absorbers' strengths tried, in units of the largest kinetic energy (_auto_W)
VMAX_MARGIN = 0.98              # a packet's throw limit v_max this far inside the grid's resolution rule (_set_vmax)
VMAX_EVERY = 20                 # frames between two checks of the throw limit as the wave moves on (_refresh_vmax)
VMAX_CHANGE = 0.25              # ... which is sent again (a scene message) when it changed by more than this share
CACHE_MAX = 256                 # reflections kept between changes of the scene (pure functions of their keys)
BOHM_RGB = [[1.0, 0.85, 0.3], [0.45, 0.85, 1.0], [1.0, 0.5, 0.6], [0.6, 1.0, 0.6], [0.8, 0.65, 1.0]]


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("dim", T("Space"), "select", "2d", group=T("Laws"),
       options=[("2d", T("plane (x, y)")), ("3d", T("volume (x, y, z)"))],
       help=T("The Schrödinger (Pauli) equation is solved in a plane or in a volume; another space is a new world")),
    _p("n2", T("Grid points per axis"), "select", "256", group=T("Grid"), show_if={"dim": ["2d"]}, live=True,
       options=[(s, s) for s in ("128", "192", "256", "384", "512")],
       help=T("Grid step = window size / number of points; the grid must resolve the wavelength and the shapes' edges. "
              "Changes on the fly: the wave is resampled onto the new grid exactly (by padding its spectrum with "
              "zeros). A coarser grid only when three rules hold: (1) less than 10⁻⁶ of the wave's norm lies beyond "
              "the new band of wavenumbers; (2) the new grid still resolves the wave: |k| + 6σ_k ≤ π/step, and next to "
              "a potential or a field ≤ ⅔·π/step (with the energy the potential can turn into motion); (3) the objects' "
              "edges are not narrower than ≈ 3 steps of the new grid (an edge “0” is frozen at the width the object "
              "was added with; the action “Coarsen the grid with edges to match” widens such edges at once). "
              "Otherwise a refusal with the reason and the number")),
    _p("n3", T("Grid points per axis"), "select", "64", group=T("Grid"), show_if={"dim": ["3d"]}, live=True,
       options=[(s, s) for s in ("48", "64", "96", "128")],
       help=T("Grid step = window size / number of points. Changes on the fly, as in the plane")),
    _p("size", T("Window size, nm"), "float", 80.0, group=T("Grid"), unit=T("nm"), min=2.0, max=1e5, log=True,
       live=True,
       help=T("The window is a square (a cube) centred at zero. Changes on the fly (grid step = size / number of "
              "points): larger when the wave is almost empty at the window's faces (less than 10⁻⁶ of the norm in the "
              "4 outermost cells), smaller when less than 10⁻⁶ of its probability lies outside the new window and "
              "under its new absorbing layers (with open edges); otherwise a refusal with that share. The edges' "
              "layers are 10 % of the window (15 % in a volume): they move with the window")),
    _p("edges", T("Window edges"), "select", "open", group=T("Laws"), live=True,
       options=[("open", T("open: absorbing (an outgoing wave does not come back)")),
                ("closed", T("closed: periodic (the wave leaves on the other side)"))],
       help=T("Changes on the fly, at the current moment (what the edges absorbed before stays absorbed); a charged "
              "particle next to a field only with open edges")),
    scene_param(),
], presets={})


def _scene(objs):
    return {"format": "lfscene", "version": 1, "objects": objs}


SCHEMA.presets.update({
    "double_slit": {"label": T("Double slit: an electron, a wall with two slits, a detector screen, Bohm particles"),
                    "params": {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": _scene([
                        {"type": "slit_wall", "label": T("Wall with two slits"),
                         "values": {"position": 0.0, "thickness": 2.0, "V": 3.0, "n_slits": 2, "width": 2.0,
                                    "spacing": 10.0}},
                        {"type": "detector", "label": T("Screen"), "values": {"x": 30.0, "sx": 4.0, "sy": 0.0, "edge": 3.0}},
                        {"type": "plane", "label": T("Flux behind the slits"), "values": {"position": 15.0}},
                        {"type": "packet", "label": T("Electron"),
                         "values": {"x": -20.0, "wavelength": 2.0, "sx": 2.5, "sy": 4.0, "bohm": 60}}])}},
    # the slits are 12-nm channels and the marker fills the upper one, 10 nm along the beam, its edges across inside the
    # wall (no lens), c = 0.021 eV = 5.6 % of the electron's energy: the transmitted wave's marker turns to P(1) = 0.95
    # (|coherence| 0.04); the screen's visibility near the centre falls from 0.94 to 0.18 (review B6-Q9: the earlier
    # 3 x 3 nm marker at the thin wall acted as a +-0.12 eV lens and left 0.61); what remains is the packet's spread of
    # speeds (the marker turns by the time spent in it)
    "which_path": {"label": T("Which-path marker in the upper slit: the fringes almost vanish (visibility {v0} → {v1})",
                                v0=0.94, v1=0.18),
                   "params": {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": _scene([
                       {"type": "slit_wall", "label": T("Wall with two slit channels"),
                        "values": {"position": 2.0, "thickness": 12.0, "V": 3.0, "n_slits": 2, "width": 2.0,
                                   "spacing": 10.0}},
                       {"type": "marker", "label": T("Marker in the upper channel"),
                        "values": {"x": 2.0, "y": 5.0, "sx": 10.0, "sy": 4.0, "rate": 0.032, "edge": 1.0}},
                       {"type": "detector", "label": T("Screen"), "values": {"x": 30.0, "sx": 4.0, "sy": 0.0, "edge": 3.0}},
                       {"type": "packet", "label": T("Electron"),
                        "values": {"x": -20.0, "wavelength": 2.0, "sx": 2.5, "sy": 4.0}}])}},
    # the tube inside the wall between the slits (3 nm thick: its field e^{-r^2/R^2} is e^{-9} at the wall's faces):
    # the screen's pattern is the ideal half-fringe shift 2 (S1 + S2) - P0 to 3.4e-4 of its peak (review B6-Q10: the
    # tube behind the wall, in the beams' overlap, left 5.6 %)
    "aharonov_bohm": {"label": T("Aharonov–Bohm: a flux tube h/2e in the wall between the slits shifts the fringes "
                                 "by half a period"),
                      "params": {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": _scene([
                          {"type": "slit_wall", "label": T("Wall with two slits"),
                           "values": {"position": 0.0, "thickness": 3.0, "V": 3.0, "n_slits": 2, "width": 2.0,
                                      "spacing": 10.0}},
                          {"type": "flux", "label": T("Flux tube"), "values": {"x": 0.0, "y": 0.0, "flux": 0.5,
                                                                                "radius": 0.5}},
                          {"type": "detector", "label": T("Screen"), "values": {"x": 30.0, "sx": 4.0, "sy": 0.0, "edge": 3.0}},
                          {"type": "packet", "label": T("Electron"),
                           "values": {"x": -20.0, "wavelength": 2.0, "sx": 2.5, "sy": 4.0}}])}},
    "tunnel": {"label": T("Tunnelling: a packet hitting a thin barrier higher than its energy"),
               "params": {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": _scene([
                   {"type": "box", "label": T("Barrier"), "values": {"x": 0.0, "sx": 1.5, "sy": 0.0, "V": 0.5}},
                   {"type": "plane", "label": T("Flux behind the barrier"), "values": {"position": 6.0}},
                   {"type": "packet", "label": T("Electron"),
                    "values": {"x": -20.0, "wavelength": 2.0, "sx": 2.5, "sy": 4.0, "bohm": 40}}])}},
    "trap": {"label": T("Harmonic trap: a displaced packet oscillates (energy conserved), a position measurement"),
             "params": {"dim": "2d", "n2": "128", "size": 60.0, "edges": "open", "scene": _scene([
                 {"type": "trap", "label": T("Trap"), "values": {"hw": 20.0}},
                 {"type": "packet", "label": T("Electron"),
                  "values": {"x": 6.0, "y": 2.0, "wavelength": 0.0, "sx": 1.38, "sy": 1.38}}])}},
    "cyclotron": {"label": T("An electron in a 100 T magnetic field: a circular orbit, spin along the field"),
                  "params": {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open", "scene": _scene([
                      {"type": "bfield", "label": T("Field Bz"), "values": {"Bz": 100.0}},
                      {"type": "packet", "label": T("Electron"),
                       "values": {"x": 0.0, "y": -10.0, "wavelength": 4.0, "sx": 3.0, "sy": 3.0, "bohm": 30}}])}},
    # lambda = 4 nm: next to the ball the wave's wavenumbers (|k| + 6 sigma_k = 3.07/nm) stay within 2/3 of the grid's
    # band (3.35/nm); with lambda = 3 nm (3.59/nm) the scene now refuses it (review B6-Q4)
    "ball_3d": {"label": T("3-D: an electron scatters off a ball"),
                "params": {"dim": "3d", "n3": "64", "size": 40.0, "edges": "open", "scene": _scene([
                    {"type": "ball", "label": T("Ball"), "values": {"x": 4.0, "radius": 3.0, "V": 1.0}},
                    {"type": "packet", "label": T("Electron"),
                     "values": {"x": -5.0, "wavelength": 4.0, "sx": 2.0, "sy": 2.0, "sz": 2.0, "bohm": 30}}])}},
})

AXES = [("0", "x"), ("1", "y"), ("2", "z")]
COLORS = {"barrier": "#ff922b", "well": "#4dabf7", "detector": "#51cf66", "field": "#74c0fc", "flux": "#b197fc",
          "marker": "#f783ac", "env": "#a9744f", "plane": "#3bc9db", "particle": "#ffd43b"}


def _xyz(ndim, region=False, defaults=(0.0, 0.0, 0.0)):
    if region:
        return [_p(c, T("Region centre: {c}, nm", c=c), "float", float(defaults[i]), min=-1e6, max=1e6)
                for i, c in enumerate("xyz"[:ndim])]
    return [_p(c, T("Centre: {c}, nm", c=c), "float", float(defaults[i]), min=-1e6, max=1e6)
            for i, c in enumerate("xyz"[:ndim])]


def _sizes(ndim, defaults=(4.0, 4.0, 4.0)):
    return [_p(f"s{c}", T("Size along {c}, nm", c=c), "float", float(defaults[i]), min=0.0, max=1e6,
               help=T("0: unbounded along this axis")) for i, c in enumerate("xyz"[:ndim])]


EDGE = _p("edge", T("Edge width, nm"), "float", 0.0, min=0.0, max=1e6,
          help=T("The distance over which the potential rises from 10 % to 90 % (a physical length); 0 is the sharpest "
                 "edge the grid resolves at the moment of adding (≈ 3 steps); a change of the grid on the fly keeps the "
                 "edge's width (the object stays the same)"))


# the display unit of every parameter by its id (Param.unit; the labels say it too): set on every palette schema
UNIT_OF = {"x": T("nm"), "y": T("nm"), "z": T("nm"), "sx": T("nm"), "sy": T("nm"), "sz": T("nm"), "edge": T("nm"),
           "mass_u": T("u"), "wavelength": T("nm"), "theta": "°", "phi": "°", "V": T("eV"), "radius": T("nm"),
           "position": T("nm"), "thickness": T("nm"), "width": T("nm"), "spacing": T("nm"), "offset": T("nm"),
           "hw": T("meV"), "Bx": T("T"), "By": T("T"), "Bz": T("T"), "grad": T("T/nm"), "flux": "h/e", "W": T("eV"),
           "length": T("nm"), "vx": T("nm/s"), "vy": T("nm/s"), "vz": T("nm/s"), "v_max": T("nm/s"),
           "bohm": T("points"), "n_slits": T("slits")}


def _with_units(schema: Schema, own: dict | None = None) -> Schema:
    for q in schema.params:
        if not q.unit:
            q.unit = (own or {}).get(q.id) or UNIT_OF.get(q.id, "")
    return schema


def palette(ndim: int) -> dict:
    axes = AXES[:ndim]
    spin = _p("spin", T("Spin (for particles of spin ½)"), "select", "+z",
              options=[("+z", T("↑ along z")), ("-z", T("↓ along z")), ("+x", T("→ along x")),
                       ("-x", T("← along x")), ("+y", T("along +y")), ("-y", T("along −y"))])
    packet = Schema([
        _p("species", T("Particle"), "select", "electron",
           options=[("electron", T("electron (charge −e, spin ½)")), ("neutron", T("neutron (spin ½)")),
                    ("he4", T("⁴He atom")), ("c60", T("fullerene C₆₀")), ("atom", T("atom of a given mass"))]),
        _p("mass_u", T("Atomic mass, u"), "float", 7.0, min=1e-3, max=1e6, log=True, show_if={"species": ["atom"]}),
        *[_p(c, T("Centre at preparation: {c}, nm", c=c), "float", 0.0, min=-1e6, max=1e6,
             help=T("Where the packet was prepared (dragging records here the point the wave was moved to); after "
                    "that the wave moves by itself, and ⟨{c}⟩ in the inspector shows where it is now", c=c)) for c in "xyz"[:ndim]],
        _p("wavelength", T("de Broglie wavelength, nm (0: at rest)"), "float", 2.0, min=0.0, max=1e6,
           help=T("Momentum ħk, k = 2π/λ; the grid must resolve the wave: |k| + 3/σ ≤ π/step. After a throw: 2π/|⟨k⟩| "
                  "of the mean wave vector of the whole wave (for a wave of several parts this is the wavelength of "
                  "none of them)")),
        _p("theta", T("Direction in the xy plane, °"), "float", 0.0, min=-360.0, max=360.0),
        *([_p("phi", T("Inclination to the xy plane, °"), "float", 0.0, min=-90.0, max=90.0)] if ndim == 3 else []),
        *[_p(f"s{c}", T("Width σ along {c}, nm", c=c), "float", 3.0, min=1e-3, max=1e6,
             help=T("σ of the distribution |ψ|²")) for c in "xyz"[:ndim]],
        _p("spin", spin.label, "select", "+z", options=spin.options,
           show_if={"species": ["electron", "neutron"]}),
        _p("bohm", T("Bohm particles (trajectories)"), "int", 0, min=0, max=300,
           help=T("An ensemble of points guided by this wave's probability current (the de Broglie–Bohm "
                  "interpretation); their initial positions drawn from |ψ|²")),
        # the velocity of a throw (the player's handle; world units: nm per second of the world's time), kept in step
        # with lambda and the direction: v = hbar k0 / m (on_add, on_set)
        *[_p(f"v{c}", T("Velocity: v{c}, nm/s", c=c), "float", 0.0, min=-1e18, max=1e18, hidden=True,
             help=T("= ħk₀/m; set by a throw")) for c in "xyz"[:ndim]],
        # the largest speed a throw may give this packet's wave now in any direction (``_set_vmax``; kept by the world)
        _p("v_max", T("Largest throw speed, nm/s"), "float", 0.0, min=0.0, max=1e30, hidden=True,
           help=T("The grid would not resolve a faster wave here and now (the world limits a faster throw and says "
                  "so)"))])
    height = T("Height, eV (negative: a well)")
    box = Schema([*_xyz(ndim), *_sizes(ndim, (2.0, 0.0, 0.0)),
                  _p("V", height, "float", 0.5, min=-1e4, max=1e4), EDGE])
    ball = Schema([*_xyz(ndim), _p("radius", T("Radius, nm"), "float", 3.0, min=1e-3, max=1e6),
                   _p("V", height, "float", 0.5, min=-1e4, max=1e4),
                   *([_p("shape", T("Shape"), "select", "sphere", options=[("sphere", T("ball")),
                                                                          ("cylinder", T("cylinder along z"))])]
                     if ndim == 3 else []), EDGE])
    wall = Schema([_p("axis", T("Wall across the axis"), "select", "0", options=axes),
                   _p("position", T("Wall position, nm"), "float", 0.0, min=-1e6, max=1e6),
                   _p("thickness", T("Thickness, nm"), "float", 2.0, min=1e-3, max=1e6),
                   _p("V", T("Height, eV"), "float", 3.0, min=-1e4, max=1e4),
                   _p("n_slits", T("Number of slits"), "int", 2, min=0, max=8),
                   _p("width", T("Slit width, nm"), "float", 2.0, min=1e-3, max=1e6),
                   _p("spacing", T("Distance between the slits' centres, nm"), "float", 10.0, min=0.0, max=1e6),
                   _p("offset", T("Shift of the slits along the wall, nm"), "float", 0.0, min=-1e6, max=1e6), EDGE])
    step = Schema([_p("axis", T("Step along the axis"), "select", "0", options=axes),
                   _p("position", T("Position, nm"), "float", 0.0, min=-1e6, max=1e6),
                   _p("V", T("Height, eV"), "float", 0.2, min=-1e4, max=1e4), EDGE])
    trap = Schema([*_xyz(ndim), _p("hw", T("Quantum energy ħω for the electron's mass, meV"), "float", 20.0, min=1e-6,
                                    max=1e5,
                                    help=T("V = m_e ω² r²/2: one potential for all particles (for a mass m the "
                                           "frequency is ω·√(m_e/m))"))])
    region = [_p("region", T("Region"), "select", "all", options=[("all", T("the whole scene")),
                                                                  ("box", T("rectangular"))]),
              *[_p(q.id, q.label, q.type, q.default, min=q.min, max=q.max, show_if={"region": ["box"]})
                for q in _xyz(ndim, region=True)],
              *[_p(q.id, q.label, q.type, q.default if q.default else 10.0, min=0.0, max=q.max,
                   show_if={"region": ["box"]}, help=q.help) for q in _sizes(ndim, (10.0, 10.0, 10.0))],
              _p("edge", EDGE.label, "float", 0.0, min=0.0, max=EDGE.max, show_if={"region": ["box"]}, help=EDGE.help)]
    bfield = Schema([_p("Bx", T("Bx, T"), "float", 0.0, min=-1e5, max=1e5),
                     _p("By", T("By, T"), "float", 0.0, min=-1e5, max=1e5),
                     _p("Bz", T("Bz, T"), "float", 10.0, min=-1e5, max=1e5),
                     _p("grad", T("Gradient g, T/nm (Bx = Bx₀ − g·(x − x_c), By = By₀ + g·(y − y_c))"), "float", 0.0,
                        min=-1e4, max=1e4,
                        help=T("A non-uniform field with div B = 0 and curl B = 0 around the region's centre (x_c, "
                               "y_c; for a field over the whole scene, around the origin): it acts on the spin; on a "
                               "charge only a uniform Bz")),
                     *region])
    flux = Schema([_p("x", T("Centre: {c}, nm", c="x"), "float", 0.0, min=-1e6, max=1e6),
                   _p("y", T("Centre: {c}, nm", c="y"), "float", 0.0, min=-1e6, max=1e6),
                   _p("flux", T("Flux, in quanta h/e"), "float", 0.5, min=-1e4, max=1e4),
                   _p("radius", T("Tube radius, nm"), "float", 1.0, min=1e-3, max=1e6)])
    det = Schema([*_xyz(ndim), *_sizes(ndim, (4.0, 0.0, 0.0)),
                  _p("W", T("Absorption strength W₀, eV (0: by the particles' energy)"), "float", 0.0, min=0.0,
                     max=1e6), EDGE])
    marker = Schema([*_xyz(ndim), *_sizes(ndim, (3.0, 3.0, 0.0)),
                     _p("rate", T("Marker's turning rate, rad/fs"), "float", 1.0, min=-1e4, max=1e4,
                        help=T("While the particle is in the region, the marker turns |0⟩ → cos|0⟩ + sin|1⟩")), EDGE])
    env = Schema([_p("rate", T("Localisation rate λ, 1/ps"), "float", 10.0, min=1e-9, max=1e9),
                  _p("length", T("Localisation length a, nm"), "float", 2.0, min=1e-3, max=1e6), *region])
    plane = Schema([_p("axis", T("Plane across the axis"), "select", "0", options=axes),
                    _p("position", T("Position, nm"), "float", 10.0, min=-1e6, max=1e6)])
    for sch, own in ((packet, None), (box, None), (ball, None), (wall, None), (step, None), (trap, None), (bfield, None),
                     (flux, None), (det, None), (marker, {"rate": T("rad/fs")}), (env, {"rate": T("1/ps")}),
                     (plane, None)):
        _with_units(sch, own)
    xyz = list("xyz"[:ndim])
    pos = {"position": xyz}
    # the throw's limit (integrator, 2026-11-11): the packet's own v_max, where the framework takes it
    vmax = {"velocity_max": "v_max"} if "velocity_max" in getattr(PG, "HANDLE_KEYS", ()) else {}
    axis_pos = {"position": {"param": "position", "axis_param": "axis"}}
    return {
        "packet": ObjectType("packet", T("Particle (wave packet)"), "particle", packet, limit=6,
                             color=COLORS["particle"],
                             help=T("A Gaussian packet; every particle has its own wave, the particles do not "
                                    "interact. A drag moves its wave at the current moment (the same wave in a new "
                                    "place), a throw sets the velocity (k₀ = m v / ħ)"),
                             handles={**pos, "velocity": [f"v{c}" for c in xyz], "size": "sx", **vmax}),
        "box": ObjectType("box", T("Barrier or well (a box)"), "potential", box, color=COLORS["barrier"],
                          handles={**pos, "size": "sx"}),
        "ball": ObjectType("ball", T("Ball (a disc)"), "potential", ball, color=COLORS["barrier"],
                           handles={**pos, "size": "radius"}),
        "slit_wall": ObjectType("slit_wall", T("Wall with slits"), "potential", wall, color=COLORS["barrier"],
                                handles={**axis_pos, "size": "thickness"}),
        "step": ObjectType("step", T("Potential step"), "potential", step, color=COLORS["barrier"], handles=axis_pos),
        "trap": ObjectType("trap", T("Harmonic trap"), "potential", trap, color=COLORS["well"], handles=pos),
        "bfield": ObjectType("bfield", T("Magnetic field"), "field", bfield, color=COLORS["field"],
                             help=T("On the spin through the magnetic moment; on a charge through the vector "
                                    "potential (only Bz in a plane, a field along an axis in a volume)"),
                             handles={**pos, "size": "sx"}),
        "flux": ObjectType("flux", T("Flux tube (Aharonov–Bohm)"), "field", flux, color=COLORS["flux"],
                           help=T("The field only inside the tube; outside, the vector potential"),
                           handles={"position": ["x", "y"], "size": "radius"}),
        "detector": ObjectType("detector", T("Detector (absorbing)"), "detector", det, color=COLORS["detector"],
                               help=T("The probability it absorbs is counted for every particle"),
                               handles={**pos, "size": "sx"}),
        "marker": ObjectType("marker", T("Which-path marker"), "detector", marker, color=COLORS["marker"],
                             help=T("A two-level device (Englert): it turns while the particle is in the region"),
                             handles={**pos, "size": "sx"}),
        "env": ObjectType("env", T("Environment (decoherence)"), "field", env, limit=1, color=COLORS["env"],
                          help=T("The environment localises the particle by random jumps (the Lindblad equation, "
                                 "quantum jumps)"),
                          handles={**pos, "size": "sx"}),
        "plane": ObjectType("plane", T("Flux plane"), "probe", plane, limit=4, color=COLORS["plane"],
                            help=T("The probability flux through the plane, integrated over time"), handles=axis_pos),
    }


SPIN = {"+z": [1, 0], "-z": [0, 1], "+x": [1 / math.sqrt(2), 1 / math.sqrt(2)],
        "-x": [1 / math.sqrt(2), -1 / math.sqrt(2)], "+y": [1 / math.sqrt(2), 1j / math.sqrt(2)],
        "-y": [1 / math.sqrt(2), -1j / math.sqrt(2)]}


def _pt(c, digits=3):
    """A point as a text: (x, y) or (x, y, z) (in Russian with semicolons); a coordinate below 1e-9 of the largest one
    (round-off) as 0. ``digits``: 3 or 4 significant digits."""
    c = [float(x) for x in c]
    big = max([abs(x) for x in c] + [1e-300])
    c = [0.0 if abs(x) < 1e-9 * big or abs(x) < 1e-12 else x for x in c]
    if len(c) == 2:
        return T("({x:.4g}, {y:.4g})", x=c[0], y=c[1]) if digits >= 4 else T("({x:.3g}, {y:.3g})", x=c[0], y=c[1])
    if len(c) == 3:
        return (T("({x:.4g}, {y:.4g}, {z:.4g})", x=c[0], y=c[1], z=c[2]) if digits >= 4
                else T("({x:.3g}, {y:.3g}, {z:.3g})", x=c[0], y=c[1], z=c[2]))
    return T("({x:.4g})", x=c[0]) if digits >= 4 else T("({x:.3g})", x=c[0])


def _mid(x) -> str:
    """The msgid of an engine's text (a T, or an exception raised with one), else its plain text."""
    t = text_of(x)
    return t["$t"] if is_t(t) else str(t)


# The engine's refusals this world puts in its own terms (code review 2026-11-12 i18n-code F5): matched by the engine's
# machine code (``lfphys.codes``), never by its wording. ``tests/test_p02_quantum.py``
# (``test_engine_refusals_are_said_in_the_worlds_terms``) triggers each one and asserts the code and the world's text.
RESOLUTION = ("qscene.resolution",)                       # an object's potential: the grid would not resolve a wave
PACKET_GRID = ("qscene.resolution", "qscene.packet_band")  # a packet the grid cannot hold
FIELD_WITH_CHARGE = ("qscene.field_with_charge",)
CLOSED_WITH_CHARGE = ("qscene.gauge",)


def _is(e, which) -> bool:
    """Whether the engine's refusal ``e`` (a coded exception, or None) has one of the codes ``which``."""
    return e is not None and code_of(e) in which


def _uncoded(why):
    """A coded stand-in for a text the engine returns without its code (``Scene.removal_reason``, ``edges_reason``:
    the engine has ``addition_check``/``particle_check`` but no ``removal_check``/``edges_check`` yet — an open point
    for the engine). The only remaining match on engine wording in this world; removed once the engine has them."""
    if not why:
        return None
    m = _mid(why)
    e = ValueError(why)
    if m.startswith("the field cannot be changed while the charged particle"):
        e.code = "qscene.field_with_charge"
    elif "a charged particle next to a field or a flux tube is" in m:
        e.code = "qscene.gauge"
    return e


def _rgb(hexcol):
    h = hexcol.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _block(a: np.ndarray, m: int) -> np.ndarray:
    """Average blocks so that no axis exceeds m points (drawing only)."""
    s = max(1, int(math.ceil(max(a.shape) / m)))
    if s == 1:
        return a
    sh = [n // s for n in a.shape]
    a = a[tuple(slice(0, n * s) for n in sh)]
    for ax in range(a.ndim):
        a = a.reshape(a.shape[:ax] + (sh[ax], s) + a.shape[ax + 1:]).mean(axis=ax + 1)
    return a


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p02_quantum"
    speed_range = (1e-18, 1e-6)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.ndim = 2 if params["dim"] == "2d" else 3
        n = int(params["n2"] if self.ndim == 2 else params["n3"])
        self.size = float(params["size"])
        self.open = params["edges"] == "open"
        self.rng = np.random.default_rng(seed)
        self.edge_w = EDGE_FRAC[self.ndim] * self.size
        edges = QS.EdgeLayers(width=self.edge_w, strength=5.0) if self.open else None
        self.qs = QS.Scene([n] * self.ndim, self.size / n, center=[0.0] * self.ndim, dt=2.0 ** -5, units=UNITS,
                           edges=edges, seed=int(seed), device="auto")
        # a world from a scene file starts at the file's time: the engine's clock too (review B6-F14: it integrated
        # the whole span from 0 in the header's first advance)
        self.qs.t = scene_time(params) / TU
        self.qs.error_every = ERROR_EVERY  # the step error sampled by scene steps, not by frames (review B6-Q7)
        self.d = self.size / n
        self.PALETTE = palette(self.ndim)
        self.ref = {}           # scene object id -> ("object" | "particle" | "plane", id in the engine's scene)
        self.bohm = {}          # particle object id -> its ensemble of Bohm points (``_seed_bohm``)
        self._abs = None        # the absorbers on the grid (rebuilt after every change of the scene)
        self._detR = {}         # the detectors' reflection and leak for the particles' waves (until the next change)
        self.marks = []         # outcomes of position measurements [(t, x, y, z, object id)]
        self._cache = {}        # absorbers' reflections and chosen strengths by what they depend on (_remember)
        self._placed_note = None  # (centre, text) of a packet ``place`` moved, announced when it is added
        self._op = None         # the scene operation in progress (``scene``): «edit» is a drag's release
        self._ps_key, self._ps = None, {}  # the palette's state by the scene's revision (palette_state)
        self._clearing = False
        # the physical width of every object's edge set to 0 («the sharpest the grid resolves»), fixed when it was
        # resolved: a live change of the grid keeps the objects as they are (review of LB1: the potential must not
        # change with the numerics)
        self.auto_edge = {}
        self._note = None       # the physics of a packet's edit, said in its own event after the change (on_set)
        self._prof = {}         # detectors' and markers' region profiles (measure; until the scene changes)
        self._regridded = False  # the grid was changed live in this world (rekey repeats it)
        self._carry_notes = []   # carry notes when the framework has no ``carry_note`` (``_cnote``)
        self._carry_waves = {}   # carried waves waiting for ``carry_world`` (``_carry_packet``)
        self.n_wave = 0
        self.carry = 0          # scene steps owed by the world's clock (Bohm advances in chunks)
        self.start_scene()
        self.default_speed = self._default_speed()

    # --- conversions -------------------------------------------------------------------------------------------
    def _vec(self, v, keys="xyz"):
        return [float(v.get(c, 0.0)) for c in keys[:self.ndim]]

    def _edge(self, v, oid=None):
        """The edge's physical width: as set, or for 0 the width resolved when the object got it (``auto_edge``), or
        for a new one 1.05 x the narrowest edge this grid resolves."""
        e = float(v.get("edge", 0.0) or 0.0)
        if e > 0:
            return e
        return self.auto_edge.get(oid, 1.05 * QS.edge_min(self.d))

    def _keep_edge(self, obj):
        """After an object was added or changed: an edge set to 0 keeps the width it was resolved with from now on."""
        v = obj["values"]
        if "edge" in v and not float(v.get("edge") or 0.0) > 0:
            self.auto_edge.setdefault(obj["id"], 1.05 * QS.edge_min(self.d))
        else:
            self.auto_edge.pop(obj["id"], None)

    def _size(self, v, i):
        s = float(v.get(f"s{'xyz'[i]}", 0.0) or 0.0)
        return s if s > 0 else None

    def _region(self, v):
        if v.get("region", "box") == "all":
            return None, None
        c = self._vec(v)
        lo = [None if self._size(v, i) is None else c[i] - 0.5 * self._size(v, i) for i in range(self.ndim)]
        hi = [None if self._size(v, i) is None else c[i] + 0.5 * self._size(v, i) for i in range(self.ndim)]
        return lo, hi

    def _object(self, obj) -> QS.SceneObject:
        t, v, n = obj["type"], obj["values"], self.ndim
        edge = self._edge(v, obj.get("id"))
        if t == "box":
            return QS.Box(self._vec(v), [self._size(v, i) for i in range(n)], v["V"] / EV, edge)
        if t == "ball":
            axes = [0, 1] if v.get("shape") == "cylinder" else None
            return QS.Ball(self._vec(v), float(v["radius"]), v["V"] / EV, edge, axes=axes)
        if t == "slit_wall":
            k = int(v["n_slits"])
            slits = [[float(v["offset"]) + (j - 0.5 * (k - 1)) * float(v["spacing"]), float(v["width"])]
                     for j in range(k)]
            if int(v["axis"]) >= n:
                raise Refusal(T("a plane has no z axis"))
            return QS.SlitWall(int(v["axis"]), float(v["position"]), float(v["thickness"]), v["V"] / EV, slits,
                               edge)
        if t == "step":
            if int(v["axis"]) >= n:
                raise Refusal(T("a plane has no z axis"))
            return QS.Step(int(v["axis"]), float(v["position"]), v["V"] / EV, edge)
        if t == "trap":
            omega = float(v["hw"]) * 1e-3 / EV  # hbar omega in units of energy = omega in units of 1/time (hbar = 1)
            return QS.HarmonicTrap(self._vec(v), [omega] * n, mass=1.0)
        if t == "bfield":
            lo, hi = self._region(v)
            g = float(v["grad"]) / TESLA
            G = None if g == 0 else [[-g, 0.0, 0.0], [0.0, g, 0.0], [0.0, 0.0, 0.0]]
            c = self._vec(v) + [0.0] * (3 - n)
            return QS.MagneticField([v["Bx"] / TESLA, v["By"] / TESLA, v["Bz"] / TESLA], gradient=G,
                                    center=c if v.get("region") == "box" else [0.0, 0.0, 0.0], lo=lo, hi=hi,
                                    edge=edge if lo is not None else None)
        if t == "flux":
            return QS.FluxTube([float(v["x"]), float(v["y"])], 2.0 * math.pi * float(v["flux"]), float(v["radius"]))
        if t == "detector":
            c = self._vec(v)
            lo = [None if self._size(v, i) is None else c[i] - 0.5 * self._size(v, i) for i in range(n)]
            hi = [None if self._size(v, i) is None else c[i] + 0.5 * self._size(v, i) for i in range(n)]
            det = QS.Detector(lo, hi, 1.0, edge, name=obj["label"])
            det.strength = float(v["W"]) / EV if float(v["W"]) > 0 else self._auto_W(det)
            return det
        if t == "marker":
            c = self._vec(v)
            lo = [None if self._size(v, i) is None else c[i] - 0.5 * self._size(v, i) for i in range(n)]
            hi = [None if self._size(v, i) is None else c[i] + 0.5 * self._size(v, i) for i in range(n)]
            return QS.PathMarker(lo, hi, float(v["rate"]) / FS, edge)
        if t == "env":
            lo, hi = self._region(v)
            return QS.Localization(float(v["rate"]) * 1e12 * TU, float(v["length"]), lo=lo, hi=hi,
                                   edge=edge if lo is not None else None)
        raise Refusal(T("no object “{type}”", type=t))

    def _finite(self, ob):
        """Refuse an object whose values on the grid are not finite (a value that overflows in the scene's units would
        make the waves NaN for good: review B6-F15)."""
        g = self.qs.grid
        with np.errstate(all="ignore"):  # an overflowing value is what this looks for
            arrs = [ob.V(g)] if isinstance(ob, QS.Shape) else [ob.W(g)] if isinstance(ob, QS.Detector) else \
                [ob.field(g)] if isinstance(ob, (QS.MagneticField, QS.FluxTube)) else \
                [ob.b(g)] if isinstance(ob, QS.PathMarker) else []
        if not all(np.all(np.isfinite(a)) for a in arrs):
            raise Refusal(T("the object's values on the grid are not finite (numbers too large)"))
        return ob

    def _packet(self, v) -> QS.Packet:
        sp = v["species"]
        species = QS.species(sp, UNITS, mass_u=float(v.get("mass_u", 0.0)) if sp == "atom" else None)
        lam = float(v["wavelength"])
        kk = 0.0 if lam <= 0 else 2.0 * math.pi / lam
        th, ph = math.radians(float(v.get("theta", 0.0))), math.radians(float(v.get("phi", 0.0)))
        k = [kk * math.cos(th) * math.cos(ph), kk * math.sin(th) * math.cos(ph), kk * math.sin(ph)][:self.ndim]
        sig = [float(v[f"s{c}"]) for c in "xyz"[:self.ndim]]
        spin = SPIN[v.get("spin", "+z")] if species.spin_half else None
        return QS.Packet(species, self._vec(v), k, sig, spin)

    def _waves(self):
        """(wavenumber, mass) of the particles' waves the absorbers must take: |k| and |k| +- 2 sigma_k of each packet
        (sigma_k = 1/(2 sigma), the narrowest axis); a packet at rest by its spread alone."""
        out = []
        for p in self.qs.particles.values():
            if not p.active:
                continue
            kk = float(np.linalg.norm(p.packet.k))
            s = 1.0 / (2.0 * float(np.min(p.packet.sigma)))
            for k in (max(kk - 2 * s, 0.5 * s), max(kk, s), kk + 2 * s):
                out.append((k, float(p.species.mass)))
        return out

    def _edge_RT(self, k, m, W0):
        """The open edges' reflection and leak for a wave of wavenumber k, averaged over the angle of incidence with the
        flux each direction carries to the face (isotropic directions: weight cos(theta) in a plane, cos(theta)
        sin(theta) in space; Gauss-Legendre over theta in [0, pi/2]), and R at 60 degrees: the transverse momentum is
        conserved, so a wave at theta meets the layer as a 1-D wave of k cos(theta) (review B6-Q8: the normal incidence
        alone showed 1.3e-4 where the 3-D preset's faces returned ~1e-3). Returns (<R>, <T>, R(60))."""
        key = ("edgeRT", float(k), float(m), float(W0), self.edge_w, self.ndim)
        if key not in self._cache:
            x, w = np.polynomial.legendre.leggauss(ANGLES)
            th = 0.25 * math.pi * (x + 1.0)
            wt = w * np.cos(th) * (np.sin(th) if self.ndim == 3 else 1.0)
            wt = wt / wt.sum()
            R, Tr = QS.EdgeLayers(width=self.edge_w, strength=float(W0)).reflection(np.append(k * np.cos(th), 0.5 * k), m)
            self._remember(key, (float(np.sum(wt * R[:-1])), float(np.sum(wt * Tr[:-1])), float(R[-1])))
        return self._cache[key]

    def _remember(self, key, value):
        """A computed reflection (a pure function of its key) kept for the next change of the scene (review UX-ui U3:
        every change re-tuned the absorbers from scratch, 18-60 s); the oldest entries go beyond CACHE_MAX."""
        if len(self._cache) >= CACHE_MAX:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = value

    def _auto_W(self, det=None):
        """The absorbers' strength W0 for the particles' waves: the one (of a log-spaced set around their energy) that
        minimises the worst reflection + leak, from stationary transfer matrices of the absorber's own profile: a weak
        absorber lets the wave through (past the edges it comes back on the other side of the periodic window), a
        strong one reflects it. The open edges' ramp W0 (s/width)^2 (``EdgeLayers.reflection``, the staircase of
        ``schrodinger_nd.layer_reflection``) for the normal wavenumbers |k|, |k| +- 2 sigma_k and for |k| at 60
        degrees (k/2: review B6-Q8 — tuned at normal incidence alone the double slit's layers sent back 3e-4 at 60
        degrees, now 1.5e-5); a detector's box with its edges at normal incidence across its thinnest axis
        (``Detector.reflection``; a screen is met head-on). What the edges return over all angles (flux-weighted;
        grazing waves are reflected by any layer) is in the checks. Without particles: 5 units (0.38 eV). All the
        strengths of the set in one vectorised call per mass, and the choice kept for the same waves and absorber
        (review UX-ui U3: a change that touches neither, e.g. a box in the middle, no longer re-tunes)."""
        waves = self._waves()
        if not waves:
            return 5.0
        E = max(k * k / (2 * m) for k, m in waves)
        ax = self._det_axis(det) if det is not None else None
        if det is None:
            waves = waves + [(0.5 * float(np.linalg.norm(p.packet.k)), float(p.species.mass))
                             for p in self.qs.particles.values() if p.active and np.linalg.norm(p.packet.k) > 0]
        # a detector's reflection depends on its profile across the axis, not on where it stands: a moved detector
        # (a drag, plan P16.2) keeps its strength without a new computation
        shape = (("edges", self.edge_w) if det is None or ax is None else
                 ("det", det.lo[ax] is None, det.hi[ax] is None,
                  None if det.lo[ax] is None or det.hi[ax] is None else float(det.hi[ax]) - float(det.lo[ax]),
                  float(det.edge), ax))
        key = ("W", shape, tuple(waves))
        if key in self._cache:
            return self._cache[key]
        W0s = E * W_SET
        worst = np.zeros(len(W0s))
        masses = sorted({m for _, m in waves})
        for m in masses:
            ks = [k for k, mm in waves if mm == m]
            if det is None or ax is None:
                R, Tr = QS.EdgeLayers(width=self.edge_w, strength=1.0).reflection(ks, m, strengths=W0s)
            else:
                R, Tr = QS.Detector(det.lo, det.hi, 1.0, det.edge).reflection(ks, m, axis=ax, strengths=W0s)
            worst = np.maximum(worst, np.max(R + Tr, axis=1))
        W = float(W0s[int(np.argmin(worst))])  # the first of equal minima, as before
        self._remember(key, W)
        return W

    def _det_axis(self, det):
        """The axis a detector is thinnest along (where a wave crosses it); None when it is unbounded everywhere."""
        bounded = [i for i in range(self.ndim) if det.lo[i] is not None or det.hi[i] is not None]
        if not bounded:
            return None
        return min(bounded, key=lambda i: (det.hi[i] if det.hi[i] is not None else math.inf)
                   - (det.lo[i] if det.lo[i] is not None else -math.inf))

    # --- a packet's momentum in its values: lambda, the direction and the velocity (plan P16.2) ------------------------
    def _k_of(self, v) -> list:
        """The packet's wavevector (1/nm) from its wavelength and direction."""
        lam = float(v["wavelength"])
        kk = 0.0 if lam <= 0 else 2.0 * math.pi / lam
        th, ph = math.radians(float(v.get("theta", 0.0))), math.radians(float(v.get("phi", 0.0)))
        return [kk * math.cos(th) * math.cos(ph), kk * math.sin(th) * math.cos(ph), kk * math.sin(ph)][:self.ndim]

    def _set_momentum(self, v, k, mass, direction=True):
        """Write the wavevector k (1/nm) into a packet's values: with ``direction`` the wavelength 2 pi/|k| and the
        direction (the direction kept at rest), and always the velocity v = hbar k / m in nm per second of the world's
        time (the throw handle's unit); 10 significant digits."""
        r10 = lambda x: float(f"{float(x):.10g}")  # noqa: E731
        kk = float(np.linalg.norm(k))
        if direction:
            v["wavelength"] = r10(2.0 * math.pi / kk) if kk > 0 else 0.0
            if kk > 0:
                v["theta"] = r10(math.degrees(math.atan2(k[1], k[0])))
                if self.ndim == 3:
                    v["phi"] = r10(math.degrees(math.asin(max(-1.0, min(1.0, k[2] / kk)))))
        for i, c in enumerate("xyz"[:self.ndim]):
            v[f"v{c}"] = r10(k[i] / mass / TU)

    def _set_vmax(self, obj):
        """The largest speed a throw may give the packet's wave now in any direction (the throw's limit,
        ``handles["velocity_max"]``; review LB1-p02-ux Q5, X5: the limit shown is the one the world applies): from the
        wave itself, ``Scene.kick_reach`` — its measured spectrum's model moved to the thrown momentum must pass the
        scene's resolution rule (|k| + 6 sigma_k <= pi/d, next to what acts on it sqrt((|k| + 6 sigma_k)^2 + 2 m dV)
        <= 2/3 pi/d) and the alias test (all but 1e-6 of the spectrum inside the band) —, VMAX_MARGIN inside it, in nm
        per second of the world's time; for a particle without a wave the fresh packet's rule (sigma_k = 1/(2 sigma)).
        Kept in the packet's values (a hidden parameter), again after every change of the packet or of the grid. The
        wave moves on between changes: a throw is decided by the scene's own tests at that moment (``_throw``)."""
        v = obj["values"]
        mass = self._packet(v).species.mass
        ref = self.ref.get(obj["id"])
        p = self.qs.particles.get(ref[1]) if ref and ref[0] == "particle" else None
        if p is not None and p.active and p.psi is not None:
            k = VMAX_MARGIN * self.qs.kick_reach(p.id)
        else:
            sk = 1.0 / (2.0 * min(float(v[f"s{c}"]) for c in "xyz"[:self.ndim]))
            lim = QS.INTERACT_BAND * math.pi / self.d
            k = VMAX_MARGIN * (lim - QS.PACKET_NYQUIST * sk)
        v["v_max"] = float(f"{max(k, 0.0) / mass / TU:.6g}")

    def _refresh_vmax(self):
        """The throw limit follows the wave (review LB1-p02-ux X5: computed once at a change, it stayed the fresh
        packet's while the wave split at a wall): every VMAX_EVERY frames (by count: a restored world does the same)
        each packet's v_max is computed again and, when it moved by more than VMAX_CHANGE, sent in a scene message."""
        changed = False
        for o in self.objects.values():
            if o["type"] != "packet":
                continue
            old = float(o["values"].get("v_max") or 0.0)
            self._set_vmax(o)
            new = float(o["values"]["v_max"])
            if (old > 0) != (new > 0) or (old > 0 and abs(new - old) > VMAX_CHANGE * old):
                changed = True
            elif new != old:
                o["values"]["v_max"] = old  # within the share: the limit the player has stays (no message)
        if changed:
            self.rev += 1
            self.emit_scene()

    # --- the framework's hooks ------------------------------------------------------------------------------------
    def on_add(self, obj, state):
        t = obj["type"]
        if t == "packet":
            pk = self._packet(obj["values"])
            try:
                pid = self.qs.add_particle(pk)
            except ValueError as e:
                raise self._packet_refusal(obj, pk, e) from None
            self._set_momentum(obj["values"], pk.k, pk.species.mass, direction=False)
            self.ref[obj["id"]] = ("particle", pid)
            self._set_vmax(obj)
            self._seed_bohm(obj)
            self._carry_packet(obj, state)
            note, self._placed_note = self._placed_note, None
            if note and note[0] == tuple(self._vec(obj["values"])) and not self._loading:
                self.emit({"type": "event", "kind": "scene", "t": self.t, "notify": True,
                           "text": T("“{label}”: {note}", label=obj["label"], note=note[1])})
        elif t == "plane":
            v = obj["values"]
            if int(v["axis"]) >= self.ndim:
                raise Refusal(T("a plane has no z axis"))
            self.ref[obj["id"]] = ("plane", self.qs.add_plane(int(v["axis"]), float(v["position"])))
        else:
            ob = self._finite(self._object(obj))
            self._inside(obj, ob)
            try:
                self.ref[obj["id"]] = ("object", self.qs.add(ob, dt=self._dt_with(ob)))
            except ValueError as e:
                raise self._refusal(obj, e) from None
            self._keep_edge(obj)
        self._tune()

    def on_remove(self, obj):
        # the engine first, the reference after it (review UX-params P28: a removal the scene refused, e.g. a field
        # while a charged particle is in the window, had already dropped the reference and every later removal or
        # "Clear scene" failed with "Scene: 'o1'")
        kind, qid = self.ref[obj["id"]]
        if kind == "particle":
            self.qs.remove_particle(qid)
            self.bohm.pop(obj["id"], None)
        elif kind == "plane":
            self.qs.remove_plane(qid)
        else:
            self.qs.remove(qid)
        del self.ref[obj["id"]]
        self.auto_edge.pop(obj["id"], None)
        self._tune()

    def on_set(self, obj, old):
        kind, qid = self.ref[obj["id"]]
        self._note = None
        if kind == "particle":
            self._set_packet(obj, old, qid)
            self._set_vmax(obj)
        elif kind == "plane":
            v = obj["values"]
            if int(v["axis"]) >= self.ndim:
                raise Refusal(T("a plane has no z axis"))
            new = self.qs.add_plane(int(v["axis"]), float(v["position"]))
            self.qs.remove_plane(qid)
            self.ref[obj["id"]] = ("plane", new)
        else:
            v = obj["values"]
            if "edge" in v and not float(v.get("edge") or 0.0) > 0 and float(old.get("edge") or 0.0) > 0:
                self.auto_edge.pop(obj["id"], None)  # set back to 0: the sharpest edge of the grid now
            ob = self._finite(self._object(obj))
            self._inside(obj, ob)
            try:
                self.qs.update(qid, dt=self._dt_with(ob, qid), **ob.params())
            except ValueError as e:
                raise self._refusal(obj, e) from None
            self._keep_edge(obj)
        self._tune()
        if self._note:
            self.emit({"type": "event", "kind": "scene", "t": self.t, "text": self._note})
            self._note = None

    POS_KEYS = ("x", "y", "z")
    MOM_KEYS = ("wavelength", "theta", "phi", "vx", "vy", "vz")

    def _set_packet(self, obj, old, qid):
        """A packet's values changed. Its position and its momentum (the wavelength and direction, or the velocity of a
        throw) prepare the same wave anew at the current moment (``Scene.transform_particle``): moved so that its mean
        position is the point given (for a charged particle by the magnetic translation, refused where none keeps the
        wave: next to a flux tube's path or across a field's edge — review LB1-p02-ux Q1, Q2), given the momentum that
        makes its mean kinetic wavenumber the one given — a thrown velocity v becomes k0 = m v / hbar (the wavelength
        and direction follow). A throw (a drag's release, op "edit") faster than the scene takes there and then is
        clamped to the fastest it takes in that direction (``Scene.kick_limit``, the scene's own tests) and said so; a
        velocity typed in the inspector (op "set") is refused with that limit. Only the Bohm points changed: the wave
        goes on (review B6-F16). Anything else (the species, the widths, the spin), or a particle without a wave (taken
        by a detector), prepares a fresh packet from the values."""
        v = obj["values"]
        nd = self.ndim
        xyz = "xyz"[:nd]
        changed = {k for k in v if v.get(k) != old.get(k)}
        pos = [c for c in xyz if c in changed]
        mom = changed & set(self.MOM_KEYS)
        other = changed - set(self.POS_KEYS) - set(self.MOM_KEYS) - {"bohm", "v_max"}
        qs = self.qs
        p = qs.particles[qid]
        thrown = bool(mom & {"vx", "vy", "vz"})
        if not changed - {"bohm", "v_max"}:
            self._seed_bohm(obj)
            return
        lab = obj["label"]
        if other or not (p.active and p.psi is not None and qs.norm(qid) > 0):
            mass = self._packet(v).species.mass
            if thrown and not mom & {"wavelength", "theta", "phi"}:
                self._set_momentum(v, [float(v[f"v{c}"]) * TU * mass for c in xyz], mass)
            pk = self._packet(v)
            try:
                qs.replace_particle(qid, pk)  # a new packet now
            except ValueError as e:
                raise self._packet_refusal(obj, pk, e) from None
            self._set_momentum(v, pk.k, mass, direction=False)
            self._seed_bohm(obj)
            if not other:
                self._note = T("“{label}”: there was no wave (the particle was registered by a detector); a new "
                               "packet was prepared at {at} nm", label=lab, at=_pt(self._vec(v)))
            return
        o = qs.observables(qid)
        mass = p.species.mass
        shift = dk = None
        if pos:
            target = np.array([float(v[c]) if c in pos else o["r"][i] for i, c in enumerate(xyz)])
            wl, wh = self._window()
            out = [i for i in range(nd) if not wl[i] <= target[i] < wh[i]]
            if out:
                i = out[0]
                raise Refusal(T("“{label}”: the point {at} nm is outside the window (along {axis} the window runs "
                                "from {lo:.4g} to {hi:.4g} nm)", label=lab, at=_pt(target), axis="xyz"[i],
                                lo=float(wl[i]), hi=float(wh[i])),
                              hint=T("move the wave inside the window"))
            shift = target - np.array(o["r"])
            if float(np.max(np.abs(shift))) <= 1e-9 * self.d:  # the same place again (a throw from where it is)
                shift = None
        kt = None
        if mom:
            if thrown:
                kt = [float(v[f"v{c}"]) * TU * mass if f"v{c}" in mom else o["k"][i] for i, c in enumerate(xyz)]
            else:
                kt = self._k_of(v)
            dk = np.array(kt) - np.array(o["k"])
        asked = None
        leak = 0.0
        if shift is not None and self.open:  # review LB1-p02-ux Q8: what a move puts into the far side's layer
            leak = self._far_leak(qs.wave(qid), shift, float(np.linalg.norm(o["k"])), mass)
            if leak > QS.REGRID_TOL:
                raise Refusal(T("“{label}”: the wave cannot be moved this way: part of it would cross the window's "
                                "face into the absorbing layer on the other side and, going inwards, pass through it: "
                                "up to {leak:.2g} of its probability would get into the window (a WKB estimate at "
                                "normal incidence), more than the tolerance {tol:.4g}", label=lab, leak=leak,
                                tol=QS.REGRID_TOL),
                              hint=T("move it a shorter distance or away from the window's edge"))
        try:
            rep = qs.transform_particle(qid, shift=shift, dk=dk)
        except ValueError as e:
            what = getattr(e, "what", None)
            if not (thrown and self._op == "edit" and what in ("alias", "resolution") and kt is not None):
                raise self._move_refusal(obj, e, shift, kt) from None
            a = qs.kick_limit(qid, kt, shift)
            if a is None:
                raise self._move_refusal(obj, e, shift, kt) from None
            asked, kt = list(kt), [a * float(x) for x in kt]
            dk = np.array(kt) - np.array(o["k"])
            try:
                rep = qs.transform_particle(qid, shift=shift, dk=dk)
            except ValueError as e2:
                raise self._move_refusal(obj, e2, shift, kt) from None
        if kt is not None:
            self._set_momentum(v, kt, mass)
        B = self.bohm.get(obj["id"])
        if B is not None and shift is not None:  # |psi|^2 moved with the wave: so do its points in flight
            B["X"][B["fly"]] = self._wrap(B["X"][B["fly"]] + shift)
            B["Xc"][B["flyc"]] = self._wrap(B["Xc"][B["flyc"]] + shift)
        parts = []
        if shift is not None:
            if p.species.charge != 0 and qs._arr["A"] is not None:
                parts.append(T("the same wave moved by {shift} nm: ⟨r⟩ {r0} → {r1} nm (a magnetic translation: the "
                               "kinetic part of the wave kept)", shift=_pt(shift), r0=_pt(rep["r_before"]),
                               r1=_pt(rep["r_after"])))
            else:
                parts.append(T("the same wave moved by {shift} nm: ⟨r⟩ {r0} → {r1} nm", shift=_pt(shift),
                               r0=_pt(rep["r_before"]), r1=_pt(rep["r_after"])))
        if kt is not None:
            kk = float(np.linalg.norm(kt))
            vk = [float(x) / mass / TU * 1e-12 for x in kt]  # km/s
            how = (T("thrown: v = {v} km/s → k₀ = m v/ħ = {k} nm⁻¹", v=_pt(vk, 4), k=_pt(kt)) if thrown
                   else T("given a momentum: k₀ = {k} nm⁻¹", k=_pt(kt)))
            if kk > 0:
                parts.append(T("{how}, λ = {lam:.4g} nm (was ⟨k⟩ = {k0} nm⁻¹)", how=how, lam=2 * math.pi / kk,
                               k0=_pt(rep["k_before"])))
            else:
                parts.append(T("{how}, λ = ∞ (was ⟨k⟩ = {k0} nm⁻¹)", how=how, k0=_pt(rep["k_before"])))
            if asked is not None:
                va = float(np.linalg.norm(asked)) / mass / TU * 1e-12
                parts[-1] = T("{text}; the throw was limited: {asked:.4g} km/s requested, the grid here and now does "
                              "not resolve the wave faster than {vmax:.4g} km/s in this direction", text=parts[-1],
                              asked=va, vmax=kk / mass / TU * 1e-12)
        if not parts:
            return
        tail = [T("probability in the window {p:.6g} kept", p=float(rep["norm_before"])),
                T("energy ⟨H⟩ {e0:.4g} → {e1:.4g} eV", e0=rep["E_before"] * EV, e1=rep["E_after"] * EV)]
        if rep.get("T_before") is not None and rep.get("T_after") is not None:
            tail.append(T("kinetic ⟨(p − qA)²⟩/2m {e0:.4g} → {e1:.4g} eV", e0=rep["T_before"] * EV,
                          e1=rep["T_after"] * EV))
        if rep.get("in_layers", 0.0) > 1e-6 and shift is not None:
            tail.append(T("the edges' absorbing layers held {p:.2g} of its probability (an outgoing wave): moved "
                          "along with the wave", p=float(rep["in_layers"])))
        if rep.get("far_layer", 0.0) > 1e-12:
            tail.append(T("{p:.2g} of the probability crossed a face into the absorbing layer on the other side of "
                          "the window: the layer will absorb it (at most {leak:.2g} gets inside)",
                          p=float(rep["far_layer"]), leak=leak))
        self._note = T("“{label}”: {what}. A fresh packet: the action “Prepare the packet anew”", label=lab,
                       what=join(parts + tail, "; "))

    def _far_leak(self, psi, shift, kk, mass):
        """The share of a wave that a move by ``shift`` carries across a face into the far side's absorbing layer and
        that the layer lets through as it goes inward from where it lands (review LB1-p02-ux Q8): per landing point at
        depth D from the layer's inner face, the WKB attenuation exp(-2 W0 D^3 / (3 v w^2)) of the ramp W0 (s/w)^2 at
        normal incidence (the least absorbed; v = hbar |<k>| / m), summed with |psi|^2. A bound for the refusal, not the
        evolution: reflection by the layer is not counted (it only lowers what passes)."""
        g = self.qs.grid
        w, W0 = float(self.edge_w), float(self.qs.edges.strength)
        v = max(kk, 1e-9) / mass
        comps = psi if psi.ndim == self.ndim + 1 else psi[None]
        rho = np.sum(comps.real ** 2 + comps.imag ** 2, axis=0)
        tot = float(rho.sum())
        if not tot > 0:
            return 0.0
        leak = 0.0
        for a in range(self.ndim):
            sa = float(shift[a])
            if sa == 0:
                continue
            lo = float(g.axes[a][0]) - 0.5 * float(g.d[a])
            hi = lo + g.shape[a] * float(g.d[a])
            shp = [1] * self.ndim
            shp[a] = -1
            x = g.axes[a].reshape(shp)
            u = (x + sa - hi) if sa > 0 else (lo - (x + sa))
            land = (u >= 0) & (u < w)
            D = np.clip(w - u, 0.0, w)
            att = np.where(land, np.exp(-2.0 * W0 * D ** 3 / (3.0 * v * w * w)), 0.0)
            leak += float(np.sum(rho * np.broadcast_to(att, rho.shape)))
        return leak / tot

    def _label_of(self, kind, qid):
        """The scene object's label for the engine's object (``kind`` "object" | "particle" | "plane") ``qid``."""
        return next((self.objects[o]["label"] for o, (k, q) in self.ref.items() if k == kind and q == qid), f"#{qid}")

    def _move_refusal(self, obj, e, shift=None, kt=None):
        """The scene's refusal of a packet's move or impulse in the owner's terms: which test refused (the window's
        face, the magnetic translation, the grid's band, the resolution next to what acts on the particle) and whether
        the place or the speed is the cause (review LB1-p02-ux Q5: "there or at this speed" left the owner guessing)."""
        lab, what = obj["label"], getattr(e, "what", None)
        if what == "wrap":
            return Refusal(T("“{label}”: the wave cannot be moved this way: {p:.3g} of its probability would cross a "
                             "window face into the window on the other side (the grid is periodic)", label=lab,
                             p=float(e.value)), detail=str(e),
                           hint=T("move it a shorter distance or closer to the window's middle; or enlarge the window "
                                  "(“Window size” changes on the fly)"))
        if what == "gauge":
            why = []
            for oid_q, pr in sorted((getattr(e, "tubes", None) or {}).items()):
                if pr > 1e-12:
                    why.append(T("the path of the tube “{tube}” relative to the wave passes through it ({p:.2g} of "
                                 "its probability there): the flux the wave's parts enclose would change",
                                 tube=self._label_of("object", oid_q), p=float(pr)))
            for oid_q in getattr(e, "fields", None) or []:
                why.append(T("the field “{field}” where the wave is moved to is not the one where it was",
                             field=self._label_of("object", oid_q)))
            if not why:
                why.append(T("the magnetic field at the new place is not the same as at the old one"))
            dT = getattr(e, "dT", float("nan"))
            hint = T("move it so that the tube goes round it relative to the wave, or to where the field is the same; to "
                     "start afresh: the action “Prepare the packet anew” (the centre from the parameters or where the "
                     "wave is now)")
            if math.isfinite(dT):
                return Refusal(T("“{label}”: the same wave cannot be moved this way: {why}. Its kinetic energy would "
                                 "change by {dT:.2g} %, the kinetic field (p − qA)ψ by a share of {share:.2g}",
                                 label=lab, why=join(why, "; "), dT=100 * dT, share=float(e.value)),
                               detail=str(e), hint=hint)
            return Refusal(T("“{label}”: the same wave cannot be moved this way: {why}; the kinetic field (p − qA)ψ "
                             "would change by a share of {share:.2g}", label=lab, why=join(why, "; "),
                             share=float(e.value)), detail=str(e), hint=hint)
        if what in ("alias", "resolution"):
            # the place or the speed: the throw's limit there (a = None: the place refuses even at rest)
            a = None
            if kt is not None:
                try:
                    a = self.qs.kick_limit(self.ref[obj["id"]][1], kt, shift)
                except Exception:  # noqa: BLE001 - a hint only
                    a = None
            place = kt is None or a is None
            mass = self.qs.particles[self.ref[obj["id"]][1]].species.mass
            where = (T("at the new place") if shift is not None and place else T("here") if place else None)
            K, lim = float(getattr(e, "K", float("nan"))), float(getattr(e, "lim", float("nan")))
            if what == "alias":
                text = T("“{label}”: at such a speed the grid (step {d:.4g} nm) will not resolve the wave: {p:.3g} of "
                         "the wave's spectrum would lie beyond its band", label=lab, d=self.d, p=float(e.value))
            elif getattr(e, "inter", True) and where is not None:
                text = T("“{label}”: {where} the grid (step {d:.4g} nm) does not resolve the wave next to what acts on "
                         "it: its wavenumbers reach {K:.3g} nm⁻¹, while next to a potential or a field the grid "
                         "resolves ≤ {lim:.3g} nm⁻¹ (⅔·π/step)", label=lab, where=where, d=self.d, K=K, lim=lim)
            elif getattr(e, "inter", True):
                text = T("“{label}”: the grid (step {d:.4g} nm) does not resolve the wave next to what acts on it: its "
                         "wavenumbers reach {K:.3g} nm⁻¹, while next to a potential or a field the grid resolves "
                         "≤ {lim:.3g} nm⁻¹ (⅔·π/step)", label=lab, d=self.d, K=K, lim=lim)
            else:
                text = T("“{label}”: the wave is finer than the grid (step {d:.4g} nm) resolves: its wavenumbers reach "
                         "{K:.3g} nm⁻¹ at π/step = {lim:.3g} nm⁻¹", label=lab, d=self.d, K=K, lim=lim)
            if kt is not None and not place:
                vmax = a * float(np.linalg.norm(kt)) / mass / TU * 1e-12
                text = T("{text}. The reason is the speed: in this direction no faster than {v:.4g} km/s now",
                         text=text, v=vmax)
                hint = T("throw slower (a smaller throw scale or a larger λ) or make the grid finer (“Grid points per "
                         "axis”, on the fly)")
            elif shift is not None:
                text = T("{text}. The reason is the location: the wave cannot be moved there even at rest", text=text)
                hint = T("move it farther from the potential or make the grid finer (“Grid points per axis”, on the "
                         "fly)")
            else:
                hint = T("a slower particle, a lower potential or a finer grid (“Grid points per axis”, on the fly)")
            return Refusal(text, detail=str(e), hint=hint)
        return e

    def scene(self, args):
        """The framework's scene command; "clear" removes the particles first: a uniform field cannot be switched off
        while a charged particle is in the window (the scene refuses it, review B6-Q3), but with them gone it can. The
        operation is kept while it runs (``_op``): a drag's release («edit») clamps a throw, an inspector's «set» does
        not."""
        self._op = args.get("op")
        try:
            if args.get("op") == "clear":
                self.objects = dict(sorted(self.objects.items(), key=lambda kv: kv[1]["type"] != "packet"))
                self._clearing = True
                try:
                    return super().scene(args)
                finally:
                    self._clearing = False
            return super().scene(args)
        finally:
            self._op = None

    # --- placement, the palette, removals (review UX-ui U4, U7, U8, U13; UX-params P28) ----------------------------
    def _removal_check(self, qid):
        """The engine's coded refusal of removing object ``qid`` now, or None (``Scene.removal_check`` when the engine
        has it; until then the text ``removal_reason`` gives, matched in ``_uncoded``)."""
        f = getattr(self.qs, "removal_check", None)
        return f(qid) if f is not None else _uncoded(self.qs.removal_reason(qid))

    def _edges_check(self, edges):
        """The engine's coded refusal of ``set_edges(edges)`` now, or None (as ``_removal_check``)."""
        f = getattr(self.qs, "edges_check", None)
        return f(edges) if f is not None else _uncoded(self.qs.edges_reason(edges))

    def can_remove(self, obj):
        """Why the object cannot be removed now (the engine's own test, nothing changed), or None. In "Clear scene"
        the particles go first, so a field can then go too."""
        ref = self.ref.get(obj["id"])
        if ref is None or ref[0] != "object" or self._clearing:
            return None
        chk = self._removal_check(ref[1])
        if _is(chk, FIELD_WITH_CHARGE):
            return T("while a charged particle is in the window, the field cannot be switched off (the impulse of the "
                     "induced field depends on how the magnet is built): remove the particle first")
        return text_of(chk) if chk is not None else None

    def _window(self):
        g = self.qs.grid
        return ([float(a[0]) - 0.5 * d for a, d in zip(g.axes, g.d)], [float(a[-1]) + 0.5 * d for a, d in zip(g.axes, g.d)])

    def _inside(self, obj, ob):
        """An object wholly outside the window is refused (review UX-ui U8: a box at 10^6 nm was taken without a word);
        one partly outside is taken with a note (beyond the window it does not act)."""
        wl, wh = self._window()
        if obj["type"] == "trap":  # its potential fills the window wherever its centre is: the centre must be inside
            c = self._vec(obj["values"])
            if any(not (wl[i] <= c[i] <= wh[i]) for i in range(self.ndim)):
                raise Refusal(T("the trap's centre {at} nm is outside the window ({lo:.4g} … {hi:.4g} nm along "
                                "every axis)", at=_pt(c, 4), lo=float(wl[0]), hi=float(wh[0])),
                              hint=T("put the centre inside the window"))
            return
        lo, hi = ob.bbox(self.ndim)
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        out = [i for i in range(self.ndim) if hi[i] < wl[i] or lo[i] > wh[i]]
        if out:
            i = out[0]
            raise Refusal(T("“{label}” is wholly outside the window along {axis}: the object runs from {lo:.4g} to "
                            "{hi:.4g} nm, the window from {wlo:.4g} to {whi:.4g} nm", label=obj["label"],
                            axis="xyz"[i], lo=float(lo[i]), hi=float(hi[i]), wlo=float(wl[i]), whi=float(wh[i])),
                          hint=T("put it inside the window"))
        part = [i for i in range(self.ndim) if (lo[i] < wl[i] and np.isfinite(lo[i])) or (hi[i] > wh[i] and np.isfinite(hi[i]))]
        if part and not self._loading:
            self.emit({"type": "event", "kind": "scene", "t": self.t, "notify": True,
                       "text": T("“{label}” is partly beyond the window's edge along {axis}: beyond the edge it does "
                                 "not act (the window runs from {lo:.4g} to {hi:.4g} nm)", label=obj["label"],
                                 axis="xyz"[part[0]], lo=float(wl[part[0]]), hi=float(wh[part[0]]))})

    def _refusal(self, obj, e):
        """The engine's refusal of an object in the owner's terms (review UX-ui U13)."""
        text = str(e)
        if _is(e, RESOLUTION):
            return Refusal(T("with “{label}” the grid (step {d:.3g} nm) does not resolve the particle's wave: next to "
                             "it the wave's wavenumbers go beyond 2/3 of the grid's band", label=obj["label"], d=self.d),
                           detail=text,
                           hint=T("a lower potential or a slower particle (a larger λ); or a finer grid: “Grid points "
                                  "per axis” (changes on the fly)"))
        if _is(e, FIELD_WITH_CHARGE):
            return Refusal(T("the field cannot be changed while a charged particle is in the window: the impulse of "
                             "the induced field at the switch depends on how the magnet is built"), detail=text,
                           hint=T("set the field before the particle or remove the particle"))
        return e

    def _packet_refusal(self, obj, pk, e):
        """A packet refused by the engine, said for this scene: where it sits and what is there (review UX-ui U13: a
        packet inside the double slit's wall was refused for a "well −3 eV" that was not in the scene)."""
        text = str(e)
        if not _is(e, PACKET_GRID):
            return e
        g = self.qs.grid
        sig = np.asarray(pk.sigma, float)
        kn = math.pi / np.asarray(g.d, float)
        if np.any(np.abs(np.asarray(pk.k, float)) + QS.PACKET_NYQUIST / (2 * sig) > kn):
            kmax = float(np.min(kn - QS.PACKET_NYQUIST / (2 * sig)))
            if kmax > 0:
                return Refusal(T("the particle's wave is finer than the grid (step {d:.3g} nm) resolves: λ must be "
                                 "larger than {lam:.3g} nm", d=self.d, lam=2 * math.pi / kmax), detail=text,
                               hint=T("increase the wavelength λ; or a finer grid: “Grid points per axis” (changes on "
                                      "the fly)"))
            return Refusal(T("the particle's wave is finer than the grid (step {d:.3g} nm) resolves: at this width σ "
                             "no wavelength will do", d=self.d), detail=text,
                           hint=T("increase the wavelength λ or the width σ; or a finer grid: “Grid points per axis” "
                                  "(changes on the fly)"))
        c = self._vec(obj["values"])
        V = self.qs.potential(pk.species)
        ic = tuple(int(np.clip(np.rint((c[a] - g.axes[a][0]) / g.d[a]), 0, g.shape[a] - 1)) for a in range(self.ndim))
        E = float(np.sum(np.asarray(pk.k, float) ** 2)) / (2 * pk.species.mass)
        Vc = float(V[ic]) - float(V.min())
        spot = self._free_spot(pk, c)
        hint = (T("put the packet in a free place, e.g. {at} nm", at=_pt(spot)) if spot is not None
                else T("lower the particle's energy (a larger λ) or the potential"))
        if Vc > max(E, 1e-12):
            where = self._what_at(c)
            return Refusal(T("the packet's centre {at} nm is inside {where}: the potential there is {V:.3g} eV at the "
                             "particle's kinetic energy {E:.3g} eV; the grid does not resolve such a wave", at=_pt(c),
                             where=where, V=Vc * EV, E=E * EV), detail=text, hint=hint)
        return Refusal(T("the grid (step {d:.3g} nm) does not resolve this particle's wave next to the scene's "
                         "potentials", d=self.d), detail=text,
                       hint=T("{hint}; or a finer grid: “Grid points per axis” (changes on the fly)", hint=hint))

    def _what_at(self, c):
        """The potential object whose box holds the point c, as a text (“a potential's region” if none)."""
        for oid, (kind, qid) in self.ref.items():
            ob = self.qs.objects.get(qid) if kind == "object" else None
            if isinstance(ob, QS.Shape):
                lo, hi = ob.bbox(self.ndim)
                if all(lo[i] <= c[i] <= hi[i] for i in range(self.ndim)):
                    return T("“{label}”", label=self.objects[oid]["label"])
        return T("a potential's region")

    def _free_spot(self, pk, c0):
        """The nearest point to c0 (the packet's own direction backwards first, then the other directions, in steps of
        its width) where the scene would take the packet (``Scene.particle_reason``: inside the window, the grid holds
        its wave) and its core (2 sigma about the centre) meets no potential higher than its kinetic energy; None if
        there is none (or the packet itself is beyond the grid wherever it is)."""
        g = self.qs.grid
        k = np.asarray(pk.k, float)
        sig = np.asarray(pk.sigma, float)
        if np.any(np.abs(k) + QS.PACKET_NYQUIST / (2 * sig) > math.pi / np.asarray(g.d, float)):
            return None  # its wave is beyond the grid wherever it is placed
        E = float(np.sum(k ** 2)) / (2 * pk.species.mass)
        V = self.qs.potential(pk.species)
        Vmin = float(V.min())
        need = sig * math.sqrt(2 * math.log(1 / QS.PACKET_TAIL))
        lo = np.array([a[0] for a in g.axes]) - 0.5 * np.asarray(g.d) + need
        hi = np.array([a[-1] for a in g.axes]) + 0.5 * np.asarray(g.d) - need
        if np.any(lo >= hi):
            return None
        step = max(float(np.max(sig)), 2 * self.d)
        back = -k / np.linalg.norm(k) if np.linalg.norm(k) > 0 else -np.eye(self.ndim)[0]
        dirs = [back] + [s_ * np.eye(self.ndim)[a] for a in range(self.ndim) for s_ in (-1, 1)]
        if self.ndim == 2:
            dirs += [np.array([sx, sy]) / math.sqrt(2) for sx in (-1, 1) for sy in (-1, 1)]
        c0 = np.asarray(c0, float)
        for q in range(0, 64):
            for u in (dirs if q else dirs[:1]):
                c = c0 + q * step * u
                if np.any(c < lo) or np.any(c > hi):
                    continue
                # the packet's core (2 sigma about its centre) clear of potential above its kinetic energy
                box = tuple(slice(int(np.clip(np.floor((c[a] - 2 * sig[a] - g.axes[a][0]) / g.d[a]), 0, g.shape[a] - 1)),
                                  int(np.clip(np.ceil((c[a] + 2 * sig[a] - g.axes[a][0]) / g.d[a]), 0, g.shape[a] - 1)) + 1)
                            for a in range(self.ndim))
                if float(np.max(V[box])) - Vmin > max(E, 1e-12):
                    continue
                cand = QS.Packet(pk.species, list(c), list(pk.k), list(pk.sigma), pk.spin)
                if self.qs.particle_reason(cand) is None:
                    return [float(x) for x in c]
        return None

    def place(self, kind, values):
        """A palette object's values before it is added (review UX-ui U4): a clicked point (``position``) as its centre
        or, for a wall, a step or a plane, its position along its axis; a packet that would sit where the scene cannot
        take it (inside a wall, against the window's edge) goes to the nearest point where it can, announced when it
        is added. An object carried from a world of the other dimension is first made the object of this one that means
        the same, or refused (``_carried``)."""
        values = self._carried(kind, dict(values))
        pos = values.get("position")
        if isinstance(pos, (list, tuple)):
            values.pop("position")
            pos = [float(x) for x in pos]
            if kind in ("slit_wall", "step", "plane"):
                ax = int(values.get("axis", "0"))
                values["position"] = pos[ax] if ax < len(pos) else 0.0
            else:
                for i, c in enumerate("xyz"[:self.ndim]):
                    values[c] = pos[i]
        if kind != "packet":
            return values
        full, errors = self.PALETTE["packet"].schema.resolve(None, values)
        if errors:
            return values
        pk = self._packet(full)
        if self.qs.particle_reason(pk) is None:
            return full
        c0 = self._vec(full)
        spot = self._free_spot(pk, c0)
        if spot is None:
            return full  # refused when added, with the reason (_packet_refusal)
        full.update({c: spot[i] for i, c in enumerate("xyz"[:self.ndim])})
        self._placed_note = (tuple(spot), T("the scene does not take the packet at {at} nm ({where} or the window's "
                                            "edge): it was put at the nearest free place {spot} nm", at=_pt(c0),
                                            where=self._what_at(c0), spot=_pt(spot)))
        return full

    def _cnote(self, text, obj=None, restarted=False):
        """A note of a carry-over: the framework's ``carry_note`` (one notice says what went how: review LB1-F5), or,
        with a framework without it, this world's own notice (``after_header``)."""
        if hasattr(PlaygroundSimulation, "carry_note"):
            self.carry_note(text, obj, restarted=restarted)
        else:
            self._carry_notes.append(text)

    def _carry_src(self):
        """The dimension of the world a scene is being carried from ("2d" | "3d"), or None outside a carry."""
        laws = getattr(self, "carrying", None)
        if laws is None:
            sc = self.params.get("scene") if isinstance(self.params.get("scene"), dict) else {}
            laws = (sc.get("laws") or {}) if sc.get("carry") and self._loading else None
        src = (laws or {}).get("dim")
        return src if src in ("2d", "3d") else None

    def _carried(self, kind, values):
        """An object of a world of the other dimension carried over (plan P16.1: "New world" with "carry the scene"):
        a plane's set-up is the section z = 0 of a set-up that does not change along z, so into space its objects go as
        that: boxes, detectors, markers and regions unbounded along z (sz = 0), a disk as a cylinder along z, walls,
        steps and flux planes across x or y as they are (unbounded along z), a flux tube along z, a trap of the same
        quantum (it separates by axes: the motion in the plane is the same), a packet with sz = sy at z = 0 moving in the
        plane (its wave is not carried: a fresh packet, said in ``on_add``). Out of space into a plane only what crosses
        the plane z = 0, as its section there (and from then on unchanged along z: the plane's approximation): a box or
        a region bounded in z that holds z = 0, a sphere as the disk of its section, a cylinder along z as it is; a
        packet moving in the plane (phi = 0) with its centre within 2 sigma_z of it. Refused with the reason: what does
        not cross the plane, a wall, a step or a flux plane across z, a packet moving out of the plane. Each adaptation
        is said (``carry_note``) and only for an object that was carried (review LB1-p02-ux Q4: the parameter z was set
        on walls, steps and flux planes, which have none, and the notes came before the add was tried)."""
        src = self._carry_src()
        if src is None or src == self.params["dim"]:
            return values
        v = dict(values)
        if self.ndim == 3:
            own = self.PALETTE[kind].schema.by_id
            if "z" in own:
                v.setdefault("z", 0.0)
            if kind in ("box", "detector", "marker") or (kind in ("env", "bfield") and v.get("region", "box") == "box"):
                v.setdefault("sz", 0.0)
                self._cnote(T("unbounded along z (its section z = 0 is the former plane figure)"))
            elif kind == "ball":
                v.setdefault("shape", "cylinder")
                self._cnote(T("the plane's disc becomes a cylinder along z"))
            elif kind in ("slit_wall", "step", "plane"):
                self._cnote(T("unbounded along z (the slits are cuts along z)") if kind == "slit_wall"
                            else T("unbounded along z"))
            elif kind == "flux":
                self._cnote(T("the tube runs along z"))
            elif kind == "trap":
                self._cnote(T("in a volume it also holds along z (the motion in the x, y plane is the same: the trap "
                              "potential is separable in x, y, z)"))
            elif kind == "packet":
                v.setdefault("sz", float(v.get("sy", 3.0)))
                v.setdefault("phi", 0.0)
                v.setdefault("vz", 0.0)
                self._cnote(T("width along z σz = {sz:.4g} nm (a plane's wave has none)", sz=float(v["sz"])))
            return v
        z = float(v.pop("z", 0.0) or 0.0)
        sz = float(v.pop("sz", 0.0) or 0.0)
        phi = float(v.pop("phi", 0.0) or 0.0)
        v.pop("vz", None)
        shape = v.pop("shape", "sphere")
        if kind in ("slit_wall", "step", "plane") and str(v.get("axis")) == "2":
            raise Refusal(T("it stands across the z axis: the (x, y) plane has no such thing"),
                          hint=T("put it across x or y"))
        if kind in ("box", "detector", "marker") or (kind in ("env", "bfield") and v.get("region") == "box"):
            if sz > 0 and abs(z) > 0.5 * sz:
                raise Refusal(T("it does not cross the plane z = 0 (along z from {lo:.4g} to {hi:.4g} nm)",
                                lo=z - sz / 2, hi=z + sz / 2),
                              hint=T("move it to z = 0 in the previous world"))
            if sz > 0:
                self._cnote(T("the section z = 0; in the plane unbounded along z (it was {sz:.4g} nm)", sz=sz))
        elif kind == "ball":
            if shape == "sphere":
                R = float(v.get("radius", 3.0))
                if abs(z) >= R:
                    raise Refusal(T("the ball does not cross the plane z = 0 (centre z = {z:.4g} nm, radius {R:.4g} "
                                    "nm)", z=z, R=R),
                                  hint=T("move it to z = 0 in the previous world"))
                v["radius"] = math.sqrt(R * R - z * z)
                self._cnote(T("the ball's section by the plane z = 0 is a disc of radius {R:.4g} nm (in the plane, a "
                              "cylinder along z)", R=float(v["radius"])))
        elif kind == "packet":
            if abs(phi) > 1e-9:
                raise Refusal(T("it moves out of the (x, y) plane: inclination φ = {phi:.4g}°", phi=phi),
                              hint=T("φ = 0 in the previous world"))
            if abs(z) > 2 * max(sz, 1e-12):
                raise Refusal(T("the packet's centre is off the plane z = 0 (z = {z:.4g} nm at σz = {sz:.4g} nm)",
                                z=z, sz=sz),
                              hint=T("the centre closer to z = 0 in the previous world"))
        elif kind == "trap" and abs(z) > 0:
            self._cnote(T("centre z = {z:.4g} nm dropped: the world is a plane", z=z))
        return v

    def after_header(self):
        super().after_header()
        if self._carry_notes:  # only with a framework that has no ``carry_note`` (its notice says it otherwise)
            self.emit({"type": "notice", "t": self.t,
                       "text": T("Carried over, with changes, from a world with the other space: {notes}",
                                 notes=join(self._carry_notes, "; "))})
            self._carry_notes = []

    # --- the carry-over's state (review LB1-F5; the framework's hooks of 2026-11-11) ----------------------------------
    def _key_out(self, key):
        """An absorbed record's key as a carried state names it: a detector by its scene object's id (kept by the
        carry), the rest as they are."""
        if isinstance(key, str) and key.startswith("detector "):
            q = int(key.split()[1])
            oid = next((o for o, (k, qq) in self.ref.items() if k == "object" and qq == q), None)
            return f"obj:{oid}" if oid else "carried"
        return key

    def _key_in(self, key):
        """A carried key in this world: the same detector if it was carried, else "in the earlier world"."""
        if isinstance(key, str) and key.startswith("obj:"):
            r = self.ref.get(key[4:])
            if r and r[0] == "object" and isinstance(self.qs.objects.get(r[1]), QS.Detector):
                return f"detector {r[1]}"
            return "carried"
        if key == "edges" and not self.open:
            return "carried"
        return key if key in ("edges", "regrid", "carried") else "carried"

    def carry_state(self):
        """What a carry-over takes beyond the parameters (review LB1-F5): each particle's wave (the old grid's samples,
        complex), its absorbed records by the scene objects' ids, its spectral model and whether a detector took it;
        the world's random generators and the measured points. Nothing changes."""
        g = self.qs.grid
        objs = {}
        for oid, (kind, qid) in self.ref.items():
            if kind != "particle":
                continue
            p = self.qs.particles[qid]
            st = {"ndim": self.ndim, "shape": [int(n) for n in g.shape], "d": [float(x) for x in g.d],
                  "active": bool(p.active and p.psi is not None),
                  "absorbed": {self._key_out(k): float(v) for k, v in self.qs.absorbed(qid).items()},
                  "detected": self._key_out(p.detected) if p.detected else None,
                  "edges_width": float(self.edge_w) if self.open else None, "sk_extra2": float(p.sk_extra2)}
            if p.kspec is not None:
                st["kspec"] = [[float(x) for x in p.kspec[0]], [float(x) for x in p.kspec[1]]]
            if st["active"]:
                st["psi"] = np.array(self.qs.wave(qid), complex)
            objs[oid] = st
        return {"objects": objs, "world": {"ndim": self.ndim, "rng": self.rng.bit_generator.state,
                                           "qs_rng": self.qs.rng.bit_generator.state,
                                           "marks": [[float(c) for c in m] for m in self.marks]}}

    def _carry_packet(self, obj, state):
        """``on_add`` of a carried packet: a wave of this dimension waits for ``carry_world`` (the detectors its records
        name are added by then); a packet from the other dimension, or one without a state, was prepared afresh."""
        if getattr(self, "carrying", None) is None:
            return
        if isinstance(state, dict) and state.get("ndim") == self.ndim and ("psi" in state or not state.get("active")):
            self._carry_waves[obj["id"]] = state
        else:
            self._cnote(T("the wave was prepared afresh from the parameters: another dimension")
                        if isinstance(state, dict) and state.get("ndim") != self.ndim
                        else T("the wave was prepared afresh from the parameters: the previous world gave no state of "
                               "it"), obj, restarted=True)

    def carry_world(self, state, laws):
        """After the carried objects (review LB1-F5): the random generators and the measured points of the previous
        world (same dimension), then each carried wave adopted (``Scene.adopt_wave``: resampled exactly to this grid,
        refused as a live change of the grid is — then a fresh packet, said), with its absorbed records (a detector that
        was not carried: "in the previous world"); Bohm points drawn again from the wave."""
        if isinstance(state, dict) and state.get("ndim") == self.ndim:
            try:
                self.rng.bit_generator.state = state["rng"]
                self.qs.rng.bit_generator.state = state["qs_rng"]
            except (KeyError, TypeError, ValueError):
                self._cnote(T("random outcomes (measurements, the environment's jumps, Bohm points): a new generator "
                              "of this world"), restarted=True)
            self.marks = [list(m) for m in state.get("marks") or []]
            if self.marks:
                self._emit_marks()
        elif state is not None:
            self._cnote(T("random outcomes (measurements, the environment's jumps, Bohm points): a new generator of "
                          "this world: another dimension; the marked outcomes of measurements were not carried over"),
                        restarted=True)
        waves, self._carry_waves = self._carry_waves, {}
        for oid, st in waves.items():
            obj = self.objects.get(oid)
            if obj is None or oid not in self.ref:
                continue
            qid = self.ref[oid][1]
            banked = {}
            for k, val in (st.get("absorbed") or {}).items():
                kk = self._key_in(k)
                banked[kk] = banked.get(kk, 0.0) + float(val)
            ew = st.get("edges_width")
            ks = st.get("kspec")
            try:
                rep = self.qs.adopt_wave(qid, st.get("psi"), st["shape"], st["d"], banked,
                                         kspec=None if ks is None else (np.array(ks[0]), np.array(ks[1])),
                                         sk_extra2=float(st.get("sk_extra2") or 0.0),
                                         old_edges=None if ew is None else QS.EdgeLayers(width=float(ew), strength=1.0),
                                         active=bool(st.get("active")),
                                         detected=self._key_in(st["detected"]) if st.get("detected") else None)
            except ValueError as e:
                self._cnote(T("the wave was prepared afresh from the parameters: this grid cannot carry it: {why}",
                              why=text_of(e)), obj, restarted=True)
                continue
            if not st.get("active"):
                self.bohm.pop(oid, None)
                self._cnote(T("the particle had been registered by a detector, and so it stays"), obj)
                continue
            if list(st["shape"]) != list(self.qs.grid.shape) or not np.allclose(st["d"], self.qs.grid.d):
                self._cnote(T("the wave resampled exactly onto this world's grid (step {d0:.4g} → {d1:.4g} nm; "
                              "{drop:.2g} dropped)", d0=float(st["d"][0]), d1=self.d,
                              drop=max(float(rep["dropped"]), 0.0)), obj)
            if "carried" in banked:
                self._cnote(T("what was absorbed in the previous world ({p:.3g}) is a separate line of the balance",
                              p=float(banked["carried"])), obj)
            if obj["values"].get("bohm"):
                self._seed_bohm(obj)
                self._cnote(T("Bohm particles drawn again from |ψ|²"), obj)
            self._set_vmax(obj)
        self._tune()

    def palette_state(self):
        """The palette types the world cannot take now with their defaults, and why (review UX-ui U7). A uniform field
        while a charged particle is in the window: always (cheap). The rest by the engine's own test on the default
        object (``Scene.addition_reason``, nothing changed), in a plane only (in space one test costs ~0.1 s, too much
        after every change), once per revision of the scene."""
        out = {}
        charged = [p for p in self.qs.particles.values() if p.active and p.species.charge != 0]
        if any(self.qs.norm(p.id) > 1e-12 for p in charged):
            out["bfield"] = T("while a charged particle is in the window, a field cannot be added: set the field "
                              "before the particle or remove it")
        if self.ndim != 2:
            return out
        key = (self.rev, self.open, tuple(sorted(self.qs.particles)), float(self.qs.dt))
        if self._ps_key != key:
            got = {}
            for typ, ot in self.PALETTE.items():
                if typ in ("packet", "plane", "bfield"):
                    continue
                try:
                    vals = self.place(typ, {})
                    obj = {"type": typ, "values": ot.schema.resolve(None, vals)[0], "label": ot.label}
                    chk = self.qs.addition_check(self._object(obj))
                    why = text_of(chk) if chk is not None else None
                except ValueError as e:
                    chk, why = None, text_of(e)
                if why:
                    got[typ] = (T("with it the grid would not resolve the wave of a particle in the scene (its energy "
                                  "would grow): lower the particle's energy or make the object weaker after adding it; "
                                  "or a finer grid: “Grid points per axis” (on the fly)")
                                if _is(chk, RESOLUTION) else why)
            self._ps_key, self._ps = key, got
        out.update(self._ps)
        return out

    # --- live laws (review UX-ui U12) --------------------------------------------------------------------------
    def live_values(self):
        nk = "n2" if self.ndim == 2 else "n3"
        return {"edges": "open" if self.open else "closed", nk: self.params[nk], "size": self.params["size"]}

    def set_live(self, values):
        """The live laws at the current moment, the world going on: the grid (points per axis) and the window's size
        (``_regrid``: the waves resampled exactly, ``Scene.regrid``) and the window's edges, open (absorbing layers) or
        closed (periodic) (``Scene.set_edges``: what the layers absorbed so far stays absorbed). A grid change and an
        edges change sent together are one change of the engine (both or neither)."""
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise Refusal(join(errors, "; "))
        nk, other = ("n2", "n3") if self.ndim == 2 else ("n3", "n2")
        if new[other] != self.params[other]:
            raise Refusal(T("“Grid points per axis” of a volume does not act in this world: the world is a plane")
                          if other == "n3" else
                          T("“Grid points per axis” of a plane does not act in this world: the world is a volume"),
                          hint=T("another space is a new world (“Space”)"))
        grid = int(new[nk]) != int(self.params[nk]) or float(new["size"]) != float(self.params["size"])
        if grid:
            return self._regrid(int(new[nk]), float(new["size"]), new["edges"] == "open", new)
        if new["edges"] == self.params["edges"]:
            return T("no change")
        want = new["edges"] == "open"
        edges = QS.EdgeLayers(width=self.edge_w, strength=float(self._auto_W())) if want else None
        chk = self._edges_check(edges)
        if chk is not None:
            why = text_of(chk)
            if _is(chk, CLOSED_WITH_CHARGE):
                raise Refusal(T("the window's edges were not changed: a charged particle next to a field is allowed "
                                "only with open edges"), hint=T("remove the particle or the field"), detail=str(why))
            raise Refusal(T("the window's edges were not changed: {why}", why=why), detail=str(why))
        self.qs.set_edges(edges)
        old = self.params["edges"]
        self.params = new
        self.open = want
        self._abs = None
        self._tune()
        if self.bohm and not want:  # points beyond a closed face come in on the other side
            for B in self.bohm.values():
                B["X"] = self._wrap(B["X"])
        self.emit_scene()  # the approximations and the drawn edges follow
        lab = {o[0]: o[1] for o in SCHEMA.by_id["edges"].options}
        return T("Window edges: {old} → {new}", old=lab[old], new=lab[new["edges"]])

    def _regrid(self, n, size, want_open, new_params):
        """The grid of n points per axis over a window of ``size`` nm now, in the same world (plan P16.1): the step
        size/n, the open edges' layers EDGE_FRAC of the window; every wave resampled exactly (``Scene.regrid``), the
        objects unchanged (their edges keep their physical widths: ``auto_edge``), the absorbers and the time step tuned
        again (``_tune``), Bohm points outside a smaller window registered as dropped by it. Refused with the measured
        numbers (``_regrid_refusal``) and nothing changed where the engine refuses; the memory is asked first
        (``lfviz.limits.require``). Emits the new box and grid, the scene and the wave at once; returns the event's
        text: the route of the resampling, per particle the norm before and after (what was dropped) and the energy
        change, the time step and the edges."""
        nd = self.ndim
        nk = "n2" if nd == 2 else "n3"
        old_n, old_size, old_d, old_dt = self.qs.grid.shape[0], self.size, self.d, self.qs.dt
        d = size / n
        est = self.estimate_bytes({**self.params, nk: str(n), "dim": self.params["dim"]})
        limits.require(est[0], est[1], est[2])
        edge_w = EDGE_FRAC[nd] * size
        edges = (QS.EdgeLayers(width=edge_w, strength=float(self.qs.edges.strength if self.qs.edges is not None
                                                                  else self._auto_W())) if want_open else None)
        try:
            rep = self.qs.regrid([n] * nd, d, edges=edges)
        except ValueError as e:
            raise self._regrid_refusal(e, n, size) from None
        old_edges = self.params["edges"]
        self.params = {**new_params, "edges": "open" if want_open else "closed"}
        self.size, self.d, self.edge_w, self.open = size, d, edge_w, want_open
        self._abs, self._detR, self._ps_key = None, {}, None
        for o in self.objects.values():
            if o["type"] == "packet":
                self._set_vmax(o)
        self._tune()
        cut = 0
        if self.bohm:  # points outside a smaller window: their probability was dropped (banked as "regrid")
            wl, wh = self._window()
            for B in self.bohm.values():
                for Xk, fk, kk in (("X", "fly", "key"), ("Xc", "flyc", "keyc")):
                    out = np.flatnonzero(B[fk] & np.any((B[Xk] < np.array(wl)) | (B[Xk] >= np.array(wh)), axis=1))
                    for j in out:
                        B[fk][j] = False
                        B[kk][j] = "regrid"
                    cut += len(out) if Xk == "X" else 0
                if not self.open:
                    B["X"], B["Xc"] = self._wrap(B["X"]), self._wrap(B["Xc"])
        self.emit_grid()
        self.emit_scene()
        self.emit_wave()
        same_window = abs(n * d - old_n * old_d) <= 1e-12 * size
        same_step = abs(d - old_d) <= 1e-12 * d
        route = (T("by padding the spectrum with zeros") if same_window and n > old_n else
                 T("by dropping the spectrum beyond the new band") if same_window else
                 (T("by the same samples, padded with zeros") if n > old_n
                  else T("by the same samples inside the new window")) if same_step else
                 T("by the values of its interpolant (the grid's band) at the new points, zeros beyond the former "
                   "window") if size > old_size else
                 T("by the values of its interpolant (the grid's band) at the new points"))
        waves = [pid for kind, pid in self.ref.values() if kind == "particle" and pid in rep["particles"]]
        if waves:
            parts = [T("Grid: {n0:d} → {n1:d} points per axis, step {d0:.4g} → {d1:.4g} nm, window {s0:.4g} → {s1:.4g} "
                       "nm: the wave resampled exactly ({route})", n0=int(old_n), n1=int(n), d0=old_d, d1=d,
                       s0=old_size, s1=size, route=route)]
        else:
            parts = [T("Grid: {n0:d} → {n1:d} points per axis, step {d0:.4g} → {d1:.4g} nm, window {s0:.4g} → {s1:.4g} "
                       "nm (no waves in the window)", n0=int(old_n), n1=int(n), d0=old_d, d1=d, s0=old_size, s1=size)]
        for oid, (kind, pid) in self.ref.items():
            r = rep["particles"].get(pid) if kind == "particle" else None
            if not r:
                continue
            dE = (r["E_after"] - r["E_before"]) * EV if r["E_before"] is not None and r["E_after"] is not None else None
            dn = r["norm_after"] - r["norm_before"]
            drop = (T("unchanged to within round-off") if abs(dn) <= 64 * np.finfo(float).eps else
                    T("{p:.2g} dropped", p=-dn) if dn < 0 else T("larger by {p:.2g} from the new grid's quadrature", p=dn))
            part = T("“{label}”: probability in the window {p0:.7g} → {p1:.7g} ({drop}), energy ⟨H⟩ {e0:.6g} → "
                     "{e1:.6g} eV", label=self.objects[oid]["label"], p0=float(r["norm_before"]),
                     p1=float(r["norm_after"]), drop=drop, e0=r["E_before"] * EV, e1=r["E_after"] * EV)
            if dE is not None:
                part = T("{text} (ΔE = {dE:.2g} eV)", text=part, dE=dE)
            # the absorbing layers moved with the window (review LB1-p02-ux Q6)
            if r.get("in_layers", 0.0) > 1e-9 and size > old_size:
                part = T("{text}; the former absorbing layers held {p:.2g} of its probability: this part, already "
                         "weakened by the layers, is now inside the window", text=part, p=float(r["in_layers"]))
            if r.get("in_new_layers", 0.0) > 1e-9:
                if r.get("exposed", 0.0) > 1e-12:
                    part = T("{text}; in the new absorbing layers: {p:.2g} of its probability (the edges will absorb "
                             "it; {q:.2g} of it outside the former layers)", text=part, p=float(r["in_new_layers"]),
                             q=float(r["exposed"]))
                else:
                    part = T("{text}; in the new absorbing layers: {p:.2g} of its probability (the edges will absorb "
                             "it)", text=part, p=float(r["in_new_layers"]))
            parts.append(part)
        parts.append(T("time step {t0:.4g} → {t1:.4g} fs", t0=old_dt / FS, t1=self.qs.dt / FS))
        if self.open:
            parts.append(T("window edges: absorbing layers {w:.4g} nm, W₀ = {W:.4g} eV (opened)", w=edge_w,
                           W=self.qs.edges.strength * EV) if old_edges != "open" else
                         T("window edges: absorbing layers {w:.4g} nm, W₀ = {W:.4g} eV", w=edge_w,
                           W=self.qs.edges.strength * EV))
        elif old_edges == "open":
            parts.append(T("window edges closed (periodic)"))
        if cut:
            parts.append(T("Bohm points beyond the new window: {n:d} (dropped with the probability the window cut "
                           "off)", n=int(cut)))
        return join(parts, "; ")

    def _regrid_refusal(self, e, n, size):
        """The engine's refusal of a new grid in the owner's terms: which particle, object or plane, the measured
        fraction against the tolerance, and what to change."""
        tol = QS.REGRID_TOL
        what = getattr(e, "what", None)
        head = T("Grid not changed ({n:d} points per axis, window {size:.4g} nm)", n=int(n), size=size)
        lab = None
        if getattr(e, "pid", None) is not None:
            lab = next((self.objects[o]["label"] for o, (k, q) in self.ref.items() if k == "particle" and q == e.pid), None)
        coarsen = T("coarsen when the wave is slower (a larger λ) or wider; or keep the grid finer")
        if what == "spectrum":
            return Refusal(T("{head}: {p:.3g} of the norm of the wave “{label}” lies beyond the new grid's band, more "
                             "than the tolerance {tol:.4g}: coarsening would drop it", head=head, p=float(e.value),
                             label=lab, tol=tol), detail=str(e), hint=coarsen)
        if what == "outside":
            return Refusal(T("{head}: {p:.3g} of the probability of “{label}” lies outside the new window, more than the "
                             "tolerance {tol:.4g}: shrinking the window would drop it", head=head, p=float(e.value),
                             label=lab, tol=tol), detail=str(e),
                           hint=T("shrink the window less, or once the wave has left the part cut off (the edges or the "
                                  "detectors will absorb it)"))
        if what == "layers":
            return Refusal(T("{head}: {p:.3g} of the probability of “{label}”, now outside the layers, would lie under "
                             "the new window's absorbing layers, more than the tolerance {tol:.4g}: the edges' layers "
                             "(10 % of the window) would move onto the wave and absorb it", head=head,
                             p=float(e.value), label=lab, tol=tol), detail=str(e),
                           hint=T("shrink the window once the wave has moved away from the edges, or less; or close the "
                                  "edges"))
        if what == "resolution":
            lab = next((self.objects[o]["label"] for o, (k, q) in self.ref.items() if k == "particle" and q == e.pid),
                       T("(unnamed particle)"))
            if getattr(e, "inter", True):
                if e.conv:
                    text = T("{head}: the new grid (step {d:.4g} nm) does not resolve the wave “{label}” next to what "
                             "acts on it: its wavenumbers reach {K:.3g} nm⁻¹ (with the energy the potential can turn "
                             "into motion), while next to a potential or a field the grid resolves ≤ {lim:.3g} nm⁻¹ "
                             "(⅔·π/step)", head=head, d=size / n, label=lab, K=float(e.K), lim=float(e.lim))
                else:
                    text = T("{head}: the new grid (step {d:.4g} nm) does not resolve the wave “{label}” next to what "
                             "acts on it: its wavenumbers reach {K:.3g} nm⁻¹, while next to a potential or a field the "
                             "grid resolves ≤ {lim:.3g} nm⁻¹ (⅔·π/step)", head=head, d=size / n, label=lab,
                             K=float(e.K), lim=float(e.lim))
                return Refusal(text, detail=str(e), hint=T("keep the grid finer or lower the particle's energy"))
            return Refusal(T("{head}: the wave “{label}” is finer than the new grid (step {d:.4g} nm) resolves: its "
                             "wavenumbers |k| + 6σ_k reach {K:.3g} nm⁻¹ at π/step = {lim:.3g} nm⁻¹", head=head,
                             label=lab, d=size / n, K=float(e.K), lim=float(e.lim)), detail=str(e), hint=coarsen)
        if what == "face":
            return Refusal(T("{head}: {p:.3g} of the probability of “{label}” lies at the window's faces, more than the "
                             "tolerance {tol:.4g}: the grid is periodic, this part of the wave continues on the other "
                             "side of the window, and in a larger window its continuation would be cut off", head=head,
                             p=float(e.value), label=lab, tol=tol), detail=str(e),
                           hint=T("enlarge the window once the wave has moved away from the faces (with open edges the "
                                  "layers will absorb it)"))
        if getattr(e, "oid", None) is not None:
            ko = next((k for k, (kd, q) in self.ref.items() if kd == "object" and q == e.oid), None)
            o = self.objects[ko]["label"] if ko else "?"
            auto = ko in self.auto_edge
            why = text_of(e)
            if is_t(why) and "reason" in (why.get("a") or {}):  # the engine's "object #n on the new grid: <reason>"
                why = why["a"]["reason"]
            if auto:
                return Refusal(T("{head}: the new grid does not carry “{label}”: {why} (its “Edge width” is 0, frozen "
                                 "at the {w:.3g} nm it was added with)", head=head, label=o, why=why,
                                 w=float(self.auto_edge[ko])), detail=str(e),
                               hint=T("the action “Coarsen the grid with edges to match” widens such edges of all the "
                                      "objects at once (the potential changes); or set the edge's width yourself, or "
                                      "keep the grid finer"))
            return Refusal(T("{head}: the new grid does not carry “{label}”: {why}", head=head, label=o, why=why),
                           detail=str(e),
                           hint=T("give the object a wider edge (or a greater length) or keep the grid finer"))
        if getattr(e, "plane", None) is not None:
            o = next((self.objects[k]["label"] for k, (kd, q) in self.ref.items() if kd == "plane" and q == e.plane), "?")
            return Refusal(T("{head}: “{label}” would be outside the new window or at its edge", head=head, label=o),
                           detail=str(e), hint=T("move the flux plane inside the new window or remove it"))
        return Refusal(T("{head}: {why}", head=head, why=text_of(e)), detail=str(e))

    def emit_grid(self):
        """The grid in force (``header``'s ``grid``) and the scene's box, after a live change: the view's axes, the
        picture's plane and the 3-D region follow."""
        grid, box = self._grid_info()
        self._regridded = True
        self.emit({"type": "grid", "t": self.t, "grid": grid})
        self.emit({"type": "box", "t": self.t, "box": box})

    def _grid_info(self):
        g = self.qs.grid
        lo = [float(a[0]) for a in g.axes] + [0.0] * (3 - self.ndim)
        hi = [float(a[-1]) for a in g.axes] + [0.0] * (3 - self.ndim)
        if self.ndim == 2:
            lo[2], hi[2] = -0.08 * self.size, 0.08 * self.size
        grid = {"ndim": self.ndim, "n": list(g.shape), "h": float(g.d[0]), "size": self.size,
                "x": [lo[0], hi[0]], "y": [lo[1], hi[1]], "z": [lo[2], hi[2]], "open": self.open,
                "edge_width": self.edge_w if self.open else 0.0}
        return grid, [lo, hi]

    @classmethod
    def estimate_bytes(cls, params):
        """The memory a world of these parameters can reach (the framework refuses it beforehand when over its budget):
        per grid point the scene's arrays (~12 doubles) and, for each of up to 6 particles, its wave (a spinor:
        2 complex), the absorbed record, three snapshots for Bohm points and its split operator (~2 complex)."""
        ndim = 2 if params.get("dim", "2d") == "2d" else 3
        n = int(params.get("n2" if ndim == 2 else "n3", 256 if ndim == 2 else 64))
        pts = n ** ndim
        # + the objects' arrays the scene keeps between changes (QS.OBJ_CACHE_DOUBLES per point)
        per_point = (12 + QS.OBJ_CACHE_DOUBLES) * 8 + 6 * (2 * 16 + 8 + 3 * 32 + 2 * 16)
        return (pts * per_point,
                T("grid {n:d}² = {pts:d} points and up to 6 particles", n=n, pts=pts) if ndim == 2 else
                T("grid {n:d}³ = {pts:d} points and up to 6 particles", n=n, pts=pts),
                T("reduce the number of grid points per axis"))

    def object_state(self, obj):
        # the wave is not kept in a scene file (a 2-D wave is megabytes): a particle starts again as its packet
        return None

    def _tune(self):
        self._abs = None
        self._prof = {}
        self._detR = {}
        self._tune_dt()

    def _dt_target(self, rates=None):
        """The time step for the fastest relevant energy (a power of two, so small changes keep it) within the
        environments' bound lambda dt <= LOC_MAX_STEP (``rates``: the environments' rates; default those in the scene).
        The largest kinetic energy a wave reaches: (|k| + 3 sigma_k)^2 / 2m per axis (sigma_k widened by measurements
        and jumps: ``Scene.k_spread``) plus the potential energy it can turn into motion (V at the packet's centre, or at
        the wave's centre now, minus the lowest V). Barriers above it are seen only by evanescent tails: not counted
        (the engine's ``suggest_dt`` counts the whole range of V: for the double slit's 3 eV wall 4 times more steps;
        measured 2026-11-03, review B6-Q11: the wave's true error at t = 12 is 2.6e-4 with this step against 1.6e-5 with
        that one, and 6.0e-4 and 1.1e-3 when the wall is raised to 30 and 300 eV); the companion's estimate of the
        step's error is in the checks. Without particles: the current step."""
        qs = self.qs
        g = qs.grid
        live = [p for p in qs.particles.values() if p.active and p.psi is not None]
        if live:
            E = 0.0
            for p in live:
                V = qs.potential(p.species)
                ic = tuple(int(np.clip(np.rint((c - g.axes[a][0]) / g.d[a]), 0, g.shape[a] - 1))
                           for a, c in enumerate(p.packet.center))
                k, sk = qs.k_spread(p.id)
                dV = max(0.0, float(V[ic] - V.min()), qs._convertible(p, qs._arr))
                E = max(E, float(np.sum((np.abs(k) + 3 * sk) ** 2)) / (2 * p.species.mass) + dV)
            dt = PHASE_PER_STEP / max(E, 1e-300)
        else:
            dt = qs.dt
        if rates is None:
            rates = [float(ob.rate) for ob in qs.objects.values() if isinstance(ob, QS.Localization)]
        for r in rates:
            dt = min(dt, QS.LOC_MAX_STEP / float(r))
        return 2.0 ** math.floor(math.log2(dt))

    def _dt_with(self, ob, qid=None):
        """The step to hand to the scene together with a new or changed environment (review B6-Q6: the scene refuses
        lambda dt > 0.05, so the step is shortened in the same change, not refused), else None."""
        if not isinstance(ob, QS.Localization):
            return None
        rates = [float(o.rate) for i, o in self.qs.objects.items() if isinstance(o, QS.Localization) and i != qid]
        dt = self._dt_target(rates + [float(ob.rate)])
        return dt if dt < self.qs.dt else None

    def _tune_dt(self):
        """After every change: the time step (``_dt_target``), the open edges' strength for the particles' energies,
        the detectors' with an automatic strength."""
        qs = self.qs
        dt = self._dt_target()
        if dt != qs.dt:
            qs.set_dt(dt)
        if not qs.particles:
            return
        if self.open:
            W = self._auto_W()
            if not 0.7 <= W / float(qs.edges.strength) <= 1.4:
                qs.set_edges(QS.EdgeLayers(width=self.edge_w, strength=W))
        # detectors with an automatic strength follow the particles too (their own reflection is in the checks)
        for oid, (kind, qid) in self.ref.items():
            o = self.objects.get(oid)
            ob = qs.objects.get(qid) if kind == "object" else None
            if o and o["type"] == "detector" and float(o["values"]["W"]) <= 0 and isinstance(ob, QS.Detector):
                W = self._auto_W(ob)
                if not 0.7 <= W / float(ob.strength) <= 1.4:
                    qs.update(qid, strength=W)

    def _default_speed(self):
        v = [float(np.linalg.norm(p.packet.k)) / p.species.mass for p in self.qs.particles.values()]
        v = max(v) if v and max(v) > 0 else 0.0
        # the fastest particle crosses a tenth of the window per second; at rest: 2.5 units of time per second
        return (0.1 * self.size / v if v > 0 else 2.5) * TU

    # --- Bohm points ---------------------------------------------------------------------------------------------
    def _seed_bohm(self, obj):
        """A fresh ensemble of Bohm points for the particle (at its creation, a change of its packet or of the number
        of points, a position measurement — whose outcome conditions on "not absorbed", so the absorptions so far are
        dropped): n points |psi|^2-distributed (``_draw``), each with its absorption clock (``_clock``); the first
        CONTROL_N of them also as the control (the same clocks); the ensemble's first epoch.
        Ensemble: n, X (n, ndim: where each point is, or where it was absorbed), fly (not absorbed), key (the absorber
        that took it), E and S (its exponential threshold and the hazard accumulated), the control Xc, flyc, keyc, Sc,
        the control's largest deviation dmax and its fates that differed, the epochs (draws) with the absorbed
        probabilities at their start."""
        n = int(obj["values"].get("bohm", 0) or 0)
        kind, pid = self.ref[obj["id"]]
        if n <= 0 or not self.qs.particles[pid].active or self.qs.norm(pid) <= 0:
            self.bohm.pop(obj["id"], None)
            return
        X = self._draw(pid, n)
        C = min(CONTROL_N, n)
        E, U = self._clock(n)
        self.bohm[obj["id"]] = {
            "n": n, "X": X, "fly": np.ones(n, bool), "key": [None] * n, "E": E, "U": U, "S": np.zeros(n),
            "Xc": X[:C].copy(), "flyc": np.ones(C, bool), "keyc": [None] * C, "Sc": np.zeros(C),
            "dmax": 0.0, "fate": 0,
            "epochs": [{"m": n, "N": self.qs.norm(pid), "A": dict(self.qs.absorbed(pid)), "end": None}]}

    def _draw(self, pid, n):
        """n points |psi|^2-distributed (a cell drawn with its probability, a uniform position inside it)."""
        g = self.qs.grid
        w = self.qs.density(pid).ravel()
        tot = float(w.sum())
        if not (math.isfinite(tot) and tot > 0.0):  # review UX-params P29: numpy's "Probabilities contain NaN"
            raise Refusal(T("there is nothing to draw Bohm particles from: the particle has no wave in the window (it "
                            "was absorbed or has left)") if math.isfinite(tot) else
                          T("the particle's wave is no longer finite: Bohm particles cannot be seeded; prepare the "
                            "packet anew"))
        idx = self.rng.choice(w.size, size=n, p=w / tot)
        ii = np.unravel_index(idx, g.shape)
        return np.stack([g.axes[a][ii[a]] + (self.rng.random(n) - 0.5) * g.d[a] for a in range(self.ndim)], axis=1)

    def _clock(self, n):
        """Each point's absorption threshold E ~ Exp(1) (it is absorbed when its accumulated hazard int 2 W dt reaches
        E) and the uniform U that picks the absorber; from the run's seeded generator."""
        return -np.log(1.0 - self.rng.random(n)), self.rng.random(n)

    def _redraw_flight(self, oid):
        """A localization jump broke the interval (review B6-Q5): the jump acts on the in-flight branch, so the absorbed
        probabilities stand and so do the points already absorbed; the points not absorbed are drawn again from the
        wave now, their number unchanged, with new clocks. The epoch closes, a new one opens; a control pair whose fates
        differ at this moment is counted, then the control follows its points again."""
        B = self.bohm[oid]
        pid = self.ref[oid][1]
        A = dict(self.qs.absorbed(pid))
        B["epochs"][-1]["end"] = A
        C = len(B["Xc"])
        B["fate"] += sum(1 for j in range(C) if B["flyc"][j] != B["fly"][j] or B["keyc"][j] != B["key"][j])
        fl = np.flatnonzero(B["fly"])
        if len(fl) and self.qs.norm(pid) > 0:
            B["X"][fl] = self._draw(pid, len(fl))
            B["E"][fl], B["U"][fl] = self._clock(len(fl))
            B["S"][fl] = 0.0
            B["epochs"].append({"m": int(len(fl)), "N": self.qs.norm(pid), "A": A, "end": None})
        B["Xc"], B["flyc"], B["keyc"] = B["X"][:C].copy(), B["fly"][:C].copy(), list(B["key"][:C])
        B["Sc"] = B["S"][:C].copy()

    def _absorbers(self):
        """The absorbing parts (detectors, the open edges) on the grid, as the engine builds them (``_absorb``)."""
        if self._abs is None:
            g, parts = self.qs.grid, {}
            for oid, (kind, qid) in self.ref.items():
                ob = self.qs.objects.get(qid) if kind == "object" else None
                if isinstance(ob, QS.Detector):
                    parts[f"detector {qid}"] = ob.W(g)
            if self.qs.edges is not None:
                parts["edges"] = self.qs.edges.W(g)
            self._abs = parts
        return self._abs

    def _W_at(self, X):
        """Each absorber's W at points X (the nearest sample), (keys, (K, N) array); points outside the grid of an open
        window get an infinite W from the edges (they have left through them)."""
        g = self.qs.grid
        lo = np.array([a[0] for a in g.axes])
        u = (X - lo) / np.asarray(g.d)
        out_ = np.any((u < -0.5) | (u > np.array(g.shape) - 0.5), axis=1)
        ii = tuple(np.clip(np.rint(u[:, a]).astype(int), 0, g.shape[a] - 1) for a in range(self.ndim))
        parts = self._absorbers()
        keys = list(parts)
        W = np.array([parts[k][ii] for k in keys]).reshape(len(keys), len(X))
        if self.open and "edges" in parts:
            W[keys.index("edges"), out_] = np.inf
        return keys, W

    def _absorb(self, B, which, idx, X0, X1, h):
        """Absorption of the points ``idx`` over a Bohm interval h (review B6-Q1/Q5): the continuity equation of the
        absorbing wave, d rho/dt + div(rho v) = -2 W rho, is kept by points that move with Bohm's velocity and are
        removed at the rate 2 W (W of the detectors and the open edges at the point): the points not yet absorbed stay
        |psi|^2 / N-distributed and the fraction absorbed by detector k is the probability it absorbs (equivariance with
        absorption). The hazard of the interval h (W(X0) + W(X1)) (trapezoid); a point is absorbed when its accumulated
        hazard passes its threshold E, credited to absorber k with probability W_k / W at the point (the scene's
        attribution; drawn with the point's U); the control uses its points' E and U."""
        if not self._absorbers():
            return
        keys, W0 = self._W_at(X0)
        _, W1 = self._W_at(X1)
        Sk, fk, kk = ("S", "fly", "key") if which == "main" else ("Sc", "flyc", "keyc")
        share = W0 + W1
        B[Sk][idx] += h * np.sum(share, axis=0)
        dead = B[Sk][idx] >= B["E"][idx]
        for j in np.flatnonzero(dead):
            i = idx[j]
            w = share[:, j]
            if np.any(np.isinf(w)):
                k = int(np.flatnonzero(np.isinf(w))[0])
            else:
                c = np.cumsum(w) / w.sum()
                k = int(min(np.searchsorted(c, B["U"][i], side="right"), len(keys) - 1))
            B[fk][i] = False
            B[kk][i] = keys[k]

    def _wrap(self, X):
        """In the closed (periodic) window a point that leaves comes in on the other side."""
        if self.open:
            return X
        g = self.qs.grid
        lo = np.array([a[0] for a in g.axes]) - 0.5 * np.asarray(g.d)
        L = np.array(g.shape) * np.asarray(g.d)
        return lo + np.mod(X - lo, L)

    def _dist(self, X, Y):
        D = X - Y
        if not self.open:
            L = np.array(self.qs.grid.shape) * np.asarray(self.qs.grid.d)
            D = D - L * np.rint(D / L)
        return np.linalg.norm(D, axis=1)

    def _pairs(self, B):
        """The control's pairs in the same state (both in flight, or absorbed by the same absorber): their distances."""
        C = len(B["Xc"])
        same = np.array([B["fly"][j] == B["flyc"][j] and B["key"][j] == B["keyc"][j] for j in range(C)], bool)
        return self._dist(B["X"][:C][same], B["Xc"][same]) if same.any() else np.zeros(0)

    def _bohm_step(self):
        for oid, B in list(self.bohm.items()):
            kind, pid = self.ref[oid]
            p = self.qs.particles.get(pid)
            if p is None or not p.active:
                self.bohm.pop(oid, None)
                continue
            snaps = self.qs.snapshots(pid)
            if snaps is None:  # a jump of the environment in the interval
                self._redraw_flight(oid)
                continue
            grid, H, xp = self.qs.guidance(pid)
            for which in ("main", "control"):  # the ensemble, then its control (order 16, 4x tighter: B6-Q1)
                Xk, fk = ("X", "fly") if which == "main" else ("Xc", "flyc")
                fl = np.flatnonzero(B[fk])
                if not len(fl):
                    continue
                step = float(min(grid.d))
                opts = {} if which == "main" else {"order": CONTROL_ORDER, "rtol": 1e-5 / CONTROL_TIGHT,
                                                   "atol": 1e-6 * step / CONTROL_TIGHT}
                X0 = B[Xk][fl]
                X, _ = bohm.advance_ensemble(grid, snaps[0], X0, snaps[1], H, xp=xp, **opts)
                X = self._wrap(X)
                B[Xk][fl] = X
                self._absorb(B, which, fl, X0, X, snaps[1])
            d = self._pairs(B)
            if len(d):
                B["dmax"] = max(B["dmax"], float(d.max()))

    def _bohm_expected(self, B, pid):
        """Per absorber: (count of points it absorbed, expected count, its variance). A point drawn from |psi|^2 / N at
        an epoch's start is absorbed by k before the epoch's end with probability Delta A_k / N (equivariance with
        absorption: ``_absorb``); the epochs' binomial counts add."""
        now = dict(self.qs.absorbed(pid))
        E, V = {}, {}
        for ep in B["epochs"]:
            end = ep["end"] or now
            for k in set(end) | set(ep["A"]):
                q = min(max((end.get(k, 0.0) - ep["A"].get(k, 0.0)) / ep["N"], 0.0), 1.0) if ep["N"] > 0 else 0.0
                E[k] = E.get(k, 0.0) + ep["m"] * q
                V[k] = V.get(k, 0.0) + ep["m"] * q * (1 - q)
        n = {}
        for key in B["key"]:
            if key is not None:
                n[key] = n.get(key, 0) + 1
        return {k: (n.get(k, 0), E.get(k, 0.0), V.get(k, 0.0)) for k in set(E) | set(n)}

    # --- time ------------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        qs = self.qs
        n = int(math.floor((t_target / TU - qs.t) / qs.dt + 1e-9))
        while n > 0:
            if any(B["fly"].any() or B["flyc"].any() for B in self.bohm.values()):
                if n < 2:
                    break
                k = min(n - n % 2, BOHM_CHUNK)
                qs.advance(k, snapshots=True)
                self._bohm_step()
            else:
                k = n
                qs.advance(k)
            n -= k
        self.t = max(self.t, t_target)

    def max_step(self):
        return MAX_STEPS * self.qs.dt * TU

    # --- frames ----------------------------------------------------------------------------------------------------
    def frame(self):
        qs = self.qs
        R = self._readings()
        ids, now, probes = [], {}, {}
        pos, rgb = [], []
        for oid, (kind, qid) in self.ref.items():
            if kind != "particle":
                continue
            p = qs.particles[qid]
            ids.append(oid)
            o = R[oid]
            nrm = o["norm"]
            ab = o["A"]
            # the inspector's rows (framework: now[id] = {label: value}): the labels are static English msgids (the
            # player translates them); what names an object goes into the value, as a text
            r = {"in the window (probability)": nrm}
            if ab:
                r["absorbed"] = join([T("{where}: {p:.6g}", where=self._det_label(k), p=float(a))
                                      for k, a in sorted(ab.items())], "; ")
            if p.active and nrm > 1e-300 and o["r"] is not None:
                for a, key in zip(range(self.ndim), ("⟨x⟩, nm", "⟨y⟩, nm", "⟨z⟩, nm")):
                    r[key] = o["r"][a]
                r["speed |⟨v⟩|, km/s"] = self._speed_kms(o, p)
                if p.species.spin_half and p.kind != "marker":
                    r["spin ⟨σ⟩"] = _pt([float(c) for c in qs.spin(qid)], 4)
                if p.kind == "marker":
                    m = qs.marker_state(qid)
                    r["marker: ⟨0|ρ|1⟩ (coherence)"] = float(abs(m[0, 1]))
                    r["marker: P(1)"] = float(m[1, 1].real)
            elif not p.active:
                r["state"] = T("registered: {where}", where=self._det_label(p.detected))
            now[oid] = r
        for i, (oid, B) in enumerate(self.bohm.items()):
            c = BOHM_RGB[i % len(BOHM_RGB)]
            for x, f in zip(B["X"], B["fly"]):  # registered: drawn where they stopped, dimmer
                pos.append(list(x) + [0.0] * (3 - self.ndim))
                rgb.append(c if f else [0.45 * v for v in c])
            if oid in now:
                cnt = {}
                for key in B["key"]:
                    if key is not None:
                        cnt[key] = cnt.get(key, 0) + 1
                now[oid]["Bohm: points in flight"] = T("{k:d} of {n:d}", k=int(B["fly"].sum()), n=int(B["n"]))
                if cnt:
                    now[oid]["Bohm: registered"] = join([T("{where}: {k:d} of {n:d}", where=self._det_label(key), k=k,
                                                           n=int(B["n"])) for key, k in sorted(cnt.items())], "; ")
        for oid, (kind, qid) in self.ref.items():
            ob = qs.objects.get(qid) if kind == "object" else None
            if isinstance(ob, QS.Shape) and ob.peak(self.ndim) is not None:
                # a shape narrower than its edges does not reach its nominal height (review B6-Q14)
                now[oid] = {"largest height of the potential, eV": ob.peak(self.ndim) * EV,
                            "height set, eV": float(ob.height) * EV}
        for oid, (kind, qid) in self.ref.items():
            o = self.objects[oid]
            if kind == "plane":
                rows = [T("“{label}”: {v:.6g}", label=self.objects[poid]["label"],
                          v=float(qs.particles[pid].planes[qid]["F"]))
                        for poid, (pk, pid) in self.ref.items() if pk == "particle" and qs.particles[pid].planes.get(qid)]
                probes[oid] = {"flux over time": join(rows, "; ")} if rows else {}
            elif o["type"] == "detector":
                rows = [T("“{label}”: {v:.6g}", label=self.objects[poid]["label"],
                          v=float(R[poid]["A"].get(f"detector {qid}", 0.0)))
                        for poid, (pk, pid) in self.ref.items() if pk == "particle"]
                probes[oid] = {"absorbed from": join(rows, "; ")} if rows else {}
        meas, note = self._measure(R)
        if self.check_due():
            self.checks()
        if self.n_wave % WAVE_EVERY == 0:
            self.emit_wave()
        if self.n_wave % VMAX_EVERY == VMAX_EVERY - 1:
            self._refresh_vmax()
        self.n_wave += 1
        z0 = 0.02 * self.size if self.ndim == 2 else 0.0
        P = np.array(pos, np.float32).reshape(-1, 3)
        if self.ndim == 2 and len(P):
            P[:, 2] = z0
        return ({"ids": ids, "now": now, "probes": probes, "n_bohm": len(P), "steps": int(qs.steps),
                 "dt_fs": qs.dt / FS, "at": self._positions(R), "meas": meas,
                 **({"meas_note": note} if note else {})},
                {"pos": P.reshape(-1), "rad": np.full(len(P), 0.004 * self.size, np.float32),
                 "rgb": np.array(rgb, np.float32).reshape(-1)})

    # --- direct manipulation and instruments (plan P16.2, P16.3) -----------------------------------------------------
    def _readings(self):
        """Each particle's readings now (``Scene.observables``: one FFT per wave), computed once per frame."""
        return {oid: {**self.qs.observables(qid), "A": self.qs.absorbed(qid)}
                for oid, (kind, qid) in self.ref.items() if kind == "particle"}

    def _speed_kms(self, o, p):
        """|<v>| = hbar |<k - qA>| / m in km/s (k in 1/nm, the scene's time unit TU)."""
        return float(np.linalg.norm(o["k"])) / p.species.mass * 1e-9 / TU * 1e-3

    def _positions(self, R):
        """``at``: every positioned object's point (nm; a plane world's z = 0): a packet at the mean position of its
        wave (none once a detector has taken it), a wall, a step and a flux plane at their place on their axis (the
        other coordinates 0), a field or an environment at its region's centre (none when it fills the scene)."""
        at = {}
        for oid, (kind, qid) in self.ref.items():
            o = self.objects[oid]
            t, v = o["type"], o["values"]
            if kind == "particle":
                r = R[oid]
                if r["r"] is not None and r["norm"] > 1e-12:
                    at[oid] = [float(c) for c in r["r"]] + [0.0] * (3 - self.ndim)
            elif t in ("slit_wall", "step", "plane"):
                pt = [0.0, 0.0, 0.0]
                ax = int(v["axis"])
                pt[ax] = float(self.qs.planes[qid]["position"]) if kind == "plane" else float(v["position"])
                at[oid] = pt
            elif t == "flux":
                at[oid] = [float(v["x"]), float(v["y"]), 0.0]
            elif t in ("bfield", "env") and v.get("region", "box") == "all":
                continue
            else:
                at[oid] = self._vec(v) + [0.0] * (3 - self.ndim)
        return at

    def _profile(self, oid):
        """The region's profile (0..1) of a detector or a which-path marker on the grid (kept until the scene changes:
        ``_tune`` clears ``_abs``)."""
        cache = self._prof
        key = oid
        if key not in cache:
            kind, qid = self.ref[oid]
            ob = self.qs.objects[qid]
            if isinstance(ob, QS.Detector):
                cache[key] = ob.W(self.qs.grid) / float(ob.strength)
            else:
                cache[key] = ob.b(self.qs.grid)[1] / float(ob.coupling) if float(ob.coupling) != 0 else \
                    QS.PathMarker(ob.lo, ob.hi, 1.0, ob.edge).b(self.qs.grid)[1]
        return cache[key]

    def measurables(self):
        """The quantities of this world the instruments can record (the integrator's API of 2026-11-11, §2): for the
        world the probability in the window and absorbed, summed over the particles; per particle its probability in
        the window and absorbed, <H>, <r>, <p - qA>/hbar, |<v>|, a spin's <sigma> or a marker's coherence; per flux
        plane the flux now and integrated since the scene's last change; per detector the probability it absorbed and
        the probability in its region now, and the Bohm points it registered; per marker the probability in its
        region. Labels and units as texts (T); values in those units in every frame's ``meas`` (``measure``)."""
        out = []

        def add(id_, label, unit="", of=None, group=None):
            out.append({"id": id_, "label": label, "unit": unit, "of": of,
                        "group": T("World") if group is None else group})
        add("norm", T("Probability in the window (sum over the particles)"))
        add("absorbed", T("Absorbed by the detectors and the edges (sum over the particles)"))
        add("regrid", T("Change of the norm due to a grid or window change: dropped (a minus: added by the new "
                        "grid's quadrature; sum over the particles)"))
        parts = [(oid, qid) for oid, (k, qid) in self.ref.items() if k == "particle"]
        for oid, qid in parts:
            lab = self.objects[oid]["label"]
            p = self.qs.particles[qid]
            add(f"{oid}.norm", T("“{label}”: probability in the window", label=lab), of=oid, group=lab)
            add(f"{oid}.absorbed", T("“{label}”: absorbed by the detectors and the edges", label=lab), of=oid,
                group=lab)
            add(f"{oid}.E", T("“{label}”: energy ⟨H⟩", label=lab), T("eV"), of=oid, group=lab)
            for c in "xyz"[:self.ndim]:
                add(f"{oid}.{c}", T("“{label}”: ⟨{c}⟩", label=lab, c=c), T("nm"), of=oid, group=lab)
            for c in "xyz"[:self.ndim]:
                add(f"{oid}.k{c}", T("“{label}”: ⟨p{c} − qA{c}⟩/ħ", label=lab, c=c), T("nm⁻¹"), of=oid, group=lab)
            add(f"{oid}.v", T("“{label}”: speed |⟨v⟩|", label=lab), T("km/s"), of=oid, group=lab)
            if p.species.spin_half and p.kind != "marker":
                for c in "xyz":
                    add(f"{oid}.s{c}", T("“{label}”: spin ⟨σ{c}⟩", label=lab, c=c), of=oid, group=lab)
            if p.kind == "marker":
                add(f"{oid}.coh", T("“{label}”: which-path marker, coherence |⟨0|ρ|1⟩|", label=lab), of=oid,
                    group=lab)
        for oid, (kind, qid) in self.ref.items():
            o = self.objects[oid]
            lab = o["label"]
            if kind == "plane":
                add(f"{oid}.J", T("“{label}”: probability flux now (sum over the particles)", label=lab), T("1/fs"),
                    of=oid, group=lab)
                add(f"{oid}.F", T("“{label}”: flux over the time since the scene's last change (sum over the "
                                  "particles)", label=lab), of=oid, group=lab)
                for poid, pq in parts:
                    add(f"{oid}.J.{poid}", T("“{label}”: flux of “{particle}” now", label=lab,
                                             particle=self.objects[poid]["label"]), T("1/fs"), of=oid, group=lab)
            elif o["type"] == "detector":
                add(f"{oid}.P", T("“{label}”: absorbed (sum over the particles)", label=lab), of=oid, group=lab)
                add(f"{oid}.in", T("“{label}”: probability in its region now (sum over the particles)", label=lab),
                    of=oid, group=lab)
                add(f"{oid}.n", T("“{label}”: Bohm particles registered", label=lab), T("points"), of=oid, group=lab)
                for poid, pq in parts:
                    add(f"{oid}.P.{poid}", T("“{label}”: absorbed from “{particle}”", label=lab,
                                             particle=self.objects[poid]["label"]), of=oid, group=lab)
            elif o["type"] == "marker":
                add(f"{oid}.in", T("“{label}”: probability in the marker's region now (sum over the particles)",
                                   label=lab), of=oid, group=lab)
        return out

    def measure(self) -> dict:
        """The current values of ``measurables`` ({id: number}, NaN where undefined): the API's optional hook the sweeps
        call alone (the integrator's API of 2026-11-11, §4; review LB1-p02-ux Q3: it returned a tuple and every p02 sweep
        failed). The reasons of the NaNs travel in the frame's ``meas_note`` (``_measure``)."""
        return self._measure()[0]

    def _measure(self, R=None):
        """(``measure``'s values, the reasons of the NaNs {id: text}); ``R`` the particles' readings when the
        frame has them."""
        qs = self.qs
        R = self._readings() if R is None else R
        m, note = {}, {}
        nan = float("nan")
        tot_n = tot_a = tot_r = 0.0
        rho = None
        for oid, (kind, qid) in self.ref.items():
            if kind != "particle":
                continue
            p = qs.particles[qid]
            o = R[oid]
            a = float(sum(v for k, v in o["A"].items() if k != "regrid"))
            tot_n += o["norm"]
            tot_a += a
            tot_r += float(o["A"].get("regrid", 0.0))
            m[f"{oid}.norm"], m[f"{oid}.absorbed"] = o["norm"], a
            keys = [f"{oid}.E", f"{oid}.v"] + [f"{oid}.{c}" for c in "xyz"[:self.ndim]] + \
                [f"{oid}.k{c}" for c in "xyz"[:self.ndim]]
            spin = p.species.spin_half and p.kind != "marker"
            if spin:
                keys += [f"{oid}.s{c}" for c in "xyz"]
            if p.kind == "marker":
                keys.append(f"{oid}.coh")
            if o["E"] is None:
                why = (T("the particle was registered by a detector: there is no wave") if not p.active else
                       T("no wave is left in the window"))
                for k in keys:
                    m[k], note[k] = nan, why
                continue
            m[f"{oid}.E"] = o["E"] * EV
            m[f"{oid}.v"] = self._speed_kms(o, p)
            for i, c in enumerate("xyz"[:self.ndim]):
                m[f"{oid}.{c}"], m[f"{oid}.k{c}"] = o["r"][i], o["k"][i]
            if spin:
                for c, val in zip("xyz", qs.spin(qid)):
                    m[f"{oid}.s{c}"] = float(val)
            if p.kind == "marker":
                m[f"{oid}.coh"] = float(abs(qs.marker_state(qid)[0, 1]))
        m["norm"], m["absorbed"], m["regrid"] = tot_n, tot_a, tot_r
        for oid, (kind, qid) in self.ref.items():
            t = self.objects[oid]["type"]
            if kind == "plane":
                J = F = 0.0
                for poid, (pk, pid) in self.ref.items():
                    if pk != "particle":
                        continue
                    st = qs.particles[pid].planes.get(qid) or {}
                    j = float(st.get("J", 0.0)) * FS
                    m[f"{oid}.J.{poid}"] = j
                    J += j
                    F += float(st.get("F", 0.0))
                m[f"{oid}.J"], m[f"{oid}.F"] = J, F
            elif t in ("detector", "marker"):
                if rho is None:
                    rho = qs.density()
                m[f"{oid}.in"] = float(np.sum(rho * self._profile(oid)) * qs.grid.dV)
                if t == "detector":
                    key = f"detector {qid}"
                    P = 0.0
                    for poid, (pk, pid) in self.ref.items():
                        if pk == "particle":
                            a = float(R[poid]["A"].get(key, 0.0))
                            m[f"{oid}.P.{poid}"] = a
                            P += a
                    m[f"{oid}.P"] = P
                    if self.bohm:
                        m[f"{oid}.n"] = float(sum(1 for B in self.bohm.values() for k in B["key"] if k == key))
                    else:
                        m[f"{oid}.n"], note[f"{oid}.n"] = nan, T("no Bohm particles (the particle's parameter “Bohm "
                                                                 "particles (trajectories)”)")
        return m, note

    def _det_label(self, key):
        if key == "edges":
            return T("the window's edges")
        if key == "regrid":
            return T("a change of the grid or the window (dropped; a minus: added by the quadrature)")
        if key == "carried":
            return T("in the previous world (before the scene was carried over)")
        if key and key.startswith("detector "):
            q = int(key.split()[1])
            for oid, (kind, qid) in self.ref.items():
                if kind == "object" and qid == q:
                    return T("“{label}”", label=self.objects[oid]["label"])
        return str(key)

    def emit_wave(self):
        """The picture of |psi|^2 summed over the particles (each its own probability): the plane's image, in 3-D the
        volume and the plane z = 0 (drawing only: block-averaged, square-root encoded)."""
        qs = self.qs
        rho = qs.density()
        g = qs.grid
        if self.ndim == 2:
            img = _block(rho, IMG_MAX)
        else:
            img = _block(rho[:, :, int(np.argmin(np.abs(g.axes[2])))], IMG_MAX)
        peak = float(img.max())
        meta = {"type": "wave", "t": self.t, "shape": list(img.shape), "peak": peak,
                "x": [float(g.axes[0][0]), float(g.axes[0][-1])], "y": [float(g.axes[1][0]), float(g.axes[1][-1])],
                "total": float(rho.sum() * g.dV)}
        blobs = {"amp": np.round(255 * np.sqrt(img / peak)).astype(np.uint8) if peak > 0
                 else np.zeros(img.shape, np.uint8)}
        act = [p for p in qs.particles.values() if p.active and p.psi is not None]
        if len(act) == 1 and self.ndim == 2:
            w = qs.wave(act[0].id)
            w = w if w.ndim == 2 else w[0]
            s = max(1, int(math.ceil(max(w.shape) / IMG_MAX)))
            ph = np.angle(w[::s, ::s][:img.shape[0], :img.shape[1]])
            blobs["phase"] = np.round((ph + math.pi) / (2 * math.pi) * 255).astype(np.uint8)
        self.emit(meta, blobs)
        if self.ndim == 3:
            vol = _block(rho, VOL_MAX)
            pk = float(vol.max())
            data = np.round(255 * np.sqrt(vol / pk)).astype(np.uint8) if pk > 0 else np.zeros(vol.shape, np.uint8)
            self.emit({"type": "wave3d", "t": self.t, "dims": [vol.shape[2], vol.shape[0], vol.shape[1]]},
                      {"data": np.ascontiguousarray(data.transpose(2, 0, 1)).ravel()})

    # --- checks ------------------------------------------------------------------------------------------------------
    def checks(self):
        qs = self.qs
        if not qs.particles:
            return
        res = qs.checks()  # the step error is sampled every ERROR_EVERY scene steps by the scene itself (B6-Q7)
        for oid, (kind, pid) in self.ref.items():
            if kind != "particle" or pid not in res:
                continue
            r, lab = res[pid], self.objects[oid]["label"]
            bal = r["balance"]
            self.running_check(f"balance_{oid}", T("“{label}”: norm + absorbed (= 1)", label=lab), 1.0 + bal, 1.0,
                               r["balance_tol"], ok=abs(bal) <= r["balance_tol"],
                               note=T("probability in the window {p:.6g} and absorbed by the detectors and the edges; "
                                      "the tolerance is round-off, 32 ε per step", p=float(r["norm"])))
            if not r["active"]:
                continue
            e = r["energy"]
            if e["closed"]:
                self.running_check(f"energy_{oid}", T("“{label}”: energy ⟨H⟩ (a closed system)", label=lab),
                                   e["E"] * EV, e["E_ref"] * EV, e["bound"] / max(abs(e["E_ref"]), 1e-300),
                                   unit=T("eV"), ok=abs(e["drift"]) <= e["bound"],
                                   note=T("against ⟨H⟩ at t = {t:.4g} s; the bound 2‖Hψ‖e + e²‖H‖ with the step "
                                          "error e estimated by a companion run (a step dt against two dt/2 every "
                                          "{n:d} steps): a bound at this estimate, not a strict one", t=e["since"] * TU,
                                          n=int(ERROR_EVERY)))
            else:
                self.running_check(f"energy_{oid}", T("“{label}”: energy ⟨H⟩ (not conserved: absorption or an "
                                                      "environment)", label=lab),
                                   e["E"] * EV, None, 0.0, unit=T("eV"), info=True,
                                   note=T("in an open system the particle's energy in the window changes, as it "
                                          "should"))
            se = r["step_error"]
            self.running_check(f"steperr_{oid}", T("“{label}”: time-step error (accumulated estimate)", label=lab),
                               se["accumulated"], None, 0.0, info=True,
                               note=T("local {loc:.3g} per step (a step dt against two dt/2, ×4/3, every {n:d} scene "
                                      "steps); the sum over the steps estimates the global error ‖ψ − ψ_exact‖ to "
                                      "leading order, not a bound (the double slit: an estimate of {e1:.2g} at a true "
                                      "{e2:.2g})", loc=float(se["local"]), n=int(ERROR_EVERY), e1=3.7e-3, e2=2.6e-4))
            for plid, pl in r["planes"].items():
                po = next((o for o, (k, q) in self.ref.items() if k == "plane" and q == plid), None)
                if po is None:
                    continue
                self.running_check(f"flux_{oid}_{po}", T("“{label}” through “{plane}”: the flux over time against the "
                                                         "gain of probability beyond the plane", label=lab,
                                                         plane=self.objects[po]["label"]),
                                   pl["flux_integral"], pl["delta_beyond"], 0.0, info=True,
                                   note=(T("the difference is of order dt² (the splitting scheme has its own current)")
                                         if pl["valid"] else
                                         T("the environment makes jumps: the balance through the plane is not "
                                           "checked")))
            self.running_check(f"grid_{oid}", T("“{label}”: share of probability at the edge of the grid's spectrum",
                                                label=lab), r["spectral_tail"],
                               None, 0.0, info=True, group=T("Grid"),
                               note=T("in the upper third of the wavenumbers (|k| > 2/3·π/step); the scene does not "
                                      "admit a wave whose wavenumbers (|k| + 6σ_k and the energy from the potential) go "
                                      "beyond 2/3·π/step next to a potential; what remains here are tails from the "
                                      "shapes' edges and the evanescent wave in high walls (the double slit: up to "
                                      "{a:.2g}, a 30 eV wall: {b:.2g}), while the well of −3 eV that was not admitted "
                                      "had {c:.2g}", a=4e-5, b=1.7e-4, c=0.25))
            self.running_check(f"face_{oid}", T("“{label}”: density at the window's faces (share of the peak)",
                                                label=lab), r["window_face"],
                               None, 0.0, info=True, group=T("Grid"),
                               note=T("the grid is periodic: a wave at a face leaves on the other side (with open "
                                      "edges the layers absorb it)"))
            if self.open:
                p = qs.particles[pid]
                kk = float(np.linalg.norm(p.packet.k))
                if kk > 0:
                    R, Tr, R60 = self._edge_RT(kk, p.species.mass, qs.edges.strength)
                    R0 = float(qs.edge_reflection([kk], p.species.mass)[0][0])
                    self.running_check(f"edgeR_{oid}", T("“{label}”: reflection by the window's edges (mean over the "
                                                         "angles of incidence)", label=lab),
                                       R, None, 0.0, info=True, group=T("Grid"),
                                       note=T("weighted by the flux to the face over all directions (any layer "
                                              "reflects almost grazing waves); at normal incidence {R0:.2g}, at 60° "
                                              "{R60:.2g}; the leak through the layer (on average) {Tl:.2g}; stationary "
                                              "transfer matrices of the layer W₀ = {W:.3g} eV, width {w:.3g} nm, at "
                                              "the packet's |k|", R0=R0, R60=float(R60), Tl=float(Tr),
                                              W=qs.edges.strength * EV, w=self.edge_w))
        self._bohm_checks()
        for oid, (kind, qid) in self.ref.items():
            ob = qs.objects.get(qid) if kind == "object" else None
            if not isinstance(ob, QS.Detector):
                continue
            ax = self._det_axis(ob)
            if ax is None:
                continue
            if oid not in self._detR:  # the same until the scene changes (cleared by _tune)
                worst = None
                for k, m in self._waves():
                    R, Tr = ob.reflection([k], m, axis=ax)
                    if worst is None or R[0] + Tr[0] > worst[0] + worst[1]:
                        worst = (float(R[0]), float(Tr[0]), k)
                self._detR[oid] = worst
            worst = self._detR[oid]
            if worst:
                self.running_check(f"detR_{oid}", T("“{label}”: the detector's reflection (normal to the {axis} axis)",
                                                    label=self.objects[oid]["label"], axis="xyz"[ax]),
                                   worst[0], None, 0.0, info=True, group=T("Grid"),
                                   note=T("the leak through it {leak:.3g}; the worst over the particles' wavenumbers "
                                          "(k = {k:.3g} nm⁻¹); stationary transfer matrices of its profile, W₀ = "
                                          "{W:.3g} eV", leak=worst[1], k=float(worst[2]), W=ob.strength * EV))
        # the estimate only: the measured seconds depend on the wall clock (a world continued from its checkpoint must
        # emit the same messages); the actual speed is the player's "actual" next to the speed
        c = qs.cost_estimate()
        rt = qs.dt * TU / c["per_step_s"] if c["per_step_s"] > 0 else None
        self.running_check("cost", T("Computation: seconds per step ({device}, estimate)",
                                     device="GPU 0" if c["device"] == "gpu" else "CPU"),
                           c["per_step_s"], None, 0.0, info=True, group=T("Computation"), unit=T("s"),
                           note=T("{points:d} points, step {dt:.3g} fs; the real-time limit ≈ {rt:.3g} s of the world "
                                  "per second; an estimate from the kernel's measured rates (RATES), the actual speed "
                                  "is next to the speed slider", points=int(c["points"]), dt=qs.dt / FS, rt=rt)
                           if rt else c["note"])

    def _bohm_checks(self):
        """Bohm points measured in the run (review B6-Q1, as r12): the control's deviation and the registrations against
        the absorbed probabilities."""
        from scipy import special, stats
        for oid, B in self.bohm.items():
            if oid not in self.ref:
                continue
            lab = self.objects[oid]["label"]
            pid = self.ref[oid][1]
            C = len(B["Xc"])
            d = self._pairs(B)
            if C and len(d):
                tol = 0.5 * self.d
                med = float(np.median(d))
                fate = B["fate"] + sum(1 for j in range(C) if B["key"][j] is not None and B["keyc"][j] is not None
                                       and B["key"][j] != B["keyc"][j])
                self.running_check(f"bohm_acc_{oid}", T("“{label}”: accuracy of the Bohm trajectories (control, "
                                                        "median)", label=lab), med,
                                   None, tol, unit=T("nm"), group=T("Bohm"), ok=med <= tol and fate <= 1,
                                   note=T("{C:d} points of the ensemble integrated once more in the same wave: "
                                          "interpolation of order {order:d} instead of 8, the time step's tolerances "
                                          "{tight:d} times tighter; the median deviation {med:.2g} nm against half "
                                          "the grid step {tol:.3g} nm (the scale on which the grid knows |ψ|²); the "
                                          "largest in the run {dmax:.2g} nm (near the wave's nodes the trajectories "
                                          "are sensitive: single ones diverge even without an error); a different "
                                          "absorber for {fate:d} (1 allowed)", C=int(C), order=int(CONTROL_ORDER), tight=int(CONTROL_TIGHT),
                                          med=med, tol=tol, dmax=float(B["dmax"]), fate=int(fate)))
            rows = self._bohm_expected(B, pid)
            if not rows:
                continue
            worst, parts = 1.0, []
            for key, (n, mu, var) in sorted(rows.items()):
                if var >= 9:
                    pv = float(special.erfc(abs(n - mu) / math.sqrt(2 * var)))
                else:  # few expected: the Poisson tail of the binomial sum
                    pv = 1.0 if mu <= 0 and n == 0 else (0.0 if mu <= 0 else
                                                         min(1.0, 2 * min(float(stats.poisson.cdf(n, mu)),
                                                                          float(stats.poisson.sf(n - 1, mu)))))
                worst = min(worst, pv)
                parts.append(T("{where}: {n:d} at an expected {mu:.1f} ± {sd:.1f}", where=self._det_label(key),
                               n=int(n), mu=float(mu), sd=math.sqrt(max(var, 0.0))))
            z = float(math.sqrt(2) * special.erfcinv(max(worst, 1e-300)))
            self.running_check(f"bohm_reg_{oid}", T("“{label}”: registrations of Bohm particles against the absorbed "
                                                    "probability", label=lab),
                               z, None, 5.0, unit="σ", group=T("Bohm"), ok=worst >= BOHM_P,
                               note=T("{rows} of {n:d}; equivariance with absorption: points absorbed at the rate 2W "
                                      "stay distributed by |ψ|², and a detector absorbs a share of them equal to the "
                                      "probability it absorbed; the tolerance is 5σ of the two-sided binomial (Poisson "
                                      "for small numbers) spread; the worst deviation {z:.2g}σ",
                                      rows=join(parts, "; "), n=int(B["n"]), z=z))

    # --- header and the scene's drawing --------------------------------------------------------------------------
    def header(self):
        grid, (lo, hi) = self._grid_info()
        objects = []
        if self.ndim == 2:
            objects.append({"id": "wave", "label": T("Wave |ψ|² (sum over the particles)"), "kind": "panel",
                            "origin": [lo[0], lo[1], 0.0], "u": [hi[0] - lo[0], 0.0, 0.0],
                            "v": [0.0, hi[1] - lo[1], 0.0], "visible": True})
        layers = ([{"id": "wave3d", "label": T("Wave |ψ|² in the volume (sum over the particles)"), "kind": "volume",
                    "visible": True, "look": {"density": 3.0, "threshold": 0.01}}] if self.ndim == 3 else [])
        return {
            "title": T("Laboratory: quantum particles"),
            "text": T("Wave packets of particles in a scene of potentials, fields and detectors. Each particle has "
                      "its own wave function, evolved by the Schrödinger equation (the Pauli equation for spin); the "
                      "particles do not interact. Everything is added and changed at the current moment; the "
                      "detectors absorb probability, a position measurement is an action."),
            "actions": self._actions(),
            "approximations": self._approx(),
            # the axes' unit: a plain msgid (a static field the 3-D environment puts into its axis labels)
            "scene3d": {"box": [lo, hi], "units": "nm", "objects": objects, "layers": layers,
                        "coord_names": ["x", "y", "z"], "up": [0, 0, 1],
                        "planes": {"max": 0, "center": [0.0, 0.0, 0.0], "defaults": {"1": [0, 0, 1]}}},
            "grid": grid,
            "units": {"time_s": TU, "energy_eV": EV, "field_T": TESLA},
            "playground": self.playground_header(),
            "modifications": SCHEMA.modifications(self.params),
        }, {}

    def _approx(self):
        a = [T("non-relativistic particles (the Schrödinger equation; spin ½: the Pauli equation); the particles do "
               "not interact"),
             T("the shapes' edges are smooth: an edge's width is a physical length, no less than three grid steps"),
             T("detectors are absorbing regions (a complex potential); their reflection is in the checks")]
        if self.ndim == 2:
            a.append(T("a plane: the field changes only in it (the change out of the plane that Maxwell's equations "
                       "require is not included: exact for uniform fields)"))
        if self.open:
            a.append(T("the window's open edges are absorbing layers (their reflection, the mean over the angles of "
                       "incidence, for every particle is in the checks)"))
        else:
            a.append(T("closed edges: the window is periodic (a wave that leaves over an edge comes in on the other "
                       "side); a charged particle next to a magnetic field or a flux tube is not admitted: at the "
                       "window's face there would be a layer of field that is not in the scene"))
        if self.bohm:
            a.append(T("Bohm particles are the de Broglie–Bohm interpretation (trajectories along the probability "
                       "current), not a consequence of the Schrödinger equation; in an absorber a point is absorbed at "
                       "the rate 2W (so that it stays distributed by |ψ|² among those not absorbed); after a "
                       "measurement the ensemble is drawn from |ψ|² again, after a jump of the environment only the "
                       "points not absorbed"))
        if any(o["type"] == "env" for o in self.objects.values()):
            a.append(T("the environment is a Markovian model of localization (the Lindblad equation with Gaussian "
                       "operators), not a specific gas or radiation"))
        return a

    def _actions(self):
        acts = []
        parts = [{"value": oid, "label": self.objects[oid]["label"]} for oid, (k, q) in self.ref.items()
                 if k == "particle" and self.qs.particles[q].active]
        if parts:
            acts.append({"name": "measure", "label": T("Measure the position"), "button": T("measure"),
                         "help": T("An unsharp measurement of the position with resolution σ (Gaussian Kraus "
                                   "operators): the outcome is a point by the Born rule or “already absorbed by a "
                                   "detector”; the wave collapses to the outcome"),
                         "args": [{"id": "particle", "label": T("Particle"), "type": "select",
                                   "default": parts[0]["value"], "options": parts},
                                  {"id": "sigma", "label": T("Resolution σ, nm"), "type": "float",
                                   "default": round(max(1.0, 2 * self.d), 3), "min": self.d}]})
        every = [{"value": oid, "label": self.objects[oid]["label"]} for oid, (k, q) in self.ref.items()
                 if k == "particle"]
        if every:
            acts.append({"name": "prepare", "label": T("Prepare the packet anew"), "button": T("prepare"),
                         "help": T("A fresh Gaussian packet at the current moment (the widths, the spin and the particle "
                                   "from the parameters): the former wave and its record of what was absorbed are "
                                   "dropped (a drag and a throw, by contrast, keep the wave). Where: the centre at "
                                   "preparation and λ from the parameters, or where the wave is now: the centre ⟨r⟩ and "
                                   "the momentum ⟨p − qA⟩ are the means of the whole wave (for a wave of several parts "
                                   "⟨r⟩ may lie between them)"),
                         "args": [{"id": "particle", "label": T("Particle"), "type": "select",
                                   "default": every[0]["value"], "options": every},
                                  {"id": "where", "label": T("Where"), "type": "select", "default": "values",
                                   "options": [{"value": "values", "label": T("centre and λ from the parameters")},
                                               {"value": "now", "label": T("where the wave is now (⟨r⟩, ⟨k⟩)")}]}]})
        nk = "n2" if self.ndim == 2 else "n3"
        coarser = [o[0] for o in SCHEMA.by_id[nk].options if int(o[0]) < int(self.params[nk])]
        if coarser:
            acts.append({"name": "coarsen", "label": T("Coarsen the grid with edges to match"), "button": T("coarsen"),
                         "help": T("A coarser grid when the edges of objects with “Edge width” 0 (“the sharpest edge "
                                   "of the grid”, frozen at the width the object was added with) are narrower than the "
                                   "new grid resolves: such edges widen to ≈ 3 steps of the new grid (the objects' "
                                   "potential changes: the edges get wider), then the wave is resampled exactly. A "
                                   "refusal changes nothing"),
                         "args": [{"id": "n", "label": T("Grid points per axis"), "type": "select",
                                   "default": coarser[-1],
                                   "options": [{"value": c, "label": c} for c in coarser]}]})
        return acts

    def _coarsen(self, n):
        """"Coarsen the grid with edges to match" (review LB1-p02-ux X10): the edges set to 0 that the grid of ``n`` points
        does not resolve are widened to 1.05 x its narrowest edge (``auto_edge``: the objects' potentials change, said),
        then the grid changes (``_regrid``); a refusal undoes the widened edges (nothing changed)."""
        nk = "n2" if self.ndim == 2 else "n3"
        if n >= int(self.params[nk]):
            raise Refusal(T("a grid of {n:d} points per axis is not coarser than the present one ({now})", n=int(n),
                            now=self.params[nk]), hint=T("choose fewer points"))
        want = 1.05 * QS.edge_min(self.size / n)
        wide = [oid for oid, w in self.auto_edge.items() if w < want and oid in self.ref]
        saved = {oid: self.auto_edge[oid] for oid in wide}
        done = []
        try:
            for oid in wide:
                self.auto_edge[oid] = want
                ob = self._finite(self._object(self.objects[oid]))
                self.qs.update(self.ref[oid][1], **ob.params())
                done.append(oid)
            text = self._regrid(n, self.size, self.open, {**self.params, nk: str(n)})
        except Exception:
            for oid in wide:
                self.auto_edge[oid] = saved[oid]
            for oid in done:
                ob = self._object(self.objects[oid])
                self.qs.update(self.ref[oid][1], **ob.params())
            self._tune()
            raise
        self.emit({"type": "live", "t": self.t, "values": self.live_values()})
        if wide:
            text = T("{text}; the edges of width 0 widened to the new grid (the potential changed): {objects}",
                     text=text, objects=join([T("“{label}” {w0:.3g} → {w1:.3g} nm", label=self.objects[o]["label"],
                                               w0=float(saved[o]), w1=want) for o in wide], ", "))
        return text

    def action(self, name, args):
        if name == "coarsen":
            nk = "n2" if self.ndim == 2 else "n3"
            n = int(args.get("n") or 0)
            if str(n) not in [o[0] for o in SCHEMA.by_id[nk].options]:
                raise Refusal(T("there is no grid of {n:d} points per axis", n=int(n)), hint=T("choose from the list"))
            text = self._coarsen(n)
            self.emit({"type": "actions", "t": self.t, "actions": self._actions()})
            return text
        if name not in ("measure", "prepare"):
            raise Refusal(T("no action “{name}”", name=str(name)))
        oid = args.get("particle")
        if oid not in self.ref or self.ref[oid][0] != "particle":
            raise Refusal(T("no such particle"))
        pid = self.ref[oid][1]
        lab = self.objects[oid]["label"]
        if name == "prepare":
            obj = self.objects[oid]
            v = obj["values"]
            where = args.get("where") or "values"
            old = dict(v)
            if where == "now":  # the packet's centre and momentum from the wave now (review LB1-p02-ux X11)
                o = self.qs.observables(pid)
                if o["r"] is None or not o["norm"] > 0:
                    raise Refusal(T("“{label}”: there is no wave in the window: nothing to take the centre and the "
                                    "momentum from", label=lab), hint=T("prepare the packet from the parameters"))
                for i, c in enumerate("xyz"[:self.ndim]):
                    v[c] = float(f"{o['r'][i]:.10g}")
                self._set_momentum(v, o["k"], self.qs.particles[pid].species.mass)
            pk = self._packet(v)
            try:
                self.qs.replace_particle(pid, pk)
            except ValueError as e:
                obj["values"] = old
                raise self._packet_refusal(obj, pk, e) from None
            self._set_momentum(v, pk.k, pk.species.mass, direction=False)
            self._seed_bohm(obj)
            self._tune()
            self._set_vmax(obj)
            if v != old:
                self.rev += 1
                self.emit_scene()
            self.emit({"type": "actions", "t": self.t, "actions": self._actions()})
            kk = float(np.linalg.norm(pk.k))
            lam = T("λ = {lam:.4g} nm", lam=2 * math.pi / kk) if kk > 0 else T("λ = ∞")
            if where == "now":
                return T("“{label}”: a fresh packet prepared at {at} nm, {lam}: where the wave was (its means ⟨r⟩ and "
                         "⟨p − qA⟩)", label=lab, at=_pt(self._vec(v)), lam=lam)
            return T("“{label}”: a fresh packet prepared at {at} nm, {lam}: from the parameters", label=lab,
                     at=_pt(self._vec(v)), lam=lam)
        out = self.qs.measure(pid, float(args.get("sigma", 1.0)), self.rng)
        self._tune()  # the wave's spectrum widened by 1/(4 sigma^2): the step follows (review B6-Q4)
        if out["outcome"] == "absorbed":
            self.bohm.pop(oid, None)
            text = T("“{label}”: already absorbed: {where} (probability {p:.3g})", label=lab,
                     where=self._det_label(out["detector"]), p=float(out["p"]))
        else:
            x = [float(c) for c in out["x"]]
            self.marks.append(x + [0.0] * (3 - self.ndim))
            self._emit_marks()
            if oid in self.bohm:
                self._seed_bohm(self.objects[oid])
            text = T("“{label}” found at {at} nm ± σ (it was in the window with probability {p:.3g})", label=lab,
                     at=_pt(x), p=float(out["p_flight"]))
        self.emit({"type": "actions", "t": self.t, "actions": self._actions()})
        return text

    def _emit_marks(self):
        z = 0.03 * self.size if self.ndim == 2 else 0.0
        P = np.array([[m[0], m[1], m[2] if self.ndim == 3 else z] for m in self.marks], np.float32)
        self.emit({"type": "marks", "t": self.t, "id": "measured", "label": T("Outcomes of position measurements")},
                  {"pos": P.reshape(-1)})

    def shapes(self):
        """What the view draws for every scene object (boxes clipped to the window, balls, planes): from the engine's
        own bounding boxes."""
        qs, items = self.qs, []
        wl = [float(a[0]) - 0.5 * d for a, d in zip(qs.grid.axes, qs.grid.d)]
        wh = [float(a[-1]) + 0.5 * d for a, d in zip(qs.grid.axes, qs.grid.d)]
        for oid, (kind, qid) in self.ref.items():
            o = self.objects[oid]
            t, v = o["type"], o["values"]
            base = {"id": oid, "label": o["label"], "type": t}
            if kind == "particle":
                continue
            if kind == "plane":
                ax = int(v["axis"])
                lo, hi = list(wl), list(wh)
                lo[ax] = hi[ax] = qs.planes[qid]["position"]
                items.append({**base, "shape": "plane", "lo": lo, "hi": hi, "color": COLORS["plane"]})
                continue
            ob = qs.objects[qid]
            col = {"detector": COLORS["detector"], "marker": COLORS["marker"], "env": COLORS["env"],
                   "bfield": COLORS["field"], "flux": COLORS["flux"], "trap": COLORS["well"]}.get(
                t, COLORS["barrier"] if float(v.get("V", 1.0)) >= 0 else COLORS["well"])
            if t == "slit_wall":
                lo, hi = (list(map(float, a)) for a in qs.bbox(qid))
                al = ob._along(self.ndim)
                cuts = sorted((float(c) - 0.5 * float(w), float(c) + 0.5 * float(w)) for c, w in ob.slits)
                a0 = lo[al]
                for c0, c1 in cuts + [(hi[al], hi[al])]:
                    if c0 > a0:
                        l2, h2 = list(lo), list(hi)
                        l2[al], h2[al] = a0, min(c0, hi[al])
                        items.append({**base, "shape": "box", "lo": l2, "hi": h2, "color": col})
                    a0 = max(a0, c1)
                continue
            if t in ("ball", "flux", "trap"):
                c = [float(x) for x in (ob.center if t != "flux" else ob.center)][:self.ndim]
                r = float(ob.radius) if t != "trap" else float(np.min(qs.bbox(qid)[1] - np.array(c))) / 3.0
                items.append({**base, "shape": "cylinder" if (t == "flux" or (t == "ball" and ob.axes)) else "ball",
                              "center": c + [0.0] * (3 - self.ndim), "r": r, "color": col})
                continue
            lo, hi = (list(map(float, a)) for a in qs.bbox(qid))
            items.append({**base, "shape": "box", "lo": lo, "hi": hi, "color": col})
        for it in items:
            for k in ("lo", "hi"):
                if k in it:
                    it[k] = it[k] + [None] * (3 - len(it[k]))
        return items

    def emit_scene(self):
        super().emit_scene()
        self.emit({"type": "shapes", "t": self.t, "items": self.shapes()})
        self.emit({"type": "actions", "t": self.t, "actions": self._actions()})
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})

    def rekey(self):
        if self._regridded:  # the grid changed in this world: a segment's viewer needs it before the wave
            self.emit({"type": "grid", "t": self.t, "grid": self._grid_info()[0], "repeat": True})
        self._emit_marks()
        self.emit_wave()

    def engine_modules(self):
        # Bohm's guidance is listed always: any particle may get Bohm points at any moment (flagged in the top bar)
        return ["lfphys.core.quantum.scene", "lfphys.core.quantum.schrodinger_nd",
                "lfphys.theories.interpretations.bohm"]


VIZ = {
    "id": "p02_quantum",
    "title": T("Quantum particles"),
    "summary": T("A quantum mechanics laboratory: wave packets of electrons, neutrons and atoms in a scene of "
                 "barriers, wells, walls with slits, traps, magnetic fields and flux tubes; detectors, a which-path "
                 "marker, an environment, measurement."),
    "purpose": T("Build an experiment and see how the wave behaves: tunnelling, interference and its loss under a "
                 "which-path marker or in an environment, the Aharonov–Bohm shift, spin precession, a cyclotron orbit, "
                 "a position measurement; the norm, the flux and the energy are checked live."),
    "version": "0.1",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "playground",
    "ui": "full",
    "teaser": T("Build an experiment of wave packets, barriers, slits and fields and watch the wave."),
    "related": [],
    "kind": "playground",
    "section": "quantum",
}
