"""P7 review, check 9: the margins of two convergence tests of tests/test_pn_binary.py.

(a) test_periastron_advance_and_mean_motion_are_gauge_invariant_closed_forms: D = residual / eps^3 at eps = 4e-3,
    2e-3, 1e-3 and the acceptance |d2| <= 0.75 |d1| + 0.05 (the absolute slack 0.05 against the size of D);
(b) the same with a deliberately wrong 2PN coefficient of K (15/j^2 (7 - 2 nu) -> (7 - nu)) and of n (555 -> 556):
    how large D and its differences become (the residual of a 2PN error grows like 1/eps).

Run: python3 s09_test_margins.py
"""
import argparse
import math

from lfphys.core.gravity import pn_binary as P

argparse.ArgumentParser(description=__doc__).parse_args()


def K_bad(eps, j, nu):
    return 1.0 + 3.0 * eps / j + eps * eps / 4.0 * (3.0 / j * (-5.0 + 2.0 * nu) + 15.0 / (j * j) * (7.0 - nu))


def n_bad(eps, j, nu):
    c2 = 556.0 + 30.0 * nu + 11.0 * nu * nu + 192.0 / math.sqrt(j) * (-5.0 + 2.0 * nu)
    return eps**1.5 * (1.0 + eps / 8.0 * (-15.0 + nu) + eps * eps / 128.0 * c2)


for nu in (0.25, 0.1):
    for j in (0.95, 0.75, 0.5):
        rows = {"K": [], "n": [], "K_bad": [], "n_bad": []}
        for eps in (4e-3, 2e-3, 1e-3):
            st = P.state_from_invariants(eps, j, nu)
            res = P.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=())
            K, n = res["Phi"] / (2 * math.pi), 2 * math.pi / res["P_r"]
            rows["K"].append((K - P.periastron_K(eps, j, nu)) / eps**3)
            rows["n"].append((n / P.mean_motion(eps, j, nu) - 1) / eps**3)
            rows["K_bad"].append((K - K_bad(eps, j, nu)) / eps**3)
            rows["n_bad"].append((n / n_bad(eps, j, nu) - 1) / eps**3)
        out = []
        for k, D in rows.items():
            d1, d2 = D[1] - D[0], D[2] - D[1]
            ok = abs(d2) <= 0.75 * abs(d1) + 0.05
            out.append(f"{k}: D = [{D[0]:+.3f}, {D[1]:+.3f}, {D[2]:+.3f}] {'pass' if ok else 'FAIL'}")
        print(f"nu={nu} j={j}: " + "; ".join(out))
