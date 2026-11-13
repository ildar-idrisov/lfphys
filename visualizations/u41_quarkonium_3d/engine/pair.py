# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The heavy quark-antiquark pair of v14 in the Cornell model (``lfphys.theories.models.cornell``: a fitted model): the
radial solves per orbital momentum L with the box the highest state needs (as ``cornell.spectrum`` chooses it), their
tabulated radial functions (``central3d.RadialTable``) and the independent route the slices are checked against (a
second radial solve on a finer grid, scipy's spherical harmonics). Natural units: GeV, GeV^-1, hbar = c = 1."""

from __future__ import annotations

import functools
import math

import numpy as np
from scipy import constants as sc
from scipy import special

from lfphys.core.quantum import central3d as C, radial
from lfphys.codes import coded
from lfphys.i18n import T
from lfphys.theories.models import cornell

HBARC_GEV_FM = sc.hbar * sc.c / (1e9 * sc.e) / 1e-15  # 0.1973... GeV fm: fm per GeV^-1
HBAR_GEV_S = sc.hbar / (1e9 * sc.e)  # s per GeV^-1 of time
N_GRID = 800  # radial solver: the drawn functions (N and 2N + 1 points, l = 0 extrapolated; radial.wavefunctions)
N_REF = 1200  # the independent solve of the checks
EPS = np.finfo(float).eps
SYSTEMS = {"charm": (T("charmonium cc̄"), "m_c", "c"), "bottom": (T("bottomonium bb̄"), "m_b", "b")}


def mass(system: str) -> float:
    return cornell.PARAMS[SYSTEMS[system][1]]


@functools.lru_cache(maxsize=32)
def solve(system: str, L: int, n_states: int = 3, N: int = N_GRID):
    """(E (GeV, Richardson), r, u, est, R_box) of the lowest n_states radial states of orbital momentum L; the box is
    enlarged until it holds the highest one (its turning point plus 8 decay lengths, ``cornell._box_needed``).
    Cached: the level diagram and the states drawn come from the same solves (read-only arrays)."""
    P = cornell.PARAMS
    V = cornell.potential(P["kappa"], P["a"])
    mu = 0.5 * mass(system)
    R = 25.0
    for _ in range(4):
        E, r, u, est = radial.wavefunctions(V, L, mu, R, N=N, n_states=n_states)
        need = cornell._box_needed(P["kappa"], P["a"], mu, L, float(E[-1]))
        if need <= R:
            for a in (E, r, u, est):
                a.flags.writeable = False
            return E, r, u, est, R
        R = 1.1 * need
    # the same condition as the engine's Cornell spectrum, with the engine's code (lfphys.codes "cornell.box")
    raise coded(ValueError(T("the states with L = {L} do not fit into the box of radius {R:.3g} GeV⁻¹", L=L, R=R)),
                "cornell.box")


def tables(system: str, specs, N: int = N_GRID):
    """For each (n, L, m, real): the radial table, its energy and the estimate of its error; one solve of the three
    lowest states per L (the same as the level diagram's)."""
    out = []
    for n, L, _, _ in specs:
        E, r, u, est, Rb = solve(system, L, 3, N)
        out.append({"R": C.RadialTable(r, u[:, n - 1], L), "E": float(E[n - 1]), "est": float(est[n - 1]),
                    "R_box": Rb})
    return out


def reference(system, specs, coefs, x, y, z, t, ref_tables, drawn_tables):
    """psi at points by the finer solve (N_REF) and scipy's harmonics, and the tolerance: 3 x the largest difference
    of the two radial solves (|R_N - R_ref| <= |R_N - R_2N| / (1 - 2^-p) with the measured order p >= 2 of the
    solver's convergence, so 3 leaves room) times |Y|, plus the harmonics' round-off. The radial part of this
    comparison is therefore bounded by construction; the check tests the angular part, the phases and the plane's
    geometry; the radial accuracy is the separate check "Convergence" against the picture's resolution."""
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    rho_xy = np.hypot(x, y)
    r = np.hypot(rho_xy, z)
    th, ph = np.arctan2(rho_xy, z), np.arctan2(y, x)
    psi = np.zeros(r.shape, complex)
    tol = np.zeros(r.shape)
    rr = np.linspace(0.0, max(tb["R_box"] for tb in ref_tables), 20001)
    for (n, l, m, real), ck, tr, td in zip(specs, coefs, ref_tables, drawn_tables):
        Yc = special.sph_harm_y(l, abs(m), th, ph)
        if m < 0 and not real:
            Yc = (-1) ** m * np.conj(Yc)
        if real:
            Y = math.sqrt(2.0) * (-1) ** m * (np.real(Yc) if m > 0 else np.imag(Yc)) if m else np.real(Yc)
        else:
            Y = Yc
        R = tr["R"](r)
        psi = psi + ck * np.exp(-1j * tr["E"] * t) * R * Y
        dR = float(np.max(np.abs(tr["R"](rr) - td["R"](rr))))
        Ymax = math.sqrt((2 * l + 1) / (4 * math.pi)) * (math.sqrt(2.0) if real else 1.0)
        tol = tol + abs(ck) * (3 * dR * np.abs(Y) + np.abs(R) * 64 * (l + 1) * EPS * Ymax +
                               abs(t) * abs(tr["E"] - td["E"]) * np.abs(R * Y))
    return psi, tol + 1e-300
