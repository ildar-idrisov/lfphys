# Review B5, check c01b: F(phi|m) near phi = pi/2 with m -> 1 (the phases of near-critical rays, k -> 1): the
# engine's ellipf against mpmath (40 digits) at the same binary64 inputs; the relative error and the stated bound
# (test_elliptic: 64 u |F| + 4 u |phi| max(1, 1/sqrt(1 - m))). The cause: y = 1 - m sin^2 phi is formed with
# cancellation (DLMF 19.25.5 writes R_F(cos^2, 1 - k^2 sin^2, 1); cos^2 phi + (1 - m) sin^2 phi has none).
# Root and run as c02 (see its header); run it also against a patched copy to see the one-line fix.
import math

import mpmath as mp
import numpy as np

from lfphys.core import elliptic as EL

mp.mp.dps = 40
U = 2.0 ** -53
for m, dphi in ((1 - 1e-6, 1e-4), (1 - 1e-9, 1e-6), (1 - 1e-12, 1e-6), (1 - 1e-13, 1e-7), (1 - 1e-13, 3e-9)):
    phi = math.pi / 2 - dphi
    F = float(EL.ellipf(phi, m))
    ref = mp.ellipf(mp.mpf(phi), mp.mpf(m))
    bound = 64 * U * abs(float(ref)) + 4 * U * phi * max(1.0, 1 / math.sqrt(1 - m))
    print(f"m = 1 - {1 - m:.0e}, phi = pi/2 - {dphi:.0e}: F = {F:.17g}, rel error {abs(F - float(ref)) / float(ref):.2e}, "
          f"error / stated bound {abs(F - float(ref)) / bound:.3g}")
