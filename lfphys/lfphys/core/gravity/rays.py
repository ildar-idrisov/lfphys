# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Propagation of light for drawing: fans of rays from an emission event, traced under the run's laws.

Every ray is returned as a polyline of events (t, x, y) in lab coordinates; between stored vertices the ray is
straight to within the storage tolerance (direction change < ``ANGLE_TOL``), so linear interpolation in t is
faithful for drawing. Exact event times (arrivals, measurements) are NOT taken from these polylines: they are
solved separately (``arrivals.py``, ``schwarzschild.py``) and the two are compared in the checks.

Laws:
* flat (gravity "none"): straight lines; lab velocity from the law set's ``emit_velocities`` (SR aberration in the
  core; the ether and emission kinematics are alternatives outside it, ``lfphys.theories.alternatives.kinematics``,
  chosen by ``lfphys.laws``). Two vertices per ray.
* GR: null geodesics of Schwarzschild, integrated in the affine parameter lambda (E = 1) in the Cartesian form
      d^2x/dlambda^2 = -(3/2) rs h^2 x / r^5,   dt/dlambda = 1/(c (1 - rs/r)),   h = x * dy/dlambda - y * dx/dlambda
  (the orbit equation u'' + u = (3/2) rs u^2 written as a central force); classical RK4, step proportional to r
  and to the distance to the horizon.
* Newtonian corpuscles: ``lfphys.theories.alternatives.newton_light.trace_newton`` (a refuted alternative, outside the core).

Status of a ray at its last vertex: 0 left the scene, 1 absorbed by the body, 2 reached the horizon (in
Schwarzschild time it approaches it forever; drawn as frozen there), 3 step limit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from lfphys.i18n import T

from .. import relativity

ABOUT = {
    "layer": "core", "kind": "numerical solution",
    "title": T("Light rays: flat space-time and Schwarzschild"),
    "statement": T("Bundles of rays for drawing: straight lines in flat space-time (speed by the world's kinematics), "
                   "Schwarzschild null geodesics (RK4 in the affine parameter). The exact times of events are "
                   "computed separately (arrivals, schwarzschild) and compared."),
    "validity": T("drawing accuracy (angular tolerance ANGLE_TOL); exact events in arrivals"),
    "basis": ["lfphys.core.gravity.schwarzschild"],
    "conflicts": [],
}

ANGLE_TOL = np.deg2rad(0.25)
MAX_STEPS = 40000


@dataclass
class RaySet:
    t0: float
    offsets: np.ndarray  # (n+1,) int32: vertices of ray i are [offsets[i], offsets[i+1])
    T: np.ndarray
    X: np.ndarray
    Y: np.ndarray
    status: np.ndarray  # (n,) uint8
    vend: np.ndarray | None = None  # (n,2) final unit lab direction (traced rays only)

    @property
    def n(self) -> int:
        return len(self.status)

    def ray(self, i: int):
        a, b = self.offsets[i], self.offsets[i + 1]
        return self.T[a:b], self.X[a:b], self.Y[a:b]

    def blobs(self) -> dict:
        return {"off": self.offsets.astype(np.int32), "T": self.T, "X": self.X, "Y": self.Y,
                "st": self.status.astype(np.uint8)}


def unit_fan(n: int, angle0: float = 0.0) -> np.ndarray:
    a = angle0 + 2.0 * np.pi * np.arange(n) / n
    return np.stack([np.cos(a), np.sin(a)], axis=1)


class _Recorder:
    """Collects vertices of many rays stepping together; packs them per ray at the end."""

    def __init__(self, n):
        self.n = n
        self.idx, self.t, self.x, self.y = [], [], [], []

    def add(self, mask, T, X):
        if np.any(mask):
            ii = np.nonzero(mask)[0]
            self.idx.append(ii)
            self.t.append(T[ii].copy())
            self.x.append(X[ii, 0].copy())
            self.y.append(X[ii, 1].copy())

    def pack(self, t0, status):
        idx = np.concatenate(self.idx)
        order = np.argsort(idx, kind="stable")
        idx = idx[order]
        T = np.concatenate(self.t)[order]
        X = np.concatenate(self.x)[order]
        Y = np.concatenate(self.y)[order]
        counts = np.bincount(idx, minlength=self.n)
        off = np.zeros(self.n + 1, dtype=np.int64)
        np.cumsum(counts, out=off[1:])
        return RaySet(t0, off, T, X, Y, status.astype(np.uint8))


