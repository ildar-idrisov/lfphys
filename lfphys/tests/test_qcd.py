# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""QCD of the core (colour algebra, running coupling) and the radial solver used by the quarkonium model."""

import math

import numpy as np
import pytest
from scipy import special

from lfphys.core.qcd import running, su3
from lfphys.core.quantum import radial

F, D = su3.structure_constants()


def test_gell_mann_algebra():
    L = su3.LAMBDA
    for a in range(8):
        for b in range(8):
            assert np.trace(L[a] @ L[b]).real == pytest.approx(2.0 * (a == b), abs=1e-14)
            comm = L[a] @ L[b] - L[b] @ L[a]
            assert np.allclose(comm, 2j * np.einsum("c,cij->ij", F[a, b], L), atol=1e-14)
    assert F[0, 1, 2] == pytest.approx(1.0) and F[3, 4, 7] == pytest.approx(math.sqrt(3) / 2)
    assert np.allclose(F, -np.transpose(F, (1, 0, 2)))  # antisymmetric


def test_casimirs_and_group_identities():
    CF = sum(su3.T[a] @ su3.T[a] for a in range(8))
    assert np.allclose(CF, su3.C_F * np.eye(3), atol=1e-14)
    assert np.allclose(np.einsum("acd,bcd->ab", F, F), su3.C_A * np.eye(8), atol=1e-13)
    assert np.allclose(np.einsum("acd,bcd->ab", D, D), (9 - 4) / 3 * np.eye(8), atol=1e-13)
    assert D[0, 0, 7] == pytest.approx(1 / math.sqrt(3)) and D[7, 7, 7] == pytest.approx(-1 / math.sqrt(3))
    # Jacobi identity
    J = (np.einsum("abe,ecd->abcd", F, F) + np.einsum("bce,ead->abcd", F, F) + np.einsum("cae,ebd->abcd", F, F))
    assert np.max(np.abs(J)) < 1e-13


def test_one_and_two_loop_running_against_closed_forms():
    a_ref, mu_ref = 0.118, 91.0
    for mu in (2.0, 10.0, 1000.0):
        num = running.alpha_s(mu, a_ref, mu_ref, {}, loops=1)  # no thresholds: n_f = 3
        assert num == pytest.approx(running.one_loop(mu, a_ref, mu_ref, 3), rel=1e-11)
    # two loops: L - L0 = 1/(b0 a) - 1/(b0 a0) + (b1/b0^2) ln[a (b0 + b1 a0) / (a0 (b0 + b1 a))]
    b0, b1 = running.beta_coefficients(5, 2)
    a0 = a_ref / (4 * math.pi)
    for mu in (5.0, 30.0, 500.0):
        a = running.alpha_s(mu, a_ref, mu_ref, {"c": 0.1, "b": 0.2}, loops=2) / (4 * math.pi)  # n_f = 5 throughout
        lhs = math.log(mu**2 / mu_ref**2)
        rhs = 1 / (b0 * a) - 1 / (b0 * a0) + b1 / b0**2 * math.log(a * (b0 + b1 * a0) / (a0 * (b0 + b1 * a)))
        assert lhs == pytest.approx(rhs, abs=1e-9)


def test_asymptotic_freedom_and_thresholds():
    th = {"c": 1.27, "b": 4.18, "t": 162.5}
    mus = np.geomspace(1.5, 1e4, 60)
    al = running.scan(mus, 0.118, 91.188, th)
    assert np.all(np.diff(al) < 0)  # falls at short distances
    for m in th.values():  # continuous across a threshold at 1 and 2 loops; at 3 and 4 the decoupling jump
        for loops in (1, 2, 3, 4):
            above = running.alpha_s(m * (1 + 1e-9), 0.118, 91.188, th, loops=loops)
            below = running.alpha_s(m * (1 - 1e-9), 0.118, 91.188, th, loops=loops)
            n_l = 3 + sum(1 for q in th.values() if q < m)
            if m < 91.188:  # crossed going down: alpha^(n_l) = down(alpha^(n_f))
                assert below == pytest.approx(running.decoupling(above, n_l, loops, down=True), rel=1e-8)
            else:  # crossed going up: alpha^(n_f) = up(alpha^(n_l)) (RunDec Eq. 23; inverse of Eq. 20 to O(a^4))
                assert above == pytest.approx(running.decoupling(below, n_l, loops, down=False), rel=1e-8)
            assert (below == pytest.approx(above, rel=1e-7)) == (loops <= 2)
    assert running.beta_coefficients(16, 1)[0] > 0 > running.beta_coefficients(17, 1)[0]
    # the series converges: 3 and 4 loops differ little at 2 GeV
    a3 = running.alpha_s(2.0, 0.118, 91.188, th, loops=3)
    a4 = running.alpha_s(2.0, 0.118, 91.188, th, loops=4)
    assert abs(a4 - a3) / a4 < 0.01


