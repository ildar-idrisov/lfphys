# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v10: what a fast observer really sees (a wrapper over lfphys; plan P14.2, on the plan's P9, P10, P11).

A 3-D scene of self-luminous bodies (black bodies with patterns: a cube, spheres, a train, towers, a floor) and
optionally a black-body sky and stars, seen by an observer who may move. The run computes the observer's image by
light-time ray tracing (lfphys.core.raytrace): every pixel is a photon, Lorentz-transformed into the lab (aberration),
its past light ray traced back to the body that emitted it (light-time: Terrell-Penrose rotation, the stretched or
shortened look of moving bodies), and the light seen as a black body at D T (Doppler colours and the searchlight
brightness, exactly). The 3-D scene shows the lab at the current lab time: the bodies Lorentz-contracted at their
lab-simultaneous positions, and the retarded shapes — where the light the observer receives now was emitted.

World time is lab time (seconds; the scenes last some hundred nanoseconds); lengths in metres. The observer's
velocity is live (a boost of a point observer at the current event: the image changes at once); what the bodies do is
a world parameter (an instantaneous velocity change of an extended body is not a rigid motion).
"""

from __future__ import annotations

import math
import zlib

import numpy as np
from scipy import constants as sc

from lfphys.core import backend as B
from lfphys.core import lorentz as LZ
from lfphys.core import raytrace as RT
from lfphys.i18n import T, join, text_of
from lfphys.tools import colour as CO
from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.sim import Simulation as BaseSimulation

C = sc.c
NS = 1e-9
RES = {"s": (192, 144), "m": (256, 192), "l": (320, 240)}
SKY_RES = {"s": (256, 128), "m": (320, 160), "l": (384, 192)}
IMG_FRAMES = 7        # frames between images while the world runs: 0.35 s of play at 20 frames/s (the record's size,
# README); counted in frames, not wall time, so that a world rebuilt from its record renders the same images (C1-6)
EPS = np.finfo(float).eps
# a star is drawn into one pixel as bright as a surface of its temperature there at rest, times its flux factor

SCENES = [("flyby", T("a cube and a ball fly past the observer")),
          ("city", T("the observer flies down a street between towers")),
          ("sky", T("a black-body sky and stars: the dipole and aberration")),
          ("train", T("a long train passes the posts"))]
IMAGES = [("seen", T("what the observer sees (full physics)")),
          ("geometry", T("for comparison: geometry only (colour and brightness as at rest)")),
          ("snapshot", T("for comparison: an instantaneous snapshot without the light's travel time (not what is seen)")),
          ("doppler", T("Doppler factor D (false colours)")),
          ("delay", T("light delay: when the light was emitted (false colours)"))]
CAMERAS = [("pinhole", T("ordinary (field of view)")), ("sky", T("whole sky (360° × 180° map)"))]


def _p(*a, **k):
    return Param(*a, **k)


def _vec(v):
    """A vector of three numbers as a text: the separator follows the language (ru: decimal commas)."""
    x, y, z = (float(c) for c in v)
    return T("({x:.3f}, {y:.3f}, {z:.3f})", x=x, y=y, z=z)


SCENE, OBSERVER, CAMERA, IMAGE = T("Scene"), T("Observer"), T("Camera"), T("Image")
SCHEMA = Schema([
    _p("scene", SCENE, "select", "flyby", group=SCENE, options=SCENES),
    _p("beta", T("Speed of the bodies β (fraction of c)"), "float", 0.9, group=SCENE, min=0.0, max=0.99,
       show_if={"scene": ["flyby", "train"]},
       help=T("The bodies move uniformly along x; this is a world parameter: the speed of an extended body cannot be "
              "changed instantly (that would not be a rigid motion)")),
    _p("sky_T", T("Temperature of the sky, K"), "float", 4000.0, group=SCENE, min=500.0, max=30000.0, log=True,
       show_if={"scene": ["sky"]}),
    _p("stars", T("Stars"), "int", 300, group=SCENE, min=0, max=2000, show_if={"scene": ["sky", "city"]}),
    _p("obs_beta", T("Speed of the observer β"), "float", 0.0, group=OBSERVER, min=0.0, max=0.99, live=True,
       help=T("A change is a boost of a point observer at the current moment: the same light, other directions and "
              "frequencies")),
    _p("obs_theta", T("Direction of the observer's velocity: from the z axis θ, °"), "float", 0.0, group=OBSERVER,
       min=0.0, max=180.0, live=True),
    _p("obs_phi", T("Direction of the observer's velocity: azimuth φ, °"), "float", 0.0, group=OBSERVER, min=0.0,
       max=360.0, live=True),
    _p("camera", CAMERA, "select", "pinhole", group=CAMERA, live=True, options=CAMERAS),
    _p("fov", T("Horizontal field of view, °"), "float", 120.0, group=CAMERA, min=20.0, max=150.0, live=True,
       show_if={"camera": ["pinhole"]}),
    _p("yaw", T("View: turn from the z axis towards the x axis, °"), "float", 0.0, group=CAMERA, min=-180.0, max=180.0,
       live=True),
    _p("pitch", T("View: up, °"), "float", 0.0, group=CAMERA, min=-80.0, max=80.0, live=True),
    _p("res", T("Image size"), "select", "m", group=CAMERA, live=True,
       options=[("s", T("small size")), ("m", T("medium size")), ("l", T("large size"))]),
    _p("image", IMAGE, "select", "seen", group=IMAGE, live=True, options=IMAGES),
    _p("exposure", T("Exposure"), "select", "fixed", group=IMAGE, live=True,
       options=[("fixed", T("as for the scene at rest (shows where it is brighter and where darker)")),
                ("auto", T("per frame (the colours show, the brightness is evened out)"))]),
    _p("ev", T("Exposure correction, stops"), "float", 0.0, group=IMAGE, min=-8.0, max=8.0, live=True),
], presets={
    "terrell": {"label": T("A cube and a ball fly past at β = {b}: Terrell rotation, the ball stays a circle", b=0.9),
                "params": {}},
    "terrell_099": {"label": T("The same at β = {b}", b=0.99), "params": {"beta": 0.99}},
    "city": {"label": T("Flight down a street at β = {b}: aberration, blue ahead, brightness", b=0.9),
             "params": {"scene": "city", "obs_beta": 0.9}},
    "sky": {"label": T("A sky of {temp:d} K at β = {b}: the dipole, the stars crowd forward", temp=4000, b=0.9),
            "params": {"scene": "sky", "obs_beta": 0.9, "camera": "sky"}},
    "train": {"label": T("A train at β = {b} passing posts: stretching and shortening", b=0.8),
              "params": {"scene": "train", "beta": 0.8}},
    "rest": {"label": T("The scene at rest (β = 0): an ordinary picture, a check of the tracer"), "params": {"beta": 0.0}},
    "snapshot": {"label": T("For comparison: an instantaneous snapshot (the Lorentz contraction that is not seen)"),
                 "params": {"image": "snapshot"}},
})


def _unit_dir(theta_deg, phi_deg):
    t, p = math.radians(theta_deg), math.radians(phi_deg)
    return np.array([math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t)])


def _look(yaw_deg, pitch_deg):
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    return np.array([math.cos(p) * math.sin(y), math.sin(p), math.cos(p) * math.cos(y)])


# --- the scenes (metres) ------------------------------------------------------------------------------------------------
def build_scene(p, rng):
    """(Scene, info per body, observer start x, notes) for the world's parameters."""
    kind = p["scene"]
    b = float(p.get("beta", 0.0))
    v = (b * C, 0.0, 0.0)
    floor = RT.Panel((0.0, -2.0, 20.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), half=(60.0, 60.0), cell=2.0,
                     temps=(5200.0, 3400.0), name=T("floor (at rest)"))
    bodies, stars, sky, x_obs = [], [], None, (0.0, 0.0, 0.0)
    if kind == "flyby":
        # the cube's faces coded: +x leading 9500 K (blue-white), -x trailing 3600 K (orange), -z facing the observer
        # 6500 K (white), +z far side 2600 K (red), top and bottom 5000 K
        cube = RT.Box((-3.0, 0.0, 8.0), (1.0, 1.0, 1.0), v, temps=(9500.0, 3600.0, 5000.0, 5000.0, 2600.0, 6500.0),
                      alt=0.8, cells=4, name=T("cube"))
        ball = RT.Sphere((-10.0, 0.5, 11.0), 1.3, v, temps=(7000.0, 3800.0), cells=(6, 12), name=T("ball"))
        bodies = [cube, ball, floor]
    elif kind == "train":
        train = RT.Box((-14.0, 0.0, 9.0), (12.0, 1.4, 1.6), v, temps=(9000.0, 3500.0, 5200.0, 5200.0, 4200.0, 6200.0),
                       alt=0.75, cells=24, name=T("train"))
        posts = [RT.Box((x, 0.5, 6.0), (0.12, 2.5, 0.12), temps=(6800.0,) * 6, alt=1.0, cells=1,
                        name=T("post x = {x} m", x=float(x)))
                 for x in np.arange(-30.0, 31.0, 6.0)]
        bodies = [train] + posts + [floor]
    elif kind == "city":
        for x in (-11.0, -5.5, 5.5, 11.0):
            for z in np.arange(10.0, 81.0, 10.0):
                h = float(rng.uniform(2.0, 6.0))
                Tk = float(rng.choice([4200.0, 5200.0, 6200.0, 7500.0]))
                bodies.append(RT.Box((x, -2.0 + h, z), (2.0, h, 2.0), temps=(Tk,) * 6, alt=0.7, cells=3,
                                     name=T("tower ({x}, {z})", x=float(x), z=float(z))))
        bodies.append(RT.Panel((0.0, -2.0, 40.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), half=(40.0, 80.0), cell=2.0,
                               temps=(5200.0, 3400.0), name=T("street (at rest)")))
        x_obs = (0.0, 0.0, -5.0)
    elif kind == "sky":
        sky = float(p["sky_T"])
    else:
        raise ValueError(f"unknown scene {kind!r}")
    if kind in ("sky", "city"):
        n = int(p.get("stars", 0))
        d = rng.normal(size=(n, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        Tk = 10 ** rng.uniform(math.log10(3000.0), math.log10(12000.0), n)
        stars = [(tuple(map(float, d[i])), float(Tk[i])) for i in range(n)]
    return RT.Scene(bodies, sky=sky, stars=stars), x_obs


def mesh_of(body, n=None):
    """Rest-frame vertices (offsets from the centre), triangles and rest temperatures of a body, for the 3-D view."""
    if body.kind == "sphere":
        nlat, nlon = 13, 24
        lat = np.linspace(-math.pi / 2, math.pi / 2, nlat)
        lon = np.linspace(-math.pi, math.pi, nlon, endpoint=False)
        LA, LO = np.meshgrid(lat, lon, indexing="ij")
        b = np.stack([np.cos(LA) * np.cos(LO), np.cos(LA) * np.sin(LO), np.sin(LA)], -1).reshape(-1, 3)
        A = np.eye(3) if body.axes is None else np.asarray(body.axes, float)
        V = body.radius * b @ A.T
        tri = []
        for i in range(nlat - 1):
            for j in range(nlon):
                a, bb, c, d = i * nlon + j, i * nlon + (j + 1) % nlon, (i + 1) * nlon + j, (i + 1) * nlon + (j + 1) % nlon
                tri += [(a, bb, d), (a, d, c)]
    elif body.kind == "box":
        h = np.asarray(body.half, float)
        A = np.eye(3) if body.axes is None else np.asarray(body.axes, float)
        V, tri = [], []
        for ax in range(3):
            for sgn in (1.0, -1.0):
                o1, o2 = [k for k in range(3) if k != ax]
                k1 = int(np.clip(round(4 * h[o1] / h.min()) + 1, 3, 17))
                k2 = int(np.clip(round(4 * h[o2] / h.min()) + 1, 3, 17))
                base = len(V)
                for i in range(k1):
                    for j in range(k2):
                        q = np.zeros(3)
                        q[ax] = sgn * h[ax]
                        q[o1] = -h[o1] + 2 * h[o1] * i / (k1 - 1)
                        q[o2] = -h[o2] + 2 * h[o2] * j / (k2 - 1)
                        V.append(A @ q)
                for i in range(k1 - 1):
                    for j in range(k2 - 1):
                        a, bb, c, d = base + i * k2 + j, base + i * k2 + j + 1, base + (i + 1) * k2 + j, base + (i + 1) * k2 + j + 1
                        tri += [(a, bb, d), (a, d, c)]
        V = np.array(V)
    else:
        hu, hv = (min(float(x), 100.0) for x in body.half)
        ku = int(min(81, 2 * round(hu / body.cell) + 1))
        kv = int(min(81, 2 * round(hv / body.cell) + 1))
        S, Tt = np.meshgrid(np.linspace(-hu, hu, ku), np.linspace(-hv, hv, kv), indexing="ij")
        V = (S[..., None] * np.asarray(body.u) + Tt[..., None] * np.asarray(body.v)).reshape(-1, 3)
        tri = []
        for i in range(ku - 1):
            for j in range(kv - 1):
                a, bb, c, d = i * kv + j, i * kv + j + 1, (i + 1) * kv + j, (i + 1) * kv + j + 1
                tri += [(a, bb, d), (a, d, c)]
    V = np.asarray(V, float)
    # the temperature of each vertex: a point just inside the surface along the vertex (patterns are rest-frame)
    Tk = RT.surface_temperature(body, V * (1 - 1e-9))
    return V, np.asarray(tri, np.uint32), Tk


def _deflate(a):
    return np.frombuffer(zlib.compress(np.ascontiguousarray(a).tobytes(), 6), np.uint8)


def _sub_filter(q):
    """Differences along each row (uint16 arithmetic modulo 2^16; the first sample of a row kept): smooth fields
    deflate about three times smaller (the player sums them back)."""
    q = q.astype(np.uint16)
    out = q.copy()
    out[:, 1:] = q[:, 1:] - q[:, :-1]
    return out


class Simulation(BaseSimulation):
    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = p = dict(params)
        self._buf = []
        self.scene, x0 = build_scene(p, self.rng)
        self.kind = p["scene"]
        self.moving = [i for i, b in enumerate(self.scene.bodies) if np.any(np.asarray(b.velocity) != 0)]
        self.live = {k: p[k] for k in SCHEMA.live_ids()}
        u0 = self._u_of(self.live)
        self.segments = [(0.0, np.asarray(x0, float), u0, 0.0)]  # (t start, x at start, u, proper time at start)
        self.table = CO.BlackbodyXYZ()
        temps = [float(t) for b in self.scene.bodies for t in (b.temps if hasattr(b, "temps") else ())]
        if self.scene.sky is not None:
            temps.append(self.scene.sky)
        self.T_ref = float(np.median(temps)) if temps else 5500.0
        self.Y_ref = float(self.table(np.array([self.T_ref]))[0, 1])
        self.meshes = {}
        for i, b in enumerate(self.scene.bodies):
            V, tri, Tk = mesh_of(b)
            self.meshes[i] = (V, tri, Tk)
        self.box = self._initial_box()
        span = max(self.box[1][k] - self.box[0][k] for k in range(3))
        # ~30 s of play for the bodies to cross 40 m (the fly-by), or for light to cross the scene 1.2 times
        bb = float(p.get("beta", 0.0)) if self.moving else 0.0
        self.default_speed = 40.0 / (bb * C) / 30.0 if bb > 0 else 1.2 * span / C / 30.0
        self.speed_range = (self.default_speed / 1000.0, self.default_speed * 100.0)
        self.seq = 0
        self.frames_since_img = 0
        self.last_img_t = None
        self.force_image = True
        self.force_checks = True
        self.worst = {}
        self.inside = None
        self._static_checks()
        self._energy_check(self.observer(0.0))
        self._render_image()  # buffered with the other messages of the start; the header then reports its device
        self.force_image = False

    # --- the observer's worldline (piecewise uniform: the live boosts) -------------------------------------------------
    def _u_of(self, live):
        return float(live["obs_beta"]) * C * _unit_dir(float(live["obs_theta"]), float(live["obs_phi"]))

    def _obs_state(self, t):
        t0, x0, u, tau0 = self.segments[-1]
        for seg in reversed(self.segments):
            if seg[0] <= t:
                t0, x0, u, tau0 = seg
                break
        g = float(LZ.gamma_of(u, C))
        return x0 + u * (t - t0), u, tau0 + (t - t0) / g, g

    def observer(self, t=None):
        t = self.t if t is None else t
        x, u, _, _ = self._obs_state(t)
        return RT.Observer(float(t), tuple(map(float, x)), tuple(map(float, u)))

    def camera(self, live=None):
        lv = self.live if live is None else live
        f = _look(float(lv["yaw"]), float(lv["pitch"]))
        up = np.array([0.0, 1.0, 0.0])
        if lv["camera"] == "sky":
            W, H = SKY_RES[lv["res"]]
            return RT.Camera(W, H, kind="sky", forward=tuple(f), up=tuple(up))
        W, H = RES[lv["res"]]
        return RT.Camera(W, H, kind="pinhole", fov=float(lv["fov"]), forward=tuple(f), up=tuple(up))

    # --- the region of the 3-D view --------------------------------------------------------------------------------------
    def _initial_box(self):
        pts = [np.asarray(self.segments[0][1])]
        for i, b in enumerate(self.scene.bodies):
            V = self.meshes[i][0]
            if b.kind == "panel":
                continue
            pts += list(RT.lab_points(b, V, 0.0, C))
        P = np.array(pts)
        lo, hi = P.min(0) - 3.0, P.max(0) + 3.0
        for b in self.scene.bodies:
            if b.kind == "panel":
                lo[1] = min(lo[1], b.center[1] - 0.5)
        if self.kind == "sky":
            lo, hi = np.full(3, -10.0), np.full(3, 10.0)
        return (tuple(map(float, lo)), tuple(map(float, hi)))

    def _grow_box(self, pts):
        lo, hi = np.array(self.box[0]), np.array(self.box[1])
        size = hi - lo
        grown = False
        for P in pts:
            for k in range(3):
                if P[k] > hi[k] - 0.05 * size[k]:
                    hi[k] += size[k]
                    grown = True
                if P[k] < lo[k] + 0.05 * size[k]:
                    lo[k] -= size[k]
                    grown = True
        if grown:
            self.box = (tuple(map(float, lo)), tuple(map(float, hi)))
            self.emit({"type": "box", "t": self.t, "box": [list(self.box[0]), list(self.box[1])]})

    # --- checks -----------------------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False, group=None):
        group = T("What is seen") if group is None else group
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
        """At rest (all velocities zero): the tracer equals plain ray casting."""
        if self.moving or float(self.live["obs_beta"]) != 0.0:
            return
        if not self.scene.bodies:
            return
        cam = self.camera()
        ob = self.observer(0.0)
        try:
            r = RT.render(self.scene, ob, cam, c=C, check=True)
        except ValueError:
            return
        who, s = RT.static_render(self.scene, ob.x, cam.directions())
        same = bool(np.array_equal(np.where(r["body"] >= 0, r["body"], -1), who))
        f = np.isfinite(s)
        err = float(np.max(np.abs(r["s"][f] - s[f]) / s[f])) if f.any() else 0.0
        self._check("rest_equal", T("Scene at rest: the tracer against ordinary rays (distances, relative)"), err, 0.0,
                    "", tol=4 * EPS, ok=same and err <= 4 * EPS, group=T("Check of the tracer"),
                    note=T("without velocities the Lorentz transformations are identities: the same bodies in {n:d} "
                           "pixels, the same distances; the bodies agree: {same}", n=int(f.sum()),
                           same=T("yes") if same else T("no")))

    def _image_checks(self, ob, r, cam, final=False):
        """Checks of one image against closed forms: the sky's temperature, the stars' directions, emission times and
        Doppler factors of the bodies (lorentz.retarded_time), Penrose's circle for every moving sphere."""
        out = []
        gu = float(LZ.gamma_of(np.asarray(ob.u), C)) ** 2
        if self.scene.sky is not None:
            m = r["body"] == -1
            if m.any():
                ref = RT.ref_sky_temperature(self.scene.sky, ob.u, cam.directions()[m], C)
                err = float(np.max(np.abs(r["T_obs"][m] / ref - 1)))
                out.append(("sky_T", T("Sky: the temperature in every pixel against T/(γ(1 − β cos θ′))"), err,
                            16 * EPS * gu, T("{n:d} pixels; γ² = {g2:.4g}; tolerance 16 ε γ² (the round-off of the "
                                             "boosts)", n=int(m.sum()), g2=gu)))
        if self.scene.stars:
            st = RT.star_images(self.scene, ob, C)
            s = np.array([x[0] for x in self.scene.stars])
            ref = RT.ref_aberration(s, ob.u, C)
            a = np.arctan2(np.linalg.norm(np.cross(st["d"], ref), axis=1), np.sum(st["d"] * ref, 1))
            out.append(("stars", T("Stars: the directions seen against the aberration formula, rad"), float(a.max()),
                        16 * EPS * gu, T("{n:d} stars; cos θ′ = (cos θ + β)/(1 + β cos θ)", n=len(s))))
        for ib in self.moving:
            body = self.scene.bodies[ib]
            m = r["body"] == ib
            if not m.any():
                continue
            te, _, D = RT.retarded_points(body, r["q"][m], ob, C)
            g2 = gu * float(LZ.gamma_of(np.asarray(body.velocity), C)) ** 2
            e_t = float(np.max(np.abs(te - r["t_emit"][m]) / np.maximum(ob.t - te, 1e-300)))
            e_d = float(np.max(np.abs(D / r["D"][m] - 1)))
            out.append((f"ret_{ib}", T("{body}: the emission time and the factor D against the retarded time",
                                       body=body.name),
                        max(e_t, e_d), 64 * EPS * g2,
                        T("{n:d} pixels: emission time (relative to the light's travel time) {et:.1e}, D {ed:.1e}; "
                          "reference: lorentz.retarded_time for the point of the body found and "
                          "D = γ_o(1 − u·n)/(γ_b(1 − v·n))", n=int(m.sum()), et=e_t, ed=e_d)))
        heavy = final or self.seq <= 1 or self.seq % 20 == 0 or self.force_checks
        self.force_checks = False
        for ib in (self.moving if heavy else []):
            body = self.scene.bodies[ib]
            if body.kind != "sphere":
                continue
            try:
                dirs, br = RT.outline(RT.Scene(self.scene.bodies), ob, ib, C)
            except ValueError:
                continue
            _, _, dev = RT.circle_fit(dirs)
            mr, rr, _ = RT.circle_fit(RT.penrose_reference(body, ob, C))
            cross = float(np.max(np.abs(np.arctan2(np.linalg.norm(np.cross(dirs, mr), axis=1), dirs @ mr) - rr)))
            P = np.linalg.norm((LZ.boost(np.asarray(body.velocity), C) @
                                np.r_[C * ob.t, np.asarray(ob.x) - np.asarray(body.center)])[1:])
            tol = 64 * EPS * gu * float(LZ.gamma_of(np.asarray(body.velocity), C)) ** 2 * (1 + P / body.radius)
            out.append((f"penrose_{ib}", T("{body}: the outline is a circle (Penrose), rad", body=body.name),
                        max(dev, cross), tol,
                        T("the outline found by bisection along the tracer's rays (64 rays); deviation from a circle "
                          "{dev:.1e}, from the circle of lorentz.sphere_outline {cross:.1e}; angular radius {r:.4g}°",
                          dev=float(dev), cross=cross, r=math.degrees(rr))))
        for cid, label, val, tol, note in out:
            prev = self.worst.get(cid)
            if final or prev is None or val > 2 * prev[0] or (val > tol) != (prev[0] > prev[1]):
                self.worst[cid] = (max(val, prev[0] if prev else 0.0), tol)
                w, wt = self.worst[cid]
                self._check(cid, label, w, 0.0, "", tol=wt, ok=w <= wt,
                            note=T("{note} (the worst value over the frames of this world)", note=note))

    def _energy_check(self, ob):
        """The sky camera of the sky scene: (1/4 pi) int (T'/T)^4 dOmega' against gamma^2 (1 + beta^2/3), with the
        quadrature error estimated from the half resolution (Richardson)."""
        cam = self.camera()
        if self.kind != "sky" or cam.kind != "sky":
            return
        sky = RT.Scene([], sky=1.0)
        vals = []
        for f in (1, 2):
            cm = RT.Camera(cam.width // f, cam.height // f, kind="sky", forward=cam.forward, up=cam.up)
            r = RT.render(sky, ob, cm, c=C, check=True)
            vals.append(float(np.sum(r["T_obs"] ** 4 * cm.solid_angles()) / (4 * math.pi)))
        b = float(np.linalg.norm(ob.u) / C)
        ref = RT.ref_energy_density_factor(b)
        tol = abs(vals[0] - vals[1]) / ref + 1e-12
        self._check("energy", T("Energy density of the sky for the observer / at rest"), vals[0], ref, "", tol=tol,
                    note=T("the sum of (T′/T)⁴ over the pixels with exact solid angles against γ²(1 + β²/3) (the "
                           "searchlight effect, integrated); tolerance: the quadrature's error estimated from half the "
                           "resolution ({half:.8g})", half=vals[1]))

    # --- the image ---------------------------------------------------------------------------------------------------
    def _colours(self, r, mode, cam, ob):
        """sRGB of the image, the stars splatted where the image shows light."""
        if mode in ("doppler", "delay"):
            return self._false_colour(r, mode)
        Tk = r["T_obs"] if mode == "seen" else r["T_rest"]
        Tk = np.where(np.isfinite(Tk), Tk, 0.0)
        XYZ = self.table(Tk)
        if mode != "snapshot" and self.scene.stars:
            st = RT.star_images(self.scene, ob, C)
            ci, rj = cam.pixel_of(st["d"])
            ks = np.flatnonzero(~st["hidden"] & np.isfinite(ci))
            if len(ks):
                Dk = st["D"][ks] if mode == "seen" else np.ones(len(ks))
                # a star's colour is the black body at D T; its flux D^2 times that at rest (radiance D^4, solid angle
                # D^-2): one pixel as bright as a surface of its rest temperature, times D^2 / D^4 of the radiance
                add = self.table(st["T"][ks] * Dk) / (Dk ** 2)[:, None]
                i = np.clip(np.round(ci[ks]).astype(int), 0, cam.width - 1)
                j = np.clip(np.round(rj[ks]).astype(int), 0, cam.height - 1)
                np.add.at(XYZ, (j, i), add)
        if self.live["exposure"] == "auto":
            Y = XYZ[..., 1]
            Yp = float(np.percentile(Y[Y > 0], 99)) if np.any(Y > 0) else 1.0
            k = 1.5 / max(Yp, 1e-300)
        else:
            k = 1.0 / self.Y_ref
        k *= 2.0 ** float(self.live["ev"])
        return CO.to_display(XYZ, k), k

    def _false_colour(self, r, mode):
        if mode == "doppler":
            x = np.log2(np.where(np.isfinite(r["D"]), r["D"], 1.0))
            f = np.clip(0.5 + x / 6.0, 0, 1)[..., None]  # D from 1/8 (red) through 1 (grey) to 8 (blue)
            red, grey, blue = np.array([0.85, 0.15, 0.1]), np.array([0.82, 0.82, 0.82]), np.array([0.1, 0.3, 0.95])
            rgb = np.where(f < 0.5, red + (grey - red) * (2 * f), grey + (blue - grey) * (2 * f - 1))
        else:
            d = (self.t - r["t_emit"]) / NS
            d = np.where(np.isfinite(d), d, np.nan)
            mx = float(np.nanmax(d)) if np.isfinite(d).any() else 1.0
            f = np.clip(np.nan_to_num(d / max(mx, 1e-30), nan=1.0), 0, 1)
            rgb = np.stack([f, 0.25 + 0.5 * (1 - np.abs(2 * f - 1)), 1 - f], -1)
        rgb = np.where((r["body"] == -2)[..., None], 0.0, rgb)
        return np.round(255 * CO.srgb_encode(rgb)).astype(np.uint8), 1.0

    def _render_image(self, final=False):
        ob = self.observer()
        cam = self.camera()
        mode = self.live["image"]
        try:
            r = RT.render(self.scene, ob, cam, c=C)
            dev = B.used().get(RT.KERNEL, {}).get("drawn")  # the image's own device (review B3-8)
            snap = RT.render(self.scene, ob, cam, c=C, mode="snapshot") if mode == "snapshot" else None
        except ValueError as e:
            if self.inside != str(e):
                self.inside = str(e)
                self._msg({"type": "notice", "t": self.t, "text": T("{error} (t = {t:.4g} ns)", error=text_of(e),
                                                                     t=self.t / NS)})
            return
        self.inside = None
        shown = snap if snap is not None else r
        rgb, k = self._colours(shown, mode, cam, ob)
        H, W = r["body"].shape
        D = np.where(np.isfinite(shown["D"]), shown["D"], 0.0)
        Dq = np.where(D > 0, np.round((np.log2(np.maximum(D, 2.0**-16)) + 16) / 32 * 65534) + 1, 0).astype(np.uint16)
        delay = np.where(np.isfinite(r["t_emit"]) & (snap is None), self.t - r["t_emit"], np.nan)
        dmax = float(np.nanmax(delay)) if np.isfinite(delay).any() else 0.0
        dq = np.where(np.isfinite(delay), np.round(delay / max(dmax, 1e-300) * 65534) + 1, 0).astype(np.uint16)
        Tq = np.round(np.nan_to_num(shown["T_rest"], nan=0.0)).clip(0, 65535).astype(np.uint16)
        body = shown["body"].astype(np.int8)
        # the retarded shapes of the moving bodies and their observed colours (visible points bright)
        ret_meta, ret_pos, ret_rgb = [], [], []
        for ib in self.moving:
            body_ = self.scene.bodies[ib]
            V, _, Tk = self.meshes[ib]
            te, xe, Dv = RT.retarded_points(body_, V, ob, C)
            dirs = RT.look_direction(ob, xe, C)
            tr = RT.trace_directions(self.scene, ob, dirs, C, aux=True)
            dist = np.linalg.norm(xe - np.asarray(ob.x), axis=1)
            vis = (tr["body"] == ib) & (np.abs(tr["s"] - dist) <= 1e-6 * dist)
            Tv = Tk * Dv if mode == "seen" else Tk
            col = CO.to_display(self.table(Tv), k).astype(float)
            col = np.where(vis[:, None], col, 0.3 * col + 40)
            ret_meta.append({"id": f"ret{ib}", "from": int(sum(len(x) for x in ret_pos)), "count": int(len(V)),
                             "visible": int(vis.sum())})
            ret_pos.append(xe.astype(np.float32))
            ret_rgb.append(np.clip(col, 0, 255).astype(np.uint8))
        self.seq += 1
        meta = {"type": "image", "t": self.t, "id": "camera", "seq": self.seq, "shape": [H, W],
                "camera": {"kind": cam.kind, "fov": cam.fov, "forward": list(cam.forward)},
                "mode": mode, "mode_label": dict(IMAGES)[mode], "exposure": k, "ev": float(self.live["ev"]),
                "auto": self.live["exposure"] == "auto", "codec": "deflate", "filter": {"D": "sub", "delay": "sub"},
                "delay_max": dmax,
                "observer": {"x": list(ob.x), "beta": [float(c) / C for c in ob.u],
                             "gamma": float(LZ.gamma_of(np.asarray(ob.u), C))},
                "bodies": [b.name for b in self.scene.bodies], "sky_T": self.scene.sky, "retarded": ret_meta,
                "device": dev,
                "fields": {"D": "log2(D) = (v - 1)/65534*32 - 16; 0: no light",
                           "delay": "delay = (v - 1)/65534*delay_max; 0: the light is not from a body",
                           "T": "rest temperature, K (rounded)", "body": "body number; -1 sky; -2 nothing"}}
        blobs = {"rgb": _deflate(rgb), "D": _deflate(_sub_filter(Dq)), "delay": _deflate(_sub_filter(dq)), "T": _deflate(Tq),
                 "body": _deflate(body)}
        if ret_pos:
            blobs["ret_pos"] = np.concatenate(ret_pos)
            blobs["ret_rgb"] = np.concatenate(ret_rgb)
        self._msg(meta, blobs)
        self._image_checks(ob, r, cam, final)
        self.last_img_t = self.t
        self.frames_since_img = 0

    # --- messages ---------------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def after_header(self):
        buf, self._buf = self._buf, []
        static = {"pos": [], "idx": [], "rgb": [], "n": 0, "names": []}
        for i, b in enumerate(self.scene.bodies):
            V, tri, Tk = self.meshes[i]
            rgb = CO.to_display(self.table(Tk), 1.0 / self.Y_ref)
            if i not in self.moving and b.kind != "panel":
                # bodies at rest (towers, posts): one layer
                static["pos"].append(RT.lab_points(b, V, 0.0, C))
                static["idx"].append(tri + static["n"])
                static["rgb"].append(rgb)
                static["n"] += len(V)
                static["names"].append(b.name)
                continue
            self._msg({"type": "mesh", "t": self.t, "id": f"body{i}", "count": int(len(V)),
                       "label": T("{body}: in the lab now (contracted)", body=b.name) if i in self.moving else
                       T("{body}: in the lab now", body=b.name),
                       "opacity": 0.35 if i in self.moving else 0.5,
                       "base": "rest" if i in self.moving else "lab"},
                      {"pos": (V if i in self.moving else RT.lab_points(b, V, 0.0, C)).astype(np.float32),
                       "idx": tri, "rgb": rgb})
            if i in self.moving:
                self._msg({"type": "mesh", "t": self.t, "id": f"ret{i}", "count": int(len(V)),
                           "label": T("{body}: where the light seen now came from", body=b.name), "opacity": 1.0,
                           "base": "lab"},
                          {"pos": RT.lab_points(b, V, 0.0, C).astype(np.float32), "idx": tri, "rgb": rgb})
        if static["n"]:
            kinds = T("towers") if self.kind == "city" else (T("posts") if self.kind == "train" else T("bodies"))
            self._msg({"type": "mesh", "t": self.t, "id": "static", "count": int(static["n"]),
                       "label": T("{kinds} at rest ({n:d})", kinds=kinds, n=len(static["names"])), "opacity": 0.85,
                       "base": "lab"},
                      {"pos": np.concatenate(static["pos"]).astype(np.float32),
                       "idx": np.concatenate(static["idx"]).astype(np.uint32), "rgb": np.concatenate(static["rgb"])})
        # the meshes first (the 3-D scene), then what was computed at the start (checks, the first image)
        buf, self._buf = self._buf + buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    # --- time ----------------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        self.t = t_target
        if self.force_image or (self.last_img_t != self.t and self.frames_since_img >= IMG_FRAMES):
            self._render_image()
            self.force_image = False
        x, _, _, _ = self._obs_state(self.t)
        pts = [x] + [RT.lab_points(self.scene.bodies[i], np.zeros(3), self.t, C) for i in self.moving]
        self._grow_box(pts)

    def _cone(self, ob, cam):
        """Lab directions from which the light at the image's border arrives (the field of view seen in the lab);
        recomputed only when the camera or the observer's velocity changes."""
        if cam.kind == "sky":
            return []
        key = (cam, tuple(ob.u))
        if getattr(self, "_cone_key", None) == key:
            return self._cone_val
        self._cone_key, self._cone_val = key, self._cone_of(ob, cam)
        return self._cone_val

    def _cone_of(self, ob, cam):
        d = cam.directions()
        H, W = d.shape[:2]
        idx = [(0, i) for i in range(0, W, max(1, W // 12))] + [(j, W - 1) for j in range(0, H, max(1, H // 9))] + \
              [(H - 1, i) for i in range(W - 1, -1, -max(1, W // 12))] + [(j, 0) for j in range(H - 1, -1, -max(1, H // 9))]
        dd = np.array([d[j, i] for j, i in idx])
        K = np.concatenate([np.ones((len(dd), 1)), -dd], axis=1) @ LZ.boost(-np.asarray(ob.u), C).T
        return (-K[:, 1:] / K[:, :1]).tolist()

    def frame(self):
        self.frames_since_img += 1
        x, u, tau, g = self._obs_state(self.t)
        ob = RT.Observer(self.t, tuple(x), tuple(u))
        cam = self.camera()
        bodies = []
        for i in self.moving:
            b = self.scene.bodies[i]
            beta = np.asarray(b.velocity) / C
            gg = float(LZ.gamma_of(beta))
            A = np.eye(3) - (gg / (gg + 1.0)) * np.outer(beta, beta)
            bodies.append({"id": f"body{i}", "A": A.ravel().tolist(),
                           "b": (np.asarray(b.center) + np.asarray(b.velocity) * self.t).tolist()})
        return {"t_ns": self.t / NS, "tau_ns": tau / NS, "obs": {"x": x.tolist(), "beta": (u / C).tolist(),
                                                                 "gamma": g, "fwd": list(cam.forward)},
                "cone": self._cone(ob, cam), "bodies": bodies, "img_seq": self.seq}, {}

    def next_event_time(self):
        return None

    # --- live set-up ------------------------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        merged, errors = SCHEMA.coerce_live(self.live, values)
        if errors:
            raise Refusal(join(errors))
        u_new = self._u_of(merged)
        x, u_old, tau, _ = self._obs_state(self.t)
        cam = self.camera(merged)  # refuses a bad camera before anything changes
        cam.directions()
        if not np.allclose(u_new, u_old, rtol=0, atol=1e-12 * C):
            self.segments = [s for s in self.segments if s[0] < self.t] + [(self.t, x, u_new, tau)]
        self.live = merged
        self.force_checks = True
        self.worst = {}
        if self.kind == "sky":
            self._energy_check(self.observer())
        # the image changes at once (also while the world stands): the same light, seen with the new set-up
        self._render_image()
        self.force_image = False
        b = float(np.linalg.norm(u_new) / C)
        obs = T("observer: β = {b:.4g} along {dir}", b=b, dir=_vec(u_new / max(b * C, 1e-300))) if b > 0 else \
            T("observer: at rest (β = 0)")
        return T("{observer}; camera: {camera}, view {fwd}; image: {image}", observer=obs,
                 camera=dict(CAMERAS)[merged["camera"]], fwd=_vec(cam.forward), image=dict(IMAGES)[merged["image"]])

    def engine_modules(self):
        return ["core.raytrace", "core.lorentz", "core.optics.radiation", "core.backend", "tools.colour"]

    def header(self):
        p = self.params
        b = float(p.get("beta", 0.0)) if self.kind in ("flyby", "train") else 0.0
        cx = [0.5 * (self.box[0][k] + self.box[1][k]) for k in range(3)]
        objects = []
        views = [["iso", T("Iso"), T("Isometric (F)")], ["side", T("Side"), T("View along the x axis")],
                 ["top", T("Top"), T("View from above (along the y axis)")],
                 ["beam", T("From behind the observer"), T("Along the z axis")],
                 ["back", T("Facing"), T("Against the z axis")]]
        names = {i: bb.name for i, bb in enumerate(self.scene.bodies)}
        return {
            "title": T("What a fast observer sees: {scene}", scene=dict(SCENES)[self.kind]),
            "text": T("The image is computed by ray tracing with the light's travel time: every pixel is a photon, "
                      "Lorentz-transformed (aberration); its past light ray is followed back to the body that emitted "
                      "it (the Terrell–Penrose rotation), and the light is seen as a black body at the temperature D·T "
                      "(the Doppler colour and the searchlight brightness, exactly). The 3-D view shows the lab now: "
                      "the bodies Lorentz-contracted and the places the light seen now came from."),
            "actions": [],
            "scene3d": {"box": [list(self.box[0]), list(self.box[1])], "units": T("m"), "objects": objects,
                        "layers": [], "views": views,
                        "planes": {"max": 0, "center": cx, "defaults": {"1": [0, 1, 0], "2": [1, 0, 0], "3": [0, 0, 1]}}},
            "bodies": [{"id": i, "name": names[i], "kind": bb.kind, "beta": (np.asarray(bb.velocity) / C).tolist(),
                        "moving": i in self.moving} for i, bb in enumerate(self.scene.bodies)],
            "scene": {"kind": self.kind, "beta_bodies": b, "sky_T": self.scene.sky, "stars": len(self.scene.stars),
                      "T_ref": self.T_ref, "c": C},
            "units": {"t": T("s (lab time; the scene lasts hundreds of nanoseconds)"), "x": T("m")},
        }, {}


VIZ = {
    "id": "v10_fast_observer",
    "title": T("What a fast observer sees"),
    "summary": T("The image of a 3-D scene for an observer or bodies at speeds close to c: ray tracing with the light's "
                 "travel time — aberration, the Terrell–Penrose rotation (the ball stays a circle), Doppler colours and "
                 "the searchlight brightness; in 3-D, the bodies in the lab and the places the light seen came from."),
    "purpose": T("To show that fast bodies do not look flattened (the Lorentz contraction is not seen, a rotation is), "
                 "and that a fast observer sees the world crowded forward, blue and bright ahead."),
    "version": "1.0",
    "schema": SCHEMA,
    "simulation": Simulation,
}
