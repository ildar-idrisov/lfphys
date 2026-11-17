# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A point body in a uniform gravitational field with declared forces (plan M1, the projectile; design
``lfphys/sources/explore_2026-11-14_design.md`` §4).

Newton's second law for a point body of mass m at r (2-D: (x, y); 3-D: (x, z, y) — the vertical is always the LAST
coordinate, the field points along it downwards):

    m dv/dt = -m g e_vert + sum_i F_i(t, r, v),      dr/dt = v,      dW_i/dt = F_i . v.

W_i is the work of the declared force i (a drag's is negative: the heat given to the medium is -W_i). It is carried as
part of the state, so the energy balance

    E_k + E_p - W = E_0,      E_k = m v^2 / 2,  E_p = m g (y - y_ground),  W = sum_i W_i

is a running check of the integration, not an identity (``Flight.energy_balance``).

Integration: ``scipy.integrate.solve_ivp`` DOP853 (Dormand–Prince 8(5,3)) with dense output, rtol 1e-11 and the
absolute tolerance set by the flight's own scales (length max(|y0 - y_ground|, v0^2/g, |r0|), speed max(v0,
sqrt(2 g h)), energy E_0) times rtol. Events are located on the dense output by the integrator (Brent's method to
4 machine epsilons in t): the landing (y = y_ground crossed downwards; terminal), the apex (v_y = 0 crossed
downwards, reported only for a launch upwards) and any declared ``Event``. Samples are taken at t_k = k / rate
exactly (k / 120 by default, so that every 12th sample is a multiple of 0.1 s: a strobe), from the dense output.

Stated error: 1e-9 relative in the landing time, the apex time and the energy balance; the lengths (the range, the
apex height, the trajectory) within 1e-9 of the flight's length scale max(h, v0^2/g) (tests: against the closed forms
in vacuum and with linear drag, against the hodograph quadrature and Radau IIA for the quadratic drag; measured
1e-15–4e-11). For a throw that is not near-vertical this is also 1e-9 of the range itself; for a near-vertical throw the
range is a small part of that scale and its own relative error grows as 1/cos(theta): with quadratic drag at 25 m/s,
1.0e-9 of L at 88°, 1.7e-8 at 89.9°, 1.4e-7 at 89.99°, while staying ~3e-11 of v0^2/g (review R-E F7).
The gravitational field is uniform: g = 9.80665 m/s^2 by default, the
standard acceleration of gravity g_n (exact; CODATA 2022, physics.nist.gov, checked 2026-11-14;
``scipy.constants.g``); a local g differs from it by up to 0.3 %, and the
field's change with height (2 h / R_earth: 3e-6 at 10 m) and the Earth's rotation (the Coriolis deflection relative
to the range is of order Omega T: 2e-4 for a 3-s flight) are not included.

Closed forms in vacuum (the references of the checks):  x = x0 + vx0 t,  y = y0 + vy0 t - g t^2 / 2,
T = (vy0 + sqrt(vy0^2 + 2 g h)) / g,  H = h + vy0^2 / (2 g) (vy0 > 0).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import constants as sc
from scipy import integrate

from lfphys.codes import coded
from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("A point body in a uniform gravitational field: the flight with declared forces"),
    "statement": T("Newton's second law for a point body in a uniform field g with any declared forces (drag), "
                   "integrated by DOP853 with dense output; the landing, the apex and declared events located by the "
                   "integrator; the work of every force carried along, so that E_k + E_p − W = E₀ is a running check; "
                   "samples at exact multiples of 1/rate; the range, the flight time and the apex height as computed "
                   "results; the closed forms of the flight in vacuum as references."),
    "validity": T("a point body (no rotation, no Magnus force, no buoyancy unless declared as a force); a uniform "
                  "field: g = 9.80665 m/s² by default (the standard gravity; a local g differs by up to 0.3 %), the "
                  "decrease of g with height and the Earth's rotation are neglected (of order 10⁻⁶ and 10⁻⁴ of the "
                  "range for school flights); the ground is a horizontal plane; stated numerical error 10⁻⁹ relative "
                  "in times and the energy balance and 10⁻⁹ of the flight's length scale max(h, v₀²/g) in lengths "
                  "(measured 10⁻¹⁵–4·10⁻¹¹; the short range of a near-vertical throw is accurate to that scale, not "
                  "to 10⁻⁹ of itself)"),
    "basis": ["Newton, Philosophiae Naturalis Principia Mathematica (1687), Book I, laws of motion",
              T("DOP853: Hairer, Nørsett, Wanner, Solving Ordinary Differential Equations I, 2nd ed. (Springer 1993), "
                "section II.10 (scipy.integrate.solve_ivp)"),
              T("the standard acceleration of gravity g_n = 9.80665 m/s², exact (CODATA 2022), through scipy.constants.g")],
    "conflicts": [],
}

