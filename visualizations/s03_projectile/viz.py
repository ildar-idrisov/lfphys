# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""S03: projectile motion, a ball thrown horizontally and at an angle, in vacuum or in air (school, FRP grades 7 and 10).

What the run computes (README.md of this folder has the model in full):
* the ball's flight from its launch (height h above the floor, speed v₀, angle θ to the horizontal): Newton's second
  law in a uniform field, with the air's quadratic drag when the air is on (``engine/shot.py`` over
  ``lfphys.core.mechanics`` and ``lfphys.theories.models.drag_quadratic``), computed ahead and revealed as the world's
  time reaches it: samples every 1/60 s (``traj``), the top of the path and the landing as events;
* optionally a second ball: one dropped at the same moment from the same point (the independence of the vertical
  motion), or the same throw in vacuum for comparison (grey; it does not affect the world's ball);
* the run's measurements: the range L, the flight time T, the highest point H, the energy, the heat given to the air;
* checks: T, L, H against the closed forms in vacuum, against the hodograph quadrature in air (the second method, no
  integration in time), the energy balance along the path, the drag model's range of validity (the Reynolds numbers
  where the constant C_d is used) and, as information, the same throw with the measured drag curve (the second drag
  model: how much the constant itself moves the range; review R-E F1), the dropped ball's fall time and its height next
  to the thrown one's.

The screens (design ``lfphys/sources/explore_2026-11-14_design.md`` §5): Watch (the recording ``independence`` with
captions, and ``air`` under «More recordings»), Explore (height × speed × angle × air on a grid of computed points) and
Lab work (three parts: L(h) and L(θ) without air, the maximum in air). No law parameter (school: no modified physics,
rule 4): the air is a medium, not a modification.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.i18n import T, text_of
from lfphys.theories.models.drag_quadratic import CD_SPHERE, RE_RANGE

from .engine.shot import OBJECTS, RATE, STROBE_EVERY, VALID_SHARE, G, Shot, curve_flight, medium, optimum_angle

def _r(x: float, digits: int = 6) -> float:
    """A value that is only drawn, to 6 significant digits (the record's size): a position of a 100 m flight to 0.1 mm,
    far below a pixel; the energy bars and the force arrows to 4 (they show 3)."""
    return float(f"{float(x):.{digits}g}")


#: the samples are sent in chunks of at least 3 (0.05 s of world time), or at the landing: one message per frame would
#: repeat the blob's descriptor for one or two samples (the atlases' size, design §1.8); the view joins the last sample
#: sent to the ball's computed position in the frame (a chord of at most 3 mm on a path of the Watch's scale)
CHUNK = 3
TOL = 1e-9  # the engine's stated error (lfphys.core.mechanics): relative, in T, L, H and the energy balance

OBJECT_LABELS = {"steel20": T("steel ball, 20 mm, 32.9 g"),
                 "ball67": T("light ball, 67 mm, 58 g (the size of a tennis ball)")}
COMPANIONS = [("none", T("none")), ("drop", T("a ball dropped at the same moment from the same point")),
              ("vacuum", T("the same throw in vacuum (grey)"))]

SCHEMA = Schema([
    Param("object", T("The ball"), "select", "steel20", options=list(OBJECT_LABELS.items()),
          help=T("A smooth sphere. The light ball has the size and the mass of a tennis ball, but a smooth sphere's "
                 "drag (a real tennis ball's felt has its own).")),
    Param("h_m", T("Launch height"), "float", 1.0, unit=T("m"), min=0.0, max=20.0,
          help=T("The height of the launch point above the floor.")),
    Param("v0", T("Launch speed"), "float", 5.0, unit=T("m/s"), min=0.0, max=40.0),
    Param("angle_deg", T("Launch angle"), "float", 45.0, unit="°", min=-30.0, max=90.0,
          help=T("The angle of the launch to the horizontal: 0° is a horizontal throw, 90° straight up, a negative "
                 "angle downwards.")),
    Param("air", T("Air resistance"), "bool", False,
          help=T("Off: the ball flies in vacuum. On: air at 20 °C and 101 325 Pa, the drag of a smooth sphere with a "
                 "constant drag coefficient of 0.47 (a model: the run also computes the same throw with the measured "
                 "drag curve and shows the difference).")),
    Param("companion", T("Ball for comparison"), "select", "none", options=COMPANIONS,
          help=T("A second ball: dropped from the same point at the same moment, or the same throw computed in vacuum "
                 "(grey). It does not affect the first ball.")),
], presets={
    "field": {"label": T("A light ball thrown at 45° from a height of 1 m"),
              "params": {"object": "ball67", "h_m": 1.0, "v0": 15.0, "angle_deg": 45.0, "air": False}},
    "chute": {"label": T("A steel ball rolls off a chute on a table"),
              "params": {"object": "steel20", "h_m": 0.6, "v0": 1.5, "angle_deg": 0.0, "air": True}},
    "launcher": {"label": T("A ballistic launcher on the floor, without air"),
                 "params": {"object": "steel20", "h_m": 0.0, "v0": 5.0, "angle_deg": 45.0, "air": False}},
    "air_max": {"label": T("A light ball at 20 m/s in air, and the same throw in vacuum"),
                "params": {"object": "ball67", "h_m": 0.0, "v0": 20.0, "angle_deg": 40.0, "air": True,
                           "companion": "vacuum"}},
    "story": {"label": T("Two balls at the same moment: one dropped, one thrown sideways"),
              "params": {"object": "steel20", "h_m": 1.25, "v0": 2.0, "angle_deg": 0.0, "air": False,
                         "companion": "drop"}},
})

