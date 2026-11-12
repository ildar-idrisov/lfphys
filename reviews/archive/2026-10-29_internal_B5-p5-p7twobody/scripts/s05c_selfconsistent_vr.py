"""P7 review, check 5c: a self-consistent quasi-circular radial velocity from the engine's own equations,
vr = (dE/dt)_RR / (dE_circ/dr): the rate of the 2PN energy under the 2.5 + 3.5PN reaction at the circular state
(complex-step derivatives, as in averaged_dissipation) divided by the slope of the 2PN energy along the 2PN circular
sequence (central difference). Compare k = vr / vr_227a with the minimising k of s05b.

Run: python3 s05c_selfconsistent_vr.py
"""
import argparse

import numpy as np

from lfphys.core.gravity import pn_binary as P

argparse.ArgumentParser(description=__doc__).parse_args()
nu = 0.25
zero = np.zeros(3)
for r0 in (40.0, 20.0, 12.0, 10.0):
    vt = P.circular_speed(r0, nu)
    x, v = np.array([r0, 0, 0.0]), np.array([0, vt, 0.0])
    ad = P.perturbation(x, v, nu, (2.5, 3.5))
    dE = P.directional(lambda X, V: P.energy(X, V, nu, 2), x, v, zero, ad)

    def Ec(r):
        return float(P.energy([r, 0, 0], [0, P.circular_speed(r, nu), 0], nu, 2))
    h = 1e-4 * r0
    dEdr = (Ec(r0 + h) - Ec(r0 - h)) / (2 * h)
    vr = float(dE) / dEdr
    print(f"r0={r0}: self-consistent k = {vr / P.circular_inspiral_rate(r0, nu):.3f}")
