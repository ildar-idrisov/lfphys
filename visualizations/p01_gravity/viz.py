# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p01: the gravity playground (plan P15.1; owner, 2026-10-28: «силумировать поведение например черной дыры или
исследовать гравитацию»). A wrapper over the engine ``lfphys``; the framework is ``lfviz.playground``.

The laws of the world (a world parameter; a change starts a new world):

* ``newton`` — Newtonian gravity of N bodies (``lfphys.core.gravity.nbody``): stars, planets, black holes as point
  masses (a black hole here is a Newtonian mass with its Schwarzschild radius as a capture radius: an approximation,
  flagged), massless test bodies; close encounters by an adaptive time-symmetric Hermite scheme; collisions merge or
  pass (a law of the world). Units: au, years, solar masses inside; the world's time in seconds.
* ``pn`` — a binary of two compact bodies by the post-Newtonian equations of motion (``core.gravity.pn_binary``: 1PN,
  2PN, radiation reaction at 2.5PN and 3.5PN), its gravitational waves by the quadrupole formula
  (``core.gravity.gw_quadrupole``) at a detector placed in the scene, and the energy the waves carry against the
  orbit's loss. Units G = c = m = 1 inside (m the total mass); the world's time in seconds.
* ``kerr`` — test bodies, light and observers with clocks around a rotating, charged black hole (the Kerr–Newman
  metric, ``core.gravity.kerr_newman``): geodesics, each body's proper time, the conserved E, L and Carter's constant.
  Units G = c = M = 1 inside; the world's time is the distant observer's t, in seconds for the hole's mass.

The scene's objects are the experimenter's set-up, changed at the current moment (``lfviz.playground``); each mode's
conservation laws are checked as the world runs.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import constants as K
from lfphys.core.gravity import gw_quadrupole as GW, kerr_newman as KN, nbody as NB, pn_binary as PN
from lfphys.theories.alternatives import kn_change_whatif as WHATIF
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param

MPC = 3.0856775814913673e22  # m (IAU 2015: 1 pc = 648000/pi au)
# Trails (review UX-ui U2, UX-3d A13: one point per frame joined by chords drew Mercury as a pentagon and the Earth at
# x10 as a line). The solvers offer points of their own continuous output at most CAND_TURN apart in the direction of
# motion (and CAND_DSPEED in speed); a trail keeps a point when the direction has turned by more than TRAIL_TURN since
# the last kept one (or the speed changed by more than TRAIL_DSPEED), with the position, the velocity and the time, and
# the view draws each piece between two kept points as the cubic Hermite curve of their positions and velocities,
# split into chords of at most 2 degrees of turn (``web/view.js``): on a circle the curve is off by r theta^4/384 =
# 3.9e-5 r at theta = 20 degrees and a chord by r (1 - cos 1 deg) = 1.5e-4 r, together under 2e-4 of the local
# radius of curvature: below 0.25 px for any orbit whose radius on the screen is under ~1200 px, at any speed.
TRAIL_TURN = math.radians(20.0)
TRAIL_DSPEED = 0.2
CAND_TURN = math.radians(10.0)
CAND_DSPEED = 0.1
TRAIL_KEEP = 300  # points kept per trail for a segment's start (the view draws as many: web/view.js)
TRAIL_FRAME_MAX = 300  # points of one trail in one frame at most (beyond: the latest ones after a break)
ENDED_KEEP = 32  # trails of bodies that merged into another, kept and drawn (the latest ones)


def _turns(v0, v1):
    """Angle between the rows of v0 and v1 (0 where either is zero)."""
    return np.arctan2(np.linalg.norm(np.cross(v0, v1), axis=1), np.einsum("ij,ij->i", v0, v1))


def _dspeed(v0, v1):
    a, b = np.linalg.norm(v0, axis=1), np.linalg.norm(v1, axis=1)
    m = np.maximum(a, b)
    return np.abs(b - a) / np.where(m > 0, m, 1.0)


class Trails:
    """The trails of a mode's bodies, from the points its solver offers (``trail_feed``): a point is kept when the
    direction of motion has turned by more than TRAIL_TURN since the last kept one or the speed changed by more than
    TRAIL_DSPEED (the candidate before it is kept first, so two kept points are never farther apart than that); a kept
    point carries its position, velocity and time (the view joins two by a Hermite curve). A break (an edit that moves
    or kicks a body, a merger) ends a piece. ``trail_new``: the points since the last trail message; ``trail_kept``:
    the last TRAIL_KEEP points sent. A trail message goes out on every frame with new points; a segment of the record
    starts with the kept points (``emit_trails(full=True)``, marked ``reset``) and changes nothing in the world (review
    B6-F5, F8). Positions in the scene's units, velocities in them per world second, times in world seconds."""

    def _trails_init(self):
        self.trail_new = {}    # key -> [(t, x, v) or None (a break)]
        self.trail_kept = {}   # key -> the last TRAIL_KEEP entries sent
        self.trail_ended = []  # keys of ended trails still kept, oldest first
        self._rgb_end = {}     # their colours (the object is gone)
        self.n_frames = 0
        self._ord = ()         # the keys of the rows of _L and _P
        self._L = (np.zeros(0), np.zeros((0, 3)), np.zeros((0, 3)))  # the last kept point of each row (t NaN: none)
        self._P = (np.zeros(0), np.zeros((0, 3)), np.zeros((0, 3)))  # the last candidate not kept (t NaN: none)

    def _rows(self, keys):
        keys = tuple(keys)
        if keys == self._ord:
            return
        old = {k: i for i, k in enumerate(self._ord)}
        for k, j in old.items():  # a body that stops moving (captured, gone): its trail ends at its last candidate
            if k not in keys and not np.isnan(self._P[0][j]):
                self._keep(k, self._P[0][j], self._P[1][j], self._P[2][j])
        n = len(keys)
        L = (np.full(n, np.nan), np.zeros((n, 3)), np.zeros((n, 3)))
        P = (np.full(n, np.nan), np.zeros((n, 3)), np.zeros((n, 3)))
        for i, k in enumerate(keys):
            j = old.get(k)
            if j is not None:
                for a, b in zip(L + P, self._L + self._P):
                    a[i] = b[j]
        self._ord, self._L, self._P = keys, L, P

    def _keep(self, k, t, x, v):
        self.trail_new.setdefault(k, []).append((float(t), np.array(x, float), np.array(v, float)))

    def trail_feed(self, t, keys, X, V, force=False):
        """A candidate point of every body (rows of X, V in ``keys`` order) at time t; ``force``: keep it for all."""
        self._rows(keys)
        if not len(keys):
            return
        X, V = np.asarray(X, float), np.asarray(V, float)
        Lt, LX, LV = self._L
        Pt, PX, PV = self._P
        fresh = np.isnan(Lt)
        with np.errstate(invalid="ignore"):
            ex = fresh | (_turns(V, LV) > TRAIL_TURN) | (_dspeed(V, LV) > TRAIL_DSPEED)
        if force:
            ex[:] = True
        hasP = ~np.isnan(Pt)
        r1 = np.flatnonzero(ex & hasP & ~fresh)
        for i in r1:  # the candidate before keeps the spacing within the limits
            self._keep(keys[i], Pt[i], PX[i], PV[i])
        Lt[r1], LX[r1], LV[r1] = Pt[r1], PX[r1], PV[r1]
        now = ex & ~hasP | fresh
        if len(r1):
            again = (_turns(V[r1], LV[r1]) > TRAIL_TURN) | (_dspeed(V[r1], LV[r1]) > TRAIL_DSPEED)
            now[r1] = again | force
        for i in np.flatnonzero(now):
            self._keep(keys[i], t, X[i], V[i])
        Lt[now], LX[now], LV[now] = t, X[now], V[now]
        Pt[now] = np.nan
        rest = ~now
        Pt[rest], PX[rest], PV[rest] = t, X[rest], V[rest]

    def trail_break(self, k):
        """The body's state jumps here (an edit, a merger): the next point starts a new piece."""
        self.trail_new.setdefault(k, []).append(None)
        if k in self._ord:
            self._L[0][self._ord.index(k)] = np.nan
            self._P[0][self._ord.index(k)] = np.nan

    def trail_kink(self, t, pre, post):
        """An edit at time t: ``pre`` and ``post`` = (keys, X, V) before and after it. Every body keeps its point at t;
        a body whose position or velocity changed starts a new piece; a body removed keeps its trail no more."""
        kp, Xp, Vp = pre
        if len(kp):
            self.trail_feed(t, kp, Xp, Vp, force=True)
        ka, Xa, Va = post
        before = {k: i for i, k in enumerate(kp)}
        for i, k in enumerate(ka):
            j = before.get(k)
            if j is not None and not (np.array_equal(Xp[j], Xa[i]) and np.array_equal(Vp[j], Va[i])):
                self.trail_break(k)
        if len(ka):
            self.trail_feed(t, ka, Xa, Va)

    def trail_end(self, k):
        """The body is gone (merged into another): its trail keeps the points it has and is drawn on."""
        if k in self._ord:
            i = self._ord.index(k)
            if not np.isnan(self._P[0][i]):
                self._keep(k, self._P[0][i], self._P[1][i], self._P[2][i])
        self._rgb_end[k] = self._trail_rgb([k])[0]
        if k in self.trail_ended:
            self.trail_ended.remove(k)
        self.trail_ended.append(k)
        while len(self.trail_ended) > ENDED_KEEP:
            gone = self.trail_ended.pop(0)
            self.trail_new.pop(gone, None)
            self.trail_kept.pop(gone, None)
            self._rgb_end.pop(gone, None)

    def _trail_drop(self, k):
        """The body was removed by hand: its trail goes (the views drop it at the full message that follows)."""
        self.trail_new.pop(k, None)
        self.trail_kept.pop(k, None)
        self._rgb_end.pop(k, None)
        if k in self.trail_ended:
            self.trail_ended.remove(k)

    def trail_tick(self):
        self.n_frames += 1
        self.emit_trails()

    def emit_trails(self, full=False):
        if full:
            ids = [k for k, v in self.trail_kept.items() if v]
            ent = {k: self.trail_kept[k] for k in ids}
        else:
            ids = [k for k, v in self.trail_new.items() if v]
            if not ids:
                return
            ent = {}
            for k in ids:
                e = self.trail_new[k]
                if len(e) > TRAIL_FRAME_MAX:  # a frame that covered many turns: its latest points, after a break
                    e = [None] + e[-TRAIL_FRAME_MAX:]
                ent[k] = e
        rows = [q for k in ids for q in ent[k]]
        n = len(rows)
        pts = np.full((n, 3), np.nan, np.float32)
        vel = np.full((n, 3), np.nan, np.float32)
        tt = np.full(n, np.nan)
        for i, q in enumerate(rows):
            if q is not None:
                tt[i], pts[i], vel[i] = q
        rgb = [self._rgb_end.get(k, c) for k, c in zip(ids, self._trail_rgb(ids))]
        self.sim.emit({"type": "trail", "t": self.sim.t, "ids": ids, "counts": [len(ent[k]) for k in ids],
                       "rgb": rgb, "hermite": True, **({"reset": True} if full else {})},
                      {"pts": pts, "vel": vel, "tt": tt})
        if not full:
            for k in ids:
                kept = self.trail_kept.setdefault(k, [])
                kept.extend(ent[k])
                del kept[:-TRAIL_KEEP]
                self.trail_new[k] = []


def _p(*a, **k):
    return Param(*a, **k)


def _otype(*args, handles=None, **kw) -> ObjectType:
    """A palette type with its handles (the LB1 framework: the parameters a drag or a throw in the scene changes,
    checked against the type's schema); an older framework without handles takes the type as before."""
    if handles is None:
        return ObjectType(*args, **kw)
    try:
        return ObjectType(*args, handles=handles, **kw)
    except TypeError:
        ot = ObjectType(*args, **kw)
        ot.handles = handles
        return ot


class Clock:
    """The world's seconds and a mode's geometric time (G = c = M = 1: one unit = T seconds). A change of the mass
    that sets the units (the hole's, the binary's: plan P16.1) changes T at the current moment: the geometric time goes
    on from where it is (s0, g0), so nothing in the solver jumps; seconds before and after keep their meaning."""

    def __init__(self, T: float):
        self.T, self.s0, self.g0 = float(T), 0.0, 0.0

    def geo(self, s: float) -> float:
        return self.g0 + (s - self.s0) / self.T

    def sec(self, g: float) -> float:
        return self.s0 + (g - self.g0) * self.T

    def rescale(self, s_now: float, T: float):
        self.g0, self.s0, self.T = self.geo(s_now), float(s_now), float(T)

    def state(self):
        return {"T": self.T, "s0": self.s0, "g0": self.g0}


SCHEMA = Schema([
    _p("laws", "Законы мира", "select", "newton", group="Законы", standard=None,
       options=[("newton", "Ньютон: N тел"), ("pn", "ОТО: двойная (постньютоновская, с излучением волн)"),
                ("kerr", "ОТО: тела и свет у чёрной дыры Керра–Ньюмена")],
       help="Какими законами считается мир; другие законы — новый мир"),
    _p("m_total", "Полная масса новой двойной, M☉", "float", 20.0, group="Двойная (ОТО)", min=0.1, max=1e10,
       log=True, show_if={"laws": ["pn"]},
       help="Масса двойной, добавленной без своей массы; масса — свойство самой двойной: меняется в её инспекторе в "
            "текущий момент (длины в G m/c², время в G m/c³)"),
    _p("m_hole", "Масса чёрной дыры в начале, M☉", "float", 10.0, group="Чёрная дыра", min=0.1, max=1e10, log=True,
       show_if={"laws": ["kerr"]},
       help="Дыра — объект сцены: её масса, спин и заряд меняются в её инспекторе в текущий момент (длины в G M/c², "
            "время в G M/c³)"),
    _p("spin", "Спин a/M в начале", "float", 0.9, group="Чёрная дыра", min=0.0, max=0.998, show_if={"laws": ["kerr"]}),
    _p("charge", "Заряд Q/M в начале (геометрические единицы)", "float", 0.0, group="Чёрная дыра", min=0.0, max=0.99,
       show_if={"laws": ["kerr"]}, help="a² + Q² < 1: иначе нет горизонта"),
    _p("collisions", "Столкновения тел", "select", "merge", group="Законы", show_if={"laws": ["newton"]}, live=True,
       options=[("merge", "сливаются (импульс и масса сохраняются)"), ("pass", "проходят друг сквозь друга")],
       help="Меняется на ходу, в текущий момент: тела уже в касании при «проходят» летят дальше, при «сливаются» — "
            "сливаются сразу"),
    scene_param(),
], presets={
    "sun_earth": {"label": "Солнце и Земля (круговая орбита 1 а.е.)", "params": {"laws": "newton", "scene": {
        "format": "lfscene", "version": 1, "objects": [
            {"type": "star", "label": "Солнце", "values": {"mass": 1.0, "radius": 1.0}},
            {"type": "planet", "label": "Земля", "values": {"mass": 1.0, "radius": 1.0, "x": 1.0}},
            {"type": "field", "label": "Датчик у Земли", "values": {"x": 1.02}}]}}},
    "inner": {"label": "Солнце, Меркурий, Венера, Земля, Марс, Юпитер (круговые орбиты)", "params": {
        "laws": "newton", "scene": {"format": "lfscene", "version": 1, "objects": [
            {"type": "star", "label": "Солнце", "values": {"mass": 1.0}},
            {"type": "planet", "label": "Меркурий", "values": {"mass": 0.0553, "radius": 0.383, "x": 0.387,
                                                               "color": "#ced4da"}},
            {"type": "planet", "label": "Венера", "values": {"mass": 0.815, "radius": 0.949, "x": 0.723,
                                                             "color": "#ffd43b"}},
            {"type": "planet", "label": "Земля", "values": {"mass": 1.0, "radius": 1.0, "x": 1.0}},
            {"type": "planet", "label": "Марс", "values": {"mass": 0.107, "radius": 0.532, "x": 1.524,
                                                           "color": "#ff6b6b"}},
            {"type": "planet", "label": "Юпитер", "values": {"mass": 317.8, "radius": 11.21, "x": 5.203,
                                                             "color": "#ff922b"}}]}}},
    "pythagorean": {"label": "Пифагорова задача трёх тел (Бурау): массы 3, 4, 5 в покое — тесные сближения",
                    "params": {"laws": "newton", "collisions": "pass", "scene": {
                        "format": "lfscene", "version": 1, "objects": [
                            {"type": "star", "label": "m = 3", "values": {"mass": 3.0, "radius": 0.001, "x": 1.0,
                                                                           "y": 3.0, "vmode": "manual",
                                                                           "color": "#ff6b6b"}},
                            {"type": "star", "label": "m = 4", "values": {"mass": 4.0, "radius": 0.001, "x": -2.0,
                                                                           "y": -1.0, "vmode": "manual",
                                                                           "color": "#8ce99a"}},
                            {"type": "star", "label": "m = 5", "values": {"mass": 5.0, "radius": 0.001, "x": 1.0,
                                                                           "y": -1.0, "vmode": "manual",
                                                                           "color": "#74c0fc"}}]}}},
    "hole_stars": {"label": "Ньютоновская чёрная дыра 1000 M☉ и звёзды: орбиты и захват", "params": {
        "laws": "newton", "scene": {"format": "lfscene", "version": 1, "objects": [
            {"type": "hole", "label": "Чёрная дыра", "values": {"mass": 1000.0}},
            {"type": "star", "label": "Звезда 1", "values": {"mass": 1.0, "x": 2.0, "vmode": "circular"}},
            {"type": "star", "label": "Звезда 2", "values": {"mass": 2.0, "x": -3.5, "vmode": "circular",
                                                              "color": "#74c0fc"}},
            {"type": "star", "label": "Падающая звезда", "values": {"mass": 1.0, "x": 0.0, "y": 4.0,
                                                                     "vmode": "manual", "vx": 20.0,
                                                                     "color": "#ff6b6b"}}]}}},
    "kerr_orbits": {"label": "У чёрной дыры (a = 0,9): тела на орбитах, лучи света, часы наблюдателей", "params": {
        "laws": "kerr", "m_hole": 10.0, "spin": 0.9, "charge": 0.0, "scene": {"format": "lfscene", "version": 1,
                                                                              "objects": [
            {"type": "body", "label": "На ISCO-близкой орбите", "values": {"r": 3.0}},
            {"type": "body", "label": "Наклонная орбита", "values": {"r": 8.0, "theta": 70.0, "vmode": "zamo",
                                                                     "v_phi": 0.42, "v_theta": 0.08,
                                                                     "color": "#74c0fc"}},
            {"type": "body", "label": "Падает", "values": {"r": 12.0, "phi": 200.0, "vmode": "zamo", "v_phi": 0.1,
                                                           "color": "#ff6b6b"}},
            {"type": "light", "label": "Луч мимо дыры", "values": {"r": 20.0, "psi": 14.0}},
            {"type": "light", "label": "Луч у фотонной орбиты", "values": {"r": 20.0, "phi": 90.0, "psi": 8.5}},
            {"type": "observer", "label": "Неподвижный на r = 4", "values": {"kind": "static", "r": 4.0}},
            {"type": "observer", "label": "На круговой орбите r = 6", "values": {"kind": "circular", "r": 6.0,
                                                                                 "phi": 120.0}}]}}},
    "pn_inspiral": {"label": "ОТО: двойная 10 + 10 M☉ с расстояния 20 G m/c² и детектор волн (сближение)",
                    "params": {"laws": "pn", "m_total": 20.0, "scene": {"format": "lfscene", "version": 1, "objects": [
                        {"type": "binary", "values": {"q": 1.0, "r0": 20.0}},
                        {"type": "detector", "values": {"distance": 400.0, "iota": 30.0}}]}}},
    "pn_eccentric": {"label": "ОТО: эксцентрическая двойная 30 + 10 M☉ (e = 0,5), прецессия перицентра",
                     "params": {"laws": "pn", "m_total": 40.0, "scene": {"format": "lfscene", "version": 1, "objects": [
                         {"type": "binary", "values": {"q": 0.3333333333333333, "r0": 25.0, "start": "ellipse",
                                                       "e": 0.5, "m_total": 40.0}},
                         {"type": "detector", "values": {"distance": 400.0, "iota": 0.0}}]}}},
})


