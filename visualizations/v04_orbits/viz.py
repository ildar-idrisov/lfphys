# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v04: orbits and clocks - a test body around a central mass in general relativity and in Newton's gravity.

What the run computes (README.md of this folder has the model in full):
* the body's orbit from its initial data: in GR the exact Schwarzschild geodesic (lfphys.core.gravity.orbit_stream:
  the Binet equation with coordinate and proper time, events located by the integrator), in a Newton world the
  Newtonian orbit (lfphys.theories.approx.newton.integrate_body);
* the orbit is computed ahead in chunks and revealed as the world's coordinate time reaches it; a live change of the
  initial data or an action (a boost, a new launch) starts a new segment at the current moment and withdraws the
  computed future;
* the body's clock (proper time) next to the distant observer's coordinate time, and its rate dtau/dt;
* the run's own measurements: periapses and apoapses, the advance of the periapsis per orbit (the angle between
  successive periapses), periods, the conservation of e and l, the fall through the horizon;
* checks against closed forms: the exact elliptic integral of the advance, the weak-field formula 6 pi M/p (leading
  order), dtau/dt = sqrt(1 - 3M/r) and Kepler's period on circular orbits, the cycloid of a radial fall, the
  impact speed, an independent second integration scheme; in a Newton world energy, angular momentum, Kepler's
  period and the closed ellipse.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.constants import AU, C, DAY, GM_SUN, R_SUN
from lfphys.core.gravity import kerr, orbit_stream, orbits
from lfphys.theories.approx import ppn

from .engine.body import GRTrack, NewtonTrack

# Mercury: NASA NSSDCA Mercury Fact Sheet, J2000 mean elements (a = 0.38709893 AU, e = 0.20563069); the GR perihelion
# advance 42.98"/century: Will, Living Rev. Relativ. 17, 4 (2014), Eq. (65) with gamma = beta = 1 and no solar J2.
# Both checked against the source texts: lfphys/sources/verification_2026-10-23.md, items 1 and 2.
MERCURY_A_AU = 0.38709893
MERCURY_ECC = 0.20563069
MERCURY_GR_ARCSEC_PER_CENTURY = 42.98
M_SUN_LEN = GM_SUN / C**2
MERCURY_R0 = MERCURY_A_AU * (1.0 - MERCURY_ECC) * AU / M_SUN_LEN   # perihelion in units of GM_sun/c^2
MERCURY_K = math.sqrt(1.0 + MERCURY_ECC)  # perihelion speed / circular speed (vis-viva; GR differs by O(M/r) ~ 3e-8)
CENTURY_S = 36525.0 * DAY
GHOST_SLICE_S = 0.03  # wall seconds of ghost catch-up per world step (review V4-16)
# the apsis of an orbit with relative spread s = (r_apo - r_peri)/r_peri is located to ~APSIS_PHASE/s rad (du/dphi
# ~ s at its zero; the integration error of du/dphi ~1e-15); measured in tests, used in the tolerances
APSIS_PHASE = 1e-14
APSIS_PHASE_NEWTON = 2e-13  # Newton: the apsis direction ~ (integration error ~1e-12 relative)/eccentricity
ARCSEC = math.pi / 180.0 / 3600.0

LAWS = [("GR", "ОТО (Шварцшильд)"), ("newton", "Ньютон (приближение)")]
LIVE_INIT = ("r0", "speed", "angle")


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("gravity", "Закон тяготения", "select", "GR", group="Законы", options=LAWS, standard="GR",
       help="ОТО — общепринятая. Ньютоново тяготение — приближение слабого поля и малых скоростей; мир с ним "
            "помечается как модифицированная физика."),
    _p("mass_msun", "Масса центрального тела, M☉", "float", 10.0, group="Центральное тело", min=1.0, max=1e9,
       log=True, help="Длина GM/c² (единица M) и время GM/c³ — от этой массы; GM☉ — номинальное значение МАС 2015 B3."),
    _p("radius_km", "Радиус тела, км (0 — чёрная дыра)", "float", 0.0, group="Центральное тело", min=0.0, max=1e8,
       help="В ОТО радиус должен быть больше 2M (иначе это чёрная дыра — задайте 0). Внешнее поле любого "
            "сферического тела — решение Шварцшильда (теорема Биркгофа)."),
    _p("r0", "Начальный радиус r₀, M (GM/c²)", "float", 20.0, group="Запуск тела", min=2.1, max=1e8, log=True,
       live=True, help="Радиус старта в единицах M = GM/c². Изменение применяется сразу: тело запускается заново "
                       "в текущий момент мира с текущего направления на центр."),
    _p("speed", "Скорость, доля круговой", "float", 1.2, group="Запуск тела", min=0.0, max=1.6, live=True,
       help="Скорость, измеренная неподвижным (статическим) наблюдателем в точке старта, в долях скорости "
            "круговой орбиты там: √(M/(r−2M)) в ОТО, √(GM/r) у Ньютона. Ниже 3M круговых орбит нет — там доля "
            "от скорости света."),
    _p("angle", "Направление скорости, ° от касательной (+ наружу)", "float", 0.0, group="Запуск тела",
       min=-90.0, max=90.0, live=True, help="0 — по касательной (против часовой стрелки), +90 — прямо от центра, "
                                             "−90 — прямо к центру."),
    _p("ghost", "Призрак другой теории", "bool", False, group="Отображение", live=True,
       help="Орбита из тех же начальных данных (тот же r₀, та же скорость) по другой теории: в мире ОТО — "
            "Ньютон, в мире Ньютона — ОТО. Пунктир; на мир не влияет."),
    _p("time_units", "Время на панелях", "select", "si", group="Отображение", live=True,
       options=[("si", "секунды (часы, сутки, годы)"), ("geo", "единицы GM/c³")]),
], presets={
    "default": {"label": "Чёрная дыра 10 M☉: розетка (перицентр 20M)", "params": {}},
    "mercury": {"label": "Меркурий у Солнца (слабое поле, 43″/век)",
                "params": {"gravity": "GR", "mass_msun": 1.0, "radius_km": R_SUN / 1e3, "r0": MERCURY_R0,
                           "speed": MERCURY_K, "angle": 0.0},
                "note": "a = 0.38709893 а.е., e = 0.20563069 (NASA NSSDCA, J2000), старт в перигелии; "
                        "эталон ОТО 42.98″/век — Will 2014, Living Rev. Relativ. 17, 4, ур. (65)"},
    "neutron_star": {"label": "Нейтронная звезда: сильная прецессия",
                     "params": {"gravity": "GR", "mass_msun": 1.4, "radius_km": 12.0, "r0": 10.0, "speed": 1.12,
                                "angle": 0.0},
                     "note": "иллюстративно: 1.4 M☉, R = 12 км ≈ 5.8M; перицентр 10M"},
    "bh_isco": {"label": "Чёрная дыра: круговая орбита у ISCO (6.2M)",
                "params": {"gravity": "GR", "mass_msun": 10.0, "radius_km": 0.0, "r0": 6.2, "speed": 1.0,
                           "angle": 0.0}},
    "plunge": {"label": "Падение внутрь ISCO (5.5M, скорость −0.5 %)",
               "params": {"gravity": "GR", "mass_msun": 10.0, "radius_km": 0.0, "r0": 5.5, "speed": 0.995,
                          "angle": 0.0}},
    "radial": {"label": "Радиальное падение с покоя с 20M (циклоида)",
               "params": {"gravity": "GR", "mass_msun": 10.0, "radius_km": 0.0, "r0": 20.0, "speed": 0.0,
                          "angle": 0.0}},
    "newton_ellipse": {"label": "Ньютон: замкнутый эллипс (призрак — ОТО)",
                       "params": {"gravity": "newton", "mass_msun": 10.0, "radius_km": 0.0, "r0": 20.0,
                                  "speed": 1.2, "angle": 0.0, "ghost": True}},
})