GROUPS = {"main": T("The thrown ball"), "drop": T("The dropped ball"), "vacuum": T("The same throw in vacuum")}
HOW = {"vacuum": T("by the formulas of a flight in vacuum"),
       "hodograph": T("second method: the hodograph quadrature of the quadratic drag (no integration in time)"),
       "vertical": T("by the formulas of vertical motion with quadratic drag")}


class Simulation(BaseSimulation):
    default_speed = 1.0
    speed_range = (0.01, 10.0)

    @classmethod
    def check_params(cls, params):
        h, v0, ang = float(params["h_m"]), float(params["v0"]), float(params["angle_deg"])
        if h <= 0.0 and (ang <= 0.0 or v0 <= 0.0):
            raise Refusal(T("The ball starts on the floor and does not move upwards: there is no flight"),
                          T("raise the launch height, or throw upwards with a speed above zero"))
        comp = params.get("companion", "none")
        if comp == "drop" and h <= 0.0:
            raise Refusal(T("A ball dropped from the floor does not fall"), T("raise the launch height"))
        if comp == "vacuum" and not params["air"]:
            raise Refusal(T("The comparison with vacuum needs the air resistance on"),
                          T("turn the air resistance on, or choose another ball for comparison"))

    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference=None):
        """A law of a lab step (design §2.3; the step's ``laws``, review D4), computed by the world when the step's atlas
        is built: ``k_horizontal`` k = v₀·√(2/g) (formula; the part is computed without air, and the air's effect is
        computed for each of the step's heights and stated); ``v2_over_g`` v₀²/g (formula, no air);
        ``theta_max_vacuum`` the angle of the largest range without air (45° from the floor by the formula, else the
        engine's scan); ``theta_max_air`` the angle of the largest range in air, found by the engine at 0.1° steps with
        the world's drag model (the constant C_d), with the measured drag curve's optimum stated beside it (review R-E
        F1: the optimum depends on the drag model)."""
        p = dict(fixed)
        ref = reference or DEFAULT_LAW.get(step_id)
        if step_id == "heights" and ref == "k_horizontal":
            v0, obj = float(p["v0"]), p["object"]
            hs = sorted(float(h) for h in (values.get("h_m") or [p["h_m"]]))
            # the air's shortening of the range at each height (m), computed by the engine: the part runs without air
            short = [(h, Shot(obj, h, v0, 0.0, False).L - Shot(obj, h, v0, 0.0, True).L) for h in hs]
            tape = INSTRUMENTS["tape"]["error"]
            over = [h for h, d in short if d > tape]
            args = dict(a=1e3 * short[0][1], h0=short[0][0], b=1e3 * short[-1][1], h1=short[-1][0], e=1e3 * tape)
            if not over:
                how = T("the formula of a horizontal throw without air, L = v₀·√(2h/g); this part is computed without "
                        "air. In air the range would be shorter by {a:.2f} mm at h = {h0:.2f} m to {b:.2f} mm at "
                        "h = {h1:.2f} m (computed by the engine for each height), less than the tape's error of "
                        "±{e:.1f} mm at every height", **args)
            elif over == [h for h in hs if h >= over[0]]:
                how = T("the formula of a horizontal throw without air, L = v₀·√(2h/g); this part is computed without "
                        "air. In air the range would be shorter by {a:.2f} mm at h = {h0:.2f} m to {b:.2f} mm at "
                        "h = {h1:.2f} m (computed by the engine for each height): more than the tape's error of "
                        "±{e:.1f} mm from h = {h2:.2f} m on, so the bench would see the air", h2=over[0], **args)
            else:
                how = T("the formula of a horizontal throw without air, L = v₀·√(2h/g); this part is computed without "
                        "air. In air the range would be shorter by {a:.2f} mm at h = {h0:.2f} m to {b:.2f} mm at "
                        "h = {h1:.2f} m (computed by the engine for each height): at some heights more than the tape's "
                        "error of ±{e:.1f} mm, so the bench would see the air", **args)
            return {"value": v0 * math.sqrt(2.0 / G), "unit": T("m^½"), "label": T("k = v₀·√(2/g)"), "how": how,
                    "kind": "closed form"}
        if step_id == "angles" and ref == "v2_over_g":
            v0 = float(p["v0"])
            return {"value": v0 * v0 / G, "unit": T("m"), "label": T("v₀²/g"),
                    "how": T("the formula of a throw from the floor without air: L = (v₀²/g)·sin 2θ"),
                    "kind": "closed form"}
        if step_id in ("angles", "air") and ref == "theta_max_vacuum":
            h = float(p["h_m"])
            if h == 0.0:
                return {"value": 45.0, "unit": "°", "label": T("θ* without air"),
                        "how": T("the formula of a throw from the floor without air, L = (v₀²/g)·sin 2θ, is largest "
                                 "where sin 2θ = 1, at θ = 45°"), "kind": "closed form"}
            best, L, n = optimum_angle(p["object"], h, float(p["v0"]), False, 0.1)
            return {"value": best, "unit": "°", "label": T("θ* without air"),
                    "how": T("computed by the engine: the largest range among {n:d} computed flights without air, at "
                             "1° and then at 0.1° steps ({L:.4g} m)", n=n, L=L), "kind": "engine"}
        if step_id == "air" and ref == "theta_max_air":
            obj, h, v0 = p["object"], float(p["h_m"]), float(p["v0"])
            best, L, n = optimum_angle(obj, h, v0, True, 0.1)
            best_c, _L_c, _n_c = optimum_angle(obj, h, v0, True, 0.1, curve=True)
            return {"value": best, "unit": "°", "label": T("θ* in air"),
                    "how": T("computed by the engine with this world's drag model, the constant C_d = {cd:.2f}: the "
                             "largest range among {n:d} computed flights, at 1° and then at 0.1° steps ({L:.4g} m). The "
                             "optimum depends on the drag model: with the measured drag curve the same search gives "
                             "{b:.1f}°. There is no formula for it; without air θ* = 45°",
                             n=n, L=L, cd=CD_SPHERE, b=best_c),
                    "kind": "engine"}
        raise ValueError(T("no law {ref} for the step {step}", ref=str(ref), step=step_id))

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        p = self.params = dict(params)
        self.check_params(p)
        self.obj = p["object"]
        self.comp = p["companion"]
        try:
            self.main = Shot(self.obj, p["h_m"], p["v0"], p["angle_deg"], p["air"])
            if self.comp == "drop":
                self.other = Shot(self.obj, p["h_m"], 0.0, 0.0, p["air"])
            elif self.comp == "vacuum":
                self.other = Shot(self.obj, p["h_m"], p["v0"], p["angle_deg"], False)
            else:
                self.other = None
        except ValueError as e:
            raise Refusal(text_of(e)) from e
        self.sent = {"main": 0, "other": 0}
        self.apex_done = self.main.t_apex is None
        self.landed = {"main": False, "other": self.other is None}

    def engine_modules(self):
        """The modules of this world's physics: the flight, the air's drag model and the one data set it reads, the
        air (``core.data:air``; review R-W F8, D10: no other data set is named). Listed for every world of S03 (the air
        is one switch of the same world; a vacuum run simply has no drag force), so that the atlases' headers do not
        repeat the catalogue's entries per point."""
        return ["core.mechanics.particle", "theories.models.drag_quadratic", "core.data:air"]

    # --- messages -----------------------------------------------------------------------------------------------------
    def _check(self, out, body, cid, label, value, ref, unit, note, tol=TOL, ok=None, info=False, t=None):
        rel = None
        if ok is None and ref is not None and ref != 0 and value is not None:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": t, "id": f"{body}.{cid}", "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "tol": tol, "group": GROUPS[body if body == "main" else self.comp], "note": note}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        out.append((t, d, None))

    def _flight_checks(self, out, body, shot: Shot, t):
        ref = shot.references()
        how = HOW[ref["how"]]
        self._check(out, body, "T", T("flight time T"), shot.T, ref["T"], "s", how, t=t)
        # lengths are compared to the engine's error of the flight's own length scale (max(h, v₀²/g)): a range or a rise
        # much shorter than the flight (a steep or a flat throw) carries the absolute error of the whole flight
        scale = max(shot.h, shot.v0 * shot.v0 / G, 1e-3)

        def tol_len(r):
            return TOL * max(1.0, scale / abs(r)) if r else TOL
        if ref["L"] == 0.0:
            self._check(out, body, "L", T("range L"), shot.L, 0.0, "m", T("a vertical flight lands where it started"),
                        ok=abs(shot.L) <= TOL * scale, t=t)
        else:
            self._check(out, body, "L", T("range L"), shot.L, ref["L"], "m", how, tol=tol_len(ref["L"]), t=t)
        if shot.vy0 > 0.0:  # (a launch that is not upwards has its highest point at the start: nothing to compare)
            self._check(out, body, "H", T("highest point H above the floor"), shot.H, ref["H"], "m", how,
                        tol=tol_len(ref["H"] - shot.h), t=t)
        e = shot.energy_balance()
        self._check(out, body, "energy", T("energy balance E_k + E_p + Q = E₀ along the path"), e, None, "",
                    T("the largest deviation along the path, relative to E₀ (Q is the heat given to the air); the "
                      "engine's stated error is {tol:.0e}", tol=TOL), ok=e <= TOL, t=t)
        val = shot.validity()
        if val is not None:
            share = val["share_outside"]
            # what this check tests: that the path stays where the model uses its constant (review R-E F1), not that
            # the constant equals the measured C_d there; the next row computes that difference
            self._check(out, body, "cd", T("the drag model's range of validity (Re)"), 100.0 * share, None, "%",
                        T("the model uses its constant C_d = {cd:.2f} at Reynolds numbers {lo:.3g}–{hi:.3g}: the share "
                          "of the drag's work done outside them must stay under {lim:.3g} %; Re along the path "
                          "{a:.3g}–{b:.3g}. This tests where the model is used, not how close its constant is to the "
                          "measured C_d (the next row)", lo=RE_RANGE[0], hi=RE_RANGE[1], lim=100.0 * VALID_SHARE,
                          a=val["re_min"], b=val["re_max"], cd=CD_SPHERE), ok=share <= VALID_SHARE, t=t)
            # the second drag model: the same launch with the measured drag curve, computed by the engine (information)
            cf = curve_flight(shot.obj, shot.h, shot.v0, shot.angle)
            sideways = shot.vx0 > 0.0
            got, ref_v = (cf.range, shot.L) if sideways else (cf.flight_time, shot.T)
            pct = 100.0 * (got - ref_v) / ref_v
            self._check(out, body, "cd_curve",
                        T("range with the measured drag curve") if sideways else T("flight time with the measured drag curve"),
                        got, ref_v, "m" if sideways else "s",
                        T("the same throw computed by the engine with the measured drag curve of a smooth sphere "
                          "(Morrison 2016; C_d {c1:.2f}–{c2:.2f} along this path) in place of the constant {cd:.2f}: "
                          "{d:+.2g} %. This is the uncertainty of the drag model itself; the world's ball flies with "
                          "the constant", c1=val["cd_curve_min"], c2=val["cd_curve_max"], cd=CD_SPHERE, d=pct),
                        info=True, t=t)

    def _landing_main(self, out):
        s = self.main
        ld = s.flight.landing
        res = s.flight.results()
        out.append((s.T, {"type": "event", "kind": "landing", "t": s.T,
                          # no measured value in the text: a lab step's instruments measure them (review R-W F8,
                          # D10); the values are the event's data, the readouts and the checks
                          "text": T("the ball lands"),
                          "data": {"T": s.T, "L": s.L, "H": s.H, "x": ld["x"], "v": res["v_land"],
                                   "angle": res["angle_land_deg"]}}, None))
        self._flight_checks(out, "main", s, s.T)

    def _landing_other(self, out):
        o = self.other
        out.append((o.T, {"type": "event", "kind": "companion_landing", "t": o.T,
                          "text": (T("the dropped ball lands") if self.comp == "drop" else
                                   T("the grey ball (vacuum) lands")),
                          "data": {"T": o.T, "L": o.L, "H": o.H, "x": o.flight.landing["x"]}}, None))
        if self.comp == "drop":
            ref = o.references()
            self._check(out, "other", "T", T("fall time of the dropped ball"), o.T, ref["T"], "s",
                        T("by the formula √(2h/g)") if not o.air else HOW["vertical"], t=o.T)
            e = o.energy_balance()
            self._check(out, "other", "energy", T("energy balance E_k + E_p + Q = E₀ along the path"), e, None, "",
                        T("the largest deviation along the path, relative to E₀"), ok=e <= TOL, t=o.T)
            # the heights of the two balls at the same moments, while both fly (the samples are at the same times)
            n = min(self.main.n_until(min(self.main.T, o.T)), o.n_until(min(self.main.T, o.T)))
            dy = float(np.max(np.abs(self.main.ys[:n] - o.ys[:n]))) if n else 0.0
            if not o.air:
                self._check(out, "other", "same_height", T("both balls at the same height at every moment"), dy, None,
                            "m", T("the largest difference of the two balls' heights at the same moments (every "
                                   "1/60 s); in vacuum the vertical motion does not depend on the horizontal one"),
                            ok=dy <= TOL * max(o.h, 1.0), t=o.T)
            else:
                self._check(out, "other", "same_height", T("difference of the two balls' heights"), dy, None, "m",
                            T("in air the thrown ball falls a little more slowly: its drag has an upward part that "
                              "grows with its whole speed"), info=True, t=o.T)
        else:
            self._flight_checks(out, "vacuum", o, o.T)

    def advance(self, t_target):
        out = []  # (time, meta, blobs), emitted in the order of their times
        for key, shot in (("main", self.main), ("other", self.other)):
            if shot is None:
                continue
            n = shot.n_until(min(t_target, shot.T))
            if n > self.sent[key] and (n - self.sent[key] >= CHUNK or shot.T <= t_target):
                out.append((float(shot.ts[n - 1]), {"type": "traj", "t": float(shot.ts[n - 1]), "body": key,
                                                    "i0": self.sent[key], "n": n - self.sent[key]},
                            {"s": shot.rows(self.sent[key], n)}))
                self.sent[key] = n
        if not self.apex_done and self.main.t_apex <= t_target:
            self.apex_done = True
            ap = self.main.flight.apex
            out.append((ap["t"], {"type": "event", "kind": "apex", "t": ap["t"],
                                  "text": T("the ball at the top of its path"),
                                  "data": {"H": ap["y"], "x": ap["x"], "t": ap["t"]}}, None))
        if not self.landed["main"] and self.main.T <= t_target:
            self.landed["main"] = True
            self._landing_main(out)
        if not self.landed["other"] and self.other.T <= t_target:
            self.landed["other"] = True
            self._landing_other(out)
        out.sort(key=lambda x: x[0])
        for _t, meta, blobs in out:
            self.emit(meta, blobs)
        self.t = max(self.t, t_target)

    def next_event_time(self):
        ts = []
        if not self.apex_done:
            ts.append(self.main.t_apex)
        if not self.landed["main"]:
            ts.append(self.main.T)
        if not self.landed["other"]:
            ts.append(self.other.T)
        ts = [x for x in ts if x > self.t]
        return min(ts) if ts else None

    def frame(self):
        """The state now. What is only drawn (the balls' positions and velocities, the drag force, the energies of the
        bars) is rounded (``_r``), far below a pixel; the measurables (range, flight time, highest
        point) are the computed values in full, null until the time reaches them."""
        s, t = self.main, self.t
        st = s.at(t)
        landed = t >= s.T
        meas = {"range": s.L if landed else None, "flight_time": s.T if landed else None,
                "apex_h": s.H if (s.t_apex is not None and t >= s.t_apex) or landed else None,
                "E_k": _r(st["E_k"], 4), "E_p": _r(st["E_p"], 4), "Q": _r(-st["W"], 4)}
        d = {"x": _r(st["x"]), "y": _r(st["y"]), "vx": _r(st["v"][0]), "vy": _r(st["v"][1]), "landed": landed,
             "meas": meas}
        if s.air and not landed:  # the drag force on the ball now (the engine's), N
            F = s.drag.force(t, np.array(st["r"]), np.array(st["v"]))
            d["F_drag"] = [_r(F[0], 4), _r(F[1], 4)]
        if self.other is not None:
            o = self.other.at(t)
            d["other"] = {"x": _r(o["x"]), "y": _r(o["y"]), "landed": t >= self.other.T}
            if self.comp == "vacuum":
                meas["range_vacuum"] = self.other.L if t >= self.other.T else None
        return d, {}

    def max_step(self):
        return None

    def header(self):
        p = self.params
        x0, x1, y1 = self.main.box()
        if self.other is not None:
            a, b, c = self.other.box()
            x0, x1, y1 = min(x0, a), max(x1, b), max(y1, c)
        o = OBJECTS[self.obj]
        meas = [{"id": "range", "label": T("Range"), "unit": "m"},
                {"id": "flight_time", "label": T("Flight time"), "unit": "s"},
                {"id": "apex_h", "label": T("Highest point"), "unit": "m"}]
        if self.comp == "vacuum":
            meas.append({"id": "range_vacuum", "label": T("Range of the grey ball (vacuum)"), "unit": "m"})
        med = medium() if (p["air"] or self.comp == "vacuum") else None
        h = {
            "title": T("Projectile motion: {ball}, {medium}", ball=OBJECT_LABELS[self.obj],
                       medium=T("in air") if p["air"] else T("in vacuum")),
            "text": T("A ball is launched from a height h above the floor at a speed v₀ and an angle θ to the horizontal. "
                      "Its flight is computed in this run by the engine from Newton's second law (with the air's drag "
                      "when the air is on) and shown as the time reaches it; the range, the flight time and the highest "
                      "point are the run's measurements. The closed forms of the flight in vacuum and the hodograph of "
                      "the flight in air are only references in the checks."),
            "scene": {"box": [[x0, 0.0], [x1, y1]]},
            "launcher": {"h": float(p["h_m"]), "angle": float(p["angle_deg"]), "v0": float(p["v0"])},
            "ball": {"id": self.obj, "d": o["d"], "m": o["m"], "label": OBJECT_LABELS[self.obj]},
            "air": bool(p["air"]), "k": self.main.k, "g": G, "weight": o["m"] * G,
            "medium": {"rho": med["rho"], "mu": med["mu"], "T_C": 20.0, "p": 101325.0} if med else None,
            "companion": self.comp, "strobe_every": STROBE_EVERY, "sample_dt": 1.0 / RATE,
            "measurables": meas, "units": {"x": T("m"), "t": T("s")}, "actions": [],
        }
        if p["air"]:
            h["approximations"] = [T("air: a smooth sphere with a constant drag coefficient C_d = {cd:.2f} (a model; the "
                                     "run compares it with the measured drag curve); no spin, no buoyancy", cd=CD_SPHERE)]
        return h, {}


