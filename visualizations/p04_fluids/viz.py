# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p04: the fluids playground (plan P15.7; owner, 2026-10-28). A wrapper over the engine's lattice Boltzmann solver
(``lfphys.core.fluids.lbm``: the incompressible Navier–Stokes equations in 2-D with their compressibility error
O(Ma²) stated); the framework is ``lfviz.playground``.

The laws of the world. World parameters (a change starts a new world): the fluid at the start, the domain and its grid,
the largest expected speed (it sets the time step through the Mach number; for a fluid the grid cannot resolve at that
speed the world lowers it to what the grid resolves and says so: review UX-params P24). Live laws (review UX-ui U12:
changed at the current moment, the flow kept): the viscosity (``Flow2D.set_viscosity``), the density
(``set_density``), the collision operator (``set_collision``), the dye on or off (``enable_dye`` / ``disable_dye``) and
its diffusivity. A grid above the memory budget is refused before anything is allocated (P25). Inside it the
experimenter places, at any moment, obstacles
(disks, rectangles, wing profiles; fixed, with a moving surface or a turning one — the bodies themselves stay where
they are), inlets and outlets on the sides, a moving wall (a lid), periodic sides, a body force, dye sources and
velocity probes; the solver advances the flow from the engine's laws in real time. Forces on each obstacle (drag, lift
and their coefficients: over the last step, and averaged over the slowest sound period of the domain, which the
weakly compressible scheme rings at), the mass, momentum and dye balances, the numbers that bound the solver's validity
(Mach, the cell Reynolds number) and, where the scene is a published benchmark's set-up, the benchmark's numbers next
to the computed ones are shown as the flow runs. A new object lands where it can exist (``place``: a free side, a
free spot for a body, a probe in the fluid, a body force the scheme can carry) or is refused with what to
change (reviews UX-ui U4, U7, U8, U13; UX-params P27).

Units: SI (m, s, kg); a 2-D flow is per metre of depth (forces in N/m).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.fluids import lbm as L
from lfphys.i18n import T, is_t, join, text_of
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param, scene_time


def refusal(text, hint=None, detail=None):
    """A refusal for the owner (reviews UX-params P4, UX-ui U13): what is wrong and what to change (texts, ``T``)."""
    return Refusal(text, hint=hint, detail=detail)

PIC_EVERY = 5      # frames between two pictures of the field (by count: the same in a restored world)
IMG_MAX = 512      # points per axis of the field's picture (area-averaged beyond)
ARROWS = 28        # velocity arrows along the longer side
MAX_STEPS = 400    # lattice steps per advance call (the runner interleaves commands and frames)
WINDOW_BLOCKS = 64  # blocks of the force record per sound period (the window of the forces' mean)
SIDES = [("left", T("left")), ("right", T("right")), ("bottom", T("bottom")), ("top", T("top"))]
SIDE_NAME = dict(SIDES)
# the inspector's rows of a side object (msgids: the player translates the keys)
RATE_KEY = {"left": "mass flow, left, kg/(s·m)", "right": "mass flow, right, kg/(s·m)",
            "bottom": "mass flow, bottom, kg/(s·m)", "top": "mass flow, top, kg/(s·m)"}
RAMP_KEY = {"left": "start-up, left (0…1)", "right": "start-up, right (0…1)", "bottom": "start-up, bottom (0…1)",
            "top": "start-up, top (0…1)"}
FIELDS = {"speed": T("speed |u|"), "vorticity": T("vorticity ω"), "pressure": T("pressure p"), "dye": T("dye")}
COLORS = {"obstacle": "#adb5bd", "inlet": "#51cf66", "outlet": "#ff922b", "lid": "#b197fc", "periodic": "#74c0fc",
          "dye": "#f783ac", "probe": "#ffd43b", "gravity": "#868e96"}
KIND_NAME = {"closed-open": T("4L/c_s (a closed and an open end)"), "closed-closed": T("2L/c_s (two closed ends)"),
             "open-open": T("2L/c_s (two open ends)"), "periodic": T("L/c_s (periodicity)")}
FRAME_S = 0.1        # the modelled computing time of one advance call on the CPU (commands and frames keep flowing;
#                      measured: 3 steps per call cost 23 % more than 400 on the 880-node Kármán grid, 8 steps ~8 %)
RE_MARGIN = 0.9      # the speed the world resolves: this share of the open-domain cell-Reynolds limit (P24)
MEM_DEFAULT = 6 * 2 ** 30   # the grid's memory budget when the server gave the worker none (P25)
FLUIDS_NAME = {"water": T("water"), "air": T("air"), "dfg": T("the DFG test fluid"), "custom": T("a custom fluid")}
SIDE_ORDER = {"inlet": ("left", "bottom", "right", "top"), "outlet": ("right", "top", "left", "bottom"),
              "lid": ("top", "bottom", "left", "right")}


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    # the defaults build: the DFG benchmark's fluid and channel; water and air at these scales run at the speeds the grid
    # resolves (review UX-params P24), or in their own presets at millimetre and centimetre scales
    _p("fluid", T("Fluid at the start"), "select", "dfg", group=T("Laws"),
       options=[("water", T("water, 20 °C")), ("air", T("air, 20 °C, 1 atm")),
                ("dfg", T("the DFG test fluid (ν = 10⁻³ m²/s, ρ = 1 kg/m³)")), ("custom", T("custom: ρ and ν below"))],
       help=T("Sets the density and the viscosity at the start of the world (they can be changed on the fly in "
              "“Set-up”). If the grid does not resolve the fluid at the “largest expected velocity”, the world lowers "
              "that velocity to one it resolves and says why; water and air at speeds of cm/s have their own scenarios "
              "(the millimetre and the centimetre channels)")),
    _p("rho", T("Density ρ, kg/m³"), "float", 1000.0, group=T("Fluid (on the fly)"), min=1e-3, max=1e5, log=True,
       live=True,
       help=T("Changed at the current moment: the same flow, pressures and forces on the new scale of ρ. At the start of "
              "the world: the density of the chosen fluid (for a custom one: this value)")),
    _p("nu", T("Kinematic viscosity ν, m²/s"), "float", 1e-6, group=T("Fluid (on the fly)"), min=1e-9, max=10.0,
       log=True, live=True,
       help=T("Changed at the current moment (the scheme's relaxation time; the same time step): velocity and pressure "
              "stay, the viscous stress adjusts within a few steps. Not below what the grid resolves. At the start of "
              "the world: the viscosity of the chosen fluid (for a custom one: this value)")),
    _p("Lx", T("Domain length along x, m"), "float", 2.2, group=T("Domain and grid (on the fly)"), min=1e-6, max=1e4,
       log=True, live=True,
       help=T("Changed at the current moment: the same grid spacing, the domain grows or shrinks on the side chosen "
              "below; the new part is fluid at rest or with the inflow; it can shrink only where there are no bodies, "
              "dye or probes")),
    _p("Ly", T("Domain height along y, m"), "float", 0.41, group=T("Domain and grid (on the fly)"), min=1e-6, max=1e4,
       log=True, live=True,
       help=T("Like the length: on the fly, the same spacing (the height is rounded to whole cells)")),
    _p("nx", T("Grid nodes along x"), "int", 440, group=T("Domain and grid (on the fly)"), min=16, max=8192, live=True,
       help=T("Grid spacing = length / number of nodes; along y as many per metre (the height is rounded to whole "
              "cells). On the fly the flow is moved to the new grid (pressure, velocity and the non-equilibrium part of "
              "the populations, rescaled with the relaxation times, as in grid refinement), the bodies are rebuilt on "
              "the nodes. A grid beyond the memory limit is not created (the estimate is in the refusal)")),
    _p("u_max", T("Largest expected velocity, m/s"), "float", 0.45, group=T("Domain and grid (on the fly)"), min=1e-9,
       max=1e4, log=True, live=True,
       help=T("Sets the time step through the lattice Mach number (≈ 0.1) and with it the scheme's speed of sound "
              "c_s = u_max/0.1: larger means a smaller compressibility error but slower computing; velocities in the "
              "world up to 3·u_max. Not above what the grid resolves for the fluid (cell Reynolds number ≤ 9): "
              "otherwise it is lowered at the start of the world, and on the fly the change is refused with the reason. "
              "On the fly the time step is recomputed, and the populations with it")),
    _p("anchor", T("The domain grows or shrinks"), "select", "right_top", group=T("Domain and grid (on the fly)"),
       live=True,
       options=[("right_top", T("on the right and at the top (the bodies keep their coordinates)")),
                ("left_bottom", T("on the left and at the bottom (the bodies' coordinates shift with the fluid)")),
                ("center", T("equally on both sides (the bodies' coordinates shift)"))]),
    _p("fill", T("New part of the domain"), "select", "rest", group=T("Domain and grid (on the fly)"), live=True,
       options=[("rest", T("fluid at rest (pressure from the nearest edge)")),
                ("inflow", T("with the inflow (the velocity of the first inlet)"))]),
    _p("collision", T("Collision operator"), "select", "trt", group=T("Scheme (on the fly)"), live=True,
       options=[("trt", T("TRT (walls independent of the viscosity)")), ("bgk", T("BGK (single-parameter)"))]),
    _p("dye", T("Dye"), "select", "on", group=T("Scheme (on the fly)"), live=True,
       options=[("on", T("on (a passive tracer)")), ("off", T("off"))],
       help=T("Switched on and off on the fly (off only when the scene has no dye sources)")),
    _p("dye_D", T("Dye diffusivity, m²/s (0: as the viscosity)"), "float", 0.0, group=T("Scheme (on the fly)"),
       min=0.0, max=10.0, show_if={"dye": ["on"]}, live=True),
    scene_param(),
], presets={})

LIVE = ("rho", "nu", "collision", "dye", "dye_D", "Lx", "Ly", "nx", "u_max", "anchor", "fill")
GRID = ("Lx", "Ly", "nx", "u_max")  # live laws that move the populations to another grid or time step (Flow2D.remap)
ANCHOR_NAME = {"right_top": T("on the right and at the top"), "left_bottom": T("on the left and at the bottom"),
               "center": T("equally on both sides")}


def _scene(objs):
    return {"format": "lfscene", "version": 1, "objects": objs}


SCHEMA.presets.update({
    "cylinder_re20": {"label": T("Flow past a cylinder, Re = 20 (the DFG 2D-1 set-up: mean C_x, C_y against the ranges of "
                                 "Schäfer & Turek)"),
                      # u_max = Um as in the engine's test (Ma 0.1 at Um): the preset's numbers are the test's (D = 20,
                      # interpolated: 5.5895 / 0.010504 once the start's ringing has decayed, inside the range)
                      "params": {"fluid": "dfg", "Lx": 2.2, "Ly": 0.41, "nx": 440, "u_max": 0.3, "scene": _scene([
                          {"type": "inlet", "label": T("Inlet (parabola, {u} m/s)", u=0.3),
                           "values": {"side": "left", "speed": 0.3, "profile": "parabolic", "ramp": 3.0}},
                          {"type": "outlet", "label": T("Outlet"), "values": {"side": "right"}},
                          {"type": "disk", "label": T("Cylinder"), "values": {"x": 0.2, "y": 0.2, "radius": 0.05,
                                                                         "wall": "interpolated", "ref": 0.1,
                                                                         "u_ref": 0.2}},
                          {"type": "dye_source", "label": T("Dye"), "values": {"x": 0.08, "y": 0.2,
                                                                                  "radius": 0.01}}])}},
    # 880 nodes: D = 40 cells and the developed flow's cell Reynolds number ~5.6 (at 440 it passed the open-domain
    # limit 10 from t = 0.44 s: review B7 L8); heavy on the CPU, real time on GPU 0
    "karman": {"label": T("Kármán vortex street behind a cylinder, Re = 100 (the DFG 2D-2 set-up: C_x max, C_y max, St "
                          "against the ranges; D = 40 cells: for the GPU)"),
               "params": {"fluid": "dfg", "Lx": 2.2, "Ly": 0.41, "nx": 880, "u_max": 2.0, "scene": _scene([
                   {"type": "inlet", "label": T("Inlet (parabola, {u} m/s)", u=1.5),
                    "values": {"side": "left", "speed": 1.5, "profile": "parabolic", "ramp": 0.5}},
                   {"type": "outlet", "label": T("Outlet"), "values": {"side": "right"}},
                   {"type": "disk", "label": T("Cylinder"), "values": {"x": 0.2, "y": 0.2, "radius": 0.05,
                                                                  "wall": "interpolated", "ref": 0.1, "u_ref": 1.0}},
                   {"type": "dye_source", "label": T("Dye"), "values": {"x": 0.08, "y": 0.2, "radius": 0.01}},
                   {"type": "probe", "label": T("Probe behind the cylinder"), "values": {"x": 0.6, "y": 0.2}}])}},
    "cavity": {"label": T("Lid-driven cavity, Re = 100 (centre-line profiles against the tables of Ghia, Ghia, Shin 1982)"),
               "params": {"fluid": "custom", "rho": 1.0, "nu": 0.01, "Lx": 1.0, "Ly": 1.0, "nx": 192, "u_max": 1.2,
                          "scene": _scene([
                              {"type": "lid", "label": T("Lid"), "values": {"side": "top", "speed": 1.0}},
                              {"type": "dye_source", "label": T("Dye"), "values": {"x": 0.5, "y": 0.75,
                                                                                      "radius": 0.03}}])}},
    "channel": {"label": T("Channel flow (Poiseuille, Re ≈ 2) and a plate across it: the profile upstream against the "
                           "parabola"),
                "params": {"fluid": "dfg", "Lx": 0.4, "Ly": 0.04, "nx": 512, "u_max": 0.1, "scene": _scene([
                    {"type": "inlet", "label": T("Inlet (parabola, {u} m/s)", u=0.05), "values": {"side": "left", "speed": 0.05,
                                                                                    "profile": "parabolic",
                                                                                    "ramp": 0.5}},
                    {"type": "outlet", "label": T("Outlet"), "values": {"side": "right"}},
                    {"type": "rect", "label": T("Plate"), "values": {"x": 0.2, "y": 0.01, "w": 0.004, "h": 0.016}},
                    {"type": "probe", "label": T("Velocity on the axis"), "values": {"x": 0.1, "y": 0.02}}])}},
    # the DFG 2D-1 set-up made with real fluids at the scale where Re = 20 (review UX-params P24): the same numbers of
    # cells and the same Re, so the same flow in the units of D and U; water in a 22 mm channel, air in a 22 cm one
    "water_cylinder": {"label": T("Water: flow past a cylinder of D = {d} mm in a {lx} × {ly} mm channel, Re = 20 (as the DFG "
                                  "2D-1 test, at the scale where the grid resolves water)", d=1, lx=22, ly=4.1),
                       "params": {"fluid": "water", "Lx": 0.022, "Ly": 0.0041, "nx": 440, "u_max": 0.03,
                                  "scene": _scene([
                                      {"type": "inlet", "label": T("Inlet (parabola, {u} cm/s)", u=3),
                                       "values": {"side": "left", "speed": 0.03, "profile": "parabolic", "ramp": 0.3}},
                                      {"type": "outlet", "label": T("Outlet"), "values": {"side": "right"}},
                                      {"type": "disk", "label": T("Cylinder"), "values": {"x": 0.002, "y": 0.002,
                                                                                     "radius": 0.0005,
                                                                                     "wall": "interpolated"}},
                                      {"type": "dye_source", "label": T("Dye"),
                                       "values": {"x": 0.0008, "y": 0.002, "radius": 0.0001}}])}},
    "air_cylinder": {"label": T("Air: flow past a cylinder of D = {d} cm in a {lx} × {ly} cm channel, Re = 20 (as the DFG 2D-1 "
                                "test, at the scale where the grid resolves air)", d=1, lx=22, ly=4.1),
                     "params": {"fluid": "air", "Lx": 0.22, "Ly": 0.041, "nx": 440, "u_max": 0.0455,
                                "scene": _scene([
                                    {"type": "inlet", "label": T("Inlet (parabola, {u} cm/s)", u=4.55),
                                     "values": {"side": "left", "speed": 0.0455, "profile": "parabolic", "ramp": 2.0}},
                                    {"type": "outlet", "label": T("Outlet"), "values": {"side": "right"}},
                                    {"type": "disk", "label": T("Cylinder"), "values": {"x": 0.02, "y": 0.02,
                                                                                   "radius": 0.005,
                                                                                   "wall": "interpolated"}},
                                    {"type": "dye_source", "label": T("Dye"),
                                     "values": {"x": 0.008, "y": 0.02, "radius": 0.001}}])}},
    "airfoil": {"label": T("NACA 2412 wing profile at an angle of attack of {aoa}°: a cascade of profiles (periodic at the "
                           "bottom and the top: pitch {pitch} m = 2 chords, not a single wing)", aoa=8, pitch=0.8),
                "params": {"fluid": "dfg", "Lx": 2.0, "Ly": 0.8, "nx": 512, "u_max": 1.2, "scene": _scene([
                    {"type": "inlet", "label": T("Stream"), "values": {"side": "left", "speed": 1.0,
                                                                   "profile": "uniform", "ramp": 0.3}},
                    {"type": "outlet", "label": T("Outlet"), "values": {"side": "right"}},
                    {"type": "periodic", "label": T("Periodic at the top and the bottom (a cascade of profiles)"),
                     "values": {"axis": "y"}},
                    {"type": "airfoil", "label": T("Wing"), "values": {"code": "2412", "chord": 0.4, "x": 0.5,
                                                                     "y": 0.4, "aoa": 8.0, "wall": "interpolated"}},
                    {"type": "dye_source", "label": T("Dye"), "values": {"x": 0.2, "y": 0.42,
                                                                            "radius": 0.012}}])}},
})


