"""R13: (a) the transverse velocity the link-wise velocity inlet leaves in a plain Poiseuille channel (started from the
exact parabola) against the cell Reynolds number, and how far it reaches into the channel; (b) flow_rates() right
after a geometry edit (the last step's link records are zeroed by the edit; forces() keeps them, flow_rates() does
not); (c) the mass and momentum balance of an open channel through edits: a turning disk added, an interpolated disk
added and moved, both removed (round-off expected). Lattice units.

Run (from engine/): docker run --rm --name lf-b7rl-r13 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz python3 /out/r13_inlet_layer_rates_balance.py
"""
import numpy as np

from lfphys.core.fluids import lbm

U = 0.1 * lbm.CS
NX, NY = 240, 42

print("=== (a) |u_y| / U left by the velocity inlet (steady, 20 000 steps from the exact parabola) ===")
for rc in (1, 2, 5, 10):
    nu = U / rc
    fl = lbm.Flow2D((float(NX), float(NY)), 1.0, nu=nu, rho=1.0, dt=1.0, device="cpu",
                    sides={"left": lbm.Inlet(U, "parabolic"), "right": lbm.Outlet(0.0)})
    fl.set_flow(velocity=lambda X, Y: (4 * U * Y * (NY - Y) / NY**2, 0 * X))
    fl.advance(20000)
    ux, uy = fl.velocity()
    a = np.abs(uy) / U
    exact = 4 * U * fl.y * (NY - fl.y) / NY**2
    print("cell Re %4g: max |uy|/U in column 0: %.3e, column 2: %.3e, column 5: %.3e, column 20: %.3e; "
          "max |ux - parabola|/U in column 0: %.3e, mid-channel: %.3e" % (
              rc, a[0].max(), a[2].max(), a[5].max(), a[20].max(), np.abs(ux[0] - exact).max() / U,
              np.abs(ux[NX // 2] - exact).max() / U))

print()
print("=== (b) flow_rates() before and right after an edit ===")
fl = lbm.Flow2D((120.0, 30.0), 1.0, nu=0.05, rho=1.0, dt=1.0, device="cpu",
                sides={"left": lbm.Inlet(0.03, "parabolic"), "right": lbm.Outlet(0.0)})
fl.advance(3000)
print("before:", {k: round(v, 6) for k, v in fl.flow_rates().items()})
fl.add_obstacle(lbm.Disk((80.0, 15.0), 3.0))
print("right after adding a disk (no step yet):", fl.flow_rates())
fl.advance(1)
print("one step later:", {k: round(v, 6) for k, v in fl.flow_rates().items()})

print()
print("=== (c) the balance of an open channel through edits ===")
fl = lbm.Flow2D((160.0, 40.0), 1.0, nu=0.04, rho=1.0, dt=1.0, device="cpu", gravity=(0.0, -1e-6), dye=0.02,
                sides={"left": lbm.Inlet(0.04, "parabolic", ramp=300.0, dye=1.0), "right": lbm.Outlet(0.0)})
fl.advance(1500)
a = fl.add_obstacle(lbm.Disk((50.0, 20.0), 5.0), omega=0.003)
fl.advance(1500)
b = fl.add_obstacle(lbm.Disk((100.0, 22.0), 4.3), interpolated=True)
fl.advance(1500)
fl.update_obstacle(b, shape=lbm.Disk((104.0, 18.0), 4.3))
fl.advance(1500)
fl.remove_obstacle(a)
fl.remove_obstacle(b)
fl.advance(1500)
bal = fl.balance()
print("steps %d: mass residual %.3e (relative), momentum %.3e, dye %.3e; booked keys %s" % (
    bal["steps"], bal["mass"]["relative_residual"], bal["momentum"]["relative_residual"],
    bal["dye"]["relative_residual"], sorted(bal["lattice"]["books"])))
print("checks:", {k: v["ok"] for k, v in fl.checks().items()})
