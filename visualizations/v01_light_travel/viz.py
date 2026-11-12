# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v01: light over large distances - finite speed, light cones, gravity, moving observers.

What the run computes (README.md of this folder has the model in full):
* light from an emission event is traced under the run's laws (flat: Lorentz-aberrated straight rays; GR: null
  geodesics of Schwarzschild; modifications: ether, ballistic light, Newtonian corpuscles);
* exact arrival events at every receiver (quadratic solve in flat space, quadrature + root finding in GR);
* clocks along every worldline from the metric of the laws; observers' frames from the laws' transformations;
* measurements by apparatus (a rod with clocks at both ends, synchronised by a simulated light exchange);
* checks: each computed quantity next to the closed-form value of accepted physics (or of the declared
  modification).
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.constants import AU, DAY, GM_SUN, LIGHT_YEAR, R_EARTH, R_SUN
from lfphys.core.constants import C as C_SI
from lfphys.core.worldlines import Orbit, Piecewise
from lfphys.laws.light import GRAVITY, KINEMATICS, Laws

from .engine import checks
from .engine.apparatus import Apparatus, fmt_s
from .engine.world import Obj, World, _check

SCN = [("sun_earth", "Солнце → Земля: свет летит 8 минут"),
       ("measure_c", "Измерение скорости света движущимися наблюдателями"),
       ("lensing", "Гравитационное отклонение света (чёрная дыра / звезда)"),
       ("andromeda", "Парадокс Андромеды: относительность одновременности")]


def _p(*a, **k):
    return Param(*a, **k)


SE = {"scenario": ["sun_earth"]}
MC = {"scenario": ["measure_c"]}
LN = {"scenario": ["lensing"]}
AN = {"scenario": ["andromeda"]}