# --- the screens (design §5.3) -----------------------------------------------------------------------------------------
_STOP_FLIGHT = {"event": "landing", "after_s": 0.3, "max_world_s": 12.0}
_HEIGHTS = [round(0.20 + 0.05 * i, 2) for i in range(17)]
_ANGLES_B = list(range(15, 76, 5))
_ANGLES_C = list(range(25, 61, 5))

INSTRUMENTS = {
    "tape": {"kind": "ruler", "label": T("Measuring tape"), "unit": "m", "division": 0.001, "error": 0.0005,
             "reads": "range"},
    # reads only once the grey ball has landed (its own event; review R-P F18)
    "tape_grey": {"kind": "ruler", "label": T("Measuring tape, grey ball"), "unit": "m", "division": 0.001,
                  "error": 0.0005, "reads": "range_vacuum", "event": "companion_landing"},
    # the stand sets the chute's height exactly at its marks (review R-E F4, D2): the heights carry no reading error
    "stand": {"kind": "ruler", "label": T("Height scale of the stand"), "unit": "m", "division": 0.01, "error": 0.0,
              "reads": "control:h_m",
              "error_note": T("the stand sets the chute's height exactly at its marks: the height has no reading error")},
    "protractor": {"kind": "protractor", "label": T("Protractor"), "unit": "°", "division": 1, "error": 0.5,
                   "reads": "control:angle_deg"},
    # the error of a start and a stop by hand: Faux & Godolphin, Am. J. Phys. 87, 110 (2019), from 4304 timekeepers'
    # reaction times: N(0.11, 0.07²) s each, so a start-and-stop interval scatters as N(0, 0.10²) s (checked 2026-11-14)
    "stopwatch": {"kind": "stopwatch", "label": T("Stopwatch"), "unit": "s", "division": 0.01, "error": 0.1,
                  "manual": True,
                  "error_note": T("your reaction: a start and a stop by hand scatter by about 0.1 s")},
}

