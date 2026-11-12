# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Statistical mechanics measured from a molecular-dynamics run (plan P8): g(r), diffusion, the velocity distribution
against Maxwell-Boltzmann, block averages, the canonical kinetic-energy distribution, the cost model of a step.

* ``rdf``: g(r) = (number of pairs at distance r in a shell) / (the ideal-gas count N_a N_b / V x the shell's volume,
  halved for a = b), minimum image on periodic axes (r_max <= L/2 there).
* ``ks_gaussian``: the Kolmogorov-Smirnov distance D_n = sup |F_n - F| of a sample against a centred Gaussian
  (each velocity component of a species is N(0, kT/m) in the canonical ensemble, independent of the positions) and the
  Dvoretzky-Kiefer-Wolfowitz bound with Massart's constant: P(D_n > eps) <= 2 exp(-2 n eps^2), so at level alpha
  eps = sqrt(ln(2/alpha) / (2n)). The bound holds for independent samples: velocities of one snapshot of a canonical
  system are independent (exactly, under Langevin dynamics at equilibrium); in NVE they are so up to O(1/N); snapshots
  closer than the velocity correlation time are not independent (pool snapshots further apart).
* ``block_average``: mean and its standard error from the spread of block means (blocks longer than the correlation
  time).
* ``kinetic_energy_gamma``: the canonical distribution of the kinetic energy of N_f quadratic degrees of freedom,
  K ~ Gamma(N_f/2, scale kT): mean N_f kT/2, variance N_f (kT)^2/2; its CDF for KS tests.
* ``diffusion_from_msd``: D from the slope of the mean-square displacement, MSD = 2 d D t at long times (Einstein),
  by least squares over a chosen window.
* ``bond_order``: the bond-orientational order of a configuration (review B7-md M3): in 2-D psi_6 = <exp(6 i
  theta_jk)> over the bonds (neighbours nearer than r_cut) - |<psi_6>| = 1 for one perfect triangular crystal, ~N^-1/2
  for a liquid (Nelson & Halperin 1979); in 3-D Steinhardt's global Q_6 = (4 pi/13 sum_m |<Y_6m(r_hat)>|^2)^(1/2) over
  the bonds - 0.5745 for fcc, ~N^-1/2 for a liquid (Steinhardt, Nelson & Ronchetti 1983).
* ``md_step_model``: seconds per MD step on this host's CPU (measured by ``bench``), for the playground's budget.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats

from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "statistics",
    "title": T("Statistical mechanics from an MD run: g(r), diffusion, the Maxwell distribution, error estimates"),
    "statement": T("The radial distribution function, the diffusion coefficient from the slope of the mean square "
                   "displacement (Einstein), the Kolmogorov–Smirnov distance of the velocity distribution from the "
                   "Maxwellian with the Dvoretzky–Kiefer–Wolfowitz bound (Massart's constant), block averages, the "
                   "gamma distribution of the kinetic energy in the canonical ensemble, bond orientational order (ψ6 "
                   "in 2-D, Q6 in 3-D), a cost model of a step."),
    "validity": T("the DKW bound holds for independent samples (the velocities of one snapshot of a canonical system "
                  "are independent; snapshots adjacent in time are not); block errors are right when the blocks are "
                  "longer than the correlation time"),
    "basis": ["Dvoretzky, Kiefer & Wolfowitz, Ann. Math. Stat. 27, 642 (1956); Massart, Ann. Probab. 18, 1269 "
              "(1990)", "Einstein (1905): ⟨Δr²⟩ = 2dDt", T("Allen & Tildesley (2017): g(r), block averages"),
              "Nelson & Halperin, PRB 19, 2457 (1979): ψ6; Steinhardt, Nelson & Ronchetti, PRB 28, 784 (1983): Q6"],
    "conflicts": [],
}


