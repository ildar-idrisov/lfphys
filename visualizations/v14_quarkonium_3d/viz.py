# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v14: quarkonium in 3-D — wave functions of a heavy quark pair in the Cornell model (a wrapper over lfphys; plan
P14.9).

The pair cc̄ or bb̄ bound by V(r) = -kappa/r + r/a^2 (lfphys.theories.models.cornell: a FITTED, non-relativistic,
spin-averaged model outside the core; it predicts level splittings, not absolute masses, STATUS V17). The radial
functions come from the radial solver (lfphys.core.quantum.radial.wavefunctions, measured accuracy), interpolated by
lfphys.core.quantum.central3d.RadialTable; the 3-D clouds, currents, superpositions and slices are those of
lfviz.orbitals3d, the same as v13's. The cloud is the distribution of the relative coordinate r = r_q - r_q̄ (the
centre of mass at the origin). Lengths in femtometres, energies in MeV, time in seconds.

The state is live (review UX-ui U12): changing it prepares the new state at the current moment (an ideal preparation:
the former state is discarded; lfviz.orbitals3d ``_prepare``); a new cloud grid resamples the same state. The quark
pair is a world parameter: another pair is another system (other masses, other levels).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data
from lfphys.core.quantum import central3d as C
from lfphys.theories.models import cornell
from lfviz.orbitals3d import OrbitalWorld
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.params import _num as num_ru  # «2,5·10⁻¹⁶»: numbers in the owner's texts

from .engine import pair as Q

LETTERS = "SPD"
DISPLAY_RESOLUTION = 1.0 / (2 * 255)  # half a step of the 8-bit picture (cloud texture, slice colour map)


def _p(*a, **k):
    return Param(*a, **k)


SUPER = {"mode": ["super"]}
PREP = ("Меняется на ходу: новое состояние приготовлено в текущий момент (идеальная подготовка; прежнее отброшено), "
        "мир, время и срезы остаются")
SCHEMA = Schema([
    _p("system", "Пара кварков", "select", "charm", group="Система",
       options=[(k, f"{v[0]} (m = {Q.mass(k):g} ГэВ, модель)") for k, v in Q.SYSTEMS.items()],
       help="Пара задаёт мир (массы кварков, уровни): другая пара — новый мир"),
    _p("mode", "Состояние", "select", "single", group="Состояние", live=True, help=PREP,
       options=[("single", "одно стационарное состояние"), ("super", "суперпозиция двух состояний")]),
    _p("n", "n (радиальное: 1S, 2S, …)", "int", 1, group="Состояние", min=1, max=3, live=True, help=PREP),
    _p("l", "L (0 — S, 1 — P, 2 — D)", "int", 0, group="Состояние", min=0, max=2, live=True, help=PREP),
    _p("m", "m (|m| ≤ L)", "int", 0, group="Состояние", min=-2, max=2, live=True, help=PREP),
    _p("real", "Вещественная угловая часть (p_z, d_z², …) вместо e^{imφ}", "bool", True, group="Состояние", live=True,
       help=PREP),
    _p("n2", "Второе состояние: n", "int", 1, group="Суперпозиция", min=1, max=3, show_if=SUPER, live=True, help=PREP),
    _p("l2", "Второе состояние: L", "int", 1, group="Суперпозиция", min=0, max=2, show_if=SUPER, live=True, help=PREP),
    _p("m2", "Второе состояние: m", "int", 0, group="Суперпозиция", min=-2, max=2, show_if=SUPER, live=True, help=PREP),
    _p("real2", "Второе состояние вещественное", "bool", True, group="Суперпозиция", show_if=SUPER, live=True,
       help=PREP),
    _p("w2", "Доля второго состояния |c₂|²", "float", 0.5, group="Суперпозиция", min=0.01, max=0.99, show_if=SUPER,
       live=True, help=PREP),
    _p("phase2", "Фаза c₂ относительно c₁, °", "float", 0.0, group="Суперпозиция", min=-180.0, max=180.0,
       show_if=SUPER, live=True, help=PREP),
    _p("ng", "Сетка облака, точек на ось", "select", 96, group="Сетка облака", options=[(64, "64"), (96, "96")],
       live=True, help="Меняется на ходу: облако пересчитывается на новой сетке; состояние и его время те же"),
], presets={
    "cc_1S": {"label": "cc̄ 1S (J/ψ, η_c без спина): облако без узлов", "params": {}},
    "cc_1P": {"label": "cc̄ 1P (χ_c, h_c), p_z", "params": {"l": 1}},
    "cc_2S": {"label": "cc̄ 2S (ψ(2S)): один радиальный узел", "params": {"n": 2}},
    "cc_1D": {"label": "cc̄ 1D, d_z²", "params": {"l": 2}},
    "cc_1P_m1": {"label": "cc̄ 1P, m = +1 комплексная: кольцевой ток", "params": {"l": 1, "m": 1, "real": False}},
    "bb_1S": {"label": "bb̄ 1S (Υ(1S)): облако теснее, кварки тяжелее", "params": {"system": "bottom"}},
    "bb_1P": {"label": "bb̄ 1P (χ_b), p_z", "params": {"system": "bottom", "l": 1}},
    "bb_2S": {"label": "bb̄ 2S (Υ(2S))", "params": {"system": "bottom", "n": 2}},
    "bb_1D": {"label": "bb̄ 1D, d_z²", "params": {"system": "bottom", "l": 2}},
    "cc_super": {"label": "cc̄ 1S + 1P_z: пара качается с частотой перехода (суперпозиция)",
                 "params": {"mode": "super", "n2": 1, "l2": 1, "m2": 0, "ng": 64}},
})


