# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.optics.polarization against closed forms and second methods (the EX2 design
``sources/explore_EX2_2026-11-18_design.md`` §3.5): the conventions (basis, handedness, rotations), Malus's law for
ideal and real analysers, Brewster's reflected state, the degree of polarisation of reflected light, the phase
difference of total internal reflection against Stratton's closed form and against Fresnel's coefficients evaluated
with 30 digits (mpmath, tests only), energy, Mueller against Jones, passivity, and photon sampling against the Born
probabilities with exact binomial tails."""

import cmath
import math

import mpmath
import numpy as np
import pytest
from scipy import stats as sps

from lfphys.core.optics import interfaces
from lfphys.core.optics import polarization as P
from lfphys.i18n import is_t

D = math.radians
P_5SIGMA = math.erfc(5.0 / math.sqrt(2.0))  # two-sided tail of 5 standard deviations


def _random_rho(rng, pure: bool | None = None) -> np.ndarray:
    """A random density matrix of trace 1 (pure or mixed)."""
    if pure is None:
        pure = rng.random() < 0.3
    if pure:
        J = rng.normal(size=2) + 1j * rng.normal(size=2)
        return P.density(J / np.linalg.norm(J))
    G = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    rho = G @ G.conj().T
    return rho / np.trace(rho).real


def _random_k(rng):
    k1 = rng.uniform(0.0, 1.0)
    return k1, rng.uniform(0.0, k1)


STRUCTURES = [  # (ns, ds) in nm at 633 nm: single boundaries (both sides, TIR), lossless stacks, absorbing films
    ([1.0, 1.515], []), ([1.515, 1.0], []), ([1.0, 1.75], []), ([1.33, 1.0], []),
    ([1.0, 1.38, 1.52], [114.7]), ([1.0] + [2.3, 1.45] * 4 + [1.52], [59.8, 94.8] * 4),
    ([1.5, 1.0, 1.5], [200.0]), ([1.0, 0.2 + 3.3j, 1.5], [30.0]), ([1.5, 0.2 + 3.3j, 1.0], [50.0]),
    ([1.0, 2.3, 0.5 + 2.0j, 1.45, 1.52], [60.0, 20.0, 95.0]), ([1.0, 1.0 + 0.05j, 1.0], [500.0]),
]


# --- conventions --------------------------------------------------------------------------------------------------
def test_basis_stokes_and_handedness():
    """p = (1, 0), s = (0, 1); S3 > 0 is right-handed: the field turns clockwise for an observer facing the beam
    (Shurcliff), checked on the field's own time trace E(t) = Re(J e^{-i omega t}) with k = p x s; the right-circular
    vector is that of core.quantum.marks."""
    from lfphys.core.quantum import marks
    assert np.allclose(P.stokes(P.jones_linear(0.0)), [1, 1, 0, 0], atol=1e-16)
    assert np.allclose(P.stokes(P.jones_linear(D(90))), [1, -1, 0, 0], atol=1e-15)
    assert np.allclose(P.stokes(P.jones_linear(D(45))), [1, 0, 1, 0], atol=1e-15)
    right = P.jones_ellipse(0.0, D(45))
    assert np.allclose(right, marks.POL_STATES["R"], atol=1e-16)
    assert np.allclose(P.stokes(right), [1, 0, 0, 1], atol=1e-15)
    rng = np.random.default_rng(351)
    for _ in range(200):
        J = rng.normal(size=2) + 1j * rng.normal(size=2)
        S = P.stokes(J)
        wt = np.linspace(0.0, 2 * math.pi, 7)
        E = np.real(J[None, :] * np.exp(-1j * wt)[:, None])
        E2 = np.real(J[None, :] * np.exp(-1j * (wt + 1e-6))[:, None])
        turn = E[:, 0] * E2[:, 1] - E[:, 1] * E2[:, 0]  # z component of E x E(t + dt): > 0 counter-clockwise
        if abs(S[3]) > 1e-6 * S[0]:
            assert np.all(np.sign(turn) == -np.sign(S[3]))  # right-handed (S3 > 0) = clockwise seen facing the beam
        # S3 = 2 Im <E_p E_s*> is minus twice the field's angular velocity term (E x dE/dt)_z / omega
        assert -0.5 * S[3] == pytest.approx(float(np.mean(turn)) / 1e-6, rel=1e-5, abs=1e-9 * S[0])


def test_rotations_follow_shurcliff():
    """R(theta) = [[cos, sin], [-sin, cos]] (Shurcliff §8.7); an element at theta is R(-theta) M0 R(theta); the
    Mueller matrix of a rotated element is T(-2 theta) M T(2 theta)."""
    rng = np.random.default_rng(352)
    for _ in range(200):
        th, psi = rng.uniform(-math.pi, math.pi, 2)
        R = P.rotation(th)
        assert np.allclose(R @ R.T, np.eye(2), atol=1e-15)
        assert np.allclose(R @ P.jones_linear(psi), P.jones_linear(psi - th), atol=1e-15)
        v = P.jones_linear(th)
        assert np.allclose(P.polariser(th), np.outer(v, v.conj()), atol=1e-15)
        M0 = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        lhs = P.mueller(P.rotated(M0, th))
        rhs = P.mueller_rotation(-th) @ P.mueller(M0) @ P.mueller_rotation(th)
        assert np.allclose(lhs, rhs, atol=1e-13 * np.max(np.abs(rhs)))


# --- Malus's law and the analyser -----------------------------------------------------------------------------------
@pytest.mark.parametrize("k1,k2", [(1.0, 0.0), (0.90, 0.009), ("random", None)])
def test_malus_law_ideal_and_real(k1, k2):
    """Linear light at psi through an analyser at alpha: P_pass = k1 cos^2(alpha - psi) + k2 sin^2(alpha - psi)
    (Ratajczyk 1979, eq. (7)), by the Jones route and by the Mueller route, at random psi, alpha (1e-14); the two
    ports add to 1."""
    rng = np.random.default_rng(353)
    for _ in range(1000):
        if k1 == "random":
            a1, a2 = _random_k(rng)
        else:
            a1, a2 = k1, k2
        psi, alpha = rng.uniform(-math.pi, math.pi, 2)
        ports = P.beam_splitter(alpha, a1, a2)
        _, _, pp, pr = P.analyse(P.jones_linear(psi), ports)
        ref = P.malus(psi, alpha, a1, a2)
        assert ref == pytest.approx(a1 * math.cos(alpha - psi) ** 2 + a2 * math.sin(alpha - psi) ** 2, abs=1e-15)
        assert abs(pp - ref) < 1e-14 and abs(pp + pr - 1.0) < 1e-14
        assert abs((P.mueller(ports[0]) @ P.stokes(P.jones_linear(psi)))[0] - ref) < 1e-14


def test_generalised_malus_for_elliptical_light():
    """Ratajczyk 1979, eqs. (5)-(7): for light of ellipticity angle chi with its major axis at a from the analyser's
    axis, I = k2 + (k1 - k2) cos^2 beta with cos 2beta = cos 2chi cos 2a."""
    rng = np.random.default_rng(354)
    for _ in range(1000):
        k1, k2 = _random_k(rng)
        az, alpha = rng.uniform(-math.pi, math.pi, 2)
        chi = rng.uniform(-math.pi / 4, math.pi / 4)
        cos2b = math.cos(2 * chi) * math.cos(2 * (az - alpha))
        ref = k2 + (k1 - k2) * (1 + cos2b) / 2
        _, _, pp, _ = P.analyse(P.jones_ellipse(az, chi), P.beam_splitter(alpha, k1, k2))
        assert abs(pp - ref) < 1e-14


def test_partial_polariser_mueller_matrix_is_ratajczyks():
    """The Mueller matrix of a dichroic plate without retardance (Ratajczyk 1979, eq. (3) with gamma = 0):
    (1/2)[[k1 + k2, k1 - k2, 0, 0], [k1 - k2, k1 + k2, 0, 0], [0, 0, 2 sqrt(k1 k2), 0], [0, 0, 0, 2 sqrt(k1 k2)]]."""
    rng = np.random.default_rng(355)
    for _ in range(300):
        k1, k2 = _random_k(rng)
        g = 2 * math.sqrt(k1 * k2)
        ref = 0.5 * np.array([[k1 + k2, k1 - k2, 0, 0], [k1 - k2, k1 + k2, 0, 0], [0, 0, g, 0], [0, 0, 0, g]])
        assert np.allclose(P.mueller(P.polariser(0.0, k1, k2)), ref, atol=1e-15)


def test_analyser_is_passive_and_its_ports_are_complete():
    """The eigenvalues of A^dagger A lie in [0, 1] (a passive device) and the two ports of the beam splitter add to the
    identity: tr(E_pass rho) + tr(E_reject rho) = tr rho for every state."""
    rng = np.random.default_rng(356)
    for _ in range(1000):
        k1, k2 = _random_k(rng)
        a, b = P.beam_splitter(rng.uniform(-math.pi, math.pi), k1, k2)
        for A in (a, b):
            w = np.linalg.eigvalsh(A.conj().T @ A)
            assert w[0] >= -1e-15 and w[1] <= 1.0 + 1e-15
        assert np.allclose(a.conj().T @ a + b.conj().T @ b, np.eye(2), atol=1e-15)
        rho = _random_rho(rng)
        _, _, pp, pr = P.analyse(rho, (a, b))
        assert abs(pp + pr - 1.0) < 1e-14 and pp >= 0 and pr >= 0


def test_refusals_are_translatable(ru):
    for bad in ((1.2, 0.0), (0.5, 0.6), (0.5, -0.1)):
        with pytest.raises(ValueError) as e:
            P.polariser(0.0, *bad)
        assert is_t(e.value.args[0]) and "k₁" in ru(e.value.args[0])
    with pytest.raises(ValueError) as e:
        P.density([[1.0, 0.0], [0.0, -0.5]])
    assert is_t(e.value.args[0]) and "матрица плотности" in ru(e.value.args[0])
    with pytest.raises(ValueError):
        P.density([[1.0, 1.0], [0.0, 1.0]])
    with pytest.raises(ValueError):
        P.density([1.0, 0.0, 0.0])


# --- Stokes, Mueller, the degree of polarisation and the ellipse ---------------------------------------------------
def test_mueller_against_jones():
    """The same Stokes vector by two routes: Stokes(J rho J^dagger) = M(J) Stokes(rho) for random complex J and random
    rho; M is real, multiplicative, and rho is recovered from its Stokes vector."""
    rng = np.random.default_rng(357)
    for _ in range(1000):
        J1 = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        J2 = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        rho = _random_rho(rng)
        out = P.stokes(J1 @ rho @ J1.conj().T)
        scale = max(1.0, float(np.max(np.abs(out))))
        assert np.allclose(P.mueller(J1) @ P.stokes(rho), out, atol=1e-14 * scale)
        full = P._A @ np.kron(J1, J1.conj()) @ P._A_INV
        assert np.max(np.abs(full.imag)) < 1e-14 * np.max(np.abs(full))
        M12 = P.mueller(J1 @ J2)
        assert np.allclose(P.mueller(J1) @ P.mueller(J2), M12, atol=1e-13 * np.max(np.abs(M12)))
        assert np.allclose(P.density_from_stokes(P.stokes(rho)), rho, atol=1e-15)


def test_degree_of_polarisation_by_the_eigenvalues():
    """sqrt(S1^2 + S2^2 + S3^2)/S0 = (l1 - l2)/(l1 + l2) of the density matrix; 1 for every pure state, 0 for I/2."""
    rng = np.random.default_rng(358)
    for _ in range(1000):
        rho = _random_rho(rng, pure=False)
        l1, l2 = sorted(np.linalg.eigvalsh(rho), reverse=True)
        assert P.degree_of_polarisation(rho) == pytest.approx((l1 - l2) / (l1 + l2), abs=1e-14)
        J = rng.normal(size=2) + 1j * rng.normal(size=2)
        assert P.degree_of_polarisation(J) == pytest.approx(1.0, abs=1e-14)
    assert P.degree_of_polarisation(P.unpolarised()) == 0.0
    e = P.ellipse(P.unpolarised(2.0))
    assert e["degree"] == 0.0 and math.isnan(e["azimuth"]) and e["intensity"] == 2.0


def test_ellipse_against_the_field_trace():
    """Azimuth, semi-axes and handedness from the Stokes parameters against the field itself: |E(t)|^2 =
    (|J|^2 + Re(J.J e^{-2i omega t}))/2 has its maximum (|J|^2 + |J.J|)/2 at omega t = arg(J.J)/2, where E points along
    the major axis (J.J = J_p^2 + J_s^2, no conjugate), and its minimum (|J|^2 - |J.J|)/2; the area of the ellipse is
    pi |Im(J_p* J_s)|."""
    rng = np.random.default_rng(359)
    for _ in range(1000):
        J = rng.normal(size=2) + 1j * rng.normal(size=2)
        e = P.ellipse(J)
        n2, jj = float(np.vdot(J, J).real), complex(J[0] ** 2 + J[1] ** 2)
        assert e["major"] == pytest.approx(math.sqrt((n2 + abs(jj)) / 2), rel=1e-13)
        # minor axis: (|J|^2 - |J.J|)/2 cancels for nearly linear light; the ellipse's area pi a b = pi |Im(J_p* J_s)|
        # (the field's angular momentum) gives it without cancellation
        assert e["minor"] == pytest.approx(math.sqrt(max((n2 - abs(jj)) / 2, 0.0)), abs=1e-7 * math.sqrt(n2))
        assert e["minor"] == pytest.approx(abs(float(np.imag(np.conj(J[0]) * J[1]))) / e["major"], rel=1e-12)
        Emax = np.real(J * cmath.exp(-1j * cmath.phase(jj) / 2))
        az = math.atan2(Emax[1], Emax[0])
        d = (az - e["azimuth"]) % math.pi
        assert min(d, math.pi - d) < 1e-12
        turn = float(np.imag(np.conj(J[0]) * J[1]))  # (E x dE/dt)_z / omega
        assert e["handedness"] == (-1 if turn > 0 else 1)
        assert e["axis_ratio"] == pytest.approx(e["minor"] / e["major"], rel=1e-12, abs=1e-15)
    # a pure state rebuilt from its ellipse
    for _ in range(200):
        az, chi = rng.uniform(-math.pi / 2, math.pi / 2), rng.uniform(-math.pi / 4, math.pi / 4)
        e = P.ellipse(P.jones_ellipse(az, chi))
        d = (e["azimuth"] - az) % math.pi
        assert min(d, math.pi - d) < 1e-12 or abs(abs(chi) - math.pi / 4) < 1e-6
        assert e["chi"] == pytest.approx(chi, abs=1e-12)


# --- a planar structure -------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n1,n2", [(1.0, 1.33), (1.0, 1.515), (1.0, 1.62), (1.0, 1.75), (1.0, 2.4), (1.515, 1.0),
                                   (1.75, 1.33)])
def test_brewster_reflection_is_pure_s(n1, n2):
    """At theta_B = atan(n2/n1) the reflected light is pure s for any input: rho_R proportional to s s^dagger, its
    degree of polarisation 1 (1e-12) and its ellipse along s (Stratton §9.6: "the reflected wave is polarized entirely
    in the direction normal to the plane of incidence")."""
    bm = P.boundary_matrices([n1, n2], [], 633.0, interfaces.brewster(n1, n2))
    rng = np.random.default_rng(360)
    states = [P.unpolarised(), P.jones_linear(D(45)), P.jones_ellipse(0.3, 0.5)] + \
             [_random_rho(rng) for _ in range(200)]
    for rho in states:
        rho = P.density(rho)
        if rho[1, 1].real < 0.02:
            continue
        rR = P.through(rho, bm)["rho_R"]
        assert abs(rR[0, 0]) + abs(rR[0, 1]) < 1e-12 * abs(rR[1, 1])
        assert P.degree_of_polarisation(rR) == pytest.approx(1.0, abs=1e-12)
        assert abs(abs(P.ellipse(rR)["azimuth"]) - math.pi / 2) < 1e-12


@pytest.mark.parametrize("n1,n2", [(1.0, 1.515), (1.0, 1.62), (1.0, 1.75), (1.515, 1.0), (1.0, 3.5)])
def test_reflected_and_transmitted_degree_of_polarisation_of_unpolarised_light(n1, n2):
    """Unpolarised light: the reflected degree of polarisation is (R_s - R_p)/(R_s + R_p) and the transmitted one
    (T_s - T_p)/(T_s + T_p), in absolute value, at every angle (1e-12)."""
    for th in np.radians(np.linspace(0.0, 89.9, 300)):
        bm = P.boundary_matrices([n1, n2], [], 633.0, th)
        out = P.through(P.unpolarised(), bm)
        Rs, Rp = bm["R_s"], bm["R_p"]
        assert P.degree_of_polarisation(out["rho_R"]) == pytest.approx(abs(Rs - Rp) / (Rs + Rp), abs=1e-12)
        assert P.degree_from_powers(Rs, Rp) == pytest.approx(abs(Rs - Rp) / (Rs + Rp), abs=1e-15)
        if bm["T_s"] > 1e-3:
            Ts, Tp = bm["T_s"], bm["T_p"]
            assert P.degree_of_polarisation(out["rho_T"]) == pytest.approx(abs(Ts - Tp) / (Ts + Tp), abs=1e-12)


@pytest.mark.parametrize("ns,ds", STRUCTURES)
def test_energy_for_random_states(ns, ds):
    """P_R + P_T + P_A = tr rho, the five outcomes add to tr rho, an analyser's ports add to the arm's probability, and
    P_R, P_T are R_p rho_pp + R_s rho_ss, T_p rho_pp + T_s rho_ss of the transfer matrices (1e-14)."""
    rng = np.random.default_rng(361)
    for th in np.radians([0.0, 20.0, 41.0, 45.0, 56.6, 70.0, 89.0]):
        bm = P.boundary_matrices(ns, ds, 633.0, th)
        for _ in range(40):
            rho = _random_rho(rng)
            out = P.through(rho, bm)
            pp, ss = rho[0, 0].real, rho[1, 1].real
            assert abs(out["P_R"] - (bm["R_p"] * pp + bm["R_s"] * ss)) < 1e-14
            assert abs(out["P_T"] - (bm["T_p"] * pp + bm["T_s"] * ss)) < 1e-14
            assert abs(out["P_R"] + out["P_T"] + out["P_A"] - 1.0) < 1e-14
            aR = P.beam_splitter(rng.uniform(0, math.pi), *_random_k(rng))
            aT = P.beam_splitter(rng.uniform(0, math.pi), *_random_k(rng))
            pr = P.outcome_probabilities(rho, bm, aR, aT)
            assert abs(sum(pr[k] for k in P.OUTCOMES) - 1.0) < 1e-14
            assert abs(pr["R_pass"] + pr["R_reject"] - out["P_R"]) < 1e-14
            assert abs(pr["T_pass"] + pr["T_reject"] - out["P_T"]) < 1e-14
            plain = P.outcome_probabilities(rho, bm)
            assert plain["R_reject"] == 0.0 and plain["T_reject"] == 0.0
            assert abs(plain["R_pass"] - out["P_R"]) < 1e-16 and abs(plain["T_pass"] - out["P_T"]) < 1e-16
        if bm["lossless"]:
            assert bm["A_p"] == 0.0 and bm["A_s"] == 0.0


@pytest.mark.parametrize("ns,ds", STRUCTURES)
def test_transmission_matrix_carries_the_power_factors(ns, ds):
    """M_T = diag(eta_p t_p, eta_s t_s): |eta t|^2 is T of the transfer matrices, and with a lossless exit medium
    eta_p = eta_s (the transmitted state is the field's own)."""
    for th in np.radians([0.0, 30.0, 60.0, 85.0]):
        bm = P.boundary_matrices(ns, ds, 633.0, th)
        assert abs(abs(bm["M_T"][0, 0]) ** 2 - bm["T_p"]) < 1e-14
        assert abs(abs(bm["M_T"][1, 1]) ** 2 - bm["T_s"]) < 1e-14
        assert abs(abs(bm["M_R"][0, 0]) ** 2 - bm["R_p"]) < 1e-15
        if complex(ns[-1]).imag == 0 and bm["T_s"] > 0:
            assert bm["eta_p"] == pytest.approx(bm["eta_s"], rel=1e-15)


def test_normal_incidence_is_isotropic_in_each_beams_frame():
    """At normal incidence r_p = -r_s: linear light at psi comes back at -psi in the reflected beam's own frame (its p
    axis points the other way in the laboratory), passes at psi; a right-circular beam comes back left-circular; the
    probabilities do not depend on the state."""
    bm = P.boundary_matrices([1.0, 1.515], [], 633.0, 0.0)
    assert bm["r_p"] == pytest.approx(-bm["r_s"], abs=1e-16)
    for psi in np.radians([10.0, 30.0, 60.0, 80.0]):
        out = P.through(P.jones_linear(psi), bm)
        aR, aT = P.ellipse(out["rho_R"])["azimuth"], P.ellipse(out["rho_T"])["azimuth"]
        assert aR == pytest.approx(-psi, abs=1e-14) and aT == pytest.approx(psi, abs=1e-14)
    SR = P.stokes(P.through(P.jones_ellipse(0.0, D(45)), bm)["rho_R"])
    assert SR[3] == pytest.approx(-SR[0], rel=1e-14)
    ref = P.through(P.unpolarised(), bm)["P_R"]
    rng = np.random.default_rng(362)
    for _ in range(50):
        assert P.through(_random_rho(rng), bm)["P_R"] == pytest.approx(ref, rel=1e-14)


def test_no_structure_passes_the_state_unchanged():
    """The bench's structure «none» is a boundary between equal media: M_R = 0 and M_T = I exactly."""
    for n in (1.0, 1.515):
        bm = P.boundary_matrices([n, n], [], 633.0, D(30))
        assert np.array_equal(bm["M_R"], np.zeros((2, 2))) and np.allclose(bm["M_T"], np.eye(2), atol=1e-16)


def test_unpolarised_light_has_no_hidden_labels():
    """I/2 as a 50/50 mixture of s and p, of +-45 degrees or of right and left circular light: the same outcome
    probabilities to round-off (the decomposition is not a property of the photons)."""
    rng = np.random.default_rng(363)
    mixes = [0.5 * (P.density(P.jones_linear(0.0)) + P.density(P.jones_linear(D(90)))),
             0.5 * (P.density(P.jones_linear(D(45))) + P.density(P.jones_linear(D(-45)))),
             0.5 * (P.density(P.jones_ellipse(0.0, D(45))) + P.density(P.jones_ellipse(0.0, D(-45))))]
    for ns, ds in STRUCTURES[:6]:
        bm = P.boundary_matrices(ns, ds, 633.0, D(50))
        aR = P.beam_splitter(rng.uniform(0, math.pi), 0.9, 0.009)
        aT = P.beam_splitter(rng.uniform(0, math.pi))
        ref = P.outcome_probabilities(P.unpolarised(), bm, aR, aT)
        for m in mixes:
            pr = P.outcome_probabilities(m, bm, aR, aT)
            assert all(abs(pr[k] - ref[k]) < 1e-15 for k in P.OUTCOMES)


# --- total internal reflection ------------------------------------------------------------------------------------
TH_MAX = math.radians(89.9)  # the bench's largest angle (u35 TH_MAX)


def _tir_points(rng, n_points=1000, th_max=TH_MAX):
    """Random (n_in, n_out, theta) beyond the critical angle, theta <= th_max."""
    out = []
    while len(out) < n_points:
        n_in = rng.uniform(1.05, 4.0)
        n_out = rng.uniform(1.0, n_in * 0.98)
        thc = math.asin(n_out / n_in)
        th = rng.uniform(thc, th_max)
        if th > thc:
            out.append((n_in, n_out, th))
    return out


def test_tir_phase_difference_against_the_closed_form():
    """Beyond the critical angle |r_s| = |r_p| = 1 and delta = arg r_s - arg r_p of the transfer matrices equals
    Stratton's tan(delta/2) = cos theta sqrt(sin^2 theta - n^2)/sin^2 theta at 1 000 random (n, theta) (1e-12); linear
    light at 45 degrees comes back with S3 = -sin delta (left-handed), ellipticity angle -asin(sin delta)/2 (-delta/2
    while delta < 90 degrees, i.e. for n_in/n_out < 1 + sqrt 2)."""
    rng = np.random.default_rng(364)
    worst = 0.0
    for n_in, n_out, th in _tir_points(rng):
        bm = P.boundary_matrices([n_in, n_out], [], 633.0, th)
        assert abs(abs(bm["r_s"]) - 1) < 1e-15 and abs(abs(bm["r_p"]) - 1) < 1e-15
        d_engine = P.tir_phase_difference(n_in, n_out, th)
        d_closed = P.tir_phase_closed_form(n_out / n_in, th)
        worst = max(worst, abs(d_engine - d_closed))
        assert 0 < d_closed < math.pi
        rR = P.through(P.jones_linear(D(45)), bm)["rho_R"]
        S = P.stokes(rR)
        assert abs(S[1]) < 1e-15 and abs(S[2] - math.cos(d_engine)) < 1e-14 and abs(S[3] + math.sin(d_engine)) < 1e-14
        e = P.ellipse(rR)
        assert e["handedness"] == -1
        if d_engine < 1.4:  # away from circular light, where the ellipticity angle is ill-conditioned
            assert e["chi"] == pytest.approx(-d_engine / 2, abs=1e-12)
    assert worst < 1e-12, worst


def _fresnel_delta_mp(n_in, n_out, th):
    """arg r_s - arg r_p from Fresnel's coefficients (the engine's convention) in 30-digit arithmetic, for the binary64
    inputs."""
    a, b, t = mpmath.mpf(n_in), mpmath.mpf(n_out), mpmath.mpf(th)
    c = mpmath.cos(t)
    ct = mpmath.sqrt(mpmath.mpc(1 - (a / b) ** 2 * mpmath.sin(t) ** 2))
    if mpmath.im(b * ct) < 0:
        ct = -ct
    rs = (a * c - b * ct) / (a * c + b * ct)
    rp = (b * c - a * ct) / (b * c + a * ct)
    return mpmath.arg(rs * mpmath.conj(rp))


def test_tir_phase_difference_against_30_digit_fresnel_coefficients():
    """The engine's delta and the closed form against Fresnel's coefficients evaluated with 30 digits (mpmath) for the
    same binary64 (n, theta) up to 89.9 degrees (1e-12); the closed form itself evaluated with 30 digits agrees with
    them to 1e-25."""
    rng = np.random.default_rng(365)
    with mpmath.workdps(30):
        for n_in, n_out, th in _tir_points(rng, 300):
            ref = _fresnel_delta_mp(n_in, n_out, th)
            n, t = mpmath.mpf(n_out) / mpmath.mpf(n_in), mpmath.mpf(th)
            s2 = mpmath.sin(t) ** 2
            closed = 2 * mpmath.atan(mpmath.cos(t) * mpmath.sqrt(s2 - n * n) / s2)
            assert abs(closed - ref) < mpmath.mpf("1e-25")
            assert abs(P.tir_phase_difference(n_in, n_out, th) - float(ref)) < 1e-12
            assert abs(P.tir_phase_closed_form(n_out / n_in, th) - float(ref)) < 1e-12


def test_tir_phase_difference_near_grazing_incidence():
    """Within 1e-1 ... 1e-7 rad of grazing incidence the closed form (math.cos) and the engine's delta stay within
    1e-12 absolute and 1e-9 relative of the 30-digit Fresnel coefficients: ``interfaces._cosines`` takes cos theta0
    itself (review EX2, R2-E F10; with sqrt(1 - sin^2 theta0) the relative error grew as eps / cos^2 theta0, 2e-7 at
    0.0013 degrees from grazing)."""
    rng = np.random.default_rng(367)
    eps = np.finfo(float).eps
    with mpmath.workdps(30):
        for _ in range(300):
            n_in = rng.uniform(1.05, 4.0)
            n_out = rng.uniform(1.0, n_in * 0.98)
            th = math.pi / 2 - 10 ** rng.uniform(-7, -1)
            if th <= math.asin(n_out / n_in):
                continue
            ref = float(_fresnel_delta_mp(n_in, n_out, th))
            assert abs(P.tir_phase_closed_form(n_out / n_in, th) - ref) < 1e-12
            d = P.tir_phase_difference(n_in, n_out, th)
            assert abs(d - ref) <= min(1e-12, 1e-9 * ref + 16 * eps)


@pytest.mark.parametrize("n_glass", [1.33, 1.5, 1.515, 1.62, 1.75, 2.4])
def test_tir_phase_maximum(n_glass):
    """Stratton's maximum (sin^2 theta = 2n^2/(1 + n^2), tan(delta_max/2) = (1 - n^2)/(2n)) against a numerical
    maximisation of the engine's delta(theta)."""
    from scipy.optimize import minimize_scalar
    n = 1.0 / n_glass
    thm, dm = P.tir_phase_maximum(n)
    res = minimize_scalar(lambda t: -P.tir_phase_difference(n_glass, 1.0, t),
                          bounds=(math.asin(n) + 1e-9, math.pi / 2 - 1e-9), method="bounded",
                          options={"xatol": 1e-12})
    assert res.x == pytest.approx(thm, abs=1e-6) and -res.fun == pytest.approx(dm, abs=1e-12)
    assert P.tir_phase_difference(n_glass, 1.0, thm) == pytest.approx(dm, abs=1e-14)


# --- photons ------------------------------------------------------------------------------------------------------
def _tail(k: int, n: int, p: float) -> float:
    """Exact two-sided binomial tail min(1, 2 min(P(K <= k), P(K >= k)))."""
    return min(1.0, 2.0 * min(sps.binom.cdf(k, n, p), sps.binom.sf(k - 1, n, p)))


def _setups():
    bA = P.boundary_matrices([1.0, 1.515], [], 633.0, interfaces.brewster(1.0, 1.515))
    tir = P.boundary_matrices([1.515, 1.0], [], 633.0, P.tir_phase_maximum(1 / 1.515)[0])
    metal = P.boundary_matrices([1.0, 2.3, 0.5 + 2.0j, 1.45, 1.52], [60.0, 20.0, 95.0], 633.0, D(40))
    none = P.boundary_matrices([1.0, 1.0], [], 633.0, 0.0)
    return [
        ("unpolarised at Brewster, analyser along p", P.unpolarised(), bA, P.beam_splitter(0.0), None),
        ("unpolarised at Brewster, analyser along s", P.unpolarised(), bA, P.beam_splitter(D(90)), None),
        ("45 degrees, TIR at the largest delta, analyser at 135", P.jones_linear(D(45)), tir,
         P.beam_splitter(D(135)), None),
        ("unpolarised through a metal stack, both analysers", P.unpolarised(), metal,
         P.beam_splitter(D(30), 0.9, 0.009), P.beam_splitter(D(100))),
        ("Malus: psi 30, real analyser at 70", P.jones_linear(D(30)), none, None, P.beam_splitter(D(70), 0.9, 0.009)),
        ("elliptical, glass at 30, no analysers", P.jones_ellipse(0.4, 0.3),
         P.boundary_matrices([1.0, 1.5], [], 633.0, D(30)), None, None),
    ]


def test_photon_counts_follow_the_born_probabilities():
    """N photons per set-up drawn by ``sample_photons``: every outcome's count against its Born probability by the exact
    binomial tail, Bonferroni over all outcomes of all set-ups, failing below the two-sided 5 sigma tail; an outcome of
    probability 0 never occurs. The same counts against a wrong law (the two arms swapped) fail."""
    rng = np.random.default_rng(366)
    N = 200_000
    tails, wrong = [], []
    for name, state, bm, aR, aT in _setups():
        pr = P.outcome_probabilities(state, bm, aR, aT)
        k = np.bincount(P.sample_photons(pr, N, rng), minlength=len(P.OUTCOMES))
        for j, key in enumerate(P.OUTCOMES):
            p = pr[key]
            if p == 0.0:
                assert k[j] == 0, (name, key)
            elif p < 1.0:
                tails.append((_tail(int(k[j]), N, p), name, key))
        swapped = dict(pr, R_pass=pr["T_pass"], T_pass=pr["R_pass"])
        if abs(pr["R_pass"] - pr["T_pass"]) > 0.01:
            wrong.append(min(_tail(int(k[j]), N, swapped[key]) for j, key in enumerate(P.OUTCOMES)
                             if 0 < swapped[key] < 1))
    p_min, name, key = min(tails)
    assert len(tails) * p_min >= P_5SIGMA, (name, key, p_min)
    assert wrong and max(wrong) * len(tails) < P_5SIGMA


# --- the numbers the EX2 design builds on (§3.1, §3.4, §3.5, Appendix A.5) ------------------------------------------
def test_numbers_the_ex2_design_uses():
    """The bench's glasses A, B, C (n 1.515, 1.620, 1.750): Brewster's and the critical angles; the largest TIR phase
    difference of glass A, 46.3 degrees at 51.2 degrees; the unpolarised reflectance of glass A from 4.19 % at normal
    incidence rising monotonically through 7.72 % at Brewster's angle; at Brewster's angle the reflected light is pure
    s; Malus's law for the real analyser (k1 0.90, extinction 1e-2): k2 = 0.009 at 90 degrees and k1 - k2 = 0.891."""
    deg = math.degrees
    for n, thb, thc in ((1.515, 56.57, 41.30), (1.620, 58.31, 38.12), (1.750, 60.26, 34.85)):
        assert round(deg(interfaces.brewster(1.0, n)), 2) == thb
        assert round(deg(interfaces.critical(n, 1.0)), 2) == thc
    thm, dm = P.tir_phase_maximum(1 / 1.515)
    assert round(deg(thm), 1) == 51.2 and round(deg(dm), 1) == 46.3
    Ru = [P.through(P.unpolarised(), P.boundary_matrices([1.0, 1.515], [], 633.0, t))["P_R"]
          for t in np.radians(np.linspace(0.0, 89.9, 900))]
    assert np.all(np.diff(Ru) > 0) and round(100 * Ru[0], 2) == 4.19
    thb = interfaces.brewster(1.0, 1.515)
    assert round(100 * P.through(P.unpolarised(), P.boundary_matrices([1.0, 1.515], [], 633.0, thb))["P_R"], 2) == 7.72
    k1, k2 = 0.90, 0.90 * 1e-2
    assert P.malus(0.0, D(90), k1, k2) == pytest.approx(0.009, abs=1e-15)
    assert P.malus(0.0, 0.0, k1, k2) - P.malus(0.0, D(90), k1, k2) == pytest.approx(0.891, abs=1e-15)
