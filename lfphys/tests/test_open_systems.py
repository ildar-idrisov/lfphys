# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Open quantum systems (plan item P5): the Lindblad equation, the two-level atom (Rabi, optical Bloch equations,
Torrey), quantum-jump trajectories, which-path decoherence and its comparison with GRW.

Tolerances (u = 2^-53, gamma_k = k u/(1 - k u)):
* two float routes to the same sum of products: each within gamma_k times the sum of the moduli of its terms (the
  magnitudes are computed in the test);
* exact propagation: ``open_systems.expm_error_bound`` (derived in its docstring) against 30-digit mpmath;
* closed forms evaluated in floats: a few roundings per operation, with the condition of the formula, stated per test;
* Monte Carlo: |mean - exact| <= z s/sqrt(N) with z = 5 (two-sided normal tail 5.7e-7 per comparison; the number of
  comparisons per test is stated, the family-wise false-alarm probability is their sum (Bonferroni)); a sampled
  distribution against its CDF by the Dvoretzky-Kiefer-Wolfowitz inequality with Massart's constant,
  P(sup |F_N - F| > eps) <= 2 exp(-2 N eps^2), at alpha = 1e-6: eps = sqrt(ln(2/alpha)/(2N)). The seeds are fixed, so
  every run is the same; the bounds say how unlikely a failure of a correct implementation would be.