def _spec(p, suffix=""):
    n, l, m = int(p["n" + suffix]), int(p["l" + suffix]), int(p["m" + suffix])
    if not (1 <= n <= 3 and 0 <= l <= 2):
        raise ValueError("n от 1 до 3, L от 0 до 2")
    if abs(m) > l:
        raise ValueError(f"нужно |m| ≤ L (L = {l}, m = {m})")
    return n, l, m, bool(p["real" + suffix])


def _fit_numbers(p, suffix=""):
    """Review UX-params P10: the form cannot bound m by L, so the world takes the nearest allowed m (|m| ≤ L), changes
    ``p`` in place (the header's parameters are the state shown) and says so."""
    l, m = int(p["l" + suffix]), int(p["m" + suffix])
    if abs(m) <= l:
        return []
    m_new = l if m > 0 else -l
    p["m" + suffix] = m_new
    who = "второго состояния: " if suffix else ""
    return [f"Квантовые числа {who}|m{suffix}| = {abs(m)} больше L{suffix} = {l} — взято m{suffix} = {m_new}; для "
            f"|m| = {abs(m)} выберите L ≥ {abs(m)}."]


def _fit_second(p):
    """The second state left at its defaults (1P_z) but equal to the first: the world takes 1S and says so (P10); a
    second state chosen equal to the first by hand is refused."""
    d = SCHEMA.defaults()
    if p["mode"] != "super" or any(p[k] != d[k] for k in ("n2", "l2", "m2", "real2")):
        return []
    if (int(p["n"]), int(p["l"]), int(p["m"]), bool(p["real"])) != (int(p["n2"]), int(p["l2"]), int(p["m2"]),
                                                                       bool(p["real2"])):
        return []
    p.update(n2=1, l2=0, m2=0)
    return ["Второе состояние по умолчанию (1P_z) совпало с первым — взято 1S."]


def _label(n, l, m, real):
    name = C.orbital_name(l, m, real)
    return f"{n}{LETTERS[l]}" + ("" if l == 0 else (name[1:] if real else f", m = {m:+d}"))