# The texts of STEPS and WORKSHEET (titles, goals, hints, the FRP names, equipment, questions, answers, notes for the
# teacher) and their translations in locales/ are Site Materials: CC BY-NC-SA 4.0 (LICENSE.md §1 item 8, §9). The code
# and the other data around them stay under LicenseRef-lfphys-Research-1.0.
STEPS = [
    {"id": "heights", "title": T("Height and range"),
     "goal": T("Find how the range of a ball rolling off a chute depends on the height of the chute above the floor. "
               "Check the hypothesis: the higher the launch, the farther the ball flies. Then plot L against √h and "
               "find the slope k. In this part the air is switched off, so the law L ∝ √h can be checked exactly; how "
               "much the air would change the range is computed below, and part 3 studies it."),
     "hint": T("measure the range from the point under the chute's end to the landing mark; plot L against √h"),
     "preset": "chute", "fixed": {"air": False},
     "controls": [{"param": "h_m", "values": _HEIGHTS, "default": 0.6}],
     "instruments": ["stand", "tape", "stopwatch"],
     # the hand-timed flight (review R-W F6): recorded, with no law; its scatter against √(2h/g) is the teaching point
     "columns": [{"id": "h", "label": T("h, m"), "from": "stand"},
                 {"id": "L", "label": T("L, m"), "from": "tape"},
                 {"id": "sqrt_h", "label": T("√h, m^½"), "of": "h", "op": "sqrt"},
                 {"id": "T", "label": T("T, s"), "from": "stopwatch"}],
     "plot": {"x": "sqrt_h", "y": "L", "fit": "line0", "fits": ["line0", "line"]},
     "laws": [{"x": "sqrt_h", "y": "L", "model": "line0", "quantity": "slope", "label": T("k = L / √h"),
               "unit": T("m^½"), "reference": "k_horizontal"}],
     "frame_dt": 1 / 60, "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 3.0},
     "quantize": {"traj.s": "u16"}},
    {"id": "angles", "title": T("Angle and range"),
     "goal": T("Launch the ball from the floor at different angles with the same speed and find the angle of the "
               "largest range. Check the law L = (v₀²/g)·sin 2θ: plot L against sin 2θ. The air is off in this part, "
               "so that the law can be checked exactly."),
     "hint": T("read the angle on the protractor and the range on the tape; the slope of L against sin 2θ is v₀²/g; a "
               "parabola through L against θ gives the angle of the largest range"),
     "preset": "launcher", "fixed": {"v0": 5.0, "air": False},
     "controls": [{"param": "angle_deg", "values": _ANGLES_B, "default": 45}],
     "instruments": ["protractor", "tape"],
     "columns": [{"id": "theta", "label": T("θ, °"), "from": "protractor"},
                 {"id": "L", "label": T("L, m"), "from": "tape"},
                 {"id": "sin2", "label": T("sin 2θ"), "of": "theta", "op": "sin2"}],
     "plot": {"x": "sin2", "y": "L", "fit": "line0", "fits": ["line0", "line", "quadratic"]},
     "laws": [{"x": "sin2", "y": "L", "model": "line0", "quantity": "slope",
               "label": T("the slope of L against sin 2θ"), "unit": T("m"), "reference": "v2_over_g"},
              {"x": "theta", "y": "L", "model": "quadratic", "quantity": "vertex",
               "label": T("θ* of the largest range"), "unit": "°", "reference": "theta_max_vacuum"}],
     "frame_dt": 1 / 60, "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 3.0},
     "quantize": {"traj.s": "u16"}},
    {"id": "air", "title": T("Air moves the maximum (beyond the basic programme)"),
     "goal": T("A light ball is thrown at 20 m/s in air; the grey ball is the same throw computed in vacuum. Measure "
               "both ranges at each angle, fit a parabola to L(θ) and find the angle of the largest range in air."),
     "hint": T("fit the parabola to the points near the top; compare with 45° for the grey ball"),
     "preset": "air_max", "fixed": {"v0": 20.0, "air": True, "companion": "vacuum"},
     "controls": [{"param": "angle_deg", "values": _ANGLES_C, "default": 40}],
     "instruments": ["protractor", "tape", "tape_grey"],
     "columns": [{"id": "theta", "label": T("θ, °"), "from": "protractor"},
                 {"id": "L", "label": T("L, m"), "from": "tape"},
                 {"id": "L_vac", "label": T("L in vacuum, m"), "from": "tape_grey"}],
     "plot": {"x": "theta", "y": "L", "fit": "quadratic", "fits": ["quadratic"]},
     "laws": [{"x": "theta", "y": "L", "model": "quadratic", "quantity": "vertex",
               "label": T("θ* of the largest range in air"), "unit": "°", "reference": "theta_max_air"},
              {"x": "theta", "y": "L_vac", "model": "quadratic", "quantity": "vertex",
               "label": T("θ* of the largest range of the grey ball (vacuum)"), "unit": "°",
               "reference": "theta_max_vacuum"}],
     "frame_dt": 1 / 30, "stop": {"event": "companion_landing", "after_s": 0.3, "max_world_s": 8.0},
     "quantize": {"traj.s": "u16"}},
]
#: the law a step's reference answers when none is named (the step's default plot)
DEFAULT_LAW = {st["id"]: st["laws"][0]["reference"] for st in STEPS}

