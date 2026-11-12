# Review of the B1 corrections (reviewer's script). propagate_plane against the engine's other routes and against
# an independent brute-force evaluation of the same sum (common_rev.brute_sum: point by point, no FFT, no recurrence,
# no modulo reading), for planes of many orientations. CPU, fp64 unless stated.
import argparse
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/lf/lfphys")
from common_rev import Tee, brute_sum, rel, rot_fn, sampled_grid, spectrum_grid, to_turned  # noqa: E402
from lfphys.core import backend  # noqa: E402
from lfphys.core import geometry as G  # noqa: E402
from lfphys.core.optics import angular_spectrum as AS  # noqa: E402
from lfphys.core.optics import aperture_fields as AF  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__)
ap.parse_args()
out = Tee("out/01_plane_vs_routes.txt")
backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})

LAM = 0.5
K = 2 * math.pi / LAM
DX = LAM / 4
RECTS = [(-2.75, -1.25, -3.0, 4.0), (1.25, 2.75, -4.0, 3.0)]  # an asymmetric double slit (no mirror symmetry)
FN = AF.rect_spectrum(RECTS)
ZNEAR = math.log(1e6) / math.sqrt((math.pi / DX) ** 2 - K * K)


def family_normal(alpha_deg, family):
    """Normals of planes with u = +x ('x'), -x, +y, -y and tilt alpha from the vertical (alpha = 90: longitudinal)."""
    a = math.radians(alpha_deg)
    sa, ca = math.sin(a), math.cos(a)
    return {"x": (0, -sa, ca), "y": (sa, 0, ca), "-x": (0, sa, ca), "-y": (-sa, 0, ca)}[family], sa, ca


