# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Light as Newtonian corpuscles (Soldner 1804): particles that move at c far from the body and follow Kepler
hyperbolae in the field -GM r/r^3. This is a refuted alternative, not an approximation: the deflection is half the
measured one at every impact parameter (0.875" instead of 1.75" at the solar limb; Dyson, Eddington & Davidson 1920;
VLBI: gamma = 1 to 1e-4), so it has no domain where it is right (review 2026-10-23, E9).

Arrival events (``newton_arrivals``): the emission angle is found by root finding on the angular miss at the target
radius (``connect_newton``, exact hyperbolae from ``lfphys.theories.approx.newton.crossings``); the images on both
sides of the body (lowest order) are found; ``trace_newton`` integrates fans of corpuscles for drawing only.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import optimize

from lfphys.i18n import T

from ...core.gravity.rays import ANGLE_TOL, MAX_STEPS, RaySet, _Recorder
from ...core.numerics import moving_root
from ..approx.newton import _wrap, crossings

ABOUT = {
    "layer": "theories", "kind": "alternative",
    "title": T("Light as Newtonian corpuscles (Soldner)"),
    "statement": T("Particles of light with the speed c far from the body move on Kepler hyperbolas in the field −GM "
                   "r/r³; the deflection of light is half the accepted value."),
    "validity": T("refuted at every impact parameter: 0.875″ instead of the measured 1.75″ at the limb of the Sun "
                  "(Dyson, Eddington & Davidson 1920; VLBI: γ = 1 to 10⁻⁴)"),
    "basis": ["Soldner, Berliner Astron. Jahrbuch 1804", "Dyson, Eddington & Davidson, Phil. Trans. A 220, 291 (1920)"],
    "conflicts": [T("lfphys.core.gravity.schwarzschild: GR gives twice the deflection of light; the measurements "
                    "favour GR")],
}


def connect_newton(origin, target, speed_rest, v_source, mu, r_abs, n_scan=4001):
    """Emission directions (in the source frame, Galilean) whose corpuscle passes through ``target``.
    Returns [{dt, angle, dir}] sorted by travel time; dir is the corpuscle velocity direction at the target."""
    origin = np.asarray(origin, float)
    target = np.asarray(target, float)
    v_source = np.asarray(v_source, float)
    rT = math.hypot(*target)
    phT = math.atan2(target[1], target[0])

    def branch_miss(alpha):
        v0 = speed_rest * np.array([math.cos(alpha), math.sin(alpha)]) + v_source
        cr = crossings(origin, v0, mu, rT, r_abs)
        return [(_wrap(math.atan2(p[1], p[0]) - phT), dt, outward) for dt, p, outward in cr]

    al = np.linspace(-math.pi, math.pi, n_scan)
    vals = [branch_miss(a) for a in al]
    roots = []
    for j in range(2):  # first and second crossing of the target radius
        for i in range(n_scan - 1):
            m0 = vals[i][j] if len(vals[i]) > j else None
            m1 = vals[i + 1][j] if len(vals[i + 1]) > j else None
            if m0 is None or m1 is None or m0[0] * m1[0] > 0 or abs(m0[0] - m1[0]) > 1.0:
                continue

            def F(a, j=j):
                b = branch_miss(a)
                return b[j][0] if len(b) > j else math.nan

            try:
                a = optimize.brentq(F, al[i], al[i + 1], xtol=1e-15, rtol=1e-15, maxiter=200)
            except ValueError:
                continue
            b = branch_miss(a)
            if len(b) <= j or abs(b[j][0]) > 1e-9:
                continue
            roots.append((b[j][1], a, b[j][2]))
    out = []
    for dt, a, outward in sorted(roots):
        if any(abs(dt - o["dt"]) <= 1e-12 * dt and abs(_wrap(a - o["angle"])) < 1e-9 for o in out):
            continue
        v0 = speed_rest * np.array([math.cos(a), math.sin(a)]) + v_source
        # velocity at the target from energy and angular momentum conservation
        r0 = math.hypot(*origin)
        E = 0.5 * float(v0 @ v0) - mu / r0
        h = float(origin[0] * v0[1] - origin[1] * v0[0])
        vT = math.sqrt(2.0 * (E + mu / rT))
        vt = h / rT
        vr2 = max(vT * vT - vt * vt, 0.0)
        rhat = target / rT
        that = np.array([-rhat[1], rhat[0]])
        vr = math.sqrt(vr2) * (1.0 if outward else -1.0)
        vel = vr * rhat + vt * that
        # side of the body the corpuscle passes: sign of its angular momentum (0 for a radial path)
        side = int(np.sign(h)) if abs(h) > 1e-12 * r0 * math.sqrt(float(v0 @ v0)) else 0
        out.append({"dt": dt, "angle": a, "side": side, "dir": (vel / np.linalg.norm(vel)).tolist()})
    return out