#: the standard acceleration of gravity g_n, m/s^2 (exact, CODATA 2022; scipy.constants.g)
G_STANDARD = float(sc.g)
RTOL = 1e-11
T_MAX = 1e4  # s: a flight that has not landed by then is refused (a declared force holding the body up)


def _finite(*xs) -> bool:
    return all(np.all(np.isfinite(np.asarray(x, float))) for x in xs)


@dataclass(frozen=True)
class Body:
    """A point body: mass in kg (> 0), diameter in m (>= 0; used by the drag laws and the Reynolds number, 0 for a
    point without size), a name for display."""
    mass: float
    diameter: float = 0.0
    name: str = "body"

    def __post_init__(self):
        if not (_finite(self.mass, self.diameter) and self.mass > 0 and self.diameter >= 0):
            raise ValueError(T("a body needs a finite mass > 0 and a diameter ≥ 0 (given {m} kg, {d} m)",
                               m=float(self.mass), d=float(self.diameter)))


@dataclass(frozen=True)
class Event:
    """A declared event: ``fn(t, r, v) -> float`` whose zero is the event (r, v: arrays of the dimension), crossed in
    ``direction`` (+1 upwards, -1 downwards, 0 both); ``terminal`` ends the flight there."""
    name: str
    fn: object
    direction: int = 0
    terminal: bool = False


@dataclass
class Flight:
    """The integrated flight. ``sol`` is the dense output over [0, t_end]; state columns: r (dim), v (dim), the work
    W_i of each force. Records of events are dicts (``record``)."""
    body: Body
    g: float
    ground: float
    dim: int
    forces: tuple
    r0: np.ndarray
    v0: np.ndarray
    sol: object
    t_end: float
    landing: dict | None
    apex: dict | None
    events: dict = field(default_factory=dict)
    nfev: int = 0

    # --- the state ---------------------------------------------------------------------------------------------------
    def state(self, t):
        """(r, v, W) at time(s) t: r and v of shape (dim,) or (n, dim), W the work of each force (nforces,) or
        (n, nforces)."""
        t = np.asarray(t, float)
        if np.any(t < 0) or np.any(t > self.t_end * (1 + 1e-15) + 1e-300):
            raise ValueError(T("time {t} s is outside the flight [0, {end}] s", t=float(np.max(np.abs(t))),
                               end=float(self.t_end)))
        Y = np.asarray(self.sol(np.clip(t, 0.0, self.t_end)))
        d = self.dim
        if Y.ndim == 1:
            return Y[:d], Y[d:2 * d], Y[2 * d:]
        return Y[:d].T, Y[d:2 * d].T, Y[2 * d:].T

    def record(self, t: float) -> dict:
        """The state at t as plain numbers: t, r, v, x, y (the vertical), vx (the horizontal speed), vy, speed, W (the
        total work of the forces), E_k, E_p."""
        r, v, W = self.state(t)
        m = self.body.mass
        horiz = r[:-1] - self.r0[:-1]
        vh = float(np.linalg.norm(v[:-1]))
        return {"t": float(t), "r": [float(c) for c in r], "v": [float(c) for c in v],
                "x": float(r[0]), "y": float(r[-1]), "vx": float(v[0]) if self.dim == 2 else vh, "vy": float(v[-1]),
                "speed": float(np.linalg.norm(v)), "distance": float(np.linalg.norm(horiz)),
                "W": float(np.sum(W)), "E_k": 0.5 * m * float(v @ v), "E_p": m * self.g * (float(r[-1]) - self.ground)}

    # --- computed results --------------------------------------------------------------------------------------------
    @property
    def flight_time(self) -> float:
        """T, s: the landing time."""
        return self.landing["t"]

    @property
    def range(self) -> float:
        """L, m: the horizontal distance from the launch point to the landing point."""
        return self.landing["distance"]

    @property
    def apex_height(self) -> float:
        """H, m: the highest point above the ground: the apex for a launch upwards, else the launch height."""
        return (self.apex["y"] if self.apex else float(self.r0[-1])) - self.ground

    def results(self) -> dict:
        """T, L, H and the landing speed (m/s) and angle below the horizontal (degrees)."""
        ld = self.landing
        vh = math.hypot(*ld["v"][:-1]) if self.dim == 3 else abs(ld["v"][0])
        return {"T": self.flight_time, "L": self.range, "H": self.apex_height, "v_land": ld["speed"],
                "angle_land_deg": math.degrees(math.atan2(-ld["v"][-1], vh))}

    # --- samples ---------------------------------------------------------------------------------------------------
    def sample(self, rate: float = 120.0, include_end: bool = False) -> dict:
        """Samples at t_k = k / rate, k = 0, 1, ... while t_k <= t_end (with the end appended if ``include_end`` and
        it is not a sample): t (n,), r (n, dim), v (n, dim), W (n,) the total work of the forces, W_i (n, nforces),
        E_k, E_p (n,)."""
        if not (_finite(rate) and rate > 0):
            raise ValueError(T("the sampling rate must be > 0 per second"))
        n = int(math.floor(self.t_end * rate * (1 + 1e-15))) + 1
        k = np.arange(n)
        t = k / float(rate)
        t = t[t <= self.t_end]
        if include_end and t[-1] < self.t_end:
            t = np.append(t, self.t_end)
        r, v, W = self.state(t)
        m = self.body.mass
        return {"t": t, "r": r, "v": v, "W_i": W, "W": W.sum(axis=1) if W.size else np.zeros(len(t)),
                "E_k": 0.5 * m * np.einsum("ij,ij->i", v, v), "E_p": m * self.g * (r[:, -1] - self.ground)}

    def energy_balance(self, n: int = 2001) -> float:
        """The largest |E_k + E_p - W - E_0| / E_0 on n equally spaced times and the events (the running check)."""
        t = np.unique(np.concatenate([np.linspace(0.0, self.t_end, n),
                                      [e["t"] for recs in self.events.values() for e in recs]]))
        s = self.sample_at(t)
        E0 = s["E_k"][0] + s["E_p"][0]
        return float(np.max(np.abs(s["E_k"] + s["E_p"] - s["W"] - E0)) / E0)

    def sample_at(self, t) -> dict:
        """The same columns as ``sample`` at the given times."""
        t = np.asarray(t, float)
        r, v, W = self.state(t)
        m = self.body.mass
        return {"t": t, "r": r, "v": v, "W_i": W, "W": W.sum(axis=1) if W.size else np.zeros(len(t)),
                "E_k": 0.5 * m * np.einsum("ij,ij->i", v, v), "E_p": m * self.g * (r[:, -1] - self.ground)}

    def reynolds(self, t=None) -> dict:
        """The Reynolds number of each force that defines one (``force.reynolds(speed)``), at times t (default: 2001
        equally spaced times): {force index: array}."""
        t = np.linspace(0.0, self.t_end, 2001) if t is None else np.asarray(t, float)
        _, v, _ = self.state(t)
        speed = np.linalg.norm(v, axis=1)
        return {i: np.asarray(f.reynolds(speed), float) for i, f in enumerate(self.forces) if hasattr(f, "reynolds")}