def test_radial_solver_coulomb_and_linear():
    """The accuracies stated in the radial module (review 2026-10-23, E5): -1/r, R = 100, n = 1..3."""
    mu, kappa = 1.0, 1.0
    V = lambda r: -kappa / r  # noqa: E731
    rel = lambda E, l: np.max(np.abs(E / (-mu * kappa**2 / (2 * (np.arange(1, 4) + l) ** 2)) - 1))  # noqa: E731
    assert rel(radial.levels(V, 0, mu, 100.0, N=800, n_states=3, richardson=0)[0], 0) < 3e-3
    assert rel(radial.levels(V, 0, mu, 100.0, N=800, n_states=3)[0], 0) < 2.5e-4  # dr^2 removed
    assert rel(radial.levels(V, 0, mu, 100.0, N=400, n_states=3, richardson=2)[0], 0) < 1.5e-5  # and dr^3
    assert rel(radial.levels(V, 1, mu, 100.0, N=800, n_states=3)[0], 1) < 1e-5
    # the closed-form kinetic matrix equals the sine-transform construction
    N, R = 37, 3.0
    n = np.arange(1, N + 1)
    S = math.sqrt(2.0 / (N + 1)) * np.sin(np.pi * np.outer(n, n) / (N + 1))
    T = S.T @ (((n * math.pi / R) ** 2 / 2)[:, None] * S)
    assert np.max(np.abs(radial._kinetic(N, R, 1.0, 1.0) - T)) < 1e-10 * np.max(np.abs(T))
    sigma = 1.0
    E, r, u = radial.levels(lambda r: sigma * r, 0, mu, 30.0, N=800, n_states=4)
    zeros = -special.ai_zeros(4)[0]
    assert np.allclose(E, (sigma**2 / (2 * mu)) ** (1 / 3) * zeros, rtol=1e-9)


def test_alpha_s_threshold_decoupling_against_an_independent_integration():
    """4-loop running from alpha_s(M_Z) = 0.1180 with 3-loop MS-bar decoupling at m_h(m_h) (RunDec Eq. 20),
    against the reviewer's independent mpmath integration (reviews/archive/2026-10-23_internal_lfphys-engine_physics,
    09_qcd.py; E7), and the round trip down and up is the identity."""
    from lfphys.core import data
    th = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
    ref = {4.183 * 0.999999: 0.224795, 2.0: 0.301507, 1.77686: 0.319595, 1.273 * 0.999999: 0.388356}
    for mu, a in ref.items():
        assert running.alpha_s(mu, 0.1180, data.M_Z[0], th) == pytest.approx(a, abs=1.5e-6)
    # down and back up: RunDec's upward relation (Eq. 23) is the inverse of Eq. 20 only to O(a^3), so the round
    # trip through m_c and m_b returns alpha_s(M_Z) to O(a^4) ~ 1e-5, not exactly
    a_c = running.alpha_s(1.273, 0.1180, data.M_Z[0], th)
    assert running.alpha_s(data.M_Z[0], a_c, 1.273, th) == pytest.approx(0.1180, rel=3e-5)
    # the jump at a threshold is the decoupling relation itself, of one loop less than the running
    for loops, size in ((1, 0.0), (2, 0.0), (3, 11 / 72), (4, None)):
        dn = running.decoupling(0.22, 4, loops, down=True)
        if size is not None:
            assert dn / 0.22 - 1 == pytest.approx(size * (0.22 / math.pi) ** 2, abs=1e-15)
        up = running.decoupling(dn, 4, loops, down=False)
        assert up == pytest.approx(0.22, rel=2e-4)  # the perturbative inverse: exact up to O(a^4)


