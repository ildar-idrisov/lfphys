# Reviewer script (B6 gravity): the terms of the tolerance in test_kerr_newman.test_kerr_generic_orbit_against_the_closed_form:
# the x2 term, the 1e-12 terms, and "e_cf_t * drdt" where drdt is |dr/dlambda| (Mino time), not |dr/dt| - a factor
# dt/dlambda = T ~ r^2 too large - and is also used for theta and phi. Which term carries each assertion, and the
# measured errors.
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys/tests")
from lfphys.core.gravity import kerr_newman as KNW, kerr_orbits as KO  # noqa: E402

chi, p, e, x = 0.9, 6.0, 0.7, math.cos(math.radians(20))
o = KO.KerrOrbit(chi, p, e, x)
r0, th0 = float(o.r(0.0)), float(o.theta(0.0))


def make(rtol):
    g = KNW.Geodesics(chi, 0.0, rtol=rtol)
    g.add_state(r0, th0, 0.0, [-o.E, 0.0, 0.0, o.L], 1.0)
    return g


g, gc = make(1e-10), make(1e-12)
lams = np.array([0.5, 2.0, 7.0, 15.0])
t, r, th, ph = o.trajectory(lams)
o2 = KO.KerrOrbit(chi, p, e, x)
t2, ph2 = np.empty(4), np.empty(4)
lt, tt, pp = 0.0, 0.0, 0.0
for i, lam in enumerate(lams):
    dt_, dp_ = o2._integrate(lt, lam, nodes=48)
    tt, pp, lt = tt + dt_, pp + dp_, lam
    t2[i], ph2[i] = tt, pp
for i, ti in enumerate(t):
    g.advance(ti)
    gc.advance(ti)
    y, yc = g.bl()[0], gc.bl()[0]
    drdl = abs(r[i] - float(o.r(lams[i] + 1e-4))) / 1e-4 * 2
    # the actual |dr/dt| bound: dr/dlambda / (dt/dlambda), dt/dlambda from the Mino-time rhs
    from lfphys.core.gravity.kerr_newman import rhs_mino
    yy = g._y[:1].copy()
    d, T = rhs_mino(yy, g._c[:1, 0], g._c[:1, 1], g._c[:1, 2], chi, 0.0)
    e_cf_t = 2 * abs(ti - t2[i])
    print(f"lambda = {lams[i]:5.1f}, t = {ti:9.3f}: |err r| = {abs(y[0] - r[i]):.2e}; x2 term {2 * abs(y[0] - yc[0]):.2e}; "
          f"1e-12 r {1e-12 * r[i]:.2e}; e_cf_t {e_cf_t:.2e} x |dr/dlambda| {drdl:.2e} = {e_cf_t * drdl:.2e} "
          f"(with |dr/dt| = {drdl / T[0]:.2e}: {e_cf_t * drdl / T[0]:.2e}; dt/dlambda = {T[0]:.1f})")
    print(f"      theta: |err| = {abs(y[1] - th[i]):.2e}; x2 term {2 * abs(y[1] - yc[1]):.2e}; loose term {e_cf_t * drdl:.2e}"
          f"   phi: |err| = {abs(y[2] - ph[i]):.2e}; x2 {2 * abs(y[2] - yc[2]):.2e}; quadrature {2 * abs(ph[i] - ph2[i]):.2e}")
