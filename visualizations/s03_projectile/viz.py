# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""S03: projectile motion, a ball thrown horizontally and at an angle, in vacuum or in air (school, FRP grades 7 and 10).

What the run computes (README.md of this folder has the model in full):
* the ball's flight from its launch (height h above the floor, speed v₀, angle θ to the horizontal, toward the east):
  Newton's second law in a uniform field on the rotating Earth (the Coriolis force at 45.5° N), with the air's real
  forces when the air is on: the measured drag curve of a smooth sphere, the buoyancy and the air carried along, and
  for a ball rolling off the chute the Magnus force of its spin and the spin's extra drag (``engine/shot.py`` over
  ``lfphys.core.mechanics`` and ``lfphys.theories.models``), computed ahead and revealed as the world's time reaches it:
  samples every 1/60 s (``traj``), the launch, the top of the path and the landing as events with their values;
* optionally a second ball: one dropped at the same moment from the same point (the independence of the vertical
  motion), or the same throw in vacuum for comparison (grey; it does not affect the world's ball);
* the run's measurements: the range L, the flight time T, the highest point H, the offset to the right by the Earth's
  rotation, the energy, the heat given to the air;
* checks: T, L, H against the second method (the flight's equations in the velocity's angle), the energy balance
  along the path, where the drag curve and the spinning ball's data hold; and, stated beside them, what each force does
  to the range, the constant drag coefficient of earlier versions as a comparison, the Magnus force's stated band, the
  Earth's rotation, the history force's upper bound.

The screens (designs ``lfphys/sources/explore_2026-11-14_design.md`` §5 and ``explore_EX2_2026-11-18_design.md`` §10):
Watch (the recording ``independence`` with captions, and ``air`` under «More recordings»), Explore (height × speed ×
angle × air on a grid of computed points) and Lab work, a narrow bench (three parts: the range against the height and
against the angle, each with the air on or off, and the maximum in air), nothing hidden and nothing judged, with a task
sheet the teacher may change. No law parameter (school: no modified physics, rule 4): the air is a medium and the
Earth's rotation is the place of the bench, not modifications.
"""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.i18n import T, text_of
from lfphys.theories.models import magnus
from lfphys.theories.models.drag_quadratic import CD_SPHERE, RE_CURVE_MAX
from lfphys.tools.stats import linear_fit

from .engine.shot import (AIR_P, AIR_T_C, LATITUDE, OBJECTS, OMEGA_Z, RATE, STROBE_EVERY, G, Shot, medium,
                          optimum_angle, spin_of, spin_speed_limit, top_speed)


def _r(x: float, digits: int = 6) -> float:
    """A value that is only drawn, to 6 significant digits (the record's size): a position of a 100 m flight to 0.1 mm,
    far below a pixel; the energy bars and the force arrows to 4 (they show 3)."""
    return float(f"{float(x):.{digits}g}")


def _shown(text):
    """A text whose numbers are only shown (a check's note, an event's sentence): its arguments to 6 significant digits,
    beyond every format it is shown with (≤ 5 digits), so that the atlases do not carry 17 random digits per number
    (the checks' and events' values themselves stay in full)."""
    if not isinstance(text, T) or not text.args:
        return text
    return T(text.msgid, **{k: (_r(v) if isinstance(v, float) and math.isfinite(v) else _shown(v))
                            for k, v in text.args.items()})


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
          help=T("Off: the ball flies in vacuum. On: air at 20 °C and 101 325 Pa: the measured drag of a smooth "
                 "sphere, the air's buoyancy and the air the ball carries along; a steel ball rolling off the chute "
                 "also feels the Magnus force of its spin. The bench stands at 45.5° N and throws toward the east, so "
                 "the Earth's rotation acts in both cases.")),
    # the launcher's setting error (review R2-W F5): a launcher set by hand at a mark of its protractor stands within
    # half a division of it, so the lab's launches draw their real angle within ± this bound, seeded by the set-up
    Param("angle_error_deg", T("Setting error of the launcher's angle (bound)"), "float", 0.0, unit="°", min=0.0,
          max=2.0,
          help=T("A launcher set by hand at a mark of its protractor stands within half a division of it. The real "
                 "angle of the launch is drawn within ± this bound for each set-up (seeded by the set-up) and the flight "
                 "is computed at it; it is shown in “How we know this is right”. 0: exactly at the mark.")),
    Param("companion", T("Ball for comparison"), "select", "none", options=COMPANIONS,
          help=T("A second ball: dropped from the same point at the same moment, or the same throw computed in vacuum "
                 "(grey). It does not affect the first ball.")),
], presets={
    "field": {"label": T("A light ball thrown at 45° from a height of 1 m"),
              "params": {"object": "ball67", "h_m": 1.0, "v0": 15.0, "angle_deg": 45.0, "air": False}},
    "chute": {"label": T("A steel ball rolls off a chute on a table"),
              "params": {"object": "steel20", "h_m": 0.6, "v0": 1.5, "angle_deg": 0.0, "air": False}},
    "launcher": {"label": T("A ballistic launcher on the floor"),
                 "params": {"object": "steel20", "h_m": 0.0, "v0": 5.0, "angle_deg": 45.0, "air": False}},
    "air_max": {"label": T("A light ball at 20 m/s in air, and the same throw in vacuum"),
                "params": {"object": "ball67", "h_m": 0.0, "v0": 20.0, "angle_deg": 40.0, "air": True,
                           "companion": "vacuum"}},
    "story": {"label": T("Two balls at the same moment: one dropped, one thrown sideways"),
              "params": {"object": "steel20", "h_m": 1.25, "v0": 2.0, "angle_deg": 0.0, "air": False,
                         "companion": "drop"}},
})

GROUPS = {"main": T("The thrown ball"), "drop": T("The dropped ball"), "vacuum": T("The same throw in vacuum")}
HOW_ANGLE = T("second method: the flight's equations in its velocity's angle, assembled on their own from the same "
              "forces (no integration in time)")
NO_SECOND = T("a vertical flight in air: the engine has no second method for it; the energy balance checks the "
              "integration")
NO_ANGLE = T("the velocity's angle does not turn steadily on this flight: no second method; the energy balance checks "
             "the integration")
PLACE = T("45.5° N")  # the latitude where the WGS 84 normal gravity equals g_n (engine/shot.py LATITUDE: 45.4996°)


def real_angle(params: dict, seed: int) -> float:
    """The launch's real angle, °: the mark ``angle_deg`` plus a setting error drawn uniformly within
    ± ``angle_error_deg`` (review R2-W F5), from a generator seeded by the seed and the set-up together (the parameters as
    sorted JSON, hashed to 64 bits; RULES.md §10: with the seed alone every point of an atlas would draw the same error);
    the mark itself when the bound is 0."""
    err = float(params.get("angle_error_deg", 0.0) or 0.0)
    ang = float(params["angle_deg"])
    if err <= 0.0:
        return ang
    key = int.from_bytes(hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).digest()[:8], "big")
    return ang + float(np.random.default_rng([int(seed), key]).uniform(-err, err))


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
        obj = params["object"]
        if params["air"] and spin_of(obj, h, v0, ang) and top_speed(h, v0) > spin_speed_limit(obj):
            raise Refusal(T("A ball rolling off the chute spins, and the measured data of a spinning ball cover speeds "
                            "up to {v:.1f} m/s for this ball: this flight would reach up to {u:.1f} m/s",
                            v=spin_speed_limit(obj), u=top_speed(h, v0)),
                          T("lower the launch speed or the height, or switch the air resistance off"))

    # --- the bench's computed values (Lab work's «Computed for this bench») ----------------------------------------------
    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference=None):
        """The world's computed values for a lab step (EX2 design §5 F6 (d): data, listed in the drawer, never set
        beside the student's fit), computed when the step's atlas is built: part 1 ``k_horizontal`` k = v₀·√(2/g)
        (formula; the Earth's rotation's effect on the ranges computed per height and stated), ``k_in_air`` (the line
        through the origin over the engine's ranges in air), ``fall_coefficient`` √(2/g); part 2 ``v2_over_g``
        (formula), ``theta_max_vacuum`` (45° from the floor), ``slope_in_air`` and ``theta_max_in_air`` (the engine);
        part 3 ``theta_max_air`` (the engine's scan with this world's forces; the constant C_d's optimum stated beside
        it) and the grey ball's ``theta_max_vacuum``."""
        p = dict(fixed)
        ref = reference or DEFAULT_LAW.get(step_id)
        tape = INSTRUMENTS["tape"]["error"]
        if step_id == "heights" and ref in ("k_horizontal", "k_in_air", "fall_coefficient"):
            v0, obj = float(p["v0"]), p["object"]
            hs = sorted(float(h) for h in (values.get("h_m") or [p["h_m"]]))
            if ref == "k_horizontal":
                rot = [1e3 * (Shot(obj, h, v0, 0.0, False).L - v0 * math.sqrt(2.0 * h / G)) for h in hs]
                how = T("the formula of a horizontal throw in vacuum, L = v₀·√(2h/g), so L = k·√h with k = v₀·√(2/g) "
                        "and v₀ = {v:.2f} m/s. On the rotating Earth the ranges in vacuum are longer by {a:.3f} mm "
                        "at h = {h0:.2f} m to {b:.3f} mm at h = {h1:.2f} m (computed for each height), far below the "
                        "tape's ±{e:.1f} mm", v=v0, a=min(rot), b=max(rot), h0=hs[int(np.argmin(rot))],
                        h1=hs[int(np.argmax(rot))], e=1e3 * tape)
                return {"value": v0 * math.sqrt(2.0 / G), "unit": T("m^½"), "label": T("k = v₀·√(2/g)"), "how": how,
                        "kind": "closed form"}
            if ref == "k_in_air":
                shots = [Shot(obj, h, v0, 0.0, True) for h in hs]
                short = [1e3 * (v0 * math.sqrt(2.0 * h / G) - s.L) for h, s in zip(hs, shots)]
                fit = linear_fit(np.sqrt(hs), np.array([s.L for s in shots]), 0.0, tape, "line0")
                k, sk = float(fit["params"][-1]), float(fit["sigma"][-1])
                over = [h for h, d in zip(hs, short) if d > 1e3 * tape]
                how = T("computed by the engine: in air the ranges are shorter than L = v₀·√(2h/g) by {a:.2f} mm at "
                        "h = {h0:.2f} m to {b:.2f} mm at h = {h1:.2f} m (the drag, the Magnus force of the spin and the "
                        "spin's extra drag, a little less from the buoyancy), more than the tape's ±{e:.1f} mm from "
                        "h = {h2:.2f} m on. The line through the origin over the {n:d} computed ranges has the slope "
                        "{k:.5f} ± {s:.5f} m^½ (errors of the tape), {z:.1f} of its errors below k = v₀·√(2/g)",
                        a=short[0], h0=hs[0], b=short[-1], h1=hs[-1], e=1e3 * tape, h2=over[0] if over else hs[-1],
                        n=len(hs), k=k, s=sk, z=(v0 * math.sqrt(2.0 / G) - k) / sk)
                return {"value": k, "unit": T("m^½"), "label": T("k in air (line through the origin)"), "how": how,
                        "kind": "engine"}
            ts = [Shot(obj, h, v0, 0.0, False).T for h in hs]
            dev = max(abs(t / math.sqrt(2.0 * h / G) - 1.0) for t, h in zip(ts, hs))
            how = T("the fall from the height h lasts T = √(2h/g), and the time from the tape, T = L / v₀, is the same "
                    "in vacuum; the computed flights agree with it to {d:.0e} (the Earth's rotation). A start and a "
                    "stop of a hand stopwatch scatter by about {e:.1f} s, while the flights last {t0:.2f}–{t1:.2f} s",
                    d=dev, e=INSTRUMENTS["stopwatch"]["error"], t0=min(ts), t1=max(ts))
            return {"value": math.sqrt(2.0 / G), "unit": T("s/m^½"), "label": T("T = √(2/g)·√h"), "how": how,
                    "kind": "closed form"}
        if step_id == "angles" and ref in ("v2_over_g", "slope_in_air"):
            v0, obj = float(p["v0"]), p["object"]
            ths = sorted(float(a) for a in (values.get("angle_deg") or [p["angle_deg"]]))
            s2 = np.sin(np.radians(2.0 * np.array(ths)))
            if ref == "v2_over_g":
                rot = [1e3 * (Shot(obj, 0.0, v0, a, False).L - v0 * v0 / G * math.sin(math.radians(2 * a))) for a in ths]
                how = T("the formula of a throw from the floor in vacuum: L = (v₀²/g)·sin 2θ with v₀ = {v:.2f} m/s. On "
                        "the rotating Earth the ranges in vacuum differ from it by {a:+.3f} to {b:+.3f} mm (computed "
                        "for each angle), far below the tape's ±{e:.1f} mm", v=v0, a=min(rot), b=max(rot),
                        e=1e3 * tape)
                return {"value": v0 * v0 / G, "unit": T("m"), "label": T("v₀²/g"), "how": how, "kind": "closed form"}
            Ls = np.array([Shot(obj, 0.0, v0, a, True).L for a in ths])
            # the bench's errors: the tape's on L, the protractor's on θ carried into sin 2θ as the lab's column does
            # (σ² = f′²σ² + ½f″²σ⁴, RULES.md §10)
            sa, rad = INSTRUMENTS["protractor"]["error"], math.pi / 180.0
            d1 = np.abs(2.0 * np.cos(np.radians(2.0 * np.array(ths)))) * rad * sa
            d2 = 4.0 * np.abs(s2) * (rad * sa) ** 2
            fit = linear_fit(s2, Ls, np.sqrt(d1 ** 2 + 0.5 * d2 ** 2), tape, "line0")
            k, sk = float(fit["params"][-1]), float(fit["sigma"][-1])
            how = T("computed by the engine: the line through the origin over the {n:d} ranges in air against "
                    "sin 2θ has the slope {k:.4f} ± {s:.4f} m (errors of the tape and the protractor), {z:.0f} of its "
                    "errors below v₀²/g = {r:.4f} m: in air the law of vacuum does not hold at the tape's resolution",
                    n=len(ths), k=k, s=sk, z=(v0 * v0 / G - k) / sk, r=v0 * v0 / G)
            return {"value": k, "unit": T("m"), "label": T("slope of L against sin 2θ in air"), "how": how,
                    "kind": "engine"}
        if step_id in ("angles", "air") and ref == "theta_max_vacuum":
            h = float(p["h_m"])
            best, L, n = optimum_angle(p["object"], h, float(p["v0"]), False, 0.1)
            if h == 0.0:
                return {"value": 45.0, "unit": "°", "label": T("θ* without air"),
                        "how": T("the formula of a throw from the floor in vacuum, L = (v₀²/g)·sin 2θ, is largest "
                                 "where sin 2θ = 1, at θ = 45°; the engine's search with the Earth's rotation, at 1° "
                                 "and then at 0.1° steps, finds {b:.1f}° too", b=best), "kind": "closed form"}
            return {"value": best, "unit": "°", "label": T("θ* without air"),
                    "how": T("computed by the engine: the largest range among {n:d} computed flights without air, at "
                             "1° and then at 0.1° steps ({L:.4g} m)", n=n, L=L), "kind": "engine"}
        if (step_id, ref) in (("angles", "theta_max_in_air"), ("air", "theta_max_air")):
            obj, h, v0 = p["object"], float(p["h_m"]), float(p["v0"])
            best, L, n = optimum_angle(obj, h, v0, True, 0.1)
            best_c, _L_c, _n_c = optimum_angle(obj, h, v0, True, 0.1, drag="const")
            return {"value": best, "unit": "°", "label": T("θ* in air"),
                    "how": T("computed by the engine with this world's forces (the measured drag curve, the buoyancy "
                             "and the air carried along, the Earth's rotation): the largest range among {n:d} computed "
                             "flights, at 1° and then at 0.1° steps ({L:.4g} m). There is no formula for it; with a "
                             "constant drag coefficient of {cd:.2f} the same search gives {b:.1f}°; without air "
                             "θ* = 45°", n=n, L=L, cd=CD_SPHERE, b=best_c),
                    "kind": "engine"}
        raise ValueError(T("no law {ref} for the step {step}", ref=str(ref), step=step_id))

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        p = self.params = dict(params)
        self.check_params(p)
        self.obj = p["object"]
        self.comp = p["companion"]
        self.angle = real_angle(p, seed)  # the mark, or the launcher's real angle near it (angle_error_deg)
        try:
            self.main = Shot(self.obj, p["h_m"], p["v0"], self.angle, p["air"])
            if self.comp == "drop":
                self.other = Shot(self.obj, p["h_m"], 0.0, 0.0, p["air"])
            elif self.comp == "vacuum":
                self.other = Shot(self.obj, p["h_m"], p["v0"], self.angle, False)
            else:
                self.other = None
        except ValueError as e:
            raise Refusal(text_of(e)) from e
        self.sent = {"main": 0, "other": 0}
        self.launched = False
        self.apex_done = self.main.t_apex is None
        self.landed = {"main": False, "other": self.other is None}

    def engine_modules(self):
        """The modules of this world's physics: the flight (a body in a medium), the rotating Earth, the history force's
        bound, the drag curve, the spinning sphere, and the one data set they read, the air (``core.data:air``; review
        R-W F8, D10: no other data set is named). Listed for every world of S03 (the air is one switch of the same
        world, the spin one launch of it), so that the atlases' headers do not repeat the catalogue's entries per
        point."""
        return ["core.mechanics.particle", "core.mechanics.earth_frame", "core.mechanics.drag",
                "theories.models.drag_quadratic", "theories.models.magnus", "core.data:air"]

    # --- messages -----------------------------------------------------------------------------------------------------
    def _check(self, out, body, cid, label, value, ref, unit, note, tol=TOL, ok=None, info=False, t=None):
        rel = None
        if ok is None and ref is not None and ref != 0 and value is not None:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": t, "id": f"{body}.{cid}", "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "tol": tol, "group": GROUPS[body if body == "main" else self.comp], "note": _shown(note)}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        out.append((t, d, None))

    def _flight_checks(self, out, body, shot: Shot, t):
        ref = shot.references
        scale = ref["scale"]

        def tol_len(r):  # a length much shorter than the flight carries the absolute error of the whole flight
            return TOL * max(1.0, scale / abs(r)) if r else TOL
        if ref["how"] == "angle":
            self._check(out, body, "T", T("flight time T"), shot.T, ref["T"], "s", HOW_ANGLE, t=t)
            self._check(out, body, "L", T("range L"), shot.L, ref["L"], "m", HOW_ANGLE, tol=tol_len(ref["L"]), t=t)
            if shot.vy0 > 0.0:  # (a launch that is not upwards has its highest point at the start: nothing to compare)
                self._check(out, body, "H", T("highest point H above the floor"), shot.H, ref["H"], "m", HOW_ANGLE,
                            tol=tol_len(ref["H"] - shot.h), t=t)
        elif ref["how"] == "vertical":
            rot2 = (OMEGA_Z * shot.T) ** 2
            if ref["T"] is not None:
                note = T("by the formula of a vertical flight in vacuum; the Earth's rotation changes it only at second "
                         "order, (Ω·T)² = {r:.1e}", r=rot2)
                self._check(out, body, "T", T("flight time T"), shot.T, ref["T"], "s", note, tol=ref["tol"], t=t)
                if shot.vy0 > 0.0:
                    self._check(out, body, "H", T("highest point H above the floor"), shot.H, ref["H"], "m", note,
                                tol=ref["tol"] * max(1.0, shot.H / (shot.H - shot.h)), t=t)
            else:
                self._check(out, body, "T", T("flight time T"), shot.T, None, "s", NO_SECOND, t=t)
            self._check(out, body, "drift", T("drift east of the launch point"), shot.x_land, ref["drift"], "m",
                        T("a vertical flight drifts west on the way up and east on the way down (the Earth's "
                          "rotation): {d:+.3g} mm. Second method: the drift by its own first-order equation along the "
                          "same flight, which agrees to the engine's error and to second order, (2Ω·T)² = {r:.1e}",
                          d=1e3 * shot.x_land, r=4.0 * rot2), tol=ref["tol_L"], t=t)
        else:
            self._check(out, body, "T", T("flight time T"), shot.T, None, "s", NO_ANGLE, t=t)
        e = shot.energy_balance()
        note = T("the largest deviation along the path, relative to E₀; Q is the heat given to the air, and the work of "
                 "the air's buoyancy and of the air the ball carries along is counted too; the engine's stated error "
                 "is {tol:.0e}", tol=TOL) if shot.air else \
            T("the largest deviation along the path, relative to E₀ (the Coriolis force does no work); the engine's "
              "stated error is {tol:.0e}", tol=TOL)
        self._check(out, body, "energy", T("energy balance E_k + E_p + Q = E₀ along the path"), e, None, "", note,
                    ok=e <= TOL, t=t)

    def _air_checks(self, out, s: Shot, t):
        """The main ball in air: where the drag curve and the spinning ball's data hold, and the comparisons (info)."""
        val = s.validity
        self._check(out, "main", "curve", T("the drag curve covers this flight"), val["re_max"], None, "",
                    T("Reynolds numbers {a:.3g}–{b:.3g} along the path; the measured drag curve of a smooth sphere "
                      "(Morrison 2016) holds up to {m:.0e} and gives C_d = {c1:.3f}–{c2:.3f} here", a=val["re_min"],
                      b=val["re_max"], m=RE_CURVE_MAX, c1=val["cd_min"], c2=val["cd_max"]),
                    ok=val["re_max"] <= RE_CURVE_MAX, t=t)
        if s.spin:
            self._check(out, "main", "spin", T("the spinning ball's data cover this flight"), val["re_max"], None, "",
                        T("the ball rolls off the chute with {w:.0f} rad/s of topspin: Reynolds numbers {a:.3g}–{b:.3g}, "
                          "spin ratio S = Rω/v {s1:.2f}–{s2:.2f}. The Magnus force and the spin's extra drag are "
                          "measured (Zhou et al. 2022) up to Re 3 472; above it, to {m:.0e}, the model carries its "
                          "stated band", w=s.spin, a=val["re_min"], b=val["re_max"], s1=val["s_min"], s2=val["s_max"],
                          m=magnus.RE_MAX), ok=val["re_max"] <= magnus.RE_MAX and val["s_max"] <= magnus.S_MAX, t=t)
        sh = s.shares
        if s.spin:
            note = T("against the same throw in vacuum: {t:+.3f} mm in all; the drag {d:+.3f} mm, the buoyancy and the "
                     "air carried along {f:+.3f} mm, the Magnus force of the spin {l:+.3f} mm, the spin's extra drag "
                     "{s:+.3f} mm (each on its own, on a non-rotating Earth)", t=1e3 * sh["total"], d=1e3 * sh["drag"],
                     f=1e3 * sh["fluid"], l=1e3 * sh["lift"], s=1e3 * sh["spin_drag"])
        elif abs(sh["total"]) < 0.1:
            note = T("against the same throw in vacuum: {t:+.3f} mm in all; the drag {d:+.3f} mm, the buoyancy and the "
                     "air carried along {f:+.3f} mm (each on its own, on a non-rotating Earth)", t=1e3 * sh["total"],
                     d=1e3 * sh["drag"], f=1e3 * sh["fluid"])
        else:
            note = T("against the same throw in vacuum: {t:+.4g} m in all; the drag {d:+.4g} m, the buoyancy and the "
                     "air carried along {f:+.3g} m (each on its own, on a non-rotating Earth)", t=sh["total"],
                     d=sh["drag"], f=sh["fluid"])
        self._check(out, "main", "air", T("what the air does to the range"), sh["total"], None, "m", note, info=True,
                    t=t)
        if s.band is not None:
            lo, hi = sorted(s.band.values())
            self._check(out, "main", "band", T("range within the Magnus force's stated band"), s.L, None, "m",
                        T("the lift of a spinning sphere is measured only up to Re 3 472: with the measured data's "
                          "spread (C_L × {a:.3f}–{b:.3f}, the spin's extra drag × {c:.3f}–{d:.3f}) the range lies "
                          "between {lo:.5f} and {hi:.5f} m (the model: {L:.5f} m). The spin's decay in flight is not "
                          "computed: at most 7 %, at most 0.010 mm on the range", a=magnus.LIFT_BAND[0],
                          b=magnus.LIFT_BAND[1], c=magnus.DRAG_BAND[0], d=magnus.DRAG_BAND[1], lo=lo, hi=hi, L=s.L),
                        info=True, t=t)
        cc = s.constant_cd
        sideways_throw = not s.vertical
        got, ref_v = (cc["L"], s.L) if sideways_throw else (cc["T"], s.T)
        if sideways_throw:
            note = T("the same throw with the constant drag coefficient C_d = {cd:.2f} of earlier versions in place of "
                     "the measured drag curve (the other forces unchanged): {d:+.4g} mm ({p:+.2g} %)", cd=CD_SPHERE,
                     d=1e3 * (got - ref_v), p=100.0 * (got - ref_v) / ref_v)
        else:
            note = T("the same throw with the constant drag coefficient C_d = {cd:.2f} of earlier versions in place of "
                     "the measured drag curve (the other forces unchanged): {d:+.4g} s ({p:+.2g} %)", cd=CD_SPHERE,
                     d=got - ref_v, p=100.0 * (got - ref_v) / ref_v)
        self._check(out, "main", "cd_const",
                    T("range with a constant drag coefficient") if sideways_throw
                    else T("flight time with a constant drag coefficient"),
                    got, ref_v, "m" if sideways_throw else "s", note, info=True, t=t)
        hb = s.history
        self._check(out, "main", "history", T("the history force's upper bound"), hb["dL_bound"], None, "m",
                    T("the force of the air's unsteady flow around the accelerating ball is not part of the flight (no "
                      "established law at these Reynolds numbers); Basset's kernel bounds it from above: at most "
                      "{b:.2g} mm on the landing, at most {r:.2g} of the weight", b=1e3 * hb["dL_bound"],
                      r=hb["B_over_weight"]), info=True, t=t)

    def _rotation_check(self, out, s: Shot, t):
        """The Earth's rotation on the main ball (info): along the throw (east) and to the right (south)."""
        u = s.unrotated
        along = s.x_land - (u["L"] if s.vx0 >= 0.0 else -u["L"])
        self._check(out, "main", "rotation", T("the Earth's rotation"), 1e3 * s.side["right"], None, "mm",
                    T("at {place}, throwing toward the east: the Coriolis force moves the landing {a:+.3g} mm to the "
                      "east and {r:.3g} mm to the south, to the right (by its first-order equation along the flight); "
                      "its share on the air carried along, at most 3·10⁻³ of it, is left out", place=PLACE,
                      a=1e3 * along, r=1e3 * s.side["right"]), info=True, t=t)

    def _launch(self, out):
        s = self.main
        err = float(self.params.get("angle_error_deg", 0.0) or 0.0)
        if err > 0.0:
            mark = float(self.params["angle_deg"])
            out.append((0.0, {"type": "check", "t": 0.0, "id": "main.angle", "label": T("the launcher's real angle"),
                              "value": self.angle, "ref": mark, "unit": "°", "rel": None, "tol": err,
                              "group": GROUPS["main"], "info": True,
                              "note": _shown(T("set by hand at the {m:g}° mark of its protractor, the launcher stands "
                                               "within ±{e:g}° of it: this set-up's angle, drawn within that bound, is "
                                               "{a:.2f}°, {d:+.2f}° from the mark; the flight is computed at it", m=mark, e=err, a=self.angle,
                                               d=self.angle - mark))}, None))
        if s.spin:
            text = T("the ball leaves the chute at {v:.2f} m/s toward the east, rolling: {w:.0f} rad/s of topspin",
                     v=s.v0, w=s.spin)
        elif s.v0 > 0.0 and err > 0.0:
            text = T("the ball is launched at {v:.2f} m/s and {a:.2f}° toward the east (the launcher set at the {m:g}° "
                     "mark)", v=s.v0, a=s.angle, m=float(self.params["angle_deg"]))
        elif s.v0 > 0.0:
            text = T("the ball is launched at {v:.2f} m/s and {a:g}° toward the east", v=s.v0, a=s.angle)
        else:
            text = T("the ball is let go")
        out.append((0.0, {"type": "event", "kind": "launch", "t": 0.0, "text": _shown(text),
                          "data": {"v0": s.v0, "angle": s.angle, "h": s.h, "spin": s.spin}}, None))

    def _landing_main(self, out):
        s = self.main
        ld = s.flight.landing
        res = s.flight.results()
        out.append((s.T, {"type": "event", "kind": "landing", "t": s.T,
                          "text": _shown(T("the ball lands: range {L:.4g} m, flight time {T:.4g} s", L=s.L, T=s.T)),
                          "data": {"T": s.T, "L": s.L, "H": s.H, "x": ld["x"], "v": res["v_land"],
                                   "angle": res["angle_land_deg"], "right": s.side["right"]}}, None))
        self._flight_checks(out, "main", s, s.T)
        if s.air:
            self._air_checks(out, s, s.T)
        self._rotation_check(out, s, s.T)

    def _landing_other(self, out):
        o = self.other
        text = T("the dropped ball lands: flight time {T:.4g} s", T=o.T) if self.comp == "drop" else \
            T("the grey ball (vacuum) lands: range {L:.4g} m, flight time {T:.4g} s", L=o.L, T=o.T)
        out.append((o.T, {"type": "event", "kind": "companion_landing", "t": o.T, "text": _shown(text),
                          "data": {"T": o.T, "L": o.L, "H": o.H, "x": o.flight.landing["x"]}}, None))
        self._flight_checks(out, "other", o, o.T)
        if self.comp == "drop":
            # the heights of the two balls at the same moments, while both fly (the samples are at the same times)
            n = min(self.main.n_until(min(self.main.T, o.T)), o.n_until(min(self.main.T, o.T)))
            diff = self.main.ys[:n] - o.ys[:n]
            dy = float(diff[int(np.argmax(np.abs(diff)))]) if n else 0.0  # the largest difference, with its sign
            note = T("in vacuum the vertical motion does not depend on the horizontal one; on the rotating Earth the "
                     "Coriolis force lifts the ball thrown toward the east a little (the Eötvös effect): at most "
                     "{d:.3f} mm while both fly", d=1e3 * dy) if not o.air else \
                T("in air the thrown ball also feels the upward part of its drag, which grows with its whole speed, and "
                  "a ball rolling off the chute the Magnus force of its topspin, which pushes it down: while both fly, "
                  "its height differs from the dropped one's by up to {d:+.3f} mm (plus: higher)", d=1e3 * dy)
            self._check(out, "other", "same_height", T("how much higher the thrown ball is"), dy, None, "m", note,
                        info=True, t=o.T)

    def advance(self, t_target):
        out = []  # (time, meta, blobs), emitted in the order of their times
        if not self.launched:
            self.launched = True
            self._launch(out)
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
                                  "text": _shown(T("the ball at the top of its path: H = {H:.4g} m", H=ap["y"])),
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
        """The state now. What is only drawn (the balls' positions and velocities, the air's forces, the energies of
        the bars) is rounded (``_r``), far below a pixel; the measurables (range, flight time, highest point, the
        offset to the right) are the computed values in full, null until the time reaches them."""
        s, t = self.main, self.t
        st = s.at(t)
        landed = t >= s.T
        meas = {"range": s.L if landed else None, "flight_time": s.T if landed else None,
                "apex_h": s.H if (s.t_apex is not None and t >= s.t_apex) or landed else None,
                "sideways": 1e3 * s.side["right"] if landed else None, "p_air": AIR_P / 1e3 if s.air else 0.0,
                "E_k": _r(st["E_k"], 4), "E_p": _r(st["E_p"], 4), "Q": _r(s.heat(t), 4)}
        d = {"x": _r(st["x"]), "y": _r(st["y"]), "vx": _r(st["v"][0]), "vy": _r(st["v"][1]), "landed": landed,
             "meas": meas}
        if s.air and not landed:  # the air's forces on the ball now (the engine's), N
            F = s.force_at(s.drag, t)
            d["F_drag"] = [_r(F[0], 4), _r(F[1], 4)]
            if s.lift is not None:
                F = s.force_at(s.lift, t)
                d["F_lift"] = [_r(F[0], 4), _r(F[1], 4)]
        if self.other is not None:
            o = self.other.at(t)
            d["other"] = {"x": _r(o["x"]), "y": _r(o["y"]), "landed": t >= self.other.T}
            if self.comp == "vacuum":
                meas["range_vacuum"] = self.other.L if t >= self.other.T else None
        return d, {}

    def max_step(self):
        return None

    def _air_force_max(self):
        """The largest air force (drag or Magnus) on the thrown ball along its computed flight (its samples and its
        landing), N; None in vacuum. The view draws the air's arrows on a scale of their own chosen from it, so that
        they stay visible next to the weight (V52 (f)): only the drawing's scale, the arrows are the frames' computed
        forces."""
        s = self.main
        if not s.air:
            return None
        ts = list(s.ts) + [s.T]
        best = 0.0
        for f in [x for x in (s.drag, s.lift) if x is not None]:
            best = max(best, max(float(np.hypot(*s.force_at(f, tk))) for tk in ts))
        return best

    def header(self):
        p = self.params
        x0, x1, y1 = self.main.box()
        if self.other is not None:
            a, b, c = self.other.box()
            x0, x1, y1 = min(x0, a), max(x1, b), max(y1, c)
        o = OBJECTS[self.obj]
        meas = [{"id": "range", "label": T("Range"), "unit": "m"},
                {"id": "flight_time", "label": T("Flight time"), "unit": "s"},
                {"id": "apex_h", "label": T("Highest point"), "unit": "m"},
                {"id": "sideways", "label": T("To the right, Earth's rotation"), "unit": "mm"},
                {"id": "p_air", "label": T("Air pressure"), "unit": "kPa"}]
        if self.comp == "vacuum":
            meas.append({"id": "range_vacuum", "label": T("Range of the grey ball (vacuum)"), "unit": "m"})
        rho_mu = None
        if p["air"] or self.comp == "vacuum":
            m = medium()
            rho_mu = {"rho": m["rho"], "mu": m["mu"], "T_C": AIR_T_C, "p": AIR_P}
        s = self.main
        h = {
            "title": T("Projectile motion: {ball}, {medium}", ball=OBJECT_LABELS[self.obj],
                       medium=T("in air") if p["air"] else T("in vacuum")),
            "text": T("A ball is launched from a height h above the floor at a speed v₀ and an angle θ to the horizontal, "
                      "toward the east, at 45.5° N. Its flight is computed in this run by the engine from Newton's "
                      "second law with the Earth's rotation and, when the air is on, the air's drag, buoyancy and the "
                      "air the ball carries along, and the Magnus force of a ball rolling off the chute; it is shown as "
                      "the time reaches it. The range, the flight time and the highest point are the run's "
                      "measurements; a second method of computing the flight is only the reference of the checks."),
            "scene": {"box": [[x0, 0.0], [x1, y1]]},
            # the angle the ball is launched at (the mark, or the launcher's real angle near it) and the mark it is set at
            "launcher": {"h": float(p["h_m"]), "angle": float(self.angle), "mark": float(p["angle_deg"]),
                         "v0": float(p["v0"]), "chute": bool(s.spin), "spin": s.spin},
            "ball": {"id": self.obj, "d": o["d"], "m": o["m"], "label": OBJECT_LABELS[self.obj]},
            "air": bool(p["air"]), "g": G, "weight": o["m"] * G, "drag_max": self._air_force_max(),
            "medium": rho_mu, "earth": {"latitude": LATITUDE, "azimuth": 90.0},
            "companion": self.comp, "strobe_every": STROBE_EVERY, "sample_dt": 1.0 / RATE,
            "measurables": meas, "units": {"x": T("m"), "t": T("s")}, "actions": [],
            "approximations": [T("the Earth's rotation: the Coriolis force in the throw's plane, the offset to the side "
                                 "by its first-order equation")],
        }
        if p["air"]:
            h["approximations"].append(T("air: the measured drag curve of a smooth sphere, the buoyancy and the air "
                                         "carried along (C_A = ½); a ball rolling off the chute: the Magnus force from "
                                         "measured data, with a stated band; the history force left out (its upper "
                                         "bound in the checks)"))
        return h, {}


# --- the screens (EX1 design §5, EX2 design §10) -----------------------------------------------------------------------
_STOP_FLIGHT = {"event": "landing", "after_s": 0.3, "max_world_s": 12.0}
_HEIGHTS = [round(0.20 + 0.05 * i, 2) for i in range(17)]
_ANGLES_B = list(range(15, 76, 5))
_ANGLES_C = list(range(20, 71, 5))
_AIR = {"param": "air", "values": [False, True], "default": False}

INSTRUMENTS = {
    "tape": {"kind": "ruler", "label": T("Measuring tape"), "unit": "m", "division": 0.001, "error": 0.0005,
             "reads": "range"},
    # reads only once the grey ball has landed (its own event; review R-P F18)
    "tape_grey": {"kind": "ruler", "label": T("Measuring tape, grey ball"), "unit": "m", "division": 0.001,
                  "error": 0.0005, "reads": "range_vacuum", "event": "companion_landing"},
    # the stand sets the chute's height exactly at its marks (review R-E F4, D2): the heights carry no reading error
    "stand": {"kind": "ruler", "label": T("Height scale of the stand"), "unit": "m", "division": 0.01, "error": 0.0,
              "reads": "control:h_m",
              "error_note": T("the stand sets the chute's height at its marks")},
    # the launcher is set by hand at a mark and stands within half a division of it: the lab's steps draw its real angle
    # within that bound for each set-up (``angle_error_deg``, review R2-W F5), so the declared error describes the data
    "protractor": {"kind": "protractor", "label": T("Protractor"), "unit": "°", "division": 1, "error": 0.5,
                   "reads": "control:angle_deg",
                   "error_note": T("the launcher, set by hand at a mark, stands within half a division of it")},
    # the error of a start and a stop by hand: Faux & Godolphin, Am. J. Phys. 87, 110 (2019), from 4304 timekeepers'
    # reaction times: N(0.11, 0.07²) s each, so a start-and-stop interval scatters as N(0, 0.10²) s (checked 2026-11-14)
    "stopwatch": {"kind": "stopwatch", "label": T("Stopwatch"), "unit": "s", "division": 0.01, "error": 0.1,
                  "manual": True,
                  "error_note": T("your reaction: a start and a stop by hand scatter by about 0.1 s")},
    # the chamber's air: open to the room (101.3 kPa) or pumped out (0): a row of the table says which; the player
    # translates the unit  i18n-msgids: "kPa"
    "manometer": {"kind": "readout", "label": T("Manometer of the chamber"), "unit": "kPa", "division": 0.1,
                  "error": 0.0, "reads": "p_air",
                  "error_note": T("the chamber is open to the room's air or pumped out")},
}

# The texts of STEPS and WORKSHEET (titles, goals, hints, the FRP names, the task sheet's goal, bench, procedure, record
# and variants) and their translations in locales/ are Site Materials: CC BY-NC-SA 4.0 (LICENSE.md §1 item 8, §9). The
# code and the other data around them stay under LicenseRef-lfphys-Research-1.0.
STEPS = [
    {"id": "heights", "title": T("Height and range"),
     "goal": T("A steel ball rolls off a chute at 1.5 m/s. Find how its range depends on the height of the chute above "
               "the floor, and the chute's speed from the slope of L against √h. With the air off the ball flies in "
               "vacuum; switch the air on to see whether the tape notices it."),
     "hint": T("L against √h through the origin has the slope k = v₀·√(2/g); L against h is a curve; compare the "
               "stopwatch's T with T = L / v₀; keep the rows with the air on apart from those without it"),
     "preset": "chute", "fixed": {},
     "controls": [{"param": "h_m", "values": _HEIGHTS, "default": 0.6}, dict(_AIR)],
     "instruments": ["stand", "tape", "stopwatch", "manometer"],
     # the hand-timed flight (review R-W F6): recorded beside the time from the tape, T = L / v₀
     "columns": [{"id": "h", "label": T("h, m"), "from": "stand"},
                 {"id": "L", "label": T("L, m"), "from": "tape"},
                 {"id": "sqrt_h", "label": T("√h, m^½"), "of": "h", "op": "sqrt"},
                 {"id": "T", "label": T("T, s"), "from": "stopwatch"},
                 {"id": "T_L", "label": T("T = L / v₀, s"), "expr": "L / 1.5"},
                 {"id": "p", "label": T("p, kPa"), "from": "manometer"}],
     "plot": {"x": "sqrt_h", "y": "L", "fit": "line0", "fits": ["line0", "line"]},
     "laws": [{"x": "sqrt_h", "y": "L", "model": "line0", "quantity": "slope", "label": T("k = L / √h"),
               "unit": T("m^½"), "reference": "k_horizontal"},
              {"x": "sqrt_h", "y": "L", "model": "line0", "quantity": "slope",
               "label": T("k in air (line through the origin)"), "unit": T("m^½"), "reference": "k_in_air"},
              {"x": "sqrt_h", "y": "T_L", "model": "line0", "quantity": "slope", "label": T("T / √h"),
               "unit": T("s/m^½"), "reference": "fall_coefficient"}],
     "frame_dt": 1 / 60, "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 3.0},
     "quantize": {"traj.s": "u16"}},
    {"id": "angles", "title": T("Angle and range"),
     "goal": T("A ballistic launcher on the floor throws the steel ball at 5 m/s. Find the angle of the largest range "
               "and check the law L = (v₀²/g)·sin 2θ by plotting L against sin 2θ, first with the air off, then with "
               "the air on."),
     "hint": T("the slope of L against sin 2θ is v₀²/g in vacuum; a parabola through L against θ gives the angle of the "
               "largest range; keep the rows with the air on apart from those without it"),
     "preset": "launcher", "fixed": {"v0": 5.0, "angle_error_deg": 0.5},
     "controls": [{"param": "angle_deg", "values": _ANGLES_B, "default": 45}, dict(_AIR)],
     "instruments": ["protractor", "tape", "manometer"],
     "columns": [{"id": "theta", "label": T("θ, °"), "from": "protractor"},
                 {"id": "L", "label": T("L, m"), "from": "tape"},
                 {"id": "sin2", "label": T("sin 2θ"), "of": "theta", "op": "sin2"},
                 {"id": "p", "label": T("p, kPa"), "from": "manometer"}],
     "plot": {"x": "sin2", "y": "L", "fit": "line0", "fits": ["line0", "line", "quadratic"]},
     "laws": [{"x": "sin2", "y": "L", "model": "line0", "quantity": "slope",
               "label": T("the slope of L against sin 2θ"), "unit": T("m"), "reference": "v2_over_g"},
              {"x": "theta", "y": "L", "model": "quadratic", "quantity": "vertex",
               "label": T("θ* of the largest range"), "unit": "°", "reference": "theta_max_vacuum"},
              {"x": "sin2", "y": "L", "model": "line0", "quantity": "slope",
               "label": T("slope of L against sin 2θ in air"), "unit": T("m"), "reference": "slope_in_air"},
              {"x": "theta", "y": "L", "model": "quadratic", "quantity": "vertex",
               "label": T("θ* of the largest range in air"), "unit": "°", "reference": "theta_max_in_air"}],
     "frame_dt": 1 / 60, "stop": {"event": "landing", "after_s": 0.2, "max_world_s": 3.0},
     "quantize": {"traj.s": "u16"}},
    {"id": "air", "title": T("Air moves the maximum (beyond the basic programme)"),
     "goal": T("A light ball is thrown at 20 m/s in air; the grey ball is the same throw computed in vacuum. Measure "
               "both ranges at each angle and find the angle of the largest range in air from a parabola through L "
               "against θ."),
     "hint": T("a parabola describes L(θ) only near its top: fit it to the points near the largest range, then to all "
               "of them, and compare; the grey ball's parabola peaks at 45°"),
     "preset": "air_max", "fixed": {"v0": 20.0, "air": True, "companion": "vacuum", "angle_error_deg": 0.5},
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
#: the law a step's reference answers when none is named (the step's first law)
DEFAULT_LAW = {st["id"]: st["laws"][0]["reference"] for st in STEPS}

#: the task sheet (EX2 design §1.4, §5 F8): what the bench is, one suggested procedure (the ways named in it), what to
#: record and hand in; no questions, answers or teacher's pages (the bench is open and the teacher judges). Every number
#: it states is asserted against the engine in tests/test_s03_physics.py
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
    "goal": T("Study the flight of a ball launched horizontally and at an angle: how its range depends on the height and "
              "on the angle of the launch, and what the air changes."),
    "bench": [
        T("Part 1: a steel ball (20 mm, 32.9 g) rolls off a chute at 1.5 m/s; the stand sets the chute's end at a "
          "height of 0.20–1.00 m at its marks. Part 2: a ballistic launcher on the floor throws the same ball at "
          "5 m/s at 15–75°. Part 3: a light ball (67 mm, 58 g) thrown at 20 m/s at 20–70°, and beside it the same "
          "throw computed in vacuum (the grey ball)."),
        T("The bench stands in a chamber that can be pumped out: in parts 1 and 2 the air can be switched off (the "
          "manometer reads 0 kPa) or on (room air at 20 °C, 101.3 kPa)."),
        T("The bench stands at 45.5° N, and the balls fly toward the east: the Earth's rotation moves the landing by "
          "up to a tenth of a millimetre in parts 1 and 2 and by millimetres in part 3, as “How we know this is right” "
          "shows."),
    ],
    "procedure": [
        T("Part 1, air off: for each height launch the ball, read the range on the tape and time the flight with the "
          "stopwatch. Plot L against √h and fit a line through the origin: its slope k gives the chute's speed, "
          "v₀ = k·√(g/2). Plotting L against h instead gives a curve; comparing the stopwatch's T with T = L / v₀ "
          "shows how much a hand stopwatch scatters."),
        T("Part 1, air on: clear the table (or delete the rows without air), measure again and compare the ranges and "
          "the slope with those without air."),
        T("Part 2: with the air off, launch at each angle, plot L against sin 2θ and fit a line through the origin: "
          "its slope is v₀²/g. Find the angle of the largest range from the table and from a parabola through L "
          "against θ. Then measure with the air on and compare the slope with v₀²/g."),
        T("Part 3: measure L and the grey ball's range at each angle. Fit a parabola to L against θ through the points "
          "near the largest range, then through all of them, and compare the two vertices with each other and with "
          "the grey ball's."),
    ],
    "record": [
        T("the table of each part with every reading and its error"),
        T("each plot with its fit: the model, the points used, the parameters with their errors"),
        T("the chute's speed from part 1, the slope from part 2 and the angle of the largest range from parts 2 and 3, "
          "each with its error"),
        T("your conclusion for each part: what the measurements show, and how the ways of processing them differ"),
    ],
    "record_rows": 17,
    # the teacher's tasks, computed in the atlases (EX2 §5 F8 (b)): «&variant=<id>» preselects the controls; nothing
    # is locked
    "variants": [
        {"id": "grade7", "grade": 7, "label": T("Grade 7: the higher the launch, the farther the ball flies"),
         "steps": ["heights"], "values": {"heights": {"air": False}},
         "text": {"goal": T("Find how the range of a ball launched horizontally depends on the launch height. Check the "
                            "hypothesis: the higher the launch, the farther the ball flies."),
                  "procedure": [T("With the air off, launch the ball from each height, read the range on the tape and "
                                  "write it into the table. Plot L against h without a line, and compare the ranges "
                                  "from 0.25 m and from 1.00 m: four times higher, how much farther?")],
                  "record": [T("the table of heights and ranges with their errors"),
                             T("the plot of L against h"),
                             T("your conclusion: does the range grow with the height, and in proportion to it?")]}},
        {"id": "air", "grade": 10, "label": T("Grade 10: the same bench in air"),
         "steps": ["heights", "angles"], "values": {"heights": {"air": True}, "angles": {"air": True}},
         "text": {"goal": T("Do parts 1 and 2 with the air on, as a real bench in a room is, and find whether the "
                            "laws of a flight in vacuum hold at the tape's resolution."),
                  "procedure": [T("Part 1 with the air on: plot L against √h, fit a line through the origin, and find "
                                  "v₀ = k·√(g/2). Then measure the same heights with the air off and compare."),
                                T("Part 2 with the air on: plot L against sin 2θ, fit a line through the origin and "
                                  "compare its slope with v₀²/g; then do the same with the air off.")]}},
    ],
}

VIZ = {
    "id": "s03_projectile",
    "title": T("Projectile motion: thrown horizontally and at an angle"),
    "summary": T("A ball thrown from a table or from the floor: the range against the height and the angle, the "
                 "independence of the vertical and the horizontal motion, the 45° maximum and how the air moves it."),
    "purpose": T("The school laboratory work on a computed bench: set it up, measure, fill the table and plot it; the "
                 "teacher judges the results."),
    "version": "2.0",
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
                                   "height, to {d:.2f} mm: the Earth's rotation lifts the ball thrown east a little.",
                                   d=0.03)},
             # the landings' difference from the run (tests/test_s03_screens.py; review R2-W F10)
             {"at": 8.0, "text": T("Twice the sideways speed: the ball lands twice as far, only {d:.1f} µs after the "
                                   "dropped one, held up by the Earth's rotation.", d=10.5)},
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
         "readouts": ["range", "flight_time", "apex_h", "sideways"]},
        {"id": "lab", "kind": "lab", "instruments": INSTRUMENTS, "steps": STEPS, "worksheet": WORKSHEET},
    ],
}