class Simulation(OrbitalWorld):
    group = "Кварконий (модель)"

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        for text in self._set_state(self.params):
            self._msg({"type": "notice", "t": 0.0, "text": text})
        self._build()
        self._levels()
        self._checks()

    def _set_state(self, p):
        """The state of the parameters ``p`` (m fitted in place, said in the returned notices): the world's state
        attributes before ``_build``. Raises (nothing of the world changed) when it cannot be made."""
        fitted = _fit_numbers(p) + (_fit_numbers(p, "2") if p["mode"] == "super" else []) + _fit_second(p)
        self.system = p["system"]
        self.mq = Q.mass(self.system)
        specs = [_spec(p)]
        coefs = [1.0]
        if p["mode"] == "super":
            specs.append(_spec(p, "2"))
            if specs[1] == specs[0]:
                raise Refusal("второе состояние совпадает с первым: суперпозиции нет",
                              "выберите другое n, L или m второго состояния (группа «Суперпозиция»)")
            w2 = float(p["w2"])
            coefs = [math.sqrt(1 - w2), math.sqrt(w2) * np.exp(1j * math.radians(float(p["phase2"])))]
        tabs = Q.tables(self.system, specs)
        orbs = [C.Orbital(tb["R"], l, m, real, tb["E"], _label(n, l, m, real))
                for tb, (n, l, m, real) in zip(tabs, specs)]
        if len(specs) == 2 and specs[0][:2] == specs[1][:2]:
            T, P, W = C.angular_quadrature(specs[0][1])
            ov = abs(np.sum(W * np.conj(orbs[0].angular(T, P)) * orbs[1].angular(T, P)))
            if ov > 1e-12:
                raise Refusal(f"состояния {orbs[0].label} и {orbs[1].label} не ортогональны (перекрытие {ov:.3f}): "
                              "одно выражается через другое", "выберите другое m или вид угловой части "
                              "(вещественная / комплексная) второго состояния")
        self.specs, self.tabs = specs, tabs
        self.state = C.Superposition(orbs, coefs)
        self.mu, self.hbar = 0.5 * self.mq, 1.0
        self.Lu, self.units, self.tu = Q.HBARC_GEV_FM, "фм", Q.HBAR_GEV_S
        self.r_max = max(tb["R_box"] for tb in self.tabs)
        self.ng = int(p["ng"])
        self.rb_state = min(C.moment(o.R, 1, self.r_max) for o in orbs)
        self.scale_min = 1.0 / (self.mu * cornell.PARAMS["kappa"])  # the Bohr radius of the Coulomb part
        self.ref_tabs = Q.tables(self.system, specs, Q.N_REF)
        return fitted

    # --- live: the state is prepared at the current moment (review UX-ui U12) -------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        values = dict(values)
        if isinstance(values.get("ng"), str) and values["ng"].strip().isdigit():  # a select's value comes as text
            values["ng"] = int(values["ng"])
        new, errors = SCHEMA.coerce_live(self.live_values(), values)
        if errors:
            raise ValueError("; ".join(errors))
        changed = [k for k in values if new[k] != self.params[k]]
        if not changed:
            return "без изменений"
        p = {**self.params, **new}
        grid_only = set(changed) == {"ng"}
        notices = []

        def build():
            notices.extend(self._set_state(p))
            self.params = p
        was = " + ".join(o.label for o in self.state.orbitals)
        self._prepare(build, keep_time=grid_only, notices=notices)
        if grid_only:
            return f"сетка облака: {self.ng} точек на ось — облако пересчитано; состояние и его время те же"
        now = " + ".join(o.label for o in self.state.orbitals)
        return (f"приготовлено состояние {now} в t = {num_ru(float(f'{self.t:.6g}'))} с (было {was}; прежнее отброшено — "
                f"идеальная подготовка){'; ' + ' '.join(notices) if notices else ''}")

    # --- the independent route ------------------------------------------------------------------------------------------
    verify_note = ("эталон: радиальная функция из второго решения на более мелкой сетке, Y_lm — scipy; допуск — 3 × "
                   "расхождение двух радиальных решений (их точность — проверка «сходимость») и округление гармоник")

    def _reference(self, x, y, z, t):
        return Q.reference(self.system, self.specs, self.state.c, x, y, z, t, self.ref_tabs, self.tabs)

    # --- levels of the model (splittings) and the data ------------------------------------------------------------------
    def _levels(self):
        table = data.CHARMONIUM if self.system == "charm" else data.BOTTOMONIUM
        self.levels = []
        E = {}
        for L in range(3):
            EL = Q.solve(self.system, L)[0]
            for n in range(1, 4):
                E[(n, L)] = float(EL[n - 1])
        self.E1S = E[(1, 0)]
        m1s, _ = data.spin_averaged(table, 0, 1)
        for (n, L), e in E.items():
            meas, used = data.spin_averaged(table, L, n)
            self.levels.append({"key": f"{n},{L}", "label": f"{n}{LETTERS[L]}", "col": L, "E": (e - self.E1S) * 1e3,
                                "data": (meas - m1s) if meas else None, "used": used})

    # --- checks -------------------------------------------------------------------------------------------------------------
    def _checks(self):
        P = cornell.PARAMS
        V = cornell.potential(P["kappa"], P["a"])
        rr = np.linspace(0.0, self.r_max, 20001)
        for k, (o, tb, tr, (n, l, m, real)) in enumerate(zip(self.state.orbitals, self.tabs, self.ref_tabs,
                                                               self.specs)):
            tag = f" ({o.label})" if len(self.specs) > 1 else ""
            norm = C.moment(o.R, 0, self.r_max)
            self._check(f"norm_{k}", f"Нормировка ∫|ψ|²dV{tag}: квадратура сплайна", norm, 1.0, tol=max(tb["est"], 1e-9),
                        note="радиальная функция нормирована на сетке решателя; допуск — оценка его ошибки "
                             "(разность сеток N и 2N + 1)")
            Rn, Rr = o.R(rr), tr["R"](rr)
            conv = float(np.max(np.abs(Rn - Rr)) / np.max(np.abs(Rr)))
            self._check(f"conv_{k}", f"Сходимость{tag}: R(r) сетки N = {Q.N_GRID} против N = {Q.N_REF}", conv, 0.0,
                        tol=DISPLAY_RESOLUTION, ok=conv <= DISPLAY_RESOLUTION,
                        note="доля max|R|; допуск — полшага 8-битной картинки (облако и окна срезов): разница "
                             "решений должна быть не видна")
            Tk, Vk = C.energy_terms(o.R, o.R.derivative, l, V, self.r_max, self.mu)
            Tr, Vr = C.energy_terms(tr["R"], tr["R"].derivative, l, V, self.r_max, self.mu)
            tol = 3 * (abs((Tk + Vk) - (Tr + Vr)) + abs(tb["E"] - tr["E"])) + 1e-12
            self._check(f"energy_{k}", f"Энергия ⟨T⟩ + ⟨V⟩ по волновой функции{tag} против собственного значения",
                        (Tk + Vk) * 1e3, tb["E"] * 1e3, "МэВ", tol=tol / abs(tb["E"]),
                        ok=abs(Tk + Vk - tb["E"]) <= tol,
                        note="⟨T⟩ = ∫(R′²r² + L(L+1)R²)dr/2μ по сплайну, ⟨V⟩ = ∫V R² r² dr; эталон — уровень решателя "
                             "(Ричардсон); допуск — 3 × (изменение обоих при N → N_ref)")
            r = np.linspace(1e-9, tb["R_box"], 200001)
            Rv = o.R(r)
            big = np.abs(Rv) > 1e-9 * np.max(np.abs(Rv))
            s = np.sign(Rv[big])
            nodes = int(np.sum(s[1:] != s[:-1]))
            self._check(f"nodes_{k}", f"Радиальные узлы{tag}: n − 1", nodes, n - 1, ok=nodes == n - 1,
                        note="смены знака R(r) (решатель не знает о n: номер состояния — по порядку уровней)")
            lev = next(v for v in self.levels if v["key"] == f"{n},{l}")
            if n == 1 and l == 0:
                continue
            if lev["data"] is not None:
                self._check(f"split_{k}", f"Расщепление M({o.label[:2]}) − M(1S): модель против опыта (PDG)",
                            lev["E"], lev["data"], "МэВ", info=True,
                            note=f"модель Корнелла с подогнанными параметрами (κ = {P['kappa']}, a = {P['a']} ГэВ⁻¹, "
                                 f"m = {self.mq} ГэВ); опыт — спин-усреднённые массы ({', '.join(lev['used'])}); "
                                 f"абсолютные массы модель не предсказывает (STATUS V17)")
        inside = min(C.moment(lambda r, o=o: np.where(r <= self.rb, o.R(r), 0.0), 0, self.r_max)
                     for o in self.state.orbitals)
        self._check("box", "Доля вероятности в шаре, который вписан в куб сцены", inside, None, info=True,
                    note=f"шар радиуса {self.rb * self.Lu:.4g} фм выбран так, чтобы снаружи было ≤ 1e-3")

    # --- header -----------------------------------------------------------------------------------------------------------
    def engine_modules(self):
        return ["theories.models.cornell", "core.quantum.radial", "core.quantum.central3d", "core.data", "core.geometry"]

    def header(self):
        sp = self.state
        states = []
        for o, ck, tb, (n, l, m, real) in zip(sp.orbitals, sp.c, self.tabs, self.specs):
            rms = math.sqrt(C.moment(o.R, 2, self.r_max)) * self.Lu
            states.append({"label": o.label, "key": f"{n},{l}", "n": n, "l": l, "m": m, "real": real,
                           "w": float(abs(ck) ** 2), "phase_deg": math.degrees(float(np.angle(ck))),
                           "E": (tb["E"] - self.E1S) * 1e3, "r_mean": None,
                           "r_mean_quad": C.moment(o.R, 1, self.r_max) * self.Lu,
                           "extra": [["энергия в потенциале E", tb["E"] * 1e3, "МэВ"], ["√⟨r²⟩", rms, "фм"]]})
        name = Q.SYSTEMS[self.system][0]
        what = " + ".join(s["label"] for s in states)
        P = cornell.PARAMS
        return {
            # the title names the pair (a world parameter), not the state: the state is live (review UX-ui U12)
            "title": f"Кварконий в 3D: {name}",
            "state_label": what,
            "text": ("Облако |ψ|² — плотность вероятности для вектора r между кварком и антикварком (центр масс в "
                     "начале координат) в модели Корнелла V(r) = −κ/r + r/a² (подогнанная модель: предсказывает "
                     "расщепления уровней, не абсолютные массы). Радиальные функции — численное решение, его точность "
                     "измерена; стрелки — ток вероятности; срезы — плоскости под любым углом с |ψ|² и фазой."),
            "actions": [],
            "approximations": ["модель Корнелла (подогнанные κ, a, m_q): нерелятивистская, без спиновых сил и связи с "
                               "открытыми каналами; предсказывает расщепления уровней, не абсолютные массы"],
            "scene3d": self.scene([{"id": "cm", "label": "Центр масс пары (облако — расстояние r = r_q − r_q̄)",
                                    "kind": "point", "pos": [0.0, 0.0, 0.0], "text": f"{Q.SYSTEMS[self.system][2]}"
                                                                                     f"{Q.SYSTEMS[self.system][2]}̄",
                                    "color": "#ffd23f"}]),
            "units": {"x": "фм", "t": "с", "E": "МэВ"},
            "system": {"label": name, "m_q": self.mq, "kappa": P["kappa"], "a": P["a"], "mu": self.mu},
            "states": states, "levels": self.levels, "energy_unit": "МэВ", "level_columns": ["S", "P", "D"],
            "period": self.period if self.nb > 1 else None, "nb": self.nb,
            "omega_E": abs(sp.orbitals[1].energy - sp.orbitals[0].energy) * 1e3 if self.nb > 1 else None,
            "grid": self.ng,
        }, {}


VIZ = {
    "id": "v14_quarkonium_3d",
    "title": "Кварконий в 3D: волновые функции",
    "summary": ("Пара тяжёлых кварков cc̄ или bb̄ в модели Корнелла: облако |ψ|², ток вероятности, срезы с фазой, "
                "суперпозиции; расщепления уровней модели против опыта."),
    "purpose": ("Увидеть, как устроены состояния 1S, 1P, 2S, 1D кваркония и чем отличаются чармоний и боттомоний; "
                "модель подогнана и помечена как модель, точность численного решения измерена."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
