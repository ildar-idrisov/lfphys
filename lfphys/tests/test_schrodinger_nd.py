# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.quantum.schrodinger_nd (plan P6): every route against a closed form or a second, independent method.

* free packets in 2-D and 3-D against the exact Gaussian; a separable 2-D problem against the product of 1-D runs
  (schrodinger1d, an independent code) to round-off;
* the split operator against the Chebyshev expansion (exact for the same spatial operator): second order in dt, with
  and without a vector potential;
* levels: the 2-D and 3-D harmonic oscillator, the Fock-Darwin levels (uniform field + harmonic trap: tests the vector
  potential), hydrogen in 3-D (the Coulomb cusp converges slowly on a grid: measured order and an extrapolation);
* spin: exact precession in a uniform coupling, Stern-Gerlach in a gradient (Ehrenfest, exact for a linear potential);
* a smooth barrier tilted at 0, 30 and 45 degrees to the grid against the closed-form transmission of the sech^2
  barrier (Landau & Lifshitz, QM, sec. 25, problem 4) and the 1-D transfer matrices: the same in every orientation;
* absorbers: norm + absorbed = 1; the layer's reflection from transfer matrices against a time-dependent run;
* Aharonov-Bohm: a flux quantum in a tube the wave cannot reach changes nothing (gauge periodicity), mirror symmetry
  Phi -> -Phi, y -> -y;
* interpolation of psi and its gradient at arbitrary points; the current and the flux through a plane; GPU = CPU.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from lfphys.core import backend
from lfphys.core.quantum import schrodinger1d as S1
from lfphys.core.quantum import schrodinger_nd as S
from lfphys.core.quantum import transfer

EPS = np.finfo(float).eps


def _cpu(H, dt, **kw):
    return S.SplitOperator(H, dt, force_cpu=True, why="test", **kw)


def _run(pr, psi, n):
    return pr.get(pr.step(pr.put(psi), n))


# --- free motion and separability ------------------------------------------------------------------------------------
@pytest.mark.parametrize("shape,spacing,center,k0,sigma,t", [
    ((256, 256), 0.12, (-3.0, 2.0), (4.0, -3.0), (1.0, 1.3), 1.2),
    ((64, 64, 64), 0.4, (-2.0, 0.0, 1.0), (2.0, 1.0, -1.5), (1.2, 1.5, 1.0), 1.5),
])
def test_free_packet_is_exact(shape, spacing, center, k0, sigma, t):
    """The kinetic step is exact on the grid, so a free packet matches the closed form up to round-off and to its
    periodic images (the packet's tail at the window's edge, computed here and included in the tolerance)."""
    g = S.Grid(shape, spacing)
    psi0 = g.gaussian(center, k0, sigma)
    dt = t / 60
    out = _run(_cpu(S.Hamiltonian(g), dt), psi0, 60)
    ref = g.free_gaussian(t, center, k0, sigma)
    tail = 0.0
    for i in range(g.ndim):
        half = 0.5 * g.shape[i] * g.d[i]
        st = abs(sigma[i] ** 2 + 0.5j * t)
        mid = center[i] + k0[i] * t
        gap = half - abs(mid)
        tail += math.exp(-gap**2 * sigma[i] ** 2 / (4 * st**2)) * (2 * math.pi * sigma[i] ** 2) ** -0.25
    err = float(np.max(np.abs(out - ref)))
    assert err <= 1e3 * EPS * np.max(np.abs(ref)) + 10 * tail, (err, tail)
    assert abs(g.norm(out) - 1.0) < 1e-12


def test_separable_problem_is_the_product_of_1d_runs():
    """V = Vx(x) + Vy(y): one Strang step in 2-D is the product of the 1-D steps (the parts commute), so the 2-D run
    equals the product of two runs of the independent 1-D code to round-off."""
    gx, gy = S1.Grid(np.arange(-64, 64) * 0.2, m=1.0), S1.Grid(np.arange(-48, 48) * 0.25, m=1.0)
    g = S.Grid((128, 96), (0.2, 0.25))
    assert np.array_equal(g.axes[0], gx.x) and np.array_equal(g.axes[1], gy.x)
    Vx, Vy = 0.3 * gx.x**2, 1.5 * np.exp(-gy.x**2)
    px, py = gx.gaussian(-2, 3.0, 1.0), gy.gaussian(1, -1.0, 1.2)
    p0 = px[:, None] * py[None, :]
    sx, sy = gx.stepper(Vx, 0.01), gy.stepper(Vy, 0.01)
    for _ in range(80):
        px, py = sx(px), sy(py)
    out = _run(_cpu(S.Hamiltonian(g, V=Vx[:, None] + Vy[None, :]), 0.01), p0, 80)
    assert np.max(np.abs(out - px[:, None] * py[None, :])) < 200 * EPS