def _circle_exit(p, u, center, radius):
    """Smallest s >= 0 with |p + u s - center| = radius for a point inside the circle (vectorized)."""
    d = p - center
    a = np.sum(u * u, axis=1)
    b = 2.0 * np.sum(d * u, axis=1)
    c = np.sum(d * d, axis=1) - radius**2
    disc = np.maximum(b * b - 4 * a * c, 0.0)
    return (-b + np.sqrt(disc)) / (2 * a)


def _circle_hit(p, u, radius):
    """Smallest s > 0 with |p + u s| = radius for points outside the circle; inf if missed."""
    a = np.sum(u * u, axis=1)
    b = 2.0 * np.sum(p * u, axis=1)
    c = np.sum(p * p, axis=1) - radius**2
    disc = b * b - 4 * a * c
    s = np.full(len(a), np.inf)
    ok = (disc >= 0) & (c > 0)
    s1 = (-b[ok] - np.sqrt(disc[ok])) / (2 * a[ok])
    s[ok] = np.where(s1 > 0, s1, np.inf)
    return s


def trace_flat(laws, origins, t0, vel, body_radius, scene_center, scene_radius) -> RaySet:
    """Straight rays with lab velocities ``vel`` (n,2) from ``origins`` (n,2) at t0."""
    origins = np.asarray(origins, float)
    vel = np.asarray(vel, float)
    n = len(vel)
    s_exit = _circle_exit(origins, vel, np.asarray(scene_center, float), scene_radius)
    status = np.zeros(n, np.uint8)
    if body_radius > 0:
        s_hit = _circle_hit(origins, vel, body_radius)
        hit = s_hit < s_exit
        s_exit = np.where(hit, s_hit, s_exit)
        status[hit] = 1
    s_exit = np.maximum(s_exit, 0.0)
    T = np.stack([np.full(n, t0), t0 + s_exit], axis=1).ravel()
    P1 = origins + vel * s_exit[:, None]
    X = np.stack([origins[:, 0], P1[:, 0]], axis=1).ravel()
    Y = np.stack([origins[:, 1], P1[:, 1]], axis=1).ravel()
    off = np.arange(0, 2 * n + 1, 2)
    return RaySet(t0, off, T, X, Y, status)


def static_frame_directions_to_dlambda(origins, n_local, rs):
    """Convert unit directions in the local static orthonormal frame (Cartesian components) to dx/dlambda
    (E = 1): dr/dlambda = n_r, r dphi/dlambda = n_phi / sqrt(f)."""
    r = np.hypot(origins[:, 0], origins[:, 1])
    rhat = origins / r[:, None]
    phat = np.stack([-rhat[:, 1], rhat[:, 0]], axis=1)
    nr = np.sum(n_local * rhat, axis=1)
    nphi = np.sum(n_local * phat, axis=1)
    f = 1.0 - rs / r
    return rhat * nr[:, None] + phat * (nphi / np.sqrt(f))[:, None]


def local_velocity_static_frame(pos, vel, rs, c):
    """Velocity of an object as measured by the static observer at its position (orthonormal components)."""
    pos = np.asarray(pos, float)
    vel = np.asarray(vel, float)
    r = float(np.hypot(*pos))
    f = 1.0 - rs / r
    rhat = pos / r
    phat = np.array([-rhat[1], rhat[0]])
    vr = vel @ rhat
    vt = vel @ phat
    return rhat * (vr / f) + phat * (vt / np.sqrt(f))


def aberrate_sr(n_rest, v_local, c):
    """Unit directions of light emitted along ``n_rest`` in a source frame moving with ``v_local`` relative to the
    frame in which the result is expressed (special-relativistic aberration via the Lorentz boost)."""
    v_local = np.asarray(v_local, float)
    if not np.any(v_local):
        return np.asarray(n_rest, float)
    return relativity.aberrate(np.asarray(n_rest, float), v_local, c)


