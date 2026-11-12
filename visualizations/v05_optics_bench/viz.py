# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v05: the optical bench - single photons at a boundary between media, at coatings and at a thin metal film.

What the run computes (README.md of this folder has the model in full), all with the engine lfphys:
* the structure's amplitudes r, t and powers R, T, A = 1 - R - T by the transfer matrices
  (lfphys.core.optics.interfaces.stack) for the source's wavelength, angle and polarization, and the curves R(theta),
  T(theta) at the current wavelength and R(lambda), T(lambda) at the current angle;
* the field |E|^2 of s-polarized light through the structure (interfaces.field_profile);
* the stream of single photons: every photon's fate (reflected, transmitted, absorbed) drawn by the Born rule with
  the computed R, T, A when it reaches the structure, revealed when it reaches a detector (or, if absorbed, the
  structure); the counts are the accumulation of these events;
* checks against closed forms (lfphys.core.optics.thin_films): Brewster, critical angle and R = 1 beyond it, the
  evanescent decay length, the quarter-wave antireflection layer, the Bragg mirror, the Airy formula of a film, the
  Airy summation of any single layer, frustrated total reflection, Joule heating, and the photon statistics.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core.optics import interfaces, thin_films

from .engine.bench import (ARM_M, P_5SIGMA, POL_LABEL, STRUCT_LABEL, STRUCTS, TH_MAX, Stream, Structure,
                           born_probs, brewster_from_rp, build_structure, critical_from_T, curves, field, field_grid,
                           flight_times, outcome_test, ray_angles, rta)

U = 2.0 ** -53  # unit round-off of binary64 (the derived tolerances of the evan and film checks)


def _p(*a, **k):
    k.setdefault("live", True)  # the whole bench is set-up an experimenter changes while the world runs
    return Param(*a, **k)


SHOW = lambda *kinds: {"structure": list(kinds)}  # noqa: E731

SCHEMA = Schema([
    # source
    _p("lam_nm", "Длина волны λ, нм", "float", 633.0, group="Источник", min=300.0, max=1600.0),
    _p("theta_deg", "Угол падения θ, °", "float", 45.0, group="Источник", min=0.0, max=TH_MAX,
       help="Угол между лучом и нормалью к поверхности. Источник и оба детектора стоят на поворотном столе: при "
            "повороте фотоны, уже летящие по старым путям, теряются (счёт «потеряно»)."),
    _p("pol", "Поляризация", "select", "unpol", group="Источник",
       options=[("s", POL_LABEL["s"] + ": E ⊥ плоскости падения"), ("p", POL_LABEL["p"] + ": E в плоскости падения"),
                ("unpol", POL_LABEL["unpol"])]),
    _p("rate", "Фотонов в секунду (время мира)", "float", 4e9, group="Источник", min=1.0, max=1e15, log=True,
       help="Пуассоновский поток одиночных фотонов. Полёт по плечу 30 см занимает около 1 нс."),
    # media
    _p("n0", "Среда падения n₀", "float", 1.0, group="Среды", min=1.0, max=4.0,
       help="Показатель преломления среды, из которой приходит свет (действительный, без дисперсии)."),
    _p("ns", "Среда выхода (подложка) n_s", "float", 1.5, group="Среды", min=1.0, max=4.0,
       help="Среда за структурой. В режиме «полное внутреннее отражение» — более редкая среда за гранью призмы "
            "(и среда зазора, если за ним стоит вторая призма)."),
    # structure
    _p("structure", "Структура", "select", "interface", group="Структура", options=STRUCTS,
       help="Все структуры считаются одной и той же функцией движка: матрицы переноса (lfphys interfaces.stack)."),
    _p("lam0_nm", "Расчётная длина волны λ₀, нм", "float", 550.0, group="Структура", min=300.0, max=1600.0,
       show_if=SHOW("ar", "bragg"), help="Толщины слоёв — λ₀/(4n) каждый."),
    _p("ar_n", "Показатель плёнки n_f", "float", 1.38, group="Структура", min=1.0, max=4.0, show_if=SHOW("ar"),
       help="1.38 — как MgF₂ (иллюстративно); R(λ₀) = 0 при n_f = √(n₀ n_s)."),
    _p("nH", "Высокий показатель n_H", "float", 2.3, group="Структура", min=1.0, max=4.0, show_if=SHOW("bragg")),
    _p("nL", "Низкий показатель n_L", "float", 1.45, group="Структура", min=1.0, max=4.0, show_if=SHOW("bragg")),
    _p("pairs", "Число пар N (слои H, L)", "int", 8, group="Структура", min=1, max=30, show_if=SHOW("bragg")),
    _p("fp_n", "Показатель плёнки", "float", 2.3, group="Структура", min=1.0, max=4.0, show_if=SHOW("fp")),
    _p("fp_d_nm", "Толщина плёнки, нм", "float", 2000.0, group="Структура", min=1.0, max=20000.0, log=True,
       show_if=SHOW("fp")),
    _p("metal_n", "Металл: n (действительная часть показателя)", "float", 0.2, group="Структура", min=0.01, max=5.0,
       show_if=SHOW("metal")),
    _p("metal_k", "Металл: κ (мнимая часть, экстинкция)", "float", 3.3, group="Структура", min=0.0, max=20.0,
       show_if=SHOW("metal")),
    _p("metal_d_nm", "Толщина металла, нм", "float", 30.0, group="Структура", min=0.1, max=500.0, log=True,
       show_if=SHOW("metal")),
    _p("tir_gap_nm", "Зазор до второй призмы, нм (0 — призмы нет)", "float", 0.0, group="Структура", min=0.0,
       max=5000.0, show_if=SHOW("tir"),
       help="Вторая призма из того же стекла n₀ за зазором из среды n_s: нарушенное полное отражение — свет "
            "туннелирует через зазор."),
], presets={
    "brewster": {"label": "Стекло n = 1.5 в воздухе под углом Брюстера (неполяризованный свет: отражаются только s)",
                 "params": {"structure": "interface", "n0": 1.0, "ns": 1.5, "theta_deg": 56.31, "pol": "unpol",
                            "lam_nm": 633.0}},
    "tir": {"label": "Полное внутреннее отражение: стекло 1.5 → воздух, θ = 60° за критическим углом",
            "params": {"structure": "tir", "n0": 1.5, "ns": 1.0, "theta_deg": 60.0, "pol": "unpol", "tir_gap_nm": 0.0,
                       "lam_nm": 633.0}},
    "ftir": {"label": "Нарушенное полное отражение: зазор 200 нм до второй призмы (туннелирование фотонов)",
             "params": {"structure": "tir", "n0": 1.5, "ns": 1.0, "theta_deg": 45.0, "pol": "s", "tir_gap_nm": 200.0,
                        "lam_nm": 633.0}},
    "ar_mgf2": {"label": "Просветление стекла слоем λ/4 с n_f = 1.38 (как MgF₂, иллюстративно), λ₀ = 550 нм",
                "params": {"structure": "ar", "n0": 1.0, "ns": 1.5, "ar_n": 1.38, "lam0_nm": 550.0, "lam_nm": 550.0,
                           "theta_deg": 0.0, "pol": "s"}},
    "ar_ideal": {"label": "Просветление идеальным слоем λ/4: n_f = √1.5 ≈ 1.2247, R(λ₀) = 0",
                 "params": {"structure": "ar", "n0": 1.0, "ns": 1.5, "ar_n": math.sqrt(1.5), "lam0_nm": 550.0,
                            "lam_nm": 550.0, "theta_deg": 0.0, "pol": "s"}},
    "bragg": {"label": "Брэгговское зеркало (H L)×8: n_H = 2.3, n_L = 1.45 (как TiO₂/SiO₂, иллюстративно) на стекле 1.52",
              "params": {"structure": "bragg", "n0": 1.0, "ns": 1.52, "nH": 2.3, "nL": 1.45, "pairs": 8,
                         "lam0_nm": 550.0, "lam_nm": 550.0, "theta_deg": 0.0, "pol": "s"}},
    "fp": {"label": "Фабри–Перо: плёнка n = 2.3 толщиной 2 мкм в воздухе (иллюстративно)",
           "params": {"structure": "fp", "n0": 1.0, "ns": 1.0, "fp_n": 2.3, "fp_d_nm": 2000.0, "lam_nm": 633.0,
                      "theta_deg": 0.0, "pol": "s"}},
    "metal": {"label": "Металлическая плёнка 30 нм, n = 0.2 + 3.3i (как золото у 633 нм, иллюстративно) на стекле",
              "params": {"structure": "metal", "n0": 1.0, "ns": 1.5, "metal_n": 0.2, "metal_k": 3.3,
                         "metal_d_nm": 30.0, "lam_nm": 633.0, "theta_deg": 0.0, "pol": "unpol"}},
    "spr": {"label": "Плазмонный резонанс по Кречману: призма 1.5, металл 50 нм (n = 0.2 + 3.3i), воздух, p (иллюстративно)",
            "params": {"structure": "metal", "n0": 1.5, "ns": 1.0, "metal_n": 0.2, "metal_k": 3.3,
                       "metal_d_nm": 50.0, "lam_nm": 633.0, "theta_deg": 44.58, "pol": "p"}},
})