# --- the split operator against the Chebyshev expansion -------------------------------------------------------------------
@pytest.mark.parametrize("field", [False, True])
def test_split_operator_converges_to_chebyshev_at_second_order(field):
    """A coherent state in a harmonic trap (with a uniform magnetic field: the vector potential by gauge phases) against
    the Chebyshev expansion of exp(-iHt) for the same spatial operator (with the field: (p - qA)^2 by spectral
    derivatives, an independent form). The difference falls by 4 per halving of dt (Strang: second order)."""
    g = S.Grid((96, 96), 0.25)
    X, Y = g.mesh()
    H = S.Hamiltonian(g, V=0.5 * (X**2 + Y**2), A=S.uniform_field(1.0) if field else None)
    psi0 = g.gaussian((1.5, 0.0), (0.0, 1.0), (1 / math.sqrt(2),) * 2)
    ref = S.chebyshev(H, psi0, 2.0)
    assert abs(g.norm(ref) - 1) < 1e-11
    errs = [float(np.max(np.abs(_run(_cpu(H, dt), psi0, int(round(2.0 / dt))) - ref))) for dt in (0.02, 0.01, 0.005)]
    r1, r2 = errs[0] / errs[1], errs[1] / errs[2]
    assert 3.6 < r1 < 4.4 and 3.6 < r2 < 4.4, errs
    assert errs[-1] < 1e-4


def test_chebyshev_free_packet_is_exact():
    g = S.Grid((128, 128), 0.2)
    psi0 = g.gaussian((-2.0, 1.0), (3.0, -2.0), (1.0, 1.2))
    out = S.chebyshev(S.Hamiltonian(g), psi0, 1.0)
    assert np.max(np.abs(out - g.free_gaussian(1.0, (-2.0, 1.0), (3.0, -2.0), (1.0, 1.2)))) < 1e-10


# --- stationary states -------------------------------------------------------------------------------------------------
def test_harmonic_levels_2d_and_3d():
    """hbar omega (n + d/2) with their degeneracies. The grid's error for these Gaussian-like states is of the order
    of their Fourier transform at k_max = pi/dx, exp(-(pi/dx)^2 / 2) ~ 3e-9 at dx = 0.5; LOBPCG to 1e-9."""
    g = S.Grid((40, 40), 0.5)
    X, Y = g.mesh()
    E, _, res = S.eigenstates(S.Hamiltonian(g, V=0.5 * (X**2 + 4 * Y**2)), 6)
    assert np.allclose(E, [1.5, 2.5, 3.5, 3.5, 4.5, 4.5], atol=1e-7), E
    assert res.max() < 1e-7
    g3 = S.Grid((24, 24, 24), 0.5)
    X, Y, Z = g3.mesh()
    E, _, _ = S.eigenstates(S.Hamiltonian(g3, V=0.5 * (X**2 + Y**2 + Z**2)), 10)
    assert np.allclose(E, [1.5] + [2.5] * 3 + [3.5] * 6, atol=1e-7), E


def test_fock_darwin_levels():
    """A charge in a uniform field B and a harmonic trap omega0 (symmetric gauge): E = hbar Omega (2 n_r + |m| + 1)
    - m hbar omega_c / 2, Omega = sqrt(omega0^2 + omega_c^2 / 4) (Fock 1928, Darwin 1931); q = m = hbar = 1."""
    g = S.Grid((96, 96), 0.25)
    X, Y = g.mesh()
    B = 1.0
    E, _, _ = S.eigenstates(S.Hamiltonian(g, V=0.5 * (X**2 + Y**2), A=S.uniform_field(B)), 6)
    Om = math.sqrt(1.0 + B * B / 4)
    ref = sorted(Om * (2 * nr + abs(m) + 1) - m * B / 2 for nr in range(4) for m in range(-8, 9))[:6]
    assert np.allclose(E, ref, atol=1e-7), (E, ref)


