# Review B8-mie, script s03: the Debye series (lfphys.core.optics.mie_debye).
# (1) The closed-form sum against the Mie coefficients for m < 1 and m > 1, including cases outside the tests
#     (m near 1, m = 0.5, large real m, strong absorption beyond the stated Im(m) x <~ 700, x = 2e4).
# (2) The individual terms, beyond the sum identity: by the localization principle (Hovenac & Lock, NASA CR-187191,
#     1991, the report version of JOSA A 9, 781 (1992): "When x >> 1, these fractions are approximated by the Fresnel
#     coefficients for oblique incidence on a flat interface"), |R22_n| -> |r_Fresnel(i)| with sin i = (n + 1/2)/x,
#     TE (b_n) <-> s, TM (a_n) <-> p; |R11_n| -> the same modulus (internal reflection, Stokes r' = -r); and
#     T21 T12 -> 1 - r^2 in modulus. A wrong assignment of beta (TE/TM swapped) would show here, not in the sum.
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie, mie_debye as dbe  # noqa: E402

print("(1) Debye sum (1 - R22 - T21T12/(1 - R11))/2 and partial sums p <= 4 + remainder, against mie.coefficients")
for m, x in [(1.333, 1000.0), (1.001, 500.0), (0.5, 1000.0), (0.75, 2e4), (1.333, 2e4), (3.0, 500.0), (10.0, 100.0),
             (1.5 + 0.5j, 1000.0), (1.5 + 1.0j, 1000.0), (1.5 + 0.1j, 1e4), (1.0 + 1e-6j, 100.0)]:
    t0 = time.time()
    try:
        c = dbe.coefficients(m, x, p_max=4)
    except Exception as e:  # noqa: BLE001
        print(f"  m = {m}, x = {x:g}: raised {type(e).__name__}: {e}")
        continue
    a, b = mie.coefficients(m, x, n_max=c["N"])
    s = max(np.abs(a).max(), np.abs(b).max())
    e1 = max(np.abs(c["sum_a"] - a).max(), np.abs(c["sum_b"] - b).max()) / s
    e2 = max(np.abs(c["a"].sum(0) + c["remainder_a"] - a).max(), np.abs(c["b"].sum(0) + c["remainder_b"] - b).max()) / s
    fin = all(np.all(np.isfinite(c[k])) for k in ("a", "b", "sum_a", "sum_b", "remainder_a", "remainder_b"))
    print(f"  m = {m}, x = {x:g}, Im(m)x = {complex(m).imag * x:g}: sum err {e1:.1e}, partial+rem err {e2:.1e}, "
          f"underflow {c['underflow']}, finite {fin}, {time.time() - t0:.1f} s")

print("\n(2) Individual terms against Fresnel by localization, m = 1.333, x = 2000 (orders n = (x - 1/2) sin i)")


def fresnel(m, i):
    r = math.asin(math.sin(i) / m)
    rs = -math.sin(i - r) / math.sin(i + r)
    rp = math.tan(i - r) / math.tan(i + r)
    return rs, rp


m, x = 1.333, 2000.0
it = dbe.interface_terms(m, x)
for deg in (10, 30, 50, 60, 70, 80):
    i = math.radians(deg)
    n = int(round(x * math.sin(i) - 0.5))
    ii = math.asin((n + 0.5) / x)
    rs, rp = fresnel(m, ii)
    R22b, R22a = abs(it["b"]["R22"][n - 1]), abs(it["a"]["R22"][n - 1])
    R11b, R11a = abs(it["b"]["R11"][n - 1]), abs(it["a"]["R11"][n - 1])
    TTb, TTa = abs(it["b"]["TT"][n - 1]), abs(it["a"]["TT"][n - 1])
    print(f"  i = {math.degrees(ii):6.2f} deg, n = {n}: |R22| TE {R22b:.5f} vs |rs| {abs(rs):.5f}; TM {R22a:.5f} vs "
          f"|rp| {abs(rp):.5f}; |R11| TE {R11b:.5f} TM {R11a:.5f}; |T21T12| TE {TTb:.5f} vs 1-rs^2 {1 - rs * rs:.5f}, "
          f"TM {TTa:.5f} vs 1-rp^2 {1 - rp * rp:.5f}")
print("  (Brewster: tan i_B = m -> i_B = %.2f deg, where |rp| = 0)" % math.degrees(math.atan(m)))
