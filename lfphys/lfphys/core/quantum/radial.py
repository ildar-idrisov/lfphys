# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Radial Schroedinger equation for a central potential (bound states):

    -hbar^2/(2 mu) u'' + [V(r) + hbar^2 l(l+1)/(2 mu r^2)] u = E u,   u(0) = u(R) = 0,   psi = u(r)/r Y_lm.

Discretised in the sine basis of the box (0, R): u is sampled at r_i = i R/(N+1); the kinetic operator is diagonal in
the discrete sine transform, T = S^T diag(hbar^2 k_n^2/2mu) S with k_n = n pi / R and the orthonormal S, built from
its closed form (Colbert & Miller 1992, Eq. A6). Spectral accuracy for smooth u. A Coulomb-like 1/r term makes u''
jump at the origin (odd extension) and the error then falls as dr^2 + c3 dr^3 + ...; Richardson extrapolation over
grids dr, dr/2 (and dr/4) removes these terms one by one.

Measured accuracy for -1/r (hbar = mu = 1, R = 100, max over n = 1..3; review 2026-10-23, E5, and
tests/test_qcd.py): l = 0, N = 800: no extrapolation 2.4e-3, ``richardson=1`` (default) 2.1e-4,
``richardson=2`` 3.8e-7; N = 400, ``richardson=2``: 1.1e-5. For l >= 1 the wave function vanishes at the origin
and the plain result is already ~1e-6 (N >= 800; then limited by the box and the grid, extrapolation does not help).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import linalg

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "law",
    "title": T("The radial Schrödinger equation (bound states)"),
    "statement": T("Levels and radial functions of a central potential in the sine basis of a box; any potential "
                   "V(r), orbital angular momentum l."),
    "validity": T("a non-relativistic particle; the box much larger than the state, the step much smaller than the "
                  "potential's scale"),
    "basis": ["Schrödinger 1926", "Colbert & Miller, J. Chem. Phys. 96, 1982 (1992)"],
    "conflicts": [],
}


def _kinetic(N: int, R: float, mu: float, hbar: float) -> np.ndarray:
    """S^T diag(hbar^2 k_n^2 / 2 mu) S in closed form (Colbert & Miller, Eq. A6, interval (0, R), N + 1 intervals)."""
    M = N + 1
    i = np.arange(1, N + 1)
    d, s_ = i[:, None] - i[None, :], i[:, None] + i[None, :]
    with np.errstate(divide="ignore"):
        T = (1.0 / np.sin(np.pi * d / (2 * M)) ** 2 - 1.0 / np.sin(np.pi * s_ / (2 * M)) ** 2)
    T[np.diag_indices(N)] = (2 * M * M + 1) / 3.0 - 1.0 / np.sin(np.pi * i / M) ** 2
    sign = np.where(d % 2 == 0, 1.0, -1.0)
    return hbar**2 / (2 * mu) * math.pi**2 / (2 * R * R) * sign * T


def _solve(V, l, mu, R, N, n_states, hbar):
    r = np.arange(1, N + 1) * R / (N + 1)
    H = _kinetic(N, R, mu, hbar) + np.diag(V(r) + hbar**2 * l * (l + 1) / (2 * mu * r * r))
    E, vec = linalg.eigh(H, subset_by_index=[0, n_states - 1])
    return E, r, vec / math.sqrt(R / (N + 1))


def levels(V, l: int, mu: float, R: float, N: int = 800, n_states: int = 5, hbar: float = 1.0,
           richardson: int = 1):
    """Energies and u(r) (columns, normalised: sum u^2 dr = 1) of the lowest radial states.
    ``richardson``: 0 - the grid of 2N + 1 points; 1 - (4 E(dr/2) - E(dr))/3 from N and 2N + 1 points (removes the
    dr^2 term of a 1/r potential); 2 - a second stage with 4N + 3 points, (8 R1(dr/2) - R1(dr))/7 (removes dr^3;
    the 4N + 3 grid costs ~ (4N)^3). u(r) is that of the 2N + 1 grid."""
    richardson = int(richardson)
    E, r, u = _solve(V, l, mu, R, 2 * N + 1, n_states, hbar)
    if richardson >= 1:
        E1, _, _ = _solve(V, l, mu, R, N, n_states, hbar)
        R1 = (4.0 * E - E1) / 3.0
        if richardson >= 2:
            E4, _, _ = _solve(V, l, mu, R, 4 * N + 3, n_states, hbar)
            R1b = (4.0 * E4 - E) / 3.0
            return (8.0 * R1b - R1) / 7.0, r, u
        return R1, r, u
    return E, r, u


def wavefunctions(V, l: int, mu: float, R: float, N: int = 800, n_states: int = 3, hbar: float = 1.0):
    """Energies and radial functions u(r) of the lowest states with their measured accuracy (plan P14.9: the 3-D
    clouds of ``lfphys.core.quantum.central3d``). Solved on the grids of N and 2N + 1 points (the coarse points are
    every other fine point). Energies: ``levels`` with ``richardson=1``. u(r): for l = 0 a 1/r-like potential makes
    u'' jump at the origin and the error of u falls as dr^2 too, so u is extrapolated on the coarse points,
    (4 u_fine - u_coarse) / 3; for l >= 1 the fine-grid u is returned as is (its error already falls faster than
    dr^2, extrapolation makes it worse). Measured for -1/r (R = 100, N = 800, n = 1, 2; tests/test_central3d.py):
    max |u - u_exact| / max |u| = 2.6e-4 (l = 0; 2.8e-3 without extrapolation), 3.5e-5 (l = 1).
    Returns (E, r, u (columns, normalised: sum u^2 dr = 1, sign: positive first lobe), est) with est[k] =
    max |u_fine - u_coarse| / max |u| of state k, an upper estimate of the error of the coarse grid."""
    Ec, rc, uc = _solve(V, l, mu, R, N, n_states, hbar)
    Ef, rf, uf = _solve(V, l, mu, R, 2 * N + 1, n_states, hbar)
    E = (4.0 * Ef - Ec) / 3.0  # = levels(..., richardson=1)
    for k in range(n_states):  # one sign convention on both grids: the first lobe positive
        for u in (uc, uf):
            j = int(np.argmax(np.abs(u[:, k]) > 1e-3 * np.max(np.abs(u[:, k]))))
            if u[j, k] < 0:
                u[:, k] *= -1.0
    fine_on_coarse = uf[1::2]
    est = np.max(np.abs(fine_on_coarse - uc), axis=0) / np.max(np.abs(uf), axis=0)
    if l == 0:
        r, u = rc, (4.0 * fine_on_coarse - uc) / 3.0
    else:
        r, u = rf, uf.copy()
    dr = r[1] - r[0]
    u /= np.sqrt(np.sum(u * u, axis=0) * dr)
    return E, r, u, est