def test_hydrogen_3d_converges_to_the_bohr_levels():
    """Hydrogen on a 3-D grid (nucleus at a cell centre, no grid point at r = 0). The Coulomb cusp makes the grid
    converge slowly: the 1s error falls as dx^p with p measured between 1.5 and 2 (spectral methods with a
    sampled 1/r); the Richardson extrapolation with that order lands on -1/2 within 2e-3; the three 2p states are
    exactly degenerate (the cubic symmetry about the nucleus). The box (+-8 a.u.) holds 1s; n = 2 needs a larger one."""
    out = {}
    for n, d in ((32, 0.5), (48, 0.5 * 32 / 48), (64, 0.25)):
        g = S.Grid((n, n, n), d)
        X, Y, Z = g.mesh()
        r = np.sqrt((X - d / 2) ** 2 + (Y - d / 2) ** 2 + (Z - d / 2) ** 2)
        E, _, _ = S.eigenstates(S.Hamiltonian(g, V=-1.0 / r), 5 if n == 64 else 1, tol=1e-8)
        out[d] = E
    ds = sorted(out, reverse=True)
    err = [out[d][0] + 0.5 for d in ds]
    assert all(e > 0 for e in err) and err[0] > err[1] > err[2]
    p = math.log(err[1] / err[2]) / math.log(ds[1] / ds[2])
    assert 1.5 < p < 2.0, p
    ext = out[ds[2]][0] - (out[ds[1]][0] - out[ds[2]][0]) / ((ds[1] / ds[2]) ** p - 1)
    assert abs(ext + 0.5) < 2e-3, ext
    E64 = out[ds[2]]
    assert np.ptp(E64[2:5]) < 1e-8  # 2p: three states
    assert abs(E64[2] + 0.125) < 0.01  # box-limited (2p reaches r ~ 10)


# --- spin -------------------------------------------------------------------------------------------------------------
def test_spin_precession_is_exact():
    """A uniform coupling b sigma_y commutes with everything else: the spinor turns as exp(-i b sigma_y t / hbar)."""
    g = S.Grid((64, 64), 0.3)
    psi = g.gaussian((0, 0), (1.0, 0), (2, 2))
    b = np.zeros((3,) + g.shape)
    b[1] = 0.7
    out = _run(_cpu(S.Hamiltonian(g, b=b), 0.05), np.stack([psi, 0 * psi]), 40)
    up, dn = (float(np.sum(np.abs(out[i]) ** 2) * g.dV) for i in (0, 1))
    assert abs(up - math.cos(1.4) ** 2) < 1e-12 and abs(dn - math.sin(1.4) ** 2) < 1e-12


def test_stern_gerlach_in_a_gradient():
    """b = (0, 0, kappa y): the up component feels +kappa y, the down one -kappa y; for a linear potential Ehrenfest's
    theorem is exact: <y> = y0 -+ kappa t^2 / 2m, <x> = x0 + v t for both."""
    g = S.Grid((128, 128), 0.25)
    X, Y = g.mesh()
    kappa = 0.4
    b = np.zeros((3,) + g.shape)
    b[2] = kappa * Y
    psi = g.gaussian((-3.0, 0.0), (2.0, 0.0), (1.2, 1.2)) / math.sqrt(2)
    t = 2.5
    out = _run(_cpu(S.Hamiltonian(g, b=b), 0.01), np.stack([psi, psi]), 250)
    for c, sgn in ((0, -1), (1, +1)):
        mx = g.mean_x(out[c])
        assert abs(mx[1] - sgn * kappa * t * t / 2) < 1e-9, mx
        assert abs(mx[0] - (-3.0 + 2.0 * t)) < 1e-9, mx


# --- a tilted barrier ----------------------------------------------------------------------------------------------------
def _sech2_T(k, U0, alpha, m=1.0, hbar=1.0):
    s = 8 * m * U0 / (hbar * alpha) ** 2
    a = np.sinh(math.pi * k / alpha) ** 2
    if s > 1:
        return a / (a + math.cosh(0.5 * math.pi * math.sqrt(s - 1)) ** 2)
    return a / (a + math.cos(0.5 * math.pi * math.sqrt(1 - s)) ** 2)


def test_sech2_closed_form_agrees_with_transfer_matrices():
    """The closed form used below against the independent 1-D transfer matrices (Richardson over two resolutions)."""
    U0, alpha = 4.0, 1.0
    for k in (2.2, 2.8, 3.4):
        E = 0.5 * k * k

        def V(x):
            return U0 / np.cosh(alpha * np.asarray(x)) ** 2
        T1 = transfer.transmission_profile(np.array([E]), V, -14, 14, 4000)[0]
        T2 = transfer.transmission_profile(np.array([E]), V, -14, 14, 8000)[0]
        Tr = T2 + (T2 - T1) / 3
        assert abs(Tr - _sech2_T(k, U0, alpha)) < 1e-6, (k, Tr, _sech2_T(k, U0, alpha))


