"""R01: (a) an obstacle given a velocity does not move (only its surface velocity is imposed on a fixed shape), which the
playground's help calls "the body moves through the fluid, carried with its shape"; the fixed "moving" disk is a
source on its front and a sink on its back; (b) a uniform body force: hydrostatic density variation g H / c_s^2 is not
checked (the playground's default gravity in the DFG-sized world); (c) gravity next to a constant-pressure outlet.

Run (from engine/): docker run --rm --name lf-b7rl-r01 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r01_moving_body_and_gravity.py
"""
import numpy as np

from lfphys.core.fluids import lbm

print("=== (a) a disk with velocity (0.05, 0) m/s in a closed box of the DFG fluid ===")
fl = lbm.Flow2D((0.4, 0.2), 0.004, nu=1e-3, rho=1.0, u_max=0.1, mach=0.1, device="cpu")
oid = fl.add_obstacle(lbm.Disk((0.2, 0.1), 0.02), velocity=(0.05, 0.0))
c0 = fl.obstacles()[0]["center"]
solid0 = fl.solid().copy()
fl.advance_to(4.0)
c1 = fl.obstacles()[0]["center"]
print("centre before / after 4 s:", c0, c1, " solid mask unchanged:", bool(np.array_equal(solid0, fl.solid())))
L = fl._L
k = L["owner"] == oid
ex = lbm.EX[L["dir"][k]]
acc = fl._link_acc()["acc_m"][k]
wx = L["wx"][k]
front = wx > 0.2
print("mass booked through the disk's links (lattice units): front half %.4g, back half %.4g, total %.3g"
      % (acc[front].sum(), acc[~front].sum(), acc.sum()))
ux, uy = fl.velocity()
print("max |u| in the box after 4 s: %.4g m/s (a body moving at 0.05 m/s for 4 s would have travelled 0.2 m)"
      % np.nanmax(np.hypot(ux, uy)))
b = fl.balance()
print("mass now / start:", b["mass"]["now"], b["mass"]["start"], " checks ok:", {k: v["ok"] for k, v in fl.checks().items()})

print()
print("=== (b) the playground's default gravity (0, -9.81) in the default DFG-size world (2.2 x 0.41 m, 440 nodes) ===")
fl = lbm.Flow2D((2.2, 0.41), 0.005, nu=1e-3, rho=1.0, u_max=0.45, mach=0.1, device="cpu")
fl.set_gravity((0.0, -9.81))
g_lat = 9.81 * fl.units.dt**2 / fl.units.dx
print("lattice g = %.4g; g H / c_s^2 = %.4g (expected hydrostatic relative density change)" % (g_lat, g_lat * fl.ny / lbm.CS2))
fl.advance_to(3.0)
n = fl.numbers()
print("density range after 3 s:", n["density_range"])
ch = fl.checks()
print("compressibility check:", ch["compressibility"]["value"], "limit", ch["compressibility"]["limit"], "ok", ch["compressibility"]["ok"])
print("refused? no - set_gravity accepted the force (no check of g H / c_s^2)")

print()
print("=== (c) gravity across a channel with a constant-pressure outlet (DFG fluid, 0.4 x 0.1 m, no inflow) ===")
fl = lbm.Flow2D((0.4, 0.1), 0.002, nu=1e-3, rho=1.0, u_max=0.05, mach=0.1, device="cpu",
                sides={"left": lbm.Wall(), "right": lbm.Outlet(0.0)})
fl.set_gravity((0.0, -0.5))
fl.advance_to(20.0)
ux, uy = fl.velocity()
print("fluid at rest in a hydrostatic field should stay at rest; max |u| after 20 s = %.4g m/s, outlet flow rate %.4g kg/(s m)"
      % (np.nanmax(np.hypot(ux, uy)), fl.flow_rates().get("right", 0.0)))
print("density range:", fl.numbers()["density_range"])
