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
from lfphys.i18n import T, english, join, text_of
from lfphys.theories.alternatives import johannsen_metric as JP
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

RES = {"s": 128, "m": 192, "l": 256}
R_OUT = 20.0          # outer edge of the disk, M
SCAN_M = 4.0          # world time (in M) over which one image is scanned at any resolution
N_MAX = 2             # crossings computed per pixel: direct image, lensing ring, photon ring
EPS = np.finfo(float).eps
TARGETS = [("m87", "M87* (EHT 2019)"), ("sgra", "Sgr A* (EHT 2022)"), ("none", T("no comparison"))]
PROFILES = [("r2", T("J ∝ r⁻² from the inner edge to {r} M", r=20)),
            ("ring", T("a narrow ring at r = {r} M (width {w} M)", r=6, w=0.3))]
G_LAWS, G_HOLE, G_DISK, G_SCREEN = T("Laws"), T("Black hole"), T("Disk"), T("Screen")


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    _p("metric", T("Metric"), "select", "kerr", group=G_LAWS, standard="kerr",
       options=[("kerr", T("Kerr (GR)")), ("jp", T("Johannsen: a deviation from Kerr (what if)"))],
       help=T("Kerr is the rotating black hole of GR. “What if”: the Johannsen metric with the parameters α (α = 0 is "
              "Kerr); for it the engine computes the edge of the shadow and its size against EHT, but not an image of "
              "the disk")),
    _p("a13", T("α₁₃: deviation in A₁ = 1 + α₁₃/r³"), "float", 0.0, group=G_LAWS, standard=0.0, min=-10.0, max=10.0,
       show_if={"metric": ["jp"]},
       help=T("The metric must be regular outside the horizon (Johannsen 2013a, Eqs. 72, 76–78), and its photon orbits "
              "must form one band: otherwise the world is not built and names the values it takes. At a = {a} with "
              "the other α = 0: α₁₃ ≥ {lo} (at a = 0: α₁₃ > {lo0})", a=0.9, lo=-2.11, lo0=-8)),
    _p("a22", T("α₂₂: deviation in A₂ = 1 + α₂₂/r²"), "float", 0.0, group=G_LAWS, standard=0.0, min=-3.0, max=10.0,
       show_if={"metric": ["jp"]},
       help=T("The admissible values depend on the spin and the other α. At a = {a} with the other α = 0: from {lo} to "
              "{hi} (at a ≤ {a0}: any value on the slider)", a=0.9, lo=-2.06, hi=5.13, a0=0.5)),
    _p("a12", T("α₁₂: deviation in A₁ (the term α₁₂/r²)"), "float", 0.0, group=G_LAWS, standard=0.0, min=-3.0,
       max=10.0, show_if={"metric": ["jp"]},
       help=T("The admissible values depend on the spin and the other α. At a = {a} with the other α = 0: α₁₂ ≥ {lo} "
              "(at a ≤ {a0}: any value on the slider)", a=0.9, lo=-1.47, a0=0.5)),
    _p("chi", T("Spin a/M"), "float", 0.9, group=G_HOLE, min=0.0, max=0.998,
       help=T("A world parameter: another spin is another black hole")),
    _p("target", T("Compare the shadow's size with"), "select", "m87", group=G_HOLE, options=TARGETS),
    _p("incl", T("Observer's inclination to the spin axis θ, °"), "float", D.EHT_M87_INCLINATION_DEG["a_positive"],
       group=T("Observer"), min=1.0, max=179.0, live=True,
       help=T("{i1}°: how EHT compared the images of M87* for a > 0 ({i2}° for a ≤ 0; EHT 2019 Paper V, Fig. 8): the "
              "jet towards us at {i2}°, the hole's spin away from us; {i3}°: the disk edge-on", i1=163, i2=17, i3=90)),
    _p("emitter", T("Gas of the disk"), "select", "cunningham", group=G_DISK, live=True,
       options=[("cunningham", T("Keplerian outside the ISCO, falling in down to the horizon (Cunningham)")),
                ("keplerian", T("Keplerian outside the ISCO only (dark inside)"))]),
    _p("retro", T("The disk rotates against the hole"), "bool", False, group=G_DISK, live=True),
    _p("profile", T("Emission of the disk J(r) (a source model)"), "select", "r2", group=G_DISK, live=True,
       options=PROFILES),
    _p("res", T("Screen resolution"), "select", "m", group=G_SCREEN, live=True,
       options=[("s", "128 × 128"), ("m", "192 × 192"), ("l", "256 × 256")]),
    _p("half", T("Half-width of the screen, M"), "float", 9.0, group=G_SCREEN, min=4.0, max=30.0, live=True),
    _p("n_rays", T("Rays in 3-D"), "int", 14, group=G_SCREEN, min=0, max=40, live=True),
], presets={
    "m87": {"label": T("M87*: a = {a}, inclination {i}° (as EHT for a > 0), Cunningham's disk: the shadow, the lensing "
                       "ring, the photon ring", a=0.9, i=163),
            "params": {}},
    "edge_on": {"label": T("The disk edge-on (θ = {i}°), a = {a}: the shadow is flattened, the rings are asymmetric",
                           i=90, a=0.99),
                "params": {"chi": 0.99, "incl": 90.0}},
    "schwarzschild": {"label": T("No rotation (a = 0): the shadow is a circle of radius √27 M"),
                      "params": {"chi": 0.0, "incl": 60.0}},
    "ring": {"label": T("A narrow ring of gas at {r} M: its images n = 0, 1, 2 are seen", r=6),
             "params": {"profile": "ring", "incl": 60.0}},
    "sgra": {"label": T("Sgr A*: a = {a}, inclination {i}°, compared with EHT 2022", a=0.5, i=30),
             "params": {"chi": 0.5, "incl": 30.0, "target": "sgra"}},
    "whatif": {"label": T("What if: the Johannsen metric with α₁₃ = {v}, a larger shadow, compared with EHT", v=3),
               "params": {"metric": "jp", "a13": 3.0, "chi": 0.0, "incl": 17.0}},
})