# --- the scene a world starts from: a preset, a file, or the previous world's (carried over: P16.1) ---------------
LAWS_RU = {"newton": "Ньютон: N тел", "pn": "ОТО: двойная", "kerr": "ОТО: у чёрной дыры Керра–Ньюмена"}


def _carry(objs, src, dst, params):
    """The objects of a world with laws ``src`` that make sense in a world with laws ``dst`` (translated), and the
    reasons for the others. Newton -> Kerr: the most massive Newtonian hole becomes the Kerr-Newman hole (its mass; spin
    and charge of the new world); Kerr -> Newton: the hole becomes a Newtonian hole at the origin (its mass); the PN
    binary -> Newton: its two bodies as Newtonian holes (masses m1, m2; positions and velocities of the Newtonian
    centre of mass); Newton -> PN: the two most massive bodies as the binary, only where their separation lies within
    the binary's range (8 ... 2000 G m/c^2). Everything else is refused with the reason: the scales do not meet (an au
    is ~10^7 G M/c^2 of a 10 M_sun hole), light, clocks and wave detectors have no counterpart."""
    keep, why = [], []

    def no(o, text):
        why.append(f"«{o.get('label') or o.get('type')}» — {text}")
    if src == "newton" and dst == "kerr":
        holes = sorted([o for o in objs if o.get("type") == "hole"], key=lambda o: -float((o.get("values") or {})
                                                                                          .get("mass", 0.0)))
        if holes:
            h = holes[0]
            keep.append({"type": "kn_hole", "label": h.get("label") or "Чёрная дыра",
                         "values": {"mass": float((h.get("state") or {}).get("m", (h.get("values") or {}).get("mass",
                                                                                                               10.0)))}})
        for o in objs:
            if holes and o is holes[0]:
                continue
            no(o, "у дыры Керра–Ньюмена тела — пробные, в единицах G M/c² (1 а.е. ≈ 10⁷ G M/c² у дыры 10 M☉): "
                  "ньютоновские тела и датчики туда не переносятся; добавьте пробные тела у дыры")
    elif src == "kerr" and dst == "newton":
        for o in objs:
            if o.get("type") == "kn_hole":
                mh = float((o.get("values") or {}).get("mass", 10.0))
                keep.append({"type": "hole", "label": o.get("label") or "Чёрная дыра",
                             "values": {"mass": mh, "x": 0.0, "y": 0.0, "z": 0.0, "vmode": "manual", "vx": 0.0,
                                        "vy": 0.0, "vz": 0.0},
                             "state": {"x": [0.0, 0.0, 0.0], "v": [0.0, 0.0, 0.0], "m": mh}})
            else:
                no(o, "пробные тела, свет и часы у дыры — в единицах G M/c² (километры): в мире Ньютона (а.е.) они "
                      "были бы в самой дыре; свет и часы ОТО там не определены")
    elif src == "pn" and dst == "newton":
        for o in objs:
            st, v = o.get("state") or {}, o.get("values") or {}
            if o.get("type") == "binary" and st.get("x") is not None:
                q, m = float(v.get("q", 1.0)), float(v.get("m_total", params.get("m_total", 20.0)))
                m1, m2 = m / (1.0 + q), m * q / (1.0 + q)
                L = m * K.GM_SUN / K.C ** 2 / K.AU            # au per G m/c^2
                x, w = np.asarray(st["x"], float), np.asarray(st["v"], float) * K.C / 1e3  # c -> km/s
                for lab, mm, f in ((" — тело 1", m1, m2 / m), (" — тело 2", m2, -m1 / m)):
                    p, u = f * x * L, f * w
                    keep.append({"type": "hole", "label": (o.get("label") or "Двойная") + lab,
                                 "values": {"mass": mm, "x": float(p[0]), "y": float(p[1]), "z": float(p[2]),
                                            "vmode": "manual", "vx": float(u[0]), "vy": float(u[1]), "vz": float(u[2])},
                                 # the state as it is (a place() of the framework's carry-over must not move it)
                                 "state": {"x": p.tolist(), "v": (u * KMS).tolist(), "m": mm}})
            else:
                no(o, "детектор волн — в мире Ньютона гравитационных волн нет" if o.get("type") == "detector"
                   else "нет состояния двойной")
    elif src == "newton" and dst == "pn":
        mass = [o for o in objs if o.get("type") in ("star", "planet", "hole") and o.get("state")]
        mass.sort(key=lambda o: -float(o["state"].get("m", 0.0)))
        used = mass[:2] if len(mass) >= 2 else []
        if used:
            a, b = used[0]["state"], used[1]["state"]
            m = float(a["m"]) + float(b["m"])
            Lm = m * K.GM_SUN / K.C ** 2 / K.AU  # au per G m/c^2
            x = (np.asarray(a["x"], float) - np.asarray(b["x"], float)) / Lm
            vv = (np.asarray(a["v"], float) - np.asarray(b["v"], float)) * K.AU / YR / K.C
            r, q = float(np.linalg.norm(x)), float(b["m"]) / float(a["m"])
            pair = f"«{used[0].get('label')}» и «{used[1].get('label')}»"
            if 8.0 <= r <= 2000.0 and q >= 0.05:
                keep.append({"type": "binary", "label": pair, "values": {"q": q, "r0": r, "start": "ellipse",
                                                                         "m_total": m},
                             "state": {"x": x.tolist(), "v": vv.tolist(), "status": "running"}})
            else:
                why.append(f"{pair} — расстояние {r:.3g} G m/c² вне диапазона двойной ОТО (8 … 2000 G m/c²)"
                           + (f", отношение масс {q:.3g} < 0,05" if q < 0.05 else ""))
        for o in objs:
            if not any(o is u for u in used):
                no(o, "в мире двойной ОТО — одна двойная и детекторы волн")
    else:
        for o in objs:
            no(o, f"в мире законов «{LAWS_RU.get(dst, dst)}» такого объекта нет")
    return keep, why


def prepare_scene(scene, params):
    """The scene a world is built from, prepared for its laws: carried over from a world of other laws, its objects
    translated where the physics allows (``_carry``; the rest listed); the hole's world always has its hole object: the
    one of the scene (a file's hole keeps its mass, spin and charge; a carried-over one of the same laws takes the new
    world's), else one of the world's parameters — the last object (the others keep their ids), its values set on the
    world before any body is placed (``KerrMode.init_hole``). Returns (scene, reasons, the hole's values or None)."""
    laws = params["laws"]
    sc = scene if isinstance(scene, dict) else None
    objs = list((sc or {}).get("objects") or [])
    carry = bool((sc or {}).get("carry"))
    src = ((sc or {}).get("laws") or {}).get("laws") if carry else None
    notes = []
    if src and src != laws:
        objs, notes = _carry(objs, src, laws, params)
    if laws == "kerr":
        holes = [o for o in objs if isinstance(o, dict) and o.get("type") == "kn_hole"]
        rest = [o for o in objs if not (isinstance(o, dict) and o.get("type") == "kn_hole")]
        world = {"mass": float(params["m_hole"]), "spin": float(params["spin"]), "charge": float(params["charge"])}
        hole = dict(holes[0]) if holes else {"type": "kn_hole", "label": "Чёрная дыра"}
        hv = dict(hole.get("values") or {})
        # a carried-over hole of the same laws takes the new world's mass, spin and charge (the dialog's); a file's keeps
        # its own; one made from another world's hole keeps its mass and takes the world's spin and charge
        hv = {**world, **hv} if holes and not (carry and src == laws) else {**hv, **world}
        if carry and src != laws:
            hv.update({"spin": world["spin"], "charge": world["charge"]})
        hole["values"] = hv
        objs = rest + [hole]
    if sc is None and not objs:
        return None, notes, None
    out = dict(sc or {"format": "lfscene", "version": 1})
    out["objects"] = objs
    return out, notes, (objs[-1]["values"] if laws == "kerr" else None)


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p01_gravity"
    default_speed = 3.15576e7  # one year of the world per second (the Newtonian presets)
    speed_range = (1e-9, 1e12)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        laws = params["laws"]
        mode = {"newton": NewtonMode, "pn": PNMode, "kerr": KerrMode}.get(laws)
        if mode is None:
            raise ValueError(f"законы «{laws}» ещё не подключены")
        self.mode = mode(self)
        self.PALETTE = self.mode.palette()
        self.start_scene()
        # after the scene: a hole or a binary of its own mass sets the units, and with them the speeds
        self.default_speed = self.mode.default_speed
        self.speed_range = self.mode.speed_range

    # --- the framework's hooks, by mode ---------------------------------------------------------------------------
    def on_add(self, obj, state):
        self.mode.on_add(obj, state)

    def on_remove(self, obj):
        self.mode.on_remove(obj)

    def on_set(self, obj, old):
        self.mode.on_set(obj, old)

    def object_state(self, obj):
        return self.mode.object_state(obj)

    def place(self, kind, values):
        """A palette object's values before it is added (``lfviz.playground``): a free spot (review UX-ui U4)."""
        return self.mode.place(kind, dict(values))

    def palette_state(self):
        return self.mode.palette_state() if hasattr(self.mode, "palette_state") else {}

    def can_remove(self, obj):
        return self.mode.can_remove(obj) if hasattr(self.mode, "can_remove") else None

    def measurables(self):
        return self.mode.measurables()

    def measure(self):
        return self.mode.measure_now()[0]

    def scene(self, args):
        """The framework's scene command; «Очистить сцену» in the hole's world clears everything but the hole (the
        world is the hole's: removing it would be a new world)."""
        if args.get("op") == "clear" and isinstance(self.mode, KerrMode):
            rest = [o for o in self.objects.values() if o["type"] != "kn_hole"]
            for o in rest:
                self.on_remove(o)
                del self.objects[o["id"]]
            self.rev += 1
            self.emit_scene()
            return "сцена очищена (дыра осталась: мир считается вокруг неё)"
        return super().scene(args)

    def start_scene(self):
        """The initial scene (a preset's, a file's, or one carried over from the previous world: P16.1) prepared for
        these laws (``prepare_scene``: the hole's world gets its hole first; objects of other laws translated where the
        physics allows, the rest listed with the reason), then built by the framework."""
        sc, notes, hole = prepare_scene(self.params.get("scene"), self.params)
        self._carry_notes = notes
        if hole is not None:
            self.mode.init_hole(float(hole["mass"]), float(hole["spin"]), float(hole["charge"]))
        saved = self.params
        self.params = {**saved, "scene": sc}
        try:
            super().start_scene()
        finally:
            self.params = saved

    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        """A law changed at the current moment, the world kept (review UX-ui U12): the collisions of Newtonian bodies
        (``nbody.NBody.set_collisions``)."""
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise ValueError("; ".join(str(e) for e in errors))
        changed = [k for k in values if new.get(k) != self.params.get(k)]
        if not changed:
            return "без изменений"
        if "collisions" in changed:
            if not isinstance(self.mode, NewtonMode):
                raise Refusal("столкновения задаются только у ньютоновских тел", hint="законы «Ньютон: N тел»")
            self.mode.set_collisions(new["collisions"])
        old = self.params
        self.params = new
        p = SCHEMA.by_id
        names = {k: {o[0]: o[1] for o in p[k].options} for k in changed}
        return "; ".join(f"{p[k].label}: {names[k].get(old[k], old[k])} → {names[k].get(new[k], new[k])}" for k in changed)

    def rekey(self):
        self.mode.emit_trails(full=True)

    def advance(self, t_target):
        if t_target > self.t:
            self.mode.advance(t_target)
        self.t = t_target

    def max_step(self):
        return self.mode.max_step()

    def frame(self):
        meta, blobs = self.mode.frame()
        if self.check_due():
            self.mode.checks()
        self.mode.trail_tick()
        return meta, blobs

    def header(self):
        h = self.mode.header()
        h.update({"actions": [], "playground": self.playground_header(),
                  "modifications": SCHEMA.modifications(self.params)})
        return h, {}

    def after_header(self):
        super().after_header()
        self.mode.after_header()
        if getattr(self, "_carry_notes", None):
            self.emit({"type": "notice", "t": self.t, "text": "Перенос сцены в мир других законов: не перенесены — "
                       + "; ".join(self._carry_notes) + " (что имеет смысл, переведено: см. сцену)"})

    def engine_modules(self):
        return self.mode.engine_modules()


# --- Newtonian N bodies ------------------------------------------------------------------------------------------
YR = K.YEAR_JULIAN
# G in au^3 / (M_sun yr^2): 4 pi^2 (1 - 3.8e-5), the square of the Julian year over Gauss's year (review B6-G15)
G_AU = K.GM_SUN * YR ** 2 / K.AU ** 3
KMS = 1e3 * YR / K.AU  # km/s in au/yr
M_EARTH_SUN = K.GM_EARTH / K.GM_SUN  # Earth's mass in solar masses (IAU 2015 B3 nominal (GM)_E = 3.986004e14)
RS_AU = 2.0 * K.GM_SUN / K.C ** 2 / K.AU  # Schwarzschild radius of one solar mass, au
BOX_GROWTH = 64.0  # the Newtonian frame grows with the bodies up to this factor of the scene's size at its last change
CLEAR = 3.0  # a new body is put at least this many sums of radii (surfaces, capture radii) away from the others
HOLE_RGB = [0.80, 0.76, 1.0]  # a Newtonian hole's sphere: light, with its name next to it (review UX-ui U18)


def _years(sec):
    """A duration in years, the owner's way («0,05 года», «1 год», «12 лет»)."""
    t = f"{sec / YR:.3g}"
    v = float(t)
    if v.is_integer():
        n = int(abs(v))
        word = "год" if n % 10 == 1 and n % 100 != 11 else "года" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "лет"
    else:
        word = "года"
    return t.replace(".", ",") + " " + word


def _num(x, digits=4):
    return f"{x:.{digits}g}".replace(".", ",")


def _fmt(v):
    return "; ".join(_num(c) for c in v)


def _pos(label="Положение"):
    # bounded (review B6-F6: a finite value that overflows in the solver broke every frame): 10^6 au
    return [_p(c, f"{label}: {c}, а.е.", "float", 0.0, min=-1e6, max=1e6) for c in "xyz"]


def _vel(default_mode="circular"):
    return [_p("vmode", "Скорость", "select", default_mode,
               options=[("circular", "круговая орбита вокруг центра масс остальных (остальные получают отдачу)"),
                        ("manual", "задать vx, vy, vz")],
               help="Круговая — в момент добавления (или смены скорости): относительная орбита тела и остальных "
                    "как двух тел круговая для любой массы тела, остальные получают общую отдачу, центр масс системы "
                    "не сдвигается; плоскость орбиты — ближайшая к xy (против часовой стрелки, если смотреть с +z)"),
            *[_p(c, f"{c}, км/с", "float", 0.0, min=-2.9979e5, max=2.9979e5, show_if={"vmode": ["manual"]},
                 help="Ньютоновская механика: скорость меньше скорости света (и много меньше — для точности)")
              for c in ("vx", "vy", "vz")]]


# a throw in the scene (P16.2) sends the velocity in the scene's units per world second (а.е./с); hidden: the body's own
# velocity is shown in km/s (vmode «задать», vx, vy, vz), set from the throw
THROW = [_p(c, f"Бросок: {c[1:]}, а.е./с", "float", 0.0, min=-1.0, max=1.0, hidden=True) for c in ("tvx", "tvy", "tvz")]
REF = _p("ref", "Расстояние в приборах — до", "select", "dominant", options=[
    ("dominant", "самого массивного другого тела"), ("com", "центра масс системы"), ("origin", "начала координат")],
    help="Для приборов (P16.3): расстояние этого тела до выбранного; элементы орбиты (a, e, период) — всегда "
         "относительно самого массивного другого тела (две массы как задача двух тел)")
COLOR = _p("color", "Цвет", "select", "#ffd43b", options=[("#ffd43b", "жёлтый"), ("#ff922b", "оранжевый"),
                                                         ("#ff6b6b", "красный"), ("#74c0fc", "голубой"),
                                                         ("#8ce99a", "зелёный"), ("#e9ecef", "белый"),
                                                         ("#b197fc", "фиолетовый"), ("#ced4da", "серый")])
STAR = Schema([_p("mass", "Масса, M☉", "float", 1.0, min=1e-4, max=1e3, log=True),
               _p("radius", "Радиус, R☉", "float", 1.0, min=1e-3, max=2000.0, log=True),
               *_pos(), *_vel(), COLOR, REF, *THROW])
PLANET = Schema([_p("mass", "Масса, M⊕", "float", 1.0, min=1e-6, max=1e4, log=True),
                 _p("radius", "Радиус, R⊕", "float", 1.0, min=1e-3, max=30.0, log=True),
                 *[q if q.id != "x" else _p("x", "Положение: x, а.е.", "float", 1.0, min=-1e6, max=1e6) for q in _pos()], *_vel(),
                 _p("color", "Цвет", "select", "#74c0fc", options=COLOR.options), REF, *THROW])
HOLE = Schema([_p("mass", "Масса, M☉", "float", 10.0, min=1e-2, max=1e10, log=True), *_pos(), *_vel(), REF, *THROW])
TEST = Schema([*[q if q.id != "x" else _p("x", "Положение: x, а.е.", "float", 2.0, min=-1e6, max=1e6) for q in _pos()], *_vel(),
               _p("color", "Цвет", "select", "#e9ecef", options=COLOR.options), REF, *THROW])
# the largest throw a Newtonian body takes from the player: 0.05 c in au per second (the player clamps to it and says so);
# the world itself accepts up to 0.1 c (Newtonian mechanics then errs by v^2/c^2 <= 1 %: typed values may lie there) and
# refuses from 0.1 c with the reason; the hidden parameters' range is wider only so that this refusal is the one shown
# (review LB1-physics P15)
BODY_HANDLES = {"position": ["x", "y", "z"], "velocity": ["tvx", "tvy", "tvz"], "velocity_max": 0.05 * 299792458.0 / 1.495978707e11}
FIELD = Schema([*_pos("Точка")])