@pytest.mark.parametrize("angle", [0.0, 30.0, 45.0])
def test_tilted_barrier_transmits_as_in_1d(angle):
    """A packet (isotropic Gaussian, mean momentum along n) on the barrier U0 / cosh^2(alpha (r.n - c)) tilted by
    ``angle`` to the grid: the motion along the barrier is free, so the transmitted probability is the 1-D
    transmission averaged over the packet's normal momenta, E[T(k_n)], k_n ~ N(k0, 1/(2 sigma)) (Gauss-Hermite).
    The packet starts 7 sigma from the barrier (at 4 sigma its front already felt the barrier's tail and the
    transmission came out 3.6e-4 higher: the state was not free). The run's own error (dt^2) is measured by halving
    dt; absorbers at the edges take the separated parts (what they absorb on each side of the barrier is counted)."""
    U0, alpha, k0, sig = 4.0, 1.0, 2.8, 3.0
    a = math.radians(angle)
    n = np.array([math.cos(a), math.sin(a)])
    g = S.Grid((320, 320), 0.25)
    X, Y = g.mesh()
    xi = X * n[0] + Y * n[1]
    V = U0 / np.cosh(alpha * xi) ** 2
    W = sum(S.absorbing_layer(g, ax, s, 5.0, 6.0) for ax in (0, 1) for s in ("low", "high"))
    c0 = -21.0 * n
    psi0 = g.gaussian(c0, k0 * n, sig)
    t_end = 21.0 / k0 + 8.5  # the slow components have left the barrier (measured: < 1e-6 within |xi| < 5)
    P = []
    for dt in (0.02, 0.01):
        pr = S.SplitOperator(S.Hamiltonian(g, V=V, W=W), dt, track_absorbed=True)
        p = _run(pr, psi0, int(round(t_end / dt)))
        beyond = g.density(p) * g.dV + pr.absorbed()
        P.append(float(np.sum(beyond[xi > 0])))
        assert abs(g.norm(p) + pr.absorbed().sum() - 1) < 1e-10
        assert float(np.sum((g.density(p) * g.dV)[np.abs(xi) < 5])) < 1e-4
    x, w = np.polynomial.hermite_e.hermegauss(40)
    sk = 1.0 / (2 * sig)
    ref = float(np.sum(w * np.array([_sech2_T(k0 + sk * xx, U0, alpha) for xx in x])) / np.sum(w))
    err_dt = abs(P[1] - P[0]) / 3
    # the absorbers reflect below 1e-5 for these momenta (layer_reflection); what is still near the barrier < 1e-4
    R, _ = S.layer_reflection(np.array([k0 - 4 * sk, k0, k0 + 4 * sk]), 5.0, 6.0, 1.0)
    assert R.max() < 1e-5
    assert abs(P[1] - ref) <= 3 * err_dt + R.max() + 1e-4, (P, ref, err_dt)


# --- absorbers ----------------------------------------------------------------------------------------------------------
def test_absorbed_plus_norm_is_one():
    g = S.Grid((128, 128), 0.2)
    W = S.absorbing_layer(g, 1, "high", 4.0, 5.0)
    pr = _cpu(S.Hamiltonian(g, W=W), 0.01, track_absorbed=True)
    p = pr.step(pr.put(g.gaussian((0, 0), (0, 6.0), (1.5, 1.5))), 300)
    assert abs(pr.norm(p) + pr.absorbed().sum() - 1.0) < 1e-12
    assert pr.absorbed().sum() > 0.5
    Z = np.broadcast_to(g.mesh()[1], g.shape)
    beyond = Z > g.axes[1][-1] - 4.0
    assert abs(pr.absorbed_in(beyond) - pr.absorbed()[beyond].sum()) < 1e-14
    assert abs(pr.absorbed_in((slice(None), slice(64, None))) - pr.absorbed()[:, 64:].sum()) < 1e-14


