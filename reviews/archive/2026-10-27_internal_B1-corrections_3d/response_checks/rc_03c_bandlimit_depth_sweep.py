# Review of the B1 corrections (reviewer's script). Sweep of v08 worlds over the schema's range: which sum the window
# Response check (written by the responder): the reviewer's script 03c_bandlimit_depth_sweep.py, unchanged but for its output file, run on the processed code.
# choice picks, and the drawn field's error at every depth of the volume (96 planes, as drawn) against the same
# volume with a 4x wider window (same sum), compared with the estimate measured on z_max only. Also the plain sum
# at the same pad, to see which part of the error is the band limit's. GPU 0.
import argparse
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from v08_wave_3d.engine import apparatus as A  # noqa: E402
from v08_wave_3d.viz import SCHEMA  # noqa: E402

argparse.ArgumentParser(description=__doc__).parse_args()
out = Tee("response_checks/03c_bandlimit_depth_sweep_after.txt")
if backend.devices()["gpu"]["available"]:
    backend.configure({"kernels": {"optics.angular_spectrum": {"device": "gpu"}}})
WORLDS = [
    {"source": "circle", "a": 3.0, "zmax": 40.0},
    {"source": "circle", "a": 1.0, "zmax": 20.0},
    {"source": "circle", "a": 5.0, "zmax": 60.0, "lam": 0.8},
    {"source": "square", "a": 3.0, "zmax": 40.0},
    {"source": "square", "a": 1.0, "zmax": 25.0},
    {"source": "slit", "a": 2.0, "L": 12.0, "zmax": 40.0},
    {"source": "double", "a": 1.0, "d": 6.0, "L": 12.0, "zmax": 40.0},
    {"source": "double", "a": 0.5, "d": 3.0, "L": 6.0, "zmax": 50.0, "lam": 0.7},
    {"source": "gauss", "w": 0.5, "zmax": 40.0},
    {"source": "gauss", "w": 1.0, "zmax": 60.0, "lam": 1.0},
]
NZ = 96
n = 256
for prm in WORLDS:
    p = {**SCHEMA.defaults(), **prm, "n": n}
    lam = float(p["lam"])
    k = 2 * math.pi / lam
    dx = lam / 4
    zmax = float(p["zmax"])
    znear = A.near_zone(dx, k)
    src = A.source(p, n)
    t0 = time.time()
    try:
        win = A.choose_window(src, dx, k, zmax)
    except ValueError:
        out(f"{prm}: refused (window)")
        continue
    zs = np.linspace(0.0, zmax, NZ)
    deep = zs >= znear
    vol = AS.propagate_field(src, dx, k, zs, pad=win.pad, check=True, band_limit=win.band_limit)
    peak = float(np.max(np.abs(win.plane)))
    wp = min(4 * win.pad, 4096 // n)
    ref = AS.propagate_field(src, dx, k, zs, pad=wp, check=True, band_limit=win.band_limit)
    e = np.max(np.abs(vol - ref), axis=(1, 2)) / peak
    i = int(np.argmax(np.where(deep, e, -1)))
    line = (f"{str(prm):<72} {win.describe():<60} max over depths {e[i]:.2e} at z = {zs[i]:5.1f} "
            f"(z_max {e[-1]:.2e}); max/est {e[i] / win.est:4.1f}")
    if win.band_limit:
        plain = AS.propagate_field(src, dx, k, zs, pad=win.pad, check=True, band_limit=False)
        refp = AS.propagate_field(src, dx, k, zs, pad=wp, check=True, band_limit=False)
        ep = np.max(np.abs(plain - refp), axis=(1, 2)) / peak
        line += f"; plain sum at the same pad: max {ep[deep].max():.2e} (z_max {ep[-1]:.2e})"
    out(line + f"  [{time.time() - t0:.1f} s]")
out("done")
