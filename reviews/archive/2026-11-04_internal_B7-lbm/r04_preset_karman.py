"""R04: the playground's preset "karman" (DFG 2D-2, Re = 100) run to a developed vortex street (the preset test runs
0.22 s only): the running checks the player would show (cell Reynolds number on the measured largest speed against the
open-domain limit 10; Mach), the shown C_x / C_y against the DFG 2D-2 ranges (Schaefer & Turek 1996, Table 4: cDmax
3.22-3.24, cLmax 0.99-1.01, St 0.295-0.305).

Run (from engine/): docker run --rm --name lf-b7rl-r04 -v $PWD:/lf:ro -v <this folder>:/out -e PYTHONDONTWRITEBYTECODE=1
-e LFPHYS_NO_GPU=1 -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests
-w /lf/lfphys light-funnel-viz python3 /out/r04_preset_karman.py
"""
import numpy as np

from harness import Harness

h = Harness("p04_fluids", "karman", {})
sim = h.sim
fl = sim.fl
cyl = [k for k, o in sim.objects.items() if o["type"] == "disk"][0]
oid = sim.ref[cyl][1]
print("grid %d x %d, dx = %.4g m, dt = %.4g s, declared u_max %.3g m/s, declared cell Re %.3g (limit %g)" % (
    fl.nx, fl.ny, fl.units.dx, fl.units.dt, fl.u_max, fl.u_max * fl.units.dx / fl.nu, fl.re_cell_limit()))
ts, cds, cls, rec, ma = [], [], [], [], []
nsub = int(round(0.01 / fl.units.dt))
first_fail = None
while fl.t < 11.0:
    fl.advance(nsub)
    F = sim._force(cyl, oid)
    n = fl.numbers()
    ts.append(fl.t)
    cds.append(F["cd"])
    cls.append(F["cl"])
    rec.append(n["re_cell"])
    ma.append(n["mach_max"])
    if first_fail is None and n["re_cell"] > fl.re_cell_limit():
        first_fail = (fl.t, n["re_cell"], n["u_max"])
ts, cds, cls, rec, ma = map(np.array, (ts, cds, cls, rec, ma))
print("cell Re over the run: max %.4g at t = %.3g s; first above the limit: %s" % (rec.max(), ts[np.argmax(rec)],
                                                                                 first_fail))
print("largest Mach: %.4g" % ma.max())
late = ts > 7.0
print("shown C_x over 7-11 s: max %.4f (DFG cDmax 3.22-3.24)" % cds[late].max())
print("shown C_y over 7-11 s: max %.4f, min %.4f, (max-min)/2 %.4f (DFG cLmax 0.99-1.01)" % (
    cls[late].max(), cls[late].min(), 0.5 * (cls[late].max() - cls[late].min())))
c = cls[late] - cls[late].mean()
tl = ts[late]
up = np.flatnonzero((c[:-1] < 0) & (c[1:] >= 0))
tz = tl[up] - c[up] * (tl[up + 1] - tl[up]) / (c[up + 1] - c[up])
print("St from the shown C_y: %.4f (DFG 0.295-0.305)" % (0.1 * (len(tz) - 1) / (tz[-1] - tz[0])))
ch = fl.checks()
print("final checks:", {k: v["ok"] for k, v in ch.items()})
np.savez("/out/r04_series.npz", t=ts, cd=cds, cl=cls, re_cell=rec, mach=ma)