def _rgb(hexcol):
    h = hexcol.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class NewtonMode(Trails):
    default_speed = YR  # a year per second
    speed_range = (1.0, 1e5 * YR)
    COMPANION_EVERY = 1  # check intervals between two companion runs (each re-integrates its interval with eta/2)
    COMPANION_EVERY_LARGE = 3  # the same beyond COMPANION_N bodies (the companion costs twice the scene's own steps)
    COMPANION_N = 50

    def __init__(self, sim):
        self.sim = sim
        self.nb = NB.NBody(G_AU, integrator="hermite", eta=0.02, collisions=sim.params["collisions"], t=0.0)
        self._trails_init()
        self.n_checks = 0
        self.ref = None  # conserved quantities at the last change of the scene: {"E", "P", "L", "err"}
        self.mark = None  # the state at the start of the companion's interval
        self.box_h = 1.5
        self.box_cap = math.inf  # BOX_GROWTH times the frame at the last change of the scene by hand
        self._placed_note = None  # (type, x, y, z, text) of a body ``place`` moved, announced when it is added

    def palette(self):
        # handles (P16.2): a drag moves a body (its velocity kept), a throw sets its velocity (the scene's а.е./с)
        return {"star": _otype("star", "Звезда", "body", STAR, color="#ffd43b", handles=BODY_HANDLES,
                               help="Масса и радиус в солнечных; поверхность звезды — граница столкновения; по умолчанию — на "
                                    "круговой орбите вокруг центра масс остальных (одна — в покое)"),
                "planet": _otype("planet", "Планета", "body", PLANET, color="#74c0fc", handles=BODY_HANDLES,
                                 help="Масса и радиус в земных; по умолчанию — на круговой орбите"),
                "hole": _otype("hole", "Чёрная дыра (ньютоновская масса)", "body", HOLE, color="#343a40",
                               handles=BODY_HANDLES,
                               help="Точечная масса с радиусом Шварцшильда как радиусом захвата: приближение "
                                    "Ньютона, не ОТО (для ОТО — законы «тела и свет у чёрной дыры»); что её "
                                    "коснётся, она поглощает, и её радиус — радиус Шварцшильда новой массы; по "
                                    "умолчанию — на круговой орбите вокруг центра масс остальных"),
                "test": _otype("test", "Пробное тело (без массы)", "particle", TEST, color="#e9ecef",
                               handles=BODY_HANDLES, help="Чувствует притяжение, само не притягивает"),
                "field": _otype("field", "Датчик поля и приливов", "probe", FIELD, limit=8, color="#f06595",
                                handles={"position": ["x", "y", "z"]},
                                help="Ускорение свободного падения и приливное растяжение в точке")}

    def t_yr(self):
        return self.sim.t / YR

    def _sync(self):
        """The bodies' clock to the world's (an object is added or changed at the world's current moment)."""
        if self.nb.t < self.t_yr():
            self._run(self.t_yr())

    def _run(self, t_yr):
        """Advance the bodies to t_yr: the points of their orbits to the trails (review UX-ui U2), then the events."""
        S = NB.Samples(turn=CAND_TURN, dspeed=CAND_DSPEED)
        ev = self.nb.advance(t_yr, samples=S)
        prev = None
        for t, keys, X, V, restart in S.points:
            if restart and prev is not None:  # a merger: both keep the contact; the one absorbed ends there
                pt, pk, pX, pV = prev
                self.trail_feed(pt * YR, pk, pX, pV / YR, force=True)
                for k in set(pk) - set(keys):
                    self.trail_end(k)
                for k in restart:
                    self.trail_break(k)
            self.trail_feed(t * YR, keys, X, V / YR)
            prev = (t, keys, X, V)
        self._events(ev)

    def _shown(self):
        """(keys, positions, velocities per world second) at the current moment, for the trails' breaks."""
        nb = self.nb
        if not nb.n:
            return (), np.zeros((0, 3)), np.zeros((0, 3))
        return tuple(nb.keys), nb.positions(), nb.velocities() / YR

    def _start_velocity(self, obj, x, m, key=None):
        """The velocity of a body from its velocity mode at the current moment, and the uniform boost of all the other
        bodies that goes with it (None: none). "circular" (review B6-G6): the two-body circular orbit of the body (mass
        m, at x) and the others (mass M at their centre of mass c, moving with cv): relative speed sqrt(G (M + m) / d),
        d = |x - c| in 3-D, along e = z x (x - c) / |...| (the orbit's plane through x - c closest to xy, counter-clockwise
        seen from +z); the body gets V + M/(M + m) v_rel e and the others a common boost that makes their centre of mass
        move with V - m/(M + m) v_rel e, V the whole system's centre-of-mass velocity before (cv for a new body): the
        relative orbit is circular for any m and the system's centre of mass keeps its velocity."""
        v = obj["values"]
        if v.get("vmode", "manual") == "manual":
            return np.array([v["vx"], v["vy"], v["vz"]], float) * KMS, None
        keys = self.nb.keys
        idx = [i for i, k in enumerate(keys) if k != key]
        mo = self.nb.masses()[idx]
        M = float(mo.sum()) if idx else 0.0
        if M <= 0.0:
            return np.zeros(3), None
        X, V = self.nb.positions(), self.nb.velocities()
        c = (mo[:, None] * X[idx]).sum(0) / M
        cv = (mo[:, None] * V[idx]).sum(0) / M
        d = np.asarray(x, float) - c
        dist = float(np.linalg.norm(d))
        e = np.cross([0.0, 0.0, 1.0], d)
        en = float(np.linalg.norm(e))
        if not (dist > 0.0 and en > 1e-9 * dist):
            raise ValueError("круговая орбита: тело на оси z, проходящей через центр масс остальных тел, — плоскость "
                             "орбиты не определена; сдвиньте его по x или y")
        e /= en
        vrel = math.sqrt(G_AU * (M + m) / dist)
        Vs = cv if key is None else (M * cv + m * V[keys.index(key)]) / (M + m)
        vb = Vs + M / (M + m) * vrel * e
        boost = (Vs - m / (M + m) * vrel * e) - cv
        return vb, (boost if m > 0.0 else None)

    def _engine_edit(self, fn, *args, **kw):
        """An edit of the engine; a body exactly on another (two point masses at one point) is refused in words."""
        try:
            return fn(*args, **kw)
        except ValueError as e:
            if "same point" in str(e):
                raise ValueError("тело оказалось бы точно в той же точке, что и другое: две точечные массы в одной "
                                 "точке (бесконечная сила) — так нельзя (копия массивного тела «в текущий момент» "
                                 "ложится на оригинал; добавьте тело из палитры в другом месте)") from None
            raise

    def _contact_radius(self, obj, m, R):
        """The radius at which another body touches the new one: its surface, or a hole's capture radius."""
        return m * RS_AU if obj["type"] == "hole" else (R if obj["type"] in ("star", "planet") else 0.0)

    def _blocker(self, x, Rc, vmode=None, skip=None):
        """The first body the point x is too close to for a new body of contact radius Rc (CLEAR times the sum of the
        radii, or exactly on it), or the reason a circular start is undefined there; None when the point is free."""
        nb = self.nb
        if not nb.n:
            return None
        X, Rb, keys = nb.positions(), nb.radii(), nb.keys
        for i, k in enumerate(keys):
            if k == skip:
                continue
            d = float(np.linalg.norm(X[i] - x))
            if d == 0.0 or d <= CLEAR * (Rc + float(Rb[i])):
                lab = self.sim.objects[k]["label"] if k in self.sim.objects else str(k)
                return f"в точке ({_fmt(x)}) а.е. уже «{lab}»" if d == 0.0 else \
                    f"точка ({_fmt(x)}) а.е. слишком близко к «{lab}» (касание сразу)"
        if vmode == "circular":
            idx = [i for i, k in enumerate(keys) if k != skip]
            mo = nb.masses()[idx]
            if mo.sum() > 0:
                c = (mo[:, None] * X[idx]).sum(0) / mo.sum()
                dd = np.asarray(x, float) - c
                if not float(np.linalg.norm(np.cross([0.0, 0.0, 1.0], dd))) > 1e-9 * max(float(np.linalg.norm(dd)), 1e-300):
                    return f"точка ({_fmt(x)}) а.е. на оси z через центр масс остальных: плоскость круговой орбиты не определена"
        return None

    def free_spot(self, x, Rc, vmode=None, skip=None):
        """(point, why it was moved or None): x itself when free, else the first free point along +x from it, in steps
        of an eighth of the scene's half-size (and never less than twice the clearance of the nearest body), up to 64
        steps; (None, why) when there is none."""
        x = np.asarray(x, float)
        why = self._blocker(x, Rc, vmode, skip)
        if why is None:
            return x, None
        Rmax = float(np.max(self.nb.radii())) if self.nb.n else 0.0
        step = max(self.box_h / 8.0, 2.0 * CLEAR * (Rc + Rmax))
        for q in range(1, 65):
            y = x + np.array([q * step, 0.0, 0.0])
            if self._blocker(y, Rc, vmode, skip) is None:
                return y, why
        return None, why

    def place(self, kind, values):
        """The palette's new body at a free spot (review UX-ui U4: a second star at the default (0, 0, 0) was refused, a
        star in the Sun merged at once, a hole swallowed the Sun): the clicked point or the form's x, y, z when free,
        else the first free point along +x; the move is announced when the body is added."""
        if kind == "field":
            pos = values.pop("position", None)
            if isinstance(pos, (list, tuple)) and len(pos) >= 3:
                values.update(x=float(pos[0]), y=float(pos[1]), z=float(pos[2]))
            return values
        ot = self.sim.PALETTE[kind]
        pos = values.pop("position", None)
        full, errors = ot.schema.resolve(None, values)
        if errors:
            return values  # the framework reports the errors with the labels
        if isinstance(pos, (list, tuple)) and len(pos) >= 3:
            full.update(x=float(pos[0]), y=float(pos[1]), z=float(pos[2]))
        self._sync()
        m, R = self._mass_radius({"type": kind, "values": full})
        x0 = np.array([full["x"], full["y"], full["z"]], float)
        x, why = self.free_spot(x0, self._contact_radius({"type": kind}, m, R), full.get("vmode"))
        if x is None:
            raise Refusal(f"рядом с ({_fmt(x0)}) а.е. нет свободного места: {why}",
                          hint="задайте положение x, y, z дальше от других тел")
        full.update(x=float(x[0]), y=float(x[1]), z=float(x[2]))
        self._placed_note = None if why is None else (
            kind, full["x"], full["y"], full["z"],
            f"{why} — поставлено в ближайшее свободное место ({_fmt(x)}) а.е.")
        return full

    def _free_check(self, obj, x, m, R, rpm):
        """A new body (a preset's, a file's, after ``place``) must not start inside another: refused with the fix."""
        why = self._blocker(x, self._contact_radius(obj, m, R), obj["values"].get("vmode"))
        if why is not None and not self.sim._loading:
            y, _ = self.free_spot(x, self._contact_radius(obj, m, R), obj["values"].get("vmode"))
            raise Refusal(f"«{obj['label']}» не поставлено: {why}",
                          hint=(f"задайте положение, например ({_fmt(y)}) а.е." if y is not None
                                else "задайте положение дальше от других тел"))

    def _mass_radius(self, obj):
        v = obj["values"]
        if obj["type"] == "star":
            return float(v["mass"]), float(v["radius"]) * K.R_SUN / K.AU
        if obj["type"] == "planet":
            return float(v["mass"]) * M_EARTH_SUN, float(v["radius"]) * K.R_EARTH / K.AU
        if obj["type"] == "hole":
            return float(v["mass"]), float(v["mass"]) * RS_AU
        return 0.0, 0.0

    def on_add(self, obj, state):
        if obj["type"] == "field":
            return
        self._sync()
        v = obj["values"]
        m, R = self._mass_radius(obj)
        rpm = RS_AU if obj["type"] == "hole" else 0.0  # a hole's capture radius stays 2 G m / c^2 (review B6-G5)
        boost = None
        if state:  # a file or a copy: the state the world had made of the body (review B6-G4: also its mass, radius)
            x, vel = np.array(state["x"], float), np.array(state["v"], float)
            m = float(state.get("m", m))
            R = float(state.get("radius", R))
            if not self.sim._loading:  # a copy lies on its original (review UX-ui U4): next to it, same velocity
                y, why = self.free_spot(x, R if not rpm else m * rpm)
                if why is not None and y is not None:
                    x = y
                    self._placed_note = (obj["type"], obj["values"].get("x"), obj["values"].get("y"),
                                         obj["values"].get("z"), f"копия поставлена рядом, в ({_fmt(y)}) а.е., с той же "
                                         f"скоростью: на месте оригинала две точечные массы совпали бы")
        else:
            x = np.array([v["x"], v["y"], v["z"]], float)
            self._free_check(obj, x, m, R, rpm)
            vel, boost = self._start_velocity(obj, x, m)
        pre = self._shown()
        self._engine_edit(self.nb.add, x, vel, m, 0.0 if rpm else R, key=obj["id"], radius_per_mass=rpm)
        if boost is not None and self.nb.n > 1:
            V = self.nb.velocities()
            try:
                self._engine_edit(self.nb.set_many, {k: {"v": V[i] + boost} for i, k in enumerate(self.nb.keys)
                                                     if k != obj["id"]})
            except Exception:
                self.nb.remove(obj["id"])
                raise
        self.trail_kink(self.sim.t, pre, self._shown())
        self._changed()
        note, self._placed_note = self._placed_note, None
        if note and note[:4] == (obj["type"], obj["values"].get("x"), obj["values"].get("y"), obj["values"].get("z")) \
                and not self.sim._loading:
            self.sim.emit({"type": "event", "kind": "scene", "t": self.sim.t, "notify": True,
                           "text": f"«{obj['label']}»: {note[4]}"})

    def on_remove(self, obj):
        if self.nb.has(obj["id"]):
            self._sync()
            pre = self._shown()
            self.nb.remove(obj["id"])
            self.trail_kink(self.sim.t, pre, self._shown())
            self._trail_drop(obj["id"])
            self.emit_trails()
            self.emit_trails(full=True)  # the views drop the removed body's trail
            self._changed()
        elif obj["id"] in self.trail_kept:  # a body that had merged: its trail goes with its object
            self._trail_drop(obj["id"])
            self.emit_trails()
            self.emit_trails(full=True)

    def on_set(self, obj, old):
        """Only what changed reaches the engine (review B6-G4: a change of colour no longer reset a merged body's
        radius); a velocity mode or velocity changed sets the velocity again (with the others' reflex for
        "circular")."""
        if obj["type"] == "field" or not self.nb.has(obj["id"]):
            return
        self._sync()
        v, k = obj["values"], obj["id"]
        kw = {}
        if any(v[c] != old.get(c) for c in ("x", "y", "z")):
            kw["x"] = np.array([v["x"], v["y"], v["z"]], float)
        m, R = self._mass_radius(obj)
        if v.get("mass") != old.get("mass"):
            kw["m"] = m
        if obj["type"] != "hole" and v.get("radius") != old.get("radius"):
            kw["radius"] = R
        changes = {k: kw}
        if any(v.get(c) != old.get(c) for c in ("tvx", "tvy", "tvz")):
            # a throw (P16.2): the velocity in the scene's units per world second becomes the body's own (km/s,
            # «задать»); the others keep theirs (a throw is not a circular start)
            tv = np.array([v["tvx"], v["tvy"], v["tvz"]], float)
            speed = float(np.linalg.norm(tv)) * K.AU
            if not speed < 0.1 * K.C:
                raise Refusal(f"скорость броска {speed / 1e3:.4g} км/с — не меньше 0,1 скорости света: ньютоновская "
                              f"механика здесь неприменима", hint="бросьте медленнее или уменьшите масштаб броска")
            kms = tv * K.AU / 1e3
            obj["values"] = {**v, "vmode": "manual", "vx": float(kms[0]), "vy": float(kms[1]), "vz": float(kms[2])}
            v = obj["values"]
            kw["v"] = tv * YR
        elif any(v.get(c) != old.get(c) for c in ("vmode", "vx", "vy", "vz")):
            b = self.nb.body(k)
            kw["v"], boost = self._start_velocity(obj, kw.get("x", b["x"]), kw.get("m", b["m"]), key=k)
            if boost is not None:
                V = self.nb.velocities()
                changes.update({kk: {"v": V[i] + boost} for i, kk in enumerate(self.nb.keys) if kk != k})
        if not kw:
            return  # a colour: nothing of the world changes
        pre = self._shown()
        self._engine_edit(self.nb.set_many, changes)
        self.trail_kink(self.sim.t, pre, self._shown())
        self._changed()

    def object_state(self, obj):
        if self.nb.has(obj["id"]):
            b = self.nb.body(obj["id"])
            return {"x": b["x"], "v": b["v"], "m": b["m"], "radius": b["radius"]}
        return None

    def _changed(self):
        """The scene changed: the conservation laws count from now; the frame may grow to BOX_GROWTH times the
        scene's present size (a body flung out leaves the frame instead of shrinking the rest to a point: review
        B6-G19)."""
        self.ref = None
        self.mark = None
        X = self.nb.positions()
        ext = float(np.max(np.abs(X))) * 1.15 if len(X) else 0.0
        size = 2.0 ** math.ceil(math.log2(ext)) if math.isfinite(ext) and ext > 0.0 else self.box_h
        self.box_cap = BOX_GROWTH * max(size, 1.5)
        approx = (["чёрная дыра — ньютоновская точечная масса с радиусом Шварцшильда как радиусом захвата (не ОТО)"]
                  if any(o["type"] == "hole" for o in self.sim.objects.values()) else [])
        self.sim.emit({"type": "approx", "t": self.sim.t, "approximations": ["ньютоновская гравитация точечных масс"] + approx})

    def set_collisions(self, policy):
        self._sync()
        self.nb.set_collisions(policy)
        self.ref = None  # the energy counts from now (a merger at once changes it)
        self.mark = None

    def palette_state(self):
        return {}

    def _write_back(self, obj, m, R):
        """A merged body's mass and radius into its parameters (in its units) where the parameters' ranges allow it
        (review B6-G4); otherwise the parameters keep the set-up and only the world (and a file: object_state) has the
        merged body. Returns whether they were written."""
        upd = {"star": {"mass": m, "radius": R * K.AU / K.R_SUN},
               "planet": {"mass": m / M_EARTH_SUN, "radius": R * K.AU / K.R_EARTH},
               "hole": {"mass": m}}.get(obj["type"])
        if upd is None:
            return False
        vals, errors = self.sim.PALETTE[obj["type"]].schema.resolve(None, {**obj["values"], **upd})
        if errors:
            return False
        obj["values"] = vals
        return True

    def _events(self, events):
        for e in events:
            if e["kind"] == "merge":
                ka, kb = e["keys"]
                kept, gone = e["key"], kb if e["key"] == ka else ka
                objs = self.sim.objects
                la, lb = objs[ka]["label"] if ka in objs else ka, objs[kb]["label"] if kb in objs else kb
                young = [objs[q] for q in (ka, kb) if q in objs and e["t"] * YR - objs[q]["t_added"] < YR]
                hole = any(q in objs and objs[q]["type"] == "hole" for q in (ka, kb))
                if gone in objs:
                    del objs[gone]
                written = kept in objs and self._write_back(objs[kept], e["m"], e["radius"])
                self.sim.rev += 1
                since = (f" через {_years(e['t'] * YR - young[0]['t_added'])} после добавления «{young[0]['label']}»"
                         if young else "")
                verb = "столкнулись: дыра поглотила тело" if hole else "столкнулись и слились"
                # a toast too (review UX-ui U4: a star added inside the Sun vanished with one line in «События»)
                self.sim.emit({"type": "event", "kind": "merge", "t": e["t"] * YR, "notify": True,
                               "text": f"«{la}» и «{lb}» {verb}{since}: масса {_num(e['m'])} M☉, "
                                       f"остался «{objs[kept]['label'] if kept in objs else kept}»"
                                       + ("" if written else " (масса вне диапазона параметров объекта: в инспекторе "
                                                            "прежние, в мире и в файле сцены — слитые)")})
                self.sim.emit_scene()
                self.ref = None
                self.mark = None
            elif e["kind"] == "contact":
                self.sim.emit({"type": "event", "kind": "contact", "t": e["t"] * YR,
                               "text": f"касание: {e['keys'][0]} и {e['keys'][1]} проходят друг сквозь друга"})

    STEPS_PER_CALL = 16  # integrator steps per advance call: the runner keeps its frame budget (no long stall)

    def max_step(self):
        """A few of the integrator's own steps per call (review UX-ui U5: at a high speed one frame's advance ran for
        minutes); the motion does not depend on how time is sliced (continuous output), nor do the trails' points."""
        h = self.nb.step_size
        return self.STEPS_PER_CALL * h * YR if h > 0 else None

    def advance(self, t_target):
        self._run(t_target / YR)

    def _trail_rgb(self, ids):
        objs = self.sim.objects
        return [_rgb(objs[k]["values"].get("color", "#888888")) if k in objs else [0.6, 0.6, 0.6] for k in ids]

    def frame(self):
        nb, objs = self.nb, self.sim.objects
        keys = nb.keys
        X = nb.positions() if keys else np.zeros((0, 3))
        V = nb.velocities() if keys else np.zeros((0, 3))
        rad = nb.radii() if keys else np.zeros(0)
        # a hole is drawn light with a ring and its name (review UX-ui U18: near-black on the near-black scene, it could
        # not be seen); its radius is the Schwarzschild radius (the view draws a body at least 0.6 % of the scene)
        rgb = np.array([_rgb(objs[k]["values"].get("color", "#343a40")) if k in objs and objs[k]["type"] != "hole"
                        else HOLE_RGB for k in keys], np.float32).reshape(-1)
        if len(X):
            ext = float(np.max(np.abs(X))) * 1.15
            if math.isfinite(ext) and ext > self.box_h and self.box_h < self.box_cap:  # grows with what is computed
                self.box_h = min(2.0 ** math.ceil(math.log2(ext)), self.box_cap)
                self.sim.emit({"type": "box", "t": self.sim.t, "box": self._box()})
        now = {}
        M = nb.masses() if keys else np.zeros(0)
        for i, k in enumerate(keys):
            now[k] = {"x, y, z, а.е.": ", ".join(f"{c:.6g}" for c in X[i]),
                      "скорость, км/с": float(np.linalg.norm(V[i])) / KMS,
                      "масса, M☉": float(M[i]), "радиус, а.е.": float(rad[i])}
        probes = {}
        for o in objs.values():
            if o["type"] != "field":
                continue
            pt = np.array([[o["values"]["x"], o["values"]["y"], o["values"]["z"]]], float)
            if nb.n and nb.masses().sum() > 0:
                g = nb.acceleration_at(pt)[0] * K.AU / YR ** 2
                T = nb.tidal_tensor_at(pt)[0] / YR ** 2
                lam = np.linalg.eigvalsh(T)
                probes[o["id"]] = {"g, м/с²": float(np.linalg.norm(g)),
                                   "прилив: растяжение, 1/с²": float(lam[-1]), "прилив: сжатие, 1/с²": float(lam[0])}
            else:
                probes[o["id"]] = {"g, м/с²": 0.0}
        d = {"steps": nb.step_count}
        at = {k: [float(c) for c in X[i]] for i, k in enumerate(keys) if k in objs}
        at.update({o["id"]: [float(o["values"][c]) for c in "xyz"] for o in objs.values() if o["type"] == "field"})
        meas, notes = self.measure_now(probes)
        return ({"ids": keys, "trail_ids": keys, "now": now, "probes": probes, "steps": d["steps"],
                 "holes": [i for i, k in enumerate(keys) if k in objs and objs[k]["type"] == "hole"], "at": at,
                 "meas": meas, **({"meas_note": notes} if notes else {})},
                {"pos": X.astype(np.float32).reshape(-1), "rad": rad.astype(np.float32), "rgb": rgb,
                 "vel": (V / YR).astype(np.float32).reshape(-1)})

    def _box(self):
        h = self.box_h
        return [[-h, -h, -0.5 * h], [h, h, 0.5 * h]]

    # --- measurables (P16.3) -----------------------------------------------------------------------------------------
    E_J = K.M_SUN * (K.AU / YR) ** 2      # J per M_sun au^2 / yr^2
    L_SI = K.M_SUN * K.AU ** 2 / YR       # kg m^2 / s per M_sun au^2 / yr

    def measurables(self):
        out = [{"id": "E", "label": "Полная энергия системы", "unit": "Дж", "of": None, "group": "Сохранение"},
               {"id": "dE", "label": "Уход энергии с последнего изменения сцены (доля Σ½mv² + Σ G mᵢmⱼ/rᵢⱼ)",
                "unit": "", "of": None, "group": "Сохранение"},
               {"id": "L", "label": "Момент импульса системы |L|", "unit": "кг·м²/с", "of": None, "group": "Сохранение"},
               {"id": "dL", "label": "Уход момента импульса с последнего изменения сцены (доля Σ|r × m v|)", "unit": "",
                "of": None, "group": "Сохранение"}]
        to = {"dominant": "до самого массивного другого тела", "com": "до центра масс системы",
              "origin": "до начала координат"}
        for o in self.sim.objects.values():
            oid, lab = o["id"], o["label"]
            if o["type"] == "field":
                out += [{"id": f"{oid}.g", "label": f"«{lab}»: ускорение свободного падения g", "unit": "м/с²",
                         "of": oid, "group": "Датчики"},
                        {"id": f"{oid}.tide", "label": f"«{lab}»: прилив, растяжение", "unit": "1/с²", "of": oid,
                         "group": "Датчики"}]
                continue
            out += [{"id": f"{oid}.dist", "label": f"«{lab}»: расстояние {to[o['values'].get('ref', 'dominant')]}",
                     "unit": "а.е.", "of": oid, "group": "Тела"},
                    {"id": f"{oid}.speed", "label": f"«{lab}»: скорость", "unit": "км/с", "of": oid, "group": "Тела"},
                    {"id": f"{oid}.a", "label": f"«{lab}»: большая полуось (относительно самого массивного другого)",
                     "unit": "а.е.", "of": oid, "group": "Орбиты"},
                    {"id": f"{oid}.e", "label": f"«{lab}»: эксцентриситет", "unit": "", "of": oid, "group": "Орбиты"},
                    {"id": f"{oid}.P", "label": f"«{lab}»: период (задача двух тел)", "unit": "годы", "of": oid,
                     "group": "Орбиты"}]
        return out

    def measure_now(self, probes=None):
        """({id: value}, {id: why undefined}): the system's energy and angular momentum (SI) and their drifts since the
        scene's last change; per body its distance to the chosen reference, its speed and its osculating two-body
        elements about the most massive other body; per probe g and the tidal stretch."""
        nb, objs = self.nb, self.sim.objects
        m, notes = {}, {}
        nan = float("nan")
        if nb.n:
            E, Lv = nb.energy(), nb.angular_momentum()
            m["E"], m["L"] = E * self.E_J, float(np.linalg.norm(Lv)) * self.L_SI
            if self.ref is not None:
                m["dE"] = (E - self.ref["E"]) / (self.ref["S"] or 1.0)
                X0, V0, M0 = nb.positions(), nb.velocities(), nb.masses()
                Ls = float(np.sum(M0 * np.linalg.norm(np.cross(X0, V0), axis=1))) or 1.0
                m["dL"] = float(np.linalg.norm(Lv - self.ref["L"])) / Ls
            else:
                m["dE"] = m["dL"] = nan
                notes["dE"] = notes["dL"] = "отсчёт начинается с первой проверки после изменения сцены"
        else:
            m["E"] = m["L"] = m["dE"] = m["dL"] = nan
            notes["E"] = notes["L"] = notes["dE"] = notes["dL"] = "в сцене нет тел"
        keys = nb.keys
        X, V, M = (nb.positions(), nb.velocities(), nb.masses()) if keys else (None, None, None)
        com = (M[:, None] * X).sum(0) / M.sum() if keys and M.sum() > 0 else np.zeros(3)
        heavy = sorted((j for j in range(len(keys)) if M[j] > 0), key=lambda j: (-M[j], j)) if keys else []
        for o in objs.values():
            oid = o["id"]
            if o["type"] == "field":
                pr = (probes or {}).get(oid)
                if pr is None:
                    pt = np.array([[o["values"][c] for c in "xyz"]], float)
                    pr = {"g, м/с²": 0.0}
                    if nb.n and nb.masses().sum() > 0:
                        pr = {"g, м/с²": float(np.linalg.norm(nb.acceleration_at(pt)[0] * K.AU / YR ** 2)),
                              "прилив: растяжение, 1/с²": float(np.linalg.eigvalsh(nb.tidal_tensor_at(pt)[0] / YR ** 2)[-1])}
                m[f"{oid}.g"] = pr["g, м/с²"]
                m[f"{oid}.tide"] = pr.get("прилив: растяжение, 1/с²", 0.0)
                continue
            if oid not in keys:
                for q in ("dist", "speed", "a", "e", "P"):
                    m[f"{oid}.{q}"] = nan
                    notes[f"{oid}.{q}"] = "тела нет в расчёте (слилось с другим)"
                continue
            i = keys.index(oid)
            m[f"{oid}.speed"] = float(np.linalg.norm(V[i])) / KMS
            d = next((j for j in heavy[:2] if j != i), None)  # the most massive other body
            ref = o["values"].get("ref", "dominant")
            if ref == "com":
                m[f"{oid}.dist"] = float(np.linalg.norm(X[i] - com))
            elif ref == "origin":
                m[f"{oid}.dist"] = float(np.linalg.norm(X[i]))
            elif d is not None:
                m[f"{oid}.dist"] = float(np.linalg.norm(X[i] - X[d]))
            else:
                m[f"{oid}.dist"] = nan
                notes[f"{oid}.dist"] = "нет другого массивного тела"
            if d is None:
                for q in ("a", "e", "P"):
                    m[f"{oid}.{q}"] = nan
                    notes[f"{oid}.{q}"] = "нет другого массивного тела: орбиты нет"
                continue
            r, v = X[i] - X[d], V[i] - V[d]
            mu = G_AU * (M[i] + M[d])
            rn, v2 = float(np.linalg.norm(r)), float(v @ v)
            ev = ((v2 - mu / rn) * r - float(r @ v) * v) / mu
            eps = 0.5 * v2 - mu / rn
            m[f"{oid}.e"] = float(np.linalg.norm(ev))
            if eps < 0.0:
                a = -mu / (2.0 * eps)
                m[f"{oid}.a"], m[f"{oid}.P"] = a, 2.0 * math.pi * math.sqrt(a ** 3 / mu)
            else:
                m[f"{oid}.a"] = m[f"{oid}.P"] = nan
                notes[f"{oid}.a"] = notes[f"{oid}.P"] = "не связано с самым массивным телом (парабола или гипербола)"
        return m, notes

    def checks(self):
        nb = self.nb
        if nb.n == 0 or nb.masses().sum() <= 0.0:
            return
        E, P, L = nb.energy(), nb.momentum(), nb.angular_momentum()
        pscale = float(np.sum(nb.masses()[:, None] * np.abs(nb.velocities()))) or 1.0
        if self.ref is None:
            # the energy's scale: kinetic + |potential| (zero only for bodies at rest with at most one massive body,
            # whose energy is then exactly 0; review B6-G3: the energy itself may vanish, e.g. a star at rest with test
            # bodies)
            self.ref = {"E": E, "P": P.copy(), "L": L.copy(), "err": 0.0, "t": nb.t, "n": 0, "n_comp": 0,
                        "S": nb.kinetic_energy() + abs(nb.potential_energy())}
            self.mark = nb.state_dict()
            return
        self.n_checks += 1
        self.ref["n"] += 1
        # the companion: the last interval again with eta / 2; its difference is the error of this interval
        every = self.COMPANION_EVERY if nb.n <= self.COMPANION_N else self.COMPANION_EVERY_LARGE
        if self.mark is not None and self.n_checks % every == 0:
            comp = NB.NBody.from_state_dict(self.mark, eta=nb.eta / 2.0)
            comp.advance(nb.t)
            dx = float(np.max(np.abs(comp.positions() - nb.positions()))) if comp.keys == nb.keys else float("nan")
            self.ref["err"] += abs(comp.energy() - E)
            self.ref["n_comp"] += every
            size = float(np.max(np.abs(nb.positions()))) or 1.0
            self.sim.running_check("companion", "Численная ошибка положений (против расчёта с вдвое меньшим η)",
                                   dx / size, None, tol=0.0, info=True,
                                   note=f"интервал с t = {self.mark['t_out'] * YR:.6g} с пересчитан с параметром точности "
                                        f"η = {nb.eta / 2:g} вместо {nb.eta:g}: наибольшее различие положений {dx:.3g} "
                                        f"а.е., доля размера системы — оценка ошибки расчёта на интервале (шаг ∝ √η: "
                                        f"с η/2 он в √2 раз короче, а ошибка схемы 4-го порядка — примерно в 4 раза "
                                        f"меньше, измерено 4,05–4,11)")
        if self.n_checks % every == 0:
            self.mark = nb.state_dict()
        u = 2.0 ** -53
        self.sim.running_check("momentum", "Импульс системы (сохраняется: силы попарно противоположны)",
                               float(np.linalg.norm(P - self.ref["P"])) / pscale, 0.0, tol=1e-12,
                               ok=float(np.linalg.norm(P - self.ref["P"])) <= 1e-12 * pscale,
                               note="изменение |P| с последнего изменения сцены, относительно Σ|m v|; допуск 10⁻¹² "
                                    "(округление сумм сил)")
        dE = abs(E - self.ref["E"])
        # the companion's measured energy error per interval, scaled to all the intervals since the scene's change
        err = self.ref["err"] * max(self.ref["n"], 1) / max(self.ref["n_comp"], 1)
        tolE = 3.0 * err + 1e3 * u * abs(E)
        S = self.ref["S"] or 1.0  # S = 0: E is exactly 0 and stays so; the change is shown absolute
        self.sim.running_check("energy", "Энергия системы (сохраняется)", (E - self.ref["E"]) / S, 0.0,
                               tol=tolE / S, ok=dE <= tolE or self.ref["err"] == 0.0,
                               note="изменение энергии с последнего изменения сцены относительно Σ½mv² + Σ G mᵢmⱼ/rᵢⱼ "
                                    "(в тот момент; полная энергия может быть нулевой); допуск — трижды ошибка "
                                    "энергии, измеренная компаньоном (тот же интервал с η/2: его ошибка вчетверо "
                                    "меньше, так что ошибка счёта не больше 4/3 их разности; "
                                    + ("каждый интервал" if every == 1 else f"каждый {every}-й интервал, отнесённая "
                                       "ко всем пройденным") + ")"
                                    + (" (компаньон ещё не считался)" if self.ref["err"] == 0.0 else ""))
        dL = float(np.linalg.norm(L - self.ref["L"]))
        X, V, m = nb.positions(), nb.velocities(), nb.masses()
        Ls = float(np.sum(m * np.linalg.norm(np.cross(X, V), axis=1))) or 1.0  # sum |r x m v|: the system's total L may be 0
        self.sim.running_check("angular", "Момент импульса системы (сохраняется)", dL / Ls, 0.0, tol=0.0, info=True,
                               note="изменение L с последнего изменения сцены относительно Σ|r × m v| (полный момент "
                                    "может быть нулевым); схема Эрмита сохраняет момент не точно, а с ошибкой порядка "
                                    "схемы, как энергию")

    def header(self):
        return {"title": "Плейграунд: ньютоновские N тел",
                "approximations": ["ньютоновская гравитация точечных масс"],
                "scene3d": {"box": self._box(), "units": "а.е.", "objects": [], "layers": [],
                            "planes": {"max": 0, "center": [0, 0, 0], "defaults": {}}, "up": [0.0, 0.0, 1.0],
                            "views": [["iso", "Изо", "Изометрия (F)", [0.5, -0.7, 0.5]],
                                      ["pole", "Сверху", "Вдоль оси z: плоскость xy", [0.0, 0.0, 1.0]],
                                      ["side", "Сбоку", "Плоскость xy с ребра", [0.0, -1.0, 0.0]]]},
                "units": {"t": "с", "x": "а.е."}}

    def after_header(self):
        pass

    def engine_modules(self):
        return ["core.gravity.nbody"]


