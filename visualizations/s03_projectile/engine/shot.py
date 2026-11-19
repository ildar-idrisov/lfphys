# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""One thrown ball: its flight computed by the engine with the real forces, sampled for drawing, with the references
of its checks and the comparisons the drawer states (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §10,
§11 items 25, 39–42; the engine's forces and their sources: ``lfphys/sources/s03_forces_2026-11-18.md``).

Orchestration only (``RULES.md`` §1, ``lfphys/LAYERS.md``): the physics is the engine's.

* **The flight** is ``lfphys.core.mechanics.fly``: Newton's second law in the uniform field g_n (DOP853, the landing and
  the apex located by the integrator, the work of every force carried in the state).
* **The rotating Earth.** The bench stands at sea level at 45.4996° N, where the WGS 84 normal gravity equals the
  standard g_n the engine uses (``earth_frame.latitude_for_gravity``), and every throw goes toward the east: each
  flight carries the Coriolis force's part in the throw's vertical plane (``earth_frame.Coriolis``, azimuth 90°), and
  the offset out of the plane, to the right (south), is computed along the flight by its own first-order equation
  (``earth_frame.sideways``).
* **The air** (when it is on): the measured drag curve of a smooth sphere at the ball's own Reynolds number
  (``drag_quadratic.CurveDrag``, Morrison 2016), and the ball as a body in a fluid at rest (``particle.Medium.air``: the
  buoyancy and the added mass, C_A = ½). Dry air at 20 °C and 101 325 Pa (``core.data``).
* **The spin.** The steel ball launched horizontally from a height leaves a chute: it rolls off without slipping, with
  topspin ω = v₀/R (150 rad/s at 1.5 m/s). In air it then feels the Magnus force and the spin's increase of its drag
  (``theories.models.magnus``: Zhou, Zhang & Xu 2022, measured to Re 3 472, with the stated band C_L × [0.825, 1.230],
  the drag's factor × [0.917, 1.084]); the spin is taken as constant (its decay is not computed: ≤ 7 % over the flight,
  ≤ 0.010 mm on the range, ``s03_forces`` §5). Every other launch (the launcher, a throw, a drop, the light ball) leaves
  without spin, a stated launch condition. The measured data of a spinning ball cover Re ≤ 10⁴: a rolling ball in air
  that would fly faster than that is refused (``spin_speed_limit``).
* **The history force** is not a force of the flight: its upper bound by Basset's kernel along the flight
  (``drag.history_bound``) is a drawer value.

The references (``Shot.references``): the second method is the flight's equations in its velocity's angle
(``drag_quadratic.angle_flight``: the drag curve, the spin's drag, the buoyancy, the added mass, the Magnus force and the
Coriolis force's planar part, assembled independently of ``fly``'s declared forces). A vertical flight (thrown straight
up or dropped) has no velocity's angle to integrate in: in vacuum its time and height are the closed forms of a fall,
which the Earth's rotation changes only at second order, (Ω_z·T)²; in air the engine has no second method for it (the
energy balance checks it); its drift east or west is checked against the same flight's drift by its own first-order
equation (``earth_frame.sideways`` along the vertical flight computed in the north–south plane, where the rotation
has no part in the plane).