def rdf(x, L, periodic, r_max, nbins=100, sel_a=None, sel_b=None, volume=None):
    """g(r) between the particles selected by the boolean masks sel_a and sel_b (default all). Returns (r centres,
    g, pair counts)."""
    x = np.asarray(x, float)
    L = np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    n = x.shape[0]
    d = x.shape[1]
    if np.any(periodic) and r_max > 0.5 * float(np.min(L[periodic])):
        raise ValueError("r_max must not exceed half a periodic box length")
    a = np.ones(n, bool) if sel_a is None else np.asarray(sel_a, bool)
    b = np.ones(n, bool) if sel_b is None else np.asarray(sel_b, bool)
    from .cells import pair_list
    i, j = pair_list(x, L, periodic, r_max)
    same = (sel_a is None and sel_b is None) or (np.array_equal(a, b))
    if same:
        keep = a[i] & a[j]
        i, j = i[keep], j[keep]
        npairs = a.sum() * (a.sum() - 1) / 2.0
    else:
        keep = (a[i] & b[j]) | (b[i] & a[j])
        i, j = i[keep], j[keep]
        npairs = float(a.sum() * b.sum() - np.sum(a & b))
    dx = x[j] - x[i]
    for ax in np.flatnonzero(periodic):
        dx[:, ax] -= L[ax] * np.rint(dx[:, ax] / L[ax])
    r = np.sqrt(np.einsum("ij,ij->i", dx, dx))
    edges = np.linspace(0.0, r_max, nbins + 1)
    cnt, _ = np.histogram(r, edges)
    V = float(np.prod(L)) if volume is None else float(volume)
    if d == 3:
        shell = 4.0 / 3.0 * math.pi * (edges[1:] ** 3 - edges[:-1] ** 3)
    else:
        shell = math.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    ideal = npairs / V * shell
    g = np.where(ideal > 0, cnt / np.where(ideal > 0, ideal, 1.0), 0.0)
    return 0.5 * (edges[1:] + edges[:-1]), g, cnt


def dkw_bound(n, alpha=0.01):
    """eps with P(D_n > eps) <= alpha by the DKW inequality with Massart's constant: sqrt(ln(2/alpha)/(2n)); None for
    an empty sample."""
    if n <= 0:
        return None
    return math.sqrt(math.log(2.0 / alpha) / (2.0 * n))


def ks_gaussian(sample, sd, alpha=0.01):
    """KS distance of a sample against N(0, sd^2) and the DKW bound at level alpha (an empty sample: D, bound and
    within are None)."""
    s = np.sort(np.asarray(sample, float))
    n = len(s)
    if n == 0:
        return {"D": None, "n": 0, "bound": None, "alpha": alpha, "within": None}
    F = 0.5 * special.erfc(-s / (math.sqrt(2.0) * sd))
    k = np.arange(1, n + 1)
    D = float(max(np.max(k / n - F), np.max(F - (k - 1) / n)))
    eps = dkw_bound(n, alpha)
    return {"D": D, "n": n, "bound": eps, "alpha": alpha, "within": D <= eps}


def ks_cdf(sample, cdf, alpha=0.01):
    """KS distance of a sample against any CDF (vectorised callable) and the DKW bound."""
    s = np.sort(np.asarray(sample, float))
    n = len(s)
    if n == 0:
        return {"D": None, "n": 0, "bound": None, "alpha": alpha, "within": None}
    F = cdf(s)
    k = np.arange(1, n + 1)
    D = float(max(np.max(k / n - F), np.max(F - (k - 1) / n)))
    eps = dkw_bound(n, alpha)
    return {"D": D, "n": n, "bound": eps, "alpha": alpha, "within": D <= eps}


def speed_cdf(v, sd, dim):
    """CDF of the speed |v| of a d-dimensional isotropic Gaussian velocity with component sd (Maxwell in 3-D,
    Rayleigh in 2-D)."""
    v = np.asarray(v, float)
    return special.gammainc(dim / 2.0, v * v / (2.0 * sd * sd))


def kinetic_energy_gamma(nf, T):
    """The canonical distribution of the kinetic energy of nf quadratic degrees of freedom at temperature T."""
    return stats.gamma(a=0.5 * nf, scale=T)


def block_average(series, nblocks=10):
    """(mean, standard error of the mean from nblocks block means)."""
    y = np.asarray(series, float)
    m = len(y) // nblocks
    if m < 1:
        raise ValueError("too few samples for the blocks")
    b = y[: m * nblocks].reshape(nblocks, m).mean(axis=1)
    return float(np.mean(y[: m * nblocks])), float(np.std(b, ddof=1) / math.sqrt(nblocks))


