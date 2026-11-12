# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v07: the Bell test with entangled pairs, a wrapper over the physics engine lfphys.

What the run computes (README.md of this folder has the model in full):
* a Poisson stream of pairs from a source between two stations at distance L; each particle flies to its station
  and its outcome is revealed only when it arrives (both at t_e + L/v);
* the stations' settings: fixed (a and b) or a fresh random choice for every particle, made a time tau before it
  arrives; the space-time relation of every choice to the other side's detection and to the emission
  (lfphys.core.causality);
* the outcomes by the world's law: the Born rule on the entangled state (lfphys.core.quantum.qubits) or a local
  hidden-variable model (lfphys.theories.alternatives.local_hidden);
* coincidence counts per setting pair, E with its error, CHSH S with its error, the marginals (no-signalling) and the
  measured E(delta) points (lfphys.tools.bell_stats);
* checks: each measured quantity against the exact expectation of the world's law (z-scores), the classical bound 2,
  the Tsirelson bound 2 sqrt 2, no-signalling, and the space-time relations against closed forms and the Lorentz
  matrices.
"""

from __future__ import annotations

import math

import numpy as np
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from lfphys.core import causality as K
from lfphys.core import relativity as R
from lfphys.core.constants import C
from lfphys.core.quantum import qubits as Q
from lfphys.tools import bell_stats as BS

from .engine.experiment import (F_FREE_A, F_FREE_B, F_LOC_A, F_LOC_B, MODEL_LABEL, PAIR_LABEL, Experiment, Law,
                                Store)

TSIRELSON = 2.0 * math.sqrt(2.0)
NMIN = 30          # pairs per cell before an estimate is compared with its reference (normal approximation)
ZTOL = 5.0         # tolerance of the statistical checks, in standard errors
DETAIL = 16        # per-pair detail sent per step (all pairs enter the statistics; the view needs the newest)


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("pair", "Пары", "select", "photon", group="Источник (мир)",
       options=[("photon", "фотоны: поляризация |Φ+⟩ = (|HH⟩ + |VV⟩)/√2, поляризаторы"),
                ("spin", "спин ½: синглет (|↑↓⟩ − |↓↑⟩)/√2, магниты Штерна–Герлаха")],
       help="Тип пары задаёт состояние, анализаторы и скорость частиц; меняется только новым миром."),
    _p("spin_beta", "Скорость частиц спиновой пары, v/c", "float", 0.5, group="Источник (мир)", min=1e-4, max=0.999,
       log=True, show_if={"pair": ["spin"]},
       help="Иллюстративно: массивные частицы со спином ½ (например, протоны). Фотоны летят со скоростью c."),
    _p("law", "Закон корреляций", "select", "quantum", group="Законы (модификации)", standard="quantum",
       options=[("quantum", "квантовая механика: правило Борна для запутанного состояния"),
                ("lhv", "локальные скрытые параметры (фотоны: поляризационная модель; спин: знаковая модель Белла)")],
       help="Квантовая механика — общепринятая физика. Локальные скрытые параметры — модификация «что если»: исход "
            "каждой стороны задан её настройкой и общим параметром из источника."),
    _p("L_m", "Расстояние источник — станция L, м", "float", 500.0, group="Геометрия", min=0.01, max=1e5, log=True,
       live=True, help="Станции Алисы (−L) и Боба (+L) на одной прямой с источником; расстояние между ними 2L."),
    _p("rate", "Пар в секунду (время мира)", "float", 1e6, group="Источник", min=1e-3, max=1e9, log=True, live=True),
    _p("switch", "Выбор настройки", "select", "random", group="Выбор настроек",
       options=[("fixed", "фиксированный: Алиса a, Боб b"),
                ("random", "случайный для каждой частицы (как в опытах без лазеек)")], live=True),
    _p("tau_ns", "Выбор делается за τ до прихода частицы, нс", "float", 100.0, group="Выбор настроек", min=1e-3,
       max=1e7, log=True, show_if={"switch": ["random"]}, live=True,
       help="Генератор случайных чисел станции выдаёт бит за τ до прихода частицы (задержка генератора и "
            "переключателя). Выбор вне светового конуса регистрации на другой стороне, если cτ < 2L."),
    _p("a_deg", "Алиса: настройка a, °", "float", 0.0, group="Настройки Алисы (A)", min=-360, max=360, live=True),
    _p("a2_deg", "Алиса: настройка a′, °", "float", 45.0, group="Настройки Алисы (A)", min=-360, max=360, live=True),
    _p("b_deg", "Боб: настройка b, °", "float", 22.5, group="Настройки Боба (B)", min=-360, max=360, live=True),
    _p("b2_deg", "Боб: настройка b′, °", "float", 67.5, group="Настройки Боба (B)", min=-360, max=360, live=True),
], presets={
    "photon_chsh": {"label": "Фотоны |Φ+⟩, квантовая механика: оптимальные углы CHSH 0°, 45° / 22.5°, 67.5°, "
                             "случайный выбор", "params": {}},
    "spin_chsh": {"label": "Синглет спина ½, квантовая механика: оптимальные углы 0°, 90° / 45°, 135°, случайный выбор",
                  "params": {"pair": "spin", "a_deg": 0.0, "a2_deg": 90.0, "b_deg": 45.0, "b2_deg": 135.0}},
    "photon_lhv": {"label": "Фотоны, локальные скрытые параметры: поляризационная модель (модификация)",
                   "params": {"law": "lhv"}},
    "spin_lhv": {"label": "Синглет спина ½, локальные скрытые параметры: знаковая модель Белла (модификация)",
                 "params": {"pair": "spin", "law": "lhv", "a_deg": 0.0, "a2_deg": 90.0, "b_deg": 45.0,
                            "b2_deg": 135.0}},
    "scan": {"label": "Кривая E(Δ): фотоны, фиксированные настройки a = b = 0° — двигайте b",
             "params": {"switch": "fixed", "a_deg": 0.0, "b_deg": 0.0}},
    "photon_slow_choice": {"label": "Фотоны: выбор за 5 мкс до прихода (cτ > 2L) — лазейка локальности открыта",
                           "params": {"tau_ns": 5000.0}},
})

ANGLES = ("a_deg", "a2_deg", "b_deg", "b2_deg")


class Simulation(BaseSimulation):
    speed_range = (1e-12, 1e3)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self.law = Law(params["pair"], params["law"])
        self.v = C if params["pair"] == "photon" else float(params["spin_beta"]) * C
        self.exp = Experiment(self.law, self.v, C, self.rng)
        self.store = Store()
        L = self.params["L_m"]
        self.t_set = {"A": (0.0, -L), "B": (0.0, L)}  # when (and where) the fixed settings were last chosen
        self.t_next = self.rng.exponential(1.0 / self.params["rate"])
        self.counts = dict(emitted=0, detected=0, lost=0)
        self.seg = 0
        self.seg_t0 = 0.0
        self.seg_counts = dict(detected=0, loc=0, free=0)
        self.n_checked = 0
        self.viol_said = False
        self._buf = []
        self.default_speed = min(max(self._flight() / 2.0, self.speed_range[0]), self.speed_range[1])
        self._engine_checks()
        self._setup_checks()
        self._spacetime_checks()
        self._stat_checks()

    # --- helpers ---------------------------------------------------------------------------------------
    def _flight(self):
        return self.params["L_m"] / self.v

    def _tau(self):
        return self.params["tau_ns"] * 1e-9

    def _angles(self):
        P = self.params
        return {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"]}

    def _cell_angles(self):
        P = self.params
        return [("a", "b", P["a_deg"], P["b_deg"]), ("a", "b′", P["a_deg"], P["b2_deg"]),
                ("a′", "b", P["a2_deg"], P["b_deg"]), ("a′", "b′", P["a2_deg"], P["b2_deg"])]

    def engine_modules(self):
        mods = ["core.constants", "core.quantum.qubits", "core.causality", "core.relativity", "tools.bell_stats"]
        if self.law.law == "lhv":
            mods.append("theories.alternatives.local_hidden")
        return mods

    # --- messages -----------------------------------------------------------------------------------------
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
        """``info``: a comparison shown for information (an identity of the model, say), never a pass or a failure
        (RULES.md §3, check message)."""
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

    def _actions(self):
        return [{"name": "clear", "label": "Сбросить статистику",
                 "help": "Счёты совпадений начинаются заново; установка и пары в полёте те же.", "args": []}]

    # --- checks: the law and the set-up ---------------------------------------------------------------------
    def _engine_checks(self):
        """Once per world: properties of the source state computed by the engine."""
        g = "Источник: состояние пары"
        if self.law.law == "quantum":
            rho = Q.dm(self.law.state)
            self._check("conc", "Запутанность состояния: согласованность (concurrence) Вуттерса", Q.concurrence(rho),
                        1.0, "", g, tol=1e-12, note="1 — максимально запутанное состояние (движок: lfphys.core.quantum.qubits)")
            ent = Q.entropy(Q.ptrace(rho, 0))
            self._check("ent", "Энтропия одной частицы пары (бит)", ent, 1.0, "", g, tol=1e-12,
                        note="частица порознь — полностью неполяризована: её маргиналы 1/2 при любой настройке")
        else:
            self._check("conc", "Источник по модели ЛСП: общий скрытый параметр λ, без квантового состояния", None,
                        None, "", g, note=f"{MODEL_LABEL[self.law.model]}: исход стороны = функция её настройки и λ "
                                           "(локальность по построению)")

    def _setup_checks(self):
        """After every change of the settings: the exact expectation of the world's law."""
        law, P = self.law, self.params
        a, a2, b, b2 = (P[k] for k in ANGLES)
        g = "Установка: ожидание закона мира (точно)"
        S_law = law.S(a, a2, b, b2)
        if law.law == "quantum":
            S_cf = sum(s * law.E_closed_form(x, y) for s, (_, _, x, y) in zip(BS.CHSH_SIGNS, self._cell_angles()))
            self._check("S_law", "S при текущих настройках: след Tr(ρ A⊗B) движка", S_law, S_cf, "", g, tol=1e-12,
                        note=("эталон — замкнутая форма E = cos 2(α_A − α_B) для |Φ+⟩" if law.pair == "photon"
                              else "эталон — замкнутая форма E = −cos(θ_A − θ_B) для синглета")
                        + "; S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′)")
            mA = [abs(law.marginal_A_quantum(x, b) - law.marginal_A_quantum(x, b2)) for x in (a, a2)]
            mB = [abs(law.marginal_B_quantum(a, y) - law.marginal_B_quantum(a2, y)) for y in (b, b2)]
            dmax = max(mA + mB)
            self._check("nosig_law", "Без сигнала в законе (точно): маргинал одной стороны от настройки другой",
                        dmax, 0.0, "", g, ok=dmax < 1e-14,
                        note="max |P_A(+|x,b) − P_A(+|x,b′)|, |P_B(+|a,y) − P_B(+|a′,y)| из совместных вероятностей "
                             "Борна Tr(ρ Π⊗Π)")
        else:
            self._check("S_law", "S при текущих настройках по модели ЛСП", S_law, None, "", g,
                        note=f"{MODEL_LABEL[law.model]}: E — функция модели движка "
                             + ("½cos 2(α_A − α_B)" if law.pair == "photon" else "−1 + 2θ/π"))
            self._check("nosig_law", "Без сигнала в законе модели ЛСП: по построению (для сведения)", 0.5, None, "", g,
                        info=True,
                        note="исход каждой стороны — функция только её настройки и λ (локальность по построению), "
                             "λ распределён изотропно: P(+) = 1/2 при любой настройке другой стороны. Это тождество "
                             "модели, а не проверка; проверка по счётам запуска — в группе «Без сигнала»")
        if law.law == "quantum":
            self._check("tsir_law", "Ожидание закона: |S| ≤ 2√2 (граница Цирельсона)", abs(S_law), TSIRELSON, "", g,
                        ok=abs(S_law) <= TSIRELSON + 1e-12, note="никакая квантовая теория не даёт больше")
        else:
            self._check("tsir_law", "Ожидание модели ЛСП и граница Цирельсона 2√2 (для сведения)", abs(S_law),
                        TSIRELSON, "", g, info=True,
                        note="в мире ЛСП следует из проверки |S| ≤ 2 (строкой ниже): не отдельная проверка")
        bound_ok = abs(S_law) <= 2.0 + 1e-12
        if law.law == "lhv":
            self._check("chsh_law", "Ожидание модели ЛСП: |S| ≤ 2 (граница CHSH)", abs(S_law), 2.0, "", g,
                        ok=bound_ok, note="любая локальная модель обязана соблюдать эту границу")
        else:  # information, not a test: quantum mechanics may exceed 2
            self._check("chsh_law", "Квантовое ожидание |S| и классическая граница 2", abs(S_law), None, "", g,
                        note=("превышает 2: квантовая механика нарушает неравенство CHSH при этих настройках"
                              if not bound_ok else "при этих настройках квантовое ожидание не превышает 2"))
        self._S_law = S_law

    def _spacetime_checks(self):
        """The space-time relation of the setting choices for a pair emitted now (nominal geometry)."""
        P = self.params
        L, c, v = P["L_m"], C, self.v
        g = "Пространство-время: выбор настройки и регистрация"
        # events of a pair emitted now, counted from its emission (intervals are translation invariant; this avoids
        # the cancellation of large world times)
        te = 0.0
        tarr = L / v
        detB = (tarr, L)
        em = (te, 0.0)
        if P["switch"] == "random":
            tau = self._tau()
            chA = (tarr - tau, -L)
            s2 = K.interval(chA, detB, c)
            rel = K.relation(chA, detB, c)
            txt = {K.SPACELIKE: "пространственноподобны — лазейка локальности закрыта",
                   K.TIMELIKE: "времениподобны — лазейка локальности ОТКРЫТА",
                   K.LIGHTLIKE: "светоподобны (на границе конуса)"}[rel]
            self._check("st_loc", "Выбор у A ↔ регистрация у B: " + txt, s2, (c * tau) ** 2 - (2 * L) ** 2, "м²", g,
                        tol=1e-9, note=f"s² = c²τ² − (2L)², cτ = {c * tau:.4g} м, 2L = {2 * L:.4g} м: сигнал от выбора у A "
                                       + ("не успевает" if rel == K.SPACELIKE else "успевает")
                                       + " к регистрации у B (и симметрично от B к A); эталон — замкнутая форма")
            if rel == K.SPACELIKE:
                beta = K.order_reversal_speed(chA, detB, c)
                self._check("st_rev", "Порядок «выбор у A → регистрация у B» обращается в системе, летящей от A к B "
                                      "быстрее v*; v*/c =", beta, _reversal_by_boosts(chA, detB), "", g, tol=1e-9,
                            note="v* = c²τ/(2L) < c: время между событиями не абсолютно, причинной связи нет; эталон — "
                                 "поиск нуля Δt′ по матрицам Лоренца (lfphys.core.relativity.boost_matrix)")
            else:
                self._check("st_rev", "Порядок «выбор у A → регистрация у B» абсолютен (времениподобные события)",
                            None, None, "", g, note="ни в одной инерциальной системе он не обращается")
            s2e = K.interval(chA, em, c)
            rel_e = K.relation(chA, em, c)
            before = tarr - tau < te
            txe = {K.SPACELIKE: "пространственноподобны — выбор и источник независимы",
                   K.TIMELIKE: ("выбор в прошлом конусе вылета — сигнал от выбора успевает к источнику"
                                if before else "выбор в будущем конусе вылета — лазейка свободы выбора открыта"),
                   K.LIGHTLIKE: "светоподобны"}[rel_e]
            self._check("st_free", "Выбор у A ↔ вылет пары: " + txe, s2e,
                        (c * (tarr - tau - te)) ** 2 - L ** 2, "м²", g, tol=1e-9,
                        note=f"s² = c²(L/v − τ)² − L²; время полёта L/v = {L / v:.4g} с, τ = {tau:.4g} с")
        else:
            tA, xA = self.t_set["A"]
            tA -= self.t  # the same origin: the emission of a pair now
            chA = (tA, xA)
            s2 = K.interval(chA, detB, c)
            rel = K.relation(chA, detB, c)
            txt = {K.SPACELIKE: "пространственноподобны (настройка задана только что)",
                   K.TIMELIKE: "времениподобны — настройки известны заранее, лазейка локальности ОТКРЫТА",
                   K.LIGHTLIKE: "светоподобны"}[rel]
            self._check("st_loc", "Фиксированная настройка a ↔ регистрация у B ближайшей пары: " + txt, s2,
                        (c * (tarr - tA)) ** 2 - (L - xA) ** 2, "м²", g, tol=1e-9,
                        note=f"настройка a задана за {abs(tA):.6g} с до вылета пары, пара придёт через {tarr:.6g} с "
                             "после вылета")
            for cid in ("st_rev", "st_free"):
                self._check(cid, "Только для случайного выбора настроек", None, None, "", g,
                            note="при фиксированных настройках выбор сделан при установке")

    # --- checks: the statistics of the run's own pairs ------------------------------------------------------
    def _cells(self):
        out = []
        for x, y, al, be in self._cell_angles():
            n = self.store.get(al, be)
            E, se, N = BS.correlation(n)
            Eref = self.law.E(al, be)
            z = BS.zscore(E, Eref, BS.se_under(Eref, N)) if N else None
            out.append({"x": x, "y": y, "alA": al, "alB": be, "n": [int(q) for q in n], "N": N, "E": E, "se": se,
                        "Eref": Eref, "z": z})
        return out

    def _S(self, cells):
        """S of the four cells and its error. With coinciding settings (a' = a or b' = b) two cells are the same
        angle pair, i.e. the same counts (Store keys by angle pair): the error counts them once (bell_stats.chsh with
        keys; review 2026-10-23, V7-2) and ``same`` lists the coinciding cells."""
        keys = [Store.key(c["alA"], c["alB"]) for c in cells]
        same = [f"({c['x']},{c['y']})" for k, c in enumerate(cells) if keys.index(keys[k]) != k]
        Sref = sum(s * c["Eref"] for s, c in zip(BS.CHSH_SIGNS, cells))
        S, se = BS.chsh([c["n"] for c in cells], keys=keys)
        if S is None:
            return {"S": None, "se": None, "Sref": Sref, "z": None, "excess": None, "Nmin": min(c["N"] for c in cells),
                    "same": same}
        seu = BS.chsh_se_under([c["Eref"] for c in cells], [c["N"] for c in cells], keys=keys)
        excess = (abs(S) - 2.0) / se if se and se > 0 else None
        return {"S": S, "se": se, "Sref": Sref, "z": BS.zscore(S, Sref, seu), "excess": excess,
                "Nmin": min(c["N"] for c in cells), "same": same}

    @staticmethod
    def _same_note(s):
        if not s["same"]:
            return ""
        return ("; настройки совпадают (a′ = a или b′ = b): ячейки " + ", ".join(s["same"]) + " — те же пары, что и "
                "другая ячейка; S сводится к 2E одной пары углов, это не проверка CHSH; ошибка S считает каждую пару "
                "углов один раз")

    def _points(self):
        """All measured angle pairs: delta, E, se, N, E of the law (for the E(delta) plot and the chi-square)."""
        rows = []
        for (al, be), n in self.store.cells.items():
            E, se, N = BS.correlation(n)
            if N == 0:
                continue
            rows.append((float(self.law.fold(al - be)), E, se, N, self.law.E(al, be)))
        return np.array(rows, float) if rows else np.zeros((0, 5))

    def _stat_checks(self):
        self.n_checked = self.seg_counts["detected"]
        law = self.law
        cells = self._cells()
        fixed = self.params["switch"] == "fixed"
        g = "Статистика пар: измерено ↔ закон мира"
        ref_txt = "квантовое ожидание (движок)" if law.law == "quantum" else "ожидание модели ЛСП"
        for k, c in enumerate(cells):
            lab = f"E({c['x']},{c['y']}) при α_A = {c['alA']:g}°, α_B = {c['alB']:g}°"
            if c["N"] >= NMIN:
                self._check(f"E{k}", lab, c["E"], c["Eref"], "", g, ok=abs(c["z"]) < ZTOL,
                            note=f"N = {c['N']}, ± {c['se']:.3g}; z = {c['z']:+.2f} (допуск {ZTOL:g}σ); эталон — {ref_txt}")
            else:
                self._check(f"E{k}", lab, None, c["Eref"], "", g,
                            note=f"набирается: N = {c['N']} < {NMIN}"
                                 + ("; в режиме «фиксированный» набирается только пара (a, b)" if fixed and k else ""))
        s = self._S(cells)
        lab_S = "S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′)"
        if s["S"] is not None and s["Nmin"] >= NMIN:
            self._check("S", lab_S, s["S"], s["Sref"], "", g, ok=abs(s["z"]) < ZTOL,
                        note=f"± {s['se']:.3g}; z = {s['z']:+.2f} (допуск {ZTOL:g}σ); эталон — {ref_txt}"
                             + self._same_note(s))
            aS = abs(s["S"])
            self._check("tsir", "Граница Цирельсона: |S| ≤ 2√2 (с допуском 5σ)", aS, TSIRELSON, "", g,
                        ok=aS - TSIRELSON < ZTOL * s["se"], note=f"|S| = {aS:.4f} ± {s['se']:.3g}")
            if law.law == "lhv":
                self._check("bound", "Граница CHSH для локальных моделей: |S| ≤ 2 (с допуском 5σ)", aS, 2.0, "", g,
                            ok=aS - 2.0 < ZTOL * s["se"],
                            note=f"(|S| − 2)/σ = {s['excess']:+.2f}" if s["excess"] is not None else "")
            else:
                exc = s["excess"]
                if abs(s["Sref"]) > 2.0:
                    need = self._pairs_needed(cells)
                    self._check("bound", "Нарушение неравенства CHSH: (|S| − 2)/σ", exc, None, "σ", g,
                                ok=True if exc is not None and exc > ZTOL else None,
                                note=(f"|S| = {aS:.4f} ± {s['se']:.3g} > 2 на {exc:.1f}σ" if exc is not None and exc > ZTOL
                                      else f"набирается: ожидание |S| = {abs(s['Sref']):.4f}; для 5σ нужно около "
                                           f"{need:.0f} пар при случайном выборе"))
                else:
                    self._check("bound", "Нарушение неравенства CHSH: (|S| − 2)/σ", exc, None, "σ", g,
                                note=f"при этих настройках квантовое ожидание |S| = {abs(s['Sref']):.4f} ≤ 2")
        else:
            why = (f"набирается: в ячейке не меньше {NMIN} пар нужно для каждой из четырёх пар настроек"
                   + ("; в режиме «фиксированный» набирается только (a, b) — включите случайный выбор" if fixed else ""))
            self._check("S", lab_S, None, s["Sref"], "", g, note=why + self._same_note(s))
            self._check("tsir", "Граница Цирельсона: |S| ≤ 2√2 (с допуском 5σ)", None, TSIRELSON, "", g, note=why)
            self._check("bound", "Граница CHSH |S| ≤ 2" if law.law == "lhv" else "Нарушение неравенства CHSH: (|S| − 2)/σ",
                        None, 2.0 if law.law == "lhv" else None, "" if law.law == "lhv" else "σ", g, note=why)
        # E(delta): all measured angle pairs against the law
        pts = self._points()
        m = pts[:, 3] >= NMIN if len(pts) else np.zeros(0, bool)
        if np.any(m):
            x2, dof, p = BS.chi2_points(pts[m, 1], pts[m, 4], np.sqrt(np.maximum(1 - pts[m, 4] ** 2, 0) / pts[m, 3]))
            if dof:
                self._check("curve", "Кривая E(Δ): χ² измеренных точек против закона мира", x2, float(dof), "", g,
                            ok=p > 1e-6, note=f"точек с N ≥ {NMIN}: {dof}; p = {p:.3g}; эталон χ² ≈ числу точек")
        # no-signalling from the run's own counts
        gn = "Без сигнала: маргинал одной стороны не зависит от настройки другой"
        for i, (x, c1, c2) in enumerate((("a", cells[0], cells[1]), ("a′", cells[2], cells[3]))):
            self._nosig(f"nsA{i}", f"P_A(+ | {x}, b) − P_A(+ | {x}, b′)", c1, c2, "A", gn, fixed)
        for i, (y, c1, c2) in enumerate((("b", cells[0], cells[2]), ("b′", cells[1], cells[3]))):
            self._nosig(f"nsB{i}", f"P_B(+ | a, {y}) − P_B(+ | a′, {y})", c1, c2, "B", gn, fixed)
        # space-time relations of the pairs actually detected in this segment
        gs = "Пространство-время: выбор настройки и регистрация"
        n = self.seg_counts["detected"]
        if n:
            self._check("st_frac", "Доля пар: выбор настроек обеих сторон вне светового конуса регистрации на другой "
                                   "стороне", self.seg_counts["loc"] / n, None, "", gs,
                        note=f"{self.seg_counts['loc']} из {n} пар (по событиям каждой пары, lfphys.core.causality)")
            self._check("st_frac_free", "Доля пар: выбор настроек обеих сторон пространственноподобен вылету пары",
                        self.seg_counts["free"] / n, None, "", gs, note=f"{self.seg_counts['free']} из {n} пар")

    def _nosig(self, cid, label, c1, c2, side, group, fixed):
        if Store.key(c1["alA"], c1["alB"]) == Store.key(c2["alA"], c2["alB"]):  # b' = b (or a' = a): one cell
            self._check(cid, label, 0.0 if c1["N"] else None, None, "", group, info=True,
                        note="настройки другой стороны совпадают: обе ячейки — одни и те же пары, разность равна 0 "
                             "тождественно (не проверка)")
            return
        if c1["N"] >= NMIN and c2["N"] >= NMIN:
            k1 = c1["n"][0] + (c1["n"][1] if side == "A" else c1["n"][2])
            k2 = c2["n"][0] + (c2["n"][1] if side == "A" else c2["n"][2])
            d, se = BS.difference(k1, c1["N"], k2, c2["N"])
            z = BS.zscore(d, 0.0, se)
            self._check(cid, label, d, 0.0, "", group, ok=abs(z) < ZTOL,
                        note=f"P = {k1 / c1['N']:.4f} (N = {c1['N']}) и {k2 / c2['N']:.4f} (N = {c2['N']}); "
                             f"± {se:.3g}; z = {z:+.2f} (допуск {ZTOL:g}σ)")
        else:
            self._check(cid, label, None, 0.0, "", group,
                        note="набирается" + ("; при фиксированных настройках вторая настройка не используется" if fixed else ""))

    @staticmethod
    def _pairs_needed(cells):
        """Pairs for a 5-sigma excess over 2 with random choice (N/4 per cell) at the law's expectation."""
        Sref = abs(sum(s * c["Eref"] for s, c in zip(BS.CHSH_SIGNS, cells)))
        if Sref <= 2.0:
            return math.inf
        return 4.0 * sum(1 - c["Eref"] ** 2 for c in cells) * (ZTOL / (Sref - 2.0)) ** 2

    # --- live changes -------------------------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise ValueError("; ".join(errors))
        changed = [k for k in SCHEMA.live_ids() if not _same(new[k], self.params[k])]
        if not changed:
            return "без изменений"
        now = self.t
        old = self.params
        lost = self.exp.reschedule(now, old["L_m"], new["L_m"], new["tau_ns"] * 1e-9, new["switch"])
        if lost:
            self.counts["lost"] += lost
            self._msg({"type": "notice", "t": now, "text": f"Станции передвинуты: пар в полёте потеряно {lost} "
                                                          "(частица уже пролетела новое место станции)"})
        if "switch" in changed:
            self.t_set = {"A": (now, -new["L_m"]), "B": (now, new["L_m"])}
        if "a_deg" in changed:
            self.t_set["A"] = (now, -new["L_m"])
        if "b_deg" in changed:
            self.t_set["B"] = (now, new["L_m"])
        if "rate" in changed:
            self.t_next = now + self.rng.exponential(1.0 / new["rate"])  # Poisson stream: memoryless
        desc = "; ".join(f"{SCHEMA.by_id[k].label}: {_fmt(old[k])} → {_fmt(new[k])}" for k in changed)
        self.params = new
        if new["switch"] == "random" and C * new["tau_ns"] * 1e-9 >= 2 * new["L_m"] and \
                any(k in changed for k in ("tau_ns", "L_m", "switch")):
            self._msg({"type": "notice", "t": now, "text": "cτ ≥ 2L: выбор настройки во времениподобной связи с "
                                                          "регистрацией на другой стороне — лазейка локальности открыта"})
        if any(k in changed for k in ANGLES):
            self._setup_checks()
        self._spacetime_checks()
        self._stat_checks()
        return desc

    def action(self, name, args):
        if name == "clear":
            self.store.clear()
            self.seg += 1
            self.seg_t0 = self.t
            self.seg_counts = dict(detected=0, loc=0, free=0)
            self.viol_said = False
            self._stat_checks()
            return "статистика сброшена; установка и пары в полёте прежние"
        raise ValueError(f"неизвестное действие {name!r}")

    # --- time -----------------------------------------------------------------------------------------
    def max_step(self):
        return 2000.0 / self.params["rate"]

    def _emissions(self, t_target):
        rate = self.params["rate"]
        out = []
        while self.t_next <= t_target:
            k = int(min(max(16, rate * (t_target - self.t_next) * 1.2 + 16), 1_000_000))
            gaps = self.rng.exponential(1.0 / rate, k)
            ts = self.t_next + np.concatenate([[0.0], np.cumsum(gaps[:-1])])
            m = ts <= t_target
            if m.all():
                out.append(ts)
                self.t_next = float(ts[-1] + gaps[-1])
            else:
                j = int(np.argmin(m))
                out.append(ts[:j])
                self.t_next = float(ts[j])
        return np.concatenate(out) if out else np.zeros(0)

    def advance(self, t_target):
        P = self.params
        L, mode = P["L_m"], P["switch"]
        te = self._emissions(t_target)
        if len(te):
            self.exp.emit(te, L, self._tau(), mode)
            self.counts["emitted"] += len(te)
        self.exp.choose(t_target, L, mode)
        d = self.exp.detect(t_target, L, mode, self._angles(), self.t_set)
        if d is not None:
            self._detected(d, t_target)
        self.t = t_target
        n = self.seg_counts["detected"]
        if n - self.n_checked >= max(100, 0.3 * self.n_checked):
            self._stat_checks()
            self._maybe_violation_event()
            if P["switch"] == "fixed":  # the age of the fixed settings grows: their relation to the next pair changes
                self._spacetime_checks()

    def _detected(self, d, t_target):
        n = len(d["te"])
        first = self.counts["detected"] == 0
        self.counts["detected"] += n
        self.seg_counts["detected"] += n
        fl = d["flags"]
        self.seg_counts["loc"] += int(np.sum((fl & F_LOC_A > 0) & (fl & F_LOC_B > 0)))
        self.seg_counts["free"] += int(np.sum((fl & F_FREE_A > 0) & (fl & F_FREE_B > 0)))
        self.store.add(d["alA"], d["alB"], d["oA"], d["oB"],
                       protect=[(x, y) for _, _, x, y in self._cell_angles()])
        sl = slice(max(0, n - DETAIL), None)
        blobs = {"t": d["tarr"][sl], "te": d["te"][sl], "id": d["id"][sl], "sA": d["sA"][sl], "sB": d["sB"][sl],
                 "oA": d["oA"][sl], "oB": d["oB"][sl], "alA": d["alA"][sl].astype(np.float64),
                 "alB": d["alB"][sl].astype(np.float64), "tcA": d["tcA"][sl], "tcB": d["tcB"][sl],
                 "xcA": d["xcA"][sl], "xcB": d["xcB"][sl], "L": d["L"][sl], "fl": fl[sl]}
        self._msg({"type": "pairs", "t": t_target, "n": n, "seg": self.seg}, blobs)
        if first:
            i = 0
            sg = lambda o: "+" if o > 0 else "−"  # noqa: E731
            self._msg({"type": "event", "kind": "detection", "t": float(d["tarr"][0]),
                       "text": f"Первая пара зарегистрирована: A {sg(d['oA'][i])} при {d['alA'][i]:g}°, "
                               f"B {sg(d['oB'][i])} при {d['alB'][i]:g}° (полёт {self._flight():.4g} с)"})

    def _maybe_violation_event(self):
        if self.viol_said or self.law.law != "quantum":
            return
        s = self._S(self._cells())
        if s["excess"] is not None and s["Nmin"] >= NMIN and s["excess"] > ZTOL:
            self.viol_said = True
            self._msg({"type": "event", "kind": "result", "t": self.t,
                       "text": f"Нарушение неравенства CHSH на {s['excess']:.1f}σ: S = {s['S']:.4f} ± {s['se']:.3g} "
                               f"после {self.seg_counts['detected']} пар"})

    def next_event_time(self):
        c = [self.t_next]
        nt = self.exp.next_time()
        if nt is not None:
            c.append(nt)
        return min(c)

    # --- frames ---------------------------------------------------------------------------------------
    def frame(self):
        P = self.params
        cells = self._cells()
        st = {"settings": {"a": P["a_deg"], "a2": P["a2_deg"], "b": P["b_deg"], "b2": P["b2_deg"],
                           "switch": P["switch"], "L": P["L_m"], "tau": self._tau(), "rate": P["rate"]},
              "flight": self._flight(),
              "counts": {**self.counts, "in_flight": self.exp.n_flight, "seg": self.seg,
                         "seg_detected": self.seg_counts["detected"], "loc": self.seg_counts["loc"],
                         "free": self.seg_counts["free"]},
              "cells": cells, "S": self._S(cells), "S_law": self._S_law}
        return st, {"flight": self.exp.in_flight(120), "pts": self._points()}

    def header(self):
        law = self.law
        d, q, h = law.curves()
        P = self.params
        return {
            "title": "Тест Белла: " + law.describe(),
            "text": ("Источник в центре выпускает пары по одной (пуассоновский поток); частицы летят к станциям Алисы "
                     "(−L) и Боба (+L). У каждой станции две настройки анализатора; в режиме случайного выбора бит "
                     "генератора станции выбирает настройку за τ до прихода частицы. Исход (+ или −) каждой частицы "
                     "вычисляется и показывается в момент её прихода: по правилу Борна для запутанного состояния или по "
                     "модели локальных скрытых параметров. Статистика — счёты совпадений этого запуска; ожидания закона "
                     "и границы 2 и 2√2 — в «Проверках». Кривая ЛСП на графике E(Δ) в квантовом мире — только для "
                     "сравнения (lfphys.theories.alternatives.local_hidden)."),
            "pair": P["pair"], "pair_label": PAIR_LABEL[P["pair"]], "law": law.law, "model": law.model,
            "model_label": MODEL_LABEL.get(law.model), "v": self.v, "c": C, "period": law.period,
            "modifications": SCHEMA.modifications(P), "actions": self._actions(),
        }, {"cd": d, "cq": q, "ch": h}


