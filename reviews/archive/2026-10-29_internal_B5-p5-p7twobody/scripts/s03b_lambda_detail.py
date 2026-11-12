"""P5 review, check 3b: the Lambda-system P_e comparison of s03 in detail (means, standard errors, exact values),
for several seeds: is the z = 7 an artefact of a vanishing standard error, or a bias?

Run: python3 s03b_lambda_detail.py
"""
import argparse
import math

import numpy as np

from lfphys.core.quantum import jumps as J, open_systems as OS

argparse.ArgumentParser(description=__doc__).parse_args()
e, g1, g2 = np.eye(3, dtype=complex)
O1, O2 = 1.1, 0.7
H = 0.5 * O1 * (np.outer(e, g1) + np.outer(g1, e)) + 0.5 * O2 * (np.outer(e, g2) + np.outer(g2, e))
c = [math.sqrt(0.6) * np.outer(g1, e), math.sqrt(0.9) * np.outer(g2, e)]
ts = np.linspace(0, 40, 9)
ex = OS.propagate(OS.liouvillian(H, c), np.outer(g1, g1), ts)
for seed in (101, 1, 2, 3):
    tr = J.trajectories(H, c, g1, ts, 4000, np.random.default_rng(seed), e_ops=[np.outer(e, e)])
    m, s = tr.mean(0), tr.stderr(0)
    print(f"seed {seed}")
    for k, t in enumerate(ts):
        z = abs(m[k] - ex[k, 0, 0].real) / s[k] if s[k] > 0 else 0.0
        print(f"  t={t:5.1f}: mean {m[k]:.3e}  exact {ex[k, 0, 0].real:.3e}  stderr {s[k]:.2e}  z {z:6.2f}  "
              f"max over trajectories {np.max(tr.expect[0][:, k]):.2e}")
