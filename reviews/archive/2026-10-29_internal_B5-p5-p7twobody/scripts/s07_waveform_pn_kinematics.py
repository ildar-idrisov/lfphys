"""P7 review, check 7: ``gw_quadrupole.binary_waveform`` fed with the PN acceleration and jerk (as its docstring
suggests, "e.g. pn_binary.acceleration and jerk") against the default Newtonian kinematics of the same (x, v), on the
engine's own 2PN circular orbits; and both against the 1PN-accurate (2,2) amplitude in terms of the gauge-invariant
x = (m Omega)^(2/3): for a face-on observer (i = 0) Blanchet 2014 Eqs. (322a, c), (323a, c) give
H+ = -2 cos 2psi + x cos 2psi (13/3 - nu/3), i.e. the amplitude factor 1 + x(-13/6 + nu/6) at 1PN.

Run: python3 s07_waveform_pn_kinematics.py
"""
import argparse
import math

import numpy as np

from lfphys.core.gravity import gw_quadrupole as W, pn_binary as P


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    nu = 0.25
    for r in (100.0, 30.0, 15.0, 10.0):
        vt = P.circular_speed(r, nu, (1, 2))
        x, v = np.array([r, 0, 0.0]), np.array([0, vt, 0.0])
        Om = vt / r
        xg = Om ** (2 / 3)
        # face-on observer: |h+| = |hx| = the (2,2) amplitude
        hN, _ = W.binary_waveform(x, v, nu, 0.0, 0.0)
        a = P.acceleration(x, v, nu, (1, 2))
        j = P.jerk(x, v, nu, (1, 2))
        hP, _ = W.binary_waveform(x, v, nu, 0.0, 0.0, a=a, j=j)
        ref0 = 4 * nu * xg  # Newtonian amplitude in terms of x: 2 mu x (1 + cos^2 i), i = 0
        ref1 = ref0 * (1 + xg * (-13 / 6 + nu / 6))
        print(f"r={r}: x={xg:.4f}; |h| default/(4 nu x) - 1 = {abs(hN) / ref0 - 1:+.3e}; with PN a, j: "
              f"{abs(hP) / ref0 - 1:+.3e}; 1PN amplitude (face-on): {ref1 / ref0 - 1:+.3e}")


if __name__ == "__main__":
    main()
