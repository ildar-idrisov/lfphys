# B2 review, check 2: core.lorentz at its edges and by independent routes.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys light-funnel-viz python3 reviews/2026-10-27_internal_B2/c02_lorentz_edges.py
import math

import mpmath as mp
import numpy as np

from lfphys.core import lorentz as L

np.set_printoptions(precision=6, suppress=False)
rng = np.random.default_rng(7)

print("1. Penrose's outline against a brute-force light-time image of the body's surface")
# The body: a sphere of radius r in its rest frame; in the lab at time t its point with rest-frame offset y is at
# centre(t) + Ti y (Lorentz contraction along v). Each such point moves uniformly, so its image is L.apparent (light
# time). The images of all surface points must fill the outline's circle: none outside, the farthest on it.
for P, rad, v in (([3.0, 1.0, -0.5], 0.7, [0.6, 0.3, 0.1]), ([0.0, 5.0, 0.0], 1.5, [0.95, 0.0, 0.0]),
                  ([-2.0, 0.3, 4.0], 0.4, [0.0, -0.4, 0.85]), ([4.0, 0.5, 0.0], 1.0, [-0.9, 0.0, 0.0])):
    P, v = np.asarray(P), np.asarray(v)
    d = L.sphere_outline(P, rad, v, n=720)
    # circle on the unit sphere: plane fit
    c0 = d.mean(0)
    _, _, Vt = np.linalg.svd(d - c0)
    nrm = Vt[2] * np.sign(Vt[2] @ c0)
    cosr = float(np.mean(d @ nrm))
    ang_r = math.acos(cosr)
    g = float(L.gamma_of(v))
    nv = v / np.linalg.norm(v)
    Ti = np.eye(3) + (1 / g - 1) * np.outer(nv, nv)
    y = rng.normal(size=(200000, 3))
    y = rad * y / np.linalg.norm(y, axis=1)[:, None]
    x0 = P + y @ Ti.T
    te, xe, dd, _ = L.apparent(x0, np.broadcast_to(v, x0.shape), 0.0)
    a = np.arccos(np.clip(dd @ nrm, -1, 1))
    print(f"   v={v}: outline angular radius {ang_r:.9f}; surface images: max angle from the axis {a.max():.9f} "
          f"(excess {a.max() - ang_r:+.2e})")

print("2. Wigner angle: matrices vs closed form vs mpmath (50 digits) at the edges")
mp.mp.dps = 50


def mp_boost(b):
    b = [mp.mpf(x) for x in b]
    b2 = sum(x * x for x in b)
    g = 1 / mp.sqrt(1 - b2)
    Lm = mp.zeros(4, 4)
    Lm[0, 0] = g
    for i in range(3):
        Lm[0, i + 1] = Lm[i + 1, 0] = -g * b[i]
        for j in range(3):
            Lm[i + 1, j + 1] = (1 if i == j else 0) + g * g / (g + 1) * b[i] * b[j]
    return Lm


def mp_wigner(u, v):
    Lm = mp_boost(v) * mp_boost(u)
    # w from the inverse's first column: inverse = eta L^T eta
    eta = mp.diag([1, -1, -1, -1])
    inv = eta * Lm.T * eta
    w = [inv[i + 1, 0] / inv[0, 0] for i in range(3)]
    R = Lm * mp_boost([-x for x in w])
    tr = R[1, 1] + R[2, 2] + R[3, 3]
    a = [(R[3, 2] - R[2, 3]) / 2, (R[1, 3] - R[3, 1]) / 2, (R[2, 1] - R[1, 2]) / 2]
    return mp.atan2(mp.sqrt(sum(x * x for x in a)), (tr - 1) / 2)


cases = [("rapidities 3, 3 at 90 deg", [math.tanh(3), 0, 0], [0, math.tanh(3), 0]),
         ("rapidities 7, 7 at 90 deg", [math.tanh(7), 0, 0], [0, math.tanh(7), 0]),
         ("rapidities 7, 7 at 170 deg", [math.tanh(7), 0, 0],
          [math.tanh(7) * math.cos(math.radians(170)), math.tanh(7) * math.sin(math.radians(170)), 0]),
         ("antiparallel 0.999999, 0.999999 + 1e-3 sideways", [0.999999, 0, 0], [-0.999999, 1e-3, 0]),
         ("tiny: 1e-8, 1e-8", [1e-8, 0, 0], [0, 1e-8, 0])]
for name, u, v in cases:
    _, _, _, th = L.wigner_rotation(u, v)
    cf = float(L.wigner_angle_closed_form(u, v))
    ex = float(mp_wigner(u, v))
    print(f"   {name:48s} exact {ex:.15e}  matrices rel {(th - ex) / ex:+.1e}  closed form rel {(cf - ex) / ex:+.1e}")

print("3. axis_angle / su2_axis_angle near their edges")
for th in (1e-12, 1e-8, math.pi - 1e-9, math.pi, 2 * math.pi - 1e-9):
    n0 = np.array([0.3, -0.5, 0.8]); n0 /= np.linalg.norm(n0)
    n, t = L.axis_angle(L.rot3(n0, th))
    n2, t2 = L.su2_axis_angle(L.sl2_rotation(n0, th))
    print(f"   theta={th:.12g}: SO(3) -> {t:.12g} axis.n0={n @ n0:+.6f}; SU(2) -> {t2:.12g} axis.n0={n2 @ n0:+.6f}")

print("4. retarded_time / apparent: a point passing the observer, and the observer at the point's position")
te, xe, d, D = L.apparent([[1.0, 0, 0]], [[-0.5, 0, 0]], 2.0)
print(f"   x0=(1,0,0), v=-0.5 x, t_obs=2: t_e={te[0]:.6f} x_e={xe[0]} d={d[0]} D={D[0]:.6f}")
try:
    te, xe, d, D = L.apparent([[0.0, 0, 0]], [[0.5, 0, 0]], 0.0)
    print(f"   point at the observer at t_obs: t_e={te[0]}, d={d[0]} (division by |x_e| = 0)")
except Exception as e:
    print("   point at the observer at t_obs: raises", type(e).__name__, e)

print("5. add_velocities near c: |u (+) v| < 1 kept?")
for b in (1 - 1e-9, 1 - 1e-12, 1 - 1e-15):
    u = np.array([b, 0, 0]); v = np.array([b, 0, 0])
    w = L.add_velocities(u, v)
    try:
        g = float(L.gamma_of(w))
    except ValueError as e:
        g = f"raises: {e}"
    print(f"   b = 1 - {1 - b:.0e}: |w| = 1 - {1 - np.linalg.norm(w):.3e}, gamma_of(w) = {g}")

print("6. searchlight: integral of D^3/gamma over the sphere at high gamma (Gauss-Legendre 4000 nodes)")
for eta in (3.0, 6.0):
    b = math.tanh(eta)
    mu, wq = np.polynomial.legendre.leggauss(4000)
    n = np.stack([mu, np.sqrt(1 - mu * mu), 0 * mu], 1)
    I4, I3 = L.searchlight(n, [b, 0, 0])
    print(f"   eta={eta}: <D^3/gamma> = {0.5 * np.sum(wq * I3):.12f}")