def test_layer_reflection_matches_a_time_dependent_run():
    """The reflection of an absorbing layer from stationary transfer matrices, averaged over a packet's spectrum,
    against the probability a 1-D run of this module sends back (a weak layer, so that R is measurable)."""
    width, W0, k0, sig = 2.0, 1.5, 3.0, 4.0
    g = S.Grid((4096,), 0.05)
    W = S.absorbing_layer(g, 0, "high", width, W0)
    pr = _cpu(S.Hamiltonian(g, W=W), 0.005, track_absorbed=True)
    x0 = g.axes[0][-1] - width - 40.0
    p = pr.get(pr.step(pr.put(g.gaussian((x0,), (k0,), (sig,))), int(round(25.0 / 0.005))))
    rho = g.density(p) * g.dV
    xs = g.axes[0]
    # at t = 25 the reflected packet is near 2 x_layer - x0 - v t (its mirror image), the leaked one has wrapped round
    # to the far left of the window: count the region between
    xl = g.axes[0][-1] - width
    xr = 2 * xl - x0 - k0 * 25.0
    back = float(np.sum(rho[(xs > xr - 30.0) & (xs < xl - 10.0)]))
    x, w = np.polynomial.hermite_e.hermegauss(60)
    R, T = S.layer_reflection(k0 + x / (2 * sig), width, W0, 1.0, slices=4000)
    ref = float(np.sum(w * R) / np.sum(w))
    assert ref > 1e-4
    assert abs(back - ref) < 0.02 * ref, (back, ref)


# --- Aharonov-Bohm --------------------------------------------------------------------------------------------------------
def _ab_run(d, flux, V0=200.0):
    n = int(round(36.0 / d))
    g = S.Grid((n, n | 1), d)
    X, Y = g.mesh()
    W = sum(S.absorbing_layer(g, a, s, 3.0, 20.0) for a in (0, 1) for s in ("low", "high"))
    r = np.sqrt(X**2 + Y**2)
    core = V0 * 0.5 * (1 - np.tanh((r - 1.0) / 0.1))  # a smooth impenetrable core of radius 1 around the flux
    c0 = (-8.0, 0.0)  # far enough that the packet's tail inside the core is < 1e-7 (at -5 it was 2e-3: see below)
    phi = g.gaussian(c0, (5.0, 0.0), (1.0, 1.5))
    A = S.flux_tube(flux, (0, 0), 0.15) if flux else None
    psi0 = phi * np.exp(1j * A.gauge(g, c0)) if A else phi  # the same physical packet in every gauge
    pr = S.SplitOperator(S.Hamiltonian(g, V=core, W=W, A=A), 0.002)
    return g, g.density(pr.get(pr.step(pr.put(psi0), 1200)))


def test_aharonov_bohm_flux_quantum_changes_nothing():
    """A flux of one quantum h/q (2 pi with hbar = q = 1) in a tube the wave cannot reach is a gauge transformation:
    the density after scattering on the core equals the one without flux, up to the grid's error, which falls fast
    with the spacing (measured 5.7e-6 of the peak at dx = 0.15, 1.2e-7 at dx = 0.1; independent of dt and of the
    tube's radius). A packet started with its tail inside the core breaks the identity (4e-4 at a tail of 2e-3: there
    the gauge factor is not a gauge transformation). Half a quantum changes the density by percents."""
    res = {}
    for d in (0.15, 0.1):
        g, d0 = _ab_run(d, 0.0)
        _, d1 = _ab_run(d, 2 * math.pi)
        res[d] = float(np.max(np.abs(d1 - d0)) / d0.max())
    assert res[0.15] < 2e-5 and res[0.1] < 0.1 * res[0.15], res
    _, dh = _ab_run(0.15, math.pi)
    _, d0 = _ab_run(0.15, 0.0)
    assert np.max(np.abs(dh - d0)) / d0.max() > 0.01