def run_family(src, n, pad, family, alpha, band_limit, label):
    x = (np.arange(n) - n // 2) * DX
    nrm, sa, ca = family_normal(alpha, family)
    c0 = n // 2 + 3  # the plane passes through node (c0, c0) in (x, y)
    z0 = 4.0
    o = (x[c0], x[c0], z0)
    pl = G.Plane.horizontal(nrm, o)
    if ca > 1e-12:
        ts = np.arange(-20, 21) * (DX / ca)  # t steps that land on the nodes of the other transverse axis
    else:
        ts = np.linspace(-3.0, 3.0, 41)
    zt = z0 + ts * pl.v[2]
    s, U = AS.propagate_plane(src, DX, K, pl, (float(x[0] - x[c0]), float(x[-1] - x[c0])), ts, pad=pad, check=True,
                              band_limit=band_limit)
    vol = AS.propagate_field(src, DX, K, np.maximum(zt, 0.0), pad=pad, check=True, band_limit=band_limit)
    ref = np.full(U.shape, np.nan + 0j)
    for it in range(len(ts)):
        if zt[it] < 0:
            continue
        P = np.asarray(o)[None, :] + s[:, None] * np.asarray(pl.u)[None, :] + ts[it] * np.asarray(pl.v)[None, :]
        ii = np.rint(P[:, 0] / DX).astype(int) + n // 2
        jj = np.rint(P[:, 1] / DX).astype(int) + n // 2
        on = (np.abs(P[:, 0] - x[np.clip(ii, 0, n - 1)]) < 1e-9) & (np.abs(P[:, 1] - x[np.clip(jj, 0, n - 1)]) < 1e-9)
        ok = on & (ii >= 0) & (ii < n) & (jj >= 0) & (jj < n)
        ref[it, ok] = vol[it, ii[ok], jj[ok]]
    peak = np.nanmax(np.abs(ref))
    deep = zt >= ZNEAR
    near = ~deep & (zt >= 0)
    d_deep = rel(U[deep], ref[deep], peak)
    d_near = rel(U[near], ref[near], peak) if np.any(near) else float("nan")
    nan_ok = bool(np.all(np.isnan(U[zt < 0]))) if np.any(zt < 0) else True
    npts = int(np.isfinite(ref).sum())
    out(f"  {label:<18} u={family:>2} alpha {alpha:>5} bl={band_limit!s:<5} pad {pad}: {npts:5d} node pts; "
        f"max|plane - volume|/peak  z>=z_near {d_deep:.2e}  z<z_near {d_near:.2e}  NaN where z<0: {nan_ok}")
    return d_deep


out("(a)(b) propagate_plane vs the volume (propagate_field) at grid nodes, planes whose t steps land on nodes")
out(f"   lambda {LAM}, dx {DX}, z_near {ZNEAR:.3f}; source: asymmetric double slit by its exact spectrum")
for n in (128, 97):
    src = AS.Spectral((n, n), FN)
    for fam in ("x", "-x", "y", "-y"):
        for alpha in (90.0, 60.0, 30.0, 1.0, 0.01):
            for bl in (False, True):
                run_family(src, n, 2, fam, alpha, bl, f"Spectral n={n}")
# a sampled source (only u = +x accepted), odd n
for n in (97, 128):
    x = (np.arange(n) - n // 2) * DX
    X, Y = np.meshgrid(x, x, indexing="ij")
    U0 = np.exp(-((X - 0.4) ** 2 + (Y + 0.3) ** 2) / 1.2 ** 2) * np.exp(1j * 1.1 * X + 0.4j * Y)
    for alpha in (90.0, 45.0, 0.5):
        run_family(U0, n, 2, "x", alpha, False, f"sampled n={n}")

out("\n(c) planes at an arbitrary azimuth: same sum (brute force in the turned frame), the unturned lattice, exact")
n, pad = 128, 4
src = AS.Spectral((n, n), FN)
x = (np.arange(n) - n // 2) * DX
for phi_deg, tilt_deg in ((30.0, 40.0), (63.0, 75.0), (137.0, 20.0), (210.0, 89.0)):
    phi, th = math.radians(phi_deg), math.radians(tilt_deg)
    # normal with azimuth phi + 90 so that u = z x n points along azimuth phi (+-)
    nrm = (math.sin(th) * math.cos(phi + math.pi / 2), math.sin(th) * math.sin(phi + math.pi / 2), math.cos(th))
    pl = G.Plane.horizontal(nrm, (0.3, -0.2, 6.0))
    ts = np.linspace(-5.0, 5.0, 41)
    t0 = time.time()
    s, U = AS.propagate_plane(src, DX, K, pl, (-7.0, 7.0), ts, pad=pad, check=True)
    tt = time.time() - t0
    S, T = np.meshgrid(s, ts)
    P = np.asarray(pl.origin)[None, :] + S.ravel()[:, None] * np.asarray(pl.u)[None, :] + \
        T.ravel()[:, None] * np.asarray(pl.v)[None, :]
    good = P[:, 2] >= 0
    phu = math.atan2(pl.u[1], pl.u[0])
    gt = spectrum_grid(rot_fn(FN, phu), n, DX, K, pad)
    same = np.full(len(P), np.nan + 0j)
    same[good] = brute_sum(gt, to_turned(P[good], phu), DX)
    g0 = spectrum_grid(FN, n, DX, K, pad)
    unturned = np.full(len(P), np.nan + 0j)
    sel = np.where(good)[0][::7]
    unturned[sel] = brute_sum(g0, P[sel], DX)
    exact = np.full(len(P), np.nan + 0j)
    for i in sel[::4]:
        exact[i] = AF.rectangles_field(K, RECTS, float(P[i, 2]), float(P[i, 0]), float(P[i, 1]))[0] if P[i, 2] > 0 \
            else np.nan
    Uf = U.ravel()
    pk = np.nanmax(np.abs(same))
    out(f"  phi_u {math.degrees(phu):7.2f} deg, tilt {tilt_deg:5.1f}: plane vs same sum {rel(Uf, same, pk):.2e}; "
        f"vs unturned lattice {rel(Uf[sel], unturned[sel], pk):.2e}; vs exact (no FFT, {np.isfinite(exact).sum()} pts) "
        f"{rel(Uf[np.isfinite(exact)], exact[np.isfinite(exact)], pk):.2e}; {tt:.2f} s")

out("\n(d) origin at a corner of the box, s range longer than half the window period (read modulo the period)")
for pad in (2, 1):
    m = 2 ** math.ceil(math.log2(n * pad)) if pad > 1 else n
    period = m * DX
    o = (float(x[-1]), float(x[-1]), 5.0)
    pl = G.Plane.horizontal((0.0, -1.0, 0.0), o)  # u = +x: s from -period+dx to 0
    s, U = AS.propagate_plane(src, DX, K, pl, (-(period - DX) + 1e-9, 0.0), np.linspace(0, 3, 4), pad=pad,
                              check=True)
    S, T = np.meshgrid(s, np.linspace(0, 3, 4))
    P = np.asarray(o)[None, :] + S.ravel()[:, None] * np.asarray(pl.u)[None, :] + T.ravel()[:, None] * \
        np.asarray(pl.v)[None, :]
    ref = brute_sum(spectrum_grid(FN, n, DX, K, pad), P, DX)
    out(f"  pad {pad}: window period {period:.2f}, s from {s[0]:.2f} to {s[-1]:.2f} ({len(s)} pts): "
        f"max|plane - brute|/peak {rel(U.ravel(), ref):.2e}")
    try:
        AS.propagate_plane(src, DX, K, pl, (-(period + 5 * DX), 0.0), [0.0], pad=pad, check=True)
        out("  s range longer than the period: accepted")
    except ValueError as e:
        out(f"  s range longer than the period: refused ({e})")

out("\n(e) planes partly before z = 0, nearly transverse planes; brute force at every point")
for nrm, o, lab in (((0.0, -0.6, -0.8), (0.0, 0.0, 0.5), "tilted, half before the source"),
                    ((0.2, -0.1, 0.97), (0.5, 0.0, 2.0), "nearly transverse 14 deg, turned"),
                    ((1e-4, -1e-4, 1.0), (0.0, 0.0, 3.0), "normal 8e-3 deg from z, turned"),
                    ((0.0, 0.0, -1.0), (0.0, 0.0, 3.0), "transverse, normal -z")):
    pl = G.Plane.horizontal(nrm, o)
    ts = np.linspace(-4.0, 4.0, 33)
    s, U = AS.propagate_plane(src, DX, K, pl, (-4.0, 4.0), ts, pad=2, check=True)
    S, T = np.meshgrid(s, ts)
    P = np.asarray(o)[None, :] + S.ravel()[:, None] * np.asarray(pl.u)[None, :] + T.ravel()[:, None] * \
        np.asarray(pl.v)[None, :]
    phu = math.atan2(pl.u[1], pl.u[0])
    good = P[:, 2] >= 0
    ref = np.full(len(P), np.nan + 0j)
    ref[good] = brute_sum(spectrum_grid(rot_fn(FN, phu), n, DX, K, 2), to_turned(P[good], phu), DX)
    Uf = U.ravel()
    out(f"  {lab:<38} u = ({pl.u[0]:+.3f}, {pl.u[1]:+.3f}), v_z {pl.v[2]:.2e}: max|plane - brute|/peak "
        f"{rel(Uf[good], ref[good]):.2e}; NaN exactly where z < 0: {bool(np.all(np.isnan(Uf[~good])) and np.all(np.isfinite(Uf[good])))}")

out("\n(f) fp32 drawing of a turned, tilted plane against fp64")
pl = G.Plane.horizontal((0.4, 0.3, 0.86), (0.3, -0.4, 4.0))
ts = np.linspace(-4.0, 4.0, 64)
backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu", "precision": "fp32"}}})
s, U32 = AS.propagate_plane(src, DX, K, pl, (-6.0, 6.0), ts, pad=4)
backend.configure({"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
s, U64 = AS.propagate_plane(src, DX, K, pl, (-6.0, 6.0), ts, pad=4, check=True)
out(f"  dtype {U32.dtype}; max|fp32 - fp64|/peak {rel(U32, U64):.2e} (kernel bound 1e-5)")

out("\n(g) the recurrence: long uniform t ranges (exp advanced step by step) against brute force")
for nt, trange, nrm in ((2000, (0.0, 60.0), (0.0, -1.0, 0.0)), (4000, (-1.0, 79.0), (0.3, -0.5, 0.81)),
                        (600, (0.0, 0.6), (0.0, -1.0, 0.0))):
    pl = G.Plane.horizontal(nrm, (0.0, 0.0, 0.0) if trange[0] >= 0 else (0.0, 0.0, 1.0))
    ts = np.linspace(*trange, nt)
    t0 = time.time()
    s, U = AS.propagate_plane(src, DX, K, pl, (-4.0, 4.0), ts, pad=2, check=True)
    tt = time.time() - t0
    rows = np.arange(0, nt, max(1, nt // 40))
    S, T = np.meshgrid(s, ts[rows])
    P = np.asarray(pl.origin)[None, :] + S.ravel()[:, None] * np.asarray(pl.u)[None, :] + T.ravel()[:, None] * \
        np.asarray(pl.v)[None, :]
    phu = math.atan2(pl.u[1], pl.u[0])
    good = P[:, 2] >= 0
    ref = np.full(len(P), np.nan + 0j)
    ref[good] = brute_sum(spectrum_grid(rot_fn(FN, phu), n, DX, K, 2), to_turned(P[good], phu), DX)
    # the same plane with t jittered by ~1e-13 (no recurrence: exp at every row)
    tj = ts + 1e-13 * np.sin(np.arange(nt)) * max(1.0, abs(trange[1]))
    s2, U2 = AS.propagate_plane(src, DX, K, pl, (-4.0, 4.0), tj, pad=2, check=True)
    out(f"  nt {nt}, t in {trange}, v_z {pl.v[2]:.2f}: recurrence vs brute {rel(U[rows].ravel()[good], ref[good]):.2e}; "
        f"vs per-row exp {rel(U, U2):.2e}; {tt:.1f} s")
out("done")
