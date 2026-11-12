# Review B5, check c11: the Keplerian emitter against two more routes. (a) Omega of circular equatorial geodesics
# from the metric alone: Omega = (-g_tphi,r +- sqrt(g_tphi,r^2 - g_tt,r g_phiphi,r)) / g_phiphi,r (derivatives by
# complex step), against the engine's +-1/(r^1.5 +- a) (Bardeen, Press & Teukolsky 1972); (b) the redshift of
# Keplerian gas, Gralla, Lupsasca & Marrone 2020 App. B Eq. (B7): g = sqrt(r^3 - 3 r^2 + 2 a r^1.5)/(r^1.5 + a - lambda)
# (prograde, M = 1), against kerr_shadow.redshift. Root and run as c02 (see its header).
import math

import numpy as np

from lfphys.core.gravity import kerr, kerr_shadow as KS


def g_eq(r, a):
    s2 = 1.0
    sig = r * r
    return (-(1 - 2 * r / sig), -2 * a * r * s2 / sig, (r * r + a * a + 2 * a * a * r * s2 / sig) * s2)


worst_om, worst_g = 0.0, 0.0
for a in (0.0, 0.3, 0.9, 0.998):
    for s in (1.0, -1.0):
        for r in np.linspace(kerr.isco(a, s > 0), 40.0, 25):
            h = 1e-20
            gtt, gtp, gpp = (np.imag(v) / h for v in g_eq(complex(r, h), a))
            om = (-gtp + s * math.sqrt(gtp * gtp - gtt * gpp)) / gpp
            om_e = s / (r ** 1.5 + s * a)
            worst_om = max(worst_om, abs(om - om_e) / abs(om_e))
    for r in np.linspace(kerr.isco(a, True), 30.0, 15):
        for lam in np.linspace(-6, 4, 11):
            g_glm = math.sqrt(r ** 3 - 3 * r * r + 2 * a * r ** 1.5) / (r ** 1.5 + a - lam)
            g_e = float(KS.redshift(np.array([r]), lam, 20.0, 1.0, a, "keplerian", True)[0])
            worst_g = max(worst_g, abs(g_glm - g_e) / g_glm)
print(f"(a) max rel |Omega(metric) - Omega(engine)| = {worst_om:.2e}")
print(f"(b) max rel |g(GLM B7) - g(engine, keplerian)| = {worst_g:.2e}")