# --- interpolation, current, flux -------------------------------------------------------------------------------------
def test_sample_values_and_gradients():
    """Lagrange interpolation of degree 8 through the 9 samples around the nearest one: the remainder is
    max|prod_j (t - j)| (k dx)^9 / 9! of the field per axis, max|prod| = 193.8 (t within half a step of the middle
    node), i.e. 1.4e-5 for k dx = 0.67 (two axes: twice); the derivative's, 576 (k dx)^8 / 9! of its size."""
    g = S.Grid((64, 64), 0.15)
    c, k, s = (0.1, -0.2), (4.0, 2.0), (0.8, 0.9)
    psi = g.gaussian(c, k, s)
    N = math.sqrt(g.norm(np.exp(-((g.mesh()[0] - c[0]) ** 2) / (4 * s[0] ** 2) - ((g.mesh()[1] - c[1]) ** 2) / (4 * s[1] ** 2))))
    P = np.random.default_rng(1).uniform(-2, 2, (80, 2))
    ex = np.exp(-((P[:, 0] - c[0]) ** 2) / (4 * s[0] ** 2) - ((P[:, 1] - c[1]) ** 2) / (4 * s[1] ** 2)
                + 1j * (k[0] * P[:, 0] + k[1] * P[:, 1])) / N
    gx = ex * (-(P[:, 0] - c[0]) / (2 * s[0] ** 2) + 1j * k[0])
    v, gr = S.sample(g, psi, P)
    kd = math.hypot(*k) * 0.15
    bound = 2 * 193.8 * kd**9 / math.factorial(9)
    assert np.max(np.abs(v[0] - ex)) / np.max(np.abs(ex)) < bound
    assert np.max(np.abs(gr[0, 0] - gx)) / np.max(np.abs(gx)) < 2 * 576 * kd**8 / math.factorial(9)


def test_sample_in_three_dimensions_and_for_a_spinor():
    """The same interpolation in 3-D, for a scalar and a two-component wave (B6 finding: the einsum named the third
    axis "c", the letter of the component index, so every 3-D sample failed — the 3-D Bohm points of the quantum
    playground). A plane wave exp(i k.x) is sampled against its closed form within the remainder bound (three axes:
    three times the one-axis term)."""
    g = S.Grid((32, 32, 32), 0.2)
    k = np.array([2.0, -1.0, 1.5])
    X = g.mesh()
    psi = np.broadcast_to(np.exp(1j * (k[0] * X[0] + k[1] * X[1] + k[2] * X[2])), g.shape).copy()
    P = np.random.default_rng(2).uniform(-2.0, 2.0, (50, 3))
    ex = np.exp(1j * P @ k)
    kd = float(np.max(np.abs(k))) * 0.2
    bound = 3 * 193.8 * kd**9 / math.factorial(9)
    v, gr = S.sample(g, psi, P)
    assert v.shape == (1, 50) and gr.shape == (1, 3, 50)
    assert np.max(np.abs(v[0] - ex)) < bound
    assert np.max(np.abs(gr[0] - 1j * k[:, None] * ex[None])) / np.max(np.abs(k)) < 3 * 576 * kd**8 / math.factorial(9)
    v2, _ = S.sample(g, np.stack([psi, 0.5 * psi]), P)
    assert v2.shape == (2, 50) and np.allclose(v2[1], 0.5 * v2[0], rtol=0, atol=1e-15)


def test_sample_is_mirror_symmetric():
    """An even wave on a grid symmetric about x = 0 (a sample there): the interpolated value is even and its x
    derivative odd at every point, so Bohm's v_x vanishes on the axis exactly (no trajectory can cross it)."""
    g = S.Grid((65, 48), 0.17)
    X, Y = g.mesh()
    psi = (np.exp(-((X - 1.3) ** 2 + Y**2) / 2 + 2j * Y) + np.exp(-((X + 1.3) ** 2 + Y**2) / 2 + 2j * Y)).astype(complex)
    P = np.random.default_rng(4).uniform(-2.5, 2.5, (200, 2))
    Pm = P * np.array([-1.0, 1.0])
    v1, g1 = S.sample(g, psi, P)
    v2, g2 = S.sample(g, psi, Pm)
    assert np.max(np.abs(v1 - v2)) < 1e-13
    assert np.max(np.abs(g1[0, 0] + g2[0, 0])) < 1e-12 and np.max(np.abs(g1[0, 1] - g2[0, 1])) < 1e-12
    _, ga = S.sample(g, psi, np.array([[0.0, 0.3], [0.0, -1.1]]))
    assert np.max(np.abs(ga[0, 0])) < 1e-13