# --- bodies, light and clocks around a Kerr-Newman black hole -----------------------------------------------------
KBODY = Schema([_p("r", "Расстояние r, G M/c²", "float", 10.0, min=1.0, max=1000.0, log=True,
                   help="Бойер–Линдквист; должно быть вне горизонта"),
                _p("theta", "Полярный угол θ, °", "float", 90.0, min=1.0, max=179.0, help="90° — экватор"),
                _p("phi", "Азимут φ, °", "float", 0.0, min=0.0, max=360.0),
                _p("vmode", "Скорость", "select", "circular", options=[
                    ("circular", "круговая орбита в экваторе (по вращению)"),
                    ("circular_retro", "круговая орбита в экваторе (против вращения)"),
                    ("zamo", "задать скорость, измеренную наблюдателем без момента (ZAMO), в долях c")]),
                _p("v_r", "v_r / c (наружу)", "float", 0.0, min=-0.99, max=0.99, show_if={"vmode": ["zamo"]}),
                _p("v_theta", "v_θ / c (к южному полюсу)", "float", 0.0, min=-0.99, max=0.99,
                   show_if={"vmode": ["zamo"]}),
                _p("v_phi", "v_φ / c (по вращению)", "float", 0.3, min=-0.99, max=0.99, show_if={"vmode": ["zamo"]}),
                _p("color", "Цвет", "select", "#e9ecef", options=COLOR.options)])
# a drag (P16.2) moves the object in the drawing coordinates (x + i y = sqrt(r^2 + a^2) sin theta e^(i phi), z = r cos
# theta, in G M/c^2): hidden parameters, turned into r, theta, phi; a throw sends the velocity in them per world second
KXYZ = [_p(c, f"Положение в сцене: {c}, G M/c²", "float", 0.0, min=-1e4, max=1e4, hidden=True) for c in "xyz"]
KTHROW = [_p(c, f"Бросок: {c[1:]}", "float", 0.0, min=-1e12, max=1e12, hidden=True, unit="(G M/c²)/с")
          for c in ("tvx", "tvy", "tvz")]
# the largest throw the player gives a body (review LB1-p02-ux X4): half the speed of light in the drawing coordinates,
# 0.5 G M/c² per G M/c³ = 0.5 / T per world second (set by the world from the hole's mass; a brisk flick gives half of it);
# near the hole the speed the local ZAMO measures is larger (1/alpha), and a throw at 0.99 c or more by it is refused
KVMAX = _p("tv_max", "Наибольшая скорость броска", "float", 1.0, min=0.0, max=1e15, hidden=True, unit="(G M/c²)/с")
KBODY = Schema([*KBODY.params, *KXYZ, *KTHROW, KVMAX])
THROW_C = 0.5  # the throw limit in units of c (drawing coordinates)
KHOLE = Schema([_p("mass", "Масса M, M☉", "float", 10.0, min=0.1, max=1e10, log=True,
                   help="Меняется в текущий момент как смена масштаба (G = c = M = 1): тела в единицах M остаются где "
                        "были и с теми же скоростями, метры и секунды пересчитываются (тело на r = 6 M при M ×2 — вдвое "
                        "дальше в километрах); собственное время тел и часы наблюдателей в секундах сохраняются"),
                _p("spin", "Спин a/M", "float", 0.9, min=0.0, max=0.998,
                   help="Меняется в текущий момент только как модель «что если» (у смены метрики под движущимися телами "
                        "нет установленной динамики): каждое тело сохраняет положение (r, θ, φ) и скорость, измеренную "
                        "местным наблюдателем без момента (ZAMO); E, L и постоянная Картера пересчитываются; мир "
                        "помечается как модель"),
                _p("charge", "Заряд Q/M (геометрические единицы)", "float", 0.0, min=0.0, max=0.99,
                   help="Как спин: на ходу — модель «что если»; a² + Q² < 1, иначе нет горизонта")])
