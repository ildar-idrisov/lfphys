# Review of the B1 corrections (reviewer's script). A plane turned by 90 degrees (u = +y) against the volume when the
# aperture's edges are NOT multiples of dx: the turned spectrum A(R q) on the grid replaces the Nyquist line
# q_x = -pi/dx by +pi/dx (fftfreq is asymmetric), so the two routes differ there. Measured at depth (z_near: 1e-6
# expected at most) and next to the aperture (hatched zone). A source even in x has A(pi/dx) = A(-pi/dx): no
# difference; v08's apertures are all centred (even), so v08 is not affected, the engine API is.
import argparse
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core import geometry as G  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/01b_turn90_nyquist.txt")
backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
LAM = 0.6
K = 2 * math.pi / LAM
DX = LAM / 4
ZNEAR = math.log(1e6) / math.sqrt((math.pi / DX) ** 2 - K * K)
n = 128
x = (np.arange(n) - n // 2) * DX
for rects in ([(-2.75, -1.25, -4.0, 4.0), (1.25, 2.75, -4.0, 4.0)], [(-0.7, 0.7, -0.7, 0.7)],
              [(-2.6, -1.1, -4.0, 4.0), (1.3, 2.9, -3.0, 4.0)], [(-0.53, 0.81, -0.62, 0.7)]):  # symmetric, then not
    src = AS.Spectral((n, n), AF.rect_spectrum(rects))
    edges_on_nodes = all(abs(e / DX - round(e / DX)) < 1e-9 for r in rects for e in r)
    zs = np.array([0.0, 0.25 * ZNEAR, 0.5 * ZNEAR, ZNEAR, 2 * ZNEAR, 10.0])
    vol = AS.propagate_field(src, DX, K, zs, pad=2, check=True)
    peak = np.max(np.abs(vol[1:]))
    c = n // 2 + 3
    # plane x = x[c] with normal +x: u = +y, v = +z (the source turned by 90 degrees)
    pl = G.Plane.horizontal((1.0, 0.0, 0.0), (x[c], 0.0, 0.0))
    s, U = AS.propagate_plane(src, DX, K, pl, (float(x[0]), float(x[-1])), zs, pad=2, check=True)
    jj = np.rint(s / DX).astype(int) + n // 2
    ok = (jj >= 0) & (jj < n)
    out(f"rects {rects} (edges on nodes: {edges_on_nodes}); lambda {LAM}, dx {DX}, z_near {ZNEAR:.3f}")
    for i, z in enumerate(zs):
        d = np.max(np.abs(U[i, ok] - vol[i, c, jj[ok]])) / peak
        out(f"   z = {z:7.3f} ({z / ZNEAR:5.2f} z_near): max|turned plane - volume| / peak = {d:.2e}")
out("done")