#: the lab's numbers the worksheet's answers and notes state as fixed text (review R-E F11): each is asserted against
#: the engine in tests/test_s03_physics.py
WORKSHEET = {
    "frp": [
        {"system": "FRP-OOO-2025-base", "programme": T("Russian federal programme, basic level, grades 7–9 (2025)"),
         "grade": 7, "kind": "lab", "part": "heights",
         "name": T("“Research to test the hypothesis: the higher the launch, the farther a ball launched horizontally "
                   "flies”")},
        {"system": "FRP-SOO-2025-base", "programme": T("Russian federal programme, basic level, grades 10–11 (2025)"),
         "grade": 10, "kind": "demonstration",
         "name": T("“Observing the motion of a body thrown at an angle to the horizontal and horizontally”")},
        {"system": "FRP-SOO-2025-base", "programme": T("Russian federal programme, basic level, grades 10–11 (2025)"),
         "grade": 10, "kind": "lab", "part": "heights",
         "name": T("“Studying the motion of a body thrown horizontally”")},
    ],
    "equipment": [T("a chute on a stand and a steel ball, 20 mm; the stand sets the chute's height at its centimetre "
                    "marks"),
                  T("a measuring tape with millimetre divisions"), T("a stopwatch"),
                  T("a ballistic launcher with a protractor"), T("a light ball, 67 mm")],
    "questions": [
        {"q": T("Part 1: the flight lasts 0.2–0.45 s. Why can a hand stopwatch not measure it well, and what do you do "
                "instead?"),
         "answer": T("Starting and stopping a stopwatch by hand scatters by about 0.1 s: from a fifth to a half of the "
                     "whole flight. Measure the range with the tape instead (its error is 0.5 mm); the time follows "
                     "from the height, T = √(2h/g), or from the range, T = L / v₀.")},
        {"q": T("Part 1: you also timed each flight with the hand stopwatch. Compare your times with T = √(2h/g). Why "
                "does the hand-timed T barely help here, and how could the time still be measured?"),
         "answer": T("A start and a stop by hand scatter by about 0.1 s, while the whole flight lasts 0.2–0.45 s and "
                     "neighbouring heights 5 cm apart differ by only 0.01–0.02 s: the readings scatter around √(2h/g) "
                     "and the steps between heights are lost in the scatter. Averaging 10 runs at each height brings "
                     "the scatter down to about 0.03 s: enough to see T grow over the whole range, not to tell "
                     "neighbouring heights apart. Light gates with an electronic timer would measure it to a "
                     "millisecond; here the time is best computed, T = √(2h/g), and compared with the readings.")},
        {"q": T("Part 1: why is the range plotted against √h and not against h?"),
         "answer": T("The fall from the height h lasts T = √(2h/g), and meanwhile the ball moves sideways at the "
                     "constant speed v₀: L = v₀·T = v₀·√(2/g)·√h. So L is proportional to √h: the points of L(√h) lie "
                     "on a straight line through the origin, while L(h) is curved.")},
        {"q": T("Part 1: how do you find the chute's speed v₀ from your graph, and why is that better than measuring "
                "it directly?"),
         "answer": T("The slope is k = v₀·√(2/g), so v₀ = k·√(g/2). The slope uses all the points at once, so the "
                     "errors of single readings average out; measuring a speed of about 1.5 m/s directly would need a "
                     "timer much better than a hand stopwatch.")},
        {"q": T("Part 2: which angles give the same range without air, and why?"),
         "answer": T("θ and 90° − θ, for example 30° and 60°: L = (v₀²/g)·sin 2θ, and sin 2θ = sin(180° − 2θ) = "
                     "sin 2(90° − θ). The steeper throw flies higher and longer, but more slowly sideways.")},
        {"q": T("Part 2: at which angle is the range largest without air?"),
         "answer": T("At 45°: sin 2θ is largest, equal to 1, at 2θ = 90°. The vertex of the parabola fitted to L(θ) "
                     "is at 45° within its error.")},
        {"q": T("Part 3: why does the maximum move below 45° in air?"),
         "answer": T("The air takes speed away all the time, so a long flight loses more. A lower throw spends less "
                     "time in the air and keeps more of its horizontal speed. For this light ball at 20 m/s the engine "
                     "finds the best angle near 42°; for a heavy slow ball the shift is tiny.")},
        {"q": T("Part 3: why does the grey ball (the same throw in vacuum) fly farther?"),
         "answer": T("Without air there is no drag: the horizontal speed stays the same and the ball rises higher, so "
                     "it flies longer and farther.")},
    ],
    "teacher": [
        T("Part 1: the chute's speed is {v} m/s; the students are not told it, they find it from the slope "
          "k = v₀·√(2/g) = {k:.4f} m^½.", v=1.5, k=1.5 * math.sqrt(2.0 / G)),
        T("Parts 1 and 2 are computed without air, so that their laws hold exactly. The virtual tape reads to 1 mm and "
          "the stand sets the heights exactly, so the bench would resolve the air: in part 1 it would shorten the range "
          "by up to 0.54 mm (0.08 %, at 1 m), more than the tape's error of 0.5 mm at the largest heights; in part 2 "
          "the slope would be about 0.5 % lower. Part 3 studies the air."),
        T("Part 3: the best angle in air depends on the drag model. The world's model, a constant drag coefficient "
          "0.47, gives 41.9°, and “Check against the law” compares with it; the measured drag curve of a smooth sphere "
          "gives 42.3°. The parabola is a model of L(θ) near its top only: fitted from 25° to 60° its vertex agrees "
          "with the world's optimum within one error. The grey ball's parabola peaks at 45°."),
        T("Part 3 goes beyond the basic programme of the Russian federal programme (FRP); AP Physics 1 neglects air "
          "resistance; IB A.1 and AQA 3.4.1.4 treat its effect on a projectile qualitatively."),
        T("Grade 7 (the hypothesis “the higher the launch, the farther the ball flies”): part 1 only, with L plotted "
          "against h. The range grows with the height, but not in proportion: four times higher (0.25 m → 1.00 m) "
          "gives twice the range. Square roots come only in grade 8 algebra, so grade 7 does not plot L against √h "
          "and does not check a formula."),
        T("A reading is rounded to the instrument's division; its error is half a division, except the heights, "
          "which the stand sets exactly. The hand stopwatch's error of 0.1 s: Faux and Godolphin, Am. J. Phys. 87, "
          "110 (2019) (4304 timekeepers' reaction times: 0.11 ± 0.07 s each; a start and a stop by hand scatter by "
          "about 0.10 s)."),
        T("The fit takes the errors of both coordinates into account (York's method for a straight line, the "
          "effective variance for the parabola). When the points scatter more than their errors (the reduced χ², χ² "
          "divided by the number of degrees of freedom, above 1), the errors are enlarged accordingly."),
    ],
    # a grade-7 variant of the worksheet (review R-W F7d): part 1 only, L against h, the hypothesis tested by the sign
    # of the change and the shape of the graph (no square roots, no formula); printed by the worksheet's layout
    "variants": [
        {"id": "grade7", "grade": 7, "label": T("Grade 7: the higher the launch, the farther the ball flies"),
         "steps": ["heights"], "plot": {"heights": {"x": "h", "y": "L", "fit": None}},
         "goals": {"heights": T("Find how the range of a ball launched horizontally depends on the launch height. Check "
                                "the hypothesis: the higher the launch, the farther the ball flies. Measure the range at "
                                "different heights, write the results into the table and plot L against h. In this "
                                "experiment the air is switched off.")},
         "questions": [
             {"q": T("Does the range grow with the height of the chute? Use your table."),
              "answer": T("Yes: every greater height gives a greater range, so the hypothesis is confirmed.")},
             {"q": T("Is the graph of L against h a straight line? Compare the ranges from 0.25 m and from 1.00 m."),
              "answer": T("No, it bends: the range grows more and more slowly. Four times higher, from 0.25 m to 1.00 m, "
                          "the range only doubles, from 0.339 m to 0.677 m.")},
             {"q": T("Why does the ball land farther when it starts higher?"),
              "answer": T("It falls for longer, and all that time it keeps moving sideways at the same speed, so it "
                          "covers a longer distance.")},
             {"q": T("Part 1: the flight lasts 0.2–0.45 s. Why can a hand stopwatch not measure it well, and what do "
                     "you do instead?"),
              "answer": T("Starting and stopping a stopwatch by hand scatters by about 0.1 s: from a fifth to a half of "
                          "the whole flight. Measure the range with the tape instead (its error is 0.5 mm); the time "
                          "follows from the height, T = √(2h/g), or from the range, T = L / v₀.")}]},
    ],
}

