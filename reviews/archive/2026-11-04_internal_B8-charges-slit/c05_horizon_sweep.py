"""Review B8 (charges): hyperbolic motion (g = 3e15 m/s^2, c^2/g = 30 m, along +x), field points at t = 0 on and off
the axis at a depth delta beyond (delta < 0: inside) the horizon x = -c^2/g (for t = 0 the horizon is the plane
x = -c^2/g). Beyond it no retarded time exists. Counts of fake roots (a time returned) and, inside, the error of the
returned time against the closed form (axis points)."""
import sys
import numpy as np
sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import charges as ch  # noqa: E402
C = ch.C
g = 3e15
a = C * C / g
w = ch.hyperbolic(g, direction=(1, 0, 0))
rng = np.random.default_rng(0)
for depth in (100.0, 30.0, 10.0, 1.0, 0.1, 1e-3):
    fake = 0
    n = 60
    for i in range(n):
        x = np.array([-a - depth, rng.uniform(-20, 20), rng.uniform(-20, 20)])
        try:
            ch.retarded_time(w, x[None], np.array([0.0]))
            fake += 1
        except (RuntimeError, ValueError):
            pass
    print(f"beyond the horizon by {depth:g} m: {fake} of {n} points get a retarded time (none exists)")
for depth in (1.0, 1e-2, 1e-4, 1e-6):
    X = -a + depth
    tr = ch.retarded_time(w, np.array([[X, 0.0, 0.0]]), np.array([0.0]))[0]
    eta = np.log((a + X) / a)
    exact = a * np.sinh(eta) / C
    print(f"inside by {depth:g} m (axis): t_ret = {tr:.6e} s, exact {exact:.6e} s, rel error {abs(tr / exact - 1):.1e}")
