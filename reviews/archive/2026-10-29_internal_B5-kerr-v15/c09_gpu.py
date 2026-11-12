# [root path fixed after archiving, 2026-10-29, by the responder: reviews/ -> reviews/archive/]
# Review B5, check c09 (GPU 0): the kernel "gravity.kerr_shadow" on CuPy against NumPy, and v15's live check `gpu`
# (tolerance 1e-12 absolute on g of the middle row, and the same finite/NaN pattern) in worlds forced onto the GPU.
# (a) whole screens chi = 0.9 / 0.998, 60 / 89.5 deg, 256 x 256: the largest |g_gpu - g_cpu| and r differences over
#     all pixels, and over pixels within 0.05 M of the critical curve; pixels whose fate or crossing set differ;
# (b) v15 worlds (presets and a few others at res "l") built with the device of the kernel forced to "gpu":
#     the `gpu` check's value and ok.
#
# Root: engine at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this script in
# /lf/reviews/archive/2026-10-29_internal_B5-kerr-v15/. GPU 0 only, through the scratchpad's gpu_run.sh:
#   gpu_run.sh lf-rev15-gpu --rm --gpus '"device=0"' --user "$(id -u):$(id -g)" -e HOME=/tmp -v <engine>:/lf:ro \
#     -v <this folder>:<same path rw> -e PYTHONPATH=... -w <this folder> light-funnel-viz python3 c09_gpu.py
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness  # noqa: E402

from lfphys.core import backend as B  # noqa: E402
from lfphys.core.gravity import kerr_null as KN, kerr_shadow as KS  # noqa: E402


def dist_to_curve(a, b, cc):
    al, be = np.append(cc["alpha"], cc["alpha"][0]), np.append(cc["beta"], cc["beta"][0])
    d = np.full(a.shape, np.inf)
    for i in range(al.size - 1):
        x0, y0, x1, y1 = al[i], be[i], al[i + 1], be[i + 1]
        ex, ey = x1 - x0, y1 - y0
        L2 = ex * ex + ey * ey
        if L2 == 0:
            continue
        t = np.clip(((a - x0) * ex + (b - y0) * ey) / L2, 0, 1)
        d = np.minimum(d, np.hypot(a - x0 - t * ex, b - y0 - t * ey))
    return d


def main():
    print("devices:", B.devices()["gpu"])
    print("== (a) whole screens, CPU vs GPU ==")
    for chi, thd in ((0.9, 60.0), (0.998, 89.5), (0.5, 17.0)):
        th = math.radians(thd)
        sc = KS.Screen(256, 256, 9.0)
        a, b = sc.rows(0, sc.ny)
        B.configure({"kernels": {KS.KERNEL: {"device": "cpu"}}})
        cpu = KS.trace_screen(a, b, th, chi, 2)
        B.configure({"kernels": {KS.KERNEL: {"device": "gpu"}}})
        t0 = time.time()
        gpu = KS.trace_screen(a, b, th, chi, 2)
        dt = time.time() - t0
        used = B.used()[KS.KERNEL]["drawn"]["device"]
        cc = KN.critical_curve(chi, th, 4001)
        near = dist_to_curve(a, b, cc) < 0.05
        fate = int(np.sum(cpu["captured"] != gpu["captured"]))
        fin = np.isfinite(cpu["g_n"]) != np.isfinite(gpu["g_n"])
        both = np.isfinite(cpu["g_n"]) & np.isfinite(gpu["g_n"])
        dg = np.where(both, np.abs(cpu["g_n"] - gpu["g_n"]), 0.0)
        dr = np.where(both, np.abs(cpu["r_n"] - gpu["r_n"]) / np.where(both, cpu["r_n"], 1.0), 0.0)
        out = (f"chi={chi} th={thd} ({used}, {dt * 1e3:.0f} ms): fate differs {fate}; finite pattern of g differs "
               f"{int(fin.sum())} (near curve {int((fin & near[None]).sum())}); max |dg| {dg.max():.2e} (far "
               f"{np.where(near[None], 0, dg).max():.2e}); max rel |dr| {dr.max():.2e}")
        if fin.any():
            n, i, j = np.argwhere(fin)[0]
            out += (f"; e.g. n={n} pixel ({a[i, j]:.6f}, {b[i, j]:.6f}): cpu r {cpu['r_n'][n, i, j]!r} g "
                    f"{cpu['g_n'][n, i, j]!r}, gpu r {gpu['r_n'][n, i, j]!r} g {gpu['g_n'][n, i, j]!r}")
        print(out, flush=True)
    print("== (b) v15 worlds forced to the GPU: the `gpu` check ==")
    for preset, params in (("m87", {"res": "l"}), ("edge_on", {"res": "l"}), ("ring", {"res": "l"}),
                           (None, {"res": "l", "chi": 0.998, "incl": 89.5}), (None, {"res": "l", "chi": 0.9, "incl": 60.0,
                                                                                    "emitter": "keplerian"}),
                           (None, {"res": "m", "chi": 0.7, "incl": 75.0, "retro": True})):
        B.configure({"kernels": {KS.KERNEL: {"device": "gpu"}}})
        h = Harness("v15_kerr_shadow", preset, params)
        from v15_kerr_shadow.viz import SCAN_M
        h.run_to(SCAN_M * 1.01)
        c = h.checks().get("gpu")
        print(f"{preset} {params}: gpu check {None if c is None else (c['value'], c['ok'])}; device "
              f"{B.used().get(KS.KERNEL, {}).get('drawn')}", flush=True)
    B.configure(None)


if __name__ == "__main__":
    main()
