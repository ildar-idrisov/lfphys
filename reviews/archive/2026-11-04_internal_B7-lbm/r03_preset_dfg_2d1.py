"""R03: the playground's preset "cylinder_re20" (labelled "тест DFG 2D-1: сопротивление и подъёмная сила"), built by the
harness exactly as the player builds it, then advanced on the engine: what the inspector shows (the instantaneous C_x,
C_y; the mean is never started by the playground) against the DFG ranges (Schaefer & Turek 1996, Table 3: cD 5.5700 -
5.5900, cL 0.0104 - 0.0110); the mean over two acoustic periods for comparison.

Run (from engine/): docker run --rm --name lf-b7rl-r03 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests
-w /lf/lfphys light-funnel-viz python3 /out/r03_preset_dfg_2d1.py
"""
import numpy as np

from harness import Harness
from lfphys.core.fluids import lbm

h = Harness("p04_fluids", "cylinder_re20", {})
sim = h.sim
fl = sim.fl
cyl = [k for k, o in sim.objects.items() if o["type"] == "disk"][0]
oid = sim.ref[cyl][1]
print("grid %d x %d, dx = %.4g m, dt = %.4g s, D = %.1f cells, interpolated: %s" % (
    fl.nx, fl.ny, fl.units.dx, fl.units.dt, 0.1 / fl.units.dx, fl._obstacles[oid].interpolated))
ts, cds, cls = [], [], []
while fl.t < 12.0:
    fl.advance(int(round(0.02 / fl.units.dt)))
    F = sim._force(cyl, oid)  # what the inspector shows ("сейчас")
    ts.append(fl.t)
    cds.append(F["cd"])
    cls.append(F["cl"])
    assert F["mean"] is None
ts, cds, cls = map(np.array, (ts, cds, cls))
for t0 in (2.0, 4.0, 8.0, 10.0, 12.0):
    k = np.argmin(abs(ts - t0))
    print("t = %5.2f s: shown C_x = %.4f, C_y = %.5f" % (ts[k], cds[k], cls[k]))
late = ts > 8.0
print("shown C_x over 8-12 s: min %.4f max %.4f (DFG range 5.5700-5.5900)" % (cds[late].min(), cds[late].max()))
print("shown C_y over 8-12 s: min %.5f max %.5f (DFG range 0.0104-0.0110)" % (cls[late].min(), cls[late].max()))
T_ac = 4 * fl.size[0] / (fl.units.c * lbm.CS)
fl.reset_force_mean()
fl.advance_to(fl.t + 2 * T_ac)
m = sim._force(cyl, oid)["mean"]
print("mean over two acoustic periods (%.3f s each): C_x = %.4f, C_y = %.5f (u_ref = %.3g)" % (
    T_ac, m["cd"], m["cl"], sim._force(cyl, oid)["u_ref"]))
print("checks:", {k: (round(v["value"], 4) if "value" in v else v.get("relative_residual"), v["ok"])
                  for k, v in fl.checks().items()})
