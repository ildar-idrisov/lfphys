# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v17: light scattered by a sphere — the rainbow, its supernumerary bows, Alexander's dark band and the glory (a
wrapper over lfphys; plan P14.8, on P1).

One drop at one wavelength: the exact Mie series (lfphys.core.optics.mie) gives the phase function and the
polarisation at every angle, the scattered intensity as a polar surface around the drop for either incident
polarisation, and, for drops of a few wavelengths, the near field inside and around the drop on slice planes and in
the volume; the Debye series (core.optics.mie_debye) splits the same field into the light reflected by the surface
(p = 0), transmitted (p = 1) and reflected once or twice inside (p = 2, 3: the primary and secondary rainbows),
compared with Descartes' rays and Airy's theory (theories.approx.rainbow). A cloud of drops in sunlight: the size
average of the series (core.optics.mie_poly) wavelength after wavelength, each weighted by the Sun's spectrum (a black
body at the IAU's 5772 K, stated) and turned into a colour (tools.colour): the colour of the sky against the scattering
angle grows as the run's time adds the wavelengths, and the sky around the antisolar point is drawn from it.

World time: seconds of the run; one wavelength of white light is added every T_LAM seconds. Lengths in the 3-D scene
in units of the drop's radius a.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data as D
from lfphys.core import geometry as G
from lfphys.core.optics import mie, mie_debye as DB, mie_poly as MP
from lfphys.theories.approx import rainbow as RB
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

from .engine import drops as DR

T_LAM = 0.5                                   # world seconds per wavelength of white light
SKY_DEG = np.linspace(125.0, 180.0, 551)      # scattering angles of the sky window (0.1 deg)
SKY_TH = np.radians(SKY_DEG)
DISP_DEG = np.linspace(0.0, 180.0, 3601)      # the phase-function window (0.05 deg)
POLAR_DEG = np.linspace(0.0, 180.0, 91)       # the polar surface (2 deg bins)
X_NEAR = 45.0                                 # near fields only for drops of a few wavelengths (x <= 45)
MAX_NODES = 1600                              # size nodes per wavelength at most (beyond: coarser, flagged); the
                                              # rainbow preset at 380 nm needs 1589 with the +-4 sigma cut
N_QUAD = 3000                                 # the angular quadrature of the energy check up to N terms (~0.8 s)
AIR_SHIFT = (-0.054, 0.096)                   # deg: p = 2, 3 bows of water (10 C, 550 nm) in air against vacuum for
                                              # an illustrative n_air - 1 = 2.77e-4 (review B8-mie s11; not sourced)
MAX_PLANES = 3
DEFAULT_NORMALS = {1: (0.0, -1.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 0.0, 1.0)}
BOX = ((-2.5, -2.5, -2.5), (2.5, 2.5, 2.5))
NV = 40                                       # the near-field volume: NV^3 points
NS = 121                                      # a slice: NS x NS points
EPS = np.finfo(float).eps
M_MATCHED = 1e-3                              # |m - 1| below this: nearly index-matched, refused (P16)
STEP_BUDGET_S = 10.0                          # one wavelength of the sky at most ~this long (P16): beyond it the size
SKY_S_PER_UNIT = 1.4e-9                       # nodes get coarser (flagged); measured cost of MP.average per node x
                                              # term x angle on the CPU of 2026-11-05 (1.2-1.5 ns; a single node ~90 ns)


def _p(*a, **k):
    return Param(*a, **k)


WATER = {"index": ["water"]}
CUSTOM = {"index": ["custom"]}
SCHEMA = Schema([
    _p("radius_um", "Радиус капли ⟨r⟩, мкм", "float", 150.0, group="Капли", min=0.05, max=1000.0, log=True,
       help="Капли дождя — 0,1–1 мм, тумана — 5–50 мкм, облака — 2–20 мкм. Ближнее поле считается для капель до "
            "~2,7 мкм (x ≤ 45 на всех длинах волн)"),
    _p("width", "Разброс размеров σ/⟨r⟩", "float", 0.02, group="Капли", min=0.0, max=0.3,
       help="Гамма-распределение размеров с этим относительным разбросом; 0 — все капли одного размера"),
    _p("index", "Вещество капли", "select", "water", group="Капли",
       options=[("water", "вода: показатель IAPWS R9-97 (с дисперсией)"),
                ("custom", "заданный показатель n + iκ (без дисперсии)")]),
    _p("t_c", "Температура воды, °C", "float", 10.0, group="Капли", min=0.0, max=40.0, show_if=WATER),
    _p("n_re", "n — действительная часть показателя", "float", 1.5, group="Капли", min=0.2, max=10.0, show_if=CUSTOM),
    _p("n_im", "κ — мнимая часть (поглощение, ≥ 0)", "float", 0.0, group="Капли", min=0.0, max=10.0, show_if=CUSTOM),
    _p("n_medium", "Показатель среды вокруг", "float", 1.0, group="Капли", min=1.0, max=1.6,
       help="1 — вакуум; показатель капли берётся относительно среды"),
    _p("n_lam", "Длин волн белого света (380–760 нм)", "select", 24, group="Расчёт",
       options=[(8, "8"), (16, "16"), (24, "24"), (32, "32")]),
    _p("light", "Свет", "select", "white", group="Свет", live=True,
       options=[("white", "солнечный (белый): чёрное тело 5772 K"), ("mono", "одна длина волны")]),
    _p("lam_nm", "Длина волны, нм", "float", 550.0, group="Свет", live=True, min=380.0, max=760.0,
       help="Для одной капли (фазовая функция, ряд Дебая, ближнее поле) и для неба в режиме одной длины волны"),
], presets={
    "rainbow": {"label": "Радуга: капли 0,15 мм ± 2 % в солнечном свете — основная и вторичная дуги, полоса "
                         "Александра, дополнительные дуги", "params": {}},
    "supernumerary": {"label": "Дополнительные дуги: одинаковые капли 0,1 мм ± 0,5 %",
                      "params": {"radius_um": 100.0, "width": 0.005}},
    "big_drops": {"label": "Крупные капли 0,3 мм ± 10 %: дополнительные дуги размыты (тяжёлый расчёт, ~минута)",
                  "params": {"radius_um": 300.0, "width": 0.10, "n_lam": 16}},
    "fogbow": {"label": "Туманная радуга: капли 15 мкм ± 15 % — широкая белая дуга",
               "params": {"radius_um": 15.0, "width": 0.15}},
    "glory": {"label": "Глория: облачные капли 8 мкм ± 10 % — цветные кольца у антисолнечной точки",
              "params": {"radius_um": 8.0, "width": 0.10}},
    "near": {"label": "Ближнее поле: капля 1 мкм в свете 550 нм — фокус внутри и за каплей",
             "params": {"radius_um": 1.0, "width": 0.0, "light": "mono", "n_lam": 8}},
    "absorbing": {"label": "Поглощающий шар 2 мкм, n = 1,6 + 0,05i: внутренние лучи гаснут, радуги нет",
                  "params": {"radius_um": 2.0, "width": 0.05, "index": "custom", "n_re": 1.6, "n_im": 0.05}},
})