KLIGHT = Schema([_p("r", "Расстояние r, G M/c²", "float", 15.0, min=1.0, max=1000.0, log=True),
                 _p("theta", "Полярный угол θ, °", "float", 90.0, min=1.0, max=179.0),
                 _p("phi", "Азимут φ, °", "float", 0.0, min=0.0, max=360.0),
                 _p("psi", "Направление в плоскости r–φ, ° от «внутрь»", "float", 20.0, min=-180.0, max=180.0,
                    help="0° — прямо к дыре; 90° — по вращению; измерено наблюдателем без момента (ZAMO)"),
                 _p("elev", "Наклон к экватору, °", "float", 0.0, min=-89.0, max=89.0), *KXYZ])
KOBS = Schema([_p("kind", "Наблюдатель", "select", "static", options=[
                   ("static", "неподвижный (держится двигателем; только вне эргосферы)"),
                   ("zamo", "без момента импульса (ZAMO: увлекается вращением)"),
                   ("circular", "на круговой орбите в экваторе (свободно падает)")]),
               _p("r", "Расстояние r, G M/c²", "float", 6.0, min=1.0, max=1000.0, log=True),
               _p("theta", "Полярный угол θ, °", "float", 90.0, min=1.0, max=179.0),
               _p("phi", "Азимут φ, °", "float", 45.0, min=0.0, max=360.0), *KXYZ])


SUB0 = 0.05      # G M/c^3: the first sub-step of a Kerr world after a body is added (then measured)
SUB_MAX = 50.0   # G M/c^3: the longest sub-step (far bodies turn slowly)