def bond_order(x, L, periodic, r_cut) -> dict:
    """Bond-orientational order of the configuration x (n, d) with the neighbours nearer than r_cut (minimum image
    on periodic axes). d = 2: {"psi6_global": |mean of the particles' psi_6|, "psi6_local": mean |psi_6| of the
    particles, "bonds"}; d = 3: {"Q6": the global Steinhardt order over all bonds, "bonds"}."""
    from .cells import pair_list
    x = np.asarray(x, float)
    L = np.asarray(L, float)
    periodic = np.asarray(periodic, bool)
    n, d = x.shape
    i, j = pair_list(x, L, periodic, r_cut)
    out = {"bonds": int(len(i)), "n": n}
    if len(i) == 0:
        return {**out, **({"psi6_global": None, "psi6_local": None} if d == 2 else {"Q6": None})}
    dx = x[j] - x[i]
    for a in np.flatnonzero(periodic):
        dx[:, a] -= L[a] * np.rint(dx[:, a] / L[a])
    if d == 2:
        e = np.exp(6j * np.arctan2(dx[:, 1], dx[:, 0]))    # the same from either end (6 pi)
        s = np.bincount(i, weights=e.real, minlength=n) + np.bincount(j, weights=e.real, minlength=n) \
            + 1j * (np.bincount(i, weights=e.imag, minlength=n) + np.bincount(j, weights=e.imag, minlength=n))
        k = np.bincount(i, minlength=n) + np.bincount(j, minlength=n)
        has = k > 0
        psi = s[has] / k[has]
        return {**out, "psi6_global": float(abs(np.mean(psi))), "psi6_local": float(np.mean(np.abs(psi)))}
    r = np.sqrt(np.einsum("ij,ij->i", dx, dx))
    theta = np.arccos(np.clip(dx[:, 2] / r, -1.0, 1.0))
    phi = np.arctan2(dx[:, 1], dx[:, 0])
    q2 = 0.0
    for m in range(-6, 7):
        q2 += abs(np.mean(special.sph_harm_y(6, m, theta, phi))) ** 2    # Y_6m(-r) = Y_6m(r): l even
    return {**out, "Q6": float(math.sqrt(4.0 * math.pi / 13.0 * q2))}


def diffusion_from_msd(t, msd, dim, t_min=None):
    """D from the least-squares slope of MSD(t) for t >= t_min (default: the second half): MSD = 2 d D t + c."""
    t = np.asarray(t, float)
    y = np.asarray(msd, float)
    if t_min is None:
        t_min = t[0] + 0.5 * (t[-1] - t[0])
    sel = t >= t_min
    A = np.vstack([t[sel], np.ones(sel.sum())]).T
    (slope, c), *_ = np.linalg.lstsq(A, y[sel], rcond=None)
    return float(slope / (2.0 * dim))


# --- cost of a step (CPU, NumPy, i9-9900K; measured by bench in tests/test_md_core.py::test_cost) -------------------
# seconds per step = a + b N + c P (P: pairs in the Verlet list); from the measured costs of LJ fluids (bench(), 20
# steps after a lattice start, rebuilds included) at rho = 0.7 (2-D) and 0.8 (3-D), r_c = 2.5, skin = 0.3:
#   2-D N = 100 / 300 / 1000 / 3000 / 10^4: 0.25 / 0.37 / 0.92 / 2.5 / 8.2 ms (P = 0.8k / 2.5k / 8.7k / 26k / 87k)
#   3-D N = 200 / 300 / 1000 / 3000 / 10^4: 0.71 / 1.4 / 5.5 / 13 / 44 ms (P = 7.1k / 13k / 40k / 122k / 376k)
# (the CPU; with the pair forces on GPU 0 - kernel md.pair_forces, from 2·10^4 pairs - a 3-D step at N = 3·10^3 /
# 10^4 / 3·10^4 takes 5.9 / 15 / 81 ms, a 2-D step at 10^4 / 3·10^4 4.1 / 9.8 ms)
_STEP_MODEL = {2: (2.0e-4, 0.0, 9.2e-8), 3: (2.0e-4, 0.0, 1.17e-7)}


def md_step_model(n, pairs, dim):
    a, b, c = _STEP_MODEL[dim]
    return a + b * n + c * pairs


def bench(pair, ns=(100, 300, 1000, 3000, 10000), dims=(2, 3), steps=20, seed=1):
    """Seconds per MD step (NVE, a fluid of one species at rho = 0.7 in 2-D and 0.8 in 3-D started from a lattice at
    T = 1, the given pair term, skin 0.3) for N particles, and the pairs in the list. The pair term is passed in (the
    core does not import the models)."""
    import time
    from .system import MD
    out = []
    for dim in dims:
        rho = 0.8 if dim == 3 else 0.7
        for n in ns:
            L = (n / rho) ** (1.0 / dim)
            md = MD(dim=dim, box=[L] * dim, pair=pair, dt=0.005, seed=seed)
            md.add_species("A")
            if 2 * (float(np.max(md.pair.tables([1.0], [1.0])["rc"])) + md.skin) > L:
                continue   # the box is smaller than twice the cutoff + skin
            md.fill("A", n=n, T=1.0)
            md.step(5)
            t = time.perf_counter()
            md.step(steps)
            sec = (time.perf_counter() - t) / steps
            out.append({"dim": dim, "n": n, "pairs": md._stats["pairs"], "s_per_step": sec,
                        "rebuilds_per_step": md._stats["rebuilds"] / max(md.nstep, 1), "device": md._device})
    return out
