"""R05: forces and torques at moving walls (Ladd) against closed forms - not covered by the engine's tests:
(a) Taylor-Couette: a disk turning at Omega inside a fixed cylinder (a Mask), torque per unit depth on the inner
    cylinder T = -4 pi mu Omega R1^2 R2^2 / (R2^2 - R1^2) (staircase walls: first order expected);
(b) the sign of the Magnus force: a disk turning counter-clockwise (omega > 0) in a stream along +x is pushed to -y
    (Kutta-Joukowski, lift = -rho U Gamma with Gamma = 2 pi R^2 omega > 0);
(c) the momentum booked at a moving lid in steady Couette flow: nu U / H per unit length and step (lattice units),
    equal and opposite at the fixed wall.
Lattice units (dx = dt = rho = 1).

Run (from engine/): docker run --rm --name lf-b7rl-r05 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz python3 /out/r05_moving_wall_forces.py
"""
import math

import numpy as np

from lfphys.core.fluids import lbm


def lattice(nx, ny, tau, **kw):
    return lbm.Flow2D((float(nx), float(ny)), 1.0, nu=(tau - 0.5) / 3, rho=1.0, dt=1.0, device="cpu", **kw)


print("=== (a) Taylor-Couette torque ===")
for N in (48, 96):
    tau = 0.8
    nu = (tau - 0.5) / 3
    R1, R2 = N / 8, N / 2 - 2
    Om = 0.02 / R1
    fl = lattice(N, N, tau)
    c = N / 2
    outer = lbm.Mask(lambda X, Y: (X - c) ** 2 + (Y - c) ** 2 >= R2**2)
    fl.add_obstacle(outer)
    oid = fl.add_obstacle(lbm.Disk((c, c), R1), omega=Om)
    nsteps = int(6 * (R2 - R1) ** 2 / nu)
    fl.advance(nsteps)
    fl.reset_force_mean()
    fl.advance(200)
    F = fl.forces()[oid]
    T_exact = -4 * math.pi * nu * Om * R1**2 * R2**2 / (R2**2 - R1**2)
    print("N = %d (R1 = %.1f, R2 = %.1f cells): torque %.6g, closed form %.6g, ratio %.4f; force on the disk (%.2g, %.2g)"
          % (N, R1, R2, F["torque"], T_exact, F["torque"] / T_exact, *F["force"]))

print()
print("=== (b) Magnus: a disk turning counter-clockwise in a stream along +x ===")
fl = lattice(120, 60, 0.8, sides={"left": "periodic", "right": "periodic"}, gravity=(2e-6, 0.0))
oid = fl.add_obstacle(lbm.Disk((60.0, 30.0), 5.0), omega=+0.004)
fl.advance(30000)
fl.reset_force_mean()
fl.advance(500)
F = fl.forces()[oid]
ux, _ = fl.velocity()
print("stream mean ux = %.4g (+x); omega = +0.004 (counter-clockwise); mean force (Fx, Fy) = (%.4g, %.4g); torque %.4g"
      % (np.nanmean(ux), F["mean"]["drag"], F["mean"]["lift"], F["torque"]))
print("expected: Fy < 0 (Kutta-Joukowski: L = -rho U Gamma, Gamma = 2 pi R^2 omega > 0); torque < 0 (opposes rotation)")

print()
print("=== (c) the momentum booked at a moving lid in steady Couette flow ===")
U, H, tau = 0.05, 16, 0.8
nu = (tau - 0.5) / 3
fl = lattice(4, H, tau, sides={"left": "periodic", "right": "periodic", "top": lbm.Wall(U)})
fl.advance(int(40 * H**2 / (nu * math.pi**2)))
last = fl._owner_sums("last")
print("top: x-momentum into the fluid per step %.12g; bottom %.12g; closed form +-nu U/H * nx = %.12g" % (
    last["top"][1], last["bottom"][1], nu * U / H * 4))