def test_current_and_flux_of_a_moving_packet():
    """A Gaussian packet as prepared (a real envelope times exp(i k.r)) carries j = (hbar k / m) |psi|^2 exactly; the
    plane flux by the 8th-order difference equals the spectral current there."""
    g = S.Grid((160, 160), 0.2)  # the packet's tail at the window's edge < 1e-8 (the grid is periodic)
    psi = g.gaussian((0, 0), (2.0, -1.0), (1.5, 1.5))
    j = g.current(psi)
    rho = g.density(psi)
    assert np.max(np.abs(j[0] - 2.0 * rho)) < 1e-10 and np.max(np.abs(j[1] + 1.0 * rho)) < 1e-10
    jf = g.flux(psi, 1, 90)
    assert np.max(np.abs(jf - j[1][:, 90])) < 1e-6 * np.max(np.abs(j[1]))
    # psi and d psi/dz on the plane: the derivative of the prepared packet is (i k_z - (z - z0)/(2 sigma^2)) psi
    pr = _cpu(S.Hamiltonian(g), 0.01)
    pc, d = pr.plane(pr.put(psi), 1, 90)
    z = g.axes[1][90]
    assert np.max(np.abs(pc[0] - psi[:, 90])) == 0
    assert np.max(np.abs(d[0] - (-1j - z / (2 * 1.5 ** 2)) * psi[:, 90])) < 1e-6 * np.max(np.abs(psi))


# --- devices -----------------------------------------------------------------------------------------------------------
def test_kernel_is_registered():
    ks = backend.kernels()
    assert S.KERNEL in ks and ks[S.KERNEL].gpu and ks[S.KERNEL].crossover


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU")
def test_gpu_equals_cpu():
    """The same steps on GPU 0 and on the CPU (cuFFT and pocketfft round differently: ~eps per step)."""
    g = S.Grid((256, 256), 0.1)
    X, Y = g.mesh()
    H = S.Hamiltonian(g, V=0.5 * (X**2 + Y**2) + 2 * np.exp(-((X - 1) ** 2 + Y**2)), W=S.absorbing_layer(g, 0, "high", 3.0, 4.0),
                      A=S.uniform_field(0.5))
    psi0 = g.gaussian((-1.0, 0.5), (3.0, 0.0), (1.0, 1.0))
    gpu = S.SplitOperator(H, 0.005, track_absorbed=True)
    assert gpu.device == "gpu"
    cpu = _cpu(H, 0.005, track_absorbed=True)
    a, b = _run(gpu, psi0, 100), _run(cpu, psi0, 100)
    assert np.max(np.abs(a - b)) < 1e-12 * 100
    assert abs(gpu.absorbed().sum() - cpu.absorbed().sum()) < 1e-12


