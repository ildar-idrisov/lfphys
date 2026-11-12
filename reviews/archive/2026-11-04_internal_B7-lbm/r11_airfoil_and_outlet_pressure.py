"""R11: (a) the playground's preset "airfoil" (NACA 2412 at 8 deg, periodic top and bottom) run past its start (the
preset test runs 0.33 s): the running checks (cell Re, Mach), C_x and C_y as shown; (b) the outlet pressure is not
checked against the compressibility limit (a few pascals in the DFG world are tens of per cent of the density).

Run (from engine/): docker run --rm --name lf-b7rl-r11 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests
-w /lf/lfphys light-funnel-viz python3 /out/r11_airfoil_and_outlet_pressure.py
"""
import numpy as np

from harness import Harness
from lfphys.core.fluids import lbm

print("=== (b) outlet pressure 10 Pa in the DFG-size world (u_max 0.45 m/s) ===")
fl = lbm.Flow2D((2.2, 0.41), 0.005, nu=1e-3, rho=1.0, u_max=0.45, mach=0.1, device="cpu")
print("pressure scale c_s^2 rho (dx/dt)^2 = %.4g Pa" % (lbm.CS2 * fl.units.rho * fl.units.c**2))
fl.set_side("right", lbm.Outlet(10.0))
print("accepted; the outlet's lattice density:", float(fl.units.density_of_pressure(10.0)))
try:
    fl.advance_to(1.0)
    ch = fl.checks()
    print("after 1 s: density range", np.round(ch["compressibility"]["density_range"], 4).tolist(), "mach",
          round(ch["mach"]["value"], 4), "compressibility ok", ch["compressibility"]["ok"], "mach ok", ch["mach"]["ok"])
except lbm.Unstable as e:
    print("the first advance blew up:", str(e)[:400])
for p in (1.0, 2.0):
    fl = lbm.Flow2D((2.2, 0.41), 0.005, nu=1e-3, rho=1.0, u_max=0.45, mach=0.1, device="cpu",
                    sides={"right": lbm.Outlet(p)})
    try:
        fl.advance_to(1.0)
        ch = fl.checks()
        print("outlet %.1f Pa: after 1 s density range %s, Mach %.3g (declared 0.1); checks failing: %s" % (
            p, np.round(ch["compressibility"]["density_range"], 4).tolist(), ch["mach"]["value"],
            [k for k, v in ch.items() if not v["ok"]]))
    except lbm.Unstable as e:
        print("outlet %.1f Pa: blew up: %s" % (p, str(e)[:200]))

print()
print("=== (a) the airfoil preset ===")
h = Harness("p04_fluids", "airfoil", {})
sim = h.sim
fl = sim.fl
foil = [k for k, o in sim.objects.items() if o["type"] == "airfoil"][0]
oid = sim.ref[foil][1]
print("grid %d x %d, dx = %.4g m, dt = %.4g s, chord %.1f cells, solid nodes %d, Re = %.0f" % (
    fl.nx, fl.ny, fl.units.dx, fl.units.dt, 0.4 / fl.units.dx, int(fl.solid().sum()), 1.0 * 0.4 / fl.nu))
ts, cds, cls, rec, ma = [], [], [], [], []
nsub = int(round(0.02 / fl.units.dt))
try:
    while fl.t < 6.0:
        fl.advance(nsub)
        F = sim._force(foil, oid)
        n = fl.numbers()
        ts.append(fl.t)
        cds.append(F["cd"])
        cls.append(F["cl"])
        rec.append(n["re_cell"])
        ma.append(n["mach_max"])
except lbm.Unstable as e:
    print("UNSTABLE:", str(e)[:200])
ts, cds, cls, rec, ma = map(np.array, (ts, cds, cls, rec, ma))
print("ran to t = %.2f s; cell Re max %.3g (limit %g), first above the limit at t = %s; Mach max %.3g" % (
    ts[-1], rec.max(), fl.re_cell_limit(), ts[np.argmax(rec > fl.re_cell_limit())] if (rec > fl.re_cell_limit()).any()
    else None, ma.max()))
late = ts > ts[-1] - 2.0
print("shown C_x over the last 2 s: %.4f ... %.4f; C_y: %.4f ... %.4f" % (cds[late].min(), cds[late].max(),
                                                                       cls[late].min(), cls[late].max()))
print("final checks:", {k: v["ok"] for k, v in fl.checks().items()})
