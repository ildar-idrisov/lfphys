# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v03: a quantum particle in one dimension (a wrapper over lfphys).

Electrons are sent one by one as wave packets at a potential (barrier, double barrier, step, well) or released in a
harmonic trap. The wave of every particle is the numerical solution of the Schroedinger equation on a grid
(split-operator, lfphys.core.quantum.schrodinger1d, converged as stated in the README); detectors at both ends absorb
the wave (a complex absorbing potential, the detector model, chosen per set-up so that it reflects and leaks below
stated limits) and the run computes how much probability each detector absorbs, and when. The outcome of each
particle is then produced in the reading the owner chooses (live), with the same statistics in all three (checked):

* Copenhagen (lfphys.theories.interpretations.copenhagen): the click happens at a random moment with the absorption
  rate of that detector; the wave collapses onto the detector;
* de Broglie-Bohm (lfphys.theories.interpretations.bohm): the particle starts at a position drawn from |psi|^2 and
  follows the guidance velocity j/|psi|^2; the detector its path reaches clicks;
* Everett (lfphys.theories.interpretations.everett): both detectors click, each in its branch with weight P; the
  observer finds himself in one branch with that weight.

References computed independently by the run: the exact transmission of the stationary problem
(lfphys.core.quantum.transfer) averaged over the packet's momentum distribution, harmonic levels hbar omega (n + 1/2).
Units: nm, eV, fs.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import constants as sc

from lfphys.core.quantum import schrodinger1d as S1
from lfphys.core.quantum import transfer
from lfphys.theories.interpretations import bohm
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

HBAR = sc.hbar / sc.e * 1e15  # eV fs
FS = 1e-15  # the world's time is in seconds (the player's unit); the physics runs in fs
M_E = sc.m_e


def mass_ev(kg):  # eV fs^2 / nm^2
    return kg * 1e12 / sc.e


def _p(*a, **k):
    return Param(*a, **k)


SCEN = [("barrier", "прямоугольный барьер"), ("double", "двойной барьер (резонансное туннелирование)"),
        ("step", "ступенька потенциала"), ("well", "потенциальная яма"), ("oscillator", "гармоническая ловушка"),
        ("free", "свободная частица")]
INTERP = [("copenhagen", "копенгагенская: щелчок и коллапс"), ("bohm", "де Бройль–Бом: траектория"),
          ("everett", "Эверетт: ветвление")]
PIECEWISE = ("barrier", "double", "step", "well", "free")

SCHEMA = Schema([
    _p("energy", "Энергия пакета, эВ", "float", 0.8, group="Частица (электрон)", min=0.05, max=20.0, log=True,
       live=True,
       help="энергия центральной компоненты пакета ħ²k₀²/2m (средняя кинетическая больше на ħ²/(8mσ²))"),
    _p("sigma", "Ширина пакета σ, нм", "float", 4.0, group="Частица (электрон)", min=1.0, max=15.0, live=True,
       help="разброс положения |ψ|²; разброс импульса ħ/(2σ)"),
    _p("scenario", "Потенциал", "select", "barrier", group="Потенциал", options=SCEN, live=True),
    _p("V0", "Высота V₀, эВ", "float", 1.0, group="Потенциал", min=-5.0, max=10.0, live=True,
       show_if={"scenario": ["barrier", "double", "step", "well"]}, help="для ямы — глубина (отрицательная)"),
    _p("width", "Ширина a, нм", "float", 0.6, group="Потенциал", min=0.05, max=10.0, live=True,
       show_if={"scenario": ["barrier", "double", "well"]}),
    _p("edge", "Размытие краёв δ, нм", "float", 0.1, group="Потенциал", min=0.02, max=2.0, log=True, live=True,
       show_if={"scenario": ["barrier", "double", "step", "well"]},
       help="края — профиль (1 + tanh(x/δ))/2; прямоугольник — предел δ → 0 (δ ≪ длины волны)"),
    _p("gap", "Промежуток между барьерами, нм", "float", 2.0, group="Потенциал", min=0.2, max=20.0, live=True,
       show_if={"scenario": ["double"]}),
    _p("hw", "Ловушка: ħω, эВ", "float", 0.05, group="Потенциал", min=0.001, max=1.0, log=True, live=True,
       show_if={"scenario": ["oscillator"]}),
    _p("x0", "Смещение пакета в ловушке, нм", "float", 15.0, group="Потенциал", min=0.0, max=60.0, live=True,
       show_if={"scenario": ["oscillator"]}),
    _p("interp", "Интерпретация (не меняет предсказаний)", "select", "copenhagen", group="Чтение исхода",
       options=INTERP, live=True),
    _p("n_bohm", "Траекторий Бома в ансамбле", "int", 60, group="Чтение исхода", min=0, max=200, live=True),
], presets={
    "tunnel": {"label": "Туннелирование электрона через барьер 1 эВ × 0,6 нм", "params": {}},
    "tunnel_bohm": {"label": "То же глазами Бома: траектории", "params": {"interp": "bohm"}},
    "tunnel_everett": {"label": "То же по Эверетту: ветви", "params": {"interp": "everett"}},
    "resonant": {"label": "Резонансное туннелирование: двойной барьер",
                 "params": {"scenario": "double", "V0": 1.0, "width": 0.4, "gap": 2.0, "energy": 0.33, "sigma": 8.0}},
    "above": {"label": "Над барьером: отражение без препятствия", "params": {"energy": 1.3}},
    "step": {"label": "Ступенька: отражение при E > V₀", "params": {"scenario": "step", "V0": 0.6, "energy": 0.8}},
    "well": {"label": "Яма: рассеяние на притягивающем потенциале",
             "params": {"scenario": "well", "V0": -2.0, "width": 1.0, "energy": 0.3, "sigma": 6.0}},
    "thick": {"label": "Толстый барьер: прохождение экспоненциально мало", "params": {"width": 1.5}},
    "oscillator": {"label": "Пакет в гармонической ловушке (когерентное состояние)",
                   "params": {"scenario": "oscillator", "hw": 0.05, "x0": 15.0}},
})

