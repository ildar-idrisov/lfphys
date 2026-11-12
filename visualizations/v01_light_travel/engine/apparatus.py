# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Time-of-flight apparatus of an observer: a rod of rest length L0, end A = the observer, end B = a mirror with a
clock. Flat spacetime only (gravity "none"; in GR runs the speed of light is measured locally, see world.py).

Construction (at the observer's current event, and again after every change of the observer's velocity - the
old apparatus is dismantled and a new one is assembled in the new rest frame):
* B is at rest relative to A at the rest-frame displacement L0 * e (e = +x or +y of the observer's rest frame);
  its lab worldline is obtained by transforming that rest-frame worldline with the laws' frame matrix (Lorentz in
  SR: this is where length contraction comes from; Galilean otherwise). Nothing is put in by hand.
* B's clock runs at its own proper rate; its reading is set by a synchronisation convention:
  - "einstein": A sends light to B, B reflects it, A receives it; B's reading at the reflection is defined as
    tau_A(send) + (tau_A(return) - tau_A(send))/2. The exchange is simulated with the run's light law and takes
    real time; until it is complete no one-way result exists;
  - "lab": B's clock agrees with A's at equal LAB times. Not available to the observer operationally (it needs
    the lab's simultaneity); shown for comparison, marked as such.

Measurements (all values come from clock readings at computed events):
* round trip:   2 L0 / (tau_A(return) - tau_A(send))  - convention-free;
* one-way A->B: L0 / (tau_B(reflect) - tau_A(send)),  B->A: L0 / (tau_A(return) - tau_B(reflect));
* a passing flash from another source: L0 / |tau_B(pass) - tau_A(pass)| with the order of passage giving the
  direction. A result becomes known to the observer at A only when the needed readings have reached A (B's
  reading travels to A as light) and the synchronisation is complete.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.worldlines import Piecewise
from lfphys.laws.light import Laws, flat_arrival


class Apparatus:
    def __init__(self, laws: Laws, owner: str, wl_a: Piecewise, L0: float, orient: str, sync: str):
        self.laws = laws
        self.owner = owner
        self.wl_a = wl_a
        self.L0 = float(L0)
        self.orient = orient  # "x" or "y" in the observer's rest frame
        self.sync = sync
        self.gen = 0  # generation; increments on every rebuild
        self.wl_b: Piecewise | None = None
        self.t_build = None
        self.offset_b = None  # tau_B = raw_B + offset
        self.t_sync_done = None
        self.sync_events = []

    @property
    def e_rest(self) -> np.ndarray:
        return np.array([1.0, 0.0]) if self.orient == "x" else np.array([0.0, 1.0])

    def build(self, t: float) -> list[dict]:
        """(Re)assemble at lab time t; returns the synchronisation events (with times) for the world."""
        laws = self.laws
        c = laws.c
        self.gen += 1
        self.t_build = t
        v = self.wl_a.vel(t)
        xa = self.wl_a.pos(t)
        M = laws.frame_matrix(v)  # lab -> rest frame
        Minv = laws.frame_matrix(-v)  # rest frame -> lab
        ev_a = M @ np.array([c * t, xa[0], xa[1]])
        ev_b = Minv @ (ev_a + np.concatenate([[0.0], self.L0 * self.e_rest]))
        t_b0 = ev_b[0] / c
        self.wl_b = Piecewise.start(laws, 0.0, t_b0, ev_b[1:], v, tau0=0.0)  # raw clock of B: 0 at t_b0
        self.offset_b = None
        self.t_sync_done = None
        self.sync_path = None
        events = []
        if self.sync == "lab":
            # equal readings at equal lab time t (both clocks run at the same rate afterwards)
            self.offset_b = self.wl_a.tau(t) - self.wl_b.tau(t)
            self.t_sync_done = t
            events.append({"t": t, "kind": "sync", "text": f"{self.owner}: часы B выставлены по лабораторной "
                           "одновременности (операционно недоступно наблюдателю)"})
        else:
            t1 = t
            t2 = self.light(t1, "A", "B")
            t3 = self.light(t2, "B", "A")
            tau1, tau3 = self.wl_a.tau(t1), self.wl_a.tau(t3)
            self.offset_b = tau1 + 0.5 * (tau3 - tau1) - self.wl_b.tau(t2)
            self.t_sync_done = t3
            self.sync_path = self.path([(t1, "A"), (t2, "B"), (t3, "A")])
            events += [
                {"t": t2, "kind": "sync", "pos": self.wl_b.pos(t2).tolist(),
                 "text": f"{self.owner}: сигнал синхронизации отражён от B"},
                {"t": t3, "kind": "sync", "text": f"{self.owner}: часы B синхронизированы по Эйнштейну "
                 f"(обмен занял {fmt_s(tau3 - tau1)} по часам A)"},
            ]
        return events

    def path(self, pts):
        """Events (t, x, y) of a light signal bouncing between the ends: [(t, end), ...]."""
        return [[t, *self.pos(e, t).tolist()] for t, e in pts]

    def pos(self, end: str, t: float) -> np.ndarray:
        return (self.wl_a if end == "A" else self.wl_b).pos(t)

    def reading(self, end: str, t: float) -> float | None:
        if end == "A":
            return self.wl_a.tau(t)
        if self.offset_b is None:
            return None
        return self.wl_b.tau(t) + self.offset_b

    def light(self, t_emit: float, src: str, dst: str) -> float:
        """Arrival time at end ``dst`` of light emitted by end ``src`` at t_emit (the run's light law)."""
        wl_s = self.wl_a if src == "A" else self.wl_b
        wl_d = self.wl_a if dst == "A" else self.wl_b
        res = flat_arrival(self.laws, t_emit, wl_s.pos(t_emit), wl_s.vel(t_emit), wl_d, t_emit)
        if res is None:
            raise ValueError("свет не догоняет конец стержня")
        return res["t"]

    def round_trip(self, t: float) -> dict:
        """Measurement started by A at t; returns the scheduled result (time known at A and the values)."""
        t2 = self.light(t, "A", "B")
        t3 = self.light(t2, "B", "A")
        tau1, tau3 = self.wl_a.tau(t), self.wl_a.tau(t3)
        out = {"t_start": t, "t_reflect": t2, "t_known": t3, "rt": 2 * self.L0 / (tau3 - tau1),
               "path": self.path([(t, "A"), (t2, "B"), (t3, "A")])}
        if self.t_sync_done is not None and self.t_sync_done <= t3:
            tb = self.reading("B", t2)
            out["ab"] = self.L0 / (tb - tau1)
            out["ba"] = self.L0 / (tau3 - tb)
        return out

    def known_time(self, t_a: float, t_b: float) -> float | None:
        """When A has both readings of passages at A (t_a) and B (t_b): B's reading travels to A as light (in the
        emission theory it may be slower than a flash, review R5); None before the clocks are synchronised."""
        if self.t_sync_done is None:
            return None
        if t_a > t_b:
            t_known = max(t_a, self.light(t_b, "B", "A"))
        else:
            t_known = self.light(t_b, "B", "A")
        return max(t_known, self.t_sync_done)

    def passing(self, t_a: float, t_b: float, dir_lab, v_light_lab) -> dict:
        """A flash passed end A at t_a and end B at t_b."""
        first, second = ("A", "B") if t_a <= t_b else ("B", "A")
        t_first, t_second = min(t_a, t_b), max(t_a, t_b)
        t_known = self.known_time(t_a, t_b)
        if t_known is None:
            return {"t_known": None}
        r_first, r_second = self.reading(first, t_first), self.reading(second, t_second)
        dt = r_second - r_first
        # direction of the light in the apparatus rest frame
        cosang = _cos_in_rest_frame(self.laws, self.wl_a.vel(t_a), np.asarray(v_light_lab, float), self.e_rest)
        speed = self.L0 / dt if dt > 0 else math.inf
        return {"t_known": t_known, "speed": speed, "order": first + "→" + second, "cos": cosang,
                "dtau": dt}


def _cos_in_rest_frame(laws: Laws, v_app, u_light, e_rest) -> float:
    """Cosine between the light's velocity in the apparatus rest frame and the rod direction."""
    c = laws.c
    if laws.relativistic:
        M = laws.frame_matrix(v_app)
        k = M @ np.array([c, u_light[0], u_light[1]])  # 4-velocity-like (c, u) transforms as (ct, x)
        u = c * k[1:] / k[0]
    else:
        u = u_light - v_app
    return float(u @ e_rest / np.linalg.norm(u))


def fmt_s(x: float) -> str:
    a = abs(x)
    if a == 0:
        return "0 с"
    for unit, k in (("с", 1.0), ("мс", 1e-3), ("мкс", 1e-6), ("нс", 1e-9), ("пс", 1e-12)):
        if a >= k:
            return f"{x / k:.6g} {unit}"
    return f"{x:.3e} с"