class KerrMode(Trails):
    default_speed = 1.0
    speed_range = (1e-9, 1e9)

    def __init__(self, sim):
        self.sim = sim
        p = sim.params
        self.a, self.q = float(p["spin"]), float(p["charge"])
        if self.a ** 2 + self.q ** 2 >= 1.0:
            raise ValueError("a² + Q² должно быть меньше 1: иначе у дыры нет горизонта (голая сингулярность)")
        self.M = float(p["m_hole"])  # M_sun: the hole object's mass (P16.1), the world's parameter at the start
        self.gm = self.M * K.GM_SUN
        self.T = self.gm / K.C ** 3  # s per G M / c^3
        self.clk = Clock(self.T)     # the world's seconds <-> t in units of M (a change of M rescales the seconds)
        self.geo = KN.Geodesics(self.a, self.q, rtol=1e-10, t=0.0, capture_eps=1e-4, r_escape=2e3)
        self.hole_id = None          # the hole's object in the scene (always there: the world is the hole's)
        self.model = []              # the «what if» changes of the metric made so far (flagged as a model)
        self.peri = {}               # key -> the last two periapsis passages (world seconds, as recorded; cleared when
        #                              the hole changes: review LB1-physics P10): the radial period
        self.default_speed = 10.0 * self.T  # 10 G M/c^3 of the world per second
        self.speed_range = (1e-3 * self.T, 1e5 * self.T)
        self.r_plus = KN.horizons(self.a, self.q)[0]
        self.r_isco = KN.isco(self.a, self.q, True)
        self._trails_init()
        # observer id -> (t0, tau at t0, phi at t0): its clock and its place counted from the moment it was placed
        # (review B6-G12: an observer added later was drawn as if placed at t = 0)
        self.obs = {}
        self.box_h = 20.0
        self.sub = SUB0  # the next sub-step (G M/c^3): the bodies turn at most ~CAND_TURN in one (``advance``)
        self._kv = {}    # key -> the velocity at the last candidate point (the measured turn sets ``sub``)

    def palette(self):
        p = self.sim.params
        hole = Schema([q if q.id not in ("mass", "spin", "charge") else
                       Param(**{**q.__dict__, "default": float(p[{"mass": "m_hole"}.get(q.id, q.id)])})
                       for q in KHOLE.params])
        return {"kn_hole": _otype("kn_hole", "Чёрная дыра Керра–Ньюмена", "body", hole, limit=1, color="#343a40",
                                  help="Дыра этого мира (в начале координат): её масса меняется в текущий момент как "
                                       "смена масштаба, спин и заряд — как модель «что если»; убрать её нельзя — мир "
                                       "считается вокруг неё"),
                "body": _otype("body", "Пробное тело", "particle", KBODY, color="#e9ecef",
                               handles={"position": ["x", "y", "z"], "velocity": ["tvx", "tvy", "tvz"],
                                        "velocity_max": "tv_max"},
                               help="Тело без собственного поля и заряда: движется по геодезической; свои часы. "
                                    "Смена положения или скорости запускает его заново с текущего момента, смена "
                                    "цвета — нет; брошенное мышью — со скоростью броска, измеренной наблюдателем без "
                                    "момента (ZAMO)"),
                "light": _otype("light", "Луч света", "light", KLIGHT, color="#ffd43b",
                                handles={"position": ["x", "y", "z"]},
                                help="Фотон, испущенный в момент добавления: изотропная геодезическая"),
                "observer": _otype("observer", "Наблюдатель с часами", "observer", KOBS, limit=8, color="#4dabf7",
                                   handles={"position": ["x", "y", "z"]},
                                   help="Часы наблюдателя против часов далёкого наблюдателя; на круговой орбите — "
                                        "только не ближе ISCO (ближе орбита неустойчива)")}

    def t_m(self):
        return self.clk.geo(self.sim.t)

    def _sync(self):
        if self.geo.t < self.t_m():
            self.advance(self.sim.t)

    START = {"body": ("r", "theta", "phi", "vmode", "v_r", "v_theta", "v_phi"),
             "light": ("r", "theta", "phi", "psi", "elev")}  # the parameters of a start (review B6-G13)

    def on_add(self, obj, state):
        v = obj["values"]
        if obj["type"] == "kn_hole":
            self.hole_id = obj["id"]
            self.set_hole(obj, None)
            return
        if obj["type"] in ("body", "light", "observer"):
            self._xyz_from_bl(obj)
        if obj["type"] == "body":
            obj["values"] = {**obj["values"], "tv_max": THROW_C / self.T}
        if obj["type"] == "observer":
            self._observer_check(v)
            if state:  # a file or a copy: its clock reading and place then (the reading in units of the state's M)
                M0 = float(state.get("M", self.M))
                if M0 != self.M:
                    self.sim.carry_note(f"масса дыры {M0:.6g} → {self.M:.6g} M☉: показание часов в секундах сохранено")
                self.obs[obj["id"]] = (self.t_m(), float(state["tau"]) * M0 / self.M, float(state["phi"]))
            else:
                self.obs[obj["id"]] = (self.t_m(), 0.0, math.radians(v["phi"]))
            return
        self._sync()
        r, th, ph = float(v["r"]), math.radians(v["theta"]), math.radians(v["phi"])
        if state:  # a file, a copy or a carry-over: in this hole's metric and units (review LB1-framework F5)
            state = self._state_here(obj, state)
        if state:  # a file or a copy: its geodesic state, also after a capture or an escape (review B6-G11)
            self.geo.add_state(state["r"], state["theta"], state["phi"], np.array(state["p"]), state["mu2"],
                               key=obj["id"], tau=state.get("tau", 0.0), status=state.get("status", "active"),
                               K0=state.get("K0"), budget=state.get("budget", (0.0, 0.0)))
        elif r <= self.r_plus * (1.0 + 1e-6):
            raise ValueError(f"r = {r:g} G M/c² — под горизонтом (r₊ = {self.r_plus:.5g})")
        elif obj["type"] == "body":
            if v["vmode"] in ("circular", "circular_retro"):
                if abs(v["theta"] - 90.0) > 1e-9:
                    raise ValueError("круговая орбита — только в экваторе (θ = 90°)")
                co = KN.circular_orbit(r, self.a, self.q, v["vmode"] == "circular")
                if not np.isfinite(co["dtau_dt"]):
                    raise ValueError(f"на r = {r:g} G M/c² нет круговой орбиты для тела (внутри фотонной орбиты)")
                z = KN.zamo(r, th, self.a, self.q)
                vel = (0.0, 0.0, float((co["Omega"] - z["omega"]) * z["varpi"] / z["alpha"]))
            else:
                vel = (float(v["v_r"]), float(v["v_theta"]), float(v["v_phi"]))
                if vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2 >= 1.0:
                    raise ValueError("скорость не меньше скорости света")
            self.geo.add_body(r, th, ph, vel, key=obj["id"])
        else:
            psi, el = math.radians(v["psi"]), math.radians(v["elev"])
            n = (-math.cos(psi) * math.cos(el), -math.sin(el), math.sin(psi) * math.cos(el))
            self.geo.add_photon(r, th, ph, n, key=obj["id"])
        self.sub = SUB0  # a new body: the sub-step is measured again from a short one
        self.peri.pop(obj["id"], None)
        self._feed()

    def _state_here(self, obj, state):
        """A saved or carried body's or ray's state (r, theta, phi, p in units of its hole's M, in its metric chi, q) put
        into this hole's (review LB1-framework F5): the same metric — as it is; another mass only — the same state in
        units of M (a change of units: the proper time kept in seconds); another spin or charge (a new world of other
        laws) — the body starts this world where it was, with the momentum its local ZAMO measured (the frame energy from
        the mass shell; ``kerr_newman.zamo_frame_momentum`` / ``momentum_from_frame``): the new world's initial
        condition, said in the carry-over's notice; under the new capture radius it starts anew from its parameters (said).
        Returns the state to add, or None (start from the parameters). States without "chi" (older files): as they are."""
        st = dict(state)
        M0 = float(st.get("M", self.M))
        if M0 != self.M:
            st["tau"] = float(st.get("tau", 0.0)) * M0 / self.M
            self.sim.carry_note(f"масса дыры {M0:.6g} → {self.M:.6g} M☉: на прежнем месте в единицах M, собственное время в "
                            f"секундах сохранено")
        chi0, q0 = float(st.get("chi", self.a)), float(st.get("q", self.q))
        if (chi0, q0) == (self.a, self.q):
            return st
        r0, th = float(st["r"]), float(st["theta"])
        eps = self.geo.capture_eps
        if st.get("status", "active") == "active" and not r0 > self.r_plus + eps:
            self.sim.carry_note(f"было на r = {r0:.5g} G M/c², под горизонтом новой дыры (r₊ = {self.r_plus:.5g}): начато "
                            f"заново из своих параметров", restarted=True)
            return None
        r1 = max(r0, self.r_plus + eps) if st.get("status") == "captured" else r0
        hat = KN.zamo_frame_momentum(r0, th, chi0, q0, np.asarray(st["p"], float))
        sp = hat[1:]
        e = math.sqrt(float(st["mu2"]) + float(sp @ sp))
        st.update(r=r1, p=KN.momentum_from_frame(r1, th, self.a, self.q, np.array([e, *sp])).tolist(),
                  budget=(0.0, 0.0))
        st.pop("K0", None)
        self.sim.carry_note(f"в метрике этой дыры (a {chi0:.4g} → {self.a:.4g}, Q {q0:.4g} → {self.q:.4g}) начато с прежнего "
                        f"места (r, θ, φ) и с импульсом, который измерял местный наблюдатель без момента (ZAMO); E, L и "
                        f"постоянная Картера — новые")
        return st

    def _xyz_from_bl(self, obj):
        """The hidden drawing coordinates (the handle's x, y, z) of an object from its r, theta, phi."""
        v = obj["values"]
        x, y, z = KN.cartesian(float(v["r"]), math.radians(v["theta"]), math.radians(v["phi"]), self.a)
        obj["values"] = {**v, "x": float(x), "y": float(y), "z": float(z)}

    def _bl_from_xyz(self, obj):
        """r, theta, phi of an object dragged to its drawing coordinates x, y, z (a circular orbit or observer: to the
        equator under the point); refused under the horizon."""
        v = obj["values"]
        r, th, ph = (float(np.asarray(u)) for u in KN.from_cartesian(float(v["x"]), float(v["y"]), float(v["z"]),
                                                                       self.a))
        if not r > self.r_plus * (1.0 + 1e-6):
            raise Refusal(f"«{obj['label']}»: точка ({_fmt([v['x'], v['y'], v['z']])}) G M/c² — под горизонтом "
                          f"(r₊ = {self.r_plus:.4g})", hint="перетащите дальше от дыры")
        th = 90.0 if v.get("vmode", v.get("kind")) in ("circular", "circular_retro") else min(max(math.degrees(th), 1.0), 179.0)
        obj["values"] = {**v, "r": min(max(r, 1.0), 1000.0), "theta": th, "phi": math.degrees(ph) % 360.0}
        self._xyz_from_bl(obj)

    def _zamo_of_throw(self, obj):
        """The ZAMO-measured velocity (fractions of c) of a body thrown in the scene: the drawing-coordinate velocity
        (G M/c^2 per world second) into dr/dt, dtheta/dt, dphi/dt by the inverse Jacobian of the drawing map, then the
        ZAMO's frame: v_r = sqrt(Sigma/Delta) r'/alpha, v_theta = sqrt(Sigma) theta'/alpha, v_phi = varpi (phi' - omega)/alpha
        (primes: d/dt in units of M)."""
        v = obj["values"]
        r, th, ph = float(v["r"]), math.radians(v["theta"]), math.radians(v["phi"])
        w = np.array([v["tvx"], v["tvy"], v["tvz"]], float) * self.T  # per unit of M
        R = math.sqrt(r * r + self.a * self.a)
        st, ct, sp, cp = math.sin(th), math.cos(th), math.sin(ph), math.cos(ph)
        J = np.array([[r / R * st * cp, R * ct * cp, -R * st * sp],
                      [r / R * st * sp, R * ct * sp, R * st * cp],
                      [ct, -r * st, 0.0]])
        dr, dth, dph = np.linalg.solve(J, w)
        z = KN.zamo(r, th, self.a, self.q)
        al = float(z["alpha"])
        vz = np.array([math.sqrt(float(z["Sigma"]) / float(z["Delta"])) * dr / al, math.sqrt(float(z["Sigma"])) * dth / al,
                       float(z["varpi"]) * (dph - float(z["omega"])) / al])
        if not float(np.linalg.norm(vz)) < 0.99:
            raise Refusal(f"«{obj['label']}»: скорость броска, измеренная местным наблюдателем, {float(np.linalg.norm(vz)):.3g} c "
                          f"— не меньше 0,99 c", hint="бросьте медленнее или уменьшите масштаб броска")
        return vz

    def place(self, kind, values):
        """A clicked point (``position``, drawing coordinates) as r, theta, phi of the new object; a circular orbit
        goes to the equator under it (review UX-ui U4). The hole sits at the origin: no point."""
        pos = values.pop("position", None)
        if kind == "kn_hole":
            return values
        if not (isinstance(pos, (list, tuple)) and len(pos) >= 3):
            return values
        r, th, ph = (float(np.asarray(u)) for u in KN.from_cartesian(*[float(c) for c in pos[:3]], self.a))
        if not r > self.r_plus * (1.0 + 1e-6):
            raise Refusal(f"точка ({_fmt(pos[:3])}) G M/c² — под горизонтом (r₊ = {self.r_plus:.4g})",
                          hint="щёлкните дальше от дыры")
        values.update(r=min(max(r, 1.0), 1000.0), theta=min(max(math.degrees(th), 1.0), 179.0),
                      phi=math.degrees(ph) % 360.0)
        if kind in ("body", "observer") and values.get("vmode", values.get("kind", "circular")) in (
                "circular", "circular_retro"):
            values["theta"] = 90.0
        return values

    def palette_state(self):
        return {"kn_hole": "дыра в этом мире одна и уже в сцене: её масса, спин и заряд — в её инспекторе"} \
            if self.hole_id is not None else {}

    def can_remove(self, obj):
        if obj["type"] == "kn_hole":
            return "мир считается вокруг этой дыры (другая дыра — новый мир)"
        return None

    # --- the hole (P16.1): its mass a change of units, its spin and charge a declared «what if» -----------------------
    def init_hole(self, M, a, q):
        """The hole a world starts with (its scene's hole object), before any body is placed in its metric."""
        if a * a + q * q >= 1.0:
            raise ValueError("a² + Q² должно быть меньше 1: иначе у дыры нет горизонта (голая сингулярность)")
        self.a, self.q, self.M = float(a), float(q), float(M)
        self.geo = KN.Geodesics(self.a, self.q, rtol=1e-10, t=self.geo.t, capture_eps=1e-4, r_escape=2e3)
        self.r_plus, self.r_isco = KN.horizons(self.a, self.q)[0], KN.isco(self.a, self.q, True)
        self.gm = self.M * K.GM_SUN
        self.T = self.gm / K.C ** 3
        self.clk = Clock(self.T)
        self.default_speed = 10.0 * self.T
        self.speed_range = (1e-3 * self.T, 1e5 * self.T)

    def set_hole(self, obj, old):
        """The hole's mass, spin and charge as its object says, at the current moment. The mass (G = c = M = 1): a change
        of units — every body keeps its place and velocity in units of M, the world's seconds per unit of M change (the
        geometric clock goes on: ``Clock``), proper times and observers' readings in seconds are kept, and lengths in
        metres scale with M. Spin and charge: no established dynamics changes a metric under moving bodies; offered as a
        model «what if», flagged: each body keeps its Boyer-Lindquist place (r, theta, phi), its proper time and the
        3-velocity its local ZAMO measures (a ray: its direction), and gets the E, L and Carter's K of that in the new
        metric (their drift accounting restarts); refused when a body, a ray or an observer would be inside the new
        capture radius, a static observer inside the new ergosurface or a circular one inside the new ISCO. Returns the
        event's text (None at the world's start)."""
        v = obj["values"]
        M, a, q = float(v["mass"]), float(v["spin"]), float(v["charge"])
        if a * a + q * q >= 1.0:
            raise Refusal(f"a² + Q² = {a * a + q * q:.4g} — не меньше 1: у дыры не было бы горизонта (голая "
                          f"сингулярность)", hint="спин или заряд меньше")
        texts = []
        if (a, q) != (self.a, self.q):
            texts.append(self._what_if_metric(a, q))
        if M != self.M:
            texts.append(self._rescale_mass(M))
        return "; ".join(t for t in texts if t) or None

    def _shown(self):
        """(keys, drawing positions, velocities per world second) of the moving bodies now (the trails' kinks)."""
        g = self.geo
        st = g.status()
        rows = [i for i in range(g.n) if st[i] == "active"]
        X = g.cartesian()[rows] if rows else np.zeros((0, 3))
        return tuple(g.keys[i] for i in rows), X, self._vel(rows) / self.T

    def _what_if_metric(self, a, q):
        """The declared «what if» of the hole's spin and charge changed now (``theories.alternatives.kn_change_whatif``,
        review LB1-physics P5): the engine's rule carries the bodies over (Boyer-Lindquist place, proper time and
        ZAMO-measured momentum kept; a photon's ZAMO frequency kept; no speed limit below c, review P6), or refuses with
        the body named; the observers keep their place and clock (refused where the new metric has no such observer).
        Returns the event's text with the rule's numbers (None at the world's start)."""
        g, objs = self.geo, self.sim.objects
        moving = g.n > 0 or self.obs
        if moving:
            self._sync()
        try:
            out = WHATIF.carry(g, a, q)
        except WHATIF.Refused as e:
            lab = objs[e.key]["label"] if e.key in objs else e.key
            raise Refusal((f"«{lab}»: " if e.key is not None else "") + str(e), hint=e.hint) from e
        new, r_plus = out["geodesics"], out["r_plus"]
        tm = self.t_m()
        anchors = {}
        for oid in self.obs:
            ov = objs[oid]["values"]
            why = WHATIF.observer_refusal(ov["kind"], float(ov["r"]), math.radians(ov["theta"]), a, q)
            if why is not None:
                raise Refusal(f"наблюдатель «{objs[oid]['label']}»: {why[0]}", hint=why[1])
            tau_o, ph_o = self._obs_now(oid, ov, tm)
            anchors[oid] = (tm, tau_o, ph_o)
        pre = self._shown()
        a0, q0 = self.a, self.q
        self.a, self.q, self.geo = a, q, new
        self.r_plus, self.r_isco = r_plus, KN.isco(a, q, True)
        self.obs.update(anchors)
        for oid in self.obs:
            self._xyz_from_bl(objs[oid])
        for k in self.geo.keys:
            if k in objs and objs[k]["type"] in ("body", "light"):
                self._xyz_from_bl(objs[k])
            self.peri.pop(k, None)  # the radial period is measured anew in the new metric (review LB1-physics P10)
        self.trail_kink(self.sim.t, pre, self._shown())
        self._kv = {}
        if self.sim._held is None:  # the hole's surfaces and orbits of the new metric (at the start: after the header)
            self.after_header()
        if not moving:
            return None
        self.model.append(f"a/M {a0:.4g} → {a:.4g}, Q/M {q0:.4g} → {q:.4g} при t = {self.sim.t:.6g} с")
        self.sim.emit({"type": "approx", "t": self.sim.t, "approximations": self._approx()})
        nums = ""
        if out["bodies"]:
            bmax = max(out["bodies"], key=lambda b: abs(b["E_new"] - b["E"]) / max(abs(b["E"]), 1e-300))
            lab = objs[bmax["key"]]["label"] if bmax["key"] in objs else bmax["key"]
            gmax = max(out["bodies"], key=lambda b: b["gamma"] if not b["photon"] else 0.0)
            nums = (f"; энергия E сильнее всего изменилась у «{lab}»: {bmax['E']:.6g} → {bmax['E_new']:.6g}; длина "
                    f"окружности через тела при тех же r, θ изменилась до {100 * out['max_dvarpi']:.3g} %")
            if not gmax["photon"]:
                nums += f"; наибольший γ по ZAMO {gmax['gamma']:.4g} сохранён (ограничения скорости нет)"
        return (f"МОДЕЛЬ «что если» (lfphys.theories.alternatives.kn_change_whatif): спин {a0:.4g} → {a:.4g}, заряд "
                f"{q0:.4g} → {q:.4g} — у смены метрики под движущимися телами нет установленной динамики; каждое тело "
                f"сохранило координаты Бойера–Линдквиста (r, θ, φ) — в другой метрике это не то же физическое место, "
                f"правило зависит от координат —, собственное время и импульс, измеренный местным наблюдателем без "
                f"момента (ZAMO; свет — направление и частоту); E, L и постоянная Картера пересчитаны в новой метрике, "
                f"их проверка — заново{nums}; горизонт r₊ = {r_plus:.5g} G M/c², ISCO {self.r_isco:.5g}")

    def _rescale_mass(self, M):
        T0, T1 = self.T, M * K.GM_SUN / K.C ** 3
        km0 = self.gm / K.C ** 2 / 1e3
        if self.geo.n or self.obs:
            self._sync()
        tm = self.t_m()
        pre = self._shown()
        for oid in list(self.obs):
            ov = self.sim.objects[oid]["values"]
            tau_o, ph_o = self._obs_now(oid, ov, tm)
            self.obs[oid] = (tm, tau_o * T0 / T1, ph_o)
        self.geo.rescale_proper_time(T0 / T1)
        self.clk.rescale(self.sim.t, T1)
        self.peri = {}  # a period measured in the old seconds per M is not the new one's (review LB1-physics P10)
        for o in self.sim.objects.values():  # the throw limit in the new seconds (review LB1-p02-ux X4)
            if o["type"] == "body":
                o["values"] = {**o["values"], "tv_max": THROW_C / T1}
        M0 = self.M
        self.M, self.gm, self.T = M, M * K.GM_SUN, T1
        self.sim.speed_range = self.speed_range = (1e-3 * T1, 1e5 * T1)
        self.trail_kink(self.sim.t, pre, self._shown())
        return (f"масса дыры {M0:.6g} → {M:.6g} M☉ — смена масштаба (G = c = M = 1): тела в единицах M на прежних местах и "
                f"с прежними скоростями; G M/c² = {km0:.6g} → {self.gm / K.C ** 2 / 1e3:.6g} км, G M/c³ = "
                f"{T0 * 1e6:.6g} → {T1 * 1e6:.6g} мкс; собственное время тел и часы наблюдателей в секундах сохранены; "
                f"движение в секундах мира теперь в {T1 / T0:.4g} раза медленнее (скорость показа — прежняя)")

    def _approx(self):
        out = ["пробные тела и свет: без собственного поля и заряда (дыра — неизменный фон)"]
        if self.model:
            out.append("МОДЕЛЬ «что если» (не установленная физика; lfphys.theories.alternatives.kn_change_whatif): "
                       "метрика дыры менялась под движущимися телами — " + "; ".join(self.model)
                       + "; тела сохраняли координаты Бойера–Линдквиста (правило зависит от координат), собственное "
                         "время и импульс, измеренный ZAMO (свет — направление и частоту)")
        return out

    def _vel(self, rows):
        """Drawing-coordinate velocities (per G M/c^3) of the rows: dy/dt of the geodesic equations
        (``kerr_newman.rhs_mino`` on the bodies' state) through the map x + i y = sqrt(r^2 + a^2) sin(theta) e^{i phi},
        z = r cos(theta)."""
        g, a = self.geo, self.a
        if not len(rows):
            return np.zeros((0, 3))
        bl, pm, tau = g.bl()[rows], g.momenta()[rows], g.proper_time()[rows]
        y = np.column_stack([bl[:, 0], bl[:, 1], bl[:, 2], pm[:, 1], pm[:, 2], tau])
        d, Tl = KN.rhs_mino(y, -pm[:, 0], pm[:, 3], np.where(g.is_photon()[rows], 0.0, 1.0), a, self.q)
        yd = d / Tl[:, None]
        r, th, ph = bl[:, 0], bl[:, 1], bl[:, 2]
        R = np.sqrt(r * r + a * a)
        dR = r * yd[:, 0] / R
        st, ct, sp, cp = np.sin(th), np.cos(th), np.sin(ph), np.cos(ph)
        return np.column_stack([dR * st * cp + R * ct * yd[:, 1] * cp - R * st * sp * yd[:, 2],
                                dR * st * sp + R * ct * yd[:, 1] * sp + R * st * cp * yd[:, 2],
                                yd[:, 0] * ct - r * st * yd[:, 1]])

    def _feed(self, force=False):
        """The moving bodies' points now, to the trails; the turn since the last point sets the next sub-step."""
        g = self.geo
        st = g.status()
        rows = [i for i in range(g.n) if st[i] == "active"]
        keys = [g.keys[i] for i in rows]
        X = g.cartesian()[rows] if rows else np.zeros((0, 3))
        V = self._vel(rows)
        self.trail_feed(self.clk.sec(g.t), keys, X, V / self.T, force=force)
        turn = max((float(_turns(self._kv[k][None], V[i][None])[0]) for i, k in enumerate(keys) if k in self._kv),
                   default=0.0)
        self._kv = {k: V[i] for i, k in enumerate(keys)}
        return turn

    def _observer_check(self, v):
        r, th = float(v["r"]), math.radians(v["theta"])
        if r <= self.r_plus * (1.0 + 1e-6):
            raise ValueError("наблюдатель под горизонтом")
        if v["kind"] == "static" and not np.isfinite(KN.static_clock_rate(r, th, self.a, self.q)):
            raise ValueError("внутри эргосферы неподвижным быть нельзя: всё увлекается вращением дыры")
        if v["kind"] == "circular":
            if abs(v["theta"] - 90.0) > 1e-9:
                raise ValueError("круговая орбита — только в экваторе (θ = 90°)")
            if r < self.r_isco:  # review B6-G19: not integrated, it would stay on an unstable orbit for ever
                raise ValueError(f"внутри ISCO (r < {self.r_isco:.5g} G M/c²) круговая орбита неустойчива: свободно "
                                 "падающий наблюдатель на ней не удержится (пробное тело там можно запустить и "
                                 "посмотреть, как оно уходит с неё)")

    def _rate(self, v):
        """dtau/dt of an observer (constant: each kind is stationary)."""
        r, th = float(v["r"]), math.radians(v["theta"])
        if v["kind"] == "static":
            return float(KN.static_clock_rate(r, th, self.a, self.q))
        if v["kind"] == "zamo":
            return float(KN.zamo(r, th, self.a, self.q)["alpha"])
        return float(KN.circular_orbit(r, self.a, self.q, True)["dtau_dt"])

    def _omega(self, v):
        """dphi/dt of an observer: a ZAMO is dragged at omega, a circular orbit goes at Omega, a static one stays."""
        r, th = float(v["r"]), math.radians(v["theta"])
        if v["kind"] == "zamo":
            return float(KN.zamo(r, th, self.a, self.q)["omega"])
        if v["kind"] == "circular":
            return float(KN.circular_orbit(r, self.a, self.q, True)["Omega"])
        return 0.0

    def _obs_now(self, oid, v, t_m):
        """(clock reading, phi) of an observer at time t_m, from its placement (t0, tau0, phi0)."""
        t0, tau0, ph0 = self.obs[oid]
        return tau0 + self._rate(v) * (t_m - t0), ph0 + self._omega(v) * (t_m - t0)

    def _obs_xyz(self, oid, v, t_m):
        """An observer's drawn position at time t (a ZAMO and a circular orbit go around)."""
        ph = self._obs_now(oid, v, t_m)[1]
        return np.array(KN.cartesian(float(v["r"]), math.radians(v["theta"]), ph, self.a), float)

    def on_remove(self, obj):
        if obj["type"] == "observer":
            self.obs.pop(obj["id"], None)
        elif obj["id"] in self.geo.keys:
            self._sync()
            self.geo.remove(obj["id"])
            self._feed()
            self._trail_drop(obj["id"])
            self.emit_trails()
            self.emit_trails(full=True)  # the views drop its trail

    def on_set(self, obj, old):
        if obj["type"] == "kn_hole":
            text = self.set_hole(obj, old)
            if text:
                self.sim.emit({"type": "event", "kind": "scene", "t": self.sim.t, "notify": True, "text": text})
            return
        if any(obj["values"].get(c) != old.get(c) for c in ("x", "y", "z")):  # a drag (P16.2)
            self._bl_from_xyz(obj)
        elif any(obj["values"].get(c) != old.get(c) for c in ("r", "theta", "phi")):
            self._xyz_from_bl(obj)
        if obj["type"] == "body" and any(obj["values"].get(c) != old.get(c) for c in ("tvx", "tvy", "tvz")):
            vz = self._zamo_of_throw(obj)  # a throw: the ZAMO-measured velocity of the drawn one
            obj["values"] = {**obj["values"], "vmode": "zamo", "v_r": float(vz[0]), "v_theta": float(vz[1]),
                             "v_phi": float(vz[2])}
        v = obj["values"]
        if obj["type"] == "observer":
            self._observer_check(v)
            # the clock goes on from its reading, at the new place's rate; the observer keeps its present azimuth
            # unless the azimuth itself was changed
            tau, ph = self._obs_now(obj["id"], old, self.t_m())
            if v["phi"] != old.get("phi"):
                ph = math.radians(v["phi"])
            self.obs[obj["id"]] = (self.t_m(), tau, ph)
            return
        # a body or a ray is placed again with its new set-up at the current moment, only when a parameter of its
        # start changed (review B6-G13: a colour restarted it)
        if not any(v.get(k) != old.get(k) for k in self.START[obj["type"]]):
            return
        self._sync()
        self._feed()
        snap = self.geo.state_dict()
        self.trail_break(obj["id"])  # it starts anew here
        if obj["id"] in self.geo.keys:
            self.geo.remove(obj["id"])
        try:
            self.on_add(obj, None)
        except Exception:
            self.geo = KN.Geodesics.from_state_dict(snap)  # refused: every body goes on exactly as it was
            raise

    def object_state(self, obj):
        if obj["type"] == "kn_hole":
            return None
        if obj["type"] == "observer":
            if obj["id"] not in self.obs:
                return None
            tau, ph = self._obs_now(obj["id"], obj["values"], self.t_m())
            return {"tau": tau, "phi": ph, "M": self.M}
        if obj["id"] in self.geo.keys:
            i = self.geo.keys.index(obj["id"])
            y = self.geo.bl()[i]
            c = self.geo.constants()
            return {"r": float(y[0]), "theta": float(y[1]), "phi": float(y[2]), "p": self.geo.momenta()[i].tolist(),
                    "mu2": 0.0 if self.geo.is_photon()[i] else 1.0, "tau": float(self.geo.proper_time()[i]),
                    "status": self.geo.status()[i], "K0": float(c["K0"][i]),
                    "budget": [float(c["budget_K"][i]), float(c["budget_mu2"][i])],
                    "chi": self.a, "q": self.q, "M": self.M}  # the metric and the unit it is in (review LB1-F5)
        return None

    def _xyz(self, key):
        i = self.geo.keys.index(key)
        return np.array(self.geo.cartesian()[i], float)

    def _events(self, events):
        objs = self.sim.objects
        for e in events:
            lab = objs[e["key"]]["label"] if e["key"] in objs else e["key"]
            if e["kind"] == "captured":
                extra = f"; по своим часам — τ = {e['tau_horizon']:.6g} G M/c³" if "tau_horizon" in e else ""
                self.sim.emit({"type": "event", "kind": "captured", "t": self.clk.sec(e["t"]),
                               "text": f"«{lab}» пересёк горизонт: для далёкого наблюдателя — никогда, движение "
                                       f"остановлено у r₊ + 10⁻⁴{extra}"})
            elif e["kind"] == "escaped":
                self.sim.emit({"type": "event", "kind": "escaped", "t": self.clk.sec(e["t"]),
                               "text": f"«{lab}» ушёл на r = {e['r']:.4g} G M/c²: дальше не прослеживается"})

    def max_step(self):
        """A few sub-steps per call: the runner keeps its frame budget."""
        return 4.0 * self.sub * self.T

    def advance(self, t_target):
        """Sub-steps of at most ``sub`` (review UX-ui U2): after each, every moving body's point goes to its trail, and
        the largest turn of a direction of motion in it sets the next (CAND_TURN, growing at most twice)."""
        t1 = self.clk.geo(t_target)
        while self.geo.t < t1:
            h = min(self.sub, t1 - self.geo.t)
            g = self.geo
            ta, pa = g.t, dict(zip(g.keys, g.momenta()[:, 1]))
            self._events(g.advance(g.t + h))
            for k, pr in zip(g.keys, g.momenta()[:, 1]):  # a periapsis: p_r from - to + (the radial period, P16.3)
                p0 = pa.get(k)
                if p0 is not None and p0 < 0.0 <= pr:
                    tc = ta + (g.t - ta) * (-p0) / (pr - p0)
                    self.peri[k] = (self.peri.get(k, ()) + (self.clk.sec(tc),))[-2:]
            turn = self._feed()
            if h >= self.sub * (1.0 - 1e-12):  # a whole sub-step: measure the next
                self.sub = min(max(0.9 * h * CAND_TURN / turn if turn > 0 else 2.0 * h, 0.25 * h), 2.0 * h, SUB_MAX)

    def _trail_rgb(self, ids):
        objs = self.sim.objects
        return [[1.0, 0.83, 0.23] if k in objs and objs[k]["type"] == "light"
                else _rgb(objs[k]["values"].get("color", "#e9ecef")) if k in objs else [0.6, 0.6, 0.6] for k in ids]

    def frame(self):
        g, objs = self.geo, self.sim.objects
        keys, st = g.keys, g.status()
        show = [i for i in range(len(keys)) if st[i] == "active"]
        X = g.cartesian()[show] if keys else np.zeros((0, 3))
        ids = [keys[i] for i in show]
        rgb = [[1.0, 0.83, 0.23] if objs.get(k, {}).get("type") == "light"
               else _rgb(objs[k]["values"].get("color", "#e9ecef")) if k in objs else [0.7, 0.7, 0.7] for k in ids]
        rad = [0.12 if objs.get(k, {}).get("type") == "light" else 0.25 for k in ids]
        now, probes = {}, {}
        c = g.constants() if keys else None
        tau = g.proper_time() if keys else None
        bl = g.bl() if keys else None
        for i, k in enumerate(keys):
            now[k] = {"r, G M/c²": float(bl[i, 0]), "θ, °": math.degrees(float(bl[i, 1])),
                      "состояние": {"active": "движется", "captured": "у горизонта (захвачено)",
                                    "escaped": "ушло далеко"}[st[i]],
                      "E (на единицу массы)": float(c["E"][i]), "L, G M/c": float(c["L"][i]),
                      "K (постоянная Картера)": float(c["K"][i])}
            if not g.is_photon()[i]:
                now[k]["собственное время τ, с"] = float(tau[i]) * self.T
        tm = self.t_m()
        for o in objs.values():
            if o["type"] != "observer":
                continue
            v = o["values"]
            rate = self._rate(v)
            reading = self._obs_now(o["id"], v, tm)[0]
            probes[o["id"]] = {"часы наблюдателя τ, с": reading * self.T, "часы далёкого t, с": self.sim.t,
                               "ход dτ/dt": rate}
            ids.append(o["id"])
            xo = self._obs_xyz(o["id"], v, tm)[None]
            X = np.vstack([X, xo]) if len(X) else xo
            rgb.append([0.3, 0.67, 0.97])
            rad.append(0.3)
        # the scene grows with the bodies and observers, not with light: a ray that leaves runs out of the frame,
        # otherwise the hole would shrink to a point as soon as the first ray escapes
        grow = [j for j, k in enumerate(ids) if objs.get(k, {}).get("type") != "light"]
        if grow:
            ext = float(np.max(np.abs(np.asarray(X)[grow]))) * 1.15
            if math.isfinite(ext) and ext > self.box_h:
                self.box_h = min(2.0 ** math.ceil(math.log2(ext)), 4096.0)
                self.sim.emit({"type": "box", "t": self.sim.t, "box": self._box()})
        Vb = self._vel(show) / self.T
        vel = np.zeros((len(ids), 3), np.float32)
        vel[:len(show)] = Vb
        at = {k: [float(u) for u in xyz] for k, xyz in zip(keys, g.cartesian()) if k in objs} if keys else {}
        at.update({ids[j]: [float(u) for u in X[j]] for j in range(len(show), len(ids))})
        if self.hole_id is not None:
            at[self.hole_id] = [0.0, 0.0, 0.0]
        meas, notes = self.measure_now()
        return ({"ids": ids, "trail_ids": [keys[i] for i in show] + [None] * (len(ids) - len(show)), "now": now,
                 "probes": probes, "at": at, "meas": meas, **({"meas_note": notes} if notes else {})},
                {"pos": np.asarray(X, np.float32).reshape(-1), "rad": np.array(rad, np.float32),
                 "rgb": np.array(rgb, np.float32).reshape(-1), "vel": vel.reshape(-1)})

    def _box(self):
        h = self.box_h
        return [[-h, -h, -h], [h, h, h]]

    # --- measurables (P16.3) -----------------------------------------------------------------------------------------
    def measurables(self):
        out = [{"id": "dK", "label": "Наибольший уход постоянной Картера K у тел (доля K)", "unit": "", "of": None,
                "group": "Сохранение"},
               {"id": "dmu2", "label": "Наибольшее отклонение массовой оболочки p·p = −μ²", "unit": "", "of": None,
                "group": "Сохранение"}]
        for o in self.sim.objects.values():
            oid, lab, t = o["id"], o["label"], o["type"]
            if t in ("body", "light"):
                out += [{"id": f"{oid}.r", "label": f"«{lab}»: расстояние до дыры r (Бойер–Линдквист)", "unit": "G M/c²",
                         "of": oid, "group": "Тела"},
                        {"id": f"{oid}.r_km", "label": f"«{lab}»: расстояние до дыры r", "unit": "км", "of": oid,
                         "group": "Тела"}]
            if t == "body":
                out += [{"id": f"{oid}.speed", "label": f"«{lab}»: скорость, измеренная местным наблюдателем (ZAMO)",
                         "unit": "доля c", "of": oid, "group": "Тела"},
                        {"id": f"{oid}.E", "label": f"«{lab}»: энергия E на единицу массы", "unit": "", "of": oid,
                         "group": "Сохранение"},
                        {"id": f"{oid}.L", "label": f"«{lab}»: момент импульса L на единицу массы", "unit": "G M/c",
                         "of": oid, "group": "Сохранение"},
                        {"id": f"{oid}.a", "label": f"«{lab}»: полуось (r_p + r_a)/2 по точкам поворота", "unit": "G M/c²",
                         "of": oid, "group": "Орбиты"},
                        {"id": f"{oid}.e", "label": f"«{lab}»: эксцентриситет (r_a − r_p)/(r_a + r_p)", "unit": "",
                         "of": oid, "group": "Орбиты"},
                        {"id": f"{oid}.Tr", "label": f"«{lab}»: радиальный период (между перицентрами, измерен)",
                         "unit": "с", "of": oid, "group": "Орбиты"}]
            elif t == "observer":
                out += [{"id": f"{oid}.tau", "label": f"«{lab}»: показание часов", "unit": "с", "of": oid,
                         "group": "Часы"},
                        {"id": f"{oid}.rate", "label": f"«{lab}»: ход часов dτ/dt", "unit": "", "of": oid,
                         "group": "Часы"}]
        return out

    def _turning_points(self, r, E, L, K):
        """The radial turning points (r_p, r_a) around r of a bound timelike geodesic: the roots of R(r) = P^2 -
        Delta (K + r^2) (P = (r^2 + a^2) E - a L; ``_shell``: Delta p_r^2 = R / Delta) on either side of r; None when
        the motion is not bound (E >= 1 or no root beyond r)."""
        a, q = self.a, self.q
        if not E < 1.0:
            return None
        b = a * a * E - a * L
        coef = [E * E - 1.0, 2.0, 2.0 * E * b - (a * a + q * q) - K, 2.0 * K, b * b - K * (a * a + q * q)]
        roots = np.roots(coef)
        re = np.sort(roots[np.abs(roots.imag) < 1e-9 * np.maximum(1.0, np.abs(roots.real))].real)
        tol = 1e-9 * r
        for lo, hi in zip(re[:-1], re[1:]):  # the band of R >= 0 that holds r (r may be a turning point itself)
            mid = 0.5 * (lo + hi)
            if lo - tol <= r <= hi + tol and np.polyval(coef, mid) > 0.0 and lo > self.r_plus:
                return float(lo), float(hi)
        return None

    def measure_now(self):
        g, objs = self.geo, self.sim.objects
        m, notes = {}, {}
        nan = float("nan")
        c = g.constants() if g.n else None
        if g.n:
            sK = np.maximum(np.abs(c["K"] - c["dK"]), 1.0)
            m["dK"], m["dmu2"] = float(np.max(np.abs(c["dK"]) / sK)), float(np.max(np.abs(c["dmu2"])))
        else:
            m["dK"] = m["dmu2"] = nan
            notes["dK"] = notes["dmu2"] = "нет тел"
        bl = g.bl() if g.n else None
        vz = g.zamo_velocity() if g.n else None
        km = self.gm / K.C ** 2 / 1e3
        for o in objs.values():
            oid, t = o["id"], o["type"]
            if t == "observer" and oid in self.obs:
                m[f"{oid}.tau"] = self._obs_now(oid, o["values"], self.t_m())[0] * self.T
                m[f"{oid}.rate"] = self._rate(o["values"])
                continue
            if t not in ("body", "light"):
                continue
            if oid not in g.keys:
                continue
            i = g.keys.index(oid)
            m[f"{oid}.r"], m[f"{oid}.r_km"] = float(bl[i, 0]), float(bl[i, 0]) * km
            if t != "body":
                continue
            m[f"{oid}.speed"] = float(np.linalg.norm(vz[i]))
            m[f"{oid}.E"], m[f"{oid}.L"] = float(c["E"][i]), float(c["L"][i])
            tp = self._turning_points(float(bl[i, 0]), float(c["E"][i]), float(c["L"][i]), float(c["K"][i]))
            if tp is None:
                m[f"{oid}.a"] = m[f"{oid}.e"] = nan
                notes[f"{oid}.a"] = notes[f"{oid}.e"] = "движение не связанное (E ≥ 1 или нет второй точки поворота)"
            else:
                m[f"{oid}.a"], m[f"{oid}.e"] = 0.5 * (tp[0] + tp[1]), (tp[1] - tp[0]) / (tp[1] + tp[0])
            pp = self.peri.get(oid, ())
            if len(pp) == 2:
                m[f"{oid}.Tr"] = pp[1] - pp[0]
            else:
                m[f"{oid}.Tr"] = nan
                notes[f"{oid}.Tr"] = ("нужны два прохождения перицентра (знак p_r с − на +) при одной и той же дыре: "
                                      "после смены её массы, спина или заряда период измеряется заново")
        return m, notes

    def checks(self):
        """Carter's K and the mass shell of every body against its own drift budget (review B6-G7): the most the
        accepted steps' allowed local errors can have changed them (``kerr_newman`` sums sqrt(6) rtol |grad| . scale
        over each body's steps: linear in the steps, growing as 1/Delta near the horizon) plus the rounding of their
        evaluation (16 u of their terms). Every body, also after its capture or escape (its last steps count)."""
        g = self.geo
        if not g.n:
            return
        c = g.constants()
        u = 2.0 ** -53
        bK = c["budget_K"] + 16.0 * u * np.abs(c["K"])
        bm = c["budget_mu2"] + 16.0 * u * c["shell_scale"]
        rK, rm = np.abs(c["dK"]) / bK, np.abs(c["dmu2"]) / bm
        i, j = int(np.argmax(rK)), int(np.argmax(rm))
        sK = max(abs(float(c["K"][i] - c["dK"][i])), 1.0)
        self.sim.running_check("carter", "Постоянная Картера K каждого тела (сохраняется)", float(abs(c["dK"][i])) / sK,
                               0.0, tol=float(bK[i]) / sK, ok=bool(np.all(rK <= 1.0)),
                               note=f"отн. изменение K с начала движения у тела, ближайшего к своему пределу "
                                    f"({g.keys[i]}, {int(c['steps'][i])} шагов); предел — сумма по его шагам "
                                    f"допустимых локальных ошибок DOP853 (rtol = {g.rtol:g}), пересчитанных в K: "
                                    f"√6·rtol·Σ|∂K/∂yₖ|·масштабₖ, плюс округление; E и L сохраняются точно (t и φ — "
                                    f"циклические координаты)")
        self.sim.running_check("shell", "Массовая оболочка p·p = −μ² (сохраняется)", float(abs(c["dmu2"][j])), 0.0,
                               tol=float(bm[j]), ok=bool(np.all(rm <= 1.0)),
                               note=f"отклонение μ² от 1 (тела) или 0 (свет) у тела, ближайшего к своему пределу "
                                    f"({g.keys[j]}); предел — как у K, по градиенту μ²: у горизонта он растёт как "
                                    f"1/Δ вместе с членами P²/Δ")

    def header(self):
        a, q = self.a, self.q
        rp, rm = KN.horizons(a, q)
        return {"title": "Плейграунд: тела и свет у чёрной дыры Керра–Ньюмена (её масса, спин и заряд — в инспекторе "
                         "дыры)",
                "approximations": self._approx(),
                "hole": {"r_plus": rp, "r_minus": rm},
                "scene3d": {"box": self._box(), "units": "G M/c²", "objects": [], "layers": [],
                            "planes": {"max": 0, "center": [0, 0, 0], "defaults": {}}, "up": [0.0, 0.0, 1.0],
                            "views": [["iso", "Изо", "Изометрия (F)", [0.55, -0.7, 0.45]],
                                      ["pole", "С полюса", "Вдоль оси вращения", [0.0, 0.0, 1.0]],
                                      ["side", "С ребра", "Экватор с ребра", [0.0, -1.0, 0.0]]]},
                "units": {"t": "с", "x": f"G M/c² = {self.gm / K.C ** 2:.4g} м"}}

    def after_header(self):
        """The hole: horizon, ergosurface, the equatorial photon orbits and the ISCO, from the metric."""
        a, q, sim = self.a, self.q, self.sim
        for mid, r_of, rgb, op, label in (
                ("horizon", lambda T: np.full_like(T, self.r_plus), (12, 12, 16), 1.0,
                 f"Горизонт r₊ = {self.r_plus:.6g} G M/c²"),
                ("ergo", lambda T: KN.ergosurface(T, a, q), (120, 90, 200), 0.18,
                 "Эргосфера (внутри неё ничто не может покоиться)")):
            X, Y, Z = KN.surface(r_of, a, 33, 64)
            pos = np.stack([X, Y, Z], -1).reshape(-1, 3).astype(np.float32)
            nt, npn = X.shape
            idx = []
            for i in range(nt - 1):
                for j in range(npn - 1):
                    a_, b_ = i * npn + j, i * npn + j + 1
                    idx += [a_, a_ + npn, b_, b_, a_ + npn, b_ + npn]
            sim.emit({"type": "mesh", "t": sim.t, "id": mid, "count": int(len(pos)), "opacity": op, "label": label},
                     {"pos": pos, "idx": np.array(idx, np.uint32), "rgb": np.tile(np.array([rgb], np.uint8), (len(pos), 1))})
        ph = np.linspace(0.0, 2.0 * math.pi, 181)
        pts, col = [], []
        for r, c in ((KN.photon_orbit(a, q, True), (1.0, 0.85, 0.35)), (KN.photon_orbit(a, q, False), (1.0, 0.6, 0.2)),
                     (KN.isco(a, q, True), (0.5, 0.9, 0.6))):
            x, y, z = KN.cartesian(np.full_like(ph, r), np.full_like(ph, math.pi / 2), ph, a)
            pts.append(np.stack([x, y, z], -1)); col.append(np.tile(c, (len(ph), 1)))
            pts.append(np.full((1, 3), np.nan)); col.append(np.zeros((1, 3)))
        sim.emit({"type": "lines", "t": sim.t, "id": "orbits",
                  "label": "Круговые орбиты в экваторе: фотонные (по и против вращения) и ISCO (по вращению)"},
                 {"pts": np.concatenate(pts).astype(np.float32).reshape(-1),
                  "rgb": np.concatenate(col).astype(np.float32).reshape(-1)})

    def engine_modules(self):
        # the «what if» of the hole's spin and charge is the engine's declared alternative (review LB1-physics P5): listed
        # with the world, since the hole's inspector offers it at any moment (the panel is sent with the header)
        return ["core.gravity.kerr_newman", "theories.alternatives.kn_change_whatif"]