"""

import math

import mpmath as mp
import numpy as np
import pytest
from scipy import integrate, linalg

from lfphys.core.quantum import decoherence as DEC, jumps as J, marks, open_systems as OS, two_level as TL
from lfphys.theories.alternatives import collapse, collapse_baseline as CB

U = 2.0 ** -53
Z = 5.0


def gam(k):
    return k * U / (1 - k * U)


def rand_op(rng, d, scale=1.0):
    return scale * (rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d)))


def rand_herm(rng, d, scale=1.0):
    A = rand_op(rng, d, scale)
    return 0.5 * (A + A.conj().T)


def rand_state(rng, d):
    A = rand_op(rng, d)
    rho = A @ A.conj().T
    return rho / np.trace(rho)


def obe(Om, De, T1, T2):
    return OS.liouvillian(TL.hamiltonian(Om, De), TL.collapse_operators(T1, T2))


def aug_bound(Om, De, T1, T2, t):
    """Rounding bound of ``bloch_solution``: the exponential of M = [[Q, b], [0, 0]] at t. Q + Q^T <= 0, so exp(Q s)
    is a 2-norm contraction and exp(M s) = [[exp(Q s), (I - exp(Q s)) x_ss], [0, 1]] has 2-norm <= 3 (|x_ss| <= 1);
    as in ``open_systems.expm_error_bound`` with that growth factor: the backward error u ||M t||_1 carried by two
    factors 3, the Pade rounding gamma_60 n and each of the s squarings gamma_n n, amplified by 2 * 3 per squaring
    (n = 4, ||.||_2 <= 2 ||.||_1)."""
    Q, b = TL.bloch_matrix(Om, De, T1, T2)
    M = np.zeros((4, 4))
    M[:3, :3], M[:3, 3] = Q, b
    a1 = float(np.linalg.norm(M * t, 1))
    s = max(0, math.ceil(math.log2(max(a1, 1e-300) / 5.371920351148152)))
    return 9 * 2 * U * a1 + 6.0 ** s * (gam(60) + gam(4)) * 4 * 9


# --- Lindblad generator ---------------------------------------------------------------------------------------------

def test_liouvillian_equals_the_direct_right_hand_side():
    rng = np.random.default_rng(11)
    for d in (2, 3, 5):
        H = rand_herm(rng, d)
        Ls = [rand_op(rng, d, 0.4) for _ in range(3)]
        Lsup = OS.liouvillian(H, Ls)
        for _ in range(3):
            rho = rand_state(rng, d)
            a = OS.unvec(Lsup @ OS.vec(rho), d)
            b = OS.rhs(H, Ls, rho)
            # magnitude of the terms of each entry: |H||rho| + |rho||H| + sum |L||rho||L^+| + |L^+ L||rho| + ...
            aH, ar = np.abs(H), np.abs(rho)
            mag = aH @ ar + ar @ aH
            for L in Ls:
                aL = np.abs(L)
                LdL = aL.T @ aL
                mag = mag + aL @ ar @ aL.T + LdL @ ar + ar @ LdL
            # per route: the superoperator entries (<= 2 products and a sum of 4 + d terms) then a sum of d^2
            # products: gamma_(2d^2 + 8) per term on each side
            assert np.all(np.abs(a - b) <= 2 * gam(2 * d * d + 8) * mag), d


def test_superoperator_identities_and_the_generator_checks():
    rng = np.random.default_rng(12)
    d = 3
    A, B, rho = rand_op(rng, d), rand_op(rng, d), rand_op(rng, d)
    assert np.allclose(OS.sprepost(A, B) @ OS.vec(rho), OS.vec(A @ rho @ B), rtol=0, atol=64 * U * 30)
    assert np.allclose(OS.spre(A) @ OS.vec(rho), OS.vec(A @ rho), rtol=0, atol=64 * U * 30)
    assert np.allclose(OS.spost(B) @ OS.vec(rho), OS.vec(rho @ B), rtol=0, atol=64 * U * 30)
    assert np.array_equal(OS.unvec(OS.vec(rho)), rho)
    assert OS.vec(np.arange(4).reshape(2, 2)).tolist() == [0, 2, 1, 3]  # column stacking
    Lsup = OS.liouvillian(rand_herm(rng, 4), [rand_op(rng, 4, 0.3) for _ in range(2)])
    c = OS.generator_checks(Lsup)
    scale = float(np.max(np.abs(Lsup)))
    assert c["trace_preservation"] <= 64 * U * scale and c["hermiticity_preservation"] <= 64 * U * scale
    # a non-Lindblad generator (a lone anticommutator) is flagged
    bad = OS.spre(np.eye(4)) * -1.0
    assert OS.generator_checks(bad)["trace_preservation"] > 0.5


@mp.workdps(30)
def _mp_propagate(Lsup, rho0, t):
    Lm = mp.matrix([[mp.mpc(complex(x)) for x in row] for row in Lsup])
    v = mp.matrix([mp.mpc(complex(x)) for x in OS.vec(rho0)])
    w = mp.expm(Lm * mp.mpf(t)) * v
    return np.array([complex(w[i]) for i in range(len(v))])


def test_exact_propagation_against_30_digit_mpmath():
    """Both routes (expm, eigendecomposition) against the exact exponential of the same binary64 generator; the
    expm route within its stated bound ``expm_error_bound`` (trace norm, so every entry), the eig route within
    cond(V) times that bound plus cond(V) n gamma_n (one solve and one product with V). The bounds are worst case
    (measured: errors <= 2.2e-15, 1e-3 of the bound; review B5, N7): this test catches a wrong generator, time or
    route, while the size of the agreement itself is recorded, not asserted at a fitted level."""
    rng = np.random.default_rng(13)
    cases = [obe(1.3, 0.7, 2.0, 1.5), obe(5.0, -2.0, 1.0, 2.0), obe(0.0, 0.3, 3.0, 0.5),
             OS.liouvillian(rand_herm(rng, 3), [rand_op(rng, 3, 0.5) for _ in range(2)])]
    for Lsup in cases:
        d = math.isqrt(Lsup.shape[0])
        rho0 = rand_state(rng, d)
        lam, V = linalg.eig(Lsup)
        kappa = float(np.linalg.cond(V))
        for t in (0.1, 1.0, 7.5, 40.0):
            ex = _mp_propagate(Lsup, rho0, t)
            a = OS.vec(OS.propagate(Lsup, rho0, [t])[0])
            b = OS.vec(OS.propagate(Lsup, rho0, [t], method="eig")[0])
            bound = OS.expm_error_bound(Lsup, t)
            n = Lsup.shape[0]
            assert np.max(np.abs(a - ex)) <= bound, (t, np.max(np.abs(a - ex)), bound)
            assert np.max(np.abs(b - ex)) <= kappa * (bound + 2 * n * gam(n)), (t, np.max(np.abs(b - ex)))


def test_exceptional_point_is_refused_by_the_eig_route():
    # resonance fluorescence at Omega = Gamma/4 (Delta = 0, T2 = 2 T1): Q of the Bloch equations has a double root
    # -3 Gamma/4 (Steck 5.161 with Omega_Gamma = 0) and the Liouvillian is not diagonalisable there
    Lsup = obe(0.25, 0.0, 1.0, 2.0)
    with pytest.raises(ValueError):
        OS.propagate(Lsup, TL.density_matrix([0, 0, -1]), [1.0], method="eig", max_cond=1e6)
    r = OS.propagate(Lsup, TL.density_matrix([0, 0, -1]), [1.0, 3.0])
    x = TL.torrey_resonance([1.0, 3.0], 0.25, 1.0, 2.0)
    assert np.max(np.abs(np.array([TL.bloch_vector(m) for m in r]) - x)) <= 1e-14


def test_propagation_keeps_trace_hermiticity_and_positivity():
    rng = np.random.default_rng(14)
    for d in (2, 4):
        Lsup = OS.liouvillian(rand_herm(rng, d, 2.0), [rand_op(rng, d, 0.3) for _ in range(3)])
        rho0 = rand_state(rng, d)
        for rho in OS.propagate(Lsup, rho0, np.linspace(0, 50, 26)):
            c = OS.state_checks(rho)
            b = OS.expm_error_bound(Lsup, 50.0)  # the largest t: bounds every entry and eigenvalue shift
            assert c["trace_err"] <= d * b and c["herm_err"] <= 2 * b and c["min_eig"] >= -b
    assert not OS.is_state(np.diag([1.2, -0.2]))
    assert not OS.is_state(np.array([[0.5, 0.1], [0.3, 0.5]]))


# --- steady state ---------------------------------------------------------------------------------------------------

OBE_CASES = [(1.0, 0.0, 1.0, 2.0), (2.5, 1.5, 1.0, 2.0), (0.3, -2.0, 4.0, 1.0), (10.0, 3.0, 0.5, 0.2),
             (1e-3, 0.0, 1.0, 2.0), (1.0, 0.0, 1.0, 1.0)]


@pytest.mark.parametrize("Om,De,T1,T2", OBE_CASES)
def test_steady_state_null_space_against_the_closed_form(Om, De, T1, T2):
    H, c = TL.hamiltonian(Om, De), TL.collapse_operators(T1, T2)
    rho, info = OS.steady_state(H, c)
    rho2, _ = OS.steady_state(H, c, method="lstsq")
    x = TL.bloch_steady_state(Om, De, T1, T2)
    # closed form: each component a ratio of sums of at most 4 products: 12 roundings relative to its magnitude
    ref = TL.density_matrix(x)
    tol_cf = gam(12) * (1 + float(np.max(np.abs(x))))
    assert np.max(np.abs(rho - ref)) <= info["err_bound"] + tol_cf
    assert np.max(np.abs(rho2 - ref)) <= info["err_bound"] + tol_cf + 4 * gam(16) * info["s_max"] / info["s_next"]
    # Steck 5.132 written out: rho_ee = (Omega^2/(2 g Gamma)) / (1 + Delta^2/g^2 + Omega^2/(g Gamma))
    G1, g = 1 / T1, 1 / T2
    ree = (Om ** 2 / (2 * g * G1)) / (1 + De ** 2 / g ** 2 + Om ** 2 / (g * G1))
    assert TL.steady_excited_population(Om, De, T1, T2) == pytest.approx(ree, rel=gam(16), abs=gam(16))
    # Steck 5.133: rho_eg = -(i Omega/2g)(1 + i Delta/g)/(...)
    reg = -(1j * Om / (2 * g)) * (1 + 1j * De / g) / (1 + De ** 2 / g ** 2 + Om ** 2 / (g * G1))
    assert abs(0.5 * (x[0] - 1j * x[1]) - reg) <= gam(16) * (1 + abs(reg))  # rho_eg = (u - i v)/2


def test_homogeneous_broadening_form_of_the_steady_state():
    # Steck 5.137: gamma_perp = Gamma/2: rho_ee = (Omega^2/Gamma^2) / (1 + (2 Delta/Gamma)^2 + 2 Omega^2/Gamma^2)
    for Om, De, G1 in ((1.0, 0.0, 1.0), (3.0, 2.0, 0.5), (0.1, -1.0, 2.0)):
        ref = (Om / G1) ** 2 / (1 + (2 * De / G1) ** 2 + 2 * (Om / G1) ** 2)
        assert TL.steady_excited_population(Om, De, 1 / G1, 2 / G1) == pytest.approx(ref, rel=gam(20))


def test_non_unique_steady_states_and_bad_t2_are_refused():
    with pytest.raises(ValueError):  # Hamiltonian only: every function of H is stationary
        OS.steady_state(TL.hamiltonian(1.0, 0.5), [])
    with pytest.raises(ValueError):  # pure dephasing without drive: every diagonal state is stationary
        OS.steady_state(TL.hamiltonian(0.0, 0.5), TL.collapse_operators(math.inf, 1.0))
    with pytest.raises(ValueError):
        TL.rates(1.0, 2.0 + 1e-9)  # T2 > 2 T1 is not completely positive
    assert TL.rates(1.0, 2.0)[2] == 0.0
    with pytest.raises(ValueError):
        TL.bloch_steady_state(0.0, 0.0, math.inf, 1.0)


# --- time-dependent Hamiltonians: Magnus 4 ----------------------------------------------------------------------------

def _lab_exact(ts, w0, w, Om, T1, T2, rho0):
    """Circularly driven atom in the lab frame: exactly the rotating-frame Bloch dynamics (module docstring)."""
    Lrot = obe(Om, w - w0, T1, T2)
    return np.array([TL.to_lab(OS.propagate(Lrot, rho0, [t])[0], t, w) for t in ts])


@pytest.mark.parametrize("method,order", [("magnus4", 4), ("cf4", 4), ("radau5", 5)])
def test_time_dependent_methods_have_their_order(method, order):
    """Fixed steps: the error falls by 2^p per halving. Magnus-4 and CF4 are time-symmetric (only even powers in the
    global error), so the ratio is 16 (1 + O((h||A||)^2)); Radau IIA is not symmetric: 32 (1 + O(h||A||)). With
    h ||A||_F <= 0.22 (measured ratios: 15.99, 16.00 for both Magnus forms; 31.98, 31.98 for Radau IIA) the bounds
    16 x [0.92, 1.08] and 32 x [0.85, 1.15] leave the O((h||A||)^2) resp. O(h||A||) correction with an O(1) constant."""
    w0, w, Om, T1, T2 = 6.0, 5.5, 1.2, 3.0, 2.0
    rho0 = TL.density_matrix([0.3, 0.0, -0.9])
    ts = np.array([0.0, 2.0])
    ex = _lab_exact(ts, w0, w, Om, T1, T2, rho0)[-1]
    H = lambda t: TL.lab_hamiltonian_circular(t, w0, w, Om)  # noqa: E731
    errs = []
    for n in (80, 160, 320):
        r, _, _ = OS.evolve(H, TL.collapse_operators(T1, T2), rho0, ts, steps=n, method=method)
        errs.append(OS.trace_norm(r[-1] - ex))
    q, band = (16.0, 0.08) if order == 4 else (32.0, 0.15)
    for x, y in zip(errs, errs[1:]):
        assert q * (1 - band) <= x / y <= q * (1 + band), (method, errs)


def test_radau_coefficients_are_the_collocation_method():
    """The Radau IIA tableau of ``open_systems``: nodes are the zeros of d^2/dx^2 [x^2 (x - 1)^3] (the Radau points,
    c3 = 1), A satisfies the collocation conditions C(3): sum_j a_ij c_j^(k-1) = c_i^k/k, and the weights b = A[2]
    (stiff accuracy) satisfy B(5): sum_i b_i c_i^(k-1) = 1/k, but not B(6) (order exactly 5)."""
    c, A = OS.RADAU_C, OS.RADAU_A
    x = np.poly1d([1.0, 0.0, 0.0]) * np.poly1d([1.0, -1.0]) ** 3
    assert np.max(np.abs(x.deriv(2)(c))) <= 64 * U * 20
    for k in (1, 2, 3):
        assert np.max(np.abs(A @ c ** (k - 1) - c ** k / k)) <= 16 * U
    for k in range(1, 6):
        assert abs(A[2] @ c ** (k - 1) - 1 / k) <= 16 * U
    assert abs(A[2] @ c ** 5 - 1 / 6) > 1e-4


@pytest.mark.parametrize("method", ["radau5", "cf4", "magnus4"])
def test_adaptive_methods_meet_their_stated_error(method):
    """Adaptive steps on the lab-frame problem: the measured trace-norm error stays below the returned estimate (the
    sum of the step estimates plus the rounding allowance), and the estimate below tol + allowance."""
    w0, w, Om, T1, T2 = 8.0, 7.2, 1.5, 2.0, 1.0
    rho0 = TL.density_matrix([0.0, 0.0, -1.0])
    ts = np.linspace(0, 6, 7)
    ex = _lab_exact(ts, w0, w, Om, T1, T2, rho0)
    H = lambda t: TL.lab_hamiltonian_circular(t, w0, w, Om)  # noqa: E731
    for tol in (1e-6, 1e-9):
        r, err, info = OS.evolve(H, TL.collapse_operators(T1, T2), rho0, ts, tol=tol, method=method)
        meas = np.array([OS.trace_norm(a - b) for a, b in zip(r, ex)])
        hmax_a = info["h_max"] * 2 * (0.5 * w0 + 1.5) * 2 * math.sqrt(2)  # >= h_max ||A||_F (generous)
        allowance = 20 * 4 * U * info["accepted"] * (1 + (hmax_a if method == "radau5" else 0))
        assert np.all(meas <= err + 1e-15), (tol, meas, err)
        assert err[-1] <= tol + allowance + 1e-15
        for m in r:
            c = OS.state_checks(m)
            assert c["trace_err"] <= 1e-13 and c["herm_err"] <= 1e-13 and c["min_eig"] >= -err[-1] - 1e-15


@pytest.mark.parametrize("G", [1e4, 1e5])
def test_stiff_dissipation_does_not_set_the_step(G):
    """Review B5, S3: Gamma >> the drive. The lab-frame circular drive with T1 = 1/Gamma, T2 = 2/Gamma has the exact
    rotating-frame solution; the default "radau5" meets its stated error in a few hundred steps (measured at tol 1e-9:
    760 steps at Gamma = 1e4, 146 at 1e5; "magnus4" would need >= span ||L||_F / 0.9 ~ 1e5 ... 1e6 steps and is
    refused before the run at 1e5 with max_steps = 1e5), and "cf4" stays exact-CPTP but is first order there (its
    quasi-static state lags by h/6), so it is checked only for honesty of its estimate on a short span."""
    w0, w, Om = 8.0, 7.2, 1.5
    T1, T2 = 1 / G, 2 / G
    rho0 = TL.density_matrix([0.0, 0.0, -1.0])
    ts = np.linspace(0, 6, 7)
    ex = _lab_exact(ts, w0, w, Om, T1, T2, rho0)
    H = lambda t: TL.lab_hamiltonian_circular(t, w0, w, Om)  # noqa: E731
    c = TL.collapse_operators(T1, T2)
    r, err, info = OS.evolve(H, c, rho0, ts, tol=1e-9)
    meas = np.array([OS.trace_norm(a - b) for a, b in zip(r, ex)])
    assert np.all(meas <= err + 1e-15), (meas, err)
    assert info["accepted"] + info["rejected"] <= 2000 and info["stiff_steps"] > 0, info
    with pytest.raises(ValueError, match="stiff"):
        OS.evolve(H, c, rho0, ts, tol=1e-9, method="magnus4", max_steps=100_000)
    tc = np.array([0.0, 0.2])
    r, err, info = OS.evolve(H, c, rho0, tc, tol=1e-6, method="cf4")
    assert OS.trace_norm(r[-1] - _lab_exact(tc, w0, w, Om, T1, T2, rho0)[-1]) <= err[-1] + 1e-15


def test_time_grids_are_validated():
    """Review B5, S4: unsorted, non-finite or (for ``propagate``) negative times are refused with a reason; repeated
    times are allowed and give the same state twice; ``propagate`` measures every time from rho0, so its times may
    come in any order (the result is the same as for the sorted grid, entry by entry)."""
    H, c = TL.hamiltonian(1.0, 0.3), TL.collapse_operators(2.0, 1.0)
    rho0 = TL.density_matrix([0, 0, -1.0])
    Lsup = obe(1.0, 0.3, 2.0, 1.0)
    for bad in ([0.0, 2.0, 1.0], [0.0, -1.0], [0.0, math.nan], []):
        with pytest.raises(ValueError):
            OS.evolve(H, c, rho0, bad)
        with pytest.raises(ValueError):
            J.trajectories(H, c, TL.G, bad, 3, np.random.default_rng(1))
    for bad in ([-3.0], [1.0, -0.5], [math.inf]):
        with pytest.raises(ValueError):
            OS.propagate(Lsup, rho0, bad)
    with pytest.raises(ValueError, match="non-decreasing"):
        OS.evolve(H, c, rho0, [0.0, 2.0, 1.0])
    r, err, _ = OS.evolve(H, c, rho0, [0.0, 1.0, 1.0, 2.0], tol=1e-10)
    assert r.shape[0] == 4 and np.array_equal(r[1], r[2]) and err[1] == err[2]
    a = OS.propagate(Lsup, rho0, [2.0, 0.5, 1.0])
    b = OS.propagate(Lsup, rho0, [0.5, 1.0, 2.0])
    assert np.array_equal(a[0], b[2]) and np.array_equal(a[1], b[0]) and np.array_equal(a[2], b[1])
    tr = J.trajectories(H, c, TL.G, [0.0, 1.0, 1.0], 20, np.random.default_rng(2), e_ops=[TL.PE])
    assert np.array_equal(tr.expect[0][:, 1], tr.expect[0][:, 2])
    # a start other than 0 is a valid clock for H(t) (only the order matters)
    r, _, _ = OS.evolve(H, c, rho0, [-1.0, 0.0], tol=1e-10)
    assert OS.trace_norm(r[-1] - OS.propagate(Lsup, rho0, [1.0])[0]) <= 1e-9


def test_evolve_with_a_constant_hamiltonian_equals_propagate():
    Om, De, T1, T2 = 2.0, -0.5, 1.5, 1.2
    rho0 = TL.density_matrix([0.2, -0.4, 0.5])
    ts = np.linspace(0, 5, 6)
    r, err, _ = OS.evolve(TL.hamiltonian(Om, De), TL.collapse_operators(T1, T2), rho0, ts, tol=1e-11)
    ex = OS.propagate(obe(Om, De, T1, T2), rho0, ts)
    for a, b, e, t in zip(r, ex, err, ts):
        assert OS.trace_norm(a - b) <= e + OS.expm_error_bound(obe(Om, De, T1, T2), t) + 1e-15


# --- two-level atom -------------------------------------------------------------------------------------------------

def test_rabi_formula_against_the_schroedinger_equation():
    for Om, De in ((1.0, 0.0), (1.0, 1.0), (0.3, -2.0), (5.0, 0.1)):
        H = TL.hamiltonian(Om, De)
        for t in (0.0, 0.7, 3.0, 25.0):
            psi = linalg.expm(-1j * H * t) @ TL.G
            # |psi_e|^2 from an exact unitary (rounding of expm: backward error u||Ht||, gamma_20 for the evaluation)
            tol = 4 * (U * np.linalg.norm(H * t, 1) + gam(20)) + gam(10)
            assert abs(abs(psi[0]) ** 2 - TL.rabi_probability(t, Om, De)) <= tol
            ce, cg = TL.rabi_amplitudes(t, Om, De)
            assert abs(ce - psi[0]) <= tol and abs(cg - psi[1]) <= tol
    # any initial state (Steck 5.58)
    a, b = 0.6, 0.8j
    H = TL.hamiltonian(1.7, -0.9)
    psi = linalg.expm(-1j * H * 2.3) @ np.array([a, b])
    ce, cg = TL.rabi_amplitudes(2.3, 1.7, -0.9, cg0=b, ce0=a)
    tol = 4 * (U * np.linalg.norm(H * 2.3, 1) + gam(20)) + gam(10)  # as above
    assert abs(ce - psi[0]) <= tol and abs(cg - psi[1]) <= tol


@pytest.mark.parametrize("Om,De,T1,T2", OBE_CASES + [(1.0, 0.5, math.inf, 3.0), (2.0, 0.0, math.inf, math.inf)])
def test_bloch_equations_equal_the_lindblad_equation(Om, De, T1, T2):
    """The 3-component Bloch equations (Steck 5.127) against the 4 x 4 Liouvillian built from H and the jump
    operators sqrt(Gamma) sigma, sqrt(gamma_c/2) sigma_z (Steck 5.177): two independent routes."""
    rng = np.random.default_rng(15)
    x0 = rng.normal(size=3)
    x0 = 0.9 * x0 / np.linalg.norm(x0)
    Lsup = obe(Om, De, T1, T2)
    for t in (0.3, 2.0, 11.0):
        a = TL.bloch_solution(t, Om, De, T1, T2, x0)
        b = TL.bloch_vector(OS.propagate(Lsup, TL.density_matrix(x0), [t])[0])
        # Bloch components are traces with Pauli matrices: |delta x_i| <= 2 ||delta rho||_1 (plus 2 gamma_4)
        tol = 2 * OS.expm_error_bound(Lsup, t) + 2 * gam(4) + aug_bound(Om, De, T1, T2, t)
        assert np.max(np.abs(a - b)) <= tol, (t, np.max(np.abs(a - b)), tol)


def test_torrey_at_resonance_reproduces_steck_and_the_exact_solution():
    """Steck 5.171 and 5.176 (T2 = 2 T1, ground-state start) written out, and the general resonant form against the
    exact exponential for under-, over- and critically damped cases and any initial vector."""
    G = 1.0
    ts = np.linspace(0, 12, 61)
    for Om in (0.7, 1.0, 4.0):
        x = TL.torrey_resonance(ts, Om, 1 / G, 2 / G)
        OG = math.sqrt(Om ** 2 - G ** 2 / 16)
        e = np.exp(-0.75 * G * ts)
        sy = (Om * G / (Om ** 2 + G ** 2 / 2)) * (1 - e * (np.cos(OG * ts) - (Om ** 2 - G ** 2 / 4) / (G * OG)
                                                           * np.sin(OG * ts)))
        sz = -1 + (Om ** 2 / (Om ** 2 + G ** 2 / 2)) * (1 - e * (np.cos(OG * ts) + 3 * G / (4 * OG) * np.sin(OG * ts)))
        assert np.max(np.abs(x[:, 0])) == 0.0
        # both are closed forms of the same quantities: ~ 30 roundings, times the size of the terms (<= 1 + 4 Om/OG)
        tol = gam(30) * (2 + 4 * Om / OG)
        assert np.max(np.abs(x[:, 1] - sy)) <= tol and np.max(np.abs(x[:, 2] - sz)) <= tol
    rng = np.random.default_rng(16)
    for Om, T1, T2 in ((1.0, 2.0, 1.0), (0.2, 1.0, 0.25), (1.5, 1.0, 1.0 / (1.0 + 3.0)), (3.0, 1.0, 2.0)):
        # (0.2, 1, 0.25): over-damped (|delta| = 1.5 > Omega); (1.5, 1, 1/4): critical (delta = 1.5 = Omega)
        x0 = rng.normal(size=3)
        x0 = 0.95 * x0 / np.linalg.norm(x0)
        a = TL.torrey_resonance(ts, Om, T1, T2, x0)
        b = TL.bloch_solution(ts, Om, 0.0, T1, T2, x0)
        # closed form: ~30 roundings on terms of size <= 2 + |N| t (sinh(mu t)/mu <= t), and the exact route's bound
        tol = aug_bound(Om, 0.0, T1, T2, ts[-1]) + gam(30) * (2 + 2 * (Om + 2 / T2) * ts[-1])
        assert np.max(np.abs(a - b)) <= tol, (Om, T1, T2, np.max(np.abs(a - b)), tol)


def test_torrey_equal_relaxation_times_any_detuning():
    rng = np.random.default_rng(17)
    ts = np.linspace(0, 15, 31)
    for Om, De, T in ((1.0, 0.5, 2.0), (3.0, -4.0, 0.7), (0.0, 1.0, 1.0)):
        x0 = rng.normal(size=3)
        x0 = 0.9 * x0 / np.linalg.norm(x0)
        a = TL.torrey_equal_times(ts, Om, De, T, x0)
        b = TL.bloch_solution(ts, Om, De, T, T, x0)
        # Rodrigues: cos and sin of a rounded angle W t (absolute error (2 + W t) u each), ~20 roundings on terms <= 2
        tol = aug_bound(Om, De, T, T, ts[-1]) + gam(20) * 4 + 6 * (2 + math.hypot(Om, De) * ts[-1]) * U
        assert np.max(np.abs(a - b)) <= tol


def test_no_emission_probability_and_waiting_time_density():
    """Closed forms against the engine's route: ||exp(-i H_eff tau)|g>||^2 and Gamma |c_e|^2; the density is
    -dP0/dtau (Plenio & Knight eq. 30, checked by integrating it back), and the mean waiting time equals 1/(Gamma
    rho_ee(steady)) because every emission resets the atom to |g> (a renewal process)."""
    for Om, De, G in ((1.0, 0.0, 1.0), (2.0, 1.5, 1.0), (0.2, 0.0, 1.0), (0.5, 0.0, 2.0)):
        Heff = J.effective_hamiltonian(TL.hamiltonian(Om, De), [math.sqrt(G) * TL.SM])
        # both routes: ~30 roundings on terms of modulus <= e^{|eps| tau}(1 + |sbar| tau) <= 30 here: gamma_30 * 30
        # (1.6e-13) plus the backward error u ||H_eff tau|| of expm
        for tau in (0.0, 0.3, 2.0, 9.0):
            psi = linalg.expm(-1j * Heff * tau) @ TL.G
            tol = 30 * gam(30) + 4 * U * float(np.linalg.norm(Heff * tau, 1))
            assert TL.no_emission_probability(tau, Om, De, G) == pytest.approx(float(np.vdot(psi, psi).real), abs=tol)
            assert TL.waiting_time_density(tau, Om, De, G) == pytest.approx(G * abs(psi[0]) ** 2, abs=G * tol)
        if De == 0:
            tt = np.linspace(0, 20, 50)
            assert np.max(np.abs(TL.waiting_time_density(tt, Om, De, G)
                                 - TL.waiting_time_density_resonant(tt, Om, G))) <= G * 30 * gam(30)
        mean, _ = integrate.quad(lambda s: TL.no_emission_probability(s, Om, De, G), 0, np.inf, epsabs=1e-13,
                                 epsrel=1e-12, limit=400)
        rate = G * TL.steady_excited_population(Om, De, 1 / G, 2 / G)
        assert mean == pytest.approx(1 / rate, rel=1e-10)
        P, _ = integrate.quad(lambda s: TL.waiting_time_density(s, Om, De, G), 0, 5.0, epsabs=1e-14, limit=200)
        assert P == pytest.approx(1 - TL.no_emission_probability(5.0, Om, De, G), abs=1e-12)


def test_circular_drive_lab_frame_equals_the_rotating_frame():
    """The rotating-frame transformation of the lab Hamiltonian (module docstring), checked by the Schroedinger
    equation in the lab frame without damping: DOP853 integrated to each time (no dense output), its stated control
    ||e||_2 <= sqrt(n)(atol + rtol max|y|) per accepted step (n = 2, |y_i| <= 1; scipy's RMS error norm <= 1),
    summed over the accepted steps (the flow is unitary, so local errors are not amplified) — a tolerance derived
    from the solver's stated control (review B5, N7: it was a fixed 1e-9)."""
    w0, w, Om = 10.0, 9.0, 1.3
    atol, rtol = 1e-14, 1e-12

    def f(t, y):
        return -1j * (TL.lab_hamiltonian_circular(t, w0, w, Om) @ y)
    for t in np.linspace(0.5, 4, 8):
        sol = integrate.solve_ivp(f, (0, t), TL.G.copy(), method="DOP853", rtol=rtol, atol=atol)
        y = sol.y[:, -1]
        tol = (len(sol.t) - 1) * math.sqrt(2) * (atol + rtol) + 64 * U
        ce, cg = TL.rabi_amplitudes(t, Om, w - w0)
        lab = TL.rotating_frame(t, w).conj().T @ np.array([ce, cg])
        # the rotating-frame H differs from Steck's by the constant Delta/2: a global phase
        ph = np.vdot(lab, y)
        assert abs(abs(ph) - 1) <= 2 * tol and np.max(np.abs(lab * ph / abs(ph) - y)) <= 3 * tol, (t, tol)


# --- quantum jumps --------------------------------------------------------------------------------------------------

def test_trajectory_average_converges_to_the_master_equation():
    """Driven, detuned, decaying and dephased atom (two jump channels), N = 4000: every entry of the averaged
    |psi><psi| (real and imaginary parts of rho_ee, rho_eg) at 21 times against the exact solution within 5 standard
    errors: 63 comparisons (rho_ee real, rho_eg real and imaginary), family-wise false alarm <= 63 * 5.7e-7 = 3.6e-5."""
    Om, De, T1, T2 = 2.0, 0.8, 1.0, 1.2
    H, c = TL.hamiltonian(Om, De), TL.collapse_operators(T1, T2)
    ts = np.linspace(0, 8, 21)
    tr = J.trajectories(H, c, TL.G, ts, 4000, np.random.default_rng(2026), e_ops=[TL.PE, TL.SX, TL.SY])
    ex = OS.propagate(OS.liouvillian(H, c), TL.density_matrix([0, 0, -1]), ts)
    m_ee, s_ee = tr.mean(0), tr.stderr(0)
    assert np.all(np.abs(m_ee - np.real(ex[:, 0, 0])) <= Z * s_ee + 1e-15)
    for k, ref in ((0, np.real(ex[:, 0, 0])), (1, np.array([TL.bloch_vector(r)[0] for r in ex]))):
        lo, hi = tr.interval(k, alpha=1e-6)  # non-asymptotic (Hoeffding), as a second, rigorous check
        assert np.all((lo <= ref + 1e-15) & (ref <= hi + 1e-15))
    # the coherence through sigma_x, sigma_y: u, v
    for k, ref in ((1, [TL.bloch_vector(r)[0] for r in ex]), (2, [TL.bloch_vector(r)[1] for r in ex])):
        assert np.all(np.abs(tr.mean(k) - np.array(ref)) <= Z * tr.stderr(k) + 1e-15), k
    # the statistic is not idle: the standard errors are those of a non-degenerate ensemble
    assert np.all(s_ee[5:] > 1e-3)
    jt = np.concatenate(tr.jump_times)
    assert np.all((jt > 0) & (jt <= ts[-1]))


def test_rare_event_error_bars_lambda_dark_state():
    """Review B5, S5, on the reviewer's case: a Lambda system (e, g1, g2; Omega1 = 1.1, Omega2 = 0.7, decay 0.6 into
    g1 and 0.9 into g2) pumped into its dark state; P_e(t) falls to 1.4e-6 at t = 40 and is carried by very few
    trajectories. With N = 4000 and the reviewer's four seeds, the sample standard error is not an error bar there
    (z = |mean - exact|/stderr reaches hundreds), while ``interval`` (Hoeffding 1963, Theorem 1; alpha = 1e-6 per
    time, 36 comparisons) covers the exact value at every time and seed, and ``contributors`` shows why."""
    e, g1, g2 = np.eye(3, dtype=complex)
    O1, O2 = 1.1, 0.7
    H = 0.5 * O1 * (np.outer(e, g1) + np.outer(g1, e)) + 0.5 * O2 * (np.outer(e, g2) + np.outer(g2, e))
    c = [math.sqrt(0.6) * np.outer(g1, e), math.sqrt(0.9) * np.outer(g2, e)]
    ts = np.linspace(0, 40, 9)
    ex = np.real(OS.propagate(OS.liouvillian(H, c), np.outer(g1, g1), ts)[:, 0, 0])
    zmax = 0.0
    for seed in (101, 1, 2, 3):
        tr = J.trajectories(H, c, g1, ts, 4000, np.random.default_rng(seed), e_ops=[np.outer(e, e)])
        lo, hi = tr.interval(0, alpha=1e-6)
        assert np.all((lo <= ex + 1e-15) & (ex <= hi + 1e-15)), (seed, lo, ex, hi)
        m, se = tr.mean(0), tr.stderr(0)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(se > 0, np.abs(m - ex) / se, 0.0)
        zmax = max(zmax, float(z[-1]))
        n_c = tr.contributors(0)  # trajectories with P_e > 1e-3
        assert n_c[0] == 0 and n_c[1] > 1000 and n_c[-1] <= 10, n_c
        # the interval adapts to the mean (KL form): narrower than the additive Hoeffding bound (his eq. 2.3,
        # +-sqrt(ln(2/alpha)/(2N)) = +-0.043) wherever the mean is small; it is wider than 2 x 5 standard errors
        # when the values are spread inside [0, 1] (measured at t = 10: 0.022 = 30 stderr): the price of holding for
        # every N without the central-limit approximation
        assert np.all(hi[1:] - lo[1:] < 2 * math.sqrt(math.log(2 / 1e-6) / (2 * 4000)))
        assert hi[-1] <= 1.1 * (1 - (1e-6 / 2) ** (1 / 4000)) + m[-1] * 50  # ~ ln(2/alpha)/N: what N can resolve
    assert zmax > 50  # the documented failure of stderr for rare events (z = 93, 28, 592, 0.06 for these seeds)


def test_hoeffding_interval_edge_cases():
    """The interval of ``Trajectories.interval`` at its edges: all values 0 gives [a, a + (b - a)(1 - (alpha/2)^(1/N))]
    (the limit case of Hoeffding's eq. 2.1, mu^N mirrored); all values at the top gives an interval ending at b;
    values in [lambda_min, lambda_max] of a non-projector observable are scaled by its range; a non-Hermitian
    observable has no interval."""
    N, alpha = 500, 1e-6
    x = np.zeros((1, N, 2))
    tr = J.Trajectories(np.array([0.0, 1.0]), x, None, [], [], [(0.0, 1.0)])
    lo, hi = tr.interval(0, alpha)
    assert np.all(lo == 0) and np.allclose(hi, 1 - (alpha / 2) ** (1 / N), rtol=1e-12, atol=0)
    tr = J.Trajectories(np.array([0.0]), np.full((1, N, 1), 3.0), None, [], [], [(-1.0, 3.0)])
    lo, hi = tr.interval(0, alpha)
    assert hi[0] == 3.0 and 3.0 - 4 * 0.03 < lo[0] < 3.0
    with pytest.raises(ValueError):
        J.Trajectories(np.array([0.0]), np.zeros((1, 3, 1), complex), None, [], [], [None]).interval(0)
    # a coin: the interval holds the exact mean
    rng = np.random.default_rng(4)
    v = (rng.random((1, 20000, 1)) < 0.3).astype(float)
    lo, hi = J.Trajectories(np.array([0.0]), v, None, [], [], [(0.0, 1.0)]).interval(0, alpha)
    assert lo[0] < 0.3 < hi[0] and hi[0] - lo[0] < 0.04


def test_waiting_times_follow_the_closed_form_distribution():
    """Resonance fluorescence: the first two intervals of each trajectory (from the start in |g> and between the
    first and second emission; i.i.d. since every emission resets to |g>) against F = 1 - P0 by the DKW inequality at
    alpha = 1e-6. The run is long enough that every trajectory has two emissions (else ValueError)."""
    for (Om, De), seed in zip(((1.0, 0.0), (3.0, 1.0), (0.2, 0.0)), (7, 8, 9)):
        # own seed per case: the sampler inverts the law exactly, so with one seed every case would give the same
        # uniform values F(tau_i) and the same statistic
        G = 1.0
        # 40 mean intervals: P(fewer than 2 emissions) ~ 41 exp(-40) per trajectory if Poisson-like, negligible
        T = 40.0 / (G * TL.steady_excited_population(Om, De, 1 / G, 2 / G))
        tr = J.trajectories(TL.hamiltonian(Om, De), [math.sqrt(G) * TL.SM], TL.G, [0.0, T], 3000,
                            np.random.default_rng(seed))
        wt = np.sort(tr.waiting_times(2, from_start=True))
        n = wt.size
        F = 1 - TL.no_emission_probability(wt, Om, De, G)
        D = max(np.max(np.arange(1, n + 1) / n - F), np.max(F - np.arange(0, n) / n))
        eps = math.sqrt(math.log(2 / 1e-6) / (2 * n))
        assert D <= eps, (Om, De, D, eps)


def test_jump_channels_are_chosen_by_their_rates():
    """A V-free three-level decay |e> -> |g1> (Gamma1), |e> -> |g2> (Gamma2): the fraction of jumps into channel 1
    is Gamma1/(Gamma1 + Gamma2) (binomial, z = 5), and the time of the single jump is exponential with rate
    Gamma1 + Gamma2 (DKW at alpha = 1e-6)."""
    G1, G2 = 0.7, 2.1
    e, g1, g2 = np.eye(3, dtype=complex)
    c = [math.sqrt(G1) * np.outer(g1, e), math.sqrt(G2) * np.outer(g2, e)]
    N = 6000
    tr = J.trajectories(np.zeros((3, 3)), c, e, [0.0, 60.0], N, np.random.default_rng(31))
    ch = np.concatenate(tr.jump_channels)
    assert ch.size == N  # exactly one jump each (the ground states are dark); P(no jump by 60) = exp(-168)
    p = G1 / (G1 + G2)
    assert abs(np.mean(ch == 0) - p) <= Z * math.sqrt(p * (1 - p) / N)
    t = np.sort(np.concatenate(tr.jump_times))
    F = 1 - np.exp(-(G1 + G2) * t)
    D = max(np.max(np.arange(1, N + 1) / N - F), np.max(F - np.arange(N) / N))
    assert D <= math.sqrt(math.log(2 / 1e-6) / (2 * N))


def test_seed_reproduces_and_states_average_to_rho():
    H, c = TL.hamiltonian(1.0, 0.3), TL.collapse_operators(2.0, 1.0)
    ts = np.linspace(0, 3, 4)
    a = J.trajectories(H, c, TL.G, ts, 50, np.random.default_rng(5), e_ops=[TL.PE], store_states=True)
    b = J.trajectories(H, c, TL.G, ts, 50, np.random.default_rng(5), e_ops=[TL.PE], store_states=True)
    assert np.array_equal(a.expect, b.expect) and all(np.array_equal(x, y) for x, y in zip(a.jump_times,
                                                                                            b.jump_times))
    rho = a.rho_mean()
    assert np.allclose(np.real(rho[:, 0, 0]), a.mean(0), rtol=0, atol=1e-15)
    for r in rho:
        assert OS.state_checks(r)["trace_err"] <= 1e-14
    with pytest.raises(ValueError):
        J.trajectories(H, c, TL.G, ts, 5, np.random.default_rng(5)).rho_mean()
    with pytest.raises(ValueError):  # censoring is refused, not silently biased
        J.trajectories(H, c, TL.G, [0.0, 0.01], 5, np.random.default_rng(5)).waiting_times(3)


def test_no_jump_propagator_routes_against_expm():
    """Both routes of exp(-i H_eff s) psi against scipy's expm: the eigendecomposition away from the exceptional
    point (within cond(V)(n gamma_n + |mu s| u) of the exact map applied to unit vectors, plus expm's own bound
    u ||A|| + gamma_60), and the Taylor scaling and squaring at the exceptional point Omega = Gamma/2 of a resonantly
    driven decaying atom (there H_eff is not diagonalisable: its eigenvalues -Gamma/4 coincide); m squarings of a
    product with entries within gamma_2 |X||X| each, |X| <= 1 + ||A s||: (m + 1) gamma_4 (1 + ||A s||)^2."""
    rng = np.random.default_rng(41)
    psi = rng.normal(size=(6, 2)) + 1j * rng.normal(size=(6, 2))
    psi /= np.linalg.norm(psi, axis=1)[:, None]
    s = np.array([0.0, 0.01, 0.4, 1.7, 6.0, 25.0])
    for Om, De, G, route in ((1.0, 0.3, 1.0, "eig"), (0.5, 0.0, 1.0, "taylor"), (0.5 + 1e-9, 0.0, 1.0, "taylor")):
        Heff = J.effective_hamiltonian(TL.hamiltonian(Om, De), [math.sqrt(G) * TL.SM])
        prop = J.NoJumpPropagator(Heff)
        assert prop.route == route
        got = prop(s, psi)
        A = -1j * Heff
        for k in range(len(s)):
            ref = linalg.expm(A * s[k]) @ psi[k]
            a = float(np.linalg.norm(A * s[k], 1))
            ref_err = U * a + gam(60) * (1 + a)
            if route == "eig":
                c = float(np.linalg.cond(prop.V))
                tol = c * (2 * gam(2) + 4 * a * U) + ref_err
            else:
                m = max(0, math.ceil(math.log2(max(float(np.max(s)) * float(np.linalg.norm(A, 1)), 1e-300) / 0.5)))
                tol = (m + 1) * gam(4) * (1 + a) ** 2 + ref_err
            assert np.max(np.abs(got[k] - ref)) <= tol, (route, s[k], np.max(np.abs(got[k] - ref)), tol)


def test_waiting_times_at_the_exceptional_point():
    """The same DKW check where H_eff is defective (Omega = Gamma/2, Delta = 0): the Taylor route of the no-jump
    propagation and the critical branch of the closed form (eps = 0 exactly:
    w = Gamma Omega^2 tau^2/4 e^{-Gamma tau/2}). The atom decays into a dark level d (basis e, g, d), so each
    trajectory jumps once; the no-jump evolution on span{e, g} is that of resonance fluorescence (L^+ L = Gamma
    |e><e|), so the time of that jump has the waiting-time law. 6000 samples, alpha = 1e-6."""
    Om, G = 0.5, 1.0
    assert TL.waiting_time_density_resonant(2.0, Om, G) == pytest.approx(G * Om ** 2 * math.exp(-1.0), rel=gam(8))
    H = np.zeros((3, 3), complex)
    H[:2, :2] = TL.hamiltonian(Om, 0.0)
    L = np.zeros((3, 3), complex)
    L[2, 0] = math.sqrt(G)
    assert J.NoJumpPropagator(J.effective_hamiltonian(H, [L])).route == "taylor"
    T = 1.0
    while TL.no_emission_probability(T, Om, 0.0, G) > 1e-12:
        T *= 1.5
    tr = J.trajectories(H, [L], np.array([0, 1, 0], complex), [0.0, T], 6000, np.random.default_rng(43))
    wt = np.sort(tr.waiting_times(1, from_start=True))
    n = wt.size
    F = 1 - TL.no_emission_probability(wt, Om, 0.0, G)
    D = max(np.max(np.arange(1, n + 1) / n - F), np.max(F - np.arange(0, n) / n))
    assert D <= math.sqrt(math.log(2 / 1e-6) / (2 * n)), D


def test_jump_times_are_found_to_round_off():
    """A single decay from |e> (Gamma = 1.3): the jump happens when exp(-Gamma t) = r, i.e. t = -ln(r)/Gamma. The
    test reproduces the generator's draws (the initial r's are the first ntraj numbers) and checks the jump times
    to round-off (Newton converged to |g| <= 8 u r: |delta t| <= 8 u / Gamma, plus the rounding of the exponential)."""
    G = 1.3
    N = 200
    rng = np.random.default_rng(99)
    r = np.random.default_rng(99).random(N)
    tr = J.trajectories(np.zeros((2, 2)), [math.sqrt(G) * TL.SM], TL.E, [0.0, 1.0, 50.0], N, rng)
    t = np.array([x[0] for x in tr.jump_times])
    ref = -np.log(r) / G
    # the exponential's backward error u ||H_eff s|| moves the norm by ~ Gamma s u relatively, i.e. the time by ~ s u
    assert np.all(np.abs(t - ref) <= 64 * U * (1 + G * ref) / G)


# --- which-path decoherence and the GRW baseline ----------------------------------------------------------------------

def test_dephasing_channel_visibility():
    gp = 0.37
    rho0 = 0.5 * np.array([[1, 1], [1, 1]], complex)
    Lsup = OS.liouvillian(np.zeros((2, 2)), DEC.dephasing_operators(gp))
    for t in (0.0, 1.0, 5.0, 30.0):
        rho = OS.propagate(Lsup, rho0, [t])[0]
        assert DEC.visibility(rho) == pytest.approx(float(DEC.dephasing_visibility(t, gp)),
                                                    abs=4 * OS.expm_error_bound(Lsup, t))
        assert abs(rho[0, 0] - 0.5) <= OS.expm_error_bound(Lsup, t)


def test_probe_visibility_duality_and_the_marks_module():
    for th in (0.0, 0.3, math.pi / 4, 1.2, math.pi / 2):
        c1, c2 = DEC.probe_qubit(th)
        V, D = DEC.probe_visibility(c1, c2)
        assert V == pytest.approx(abs(math.cos(th)), abs=4 * U) and V * V + D * D == pytest.approx(1.0, abs=8 * U)
        for w1 in (0.5, 0.2):
            V, D = DEC.probe_visibility(c1, c2, w1)
            Vm, Dm = marks.englert(math.sqrt(w1) * c1, math.sqrt(1 - w1) * c2)  # second route (eigenvalues)
            assert V == pytest.approx(Vm, abs=1e-15) and D == pytest.approx(Dm, abs=1e-14)
            assert V * V + D * D == pytest.approx(1.0, abs=1e-14)
    Ks = DEC.probe_kraus(*DEC.probe_qubit(0.9))
    assert np.allclose(sum(K.conj().T @ K for K in Ks), np.eye(2), rtol=0, atol=4 * U)


def test_probe_stream_lindblad_equals_the_closed_form():
    """A three-state probe with a complex overlap chi: the Lindblad equation with jump operators sqrt(rate) K_k
    against rho_12(0) exp(-rate t (1 - chi)) (decay and fringe shift), populations unchanged."""
    c1 = np.array([1.0, 0.0, 0.0], complex)
    c2 = np.array([0.6, 0.48j, 0.64], complex)
    chi = DEC.probe_overlap(c1, c2)
    assert chi == pytest.approx(0.6, abs=4 * U)
    c2 = np.array([0.6 * np.exp(0.7j), 0.48j, 0.64], complex)
    chi = DEC.probe_overlap(c1, c2)
    rate = 1.7
    Lsup = OS.liouvillian(np.zeros((2, 2)), DEC.probe_stream_operators(rate, c1, c2))
    rho0 = np.array([[0.36, 0.48], [0.48, 0.64]], complex)
    for t in (0.2, 1.0, 4.0):
        rho = OS.propagate(Lsup, rho0, [t])[0]
        b = OS.expm_error_bound(Lsup, t)
        assert abs(rho[0, 1] - DEC.probe_stream_coherence(t, rate, chi, 0.48)) <= b + gam(10)
        assert abs(rho[0, 0] - 0.36) <= b
        V = 2 * abs(rho[0, 1])
        assert V == pytest.approx(float(DEC.probe_stream_visibility(t, rate, chi, 0.96)), abs=2 * b + gam(10))


def test_converging_paths_equal_the_grw_pattern_shift():
    """Two routes to the GRW factor of a double slit: the density-matrix rate averaged over the converging paths
    (core.quantum.decoherence) and the characteristic function of the pattern shift at the fringe frequency k d/z
    (theories.alternatives.collapse.grw_shift_cf); and the Gauss-Legendre quadrature of the separation history."""
    k, z, rc = 2 * math.pi / 5e-12, 1.0, 1e-7
    for d in (1e-12, 1e-9, 3e-8, 1e-7, 4e-7, 1e-5):
        for lam_T in (0.01, 1.0, 7.0):
            a = DEC.converging_paths_visibility(d, lam_T, rc)
            b = abs(complex(collapse.grw_shift_cf(np.array([k * d / z]), k, z, lam_T, rc)[0]))
            # both: exp(-lam_T loss); the loss within 16 u relative on the core's side; collapse.py forms 1 - g with
            # g = sqrt(pi) erf(a)/(2a) rounded (4 operations): an absolute 8 u in the loss, which dominates for small
            # a; the core's series branch (x < 1e-4) is accurate to x^6/42; exp adds 2 u per side
            loss = DEC.mean_kick_loss_converging(d, rc)
            tol = a * (lam_T * (loss * 16 * U + 8 * U + (d / (2 * rc)) ** 6) + 4 * U)
            assert abs(a - b) <= tol, (d, lam_T, abs(a - b), tol)
            # Gauss-Legendre with 200 nodes: the truncation error for the entire integrand exp(-x^2 u^2), x <= 50,
            # is below exp(-47) by the Bernstein-ellipse bound (rho = 1.32); rounding: lam_T gamma_400 in the
            # exponent, plus exp and the closed form's 16 u
            c = DEC.separation_visibility(lambda t: d * (1 - t), 1.0, lam_T, rc)
            assert c == pytest.approx(a, rel=lam_T * (gam(400) + 16 * U) + 8 * U)


def test_grw_kicks_have_the_gaussian_overlap_of_the_baseline():
    """The momentum kicks of collapse.grw_kicks give <exp(i q d)> = exp(-d^2/(4 r_C^2)) (the Gaussian-kick
    overlap), checked on 200000 samples within 5 standard errors at 4 separations."""
    rc = 1e-7
    q = collapse.grw_kicks(np.random.default_rng(8), 200000, rc)
    for d in (0.5e-7, 1e-7, 2e-7, 4e-7):
        x = np.cos(q * d)
        assert abs(np.mean(x) - float(DEC.gaussian_kick_overlap(d, rc))) <= Z * np.std(x, ddof=1) / math.sqrt(x.size)
        assert abs(np.mean(np.sin(q * d))) <= Z * np.std(np.sin(q * d), ddof=1) / math.sqrt(x.size)


def test_compare_grw_with_the_baseline():
    d, T, m = 1e-6, 1e-3, 720.0
    r = CB.compare(d, T, m, lam_amu=3.0, rc=1e-7, gamma_phi=10.0, probe_rate=50.0, probe_overlap=0.9)
    assert r["exponent_grw"] == pytest.approx(3.0 * m * T * DEC.mean_kick_loss_converging(d, 1e-7), rel=gam(4))
    assert r["exponent_baseline"] == pytest.approx(10.0 * T + 50.0 * T * 0.1, rel=gam(6))
    assert r["V_total"] == pytest.approx(r["V_grw"] * r["V_baseline"], rel=gam(8))
    # Bassi et al. eq. 22 at constant separation, and the saturation at the full rate for d >> r_C
    assert CB.grw_rate(2e-7, 1.0, 1e-16, 1e-7) == pytest.approx(1e-16 * (1 - math.exp(-1.0)), rel=gam(6))
    assert CB.grw_rate(1e-3, 1.0, 1e-16, 1e-7) == 1e-16
    r2 = CB.compare(2e-7, 1.0, 1.0, 1e-16, 1e-7, converging=False)
    assert r2["exponent_grw"] == pytest.approx(CB.grw_rate(2e-7, 1.0, 1e-16, 1e-7), rel=gam(4))
    assert r2["grw_over_baseline"] == math.inf
    # an environment of Gaussian kicks (callable overlap) with GRW's rate and width reproduces GRW exactly
    r3 = CB.compare(d, T, m, 3.0, 1e-7, probe_rate=3.0 * m, probe_overlap=lambda s: DEC.gaussian_kick_overlap(s, 1e-7))
    assert r3["exponent_baseline"] == pytest.approx(r3["exponent_grw"], rel=1e-12)
    assert r3["grw_over_baseline"] == pytest.approx(1.0, rel=1e-12)
    assert DEC.mean_kick_loss_converging(1e-12, 1e-7) == pytest.approx((1e-12 / 2e-7) ** 2 / 3, rel=1e-12)
    x = 1e-4 * 2e-7  # continuity of the series branch at the switch
    assert DEC.mean_kick_loss_converging(x * 0.999999, 1e-7) == pytest.approx(
        DEC.mean_kick_loss_converging(x * 1.000001, 1e-7), rel=1e-5)