def _check_matched(p, lam_nm):
    """Review UX-params P16: a drop whose index equals the medium's (m = 1) scatters nothing; its checks divided by the
    zero scattering (NaN, the Debye route 1163 against 0). Nearly matched drops fail the series' checks too: the Debye
    route up to |m - 1| ~ 3e-5, the energy identity of large drops up to ~1e-4 (r = 150 µm), all pass from 3e-4
    (measured: response_checks_v-worlds/v17_m1.out, v17_m1b.out; the cause is open, STATUS). Such a drop is refused at
    the display wavelength, saying what to change. Cheap: also used by ``check_params``."""
    m = DR.index(p, lam_nm)
    if abs(m - 1.0) < M_MATCHED:
        n_drop = abs(m * float(p["n_medium"]))
        raise Refusal(f"капля почти неотличима от среды на {lam_nm:g} нм: её показатель {n_drop:.7g} против "
                      f"показателя среды {float(p['n_medium']):g} (m = {m.real:.7g}{m.imag:+.2g}i, |m − 1| < 10⁻³); "
                      "она почти ничего не рассеивает (рассеяние ∝ |m − 1|²), а проверки ряда (ряд Дебая, энергия) "
                      "здесь не выдерживают точности",
                      "измените показатель капли или «Показатель среды вокруг» так, чтобы |m − 1| ≥ 10⁻³, или "
                      "возьмите другую длину волны")


