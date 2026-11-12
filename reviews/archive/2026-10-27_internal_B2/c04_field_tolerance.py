# B2 review, check 4: v09's field of three-burn loops at the edge of its schema (eta_u = 3, |w| up to 0.999).
# The field's theta (engine matrices) and its reference (L'Huilier from the sides) against a 50-digit evaluation, and
# both against the tolerance 64 eps gamma_u^2 gamma_w^2 that the checks field_exact / plane_exact_N use.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server light-funnel-viz python3 reviews/2026-10-27_internal_B2/c04_field_tolerance.py
import math

import mpmath as mp
import numpy as np

from lfphys.core import lorentz as LZ
from v09_thomas_3d.engine import loops as LP

mp.mp.dps = 40
rng = np.random.default_rng(3)


def mp_rap(b):
    return mp.atanh(mp.sqrt(sum(mp.mpf(x) ** 2 for x in b)))


def mp_dist(a, b):
    # relative rapidity: cosh d = gamma_a gamma_b (1 - a.b)
    a = [mp.mpf(x) for x in a]; b = [mp.mpf(x) for x in b]
    ga = 1 / mp.sqrt(1 - sum(x * x for x in a)); gb = 1 / mp.sqrt(1 - sum(x * x for x in b))
    return mp.acosh(ga * gb * (1 - sum(x * y for x, y in zip(a, b))))


def mp_area(u, w):
    z = [0, 0, 0]
    a, b, c = mp_dist(z, u), mp_dist(u, w), mp_dist(w, z)
    s = (a + b + c) / 2
    t = mp.tanh(s / 2) * mp.tanh((s - a) / 2) * mp.tanh((s - b) / 2) * mp.tanh((s - c) / 2)
    return 4 * mp.atan(mp.sqrt(t))


for eta_u in (1.0, 3.0):
    u = np.array([math.tanh(eta_u), 0.0, 0.0])
    # points of the ball: random, and the hardest ones (|w| = 0.999 nearly opposite to u, small angle)
    W = rng.normal(size=(400, 3)); W /= np.linalg.norm(W, axis=1)[:, None]
    W *= rng.uniform(0.0, 0.999, size=400)[:, None] ** 0.3
    hard = []
    for ang in (179.9, 179.0, 170.0, 150.0, 90.0, 30.0, 5.0, 0.5):
        a = math.radians(ang)
        hard.append(0.999 * np.array([math.cos(a), math.sin(a), 0.0]))
    W = np.vstack([W, np.array(hard)])
    th, _, _ = LP.triangle_field(u, W)
    worst = (0, None)
    worst_ref = (0, None)
    for i, w in enumerate(W):
        if not np.isfinite(th[i]) or th[i] < 1e-9:
            continue
        ex = float(mp_area(u, w))
        ref = LP.triangle_reference(u, w)
        tol = LP.field_tolerance(u, w)
        r1 = abs(th[i] - ex) / tol
        r2 = abs(ref - ex) / tol
        if r1 > worst[0]:
            worst = (r1, w, th[i] - ex, tol)
        if r2 > worst_ref[0]:
            worst_ref = (r2, w, ref - ex, tol)
    print(f"eta_u = {eta_u}: matrix route worst |err|/tol = {worst[0]:.3f} (err {worst[2]:+.2e}, tol {worst[3]:.1e}, "
          f"|w| = {np.linalg.norm(worst[1]):.4f})")
    print(f"             L'Huilier reference worst |err|/tol = {worst_ref[0]:.3f} (err {worst_ref[2]:+.2e}, tol "
          f"{worst_ref[3]:.1e}, w = {np.round(worst_ref[1], 4)})")
    for ang in (179.9, 179.0, 170.0):
        a = math.radians(ang)
        w = 0.999 * np.array([math.cos(a), math.sin(a), 0.0])
        ex = float(mp_area(u, w))
        thw = float(LP.triangle_field(u, w[None])[0][0])
        print(f"   w at {ang} deg, |w|=0.999: exact {ex:.6e}; matrices err {thw - ex:+.2e}; L'Huilier err "
              f"{LP.triangle_reference(u, w) - ex:+.2e}; tol {LP.field_tolerance(u, w):.1e}")
