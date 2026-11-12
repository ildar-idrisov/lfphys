"""01: the next-order coefficient (18 + e^2)/4 of the periapsis advance, and the tolerance of the 'ppn' check.

Independent route (not the project's elliptic-integral code): with u = (1 + e cos chi)/p (p, e from the turning
points r_pm = p/(1 -+ e), as in lfphys.core.gravity.orbits.elements), the Schwarzschild orbit equation gives exactly
    dphi/dchi = 1 / sqrt(1 - 2 mu (3 + e cos chi)),   mu = M/p
(derivation: with u1,2 = (1 -+ e)/p and u3 = 1/2 - u1 - u2 = 1/2 - 2/p, f(u) = 2(u - u1)(u - u2)(u - u3) and
(du/dphi)^2 = (e/p)^2 sin^2 chi (dchi/dphi)^2 give (dchi/dphi)^2 = 2 (u3 - u) = 1 - (2/p)(3 + e cos chi)), so the advance per radial period is Delta = int_0^{2 pi} dchi / sqrt(1 - 2 mu (3 + e cos chi)) - 2 pi.
Series: Delta = 6 pi mu [1 + (18 + e^2)/4 mu + (5/12)(54 + 9 e^2) mu^2 + ...] (binomial series of the integrand).
Here: the integral with mpmath at 50 digits, the coefficient extracted, compared with the project's claim, and
with the project's float route orbits.advance_from_turning.
"""
import math
import sys

import mpmath as mp

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.gravity import orbits  # noqa: E402

mp.mp.dps = 50


def exact_adv(mu, e):
    mu, e = mp.mpf(mu), mp.mpf(e)
    f = lambda c: 1 / mp.sqrt(1 - 2 * mu * (3 + e * mp.cos(c)))
    return mp.quad(f, [0, mp.pi, 2 * mp.pi]) - 2 * mp.pi


print("relative correction to 6 pi M/p, times p/M  ->  (18 + e^2)/4 as p -> inf")
print(f"{'e':>5} {'p/M':>10} {'(Delta/(6pi/p)-1)*p':>24} {'(18+e^2)/4':>12} {'next: ((rel - c1 mu)/mu^2)':>28} {'(5/12)(54+9e^2)':>16}")
worst = 0.0
for e in (0.0, 0.2, 0.6, 0.9, 0.99):
    c1 = (18 + e * e) / 4
    c2 = mp.mpf(5) / 12 * (54 + 9 * e * e)
    for p in (1e3, 1e5, 1e7):
        mu = mp.mpf(1) / p
        d = exact_adv(mu, e)
        rel = d / (6 * mp.pi * mu) - 1
        nxt = (rel - c1 * mu) / mu**2
        print(f"{e:5.2f} {p:10.0e} {mp.nstr(rel / mu, 15):>24} {c1:12.6f} {mp.nstr(nxt, 10):>28} {mp.nstr(c2, 10):>16}")

# the project's float route (orbits.advance_from_turning) vs the mp integral
print("\nproject float route orbits.advance_from_turning vs the 50-digit integral (relative error)")
for e in (0.05, 0.2056, 0.6, 0.9):
    for p in (10.0, 30.0, 1e3, 1e5, 3.0e7):
        if p < 6 + 2 * e + 1e-9:
            continue
        rp, ra = p / (1 + e), p / (1 - e)
        try:
            fl = orbits.advance_from_turning(1 / ra, 1 / rp)
        except ValueError as ex:
            print(f"  e={e} p={p}: {ex}")
            continue
        ex_ = exact_adv(1 / mp.mpf(p), e)
        print(f"  e={e:6.4f} p={p:9.3g}: float {fl:.15e}  exact {mp.nstr(ex_, 16)}  rel {float((fl - ex_) / ex_):+.2e}")

# the tolerance of the 'ppn' row: 1.5 * c1 * mu + tol_adv, for mu <= 0.02 (the row is a verdict only there)
print("\n'ppn' row: actual relative deviation of the exact advance from 6 pi M/p vs the tolerance 1.5 (18+e^2)/4 M/p")
for e in (0.0, 0.5, 0.9, 0.99):
    for p in (50.0, 100.0, 1e3):
        mu = 1 / p
        rel = float(exact_adv(mu, e) / (6 * mp.pi * mu) - 1)
        tol = 1.5 * (18 + e * e) / 4 * mu
        print(f"  e={e:4.2f} p={p:6.0f} M/p={mu:.3g}: rel {rel:.4e}  tol {tol:.4e}  margin {tol / rel:.3f}")
