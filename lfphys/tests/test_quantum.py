# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Quantum mechanics of the core and the interpretations and alternatives outside it."""

import cmath
import math

import numpy as np
import pytest
from scipy import constants as sc
from scipy import integrate

from lfphys.core.quantum import compton, hydrogen, qubits as Q, schrodinger1d as S1, transfer
from lfphys.theories.alternatives import local_hidden as LHV
from lfphys.theories.interpretations import bohm, copenhagen, everett

rng = np.random.default_rng(3)


# --- Schroedinger -------------------------------------------------------------------------------------------
def test_free_packet_spreads_as_the_closed_form_and_keeps_norm():
    g = S1.Grid(np.linspace(-200, 200, 4096, endpoint=False), m=1.0)
    sigma, k0 = 2.0, 1.5
    psi = g.gaussian(-40.0, k0, sigma)
    dt, n = 0.05, 800
    step = g.stepper(np.zeros(g.n), dt)
    for _ in range(n):
        psi = step(psi)
    t = dt * n
    w = np.abs(psi) ** 2 * g.dx
    sd = math.sqrt(np.sum(w * g.x**2) - np.sum(w * g.x) ** 2)
    assert g.norm(psi) == pytest.approx(1.0, abs=1e-12)
    assert sd == pytest.approx(g.free_gaussian_width(sigma, t), rel=1e-9)
    assert g.mean_x(psi) == pytest.approx(-40.0 + k0 * t, abs=1e-8)


def test_harmonic_oscillator_spectrum_and_coherent_state():
    m, w = 1.0, 0.7
    g = S1.Grid(np.linspace(-20, 20, 400, endpoint=False), m=m)
    V = 0.5 * m * w * w * g.x**2
    E, vec = g.eigenstates(V, 8)
    assert np.allclose(E, S1.harmonic_levels(np.arange(8), 1.0, w), rtol=1e-11)
    # a displaced ground state oscillates with period 2 pi / w and keeps its energy
    g2 = S1.Grid(np.linspace(-20, 20, 1024, endpoint=False), m=m)
    V2 = 0.5 * m * w * w * g2.x**2
    psi = g2.gaussian(3.0, 0.0, math.sqrt(1.0 / (2 * m * w)))
    E0 = g2.energy(psi, V2)
    T = 2 * math.pi / w
    n = 2000
    step = g2.stepper(V2, T / n)
    for _ in range(n):
        psi = step(psi)
    assert g2.mean_x(psi) == pytest.approx(3.0, abs=1e-5)
    assert g2.energy(psi, V2) == pytest.approx(E0, rel=1e-9)


def test_staircase_amplitudes_against_closed_forms():
    """Complex amplitudes of a rectangular barrier, t = 1/(cos qa - i (k^2 + q^2)/(2kq) sin qa) with the transmitted
    wave referred to the barrier's far edge (and the evanescent form); free space gives t = e^{ika}; a smooth profile
    agrees with the transfer matrices' |t|^2 and converges as h^2; many strengths at once equal one at a time."""
    E, V, a = 3.0, 1.2, 1.7
    k, q = math.sqrt(2 * E), math.sqrt(2 * (E - V))
    t_cf = 1 / (math.cos(q * a) - 1j * (k * k + q * q) / (2 * k * q) * math.sin(q * a))
    t, r = transfer.staircase_amplitudes(E, np.full(400, V), a / 400)
    assert abs(t - t_cf) < 1e-12 and abs(abs(t) ** 2 + abs(r) ** 2 - 1) < 1e-12
    t0, r0 = transfer.staircase_amplitudes(E, np.zeros(10), 0.3)
    assert abs(t0 - np.exp(1j * k * 3.0)) < 1e-12 and abs(r0) < 1e-12
    E2, V2 = 0.8, 2.0  # an evanescent (thin) barrier
    kk, kap = math.sqrt(2 * E2), math.sqrt(2 * (V2 - E2))
    t_ev = 1 / (math.cosh(kap * a) + 1j * (kap * kap - kk * kk) / (2 * kk * kap) * math.sinh(kap * a))
    t, _ = transfer.staircase_amplitudes(E2, np.full(50, V2), a / 50)
    assert abs(t - t_ev) < 1e-12
    prof = lambda x: 0.9 * np.exp(-np.asarray(x) ** 2)  # noqa: E731

    def smooth(n):
        z = np.linspace(-3, 3, n + 1)
        mid = 0.5 * (z[1:] + z[:-1])
        return transfer.staircase_amplitudes(E, prof(mid), 6.0 / n)[0], mid
    t1, _ = smooth(1000)
    tg, mid = smooth(2000)
    t4, _ = smooth(4000)
    assert abs(abs(tg) ** 2 - transfer.transmission_profile(E, prof, -3.0, 3.0, 2000)[0]) < 1e-9
    assert 3.5 < abs(t1 - tg) / abs(tg - t4) < 4.5  # second order in h
    z = np.linspace(-3, 3, 2001)
    s = np.array([0.0, 0.5, 1.0])[:, None] * prof(mid)[None, :]
    tb, _ = transfer.staircase_amplitudes(E, s, z[1] - z[0])
    for i, f in enumerate([0.0, 0.5, 1.0]):
        assert abs(tb[i] - transfer.staircase_amplitudes(E, f * prof(mid), z[1] - z[0])[0]) < 1e-13


