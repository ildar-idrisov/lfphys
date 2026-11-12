# B2 review, check 12: v09's note "the seam's error falls as 1/N^2" (viz.py:371): differences of the holonomy between
# seams of N, 2N, 4N burns (preset seam: rho 0.9, chi 30 deg, default plane).
# Run: docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server light-funnel-viz python3 reviews/2026-10-27_internal_B2/c12_seam_order.py
import math

import numpy as np

from lfphys.core import spin_transport as T
from v09_thomas_3d.engine import loops as LP

e1, e2, n = LP.base_frame(90.0, 90.0)
R = {}
for N in (48, 96, 192, 384, 768):
    R[N] = T.holonomy(T.Manoeuvre(T.polygon_burns(LP.seam_vertices(0.9, math.radians(30.0), e1, e2, n, N))).end())["R"]
for N in (48, 96, 192, 384):
    d1 = np.max(np.abs(R[N] - R[2 * N]))
    d2 = np.max(np.abs(R[2 * N] - R[4 * N])) if 4 * N in R else float("nan")
    print(f"N = {N:4d}: |R_N - R_2N| = {d1:.3e}; ratio to the next halving {d1 / d2:.2f}" if 4 * N in R else
          f"N = {N:4d}: |R_N - R_2N| = {d1:.3e}")
