# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v13: the hydrogen atom in 3-D — orbital clouds (a wrapper over lfphys; plan P14.5).

The exact bound states of a hydrogen-like atom (lfphys.core.quantum.hydrogen: R_nl by the log-scaled Laguerre
recurrence; lfphys.core.quantum.central3d: Y_lm, real orbitals, superpositions, the probability current), with the
reduced mass of the electron and the nucleus (hydrogen, deuterium, He+, positronium). The scene: the nucleus, the cloud
|psi|^2 of the relative coordinate (computed on a grid of up to 96^3 points), the probability current (rings around z
for complex m != 0, none for real orbitals, a sloshing flow for a superposition), up to three slice planes computed
exactly for their plane (|psi|^2 and the phase of psi) and checked at points against an independent route (the
Laguerre power series and scipy's harmonics). A superposition of two levels oscillates at the Bohr frequency: its
phases are revealed as the world's time reaches them (lfviz.orbitals3d). Lengths in angstroms, time in seconds.

The state is live (review UX-ui U12): changing it prepares the new state at the current moment (an ideal preparation:
the former state is discarded; lfviz.orbitals3d ``_prepare``); a new cloud grid resamples the same state. The atom is a
world parameter: no operation turns one atom into another while keeping its electron's state.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import constants as sc

from lfphys.core.quantum import central3d as C
from lfphys.core.quantum import hydrogen as H
from lfviz.orbitals3d import OrbitalWorld
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.params import _num as num_ru  # «2,5·10⁻¹⁶»: numbers in the owner's texts

from .engine import atoms as A

N_MAX = 12


def _p(*a, **k):
    return Param(*a, **k)


SUPER = {"mode": ["super"]}
PREP = ("Меняется на ходу: новое состояние приготовлено в текущий момент (идеальная подготовка; прежнее отброшено), "
        "мир, время и срезы остаются")
SCHEMA = Schema([
    _p("atom", "Атом", "select", "H", group="Атом", options=[(k, v[0]) for k, v in A.ATOMS.items()],
       help="Ядро задаёт мир: другое ядро — новый мир (никакая операция не превращает один атом в другой с тем же "
            "состоянием электрона)"),
    _p("mode", "Состояние", "select", "single", group="Состояние", live=True, help=PREP,
       options=[("single", "одно стационарное состояние"), ("super", "суперпозиция двух состояний")]),
    _p("n", "n (главное число)", "int", 2, group="Состояние", min=1, max=N_MAX, live=True, help=PREP),
    _p("l", "l (орбитальное, 0 ≤ l < n)", "int", 1, group="Состояние", min=0, max=N_MAX - 1, live=True, help=PREP),
    _p("m", "m (магнитное, |m| ≤ l)", "int", 0, group="Состояние", min=-(N_MAX - 1), max=N_MAX - 1, live=True,
       help=PREP),
    _p("real", "Вещественная орбиталь (p_x, d_xy, …) вместо комплексной с e^{imφ}", "bool", True, group="Состояние",
       live=True,
       help="Вещественные орбитали — суммы m и −m: стоячие волны без тока. Комплексные — с определённым m: ток "
            "вероятности кольцами вокруг оси z. " + PREP),
    _p("n2", "Второе состояние: n", "int", 1, group="Суперпозиция", min=1, max=N_MAX, show_if=SUPER, live=True,
       help="По умолчанию 1s: «Суперпозиция» с первым состоянием по умолчанию (2p_z) — облако, качающееся с частотой "
            "перехода 2p → 1s. " + PREP),
    _p("l2", "Второе состояние: l", "int", 0, group="Суперпозиция", min=0, max=N_MAX - 1, show_if=SUPER, live=True,
       help=PREP),
    _p("m2", "Второе состояние: m", "int", 0, group="Суперпозиция", min=-(N_MAX - 1), max=N_MAX - 1,
       show_if=SUPER, live=True, help=PREP),
    _p("real2", "Второе состояние вещественное", "bool", True, group="Суперпозиция", show_if=SUPER, live=True,
       help=PREP),
    _p("w2", "Доля второго состояния |c₂|²", "float", 0.5, group="Суперпозиция", min=0.01, max=0.99,
       show_if=SUPER, live=True, help=PREP),
    _p("phase2", "Фаза c₂ относительно c₁, °", "float", 0.0, group="Суперпозиция", min=-180.0, max=180.0,
       show_if=SUPER, live=True, help=PREP),
    _p("ng", "Сетка облака, точек на ось", "select", 96, group="Сетка облака", options=[(64, "64"), (96, "96")],
       live=True, help="Меняется на ходу: облако пересчитывается на новой сетке; состояние и его время те же"),
], presets={
    "1s": {"label": "1s: основное состояние водорода", "params": {"n": 1, "l": 0, "m": 0}},
    "2pz": {"label": "2p_z: гантель вдоль z, узловая плоскость z = 0", "params": {"n": 2, "l": 1, "m": 0}},
    "3dz2": {"label": "3d_z²: лепестки вдоль z и кольцо", "params": {"n": 3, "l": 2, "m": 0}},
    "2px_real": {"label": "2p_x вещественная: стоячая волна, тока нет",
                 "params": {"n": 2, "l": 1, "m": 1, "real": True}},
    "2p_m1": {"label": "2p, m = +1 комплексная: бублик и кольцевой ток",
              "params": {"n": 2, "l": 1, "m": 1, "real": False}},
    "3d_m2": {"label": "3d, m = +2 комплексная: ток кольцами вокруг z",
              "params": {"n": 3, "l": 2, "m": 2, "real": False}},
    "super_1s2p": {"label": "1s + 2p_z: облако качается вдоль z с частотой Бора (суперпозиция)",
                   "params": {"mode": "super", "n": 1, "l": 0, "m": 0, "n2": 2, "l2": 1, "m2": 0, "ng": 64}},
    "px_ipy": {"label": "2p_x + i·2p_y: это 2p с m = +1 (суперпозиция одной энергии, стационарна)",
               "params": {"mode": "super", "n": 2, "l": 1, "m": 1, "real": True, "n2": 2, "l2": 1, "m2": -1,
                          "real2": True, "phase2": 90.0, "ng": 64}},
    "n10": {"label": "n = 10, l = 3, m = 1: большое облако, 6 радиальных узлов",
            "params": {"n": 10, "l": 3, "m": 1, "real": True}},
    "he_3dxy": {"label": "Ион He⁺, 3d_xy: облако в Z = 2 раза меньше", "params": {"atom": "He+", "n": 3, "l": 2,
                                                                                    "m": -2, "real": True}},
})


def _spec(p, suffix=""):
    n, l, m = int(p["n" + suffix]), int(p["l" + suffix]), int(p["m" + suffix])
    if not (1 <= n <= N_MAX):
        raise ValueError(f"n{suffix} от 1 до {N_MAX}")
    if not (0 <= l < n):
        raise ValueError(f"нужно 0 ≤ l < n (n = {n}, l = {l})")
    if abs(m) > l:
        raise ValueError(f"нужно |m| ≤ l (l = {l}, m = {m})")
    return n, l, m, bool(p["real" + suffix])


def _fit_numbers(p, suffix=""):
    """Review UX-params P10 (owner, 2026-11-04: a choice the form offers must work): the form cannot bound l by n and
    m by l, so the world takes the nearest allowed numbers — n first, then 0 ≤ l < n, then |m| ≤ l — changes ``p`` in
    place (the header's parameters are the state shown) and says what it changed and how to get what was asked."""
    n, l, m = int(p["n" + suffix]), int(p["l" + suffix]), int(p["m" + suffix])
    who = "второго состояния: " if suffix else ""
    out = []
    if l > n - 1:
        out.append(f"l{suffix} = {l} при n{suffix} = {n} невозможно (0 ≤ l < n) — взято l{suffix} = {n - 1}; для "
                   f"l = {l} выберите n ≥ {l + 1}")
        l = n - 1
    if abs(m) > l:
        m_new = l if m > 0 else -l
        out.append(f"|m{suffix}| = {abs(m)} больше l{suffix} = {l} — взято m{suffix} = {m_new}; для |m| = {abs(m)} "
                   f"нужны l ≥ {abs(m)} и n ≥ {abs(m) + 1}")
        m = m_new
    p["l" + suffix], p["m" + suffix] = l, m
    return [f"Квантовые числа {who}{t}." for t in out]


def _fit_second(p):
    """The second state left at its defaults but equal to the first (a first state of 1s with the default second 1s):
    the world takes another one, 2p_z for 1s and 1s otherwise, and says so (P10). A second state chosen equal to the
    first by hand is refused."""
    d = SCHEMA.defaults()
    if p["mode"] != "super" or any(p[k] != d[k] for k in ("n2", "l2", "m2", "real2")):
        return []
    if (int(p["n"]), int(p["l"]), int(p["m"]), bool(p["real"])) != (int(p["n2"]), int(p["l2"]), int(p["m2"]),
                                                                       bool(p["real2"])):
        return []
    if int(p["n"]) == 1:
        p.update(n2=2, l2=1, m2=0)
        return ["Второе состояние по умолчанию (1s) совпало с первым — взято 2p_z: облако качается с частотой "
                "перехода 2p → 1s."]
    p.update(n2=1, l2=0, m2=0)
    return ["Второе состояние совпало с первым — взято 1s."]


def _ng_as_number(values):
    """The player sends a select's value as text («64»); the cloud grid's options are numbers (64, 96)."""
    v = dict(values)
    if isinstance(v.get("ng"), str) and v["ng"].strip().isdigit():
        v["ng"] = int(v["ng"])
    return v


class Simulation(OrbitalWorld):
    group = "Атом водорода"

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        for text in self._set_state(self.params):
            self._msg({"type": "notice", "t": 0.0, "text": text})
        self._build()
        self._checks()

    def _set_state(self, p):
        """The state of the parameters ``p`` (quantum numbers fitted in place, said in the returned notices): the
        world's state attributes before ``_build``. Raises (nothing of the world changed) when it cannot be made."""
        fitted = _fit_numbers(p) + (_fit_numbers(p, "2") if p["mode"] == "super" else []) + _fit_second(p)
        self.u = A.units(p["atom"])
        self.Z = self.u["Z"]
        specs = [_spec(p)]
        coefs = [1.0]
        if p["mode"] == "super":
            specs.append(_spec(p, "2"))
            if specs[1] == specs[0]:
                raise Refusal("второе состояние совпадает с первым: суперпозиции нет",
                              "выберите другое n, l или m второго состояния (группа «Суперпозиция»)")
            w2 = float(p["w2"])
            coefs = [math.sqrt(1 - w2), math.sqrt(w2) * np.exp(1j * math.radians(float(p["phase2"])))]
        orbs = [H.orbital(n, l, m, Z=self.Z, real=real) for n, l, m, real in specs]
        if len(specs) == 2 and specs[0][:2] == specs[1][:2]:  # same n, l: the angular parts must be orthogonal
            T, P, W = C.angular_quadrature(specs[0][1])
            ov = abs(np.sum(W * np.conj(orbs[0].angular(T, P)) * orbs[1].angular(T, P)))
            if ov > 1e-12:
                raise Refusal(f"состояния {orbs[0].label} и {orbs[1].label} не ортогональны (перекрытие {ov:.3f}): одно "
                              "выражается через другое", "выберите другое m или вид орбитали (вещественная / "
                              "комплексная) второго состояния")
        self.specs = specs
        self.state = C.Superposition(orbs, coefs)
        self.Lu, self.units, self.tu = self.u["Lu"], "Å", self.u["tu"]
        nmax = max(s[0] for s in specs)
        self.r_max = (2.0 * nmax * nmax + 40.0 * nmax) / self.Z
        self.ng = int(p["ng"])
        self.rb_state = min(H.expectation(n, l, 1, self.Z) for n, l, _, _ in specs)
        self.scale_min = 1.0 / self.Z  # psi varies on a / Z at the nucleus (the cusp of s states)
        return fitted

    # --- live: the state is prepared at the current moment (review UX-ui U12) -------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        values = _ng_as_number(values)
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

    # --- the independent route -------------------------------------------------------------------------------------
    verify_note = "эталон: R_nl степенным рядом (точные коэффициенты), Y_lm — scipy; допуск — оценки их округления"

    def _reference(self, x, y, z, t):
        return A.reference(self.specs, self.state.c, self.Z, x, y, z, t)

    def _dipole_ref(self):
        (n1, l1, m1, r1), (n2, l2, m2, r2) = self.specs
        D, how = super()._dipole_ref()
        if {(n1, l1), (n2, l2)} == {(1, 0), (2, 1)} and m1 == m2 == 0 and self.Z == 1:
            return np.array([0.0, 0.0, H.DIPOLE_1S_2P0]), "⟨1s|z|2p₀⟩ = 2⁷√2/3⁵ a (Бете и Солпитер)"
        return D, how

    # --- checks of the states (closed forms of the exact solution) ------------------------------------------------------
    def _checks(self):
        eV, Lu = self.u["eV"], self.Lu
        for k, (o, (n, l, m, real)) in enumerate(zip(self.state.orbitals, self.specs)):
            tag = f" ({o.label})" if len(self.specs) > 1 else ""
            norm = C.moment(o.R, 0, self.r_max)
            n2 = C.moment(o.R, 0, self.r_max, panels=800)
            self._check(f"norm_{k}", f"Нормировка ∫|ψ|²dV{tag}: квадратура", norm, 1.0, tol=1e-12 + 10 * abs(norm - n2),
                        note="радиальные панели Гаусса–Лежандра (угловая часть нормирована точно); допуск — "
                             "1e-12 + 10 × разность при удвоенном числе панелей")
            rm = C.moment(o.R, 1, self.r_max)
            self._check(f"r_{k}", f"Средний радиус ⟨r⟩{tag}", rm * Lu, H.expectation(n, l, 1, self.Z) * Lu, "Å",
                        tol=1e-10, note="квадратура |ψ|² против a/(2Z)·[3n² − l(l+1)]")
            Tk, Vk = C.energy_terms(o.R, C.derivative_fd(o.R, n / self.Z), l, lambda r: -self.Z / r, self.r_max)
            self._check(f"energy_{k}", f"Энергия ⟨T⟩ + ⟨V⟩ по волновой функции{tag}", (Tk + Vk) * eV, o.energy * eV,
                        "эВ", tol=1e-9,
                        note=f"⟨T⟩ = ½∫(R′²r² + l(l+1)R²)dr (R′ — разности 4-го порядка), ⟨V⟩ = −Z⟨1/r⟩; эталон "
                             f"−μc²(Zα)²/2n² с приведённой массой; вириал −⟨V⟩/⟨T⟩ = {-Vk / Tk:.12f} (точно 2)")
            r = np.linspace(1e-9, self.r_max, 400001)
            R = o.R(r)
            big = np.abs(R) > 1e-12 * np.max(np.abs(R))
            sgn = np.sign(R[big])
            nodes = int(np.sum(sgn[1:] != sgn[:-1]))
            self._check(f"nodes_{k}", f"Радиальные узлы{tag}: n − l − 1", nodes, n - l - 1, ok=nodes == n - l - 1,
                        note="смены знака R(r) на сетке 400 001 точек")
        inside = min(C.moment(lambda r, o=o: np.where(r <= self.rb, o.R(r), 0.0), 0, self.r_max)
                     for o in self.state.orbitals)
        self._check("box", "Доля вероятности в шаре, который вписан в куб сцены", inside, None, info=True,
                    note=f"шар радиуса {self.rb * Lu:.4g} Å выбран так, чтобы снаружи было ≤ 1e-3")

    # --- header -----------------------------------------------------------------------------------------------------------
    def engine_modules(self):
        return ["core.quantum.hydrogen", "core.quantum.central3d", "core.geometry"]

    def header(self):
        u, sp = self.u, self.state
        states = []
        for o, ck, (n, l, m, real) in zip(sp.orbitals, sp.c, self.specs):
            states.append({"label": o.label, "n": n, "l": l, "m": m, "real": real, "w": float(abs(ck) ** 2),
                           "phase_deg": math.degrees(float(np.angle(ck))), "E": o.energy * u["eV"],
                           "r_mean": H.expectation(n, l, 1, self.Z) * self.Lu,
                           "r_mean_quad": C.moment(o.R, 1, self.r_max) * self.Lu})
        nmax = max(6, max(s[0] for s in self.specs))
        lmax = max(3, max(s[1] for s in self.specs))
        letters = "spdfghik"
        levels = [{"key": f"{n},{l}", "label": f"n = {n}" if l == 0 and n <= 4 else "", "col": l,
                   "E": H.level(n, self.Z, u["mu"]) / sc.e} for l in range(lmax + 1) for n in range(l + 1, nmax + 1)]
        for st in states:
            st["key"] = f"{st['n']},{st['l']}"
        what = " + ".join(s["label"] for s in states)
        return {
            # the title names the atom (a world parameter), not the state: the state is live (review UX-ui U12)
            "title": "Атом водорода в 3D" if self.params["atom"] == "H" else f"Водородоподобный атом в 3D: {u['label']}",
            "state_label": what,
            "text": ("Облако |ψ|² — плотность вероятности найти электрон в точке относительно ядра (точное решение "
                     "уравнения Шрёдингера с приведённой массой). Стрелки — ток вероятности. Срезы — плоскости под "
                     "любым углом: |ψ|² и фаза ψ, посчитанные для плоскости и сверенные с независимым расчётом."
                     + (" Суперпозиция двух уровней: облако колеблется с частотой Бора; фазы периода открываются, "
                        "когда до них доходит время мира." if self.nb > 1 else "")),
            "actions": [],
            "scene3d": self.scene([{"id": "nucleus", "label": f"Ядро ({u['mark']}) в начале координат", "kind": "point",
                                    "pos": [0.0, 0.0, 0.0], "text": u["mark"], "color": "#ffd23f"}]),
            "units": {"x": "Å", "t": "с", "E": "эВ"},
            "atom": {"label": u["label"], "Z": self.Z, "mu_over_me": u["mu"] / sc.m_e, "a_A": self.Lu,
                     "Eh_eV": u["eV"], "tu": self.tu},
            "states": states, "levels": levels, "energy_unit": "эВ", "levels_top": 0.0,
            "level_columns": [letters[l] if l < len(letters) else f"l={l}" for l in range(lmax + 1)],
            "period": self.period if self.nb > 1 else None, "nb": self.nb,
            "omega_E": (abs(sp.orbitals[1].energy - sp.orbitals[0].energy) * u["eV"]) if self.nb > 1 else None,
            "grid": self.ng,
        }, {}


VIZ = {
    "id": "v13_hydrogen_3d",
    "title": "Атом водорода в 3D: орбитали",
    "summary": ("Точные волновые функции водородоподобного атома: облако |ψ|², ток вероятности, срезы под любым "
                "углом с фазой; вещественные и комплексные орбитали, суперпозиции с колебанием на частоте Бора."),
    "purpose": ("Увидеть форму орбиталей, узлы, разницу вещественных и комплексных состояний (стоячая волна или "
                "кольцевой ток) и движение облака в суперпозиции — всё посчитано движком и сверено с независимым "
                "расчётом."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
