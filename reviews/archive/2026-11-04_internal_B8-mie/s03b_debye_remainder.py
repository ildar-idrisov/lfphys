# Review B8-mie, script s03b: where the partial Debye sums plus the closed-form remainder miss a_n (s03 found 5e-4
# for m = 1 + 1e-6 i, x = 100): the remainder -T21T12 R11^p/(2(1 - R11)) takes 1 - R11 from the cancellation-free
# form but R11^p from R11 computed directly; where R11 -> 1 (tunnelling orders) the two disagree.
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie, mie_debye as dbe  # noqa: E402

for m, x in [(1.0 + 1e-6j, 100.0), (1.0001, 100.0), (1.01, 100.0), (1.05, 100.0), (1.1, 1000.0), (1.333, 100.0),
             (1.333, 10.0), (1.5 + 0.01j, 50.0)]:
    c = dbe.coefficients(m, x, p_max=4)
    it = dbe.interface_terms(m, x)
    a, b = mie.coefficients(m, x, n_max=c["N"])
    s = max(np.abs(a).max(), np.abs(b).max())
    worst = 0.0
    where = None
    for key, ref in (("a", a), ("b", b)):
        e = np.abs(c[key].sum(0) + c["remainder_" + key] - ref) / s
        k = int(np.argmax(e))
        if e[k] > worst:
            worst, where = float(e[k]), (key, k + 1)
    key, n = where
    R11 = it[key]["R11"][n - 1]
    omr = it[key]["one_minus_R11"][n - 1]
    terms = np.abs(c[key][:, n - 1]).max() / s
    print(f"m = {m}, x = {x:g}: worst |partial(p<=4) + remainder - Mie| = {worst:.1e} of the largest coefficient, at "
          f"{key}_{n}; there |1 - R11| direct {abs(1 - R11):.3e}, cancellation-free {abs(omr):.3e}; largest |term p<=4| "
          f"{terms:.1e}; closed-form sum err {np.abs(c['sum_' + key] - (a if key == 'a' else b)).max() / s:.1e}")
