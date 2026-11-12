"""p03: a change of an object's number / region / temperature is on_remove + on_add. When the add is refused, the
framework restores the object's values but not the engine: the atoms are gone while the scene still lists the object
with its old values (LJ world, preset "maxwell": n 300 -> 5000 does not fit)."""
import common  # noqa: F401
from harness import Harness

h = Harness("p03_molecules", "maxwell")
h.run_to(1e-12)
print("before: atoms", h.sim.md.n, "; scene", {k: o["values"]["n"] for k, o in h.sim.objects.items()},
      "; parts", {k: len(v) for k, v in h.sim.parts.items()})
h.cmd("scene", op="set", id="o1", values={"n": 5000})
print("refused:", h.errors())
print("after: atoms", h.sim.md.n, "; scene", {k: o["values"]["n"] for k, o in h.sim.objects.items()},
      "; parts", {k: len(v) for k, v in h.sim.parts.items()}, "; kind", h.sim.kind)
ne = len(h.errors())
h.cmd("scene", op="remove", id="o1")
print("then removing the object:", h.errors()[ne:])