SCHEMA = Schema([
    _p("scenario", "Сценарий", "select", "sun_earth", group="Сценарий", options=SCN),
    _p("kinematics", "Кинематика", "select", "SR", group="Законы физики", options=KINEMATICS, standard="SR",
       help="СТО — общепринятая. Эфир и баллистическая теория — исторические альтернативы, опровергнутые опытом; "
            "выбор помечает запуск как модифицированную физику."),
    _p("gravity", "Гравитация", "select", "GR", group="Законы физики", options=GRAVITY, standard="GR",
       help="ОТО — общепринятая (для сценариев с массой). «Без гравитации» в сценарии с массой — модификация."),
    _p("c_factor", "Скорость света, × c", "float", 1.0, group="Законы физики", min=1e-3, max=1e3, log=True,
       standard=1.0, help="Множитель к c = 299 792 458 м/с; любое значение кроме 1 — модификация."),
    _p("n_rays", "Лучей во вспышке", "int", 360, group="Свет", min=36, max=1440,
       help="Сколько лучей рисует фронт одной вспышки. На точность событий не влияет: они решаются отдельно."),
    # sun-earth
    _p("se_mass", "Масса Солнца, M☉", "float", 1.0, group="Солнце и Земля", min=1e-3, max=1e6, log=True,
       show_if=SE),
    _p("se_radius_km", "Радиус Солнца, км", "float", R_SUN / 1e3, group="Солнце и Земля", min=1.0, max=1e8,
       log=True, show_if=SE),
    _p("se_distance_au", "Расстояние до Земли, а.е.", "float", 1.0, group="Солнце и Земля", min=0.01, max=100,
       log=True, show_if=SE),
    _p("se_orbit", "Земля движется по орбите", "bool", True, group="Солнце и Земля", show_if=SE),
    # measure c
    _p("mc_v1", "Наблюдатель 1: скорость, × c", "float", 0.0, group="Измерение c", min=-0.99, max=0.99,
       show_if=MC),
    _p("mc_v2", "Наблюдатель 2: скорость, × c", "float", 0.5, group="Измерение c", min=-0.99, max=0.99,
       show_if=MC, help="Положительная — от источника (по ходу света), отрицательная — навстречу свету."),
    _p("mc_v3", "Наблюдатель 3: скорость, × c", "float", -0.5, group="Измерение c", min=-0.99, max=0.99,
       show_if=MC),
    _p("mc_L0_km", "Длина стержня L₀ (в покое), км", "float", 300.0, group="Измерение c", min=1e-3, max=1e6,
       log=True, show_if=MC),
    _p("mc_src_km", "Источники на расстоянии, км", "float", 3000.0, group="Измерение c", min=1.0, max=1e8,
       log=True, show_if=MC),
    _p("mc_src_u", "Скорость источников, × c", "float", 0.0, group="Измерение c", min=-0.9, max=0.9, show_if=MC,
       help="Важна в баллистической теории (свет летит с c относительно источника); в СТО не влияет на c."),
    _p("mc_sync", "Синхронизация часов B", "select", "einstein", group="Измерение c", show_if=MC,
       options=[("einstein", "по Эйнштейну (обмен светом)"),
                ("lab", "по лабораторной одновременности (недоступно наблюдателю)")]),
    _p("mc_orient", "Стержень", "select", "x", group="Измерение c", show_if=MC,
       options=[("x", "вдоль движения (ось x)"), ("y", "поперёк движения (ось y)")]),
    _p("mc_t_flash_ms", "Вспышка источников в момент, мс", "float", 3.0, group="Измерение c", min=0.0, max=1e6,
       show_if=MC),
    # lensing
    _p("ln_mass", "Масса тела, M☉", "float", 10.0, group="Линза", min=1e-3, max=1e10, log=True, show_if=LN),
    _p("ln_radius_km", "Радиус тела, км (0 = чёрная дыра)", "float", 0.0, group="Линза", min=0.0, max=1e8,
       show_if=LN),
    _p("ln_src_rs", "Источник: расстояние, rs", "float", 60.0, group="Линза", min=5.0, max=1e5, log=True,
       show_if=LN),
    _p("ln_src_y_rs", "Источник: смещение вбок, rs", "float", 0.5, group="Линза", min=-1e4, max=1e4, show_if=LN),
    _p("ln_obs_rs", "Наблюдатель: расстояние, rs", "float", 60.0, group="Линза", min=5.0, max=1e5, log=True,
       show_if=LN),
    _p("ln_plane", "Параллельный пучок слева", "bool", True, group="Линза", show_if=LN),
    _p("ln_plane_hw_rs", "Полуширина пучка, rs", "float", 10.0, group="Линза", min=0.5, max=1e4, log=True,
       show_if=LN),
    # andromeda
    _p("an_dist_mly", "Расстояние до Андромеды, млн св. лет", "float", 2.5, group="Андромеда", min=1e-9,
       max=1e4, log=True, show_if=AN),
    _p("an_walk", "Скорость пешеходов, м/с", "float", 1.4, group="Андромеда", min=0.0, max=2.9e8, show_if=AN),
    _p("an_event_days", "Событие на Андромеде в момент (лаб.), сут", "float", 0.0, group="Андромеда",
       min=-1e12, max=1e12, show_if=AN),
], presets={
    "sun_earth": {"label": "Солнце → Земля (стандартная физика)", "params": {"scenario": "sun_earth"}},
    "measure_c": {"label": "Измерение c: покой, по ходу света, навстречу (СТО)",
                  "params": {"scenario": "measure_c", "gravity": "none"}},
    "measure_c_lab": {"label": "Измерение c: часы по лабораторной одновременности (СТО)",
                      "params": {"scenario": "measure_c", "gravity": "none", "mc_sync": "lab"}},
    "measure_c_ether": {"label": "Измерение c в мире с эфиром (модификация)",
                        "params": {"scenario": "measure_c", "gravity": "none", "kinematics": "ether"}},
    "measure_c_emission": {"label": "Измерение c при баллистическом свете (модификация)",
                           "params": {"scenario": "measure_c", "gravity": "none", "kinematics": "emission",
                                      "mc_src_u": 0.3}},
    "michelson": {"label": "Плечо поперёк движения (Майкельсон–Морли), эфир (модификация)",
                  "params": {"scenario": "measure_c", "gravity": "none", "kinematics": "ether", "mc_orient": "y"}},
    "lensing": {"label": "Чёрная дыра 10 M☉: отклонение, тень, два изображения", "params": {"scenario": "lensing"}},
    "lensing_newton": {"label": "Ньютоновы корпускулы у чёрной дыры (модификация)",
                       "params": {"scenario": "lensing", "kinematics": "emission", "gravity": "newton",
                                  "ln_radius_km": 29.5}},
    "andromeda": {"label": "Парадокс Андромеды: пешеходы 1.4 м/с", "params": {"scenario": "andromeda",
                                                                              "gravity": "none"}},
    "andromeda_fast": {"label": "Парадокс Андромеды: наблюдатели ±1.499·10⁸ м/с (0.5 c при стандартном c)",
                       "params": {"scenario": "andromeda", "gravity": "none", "an_walk": 0.5 * 299792458.0}},
})


MASSIVE = ("sun_earth", "lensing")  # scenarios with a gravitating body: there the gravity law matters
_KIN = dict(KINEMATICS)
_GRAV = dict(GRAVITY)


def _short(label):
    return label.split(" (")[0]


