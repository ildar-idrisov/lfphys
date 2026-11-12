# Review of the B1 corrections (reviewer's script). fp32 drawing (the kernel's declared bound 1e-5 of the peak,
# validated "до 1024 точек на ось") at the window sizes v08 uses (pad up to 16 at n = 256: 4096 points per axis):
# propagate_plane (its q_y sum in complex64), propagate_field and propagate_current against fp64. GPU 0.
import argparse
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee, rel  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core import geometry as G  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/01d_fp32_large_windows.txt")
dev = "gpu" if backend.devices()["gpu"]["available"] else "cpu"
K = 2 * math.pi / 0.5
DX = 0.125
n = 256
src = AS.Spectral((n, n), AF.rect_spectrum([(-2.75, -1.25, -4, 4), (1.25, 2.75, -4, 4)]))
pl = G.Plane.horizontal((0.4, 0.3, 0.86), (0.3, -0.4, 40.0))
ts = np.linspace(-45, 45, 96)
for pad in (4, 8, 16):
    m = n * pad
    res = {}
    for prec in ("fp32", "fp64"):
        backend.configure({"kernels": {"optics.angular_spectrum": {"device": dev, "precision": prec}}})
        res[prec] = (AS.propagate_plane(src, DX, K, pl, (-25.0, 25.0), ts, pad=pad)[1],
                     AS.propagate_field(src, DX, K, [80.0], pad=pad)[0],
                     AS.propagate_current(src, DX, K, [80.0], pad=pad))
    backend.configure(None)
    e_pl = rel(res["fp32"][0], res["fp64"][0])
    e_f = rel(res["fp32"][1], res["fp64"][1])
    e_j = float(np.max(np.abs(res["fp32"][2][0] - res["fp64"][2][0])) / np.max(np.abs(res["fp64"][2][0])))
    e_P = float(abs(res["fp32"][2][1][0] - res["fp64"][2][1][0]) / res["fp64"][2][1][0])
    out(f"{dev}: window {m} points per axis (k z up to {K * 80:.0f} rad): fp32 vs fp64 / peak: plane {e_pl:.2e}, "
        f"transverse plane z = 80 {e_f:.2e}, current {e_j:.2e}, power {e_P:.2e} (declared bound 1e-5)")
out("done")
