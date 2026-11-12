"""R09: where the open-boundary instability of R07 comes from, and whether the open-domain limit (cell Re 10) holds for
long runs. (a) the same channel driven by a body force with periodic ends (no inlet, no outlet) at cell Re 20 and 60;
(b) inlet + outlet at cell Re 20: the node where the deviation from the steady Poiseuille state first grows;
(c) inlet + outlet at cell Re 10 and 11 for 100 000 steps (the engine's limit is 10).
Lattice units (dx = dt = rho = 1).

Run (from engine/): docker run --rm --name lf-b7rl-r09 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz python3 /out/r09_open_boundary_instability.py
"""
import numpy as np

from lfphys.core.fluids import lbm

lbm.RE_CELL_MAX_OPEN = 1e9
lbm.RE_CELL_MAX = 1e9
U = 0.1 * lbm.CS
NX, NY = 240, 42

print("=== (a) periodic channel driven by a body force (Poiseuille with centre speed U) ===")
for rc in (20, 60):
    nu = U / rc
    g = 8 * nu * U / NY**2
    fl = lbm.Flow2D((float(NX), float(NY)), 1.0, nu=nu, rho=1.0, dt=1.0, device="cpu",
                    sides={"left": "periodic", "right": "periodic"}, gravity=(g, 0.0))
    fl.set_flow(velocity=lambda X, Y: (4 * U * Y * (NY - Y) / NY**2, 0 * X))
    try:
        fl.advance(30000)
        ux, uy = fl.velocity()
        print("cell Re %g: stable; max |uy| = %.3g, max ux / U = %.6f" % (rc, np.nanmax(abs(uy)), np.nanmax(ux) / U))
    except lbm.Unstable as e:
        print("cell Re %g: UNSTABLE %s" % (rc, str(e)[:100]))

print()
print("=== (b) inlet + outlet at cell Re 20: where |uy| first grows ===")
nu = U / 20
fl = lbm.Flow2D((float(NX), float(NY)), 1.0, nu=nu, rho=1.0, dt=1.0, device="cpu",
                sides={"left": lbm.Inlet(U, "parabolic"), "right": lbm.Outlet(0.0)})
fl.set_flow(velocity=lambda X, Y: (4 * U * Y * (NY - Y) / NY**2, 0 * X))
for k in range(60):
    try:
        fl.advance(32)
    except lbm.Unstable as e:
        print("blow-up:", str(e)[:90])
        break
    ux, uy = fl.velocity()
    a = np.abs(uy)
    i, j = np.unravel_index(np.argmax(a), a.shape)
    if k % 4 == 0 or a.max() > 1e-2:
        print("step %5d: max |uy| = %.3e at node (%d, %d); max |uy| in the first 5 columns %.3e, last 5 %.3e, "
              "middle %.3e" % (fl.steps, a.max(), i, j, a[:5].max(), a[-5:].max(), a[100:140].max()))
    if a.max() > 0.05:
        break

print()
print("=== (c) inlet + outlet at cell Re 10 and 11, 100 000 steps ===")
for rc in (10, 11):
    nu = U / rc
    fl = lbm.Flow2D((float(NX), float(NY)), 1.0, nu=nu, rho=1.0, dt=1.0, device="cpu",
                    sides={"left": lbm.Inlet(U, "parabolic", ramp=500.0), "right": lbm.Outlet(0.0)})
    done = 0
    try:
        while done < 100000:
            fl.advance(10000)
            done += 10000
        ux, uy = fl.velocity()
        print("cell Re %g: stable for %d steps; max |uy| %.3g" % (rc, done, np.nanmax(abs(uy))))
    except lbm.Unstable as e:
        print("cell Re %g: UNSTABLE after about %d steps: %s" % (rc, done, str(e)[:100]))
