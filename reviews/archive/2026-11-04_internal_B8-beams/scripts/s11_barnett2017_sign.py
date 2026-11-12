"""s11: the curvature sign of the LG formula printed by Barnett, Babiker & Padgett, Phil. Trans. R. Soc. A 375, 20150444
(2017), Eq. (3.5) of the published text (PMC5247487; the equation image rsta20150444-e6), with their v = u e^{ikz}
(Eq. 3.2) and paraxial equation i du/dz = -(1/2k)(d2/dx2 + d2/dy2) u (Eq. 3.4). Their u is built here literally, with the
printed curvature factor exp(-i k rho^2 z / (2 (z_R^2 + z^2))), and with the opposite sign; the residual of Eq. (3.4)
by fourth-order differences, relative to |du/dz|. Written independently of lfphys."""
import math

import numpy as np
from scipy.special import eval_genlaguerre

k = 2 * math.pi
w0 = 2.0
zr = k * w0 * w0 / 2


def u(x, y, z, p, l, curv_sign):
    rho2 = x * x + y * y
    w = w0 * math.sqrt(1 + (z / zr) ** 2)
    C = math.sqrt(2 * math.factorial(p) / (math.pi * math.factorial(p + abs(l))))
    amp = C / w * (np.sqrt(2 * rho2) / w) ** abs(l) * np.exp(-rho2 / w ** 2) * eval_genlaguerre(p, abs(l), 2 * rho2 / w ** 2)
    ph = (l * np.arctan2(y, x) + curv_sign * k * rho2 * z / (2 * (zr * zr + z * z))
          - (2 * p + abs(l) + 1) * math.atan(z / zr))
    return amp * np.exp(1j * ph)


h = 2e-3
xs = np.linspace(-3, 3, 9)
X, Y = np.meshgrid(xs, xs, indexing="ij")
z = 0.37 * zr
for p, l in [(0, 1), (1, 2), (2, -3)]:
    for sgn, name in ((-1, "printed (-)"), (+1, "opposite (+)")):
        f = lambda a, b, c: u(a, b, c, p, l, sgn)  # noqa: E731
        d2 = lambda g: (-g(2) + 16 * g(1) - 30 * g(0) + 16 * g(-1) - g(-2)) / (12 * h * h)  # noqa: E731
        lap = d2(lambda s: f(X + s * h, Y, z)) + d2(lambda s: f(X, Y + s * h, z))
        dz = (-f(X, Y, z + 2 * h) + 8 * f(X, Y, z + h) - 8 * f(X, Y, z - h) + f(X, Y, z - 2 * h)) / (12 * h)
        res = np.max(np.abs(1j * dz + lap / (2 * k))) / np.max(np.abs(dz))
        print(f"LG_{{{p},{l}}}, curvature {name}: residual of i du/dz = -(1/2k) lap u: {res:.2e}")
