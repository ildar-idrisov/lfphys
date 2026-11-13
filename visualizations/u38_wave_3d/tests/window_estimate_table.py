# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The calibration of v08's window estimate (engine/apparatus.py, SAFETY), over depth (review C1): for worlds across
the schema's range, both sums and pads 2-16, the true error of the field against the exact field (no FFTs) at points
of the plane z_max and of the central planes y = 0, x = 0 at the measured depths, next to the estimate's difference
max|U_p - U_2p| over the same planes, each against its own plane's peak. Prints a Markdown table (README, "Accuracy").

Run in the image, from engine/ (GPU 0 makes it take a minute):
  docker run --rm --gpus '"device=0"' -v "$PWD":/lf -w /lf/visualizations \
    -e PYTHONPATH=/lf/lfphys:/lf/visualizations:/lf/visualizations/server lfphys-viz \
    python3 v08_wave_3d/tests/window_estimate_table.py
"""

import argparse
import math

import numpy as np

WORLDS = {
    "double (preset)": dict(source="double", lam=0.5, a=0.75, d=4.0, L=8.0, zmax=30.0, n=256),
    "circle (preset)": dict(source="circle", lam=0.5, a=3.0, zmax=40.0, n=256),
    "circle a 5, λ 0.8": dict(source="circle", lam=0.8, a=5.0, zmax=40.0, n=256),
    "square_big (n 512, z 15)": dict(source="square", lam=0.5, a=2.0, zmax=15.0, n=512),
    "square a 3": dict(source="square", lam=0.5, a=3.0, zmax=30.0, n=256),
    "double, z 80": dict(source="double", lam=0.5, a=0.75, d=4.0, L=8.0, zmax=80.0, n=256),
    "slit, a 0.2, λ 0.3, z 80": dict(source="slit", lam=0.3, a=0.2, L=8.0, zmax=80.0, n=256),
    "slit a 3, z 40": dict(source="slit", lam=0.5, a=3.0, L=12.0, zmax=40.0, n=256),
    "gauss w 0.5, λ 0.5, z 30": dict(source="gauss", lam=0.5, w=0.5, zmax=30.0, n=256),
    "gauss w 0.5, λ 0.5, z 40": dict(source="gauss", lam=0.5, w=0.5, zmax=40.0, n=256),
    "circle a 1, z 20": dict(source="circle", lam=0.5, a=1.0, zmax=20.0, n=256),
    "square a 1, z 25": dict(source="square", lam=0.5, a=1.0, zmax=25.0, n=256),
}


def truth_points(p, n, x, zs):
    """Points (plane, index...) where the exact field is known: z_max grid (rectangles: 7 x 3; others: the axis) and
    the central planes at every depth (rectangles, gauss: 7 lateral nodes on each; circle: the axis)."""
    idx = [n // 2, n // 2 + n // 8, n // 2 + n // 4, n // 2 + 3 * n // 8, n - 1, n // 8, 0]
    on_axis_only = p["source"] == "circle"
    pts = []
    for i in ([n // 2] if on_axis_only else idx):
        for j in ([n // 2] if on_axis_only else (n // 2, n // 2 + n // 4, n - 1)):
            pts.append(("plane", None, i, j))
    for iz in range(len(zs)):
        for i in ([n // 2] if on_axis_only else idx):
            pts.append(("y0", iz, i, None))  # y = 0 slice: field across x at depth zs[iz]
            pts.append(("x0", iz, i, None))  # x = 0 slice: field across y
    return pts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--max-window", type=int, default=8192, help="largest padded window computed (points per axis)")
    a = ap.parse_args(argv)
    from v08_wave_3d.engine import apparatus as A
    print("| world | sum | pad: true error / max|U_p − U_2p| over z_max and the central planes at depth | max ratio |")
    print("|---|---|---|---|")
    worst = 0.0
    for name, p in WORLDS.items():
        p = {"a": 1.0, "d": 4.0, "L": 8.0, "w": 1.5, **p}
        lam, n = p["lam"], p["n"]
        k, dx = 2 * math.pi / lam, lam / 4 if n <= 256 else lam / 8
        x = (np.arange(n) - n // 2) * dx
        src = A.source(p, n)
        zs = A.check_depths(dx, k, p["zmax"])
        pts = truth_points(p, n, x, zs)
        ref = []
        for kind, iz, i, j in pts:
            if kind == "plane":
                ref.append(A.reference(p, k, p["zmax"], x[i], x[j])[0])
            elif kind == "y0":
                ref.append(A.reference(p, k, zs[iz], x[i], 0.0)[0])
            else:
                ref.append(A.reference(p, k, zs[iz], 0.0, x[i])[0])
        for bl in (False, True):
            F = {pad: A._measured(src, dx, k, p["zmax"], zs, pad, bl) for pad in (2, 4, 8, 16, 32)
                 if n * pad <= a.max_window}
            cells, ratio = [], 0.0
            for pad in sorted(F):
                if 2 * pad not in F:
                    continue
                plane, sy, sx = F[pad]
                peaks = {"plane": np.max(np.abs(plane)), "y0": np.max(np.abs(sy)), "x0": np.max(np.abs(sx))}
                err = 0.0  # each point against its own plane's peak, as the estimate measures it
                for (kind, iz, i, j), r in zip(pts, ref):
                    v = plane[i, j] if kind == "plane" else (sy[iz, i] if kind == "y0" else sx[iz, i])
                    err = max(err, abs(v - r) / peaks[kind])
                d = A._diff(F[pad], F[2 * pad])[0]
                ratio = max(ratio, err / d)
                cells.append(f"×{pad}: {err:.1e} / {d:.1e}")
            worst = max(worst, ratio)
            print(f"| {name} | {'band-limited' if bl else 'plain'} | {'; '.join(cells)} | {ratio:.2f} |", flush=True)
    print(f"\nlargest ratio true error / max|U_p - U_2p|: {worst:.2f} (SAFETY = {A.SAFETY})")


if __name__ == "__main__":
    main()
