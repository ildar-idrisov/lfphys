# Review of the B1 corrections (reviewer's script). v08's window for a plane that turns the source
# (apparatus.window_for_plane): the estimate is measured on the plane z_max of the TURNED source, cropped to n x n in
# the turned frame; a slice through the box reaches the box's corners, outside that crop. Here: the drawn slice
# (apparatus.compute_slice with the window chosen) against (a) the same slice with a window 4x wider (converged, all
# points) and (b) the exact field without FFTs (rectangles_field) at sampled points; split into points inside the
# turned crop and outside it (box corners); and what verify_slice reports. GPU 0 for the wide windows when present.
import argparse
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core import geometry as G  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402
from v08_wave_3d.engine import apparatus as A  # noqa: E402
from v08_wave_3d.viz import SCHEMA  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("out/03_turned_window.txt")
gpu = backend.devices()["gpu"]["available"]
out(f"GPU available: {gpu}")

WORLDS = [
    ("default double (preset)", {}),
    ("circle (preset)", {"source": "circle", "a": 3.0, "zmax": 40.0}),
    ("gauss (preset)", {"source": "gauss", "zmax": 30.0}),
    ("square a = 2, zmax = 15", {"source": "square", "a": 2.0, "zmax": 15.0}),
    ("slit a = 1.5, L = 10, lam = 0.6, zmax = 15", {"source": "slit", "a": 1.5, "L": 10.0, "lam": 0.6, "zmax": 15.0}),
    ("double a = 1, d = 6, L = 12, lam = 0.4, zmax = 20", {"a": 1.0, "d": 6.0, "L": 12.0, "lam": 0.4, "zmax": 20.0}),
]
N = 256
AZ = (0.0, 45.0, 30.0)  # 0: control, the source not turned
for name, prm in WORLDS:
    p = {**SCHEMA.defaults(), **prm, "n": N}
    n = N
    lam = float(p["lam"])
    k = 2 * math.pi / lam
    dx = lam / 4
    x = (np.arange(n) - n // 2) * dx
    half = n // 2 * dx
    zmax = float(p["zmax"])
    box = ((float(x[0]), float(x[0]), 0.0), (float(x[-1]), float(x[-1]), zmax))
    znear = A.near_zone(dx, k)
    src = A.source(p, n)
    t0 = time.time()
    try:
        base = A.choose_window(src, dx, k, zmax)
    except ValueError as e:
        out(f"\n== {name}: refused ({str(e)[:80]}...)")
        continue
    peak = float(np.max(np.abs(base.plane)))
    out(f"\n== {name}: n {n}, dx {dx}, base {base.describe()} ({time.time() - t0:.1f} s)")
    for az in AZ:
        # a longitudinal plane through the box centre whose u is at azimuth az (normal horizontal)
        a = math.radians(az)
        nrm = (-math.sin(a), math.cos(a), 0.0)
        o = (0.0, 0.0, zmax / 2)
        pl, poly, s_rng, t_rng = A.plane_box(o, nrm, box)
        win = A.window_for_plane(src, dx, k, zmax, pl, base)
        s, t, U = A.compute_slice(src, dx, k, pl, s_rng, t_rng, win, box, nt=96, check=True)
        if gpu:
            backend.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
        wide = A.Window(win.pad * 4, win.band_limit, 0.0)
        _, _, Uw = A.compute_slice(src, dx, k, pl, s_rng, t_rng, wide, box, nt=96)
        backend.configure(None)
        P = A.slice_points(pl, s, t)
        phi = math.atan2(pl.u[1], pl.u[0])
        xr = math.cos(phi) * P[..., 0] + math.sin(phi) * P[..., 1]
        yr = -math.sin(phi) * P[..., 0] + math.cos(phi) * P[..., 1]
        in_crop = (np.abs(xr) <= half) & (np.abs(yr) <= half)
        fin = np.isfinite(U) & (P[..., 2] >= znear)
        d = np.abs(U - Uw) / peak
        d_in = float(np.nanmax(np.where(fin & in_crop, d, np.nan)))
        d_out = float(np.nanmax(np.where(fin & ~in_crop, d, np.nan))) if np.any(fin & ~in_crop) else float("nan")
        # exact field at points outside the crop (corners), deepest first
        idx = np.argwhere(fin & ~in_crop)
        ex_out = float("nan")
        if len(idx) and p["source"] != "circle":  # the circle's exact field is known on its axis only
            idx = idx[np.argsort(-P[idx[:, 0], idx[:, 1], 2])][: 60: 3]
            errs = []
            for i, j in idx:
                ref = A.reference(p, k, float(P[i, j, 2]), float(P[i, j, 0]), float(P[i, j, 1]))[0]
                errs.append(abs(U[i, j] - ref) / peak)
            ex_out = max(errs)
        tol = win.est * peak + 1e-9
        ver = A.verify_slice(p, k, pl, s, t, U, znear, tol)
        out(f"  azimuth {az:4.1f}: turned window x{win.pad} (bl {win.band_limit}), est {win.est:.2e} of the peak; "
            f"rows {[(r[0], r[1], f'{r[2]:.1e}') for r in win.rows]}")
        out(f"     drawn vs window x{4 * win.pad}: inside the turned crop {d_in:.2e}, outside it (box corners) {d_out:.2e}"
            f" of the peak; vs exact at {min(20, len(idx))} corner points {ex_out:.2e}; "
            f"fraction of slice points outside the crop {np.mean(~in_crop[fin]):.2f}")
        out(f"     verify_slice: {ver}")
out("done")