def trace_newton(laws, origins, t0, vel0, gm, body_radius, r_out, eta=4e-3) -> RaySet:
    """Newtonian corpuscles: RK4 in t with step eta * r / |v|."""
    X = np.array(origins, float)
    V = np.array(vel0, float)
    n = len(X)
    T = np.full(n, float(t0))
    alive = np.ones(n, bool)
    status = np.zeros(n, np.uint8)
    rec = _Recorder(n)
    rec.add(alive, T, X)
    last_dir = V / np.linalg.norm(V, axis=1)[:, None]
    since = np.zeros(n, int)

    def acc(Xs):
        r2 = np.sum(Xs * Xs, axis=1)
        return -gm * Xs / (r2 * np.sqrt(r2))[:, None]

    for _ in range(MAX_STEPS):
        if not np.any(alive):
            break
        ia = np.nonzero(alive)[0]
        Xa, Va = X[ia], V[ia]
        r = np.hypot(Xa[:, 0], Xa[:, 1])
        sp = np.linalg.norm(Va, axis=1)
        dt = eta * r / sp
        if body_radius > 0:
            dt = np.minimum(dt, np.maximum(0.25 * (r - body_radius), 1e-3 * r) / sp)
        d = dt[:, None]
        k1x, k1v = Va, acc(Xa)
        k2x, k2v = Va + 0.5 * d * k1v, acc(Xa + 0.5 * d * k1x)
        k3x, k3v = Va + 0.5 * d * k2v, acc(Xa + 0.5 * d * k2x)
        k4x, k4v = Va + d * k3v, acc(Xa + d * k3x)
        Xn = Xa + d / 6.0 * (k1x + 2 * k2x + 2 * k3x + k4x)
        Vn = Va + d / 6.0 * (k1v + 2 * k2v + 2 * k3v + k4v)
        X[ia], V[ia], T[ia] = Xn, Vn, T[ia] + dt
        rn = np.hypot(Xn[:, 0], Xn[:, 1])
        since[ia] += 1
        dirn = Vn / np.linalg.norm(Vn, axis=1)[:, None]
        store = (np.sum(dirn * last_dir[ia], axis=1) < np.cos(ANGLE_TOL)) | (since[ia] >= 64)
        out = rn >= r_out
        absorbed = rn <= body_radius
        done = out | absorbed
        mask = np.zeros(n, bool)
        mask[ia[store | done]] = True
        rec.add(mask, T, X)
        last_dir[ia[store]] = dirn[store]
        since[ia[store]] = 0
        if np.any(done):
            status[ia[done]] = np.where(absorbed, 1, 0)[done]
            alive[ia[done]] = False
    else:
        status[alive] = 3
        rec.add(alive, T, X)
    rays = rec.pack(t0, status)
    rays.vend = V / np.linalg.norm(V, axis=1)[:, None]
    return rays


def newton_arrivals(c, gm, r_abs, t0, origin, v_source, wl, t_from=-math.inf, scene_r=None):
    """Corpuscle arrivals (primary and secondary image) from exact Kepler hyperbolae; moving targets by the same
    bracketed root finding as in GR."""
    origin = np.asarray(origin, float)
    r0 = float(np.hypot(*origin))
    speed_rest = math.sqrt(c * c + 2.0 * gm / r0)  # c far from the body for a source at rest
    v_source = np.asarray(v_source, float)
    first = connect_newton(origin, wl.pos(max(t0, t_from)), speed_rest, v_source, gm, r_abs)
    out = []
    for img0 in first:
        side = img0["side"]
        last = {}

        def dt_of(pos, side=side, last=last):
            imgs = [m for m in connect_newton(origin, pos, speed_rest, v_source, gm, r_abs) if m["side"] == side]
            if not imgs:
                return None
            last["img"] = min(imgs, key=lambda m: m["dt"])
            return last["img"]["dt"]

        t = moving_root(dt_of, t0, t_from, wl)
        if t is None:
            continue
        dt_of(wl.pos(t))
        out.append({"t": float(t), "image": 0, "side": side, "key": f"s{side:+d}", "dir": last["img"]["dir"],
                    "method": "exact (Kepler hyperbola)"})
    out.sort(key=lambda a: a["t"])
    for i, a in enumerate(out):
        a["image"] = i
    return out
