"""P5 review, check 12: input validation of the time grids (the docstrings say "increasing").

Run: python3 s12_time_grid_validation.py
"""
import argparse

import numpy as np

from lfphys.core.quantum import jumps as J, open_systems as OS, two_level as TL

argparse.ArgumentParser(description=__doc__).parse_args()
H, c = TL.hamiltonian(1.0, 0.0), TL.collapse_operators(1.0, 2.0)
rho0 = TL.density_matrix([0, 0, -1])
r, err, _ = OS.evolve(H, c, rho0, [0.0, 2.0, 1.0])
ex = OS.propagate(OS.liouvillian(H, c), rho0, [0.0, 2.0, 1.0])
print(f"evolve, times [0, 2, 1]: {len(r)} states; state labelled t=1 equals the t=2 state: "
      f"{np.allclose(r[2], ex[1])}; error to the true t=1 state {OS.trace_norm(r[2] - ex[2]):.2e}; err[2] = {err[2]:.1e}")
r, err, _ = OS.evolve(H, c, rho0, [0.0, -1.0])
print(f"evolve, times [0, -1]: {len(r)} state(s) returned for 2 requested times")
rr = OS.propagate(OS.liouvillian(H, c), rho0, [-3.0])[0]
print(f"propagate at t = -3: smallest eigenvalue {OS.state_checks(rr)['min_eig']:.3f} (no error raised)")
tr = J.trajectories(H, c, TL.G, [0.0, -2.0], 20, np.random.default_rng(1), e_ops=[TL.PE])
print(f"trajectories, times [0, -2]: no error; <P_e(-2)> = {tr.mean(0)[-1]:.3f}, jumps {sum(len(x) for x in tr.jump_times)}")
