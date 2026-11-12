"""Review B8 (slit): an INDEPENDENT finite-difference frequency-domain (FDFD) check of the thin-screen slit, both
polarisations, against lfphys.core.em.slit and the Libelo-Bombardt table (NOLTR 70-58, Table I).

Nothing of the engine is used for the FDFD: the 2-D Helmholtz equation on a uniform grid (5-point stencil), a
stretched-coordinate PML on all four sides, the zero-thickness screen at z = 0 placed between two grid rows
(z = -h/2 and +h/2): Dirichlet (TE, E along the slit) by an antisymmetric ghost, Neumann (TM, H along the slit) by
cutting the links; the aperture columns keep their links. The unknown is the scattered field relative to the exact
DISCRETE solution of the screen without slit (standing wave with the grid's own wavenumber k~, cos(k~ h) = 1 - k^2 h^2
/ 2), so the only source sits on the aperture's links. The transmitted power is the exact discrete flux through the
aperture links, Im(conj(u_lo) u_hi) (discrete energy conservation of the scheme), normalised by the incident discrete
flux sin(k~ h)/h. The slit is |x| < b = N h with cell-centred columns: refining h -> h/2 keeps the geometry; the
limit h -> 0 by Richardson extrapolation from four levels (N = 8, 16, 32, 64), observed order printed.
Lengths in wavelengths (k = 2 pi); eta = k w / 2 (Libelo-Bombardt's variable).
"""
import math
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

K = 2 * math.pi


def fdfd_T(pol, b, N, margin=0.3, Lp=0.4, R0=1e-8):
    h = b / N
    nx_half = int(math.ceil((b + margin + Lp) / h))
    nz_half = int(math.ceil((margin + Lp) / h))
    xs = (np.arange(-nx_half, nx_half) + 0.5) * h  # cell-centred columns, symmetric
    zs = (np.arange(-nz_half, nz_half) + 0.5) * h  # rows at +-h/2, +-3h/2, ...
    nx, nz = len(xs), len(zs)
    kt = math.acos(1 - (K * h) ** 2 / 2) / h  # the grid's wavenumber along z
    smax = 3 * math.log(1 / R0) / (2 * Lp)

    def stretch(c, lim):
        d = np.clip(np.abs(c) - (lim - Lp), 0, None)
        return 1 + 1j * smax * (d / Lp) ** 2 / K
    xlim, zlim = xs[-1] + 0.5 * h, zs[-1] + 0.5 * h
    sx_n, sz_n = stretch(xs, xlim), stretch(zs, zlim)
    sx_f = stretch(np.concatenate([[xs[0] - 0.5 * h], 0.5 * (xs[1:] + xs[:-1]), [xs[-1] + 0.5 * h]]), xlim)
    sz_f = stretch(np.concatenate([[zs[0] - 0.5 * h], 0.5 * (zs[1:] + zs[:-1]), [zs[-1] + 0.5 * h]]), zlim)
    idx = lambda i, j: i * nz + j  # noqa: E731
    open_col = np.abs(xs) < b
    jlo = nz_half - 1  # row z = -h/2
    jhi = nz_half      # row z = +h/2
    rows, cols, vals = [], [], []
    rhs = np.zeros(nx * nz, complex)
    ub_lo = (2j * math.sin(kt * zs[jlo])) if pol == "TE" else 2 * math.cos(kt * zs[jlo])
    I, J = np.meshgrid(np.arange(nx), np.arange(nz), indexing="ij")
    I, J = I.ravel(), J.ravel()
    p = idx(I, J)
    diag = np.full(len(p), K * K + 0j)
    # x links (never cut: the screen is horizontal)
    for di in (-1, 1):
        ok = (I + di >= 0) & (I + di < nx)
        f = np.where(di > 0, I + 1, I)  # face index between I and I+di
        cf = 1 / (sx_n[I] * sx_f[np.clip(f, 0, nx)] * h * h)
        rows.append(p[ok]); cols.append(idx(I[ok] + di, J[ok])); vals.append(cf[ok])
        diag -= np.where(ok, cf, cf)  # outermost: Dirichlet 0 beyond the PML
    # z links
    for dj in (-1, 1):
        ok = (J + dj >= 0) & (J + dj < nz)
        f = np.where(dj > 0, J + 1, J)
        cf = 1 / (sz_n[J] * sz_f[np.clip(f, 0, nz)] * h * h)
        crosses = ((J == jlo) & (dj == 1)) | ((J == jhi) & (dj == -1))
        cut = crosses & ~open_col[I]
        keep = ok & ~cut
        rows.append(p[keep]); cols.append(idx(I[keep] + 0, J[keep] + dj)); vals.append(cf[keep])
        if pol == "TE":  # cut link: ghost = -u (u = 0 at the screen) -> -2 cf on the diagonal; else the usual -cf
            diag -= np.where(cut, 2 * cf, cf)
        else:  # Neumann: a cut link carries nothing
            diag -= np.where(cut, 0.0, cf)
    rows.append(p); cols.append(p); vals.append(diag)
    A = sp.csc_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nx * nz, nx * nz))
    # sources: L u_b on the aperture rows (u_b solves the screen without slit with the links cut)
    cf0 = 1 / (h * h)  # no stretching at the aperture
    if pol == "TE":  # cut-link operator had -2 cf (ghost -u_lo); with the link: + u_hi - u_lo ... L u_b(lo) = +u_b/h^2
        s_lo, s_hi = ub_lo * cf0, ub_lo * cf0
    else:  # Neumann: L u_b(lo) = (u_b(hi) - u_b(lo)) / h^2 = -u_b/h^2; L u_b(hi) = (u_b(lo) - 0)/h^2
        s_lo, s_hi = -ub_lo * cf0, ub_lo * cf0
    ic = np.nonzero(open_col)[0]
    rhs[idx(ic, jlo)] = -s_lo
    rhs[idx(ic, jhi)] = -s_hi
    t0 = time.time()
    us = spla.spsolve(A, rhs, permc_spec="MMD_AT_PLUS_A")
    dt = time.time() - t0
    us = us.reshape(nx, nz)
    u_lo = us[ic, jlo] + ub_lo
    u_hi = us[ic, jhi]
    P = float(np.sum(np.imag(np.conj(u_lo) * u_hi)))  # sum over the aperture links (times h / h)
    T = P * h / (2 * b * math.sin(kt * h))
    return T, nx * nz, dt


