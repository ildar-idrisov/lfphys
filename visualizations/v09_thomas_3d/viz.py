# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v09: Thomas-Wigner precession in 3-D (a wrapper over lfphys; plan P14.1, on the plan's P9 and P10).

A craft starts at rest and flies a manoeuvre: burns and turns of its thrust given in its own frame. Its gyroscopes are
carried without rotation (Fermi-Walker), and when the craft is back at rest they are turned: the holonomy of the loop
its velocity ran in velocity space (Thomas precession; for two boosts the Wigner rotation). The run computes the
manoeuvre exactly (lfphys.core.spin_transport), the rotation in SO(3) and the spinor in SU(2) (which tells a turn by
2 pi from none), the fuel spent (the total rapidity), and compares the rotation with closed forms where they exist
(loops in a plane: Gauss-Bonnet, the enclosed area of velocity space; Thomas's 2 pi (gamma - 1) per revolution) and
with the isoperimetric bound of the hyperbolic plane at the same fuel (a theorem for planar loops; a comparison line
for the others).

The 3-D scene is velocity space (the ball of velocities, light at its boundary) or ordinary space (the trajectory, in
light-years). In velocity space a field fills the ball: the gyroscopes' rotation after the three-burn loop
rest -> u -> w -> rest for every w (u fixed), or that rotation per the planar bound at the same fuel; the slice planes
cut it (up to three, any orientation, computed by the run and checked against Gauss-Bonnet at points of each plane).
Time is lab time (the world clock counts seconds, as every world does; the manoeuvre lasts years); the path, the
gyroscopes and the result are revealed as the run's time reaches them.
"""

from __future__ import annotations

import math
import re

import numpy as np

from lfphys.core import geometry as G
from lfphys.core import lorentz as LZ
from lfphys.core import spin_transport as T
from lfphys.core.constants import YEAR_JULIAN as YEAR
from lfviz.params import Param, Schema
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

from .engine import loops as LP

FIELDS = [("theta", "поворот гироскопов θ после петли покой → u → w → покой"),
          ("ratio", "θ на единицу «изопериметрической» границы плоских петель при том же топливе")]
NS = 160         # samples of a slice along each in-plane axis
COARSE = 64      # rows of a moving (auto) slice
TRIADS = 36      # gyroscope triads along the path
MAX_SAMPLES = 4000


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("space", "3D-сцена", "select", "velocity", group="Сцена",
       options=[("velocity", "пространство скоростей (шар β = v/c; свет — его граница)"),
                ("lab", "обычное пространство: траектория корабля, световые годы")]),
    _p("loop", "Манёвр (петля в пространстве скоростей)", "select", "thomas", group="Манёвр", options=LP.LOOPS),
    _p("rho", "Размер петли ρ (быстрота: радиус круга, сторона импульса)", "float", 0.8, group="Манёвр",
       min=0.05, max=3.0),
    _p("turns", "Повторов петли", "int", 1, group="Манёвр", min=1, max=6),
    _p("sides", "Вершин многоугольника", "int", 6, group="Манёвр", min=3, max=24,
       show_if={"loop": ["polygon", "crown"]}),
    _p("alpha", "Поворот тяги между импульсами α, °", "float", 90.0, group="Манёвр", min=10.0, max=170.0,
       show_if={"loop": ["triangle"]}),
    _p("chi", "Неплоскость χ, °", "float", 30.0, group="Манёвр", min=0.0, max=80.0,
       show_if={"loop": ["crown", "helix", "seam"]}),
    _p("nth", "Нормаль плоскости петли: наклон от оси z θ, °", "float", 90.0, group="Манёвр", min=0.0, max=180.0),
    _p("nph", "Нормаль плоскости петли: азимут φ, °", "float", 90.0, group="Манёвр", min=0.0, max=360.0),
    _p("accel_g", "Тяга (собственное ускорение), g", "float", 1.0, group="Манёвр", min=0.1, max=10.0),
    _p("field", "Поле в шаре скоростей (объём и срезы)", "select", "theta", group="Поле",
       options=FIELDS, show_if={"space": ["velocity"]}),
    _p("eta_u", "Быстрота первого импульса u петель поля (вдоль оси e₁ петли)", "float", 1.0, group="Поле",
       min=0.1, max=3.0, show_if={"space": ["velocity"]}),
    _p("ngrid", "Сетка объёма, точек на ось", "select", 64, group="Поле",
       options=[(48, "48"), (64, "64"), (96, "96")], show_if={"space": ["velocity"]}),
], presets={
    "thomas": {"label": "Прецессия Томаса: равномерное движение по окружности, γ = 1,34", "params": {}},
    "circle": {"label": "Круг через покой: равенство в изопериметрической границе", "params": {"loop": "circle"}},
    "spin_flip": {"label": "SU(2): гироскопы вернулись (поворот 2π), спинор сменил знак",
                  "params": {"loop": "circle", "rho": round(math.acosh(2.0), 10)}},
    "triangle": {"label": "Три импульса: угол Вигнера = площадь треугольника скоростей",
                 "params": {"loop": "triangle", "rho": 1.2, "alpha": 120.0}},
    "crown": {"label": "Неплоская корона из 6 импульсов", "params": {"loop": "crown", "sides": 6, "chi": 35.0}},
    "helix": {"label": "Винт: тяга поворачивается вокруг наклонной оси", "params": {"loop": "helix", "chi": 30.0}},
    "seam": {"label": "Шов мяча на сфере скоростей (неплоский, 96 импульсов)",
             "params": {"loop": "seam", "rho": 0.9, "chi": 30.0}},
    "lab": {"label": "Обычное пространство: траектория и гироскопы при прецессии Томаса",
            "params": {"space": "lab", "rho": 1.0, "turns": 2}},
})


class Simulation(SlicePlanes, BaseSimulation):
    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        self.space = p["space"]
        self.accel = float(p["accel_g"]) * LP.G_LY  # ly / yr^2 (c = 1 ly/yr)
        self.pieces, self.info = LP.build(p)
        self.mv = T.Manoeuvre(self.pieces, c=1.0, accel=self.accel)
        fuel = self.mv.fuel()
        self.track = self.mv.run(ds=max(fuel / MAX_SAMPLES, 0.002))
        self.end = self.mv.end()
        self.hol = T.holonomy(self.end)
        tr = self.track
        self.tt = tr.x[:, 0] * YEAR             # lab time of every sample: the world clock, seconds
        self.T_end = float(self.tt[-1])
        # the speed from the programme's own clock (fuel / thrust: an input), not from the computed duration, which
        # is a consequence revealed only at the closure (review B2-2)
        tau_plan = fuel / self.accel * YEAR
        self.default_speed = tau_plan / 20.0
        self.speed_range = (tau_plan / 2000.0, tau_plan * 20.0)
        self.plane_time_scale = YEAR            # an auto plane's speed is per year of world time
        self.thrust = self._thrust_lab()
        self.eta_max = float(np.arccosh(max(1.0, float(np.max(tr.M[:, 0, 0])))))
        self.gamma_so_far = np.maximum.accumulate(tr.M[:, 0, 0])  # shown in the frames: the largest gamma up to now
        self.accumulated = self._accumulated() if self.info["planar"] else None
        self.k_rev = 0          # samples revealed so far
        self.next_piece = 0     # the next piece whose start is announced
        self.done = False
        self.e1 = np.asarray(self.info["e1"])
        self.spin0 = self.e1    # the spin drawn: the gyroscope axis that starts along e1
        self.triad_every = max(1, len(tr.s) // TRIADS)
        starts = np.concatenate([[0], np.flatnonzero(np.diff(tr.piece)) + 1])
        self.piece_t = [(int(tr.piece[i]), float(self.tt[max(i - 1, 0)])) for i in starts]
        self._init_planes()
        self.u_field = math.tanh(float(p["eta_u"])) * self.e1
        if self.space == "velocity":
            self.box = ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
            self.plane_center = (0.0, 0.0, 0.0)
            n = np.asarray(self.info["normal"])
            self.default_normals = {1: tuple(n), 2: tuple(self.e1), 3: tuple(np.asarray(self.info["e2"]))}
            self.plane_min_step = 2.0 / NS
            self._field_volume()
            self._set_plane(1, self.plane_center, self.default_normals[1])
        else:
            # the box from an input scale (c^2/a, the length of hyperbolic motion), doubled whenever the revealed path
            # comes near its edge: the framing does not show where the craft will go (review B2-2)
            self.box_half = 1.0 / self.accel
            self.box = self._lab_box()
            self.plane_center = (0.0, 0.0, 0.0)
            self.default_normals = {1: (0.0, 1.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 0.0, 1.0)}
            self.plane_min_step = self.box_half / 50
        self._static_checks()

    # --- the manoeuvre ---------------------------------------------------------------------------------------------
    def _thrust_lab(self):
        """The lab direction of the thrust at every sample: the spatial part of M (0, a), a the comoving direction."""
        tr = self.track
        starts = np.concatenate([[0.0], np.cumsum([q.rapidity for q in self.pieces])])
        out = np.zeros((len(tr.s), 3))
        for i in range(len(tr.s)):
            k = int(tr.piece[i])
            q = self.pieces[k]
            s_loc = tr.s[i] - starts[k]
            a = np.asarray(q.direction, float)
            a = a / np.linalg.norm(a)
            if isinstance(q, T.Turn):
                a = LZ.rot3(q.axis, q.curvature * s_loc) @ a
            v = tr.M[i] @ np.r_[0.0, a]
            out[i] = v[1:] / max(np.linalg.norm(v[1:]), 1e-300)
        return out

    def _lab_box(self):
        h = self.box_half
        return ((-h, -h, -h), (h, h, h))

    def _accumulated(self):
        """The accumulated rotation of a planar loop, computed along the run (review B2-3): the gyroscopes' frame
        relative to the pure-boost frame turns about the loop's normal n at every sample; its signed angle about n,
        unwrapped along the samples (steps <= 0.1 of fuel, rotation per unit fuel < 1), ends at -A."""
        e1, e2 = np.asarray(self.info["e1"]), np.asarray(self.info["e2"])
        v = self.track.O @ e1
        phi = np.unwrap(np.arctan2(v @ e2, v @ e1))
        return float(-phi[-1])

    def _pos(self, i):
        return self.track.beta[i] if self.space == "velocity" else self.track.x[i, 1:]

    # --- the field of three-burn loops (velocity space) -----------------------------------------------------------------
    def _field_volume(self):
        N = int(self.params["ngrid"])
        g = np.linspace(-1.0, 1.0, N)
        Z, X, Y = np.meshgrid(g, g, g, indexing="ij")  # layout (iz, ix, iy) of the environment's volume
        P = np.stack([X, Y, Z], -1)
        th, rv, L = LP.triangle_field(self.u_field, P)
        val = LP.field_values(self.params["field"], th, L)
        self.field_peak = float(np.nanmax(val))
        self.vol = np.nan_to_num(val / self.field_peak, nan=0.0).astype(np.float32)
        # glyphs: the gyroscopes' rotation vector on a coarse grid inside the ball
        gc = np.linspace(-0.9, 0.9, 9)
        Q = np.stack(np.meshgrid(gc, gc, gc, indexing="ij"), -1).reshape(-1, 3)
        Q = Q[np.linalg.norm(Q, axis=1) <= 0.95]
        thq, rvq, _ = LP.triangle_field(self.u_field, Q)
        keep = np.isfinite(thq)
        self.glyphs = (Q[keep].astype(np.float32), rvq[keep].astype(np.float32))
        # the check of the field: the matrix route against Gauss-Bonnet (L'Huilier) at points of the grid
        flat = P.reshape(-1, 3)
        ok_idx = np.flatnonzero(np.isfinite(th.ravel()) & (th.ravel() > 1e-6))
        pick = self.rng.choice(ok_idx, size=min(300, len(ok_idx)), replace=False)
        worst, worst_tol, ok = 0.0, 0.0, True
        for i in pick:
            w = flat[i]
            d = abs(float(th.ravel()[i]) - LP.triangle_reference(self.u_field, w))
            tol = LP.field_tolerance(self.u_field, w)
            ok &= d <= tol
            if d / tol >= worst / max(worst_tol, 1e-300):
                worst, worst_tol = d, tol
        self.field_check = (len(pick), worst, worst_tol, ok)

    def _field_on(self, P):
        th, _, L = LP.triangle_field(self.u_field, P)
        return th, LP.field_values(self.params["field"], th, L)

    def _quantity(self):
        if self.params["field"] == "theta":
            return {"label": "θ", "unit": "рад", "scale": math.pi}
        return {"label": "θ / граница(L)", "unit": "", "scale": 1.0}

    # --- slice planes (lfviz.planes3d hooks) --------------------------------------------------------------------------
    def _plane_label(self, pl):
        lab = G._label(pl)
        return re.sub(r"^([xyz]) = ", lambda m: f"β{m.group(1)} = ", lab).replace("через ось z", "через ось βz")

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        if self.space != "velocity":
            raise ValueError("в обычном пространстве срезов нет: поле считается в пространстве скоростей")
        n = COARSE if coarse else NS
        s, t = np.linspace(*s_rng, n), np.linspace(*t_rng, n)
        P = G.plane_points(pl, s, t)
        P = np.where(G.inside_box(P, self.box)[..., None], P, 2.0)  # outside the box: outside the ball, blank
        th, val = self._field_on(P)
        ver = {"points": 0, "note": "автосмещение: грубый срез, без сверки"} if coarse else self._verify(P, th)
        return {"s": s, "t": t, "th": th, "val": val, "verify": ver, "coarse": coarse}

    def _verify(self, P, th):
        """Up to three points of the plane (the largest rotation and two with at least 5 % of it): the matrix route
        against Gauss-Bonnet from the sides (L'Huilier); tolerance: the matrix route's round-off bound there."""
        f = np.where(np.isfinite(th), th, -1.0)
        if f.max() <= 1e-9:
            return {"points": 0, "note": "на плоскости нет поворота (u и w на одной прямой)"}
        i0 = np.unravel_index(np.argmax(f), f.shape)
        cand = np.argwhere(f >= 0.05 * f.max())
        pts = [i0] + [tuple(cand[j]) for j in self.rng.choice(len(cand), size=min(2, len(cand)), replace=False)]
        errs, tols = [], []
        for idx in pts:
            w = P[idx]
            errs.append(abs(float(th[idx]) - LP.triangle_reference(self.u_field, w)))
            tols.append(LP.field_tolerance(self.u_field, w))
        k = int(np.argmax(np.array(errs) / np.array(tols)))
        return {"points": len(pts), "max_err": errs[k], "tol": tols[k], "ok": all(e <= t for e, t in zip(errs, tols))}

    def _plane_emit(self, pid):
        sl, pd = self.slices[pid], self.planes[pid]
        val = sl["val"]
        peak = float(np.nanmax(val)) if np.isfinite(val).any() else 1.0
        q = self._quantity()
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(val.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": "plane", "units": "c", "depth": False, "coord_names": ["βx", "βy", "βz"],
                "verify_title": "θ в точках плоскости против площади треугольника скоростей (Гаусс–Бонне)",
                "quantity": {**q, "peak": peak * q["scale"]},
                "route_label": "точно для этой плоскости (матрицы Лоренца в каждой точке)", "exact": True,
                "approximation": False, "reason": "", "verify": sl["verify"]}
        self._msg(meta, {"I": (val / max(peak, 1e-300)).astype(np.float32)})
        ver = sl["verify"]
        if ver.get("points"):
            self._check(f"plane_exact_{pid}", f"Срез {pid} ({pd['label']}): поворот θ в {ver['points']} точках против "
                                              f"Гаусса–Бонне", ver["max_err"], 0.0, "рад", tol=ver["tol"], ok=ver["ok"],
                        note="θ матрицами Лоренца против площади треугольника скоростей по его сторонам (Люилье); "
                             "допуск — граница округления матриц в этой точке")

    def _plane_preview(self, pid, pl, s_rng, t_rng):
        if self.space != "velocity":
            raise ValueError("в обычном пространстве срезов нет")
        s, t = np.linspace(*s_rng, 48), np.linspace(*t_rng, 48)
        P = G.plane_points(pl, s, t)
        P = np.where(G.inside_box(P, self.box)[..., None], P, 2.0)
        _, val = self._field_on(P)
        peak = float(np.nanmax(val)) if np.isfinite(val).any() else 1.0
        self._msg({"type": "slice", "t": self.t, "id": pid, "preview": True, "shape": list(val.shape),
                   "s": [float(s[0]), float(s[-1]), len(s)], "tt": [float(t[0]), float(t[-1]), len(t)],
                   "origin": [float(c) for c in pl.origin], "u": list(pl.u), "v": list(pl.v),
                   "normal": [float(c) for c in pl.normal], "label": self._plane_label(pl), "peak": peak,
                   "units": "c", "depth": False, "coord_names": ["βx", "βy", "βz"],
                   "quantity": {**self._quantity(), "peak": peak * self._quantity()["scale"]}},
                  {"I": (val / max(peak, 1e-300)).astype(np.float32)})

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):
            self._check(f"plane_exact_{pid}", f"Срез {pid}: убран", None, None, "", info=True,
                        note="последняя сверка этого среза — в записи запуска")

    def view(self, args):
        if self.space != "velocity":
            raise ValueError("в обычном пространстве срезов нет: поле считается в пространстве скоростей")
        return super().view(args)

    # --- checks ----------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group="Гироскоп"):
        rel = None
        if ref is not None and value is not None and ref != 0:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        self._msg(d)

    def _static_checks(self):
        """Checks known at the start: the field of three-burn loops against Gauss-Bonnet."""
        if self.space == "velocity":
            n, worst, tol, ok = self.field_check
            self._check("field_exact", f"Поле: поворот θ в {n} точках объёма против Гаусса–Бонне", worst, 0.0, "рад",
                        tol=tol, ok=ok, group="Поле",
                        note="θ из матриц Лоренца (буст u, затем буст v' = w, увиденная из u) против площади "
                             "треугольника скоростей (покой, u, w) по его сторонам (Люилье); допуск — граница "
                             "округления 64 ε γ_u² γ_w² в худшей точке")

    def _round_bound(self):
        """An alarm level for the round-off (empirical, not derived; review B2-6): 1e-11 cosh(eta_max)^2 (pieces + 1 +
        the sum of the pieces' exponent norms s max(1, kappa)): the entries reach cosh(eta_max) and a turn's exponential
        (scaling and squaring) loses accuracy with the norm of its exponent. Over 640 random worlds of the schema (the
        reviewer's grids, rerun in the response) the measured round-off stayed below it by a factor >= 46 (Thomas loops
        at rho = 3; >= 140 for the others). It catches a blow-up; the comparisons use the measured round-off."""
        norm = sum(q.rapidity * max(1.0, abs(getattr(q, "curvature", 1.0))) for q in self.pieces)
        return 1e-11 * math.cosh(self.eta_max) ** 2 * (len(self.pieces) + 1 + norm)

    def _round_est(self):
        """The round-off of this run, measured: the disagreement of the two independent representations (4 x 4 Lorentz
        matrices by Pade exponentials, SL(2, C) by closed-form 2 x 2 exponentials) and the final state's distance from
        the Lorentz group."""
        e = self.end
        return max(float(np.max(np.abs(LZ.lorentz_of_sl2(e.A) - e.M))), LZ.lorentz_defect(e.M))

    def _closing_checks(self):
        h, e = self.hol, self.end
        est, bound = self._round_est(), self._round_bound()
        self._check("roundoff", "Округление: расхождение двух представлений (Лоренц 4×4 и SL(2, C))", est, 0.0, "",
                    tol=bound, ok=est <= bound,
                    note=f"оценка ошибки этого запуска (и отклонение состояния от группы Лоренца); порог тревоги — "
                         f"эмпирический: 1e-11·ch²(η_max)·(участки + 1 + Σ нормы показателей) = {bound:.1e}; допуски "
                         f"сверок ниже — 8 × эта оценка (импульсы многоугольников строятся в расширенной точности, "
                         f"их ошибка построения много меньше)")
        tol = max(8 * est, 1e3 * np.finfo(float).eps)
        self._check("closed", "Корабль вернулся к покою: |β| в конце", h["residual_beta"], 0.0, "", tol=tol,
                    ok=h["residual_beta"] <= tol, note="последний импульс рассчитан так, чтобы вернуть к покою; "
                                                       "допуск — 8 × оценка округления")
        ang = math.degrees(h["angle"])
        if self.info["planar"]:
            ref = float(self.info["reference"])
            n = np.asarray(self.info["normal"])
            tol = max(8 * est, 1e3 * np.finfo(float).eps * (1.0 + abs(ref)))  # + the reference's own rounding
            dR = float(np.max(np.abs(h["R"] - LZ.rot3(n, -ref))))
            ref_fold = math.degrees(abs((ref + math.pi) % (2 * math.pi) - math.pi))
            self._check("holonomy", "Поворот гироскопов (SO(3)), °: против замкнутой формулы", ang, ref_fold, "°",
                        tol=tol, ok=dR <= tol,
                        note=f"{self.info['ref_how']}; накопленный угол {ref:.10g} рад; гироскопы поворачиваются "
                             f"против обхода петли; сравнение матриц: max|R − R(n, −A)| = {dR:.1e}")
            dA = float(np.max(np.abs(h["su2"] - LZ.sl2_rotation(n, -ref))))
            dacc = abs(self.accumulated - ref)
            self._check("holonomy_accumulated", "Накопленный угол поворота (по ходу расчёта), рад: против площади",
                        self.accumulated, ref, "рад", tol=tol / max(abs(ref), 1e-300), ok=dacc <= tol,
                        note=f"угол системы гироскопов вокруг нормали петли, прослеженный по точкам манёвра без "
                             f"скачков на 2π; эталон — {self.info['ref_how']}; разность {dacc:.1e}")
            self._check("holonomy_su2", "Спинор (SU(2)): против exp(+iAσ·n/2) — знак после каждых 2π", dA, 0.0, "",
                        tol=tol, ok=dA <= tol,
                        note=f"угол SU(2) {math.degrees(h['su2_angle']):.6g}° (в [0, 360°]); знак спинора "
                             f"{'−1' if h['spinor_sign'] < 0 else '+1'} относительно поворота SO(3) на ≤ 180°")
        else:
            self._check("holonomy", "Поворот гироскопов (SO(3)), °", ang, None, "°", info=True,
                        note=f"{self.info['ref_how']}; ось ({', '.join(f'{c:.4f}' for c in h['axis'])})")
            if self.info["kind"] == "seam":
                self._check_seam()
        acc, L, how = self._per_fuel()
        bound = float(T.isoperimetric_bound(L))
        self._check("fuel_bound", "Поворот на единицу топлива против границы плоских петель", acc / bound, None, "",
                    info=True,
                    note=f"{how}; топливо L = {L:.6g} (сумма быстрот, ∫|a|dτ/c); граница плоских петель при этом L: "
                         f"√(4π² + L²) − 2π = {bound:.6g} рад (Оссерман 1978, (4.23): равенство только для круга); "
                         + ("для плоской петли граница — теорема" if self.info["planar"] else
                            "граница доказана только для плоских петель, здесь это линия сравнения"))

    def _per_fuel(self):
        """(angle, fuel, what): a planar loop's accumulated angle (computed along the run) and the whole fuel; for a
        non-planar loop the SU(2) angle of ONE loop and that loop's fuel (review B2-3: the SU(2) angle of a loop flown
        m times is only known mod 4 pi)."""
        if self.info["planar"]:
            return self.accumulated, self.mv.fuel(), "накопленный угол плоской петли (по ходу расчёта)"
        k = int(self.info.get("loop_pieces", len(self.pieces)))
        h1 = T.holonomy(self.track.ends[k - 1])
        L1 = float(sum(q.rapidity for q in self.pieces[:k]))
        return h1["su2_angle"], L1, "угол SU(2) одной петли (первого облёта) и её топливо"

    def _check_seam(self):
        p = dict(self.params)
        e1, e2, n = LP.base_frame(float(p["nth"]), float(p["nph"]))
        chi = math.radians(float(p["chi"]))
        rho, m = float(p["rho"]), int(p["turns"])
        h2 = T.holonomy(T.Manoeuvre(T.polygon_burns(LP.repeated(LP.seam_vertices(rho, chi, e1, e2, n,
                                                                                  2 * LP.SEAM_BURNS), m)),
                                    c=1.0, accel=self.accel).end())
        d = float(np.max(np.abs(h2["R"] - self.hol["R"])))
        self._check("seam_convergence", f"Шов: {LP.SEAM_BURNS} импульсов против {2 * LP.SEAM_BURNS}", d, None, "",
                    info=True, note="разница поворотов (матрицы); гладкий шов — предел; ошибка падает как 1/N²")

    # --- messages -----------------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, []
        if self.space == "velocity":
            self._msg({"type": "volume", "t": self.t, "id": "field", "dims": list(self.vol.shape),
                       "box": [list(self.box[0]), list(self.box[1])], "peak": self.field_peak,
                       "quantity": {**self._quantity(), "peak": self.field_peak * self._quantity()["scale"]},
                       "note": "поворот после петли покой → u → w → покой для каждого w; доля максимума"},
                      {"data": self.vol})
            pos, vec = self.glyphs
            self._msg({"type": "vectors", "t": self.t, "id": "rotvec", "count": int(len(pos)),
                       "note": "ось и угол поворота гироскопов (длина ~ √угла)"}, {"pos": pos, "vec": vec})
        if "vertices" in self.info:
            V = np.asarray(self.info["vertices"], float)
            if self.space == "velocity":
                self._msg({"type": "marks", "t": self.t, "id": "vertices", "count": int(len(V)),
                           "label": "вершины петли (заданы)"}, {"pos": V.astype(np.float32)})
        buf, self._buf = buf + self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)
        self.advance(0.0)

    # --- time: the manoeuvre revealed as lab time runs ------------------------------------------------------------
    def advance(self, t_target):
        dt = t_target - self.t
        self.t = t_target
        k = int(np.searchsorted(self.tt, t_target, side="right"))
        if k > self.k_rev:
            a = max(self.k_rev - 1, 0)
            idx = np.arange(a, k)
            P = np.array([self._pos(i) for i in idx], dtype=np.float32)
            if self.space == "lab":  # the box grows as the path is revealed (review B2-2)
                far, grown = float(np.max(np.abs(P))), False
                while far > 0.9 * self.box_half:
                    self.box_half *= 2.0
                    grown = True
                if grown:
                    self.box = self._lab_box()
                    self.emit({"type": "box", "t": self.t, "box": [list(self.box[0]), list(self.box[1])]})
            self.emit({"type": "path", "t": self.t, "id": "path", "from": int(a), "count": int(len(idx))},
                      {"pts": P})
            tri = idx[(idx % self.triad_every == 0) & (idx >= self.k_rev)]
            if len(tri):
                self.emit({"type": "triads", "t": self.t, "id": "triads", "count": int(len(tri))},
                          {"pos": np.array([self._pos(i) for i in tri], np.float32),
                           "mats": self.track.O[tri].reshape(-1, 9).astype(np.float32)})
            while self.next_piece < len(self.piece_t) and self.piece_t[self.next_piece][1] <= t_target:
                piece, tp = self.piece_t[self.next_piece]
                if len(self.pieces) <= 16:  # a seam of 96 burns would flood the log
                    self.emit({"type": "event", "t": tp, "kind": "burn", "text": self._piece_text(piece)})
                self.next_piece += 1
            self.k_rev = k
        if not self.done and t_target >= self.T_end:
            self.done = True
            self._closing()
        self._advance_planes(t_target, dt)

    def _piece_text(self, k):
        q = self.pieces[k]
        d = ", ".join(f"{c:.3f}" for c in np.asarray(q.direction, float) / np.linalg.norm(q.direction))
        if isinstance(q, T.Turn):
            return (f"участок {k + 1} из {len(self.pieces)}: тяга ({d}) в своей системе поворачивается со скоростью "
                    f"{q.curvature:.4g} рад на единицу быстроты, топливо {q.rapidity:.4g}")
        return f"участок {k + 1} из {len(self.pieces)}: импульс вдоль ({d}) своей системы, быстрота {q.rapidity:.4g}"

    def _closing(self):
        h = self.hol
        ang = math.degrees(h["angle"])
        ax = h["axis"]
        sign = "сменил знак (−1)" if h["spinor_sign"] < 0 else "тот же (+1)"
        self.emit({"type": "event", "t": self.T_end, "kind": "closed",
                   "text": f"петля замкнута: гироскопы повернулись на {ang:.4g}° вокруг оси "
                           f"({ax[0]:.3f}, {ax[1]:.3f}, {ax[2]:.3f}); спинор {sign}; топливо {self.mv.fuel():.4g}"})
        origin = self._pos(len(self.tt) - 1)
        size = 0.45 if self.space == "velocity" else 0.25 * (self.box[1][0] - self.box[0][0])
        self.emit({"type": "arrow", "t": self.T_end, "id": "holonomy", "from": [float(c) for c in origin],
                   "vec": [float(c) * size for c in ax], "label": f"ось поворота, {ang:.3g}°", "color": "#ffd23f",
                   "layer": "Ось поворота гироскопов (после петли)"})
        acc, L, how = self._per_fuel()
        bound = float(T.isoperimetric_bound(L))
        self.emit({"type": "holonomy", "t": self.T_end, "angle": h["angle"], "axis": [float(c) for c in ax],
                   "su2_angle": h["su2_angle"], "spinor_sign": h["spinor_sign"], "fuel": self.mv.fuel(),
                   "planar": self.info["planar"], "accumulated": self.accumulated, "per_fuel_angle": acc,
                   "per_fuel_L": L, "per_fuel_how": how, "bound": bound, "per_bound": acc / bound,
                   "T_end": self.T_end / YEAR, "tau_end": float(self.end.tau), "gamma_max": math.cosh(self.eta_max)})
        self._closing_checks()

    def frame(self):
        i = max(0, min(len(self.tt) - 1, int(np.searchsorted(self.tt, self.t, side="right")) - 1))
        tr = self.track
        O = tr.O[i]
        n, th = LZ.axis_angle(O)
        return {"i": i, "rot_angle": float(th), "rot_axis": [float(c) for c in n],
                "gamma": float(tr.M[i, 0, 0]), "gamma_so_far": float(self.gamma_so_far[i]), "tau": float(tr.tau[i]), "s": float(tr.s[i]), "t_yr": float(tr.x[i, 0]),
                "beta": [float(c) for c in tr.beta[i]], "pos": [float(c) for c in self._pos(i)],
                "O": [float(c) for c in O.ravel()], "spin": [float(c) for c in O @ self.spin0],
                "thrust": [float(c) for c in self.thrust[i]], "done": bool(self.done)}, {}

    def next_event_time(self):
        for _, tp in self.piece_t:
            if tp > self.t + 1e-12:
                return tp
        return self.T_end if self.t < self.T_end else None

    def live_values(self):
        return {}

    def set_live(self, values):
        raise ValueError("у этого мира нет параметров, меняемых на ходу: манёвр — параметр мира")

    def engine_modules(self):
        return ["core.lorentz", "core.spin_transport", "core.geometry"]

    def header(self):
        p, info, h = self.params, self.info, self.hol
        vel = self.space == "velocity"
        objects = []
        if vel:
            objects += [{"id": "light", "label": "Свет: |β| = 1 (граница пространства скоростей)", "kind": "sphere",
                         "center": [0.0, 0.0, 0.0], "radius": 1.0, "visible": True},
                        {"id": "rest", "label": "Покой (начало и конец петли)", "kind": "point",
                         "pos": [0.0, 0.0, 0.0], "text": "покой", "visible": True}]
        else:
            objects += [{"id": "start", "label": "Старт и финиш (покой)", "kind": "point", "pos": [0.0, 0.0, 0.0],
                         "text": "старт", "visible": True}]
        layers = [{"id": "field", "label": "Поле поворотов (объём)", "kind": "volume", "visible": True,
                   "look": {"density": 0.35, "threshold": 0.05}},
                  {"id": "rotvec", "label": "Оси поворота гироскопов (стрелки)", "kind": "vectors", "visible": False}] \
            if vel else []
        views = ([["iso", "Изо", "Изометрия (F)"], ["side", "вдоль x", "Взгляд вдоль оси βx"],
                  ["top", "сверху", "Взгляд вдоль оси βy (сверху)"], ["beam", "вдоль z", "Взгляд вдоль оси βz"],
                  ["back", "против z", "Взгляд против оси βz"]] if vel else
                 [["iso", "Изо", "Изометрия (F)"], ["side", "вдоль x", "Взгляд вдоль оси x"],
                  ["top", "сверху", "Взгляд вдоль оси y (сверху)"], ["beam", "вдоль z", "Взгляд вдоль оси z"],
                  ["back", "против z", "Взгляд против оси z"]])
        units = "c" if vel else "св. лет"
        return {
            "title": "Прецессия Томаса–Вигнера в 3D: " + dict(LP.LOOPS)[p["loop"]],
            "text": ("Корабль стартует из покоя и выполняет манёвр: импульсы и повороты тяги в своей системе. Его "
                     "гироскопы переносятся без вращения (Ферми–Уокер); вернувшись к покою, они оказываются "
                     "повёрнутыми — это голономия петли, которую скорость пробежала в пространстве скоростей. Поворот "
                     "считается точно (SO(3) и спинор SU(2)), сверяется с площадью петли (Гаусс–Бонне) для плоских "
                     "петель и сравнивается с изопериметрической границей при том же топливе."),
            "actions": [],
            "scene3d": {"box": [list(self.box[0]), list(self.box[1])], "units": units, "objects": objects,
                        "layers": layers, "views": views, "coord_names": ["βx", "βy", "βz"] if vel else ["x", "y", "z"],
                        "planes": {"max": 3 if vel else 0, "center": list(self.plane_center), "time_unit": "год",
                                   "defaults": {str(i): list(v) for i, v in self.default_normals.items()}}},
            "loop": {"kind": info["kind"], "planar": info["planar"], "normal": info["normal"], "e1": info["e1"],
                     "e2": info["e2"], "ref_how": info["ref_how"], "pieces": len(self.pieces), "fuel": self.mv.fuel(),
                     "accel": self.accel},
            "field": {"kind": p["field"], "u": self.u_field.tolist(), "quantity": self._quantity(),
                      "peak": getattr(self, "field_peak", None)} if vel else None,
            "units": {"t": "с (мировые часы; манёвр — годы)", "x": units},
            "space": self.space,
        }, {}


VIZ = {
    "id": "v09_thomas_3d",
    "title": "Прецессия Томаса–Вигнера в 3D",
    "summary": ("Манёвр корабля в 3D (импульсы и повороты тяги): гироскопы после возврата к покою повёрнуты — "
                "голономия петли в пространстве скоростей, в SO(3) и SU(2); топливо и изопериметрическая граница; "
                "поле поворотов в шаре скоростей со срезами."),
    "purpose": ("Продолжение линии вращения Томаса–Вигнера в 3+1: неплоские манёвры, двойное накрытие (знак спинора), "
                "поворот на единицу топлива против границы плоских петель."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
