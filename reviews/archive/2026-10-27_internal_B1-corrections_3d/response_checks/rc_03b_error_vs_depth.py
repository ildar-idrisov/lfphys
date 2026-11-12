# Review of the B1 corrections (reviewer's script). v08's window error is estimated on the deepest plane z_max only
# Response check (written by the responder): the reviewer's script 03b_error_vs_depth.py, unchanged but for its output file, run on the processed code.
# (apparatus.choose_window) and used as the tolerance of every slice. Is the drawn field's error largest at z_max?
# For each preset world: the default slice (plane 1, y = 0, nt = 256 as the run draws it) against the exact field
# without FFTs at many depths (circle: its axis, closed form; Gaussian: Hankel integral; rectangles: RS-I integral),
# and the same against a window 4x wider; then the real run (Harness) and its checks for that preset.
import argparse
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
sys.path.insert(0, "/lf/visualizations/tests")
from common_rev import Tee  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402
from v08_wave_3d.engine import apparatus as A  # noqa: E402
from v08_wave_3d.viz import SCHEMA  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("response_checks/03b_error_vs_depth_after.txt")
gpu = backend.devices()["gpu"]["available"]
out(f"GPU available: {gpu}")

for preset in ("circle", "gauss", "double", "square_big"):
    p = SCHEMA.resolve(preset, None)[0]
    n = int(p["n"])
    lam = float(p["lam"])
    k = 2 * math.pi / lam
    dx = lam / 4 if n <= 256 else lam / 8
    x = (np.arange(n) - n // 2) * dx
    zmax = float(p["zmax"])
    box = ((float(x[0]), float(x[0]), 0.0), (float(x[-1]), float(x[-1]), zmax))
    znear = A.near_zone(dx, k)
    src = A.source(p, n)
    t0 = time.time()
    if gpu:
        backend.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
    win = A.choose_window(src, dx, k, zmax)
    peak = float(np.max(np.abs(win.plane)))
    pl, poly, s_rng, t_rng = A.plane_box((0.0, 0.0, zmax / 2), (0.0, -1.0, 0.0), box)
    s, t, U = A.compute_slice(src, dx, k, pl, s_rng, t_rng, win, box, check=True)
    wide = A.Window(min(win.pad * 4, 4096 // n), win.band_limit, 0.0)
    _, _, Uw = A.compute_slice(src, dx, k, pl, s_rng, t_rng, wide, box, check=True)
    backend.configure(None)
    z = pl.origin[2] + t * pl.v[2]
    out(f"\n== preset {preset}: source {p['source']}, n {n}, dx {dx}, z_max {zmax}; {win.describe()}; "
        f"tolerance of slices = est x peak = {win.est * peak:.2e} ({time.time() - t0:.1f} s)")
    # exact references along depth
    rows = []
    if p["source"] == "circle":
        j0 = int(np.argmin(np.abs(s)))
        for it in range(len(t)):
            if z[it] < znear:
                continue
            ref = AF.circle_on_axis(k, float(p["a"]), float(z[it]))
            rows.append((z[it], abs(U[it, j0] - ref) / peak, abs(U[it, j0] - Uw[it, j0]) / peak))
        what = "axis (closed form)"
    else:
        cols = np.linspace(0, len(s) - 1, 9).astype(int)
        for it in range(0, len(t), 8):
            if z[it] < znear:
                continue
            worst, worst_w = 0.0, 0.0
            for j in cols:
                ref = A.reference(p, k, float(z[it]), float(pl.origin[0] + s[j] * pl.u[0]), 0.0)[0]
                worst = max(worst, abs(U[it, j] - ref) / peak)
                worst_w = max(worst_w, abs(U[it, j] - Uw[it, j]) / peak)
            rows.append((z[it], worst, worst_w))
        what = "9 points across x (RS-I / Hankel)"
    rows = np.array(rows)
    imax = int(np.argmax(rows[:, 1]))
    out(f"  vs exact on {what}: max over depths {rows[imax, 1]:.2e} at z = {rows[imax, 0]:.2f} "
        f"(at z_max {rows[-1, 1]:.2e}); estimate used as tolerance {win.est:.2e}; ratio {rows[imax, 1] / win.est:.1f}")
    dW = np.abs(U - Uw) / peak
    dzmax = np.nanmax(dW, axis=1)
    iw = int(np.nanargmax(np.where(z >= znear, dzmax, np.nan)))
    out(f"  vs window x{wide.pad} over the whole slice: max {dzmax[iw]:.2e} at z = {z[iw]:.2f} (at z_max {dzmax[-1]:.2e})")
    for zz, e, ew in rows[:: max(1, len(rows) // 8)]:
        out(f"     z = {zz:6.2f}: |drawn - exact|/peak {e:.2e}   |drawn - wide|/peak {ew:.2e}")
    # the real run of this preset (CPU) and its checks
    t0 = time.time()
    from harness import Harness  # noqa: E402
    h = Harness("v08_wave_3d", preset)
    sl = h.of("slice")[-1]
    bad = [c["id"] for c in h.checks().values() if not c.get("info") and c.get("ok") is False]
    out(f"  real run ({time.time() - t0:.1f} s): slice 1 verify {sl.get('verify')}; failed checks {bad}")
    if p["source"] == "circle":
        U1 = h.sim.slices[1]["U"]
        s1, t1 = h.sim.slices[1]["s"], h.sim.slices[1]["t"]
        j0 = int(np.argmin(np.abs(s1)))
        z1 = h.sim.slices[1]["plane"].origin[2] + t1 * h.sim.slices[1]["plane"].v[2]
        errs = [abs(U1[i, j0] - AF.circle_on_axis(k, float(p["a"]), float(z1[i]))) / peak
                for i in range(len(t1)) if z1[i] >= znear]
        out(f"  real run, slice 1 on the axis vs closed form at {len(errs)} depths: max {max(errs):.2e}, "
            f"{np.mean(np.array(errs) > win.est):.0%} of depths above the estimate {win.est:.2e}")
out("done")
