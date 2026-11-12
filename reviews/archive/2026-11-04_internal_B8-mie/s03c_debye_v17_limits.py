# Review B8-mie, script s03c: (a) the v17 "debye" check (tolerance 5e-10 of the largest coefficient) at the largest
# drops v17 admits (x <= 2e4 at 380 nm; the display wavelength is live, 380-760 nm); (b) |R11|, |R22| and the size of
# the individual Debye terms p = 1..3 for m near 1 (custom index n = 1, small kappa), where the partial waves above x
# tunnel and the Debye terms need not be small.
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie, mie_debye as dbe  # noqa: E402

print("(a) v17's debye check: the closed-form sum against mie.coefficients, tol 5e-10")
for m, x in [(0.75, 16535.0), (0.75, 19000.0), (1.335401, 16535.0), (1.335401, 19900.0), (2.0, 19900.0), (1.6 + 0.05j, 19900.0)]:
    c = dbe.coefficients(m, x, p_max=3)
    a, b = mie.coefficients(m, x, n_max=c["N"])
    s = max(np.abs(a).max(), np.abs(b).max())
    e = max(np.abs(c["sum_a"] - a).max(), np.abs(c["sum_b"] - b).max()) / s
    print(f"  m = {m}, x = {x:g}: err {e:.2e}  -> v17 check {'PASS' if e <= 5e-10 else 'FAIL'}")

print("(b) m near 1: the interface terms and the Debye terms p = 1..3 (largest over n, in units of the largest Mie coefficient)")
for m, x in [(1.0 + 1e-6j, 100.0), (1.0001, 100.0), (1.001, 100.0), (1.01, 100.0), (1.0 + 0.01j, 100.0)]:
    it = dbe.interface_terms(m, x)
    c = dbe.coefficients(m, x, p_max=3)
    a, b = mie.coefficients(m, x, n_max=c["N"])
    s = max(np.abs(a).max(), np.abs(b).max())
    r11 = max(np.abs(it["a"]["R11"]).max(), np.abs(it["b"]["R11"]).max())
    r22 = max(np.abs(it["a"]["R22"]).max(), np.abs(it["b"]["R22"]).max())
    big = max(np.abs(c["a"][1:]).max(), np.abs(c["b"][1:]).max()) / s
    nbig = int(np.argmax(np.abs(c["b"][1:]).max(0))) + 1
    th = np.radians(np.linspace(0, 180, 361))
    S1m, S2m = mie.amplitudes(a, b, th)
    Im = 0.5 * (np.abs(S1m) ** 2 + np.abs(S2m) ** 2)
    ratio = 0.0
    for p in (1, 2, 3):
        s1, s2 = mie.amplitudes(c["a"][p], c["b"][p], th)
        ratio = max(ratio, float(np.max(0.5 * (np.abs(s1) ** 2 + np.abs(s2) ** 2) / Im)))
    print(f"  m = {m}, x = {x:g}: max|R11| = {r11:.3g}, max|R22| = {r22:.3g}; largest |a^(p)|,|b^(p)| (p=1..3) = {big:.2e} "
          f"(b at n = {nbig}); largest Debye intensity p=1..3 / Mie intensity over 0-180 deg = {ratio:.2e}")
