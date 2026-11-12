"""Bit-identical continuation from state_dict in cases the engine's tests do not cover: hard disks with a thermal wall
(random re-emission) and two species; MD with a soft LJ wall, a driven piston, a Langevin bath in a region, bonded
molecules and an energy-shifted LJ pair term (2-D). Each: save mid-run, continue the original and the copy, compare
positions, velocities, counters and the first-law balance exactly."""
import common  # noqa: F401
import numpy as np

from lfphys.core.md.hard import HardSpheres
from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import HarmonicAngle, HarmonicBond, LennardJones, LJWall

hs = HardSpheres(2, (14.0, 12.0), boundary=["periodic", "walls"], seed=8)
hs.add_species("a", mass=1.0, sigma=1.0)
hs.add_species("b", mass=3.0, sigma=0.7)
hs.fill("a", n=60, T=1.0, region=([0, 0.6], [14, 6]))
hs.fill("b", n=40, T=1.0, region=([0, 6.5], [14, 11.6]))
hs.set_wall("y", "lo", "thermal", T=2.0)
hs.advance(20.0)
twin = HardSpheres.from_state_dict(hs.state_dict())
hs.advance(60.0)
twin.advance(60.0)
print("hard + thermal wall:", np.array_equal(hs.positions(True), twin.positions(True)),
      np.array_equal(hs.velocities(), twin.velocities()), hs.counters() == twin.counters(),
      hs.energy_balance() == twin.energy_balance())

md = MD(dim=2, box=(16.0, 14.0), boundary="walls", pair=LennardJones(2.5, "energy"), dt=0.004, seed=12)
md.add_species("A")
md.add_species("B", mass=2.0, sigma=1.1)
md.set_bond_type("b", HarmonicBond(150.0, 1.1))
md.set_angle_type("t", HarmonicAngle(30.0, 2.0))
md.fill("A", n=80, T=1.2, region=([0.5, 0.5], [15.5, 8.0]))
for k in range(4):
    c = np.array([2.5 + 3.5 * k, 10.5])
    md.add_molecule("B", [c + [-0.9, 0.0], c, c + [0.5, 0.9]], bonds=[(0, 1, "b"), (1, 2, "b")],
                    angles=[(0, 1, 2, "t")], T=1.0)
md.set_wall("x", "lo", "soft", term=LJWall(2, epsilon=1.0, sigma=1.0, cutoff=2.5))
md.set_piston("y", X=13.5, mass=float("inf"), V=-0.05)
md.add_thermostat("langevin", T=1.5, gamma=0.5, region=([8.0, 0.0], [16.0, 14.0]))
md.step(300)
twin = MD.from_state_dict(md.state_dict())
md.step(700)
twin.step(700)
print("MD soft wall + driven piston + local Langevin + molecules:", np.array_equal(md.positions(True),
      twin.positions(True)), np.array_equal(md.velocities(), twin.velocities()), md.counters() == twin.counters(),
      md.energy_balance() == twin.energy_balance(), "| piston X", md.piston()["X"] == twin.piston()["X"])
