"""10: theories.models.cornell spin-averaged levels: an independent shooting solution of the radial equation
(DOP853, rtol 1e-11, eigenvalue by node counting + brentq, outer boundary at the turning point + 12 decay lengths) vs
the engine's sine-DVR, and the model-vs-PDG splittings quoted in the module ("2S-1S: 591 vs 605 MeV", "2-10 %").
Usage: python3 10_cornell.py
"""
import argparse
import math

argparse.ArgumentParser(description=__doc__).parse_args()

import numpy as np
from scipy import integrate, optimize

from lfphys.core import data
from lfphys.theories.models import cornell

KAP, A = cornell.PARAMS["kappa"], cornell.PARAMS["a"]


def shoot(E, l, mu, rmax):
    def rhs(r, y):
        V = -KAP / r + r / A**2
        return [y[1], (2 * mu * (V - E) + l * (l + 1) / r**2) * y[0]]
    r0 = 1e-6
    y0 = [r0 ** (l + 1) * (1 - mu * KAP * r0 / (l + 1)), (l + 1) * r0**l * (1 - mu * KAP * r0 * (l + 2) / ((l + 1) ** 2))]
    sol = integrate.solve_ivp(rhs, (r0, rmax), y0, method="DOP853", rtol=1e-11, atol=1e-30, dense_output=True)
    rr = np.linspace(r0, rmax, 4001)
    u = sol.sol(rr)[0]
    nodes = int(np.sum(np.sign(u[1:-1]) != np.sign(u[2:])))
    return sol.y[0, -1], nodes


def level(n, l, mu):
    # bracket by node count, then brentq on u(rmax)
    lo, hi = -2.0, 4.0
    rmax = 18.0  # V(18) - E > 1.5 GeV for all levels used: decay length << 1 GeV^-1 there
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        _, k = shoot(mid, l, mu, rmax)
        if k >= n + 1:  # the n-node eigenvalue is where the count jumps from n to n + 1
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-4:
            break
    f = lambda E: shoot(E, l, mu, rmax)[0]  # noqa: E731
    a, b = lo - 2e-4, hi + 2e-4
    while f(a) * f(b) > 0:
        a -= 1e-3
        b += 1e-3
    return optimize.brentq(f, a, b, xtol=1e-12)


for name, mq, table in (("charmonium", cornell.PARAMS["m_c"], data.CHARMONIUM),
                        ("bottomonium", cornell.PARAMS["m_b"], data.BOTTOMONIUM)):
    mu = 0.5 * mq
    ref = {(n, l): 2 * mq + level(n - 1, l, mu) for (n, l) in ((1, 0), (2, 0), (3, 0), (1, 1))}
    eng = cornell.spectrum(mq, n_max=3, L_max=1)
    eng_fine = cornell.spectrum(mq, n_max=3, L_max=1, N=2000)
    print(f"--- {name} (m_q = {mq}) ---")
    for k in ref:
        print(f"  (n,L)={k}: shooting {ref[k]:.6f} GeV, engine N=700 {eng[k]:.6f} (diff {1e3 * (eng[k] - ref[k]):+.3f} MeV),"
              f" N=2000 {eng_fine[k]:.6f}")
    m1s = data.spin_averaged(table, 0, 1)[0]
    for (n, L) in ((2, 0), (1, 1), (3, 0)):
        m = data.spin_averaged(table, L, n)
        if m[0] is None:
            continue
        model = 1e3 * (ref[(n, L)] - ref[(1, 0)])
        print(f"  splitting {n}{'SP'[L]}-1S: model {model:.1f} MeV, PDG spin-averaged {m[0] - m1s:.1f} MeV "
              f"({model / (m[0] - m1s) - 1:+.1%}); states {m[1]}")
    print(f"  absolute: 2 m_q + E(1S) = {ref[(1, 0)]:.4f} GeV vs spin-averaged 1S {m1s / 1e3:.4f} GeV")
