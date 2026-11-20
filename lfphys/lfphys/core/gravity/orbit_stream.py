# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A massive body's orbit in the Schwarzschild exterior, integrated chunk by chunk with located events.

Geometric units (G = c = 1, lengths in M = GM/c^2, times in GM/c^3). The body starts at r0 with the velocity
(v_r, v_phi) measured by the static observer there (fractions of c); then (lfphys.core.gravity.orbits)

    e = gamma sqrt(1 - 2/r0),   e^2 - 1 = gamma^2 (v^2 - 2/r0)  (no cancellation),   l = gamma v_phi r0.

Non-radial orbits (l != 0): the Binet form in the swept angle psi = |phi - phi0| for u = 1/r, scaled by the start
value u_s = 1/r0 (y = u/u_s), so that a weak-field orbit is integrated at the relative tolerance without an absolute
floor (the general-relativistic term 3 u_s y^2 is ~1e-7 of the others for Mercury):

    y'' = A - y + 3 u_s y^2,   A = 1/(l^2 u_s),
    dT_t/dpsi   = e / (L y^2 (1 - 2 u_s y)),     T_t   = t   u_s^{3/2},
    dT_tau/dpsi = 1 / (L y^2),                   T_tau = tau u_s^{3/2},     L = |l| sqrt(u_s).

