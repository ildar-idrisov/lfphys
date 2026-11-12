"""Numbers and statements in p03's texts against the engine:
(a) the field's help: "Для аргона единица ≈ 9·10¹¹ м/с²" - the acceleration unit eps/(m sigma);
(b) the 2-D pressure unit (mN/m) and the preset piston's 50 mN/m in reduced units and against the gas's own pressure;
(c) "gas: random places without overlaps" (README, palette help) - the positions MD.fill gives;
(d) the energy check's note "W = работа поршня и правок": an edit (a substance change) moves E0, W stays;
(e) a slab (walls along y, periodic along x), NVE: P_x is conserved but dof() counts d N."""
import common  # noqa: F401
import numpy as np
from harness import Harness

from lfphys.core.md.system import MD
from p03_molecules.viz import NM, U

print(f"(a) acceleration unit eps/(m sigma) = {U.acceleration_m_s2:.3e} m/s^2 (help text: 9e11); "
      f"Earth's g = {U.from_m_s2(9.81):.2e} reduced")
p2 = U.pressure_Pa(2)
print(f"(b) 2-D pressure unit eps/sigma^2 = {p2 * 1e3:.3f} mN/m; preset piston p_ext 50 mN/m = {50e-3 / p2:.3f} reduced")
h = Harness("p03_molecules", "piston")
md = h.sim.md
A = md.L[0]
gas_h = 8.0 / NM
print(f"    the preset's gas: N = {sum(1 for s in md.particles()['species'] if s == 'o1')} in {A:.1f} x {gas_h:.1f} "
      f"sigma at 300 K = {300 / U.temperature_K:.3f}: ideal-gas pressure N T / A = "
      f"{200 * (300 / U.temperature_K) / (A * gas_h):.3f} reduced = {200 * (300 / U.temperature_K) / (A * gas_h) * p2 * 1e3:.2f} mN/m")
hm = Harness("p03_molecules", "maxwell")
x = hm.sim.md.positions()
print(f"(c) preset 'maxwell' gas, {len(x)} atoms: distinct x coordinates {len(np.unique(np.round(x[:, 0], 9)))}, "
      f"distinct y coordinates {len(np.unique(np.round(x[:, 1], 9)))} (random places would give {len(x)} each)")
hm.run_to(2e-12)
b0 = hm.sim.md.energy_balance()
hm.cmd("scene", op="set", id="o1", values={"substance": "custom", "mass": 80.0})
b1 = hm.sim.md.energy_balance()
print(f"(d) substance change (mass 39.948 -> 80 u, velocities kept): E0 {b0['E0']:.4f} -> {b1['E0']:.4f}, "
      f"W {b0['W']:.4f} -> {b1['W']:.4f}, residual {b1['residual']:.2e}")
s = MD(dim=2, box=(20.0, 20.0), boundary=["periodic", "walls"], pair=None, dt=0.01, seed=1)
s.add_species("A")
s.fill("A", n=50, T=1.0)
P0 = s.momentum().copy()
s.step(2000)
print(f"(e) slab, NVE: P_x {P0[0]:.3e} -> {s.momentum()[0]:.3e} (conserved); dof() = {s.dof()}")
