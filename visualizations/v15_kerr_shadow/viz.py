# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v15: the shadow of a rotating black hole and its photon rings, and what if the hole is not Kerr (a wrapper over
lfphys; plan P14.3, on the plan's P7, P10, P11).

The run computes what a distant observer sees of a Kerr black hole lit by a thin equatorial disk: every pixel of the
observer's screen is a photon traced back in closed form (``lfphys.core.gravity.kerr_shadow``): captured by the hole
(the shadow) or come from infinity, and where it crossed the equatorial plane - the n-th crossing along the ray traced
back (GL-b's m-bar: n = 0 the first, for moderate inclinations the direct image; n = 1 the lensing ring; n = 2 the
photon ring; near edge-on the direct image of the disk's lower face is n = 1, review B5-K9) - with the redshift g of the
gas there. The brightness of a pixel is the sum over its crossings of g^4 J(r) (the source model, stated, not a law:
bolometric intensity of a thin disk of emissivity J moving with the gas, each crossing counted once, f_n = 1, without a
path-length weight; Gralla, Lupsasca & Marrone 2020 use f = 1.5 for n >= 1 and Chael et al. 2021 g^3 with 2/3 -
review B5-K15). When an image is complete the run measures on its own tracer the shadow's edge against Bardeen's
closed-form critical curve, the photon rings' demagnification against the Lyapunov exponent, and the shadow's size
against the EHT measurements of M87* and Sgr A* (review B5-K10: the closed forms are references next to the computed
values, after them). A world with modified physics replaces the Kerr metric by Johannsen's parametrized deviation: the
engine then computes the edge of its shadow (from its photon orbits), its circular orbits and ergosphere, and its size
against EHT, not an image of the disk.

The scene is stationary: the image does not change in time. The run reveals it as the world's time goes on, a band of
rows at a time (like the scan of a camera); a change of the set-up starts a new image at once. Units: M (G = c = 1).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import backend as B
from lfphys.core import data as D
from lfphys.core.gravity import kerr, kerr_null as KN, kerr_shadow as KS
from lfphys.theories.alternatives import johannsen_metric as JP
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

RES = {"s": 128, "m": 192, "l": 256}
R_OUT = 20.0          # outer edge of the disk, M
SCAN_M = 4.0          # world time (in M) over which one image is scanned at any resolution
N_MAX = 2             # crossings computed per pixel: direct image, lensing ring, photon ring
EPS = np.finfo(float).eps
TARGETS = [("m87", "M87* (EHT 2019)"), ("sgra", "Sgr A* (EHT 2022)"), ("none", "без сравнения")]
PROFILES = [("r2", "J ∝ r⁻² от внутреннего края до 20 M"), ("ring", "узкое кольцо у r = 6 M (ширина 0,3 M)")]


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("metric", "Метрика", "select", "kerr", group="Законы", standard="kerr",
       options=[("kerr", "Керр (ОТО)"), ("jp", "Йоханнсен: отклонение от Керра (что если)")],
       help="Керр — вращающаяся чёрная дыра ОТО. «Что если»: метрика Йоханнсена с параметрами α (при α = 0 — Керр); "
            "для неё движок считает край тени и его размер против EHT, но не изображение диска"),
    _p("a13", "α₁₃: отклонение в A₁ = 1 + α₁₃/r³", "float", 0.0, group="Законы", standard=0.0, min=-10.0, max=10.0,
       show_if={"metric": ["jp"]},
       help="Метрика должна быть регулярна вне горизонта (Johannsen 2013a, ур. 72, 76–78), а её фотонные орбиты — "
            "одной полосой: иначе мир не создаётся и называет значения, которые примет. При a = 0,9 и остальных "
            "α = 0 — α₁₃ ≥ −2,11 (при a = 0 — α₁₃ > −8)"),
    _p("a22", "α₂₂: отклонение в A₂ = 1 + α₂₂/r²", "float", 0.0, group="Законы", standard=0.0, min=-3.0, max=10.0,
       show_if={"metric": ["jp"]},
       help="Допустимые значения зависят от спина и других α. При a = 0,9 и остальных α = 0 — от −2,06 до 5,13 "
            "(при a ≤ 0,5 — любое на ползунке)"),
    _p("a12", "α₁₂: отклонение в A₁ (член α₁₂/r²)", "float", 0.0, group="Законы", standard=0.0, min=-3.0, max=10.0,
       show_if={"metric": ["jp"]},
       help="Допустимые значения зависят от спина и других α. При a = 0,9 и остальных α = 0 — α₁₂ ≥ −1,47 "
            "(при a ≤ 0,5 — любое на ползунке)"),
    _p("chi", "Спин a/M", "float", 0.9, group="Чёрная дыра", min=0.0, max=0.998,
       help="Параметр мира: другой спин — другая чёрная дыра"),
    _p("target", "Сравнить размер тени с", "select", "m87", group="Чёрная дыра", options=TARGETS),
    _p("incl", "Наклон наблюдателя к оси вращения θ, °", "float", D.EHT_M87_INCLINATION_DEG["a_positive"],
       group="Наблюдатель", min=1.0, max=179.0, live=True,
       help="163° — так EHT сравнивал снимки M87* при a > 0 (17° при a ≤ 0; EHT 2019 Paper V, рис. 8): джет к нам под "
            "17°, спин дыры — от нас; 90° — диск с ребра"),
    _p("emitter", "Газ диска", "select", "cunningham", group="Диск", live=True,
       options=[("cunningham", "кеплеровский вне ISCO, падающий внутрь до горизонта (Каннингем)"),
                ("keplerian", "только кеплеровский вне ISCO (внутри не светит)")]),
    _p("retro", "Диск вращается против дыры", "bool", False, group="Диск", live=True),
    _p("profile", "Излучение диска J(r) (модель источника)", "select", "r2", group="Диск", live=True, options=PROFILES),
    _p("res", "Разрешение экрана", "select", "m", group="Экран", live=True,
       options=[("s", "128 × 128"), ("m", "192 × 192"), ("l", "256 × 256")]),
    _p("half", "Полуширина экрана, M", "float", 9.0, group="Экран", min=4.0, max=30.0, live=True),
    _p("n_rays", "Лучей в 3D", "int", 14, group="Экран", min=0, max=40, live=True),
], presets={
    "m87": {"label": "M87*: a = 0,9, наклон 163° (как у EHT при a > 0), диск Каннингема — тень, кольцо линзирования, "
                     "фотонное кольцо",
            "params": {}},
    "edge_on": {"label": "Диск с ребра (θ = 90°), a = 0,99: тень сплюснута, кольца несимметричны",
                "params": {"chi": 0.99, "incl": 90.0}},
    "schwarzschild": {"label": "Без вращения (a = 0): тень — круг радиуса √27 M", "params": {"chi": 0.0, "incl": 60.0}},
    "ring": {"label": "Узкое кольцо газа у 6 M: видны его изображения n = 0, 1, 2", "params": {"profile": "ring", "incl": 60.0}},
    "sgra": {"label": "Sgr A*: a = 0,5, наклон 30°, сравнение с EHT 2022", "params": {"chi": 0.5, "incl": 30.0,
                                                                                       "target": "sgra"}},
    "whatif": {"label": "Что если: метрика Йоханнсена α₁₃ = 3 — тень больше, сравнение с EHT",
               "params": {"metric": "jp", "a13": 3.0, "chi": 0.0, "incl": 17.0}},
})


