# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u38: a wave in 3-D — diffraction of monochromatic light by an aperture (a wrapper over lfphys; plan P10, P11;
the 3-D environment: owner, 2026-10-27).

The scalar field behind an aperture in the plane z = 0 (a Gaussian beam, a circle, a square, a slit or a double slit
of finite length) is propagated by its angular spectrum (lfphys.core.optics.angular_spectrum), the source entering by
its exact spectrum (lfphys.core.optics.aperture_fields), on the CPU or on GPU 0 (lfphys.core.backend).

The view is a 3-D scene: the screen with its aperture, the incident wave, the light behind the screen (the computed
volume), the energy current, the target at z_max; every element can be switched off. Slices are planes placed in the
scene at any orientation, up to three, each with its own window; they stay where they are put (moving them by
themselves is an option per plane, off by default). Each slice is computed exactly for its plane by the engine (as
the volume would give it on the same grid) and checked against the exact field where the source has one.

Modelling (owner, 2026-10-24): **full 3-D** computes the volume (the 3-D light and the energy current are shown);
**slices only** computes nothing but the slices placed (faster; the 3-D scene shows the apparatus and the slices).
For a slit or a double slit, the planes y = c can be computed by the reduced 2-D model (the slit taken as infinitely
long): an approximation, flagged everywhere and measured against the exact slice. Units: micrometres.
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import backend
from lfphys.core import geometry as G
from lfphys.core.optics import angular_spectrum as AS
from lfphys.i18n import T, join
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

from .engine import apparatus as A

SOURCES = [("gauss", T("Gaussian beam")), ("circle", T("circular aperture")), ("square", T("square aperture")),
           ("slit", T("slit of finite length")), ("double", T("two slits of finite length"))]
SLITS = ("slit", "double")
NZ = 96  # z planes of the volume
MAX_PLANES = 3  # the shared environment's limit (lfviz.planes3d)
DEFAULT_NORMALS = {1: (0.0, -1.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 0.0, 1.0)}  # mutually perpendicular
ROUTES = {"plane": T("exact for this plane (as the volume would give it on this grid)"),
          "turned": T("exact for this plane; the source is rotated, the window measured for the rotated source"),
          "reduced": T("APPROXIMATION: the reduced 2-D model (the slit taken as infinite)")}
AUTO_NT = 64  # rows of a slice moved by "auto" (coarse, not checked; the full slice when the plane stops)


def _p(*a, **k):
    return Param(*a, **k)


EXPERIMENT, COMPUTATION = T("Experiment"), T("Computation")
SCHEMA = Schema([
    _p("source", T("Source in the plane z = 0"), "select", "double", group=EXPERIMENT, options=SOURCES),
    _p("lam", T("Wavelength λ, µm"), "float", 0.5, group=EXPERIMENT, min=0.3, max=1.5),
    _p("w", T("Gaussian beam waist w, µm"), "float", 1.5, group=EXPERIMENT, min=0.5, max=6.0,
       show_if={"source": ["gauss"]}),
    _p("a", T("Radius / half-width a, µm"), "float", 0.75, group=EXPERIMENT, min=0.2, max=6.0,
       show_if={"source": ["circle", "square", "slit", "double"]}),
    _p("d", T("Distance between the slits, µm"), "float", 4.0, group=EXPERIMENT, min=1.0, max=12.0,
       show_if={"source": ["double"]}),
    _p("L", T("Slit length along y, µm"), "float", 8.0, group=EXPERIMENT, min=1.0, max=24.0,
       show_if={"source": ["slit", "double"]}),
    _p("zmax", T("Depth to the target z_max, µm"), "float", 30.0, group=EXPERIMENT, min=2.0, max=80.0),
    _p("n", T("Grid in the plane, points per axis"), "select", 256, group=COMPUTATION,
       options=[(128, "128"), (256, "256"), (512, T("{n:d} (slices only)", n=512))]),
    _p("mode", T("Modelling"), "select", "full3d", group=COMPUTATION,
       options=[("full3d", T("whole volume: light and energy current in 3-D, any slices")),
                ("slices", T("slices only (faster): only the planes placed are computed"))]),
    _p("reduced", T("Slices y = c by the reduced 2-D model (the slit taken as infinite) — an approximation"), "bool",
       False, group=COMPUTATION, show_if={"mode": ["slices"], "source": ["slit", "double"]}),
], presets={
    "double": {"label": T("Two slits of finite length: the whole volume"), "params": {}},
    "double_slices": {"label": T("Two slits: slices only, y = c by the reduced 2-D model (approximation)"),
                      "params": {"mode": "slices", "reduced": True}},
    "circle": {"label": T("Circular aperture: dips and peaks of intensity on the axis"),
               "params": {"source": "circle", "a": 3.0, "zmax": 40.0}},
    "gauss": {"label": T("Gaussian beam, w = {w} µm: divergence (checked against the integral)", w=1.5),
              "params": {"source": "gauss", "zmax": 30.0}},
    "square_big": {"label": T("Square aperture, grid {n:d}: slices only", n=512), "params": {
        "source": "square", "a": 2.0, "n": 512, "mode": "slices", "zmax": 15.0}},
})


