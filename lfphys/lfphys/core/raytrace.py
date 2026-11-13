# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""What an observer moving with any velocity sees: light-time ray tracing of a 3-D scene (plan P9 and P14.2).

Lab coordinates (ct, x, y, z), metric diag(1, -1, -1, -1), ``c`` as in ``lfphys.core.lorentz`` (default 1).

* **Bodies** are rigid in their own rest frames and move uniformly: a body with lab velocity v whose centre passes
  c0 at lab time 0 occupies the world tube {Lambda(-v) (c tau, q) + (0, c0) : q in S}, S its rest-frame shape centred
  on the origin (sphere, box, flat rectangle). In the lab a body point q is at c0 + v t + q - gamma/(gamma + 1)
  (beta.q) beta at lab time t (Lorentz contraction along v; ``lab_points``).
* **The observer** is at the event (t_o, x_o) with lab velocity u; its camera looks along directions d' given in its
  rest frame (the axes of ``boost(u)``). The photon arriving from d' has the observer-frame wave vector k' = (1, -d')
  (energy 1) and the lab wave vector k = boost(-u) k': the aberration of every pixel is the Lorentz transformation of
  its photon.
* **The past light ray** of a pixel is X(s) = (c t_o - s, x_o - s n), n = k_sp / k_0 the photon's lab direction and
  s >= 0 the lab distance. In a body's rest frame it is the straight line p(s) = P + s Q (P the observation event's
  rest-frame position, Q the spatial part of boost(v) applied to -(1, n)); the photon left the body where this line
  first meets its surface (the smallest s >= 0: the most recent emission, which hides everything emitted earlier
  along the ray). Exact: a quadratic for a sphere, slabs for a box, a linear equation for a rectangle. The nearest
  emission over all bodies wins. Images at t_o use only light emitted at or before t_o, by construction.
* **Light**: every surface emits as a black body at a temperature T(q) of its rest-frame point (a pattern: a
  checkerboard of two temperatures, face temperatures of a box), with isotropic radiance in its rest frame. I_nu / nu^3
  is invariant, so the observer sees a black body at D T, D = nu_obs / nu_emit = (k . U_o) / (k . U_body) = k'_0 /
  (boost(v) k)_0: colour and brightness follow from D T exactly (the searchlight effect, radiance proportional to D^4,
  is contained). A uniform black-body sky at rest in the lab fills the directions that meet no body (D = 1 / k_0);
  point stars at infinity at rest in the lab are imaged by the same transformation (flux D^2 times).
