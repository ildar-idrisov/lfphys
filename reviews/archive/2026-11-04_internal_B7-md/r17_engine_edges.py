"""Edges of the engine's edits and measurements:
(a) MD.set_species(sigma=...) checks no overlap (only add / set(x=) do): a dense LJ fluid whose sigma grows 1 -> 1.4
    is accepted with an enormous potential energy, and the next steps blow up (the playground's substance change of a
    gas object calls exactly this);
(b) HardSpheres.pressure()['pressure'] in a box with walls against the momentum given to the walls."""
import common  # noqa: F401
import numpy as np

from lfphys.core.md.hard import HardSpheres
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import LennardJones

md = MD(dim=2, box=(20.0, 20.0), pair=LennardJones(2.5, "force"), dt=0.004, seed=5)
md.add_species("A")
md.fill("A", n=300, T=1.0)
md.step(200)
try:
    md.set_species("A", sigma=1.4)
    print(f"(a) set_species(sigma 1 -> 1.4) accepted: potential energy {md.potential_energy()['total']:.4g}, "
          f"largest |F| {np.abs(md.forces()).max():.4g}")
    try:
        md.step(20)
        print(f"    after 20 steps: max |v| {np.abs(md.velocities()).max():.4g}, T = {md.temperature()['T']:.4g}")
    except Exception as e:  # noqa: BLE001
        print("    stepping:", type(e).__name__, e)
except ValueError as e:
    print("(a) refused:", e)

hs = HardSpheres(2, (15.0, 15.0), boundary="walls", seed=3)
hs.add_species("a")
hs.fill("a", n=100, T=1.0)
hs.advance(50.0)
hs.reset_counters()
hs.advance(450.0)
p = hs.pressure()
print(f"(b) hard disks in a walled box: pressure() = {p['pressure']:.4f}; walls "
      f"{ {k: round(v, 4) for k, v in p['walls'].items()} }; with V = (L - sigma)^2 in place of L^2: "
      f"{p['pressure'] * 15.0 ** 2 / 14.0 ** 2:.4f}")
