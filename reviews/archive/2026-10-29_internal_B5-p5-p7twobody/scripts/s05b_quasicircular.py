"""P7 review, check 5b: quasi-circular initial data of ``pn_binary.circular_state(quasi=True)``.

The radial velocity added is Blanchet 2014 Eq. (227a) (re-expanded, 1PN-corrected); the conservative tangential
speed is the 2PN circular speed. Scan the initial radial velocity vr = k * vr_227a (k from 0 to 2) and the tangential
speed, and measure the residual radial oscillation (r(t) minus a smooth fit of the secular inspiral, over 3 orbits);
the k that minimises it is the radial velocity of the inspiral that the equations of motion actually produce.

Run: python3 s05b_quasicircular.py
"""
import argparse
import math

import numpy as np

from lfphys.core.gravity import pn_binary as P


def osc_amp(r0, nu, vr, vt):
    st = P.state(0.0, [r0, 0, 0], [vr, vt, 0])
    T = 3 * 2 * math.pi * r0**1.5
    out = P.integrate(st, T, nu, n_out=6000, rtol=1e-12)
    r = np.linalg.norm(out["x"], axis=1)
    t = out["t"] / T
    c = np.polyfit(t, r, 5)  # the secular inspiral over 3 orbits is smooth: a quintic removes it far below 1e-6 r0
    return np.ptp(r - np.polyval(c, t)) / (2 * r0)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    nu = 0.25
    for r0 in (40.0, 20.0, 12.0, 10.0):
        vt = P.circular_speed(r0, nu)
        vr0 = P.circular_inspiral_rate(r0, nu)
        ks = np.linspace(0.0, 2.0, 21)
        amps = [osc_amp(r0, nu, k * vr0, vt) for k in ks]
        kbest = ks[int(np.argmin(amps))]
        # refine
        ks2 = np.linspace(max(kbest - 0.1, 0), kbest + 0.1, 21)
        amps2 = [osc_amp(r0, nu, k * vr0, vt) for k in ks2]
        kb = ks2[int(np.argmin(amps2))]
        print(f"r0={r0}: residual eccentricity with vr=0: {amps[0]:.2e}; with Eq.(227a) (k=1): {amps[10]:.2e}; "
              f"minimum {min(amps2):.2e} at k = {kb:.3f} (vr_227a = {vr0:.3e}, leading-order only would be "
              f"k = {-12.8 * nu / r0**3 / vr0:.3f})")


if __name__ == "__main__":
    main()