* **For comparison only** (not what is seen): ``mode="snapshot"`` intersects the observer's simultaneity (the
  spacelike lines X_o + s boost(-u) (0, d')) instead of the past light cone — the Lorentz-contracted picture that light
  of finite speed never shows; it carries no Doppler factor.

References (``ref_*``: closed forms written without the 4 x 4 matrices, for the checks): the sky's temperature
T / (gamma (1 - beta cos theta')), the aberration cos theta' = (cos theta + beta) / (1 + beta cos theta), the energy
density of the sky seen moving gamma^2 (1 + beta^2 / 3); ``lfphys.core.lorentz.retarded_time`` (emission times) and
``sphere_outline`` (Penrose's circle). ``outline`` finds a sphere's apparent outline by bisection along rays of the
tracer (an independent route to Penrose's result); ``static_render`` casts plain rays through bodies at rest (the
tracer at zero velocities must equal it).

The heavy part (all pixels at once) runs on the CPU or on GPU 0 (``lfphys.core.backend``, kernel
"relativity.raytrace"); the results are returned as NumPy arrays.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.i18n import T
from lfphys.codes import coded

from . import backend
from . import lorentz as LZ

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("What a fast observer sees: ray tracing with light travel time"),
    "statement": T("The image of a scene for an observer at any speed: every pixel is a photon Lorentz-transformed "
                   "(aberration); its past light ray is intersected exactly with the world tubes of the bodies "
                   "(sphere, box, rectangle) in their rest frames (light travel time, the Terrell–Penrose rotation); "
                   "surfaces radiate as black bodies, the observer sees a black body at D·T (Doppler colour and the "
                   "searchlight effect exactly); the sky and the stars at infinity."),
    "validity": T("special relativity, flat spacetime; bodies rigid in their rest frames and moving uniformly; "
                  "radiation in equilibrium (a black body), isotropic in the body's frame; geometric optics (sizes "
                  "much larger than the wavelength)"),
    "basis": ["Penrose, Proc. Camb. Phil. Soc. 55, 137 (1959); Terrell, Phys. Rev. 116, 1041 (1959)",
              T("McKinley & Doherty, Am. J. Phys. 47, 309 (1979): the radiation of a moving black body, T' = D T"),
              T("Peebles & Wilkinson, Phys. Rev. 174, 2168 (1968): the dipole anisotropy of the background for a "
                "moving observer"),
              "Jackson, Classical Electrodynamics, 3rd ed. (1999), § 11.3"],
    "conflicts": [],
}

KERNEL = "relativity.raytrace"


# --- the scene -------------------------------------------------------------------------------------------------------
def _axes(a):
    A = np.eye(3) if a is None else np.asarray(a, float).reshape(3, 3)
    if np.max(np.abs(A.T @ A - np.eye(3))) > 1e-9:
        raise ValueError("body axes must be orthonormal")
    return A


@dataclass(frozen=True)
class Sphere:
    """A sphere of ``radius`` in its rest frame; a checkerboard of ``cells`` = (latitude bands, longitude sectors) in
    the two ``temps`` (K); ``axes``: the pattern's axes in the rest frame (columns; default the boost frame's)."""
    center: tuple
    radius: float
    velocity: tuple = (0.0, 0.0, 0.0)
    temps: tuple = (6500.0, 3500.0)
    cells: tuple = (6, 12)
    axes: tuple | None = None
    name: T | str = field(default_factory=lambda: T("sphere"), compare=False)
    kind = "sphere"


@dataclass(frozen=True)
class Box:
    """A rectangular box of half-sizes ``half`` along its ``axes`` (rest frame); face temperatures ``temps`` in the
    order +a1, -a1, +a2, -a2, +a3, -a3; each face a checkerboard of about ``cells`` squares along its longer side,
    alternate squares at ``alt`` times the face temperature."""
    center: tuple
    half: tuple
    velocity: tuple = (0.0, 0.0, 0.0)
    temps: tuple = (6000.0, 6000.0, 6000.0, 6000.0, 6000.0, 6000.0)
    alt: float = 0.75
    cells: int = 4
    axes: tuple | None = None
    name: T | str = field(default_factory=lambda: T("box"), compare=False)
    kind = "box"


@dataclass(frozen=True)
class Panel:
    """A flat rectangle through its centre spanned by the orthonormal rest-frame axes ``u``, ``v`` with half-sizes
    ``half`` (inf: unbounded), a checkerboard of squares of side ``cell`` in the two ``temps``; seen from both sides."""
    center: tuple
    u: tuple = (1.0, 0.0, 0.0)
    v: tuple = (0.0, 0.0, 1.0)
    half: tuple = (math.inf, math.inf)
    velocity: tuple = (0.0, 0.0, 0.0)
    temps: tuple = (5500.0, 3000.0)
    cell: float = 1.0
    name: T | str = field(default_factory=lambda: T("plane"), compare=False)
    kind = "panel"


@dataclass
class Scene:
    """Bodies; a uniform black-body sky at rest in the lab (temperature in K, or None: black); point stars at
    infinity at rest in the lab, as (lab direction towards the star, temperature)."""
    bodies: list
    sky: float | None = None
    stars: list = ()


@dataclass(frozen=True)
class Observer:
    """The observation event (t, x) and the observer's lab velocity u (same units as c)."""
    t: float
    x: tuple
    u: tuple = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Camera:
    """A camera in the observer's rest frame: ``kind`` "pinhole" (horizontal field of view ``fov`` degrees, < 180) or
    "sky" (equirectangular: the whole sphere, longitude across, latitude down); ``forward`` and ``up`` (observer
    frame). Pixel (i, j): column i from the left, row j from the top."""
    width: int
    height: int
    kind: str = "pinhole"
    fov: float = 90.0
    forward: tuple = (0.0, 0.0, 1.0)
    up: tuple = (0.0, 1.0, 0.0)

    def basis(self):
        f = np.asarray(self.forward, float)
        f = f / np.linalg.norm(f)
        r = np.cross(f, np.asarray(self.up, float))
        if np.linalg.norm(r) < 1e-12:
            raise coded(ValueError(T("the camera's up direction is parallel to its look direction")),
                        "raytrace.camera_up")
        r = r / np.linalg.norm(r)
        return r, np.cross(r, f), f

    def _angles(self):
        i = (np.arange(self.width) + 0.5) / self.width
        j = (np.arange(self.height) + 0.5) / self.height
        return np.meshgrid(i, j)  # (H, W)

    def directions(self):
        """(H, W, 3) unit look directions in the observer's frame."""
        r, up, f = self.basis()
        a, b = self._angles()
        if self.kind == "pinhole":
            if not 0 < self.fov < 179:
                raise ValueError(T("pinhole camera field of view: from 0 to 179°"))
            th = math.tan(math.radians(self.fov) / 2)
            x = (2 * a - 1) * th
            y = (1 - 2 * b) * th * self.height / self.width
            d = f + x[..., None] * r + y[..., None] * up
            return d / np.linalg.norm(d, axis=-1, keepdims=True)
        if self.kind == "sky":
            lon, lat = (2 * a - 1) * math.pi, (0.5 - b) * math.pi
            cl = np.cos(lat)[..., None]
            return cl * (np.sin(lon)[..., None] * r + np.cos(lon)[..., None] * f) + np.sin(lat)[..., None] * up
        raise ValueError(f"unknown camera {self.kind!r}")

    def solid_angles(self):
        """(H, W) exact solid angle of each pixel of a "sky" camera."""
        if self.kind != "sky":
            raise ValueError("pixel solid angles exist only for the whole-sky camera")
        lat_edges = math.pi * (0.5 - np.arange(self.height + 1) / self.height)
        band = np.sin(lat_edges[:-1]) - np.sin(lat_edges[1:])
        return np.repeat((band * 2 * math.pi / self.width)[:, None], self.width, axis=1)

    def pixel_of(self, d):
        """Fractional pixel coordinates (column, row; pixel centres at integers) of observer-frame look directions;
        NaN where a pinhole camera does not see them."""
        d = np.asarray(d, float)
        r, up, f = self.basis()
        x, y, z = d @ r, d @ up, d @ f
        if self.kind == "pinhole":
            th = math.tan(math.radians(self.fov) / 2)
            with np.errstate(divide="ignore", invalid="ignore"):
                ci = ((x / z) / th + 1) / 2 * self.width - 0.5
                rj = (1 - (y / z) / (th * self.height / self.width)) / 2 * self.height - 0.5
            ok = (z > 0) & (ci > -0.5) & (ci < self.width - 0.5) & (rj > -0.5) & (rj < self.height - 0.5)
            return np.where(ok, ci, np.nan), np.where(ok, rj, np.nan)
        lon, lat = np.arctan2(x, z), np.arcsin(np.clip(y, -1, 1))
        return (lon / math.pi + 1) / 2 * self.width - 0.5, (0.5 - lat / math.pi) * self.height - 0.5


# --- kinematics of bodies ----------------------------------------------------------------------------------------------
def lab_points(body, q, t, c: float = 1.0):
    """Lab positions at lab time t of body points given by their rest-frame offsets q from the centre (..., 3)."""
    q = np.asarray(q, float)
    b = np.asarray(body.velocity, float) / c
    g = float(LZ.gamma_of(b))
    contracted = q - (g / (g + 1.0)) * (q @ b)[..., None] * b
    return np.asarray(body.center, float) + np.asarray(body.velocity, float) * t + contracted


def retarded_points(body, q, observer: Observer, c: float = 1.0):
    """Where and when the light that reaches the observer at (t_o, x_o) left the body points q (rest-frame offsets):
    (t_e, x_e) by ``lorentz.retarded_time``, and the Doppler factor D = nu_obs / nu_emit of that light,
    gamma_o (1 - u.n / c) / (gamma_b (1 - v.n / c)) with n the lab direction from x_e to x_o."""
    q = np.asarray(q, float)
    xo = np.asarray(observer.x, float)
    x0 = lab_points(body, q, 0.0, c)
    v = np.asarray(body.velocity, float)
    te = LZ.retarded_time(x0 - xo, v, observer.t, c)
    xe = x0 + v * te[..., None]
    n = xo - xe
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    u = np.asarray(observer.u, float)
    D = LZ.gamma_of(u, c) * (1.0 - n @ u / c) / (LZ.gamma_of(v, c) * (1.0 - n @ v / c))
    return te, xe, D


def look_direction(observer: Observer, x_e, c: float = 1.0):
    """The observer-frame direction in which the observer at (t_o, x_o) sees light emitted at lab points x_e."""
    n = np.asarray(observer.x, float) - np.asarray(x_e, float)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    k = np.concatenate([np.ones(n.shape[:-1] + (1,)), n], axis=-1)
    kp = np.einsum("ij,...j->...i", LZ.boost(np.asarray(observer.u, float), c), k)
    return -kp[..., 1:] / kp[..., :1]


# --- intersections in a body's rest frame (P: the observation event, Q per ray) -----------------------------------------
def _hit_sphere(xp, body, P, Q):
    r = float(body.radius)
    cc = float(P @ P) - r * r
    if cc <= 0:
        raise ValueError(T("the observer is inside the body “{name}”: no image is built from inside", name=body.name))
    a = xp.sum(Q * Q, axis=-1)
    b = Q @ xp.asarray(P)
    disc = b * b - a * cc
    ok = (disc >= 0) & (b < 0)
    s = cc / (-b + xp.sqrt(xp.where(ok, disc, 0.0)))  # the near root, without cancellation
    return xp.where(ok, s, xp.inf)


def _hit_box(xp, body, P, Q):
    A = _axes(body.axes)
    h = np.asarray(body.half, float)
    Pb = A.T @ P
    if np.all(np.abs(Pb) < h):
        raise ValueError(T("the observer is inside the body “{name}”: no image is built from inside", name=body.name))
    Qb = Q @ xp.asarray(A)
    tn = xp.full(Q.shape[:-1], -xp.inf)
    tf = xp.full(Q.shape[:-1], xp.inf)
    for i in range(3):
        qi = Qb[..., i]
        small = xp.abs(qi) < 1e-300
        qs = xp.where(small, 1e-300, qi)
        with np.errstate(over="ignore", invalid="ignore"):
            t1, t2 = (-h[i] - Pb[i]) / qs, (h[i] - Pb[i]) / qs
        lo, hi = xp.minimum(t1, t2), xp.maximum(t1, t2)
        inside = abs(Pb[i]) <= h[i]
        lo = xp.where(small, -xp.inf if inside else xp.inf, lo)
        hi = xp.where(small, xp.inf if inside else -xp.inf, hi)
        tn, tf = xp.maximum(tn, lo), xp.minimum(tf, hi)
    return xp.where((tn <= tf) & (tn >= 0), tn, xp.inf)


def _hit_panel(xp, body, P, Q):
    u, v = np.asarray(body.u, float), np.asarray(body.v, float)
    nrm = np.cross(u, v)
    num = -float(P @ nrm)
    den = Q @ xp.asarray(nrm)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = num / xp.where(den == 0, xp.nan, den)
    p = xp.asarray(P) + s[..., None] * Q
    ok = (s > 0) & (xp.abs(p @ xp.asarray(u)) <= body.half[0]) & (xp.abs(p @ xp.asarray(v)) <= body.half[1])
    return xp.where(ok, s, xp.inf)


_HIT = {"sphere": _hit_sphere, "box": _hit_box, "panel": _hit_panel}


def _pattern(xp, body, q):
    """Rest-frame temperature of the surface points q (rest-frame offsets from the centre)."""
    if body.kind == "sphere":
        A = _axes(body.axes)
        b = q @ xp.asarray(A) / float(body.radius)
        lat = xp.arcsin(xp.clip(b[..., 2], -1.0, 1.0))
        lon = xp.arctan2(b[..., 1], b[..., 0])
        i = xp.floor((lat + math.pi / 2) / math.pi * body.cells[0])
        j = xp.floor((lon + math.pi) / (2 * math.pi) * body.cells[1])
        return xp.where((i + j) % 2 == 0, float(body.temps[0]), float(body.temps[1]))
    if body.kind == "box":
        A = _axes(body.axes)
        h = np.asarray(body.half, float)
        b = q @ xp.asarray(A)
        rel = xp.abs(b) / xp.asarray(h)
        face = xp.argmax(rel, axis=-1)
        bf = xp.take_along_axis(b, face[..., None], axis=-1)[..., 0]
        T = xp.asarray(np.asarray(body.temps, float))[2 * face + (bf < 0)]
        n = np.maximum(1, np.round(body.cells * h / h.max()))
        size = 2 * h / n
        k = xp.floor((b + xp.asarray(h)) / xp.asarray(size))
        par = (xp.sum(k, axis=-1) - xp.take_along_axis(k, face[..., None], axis=-1)[..., 0]) % 2
        return xp.where(par == 0, T, float(body.alt) * T)
    u, v = np.asarray(body.u, float), np.asarray(body.v, float)
    a = xp.floor((q @ xp.asarray(u)) / body.cell)
    b = xp.floor((q @ xp.asarray(v)) / body.cell)
    return xp.where((a + b) % 2 == 0, float(body.temps[0]), float(body.temps[1]))


def surface_temperature(body, q):
    """Rest-frame temperature (K) of a body's surface points q (rest-frame offsets from the centre, (..., 3))."""
    return _pattern(np, body, np.asarray(q, float))


# --- the tracer ----------------------------------------------------------------------------------------------------------
def _trace(xp, scene: Scene, observer: Observer, d, c: float, mode: str, only=None):
    """All pixels at once on the array module xp; d: observer-frame look directions (..., 3) on xp."""
    u = np.asarray(observer.u, float)
    Xo = np.concatenate([[c * float(observer.t)], np.asarray(observer.x, float)])
    Bu_inv = xp.asarray(LZ.boost(-u, c))
    if mode == "seen":
        kp = xp.concatenate([xp.ones(d.shape[:-1] + (1,)), -d], axis=-1)
        k = kp @ Bu_inv.T          # lab wave vector, observer-frame energy 1
        k0 = k[..., 0]
        K = -k / k0[..., None]      # the past light ray's direction: -(1, n)
    elif mode == "snapshot":
        K = xp.concatenate([xp.zeros(d.shape[:-1] + (1,)), d], axis=-1) @ Bu_inv.T
        k0 = None
    else:
        raise ValueError(f"unknown mode {mode!r}")
    best = xp.full(d.shape[:-1], xp.inf)
    who = xp.full(d.shape[:-1], -1, dtype=xp.int32)
    cache = {}
    per_body = []
    for ib, body in enumerate(scene.bodies):
        if only is not None and ib not in only:
            per_body.append(None)
            continue
        v = tuple(float(x) for x in body.velocity)
        if v not in cache:
            Bv = LZ.boost(np.asarray(v), c)
            cache[v] = (Bv, K @ xp.asarray(Bv).T)
        Bv, KB = cache[v]
        P = (Bv @ (Xo - np.concatenate([[0.0], np.asarray(body.center, float)])))[1:]
        Q = KB[..., 1:]
        s = _HIT[body.kind](xp, body, P, Q)
        per_body.append((P, v))
        closer = s < best
        best = xp.where(closer, s, best)
        who = xp.where(closer, ib, who)
    hit = xp.isfinite(best)
    shape = d.shape[:-1]
    T_rest = xp.full(shape, xp.nan)
    D = xp.full(shape, xp.nan)
    q_all = xp.full(shape + (3,), xp.nan)
    for ib, body in enumerate(scene.bodies):
        if per_body[ib] is None:
            continue
        m = who == ib
        if not bool(xp.any(m)):
            continue
        P, v = per_body[ib]
        KB = cache[v][1]
        q = xp.asarray(P) + xp.where(m, best, 0.0)[..., None] * KB[..., 1:]
        q_all = xp.where(m[..., None], q, q_all)
        T_rest = xp.where(m, _pattern(xp, body, q), T_rest)
        if mode == "seen":
            D = xp.where(m, 1.0 / (-k0 * KB[..., 0]), D)
    if scene.sky is not None:
        T_rest = xp.where(hit, T_rest, float(scene.sky))
        if mode == "seen":
            D = xp.where(hit, D, 1.0 / k0)
    if mode == "snapshot":
        D = xp.where(xp.isfinite(T_rest), 1.0, D)
    body_idx = xp.where(hit, who, -1 if scene.sky is not None else -2)
    out = {"body": body_idx, "s": best, "T_rest": T_rest, "D": D, "T_obs": D * T_rest, "q": q_all,
           "event": xp.asarray(Xo) + xp.where(hit, best, 0.0)[..., None] * K}
    if mode == "seen":
        out["n_lab"] = -K[..., 1:]
        out["t_emit"] = xp.where(hit, float(observer.t) - best / c, -xp.inf)
    return out


def trace_directions(scene: Scene, observer: Observer, d, c: float = 1.0, mode: str = "seen", check: bool = False,
                     only=None, aux: bool = False):
    """What the observer sees in the observer-frame look directions d (..., 3), as NumPy arrays: ``body`` (index of
    the body; -1 the sky; -2 nothing), ``s`` (lab distance to the emission, or observer-frame distance in the
    snapshot; inf for the sky), ``t_emit`` (lab emission time), ``event`` (the emission event (c t, x) in the lab),
    ``q`` (the rest-frame point of the body that emitted), ``n_lab`` (the photon's lab direction), ``T_rest``, ``D``,
    ``T_obs`` = D T_rest (the observed black-body temperature). ``mode``: "seen" or, for comparison only,
    "snapshot". ``only``: indices of the bodies to trace (others transparent). ``check``: fp64 references. ``aux``: a
    small auxiliary trace (stars, the visibility of retarded points), recorded apart from the image's device."""
    d = np.asarray(d, float)
    size = int(np.prod(d.shape[:-1])) * max(1, len(scene.bodies))
    ch = backend.choose(KERNEL, size, check=check, footprint=int(d.size // 3) * 8 * 40, aux=aux)
    try:
        out = _trace(ch.xp, scene, observer, ch.xp.asarray(d), c, mode, only)
        res = {k: backend.to_numpy(v) for k, v in out.items()}
    except Exception as e:
        if not backend.is_out_of_memory(e):
            raise
        backend.release()
        backend.choose(KERNEL, size, check=check, force="cpu", why=T("GPU: not enough memory, recomputed on the CPU"),
                       aux=aux)
        res = _trace(np, scene, observer, d, c, mode, only)
    finally:
        if ch.device == "gpu":
            backend.release()
    return res


def render(scene: Scene, observer: Observer, camera: Camera, c: float = 1.0, mode: str = "seen", check: bool = False):
    """``trace_directions`` for every pixel of the camera: arrays of shape (height, width[, 3])."""
    return trace_directions(scene, observer, camera.directions(), c, mode, check)


def star_images(scene: Scene, observer: Observer, c: float = 1.0):
    """For each star (lab direction s_hat towards it, temperature): the observer-frame look direction d', the Doppler
    factor D (the star seen at D T; its flux D^2 times its flux at rest) and whether a body hides it."""
    if not scene.stars:
        return {"d": np.zeros((0, 3)), "D": np.zeros(0), "T": np.zeros(0), "hidden": np.zeros(0, bool)}
    s = np.array([np.asarray(st[0], float) / np.linalg.norm(st[0]) for st in scene.stars])
    T = np.array([float(st[1]) for st in scene.stars])
    K = np.concatenate([np.ones((len(s), 1)), -s], axis=1)  # lab photon from the star, lab energy 1
    kp = K @ LZ.boost(np.asarray(observer.u, float), c).T
    d = -kp[:, 1:] / kp[:, :1]
    hidden = np.zeros(len(s), bool)
    if scene.bodies:
        hidden = np.isfinite(trace_directions(Scene(scene.bodies), observer, d, c, aux=True)["s"])
    return {"d": d, "D": kp[:, 0], "T": T, "hidden": hidden}


# --- references ------------------------------------------------------------------------------------------------------------
def ref_sky_temperature(T_sky: float, u, d, c: float = 1.0):
    """A uniform black-body sky at rest in the lab seen in observer-frame direction d by an observer with lab velocity
    u: T / (gamma (1 - beta cos theta')), theta' between d and u in the observer's frame (closed form)."""
    b = np.asarray(u, float) / c
    bb = float(np.linalg.norm(b))
    g = 1.0 / math.sqrt((1 - bb) * (1 + bb))
    return T_sky / (g * (1.0 - np.asarray(d, float) @ b))


def ref_aberration(s_hat, u, c: float = 1.0):
    """Observer-frame direction of a star at lab direction s_hat (at rest in the lab) seen by an observer with lab
    velocity u, in the plane of s_hat and u (closed form): cos theta' = (cos theta + beta) / (1 + beta cos theta) and
    sin theta' = sin theta / (gamma (1 + beta cos theta)), both formed directly (review B3-3: sin theta' taken as
    sqrt(1 - cos^2 theta') lost ~eps / sin theta' near the line of motion and failed a correct run)."""
    s = np.asarray(s_hat, float)
    s = s / np.linalg.norm(s, axis=-1, keepdims=True)
    b = np.asarray(u, float) / c
    bb = float(np.linalg.norm(b))
    if bb == 0:
        return s
    e = b / bb
    ct = s @ e
    perp = s - ct[..., None] * e
    st = np.linalg.norm(perp, axis=-1)
    perp = np.where(st[..., None] > 0, perp / np.where(st > 0, st, 1.0)[..., None], 0.0)
    den = 1 + bb * ct
    g = 1.0 / math.sqrt((1 - bb) * (1 + bb))
    cp = (ct + bb) / den
    sp = st / (g * den)
    out = cp[..., None] * e + sp[..., None] * perp
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def ref_energy_density_factor(beta: float) -> float:
    """The energy density of a uniform black-body sky seen by an observer moving at beta, relative to rest:
    (1/4 pi) int D^4 dOmega' = gamma^2 (1 + beta^2 / 3)."""
    return (1 + beta * beta / 3.0) / ((1 - beta) * (1 + beta))


def circle_fit(dirs):
    """A circle on the unit sphere through unit directions: its axis m and angular radius rho (least squares for
    d_i . w = 1, m = w / |w|, cos rho = 1 / |w|) and the largest angular deviation of the points from it."""
    d = np.asarray(dirs, float)
    w, *_ = np.linalg.lstsq(d, np.ones(len(d)), rcond=None)
    m = w / np.linalg.norm(w)
    rho = math.acos(min(1.0, 1.0 / np.linalg.norm(w)))
    dev = np.abs(np.arccos(np.clip(d @ m, -1, 1)) - rho)
    return m, rho, float(dev.max())


def outline(scene: Scene, observer: Observer, ib: int, c: float = 1.0, n: int = 64, iters: int = 64):
    """The apparent outline of body ``ib`` (alone; others transparent) seen by the observer: observer-frame
    directions on n rays from the direction of its retarded centre, each found by bisection between a direction
    that meets the body and one that misses it (``iters`` halvings of the angle). An independent route to the shape
    of the image (for a sphere: Penrose's circle, ``lorentz.sphere_outline``)."""
    body = scene.bodies[ib]
    _, xe, _ = retarded_points(body, np.zeros((1, 3)), observer, c)
    a = look_direction(observer, xe, c)[0]
    if not np.isfinite(trace_directions(scene, observer, a[None], c, only=[ib], check=True)["s"][0]):
        raise ValueError(T("the direction to the retarded centre misses the body"))
    e1 = np.cross(a, [1.0, 0.0, 0.0] if abs(a[0]) < 0.9 else [0.0, 1.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(a, e1)
    psi = np.linspace(0, 2 * math.pi, n, endpoint=False)
    w = np.cos(psi)[:, None] * e1 + np.sin(psi)[:, None] * e2
    lo, hi = np.zeros(n), np.full(n, math.pi * 0.999)
    far = trace_directions(scene, observer, np.cos(hi)[:, None] * a + np.sin(hi)[:, None] * w, c, only=[ib],
                           check=True)["s"]
    if np.any(np.isfinite(far)):
        raise ValueError(T("the outline is not closed: the body fills almost the whole sky"))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        s = trace_directions(scene, observer, np.cos(mid)[:, None] * a + np.sin(mid)[:, None] * w, c, only=[ib],
                             check=True)["s"]
        inside = np.isfinite(s)
        lo, hi = np.where(inside, mid, lo), np.where(inside, hi, mid)
    al = 0.5 * (lo + hi)
    return np.cos(al)[:, None] * a + np.sin(al)[:, None] * w, float(np.max(hi - lo))


def penrose_reference(body: Sphere, observer: Observer, c: float = 1.0, n: int = 64):
    """The outline of a moving sphere by ``lorentz.sphere_outline`` (lab directions for an observer at rest),
    carried into the observer's frame (aberration of each outline photon)."""
    lab = LZ.sphere_outline(np.asarray(body.center, float) - np.asarray(observer.x, float), float(body.radius),
                            np.asarray(body.velocity, float), float(observer.t), c, n)
    K = np.concatenate([np.ones((len(lab), 1)), -lab], axis=1)
    kp = K @ LZ.boost(np.asarray(observer.u, float), c).T
    return -kp[:, 1:] / kp[:, :1]


def static_render(scene: Scene, eye, d):
    """Plain ray casting for bodies at rest (no Lorentz transformation, no light-time): the nearest intersection of
    the rays eye + s d (lab look directions d) with the bodies at their centres; returns (body index or -1, s)."""
    d = np.asarray(d, float)
    best = np.full(d.shape[:-1], np.inf)
    who = np.full(d.shape[:-1], -1)
    for ib, body in enumerate(scene.bodies):
        if np.any(np.asarray(body.velocity, float) != 0):
            raise ValueError("static_render: bodies at rest only")
        s = _HIT[body.kind](np, body, np.asarray(eye, float) - np.asarray(body.center, float), d)
        closer = s < best
        best, who = np.where(closer, s, best), np.where(closer, ib, who)
    return who, best


# --- the GPU kernel ------------------------------------------------------------------------------------------------------
def _bench_scene():
    bodies = [Sphere((0.0, 0.0, 6.0), 1.0, (0.6, 0.0, 0.0)), Box((2.5, 0.0, 7.0), (0.5, 0.5, 0.5), (0.6, 0.0, 0.0)),
              Panel((0.0, -1.5, 0.0), half=(20.0, 20.0))]
    bodies += [Box((x, 0.0, 12.0), (0.1, 3.0, 0.1)) for x in np.linspace(-4, 4, 9)]
    return Scene(bodies, sky=3000.0)


def _bench(size: int, xp, cplx):
    """One frame as a call does it: the look directions to the device, all bodies, the results back to the host."""
    n = max(8, int(round(math.sqrt(size / 12))))
    cam = Camera(n, n, fov=90.0)
    out = _trace(xp, _bench_scene(), Observer(0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.5)), xp.asarray(cam.directions()),
                 1.0, "seen")
    for v in out.values():
        backend.to_numpy(v)


backend.register(backend.KernelSpec(
    KERNEL, T("Ray tracing with light travel time"),
    T("what a fast observer sees: the aberration of every pixel, the intersection of the past light ray with the "
      "bodies' world tubes, the Doppler temperature (u39)"),
    gpu=True,
    precisions={"fp64": {"allowed": True}},
    crossover=256 * 256 * 12,
    crossover_note=T("measured 2026-10-28 on an RTX 2080 Ti against two CPU threads, fp64, results transferred back "
                     "(size = pixels × bodies): the GPU is faster from 256×256 pixels with 12 bodies (×3.8), ×7 at "
                     "512×512; below that, the CPU (kernel launch overheads); “Measure again” refines this"),
    bench=_bench, bench_sizes=(32 * 32 * 12, 64 * 64 * 12, 128 * 128 * 12, 256 * 256 * 12, 512 * 512 * 12)))
