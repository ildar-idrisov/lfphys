# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u38 apparatus: the source on z = 0 by its exact spectrum, the window chosen by measurement, the exact references
for the checks, the zone next to the aperture. No physics of its own: the spectra and the exact fields come from
``lfphys.core.optics.aperture_fields``, the propagation from ``lfphys.core.optics.angular_spectrum``.

* **Source.** The aperture (or the Gaussian field) enters by its exact Fourier transform at the grid's frequencies, not
  by samples: sharp edges carry no staircase (area-weighted samples on the grid lambda/4 were off by ~1e-2 of the peak,
  review B1-2). Left out are the components beyond the grid's band, |q_i| >= pi/d: with d <= lambda/4 they are
  evanescent, and at depth z below exp(-sqrt((pi/d)^2 - k^2) z) of their size on z = 0. That factor is 1e-6 at
  ``near_zone``: closer to the aperture the drawn field is that of the aperture band-limited by the grid (ringing
  next to the edges on z = 0), and it is marked.
* **Window** (review B1-1). The angular spectrum on a window of period P gives the field of a periodic array of copies
  of the source; light leaving at wide angles reaches the neighbouring copies. The run measures this on the deepest
  plane z_max: the plane with the window padded p times against 2p, for the plain sum and the band-limited one
  (``angular_spectrum``, ``band_limit``), and on the two central longitudinal planes y = 0 and x = 0 at NZ_CHECK
  depths (review C1: the band-limited sum removes the copies' error on z_max but not at mid-depth); the estimate is
  SAFETY * max|U_p - U_2p| / max|U| for each of these planes against its own peak (what a window or the target shows),
  the largest of them; in field units it is the tolerance of the checks at points. SAFETY = 1.5
EST_FLOOR = 1e-12  # the estimate never below the rounding of the fp64 sums (~1e-13 of the peak) is calibrated against the exact field
  (tests/window_estimate_table.py: points of z_max and of the central planes over depth; README). The smallest window, and of the two sums the one, whose estimate is within TOL is drawn (the plain
  sum when both are). The largest window ever computed is
  M_MAX points per axis (the comparison at 2p; a 4096^2 complex128 array is 268 MB, a call needs about seven, which
  fits the container's 6 GB on the CPU too), so what is drawn has at most M_MAX/2; a world that needs more is refused
  with the reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from lfphys.core import geometry as G
from lfphys.core.optics import angular_spectrum as AS
from lfphys.core.optics import aperture_fields as AF
from lfphys.i18n import T

TOL = 2e-3  # window error allowed in the drawing, fraction of the peak amplitude: below one of 256 colour levels
SAFETY = 1.5
EST_FLOOR = 1e-12  # the estimate never below the rounding of the fp64 sums (~1e-13 of the peak)
M_MAX = 4096  # the largest padded window computed, points per axis
NEAR_LEVEL = 1e-6


def rects(p) -> list | None:
    """The aperture as disjoint unit rectangles (xa, xb, ya, yb), micrometres; None for the circle and the beam."""
    src = p["source"]
    a = float(p["a"])
    if src == "square":
        return [(-a, a, -a, a)]
    if src == "slit":
        h = float(p["L"]) / 2
        return [(-a, a, -h, h)]
    if src == "double":
        c, h = float(p["d"]) / 2, float(p["L"]) / 2
        return [(-c - a, -c + a, -h, h), (c - a, c + a, -h, h)]
    return None


def source(p, n: int, azimuth_deg: float = 0.0) -> AS.Spectral:
    """The field on z = 0 on an n x n grid, by its exact spectrum; turned so that the plane through the axis at
    azimuth phi becomes the plane y = 0 (``azimuth_deg`` = phi)."""
    src = p["source"]
    if src == "gauss":
        fn = AF.gaussian_spectrum(float(p["w"]))
    elif src == "circle":
        fn = AF.disc_spectrum(float(p["a"]))
    else:
        fn = AF.rect_spectrum(rects(p))
    if azimuth_deg:
        fn = AF.rotated(fn, -math.radians(azimuth_deg))
    return AS.Spectral((n, n), fn)


def profile(p, n: int) -> AS.Spectral:
    """The reduced 2-D model of a slit or a double slit: the slit taken as infinitely long, its profile across x."""
    a = float(p["a"])
    if p["source"] == "slit":
        iv = [(-a, a)]
    else:
        c = float(p["d"]) / 2
        iv = [(-c - a, -c + a), (c - a, c + a)]
    return AS.Spectral((n,), AF.interval_spectrum(iv))


def ref_points(p, x) -> list[tuple[int, int]]:
    """Grid nodes (i, j) on the plane z_max where the exact field is known: the axis for the beam and the circle; for
    rectangle apertures also the slit's centre line (or half the half-width) and a point near the window's edge."""
    n = len(x)
    c = n // 2
    if p["source"] in ("gauss", "circle"):
        return [(c, c)]
    xc = float(p["d"]) / 2 if p["source"] == "double" else float(p["a"]) / 2
    i = min(n - 1, c + int(round(xc / (x[1] - x[0]))))
    return [(c, c), (i, c), (n - 1 - n // 16, c + n // 4)]


def reference(p, k: float, z: float, x0: float, y0: float) -> tuple[complex, float]:
    """The exact field and its error estimate at (x0, y0, z), without FFTs."""
    src = p["source"]
    if src == "gauss":
        return AF.gaussian_field(k, float(p["w"]), z, math.hypot(x0, y0))
    if src == "circle":
        if x0 or y0:
            raise ValueError("the circle's closed form is on its axis only")
        return AF.circle_on_axis(k, float(p["a"]), z), 0.0
    return AF.rectangles_field(k, rects(p), z, x0, y0)


def reference_current(p, k: float, z: float, x0: float, y0: float):
    """The exact energy current j = Im(U* grad U)/k at (x0, y0, z), without FFTs (review C4): the Gaussian and the
    circle (on its axis) from closed-form derivatives; rectangles from five-point differences of the exact field
    (step 1e-3 um: truncation ~h^4 k^5 / 30 < 1e-8, rounding ~2e-9). Returns (j, U, |grad U|/k, error estimate)."""
    src = p["source"]
    if src == "gauss":
        w, r = float(p["w"]), math.hypot(x0, y0)
        U, e0 = AF.gaussian_field(k, w, z, r)
        Uz, e1 = AF.gaussian_field(k, w, z, r, deriv="z")
        Ur, e2 = AF.gaussian_field(k, w, z, r, deriv="r") if r else (0.0, 0.0)
        grad = np.array([Ur * x0 / r if r else 0.0, Ur * y0 / r if r else 0.0, Uz], complex)
        err = (e0 + e1 + e2) / k * 3
    elif src == "circle":
        if x0 or y0:
            raise ValueError("the circle's closed form is on its axis only")
        a = float(p["a"])
        R = math.hypot(z, a)
        U = np.exp(1j * k * z) - z / R * np.exp(1j * k * R)
        dUz = 1j * k * np.exp(1j * k * z) - (np.exp(1j * k * R) / R
                                              + z * (z / R) * np.exp(1j * k * R) * (1j * k / R - 1 / R ** 2))
        grad = np.array([0.0, 0.0, dUz], complex)
        err = 1e-12
    else:
        h = 1e-3
        f = lambda dx_, dy_, dz_: AF.rectangles_field(k, rects(p), z + dz_, x0 + dx_, y0 + dy_)[0]  # noqa: E731
        U = f(0, 0, 0)
        grad = []
        for e in ((h, 0, 0), (0, h, 0), (0, 0, h)):
            m2 = f(*(-2 * c for c in e)); m1 = f(*(-c for c in e)); p1 = f(*e); p2 = f(*(2 * c for c in e))
            grad.append((m2 - 8 * m1 + 8 * p1 - p2) / (12 * h))
        grad = np.array(grad, complex)
        err = 1e-8
    j = np.imag(np.conj(U) * grad) / k
    return j, complex(U), float(np.linalg.norm(grad)) / k, err


def near_zone(dx: float, k: float, level: float = NEAR_LEVEL) -> float:
    """Depth below which the components beyond the grid's band (|q_i| >= pi/dx, evanescent) are not yet down to
    ``level`` of their size on z = 0."""
    kappa = math.sqrt((math.pi / dx) ** 2 - k * k)
    return math.log(1.0 / level) / kappa


@dataclass
class Window:
    pad: int
    band_limit: bool
    est: float  # estimated error, fraction of the peak amplitude of each measured plane (the largest of them)
    rows: list = field(default_factory=list)  # (pad, band_limit, relative difference) as measured
    plane: np.ndarray | None = None  # fp64 field on z_max with the chosen window (what the drawing is, in fp64)
    abs_err: float = 0.0  # estimated error in field units (the tolerance of checks at points anywhere)

    def describe(self) -> T:
        how = T("band-limited sum") if self.band_limit else T("plain sum")
        return T("window ×{pad:d}, {how}; error estimate {est:.1e} of the peak", pad=int(self.pad), how=how,
                 est=float(self.est))


class WindowError(ValueError):
    """No window within the tolerance: ``text`` what is wrong, ``hint`` what to change (translatable texts)."""

    def __init__(self, text: T, hint: T):
        super().__init__(str(text))
        self.text, self.hint = text, hint


NZ_CHECK = 12  # depths of the window measurement on the two central longitudinal planes


def check_depths(dx: float, k: float, zmax: float) -> np.ndarray:
    """The depths where the window is measured: beyond the zone next to the aperture, up to z_max (review C1: the
    band-limited sum's error peaks at mid-depth, not on z_max)."""
    z0 = min(zmax, max(2 * near_zone(dx, k), zmax / NZ_CHECK))
    return np.linspace(z0, zmax, NZ_CHECK)


def _measured(src, dx, k, zmax, zs, pad, bl):
    """What the window estimate compares: the plane z_max and the two central longitudinal planes y = 0, x = 0 at
    the depths ``zs`` (fp64); for a 1-D source (the reduced 2-D model) its line at z_max and at the depths."""
    if src.ndim == 1:
        return (AS.propagate_field(src, dx, k, zmax, pad=pad, check=True, band_limit=bl),
                AS.propagate_field(src, dx, k, zs, pad=pad, check=True, band_limit=bl))
    return (AS.propagate_field(src, dx, k, zmax, pad=pad, check=True, band_limit=bl),
            AS.propagate_slice(src, dx, k, zs, axis=1, at=0.0, pad=pad, check=True, band_limit=bl),
            AS.propagate_slice(src, dx, k, zs, axis=0, at=0.0, pad=pad, check=True, band_limit=bl))


def _diff(a, b):
    """(relative, absolute) difference of two measurements: each plane against its own peak (what a window or the
    target shows; a deep plane where the beam has spread is dim, so a global peak would hide its error), and in
    field units."""
    rel = max(float(np.max(np.abs(x - y))) / max(float(np.max(np.abs(y))), 1e-300) for x, y in zip(a, b))
    return rel, max(float(np.max(np.abs(x - y))) for x, y in zip(a, b))


def choose_window(src: AS.Spectral, dx: float, k: float, zmax: float, tol: float = TOL,
                  m_max: int = M_MAX) -> Window:
    """The smallest window (pad 2, 4, 8, ...) and the sum (plain or band-limited) whose estimate is within ``tol``:
    SAFETY * max|U_p - U_2p| / max|U| over the plane z_max and the planes y = 0 and x = 0 at NZ_CHECK depths (review
    C1); WindowError (a ValueError) with the measurements when none is, with the comparison window up to ``m_max`` points per axis."""
    n = max(src.shape)
    zs = check_depths(dx, k, zmax)
    prev = {bl: _measured(src, dx, k, zmax, zs, 2, bl) for bl in (False, True)}
    rows = []
    best = None
    p = 2
    while n * 2 * p <= m_max:
        passing = {}
        for bl in (False, True):
            nxt = _measured(src, dx, k, zmax, zs, 2 * p, bl)
            d, da = _diff(prev[bl], nxt)
            rows.append((p, bl, d))
            w = Window(p, bl, max(SAFETY * d, EST_FLOOR), rows, prev[bl][0], max(SAFETY * da, EST_FLOOR))
            if best is None or w.est < best.est:
                best = w
            if w.est <= tol:
                passing[bl] = w
            prev[bl] = nxt
        if passing:
            return passing.get(False) or passing[True]
        p *= 2
    raise WindowError(
        T("the computation window is too small for the depth z_max = {zmax} µm: light that left at large angles comes "
          "back as periodic copies of the source; the best reachable with a window of up to {m:d} points per axis is "
          "{best}, and at most {tol:.0e} is needed", zmax=float(zmax), m=int(m_max // 2), best=best.describe(),
          tol=float(tol)),
        T("reduce z_max or take a wider source (light then leaves at smaller angles)"))


# --- slices on planes of any orientation (owner, 2026-10-27) ---------------------------------------------------------
NT = 256  # samples along the plane's v axis; along u the grid step dx


# the cut of a plane by the box, its points, the box test: shared by every 3-D world (lfphys.core.geometry)
plane_box = G.plane_cut
slice_points = G.plane_points
inside_box = G.inside_box


def window_for_plane(src, dx, k, zmax, pl, base, tol=TOL, m_max=M_MAX):
    """The window for a slice whose plane turns the source (its u not along x or y): the copies' lattice of the turned
    source is not that of the source as placed, so the window is measured again for the turned source, as
    ``choose_window`` measures it (z_max and the central planes over depth), starting from the base window's pad and
    sum; the pad doubles while the estimate exceeds ``tol``. Returns a Window (the base one when the plane does not
    turn the source)."""
    phi = math.atan2(pl.u[1], pl.u[0])
    q = math.degrees(phi) % 90.0
    if min(q, 90.0 - q) < 1e-9:  # turns by multiples of 90 degrees map the square lattice onto itself
        return base
    turned = AS.Spectral(src.shape, AF.rotated(src.fn, -phi))
    n = max(src.shape)
    zs = check_depths(dx, k, zmax)
    p = base.pad
    F = _measured(turned, dx, k, zmax, zs, p, base.band_limit)
    rows, last_abs = [], 0.0
    while True:
        if n * 2 * p > m_max:
            return Window(p, base.band_limit, rows[-1][2] * SAFETY if rows else float("inf"), rows, F[0],
                          last_abs * SAFETY if rows else float("inf"))
        F2 = _measured(turned, dx, k, zmax, zs, 2 * p, base.band_limit)
        d, last_abs = _diff(F, F2)
        rows.append((p, base.band_limit, d))
        if SAFETY * d <= tol:
            return Window(p, base.band_limit, max(SAFETY * d, EST_FLOOR), rows, F[0], max(SAFETY * last_abs, EST_FLOOR))
        p, F = 2 * p, F2


def compute_slice(src, dx, k, pl, s_rng, t_rng, window, box, nt=NT, check=False):
    """The exact slice (as the volume would give it on the same grid): s on the grid step, ``nt`` values of t; points
    outside the box are NaN. ``check=True``: as a reference of a check (fp64). Returns (s, t, U[nt, ns])."""
    t = np.linspace(t_rng[0], t_rng[1], nt)
    s, U = AS.propagate_plane(src, dx, k, pl, s_rng, t, pad=window.pad, band_limit=window.band_limit, check=check)
    U = np.asarray(U, np.complex128)
    U[~inside_box(slice_points(pl, s, t), box)] = np.nan
    return s, t, U


def reduced_slice(p, n, dx, k, pl, s_rng, t_rng, box, nt=NT):
    """The reduced 2-D model (the slit infinitely long) on a plane y = c: its 1-D field across x at the plane's
    depths. Only for planes with the normal along y (u = +/-x, v = +z)."""
    t = np.linspace(t_rng[0], t_rng[1], nt)
    o, u = np.asarray(pl.origin), np.asarray(pl.u)
    js = np.arange(int(np.ceil(s_rng[0] / dx - 1e-9)), int(np.floor(s_rng[1] / dx + 1e-9)) + 1)
    s = js * dx
    prof = profile(p, n)
    shifted = AS.Spectral(prof.shape, lambda q: prof.fn(q) * np.exp(1j * q * o[0]))  # field at x - o_x
    z = o[2] + t * pl.v[2]
    w1 = choose_window(prof, dx, k, max(float(z.max()), 1e-9), m_max=1 << 20)
    m = n * w1.pad
    zz = np.maximum(z, 0.0)
    line = AS.propagate(AS.Spectral((m,), shifted.fn), dx, k, zz, pad=1, band_limit=w1.band_limit)  # (nt, m)
    idx = (np.rint(u[0] * s / dx).astype(int) + m // 2) % m  # x - o_x = s u_x
    U = np.asarray(line[:, idx], np.complex128)
    U[z < 0] = np.nan
    U[~inside_box(slice_points(pl, s, t), box)] = np.nan
    return s, t, U


def verify_slice(p, k, pl, s, t, U, z_near, tol_abs, max_points=3):
    """The slice at up to three of its points against the exact field without FFTs (where the source has one there):
    the brightest point and two more with at least 5 % of its intensity, deeper than z_near. Returns a dict."""
    I = np.where(np.isfinite(U), np.abs(U) ** 2, -1.0)
    P = slice_points(pl, s, t)
    ok_z = P[..., 2] >= z_near
    cand = np.argwhere((I >= 0.05 * I.max()) & ok_z)
    if p["source"] == "circle":
        cand = cand[np.hypot(P[cand[:, 0], cand[:, 1], 0], P[cand[:, 0], cand[:, 1], 1]) < 1e-9]
    if not len(cand):
        return {"points": 0, "note": T("this source has no exact value at the points of this plane")}
    order = np.argsort(-I[cand[:, 0], cand[:, 1]])
    picks = [cand[order[0]]] + ([cand[order[len(order) // 3]], cand[order[2 * len(order) // 3]]] if len(order) > 2 else [])
    worst, rel = 0.0, 0.0
    for i, j in picks[:max_points]:
        x, y, z = P[i, j]
        ref, err = reference(p, k, float(z), float(x), float(y))
        d = abs(U[i, j] - ref)
        worst = max(worst, d - err)
        rel = max(rel, d / max(abs(ref), 1e-300))
    return {"points": len(picks[:max_points]), "max_err": float(worst), "tol": float(tol_abs),
            "ok": bool(worst <= tol_abs), "max_rel": float(rel)}


def preview_volume(vol, n):
    """|U|^2 of the volume, normalised to its peak, 2 x 2-averaged across for n > 128: the 3-D cloud of the view
    (a preview; exact values are in the slices). Shape (nz, nx', ny'), float32."""
    I = np.abs(vol) ** 2
    if n > 128:
        f = n // 128
        I = I.reshape(I.shape[0], n // f, f, n // f, f).mean(axis=(2, 4))
    return (I / max(float(I.max()), 1e-300)).astype(np.float32)


def flux_glyphs(src, dx, k, zs, x, window, grid=16):
    """The energy current on ``grid`` x ``grid`` points of the planes ``zs`` (positions and vectors, float32), the
    power through each plane (whole window) and the full current on the last plane (for the checks)."""
    j, P = AS.propagate_current(src, dx, k, zs, pad=window.pad, band_limit=window.band_limit)
    n = len(x)
    step = max(1, n // grid)
    idx = np.arange(step // 2, n, step)
    X, Y = np.meshgrid(x[idx], x[idx], indexing="ij")
    pos, vec = [], []
    for iz, z in enumerate(zs):
        jj = j[iz][:, idx][:, :, idx]
        pos.append(np.stack([X, Y, np.full_like(X, z)], axis=-1).reshape(-1, 3))
        vec.append(np.moveaxis(jj, 0, -1).reshape(-1, 3))
    return np.concatenate(pos).astype(np.float32), np.concatenate(vec).astype(np.float32), P, j[-1]