VIZ = {
    "id": "s03_projectile",
    "title": T("Projectile motion: thrown horizontally and at an angle"),
    "summary": T("A ball thrown from a table or from the floor: the range against the height and the angle, the "
                 "independence of the vertical and the horizontal motion, the 45° maximum and how the air moves it."),
    "purpose": T("The school laboratory work on a computed bench: measure, fill the table, draw the line, compare with "
                 "the law."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "school",
    "section": "mechanics",
    "ui": "school",
    "teaser": T("A dropped ball and a ball thrown sideways land at the same moment."),
    "curriculum": [{"system": "FRP-OOO-2025-base", "grade": 7}, {"system": "FRP-SOO-2025-base", "grade": 10},
                   {"system": "AP1", "unit": 1, "topic": "1.5"}, {"system": "IB-2025", "topic": "A.1"},
                   {"system": "AQA-7408", "section": "3.4.1.4"}],
    "related": [],
    # Watch (review R-W F3, F4; D8): one recording per comparison, so that the screen keeps one scale for all its
    # throws (the view fits the box over every world of the recording and keeps the earlier throws as faded traces):
    # «independence» (three throws from a table, h ≤ 5 m, L ≤ 4.1 m) and «air» (the light ball, a 40 m scale). A
    # caption comes no later than what it describes; the first one holds the start so that it can be read
    "recordings": [
        {"id": "independence", "preset": "story", "seconds": 30, "fps": 20, "speed": 0.1, "seed": 1, "poster": 24,
         "script": [
             {"at": 8.0, "cmd": "new_world", "args": {"preset": "story", "params": {"v0": 4.0}}},
             {"at": 8.0, "cmd": "speed", "args": {"value": 0.1}},
             {"at": 16.0, "cmd": "new_world", "args": {"preset": "story", "params": {"v0": 4.0, "h_m": 5.0}}},
             {"at": 16.0, "cmd": "speed", "args": {"value": 0.1}}],
         "captions": [
             {"at": 0.0, "text": T("Two balls start at the same moment: one is dropped, the other is thrown sideways."),
              "hold": 2.5},
             {"at": 1.0, "text": T("The dots are the positions every 0.1 s. At every moment both balls are at the same "
                                   "height.")},
             {"at": 8.0, "text": T("Twice the sideways speed: the ball lands twice as far, at the same moment as the "
                                   "dropped one.")},
             {"at": 16.0, "text": T("Four times higher: the flight lasts twice as long, and the range doubles: L grows "
                                    "as √h.")}],
         "quantize": {"traj.s": "u16"}},
        {"id": "air", "preset": "air_max", "seconds": 9, "fps": 20, "speed": 0.5, "seed": 1, "poster": 7,
         "captions": [
             {"at": 0.0, "text": T("A light ball is thrown at {v:g} m/s and {a:g}° in air; the grey ball is the same "
                                   "throw computed without air.", v=SCHEMA.presets["air_max"]["params"]["v0"],
                                   a=SCHEMA.presets["air_max"]["params"]["angle_deg"]), "hold": 2.5},
             {"at": 1.5, "text": T("The air takes speed away all the time: the ball in air rises lower and falls "
                                   "short of the grey one.")}],
         "quantize": {"traj.s": "u16"}},
    ],
    "screens": [
        {"id": "watch", "kind": "watch", "recording": "independence", "more": ["air"]},
        {"id": "explore", "kind": "explore", "preset": "field", "fixed": {},
         "controls": [{"param": "h_m", "values": [0.0, 1.0, 2.0, 5.0, 10.0], "default": 1.0},
                      {"param": "v0", "values": [5.0, 10.0, 15.0, 20.0, 25.0], "default": 15.0},
                      {"param": "angle_deg", "values": [float(a) for a in range(0, 91, 5)], "default": 45.0},
                      {"param": "air", "values": [False, True], "default": False}],
         "acts": "next", "time": "flight", "frame_dt": 1 / 30, "stop": _STOP_FLIGHT,
         "quantize": {"traj.s": "u16"},
         "overlays": ["path", "strobe", "v", "v_parts", "forces", "energy"], "traces": 5,
         "readouts": ["range", "flight_time", "apex_h"]},
        {"id": "lab", "kind": "lab", "instruments": INSTRUMENTS, "steps": STEPS, "worksheet": WORKSHEET},
    ],
}