def _adjust_laws(p) -> list[str]:
    """Review UX-params P12 (owner, 2026-11-04: a choice the form offers must work): the law sets of the engine allow
    GR only with SR and Newtonian light only with the emission kinematics (``Laws.validate``). When one law is changed
    and the other is left at its standard value, the world takes the other one as the nearest law that goes with it
    and says so (the returned lines; ``p`` is changed in place, so that the header's parameters and the "modified
    physics" list are the ones in force); two changed laws that do not go together are refused, saying what to
    change. In a scene without a gravitating body (measuring c, Andromeda) the gravity law has nothing to act on and
    is set to «Без гравитации». A lens of radius 0 (a black hole) is GR's object: without GR the world gives the body
    the horizon's radius 2GM/c² of the same mass, so that it is a body that stops light (the preset
    «lensing_newton»'s choice)."""
    out = []
    k, g = p["kinematics"], p["gravity"]
    massive = p["scenario"] in MASSIVE
    if g == "GR" and k != "SR":
        if massive and k == "emission":
            g = "newton"
            why = (f"ОТО несовместима с баллистическим светом (метрика Шварцшильда локально лоренцева), поэтому "
                   f"гравитация — «{_short(_GRAV[g])}»: свет — корпускулы со скоростью c относительно источника, "
                   "притяжение тела отклоняет их вдвое слабее ОТО и без шапировской задержки.")
        else:
            g = "none"
            why = ("ОТО несовместима с эфиром (метрика Шварцшильда локально лоренцева), поэтому гравитация — «Без "
                   "гравитации»: тело не отклоняет и не задерживает свет, только поглощает его; движение тел "
                   "(орбита Земли) остаётся заданным." if massive and k == "ether" else
                   "в этой сцене нет тяготеющего тела, поэтому гравитация — «Без гравитации» (для неё ОТО и "
                   f"«{_short(_KIN[k])}» не сочетаются, но здесь это ничего не меняет).")
        out.append(f"Кинематика «{_short(_KIN[k])}» с гравитацией по умолчанию (ОТО): {why} Чтобы вернуть ОТО, "
                   "выберите кинематику СТО.")
    elif g == "newton" and k == "SR":
        if massive:
            k = "emission"
            out.append("Гравитация «Ньютон: свет как корпускулы» задана для корпускул, летящих со скоростью c "
                       "относительно источника, поэтому кинематика — баллистическая (Ритц), а не СТО: скорость света "
                       "зависит от скорости источника. Чтобы вернуть СТО, выберите гравитацию ОТО или «Без гравитации».")
        else:
            g = "none"
            out.append("В этой сцене нет тяготеющего тела, поэтому ньютоново притяжение света не на что применить: "
                       "гравитация — «Без гравитации», кинематика остаётся СТО.")
    elif g == "newton" and k == "ether":
        if massive:
            raise ValueError("ньютоново притяжение света задано для корпускул (баллистическая кинематика), а в мире "
                             "с эфиром свет — волна в эфире: выберите «Кинематика» = баллистическая (Ритц) или "
                             "«Гравитация» = «Без гравитации»")
        g = "none"
        out.append("В этой сцене нет тяготеющего тела: гравитация — «Без гравитации» (ньютоново притяжение света с "
                   "эфиром не сочетается, но здесь это ничего не меняет).")
    p["kinematics"], p["gravity"] = k, g
    if p["scenario"] == "lensing" and g != "GR" and p["ln_radius_km"] == 0.0:
        rs_km = 2 * GM_SUN * p["ln_mass"] / (C_SI * p["c_factor"]) ** 2 / 1e3
        r_max = SCHEMA.by_id["ln_radius_km"].max  # the header's parameters must stay inside the form's range
        p["ln_radius_km"] = min(rs_km, r_max)
        out.append("Радиус тела 0 (чёрная дыра) имеет смысл только в ОТО; без неё тело взято радиусом горизонта той "
                   f"же массы, 2GM/c² = {rs_km:.4g} км" + (f" (ограничен пределом формы {r_max:.4g} км)"
                                                            if rs_km > r_max else "")
                   + ": оно поглощает свет, который в него попал.")
    return out


COLORS = {"star": "#f5b700", "planet": "#3d8bfd", "observer": "#e8590c", "beacon": "#c2255c",
          "galaxy": "#7048e8", "station": "#2b8a3e"}
OBS_COLORS = ["#e8590c", "#2b8a3e", "#1971c2", "#9c36b5", "#c92a2a"]