# what a live change touches (owner, 2026-10-23: the set-up changes at once, as in a laboratory)
PATH_FIELDS = ("n0", "ns", "theta_deg")  # the beam paths (media, goniometer): photons under way are lost
SOURCE_FIELDS = ("lam_nm", "pol", "rate")  # new photons only; those under way fly on and are transitional
STAT_STEPS = (1, 2, 5)
# joule: the Gauss-Legendre remainder is < 1e-25 (thin_films._layer_nodes); what is left is the float rounding of
# |E|^2 and of R + T, <= 1.5e-14 over 3000 random absorbing films in the ranges of this bench
JOULE_TOL = 1e-12
OUT_NAMES = ("R", "T", "A")


class Simulation(BaseSimulation):
    speed_range = (1e-15, 1e3)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._buf = []
        self.seg = -1
        self.st = build_structure(self.params)
        self.flight = Stream()
        self.pid = 0
        self.t_next = float(self.rng.exponential(1.0 / self.params["rate"]))
        self.tot = dict(emitted=0, R=0, T=0, A=0, lost=0, transitional=0)
        self.segc: dict[int, dict] = {}
        self.cache: dict = {}
        self.times = flight_times(self.st)
        self.default_speed = self.times["t_in"] / 1.2  # one arm in about 1.2 s of wall time
        try:
            self._new_segment("начало")
        except ValueError:
            raise
        except Exception as e:  # reported as a refused world (the runner catches ValueError), never a crash
            raise ValueError(f"мир не создан: {type(e).__name__}: {e}") from e

    def engine_modules(self):
        return ["core.optics.interfaces", "core.optics.thin_films", "core.constants", "theories.approx.ray_optics"]

    # --- messages -------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def _check(self, cid, label, value, ref, unit="", group="", note="", tol=1e-9, ok=None, info=False):
        """``info``: a comparison shown for information, never a pass or a failure (RULES.md §3, check message)."""
        rel = None
        if ref is not None and value is not None and ref != 0 and math.isfinite(value):
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if info:
            d["info"] = True
        elif ok is not None:
            d["ok"] = bool(ok)
        self._msg(d)

    # --- atomic changes -------------------------------------------------------------------------------------
    def _atomic(self, fn, *args):
        """Apply a change of the world as one transaction (review 2026-10-23, V5-1): the messages it produces are
        held back until it has succeeded as a whole; if anything raises, the world's state (parameters, structure,
        photons in flight, counters, segments, the random generator) is restored and nothing is emitted. Any
        exception becomes a ValueError, which the runner reports as a refused change, followed by the live values
        in force (the player rolls its control back)."""
        snap = {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in self.__dict__.items()}
        flight, flight_cols = self.flight, dict(self.flight.a)  # Stream.add/keep replace its columns, never edit them
        rng_state = self.rng.bit_generator.state
        outer = self._buf
        self._buf = []
        try:
            out = fn(*args)
        except Exception as e:
            self.__dict__.clear()
            self.__dict__.update(snap)
            flight.a = flight_cols
            self.rng.bit_generator.state = rng_state
            self._buf = outer
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"{type(e).__name__}: {e} (мир оставлен прежним)") from e
        buf, self._buf = self._buf, outer
        for meta, blobs in buf:
            self._msg(meta, blobs)
        return out

    # --- live changes (command "set") ---------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        return self._atomic(self._set_live, values)

    def _set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise ValueError("; ".join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return "без изменений"
        st = build_structure(new)  # raises on a bad set-up; nothing of the world is touched before this point
        desc = "; ".join(f"{SCHEMA.by_id[k].label}: {_fmt(SCHEMA.by_id[k], self.params[k])} → "
                         f"{_fmt(SCHEMA.by_id[k], new[k])}" for k in changed)
        notes = []
        path = any(k in PATH_FIELDS for k in changed) or st.n_out != self.st.n_out
        if path and len(self.flight):
            lost = len(self.flight)
            self.tot["lost"] += lost
            self.flight = Stream()
            notes.append(f"пути пучков перестроены (среды или угол): фотонов в полёте потеряно {lost}")
        elif len(self.flight) and not any(k in SOURCE_FIELDS for k in changed):
            n0 = int(np.sum(self.flight.a["stage"] == 0))
            if n0:
                notes.append(f"{n0} фотон(ов), ещё не долетевших до структуры, встретят уже новую структуру "
                             "(переходные: в счёт нового отрезка не входят)")
        self.params = new
        self.st = st
        if "rate" in changed:
            self.t_next = self.t + float(self.rng.exponential(1.0 / new["rate"]))
        self._new_segment("изменена установка: " + desc)
        for text in notes:
            self._msg({"type": "notice", "t": self.t, "text": text})
        return desc

    def action(self, name, args):
        return self._atomic(self._action, name, args)

    def _action(self, name, args):
        if name == "clear":
            self._new_segment("новый отрезок: счётчики обнулены")
            return "новый отрезок: счётчики обнулены, установка прежняя"
        if name == "emit_one":
            self._emit_photons(np.array([self.t]))
            return "источник выпустил один фотон"
        raise ValueError(f"неизвестное действие {name!r}")

    def _actions(self):
        return [{"name": "emit_one", "label": "Выпустить один фотон", "args": [],
                 "help": "Один фотон сейчас, сверх пуассоновского потока"},
                {"name": "clear", "label": "Обнулить счётчики (новый отрезок)", "args": [],
                 "help": "Установка та же; статистика начинается заново"}]

    # --- one segment: the run's own numbers for the current set-up ------------------------------------------
    def _title(self):
        return "Оптический стол: " + STRUCT_LABEL[self.st.kind]

    def _new_segment(self, reason):
        if self.seg >= 0:
            self._stat_check(self.seg)
        self.seg += 1
        s = self.seg
        self.cache = {}
        p, st = self.params, self.st
        lam, th, pm = float(p["lam_nm"]), math.radians(p["theta_deg"]), p["pol"]
        self.times = flight_times(st)
        cur = {pol: rta(st, lam, th, pol) for pol in ("s", "p")}
        probs = {pol: born_probs(cur[pol]) for pol in ("s", "p")}
        if pm == "unpol":
            pexp = tuple(0.5 * (a + b) for a, b in zip(probs["s"], probs["p"]))
        else:
            pexp = probs[pm]
        self.segc[s] = {"n": 0, "R": 0, "T": 0, "A": 0, "pR": pexp[0], "pT": pexp[1], "pA": pexp[2]}
        self._stat_next = 20
        # angles found by the run from its own transfer matrices. The exit wave becomes evanescent where T of the bare
        # boundary n_in -> n_out vanishes: n sin(theta) is the same in every layer, so the layers do not move this
        # angle, while T of a thick structure can underflow to exactly 0 long before it (an evanescent thick film)
        th_c = critical_from_T(Structure("interface", st.n_in, st.n_out), lam)
        face = Structure("interface", st.n_in, float(p["ns"]))
        th_c_face = critical_from_T(face, lam) if st.kind == "tir" and st.layers else th_c
        single = not st.layers
        th_B = brewster_from_rp(st.n_in, st.n_out, lam, th_c) if single else None
        deg = lambda x: None if x is None else math.degrees(x)  # noqa: E731
        extra_lam = [lam] + ([float(p["lam0_nm"])] if st.kind in ("ar", "bragg") else [])
        cv, m_spec = curves(st, lam, th, pm, [deg(th_c), deg(th_c_face), deg(th_B), p["theta_deg"]], extra_lam)
        min_rp = None
        if not single:  # the minimum of R_p of the run (a multilayer has no Brewster closed form): grid, then Brent
            i = int(np.argmin(cv["Rp"]))
            if 0 < i < len(cv["th"]) - 1:
                min_rp = {"deg": float(cv["th"][i]), "Rp": float(cv["Rp"][i])}
                min_rp.update(_refine_min_rp(st, lam, float(cv["th"][i - 1]), float(cv["th"][i + 1]), min_rp))
        z = field_grid(st, lam)
        E2 = field(st, lam, th, z)
        angles = ray_angles(st, th)
        mix = {k: 0.5 * (cur["s"][k] + cur["p"][k]) for k in ("R", "T", "A")}
        curd = {"s": {k: cur["s"][k] for k in ("R", "T", "A")}, "p": {k: cur["p"][k] for k in ("R", "T", "A")},
                "mix": mix if pm == "unpol" else {k: cur[pm][k] for k in ("R", "T", "A")}}
        setup = {"title": self._title(), "kind": st.kind, "label": STRUCT_LABEL[st.kind], "n_in": st.n_in,
                 "n_out": st.n_out, "n_s": float(p["ns"]), "out_name": st.out_name, "layers": st.describe(),
                 "thickness": st.thickness, "lam": lam, "lam0": float(p["lam0_nm"]) if st.kind in ("ar", "bragg") else None,
                 "theta": float(p["theta_deg"]), "pol": pm, "pol_label": POL_LABEL[pm], "rate": float(p["rate"]),
                 "lossless": st.lossless, **self.times}
        approx = self._approximations(m_spec)
        blobs = {k: np.asarray(v, np.float64) for k, v in cv.items()}
        blobs["z"] = np.asarray(z, np.float64)
        blobs["E2"] = np.asarray(E2, np.float64)
        self._msg({"type": "segment", "t": self.t, "seg": s, "reason": reason, "setup": setup, "angles": angles,
                   "cur": curd, "expected": dict(zip(OUT_NAMES, pexp)),
                   "theta_B": None if th_B is None else {"deg": deg(th_B), "Rp": rta(face, lam, th_B, "p")["R"]},
                   "min_rp": min_rp, "theta_c": deg(th_c), "theta_c_face": deg(th_c_face), "approx": approx},
                  blobs)
        self._segment_checks(s, cur, cv, th_B, th_c, th_c_face, face)
        if s > 0:
            self._msg({"type": "actions", "t": self.t, "actions": self._actions()})

    def _approximations(self, m_spec):
        st, pm = self.st, self.params["pol"]
        out = ["Плоские волны и бесконечные плоские границы; среды однородные, изотропные, линейные и без дисперсии: "
               "показатели заданы числами (комплексными для поглощения), одинаковыми для всех λ. Значения «как MgF₂, "
               "TiO₂, золото» иллюстративны, это не табличные данные.",
               "Фотоны по одному: судьба каждого (отражён, прошёл, поглощён) разыгрывается по правилу Борна с "
               "вероятностями R, T, A, рассчитанными в этом запуске для его длины волны, угла и поляризации.",
               "Полёт по плечам (30 см) — со скоростью c/n (без дисперсии фазовая и групповая скорости равны); время "
               "внутри структуры (микроны) не учитывается.",
               "Лучи на схеме — геометрическая оптика (закон Снелла), приближённо; в поглощающем слое — по "
               "действительной части показателя. Структура нарисована в масштабе, плечи — нет.",
               "Профиль |E|² — для s-поляризации (функция движка field_profile считает только s)."
               + ("" if pm == "s" else " Сейчас источник " + ("p" if pm == "p" else "неполяризован")
                  + ": показан профиль s-компоненты.")]
        if pm == "unpol":
            out.append("Неполяризованный источник — смесь 50/50 s- и p-фотонов: изотропная плоская структура их не "
                       "смешивает, поэтому это то же, что матрица плотности ρ = I/2.")
        if m_spec >= 1600:
            out.append("Спектр стопки очень частый: 1600 точек могут не разрешить все полосы на коротких волнах.")
        out.extend(st.notes)
        return out

    def _segment_checks(self, s, cur, cv, th_B, th_c, th_c_face, face):
        p, st = self.params, self.st
        lam, th, pm = float(p["lam_nm"]), math.radians(p["theta_deg"]), p["pol"]
        G = f"Отрезок {s}: {STRUCT_LABEL[st.kind]}"
        CONS = f"Отрезок {s}: согласованность (тождества)"

        def mixed(fs, fp_):  # value for the source's polarization from per-polarization values
            return fs if pm == "s" else fp_ if pm == "p" else 0.5 * (fs + fp_)

        Rc, Tc, Ac = (mixed(cur["s"][k], cur["p"][k]) for k in ("R", "T", "A"))
        tot = Rc + Tc + Ac
        self._check(f"sum{s}", "R + T + A = 1 (A = 1 − R − T по определению)", tot, 1.0, "", CONS, tol=1e-12,
                    ok=abs(tot - 1.0) <= 1e-12,
                    note=f"R = {Rc:.10g}, T = {Tc:.10g}, A = {Ac:.3g}; тождество: поглощение в движке — остаток")
        # energy: lossless structures conserve R + T; absorbing ones are passive, and their A is Joule heating
        if st.lossless:
            dev = max(float(np.max(np.abs(1.0 - cv[pre + "R" + q] - cv[pre + "T" + q])))
                      for pre in ("", "l") for q in ("s", "p"))
            self._check(f"energy{s}", "Без потерь: max |1 − R − T| по всем рассчитанным углам и длинам волн (s и p)",
                        dev, 0.0, "", G, ok=dev < 1e-10,
                        note="R и T движок считает по отдельности из r и t; их сумма = 1 — закон сохранения энергии")
        else:
            amin = min(float(np.min(cv[pre + "A" + q])) for pre in ("", "l") for q in ("s", "p"))
            self._check(f"passive{s}", "Пассивная среда: наименьшее A по всем рассчитанным точкам", amin, None, "", G,
                        ok=amin >= -1e-12, note="поглощение не может быть отрицательным (κ ≥ 0)")
            jl = thin_films.joule_absorption_s(st.ns, st.ds, lam, th)
            AJ = jl["A"]
            val = cur["s"]["R"] + cur["s"]["T"] + AJ
            self._check(f"joule{s}", "R + T + A = 1 для s, где A — джоулево тепло k₀ Im(n²)∫|E|²dz / (n₀ cos θ)",
                        val, 1.0, "", G, tol=JOULE_TOL, ok=abs(val - 1.0) <= JOULE_TOL,
                        note=f"A по полю |E|² запуска = {AJ:.10g}; 1 − R − T из r, t = {cur['s']['A']:.10g} "
                             f"(теорема Пойнтинга: независимый путь); квадратура Гаусса–Лежандра, {jl['nodes']} узлов, "
                             "шаг по толщине скин-слоя и периоду стоячей волны")
        # Brewster: a single boundary
        if th_B is not None:
            ref = interfaces.brewster(st.n_in, st.n_out)
            self._check(f"brew{s}", "Угол Брюстера: ноль r_p, найденный запуском", math.degrees(th_B),
                        math.degrees(ref), "°", G, tol=1e-9, note=f"эталон arctg(n_выход/n₀) = arctg({st.n_out:g}/{st.n_in:g})")
            RpB = rta(face, lam, th_B, "p")["R"]
            self._check(f"brewR{s}", "R_p при найденном угле Брюстера", RpB, 0.0, "", G, ok=RpB < 1e-24,
                        note="p-фотоны там не отражаются: из неполяризованного пучка отражаются только s")
        # critical angle and total reflection
        if th_c_face is not None:
            ref = interfaces.critical(st.n_in, float(p["ns"]))
            lab = ("Критический угол грани: граница, за которой T запуска для грани без второй призмы = 0"
                   if st.kind == "tir" and st.layers else
                   "Критический угол: граница, за которой T запуска для голой границы n₀ → n_s = 0 (волна в среде "
                   "выхода затухает)")
            self._check(f"crit{s}", lab, math.degrees(th_c_face), None if ref is None else math.degrees(ref), "°", G,
                        tol=1e-9, note=f"эталон arcsin(n_s/n₀) = arcsin({float(p['ns']):g}/{st.n_in:g})")
        if th_c is not None and st.lossless:
            beyond = list(np.linspace(math.degrees(th_c) + 1e-6, TH_MAX, 60))
            dev = max(abs(1.0 - rta(st, lam, math.radians(x), q)["R"]) for x in beyond for q in ("s", "p"))
            self._check(f"tir{s}", "За критическим углом R = 1: max |1 − R| (s и p, 60 углов от θ_c до 89.9°)", dev, 0.0,
                        "", G, ok=dev < 1e-12, note="без потерь: всё, что не прошло, отражено")
            if th >= th_c:  # th_c is the first float angle at which the run's T = 0
                self._check(f"tirnow{s}", "R при текущем угле (он за критическим)", Rc, 1.0, "", G, tol=1e-12,
                            ok=abs(Rc - 1.0) <= 1e-12)
                if not st.layers:
                    self._evan_check(s, G, lam, th)
        # quarter-wave antireflection
        if st.kind == "ar":
            nf, lam0 = float(p["ar_n"]), float(p["lam0_nm"])
            R0 = rta(st, lam0, 0.0, "s")["R"]
            ref = thin_films.quarter_wave_R(st.n_in, nf, st.n_out)
            ideal = math.sqrt(st.n_in * st.n_out)
            self._check(f"ar{s}", "Просветление λ/4: R(λ₀, 0°) запуска", R0, ref, "", G, ok=abs(R0 - ref) <= 1e-12,
                        tol=1e-12, note=f"эталон ((n₀n_s − n_f²)/(n₀n_s + n_f²))²; = 0 при n_f = √(n₀ n_s) = {ideal:.8g} "
                                        f"(здесь n_f = {nf:.8g}); голая граница: {rta(face, lam0, 0.0, 's')['R']:.6g}")
        # Bragg mirror
        if st.kind == "bragg":
            nH, nL, N, lam0 = float(p["nH"]), float(p["nL"]), int(p["pairs"]), float(p["lam0_nm"])
            R0 = rta(st, lam0, 0.0, "s")["R"]
            ref = thin_films.quarter_wave_stack_R(st.n_in, nH, nL, st.n_out, N)
            self._check(f"bragg{s}", "Брэгговское зеркало: R(λ₀, 0°) запуска", R0, ref, "", G, tol=1e-10,
                        note="эталон для порядка «среда, H, L, …, H, L, подложка»: "
                             "R = ((n₀n_L^{2N} − n_s n_H^{2N})/(n₀n_L^{2N} + n_s n_H^{2N}))²; "
                             f"N = {N}, 1 − R = {1 - R0:.4g}")
        # any single layer: the Airy sum of multiple reflections with complex Fresnel coefficients
        if len(st.layers) == 1:
            self._film_check(s, G, cur, lam, th)
        # Fabry-Perot film: the Airy intensity formula
        if st.kind == "fp":
            self._airy_checks(s, G, cv, lam, th, Tc)
        # frustrated total internal reflection
        if st.kind == "tir" and st.layers and th_c_face is not None and th > th_c_face:
            gap = st.layers[0][1]
            ref = mixed(*(thin_films.ftir_T(st.n_in, float(p["ns"]), gap, lam, th, q) for q in ("s", "p")))
            self._check(f"ftir{s}", "Нарушенное полное отражение: T запуска (туннелирование через зазор)", Tc, ref, "", G,
                        tol=1e-9, note="эталон 1/(1 + ((a² + b²)/(2ab))² sh²(κd)): s — a = k_z, b = κ; p — a = k_z/n₀², "
                                       "b = κ/n_s²")

    def _stat_check(self, s):
        """All three outcomes against the Born probabilities of the segment (review 2026-10-23, V5-4: the reflected
        fraction alone let a swap of T and A pass): exact binomial tail of each outcome, Bonferroni over the
        outcomes, failure below the two-sided 5-sigma tail (bench.outcome_test)."""
        c = self.segc.get(s)
        if not c or c["n"] == 0:
            return
        n = c["n"]
        k = [c[x] for x in OUT_NAMES]
        pr = [c["p" + x] for x in OUT_NAMES]
        t = outcome_test(k, pr)
        parts = [f"{x}: {kx} (ожидание {px * n:.1f}, z = {zx:+.2f})" if math.isfinite(zx)
                 else f"{x}: {kx} (ожидание {px * n:.3g}: невозможный исход)"
                 for x, kx, px, zx in zip(OUT_NAMES, k, pr, t["z"])]
        self._check(f"stat{s}", "Исходы R, T, A (счёт событий запуска) против вероятностей Борна: p-значение",
                    t["p"], None, "", f"Отрезок {s}: статистика фотонов", ok=t["p"] >= P_5SIGMA,
                    note=f"n = {n}; " + "; ".join(parts) + f". Точный биномиальный хвост каждого исхода, поправка "
                         f"Бонферрони ({t['m']} исх.); провал при p < {P_5SIGMA:.2g} (как 5σ); χ² Пирсона = "
                         f"{t['chi2']:.3g} при {t['dof']} ст. св. (для сведения)")

    # --- checks near the critical and grazing angles (review 2026-10-23, V5-2) --------------------------------
    def _evan_check(self, s, G, lam, th):
        """The decay length of the evanescent wave from the run's field against lambda / (2 pi sqrt(q)),
        q = n0^2 sin^2 theta - n_s^2 (thin_films, exact to one rounding).

        The run's number: |E|^2 at the face and at a depth z; first z = lambda/4, then z = the length so found, so that
        ln(I(0)/I(z)) ~ 2 (the logarithm of a ratio near 1 would lose digits). Its error to first order in u = 2^-53
        (README, "evan"): the engine's cos theta_t = sqrt(1 - x^2), x = n0 sin theta / n_s, carries 9u in x^2, i.e.
        9u K in 1 - x^2 (the subtraction itself is exact near x = 1), K = n0^2 sin^2 theta / q; the root halves it,
        and 2 pi, n_s, the product and lambda add <= 5u: the decay constant to (4.5 K + 5) u. Each |E|^2 value carries
        <= (11 + ln) u and their ratio and logarithm add 1u each: ln to (15 + ln) u absolutely; the division by ln
        and the reference add 3u. Tolerance (4.5 K + 9 + 15/ln) u. Where it exceeds 1e-2 the first-order bound no
        longer holds: the angle is within rounding of theta_c and fixes the decay length only to ~K u; the line is
        then shown for information."""
        st = self.st
        n0, n2 = st.n_in, st.n_out
        cid, lab = f"evan{s}", "Затухающая волна: длина спада амплитуды по |E|² запуска"
        q = thin_films.evanescent_q(n0, n2, th)
        K = 1.0 + n2 * n2 / q if q > 0 else math.inf
        L_run, ln, z = None, None, None
        I0, I1 = field(st, lam, th, [0.0, 0.25 * lam])
        if I0 > I1 > 0:
            z = 0.5 * lam / math.log(I0 / I1)  # the decay length from the first pair of depths
            if math.isfinite(z) and z > 0:
                I0, I2 = field(st, lam, th, [0.0, z])
                if I0 > I2 > 0:
                    ln = math.log(I0 / I2)
                    L_run = 2 * z / ln
        L_ref = thin_films.evanescent_length(n0, n2, lam, th) if q > 0 else None
        tol = (4.5 * K + 9 + 15 / (ln if ln else 1.0)) * U if math.isfinite(K) else math.inf
        cond = f"число обусловленности K = n₀² sin²θ / (n₀² sin²θ − n_s²) = {K:.3g}" if math.isfinite(K) else \
            "n₀ sin θ = n_s в пределах округления"
        if tol > 1e-2:
            self._check(cid, lab + " (для сведения)", L_run, L_ref, "нм", G, info=True,
                        note=f"θ отличается от критического угла на величину порядка округления: {cond}, угол задаёт "
                             "длину спада лишь с точностью ~K·2⁻⁵³ (первый порядок оценки ошибки тут неприменим); "
                             + ("поле запуска за гранью не спадает (волна скользит вдоль грани)" if L_run is None
                                else "длина по полю запуска показана для сведения"))
            return
        if L_run is None:
            self._check(cid, lab, None, L_ref, "нм", G, ok=False, tol=tol,
                        note=f"поле запуска за гранью не спадает, а эталон даёт конечную длину; {cond}")
            return
        rel = (L_run - L_ref) / L_ref
        self._check(cid, lab, L_run, L_ref, "нм", G, tol=tol, ok=abs(rel) <= tol,
                    note=f"по |E|² на грани и на глубине {z:.4g} нм (ln отношения = {ln:.3g}); "
                         f"эталон λ/(2π√(n₀² sin²θ − n_s²)), подкоренное — в 160-битной арифметике; допуск "
                         f"(4,5K + 9 + 15/ln)·2⁻⁵³ из оценки ошибки округления, {cond}")

    def _airy_checks(self, s, G, cv, lam, th, Tc):
        """Fabry-Perot film: the run's T at (lambda, theta) and over its spectrum against the Airy intensity formula
        (thin_films.airy, with the engine's Snell cosines and phase). Tolerance: the sum of the two routes'
        first-order rounding bounds (airy err_T, growing as 1/(1 - rho) just below grazing inside the film where
        F -> infinity; thin_films.stack_error_single_layer err_T). Where that exceeds 1e-9 the routes are also
        compared 1e-3 rad further from grazing (the formula needs a propagating wave in the film)."""
        st, p, pm = self.st, self.params, self.params["pol"]
        n1, d = float(p["fp_n"]), float(p["fp_d_nm"])
        pols = ("s", "p") if pm == "unpol" else (pm,)

        def at(a_, lam_):
            """{pol: (T of the formula, bound)} at angle a_ and wavelength lam_."""
            out = {}
            for q in ("s", "p"):
                A = thin_films.airy(st.n_in, n1, st.n_out, d, lam_, a_, q)
                M = thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, lam_, a_, q)
                out[q] = (A["T"], A["err_T"] + M["err_T"], A)
            return out

        try:
            here = at(th, lam)
        except ValueError as e:
            self._check(f"airy{s}", "Фабри–Перо: T запуска и формула Эйри", Tc, None, "", G,
                        note=f"формула Эйри в интенсивностях здесь не применима: {e}")
            return
        ref = sum(here[q][0] for q in pols) / len(pols)
        bound = sum(here[q][1] for q in pols) / len(pols)
        ok = abs(Tc - ref) <= bound
        q0 = pols[0]
        note = (f"эталон T = T_max/(1 + F sin²(Δ/2)), F = {here[q0][2]['F']:.6g}, T_max = {here[q0][2]['T_max']:.6g} "
                f"({q0}); при n₀ = n_s это 1/(1 + F sin²(δ/2)); косинусы Снелла и фаза слоя — общие с матрицами; "
                f"допуск |ΔT| ≤ {bound:.2g} — сумма оценок ошибки округления обоих путей")
        side_th = th - 1e-3 if th > 1e-3 else None
        side = None
        if bound > 1e-9 and side_th is not None:
            try:
                side = at(side_th, lam)
            except ValueError:
                side = None
            if side is not None:
                Ts = sum(rta(st, lam, side_th, q)["T"] for q in pols) / len(pols)
                refs = sum(side[q][0] for q in pols) / len(pols)
                bs = sum(side[q][1] for q in pols) / len(pols)
                ok = ok and abs(Ts - refs) <= bs
                note += (f"; F велико (волна в плёнке почти скользит): пути сравнены и при θ − 0,001 рад: "
                         f"|ΔT| = {abs(Ts - refs):.2g} при допуске {bs:.2g}")
        self._check(f"airy{s}", "Фабри–Перо: T(λ, θ) запуска", Tc, ref, "", G,
                    tol=bound / abs(ref) if ref else bound, ok=ok, note=note)
        # the whole spectrum at the current angle (the cosines do not depend on lambda: no dispersion)
        lg = cv["lam"]
        dev, tol, ok = 0.0, 0.0, True
        for q in pols:
            for x, Tr in zip(lg, cv["lT" + q]):
                A = thin_films.airy(st.n_in, n1, st.n_out, d, float(x), th, q)
                b = A["err_T"] + thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, float(x), th, q)["err_T"]
                e = abs(A["T"] - Tr)
                dev, tol, ok = max(dev, e), max(tol, b), ok and e <= b
        note = f"{len(lg)} длин волн при текущем угле; допуск в каждой точке — сумма оценок ошибки округления обоих путей"
        if tol > 1e-9 and side is not None:
            dev_s, tol_s = 0.0, 0.0
            for q in pols:
                for x in lg:
                    A = thin_films.airy(st.n_in, n1, st.n_out, d, float(x), side_th, q)
                    b = A["err_T"] + thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, float(x), side_th,
                                                                         q)["err_T"]
                    e = abs(A["T"] - rta(st, float(x), side_th, q)["T"])
                    dev_s, tol_s, ok = max(dev_s, e), max(tol_s, b), ok and e <= b
            note += f"; и при θ − 0,001 рад: max |ΔT| = {dev_s:.2g} при допуске до {tol_s:.2g}"
        self._check(f"airymax{s}", "Фабри–Перо: max |T − T_Эйри| по всему рассчитанному спектру", dev, 0.0, "",
                    G, tol=tol, ok=ok, note=note)

    def _film_check(self, s, G, cur, lam, th):
        """One layer: r, t of the transfer matrices against the Airy sum (thin_films.single_film, with the engine's
        Snell cosines, so that the routes differ in the algebra only). Tolerance: the sum of the two routes'
        first-order rounding bounds (single_film err_r/err_t, growing as 1/|D| near grazing in the layer, D = 1 +
        r01 r12 e^{2i beta}; thin_films.stack_error_single_layer). At exact grazing (0/0) or where that tolerance
        exceeds 1e-9 the routes are also compared at theta -/+ 1e-3 rad, where the sum is well-conditioned."""
        st = self.st
        n1, d = st.layers[0][0], st.layers[0][1]

        def compare(a_):
            """(max |difference|, max bound, every difference within its own bound) over r, t and s, p."""
            rows = []
            for q in ("s", "p"):
                sf = thin_films.single_film(st.n_in, n1, st.n_out, d, lam, a_, q)
                mt = cur[q] if a_ == th else rta(st, lam, a_, q)
                mb = thin_films.stack_error_single_layer(st.n_in, n1, st.n_out, d, lam, a_, q)
                rows += [(abs(sf["r"] - mt["r"]), sf["err_r"] + mb["err_r"]),
                         (abs(sf["t"] - mt["t"]), sf["err_t"] + mb["err_t"])]
            return max(x for x, _ in rows), max(b for _, b in rows), all(x <= b for x, b in rows)

        try:
            here = compare(th)
        except ValueError:  # cos theta1 = 0 exactly: the Airy sum is 0/0 (the matrices are regular)
            here = None
        side = None
        if here is None or here[1] > 1e-9:
            side = [compare(a_) for a_ in (th - 1e-3, th + 1e-3)]
        ok = all(w[2] for w in ([here] if here else []) + (side or []))
        diff, tol = (here[0], here[1]) if here else (max(w[0] for w in side), max(w[1] for w in side))
        note = ("max |Δr|, |Δt| по s и p; матрицы переноса и суммирование отражений — разные пути (косинусы Снелла "
                f"общие); допуск — сумма оценок ошибки округления обоих путей, {tol:.2g}")
        if here is None:
            note += ("; волна в слое сейчас скользит вдоль границ (cos θ₁ = 0): сумма отражений здесь 0/0 "
                     "(устранимая особенность), поэтому сравнение — при θ ∓ 0,001 рад")
        elif side:
            note += (f"; знаменатель суммы отражений мал (волна в слое почти скользит): допуск велик, поэтому пути "
                     f"сравнены и при θ ∓ 0,001 рад: |Δ| ≤ {max(w[0] for w in side):.2g} при допуске "
                     f"{max(w[1] for w in side):.2g}")
        self._check(f"film{s}", "Один слой: r и t запуска = сумма многократных отражений (Эйри, комплексные "
                    "коэффициенты Френеля)", diff, 0.0, "", G, tol=tol, ok=ok, note=note)

    # --- the photon stream ----------------------------------------------------------------------------
    def max_step(self):
        return 2e4 / float(self.params["rate"])

    def _emissions(self, t_target):
        rate = float(self.params["rate"])
        out = []
        while self.t_next <= t_target:
            m = int(min(2e5, max(16, (t_target - self.t_next) * rate * 1.2 + 16)))
            gaps = self.rng.exponential(1.0 / rate, m)
            times = self.t_next + np.concatenate([[0.0], np.cumsum(gaps[:-1])])
            k = int(np.searchsorted(times, t_target, side="right"))
            out.append(times[:k])
            if k < m:
                self.t_next = float(times[k])
            else:
                self.t_next = float(times[-1] + gaps[-1])
        return np.concatenate(out) if out else np.zeros(0)

    def _emit_photons(self, te):
        k = len(te)
        pm = self.params["pol"]
        if pm == "s":
            pol = np.zeros(k, np.int8)
        elif pm == "p":
            pol = np.ones(k, np.int8)
        else:  # the 50/50 mixture: each photon is s or p
            pol = (self.rng.random(k) < 0.5).astype(np.int8)
        self.flight.add(pid=np.arange(self.pid, self.pid + k), te=te, ts=te + self.times["t_in"],
                        lam=np.full(k, float(self.params["lam_nm"])), pol=pol, sege=np.full(k, self.seg),
                        stage=np.zeros(k))
        self.pid += k
        self.tot["emitted"] += k

    def _probs(self, lam, pol):
        key = (float(lam), int(pol))
        if key not in self.cache:
            th = math.radians(self.params["theta_deg"])
            self.cache[key] = born_probs(rta(self.st, float(lam), th, "sp"[int(pol)]))
        return self.cache[key]

    def _at_structure(self, idx):
        """The photons reach the structure present now: the fate of each by the Born rule with its R, T, A."""
        a = self.flight.a
        lam, pol = a["lam"][idx], a["pol"][idx]
        R = np.empty(len(idx))
        T = np.empty(len(idx))
        for lv in np.unique(lam):
            for pv in np.unique(pol):
                m = (lam == lv) & (pol == pv)
                if m.any():
                    R[m], T[m], _ = self._probs(lv, pv)
        u = self.rng.random(len(idx))
        out = np.where(u < R, 0, np.where(u < R + T, 1, 2)).astype(np.int8)
        ts = a["ts"][idx]
        tR, tT = ts + self.times["t_R"], ts + self.times["t_T"]
        den = R + T
        with np.errstate(invalid="ignore", divide="ignore"):
            wR = np.where(den > 0, R / np.where(den > 0, den, 1.0), 0.0)
        a["out"][idx] = out
        a["seg"][idx] = np.where(a["sege"][idx] == self.seg, self.seg, -1)
        a["tR"][idx], a["tT"][idx] = tR, tT
        a["wR"][idx], a["wT"][idx] = wR, np.where(den > 0, 1.0 - wR, 0.0)
        a["tdet"][idx] = np.where(out == 0, tR, np.where(out == 1, tT, ts))
        a["stage"][idx] = 1

    def _reveal(self, done, t_target):
        a = self.flight.a
        ii = np.nonzero(done)[0]
        ii = ii[np.argsort(a["tdet"][ii], kind="stable")]
        out, seg = a["out"][ii], a["seg"][ii]
        for j, name in enumerate(OUT_NAMES):
            self.tot[name] += int(np.sum(out == j))
        self.tot["transitional"] += int(np.sum(seg < 0))
        by_seg = []
        for sv in np.unique(seg):
            m = seg == sv
            row = [int(np.sum(out[m] == j)) for j in range(3)]
            by_seg.append([int(sv)] + row)
            if sv >= 0:
                c = self.segc[int(sv)]
                c["n"] += int(m.sum())
                for j, name in enumerate(OUT_NAMES):
                    c[name] += row[j]
        # the exact counts of this step per segment (-1: transitional) and outcome go into the record; the individual
        # detections (for the view's flashes) are the last 256 of the step
        sh = ii[-256:]
        self._msg({"type": "clicks", "t": t_target, "n": int(len(ii)), "by_seg": by_seg, "shown": int(len(sh))},
                  {"t": a["tdet"][sh].astype(np.float64), "det": a["out"][sh].astype(np.uint8),
                   "pol": a["pol"][sh].astype(np.uint8), "seg": a["seg"][sh].astype(np.int32),
                   "te": a["te"][sh].astype(np.float64)})
        self.flight.keep(~done)

    def advance(self, t_target):
        te = self._emissions(t_target)
        if len(te):
            self._emit_photons(te)
        a = self.flight.a
        idx = np.nonzero((a["stage"] == 0) & (a["ts"] <= t_target))[0]
        if len(idx):
            self._at_structure(idx)
        a = self.flight.a
        done = (a["stage"] == 1) & (a["tdet"] <= t_target)
        if done.any():
            self._reveal(done, t_target)
        self.t = t_target
        c = self.segc[self.seg]
        if c["n"] >= self._stat_next:
            self._stat_check(self.seg)
            while self._stat_next <= c["n"]:
                self._stat_next = _next_step(self._stat_next)

    def next_event_time(self):
        """The next emission, the next arrival at the structure or at a detector."""
        a = self.flight.a
        cands = [self.t_next]
        m0, m1 = a["stage"] == 0, a["stage"] == 1
        if m0.any():
            cands.append(float(a["ts"][m0].min()))
        if m1.any():
            cands.append(float(a["tdet"][m1].min()))
        return min(cands)

    # --- frames -----------------------------------------------------------------------------------------
    def frame(self):
        """Photons under way as the viewer may know them at time t: on the way in, a progress along the incident
        arm; after the structure, not yet detected: the reflected and transmitted packets (weights R/(R+T), T/(R+T));
        once a detector's arrival time has passed without a click, that packet is gone (Lueders update)."""
        a = self.flight.a
        t = self.t
        n = len(self.flight)
        fl = np.zeros((n, 6))
        if n:
            st0 = a["stage"] == 0
            fl[:, 0] = a["stage"]
            fl[:, 1] = a["pol"]
            fl[st0, 2] = (t - a["te"][st0]) / np.maximum(a["ts"][st0] - a["te"][st0], 1e-300)
            s1 = ~st0
            ts, tR, tT = a["ts"][s1], a["tR"][s1], a["tT"][s1]
            wR, wT = a["wR"][s1].copy(), a["wT"][s1].copy()
            goneT = t >= tT  # the transmission detector stayed silent: only the reflected packet is left
            goneR = t >= tR
            wR[goneT & ~goneR & (wR > 0)] = 1.0
            wT[goneT] = 0.0
            wT[goneR & ~goneT & (wT > 0)] = 1.0
            wR[goneR] = 0.0
            fl[s1, 2] = (t - ts) / np.maximum(tR - ts, 1e-300)
            fl[s1, 3] = wR
            fl[s1, 4] = (t - ts) / np.maximum(tT - ts, 1e-300)
            fl[s1, 5] = wT
            if n > 400:
                fl = fl[np.linspace(0, n - 1, 400).astype(int)]
        c = self.segc[self.seg]
        cnt = {k: c[k] for k in ("n", "R", "T", "A")}
        exp = {k: c["p" + k] for k in OUT_NAMES}
        sig = {k: (math.sqrt(exp[k] * (1 - exp[k]) / c["n"]) if c["n"] else None) for k in OUT_NAMES}
        z = None
        if c["n"]:
            sR = math.sqrt(c["n"] * exp["R"] * (1 - exp["R"]))
            z = (c["R"] - c["n"] * exp["R"]) / sR if sR > 0 else (0.0 if c["R"] == round(c["n"] * exp["R"]) else None)
        return ({"seg": self.seg, "counts": cnt, "expected": exp, "sigma": sig, "z": z, "totals": dict(self.tot),
                 "in_flight": n}, {"fl": fl})

    def header(self):
        return {
            "title": self._title(),
            "text": ("Источник выпускает фотоны по одному (пуассоновский поток) на плоскую структуру: границу двух сред, "
                     "просветляющий слой, брэгговское зеркало, плёнку Фабри–Перо, металлическую плёнку или грань призмы "
                     "(полное внутреннее отражение, с зазором — туннелирование). Для каждой установки запуск считает "
                     "матрицами переноса движка lfphys амплитуды r, t и вероятности R, T, A, кривые R(θ), T(θ), R(λ), "
                     "T(λ) и поле |E|² внутри структуры. Каждый фотон, долетев до структуры, получает судьбу по правилу "
                     "Борна с этими вероятностями; узнаём её, когда он долетает до детектора (поглощённый — исчезает в "
                     "структуре). Счётчики — накопление этих событий, рядом — ожидание запуска."),
            "modifications": SCHEMA.modifications(self.params),
            "actions": self._actions(),
            "arm_m": ARM_M, "t_in": self.times["t_in"], "rate": float(self.params["rate"]),
        }, {}


