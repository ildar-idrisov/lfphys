"""p03's pass/fail momentum check compares |P| itself with 1e-10 sum|v|, not the change of P: a world whose momentum
is conserved but not zero (an atom launched with a velocity into the periodic, NVE preset "maxwell") is reported as
failing. And a global CSVR with that momentum keeps momentum_conserved() True while it rescales P (r02)."""
import common  # noqa: F401
import numpy as np
from harness import Harness


def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)


def add_atom(h, vx):
    ne = len(h.errors())
    for x in np.arange(0.3, 12.0, 0.37):
        for y in np.arange(0.3, 12.0, 0.41):
            h.cmd("scene", op="add", type="atom", values={"x": float(x), "y": float(y), "vx": vx, "vy": 0.0})
            if len(h.errors()) == ne:
                return x, y
            ne = len(h.errors())
    raise RuntimeError("no free place")


h = Harness("p03_molecules", "maxwell")
run(h, 2.0, 40)
print("before:", {k: (c.get("ok"), c.get("value")) for k, c in h.checks().items() if k == "momentum"})
x, y = add_atom(h, 400.0)
md = h.sim.md
P_after_add = md.momentum().copy()
print(f"atom added at ({x:.2f}, {y:.2f}) nm with vx = 400 m/s; P = {P_after_add}")
Ps = []
for _ in range(6):
    run(h, 1.0, 20)
    Ps.append(md.momentum().copy())
c = h.checks()["momentum"]
print("momentum check after:", {"ok": c.get("ok"), "value": c.get("value"), "tol": c.get("tol")})
print("P during the run (NVE, periodic: conserved):", [f"{p[0]:.12f}" for p in Ps])
print("max |P(t) - P(add)| =", float(np.max(np.abs(np.array(Ps) - P_after_add))))
print("momentum_conserved():", md.momentum_conserved(), "; errors:", h.errors())
