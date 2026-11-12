"""P7 review, check 11: the residual of tests/test_peters_mathews.py::test_psr_b1913_averaged_reaction_at_1pn
(ratio - 1 - x I1/I0, stated there as "O(x^2) ~ 1e-11") with the 1PN maps x(eps, j), e_t(eps, j) used by the test and
with their 2PN forms (Blanchet 2014 Eq. (350) to eps^2 and Eq. (351) to eps^2, read from arXiv:1310.1528v3):

  x/eps = 1 + eps(-5/4 + nu/12 + 2/j) + eps^2 [5/2 + 5 nu/24 + nu^2/18 + (-5 + 2 nu)/j^(1/2)
          + (1/j)(-5 + 7 nu/6 + (1/j)(33/2 - 5 nu))],
  e_t^2 = 1 - j + (eps/4)(-8 + 8 nu + j(17 - 7 nu)) + (eps^2/8)[12 + 72 nu + 20 nu^2 + j(-112 + 47 nu - 16 nu^2)
          + 24 j^(1/2)(5 - 2 nu) + (16/j)(4 - 7 nu) + (24/j^(1/2))(-5 + 2 nu)].

Run: python3 s11_b1913_1pn_flux_residual.py
"""
import argparse
import math

from lfphys.core import data as D
from lfphys.core.constants import C
from lfphys.core.gravity import pn_binary as P
from lfphys.theories.approx import peters_mathews as PM

argparse.ArgumentParser(description=__doc__).parse_args()
PB = D.PSR_B1913_PB_DAYS[0] * 86400.0
ECC = D.PSR_B1913_ECC[0]
om = math.radians(D.PSR_B1913_PERIASTRON_DEG_PER_YR[0]) / (365.25 * 86400.0)
g1, g2 = PM.masses_from_pk(om, D.PSR_B1913_GAMMA_S[0], PB, ECC)
M = g1 + g2
nu = g1 * g2 / M**2
a = PM.semi_major_axis(M, PB) / P.mass_units(M)["length"]
st = P.periapsis_state(a, ECC)
res = P.averaged_dissipation(st, nu, conservative=(1, 2), dissipative=(2.5, 3.5), order=2, rtol=1e-13)
gi = P.gauge_invariants(st["x"], st["v"], nu)
eps, j = gi["eps"], gi["j"]


def I0I1(et):
    e2 = et * et
    I0 = (1 + 73 / 24 * e2 + 37 / 96 * e2**2) / (1 - e2) ** 3.5
    I1 = (-1247 / 336 - 35 / 12 * nu + e2 * (10475 / 672 - 1081 / 36 * nu) + e2**2 * (10043 / 384 - 311 / 12 * nu)
          + e2**3 * (2179 / 1792 - 851 / 576 * nu)) / (1 - e2) ** 4.5
    return I0, I1


x1 = P.x_parameter(eps, j, nu)
et1 = P.time_eccentricity(eps, j, nu)
x2 = eps * (1 + eps * (-1.25 + nu / 12 + 2 / j) + eps**2 * (2.5 + 5 * nu / 24 + nu**2 / 18 + (-5 + 2 * nu) / math.sqrt(j)
                                                           + (1 / j) * (-5 + 7 * nu / 6 + (1 / j) * (16.5 - 5 * nu))))
et2 = math.sqrt(1 - j + eps / 4 * (-8 + 8 * nu + j * (17 - 7 * nu))
                + eps**2 / 8 * (12 + 72 * nu + 20 * nu**2 + j * (-112 + 47 * nu - 16 * nu**2)
                                + 24 * math.sqrt(j) * (5 - 2 * nu) + 16 / j * (4 - 7 * nu) + 24 / math.sqrt(j) * (-5 + 2 * nu)))
for label, x, et in (("1PN maps (as the test)", x1, et1), ("2PN maps", x2, et2)):
    I0, I1 = I0I1(et)
    ratio = res["dE"] / (-6.4 * nu * x**5 * I0)
    print(f"{label}: x = {x:.6e}, e_t = {et:.10f}, ratio - 1 - x I1/I0 = {ratio - 1 - x * I1 / I0:+.2e}, x^2 = {x * x:.1e}")