def trace_gr(laws, origins, t0, n_local, rs, body_radius, r_out, eta=4e-3) -> RaySet:
    """Null geodesics of Schwarzschild from ``origins`` (n,2) at coordinate time t0 with unit directions
    ``n_local`` (n,2) in the local static frame."""
    c = laws.c
    X = np.array(origins, float)
    V = static_frame_directions_to_dlambda(X, np.asarray(n_local, float), rs)
    n = len(X)
    CT = np.full(n, c * t0)
    h2 = (X[:, 0] * V[:, 1] - X[:, 1] * V[:, 0]) ** 2
    r_stop_in = max(body_radius, rs * (1.0 + 1e-4)) if rs > 0 else body_radius
    alive = np.ones(n, bool)
    status = np.zeros(n, np.uint8)
    rec = _Recorder(n)
    rec.add(alive, CT / c, X)
    last_dir = V / np.linalg.norm(V, axis=1)[:, None]
    since = np.zeros(n, int)

    for _ in range(MAX_STEPS):
        if not np.any(alive):
            break
        ia = np.nonzero(alive)[0]
        Xa, Va = X[ia], V[ia]
        r = np.hypot(Xa[:, 0], Xa[:, 1])
        sp = np.linalg.norm(Va, axis=1)
        dl = eta * r / sp
        if rs > 0:
            dl = np.minimum(dl, 0.05 * (r - rs) / sp)
        if body_radius > rs:
            dl = np.minimum(dl, np.maximum(0.25 * (r - body_radius), 1e-3 * r) / sp)
        h2a = h2[ia]

        def f(Xs, Vs):
            r2 = np.sum(Xs * Xs, axis=1)
            rr = np.sqrt(r2)
            if rs > 0:
                a = -1.5 * rs * h2a[:, None] * Xs / (r2 * r2 * rr)[:, None]
                dct = 1.0 / (1.0 - rs / rr)
            else:
                a = np.zeros_like(Xs)
                dct = np.ones_like(rr)
            return Vs, a, dct

        d = dl[:, None]
        k1x, k1v, k1t = f(Xa, Va)
        k2x, k2v, k2t = f(Xa + 0.5 * d * k1x, Va + 0.5 * d * k1v)
        k3x, k3v, k3t = f(Xa + 0.5 * d * k2x, Va + 0.5 * d * k2v)
        k4x, k4v, k4t = f(Xa + d * k3x, Va + d * k3v)
        Xn = Xa + d / 6.0 * (k1x + 2 * k2x + 2 * k3x + k4x)
        Vn = Va + d / 6.0 * (k1v + 2 * k2v + 2 * k3v + k4v)
        CTn = CT[ia] + dl / 6.0 * (k1t + 2 * k2t + 2 * k3t + k4t)
        rn = np.hypot(Xn[:, 0], Xn[:, 1])
        X[ia], V[ia], CT[ia] = Xn, Vn, CTn
        since[ia] += 1
        dirn = Vn / np.linalg.norm(Vn, axis=1)[:, None]
        cosang = np.sum(dirn * last_dir[ia], axis=1)
        store = (cosang < np.cos(ANGLE_TOL)) | (since[ia] >= 64)
        out = rn >= r_out
        absorbed = rn <= r_stop_in
        done = out | absorbed
        mask = np.zeros(n, bool)
        mask[ia[store | done]] = True
        rec.add(mask, CT / c, X)
        last_dir[ia[store]] = dirn[store]
        since[ia[store]] = 0
        if np.any(done):
            st = np.where(absorbed, np.where(body_radius > rs, 1, 2), 0)
            status[ia[done]] = st[done]
            alive[ia[done]] = False
    else:
        status[alive] = 3
        rec.add(alive, CT / c, X)
    rays = rec.pack(t0, status)
    rays.vend = V / np.linalg.norm(V, axis=1)[:, None]
    return rays