def vacuum_state(t, r0, v0, g: float = G_STANDARD):
    """Closed form in vacuum: r(t) = r0 + v0 t - g t^2/2 e_vert, v(t) = v0 - g t e_vert (t scalar or array)."""
    t = np.asarray(t, float)[..., None]
    r0, v0 = np.asarray(r0, float), np.asarray(v0, float)
    e = np.zeros_like(r0)
    e[-1] = 1.0
    return r0 + v0 * t - 0.5 * g * t * t * e, v0 - g * t * e


def vacuum_landing_time(h: float, vy0: float, g: float = G_STANDARD) -> float:
    """T = (vy0 + sqrt(vy0^2 + 2 g h)) / g, written without cancellation for vy0 < 0: T = 2h / (sqrt(...) - vy0)."""
    s = math.sqrt(vy0 * vy0 + 2.0 * g * h)
    return (vy0 + s) / g if vy0 >= 0 else 2.0 * h / (s - vy0)


def vacuum_apex_height(h: float, vy0: float, g: float = G_STANDARD) -> float:
    """H = h + vy0^2 / (2 g) for vy0 > 0, else h."""
    return h + (vy0 * vy0 / (2.0 * g) if vy0 > 0 else 0.0)


def fly(body: Body, r0, v0, *, g: float = G_STANDARD, forces=(), ground: float = 0.0, events=(),
        rtol: float = RTOL, t_max: float = T_MAX) -> Flight:
    """Integrate the flight from r0 with v0 (2-D (x, y) or 3-D (x, z, y), the vertical last) until the landing on
    y = ground. ``forces``: objects with ``force(t, r, v) -> array (N)`` (and optionally ``reynolds(speed)``).
    Refusals (ValueError with a translatable text and a machine code of ``lfphys.codes``): a start below the ground
    (``mechanics.below_ground``), a start on the ground not moving up (``mechanics.no_flight``), non-finite input
    (``mechanics.nonfinite``), g <= 0 (``mechanics.bad_gravity``), a body that has not landed by ``t_max``
    (``mechanics.no_landing``)."""
    if not isinstance(body, Body):
        raise TypeError("body must be a lfphys.core.mechanics.Body")
    r0 = np.array(r0, float)
    v0 = np.array(v0, float)
    if r0.shape not in ((2,), (3,)) or v0.shape != r0.shape:
        raise ValueError(T("the position and the velocity need 2 or 3 components each (the vertical last)"))
    if not _finite(r0, v0, g, ground, rtol, t_max):
        raise coded(ValueError(T("the launch has a value that is not a finite number")), "mechanics.nonfinite")
    if not g > 0:
        raise coded(ValueError(T("the gravitational acceleration must be > 0 (given {g} m/s²)", g=float(g))),
                    "mechanics.bad_gravity")
    if not (0 < rtol < 1e-3 and t_max > 0):
        raise ValueError(T("the tolerance must be in (0, 1e-3) and the time limit > 0"))
    h = float(r0[-1] - ground)
    if h < 0:
        raise coded(ValueError(T("the body starts {h:.3g} m below the ground", h=-h)), "mechanics.below_ground")
    if h == 0 and not v0[-1] > 0:
        raise coded(ValueError(T("the body starts on the ground and does not move upwards: there is no flight")),
                    "mechanics.no_flight")
    d = r0.size
    forces = tuple(forces)
    for f in forces:
        if not callable(getattr(f, "force", None)):
            raise TypeError("a force needs a method force(t, r, v)")
    m = body.mass
    nf = len(forces)
    ev_vert = np.zeros(d)
    ev_vert[-1] = 1.0
    grav = -g * ev_vert

    def rhs(t, Y):
        r, v = Y[:d], Y[d:2 * d]
        dY = np.empty_like(Y)
        dY[:d] = v
        a = grav.copy()
        for i, f in enumerate(forces):
            F = np.asarray(f.force(t, r, v), float)
            a += F / m
            dY[2 * d + i] = F @ v
        dY[d:2 * d] = a
        return dY

    vs = float(np.linalg.norm(v0))
    Ls = max(h, vs * vs / g, float(np.max(np.abs(r0))), 1e-300)
    Vs = max(vs, math.sqrt(2.0 * g * h), 1e-300)
    Es = 0.5 * m * vs * vs + m * g * h
    atol = np.concatenate([np.full(d, Ls), np.full(d, Vs), np.full(nf, Es)]) * rtol

    def landing(t, Y):
        return Y[d - 1] - ground
    landing.terminal, landing.direction = True, -1

    def apex(t, Y):
        return Y[2 * d - 1]
    apex.terminal, apex.direction = False, -1

    def wrap(e):
        def fn(t, Y):
            return float(e.fn(t, Y[:d], Y[d:2 * d]))
        fn.terminal, fn.direction = bool(e.terminal), int(e.direction)
        return fn

    events = tuple(events)
    for e in events:
        if not isinstance(e, Event) or e.name in ("landing", "apex"):
            raise ValueError(T("a declared event must be an Event with a name other than landing and apex"))
    Y0 = np.concatenate([r0, v0, np.zeros(nf)])
    sol = integrate.solve_ivp(rhs, (0.0, float(t_max)), Y0, method="DOP853", rtol=rtol, atol=atol,
                              dense_output=True, events=[landing, apex] + [wrap(e) for e in events])
    if sol.status < 0:
        raise RuntimeError(T("the integration failed: {msg}", msg=str(sol.message)))
    if not len(sol.t_events[0]):
        raise coded(ValueError(T("the body has not landed within {t} s", t=float(t_max))), "mechanics.no_landing")
    t_end = float(sol.t_events[0][0])
    fl = Flight(body=body, g=float(g), ground=float(ground), dim=d, forces=forces, r0=r0, v0=v0, sol=sol.sol,
                t_end=t_end, landing=None, apex=None, nfev=int(sol.nfev))
    fl.landing = fl.record(t_end)
    if v0[-1] > 0:
        ta = [t for t in sol.t_events[1] if 0 < t <= t_end]
        fl.apex = fl.record(ta[0]) if ta else None
    fl.events = {"landing": [fl.landing], "apex": [fl.apex] if fl.apex else []}
    for e, te in zip(events, sol.t_events[2:]):
        fl.events[e.name] = [fl.record(t) for t in te if t <= t_end]
    return fl
