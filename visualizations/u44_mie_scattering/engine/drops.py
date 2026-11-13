# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u44's apparatus over lfphys: the drop's index at a wavelength, the wavelengths of sunlight and their weights, the
colour of the accumulated spectra (lfphys.tools.colour, a display tool), the polar surface and the ray fans as drawable
geometry. The physics (the Mie and Debye series, the size average, Planck's law, water's index) is the engine's."""

from __future__ import annotations

import math

import numpy as np

from lfphys.core import data as D
from lfphys.core.optics import mie, radiation
from lfphys.theories.approx import rainbow as RB
from lfphys.tools import colour as CO

LAM_MIN, LAM_MAX = 380.0, 760.0  # nm: the visible band summed for white light (the CMFs fit is used 360-830 nm)


def index(params, lam_nm):
    """The drop's index relative to the medium at a vacuum wavelength (nm): water by IAPWS R9-97 at t (0.1 MPa), or
    the given n + i kappa (no dispersion), divided by the medium's index."""
    nm = float(params["n_medium"])
    if params["index"] == "water":
        n = complex(float(D.water_index(lam_nm, float(params["t_c"]))))
    else:
        n = complex(float(params["n_re"]), float(params["n_im"]))
    return n / nm


def wavelengths(n: int):
    """Sample wavelengths (nm, vacuum) of white light and their trapezoid weights (nm)."""
    lam = np.linspace(LAM_MIN, LAM_MAX, int(n))
    w = np.full(len(lam), lam[1] - lam[0])
    w[0] = w[-1] = 0.5 * (lam[1] - lam[0])
    return lam, w


def sun(lam_nm):
    """Relative spectral radiance of sunlight taken as a black body at the IAU nominal effective temperature (a stated
    approximation of the solar spectrum: no absorption lines, no atmosphere), per nm, normalised to 1 at 550 nm."""
    T = D.SUN_TEFF_NOMINAL_K
    return radiation.planck_lambda(np.asarray(lam_nm) * 1e-9, T) / radiation.planck_lambda(550e-9, T)


def cmf(lam_nm):
    """CIE 1931 colour matching functions (x, y, z) at a wavelength (tools.colour: Wyman, Sloan & Shirley 2013)."""
    return CO.cmfs(np.atleast_1d(lam_nm))[0]


def strip_rgb(XYZ, Y_ref=None):
    """sRGB (uint8, n x 3) of the accumulated XYZ along the angles: exposure so that the brightest angle (or Y_ref)
    gives Y = 2 before the display compression (tools.colour.to_display)."""
    Y = XYZ[:, 1]
    top = float(Y_ref) if Y_ref else float(np.max(Y)) if Y.size else 0.0
    exposure = 2.0 / top if top > 0 else 1.0
    return CO.to_display(XYZ, exposure)


def polar_mesh(theta_deg, I_parallel, I_perp, mode: str, decades: float = 5.0, n_phi: int = 72):
    """Vertices, triangles and colours of the scattered intensity as a polar surface around the drop (radius 1): the
    direction (theta, phi) at distance 1.15 + 1.25 (1 + log10(I/I_max)/decades) (clipped at 1.15); the intensity for
    the incident wave along +z polarised along x ("x"), y ("y") or unpolarised ("u") is the engine's
    (mie.intensity_polarised: I = |S2|^2 cos^2 phi + |S1|^2 sin^2 phi for "x"; review B8-mie, M12: it was computed
    here). I_parallel = |S2|^2, I_perp = |S1|^2 (bin means from the run)."""
    th = np.radians(np.asarray(theta_deg, float))
    ph = np.linspace(0.0, 2 * math.pi, n_phi, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing="ij")
    i2, i1 = np.asarray(I_parallel)[:, None], np.asarray(I_perp)[:, None]
    I = mie.intensity_polarised(i1, i2, P, mode if mode in ("x", "y") else "u")
    top = float(np.max(I)) if I.size else 1.0
    lg = np.log10(np.maximum(I / top, 1e-300))
    f = np.clip(1.0 + lg / decades, 0.0, 1.0)
    R = 1.15 + 1.25 * f
    pos = np.stack([R * np.sin(T) * np.cos(P), R * np.sin(T) * np.sin(P), R * np.cos(T)], -1).reshape(-1, 3)
    nt, npf = T.shape
    idx = []
    for i in range(nt - 1):
        for j in range(npf):
            a, b = i * npf + j, i * npf + (j + 1) % npf
            idx += [a, a + npf, b, b, a + npf, b + npf]
    c = f.reshape(-1)
    rgb = np.stack([60 + 195 * c, 90 + 140 * c ** 1.5, 200 - 120 * c], -1).clip(0, 255).astype(np.uint8)
    return pos.astype(np.float32), np.array(idx, np.uint32), rgb


RAY_COLOURS = {0: (0.75, 0.75, 0.8), 1: (0.45, 0.8, 1.0), 2: (1.0, 0.82, 0.3), 3: (0.95, 0.45, 0.9)}


def ray_fans(m: float, orders=(0, 1, 2, 3), n_rays: int = 9):
    """Geometric rays through the drop in the plane y = 0 (polylines, NaN-separated, with colours): for each order p a
    fan of impact parameters, and the Descartes ray of p = 2 and 3 where it exists (1 < m < p; from the engine's ray
    optics, theories.approx.rainbow). For m < 1 the rays that enter have b < m (sin r = b/m <= 1): the fans of p >= 1
    span b up to 0.95 m, the reflection p = 0 all b (review B8-mie, M11: the rays of m = 1.333 were drawn for
    m <= 1)."""
    pts, col = [], []
    for p in orders:
        top = 0.95 if (p == 0 or m >= 1.0) else 0.95 * m
        bs = list(np.linspace(0.1 * min(1.0, top / 0.95), top, n_rays))
        if p >= 2:
            try:
                bs.append(RB.descartes(m, p)["b"])
            except ValueError:
                pass
        for k, b in enumerate(bs):
            path = RB.ray_path(m, p, float(b), length=2.4)
            P3 = np.stack([path[:, 0], np.zeros(len(path)), path[:, 1]], -1)
            descartes = p >= 2 and k == len(bs) - 1
            c = np.array(RAY_COLOURS[p]) * (1.0 if descartes else 0.55)
            pts.append(P3)
            col.append(np.tile(c, (len(P3), 1)))
            pts.append(np.full((1, 3), np.nan))
            col.append(np.zeros((1, 3)))
    return np.concatenate(pts).astype(np.float32), np.concatenate(col).astype(np.float32)


def bin_mean(theta_fine, values, edges):
    """Means of values over the angular bins [edges_k, edges_k+1) (fine grid), and their minima and maxima."""
    k = np.clip(np.searchsorted(edges, theta_fine, side="right") - 1, 0, len(edges) - 2)
    n = np.bincount(k, minlength=len(edges) - 1).astype(float)
    s = np.bincount(k, weights=values, minlength=len(edges) - 1)
    mean = s / np.maximum(n, 1)
    lo = np.full(len(edges) - 1, np.inf)
    hi = np.full(len(edges) - 1, -np.inf)
    np.minimum.at(lo, k, values)
    np.maximum.at(hi, k, values)
    return mean, lo, hi
