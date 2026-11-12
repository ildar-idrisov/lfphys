"""v03: the run stops integrating when the norm left in the window drops below 1e-5 (viz.py:_evolve, `norm[-1] < 1e-5`)
and the run time is t_end = 1.3 (L/v_in + L/v_out). Test whether these two cut-offs explain the disagreements of
scripts 01/02: re-run with the threshold 1e-9 and t_end x 4 (the method source is patched in this process only, by
text replacement + exec; the project files are not touched).
Output: out/03_v03_stop_criterion.txt
"""
import inspect
import sys
import textwrap
import time

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402
import v03_quantum_1d.viz as V  # noqa: E402

OUT = open("out/03_v03_stop_criterion.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")
    OUT.flush()


src = textwrap.dedent(inspect.getsource(V.Simulation._evolve))
assert "norm[-1] < 1e-5" in src and "t_end = 1.3 *" in src
orig = V.Simulation._evolve
ns = dict(V.__dict__)


def patched(threshold, tfac):
    s = src.replace("norm[-1] < 1e-5", f"norm[-1] < {threshold}").replace("t_end = 1.3 *", f"t_end = {1.3 * tfac} *")
    s = s.replace("n_store = 600", f"n_store = {int(600 * tfac)}")  # keep the same store step
    exec(s, ns)
    return ns["_evolve"]


CASES = [("thick barrier 5 nm", {"width": 5.0}),
         ("step V0 = 0.75, E = 0.8", {"scenario": "step", "V0": 0.75, "energy": 0.8}),
         ("free, E = 0.05, sigma = 1", {"scenario": "free", "energy": 0.05, "sigma": 1.0}),
         ("barrier, E = 0.05, sigma = 1", {"energy": 0.05, "sigma": 1.0})]
for name, params in CASES:
    for thr, tfac in ((1e-5, 1), (1e-9, 4)):
        V.Simulation._evolve = orig if (thr, tfac) == (1e-5, 1) else patched(thr, tfac)
        t0 = time.time()
        h = Harness("v03_quantum_1d", None, params, seed=1)
        c, a = h.checks()["T0"], h.checks()["abs0"]
        say(f"{name}: stop at norm < {thr:g}, t_end x {tfac}: T_run = {c['value']:.6e}, T_ref(run) = {c['ref']:.6e}, "
            f"rel = {(c['value'] - c['ref']) / c['ref']:+.3e}, absorbed = {a['value']:.7f}, "
            f"left in window = {h.sim.norm[-1]:.1e}, {time.time() - t0:.1f} s")
V.Simulation._evolve = orig