def _nice(v: float, digits: int = 2) -> float:
    """v rounded down to ``digits`` significant digits (defaults that read well: 0.041, 4e-4)."""
    if v == 0 or not math.isfinite(v):
        return 0.0
    e = math.floor(math.log10(abs(v))) - digits + 1
    return math.copysign(math.floor(abs(v) / 10 ** e) * 10 ** e, v)


def _xy(label=None, x=0.1, y=0.1):
    label = label or T("Centre")
    return [_p("x", T("{what}: x, m", what=label), "float", x, min=-1e4, max=1e4),
            _p("y", T("{what}: y, m", what=label), "float", y, min=-1e4, max=1e4)]


# the engine imposes a surface velocity on a fixed shape (Ladd); the body itself does not move (review B7 L3)
MOTION = [_p("vx", T("Surface velocity (the body stays in place): vx, m/s"), "float", 0.0, min=-1e4, max=1e4,
             help=T("The body does NOT move: a surface velocity is set on its fixed shape (Ladd's condition). The part "
                    "normal to the surface is a source in front and a sink behind (fluid passes through the wall; the "
                    "mass balance accounts for it): this gives the instantaneous boundary condition of a moving body, "
                    "not its flow. Moving bodies are not done yet (STATUS V41 o)")),
          _p("vy", T("Surface velocity (the body stays in place): vy, m/s"), "float", 0.0, min=-1e4, max=1e4),
          _p("omega", T("Surface rotation, rad/s"), "float", 0.0, min=-1e6, max=1e6,
             help=T("The surface turns about the centre, the shape stays in place (on a circle the velocity is tangent "
                    "to the surface: a rotating cylinder, the Magnus effect)"))]
WALL = _p("wall", T("Body wall"), "select", "staircase",
          options=[("staircase", T("staircase (half-way bounce-back; first order in the shape)")),
                   ("interpolated", T("Bouzidi interpolation (more accurate; only for a surface at rest)"))],
          help=T("How the grid sees a curved wall: as a staircase of cells or with the wall's exact position on every "
                 "link (mass through such a wall is not conserved exactly; the balance accounts for it)"))
SIDE = _p("side", T("Domain side"), "select", "left", options=SIDES)


def _otype(*args, handles=None, **kw) -> ObjectType:
    """A palette type with its handles (the LB1 framework: the parameters a drag in the scene changes, checked against
    the type's schema); an older framework without handles takes the type as before."""
    if handles is None:
        return ObjectType(*args, **kw)
    try:
        return ObjectType(*args, handles=handles, **kw)
    except TypeError:
        ot = ObjectType(*args, **kw)
        ot.handles = handles
        return ot


def palette(size=(2.2, 0.41), u_max=0.45, g=9.81) -> dict:
    """The palette with defaults made for this world (review UX-ui U4, U7): places and sizes in proportion to the domain
    (a body a tenth of the shorter side, a quarter along x, on the centre line), speeds a fraction of the speed the world
    resolves, the body force the largest the scheme carries up to 9.81 m/s²."""
    Lx, Ly = float(size[0]), float(size[1])
    m = min(Lx, Ly)
    cx, cy = _nice(0.25 * Lx, 3), _nice(0.5 * Ly, 3)
    v0 = _nice(u_max / 4.5) or 1e-9
    disk = Schema([*_xy(x=cx, y=cy), _p("radius", T("Radius, m"), "float", _nice(0.1 * m), min=1e-9, max=1e4), WALL,
                   *MOTION,
                   _p("ref", T("Length for the coefficients (0: the diameter), m"), "float", 0.0, min=0.0, max=1e4),
                   _p("u_ref", T("Velocity for the coefficients (0: the mean at the inlet), m/s"), "float", 0.0,
                      min=0.0, max=1e4)])
    rect = Schema([*_xy(x=cx, y=cy), _p("w", T("Width, m"), "float", _nice(0.1 * m), min=1e-9, max=1e4),
                   _p("h", T("Height, m"), "float", _nice(0.05 * m), min=1e-9, max=1e4),
                   _p("angle", T("Rotation, °"), "float", 0.0, min=-360.0, max=360.0), WALL, *MOTION[:2],
                   _p("ref", T("Length for the coefficients (0: the height across the flow), m"), "float", 0.0,
                      min=0.0, max=1e4),
                   _p("u_ref", T("Velocity for the coefficients (0: the mean at the inlet), m/s"), "float", 0.0,
                      min=0.0, max=1e4)])
    foil = Schema([_p("code", T("NACA profile (4 digits)"), "select", "0012",
                      options=[(c, T("NACA {code}", code=c)) for c in ("0006", "0012", "0018", "2412", "4412",
                                                                       "6409")]),
                   _p("chord", T("Chord, m"), "float", _nice(0.3 * m), min=1e-9, max=1e4),
                   *_xy(T("Leading edge"), x=cx, y=cy),
                   _p("aoa", T("Angle of attack, °"), "float", 5.0, min=-90.0, max=90.0),
                   WALL,
                   _p("u_ref", T("Velocity for the coefficients (0: the mean at the inlet), m/s"), "float", 0.0,
                      min=0.0, max=1e4)])
    inlet = Schema([SIDE, _p("speed", T("Inlet velocity (the largest for a parabola), m/s"), "float", v0, min=-1e4,
                             max=1e4),
                    _p("profile", T("Profile"), "select", "uniform",
                       options=[("uniform", T("uniform")), ("parabolic", T("parabola (as in a channel)"))]),
                    _p("ramp", T("Smooth start-up within, s"), "float", 0.0, min=0.0, max=1e6,
                       help=T("After a change of the velocity the inlet passes smoothly from the old velocity to the "
                              "new one within this time; a change of the dye alone does not restart the start-up")),
                    _p("dye", T("Dye in the incoming fluid (fraction)"), "float", 0.0, min=0.0, max=1.0)])
    outlet = Schema([_p("side", T("Domain side"), "select", "right", options=SIDES),
                     _p("pressure", T("Outlet pressure (relative), Pa"), "float", 0.0, min=-1e9, max=1e9,
                        help=T("The pressure in the middle of the side; with a body force along the side its "
                               "hydrostatic part is added. The engine refuses when the scheme's density would deviate "
                               "by more than 0.045 (the scale is c_s²ρ, c_s the scheme's speed of sound)"))])
    lid = Schema([_p("side", T("Domain side"), "select", "top", options=SIDES),
                  _p("speed", T("Wall velocity along itself, m/s"), "float", v0, min=-1e4, max=1e4,
                     help=T("At the bottom and the top: along +x; on the left and the right: along +y"))])
    periodic = Schema([_p("axis", T("Pair of sides"), "select", "x",
                          options=[("x", T("left–right (along x)")), ("y", T("bottom–top (along y)"))])])
    gravity = Schema([_p("gx", T("Acceleration: gx, m/s²"), "float", 0.0, min=-1e4, max=1e4),
                      _p("gy", T("Acceleration: gy, m/s²"), "float", -g, min=-1e4, max=1e4,
                         help=T("A uniform body force (Guo's scheme). In a fluid of constant density it changes only "
                                "the pressure (hydrostatic, at once) while the walls and the outlets balance it; along "
                                "a periodic axis it drives the flow like a pressure drop. The scheme carries its "
                                "hydrostatic density spread g·L/c_s² (c_s is the scheme's speed of sound, not the "
                                "fluid's): by default the largest force the scheme of this world carries (up to "
                                "9.81 m/s²); for a larger one, a larger “largest expected velocity” (a new world)"))])
    dye = Schema([*_xy(x=_nice(0.1 * Lx, 3), y=cy), _p("radius", T("Spot radius, m"), "float", _nice(0.03 * m),
                                                     min=1e-9, max=1e4),
                  _p("concentration", T("Concentration (fraction)"), "float", 1.0, min=0.0, max=1.0),
                  _p("mode", T("How"), "select", "source", options=[("source", T("a source (holds the concentration)")),
                                                                  ("drop", T("a single drop"))])])
    probe = Schema([*_xy(T("Point"), x=_nice(0.6 * Lx, 3), y=cy)])
    return {
        # handles (P16.2): the bodies, the dye and the probes are dragged in the plane; a body moved is re-voxelised at
        # once (the nodes it leaves start as fluid at its neighbours' density, the ones it covers book their fluid)
        "disk": _otype("disk", T("Cylinder (circle)"), "body", disk, color=COLORS["obstacle"],
                       handles={"position": ["x", "y"], "size": "radius"}),
        "rect": _otype("rect", T("Rectangle"), "body", rect, color=COLORS["obstacle"],
                       handles={"position": ["x", "y"]}),
        "airfoil": _otype("airfoil", T("NACA wing profile"), "body", foil, color=COLORS["obstacle"],
                          handles={"position": ["x", "y"]}),
        "inlet": ObjectType("inlet", T("Flow inlet"), "source", inlet, limit=4, color=COLORS["inlet"],
                            help=T("A set velocity on a side of the domain (placed on the first free side)")),
        "outlet": ObjectType("outlet", T("Outlet (pressure)"), "source", outlet, limit=4, color=COLORS["outlet"]),
        "lid": ObjectType("lid", T("Moving wall"), "source", lid, limit=4, color=COLORS["lid"]),
        "periodic": ObjectType("periodic", T("Periodicity"), "field", periodic, limit=2, color=COLORS["periodic"],
                               help=T("What leaves through one side enters through the opposite one (the bodies repeat: "
                                      "a lattice)")),
        "gravity": ObjectType("gravity", T("Body force (gravity)"), "field", gravity, limit=1,
                              color=COLORS["gravity"]),
        "dye_source": _otype("dye_source", T("Dye"), "source", dye, limit=12, color=COLORS["dye"],
                             help=T("A passive tracer: shows where the fluid flows (a drop moved with the mouse falls "
                                    "again at the new place)"),
                             handles={"position": ["x", "y"], "size": "radius"}),
        "probe": _otype("probe", T("Velocity probe"), "probe", probe, limit=8, color=COLORS["probe"],
                        handles={"position": ["x", "y"]}),
    }


def naca4(code: str, chord: float, n: int = 80) -> np.ndarray:
    """The NACA four-digit profile (Abbott & von Doenhoff, Theory of Wing Sections, 1959, §6.4: the thickness
    distribution y_t = 5 t (0.2969 sqrt x - 0.1260 x - 0.3516 x^2 + 0.2843 x^3 - 0.1015 x^4) — with the closed
    trailing edge, last coefficient 0.1036 — about the mean line of camber m at p), in units of the chord from the
    leading edge, as a closed polygon (upper surface then lower)."""
    m, p, t = int(code[0]) / 100.0, int(code[1]) / 10.0, int(code[2:]) / 100.0
    beta = np.linspace(0.0, math.pi, n)
    x = 0.5 * (1.0 - np.cos(beta))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    if m > 0 and p > 0:
        yc = np.where(x < p, m / p ** 2 * (2 * p * x - x ** 2), m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x ** 2))
        dy = np.where(x < p, 2 * m / p ** 2 * (p - x), 2 * m / (1 - p) ** 2 * (p - x))
    else:
        yc, dy = np.zeros_like(x), np.zeros_like(x)
    th = np.arctan(dy)
    xu, yu = x - yt * np.sin(th), yc + yt * np.cos(th)
    xl, yl = x + yt * np.sin(th), yc - yt * np.cos(th)
    pts = np.concatenate([np.stack([xu, yu], 1), np.stack([xl, yl], 1)[::-1][1:-1]])
    return pts * chord


def _overlap(n: int, m: int) -> np.ndarray:
    """(m, n): the part of cell j (n equal cells over the side) inside picture interval k (m equal intervals over the
    same side), in units of a cell."""
    ec, ep = np.arange(n + 1) / n, np.arange(m + 1) / m
    lo = np.maximum(ep[:-1, None], ec[None, :-1])
    hi = np.minimum(ep[1:, None], ec[None, 1:])
    return np.clip(hi - lo, 0.0, None) * n


