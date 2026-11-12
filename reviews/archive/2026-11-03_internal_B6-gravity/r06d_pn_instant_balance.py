# Reviewer script (B6 gravity): the instantaneous energy balance of the engine's PN equations on circular states
# (no time integration): -dE_2PN/dt along the full acceleration (1PN, 2PN, 2.5PN, 3.5PN), divided by the 1PN flux
# F = 32/5 nu^2 x^5 [1 + (-1247/336 - 35/12 nu) x] (Blanchet 2014, LRR 17, 2, Eq. 314, verified in sources/), x from
# the state's Omega. (ratio - 1)/x^2 shows whether the playground's residual "-40 .. -70 x^2" is a property of the
# equations (the absent 2PN-relative radiation reaction) and how it depends on nu.  The physical 2PN flux coefficient
# for comparison: -44711/9072 + 9271/504 nu + 65/18 nu^2.
import numpy as np

from lfphys.core.gravity import pn_binary as PN

for q in (1.0, 0.25, 0.05):
    nu = q / (1 + q) ** 2
    c2 = -44711 / 9072 + 9271 / 504 * nu + 65 / 18 * nu * nu
    print(f"q = {q}, nu = {nu:.4f} (physical 2PN flux coefficient {c2:+.3f})")
    for r in (3000.0, 1000.0, 300.0, 100.0, 30.0, 20.0, 12.0, 10.0, 8.0):
        st = PN.circular_state(r, nu, (1, 2, 2.5, 3.5), quasi=False)
        x, v = st["x"], st["v"]
        a = PN.acceleration(x, v, nu, (1, 2, 2.5, 3.5))
        Edot = float(PN.rate_along(lambda X, V: PN.energy(X, V, nu, 2), x, v, a))
        Om = np.linalg.norm(np.cross(x, v)) / r ** 2
        xx = Om ** (2 / 3)
        F = 32 / 5 * nu ** 2 * xx ** 5 * (1 + (-1247 / 336 - 35 / 12 * nu) * xx)
        ratio = -nu * Edot / F
        print(f"   r = {r:7.1f}  x = {xx:.5f}  -dE/dt / F_1PN = {ratio:.8f}  (ratio - 1)/x^2 = {(ratio - 1) / xx ** 2:9.3f}"
              f"  playground tol 100 x^2 (x = 1/r) = {100 / r ** 2:.3g}")