def _surface(r_of_theta, chi, nth=36, nph=48):
    """A surface r = r(theta) of revolution about the spin axis in the drawing coordinates (kerr_null.cartesian)."""
    th = np.linspace(0.0, math.pi, nth)
    ph = np.linspace(0.0, 2.0 * math.pi, nph, endpoint=False)
    Th, P = np.meshgrid(th, ph, indexing="ij")
    x, y, z = KN.cartesian(r_of_theta(Th), Th, P, chi)
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
                raise Refusal(T("the Johannsen metric is available here only for a < M"),
                              hint=T("choose a spin a/M below 1"))
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
                raise Refusal(T("at the inclination θ = {i}° no spherical photon orbit of this metric is visible: "
                                "there is no edge of the shadow", i=float(self.live["incl"])),
                              hint=T("choose another inclination θ of the observer"),
                              detail=english(text_of(e))) from e
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
                   "label": T("observer: θ = {i:.4g}°", i=float(self.live["incl"])),
                   "layer": T("Observer (far away, in this direction)"), "color": "#7fb7ff"})
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
                   "label": T("Disk: emission J(r) from {r0:.4g} to {r1} M (a source model)", r0=r_in, r1=R_OUT)},
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
                   "label": T("Rays to the observer (computed): red, captured; yellow, near the critical curve; blue, "
                              "farther out")},
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
            s = english(text_of(e))
            why = (T("there is no circular photon orbit between the horizon and {r} M", r=60) if "photon orbit" in s
                   else T("there are no stable circular orbits even at {r} M", r=200) if "stable" in s else
                   T("the inner edge of the stable circular orbits (ISCO) is not found up to {r} M", r=200))
            self._msg({"type": "notice", "t": self.t, "text": T(
                "The equatorial circular orbits of this metric are not drawn: {why}. The edge of the shadow and its "
                "comparison with EHT are computed", why=why)})
            return None
        return {"ph_pro": o["photon_pro"], "ph_retro": o["photon_retro"], "isco_pro": o["isco_pro"],
                "isco_retro": o["isco_retro"], "isco_kind": o.get("isco_kind_pro", "stability")}

    def _static_scene(self):
        """The hole: horizon, ergosphere, the equatorial photon orbits and the ISCO (of this world's metric)."""
        rp = self.r_plus
        pos, idx = _surface(lambda th: np.full_like(th, rp), self.chi)
        self._msg({"type": "mesh", "t": self.t, "id": "horizon", "count": int(len(pos)), "opacity": 1.0,
                   "label": T("Horizon r₊ = {r:.6g} M", r=rp)},
                  {"pos": pos, "idx": idx, "rgb": np.tile(np.array([[12, 12, 16]], np.uint8), (len(pos), 1))})
        if self.dev is None:
            pos, idx = _surface(lambda th: 1.0 + np.sqrt(np.maximum(1.0 - self.chi ** 2 * np.cos(th) ** 2, 0.0)),
                                self.chi)
            ergo = T("Ergosphere (inside it nothing can stay at rest)")
        else:
            pos, idx = _surface(lambda th: JP.ergosurface(self.chi, self.dev, th), self.chi)
            ergo = T("Ergosphere of this metric: g_tt = 0, Δ = a²A₂² sin²θ (Johannsen 2013a, Eq. 69)")
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
        if self.dev is None:
            label = T("Equatorial circular orbits: photon orbits (prograde and retrograde) and the ISCO")
        else:
            label = T("Equatorial circular orbits of this metric (computed numerically): photon orbits (prograde and "
                      "retrograde) and the ISCO")
        if o.get("isco_kind") == "existence":  # P6: a band without circular geodesics bounds the stable orbits
            label = join([label, T("ISCO = {r:.4g} M is the edge of the region where circular orbits exist at all "
                                   "(inside it, down to the photon orbit, Ω² < 0: gravity repels there)",
                                   r=o["isco_pro"])])
        self._msg({"type": "lines", "t": self.t, "id": "orbits", "label": label},
                  {"pts": np.concatenate(pts).astype(np.float32).reshape(-1),
                   "rgb": np.concatenate(col).astype(np.float32).reshape(-1)})

    # --- checks ------------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group=None):
        group = T("Shadow") if group is None else group
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
        self._check("edge", T("Edge of the shadow: where a ray stops being captured, against Bardeen's curve (rel.)"),
                    float(err[k] / rc[k]), 0.0, tol=float(tol[k] / rc[k]), ok=bool(np.all(err <= tol)),
                    note=T("8 directions on the screen: the boundary of capture found by bisection on the tracer "
                           "itself (its outcome for each ray); the curve is the closed form of the spherical photon "
                           "orbits; the tolerance is derived for each direction: the round-off error of "
                           "d₃₄ = (r₄ − r₃)²/4, whose sign decides the outcome, divided by its slope, plus the accuracy "
                           "of the curve's formula and the last step of the bisection"))
        if self.chi == 0.0:
            b = math.sqrt(27.0)
            e = np.abs(edge - b) + 0.5 * (hi - lo)
            kk = int(np.argmax(e / tol))
            self._check("schw", T("No rotation: the tracer's edge of the shadow against √27 M"), float(np.max(edge)), b,
                        "M", tol=float(tol[kk] / b), ok=bool(np.all(e <= tol)),
                        note=T("the edge found from the outcome of rays in 8 directions, against the circle of radius "
                               "√27 M (Synge 1966); the tolerance is the same derived one as the shadow edge's"))
        # photon rings: the n-th image of a ring of gas approaches the curve by e^-gamma per half-orbit
        try:
            r_src = max(8.0, self._r_in() + 1.0)
            rhos = [KS.ring_image(self.chi, th, r_src, 0.0, n)[0] for n in (1, 2, 3)]
            rho_c, r_b = KN.critical_radius_at(self.chi, th, 0.0)
            eg = float(np.exp(-KN.lyapunov(np.array([r_b]), self.chi)[0]))
            ratio = (rhos[2] - rho_c) / (rhos[1] - rho_c)
            ratio1 = (rhos[1] - rho_c) / (rhos[0] - rho_c)
            tl = 4.0 * abs(ratio1 - eg) * eg + 1e-6
            self._check("lyapunov", T("Photon ring: the demagnification of the images n = 2 → 3 against e^(−γ)"), ratio,
                        eg, tol=max(tl / eg, 1e-6), ok=abs(ratio - eg) <= tl,
                        note=T("images of a ring of gas r = {r:.3g} M in the direction α > 0: the distance to the curve "
                               "decreases e^γ times per half-period in θ (Johnson et al. 2020), γ = {g:.6g} at the "
                               "orbit r = {rb:.6g} M; the ratio n = 1 → 2 = {q:.6g}; tolerance: 4 e^(−γ)·|the "
                               "deviation n = 1 → 2| (the corrections decrease as e^(−γ) with each order)",
                               r=r_src, g=-math.log(eg), rb=r_b, q=ratio1))
        except ValueError as e:
            self._check("lyapunov", T("Photon ring: the demagnification of the images"), None, None, info=True,
                        note=T("not computed: {why}", why=text_of(e)))
        # the size on the tracer's edge (128 directions) against the closed form, then against EHT
        sz = KS.shadow_size(self.chi, th)
        ok = abs(sz["delta"] - sz["delta_closed"]) <= sz["delta_tol"]
        ref = sz["delta_closed"]
        self._check("size", T("Size of the shadow δ from the tracer's edge against the closed form"), sz["delta"], ref,
                    tol=sz["delta_tol"] / abs(ref) if ref else sz["delta_tol"], ok=ok,
                    note=T("the median diameter over 128 directions from the midpoint between the extreme α (EHT 2022, "
                           "Sgr A* Paper VI, Eq. 14: δ = d/(6√3 M) − 1): from the tracer's edge {d:.12g} M, from "
                           "Bardeen's curve {dc:.12g} M; tolerance {tol:.2g}: the derived tolerances of the edge",
                           d=sz["median_diameter"], dc=sz["median_diameter_closed"], tol=sz["delta_tol"]))
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
        size_note = T("the size of this world's shadow by the definition of EHT 2022 (Sgr A* Paper VI, Eq. 14): "
                      "δ = {d:.6g}, the median diameter {dm:.6g} M from the edge the tracer found", d=d,
                      dm=sz["median_diameter"])
        if tgt == "m87":
            s = D.EHT_M87_DELTA_STELLAR[1]
            self._check("eht", T("M87*: the deviation of the shadow's size from Kerr's (the same a and θ) against EHT "
                                 "2019 ±{s:.2f}", s=s),
                        0.0, 0.0, tol=s, ok=True, info=True, group=T("Comparison with EHT"),
                        note=T("EHT 2019 (Paper VI, Sec. 9.5, Eq. 31) measured δ = θg(ring)/θg(mass from stars) − 1 = "
                               "{d0} ± {s}, having calibrated the ring on Kerr models: every Kerr hole has δ = 0 there, "
                               "and this world (Kerr) agrees with it; ±{s} as in Psaltis et al. 2020. {size}; the "
                               "angular diameter of the shadow at θg = {thg} µas is {ang:.4g} µas (the EHT ring "
                               "{ring} ± {ring_e} µas is a ring of emission, not the shadow)",
                               d0=D.EHT_M87_DELTA_STELLAR[0], s=s, size=size_note, thg=th_g,
                               ang=sz["median_diameter"] * th_g, ring=42, ring_e=3))
        elif tgt == "sgra":
            lo, hi = (v - 1.0 for v in D.EHT_SGRA_SHADOW_RADIUS_VLTI)
            v, up, dn = D.EHT_SGRA_DELTA_VLTI
            self._check("eht", T("Sgr A*: δ of this world against EHT 2022 (VLTI) {v:+.2f} +{up}/−{dn}", v=v, up=up,
                                 dn=dn), d, v,
                        tol=max(up, dn), ok=lo <= d <= hi, info=True, group=T("Comparison with EHT"),
                        note=T("{size}; the 68 % interval [{lo:+.2f}, {hi:+.2f}] (EHT 2022 Paper VI, Eq. 13, VLTI)",
                               size=size_note, lo=lo, hi=hi))

    def _eht_whatif(self):
        """A "what if" world against EHT: the size of the deviating metric's shadow edge (computed from its photon
        orbits) and of the Kerr hole with the same spin and inclination, in the same convention."""
        tgt = self.params["target"]
        th = self.theta_o
        d_jp = JP.delta(self.chi, th, self.dev)
        d_k = JP.delta(self.chi, th, None)
        if tgt == "m87":
            s = D.EHT_M87_DELTA_STELLAR[1]
            self._check("eht", T("M87*: the deviation of the shadow's size from Kerr's δ − δ_Kerr against EHT 2019 "
                                 "±{s:.2f}", s=s),
                        d_jp - d_k, 0.0, tol=s, ok=abs(d_jp - d_k) <= s, info=True, group=T("Comparison with EHT"),
                        note=T("EHT 2019 (Paper VI, Eq. 31) measured θg from the ring calibrated on Kerr against θg "
                               "from the stars: the deviation of the size from Kerr's within ±{s} (Psaltis et al. "
                               "2020); δ of this metric {d:.6g}, of Kerr {dk:.6g} (the median diameter, EHT 2022 Paper "
                               "VI, Eq. 14)", s=s, d=d_jp, dk=d_k))
        elif tgt == "sgra":
            lo, hi = (v - 1.0 for v in D.EHT_SGRA_SHADOW_RADIUS_VLTI)
            v, up, dn = D.EHT_SGRA_DELTA_VLTI
            self._check("eht", T("Sgr A*: δ of this metric against EHT 2022 (VLTI) {v:+.2f} +{up}/−{dn}", v=v, up=up,
                                 dn=dn), d_jp, v,
                        tol=max(up, dn), ok=lo <= d_jp <= hi, info=True, group=T("Comparison with EHT"),
                        note=T("δ = d/(6√3 M) − 1, the median diameter of this metric's shadow edge; the 68 % interval "
                               "[{lo:+.2f}, {hi:+.2f}] (EHT 2022 Paper VI, Eq. 13, VLTI)", lo=lo, hi=hi))
        self._check("eht_kerr", T("The same hole by Kerr: δ"), d_k, None, info=True, group=T("Comparison with EHT"),
                    note=T("the deviation of the metric changes δ by {dd:+.4g}", dd=d_jp - d_k))

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
        self._check("pixels", T("Shadow in the image: the captured pixels against the inside of the curve"),
                    bad, 0, T("px"), tol=0, ok=bad == 0,
                    note=T("{k:d} of {n:d} pixels are farther than {margin:.2g} M from the curve (as far as the polyline "
                           "of {pts:d} points can be from the curve itself); mismatches: {bad:d}",
                           k=int(np.sum(far)), n=int(far.size), margin=margin, pts=721, bad=bad))

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
        self._check("gpu", T("GPU against CPU: the redshift of the middle row"), worst, 0.0,
                    tol=float(tol[k]) if cmp.any() else 0.0,
                    ok=fate_ok and same and r_ok and bool(np.all(err[cmp] <= tol[cmp])), group=T("Where it was computed"),
                    note=T("the same code on NumPy and CuPy in fp64: the CUDA functions differ from glibc by ≤ 2 ulp; "
                           "the radii of the crossings within 128 u × the sensitivity (|α ∂r/∂α| + |β ∂r/∂β| + |r|, "
                           "central differences on the CPU), the redshift within its consequence for g plus the "
                           "round-off of the formula itself (at the ray's turning point and inside the ISCO, roots of "
                           "cancelling differences); {n:d} values farther than {d} M from the curve compared, the "
                           "outcome for every pixel of the row", n=int(cmp.sum()), d=0.05))

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
            raise ValueError(join(errors))
        old = self.live
        self.live = merged
        try:
            self._new_image()
        except Exception:
            self.live = old
            raise
        self._scan()
        gas = {"cunningham": T("Cunningham's disk"), "keplerian": T("a Keplerian disk")}[merged["emitter"]]
        if merged["retro"]:
            gas = T("{gas}, counter-rotating", gas=gas)
        return T("observer θ = {i:.4g}°; gas: {gas}; screen {n:d}², ±{h:.4g} M: a new image", i=float(merged["incl"]),
                 gas=gas, n=RES[merged["res"]], h=float(merged["half"]))

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
        views = [["iso", T("Iso"), T("Isometric (F)"), [0.55, -0.7, 0.45]],
                 ["obs", T("Observer"), T("From the observer's direction: as on the screen, the spin axis up"),
                  {"along": "observer"}],
                 ["side", T("Edge-on"), T("From the side: the disk edge-on, the spin axis up"), [0.0, -1.0, 0.0]],
                 ["pole", T("From the pole"), T("From the spin axis (above): the disk face-on"), [0.0, 0.0, 1.0]]]
        approximations = [T("the emitter is a thin equatorial disk with the emission J(r) (a source model, not a law)"),
                          T("geometric optics, the screen at infinity, no absorption")]
        if modified:
            approximations.append(T("the Johannsen metric: the edge of the shadow is computed (the photon orbits), "
                                    "the image of the disk is not"))
        return {
            "title": T("The shadow of a Kerr black hole: a = {a:.4g}", a=self.chi) if not modified else T(
                "What if the hole is not Kerr: the shadow of the Johannsen metric, a = {a:.4g}", a=self.chi),
            "text": T("Every pixel of a distant observer's screen is a photon traced back in closed form: captured by "
                      "the hole (the shadow) or come from far away, and where it crossed the plane of the disk, the "
                      "n-th crossing along the ray traced back: at a moderate inclination n = 0 is the direct image, "
                      "n = 1 the lensing ring, n = 2 the photon ring; nearly edge-on the lower face of the disk is "
                      "seen directly as n = 1. The brightness is the sum of g⁴J(r) over the crossings (a source "
                      "model). When the image is complete, the tracer's edge of the shadow is verified against "
                      "Bardeen's formula, the rings against their exponential demagnification, the size against EHT."),
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
            "units": {"t": T("M (G = c = 1): the world's time; the image is stationary, its rows are computed as the "
                             "time goes on"),
                      "x": "M"},
        }, {}


