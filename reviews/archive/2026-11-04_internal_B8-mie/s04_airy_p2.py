# Review B8-mie, script s04: the p = 2 Debye peak against Airy's theory at x = 1000 and 3000 (m = 1.333), both
# polarisations; the supernumerary maxima; Descartes' angles quoted in the docs; h against Hovenac & Lock's
# closed form (NASA CR-187191 Eq. 11: h = (p^2 - 1)^2 (p^2 - n^2)^(1/2) / (p^2 (n^2 - 1)^(3/2)), their Airy argument
# x^(2/3) Delta / h^(1/3)), which should equal |d^2 theta/db^2| / 2 of the engine.
import math
import sys

import numpy as np
from scipy.signal import argrelmax

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.optics import mie, mie_debye as dbe  # noqa: E402
from lfphys.theories.approx import rainbow as rb  # noqa: E402

for m in (4 / 3, 1.333, 1.335401):
    for p in (2, 3):
        d = rb.descartes(m, p)
        h_hl = (p * p - 1) ** 2 * math.sqrt(p * p - m * m) / (p * p * (m * m - 1) ** 1.5)
        print(f"m = {m:.6f}, p = {p}: Descartes theta = {math.degrees(d['theta']):.4f} deg, engine |h|/2 = "
              f"{abs(d['h']) / 2:.6f}, Hovenac-Lock h = {h_hl:.6f}")
print(f"Alexander band width (m = 1.335401): {math.degrees(rb.descartes(1.335401, 2)['theta'] - rb.descartes(1.335401, 3)['theta']):.3f} deg")

m = 1.333
for x in (1000.0, 3000.0):
    d = rb.descartes(m, 2)
    am = rb.airy_maxima(m, 2, x, 4)
    off = am[0] - d["theta"]
    th = d["theta"] + np.linspace(-0.5, 6.0, 26001) * off
    c = dbe.coefficients(m, x, p_max=2)
    S1, S2 = mie.amplitudes(c["a"][2], c["b"][2], th)
    for name, I, pol in (("s (|S1|^2)", np.abs(S1) ** 2, "s"), ("p (|S2|^2)", np.abs(S2) ** 2, "p")):
        k = int(np.argmax(I))
        A = rb.airy(m, 2, x, th, pol)
        mx = argrelmax(I, order=40)[0]
        sup = [math.degrees(th[j] - d["theta"]) for j in mx[:4]]
        print(f"x = {x:g}, {name}: Debye p=2 peak beyond Descartes {math.degrees(th[k] - d['theta']):.4f} deg, Airy "
              f"{math.degrees(off):.4f} deg (diff {100 * (th[k] - am[0]) / off:+.2f} % of the offset); peak Debye/Airy "
              f"{I[k] / A.max():.3f}; maxima offsets (deg) Debye {[round(v, 4) for v in sup]} vs Airy "
              f"{[round(math.degrees(v - d['theta']), 4) for v in am]}")
