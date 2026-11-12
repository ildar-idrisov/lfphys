"""P7 review, check 13: ``pn_binary.periapsis_state(a, e)`` (Newtonian osculating elements) as initial data of the PN
motion: the gauge-invariant eps, j of the state, its PN time eccentricity, and the smallest a at which the state is
still bound (E_2PN < 0), for nu = 0.25.

Run: python3 s13_periapsis_state_binding.py
"""
import argparse
import math

from scipy import optimize

from lfphys.core.gravity import pn_binary as P

argparse.ArgumentParser(description=__doc__).parse_args()
nu = 0.25
for e in (0.3, 0.5, 0.7, 0.9):
    def E(a):
        st = P.periapsis_state(a, e)
        return float(P.energy(st["x"], st["v"], nu, 2))
    a_b = optimize.brentq(E, 3.0 / (1 - e), 1e5)
    line = [f"e={e}: bound only for a > {a_b:.1f} (r_p > {a_b * (1 - e):.1f})"]
    for a in (2 * a_b, 5 * a_b, 50 * a_b):
        st = P.periapsis_state(a, e)
        gi = P.gauge_invariants(st["x"], st["v"], nu)
        et = P.time_eccentricity(gi["eps"], gi["j"], nu)
        line.append(f"a={a:.0f}: 2 a eps = {2 * a * gi['eps']:.3f}, e_t = {et:.3f}")
    print("; ".join(line))
