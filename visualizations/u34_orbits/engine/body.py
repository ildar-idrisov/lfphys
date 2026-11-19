# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Tracks of one test body: the computed orbit, held ahead of the world time and revealed as the time reaches it.

Orchestration only (RULES.md §2.2, lfphys/LAYERS.md rule 5): the general-relativistic orbit comes from
``lfphys.core.gravity.orbit_stream`` (exact Schwarzschild geodesic, events located by the integrator), the Newtonian
one from ``lfphys.theories.approx.newton.integrate_body_regularized`` (Levi-Civita). Here: chunking, the time line (what is revealed when),
thinning of samples for drawing, and the measurements a run makes on its own orbit (apsides of the Newtonian
orbit as zeros of r.v, the energy and angular momentum along it).

Units: lengths in M = GM/c^2, times in GM/c^3, velocities in c (the static observer's measure in GR).
"""

from __future__ import annotations

import math
import time

import numpy as np

from lfphys.core.gravity import orbit_stream
from lfphys.theories.approx import newton

TWO_PI = 2.0 * math.pi
MAX_KEEP = 96  # fine Newtonian chunks kept for exact states (frames, actions; ~10-30 chunks per orbit)


class Track:
    """Common part: a buffer of computed samples (t, x, y, r, rate, tau) and events, revealed in time order."""

    theory = "?"

    def __init__(self, t0: float, tau0: float):
        self.t0, self.tau0 = float(t0), float(tau0)
        self.buf = {k: np.zeros(0) for k in ("t", "x", "y", "r", "lag", "tau")}
        self.pending: list[dict] = []   # computed events not yet revealed (time order)
        self.covered = self.t0          # coordinate time up to which the orbit is computed
        self.done: str | None = None    # computed end: horizon / surface / center / escape
        self.end_event: dict | None = None
        self.last = None                # the last revealed sample (dict)
        self.dyn = 1.0                  # dynamical time scale (M units) for chunking
        self.caught_up = True           # False while a budgeted take() has not reached the requested time

    # --- filled by subclasses -------------------------------------------------------------------------
    def _chunk(self, t_until: float) -> None:
        raise NotImplementedError

    def state(self, t: float) -> dict:
        raise NotImplementedError

    # --- common -----------------------------------------------------------------------------------------
    def _push(self, t, x, y, r, lag, tau, events):
        """Append computed samples: coordinate time, position, the clock lag 1 - dtau/dt, proper time (M units)."""
        for k, a in zip(("t", "x", "y", "r", "lag", "tau"), (t, x, y, r, lag, tau)):
            self.buf[k] = np.concatenate([self.buf[k], np.asarray(a, float)])
        self.pending.extend(events)
        self.pending.sort(key=lambda d: d["t"])
        if len(t):
            self.covered = max(self.covered, float(t[-1]))

    def ensure(self, t: float, ahead: float | None = None, budget: float | None = None) -> bool:
        """Compute the orbit at least up to the coordinate time t (plus a margin, to keep chunks long). With a wall-time
        budget (seconds) stop early; returns True when the orbit is computed up to t (or has ended)."""
        margin = 0.125 * self.dyn if ahead is None else ahead
        guard = 0
        w0 = time.monotonic()
        while self.done is None and self.covered < t and guard < 100000:
            self._chunk(max(t, self.covered) + margin)
            guard += 1
            if budget is not None and time.monotonic() - w0 > budget:
                break
        return self.done is not None or self.covered >= t

    def take(self, t: float, budget: float | None = None) -> tuple[dict | None, list[dict]]:
        """The samples and events with time <= t that were not revealed yet (they are removed from the buffer). With
        a budget only what was computed within it is revealed (up to min(t, computed)): a catch-up in slices."""
        complete = self.ensure(t, budget=budget)
        if not complete:
            t = min(t, self.covered)
        self.caught_up = complete
        n = int(np.searchsorted(self.buf["t"], t, side="right"))
        out = None
        if n:
            out = {k: v[:n] for k, v in self.buf.items()}
            self.buf = {k: v[n:] for k, v in self.buf.items()}
            self.last = {k: float(v[-1]) for k, v in out.items()}
        evs = [e for e in self.pending if e["t"] <= t]
        self.pending = [e for e in self.pending if e["t"] > t]
        return out, evs

    def next_event_after(self, t: float, kinds=None) -> float | None:
        """The time of the next computed event after t (computing ahead, with a look-ahead that grows by 1.5 per
        chunk, so that a slow escape to 1000 r0 is reached too)."""
        step = self.dyn
        for _ in range(200):
            for e in self.pending:
                if e["t"] > t and (kinds is None or e["kind"] in kinds):
                    return e["t"]
            if self.done is not None:
                return None
            self._chunk(self.covered + step)
            step *= 1.5
        return None

    def ended(self, t: float) -> bool:
        return self.end_event is not None and self.end_event["t"] <= t


class GRTrack(Track):
    """Schwarzschild geodesic (core): lfphys.core.gravity.orbit_stream."""

    theory = "GR"

    def __init__(self, r0, phi0, v_r, v_phi, *, t0=0.0, tau0=0.0, r_stop=2.0, n_turn=240):
        super().__init__(t0, tau0)
        self.s = orbit_stream.OrbitStream(r0, v_r, v_phi, phi0=phi0, r_stop=r_stop, n_turn=n_turn)
        self.info = dict(self.s.info)
        self.e, self.l, self.em1 = self.s.e, self.s.l, self.s.em1
        r_ref = self.info.get("r_apo") or r0
        r_ref = r_ref if (r_ref and math.isfinite(r_ref)) else r0
        self.dyn = TWO_PI * max(r0, min(r_ref, 1e3 * r0)) ** 1.5
        self._chunk(self.t0 + 0.125 * self.dyn)  # the state at the start exists from construction on

    def _chunk(self, t_until):
        ch = self.s.advance(t_until - self.t0, max_turns=2.0)
        t = ch["t"] + self.t0
        r, phi = ch["r"], ch["phi"]
        evs = []
        for e in ch["events"]:
            e = dict(e)
            e["t"] += self.t0
            e["tau"] += self.tau0
            e["x"], e["y"] = e["r"] * math.cos(e["phi"]), e["r"] * math.sin(e["phi"])
            evs.append(e)
            if e["kind"] in ("horizon", "surface", "escape"):
                self.end_event = e
        self._push(t, r * np.cos(phi), r * np.sin(phi), r, self.s.clock_lag(r), ch["tau"] + self.tau0, evs)
        self.done = self.s.done

    def state(self, t, exact=False):
        """Exact state at t (dense output of the integrator); after the end: the end state."""
        self.ensure(t)
        if self.end_event is not None and t >= self.end_event["t"]:
            e = self.end_event
            return {"x": e["x"], "y": e["y"], "r": e["r"], "phi": e["phi"], "tau": e["tau"],
                    "rate": float(self.s.clock_rate(e["r"])), "lag": float(self.s.clock_lag(e["r"])),
                    "v_r": e["v_r"], "v_phi": e["v_phi"], "alive": False}
        st = self.s.state_at(t - self.t0)
        if st is None:  # outside the chunks kept: interpolate the samples (display only)
            return self._interp(t)
        r, phi = st["r"], st["phi"]
        return {"x": r * math.cos(phi), "y": r * math.sin(phi), "r": r, "phi": phi, "tau": st["tau"] + self.tau0,
                "rate": float(self.s.clock_rate(r)), "lag": float(self.s.clock_lag(r)), "v_r": st["v_r"],
                "v_phi": st["v_phi"], "alive": True}

    def _interp(self, t):
        b = self.buf
        if self.last is None and not len(b["t"]):
            return None
        ts = np.concatenate([[self.last["t"]] if self.last else [], b["t"]])
        out = {}
        for k in ("x", "y", "r", "tau", "lag"):
            vs = np.concatenate([[self.last[k]] if self.last else [], b[k]])
            out[k] = float(np.interp(t, ts, vs))
        out["phi"] = math.atan2(out["y"], out["x"])
        out.update(rate=float(self.s.clock_rate(out["r"])), lag=float(self.s.clock_lag(out["r"])), v_r=None, v_phi=None,
                   alive=True)
        return out


class NewtonTrack(Track):
    """Newtonian body (approximation outside the core): lfphys.theories.approx.newton.integrate_body_regularized.

    Every chunk is integrated in units of its own start radius r_c (GM = 1, time unit r_c^{3/2}), so that the engine's
    tolerance (relative 1e-12, absolute 1e-12 of the position scale) is uniform in position and velocity at every depth
    of an eccentric orbit; a chunk ends when the body has fallen to r_c/4 (the engine's stop radius) or after half a
    local dynamical time, and the next one is rescaled (review V4-4: one scale r0 for the whole orbit lost the
    periapsis region of eccentric orbits). The swept angle is accumulated from the angle between successive samples
    (atan2 of their cross and dot products; the samples are dense enough that it is below pi)."""

    theory = "newton"

    def __init__(self, r0, phi0, v_r, v_phi, *, t0=0.0, tau0=0.0, r_stop=0.0, r_far=None, n_turn=240):
        super().__init__(t0, tau0)
        c, s = math.cos(phi0), math.sin(phi0)
        # absolute state: positions in M, velocities in c, time in GM/c^3 (GM = 1)
        self.X = np.array([r0 * c, r0 * s, v_r * c - v_phi * s, v_r * s + v_phi * c])
        self.r0 = float(r0)
        self.phi0 = float(phi0)
        self.sense = 1.0 if v_phi >= 0 else -1.0
        self.tl = 0.0  # time of the chunk start since t0 (M units)
        self.n_turn = int(n_turn)
        self.point_mass = r_stop <= 0
        self.R = r_stop if r_stop > 0 else 1e-6 * r0  # a point mass stops the body at 1e-6 r0
        x, y, vx, vy = self.X
        self.E0 = 0.5 * (vx * vx + vy * vy) - 1.0 / r0
        self.h0 = x * vy - y * vx
        self.ecc = math.sqrt(max(1.0 + 2.0 * self.E0 * self.h0 * self.h0, 0.0))
        p = self.h0 * self.h0
        self.period = TWO_PI * (-0.5 / self.E0) ** 1.5 if self.E0 < 0 else None
        if self.h0 == 0.0:  # radial: rises to -1/E (bound) and falls to the centre
            r_peri, r_apo = 0.0, (-1.0 / self.E0 if self.E0 < 0 else None)
        else:
            r_peri = p / (1.0 + self.ecc)
            r_apo = p / (1.0 - self.ecc) if self.ecc < 1 else None
        moving = 1 if v_r > 0 else (-1 if v_r < 0 else 0)
        spread = (r_apo - r_peri) / r_peri if (r_apo is not None and r_peri > 0) else None
        if spread is not None and spread <= orbit_stream.CIRCULAR_SPREAD:
            kind = "circular"
        elif r_peri <= self.R:
            # the periapsis lies below the surface: a fall, unless the body moves outward on an unbound orbit
            kind = "escape" if (self.E0 >= 0 and moving > 0) else "plunge"
        elif self.E0 < 0:
            kind = "bound"
        else:
            kind = "escape"
        self.info = {"kind": kind, "r_peri": r_peri, "r_apo": r_apo, "ecc": self.ecc, "spread": spread,
                     "a": (-0.5 / self.E0) if self.E0 < 0 else None, "period": self.period, "moving": moving}
        far = r_far or 1e3 * r0
        if r_apo is not None:
            far = max(far, 1.5 * r_apo)  # a bound orbit is followed out to its apoapsis (review V4-6)
        self.r_far = far
        # the integrator (EX2 §11 item 10; W34's CI fix of 2026-11-19): the Levi-Civita regularised one where the orbit
        # dives deep (its largest term v²/2 + GM/r exceeds |E| by more than 1e3, so that the coordinate-time integration's
        # 1e-12 of that term would exceed 1e-9 of |E|: r_p < 2e-3 of a, of r0 for an unbound orbit, a radial fall), the
        # coordinate-time one elsewhere: on a smooth orbit its states are consistent to ~1e-15, while the regularised
        # output (inverted from its fictitious time) scatters by ~1e-12, which a nearly circular orbit's apsis turns into
        # ~1e-6 rad (measured: 0.69″ against 0.0009″ at r0 50 M, speed 1.0000004, under ulp changes of the start)
        scale = (-0.5 / self.E0) if self.E0 < 0 else r0
        self.regularised = self.h0 == 0.0 or r_peri < 2e-3 * scale
        self.dyn = self.period or TWO_PI * r0**1.5
        self.chunks: list[dict] = []
        self.psi_prev = 0.0  # swept angle at the chunk start
        self.drift = {"E": 0.0, "h": 0.0, "scale": abs(self.E0)}  # scale: the largest energy term seen
        self.n_lap = 0
        self.last_kept = None
        self._chunk(self.t0 + 0.125 * self.dyn)

    def _fine(self, Xl, dt, n, r_stop):
        """The engine's integration of one chunk: Levi-Civita regularised (``newton.integrate_body_regularized``; EX2
        §11 item 10, STATUS V19 (e)) on a deep orbit, smooth through its periapsis where the coordinate-time integration
        lost ~1e-5 of |E|; ``newton.integrate_body`` on the others (see ``regularised`` in the constructor)."""
        f = newton.integrate_body_regularized if self.regularised else newton.integrate_body
        return f((Xl[0], Xl[1]), (Xl[2], Xl[3]), 1.0, dt, n_out=n, r_stop=r_stop)

    def _chunk(self, t_until):
        rc = math.hypot(self.X[0], self.X[1])
        T = rc**1.5
        k = math.sqrt(rc)
        Xl = np.array([self.X[0] / rc, self.X[1] / rc, self.X[2] * k, self.X[3] * k])  # local units
        # at most half a local dynamical time, and shorter than the fastest fall from rc to rc/4 that the local speed
        # allows (energy: v^2 <= v_0^2 + 6 above rc/4, so the fall takes at least 0.75/sqrt(v_0^2 + 6)): a chunk then
        # never dips below rc/4 and comes back within it. The regularised integration (EX2 §11 item 10) passes a deep
        # periapsis in one smooth step of its fictitious time, so its stop event at rc/4 alone could miss such a dip
        # and leave the periapsis between two samples uniform in t (measured: -360 deg «advance» at a -89.9 deg launch)
        v_l = math.hypot(Xl[2], Xl[3])
        dt = min((t_until - self.t0 - self.tl) / T, math.pi, 0.9 * 0.75 / math.sqrt(v_l * v_l + 6.0))
        dt = max(dt, 1e-9)
        n = max(64, int(640 * dt) + 2)  # ~4000 samples per local 2 pi
        R_l = self.R / rc
        stop_l = max(R_l, 0.25)
        o = self._fine(Xl, dt, n, stop_l)
        ts, x, y, vx, vy = o["t"], o["x"], o["y"], o["vx"], o["vy"]
        r = np.hypot(x, y)
        reason = None
        if o["status"] == "hit" and abs(r[-1] - R_l) <= 1e-9 * max(R_l, 1e-300) + 1e-12:
            reason = "center" if self.point_mass else "surface"
        far = np.nonzero(r >= self.r_far / rc)[0]
        # swept angle: the angle between successive samples (< pi on this grid)
        dpsi = np.arctan2(x[:-1] * y[1:] - y[:-1] * x[1:], x[:-1] * x[1:] + y[:-1] * y[1:])
        psi = self.psi_prev + self.sense * np.concatenate([[0.0], np.cumsum(dpsi)])
        esc = None
        if far.size and far[0] > 0:  # escape: locate r = r_far between the bracketing samples, end there
            i = int(far[0])
            esc = self._refine("escape", ts, x, y, vx, vy, psi, i - 1, lambda X: np.hypot(X[0], X[1]) - self.r_far / rc,
                               rc)
            Xs = esc.pop("_local")
            ts = np.append(ts[:i], esc.pop("_tl"))
            x, y, vx, vy = (np.append(a[:i], b) for a, b in zip((x, y, vx, vy), Xs))
            psi = np.append(psi[:i], esc["psi"])
            r = np.hypot(x, y)
            reason = "escape"
        # conservation along the integrated orbit (the run's own measurement), in absolute units
        E = (0.5 * (vx * vx + vy * vy) - 1.0 / r) / rc
        h = (x * vy - y * vx) * k
        self.drift["E"] = max(self.drift["E"], float(np.max(np.abs(E - self.E0))) / abs(self.E0))
        self.drift["h"] = max(self.drift["h"], float(np.max(np.abs(h - self.h0))) / abs(self.h0)) if self.h0 else 0.0
        self.drift["scale"] = max(self.drift["scale"], float(np.max(0.5 * (vx * vx + vy * vy) + 1.0 / r)) / rc)
        events = []
        g0 = x[0] * vx[0] + y[0] * vy[0]
        launch = self.tl == 0.0
        if self.info["kind"] != "circular" and launch and abs(g0) <= 1e-13 * r[0] * math.hypot(vx[0], vy[0]):
            # a launch exactly at a turning point (r.v = 0): an apsis at t0, the kind from where r goes next
            kind = "peri" if r[1] > r[0] else "apo"
            events.append(self._sample_event(kind, ts[0], x[0], y[0], vx[0], vy[0], psi[0], rc))
        if self.info["kind"] != "circular":
            g = x * vx + y * vy
            if launch and events:
                g[0] = 0.0  # the launch apsis is counted once
            for i in np.nonzero(np.sign(g[:-1]) * np.sign(g[1:]) < 0)[0]:
                kind = "peri" if g[i] < 0 else "apo"
                ev = self._refine(kind, ts, x, y, vx, vy, psi, i, lambda X: X[0] * X[2] + X[1] * X[3], rc)
                ev.pop("_local"), ev.pop("_tl")
                events.append(ev)
        for nlap in range(int(math.floor(psi[0] / TWO_PI)) + 1, int(math.floor(psi[-1] / TWO_PI)) + 1):
            j = int(np.searchsorted(psi, TWO_PI * nlap))
            if 0 < j < len(psi):
                ev = self._refine("lap", ts, x, y, vx, vy, psi, j - 1, None, rc, psi_target=TWO_PI * nlap)
                ev.pop("_local"), ev.pop("_tl")
                ev["n"] = nlap
                events.append(ev)
        if esc is not None:
            events.append(esc)
        elif reason:
            events.append(self._sample_event(reason, ts[-1], x[-1], y[-1], vx[-1], vy[-1], psi[-1], rc))
        # absolute samples; thinning for drawing (vectorised): a new sample when the swept angle, the time or ln r
        # passes to the next step of a fixed grid
        tt = self.t0 + self.tl + ts * T
        xa, ya, ra = x * rc, y * rc, r * rc
        self.chunks.append({"t": tt, "x": xa, "y": ya, "vx": vx / k, "vy": vy / k, "rc": rc})
        self.chunks = self.chunks[-MAX_KEEP:]
        keep = self._thin(tt, ra, psi)
        self._push(tt[keep], xa[keep], ya[keep], ra[keep], np.zeros(keep.size), tt[keep] - self.t0 + self.tau0,
                   sorted(events, key=lambda d: d["t"]))
        for e in events:
            if e["kind"] in ("surface", "center", "escape"):
                self.end_event = e
            if e["kind"] == "lap":
                self.n_lap += 1
        self.X = np.array([xa[-1], ya[-1], vx[-1] / k, vy[-1] / k])
        self.tl += ts[-1] * T
        self.psi_prev = float(psi[-1])
        if reason:
            self.done = reason

    def _thin(self, tt, ra, psi):
        """Samples kept for drawing (the orbit, r(t)): a new one at every 1/n_turn of a turn in angle, every 1/60 of a
        period in time (what a radial orbit needs) and every 2 % in r (a deep fall); the chunk's last one. (Drawing
        only: the apsides and the measurements come from the full samples; EX2's atlases measured 595 samples per
        orbit with steps of 1/240 and 1 %, twice the general-relativistic trail's.)"""
        step_a = TWO_PI / self.n_turn
        step_t = (self.period or TWO_PI * self.r0**1.5) / 60.0
        key = np.stack([np.floor(psi / step_a), np.floor(tt / step_t), np.floor(np.log(ra) / math.log(1.02))])
        first = key[:, :1] - 1.0 if self.last_kept is None else self.last_kept[:, None]  # the first sample is kept
        prev = np.concatenate([first, key[:, :-1]], axis=1)
        change = np.any(key != prev, axis=0)
        change[-1] = True
        self.last_kept = key[:, -1]
        return np.nonzero(change)[0]

    def _sample_event(self, kind, ts, x, y, vx, vy, psi, rc):
        """An event at a local-unit sample of the current chunk, in absolute units."""
        r = math.hypot(x, y)
        k = math.sqrt(rc)
        rh = (x / r, y / r)
        v_r = (vx * rh[0] + vy * rh[1]) / k
        v_phi = (-vx * rh[1] + vy * rh[0]) / k
        t = self.t0 + self.tl + ts * rc**1.5
        return {"kind": kind, "t": t, "tau": t - self.t0 + self.tau0, "r": r * rc, "phi": math.atan2(y, x),
                "psi": psi, "x": x * rc, "y": y * rc, "v_r": v_r, "v_phi": v_phi,
                "E": (0.5 * (vx * vx + vy * vy) - 1.0 / r) / rc}

    def _refine(self, kind, ts, x, y, vx, vy, psi, i, g, rc, psi_target=None):
        """Locate a zero between samples i and i+1 on a second, 1000 times finer integration by the engine from the
        state at sample i (linear interpolation on that grid)."""
        X = np.array([x[i], y[i], vx[i], vy[i]])
        dt = ts[i + 1] - ts[i]
        o = self._fine(X, dt, 1001, max(self.R / rc, 1e-12))
        F = np.stack([o["x"], o["y"], o["vx"], o["vy"]])
        if psi_target is not None:
            d = np.arctan2(x[i] * F[1] - y[i] * F[0], x[i] * F[0] + y[i] * F[1])
            vals = psi[i] + self.sense * d - psi_target
        else:
            vals = g(F)
        j = np.nonzero(np.sign(vals[:-1]) * np.sign(vals[1:]) <= 0)[0]
        j = int(j[0]) if j.size else 0
        w = vals[j] / (vals[j] - vals[j + 1]) if vals[j] != vals[j + 1] else 0.0
        Xs = F[:, j] + w * (F[:, j + 1] - F[:, j])
        tz = ts[i] + o["t"][j] + w * (o["t"][j + 1] - o["t"][j])
        if psi_target is not None:
            ps = psi_target
        else:  # swept angle at the zero, relative to sample i
            ps = psi[i] + self.sense * math.atan2(x[i] * Xs[1] - y[i] * Xs[0], x[i] * Xs[0] + y[i] * Xs[1])
        ev = self._sample_event(kind, tz, *Xs, ps, rc)
        ev["_local"], ev["_tl"] = Xs, tz
        return ev

    def state(self, t, exact=False):
        """The state at t: for frames the cubic Hermite interpolant of the fine samples (velocity from its
        derivative); exact=True (an action needs it) re-integrates with the engine from the nearest sample."""
        self.ensure(t)
        if self.end_event is not None and t >= self.end_event["t"]:
            e = self.end_event
            return {"x": e["x"], "y": e["y"], "r": e["r"], "phi": e["phi"], "tau": e["tau"], "rate": 1.0, "lag": 0.0,
                    "v_r": e["v_r"], "v_phi": e["v_phi"], "alive": False}
        for ch in reversed(self.chunks):
            tt = ch["t"]
            if tt[0] <= t <= tt[-1]:
                j = int(min(max(np.searchsorted(tt, t) - 1, 0), len(tt) - 2))
                if exact:
                    rc = ch["rc"]
                    k = math.sqrt(rc)
                    Xl = (ch["x"][j] / rc, ch["y"][j] / rc, ch["vx"][j] * k, ch["vy"][j] * k)
                    dt = (t - tt[j]) / rc**1.5
                    if dt > 0:
                        o = self._fine(Xl, dt, 2, 1e-12)
                        Xl = (o["x"][-1], o["y"][-1], o["vx"][-1], o["vy"][-1])
                    xx, yy, vx, vy = Xl[0] * rc, Xl[1] * rc, Xl[2] / k, Xl[3] / k
                else:
                    h = tt[j + 1] - tt[j]
                    s = (t - tt[j]) / h if h > 0 else 0.0
                    h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
                    d00, d10, d01, d11 = 6 * s**2 - 6 * s, 3 * s**2 - 4 * s + 1, -6 * s**2 + 6 * s, 3 * s**2 - 2 * s
                    X0, X1 = (ch["x"][j], ch["y"][j]), (ch["x"][j + 1], ch["y"][j + 1])
                    V0, V1 = (ch["vx"][j], ch["vy"][j]), (ch["vx"][j + 1], ch["vy"][j + 1])
                    xx, yy = (h00 * X0[i] + h10 * h * V0[i] + h01 * X1[i] + h11 * h * V1[i] for i in (0, 1))
                    vx, vy = ((d00 * X0[i] + d01 * X1[i]) / h + d10 * V0[i] + d11 * V1[i] if h > 0 else V0[i]
                              for i in (0, 1))
                r = math.hypot(xx, yy)
                return {"x": xx, "y": yy, "r": r, "phi": math.atan2(yy, xx), "tau": t - self.t0 + self.tau0,
                        "rate": 1.0, "lag": 0.0, "v_r": (vx * xx + vy * yy) / r, "v_phi": (-vx * yy + vy * xx) / r,
                        "alive": True}
        L = self.last
        if L is not None:
            return {"x": L["x"], "y": L["y"], "r": L["r"], "phi": math.atan2(L["y"], L["x"]),
                    "tau": t - self.t0 + self.tau0, "rate": 1.0, "lag": 0.0, "v_r": None, "v_phi": None,
                    "alive": True}
        b = self.buf
        x0 = self.X[0] if not len(b["x"]) else b["x"][0]
        y0 = self.X[1] if not len(b["y"]) else b["y"][0]
        return {"x": x0, "y": y0, "r": math.hypot(x0, y0), "phi": math.atan2(y0, x0), "tau": self.tau0, "rate": 1.0,
                "lag": 0.0, "v_r": None, "v_phi": None, "alive": True}