class Simulation(SlicePlanes, BaseSimulation):
    speed_range = (0.05, 20.0)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._buf = []
        p = self.params
        if p["mode"] == "full3d" and int(p["n"]) > 256:
            raise Refusal(T("the whole volume on a grid of {n:d} would take ~{gb} GB", n=int(p["n"]), gb=1.6),
                          T("for a grid of {n:d} choose «slices only»", n=int(p["n"])))
        self.lam = float(p["lam"])
        self.k = 2 * math.pi / self.lam
        self.n = int(p["n"])
        self.dx = self.lam / 4 if self.n <= 256 else self.lam / 8
        self.x = (np.arange(self.n) - self.n // 2) * self.dx
        self.half = self.n // 2 * self.dx
        self.zmax = float(p["zmax"])
        self.box = ((float(self.x[0]), float(self.x[0]), 0.0), (float(self.x[-1]), float(self.x[-1]), self.zmax))
        self.zs = np.linspace(0.0, self.zmax, NZ)
        self.z_near = A.near_zone(self.dx, self.k)
        backend.reset_used()
        self.src = A.source(p, self.n)
        try:
            self.win = A.choose_window(self.src, self.dx, self.k, self.zmax)
        except A.WindowError as e:  # the world is refused: what to change, with a working example (review UX-params P26)
            ex = [T("{hint}; a working example: the “{preset}” preset (a = {a} µm, z_max = {zmax} µm)", hint=e.hint,
                    preset=v["label"], a=float(v["params"]["a"]), zmax=float(v["params"]["zmax"]))
                  for v in SCHEMA.presets.values() if v["params"].get("source") == p["source"]
                  and "a" in v["params"] and "zmax" in v["params"]]
            raise Refusal(e.text, ex[0] if ex else e.hint) from e
        self.kw = {"pad": self.win.pad, "band_limit": self.win.band_limit}
        self.peak_amp = float(np.max(np.abs(self.win.plane)))
        self.vol = None
        self.flux_P = None
        self.modelling = G.Modelling("full3d")
        if p["mode"] == "full3d":
            self.vol = AS.propagate_volume(self.src, self.dx, self.k, self.zs, **self.kw)
        self._turned = {}  # azimuth of a plane's u (degrees) -> the window measured for the turned source
        self._init_planes()  # the shared slice planes (lfviz.planes3d): self.planes, self.slices
        self.plane_center = (0.0, 0.0, self.zmax / 2)  # the axis at mid-depth (the box's centre is dx/2 off the axis)
        self.default_normals = DEFAULT_NORMALS
        self.plane_min_step = self.dx
        self._set_plane(1, self.plane_center, DEFAULT_NORMALS[1])
        self._checks()

    # --- the scene ------------------------------------------------------------------------------------------------
    def _scene(self):
        p = self.params
        W = 2 * self.half
        objects = []
        if p["source"] == "gauss":
            objects.append({"id": "source", "label": T("Gaussian beam in the plane z = 0 (given)"), "kind": "disk",
                            "z": 0.0, "w": float(p["w"]), "size": [W, W], "visible": True})
        else:
            holes = ([{"circle": [0.0, 0.0, float(p["a"])]}] if p["source"] == "circle"
                     else [{"rect": list(r)} for r in A.rects(p)])
            objects.append({"id": "screen", "label": T("Screen with the aperture (z = 0)"), "kind": "plate", "z": 0.0,
                            "size": [W, W], "holes": holes, "visible": True})
        objects.append({"id": "incident", "label": T("Incident plane wave (given)"), "kind": "incident",
                        "z0": -0.15 * self.zmax, "z1": 0.0, "lam": self.lam, "size": [W, W], "visible": True})
        objects.append({"id": "target", "label": T("Target (z = {z} µm): intensity", z=self.zmax), "kind": "target",
                        "z": self.zmax, "size": [W, W], "visible": True})
        layers = []
        if self.vol is not None:
            layers.append({"id": "light", "label": T("Light behind the aperture (volume, preview)"), "kind": "volume",
                           "visible": True})
            layers.append({"id": "flux", "label": T("Energy current (direction and magnitude)"), "kind": "vectors",
                           "visible": False})
        return {"box": [list(self.box[0]), list(self.box[1])], "units": T("µm"), "objects": objects, "layers": layers,
                "planes": {"max": MAX_PLANES, "center": [0.0, 0.0, self.zmax / 2],
                           "defaults": {str(i): list(v) for i, v in DEFAULT_NORMALS.items()}},
                "z_near": self.z_near, "dx": self.dx}

    def _send_scene_data(self):
        if self.vol is not None:
            pv = A.preview_volume(self.vol, self.n)
            self._msg({"type": "volume", "t": self.t, "id": "light", "dims": list(pv.shape),
                       "box": [list(self.box[0]), list(self.box[1])],
                       "note": T("intensity averaged over 2×2 cells (preview); the exact values are in the slices")},
                      {"data": pv})
            zf = np.linspace(max(2 * self.z_near, self.zmax / 12), self.zmax, 10)
            pos, vec, P, jlast = A.flux_glyphs(self.src, self.dx, self.k, zf, self.x, self.win)
            self.flux_P = (zf, P, jlast)
            self._msg({"type": "vectors", "t": self.t, "id": "flux", "count": int(len(pos)),
                       "note": T("energy current j = Im(U*∇U)/k on 10 planes z, 16×16 points; length ~ √|j|")},
                      {"pos": pos, "vec": vec})
        tgt = np.abs(self.win.plane) ** 2
        step = max(1, self.n // 256)
        tgt = tgt[::step, ::step]
        self._msg({"type": "target", "t": self.t, "id": "target", "shape": list(tgt.shape),
                   "x": [float(self.x[0]), float(self.x[-1])], "peak": float(tgt.max())},
                  {"img": (tgt / max(float(tgt.max()), 1e-300)).astype(np.float32)})

    # --- slice planes (view commands; owner, 2026-10-27) ------------------------------------------------------------
    def _is_reduced(self, normal):
        n = np.asarray(normal, float) / np.linalg.norm(normal)
        return bool(self.params["mode"] == "slices" and self.params["reduced"] and self.params["source"] in SLITS
                    and abs(abs(n[1]) - 1.0) < 1e-9)

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        """The slice of one plane (lfviz.planes3d hook): exact for its plane, or the reduced 2-D model (flagged)."""
        reduced = self._is_reduced(pl.normal)
        nt = AUTO_NT if coarse else A.NT
        if reduced:
            win, route = self.win, "reduced"
            s, t, U = A.reduced_slice(self.params, self.n, self.dx, self.k, pl, s_rng, t_rng, self.box, nt=nt)
            reason = T("the slit of length L = {L} µm is taken as infinite (the reduced 2-D model); the error of the "
                       "approximation is given in the checks", L=float(self.params["L"]))
        else:
            key = round(math.degrees(math.atan2(pl.u[1], pl.u[0])) % 180.0, 2)
            if key not in self._turned:  # a plane that turns the source: its window measured once per azimuth
                self._turned[key] = A.window_for_plane(self.src, self.dx, self.k, self.zmax, pl, self.win)
            win = self._turned[key]
            route = "plane" if win is self.win else "turned"
            s, t, U = A.compute_slice(self.src, self.dx, self.k, pl, s_rng, t_rng, win, self.box, nt=nt)
            reason = ""
        tol = win.abs_err + 1e-9
        if reduced:
            ver = {"points": 0, "note": T("an approximation: its error is given in the “APPROXIMATION” check")}
        elif coarse:
            ver = {"points": 0, "note": T("auto-move: a coarse slice, not checked; the full one when auto-move is off")}
        else:
            ver = A.verify_slice(self.params, self.k, pl, s, t, U, self.z_near, tol)
        return {"s": s, "t": t, "U": U, "route": route, "exact": not reduced, "coarse": coarse, "reason": reason,
                "verify": ver, "plane": pl, "window": win, "tol": tol}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        pl = sl["plane"]
        self._send_slice(pid)
        ver = sl["verify"]
        if not sl["exact"] and not sl["coarse"]:
            self._check_reduced(pid)
        elif ver.get("points"):
            self._check(f"plane_exact_{pid}", T("Slice {pid} ({plane}): the field at {n:d} points against the exact one",
                                                pid=pid, plane=G._label(pl), n=int(ver["points"])),
                        ver["max_err"], 0.0, "", tol=sl["tol"], ok=ver["ok"],
                        note=T("reference without FFT at points of the plane itself (the brightest and two with ≥ 5 % "
                               "of its intensity, deeper than z_near); tolerance: the window's error ({tol:.1e})",
                               tol=float(sl["tol"])))
        self._update_modelling()

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):  # its check row says so (review C8)
            self._check(f"plane_exact_{pid}", T("Slice {pid}: removed", pid=pid), None, None, "", info=True,
                        note=T("the last comparison of this slice is in the run's record"))
        self._update_modelling()

    def _update_modelling(self):
        if self.params["mode"] == "full3d":
            return
        self.modelling = G.Modelling("slices", [G.Slice(sl["plane"], sl["exact"], sl["reason"])
                                                for sl in self.slices.values()] or [G.Slice(G.Plane.preset("xz"))])
        self._msg({"type": "modelling", "t": self.t, "modelling": self.modelling.describe(),
                   "approximations": self.modelling.approximations()})

    def _send_slice(self, pid):
        sl = self.slices[pid]
        U = sl["U"]
        I = np.abs(U) ** 2
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        pd = self.planes[pid]
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(U.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd["origin"], "u": pd["u"], "v": pd["v"], "normal": pd["normal"], "label": pd["label"],
                "peak": peak, "route": sl["route"],
                "route_label": ROUTES[sl["route"]] if sl["window"].est <= A.TOL else
                T("{route}; the window for the rotated source did not reach the tolerance ({est:.1e} > {tol:.0e})",
                  route=ROUTES[sl["route"]], est=float(sl["window"].est), tol=float(A.TOL)),
                "exact": sl["exact"],
                "approximation": not sl["exact"], "reason": sl["reason"], "verify": sl["verify"],
                "z_near": self.z_near, "window_est": sl["window"].est, "window": sl["window"].describe()}
        blobs = {"I": (I / max(peak, 1e-300)).astype(np.float32)}
        if not sl["coarse"]:  # moving slices are not recorded with their phase (review C6: the record's size)
            blobs["phase"] = np.angle(U).astype(np.float32)
        self._msg(meta, blobs)

    def _plane_preview(self, pid, pl, s_rng, t_rng):
        """While a plane is dragged in "slices only": a coarse slice, not kept, not checked."""
        if self._is_reduced(pl.normal):
            s, t, U = A.reduced_slice(self.params, self.n, self.dx, self.k, pl, s_rng, t_rng, self.box, nt=48)
        else:
            s, t, U = A.compute_slice(self.src, self.dx, self.k, pl, s_rng, t_rng, self.win, self.box, nt=48)
        I = np.abs(U) ** 2
        peak = float(np.nanmax(I)) if np.isfinite(I).any() else 1.0
        self._msg({"type": "slice", "t": self.t, "id": pid, "preview": True, "shape": list(U.shape),
                   "s": [float(s[0]), float(s[-1]), len(s)], "tt": [float(t[0]), float(t[-1]), len(t)],
                   "origin": [float(c) for c in pl.origin], "u": list(pl.u), "v": list(pl.v),
                   "normal": [float(c) for c in pl.normal], "label": G._label(pl), "peak": peak,
                   "z_near": self.z_near, "window_est": self.win.est},
                  {"I": (I / max(peak, 1e-300)).astype(np.float32)})

    # --- checks -------------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False):
        rel = None
        if ref is not None and value is not None and ref != 0:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": T("Wave"), "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        self._msg(d)

    def _check_reduced(self, pid):
        sl = self.slices[pid]
        s, t, Ue = A.compute_slice(self.src, self.dx, self.k, sl["plane"], (sl["s"][0], sl["s"][-1]),
                                   (sl["t"][0], sl["t"][-1]), self.win, self.box, check=True)
        Ie, Ir = np.abs(Ue) ** 2, np.abs(sl["U"]) ** 2
        err = float(np.nanmax(np.abs(Ir - Ie)) / np.nanmax(Ie))
        self._check("reduced", T("APPROXIMATION: the reduced 2-D model of slice {pid} ({plane}) against the exact one",
                                 pid=pid, plane=G._label(sl["plane"])), err, 0.0, "", info=True,
                    note=T("the largest difference of intensity, as a fraction of the peak; {reason}",
                           reason=sl["reason"]))

    def _checks(self):
        p = self.params
        win, j0 = self.win, self.n // 2
        rows = join([T("×{pad:d} (band-limited): {d:.1e}", pad=int(pp), d=float(d)) if bl else
                     T("×{pad:d}: {d:.1e}", pad=int(pp), d=float(d)) for pp, bl, d in win.rows])
        self._check("window", T("Computation window: periodic copies at depth z_max"), win.est, None, "",
                    tol=A.TOL, ok=win.est <= A.TOL,
                    note=T("{window}; a fraction of the peak amplitude, estimated as {k}·max|U(window) − U(window×2)|; "
                           "measured: {rows}", window=win.describe(), k=float(A.SAFETY), rows=rows))
        for i, j in A.ref_points(p, self.x):
            x0, y0 = float(self.x[i]), float(self.x[j])
            ref, rerr = A.reference(p, self.k, self.zmax, x0, y0)
            U = complex(win.plane[i, j])
            tol = win.abs_err + rerr + 1e-9
            how = {"gauss": T("the Hankel integral (quadrature)"),
                   "circle": T("the closed-form Rayleigh–Sommerfeld solution on the axis")}
            self._check(f"exact_{i}_{j}", T("Field at the point x = {x:.3g}, y = {y:.3g}, z = z_max: the exact value",
                                            x=x0, y=y0),
                        abs(U), abs(ref), "", tol=tol / max(abs(ref), 1e-300), ok=abs(U - ref) <= tol,
                        note=T("reference without FFT: {how}; complex difference {d:.1e}, tolerance = the window's error "
                               "+ the reference's error ({tol:.1e})",
                               how=how.get(p["source"], T("the Rayleigh–Sommerfeld integral over the angle")),
                               d=float(abs(U - ref)), tol=float(tol)))
        # two fp64 routes of the engine: the plane y = 0 by the plane route against the transverse planes' rows
        zc = [float(self.zs[NZ // 2]), self.zmax]
        rows_v = np.stack([AS.propagate_field(self.src, self.dx, self.k, zc[0], check=True, **self.kw)[:, j0],
                           win.plane[:, j0]])
        s, U = AS.propagate_plane(self.src, self.dx, self.k, G.Plane.horizontal((0.0, -1.0, 0.0)),
                                  (float(self.x[0]), float(self.x[-1])), zc, check=True, **self.kw)
        diff = float(np.max(np.abs(U - rows_v)) / np.max(np.abs(rows_v)))
        self._check("slice_route", T("The slice y = 0 computed in its own plane agrees with the one cut from the "
                                     "stack of transverse planes"),
                    diff, 0.0, "", tol=1e-12, ok=diff <= 1e-12,
                    note=T("the engine's two methods in fp64 at z = z_max/2 and z_max (a fraction of the peak "
                           "amplitude)"))
        u = backend.used().get(AS.KERNEL, {}).get("drawn", {})
        exact = [sl for sl in self.slices.values() if sl["exact"]]  # the reduced model is computed in fp64
        if u.get("precision") == "fp32" and (self.vol is not None or exact):
            # what is drawn in fp32 against fp64 (review B1-5): the kernel's declared bound is the tolerance
            bound = backend.kernels()[AS.KERNEL].precisions["fp32"]["bound"]
            if self.vol is not None:
                drawn, ref64 = self.vol[-1], win.plane
            else:
                drawn, ref64 = self._fp64_pair(exact[0])
            err = float(np.nanmax(np.abs(drawn - ref64)) / np.nanmax(np.abs(ref64)))
            self._check("fp32", T("The picture in fp32 compared with the same computation in fp64"), err, 0.0, "", tol=bound,
                        ok=err <= bound, note=T("the kernel's bound for fp32: {b:.0e} of the peak amplitude", b=float(bound)))
        self._check("near", T("Next to the aperture (z < {z:.2g} µm): the field band-limited by the grid", z=self.z_near),
                    self.z_near, None, T("µm"), info=True,
                    note=T("components with |q| ≥ π/dx (evanescent) are left out: at depth z_near they are below "
                           "1e-6 of their amplitude at z = 0; closer to the aperture (hatched in the picture) the "
                           "field oscillates next to the edges (the Gibbs phenomenon): a property of the grid, not "
                           "of the physics"))
        if u:
            self._check("device", T("The angular spectrum (the picture) was computed on {device} ({precision})",
                                    device="GPU" if u["device"] == "gpu" else "CPU", precision=u["precision"]),
                        None, None, "", info=True,
                        note=T("{reason}; the checks are always in fp64", reason=u.get("reason", "")))

    def _fp64_pair(self, sl):
        """The drawn slice and the same slice in fp64 (check=True), NaN where the drawn one is."""
        s, U = AS.propagate_plane(self.src, self.dx, self.k, sl["plane"], (sl["s"][0], sl["s"][-1]), sl["t"],
                                  check=True, **self.kw)
        U = np.asarray(U, np.complex128)
        U[np.isnan(sl["U"])] = np.nan
        return sl["U"], U

    def _check_flux(self):
        """The energy current where the exact one is known (review C4): j at the reference points of z_max against
        Im(U* grad U)/k of the exact field and its derivatives (no FFTs); the window's error as tolerance. The power
        through the planes is shown as information: for the plain sum it equals the spectrum's closed form by
        Parseval's identity of the discrete sum (a check of the code, not of the physics)."""
        if self.flux_P is None:
            return
        zf, P, jlast = self.flux_P
        u = backend.used().get(AS.KERNEL, {}).get("drawn", {})
        fp32 = u.get("precision") == "fp32"
        worst, worst_tol, ok = 0.0, 0.0, True
        for i, j in A.ref_points(self.params, self.x):
            jr, Ur, g, rerr = A.reference_current(self.params, self.k, self.zmax, float(self.x[i]), float(self.x[j]))
            jc = jlast[:, i, j]
            tol = self.win.abs_err * (abs(Ur) + g) + rerr + 1e-9
            if fp32:
                tol += backend.kernels()[AS.KERNEL].precisions["fp32"]["bound"] * self.peak_amp ** 2 * 3
            d = float(np.max(np.abs(jc - jr)))
            ok &= d <= tol
            if d / tol >= worst / max(worst_tol, 1e-300):
                worst, worst_tol = d, tol
        self._check("flux_exact", T("Energy current at points of z_max against the exact one (derivatives of the exact "
                                    "field)"), worst, 0.0, "", tol=worst_tol, ok=ok,
                    note=T("j = Im(U*∇U)/k; reference without FFT: closed-form derivatives (the Gaussian field, the "
                           "circle on its axis) or five-point differences of the exact field (rectangles); tolerance: "
                           "the window's error × (|U| + |∇U|/k) + the fp32 bound") if fp32 else
                    T("j = Im(U*∇U)/k; reference without FFT: closed-form derivatives (the Gaussian field, the circle "
                      "on its axis) or five-point differences of the exact field (rectangles); tolerance: the window's "
                      "error × (|U| + |∇U|/k)"))
        ref = AS.flux_of_spectrum(self.src, self.dx, self.k, pad=self.win.pad)
        dev = float(np.max(np.abs(P - ref)) / ref)
        self._check("flux", T("Power through the planes z: an identity of the sum (a check of the code)"), dev, 0.0, "",
                    info=True,
                    note=(T("the band limit removes the components at large angles with depth: a fraction of the power")
                          if self.win.band_limit else
                          T("P(z) = Σ j_z dx dy over the whole window at {n:d} depths against the closed form from "
                            "the spectrum: Parseval's identity of the discrete sum; it confirms the code and the "
                            "normalisation, not the window or the physics (those are checked in the row above)", n=len(zf))))

    # --- messages -----------------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, []
        self._send_scene_data()
        self._check_flux()
        buf, self._buf = buf + self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- live: none (the view is driven by view commands) --------------------------------------------------------
    def live_values(self):
        return {}

    def set_live(self, values):
        raise Refusal(T("this world has no parameters to change on the fly: slices are placed in the 3-D scene"))

    # --- time: planes with "auto" move along their normal; the others stay where they are (owner, 2026-10-27) --------
    def advance(self, t_target):
        dt = t_target - self.t
        self.t = t_target
        self._advance_planes(t_target, dt)

    def frame(self):
        return {}, {}

    def engine_modules(self):
        return ["core.optics.angular_spectrum", "core.optics.aperture_fields", "core.geometry", "core.backend"]

    def header(self):
        p = self.params
        return {
            "title": T("Wave in 3-D: {source}", source=dict(SOURCES)[p["source"]]),
            "text": T("The field behind the aperture in the plane z = 0 propagates as a sum of plane waves (the angular "
                      "spectrum); the aperture enters by its exact spectrum. The 3-D scene shows the screen, the "
                      "incident wave, the light behind the aperture, the energy current and the target; any part can "
                      "be switched off. Slices are planes at any angle (up to three), each with its own window; each "
                      "slice is computed exactly for its plane and checked against the exact field. Slices stay where "
                      "they are put; auto-move is optional."),
            "actions": [],
            "scene3d": self._scene(),
            "modelling": self.modelling.describe(),
            "approximations": self.modelling.approximations(),
            "accuracy": {"window": self.win.est, "tol": A.TOL, "pad": self.win.pad,
                         "band_limit": self.win.band_limit, "z_near": self.z_near},
            "units": {"x": T("µm"), "z": T("µm")},
            "lam": self.lam, "half": self.half, "zmax": self.zmax, "n": self.n, "dx": self.dx,
        }, {}


VIZ = {
    "id": "u38_wave_3d",
    "title": T("Wave in 3-D: diffraction by an aperture"),
    "summary": T("A 3-D scene: the screen with its aperture, the incident wave, the light behind the aperture, the "
                 "energy current and the target; slices are planes at any angle (up to three) with their own windows; "
                 "the accuracy of every world is measured."),
    "purpose": T("A full 3-D environment for a researcher on the engine: parts of the scene are switched on one by one, "
                 "slices are placed and turned by hand or by parameters, the computation runs on the CPU or the GPU."),
    "version": "2.0",
    "schema": SCHEMA,
    "simulation": Simulation,
    "audience": "university",
    "section": "optics",
    "ui": "standard",
    "teaser": T("Light passes two slits of finite length: the 3-D field behind them, slices at any angle, the energy current."),
    "courses": [
        {"text": T("Halliday, Resnick & Walker, Fundamentals of Physics"), "chapters": "36"},
        {"text": T("Hecht, Optics"), "chapters": "10"},
    ],
    "related": ["S38"],
    "recordings": [
        {"id": "double", "preset": "double", "seconds": 20, "fps": 10, "speed": None, "seed": 1, "script": [], "poster": 15},
    ],
}