def resample(a: np.ndarray, fluid: np.ndarray, m: int):
    """The picture of a field ``a`` (nx, ny) on at most ``m`` points per axis (review B7 L16): each point covers an
    equal part of the domain (cells cut at its edges count by their share), so the picture spans the whole domain, and
    its value is the mean over the fluid it covers only (solid cells have weight 0). Returns (values, fluid fraction)."""
    nx, ny = a.shape
    s = max(nx, ny) / m
    w = fluid.astype(float)
    if s <= 1.0:
        return np.where(fluid, a, 0.0), w
    mx, my = max(1, int(round(nx / s))), max(1, int(round(ny / s)))
    Ax, Ay = _overlap(nx, mx), _overlap(ny, my)
    num = Ax @ (np.where(fluid, a, 0.0) * w) @ Ay.T
    den = Ax @ w @ Ay.T
    area = Ax.sum(axis=1)[:, None] * Ay.sum(axis=1)[None, :]
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0), den / area


# the engine's refusals of the flow, recognised by a fragment of their English text (the msgid, and its English
# rendering), put in the world's terms: "dt" is not a parameter here (U13, P24); the numbers come from the text's args
_LBM_REFUSALS = [
    ("the compressibility error O(Ma²) is too large (and the scheme unstable)", "mach"),
    ("is too close to 1/2", "tau"),
    ("the grid does not resolve the flow", "recell"),
    ("the scheme's rest density would deviate", "density"),
    ("interpolated walls only for a surface at rest", "interp"),
]


def _lbm_refusal(e):
    """(key, the text's numeric args) of an engine refusal of the flow, or (None, {})."""
    x = text_of(e)
    s = x["$t"] if is_t(x) else str(x)
    for frag, key in _LBM_REFUSALS:
        if frag in s or frag in str(e):
            return key, dict(x.get("a") or {}) if is_t(x) else {}
    return None, {}


def _grid(params):
    """(nx, ny, dx) of a world's grid, as the world builds it."""
    nx = int(params["nx"])
    dx = float(params["Lx"]) / nx
    ny = max(8, int(round(float(params["Ly"]) / dx)))
    return nx, ny, dx


def _budget():
    try:
        from lfviz import limits
        b = limits.worker_budget()
        return int(b * limits.HEADROOM) if b else MEM_DEFAULT
    except Exception:  # noqa: BLE001 - an older framework without limits
        return MEM_DEFAULT


