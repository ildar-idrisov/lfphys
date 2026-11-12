"""P13 reproduction: the bisection's «сейчас можно до …» ignores the 10 % bond limit (molecules)."""
import re
import sys
sys.path[:0] = ["/lf/visualizations/tests", "/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys"]
from harness import Harness  # noqa: E402

h = Harness("p03_molecules", None, {"dim": "2d", "Lx": 8.0, "Ly": 8.0, "boundary": "periodic"})
h.cmd("scene", op="add", type="molecule", values={"shape": "dimer", "count": 60, "T": 120.0, "bond": 1.1})
h.run_to(2e-12)
print("errors so far:", h.errors())
n0 = len(h.errors())
h.set(Lx=5.0)
errs = h.errors()[n0:]
print("refusal 1:", errs)
m = re.search(r"Lx ≈ ([\d,]+) нм", errs[-1]) if errs else None
if m:
    fit = float(m.group(1).replace(",", "."))
    print("named size:", fit, "relative change:", 1 - fit / 8.0)
    n1 = len(h.errors())
    h.set(Lx=fit)
    print("trying the named size:", h.errors()[n1:] or "accepted", "| live Lx:", h.sim.live["Lx"])
