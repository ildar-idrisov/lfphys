# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The world of a run: one optional gravitating body at the origin, objects on worldlines, light flashes.

Causal bookkeeping:
* every consequence (arrival of light, a measurement result, a scheduled emission) is a pending event with a
  time; it is revealed (emitted to the viewer) only when the run's time reaches it;
* an action changes the world at the current event only; pending events that depended on the changed object
  are withdrawn and recomputed from the current event on (e.g. an observer who accelerates before a flash
  reaches him receives it at a different time, his old apparatus is dismantled and re-synchronised);
* the past is never rewritten: revealed events stay as they were.
"""

from __future__ import annotations

import heapq
import itertools
import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.codes import code_of
from lfphys.core.gravity import arrivals, schwarzschild
from lfphys.core.gravity import rays as light
from lfphys.core.worldlines import Orbit, Piecewise, clock_rate
from lfphys.i18n import T
from lfphys.laws.light import Laws, flat_arrival
from lfphys.theories.alternatives import newton_light
from lfviz.errors import Refusal

from . import checks
from .apparatus import Apparatus, fmt_s

#: the engine's codes for a worldline that would outrun the local light (relativity.metric_clock_rate, clock_rate_flat)
SUPERLUMINAL = ("gr.not_timelike", "kinematics.superluminal")


@dataclass
class Obj:
    id: str
    name: object  # a translatable text (lfphys.i18n.T)
    kind: str  # star | planet | observer | beacon | galaxy
    color: str
    wl: object
    radius: float = 0.0  # physical radius for drawing (m)
    receiver: bool = True
    movable: bool = False
    apparatus: Apparatus | None = None
    trains: list = field(default_factory=list)


@dataclass(order=True)
class Pending:
    t: float
    seq: int
    ev: dict = field(compare=False)


class World:
    def __init__(self, laws: Laws, body: dict | None, scene_center, scene_radius: float, n_rays: int,
                 emit_msg):
        self.laws = laws
        self.body = body or {}
        gm = self.body.get("gm", 0.0)
        self.gm = gm
        self.rs = laws.rs(gm) if body else 0.0
        R = self.body.get("radius", 0.0)
        self.r_abs = max(R, self.rs)
        self.scene_center = np.asarray(scene_center, float)
        self.scene_radius = float(scene_radius)
        self.n_rays = int(n_rays)
        self.objects: dict[str, Obj] = {}
        self.pulses: list[dict] = []
        self.pending: list[Pending] = []
        self.seq = itertools.count()
        self.t = 0.0
        self.msg = emit_msg  # callable(meta, blobs)
        self.train_arrivals: dict = {}  # (train, receiver, image side, motion segments) -> [(pulse k, tau)]
        self.revealed: set = set()  # (pulse, receiver, image side) of arrivals already revealed (review R2)
        self.noticed: set = set()

    # --- construction -------------------------------------------------------------------------------
    def add(self, obj: Obj):
        self.objects[obj.id] = obj

    @property
    def gr(self) -> bool:
        return self.laws.gravity == "GR" and self.rs > 0

    @property
    def flat(self) -> bool:
        return self.laws.gravity == "none" or not self.body

    def schedule(self, ev: dict):
        heapq.heappush(self.pending, Pending(float(ev["t"]), next(self.seq), ev))

    def next_event_time(self):
        while self.pending and self.pending[0].ev.get("cancelled"):
            heapq.heappop(self.pending)
        return self.pending[0].t if self.pending else None

    # --- time ---------------------------------------------------------------------------------------
    def advance(self, t_target: float):
        while True:
            te = self.next_event_time()
            if te is None or te > t_target:
                break
            p = heapq.heappop(self.pending)
            self.t = max(self.t, p.t)
            self._reveal(p.ev)
        self.t = max(self.t, t_target)

    def _reveal(self, ev: dict):
        do = ev.pop("do", None)
        if do is not None:
            do()
        if "rkey" in ev:
            # the ordinal of this image among the arrivals of the same flash at the same receiver
            k = sum(1 for r in self.revealed if r[0] == ev["rkey"][0] and r[1] == ev["rkey"][1])
            ev["image"] = k
            if k and "targs" in ev:
                if ev["gr_clock"]:
                    ev["text"] = T("{obj}: light from “{src}” arrived (image {k:d}) after {dt} of Schwarzschild "
                                   "coordinate time (clock of “{obj}”: τ = {tau})", k=k + 1, **ev["targs"])
                else:
                    ev["text"] = T("{obj}: light from “{src}” arrived (image {k:d}) after {dt} (clock of “{obj}”: "
                                   "τ = {tau})", k=k + 1, **ev["targs"])
            self.revealed.add(ev["rkey"])
        if not ev.get("silent"):
            meta = {"type": "event", "t": ev["t"], "kind": ev["kind"], "text": ev.get("text", "")}
            for k in ("obj", "pulse", "data", "image", "pos"):
                if k in ev:
                    meta[k] = ev[k]
            self.msg(meta)
        for chk in ev.get("checks", []):
            self.msg(dict(chk, type="check", t=ev["t"]))

    def notice(self, key, text):
        if key not in self.noticed:
            self.noticed.add(key)
            self.msg({"type": "notice", "t": self.t, "text": text})

    def _cancel(self, pred):
        for p in self.pending:
            if not p.ev.get("cancelled") and pred(p.ev):
                p.ev["cancelled"] = True

    # --- light --------------------------------------------------------------------------------------
    def flash(self, src_id: str, t: float, n_rays: int | None = None, kind: str = "flash", train=None,
              label: str = "") -> dict:
        src = self.objects[src_id]
        origin = src.wl.pos(t)
        v = src.wl.vel(t)
        n = int(n_rays or self.n_rays)
        n_rest = light.unit_fan(n, angle0=0.5 * 2 * np.pi / n)
        rays = self._trace(origin[None, :].repeat(n, 0), t, n_rest, v)
        pid = f"p{len(self.pulses) + 1}"
        pulse = {"id": pid, "src": src_id, "t0": t, "origin": origin.tolist(), "v": v.tolist(), "kind": kind,
                 "n": n, "train": train, "label": label}
        self.pulses.append(pulse)
        self.msg({"type": "pulse", "t": t, **pulse}, rays.blobs())
        self.msg({"type": "event", "t": t, "kind": "emit", "obj": src_id, "pulse": pid,
                  "text": T("{obj}: {what}", obj=src.name, what=label or T("flash"))})
        for rid, obj in self.objects.items():
            if obj.receiver and rid != src_id:
                self._schedule_arrivals(pulse, obj, t)
        return pulse

    def plane_wave(self, t: float, x0: float, half_width: float, n: int, label=None):
        """Parallel rays moving along +x from the line x = x0, |y| <= half_width (drawing and deflection)."""
        ys = np.linspace(-half_width, half_width, n)
        origins = np.stack([np.full(n, x0), ys], axis=1)
        dirs = np.tile([1.0, 0.0], (n, 1))
        label = label or T("plane wave")
        rays = self._trace(origins, t, dirs, np.zeros(2))
        pid = f"p{len(self.pulses) + 1}"
        pulse = {"id": pid, "src": None, "t0": t, "origin": [x0, 0.0], "v": [0.0, 0.0], "kind": "plane", "n": n,
                 "train": None, "label": label}
        self.pulses.append(pulse)
        self.msg({"type": "pulse", "t": t, **pulse}, rays.blobs())
        self.msg({"type": "event", "t": t, "kind": "emit", "pulse": pid, "text": label})
        return rays, ys

    def _trace(self, origins, t, n_rest, v_src) -> light.RaySet:
        laws = self.laws
        far = np.max(np.linalg.norm(origins - self.scene_center, axis=1))
        r_scene = max(self.scene_radius, 1.05 * far)
        if self.gr:
            v_loc = light.local_velocity_static_frame(origins[0], v_src, self.rs, laws.c) if np.any(v_src) \
                else np.zeros(2)
            n_loc = light.aberrate_sr(n_rest, v_loc, laws.c)
            r_out = np.linalg.norm(self.scene_center) + r_scene
            return light.trace_gr(laws, origins, t, n_loc, self.rs, self.r_abs, r_out)
        if laws.gravity == "newton" and self.gm > 0:
            r0 = np.linalg.norm(origins, axis=1)
            sp = np.sqrt(laws.c**2 + 2 * self.gm / r0)
            vel = n_rest * sp[:, None] + np.asarray(v_src, float)
            r_out = np.linalg.norm(self.scene_center) + r_scene
            return newton_light.trace_newton(laws, origins, t, vel, self.gm, self.body.get("radius", 0.0), r_out)
        vel = laws.emit_velocities(n_rest, v_src)
        return light.trace_flat(laws, origins, t, vel, self.body.get("radius", 0.0), self.scene_center, r_scene)

    def _arrivals(self, pulse, wl, t_from):
        laws = self.laws
        o = np.asarray(pulse["origin"])
        if self.gr:
            return arrivals.gr_arrivals(laws.c, self.rs, self.r_abs, pulse["t0"], o, wl, t_from)
        if laws.gravity == "newton" and self.gm > 0:
            return newton_light.newton_arrivals(laws.c, self.gm, self.body.get("radius", 0.0), pulse["t0"], o,
                                            pulse["v"], wl, t_from, self.scene_radius)
        a = flat_arrival(laws, pulse["t0"], o, pulse["v"], wl, t_from)
        if a is None:
            return []
        a["key"] = "s0"
        # a body between source and receiver blocks the straight ray
        R = self.body.get("radius", 0.0)
        if R > 0 and _segment_hits_circle(o, wl.pos(a["t"]), R):
            return []
        return [a]

    def _schedule_arrivals(self, pulse, obj: Obj, t_from):
        if self.gr:
            r = float(np.linalg.norm(obj.wl.pos(max(t_from, pulse["t0"]))))
            if r <= 1.5 * self.rs:
                self.notice(("ps", obj.id), T("“{obj}” is inside the photon sphere (r ≤ 1.5 rs): this run does not "
                                              "compute the arrival of light there (STATUS V-items)", obj=obj.name))
        for a in self._arrivals(pulse, obj.wl, t_from):
            if (pulse["id"], obj.id, a.get("key", "s0")) in self.revealed:
                continue  # this image already arrived (a boost at the arrival instant must not repeat it)
            self._schedule_arrival(pulse, obj, a)
        if obj.apparatus is not None and self.flat:
            self._schedule_passing(pulse, obj, t_from)

    def _schedule_arrival(self, pulse, obj: Obj, a: dict):
        laws = self.laws
        dt = a.get("dt", a["t"] - pulse["t0"])  # flat solves give it without subtracting absolute times (P14)
        tau = obj.wl.tau(a["t"])
        src = self.objects.get(pulse["src"])
        data = {"dt": dt, "tau": tau, "dir": a["dir"], "method": a.get("method", ""), "side": a.get("key", "s0")}
        chks = []
        targs = {"obj": obj.name, "src": src.name if src else "?", "dt": fmt_s(dt), "tau": fmt_s(tau)}
        if self.gr:
            text = T("{obj}: light from “{src}” arrived after {dt} of Schwarzschild coordinate time (clock of "
                     "“{obj}”: τ = {tau})", **targs)
        else:
            text = T("{obj}: light from “{src}” arrived after {dt} (clock of “{obj}”: τ = {tau})", **targs)
        if self.gr and src is not None:
            # flat-space time for the same coordinate separation and the Shapiro excess
            d = float(np.linalg.norm(obj.wl.pos(a["t"]) - np.asarray(pulse["origin"])))
            data["shapiro"] = dt - d / laws.c
            o = np.asarray(pulse["origin"])
            p = obj.wl.pos(a["t"])
            if abs(_cross(o, p)) < 1e-12 * np.linalg.norm(o) * np.linalg.norm(p) and float(o @ p) > 0 \
                    and a["image"] == 0 and not np.any(obj.wl.vel(a["t"])):
                ref = checks.radial_light_time(np.linalg.norm(o), np.linalg.norm(p), self.rs, laws.c)
                chks.append(_check(f"radial_{pulse['id']}_{obj.id}", T("Time of flight of radial light (GR)"),
                                   dt, ref, T("s"), group=T("GR")))
        elif not self.gr and laws.gravity == "none" and src is not None and laws.kinematics != "emission":
            xr = obj.wl.pos(a["t"])
            d = float(np.linalg.norm(xr - np.asarray(pulse["origin"])))
            # the receiver's position is taken at the absolute arrival time, rounded to eps |t|: at t ~ 4e11 s that
            # moves a fast receiver by |v| eps |t| (review UX-params P14), plus the positions' own rounding
            eps = float(np.finfo(float).eps)
            vr = float(np.linalg.norm(obj.wl.vel(a["t"])))
            tol = 1e-9 + (4 * eps * (vr * abs(a["t"]) + float(np.linalg.norm(xr)) + float(np.linalg.norm(pulse["origin"])))
                          / (laws.c * dt) if dt > 0 else 0.0)
            chks.append(_check(f"flat_{pulse['id']}_{obj.id}",
                               T("Residual of the solution: time of flight to “{obj}” and |Δx|/c", obj=obj.name),
                               dt, d / laws.c, T("s"), group=T("Self-consistency"), tol=tol,
                               note=T("not an independent check: the residual of the equation the run solved; the "
                                      "time of flight is solved for starting from the flash event, while the "
                                      "receiver's position is taken at the absolute arrival time — tolerance "
                                      "{tol0:.0e} plus 4ε(|v|·|t| + |x|)/(c·Δt) for the rounding of absolute times "
                                      "and coordinates",
                                      tol0=1e-9)))
        ev = {"t": a["t"], "kind": "arrival", "obj": obj.id, "pulse": pulse["id"], "image": a["image"],
              "text": text, "targs": targs, "gr_clock": self.gr, "data": data, "checks": chks, "deps": {obj.id},
              "rkey": (pulse["id"], obj.id, a.get("key", "s0"))}
        if pulse.get("train"):
            ev["do"] = lambda pulse=pulse, obj=obj, tau=tau, a=a: self._train_arrival(pulse, obj, tau, a)
        self.schedule(ev)

    # --- pulse trains (Doppler, gravitational redshift) ------------------------------------------------
    def start_train(self, src_id: str, t: float, period: float, count: int):
        src = self.objects[src_id]
        tid = f"tr{sum(len(o.trains) for o in self.objects.values()) + 1}"
        train = {"id": tid, "src": src_id, "period": period, "count": count, "k": 0, "tau0": src.wl.tau(t)}
        src.trains.append(train)
        self._train_fire(train, t)
        return tid

    def _train_fire(self, train, t):
        k = train["k"]
        self.flash(train["src"], t, n_rays=max(36, self.n_rays // 6), kind="train",
                   train={"id": train["id"], "k": k, "period": train["period"]},
                   label=T("pulse {k:d}/{n:d} (period {period} by the source's clock)", k=k + 1, n=train["count"],
                           period=fmt_s(train["period"])))
        train["k"] += 1
        if train["k"] < train["count"]:
            self._schedule_train_next(train)

    def _schedule_train_next(self, train):
        src = self.objects[train["src"]]
        tau_next = train["tau0"] + train["k"] * train["period"]
        t_next = _inverse_tau(src.wl, tau_next, self.t)
        self.schedule({"t": t_next, "kind": "train", "obj": src.id, "silent": True, "deps": {src.id},
                       "train": train["id"], "do": lambda: self._train_fire(train, t_next)})

    def _train_arrival(self, pulse, obj, tau, a):
        tr = pulse["train"]
        # pair only pulses emitted on one inertial segment of the source and received on one of the receiver
        # (review R9: a pair across a boost mixes two motions), and of the same image side
        src = self.objects[pulse["src"]]
        key = (tr["id"], obj.id, a.get("key", "s0"), _seg_index(src.wl, pulse["t0"]), _seg_index(obj.wl, a["t"]))
        lst = self.train_arrivals.setdefault(key, [])
        lst.append((tr["k"], tau))
        if len(lst) >= 2 and lst[-1][0] == lst[-2][0] + 1:
            T_rx = lst[-1][1] - lst[-2][1]
            ratio = tr["period"] / T_rx  # received / emitted frequency
            ref, note = self._doppler_reference(pulse, obj, a)
            self.msg({"type": "check", "t": a["t"], **_check(
                f"doppler_{tr['id']}_{obj.id}_{a.get('key', 's0')}",
                T("Frequency at “{obj}” / frequency of the source", obj=obj.name), ratio, ref, "",
                group=T("Doppler effect and redshift"),
                note=note)})

    def _doppler_reference(self, pulse, obj, a):
        laws = self.laws
        src = self.objects[pulse["src"]]
        t_e = pulse["t0"]
        vs = np.asarray(pulse["v"])
        vr = obj.wl.vel(a["t"])
        if self.gr:
            if not np.any(vs) and not np.any(vr) and isinstance(src.wl, Piecewise):
                re = np.linalg.norm(pulse["origin"])
                rr = np.linalg.norm(obj.wl.pos(a["t"]))
                return 1.0 / checks.gravitational_period_ratio(re, rr, self.rs), \
                    T("static clocks: √(f_received/f_emitted)⁻¹")
            return None, T("no closed form for this motion")
        o = np.asarray(pulse["origin"])
        p = obj.wl.pos(a["t"])
        collinear = abs(o[1]) < 1e-9 * (1 + abs(o[0])) and abs(p[1]) < 1e-9 * (1 + abs(p[0])) \
            and abs(vs[1]) == 0 and abs(vr[1]) == 0
        if not collinear or laws.gravity != "none":
            return None, T("a reference only for motion along the x axis")
        s = 1 if p[0] > o[0] else -1
        return checks.doppler_ratio(laws.kinematics, s, vs[0] / laws.c, vr[0] / laws.c), T("longitudinal Doppler effect")

    # --- apparatus ----------------------------------------------------------------------------------
    def build_apparatus(self, obj: Obj, t: float):
        ap = obj.apparatus
        evs = ap.build(t)
        gen = ap.gen
        self.msg({"type": "worldline", "t": t, "id": obj.id + ":B", "wl": ap.wl_b.to_json(), "gen": gen,
                  "owner": obj.id})
        if ap.sync_path:
            self.msg({"type": "signal", "t": t, "owner": obj.id, "gen": gen, "kind": "sync", "pts": ap.sync_path})
        for e in evs:
            self.schedule(dict(e, obj=obj.id, deps={obj.id}, gen=gen))
        return evs

    def _schedule_passing(self, pulse, obj: Obj, t_from):
        ap = obj.apparatus
        if pulse["src"] == obj.id:
            return
        a_list = self._arrivals(pulse, ap.wl_a, t_from)
        b_list = self._arrivals(pulse, ap.wl_b, t_from)
        if not a_list or not b_list:
            return
        ta, tb = a_list[0]["t"], b_list[0]["t"]
        if min(ta, tb) < ap.t_build:
            return  # the flash had passed one end before this apparatus existed
        if float(np.dot(a_list[0]["dir"], b_list[0]["dir"])) < 0.0:
            # the flash went off between the ends (review UX-params P9): the light that reaches A and the light that
            # reaches B run in opposite directions, so the two passages are not one light passing the rod and
            # L0/(tau_B - tau_A) is not a speed (it read 5.6e8 ... 7.8e9 m/s). Said when A could know it
            t_known = ap.known_time(ta, tb)
            if t_known is None:
                return
            src = self.objects.get(pulse["src"])
            self.schedule({"t": t_known, "kind": "measure", "obj": obj.id, "pulse": pulse["id"],
                           "deps": {obj.id}, "gen": ap.gen,
                           "text": T("{obj}: the flash of “{src}” went off between the ends of the rod — the light "
                                     "passed A and B in opposite directions, so the two ends do not measure a speed",
                                     obj=obj.name, src=src.name if src else "?")})
            return
        ref_a = a_list[0] if a_list[0].get("speed_lab", 1.0) > 0 and np.any(a_list[0]["dir"]) else b_list[0]
        u = np.asarray(ref_a["dir"]) * ref_a.get("speed_lab", self.laws.c)  # review R25: not from a zero vector
        res = ap.passing(ta, tb, ref_a["dir"], u)
        if res["t_known"] is None:
            return
        if abs(abs(res["cos"]) - 1.0) > 1e-6:
            return  # light not along the rod: the two passages do not measure its speed
        src = self.objects.get(pulse["src"])
        v_app = ap.wl_a.vel(ta)
        ref, note = None, _sync_note(ap.sync)
        if ap.orient == "x" and v_app[1] == 0 and pulse["v"][1] == 0:
            s = 1 if res["order"] == "A→B" else -1
            ref = checks.one_way_speed(self.laws.kinematics, ap.sync, self.laws.c, v_app[0], s, pulse["v"][0])
        text = T("{obj}: light from “{src}” passed the rod {order}, measured c = {c:.9g} m/s", obj=obj.name,
                 src=src.name if src else "?", order=res["order"], c=res["speed"])
        chk = _check(f"pass_{pulse['id']}_{obj.id}_{ap.gen}",
                     T("{obj}: one-way speed (external light)", obj=obj.name),
                     res["speed"], ref, T("m/s"), group=T("Speed of light"), note=note)
        self.schedule({"t": res["t_known"], "kind": "measure", "obj": obj.id, "pulse": pulse["id"], "text": text,
                       "data": res, "checks": [chk], "deps": {obj.id}, "gen": ap.gen,
                       "redeliver": {"type": "passing", "ta": ta, "tb": tb}})

    def measure(self, obj_id: str, t: float) -> T:
        obj = self.objects[obj_id]
        if self.gr:
            return self._measure_local_gr(obj, t)
        ap = obj.apparatus
        if ap is None:
            raise Refusal(T("“{obj}” has no apparatus", obj=obj.name),
                          hint=T("choose an observer that carries a rod"))
        res = ap.round_trip(t)
        self.msg({"type": "signal", "t": t, "owner": obj_id, "gen": ap.gen, "kind": "measure", "pts": res["path"]})
        v = ap.wl_a.vel(t)
        chks = [_check(f"rt_{obj_id}_{t:.17g}", T("{obj}: round-trip speed (2L₀/Δτ)", obj=obj.name), res["rt"],
                       checks.round_trip_speed(self.laws.kinematics, self.laws.c, float(np.linalg.norm(v)),
                                               transverse=(ap.orient == "y")) if (v[1] == 0) else None,
                       T("m/s"), group=T("Speed of light"), note=T("independent of the synchronisation"))]
        if "ab" in res:
            for key, s, lab in (("ab", 1, "A→B"), ("ba", -1, "B→A")):
                ref = None
                if ap.orient == "x" and v[1] == 0:
                    ref = checks.one_way_speed(self.laws.kinematics, ap.sync, self.laws.c, v[0], s, v[0])
                chks.append(_check(f"ow{key}_{obj_id}_{t:.17g}",
                                   T("{obj}: one way {dir} (own light)", obj=obj.name, dir=lab),
                                   res[key], ref, T("m/s"), group=T("Speed of light"), note=_sync_note(ap.sync)))
            txt = T("{obj}: round trip c = {c:.9g} m/s; A→B {ab:.9g}, B→A {ba:.9g} m/s", obj=obj.name, c=res["rt"],
                    ab=res["ab"], ba=res["ba"])
        else:
            txt = T("{obj}: round trip c = {c:.9g} m/s; one-way speeds are not available: clock B is not "
                    "synchronised yet", obj=obj.name, c=res["rt"])
        self.schedule({"t": res["t_known"], "kind": "measure", "obj": obj_id, "text": txt, "data": res,
                       "checks": chks, "deps": {obj_id}, "gen": ap.gen,
                       "redeliver": {"type": "round", "t1": t, "t2": res["t_reflect"], "label": obj.name}})
        self.schedule({"t": res["t_reflect"], "kind": "sync", "obj": obj_id, "gen": ap.gen,
                       "pos": ap.wl_b.pos(res["t_reflect"]).tolist(),
                       "text": T("{obj}: the measuring pulse reflected from B", obj=obj.name)})
        return T("{obj}: a measuring pulse sent along the rod", obj=obj.name)

    def _measure_local_gr(self, obj: Obj, t: float) -> T:
        """Local round trip over a short radial rod at a static observer (exact geodesics)."""
        if np.any(obj.wl.vel(t)):
            raise Refusal(T("in GR the local measurement is made for an observer at rest (a static observer)"),
                          hint=T("set the observer's speed to 0 first"))
        p = obj.wl.pos(t)
        r = float(np.linalg.norm(p))
        ell = 1e-3 * r  # proper length of the rod
        # B at proper radial distance ell outward: solve integral dr / sqrt(f) = ell
        rs = self.rs
        from scipy import optimize

        def proper(x):  # antiderivative of dr / sqrt(1 - rs/r): sqrt(r(r - rs)) + rs ln(sqrt r + sqrt(r - rs))
            return math.sqrt(x * (x - rs)) + rs * math.log(math.sqrt(x) + math.sqrt(x - rs))

        rb = optimize.brentq(lambda x: proper(x) - proper(r) - ell, r, r + 2 * ell, xtol=1e-15 * r, rtol=1e-15)
        pb = p / r * rb
        i1 = schwarzschild.connect(p, pb, rs, self.laws.c, self.r_abs)[0]["dt"]
        i2 = schwarzschild.connect(pb, p, rs, self.laws.c, self.r_abs)[0]["dt"]
        dtau = math.sqrt(1 - rs / r) * (i1 + i2)
        c_loc = 2 * ell / dtau
        coord = self.laws.c * (1 - rs / r)
        # reference: the same finite radial rod in closed form (review R8); -> c as the rod shrinks
        ref = 2 * ell / (math.sqrt(1 - rs / r) * 2 * checks.radial_light_time(r, rb, rs, self.laws.c))
        chk = _check(f"loc_{obj.id}_{t:.17g}",
                     T("{obj}: locally measured speed of light (rod {ell:.3g} m, round trip)", obj=obj.name, ell=ell),
                     c_loc, ref, T("m/s"), group=T("GR"),
                     note=T("reference: the radial time in closed form for this rod; as its length → 0 the speed "
                            "derived from it → c (the difference now {d:.2e}); the coordinate radial speed here "
                            "c·(1−rs/r) = {v:.9g} m/s",
                            d=(ref - self.laws.c) / self.laws.c, v=coord))
        self.schedule({"t": t + i1 + i2, "kind": "measure", "obj": obj.id, "deps": {obj.id},
                       "text": T("{obj}: locally c = {c:.9g} m/s (coordinate {v:.9g})", obj=obj.name, c=c_loc,
                                 v=coord),
                       "checks": [chk]})
        return T("{obj}: local measurement along a radial rod", obj=obj.name)

    # --- actions ------------------------------------------------------------------------------------
    def boost(self, obj_id: str, v_new, t: float):
        obj = self.objects[obj_id]
        if not obj.movable or not isinstance(obj.wl, Piecewise):
            raise Refusal(T("“{obj}” cannot be accelerated", obj=obj.name),
                          hint=T("choose an observer or a rocket"))
        v_new = np.asarray(v_new, float)
        self._validate_path(obj, t, v_new)  # raises with the reason (review R10)
        old_ap = None
        if obj.apparatus is not None and self.flat:
            ap = obj.apparatus
            old_ap = (ap.gen, ap.wl_b, ap.offset_b, ap.t_sync_done)
        keep = [p for p in self.pending if not p.ev.get("cancelled") and obj_id in p.ev.get("deps", ())
                and p.ev.get("redeliver")]
        obj.wl.boost(t, v_new)
        self._cancel(lambda ev: obj_id in ev.get("deps", ()))
        self.msg({"type": "worldline", "t": t, "id": obj_id, "wl": obj.wl.to_json()})
        if obj.apparatus is not None and self.flat:
            # idealisation (review R12, stated in the README): a new mirror B' is taken to be at rest at L0 in the
            # new frame from this moment; the old mirror goes on inertially and light already sent goes on too
            self.msg({"type": "event", "t": t, "kind": "sync", "obj": obj_id,
                      "text": T("{obj}: the apparatus rebuilt in the new rest frame (an idealisation: the new mirror "
                                "B′ is taken as prepared in advance; the old mirror flies on by inertia)",
                                obj=obj.name)})
            for p in keep:
                self._redeliver(obj, p.ev, old_ap, t)
            self.build_apparatus(obj, t)
        for pulse in self.pulses:
            if pulse["src"] == obj_id or pulse["kind"] == "plane":
                continue
            self._schedule_arrivals(pulse, obj, t)
        for tr in obj.trains:
            if tr["k"] < tr["count"]:
                self._schedule_train_next(tr)

    def _redeliver(self, obj: Obj, ev: dict, old_ap, t_boost: float):
        """A measurement that was under way when A changed its velocity (review R13): the readings that already
        exist are kept; light already on its way (B's report, or the returning pulse reflected by the old mirror,
        which goes on inertially) is delivered to A's NEW worldline."""
        gen, wl_b, offset_b, t_sync = old_ap
        rd = ev["redeliver"]
        wl_b = rd.get("wl_b", wl_b)  # a second boost before delivery: the mirror is still the first one
        t_sync = rd.get("t_sync", t_sync)
        laws = self.laws
        if rd["type"] == "passing":
            ta, tb = rd["ta"], rd["tb"]
            if max(ta, tb) > t_boost or t_sync is None or t_sync > t_boost:
                self.msg({"type": "event", "t": t_boost, "kind": "measure", "obj": obj.id,
                          "text": T("{obj}: the measurement of external light interrupted — the light had not yet "
                                    "passed both ends of the old apparatus, or its clocks were not synchronised",
                                    obj=obj.name)})
                return
            # B's reading leaves old B at tb and travels to A's new worldline
            rep = flat_arrival(laws, tb, wl_b.pos(tb), wl_b.vel(tb), obj.wl, t_boost)
            if rep is None:
                return
            t_known = max(rep["t"], ta)
            ev2 = dict(ev)
            ev2.pop("cancelled", None)
            ev2["t"] = t_known
            ev2["deps"] = {obj.id}
            ev2["redeliver"] = dict(rd, wl_b=wl_b, t_sync=t_sync)
            if not ev.get("redelivered"):
                ev2["text"] = T("{text} (the result delivered after A changed its speed)", text=ev["text"])
                ev2["redelivered"] = True
            self.schedule(ev2)
        else:  # own round trip: the old mirror reflects at t2 (unchanged), the pulse returns to the new A
            t1, t2 = rd["t1"], rd["t2"]
            back = flat_arrival(laws, t2, wl_b.pos(t2), wl_b.vel(t2), obj.wl, max(t_boost, t2))
            if back is None:
                return
            t3 = back["t"]
            ap = obj.apparatus
            rt = 2 * ap.L0 / (obj.wl.tau(t3) - obj.wl.tau(t1))
            chk = _check(f"rt_{obj.id}_{t1:.17g}",
                         T("{obj}: round trip, A changed its speed during the measurement", obj=rd["label"]),
                         rt, None, T("m/s"), group=T("Speed of light"),
                         note=T("no closed form: A moved along two different worldlines"))
            self.schedule({"t": t3, "kind": "measure", "obj": obj.id, "deps": {obj.id}, "checks": [chk],
                           "redeliver": dict(rd, wl_b=wl_b, t_sync=t_sync),
                           "text": T("{obj}: the pulse returned to A after the change of speed, 2L₀/Δτ = {v:.9g} m/s",
                                     obj=rd["label"], v=rt)})

    def _validate_path(self, obj: Obj, t: float, v) -> None:
        """Refuse a boost whose straight future path crosses the body or, in GR, stops being timelike for the local
        static observers (a constant coordinate velocity is not a free motion; review R10)."""
        p0 = obj.wl.pos(t)
        R = self.body.get("radius", 0.0) if self.body else 0.0
        r_abs = max(R, self.rs)
        if not np.any(v):
            clock_rate(self.laws, self.rs, p0, v)
            return
        vv = float(v @ v)
        s_star = max(-float(p0 @ v) / vv, 0.0)
        d_min = float(np.linalg.norm(p0 + v * s_star))
        if r_abs > 0 and d_min <= r_abs:
            raise Refusal(T("at this speed “{obj}” would fly into the body (in {dt} of lab time)", obj=obj.name,
                            dt=fmt_s(s_star)), hint=T("choose another direction"))
        if self.gr:
            scale = max(float(np.linalg.norm(p0)), self.scene_radius) / math.sqrt(vv)
            u = np.tan(np.linspace(0.0, 0.499 * math.pi, 4001)) * scale
            for s in np.concatenate([u, s_star + np.linspace(-1, 1, 401) * 0.01 * scale]):
                if s < 0:
                    continue
                try:
                    clock_rate(self.laws, self.rs, p0 + v * s, v)
                except ValueError as e:  # by the engine's machine code (lfphys.codes; review i18n-code F5)
                    if code_of(e) not in SUPERLUMINAL:
                        raise
                    raise Refusal(T("at a constant coordinate speed “{obj}” would move faster than light for the "
                                    "local static observer in {dt}; in GR the “speed” is the coordinate one "
                                    "(Schwarzschild dx/dt)", obj=obj.name, dt=fmt_s(s)),
                                  hint=T("choose a smaller speed or another direction")) from None

    # --- views --------------------------------------------------------------------------------------
    def frame_state(self, t: float) -> dict:
        objs = []
        for o in self.objects.values():
            p, v = o.wl.pos(t), o.wl.vel(t)
            d = {"id": o.id, "x": p[0], "y": p[1], "vx": v[0], "vy": v[1], "tau": o.wl.tau(t)}
            if o.apparatus is not None and o.apparatus.wl_b is not None and self.flat:
                pb = o.apparatus.wl_b.pos(t)
                d["bx"], d["by"] = pb[0], pb[1]
                synced = o.apparatus.t_sync_done is not None and o.apparatus.t_sync_done <= t
                # B's synchronised reading exists only once the exchange that defines it is over (review R4)
                d["tau_b"] = o.apparatus.reading("B", t) if synced else None
                d["synced"] = synced
            objs.append(d)
        frames, seen, now_at, cones = {}, {}, {}, {}
        for o in self.objects.values():
            if o.kind in ("observer", "station"):
                cones[o.id] = self._cone(o, t)
        if self.flat:
            for o in self.objects.values():
                if o.kind != "observer":
                    continue
                v = o.wl.vel(t)
                M = self.laws.frame_matrix(v)
                frames[o.id] = M.ravel().tolist()
                seen[o.id] = {q.id: self._seen(o, q, t) for q in self.objects.values() if q.id != o.id}
                now_at[o.id] = {q.id: self._now_at(M, o, q, t) for q in self.objects.values() if q.id != o.id}
        return {"objects": objs, "frames": frames, "seen": seen, "now_at": now_at, "cones": cones}

    def _cone(self, o: Obj, t: float) -> dict:
        """Local light cone at the object's current event in the (x, t) projection, as lab velocities dx/dt.
        future: the extreme x-velocities of light the object emits in any direction (law-dependent; review R7: not
        the rays along its own x axis); past: light arriving along +-x from sources at rest in the lab.
        GR: the coordinate light speed along x at the object's position, c f / sqrt(cos^2 a + f sin^2 a) with a the
        angle between x and the radial direction (review R23); exact locally, it changes along the ray."""
        c = self.laws.c
        if self.gr:
            p = o.wl.pos(t)
            r = float(np.linalg.norm(p))
            if r <= 0:
                return {"fut": [0.0, 0.0], "past": [0.0, 0.0], "local": True}
            f = 1.0 - self.rs / r
            ca = p[0] / r
            k = c * f / math.sqrt(ca * ca + f * (1 - ca * ca))
            return {"fut": [k, -k], "past": [k, -k], "local": True}
        v = o.wl.vel(t)
        from scipy import optimize

        def ux(a, sign):  # lab x-velocity of light emitted at rest-frame angle a (the laws' own emission rule)
            return -sign * float(self.laws.emit_velocities(np.array([[math.cos(a), math.sin(a)]]), v)[0, 0])

        ext = []
        fan = light.unit_fan(720)
        u = self.laws.emit_velocities(fan, v)[:, 0]
        for sign in (1, -1):
            k = int(np.argmax(sign * u))
            a0 = math.atan2(fan[k, 1], fan[k, 0])
            r = optimize.minimize_scalar(ux, bounds=(a0 - 0.02, a0 + 0.02), args=(sign,), method="bounded",
                                         options={"xatol": 1e-12})
            ext.append(-sign * r.fun)
        return {"fut": ext, "past": [c, -c], "local": False}

    def _now_at(self, M, obs: Obj, q: Obj, t: float):
        """Lab time of the event on q's worldline that obs (inertial now, matrix M) calls simultaneous with
        its current event: equal ct' in obs's frame."""
        c = self.laws.c
        xo = obs.wl.pos(t)
        target = M[0] @ np.array([c * t, xo[0], xo[1]])

        def h(tq):
            xq = q.wl.pos(tq)
            return float(M[0] @ np.array([c * tq, xq[0], xq[1]]) - target)

        from scipy import optimize
        span = max(float(np.linalg.norm(q.wl.pos(t) - xo)) / c, 1e-12)
        lo, hi = t - span, t + span
        for _ in range(80):
            if h(lo) <= 0 <= h(hi):
                break
            lo, hi = t - 2 * (t - lo), t + 2 * (hi - t)
        else:
            return None
        return optimize.brentq(h, lo, hi, xtol=1e-16 * max(1.0, abs(t)), rtol=1e-15, maxiter=300)

    def _seen(self, obs: Obj, q: Obj, t: float):
        """Emission event on q's worldline whose light reaches obs at t (the past light cone)."""
        laws = self.laws
        xo = obs.wl.pos(t)
        c = laws.c

        def g(te):
            xq = q.wl.pos(te)
            w = q.wl.vel(te) if laws.kinematics == "emission" else np.zeros(2)
            return float(np.linalg.norm(xo - xq - w * (t - te)) - c * (t - te))

        hi = t
        if g(hi) <= 0:
            return None
        span = max(float(np.linalg.norm(xo - q.wl.pos(t))) / c, 1e-15)
        lo = t - span
        for _ in range(80):
            if g(lo) < 0:
                break
            lo = t - 2 * (t - lo)
        else:
            return None
        from scipy import optimize
        te = optimize.brentq(g, lo, hi, xtol=1e-16 * max(1.0, abs(t)), rtol=1e-15, maxiter=300)
        xq = q.wl.pos(te)
        R = self.body.get("radius", 0.0) if self.body else 0.0
        if R > 0 and q.kind != "star" and _segment_hits_circle(xq, xo, R):
            return None  # hidden behind the body (review R24)
        return [te, xq[0], xq[1]]


