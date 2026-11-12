"""v03: is the 55 % disagreement of the packet transmission for a 5 nm barrier (script 01) a convergence error of the
time-dependent route? Re-run the same world with the time step and the grid step refined (monkey-patched in this
process only; the project files are not touched), and with a longer run time.
Output: out/02_v03_thick_barrier_convergence.txt
"""
import sys
import time

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
import v03_quantum_1d.viz as V  # noqa: E402

OUT = open("out/02_v03_thick_barrier_convergence.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


orig_dt = V.Simulation._dt_max
for width in (3.0, 5.0):
    for fdt in (1.0, 0.5, 0.25):
        V.Simulation._dt_max = lambda self, f=fdt: f * orig_dt(self)
        t0 = time.time()
        h = Harness("v03_quantum_1d", None, {"width": width}, seed=1)
        c = h.checks()["T0"]
        say(f"width {width} nm, dt x {fdt}: T_run = {c['value']:.6e}, T_ref = {c['ref']:.6e}, "
            f"rel = {(c['value'] - c['ref']) / c['ref']:+.3e}, ok = {c['ok']}, n_grid = {h.sim.n_grid}, "
            f"abs = {h.checks()['abs0']['value']:.6f}, {time.time() - t0:.1f} s")
V.Simulation._dt_max = orig_dt