# detector ramps W = W0 (d/D)^2 (nm, eV), tried in this order; the first whose reflection averaged over the packet's
# spectrum and whose leak through the ramp (the grid is periodic) are below the limits is used (review V3-3:
# a fixed 15 nm ramp reflected 0.4 % at 0.05 eV and 17 % at 0.01 eV, and leaked 1e-5 at 20 eV)
DETECTORS = ((15.0, 2.0), (30.0, 2.0), (60.0, 0.5), (120.0, 0.5))
R_DET_MAX, LEAK_MAX = 1e-6, 1e-8
R_REL_AIM, R_REL_MAX = 1e-3, 1e-2  # behind a raised step: the fraction of the transmitted probability the right
# ramp sends back — the first ramp within R_REL_AIM, else the one that sends back least, accepted within R_REL_MAX
# (near the threshold the transmitted waves are slow and every ramp of DETECTORS reflects them: 6.8e-3 at best for the
# default step; the T check counts the probability returned, T_ref r_rel, in its tolerance)
N_GRID_MAX = 32768
COST_MAX = 1.2e9  # grid points x time steps per set-up; a set-up estimated above COST_MAX/2 (~ 25 s at ~4e-8 s per
# point-step, measured) is refused, the adaptive continuation stops at COST_MAX (review V3-4)
# The time step at sharp edges (review UX-params P19: a 10 nm barrier with delta = 0.02 nm transmitted 7.7e-5 against the
# stationary 1.38e-6). The split operator's error at an edge of width delta is set by the edge's kinetic energy
# hbar^2/(2 m delta^2) (95 eV at 0.02 nm, against the 3 eV the phase step counted): the phase of one step at that energy,
# phi = dt hbar/(2 m delta^2), measured (2026-11-05, E = 0.8 eV, V0 = 1 eV, sigma = 4 nm; ``reviews``' response checks):
# phi = 2.96 put a spurious 7.5e-5 above the barrier for widths 0.6, 3 and 10 nm alike (harmless for T = 0.16, 55x
# for T = 1.4e-6), phi = 1.48: 8.2e-6, phi = 0.74: 2.3e-7, phi = 0.47: 3.5e-7 (the floor of other errors). Where the
# expected transmission is below T_EDGE the step keeps phi <= PHI_EDGE, so that this error stays below the check's
# 1e-7 + 1e-3 T; above, the 1e-3 T tolerance holds at the phase step's own dt (2.7e-5 at T = 0.16).
PHI_EDGE = 0.25
T_EDGE = 0.1
E_DET_MIN = 0.01  # eV: the slowest electrons the detector ramps absorb within R_DET_MAX (stationary calculation)
N_KEEP = 300  # stored snapshots are thinned to between N_KEEP and 2 N_KEEP