def _seg_index(wl, t):
    """Index of the inertial segment containing t (0 for an orbit)."""
    if isinstance(wl, Piecewise):
        k = 0
        for i, sgm in enumerate(wl.segments):
            if sgm.t0 <= t:
                k = i
        return k
    return 0


def _inverse_tau(wl, tau_target, t_now):
    """Lab time at which the worldline's clock reads tau_target (searching from t_now forward)."""
    from scipy import optimize
    lo = t_now
    if wl.tau(lo) >= tau_target:
        return lo
    hi = lo + max(tau_target - wl.tau(lo), 1e-15) * 2 + 1e-12
    while wl.tau(hi) < tau_target:
        hi = lo + 2 * (hi - lo)
    return optimize.brentq(lambda x: wl.tau(x) - tau_target, lo, hi, xtol=1e-15 * max(1.0, abs(hi)),
                           rtol=1e-15, maxiter=300)


def _cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def _segment_hits_circle(p, q, R) -> bool:
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p
    L2 = float(d @ d)
    if L2 == 0:
        return float(p @ p) < R * R
    s = float(np.clip(-(p @ d) / L2, 0.0, 1.0))
    m = p + s * d
    return float(m @ m) < R * R


def _sync_note(sync: str) -> T:
    return T("synchronisation: Einstein's") if sync == "einstein" else T("synchronisation: laboratory")


def _check(cid, label, value, ref, unit, group="", note="", tol=1e-9):
    """A computed value next to its reference. ``tol``: the relative agreement expected from the numerics
    (exact solves: 1e-9; resolution-limited quantities state their own)."""
    rel = None
    if ref is not None and value is not None and math.isfinite(value) and ref != 0:
        rel = (value - ref) / abs(ref)
    return {"id": cid, "label": label, "value": value, "ref": ref, "unit": unit, "rel": rel, "group": group,
            "note": note, "tol": tol}
