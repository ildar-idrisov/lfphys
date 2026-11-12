# B2 review, check 1: signs and senses of the Lorentz-group conventions, by routes independent of the code under test.
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server light-funnel-viz python3 reviews/2026-10-27_internal_B2/c01_conventions.py
import math

import numpy as np
from scipy.integrate import solve_ivp

from lfphys.core import lorentz as L
from lfphys.core import spin_transport as T
from v09_thomas_3d.engine import loops as LP

np.set_printoptions(precision=6, suppress=True)
rng = np.random.default_rng(1)

print("1. Wigner rotation: R of boost(v) boost(u) = diag(1,R) boost(w); holonomy of rest->u->w->rest by burns")
worst_t, worst_h = 0.0, 0.0
for _ in range(200):
    u = rng.normal(size=3); u *= rng.uniform(0.05, 0.95) / np.linalg.norm(u)
    w = rng.normal(size=3); w *= rng.uniform(0.05, 0.95) / np.linalg.norm(w)
    vp = L.relative_velocity(u, w)
    _, Rw, n, th = L.wigner_rotation(u, vp)
    h = T.holonomy(T.Manoeuvre(T.polygon_burns([u, w])).end())
    # expectation (passive composition): gyroscope axes after the loop are the columns of R_W^T
    worst_h = max(worst_h, float(np.max(np.abs(h["R"] - Rw.T))))
    # v09's rotation vector of the field
    thf, rvf, _ = LP.triangle_field(u, w[None, :])
    Rf = L.rot3(rvf[0], np.linalg.norm(rvf[0]))
    worst_t = max(worst_t, float(np.max(np.abs(h["R"] - Rf))))
print(f"   max|R_hol - R_W^T| = {worst_h:.2e};  max|R_hol - rot(field rotation vector)| = {worst_t:.2e}")

print("2. u along x, v along y: axis and sense")
_, Rw, n, th = L.wigner_rotation([0.6, 0, 0], [0, 0.6, 0])
print(f"   n = {n}, theta = {th:.6f}; R_W = rot3(n, theta)? {np.allclose(Rw, L.rot3(n, th))}")
h = T.holonomy(T.Manoeuvre(T.polygon_burns([[0.6, 0, 0], L.add_velocities([0.6, 0, 0], [0, 0.6, 0])])).end())
print(f"   holonomy of the counter-clockwise loop (about +z): axis {h['axis']}, angle {h['angle']:.6f} -> retrograde: "
      f"{h['axis'][2] < 0}")

print("3. Thomas precession sense from an independent integration of the Fermi-Walker equation in lab time")
# circular motion v(t) = v (cos wt, sin wt, 0): the FW-transported spatial vector s (rest frame, pure boost) obeys
# ds/dt = omega_T x s with omega_T = gamma^2/(gamma+1) (a x v) (Jackson 11.119) -- check the sign against a direct
# integration of the 4-D Fermi-Walker equation (c = 1, signature +---, Minkowski products):
# dS/dtau = -U (A.S) + A (U.S) (keeps S.U = 0 since U.U = 1, A.U = 0), then project to the rest frame.
b, om = 0.5, 1.0  # 2 pi (gamma - 1) = 0.97 < pi: no ambiguity mod 2 pi
g = 1 / math.sqrt(1 - b * b)


def UA(t):
    v = b * np.array([math.cos(om * t), math.sin(om * t), 0.0])
    a = b * om * np.array([-math.sin(om * t), math.cos(om * t), 0.0])
    U = g * np.r_[1.0, v]
    A = np.r_[0.0, g * g * a]  # dU/dtau for |v| const: gamma * d(gamma v)/dt = gamma^2 a (gamma const)
    return U, A


def fw(t, S):  # in lab time: dS/dt = (1/gamma) [-U (A.S) + A (U.S)]
    U, A = UA(t)
    return (-U * L.mdot(A, S) + A * L.mdot(U, S)) / g


U0, _ = UA(0.0)
s0 = np.array([0.0, 1.0, 0.0])  # rest-frame spin along y; S = (gamma b.s, s + ...) with b.s = 0
S0 = np.r_[0.0, s0]
Tper = 2 * math.pi / om
sol = solve_ivp(fw, (0, Tper), S0, rtol=1e-12, atol=1e-14)
U1, _ = UA(Tper)
s1 = T.rest_spin(U1, sol.y[:, -1])
ang = math.atan2(s0[0] * s1[1] - s0[1] * s1[0], s1 @ s0)  # rotation of s about +z: (s0 x s1)_z
print(f"   after one revolution (anticlockwise): s turned by {ang:+.9f} rad about +z; expected -2 pi (gamma-1) mod 2 pi"
      f" = {(-2 * math.pi * (g - 1) + math.pi) % (2 * math.pi) - math.pi:+.9f}")
rho = math.atanh(b)
p = [T.Burn((1.0, 0.0, 0.0), rho), T.Turn((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), 1 / b, 2 * math.pi * math.sinh(rho))]
p.append(T.return_burn(T.Manoeuvre(p).end()))
h = T.holonomy(T.Manoeuvre(p).end())
print(f"   the engine's Thomas loop: axis {h['axis']}, angle {h['angle']:.9f} (signed about +z: "
      f"{h['angle'] * h['axis'][2]:+.9f})")

print("4. aberrate vs doppler reciprocity and transform_fields vs the Lorentz force on a test charge")
for _ in range(3):
    v = rng.normal(size=3); v *= 0.9 / np.linalg.norm(v)
    E, B = rng.normal(size=3), rng.normal(size=3)
    q = 1.0
    # force on a charge momentarily at rest in the moving frame: in that frame F' = q E'; in the lab
    # dp/dt = q (E + v x B). Transform: the frame's 3-force along v is the same, perpendicular F' = gamma F_perp.
    Ep, Bp = L.transform_fields(E, B, v)
    Flab = q * (E + np.cross(v, B))
    vh = v / np.linalg.norm(v)
    gam = float(L.gamma_of(v))
    Fpar = (Flab @ vh) * vh
    Fperp = Flab - Fpar
    Fexp = Fpar + gam * Fperp  # force in the rest frame of the charge (pure boost)
    print(f"   |q E' - F_rest| = {np.linalg.norm(q * Ep - Fexp):.2e}")
