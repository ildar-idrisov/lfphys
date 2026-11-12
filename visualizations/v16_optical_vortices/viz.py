# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v16: optical vortices — Laguerre-Gauss beams, orbital angular momentum and the rotational Doppler effect (a wrapper
over lfphys; plan P14.7).

The beam of a world comes from the engine: a Laguerre-Gauss mode LG_pl with its waist at z = 0 or a Gaussian behind a
spiral phase plate, either as the exact vector beam of the same spectrum (lfphys.core.optics.beams.VortexBeam: plane
waves of helicity sigma, an exact solution of Maxwell's equations) or in the paraxial approximation
(lfphys.theories.approx.beams_paraxial, flagged); or a Gaussian on a fork hologram propagated by the angular spectrum
(the thin masks of lfphys.theories.approx.beams_thin_masks; core.optics.angular_spectrum). The scene: the helical
surfaces of equal phase (sheets of
arg psi = omega t, revealed per phase of the slowed optical period as the world's time reaches it), the intensity as a
volume, the energy flow lines (Poynting vector; the orbital current too), slice planes with intensity and phase, the
generator, and a rotating element — a spinning rough disc (Lavery et al. 2013) or a turning Dove prism (Courtial et
al. 1998) — whose detector's samples are taken as the time runs; their spectrum gives the measured beat, compared with
the closed form. The angular momentum per photon (orbital, spin, total; per unit length in the canonical split, and
Barnett's split of the flux through the plane) is measured from the field on a plane.
Units: micrometres; world time in seconds (the optical phase is shown slowed: one period per t_show of world time).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import eval_genlaguerre

from lfphys.core import geometry as G
from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import beams as B
from lfphys.core.optics import beams_rotation as ROT
from lfphys.theories.approx import beams_paraxial as PX
from lfphys.theories.approx import beams_thin_masks as TM
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

from .engine import apparatus as A

MAX_PLANES = 3
DEFAULT_NORMALS = {1: (0.0, 0.0, 1.0), 2: (0.0, -1.0, 0.0), 3: (1.0, 0.0, 0.0)}
NB = 16          # phases of the displayed optical period (equiphase sheets)
FLOW_STEPS = 220  # RK4 steps of the flow lines over the region's depth
NS, NT = 150, 150
BEAMS = {"gen": ["mode", "spp"]}
ROTS = {"gen": ["mode", "spp"], "rot": ["disc", "dove"]}


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("gen", "Источник вихря", "select", "mode", group="Пучок",
       options=[("mode", "мода Лагерра–Гаусса LG_pl (перетяжка в z = 0)"),
                ("spp", "гауссов пучок за спиральной фазовой пластинкой (z = 0)"),
                ("fork", "гауссов пучок на голограмме-«вилке» (z = 0)")]),
    _p("l", "Топологический заряд l", "int", 3, group="Пучок", min=-6, max=6),
    _p("p", "Радиальный индекс p", "int", 0, group="Пучок", min=0, max=3, show_if={"gen": ["mode"]}),
    _p("w0", "Перетяжка w0, мкм", "float", 1.5, group="Пучок", min=0.3, max=6.0,
       help="Ширина спектра источника (моды LG или гауссова пучка за пластинкой). Точная модель берёт из спектра только "
            "распространяющиеся волны (q ≤ k): при w0 ≲ λ это уже не перетяжка названного источника — мир помечается, "
            "а при потере больше 10 % мощности источника не строится."),
    _p("lam", "Длина волны λ, мкм", "float", 1.0, group="Пучок", min=0.4, max=1.6),
    _p("pol", "Поляризация", "select", "+1", group="Пучок", show_if=BEAMS,
       options=[("+1", "круговая, σ = +1"), ("-1", "круговая, σ = −1"), ("lin", "линейная (x)")]),
    _p("model", "Модель пучка", "select", "exact", group="Пучок", show_if=BEAMS,
       options=[("exact", "точная: векторное решение уравнений Максвелла"),
                ("paraxial", "параксиальная (приближение): мода × однородная поляризация")]),
    _p("zspan", "Длина области, в z_R", "float", 1.5, group="Пучок", min=0.4, max=3.0, show_if=BEAMS),
    _p("period", "Период голограммы Λ, мкм", "float", 2.5, group="Голограмма", min=1.0, max=8.0,
       show_if={"gen": ["fork"]}),
    _p("kind", "Голограмма", "select", "binary", group="Голограмма", show_if={"gen": ["fork"]},
       options=[("amplitude", "амплитудная (1 + cos)/2"), ("binary", "бинарная амплитудная"),
                ("blazed", "фазовая с блеском (всё в 1-й порядок)")]),
    _p("rot", "Вращающийся элемент", "select", "disc", group="Вращение", show_if=BEAMS,
       options=[("disc", "шероховатый диск, детектор за фильтром мод ±l (Лавери 2013)"),
                ("dove", "призма Дове в плече интерферометра (Куртиаль 1998)"), ("none", "нет")]),
    _p("f_rot", "Частота вращения f, Гц", "float", 5.0, group="Вращение", min=0.0, max=40.0, live=True,
       show_if=ROTS, help="Меняется на ходу: новая серия измерений начинается с этого момента."),
    _p("t_show", "Оптическая фаза на экране: период, мс времени мира", "float", 400.0, group="Время", min=40.0,
       max=4000.0, help="Свет с частотой ~10¹⁵ Гц показан замедленно: один оптический период за это время мира."),
], presets={
    "lg3": {"label": "LG₀³, σ = +1: три винтовых фронта, точная модель, вращающийся диск", "params": {}},
    "tight": {"label": "Острая фокусировка: l = 1, σ = −1, w0 = 0,6 λ — продольное поле и спин-орбитальное расщепление",
              "params": {"l": 1, "pol": "-1", "w0": 0.6, "zspan": 1.5, "rot": "none"}},
    "tight_par": {"label": "То же в параксиальной модели (приближение): чего она не видит",
                  "params": {"l": 1, "pol": "-1", "w0": 0.6, "zspan": 1.5, "rot": "none", "model": "paraxial"}},
    "lg_p2": {"label": "LG₂¹: три кольца, фронты со скачками фазы на узлах", "params": {"l": 1, "p": 2, "w0": 1.2}},
    "spp": {"label": "Спиральная фазовая пластинка, l = 2: заряд 2, не одна мода LG; орбитальный момент скалярного поля "
                     "2ħ на фотон, у векторного L_z = l + σ(1 − ⟨cos θ⟩)",
            "params": {"gen": "spp", "l": 2, "w0": 1.5}},
    "dove": {"label": "Призма Дове вращается: сдвиг частоты 2|l|f у пучка l = 2", "params": {"l": 2, "rot": "dove"}},
    "l0": {"label": "Контроль: гауссов пучок без вихря (l = 0) — биений нет", "params": {"l": 0}},
    "lin": {"label": "Линейная поляризация, l = 1: J_z = l в среднем, спин нулевой", "params": {"l": 1, "pol": "lin"}},
    "fork": {"label": "Голограмма-«вилка», l = 1: порядок m несёт заряд m·l",
             "params": {"gen": "fork", "l": 1, "w0": 4.0, "period": 2.5}},
})


class Simulation(SlicePlanes, BaseSimulation):
    default_speed = 0.05
    speed_range = (0.001, 2.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._buf = []
        p = self.params
        self.l = int(p["l"])
        self.lam = float(p["lam"])
        self.k = 2 * math.pi / self.lam
        self.T_show = float(p["t_show"]) / 1000.0
        self.fork = None
        self.beam = None
        if p["gen"] == "fork":
            self._init_fork()
        else:
            self._init_beam()
        self._init_planes()
        self.plane_min_step = self.lam / 4
        self.default_normals = DEFAULT_NORMALS
        self._set_plane(1, self.plane_center, DEFAULT_NORMALS[1])

    # --- the world ------------------------------------------------------------------------------------------------
    def _init_beam(self):
        p = self.params
        self.beam = bm = A.Beam(p["gen"], p["model"], self.l, int(p["p"]) if p["gen"] == "mode" else 0,
                                float(p["w0"]), self.lam, p["pol"], float(p["zspan"]))
        self.rot = p["rot"]
        L = bm.z1 - bm.z0
        self.z_rot = bm.z1 - 0.10 * L if self.rot != "none" else None
        self.z_end = self.z_rot if self.z_rot is not None else bm.z1  # the light is computed up to the element
        self.box = ((-bm.half, -bm.half, bm.z0), (bm.half, bm.half, bm.z1))
        self.zc = 0.0 if p["gen"] == "mode" else bm.z0 + 0.5 * (self.z_end - bm.z0)
        self.plane_center = (0.0, 0.0, self.zc)
        self.sigma_bar = sum(s * abs(a) ** 2 for s, a in bm.amp.items()) / sum(abs(a) ** 2 for a in bm.amp.values())
        # the detector and its time series
        self.f_rot = float(p["f_rot"])
        self.angle = 0.0          # the element's turn (rad), integrated over the changes of f
        self.t_angle = 0.0        # the time the angle refers to
        self.seg = 0
        self.seg_t0 = 0.0
        self.seg_n = 0
        self.samples = []         # (t, value, complex) of the current segment
        self.n_sent = 0
        self.all_n = 0
        self.det = None
        if self.rot == "disc":
            self.det = A.SpinningDisc(bm, self.z_rot, seed=self.seed)
        elif self.rot == "dove":
            self.det = A.DovePrism(bm, self.z_rot)
        self.helix_grid = A.helix_grid(bm, self.z_end) if self.l != 0 else None
        self.has_helix = self.helix_grid is not None
        self.revealed = 0
        # the table against the direct route at 24 seeded points and at 18 on the brightest ring at six depths (its
        # error is the slices' tolerance, and a slice compares at its brightest point: the seeded points alone, mostly
        # in dim light, gave a tolerance 2.3 times below the error there for the l = 0 world)
        rng = np.random.default_rng(11)
        zr6 = np.linspace(bm.z0, self.z_end, 6)
        # the brightest ring (the axis for l = 0, then a point 1.4 radial steps off it, where a spline is least sure)
        rr = np.array([max(A.ring_radius(bm, zz), 1.4 * float(bm.r[1])) for zz in zr6])
        ang = np.array([0.3, 2.4, 4.5])
        ring = np.stack([np.outer(rr, np.cos(ang)).ravel(), np.outer(rr, np.sin(ang)).ravel(), np.repeat(zr6, 3)])
        self.table_pts = np.concatenate([np.stack([rng.uniform(-0.8, 0.8, 24) * bm.half,
                                                   rng.uniform(-0.8, 0.8, 24) * bm.half,
                                                   rng.uniform(bm.z0, self.z_end, 24)]), ring], axis=1)
        self.table_err = bm.table.max_error(bm.direct, *self.table_pts)

    def _fork_waist(self, w0, period):
        """The smallest waist >= w0 (0.1 µm steps, up to the form's maximum) with which the fork's orders separate with
        a 20 % margin and the region fits the grid (the conditions of apparatus.Fork), and the region's length; None
        when there is none. The orders separate when the first order's angle beats the beam's spread: tan θ1 >
        4.5 w0 / z_R = 9 / (k w0) (an order's 4.5-waist disc leaves the zeroth)."""
        s = self.lam / period
        if s >= 1:
            return None
        tan = s / math.sqrt(1 - s * s)
        w = max(w0, math.ceil(1.2 * 9.0 / (self.k * tan) * 10.0 - 1e-9) / 10.0)
        w_max = SCHEMA.by_id["w0"].max
        while w <= w_max + 1e-9:
            zr = PX.rayleigh(self.k, w)
            q = tan * tan - (4.5 * w / zr) ** 2
            if q > 0:
                z_end = 1.25 * 4.5 * w / math.sqrt(q)
                x1 = abs(TM.order_position(1, period, self.k, z_end))
                half = max(x1 + 3.2 * float(PX.params(z_end, self.k, w)[0]), 3.5 * w)
                if 2 * half / A.FORK_N <= self.lam / 2:
                    return w, z_end
            w = round(w + 0.1, 10)
        return None

    def _init_fork(self):
        p = self.params
        w_ask, period = float(p["w0"]), float(p["period"])
        if self.lam / period >= 1:
            raise Refusal(f"период голограммы Λ = {period:g} мкм не больше длины волны λ = {self.lam:g} мкм: первый "
                          "порядок не распространяется (sin θ₁ = λ/Λ ≥ 1)",
                          f"выберите период Λ больше {self.lam:g} мкм (или λ меньше {period:g} мкм)")
        # review UX-params P11: the default waist (1.5 µm, the LG modes') is too narrow for any Λ of the form, so
        # «Голограмма-вилка» alone was refused, with advice that could not be followed; the world now takes the
        # smallest waist that works (the preset «fork»: 4 µm at Λ = 2.5) and says so
        fit = self._fork_waist(w_ask, period)
        if fit is None:
            ok = [pp for pp in np.arange(round(period, 2) - 0.01, self.lam, -0.01) if self._fork_waist(w_ask, pp)]
            s = self.lam / period
            ang = math.degrees(math.asin(min(s, 1.0)))
            raise Refusal(f"с периодом Λ = {period:g} мкм при λ = {self.lam:g} мкм порядки голограммы не разойдутся ни при "
                          f"какой перетяжке до {SCHEMA.by_id['w0'].max:g} мкм (угол первого порядка {ang:.3g}° слишком "
                          "мал для расходимости пучка или область не помещается в сетку)",
                          f"уменьшите период Λ до {ok[0]:.3g} мкм или меньше" if ok else
                          "возьмите другую длину волны")
        w0, z_end = fit
        fork = A.Fork(self.l, w0, self.lam, period, p["kind"], z_end)
        if w0 != w_ask:
            p["w0"] = w0
            tan = math.tan(math.asin(self.lam / period))
            self._msg({"type": "notice", "t": 0.0, "text": (
                f"Голограмма-«вилка»: при перетяжке {w_ask:g} мкм пучок расходится быстрее, чем расходятся порядки "
                f"(угол первого порядка {math.degrees(math.atan(tan)):.3g}° при Λ = {period:g} мкм, расходимость "
                f"λ/(πw0) = {math.degrees(self.lam / (math.pi * w_ask)):.3g}°) — порядки не разошлись бы. Мир взял "
                f"w0 = {w0:g} мкм, наименьшую, при которой они расходятся с запасом 20 %: пучок шире, область длиннее "
                f"(до z = {z_end:.3g} мкм). Меньший период Λ позволяет более узкий пучок.")})
        self.fork = fork
        z_end = fork.z1
        f = self.fork
        self.rot = "none"
        self.z_rot = None
        self.z_end = z_end
        self.box = ((-f.half, -f.half, 0.0), (f.half, f.half, z_end))
        self.zc = 0.5 * z_end
        self.plane_center = (0.0, 0.0, self.zc)
        self.helix_grid = None
        self.has_helix = False
        self.revealed = NB
        self.det = None

    # --- the scene ----------------------------------------------------------------------------------------------
    def _scene(self):
        lo, hi = self.box
        objects, layers = [], [{"id": "light", "label": "Интенсивность |E|² (объём, посчитан)", "kind": "volume",
                                "visible": True, "look": {"density": 0.9, "threshold": 0.03}}]
        W = hi[0] - lo[0]
        if self.fork is None and self.params["gen"] == "mode":
            objects.append({"id": "waist", "label": "Перетяжка пучка (z = 0): w0", "kind": "disk", "z": 0.0,
                            "w": float(self.params["w0"]), "size": [W, W], "visible": False})
        if self.det is not None:
            L = hi[2] - lo[2]
            objects.append({"id": "detector", "label": "Детектор (одномодовый, дальняя зона)" if self.rot == "disc"
                            else "Детектор: оба плеча интерферометра", "kind": "box",
                            "center": [0.0, 0.0, hi[2] - 0.03 * L], "size": [0.12 * W, 0.12 * W, 0.02 * L],
                            "color": "#9fe870", "opacity": 0.8, "text": "детектор", "visible": True})
        return {"box": [list(lo), list(hi)], "units": "мкм", "objects": objects, "layers": layers,
                "planes": {"max": MAX_PLANES, "center": list(self.plane_center),
                           "defaults": {str(i): list(v) for i, v in DEFAULT_NORMALS.items()}}}

    def _send_scene_data(self):
        lo, hi = self.box
        if self.fork is not None:
            V = self.fork.volume()
        else:
            V = A.volume(self.beam, self.z_end)
        self._msg({"type": "volume", "t": self.t, "id": "light", "dims": list(V.shape),
                   "box": [list(lo), list(hi)],
                   "note": "|E|² / пик на сетке 56³ (за вращающимся элементом не считается); точные значения — в срезах"},
                  {"data": V})
        if self.fork is not None:
            f = self.fork
            n = 96
            xs = np.linspace(-f.half, f.half, n)
            X, Y = np.meshgrid(xs, xs, indexing="ij")
            t = TM.fork_hologram(X, Y, f.l, f.period, f.kind)  # the declared pattern, for drawing
            if f.kind == "blazed":
                ph = np.angle(t)
                v = (ph + math.pi) / (2 * math.pi)
                rgb = np.stack([60 + 190 * v, 60 + 120 * v, 200 - 120 * v], axis=-1)
            else:
                v = np.real(t)
                rgb = np.stack([40 + 200 * v] * 3, axis=-1)
            pos = np.stack([X, Y, np.zeros_like(X)], axis=-1).reshape(-1, 3)
            idx = []
            for i in range(n - 1):
                for j in range(n - 1):
                    a = i * n + j
                    idx += [a, a + n, a + n + 1, a, a + n + 1, a + 1]
            self._msg({"type": "mesh", "t": self.t, "id": "hologram", "label": "Голограмма-«вилка» (z = 0)",
                       "count": int(len(pos)), "base": "lab", "opacity": 0.95},
                      {"pos": pos.astype(np.float32), "idx": np.array(idx, np.uint32),
                       "rgb": np.clip(rgb, 0, 255).astype(np.uint8).reshape(-1, 3)})
            return
        bm = self.beam
        if self.params["gen"] == "spp" and self.l:
            h_max = abs(self.l) * self.lam / 0.5  # the plate's step for n = 1.5
            pos, idx, rgb = A.spp_mesh(self.l, self.lam, 0.9 * bm.half, exaggerate=0.04 * (bm.z1 - bm.z0) / h_max)
            self._msg({"type": "mesh", "t": self.t, "id": "plate", "base": "lab",
                       "label": "Спиральная фазовая пластинка (z = 0; толщина преувеличена)", "count": int(len(pos)),
                       "opacity": 0.75}, {"pos": pos, "idx": idx, "rgb": rgb})
        if self.rot == "disc":
            pos, idx, rgb = A.disc_mesh(min(self.det.r_max, 0.95 * bm.half), 0.01 * (bm.z1 - bm.z0),
                                        rgb_fn=A.surface_rgb(self.det.surface))
            self._msg({"type": "mesh", "t": self.t, "id": "rotor", "base": "rest", "label":
                       "Вращающийся шероховатый диск", "count": int(len(pos)), "opacity": 0.85},
                      {"pos": pos, "idx": idx, "rgb": rgb})
        elif self.rot == "dove":
            h = min(2 * self.det.X.max(), 1.8 * bm.half)
            pos, idx, rgb = A.prism_mesh(0.08 * (bm.z1 - bm.z0), h, 0.8 * h)
            self._msg({"type": "mesh", "t": self.t, "id": "rotor", "base": "rest", "label": "Вращающаяся призма Дове",
                       "count": int(len(pos)), "opacity": 0.6}, {"pos": pos, "idx": idx, "rgb": rgb})
        self._flow_lines()
        if self.has_helix:
            self._reveal(0)
            self.revealed = 1

    def _flow_lines(self):
        bm = self.beam
        starts, r_pk = A.flow_starts(bm)
        zs = starts[0, 2]
        steps = FLOW_STEPS
        self.flow_err = None
        if bm.model == "exact":  # the paraxial vector field has no E_z: its Poynting vector is along z (not shown)
            jP = A.poynting_current(bm)
            self.flowP = B.trace_lines(jP, starts, self.z_end, steps)
            # the integration error, by step doubling on two lines (review B8-beams, O16): RK4 with twice the steps
            two = starts[[0, len(starts) // 2 + 1]]
            fine = B.trace_lines(jP, two, self.z_end, 2 * steps)[:, ::2]
            coarse = self.flowP[[0, len(starts) // 2 + 1]]
            self.flow_err = float(np.max(np.hypot(*(fine[:, :, :2] - coarse[:, :, :2]).transpose(2, 0, 1)))) / bm.w0
            pts, rgb = A.lines_message(self.flowP, (1.0, 0.82, 0.25))
            self._msg({"type": "lines", "t": self.t, "id": "flowP", "visible": True,
                       "label": "Линии потока энергии (вектор Пойнтинга, посчитаны)"}, {"pts": pts, "rgb": rgb})
        if bm.model == "exact":
            jo = A.orbital_current(bm, bm.lam / 60)
        elif self.params["gen"] == "mode":  # the paraxial mode's current (Im(u* grad_T u)/k, |u|^2), closed form
            p_, l_ = bm.p, self.l
            jo = lambda x, y, z: PX.current(p_, l_, x, y, z, bm.k, bm.w0)  # noqa: E731
        else:  # the paraxial current of the Fresnel field (the engine's differences of the table's field)
            jo = lambda x, y, z: PX.field_current(lambda a, b, c: bm.psi(a, b, c), x, y, z, bm.k, bm.lam / 60)  # noqa: E731
        self.flowO = B.trace_lines(jo, starts, self.z_end, steps)
        pts, rgb = A.lines_message(self.flowO, (0.35, 0.9, 1.0))
        self._msg({"type": "lines", "t": self.t, "id": "flowO",
                   "label": "Линии орбитального (канонического) тока p_o", "visible": bm.model != "exact"},
                  {"pts": pts, "rgb": rgb})
        self.flow_meta = (starts, zs, r_pk)

    def _reveal(self, k):
        omega_t = 2 * math.pi * k / NB
        pos, idx, rgb = A.helix_mesh(self.beam, self.helix_grid, omega_t)
        a, b = A.helix_region(self.beam, self.z_end)
        self._msg({"type": "helix", "t": self.t, "bin": k, "nb": NB, "t_bin": k * self.T_show / NB,
                   "count": int(len(pos)), "region": [a, b],
                   "label": f"Поверхности равной фазы arg ψ = ωt (участок z = {a:.3g}…{b:.3g} мкм)"},
                  {"pos": pos, "idx": idx, "rgb": rgb})

    # --- checks -----------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group="Пучок"):
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

    def _checks_beam(self):
        bm = self.beam
        # 1. the table against the direct route (measured when the world was built)
        self._check("table", "Таблица поля против прямого расчёта (24 точки + 18 на ярком кольце)", self.table_err,
                    0.0, "",
                    tol=1e-4, ok=self.table_err <= 1e-4,
                    note=("бикубические сплайны огибающих по таблице r × z против " +
                          ("прямой квадратуры векторного пучка" if bm.model == "exact" else
                           "замкнутой формы / интеграла Френеля") + "; доля пика |E|"))
        if bm.model == "exact":
            # what the propagating beam keeps of the named source (review B8-beams, O2)
            self._check("kept", "Доля мощности источника, которую несёт пучок (распространяющиеся волны, q ≤ k)",
                        bm.kept, 1.0, "", info=True,
                        note=(f"из спектра источника (Парсеваль для преобразования Ганкеля); не распространяется "
                              f"{bm.dropped:.2e} мощности перетяжки LG: поле на z = 0 отличается от названного на "
                              f"{math.sqrt(bm.dropped):.2g} в норме L2"
                              + ("; мир помечен" if bm.dropped >= A.DROP_LABEL else "")
                              + f"; больше {100 * A.DROP_REFUSE:.3g} % — мир не строится") if bm.gen == "mode" else
                             (f"из спектра поля за пластинкой (Парсеваль): {bm.dropped:.2e} его мощности на z = 0 — "
                              f"затухающие волны ближнего поля особой точки; на расстоянии λ от пластинки их "
                              f"{bm.ev_near[1]:.2e}, 2λ — {bm.ev_near[2]:.2e}; пучок — точное дальнее поле"))
        # 2. the angular momentum per photon, measured on the plane z_am: the waist (LG), or 2 lambda behind the plate,
        # before the light the plate's singular centre sends to wide angles has left the window
        z_am = self.zc if self.params["gen"] == "mode" else bm.z0 + 2 * bm.lam
        self.z_am = z_am
        n = int(min(192, max(96, 2 * math.ceil(bm.am_half / (bm.lam / 6)))))
        x = np.linspace(-bm.am_half, bm.am_half, n, endpoint=False)
        X, Y = np.meshgrid(x, x, indexing="ij")
        Z = np.full_like(X, z_am)
        sb = self.sigma_bar
        am = {"l": self.l, "sigma": sb, "z": z_am}
        dx = float(x[1] - x[0])
        per = "на фотон на единицу длины"
        if bm.model == "exact":
            E, H = bm.fields(X, Y, Z)
            hz = bm.lam / 40
            Ep, Hp = bm.fields(X, Y, Z + hz)
            Em, Hm = bm.fields(X, Y, Z - hz)
            gE = np.stack([np.stack(B.spectral_gradient(E[i], dx, dx) + ((Ep[i] - Em[i]) / (2 * hz),))
                           for i in range(3)])
            gH = np.stack([np.stack(B.spectral_gradient(H[i], dx, dx) + ((Hp[i] - Hm[i]) / (2 * hz),))
                           for i in range(3)])
            m = B.angular_momentum(x, x, E, H, gE, gH, bm.k)
            Ezf = float(np.max(np.abs(E[2])) / np.max(np.sqrt(np.sum(np.abs(E) ** 2, axis=0))))
            ref = bm.vb.moments()
            W_spec = ref["W"]
            miss = max(0.0, 1.0 - m["W"] / W_spec)
            tol = max(2e-4, 4 * (abs(self.l) + 2) * miss)
            wide = miss > 1e-3  # the window misses too much: the comparison is shown for information
            why = (f"; ОКНО НЕ ВМЕЩАЕТ свет под большими углами (доля энергии вне окна {miss:.1e}): сравнение для "
                   f"сведения" if wide else "")
            am.update({"L": m["L"], "S": m["S"], "J": m["J"], "flux_J": m["flux_J"], "J_poynting": m["J_poynting_per_photon"],
                       "S_flux": m["flux_S"], "L_flux": m["flux_L"], "S_flux_ref": ref["S_flux"],
                       "L_flux_ref": ref["L_flux"], "J_poynting_ref": ref["J_poynting"],
                       "L_ref": ref["L"], "S_ref": ref["S"], "J_ref": ref["J"], "cos": ref["cos_mean"], "miss": miss})
            win = (f"плотности Берри на сетке {n}² в окне ±{bm.am_half:.3g} мкм; допуск — 4(|l| + 2) × доля энергии "
                   f"вне окна ({miss:.1e})")
            for key, lab in (("J", f"Полный момент J_z = L_z + S_z {per}"),
                             ("S", f"Спин S_z {per} (каноническое разделение, Блиох и др. 2010)"),
                             ("L", f"Орбитальный момент L_z {per} (каноническое разделение)")):
                self._check(f"am_{key}", lab + f" (измерен по полю на плоскости z = {z_am:.3g} мкм)", m[key], ref[key],
                            "ħ", tol=tol, ok=None if wide else abs(m[key] - ref[key]) <= tol, info=wide,
                            group="Момент импульса",
                            note=f"эталон из спектра: J = l + σ, S = σ⟨cos θ⟩, L = l + σ(1 − ⟨cos θ⟩), "
                                 f"⟨cos θ⟩ = {ref['cos_mean']:.6f}; {win}; разделение на спин и орбиту зависит от "
                                 f"определения — по потоку (Барнетт) ниже" + why)
            self._check("am_flux", "Поток момента / поток энергии × ω (тензор натяжений)", m["flux_J"], ref["J"],
                        "ħ", tol=tol, ok=None if wide else abs(m["flux_J"] - ref["J"]) <= tol, info=wide,
                        group="Момент импульса",
                        note="момент, переносимый через плоскость, на фотон, прошедший через неё: l + σ точно" + why)
            flux_notes = {
                "S_flux": "другое опубликованное определение: спиновый поток σ/(2ω)∫|E_⊥|² dA (Монтейру и др. 2009, "
                          "ур. 33), измерен как −∫Im(E_⊥*·H_⊥) dA/(2ω); эталон σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩ (|спин| > 1, "
                          "сдвиг от σ в другую сторону, чем у канонического S_z); от определения не зависит только "
                          "J_z = l + σ",
                "L_flux": "поток момента (тензор натяжений) минус спиновый поток Барнетта, на фотон через плоскость; "
                          "эталон l + σ − σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩"}
            for key, mkey, lab in (("S_flux", "flux_S", "Спин по потоку через плоскость на фотон (разделение Барнетта)"),
                                   ("L_flux", "flux_L", "Орбита по потоку через плоскость на фотон (разделение Барнетта)")):
                self._check(f"am_{key}", lab, m[mkey], ref[key], "ħ", tol=tol,
                            ok=None if wide else abs(m[mkey] - ref[key]) <= tol, info=wide, group="Момент импульса",
                            note=flux_notes[key] + "; " + win + why)
            # the Poynting moment weights the r^-3/2 tails of a spectrum cut at q = k more than the densities above: in
            # a window of half-width R its error falls only as R^-1/2 (measured for the tight preset: 5.6e-3, 4.6e-3,
            # 4.0e-3, 3.2e-3 at R = 10, 15, 20, 30 lambda), so for such a spectrum it is a comparison, not a check
            pinfo = wide or bm.edge >= 1e-6
            self._check("am_poynting", f"Момент по Пойнтингу ∫(r × P)_z {per}", m["J_poynting_per_photon"],
                        ref["J_poynting"], "ħ", tol=tol,
                        ok=None if pinfo else abs(m["J_poynting_per_photon"] - ref["J_poynting"]) <= tol, info=pinfo,
                        group="Момент импульса",
                        note=f"эталон l + σ + (σ/2)⟨sin²θ/cos θ⟩ = {ref['J_poynting']:.7f}: отличается от L_z + S_z на "
                             f"½ d/dz ∫ r·S_⊥ dA; при одной спиральности S = σP/ω, и этот член одинаков на всех "
                             f"плоскостях z — свойство углового спектра, есть и в перетяжке"
                             + (why if wide else "")
                             + (f"; спектр обрезан на q = k (на краю {bm.edge:.2g} максимума): хвосты поля ∝ r^−3/2, "
                                f"в окне этот момент сходится лишь как R^−1/2 — сравнение для сведения"
                                if bm.edge >= 1e-6 and not wide else ""))
            # the power through planes (exact field): the energy flux is the same at every z
            fl, misses = [], []
            for zz in (z_am, 0.5 * (z_am + self.z_end), self.z_end):
                Ez, Hz = bm.fields(X, Y, np.full_like(X, zz))
                fl.append(float(np.sum(B.poynting(Ez, Hz)[2])) * dx * dx)
                misses.append(max(0.0, 1.0 - float(np.sum(B.energy_density(Ez, Hz))) * dx * dx / W_spec))
            dev = (max(fl) - min(fl)) / max(fl)
            ptol = max(1e-6, 3 * max(misses))
            pwide = max(misses) > 1e-3
            self._check("power", "Мощность через плоскости z: одна и та же", dev, 0.0, "", tol=ptol,
                        ok=None if pwide else dev <= ptol, info=pwide,
                        note=f"P_z, проинтегрированный по окну на трёх глубинах: {', '.join(f'{v:.6g}' for v in fl)}; "
                             f"допуск — 3 × наибольшая доля энергии вне окна ({max(misses):.1e})"
                             + ("; свет под большими углами уходит из окна: для сведения" if pwide else ""))
            self._check("ez", "Продольное поле max|E_z| / max|E| (плоскость z_c)", Ezf, None, "", info=True,
                        note=f"в параксиальной картине его нет; первого порядка, ~1/(k w0) = {1 / (bm.k * bm.w0):.3g}")
            am["ez"] = Ezf
            # where the paraxial picture fails: the paraxial mode against the exact field at points of z_c — the
            # transverse components (second order); E_z, first order, is the check above (review B8-beams, O1)
            if self.params["gen"] == "mode":
                r = np.linspace(0, 0.8 * bm.half, 60)
                Ex = bm.direct(r, 0 * r, np.full_like(r, self.zc))
                Pa = PX.lg(int(self.params["p"]), self.l, r, 0 * r, self.zc, bm.k, bm.w0) * np.exp(1j * bm.k * self.zc)
                Pa = Pa[None] * A.pol_vector(self.params["pol"])[:, None]
                d = float(np.max(np.abs(Ex[:2] - Pa[:2])) / np.max(np.abs(Pa)))
                am["parax_diff"] = d
                self._check("parax", "Параксиальная мода против точного поля: поперечные компоненты (плоскость z_c)",
                            d, None, "", info=True,
                            note=f"наибольшее отличие E_x, E_y, доля пика; второй порядок — растёт как (λ/w0)² = "
                                 f"{(bm.lam / bm.w0) ** 2:.3g} (измерено: ×4 при w0/2); продольное поле E_z, которого "
                                 f"у моды нет, первого порядка (λ/w0) — проверка «Продольное поле»")
        else:
            psi = bm.psi(X, Y, Z)
            Lm = B.scalar_oam_per_photon(psi, x, x)
            # the spin from the model's own field (review B8-beams, O9): u e_pol with H = -i sigma E per helicity
            E, H = bm.fields(X, Y, Z)
            Sm = bm.k * float(np.sum(B.spin_density(E, H, bm.k)[2])) / float(np.sum(B.energy_density(E, H)))
            am.update({"L": Lm, "S": Sm, "J": Lm + Sm, "L_ref": self.l, "S_ref": sb, "J_ref": self.l + sb})
            self._check("am_L", f"Орбитальный момент L_z {per} (измерен по полю на плоскости z = {z_am:.3g} мкм)", Lm,
                        self.l, "ħ", tol=2e-4, ok=abs(Lm - self.l) <= 2e-4, group="Момент импульса",
                        note="∫Im(ψ*∂_φψ) dA / ∫|ψ|² dA, производные спектральные; в параксиальной модели L_z = l")
            self._check("am_S", f"Спин S_z {per} (по полю модели на той же плоскости)", Sm, sb, "ħ", tol=1e-9,
                        ok=abs(Sm - sb) <= 1e-9, group="Момент импульса",
                        note="ω∫S_z dA / ∫w dA для u·e_σ (плотности Берри): σ̄ при однородной поляризации — так модель "
                             "устроена; точная модель покажет расщепление; допуск — округление")
        self.am = am
        self._msg({"type": "am", "t": self.t, **{k: (float(v) if v is not None else None) for k, v in am.items()}})
        # 3. the topological charge on the plane z_c
        r_ring = A.ring_radius(bm, self.zc)
        q = B.charge_on_circle(lambda xx, yy: bm.psi(xx, yy, np.full_like(xx, self.zc)), 0.0, 0.0,
                               max(r_ring, 0.05 * bm.w0), 720)
        self._check("charge", "Топологический заряд: обход фазы ψ вокруг оси (z_c)", q, float(self.l), "",
                    tol=1e-6, ok=abs(q - self.l) < 1e-6,
                    note=f"сумма скачков фазы по окружности r = {r_ring:.3g} мкм (самое яркое кольцо), 720 точек; эталон — l")
        # 4. the Gouy phase on the ring (or the axis) at z = min(z_R, end)
        zg = min(bm.zr, 0.98 * self.z_end) if self.params["gen"] == "mode" else None
        if zg is not None and zg > 0:
            rho = 0.0 if self.l == 0 else 1 / math.sqrt(2)
            wg = bm.width(zg)
            ph = np.linspace(0, 2 * math.pi, 64, endpoint=False)
            vals = bm.psi(rho * wg * np.cos(ph), rho * wg * np.sin(ph), np.full_like(ph, zg)) * np.exp(-1j * self.l * ph)
            meas = float(np.angle(np.mean(vals) * np.exp(-1j * bm.k * zg)))
            pp = int(self.params["p"])
            Lp = float(eval_genlaguerre(pp, abs(self.l), 2 * rho * rho))
            ref = rho * rho * zg / bm.zr - float(PX.gouy(2 * pp + abs(self.l), zg, bm.k, bm.w0)) + (math.pi if Lp < 0 else 0)
            ref = float(np.angle(np.exp(1j * ref)))  # in (-pi, pi], as the measured phase
            d = float(np.angle(np.exp(1j * (meas - ref))))
            exact = bm.model == "exact"
            self._check("gouy", f"Фаза Гюи: arg ψ на {'оси' if rho == 0 else 'кольце r = w/√2'} при z = {zg:.3g} мкм",
                        meas, ref, "рад", tol=1e-3, ok=None if exact else abs(d) < 1e-3, info=exact,
                        note=f"эталон ρ²z/z_R − (2p+|l|+1)·arctan(z/z_R) (параксиальная формула); отличие {d:.2e} рад"
                             + ("; у точного поля — непараксиальная поправка" if exact else ""))
        # 5. the equiphase sheets: |l| of them
        if self.helix_grid is not None:
            nsheets = A.sheet_count(self.helix_grid)
            self._check("sheets", "Число винтовых поверхностей равной фазы", nsheets, float(abs(self.l)), "",
                        tol=0.02, note="среднее число пересечений arg ψ = const по азимуту в ярких ячейках (z, r)")
        # 6. the flow lines' twist: the paraxial orbital current against the closed-form spiral
        starts, zs, r_pk = self.flow_meta
        if self.params["gen"] == "mode":
            worst = 0.0
            for i in range(len(starts)):
                r0, a0 = math.hypot(*starts[i, :2]), math.atan2(starts[i, 1], starts[i, 0])
                xr, yr = PX.flow_line(self.l, r0, a0, zs, self.flowO[i, :, 2], bm.k, bm.w0)
                worst = max(worst, float(np.max(np.hypot(self.flowO[i, :, 0] - xr, self.flowO[i, :, 1] - yr))))
            par = bm.model != "exact"
            self._check("flow", "Линии орбитального тока против параксиальной спирали φ(z)", worst / bm.w0, 0.0, "",
                        tol=2e-3, ok=(worst / bm.w0 <= 2e-3) if par else None, info=not par,
                        note="наибольшее отклонение, доля w0; спираль: ρ = r/w(z) постоянно, φ − φ0 = l/(2ρ²)·(ψ − ψ0)"
                             + ("" if par else " — у точного поля отличие показывает непараксиальность"))
        if self.flow_err is not None:
            self._check("flow_step", "Линии потока энергии (Пойнтинг): ошибка интегрирования", self.flow_err, None, "",
                        info=True,
                        note=f"RK4, {FLOW_STEPS} шагов по z; две линии пересчитаны с вдвое меньшим шагом — наибольшее "
                             f"расхождение, доля w0 (оценка ошибки линий на сцене)")

    def _checks_fork(self):
        f = self.fork
        orders, _ = f.orders(f.z1)
        for m, xm, q in orders:
            if TM.fork_order_coefficient(f.kind, m) == 0:
                continue
            self._check(f"order_{m}", f"Порядок m = {m:+d} (x = {xm:.3g} мкм): топологический заряд", float(q),
                        float(m * f.l), "", tol=0.0, ok=q == m * f.l,
                        note="сумма зарядов ячеек сетки в круге радиуса 1,3 w(z) вокруг порядка (обход по его границе); эталон m·l")
        sh = f.shares()
        self.fork_shares = sh
        for m in sh["orders"]:
            if m not in (-1, 0, 1):
                continue
            v, r = sh["meas"][m], sh["ref"][m]
            self._check(f"frac_{m}", f"Порядок m = {m:+d}: доля распространяющейся мощности", v, r, "",
                        tol=sh["tol"], ok=abs(v - r) <= sh["tol"],
                        note=f"измерена по угловому спектру поля за маской (ячейка |k_x + mK| < K/2; по Парсевалю та же "
                             f"на любой плоскости z); эталон — замкнутая форма той же тонкой маски на той же сетке k "
                             f"(каждый порядок — гауссов пучок за пластинкой заряда m·l, сдвинутый на −mK; их хвосты "
                             f"∝ q^−2 перекрываются); без перекрытия было бы |c_m|²/Σ|c_j|² = {sh['ideal'][m]:.4f}; "
                             f"допуск — 2 × наложение спектра сеткой, оценённое по замкнутой форме с периодическими "
                             f"образами ({sh['alias']:.1e})"
                             + (f"; бинарная маска — ряд Фурье до полосы сетки, |m| ≤ {f.m_band}" if f.kind == "binary"
                                else ""))

    # --- slice planes (lfviz.planes3d hooks) -------------------------------------------------------------------------
    def _plane_points(self, pl, s_rng, t_rng, ns, nt):
        s = np.linspace(s_rng[0], s_rng[1], ns)
        t = np.linspace(t_rng[0], t_rng[1], nt)
        S, T = np.meshgrid(s, t)  # (nt, ns)
        o, u, v = (np.asarray(a, float) for a in (pl.origin, pl.u, pl.v))
        P = o[:, None, None] + u[:, None, None] * S + v[:, None, None] * T
        lo, hi = (np.asarray(b, float) for b in self.box)
        inside = np.all((P >= lo[:, None, None] - 1e-9) & (P <= hi[:, None, None] + 1e-9), axis=0)
        return s, t, P, inside

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        ns, nt = (48, 48) if coarse else (NS, NT)
        if self.fork is not None:
            return self._fork_slice(pl, s_rng, t_rng, coarse)
        s, t, P, inside = self._plane_points(pl, s_rng, t_rng, ns, nt)
        z = np.where(inside, P[2], self.beam.z0)
        E = self.beam.fields(P[0], P[1], z)[0]
        I = np.sum(np.abs(E) ** 2, axis=0)
        psi = self.beam.psi(None, None, None, E) * np.exp(-1j * self.beam.k * z)
        I[~inside] = np.nan
        ver = {"points": 0, "note": "грубый срез (автосмещение), без сверки"} if coarse else self._verify(P, I, inside)
        return {"s": s, "t": t, "I": I, "phase": np.angle(psi), "coarse": coarse, "verify": ver, "plane": pl,
                "route": "таблица точного поля" if self.beam.model == "exact" else "ПРИБЛИЖЕНИЕ: параксиальная модель",
                "exact": self.beam.model == "exact"}

    def _verify(self, P, I, inside):
        """|E|^2 at three points of the plane (the brightest and two seeded others with >= 5 % of it) against the
        direct route."""
        flat = np.where(inside, np.nan_to_num(I, nan=-1.0), -1.0).ravel()
        top = int(np.argmax(flat))
        peak = flat[top]
        cand = np.nonzero(flat >= 0.05 * peak)[0]
        rng = np.random.default_rng(7)
        picks = [top] + [int(c) for c in rng.choice(cand, size=min(2, len(cand)), replace=False)]
        pts = P.reshape(3, -1)[:, picks]
        Ed = self.beam.direct(*pts)
        Id = np.sum(np.abs(Ed) ** 2, axis=0)
        err = float(np.max(np.abs(Id - flat[picks])) / max(peak, 1e-300))
        tol = 4 * self.table_err + 1e-9
        return {"points": len(picks), "max_err": err, "tol": tol, "ok": err <= tol}

    def _fork_slice(self, pl, s_rng, t_rng, coarse):
        f = self.fork
        n = np.asarray(pl.normal)
        o = np.asarray(pl.origin)
        u = np.asarray(pl.u)
        if abs(abs(n[2]) - 1) < 1e-9:  # a transverse plane: the field on the grid at its z
            U = f.plane(float(o[2]))
            ss = (f.x - o[0]) * u[0]
            tt = (f.x - o[1]) * np.asarray(pl.v)[1]
            si, ti = np.argsort(ss), np.argsort(tt)
            vals = U[np.ix_(si, ti)].T  # (t, s)
            s, t = ss[si], tt[ti]
        elif abs(abs(n[1]) - 1) < 1e-9 and u[0] > 0:  # y = c: the exact plane route (u = +x)
            t = np.linspace(t_rng[0], t_rng[1], NT if not coarse else 48)
            s, vals = AS.propagate_plane(f.U0, f.dx, f.k, pl, s_rng, t, pad=f.pad, check=True)
        elif abs(abs(n[0]) - 1) < 1e-9:  # x = c: the exact longitudinal slice across y
            t = np.linspace(t_rng[0], t_rng[1], NT if not coarse else 48)
            zz = o[2] + t * np.asarray(pl.v)[2]
            line = AS.propagate_slice(f.U0, f.dx, f.k, np.maximum(zz, 0.0), 0, float(o[0]), pad=f.pad, check=True)
            ss = (f.x - o[1]) * u[1]
            si = np.argsort(ss)
            s, vals = ss[si], line[:, si]
        else:
            raise ValueError("у голограммы срезы считаются только вдоль осей: z = c, y = c или x = c")
        I = np.abs(vals) ** 2
        z_of = o[2] + np.outer(t, np.ones(len(s))) * np.asarray(pl.v)[2]
        return {"s": np.asarray(s), "t": np.asarray(t), "I": I, "phase": np.angle(vals * np.exp(-1j * f.k * z_of)),
                "coarse": coarse, "verify": {"points": 0, "note": "точный путь углового спектра (тот же, что объём)"},
                "plane": pl, "route": "угловой спектр (точно для этой плоскости)", "exact": True}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        pd = self.planes[pid]
        I = sl["I"]
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(I.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": "plane", "route_label": sl["route"] + "; фаза — arg(ψ e^{−ikz}) (огибающая)",
                "exact": sl["exact"], "approximation": not sl["exact"],
                "reason": "" if sl["exact"] else "параксиальная модель пучка (мир выбран так)",
                "verify": sl["verify"], "verify_title": "|E|² в точках плоскости против прямого расчёта",
                "z_near": 0.0, "window_est": 0.0}
        blobs = {"I": (I / max(peak, 1e-300)).astype(np.float32)}
        if not sl["coarse"]:
            blobs["phase"] = sl["phase"].astype(np.float32)
        self._msg(meta, blobs)
        ver = sl["verify"]
        if ver.get("points"):
            self._check(f"plane_{pid}", f"Срез {pid} ({pd['label']}): |E|² в {ver['points']} точках против прямого "
                                        f"расчёта", ver["max_err"], 0.0, "", tol=ver["tol"], ok=ver["ok"],
                        group="Срезы", note="доля пика среза; допуск — 4 × ошибка таблицы")

    def _plane_preview(self, pid, pl, s_rng, t_rng):
        sl = self._plane_slice(pid, pl, s_rng, t_rng, True)
        I = sl["I"]
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        self._msg({"type": "slice", "t": self.t, "id": pid, "preview": True, "shape": list(I.shape),
                   "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                   "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                   "origin": [float(c) for c in pl.origin], "u": list(pl.u), "v": list(pl.v),
                   "normal": [float(c) for c in pl.normal], "label": G._label(pl), "peak": peak,
                   "z_near": 0.0, "window_est": 0.0}, {"I": (I / max(peak, 1e-300)).astype(np.float32)})

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):
            self._check(f"plane_{pid}", f"Срез {pid}: убран", None, None, "", info=True, group="Срезы",
                        note="последняя сверка этого среза — в записи запуска")

    # --- the rotating element and its detector ------------------------------------------------------------------------
    def _omega(self):
        return 2 * math.pi * self.f_rot

    def _angle_at(self, t):
        return self.angle + self._omega() * (t - self.t_angle)

    def _dt_sample(self):
        return 1.0 / (A.SAMPLES_PER_TURN * max(self.f_rot, 1.0))

    def _next_sample_time(self):
        return self.seg_t0 + self.seg_n * self._dt_sample()

    def _beat_ref(self):
        """The closed form of the detector's beat (Hz): Lavery's 2|l| f for the disc behind the +-l filter
        (``beams_rotation.superposition_beat``); for the Dove prism turning at f the beam turns at 2f and the shift is
        l_out 2 f, l_out = -l (``rotated_beam_frequency`` against the arm at rest): the beat 2|l| f."""
        if self.rot == "disc":
            return ROT.superposition_beat(self.l, self.f_rot)
        return abs(ROT.rotated_beam_frequency(0.0, -self.l, 2 * self.f_rot))

    def _shift_ref(self):
        """The closed form of the frequency shift (Hz) of the complex amplitude: -l f (disc, on the axis:
        ``scattered_on_axis_shift``); -2 l f (the turned arm of the Dove prism against the arm at rest:
        ``rotated_beam_frequency`` with omega = 0)."""
        if self.rot == "disc":
            return ROT.scattered_on_axis_shift(self.l, self.f_rot)
        return ROT.rotated_beam_frequency(0.0, -self.l, 2 * self.f_rot)

    def _sample_until(self, t_target):
        new = []
        while self.det is not None and self._next_sample_time() <= t_target * (1 + 1e-12) + 1e-15:
            ts = self._next_sample_time()
            ang = self._angle_at(ts)
            v, c = self.det.sample(ang)
            self.samples.append((ts, v, c))
            new.append((ts, v, c))
            self.seg_n += 1
            if len(self.samples) % A.WINDOW == 0:
                self._measure()
        if new:
            arr = np.array([(a, b, c.real, c.imag) for a, b, c in new], float)
            self._msg({"type": "trace", "t": self.t, "from": self.all_n, "count": len(new), "seg": self.seg,
                       "f_rot": self.f_rot},
                      {"ts": arr[:, 0], "v": arr[:, 1], "re": arr[:, 2], "im": arr[:, 3]})
            self.all_n += len(new)

    def _measure(self):
        w = self.samples[-A.WINDOW:]
        dt = self._dt_sample()
        v = np.array([a[1] for a in w])
        c = np.array([a[2] for a in w])
        depth = ROT.modulation_depth(v)
        ref = self._beat_ref()
        n_meas = len(self.samples) // A.WINDOW
        what = "диск: интенсивность за фильтром мод ±l" if self.rot == "disc" else "призма: мощность двух плеч"
        if ref == 0:
            self._check("beat", "Биения на детекторе: глубина модуляции (их нет)", depth, 0.0, "", tol=1e-6,
                        ok=depth <= 1e-6, group="Вращение",
                        note=f"{what}; {A.WINDOW} отсчётов; эталон: при l = 0 или f = 0 частота не сдвигается")
            f_meas = 0.0
        else:
            f_meas = ROT.peak_frequency(v, dt, positive=True, exclude_dc=True) / (2 * math.pi)
            self._check("beat", "Биения на детекторе: частота по спектру отсчётов", f_meas, ref, "Гц",
                        tol=1e-3, group="Вращение",
                        note=f"{what}; {A.WINDOW} отсчётов за два оборота, пик спектра; эталон 2|l|·f "
                             f"(глубина модуляции {depth:.3g})")
        s_meas = ROT.peak_frequency(c, dt) / (2 * math.pi)
        s_ref = self._shift_ref()
        self._check("shift", ("Сдвиг частоты света на оси (по комплексной амплитуде)" if self.rot == "disc" else
                              "Сдвиг частоты повёрнутого пучка (по их перекрытию)"), s_meas, s_ref, "Гц",
                    tol=1e-3 if s_ref else 1e-6 * max(self.f_rot, 1.0),
                    ok=(abs(s_meas) < 1e-6 * max(self.f_rot, 1.0)) if s_ref == 0 else None,
                    group="Вращение",
                    note=("−l·f: свет, рассеянный на ось, взял гармонику n = −l поверхности" if self.rot == "disc" else
                          "l_вых·2f, l_вых = −l: изображение повёрнуто на удвоенный угол призмы и отражено"))
        f, P = ROT.spectrum(v - v.mean(), dt, pad=8)
        keep = f >= 0
        fh = f[keep] / (2 * math.pi)
        Pk = P[keep]
        top = max(4 * (ref or self.f_rot or 1.0), 2.0)
        sel = fh <= top
        self._msg({"type": "beat", "t": self.t, "n": n_meas, "seg": self.seg, "f_meas": f_meas, "f_ref": ref,
                   "shift_meas": s_meas, "shift_ref": s_ref, "depth": depth, "f_rot": self.f_rot},
                  {"f": fh[sel].astype(np.float32), "P": (Pk[sel] / max(float(Pk.max()), 1e-300)).astype(np.float32)})
        self._msg({"type": "event", "t": self.t, "kind": "measure",
                   "text": f"измерение {n_meas}: биения {f_meas:.4g} Гц (эталон {ref:.4g}), сдвиг {s_meas:.4g} Гц"})

    # --- messages and time ----------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, []
        self._send_scene_data()
        if self.fork is not None:
            self._checks_fork()
        else:
            self._checks_beam()
        buf, self._buf = buf + self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def advance(self, t_target):
        dt = t_target - self.t
        if self.has_helix:
            while self.revealed < NB and self.revealed * self.T_show / NB <= t_target * (1 + 1e-12):
                self.t = self.revealed * self.T_show / NB
                self._reveal(self.revealed)
                self.revealed += 1
            if self.revealed == NB:
                self.helix_grid = None  # every phase sent: the grid is not kept (a checkpoint's size)
        self.t = t_target
        self._sample_until(t_target)
        self._advance_planes(t_target, dt)

    def next_event_time(self):
        times = []
        if self.has_helix and self.revealed < NB:
            times.append(self.revealed * self.T_show / NB)
        if self.det is not None:
            k = A.WINDOW - (len(self.samples) % A.WINDOW)
            times.append(self.seg_t0 + (self.seg_n + k - 1) * self._dt_sample())
        times = [t for t in times if t > self.t + 1e-12]
        return min(times) if times else None

    def max_step(self):
        return 0.25

    def frame(self):
        k = int(math.floor((self.t / self.T_show) * NB + 1e-9)) % NB if self.has_helix else 0
        f = {"bin": min(k, self.revealed - 1) if self.has_helix else 0, "nb": NB,
             "phase": (self.t / self.T_show) % 1.0, "revealed": self.revealed}
        if self.det is not None:
            ang = self._angle_at(self.t)
            f.update({"angle": ang, "rotA": A.rot_z(ang), "rotb": [0.0, 0.0, float(self.z_rot)], "f_rot": self.f_rot,
                      "n_samples": len(self.samples)})
        return f, {}

    # --- live: the rotation frequency -----------------------------------------------------------------------------
    def live_values(self):
        return {"f_rot": self.f_rot} if self.fork is None and self.rot != "none" else {}

    def set_live(self, values):
        if self.fork is not None or self.rot == "none":
            raise ValueError("в этом мире нет вращающегося элемента: нечего менять на ходу")
        merged, errors = SCHEMA.coerce_live({"f_rot": self.f_rot}, values)
        if errors:
            raise ValueError("; ".join(errors))
        f_new = float(merged["f_rot"])
        self.angle = self._angle_at(self.t)
        self.t_angle = self.t
        self.f_rot = f_new
        self.seg += 1
        self.seg_t0 = self.t
        self.seg_n = 0
        self.samples = []
        return f"частота вращения f = {f_new:.4g} Гц с t = {self.t * 1e3:.4g} мс: новая серия измерений"

    def view_state(self):
        return SlicePlanes.view_state(self)

    def engine_modules(self):
        if self.fork is not None:
            return ["core.optics.beams", "core.optics.angular_spectrum", "core.geometry",
                    "theories.approx.beams_paraxial", "theories.approx.beams_thin_masks"]
        # every beam world uses beams_paraxial's Gaussian parameters (the region, the helix grid, the widths) and the
        # paraxial references of its checks (review B8-beams, O12)
        mods = ["core.optics.beams", "core.optics.beams_rotation", "core.geometry", "theories.approx.beams_paraxial"]
        if self.params["gen"] == "spp" or self.rot == "disc":  # the plate, the rough disc: thin masks
            mods.append("theories.approx.beams_thin_masks")
        return mods

    def header(self):
        p = self.params
        approximations = []
        if self.fork is not None:
            approximations.append("голограмма — тонкая маска в плоскости z = 0 (дальше распространение точное)")
        else:
            bm0 = self.beam
            if bm0.model == "paraxial":
                approximations.append(
                    f"параксиальная модель пучка: мода × однородная поляризация (ошибка поперечного поля ~ (λ/w0)² = "
                    f"{(bm0.lam / bm0.w0) ** 2:.2g}, продольного поля нет — у точного оно ~ λ/(πw0) = "
                    f"{bm0.lam / (math.pi * bm0.w0):.2g})")
            elif bm0.dropped >= A.DROP_LABEL and p["gen"] == "mode":
                approximations.append(
                    f"спектр источника обрезан на q = k: {100 * bm0.dropped:.3g} % мощности перетяжки LG — затухающие "
                    f"волны, их у пучка нет; w0 — ширина спектра, а не измеренная перетяжка (поле на z = 0 отличается "
                    f"от названного на {100 * math.sqrt(bm0.dropped):.3g} % в норме L2)")
            elif bm0.dropped >= A.DROP_LABEL:
                approximations.append(
                    f"у пучка нет затухающих волн за пластинкой: на z = 0 это {100 * bm0.dropped:.3g} % мощности (ближнее "
                    f"поле особой точки в центре пластинки), на расстоянии λ — {100 * bm0.ev_near[1]:.3g} %, 2λ — "
                    f"{100 * bm0.ev_near[2]:.3g} %; дальше пучок — точное дальнее поле тонкой пластинки")
            if p["gen"] == "spp":
                approximations.append("спиральная пластинка — тонкая маска exp(ilφ) в плоскости z = 0")
            if self.rot == "disc":
                approximations.append("шероховатый диск — тонкий фазовый экран, скалярно (поляризация не участвует)")
            elif self.rot == "dove":
                approximations.append("призма Дове — идеальный поворот изображения, поляризация не меняется")
        bm = self.beam
        info = {}
        if bm is not None:
            info = {"model": bm.model, "gen": p["gen"], "l": self.l, "p": bm.p, "w0": bm.w0, "lam": bm.lam,
                    "kept": bm.kept, "cost_s": bm.cost["seconds"],
                    "zr": bm.zr, "theta_div": bm.lam / (math.pi * bm.w0), "pol": p["pol"], "sigma": self.sigma_bar,
                    "z_rot": self.z_rot, "rot": self.rot, "zc": self.zc,
                    "helix_region": list(A.helix_region(bm, self.z_end)) if self.l else None}
        else:
            f = self.fork
            info = {"model": "fork", "gen": "fork", "l": self.l, "w0": f.w0, "lam": f.lam, "period": f.period,
                    "kind": f.kind, "z_end": f.z1}
        sub = str.maketrans("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋")
        sup = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
        lg_name = "LG" + str(int(p["p"])).translate(sub) + str(self.l).translate(sup)
        title = {"mode": f"Оптический вихрь: {lg_name}", "spp": f"Спиральная пластинка, l = {self.l}",
                 "fork": f"Голограмма-«вилка», l = {self.l}"}[p["gen"]]
        cut = bm is not None and bm.model == "exact" and bm.dropped >= A.DROP_LABEL and p["gen"] == "mode"
        return {
            "title": title + ("" if bm is None else ((", точный векторный пучок" + (" (спектр обрезан на q = k)" if cut
                                                                                   else "")) if bm.model == "exact" else
                                                     ", параксиальная модель")),
            "text": ("Пучок с фазой e^{ilφ}: поверхности равной фазы — l переплетённых винтов, поток энергии "
                     "закручивается вокруг оси, каждый фотон несёт орбитальный момент. Всё на сцене посчитано движком: "
                     "поле пучка, винтовые фронты (их фазы открываются по ходу времени), объём интенсивности, линии "
                     "потока, срезы. Вращающийся элемент сдвигает частоту света на величину, пропорциональную l: "
                     "детектор копит отсчёты, по их спектру измеряются биения и сравниваются с формулой."),
            "actions": [],
            "approximations": approximations,
            "scene3d": self._scene(),
            "beam": info,
            "t_show": self.T_show, "nb": NB,
            "units": {"x": "мкм", "z": "мкм", "t": "с (время мира; оптическая фаза показана замедленно)"},
        }, {}


VIZ = {
    "id": "v16_optical_vortices",
    "title": "Оптические вихри: пучки Лагерра–Гаусса, орбитальный момент, вращательный Доплер",
    "summary": ("Винтовые фронты пучка с фазой e^{ilφ}, закрученный поток энергии, срезы с фазой на цветовом круге; "
                "орбитальный и спиновый момент на фотон, измеренные по полю (точное векторное решение или "
                "параксиальная модель); вращающийся диск или призма Дове сдвигают частоту — биения на детекторе "
                "измеряются по спектру отсчётов."),
    "purpose": ("Показать, что такое орбитальный момент света, где параксиальная картина перестаёт работать (острая "
                "фокусировка: продольное поле, обмен между спином и орбитой) и как вращение даёт сдвиг частоты lΩ."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