# --- the post-Newtonian binary ----------------------------------------------------------------------------------
BINARY = Schema([
    _p("q", "Отношение масс m₂/m₁", "float", 1.0, min=0.05, max=1.0),
    _p("r0", "Начальное расстояние, G m/c²", "float", 20.0, min=8.0, max=2000.0, log=True,
       help="Гармонические координаты; с полными уравнениями — дальше границы, где их реакция излучения ещё "
            "упорядоченный ряд (≈ 10,6 G m/c² при q = 1 … 13 при q = 0,05)"),
    _p("start", "Начальная орбита", "select", "quasi", options=[
        ("quasi", "квазикруговая (радиальная скорость адиабатического сближения)"),
        ("ellipse", "эллиптическая: перицентр r₀, эксцентриситет e (ньютоновские элементы)")]),
    _p("e", "Эксцентриситет e", "float", 0.3, min=0.0, max=0.9, show_if={"start": ["ellipse"]}),
    _p("orders", "Порядки уравнений", "select", "all", options=[
        ("all", "1ПН + 2ПН + реакция излучения 2,5ПН и 3,5ПН"), ("rr", "Ньютон + реакция излучения 2,5ПН"),
        ("cons", "1ПН + 2ПН без излучения (сохраняется энергия)")]),
    _p("r_stop", "Остановить при расстоянии, G m/c²", "float", 6.0, min=2.5, max=50.0,
       help="Ближе постньютоновское приближение кончается: слияние им не описывается. Полные уравнения "
            "останавливаются не ближе границы, где их реакция излучения перестаёт быть упорядоченным рядом "
            "(≈ 10,6–13 G m/c², считается при старте двойной)"),
    _p("m_total", "Полная масса m, M☉", "float", 20.0, min=0.1, max=1e10, log=True,
       help="Меняется в текущий момент как смена масштаба (G = c = m = 1): двойная продолжает ту же орбиту в единицах "
            "m, метры, секунды, частота волн и их амплитуда у детектора пересчитываются; другие параметры начинают "
            "двойную заново"),
])
DETECTOR = Schema([
    _p("distance", "Расстояние до источника, Мпк", "float", 400.0, min=1e-6, max=1e5, log=True),
    _p("iota", "Наклон орбиты к лучу зрения ι, °", "float", 30.0, min=0.0, max=180.0),
    _p("phi", "Азимут Φ, °", "float", 0.0, min=0.0, max=360.0),
])
ORDERS = {"all": (1, 2, 2.5, 3.5), "rr": (2.5,), "cons": (1, 2)}
ALL_ORDERS = ORDERS["all"]


# the ordering of the reaction series (review B6-G1) lives in the engine (``pn_binary``): used here by these names
flux_c1 = PN.flux_c1
reaction_on_circle = PN.reaction_on_circle
reaction_limit = PN.reaction_validity_radius