# --- a 2-D double slit approaches Kirchhoff's theory as the slits widen ------------------------------------------------
def _double_slit_deviation(a, h=1 / 8):
    """A packet (lambda = 1, k0 = 2 pi, sigma_z = 4) through two slits of width a, period 2a, in a thin high wall
    (thickness 0.5, height 8 E0, edges smoothed over one grid step), screen at L = 1.6 a^2 (Fresnel number 0.625);
    the time-integrated flux into the screen against the Kirchhoff boundary values propagated exactly (2-D
    Rayleigh-Sommerfeld, lfphys.theories.approx.kirchhoff), both normalised over the screen. Returns the largest
    difference in units of the reference's peak."""
    from lfphys.theories.approx import kirchhoff
    k0, sz, w, d, L = 2 * math.pi, 4.0, 0.5, 2 * a, 1.6 * a * a
    sx = 2.5 * d
    zs = -(4.5 * sz + 1.0)
    half = 0.5 * d + a + L * math.tan(math.asin(min(0.999, 3.0 / a))) if a > 3 else 0.5 * d + a + L
    half = max(half, 3 * sx)
    xh, z0, z1 = half + 6.0, zs - 4 * sz - 6.0, L + 6.0
    nx = int(math.ceil(2 * xh / h)) | 1
    nz = int(math.ceil((z1 - z0) / h)) + 1
    g = S.Grid((nx, nz), h, center=(0.0, z0 + (nz // 2) * h))
    X, Z = g.mesh()

    def step(u):
        return 0.5 * (1 + np.tanh(u / h))
    holes = sum(step(X - (c - a / 2)) * step((c + a / 2) - X) for c in (-d / 2, d / 2))
    V = 8 * 0.5 * k0**2 * step(Z + w / 2) * step(w / 2 - Z) * (1 - holes)
    W0 = 2 * 0.5 * k0**2
    W = S.absorbing_layer(g, 1, "high", g.axes[1][-1] - L, W0) + S.absorbing_layer(g, 1, "low", 6.0, W0)
    W = W + S.absorbing_layer(g, 0, "low", 6.0, W0) + S.absorbing_layer(g, 0, "high", 6.0, W0)
    dt = 0.1 / (0.5 * k0**2)
    pr = S.SplitOperator(S.Hamiltonian(g, V=V, W=W), dt)
    psi = pr.put(g.gaussian((0.0, zs), (0.0, k0), (sx, sz)))
    iL = int(np.searchsorted(g.axes[1], L, side="right")) - 1
    flux = np.zeros(nx)
    for _ in range(int((abs(zs) + L + 4 * sz) / k0 * 1.6 / dt)):
        psi = pr.step(psi, 1)
        flux += pr.flux(psi, 1, iL, 16)
    x = g.axes[0]
    m = np.abs(x) <= half
    P = flux[m] / np.trapezoid(flux[m], x[m])
    xg, wg = np.polynomial.hermite_e.hermegauss(7)
    R = np.zeros(m.sum())
    c = np.array([-d / 2, d / 2])
    v = np.exp(-(c**2) / (4 * sx**2))
    for k, wk in zip(k0 + xg / (2 * sz), wg / wg.sum()):
        Up = np.tensordot(v, kirchhoff.slit_fields(x[m], L - w / 2 + 0.005, k, c, a), axes=1)
        Um = np.tensordot(v, kirchhoff.slit_fields(x[m], L - w / 2 - 0.005, k, c, a), axes=1)
        R += wk * np.imag(np.conj(0.5 * (Up + Um)) * (Up - Um) / 0.01) / k
    R = R / np.trapezoid(R, x[m])
    return float(np.max(np.abs(P - R)) / R.max())


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="needs GPU 0 for speed (minutes on the CPU)")
def test_double_slit_approaches_kirchhoff_as_the_slits_widen():
    """Kirchhoff's boundary values (the incident wave in the slits, nothing on the wall) are an approximation whose
    error falls with the slit width in wavelengths; the exact 2-D solution must approach it. Measured (2026-10-28):
    0.50 of the peak at a = 2.5 lambda, 0.19 at 5 lambda, 0.078 at 10 lambda (not run here: 4 M points): at least
    first order in lambda / a. A solver error that does not shrink with a would stop the approach."""
    d1, d2 = _double_slit_deviation(2.5), _double_slit_deviation(5.0)
    assert d2 < 0.25, (d1, d2)
    assert d1 / d2 > 2.0, (d1, d2)


def test_demodulated_sampling_is_exact_on_the_samples_and_for_its_carrier():
    """Review B6-Q1: with a carrier kappa, ``sample`` interpolates exp(i kappa x) times the Lagrange interpolant of
    psi exp(-i kappa x): at the grid's samples it returns the samples (exact identity), a plane wave of wavevector
    kappa is reproduced to round-off at any k d (here 2.5: the plain interpolation errs by 0.43 of the gradient), and a
    field near the carrier errs by the remainder of k - kappa, not of k."""
    g = S.Grid((48, 48), 0.25)
    k = np.array([10.0, -6.0])  # k d = 2.5 and 1.5
    X = g.mesh()
    psi = np.broadcast_to(np.exp(1j * (k[0] * X[0] + k[1] * X[1])), g.shape).copy()
    P = np.random.default_rng(3).uniform(-3.0, 3.0, (40, 2))
    ex = np.exp(1j * P @ k)
    v, gr = S.sample(g, psi, P, carrier=np.tile(k, (40, 1)))
    assert np.max(np.abs(v[0] - ex)) < 1e-12 and np.max(np.abs(gr[0] - 1j * k[:, None] * ex[None])) < 1e-11 * 10
    vp, grp = S.sample(g, psi, P)
    assert np.max(np.abs(grp[0, 0] - 1j * k[0] * ex)) / k[0] > 0.1
    nodes = np.column_stack([g.axes[0][[10, 20, 30]], g.axes[1][[5, 25, 40]]])
    vn, _ = S.sample(g, psi, nodes, carrier=np.tile([3.0, 1.0], (3, 1)))
    assert np.max(np.abs(vn[0] - psi[[10, 20, 30], [5, 25, 40]])) < 1e-13
    k2 = k + np.array([0.4, -0.3])  # a wave near the carrier: the remainder of |k - kappa| d = 0.125
    psi2 = np.broadcast_to(np.exp(1j * (k2[0] * X[0] + k2[1] * X[1])), g.shape).copy()
    v2, _ = S.sample(g, psi2, P, carrier=np.tile(k, (40, 1)))
    assert np.max(np.abs(v2[0] - np.exp(1j * P @ k2))) < 2 * 193.8 * 0.125**9 / math.factorial(9) + 1e-13