class Simulation(BaseSimulation):
    speed_range = (1e-12, 1e18)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        self.adjusted = _adjust_laws(p)  # P12: the dependent law and the lens's size chosen by the world, stated
        self.laws = Laws(p["kinematics"], p["gravity"], float(p["c_factor"]))
        errs = self.laws.validate()
        if errs:
            raise ValueError("; ".join(errs))
        self.planned = []
        self.scn = getattr(self, "_scn_" + p["scenario"])(p)
        self.default_speed = self.scn["speed"]
        if self.adjusted:
            note = "Мир изменил зависимые параметры: " + " ".join(self.adjusted)
            self.scn["text"] = note + "\n\n" + self.scn["text"]
            self._msg({"type": "notice", "t": 0.0, "text": note})

    def _laws_text(self):
        L = self.laws
        parts = [dict(KINEMATICS)[L.kinematics].split(" (")[0]]
        parts.append(dict(GRAVITY)[L.gravity].split(" (")[0])
        if L.c_factor != 1.0:
            parts.append(f"c × {L.c_factor:g}")
        return ", ".join(parts)

    def _plan(self, t, obj_id, text):
        """A scripted world event from the initial data: shown to the view in advance as planned (review R14)."""
        p = self.world.objects[obj_id].wl.pos(t)
        self.planned.append({"t": t, "obj": obj_id, "x": float(p[0]), "y": float(p[1]), "text": text})

    # message buffering until the header is out
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- scenarios ------------------------------------------------------------------------------------
    def _new_world(self, body, center, radius):
        self.world = World(self.laws, body, center, radius, self.params["n_rays"], self._msg)
        return self.world

    def _obs(self, oid, name, x0, v, color, movable=True, kind="observer"):
        wl = Piecewise.start(self.laws, self.world.rs, 0.0, x0, v)
        o = Obj(oid, name, kind, color, wl, movable=movable)
        self.world.add(o)
        return o

    def _scn_sun_earth(self, p):
        gm = GM_SUN * p["se_mass"]
        R = p["se_radius_km"] * 1e3
        d = p["se_distance_au"] * AU
        body = {"gm": gm, "radius": R, "name": "Солнце"}
        w = self._new_world(body, [0.5 * d, 0.0], 1.6 * d)
        rs = w.rs
        if R <= rs * 1.5:
            raise ValueError("радиус Солнца меньше 1.5 rs: возьмите сценарий «линза»")
        # the central body's own clock is not used (its worldline is the centre r = 0)
        w.add(Obj("sun", "Солнце", "star", COLORS["star"], Piecewise.start(self.laws, 0.0, 0.0, [0.0, 0.0], [0, 0]),
                  radius=R, receiver=False))
        flare = Obj("flare", "Вспышка на Солнце", "beacon", "#ff922b",
                    Piecewise.start(self.laws, rs, 0.0, [R * (1 + 1e-9), 0.0], [0, 0]), receiver=False)
        w.add(flare)
        if p["se_orbit"]:
            # Kepler's third law (exact for circular orbits in Schwarzschild coordinates); the orbit is the
            # scenario's prescribed worldline also when the light's gravity is switched off
            earth_wl = Orbit(self.laws, rs, d, math.sqrt(gm / d**3))
        else:
            earth_wl = Piecewise.start(self.laws, rs, 0.0, [d, 0.0], [0.0, 0.0])
        w.add(Obj("earth", "Земля", "planet", COLORS["planet"], earth_wl, radius=R_EARTH))
        w.add(Obj("station", "Станция (покоится в точке старта Земли)", "station", COLORS["station"],
                  Piecewise.start(self.laws, rs, 0.0, [d, 0.0], [0.0, 0.0])))
        self._obs("rocket", "Ракета", [0.5 * d, 0.0], [0.0, 0.0], OBS_COLORS[2])
        w.schedule({"t": 0.0, "kind": "scripted", "silent": True, "deps": set(),
                    "do": lambda: w.flash("flare", 0.0, label="вспышка на поверхности Солнца")})
        self._plan(0.0, "flare", "вспышка на Солнце")
        self._initial_checks_sun_earth(p, d, R)
        actions = [self._act_flash(), self._act_boost(), self._act_train()]
        if w.gr:
            actions.append(self._act_measure("Локально измерить c (статичный наблюдатель, ОТО)"))
        return {"speed": 20.0, "actions": actions,
                "view": {"center": [0.5 * d, 0.0], "half": 0.62 * d, "unit": "au"},
                "diagram": {"axis": "x", "x0": -0.05 * d, "x1": 1.05 * d, "t0": -20.0, "t1": 1.3 * d / self.laws.c},
                "text": ("В момент 0 на поверхности Солнца вспыхивает свет. Фронт уходит от места вспышки по законам "
                         f"этого запуска ({self._laws_text()}); когда он доходит до ракеты, станции и Земли, в журнале "
                         "появляется событие с вычисленным временем полёта и показанием часов получателя. Станция "
                         "покоится там, где Земля была в момент вспышки; Земля идёт по заданной круговой орбите "
                         "(закон Кеплера для массы Солнца; при выключенной гравитации это остаётся заданным движением). "
                         "«1:1» — реальное время.")}

    def _initial_checks_sun_earth(self, p, d, R):
        w = self.world
        if not w.gr:
            return
        rs = w.rs
        st = w.objects["station"]
        self._msg({"type": "check", "t": 0.0, **_check(
            "rate_station", "Ход часов станции dτ/dt (метрика) — самосогласованность", st.wl.tau(1.0) - st.wl.tau(0.0),
            checks.static_clock_rate(d, rs), "", group="Самосогласованность",
            note="для покоящихся часов общая формула метрики совпадает с √(1 − rs/r) тождественно; независимая "
                 "проверка — серия импульсов со станции (красное смещение)")})
        e = w.objects["earth"]
        if isinstance(e.wl, Orbit):
            self._msg({"type": "check", "t": 0.0, **_check(
                "rate_earth", "Ход часов Земли на орбите dτ/dt (метрика)", e.wl.rate(),
                checks.circular_orbit_clock_rate(d, rs), "", group="ОТО", note="круговая геодезическая: √(1 − 1.5 rs/r)")})

    def _scn_measure_c(self, p):
        c = self.laws.c
        D = p["mc_src_km"] * 1e3
        L0 = p["mc_L0_km"] * 1e3
        betas = [p["mc_v1"], p["mc_v2"], p["mc_v3"]]
        w = self._new_world(None, [0.0, 0.0], 3.0 * D + 6 * L0)
        u = p["mc_src_u"] * c
        # one source on the axis; the three observers meet at the origin at t = 0 with different velocities,
        # so every one of them measures light that runs along its rod (collinear)
        w.add(Obj("src", "Источник", "beacon", COLORS["beacon"],
                  Piecewise.start(self.laws, 0.0, 0.0, [-D, 0.0], [u, 0.0]), receiver=False))
        for i, beta in enumerate(betas):
            # the name carries no velocity: it changes with every boost (the table shows the current one)
            o = self._obs(f"obs{i + 1}", f"Наблюдатель {i + 1}", [0.0, 0.0], [beta * c, 0.0], OBS_COLORS[i])
            o.apparatus = Apparatus(self.laws, o.name, o.wl, L0, p["mc_orient"], p["mc_sync"])
            w.build_apparatus(o, 0.0)
        tf = p["mc_t_flash_ms"] * 1e-3
        w.schedule({"t": tf, "kind": "scripted", "silent": True, "deps": set(),
                    "do": lambda: w.flash("src", tf, label="вспышка источника")})
        self._plan(tf, "src", "вспышка источника")
        return {"speed": 1e-3, "actions": [self._act_flash(), self._act_boost(),
                                           self._act_measure("Измерить c прибором (туда-обратно)"),
                                           self._act_train()],
                "view": {"center": [-0.3 * D, 0.0], "half": 0.9 * D, "unit": "km"},
                "diagram": {"axis": "x", "x0": -1.1 * D, "x1": 0.8 * D, "t0": -0.1 * D / c, "t1": 2.5 * D / c},
                "text": (f"Законы запуска: {self._laws_text()}. "
                         "Три наблюдателя встречаются в начале координат в момент 0 с разными скоростями и несут "
                         "стержни длины L₀ (в своей системе покоя) с часами на концах A и B (B — дальний конец). "
                         "Сначала каждый синхронизирует часы B световым обменом (видно на диаграмме), затем "
                         f"в момент {fmt_s(tf)} источник вспыхивает. Скорость света вычисляется по показаниям часов "
                         "в событиях прохождения света через концы стержня; результат приходит к наблюдателю, "
                         "когда до A доходит сигнал о показании B. «Измерить» — замер туда-обратно своим светом. "
                         "«Изменить скорость» разгоняет наблюдателя: прибор разбирается, собирается заново и "
                         "заново синхронизируется.")}

    def _scn_lensing(self, p):
        gm = GM_SUN * p["ln_mass"]
        rs0 = 2 * gm / self.laws.c**2  # scale unit even when gravity is switched off
        R = p["ln_radius_km"] * 1e3
        body = {"gm": gm, "radius": R, "name": "Линза"}
        xs = -p["ln_src_rs"] * rs0
        xo = p["ln_obs_rs"] * rs0
        span = max(-xs, xo)
        w = self._new_world(body, [0.0, 0.0], 1.35 * span)
        rs = w.rs
        w.add(Obj("lens", "Чёрная дыра" if R <= rs else "Тело-линза", "star", "#212529",
                  Piecewise.start(self.laws, 0.0, 0.0, [0.0, 0.0], [0, 0]), radius=max(R, rs), receiver=False))
        w.add(Obj("src", "Источник", "beacon", COLORS["beacon"],
                  Piecewise.start(self.laws, rs, 0.0, [xs, p["ln_src_y_rs"] * rs0], [0, 0]), receiver=False))
        self._obs("obs", "Наблюдатель", [xo, 0.0], [0.0, 0.0], OBS_COLORS[0])

        def at_zero():
            w.flash("src", 0.0, label="вспышка источника")
            if p["ln_plane"]:
                rays, ys = w.plane_wave(0.0, -0.5 * span, p["ln_plane_hw_rs"] * rs0, 121)
                self._deflection_checks(rays, ys)

        w.schedule({"t": 0.0, "kind": "scripted", "silent": True, "deps": set(), "do": at_zero})
        self._plan(0.0, "src", "вспышка источника")
        if w.gr:
            self._msg({"type": "check", "t": 0.0, **_check(
                "bc", "Критический прицельный параметр b_c / rs (фотонная сфера)", None,
                checks.b_crit(rs) / rs, "", group="ОТО",
                note="лучи с b < b_c захватываются; граница по пучку появится после его расчёта")})
        actions = [self._act_flash(), self._act_train(), self._act_boost()]
        if w.gr:
            actions.append(self._act_measure("Локально измерить c (статичный наблюдатель, ОТО)"))
        return {"speed": 2.5 * span / self.laws.c / 20.0, "actions": actions,
                "view": {"center": [0.0, 0.0], "half": 0.45 * span, "unit": "rs", "rs": rs0},
                "diagram": {"axis": "x", "x0": 1.25 * xs, "x1": 1.25 * xo, "t0": -0.05 * span / self.laws.c,
                            "t1": 3.0 * span / self.laws.c},
                "text": ("Слева — параллельный пучок, у источника — вспышка. Каждый луч считается по законам запуска "
                         f"({self._laws_text()}). Что фронт делает возле тела — запаздывает, огибает, захватывается "
                         "или проходит прямо — видно по рассчитанным лучам; наблюдатель получает столько изображений и "
                         "в такие моменты, какие нашёл запуск (события в журнале). Проверки появляются, когда лучи "
                         "действительно дошли до горизонта или вышли из сцены.")}

    def _deflection_checks(self, rays, ys):
        """Compare the RK fan with exact quadrature on the same finite path; the capture boundary vs b_c."""
        w = self.world
        if not w.gr:
            return
        from lfphys.core.gravity import schwarzschild as S
        rs = w.rs
        f = lambda r: 1.0 - rs / r
        esc_b, cap_b = [], []
        t_end = {}
        picks = []
        for i in range(rays.n):
            T, X, Y = rays.ray(i)
            r0 = math.hypot(X[0], Y[0])
            b = abs(ys[i]) / math.sqrt(f(r0))  # L of a ray launched along +x in the static frame
            t_end[b] = T[-1]
            if rays.status[i] == 0:
                esc_b.append(b)
                if b > 3.0 * rs and len(picks) < 3 and ys[i] > 0:
                    picks.append((i, b, r0, math.hypot(X[-1], Y[-1]), X, Y, T[-1]))
            elif rays.status[i] == 2:
                cap_b.append(b)

        def later(t, chk):  # revealed when the run's time reaches the rays' fate (review R6)
            w.schedule({"t": t, "kind": "check", "silent": True, "deps": set(), "checks": [chk]})

        if esc_b and cap_b:
            lo, hi = max(cap_b), min(b for b in esc_b if b > max(cap_b))
            mid = 0.5 * (lo + hi)
            later(max(t_end[lo], t_end[hi]), _check(
                "bc", "Критический прицельный параметр b_c / rs: граница захвата пучка", mid / rs,
                checks.b_crit(rs) / rs, "", group="ОТО", tol=0.5 * (hi - lo) / mid,
                note=f"граница между захваченными и ушедшими лучами пучка: [{lo / rs:.4f}, {hi / rs:.4f}] rs; "
                     "точность ограничена шагом лучей; эталон 3√3/2 rs"))
        for i, b, r0, r1, X, Y, te in picks[-2:]:
            phi_rk = abs(np.unwrap(np.arctan2(Y, X))[-1] - np.unwrap(np.arctan2(Y, X))[0])
            rtp = S.turning_point(b, rs)
            p1, _ = S.integrals(b, rtp, r0, rs, self.laws.c, rtp)
            p2, _ = S.integrals(b, rtp, r1, rs, self.laws.c, rtp)
            later(te, _check(
                f"swept_{i}", f"Угол, заметённый лучом b = {b / rs:.3f} rs (RK против квадратуры)", phi_rk, p1 + p2,
                "рад", group="ОТО", note="один и тот же конечный путь: проверка интегратора геодезических"))
            later(te, _check(
                f"defl_{i}", f"Отклонение того же луча на бесконечности (квадратура, справочный расчёт)",
                S.deflection_from_quadrature(b, rs), checks.darwin_deflection(rtp, rs), "рад", group="ОТО",
                note=f"не событие запуска: путь от −∞ до +∞; эталон — формула Дарвина (эллиптические интегралы); "
                     f"слабое поле 2rs/b = {2 * rs / b:.6g}"))

    def _scn_andromeda(self, p):
        c = self.laws.c
        D = p["an_dist_mly"] * 1e6 * LIGHT_YEAR
        v = p["an_walk"]
        if self.laws.relativistic and v >= c:  # P7: the walkers' worldlines would not be timelike in this world
            raise ValueError(f"пешеходы не быстрее света этого мира: скорость пешеходов {v:.4g} м/с ≥ c × "
                             f"{self.laws.c_factor:g} = {c:.4g} м/с (в СТО тело не догоняет свет). Уменьшите скорость "
                             f"пешеходов ниже {c:.4g} м/с или увеличьте множитель «Скорость света, × c» выше "
                             f"{v / C_SI:.4g}")
        w = self._new_world(None, [0.5 * D, 0.0], 1.2 * D)
        w.add(Obj("earth", "Земля", "planet", COLORS["planet"], Piecewise.start(self.laws, 0.0, 0.0, [0, 0], [0, 0]),
                  radius=R_EARTH, receiver=True))
        w.add(Obj("andromeda", "Андромеда", "galaxy", COLORS["galaxy"],
                  Piecewise.start(self.laws, 0.0, 0.0, [D, 0.0], [0, 0]), radius=5e20, receiver=True))
        self._obs("walk_to", "Идёт к Андромеде", [0.0, 0.0], [v, 0.0], OBS_COLORS[0])
        self._obs("stay", "Стоит", [0.0, 0.0], [0.0, 0.0], OBS_COLORS[1])
        self._obs("walk_from", "Идёт от Андромеды", [0.0, 0.0], [-v, 0.0], OBS_COLORS[2])
        tA = p["an_event_days"] * DAY
        w.schedule({"t": tA, "kind": "scripted", "silent": True, "deps": set(),
                    "do": lambda: w.flash("andromeda", tA, label="событие на Андромеде (флот стартует)")})
        self._plan(tA, "andromeda", "событие на Андромеде (флот стартует)")
        # simultaneity at t = 0 from the observers' frames (computed) vs the closed form
        for oid in ("walk_to", "walk_from"):
            o = w.objects[oid]
            M = self.laws.frame_matrix(o.wl.vel(0.0))
            # event on Andromeda's worldline with ct' = 0: M00 c t + M01 D = 0
            t_sim = -M[0, 1] * D / (M[0, 0] * c)
            self._msg({"type": "check", "t": 0.0, **_check(
                f"simul_{oid}", f"«{o.name}»: «сейчас» на Андромеде в момент t = 0 (лаб. время, сут)",
                t_sim / DAY, checks.simultaneity_offset(o.wl.vel(0.0)[0], D, c, self.laws.kinematics) / DAY, "сут",
                group="Одновременность", note="эталон: v·D/c² (СТО), 0 при абсолютном времени")})
        return {"speed": 1e12, "actions": [self._act_flash(), self._act_boost()],
                "view": {"center": [0.5 * D, 0.0], "half": 0.65 * D, "unit": "ly"},
                "diagram": {"axis": "x", "x0": -0.05 * D, "x1": 1.05 * D, "t0": -0.3 * D / c, "t1": 1.3 * D / c,
                            "zooms": [{"label": "у Андромеды ±10 сут", "x0": D - c * 12 * DAY, "x1": D + c * 12 * DAY,
                                       "t0": tA - 10 * DAY, "t1": tA + 10 * DAY},
                                      {"label": "у Земли ±10 сут", "x0": -c * 12 * DAY, "x1": c * 12 * DAY,
                                       "t0": -10 * DAY, "t1": 10 * DAY}]},
                "text": ("Три наблюдателя проходят мимо друг друга на Земле в момент 0 с разными скоростями. На "
                         "диаграмме — их линии одновременности («сейчас»), посчитанные по законам запуска "
                         f"({self._laws_text()}); кнопки «у Андромеды ±10 сут» и «у Земли ±10 сут» приближают диаграмму. "
                         "Таблица «Объекты и часы» показывает, какой момент на Андромеде каждый наблюдатель называет "
                         "«сейчас» и было ли там уже запланированное событие. Части среза, которые лежат в лабораторном "
                         "будущем, ещё не вычислены и показаны бледно. Свет от события приходит к наблюдателям в "
                         "моменты, которые вычисляет запуск.")}

    # --- actions --------------------------------------------------------------------------------------
    def _objs(self, pred):
        return [{"value": o.id, "label": o.name} for o in self.world.objects.values() if pred(o)]

    def _act_flash(self):
        return {"name": "flash", "label": "Вспышка", "args": [
            {"id": "obj", "label": "Кто", "type": "select", "options": self._objs(lambda o: o.kind != "star")}]}

    def _act_flash_all(self):
        return {"name": "flash_all", "label": "Вспышка всех источников", "args": []}

    def _act_boost(self):
        """A live action (owner, 2026-10-23: changes apply at once): choose who, then move the speed or direction;
        each committed value is a boost at the current moment. ``current`` gives each object's present velocity."""
        c = self.laws.c
        cur = {}
        for o in self.world.objects.values():
            if o.movable:
                v = o.wl.vel(self.t)
                cur[o.id] = {"v": float(math.hypot(v[0], v[1]) / c), "angle": float(math.degrees(math.atan2(v[1], v[0])))}
        return {"name": "boost", "label": "Скорость (меняется сразу)", "mode": "live", "key": "obj",
                "help": "Отпустите ползунок или нажмите Enter: объект мгновенно получает новую скорость в текущий "
                        "момент. Малые скорости вводите числом (1,4 м/с ≈ 4,67e-9 c).",
                "current": cur, "args": [
                    {"id": "obj", "label": "Кто", "type": "select", "options": self._objs(lambda o: o.movable)},
                    {"id": "v", "label": "скорость, доли c", "type": "float", "default": 0.0, "min": 0.0,
                     "max": 0.99},
                    {"id": "angle", "label": "направление, °", "type": "float", "default": 0.0, "min": -180.0,
                     "max": 180.0}]}

    def _actions_now(self):
        """The scenario's actions with the current velocities in the live speed control."""
        return [self._act_boost() if a.get("name") == "boost" else a for a in self.scn["actions"]]

    def _act_measure(self, label):
        pred = (lambda o: o.apparatus is not None) if self.world.flat else (lambda o: o.kind in ("observer", "station"))
        return {"name": "measure", "label": label, "args": [
            {"id": "obj", "label": "Кто", "type": "select", "options": self._objs(pred)}]}

    def _act_train(self):
        return {"name": "train", "label": "Серия импульсов (частота)", "args": [
            {"id": "obj", "label": "Источник", "type": "select", "options": self._objs(lambda o: o.kind != "star")},
            {"id": "period", "label": "Период по часам источника, с", "type": "float", "default": 1.0},
            {"id": "count", "label": "Сколько", "type": "int", "default": 5}]}

    def action(self, name, args):
        w = self.world
        t = self.t
        if name == "flash":
            w.flash(args["obj"], t)
            return f"{w.objects[args['obj']].name}: вспышка"
        if name == "flash_all":
            n = 0
            for o in list(w.objects.values()):
                if o.kind == "beacon":
                    w.flash(o.id, t, label="вспышка источника")
                    n += 1
            return f"вспышка {n} источников"
        if name == "boost":
            unit = {"c": self.laws.c, "kms": 1e3, "ms": 1.0}[args.get("unit", "c")]
            sp = float(args["v"]) * unit
            a = math.radians(float(args.get("angle", 0.0)))
            try:
                w.boost(args["obj"], [sp * math.cos(a), sp * math.sin(a)], t)
            finally:  # the speed control shows the velocity in force (also after a refused boost)
                self._msg({"type": "actions", "t": t, "actions": self._actions_now()})
            return f"{w.objects[args['obj']].name}: скорость {sp:.6g} м/с ({sp / self.laws.c:.6g} c), {math.degrees(a):.4g}°"
        if name == "measure":
            return w.measure(args["obj"], t)
        if name == "train":
            period = float(args["period"])
            count = int(args["count"])
            if not (period > 0 and 1 <= count <= 200):
                raise ValueError("период > 0, импульсов от 1 до 200")
            w.start_train(args["obj"], t, period, count)
            return f"{w.objects[args['obj']].name}: серия из {count} импульсов, период {fmt_s(period)}"
        raise ValueError(f"неизвестное действие {name!r}")

    def engine_modules(self):
        L = self.laws
        mods = ["core.constants", "core.worldlines", "core.gravity.rays", "core.gravity.arrivals", "laws.light"]
        mods.append("core.relativity" if L.relativistic else "theories.alternatives.kinematics")
        if L.gravity == "GR":
            mods.append("core.gravity.schwarzschild")
        elif L.gravity == "newton":  # light as Newtonian corpuscles: a refuted alternative (review 2026-10-23, E9)
            mods.append("theories.alternatives.newton_light")
        return mods

    # --- contract -------------------------------------------------------------------------------------
    def header(self):
        w = self.world
        objs = []
        for o in w.objects.values():
            objs.append({"id": o.id, "name": o.name, "kind": o.kind, "color": o.color, "radius": o.radius,
                         "movable": o.movable, "apparatus": o.apparatus is not None, "wl": o.wl.to_json(),
                         "L0": o.apparatus.L0 if o.apparatus else None})
        body = None
        if w.body:
            body = {"gm": w.gm, "radius": w.body.get("radius", 0.0), "rs": w.rs, "r_abs": w.r_abs,
                    "name": w.body.get("name", "")}
        mods = SCHEMA.modifications(self.params)
        if self.params["scenario"] != "lensing" and self.params["scenario"] != "sun_earth":
            mods = [m for m in mods if m["id"] != "gravity"]  # no mass in the scene: gravity is irrelevant
        return {
            "title": dict(SCN)[self.params["scenario"]],
            "scenario": self.params["scenario"],
            "text": self.scn["text"],
            "laws": {"kinematics": self.laws.kinematics, "gravity": self.laws.gravity, "c": self.laws.c,
                     "c_factor": self.laws.c_factor,
                     "kinematics_label": dict(KINEMATICS)[self.laws.kinematics],
                     "gravity_label": dict(GRAVITY)[self.laws.gravity]},
            "modifications": mods,
            "objects": objs, "body": body,
            "flat": w.flat, "gr": w.gr,
            "scene": {"center": w.scene_center.tolist(), "radius": w.scene_radius},
            "view": self.scn["view"], "diagram": self.scn["diagram"], "planned": self.planned,
            "actions": self._actions_now(),
            "units": {"au": AU, "ly": LIGHT_YEAR, "rs": self.scn["view"].get("rs", w.rs)},
        }, {}

    def advance(self, t_target):
        self.world.advance(t_target)
        self.t = t_target

    def frame(self):
        return self.world.frame_state(self.t), {}

    def next_event_time(self):
        return self.world.next_event_time()


VIZ = {
    "id": "v01_light_travel",
    "title": "Свет на больших расстояниях",
    "summary": ("Конечная скорость света от Солнца до Земли, конусы света, гравитационное отклонение, измерение "
                "скорости света движущимися наблюдателями, относительность одновременности (парадокс Андромеды)."),
    "purpose": ("Исследование конуса времени, абсолютности скорости света и парадокса Андромеды; законы можно "
                "намеренно менять (эфир, баллистический свет, ньютоновы корпускулы, другое c)."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
