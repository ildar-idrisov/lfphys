# Review B8-mie, script s12: v17's "energy" check for transparent drops with N <= 150 terms (x up to ~112): Gauss-
# Legendre quadrature of |S1|^2 + |S2|^2 with numpy's leggauss(2N + 20) against Q_ext, tolerance 200 N eps + 1e-12
# (relative). s08 found numpy's weights near mu = +-1 off by ~1e-11 already at 292 nodes. Scan of water drops (10 C,
# 550 nm) over x in [60, 112], replicating the check's arithmetic; then one world through the harness.
import sys
import numpy as np
for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from lfphys.core import data as D  # noqa: E402
from lfphys.core.optics import mie  # noqa: E402
from harness import Harness  # noqa: E402

EPS = np.finfo(float).eps
m = complex(float(D.water_index(550.0, 10.0)))
fails = []
xs = np.linspace(60.0, 112.0, 105)
worst = (0, None)
for x in xs:
    a, b = mie.coefficients(m, x)
    N = len(a)
    if N > 150:
        continue
    q = mie.efficiencies_from(a, b, x)
    mu, wq = np.polynomial.legendre.leggauss(2 * N + 20)
    s1, s2 = mie.amplitudes(a, b, np.arccos(mu))
    qs = float(wq @ (np.abs(s1) ** 2 + np.abs(s2) ** 2)) / x ** 2
    rel = abs(qs - q["Qext"]) / q["Qext"]
    tol = 200 * N * EPS + 1e-12
    if rel / tol > worst[0]:
        worst = (rel / tol, (x, N, rel, tol))
    if rel > tol:
        fails.append((round(float(x), 2), N, f"{rel:.1e}", f"{tol:.1e}"))
print(f"x in [60, 112]: {len(fails)} of {len(xs)} sizes fail the check; worst rel/tol {worst[0]:.2f} at {worst[1]}")
print("failing (x, N, rel, tol):", fails[:12])
if fails:
    x = fails[0][0]
    r_um = x * 0.55 / (2 * np.pi)
    h = Harness("v17_mie_scattering", "glory", {"radius_um": float(r_um), "width": 0.0, "n_lam": 8})
    c = h.checks()["energy"]
    print(f"harness, radius {r_um:.4f} um (x = {x}): energy check value {c['value']!r} ref {c['ref']!r} rel {c['rel']:.2e} "
          f"tol {c['tol']:.2e} -> {'FAIL' if abs(c['rel']) > c['tol'] else 'ok'}")