def _refine_min_rp(st, lam, lo_deg, hi_deg, start):
    """Bounded Brent minimisation of the run's R_p(theta) between two grid neighbours of the grid minimum."""
    from scipy.optimize import minimize_scalar
    f = lambda d: rta(st, lam, math.radians(d), "p")["R"]  # noqa: E731
    try:
        r = minimize_scalar(f, bounds=(lo_deg, hi_deg), method="bounded", options={"xatol": 1e-9})
    except (ValueError, ZeroDivisionError, FloatingPointError):
        return {}
    if not (math.isfinite(r.fun) and r.fun <= start["Rp"]):
        return {}
    return {"deg": float(r.x), "Rp": float(r.fun)}


def _next_step(x):
    e = 10 ** math.floor(math.log10(x) + 1e-12)
    m = round(x / e)
    for s in STAT_STEPS + (10,):
        if s > m:
            return s * e
    return 10 * e


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _fmt(p, v):
    if p.type == "select":
        return dict(p.options).get(v, v)
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


VIZ = {
    "id": "v05_optics_bench",
    "title": "Оптический стол: границы сред и покрытия",
    "summary": ("Фотоны по одному на границу двух сред, просветляющий слой, брэгговское зеркало, плёнку Фабри–Перо, "
                "металлическую плёнку, грань призмы (полное и нарушенное полное отражение). Угол Брюстера, критический "
                "угол, спектры R(λ), T(λ), поле |E|² в слоях."),
    "purpose": ("Как из уравнений Максвелла на границах (матрицы переноса) получаются отражение, пропускание и "
                "поглощение, и как отдельные фотоны по правилу Борна складываются в эти доли."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
