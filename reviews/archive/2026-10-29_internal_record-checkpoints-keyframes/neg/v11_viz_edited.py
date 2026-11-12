# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v11: the double slit in 2-D without the paraxial approximation (a wrapper over lfphys; plan P14.4, on P6 and P10).

A wave packet of a massive particle runs at a plate with two slits (a wall of finite height and thickness, long along
y: the 2-D model in the plane (x, z) is the exact reduction of that 3-D set-up) and on to a detecting screen. The run
solves the time-dependent Schroedinger equation on the whole plane (lfphys.core.quantum.schrodinger_nd: split
operator, on GPU 0 where it pays): reflection by the plate, the waves inside the slits, diffraction to any angle; the
screen and the window's edges absorb (detectors). The pattern on the screen is the probability that flows into it,
accumulated as the wave arrives. An ensemble of particles follows the Bohm trajectories of the same wave
(lfphys.theories.interpretations.bohm: an interpretation; each trajectory starts at a position drawn from |psi|^2 and
is labelled by the slit it went through); their hits build up next to the computed pattern.

The set-up is live: a slit can be closed or opened at any moment, a path mark switched on in slit B (the particle's
spin turned by a field inside the slit: which-path information carried by the particle itself), an Aharonov-Bohm flux
set between the slits (charged particles). A change acts from that moment on: it changes nothing for parts of the
wave that have already passed.

Checks: norm + absorbed = 1; the time step (a companion run with 2 dt); the flux into the screen against the
probability the screen absorbs; the Bohm hits against the computed pattern (equivariance); the symmetry of a
symmetric set-up and trajectories that do not cross its axis; for information, the paraxial (Fresnel-Kirchhoff) and
the Kirchhoff-Rayleigh-Sommerfeld patterns, the visibility against the two-path prediction, the fractions reflected,
detected and lost.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import backend
from lfphys.core.quantum import particles
from lfphys.core.quantum import schrodinger_nd as S
from lfphys.core.quantum.schrodinger1d import FreeGaussians
from lfphys.theories.interpretations import bohm
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

from .engine import apparatus as AP

GRIDS = [("coarse", "грубая: λ/5"), ("normal", "обычная: λ/6"), ("fine", "мелкая: λ/8")]
H_OF = {"coarse": 1 / 5, "normal": 1 / 6, "fine": 1 / 8}
DT_E0 = 0.1            # time step: E0 dt = 0.1 rad per step at the mean energy
COMP_GRID = 1.2        # the companion's grid step relative to the run's (and its time step is 2 dt)
CONTROL_N = 100        # Bohm particles integrated again, more tightly, to measure the trajectories' accuracy
CONTROL_TIGHT = 4      # how much tighter (the difference then estimates the ensemble's error to ~25 %)
BOHM_P95 = 0.05        # the target for 95 % of the control's hits (lambda)
# measured rates (2026-10-28, whole runs: RTX 2080 Ti, the narrow preset with 100 and 2000 particles; the container's
# CPU with OMP 2, the tests' small geometry with 100 and 1000): seconds per grid point per split step (the flux and
# the images included), seconds per Bohm particle per pair of steps (its error-controlled steps near nodes included)
RATES = {"gpu": (1.9e-8, 1.0e-5), "cpu": (3.0e-7, 4.2e-5)}
COST_LIMIT = {"gpu": 600.0, "cpu": 3600.0}  # seconds: GPU 0 well below the host's ~18 min hang; on the CPU an hour
WAVE_EVERY = 16        # pairs of steps between images of the wave (accumulative "wave" messages: the record keeps every
                       # one, so a viewer who scrolls back sees the wave of that moment; frames are thinned)
TRACK_EVERY = 3        # pairs of steps between points of the drawn trajectories
SCREEN_EVERY = 25      # pairs of steps between updates of the screen's pattern
END_NORM = 1e-4        # the world's wave is done when less than this is left in the window
SCREEN_FLOOR = 1e-10   # probability on the screen below which its "pattern" is round-off (|flux| ~ 1e-16 per cell)
MAX_PX = 200           # the wave's image: at most this many pixels along an axis
NY_VOLUME = 48         # samples of the y-factor |eta(y, t)|^2 sent with each image (the 3-D volume's depth along y)
NY_SCREEN = 48         # y bins of the screen's pattern P(x, y)
Y_MOTION_TOL = 1e-6    # the hits' y against the guidance equation integrated in eta, in widths of eta at the hit (C1-11)
SCREEN_COLS = 128      # x columns of its 3-D picture (the pattern P(x) keeps the grid's resolution)
FLUX_ORDER = 32        # the screen's current by a centred difference of this order: relative error (16!)^2/33! (k dz)^32,
                       # 3e-6 at the top of a packet's spectrum on the coarse grid (k dz = 1.4, lambda/5); order 16 lost
                       # 1e-3 there (v12: the flux of a whole free packet came out 1e-4 too large), order 8 lost 2e-3 at
                       # lambda/6 (measured: the flux fell 0.16 % short)


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("particle", "Частица", "select", "electron", group="Частица",
       options=[("electron", "электрон"), ("neutron", "нейтрон"), ("he4", "атом ⁴He"), ("c60", "фуллерен C₆₀")]),
    _p("lam_pm", "Длина волны де Бройля λ", "float", 100.0, unit="пм", group="Частица", min=20.0, max=5000.0, log=True,
       help="задаёт физический масштаб: все длины опыта — в λ"),
    _p("a", "Ширина щели a", "float", 2.0, unit="λ", group="Пластина", min=0.5, max=20.0),
    _p("d", "Расстояние между щелями d (центр — центр)", "float", 8.0, unit="λ", group="Пластина", min=1.0, max=60.0),
    _p("w", "Толщина пластины", "float", 2.0, unit="λ", group="Пластина", min=0.5, max=10.0),
    _p("V0", "Высота стенки", "float", 4.0, unit="E₀", group="Пластина", min=1.5, max=8.0,
       help="потенциальная энергия частицы в материале пластины, в единицах её кинетической энергии E₀"),
    _p("edge", "Ширина краёв стенки и поля метки", "float", 0.2, unit="λ", group="Пластина", min=0.1, max=1.0,
       help="потенциал стенки и поле метки нарастают на этой длине (tanh); не меньше шага сетки"),
    _p("L", "Расстояние до экрана", "float", 50.0, unit="λ", group="Экран", min=5.0, max=200.0),
    _p("sigma_x", "Пакет: ширина поперёк σx", "float", 8.0, unit="λ", group="Пакет", min=1.0, max=40.0),
    _p("sigma_z", "Пакет: длина вдоль σz", "float", 5.0, unit="λ", group="Пакет", min=2.0, max=20.0,
       help="разброс импульса Δk/k = 1/(4π σz/λ)"),
    _p("sigma_y", "Пакет: ширина вдоль y σy", "float", 3.0, unit="λ", group="Пакет", min=0.5, max=40.0,
       help="вдоль щелей ничего не меняется, поэтому волна — точное произведение ψ(x, z, t)·η(y, t): η — свободный "
            "гауссов пакет, он только расплывается"),
    _p("mark", "Метка пути в щели B", "select", "none", group="Метка пути и наблюдатель",
       options=[("none", "нет"), ("spin", "спин частицы: поле в щели B поворачивает спин ½ (электрон, нейтрон)"),
                ("detector", "наблюдатель: детектор пути у щели B (двухуровневый, модель Энглерта; любая частица)")],
       help="волна получает вторую компоненту: спин частицы или состояние детектора; пока частица в щели B, она "
            "поворачивается на угол θ — путь помечен, интерференция гаснет (в модели двух путей как |cos(θ/2)|)"),
    _p("grid", "Сетка", "select", "normal", group="Расчёт", options=GRIDS),
    _p("n_bohm", "Частиц Бома в ансамбле", "int", 2000, group="Траектории Бома", min=100, max=8000),
    _p("n_tracks", "Из них рисовать траекторий", "int", 120, group="Траектории Бома", min=10, max=400),
    _p("slit_a", "Щель A (x = −d/2) открыта", "bool", True, group="Установка", live=True),
    _p("slit_b", "Щель B (x = +d/2) открыта", "bool", True, group="Установка", live=True),
    _p("mark_deg", "Метка в щели B: поворот θ", "float", 0.0, unit="°", group="Установка", min=0.0, max=360.0,
       live=True, show_if={"mark": ["spin", "detector"]},
       help="поворот спина (или состояния детектора) основной поперечной моды щели B при средней скорости; связь "
            "откалибрована по этой моде: 0 — пути не различить, 180° — основная мода помечена полностью; часть волны "
            "поворачивается иначе (вероятно, высшие моды узкой щели и разброс скоростей), поэтому полосы гаснут не до нуля"),
    _p("flux", "Поток Ааронова–Бома между щелями Φ/Φ₀", "float", 0.0, group="Установка", min=-2.0, max=2.0,
       live=True, help="тонкая трубка магнитного потока внутри пластины между щелями; только заряженные частицы"),
], presets={
    "narrow": {"label": "Узкие щели a = 2λ: дифракция на большие углы, параксиальная теория не годится", "params": {}},
    "wide": {"label": "Щели a = 6λ в тонкой высокой стенке: ближе к параксиальной теории (отличие ~λ/a)",
             "params": {"a": 6.0, "d": 12.0, "w": 0.5, "V0": 8.0, "L": 72.0, "sigma_x": 15.0}},
    "mark180": {"label": "Метка пути: спин в щели B повёрнут на 180° — полосы почти гаснут, траектории пересекают ось",
                "params": {"mark": "spin", "mark_deg": 180.0}},
    "mark90": {"label": "Частичная метка: поворот на 90°, видность cos 45°",
               "params": {"mark": "spin", "mark_deg": 90.0}},
    "observer": {"label": "Наблюдатель у щели B: детектор пути (θ = 180°) у атома ⁴He без спина — полосы почти гаснут",
                 "params": {"particle": "he4", "mark": "detector", "mark_deg": 180.0}},
    "ab": {"label": "Эффект Ааронова–Бома: поток Φ₀/2 между щелями сдвигает полосы на полпериода",
           "params": {"flux": 0.5}},
    "single": {"label": "Одна щель (B закрыта): огибающая без полос", "params": {"slit_b": False}},
})


