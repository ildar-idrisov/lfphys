# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Scattering of a plane wave by an infinite circular cylinder at normal incidence: the exact series solution of
Maxwell's equations (2-D), a reference for the FDTD solver (``lfphys.core.em.fdtd``).

Time dependence exp(-i omega t); the incident wave travels along +x, the cylinder's axis is z, its radius a, the
relative refractive index m = n_cyl / n_medium (complex, Im m >= 0 for absorption; or "pec"), size x = k a with k the
wavenumber in the medium (non-magnetic cylinder). Two polarizations: "tm" (E along the axis, E_z; Bohren & Huffman's
case I) and "te" (H along the axis, H_z; case II). The incident field is sum_n i^n J_n(k rho) e^{i n phi}; the scattered
field sum_n i^n c_n H_n(k rho) e^{i n phi} (H_n = H_n^(1)), with c_{-n} = c_n and, from the continuity of the axial
field and of the tangential field of the other kind at rho = a,

    TM:  c_n = [m J_n'(m x) J_n(x) - J_n(m x) J_n'(x)] / [J_n(m x) H_n'(x) - m J_n'(m x) H_n(x)],
    TE:  c_n = -[m J_n(m x) J_n'(x) - J_n(x) J_n'(m x)] / [m J_n(m x) H_n'(x) - J_n'(m x) H_n(x)],
    PEC: TM c_n = -J_n(x) / H_n(x),  TE c_n = -J_n'(x) / H_n'(x).

Cross sections per unit length (scattering widths; efficiencies Q = sigma / (2 a)):
    sigma_sca = (4 / k) sum_{n=-inf}^{inf} |c_n|^2,   sigma_ext = -(4 / k) Re T(0),   T(phi) = sum_n c_n e^{i n phi},
    dsigma/dphi = (2 / (pi k)) |T(phi)|^2   (phi from the forward direction; the integral over phi is sigma_sca),
from the far field of H_n (DLMF 10.17.5) and the flux through a large circle. (Bohren & Huffman, ch. 8, give the
same series with b_n = -c_n (TM) and a_n = -c_n (TE); the book was not obtained, so the coefficients are derived here
from the boundary conditions and checked by them in the tests.) The series is summed to n_max = x + 4.05 x^(1/3) + 8 (Wiscombe's criterion plus margin); terms beyond are below
1e-16 of the largest for the sizes used (checked against n_max + 20 in the tests).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special as sp

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "exact solution",
    "title": T("Scattering of a plane wave by an infinite circular cylinder (exact series)"),
    "statement": T("The exact solution of Maxwell's equations for an infinite circular cylinder (dielectric, "
                   "absorbing or a perfect conductor) at incidence perpendicular to the axis: the series coefficients, "
                   "the scattering, extinction and absorption cross-sections per unit length, the angular "
                   "distribution, the field near the cylinder."),
    "validity": T("a plane wave perpendicular to the axis; a homogeneous isotropic non-magnetic cylinder in a "
                  "homogeneous lossless medium; the series is truncated at n > x + 4.05·x^(1/3) + 8"),
    "basis": [T("derived from the boundary conditions (continuity of E_z and H_φ, H_z and E_φ; checked in the tests); "
                "the same series: Bohren & Huffman (1983), ch. 8 (book not obtained)"),
              T("asymptotics of H_n: DLMF 10.17.5")],
    "conflicts": [],
}


def n_max(x: float) -> int:
    return int(math.ceil(abs(x) + 4.05 * abs(x) ** (1 / 3) + 8))


def coefficients(m, x: float, pol: str, nmax: int | None = None) -> np.ndarray:
    """c_n for n = 0..nmax (the scattered field's coefficients, c_{-n} = c_n)."""
    if pol not in ("tm", "te"):
        raise ValueError(T("pol: tm (E along the axis) or te (H along the axis)"))
    N = n_max(x) if nmax is None else int(nmax)
    n = np.arange(N + 1)
    Jx, dJx = sp.jv(n, x), sp.jvp(n, x)
    Hx, dHx = sp.hankel1(n, x), sp.h1vp(n, x)
    if isinstance(m, str):
        if m != "pec":
            raise ValueError(T("m: a complex refractive index or 'pec'"))
        return -Jx / Hx if pol == "tm" else -dJx / dHx
    m = complex(m)
    mx = m * x
    Jm, dJm = sp.jv(n, mx), sp.jvp(n, mx)
    if pol == "tm":
        c = (m * dJm * Jx - Jm * dJx) / (Jm * dHx - m * dJm * Hx)
    else:
        c = -(m * Jm * dJx - Jx * dJm) / (m * Jm * dHx - dJm * Hx)
    c = np.where(np.isfinite(c), c, 0.0)
    return c


