# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v08: a wave in 3-D — diffraction of monochromatic light by an aperture (a wrapper over lfphys; plan P10, P11;
the 3-D environment: owner, 2026-10-27).

The scalar field behind an aperture in the plane z = 0 (a Gaussian beam, a circle, a square, a slit or a double slit
of finite length) is propagated by its angular spectrum (lfphys.core.optics.angular_spectrum), the source entering by
its exact spectrum (lfphys.core.optics.aperture_fields), on the CPU or on GPU 0 (lfphys.core.backend).

The view is a 3-D scene: the screen with its aperture, the incident wave, the light behind the screen (the computed
volume), the energy current, the target at z_max; every element can be switched off. Slices are planes placed in the
scene at any orientation, up to three, each with its own window; they stay where they are put (moving them by
themselves is an option per plane, off by default). Each slice is computed exactly for its plane by the engine (as
the volume would give it on the same grid) and checked against the exact field where the source has one.

Modelling (owner, 2026-10-24): **full 3-D** computes the volume (the 3-D light and the energy current are shown);
**slices only** computes nothing but the slices placed (faster; the 3-D scene shows the apparatus and the slices).
For a slit or a double slit, the planes y = c can be computed by the reduced 2-D model (the slit taken as infinitely
long): an approximation, flagged everywhere and measured against the exact slice. Units: micrometres.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import backend
from lfphys.core import geometry as G
from lfphys.core.optics import angular_spectrum as AS
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

from .engine import apparatus as A

SOURCES = [("gauss", "гауссов пучок"), ("circle", "круглое отверстие"), ("square", "квадратное отверстие"),
           ("slit", "щель конечной длины"), ("double", "две щели конечной длины")]
SLITS = ("slit", "double")
NZ = 96  # z planes of the volume
MAX_PLANES = 3  # the shared environment's limit (lfviz.planes3d)
DEFAULT_NORMALS = {1: (0.0, -1.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 0.0, 1.0)}  # mutually perpendicular
ROUTES = {"plane": "точно для этой плоскости (как дал бы объём на этой сетке)",
          "turned": "точно для этой плоскости; источник повёрнут, окно измерено для повёрнутого источника",
          "reduced": "ПРИБЛИЖЕНИЕ: упрощённая 2-D модель (щель бесконечна)"}
AUTO_NT = 64  # rows of a slice moved by "auto" (coarse, not checked; the full slice when the plane stops)


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("source", "Источник в плоскости z = 0", "select", "double", group="Опыт", options=SOURCES),
    _p("lam", "Длина волны λ, мкм", "float", 0.5, group="Опыт", min=0.3, max=1.5),
    _p("w", "Перетяжка гауссова пучка w, мкм", "float", 1.5, group="Опыт", min=0.5, max=6.0,
       show_if={"source": ["gauss"]}),
    _p("a", "Радиус / полуширина a, мкм", "float", 0.75, group="Опыт", min=0.2, max=6.0,
       show_if={"source": ["circle", "square", "slit", "double"]}),
    _p("d", "Расстояние между щелями, мкм", "float", 4.0, group="Опыт", min=1.0, max=12.0,
       show_if={"source": ["double"]}),
    _p("L", "Длина щели вдоль y, мкм", "float", 8.0, group="Опыт", min=1.0, max=24.0,
       show_if={"source": ["slit", "double"]}),
    _p("zmax", "Глубина до мишени z_max, мкм", "float", 30.0, group="Опыт", min=2.0, max=80.0),
    _p("n", "Сетка в плоскости, точек на ось", "select", 256, group="Расчёт",
       options=[(128, "128"), (256, "256"), (512, "512 (только срезы)")]),
    _p("mode", "Моделирование", "select", "full3d", group="Расчёт",
       options=[("full3d", "весь объём: свет и поток энергии в 3D, любые срезы"),
                ("slices", "только срезы (быстрее): считаются лишь поставленные плоскости")]),
    _p("reduced", "Срезы y = c упрощённой 2-D моделью (щель бесконечна) — приближение", "bool", False,
       group="Расчёт", show_if={"mode": ["slices"], "source": ["slit", "double"]}),
], presets={
    "double": {"label": "Две щели конечной длины: весь объём", "params": {}},
    "double_slices": {"label": "Две щели: только срезы, y = c упрощённой 2-D моделью (приближение)",
                      "params": {"mode": "slices", "reduced": True}},
    "circle": {"label": "Круглое отверстие: провалы и пики интенсивности на оси",
               "params": {"source": "circle", "a": 3.0, "zmax": 40.0}},
    "gauss": {"label": "Гауссов пучок, w = 1,5 мкм: расходимость (проверка по интегралу)",
              "params": {"source": "gauss", "zmax": 30.0}},
    "square_big": {"label": "Квадратное отверстие, сетка 512: только срезы", "params": {
        "source": "square", "a": 2.0, "n": 512, "mode": "slices", "zmax": 15.0}},
})


