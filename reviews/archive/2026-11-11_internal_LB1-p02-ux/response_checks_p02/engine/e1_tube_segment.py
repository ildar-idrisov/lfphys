# Check schrodinger_nd.flux_tube_segment against direct Gauss-Legendre quadrature of the tube's A along the segment
import math, numpy as np
from lfphys.core.quantum import schrodinger_nd as S
g = S.Grid((64, 64), 0.37, center=(0.3, -0.2))
for flux, c, R, s in ((math.pi, (1.1, -0.7), 0.8, (3.0, 1.5)), (-2.0, (-2.0, 3.0), 1.5, (-1.2, 4.0)), (1.0, (0.0, 0.0), 0.5, (0.0, -6.0))):
    A = S.flux_tube(flux, c, R)
    chi = S.flux_tube_segment(g, flux, s, c, R)
    X = g.mesh(sparse=False)
    s_ = np.array(s)
    xg, wg = np.polynomial.legendre.leggauss(400)
    ref = np.zeros(g.shape)
    for t, w in zip(0.5 * (xg + 1), 0.5 * wg):
        P = [X[i] - s_[i] + t * s_[i] for i in range(2)]
        ref += w * sum(A.fn(i, *P) * s_[i] for i in range(2))
    # points where the segment passes within 0.4 R of the axis are a near-singular quadrature: compare the rest
    u = s_ / np.linalg.norm(s_)
    ra, rb = X[0] - c[0], X[1] - c[1]
    t = np.clip((ra * s_[0] + rb * s_[1]) / (s_ @ s_), 0, 1)
    dist = np.hypot(ra - t * s_[0], rb - t * s_[1])
    far = dist > 0.4 * R
    print(f"flux {flux}, R {R}, s {s}: max |chi - GL400| = {np.max(np.abs(chi - ref)[far]):.2e} "
          f"(max |chi| {np.max(np.abs(chi)):.3g}; points compared {far.sum()} of {far.size})")