def test_alpha_s_from_the_world_average_and_the_cornell_spectrum():
    from lfphys.core import data
    from lfphys.theories.models import cornell
    th = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
    a_mz = data.ALPHA_S_MZ[0]
    assert running.alpha_s(data.M_Z[0], a_mz, data.M_Z[0], th) == pytest.approx(a_mz, rel=1e-12)
    a_b = running.alpha_s(data.M_B_MB[0], a_mz, data.M_Z[0], th)
    assert 0.20 < a_b < 0.24  # alpha_s(m_b) ~ 0.22: asymptotic freedom from M_Z down to m_b
    # Cornell model vs spin-averaged quarkonium: the splittings (the model fixes no absolute scale) within 10 %
    for table, m_q, L1n in ((data.CHARMONIUM, cornell.PARAMS["m_c"], (0, 2)), (data.BOTTOMONIUM, cornell.PARAMS["m_b"], (0, 3))):
        sp = cornell.splittings(m_q, n_max=3, L_max=1)
        m1s = data.spin_averaged(table, 0, 1)[0]
        for (L, n) in ((0, 2), (1, 1), L1n):
            m = data.spin_averaged(table, L, n)[0]
            assert sp[(n, L)] * 1e3 == pytest.approx(m - m1s, rel=0.10)


def test_cornell_box_grows_for_large_states():
    """A light quark / weak string: the levels must not be box levels (review 2026-10-23, V6-5: 152-393 MeV errors in
    a fixed box of 25 GeV^-1). Against a 1.6 times larger box: within 1 MeV."""
    from lfphys.theories.models import cornell
    for mq, k, a in ((0.3, 0.52, 5.0), (1.0, 0.0, 5.0)):
        info = {}
        sp = cornell.splittings(mq, kappa=k, a=a, L_max=2, n_max=3, info=info)
        assert info["R"] > 25.0
        big = cornell.splittings(mq, kappa=k, a=a, L_max=2, n_max=3, R=1.6 * info["R"], N=1400)
        assert max(abs(sp[x] - big[x]) for x in sp) < 1e-3  # GeV


def test_landau_pole_reached_through_a_threshold_matching():
    """Review UX-params P5: alpha_s(M_Z) = 0.19 at 4 loops runs to 2.9 just above m_b; the 3-loop decoupling there takes it
    to 4.9, past ALPHA_MAX, so the next segment started beyond the pole event and DOP853 failed on the overflow ("RG
    integration failed", a raw refusal of v06). Now the pole is reported at m_b. Negative control: the world average and
    alpha_s(M_Z) = 0.185 (whose pole lies above m_b, found by the event) are unchanged in kind."""
    from lfphys.core import data
    th = {"c": data.M_C_MC[0], "b": data.M_B_MB[0], "t": data.M_T_MSBAR}
    for mu in (1.0, 1.5, data.M_C_MC[0]):
        with pytest.raises(running.LandauPole) as e:
            running.alpha_s(mu, 0.19, data.M_Z[0], th, 4)
        assert e.value.mu == pytest.approx(data.M_B_MB[0], rel=1e-12)
    # the coupling just above m_b is below the bound, and the matching is what crosses it
    a_above = running.alpha_s(data.M_B_MB[0] * (1 + 1e-12), 0.19, data.M_Z[0], th, 4)
    assert a_above < running.ALPHA_MAX < running.decoupling(a_above, 4, 4, down=True)
    with pytest.raises(running.LandauPole):
        running.alpha_s(data.M_B_MB[0], 0.19, data.M_Z[0], th, 4)  # the target at the threshold itself
    # a start already past the bound is a pole at the start, not an integration failure
    with pytest.raises(running.LandauPole) as e:
        running._evolve(4.0 / (4 * math.pi), math.log(4.0), math.log(1.0), 4, 4)
    assert e.value.mu == pytest.approx(2.0)
    # negative controls: nothing changes where the coupling stays perturbative or the pole is met by the event
    assert running.alpha_s(1.0, data.ALPHA_S_MZ[0], data.M_Z[0], th, 4) < running.ALPHA_MAX
    with pytest.raises(running.LandauPole) as e:
        running.alpha_s(1.0, 0.25, data.M_Z[0], th, 4)
    assert e.value.mu > data.M_B_MB[0]  # met by the event inside the n_f = 5 segment
    # the scan of the review (alpha_s(M_Z) 0.11 ... 0.30, 1-4 loops, +- the PDG error): only poles, no failures
    for loops in (1, 2, 3, 4):
        for a in np.arange(0.11, 0.3001, 0.005):
            for aa in (a - data.ALPHA_S_MZ[1], a, a + data.ALPHA_S_MZ[1]):
                for mu in (1.0, 1.3, 2.0, 4.0, 10.0):
                    try:
                        val = running.alpha_s(mu, aa, data.M_Z[0], th, loops)
                    except running.LandauPole:
                        continue
                    assert 0 < val < running.ALPHA_MAX