KIND_RU = {"bound": "связанная (эллипс с прецессией)", "circular": "круговая", "plunge": "падение на центр",
           "escape": "уход на бесконечность", "radial_fall": "радиальная: падение", "radial_escape": "радиальная: уход"}
KIND_RU_NEWTON = {**KIND_RU, "bound": "связанная (эллипс Кеплера)"}


def _kind_text(kind, law):
    return (KIND_RU if law == "GR" else KIND_RU_NEWTON).get(kind, kind)
END_RU = {"horizon": "падение за горизонт", "surface": "удар о поверхность тела", "center": "падение в центр",
          "escape": "уход на бесконечность"}


def _due(n: int) -> bool:
    """Which periapsis / turn numbers refresh the checks (all early ones, then sparsely: the record stays small)."""
    return n <= 4 or n in (6, 11, 21, 51) or (n - 1) % 100 == 0


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _fmt(v):
    if isinstance(v, bool):
        return "да" if v else "нет"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def _angle_text(rad: float) -> str:
    a = abs(rad)
    if a < math.radians(1.0):
        return f"{rad / ARCSEC:.6g}″"
    return f"{math.degrees(rad):.6g}°"


class Simulation(BaseSimulation):
    speed_range = (1e-10, 1e18)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        p = self.params
        self.law = p["gravity"]
        self.msun = float(p["mass_msun"])
        self.gm = self.msun * GM_SUN
        self.M_m = self.gm / C**2   # metres per M
        self.T_s = self.M_m / C     # seconds per GM/c^3
        self.R = p["radius_km"] * 1e3 / self.M_m  # body radius in M; 0 = black hole (GR) / point mass (Newton)
        if self.law == "GR" and 0.0 < self.R <= 2.0:
            raise ValueError(f"радиус {p['radius_km']:.6g} км не больше 2M = {2 * self.M_m / 1e3:.6g} км: такое тело "
                             "— чёрная дыра (задайте радиус 0)")
        # special radii of the Schwarzschild geometry (the Kerr closed forms at zero spin)
        self.special = {"horizon": kerr.horizons(0.0)[0], "photon": kerr.photon_orbit(0.0),
                        "mb": kerr.marginally_bound(0.0), "isco": kerr.isco(0.0)}
        self._buf = []
        self.seg = -1
        self.track = self.ghost = None
        self.t_launch = 0.0
        init = self._launch_data(p, 0.0)
        self._start_segment(init, "запуск тела", launch=True, ghost_on=bool(p["ghost"]))
        dyn = self._period_estimate(self.track) or self.track.dyn
        self.default_speed = float(min(max(dyn * self.T_s / 8.0, self.speed_range[0]), self.speed_range[1]))

    # --- engine modules of this world ------------------------------------------------------------------------
    def engine_modules(self):
        gr = ["core.gravity.orbit_stream", "core.gravity.orbits", "core.gravity.kerr"]
        if self.law == "GR":
            mods = ["core.constants"] + gr + ["theories.approx.ppn"]
            if self.params["ghost"]:
                mods.append("theories.approx.newton")
        else:
            mods = ["core.constants", "theories.approx.newton"]
            if self.params["ghost"]:
                mods += gr
        return mods

    # --- initial data ------------------------------------------------------------------------------------------
    def _v_ref(self, r, law):
        """The reference speed of the 'speed' parameter: the local circular speed (GR: sqrt(M/(r - 2M)), measured by
        the static observer; below 3M, where there is no circular orbit, c) or Newton's sqrt(GM/r)."""
        if law == "GR":
            return min(math.sqrt(1.0 / (r - 2.0)), 1.0)
        return math.sqrt(1.0 / r)

    def _launch_data(self, p, phi0):
        r0 = float(p["r0"])
        if self.R > 0 and r0 <= self.R:
            raise ValueError(f"r₀ = {r0:.6g}M внутри тела (радиус {self.R:.6g}M)")
        if self.law == "GR" and r0 <= 2.0:
            raise ValueError("r₀ внутри горизонта")
        k, alpha = float(p["speed"]), math.radians(float(p["angle"]))
        v = k * self._v_ref(r0, self.law)
        if self.law == "GR" and v >= 1.0:
            raise ValueError(f"локальная скорость {v:.6g} c не меньше скорости света")
        v_r, v_phi = v * math.sin(alpha), v * math.cos(alpha)
        if abs(v_phi) <= 1e-12 * v:
            v_phi = 0.0  # radial launch (cos 90 deg is not exactly zero in floating point)
        return {"r0": r0, "phi0": float(phi0), "v_r": v_r, "v_phi": v_phi, "v": v, "k": k,
                "alpha": float(p["angle"]), "how": "launch"}

    def _make_track(self, law, init, t0, tau0):
        r_stop = self.R if self.R > 0 else (2.0 if law == "GR" else 0.0)
        args = (init["r0"], init["phi0"], init["v_r"], init["v_phi"])
        if law == "GR":
            if math.hypot(init["v_r"], init["v_phi"]) >= 1.0:
                raise ValueError("для ОТО локальная скорость должна быть меньше c")
            if init["r0"] <= 2.0:
                raise ValueError("старт внутри горизонта")
            return GRTrack(*args, t0=t0, tau0=tau0, r_stop=r_stop)
        return NewtonTrack(*args, t0=t0, tau0=tau0, r_stop=r_stop)

    def _other(self):
        return "newton" if self.law == "GR" else "GR"

    # --- segments -------------------------------------------------------------------------------------------------
    def _start_segment(self, init, reason, launch, ghost_on):
        """Build the tracks first (may raise: then nothing changes), then commit the new segment at the current t."""
        tg = self.t / self.T_s
        if launch:
            tau0 = 0.0
        else:
            tau0 = self.track.state(tg, exact=True)["tau"]
        track = self._make_track(self.law, init, tg, tau0)
        ghost, ghost_note = None, None
        if ghost_on:
            try:
                ghost = self._make_track(self._other(), init, tg, tau0)
            except ValueError as e:
                ghost_note = f"призрак не построен: {e}"
        # commit
        self.seg += 1
        if launch:
            self.t_launch = self.t
        self.track, self.ghost, self.init = track, ghost, dict(init)
        self.seg_t0, self.seg_tau0 = self.t, tau0
        self.S = {"peri": [], "apo": [], "laps": [], "second": None, "notes": set(), "maxdev": 0.0,
                  "ghost_ends": set()}
        info = self._orbit_info(track, init)
        self.info = info
        p_est = self._period_estimate(track, init) or track.dyn
        self._msg({"type": "segment", "t": self.t, "seg": self.seg, "reason": reason, "launch": launch,
                   "law": self.law, "init": init, **info, "t_window": 4.0 * p_est * self.T_s,
                   "ghost": self._ghost_info(ghost) if ghost else None})
        self._msg({"type": "event", "t": self.t, "kind": "segment", "text": self._segment_text(reason, init, info)})
        if ghost_note:
            self._msg({"type": "notice", "t": self.t, "text": ghost_note})
        if info["kind"] == "circular" and self.law == "GR" and init["r0"] < self.special["isco"]:
            self._msg({"type": "notice", "t": self.t,
                       "text": f"Круговая орбита при r₀ = {init['r0']:.6g}M < ISCO = {self.special['isco']:g}M "
                               "неустойчива: ошибки округления (~10⁻¹⁶) нарастают, и тело уйдёт с неё."})
        self.advance(self.t)  # what happens at the launch instant itself (e.g. a start at a turning point)

    def _orbit_info(self, track, init):
        """Kind of orbit and the closed-form references for this segment (the run's checks compare with them)."""
        kind = track.info["kind"]
        ti = track.info
        d = {"kind": kind, "kind_text": _kind_text(kind, self.law), "r_peri": ti.get("r_peri"),
             "r_apo": ti.get("r_apo"), "e": None, "l": None, "em1": None, "elements": None,
             "adv_exact": None, "adv_ppn": None, "adv_series2": None, "period_ref": None, "period_t_ref": None,
             "rate_circ": None, "spread": ti.get("spread"), "moving": ti.get("moving"),
             "start_turning": ti.get("start_turning"), "double_root": ti.get("double_root"),
             "nearest_root": ti.get("nearest_root"), "u_cond": None, "u_sens": None}
        if self.law == "GR":
            d.update(e=track.e, l=track.l, em1=track.em1)
            if kind == "bound":
                try:  # references from e^2 - 1 itself (no cancellation; review V4-7)
                    el = orbits.elements(track.e, abs(track.l), track.em1)
                    d["elements"] = {k: float(v) for k, v in el.items()}
                    d["elements"]["a"] = el["p"] / (1.0 - el["ecc"] ** 2)
                    d["adv_exact"] = orbits.periapsis_advance(track.e, abs(track.l), track.em1)
                    a_m = d["elements"]["a"] * self.M_m
                    d["adv_ppn"] = ppn.periapsis_advance(self.gm, a_m, el["ecc"])
                    d["adv_series2"] = orbits.advance_series(el["p"], el["ecc"], 2)
                    d["period_t_ref"] = orbits.radial_period(track.e, abs(track.l), track.em1)["t"] * self.T_s
                    cond = orbits.turning_conditioning(track.e, abs(track.l), track.em1)
                    d["u_cond"] = {"apo": float(cond[0]), "peri": float(cond[1])}
                    # how a relative change of e^2 - 1 moves each turning point: |e^2-1| / (l^2 |f'(u)| u)
                    u = orbits.turning_points(track.e, abs(track.l), track.em1)
                    l2 = track.l * track.l
                    fp = [2.0 * (u[i] - u[(i + 1) % 3]) * (u[i] - u[(i + 2) % 3]) for i in (0, 1)]
                    d["u_sens"] = {"apo": abs(track.em1) / (l2 * abs(fp[0]) * u[0]),
                                   "peri": abs(track.em1) / (l2 * abs(fp[1]) * u[1])}
                except ValueError:
                    pass
            if kind == "circular":
                r = init["r0"]
                d["rate_circ"] = math.sqrt(1.0 - 3.0 / r)
                d["period_ref"] = 2.0 * math.pi * r**1.5 * self.T_s
        else:
            ti = track.info
            if ti.get("a"):
                d["elements"] = {"a": ti["a"], "ecc": ti["ecc"], "r_peri": ti["r_peri"], "r_apo": ti["r_apo"],
                                 "p": ti["a"] * (1 - ti["ecc"] ** 2)}
                d["period_ref"] = ti["period"] * self.T_s
                d["adv_exact"] = 0.0
            d["E"] = track.E0  # specific energy in c^2 (v^2/2 - GM/r)
            d["h"] = track.h0  # specific angular momentum in M c
        return d

    def _ghost_info(self, g):
        i = dict(g.info)
        i["law"] = g.theory
        i["kind_text"] = _kind_text(i["kind"], g.theory)
        return {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in i.items()}

    def _segment_text(self, reason, init, info):
        law = "ОТО" if self.law == "GR" else "Ньютон"
        s = (f"{reason[:1].upper() + reason[1:]}: r = {init['r0']:.6g}M, скорость {init['v']:.6g} c "
             f"({init['k']:.4g} от круговой), угол {init['alpha']:.4g}°. {law}: орбита — {info['kind_text']}")
        if info.get("r_peri") and (info["kind"] == "bound" or (info["kind"] == "escape" and (info.get("moving") or 0) <= 0)):
            s += f", перицентр {info['r_peri']:.6g}M"  # (an outward escape never passes the periapsis behind it)
        if info.get("r_apo") and info["kind"] in ("bound", "plunge", "radial_fall"):
            s += f", апоцентр {info['r_apo']:.6g}M"
        if info.get("adv_exact"):
            s += "; смещение перицентра за оборот (точная формула) " + _angle_text(info["adv_exact"])
        return s

    def _period_estimate(self, track, init=None):
        """A time scale of the orbit (M units) for the default speed and the plot window: 2 pi a^{3/2} (bound),
        2 pi r^{3/2} (circular); None otherwise. A display scale, not a measured or reference quantity."""
        i = track.info
        if i.get("kind") == "bound" and i.get("r_apo"):
            a = 0.5 * (i["r_peri"] + i["r_apo"])
            return 2 * math.pi * a**1.5
        if i.get("kind") == "circular":
            return 2 * math.pi * (init or self.init)["r0"] ** 1.5
        return None

    # --- live parameters ----------------------------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise ValueError("; ".join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return "без изменений"
        desc = "; ".join(f"{SCHEMA.by_id[k].label}: {_fmt(self.params[k])} → {_fmt(new[k])}" for k in changed)
        if any(k in LIVE_INIT for k in changed):
            init = self._launch_data(new, self._phi_now())
            ghost_on = bool(new["ghost"])
            old = self.params
            self.params = new  # _start_segment reads only init and ghost_on; restored if it raises
            try:
                self._start_segment(init, "новые начальные данные (" + desc + ")", launch=True, ghost_on=ghost_on)
            except ValueError:
                self.params = old
                raise
            return desc
        if "ghost" in changed:
            if new["ghost"]:
                st = self.init
                try:  # the other theory from this segment's initial data, from the segment's start
                    self.ghost = self._make_track(self._other(), st, self.seg_t0 / self.T_s, self.seg_tau0)
                except ValueError as e:
                    raise ValueError(f"призрак не построен: {e}")
                self._msg({"type": "ghost", "t": self.t, "seg": self.seg, "info": self._ghost_info(self.ghost)})
                # its past up to now (a computation about the other theory), in slices: a late switch must not block
                # the worker (review V4-16); what is not computed now follows in the next steps of the world
                self._reveal_ghost(self.t / self.T_s, budget=GHOST_SLICE_S)
            else:
                self.ghost = None
                self._msg({"type": "ghost", "t": self.t, "seg": self.seg, "info": None})
        self.params = new
        return desc

    def _phi_now(self):
        st = self.track.state(self.t / self.T_s) if self.track else None
        return float(st["phi"]) if st else 0.0

    # --- actions ------------------------------------------------------------------------------------------------
    def _actions(self):
        return [
            {"name": "boost", "label": "Толчок", "button": "толкнуть",
             "help": "Мгновенное изменение скорости вдоль движения (в системе неподвижного наблюдателя в этой "
                     "точке): доля текущей скорости, минус — торможение. Часы тела идут дальше.",
             "args": [{"id": "dv", "label": "Δv, доля скорости", "type": "float", "default": 0.05, "min": -1.0,
                       "max": 1.0}]},
            {"name": "relaunch", "label": "Новый запуск тела",
             "help": "Тело запускается заново из начальных данных панели «Запуск тела» (r₀, скорость, угол) в "
                     "текущий момент, с текущего направления на центр; часы тела — с нуля.", "args": []},
        ]

    def action(self, name, args):
        tg = self.t / self.T_s
        if name == "relaunch":
            init = self._launch_data(self.params, self._phi_now())
            self._start_segment(init, "новый запуск тела", launch=True, ghost_on=bool(self.params["ghost"]))
            return "тело запущено заново"
        if name == "boost":
            dv = float(args.get("dv", 0.05))
            if not -1.0 <= dv <= 1.0:
                raise ValueError("Δv — доля скорости от −1 до 1")
            if self.track.ended(tg):
                raise ValueError("тела на орбите нет (" + END_RU.get(self.track.end_event["kind"], "") + ")")
            st = self.track.state(tg, exact=True)
            vr, vp = st["v_r"], st["v_phi"]
            if vr is None:
                raise ValueError("состояние тела в этот момент не найдено")
            v = math.hypot(vr, vp)
            if v == 0.0:
                raise ValueError("тело покоится относительно неподвижного наблюдателя: направление движения "
                                 "не определено")
            f = 1.0 + dv
            vr, vp = vr * f, vp * f
            if abs(vp) <= 1e-12 * abs(vr):
                vp = 0.0
            if abs(vr) <= 1e-12 * abs(vp):
                vr = 0.0  # the dense-output state of a circular orbit has v_r ~ 1e-17: rounding (review V4-1)
            if self.law == "GR" and math.hypot(vr, vp) >= 1.0:
                raise ValueError(f"после толчка скорость {math.hypot(vr, vp):.6g} c — не меньше c")
            r = st["r"]
            vref = self._v_ref(r, self.law)
            init = {"r0": r, "phi0": st["phi"], "v_r": vr, "v_phi": vp, "v": math.hypot(vr, vp),
                    "k": math.hypot(vr, vp) / vref, "alpha": math.degrees(math.atan2(vr, abs(vp))) if vp or vr else 0.0,
                    "how": "boost"}
            self._start_segment(init, f"толчок Δv = {dv:+.4g} скорости", launch=False,
                                ghost_on=bool(self.params["ghost"]))
            return f"толчок: скорость {v:.6g} c → {math.hypot(vr, vp):.6g} c на r = {r:.6g}M"
        raise ValueError(f"неизвестное действие {name!r}")

    # --- messages and checks --------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None):
        rel = None
        if ref is not None and value is not None and ref != 0 and math.isfinite(value):
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": f"s{self.seg}.{cid}", "label": label, "value": value, "ref": ref,
             "unit": unit, "rel": rel, "group": self._group(), "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        self._msg(d)

    def _group(self):
        law = "ОТО" if self.law == "GR" else "Ньютон"
        return f"Отрезок {self.seg} ({law}, {self.info['kind_text']})"

    # --- time ---------------------------------------------------------------------------------------------------
    def max_step(self):
        return 0.5 * self.track.dyn * self.T_s

    def advance(self, t_target):
        tg = t_target / self.T_s
        self.t = max(self.t, t_target)  # checks and messages carry the time they are revealed at
        out, evs = self.track.take(tg)
        if out is not None:
            self._trail("trail", out, rate=True)
            if self.info["kind"] == "circular":  # the largest departure from r0 seen so far (circle checks)
                r0 = self.init["r0"]
                self.S["maxdev"] = max(self.S["maxdev"], float(np.max(np.abs(out["r"] - r0))) / r0)
        for e in evs:
            self._on_event(e)
        self._reveal_ghost(tg, budget=GHOST_SLICE_S)
        self.t = t_target

    def _reveal_ghost(self, tg, budget=None):
        if self.ghost is not None:
            gout, gevs = self.ghost.take(tg, budget=budget)
            if not self.ghost.caught_up and "ghost_lag" not in self.S["notes"]:
                self.S["notes"].add("ghost_lag")
                self._msg({"type": "notice", "t": self.t, "text": "Призрак досчитывается от начала отрезка по частям, "
                           "пока мир идёт; до этого его след короче."})
            if gout is not None:
                self._trail("gtrail", gout, rate=False)
            for e in gevs:
                if e["kind"] in END_RU:
                    key = (e["kind"], round(e["t"], 6))
                    if key in self.S["ghost_ends"]:
                        continue  # the ghost was rebuilt after a toggle: its end is not reported twice (V4-14)
                    self.S["ghost_ends"].add(key)
                    law = "ОТО" if self.ghost.theory == "GR" else "Ньютон"
                    self._msg({"type": "event", "t": e["t"] * self.T_s, "kind": "ghost",
                               "text": f"Призрак ({law}): {END_RU[e['kind']]} на r = {e['r']:.6g}M"})
                elif e["kind"] == "peri":
                    self._msg({"type": "gapsis", "t": e["t"] * self.T_s, "seg": self.seg,
                               "x": e["x"], "y": e["y"], "r": e["r"]})

    def _trail(self, typ, out, rate):
        """Send revealed samples. A step that reveals more than ~3 turns (high speed) keeps the newest two turns at
        full resolution and every 4th sample (at most 1500) of the rest: drawing only, the record stays small."""
        n = len(out["t"])
        idx = np.arange(n)
        full = 480
        if n > 720:
            k = max(4, int(math.ceil((n - full) / 1500)))
            idx = np.concatenate([np.arange(0, n - full, k), np.arange(n - full, n)])
        blobs = {"t": out["t"][idx] * self.T_s, "x": out["x"][idx], "y": out["y"][idx], "r": out["r"][idx]}
        if rate:
            blobs["lag"] = out["lag"][idx]  # 1 - dtau/dt in double precision (Mercury: 6e-8)
        self._msg({"type": typ, "t": float(out["t"][-1]) * self.T_s, "seg": self.seg, "n": int(len(idx))}, blobs)

    def _on_event(self, e):
        k = e["kind"]
        te = e["t"] * self.T_s
        S = self.S
        if k in ("peri", "apo"):
            lst = S[k]
            lst.append(e)
            n = len(lst)
            adv = (lst[-1]["psi"] - lst[-2]["psi"] - 2 * math.pi) if n >= 2 else None
            shift = (lst[-1]["psi"] - lst[0]["psi"] - 2 * math.pi * (n - 1)) if n >= 2 else 0.0
            self._msg({"type": "apsis", "t": te, "seg": self.seg, "kind": k, "n": n, "x": e["x"], "y": e["y"],
                       "r": e["r"], "phi": e["phi"], "adv": adv, "shift": shift,
                       "dt": (lst[-1]["t"] - lst[-2]["t"]) * self.T_s if n >= 2 else None})
            if k == "peri" and (n <= 3 or n % 100 == 0):
                txt = f"Перицентр №{n}: r = {e['r']:.8g}M, φ = {math.degrees(e['phi']) % 360:.6g}°"
                if adv is not None:
                    txt += "; смещение за оборот " + _angle_text(adv)
                self._msg({"type": "event", "t": te, "kind": "periapsis", "text": txt})
            if k == "peri" and n >= 2 and _due(n):
                self._checks_advance()
            if k == "apo" and _due(n):
                self._checks_turning(e, "apo")
            if k == "peri" and _due(n):
                self._checks_turning(e, "peri")
            if self._mercury() and S["peri"] and S["apo"] and "merc" not in S["notes"]:
                S["notes"].add("merc")
                rp, ra = S["peri"][0]["r"], S["apo"][0]["r"]
                self._check("merc_a", "Большая полуось (r_п + r_а)/2 по событиям орбиты ↔ Меркурий",
                            0.5 * (rp + ra) * self.M_m / AU, MERCURY_A_AU, "а.е.", tol=1e-6,
                            note="измерено: первые перицентр и апоцентр этого запуска; эталон — NASA NSSDCA Mercury "
                                 "Fact Sheet (J2000); отличие O(M/r) ~ 3·10⁻⁸ — вклад ОТО в начальные данные")
                self._check("merc_e", "Эксцентриситет (r_а − r_п)/(r_а + r_п) по событиям орбиты ↔ Меркурий",
                            (ra - rp) / (ra + rp), MERCURY_ECC, "", tol=1e-6,
                            note="измерено: первые перицентр и апоцентр этого запуска; эталон — NASA NSSDCA (J2000)")
        elif k == "lap":
            S["laps"].append(e)
            if self.info["kind"] == "circular" and _due(len(S["laps"])):
                self._checks_circular()
        elif k in END_RU:
            v = math.hypot(e.get("v_r") or 0.0, e.get("v_phi") or 0.0)
            tau = e["tau"] * self.T_s  # the body's clock since its launch
            txt = f"{END_RU[k][:1].upper() + END_RU[k][1:]}: r = {e['r']:.8g}M, собственное время тела τ = {tau:.6g} с"
            if k == "horizon":
                txt += (" (удалённый наблюдатель видит, как тело лишь асимптотически приближается к r = 2M; "
                        "здесь расчёт остановлен при r − 2M = 2·10⁻⁶ M)")
            if k == "surface":
                txt += f", скорость удара {v:.6g} c (неподвижный наблюдатель у поверхности)"
            self._msg({"type": "event", "t": te, "kind": k, "text": txt})
            self._checks_end(e)
            self._check_outcome(k)

    # --- checks ---------------------------------------------------------------------------------------------------
    def _adv_unit(self, adv):
        return ("″", ARCSEC) if abs(adv) < math.radians(1.0) else ("°", math.pi / 180.0)

    def _apsis_tol(self, adv):
        """Relative tolerance of a measured advance: the integrator's phase floor (~1e-12 rad per orbit) and the
        location of apsides on a nearly circular orbit (APSIS_PHASE/spread)."""
        s = self.info.get("spread") or 1.0
        return max(1e-8, (2e-11 + APSIS_PHASE / s) / abs(adv)) if adv else None

    def _checks_advance(self):
        P = self.S["peri"]
        n = len(P)
        info = self.info
        mean = (P[-1]["psi"] - P[0]["psi"]) / (n - 1) - 2 * math.pi
        period = (P[-1]["t"] - P[0]["t"]) / (n - 1) * self.T_s
        orbits_n = n - 1
        spread = info.get("spread") or 1.0
        if self.law == "GR":
            ref = info["adv_exact"]
            if ref is None:
                return
            unit, sc = self._adv_unit(ref)
            tol = self._apsis_tol(ref)
            self._check("adv", "Смещение перицентра за оборот: измерено по орбите ↔ точный эллиптический интеграл",
                        mean / sc, ref / sc, unit, tol=tol,
                        note=f"угол между последовательными перицентрами (нули du/dφ на выходе интегратора) минус "
                             f"360°, среднее по {orbits_n} обор.; эталон — lfphys.core.gravity.orbits."
                             "periapsis_advance (4K(m)/√(2(u₃−u₁)) − 2π) от e² − 1 без потери точности")
            el = info["elements"]
            mp = 1.0 / el["p"]
            ecc = el["ecc"]
            c2 = (18.0 + ecc * ecc) / 4.0 * mp
            c3 = 5.0 / 12.0 * (54.0 + 9.0 * ecc * ecc) * mp * mp
            if mp <= 0.02:
                self._check("ppn", "То же ↔ 6πM/p·[1 + (18 + ε²)/4·M/p] (слабое поле: PPN и следующий порядок)",
                            mean / sc, info["adv_series2"] / sc, unit, tol=1.5 * c3 + tol,
                            note=f"M/p = {mp:.3g}; первый член 6πM/p = {info['adv_ppn'] / sc:.10g}{unit} — "
                                 "lfphys.theories.approx.ppn (γ = β = 1); поправка второго порядка "
                                 f"{c2:.3g} отн. и третий член (5/12)(54 + 9ε²)(M/p)² = {c3:.3g} — "
                                 "lfphys.core.gravity.orbits.advance_series, сверено с точным интегралом "
                                 "(lfphys/tests/test_relativity_gravity.py); допуск 1.5× третьего члена + численный")
            else:
                ratio = mean / info["adv_ppn"]
                self._check("ppn", f"6πM/p (PPN, первый порядок): здесь M/p = {mp:.3g} — вне области применимости",
                            info["adv_ppn"] / sc, None, unit,
                            note=f"измеренное смещение в {ratio:.4g} раза больше: разложение по M/p в сильном поле "
                                 "не работает (поправка следующего порядка ≈ " + f"{c2:.3g})")
            cent = mean * CENTURY_S / period / ARCSEC
            if mp > 0.02:
                pass  # per century only means something in a weak field
            elif self._mercury():
                self._check("century", "Смещение перигелия Меркурия за юлианское столетие (измерено)", cent,
                            MERCURY_GR_ARCSEC_PER_CENTURY, "″/век", tol=2e-4,
                            note="измерено: смещение за оборот × (36525 сут / радиальный период запуска); эталон "
                                 "42.98″/век — Will 2014, Living Rev. Relativ. 17, 4, ур. (65), γ = β = 1, без J2 "
                                 "Солнца (+0.03″); допуск — точность записи эталона (0.01″)")
            else:
                self._check("century", "Смещение перицентра за юлианское столетие (измерено)", cent, None, "″/век",
                            note="смещение за оборот × (36525 сут / радиальный период)")
            ref_t = info.get("period_t_ref")
            self._check("period", "Радиальный период (t), измерен ↔ квадратура 2∫e dr/((1 − 2M/r)√R)", period, ref_t,
                        "с", tol=1e-9 + 2.0 * APSIS_PHASE / spread,
                        note="время между перицентрами; эталон без дифференциальных уравнений — "
                             "lfphys.core.gravity.orbits.radial_period (гладкая χ-квадратура по точкам поворота)")
            if self.S["second"] is None:
                self._second_scheme_bound()
        else:
            ref_p = info["period_ref"]
            tol_a = 1e-9 + APSIS_PHASE_NEWTON / spread
            self._check("adv", "Смещение перицентра за оборот (Ньютон) ↔ 0: эллипс замкнут", mean / ARCSEC, 0.0,
                        "″", tol=tol_a / ARCSEC, ok=abs(mean) <= tol_a,
                        note=f"угол между перицентрами (нули r·v) минус 360°, среднее по {orbits_n} обор.; "
                             f"допуск {tol_a:.2g} рад (точность нахождения перицентров)")
            if ref_p:
                dE = self.track.drift["E"]
                self._check("period", "Период (время между перицентрами) ↔ закон Кеплера 2π√(a³/GM)", period, ref_p,
                            "с", tol=1e-8 + 2.0 * dE + 2.0 * APSIS_PHASE_NEWTON / spread,
                            note="a = −GM/(2E) из начальных данных; допуск 10⁻⁸ + 2× измеренного дрейфа энергии "
                                 f"({dE:.2g}: период интегрированной орбиты меняется на 1.5 δE/E)")
            self._checks_newton_conservation()

    def _checks_turning(self, e, which):
        info = self.info
        if self.law != "GR" or info["kind"] != "bound" or not info.get("elements"):
            return
        el = info["elements"]
        ref = el["r_peri"] if which == "peri" else el["r_apo"]
        lab = "Перицентр" if which == "peri" else "Апоцентр"
        # the reference is computed from e^2 - 1 itself (review V4-7), its roots at 30 digits; what remains is the
        # rounding of the cubic's coefficients, amplified where two turning points come together (near the ISCO)
        cond = (info.get("u_cond") or {}).get(which) or 1.0
        sens = (info.get("u_sens") or {}).get(which) or 0.0
        drift = abs(e["em1_state"] - info["em1"]) / abs(info["em1"])
        tol = 1e-11 + 4.0 * 2.2e-16 * cond + 2.0 * sens * drift
        self._check("r_" + which, f"{lab}: r в событии du/dφ = 0 по орбите ↔ корень f(u) (точка поворота)",
                    e["r"], ref, "M", tol=tol,
                    note="эталон — lfphys.core.gravity.orbits.elements от e² − 1 (без потери точности), корни кубики "
                         "с 30 знаками; допуск 10⁻¹¹ + 4ε·κ + 2·s·δ: κ = Σ|членов f|/(|f′(u)|·u) = "
                         f"{cond:.3g} (обусловленность корня), δ = {drift:.2g} — измеренный дрейф e² − 1 в этом "
                         f"событии (строка ниже), s = {sens:.3g} — насколько он сдвигает точку поворота")
        self._check("em1", "e² − 1 по состоянию тела в точке поворота ↔ начальное (дрейф интегрирования)",
                    e["em1_state"], info["em1"], "", tol=1e-9,
                    note="первый интеграл e² − 1 = l²(u'² + u² − 2u³) − 2u по (u, du/dφ) интегратора, u = M/r")

    def _second_scheme_bound(self):
        """The same initial data integrated by the independent scheme (geodesic equations in proper time)."""
        P = self.S["peri"]
        init = self.init
        tau_end = (P[1]["tau"] - self.seg_tau0) + 0.25 * (P[1]["tau"] - P[0]["tau"])
        g = orbit_stream.geodesic_tau(init["r0"], init["v_r"], init["v_phi"], tau_end,
                                      r_stop=self.R if self.R > 0 else 2.0)
        self.S["second"] = g
        main = P[1]["psi"] - P[0]["psi"] - 2 * math.pi
        ref = self.info["adv_exact"]
        if len(g["peri_phi"]) >= 2:
            sec = abs(g["peri_phi"][1] - g["peri_phi"][0]) - 2 * math.pi
            unit, sc = self._adv_unit(ref)
            self._check("adv2", "Смещение за первый оборот: вторая схема (уравнения геодезических в τ) ↔ основная",
                        sec / sc, main / sc, unit, tol=2.0 * self._apsis_tol(ref),
                        note="lfphys.core.gravity.orbit_stream.geodesic_tau: (t, r, φ) по символам Кристоффеля, "
                             "e, l и нормировка не навязаны")
        self._drift_checks(g)

    def _drift_checks(self, g):
        """Drifts of the second scheme. e and the norm are compared with the binding energy |e^2 - 1| (review V4-8:
        in a weak field |e - 1| ~ 1e-8, so a drift of e of 1e-9 relative to e would be 8 % of it); in these variables
        double precision resolves it only to ~eps/|e^2 - 1| per step (measured up to ~30 eps over an eccentric orbit
        from 1e8 M), hence the tolerance max(1e-9, 100 eps/|e^2 - 1|)."""
        floor = g["binding_floor"] or 0.0
        tol = max(1e-9, 100.0 * floor)
        eb, nb = g["e_drift_binding"], g["norm_drift_binding"]
        self._check("drift_e", "Вторая схема: дрейф e² относительно энергии связи |e² − 1|", eb, None, "",
                    tol=tol, ok=eb is not None and eb <= tol,
                    note=f"максимум |e² − e₀²|/|e₀² − 1| по орбите, |e² − 1| = {abs(g['em1']):.3g}; предел точности "
                         f"переменных ~{floor:.1g}; допуск {tol:.2g}")
        self._check("drift_l", "Вторая схема: дрейф l = r² dφ/dτ", g["l_drift"], None, "", tol=1e-9,
                    ok=g["l_drift"] <= 1e-9,
                    note="относительный, максимум по орбите; в основной схеме (Бине) l — параметр уравнения")
        self._check("drift_n", "Вторая схема: нормировка |u·u + 1| относительно |e² − 1|", nb, None, "", tol=tol,
                    ok=nb is not None and nb <= tol, note=f"максимум по орбите; допуск {tol:.2g}")

    def _checks_circular(self):
        """Circle checks. «Circular» is granted up to a relative spread s = (r_apo - r_peri)/r_peri of 1e-6; the mean
        rate and the lap time of such an orbit differ from the exact circle by O(s), so the tolerance is 1e-10 + 3 s
        (GR; Newton 1e-8 + 3 s). On an unstable circle (r0 < 6M) rounding grows: laps are checked only while the
        largest departure from r0 seen so far stays below 1.5 s + 2e-11 (the rate moves by ~2M/(r - 2M) of it)
        (review V4-5)."""
        L = self.S["laps"]
        n = len(L)
        e = L[-1]
        r0 = self.init["r0"]
        s = self.info.get("spread") or 0.0
        guard = 1.5 * s + 2e-11
        if self.S["maxdev"] > guard:
            if "left" not in self.S["notes"]:
                self.S["notes"].add("left")
                self._msg({"type": "notice", "t": self.t,
                           "text": f"Тело уходит с круговой орбиты (отклонение r до {self.S['maxdev']:.2g} r₀ после "
                                   f"{n} обор.; разброс точек поворота {s:.2g}): неустойчивость — проверки круга "
                                   "дальше не ведутся."})
            return
        dt = e["t"] * self.T_s - self.seg_t0
        dtau = (e["tau"] - self.seg_tau0) * self.T_s
        note_s = f"; орбита круговая с разбросом точек поворота s = {s:.2g}, допуск включает 3s"
        if self.law == "GR":
            tol = 1e-10 + 3.0 * s
            self._check("rate", "dτ/dt на круговой орбите: Δτ/Δt по орбите ↔ √(1 − 3M/r)", dtau / dt,
                        self.info["rate_circ"], "", tol=tol,
                        note=f"собственное время тела за {n} обор. к координатному; эталон — замкнутая формула"
                             + note_s)
            self._check("period", "Период обращения (t) ↔ 2π√(r³/GM) (точно для круговой геодезической)", dt / n,
                        self.info["period_ref"], "с", tol=tol, note="время одного оборота по φ, среднее" + note_s)
            if self.S["second"] is None:
                g = orbit_stream.geodesic_tau(r0, self.init["v_r"], self.init["v_phi"], dtau / self.T_s,
                                              r_stop=self.R if self.R > 0 else 2.0)
                self.S["second"] = g
                dr = float(np.max(np.abs(g["r"] - r0)) / r0)
                stable = r0 > self.special["isco"]
                lim = (1e-9 if stable else 1e-6) + 1.5 * s
                self._check("circ2", "Вторая схема: отклонение r от r₀ за оборот", dr, None, "", tol=lim, ok=dr < lim,
                            note="уравнения геодезических в τ из тех же начальных данных" + note_s)
                self._drift_checks(g)
        else:
            tol = 1e-8 + 3.0 * s
            self._check("period", "Период обращения ↔ 2π√(r³/GM) (Кеплер)", dt / n, 2 * math.pi * r0**1.5 * self.T_s,
                        "с", tol=tol, note="время одного оборота по φ, среднее" + note_s)
            self._checks_newton_conservation()

    def _checks_newton_conservation(self):
        """E and h along every integration sample. The integration keeps a relative tolerance 1e-12 of the local
        terms, so near a deep periapsis the error of E is ~1e-12 of the largest term v^2/2 + GM/r there, which can be
        10^6 |E|: the tolerance is 1e-9 of the largest term seen (review V4-4); the row shows it (V4-13)."""
        d = self.track.drift
        E0 = abs(self.track.E0)
        tol_E = 1e-9 * d["scale"] / E0
        self._check("energy", "Энергия E = v²/2 − GM/r: дрейф по орбите", d["E"], None, "", tol=tol_E,
                    ok=d["E"] <= tol_E,
                    note=f"относительно |E|, максимум по всем точкам интегрирования; допуск 10⁻⁹ наибольшего члена "
                         f"v²/2 + GM/r на орбите (в {d['scale'] / E0:.3g} раз больше |E|)")
        self._check("angmom", "Момент h = x·v_y − y·v_x: дрейф по орбите", d["h"], None, "", tol=1e-9,
                    ok=d["h"] <= 1e-9, note="относительный, максимум; допуск 10⁻⁹")

    def _checks_end(self, e):
        k = e["kind"]
        init = self.init
        tau = (e["tau"] - self.seg_tau0) * self.T_s
        if self.law != "GR":
            if k in ("center", "surface"):
                self._checks_newton_conservation()
            return
        if k in ("horizon", "surface"):
            if init["v"] == 0.0 and init["how"] == "launch":
                r0 = init["r0"]
                rs = e["r"]
                eta = math.acos(2.0 * rs / r0 - 1.0)
                ref = math.sqrt(r0**3 / 8.0) * (eta + math.sin(eta)) * self.T_s
                self._check("fall_tau", f"Собственное время падения с покоя до r = {rs:.10g}M ↔ циклоида", tau, ref,
                            "с", tol=1e-9, note="τ = √(r₀³/8M)(η + sin η), r = r₀(1 + cos η)/2 — точное решение "
                                                "радиального падения")
            else:
                ref = None
                nr = self.info.get("nearest_root")
                on_double = bool(self.info.get("double_root")) or (
                    bool(self.info.get("start_turning")) and nr is not None and nr < 1e-6)
                note = ("эталон без дифференциальных уравнений: R = e² − (1 − 2M/r)(1 + l²/r²), "
                        "lfphys.core.gravity.orbit_stream.plunge_proper_time")
                if on_double:
                    note = ("эталона нет: старт на (почти) двойном корне R(r) — на неустойчивой круговой орбите; "
                            "время до падения задаётся ростом ошибок округления, интеграл ∫dr/√R расходится")
                else:
                    try:
                        ref = orbit_stream.plunge_proper_time(self.track.em1, self.track.l, init["r0"], init["v_r"],
                                                              e["r"], self.info.get("r_apo")) * self.T_s
                    except ValueError:
                        pass
                self._check("fall_tau", f"Собственное время до r = {e['r']:.10g}M ↔ квадратура ∫dr/√R(r)", tau, ref,
                            "с", tol=1e-9, note=note)
            if k == "surface":
                v = math.hypot(e["v_r"], e["v_phi"])
                ref = orbit_stream.local_speed_from_e(self.R, self.track.e)
                self._check("impact", "Скорость удара (неподвижный наблюдатель у поверхности) ↔ √(1 − (1 − 2M/R)/e²)",
                            v, ref, "c", tol=1e-9, note="по состоянию интегратора в момент r = R")

    def _check_outcome(self, k):
        """The end the run observed against the kind predicted from the turning points at the start of the segment
        (review V4-12: a check that can fail). A circle at r0 < 6M (unstable) may end either way."""
        kind = self.info["kind"]
        r0 = self.init["r0"]
        fall = {"horizon", "surface", "center"}
        expect = {"plunge": fall, "radial_fall": fall, "escape": {"escape"}, "radial_escape": {"escape"}}.get(kind)
        unstable_circle = kind == "circular" and (self.law == "GR" and r0 < self.special["isco"])
        if unstable_circle:
            expect = fall | {"escape"}
        ok = expect is not None and k in expect
        pred = {"plunge": "падение", "radial_fall": "падение", "escape": "уход", "radial_escape": "уход",
                "bound": "связанная — конца нет", "circular": "круговая"}.get(kind, kind)
        note = "предсказание — по точкам поворота в начале отрезка (lfphys.core.gravity.orbit_stream)"
        if unstable_circle or (kind == "plunge" and self.law == "GR" and self.special["photon"] < r0 < self.special["isco"]):
            note += (f"; r₀ = {r0:.4g}M < ISCO = {self.special['isco']:g}M (lfphys.core.gravity.kerr.isco(0)): "
                     "вне ISCO такое же возмущение даёт связанную орбиту (тест v04)")
        self._check("outcome", f"Исход орбиты: предсказан «{pred}», наблюдён «{END_RU.get(k, k)}»", None, None, "",
                    ok=ok, note=note)

    def _mercury(self):
        """The Mercury reference applies only to its own initial data (preset values, unchanged)."""
        p = self.params
        return (self.law == "GR" and math.isclose(self.msun, 1.0, rel_tol=1e-12) and self.init["how"] == "launch"
                and math.isclose(self.init["r0"], MERCURY_R0, rel_tol=1e-9)
                and math.isclose(self.init["k"], MERCURY_K, rel_tol=1e-9) and self.init["alpha"] == 0.0
                and p["r0"] == self.init["r0"])

    # --- frames ---------------------------------------------------------------------------------------------------
    def frame(self):
        tg = self.t / self.T_s
        st = self.track.state(tg)
        d = {"seg": self.seg, "x": st["x"], "y": st["y"], "r": st["r"], "phi": st["phi"], "alive": st["alive"],
             "status": (self.track.end_event["kind"] if not st["alive"] else "orbit"),
             "tau": st["tau"] * self.T_s, "t_launch": self.t_launch, "rate": st["rate"], "deficit": st["lag"],
             "n_peri": len(self.S["peri"]), "n_lap": len(self.S["laps"])}
        vr, vp = st.get("v_r"), st.get("v_phi")
        if self.law == "GR":
            r = st["r"]
            v = math.hypot(vr, vp) if vr is not None else orbit_stream.local_speed_from_e(r, self.track.e)
            d.update(v=v, grav=math.sqrt(max(1.0 - 2.0 / r, 0.0)), kin=math.sqrt(max(1.0 - v * v, 0.0)))
        else:
            v = math.hypot(vr, vp) if vr is not None else None
            d.update(v=v, grav=1.0, kin=1.0)
        if self.ghost is not None:
            g = self.ghost.state(tg)
            d["ghost"] = {"x": g["x"], "y": g["y"], "r": g["r"], "alive": g["alive"], "tau": g["tau"] * self.T_s,
                          "rate": g["rate"]}
        # (the frame key "lag" is the runner's flag "the computation cannot keep up"; 1 - dtau/dt is "deficit")
        else:
            d["ghost"] = None
        return d, {}

    def next_event_time(self):
        kinds = {"peri", "apo", "horizon", "surface", "center", "escape"}
        if self.info["kind"] == "circular":
            kinds.add("lap")
        te = self.track.next_event_after(self.t / self.T_s, kinds)
        return None if te is None else te * self.T_s

    def header(self):
        law = "ОТО" if self.law == "GR" else "Ньютон"
        body = "чёрная дыра" if self.R == 0 and self.law == "GR" else (
            "точечная масса" if self.R == 0 else f"тело радиусом {self.params['radius_km']:.6g} км")
        return {
            "title": f"Орбиты и часы: {law}, {self.msun:.6g} M☉, {body}",
            "text": ("Пробное тело в экваториальной плоскости центрального тела. Орбита считается в этом запуске из "
                     "начальных данных: в ОТО — точная геодезическая Шварцшильда (уравнение орбиты вместе с "
                     "координатным временем t и собственным временем τ тела), в мире Ньютона — ньютонова орбита. "
                     "Запуск показывает орбиту по мере того, как время мира t (часы далёкого неподвижного "
                     "наблюдателя) доходит до неё; перицентры, их смещение, часы тела — измерения запуска. "
                     "Замкнутые формулы ОТО — только эталоны в «Проверках». Изменение r₀, скорости или угла "
                     "запускает тело заново в текущий момент; «Толчок» меняет скорость на ходу."),
            "modifications": SCHEMA.modifications(self.params),
            "law": self.law,
            "units": {"M_m": self.M_m, "T_s": self.T_s, "au_m": AU, "gm": self.gm},
            "body": {"mass_msun": self.msun, "R": self.R, "R_km": self.params["radius_km"]},
            "special": self.special,
            "actions": self._actions(),
        }, {}


VIZ = {
    "id": "v04_orbits",
    "title": "Орбиты и часы: ОТО и Ньютон",
    "summary": ("Тело на орбите вокруг звезды или чёрной дыры: прецессия перицентра (Меркурий 43″/век, нейтронная "
                "звезда, ISCO), падение за горизонт, собственное время тела против времени далёкого наблюдателя; "
                "сравнение с ньютоновой орбитой из тех же начальных данных."),
    "purpose": ("Увидеть, как из уравнений движения ОТО получаются прецессия, неустойчивость орбит у ISCO и замедление "
                "часов, и чем от этого отличается Ньютон; законы можно намеренно заменить ньютоновыми."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
