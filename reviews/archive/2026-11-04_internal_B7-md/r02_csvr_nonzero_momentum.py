"""A global CSVR bath in a periodic box whose total momentum is not zero (an atom launched with a velocity, or a
molecule or gas added with momentum): MD.momentum_conserved() still says True and dof() says dN - d, the bath
rescales P with the rest (P is not conserved), and the reported temperature (centre-of-mass frame) settles below
the bath's: the bath fixes K_total, which includes P^2/2M. Control: the same run with P = 0."""
import common  # noqa: F401
import numpy as np

from lfphys.core.md.system import MD
from lfphys.theories.models.interatomic import LennardJones


def run(drift):
    n, rho = 256, 0.6
    L = (n / rho) ** (1 / 3)
    md = MD(dim=3, box=[L] * 3, pair=LennardJones(2.5, "force"), dt=0.004, seed=4)
    md.add_species("A")
    md.fill("A", n=n, T=1.0)
    md.set(md.keys, v=md.velocities() + np.array([drift, 0.0, 0.0]))
    md.add_thermostat("csvr", T=1.0, tau=0.05)
    P0 = md.momentum().copy()
    Ts, Px = [], []
    md.step(1000)
    for _ in range(400):
        md.step(25)
        Ts.append(md.temperature()["T"])
        Px.append(md.momentum()[0])
    Ts = np.array(Ts)
    print(f"drift {drift}: momentum_conserved() = {md.momentum_conserved()}, dof = {md.dof()}")
    print(f"   P_x at start {P0[0]:.4f}; during the run min {min(Px):.4f} max {max(Px):.4f} (constant if conserved)")
    print(f"   reported T (centre-of-mass frame): mean {Ts.mean():.4f} +- {Ts.std() / np.sqrt(len(Ts) / 4):.4f} "
          f"(bath 1.0); expected low by 2 <P^2/2M>/N_f = {np.mean(np.square(Px)) / (2 * n) * 2 / (3 * n - 3):.4f}")


run(0.0)
run(0.5)
