# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Bohm trajectories in time-dependent 2-D waves (lfphys.theories.interpretations.bohm, plan P6/P14.4): the free
packet's exact trajectories; equivariance (|psi|^2-distributed starts stay |psi|^2-distributed) behind an obstacle;
time reversal; the spinor guidance law."""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.quantum import schrodinger_nd as S
from lfphys.theories.interpretations import bohm


def _follow(g, H, psi0, X0, dt, pairs, reverse_from=None):
    """Integrate trajectories with RK4 over h = 2 dt, the wave from the split operator (steps of dt)."""
    pr = S.SplitOperator(H, dt, force_cpu=True, why="test")
    a = pr.put(psi0)
    X = np.array(X0, float)
    for _ in range(pairs):
        b = pr.step(a, 1)
        c = pr.step(b, 1)
        snaps = {0.0: pr.get(a), 0.5: pr.get(b), 1.0: pr.get(c)}
        X = bohm.rk4(X, 2 * dt, lambda Y, f: bohm.velocity_nd(g, snaps[f], Y, H)[0])
        a = c
    return X, pr.get(a)


def test_free_packet_trajectories_are_exact():
    """In a free Gaussian packet every trajectory keeps its quantile: x(t) = x0 + v t + (x_start - x0) |s_t| / sigma.
    Errors: the Lagrange interpolation of psi and grad psi (9 samples per axis; relative remainders 194 (k dx)^9 / 9!
    and, for the derivative, 576 (k dx)^8 / 9!), integrated over t at the largest speed; RK4 with h = 0.02 adds ~h^4
    (negligible)."""
    g = S.Grid((192, 192), 0.1)
    c, k, s = (-3.0, 1.0), (4.0, -2.0), (0.8, 1.1)
    psi0 = g.gaussian(c, k, s)
    rng = np.random.default_rng(3)
    X0 = rng.normal(c, s, (200, 2))
    X, _ = _follow(g, S.Hamiltonian(g), psi0, X0, 0.01, 50)  # t = 1
    ref = bohm.gaussian_trajectory(X0, 1.0, c, k, s)
    kd = math.hypot(*k) * 0.1
    vmax = math.hypot(*k) + 3.0  # the packet's speed plus its spreading speed at 3 sigma
    tol = 1.0 * vmax * (576 * kd**8 + 194 * kd**9) / math.factorial(9)
    assert np.max(np.abs(X - ref)) < tol, (np.max(np.abs(X - ref)), tol)


def test_equivariance_behind_an_obstacle():
    """Starts drawn from |psi0|^2 (a Gaussian: exactly normal), the packet scattered by a Gaussian bump (a
    non-separable potential): the trajectories' positions at t are distributed by |psi(t)|^2. Kolmogorov-Smirnov
    distance of both marginals below the 99.9 % critical value 1.95 / sqrt(N) (seeded, so deterministic)."""
    g = S.Grid((160, 160), 0.15)
    X, Y = g.mesh()
    V = 6.0 * np.exp(-((X - 0.0) ** 2 + (Y - 0.4) ** 2) / 0.5)
    H = S.Hamiltonian(g, V=V)
    c, k, s = (-4.0, 0.0), (3.0, 0.0), (1.0, 1.0)
    psi0 = g.gaussian(c, k, s)
    N = 3000
    X0 = np.random.default_rng(11).normal(c, s, (N, 2))
    Xt, psit = _follow(g, H, psi0, X0, 0.005, 250)  # t = 2.5: the packet has crossed the bump
    rho = g.density(psit)
    for axis in (0, 1):
        marg = rho.sum(axis=1 - axis)
        F = np.cumsum(marg) / marg.sum()
        grid = g.axes[axis] + 0.5 * g.d[axis]  # F at the cell's upper edge
        emp = np.searchsorted(np.sort(Xt[:, axis]), grid, side="right") / N
        D = float(np.max(np.abs(emp - F)))
        assert D < 1.95 / math.sqrt(N), (axis, D)


def test_time_reversal():
    """Forward to t, then the reversed wave (complex conjugate) forward again: the trajectories return to their
    starts (Bohm's law is time-reversible; errors as above)."""
    g = S.Grid((160, 160), 0.15)
    X, Y = g.mesh()
    H = S.Hamiltonian(g, V=4.0 * np.exp(-((X - 0.5) ** 2 + Y**2) / 0.8))
    c, k, s = (-3.0, 0.3), (3.0, 0.0), (1.0, 1.0)
    psi0 = g.gaussian(c, k, s)
    X0 = np.random.default_rng(5).normal(c, s, (100, 2))
    X1, psi1 = _follow(g, H, psi0, X0, 0.005, 150)
    X2, _ = _follow(g, H, np.conj(psi1), X1, 0.005, 150)
    assert np.max(np.abs(X2 - X0)) < 1e-4, np.max(np.abs(X2 - X0))


def test_spinor_guidance_sums_the_components():
    """psi = (a phi, b phi) with |a|^2 + |b|^2 = 1 guides like phi; two different components weight their currents
    by their densities (Bohm-Schiller-Tiomno)."""
    g = S.Grid((96, 96), 0.15)
    phi = g.gaussian((0, 0), (2.0, 1.0), (1.0, 1.0))
    chi = g.gaussian((0.5, 0), (-1.0, 0.5), (1.0, 1.2))
    P = np.random.default_rng(2).uniform(-1.5, 1.5, (30, 2))
    v1, _ = bohm.velocity_nd(g, phi, P)
    v2, _ = bohm.velocity_nd(g, np.stack([0.6 * phi, 0.8j * phi]), P)
    assert np.max(np.abs(v1 - v2)) < 1e-10
    va, ra = bohm.velocity_nd(g, phi, P)
    vb, rb = bohm.velocity_nd(g, chi, P)
    vs, rs = bohm.velocity_nd(g, np.stack([phi, chi]) / math.sqrt(2), P)
    assert np.max(np.abs(vs - (va * ra[:, None] + vb * rb[:, None]) / (ra + rb)[:, None])) < 1e-10


def test_error_controlled_steps_follow_a_vortex():
    """The 2-D oscillator's vortex state psi = (x + iy) exp(-r^2/2) / sqrt(pi) (m = hbar = omega = 1, E = 2) is
    stationary; Bohm's velocity is grad(angle) = (-y, x)/r^2: every trajectory is a circle run at angular speed 1/r^2,
    which grows without bound at the node (r = 0.05: 400 rad per unit time, 4 rad per step of 0.01). The error-
    controlled integration (review B3-4) keeps each particle on its circle and on its exact angle; without sub-steps
    the same steps fly off. Snapshots are the exact state at the three times of each step."""
    g = S.Grid((96, 96), 0.15)
    X, Y = g.mesh()
    psi = ((X + 1j * Y) * np.exp(-(X**2 + Y**2) / 2) / math.sqrt(math.pi)).astype(complex)
    r0 = np.array([0.05, 0.08, 0.1, 0.2, 0.5, 1.0, 1.5])
    th0 = np.random.default_rng(3).uniform(0, 2 * math.pi, len(r0))
    P = np.column_stack([r0 * np.cos(th0), r0 * np.sin(th0)])
    h, T = 0.01, 0.5
    for k in range(int(round(T / h))):
        t = k * h
        snaps = tuple(psi * np.exp(-2j * (t + f * h)) for f in (0.0, 0.5, 1.0))
        P, _ = bohm.advance_ensemble(g, snaps, P, h)
    r = np.hypot(P[:, 0], P[:, 1])
    th = np.arctan2(P[:, 1], P[:, 0])
    dth = np.remainder(th - (th0 + T / r0**2) + math.pi, 2 * math.pi) - math.pi
    assert np.max(np.abs(r - r0) / r0) < 2e-3, r - r0
    # the error along the circle relative to the path run (T / r0: 10 at r0 = 0.05, ~32 turns); measured 8.7e-4 there,
    # 1e-4 and below elsewhere
    assert np.max(np.abs(dth) * r0**2 / T) < 2e-3, dth * r0**2 / T
    # the bare RK4 at h (no sub-steps) cannot follow the fastest ones
    Q = np.column_stack([r0 * np.cos(th0), r0 * np.sin(th0)])
    for k in range(int(round(T / h))):
        t = k * h
        snap = {f: psi * np.exp(-2j * (t + f * h)) for f in (0.0, 0.5, 1.0)}
        Q = bohm.rk4(Q, h, lambda Z, f: bohm.velocity_nd(g, snap[f], Z)[0])
    assert abs(np.hypot(*Q[0]) - r0[0]) / r0[0] > 0.1


def test_patches_on_the_host_equal_the_grid():
    """The few particles left to many small steps are stepped from copies of their surroundings on the host; the
    result equals stepping them from the grid itself (to round-off), also when they leave their first patch."""
    g = S.Grid((96, 96), 0.15)
    X, Y = g.mesh()
    psi = ((X + 1j * Y) * np.exp(-(X**2 + Y**2) / 2) / math.sqrt(math.pi)).astype(complex)
    psi = psi + 0.3 * g.gaussian((1.0, -0.5), (2.0, 1.0), (1.0, 1.0))
    r0 = np.array([0.05, 0.1, 0.3, 0.7, 1.2, 2.0])
    P0 = np.column_stack([r0, 0.2 * r0])
    snaps = tuple(psi * np.exp(-2j * f * 0.05) for f in (0.0, 0.5, 1.0))
    a, sa = bohm.advance_ensemble(g, snaps, P0, 0.05)
    keep = bohm.PATCH_MAX
    try:
        bohm.PATCH_MAX = -1  # never use patches
        b, sb = bohm.advance_ensemble(g, snaps, P0, 0.05)
    finally:
        bohm.PATCH_MAX = keep
    assert np.array_equal(sa, sb) and sa.max() > 4
    assert np.max(np.abs(a - b)) < 1e-12


def _free_run(kd: float, demodulate: bool, d: float = 80 / 256):
    """Review B6-Q1 (its s04): a free 2-D packet (sigma 2.5, 4) on a grid of step d at k d, 60 points from |psi|^2,
    advanced in Bohm intervals of 8 split steps (the playground's), against the exact trajectories after ~30 nm."""
    from lfphys.core.quantum import scene as Q
    from scipy import constants as sc
    m1 = Q.species("atom", mass_u=sc.m_e / sc.atomic_mass)
    sg, c = (2.5, 4.0), (-18.0, 0.0)
    k = (kd / d, 0.0)
    E = sum((abs(kk) + 3 / (2 * s)) ** 2 for kk, s in zip(k, sg)) / 2
    dt = 2.0 ** math.floor(math.log2(0.1 / E))
    s = Q.Scene((256, 256), d, dt=dt)
    pid = s.add_particle(Q.Packet(m1, list(c), list(k), list(sg)))
    X0 = np.random.default_rng(5).normal(c, sg, (60, 2))
    X = X0.copy()
    for _ in range(int(round(30.0 / k[0] / dt / 8))):
        s.advance(8, snapshots=True)
        snaps, h = s.snapshots(pid)
        grid, H, xp = s.guidance(pid)
        X, _ = bohm.advance_ensemble(grid, snaps, X, h, H, xp=xp, demodulate=demodulate)
    ref = bohm.gaussian_trajectory(X0, s.t, c, k, sg)
    return float(np.max(np.linalg.norm(X - ref, axis=1))), float(np.mean(np.linalg.norm(ref - X0, axis=1)))


def test_demodulated_interpolation_keeps_trajectories_at_any_admitted_k_d():
    """Review B6-Q1: the Lagrange interpolation of psi errs by its remainder at the wave's k d (the trajectories' error
    over 30 nm: 3.3e-2 nm at k d = 1, 2.2 nm at 2, 7.9 nm at 2.5 — negative control at k d = 2); interpolated with
    the carrier of each point's local wavevector (exact on the samples), the error is the integrator's: measured
    3e-5, 9e-5, 2e-5 nm at k d = 1, 2, 2.5; asserted below the integrator's tolerance accumulated over the path
    (rtol 1e-5 of 30 nm plus atol 1e-6 d per step: < 1e-3 nm)."""
    for kd in (1.0, 2.0, 2.5):
        err, disp = _free_run(kd, True)
        assert err < 1e-3 and disp > 25, (kd, err)
    err, _ = _free_run(2.0, False)
    assert err > 1.0, err


def test_patches_in_three_dimensions_and_for_a_spinor():
    """Review B6-Q15 (its s12): the host patches (used whenever <= 64 points are left: always for the playground's
    ensembles) in 3-D equal the device path to round-off and follow the exact free trajectories (the integrator's
    tolerance); a two-component wave of one Gaussian (weights 0.6, 0.8) has the same guidance field."""
    g = S.Grid((48, 48, 48), 0.25)
    c, k, sg = (-1.0, 0.5, 0.0), (1.5, -1.0, 0.8), (1.0, 1.2, 0.9)
    psi0 = g.gaussian(c, k, sg)
    H = S.Hamiltonian(g)
    op = S.SplitOperator(H, 0.005, force_cpu=True)
    X0 = np.random.default_rng(1).normal(c, sg, (30, 3))
    res = {}
    for mode in ("patches", "device"):
        keep = bohm.PATCH_MAX
        if mode == "device":
            bohm.PATCH_MAX = -1
        try:
            psi, X = psi0.copy(), X0.copy()
            for _ in range(20):
                a = psi
                b = op.step(a, 2)
                cc = op.step(b, 2)
                X, _ = bohm.advance_ensemble(g, (a, b, cc), X, 0.02, H)
                psi = cc
        finally:
            bohm.PATCH_MAX = keep
        res[mode] = X
    ref = bohm.gaussian_trajectory(X0, 0.4, c, k, sg)
    assert np.max(np.abs(res["patches"] - res["device"])) < 1e-12
    assert np.max(np.linalg.norm(res["patches"] - ref, axis=1)) < 1e-3
    Hs = S.Hamiltonian(g, b=np.zeros((3,) + g.shape))
    ops = S.SplitOperator(Hs, 0.005, force_cpu=True)
    X, psi = X0.copy(), np.stack([0.6 * psi0, 0.8 * psi0])
    for _ in range(20):
        a = psi
        b = ops.step(a, 2)
        cc = ops.step(b, 2)
        X, _ = bohm.advance_ensemble(g, (a, b, cc), X, 0.02, Hs)
        psi = cc
    assert np.max(np.abs(X - res["patches"])) < 1e-10