def test_transfer_matrix_against_closed_forms():
    for E in (0.2, 0.5, 0.99, 1.3, 2.7):
        T, R, *_ = transfer.transmission(E, [0.0, 2.0], [0.0, 1.0, 0.0])
        assert T == pytest.approx(transfer.rectangular_barrier(E, 1.0, 2.0), rel=1e-12)
        assert T + R == pytest.approx(1.0, abs=1e-12)
    # a thin tall barrier -> delta barrier with alpha = V0 a
    a, alpha, E = 1e-4, 0.8, 0.6
    T, *_ = transfer.transmission(E, [0.0, a], [0.0, alpha / a, 0.0])
    assert T == pytest.approx(transfer.delta_barrier(E, alpha), rel=1e-3)


def test_wave_packet_tunnelling_matches_stationary_transmission():
    """Time-dependent route: the transmitted probability of a packet = int T(k) |phi(k)|^2 dk. On the grid the barrier
    is n samples, i.e. a width n dx with edges half-way between grid points (T depends exponentially on the width)."""
    g = S1.Grid(np.linspace(-300, 300, 16384, endpoint=False), m=1.0)
    V0, a = 1.0, 1.5
    n = int(round(a / g.dx))
    i0 = int(np.searchsorted(g.x, 0.0))
    V = np.zeros(g.n)
    V[i0:i0 + n] = V0
    width, right = n * g.dx, g.x[i0] - g.dx / 2 + n * g.dx
    k0, sigma = 1.3, 8.0
    psi = g.gaussian(-80.0, k0, sigma)
    step = g.stepper(V, 0.01)
    for _ in range(14000):
        psi = step(psi)
    p_trans = float(np.sum(np.abs(psi[g.x > right]) ** 2) * g.dx)
    sk = 1 / (2 * sigma)  # momentum spread of the packet
    ks = np.linspace(k0 - 8 * sk, k0 + 8 * sk, 2001)
    phi2 = np.exp(-((ks - k0) ** 2) / (2 * sk * sk))
    Tk = np.array([transfer.transmission(0.5 * k * k, [0.0, width], [0.0, V0, 0.0])[0] for k in ks])
    assert p_trans == pytest.approx(np.sum(Tk * phi2) / np.sum(phi2), abs=3e-4)


