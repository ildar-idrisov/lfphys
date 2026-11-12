"""Review B8 (slit): convergence of the waveguide-mode method at the default number of modes, against what v02 shows.

v02 shows conv = T(M + max(4, ceil(M/4))) / T(M) - 1 with a 1 % tolerance; the README claims "~M^-1.3; at the default
number of modes about 0.2 % in T for TM and 0.03 % for TE". Here: T(M) for M = default ... 8 x default, the observed
order p from three doublings, the Richardson limit, the true error at the default M, and the ratio true error / shown
change. Geometries (lambda = 1):
* v02's vector_narrow: two slits a = 0.5/0.6328, d = 3/0.6328, t = 0.2/0.6328 (thick: modal);
* the engine test's 1.3 lambda slit in a 0.5 lambda screen;
* a thin (t = 0) slit of k a = 100 and 130 (v02's cap; 'auto' takes the waveguide modes beyond k a = 40), against the
  edge basis (exponential convergence) as the reference.
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import slit as S  # noqa: E402

K = 2 * math.pi
lam = 0.6328


def study(label, centers, widths, t, pol, method="modal", ref=None):
    M0 = S._default_modes(K, max(np.atleast_1d(widths)), method)
    Ms = [M0, M0 + max(4, math.ceil(M0 / 4)), 2 * M0, 4 * M0, 8 * M0]
    T = []
    t0 = time.time()
    for M in Ms:
        T.append(S.solve(K, centers, widths, t, pol, modes=M, method=method).transmission())
    dt = time.time() - t0
    d1, d2 = T[2] - T[0], T[3] - T[2]
    d3 = T[4] - T[3]
    p = math.log2(abs(d1 / d2)) if d2 != 0 else float("nan")
    p2 = math.log2(abs(d2 / d3)) if d3 != 0 else float("nan")
    Tinf = T[4] + d3 / (2 ** p2 - 1) if ref is None else ref
    true = T[0] / Tinf - 1
    shown = T[1] / T[0] - 1
    print(f"{label} {pol}: default M = {M0}; T = " + ", ".join(f"{m}:{x:.8f}" for m, x in zip(Ms, T)) +
          f"\n   observed order p = {p:.2f} (M0->2M0->4M0), {p2:.2f} (2M0->4M0->8M0); limit {Tinf:.8f}"
          f"{' (edge basis)' if ref is not None else ' (Richardson)'}; true error at M0 = {true:+.2e}; "
          f"shown T(1.25 M0)/T(M0)-1 = {shown:+.2e}; ratio true/shown = {true / shown if shown else float('nan'):.1f}; "
          f"{dt:.0f} s")


a, d, t = 0.5 / lam, 3.0 / lam, 0.2 / lam
for pol in ("TE", "TM"):
    study("vector_narrow (2 slits a = 0.79, d = 4.74, t = 0.316)", [-d / 2, d / 2], a, t, pol)
for pol in ("TE", "TM"):
    study("test geometry (w = 1.3, t = 0.5)", [0.0], 1.3, 0.5, pol)
for ka in (100.0, 130.0):
    w = ka / K
    for pol in ("TE", "TM"):
        t0 = time.time()
        ref = S.solve(K, [0.0], [w], 0.0, pol, modes=80, method="edge").transmission()
        ref2 = S.solve(K, [0.0], [w], 0.0, pol, modes=100, method="edge").transmission()
        print(f"thin k a = {ka:g}: edge basis T(80) = {ref:.10f}, T(100) = {ref2:.10f} ({time.time() - t0:.0f} s)")
        study(f"thin slit k a = {ka:g} (w = {w:.2f})", [0.0], w, 0.0, pol, ref=ref2)
