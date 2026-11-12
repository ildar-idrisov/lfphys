# B2 review, check 5: why v09's `holonomy` check fails at some points of its schema (found by c03_v09_grid.py), and
# whether the tolerance "8 x the measured disagreement of the two representations" can bound the error at all.
# For each case: the engine's rotation R against the closed form R(n, -A) (dR, what the check compares), the measured
# round-off est, and an attribution with 40-digit mpmath:
#   A_exact      the exact area of the loop whose vertices are the float vertices v09 builds (L'Huilier in mpmath)
#   R_fly_exact  the exact rotation produced by flying the float burns v09 builds (pieces) in mpmath
# so that   dR = (R - R_fly_exact)       [flying error: what est measures]
#              + (R_fly_exact - R(A_exact))  [the burns built in float do not trace the intended polygon exactly]
#              + (R(A_exact) - R(A_ref))     [the closed form's own rounding]
# Also the rho = 0.05 corner of the schema (the tests check only rho = 3) against the a priori bound.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server:/lf/visualizations/tests light-funnel-viz python3 reviews/2026-10-27_internal_B2/c05_holonomy_tolerance.py
import math

import mpmath as mp
import numpy as np
from harness import Harness

from lfphys.core import lorentz as LZ
from lfphys.core import spin_transport as T

mp.mp.dps = 40
V = "v09_thomas_3d"


def mp_boost_gen(n):
    G = mp.zeros(4, 4)
    for i in range(3):
        G[0, i + 1] = G[i + 1, 0] = mp.mpf(n[i])
    return G


def mp_fly(pieces):
    """The burns flown exactly (only Burn pieces): M = prod exp(eta K.n) in mpmath; returns the 3x3 rotation at the end
    and the residual |beta|."""
    M = mp.eye(4)
    for p in pieces:
        assert isinstance(p, T.Burn)
        n = np.asarray(p.direction, float)
        n = n / np.linalg.norm(n)  # as the engine does (_unit), in float
        M = M * mp.expm(mp.mpf(p.rapidity) * mp_boost_gen([mp.mpf(x) for x in n]))
    beta = [M[i + 1, 0] / M[0, 0] for i in range(3)]
    return M, beta


def mp_dist(a, b):
    a = [mp.mpf(x) for x in a]; b = [mp.mpf(x) for x in b]
    ga = 1 / mp.sqrt(1 - sum(x * x for x in a)); gb = 1 / mp.sqrt(1 - sum(x * x for x in b))
    return mp.acosh(ga * gb * (1 - sum(x * y for x, y in zip(a, b))))


def mp_triangle(a, b, c):
    s = (a + b + c) / 2
    t = mp.tanh(s / 2) * mp.tanh((s - a) / 2) * mp.tanh((s - b) / 2) * mp.tanh((s - c) / 2)
    return 4 * mp.atan(mp.sqrt(t))


def mp_polygon_area(verts):
    """Area of a planar geodesic polygon (fan triangulation from vertex 0) in mpmath."""
    A = 0
    for k in range(1, len(verts) - 1):
        A += mp_triangle(mp_dist(verts[0], verts[k]), mp_dist(verts[k], verts[k + 1]), mp_dist(verts[k + 1], verts[0]))
    return A


cases = [
    {"loop": "triangle", "rho": 2.6877902048795144, "turns": 3, "sides": 5, "alpha": 57.76537981020704,
     "nth": 25.230265411303613, "nph": 123.45851349639912, "accel_g": 2.070161305081177},
    {"loop": "polygon", "rho": 3.0, "turns": 4, "sides": 24, "nth": 14.666572836044317, "nph": 114.32638600170613,
     "accel_g": 6.651339398612368},
    {"loop": "triangle", "rho": 2.9691471306145036, "turns": 2, "alpha": 35.09978703667615,
     "nth": 30.60660887473022, "nph": 85.33324560959734, "accel_g": 4.942155829248469},
]
for p in cases:
    h = Harness(V, None, {"space": "lab", **p})
    h.run_to(h.sim.T_end * 1.0001)
    sim = h.sim
    est = sim._round_est()
    ref = float(sim.info["reference"])
    n = np.asarray(sim.info["normal"])
    R = sim.hol["R"]
    dR = float(np.max(np.abs(R - LZ.rot3(n, -ref))))
    tol = max(8 * est, 1e3 * np.finfo(float).eps * (1.0 + abs(ref)))
    chk = h.checks()["holonomy"]
    # attribution
    verts = [np.zeros(3)] + [np.asarray(v) for v in sim.info["vertices"]] + [np.zeros(3)]
    A_exact = mp_polygon_area(verts[:-1]) * p["turns"]
    M, beta = mp_fly(sim.pieces)
    Rx = np.array([[float(M[i + 1, j + 1]) for j in range(3)] for i in range(3)])
    print(f"{p['loop']} rho={p['rho']:.4f} turns={p['turns']}: check ok={chk.get('ok')}  dR = {dR:.2e}  "
          f"tol = 8 est = {tol:.2e}  (est {est:.2e}, a priori bound {sim._round_bound():.2e})")
    print(f"   |A_ref - A_exact(float vertices)| = {abs(ref - float(A_exact)):.2e}   "
          f"|R_engine - R_fly_exact| = {np.max(np.abs(R - Rx)):.2e}   "
          f"|R_fly_exact - R(n, -A_exact)| = {np.max(np.abs(Rx - LZ.rot3(n, -float(A_exact)))):.2e}   "
          f"residual |beta| exact {float(mp.sqrt(sum(b * b for b in beta))):.1e}")

print("rho = 0.05 corner (tests check only rho = 3): roundoff est against the a priori bound")
for loop in ("circle", "thomas", "polygon", "crown", "helix", "seam", "triangle"):
    for turns in (6,):
        p = {"space": "lab", "loop": loop, "rho": 0.05, "turns": turns, "sides": 24, "chi": 80.0, "alpha": 170.0}
        h = Harness(V, None, p)
        h.run_to(h.sim.T_end * 1.0001)
        est, bound = h.sim._round_est(), h.sim._round_bound()
        bad = [c["id"] for c in h.checks().values() if c.get("ok") is False]
        print(f"   {loop:8s} turns={turns}: est {est:.2e}  bound {bound:.2e}  bound/est {bound / est:6.2f}  failed: {bad}")
