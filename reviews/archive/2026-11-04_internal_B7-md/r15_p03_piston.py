"""p03 preset "piston" (gas under a free piston, p_ext 50 mN/m = 3.5 reduced, a thermal floor at 300 K): what the run
shows - the piston's height, the gas temperature, the first-law check (Q, W, residual). Then an edit of the piston's
external pressure only: _piston() passes X = the object's 'position' value every time, so the piston jumps back to
its initial height."""
import common  # noqa: F401
from harness import Harness

from p03_molecules.viz import KELVIN, NM


def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)


h = Harness("p03_molecules", "piston")
md = h.sim.md
for k in range(6):
    run(h, 10.0, 20)
    b = md.energy_balance()
    p = md.piston()
    print(f"t = {h.sim.t * 1e12:5.1f} ps: piston at {p['X'] * NM:6.3f} nm, V = {p['V']:+.3f}, hits {p['hits']}, "
          f"T = {md.temperature()['T'] * KELVIN:6.1f} K; Q = {b['Q']:+9.3f}, W = {b['W']:+9.3f}, "
          f"residual = {b['residual']:+.3e} (reduced energy)")
c = h.checks().get("energy")
print("energy check:", {k: c.get(k) for k in ("value", "info", "ok")}, "\n   note:", c.get("note"))
X_before = md.piston()["X"] * NM
ne = len(h.errors())
h.cmd("scene", op="set", id="o2", values={"p_ext": 40.0})
print(f"after setting p_ext 50 -> 40 mN/m: piston at {md.piston()['X'] * NM:.3f} nm (was {X_before:.3f}); "
      f"errors {h.errors()[ne:]}")
