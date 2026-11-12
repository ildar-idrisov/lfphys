# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v12: when does the particle arrive? Arrival times in 2-D by the rules in use (a wrapper over lfphys; plan P14.6, on
P6 and v11).

A wave packet flies along z to a detecting plane, freely or through v11's double slit. The run solves the
Schroedinger equation on the plane (x, z) (v11's machinery: split operator on GPU 0 where it pays, absorbing layers,
the Bohm ensemble) and records at the plane, at every step, the current J(x, t), psi and d psi/dz. From them and
from the initial state the run computes the arrival-time distribution by each rule
(lfphys.theories.interpretations.arrival_times, lfphys.theories.models.detection):

* quantum flux: J integrated over the plane (and J(x, t) itself: the joint distribution of place and time);
* Bohm: the first crossing of each trajectory of the ensemble (and, in free flight, the exact first-arrival law from
  the running maximum of the flux's integral);
* Aharonov-Bohm-Kijowski, semiclassical and the absorbing boundary rule (free flight only: functionals of the initial
  state for free motion);
* the exponential rules of Wlodarz and Marchewka-Schuss, from psi and d psi/dz on the plane;
* the soft detector: a second run of the same experiment whose screen is an absorbing potential -i W0 (it reflects a
  part of the wave; its clicks are the probability it absorbs).

Initial states along the flight: one packet; a train of packets (Das & Struyve 2021: the exponential rules damp the later
peaks, the semiclassical rule shows one peak); a two-speed superposition whose current flows back through the plane
for a while (quantum backflow: the flux is negative, Bohm's first arrivals are not).

Checks (free flight, against closed forms): the flux and psi on the plane against the exact free evolution; Bohm
hit times against the first-arrival law (KS); the soft detector's reflection against stationary transfer matrices
of its profile; the ABR identity; the initial state's momentum distribution; v11's checks (norm, time step, flux,
equivariance, symmetry).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import cumulative_trapezoid

from lfphys.core.quantum import schrodinger_nd as S
from lfphys.core.quantum.schrodinger1d import FreeGaussians
from lfphys.core.quantum.transfer import transmission_profile
from lfphys.theories.interpretations import arrival_times as AT
from lfphys.theories.models import detection as DET
from lfviz.params import Param, Schema
from v11_double_slit_2d import viz as V11

from .engine import apparatus as AP

V11_FIXED = {"mark": "none", "mark_deg": 0.0, "flux": 0.0}  # v11's parameters this world does not offer
CURVE_N = 1501        # samples of the curves computed from the initial state (ABK, semiclassical, ABR)
K_N = 4001            # wave numbers for them
ROWS_PER_T0 = 120     # time bins of the joint distribution J(x, t) per classical flight time t0 (a set-up scale)
COLS_MAX = 240        # its x bins
SOFT_REL_TOL = 0.1    # the soft detector's reflection against the stationary one (measured 0.1-4 % at lambda/6-8)
EARLY = 1e-6          # a live detector change at t = 0, or before this much signal reached the detector, acts as if made
                      # at the start (below the tolerances of the comparisons that assume one value: >= 2e-4)


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("particle", "Частица", "select", "electron", group="Частица",
       options=[("electron", "электрон"), ("neutron", "нейтрон"), ("he4", "атом ⁴He"), ("c60", "фуллерен C₆₀")]),
    _p("lam_pm", "Длина волны де Бройля λ, пм", "float", 100.0, unit="пм", group="Частица", min=20.0, max=5000.0,
       log=True, help="задаёт физический масштаб: все длины опыта — в λ, времена — в единицах mλ²/ħ"),
    _p("scene", "Полёт", "select", "free", group="Опыт",
       options=[("free", "свободно до плоскости детектора"), ("slits", "через две щели (как v11)")]),
    _p("L", "Расстояние до детектора L, λ", "float", 30.0, unit="λ", group="Опыт", min=2.0, max=200.0,
       help="свободный полёт: от центра первого пакета до плоскости; щели: от пластины до экрана"),
    _p("state", "Начальное состояние вдоль полёта", "select", "gauss", group="Пакет",
       options=[("gauss", "один пакет"), ("train", "цепочка пакетов (Das & Struyve 2021)"),
                ("backflow", "медленный и быстрый пакеты встречаются у плоскости: обратный ток")]),
    _p("sigma_z", "Ширина пакета вдоль σz, λ", "float", 5.0, unit="λ", group="Пакет", min=1.0, max=20.0,
       help="разброс импульса Δk/k = 1/(4π σz/λ): чем уже пакет, тем сильнее расходятся правила"),
    _p("sigma_x", "Ширина пакета поперёк σx, λ", "float", 4.0, unit="λ", group="Пакет", min=1.0, max=40.0),
    _p("sigma_y", "Ширина пакета вдоль y σy, λ", "float", 3.0, unit="λ", group="Пакет", min=0.5, max=40.0,
       help="ничто не зависит от y, поэтому волна — точное произведение ψ(x, z, t)·η(y, t): η — свободный гауссов "
            "пакет, он только расплывается; время прихода от y не зависит"),
    _p("n_train", "Пакетов в цепочке", "int", 4, group="Пакет", min=2, max=8, show_if={"state": ["train"]}),
    _p("sep", "Расстояние между пакетами, λ", "float", 30.0, unit="λ", group="Пакет", min=6.0, max=120.0,
       show_if={"state": ["train"]}, help="не меньше 6σz: пакеты не перекрываются"),
    # the plate is live (review UX-ui U12; v11's rules: rebuilt at the current moment in the world's window)
    _p("a", "Ширина щели a, λ", "float", 2.0, unit="λ", group="Пластина", min=0.5, max=20.0, show_if={"scene": ["slits"]},
       live=True, help=V11.LIVE_PLATE_HELP),
    _p("d", "Расстояние между щелями d, λ", "float", 8.0, unit="λ", group="Пластина", min=1.0, max=60.0,
       show_if={"scene": ["slits"]}, live=True, help=V11.LIVE_PLATE_HELP),
    _p("w", "Толщина пластины w, λ", "float", 2.0, unit="λ", group="Пластина", min=0.5, max=10.0,
       show_if={"scene": ["slits"]}, live=True, help=V11.LIVE_PLATE_HELP),
    _p("V0", "Высота стенки V₀, в E₀", "float", 4.0, unit="E₀", group="Пластина", min=1.5, max=8.0,
       show_if={"scene": ["slits"]}, live=True,
       help="потенциальная энергия частицы в материале пластины, в единицах её кинетической энергии E₀. "
            + V11.LIVE_PLATE_HELP),
    _p("edge", "Ширина краёв стенки и мягкого детектора, λ", "float", 0.2, unit="λ", group="Детекторы", min=0.1,
       max=1.0, help="потенциалы нарастают на этой длине (tanh); не меньше шага сетки"),
    _p("kappa", "Поглощающая граница: κ, в k₀", "float", 1.0, unit="k₀", group="Детекторы", min=0.05, max=20.0,
       log=True, help="граничное условие ∂ψ/∂z = iκψ (Вернер, Тумулька): волна с k = κ поглощается целиком, другие "
                      "частично отражаются; только свободный полёт. k₀ — средний волновой вектор пакета"),
    # the exponential rules' strengths and the soft detector's height are live (review UX-ui U12): a detector made
    # more or less sensitive at the current moment
    _p("mu_w", "Правило Влодажа: сила λ₀ (безразмерная)", "float", 1.0, group="Детекторы", min=0.01,
       max=20.0, log=True, live=True,
       help="λ(t) = λ₀ v₀ ∫|ψ(x, L, t)|² dx: λ₀ — среднее число щелчков, если бы частица не исчезала. Меняется на "
            "ходу: щелчки до этого момента посчитаны с прежней силой, после — с новой"),
    _p("mu_ms", "Правило Маркевки–Шусса: сила λ₀ (безразмерная)", "float", 1.0, group="Детекторы",
       min=0.01, max=20.0, log=True, live=True,
       help="λ(t) = λ₀ (v₀/k₀²) ∫|∂ψ/∂z(x, L, t)|² dx, нормировано так же. Меняется на ходу: щелчки до этого момента "
            "посчитаны с прежней силой, после — с новой"),
    _p("soft", "Мягкий детектор (поглощающий потенциал)", "bool", True, group="Детекторы",
       help="второй прогон того же опыта: за плоскостью детектора потенциал −iW₀; часть волны он отражает"),
    _p("W0", "Мягкий детектор: высота W₀, в E₀", "float", 1.0, unit="E₀", group="Детекторы",
       min=0.01, max=6.0, log=True, show_if={"soft": [True]}, live=True,
       help="высота поглощающего потенциала −iW₀ за плоскостью детектора, в единицах кинетической энергии пакета E₀: "
            "больше — поглощает быстрее, но сильнее отражает. Меняется на ходу: поглотитель второго прогона "
            "перестраивается в текущий момент"),
    _p("grid", "Сетка", "select", "normal", group="Расчёт", options=V11.GRIDS),
    _p("n_bohm", "Частиц Бома в ансамбле", "int", 2000, group="Траектории Бома", min=100, max=8000),
    _p("n_tracks", "Из них рисовать траекторий", "int", 60, group="Траектории Бома", min=10, max=400),
    _p("slit_a", "Щель A (x = −d/2) открыта", "bool", True, group="Установка", live=True, show_if={"scene": ["slits"]}),
    _p("slit_b", "Щель B (x = +d/2) открыта", "bool", True, group="Установка", live=True, show_if={"scene": ["slits"]},
       help="закройте щель, пока пакет в пути: опыт Das, Deckert, Kellers, Krekels, Struyve (2024)"),
], presets={
    "gauss": {"label": "Один пакет: все правила почти совпадают вдали от источника", "params": {}},
    "near": {"label": "Близко к источнику (σz = 1λ, L = 5λ): правила расходятся", "params": {"sigma_z": 1.0, "L": 5.0}},
    "train": {"label": "Цепочка из 4 пакетов: экспоненциальные правила гасят поздние пики (Das & Struyve 2021)",
              "params": {"state": "train", "mu_w": 2.0, "mu_ms": 2.0}},
    "backflow": {"label": "Обратный ток: поток через плоскость местами отрицателен, первые прибытия Бома — нет",
                 "params": {"state": "backflow", "sigma_z": 3.0, "L": 16.5}},
    "slits": {"label": "Через две щели: совместное распределение места и времени прихода (Das и др. 2024)",
              "params": {"scene": "slits", "sigma_x": 8.0, "L": 30.0, "soft": False}},
})