class Simulation(BaseSimulation):
    speed_range = (1e-18, 1e-6)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self.seg = -1
        self.counts = {"emitted": 0, "left": 0, "right": 0}
        self.particle = None
        self.history = []  # outcomes of this segment (side per particle)
        self._buf = []
        self._build()
        self.default_speed = self.cycle * FS / 6.0
        self._new_segment("начало", rebuild=True)

    # --- the set-up -------------------------------------------------------------------------------------------
    def _build(self):
        p = self.params
        self.m = mass_ev(M_E)
        self._exp, self.dt_edge, self.slow_note = None, math.inf, ""
        sc_ = p["scenario"]
        osc = sc_ == "oscillator"
        delta = p["edge"]
        a, gap, V0 = p["width"], p["gap"], p["V0"]

        def step_fn(xx):
            return 0.5 * (1.0 + np.tanh(np.asarray(xx, float) / delta))

        if sc_ in ("barrier", "well"):
            self.Vf = lambda xx: V0 * (step_fn(xx) - step_fn(np.asarray(xx) - a))
            self.extent = (-10 * delta, a + 10 * delta)
        elif sc_ == "double":
            self.Vf = lambda xx: V0 * (step_fn(xx) - step_fn(np.asarray(xx) - a)
                                       + step_fn(np.asarray(xx) - a - gap) - step_fn(np.asarray(xx) - 2 * a - gap))
            self.extent = (-10 * delta, 2 * a + gap + 10 * delta)
        elif sc_ == "step":
            self.Vf = lambda xx: V0 * step_fn(xx)
            self.extent = (-10 * delta, 10 * delta)
        elif sc_ == "free":
            self.Vf = lambda xx: np.zeros_like(np.asarray(xx, float))
            self.extent = (-1.0, 1.0)
        else:
            w = p["hw"] / HBAR
            self.Vf = lambda xx: 0.5 * self.m * w * w * np.asarray(xx, float) ** 2
            self.extent = None
        # the packet
        if osc:
            w = p["hw"] / HBAR
            self.sigma = math.sqrt(HBAR / (2 * self.m * w))  # ground-state width: a coherent state
            self.k0 = 0.0
            self.x_start = p["x0"]
            self.L = abs(p["x0"]) + 12 * self.sigma + 10.0  # the window of the motion (V grows as x^2)
            k_need = self.m * w * (abs(p["x0"]) + 6 * self.sigma) / HBAR + 4 / self.sigma
            dx_max = math.pi / (6 * k_need)
        else:
            self.sigma = p["sigma"]
            self.k0 = math.sqrt(2 * self.m * p["energy"]) / HBAR
            sk = 1 / (2 * self.sigma)
            k_min = math.sqrt(2 * self.m * E_DET_MIN) / HBAR
            if self.k0 - 3 * sk < k_min:  # the packet's slow edge would stand still, fly back or pass the detectors
                need = 1.5 / (self.k0 - k_min) if self.k0 > k_min else math.inf
                raise ValueError(f"пакет слишком широк по импульсу: при E = {p['energy']:g} эВ нужна σ ≥ "
                                 f"{need:.3g} нм — медленный край пакета (k₀ − 3·ħ/(2σ)) должен иметь не меньше "
                                 f"{E_DET_MIN:g} эВ: более медленные электроны края-детекторы не поглощают, а "
                                 "отражают, и часть волны стоит на месте или летит назад; увеличьте σ или энергию")
            self.x_start = self.extent[0] - 6 * self.sigma - 5.0
            v_right = float(self.Vf(np.array([1e6]))[0])
            self._exp = self._expected_T()
            self.det, self.W0, self.R_det, self.leak_det = self._detector(self.k0, sk, v_right)
            # the window: the packet's tail, then the detector on the left; the same room on the right
            D = self.det
            self.L = max(-self.x_start + 6 * self.sigma + D + 2.0, self.extent[1] + 6 * self.sigma + D + 10.0)
            vmin = min(0.0, V0 if sc_ != "free" else 0.0)
            k_need = math.sqrt(2 * self.m * (p["energy"] - vmin)) / HBAR + 4 / self.sigma
            dx_max = min(math.pi / (6 * k_need), delta)  # 6 points per half-wave: converged (measured)
        n = int(2 ** math.ceil(math.log2(max(1024, 2 * self.L / dx_max))))
        if n > N_GRID_MAX:  # refuse rather than cap silently (aliasing; review V3-4)
            raise ValueError(f"нужна сетка из {n} точек (больше {N_GRID_MAX}): "
                             + ("уменьшите смещение x₀ или ħω ловушки" if osc else
                                "уменьшите энергию или ширину пакета σ, или увеличьте размытие краёв δ"))
        self.n_grid = n
        if osc:
            self.det, self.W0, self.R_det, self.leak_det = 0.0, 0.0, 0.0, 0.0
        x = np.linspace(-self.L, self.L, self.n_grid, endpoint=False)
        self.grid = S1.Grid(x, self.m, HBAR)
        self.V = self.Vf(x)
        # detectors: absorbing potential ramps at the edges (scattering scenarios only)
        W = np.zeros_like(x)
        if not osc:
            for side in (-1, 1):
                d = np.clip((side * x - (self.L - self.det)) / self.det, 0, 1)
                W += self.W0 * d**2  # eV
        self.W = W
        self.t_end_est = self._t_end()
        self.dt_edge = self._dt_edge()
        cost = self.n_grid * self.t_end_est / self._dt_max()
        if cost > COST_MAX / 2:
            raise ValueError(self._cost_reason(cost))
        self._evolve()

    def _dt_edge(self):
        """The step the edges ask for (PHI_EDGE, above), or inf: only where the expected transmission is small enough
        for the edges' error to matter (review UX-params P19)."""
        p = self.params
        if p["scenario"] not in ("barrier", "double", "step", "well") or self._exp is None or self._exp[0] >= T_EDGE:
            return math.inf
        return PHI_EDGE * 2 * self.m * p["edge"] ** 2 / HBAR

    def _cost_reason(self, cost):
        """Why the set-up is too costly, in the owner's terms: what makes it so and what to change for this scenario
        (review UX-params P19: the advice named parameters the oscillator does not show)."""
        p = self.params
        head = (f"этот опыт слишком дорог для живого мира: сетка {self.n_grid} точек × {cost / self.n_grid:.3g} шагов "
                f"(≈ {cost * 4e-8:.0f} с счёта, предел ≈ {COST_MAX / 2 * 4e-8:.0f} с)")
        if p["scenario"] == "oscillator":
            return head + "; уменьшите ħω ловушки или смещение x₀"
        if self.dt_edge < self._dt_phase():
            k = self._dt_phase() / self.dt_edge
            d_need = p["edge"] * math.sqrt(min(k, 1e6))
            return (head + f": края барьера резкие (δ = {p['edge']:g} нм), а прохождение мало (T ≈ "
                    f"{self._exp[0]:.2g}): шаг по времени нужен в {k:.3g} раза меньше, иначе ошибка схемы на краях "
                    f"больше самого прохождения; увеличьте размытие краёв δ (до ≈ {min(d_need, 2.0):.2g} нм) или "
                    f"уменьшите ширину или высоту барьера")
        if self.slow_note:
            return head + ": " + self.slow_note
        return head + "; уменьшите ширину пакета σ, энергию или высоту потенциала"

    def _detector(self, k0, sk, v_right):
        """(D, W0, reflection, largest leak through the ramp) of the first detector ramp in DETECTORS within the limits:
        stationary R and T of the ramp -iW0 (d/D)^2 by transfer matrices (lfphys.core.quantum.transfer
        .transmission_profile), on the left for the incident energies and on the right for the transmitted ones
        (E - V_right). Behind a raised step (V_right > 0) the right ramp meets the transmitted spectrum w(k) T(k) of the
        stationary reference, much of it just above the threshold and slow, which ramps reflect (review UX-params P13: a
        ramp chosen for the incident spectrum sent 19 % of T back and T came out 8 % low): there the limit is on the
        fraction of T it sends back (R_REL_MAX; the T check counts it in its tolerance), and the reflection reported is the
        absolute probability returned, max(left, T r_rel). Sets ``det_ok``."""
        ks = np.linspace(max(k0 - 4 * sk, 0.02 * k0), k0 + 4 * sk, 41)
        w = np.exp(-((ks - k0) ** 2) / (2 * sk * sk))
        E = HBAR**2 * ks**2 / (2 * self.m)
        rel = None
        if v_right > 0 and self._exp is not None:
            on = self._exp[2] > 0
            if on.any():
                rel = (self._exp[1][on], self._exp[3][on] * self._exp[2][on], self._exp[0])
        kr, wr = (ks, w) if rel is None else (rel[0], rel[1])
        Er = HBAR**2 * kr**2 / (2 * self.m) - v_right
        ok = Er > 1e-4
        best = None
        for D, W0 in DETECTORS:
            ramp = lambda xx, D=D, W0=W0: np.where(np.asarray(xx) <= D, -1j * W0 * np.clip(np.asarray(xx) / D, 0, 1) ** 2, 0.0)  # noqa: E731
            Tl, Rl = transfer.transmission_profile(E, ramp, 0.0, D, 2000, self.m, HBAR, return_r=True)
            Rr = np.zeros_like(Er)
            Tr = np.zeros_like(Er)
            if ok.any():
                Tr[ok], Rr[ok] = transfer.transmission_profile(Er[ok], ramp, 0.0, D, 2000, self.m, HBAR, return_r=True)
            Rl_ = float(np.sum(w * Rl) / np.sum(w))
            leak = float(max(Tl.max(), Tr.max()))
            if rel is None:
                Rbar = float(max(Rl_, np.sum(wr * Rr) / np.sum(wr)))
                best = (D, W0, Rbar, leak)
                self.det_ok = Rbar <= R_DET_MAX and leak <= LEAK_MAX
                if self.det_ok:
                    break
            else:  # the first within R_REL_AIM; else the one that sends back least, accepted within R_REL_MAX
                r_rel = float(np.sum(wr * Rr) / np.sum(wr))
                cand = (r_rel, (D, W0, max(Rl_, rel[2] * r_rel), leak), Rl_ <= R_DET_MAX and leak <= LEAK_MAX)
                if best is None or (cand[2], -cand[0]) > (best[2], -best[0]):
                    best = cand
                if cand[2] and r_rel <= R_REL_AIM:
                    break
        if rel is not None:
            self.det_ok = best[2] and best[0] <= R_REL_MAX
            best = best[1]
        return best

    def _t_end(self):
        """The time by which the packet should have left the window: through the window at the slow edge of the
        incident spectrum, and back or onwards at the slow edge of the transmitted one (for a step just above the
        incident energy the transmitted wave is slow: review V3-1). Where the potential beyond is raised (a step), the
        transmitted spectrum is that of the stationary reference, w(k) T(k): its slowest part that still carries 1e-3
        of T must leave the step's region (review UX-params P13: below the step only the fast tail of the packet passes,
        just above the threshold and slowly; the run waited for it until its budget and missed 8 % of T). The run
        continues past it until the wave is absorbed (``_evolve``)."""
        p = self.params
        self.slow_note = ""
        if p["scenario"] == "oscillator":
            return 2 * 2 * math.pi * HBAR / p["hw"]
        v = HBAR * self.k0 / self.m
        spread = 3 * HBAR / (2 * self.m * self.sigma)
        v_in = max(v - spread, 0.25 * v)
        v_right = float(self.Vf(np.array([self.L]))[0])
        e_slow = 0.5 * self.m * v_in**2 - v_right
        e_mid = p["energy"] - v_right
        e_out = e_slow if e_slow > 0 else (e_mid if e_mid > 0 else 0.0)  # the run extends past t_end if needed
        v_out = math.sqrt(2 * e_out / self.m) if e_out > 0 else v_in
        t = 1.3 * (self.L / v_in + self.L / max(min(v_in, v_out), 0.05 * v_in))
        if v_right > 0 and self._exp is not None:
            ks, T, w = self._exp[1], self._exp[2], self._exp[3]
            kv = math.sqrt(2 * self.m * v_right) / HBAR
            on = (ks > kv) & (T > 0)
            if on.any():
                q = np.sqrt(np.maximum(ks[on] ** 2 - kv * kv, 0.0))
                f = w[on] * T[on]
                cum = np.cumsum(f[np.argsort(q)]) / f.sum()
                q_min = float(np.sort(q)[min(int(np.searchsorted(cum, 1e-3)), len(q) - 1)])
                v_min = HBAR * max(q_min, 1e-12) / self.m
                t_slow = 1.3 * (abs(self.x_start) / v_in + (self.extent[1] + 3.0 + 2.0) / v_min)
                if t_slow > t:
                    self.slow_note = (f"энергия пакета {p['energy']:g} эВ {'ниже' if p['energy'] < v_right else 'близко к'}"
                                      f" высоты ступеньки {v_right:g} эВ: проходит только часть спектра у порога, "
                                      f"медленно (до {v_min * 1e3:.2g} нм/пс), и её надо дождаться; поднимите энергию "
                                      f"выше ступеньки, опустите ступеньку или сузьте пакет по импульсу (больше σ)")
                    t = t_slow
        return t

    def _evolve(self):
        """The wave of every particle of this set-up, exactly (split-operator), stored at display times; the
        probability each detector absorbs; with the Bohm reading, the trajectories of an ensemble of quantiles."""
        g, p = self.grid, self.params
        psi = g.gaussian(self.x_start, self.k0, self.sigma)
        self.psi0 = psi.copy()
        osc = p["scenario"] == "oscillator"
        with_bohm = p["interp"] == "bohm" or osc
        t_end = self.t_end_est
        dt_store = t_end / (2 * N_KEEP)
        sub = max(1, int(math.ceil(dt_store / self._dt_max())))
        dt = dt_store / sub
        step = g.stepper(self.V, dt, absorb=self.W)
        snaps, PL, PR, norm = [np.abs(psi) ** 2], [0.0], [0.0], [1.0]
        left = g.x < 0
        pl = pr = 0.0
        n_steps, t, self.capped = 0, 0.0, False
        cl = cr = unc = 0.0
        while True:
            for _ in range(sub):
                new = step(psi)
                if not osc:  # the exact loss of norm in the step, shared between the detectors as W |psi|^2 is
                    a2, b2 = np.abs(psi) ** 2, np.abs(new) ** 2
                    lost = float(np.sum(a2 - b2)) * g.dx
                    wl = float(np.sum((self.W * (a2 + b2))[left]))
                    wr = float(np.sum((self.W * (a2 + b2))[~left]))
                    if wl + wr > 0:
                        pl += lost * wl / (wl + wr)
                        pr += lost * wr / (wl + wr)
                psi = new
            n_steps += sub
            t += dt_store
            snaps.append(np.abs(psi) ** 2)
            PL.append(pl)
            PR.append(pr)
            norm.append(g.norm(psi))
            if len(snaps) > 2 * N_KEEP:  # keep every other snapshot and store half as often (uniform spacing)
                snaps, PL, PR, norm = snaps[::2], PL[::2], PR[::2], norm[::2]
                dt_store, sub = 2 * dt_store, 2 * sub
            if osc:
                if t >= t_end * (1 - 1e-12):
                    break
                continue
            # stop when the part of the wave whose fate is still open cannot change T by more than 1e-3 T + 1e-9 nor
            # R by more than 1e-3 R + 1e-6 (``_leftover_allowed``), after the estimated time
            # (review V3-1, V3-2). Probability already beyond the potential and moving outward in a region of constant
            # potential reaches its detector for sure (free motion): it is assigned now instead of waited for.
            if t >= t_end:
                cl, cr = self._fates(psi)
                unc = max(norm[-1] - cl - cr, 0.0)
                if unc <= self._leftover_allowed(pl + cl, pr + cr):
                    break
            if n_steps * self.n_grid > COST_MAX:
                self.capped = True
                cl, cr = self._fates(psi)
                unc = max(norm[-1] - cl - cr, 0.0)
                break
        if not osc:  # the certain fates join the detectors at the end of the computed time
            PL[-1] += cl
            PR[-1] += cr
            pl, pr = PL[-1], PR[-1]
        self.assigned = 0.0 if osc else float(cl + cr)
        self.leftover = 0.0 if osc else float(unc)
        self.leftover_allowed = 0.0 if osc else self._leftover_allowed(pl, pr)
        self.t_snap = np.arange(len(snaps)) * dt_store
        self.snaps = np.array(snaps, np.float32)
        self.PL, self.PR, self.norm = np.array(PL), np.array(PR), np.array(norm)
        # Bohm: the trajectory of quantile q is the q-quantile of |psi(t)|^2 with the absorbed mass beyond the
        # edges (exact in 1-D; lfphys.theories.interpretations.bohm.quantile_positions)
        quant = (np.arange(400) + 0.5) / 400
        self.traj = np.array([bohm.quantile_positions(g.x, self.snaps[i].astype(float), self.PL[i], quant)
                              for i in range(len(self.snaps))]) if with_bohm else np.zeros((len(self.snaps), 400))
        self.has_bohm = with_bohm
        self.cycle = float(self.t_snap[-1]) * (1.0 if osc else 1.05)
        self.dt_store = dt_store

    def _fates(self, psi):
        """(to the left detector, to the right one) for sure: the probability outside the potential's extent, in its
        region of constant potential, moving away from it (k < 0 on the left, k > 0 on the right), from the momentum
        spectrum of psi under a smooth mask of that region (the free particle: all of it, by the sign of k)."""
        g = self.grid
        x = g.x
        k = 2 * np.pi * np.fft.fftfreq(len(x), d=g.dx)
        w = 0.5  # nm, mask edge
        if self.params["scenario"] == "free":
            masks = (np.ones_like(x), np.ones_like(x))
        else:
            a, b = self.extent[0] - 3.0, self.extent[1] + 3.0
            masks = (0.5 * (1 - np.tanh((x - a) / w)), 0.5 * (1 + np.tanh((x - b) / w)))
        out = []
        for m, sign in zip(masks, (-1, 1)):
            mass = float(np.sum(np.abs(psi) ** 2 * m)) * g.dx
            if mass <= 0:
                out.append(0.0)
                continue
            ph = np.abs(np.fft.fft(psi * m)) ** 2
            tot = float(np.sum(ph))
            out.append(mass * float(np.sum(ph[sign * k > 0])) / tot if tot > 0 else 0.0)
        return out[0], out[1]

    @staticmethod
    def _leftover_allowed(pl, pr):
        """How much probability of open fate may be left: it can still go to either side, so it must stay within the
        accuracy the run claims for T (the right share: 1e-3 T + 1e-9, the T check) and for R (the left share:
        1e-3 R + 1e-6; R is not checked separately, and a part ~1e-7 of a broad packet sits at k ~ 0 for ever)."""
        return max(1e-10, min(1e-3 * pr + 1e-9, 1e-3 * pl + 1e-6))

    def _dt_max(self):
        """The time step: the phase step (``_dt_phase``) and, for a small transmission behind sharp edges, the edges'
        step (``_dt_edge``, review UX-params P19)."""
        return min(self._dt_phase(), getattr(self, "dt_edge", math.inf))

    def _dt_phase(self):
        """Phase step of the fastest relevant component and of the potential where the wave lives below 0.1 rad
        (Strang splitting; measured: 0.3 rad gives 2.5 % error in the transmission near sharp edges, 0.1 rad < 1e-3)."""
        p = self.params
        if p["scenario"] == "oscillator":
            w = p["hw"] / HBAR
            reach = abs(p["x0"]) + 6 * self.sigma
            e_pot = 0.5 * self.m * w * w * reach**2
            kmax = self.m * w * reach / HBAR + 3 / self.sigma
        else:
            e_pot = float(np.max(np.abs(self.V)))
            kmax = math.sqrt(2 * self.m * (p["energy"] + e_pot)) / HBAR + 3 / self.sigma
        e_kin = HBAR**2 * kmax**2 / (2 * self.m)
        rad = 0.25 if p["scenario"] == "oscillator" else 0.1  # a smooth trap tolerates a larger step
        return rad * HBAR / max(e_kin + e_pot, 1e-6)

    # --- live parameters -----------------------------------------------------------------------------------
    def live_values(self):
        return {k: self.params[k] for k in SCHEMA.live_ids()}

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.params, values)
        if errors:
            raise ValueError("; ".join(errors))
        changed = [k for k in values if new.get(k) != self.params.get(k)]
        if not changed:
            return "без изменений"
        desc = "; ".join(f"{SCHEMA.by_id[k].label}: {self.params[k]} → {new[k]}" for k in changed)
        bohm_needed = new["interp"] == "bohm" and not self.has_bohm
        if set(changed) <= {"interp", "n_bohm"} and not bohm_needed:
            self.params = new  # a reading, not physics: the wave and the statistics stay; outcomes are produced anew
            self._new_segment("другая интерпретация: " + desc, rebuild=False)
            return desc
        old = self.params
        self.params = new
        try:
            self._build()
        except Exception:
            self.params = old
            self._build()
            raise
        self._new_segment("изменена установка: " + desc, rebuild=True)
        return desc

    # --- particles -----------------------------------------------------------------------------------------
    def _new_segment(self, reason, rebuild):
        self.seg += 1
        self.seg_t0 = self.t
        self.history = []
        self.counts = {"emitted": 0, "left": 0, "right": 0}
        self._segment_msg(reason)
        self._new_particle(self.t)

    def _new_particle(self, t0):
        """Emit the next particle at t0 and decide its outcome in the chosen reading (revealed at the click)."""
        rng = self.rng
        p = self.params
        osc = p["scenario"] == "oscillator"
        part = {"t0": t0, "click": None, "side": None, "q": None, "branches": None}
        if not osc:
            PL, PR = self.PL[-1], self.PR[-1]
            tot = PL + PR
            interp = p["interp"]
            if interp == "bohm":
                q = rng.random()  # where in |psi|^2 the particle starts: its quantile
                part["q"] = q
                gone_l = np.nonzero(self.PL > q)[0]
                gone_r = np.nonzero(1.0 - self.PR < q)[0]
                i_l = int(gone_l[0]) if len(gone_l) else None
                i_r = int(gone_r[0]) if len(gone_r) else None
                if i_r is not None and (i_l is None or i_r < i_l):
                    part["side"], i = "right", i_r
                else:
                    part["side"], i = "left", i_l if i_l is not None else len(self.t_snap) - 1
                part["click"] = t0 + self.t_snap[i] * FS
            else:
                side = "right" if rng.random() < PR / tot else "left"
                cum = self.PR if side == "right" else self.PL
                u = rng.random() * cum[-1]
                i = int(np.searchsorted(cum, u))
                part["side"] = side
                part["click"] = t0 + self.t_snap[min(i, len(self.t_snap) - 1)] * FS
                if interp == "everett":
                    part["branches"] = {"left": PL / tot, "right": PR / tot}
        self.particle = part
        self.counts["emitted"] += 1
        self._msg({"type": "emit", "t": t0, "seg": self.seg, "interp": p["interp"]})

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

    def _check(self, cid, label, value, ref, unit="", group="", note="", tol=1e-9, ok=None):
        rel = None
        if ref is not None and value is not None and ref != 0 and math.isfinite(value):
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        self._msg(d)

    def _expected_T(self):
        """The independent reference: the stationary transmission T(E) of the same potential (transfer matrices over
        a fine staircase, two resolutions, Richardson), averaged over the packet's momentum distribution
        |phi(k)|^2 ~ exp(-(k - k0)^2 / (2 s_k^2)), s_k = 1/(2 sigma)."""
        if self.extent is None:
            return None
        if getattr(self, "_exp", None) is not None:
            return self._exp
        sk = 1 / (2 * self.sigma)
        # the whole Gaussian: components with k <= 0 move away from the potential and count as reflected (T = 0);
        # until 2026-10-23 they were dropped and the rest renormalised (review V3-3)
        ks = np.linspace(self.k0 - 8 * sk, self.k0 + 8 * sk, 801)
        fwd = ks > 1e-6
        E = HBAR**2 * ks[fwd] ** 2 / (2 * self.m)
        x0, x1 = self.extent
        vmax = float(np.max(np.abs(self.Vf(np.linspace(x0, x1, 4001)))))
        kmax = math.sqrt(2 * self.m * (E.max() + vmax)) / HBAR
        h = min(self.params["edge"] / 20, math.pi / (40 * kmax))
        n = int(math.ceil((x1 - x0) / h))
        t1 = transfer.transmission_profile(E, self.Vf, x0, x1, n, self.m, HBAR)
        t2 = transfer.transmission_profile(E, self.Vf, x0, x1, 2 * n, self.m, HBAR)
        T = np.zeros_like(ks)
        T[fwd] = (4 * t2 - t1) / 3
        w = np.exp(-((ks - self.k0) ** 2) / (2 * sk * sk))
        return float(np.sum(T * w) / np.sum(w)), ks, T, w, float(np.max(np.abs(t2 - t1)))

    def _segment_msg(self, reason):
        g, p = self.grid, self.params
        osc = p["scenario"] == "oscillator"
        grp = f"Отрезок {self.seg}"
        # space-time map of |psi|^2 (subsampled) and the Bohm ensemble for drawing
        step_t = max(1, len(self.t_snap) // 300)
        step_x = 4
        mp = self.snaps[::step_t, ::step_x]
        nb = int(p["n_bohm"])
        sel = np.linspace(0, 399, nb).astype(int) if nb > 0 else np.array([], int)
        blobs = {"x": g.x.astype(np.float32), "V": self.V.astype(np.float32), "W": self.W.astype(np.float32),
                 "map": (mp / max(float(mp.max()), 1e-30)).astype(np.float32),
                 "t_map": self.t_snap[::step_t].astype(np.float64),
                 "traj": np.clip(self.traj[::step_t][:, sel], -self.L, self.L).astype(np.float32)}
        meta = {"type": "segment", "t": self.t, "seg": self.seg, "reason": reason, "scenario": p["scenario"],
                "interp": p["interp"], "cycle": self.cycle, "map_shape": list(mp.shape),
                "traj_shape": [len(self.t_snap[::step_t]), int(len(sel))], "L": self.L, "det": self.det,
                "energy": p["energy"], "k0": self.k0, "sigma": self.sigma, "PL": float(self.PL[-1]),
                "PR": float(self.PR[-1]), "osc": osc, "has_bohm": bool(self.has_bohm)}
        exp = self._expected_T() if not osc else None
        if exp is not None:
            meta["T_expected"] = exp[0]
            fwd = exp[1] > 1e-6
            kf = exp[1][fwd]
            blobs["T_k"] = exp[2][fwd].astype(np.float64)
            blobs["E_k"] = (HBAR**2 * kf**2 / (2 * self.m)).astype(np.float64)
            wE = exp[3][fwd] / (HBAR**2 * kf / self.m)  # the energy density: w(k) dk/dE (review V3-5)
            blobs["w_k"] = (wE / wE.max()).astype(np.float64)
        self._msg(meta, blobs)
        # checks
        if not osc:
            tot = self.PL[-1] + self.PR[-1]
            capped = " Счёт остановлен по бюджету раньше." if self.capped else ""
            self._check(f"abs{self.seg}", "Волна поглощена детекторами (остаток не меняет результат)", tot, 1.0, "",
                        grp, ok=self.leftover <= self.leftover_allowed, tol=self.leftover_allowed,
                        note=f"неопределённый остаток {self.leftover:.1e}, допустимо {self.leftover_allowed:.1e} "
                             f"(10⁻³·T + 10⁻⁹ и 10⁻³·R + 10⁻⁶); ещё {self.assigned:.1e} — за потенциалом и уходит от него (свободное "
                             f"движение): отнесено к своему детектору в конце счёта; поглощающие края — модель "
                             f"детектора.{capped}")
            self._check(f"det{self.seg}", "Детекторы: отражение (среднее по спектру пакета) и утечка сквозь край",
                        self.R_det, 0.0, "", grp, ok=self.det_ok,
                        tol=R_DET_MAX,
                        note=f"край W = {self.W0:g} эВ·(d/D)², D = {self.det:g} нм, выбран по спектру пакета; "
                             f"отражение {self.R_det:.1e} (допуск {R_DET_MAX:.0e}"
                             + (f"; за ступенькой — доля прошедшего, которую правый край возвращает, не больше "
                                f"{R_REL_MAX:.0e}" if p["scenario"] == "step" and p["V0"] > 0 else "")
                             + f"), утечка {self.leak_det:.1e} (допуск {LEAK_MAX:.0e}); стационарный расчёт матрицами "
                               f"переноса")
            if exp is not None:
                Tp = self.PR[-1] / tot
                tolT = 1e-7 + 1e-3 * exp[0] + self.leftover + self.R_det
                self._check(f"T{self.seg}", "Прохождение волнового пакета (вычислено по времени)", Tp,
                            exp[0], "", grp, ok=abs(Tp - exp[0]) <= tolT, tol=tolT / max(exp[0], 1e-300),
                            note="эталон — другим методом: стационарное прохождение T(E) того же потенциала "
                                 "(матрицы переноса по мелкой лестнице, экстраполяция Ричардсона) по всему "
                                 "распределению импульсов пакета |φ(k)|² (k ≤ 0 — отражены); допуск 1e-7 + 1e-3·T + "
                                 f"непоглощённый остаток + отражение детекторов = {tolT:.1e}; Ричардсон эталона "
                                 f"±{exp[4]:.0e}")
            E_mean = g.energy(self.psi0, self.V)
            self._check(f"E{self.seg}", "Средняя энергия пакета", E_mean,
                        p["energy"] + HBAR**2 / (8 * self.m * self.sigma**2), "эВ", grp, tol=1e-6,
                        note="эталон: ħ²k₀²/2m + ħ²/(8mσ²) (гауссов пакет в свободной области)")
        else:
            w = p["hw"] / HBAR
            # the 4 lowest levels on a window around the trap (sinc DVR, 256 points; the whole grid as a dense matrix
            # needed gigabytes: review V3-4): turning point of the 4th level plus 8 ground-state widths
            Lw = math.sqrt(9 * HBAR / (self.m * w)) + 8 * self.sigma
            xw = np.linspace(-Lw, Lw, 256, endpoint=False)
            gw = S1.Grid(xw, self.m, HBAR)
            E, _ = gw.eigenstates(self.Vf(xw), 4)
            self._check(f"lev{self.seg}", "Нижний уровень ловушки (спектральный метод)", E[0], 0.5 * p["hw"], "эВ",
                        grp, tol=1e-9, note="эталон ħω/2")
            self._check(f"lev3{self.seg}", "Четвёртый уровень", E[3], 3.5 * p["hw"], "эВ", grp, tol=1e-9,
                        note="эталон ħω(n + ½), n = 3")
            xm = np.sum(self.snaps * g.x[None, :], axis=1) / np.sum(self.snaps, axis=1)
            T_osc = 2 * math.pi / w
            i_T = int(round(T_osc / self.dt_store))
            if i_T < len(xm):
                self._check(f"per{self.seg}", "Пакет вернулся через период 2π/ω", float(xm[i_T]), float(xm[0]),
                            "нм", grp, tol=1e-4, note="центр пакета ⟨x⟩ через T = 2π/ω (когерентное состояние)")
            self._check(f"norm{self.seg}", "Норма волновой функции через два периода", float(self.norm[-1]), 1.0, "",
                        grp, tol=1e-10, note="унитарная эволюция (метод расщепления оператора)")

    # --- time ---------------------------------------------------------------------------------------------------
    def max_step(self):
        return self.cycle * FS / 50

    def next_event_time(self):
        c = self.particle and self.particle.get("click")
        return c if c is not None and c > self.t else self.particle["t0"] + self.cycle * FS

    def advance(self, t_target):
        while True:
            part = self.particle
            c = part.get("click")
            if c is not None and c <= t_target and "done" not in part:
                part["done"] = True
                side = part["side"]
                self.counts[side] += 1
                self.history.append(side)
                xd = (self.L - self.det / 2) * (1 if side == "right" else -1)
                ev = {"type": "event", "kind": "click", "t": c, "side": side, "x": xd, "seg": self.seg,
                      "text": f"щелчок детектора {'справа (прошла)' if side == 'right' else 'слева (отразилась)'}"}
                if part.get("branches"):
                    ev["branches"] = part["branches"]
                    ev["text"] += f"; ветви: слева {part['branches']['left']:.3f}, справа {part['branches']['right']:.3f}"
                self._msg(ev)
                self._statistics_check()
            t_next = part["t0"] + self.cycle * FS
            if t_next <= t_target:
                self.t = t_next
                self._new_particle(t_next)
                continue
            break
        self.t = t_target

    def _statistics_check(self):
        n = len(self.history)
        if n < 20 or n % 10:
            return
        PR = self.PR[-1] / (self.PL[-1] + self.PR[-1])
        k = sum(1 for s in self.history if s == "right")
        sd = math.sqrt(max(PR * (1 - PR), 1e-12) / n)
        z = (k / n - PR) / sd if sd > 0 else 0.0
        self._check(f"stat{self.seg}", f"Доля прошедших среди {n} частиц", k / n, PR, "", f"Отрезок {self.seg}",
                    ok=abs(z) < 5, note=f"отклонение {z:+.2f}σ от вероятности, посчитанной из волны")

    def frame(self):
        part = self.particle
        tl = (self.t - part["t0"]) / FS  # fs since the emission
        i = int(min(max(round(tl / self.dt_store), 0), len(self.t_snap) - 1))
        rho = self.snaps[i]
        st = {"t_local": tl, "seg": self.seg, "counts": self.counts, "interp": self.params["interp"],
              "PL_t": max(0.0, float(self.PL[i])), "PR_t": max(0.0, float(self.PR[i])),
              "norm_t": float(self.norm[i])}
        c = part.get("click")
        collapsed = c is not None and self.t >= c
        st["clicked"] = part["side"] if collapsed else None
        if part.get("q") is not None:
            xb = bohm.quantile_positions(self.grid.x, rho.astype(float), self.PL[i], [part["q"]])[0]
            if np.isfinite(xb):
                st["x_bohm"] = float(xb)
        if part.get("branches"):
            st["branches"] = part["branches"]
        return st, {"rho": rho}

    # --- contract ---------------------------------------------------------------------------------------------
    def engine_modules(self):
        mods = ["core.quantum.schrodinger1d", "core.quantum.transfer"]
        mods.append({"copenhagen": "theories.interpretations.copenhagen", "bohm": "theories.interpretations.bohm",
                     "everett": "theories.interpretations.everett"}[self.params["interp"]])
        if self.params["interp"] != "bohm" and self.has_bohm:
            mods.append("theories.interpretations.bohm")
        return mods

    def action(self, name, args):
        if name == "clear":
            self._new_segment("очистка счётчиков", rebuild=False)
            return "счётчики очищены"
        raise ValueError(f"неизвестное действие {name!r}")

    def header(self):
        p = self.params
        return {
            "title": "Квантовая частица: " + dict(SCEN)[p["scenario"]],
            "text": ("Частицы вылетают по одной. Волна каждой — численное решение уравнения Шрёдингера на сетке "
                     "(сходимость проверяется эталоном); детекторы по краям поглощают волну (модель детектора), и "
                     "запуск считает, какую вероятность и когда поглотил каждый. Исход "
                     "частицы получается в выбранной интерпретации: щелчок и коллапс, траектория Бома или ветвление "
                     "Эверетта. Статистика у всех трёх одна и та же — это проверяется."),
            "actions": [{"name": "clear", "label": "Очистить счётчики", "args": []}],
            "units": {"x": "нм", "t": "фс", "E": "эВ"},
        }, {}


VIZ = {
    "id": "v03_quantum_1d",
    "title": "Квантовая частица в одном измерении",
    "summary": ("Электроны по одному у барьера, двойного барьера, ступеньки, ямы или в ловушке: точная волна, "
                "туннелирование, детекторы; исход в копенгагенском, бомовском или эвереттовском прочтении."),
    "purpose": ("Причины поведения частицы: что даёт расчёт волны, а что добавляет интерпретация (одинаковая "
                "статистика, разная картина)."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
