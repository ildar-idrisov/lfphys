"""R04b: a summary of r04_series.npz (the karman preset's series written by r04_preset_karman.py)."""
import numpy as np

d = np.load("/out/r04_series.npz")
t, rc = d["t"], d["re_cell"]
for a, b in ((0.0, 1.0), (1.0, 4.0), (4.0, 7.0), (7.0, 11.0)):
    m = (t > a) & (t <= b)
    print("t in (%.0f, %.0f] s: cell Re max %.3f, fraction of samples above 10: %.2f" % (a, b, rc[m].max(), np.mean(rc[m] > 10)))