class Simulation(V11.Simulation):
    SCHEMA = SCHEMA
    FIXED_LIVE = {"mark_deg": 0.0, "flux": 0.0}  # v11's path mark and flux: not in this world

    def __init__(self, params, seed, emit):
        p = {**V11_FIXED, **dict(params)}
        self.free = p["scene"] == "free"
        self.label_slits = not self.free
        self.BACK_LABEL = "отражено пластиной" if not self.free else "ушло назад"
        # the flight from the leading packet's centre to the plane (behind the plate: from v11's source point)
        D = float(p["L"]) if self.free else float(p["L"]) - AP.SlitGeometry(
            p["a"], p["d"], p["w"], p["L"], p["sigma_x"], p["sigma_z"], V11.H_OF[p["grid"]], edge=float(p["edge"])).z_src
        self.pk = AP.packets(p["state"], p["sigma_z"], p["n_train"], p["sep"], D)
        self.fg = FreeGaussians(self.pk)  # the longitudinal state, z from the leading packet's centre, hbar = m = 1
        ov = AP.overlap(self.fg, D)
        if ov > AP.OVERLAP_MAX:
            raise ValueError(f"детектор слишком близко: {ov:.1e} вероятности уже за его плоскостью в начале "
                             f"(допустимо {AP.OVERLAP_MAX:g}); отодвиньте плоскость или сузьте пакет")
        self.soft = bool(p["soft"])
        # the detectors' strengths in force from each moment (review UX-ui U12: live): (tau from, value, early) — early:
        # set before any signal reached the plane, so the rule saw that value alone
        self.det_hist = {k: [(0.0, float(p[k]), True)] for k in ("mu_w", "mu_ms", "W0")}
        super().__init__(p, seed, emit)
        # the world's parameters are this world's own: v11's fixed path mark and flux are not among them (the header's
        # parameters seed the player's «new world» form; with them a new world without a scenario was refused, «нет
        # параметра «mark»», found while processing review UX-ui U12)
        self.params = {k: v for k, v in self.params.items() if k in SCHEMA.by_id}
        g = self.g
        self.z_lead = 0.0 if self.free else self.geo.z_src
        self.D = float(self.zL - self.z_lead)          # the flight from the leading packet's centre to the plane
        self.t0 = self.D / AP.V0_SPEED                 # its classical time at the mean speed
        self.t_obs = self.t_end_est                    # the observation window ends here
        self.rec = {k: [] for k in ("tau", "J", "rho", "d2", "click")}
        self.sent = 0
        # the joint distribution: J(x, t) in time bins of tbin steps and x bins over the screen (the bins from the set-up's
        # t0, not from the window's end, which is a consequence of the run: review B4-5)
        self.tbin = max(1, int(math.ceil(self.t0 / (ROWS_PER_T0 * self.dt))))
        xs = g.axes[0]
        on = np.flatnonzero(self.on_screen)
        self.cols = max(1, int(math.ceil(len(on) / COLS_MAX)))
        self.col_lo = int(on[0])
        self.ncol = len(on) // self.cols
        self.col_x0 = float(xs[self.col_lo]) + 0.5 * (self.cols - 1) * g.d[0]
        self._jacc = np.zeros(g.shape[0])
        self._jn = 0
        self.rows = []
        self.rows_sent = 0
        self.curve_sent = 0
        # the soft detector: the same experiment with the absorbing potential as its screen
        self.det = None
        if self.soft:
            W0 = float(p["W0"]) * AP.E0
            self.W_d = self.W + AP.soft_detector(g, self.zL, W0, self.geo.edge)
            Hd = self._hamiltonian(self.live, g, self.W_d)
            self.det = S.SplitOperator(Hd, self.dt, track_absorbed=True, force_cpu=self.prop.device == "cpu",
                                       why="как основной прогон")
            self.psi_d = self.det.put(self._packet(Hd, g))
            iz0 = int(np.searchsorted(g.axes[1], self.zL - 5 * self.geo.edge))
            self.det_region = (slice(None), slice(iz0, None))
        self._arrival_static_checks()
        self.curves = self._initial_state_rules() if self.free else None

    # --- v11's hooks ---------------------------------------------------------------------------------------------------
    def _geometry(self, p):
        h = V11.H_OF[p["grid"]]
        layer = AP.screen_layer(*AP.k_range(self.pk, 3.0))
        if self.free:
            t_end = AP.leave_time(self.fg, float(p["L"]))
            return AP.FreeGeometry(p["L"], p["sigma_x"], p["sigma_z"], h, AP.rear(self.pk), t_end, edge=float(p["edge"]),
                                   layer=layer)
        return AP.SlitGeometry(p["a"], p["d"], p["w"], p["L"], p["sigma_x"], p["sigma_z"], h, edge=float(p["edge"]),
                               back=-AP.rear(self.pk), layer=layer)

    def _layer_k(self) -> np.ndarray:
        """The state's whole spectrum (+-3 standard deviations of each packet)."""
        lo, hi = AP.k_range(self.pk, 3.0)
        return np.linspace(max(lo, 0.05 * AP.K0), hi, 7)

    def _t_end_estimate(self) -> float:
        if self.free:  # the free flight in closed form: until all but 1e-4 has crossed the plane
            return 1.02 * AP.leave_time(self.fg, self.geo.L)
        geo = self.geo
        v_slow = min(k - 2 / (2 * s) for _, _, k, s in self.pk)  # hbar = m = 1
        return (abs(geo.z_src) - AP.rear(self.pk) + geo.L + 4 * geo.sz + 2 * geo.screen_half) / v_slow

    def _starts(self, N: int) -> np.ndarray:
        """Starts drawn from |psi0|^2 = chi(x)^2 |phi(z)|^2: x normal, z by the inverse of phi's cumulative
        distribution (closed form on 40001 points: interpolation error ~1e-7 of the width)."""
        z_lead = 0.0 if self.free else self.geo.z_src
        zz = np.linspace(AP.rear(self.pk) - 9 * self.geo.sz, 9 * self.geo.sz, 40001)
        rho = np.abs(self.fg.psi(zz, 0.0)) ** 2
        cdf = np.concatenate([[0.0], np.cumsum(0.5 * (rho[1:] + rho[:-1]) * np.diff(zz))])
        cdf /= cdf[-1]
        return np.column_stack([self.rng.normal(0.0, self.geo.sx, N), np.interp(self.rng.random(N), cdf, zz) + z_lead])

    def _packet(self, H, g) -> np.ndarray:
        z_lead = 0.0 if self.free else self.geo.z_src
        chi = np.exp(-g.axes[0] ** 2 / (4 * self.geo.sx ** 2))
        phi = self.fg.psi(g.axes[1] - z_lead, 0.0)
        psi = chi[:, None] * phi[None, :]
        return psi / math.sqrt(float(np.sum(np.abs(psi) ** 2)) * g.dV)

    def _widest_angle(self) -> float:
        if self.free:  # three standard deviations of the transverse momentum
            return math.atan(3.0 / (2 * self.geo.sx * AP.K0))
        return super()._widest_angle()

    def cost_estimate(self) -> float:
        pairs = self.t_end_est / self.pair
        per_point, per_particle = V11.RATES[self.prop.device]
        steps = 2 + (self.geo.h / self._companion_step()) ** 2 + (2 if self.soft else 0)
        return pairs * (self.g.size * steps * per_point + int(self.params["n_bohm"]) * per_particle)

    def _references(self, xs):
        return {} if self.free else super()._references(xs)

    def _record(self, psi, J, tau):
        g = self.g
        dx = float(g.d[0])
        pc, d = self.prop.plane(psi, 1, self.iL, V11.FLUX_ORDER)
        r = self.rec
        r["tau"].append(tau)
        r["J"].append(float(J.sum()) * dx)
        r["rho"].append(float(np.sum(np.abs(pc) ** 2)) * dx)
        r["d2"].append(float(np.sum(np.abs(d) ** 2)) * dx)
        self._jacc += J
        self._jn += 1
        if self._jn == self.tbin:
            seg = self._jacc[self.col_lo:self.col_lo + self.ncol * self.cols] / self._jn
            self.rows.append(seg.reshape(self.ncol, self.cols).mean(axis=1))
            self._jacc[:] = 0.0
            self._jn = 0
        if self.det is not None:
            self.psi_d = self.det.step(self.psi_d, 1)
            r["click"].append(self.det.absorbed_in(self.det_region))

    def advance(self, t_target):
        self.t = t_target
        tau_t = t_target / self.tunit
        while not self.done and self.tau + self.pair <= tau_t + 1e-12:
            self._pair()
            if not self.done and self.tau >= self.t_obs:
                self._finish("окно наблюдения закончилось")

    def set_live(self, values):
        from lfviz.errors import Refusal
        if self.det is None and "W0" in values and float(values["W0"]) != float(self.live["W0"]):
            raise Refusal("мягкого детектора в этом мире нет: его высоту W₀ менять не у чего",
                          "включите «Мягкий детектор» в форме нового мира")
        before = dict(self.live)
        signal = self._signal_so_far()
        out = super().set_live(values)
        if out == "без изменений":
            return out
        notes = []
        for k in ("mu_w", "mu_ms", "W0"):
            if self.live[k] == before[k]:
                continue
            early = self.tau == 0.0 or signal[k] < EARLY
            self.det_hist[k].append((self.tau, float(self.live[k]), early))
            what = "мягкий детектор" if k == "W0" else "правило " + ("Влодажа" if k == "mu_w" else "Маркевки–Шусса")
            notes.append(f"{what}: волна до детектора ещё не дошла (< 10⁻⁶ вероятности) — опыт как с новым значением с "
                         f"самого начала" if early else
                         f"{what}: до этого момента посчитано с прежним значением, дальше — с новым; сверка, которая "
                         f"предполагает одно значение на весь опыт, отключена")
        if self.det is not None:
            if self.live["W0"] != before["W0"]:
                self.W_d = self.W + AP.soft_detector(self.g, self.zL, float(self.live["W0"]) * AP.E0, self.geo.edge)
                self._soft_grid_check()
            Hd = self._hamiltonian(self.live, self.g, self.W_d)
            self.det.rebuild(V=Hd.V, W=Hd.W, keep=())
        return out + ("; " + "; ".join(notes) if notes else "")

    def _signal_so_far(self) -> dict:
        """What has reached the detectors by now, per live detector parameter: the exponential rules' unit-strength
        intensities integrated so far (v0 ∫∫|ψ|² dx dt and (v0/k0²) ∫∫|∂ψ/∂z|² dx dt on the plane), and the probability
        the soft detector's run took or holds behind z = L − 5·edge."""
        r, dt = self.rec, self.dt
        out = {"mu_w": AP.V0_SPEED * float(np.sum(r["rho"])) * dt,
               "mu_ms": AP.V0_SPEED / AP.K0 ** 2 * float(np.sum(r["d2"])) * dt, "W0": 0.0}
        if self.det is not None:
            out["W0"] = float(self.det.absorbed_in(self.det_region)) + \
                float(self.det.density(self.psi_d)[self.det_region].sum()) * self.g.dV
        return out

    def _strength(self, key, tau) -> np.ndarray:
        """A detector parameter at the run's sample times: the value in force when each sample was recorded (a sample
        at the moment of a change belongs to the value before it)."""
        h = self.det_hist[key]
        vals = np.array([v for _, v, _ in h])
        if len(h) == 1:
            return np.full(len(tau), vals[0])
        return vals[np.searchsorted(np.array([t for t, _, _ in h[1:]]), np.asarray(tau), side="left")]

    def _one_value(self, key):
        """The value a detector parameter had for the whole signal (every change made before the signal reached it),
        or None when it changed while the signal arrived."""
        h = self.det_hist[key]
        return h[-1][1] if all(early for _, _, early in h) else None

    def _screen(self):
        super()._screen()
        self._send_arrival()

    # --- the rules -----------------------------------------------------------------------------------------------------
    def _series(self):
        """Every rule's density on the run's sample times (units of the computation), from what was recorded."""
        r = self.rec
        tau = np.asarray(r["tau"])
        dt = self.dt
        J = np.asarray(r["J"])
        out = {"tau": tau, "flux": J}
        C = self._cum_flux(tau, J)
        if self.free:  # Bohm's first-arrival law in free flight: the running maximum of the flux's integral
            A = np.maximum.accumulate(np.maximum(C, 0.0))
            out["bohm_law"] = np.diff(np.concatenate([[0.0], A])) / dt
        v0, k0 = AP.V0_SPEED, AP.K0
        for key, lam in (("wlodarz", DET.wlodarz_intensity(np.sqrt(np.asarray(r["rho"])), self._strength("mu_w", tau) * v0)),
                         ("ms", DET.marchewka_schuss_intensity(np.sqrt(np.asarray(r["d2"])),
                                                               self._ms_lambda0p(self._strength("mu_ms", tau))))):
            Lam = np.cumsum(lam) * dt  # the first click falls in step i with probability e^{-Lam_{i-1}} - e^{-Lam_i}
            surv = np.exp(-Lam)
            out[key] = np.diff(np.concatenate([[1.0], surv])) * -1 / dt
            out[key + "_none"] = float(surv[-1]) if len(surv) else 1.0
        if self.det is not None:
            clicks = np.asarray(r["click"])
            out["soft"] = np.diff(np.concatenate([[0.0], clicks])) / dt
        return out

    @staticmethod
    def _cum_flux(tau, J):
        """int_0^t J by the trapezoid rule from J(0) = 0 (review B4-7: the rectangle sum ran dt/2 ahead)."""
        if not len(J):
            return np.zeros(0)
        return cumulative_trapezoid(np.concatenate([[0.0], J]), np.concatenate([[0.0], tau]))

    def _send_arrival(self):
        n = len(self.rec["tau"])
        if n == self.sent and len(self.rows) == self.rows_sent:
            return
        s = self._series()
        sl = slice(self.sent, n)
        keys = [k for k in ("flux", "bohm_law", "wlodarz", "ms", "soft") if k in s]
        blobs = {k: np.asarray(s[k][sl], np.float32) for k in keys}
        blobs["tau"] = np.asarray(s["tau"][sl], np.float32)
        if len(self.rows) > self.rows_sent:
            blobs["rows"] = np.asarray(self.rows[self.rows_sent:], np.float32).ravel()
        meta = {"type": "arrival", "t": self.t, "from": self.sent, "n": n - self.sent, "keys": keys,
                "row_from": self.rows_sent, "row_n": len(self.rows) - self.rows_sent, "ref_n": 0}
        if self.curves is not None:  # the initial state's rules, revealed as the run's time reaches them (B4-5)
            c = self.curves
            upto = int(np.searchsorted(c["tau"], self.tau, side="right"))
            if upto > self.curve_sent:
                for k_ in ("tau", "abk", "sc", "abr"):
                    blobs["ref_" + k_] = np.asarray(c[k_][self.curve_sent:upto], np.float32)
                meta["ref_n"] = upto - self.curve_sent
                self.curve_sent = upto
        self.sent, self.rows_sent = n, len(self.rows)
        self._msg(meta, blobs)

    @staticmethod
    def _ms_lambda0p(mu):
        """Das & Struyve's lambda0' for the strength mu_ms: (4 lambda0' eps / pi) |d psi/dz|^2 = mu (v0 / k0^2)
        |d psi/dz|^2 with eps = hbar/m = 1, so lambda0' = pi mu v0 / (4 k0^2) = mu / 8 in these units."""
        return math.pi * np.asarray(mu, float) * AP.V0_SPEED / (4 * AP.K0 ** 2)

    def _initial_state_rules(self):
        """Free flight: the rules that are functionals of the initial state (ABK, semiclassical, absorbing boundary),
        computed from its momentum amplitude for the flight D from the leading packet to the plane."""
        lo, hi = AP.k_range(self.pk)
        k = np.linspace(lo, hi, K_N)
        phi = self.fg.phi(k)
        tau = np.linspace(0.0, self.t_obs, CURVE_N)
        kappa = float(self.params["kappa"]) * AP.K0
        abk = AT.kijowski(phi, k, self.D, tau)
        tn = np.linspace(-self.t_obs, 0.0, 801)
        abk_neg = float(np.trapezoid(AT.kijowski(phi, k, self.D, tn), tn))
        # the semiclassical rule in k, exact: bin averages of its cumulative distribution (review B4-2: samples of its
        # density alias on a train); k sampled well below 2 pi / the state's extent
        extent = max(z0 for _, z0, _, _ in self.pk) - AP.rear(self.pk) + 10 * self.geo.sz
        nk = max(20001, int(math.ceil(40 * (hi - lo) * extent / (2 * math.pi))))
        self.sc_rule = AT.Semiclassical(self.fg.phi, self.D, lo, hi, nk)
        h = tau[1] - tau[0]
        sc = self.sc_rule.bin_density(np.concatenate([[tau[0] - 0.5 * h], tau + 0.5 * h]))
        abr = DET.abr_density(phi, k, self.D, kappa, tau)
        return {"tau": tau, "abk": abk, "sc": sc, "abr": abr, "abk_neg": abk_neg,
                "abr_total": DET.abr_total(phi, k, kappa), "k_lo": lo}

    # --- checks --------------------------------------------------------------------------------------------------------
    def _arrival_static_checks(self):
        g = self.g
        # the run starts from the state the rules are computed for: its longitudinal momentum distribution
        psi0 = self.prop.get(self.psi)
        chi = np.exp(-g.axes[0] ** 2 / (4 * self.geo.sx ** 2))
        chi /= math.sqrt(float(np.sum(chi ** 2)) * g.d[0])
        phi_z = (chi[None, :] @ psi0)[0] * g.d[0]
        z = g.axes[1] - self.z_lead
        kz = 2 * math.pi * np.fft.fftfreq(len(z), g.d[1])
        ft = np.fft.fft(phi_z) * g.d[1] / math.sqrt(2 * math.pi) * np.exp(-1j * kz * z[0])
        P_run, P_cf = np.abs(ft) ** 2, np.abs(self.fg.phi(kz)) ** 2
        dev = float(np.max(np.abs(P_run - P_cf)) / P_cf.max())
        self._check("arr_state", "Начальное состояние: распределение импульса вдоль полёта против точного", dev, None, "",
                    ok=dev < 1e-3, group="Время прихода",
                    note="|ψ̃(k_z)|² начальной волны прогона (БПФ по z проекции на поперечный пакет) против замкнутой "
                         "формы суперпозиции гауссовых пакетов, по которой считаются правила; в долях пика; окно "
                         "обрезает хвосты амплитуды (e^(−(z/2σz)²) ~ 10⁻⁴ у краёв), цель < 10⁻³")
        if self.det is not None:
            self._soft_grid_check()

    def _soft_grid_check(self):
        """The soft detector's absorber resolved by the grid, for the highest W₀ it has had (live since U12)."""
        g = self.g
        W0 = max(v for _, v, _ in self.det_hist["W0"]) * AP.E0
        kmax = math.pi / g.d[1]
        k_hi = AP.k_range(self.pk, 6.0)[1]
        q = (k_hi ** 4 + 4 * W0 ** 2) ** 0.25
        self._check("soft_grid", "Мягкий детектор разрешён сеткой: |q|/k_max", q / kmax, None, "",
                    ok=q / kmax < 0.8 and self.geo.edge >= g.d[1] * (1 - 1e-9), group="Расчёт",
                    note=f"волна в поглотителе: q = √(k² + 2imW₀/ħ²), |q| = {q:.3g} λ⁻¹ при k = {k_hi:.3g} λ⁻¹ "
                         f"(верх спектра) и наибольшей высоте W₀ = {W0 / AP.E0:g} E₀, что была в опыте, k_max = π/шаг "
                         f"= {kmax:.3g} λ⁻¹; нужно < 0,8")

    def _finish(self, why):
        if self._jn:  # the last, partial time bin of J(x, t) (review B4-8)
            seg = self._jacc[self.col_lo:self.col_lo + self.ncol * self.cols] / self._jn
            self.rows.append(seg.reshape(self.ncol, self.cols).mean(axis=1))
            self._jacc[:] = 0.0
            self._jn = 0
        self._send_arrival()
        super()._finish(why)
        s = self._series()
        res = {"t0_units": self.t0, "D": self.D, "tau_obs": self.t_obs,
               "none": {"wlodarz": s["wlodarz_none"], "ms": s["ms_none"]}}
        J, tau, dt = s["flux"], s["tau"], self.dt
        res["flux_total"] = float(J.sum() * dt)
        res["backflow"] = float(np.clip(-J, 0, None).sum() * dt)
        if self.det is not None:
            clicks = self.rec["click"][-1] if self.rec["click"] else 0.0
            rem = float(self.det.density(self.psi_d)[self.det_region].sum()) * self.g.dV
            res["soft"] = {"clicks": clicks, "inside": rem, "reflected": 1.0 - clicks - rem}
        if self.curves is not None:
            res["abk_neg"] = self.curves["abk_neg"]
            res["abr_total"] = self.curves["abr_total"]
        res["rules"] = self._rule_stats(s)
        self.arrival_final = res
        self._msg({"type": "arrival_result", "t": self.t, **res})
        self._arrival_checks(s, res)

    def _rule_stats(self, s) -> dict:
        """Each rule's probability within the observation window, its mean arrival time and spread (units of the
        computation): sums over the run's steps, the trapezoid rule over the curves of the initial state, the
        ensemble's hit times."""
        def moments(tau, P, w):
            tot = float(np.sum(P * w))
            if tot <= 0:
                return {"total": tot, "mean": None, "sd": None}
            m = float(np.sum(tau * P * w) / tot)
            return {"total": tot, "mean": m, "sd": float(math.sqrt(max(np.sum((tau - m) ** 2 * P * w) / tot, 0.0)))}
        out = {}
        for k in ("flux", "bohm_law", "wlodarz", "ms", "soft"):
            if k in s and len(s[k]):
                out[k] = moments(s["tau"], s[k], self.dt)
        if self.curves is not None:
            c = self.curves
            w = np.gradient(c["tau"])  # trapezoid weights on the uniform grid, up to the half-weights at the ends
            w[0] *= 0.5
            w[-1] *= 0.5
            for k in ("abk", "abr"):
                out[k] = moments(c["tau"], c[k], w)
            tot, mean, sd = self.sc_rule.moments(float(c["tau"][-1]))  # exact in k (B4-2)
            out["sc"] = {"total": tot, "mean": mean, "sd": sd}
        hits = self.hit_t[self.fate == 1] / self.tunit
        out["bohm"] = {"total": len(hits) / len(self.fate), "mean": float(hits.mean()) if len(hits) else None,
                       "sd": float(hits.std()) if len(hits) > 1 else None}
        return out

    def _arrival_checks(self, s, res):
        tau, J, dt = s["tau"], s["flux"], self.dt
        grp = "Время прихода"
        n_tot = len(self.fate)
        if self.free:
            Jx = self.fg.current(self.D, tau)
            dev = float(np.max(np.abs(J - Jx)) / np.max(np.abs(Jx)))
            bx = float(np.clip(-Jx, 0, None).sum() * dt)
            self._check("arr_flux_exact", "Поток через плоскость против точной свободной эволюции", dev, None, "",
                        ok=dev < 1e-2, group=grp,
                        note=f"J(t) = ∫ j_z(x, L, t) dx прогона против тока точного решения (суперпозиция гауссовых "
                             f"пакетов); наибольшее отличие в долях пика; обратный ток: {res['backflow']:.3g} "
                             f"(точно {bx:.3g}) вероятности; цель < 1 % (как сверка «Сетка и шаг»)")
            rho_x = np.abs(self.fg.psi(self.D, tau)) ** 2
            rho = np.asarray(self.rec["rho"])
            dev = float(np.max(np.abs(rho - rho_x)) / rho_x.max())
            self._check("arr_plane_psi", "ψ на плоскости детектора против точного: ∫|ψ(x, L, t)|² dx", dev, None, "",
                        ok=dev < 1e-2, group=grp,
                        note="вход экспоненциальных правил (Влодаж, Маркевка–Шусс); наибольшее отличие в долях пика")
            if self.curves is not None:
                c = self.curves
                got = float(np.trapezoid(c["abr"], c["tau"]))
                self._check("arr_abr_identity", "Поглощающая граница: квадратура кривой — ∫Π dt за окно против "
                                                "∫|ψ̃|²(1 − R_k) dk", got, c["abr_total"], "", tol=2e-3, group=grp,
                            note=f"обе стороны — из формулы изображений (тождество Парсеваля), так что сверка проверяет "
                                 f"квадратуры по t и k на окне наблюдения, а не само правило (R_k = (k − κ)²/(k + κ)², "
                                 f"κ = {float(self.params['kappa']):g} k₀; за окном остаётся < 1e-4). Само правило "
                                 f"проверено в тестах движка против независимого решения Кранка–Николсон с условием "
                                 f"Робена (review B4-9)")
                tot = float(np.trapezoid(c["abk"], c["tau"]))
                self._check("arr_abk_norm", "Ааронов–Бом–Киёвский: ∫Π dt при t > 0 и вес t < 0", tot + c["abk_neg"], 1.0,
                            "", tol=2e-3, info=True, group=grp,
                            note=f"при t > 0 (окно) — {tot:.6f}, при t < 0 — {c['abk_neg']:.2e} (по Das и Nöth — "
                                 f"вероятность «не обнаружена»); сумма должна быть 1")
        hits_t = self.hit_t[self.fate == 1] / self.tunit
        n = len(hits_t)
        if n >= 20:
            C = self._cum_flux(tau, J)
            law = np.maximum.accumulate(np.maximum(C, 0.0)) if self.free else self._cum_flux(tau, np.clip(J, 0, None))
            F = law / law[-1]
            emp = np.searchsorted(np.sort(hits_t), tau, side="right") / n
            Dks = float(np.max(np.abs(emp - F)))
            crit = 1.95 / math.sqrt(n)
            self._check("arr_bohm_times", "Времена первого прихода частиц Бома против закона (Колмогоров–Смирнов)", Dks,
                        None, "", ok=Dks < crit, group="Бом",
                        note=(f"{n} частиц из {n_tot}; " + (
                            "свободный полёт: закон первого прихода — бегущий максимум ∫J dt (траектории не "
                            "пересекаются); " if self.free else
                            "за щелями: поток в экран (траектории, вернувшиеся через плоскость, не учтены); ")
                            + f"критическое значение 99,9 %: 1,95/√n = {crit:.3g}"))
        if self.det is not None and self.free and self._one_value("W0") is None:
            self._check("arr_soft_reflection", "Мягкий детектор: отражённая доля против стационарной теории", None,
                        None, "", info=True, group=grp,
                        note="высота W₀ менялась, когда волна уже была у детектора: стационарная теория для одной "
                             "высоты к этому опыту не применима (изменения — в событиях)")
        elif self.det is not None and self.free:
            Rref = self._soft_reflection_reference()
            Rrun = res["soft"]["reflected"]
            tol = SOFT_REL_TOL * Rref + 2e-4
            self._check("arr_soft_reflection", "Мягкий детектор: отражённая доля против стационарной теории", Rrun, Rref,
                        "", tol=tol / max(Rref, 1e-12), ok=abs(Rrun - Rref) <= tol, group=grp,
                        note=f"прогон: 1 − поглощённое детектором − оставшееся в нём; теория: R(k) матриц переноса "
                             f"для профиля −iW(z) детектора (ступень W₀ = {self._one_value('W0'):g} E₀ с краем "
                             f"{self.geo.edge:g} λ и поглощающий слой за ней), усреднённое по |ψ̃(k)|²; резкая ступень "
                             f"дала бы {self._sharp_reflection():.3g}; допуск 10 % + 2e-4 (не долетевшее за окно)")
        if self.det is not None:
            lost = abs(self.det.norm(self.psi_d) + float(self.det.absorbed().sum()) - 1.0)
            self._check("arr_det_norm", "Прогон с мягким детектором: норма + поглощённое = 1", lost, 0.0, "", tol=1e-9,
                        ok=lost < 1e-9, group="Расчёт")
        if self.free and self.params["state"] == "train":
            self._train_check(s)

    def _soft_reflection_reference(self) -> float:
        lo, hi = AP.k_range(self.pk)
        k = np.linspace(max(lo, 1e-3), hi, 1201)
        W0, e = self._one_value("W0") * AP.E0, self.geo.edge
        Wl = self.geo.screen_W * AP.E0
        gap = AP.AP11.SCREEN_GAP
        width = float(self.g.axes[1][-1] - self.zL) - gap

        def prof(z):  # the step at the plane, the screen's layer from SCREEN_GAP behind it
            z = np.asarray(z, float)
            return AP.soft_profile(W0, e)(z) - 1j * Wl * np.clip((z - gap) / width, 0.0, 1.0) ** 2
        R = []
        for nsl in (1500, 3000):
            _, Rk = transmission_profile(0.5 * k * k, prof, -10 * e, gap + width, nsl, return_r=True)
            R.append(Rk)
        Rk = R[1] + (R[1] - R[0]) / 3  # Richardson: the staircase's error falls as 1/n^2
        w = np.abs(self.fg.phi(k)) ** 2
        return float(np.trapezoid(w * Rk, k) / np.trapezoid(w, k))

    def _sharp_reflection(self) -> float:
        lo, hi = AP.k_range(self.pk)
        k = np.linspace(max(lo, 1e-3), hi, 1201)
        w = np.abs(self.fg.phi(k)) ** 2
        return float(np.trapezoid(w * DET.step_reflection(k, self._one_value("W0") * AP.E0), k) / np.trapezoid(w, k))

    def _train_check(self, s):
        """Das & Struyve 2021: with the train, the flux shows N equal peaks; Wlodarz's rule damps them by exp(-mu / N) each."""
        N, sep = int(self.params["n_train"]), float(self.params["sep"])
        tau = s["tau"]
        t_j = (self.D + sep * np.arange(N)) / AP.V0_SPEED
        half = 0.5 * sep / AP.V0_SPEED
        peaks = {k: np.array([s[k][(tau > tj - half) & (tau < tj + half)].max() for tj in t_j]) for k in ("flux", "wlodarz")}
        r_flux = peaks["flux"][1:] / peaks["flux"][:-1]
        r_w = peaks["wlodarz"][1:] / peaks["wlodarz"][:-1]
        mu = self._one_value("mu_w")
        if mu is None:
            self._check("arr_train", "Цепочка пакетов: пики правила Влодажа гаснут как e^(−λ₀/N)", None, None, "",
                        info=True, group="Время прихода",
                        note="сила λ₀ менялась, когда цепочка уже приходила: сравнение с e^(−λ₀/N) для одной силы к "
                             "этому опыту не применимо (изменения — в событиях)")
            return
        expect = math.exp(-mu / N)
        dev = float(np.max(np.abs(r_w / expect - 1)))
        self._check("arr_train", "Цепочка пакетов: пики правила Влодажа гаснут как e^(−λ₀/N)", dev, None, "", info=True,
                    group="Время прихода",
                    note=f"отношения соседних пиков: поток {', '.join(f'{v:.3f}' for v in r_flux)} (ожидается ≈ 1 с "
                         f"поправкой на расплывание), Влодаж {', '.join(f'{v:.3f}' for v in r_w)} против "
                         f"e^(−λ₀/N) = {expect:.3f} (Das & Struyve 2021, ур. 24–25); наибольшее отличие {dev:.2%}")

    # --- the scene -------------------------------------------------------------------------------------------------------
    def engine_modules(self):
        mods = ["core.quantum.schrodinger_nd", "core.quantum.schrodinger1d", "core.quantum.transfer",
                "core.quantum.particles", "core.backend", "theories.interpretations.bohm",
                "theories.interpretations.arrival_times", "theories.models.detection"]
        if not self.free:
            mods += ["theories.approx.paraxial", "theories.approx.kirchhoff"]
        return mods

    def _plate_obj(self):
        o = super()._plate_obj()
        if self.free:
            o["visible"] = False
            o["label"] = "Пластины нет: свободный полёт"
        return o

    def header(self):
        hd, extra = super().header()
        title = "Время прихода частицы: правила в 2D"
        hd["title"] = title
        hd["text"] = ("Пакет частицы летит к плоскости детектора — свободно или через две щели. Прогон решает уравнение "
                      "Шрёдингера на плоскости (x, z) и записывает на плоскости детектора ток, волну и её производную в "
                      "каждый момент. Из них и из начального состояния прогон считает распределение времени прихода по "
                      "каждому правилу: квантовый поток, первые прибытия частиц Бома, Ааронов–Бом–Киёвский, "
                      "полуклассическое, поглощающая граница, экспоненциальные правила Влодажа и Маркевки–Шусса и "
                      "мягкий детектор (второй прогон с поглощающим потенциалом). Квантовая механика не задаёт одно "
                      "правило: где они расходятся, опыт мог бы их различить.")
        for o in hd["scene3d"]["objects"]:
            if o["id"] == "screen":
                o["label"] = f"Плоскость детектора (z = {self.geo.L:g} λ): поток, накопленный за опыт"
        approx = list(hd["approximations"])
        if self.free:
            approx = [a for a in approx if not a.startswith(("стенка", "щели бесконечно длинные"))]
            approx.insert(0, "ничто не зависит от y: уравнение Шрёдингера решается на плоскости (x, z), трёхмерная "
                             "волна — точное произведение ψ(x, z, t)·η(y, t) со свободным гауссовым η (замкнутая форма)")
            approx.append("АБК, полуклассическое и поглощающая граница — для свободного полёта и разделимого состояния "
                          "(поперечный пакет — наблюдатель); экспоненциальные правила обобщены на плоскость как поток "
                          "Пуассона с плотностью λ(x, t), их время — интеграл по x")
        approx.append("детектор плоскости в основном прогоне — поглощающий слой без отражения (идеальная плоскость "
                      "прихода); правила «детекторов» считаются отдельно")
        hd["approximations"] = approx
        rules = ["flux", "bohm"] + (["bohm_law", "abk", "sc", "abr"] if self.free else []) + ["wlodarz", "ms"] + \
                (["soft"] if self.soft else [])
        hd["arrival"] = {"scene": "free" if self.free else "slits", "state": self.params["state"], "t0_units": self.t0,
                         "D": self.D, "dt": self.dt, "rules": rules,
                         "rows": {"tbin_units": self.tbin * self.dt, "x0": self.col_x0, "dx": float(self.g.d[0]) * self.cols,
                                  "n": self.ncol},
                         "params": {k: self.params[k] for k in ("kappa", "mu_w", "mu_ms", "W0", "n_train", "sep")}}
        hd["geometry"]["scene"] = hd["arrival"]["scene"]
        return hd, extra


VIZ = {
    "id": "v12_arrival_times_2d",
    "title": "Время прихода частицы: правила в 2D",
    "summary": ("Когда частица придёт к детектору? Пакет летит к плоскости свободно или через две щели; прогон решает "
                "уравнение Шрёдингера и по записи на плоскости и начальному состоянию считает распределение времени "
                "прихода по квантовому потоку, траекториям Бома, Ааронову–Бому–Киёвскому, полуклассическому правилу, "
                "поглощающей границе, правилам Влодажа и Маркевки–Шусса и мягкому детектору."),
    "purpose": ("Квантовая механика не задаёт время прихода однозначно; мир показывает, где правила совпадают (вдали от "
                "источника) и где расходятся: у источника, на цепочке пакетов, при обратном токе, за двумя щелями."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