def test_bohm_trajectories_are_equivariant():
    """Particles started |psi|^2-distributed stay |psi|^2-distributed (the interpretation adds no prediction for
    positions): compare the quantiles of the ensemble with those of |psi(t)|^2."""
    g = S1.Grid(np.linspace(-100, 100, 4096, endpoint=False), m=1.0)
    psi = g.gaussian(-10.0, 0.8, 1.5) + g.gaussian(10.0, -0.8, 1.5)
    psi /= math.sqrt(g.norm(psi))
    rho = np.abs(psi) ** 2 * g.dx
    cdf = np.cumsum(rho) / rho.sum()
    qs = (np.arange(400) + 0.5) / 400
    xs = np.interp(qs, cdf, g.x)
    dt = 0.01
    step = g.stepper(np.zeros(g.n), dt)
    for _ in range(1500):
        new = step(psi)
        xs = bohm.advance_1d(xs, g, psi, new, dt)
        psi = new
    rho = np.abs(psi) ** 2 * g.dx
    cdf = np.cumsum(rho) / rho.sum()
    ref = np.interp(qs, cdf, g.x)
    assert np.median(np.abs(np.sort(xs) - ref)) < 0.05


# --- qubits and Bell -------------------------------------------------------------------------------------------
def test_singlet_correlations_and_tsirelson():
    for _ in range(20):
        a, b = rng.normal(size=3), rng.normal(size=3)
        a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
        assert Q.spin_correlation(Q.SINGLET, a, b) == pytest.approx(-a @ b, abs=1e-14)
    E = lambda x, y: Q.spin_correlation(Q.SINGLET, [math.cos(x), 0, math.sin(x)], [math.cos(y), 0, math.sin(y)])  # noqa: E731
    S = Q.chsh(E, 0.0, math.pi / 2, math.pi / 4, 3 * math.pi / 4)
    assert abs(S) == pytest.approx(2 * math.sqrt(2), rel=1e-14)
    for _ in range(200):  # never beyond Tsirelson
        assert abs(Q.chsh(E, *rng.uniform(0, 2 * math.pi, 4))) <= 2 * math.sqrt(2) + 1e-12


def test_photon_pairs_malus_correlation():
    for a, b in rng.uniform(0, math.pi, (10, 2)):
        E = Q.correlation(Q.PHI_PLUS, Q.polarizer_observable(a), Q.polarizer_observable(b))
        assert E == pytest.approx(math.cos(2 * (a - b)), abs=1e-14)


def test_entanglement_measures_and_measurement():
    rho = Q.dm(Q.SINGLET)
    assert Q.concurrence(rho) == pytest.approx(1.0, abs=1e-12)
    assert Q.entropy(Q.ptrace(rho, 0)) == pytest.approx(1.0, abs=1e-12)
    assert Q.concurrence(Q.dm(Q.ket(1, 0, 0, 0))) == pytest.approx(0.0, abs=1e-12)
    up = Q.dm(Q.ket(1, 0))
    p = Q.measure(up, Q.projectors([math.sin(0.6), 0, math.cos(0.6)]))
    assert p[0] == pytest.approx(math.cos(0.3) ** 2, rel=1e-14)


def test_larmor_precession():
    U = Q.larmor(2.0, math.pi / 4)  # omega t = pi/2: a quarter turn about z of a spin along x
    rho = U @ Q.dm(Q.ket(1, 1)) @ U.conj().T
    assert np.allclose(Q.bloch(rho), [0, 1, 0], atol=1e-14)


def test_local_hidden_variables_obey_chsh_and_quantum_violates():
    a, a2, b, b2 = 0.0, math.pi / 2, math.pi / 4, 3 * math.pi / 4
    S_lhv = LHV.sign_model_E(a - b) - LHV.sign_model_E(a - b2) + LHV.sign_model_E(a2 - b) + LHV.sign_model_E(a2 - b2)
    assert abs(S_lhv) == pytest.approx(2.0, abs=1e-12)  # the sign model saturates the bound here
    A, B = LHV.sign_model(0.3, 1.1, 400000, rng)
    assert np.mean(A * B) == pytest.approx(LHV.sign_model_E(0.8), abs=0.006)
    for _ in range(200):
        x = rng.uniform(0, 2 * math.pi, 4)
        S = (LHV.polarization_model_E(x[0], x[2]) - LHV.polarization_model_E(x[0], x[3])
             + LHV.polarization_model_E(x[1], x[2]) + LHV.polarization_model_E(x[1], x[3]))
        assert abs(S) <= 2 + 1e-12