class Simulation(SlicePlanes, BaseSimulation):
    speed_range = (0.05, 20.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._buf = []
        p = self.params
        if p["mode"] == "full3d" and int(p["n"]) > 256:
            raise ValueError("весь объём на сетке 512 занял бы ~1,6 ГБ: для 512 выберите «только срезы»")
        self.lam = float(p["lam"])
        self.k = 2 * math.pi / self.lam
        self.n = int(p["n"])
        self.dx = self.lam / 4 if self.n <= 256 else self.lam / 8
        self.x = (np.arange(self.n) - self.n // 2) * self.dx
        self.half = self.n // 2 * self.dx
        self.zmax = float(p["zmax"])
        self.box = ((float(self.x[0]), float(self.x[0]), 0.0), (float(self.x[-1]), float(self.x[-1]), self.zmax))
        self.zs = np.linspace(0.0, self.zmax, NZ)
        self.z_near = A.near_zone(self.dx, self.k)
        backend.reset_used()
        self.src = A.source(p, self.n)
        try:
            self.win = A.choose_window(self.src, self.dx, self.k, self.zmax)
        except ValueError as e:  # the world is refused: what to change, with a working example (review UX-params P26)
            text, _, advice = str(e).partition(". Уменьшите")
            ex = [f"«{v['label'].split(':')[0]}» (a = {v['params']['a']:g} мкм, z_max = {v['params']['zmax']:g} мкм)"
                  for v in SCHEMA.presets.values() if v["params"].get("source") == p["source"]
                  and "a" in v["params"] and "zmax" in v["params"]]
            hint = ("уменьшите" + advice if advice else "уменьшите z_max или возьмите источник шире") + (
                f"; работающий пример — сценарий {ex[0]}" if ex else "")
            raise Refusal(text, hint) from e
        self.kw = {"pad": self.win.pad, "band_limit": self.win.band_limit}
        self.peak_amp = float(np.max(np.abs(self.win.plane)))
        self.vol = None
        self.flux_P = None
        self.modelling = G.Modelling("full3d")
        if p["mode"] == "full3d":
            self.vol = AS.propagate_volume(self.src, self.dx, self.k, self.zs, **self.kw)
        self._turned = {}  # azimuth of a plane's u (degrees) -> the window measured for the turned source
        self._init_planes()  # the shared slice planes (lfviz.planes3d): self.planes, self.slices
        self.plane_center = (0.0, 0.0, self.zmax / 2)  # the axis at mid-depth (the box's centre is dx/2 off the axis)
        self.default_normals = DEFAULT_NORMALS
        self.plane_min_step = self.dx
        self._set_plane(1, self.plane_center, DEFAULT_NORMALS[1])
        self._checks()

    # --- the scene ------------------------------------------------------------------------------------------------
    def _scene(self):
        p = self.params
        W = 2 * self.half
        objects = []
        if p["source"] == "gauss":
            objects.append({"id": "source", "label": "Гауссов пучок в плоскости z = 0 (задан)", "kind": "disk",
                            "z": 0.0, "w": float(p["w"]), "size": [W, W], "visible": True})
        else:
            holes = ([{"circle": [0.0, 0.0, float(p["a"])]}] if p["source"] == "circle"
                     else [{"rect": list(r)} for r in A.rects(p)])
            objects.append({"id": "screen", "label": "Заслонка с отверстием (z = 0)", "kind": "plate", "z": 0.0,
                            "size": [W, W], "holes": holes, "visible": True})
        objects.append({"id": "incident", "label": "Падающая плоская волна (задана)", "kind": "incident",
                        "z0": -0.15 * self.zmax, "z1": 0.0, "lam": self.lam, "size": [W, W], "visible": True})
        objects.append({"id": "target", "label": f"Мишень (z = {self.zmax:g} мкм): интенсивность", "kind": "target",
                        "z": self.zmax, "size": [W, W], "visible": True})
        layers = []
        if self.vol is not None:
            layers.append({"id": "light", "label": "Свет за отверстием (объём, предпросмотр)", "kind": "volume",
                           "visible": True})
            layers.append({"id": "flux", "label": "Поток энергии (направление и величина)", "kind": "vectors",
                           "visible": False})
        return {"box": [list(self.box[0]), list(self.box[1])], "units": "мкм", "objects": objects, "layers": layers,
                "planes": {"max": MAX_PLANES, "center": [0.0, 0.0, self.zmax / 2],
                           "defaults": {str(i): list(v) for i, v in DEFAULT_NORMALS.items()}},
                "z_near": self.z_near, "dx": self.dx}

    def _send_scene_data(self):
        if self.vol is not None:
            pv = A.preview_volume(self.vol, self.n)
            self._msg({"type": "volume", "t": self.t, "id": "light", "dims": list(pv.shape),
                       "box": [list(self.box[0]), list(self.box[1])],
                       "note": "интенсивность, усреднённая 2×2 поперёк (предпросмотр); точные значения — в срезах"},
                      {"data": pv})
            zf = np.linspace(max(2 * self.z_near, self.zmax / 12), self.zmax, 10)
            pos, vec, P, jlast = A.flux_glyphs(self.src, self.dx, self.k, zf, self.x, self.win)
            self.flux_P = (zf, P, jlast)
            self._msg({"type": "vectors", "t": self.t, "id": "flux", "count": int(len(pos)),
                       "note": "поток энергии j = Im(U*∇U)/k на 10 плоскостях z, 16×16 точек; длина ~ √|j|"},
                      {"pos": pos, "vec": vec})
        tgt = np.abs(self.win.plane) ** 2
        step = max(1, self.n // 256)
        tgt = tgt[::step, ::step]
        self._msg({"type": "target", "t": self.t, "id": "target", "shape": list(tgt.shape),
                   "x": [float(self.x[0]), float(self.x[-1])], "peak": float(tgt.max())},
                  {"img": (tgt / max(float(tgt.max()), 1e-300)).astype(np.float32)})

    # --- slice planes (view commands; owner, 2026-10-27) ------------------------------------------------------------
    def _is_reduced(self, normal):
        n = np.asarray(normal, float) / np.linalg.norm(normal)
        return bool(self.params["mode"] == "slices" and self.params["reduced"] and self.params["source"] in SLITS
                    and abs(abs(n[1]) - 1.0) < 1e-9)

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        """The slice of one plane (lfviz.planes3d hook): exact for its plane, or the reduced 2-D model (flagged)."""
        reduced = self._is_reduced(pl.normal)
        nt = AUTO_NT if coarse else A.NT
        if reduced:
            win, route = self.win, "reduced"
            s, t, U = A.reduced_slice(self.params, self.n, self.dx, self.k, pl, s_rng, t_rng, self.box, nt=nt)
            reason = (f"щель длиной L = {self.params['L']:g} мкм принята бесконечной (упрощённая 2-D модель); "
                      f"размер приближения — в проверках")
        else:
            key = round(math.degrees(math.atan2(pl.u[1], pl.u[0])) % 180.0, 2)
            if key not in self._turned:  # a plane that turns the source: its window measured once per azimuth
                self._turned[key] = A.window_for_plane(self.src, self.dx, self.k, self.zmax, pl, self.win)
            win = self._turned[key]
            route = "plane" if win is self.win else "turned"
            s, t, U = A.compute_slice(self.src, self.dx, self.k, pl, s_rng, t_rng, win, self.box, nt=nt)
            reason = ""
        tol = win.abs_err + 1e-9
        if reduced:
            ver = {"points": 0, "note": "приближение: его размер — в проверке «ПРИБЛИЖЕНИЕ»"}
        elif coarse:
            ver = {"points": 0, "note": "автосмещение: грубый срез, без сверки; полный — когда автосмещение выключено"}
        else:
            ver = A.verify_slice(self.params, self.k, pl, s, t, U, self.z_near, tol)
        return {"s": s, "t": t, "U": U, "route": route, "exact": not reduced, "coarse": coarse, "reason": reason,
                "verify": ver, "plane": pl, "window": win, "tol": tol}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        pl = sl["plane"]
        self._send_slice(pid)
        ver = sl["verify"]
        if not sl["exact"] and not sl["coarse"]:
            self._check_reduced(pid)
        elif ver.get("points"):
            self._check(f"plane_exact_{pid}", f"Срез {pid} ({G._label(pl)}): поле в {ver['points']} точках против "
                                              f"точного", ver["max_err"], 0.0, "", tol=sl["tol"], ok=ver["ok"],
                        note="эталон без БПФ в точках самой плоскости (самая яркая и две с ≥ 5 % её интенсивности, "
                             f"глубже z_near); допуск — ошибка окна ({sl['tol']:.1e})")
        self._update_modelling()

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):  # its check row says so (review C8)
            self._check(f"plane_exact_{pid}", f"Срез {pid}: убран", None, None, "", info=True,
                        note="последняя сверка этого среза — в записи запуска")
        self._update_modelling()

    def _update_modelling(self):
        if self.params["mode"] == "full3d":
            return
        self.modelling = G.Modelling("slices", [G.Slice(sl["plane"], sl["exact"], sl["reason"])
                                                for sl in self.slices.values()] or [G.Slice(G.Plane.preset("xz"))])
        self._msg({"type": "modelling", "t": self.t, "modelling": self.modelling.describe(),
                   "approximations": self.modelling.approximations()})

    def _send_slice(self, pid):
        sl = self.slices[pid]
        U = sl["U"]
        I = np.abs(U) ** 2
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        pd = self.planes[pid]
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(U.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": sl["route"],
                "route_label": ROUTES[sl["route"]] + ("" if sl["window"].est <= A.TOL else
                                                      f"; окно для повёрнутого источника не достигло допуска "
                                                      f"({sl['window'].est:.1e} > {A.TOL:.0e})"),
                "exact": sl["exact"],
                "approximation": not sl["exact"], "reason": sl["reason"], "verify": sl["verify"],
                "z_near": self.z_near, "window_est": sl["window"].est, "window": sl["window"].describe()}
        blobs = {"I": (I / max(peak, 1e-300)).astype(np.float32)}
        if not sl["coarse"]:  # moving slices are not recorded with their phase (review C6: the record's size)
            blobs["phase"] = np.angle(U).astype(np.float32)
        self._msg(meta, blobs)

    def _plane_preview(self, pid, pl, s_rng, t_rng):
        """While a plane is dragged in "slices only": a coarse slice, not kept, not checked."""
        if self._is_reduced(pl.normal):
            s, t, U = A.reduced_slice(self.params, self.n, self.dx, self.k, pl, s_rng, t_rng, self.box, nt=48)
        else:
            s, t, U = A.compute_slice(self.src, self.dx, self.k, pl, s_rng, t_rng, self.win, self.box, nt=48)
        I = np.abs(U) ** 2
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        self._msg({"type": "slice", "t": self.t, "id": pid, "preview": True, "shape": list(U.shape),
                   "s": [float(s[0]), float(s[-1]), len(s)], "tt": [float(t[0]), float(t[-1]), len(t)],
                   "origin": [float(c) for c in pl.origin], "u": list(pl.u), "v": list(pl.v),
                   "normal": [float(c) for c in pl.normal], "label": G._label(pl), "peak": peak,
                   "z_near": self.z_near, "window_est": self.win.est},
                  {"I": (I / max(peak, 1e-300)).astype(np.float32)})

    # --- checks -------------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False):
        rel = None
        if ref is not None and value is not None and ref != 0:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": "Волна", "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        self._msg(d)

    def _check_reduced(self, pid):
        sl = self.slices[pid]
        s, t, Ue = A.compute_slice(self.src, self.dx, self.k, sl["plane"], (sl["s"][0], sl["s"][-1]),
                                   (sl["t"][0], sl["t"][-1]), self.win, self.box, check=True)
        Ie, Ir = np.abs(Ue) ** 2, np.abs(sl["U"]) ** 2
        err = float(np.nanmax(np.abs(Ir - Ie)) / np.nanmax(Ie))
        self._check("reduced", f"ПРИБЛИЖЕНИЕ: упрощённая 2-D модель среза {pid} ({G._label(sl['plane'])}) против "
                               f"точного", err, 0.0, "", info=True,
                    note=f"максимальное отличие интенсивности, доля пика; {sl['reason']}")

    def _checks(self):
        p = self.params
        win, j0 = self.win, self.n // 2
        rows = "; ".join(f"×{pp}{' огр.' if bl else ''}: {d:.1e}" for pp, bl, d in win.rows)
        self._check("window", "Окно расчёта: периодические копии на глубине z_max", win.est, None, "",
                    tol=A.TOL, ok=win.est <= A.TOL,
                    note=f"{win.describe()}; доля пика амплитуды, оценка {A.SAFETY}·max|U(окно) − U(окно×2)|; "
                         f"замеры: {rows}")
        for i, j in A.ref_points(p, self.x):
            x0, y0 = float(self.x[i]), float(self.x[j])
            ref, rerr = A.reference(p, self.k, self.zmax, x0, y0)
            U = complex(win.plane[i, j])
            tol = win.abs_err + rerr + 1e-9
            how = {"gauss": "интеграл Ганкеля (квадратура)", "circle": "замкнутая формула Рэлея–Зоммерфельда на оси"}
            self._check(f"exact_{i}_{j}", f"Поле в точке x = {x0:.3g}, y = {y0:.3g}, z = z_max: точное значение",
                        abs(U), abs(ref), "", tol=tol / max(abs(ref), 1e-300), ok=abs(U - ref) <= tol,
                        note=f"эталон без БПФ — {how.get(p['source'], 'интеграл Рэлея–Зоммерфельда по углу')}; "
                             f"комплексная разность {abs(U - ref):.1e}, допуск = ошибка окна + ошибка эталона "
                             f"({tol:.1e})")
        # two fp64 routes of the engine: the plane y = 0 by the plane route against the transverse planes' rows
        zc = [float(self.zs[NZ // 2]), self.zmax]
        rows_v = np.stack([AS.propagate_field(self.src, self.dx, self.k, zc[0], check=True, **self.kw)[:, j0],
                           win.plane[:, j0]])
        s, U = AS.propagate_plane(self.src, self.dx, self.k, G.Plane.horizontal((0.0, -1.0, 0.0)),
                                  (float(self.x[0]), float(self.x[-1])), zc, check=True, **self.kw)
        diff = float(np.max(np.abs(U - rows_v)) / np.max(np.abs(rows_v)))
        self._check("slice_route", "Срез y = 0 по плоскости совпадает со срезом поперечных плоскостей", diff, 0.0,
                    "", tol=1e-12, ok=diff <= 1e-12,
                    note="два пути движка в fp64 на z = z_max/2 и z_max (доля пика амплитуды)")
        u = backend.used().get(AS.KERNEL, {}).get("drawn", {})
        exact = [sl for sl in self.slices.values() if sl["exact"]]  # the reduced model is computed in fp64
        if u.get("precision") == "fp32" and (self.vol is not None or exact):
            # what is drawn in fp32 against fp64 (review B1-5): the kernel's declared bound is the tolerance
            bound = backend.kernels()[AS.KERNEL].precisions["fp32"]["bound"]
            if self.vol is not None:
                drawn, ref64 = self.vol[-1], win.plane
            else:
                drawn, ref64 = self._fp64_pair(exact[0])
            err = float(np.nanmax(np.abs(drawn - ref64)) / np.nanmax(np.abs(ref64)))
            self._check("fp32", "Рисунок в fp32 против того же расчёта в fp64", err, 0.0, "", tol=bound,
                        ok=err <= bound, note=f"граница ядра для fp32: {bound:.0e} пика амплитуды")
        self._check("near", f"У отверстия (z < {self.z_near:.2g} мкм) — поле, ограниченное по спектру сеткой",
                    self.z_near, None, "мкм", info=True,
                    note="компоненты с |q| ≥ π/dx (затухающие) отброшены: на глубине z_near они меньше 1e-6 своей "
                         "величины на z = 0; ближе к отверстию (на рисунке — штриховка) поле у краёв рябит "
                         "(Гиббс), это свойство сетки, а не физики")
        if u:
            self._check("device", f"Угловой спектр (рисунок) считался на {'GPU' if u['device'] == 'gpu' else 'CPU'} "
                                  f"({u['precision']})", None, None, "", info=True,
                        note=u.get("reason", "") + "; проверки — всегда в fp64")

    def _fp64_pair(self, sl):
        """The drawn slice and the same slice in fp64 (check=True), NaN where the drawn one is."""
        s, U = AS.propagate_plane(self.src, self.dx, self.k, sl["plane"], (sl["s"][0], sl["s"][-1]), sl["t"],
                                  check=True, **self.kw)
        U = np.asarray(U, np.complex128)
        U[np.isnan(sl["U"])] = np.nan
        return sl["U"], U

    def _check_flux(self):
        """The energy current where the exact one is known (review C4): j at the reference points of z_max against
        Im(U* grad U)/k of the exact field and its derivatives (no FFTs); the window's error as tolerance. The power
        through the planes is shown as information: for the plain sum it equals the spectrum's closed form by
        Parseval's identity of the discrete sum (a check of the code, not of the physics)."""
        if self.flux_P is None:
            return
        zf, P, jlast = self.flux_P
        u = backend.used().get(AS.KERNEL, {}).get("drawn", {})
        fp32 = u.get("precision") == "fp32"
        worst, worst_tol, ok = 0.0, 0.0, True
        for i, j in A.ref_points(self.params, self.x):
            jr, Ur, g, rerr = A.reference_current(self.params, self.k, self.zmax, float(self.x[i]), float(self.x[j]))
            jc = jlast[:, i, j]
            tol = self.win.abs_err * (abs(Ur) + g) + rerr + 1e-9
            if fp32:
                tol += backend.kernels()[AS.KERNEL].precisions["fp32"]["bound"] * self.peak_amp ** 2 * 3
            d = float(np.max(np.abs(jc - jr)))
            ok &= d <= tol
            if d / tol >= worst / max(worst_tol, 1e-300):
                worst, worst_tol = d, tol
        self._check("flux_exact", "Поток энергии в точках z_max против точного (производные точного поля)", worst,
                    0.0, "", tol=worst_tol, ok=ok,
                    note="j = Im(U*∇U)/k; эталон без БПФ: замкнутые производные (гауссово поле, круг на оси) или "
                         "пятиточечные разности точного поля (прямоугольники); допуск — ошибка окна × (|U| + |∇U|/k)"
                         + (" + граница fp32" if fp32 else ""))
        ref = AS.flux_of_spectrum(self.src, self.dx, self.k, pad=self.win.pad)
        dev = float(np.max(np.abs(P - ref)) / ref)
        self._check("flux", "Мощность через плоскости z: тождество суммы (проверка кода)", dev, 0.0, "", info=True,
                    note=("ограничение полосы убирает на глубине компоненты с большими углами: доля мощности"
                          if self.win.band_limit else
                          f"P(z) = Σ j_z dx dy по всему окну на {len(zf)} глубинах против замкнутой формулы по "
                          f"спектру — тождество Парсеваля дискретной суммы: подтверждает код и нормировку, но не "
                          f"окно и не физику (их — строка выше)"))

    # --- messages -----------------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, []
        self._send_scene_data()
        self._check_flux()
        buf, self._buf = buf + self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- live: none (the view is driven by view commands) --------------------------------------------------------
    def live_values(self):
        return {}

    def set_live(self, values):
        raise ValueError("у этого мира нет параметров, меняемых на ходу: срезы ставятся в 3D-сцене")

    # --- time: planes with "auto" move along their normal; the others stay where they are (owner, 2026-10-27) --------
    def advance(self, t_target):
        dt = t_target - self.t
        self.t = t_target
        self._advance_planes(t_target, dt)

    def frame(self):
        return {}, {}

    def engine_modules(self):
        return ["core.optics.angular_spectrum", "core.optics.aperture_fields", "core.geometry", "core.backend"]

    def header(self):
        p = self.params
        return {
            "title": "Волна в 3D: " + dict(SOURCES)[p["source"]],
            "text": ("Поле за отверстием в плоскости z = 0 распространяется суммой плоских волн (угловой спектр); "
                     "отверстие входит своим точным спектром. В 3D-сцене — заслонка, падающая волна, свет за "
                     "отверстием, поток энергии и мишень; любую часть можно выключить. Срезы — плоскости под любым "
                     "углом (до трёх), у каждой своё окно; каждый срез считается точно для своей плоскости и "
                     "сверяется с точным полем. Срезы стоят, где их поставили; автосмещение — по желанию."),
            "actions": [],
            "scene3d": self._scene(),
            "modelling": self.modelling.describe(),
            "approximations": self.modelling.approximations(),
            "accuracy": {"window": self.win.est, "tol": A.TOL, "pad": self.win.pad,
                         "band_limit": self.win.band_limit, "z_near": self.z_near},
            "units": {"x": "мкм", "z": "мкм"},
            "lam": self.lam, "half": self.half, "zmax": self.zmax, "n": self.n, "dx": self.dx,
        }, {}


VIZ = {
    "id": "v08_wave_3d",
    "title": "Волна в 3D: дифракция на отверстии",
    "summary": ("3D-сцена: заслонка с отверстием, падающая волна, свет за отверстием, поток энергии и мишень; "
                "срезы — плоскости под любым углом (до трёх) со своими окнами; точность каждого мира измерена."),
    "purpose": ("Полноценная 3D-среда исследователя на движке: части сцены включаются по отдельности, срезы ставятся "
                "и поворачиваются руками или параметрами, расчёт на CPU или GPU."),
    "version": "2.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