class PNMode(Trails):
    default_speed = 1.0
    speed_range = (1e-6, 1e6)

    def __init__(self, sim):
        self.sim = sim
        p = sim.params
        self.m = float(p["m_total"])  # M_sun: the binary's mass (its object's, P16.1); the world's for a new binary
        self.gm = self.m * K.GM_SUN  # m^3 s^-2
        self.T = self.gm / K.C ** 3  # s per unit of time
        self.L = self.gm / K.C ** 2  # m per unit of length
        self.clk = Clock(self.T)     # the world's seconds <-> t in units of m (a change of m rescales the seconds)
        self.bin = None  # {"id", "st", "nu", "orders", "status", "E0", "E_rad", "r_stop", "trail": [...]}
        self.default_speed = 200.0 * self.T  # an orbit at r = 20 G m/c^2 in about 3 s
        self.speed_range = (1e-2 * self.T, 1e6 * self.T)
        self._trails_init()

    def palette(self):
        sch = Schema([q if q.id != "m_total" else Param(**{**q.__dict__, "default": float(self.sim.params["m_total"])})
                      for q in BINARY.params])
        return {"binary": ObjectType("binary", "Двойная (две компактные массы)", "body", sch, limit=1,
                                     color="#f08c00",
                                     help="Две массы на постньютоновской орбите; изменение параметров (кроме массы) "
                                          "начинает двойную заново с текущего момента; масса — смена масштаба"),
                "detector": ObjectType("detector", "Детектор волн", "probe", DETECTOR, limit=4, color="#1c7ed6",
                                       help="Наблюдатель на расстоянии R под наклоном ι: h₊, h× по квадрупольной формуле")}

    def _start(self, obj, state=None):
        v = obj["values"]
        if float(v["m_total"]) != self.m:  # the binary's own mass sets the units (G = c = m = 1)
            self._units(float(v["m_total"]))
        q = float(v["q"])
        nu = q / (1.0 + q) ** 2
        o = ORDERS[v["orders"]]
        t = self.clk.geo(self.sim.t)
        # the full equations stop where their radiation reaction stops being an ordered series (review B6-G1: below
        # r ~ 9.1 it changes sign and the default binary flew apart instead of reaching r_stop = 6)
        r_rr = reaction_limit(nu) if o == ALL_ORDERS else 0.0
        r_eff = max(float(v["r_stop"]), r_rr)
        stopped = bool(state) and state.get("status") == "stopped"
        if state:
            st = PN.state(t, state["x"], state["v"])
        elif v["start"] == "quasi":
            st = PN.circular_state(float(v["r0"]), nu, o, t=t, quasi=2.5 in o)
        else:
            e = float(v["e"])
            a = float(v["r0"]) / (1.0 - e)  # periapsis r0
            st = PN.periapsis_state(a, e, t)
        r0 = float(np.linalg.norm(st["x"]))
        if not stopped and r0 <= r_eff:
            if r_rr > float(v["r_stop"]):
                raise ValueError(f"начальное расстояние не больше {r_rr:.4g} G m/c²: ближе реакция излучения полных "
                                 f"уравнений (2,5ПН + 3,5ПН) уже не упорядоченный ряд, а у r ≈ 9,1 она меняет знак — "
                                 f"начните дальше или выберите порядки «Ньютон + 2,5ПН»")
            raise ValueError(f"начальное расстояние не больше «остановить при» ({v['r_stop']} G m/c²)")
        xx = (float(np.linalg.norm(np.cross(st["x"], st["v"]))) / (r0 * r0)) ** (2.0 / 3.0)
        self.bin = {"id": obj["id"], "st": st, "nu": nu, "orders": o, "status": "stopped" if stopped else "running",
                    "circular": v["start"] == "quasi", "E0": self._energy(st, nu, o), "E_rad": 0.0, "E_rad1": 0.0,
                    "r_stop": r_eff, "r_rr": r_rr, "r_stop_set": float(v["r_stop"]), "x_max": xx,
                    "phase": float((state or {}).get("phase", math.atan2(st["x"][1], st["x"][0])))}
        self._trails_init()
        self.emit_trails(full=True)  # a new binary: the views drop the previous one's trails
        self._trail_append(st["t"], st["x"], st["v"])
        self.sim.emit({"type": "box", "t": self.sim.t, "box": self._box(r0)})
        if r_rr > float(v["r_stop"]):
            self.sim.emit({"type": "notice", "t": self.sim.t,
                           "text": f"Полные уравнения (ν = {nu:.4g}) будут остановлены у r = {r_rr:.4g} G m/c²: ближе их "
                                   f"реакция излучения уже не упорядоченный ряд (см. README p01)"})

    @staticmethod
    def _energy(st, nu, orders):
        """E/mu of the orders' conservative part: 2PN with 1PN and 2PN in the equations, Newtonian without."""
        return float(PN.energy(st["x"], st["v"], nu, order=2 if 2 in orders else 1 if 1 in orders else 0))

    @staticmethod
    def _box(r):
        h = 0.65 * r
        return [[-h, -h, -0.25 * h], [h, h, 0.25 * h]]

    def on_add(self, obj, state):
        if obj["type"] == "binary":
            self._start(obj, state)

    def place(self, kind, values):
        values.pop("position", None)  # the binary sits at the centre of mass; a detector is far away
        return values

    def palette_state(self):
        return {}

    def on_remove(self, obj):
        if obj["type"] == "binary":
            self.bin = None
            self._trails_init()
            self.emit_trails(full=True)  # the views drop its trails

    def on_set(self, obj, old):
        if obj["type"] == "binary":
            changed = {k for k, v in obj["values"].items() if v != old.get(k)}
            if changed == {"m_total"} and self.bin is not None:  # the mass alone: a change of units, the orbit goes on
                text = self._units(float(obj["values"]["m_total"]))
                self.sim.emit({"type": "event", "kind": "scene", "t": self.sim.t, "notify": True, "text": text})
                return
            self._start(obj)  # the binary starts anew at the current moment with its new parameters

    def _units(self, m):
        """The binary's mass m (M_sun) now: G = c = m = 1, so a change of m is a change of units — the orbit in units of
        m goes on as it is, the geometric clock too (``Clock``); seconds per unit, metres per unit, the waves'
        frequency and their strain at a detector follow m. Returns the event's text."""
        m0, T0, L0 = self.m, self.T, self.L
        if self.bin is not None and self.bin["status"] == "running":
            self.advance(self.sim.t)
        pre = self._shown()
        self.m, self.gm = m, m * K.GM_SUN
        self.T, self.L = self.gm / K.C ** 3, self.gm / K.C ** 2
        self.clk.rescale(self.sim.t, self.T)
        self.default_speed = 200.0 * self.T
        self.sim.speed_range = self.speed_range = (1e-2 * self.T, 1e6 * self.T)
        self.trail_kink(self.sim.t, pre, self._shown())
        return (f"полная масса двойной {m0:.6g} → {m:.6g} M☉ — смена масштаба (G = c = m = 1): орбита в единицах m "
                f"продолжается как была; G m/c² = {L0 / 1e3:.6g} → {self.L / 1e3:.6g} км, G m/c³ = {T0 * 1e6:.6g} → "
                f"{self.T * 1e6:.6g} мкс; частота волн и амплитуда у детекторов пересчитаны (∝ 1/m и ∝ m); движение в "
                f"секундах мира теперь в {self.T / T0:.4g} раза медленнее (скорость показа — прежняя)")

    def _shown(self):
        """(trail keys, both bodies' positions, their velocities per world second) now: the trails' kinks."""
        if self.bin is None or self.bin["status"] != "running":
            return (), np.zeros((0, 3)), np.zeros((0, 3))
        Y, W, _ = self._body_states(np.asarray(self.bin["st"]["x"], float), np.asarray(self.bin["st"]["v"], float))
        oid = self.bin["id"]
        return (f"{oid}#1", f"{oid}#2"), Y, W / self.T

    def object_state(self, obj):
        if obj["type"] == "binary" and self.bin is not None:  # with its status (review B6-G11: a stopped binary)
            return {"x": self.bin["st"]["x"].tolist(), "v": self.bin["st"]["v"].tolist(), "status": self.bin["status"],
                    "phase": self.bin["phase"]}
        return None

    def max_step(self):
        return None

    def advance(self, t_target):
        b = self.bin
        if b is None or b["status"] != "running":
            return
        t1 = self.clk.geo(t_target)
        dt = t1 - b["st"]["t"]
        if dt <= 0.0:
            return
        # the radiated energy over the step from the dense solution of the same integration
        res = PN.integrate(b["st"], t1, b["nu"], b["orders"], n_out=65, r_stop=b["r_stop"])
        X, V = res["x"], res["v"]
        nu, tt = b["nu"], res["t"]
        lum = GW.luminosity(GW.quadrupole(X, V, *GW.newtonian_kinematics(X, V), nu)[2])
        b["E_rad"] += float(np.sum(0.5 * (lum[1:] + lum[:-1]) * np.diff(tt)))
        # the flux of a circular orbit to 1PN in the invariant x = (m Omega)^(2/3) (Blanchet 2014 Eq. 314 without the
        # tail, which local equations of motion do not contain)
        r = np.linalg.norm(X, axis=1)
        xx = (np.linalg.norm(np.cross(X, V), axis=1) / r ** 2) ** (2.0 / 3.0)
        f1 = 32.0 / 5.0 * nu ** 2 * xx ** 5 * (1.0 + flux_c1(nu) * xx)
        b["E_rad1"] += float(np.sum(0.5 * (f1[1:] + f1[:-1]) * np.diff(tt)))
        b["x_max"] = max(b["x_max"], float(np.max(xx)))
        self._trail_points(res, b["st"]["t"], float(res["end"]["t"]))
        b["st"] = res["end"]
        if res["status"] == "r_stop":
            b["status"] = "stopped"
            self._trail_append(b["st"]["t"], b["st"]["x"], b["st"]["v"], force=True)  # the trails end where it stopped
            if b["r_rr"] > b["r_stop_set"]:
                text = (f"Двойная сблизилась до {b['r_stop']:.4g} G m/c²: ближе реакция излучения этих уравнений "
                        f"(2,5ПН + 3,5ПН, гармоническая калибровка) перестаёт быть упорядоченным рядом — отброшенное "
                        f"в ней больше учтённой поправки 1ПН, а у r ≈ 9,1 она меняет знак (орбита набирала бы "
                        f"энергию). Последние витки и слияние постньютоновские уравнения не описывают — движение "
                        f"остановлено")
            else:
                text = (f"Двойная сблизилась до {b['r_stop']:.4g} G m/c²: постньютоновское приближение здесь "
                        f"кончается, слияние им не описывается — движение остановлено")
            self.sim.emit({"type": "event", "kind": "merger", "t": self.clk.sec(b["st"]["t"]), "text": text,
                           "notify": True})

    def _bodies(self):
        b = self.bin
        y1, y2 = PN.body_positions(b["st"]["x"], b["st"]["v"], b["nu"])
        return y1, y2

    def _body_states(self, x, v):
        """Both bodies' positions (G m/c^2) and velocities (per G m/c^3): ``pn_binary.body_positions`` and its time
        derivative along the equations of motion (``pn_binary.directional``, a complex step)."""
        b = self.bin
        a = PN.acceleration(x, v, b["nu"], b["orders"])
        Y = np.stack(PN.body_positions(x, v, b["nu"]))
        W = PN.directional(lambda X, V: np.stack(PN.body_positions(X, V, b["nu"])), x, v, v, a)
        return Y, W, a

    def _trail_append(self, t, x, v, force=False):
        if self.bin is None:
            return
        Y, W, _ = self._body_states(np.asarray(x, float), np.asarray(v, float))
        oid = self.bin["id"]
        self.trail_feed(self.clk.sec(t), (f"{oid}#1", f"{oid}#2"), Y, W / self.T, force=force)

    def _trail_points(self, res, t0, t1):
        """Points of the step's dense solution (``res["at"]``) at most CAND_TURN of the relative velocity's turn (and
        CAND_DSPEED of its speed) apart, to the trails (review UX-ui U2: the trail kept one of the 65 samples)."""
        b = self.bin
        t = t0
        x, v = b["st"]["x"], b["st"]["v"]
        while t < t1:
            a = PN.acceleration(x, v, b["nu"], b["orders"])
            vv = float(v @ v)
            rate = max(float(np.linalg.norm(np.cross(v, a))) / vv, abs(float(v @ a)) / vv * CAND_TURN / CAND_DSPEED,
                       1e-300)
            t = min(t + CAND_TURN / rate, t1)
            xp = x
            x, v = (np.asarray(u, float) for u in res["at"](t))
            # the orbital phase (P16.3): the angle swept between candidates (at most ~10 degrees apart: unambiguous)
            b["phase"] += math.atan2(float(xp[0] * x[1] - xp[1] * x[0]), float(xp @ x))
            self._trail_append(t, x, v)

    def _trail_rgb(self, ids):
        return [[1.0, 0.65, 0.2] if k.endswith("#1") else [0.6, 0.8, 1.0] for k in ids]

    def frame(self):
        sim, b = self.sim, self.bin
        probes, now = {}, {}
        meas, notes = self.measure_now()
        mm = {"meas": meas, **({"meas_note": notes} if notes else {})}
        if b is None:
            return {"ids": [], "probes": probes, "now": now, "at": {}, **mm}, {"pos": np.zeros(0, np.float32)}
        x, v, nu = b["st"]["x"], b["st"]["v"], b["nu"]
        y1, y2 = self._bodies()
        X1 = 0.5 * (1.0 + math.sqrt(max(1.0 - 4.0 * nu, 0.0)))
        r = float(np.linalg.norm(x))
        omega = float(np.linalg.norm(np.cross(x, v))) / r ** 2
        f_gw = 2.0 * omega / (2.0 * math.pi) / self.T
        el = PN.newtonian_elements(x, v)
        now[b["id"]] = {"расстояние r, G m/c²": r, "эксцентриситет (оскулирующий)": float(el["e"]),
                        "частота волн f, Гц": f_gw, "энергия E/μ (2ПН)": float(PN.energy(x, v, nu)),
                        "состояние": "считается" if b["status"] == "running"
                        else f"остановлена у r = {b['r_stop']:.4g} G m/c²"}
        for o in sim.objects.values():
            if o["type"] != "detector":
                continue
            dv = o["values"]
            hp, hx = GW.binary_waveform(x, v, nu, math.radians(dv["iota"]), math.radians(dv["phi"]))
            s = GW.strain_scale(self.gm, float(dv["distance"]) * MPC)
            probes[o["id"]] = {"h₊": float(hp) * s, "h×": float(hx) * s, "f волн, Гц": f_gw}
        pos = np.array([y1, y2], np.float32).reshape(-1)
        rad = np.array([2.0 * X1, 2.0 * (1.0 - X1)], np.float32)  # each body's Schwarzschild radius, G m/c²
        rgb = np.array([[1.0, 0.65, 0.2], [0.6, 0.8, 1.0]], np.float32).reshape(-1)
        W = self._body_states(np.asarray(x, float), np.asarray(v, float))[1] / self.T if b["status"] == "running" \
            else np.zeros((2, 3))
        return {"ids": [b["id"], b["id"]], "trail_ids": [f"{b['id']}#1", f"{b['id']}#2"] if b["status"] == "running" else [None, None], "probes": probes,
                "now": now, "status": b["status"], "at": {b["id"]: [0.0, 0.0, 0.0]}, **mm}, {
                    "pos": pos, "rad": rad, "rgb": rgb, "vel": np.asarray(W, np.float32).reshape(-1)}

    # --- measurables (P16.3) -----------------------------------------------------------------------------------------
    def measurables(self):
        out = []
        for o in self.sim.objects.values():
            oid, lab = o["id"], o["label"]
            if o["type"] == "binary":
                out += [{"id": f"{oid}.r", "label": f"«{lab}»: расстояние между телами r (гармонические координаты)",
                         "unit": "км", "of": oid, "group": "Двойная"},
                        {"id": f"{oid}.r_m", "label": f"«{lab}»: расстояние между телами r", "unit": "G m/c²", "of": oid,
                         "group": "Двойная"},
                        {"id": f"{oid}.phase", "label": f"«{lab}»: орбитальная фаза (накопленная)", "unit": "рад",
                         "of": oid, "group": "Двойная"},
                        {"id": f"{oid}.f", "label": f"«{lab}»: частота волн 2Ω/2π", "unit": "Гц", "of": oid,
                         "group": "Двойная"},
                        {"id": f"{oid}.e", "label": f"«{lab}»: эксцентриситет (оскулирующий, ньютоновский)", "unit": "",
                         "of": oid, "group": "Двойная"},
                        {"id": f"{oid}.E", "label": f"«{lab}»: энергия орбиты E/μ (2ПН)", "unit": "", "of": oid,
                         "group": "Сохранение"},
                        {"id": f"{oid}.dE", "label": f"«{lab}»: потеря энергии с начала (доля |E₀|)", "unit": "",
                         "of": oid, "group": "Сохранение"},
                        {"id": f"{oid}.J", "label": f"«{lab}»: момент импульса орбиты |x × v| на μ (ньютоновский)",
                         "unit": "G m/c", "of": oid, "group": "Сохранение"}]
            elif o["type"] == "detector":
                out += [{"id": f"{oid}.hp", "label": f"«{lab}»: амплитуда h₊ у детектора", "unit": "", "of": oid,
                         "group": "Волны"},
                        {"id": f"{oid}.hx", "label": f"«{lab}»: амплитуда h× у детектора", "unit": "", "of": oid,
                         "group": "Волны"}]
        return out

    def measure_now(self):
        b, m, notes = self.bin, {}, {}
        objs = self.sim.objects
        nan = float("nan")
        if b is None:
            for o in objs.values():
                if o["type"] == "detector":
                    m[f"{o['id']}.hp"] = m[f"{o['id']}.hx"] = nan
                    notes[f"{o['id']}.hp"] = notes[f"{o['id']}.hx"] = "двойной нет"
            return m, notes
        x, v, nu, oid = b["st"]["x"], b["st"]["v"], b["nu"], b["id"]
        r = float(np.linalg.norm(x))
        E = self._energy(b["st"], nu, b["orders"])
        m.update({f"{oid}.r": r * self.L / 1e3, f"{oid}.r_m": r, f"{oid}.phase": float(b["phase"]),
                  f"{oid}.f": 2.0 * float(np.linalg.norm(np.cross(x, v))) / r ** 2 / (2.0 * math.pi) / self.T,
                  f"{oid}.e": float(PN.newtonian_elements(x, v)["e"]), f"{oid}.E": E,
                  f"{oid}.dE": (b["E0"] - E) / abs(b["E0"]) if b["E0"] else nan,
                  f"{oid}.J": float(np.linalg.norm(np.cross(x, v)))})
        for o in objs.values():
            if o["type"] != "detector":
                continue
            dv = o["values"]
            hp, hx = GW.binary_waveform(x, v, nu, math.radians(dv["iota"]), math.radians(dv["phi"]))
            sc = GW.strain_scale(self.gm, float(dv["distance"]) * MPC)
            m[f"{o['id']}.hp"], m[f"{o['id']}.hx"] = float(hp) * sc, float(hx) * sc
        return m, notes

    def checks(self):
        b = self.bin
        if b is None:
            return
        E = self._energy(b["st"], b["nu"], b["orders"])
        x = 1.0 / float(np.linalg.norm(b["st"]["x"]))
        if 2.5 not in b["orders"]:  # without radiation reaction the energy of the conservative orders is conserved
            self.sim.running_check("energy", "Энергия орбиты без излучения", E, b["E0"], tol=1e-9,
                                   ok=abs(E - b["E0"]) <= 1e-9 * abs(b["E0"]) + 10.0 * x ** 3 * abs(b["E0"]),
                                   note="энергия 2ПН (Kidder 1995) сохраняется уравнениями 1ПН + 2ПН до O(x³) (3ПН нет) "
                                        "и точности интегрирования")
            return
        loss = b["nu"] * (b["E0"] - E)  # E is per reduced mass mu = nu m (m = 1)
        if b["circular"] and b["orders"] == ALL_ORDERS and b["E_rad1"] > 0.0:
            ratio = loss / b["E_rad1"]
            # review B6-G1: the equations' reaction is accurate to relative 1PN; while it is an ordered series its
            # remainder is at most the 1PN correction it carries, |D - F1| <= |c1| x F_N at every moment, so the
            # accumulated ratio stays within |c1| x/(1 + c1 x) at the largest x so far (c1 < 0); a binary gaining energy
            # (ratio < 0) fails it, since the bound is < 1 while x < 1/(2|c1|) ~ 0.11 (the run stops before)
            c1, xm = flux_c1(b["nu"]), b["x_max"]
            tol = abs(c1) * xm / (1.0 + c1 * xm)
            self.sim.running_check("balance", "Баланс: убыль энергии орбиты / поток волн 1ПН", ratio, 1.0,
                                   tol=tol, ok=abs(ratio - 1.0) <= tol,
                                   note=f"поток круговой орбиты к 1ПН точности по x = (mΩ)^(2/3) (Blanchet 2014, ур. 314, "
                                        f"без хвостового члена, которого нет в локальных уравнениях); остаток реакции "
                                        f"излучения уравнений — порядка x² (её поправки 2ПН нет: измерено −35,5 x² при "
                                        f"малых x); допуск — пока ряд упорядочен, остаток не больше учтённой поправки "
                                        f"1ПН: |c₁| x/(1 + c₁ x), c₁ = −1247/336 − 35ν/12, x ≈ {xm:.3g} — наибольшее "
                                        f"за запуск; рост энергии (отношение < 0) не проходит")
        elif b["E_rad"] > 0.0:
            ratio = loss / b["E_rad"]
            self.sim.running_check("balance", "Баланс: убыль энергии / излучённое (квадрупольная формула)", ratio, 1.0,
                                   tol=0.0, info=True,
                                   note=f"излучённое — квадрупольная формула ведущего порядка по посчитанной орбите; "
                                        f"с реакцией излучения только 2,5ПН совпадение точное, с полными уравнениями — до "
                                        f"поправок порядка x ≈ {x:.3g} (около 7x при ν = 1/4)")

    def header(self):
        r0 = 20.0
        if self.bin is not None:
            r0 = float(np.linalg.norm(self.bin["st"]["x"]))
        return {"title": f"Плейграунд: двойная в ОТО (m = {self.sim.params['m_total']:.4g} M☉)",
                "approximations": ["постньютоновские уравнения движения (1ПН, 2ПН; реакция излучения 2,5ПН, 3,5ПН), "
                                   "без спинов и приливов; волны — квадрупольная формула ведущего порядка",
                                   "полные уравнения останавливаются там, где их реакция излучения перестаёт быть "
                                   "упорядоченным рядом (≈ 10,6–13 G m/c² по отношению масс): последние витки и "
                                   "слияние не показываются"],
                "scene3d": {"box": self._box(r0), "units": "G m/c²", "objects": [], "layers": [],
                            "planes": {"max": 0, "center": [0, 0, 0], "defaults": {}}, "up": [0.0, 0.0, 1.0],
                            "views": [["iso", "Изо", "Изометрия (F)", [0.5, -0.7, 0.5]],
                                      ["pole", "Сверху", "Вдоль момента орбиты", [0.0, 0.0, 1.0]],
                                      ["side", "С ребра", "Плоскость орбиты с ребра", [0.0, -1.0, 0.0]]]},
                "units": {"t": "с", "x": f"G m/c² = {self.L:.4g} м"}}

    def after_header(self):
        pass

    def engine_modules(self):
        return ["core.gravity.pn_binary", "core.gravity.gw_quadrupole"]


VIZ = {
    "id": "p01_gravity",
    "title": "Космос и гравитация",
    "summary": ("Песочница гравитации: звёзды, планеты, чёрные дыры, пробные тела и свет; ньютоновские N тел, "
                "двойная в ОТО с излучением гравитационных волн, геодезические у чёрной дыры Керра–Ньюмена."),
    "purpose": ("Собрать систему тел и посмотреть, как она движется: орбиты, сближения, захваты, сближение двойной "
                "из-за излучения волн, движение света и часов у вращающейся чёрной дыры; законы сохранения — вживую."),
    "version": "0.1",
    "schema": SCHEMA,
    "simulation": Simulation,
    "kind": "playground",
    "section": "gravity",
}
