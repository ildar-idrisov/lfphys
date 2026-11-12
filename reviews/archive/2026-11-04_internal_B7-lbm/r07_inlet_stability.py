"""R07: the claim "the velocity inlet is unstable from a cell Reynolds number of about 12" (STATUS V41 m; RE_CELL_MAX_OPEN
= 10 for every domain with an inlet or an outlet). A plain channel (no obstacle) with the link-wise velocity inlet and
the anti-bounce-back outlet at cell Reynolds numbers 12 ... 60 (the limit lifted in this script only), parabolic and
uniform profiles, Ma 0.1 at the largest inlet speed; then a cylinder (D = 20 cells) at 12 and 20.
Lattice units (dx = dt = rho = 1).

Run (from engine/): docker run --rm --name lf-b7rl-r07 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/lfphys -w /lf/lfphys light-funnel-viz python3 /out/r07_inlet_stability.py
"""
import numpy as np

from lfphys.core.fluids import lbm

lbm.RE_CELL_MAX_OPEN = 1e9  # lifted here only, to see where the scheme itself fails
U = 0.1 * lbm.CS


def channel(re_cell, profile, nx=240, ny=42, obstacle=False, collision="trt"):
    nu = U / re_cell
    fl = lbm.Flow2D((float(nx), float(ny)), 1.0, nu=nu, rho=1.0, dt=1.0, device="cpu", collision=collision,
                    sides={"left": lbm.Inlet(U, profile, ramp=500.0), "right": lbm.Outlet(0.0)})
    if obstacle:
        fl.add_obstacle(lbm.Disk((40.0, 20.5), 10.0))
    try:
        fl.advance(30000)
        ux, uy = fl.velocity()
        return "stable, max |u| / U_in = %.3f, density range %s" % (
            np.nanmax(np.hypot(ux, uy)) / U, np.round(fl.numbers()["density_range"], 4).tolist())
    except lbm.Unstable as e:
        return "UNSTABLE: " + str(e)[:120]


for profile in ("parabolic", "uniform"):
    for rc in (12, 20, 40, 60):
        print("plain channel, %s inlet, TRT, cell Re %g: %s" % (profile, rc, channel(rc, profile)))
for rc in (12, 20):
    print("plain channel, parabolic, BGK, cell Re %g: %s" % (rc, channel(rc, "parabolic", collision="bgk")))
for rc in (8, 12, 20):
    print("cylinder D = 20 cells, parabolic, TRT, cell Re %g (Re = %.0f): %s" % (
        rc, rc * 20 * 2 / 3, channel(rc, "parabolic", obstacle=True)))