def test_interpretations_share_the_born_weights():
    psi = Q.ket(0.6, 0.8j)
    projs = Q.projectors([0, 0, 1])
    br = everett.branch(psi, projs)
    assert [b["weight"] for b in br] == pytest.approx([0.36, 0.64], abs=1e-14)
    ks = [copenhagen.measure_and_collapse(psi, projs, rng)[0] for _ in range(20000)]
    assert np.mean(ks) == pytest.approx(0.64, abs=0.012)
    tree = everett.branch_tree([[0.36, 0.64]] * 3)
    assert sum(w for _, w in tree) == pytest.approx(1.0, abs=1e-14) and len(tree) == 8


# --- hydrogen and Compton -------------------------------------------------------------------------------------
def test_dirac_levels_reduce_to_schrodinger_and_fine_structure():
    a = hydrogen.ALPHA
    for n in (1, 2, 3):
        E = hydrogen.dirac_level(n, 0.5, M=math.inf)
        bohr = -hydrogen.ME_C2 * a * a / (2 * n * n)
        # Sommerfeld expansion: E = bohr [1 + (a/n)^2 (n/(j+1/2) - 3/4)] + O(a^6)
        assert E == pytest.approx(bohr * (1 + (a / n) ** 2 * (n / 1.0 - 0.75)), rel=1e-8)
    inf = math.inf
    split = hydrogen.frequency(hydrogen.dirac_level(2, 0.5, M=inf), hydrogen.dirac_level(2, 1.5, M=inf))
    ref = hydrogen.ME_C2 * a**4 / 32 / sc.h  # leading order alpha^4 m c^2 / 32
    assert split == pytest.approx(ref, rel=1e-4)
    assert split / 1e9 == pytest.approx(10.95, abs=0.05)  # GHz (infinite nuclear mass)
    # with recoil the fine-structure splitting scales by mu / m_e to leading order
    split_mu = hydrogen.frequency(hydrogen.dirac_level(2, 0.5), hydrogen.dirac_level(2, 1.5))
    assert split_mu / split == pytest.approx(sc.m_p / (sc.m_e + sc.m_p), rel=1e-6)
    with pytest.raises(ValueError):
        hydrogen.dirac_level(1, 1.5)


def test_hydrogen_1s2s_against_the_measurement():
    """Parthey et al., PRL 107, 203001 (2011): f(1S-2S) = 2 466 061 413 187 035 (10) Hz (hyperfine centroid).
    Dirac with recoil is above it by the 1S - 2S Lamb shift difference (~ 8.2 GHz, 3.3e-6); the infinite-mass
    level is off by m_e/m_p, Schroedinger by the fine structure (review 2026-10-23, E1)."""
    f_meas = 2466061413187035.0
    f = hydrogen.frequency(hydrogen.dirac_level(1, 0.5), hydrogen.dirac_level(2, 0.5))
    assert 2.0e-6 < f / f_meas - 1 < 4.0e-6
    f_inf = hydrogen.frequency(hydrogen.dirac_level(1, 0.5, M=math.inf), hydrogen.dirac_level(2, 0.5, M=math.inf))
    assert f_inf / f_meas - 1 == pytest.approx(sc.m_e / sc.m_p, rel=0.01)
    f_s = hydrogen.frequency(hydrogen.schrodinger_level(1), hydrogen.schrodinger_level(2))
    assert -1.2e-5 < f_s / f_meas - 1 < -7e-6


def test_compton_shift_and_klein_nishina_total():
    E = 662e3 * sc.electron_volt  # the Cs-137 line
    th = 1.0
    lam = sc.h * sc.c / E
    lam2 = sc.h * sc.c / (E * compton.energy_ratio(E, th))
    assert lam2 - lam == pytest.approx(compton.LAMBDA_C * (1 - math.cos(th)), rel=1e-12)
    for E in (1e-3 * compton.ME_C2, 0.3 * compton.ME_C2, 5 * compton.ME_C2):
        num, _ = integrate.quad(lambda t: 2 * math.pi * math.sin(t) * compton.klein_nishina(E, t), 0, math.pi,
                                epsabs=0, epsrel=1e-12)
        assert num == pytest.approx(compton.total_cross_section(E), rel=1e-6)
    sigma_t = sc.physical_constants["Thomson cross section"][0]
    assert compton.total_cross_section(1e-9 * compton.ME_C2) == pytest.approx(sigma_t, rel=1e-6)