class Simulation(SlicePlanes, BaseSimulation):
    default_speed = 1.0
    speed_range = (0.05, 20.0)

    @classmethod
    def check_params(cls, params):
        """Cheap refusals before anything is built: an index-matched drop (P16)."""
        _check_matched(params, float(params["lam_nm"]))

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        if p["index"] == "custom" and float(p["n_im"]) < 0:
            raise ValueError("κ ≥ 0: поглощающее вещество (время exp(−iωt))")
        self.r_um = float(p["radius_um"])
        self.width = float(p["width"])
        self.n_med = float(p["n_medium"])
        self.lams, self.lam_w = DR.wavelengths(int(p["n_lam"]))
        self.live = {k: p[k] for k in SCHEMA.live_ids()}
        self.x_max = float(mie.size_parameter(self.r_um, DR.LAM_MIN * 1e-3, self.n_med))
        self.near = self.x_max <= X_NEAR
        if float(mie.size_parameter(self.r_um * (1 + 3 * self.width), DR.LAM_MIN * 1e-3, self.n_med)) > 2e4:
            raise ValueError("капли слишком крупные: x > 2·10⁴ на 380 нм (предел проверенной точности ряда)")
        self._ang = None   # the angular functions of the sky window (a cache, rebuilt after a checkpoint)
        self.seq = 0       # the set-up's number (a live change starts a new one)
        self.sky_seq = 0
        self.vol = None
        self._init_planes()
        self.box = BOX
        self.plane_center = (0.0, 0.0, 0.0)
        self.default_normals = DEFAULT_NORMALS
        self.plane_min_step = 0.05
        self._setup()
        if self.near:
            self._set_plane(1, self.plane_center, DEFAULT_NORMALS[1])

    def __getstate__(self):
        d = dict(self.__dict__)
        d["_ang"] = None  # recomputed on demand: identical (deterministic), and 10-20 MB smaller checkpoints
        return d

    # --- the set-up: one drop at the display wavelength, the cloud in the chosen light ------------------------------
    @property
    def lam_nm(self):
        return float(self.live["lam_nm"])

    def _setup(self):
        lam = self.lam_nm
        _check_matched(self.params, lam)  # before anything changes: a refused live change leaves the world as it was
        self.seq += 1
        self.m = DR.index(self.params, lam)
        self.x = float(mie.size_parameter(self.r_um, lam * 1e-3, self.n_med))
        self._mono()
        if self.near:
            self._volume()
            for pid in sorted(self.planes):
                pl = self.planes[pid]
                self._set_plane(pid, pl["origin"], pl["normal"], auto=pl["auto"], speed=pl["speed"])
        self._start_sky()

    def _mono(self):
        """The drop at the display wavelength: Mie on a fine angular grid (bin means for display), the Debye terms,
        ray optics and Airy, the polar surfaces, the checks."""
        m, x = self.m, self.x
        a, b = mie.coefficients(m, x)
        N = len(a)
        q = mie.efficiencies_from(a, b, x)
        self.coef = (a, b)
        n_fine = int(min(20001, max(3601, 180.0 * x / 4.0 + 1)))
        if n_fine <= 3601:
            S1, S2 = mie.amplitudes(a, b, np.radians(DISP_DEG))
            i1, i2 = np.abs(S1) ** 2, np.abs(S2) ** 2
            s11 = 0.5 * (i1 + i2)
            lo = hi = s11
            fine_deg, f1, f2 = DISP_DEG, i1, i2
        else:
            fine_deg = np.linspace(0.0, 180.0, n_fine)
            S1, S2 = mie.amplitudes(a, b, np.radians(fine_deg))
            f1, f2 = np.abs(S1) ** 2, np.abs(S2) ** 2
            edges = np.concatenate([[-1e-9], 0.5 * (DISP_DEG[1:] + DISP_DEG[:-1]), [180.0 + 1e-9]])
            i1, _, _ = DR.bin_mean(fine_deg, f1, edges)
            i2, _, _ = DR.bin_mean(fine_deg, f2, edges)
            s11 = 0.5 * (i1 + i2)
            _, lo, hi = DR.bin_mean(fine_deg, 0.5 * (f1 + f2), edges)
        # the phase function normalised to 4 pi over the sphere and the polarisation, from the bins' intensities by the
        # engine's formulas (review B8-mie, M12: they were recomputed here)
        pf = mie.phase_function_from_intensities(i1, i2, x, q["Qsca"])
        norm = 4.0 / (x * x * q["Qsca"])  # the same scale for the Debye terms, the envelope and Airy (pf = norm s11)
        P = mie.polarisation_from_intensities(i1, i2)
        # Debye terms p = 0..3 on the display grid
        dd = DB.amplitudes(m, x, np.radians(DISP_DEG), p_max=3)
        deb = [mie.phase_function_from_intensities(np.abs(dd["S1"][p]) ** 2, np.abs(dd["S2"][p]) ** 2, x, q["Qsca"])
               for p in range(4)]
        deb_P2 = mie.polarisation_from_intensities(np.abs(dd["S1"][2]) ** 2, np.abs(dd["S2"][2]) ** 2)
        self.debye_div = int(np.count_nonzero(dd["diverges_a"] | dd["diverges_b"]))
        self.debye_amp = float(dd["amplification"])
        # ray optics and Airy (approximations, for comparison) for a transparent drop
        mr = float(m.real)
        bows = {}
        airy = {}
        for p in (2, 3):
            try:
                d = RB.descartes(mr, p)
            except ValueError:
                continue
            am = RB.airy_maxima(mr, p, x, 3)
            bows[p] = {"theta": math.degrees(d["theta"]), "airy": [math.degrees(v) for v in am], "b": d["b"]}
            win = np.abs(DISP_DEG - math.degrees(d["theta"])) <= 25.0
            a2 = np.full(len(DISP_DEG), np.nan)
            th = np.radians(DISP_DEG[win])
            a2[win] = 0.5 * (RB.airy(mr, p, x, th, "s") + RB.airy(mr, p, x, th, "p")) * norm
            if float(m.imag) > 0:
                a2[:] = np.nan  # Airy's theory here is for a transparent drop
            airy[p] = a2
        self.bows = bows
        # the measured bow of the Debye term p = 2 (its maximum within 15 deg on the bright side of Descartes)
        meas = {}
        for p in bows:
            th0 = bows[p]["theta"]
            side = 1.0 if p == 2 else -1.0
            win = (side * (DISP_DEG - th0) >= -1.0) & (side * (DISP_DEG - th0) <= 15.0)
            if win.any() and np.isfinite(deb[p][win]).any():
                k = int(np.nanargmax(np.where(win, deb[p], -np.inf)))
                meas[p] = float(DISP_DEG[k])
        self.measured_bows = meas
        blobs = {"theta": DISP_DEG.astype(np.float32), "s11": pf.astype(np.float32),
                 "lo": (np.asarray(lo) * norm).astype(np.float32), "hi": (np.asarray(hi) * norm).astype(np.float32),
                 "pol": P.astype(np.float32), "pol_p2": deb_P2.astype(np.float32)}
        for p in range(4):
            blobs[f"deb{p}"] = deb[p].astype(np.float32)
        for p, a2 in airy.items():
            blobs[f"airy{p}"] = a2.astype(np.float32)
        self._msg({"type": "mono", "t": self.t, "seq": self.seq, "lam_nm": self.lam_nm, "x": x,
                   "m": [float(m.real), float(m.imag)], "n_terms": N, "n_fine": n_fine,
                   "Q": {k: float(q[k]) for k in ("Qext", "Qsca", "Qabs", "Qback", "Qpr", "g")},
                   "bows": {str(k): v for k, v in bows.items()}, "measured": {str(k): v for k, v in meas.items()},
                   "alexander": ([bows[3]["theta"], bows[2]["theta"]] if 2 in bows and 3 in bows else None),
                   "r_um": self.r_um, "debye": {"diverging_orders": self.debye_div, "amplification": self.debye_amp}},
                  blobs)
        if self.debye_div or self.debye_amp > 10.0:
            what = (f"ряд Дебая расходится на {self.debye_div} порядках (|R¹¹| > 1: так бывает у слабо поглощающей "
                    f"капли с m ≈ 1)" if self.debye_div else
                    "члены почти гасят друг друга (так бывает при m ≈ 1: дифракция против прохода почти без "
                    "преломления)")
            amp = f"{self.debye_amp:.2g}".replace(".", ",")
            self._msg({"type": "notice", "t": self.t,
                       "text": f"Члены ряда Дебая p = 0–3 этой капли до {amp} раз больше полного ответа: {what}. "
                               f"Цветные кривые — не пути света, а слагаемые, которые сокращаются; верна их сумма в "
                               f"замкнутом виде (проверка «Ряд Дебая»)."})
        # the polar surfaces (2-deg bin means of the fine grid)
        edges = np.concatenate([[-1e-9], 0.5 * (POLAR_DEG[1:] + POLAR_DEG[:-1]), [180.0 + 1e-9]])
        p1, _, _ = DR.bin_mean(fine_deg, f1, edges)
        p2, _, _ = DR.bin_mean(fine_deg, f2, edges)
        for mode, label, vis in (("u", "Рассеянный свет, неполяризованный падающий (лог. шкала, 5 порядков)", True),
                                 ("x", "Рассеянный свет при поляризации падающего вдоль x", False),
                                 ("y", "Рассеянный свет при поляризации падающего вдоль y", False)):
            pos, idx, rgb = DR.polar_mesh(POLAR_DEG, p2, p1, mode)
            self._msg({"type": "mesh", "t": self.t, "id": f"polar_{mode}", "count": int(len(pos)), "opacity": 0.55,
                       "visible": vis, "label": label}, {"pos": pos, "idx": idx, "rgb": rgb})
        pts, col = DR.ray_fans(mr)
        self._msg({"type": "lines", "t": self.t, "id": "rays",
                   "label": (f"Лучи (геометрическая оптика, m = {mr:.4g}): серые — отражение p = 0, голубые — "
                             f"проход p = 1, жёлтые — одно внутреннее отражение p = 2, лиловые — два, p = 3"
                             + ("; яркие — лучи Декарта" if bows else "; лучей Декарта нет (радуга p = 2 только при "
                                                                      "1 < m < 2)")
                             + ("; при m < 1 внутрь входят лишь лучи с b < m" if mr < 1.0 else ""))},
                  {"pts": pts.reshape(-1), "rgb": col.reshape(-1)})
        self._mono_checks(a, b, q, dd)

    def _mono_checks(self, a, b, q, dd):
        """The drop's checks. Which of them test the coefficients' values (review B8-mie, M3): only `debye` (a second
        route to the same coefficients) and `wiscombe` (the engine against published numbers, at fixed spheres);
        `theorem`, `energy` and `mueller` are identities of the series' structure, labelled as such: they test the
        angular functions, the quadrature and the arithmetic, and stay at round-off when D_n, psi_n or chi_n are
        wrong (tests/test_v17_mie_scattering.py shows what each one catches)."""
        x, m = self.x, self.m
        N = len(a)
        S1, S2 = mie.amplitudes(a, b, np.array([0.0]))
        self._check("theorem", "Угловая сумма при θ = 0 против Q_ext (оптическая теорема в форме ряда)", q["Qext"],
                    4.0 / x ** 2 * float(S1[0].real), tol=100 * N * EPS, group="Капля: точный ряд",
                    note=f"тождество формы ряда (πₙ(1) = τₙ(1) = n(n+1)/2): верно для любых коэффициентов, проверяет "
                         f"угловые функции и сумму при θ = 0, а не aₙ, bₙ; N = {N} членов, допуск — 100 N ε округления")
        if m.imag == 0 and N <= N_QUAD:
            r = mie.angular_integrals(a, b, x)
            self._check("energy", "Энергия: рассеянное по всем углам против Q_ext (капля не поглощает)", r["Qsca"],
                        q["Qext"], tol=r["rel_bound"], group="Капля: точный ряд",
                        note=f"∫(|S₁|² + |S₂|²) по сфере — квадратура Фейера (второе правило, {r['n_nodes']} узлов, "
                             f"точна для этих многочленов) против Q_ext из коэффициентов. При вещественном m это "
                             f"тождество формы ряда (каждое aₙ = A/(A − iB) с вещественными A, B, Re aₙ = |aₙ|² при "
                             f"любых Dₙ, ψₙ, χₙ): проверяет угловые функции, суммы и квадратуру, не коэффициенты. "
                             f"Допуск — выведенная граница округления u(x²Q²_ext/(2Q_sca) + 8N + 16): узлы — "
                             f"округлённые косинусы под пиком вперёд ширины ~1/x²")
        elif m.imag == 0:
            dev = max(float(np.max(np.abs(a.real - np.abs(a) ** 2))), float(np.max(np.abs(b.real - np.abs(b) ** 2))))
            tol = 16 * mie.U
            self._check("energy", "Энергия: Re aₙ = |aₙ|², Re bₙ = |bₙ|² (капля не поглощает)", dev, 0.0, tol=tol,
                        ok=dev <= tol, group="Капля: точный ряд",
                        note=f"наибольшее отклонение по {N} порядкам. Тождество формы ряда: верно при любых Dₙ, ψₙ, "
                             f"χₙ, пока счёт вещественный — проверяет, что в коэффициенты не попала мнимая часть, а не "
                             f"их значения. Допуск 16u: вещественная часть знаменателя совпадает с числителем бит в "
                             f"бит, остаётся округление комплексного деления. Квадратура по углам — до N = {N_QUAD}")
        c = DB.check_against_mie(m, x, c=dd)
        k = int(np.argmax(c["err"] / c["tol"]))
        self._check("debye", "Ряд Дебая: сумма всех p против коэффициентов Ми (второй путь счёта)", c["max_err"], 0.0,
                    tol=float(c["tol"][k]), ok=c["ok"], group="Капля: точный ряд",
                    note=f"(1 − R²² − T²¹T¹²/(1 − R¹¹))/2 по отношениям функций Ханкеля и вронскиану против aₙ, bₙ "
                         f"ряда Ми (Dₙ вниз, ψₙ по Миллеру, χₙ вверх), по всем {c['N']} порядкам, в долях "
                         f"наибольшего коэффициента: проверка значений коэффициентов. Допуск по порядкам "
                         f"u(1000N + 32x|daₙ/dx|/max|a|) (обусловленность у узких резонансов; mie_debye.ACCURACY): "
                         f"от {float(c['tol'].min()):.1e} до {float(c['tol'].max()):.1e}; наибольшее отношение "
                         f"отклонения к допуску {c['worst']:.2g} (порядок {k + 1})")
        w = mie.wiscombe_self_test()
        self._check("wiscombe", "Движок против опубликованных значений Уискомба (1979, x = 100, m = 1,5 и 1,5 − 0,1i)",
                    w["worst"], None, tol=1.0, ok=w["worst"] <= 1.0, group="Капля: точный ряд",
                    note=f"{w['n']} напечатанных величин (Q_ext, Q_sca, g, S₁(0), S₁(90°), S₂(90°), S₁(180°)) — "
                         f"наибольшее отклонение в половинах последнего напечатанного знака (≤ 1 — совпадает): "
                         f"проверка значений коэффициентов по опубликованным числам, для двух шаров, не для этой "
                         f"капли")
        r = mie.mueller(*mie.amplitudes(a, b, np.radians(DISP_DEG[::10])))
        dev = float(np.max(np.abs(r["S11"] ** 2 - r["S12"] ** 2 - r["S33"] ** 2 - r["S34"] ** 2) / r["S11"] ** 2))
        self._check("mueller", "Матрица Мюллера: S11² = S12² + S33² + S34² (тождество)", dev, 0.0, tol=1e-10,
                    ok=dev <= 1e-10, group="Капля: точный ряд",
                    note="верно для любых комплексных S₁, S₂ (матрица одной частицы чистая): проверяет только "
                         "арифметику mie.mueller; наибольшее отклонение по 361 углу, отн.")
        if self.params["index"] == "water":
            lam, n_tab = D.IAPWS97_RINDEX_CHECK_0C_01MPA[1]
            n_eng = float(D.water_index(lam * 1e3, 0.0))
            self._check("water", "Показатель воды IAPWS при 589 нм и 0 °C против таблицы проверки (табл. 3)", n_eng,
                        n_tab, tol=1e-6 / n_tab, ok=abs(n_eng - n_tab) <= 1e-6, group="Вода",
                        note=f"плотность — IAPWS SR6-08; этот мир: n({self.lam_nm:g} нм, {self.params['t_c']:g} °C) = "
                             f"{abs(self.m * self.n_med):.6f}")
        transparent = abs(m.imag) <= 1e-6 and x >= 50.0
        for p, name in ((2, "первичная"), (3, "вторичная")):
            if transparent and p in self.bows and p in self.measured_bows:
                bw = self.bows[p]
                d = self.measured_bows[p] - bw["airy"][0]
                self._check(f"bow{p}", f"Радуга p = {p} ({name}): максимум члена Дебая против максимума Эйри",
                            self.measured_bows[p], bw["airy"][0], "°", tol=None, info=True, group="Радуга",
                            note=f"максимум |S^({p})|² по ряду Дебая (сетка 0,05°) — {self.measured_bows[p]:.3f}°, "
                                 f"разница с Эйри {d:+.3f}°; угол Декарта {bw['theta']:.3f}°, первый максимум Эйри "
                                 f"{bw['airy'][0]:.3f}° (сдвиг ~x^(−2/3) в светлую сторону); при x = {x:.4g} теория "
                                 f"Эйри — приближение")
        if abs(m.imag) <= 1e-6 and 2 in self.bows and 3 in self.bows:
            self._check("alexander", "Полоса Александра между дугами (углы рассеяния по Декарту)",
                        self.bows[2]["theta"] - self.bows[3]["theta"], None, "°", tol=None, info=True, group="Радуга",
                        note=f"вторичная {self.bows[3]['theta']:.3f}°, первичная {self.bows[2]['theta']:.3f}°: между "
                             f"ними лучи p = 2 и 3 не выходят")

    # --- the near field -----------------------------------------------------------------------------------------------
    def _volume(self):
        g = np.linspace(BOX[0][0], BOX[1][0], NV)
        Z, X, Y = np.meshgrid(g, g, g, indexing="ij")
        pts = np.stack([X, Y, Z], -1)
        f = mie.near_field(self.m, self.x, pts)
        I = np.sum(np.abs(f["E"]) ** 2, -1)
        peak = float(I.max())
        self.vol_peak = peak
        self._msg({"type": "volume", "t": self.t, "id": "field", "dims": [NV, NV, NV],
                   "quantity": {"label": "|E|²/|E₀|²", "unit": "", "peak": peak},
                   "note": f"|E|² падающего плюс рассеянного (снаружи) и внутреннего поля, сетка {NV}³"},
                  {"data": (I / peak).astype(np.float32).reshape(-1)})
        # the boundary conditions on the drop's surface (24 points)
        k = np.arange(24)
        th = np.arccos(1 - 2 * (k + 0.5) / 24)
        ph = k * math.pi * (3 - math.sqrt(5))
        nrm = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
        d = 1e-10
        fo, fi = mie.near_field(self.m, self.x, nrm * (1 + d)), mie.near_field(self.m, self.x, nrm * (1 - d))
        tE = fo["E"] - fi["E"]
        tE = tE - np.sum(tE * nrm, -1)[:, None] * nrm
        tH = fo["H"] - fi["H"]
        tH = tH - np.sum(tH * nrm, -1)[:, None] * nrm
        s = float(np.abs(fo["E"]).max())
        err = max(float(np.abs(tE).max()), float(np.abs(tH).max()) / abs(self.m)) / s
        tol = 20 * self.x * abs(self.m) ** 2 * d + 1e-11
        self._check("boundary", "Ближнее поле: касательные E и H непрерывны на поверхности капли", err, 0.0, tol=tol,
                    ok=err <= tol, group="Ближнее поле",
                    note="24 точки поверхности, поле в 10⁻¹⁰ a снаружи и внутри; допуск — изменение поля на этом "
                         "зазоре (20 x |m|² · 10⁻¹⁰) плюс округление. Проверяет сборку полей (сферические гармоники, "
                         "внутренние cₙ, dₙ, Z·H) против aₙ, bₙ; сами Dₙ, ψₙ, χₙ входят в обе стороны согласованно — "
                         "их значения проверяет «Ряд Дебая»")

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        n = 61 if coarse else NS
        s = np.linspace(s_rng[0], s_rng[1], n)
        t = np.linspace(t_rng[0], t_rng[1], n)
        P = G.plane_points(pl, s, t)
        f = mie.near_field(self.m, self.x, P)
        E = f["E"]
        ver = {"points": 0, "note": "грубый срез при автосмещении, без сверки"}
        if not coarse:
            ver = self._verify_plane(pl)
        return {"s": s, "t": t, "E": E, "verify": ver, "plane": pl, "coarse": coarse}

    def _verify_plane(self, pl):
        """Points of the plane on the drop's surface (the circle where the plane cuts the sphere): the tangential E
        just inside and outside agree (the slice's field is the engine's total field there)."""
        o = np.asarray(pl.origin, float)
        n = np.asarray(pl.normal, float)
        dist = float(o @ n)
        if abs(dist) >= 0.999:
            return {"points": 0, "note": "плоскость не пересекает каплю: сверять на поверхности нечего"}
        c = dist * n
        rr = math.sqrt(1 - dist * dist)
        u, v = np.asarray(pl.u, float), np.asarray(pl.v, float)
        ang = np.linspace(0, 2 * math.pi, 12, endpoint=False)
        pts = c + rr * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v)
        nr = pts / np.linalg.norm(pts, axis=-1, keepdims=True)
        d = 1e-10
        fo, fi = mie.near_field(self.m, self.x, nr * (1 + d)), mie.near_field(self.m, self.x, nr * (1 - d))
        t = fo["E"] - fi["E"]
        t = t - np.sum(t * nr, -1)[:, None] * nr
        err = float(np.abs(t).max()) / float(np.abs(fo["E"]).max())
        tol = 20 * self.x * abs(self.m) ** 2 * d + 1e-11
        return {"points": 12, "max_err": err, "tol": tol, "ok": err <= tol}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        pd = self.planes[pid]
        E = sl["E"]
        I = np.sum(np.abs(E) ** 2, -1)
        peak = float(np.nanmax(I))
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(I.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": "mie", "route_label": "ряд Ми: падающая волна + рассеянное поле снаружи, "
                                                             "внутреннее поле внутри капли; фаза — arg Eₓ",
                "exact": True, "approximation": False, "reason": "", "verify": sl["verify"],
                "verify_title": "непрерывность касательного E на окружности, где срез пересекает каплю",
                "units": "a", "depth": False,
                "quantity": {"label": "|E|²/|E₀|²", "unit": "", "peak": peak}}
        blobs = {"I": (I / peak).astype(np.float32)}
        if not sl["coarse"]:
            blobs["phase"] = np.angle(E[..., 0]).astype(np.float32)
        self._msg(meta, blobs)
        ver = sl["verify"]
        if ver.get("points"):
            self._check(f"plane_{pid}", f"Срез {pid}: касательное E на поверхности капли непрерывно", ver["max_err"],
                        0.0, tol=ver["tol"], ok=ver["ok"], group="Ближнее поле",
                        note="12 точек окружности пересечения среза с каплей, в 10⁻¹⁰ a снаружи и внутри")

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):
            self._check(f"plane_{pid}", f"Срез {pid}: убран", None, None, info=True, group="Ближнее поле",
                        note="последняя сверка этого среза — в записи запуска")

    # --- the cloud in sunlight ----------------------------------------------------------------------------------------
    def _sky_lams(self):
        if self.live["light"] == "mono":
            return np.array([self.lam_nm]), np.array([1.0])
        return self.lams, self.lam_w

    def _start_sky(self):
        self.sky_seq += 1
        self.sky_t0 = self.t
        self.sky_k = 0
        self.XYZ = np.zeros((len(SKY_DEG), 3))
        self.Ysum = np.zeros(len(SKY_DEG))
        self.Ypol = np.zeros(len(SKY_DEG))
        self.sky_err = 0.0
        self.sky_tail = 0.0
        self.sky_coarse_dx = 0.0
        lam, _ = self._sky_lams()
        self.sky_n = len(lam)
        self._msg({"type": "sky_start", "t": self.t, "seq": self.sky_seq, "n": self.sky_n,
                   "lams": [float(v) for v in lam], "mode": self.live["light"], "t_lam": T_LAM,
                   "deg": [float(SKY_DEG[0]), float(SKY_DEG[-1]), len(SKY_DEG)]})

    def _angular(self, N):
        if self._ang is None or self._ang[0].shape[0] < N:
            self._ang = mie.angular(np.cos(SKY_TH), N)
        return self._ang

    def _sky_step(self):
        lams, ws = self._sky_lams()
        k = self.sky_k
        lam = float(lams[k])
        m = DR.index(self.params, lam)
        nodes = MP.size_nodes(self.r_um, self.width, lam * 1e-3, self.n_med, max_nodes=self._max_nodes(lam))
        N = mie.n_terms(float(nodes["x"].max()))
        av = MP.average(m, lam * 1e-3, nodes, SKY_TH, self.n_med, angular=self._angular(N))
        cm = DR.cmf(lam)
        if self.live["light"] == "mono":
            wgt = 1.0
            self.XYZ = av["dsdo"][:, None] * cm[None, :]
            self.Ysum = cm[1] * av["dsdo"]
            self.Ypol = cm[1] * av["dsdo_pol"]
        else:
            wgt = float(ws[k] * DR.sun(lam))
            self.XYZ += wgt * av["dsdo"][:, None] * cm[None, :]
            self.Ysum += wgt * cm[1] * av["dsdo"]
            self.Ypol += wgt * cm[1] * av["dsdo_pol"]
        rel = float(np.max(av["err"]) / np.max(av["dsdo"])) if np.max(av["dsdo"]) > 0 else 0.0
        self.sky_err = max(self.sky_err, rel)
        self.sky_tail = max(self.sky_tail, float(av["tail"]))
        if nodes["coarse"]:
            self.sky_coarse_dx = max(self.sky_coarse_dx, float(nodes["dx"]))
        rgb = DR.strip_rgb(self.XYZ)
        Y = self.Ysum / max(float(self.Ysum.max()), 1e-300)
        pol = np.where(self.Ysum > 0, -self.Ypol / np.where(self.Ysum > 0, self.Ysum, 1.0), 0.0)
        self.sky_k += 1
        self._msg({"type": "sky", "t": self.t, "seq": self.sky_seq, "k": k, "n": self.sky_n, "lam_nm": lam,
                   "m": [float(m.real), float(m.imag)], "n_nodes": int(nodes["w"].size), "dx": nodes["dx"],
                   "coarse": bool(nodes["coarse"]), "rel_err": rel, "C_sca": av["C_sca"], "C_ext": av["C_ext"],
                   "tail": float(av["tail"])},
                  {"dsdo": av["dsdo"].astype(np.float32), "rgb": rgb.reshape(-1), "Y": Y.astype(np.float32),
                   "pol": pol.astype(np.float32)})
        if self.sky_k == self.sky_n:
            self._sky_done()

    def _max_nodes(self, lam):
        """Size nodes at this wavelength within MAX_NODES and the step's time budget (review UX-params P16: drops of
        1 mm took ~19 s per wavelength, «⏭» computed all 24 at once, > 2 min): the cost of the size average is ~nodes x
        terms x angles; beyond the budget the nodes are coarser, and the sky's check says so (the ripple and the
        supernumerary bows of such drops are washed out anyway)."""
        hi = self.r_um * (1.0 + 4.0 * self.width) if self.width > 0 else self.r_um
        N = mie.n_terms(float(mie.size_parameter(hi, lam * 1e-3, self.n_med)))
        cap = int(STEP_BUDGET_S / (SKY_S_PER_UNIT * N * len(SKY_TH)))
        return max(9, min(MAX_NODES, cap))

    def _sky_done(self):
        lams, _ = self._sky_lams()
        self._check("sky_sum", "Небо: оценка ошибки суммы по размерам (наибольшая по длинам волн)", self.sky_err, None,
                    tol=None, info=True, group="Облако капель",
                    note=f"наибольшая по углам разность двух чередующихся половинных сумм по размерам, в долях "
                         f"максимума ⟨dσ/dΩ⟩: оценка наибольшей ошибки по порядку величины (на пресетах настоящая "
                         f"наибольшая ошибка 0,1–3 этой оценки), не граница и не ошибка в каждом угле; узкие резонансы "
                         f"ряда шаг по размеру не разрешает"
                         + (f". Не входит: обрезка распределения на ±4σ — отрезано {self.sky_tail:.1e} вероятности, её "
                            f"смещение ≲ 3 этой доли максимума" if self.width > 0 else "; капли одного размера")
                         + ("; грубая выборка размеров (шаг по x до " + f"{self.sky_coarse_dx:.2g}".replace(".", ",")
                            + "): рябь и дополнительные дуги здесь размыты в шум" if self.sky_coarse_dx else ""))
        Y = self.Ysum
        lo = (SKY_DEG >= 132.0) & (SKY_DEG <= 145.0)
        if lo.any() and 2 in self.bows and self.live["light"] == "white" and self.params["index"] == "water":
            k = int(np.argmax(np.where(lo, Y, -np.inf)))
            d550 = RB.descartes(float(DR.index(self.params, 550.0).real), 2)
            th_d = math.degrees(d550["theta"])
            self._check("sky_bow", "Небо: самый яркий угол основной дуги (белый свет) против Декарта при 550 нм",
                        float(SKY_DEG[k]), th_d, "°", tol=None, info=True, group="Облако капель",
                        note=f"яркость Y по {len(lams)} длинам волн, размер {self.r_um:g} мкм ± "
                             f"{100 * self.width:g} %: максимум на {float(SKY_DEG[k]) - th_d:+.2f}° от угла Декарта — "
                             f"смещён в светлую сторону на сдвиг Эйри и размыт по длинам волн")
        self._msg({"type": "event", "t": self.t, "kind": "sky",
                   "text": f"небо досчитано: {len(lams)} длин волн, капли {self.r_um:g} мкм ± {100 * self.width:g} %"})

    # --- checks and messages ---------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group="Капля"):
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

    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        self._msg({"type": "arrow", "t": self.t, "id": "incident", "from": [0.0, 0.0, -2.45], "vec": [0.0, 0.0, 1.0],
                   "label": "падающий свет (вдоль +z)", "layer": "Падающая волна", "color": "#ffe9a0"})
        self._msg({"type": "arrow", "t": self.t, "id": "polarisation", "from": [0.0, 0.0, -2.2], "vec": [0.6, 0.0, 0.0],
                   "label": "поляризация E вдоль x", "layer": "Поляризация падающей волны", "color": "#7fb7ff"})
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- time ------------------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        dt = t_target - self.t
        self.t = t_target
        while self.sky_k < self.sky_n and self.t >= self.sky_t0 + (self.sky_k + 1) * T_LAM - 1e-12:
            self._sky_step()
        if self.near:
            self._advance_planes(t_target, dt)

    def max_step(self):
        return T_LAM

    def next_event_time(self):
        """The next wavelength of the sky (P16: «⏭» to the end of the scan computed every wavelength at once)."""
        if self.sky_k >= self.sky_n:
            return None
        return self.sky_t0 + (self.sky_k + 1) * T_LAM

    def frame(self):
        return {"seq": self.seq, "sky_seq": self.sky_seq, "k": self.sky_k, "n": self.sky_n}, {}

    # --- live set-up ---------------------------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        merged, errors = SCHEMA.coerce_live(self.live, values)
        if errors:
            raise ValueError("; ".join(errors))
        old = self.live
        self.live = merged
        try:
            self._setup()
        except Exception:
            self.live = old
            raise
        what = "солнечный свет" if merged["light"] == "white" else f"одна длина волны {float(merged['lam_nm']):g} нм"
        return f"свет: {what}; капля при {float(merged['lam_nm']):g} нм — заново"

    def engine_modules(self):
        mods = ["core.optics.mie", "core.optics.mie_debye", "core.optics.mie_poly", "core.optics.radiation",
                "core.data", "theories.approx.rainbow", "tools.colour"]
        if self.near:
            mods.append("core.geometry")
        return mods

    def header(self):
        p = self.params
        mat = ("вода" if p["index"] == "water" else f"n = {float(p['n_re']):g} + {float(p['n_im']):g}i")
        approximations = ["однократное рассеяние разреженным облаком капель: интенсивности капель складываются",
                          "солнечный свет — чёрное тело 5772 K (без линий поглощения и атмосферы); угловой размер "
                          "Солнца (0,5°) не учтён: дуги в небе ещё размыты на полградуса",
                          "капли — шары (крупные капли дождя сплюснуты)"]
        if p["index"] == "water":
            approximations.append("вода без поглощения: IAPWS даёт только действительную часть показателя (поэтому "
                                  "узкие резонансы ряда здесь уже, чем у настоящей воды)")
        if self.n_med == 1.0:
            def deg(v):
                return f"{v:+.2f}".replace("-", "−").replace(".", ",") + "°"
            approximations.append("среда вокруг капли — вакуум (n = 1): в воздухе показатель капли относительно среды "
                                  "меньше в n_воздуха раз, и углы дуг сдвигаются на доли градуса (для воды при 10 °C и "
                                  f"550 нм: p = 2 на {deg(AIR_SHIFT[0])}, p = 3 на {deg(AIR_SHIFT[1])} при "
                                  "иллюстративном n_воздуха − 1 = 2,77·10⁻⁴)")
        else:
            approximations.append(f"среда — однородная, прозрачная, без дисперсии: n = {self.n_med:g}")
        if self.width > 0:
            approximations.append("размеры — гамма-распределение, обрезанное на ±4σ (отрезанная доля — в проверке "
                                  "«Небо: оценка ошибки»)")
            nd = MP.size_nodes(self.r_um, self.width, DR.LAM_MIN * 1e-3, self.n_med, max_nodes=MAX_NODES)
            if nd["coarse"]:
                dx = f"{nd['dx']:.2g}".replace(".", ",")
                approximations.append(f"грубая выборка размеров: на коротких волнах шаг по x до {dx} (нужно ≤ 0,25, "
                                      f"узлов не больше {MAX_NODES}) — рябь интенсивности и дополнительные дуги в небе "
                                      f"размыты в шум, расчёт тяжёлый")
        objects = [{"id": "drop", "label": f"Капля ({mat}), радиус a = {self.r_um:g} мкм — в сцене радиус 1",
                    "kind": "sphere", "center": [0.0, 0.0, 0.0], "radius": 1.0, "visible": True}]
        layers = []
        if self.near:
            layers.append({"id": "field", "label": "Поле |E|² в объёме (внутри и вокруг капли)", "kind": "volume",
                           "visible": True, "look": {"density": 0.6, "threshold": 0.05}})
        views = [["iso", "Изо", "Изометрия (F)", [0.45, -0.75, -0.5]],
                 ["side", "Сбоку", "Плоскость xz: свет слева направо, поляризация вверх", [0.0, -1.0, 0.0]],
                 ["back", "К Солнцу спиной", "Взгляд наблюдателя радуги: вдоль света, Солнце за спиной",
                  [0.0, 0.0, -1.0]]]
        return {
            "title": f"Рассеяние света каплей: {mat}, ⟨r⟩ = {self.r_um:g} мкм",
            "text": ("Точный ряд Ми для одной капли: фазовая функция, поляризация, рассеянный свет поверхностью вокруг "
                     "капли, ближнее поле для малых капель; ряд Дебая разделяет отражённый свет (p = 0), прошедший "
                     "(p = 1) и отражённый внутри (p = 2 — первичная радуга, p = 3 — вторичная). Облако капель в "
                     "солнечном свете: цвет неба против угла рассеяния складывается длина волны за длиной волны."),
            "actions": [],
            "approximations": approximations,
            "scene3d": {"box": [list(BOX[0]), list(BOX[1])], "units": "a", "objects": objects, "layers": layers,
                        "views": views, "up": [1.0, 0.0, 0.0],
                        "planes": {"max": MAX_PLANES if self.near else 0, "center": [0.0, 0.0, 0.0],
                                   "defaults": {str(i): list(v) for i, v in DEFAULT_NORMALS.items()}}},
            "drop": {"r_um": self.r_um, "width": self.width, "index": p["index"], "t_c": float(p["t_c"]),
                     "n_medium": self.n_med, "near": self.near, "x_max": self.x_max},
            "sky": {"deg": [float(SKY_DEG[0]), float(SKY_DEG[-1]), len(SKY_DEG)], "t_lam": T_LAM},
            "units": {"t": "с (время мира: одна длина волны за 0,5 с)", "x": "a"},
        }, {}


VIZ = {
    "id": "v17_mie_scattering",
    "title": "Рассеяние Ми на капле: радуга и глория",
    "summary": ("Точный ряд Ми для капли воды: фазовая функция и поляризация, ряд Дебая (отражение, проход, внутренние "
                "отражения) против лучей Декарта и теории Эйри, ближнее поле малой капли; облако капель в солнечном "
                "свете — цвет неба: радуга, дополнительные дуги, полоса Александра, глория."),
    "purpose": ("Увидеть, откуда берутся радуга и её дополнительные дуги, чем волновая теория отличается от лучевой, "
                "почему дуги размываются у капель разного размера и откуда у антисолнечной точки глория."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