def efficiencies(m, x: float, pol: str) -> dict:
    """Q_sca, Q_ext, Q_abs (per projected width 2a) and the cross sections per unit length for k = 1 / a = 1:
    multiply sigma by a for a cylinder of radius a."""
    c = coefficients(m, x, pol)
    s2 = abs(c[0]) ** 2 + 2.0 * np.sum(np.abs(c[1:]) ** 2)
    T0 = c[0] + 2.0 * np.sum(c[1:])
    qs = 2.0 / x * s2
    qe = -2.0 / x * T0.real
    return {"Qsca": float(qs), "Qext": float(qe), "Qabs": float(qe - qs), "n_terms": len(c)}


def amplitude(m, x: float, pol: str, phi) -> np.ndarray:
    """T(phi) = sum_n c_n e^{i n phi} (phi from the forward direction): the far field is
    sqrt(2 / (pi k rho)) e^{i (k rho - pi/4)} T(phi) times the incident amplitude."""
    c = coefficients(m, x, pol)
    phi = np.asarray(phi, float)
    n = np.arange(1, len(c))
    return c[0] + 2.0 * (np.cos(np.multiply.outer(phi, n)) @ c[1:])


def dsigma_dphi(m, x: float, pol: str, phi, k: float = 1.0) -> np.ndarray:
    """Differential scattering width per radian, (2 / (pi k)) |T(phi)|^2 (its integral over phi is sigma_sca)."""
    return 2.0 / (math.pi * k) * np.abs(amplitude(m, x, pol, phi)) ** 2


def fields(m, x: float, pol: str, rho, phi) -> dict:
    """The axial field (E_z for TM, H_z for TE) and the azimuthal field of the other kind at (k rho, phi) (rho in
    units of 1/k, inside and outside the cylinder), incident amplitude 1: {"axial", "azimuthal", "inside"}. TM: the
    azimuthal field is eta H_phi = i dE_z/d(k rho) outside, i m dE_z/d(m k rho) inside; TE: E_phi / eta =
    -i dH_z/d(k rho) outside, -(i / m) dH_z/d(m k rho) inside (Faraday's and Ampere's laws; eta of the medium).
    Both are continuous at rho = a (the tests check it)."""
    c = coefficients(m, x, pol)
    N = len(c) - 1
    rho, phi = np.broadcast_arrays(np.asarray(rho, float), np.asarray(phi, float))
    n = np.arange(-N, N + 1)
    cn = c[np.abs(n)]
    inside = rho < x
    ax = np.zeros(rho.shape, complex)
    az = np.zeros(rho.shape, complex)
    e = np.exp(1j * np.multiply.outer(phi, n)) * (1j ** n)
    out = ~inside
    if np.any(out):
        r = rho[out][:, None]
        f = sp.jv(n, r) + cn * sp.hankel1(n, r)
        df = sp.jvp(n, r) + cn * sp.h1vp(n, r)
        ax[out] = np.sum(e[out] * f, axis=1)
        az[out] = (1j if pol == "tm" else -1j) * np.sum(e[out] * df, axis=1)
    if np.any(inside) and not isinstance(m, str):
        mm = complex(m)
        dn = (sp.jv(n, x) + cn * sp.hankel1(n, x)) / sp.jv(n, mm * x)
        r = rho[inside][:, None]
        ax[inside] = np.sum(e[inside] * dn * sp.jv(n, mm * r), axis=1)
        df = np.sum(e[inside] * dn * sp.jvp(n, mm * r), axis=1)
        az[inside] = 1j * mm * df if pol == "tm" else -1j / mm * df
    return {"axial": ax, "azimuthal": az, "inside": inside}