_JP_PARAMS = (("a13", "alpha13", "α₁₃"), ("a22", "alpha22", "α₂₂"), ("a12", "alpha12", "α₁₂"))


def _margin(key, v):
    """A regularity condition of the Johannsen metric that fails (Johannsen 2013a), in the owner's terms."""
    if key == "A1":
        return T("A₁ ≤ 0 (down to {v:.3g})", v=v)
    if key == "A2":
        return T("A₂ ≤ 0 (down to {v:.3g})", v=v)
    if key == "det_eq72":
        return T("det g vanishes (Eq. 72)")
    return T("closed timelike curves (Eq. 76)")


def _either(items):
    """Alternatives as one text: «a or b or c»."""
    out = items[0]
    for x in items[1:]:
        out = T("{a} or {b}", a=out, b=x)
    return out


def _jp_admissible(chi, p):
    """Refuse, in the owner's terms, a Johannsen metric whose shadow edge the engine cannot compute (review UX-params
    P6): not regular outside the horizon (Johannsen 2013a Eqs. 72, 76-78), or its photon orbits not one band. The
    refusal names what fails and, for each deviation with the others as they are, the values the world takes
    (``johannsen_metric.admissible_intervals`` over the slider's range)."""
    dev = JP.Deviation(p["a12"], p["a13"], p["a22"])
    why = JP.shadow_computable(chi, dev)
    if why is None:
        return
    now = join([T("{name} = {v:.3g}", name=lab, v=float(p[pid])) for pid, _, lab in _JP_PARAMS], ", ")
    if why == "regular":
        m = JP.regularity_margins(chi, dev)
        bad = join([_margin(k, v) for k, v in m.items() if not v > 0.0], "; ")
        head = T("the Johannsen metric at a = {a} and {now} is not regular outside the horizon: {bad} (Johannsen 2013a, "
                 "Eqs. 72, 76–78): no such metric exists as a black hole, and no shadow is built.", a=chi, now=now,
                 bad=bad)
    else:
        head = T("the photon orbits of the Johannsen metric at a = {a} and {now} do not form one band between the "
                 "horizon and {r} M (there are several or none): the edge of the shadow cannot be computed here.",
                 a=chi, now=now, r=12)
    tips = []
    for pid, key, lab in _JP_PARAMS:
        par = SCHEMA.by_id[pid]
        others = {k: p[q] for q, k, _ in _JP_PARAMS if q != pid}
        iv = JP.admissible_intervals(chi, key, others, par.min, par.max)
        if not iv:
            tips.append(T("{name}: no value from {lo:.3g} to {hi:.3g} helps", name=lab, lo=par.min, hi=par.max))
        else:
            tips.append(T("{name}: {ranges}", name=lab,
                          ranges=_either([T("from {lo:.3g} to {hi:.3g}", lo=a, hi=b) for a, b in iv])))
    if chi > 0:
        hint = T("the world is built if one value is changed (the others as now): {tips}; at a smaller spin a the "
                 "intervals are usually wider", tips=join(tips, "; "))
    else:
        hint = T("the world is built if one value is changed (the others as now): {tips}", tips=join(tips, "; "))
    raise Refusal(head, hint=hint)


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
    "title": T("The shadow of a Kerr black hole and its photon rings"),
    "summary": T("What a distant observer sees of a rotating black hole with a disk of gas: the shadow, the lensing "
                 "ring and the photon ring, every pixel a ray traced back in closed form; the edge of the shadow "
                 "against Bardeen's formula, the rings' demagnification against the Lyapunov exponent, the size against "
                 "EHT; what if the metric is not Kerr."),
    "purpose": T("Show where the shadow and the rings in the EHT images come from, how their shape depends on the spin "
                 "and the inclination, and how one can test that the hole is a Kerr one."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
