# Review B8-mie, script s09 (image light-funnel-ext): where miepython's coefficients lose accuracy. The xfail text of
# test_ext_mie_miepython.py says "its top orders lose accuracy at large x", but the xfailed rows are n = 1 and
# n = N/2. Error of a_n, b_n against the 40-digit reference of the comparison suite (_exact), per order band.
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys"); sys.path.insert(0, "/lf/lfphys/tests/external")
import miepython  # noqa: E402
from test_ext_mie_miepython import _exact, _c  # noqa: E402
from lfphys.core.optics import mie  # noqa: E402
print("miepython", miepython.__version__)
for x in (1000.0, 1e4):
    al, bl = (np.asarray(v) for v in miepython.coefficients(1.333, x))
    N = len(al)
    ea, eb = _exact(1.333, x, N)
    ea = np.array([_c(v) for v in ea]); eb = np.array([_c(v) for v in eb])
    amax = max(np.abs(ea).max(), np.abs(eb).max())
    err = np.maximum(np.abs(al - ea), np.abs(bl - eb)) / amax
    ae, be = mie.coefficients(1.333, x, n_max=N)
    erre = np.maximum(np.abs(ae - ea), np.abs(be - eb)) / amax
    bands = [(1, 10), (11, N // 4), (N // 4, N // 2), (N // 2, int(0.9 * x)), (int(0.9 * x), int(x)), (int(x), N)]
    print(f"x = {x:g}, N = {N}:")
    for lo, hi in bands:
        s = slice(lo - 1, hi)
        print(f"   n in [{lo}, {hi}]: miepython max err {err[s].max():.2e} (median {np.median(err[s]):.1e}); engine max {erre[s].max():.2e}")
    # is miepython's error a relative perturbation of x (backward-stable-like) or something else? relative errors at n=1
    print(f"   n = 1: |a_1| = {abs(ea[0]):.3f}, miepython rel err {abs(al[0] - ea[0]) / abs(ea[0]):.2e}")
