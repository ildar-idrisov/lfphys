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
from lfphys.i18n import T, join
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


G_BEAM, G_HOLO, G_ROT = T("Beam"), T("Hologram"), T("Rotation")
SCHEMA = Schema([
    _p("gen", T("Source of the vortex"), "select", "mode", group=G_BEAM,
       options=[("mode", T("a Laguerre–Gauss mode LG_pl (the waist at z = 0)")),
                ("spp", T("a Gaussian beam behind a spiral phase plate (z = 0)")),
                ("fork", T("a Gaussian beam on a “fork” hologram (z = 0)"))]),
    _p("l", T("Topological charge l"), "int", 3, group=G_BEAM, min=-6, max=6),
    _p("p", T("Radial index p"), "int", 0, group=G_BEAM, min=0, max=3, show_if={"gen": ["mode"]}),
    _p("w0", T("Waist w0, µm"), "float", 1.5, group=G_BEAM, min=0.3, max=6.0,
       help=T("The width of the source's spectrum (of the LG mode or of the Gaussian beam behind the plate). The exact "
              "model takes only the propagating waves (q ≤ k) of the spectrum: at w0 ≲ λ it is no longer the waist "
              "of the named source, and the world is marked; when more than {p} % of the source's power is lost, it "
              "is not built.", p=10)),
    _p("lam", T("Wavelength λ, µm"), "float", 1.0, group=G_BEAM, min=0.4, max=1.6),
    _p("pol", T("Polarisation"), "select", "+1", group=G_BEAM, show_if=BEAMS,
       options=[("+1", T("circular, σ = +1")), ("-1", T("circular, σ = −1")), ("lin", T("linear (x)"))]),
    _p("model", T("Beam model"), "select", "exact", group=G_BEAM, show_if=BEAMS,
       options=[("exact", T("exact: a vector solution of Maxwell's equations")),
                ("paraxial", T("paraxial (an approximation): a mode × a uniform polarisation"))]),
    _p("zspan", T("Length of the region, in z_R"), "float", 1.5, group=G_BEAM, min=0.4, max=3.0, show_if=BEAMS),
    _p("period", T("Hologram period Λ, µm"), "float", 2.5, group=G_HOLO, min=1.0, max=8.0,
       show_if={"gen": ["fork"]}),
    _p("kind", T("Hologram"), "select", "binary", group=G_HOLO, show_if={"gen": ["fork"]},
       options=[("amplitude", T("amplitude (1 + cos)/2")), ("binary", T("binary amplitude")),
                ("blazed", T("blazed phase (all into the 1st order)"))]),
    _p("rot", T("Rotating element"), "select", "disc", group=G_ROT, show_if=BEAMS,
       options=[("disc", T("a rough disc, the detector behind a ±l mode filter (Lavery 2013)")),
                ("dove", T("a Dove prism in an arm of an interferometer (Courtial 1998)")), ("none", T("none"))]),
    _p("f_rot", T("Rotation frequency f, Hz"), "float", 5.0, group=G_ROT, min=0.0, max=40.0, live=True,
       show_if=ROTS, help=T("Changes on the fly: a new series of measurements starts at this moment.")),
    _p("t_show", T("Optical phase on the screen: the period, ms of the world's time"), "float", 400.0,
       group=T("Time"), min=40.0, max=4000.0,
       help=T("Light at a frequency of ~{f} Hz is shown slowed down: one optical period takes this much world time.",
              f=1e15)),
], presets={
    "lg3": {"label": T("LG₀³, σ = +1: three helical fronts, the exact model, a rotating disc"), "params": {}},
    "tight": {"label": T("Tight focusing: l = 1, σ = −1, w0 = {w} λ: the longitudinal field and the spin-orbit "
                         "splitting", w=0.6),
              "params": {"l": 1, "pol": "-1", "w0": 0.6, "zspan": 1.5, "rot": "none"}},
    "tight_par": {"label": T("The same in the paraxial model (an approximation): what it does not see"),
                  "params": {"l": 1, "pol": "-1", "w0": 0.6, "zspan": 1.5, "rot": "none", "model": "paraxial"}},
    "lg_p2": {"label": T("LG₂¹: three rings, fronts with phase jumps at the nodes"),
              "params": {"l": 1, "p": 2, "w0": 1.2}},
    "spp": {"label": T("Spiral phase plate, l = {l}: charge {l}, not a single LG mode; the scalar field's orbital "
                       "angular momentum is {l}ħ per photon, the vector field's L_z = l + σ(1 − ⟨cos θ⟩)", l=2),
            "params": {"gen": "spp", "l": 2, "w0": 1.5}},
    "dove": {"label": T("A Dove prism rotates: a frequency shift 2|l|f for the beam l = {l}", l=2),
             "params": {"l": 2, "rot": "dove"}},
    "l0": {"label": T("Control: a Gaussian beam without a vortex (l = 0): no beat"), "params": {"l": 0}},
    "lin": {"label": T("Linear polarisation, l = 1: J_z = l on average, zero spin"), "params": {"l": 1, "pol": "lin"}},
    "fork": {"label": T("A “fork” hologram, l = 1: the order m carries the charge m·l"),
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
            raise Refusal(T("the hologram period Λ = {P} µm is not longer than the wavelength λ = {lam} µm: the first "
                            "order does not propagate (sin θ₁ = λ/Λ ≥ 1)", P=period, lam=self.lam),
                          hint=T("choose a period Λ longer than {lam} µm (or λ shorter than {P} µm)", lam=self.lam,
                                 P=period))
        # review UX-params P11: the default waist (1.5 µm, the LG modes') is too narrow for any Λ of the form, so
        # "Fork hologram" alone was refused, with advice that could not be followed; the world now takes the
        # smallest waist that works (the preset "fork": 4 µm at Λ = 2.5) and says so
        fit = self._fork_waist(w_ask, period)
        if fit is None:
            ok = [pp for pp in np.arange(round(period, 2) - 0.01, self.lam, -0.01) if self._fork_waist(w_ask, pp)]
            s = self.lam / period
            ang = math.degrees(math.asin(min(s, 1.0)))
            raise Refusal(T("with the period Λ = {P} µm at λ = {lam} µm the orders of the hologram do not separate at "
                            "any waist up to {wmax} µm (the first order's angle {ang:.3g}° is too small for the beam's "
                            "divergence, or the region does not fit into the grid)", P=period, lam=self.lam,
                            wmax=SCHEMA.by_id["w0"].max, ang=ang),
                          hint=T("decrease the period Λ to {P:.3g} µm or less", P=float(ok[0])) if ok else
                          T("choose another wavelength"))
        w0, z_end = fit
        fork = A.Fork(self.l, w0, self.lam, period, p["kind"], z_end)
        if w0 != w_ask:
            p["w0"] = w0
            tan = math.tan(math.asin(self.lam / period))
            self._msg({"type": "notice", "t": 0.0, "text": T(
                "Fork hologram: at the waist {w:.6g} µm the beam spreads faster than the orders separate (the first "
                "order's angle {a1:.3g}° at Λ = {P} µm, the divergence λ/(πw0) = {div:.3g}°): the orders would not "
                "separate. The world took w0 = {w0:.6g} µm, the smallest at which they separate with a margin of "
                "{m} %: the beam is wider, the region longer (up to z = {z:.3g} µm). A smaller period Λ allows a "
                "narrower beam.", w=w_ask, a1=math.degrees(math.atan(tan)), P=period,
                div=math.degrees(self.lam / (math.pi * w_ask)), w0=w0, m=20, z=z_end)})
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
        objects, layers = [], [{"id": "light", "label": T("Intensity |E|² (a volume, computed)"), "kind": "volume",
                                "visible": True, "look": {"density": 0.9, "threshold": 0.03}}]
        W = hi[0] - lo[0]
        if self.fork is None and self.params["gen"] == "mode":
            objects.append({"id": "waist", "label": T("Beam waist (z = 0): w0"), "kind": "disk", "z": 0.0,
                            "w": float(self.params["w0"]), "size": [W, W], "visible": False})
        if self.det is not None:
            L = hi[2] - lo[2]
            objects.append({"id": "detector", "label": T("Detector (single-mode, far zone)") if self.rot == "disc"
                            else T("Detector: both arms of the interferometer"), "kind": "box",
                            "center": [0.0, 0.0, hi[2] - 0.03 * L], "size": [0.12 * W, 0.12 * W, 0.02 * L],
                            "color": "#9fe870", "opacity": 0.8, "text": T("detector"), "visible": True})
        return {"box": [list(lo), list(hi)], "units": T("µm"), "objects": objects, "layers": layers,
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
                   "note": T("|E|² / peak on a grid of {n:d}³ (not computed behind the rotating element); the exact "
                             "values are in the slices", n=int(V.shape[0]))},
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
            self._msg({"type": "mesh", "t": self.t, "id": "hologram", "label": T("Fork hologram (z = 0)"),
                       "count": int(len(pos)), "base": "lab", "opacity": 0.95},
                      {"pos": pos.astype(np.float32), "idx": np.array(idx, np.uint32),
                       "rgb": np.clip(rgb, 0, 255).astype(np.uint8).reshape(-1, 3)})
            return
        bm = self.beam
        if self.params["gen"] == "spp" and self.l:
            h_max = abs(self.l) * self.lam / 0.5  # the plate's step for n = 1.5
            pos, idx, rgb = A.spp_mesh(self.l, self.lam, 0.9 * bm.half, exaggerate=0.04 * (bm.z1 - bm.z0) / h_max)
            self._msg({"type": "mesh", "t": self.t, "id": "plate", "base": "lab",
                       "label": T("Spiral phase plate (z = 0; the thickness exaggerated)"), "count": int(len(pos)),
                       "opacity": 0.75}, {"pos": pos, "idx": idx, "rgb": rgb})
        if self.rot == "disc":
            pos, idx, rgb = A.disc_mesh(min(self.det.r_max, 0.95 * bm.half), 0.01 * (bm.z1 - bm.z0),
                                        rgb_fn=A.surface_rgb(self.det.surface))
            self._msg({"type": "mesh", "t": self.t, "id": "rotor", "base": "rest", "label":
                       T("Rotating rough disc"), "count": int(len(pos)), "opacity": 0.85},
                      {"pos": pos, "idx": idx, "rgb": rgb})
        elif self.rot == "dove":
            h = min(2 * self.det.X.max(), 1.8 * bm.half)
            pos, idx, rgb = A.prism_mesh(0.08 * (bm.z1 - bm.z0), h, 0.8 * h)
            self._msg({"type": "mesh", "t": self.t, "id": "rotor", "base": "rest", "label": T("Rotating Dove prism"),
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
                       "label": T("Energy flow lines (the Poynting vector, computed)")}, {"pts": pts, "rgb": rgb})
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
                   "label": T("Lines of the orbital (canonical) current p_o"), "visible": bm.model != "exact"},
                  {"pts": pts, "rgb": rgb})
        self.flow_meta = (starts, zs, r_pk)

    def _reveal(self, k):
        omega_t = 2 * math.pi * k / NB
        pos, idx, rgb = A.helix_mesh(self.beam, self.helix_grid, omega_t)
        a, b = A.helix_region(self.beam, self.z_end)
        self._msg({"type": "helix", "t": self.t, "bin": k, "nb": NB, "t_bin": k * self.T_show / NB,
                   "count": int(len(pos)), "region": [a, b],
                   "label": T("Surfaces of equal phase arg ψ = ωt (the stretch z = {a:.3g}…{b:.3g} µm)", a=a, b=b)},
                  {"pos": pos, "idx": idx, "rgb": rgb})

    # --- checks -----------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group=None):
        group = G_BEAM if group is None else group
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
        self._check("table", T("Field table against the direct calculation ({n1:d} points + {n2:d} on the bright ring)",
                               n1=24, n2=18), self.table_err, 0.0, "",
                    tol=1e-4, ok=self.table_err <= 1e-4,
                    note=T("bicubic splines of the envelopes on the table r × z against the direct quadrature of the "
                           "vector beam; fraction of the peak |E|") if bm.model == "exact" else
                    T("bicubic splines of the envelopes on the table r × z against the closed form / the Fresnel "
                      "integral; fraction of the peak |E|"))
        if bm.model == "exact":
            # what the propagating beam keeps of the named source (review B8-beams, O2)
            if bm.gen == "mode":
                note = join([T("from the source's spectrum (Parseval for the Hankel transform); {d:.2e} of the power of "
                               "the LG waist does not propagate: the field at z = 0 differs from the named one by "
                               "{n:.2g} in the L2 norm", d=bm.dropped, n=math.sqrt(bm.dropped)),
                             T("the world is marked") if bm.dropped >= A.DROP_LABEL else "",
                             T("above {p:.3g} % the world is not built", p=100 * A.DROP_REFUSE)])
            else:
                note = T("from the spectrum of the field behind the plate (Parseval): {d:.2e} of its power at z = 0 is "
                         "in evanescent waves of the near field of the singular point; at the distance λ from the "
                         "plate they are {e1:.2e}, at 2λ {e2:.2e}; the beam is the exact far field", d=bm.dropped,
                         e1=bm.ev_near[1], e2=bm.ev_near[2])
            self._check("kept", T("Fraction of the source's power the beam carries (propagating waves, q ≤ k)"),
                        bm.kept, 1.0, "", info=True, note=note)
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
        G_AM = T("Angular momentum")
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
            why = (T("the WINDOW DOES NOT HOLD the light at large angles (the fraction of the energy outside the window "
                     "{m:.1e}): a comparison for information", m=miss) if wide else "")
            am.update({"L": m["L"], "S": m["S"], "J": m["J"], "flux_J": m["flux_J"], "J_poynting": m["J_poynting_per_photon"],
                       "S_flux": m["flux_S"], "L_flux": m["flux_L"], "S_flux_ref": ref["S_flux"],
                       "L_flux_ref": ref["L_flux"], "J_poynting_ref": ref["J_poynting"],
                       "L_ref": ref["L"], "S_ref": ref["S"], "J_ref": ref["J"], "cos": ref["cos_mean"], "miss": miss})
            win = T("Berry densities on a grid {n:d}² in the window ±{h:.3g} µm; tolerance: 4(|l| + 2) × the fraction "
                    "of the energy outside the window ({m:.1e})", n=n, h=bm.am_half, m=miss)
            for key, lab in (("J", T("Total angular momentum J_z = L_z + S_z per photon per unit length (measured from "
                                     "the field on the plane z = {z:.3g} µm)", z=z_am)),
                             ("S", T("Spin S_z per photon per unit length (the canonical split, Bliokh et al. 2010; "
                                     "measured from the field on the plane z = {z:.3g} µm)", z=z_am)),
                             ("L", T("Orbital angular momentum L_z per photon per unit length (the canonical split; "
                                     "measured from the field on the plane z = {z:.3g} µm)", z=z_am))):
                self._check(f"am_{key}", lab, m[key], ref[key],
                            "ħ", tol=tol, ok=None if wide else abs(m[key] - ref[key]) <= tol, info=wide,
                            group=G_AM,
                            note=join([T("the reference from the spectrum: J = l + σ, S = σ⟨cos θ⟩, "
                                         "L = l + σ(1 − ⟨cos θ⟩), ⟨cos θ⟩ = {c:.6f}; {win}; the split into spin and "
                                         "orbit depends on the definition: by the flux (Barnett) below",
                                         c=ref["cos_mean"], win=win), why]))
            self._check("am_flux", T("Angular momentum flux / energy flux × ω (the stress tensor)"), m["flux_J"],
                        ref["J"], "ħ", tol=tol, ok=None if wide else abs(m["flux_J"] - ref["J"]) <= tol, info=wide,
                        group=G_AM,
                        note=join([T("the angular momentum carried through the plane per photon crossing it: exactly "
                                     "l + σ"), why]))
            flux_notes = {
                "S_flux": T("another published definition: the spin flux σ/(2ω)∫|E_⊥|² dA (Monteiro et al. 2009, "
                            "eq. 33), measured as −∫Im(E_⊥*·H_⊥) dA/(2ω); reference σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩ (|spin| > "
                            "1, a shift from σ the other way than the canonical S_z's); only J_z = l + σ does not "
                            "depend on the definition"),
                "L_flux": T("the angular momentum flux (the stress tensor) minus Barnett's spin flux, per photon "
                            "through the plane; reference l + σ − σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩")}
            for key, mkey, lab in (("S_flux", "flux_S", T("Spin from the flux through the plane per photon (Barnett's "
                                                          "split)")),
                                   ("L_flux", "flux_L", T("Orbital part from the flux through the plane per photon (Barnett's "
                                                          "split)"))):
                self._check(f"am_{key}", lab, m[mkey], ref[key], "ħ", tol=tol,
                            ok=None if wide else abs(m[mkey] - ref[key]) <= tol, info=wide, group=G_AM,
                            note=join([flux_notes[key], win, why]))
            # the Poynting moment weights the r^-3/2 tails of a spectrum cut at q = k more than the densities above: in
            # a window of half-width R its error falls only as R^-1/2 (measured for the tight preset: 5.6e-3, 4.6e-3,
            # 4.0e-3, 3.2e-3 at R = 10, 15, 20, 30 lambda), so for such a spectrum it is a comparison, not a check
            pinfo = wide or bm.edge >= 1e-6
            self._check("am_poynting", T("Poynting angular momentum ∫(r × P)_z per photon per unit length"),
                        m["J_poynting_per_photon"], ref["J_poynting"], "ħ", tol=tol,
                        ok=None if pinfo else abs(m["J_poynting_per_photon"] - ref["J_poynting"]) <= tol, info=pinfo,
                        group=G_AM,
                        note=join([T("reference l + σ + (σ/2)⟨sin²θ/cos θ⟩ = {j:.7f}: it differs from L_z + S_z by "
                                     "½ d/dz ∫ r·S_⊥ dA; with one helicity S = σP/ω, and this term is the same on "
                                     "every plane z: a property of the angular spectrum, present in the waist too",
                                     j=ref["J_poynting"]),
                                   why,
                                   T("the spectrum is cut at q = k (at the edge {e:.2g} of the maximum): the field's "
                                     "tails ∝ r^−3/2, and in the window this moment converges only as R^−1/2: a "
                                     "comparison for information", e=bm.edge)
                                   if bm.edge >= 1e-6 and not wide else ""]))
            # the power through planes (exact field): the energy flux is the same at every z
            fl, misses = [], []
            for zz in (z_am, 0.5 * (z_am + self.z_end), self.z_end):
                Ez, Hz = bm.fields(X, Y, np.full_like(X, zz))
                fl.append(float(np.sum(B.poynting(Ez, Hz)[2])) * dx * dx)
                misses.append(max(0.0, 1.0 - float(np.sum(B.energy_density(Ez, Hz))) * dx * dx / W_spec))
            dev = (max(fl) - min(fl)) / max(fl)
            ptol = max(1e-6, 3 * max(misses))
            pwide = max(misses) > 1e-3
            self._check("power", T("Power through the planes z: one and the same"), dev, 0.0, "", tol=ptol,
                        ok=None if pwide else dev <= ptol, info=pwide,
                        note=join([T("P_z integrated over the window at three depths: {p1:.6g}, {p2:.6g}, {p3:.6g}; "
                                     "tolerance: 3 × the largest fraction of the energy outside the window ({m:.1e})",
                                     p1=fl[0], p2=fl[1], p3=fl[2], m=max(misses)),
                                   T("the light at large angles leaves the window: for information") if pwide else ""]))
            self._check("ez", T("Longitudinal field max|E_z| / max|E| (the plane z_c)"), Ezf, None, "", info=True,
                        note=T("there is none in the paraxial picture; first order, ~1/(k w0) = {v:.3g}",
                               v=1 / (bm.k * bm.w0)))
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
                self._check("parax", T("Paraxial mode against the exact field: the transverse components (the plane "
                                       "z_c)"),
                            d, None, "", info=True,
                            note=T("the largest difference of E_x, E_y, fraction of the peak; second order: it grows "
                                   "as (λ/w0)² = {v:.3g} (measured: ×4 at w0/2); the longitudinal field E_z, which the "
                                   "mode does not have, is first order (λ/w0): the “Longitudinal field” check",
                                   v=(bm.lam / bm.w0) ** 2))
        else:
            psi = bm.psi(X, Y, Z)
            Lm = B.scalar_oam_per_photon(psi, x, x)
            # the spin from the model's own field (review B8-beams, O9): u e_pol with H = -i sigma E per helicity
            E, H = bm.fields(X, Y, Z)
            Sm = bm.k * float(np.sum(B.spin_density(E, H, bm.k)[2])) / float(np.sum(B.energy_density(E, H)))
            am.update({"L": Lm, "S": Sm, "J": Lm + Sm, "L_ref": self.l, "S_ref": sb, "J_ref": self.l + sb})
            self._check("am_L", T("Orbital angular momentum L_z per photon per unit length (measured from the field on "
                                  "the plane z = {z:.3g} µm)", z=z_am), Lm,
                        self.l, "ħ", tol=2e-4, ok=abs(Lm - self.l) <= 2e-4, group=G_AM,
                        note=T("∫Im(ψ*∂_φψ) dA / ∫|ψ|² dA, spectral derivatives; in the paraxial model L_z = l"))
            self._check("am_S", T("Spin S_z per photon per unit length (from the model's field on the same plane)"), Sm,
                        sb, "ħ", tol=1e-9, ok=abs(Sm - sb) <= 1e-9, group=G_AM,
                        note=T("ω∫S_z dA / ∫w dA for u·e_σ (Berry densities): σ̄ at a uniform polarisation, as the "
                               "model is built; the exact model shows the splitting; tolerance: round-off"))
        self.am = am
        self._msg({"type": "am", "t": self.t, **{k: (float(v) if v is not None else None) for k, v in am.items()}})
        # 3. the topological charge on the plane z_c
        r_ring = A.ring_radius(bm, self.zc)
        q = B.charge_on_circle(lambda xx, yy: bm.psi(xx, yy, np.full_like(xx, self.zc)), 0.0, 0.0,
                               max(r_ring, 0.05 * bm.w0), 720)
        self._check("charge", T("Topological charge: the winding of the phase of ψ around the axis (z_c)"), q,
                    float(self.l), "", tol=1e-6, ok=abs(q - self.l) < 1e-6,
                    note=T("the sum of the phase jumps around the circle r = {r:.3g} µm (the brightest ring), {npts:d} "
                           "points; reference: l", r=r_ring, npts=720))
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
            label = (T("Gouy phase: arg ψ on the axis at z = {z:.3g} µm", z=zg) if rho == 0 else
                     T("Gouy phase: arg ψ on the ring r = w/√2 at z = {z:.3g} µm", z=zg))
            self._check("gouy", label, meas, ref, T("rad"), tol=1e-3, ok=None if exact else abs(d) < 1e-3, info=exact,
                        note=join([T("reference ρ²z/z_R − (2p+|l|+1)·arctan(z/z_R) (the paraxial formula); the "
                                     "difference {d:.2e} rad", d=d),
                                   T("the exact field has a non-paraxial correction") if exact else ""]))
        # 5. the equiphase sheets: |l| of them
        if self.helix_grid is not None:
            nsheets = A.sheet_count(self.helix_grid)
            self._check("sheets", T("Number of helical surfaces of equal phase"), nsheets, float(abs(self.l)), "",
                        tol=0.02, note=T("the mean number of crossings of arg ψ = const along the azimuth in the bright "
                                         "cells (z, r)"))
        # 6. the flow lines' twist: the paraxial orbital current against the closed-form spiral
        starts, zs, r_pk = self.flow_meta
        if self.params["gen"] == "mode":
            worst = 0.0
            for i in range(len(starts)):
                r0, a0 = math.hypot(*starts[i, :2]), math.atan2(starts[i, 1], starts[i, 0])
                xr, yr = PX.flow_line(self.l, r0, a0, zs, self.flowO[i, :, 2], bm.k, bm.w0)
                worst = max(worst, float(np.max(np.hypot(self.flowO[i, :, 0] - xr, self.flowO[i, :, 1] - yr))))
            par = bm.model != "exact"
            self._check("flow", T("Orbital current lines against the paraxial spiral φ(z)"), worst / bm.w0, 0.0, "",
                        tol=2e-3, ok=(worst / bm.w0 <= 2e-3) if par else None, info=not par,
                        note=T("the largest deviation, fraction of w0; the spiral: ρ = r/w(z) constant, "
                               "φ − φ0 = l/(2ρ²)·(ψ − ψ0)") if par else
                        T("the largest deviation, fraction of w0; the spiral: ρ = r/w(z) constant, "
                          "φ − φ0 = l/(2ρ²)·(ψ − ψ0); for the exact field the difference shows the non-paraxiality"))
        if self.flow_err is not None:
            self._check("flow_step", T("Energy flow lines (Poynting): the integration error"), self.flow_err, None, "",
                        info=True,
                        note=T("RK4, {steps:d} steps in z; two lines recomputed with half the step: the largest "
                               "difference, fraction of w0 (an estimate of the error of the lines in the scene)",
                               steps=FLOW_STEPS))

    def _checks_fork(self):
        f = self.fork
        orders, _ = f.orders(f.z1)
        for m, xm, q in orders:
            if TM.fork_order_coefficient(f.kind, m) == 0:
                continue
            self._check(f"order_{m}", T("Order m = {m:+d} (x = {x:.3g} µm): topological charge", m=int(m), x=xm),
                        float(q), float(m * f.l), "", tol=0.0, ok=q == m * f.l,
                        note=T("the sum of the charges of the grid cells in the circle of radius {f} w(z) around the "
                               "order (the winding along its boundary); reference m·l", f=1.3))
        sh = f.shares()
        self.fork_shares = sh
        for m in sh["orders"]:
            if m not in (-1, 0, 1):
                continue
            v, r = sh["meas"][m], sh["ref"][m]
            self._check(f"frac_{m}", T("Order m = {m:+d}: fraction of the propagating power", m=int(m)), v, r, "",
                        tol=sh["tol"], ok=abs(v - r) <= sh["tol"],
                        note=join([T("measured from the angular spectrum of the field behind the mask (the cell "
                                     "|k_x + mK| < K/2; by Parseval the same on every plane z); reference: the closed "
                                     "form of the same thin mask on the same grid in k (each order is a Gaussian beam "
                                     "behind a plate of charge m·l, shifted by −mK; their tails ∝ q^−2 overlap); "
                                     "without the overlap it would be |c_m|²/Σ|c_j|² = {ideal:.4f}; tolerance: 2 × the "
                                     "aliasing of the spectrum by the grid, estimated from the closed form with "
                                     "periodic images ({alias:.1e})", ideal=sh["ideal"][m], alias=sh["alias"]),
                                   T("the binary mask is a Fourier series up to the grid's band, |m| ≤ {mb:d}",
                                     mb=int(f.m_band)) if f.kind == "binary" else ""]))

    # --- slice planes (lfviz.planes3d hooks) -------------------------------------------------------------------------
    def _plane_points(self, pl, s_rng, t_rng, ns, nt):
        s = np.linspace(s_rng[0], s_rng[1], ns)
        t = np.linspace(t_rng[0], t_rng[1], nt)
        S, Tt = np.meshgrid(s, t)  # (nt, ns)
        o, u, v = (np.asarray(a, float) for a in (pl.origin, pl.u, pl.v))
        P = o[:, None, None] + u[:, None, None] * S + v[:, None, None] * Tt
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
        ver = ({"points": 0, "note": T("a coarse slice (auto-move), not verified")} if coarse
               else self._verify(P, I, inside))
        return {"s": s, "t": t, "I": I, "phase": np.angle(psi), "coarse": coarse, "verify": ver, "plane": pl,
                "route": T("the table of the exact field") if self.beam.model == "exact" else
                T("APPROXIMATION: the paraxial model"),
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
            raise Refusal(T("the hologram's slices are computed only along the axes: z = c, y = c or x = c"),
                          hint=T("turn the plane perpendicular to the x, y or z axis"))
        I = np.abs(vals) ** 2
        z_of = o[2] + np.outer(t, np.ones(len(s))) * np.asarray(pl.v)[2]
        return {"s": np.asarray(s), "t": np.asarray(t), "I": I, "phase": np.angle(vals * np.exp(-1j * f.k * z_of)),
                "coarse": coarse, "verify": {"points": 0, "note": T("the exact route of the angular spectrum (the "
                                                                     "same as the volume's)")},
                "plane": pl, "route": T("angular spectrum (exact for this plane)"), "exact": True}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        pd = self.planes[pid]
        I = sl["I"]
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(I.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": "plane",
                "route_label": T("{route}; the phase is arg(ψ e^{−ikz}) (the envelope)", route=sl["route"]),
                "exact": sl["exact"], "approximation": not sl["exact"],
                "reason": "" if sl["exact"] else T("the paraxial beam model (as chosen for this world)"),
                "verify": sl["verify"], "verify_title": T("|E|² at points of the plane against the direct calculation"),
                "z_near": 0.0, "window_est": 0.0}
        blobs = {"I": (I / max(peak, 1e-300)).astype(np.float32)}
        if not sl["coarse"]:
            blobs["phase"] = sl["phase"].astype(np.float32)
        self._msg(meta, blobs)
        ver = sl["verify"]
        if ver.get("points"):
            self._check(f"plane_{pid}", T("Slice {id} ({plane}): |E|² at {n} points against the direct calculation",
                                          id=pid, plane=pd["label"], n=ver["points"]),
                        ver["max_err"], 0.0, "", tol=ver["tol"], ok=ver["ok"],
                        group=T("Slices"), note=T("fraction of the slice's peak; tolerance: 4 × the error of the table"))

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
            self._check(f"plane_{pid}", T("Slice {id}: removed", id=pid), None, None, "", info=True, group=T("Slices"),
                        note=T("the last verification of this slice is in the run's record"))

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
        what = T("disc: the intensity behind the ±l mode filter") if self.rot == "disc" else T(
            "prism: the power of the two arms")
        if ref == 0:
            self._check("beat", T("Beat at the detector: the modulation depth (there is none)"), depth, 0.0, "",
                        tol=1e-6, ok=depth <= 1e-6, group=G_ROT,
                        note=T("{what}; {n:d} samples; reference: at l = 0 or f = 0 the frequency is not shifted",
                               what=what, n=A.WINDOW))
            f_meas = 0.0
        else:
            f_meas = ROT.peak_frequency(v, dt, positive=True, exclude_dc=True) / (2 * math.pi)
            self._check("beat", T("Beat at the detector: the frequency from the spectrum of the samples"), f_meas, ref,
                        T("Hz"), tol=1e-3, group=G_ROT,
                        note=T("{what}; {n:d} samples over two turns, the peak of the spectrum; reference 2|l|·f (the "
                               "modulation depth {d:.3g})", what=what, n=A.WINDOW, d=depth))
        s_meas = ROT.peak_frequency(c, dt) / (2 * math.pi)
        s_ref = self._shift_ref()
        self._check("shift", (T("Frequency shift of the light on the axis (from the complex amplitude)")
                              if self.rot == "disc" else
                              T("Frequency shift of the turned beam (from the overlap of the turned and the original beam)")), s_meas, s_ref, T("Hz"),
                    tol=1e-3 if s_ref else 1e-6 * max(self.f_rot, 1.0),
                    ok=(abs(s_meas) < 1e-6 * max(self.f_rot, 1.0)) if s_ref == 0 else None,
                    group=G_ROT,
                    note=(T("−l·f: the light scattered onto the axis took the harmonic n = −l of the surface")
                          if self.rot == "disc" else
                          T("l_out·2f, l_out = −l: the image is turned by twice the prism's angle and mirrored")))
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
                   "text": T("measurement {k:d}: beat {f:.4g} Hz (reference {ref:.4g}), shift {s:.4g} Hz", k=n_meas,
                             f=f_meas, ref=ref, s=s_meas)})

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
            raise Refusal(T("this world has no rotating element: there is nothing to change on the fly"))
        merged, errors = SCHEMA.coerce_live({"f_rot": self.f_rot}, values)
        if errors:
            raise ValueError(join(errors))
        f_new = float(merged["f_rot"])
        self.angle = self._angle_at(self.t)
        self.t_angle = self.t
        self.f_rot = f_new
        self.seg += 1
        self.seg_t0 = self.t
        self.seg_n = 0
        self.samples = []
        return T("rotation frequency f = {f:.4g} Hz from t = {t:.4g} ms: a new series of measurements", f=f_new,
                 t=self.t * 1e3)

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
            approximations.append(T("the hologram is a thin mask in the plane z = 0 (the propagation beyond it is "
                                    "exact)"))
        else:
            bm0 = self.beam
            if bm0.model == "paraxial":
                approximations.append(T(
                    "the paraxial beam model: a mode × a uniform polarisation (the error of the transverse field ~ "
                    "(λ/w0)² = {e:.2g}; there is no longitudinal field, while the exact one has ~ λ/(πw0) = {ez:.2g})",
                    e=(bm0.lam / bm0.w0) ** 2, ez=bm0.lam / (math.pi * bm0.w0)))
            elif bm0.dropped >= A.DROP_LABEL and p["gen"] == "mode":
                approximations.append(T(
                    "the source's spectrum is cut at q = k: {p:.3g} % of the power of the LG waist is in evanescent "
                    "waves, which the beam does not have; w0 is the width of the spectrum, not a measured waist (the "
                    "field at z = 0 differs from the named one by {d:.3g} % in the L2 norm)", p=100 * bm0.dropped,
                    d=100 * math.sqrt(bm0.dropped)))
            elif bm0.dropped >= A.DROP_LABEL:
                approximations.append(T(
                    "the beam has no evanescent waves behind the plate: at z = 0 they are {p:.3g} % of the power (the "
                    "near field of the singular point at the centre of the plate), at the distance λ {p1:.3g} %, at "
                    "2λ {p2:.3g} %; farther on the beam is the exact far field of the thin plate",
                    p=100 * bm0.dropped, p1=100 * bm0.ev_near[1], p2=100 * bm0.ev_near[2]))
            if p["gen"] == "spp":
                approximations.append(T("the spiral plate is a thin mask exp(ilφ) in the plane z = 0"))
            if self.rot == "disc":
                approximations.append(T("the rough disc is a thin phase screen, scalar (the polarisation takes no "
                                        "part)"))
            elif self.rot == "dove":
                approximations.append(T("the Dove prism is an ideal turn of the image; the polarisation does not "
                                        "change"))
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
        title = {"mode": T("Optical vortex: {name}", name=lg_name), "spp": T("Spiral plate, l = {l:d}", l=self.l),
                 "fork": T("Fork hologram, l = {l:d}", l=self.l)}[p["gen"]]
        cut = bm is not None and bm.model == "exact" and bm.dropped >= A.DROP_LABEL and p["gen"] == "mode"
        return {
            "title": title if bm is None else (
                (T("{title}, the exact vector beam (the spectrum cut at q = k)", title=title) if cut else
                 T("{title}, the exact vector beam", title=title)) if bm.model == "exact" else
                T("{title}, the paraxial model", title=title)),
            "text": T("A beam with the phase e^{ilφ}: the surfaces of equal phase are l intertwined helices, the energy "
                      "flow twists around the axis, every photon carries orbital angular momentum. Everything in the "
                      "scene is computed by the engine: the beam's field, the helical fronts (their phases are revealed "
                      "as the time goes on), the volume of the intensity, the flow lines, the slices. The rotating "
                      "element shifts the frequency of the light by an amount proportional to l: the detector collects "
                      "samples, and the beat is measured from their spectrum and compared with the formula."),
            "actions": [],
            "approximations": approximations,
            "scene3d": self._scene(),
            "beam": info,
            "t_show": self.T_show, "nb": NB,
            "units": {"x": T("µm"), "z": T("µm"), "t": T("s (the world's time; the optical phase is shown slowed)")},
        }, {}


VIZ = {
    "id": "v16_optical_vortices",
    "title": T("Optical vortices: Laguerre–Gauss beams, orbital angular momentum, the rotational Doppler effect"),
    "summary": T("The helical fronts of a beam with the phase e^{ilφ}, the twisted energy flow, slices with the phase "
                 "on a colour wheel; the orbital and spin angular momentum per photon measured from the field (the "
                 "exact vector solution or the paraxial model); a rotating disc or a Dove prism shifts the frequency, "
                 "and the beat at the detector is measured from the spectrum of the samples."),
    "purpose": T("Show what the orbital angular momentum of light is, where the paraxial picture stops working (tight "
                 "focusing: the longitudinal field, the exchange between spin and orbit) and how rotation gives the "
                 "frequency shift lΩ."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
