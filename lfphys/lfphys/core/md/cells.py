# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Neighbour search for the molecular dynamics (plan P8): cell lists and Verlet pair lists, vectorised in NumPy.

``pair_list(x, L, periodic, r)`` returns every pair (i, j), i != j, whose minimum-image distance is below r, each pair
once, in a deterministic order (the same input gives the same list bit for bit; a saved state rebuilds its list from
the positions of the last build and continues bit-identically). Method (Allen & Tildesley, "Computer Simulation of
Liquids", §5.3): the box is cut into nc_a = floor(L_a / r) cells per axis; a pair can only join a cell to itself or to
an adjacent cell; each unordered pair of cells is visited once through a half stencil (the offsets o in {-1, 0, 1}^d
whose first non-zero component is +1, and o = 0 with j after i). A periodic axis needs nc_a >= 3 for the half stencil
(otherwise c + 1 and c - 1 are the same cell and pairs would be counted twice): with nc_a < 3 the axis gets one cell.
With one cell on every axis (or few particles) all pairs are tested directly. The candidates of one offset are made
at once with a ragged arange (no Python loop over particles) and filtered by distance; the work is done offset by
offset to bound the memory.

The minimum image along periodic axes is exact for r <= L_a / 2 (checked by the caller). A Verlet list built with
r = r_c + skin stays complete while no particle has moved more than skin/2 since the build (the caller checks the
largest displacement and rebuilds).
"""

from __future__ import annotations

import itertools

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("Neighbour search: cell lists and Verlet pair lists"),
    "statement": T("All pairs of particles closer than a given radius (with the minimum image along periodic axes), "
                   "each pair once, in a deterministic order; cells and a half stencil of neighbouring cells, "
                   "vectorised (NumPy)."),
    "validity": T("exact (the complete pair list) for r ≤ L/2 along periodic axes; a Verlet list with a skin is "
                  "complete while no particle has moved more than skin/2"),
    "basis": [T("Allen & Tildesley, Computer Simulation of Liquids (2nd ed., 2017), §5.3: cell lists and Verlet "
                "lists")],
    "conflicts": [],
}

_BRUTE_N = 48


def _minimum_image(dx, L, periodic):
    for a in np.flatnonzero(periodic):
        dx[:, a] -= L[a] * np.rint(dx[:, a] / L[a])
    return dx


def _brute(x, L, periodic, r):
    n = x.shape[0]
    i, j = np.triu_indices(n, 1)
    dx = _minimum_image(x[j] - x[i], L, periodic)
    keep = np.einsum("ij,ij->i", dx, dx) < r * r
    return i[keep].astype(np.int64), j[keep].astype(np.int64)


def cell_counts(L, periodic, r):
    """Cells per axis for a search radius r."""
    L = np.asarray(L, float)
    nc = np.maximum(np.floor(L / r).astype(np.int64), 1)
    nc = np.where(np.asarray(periodic, bool) & (nc < 3), 1, nc)
    return nc


def pair_list(x, L, periodic, r, brute_n: int = _BRUTE_N):
    """Pairs (i, j) (int64 arrays) with minimum-image distance < r; positions x (n, d) inside [0, L) on periodic axes
    and [0, L] on walled axes."""
    x = np.asarray(x, float)
    n, d = x.shape
    L = np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    if n < 2:
        z = np.zeros(0, np.int64)
        return z, z.copy()
    nc = cell_counts(L, periodic, r)
    if n <= brute_n or np.all(nc == 1):
        return _brute(x, L, periodic, r)
    w = L / nc
    cidx = np.floor(x / w).astype(np.int64)
    cidx = np.clip(cidx, 0, nc - 1)
    strides = np.cumprod(np.concatenate([[1], nc[::-1][:-1]]))[::-1]   # row-major
    cell = cidx @ strides
    order = np.argsort(cell, kind="stable")
    cs = cell[order]
    ncell = int(np.prod(nc))
    count = np.bincount(cs, minlength=ncell)
    start = np.concatenate([[0], np.cumsum(count)[:-1]])
    xs = x[order]
    # all cells' multi-indices
    grid = np.stack(np.unravel_index(np.arange(ncell), tuple(nc)), axis=1)
    out_i, out_j = [], []
    pos = np.arange(n)
    # self cell: partners after p within its cell
    end = start[cs] + count[cs]
    cnt = end - pos - 1
    _emit(pos, pos + 1, cnt, xs, L, periodic, r, out_i, out_j)
    # half stencil
    choices = [(-1, 0, 1) if nc[a] > 1 else (0,) for a in range(d)]
    for o in itertools.product(*choices):
        o = np.array(o)
        nz = np.flatnonzero(o)
        if len(nz) == 0 or o[nz[0]] < 0:
            continue
        g = grid + o
        valid = np.ones(ncell, bool)
        for a in range(d):
            if periodic[a]:
                g[:, a] %= nc[a]
            else:
                valid &= (g[:, a] >= 0) & (g[:, a] < nc[a])
        nb = np.where(valid, np.clip(g, 0, nc - 1) @ strides, -1)
        nbp = nb[cs]
        ok = nbp >= 0
        c = np.where(ok, count[np.where(ok, nbp, 0)], 0)
        s0 = np.where(ok, start[np.where(ok, nbp, 0)], 0)
        _emit(pos, s0, c, xs, L, periodic, r, out_i, out_j)
    if not out_i:
        z = np.zeros(0, np.int64)
        return z, z.copy()
    I = np.concatenate(out_i)
    J = np.concatenate(out_j)
    return order[I].astype(np.int64), order[J].astype(np.int64)


def _emit(p, s0, cnt, xs, L, periodic, r, out_i, out_j):
    """Candidates: particle p[k] with the cnt[k] particles from sorted index s0[k]; keep those closer than r."""
    cnt = np.maximum(cnt, 0)
    tot = int(cnt.sum())
    if tot == 0:
        return
    I = np.repeat(p, cnt)
    off = np.repeat(np.cumsum(cnt) - cnt, cnt)
    J = np.repeat(s0, cnt) + (np.arange(tot) - off)
    dx = _minimum_image(xs[J] - xs[I], L, periodic)
    keep = np.einsum("ij,ij->i", dx, dx) < r * r
    out_i.append(I[keep])
    out_j.append(J[keep])
