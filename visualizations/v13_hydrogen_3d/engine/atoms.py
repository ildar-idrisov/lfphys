# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The atoms of v13 (a nucleus of charge Z and mass M with an electron, or positronium) and their units, and the
independent route the slices are checked against: R_nl by the explicit power series of the Laguerre polynomial
(``hydrogen.radial_series``, with its round-off bound) and Y_lm by scipy (``scipy.special.sph_harm_y``), instead of
the world's log-scaled recurrence and the engine's own harmonics."""

from __future__ import annotations

import math

import numpy as np
from scipy import constants as sc
from scipy import special

from lfphys.core.quantum import hydrogen as H

ANGSTROM = 1e-10
EPS = np.finfo(float).eps

# id: (label, Z, nucleus mass kg, nucleus mark)
ATOMS = {
    "H": ("водород ¹H: электрон и протон", 1, sc.m_p, "p⁺"),
    "D": ("дейтерий ²H: электрон и дейтрон", 1, sc.physical_constants["deuteron mass"][0], "d⁺"),
    "He+": ("ион ⁴He⁺: электрон и α-частица (Z = 2)", 2, sc.physical_constants["alpha particle mass"][0], "α²⁺"),
    "Ps": ("позитроний: электрон и позитрон (μ = mₑ/2)", 1, sc.m_e, "e⁺"),
}


def units(atom: str) -> dict:
    """The reduced mass mu, its Bohr radius a (m) and Hartree energy E_h (J); the world computes in a = hbar = mu = 1:
    lengths in a, energies in E_h, times in hbar / E_h."""
    label, Z, M, mark = ATOMS[atom]
    mu = H.reduced_mass(sc.m_e, M)
    a, Eh = H.bohr_radius(mu), H.hartree(mu)
    return {"label": label, "Z": Z, "mu": mu, "a": a, "Eh": Eh, "mark": mark, "Lu": a / ANGSTROM, "tu": sc.hbar / Eh,
            "eV": Eh / sc.e}


def _real_from_complex(Y, m):
    if m > 0:
        return math.sqrt(2.0) * (-1) ** m * np.real(Y)
    if m < 0:
        return math.sqrt(2.0) * (-1) ** m * np.imag(Y)
    return np.real(Y)


def reference(specs, coefs, Z, x, y, z, t):
    """psi(x, y, z, t) = sum_k c_k e^{-i E_k t} R_nl Y_lm (a = hbar = mu = 1) by the series and scipy, and a bound on
    |psi_world - psi_ref|: the series' round-off bound, the log route's (exp of a sum S of logs: ~ S eps, the
    recurrence ~ n eps) and the harmonics' (three-term recurrences on both sides: 64 (l + 1) eps of the largest |Y|).
    ``specs``: (n, l, m, real) per state."""
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    rho_xy = np.hypot(x, y)
    r = np.hypot(rho_xy, z)
    th, ph = np.arctan2(rho_xy, z), np.arctan2(y, x)
    psi = np.zeros(r.shape, complex)
    tol = np.zeros(r.shape)
    for (n, l, m, real), ck in zip(specs, coefs):
        R, bR = H.radial_series(n, l, r, Z)
        Yc = special.sph_harm_y(l, abs(m), th, ph)
        if m < 0 and not real:
            Yc = (-1) ** m * np.conj(Yc)
        Y = _real_from_complex(Yc, m) if real else Yc
        E = -Z * Z / (2.0 * n * n)
        psi = psi + ck * np.exp(-1j * E * t) * R * Y
        rho = 2.0 * Z * r / n
        S = np.abs(np.log(np.where(np.abs(R) > 0, np.abs(R), 1.0))) + rho + \
            l * np.abs(np.log(np.where(rho > 0, rho, 1.0)))
        Ymax = math.sqrt((2 * l + 1) / (4 * math.pi)) * (math.sqrt(2.0) if real else 1.0)  # |Y_lm| <= this
        tol = tol + abs(ck) * ((bR + 8 * EPS * (S + 4 * n) * np.abs(R)) * np.abs(Y) + np.abs(R) * 64 * (l + 1) * EPS * Ymax)
    return psi, tol + 1e-300
