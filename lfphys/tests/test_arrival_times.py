# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Arrival-time rules and detector models (plan P14.6): the closed-form free packets (core.quantum.schrodinger1d.
FreeGaussians) against quadrature; Bohm first arrival against trajectories integrated one by one (with backflow);
ABK and semiclassical normalisation and their far-field agreement with the flux; the semiclassical density of a
Gaussian train against Das & Struyve 2021, eq. 43; the exponential rules' decaying peaks (Das & Struyve 2021, eqs. 24-25); the absorbing
boundary rule against an independent Crank-Nicolson solution with the Robin condition; the absorbing step's
reflection against a Crank-Nicolson packet."""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import cumulative_trapezoid, solve_ivp
from scipy.linalg import solve_banded

from lfphys.core.quantum.schrodinger1d import FreeGaussians
from lfphys.theories.interpretations import arrival_times as AT
from lfphys.theories.models import detection as D

BACKFLOW = [(1, 0, 0.5, 5.0), (0.5, 0, 6.0, 5.0)]  # two right-moving packets: 1.2 % of the probability flows back


def test_free_gaussians_closed_form():
    fg = FreeGaussians([(1, -20, 2, 2), (0.7j, -40, 3.5, 3)])
    x = np.linspace(-200, 400, 60001)
    for t in (0.0, 5.0, 20.0):
        assert abs(np.trapezoid(np.abs(fg.psi(x, t)) ** 2, x) - 1) < 1e-12
    xx, t, h = np.array([-3.0, 0.5, 12.0]), 7.0, 1e-5
    assert np.max(np.abs((fg.psi(xx + h, t) - fg.psi(xx - h, t)) / (2 * h) - fg.dpsi(xx, t))) < 1e-9
    k = np.linspace(-2, 7, 7)
    ft = np.array([np.trapezoid(fg.psi(x, 0) * np.exp(-1j * q * x), x) for q in k]) / math.sqrt(2 * math.pi)
    assert np.max(np.abs(ft - fg.phi(k))) < 1e-12
    kk, t = np.linspace(-5, 10, 30001), 9.0
    xs = np.array([-10.0, 0.0, 15.0])
    ev = np.array([np.trapezoid(fg.phi(kk) * np.exp(1j * kk * q - 1j * kk * kk * t / 2), kk) for q in xs])
    assert np.max(np.abs(ev / math.sqrt(2 * math.pi) - fg.psi(xs, t))) < 1e-12
    L, t, e = 10.0, 8.0, 1e-4  # continuity: dF/dt = -j(L)
    assert abs((fg.cdf(L, t + e) - fg.cdf(L, t - e))[0] / (2 * e) + fg.current(L, t)) < 1e-9


def test_bohm_first_arrival_follows_trajectories_through_backflow():
    """Each trajectory, started at the quantile u of |psi|^2, first reaches L when the running minimum of F(L, t)
    drops to u; the flux is negative in places (backflow), the first-arrival density never is."""
    fg, L = FreeGaussians(BACKFLOW), 8.0
    t = np.linspace(0, 40, 4001)
    F = fg.cdf(L, t)
    J = fg.current(L, t)
    assert J.min() < -0.02
    cdf, pdf = AT.bohm_first_arrival(t, F)
    assert pdf.min() >= 0 and np.all(np.diff(cdf) >= 0)
    x = np.linspace(-60, L, 20001)
    P = np.concatenate([[0], np.cumsum(0.5 * (np.abs(fg.psi(x[1:], 0)) ** 2 + np.abs(fg.psi(x[:-1], 0)) ** 2)
                                       * np.diff(x))])
    u = np.linspace(0.3, 0.97, 25)
    x0 = np.interp(u, P, x)
    run = np.minimum.accumulate(F)

    def vel(_t, y):
        return [fg.hbar / fg.m * np.imag(fg.dpsi(y[0], _t) / fg.psi(y[0], _t))]

    def hit(_t, y):
        return y[0] - L
    hit.terminal, hit.direction = True, 1
    for ui, xi in zip(u, x0):
        sol = solve_ivp(vel, (0, 40), [xi], method="DOP853", rtol=1e-10, atol=1e-10, events=hit)
        T = sol.t_events[0][0]
        Tpred = np.interp(-ui, -run, t)  # first time the running minimum reaches the start quantile
        assert abs(T - Tpred) < 0.02, (ui, T, Tpred)


def test_flux_equals_bohm_without_backflow():
    fg, L = FreeGaussians([(1, 0, 2.0, 1.0)]), 15.0
    t = np.linspace(0, 30, 6001)
    cdf, pdf = AT.bohm_first_arrival(t, fg.cdf(L, t))
    J = AT.flux_density(fg.current(L, t))
    assert J.min() > -1e-12
    assert np.max(np.abs(pdf - J)) < 1e-3 * J.max()


def _phi_grid(fg, lo, hi, n=40001):
    k = np.linspace(lo, hi, n)
    return k, fg.phi(k)


def test_kijowski_normalisation_and_far_field():
    fg = FreeGaussians([(1, 0, 3.0, 1.0)])
    k, phi = _phi_grid(fg, -4, 10, 8001)
    t = np.linspace(-50, 150, 20001)
    P = AT.kijowski(phi, k, 10.0, t)
    assert abs(np.trapezoid(P, t) - 1) < 1e-6
    neg = np.trapezoid(P[t <= 0], t[t <= 0])  # read as "never detected" by Das & Noeth (eq. 7)
    assert 0 < neg < 1e-6
    # far from the source the ABK density approaches the flux (Das & Noeth 2021: they "practically coincide")
    L = 300.0
    t = np.linspace(80, 120, 801)
    P = AT.kijowski(phi, k, L, t)
    J = fg.current(L, t)
    assert np.max(np.abs(P - J)) < 2e-3 * J.max()


def test_semiclassical_normalisation_and_far_field():
    fg = FreeGaussians([(1, 0, 3.0, 1.0)])
    t = np.linspace(1e-3, 2000, 400001)
    P = AT.semiclassical(fg.phi, 10.0, t)
    kpos = np.linspace(1e-6, 12, 200001)
    assert abs(np.trapezoid(P, t) - np.trapezoid(np.abs(fg.phi(kpos)) ** 2, kpos)) < 1e-4
    L = 300.0
    t = np.linspace(80, 120, 801)
    assert np.max(np.abs(AT.semiclassical(fg.phi, L, t) - fg.current(L, t))) < 2e-2 * fg.current(L, t).max()


def test_semiclassical_train_matches_das_eq43():
    """Das & Struyve 2021, eq. 43, for N packets phi(x + jL, 0) (j = 0..N-1), phase velocity v, eps = hbar/m; their sigma is
    sqrt(2) times the rms width s used here, and his packet j carries the carrier phase e^{i v jL / eps}."""
    N, sig, eps, v = 4, 5.0, 0.01, 1.0
    L = 10 * sig
    s, k0 = sig / math.sqrt(2), v / eps
    fg = FreeGaussians([(np.exp(1j * k0 * j * L), -j * L, k0, s) for j in range(N)], m=1.0, hbar=eps)
    tau = np.linspace(35, 70, 2001)
    tau0 = L / v
    das = (sig * L / (N * math.sqrt(math.pi) * eps * tau ** 2)
           * np.sin(N * L * L / (2 * eps * tau)) ** 2 / np.sin(L * L / (2 * eps * tau)) ** 2
           * np.exp(-(sig * v / eps) ** 2 * (1 - tau0 / tau) ** 2))
    ours = AT.semiclassical(fg.phi, L, tau, m=1.0, hbar=eps)
    assert das.max() > 1
    assert np.max(np.abs(ours - das)) < 1e-9 * das.max()


def test_semiclassical_distribution_in_k_does_not_alias():
    """The semiclassical rule through its CDF in k (review B4-2): for a long train its total within a window is exact,
    where samples of the density over the window alias; its derivative equals the density for one packet; its
    moments agree with quadrature in time."""
    N, sig, eps, v = 8, 5.0, 0.01, 1.0
    L = 10 * sig
    s, k0 = sig / math.sqrt(2), v / eps
    sep = 60.0
    fg = FreeGaussians([(np.exp(1j * k0 * j * sep), -j * sep, k0, s) for j in range(N)], m=1.0, hbar=eps)
    sc = AT.Semiclassical(fg.phi, L, k0 - 8 / (2 * s), k0 + 8 / (2 * s), 200001, m=1.0, hbar=eps)
    t_edges = np.linspace(0.0, 5 * L / v, 1502)
    dens = sc.bin_density(t_edges)
    assert abs(np.sum(dens * np.diff(t_edges)) - sc.cdf(t_edges[-1])[0]) < 1e-12
    assert abs(sc.cdf(1e9)[0] - 1) < 1e-6
    tc = 0.5 * (t_edges[1:] + t_edges[:-1])
    sampled = np.trapezoid(AT.semiclassical(fg.phi, L, tc, m=1.0, hbar=eps), tc)
    assert abs(sampled - 1) > 0.05  # the old way: samples of the comb alias
    one = FreeGaussians([(1, 0, 3.0, 1.0)])
    s1 = AT.Semiclassical(one.phi, 10.0, 0.0, 8.0, 20001)
    t = np.linspace(1.0, 8.0, 701)
    h = 1e-4
    num = (s1.cdf(t + h) - s1.cdf(t - h)) / (2 * h)
    ref = AT.semiclassical(one.phi, 10.0, t)  # the cumulative is linear between the k samples: O(dk) pointwise
    assert np.max(np.abs(num - ref)) < 3e-4 * ref.max()
    tt = np.linspace(1e-3, 60.0, 600001)
    P = AT.semiclassical(one.phi, 10.0, tt)
    tot, mean, sd = s1.moments(60.0)
    assert abs(tot - np.trapezoid(P, tt)) < 1e-7
    assert abs(mean - np.trapezoid(tt * P, tt) / np.trapezoid(P, tt)) < 1e-6
    assert abs(sd - math.sqrt(np.trapezoid((tt - mean) ** 2 * P, tt) / np.trapezoid(P, tt))) < 1e-5


def test_marchewka_schuss_as_in_das_struyve_table_1():
    """lambda_MS = (lambda0' eps / pi) |d psibar/dx (L)|^2 with psibar the Dirichlet solution psi(x) - psi(2L - x), whose
    derivative at L is twice the free one (Das & Struyve 2021, eqs. 27-28; review B4-4)."""
    fg = FreeGaussians([(1, 0, 3.0, 1.0)], hbar=0.5)
    L, t, h = 10.0, 2.0, 1e-5
    psibar = lambda x: fg.psi(x, t) - fg.psi(2 * L - x, t)  # noqa: E731
    dbar = (psibar(L + h) - psibar(L - h)) / (2 * h)
    lam = D.marchewka_schuss_intensity(fg.dpsi(L, t), 0.3, m=1.0, hbar=0.5)
    assert abs(lam - 0.3 * 0.5 / math.pi * abs(dbar) ** 2) < 1e-8 * lam


def test_exponential_rules_damp_a_train():
    """Das & Struyve 2021, Fig. 3 parameters (N = 10, sigma = 5, L = 10 sigma, eps = hbar/m = 0.01, v = 1, lambda0 = 2): with
    Wlodarz's rule the train's peaks fall by exp(-lambda0 / (N v)) from one packet to the next (eqs. 24-25: each
    packet adds int lambda = lambda0 int |psi(L, t)|^2 dt = lambda0 / (N v) without spreading); the flux has equal
    peaks; Pi + P(no click) = 1 for both exponential rules."""
    N, sig, eps, v, lam0 = 10, 5.0, 0.01, 1.0, 2.0
    L, s, k0 = 10 * sig, sig / math.sqrt(2), v / eps
    fg = FreeGaussians([(np.exp(1j * k0 * j * L), -j * L, k0, s) for j in range(N)], m=1.0, hbar=eps)
    tau0 = L / v
    t = np.linspace(0, (N + 1) * tau0, 22001)
    Pi, Pinf = D.exponential(t, D.wlodarz_intensity(fg.psi(L, t), lam0))
    assert abs(np.trapezoid(Pi, t) + Pinf - 1) < 1e-5  # exact up to the O(dt^2) of the quadrature
    win = [(t > (j + 0.5) * tau0) & (t < (j + 1.5) * tau0) for j in range(N)]
    survive = 1 - cumulative_trapezoid(Pi, t, initial=0)
    at = np.interp((np.arange(N) + 0.5) * tau0, t, survive)
    assert np.max(np.abs(at / np.exp(-np.arange(N) * lam0 / (N * v)) - 1)) < 1e-3
    peaks = np.array([Pi[w].max() for w in win])  # the packets spread a little: later peaks are 0.05-0.3 % lower
    assert np.max(np.abs(peaks[1:] / peaks[:-1] - math.exp(-lam0 / (N * v)))) < 4e-3
    J = fg.current(L, t)
    flux_peaks = np.array([J[w].max() for w in win])  # equal but for the slow spreading s(t) of each packet
    width = np.sqrt(1 + (eps * (np.arange(N) + 1) * tau0 / (2 * s * s)) ** 2)
    assert np.max(np.abs(flux_peaks / flux_peaks[0] * width / width[0] - 1)) < 1e-3
    Pi, Pinf = D.exponential(t, D.marchewka_schuss_intensity(fg.dpsi(L, t), 0.01, m=1.0, hbar=eps))
    assert abs(np.trapezoid(Pi, t) + Pinf - 1) < 1e-5 and 0 < Pinf < 1


def _crank_nicolson(x, psi, dt, steps, V=None, robin=None, record=None):
    """Second-order finite differences, Crank-Nicolson in time (hbar = m = 1); Dirichlet on the left; on the right
    either Dirichlet or the Robin condition psi' = i kappa psi (ghost point psi_{N+1} = psi_{N-1} + 2 h i kappa psi_N).
    ``record(n, psi)`` is called after every step."""
    n, h = len(x), x[1] - x[0]
    diag = np.full(n, 1 / h ** 2, complex) + (0 if V is None else V)
    off = np.full(n - 1, -0.5 / h ** 2, complex)
    sup = off.copy()
    if robin is not None:  # last row: (-psi_{N-1} + psi_N) / h^2 - i kappa psi_N / h  (from the ghost point)
        diag[-1] = 1 / h ** 2 - 1j * robin / h + (0 if V is None else V[-1])
        sub_last = -1 / h ** 2
    else:
        sub_last = off[-1]
    sub = off.copy()
    sub[-1] = sub_last

    def apply(p):
        out = diag * p
        out[:-1] += sup * p[1:]
        out[1:] += sub * p[:-1]
        return out
    ab = np.zeros((3, n), complex)
    ab[0, 1:] = 0.5j * dt * sup
    ab[1] = 1 + 0.5j * dt * diag
    ab[2, :-1] = 0.5j * dt * sub
    for i in range(steps):
        psi = solve_banded((1, 1), ab, psi - 0.5j * dt * apply(psi))
        if record is not None:
            record(i + 1, psi)
    return psi


def test_absorbing_boundary_against_crank_nicolson():
    """The image formula for psi(L, t) on the Robin boundary, and the click total int |phi|^2 (1 - R_k), against an
    independent Crank-Nicolson solution on the half-line with the boundary condition itself."""
    s, k0, L, kappa = 2.0, 2.0, 12.0, 1.5
    fg = FreeGaussians([(1, 0, k0, s)])
    h, dt, T = 0.005, 0.002, 14.0
    x = np.arange(-40, L + h / 2, h)
    rec = []
    _crank_nicolson(x, fg.psi(x, 0).astype(complex), dt, int(round(T / dt)), robin=kappa,
                    record=lambda i, p: rec.append(p[-1]) if i % 10 == 0 else None)
    tt = dt * 10 * np.arange(1, len(rec) + 1)
    k, phi = _phi_grid(fg, 1e-6, 6, 20001)
    psiL = D.abr_boundary_wave(phi, k, L, kappa, tt)
    assert np.max(np.abs(np.array(rec) - psiL)) < 2e-3 * np.abs(psiL).max()
    dens = D.abr_density(phi, k, L, kappa, tt)
    assert abs(np.trapezoid(dens, tt) - D.abr_total(phi, k, kappa)) < 2e-3
    refl = np.trapezoid(np.abs(phi) ** 2 * D.robin_reflection(k, kappa), k)
    assert abs(D.abr_total(phi, k, kappa) - (1 - refl)) < 1e-9
    assert abs(D.robin_reflection(kappa, kappa)) == 0


def test_absorbing_step_reflection_against_crank_nicolson():
    s, k0, L, W0 = 4.0, 2.0, 0.0, 0.6
    fg = FreeGaussians([(1, -30, k0, s)])
    h, dt = 0.01, 0.004
    x = np.arange(-90, 40, h)
    V = np.where(x > L, -1j * W0, 0.0)
    psi = _crank_nicolson(x, fg.psi(x, 0).astype(complex), dt, int(round(30 / dt)), V=V)
    left = np.trapezoid(np.abs(psi[x < L - 10]) ** 2, x[x < L - 10])
    k, phi = _phi_grid(fg, 1e-6, 5, 20001)
    R = np.trapezoid(np.abs(phi) ** 2 * D.step_reflection(k, W0), k)
    assert R > 0.003
    assert abs(left - R) < 0.02 * R