sys.path.insert(0, "/lf/lfphys")
from lfphys.core.em import slit as S  # noqa: E402

LB = {0.8: 0.2923, 1.0: 0.6012, 1.5: 1.2307, 2.0: 1.2061}
cases = [("TE", 0.8), ("TE", 1.0), ("TE", 1.5), ("TE", 2.0), ("TM", 0.8), ("TM", 1.5)]
for pol, eta in cases:
    b = eta / K  # w = 2 eta / k -> b = eta / k
    Ns = (8, 16, 32, 64)
    Ts = []
    for N in Ns:
        T, n, dt = fdfd_T(pol, b, N)
        Ts.append(T)
        print(f"  {pol} eta = {eta}: N = {N:3d} ({n} unknowns, {dt:.0f} s): T = {T:.6f}", flush=True)
    d = np.diff(Ts)
    p = math.log2(abs(d[-2] / d[-1]))
    Tx = Ts[-1] + d[-1] / (2 ** p - 1)
    p1 = 1.0
    Tx1 = Ts[-1] + d[-1] / (2 ** p1 - 1)
    eng = S.solve(K, [0.0], [2 * b], 0.0, pol).transmission()
    line = (f"{pol} eta = {eta}: FDFD extrapolated {Tx:.4f} (observed order {p:.2f}; with order 1: {Tx1:.4f}); "
            f"engine {eng:.4f} (engine/FDFD - 1 = {eng / Tx - 1:+.2%})")
    if pol == "TE":
        line += f"; Libelo-Bombardt {LB[eta]:.4f} (LB/FDFD - 1 = {LB[eta] / Tx - 1:+.2%})"
    print(line, flush=True)
