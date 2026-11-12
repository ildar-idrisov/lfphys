"""r05 continued: where the extra heat of the "molecules" preset comes from. Energy bookkeeping at t = 0 (NVE, periodic):
the kinetic energy (as temperature), the LJ pair energy and each atom's share of it; the molecules are placed at
random and accepted up to max_insert_energy = 50 eps per inserted atom. The equilibrium temperature the kinetic
energy alone would give (357 kinetic + 60 vibrational-potential quadratic terms) against the measured ~105 K."""
import common  # noqa: F401
import numpy as np
from harness import Harness

from p03_molecules.viz import KELVIN, PS

h = Harness("p03_molecules", "molecules")
md = h.sim.md
pe = md.potential_energy()
K = md.kinetic_energy()
e_atom = md._per_particle_energy()
nf = md.dof()[0]
print(f"t = 0: K = {K:.2f} eps (T = {md.temperature()['T'] * KELVIN:.1f} K), LJ pair energy {pe['pair']:.2f} eps, "
      f"bond {pe['bond']:.3f}; per-atom potential energy: max {e_atom.max():.2f} eps, "
      f"atoms above 1 eps: {int(np.sum(e_atom > 1.0))}, sum of the positive shares {e_atom[e_atom > 0].sum():.2f} eps")
print(f"   equilibrium T from K alone: 2 K / ({nf} + 60) = {2 * K / (nf + 60) * KELVIN:.1f} K; "
      f"with the pair energy released as well: {2 * (K + pe['pair']) / (nf + 60) * KELVIN:.1f} K")
md.advance(md.t + 300 / PS)
pe = md.potential_energy()
print(f"t = 300 ps: T = {md.temperature()['T'] * KELVIN:.1f} K, LJ pair energy {pe['pair']:.2f} eps, "
      f"total E drift {md.energy_balance()['residual']:.3f} eps")