def test_klein_nishina_total_in_the_low_energy_window():
    """1e-5 <= E/mc^2 <= 1: the series / closed form against the closed form in 60-digit arithmetic (mpmath); the old
    log(1 + 2x) route lost 6e-5 near x = 1e-4 (review 2026-10-23, E2)."""
    mpmath = pytest.importorskip("mpmath")
    mpmath.mp.dps = 60
    worst = 0.0
    for x in np.geomspace(1e-5, 1.0, 157):
        X = mpmath.mpf(x)
        lg = mpmath.log(1 + 2 * X)
        ref = 2 * mpmath.pi * ((1 + X) / X**3 * (2 * X * (1 + X) / (1 + 2 * X) - lg) + lg / (2 * X)
                               - (1 + 3 * X) / (1 + 2 * X) ** 2)
        got = compton.total_cross_section(x * compton.ME_C2) / compton.R_E**2
        worst = max(worst, abs(got / float(ref) - 1))
    assert worst < 1e-12, worst


def test_pair_sampling_reproduces_the_born_correlation():
    a, b = 0.2, 0.9
    A, B = Q.sample_pairs(Q.PHI_PLUS, Q.polarizer_projectors(a), Q.polarizer_projectors(b), 200000, rng)
    sa, sb = 1 - 2 * A, 1 - 2 * B  # index 0 = transmitted = +1
    assert np.mean(sa * sb) == pytest.approx(math.cos(2 * (a - b)), abs=0.006)
    assert np.mean(sa) == pytest.approx(0.0, abs=0.006)  # no signalling: the marginal does not see b


def test_transmission_profile_matches_closed_forms_and_converges():
    E = np.linspace(0.2, 2.5, 40)
    rect = lambda x: np.where((x >= 0) & (x < 2.0), 1.0, 0.0)  # noqa: E731
    T = transfer.transmission_profile(E, rect, 0.0, 2.0, 1)
    ref = np.array([transfer.rectangular_barrier(e, 1.0, 2.0) for e in E])
    assert np.allclose(T, ref, rtol=1e-10)
    # a smooth barrier: second-order convergence in the number of slices
    smooth = lambda x: 1.0 / np.cosh(np.asarray(x, float)) ** 2  # noqa: E731  (Poschl-Teller)
    t1 = transfer.transmission_profile(E, smooth, -15, 15, 2000)
    t2 = transfer.transmission_profile(E, smooth, -15, 15, 4000)
    assert np.max(np.abs(t2 - t1)) < 2e-5  # second order: 1.5e-5 -> 3.7e-6
    # Poschl-Teller V0 / cosh^2(x/d) has a closed-form T (Landau & Lifshitz, problem to §25):
    # T = sinh^2(pi k d) / (sinh^2(pi k d) + cos^2(pi/2 sqrt(1 - 8 m V0 d^2 / hbar^2)))  for 8 m V0 d^2 < hbar^2,
    # with cosh^2 (pi/2 sqrt(8 m V0 d^2/hbar^2 - 1)) in place of cos^2 otherwise (here m = hbar = d = V0 = 1)
    k = np.sqrt(2 * E)
    pt = np.sinh(np.pi * k) ** 2 / (np.sinh(np.pi * k) ** 2 + np.cosh(np.pi / 2 * np.sqrt(8 - 1)) ** 2)
    assert np.allclose((4 * t2 - t1) / 3, pt, atol=2e-6)


