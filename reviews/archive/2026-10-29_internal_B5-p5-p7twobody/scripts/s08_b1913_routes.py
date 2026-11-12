"""P7 review, check 8: PSR B1913+16 through the PN equations of motion, both integration routes, and the size of the
post-Newtonian part of the decay measured from Newtonian osculating elements.

(a) Newton + 2.5PN: Pb_dot from the osculating a at successive periapses (elements route and Cartesian route) against
    Peters-Mathews (the docstring: the Cartesian route cannot resolve 1e-12 per orbit in double precision);
(b) all orders: the same estimator; the difference from Peters-Mathews is a mixture of the 1PN flux correction
    (x I1/I0 = 2.4e-6) and the mapping between the osculating Newtonian a and the PN radial period.

Run: python3 s08_b1913_routes.py
"""
import argparse
import math

import numpy as np

from lfphys.core import data as D
from lfphys.core.constants import C
from lfphys.core.gravity import pn_binary as P
from lfphys.theories.approx import peters_mathews as PM


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    PB = D.PSR_B1913_PB_DAYS[0] * 86400.0
    ECC = D.PSR_B1913_ECC[0]
    om = math.radians(D.PSR_B1913_PERIASTRON_DEG_PER_YR[0]) / (365.25 * 86400.0)
    g1, g2 = PM.masses_from_pk(om, D.PSR_B1913_GAMMA_S[0], PB, ECC)
    M = g1 + g2
    nu = g1 * g2 / M**2
    a = PM.semi_major_axis(M, PB) / P.mass_units(M)["length"]
    ref = PM.pb_dot(g1, g2, PB, ECC)
    print(f"a = {a:.1f} G M/c^2, Peters-Mathews Pb_dot = {ref:.6e}")
    for orders in ((2.5,), (1, 2, 2.5, 3.5)):
        for method in ("elements", "cartesian"):
            out = P.integrate(P.periapsis_state(a, ECC), 5.3 * 2 * math.pi * a**1.5, nu, orders=orders,
                              method=method, n_out=3)
            if method == "elements":
                els = out["elements"]
                da = np.array([el["da"] for el in els])
                a0 = els[0]["a0"]
            else:
                A = np.array([P.newtonian_elements(*out["at"](t))["a"] for t in out["t_peri"]])
                da, a0 = A - A[0], A[0]
            slope = np.polyfit(np.arange(len(da)), da, 1)[0]
            pbd = 1.5 * slope / a0
            print(f"  orders {orders}, {method}: Pb_dot / PM - 1 = {pbd / ref - 1:+.2e} over {len(da)} periapses")


if __name__ == "__main__":
    main()