Samples every 1/60 s of world time (every 6th is a multiple of 0.1 s: the strobe).
"""

from __future__ import annotations

import math
from functools import cached_property

import numpy as np

from lfphys.core import data
from lfphys.core.mechanics import (G_STANDARD, Body, Coriolis, Medium, fly, history_bound, latitude_for_gravity,
                                   omega_vector, sideways, vacuum_apex_height, vacuum_landing_time)
from lfphys.theories.models import drag_quadratic as dq
from lfphys.theories.models import magnus

#: the balls of the world: diameter (m) and mass (kg). A steel ball of 20 mm has 32.9 g at the density of steel
#: (7.85 g/cm³, a nominal value); the light ball has the size and mass of a tennis ball (ITF Rules of Tennis, Appendix
#: I: 6.54–6.86 cm, 56.0–59.4 g; checked 2026-11-14) but is treated as a smooth sphere: a real tennis ball's felt has its
#: own drag.
OBJECTS = {"steel20": {"d": 0.020, "m": 0.0329}, "ball67": {"d": 0.067, "m": 0.058}}
#: samples per world second: t_k = k/60 s exactly, so every 6th is a multiple of 0.1 s (the strobe); a polyline through
#: them departs from the computed path by at most g·Δt²/8 = 0.34 mm (Δt = 1/60 s), far below a pixel
RATE = 60.0
STROBE_EVERY = 6
AIR_T_C, AIR_P = 20.0, data.P_ATM  # the air: 20 °C, 101 325 Pa (U.S. Standard Atmosphere 1976 through core.data)
G = G_STANDARD
#: the place: the latitude where the WGS 84 normal gravity on the ellipsoid equals g_n (45.4996° N), sea level
LATITUDE = latitude_for_gravity(G)
#: the throws go toward the east (azimuth 90°, clockwise from north)
AZIMUTH = 90.0
#: the Earth's angular velocity's component normal to the throw's plane (rad/s): its planar part acts through it
OMEGA_Z = float(omega_vector(LATITUDE, AZIMUTH)[1])
#: steps of the history force's bound along a flight: the product integration's error is of order n^-1.5 (n = 500:
#: 5e-5 relative, against n = 2000 in the tests), far below the two digits the drawer shows
HISTORY_N = 500
#: the measured data of a spinning ball (Zhou et al. 2022, cross-checked at 1e4): the model's domain
SPIN_RE_MAX = magnus.RE_MAX
#: the relative tolerance of the shown flights' integration: with the medium and the drag curve the engine's default
#: (1e-11) let the energy balance reach 1.16e-9 on Explore's grid (the light ball from the floor at 5 m/s and 60°), above
#: the engine's stated 1e-9; at 1e-12 the grid's worst is 1.0e-10 (measured 2026-11-19), for 18 % more CPU
RTOL = 1e-12


def medium() -> dict:
    """The air's density and viscosity (``core.data.fluid_properties``)."""
    return data.fluid_properties("air", AIR_T_C, AIR_P)


def air_medium() -> Medium:
    """The air as the fluid the ball flies in (``particle.Medium``): its buoyancy and added mass (C_A = ½)."""
    return Medium.air(AIR_T_C, AIR_P)


def body_of(obj: str) -> Body:
    o = OBJECTS[obj]
    return Body(o["m"], o["d"], obj)


def launch_vector(v0: float, angle_deg: float) -> tuple[float, float]:
    """(v_x, v_y) of a launch: exact zeros at 0° and ±90° (cos 90° is not exactly zero in floating point)."""
    if angle_deg == 90.0:
        return 0.0, float(v0)
    if angle_deg == -90.0:
        return 0.0, -float(v0)
    if angle_deg == 0.0:
        return float(v0), 0.0
    a = math.radians(angle_deg)
    return v0 * math.cos(a), v0 * math.sin(a)


def rolls(obj: str, h: float, v0: float, angle_deg: float) -> bool:
    """Whether the ball leaves a chute rolling: the steel ball launched horizontally from a height (the view draws a
    chute there). Every other launch leaves without spin."""
    return obj == "steel20" and float(angle_deg) == 0.0 and float(h) > 0.0 and float(v0) > 0.0


def spin_of(obj: str, h: float, v0: float, angle_deg: float) -> float:
    """The ball's spin about the axis normal to the throw's plane, rad/s (positive: topspin for a throw along +x):
    ω = v₀/R for a ball rolling off the chute without slipping, else 0."""
    return float(v0) / (0.5 * OBJECTS[obj]["d"]) if rolls(obj, h, v0, angle_deg) else 0.0


def spin_speed_limit(obj: str) -> float:
    """The largest speed (m/s) at which the measured data of a spinning ball cover this ball in the air: Re ≤ 10⁴."""
    med = medium()
    return SPIN_RE_MAX * med["mu"] / (med["rho"] * OBJECTS[obj]["d"])


def top_speed(h: float, v0: float) -> float:
    """An upper bound of the speed along a flight from height h at v0 (m/s): the energy without the air's losses,
    √(v₀² + 2gh) (the drag only takes energy; the buoyancy lowers the weight; the Magnus and Coriolis forces do no
    work)."""
    return math.sqrt(float(v0) ** 2 + 2.0 * G * max(float(h), 0.0))