def _surface(r_of_theta, chi, nth=36, nph=48):
    """A surface r = r(theta) of revolution about the spin axis in the drawing coordinates (kerr_null.cartesian)."""
    th = np.linspace(0.0, math.pi, nth)
    ph = np.linspace(0.0, 2.0 * math.pi, nph, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing="ij")
    x, y, z = KN.cartesian(r_of_theta(T), T, P, chi)
    pos = np.stack([x, y, z], -1).reshape(-1, 3)
    idx = []
    for i in range(nth - 1):
        for j in range(nph):
            a, b = i * nph + j, i * nph + (j + 1) % nph
            c, d = a + nph, b + nph
            idx += [a, c, b, b, c, d]
    return pos.astype(np.float32), np.array(idx, np.uint32)


class Simulation(BaseSimulation):
    default_speed = 1.0                # M of world time per wall second: an image is scanned in SCAN_M seconds
    speed_range = (0.01, 100.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        self.chi = float(p["chi"])
        self.dev = JP.Deviation(p["a12"], p["a13"], p["a22"]) if p["metric"] == "jp" else None
        if self.dev is not None:
            if self.chi >= 1.0:
                raise ValueError("метрика Йоханнсена здесь — при a < M")
            _jp_admissible(self.chi, p)
        self.live = {k: p[k] for k in SCHEMA.live_ids()}
        self.r_plus = kerr.horizons(self.chi)[0]
        self.orbits = self._orbits()
        self.seq = 0
        self.image = None      # the image being scanned (Kerr only)
        self.img_t0 = 0.0      # world time when its scan began
        self.sent_rows = 0
        self.done_checked = False
        self.curve = None
        self._new_image()

    # --- the observer, the screen and the image --------------------------------------------------------------------
    @property
    def theta_o(self):
        return math.radians(float(self.live["incl"]))

    def _screen(self):
        n = RES[self.live["res"]]
        return KS.Screen(n, n, float(self.live["half"]))

    def _r_in(self):
        if self.live["emitter"] == "cunningham":
            return self.r_plus
        return kerr.isco(self.chi, not self.live["retro"])

    def _J(self, r):
        """Emissivity of the disk at radius r: the model of the source (stated), zero off the disk."""
        r = np.asarray(r, float)
        on = np.isfinite(r) & (r >= self._r_in()) & (r <= R_OUT)
        if self.live["profile"] == "ring":
            J = np.exp(-0.5 * ((r - 6.0) / 0.3) ** 2)
        else:
            J = 1.0 / np.where(on, r, 1.0) ** 2
        return np.where(on, J, 0.0)

    def _new_image(self):
        """Start the scan of a new image for the set-up in force (Kerr). The closed-form critical curve goes with it as
        the reference the view draws over the rows computed so far; the checks come when the image is complete (review
        B5-K10). In a "what if" world the deviating metric's shadow edge is the world's computed result (from its
        photon orbits) and is compared with EHT at once."""
        self.seq += 1
        self.img_t0 = self.t
        self.sent_rows = 0
        self.done_checked = False
        th = self.theta_o
        if self.dev is None:
            self.image = KS.ShadowImage(self.chi, th, self._screen(), N_MAX, self.live["emitter"],
                                        not self.live["retro"])
            self.curve = KN.critical_curve(self.chi, th, 721)
        else:
            self.image = None
            try:
                self.curve = JP.shadow_curve(self.chi, th, self.dev, 721)
            except ValueError as e:  # P6: in the owner's terms
                raise Refusal(f"при наклоне θ = {self.live['incl']:g}° не видна ни одна сферическая фотонная орбита "
                              "этой метрики: края тени нет", "возьмите другой наклон наблюдателя θ",
                              detail=str(e)) from e
        self.kerr_curve = KN.critical_curve(self.chi, th, 721)
        sc = self._screen()
        self._msg({"type": "curve", "t": self.t, "seq": self.seq, "metric": self.params["metric"],
                   "half": sc.half_width, "n": sc.nx},
                  {"alpha": self.curve["alpha"].astype(np.float32), "beta": self.curve["beta"].astype(np.float32),
                   "kerr_alpha": self.kerr_curve["alpha"].astype(np.float32),
                   "kerr_beta": self.kerr_curve["beta"].astype(np.float32)})
        self._observer()
        self._rays()
        if self.dev is not None:
            self._eht_whatif()

    def _rows_due(self):
        if self.image is None:
            return 0
        ny = self.image.screen.ny
        return min(ny, int(math.floor((self.t - self.img_t0) / SCAN_M * ny + 1e-9)) + 1)

    def _scan(self):
        """Compute and send the rows of the image that the world's time has reached."""
        img = self.image
        if img is None:
            return
        due = self._rows_due()
        if due <= img.next_row:
            return
        i0 = img.next_row
        while img.next_row < due:
            img.step(due - img.next_row)
        self._send_rows(i0, img.next_row)
        if img.done and not self.done_checked:
            self.done_checked = True
            self._image_checks()

    def _send_rows(self, i0, i1):
        a = self.image.arrays
        cap = a["captured"][i0:i1]
        r_n, g_n = a["r_n"][:, i0:i1], a["g_n"][:, i0:i1]
        I_n = np.where(np.isfinite(g_n), np.nan_to_num(g_n) ** 4 * self._J(r_n), 0.0)
        sc = self.image.screen
        # sent as they are (not compressed): the browser takes them in at once, so that the view at any time of the
        # history is a function of the messages fed (key frames of the player); ~29 bytes per pixel
        meta = {"type": "rows", "t": self.t, "seq": self.seq, "i0": int(i0), "i1": int(i1), "nx": sc.nx,
                "ny": sc.ny, "half": sc.half_width, "n_max": N_MAX, "r_in": self._r_in(), "r_out": R_OUT,
                "device": B.used().get(KS.KERNEL, {}).get("drawn")}
        # face: the side of the disk the photon left at each crossing (+1 towards +z, the spin; -1 the other; 0 none)
        blobs = {"cap": cap.astype(np.uint8), "I": I_n.astype(np.float32),
                 "g": np.nan_to_num(g_n, nan=0.0).astype(np.float32),
                 "r": np.nan_to_num(r_n, nan=0.0).astype(np.float32),
                 "face": np.nan_to_num(a["face_n"][:, i0:i1], nan=0.0).astype(np.int8)}
        self.sent_rows = i1
        self._msg(meta, blobs)

    # --- the 3-D scene: the hole, the disk, the observer, sample rays ------------------------------------------------
    def _observer(self):
        th = self.theta_o
        n = np.array([math.sin(th), 0.0, math.cos(th)])
        self._msg({"type": "arrow", "t": self.t, "id": "observer", "from": (24.0 * n).tolist(), "vec": (-7.0 * n).tolist(),
                   "label": f"наблюдатель: θ = {float(self.live['incl']):.4g}°", "layer": "Наблюдатель (далеко, в этом направлении)",
                   "color": "#7fb7ff"})
        r_in = self._r_in()
        rr = np.linspace(r_in, R_OUT, 40)
        ph = np.linspace(0.0, 2.0 * math.pi, 96, endpoint=False)
        Rg, Pg = np.meshgrid(rr, ph, indexing="ij")
        x, y, z = KN.cartesian(Rg, np.full_like(Rg, math.pi / 2), Pg, self.chi)
        pos = np.stack([x, y, z], -1).reshape(-1, 3).astype(np.float32)
        J = self._J(Rg).reshape(-1)
        J = J / max(float(J.max()), 1e-300)
        rgb = np.stack([255 * J ** 0.5, 150 * J ** 0.7, 40 + 60 * J], -1).clip(0, 255).astype(np.uint8)
        idx = []
        for i in range(len(rr) - 1):
            for j in range(len(ph)):
                a_, b_ = i * len(ph) + j, i * len(ph) + (j + 1) % len(ph)
                idx += [a_, a_ + len(ph), b_, b_, a_ + len(ph), b_ + len(ph)]
        self._msg({"type": "mesh", "t": self.t, "id": "disk", "count": int(len(pos)), "opacity": 0.55,
                   "label": f"Диск: излучение J(r) от {r_in:.4g} до {R_OUT:g} M (модель источника)"},
                  {"pos": pos, "idx": np.array(idx, np.uint32), "rgb": rgb})

    def _rays(self):
        """Sample photons of the screen traced back through the scene: along the screen's horizontal and vertical
        axes, several just outside the critical curve (they wind around the hole before leaving)."""
        n = int(self.live["n_rays"])
        pts, col = [], []
        if n > 0 and self.dev is None:
            th = self.theta_o
            angles = [0.0, math.pi, math.pi / 2, -math.pi / 2]
            factors = [0.6, 0.95, 1.003, 1.02, 1.1, 1.4, 2.0, 3.0, 4.5, 6.0]
            chosen = []
            for k in range(n):
                ang = angles[k % len(angles)]
                f = factors[(k // len(angles)) % len(factors)]
                chosen.append((ang, f))
            for ang, f in chosen:
                rho_c, _ = KN.critical_radius_at(self.chi, th, ang)
                al, be = f * rho_c * math.cos(ang), f * rho_c * math.sin(ang)
                try:
                    path = KN.screen_ray_path(al, be, th, self.chi, r_out=26.0, n=240)
                except ValueError:
                    continue
                P = np.stack([path["x"], path["y"], path["z"]], -1)
                c = (0.95, 0.35, 0.3) if path["captured"] else ((1.0, 0.85, 0.35) if f < 1.05 else (0.55, 0.8, 1.0))
                pts.append(P)
                col.append(np.tile(c, (len(P), 1)))
                pts.append(np.full((1, 3), np.nan))
                col.append(np.zeros((1, 3)))
        P = np.concatenate(pts) if pts else np.zeros((0, 3))
        C = np.concatenate(col) if col else np.zeros((0, 3))
        self._msg({"type": "lines", "t": self.t, "id": "rays",
                   "label": "Лучи к наблюдателю (посчитаны): красные — захвачены, жёлтые — у критической кривой, голубые — дальше"},
                  {"pts": P.astype(np.float32).reshape(-1), "rgb": C.astype(np.float32).reshape(-1)})

    def _orbits(self):
        """The equatorial circular orbits of this world's metric: Kerr's closed forms, or the deviating metric's own,
        computed numerically (johannsen_metric.circular_orbits; review B5-K7)."""
        if self.dev is None:
            return {"ph_pro": kerr.photon_orbit(self.chi, True), "ph_retro": kerr.photon_orbit(self.chi, False),
                    "isco_pro": kerr.isco(self.chi, True), "isco_retro": kerr.isco(self.chi, False)}
        try:
            o = JP.circular_orbits(self.chi, self.dev)
        except ValueError as e:  # the shadow is still computable: the world goes on without the rings (P6)
            s = str(e)
            why = ("нет круговой фотонной орбиты между горизонтом и 60 M" if "photon orbit" in s else
                   "нет устойчивых круговых орбит даже на 200 M" if "stable" in s else
                   "внутренняя граница устойчивых круговых орбит (ISCO) не найдена до 200 M")
            self._msg({"type": "notice", "t": self.t, "text": (
                f"Круговые орбиты этой метрики в экваторе не нарисованы: {why}. Край тени и его сравнение с EHT "
                "считаются")})
            return None
        return {"ph_pro": o["photon_pro"], "ph_retro": o["photon_retro"], "isco_pro": o["isco_pro"],
                "isco_retro": o["isco_retro"], "isco_kind": o.get("isco_kind_pro", "stability")}

    def _static_scene(self):
        """The hole: horizon, ergosphere, the equatorial photon orbits and the ISCO (of this world's metric)."""
        rp = self.r_plus
        pos, idx = _surface(lambda T: np.full_like(T, rp), self.chi)
        self._msg({"type": "mesh", "t": self.t, "id": "horizon", "count": int(len(pos)), "opacity": 1.0,
                   "label": f"Горизонт r₊ = {rp:.6g} M"},
                  {"pos": pos, "idx": idx, "rgb": np.tile(np.array([[12, 12, 16]], np.uint8), (len(pos), 1))})
        if self.dev is None:
            pos, idx = _surface(lambda T: 1.0 + np.sqrt(np.maximum(1.0 - self.chi ** 2 * np.cos(T) ** 2, 0.0)), self.chi)
            ergo = "Эргосфера (внутри неё ничто не может покоиться)"
        else:
            pos, idx = _surface(lambda T: JP.ergosurface(self.chi, self.dev, T), self.chi)
            ergo = "Эргосфера этой метрики: g_tt = 0, Δ = a²A₂² sin²θ (Johannsen 2013a, ур. 69)"
        self._msg({"type": "mesh", "t": self.t, "id": "ergo", "count": int(len(pos)), "opacity": 0.18, "label": ergo},
                  {"pos": pos, "idx": idx, "rgb": np.tile(np.array([[120, 90, 200]], np.uint8), (len(pos), 1))})
        ph = np.linspace(0.0, 2.0 * math.pi, 181)
        pts, col = [], []
        o = self.orbits
        if o is None:
            return
        rings = [(o["ph_pro"], (1.0, 0.85, 0.35)), (o["ph_retro"], (1.0, 0.6, 0.2)), (o["isco_pro"], (0.5, 0.9, 0.6))]
        for r, c in rings:
            x, y, z = KN.cartesian(np.full_like(ph, r), np.full_like(ph, math.pi / 2), ph, self.chi)
            pts.append(np.stack([x, y, z], -1)); col.append(np.tile(c, (len(ph), 1)))
            pts.append(np.full((1, 3), np.nan)); col.append(np.zeros((1, 3)))
        which = "" if self.dev is None else " этой метрики (посчитаны численно)"
        if o.get("isco_kind") == "existence":  # P6: a band without circular geodesics bounds the stable orbits
            which += (f"; ISCO = {o['isco_pro']:.4g} M — край области, где круговые орбиты вообще есть (внутри до "
                      "фотонной орбиты Ω² < 0: тяготение там отталкивает)")
        self._msg({"type": "lines", "t": self.t, "id": "orbits",
                   "label": f"Круговые орбиты в экваторе{which}: фотонные (по и против вращения) и ISCO"},
                  {"pts": np.concatenate(pts).astype(np.float32).reshape(-1),
                   "rgb": np.concatenate(col).astype(np.float32).reshape(-1)})

    # --- checks ------------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group="Тень"):
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

    def _image_checks(self):
        """When an image is complete, on the run's own tracer: the shadow's edge against Bardeen's curve, the radius
        at a = 0, the photon rings' demagnification, the shadow's size against the closed form and against EHT, the
        captured pixels against the inside of the curve, and the GPU's rows against the CPU's (review B5-K10: the
        closed forms are references, posted after the computed values they check)."""
        th = self.theta_o
        # the tracer's own edge (bisection on its fate) against Bardeen's closed-form curve, in 8 directions, each
        # within its derived bound (kerr_shadow.edge_tolerance, review B5-K1)
        ang = 2.0 * math.pi * np.arange(8) / 8
        lo, hi = KS.capture_boundaries(self.chi, th, ang, rho_max=18.0)
        edge = 0.5 * (lo + hi)
        tol = KS.edge_tolerance(self.chi, th, ang, edge) + (hi - lo)
        rc, _ = KN.critical_radii(self.chi, th, ang)
        err = np.maximum(np.abs(lo - rc), np.abs(hi - rc))
        k = int(np.argmax(err / tol))
        self._check("edge", "Край тени: где луч перестаёт захватываться против кривой Бардина (отн.)",
                    float(err[k] / rc[k]), 0.0, tol=float(tol[k] / rc[k]), ok=bool(np.all(err <= tol)),
                    note="8 направлений на экране: граница захвата найдена делением пополам по самому трассировщику "
                         "(его исход для каждого луча), кривая — замкнутая формула сферических фотонных орбит; допуск "
                         "выведен для каждого направления: ошибка округления d₃₄ = (r₄ − r₃)²/4, знак которой решает "
                         "исход, делённая на её наклон, плюс точность формулы кривой и последний шаг деления")
        if self.chi == 0.0:
            b = math.sqrt(27.0)
            e = np.abs(edge - b) + 0.5 * (hi - lo)
            kk = int(np.argmax(e / tol))
            self._check("schw", "Без вращения: край тени по трассировщику против √27 M", float(np.max(edge)), b, "M",
                        tol=float(tol[kk] / b), ok=bool(np.all(e <= tol)),
                        note="край, найденный по исходу лучей в 8 направлениях, против окружности радиуса √27 M "
                             "(Синг 1966); допуск — тот же выведенный, что у края тени")
        # photon rings: the n-th image of a ring of gas approaches the curve by e^-gamma per half-orbit
        try:
            r_src = max(8.0, self._r_in() + 1.0)
            rhos = [KS.ring_image(self.chi, th, r_src, 0.0, n)[0] for n in (1, 2, 3)]
            rho_c, r_b = KN.critical_radius_at(self.chi, th, 0.0)
            eg = float(np.exp(-KN.lyapunov(np.array([r_b]), self.chi)[0]))
            ratio = (rhos[2] - rho_c) / (rhos[1] - rho_c)
            ratio1 = (rhos[1] - rho_c) / (rhos[0] - rho_c)
            tl = 4.0 * abs(ratio1 - eg) * eg + 1e-6
            self._check("lyapunov", "Фотонное кольцо: сжатие изображений n = 2 → 3 против e^(−γ)", ratio, eg,
                        tol=max(tl / eg, 1e-6), ok=abs(ratio - eg) <= tl,
                        note=f"изображения кольца газа r = {r_src:.3g} M в направлении α > 0: расстояние до кривой "
                             f"убывает в e^γ раз за полупериод по θ (Johnson et al. 2020), γ = {-math.log(eg):.6g} у "
                             f"орбиты r = {r_b:.6g} M; отношение n = 1 → 2 = {ratio1:.6g}; допуск — 4 e^(−γ)·|"
                             f"отклонение n = 1 → 2| (поправки убывают как e^(−γ) с каждым порядком)")
        except ValueError as e:
            self._check("lyapunov", "Фотонное кольцо: сжатие изображений", None, None, info=True,
                        note=f"не посчитано: {e}")
        # the size on the tracer's edge (128 directions) against the closed form, then against EHT
        sz = KS.shadow_size(self.chi, th)
        ok = abs(sz["delta"] - sz["delta_closed"]) <= sz["delta_tol"]
        ref = sz["delta_closed"]
        self._check("size", "Размер тени δ по краю трассировщика против замкнутой формы", sz["delta"], ref,
                    tol=sz["delta_tol"] / abs(ref) if ref else sz["delta_tol"], ok=ok,
                    note=f"медианный диаметр по 128 направлениям от середины между крайними α (EHT 2022, Sgr A* Paper "
                         f"VI, ур. 14: δ = d/(6√3 M) − 1): по краю трассировщика {sz['median_diameter']:.12g} M, по "
                         f"кривой Бардина {sz['median_diameter_closed']:.12g} M; допуск {sz['delta_tol']:.2g} — "
                         f"выведенные допуски края")
        self._eht_kerr(sz)
        self._pixels_check()
        self._gpu_check()

    def _eht_kerr(self, sz):
        """A Kerr world against EHT (review B5-K4). M87* (EHT 2019 Paper VI Sec. 9.5, Eq. 31) measured
        delta = theta_g(ring)/theta_g(stellar dynamics) - 1 with the ring calibrated on Kerr GRMHD models: every Kerr
        hole has delta = 0 there, and Psaltis et al. 2020 use it as the deviation of the size from Kerr's within 17 %
        - so a Kerr world's comparison is its deviation from itself. Sgr A* (EHT 2022 Paper VI) bounds the shadow
        size itself, delta = d/(6 sqrt 3) - 1: the traced delta against it."""
        tgt = self.params["target"]
        d = sz["delta"]
        th_g = D.EHT_M87_THETA_G_UAS[0]
        size_note = (f"размер тени этого мира по определению EHT 2022 (Sgr A* Paper VI, ур. 14): δ = {d:.6g}, медианный "
                     f"диаметр {sz['median_diameter']:.6g} M по краю, найденному трассировщиком")
        if tgt == "m87":
            s = D.EHT_M87_DELTA_STELLAR[1]
            self._check("eht", f"M87*: отклонение размера тени от керровского (та же a и θ) против EHT 2019 ±{s:.2f}",
                        0.0, 0.0, tol=s, ok=True, info=True, group="Сравнение с EHT",
                        note=f"EHT 2019 (Paper VI, разд. 9.5, ур. 31) мерил δ = θg(кольцо)/θg(масса по звёздам) − 1 = "
                             f"{D.EHT_M87_DELTA_STELLAR[0]} ± {s}, откалибровав кольцо на керровских моделях: у любой "
                             f"керровской дыры там δ = 0, и этот мир (Керр) с ним согласен; ±{s} как у Psaltis et al. "
                             f"2020. {size_note}; угловой диаметр тени при θg = {th_g} мкс дуги — "
                             f"{sz['median_diameter'] * th_g:.4g} мкс дуги (кольцо EHT 42 ± 3 мкс дуги — кольцо "
                             f"излучения, а не тень)")
        elif tgt == "sgra":
            lo, hi = (v - 1.0 for v in D.EHT_SGRA_SHADOW_RADIUS_VLTI)
            v, up, dn = D.EHT_SGRA_DELTA_VLTI
            self._check("eht", f"Sgr A*: δ этого мира против EHT 2022 (VLTI) {v:+.2f} +{up}/−{dn}", d, v,
                        tol=max(up, dn), ok=lo <= d <= hi, info=True, group="Сравнение с EHT",
                        note=f"{size_note}; интервал 68 % [{lo:+.2f}, {hi:+.2f}] (EHT 2022 Paper VI, ур. 13, VLTI)")

    def _eht_whatif(self):
        """A "what if" world against EHT: the size of the deviating metric's shadow edge (computed from its photon
        orbits) and of the Kerr hole with the same spin and inclination, in the same convention."""
        tgt = self.params["target"]
        th = self.theta_o
        d_jp = JP.delta(self.chi, th, self.dev)
        d_k = JP.delta(self.chi, th, None)
        if tgt == "m87":
            s = D.EHT_M87_DELTA_STELLAR[1]
            self._check("eht", f"M87*: отклонение размера тени от керровского δ − δ_Керр против EHT 2019 ±{s:.2f}",
                        d_jp - d_k, 0.0, tol=s, ok=abs(d_jp - d_k) <= s, info=True, group="Сравнение с EHT",
                        note=f"EHT 2019 (Paper VI, ур. 31) мерил θg по кольцу, откалиброванному на Керре, против θg по "
                             f"звёздам: отклонение размера от керровского в пределах ±{s} (Psaltis et al. 2020); δ этой "
                             f"метрики {d_jp:.6g}, Керра {d_k:.6g} (медианный диаметр, EHT 2022 Paper VI, ур. 14)")
        elif tgt == "sgra":
            lo, hi = (v - 1.0 for v in D.EHT_SGRA_SHADOW_RADIUS_VLTI)
            v, up, dn = D.EHT_SGRA_DELTA_VLTI
            self._check("eht", f"Sgr A*: δ этой метрики против EHT 2022 (VLTI) {v:+.2f} +{up}/−{dn}", d_jp, v,
                        tol=max(up, dn), ok=lo <= d_jp <= hi, info=True, group="Сравнение с EHT",
                        note=f"δ = d/(6√3 M) − 1, медианный диаметр края тени этой метрики; интервал 68 % "
                             f"[{lo:+.2f}, {hi:+.2f}] (EHT 2022 Paper VI, ур. 13, VLTI)")
        self._check("eht_kerr", "Та же дыра по Керру: δ", d_k, None, info=True, group="Сравнение с EHT",
                    note=f"отклонение метрики меняет δ на {d_jp - d_k:+.4g}")

    def _pixels_check(self):
        """The image's captured pixels against the inside of the critical curve, every pixel farther from the curve
        than the polygon of the drawn curve can be from the true one (its chords' sag, measured against a curve of
        8001 points, review B5-K16), so a shadow too large or small by more than ~1e-4 M is caught."""
        img = self.image
        sc = img.screen
        A, Bm = np.meshgrid(sc.alpha(), sc.beta())
        ax, bx = self.curve["alpha"], self.curve["beta"]
        dense = KN.critical_curve(self.chi, self.theta_o, 8001)
        sag = float(np.max(_distance_to_curve(ax, bx, dense["alpha"], dense["beta"])))
        margin = 1.1 * sag + 1e-9
        inside = _inside(ax, bx, A, Bm)
        far = _distance_to_curve(ax, bx, A, Bm) > margin
        bad = int(np.sum((img.arrays["captured"].astype(bool) != inside) & far))
        self._check("pixels", "Тень на изображении: захваченные пиксели против внутренности кривой",
                    bad, 0, "пикс.", tol=0, ok=bad == 0,
                    note=f"{int(np.sum(far))} из {far.size} пикселей дальше {margin:.2g} M от кривой (на столько "
                         f"ломаная из 721 точки может отойти от самой кривой); несовпадений {bad}")

    def _gpu_check(self):
        """When the image ran on GPU 0: its middle row against the same code on the CPU (review B5-kerr-v15 K2). The
        crossing radii within the engine's GPU test bound, 128 u (|alpha dr/dalpha| + |beta dr/dbeta| + |r|) by
        central differences on the CPU; the redshift within that bound propagated plus the formula's own rounding
        (``kerr_shadow.redshift_tolerance``: near a photon's turning point and inside the ISCO the square roots of
        cancelling differences amplify it); the values farther than 0.05 M from the critical curve, where these
        sensitivities are bounded; the fate of every pixel not within 1e-9 M of it."""
        dev = B.used().get(KS.KERNEL, {}).get("drawn")
        if not (dev and dev.get("device") == "gpu"):
            return
        img, sc = self.image, self.image.screen
        j = sc.ny // 2
        a_, b_ = sc.rows(j, j + 1)
        args = (self.theta_o, self.chi, N_MAX, self.live["emitter"], not self.live["retro"])
        cpu = KS._trace(np, a_, b_, *args)
        h = 1e-6

        def r(da, db):
            return KS._trace(np, a_ + da, b_ + db, *args)["r_n"]
        sens = (np.abs(a_) * np.abs(r(h, 0.0) - r(-h, 0.0)) + np.abs(b_) * np.abs(r(0.0, h) - r(0.0, -h))) / (2 * h)
        r_tol = 64 * EPS * (sens + np.abs(cpu["r_n"]))
        tol = KS.redshift_tolerance(cpu["r_n"], cpu["lam"][None], cpu["eta"][None], cpu["kr_sign_n"], self.chi,
                                    self.live["emitter"], not self.live["retro"], r_tol=r_tol)
        dist = _distance_to_curve(self.curve["alpha"], self.curve["beta"], a_, b_)
        g_cpu, g_gpu = cpu["g_n"], img.arrays["g_n"][:, j:j + 1]
        r_gpu = img.arrays["r_n"][:, j:j + 1]
        fate_ok = bool(np.array_equal(np.asarray(cpu["captured"], bool)[dist > 1e-9],
                                      img.arrays["captured"][j:j + 1].astype(bool)[dist > 1e-9]))
        far = np.broadcast_to(dist > 0.05, g_cpu.shape)
        same = bool(np.array_equal(np.isfinite(g_cpu)[far], np.isfinite(g_gpu)[far]))
        cmp = far & np.isfinite(g_cpu) & np.isfinite(g_gpu) & np.isfinite(tol) & np.isfinite(r_tol)
        r_ok = bool(np.all(np.abs(cpu["r_n"] - r_gpu)[cmp] <= r_tol[cmp]))
        err = np.abs(g_cpu - g_gpu)
        ratio = np.where(cmp, err / np.where(tol > 0, tol, np.inf), 0.0)
        k = np.unravel_index(int(np.argmax(ratio)), ratio.shape)
        worst = float(err[k]) if cmp.any() else 0.0
        self._check("gpu", "GPU против CPU: красное смещение средней строки", worst, 0.0,
                    tol=float(tol[k]) if cmp.any() else 0.0,
                    ok=fate_ok and same and r_ok and bool(np.all(err[cmp] <= tol[cmp])), group="Где считалось",
                    note=f"тот же код на NumPy и CuPy в fp64: функции CUDA отличаются от glibc на ≤ 2 ulp; радиусы "
                         f"пересечений — в пределах 128 u × чувствительность (|α ∂r/∂α| + |β ∂r/∂β| + |r|, центральные "
                         f"разности на CPU), красное смещение — в пределах её следствия для g плюс округление самой "
                         f"формулы (у точки поворота луча и внутри ISCO корни из сокращающихся разностей); сравнено "
                         f"{int(cmp.sum())} значений дальше 0,05 M от кривой, исход — у всех пикселей строки")

    # --- messages and time ------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, None
        self._static_scene()
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def advance(self, t_target):
        self.t = t_target
        self._scan()

    def max_step(self):
        return SCAN_M / 8.0

    def frame(self):
        img = self.image
        return {"seq": self.seq, "rows": (img.next_row if img else 0), "ny": (img.screen.ny if img else 0),
                "done": bool(img.done) if img else True}, {}

    def next_event_time(self):
        if self.image is None or self.image.done:
            return None
        return self.img_t0 + SCAN_M

    # --- live set-up ----------------------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        merged, errors = SCHEMA.coerce_live(self.live, values)
        if errors:
            raise ValueError("; ".join(errors))
        old = self.live
        self.live = merged
        try:
            self._new_image()
        except Exception:
            self.live = old
            raise
        self._scan()
        gas = {"cunningham": "диск Каннингема", "keplerian": "кеплеровский диск"}[merged["emitter"]]
        return (f"наблюдатель θ = {float(merged['incl']):.4g}°; газ: {gas}"
                f"{', против вращения' if merged['retro'] else ''}; экран {RES[merged['res']]}², ±{float(merged['half']):.4g} M"
                f" — новое изображение")

    def engine_modules(self):
        mods = ["core.gravity.kerr_shadow", "core.gravity.kerr_null", "core.gravity.kerr", "core.backend", "core.data"]
        if self.dev is not None:
            mods.append("theories.alternatives.johannsen_metric")
        return mods

    def header(self):
        p = self.params
        modified = p["metric"] != "kerr"
        objects = []
        # the spin axis (physics z) up; the views look from the directions named (review B5-K8)
        views = [["iso", "Изо", "Изометрия (F)", [0.55, -0.7, 0.45]],
                 ["obs", "Наблюдатель", "С направления наблюдателя: как на экране, ось вращения вверх",
                  {"along": "observer"}],
                 ["side", "С ребра", "Сбоку: диск с ребра, ось вращения вверх", [0.0, -1.0, 0.0]],
                 ["pole", "С полюса", "С оси вращения (сверху): диск плашмя", [0.0, 0.0, 1.0]]]
        approximations = ["излучатель — тонкий экваториальный диск с излучением J(r) (модель источника, не закон)",
                          "геометрическая оптика, экран на бесконечности, без поглощения"]
        if modified:
            approximations.append("метрика Йоханнсена: считается край тени (фотонные орбиты), изображение диска — нет")
        return {
            "title": ("Тень чёрной дыры Керра" if not modified else "Что если дыра не керровская: тень метрики Йоханнсена")
                     + f": a = {self.chi:.4g}",
            "text": ("Каждый пиксель экрана далёкого наблюдателя — фотон, прослеженный назад в замкнутом виде: захвачен "
                     "дырой (тень) или пришёл издалека, и где пересёк плоскость диска — n-е пересечение по лучу назад: "
                     "при умеренном наклоне n = 0 — прямое изображение, n = 1 — кольцо линзирования, n = 2 — фотонное "
                     "кольцо; почти с ребра нижняя сторона диска видна прямо как n = 1. Яркость — сумма g⁴J(r) по "
                     "пересечениям (модель источника). Когда изображение досчитано, край тени по трассировщику "
                     "сверяется с формулой Бардина, кольца — с экспоненциальным сжатием, размер — с EHT."),
            "actions": [],
            "modifications": SCHEMA.modifications(p),  # the "what if" metric is flagged as modified physics
            "approximations": approximations,
            "scene3d": {"box": [[-24.0, -24.0, -24.0], [24.0, 24.0, 24.0]], "units": "M", "objects": objects,
                        "layers": [], "views": views, "up": [0.0, 0.0, 1.0],
                        "planes": {"max": 0, "center": [0, 0, 0], "defaults": {}}},
            # the circular orbits of this world's metric; in a "what if" world Kerr's too, for comparison (B5-K7)
            "hole": {"chi": self.chi, "r_plus": self.r_plus, **(self.orbits or {}),
                     "kerr": None if self.dev is None else {
                         "isco_pro": kerr.isco(self.chi, True), "isco_retro": kerr.isco(self.chi, False),
                         "ph_pro": kerr.photon_orbit(self.chi, True), "ph_retro": kerr.photon_orbit(self.chi, False)}},
            "metric": {"kind": p["metric"], "a12": p["a12"], "a13": p["a13"], "a22": p["a22"]},
            "scan_m": SCAN_M, "r_out": R_OUT, "n_max": N_MAX,
            "units": {"t": "M (G = c = 1): время мира; изображение стационарно, строки досчитываются по ходу времени",
                      "x": "M"},
        }, {}


_JP_PARAMS = (("a13", "alpha13", "α₁₃"), ("a22", "alpha22", "α₂₂"), ("a12", "alpha12", "α₁₂"))
_MARGIN_RU = {"A1": "A₁ ≤ 0 (до {v})", "A2": "A₂ ≤ 0 (до {v})",
              "det_eq72": "det g обращается в нуль (ур. 72)", "ctc_eq76": "замкнутые времениподобные кривые (ур. 76)"}


def _num(x):
    return f"{x:.3g}".replace("-", "−")


def _jp_admissible(chi, p):
    """Refuse, in the owner's terms, a Johannsen metric whose shadow edge the engine cannot compute (review UX-params
    P6): not regular outside the horizon (Johannsen 2013a Eqs. 72, 76-78), or its photon orbits not one band. The
    refusal names what fails and, for each deviation with the others as they are, the values the world takes
    (``johannsen_metric.admissible_intervals`` over the slider's range)."""
    dev = JP.Deviation(p["a12"], p["a13"], p["a22"])
    why = JP.shadow_computable(chi, dev)
    if why is None:
        return
    now = ", ".join(f"{lab} = {_num(p[pid])}" for pid, _, lab in _JP_PARAMS)
    if why == "regular":
        m = JP.regularity_margins(chi, dev)
        bad = "; ".join(_MARGIN_RU[k].format(v=_num(v)) for k, v in m.items() if not v > 0.0)
        head = (f"метрика Йоханнсена при a = {chi:g} и {now} не регулярна вне горизонта: {bad} (Johannsen 2013a, "
                "ур. 72, 76–78) — такой метрики нет как чёрной дыры, тень не строится.")
    else:
        head = (f"у метрики Йоханнсена при a = {chi:g} и {now} фотонные орбиты не образуют одну полосу между "
                "горизонтом и 12 M (их несколько или нет): край тени здесь не вычисляется.")
    tips = []
    for pid, key, lab in _JP_PARAMS:
        par = SCHEMA.by_id[pid]
        others = {k: p[q] for q, k, _ in _JP_PARAMS if q != pid}
        iv = JP.admissible_intervals(chi, key, others, par.min, par.max)
        if not iv:
            tips.append(f"{lab} — никакое значение от {_num(par.min)} до {_num(par.max)} не помогает")
        else:
            tips.append(f"{lab} — " + " или ".join(f"от {_num(a)} до {_num(b)}" for a, b in iv))
    raise Refusal(head, "мир строится, если изменить одно значение (остальные как сейчас): " + "; ".join(tips)
                  + ("; при меньшем спине a промежутки обычно шире" if chi > 0 else ""))


def _inside(ax, bx, A, Bm):
    """Point-in-polygon (even-odd rule) of the screen points (A, Bm) in the closed curve (ax, bx)."""
    inside = np.zeros(A.shape, bool)
    n = len(ax)
    for k in range(n - 1):
        x0, y0, x1, y1 = ax[k], bx[k], ax[k + 1], bx[k + 1]
        if y0 == y1:
            continue
        cond = (y0 > Bm) != (y1 > Bm)
        xc = x0 + (Bm - y0) * (x1 - x0) / (y1 - y0)
        inside ^= cond & (A < xc)
    return inside


def _distance_to_curve(ax, bx, A, Bm):
    """Distance of the screen points to the polyline (ax, bx)."""
    P = np.stack([A.ravel(), Bm.ravel()], -1)
    best = np.full(len(P), np.inf)
    for k in range(len(ax) - 1):
        a = np.array([ax[k], bx[k]]); b = np.array([ax[k + 1], bx[k + 1]])
        d = b - a
        L2 = float(d @ d)
        if L2 == 0.0:
            continue
        s = np.clip(((P - a) @ d) / L2, 0.0, 1.0)
        q = a + s[:, None] * d
        best = np.minimum(best, np.hypot(*(P - q).T))
    return best.reshape(A.shape)


VIZ = {
    "id": "v15_kerr_shadow",
    "title": "Тень чёрной дыры Керра и кольца фотонов",
    "summary": ("Что видит далёкий наблюдатель вращающейся чёрной дыры с диском газа: тень, кольцо линзирования и "
                "фотонное кольцо — каждый пиксель как луч, прослеженный назад в замкнутом виде; край тени против формулы "
                "Бардина, сжатие колец против показателя Ляпунова, размер против EHT; что если метрика не керровская."),
    "purpose": ("Показать, откуда берётся тень и кольца на снимках EHT, как их форма зависит от спина и наклона, и чем "
                "можно проверить, что дыра — керровская."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
