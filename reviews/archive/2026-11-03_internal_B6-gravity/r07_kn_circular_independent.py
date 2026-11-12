# Reviewer script (B6 gravity): Kerr-Newman equatorial circular orbits, photon orbits and ISCO by an independent
# route at 40 digits (mpmath): the metric written out here (Adamo & Newman 2014 below Eq. 2.19, M = 1), the geodesic
# condition for Omega solved directly, E(r) and L(r) from u_t, u_phi, the ISCO as the minimum of E(r) (dE/dr = 0 found
# by findroot on a high-precision derivative), the photon orbit as the zero of u^t's normalisation; compared with
# kerr_newman.circular_orbit / photon_orbit / isco. Also the closed equatorial photon-orbit equation
# r^2 - 3 r + 2 q^2 +- 2 a sqrt(r - q^2) = 0 (prograde plus) as a third route.
import math

import mpmath as mp

from lfphys.core.gravity import kerr_newman as KN

mp.mp.dps = 40


def metric_eq(r, a, q):
    m2 = 2 * r - q * q
    gtt = -(1 - m2 / r ** 2)
    gtp = -a * m2 / r ** 2
    gpp = r ** 2 + a ** 2 + a ** 2 * m2 / r ** 2
    return gtt, gtp, gpp


def dmetric(r, a, q):
    return [mp.diff(lambda rr: metric_eq(rr, a, q)[k], r) for k in range(3)]


def omega(r, a, q, pro):
    gtt, gtp, gpp = dmetric(r, a, q)
    disc = gtp ** 2 - gtt * gpp
    roots = [(-gtp + mp.sqrt(disc)) / gpp, (-gtp - mp.sqrt(disc)) / gpp]
    return max(roots) if pro else min(roots)


def norm(r, a, q, pro):
    gtt, gtp, gpp = metric_eq(r, a, q)
    om = omega(r, a, q, pro)
    return -(gtt + 2 * gtp * om + gpp * om ** 2)


def EL(r, a, q, pro):
    gtt, gtp, gpp = metric_eq(r, a, q)
    om = omega(r, a, q, pro)
    n = -(gtt + 2 * gtp * om + gpp * om ** 2)
    ut = 1 / mp.sqrt(n)
    return -(gtt + gtp * om) * ut, (gtp + gpp * om) * ut, om, n


worst = {"Omega": 0, "E": 0, "L": 0, "photon": 0, "photon_closed": 0, "isco": 0}
for a, q in ((0.9, 0.0), (0.0, 0.6), (0.5, 0.5), (0.3, 0.9), (0.95, 0.2), (0.7, 0.7), (0.998, 0.0), (0.1, 0.99)):
    if a * a + q * q >= 1:
        continue
    a_, q_ = mp.mpf(a), mp.mpf(q)
    for pro in (True, False):
        for r in (4.5, 7.0, 20.0):
            if norm(mp.mpf(r), a_, q_, pro) <= 0:
                continue
            E, L, om, n = EL(mp.mpf(r), a_, q_, pro)
            c = KN.circular_orbit(r, a, q, pro)
            worst["Omega"] = max(worst["Omega"], abs(float(c["Omega"]) - float(om)) / abs(float(om)))
            worst["E"] = max(worst["E"], abs(float(c["E"]) - float(E)) / abs(float(E)))
            worst["L"] = max(worst["L"], abs(float(c["L"]) - float(L)) / abs(float(L)))
        rp = 1 + mp.sqrt(1 - a_ ** 2 - q_ ** 2)
        # photon orbit: n(r) = 0 on the circular family, the outermost root
        f = lambda rr: norm(rr, a_, q_, pro)  # noqa: E731
        xs = [rp * (1 + mp.mpf("1e-10")) + k * (5 - rp) / 400 for k in range(401)]
        ys = [f(x) for x in xs]
        k = max(i for i in range(400) if ys[i] <= 0 < ys[i + 1])
        rph = mp.findroot(f, (xs[k], xs[k + 1]), solver="anderson")
        s = 1 if pro else -1  # Kerr limit: r^(3/2) - 3 r^(1/2) + 2 a = 0 prograde
        g = lambda rr: rr ** 2 - 3 * rr + 2 * q_ ** 2 + s * 2 * a_ * mp.sqrt(rr - q_ ** 2)  # noqa: E731
        rph2 = mp.findroot(g, rph)
        eng = KN.photon_orbit(a, q, pro)
        worst["photon"] = max(worst["photon"], abs(eng - float(rph)))
        worst["photon_closed"] = max(worst["photon_closed"], abs(float(rph2 - rph)))
        # ISCO: dE/dr = 0 outside the photon orbit, the outermost root
        dE = lambda rr: mp.diff(lambda z: EL(z, a_, q_, pro)[0], rr)  # noqa: E731
        xs = [rph * (1 + mp.mpf("1e-6")) * (20 / (rph * (1 + mp.mpf("1e-6")))) ** (k / 300) for k in range(301)]
        ys = [dE(x) for x in xs]
        k = max(i for i in range(300) if ys[i] < 0 <= ys[i + 1])
        risco = mp.findroot(dE, (xs[k], xs[k + 1]), solver="anderson")
        eng_i = KN.isco(a, q, pro)
        worst["isco"] = max(worst["isco"], abs(eng_i - float(risco)) / float(risco))
        print(f"a = {a}, q = {q}, {'pro ' if pro else 'retro'}: photon orbit engine {eng:.15f} vs 40-digit "
              f"{mp.nstr(rph, 17)} (closed equation {mp.nstr(rph2, 17)}); ISCO engine {eng_i:.14f} vs {mp.nstr(risco, 16)}")
print("worst relative differences (engine vs 40-digit route):", {k: f"{v:.2e}" for k, v in worst.items()})