The state (y, y') is carried from chunk to chunk exactly, so a chunk boundary costs nothing in precision.
Radial orbits (l = 0): rho = r/r0 in the scaled proper time s = tau/r0^{3/2}: rho'' = -1/rho^2 (exact),
dT_t/ds = e / (1 - 2/(r0 rho)).

Events are located on the DOP853 dense output: periapsis and apoapsis (zeros of du/dpsi; the top of a radial
flight, dr/dtau = 0), each full turn psi = 2 pi n, the horizon (the stop at r = 2M (1 + 1e-6): in coordinate time
the body only approaches it), the surface of the body (r = R), escape (r = r_far) and a requested coordinate time.

Proper time of a plunge by quadrature, tau = integral dr / sqrt(R(r)), R = e^2 - (1 - 2/r)(1 + l^2/r^2): a reference
that integrates no differential equation (``plunge_proper_time``).

Inside the horizon (EX2 design §11 item 34): the body's own time does not end at the stop above the horizon. The
first integrals e = (1 - 2/r) dt/dtau, l = r^2 dphi/dtau and the norm hold for every r > 0 (Blau, Lecture Notes on
General Relativity, eqs. (25.29)-(25.33)), so (dr/dtau)^2 = R(r) there too, and for r < 2M

    R(r) = e^2 + (2/r - 1)(1 + l^2/r^2) >= e^2 > 0:

nothing turns back, and the body reaches r = 0 after the finite proper time tau = integral_0^r dr / sqrt(R(r))
(``proper_time_to_centre``; ``OrbitStream.interior`` after a stop at the horizon). The coordinate time, the distant
observer's, diverges at r = 2M and the stream still stops there. Near r = 0, 1/sqrt(R) ~ sqrt(r/2) (l = 0) or
r^{3/2}/(sqrt(2)|l|): integrable. Since R >= 2/r - 1 inside, no fall lasts longer than integral_0^2 dr/sqrt(2/r - 1)
= pi M from the horizon to r = 0. The radial fall from rest at r0 is the cycloid r = (r0/2)(1 + cos eta),
tau = sqrt(r0^3/8)(eta + sin eta), down to eta = pi: tau(r = 0) = pi sqrt(r0^3/8M) (Blau, eqs. (26.25)-(26.29); Guth,
MIT 8.286 (2013), lecture 15, «ripped apart by the singularity at r = 0 in a finite amount of the object's proper
time»; ``cycloid_proper_time``). General relativity, and the computation, end at the singularity r = 0.

Diagnostics: the first integral e^2 - 1 evaluated from the state, (e^2 - 1)_state = l^2 u_s^2 (y'^2 - 2 u_s y^3 +
y^2 - 2 A y), whose drift from the initial value measures the integration error; and an independent second scheme
(``geodesic_tau``): the geodesic equations x''^a = -Gamma^a_bc x'^b x'^c of the Schwarzschild metric in proper time
for (t, r, phi), along which e = (1 - 2/r) t', l = r^2 phi' and the norm -(1 - 2/r) t'^2 + r'^2/(1 - 2/r) + r^2 phi'^2
= -1 are conserved only numerically.
"""

from __future__ import annotations

import math

import mpmath as mp
import numpy as np
from scipy import integrate, optimize

from lfphys.i18n import T
from lfphys.codes import coded

from . import orbits

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("The orbit of a body in the Schwarzschild field: continuous integration with events"),
    "statement": T("A timelike geodesic in the equatorial plane, piece by piece: Binet's equation for u = M/r scaled "
                   "by the initial radius, together with t and τ; radial orbits in proper time; periapsides, "
                   "apoapsides, turns, the horizon, the surface and escape as events on the dense output of DOP853; "
                   "the drift of e from the state; a second independent scheme (the geodesic equations in τ) to check "
                   "e, l and the normalisation; the proper time of a fall by the quadrature τ = ∫dr/√R(r), also past "
                   "the horizon to r = 0, which a falling body reaches in a finite time of its own clock (the radial "
                   "fall from rest: τ = π√(r₀³/8M))."),
    "validity": T("a test body outside a non-rotating spherical body (r > R, r > 2M), equatorial plane; inside a black "
                  "hole's horizon only the body's proper time on to r = 0, where general relativity itself ends; "
                  "relative integration accuracy 1e-12, quadratures 1e-11"),
    "basis": [T("orbit equations: lfphys.core.gravity.orbits (Schwarzschild 1916)"),
              "DOP853: Hairer, Nørsett, Wanner, Solving Ordinary Differential Equations I (scipy.integrate)",
              "M. Blau, Lecture Notes on General Relativity (Universität Bern), eqs. (25.29)–(25.33), (26.25)–(26.29)",
              "A. H. Guth, MIT 8.286 The Early Universe (2013), lecture 15"],
    "conflicts": [],
}

CIRCULAR_SPREAD = 1e-6  # (r_apo - r_peri)/r_peri below which an orbit is treated as circular (no apsis events)
SNAP = 1e-12  # |v_r| or |v_phi| below SNAP * v is rounding (e.g. the state of a boosted circular orbit): set to 0
HORIZON_GAP = 1e-6  # the stop at the horizon: r = 2M / (1 - HORIZON_GAP); the coordinate time diverges
# logarithmically there, and resolving it much closer (1e-8) costs 1e6 steps in double precision


def local_velocity_to_constants(r0: float, v_r: float, v_phi: float) -> dict:
    """e, e^2 - 1 (without cancellation), l and gamma from the static observer's velocity at r0 (in M, c)."""
    e, l = orbits.from_local_velocity(r0, v_r, v_phi)
    v2 = v_r * v_r + v_phi * v_phi
    g2 = 1.0 / (1.0 - v2)
    return {"e": e, "em1": g2 * (v2 - 2.0 / r0), "l": l, "gamma": math.sqrt(g2)}


def local_speed_from_e(r: float, e: float) -> float:
    """Speed measured by the static observer at r of a geodesic body with energy e: v^2 = 1 - (1 - 2/r)/e^2."""
    return math.sqrt(max(0.0, 1.0 - (1.0 - 2.0 / r) / (e * e)))


class OrbitStream:
    """One body's geodesic, advanced in chunks of coordinate time. All quantities in M units; phi grows with the
    motion if v_phi > 0 (sense = +1) and decreases if v_phi < 0."""

    def __init__(self, r0: float, v_r: float, v_phi: float, *, phi0: float = 0.0, r_stop: float = 2.0,
                 r_far: float | None = None, rtol: float = 1e-12, n_turn: int = 240):
        if r0 <= 2.0:
            raise coded(ValueError(T("the start must be outside the horizon (r0 > 2M)")), "orbit.horizon")
        if r_stop >= r0:
            raise coded(ValueError(T("the start must be above the surface of the body")), "orbit.horizon")
        v = math.hypot(v_r, v_phi)
        if abs(v_r) <= SNAP * v:
            v_r = 0.0  # a start at a turning point: the rounding of a boosted circular state is not a radial speed
        if abs(v_phi) <= SNAP * v:
            v_phi = 0.0  # a radial start
        k = local_velocity_to_constants(r0, v_r, v_phi)
        self.r0, self.phi0, self.rtol = float(r0), float(phi0), float(rtol)
        self.v_r0, self.v_phi0 = v_r, v_phi
        self.e, self.em1, self.gamma = k["e"], k["em1"], k["gamma"]
        self.radial = v_phi == 0.0
        self.sense = 1.0 if v_phi >= 0 else -1.0
        self.l = 0.0 if self.radial else k["l"]
        self.surface = r_stop > 2.0
        self.r_stop = r_stop if self.surface else 2.0 / (1.0 - HORIZON_GAP)
        self.r_far = float(r_far) if r_far else 1e3 * r0
        self.us = 1.0 / r0
        self.n_turn = int(n_turn)
        # offsets of the chunk start: swept angle (psi), coordinate and proper time
        self.psi, self.t, self.tau = 0.0, 0.0, 0.0
        self.chunks: list[dict] = []
        self.done: str | None = None  # "horizon" | "surface" | "escape"
        self.n_peri = self.n_apo = self.n_lap = 0
        if self.radial:
            self.Yr = (float(r0), self.e * v_r)  # r and dr/dtau; each chunk is scaled to its own start radius
        else:
            L = abs(self.l)
            self.A = 1.0 / (L * L * self.us)
            self.B = self.em1 / (L * L * self.us * self.us)
            self.Lq = L * math.sqrt(self.us)
            self.sc = self.us ** -1.5
            # du/dpsi = -(dr/dtau)/L, dr/dtau = e v_r
            self.Y = np.array([1.0, -self.e * v_r / (L * self.us), 0.0, 0.0])
        self.info = self._classify(v_r)
        # an orbit with an apoapsis is followed out to it: it does not end at r_far as an escape
        ra = self.info.get("r_apo")
        if ra is not None and math.isfinite(ra):
            self.r_far = max(self.r_far, 1.5 * ra)

    # --- what kind of orbit -------------------------------------------------------------------------------
    def _turning_offsets(self):
        """Turning points as offsets z = y - 1 from the start (y = u/u_s): the real roots of

            P(z) = F(1 + z) = 2 u_s z^3 + (6 u_s - 1) z^2 + c1 z + c0,   c1 = F'(1) = 2(A - 1) + 6 u_s,   c0 = y'(0)^2.

        c0 is the first integral the integrator conserves, evaluated at the start, so these are the turning points of
        the integrated orbit; a start at a turning point (c0 = 0) is an exact root and is never re-found (review
        V4-1), and |c1| <= 1e-13 there is a double root (a circular start). The roots of the float coefficients are
        found at 30 digits (mpmath); their signs relative to the start are therefore exact."""
        us = self.us
        a3, a2 = 2.0 * us, 6.0 * us - 1.0
        c1 = 2.0 * (self.A - 1.0) + 6.0 * us
        c0 = float(self.Y[1]) ** 2
        if c0 == 0.0 and abs(c1) <= 1e-13 * max(1.0, abs(a2)):
            c1 = 0.0
        coeffs, extra = ([a3, a2, c1], [0.0]) if c0 == 0.0 else ([a3, a2, c1, c0], [])
        if c0 == 0.0 and c1 == 0.0:
            return sorted([0.0, 0.0, -a2 / a3]), c0, c1
        with mp.workdps(30):
            try:
                zs = mp.polyroots([mp.mpf(c) for c in coeffs], maxsteps=200, extraprec=200)
                real = [float(mp.re(z)) for z in zs if abs(mp.im(z)) <= mp.mpf(10) ** -20 * max(1, abs(mp.re(z)))]
            except mp.NoConvergence:  # pragma: no cover - a fallback, not expected for cubics
                real = [float(z.real) for z in np.roots(coeffs) if abs(z.imag) <= 1e-9 * max(1.0, abs(z.real))]
        return sorted(real + extra), c0, c1

    def _classify(self, v_r) -> dict:
        r0 = self.r0
        moving = 1 if v_r > 0 else (-1 if v_r < 0 else 0)  # +1 outward
        if self.radial:
            apex = -2.0 / self.em1 if self.em1 < 0 else math.inf  # (dr/dtau)^2 = e^2 - 1 + 2/r
            kind = "radial_escape" if (v_r > 0 and not math.isfinite(apex)) else "radial_fall"
            return {"kind": kind, "r_apex": apex, "r_peri": None, "r_apo": apex if math.isfinite(apex) else None,
                    "moving": moving, "spread": None, "start_turning": v_r == 0.0, "double_root": False,
                    "nearest_root": None}
        zs, c0, c1 = self._turning_offsets()
        if c0 > 0.0:
            lo = max([z for z in zs if z < 0.0], default=None)
            hi = min([z for z in zs if z > 0.0], default=None)
        elif c1 < 0.0:  # the start is a maximum of u: the periapsis; the motion is at z <= 0
            hi, lo = 0.0, max([z for z in zs if z < 0.0], default=None)
        elif c1 > 0.0:  # a minimum of u: the apoapsis; the motion is at z >= 0
            lo, hi = 0.0, min([z for z in zs if z > 0.0], default=None)
        else:  # a double root at the start: a circular orbit (stable if 6 u_s < 1)
            lo = hi = 0.0
        y_stop = r0 / self.r_stop
        r_peri = r0 / (1.0 + hi) if (hi is not None and 1.0 + hi < y_stop) else None
        r_apo = r0 / (1.0 + lo) if (lo is not None and 1.0 + lo > 0.0) else None
        spread = (r_apo - r_peri) / r_peri if (r_peri is not None and r_apo is not None) else None
        if spread is not None:
            kind = "circular" if spread <= CIRCULAR_SPREAD else "bound"
        elif r_peri is not None:
            kind = "escape"  # past the periapsis (ahead or behind) nothing turns the body back
        elif r_apo is not None:
            kind = "plunge"  # up to the apoapsis (if moving out), then down
        else:
            kind = "escape" if moving > 0 else "plunge"  # no turning point: the direction of motion decides
        others = [abs(z) for z in zs if z != 0.0] if c0 == 0.0 else [abs(z) for z in zs]
        return {"kind": kind, "r_peri": r_peri, "r_apo": r_apo, "moving": moving, "spread": spread,
                "start_turning": c0 == 0.0, "double_root": c0 == 0.0 and c1 == 0.0,
                "nearest_root": min(others) if others else None}  # |y - 1| of the nearest other turning point

    # --- integration ------------------------------------------------------------------------------------
    def _rhs_binet(self, psi, Y):
        y, yp = Y[0], Y[1]
        g = 1.0 / (self.Lq * y * y)
        return [yp, self.A - y + 3.0 * self.us * y * y, self.e * g / (1.0 - 2.0 * self.us * y), g]


    def advance(self, t_until: float, max_turns: float = 2.0) -> dict:
        """Integrate one chunk: until the coordinate time t_until (M units), or ``max_turns`` turns, or a stop.
        Returns dict(t, tau, r, phi, events) of the chunk's samples (M units, absolute) and located events
        (each a dict: kind, t, tau, r, phi, psi, and for apsides em1_state); updates the state."""
        if self.done:
            return {"t": np.zeros(0), "tau": np.zeros(0), "r": np.zeros(0), "phi": np.zeros(0), "events": []}
        if self.radial:
            return self._advance_radial(t_until, max_turns)
        return self._advance_binet(t_until, max_turns)

    def _advance_binet(self, t_until, max_turns):
        sc = self.sc
        circular = self.info["kind"] == "circular"
        y_stop, y_far = self.r0 / self.r_stop, self.r0 / self.r_far
        T_until = (t_until - self.t) / sc

        def ev_peri(p, Y):
            return Y[1]
        ev_peri.direction = -1.0

        def ev_apo(p, Y):
            return Y[1]
        ev_apo.direction = 1.0

        def ev_stop(p, Y):
            return Y[0] - y_stop
        ev_stop.terminal, ev_stop.direction = True, 1.0

        def ev_far(p, Y):
            return Y[0] - y_far
        ev_far.terminal, ev_far.direction = True, -1.0

        def ev_time(p, Y):
            return Y[2] - T_until
        ev_time.terminal, ev_time.direction = True, 1.0

        evs = [ev_stop, ev_far, ev_time] + ([] if circular else [ev_peri, ev_apo])
        span = 2.0 * math.pi * max_turns
        Y0 = np.array([self.Y[0], self.Y[1], 0.0, 0.0])
        # absolute tolerance of y and y' scaled by the smallest y the orbit can reach (r0/r_far): an apoapsis far out
        # (y ~ 7e-5 at r_apo = 1.5e4 r0) keeps the relative precision of its radius
        y_lo = min(1.0, self.r0 / self.r_far)
        atol = np.array([y_lo, y_lo, 1.0, 1.0]) * self.rtol * 1e-3
        sol = integrate.solve_ivp(self._rhs_binet, (0.0, span), Y0, method="DOP853", rtol=self.rtol,
                                  atol=atol, dense_output=True, events=evs)
        p_end = float(sol.t[-1])
        Y_end = sol.y[:, -1]
        stop = "surface" if self.surface else "horizon"
        reason = None
        if sol.t_events[0].size:
            reason = stop
        elif sol.t_events[1].size:
            reason = "escape"
        events = []
        if not circular:
            for kind, k in (("peri", 3), ("apo", 4)):
                for p, Y in zip(sol.t_events[k], sol.y_events[k]):
                    events.append(self._event_binet(kind, float(p), Y))
        # full turns, counted by the stream's own counter: the next turn's angle is 2 pi (n_lap + 1), at p = that minus
        # the chunk's start, in this chunk when p <= p_end (one comparison decides it). The former floor(psi / 2 pi)
        # bounds and the test 0 < p <= p_end rounded two ways: a chunk ending within a rounding of a turn (the screens'
        # frame clock makes that systematic on circles, T/32 per frame) lost the turn or counted it twice, depending on
        # the CPU's last bits (CI's AVX-512 runner; EX2 W34). A turn that the previous chunk ended a rounding short of
        # lies at this chunk's start (p = 0).
        n = self.n_lap + 1
        while True:
            p = 2 * math.pi * n - self.psi
            if p > p_end:
                break
            p = max(p, 0.0)
            ev = self._event_binet("lap", p, sol.sol(p))
            ev["n"] = n
            events.append(ev)
            n += 1
        if reason:
            events.append(self._event_binet(reason, p_end, Y_end))
        # samples: a uniform grid in psi aligned to the global angle, the chunk end, and (before a stop or escape)
        # a geometric approach, along which the coordinate time grows by equal steps near the horizon
        h = 2 * math.pi / self.n_turn
        k0 = math.floor(self.psi / h) + 1
        grid = np.arange(k0, math.floor((self.psi + p_end) / h) + 1) * h - self.psi
        grid = grid[(grid > 0) & (grid < p_end)]
        if reason:
            last = grid[-1] if grid.size else 0.0
            q = (p_end - last) * 0.7 ** np.arange(1, 61)
            grid = np.concatenate([grid, p_end - q])
        grid = np.concatenate([grid, [p_end]])
        Yg = sol.sol(grid)
        Yg[:, -1] = Y_end
        out = {"t": self.t + sc * Yg[2], "tau": self.tau + sc * Yg[3], "r": self.r0 / Yg[0],
               "phi": self.phi0 + self.sense * (self.psi + grid), "events": sorted(events, key=lambda d: d["t"])}
        self.chunks.append({"sol": sol.sol, "psi": self.psi, "t": self.t, "tau": self.tau, "p_end": p_end,
                            "t_end": self.t + sc * float(Y_end[2])})
        self.chunks = self.chunks[-8:]
        self.psi += p_end
        self.t += sc * float(Y_end[2])
        self.tau += sc * float(Y_end[3])
        self.Y = np.array([Y_end[0], Y_end[1], 0.0, 0.0])
        if reason:
            self.done = reason
        for ev in events:
            if ev["kind"] == "peri":
                self.n_peri += 1
            elif ev["kind"] == "apo":
                self.n_apo += 1
            elif ev["kind"] == "lap":
                self.n_lap += 1
        return out

    def em1_state(self, y: float, yp: float) -> float:
        """e^2 - 1 from the state (y, y') through the first integral (exact value: self.em1)."""
        L2us2 = self.l * self.l * self.us * self.us
        return L2us2 * (yp * yp - 2.0 * self.us * y**3 + y * y - 2.0 * self.A * y)

    def _event_binet(self, kind, p, Y):
        y, yp = float(Y[0]), float(Y[1])
        return {"kind": kind, "psi": self.psi + p, "phi": self.phi0 + self.sense * (self.psi + p),
                "t": self.t + self.sc * float(Y[2]), "tau": self.tau + self.sc * float(Y[3]), "r": self.r0 / y,
                "em1_state": self.em1_state(y, yp), **self._velocity_binet(y, yp)}

    def _velocity_binet(self, y, yp):
        """The static observer's velocity at the state: v_r = (dr/dtau)/e, v_phi = l u sqrt(1 - 2u)/e."""
        u = self.us * y
        L = abs(self.l)
        v_r = (-L * self.us * yp) / self.e
        v_phi = self.sense * L * u * math.sqrt(max(1.0 - 2.0 * u, 0.0)) / self.e
        return {"v_r": v_r, "v_phi": v_phi}

    def _advance_radial(self, t_until, max_turns):
        """A radial chunk in units of its own start radius rc: rho = r/rc, s = tau/rc^{3/2}, T = t/rc^{3/2}; the
        chunk also ends when r has fallen to rc/4 or grown to 4 rc, so the next one is rescaled. (A single scale r0,
        as before, cannot resolve the last 1e-4 M of a fall from r0 >~ 1e6 M in doubles: review V4-3.)"""
        r_c, rdot = self.Yr
        sc = r_c**1.5
        rho_stop, rho_far = self.r_stop / r_c, self.r_far / r_c
        T_until = (t_until - self.t) / sc
        e = self.e

        def rhs(s, Y):
            rho = Y[0]
            return [Y[1], -1.0 / (rho * rho), e / (1.0 - 2.0 / (r_c * rho))]

        def ev_top(s, Y):
            return Y[1]
        ev_top.direction = -1.0

        def ev_stop(s, Y):
            return Y[0] - rho_stop
        ev_stop.terminal, ev_stop.direction = True, -1.0

        def ev_far(s, Y):
            return Y[0] - rho_far
        ev_far.terminal, ev_far.direction = True, 1.0

        def ev_time(s, Y):
            return Y[2] - T_until
        ev_time.terminal, ev_time.direction = True, 1.0

        def ev_shrink(s, Y):
            return Y[0] - 0.25
        ev_shrink.terminal, ev_shrink.direction = True, -1.0

        def ev_grow(s, Y):
            return Y[0] - 4.0
        ev_grow.terminal, ev_grow.direction = True, 1.0

        span = 2 * math.pi * max_turns
        Y0 = np.array([1.0, math.sqrt(r_c) * rdot, 0.0])
        sol = integrate.solve_ivp(rhs, (0.0, span), Y0, method="DOP853", rtol=self.rtol, atol=self.rtol * 1e-3,
                                  dense_output=True, events=[ev_stop, ev_far, ev_time, ev_top, ev_shrink, ev_grow])
        s_end = float(sol.t[-1])
        Y_end = sol.y[:, -1]
        reason = ("surface" if self.surface else "horizon") if sol.t_events[0].size else (
            "escape" if sol.t_events[1].size else None)
        events = []
        for s_ev, Y in zip(sol.t_events[3], sol.y_events[3]):
            events.append(self._event_radial("apo", float(s_ev), Y, r_c, sc))
        if reason:
            events.append(self._event_radial(reason, s_end, Y_end, r_c, sc))
        h = 2 * math.pi / self.n_turn
        grid = np.arange(1, math.floor(s_end / h) + 1) * h
        grid = grid[grid < s_end]
        if reason:
            last = grid[-1] if grid.size else 0.0
            q = (s_end - last) * 0.7 ** np.arange(1, 61)
            grid = np.concatenate([grid, s_end - q])
        grid = np.concatenate([grid, [s_end]])
        Yg = sol.sol(grid)
        Yg[:, -1] = Y_end
        out = {"t": self.t + sc * Yg[2], "tau": self.tau + sc * grid, "r": r_c * Yg[0],
               "phi": np.full(grid.size, self.phi0), "events": sorted(events, key=lambda d: d["t"])}
        self.chunks.append({"sol": sol.sol, "psi": 0.0, "t": self.t, "tau": self.tau, "p_end": s_end,
                            "t_end": self.t + sc * float(Y_end[2]), "sc": sc, "rc": r_c})
        self.chunks = self.chunks[-8:]
        self.t += sc * float(Y_end[2])
        self.tau += sc * s_end
        self.Yr = (r_c * float(Y_end[0]), float(Y_end[1]) / math.sqrt(r_c))
        if reason:
            self.done = reason
        self.n_apo += len(sol.t_events[3])
        return out

    def _event_radial(self, kind, s, Y, r_c, sc):
        r = r_c * float(Y[0])
        rdot = float(Y[1]) / math.sqrt(r_c)  # dr/dtau
        return {"kind": kind, "psi": 0.0, "phi": self.phi0, "t": self.t + sc * float(Y[2]),
                "tau": self.tau + sc * s, "r": r, "em1_state": rdot * rdot - 2.0 / r,
                "v_r": rdot / self.e, "v_phi": 0.0}

    # --- the state at a given coordinate time (inside the chunks kept) -----------------------------------
    def state_at(self, t: float) -> dict | None:
        """The exact state at coordinate time t (M units) from the dense output of a kept chunk: r, phi, tau and
        the static observer's velocity (v_r, v_phi). None if t is outside the chunks kept."""
        for ch in reversed(self.chunks):
            if ch["t"] <= t <= ch["t_end"]:
                break
        else:
            return None
        sc = ch.get("sc", getattr(self, "sc", 1.0))

        def F(p):  # the coordinate time is component 2 in both forms
            return ch["t"] + sc * float(ch["sol"](p)[2]) - t

        if t <= ch["t"]:
            p = 0.0
        elif t >= ch["t_end"]:
            p = ch["p_end"]
        else:
            p = optimize.brentq(F, 0.0, ch["p_end"], xtol=1e-14 * max(1.0, ch["p_end"]), rtol=1e-15, maxiter=200)
        Y = ch["sol"](p)
        if self.radial:
            r = ch["rc"] * float(Y[0])
            rdot = float(Y[1]) / math.sqrt(ch["rc"])
            return {"r": r, "phi": self.phi0, "tau": ch["tau"] + sc * p, "t": t, "v_r": rdot / self.e, "v_phi": 0.0}
        y, yp = float(Y[0]), float(Y[1])
        return {"r": self.r0 / y, "phi": self.phi0 + self.sense * (ch["psi"] + p), "tau": ch["tau"] + sc * float(Y[3]),
                "t": t, **self._velocity_binet(y, yp)}

    def interior(self) -> dict | None:
        """The body's own time past the stop at the horizon (EX2 §11 item 34): the stream stops 2e-6 M above r = 2M,
        where the distant observer's time diverges; the body's clock goes on, by the quadrature, through the horizon
        to r = 0 (``proper_time_to_centre``). Returns dict(r_stop, tau_stop: the stream's own at its stop; tau_horizon,
        tau_centre: at r = 2M and at r = 0; dtau_inside: from the horizon to r = 0, at most pi M), M units; None unless
        the stream stopped at a black hole's horizon (a body's surface or an escape ends nothing inside)."""
        if self.done != "horizon":
            return None
        r_s = float(self.Yr[0]) if self.radial else self.r0 / float(self.Y[0])  # the state at the located stop
        d_h = proper_time_to_centre(self.em1, self.l, r_s, 2.0)
        d_in = proper_time_to_centre(self.em1, self.l, 2.0, 0.0)
        return {"r_stop": r_s, "tau_stop": self.tau, "tau_horizon": self.tau + d_h, "tau_centre": self.tau + d_h + d_in,
                "dtau_inside": d_in}

    def clock_rate(self, r):
        """dtau/dt of the body at r: (1 - 2/r)/e (array or scalar)."""
        return (1.0 - 2.0 / np.asarray(r)) / self.e

    def clock_lag(self, r):
        """1 - dtau/dt = (e - 1 + 2/r)/e with e - 1 = (e^2 - 1)/(e + 1): no cancellation in a weak field
        (Mercury: ~6e-8, below the resolution of 1 - clock_rate in single precision)."""
        return (self.em1 / (self.e + 1.0) + 2.0 / np.asarray(r)) / self.e


# --- proper time by quadrature (no differential equation) ------------------------------------------------------
def radial_potential(r, em1: float, l: float):
    """R(r) = (dr/dtau)^2 = e^2 - (1 - 2/r)(1 + l^2/r^2) = (e^2 - 1) + 2/r - l^2/r^2 + 2 l^2/r^3."""
    r = np.asarray(r, float)
    return em1 + 2.0 / r - l * l / (r * r) + 2.0 * l * l / r**3


def proper_time_between(em1: float, l: float, r_a: float, r_b: float) -> float:
    """Proper time of a monotonic radial leg between r_a < r_b (either may be a turning point, R = 0):
    tau = integral dr / sqrt(R(r)), with r = r_a + (r_b - r_a)(1 - cos theta)/2, which removes the inverse square
    root at a simple turning point (Gauss-Kronrod quadrature on two halves, relative 1e-11)."""
    if not r_a < r_b:
        raise coded(ValueError(T("r_a < r_b required")), "orbit.bad_radii")
    h = 0.5 * (r_b - r_a)

    def g(th):
        r = r_a + h * (1.0 - math.cos(th))
        R = float(radial_potential(r, em1, l))
        return h * math.sin(th) / math.sqrt(R) if R > 0 else 0.0

    total = 0.0
    for a, b in ((0.0, 0.5 * math.pi), (0.5 * math.pi, math.pi)):
        val, _ = integrate.quad(g, a, b, epsabs=0.0, epsrel=1e-11, limit=400)
        total += val
    return total


def _turning_points(em1: float, l: float, r_lo: float, r_hi: float) -> list[float]:
    """The turning points of the radial motion (R(r) = 0) strictly between r_lo and r_hi (1e-9 of r_hi kept clear of
    r_hi itself, a start at a turning point): the positive real roots of r^3 R(r) = (e^2 - 1) r^3 + 2 r^2 - l^2 r + 2 l^2
    (none below 2M: R >= e^2 there)."""
    roots = np.roots([em1, 2.0, -l * l, 2.0 * l * l]) if (em1 != 0.0 or l != 0.0) else np.zeros(0)
    return sorted(float(z.real) for z in np.atleast_1d(roots)
                  if abs(z.imag) <= 1e-9 * max(1.0, abs(z.real)) and r_lo < z.real < r_hi * (1.0 - 1e-9))


def proper_time_to_centre(em1: float, l: float, r_from: float, r_to: float = 0.0) -> float:
    """Proper time of a fall from r_from down to r_to (0 <= r_to < r_from), outside the horizon, through it or inside
    it: tau = integral_{r_to}^{r_from} dr / sqrt(R(r)), R = e^2 - (1 - 2/r)(1 + l^2/r^2) (e^2 - 1 = em1, M = 1). The body
    falls inward all the way (dr/dtau < 0, or 0 at r_from: a start at a turning point); with a turning point between the
    two radii it does not get there, and the call is refused (orbit.turns_back; radii out of order: orbit.bad_radii).
    Inside the horizon R >= e^2 > 0 (see the
    module's docstring), and r_to = 0 is the singularity, reached in finite proper time. The substitution
    r = r_to + (r_from - r_to) sin^2(theta/2) makes the integrand smooth at both ends: at a turning point (R ~ r_from - r)
    and at r = 0 (1/sqrt(R) ~ r^{1/2}, or r^{3/2} with l != 0). Gauss-Kronrod on two halves, relative 1e-11."""
    if not (0.0 <= r_to < r_from and math.isfinite(r_from)):
        raise coded(ValueError(T("0 ≤ r_to < r_from required")), "orbit.bad_radii")
    turn = _turning_points(em1, l, r_to, r_from)
    if turn:
        raise coded(ValueError(T("the body turns back at r = {r:.6g}M and does not fall to r = {r_to:.6g}M",
                                 r=turn[-1], r_to=r_to)), "orbit.turns_back")
    d = r_from - r_to

    def g(th):
        r = r_to + d * math.sin(0.5 * th) ** 2
        if r <= 0.0:
            return 0.0
        R = float(radial_potential(r, em1, l))
        return 0.5 * d * math.sin(th) / math.sqrt(R) if R > 0 else 0.0

    total = 0.0
    for a, b in ((0.0, 0.5 * math.pi), (0.5 * math.pi, math.pi)):
        val, _ = integrate.quad(g, a, b, epsabs=0.0, epsrel=1e-11, limit=400)
        total += val
    return total


def cycloid_proper_time(r0: float, r: float = 0.0) -> float:
    """The radial fall from rest at r0 > 2M, in closed form (Blau, eqs. (26.25)-(26.29)): r = (r0/2)(1 + cos eta),
    tau = sqrt(r0^3/8)(eta + sin eta), for any 0 <= r <= r0, inside the horizon too; tau(0) = pi sqrt(r0^3/8M). Other
    radii: orbit.bad_radii."""
    if not (r0 > 2.0 and 0.0 <= r <= r0):
        raise coded(ValueError(T("0 ≤ r ≤ r0 and r0 > 2M required")), "orbit.bad_radii")
    eta = math.acos(min(1.0, max(-1.0, 2.0 * r / r0 - 1.0)))
    return math.sqrt(r0**3 / 8.0) * (eta + math.sin(eta))


def plunge_proper_time(em1: float, l: float, r0: float, v_r: float, r_end: float, r_apo: float | None) -> float:
    """Proper time from r0 to r_end < r0 of an orbit without periapsis (a plunge): an outward leg to the apoapsis
    first if the body starts outward (v_r > 0), then the fall."""
    if v_r > 0:
        if r_apo is None:
            raise coded(ValueError(T("an outward start without an apoapsis does not fall")), "orbit.no_fall")
        return proper_time_between(em1, l, r0, r_apo) + proper_time_between(em1, l, r_end, r_apo)
    return proper_time_between(em1, l, r_end, r0)


# --- the independent second scheme ----------------------------------------------------------------------------
def geodesic_tau(r0: float, v_r: float, v_phi: float, tau_end: float, r_stop: float = 2.0,
                 rtol: float = 1e-12, n_out: int = 2001) -> dict:
    """The geodesic equations of the Schwarzschild metric in proper time for (t, r, phi), with scaled variables
    rho = r/r0, s = tau/r0^{3/2}, T = t/r0^{3/2}:

        rho'' = -f t'^2/rho^2 + rho'^2/(r0 rho^2 f) + rho f phi'^2,   t'' = -2 t' rho'/(r0 rho^2 f),
        phi'' = -2 rho' phi'/rho,    f = 1 - 2/(r0 rho),   (' = d/ds; t' = dt/dtau).

    Nothing is imposed: e = f t', l = sqrt(r0) rho^2 phi' and the norm N = -f t'^2 + rho'^2/(r0 f) + rho^2 phi'^2/r0
    (= -1) drift only by the integration error. Returns the samples, the periapses (rho' = 0 upward) and the drifts."""
    if r_stop <= 2.0:
        r_stop = 2.0 / (1.0 - HORIZON_GAP)
    sq = math.sqrt(r0)
    f0 = 1.0 - 2.0 / r0
    v2 = v_r * v_r + v_phi * v_phi
    g = 1.0 / math.sqrt(1.0 - v2)
    td0 = g / math.sqrt(f0)                      # dt/dtau
    rhod0 = g * math.sqrt(f0) * v_r * sq          # drho/ds = sqrt(r0) dr/dtau
    phid0 = g * v_phi / r0 * r0**1.5              # dphi/ds = r0^{3/2} dphi/dtau

    def rhs(s, Y):
        rho, rd, T, td, ph, pd = Y
        f = 1.0 - 2.0 / (r0 * rho)
        return [rd, -f * td * td / (rho * rho) + rd * rd / (r0 * rho * rho * f) + rho * f * pd * pd,
                td, -2.0 * td * rd / (r0 * rho * rho * f), pd, -2.0 * rd * pd / rho]

    def peri(s, Y):
        return Y[1]
    peri.direction = 1.0

    def stop(s, Y):
        return Y[0] - r_stop / r0
    stop.terminal, stop.direction = True, -1.0

    sol = integrate.solve_ivp(rhs, (0.0, tau_end / r0**1.5), [1.0, rhod0, 0.0, td0, 0.0, phid0], method="DOP853",
                              rtol=rtol, atol=rtol * 1e-3, dense_output=True, events=[peri, stop])
    s = np.linspace(0.0, sol.t[-1], n_out)
    Y = sol.sol(s)
    rho, rd, T, td, ph, pd = Y
    f = 1.0 - 2.0 / (r0 * rho)
    e = f * td
    l = sq * rho * rho * pd
    norm = -f * td * td + rd * rd / (r0 * f) + rho * rho * pd * pd / r0
    e0, l0 = f0 * td0, sq * phid0
    em1_0 = g * g * (v2 - 2.0 / r0)  # e^2 - 1 without cancellation
    em1_bind = abs(em1_0)
    return {"tau": s * r0**1.5, "t": T * r0**1.5, "r": r0 * rho, "phi": ph,
            "peri_phi": [float(y[4]) for y in sol.y_events[0]],
            "peri_tau": [float(x) * r0**1.5 for x in sol.t_events[0]],
            "stop_tau": float(sol.t_events[1][0]) * r0**1.5 if sol.t_events[1].size else None,
            "e0": e0, "l0": l0,
            "e_drift": float(np.max(np.abs(e - e0)) / e0),
            "l_drift": float(np.max(np.abs(l - l0)) / abs(l0)) if l0 != 0 else 0.0,
            "norm_drift": float(np.max(np.abs(norm + 1.0))),
            # the same relative to the binding energy |e^2 - 1| (review V4-8: in a weak field |e - 1| ~ 1e-8, and a
            # drift of e of 1e-9 relative to e would be 8 % of it); the attainable floor in these variables is
            # ~eps/|e^2 - 1| (e is carried as a number near 1)
            "em1": em1_0,
            "e_drift_binding": float(np.max(np.abs(e * e - e0 * e0)) / em1_bind) if em1_bind else None,
            "norm_drift_binding": float(np.max(np.abs(norm + 1.0)) / em1_bind) if em1_bind else None,
            "binding_floor": 2.2e-16 / em1_bind if em1_bind else None}