class Simulation(BaseSimulation):
    label_slits = True                 # Bohm particles are labelled by the slit they cross (v12's free flight: no plate)
    BACK_LABEL = "отражено пластиной"  # what is absorbed before the plate's middle plane

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        self.part = particles.make(p["particle"], "lambda", float(p["lam_pm"]) * 1e-12)
        self.charged = self.part.charge != 0
        if abs(float(p["flux"])) > 0 and not self.charged:
            raise ValueError("поток Ааронова–Бома действует только на заряженные частицы (электрон)")
        self.mark = p.get("mark", "none")
        if float(p["mark_deg"]) and self.mark == "none":
            raise ValueError("метка пути выключена: выберите в «Метка пути в щели B» спин частицы или детектор")
        if self.mark == "spin" and self.part.internal != "spin":
            raise ValueError(f"у частицы «{self.part.label}» нет спина ½ (внутреннего состояния в движке нет): метка "
                             f"пути спином для неё не определена — выберите электрон или нейтрон, или детектор пути")
        self.geo = self._geometry(p)
        if self.geo.edge < self.geo.h * (1 - 1e-9):
            raise ValueError(f"края стенки ({self.geo.edge:g} λ) уже шага сетки ({self.geo.h:.3g} λ): сетка их не "
                             f"разрешает — выберите сетку мельче или края шире")
        self.g = self.geo.grid()
        g = self.g
        self.tunit = AP.time_unit(self.part.mass, self.part.lam)  # seconds of the world per unit of computation
        self.dt = DT_E0 / AP.E0
        self.pair = 2 * self.dt
        # the wave's second component: the particle's spin, or the state of the which-path detector at slit B (an
        # external two-level system that turns while the particle is in slit B: the same 2 x 2 coupling b.sigma)
        self.spinor = self.mark != "none"
        # the mark's coupling calibrated on slit B's channel (review B4-3: the first-order b0 turned it by ~1.2 theta)
        self.mark_cal = AP.MarkCalibration(self.geo, float(p["V0"]) * AP.E0) if self.spinor and self.geo.n_slits == 2 \
            else None
        self.mark_flux = np.zeros(2)  # flux of the up and down components through a plane just behind slit B (x > 0)
        self.W = self.geo.absorbers(g)
        self.iL = int(np.argmin(np.abs(g.axes[1] - self.geo.L)))  # the screen's face, a sample of the grid
        self.zL = float(g.axes[1][self.iL])
        self.regions = self.geo.regions(g, self.zL)
        self.on_screen = np.abs(g.axes[0]) <= self.geo.screen_half
        # where the mark is measured: a plane 0.5 lambda behind the plate's edges, across slit B's opening and 0.5 lambda
        # on either side (what left slit B; slit A's wave reaches there only by diffraction)
        if self.mark_cal is not None:
            self.iM = int(np.argmin(np.abs(g.axes[1] - (0.5 * self.geo.w + 5 * self.geo.edge + 0.5))))
            self.right = np.abs(g.axes[0] - self.geo.centers[1]) <= 0.5 * self.geo.a + 0.5
        self.live = {k: p[k] for k in SCHEMA.live_ids()}
        self.t_end_est = self._t_end_estimate()
        H = self._hamiltonian(self.live, g, self.W)
        self.prop = S.SplitOperator(H, self.dt, track_absorbed=True)
        self._cost_guard()
        # the companion: the same experiment on a grid 1.2 times coarser with twice the time step, whose difference
        # from the run estimates the run's numerical error (grid and time step) from above (review B3-2); when the
        # coarser grid would not resolve the edges (the run's step is already the edge width), 1.2 times finer
        self.g_c = self.geo.grid(self._companion_step())
        self.W_c = self.geo.absorbers(self.g_c)
        self.iL_c = int(np.argmin(np.abs(self.g_c.axes[1] - self.geo.L)))
        H_c = self._hamiltonian(self.live, self.g_c, self.W_c)
        self.comp = S.SplitOperator(H_c, 2 * self.dt, track_absorbed=True, force_cpu=self.prop.device == "cpu",
                                    why="как основной прогон")
        psi0 = self._packet(H, g)
        self.psi = self.prop.put(psi0)
        self.psi_c = self.comp.put(self._packet(H_c, self.g_c))
        self.n_pairs = 0
        self.tau = 0.0                         # the wave's time (units of the computation)
        self.flux = np.zeros(g.shape[0])       # time-integrated current into the screen, per x (per cell)
        self.flux_c = np.zeros(self.g_c.shape[0])
        self.done = False
        self.final = None
        # Bohm ensemble: starts drawn from |psi0|^2 (the Gaussian: exactly normal), seeded
        N = int(p["n_bohm"])
        self.X = self._starts(N)
        # the third dimension: nothing depends on y (slits infinitely long along y), so the state is the exact product
        # psi(x, z, t) eta(y, t), eta a free Gaussian (closed form, lfphys.core.quantum.schrodinger1d.FreeGaussians);
        # each Bohm trajectory's y scales with eta's width (bohm.gaussian_trajectory). The y starts are drawn after
        # the x, z starts, so these keep their sequence
        self.sy = float(p.get("sigma_y", 3.0))
        self.eta = FreeGaussians([(1.0, 0.0, 0.0, self.sy)])
        self.Y0 = self.rng.normal(0.0, self.sy, N)
        self.hit_y = np.full(N, np.nan)
        self.y_half = self._y_half()
        dy = 2 * self.y_half / NY_SCREEN
        self.y_screen = -self.y_half + (np.arange(NY_SCREEN) + 0.5) * dy  # bin centres of P(x, y)
        self.flux_xy = np.zeros((int(self.on_screen.sum()), NY_SCREEN))
        self.fate = np.zeros(N, np.int8)       # 0 in flight, 1 screen, 2 back (reflected), 3 side
        self.slit = np.zeros(N, np.int8)       # 0 not yet through, 1 A, 2 B
        self.hit_x = np.full(N, np.nan)
        self.hit_t = np.full(N, np.nan)
        self.crossed_axis = np.zeros(N, bool)  # behind the plate, from one side of x = 0 to the other
        self.max_sub = 1                       # the most sub-steps a trajectory needed in one step
        self.side0 = np.zeros(N, np.int8)
        self.K = min(int(p["n_tracks"]), N)
        # the control: the first CONTROL_N starts again, integrated CONTROL_TIGHT times more tightly in the same wave; their hits
        # against the ensemble's measure the trajectories' integration error (review B3-4)
        self.Kc = min(CONTROL_N, N)
        self.Xc = self.X[:self.Kc].copy()
        self.fate_c = np.zeros(self.Kc, np.int8)
        self.hit_c = np.full(self.Kc, np.nan)
        self.track_from = 0
        self.ds = max(1, int(math.ceil(max(g.shape) / MAX_PX)))
        self.default_speed = self.t_end_est * self.tunit / 40.0
        self.speed_range = (self.default_speed / 100, self.default_speed * 20)
        self.events = []
        self._static_checks()

    # --- hooks for worlds built on this one (v12) ---------------------------------------------------------------------
    def _geometry(self, p) -> AP.Geometry:
        return AP.Geometry(p["a"], p["d"], p["w"], p["L"], p["sigma_x"], p["sigma_z"], H_OF[p["grid"]],
                           edge=float(p["edge"]))

    def _t_end_estimate(self) -> float:
        """Units of the computation until the wave has left the window (an upper estimate from the geometry)."""
        geo = self.geo
        return (abs(geo.z_src) + geo.L + 4 * geo.sz + 2 * geo.screen_half) / AP.V0_SPEED

    def _starts(self, N: int) -> np.ndarray:
        """Bohm starts drawn from |psi0|^2: for the Gaussian packet exactly normal in x and z (seeded)."""
        return np.column_stack([self.rng.normal(0.0, self.geo.sx, N), self.rng.normal(self.geo.z_src, self.geo.sz, N)])

    def _layer_k(self) -> np.ndarray:
        """Wave numbers at which the absorbing layers are checked: the packet's spectrum (k0 +- 10 %)."""
        return AP.K0 * np.array([0.9, 1.0, 1.1])

    def _widest_angle(self) -> float:
        """The largest angle to the normal at which the wave meets the screen: its edge seen from the slits."""
        return math.atan2(self.geo.screen_half, self.geo.L)

    def _y_half(self) -> float:
        """Half the scene's extent along y: the slits' length drawn (a quarter of the window's length, as before) or
        four widths of eta at a set-up time (twice the window's length at the mean speed), whichever is larger. A
        set-up estimate: nothing of the run's future enters it."""
        geo = self.geo
        t_set = 2.0 * (geo.z_max - geo.z_min) / AP.V0_SPEED
        s_set = self.sy * math.sqrt(1.0 + (t_set / (2.0 * self.sy ** 2)) ** 2)  # hbar = m = 1
        return max(0.25 * (geo.z_max - geo.z_min), 4.0 * s_set)

    def _y_of(self, y0, tau):
        """The y of Bohm trajectories started at y0, at time tau: one time for all or one per trajectory (exact for the
        free factor eta). The times go in as a column: a row of them broadcast against the starts gave every hit of a
        step the first one's time (found by the check bohm_y_motion, review C1-11)."""
        y0 = np.asarray(y0, float)
        tau = np.broadcast_to(np.asarray(tau, float), y0.shape)
        return bohm.gaussian_trajectory(y0[:, None], tau[:, None], 0.0, 0.0, self.sy)[:, 0]

    def _acc_y(self, J, tau):
        """The screen's pattern across y: J(x, t) |eta(y, t)|^2 dt per bin (the flux through the face of the
        product state)."""
        e2 = np.abs(self.eta.psi(self.y_screen, tau)) ** 2
        self.flux_xy += np.outer(J[self.on_screen], e2) * self.dt * self.g.d[0]

    def _record(self, psi, J, tau):
        """Called after every step of the wave with the state and the current J(x) into the screen at time tau."""

    # --- the cost ----------------------------------------------------------------------------------------------------
    def _companion_step(self) -> float:
        h = self.geo.h
        return COMP_GRID * h if COMP_GRID * h <= self.geo.edge * (1 + 1e-9) else h / COMP_GRID

    def cost_estimate(self) -> float:
        """Seconds of computation the experiment needs on the device chosen, from the measured rates (RATES): the grid
        steps (the run's two per pair and the companion's one on a grid 1.2 times coarser) and the Bohm particles,
        over the pairs to the end estimated from the geometry (an upper estimate: runs usually end at ~0.6 of it)."""
        pairs = self.t_end_est / self.pair
        per_point, per_particle = RATES[self.prop.device]
        steps = 2 + (self.geo.h / self._companion_step()) ** 2  # the run's two steps, the companion's one
        work = self.g.size * steps * (2 if self.spinor else 1)
        return pairs * (work * per_point + int(self.params["n_bohm"]) * per_particle)

    def _cost_guard(self):
        """Refuse an experiment that would run longer than COST_LIMIT on its device: on GPU 0 the host hangs after
        ~18 min of full load (review B3-6: corners of the schema would have run ~29 min); on the CPU it would run for
        hours behind the chosen speed. The estimate is an upper one (measured runs end at ~0.56 of its pairs)."""
        est = self.cost_estimate()
        lim = COST_LIMIT[self.prop.device]
        if est > lim:
            raise ValueError(f"опыт слишком тяжёл: ~{est / 60:.0f} мин счёта на {'GPU 0' if self.prop.device == 'gpu' else 'CPU'} "
                             f"(предел {lim / 60:.0f} мин; сетка {self.g.shape[0]}×{self.g.shape[1]}, ~"
                             f"{self.t_end_est / self.pair:.0f} пар шагов): уменьшите экран, пакет или выберите сетку грубее")
        self.est_cost = est

    # --- the set-up ---------------------------------------------------------------------------------------------------
    def _hamiltonian(self, live, g, W) -> S.Hamiltonian:
        geo = self.geo
        V = float(self.params["V0"]) * AP.E0 * geo.plate(g, (bool(live["slit_a"]), bool(live["slit_b"])))
        b = None
        if self.spinor:
            b = np.zeros((3,) + g.shape)
            b0 = self.mark_cal.coupling(math.radians(float(live["mark_deg"])))
            if b0:
                b[1] = b0 * geo.slit_channel(g, 1)
        A = None
        if self.charged and float(live["flux"]):
            # the flux in units of the flux quantum h/|q| = 2 pi hbar/|q| (hbar = 1, |q| = 1 in these units); the
            # tube's field exp(-r^2/R^2) is below 1e-4 of its peak at the plate's faces (R = w/6) and at the slits
            A = S.flux_tube(2 * math.pi * float(live["flux"]) * np.sign(self.part.charge), (0.0, 0.0),
                            self._tube_radius(), axes=(0, 1))
        return S.Hamiltonian(g, V=V, W=W, A=A, b=b, q=1.0)

    def _tube_radius(self) -> float:
        return min(self.geo.w, 0.5 * (self.geo.d - self.geo.a)) / 6.0

    def _packet(self, H, g) -> np.ndarray:
        geo = self.geo
        center = (0.0, geo.z_src)
        phi = g.gaussian(center, (0.0, AP.K0), (geo.sx, geo.sz))
        if H.A is not None:  # the same physical packet in every gauge: its kinetic momentum is hbar k0 along z
            phi = phi * np.exp(1j * H.q * H.A.gauge(g, center))
        if self.spinor:
            return np.stack([phi, np.zeros_like(phi)])  # spin up along z: the mark turns it towards x
        return phi

    # --- live parameters --------------------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        new, errors = SCHEMA.coerce_live(self.live, values)
        if errors:
            raise ValueError("; ".join(errors))
        if abs(float(new["flux"])) > 0 and not self.charged:
            raise ValueError("поток Ааронова–Бома действует только на заряженные частицы")
        if float(new["mark_deg"]) and not self.spinor:
            raise ValueError("метки пути в этом мире нет: выберите спин или детектор в «Метка пути в щели B» (новый мир)")
        changed = [k for k in values if new.get(k) != self.live.get(k)]
        if not changed:
            return "без изменений"
        H = self._hamiltonian(new, self.g, self.W)
        H_c = self._hamiltonian(new, self.g_c, self.W_c)
        self.prop.rebuild(V=H.V, W=H.W, A=H.A, b=H.b, keep=())
        self.comp.rebuild(V=H_c.V, W=H_c.W, A=H_c.A, b=H_c.b, keep=())
        desc = "; ".join(f"{SCHEMA.by_id[k].label}: {self._fmt(k, self.live[k])} → {self._fmt(k, new[k])}"
                         for k in changed)
        self.live = new
        self.events.append((self.t, desc))
        self._msg({"type": "setup", "t": self.t, "live": dict(new), "plate": self._plate_obj(),
                   "observer": self._observer_obj()})
        return desc + " (действует с этого момента)"

    @staticmethod
    def _fmt(k, v):
        if isinstance(v, bool):
            return "открыта" if v else "закрыта"
        return f"{float(v):g}"

    # --- time ----------------------------------------------------------------------------------------------------------
    def max_step(self):
        return 4 * self.pair * self.tunit

    def advance(self, t_target):
        self.t = t_target
        tau_t = t_target / self.tunit
        while not self.done and self.tau + self.pair <= tau_t + 1e-12:
            self._pair()
        if not self.done and self.tau >= self.t_end_est * 4:
            self._finish("время вышло: волна задержалась в окне")

    def _pair(self):
        """Two steps of the wave (dt), one of the companion (2 dt), one RK4 step of the Bohm ensemble over 2 dt."""
        pr, g = self.prop, self.g
        a = self.psi
        b = pr.step(a, 1)
        Jb = pr.flux(b, 1, self.iL, FLUX_ORDER)
        self.flux += Jb * self.dt * (g.d[0])
        self._acc_y(Jb, self.tau + self.dt)
        self._record(b, Jb, self.tau + self.dt)
        c = pr.step(b, 1)
        Jc = pr.flux(c, 1, self.iL, FLUX_ORDER)
        self.flux += Jc * self.dt * (g.d[0])
        self._acc_y(Jc, self.tau + 2 * self.dt)
        self._record(c, Jc, self.tau + 2 * self.dt)
        self.psi_c = self.comp.step(self.psi_c, 1)
        self.flux_c += self.comp.flux(self.psi_c, 1, self.iL_c, FLUX_ORDER) * 2 * self.dt * self.g_c.d[0]
        if self.mark_cal is not None:
            for st in (b, c):
                pc, d = pr.plane(st, 1, self.iM, 8)
                j = np.imag(np.conj(pc) * d)[:, self.right]  # hbar = m = 1
                self.mark_flux += j.sum(axis=1) * g.d[0] * self.dt
        self._bohm(a, b, c)
        self._bohm_control(a, b, c)
        self.psi = c
        self.n_pairs += 1
        self.tau += self.pair
        if self.n_pairs % TRACK_EVERY == 0:
            self._tracks()
        if self.n_pairs % WAVE_EVERY == 0:
            self._wave()
        if self.n_pairs % SCREEN_EVERY == 0:
            self._screen()
            if pr.norm(self.psi) < END_NORM and not np.any(self.fate == 0):
                self._finish("волна ушла из окна")
            elif pr.norm(self.psi) < END_NORM * 0.01:
                self._finish("волна ушла из окна")

    def _bohm(self, a, b, c):
        act = np.flatnonzero(self.fate == 0)
        if not len(act):
            return
        X0 = self.X[act]
        X1, nsub = bohm.advance_ensemble(self.g, (a, b, c), X0, self.pair, self.prop.H, xp=self.prop.xp)
        self.max_sub = max(self.max_sub, int(nsub.max()))
        geo = self.geo
        z0, z1 = X0[:, 1], X1[:, 1]
        # the slit a particle went through: where it crossed the plate's middle plane z = 0 forwards
        cross = (z0 < 0) & (z1 >= 0) & (self.slit[act] == 0) & self.label_slits
        if np.any(cross):
            xc = X0[cross, 0] + (X1[cross, 0] - X0[cross, 0]) * (-z0[cross]) / (z1[cross] - z0[cross])
            self.slit[act[cross]] = np.where(xc < 0, 1, 2)
            self.side0[act[cross]] = np.where(xc < 0, -1, 1)
        behind = (self.side0[act] != 0) & (z1 > 0.5 * geo.w)
        flip = behind & (np.sign(X1[:, 0]) * self.side0[act] < 0)
        self.crossed_axis[act[flip]] = True
        hit = z1 >= self.zL
        if np.any(hit):
            f = (self.zL - z0[hit]) / (z1[hit] - z0[hit])
            self.hit_x[act[hit]] = X0[hit, 0] + f * (X1[hit, 0] - X0[hit, 0])
            self.hit_t[act[hit]] = (self.tau + f * self.pair) * self.tunit
            self.hit_y[act[hit]] = self._y_of(self.Y0[act[hit]], self.tau + f * self.pair)
            self.fate[act[hit]] = 1
        back = (~hit) & (z1 < geo.z_min + AP.ABS_W)
        side = (~hit) & (~back) & (np.abs(X1[:, 0]) > geo.screen_half)
        self.fate[act[back]] = 2
        self.fate[act[side]] = 3
        self.X[act] = X1
        if np.any(hit):
            idx = act[hit]
            self._msg({"type": "hits", "t": self.t, "count": int(len(idx))},
                      {"x": self.hit_x[idx].astype(np.float32), "slit": self.slit[idx].astype(np.int8),
                       "idx": idx.astype(np.int32), "t": self.hit_t[idx].astype(np.float32),
                       "y": self.hit_y[idx].astype(np.float32)})

    def _bohm_control(self, a, b, c):
        act = np.flatnonzero(self.fate_c == 0)
        if not len(act):
            return
        step = float(min(self.g.d))
        X0 = self.Xc[act]
        X1, _ = bohm.advance_ensemble(self.g, (a, b, c), X0, self.pair, self.prop.H, xp=self.prop.xp,
                                      rtol=1e-5 / CONTROL_TIGHT, atol=1e-6 * step / CONTROL_TIGHT)
        z0, z1 = X0[:, 1], X1[:, 1]
        hit = z1 >= self.zL
        if np.any(hit):
            f = (self.zL - z0[hit]) / (z1[hit] - z0[hit])
            self.hit_c[act[hit]] = X0[hit, 0] + f * (X1[hit, 0] - X0[hit, 0])
            self.fate_c[act[hit]] = 1
        back = (~hit) & (z1 < self.geo.z_min + AP.ABS_W)
        side = (~hit) & (~back) & (np.abs(X1[:, 0]) > self.geo.screen_half)
        self.fate_c[act[back]] = 2
        self.fate_c[act[side]] = 3
        self.Xc[act] = X1

    def _tracks(self):
        K = self.K
        P = np.where((self.fate[:K] == 0)[:, None], self.X[:K], np.nan).astype(np.float32)
        self._msg({"type": "tracks", "t": self.t, "id": "bohm", "from": self.track_from, "n": K},
                  {"xz": P, "slit": self.slit[:K].astype(np.int8), "fate": self.fate[:K].astype(np.int8),
                   "y": self._y_now(K)})
        self.track_from += 1

    def _y_now(self, K):
        """y of the first K particles now (NaN for those no longer in flight), float32."""
        return np.where(self.fate[:K] == 0, self._y_of(self.Y0[:K], self.tau), np.nan).astype(np.float32)

    def _pattern(self, flux):
        x = self.g.axes[0]
        P = np.where(self.on_screen, flux, 0.0)
        return x, P

    def _screen(self):
        """The pattern accumulated so far. Below SCREEN_FLOOR of probability it is round-off of either sign, not a
        pattern: nothing is drawn then (review B3-5: the noise's largest value was drawn at full brightness while
        the packet was still at the plate)."""
        x, P = self._pattern(self.flux)
        tot = float(P.sum())
        empty = tot < SCREEN_FLOOR
        if empty:
            P = np.zeros_like(P)
        pk = float(P.max()) if P.max() > 0 else 1.0
        self._msg({"type": "screen", "t": self.t, "x0": float(x[0]), "dx": float(self.g.d[0]), "n": int(len(x)),
                   "total": 0.0 if empty else tot, "peak": pk, "half": self.geo.screen_half, "empty": empty},
                  {"P": P.astype(np.float32)})
        # the 3-D screen: P(x, y), the flux of the product state across y as well (its x-marginal is the pattern above)
        Pxy = np.clip(self.flux_xy, 0, None)
        b = max(1, int(math.ceil(Pxy.shape[0] / SCREEN_COLS)))  # the 3-D picture only: at most SCREEN_COLS columns
        n = (Pxy.shape[0] // b) * b
        Pxy = Pxy[:n].reshape(n // b, b, Pxy.shape[1]).mean(axis=1)
        img = (np.zeros_like(Pxy) if empty or Pxy.max() <= 0 else Pxy / Pxy.max()).astype(np.float32)
        self._msg({"type": "target", "t": self.t, "id": "screen", "shape": list(img.shape)}, {"img": img})

    # --- the end: the pattern is complete ------------------------------------------------------------------------------
    def _finish(self, why):
        self.done = True
        self._screen()
        self._wave()
        g, geo = self.g, self.geo
        x = g.axes[0]
        absorbed = self.prop.absorbed()
        norm = self.prop.norm(self.psi)
        xs, P = self._pattern(self.flux)
        Pc = self._companion_density(xs)
        tot = float(P.sum())
        # detected: what flowed through the screen's face within its width; reflected: absorbed before the plate's
        # middle (z < 0), by whichever layer; lost sideways: the rest (the side layers behind the plate, the screen
        # layer's corners beyond its width) (review B3-13)
        back = float(absorbed[self.regions["before"]].sum())
        frac = {"screen": tot, "back": back, "side": 1.0 - norm - back - tot, "left": norm}
        res = {"why": why, "fractions": frac, "tau_end": self.tau, "t_end": self.t,
               "bohm": {"n": int(len(self.fate)), "screen": int((self.fate == 1).sum()), "back": int((self.fate == 2).sum()),
                        "side": int((self.fate == 3).sum()), "flight": int((self.fate == 0).sum()),
                        "A": int(((self.fate == 1) & (self.slit == 1)).sum()), "B": int(((self.fate == 1) & (self.slit == 2)).sum()),
                        "crossed_axis": int(self.crossed_axis.sum()), "max_substeps": self.max_sub}}
        self._msg({"type": "event", "t": self.t, "kind": "done",
                   "text": f"картина на экране завершена ({why}): на экран {frac['screen']:.4f}, {self.BACK_LABEL} "
                           f"{frac['back']:.4f}, ушло вбок {frac['side']:.4f}"})
        mk = self._mark_measured()
        if mk is not None:
            res["mark"] = {**mk, "theta_nominal_deg": float(self.live["mark_deg"]),
                           "calibration": {"E_perp_E0": self.mark_cal.E_perp / AP.E0, "c_x": self.mark_cal.c_x}}
        self.final = res
        refs = self._references(xs)
        res["refs"] = {k: v.astype(np.float32).tolist() for k, v in refs.items()} if refs else {}
        self._msg({"type": "result", "t": self.t, **res})
        self._final_checks(xs, P, Pc, tot, frac, absorbed)

    def _companion_density(self, xs):
        """The companion's pattern as a probability density per unit length, on the run's x (cubic spline over the
        screen: its error ~(dx / fringe period)^4 is far below what it compares)."""
        from scipy.interpolate import CubicSpline
        xc = self.g_c.axes[0]
        mc = np.abs(xc) <= self.geo.screen_half + 2 * self.g_c.d[0]
        rho_c = self.flux_c[mc] / self.g_c.d[0]
        out = np.zeros_like(xs)
        m = self.on_screen
        out[m] = CubicSpline(xc[mc], rho_c)(xs[m])
        return out

    def _two_path(self, op=(True, True)):
        """The two-path model's slit phases (Aharonov-Bohm: -+pi Phi/Phi0 for slits A, B, the fringe phase
        phi_B - phi_A = 2 pi Phi/Phi0 sign(q): the fringes move by Phi/Phi0 of a period) and the marks' overlap <m_B|m_A> = cos(theta/2) (the spin turned by theta about
        y in slit B, for the mean speed)."""
        live = self.live
        ph = None
        if self.charged and float(live["flux"]) and all(op):
            # the fringe phase is phi_B - phi_A (slit B at +d/2 is nearer to x > 0): the tube's vector potential adds
            # +q Phi / hbar along the path through B relative to A (review B3-1: the signs were swapped)
            s = math.pi * float(live["flux"]) * np.sign(self.part.charge)
            ph = (-s, s)
        coh = math.cos(math.radians(float(live["mark_deg"])) / 2) if self.spinor else 1.0
        return ph, coh

    def _mark_measured(self):
        """What the mark did to the wave that left slit B, measured in the run: the share of the down component in the
        flux through a plane 0.5 lambda behind the plate, across slit B's opening. A pure rotation by theta gives
        sin^2(theta / 2); the wave leaving a slit of a few wavelengths is not turned uniformly (candidates: its higher
        transverse modes, the speed spread), so the share stays below 1 at any theta (measured 0.86-0.93 in a slit of
        1.5 lambda: review B4-3) and is reported as information, not as an angle. None before any flux."""
        up, down = (float(v) for v in self.mark_flux)
        if self.mark_cal is None or up + down <= 0:
            return None
        return {"down_fraction": min(max(down / (up + down), 0.0), 1.0)}

    def _references(self, xs):
        """The approximate theories' patterns on the screen for the set-up in force (information)."""
        live = self.live
        op = (bool(live["slit_a"]), bool(live["slit_b"]))
        if not any(op) or self.events and any(t > 0 for t, _ in self.events):
            return {}
        m = self.on_screen
        out = {}
        try:
            ph, coh = self._two_path(op)
            xx = xs[m]
            out["paraxial"] = np.zeros(len(xs))
            out["paraxial"][m] = AP.paraxial_pattern(xx, self.geo, op, ph, coh)
            out["kirchhoff"] = np.zeros(len(xs))
            out["kirchhoff"][m] = AP.kirchhoff_pattern(xx, self.geo, op, ph, coh)
        except Exception:  # noqa: BLE001  references never break a run
            return {}
        return out

    # --- checks -----------------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group="Двухщелевой опыт"):
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
        g = self.g
        kmax = math.pi / g.d[0]
        self._check("grid_k", "Сетка разрешает волну: k_max / k₀", kmax / AP.K0, None, "", ok=kmax / AP.K0 >= 2.4,
                    group="Расчёт", note=f"шаг сетки λ/{1 / g.d[0]:.3g}; k_max = π/шаг; нужно ≥ 2,4·k₀ (спектр пакета и "
                                         f"затухание в стенке)")
        Emax = 0.5 * kmax * kmax
        V0 = float(self.params["V0"]) * AP.E0
        kap = math.sqrt(2 * (V0 - AP.E0)) if V0 > AP.E0 else 0.0
        if self.geo.n_slits:
            self._check("grid_wall", "Затухание в стенке разрешено сеткой: κ/k_max", kap / kmax, None, "",
                        ok=kap < kmax and V0 < Emax, group="Расчёт",
                        note=f"κ = √(2(V0 − E0)) = {kap:.3g} λ⁻¹; прохождение сквозь толщину w ≈ e^(−2κw) = "
                             f"{math.exp(-2 * kap * self.geo.w):.1e}")
        # absorbers: the reflection of the layers for the beam (normal) and the screen's widest angle
        th = self._widest_angle()
        kk = self._layer_k()
        sw, sW = self.geo.screen_w, self.geo.screen_W * AP.E0
        R_n, T_n = S.layer_reflection(kk, sw, sW, 1.0)
        R_o, T_o = S.layer_reflection(kk * math.cos(th), sw, sW, 1.0)
        self.R_layer = float(max(R_n.max(), R_o.max()))
        self.T_layer = float(max(T_n.max(), T_o.max()))
        self._check("absorbers", "Детекторы: отражение и утечка поглощающих слоёв", self.R_layer, None, "",
                    ok=self.R_layer < 1e-3 and self.T_layer < 1e-3, group="Расчёт",
                    note=f"матрицы переноса для слоя экрана −iW (ширина {self.geo.screen_w:g} λ, W = {self.geo.screen_W:g} "
                         f"E0·(s/ширина)²) при k ∈ [{kk.min() / AP.K0:.2f}; {kk.max() / AP.K0:.2f}] k₀, по нормали и под "
                         f"наибольшим углом {math.degrees(th):.0f}°: "
                         f"R ≤ {self.R_layer:.1e}, утечка ≤ {self.T_layer:.1e}")

    def _final_checks(self, xs, P, Pc, tot, frac, absorbed):
        g, geo = self.g, self.geo
        lost = abs(self.prop.norm(self.psi) + float(absorbed.sum()) - 1.0)
        self._check("norm", "Норма + поглощённое = 1", lost, 0.0, "", tol=1e-9, ok=lost < 1e-9, group="Расчёт",
                    note="шаги расщепления унитарны; поглощение учитывается в каждой точке")
        rho_m = P / g.d[0]
        pk = float(rho_m.max()) if rho_m.max() > 0 else 1.0
        err_num = float(np.max(np.abs(rho_m - Pc))) / pk
        coarser = self.g_c.d[0] > g.d[0]
        self._check("numerics", "Сетка и шаг по времени: ошибка картины на экране (оценка по прогону на соседней "
                                "сетке с шагом 2dt)", err_num, None, "", ok=err_num < 1e-2, group="Расчёт",
                    note=f"параллельный прогон на сетке λ/{1 / self.g_c.d[0]:.3g} ({'в 1,2 раза грубее' if coarser else 'в 1,2 раза мельче: грубее края не разрешаются'}) "
                         f"с шагом по времени 2dt; наибольшая разность плотностей на экране в долях пика — оценка "
                         f"ошибки этого прогона (λ/{1 / g.d[0]:.3g}, dt = {self.dt:.3g}, E0·dt = {DT_E0}) с запасом: у "
                         f"спутника шаг по времени вдвое больше; края стенки и поля — {geo.edge:g} λ на обеих сетках "
                         f"(review B3-2); цель < 1 %"),
        err_dt = err_num
        rho = self.prop.density(self.psi) * g.dV
        scr = float(absorbed[self.regions["beyond"]].sum()) + float(rho[self.regions["beyond"]].sum())
        through = float(self.flux.sum())
        d = abs(through - scr)
        # the face's own cells lie half before, half beyond the face: what they hold is ambiguous (0 once the wave has
        # gone; v12 stops while ~1e-4 is still near the face)
        face = float(rho[:, self.iL].sum())
        tol = self.R_layer * max(scr, 1e-12) + 3 * err_dt * scr + face + 1e-6
        self._check("flux_absorbed", "Поток через грань экрана против вероятности, ушедшей за неё", through, scr, "",
                    tol=tol / max(scr, 1e-12), ok=d <= tol, group="Расчёт",
                    note="∫∫ j_z dx dt на передней грани экрана (по всей ширине окна) против поглощённого за ней (и "
                         "оставшегося там); допуск — отражение слоя и численная ошибка (сверка «Сетка и шаг»)")
        if frac["screen"] > 0:
            self._bohm_checks(xs, P, tot)
            self._y_checks(P)
        self._symmetry_checks(xs, P)
        self._reference_checks(xs, P)

    def _bohm_checks(self, xs, P, tot):
        hits = self.hit_x[self.fate == 1]
        N = len(self.fate)
        n = len(hits)
        if n < 20:
            self._check("bohm_born", "Траектории Бома против картины", None, None, "", info=True, group="Бом",
                        note=f"на экран пришло {n} частиц: мало для сравнения")
            return
        Q = np.where(self.on_screen, P, 0.0)
        F = np.cumsum(Q) / Q.sum()
        edges = xs + 0.5 * self.g.d[0]
        emp = np.searchsorted(np.sort(hits), edges, side="right") / n
        D = float(np.max(np.abs(emp - F)))
        crit = 1.95 / math.sqrt(n)
        self._check("bohm_born", "Попадания частиц Бома против картины потока (Колмогоров–Смирнов)", D, None, "",
                    ok=D < crit, group="Бом",
                    note=f"{n} попаданий; расстояние между их распределением по x и картиной потока; критическое "
                         f"значение 99,9 %: 1,95/√n = {crit:.3g} (эквивариантность: старт по |ψ|² → попадания по потоку)")
        K = self.Kc
        both = (self.fate[:K] == 1) & (self.fate_c == 1)
        changed = int((self.fate[:K] != self.fate_c).sum())
        if both.any():
            dx = np.abs(self.hit_x[:K][both] - self.hit_c[both])
            p95, mx = float(np.percentile(dx, 95)), float(dx.max())
            fringe = f" (период полос {(self.geo.L - 0.5 * self.geo.w) / self.geo.d:.3g} λ)" if self.geo.d else ""
            self._check("bohm_accuracy", "Траектории Бома: точность интегрирования (95 % попаданий), λ", p95, None, "λ",
                        ok=p95 < BOHM_P95 and changed <= max(1, K // 50), group="Бом",
                        note=f"{K} частиц проинтегрированы ещё раз в той же волне в {CONTROL_TIGHT} раза строже; из {int(both.sum())} "
                             f"попавших в обоих случаях 95 % отличаются не больше чем на {p95:.2g} λ, наибольшее — "
                             f"{mx:.2g} λ{fringe}; судьба (экран, отражение, вбок) другая у "
                             f"{changed}; цель: 95 % < {BOHM_P95:g} λ и не больше 2 % другой судьбы (review B3-4)")
        p_scr = tot
        pc = min(max(p_scr, 0.5 / N), 1 - 0.5 / N)  # the binomial spread stays finite when all particles arrive
        sd = math.sqrt(pc * (1 - pc) / N)
        self._check("bohm_fraction", "Доля частиц Бома на экране против вероятности", n / N, p_scr, "",
                    tol=3.3 * sd / max(p_scr, 1e-12), group="Бом",
                    note=f"N = {N}; допуск 3,3σ биномиального разброса")

    def _y_motion(self, y0, tau):
        """The y of Bohm particles by a second method (review C1-11): the guidance equation dy/dt = j/|eta|^2 in the
        run's own free factor eta (its closed-form psi and current), integrated by RK4 from each start y0 to its time
        tau, in steps of at most a twentieth of eta's spreading time 2 m sigma_y^2 / hbar (hbar = m = 1): its error
        is then below 3e-8 of eta's width at any time (measured from sigma_y = 0.5 to 40)."""
        y = np.array(y0, float)
        tau = np.asarray(tau, float)
        if not len(y):
            return y
        n = max(100, int(math.ceil(float(tau.max()) / (0.1 * self.sy ** 2))))
        h = tau / n
        t = np.zeros_like(y)

        def v(y, t):
            return self.eta.current(y, t) / np.abs(self.eta.psi(y, t)) ** 2
        for _ in range(n):
            k1 = v(y, t)
            k2 = v(y + 0.5 * h * k1, t + 0.5 * h)
            k3 = v(y + 0.5 * h * k2, t + 0.5 * h)
            k4 = v(y + h * k3, t + h)
            y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            t = t + h
        return y

    def _y_checks(self, P):
        """The third dimension: the screen's P(x, y) summed over y gives back the pattern P(x) (the y bins resolve
        |eta|^2 and the scene holds it); the Bohm hits' y against the guidance equation integrated in eta (the
        y-motion, by a second method); the hits' y against the screen's y-marginal (the starts drawn from |eta_0|^2)."""
        dy = 2 * self.y_half / NY_SCREEN
        Px = P[self.on_screen]
        marg = self.flux_xy.sum(axis=1) * dy
        pk = float(np.max(np.abs(Px))) or 1.0
        dev = float(np.max(np.abs(marg - Px)) / pk)
        self._check("screen_y", "Экран P(x, y): сумма по y против картины P(x)", dev, None, "", ok=dev < 1e-3,
                    group="Расчёт",
                    note=f"Σ_y P(x, y) Δy против потока в экран по x; {NY_SCREEN} полос по y на ±{self.y_half:.3g} λ, "
                         f"|η(y, t)|² свободного гауссова множителя (σy = {self.sy:g} λ при t = 0); доля пика; цель < 1e-3 "
                         f"(обрезка хвостов η краями сцены и шаг полос)")
        hit = self.fate == 1
        hy = self.hit_y[hit]
        n = len(hy)
        if n:
            tau = self.hit_t[hit] / self.tunit
            spread = self.sy * np.sqrt(1.0 + (tau / (2.0 * self.sy ** 2)) ** 2)  # eta's width at each hit
            dev = float(np.max(np.abs(hy - self._y_motion(self.Y0[hit], tau)) / spread))
            grow = float(np.median(spread) / self.sy - 1.0)
            self._check("bohm_y_motion", "Движение частиц Бома по y: попадания против уравнения ведения в η", dev, None,
                        "", ok=dev < Y_MOTION_TOL, group="Бом",
                        note=f"{n} попаданий; y каждого — y₀·σy(t)/σy (точная формула прогона) против dy/dt = j/|η|², "
                             f"проинтегрированного методом Рунге–Кутты 4-го порядка в волне η этого прогона от старта до "
                             f"момента попадания (второй метод); наибольшая разность в ширинах η в момент попадания; цель "
                             f"< {Y_MOTION_TOL:g} (ошибка интегрирования); за полёт η расплывается на {100 * grow:.3g} % "
                             f"(медиана)")
        if n < 20:
            return
        Py = np.clip(self.flux_xy, 0, None).sum(axis=0)
        if Py.sum() <= 0:
            return
        F = np.cumsum(Py) / Py.sum()
        edges = self.y_screen + 0.5 * dy
        emp = np.searchsorted(np.sort(hy), edges, side="right") / n
        D = float(np.max(np.abs(emp - F)))
        crit = 1.95 / math.sqrt(n)
        self._check("bohm_y", "Попадания частиц Бома по y против картины P(x, y) (Колмогоров–Смирнов)", D, None, "",
                    ok=D < crit, group="Бом",
                    note=f"{n} попаданий; эталон — распределение по y потока в экран, Σ_t J(x, t)|η(y, t)|²; критическое "
                         f"значение 99,9 %: 1,95/√n = {crit:.3g}. Проверяет старты по |η₀|²; движение по y так не "
                         f"различить (η за полёт расплывается на {100 * grow:.3g} %) — его проверяет «Движение частиц "
                         f"Бома по y»")

    def _symmetric(self):
        L = self.live
        return (bool(L["slit_a"]) and bool(L["slit_b"]) and not float(L["mark_deg"]) and not float(L["flux"])
                and not self.events)

    def _symmetry_checks(self, xs, P):
        L = self.live
        pk = float(P.max()) if P.max() > 0 else 1.0
        asym = float(np.max(np.abs(P - P[::-1]))) / pk
        half = 2 * float(L["flux"])
        if (bool(L["slit_a"]) and bool(L["slit_b"]) and not float(L["mark_deg"]) and float(L["flux"])
                and abs(half - round(half)) < 1e-12 and not self.events):
            # Phi -> -Phi with x -> -x is the mirror image; -Phi = Phi - k Phi0 is the same physics (gauge): at a
            # half-integer flux the pattern is symmetric. The gauge identity holds to the grid's error (tests: ~1e-5
            # at lambda/6 for a tube the wave cannot reach)
            self._check("symmetry_ab", "Поток Φ₀/2 (полуцелый): картина симметрична, P(x) = P(−x)", asym, 0.0, "",
                        tol=1e-4, ok=asym < 1e-4, group="Расчёт",
                        note="зеркало x → −x переворачивает поток, а потоки Φ и Φ − Φ₀ физически одинаковы (калибровка): "
                             "при полуцелом Φ/Φ₀ картина симметрична; допуск — ошибка сетки калибровочного тождества")
        if not self._symmetric():
            return
        self._check("symmetry", "Симметричная установка: картина симметрична, P(x) = P(−x)", asym, 0.0, "", tol=1e-8,
                    ok=asym < 1e-8, group="Расчёт", note="сетка симметрична по x (x = 0 — узел); допуск — округление")
        if not self.label_slits:
            return
        c = int(self.crossed_axis.sum())
        self._check("no_crossing", "Траектории Бома не пересекают ось симметрии за пластиной", float(c), 0.0, "",
                    ok=c == 0, group="Бом",
                    note="у симметричной волны v_x = 0 на оси: траектории из щели A остаются слева, из B — справа "
                         "(свойство теории Бома для этой установки)")

    def _reference_checks(self, xs, P):
        refs = (self.final or {}).get("refs") or {}
        m = self.on_screen
        Pn = np.zeros_like(P)
        Pn[m] = P[m] / np.trapezoid(P[m], xs[m]) if P[m].sum() > 0 else 0
        for key, label in (("paraxial", "параксиальная теория (Френель, граничные условия Кирхгофа)"),
                           ("kirchhoff", "точное распространение граничных условий Кирхгофа (Рэлей–Зоммерфельд)")):
            if key not in refs:
                continue
            R = np.asarray(refs[key])
            dev = float(np.max(np.abs(Pn[m] - R[m])) / max(R[m].max(), 1e-300))
            self._check(f"ref_{key}", f"Картина против приближения: {label}", dev, None, "", info=True,
                        group="Сравнение",
                        note="наибольшее отличие нормированных картин в долях пика; приближение — не эталон: точный "
                             "расчёт здесь — решение уравнения Шрёдингера")
        L = self.live
        if self.geo.n_slits == 2 and bool(L["slit_a"]) and bool(L["slit_b"]) and not self.events:
            period = (self.geo.L - 0.5 * self.geo.w) / self.geo.d
            V, phi = AP.fringes(xs, Pn, period)
            ph, coh = self._two_path()
            mk = self._mark_measured()
            th = float(L["mark_deg"])
            mark_note = (f"метка: поворот θ = {th:g}° основной поперечной моды щели B при средней скорости (связь "
                         f"откалибрована по этой моде матрицами переноса, review B4-3), |⟨m_A|m_B⟩| = |cos(θ/2)|; "
                         f"измерено в прогоне: доля компоненты «вниз» в потоке сразу за щелью B "
                         f"{mk['down_fraction']:.3f} (при чистом повороте было бы sin²(θ/2) = "
                         f"{math.sin(math.radians(th) / 2) ** 2:.3f}: волна за щелью повёрнута неравномерно)"
                         if mk else "метки нет")
            self._check("visibility", "Видность полос у оси против двух путей |⟨m_B|m_A⟩|", V, abs(coh), "",
                        info=True, group="Сравнение",
                        note=f"фурье-компонента картины на частоте полос (период λL/d = {period:.3g} λ, окно Ханна "
                             f"±2 периода); {mark_note}; огибающая, разброс скоростей и смесь поперечных мод в щели "
                             f"(они поворачивают метку по-разному) снижают видность")
            if self.charged and float(L["flux"]):
                shift = 2 * math.pi * float(L["flux"]) * np.sign(self.part.charge)
                self._check("ab_phase", "Сдвиг полос потоком Ааронова–Бома: фаза полос у оси минус 2πΦ/Φ₀ (по модулю "
                                        "2π)", math.remainder(phi - shift, 2 * math.pi), 0.0, "рад", info=True,
                            group="Сравнение",
                            note=f"фаза фурье-компоненты картины на частоте полос {phi:+.4f} рад (у симметричной "
                                 f"картины без потока — 0) против модели двух путей 2πΦ/Φ₀·sign(q) = {shift:+.4f} рад: "
                                 f"полосы сдвигаются на Φ/Φ₀ периода; разность взята по модулю 2π (review B3-9)")

    # --- messages ------------------------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)
        self._wave()
        self._tracks()

    def _wave(self):
        pk, amp, ph = self._image()
        if not hasattr(self, "peak0"):
            self.peak0 = pk
        # the y-factor at this moment, on NY_VOLUME points across the scene's y extent (its peak 1): the view draws the
        # volume |psi(x, z)|^2 |eta(y)|^2 as the outer product of the image and this profile
        y = np.linspace(-self.y_half, self.y_half, NY_VOLUME)
        e2 = np.abs(self.eta.psi(y, self.tau)) ** 2
        sy_t = float(self.sy * math.sqrt(1.0 + (self.tau / (2.0 * self.sy ** 2)) ** 2))
        self._msg({"type": "wave", "t": self.t, "tau": self.tau, "peak": pk, "peak_rel": pk / self.peak0,
                   "norm": self.prop.norm(self.psi), "shape": list(amp.shape), "ds": self.ds, "spinor": self.spinor,
                   "sigma_y": sy_t, "y_half": self.y_half},
                  {"amp": amp, "phase": ph, "eta": (e2 / e2.max()).astype(np.float32)})

    def _image(self):
        """|psi|^2 (u2, sqrt-encoded, block-averaged ds x ds) and its phase (u1; of the spin-up component for a
        spinor) for the view; reduced on the device, only the image is moved."""
        xp, ds = self.prop.xp, self.ds
        rho = self.prop._rho(self.psi)
        nx, nz = (rho.shape[0] // ds) * ds, (rho.shape[1] // ds) * ds
        r = backend.to_numpy(rho[:nx, :nz].reshape(nx // ds, ds, nz // ds, ds).mean(axis=(1, 3)))
        p0 = self.psi[0] if self.spinor else self.psi
        ph = backend.to_numpy(xp.angle(p0[ds // 2:nx:ds, ds // 2:nz:ds]))
        pk = float(r.max()) if r.max() > 0 else 1.0
        amp = np.sqrt(np.clip(r / pk, 0, 1))
        return pk, (amp * 65535).astype(np.uint16), ((ph + math.pi) / (2 * math.pi) * 255).astype(np.uint8)

    def frame(self):
        K = self.K
        pos = np.where((self.fate[:K] == 0)[:, None], self.X[:K], np.nan).astype(np.float32)
        counts = {"screen": int((self.fate == 1).sum()), "back": int((self.fate == 2).sum()),
                  "side": int((self.fate == 3).sum()), "flight": int((self.fate == 0).sum())}
        meta = {"tau": self.tau, "norm": self.prop.norm(self.psi), "counts": counts, "done": self.done,
                "live": self.live}
        return meta, {"pos": pos, "slit": self.slit[:K].astype(np.int8), "y": self._y_now(K)}

    def next_event_time(self):
        return None

    def engine_modules(self):
        mods = ["core.quantum.schrodinger_nd", "core.quantum.particles", "core.quantum.transfer", "core.backend",
                "theories.interpretations.bohm", "theories.approx.paraxial", "theories.approx.kirchhoff"]
        return mods

    def _plate_obj(self):
        geo = self.geo
        yh = self.y_half
        holes = [{"rect": [c - 0.5 * geo.a, c + 0.5 * geo.a, -0.97 * yh, 0.97 * yh]}
                 for c, op in zip(geo.centers, (self.live["slit_a"], self.live["slit_b"])) if op]
        return {"id": "plate", "label": "Пластина с двумя щелями (вдоль y)", "kind": "plate", "z": 0.0,
                "size": [2 * geo.x_half, 2 * yh], "holes": holes, "visible": True}

    def _observer_obj(self):
        """The which-path mark in slit B's channel, drawn: the detector (or the spin's field), more opaque the more
        the path is marked (sin^2(theta/2): the distinguishability of the two paths)."""
        if not self.spinor or self.geo.n_slits < 2:
            return None
        geo, th = self.geo, float(self.live["mark_deg"])
        dist = math.sin(math.radians(th) / 2) ** 2
        who = "Наблюдатель: детектор пути у щели B" if self.mark == "detector" else "Метка пути: поле, поворачивающее спин в щели B"
        return {"id": "observer", "label": who, "kind": "box", "center": [geo.centers[1], 0.0, 0.0],
                "size": [geo.a, 1.94 * self.y_half, geo.w], "color": "#ff8a1f", "opacity": 0.12 + 0.5 * dist,
                "text": f"{'детектор' if self.mark == 'detector' else 'спин'}: θ = {th:g}°",
                "text_size": 0.03 * (geo.z_max - geo.z_min), "visible": True}

    def header(self):
        g, geo, part = self.g, self.geo, self.part
        x0, x1 = float(g.axes[0][0]), float(g.axes[0][-1])
        z0, z1 = float(g.axes[1][0]), float(g.axes[1][-1])
        objects = [self._plate_obj(), *([self._observer_obj()] if self._observer_obj() else []),
                   {"id": "incident", "label": "Падающий пакет (задан)", "kind": "incident",
                    "z0": geo.z_src - 2 * geo.sz, "z1": -0.5 * geo.w, "lam": 4.0, "size": [4 * geo.sx, 2 * self.y_half],
                    "visible": False},
                   {"id": "screen", "label": f"Экран (z = {geo.L:g} λ): поток, накопленный за опыт", "kind": "target",
                    "z": float(self.zL), "size": [2 * geo.screen_half, 2 * self.y_half], "visible": True},
                   {"id": "wave", "label": "Волна |ψ|² в плоскости опыта (y = 0)", "kind": "panel",
                    "origin": [x0, 0.0, z0], "u": [x1 - x0, 0.0, 0.0], "v": [0.0, 0.0, z1 - z0], "visible": False}]
        lam = part.lam
        approx = ["щели бесконечно длинные вдоль y: уравнение Шрёдингера решается на плоскости (x, z), трёхмерная волна — "
                  "точное произведение ψ(x, z, t)·η(y, t) со свободным гауссовым η (замкнутая форма)",
                  "стенка — потенциальный барьер конечной высоты и толщины с краями, сглаженными на шаг сетки",
                  "детекторы — поглощающие слои (модель); их отражение и утечка — в проверках"]
        if self.mark == "detector":
            approx.append("наблюдатель — двухуровневый детектор у щели B (модель Энглерта): пока частица в щели, его "
                          "состояние поворачивается на θ (для средней скорости); сам прибор не моделируется")
        if part.v / 2.998e8 > 0.01:
            approx.append(f"нерелятивистское уравнение Шрёдингера при β = {part.v / 2.998e8:.3f}: длины и картина "
                          f"точны для данной λ, время — с ошибкой ~β²/2")
        return {
            "title": "Двухщелевой опыт (длинные щели, 3D): точное уравнение Шрёдингера и траектории Бома",
            "text": ("Пакет частицы летит на пластину с двумя щелями и дальше на экран. Прогон решает уравнение "
                     "Шрёдингера на всей плоскости (x, z): отражение пластиной, волна в щелях, дифракция на любые углы; "
                     "экран и края поглощают. Картина на экране — вероятность, втекающая в экран, копится по мере "
                     "прихода волны. Ансамбль частиц идёт по траекториям Бома той же волны; каждая помечена щелью, "
                     "через которую прошла. Установку можно менять на ходу: закрыть щель, включить метку пути (спин частицы "
                     "или наблюдатель — детектор у щели B), поток Ааронова–Бома. Вдоль щелей (ось y) ничего не меняется: "
                     "трёхмерная волна — точное произведение посчитанной волны на плоскости и свободного гауссова пакета "
                     "по y; в 3D она показана объёмом, частицы и траектории — во всех трёх координатах, экран — картиной "
                     "P(x, y)."),
            "actions": [],
            "approximations": approx,
            "scene3d": {"box": [[x0, -self.y_half, z0], [x1, self.y_half, z1]], "units": "λ", "objects": objects,
                        "layers": [{"id": "wave3d", "label": "Волна |ψ|² в объёме: ψ(x, z, t)·η(y, t)", "kind": "volume",
                                    "visible": True, "look": {"density": 3.0, "threshold": 0.01}}],
                        "coord_names": ["x", "y", "z"],
                        "planes": {"max": 0, "center": [0.0, 0.0, 0.0], "defaults": {"1": [0, 1, 0], "2": [1, 0, 0], "3": [0, 0, 1]}}},
            "geometry": {"a": geo.a, "d": geo.d, "w": geo.w, "L": geo.L, "zL": self.zL, "screen_half": geo.screen_half,
                         "z_src": geo.z_src, "sigma_x": geo.sx, "sigma_z": geo.sz, "centers": geo.centers,
                         "x": [x0, x1], "z": [z0, z1], "grid": list(g.shape), "h": float(g.d[0]), "dt": self.dt,
                         "V0": float(self.params["V0"]), "sigma_y": self.sy, "y_half": self.y_half},
            "particle": {"label": part.label, "lambda_m": lam, "Ekin_eV": part.Ekin / particles.EV, "v": part.v,
                         "charge_e": part.charge / particles.E_CHARGE, "time_unit_s": self.tunit,
                         "spin": self.spinor, "mark": self.mark},
            "device": {"wave": self.prop.device, "reason": self.prop.choice.reason},
            "n_bohm": int(len(self.fate)), "n_tracks": self.K,
            "units": {"x": "λ", "t": "с (мировые часы)"},
        }, {}


VIZ = {
    "id": "v11_double_slit_2d",
    "title": "Двухщелевой опыт (длинные щели, 3D): точное уравнение Шрёдингера и траектории Бома",
    "summary": ("Пакет частицы проходит две щели в стенке конечной толщины и попадает на экран; волна считается на всей "
                "плоскости без параксиального приближения, картина копится по мере прихода; ансамбль частиц идёт по "
                "траекториям Бома с метками щели; метка пути спином, закрытие щели и поток Ааронова–Бома — на ходу; в 3D "
                "— волна объёмом, частицы и картина P(x, y) (вдоль длинных щелей волна — точное произведение)."),
    "purpose": ("Настоящий двухщелевой опыт: где ломается параксиальная теория (узкие щели, большие углы), как "
                "метка пути гасит интерференцию и как идут траектории Бома."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
# an edit of v11 (review 2026-10-29 negative control): v12 imports this module