def test_bohm_quantile_rule_equals_integrated_guidance():
    """The exact 1-D construction (trajectory = conserved quantile of |psi|^2) against the guidance equation
    integrated step by step (Heun): an independent route for the same trajectories. The integrated route has a
    dt-independent error where it crosses interference nodes (linear interpolation of v = j/rho on the grid; measured
    max 0.71 for dt = 0.01, 0.005, 0.0025): the quantile rule is the more accurate of the two."""
    g = S1.Grid(np.linspace(-100, 100, 4096, endpoint=False), m=1.0)
    psi = g.gaussian(-10.0, 0.8, 1.5) + g.gaussian(10.0, -0.8, 1.5)
    psi /= math.sqrt(g.norm(psi))
    qs = (np.arange(200) + 0.5) / 200
    xs = bohm.quantile_positions(g.x, np.abs(psi) ** 2, 0.0, qs)
    dt = 0.005
    step = g.stepper(np.zeros(g.n), dt)
    for _ in range(3000):
        new = step(psi)
        xs = bohm.advance_1d(xs, g, psi, new, dt)
        psi = new
    exact = bohm.quantile_positions(g.x, np.abs(psi) ** 2, 0.0, qs)
    assert np.median(np.abs(xs - exact)) < 0.02 and np.max(np.abs(xs - exact)) < 1.0


def test_transfer_matrices_do_not_depend_on_the_position_and_survive_thick_barriers():
    """Review 2026-10-23, E4: a barrier at x = 1000 (kappa x ~ 1000) used to overflow / give NaN."""
    ref = transfer.rectangular_barrier(0.5, 1.0, 2.0)
    for x0 in (0.0, 600.0, 1000.0, -5000.0, 1e5):
        T, R, t, r = transfer.transmission(0.5, [x0, x0 + 2.0], [0.0, 1.0, 0.0])
        assert T == pytest.approx(ref, rel=1e-12) and T + R == pytest.approx(1.0, abs=1e-14)
        Tp = transfer.transmission_profile(np.array([0.5]), lambda x: np.where((x > x0) & (x < x0 + 2.0), 1.0, 0.0),
                                           x0, x0 + 2.0, 1)[0]
        assert Tp == pytest.approx(ref, rel=1e-12)
    # a barrier 2000 decay lengths thick: T underflows to 0, R = 1, no exception
    T, R, _, _ = transfer.transmission(0.5, [0.0, 2000.0], [0.0, 1.0, 0.0])
    assert T == 0.0 and R == pytest.approx(1.0, abs=1e-14)
    thick = lambda x: np.where((x > 0) & (x < 2000.0), 1.0, 0.0)  # noqa: E731
    assert transfer.transmission_profile(np.array([0.5]), thick, 0.0, 2000.0, 400)[0] == 0.0
    # the phases still refer to the origin: shifting the barrier by L multiplies r by e^{2 i k L}
    k = math.sqrt(2 * 0.5)
    _, _, _, r0 = transfer.transmission(0.5, [0.0, 2.0], [0.0, 1.0, 0.0])
    _, _, _, r1 = transfer.transmission(0.5, [3.0, 5.0], [0.0, 1.0, 0.0])
    assert r1 == pytest.approx(r0 * cmath.exp(2j * k * 3.0), abs=1e-13)


def test_transmission_profile_reflection_and_absorption():
    """R from the vectorised profile equals the scalar route; with an absorbing potential -iW, 1 - R - T > 0 is the
    absorbed fraction and a long gentle ramp reflects little (the v03 detectors are chosen this way)."""
    E = np.array([0.3, 0.5, 2.0])
    T, R = transfer.transmission_profile(E, lambda x: np.where((x > 0) & (x < 2), 1.0, 0.0), 0.0, 2.0, 1,
                                         return_r=True)
    for Ei, Ti, Ri in zip(E, T, R):
        T1, R1, _, _ = transfer.transmission(Ei, [0.0, 2.0], [0.0, 1.0, 0.0])
        assert Ti == pytest.approx(T1, rel=1e-12) and Ri == pytest.approx(R1, rel=1e-10)
    W = lambda x: -1j * 0.5 * np.clip(x / 60.0, 0, 1) ** 2  # noqa: E731
    T, R = transfer.transmission_profile(np.array([0.5, 5.0]), W, 0.0, 60.0, 3000, return_r=True)
    assert np.all(R < 1e-6) and np.all(1 - R - T > 0.999)
