# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.quantum.qubits, real stations and real sources (EX2 §4.7): the POVMs of an analyser with one or two
threshold detectors against their limits and against an enumeration of the photon's port, its detection and the dark
clicks (an independent method); joint distributions of POVMs; Eberhard's states and Werner's mixtures."""

import itertools
import math

import numpy as np
import pytest

from lfphys.core.quantum import qubits as Q

rng = np.random.default_rng(1993)


def _random_state(rank=4):
    G = rng.normal(size=(4, rank)) + 1j * rng.normal(size=(4, rank))
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def test_ideal_detectors_give_the_projectors():
    P, Pc = Q.polarizer_projectors(0.4)
    Ep, E0 = Q.povm_one_detector(P, 1.0, 0.0)
    assert np.allclose(Ep, P, atol=1e-15) and np.allclose(E0, Pc, atol=1e-15)
    Ep, Em, E0, Eb = Q.povm_two_detectors((P, Pc), 1.0, 0.0)
    assert np.allclose(Ep, P, atol=1e-15) and np.allclose(Em, Pc, atol=1e-15)
    assert np.allclose(E0, 0, atol=1e-15) and np.allclose(Eb, 0, atol=1e-15)
    # a blind detector: never a click without dark counts; always one with p_d = 1
    assert np.allclose(Q.povm_one_detector(P, 0.0, 0.0)[0], 0, atol=1e-15)
    assert np.allclose(Q.povm_one_detector(P, 0.3, 1.0)[0], np.eye(2), atol=1e-15)


@pytest.mark.parametrize("trial", range(20))
def test_station_effects_form_a_povm(trial):
    th = rng.uniform(0, math.pi)
    eta, pd = rng.uniform(0, 1, 2), rng.uniform(0, 0.3, 2)
    P, Pc = Q.polarizer_projectors(th)
    assert Q.is_povm(Q.povm_one_detector(P, eta[0], pd[0]))
    assert Q.is_povm(Q.povm_two_detectors((P, Pc), eta, pd))
    assert Q.is_povm(Q.projectors(rng.normal(size=3)))
    assert not Q.is_povm([P, P])                                   # sums to 2P, not I
    assert not Q.is_povm([np.diag([1.2, 1.0]), np.diag([-0.2, 0.0])])  # not positive


def _enumerated_two_detectors(psi_pol, P_plus, eta, pd):
    """P(+ only), P(- only), P(none), P(both) for one photon in the pure state ``psi_pol``, by enumerating its port
    (Born), the detector's detection (Bernoulli eta) and each detector's dark click (Bernoulli p_d)."""
    p_port = [float(np.real(psi_pol.conj() @ P_plus @ psi_pol)), 0.0]
    p_port[1] = 1.0 - p_port[0]
    out = {"+": 0.0, "-": 0.0, "0": 0.0, "+-": 0.0}
    for port, det, dark_p, dark_m in itertools.product((0, 1), (0, 1), (0, 1), (0, 1)):
        w = p_port[port] * (eta[port] if det else 1 - eta[port])
        w *= (pd[0] if dark_p else 1 - pd[0]) * (pd[1] if dark_m else 1 - pd[1])
        click_p = (port == 0 and det) or dark_p
        click_m = (port == 1 and det) or dark_m
        key = {(1, 0): "+", (0, 1): "-", (0, 0): "0", (1, 1): "+-"}[(int(click_p), int(click_m))]
        out[key] += w
    return out


@pytest.mark.parametrize("trial", range(10))
def test_povms_against_an_enumeration_of_port_detection_and_dark_clicks(trial):
    psi = Q.ket(*(rng.normal(size=2) + 1j * rng.normal(size=2)))
    P, Pc = Q.polarizer_projectors(rng.uniform(0, math.pi))
    eta, pd = rng.uniform(0.2, 1, 2), rng.uniform(0, 0.2, 2)
    ref = _enumerated_two_detectors(psi, P, eta, pd)
    E = Q.povm_two_detectors((P, Pc), eta, pd)
    got = [float(np.real(psi.conj() @ e @ psi)) for e in E]
    assert got == pytest.approx([ref[k] for k in Q.TWO_DETECTOR_OUTCOMES], abs=1e-14)
    # one detector behind the transmitted port: a click with p_d + (1 - p_d) eta <Pi>
    Ep, E0 = Q.povm_one_detector(P, eta[0], pd[0])
    tp = float(np.real(psi.conj() @ P @ psi))
    assert float(np.real(psi.conj() @ Ep @ psi)) == pytest.approx(pd[0] + (1 - pd[0]) * eta[0] * tp, abs=1e-15)


@pytest.mark.parametrize("trial", range(10))
def test_joint_povm_distributions_sum_to_one_without_signalling(trial):
    rho = _random_state(rank=int(rng.integers(1, 5)))
    PA = Q.polarizer_projectors(rng.uniform(0, math.pi))
    PB = Q.polarizer_projectors(rng.uniform(0, math.pi))
    PB2 = Q.polarizer_projectors(rng.uniform(0, math.pi))
    EA = Q.povm_two_detectors(PA, rng.uniform(0.3, 1, 2), rng.uniform(0, 0.1, 2))
    EB = Q.povm_one_detector(PB[0], rng.uniform(0.3, 1), rng.uniform(0, 0.1))
    EB2 = Q.povm_two_detectors(PB2, rng.uniform(0.3, 1, 2), rng.uniform(0, 0.1, 2))
    J1 = Q.joint_probabilities(rho, EA, EB)
    J2 = Q.joint_probabilities(rho, EA, EB2)
    assert J1.shape == (4, 2) and J2.shape == (4, 4)
    assert J1.sum() == pytest.approx(1.0, abs=1e-14) and J2.sum() == pytest.approx(1.0, abs=1e-14)
    assert (J1 >= 0).all() and (J2 >= 0).all()
    assert J1.sum(axis=1) == pytest.approx(J2.sum(axis=1), abs=1e-14)  # A's marginal: B's choice does not show


def test_werner_state_scales_chsh_by_its_visibility():
    a, a2, b, b2 = 0.0, math.pi / 2, math.pi / 4, 3 * math.pi / 4
    vec = lambda x: [math.cos(x), 0, math.sin(x)]  # noqa: E731
    for V in (1.0, 0.85, 0.5, 0.0, -1 / 3):
        rho = Q.werner(Q.SINGLET, V)
        assert np.trace(rho).real == pytest.approx(1.0, abs=1e-15)
        assert np.linalg.eigvalsh(rho).min() >= -1e-15
        S = Q.chsh(lambda x, y: Q.spin_correlation(rho, vec(x), vec(y)), a, a2, b, b2)
        assert abs(S) == pytest.approx(abs(V) * 2 * math.sqrt(2), abs=1e-14)
    # photons: |Phi+> through polarisers at the CHSH angles 0, 45, 22.5, 67.5 degrees
    al, al2, be, be2 = (math.radians(x) for x in (0.0, 45.0, 22.5, 67.5))
    for V in (1.0, 0.85):
        rho = Q.werner(Q.PHI_PLUS, V)
        E = lambda x, y: Q.correlation(rho, Q.polarizer_observable(x), Q.polarizer_observable(y))  # noqa: E731
        assert Q.chsh(E, al, al2, be, be2) == pytest.approx(V * 2 * math.sqrt(2), abs=1e-14)
    with pytest.raises(ValueError):
        Q.werner(Q.SINGLET, 1.5)


def test_eberhard_states():
    """(|VH> + r|HV>)/sqrt(1 + r^2): r = -1 the singlet (up to a phase), r = 0 a product, concurrence 2|r|/(1 + r^2);
    r and 1/r are the same state with H and V exchanged at both stations (X (x) X)."""
    assert abs(np.vdot(Q.eberhard_state(-1.0), Q.SINGLET)) == pytest.approx(1.0, abs=1e-15)
    assert Q.concurrence(Q.dm(Q.eberhard_state(0.0))) == pytest.approx(0.0, abs=1e-12)
    XX = np.kron(Q.SX, Q.SX)
    for r in (-2.9, -0.3, 0.5, 4.0):
        psi = Q.eberhard_state(r)
        assert np.linalg.norm(psi) == pytest.approx(1.0, abs=1e-15)
        # the concurrence takes square roots of eigenvalues at round-off: 1e-7
        assert Q.concurrence(Q.dm(psi)) == pytest.approx(2 * abs(r) / (1 + r * r), abs=1e-7)
        assert abs(np.vdot(Q.eberhard_state(1 / r), XX @ psi)) == pytest.approx(1.0, abs=1e-15)
    # Giustina et al.'s state: amplitude 1 on |V>_A |H>_B
    psi = Q.eberhard_state(-2.9)
    assert psi[2].real == pytest.approx(1 / math.sqrt(1 + 2.9 ** 2))
    assert psi[1].real == pytest.approx(-2.9 * psi[2].real)
    with pytest.raises(ValueError):
        Q.eberhard_state(math.inf)


def test_station_parameters_are_checked():
    P = Q.polarizer_projectors(0.0)[0]
    for bad in (-0.1, 1.1):
        with pytest.raises(ValueError):
            Q.povm_one_detector(P, bad)
        with pytest.raises(ValueError):
            Q.povm_two_detectors(Q.polarizer_projectors(0.0), 0.5, bad)