def forces_of(obj: str, spin: float, air: bool, *, rotation: bool = True, drag: str = "curve", edge: str = "central",
              lift: bool = True, spin_drag: bool = True, azimuth: float = AZIMUTH) -> list:
    """The declared forces of a flight, in this order: the drag (``CurveDrag``, a spinning ball's ``SpinDrag``, or the
    constant C_d's ``QuadraticDrag`` for ``drag="const"``), the Magnus force (a spinning ball, ``lift``), the Coriolis
    force (``rotation``; azimuth ``azimuth``). ``edge``: the Magnus model's band ("central", "low", "high"). Without air,
    only the Coriolis force (a spin has no effect without a fluid)."""
    d, m = OBJECTS[obj]["d"], OBJECTS[obj]["m"]
    out = []
    if air:
        med = medium()
        if drag == "const":
            out.append(dq.QuadraticDrag.sphere(d, med))
        elif spin and spin_drag:
            out.append(magnus.SpinDrag(d, spin, med, edge=edge))
        else:
            out.append(dq.CurveDrag.sphere(d, med))
        if spin and lift:
            out.append(magnus.Magnus(d, spin, med, edge=edge))
    if rotation:
        out.append(Coriolis(m, LATITUDE, azimuth))
    return out


def flight_of(obj: str, h: float, v0: float, angle_deg: float, air: bool, rtol: float | None = None, **kw):
    """The engine's flight of this launch with the forces of ``forces_of(**kw)`` (in air, in the air's medium); ``rtol``
    the integration's tolerance (the engine's default when None)."""
    spin = spin_of(obj, h, v0, angle_deg)
    extra = {} if rtol is None else {"rtol": rtol}
    return fly(body_of(obj), (0.0, float(h)), launch_vector(v0, angle_deg), forces=forces_of(obj, spin, air, **kw),
               medium=air_medium() if air else None, **extra)