def _fmt_bytes(n):
    """Bytes as a text with its number (the framework's units)."""
    from lfviz.limits import fmt_bytes
    return fmt_bytes(n)


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p04_fluids"
    speed_range = (1e-9, 1e6)

    # --- before a world is built (the integrator's API of 2026-11-05; review UX-params P25) ------------------------
    @classmethod
    def estimate_bytes(cls, params):
        nx, ny, _ = _grid(params)
        return (L.Flow2D.memory_estimate(nx, ny, params.get("dye", "on") == "on"),
                T("a flow grid of {nx:d} × {ny:d} nodes", nx=nx, ny=ny), cls._grid_hint(params))

    @classmethod
    def _grid_hint(cls, params, budget=None):
        budget = budget or _budget()
        per = 1000 if params.get("dye", "on") == "on" else 800
        n_max = budget / per
        Lx, Ly = float(params["Lx"]), float(params["Ly"])
        nx = int(params["nx"])
        # the largest nx whose grid fits: nx * ny ~ nx^2 Ly / Lx <= n_max (ny at least 8)
        fit = [o for o in (int(math.sqrt(n_max * Lx / Ly)), int(n_max / 8)) if o >= 16
               and o * max(8, round(Ly / (Lx / o))) <= n_max]
        lx_min = nx * nx * Ly / n_max
        parts = []
        if fit:
            parts.append(T("“Grid nodes along x” at most {n:d}", n=max(fit)))
        parts.append(T("“Domain length along x” at least {lx:.2g} m with {nx:d} nodes", lx=lx_min, nx=nx))
        parts.append(T("a domain closer to a square (along y as many nodes per metre as along x)"))
        out = parts[0]
        for q in parts[1:]:
            out = T("{a}, or {b}", a=out, b=q)
        return out

    @classmethod
    def check_params(cls, params):
        nx, ny, dx = _grid(params)
        need = L.Flow2D.memory_estimate(nx, ny, params.get("dye", "on") == "on")
        budget = _budget()
        if need > budget:
            raise refusal(T("a domain of {lx:.2g} × {ly:.2g} m on a grid of nx = {nx:d}: spacing {dx:.2g} m, {ny:d} "
                            "nodes along y, {n:.2g} nodes in all; that is ≈ {need} of memory, above the limit of "
                            "{budget}", lx=float(params["Lx"]), ly=float(params["Ly"]), nx=nx, dx=dx, ny=ny,
                            n=float(nx) * ny, need=_fmt_bytes(need), budget=_fmt_bytes(budget)),
                          hint=cls._grid_hint(params, budget))

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(self.params)
        self.check_params(params)
        fl = params["fluid"]
        if fl == "custom":
            rho, nu = float(params["rho"]), float(params["nu"])
        elif fl == "dfg":
            rho, nu = 1.0, 1e-3
        else:
            props = L.FLUIDS["water_20C" if fl == "water" else "air_20C"]
            rho, nu = float(props["rho"]), float(props["nu"])
        self.rho, self.nu = rho, nu
        nx, ny, dx = _grid(params)
        # P24: a fluid the grid cannot resolve at the asked u_max runs at the largest speed it resolves
        u_req = float(params["u_max"])
        u_ok = _nice(RE_MARGIN * L.RE_CELL_MAX_OPEN * nu / dx)
        self.u_note = None
        if u_req > u_ok:
            self.u_note = T("{fluid:cap} (ν = {nu:.2g} m²/s) on a grid of spacing {dx:.2g} m is resolved at velocities "
                            "up to {u_ok:.2g} m/s (cell Reynolds number u·dx/ν ≤ {re:.3g}): the “largest expected "
                            "velocity” is lowered from {u_req:.2g} to {u_ok:.2g} m/s; for higher velocities a smaller "
                            "domain or more nodes (a new world), or the scenarios “Water…”, “Air…”",
                            fluid=FLUIDS_NAME[fl], nu=nu, dx=dx, u_ok=u_ok, re=RE_MARGIN * 10, u_req=u_req)
            self.params["u_max"] = u_ok
        self.u_max = float(self.params["u_max"])
        self.live = {"rho": rho, "nu": nu, "collision": params["collision"], "dye": params["dye"],
                     "dye_D": float(params["dye_D"]), "Lx": nx * dx, "Ly": ny * dx, "nx": nx, "u_max": self.u_max,
                     "anchor": params["anchor"], "fill": params["fill"]}
        self.D = (float(params["dye_D"]) or nu) if params["dye"] == "on" else None
        # a world from a scene file starts at the file's time (the flow from rest): the engine counts its steps from
        # there (review B7 L2)
        self.fl = L.Flow2D(size=(nx * dx, ny * dx), dx=dx, nu=nu, rho=rho, u_max=self.u_max,
                           collision=params["collision"], dye=self.D, device="auto", t0=scene_time(params))
        self.size = (nx * dx, ny * dx)
        self.PALETTE = palette(self.size, self.u_max, self._g_default())
        self.ref = {}            # scene object id -> ("obstacle", oid) | ("side", names) | ("dye", sid) | ("probe",) ...
        self.side_owner = {}     # side name -> scene object id
        self.shown = "dye" if self.D else "speed"
        self.n_pic = 0
        self.win = None
        self._dup = False
        self.start_scene()
        self._record_setup()
        self.default_speed = self.size[0] / (10.0 * self.u_max)  # the fastest flow crosses in ~10 s

    def after_header(self):
        super().after_header()
        if self.u_note:
            self.emit({"type": "notice", "t": self.t, "text": T("Fluid and velocities: {note}", note=self.u_note)})

    # --- limits of this world (U7, U13, P24) -----------------------------------------------------------------------
    def _v_limit(self, sides=None):
        """The largest speed (m/s) a side or a surface may have now: Mach 0.3 of the scheme's sound and the cell
        Reynolds limit of the domain (with an inlet or an outlet the lower one)."""
        fl = self.fl
        c_s = fl.units.c * L.CS
        return min(L.MACH_MAX * c_s, fl.re_cell_limit(sides) * self.live["nu"] / fl.units.dx)

    def _g_default(self):
        """The body force the palette offers: 9.81 m/s² downwards when the scheme carries it with walls on every side,
        else the largest it carries (two digits)."""
        lim = self.fl.gravity_limit((0.0, -1.0), {k: L.Wall() for k in L.SIDES})
        return 9.81 if lim >= 9.81 else _nice(0.98 * lim)

    def _u_for_g(self, g, lim):
        """The u_max at which the scheme would carry |g| (the hydrostatic spread goes as 1/c_s² ∝ 1/u_max²)."""
        return self.u_max * math.sqrt(g / lim) * 1.02 if lim > 0 else math.inf

    def _ru(self, e):
        """An engine refusal of the flow put in this world's terms (what to change here: the speeds, ν, u_max, the
        grid), its English sentence as the detail (review UX-ui U13, UX-params P24); anything else as it was."""
        key, a = _lbm_refusal(e)
        if key is None:
            return e
        s = str(e)
        nu, dx = self.live["nu"], self.fl.units.dx
        v = self._v_limit()
        if key == "mach":
            return refusal(T("a velocity above what the weakly compressible scheme of this world carries (Mach number "
                             "{ma:.2g} > {max}: up to {v:.2g} m/s)", ma=float(a.get("ma", float("nan"))),
                             max=float(a.get("max", L.MACH_MAX)), v=v),
                           hint=T("velocities at most {v:.2g} m/s, or a larger “Largest expected velocity” (a new "
                                  "world)", v=v), detail=s)
        if key == "tau":
            nu_min = L.TAU_MIN_EXCESS / 3 * dx ** 2 / self.fl.units.dt
            return refusal(T("the viscosity ν = {nu:.2g} m²/s is too small for this grid and time step (the scheme is "
                             "unstable)", nu=nu),
                           hint=T("ν at least {nu:.2g} m²/s, or more nodes, or a smaller “Largest expected velocity” "
                                  "(a new world)", nu=nu_min * 1.01), detail=s)
        if key == "recell":
            return refusal(T("the grid does not resolve a flow this fast (cell Reynolds number {rec:.3g} > {lim})",
                             rec=float(a.get("rec", float("nan"))), lim=float(a.get("lim", L.RE_CELL_MAX_OPEN))),
                           hint=T("velocities at most {v:.2g} m/s, or a larger ν (changed on the fly), or more nodes "
                                  "(a new world)", v=v), detail=s)
        if key == "density":
            return refusal(T("the outlet pressure or the body force is too large for the weakly compressible scheme of "
                             "this world (its density would deviate by more than 4.5 %)"),
                           hint=T("a smaller pressure or force, or a larger “Largest expected velocity” (a new world)"),
                           detail=s)
        return refusal(T("the surface of a body with an interpolated wall cannot move"),
                       hint=T("“Body wall” = staircase, or the surface velocity and rotation 0"), detail=s)

    # --- objects ------------------------------------------------------------------------------------------------
    def _shape(self, obj):
        t, v = obj["type"], obj["values"]
        if t == "disk":
            return L.Disk((v["x"], v["y"]), v["radius"])
        if t == "rect":
            return L.Rect((v["x"], v["y"]), (v["w"], v["h"]), math.radians(v["angle"]))
        if t == "airfoil":
            return L.Polygon([tuple(map(float, q)) for q in self._foil(v)])
        raise ValueError(t)

    @staticmethod
    def _foil(v):
        """The profile placed: leading edge at (x, y), turned by the angle of attack (nose up into a stream along +x:
        the trailing edge goes down)."""
        a = -math.radians(v["aoa"])
        R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        return naca4(v["code"], v["chord"]) @ R.T + np.array([v["x"], v["y"]])

    def _outline(self, obj, n=48):
        t, v = obj["type"], obj["values"]
        if t == "disk":
            a = np.linspace(0, 2 * math.pi, n, endpoint=False)
            return np.stack([v["x"] + v["radius"] * np.cos(a), v["y"] + v["radius"] * np.sin(a)], 1)
        if t == "rect":
            a = math.radians(v["angle"])
            R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
            c = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * 0.5 * np.array([v["w"], v["h"]])
            return c @ R.T + np.array([v["x"], v["y"]])
        if t == "airfoil":
            return self._foil(v)
        return None

    def _ref_len(self, obj) -> float:
        """The coefficients' length: the chord of a profile, the object's own length, or 0 = the engine's default
        (the width across the flow); 0 also clears a length set before (review B7 L10)."""
        v = obj["values"]
        if obj["type"] == "airfoil":
            return float(v["chord"])
        return float(v.get("ref", 0.0) or 0.0)

    def _claim(self, obj, sides):
        for sd in sides:
            own = self.side_owner.get(sd)
            if own is not None and own != obj["id"]:
                free = [SIDE_NAME[k] for k in L.SIDES if self.side_owner.get(k) in (None, obj["id"])]
                raise refusal(T("the side “{side}” is already taken by “{label}”", side=SIDE_NAME[sd],
                                label=self.objects[own]["label"]),
                              hint=T("free: {sides}", sides=join(free, ", ")) if free else
                              T("all sides are taken: remove one of the objects on the sides"))

    def _side_obj(self, obj):
        t, v = obj["type"], obj["values"]
        if t == "inlet":
            return {v["side"]: L.Inlet(velocity=float(v["speed"]), profile=v["profile"], ramp=float(v["ramp"]),
                                       dye=float(v["dye"]))}
        if t == "outlet":
            return {v["side"]: L.Outlet(pressure=float(v["pressure"]))}
        if t == "lid":
            return {v["side"]: L.Wall(velocity=float(v["speed"]))}
        if t == "periodic":
            a, b = ("left", "right") if v["axis"] == "x" else ("bottom", "top")
            return {a: L.Periodic(), b: L.Periodic()}
        raise ValueError(t)

    # --- placement (reviews UX-ui U4, U7, U8, P27; the integrator's API of 2026-11-05) ----------------------------
    def place(self, kind, values):
        """A palette object's values before it is added: the defaults completed; a clicked point (``position``, m) as
        its place (for a side object: the nearest side); a side object on the first free side; a body moved to the
        nearest place where it does not cover another body; a probe or a dye spot into the fluid; a body force reduced
        to what the scheme carries (with a note); speeds above what the world resolves reduced to it (with a note).
        Deterministic: it reads the state, never changes it."""
        ot = self._type(kind)
        values = dict(values or {})
        pos = values.pop("position", None)
        v, errors = ot.schema.resolve(None, values)
        if errors:
            raise refusal(join(errors, "; "))
        v = dict(v)
        Lx, Ly = self.size
        if pos is not None:
            px, py = float(pos[0]), float(pos[1])
            if "x" in v:
                v["x"], v["y"] = px, py
            elif kind in ("inlet", "outlet", "lid"):
                d = {"left": abs(px), "right": abs(Lx - px), "bottom": abs(py), "top": abs(Ly - py)}
                v["side"] = min(d, key=d.get)
            elif kind == "periodic":
                v["axis"] = "x" if min(abs(px), abs(Lx - px)) <= min(abs(py), abs(Ly - py)) else "y"
        if kind in ("inlet", "outlet", "lid"):
            if self.side_owner.get(v["side"]) is not None:
                free = [k for k in SIDE_ORDER[kind] if self.side_owner.get(k) is None]
                if not free:
                    raise refusal(T("all four sides of the domain are taken"),
                                  hint=T("remove one of the objects on the sides or change its side"))
                self._note(T("the side “{side}” is taken: “{type}” is placed on the side “{free}”",
                             side=SIDE_NAME[v["side"]], type=ot.label, free=SIDE_NAME[free[0]]))
                v["side"] = free[0]
            self._cap_speed(kind, v, "speed")
        elif kind == "periodic":
            pair = {"x": ("left", "right"), "y": ("bottom", "top")}
            if any(self.side_owner.get(k) is not None for k in pair[v["axis"]]):
                other = "y" if v["axis"] == "x" else "x"
                if any(self.side_owner.get(k) is not None for k in pair[other]):
                    raise refusal(T("periodicity needs a pair of free opposite sides, and both pairs are taken"),
                                  hint=T("remove the objects from the left and the right (or the bottom and the top) "
                                         "sides"))
                v["axis"] = other
        elif kind in ("disk", "rect", "airfoil"):
            self._inside(kind, v, place=True)
            self._free_body(kind, v)
            for c in ("vx", "vy"):
                self._cap_speed(kind, v, c)
        elif kind in ("probe", "dye_source"):
            v["x"] = min(max(float(v["x"]), 0.0), Lx)
            v["y"] = min(max(float(v["y"]), 0.0), Ly)
            self._into_fluid(v)
        elif kind == "gravity":
            g = math.hypot(float(v["gx"]), float(v["gy"]))
            if g > 0:
                lim = self.fl.gravity_limit((float(v["gx"]), float(v["gy"])))
                if g > lim:
                    k = _nice(0.98 * lim) / g
                    self._note(T("a force of {g:.3g} m/s² is too large for the scheme of this world (its hydrostatic "
                                 "density spread would exceed 4.5 %): {g_set:.3g} m/s² is set; {g:.3g} m/s² needs a "
                                 "“largest expected velocity” of at least {u:.2g} m/s (a new world)", g=g,
                                 g_set=_nice(0.98 * lim), u=self._u_for_g(g, lim)))
                    v["gx"], v["gy"] = float(v["gx"]) * k, float(v["gy"]) * k
        return v

    def _note(self, text):
        """A short note for the owner about what was done instead of what was asked (shown at once: ``notify``)."""
        if not self._loading:
            self.emit({"type": "event", "kind": "scene", "t": self.t, "text": text, "notify": True})

    def _cap_speed(self, kind, v, key):
        lim = self._v_limit()
        sp = float(v.get(key, 0.0))
        if abs(sp) > lim:
            new = math.copysign(_nice(0.95 * lim), sp)
            self._note(T("a velocity of {v:.3g} m/s is above what this world resolves (up to {lim:.2g} m/s): {new:.2g} "
                         "m/s is set", v=sp, lim=lim, new=new))
            v[key] = new

    def _bbox(self, kind, v):
        P = self._outline({"type": kind, "values": v})
        return P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()

    def _inside(self, kind, v, place=False):
        """A body wholly outside the domain is refused (place: moved in); one that would cover (nearly) the whole
        domain is refused; one partly outside is accepted with a note (the wall cuts it)."""
        Lx, Ly = self.size
        x0, x1, y0, y1 = self._bbox(kind, v)
        if x1 <= 0 or x0 >= Lx or y1 <= 0 or y0 >= Ly:
            if place:
                cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
                v["x"] = round(float(v["x"]) + min(max(cx, 0.0), Lx) - cx, 9)
                v["y"] = round(float(v["y"]) + min(max(cy, 0.0), Ly) - cy, 9)
                return
            raise refusal(T("the body is wholly outside the domain of {lx:.2g} × {ly:.2g} m", lx=Lx, ly=Ly),
                          hint=T("its place is inside: x from 0 to {lx:.2g} m, y from 0 to {ly:.2g} m", lx=Lx, ly=Ly))
        frac = float(np.mean(self.fl.shape_mask(self._shape({"type": kind, "values": v}))))
        if frac > 0.9:
            raise refusal(T("the body would cover {pct:.0f} % of the domain: almost no fluid would be left",
                            pct=100.0 * frac),
                          hint=T("a body smaller than the domain"))
        if (x0 < 0 or x1 > Lx or y0 < 0 or y1 > Ly) and not place:
            self._note(T("the body reaches beyond the edge of the domain: its part behind the wall is cut off (the "
                         "part inside is computed)"))

    def _free_body(self, kind, v):
        """Move a body (in place) to the nearest spot where it does not cover another body, inside the domain with a
        margin of two cells; a refusal when there is none."""
        solid = self._bodies_mask()
        if not solid.any():
            return
        shape0 = self._shape({"type": kind, "values": v})
        m = self.fl.shape_mask(shape0)
        if not (m & solid).any():
            return
        Lx, Ly = self.size
        x0, x1, y0, y1 = self._bbox(kind, v)
        hx, hy = 0.5 * (x1 - x0), 0.5 * (y1 - y0)
        cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        dx = self.fl.units.dx
        xs = np.linspace(hx + 2 * dx, Lx - hx - 2 * dx, 61) if Lx - 2 * hx > 4 * dx else np.array([cx])
        ys = np.linspace(hy + 2 * dx, Ly - hy - 2 * dx, 31) if Ly - 2 * hy > 4 * dx else np.array([cy])
        C = np.stack(np.meshgrid(xs, ys, indexing="ij"), -1).reshape(-1, 2)
        order = np.argsort((C[:, 0] - cx) ** 2 + (C[:, 1] - cy) ** 2, kind="stable")
        for k in order[:400]:
            w = {**v, "x": float(v["x"]) + C[k, 0] - cx, "y": float(v["y"]) + C[k, 1] - cy}
            if not (self.fl.shape_mask(self._shape({"type": kind, "values": w})) & solid).any():
                self._note(T("the place is taken by another body: the body is placed at ({x:.4g}, {y:.4g}) m",
                             x=w["x"], y=w["y"]))
                v["x"], v["y"] = round(w["x"], 9), round(w["y"], 9)
                return
        raise refusal(T("there is no place in the domain for this body without covering another"),
                      hint=T("a smaller body, or remove the other body"))

    def _bodies_mask(self):
        m = np.zeros((self.fl.nx, self.fl.ny), bool)
        for oid, k in self.ref.items():
            if k[0] == "obstacle":
                m |= self.fl.shape_mask(self._shape(self.objects[oid]))
        return m

    def _into_fluid(self, v):
        """A probe or a dye spot inside a body goes to the nearest fluid node (with a note)."""
        solid = self.fl.solid()
        i, j = self._at(v["x"], v["y"])
        if not solid[i, j]:
            return
        fi, fj = np.nonzero(~solid)
        if not len(fi):
            raise refusal(T("there is no fluid in the domain"), hint=T("remove bodies"))
        k = int(np.argmin((self.fl.x[fi] - v["x"]) ** 2 + (self.fl.y[fj] - v["y"]) ** 2))
        v["x"], v["y"] = float(self.fl.x[fi[k]]), float(self.fl.y[fj[k]])
        self._note(T("the point is inside a body: placed at the nearest point of fluid ({x:.4g}, {y:.4g}) m",
                     x=v["x"], y=v["y"]))

    def palette_state(self):
        """The palette types the world cannot take now and why (review UX-ui U7, U22)."""
        out = {}
        if all(self.side_owner.get(k) is not None for k in L.SIDES):
            for t in ("inlet", "outlet", "lid"):
                out[t] = T("all four sides are taken: remove the object from one of the sides")
        pairs = (("left", "right"), ("bottom", "top"))
        if all(any(self.side_owner.get(k) is not None for k in p) for p in pairs):
            out["periodic"] = T("no pair of free opposite sides: remove the objects from one of the pairs")
        if self.D is None:
            out["dye_source"] = T("the dye is off: switch “Dye” on in “Set-up” (on the fly)")
        return out

    # --- a new world that keeps the scene (plan P16.1; review LB1-framework F5) ------------------------------------
    def carry_state(self):
        """The flow itself goes with a carry-over (the scene file keeps only the set-up): the engine's whole state but
        its force record (keyed by obstacle number; the new world records its own)."""
        d = self.fl.state_dict()
        d["rec"] = None
        return {"world": {"flow": d}}

    def carry_world(self, state, laws):
        """Continue the previous world's flow here (``Flow2D.adopt``): on the same grid and time step as it is; on another
        grid, domain or time step moved there first by the engine's transfer (``Flow2D.remap``, as a live change of the
        grid would; the domain grows or is cut on the right and the top, where the objects keep their coordinates);
        this world's fluid, sides, bodies, dye and force from now on. What could not be taken starts at rest, said in the
        carry-over's notice."""
        fl = self.fl
        if not state or not isinstance(state.get("flow"), dict):
            self.carry_note(T("the flow restarted from rest: the previous world did not pass it on"), restarted=True)
            return
        try:
            old = L.Flow2D.from_state_dict(state["flow"], device="cpu")
        except (ValueError, KeyError, TypeError) as e:
            self.carry_note(T("the flow restarted from rest: the previous world's state cannot be read ({why})",
                              why=text_of(e)), restarted=True)
            return
        notes = []
        same = (old.nx, old.ny) == (fl.nx, fl.ny) and old.units.dx == fl.units.dx and \
            math.isclose(old.units.dt, fl.units.dt, rel_tol=1e-12)
        if not same:
            g0 = T("{nx:d} × {ny:d} nodes (spacing {dx:.2g} m, dt {dt:.2g} s)", nx=old.nx, ny=old.ny,
                   dx=old.units.dx, dt=old.units.dt)
            try:
                try:
                    old.remap(dx=fl.units.dx, size=fl.size, dt=fl.units.dt)
                except ValueError:  # the old viscosity may not run on the new grid: this world's first
                    old.set_viscosity(self.nu)
                    old.remap(dx=fl.units.dx, size=fl.size, dt=fl.units.dt)
            except (ValueError, L.Unstable) as e:
                self.carry_note(T("the flow restarted from rest: it cannot be moved from the grid {grid} to this "
                                  "world's grid ({why})", grid=g0, why=text_of(e)), restarted=True)
                return
            notes.append(T("the flow moved from the grid {grid} to {nx:d} × {ny:d} (spacing {dx:.2g} m, dt {dt:.2g} s) "
                           "by the engine's transfer, as at a change of the grid on the fly (it took one step of the "
                           "previous grid)", grid=g0, nx=fl.nx, ny=fl.ny, dx=fl.units.dx, dt=fl.units.dt))
        try:
            rep = fl.adopt(old)
        except (ValueError, L.Unstable) as e:
            self.carry_note(T("the flow restarted from rest: {why}", why=text_of(e)), restarted=True)
            return
        if not notes:
            notes.append(T("the flow carried over as it was ({nx:d} × {ny:d} nodes, the same time step)", nx=fl.nx,
                           ny=fl.ny))
        if not math.isclose(old.nu, self.nu, rel_tol=1e-12):
            notes.append(T("viscosity {a:.2g} → {b:.2g} m²/s: the viscous stress adjusts within a few steps",
                           a=old.nu, b=self.nu))
        if not math.isclose(old.units.rho, self.rho, rel_tol=1e-12):
            notes.append(T("density {a:.2g} → {b:.2g} kg/m³: the same flow, pressures and forces on the new scale",
                           a=old.units.rho, b=self.rho))
        if rep["rest"]:
            notes.append(T("{n:d} nodes where the previous world had a body start at rest", n=int(rep["rest"])))
        if rep["dye"] == "zero":
            notes.append(T("the dye in this world starts from zero (the previous one had none)"))
        elif rep["dye"] == "dropped":
            notes.append(T("the previous world's dye is not carried over: it is off here"))
        lost = [SIDE_NAME.get(n, n) for n, sd in fl._sides.items() if isinstance(sd, L.Inlet) and n not in rep["ramps"]]
        if lost:
            notes.append(T("the inlet's start-up restarted: {sides}", sides=join(lost, ", ")))
        notes.append(T("the balances count from the carried state"))
        for n in notes:
            self.carry_note(n)

    def scene(self, args):
        # a copy lands on its original by design (lfviz.playground): this section moves a body's copy aside (U4)
        self._dup = args.get("op") == "duplicate"
        try:
            return super().scene(args)
        finally:
            self._dup = False

    def on_add(self, obj, state):
        try:
            self._on_add(obj, state)
        except ValueError as e:
            raise self._ru(e) from e

    def _on_add(self, obj, state):
        t, v = obj["type"], obj["values"]
        fl = self.fl
        if t in ("disk", "rect", "airfoil"):
            self._inside(t, v)
            if self._dup:
                self._free_body(t, v)
            oid = fl.add_obstacle(self._shape(obj), velocity=(v.get("vx", 0.0), v.get("vy", 0.0)),
                                  omega=v.get("omega", 0.0), interpolated=v.get("wall") == "interpolated",
                                  label=obj["label"], ref_length=self._ref_len(obj))
            self.ref[obj["id"]] = ("obstacle", oid)
        elif t in ("inlet", "outlet", "lid", "periodic"):
            sides = self._side_obj(obj)
            self._claim(obj, sides)
            fl.set_sides(sides)
            for sd in sides:
                self.side_owner[sd] = obj["id"]
            self.ref[obj["id"]] = ("side", tuple(sides))
        elif t == "gravity":
            self._set_gravity(v)
            self.ref[obj["id"]] = ("gravity",)
        elif t == "dye_source":
            if self.D is None:
                raise refusal(T("the dye is off in this world"), hint=T("switch “Dye” on in “Set-up” (on the fly)"))
            self._point_inside(v)
            shape = L.Disk((v["x"], v["y"]), v["radius"])
            if v["mode"] == "drop":
                fl.add_dye(shape, concentration=float(v["concentration"]), mode="add")
                self.ref[obj["id"]] = ("drop",)
            else:
                self.ref[obj["id"]] = ("dye", fl.add_dye_source(shape, concentration=float(v["concentration"]),
                                                                label=obj["label"]))
        elif t == "probe":
            self._point_inside(v)
            self.ref[obj["id"]] = ("probe",)
        self._changed()

    def _point_inside(self, v):
        Lx, Ly = self.size
        if not (0.0 <= float(v["x"]) <= Lx and 0.0 <= float(v["y"]) <= Ly):
            raise refusal(T("the point ({x:.4g}, {y:.4g}) m is outside the domain of {lx:.2g} × {ly:.2g} m",
                            x=float(v["x"]), y=float(v["y"]), lx=Lx, ly=Ly),
                          hint=T("x from 0 to {lx:.2g} m, y from 0 to {ly:.2g} m", lx=Lx, ly=Ly))

    def _set_gravity(self, v):
        g = (float(v["gx"]), float(v["gy"]))
        try:
            self.fl.set_gravity(g)
        except ValueError as e:
            gm = math.hypot(*g)
            lim = self.fl.gravity_limit(g) if gm > 0 else 0.0
            raise refusal(T("a body force of {g:.3g} m/s² is too large for the weakly compressible scheme of this "
                            "world (the hydrostatic density spread would exceed 4.5 %): it carries up to {lim:.3g} "
                            "m/s²", g=gm, lim=_nice(lim)),
                          hint=T("|g| at most {lim:.3g} m/s², or a “Largest expected velocity” of at least {u:.2g} "
                                 "m/s (a new world)", lim=_nice(lim), u=self._u_for_g(gm, lim)),
                          detail=str(e)) from e

    def on_remove(self, obj):
        kind = self.ref.get(obj["id"], (None,))
        fl = self.fl
        if kind[0] == "obstacle":
            fl.remove_obstacle(kind[1])
        elif kind[0] == "side":
            fl.set_sides({sd: L.Wall() for sd in kind[1]})
            for sd in kind[1]:
                self.side_owner.pop(sd, None)
        elif kind[0] == "gravity":
            fl.set_gravity((0.0, 0.0))
        elif kind[0] == "dye":
            fl.remove_dye_source(kind[1])
        self.ref.pop(obj["id"], None)
        self._changed()

    def on_set(self, obj, old):
        try:
            self._on_set(obj, old)
        except ValueError as e:
            raise self._ru(e) from e

    def _on_set(self, obj, old):
        t, v = obj["type"], obj["values"]
        kind = self.ref[obj["id"]]
        fl = self.fl
        if kind[0] == "obstacle":
            self._inside(t, v)
            fl.update_obstacle(kind[1], shape=self._shape(obj), velocity=(v.get("vx", 0.0), v.get("vy", 0.0)),
                               omega=v.get("omega", 0.0), interpolated=v.get("wall") == "interpolated",
                               label=obj["label"], ref_length=self._ref_len(obj))
        elif kind[0] == "side":
            sides = self._side_obj(obj)
            self._claim(obj, sides)
            new = {sd: L.Wall() for sd in kind[1] if sd not in sides}
            new.update(sides)
            fl.set_sides(new)  # an inlet whose velocity is unchanged keeps its ramp (engine: review B7 L1)
            for sd in kind[1]:
                self.side_owner.pop(sd, None)
            for sd in sides:
                self.side_owner[sd] = obj["id"]
            self.ref[obj["id"]] = ("side", tuple(sides))
        elif kind[0] == "gravity":
            self._set_gravity(v)
        elif kind[0] in ("dye", "drop"):
            self._point_inside(v)
            if kind[0] == "dye":
                fl.remove_dye_source(kind[1])
            self.ref.pop(obj["id"])
            self._on_add(obj, None)
            return
        elif kind[0] == "probe":
            self._point_inside(v)
        self._changed()

    def _changed(self):
        """After a change of the scene: the outlines, and the force record's block (the sound period depends on the
        sides; the engine restarts the record itself when the flow's set-up changed)."""
        self._shapes()
        if not self._loading:
            self._record_setup()

    def emit_scene(self):
        super().emit_scene()
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})

    # --- live laws (review UX-ui U12) ------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        """The fluid's viscosity and density, the collision operator and the dye at the current moment: the populations
        stay (the density ratio and the velocity of every node are kept: mass and momentum do not jump in lattice
        units), the next steps use the new rates; a new ρ rescales pressures and forces; the dye switched off books its
        amount as removed (its balance closes again when it comes back, zero). The grid, the domain and the largest
        expected speed (plan P16.1): the flow is moved to the new grid or time step (``Flow2D.remap``, ``_regrid``). What
        the scheme cannot carry is refused, the world as it was (all or nothing)."""
        new, errors = SCHEMA.coerce_live(self.live, values or {})
        if errors:
            raise refusal(join(errors, "; "))
        changed = {k: v for k, v in new.items() if self.live.get(k) != v}
        if not changed:
            return ""
        fl = self.fl
        old = dict(self.live)
        if "dye" in changed and new["dye"] == "off":
            srcs = [o["label"] for o in self.objects.values() if o["type"] == "dye_source"]
            if srcs:
                raise refusal(T("the dye cannot be switched off while the scene has its sources: {names}",
                                names=join([T("“{label}”", label=x) for x in srcs], ", ")),
                              hint=T("remove them from the scene first"))
        if "nu" in changed:
            try:
                fl._check_numbers(float(new["nu"]), fl.u_max)
            except ValueError as e:
                raise self._ru(e) from e
        D_new = (float(new["dye_D"]) or float(new["nu"])) if new["dye"] == "on" else None
        try:
            if "nu" in changed:
                fl.set_viscosity(float(new["nu"]))
            if "rho" in changed:
                fl.set_density(float(new["rho"]))
            if "collision" in changed:
                fl.set_collision(new["collision"])
            if D_new is None and self.D is not None:
                fl.disable_dye()
            elif D_new is not None and D_new != self.D:
                fl.set_dye_diffusivity(D_new)   # switches it on (zero) when it was off
        except ValueError as e:
            self._live_back(old)
            raise self._ru(e) from e
        self.nu, self.rho = float(new["nu"]), float(new["rho"])
        regrid = ""
        if any(k in changed for k in GRID):
            try:
                regrid = self._regrid(new, old)
            except Exception:
                self.nu, self.rho = float(old["nu"]), float(old["rho"])
                self._live_back(old)
                raise
            changed = {k: new[k] for k in changed if k not in GRID or new[k] != old[k]}
        self.live, self.D = dict(new), D_new
        if self.D is None and self.shown == "dye":
            self.shown = "speed"
        self._record_setup()
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})
        self.emit_picture()

        def show(k, v):
            p = SCHEMA.by_id[k]
            if p.options:
                return T("{label} = {value}", label=p.label, value=dict(p.options).get(v, v))
            if p.type == "int":
                return T("{label} = {value:d}", label=p.label, value=int(v))
            return T("{label} = {value:.2g}", label=p.label, value=float(v))
        labels = join([show(k, v) for k, v in changed.items()], ", ")
        what = []
        if "nu" in changed:
            what.append(T("velocity and pressure stay, the viscous stress adjusts within a few steps"))
        if "rho" in changed:
            what.append(T("pressures and forces on the scale of ρ (×{k:.3g})", k=float(new["rho"]) / float(old["rho"])))
        if "dye" in changed:
            what.append(T("the dye is off (its amount is booked as removed)") if D_new is None
                        else T("the dye is on (zero so far)"))
        if regrid:
            what.append(regrid)
        return T("laws on the fly: {labels}{what}; the window of the mean forces restarts", labels=labels,
                 what=T("; {list}", list=join(what, "; ")) if what else "")

    def _anchor_shift(self, anchor, grow, dx):
        """Where the present domain's origin lands in the new one (m) when it grows by ``grow`` (m, < 0: shrinks)."""
        if anchor == "left_bottom":
            return grow
        if anchor == "center":
            return round(0.5 * grow / dx) * dx
        return 0.0

    def _regrid(self, new, old):
        """The grid (nx), the domain (Lx, Ly) and the largest expected speed (u_max) changed now (plan P16.1): the flow
        goes on on the new grid or time step (``Flow2D.remap``: the pre-collision populations' pressure, velocity and
        non-equilibrium part moved to the new nodes, the latter rescaled with the relaxation times — Dupuis & Chopard's
        grid-refinement transfer; a new part of the domain at rest or with the inflow, as chosen; the bodies
        re-voxelised). A change of nx changes the spacing (dx = Lx / nx); a change of Lx or Ly keeps it (cells added or
        cut at the side ``anchor`` names; objects keep their place in the fluid, so with the left or the middle anchor
        their coordinates move). Refused, with the world as it was: a grid beyond the memory budget, a domain that would
        cut a body, a dye source or leave a probe outside, a grid or time step the scheme cannot run. ``new`` gets the
        values in force (the domain rounded to whole cells). Returns the event's text: the grids, the time steps, the
        mass and momentum before and after and what the transfer changed."""
        fl = self.fl
        dx0, (Lx0, Ly0) = fl.units.dx, self.size
        Lx_req, Ly_req = float(new["Lx"]), float(new["Ly"])
        if new["nx"] != old["nx"]:
            dx1 = Lx_req / int(new["nx"])
        else:
            dx1 = dx0
        nx1 = max(2, int(round(Lx_req / dx1)))
        ny1 = max(8, int(round(Ly_req / dx1)))
        Lx1, Ly1 = nx1 * dx1, ny1 * dx1
        sx = self._anchor_shift(new["anchor"], Lx1 - Lx0, dx1)
        sy = self._anchor_shift(new["anchor"], Ly1 - Ly0, dx1)
        um = float(new["u_max"])
        dye = self.D is not None
        need = L.Flow2D.memory_estimate(nx1, ny1, dye)
        budget = _budget()
        if need > budget:
            raise refusal(T("a grid of {nx:d} × {ny:d} nodes (spacing {dx:.2g} m) would need ≈ {need} of memory, above "
                            "the limit of {budget}", nx=nx1, ny=ny1, dx=dx1, need=_fmt_bytes(need),
                            budget=_fmt_bytes(budget)), hint=self._grid_hint({"Lx": Lx1, "Ly": Ly1, "nx": nx1,
                                                                               "dye": "on" if dye else "off"}, budget))
        try:
            from lfviz import limits
            limits.require(fl.remap_memory_estimate(nx1, ny1),
                           T("moving the flow to a grid of {nx:d} × {ny:d} nodes", nx=nx1, ny=ny1),
                           T("fewer nodes or a smaller domain"))
        except ImportError:  # an older framework without limits: the estimate above holds
            pass
        for o in self.objects.values():  # probes and dye drops must stay in the fluid (the engine checks the sources)
            if o["type"] in ("probe", "dye_source"):
                x, y = float(o["values"]["x"]) + sx, float(o["values"]["y"]) + sy
                if not (0.0 <= x <= Lx1 and 0.0 <= y <= Ly1):
                    raise refusal(T("“{label}” would be outside the new domain of {lx:.2g} × {ly:.2g} m",
                                    label=o["label"], lx=Lx1, ly=Ly1),
                                  hint=T("move or remove it, or shrink the domain on the other side"))
        inflow = any(isinstance(v, L.Inlet) for v in fl._sides.values())
        dfg0 = self._dfg_case()
        # the pressure integral now: the transfer keeps the pressure, so the scheme's density deviation p / c_s^2 (and the
        # lattice mass with it) changes with the scheme's sound speed (review LB1-p02-ux X14)
        Ip = float(np.nansum(fl.fields()["p"])) * dx0 * dx0
        cs0 = fl.units.c * L.CS
        try:
            rep = fl.remap(dx=dx1, size=(Lx1, Ly1), shift=(sx, sy), u_max=um, fill=new["fill"])
        except ValueError as e:
            raise self._ru(e) from e
        moved = sx != 0.0 or sy != 0.0
        if moved:
            for o in self.objects.values():
                if "x" in o["values"] and "y" in o["values"]:
                    o["values"] = {**o["values"], "x": float(o["values"]["x"]) + sx, "y": float(o["values"]["y"]) + sy}
        self.size = fl.size
        self.u_max = um
        if um != float(old["u_max"]):
            self.u_note = None
        new.update(Lx=fl.size[0], Ly=fl.size[1], nx=fl.nx, u_max=um)
        self.PALETTE = palette(self.size, self.u_max, self._g_default())
        h = 0.04 * max(self.size)
        self.emit({"type": "box", "t": self.t, "box": [[0.0, 0.0, -h], [self.size[0], self.size[1], h]]})
        self._shapes()
        if moved:
            self.rev += 1
            self.emit_scene()
        b, a, tr = rep["before"], rep["after"], rep["transfer"]

        def mom(v):
            return T("({x:.4g}, {y:.4g})", x=float(v[0]), y=float(v[1]))
        parts = [T("grid {nx0:d} × {ny0:d} → {nx1:d} × {ny1:d} nodes (spacing {dx0:.2g} → {dx1:.2g} m), time step "
                   "{dt0:.2g} → {dt1:.2g} s (τ {tau0:.3g} → {tau1:.3g})", nx0=int(b["nodes"][0]),
                   ny0=int(b["nodes"][1]), nx1=int(a["nodes"][0]), ny1=int(a["nodes"][1]), dx0=b["dx"], dx1=a["dx"],
                   dt0=b["dt"], dt1=a["dt"], tau0=b["tau_plus"], tau1=a["tau_plus"])]
        if rep["new_part"] > 0:
            how = T("with the inflow") if rep["fill"] == "inflow" else (
                T("at rest (there is no inlet: at rest)") if new["fill"] == "inflow" and not inflow else T("fluid at rest"))
            parts.append(T("the new part of the domain ({pct:.2g} %): {how}", pct=100 * rep["new_part"], how=how))
        if moved:
            parts.append(T("the domain grew or shrank {where}: the coordinates of the bodies, the dye and the probes "
                           "shifted by ({sx:.4g}, {sy:.4g}) m with the fluid", where=ANCHOR_NAME[new["anchor"]],
                           sx=sx, sy=sy))
        if new["nx"] != old["nx"] and not math.isclose(Ly1, Ly_req, rel_tol=1e-9):
            keep = self._nx_keeping(Lx_req, Ly_req, int(new["nx"]))
            parts.append(T("domain height {a:.6g} → {b:.6g} m: at a spacing of {dx:.4g} m a whole number of cells fits "
                           "along y ({ny:d}){keep}", a=Ly_req, b=Ly1, dx=dx1, ny=ny1,
                           keep=T("; both lengths are kept by nx = {list}", list=", ".join(map(str, keep)))
                           if keep else ""))
        if dfg0 and not self._dfg_case():
            parts.append(T("the DFG set-up is no longer recognised (the channel's sizes changed): its “Benchmarks” are "
                           "not shown"))
        cs1 = fl.units.c * L.CS
        dm_cs = Ip * (1.0 / cs1**2 - 1.0 / cs0**2)
        m_inc = self.rho * float(np.sum(~fl.solid())) * fl.units.dx ** 2
        parts.append(T("mass {m0:.6g} → {m1:.6g} kg/m, momentum {p0} → {p1} kg/(m·s); the transfer changed the mass by "
                       "{dm:.3g} kg/m ({pct:.3g} %) and the momentum by {dp}", m0=b["mass"], m1=a["mass"],
                       p0=mom(b["momentum"]), p1=mom(a["momentum"]), dm=tr["mass"],
                       pct=100 * tr["mass"] / b["mass"], dp=mom(tr["momentum"])))
        why = []
        if not math.isclose(cs1, cs0, rel_tol=1e-9):
            why.append(T("{dm:.3g} kg/m: the compressibility of the scheme, not of the fluid: the pressure was moved as "
                         "it was, the scheme's density at the same pressure is ρ − ρ₀ = p/c_s², and the scheme's speed "
                         "of sound (u_max/{ma:.2g}, higher where the step is bound by the relaxation time) changed "
                         "{cs0:.4g} → {cs1:.4g} m/s", dm=dm_cs, ma=fl.mach_target, cs0=cs0, cs1=cs1))
        if rep["new_part"] > 0:
            why.append(T("≈ {dm:.3g} kg/m: the fluid of the new part of the domain",
                         dm=self.rho * rep["new_part"] * fl.size[0] * fl.size[1]))
        if b["nodes"] != a["nodes"]:
            why.append(T("the rest: the interpolation to the new nodes and the bodies laid out on the nodes again"))
        if why:
            parts.append(T("of this {list}; the mass of the incompressible fluid ρ·S = {m:.6g} kg/m",
                           list=join(why, "; "), m=m_inc))
        parts.append(T("the transfer is booked in the balances as “transfer” (remap): the balance checks close by "
                       "construction and do not see the error of the transfer itself; its accuracy is in the engine's "
                       "tests (Poiseuille to rounding, Taylor–Green to the scheme's accuracy) and in this world's "
                       "“Benchmarks” (the rest is the flow's step)"))
        parts.append(T("the flow goes on: pressure and velocity moved, the non-equilibrium part of the populations "
                       "rescaled (×{k:.3g}), the transfer took one step of the previous grid",
                       k=rep["factors"]["neq_plus"]))
        return join(parts, "; ")

    @staticmethod
    def _nx_keeping(Lx, Ly, nx):
        """Up to two numbers of nodes along x nearest ``nx`` (within the schema's 16 … 8192) whose spacing Lx / n fits
        a whole number of cells into Ly too (review LB1-physics P14)."""
        out = []
        for n in sorted(range(16, 8193), key=lambda k: (abs(k - nx), k)):
            m = Ly * n / Lx
            if abs(m - round(m)) <= 1e-9 * max(1.0, m) and round(m) >= 8:
                out.append(n)
                if len(out) == 2:
                    break
        return out

    def _live_back(self, old):
        """Put the engine's live laws back as they were (a later setter of the same change refused)."""
        fl = self.fl
        fl.set_viscosity(float(old["nu"]))
        fl.set_density(float(old["rho"]))
        fl.set_collision(old["collision"])
        D_old = self.D
        if D_old is None:
            if fl.dye_D is not None and not fl.dye_sources():
                fl.disable_dye()
        elif fl.dye_D != D_old:
            fl.set_dye_diffusivity(D_old)

    # --- time ----------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        if t_target > self.fl.t:
            try:
                self.fl.advance_to(t_target)
            except L.Unstable as e:
                raise RuntimeError(T("the flow lost its stability (the world is stopped in its state before the step): "
                                     "{why}. Lower the velocities or raise the “largest expected velocity” in the "
                                     "world's laws (a new world)", why=text_of(e))) from e
        self.t = max(self.t, t_target)

    def max_step(self):
        """At most MAX_STEPS lattice steps per advance call, fewer when the CPU's measured rate (``lbm.RATES``, a fixed
        table: deterministic) makes one call longer than FRAME_S: a large grid keeps the frames and the commands flowing
        (review UX-params P25: one frame of a 4·10⁶-node grid took minutes). The flow does not depend on the cut: the
        engine steps to the step nearest each target."""
        per = L._interp_rate("cpu", self.fl.N)
        return int(min(MAX_STEPS, max(1, FRAME_S / per))) * self.fl.units.dt

    # --- the forces' window ----------------------------------------------------------------------------------------
    def _record_setup(self):
        """The forces are recorded in blocks of 1/``WINDOW_BLOCKS`` of the domain's slowest sound period (whole
        steps); the mean shown is over the last ``WINDOW_BLOCKS`` blocks, i.e. one whole period to within half a block
        (the scheme's standing sound wave averages out: review B7 L4)."""
        ap = self.fl.acoustic_period()
        dt = self.fl.units.dt
        T_steps = ap["period"] / dt
        k = max(1, int(T_steps // WINDOW_BLOCKS))
        n = max(1, int(round(T_steps / k)))
        self.win = {"every": k, "n": n, "period": ap["period"], "axis": ap["axis"],
                    "kind": ap[ap["axis"]]["kind"], "length": ap[ap["axis"]]["length"], "c_s": ap["c_s"]}
        rec = self.fl.force_record()
        if rec is None or rec["every"] != k:
            self.fl.record_forces(k, keep=max(8 * n, 1024))

    def _window(self, eid):
        """The mean force (N/m) on obstacle ``eid`` over the last whole window, with the window; or the time it will be
        ready."""
        r = self.fl.force_record()
        if r is None or self.win is None:
            return None
        n = self.win["n"]
        t = r["t_end"]
        if len(t) < n or eid not in r["obstacles"]:
            return {"ready_at": r["since"] + n * r["block"]}
        F = r["obstacles"][eid]["force"][-n:]
        return {"force": F.mean(axis=0), "t0": float(t[-n] - r["block"]), "t1": float(t[-1])}

    def _window_text(self, w):
        return T("{t0:.4g} … {t1:.4g} s (sound period {kind} = {period:.4g} s, along {axis}, c_s = {cs:.4g} m/s)",
                 t0=w["t0"], t1=w["t1"], kind=KIND_NAME[self.win["kind"]], period=self.win["period"],
                 axis=self.win["axis"], cs=self.win["c_s"])

    def _coeffs(self, F, vec):
        q = 0.5 * self.rho * F["u_ref"] ** 2 * F["length"]
        return (float(vec[0]) / q, float(vec[1]) / q) if q > 0 else (float("nan"), float("nan"))

    # --- frames --------------------------------------------------------------------------------------------------
    def _at(self, x, y):
        fl = self.fl
        i = int(np.clip(np.rint((x - fl.x[0]) / fl.units.dx), 0, fl.nx - 1))
        j = int(np.clip(np.rint((y - fl.y[0]) / fl.units.dx), 0, fl.ny - 1))
        return i, j

    def _body_at(self, i, j):
        for oid, k in self.ref.items():
            if k[0] == "obstacle" and self.fl.shape_mask(self._shape(self.objects[oid]))[i, j]:
                return self.objects[oid]["label"]
        return None

    def frame(self):
        fl = self.fl
        now, probes, ids = {}, {}, []
        rates = fl.flow_rates()
        f = fl.fields()
        om = fl.vorticity()
        dye = fl.dye() if self.D else None
        for oid, kind in self.ref.items():
            o = self.objects[oid]
            if kind[0] == "obstacle" and (F := self._force(oid, kind[1])):
                w = self._window(kind[1])
                r = {}
                if w and "force" in w:
                    cx, cy = self._coeffs(F, w["force"])
                    r.update({"C_x, mean over the sound period": cx, "C_y, mean over the sound period": cy,
                              "drag, mean, N/m": float(w["force"][0]),
                              "lift, mean, N/m": float(w["force"][1]),
                              "averaging window": self._window_text(w)})
                elif w:
                    r["C_x, C_y means over the sound period"] = T("the window is filling: until t = {t:.4g} s",
                                                                   t=w["ready_at"])
                r.update({"C_x over the last step (with the scheme's sound)": F["cd"],
                          "C_y over the last step (with the scheme's sound)": F["cl"],
                          "torque over the last step, N": F["torque"],
                          "Re (by the length and the velocity for the coefficients)": F["u_ref"] * F["length"] / self.nu})
                now[oid] = r
            elif kind[0] == "side":
                now[oid] = {RATE_KEY[sd]: rates.get(sd, 0.0) for sd in kind[1]}
                if o["type"] == "inlet":
                    sc = fl.inlet_scales()
                    now[oid].update({RAMP_KEY[sd]: sc[sd] for sd in kind[1] if sd in sc})
                if o["type"] == "lid":  # Re of a driven cavity: the wall's speed and length
                    side_len = self.size[0] if o["values"]["side"] in ("bottom", "top") else self.size[1]
                    now[oid]["Re = U·L/ν"] = abs(float(o["values"]["speed"])) * side_len / self.nu
            elif kind[0] == "probe":
                i, j = self._at(o["values"]["x"], o["values"]["y"])
                if not math.isfinite(float(f["ux"][i, j])):   # inside a body: no fluid there (UX-params P27)
                    body = self._body_at(i, j)
                    r = {"where": T("inside the body “{label}”: there is no fluid here; move the probe", label=body)
                         if body else T("inside a body: there is no fluid here; move the probe")}
                else:
                    r = {"ux, m/s": float(f["ux"][i, j]), "uy, m/s": float(f["uy"][i, j]),
                         "|u|, m/s": float(math.hypot(f["ux"][i, j], f["uy"][i, j])),
                         "p, Pa": float(f["p"][i, j]), "ω, 1/s": float(om[i, j])}
                    if dye is not None:
                        r["dye"] = float(dye[i, j])
                probes[oid] = r
                ids.append(oid)
        if self.check_due():
            self.checks()
        if self.n_pic % PIC_EVERY == 0:
            self.emit_picture(f, om, dye)
        self.n_pic += 1
        nb = fl.numbers()
        meas, notes = self._meas(f, rates, nb)
        out = {"ids": ids, "now": now, "probes": probes, "steps": int(fl.steps), "re": nb.get("re"),
               "mach": nb.get("mach_max"), "at": self._at_all(), "meas": meas}
        if notes:
            out["meas_note"] = notes
        return out, {}

    # --- positions and measurables (P16.2, P16.3) ----------------------------------------------------------------------
    def _at_all(self):
        """Where every positioned object is (m, the plane z = 0): its handle's x, y (a profile's leading edge)."""
        return {oid: [float(o["values"]["x"]), float(o["values"]["y"]), 0.0] for oid, o in self.objects.items()
                if o["type"] in ("disk", "rect", "airfoil", "dye_source", "probe")}

    def measurables(self):
        """The quantities the instruments record (P16.3): per body its drag and lift coefficients (over the last step and
        averaged over the domain's slowest sound period) and its forces; per probe the velocity and the pressure; per side
        object the mass flow through its side; for the world the balances' residuals, the Reynolds and Mach numbers and
        the net inflow."""
        out = []
        for oid, o in self.objects.items():
            lab, t = o["label"], o["type"]

            def m(key, text, unit, group):
                return {"id": f"{oid}.{key}", "label": T("“{label}”: {what}", label=lab, what=text), "unit": unit,
                        "of": oid, "group": group}
            if t in ("disk", "rect", "airfoil"):
                g = T("Bodies")
                out += [m("cd", T("C_x over the last step (with the scheme's sound)"), "", g),
                        m("cl", T("C_y over the last step (with the scheme's sound)"), "", g),
                        m("cd_mean", T("C_x, mean over the sound period"), "", g),
                        m("cl_mean", T("C_y, mean over the sound period"), "", g),
                        m("fx", T("force along x (drag)"), T("N/m"), g),
                        m("fy", T("force along y (lift)"), T("N/m"), g)]
            elif t == "probe":
                g = T("Probes")
                out += [m("ux", T("velocity u_x"), T("m/s"), g), m("uy", T("velocity u_y"), T("m/s"), g),
                        m("speed", T("speed |u|"), T("m/s"), g), m("p", T("pressure (relative)"), T("Pa"), g)]
            elif t in ("inlet", "outlet", "lid"):
                out.append(m("q", T("mass flow into the domain through the side"), T("kg/(s·m)"), T("Flow rates")))
        out += [{"id": "q_net", "label": T("Total mass flow into the domain (all sides)"), "unit": T("kg/(s·m)"),
                 "of": None, "group": T("Flow rates")},
                {"id": "mass_res", "label": T("Mass balance residual (fraction of the mass)"), "unit": "", "of": None,
                 "group": T("Balances")},
                {"id": "mom_res", "label": T("Momentum balance residual (per lattice mass)"), "unit": "", "of": None,
                 "group": T("Balances")},
                {"id": "re", "label": T("Reynolds number Re (the body's length and the inlet velocity)"), "unit": "",
                 "of": None, "group": T("Numbers")},
                {"id": "mach", "label": T("Lattice Mach number, largest"), "unit": "", "of": None,
                 "group": T("Numbers")}]
        return out

    def measure(self):
        """The measurables' values now (``meas`` of a frame without the picture; the sweeps read it)."""
        fl = self.fl
        return self._meas(fl.fields(), fl.flow_rates(), fl.numbers())[0]

    def _meas(self, f, rates, nb):
        """({measurable id: value in its unit}, {id: why it is undefined}) from the fields, rates and numbers of now."""
        fl = self.fl
        m, notes = {}, {}
        for oid, kind in self.ref.items():
            o = self.objects[oid]
            if kind[0] == "obstacle":
                F = self._force(oid, kind[1])
                if not F:
                    continue
                m[f"{oid}.cd"], m[f"{oid}.cl"] = float(F["cd"]), float(F["cl"])
                m[f"{oid}.fx"], m[f"{oid}.fy"] = float(F["force"][0]), float(F["force"][1])
                w = self._window(kind[1])
                if w and "force" in w:
                    m[f"{oid}.cd_mean"], m[f"{oid}.cl_mean"] = self._coeffs(F, w["force"])
                else:
                    m[f"{oid}.cd_mean"] = m[f"{oid}.cl_mean"] = float("nan")
                    why = (T("the window of the mean over the sound period is filling: until t = {t:.4g} s",
                             t=w["ready_at"]) if w else T("the forces are not being recorded"))
                    notes[f"{oid}.cd_mean"] = notes[f"{oid}.cl_mean"] = why
            elif kind[0] == "probe":
                i, j = self._at(o["values"]["x"], o["values"]["y"])
                vals = (float(f["ux"][i, j]), float(f["uy"][i, j]), float(f["p"][i, j]))
                if all(math.isfinite(v) for v in vals):
                    m[f"{oid}.ux"], m[f"{oid}.uy"], m[f"{oid}.p"] = vals
                    m[f"{oid}.speed"] = math.hypot(vals[0], vals[1])
                else:
                    for k in ("ux", "uy", "speed", "p"):
                        m[f"{oid}.{k}"] = float("nan")
                        notes[f"{oid}.{k}"] = T("the probe is inside a body: there is no fluid here")
            elif kind[0] == "side" and o["type"] in ("inlet", "outlet", "lid"):
                m[f"{oid}.q"] = float(sum(rates.get(sd, 0.0) for sd in kind[1]))
        m["q_net"] = float(sum(rates.values()))
        b = fl.balance()
        m["mass_res"] = float(b["mass"]["relative_residual"])
        m["mom_res"] = float(b["momentum"]["relative_residual"])
        m["re"] = float(nb.get("re") or float("nan"))
        m["mach"] = float(nb.get("mach_max") or 0.0)
        return m, notes

    def emit_picture(self, f=None, om=None, dye=None):
        """The field shown (``view`` op "field"), 8-bit (255 = solid), and the velocity arrows: drawing only."""
        fl = self.fl
        if f is None:
            f, om = fl.fields(), fl.vorticity()
            dye = fl.dye() if self.D else None
        name = self.shown if (self.shown != "dye" or dye is not None) else "speed"
        if name == "speed":
            a = np.hypot(f["ux"], f["uy"])
            lo, hi, note = 0.0, None, T("m/s")
        elif name == "vorticity":
            a, note = om, T("1/s (0: the middle of the scale)")
            lo = hi = None
        elif name == "pressure":
            a, note = f["p"], T("Pa")
            lo = hi = None
        else:
            a, lo, hi, note = dye, 0.0, 1.0, T("fraction")
        a = np.asarray(a, float)
        solid = ~np.isfinite(a)
        fin = a[~solid]
        if name == "vorticity":  # symmetric about zero (the middle of the scale), also for a fluid at rest
            m = (float(np.percentile(np.abs(fin), 99.0)) if fin.size else 0.0) or 1.0
            lo, hi = -m, m
        if lo is None:
            lo = float(fin.min()) if fin.size else 0.0
        if hi is None:
            hi = float(fin.max()) if fin.size else 1.0
        if not hi > lo:
            hi = lo + 1.0
        val, frac = resample(a, ~solid, IMG_MAX)
        img = np.clip((val - lo) / (hi - lo), 0.0, 1.0)
        u8 = np.where(frac < 0.5, 255, np.round(254 * img)).astype(np.uint8)
        self.emit({"type": "field", "t": self.t, "name": name, "label": FIELDS[name], "unit": note,
                   "range": [lo, hi], "shape": list(u8.shape), "size": list(self.size)}, {"img": u8})
        # velocity arrows on a coarse grid (z = 0 plane)
        s = max(1, int(math.ceil(max(fl.nx, fl.ny) / ARROWS)))
        ii, jj = np.meshgrid(np.arange(s // 2, fl.nx, s), np.arange(s // 2, fl.ny, s), indexing="ij")
        ux, uy = f["ux"][ii, jj], f["uy"][ii, jj]
        ok = np.isfinite(ux) & np.isfinite(uy)
        pos = np.stack([fl.x[ii][ok], fl.y[jj][ok], np.full(ok.sum(), 0.01 * self.size[0])], 1)
        vec = np.stack([ux[ok], uy[ok], np.zeros(ok.sum())], 1)
        self.emit({"type": "vectors", "t": self.t, "id": "flow"},
                  {"pos": pos.astype(np.float32).reshape(-1), "vec": vec.astype(np.float32).reshape(-1)})

    def view(self, args):
        if args.get("op") != "field" or args.get("field") not in FIELDS:
            raise refusal(T("the picture's field: speed | vorticity | pressure | dye"))
        self.shown = args["field"]
        self.emit_picture()
        return T("picture: {field}", field=FIELDS[self.shown])

    def view_state(self):
        return {"field": self.shown}

    def adopt_view(self, state):
        if isinstance(state, dict) and state.get("field") in FIELDS:
            self.shown = state["field"]

    # --- checks ----------------------------------------------------------------------------------------------------
    def checks(self):
        fl = self.fl
        cons, appl = T("Conservation laws"), T("Applicability")
        names = {"mass": (T("Fluid mass (balance with inflow and outflow)"), cons),
                 "momentum": (T("Fluid momentum (balance with forces and fluxes)"), cons),
                 "dye": (T("Amount of dye (balance)"), cons),
                 "mach": (T("Lattice Mach number (compressibility error ~ Ma²)"), appl),
                 "re_cell": (T("Cell Reynolds number u·dx/ν (a stability limit, not an accuracy one)"), appl),
                 "compressibility": (T("Density spread (a measure of the compressibility error)"), appl)}
        for key, c in fl.checks().items():
            lab, grp = names.get(key, (key, T("Checks")))
            val = c.get("relative_residual", c.get("value", c.get("residual")))
            conserved = key in ("mass", "momentum", "dye")
            tol = T("tolerance {tol:.3g}", tol=float(c["limit"])) if "limit" in c else ""
            self.running_check(key, lab, val, 0.0 if conserved else None, float(c.get("limit", 0.0) or 0.0),
                               group=grp, ok=c.get("ok"), info="ok" not in c,
                               note=join([tol, c.get("note") or ""], "; "))
        for oid, kind in self.ref.items():
            if kind[0] != "obstacle":
                continue
            F = self._force(oid, kind[1])
            if not F:
                continue
            lab = self.objects[oid]["label"]
            re = F["u_ref"] * F["length"] / self.nu
            basis = T("Re = {re:.4g} (length {l:.4g} m, velocity {u:.4g} m/s); the forces by momentum exchange at the "
                      "wall", re=re, l=F["length"], u=F["u_ref"])
            w = self._window(kind[1])
            if w and "force" in w:
                cx, cy = self._coeffs(F, w["force"])
                self.running_check(f"cd_{oid}", T("“{label}”: C_x, mean over the sound period", label=lab), cx, None,
                                   0.0, info=True, group=T("Forces"),
                                   note=T("mean C_y = {cy:.4g}; window {window}; over the last step C_x = {cd:.4g}, "
                                          "C_y = {cl:.4g} (they carry the scheme's sound wave); {basis}", cy=cy,
                                          window=self._window_text(w), cd=F["cd"], cl=F["cl"], basis=basis))
            else:
                ready = T("; the mean over the sound period is filling until t = {t:.4g} s", t=w["ready_at"]) if w \
                    else ""
                self.running_check(f"cd_{oid}", T("“{label}”: C_x over the last step (instantaneous, with the "
                                                  "scheme's sound)", label=lab),
                                   F["cd"], None, 0.0, info=True, group=T("Forces"),
                                   note=T("C_y = {cl:.4g}{ready}; {basis}", cl=F["cl"], ready=ready, basis=basis))
        self._benchmark_checks()
        c = fl.cost_estimate()
        self.running_check("cost", T("Computation: seconds per step ({device}, estimate)",
                                     device="GPU 0" if c.get("device") == "gpu" else "CPU"),
                           c.get("per_step_s"), None, 0.0, info=True, group=T("Computation"), unit=T("s"),
                           note=T("{nx:d}×{ny:d} nodes, step {dt:.3g} s; the real-time limit ≈ {rate:.3g} s of the "
                                  "world per second (estimated; the measured speed depends on the wall clock: it is at "
                                  "the speed slider)", nx=fl.nx, ny=fl.ny, dt=fl.units.dt,
                                  rate=fl.units.dt / c["per_step_s"]))

    def _force(self, oid, eid):
        """Forces on an obstacle with its own reference speed (the object's u_ref, else the engine's)."""
        u = float(self.objects[oid]["values"].get("u_ref", 0.0) or 0.0)
        return self.fl.forces(u_ref=u if u > 0 else None).get(eid)

    # --- the published benchmarks, where the scene is their set-up (review B7 L5) -------------------------------------
    def _objs(self, typ):
        return [o for o in self.objects.values() if o["type"] == typ]

    def _plain_sides(self, **want):
        """The sides are of the kinds ``want`` (side -> kind) and fixed walls elsewhere."""
        sd = self.fl.sides()
        for name in L.SIDES:
            k = want.get(name, "wall")
            if sd[name]["kind"] != k or (name not in want and sd[name]["velocity"] != 0.0):
                return False
        return True

    def _dfg_case(self):
        """("2D-1" | "2D-2", scene id, engine id) when the world is the DFG cylinder channel of Schäfer & Turek: their
        fluid and channel, a parabolic inlet of Um 0.3 or 1.5 m/s on the left, an outlet at 0 Pa on the right, plain
        walls, one fixed disk of D = 0.1 m at (0.2, 0.2), no body force."""
        G = L.DFG_GEOMETRY
        if not (math.isclose(self.nu, G["nu"], rel_tol=1e-12) and math.isclose(self.rho, G["rho"], rel_tol=1e-12)):
            return None
        if not (math.isclose(self.size[0], G["Lx"], rel_tol=1e-9) and math.isclose(self.size[1], G["H"],
                                                                                    rel_tol=1e-9)):
            return None
        if not self._plain_sides(left="inlet", right="outlet") or self._objs("gravity"):
            return None
        sd = self.fl.sides()
        inl, out = sd["left"], sd["right"]
        if inl.get("profile") != "parabolic" or inl.get("tangential") or out["pressure"] != 0.0:
            return None
        obs = [(k, v) for k, v in self.ref.items() if v[0] == "obstacle"]
        if len(obs) != 1 or self.objects[obs[0][0]]["type"] != "disk":
            return None
        v = self.objects[obs[0][0]]["values"]
        if (v["x"], v["y"], 2 * v["radius"]) != (G["center"][0], G["center"][1], G["D"]) or v["vx"] or v["vy"] \
                or v["omega"]:
            return None
        for case, ref in (("2D-1", L.DFG_2D1), ("2D-2", L.DFG_2D2)):
            if inl["velocity"] == ref["Um"]:
                return case, obs[0][0], obs[0][1][1]
        return None

    def _range_note(self, value, lo, hi, source):
        if lo <= value <= hi:
            return T("the range of {source}: {lo:.4f} … {hi:.4f}; the value is inside", source=source, lo=lo, hi=hi)
        return T("the range of {source}: {lo:.4f} … {hi:.4f}; the value is outside", source=source, lo=lo, hi=hi)

    def _benchmark_checks(self):
        fl = self.fl
        case = self._dfg_case()
        if case and min(fl.inlet_scales().values() or [1.0]) >= 1.0:
            name, oid, eid = case
            G = L.DFG_GEOMETRY
            Um = L.DFG_2D1["Um"] if name == "2D-1" else L.DFG_2D2["Um"]
            q = 0.5 * G["rho"] * (2 * Um / 3) ** 2 * G["D"]  # their U = 2 Um / 3 and D
            interp = self.objects[oid]["values"].get("wall") == "interpolated"
            cells = G["D"] / fl.units.dx
            grid = T("grid: D = {cells:.4g} cells, {wall}; C = 2F/(ρU²D), U = 2Um/3 = {u:.4g} m/s", cells=cells,
                     wall=T("an interpolated wall") if interp else T("a staircase wall"), u=2 * Um / 3)
            if name == "2D-1":
                w = self._window(eid)
                if w and "force" in w:
                    known = T("the engine in this set-up (Ma 0.1 at Um, a start-up of 3 s; windows after 24 s): "
                              "interpolated D = 20: 5.5895 / 0.010504, D = 40: 5.5791 / 0.010770, inside; staircase "
                              "D = 20: ≈ 5.637 / 0.0113, outside; while the start's sound decays (≈ 40 % per period), "
                              "the mean over one period deviates from the steady one by up to ±0.007 at 14 s and "
                              "±0.002 at 20 s")
                    for key, lab, val in (("cD", "C_D", w["force"][0] / q), ("cL", "C_L", w["force"][1] / q)):
                        lo, hi = L.DFG_2D1[key]
                        self.running_check(f"dfg_{key}", T("DFG 2D-1: {c}, mean over the sound period", c=lab), val,
                                           0.5 * (lo + hi), 0.0, info=True, group=T("Benchmarks"),
                                           note=T("{range}; window {window}; {grid}; {known}",
                                                  range=self._range_note(val, lo, hi,
                                                                         T("Schäfer & Turek 1996, table 3")),
                                                  window=self._window_text(w), grid=grid, known=known))
            else:
                r = fl.force_record()
                n = self.win["n"]
                if r is not None and eid in r["obstacles"] and len(r["t_end"]) >= n:
                    m = min(len(r["t_end"]), 4 * n)  # St over the last four sound periods (~5 shedding periods)
                    t = (r["t_end"] - 0.5 * r["block"])[-m:]
                    Fr = r["obstacles"][eid]["force"]
                    cd, cl = Fr[:, 0] / q, Fr[:, 1] / q
                    c = cl[-m:] - cl[-m:].mean()
                    up = np.flatnonzero((c[:-1] < 0) & (c[1:] >= 0))
                    win = T("from the means over blocks of {ms:.3g} ms: C_D max and C_L max over the last sound "
                            "period ({n:d} blocks), St over the last sound periods ({m:d} blocks, from t = {t:.4g} s)",
                            ms=r["block"] * 1e3, n=n, m=m, t=t[0] - 0.5 * r["block"])
                    known = T("the engine's test (Ma 0.1, interpolated, 9–12 s): D = 20: St 0.2990, C_D max 3.330, "
                              "C_L max 0.979; D = 40: St 0.3009, C_D max 3.248, C_L max 0.980 (C_L max and C_D max are "
                              "outside the ranges, the cause is open: STATUS)")
                    vals = [("cDmax", T("C_D max over the last sound period"), float(cd[-n:].max())),
                            ("cLmax", T("C_L max over the last sound period"), float(cl[-n:].max()))]
                    if len(up) >= 3:
                        tz = t[up] - c[up] * (t[up + 1] - t[up]) / (c[up + 1] - c[up])
                        vals.append(("St", T("St = f D / U ({n:d} periods of C_L)", n=len(up) - 1),
                                     G["D"] * (len(tz) - 1) / (tz[-1] - tz[0]) / (2 * Um / 3)))
                    for key, lab, val in vals:
                        lo, hi = L.DFG_2D2[key]
                        self.running_check(f"dfg_{key}", T("DFG 2D-2: {what}", what=lab), val, 0.5 * (lo + hi), 0.0,
                                           info=True, group=T("Benchmarks"),
                                           note=T("{range}; {win}; {grid}; {known}; a developed street is needed "
                                                  "(≳ 5 s)", range=self._range_note(val, lo, hi,
                                                                                     T("Schäfer & Turek 1996, table 4")),
                                                  win=win, grid=grid, known=known))
        self._ghia_check()
        self._poiseuille_checks()
        self._force_poiseuille_check()
        self._couette_check()

    def _ghia_check(self):
        """The driven cavity of Ghia, Ghia & Shin at Re = 100: a square, a lid on top moving along +x, plain walls, no
        obstacles and no body force; the centre-line profiles against their tables."""
        fl = self.fl
        lids = self._objs("lid")
        if fl.nx != fl.ny or len(lids) != 1 or self._objs("gravity") or any(v[0] == "obstacle"
                                                                              for v in self.ref.values()):
            return
        sd = fl.sides()
        if not self._plain_sides(top="wall") or sd["top"]["velocity"] <= 0.0:
            return
        sd_ok = all(sd[k]["velocity"] == 0.0 for k in ("left", "right", "bottom"))
        U, Lc = sd["top"]["velocity"], self.size[0]
        if not sd_ok or not math.isclose(U * Lc / self.nu, 100.0, rel_tol=1e-9):
            return
        ux, uy = fl.velocity()
        n = fl.nx
        i = n // 2
        yy = fl.y / Lc
        if n % 2 == 0:  # the centre line half-way between two columns
            ucol, vrow = 0.5 * (ux[i - 1] + ux[i]), 0.5 * (uy[:, i - 1] + uy[:, i])
        else:
            ucol, vrow = ux[i], uy[:, i]
        ye = np.concatenate([[0.0], yy, [1.0]])
        u = np.interp(L.GHIA_Y, ye, np.concatenate([[0.0], ucol / U, [1.0]]))
        v = np.interp(L.GHIA_X, ye, np.concatenate([[0.0], vrow / U, [0.0]]))
        du = float(np.max(np.abs(u - np.array(L.GHIA_U100))[1:-1]))
        dv = float(np.max(np.abs(v - np.array(L.GHIA_V100))[1:-1]))
        known = T("grid {n:d}²; the engine's test on 64²–256²: 0.005 (u) and 0.008 (v), not decreasing with the grid "
                  "(the difference from Ghia's 129² solution); a steady flow is needed (≈ 25 L/U = {t:.3g} s); the "
                  "tables from two agreeing reprints", n=n, t=25 * Lc / U)
        self.running_check("ghia_u", T("Ghia 1982, Re = 100: max |u − u_Ghia| / U on the vertical axis"), du, None,
                           0.0, info=True, group=T("Benchmarks"),
                           note=T("15 points of table I; {known}", known=known))
        self.running_check("ghia_v", T("Ghia 1982, Re = 100: max |v − v_Ghia| / U on the horizontal axis"), dv, None,
                           0.0, info=True, group=T("Benchmarks"),
                           note=T("15 points of table II; {known}", known=known))

    def _poiseuille_checks(self):
        """A channel with a parabolic inlet on the left and an outlet on the right between plain walls, no body force:
        at each probe at least 2 H from the inlet and 2 H upstream of every obstacle, the velocity profile of its
        column against the inflow's parabola 4 Um y (H - y) / H^2."""
        fl = self.fl
        if not self._plain_sides(left="inlet", right="outlet") or self._objs("gravity"):
            return
        inl = fl.sides()["left"]
        if inl.get("profile") != "parabolic" or inl.get("tangential") or fl.inlet_scales().get("left", 1.0) < 1.0:
            return
        H, Um = self.size[1], inl["velocity"]
        starts = [float(np.min(self._outline(o)[:, 0])) for o in self.objects.values()
                  if o["type"] in ("disk", "rect", "airfoil")]
        ux, uy = fl.velocity()
        for oid, kind in self.ref.items():
            if kind[0] != "probe":
                continue
            x = self.objects[oid]["values"]["x"]
            if x < 2 * H or any(s < x + 2 * H for s in starts):
                continue
            i, _ = self._at(x, 0.0)
            exact = 4 * Um * fl.y * (H - fl.y) / H**2
            ok = np.isfinite(ux[i])
            d = float(np.max(np.abs(ux[i][ok] - exact[ok]))) / Um
            dvy = float(np.max(np.abs(uy[i][ok]))) / Um
            dr = fl.numbers()["density_range"]
            self.running_check(f"pois_{oid}", T("Poiseuille at “{label}”: max |u − u_P| / Um",
                                                label=self.objects[oid]["label"]), d,
                               None, 0.0, info=True, group=T("Benchmarks"),
                               note=T("u_P = 4 Um y (H − y)/H², Um = {um:.4g} m/s, H = {h:.4g} m, x = {x:.4g} m; "
                                      "max |v| / Um = {dv:.3g}; the reference is the developed flow of an "
                                      "incompressible fluid: the difference includes the compressibility error (the "
                                      "flux ρu is conserved while the density falls with the pressure along the "
                                      "channel: now {r0:.4g} … {r1:.4g}) and the trace of the inlet (STATUS V41 m); "
                                      "the engine's test: a channel with a force and periodic ends, a parabola to "
                                      "rounding", um=Um, h=H, x=float(fl.x[i]), dv=dvy, r0=float(dr[0]),
                                      r1=float(dr[1])))

    def _force_poiseuille_check(self):
        """Poiseuille flow driven by a body force (review LB1-physics P7: a reference a wrong transfer to a new grid breaks,
        which the balances cannot see): periodic along x, fixed plain walls at the bottom and the top, a body force gx
        along x only, no bodies: the profile averaged along x against the steady u = gx y (H − y) / (2 ν)."""
        fl = self.fl
        sd = fl.sides()
        if sd["left"]["kind"] != "periodic" or any(v[0] == "obstacle" for v in self.ref.values()):
            return
        if not all(sd[k]["kind"] == "wall" and sd[k]["velocity"] == 0.0 for k in ("bottom", "top")):
            return
        gx, gy = fl.gravity
        if gx == 0.0 or gy != 0.0:
            return
        H = self.size[1]
        exact = gx * fl.y * (H - fl.y) / (2 * self.nu)
        peak = abs(gx) * H * H / (8 * self.nu)
        u = np.nanmean(fl.velocity()[0], axis=0)
        d = float(np.max(np.abs(u - exact))) / peak
        self.running_check("pois_force", T("Poiseuille under a body force: max |u − u_P| / u_max (mean along x)"), d,
                           None, 0.0, info=True, group=T("Benchmarks"),
                           note=T("u_P = g_x y (H − y)/(2ν), g_x = {gx:.4g} m/s², H = {h:.4g} m, u_max = {peak:.4g} "
                                  "m/s; the reference is the steady profile: the difference decays as exp(−π²νt/H²), "
                                  "the time H²/ν = {tv:.4g} s; the engine's test: a parabola to rounding, also after a "
                                  "change of the grid, the domain and the step (a wrong transfer to a new grid shows "
                                  "here, while the balances do not see it)", gx=gx, h=H, peak=peak,
                                  tv=H ** 2 / self.nu))

    def _couette_check(self):
        """Plane Couette flow: periodic along x, one wall (bottom or top) moving along +x at U and the other fixed, no
        bodies and no body force: the profile averaged along x against the steady u = U y / H (or U (H - y) / H)."""
        fl = self.fl
        sd = fl.sides()
        if sd["left"]["kind"] != "periodic" or self._objs("gravity") or any(v[0] == "obstacle"
                                                                              for v in self.ref.values()):
            return
        if sd["bottom"]["kind"] != "wall" or sd["top"]["kind"] != "wall":
            return
        ub, ut = sd["bottom"]["velocity"], sd["top"]["velocity"]
        if (ub == 0.0) == (ut == 0.0):
            return
        U, H = (ut or ub), self.size[1]
        exact = U * (fl.y / H if ut else (H - fl.y) / H)
        u = np.nanmean(fl.velocity()[0], axis=0)
        d = float(np.max(np.abs(u - exact))) / abs(U)
        t_visc = H**2 / self.nu
        self.running_check("couette", T("Couette: max |u − U·y/H| / U (mean along x)"), d, None, 0.0, info=True,
                           group=T("Benchmarks"),
                           note=T("U = {u:.4g} m/s, H = {h:.4g} m; the reference is the steady linear profile: the "
                                  "difference decays as exp(−π²νt/H²), the time H²/ν = {tv:.4g} s; the engine's test: "
                                  "a linear profile to rounding (1e-11), the start-up by the series, second order in "
                                  "the grid", u=U, h=H, tv=t_visc))

    # --- header and drawing ------------------------------------------------------------------------------------------
    def _shapes(self):
        items = []
        for oid, kind in self.ref.items():
            o = self.objects.get(oid)
            if o is None:
                continue
            base = {"id": oid, "label": o["label"], "type": o["type"]}
            if kind[0] == "obstacle":
                P = self._outline(o)
                items.append({**base, "shape": "polygon", "pts": [[float(a), float(b)] for a, b in P],
                              "color": COLORS["obstacle"]})
            elif kind[0] == "side":
                items.append({**base, "shape": "sides", "sides": list(kind[1]), "color": COLORS[o["type"]]})
            elif kind[0] in ("dye", "drop"):
                v = o["values"]
                items.append({**base, "shape": "circle", "c": [v["x"], v["y"]], "r": v["radius"],
                              "color": COLORS["dye"]})
            elif kind[0] == "probe":
                v = o["values"]
                items.append({**base, "shape": "point", "c": [v["x"], v["y"]], "color": COLORS["probe"]})
        self.emit({"type": "shapes", "t": self.t, "items": items, "size": list(self.size)})

    def rekey(self):
        self.emit_picture()

    def header(self):
        Lx, Ly = self.size
        h = 0.04 * max(Lx, Ly)
        fl = self.fl
        nb = fl.numbers()
        return {
            "title": T("Playground: fluids"),
            "text": T("The flow of an incompressible fluid in a plane: the lattice Boltzmann method solves the "
                      "Navier–Stokes equations. Add obstacles, inlets and outlets, moving walls, dye and probes at the "
                      "current moment; the forces on the bodies and the balances are computed live."),
            "actions": [],
            "approximations": self._approx(),
            "scene3d": {"box": [[0.0, 0.0, -h], [Lx, Ly, h]], "units": "m", "up": [0, 0, 1],
                        "objects": [{"id": "field", "label": T("Flow field (picture)"), "kind": "panel",
                                     "origin": [0.0, 0.0, 0.0], "u": [Lx, 0.0, 0.0], "v": [0.0, Ly, 0.0],
                                     "visible": True}],
                        "layers": [{"id": "flow", "label": T("Velocity (arrows)"), "kind": "vectors", "visible": False}],
                        "coord_names": ["x", "y", "z"],
                        "planes": {"max": 0, "center": [0.5 * Lx, 0.5 * Ly, 0.0], "defaults": {"1": [0, 0, 1]}}},
            "grid": {"nx": fl.nx, "ny": fl.ny, "dx": fl.units.dx, "dt": fl.units.dt, "size": [Lx, Ly]},
            "fluid": {"rho": self.rho, "nu": self.nu, "dye_D": self.D},
            "fields": FIELDS, "shown": self.shown,
            "numbers": nb,
            "playground": self.playground_header(),
            "modifications": SCHEMA.modifications(self.params),
        }, {}

    def _approx(self):
        out = [T("an incompressible fluid in a plane (2-D, per metre of depth): the lattice Boltzmann method D2Q9; "
                 "compressibility error ~ Ma² (lattice Mach number ≈ 0.1)"),
               T("the scheme's sound waves (speed of sound c_s = u_max/0.1, a property of the computation): a standing "
                 "wave O(Ma²) in the forces and the pressure, larger after abrupt changes; the means over the sound "
                 "period do not carry it"),
               T("walls: half-way bounce-back (curved walls as a staircase: first order in the shape) or with "
                 "Bouzidi's interpolation (for bodies with that choice)"),
               T("the dye is a passive tracer (it does not affect the flow); its diffusivity equals the viscosity "
                 "(Schmidt number 1) unless set") if self.D else
               T("the dye is a passive tracer (it does not affect the flow)"),
               T("turbulence is not modelled separately: at high Re the grid must resolve all eddies (otherwise the "
                 "world stops itself with the reason); the limits of the cell Reynolds number are stability limits, "
                 "not accuracy ones")]
        if self.u_note:
            out.append(self.u_note)
        fl0 = self.params["fluid"]
        nu0, rho0 = ((float(self.params["nu"]), float(self.params["rho"])) if fl0 == "custom" else
                     (1e-3, 1.0) if fl0 == "dfg" else
                     (float(L.FLUIDS["water_20C" if fl0 == "water" else "air_20C"]["nu"]),
                      float(L.FLUIDS["water_20C" if fl0 == "water" else "air_20C"]["rho"])))
        if not (math.isclose(self.nu, nu0, rel_tol=1e-12) and math.isclose(self.rho, rho0, rel_tol=1e-12)):
            out.append(T("the fluid was changed on the fly: ν = {nu:.2g} m²/s, ρ = {rho:.2g} kg/m³ (at the start: "
                         "{fluid})", nu=self.nu, rho=self.rho, fluid=FLUIDS_NAME[fl0]))
        per = L._interp_rate(self.fl.device if self.fl.device in ("cpu", "gpu") else "cpu", self.fl.N)
        if per > 0.25:
            out.append(T("a large grid ({nx:d} × {ny:d}): a step takes ≈ {s:.2g} s, the world runs slowly; fewer nodes "
                         "are faster", nx=self.fl.nx, ny=self.fl.ny, s=per))
        bodies = [o for o in self.objects.values() if o["type"] in ("disk", "rect", "airfoil")]
        if any(o["values"].get("vx") or o["values"].get("vy") or o["values"].get("omega") for o in bodies):
            out.append(T("bodies with a moving surface stay in place: a surface velocity is set on a fixed shape (its "
                         "normal part is a source and a sink), not the motion of the body"))
        sd = self.fl.sides()
        if bodies and any(sd[k]["kind"] == "periodic" for k in L.SIDES):
            out.append(T("periodicity: the bodies repeat with the domain's pitch (a lattice of bodies), not a single "
                         "body in an unbounded stream"))
        return out

    def engine_modules(self):
        return ["lfphys.core.fluids.lbm"]


VIZ = {
    "id": "p04_fluids",
    "title": T("Fluids"),
    "summary": T("A flow sandbox: obstacles, wings, inlets and outlets, moving walls, dye; an incompressible fluid by "
                 "the lattice Boltzmann method."),
    "purpose": T("Build a flow and see what comes of it: flow past bodies, separation, the Kármán street, the vortex in "
                 "a cavity, the lift of a wing, the mixing of dye; forces and balances live."),
    "version": "0.2",
    "schema": SCHEMA,
    "simulation": Simulation,
    "kind": "playground",
    "section": "fluids",
}
