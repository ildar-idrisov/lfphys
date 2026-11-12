"""P7 review, check 14: the 2.5PN radiation-reaction term of the general-frame harmonic equations of motion
(Blanchet 2014 Eq. (203), the 1/c^5 line, read from arXiv:1310.1528v3):

  a1 = n12 [208 G^3 m1 m2^2/(15 r^4) (n12.v12) - 24 G^3 m1^2 m2/(5 r^4) (n12.v12) + 12 G^2 m1 m2/(5 r^3) (n12.v12) v12^2]
     + v12 [8 G^3 m1^2 m2/(5 r^4) - 32 G^3 m1 m2^2/(5 r^4) - 4 G^2 m1 m2/(5 r^3) v12^2],   a2 = (1 <-> 2),

reduced to the relative acceleration a1 - a2 (at 2.5PN the centre-of-mass relations add nothing), against
pn_binary.perturbation(x, v, nu, (2.5,)) (the engine's B14 Eq. (220) / B24 Eqs. (358c), (359c) term).

Run: python3 s14_general_frame_2p5pn.py
"""
import argparse
import math

import numpy as np

from lfphys.core.gravity import pn_binary as P

argparse.ArgumentParser(description=__doc__).parse_args()


def a_body(mA, mB, n, v, r):
    rd = float(n @ v)
    v2 = float(v @ v)
    return (n * (208 / 15 * mA * mB**2 / r**4 * rd - 24 / 5 * mA**2 * mB / r**4 * rd + 12 / 5 * mA * mB / r**3 * rd * v2)
            + v * (8 / 5 * mA**2 * mB / r**4 - 32 / 5 * mA * mB**2 / r**4 - 4 / 5 * mA * mB / r**3 * v2))


rng = np.random.default_rng(5)
worst = 0.0
for _ in range(200):
    m1 = rng.uniform(0.05, 0.95)
    m2 = 1 - m1
    r = rng.uniform(5, 200)
    x = r * np.array([1.0, 0, 0])
    v = math.sqrt(1 / r) * rng.uniform(0.2, 1.5) * np.array([rng.normal(), rng.normal(), 0])
    n = x / r
    rel = a_body(m1, m2, n, v, r) - a_body(m2, m1, -n, -v, r)
    eng = P.perturbation(x, v, m1 * m2, (2.5,))
    worst = max(worst, float(np.max(np.abs(rel - eng)) / np.max(np.abs(eng))))
print(f"max relative difference over 200 random states: {worst:.1e}")