def _reversal_by_boosts(e1, e2):
    """beta at which t2' - t1' = 0 in a frame moving along +x, found by bisection on the 3x3 Lorentz matrices of
    lfphys.core.relativity (an independent route to the closed form c^2 dt / dx). The matrix acts on the separation
    e2 - e1 (the transformation is linear): boosting the two events apart and subtracting cancelled terms of the size
    of c t ~ L and lost ~eps L / (c tau) of the root — 1.2e-8 at tau = 1 ps, L = 1e5 m, beyond the 1e-9 tolerance
    (review UX-params P21)."""
    d = np.array([C * (e2[0] - e1[0]), e2[1] - e1[1], 0.0])

    def dt_prime(beta):
        M = R.boost_matrix(np.array([beta * C, 0.0]), C)
        return (M @ d)[0] / C
    lo, hi = 0.0, 1.0 - 1e-15
    s0 = math.copysign(1.0, dt_prime(lo))
    if math.copysign(1.0, dt_prime(hi)) == s0:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if math.copysign(1.0, dt_prime(mid)) == s0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=0.0)
    return a == b


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


VIZ = {
    "id": "v07_bell_test",
    "title": "Тест Белла: запутанные пары",
    "summary": ("Пары фотонов |Φ+⟩ или спинов ½ в синглете летят к двум станциям; у каждой — две настройки, выбор "
                "фиксированный или случайный перед приходом частицы (вне светового конуса другой стороны). Счёты "
                "совпадений, корреляции E, параметр CHSH S против границ 2 и 2√2, кривая E(Δ), отсутствие сигнала."),
    "purpose": ("Исследование нелокальных корреляций и условий опыта без лазеек; закон можно намеренно заменить "
                "локальными скрытыми параметрами и увидеть, что |S| не превышает 2."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