class Shot:
    """A ball of kind ``obj`` launched from (0, h) at v0 and angle_deg toward the east, in vacuum or in air (``air``),
    on the rotating Earth: the world's flight and, computed when first asked, its references and comparisons."""

    def __init__(self, obj: str, h: float, v0: float, angle_deg: float, air: bool):
        self.obj, self.h, self.v0, self.angle, self.air = obj, float(h), float(v0), float(angle_deg), bool(air)
        self.body = body_of(obj)
        self.spin = spin_of(obj, h, v0, angle_deg)
        self.vx0, self.vy0 = launch_vector(self.v0, self.angle)
        self.forces = forces_of(obj, self.spin, self.air)
        self.coriolis = self.forces[-1]
        self.drag = self.forces[0] if self.air else None
        self.lift = self.forces[1] if self.air and self.spin else None
        self.medium = air_medium() if self.air else None
        self.flight = fly(self.body, (0.0, self.h), (self.vx0, self.vy0), forces=self.forces, medium=self.medium,
                          rtol=RTOL)
        fl = self.flight
        self.T = fl.flight_time
        self.L = fl.range
        self.x_land = float(fl.landing["r"][0])
        self.H = fl.apex_height
        self.t_apex = fl.apex["t"] if fl.apex else None
        s = fl.sample(RATE)
        self.ts = s["t"]
        self.xs, self.ys = s["r"][:, 0], s["r"][:, 1]
        self.vxs, self.vys = s["v"][:, 0], s["v"][:, 1]

    @property
    def vertical(self) -> bool:
        """A flight without a horizontal launch speed (thrown straight up or down, or dropped)."""
        return self.vx0 == 0.0

    # --- the state ----------------------------------------------------------------------------------------------------
    def at(self, t: float) -> dict:
        """The state at t (clamped to the flight; after the landing the ball lies where it landed)."""
        return self.flight.record(min(max(float(t), 0.0), self.T))

    def heat(self, t: float) -> float:
        """The heat given to the air by the drag up to t (J): minus the drag's work (the buoyancy's and the added mass's
        work are not heat; the Magnus and Coriolis forces do none)."""
        if not self.air:
            return 0.0
        return -float(self.flight.state(min(max(float(t), 0.0), self.T))[2][0])

    def force_at(self, force, t: float) -> np.ndarray:
        r, v, _ = self.flight.state(min(max(float(t), 0.0), self.T))
        return np.asarray(force.force(t, r, v), float)

    def rows(self, i0: int, i1: int) -> np.ndarray:
        """Samples i0..i1-1 as rows t, x, y (the drawn table: blob ``s`` of ``traj``)."""
        return np.column_stack([self.ts[i0:i1], self.xs[i0:i1], self.ys[i0:i1]])

    def n_until(self, t: float) -> int:
        """How many samples have times <= t."""
        return int(np.searchsorted(self.ts, t * (1 + 1e-15) + 1e-15, side="right"))

    def box(self) -> tuple[float, float, float]:
        """x_min, x_max, y_max of the computed path (samples and landing)."""
        xs = np.append(self.xs, self.x_land)
        return float(xs.min()), float(xs.max()), float(max(self.ys.max(), self.H))

    def energy_balance(self) -> float:
        return self.flight.energy_balance()

    # --- the references (the checks' second method) -------------------------------------------------------------------
    @cached_property
    def references(self) -> dict:
        """T, L, H by the second method with their tolerances and how they were computed (module docstring). None
        where no second method exists (a vertical flight in air: T and H)."""
        g = self.flight.g
        scale = max(self.h, self.v0 * self.v0 / g, 1e-3)
        if not self.vertical:
            kw = {"omega_z": OMEGA_Z}
            if self.air:
                kw.update(medium=medium(), buoyancy=True, added_mass=self.medium.added_mass)
                if self.spin:
                    kw.update(cd=lambda re, S: float(magnus.drag_factor(S)) * float(dq.cd_standard(re)),
                              spin=self.spin, cl=lambda S, re: float(magnus.cl_zhou(S, re)))
                else:
                    kw.update(cd=lambda re, S: float(dq.cd_standard(re)))
            else:
                kw.update(cd=0.0)
            try:
                r = dq.angle_flight(self.v0, math.radians(self.angle), self.h, mass=self.body.mass,
                                    diameter=self.body.diameter, g=g, **kw)
            except (ValueError, RuntimeError):  # the velocity's angle does not turn monotonically: no second method
                return {"T": None, "L": None, "H": None, "how": "none", "tol": 1e-9, "scale": scale}
            return {"T": r["T"], "L": r["L"], "H": r["H"], "how": "angle", "tol": 1e-9, "scale": scale}
        # a vertical flight: its drift by the first-order equation along the same flight in the north-south plane
        north = flight_of(self.obj, self.h, self.v0, self.angle, self.air, rtol=RTOL, azimuth=0.0)
        drift = sideways(north, north.forces[-1])["right"]  # to the right of north: east
        rot2 = (OMEGA_Z * self.T) ** 2
        # the drift's tolerance: the engine's error of the flight's length scale (1e-9 of max(h, v0^2/g), as for a
        # range) and the first-order equation's own, of second order in the rotation, (2 Omega_z T)^2 of the drift
        out = {"L": abs(drift), "drift": drift, "how": "vertical", "scale": scale,
               "tol_L": 1e-9 * max(1.0, scale / abs(drift)) + 4.0 * rot2 if drift else 1e-9, "tol": 1e-9 + rot2}
        if not self.air:
            out["T"] = vacuum_landing_time(self.h, self.vy0, g)
            out["H"] = vacuum_apex_height(self.h, self.vy0, g)
        else:
            out["T"] = out["H"] = None
        return out

    # --- the comparisons the drawer states ------------------------------------------------------------------------------
    @cached_property
    def side(self) -> dict:
        """The offset out of the throw's plane by the Coriolis force (``earth_frame.sideways``): ``right`` (m, to the
        right of the throw: south)."""
        return sideways(self.flight, self.coriolis)

    @cached_property
    def unrotated(self):
        """The same flight on a non-rotating Earth (the other forces unchanged): its range and time."""
        if not self.air:  # in vacuum the closed forms of a flight in a uniform field
            T = vacuum_landing_time(self.h, self.vy0, G)
            return {"L": abs(self.vx0) * T, "T": T}
        f = flight_of(self.obj, self.h, self.v0, self.angle, True, rotation=False)
        return {"L": f.range, "T": f.flight_time}

    @cached_property
    def vacuum(self) -> dict:
        """The same launch in vacuum on a non-rotating Earth (closed forms): L, T."""
        T = vacuum_landing_time(self.h, self.vy0, G)
        return {"L": abs(self.vx0) * T, "T": T}

    @cached_property
    def shares(self) -> dict:
        """In air, what each force adds to the range on a non-rotating Earth (m), each against the flight without it:
        ``drag`` (the drag curve alone, against vacuum), ``fluid`` (the buoyancy and the added mass, against the drag
        alone), for a spinning ball ``lift`` (the Magnus force) and ``spin_drag`` (the spin's increase of the drag),
        each against the drag curve in the medium; ``total``: the whole air against vacuum (the shares are not exactly
        additive)."""
        if not self.air:
            return {}
        L0 = self.vacuum["L"]
        fk = flight_of(self.obj, self.h, self.v0, self.angle, True, rotation=False, lift=False, spin_drag=False)
        drag_only = fly(self.body, (0.0, self.h), (self.vx0, self.vy0), forces=[fk.forces[0]])
        out = {"drag": drag_only.range - L0, "fluid": fk.range - drag_only.range, "total": self.unrotated["L"] - L0}
        if self.spin:
            fl = flight_of(self.obj, self.h, self.v0, self.angle, True, rotation=False, spin_drag=False)
            fs = flight_of(self.obj, self.h, self.v0, self.angle, True, rotation=False, lift=False)
            out.update(lift=fl.range - fk.range, spin_drag=fs.range - fk.range)
        return out

    @cached_property
    def constant_cd(self) -> dict:
        """The same throw with a constant drag coefficient C_d = 0.47 (``drag_quadratic.CD_SPHERE``) in place of the
        measured curve, the other forces unchanged: L, T (the comparison of design §11 item 25)."""
        f = flight_of(self.obj, self.h, self.v0, self.angle, True, drag="const")
        return {"L": f.range, "T": f.flight_time}

    @cached_property
    def band(self) -> dict | None:
        """A spinning ball in air: the range at the Magnus model's band edges (``low``: the least lift and spin's drag,
        ``high``: the most), m."""
        if not (self.air and self.spin):
            return None
        return {e: flight_of(self.obj, self.h, self.v0, self.angle, True, edge=e).range for e in ("low", "high")}

    @cached_property
    def history(self) -> dict | None:
        """In air: the history force's bound along the flight (``drag.history_bound``): ``dL_bound`` (m), the largest
        force over the weight ``B_over_weight``, Basset's own shift ``dL``."""
        if not self.air:
            return None
        hb = history_bound(self.flight, n=HISTORY_N)
        return {"dL_bound": hb["dL_bound"], "dL": hb["dL"], "B_over_weight": hb["B_over_weight"]}

    @cached_property
    def validity(self) -> dict | None:
        """In air: the Reynolds numbers along the path, the drag curve's C_d there, and for a spinning ball the spin
        ratio S = Rω/v (its range)."""
        if not self.air:
            return None
        ts = np.linspace(0.0, self.T, 2001)
        _, v, _ = self.flight.state(ts)
        sp = np.linalg.norm(v, axis=1)
        re = self.drag.reynolds(sp)
        out = {"re_min": float(re.min()), "re_max": float(re.max()),
               "cd_min": float(np.min(dq.cd_standard(re))), "cd_max": float(np.max(dq.cd_standard(re)))}
        if self.spin:
            S = 0.5 * self.body.diameter * abs(self.spin) / sp
            out.update(s_min=float(S.min()), s_max=float(S.max()))
        return out


def optimum_angle(obj: str, h: float, v0: float, air: bool, step: float = 0.1, drag: str = "curve",
                  rotation: bool = True) -> tuple[float, float, int]:
    """The launch angle of the largest range (degrees) with this world's forces (``drag="const"``: the constant C_d in
    place of the measured curve; ``rotation``: the Earth's rotation), that range and the number of flights computed: a
    scan at 1° steps, then at ``step`` around the best one. No closed form exists in air; it is the engine's
    computation."""
    def rng(a):
        return flight_of(obj, h, v0, float(a), air, drag=drag, rotation=rotation).range
    coarse = np.arange(1.0, 89.5, 1.0)
    best = float(coarse[int(np.argmax([rng(a) for a in coarse]))])
    fine = np.round(np.arange(best - 1.0, best + 1.0 + step / 2, step), 6)
    ls = [rng(a) for a in fine]
    i = int(np.argmax(ls))
    return float(fine[i]), float(ls[i]), len(coarse) + len(fine)
