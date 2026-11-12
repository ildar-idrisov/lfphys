# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Response to review B1: the reviewer's inputs re-run on the processed code (written by the responder, not the
reviewer). Run in the image from engine/ with GPU 0:
  docker run --rm --user 1000:1000 --gpus '"device=0"' -v "$PWD":/lf -w /lf/reviews/archive/2026-10-27_internal_B1 \
    -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server light-funnel-viz \
    python3 response_checks/rc_b1.py > response_checks/rc_b1.txt
"""

import argparse
import math

import numpy as np


def b1_1():
    from lfphys.core.optics import angular_spectrum as AS
    from v08_wave_3d.engine import apparatus as A
    from v08_wave_3d.viz import SCHEMA, Simulation
    print("B1-1 (a) the reviewer's wide-angle world (double, a 0.2, lambda 1.5, n 128, z_max 80):")
    p = SCHEMA.resolve(None, {"source": "double", "lam": 1.5, "a": 0.2, "zmax": 80.0, "n": 128})[0]
    try:
        Simulation(p, 1, lambda *a: None)
        print("    built (unexpected)")
    except ValueError as e:
        print("    refused:", str(e)[:200], "...")
    print("B1-1 (b) presets: the drawn plane z_max against the exact field (21 points) and against a window x4 wider")
    for name in ("double", "circle", "gauss", "square_big"):
        p = SCHEMA.resolve(name, None)[0]
        sim = Simulation(p, 1, lambda *a: None)
        n, k, dx, z = sim.n, sim.k, sim.dx, sim.zmax
        U = sim.win.plane
        peak = np.max(np.abs(U))
        pts = [(i, j) for i in (n // 2, n // 2 + n // 8, n // 2 + n // 4, n // 2 + 3 * n // 8, n - 1, n // 8, 0)
               for j in (n // 2, n // 2 + n // 4, n - 1)]
        if p["source"] in ("gauss", "circle"):
            pts = [(n // 2, n // 2)]
        err = max(abs(U[i, j] - A.reference(p, k, z, sim.x[i], sim.x[j])[0]) for i, j in pts) / peak
        ref = AS.propagate_field(sim.src, dx, k, z, pad=min(4 * sim.win.pad, 8192 // n), check=True,
                                 band_limit=sim.win.band_limit)
        I, Ir = np.abs(U) ** 2, np.abs(ref) ** 2
        pk = Ir.max()
        lin = np.max(np.abs(I - Ir)) / pk
        floor = max(1e-6, (3 * sim.win.est) ** 2)
        out = []
        for lo in (1e-6, floor):
            m = Ir > lo * pk
            dl = np.abs(np.log10(np.maximum(I[m], 1e-300) / Ir[m]))
            out.append(f"{np.mean(dl > 0.1):.1%} of pixels above {lo:.0e} off > 0.1 decade (max {dl.max():.2f})")
        print(f"    {name}: {sim.win.describe()}; exact: {err:.1e} of peak at {len(pts)} points; wider window: "
              f"linear {lin:.1e}; log view: " + "; ".join(out))


def b1_2():
    from lfphys.core.optics import angular_spectrum as AS
    from v08_wave_3d.viz import SCHEMA, Simulation
    from v08_wave_3d.engine import apparatus as A
    print("B1-2 grid error: the same world on the grid n against 2n (half the step, the same window), exact sources")
    for name, extra in (("double", {}), ("square", {"source": "square", "a": 2.0})):
        p = SCHEMA.resolve("double", {**extra, "n": 256})[0]
        sim = Simulation(p, 1, lambda *a: None)
        n, k, dx, zs = sim.n, sim.k, sim.dx, sim.zs
        far = zs >= sim.z_near
        sl = sim.vol[:, :, n // 2]
        fine = AS.propagate_slice(A.source(p, 2 * n), dx / 2, k, zs, axis=1, at=0.0, pad=sim.win.pad,
                                  band_limit=sim.win.band_limit)[:, ::2]
        d_far = np.max(np.abs(np.abs(sl[far]) ** 2 - np.abs(fine[far]) ** 2)) / np.max(np.abs(fine) ** 2)
        d_all = np.max(np.abs(np.abs(sl) ** 2 - np.abs(fine) ** 2)) / np.max(np.abs(fine) ** 2)
        print(f"    {name}: y = 0 slice, z >= z_near = {sim.z_near:.2f}: {d_far:.1e} of the peak intensity; "
              f"including z < z_near (the band-limited zone): {d_all:.1e}")


def b1_3():
    from lfphys.core.optics import angular_spectrum as AS
    from lfphys.core.optics import aperture_fields as AF
    print("B1-3 odd n = 65, pad 2: slice x = 0 against the Hankel integral (no FFT)")
    n, dx, k, w, z = 65, 1 / 6, 2 * math.pi, 1.2, 2.0
    x = (np.arange(n) - n // 2) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    s = AS.propagate_slice(np.exp(-(X ** 2 + Y ** 2) / w ** 2), dx, k, [z], axis=0, at=0.0, pad=2, check=True)[0]
    err = max(abs(s[j] - AF.gaussian_field(k, w, z, abs(x[j]))[0]) for j in range(n // 2 - 8, n // 2 + 9))
    print(f"    max error {err:.1e} (reviewer: 3.6e-2 before)")


def b1_6():
    from lfphys.core import backend as B
    from lfphys.core.optics import angular_spectrum as AS
    from v08_wave_3d.engine import apparatus as A
    from v08_wave_3d.viz import SCHEMA
    print("B1-6 fp32 against fp64, double slit, lambda 0.3, z 80 (k z = 1676), CPU")
    p = SCHEMA.resolve("double", {"lam": 0.3, "zmax": 80.0})[0]
    src, k, dx = A.source(p, 256), 2 * math.pi / 0.3, 0.3 / 4
    out = {}
    for prec in ("fp64", "fp32"):
        B.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu", "precision": prec}}})
        out[prec] = AS.propagate_field(src, dx, k, [80.0], pad=4)[0]
    B.configure(None)
    print(f"    max|U32 - U64| / max|U64| = {np.max(np.abs(out['fp32'] - out['fp64'])) / np.max(np.abs(out['fp64'])):.1e}"
          f" (bound 1e-5; reviewer: 1.2e-5 before)")


def b1_13():
    from v08_wave_3d.viz import SCHEMA, Simulation
    print("B1-13 the reviewer's Gaussian worlds (11_gauss_check_sweep.py) on the processed v08")
    for lam, w, z, n in [(0.5, 1.5, 30.0, 256), (0.3, 0.5, 80.0, 256), (1.5, 0.5, 80.0, 128), (0.3, 6.0, 80.0, 256),
                         (1.5, 6.0, 2.0, 256), (0.5, 6.0, 30.0, 128), (0.3, 6.0, 30.0, 128), (1.0, 3.0, 80.0, 256)]:
        p = SCHEMA.resolve(None, {"source": "gauss", "lam": lam, "w": w, "zmax": z, "n": n})[0]
        msgs = []
        try:
            sim = Simulation(p, 1, lambda m, b=None: msgs.append(m))
            sim.after_header()
        except ValueError as e:
            print(f"    lam={lam} w={w} z={z:g} n={n}: refused: {str(e)[:120]}")
            continue
        c = [m for m in msgs if m.get("type") == "check" and m["id"].startswith("exact_")][0]
        err = abs(c["value"] - c["ref"]) / abs(c["ref"])
        print(f"    lam={lam} w={w} z={z:g} n={n}: {sim.win.describe()}; |U| vs exact: rel {err:.1e}, "
              f"tolerance {c['tol']:.1e}, ok={c['ok']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Re-run the reviewer's inputs of review B1 on the processed code.")
    ap.add_argument("--only", nargs="*", help="subset: b1_1 b1_2 b1_3 b1_6 b1_13")
    a = ap.parse_args(argv)
    for f in (b1_1, b1_2, b1_3, b1_6, b1_13):
        if not a.only or f.__name__ in a.only:
            f()


if __name__ == "__main__":
    main()
