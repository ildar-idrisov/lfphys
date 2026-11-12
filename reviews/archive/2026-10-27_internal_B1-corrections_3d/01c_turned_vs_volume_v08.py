# Review of the B1 corrections (reviewer's script). v08's default world (double, n = 256, window as chosen): a slice
# whose plane turns the source (azimuth 30 deg, through the axis) against what the VOLUME's sum gives at the same
# points (the unturned lattice, same pad and sum: brute force on GPU 0, no FFT) and against the exact field (RS-I,
# no FFT). The slice is labelled "точно для этой плоскости (как дал бы объём на этой сетке)".
import argparse
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee, spectrum_grid  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402
from v08_wave_3d.engine import apparatus as A  # noqa: E402
from v08_wave_3d.viz import SCHEMA  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/01c_turned_vs_volume_v08.txt")
import cupy as cp  # noqa: E402

backend.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
p = SCHEMA.resolve("double", None)[0]
n = 256
lam = float(p["lam"])
k = 2 * math.pi / lam
dx = lam / 4
x = (np.arange(n) - n // 2) * dx
zmax = float(p["zmax"])
box = ((float(x[0]), float(x[0]), 0.0), (float(x[-1]), float(x[-1]), zmax))
src = A.source(p, n)
base = A.choose_window(src, dx, k, zmax)
peak = float(np.max(np.abs(base.plane)))
out(f"default double: {base.describe()}")
for az in (30.0, 45.0, 90.0):
    a = math.radians(az)
    pl, poly, s_rng, t_rng = A.plane_box((0.0, 0.0, zmax / 2), (-math.sin(a), math.cos(a), 0.0), box)
    win = A.window_for_plane(src, dx, k, zmax, pl, base)
    s, t, U = A.compute_slice(src, dx, k, pl, s_rng, t_rng, win, box, nt=64, check=True)
    P = A.slice_points(pl, s, t)
    sel = np.argwhere(np.isfinite(U) & (P[..., 2] > 2.0))[::23]
    pts = P[sel[:, 0], sel[:, 1]]
    m, QX, QY, Aq, kz = spectrum_grid(AF.rect_spectrum(A.rects(p)), n, dx, k, base.pad)
    qx, qy, aa, kzz = (cp.asarray(v.ravel()) for v in (QX, QY, Aq, kz))
    vol = np.empty(len(pts), complex)
    for i0 in range(0, len(pts), 16):
        Pc = cp.asarray(pts[i0:i0 + 16])
        ph = cp.exp(1j * (Pc[:, 0:1] * qx[None, :] + Pc[:, 1:2] * qy[None, :] + Pc[:, 2:3] * kzz[None, :]))
        vol[i0:i0 + 16] = cp.asnumpy(ph @ aa) / (m * m)
    Us = U[sel[:, 0], sel[:, 1]]
    ex = np.array([AF.rectangles_field(k, A.rects(p), float(q[2]), float(q[0]), float(q[1]))[0] for q in pts[::4]])
    out(f"azimuth {az:4.0f}: window of the slice x{win.pad} (est {win.est:.1e}); at {len(pts)} points: "
        f"max|slice - volume's sum| = {np.max(np.abs(Us - vol)) / peak:.2e} of the peak; "
        f"slice vs exact {np.max(np.abs(Us[::4] - ex)) / peak:.2e}, volume's sum vs exact {np.max(np.abs(vol[::4] - ex)) / peak:.2e}")
out("done")
