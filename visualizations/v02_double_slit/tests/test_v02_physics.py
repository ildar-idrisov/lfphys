# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v02 physics: wave kinematics, the diffraction engine, marks and the whole stream of particles."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.quantum import marks, scattering  # noqa: E402
from lfphys.core.quantum.particles import EV, C, H, make  # noqa: E402
from lfphys.i18n import render  # noqa: E402
from lfphys.theories.approx import kirchhoff, paraxial  # noqa: E402
from lfphys.tools import stats  # noqa: E402

V = "v02_double_slit"


def _en(x):
    """The English rendering of a text of the world (a translatable text, live or from the record, or a plain one)."""
    return render(x)


def _txt(exc):
    """A refusal's text and hint in English (a refusal keeps them translatable; any other exception: its own text)."""
    text = getattr(exc, "text", None)
    if text is None:
        return str(exc)
    hint = getattr(exc, "hint", None)
    return _en(text) + (" | " + _en(hint) if hint else "")


# --- particles ------------------------------------------------------------------------------------------
def test_electron_50kev_wavelength():
    p = make("electron", "ekin", 50e3)
    mc2 = 510998.95 * EV
    ek = 50e3 * EV
    assert p.lam == pytest.approx(H * C / math.sqrt(ek**2 + 2 * ek * mc2), rel=1e-6)
    assert p.lam == pytest.approx(5.355e-12, rel=2e-4)


def test_slow_neutron_kinetic_energy_has_no_cancellation():
    p = make("neutron", "lambda", 2e-9)
    # non-relativistic E_k = h^2 / (2 m lambda^2) to 1e-12 for such a slow neutron
    assert p.Ekin == pytest.approx(H**2 / (2 * p.mass * p.lam**2), rel=1e-9)


def test_photon_relations():
    p = make("photon", "lambda", 500e-9)
    assert p.E == pytest.approx(H * C / 500e-9, rel=1e-15)
    assert p.v == C and p.nu == pytest.approx(C / 500e-9, rel=1e-15)


# --- diffraction engine ---------------------------------------------------------------------------------
def test_fresnel_reaches_fraunhofer_in_far_field():
    lam, a, d, L = 500e-9, 5e-6, 25e-6, 10.0  # d^2/(lam L) = 1.25e-4
    k = 2 * math.pi / lam
    x = np.linspace(-0.5, 0.5, 2001)
    P = paraxial.intensity(paraxial.slit_amplitudes(x, L, k, [-d / 2, d / 2], a), np.ones((2, 2)))
    P /= P.max()
    s = x / L  # paraxial far field: the Fresnel kernel's limit (the exact angle is tested against RS separately)
    ref = np.sinc(a * s / lam) ** 2 * np.cos(math.pi * d * s / lam) ** 2
    assert np.max(np.abs(P - ref)) < 1e-3


def test_paraxial_matches_rayleigh_sommerfeld():
    lam, a, d, L = 632.8e-9, 20e-6, 100e-6, 1.0
    k = 2 * math.pi / lam
    x = np.linspace(-0.02, 0.02, 301)
    A = paraxial.slit_amplitudes(x, L, k, [-d / 2, d / 2], a)
    dev, _ = kirchhoff.paraxial_deviation(x, L, k, [-d / 2, d / 2], a, math.inf, np.ones((2, 2), complex), A)
    assert dev < 1e-3


def test_rs_exact_for_wide_slit_in_near_field():
    """Inside the geometric projection of a wide slit, close behind it (Fresnel number 1e5), the exact field is the
    incident wave up to small edge ripples. With the former cap of 2000 panels this needed 260 rad per 32-node panel
    and the reference integral was wrong (response check to the v02 review)."""
    lam, a, z = 5e-12, 1e-6, 2e-6
    k = 2 * math.pi / lam
    x = np.linspace(-0.4e-6, 0.4e-6, 9)
    U = kirchhoff.slit_fields(x, z, k, [0.0], a)[0]
    assert np.max(np.abs(np.abs(U) - 1.0)) < 0.03
    # phase: the incident plane wave exp(ikz) (common constants included in slit_fields)
    assert np.max(np.abs(np.angle(U * np.exp(-1j * k * z)))) < 0.03


def test_rs_fields_cached_across_segments():
    """A new segment with the same geometry recombines the run's cached exact fields (no new RS integrals)."""
    h = Harness(V, "electron")
    calls = []
    orig = kirchhoff.slit_fields
    kirchhoff.slit_fields = lambda *a, **kw: calls.append(1) or orig(*a, **kw)
    try:
        z0 = h.of("segment")[0]["z_paraxial"]
        h.action("clear")
        z1 = h.of("segment")[-1]["z_paraxial"]
    finally:
        kirchhoff.slit_fields = orig
    assert not calls and z1 == z0


def test_rs_budget_marks_unaffordable_columns_unverified():
    """k a = 3e7 (1 u at 1e5 m/s through 20 um slits): the exact near-field integral would need ~1e6 panels per slit;
    the run marks those columns as not verified (instead of computing for minutes or trusting a capped rule)."""
    import time
    t0 = time.time()
    h = Harness(V, None, {"species": "custom", "mass_u": 1.0, "energy_by": "speed", "speed_ms": 1e5})
    assert time.time() - t0 < 60
    seg = h.of("segment")[0]
    assert seg["z_paraxial_why"] == "cost" and seg["z_paraxial"] > 2 * h.sim.geom.a
    assert any("not verified" in _en(a) for a in seg["approx"])


def test_derivative_closed_form():
    k = 2 * math.pi / 500e-9
    x = np.linspace(-1e-3, 1e-3, 7)
    A, dA = paraxial.slit_amplitudes(x, 0.3, k, [-50e-6, 50e-6], 20e-6, L1=0.5, src=1e-5, kappa=3e4, deriv=True)
    h = 1e-9
    fd = (paraxial.slit_amplitudes(x + h, 0.3, k, [-50e-6, 50e-6], 20e-6, L1=0.5, src=1e-5, kappa=3e4)
          - paraxial.slit_amplitudes(x - h, 0.3, k, [-50e-6, 50e-6], 20e-6, L1=0.5, src=1e-5, kappa=3e4)) / (2 * h)
    assert np.max(np.abs(fd - dA)) / np.max(np.abs(dA)) < 1e-7


def test_parseval_flux_on_wide_screen():
    """Total flux through a wide screen = lambda z a per slit (the normalisation used for 'missed the screen')."""
    lam, a, L = 1e-6, 20e-6, 0.5
    k = 2 * math.pi / lam
    x = np.linspace(-0.5, 0.5, 400001)
    A = paraxial.slit_amplitudes(x, L, k, [0.0], a)
    flux = float(np.sum(np.abs(A[0]) ** 2) * (x[1] - x[0]))
    assert flux == pytest.approx(lam * L * a, rel=2e-3)


# --- marks ----------------------------------------------------------------------------------------------
def test_orthogonal_polarizers_remove_cross_term_and_eraser_restores_it():
    chi = np.array([1, 1], complex) / math.sqrt(2)
    J = [marks.element_matrix("polarizer", 0, "pol"), marks.element_matrix("polarizer", 90, "pol")]
    I = np.eye(2, dtype=complex)
    m = marks.marks(chi, J, I, [np.ones(1)] * 2)
    G = marks.gram_by_readout(m, 2, None)[0]
    assert abs(G[0, 1]) < 1e-15
    Pa = marks.analyzer_matrix("on", 45, "pol")
    m2 = marks.marks(chi, J, Pa, [np.ones(1)] * 2)
    G2 = marks.gram_by_readout(m2, 2, None)[0]
    assert abs(G2[0, 1]) / math.sqrt(G2[0, 0].real * G2[1, 1].real) == pytest.approx(1.0, rel=1e-12)


def test_half_wave_plate_rotates_polarization():
    J = marks.element_matrix("hwp", 22.5, "pol")
    out = J @ np.array([1, 0], complex)
    assert abs(abs(out[0]) - abs(out[1])) < 1e-12  # H -> D (up to phase)


def test_spin_flip_marks_path():
    chi = np.array([1, 0], complex)
    J = [marks.element_matrix("rot_y", 180, "spin"), np.eye(2, dtype=complex)]
    m = marks.marks(chi, J, np.eye(2, dtype=complex), [np.ones(1)] * 2)
    assert abs(np.vdot(m[1], m[0])) < 1e-15


@pytest.mark.parametrize("theta", [0, 20, 45, 70, 90])
def test_englert_duality_pure_marks(theta):
    dets = marks.detector_states(2, 0, theta, True)
    m = marks.marks(np.ones(1, complex), [np.eye(1)] * 2, np.eye(1), dets)
    Vv, D = marks.englert(m[0], m[1])
    assert Vv * Vv + D * D == pytest.approx(1.0, abs=1e-12)
    assert Vv == pytest.approx(abs(math.cos(math.radians(theta))), abs=1e-12)


def test_readout_sum_equals_unread():
    dets = marks.detector_states(2, 0, 60, True)
    m = marks.marks(np.ones(1, complex), [np.eye(1)] * 2, np.eye(1), dets)
    Gs = marks.gram_by_readout(m, 1, marks.readout_basis(33.0))
    G = marks.gram_by_readout(m, 1, None)[0]
    assert np.allclose(Gs[0] + Gs[1], G, atol=1e-15)


@pytest.mark.parametrize("u", [0.3, 1.0, math.pi, 5.0, 12.0])
def test_dipole_coherence_closed_forms(u):
    perp = 1.5 * (math.sin(u) / u + math.cos(u) / u**2 - math.sin(u) / u**3)
    par = 3.0 * (math.sin(u) / u**3 - math.cos(u) / u**2)
    # probe along y (no x component): only the scattered direction matters
    g_perp = scattering.dipole_coherence(u, [0, 1, 0], [0, 0, 1])
    g_par = scattering.dipole_coherence(u, [0, 1, 0], [1, 0, 0])
    assert g_perp.real == pytest.approx(perp, abs=1e-10) and abs(g_perp.imag) < 1e-10
    assert g_par.real == pytest.approx(par, abs=1e-10)


# --- whole runs -------------------------------------------------------------------------------------------
def _bad_checks(h):
    bad = []
    for c in h.checks().values():
        if c.get("ok") is False:
            bad.append(c)
        elif c.get("ok") is None and c.get("ref") is not None and c.get("rel") is not None \
                and abs(c["rel"]) > max(c.get("tol") or 1e-9, 1e-9):
            bad.append(c)
    return [(c["label"], c["value"], c["ref"]) for c in bad]


GOOD = ["photon_young", "photon_pol_marks", "photon_eraser", "photon_eraser_minus", "photon_partial",
        "photon_qubit", "electron", "electron_qubit", "electron_weak", "electron_eraser", "electron_microscope",
        "electron_ab", "neutron", "c60", "c60_grw", "triple", "slit_collapse"]


@pytest.mark.parametrize("preset", GOOD)
def test_presets_checks_agree(preset):
    h = Harness(V, preset)
    rate = h.of("header")[0]["rate"]
    h.run_to(400 / rate)
    assert not h.errors()
    assert _bad_checks(h) == []


def test_born_modification_is_flagged_and_breaks_sorkin():
    h = Harness(V, "triple_mod")
    hd = h.of("header")[0]
    assert [m["id"] for m in hd["modifications"]] == ["born_p"]
    s = [c for c in h.checks().values() if "Sorkin" in _en(c["label"])][0]
    assert s["ok"] is False and s["value"] > 0.05


def test_histogram_agrees_with_expectation_and_coherence():
    h = Harness(V, "electron_weak", seed=3)
    rate = h.of("header")[0]["rate"]
    h.run_to(20000 / rate)
    fr, _ = h.sim.frame()
    assert fr["chi2"]["p"] > 1e-4
    coh = fr["coh"]
    assert abs(coh["hist"] - coh["expected"]) < 4 * coh["err"]
    assert coh["expected"] == pytest.approx(math.cos(math.radians(30)), abs=1e-6)


def test_eraser_sorting_restores_fringes():
    h = Harness(V, "electron_eraser", seed=5)
    rate = h.of("header")[0]["rate"]
    h.run_to(20000 / rate)
    sim = h.sim
    bins = sim.hist["bins"]  # (readout, bins)
    g0, e0 = sim._coherence(bins[0].astype(float), weights=1 / np.maximum(bins[0], 1), bins=True)
    g1, e1 = sim._coherence(bins[1].astype(float), weights=1 / np.maximum(bins[1], 1), bins=True)
    gall, eall = sim._coherence(bins.sum(axis=0).astype(float), weights=1 / np.maximum(bins.sum(axis=0), 1), bins=True)
    assert g0 > 0.8 and g1 > 0.8  # fringes and anti-fringes in the sorted subsets
    assert gall < 0.15  # none in the sum


def test_absorption_fractions():
    h = Harness(V, "photon_eraser", seed=2)
    h.run_to(20000 / 1000.0)
    c = h.sim.counts
    # polarizers H/V at the slits take half of D; the 45-degree analyzer takes half of the rest, at the screen
    assert c["absorbed_slits"] / c["emitted"] == pytest.approx(0.5, abs=0.015)
    assert (c["absorbed_slits"] + c["absorbed_an"]) / c["emitted"] == pytest.approx(0.75, abs=0.015)


def test_apparatus_change_starts_new_segment_and_updates_actions():
    h = Harness(V, "electron")
    h.run_to(0.2)
    h.action("apparatus", wp_mode="qubit", wp_theta=90.0)
    h.run_to(0.4)
    segs = h.of("segment")
    assert len(segs) == 2 and "which-path detector" in _en(segs[1]["apparatus"])
    assert h.of("actions")
    coh = [c for c in h.checks().values() if c["id"] == "coh1"][0]
    assert coh["value"] < 1e-9


def test_invalid_combinations_rejected():  # texts: test_refusals_name_the_choice_and_what_to_take
    with pytest.raises(ValueError):
        Harness(V, None, {"species": "photon", "wp_mode": "microscope"})
    with pytest.raises(ValueError):
        Harness(V, None, {"species": "c60", "energy_by": "speed", "speed_ms": 200.0, "analyzer": "on"})


# --- regressions from the physics review 2026-10-22 (reviews/archive/2026-10-22_internal_viz-v02_physics) ---------
from lfphys.theories.approx import paraxial_ensemble as ens  # noqa: E402
from lfphys.core.quantum.particles import E_CHARGE, U  # noqa: E402


def test_R1_grw_coherence_exact_kick_model():
    h = Harness(V, "c60_grw")
    c = [c for c in h.checks().values() if c["id"] == "coh0"][0]
    sim = h.sim
    g = sim.geom
    Lam = sim.exp.grw_rate() * g.L2 / sim.particle.v
    rc = sim.laws.grw_rc
    ref = math.exp(-Lam * (1 - math.sqrt(math.pi) * rc / g.d * math.erf(g.d / (2 * rc))))
    assert c["ref"] == pytest.approx(ref, rel=1e-12)
    assert abs(c["value"] - ref) < 0.01


def test_R2_coherence_estimator_unbiased_on_samples():
    h = Harness(V, "electron_weak")
    sim = h.sim
    P = sim.theory["curves"]["all"]
    rng = np.random.default_rng(0)
    vals = []
    for _ in range(60):
        cnt = rng.multinomial(2000, P / P.sum()).astype(float)
        gam, err = sim._coherence(cnt, bins=True)
        assert gam is not None and err is not None
        vals.append(gam)
    assert abs(np.mean(vals) - math.cos(math.radians(30))) < 0.02


def test_coherence_error_is_calibrated_at_full_coherence():
    """|gamma| = 1 at N = 100: the Fisher error was 14x smaller than the real scatter (zero expected minima); the shown
    error is the parametric bootstrap, within 30 % of the scatter (response to the v02 review)."""
    h = Harness(V, "photon_young")
    sim = h.sim
    P = sim.theory["curves"]["all"]
    basis = sim._coh_basis(True)
    rng = np.random.default_rng(1)
    vals, errs = [], []
    for _ in range(40):
        cnt = rng.multinomial(100, P / P.sum()).astype(float)
        g, _ = stats.coherence_ml(cnt, *basis)
        e, _ = stats.coherence_boot_err(cnt, *basis, rng=rng)
        if g is not None and e is not None:
            vals.append(g)
            errs.append(e)
    ratio = np.median(errs) / np.std(vals, ddof=1)
    assert len(vals) >= 35 and 0.7 < ratio < 1.3


def test_R3_map_shows_the_decoherence():
    h = Harness(V, "electron_microscope")
    seg = h.of("segment")[0]
    blobs = [b for m, b in h.msgs if m.get("type") == "segment"][0]
    nz = len(blobs["map_z"])
    I = blobs["map"].reshape(nz, -1)
    xi = np.linspace(-1, 1, I.shape[1]) * blobs["map_w"][-1]
    m = np.abs(xi) < 10e-6  # about two fringes around the centre (envelope nearly flat there)
    last = I[-1][m]
    contrast = (last.max() - last.min()) / (last.max() + last.min())
    assert contrast < 0.4  # the coherent wave has contrast ~1 here; one scattered photon leaves |gamma| ~ 0.15


def test_R4_analyzer_inserted_in_flight_acts_on_flying_particles():
    h = Harness(V, None, {"species": "neutron", "lam_nm": 2.0, "a_um": 5.0, "d_um": 25.0, "L2_m": 5.0,
                          "rate": 20000.0, "spin_state": "up_z"})
    tf = h.sim.t_flight
    h.run_to(3 * tf)
    n0 = h.sim.counts["detected"]
    h.action("apparatus", analyzer="on", analyzer_angle=90.0)  # spin filter along x: passes half of up_z
    h.run_to(4 * tf)  # exactly the particles that were in flight at the change
    n1 = h.sim.counts["detected"] - n0
    expected_full = 20000.0 * tf
    assert n1 < 0.65 * expected_full  # about half are absorbed although they passed the slits before the change


def test_R5_slow_neutron_by_kinetic_energy():
    p = make("neutron", "ekin", 0.2045e-3)
    from mpmath import mp, mpf, sqrt as msqrt
    mp.dps = 50
    ek = mpf(0.2045e-3) * mpf(EV)
    mc2 = mpf(p.mass) * mpf(C) ** 2
    lam = mpf(H) * mpf(C) / msqrt(ek * ek + 2 * ek * mc2)
    assert p.lam == pytest.approx(float(lam), rel=1e-13)


@pytest.mark.parametrize("q,flux,expect", [(2.0, 0.25, math.pi), (-3.0, 1 / 6, -math.pi), (0.5, 1.0, math.pi)])
def test_R6_ab_phase_scales_with_charge(q, flux, expect):
    h = Harness(V, None, {"species": "custom", "mass_u": 1.0, "charge_e": q, "energy_by": "speed", "speed_ms": 1e5,
                          "ab_flux": flux})
    ph = h.sim.exp.ab_phases(h.sim.app)
    assert ph[1] == pytest.approx(expect, abs=1e-12)


def test_R7_signalling_under_modified_born_rule_is_reported():
    h = Harness(V, "electron_eraser", params={"born_p": 2.4})
    c = [c for c in h.checks().values() if c["id"].startswith("nosig")][0]
    assert c["ok"] is False and c["value"] > 1e-3


def test_R8_dark_counts_in_the_expectation():
    h = Harness(V, None, {"dark_rate": 50.0}, seed=4)
    h.run_to(30.0)
    fr, _ = h.sim.frame()
    assert fr["chi2"]["p"] > 1e-4


def test_R10_R9_server_curves_per_class():
    h = Harness(V, "electron_microscope", params={"mic_prob": 0.5})
    seg = h.of("segment")[0]
    assert "noscat" in seg["curves"] and "all" in seg["curves"]


def test_R11_R24_probe_rules():
    with pytest.raises(ValueError):
        Harness(V, "electron_microscope", params={"mic_dir": "z", "mic_pol": "z"})
    with pytest.raises(ValueError):
        Harness(V, None, {"species": "neutron", "lam_nm": 2.0, "wp_mode": "microscope"})


def test_R13_R15_reported():
    h = Harness(V, "photon_young")
    seg = h.of("segment")[0]
    assert seg["z_paraxial"] > 0 and seg["approx"]
    assert h.checks()["grid"]["ok"] is True


def test_map_shows_the_wave_before_the_analyzer():
    """Eraser: orthogonal polarizers at the slits, analyzer at 45 deg in front of the screen. Between the slits and the
    analyzer the marks are orthogonal, so the map has no fringes; the screen (after the analyzer) has full fringes
    (found in the processing of the v02 review: the map used the marks after the analyzer)."""
    h = Harness(V, "photon_eraser")
    sim = h.sim
    b = [b for m, b in h.msgs if m.get("type") == "segment"][0]
    I = b["map"].reshape(len(b["map_z"]), -1)
    xi = np.linspace(-1, 1, I.shape[1]) * b["map_w"][-1]
    win = sim.particle.lam * sim.geom.L2 / sim.geom.d
    last = I[-1][np.abs(xi) < win]
    e = sim.edges
    xc = 0.5 * (e[1:] + e[:-1])
    cv = sim.theory["curves"]["all"][np.abs(xc) < win]
    con = lambda v: (v.max() - v.min()) / (v.max() + v.min())  # noqa: E731
    assert con(last) < 0.1 and con(cv) > 0.8
    assert any("before the analyser" in _en(a) for a in h.of("segment")[0]["approx"])


def test_R19_right_circular_has_s3_plus_one():
    from v02_double_slit.engine.experiment import state_label
    lab = state_label(np.array(marks.POL_STATES["R"], complex), "pol")
    assert lab.msgid.startswith("Stokes") and lab.args["s3"] == pytest.approx(1.0) and _en(lab).endswith("+1.00)")
    chi = marks.sample_internal(np.random.default_rng(0), "pol", "custom", 1.0, (0.0, 45.0))
    assert np.allclose(chi, np.array(marks.POL_STATES["R"], complex))


def test_R21_per_particle_flight_time():
    h = Harness(V, "neutron", params={"dlam_rel": 0.1, "rate": 20000.0})
    h.run_to(0.01)
    b = h.sim.batches[0] if h.sim.batches else None
    assert b is not None and np.std(b.t_det - b.t_e) > 0


def test_R22_grw_acts_on_electrons():
    h = Harness(V, "electron", params={"collapse": "grw", "grw_lambda": 1e3})
    assert h.sim.exp.grw_rate() == pytest.approx(1e3 * h.sim.particle.mass / U, rel=1e-12)


def test_ensemble_matches_monte_carlo_with_shifts():
    """The exact ensemble (characteristic functions) against a direct Monte-Carlo over kicks and source points."""
    lam = 632.8e-9
    k = 2 * math.pi / lam
    slits, a, L1, L2, s = [-50e-6, 50e-6], 20e-6, 0.5, 1.0, 1e-3
    model = ens.Model(k, 0.0, slits, a, L1, s, 0.0, 0.0, 0.0, 0.0, 0.0, lambda kk: C, 1e-7)
    x = np.linspace(-0.03, 0.03, 3001)
    G = np.ones((2, 2), complex)
    Pe = ens.screen(model, x, L2, [G])[0]
    rng = np.random.default_rng(3)
    xs = (rng.random(20000) - 0.5) * s
    acc = np.zeros_like(x)
    for i in range(0, len(xs), 1000):
        A = paraxial.slit_amplitudes(x[None, :], L2, k, slits, a, L1, xs[i:i + 1000, None])
        acc += np.einsum("bjx,blx,jl->x", A, A.conj(), G).real
    acc /= len(xs) * lam * L2 * a * 2
    assert np.max(np.abs(Pe - acc)) / Pe.max() < 0.02


# --- live set-up (owner, 2026-10-23: changes apply at once; only the laws are fixed for a world) ---------------
def test_live_screen_and_slits_change_rebuilds_the_setup():
    h = Harness(V, "neutron")  # slow particles: some are in flight when the set-up changes
    h.run_to(0.2)
    flying = sum(int((b.stage < 2).sum()) for b in h.sim.batches)
    assert flying > 0
    h.set(L2_m=2.0, a_um=4.0)
    assert not h.errors()
    seg = h.of("segment")[-1]
    assert seg["setup"]["geometry"]["L2"] == 2.0 and abs(seg["setup"]["geometry"]["a"] - 4e-6) < 1e-15
    assert h.sim.counts["lost"] == flying and h.of("live")[-1]["values"]["L2_m"] == 2.0
    h.run_to(1.5)
    assert h.sim.counts["detected"] > 0
    assert not [c["id"] for c in h.checks().values() if c.get("ok") is False]
    assert h.checks()["lam"]["value"] is not None  # the set-up's own checks are emitted again


def test_live_particle_change_removes_incompatible_elements():
    h = Harness(V, "photon_pol_marks")
    h.set(species="electron", energy_by="ekin", ekin_ev=5e4, a_um=0.1, d_um=0.5)
    assert not h.errors()
    v = h.of("live")[-1]["values"]
    assert v["species"] == "electron" and v["el1"] == "none" and v["el2"] == "none"
    assert any("removed" in _en(m["text"]) for m in h.of("notice"))
    # an explicit impossible request is refused and nothing changes
    h.set(el1="polarizer")
    assert h.errors() and h.of("live")[-1]["values"]["el1"] == "none" and h.sim.particle.species == "electron"


def test_laws_are_not_live():
    h = Harness(V, "photon_young")
    h.set(born_p=2.4)
    # refused by the framework's schema (a law is a world parameter), naming the parameter by its label
    assert "Born rule" in _en(h.errors()[-1]) and h.sim.laws.born_p == 2.0


def test_source_change_lets_emitted_particles_fly_on_as_transitional():
    h = Harness(V, "neutron", params={"spin_state": "up_z", "rate": 2000.0})
    h.run_to(0.1)
    h.set(spin_state="down_z")
    assert h.sim.counts["lost"] == 0
    h.run_to(0.2)
    assert h.sim.counts["mixed"] > 0


def test_new_world_replaces_the_simulation_in_the_same_runner():
    h = Harness(V, "photon_young")
    h.runner.handle({"cmd": "new_world", "args": {"preset": "triple_mod"}})
    heads = h.of("header")
    assert [m["world"] for m in heads] == [1, 2] and h.sim.laws.born_p == 2.4 and heads[1]["modifications"]


# --- the record's world is the same however fast the wall clock ran (review C1-6) ----------------------------------
def _same_exactly(a, b, path=""):
    if isinstance(a, dict):
        assert set(a) == set(b), (path, set(a) ^ set(b))
        for k in a:
            if k not in ("cpu_ms", "speed_actual", "lag"):  # the runner's measurements of the wall clock
                _same_exactly(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _same_exactly(x, y, f"{path}[{i}]")
    elif isinstance(a, np.ndarray):
        assert a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b, equal_nan=a.dtype.kind in "fc"), path
    elif isinstance(a, float):
        assert a == b or (math.isnan(a) and math.isnan(b)), (path, a, b)
    else:
        assert a == b, (path, a, b)


def _messages_under_clock(monkeypatch, wall_step, frames=80):
    """Every message of a world driven through the same frames, with ``wall_step`` seconds of wall time passing at
    every read of the clock (0: a frozen clock, as a world rebuilt from its record in a burst sees it)."""
    import time
    clock = [1e4]

    def now():
        clock[0] += wall_step
        return clock[0]
    with monkeypatch.context() as mp:
        for name in ("monotonic", "time", "perf_counter"):
            mp.setattr(time, name, now)
        h = Harness(V, "photon_young")
        step = h.sim.default_speed / 20
        for k in range(1, frames + 1):
            h.run_to(k * step)
            h.runner._frame(0.0)
    assert h.sim._coh_err_cache is not None and h.of("frame")[-1]["n_seg"] > 100  # the bootstrap error was computed
    return h.msgs


def test_the_coherence_error_does_not_depend_on_the_wall_clock(monkeypatch):
    """C1-6: the bootstrap error of |gamma_12| was recomputed at most once per wall second, so a world continued from
    its record (its frames replayed in a burst) showed other errors than the run had; now its clock is the frames."""
    a = _messages_under_clock(monkeypatch, 0.0)
    b = _messages_under_clock(monkeypatch, 0.5)
    assert [m["type"] for m, _ in a] == [m["type"] for m, _ in b]
    for (ma, ba), (mb, bb) in zip(a, b):
        _same_exactly(ma, mb, ma["type"])
        _same_exactly(ba or {}, bb or {}, ma["type"])


# --- vector mode: a perfectly conducting screen (lfphys.core.em.slit; closes STATUS V4) --------------------------------
def _seg_vec(h):
    return h.of("segment")[-1]["vector"]


def test_scalar_mode_is_the_default_and_has_no_vector_part():
    h = Harness(V, "photon_young")
    seg = h.of("segment")[0]
    assert seg["vector"] is None and "core.em.slit" not in [m["id"] for m in h.of("header")[0]["engine"]]
    assert sorted(seg["curves"]) == ["all", "cl"]


def test_vector_mode_hits_follow_the_vector_flux_not_the_scalar_one():
    h = Harness(V, "vector_narrow", seed=3)
    v = _seg_vec(h)
    assert v["hits"] == "vector" and "core.em.slit" in [m["id"] for m in h.of("header")[0]["engine"]]
    rate = h.of("header")[0]["rate"]
    h.run_to(60000 / rate)
    sim = h.sim
    hist = sim.hist["bins"].sum(axis=0).astype(float)
    cur = sim.theory["curves"]
    x2v, pv, _ = stats.chi2(hist, cur["all"])
    x2s, ps, _ = stats.chi2(hist, cur["kir"])
    assert pv > 1e-4  # the hits are drawn from the vector flux
    assert ps < 1e-8  # ... and the scalar Kirchhoff curve (same unit) is rejected by the same histogram
    c = sim.counts
    n_tr = c["detected"] + c["missed"]
    p = v["p_trans"]
    assert abs(n_tr / c["emitted"] - p) < 5 * math.sqrt(p * (1 - p) / c["emitted"])
    assert c["reflected"] + n_tr == c["emitted"]
    ch = h.checks()
    for pol in ("TE", "TM"):
        assert ch[f"vbal{pol}0"]["ok"] and ch[f"vmod{pol}0"]["ok"] and ch[f"vconv{pol}0"]["ok"]
    assert "fr" not in ch and "coh0" not in ch  # the scalar coherence fit is not applied to vector hits


def test_vector_mode_polarisation_below_te_cutoff():
    """Slits narrower than lambda/2 in a thick screen: TE (E along the slits, V) is cut off — its transmission falls
    like exp(-2 |beta_1| t) — while TM (H) passes through the TEM mode."""
    base = {"screen_model": "pec", "screen_t_um": 0.6, "a_um": 0.25, "d_um": 4.0, "L2_m": 0.01}
    hv = Harness(V, None, {**base, "pol_state": "V"})
    hh = Harness(V, None, {**base, "pol_state": "H"})
    v = _seg_vec(hv)
    k = 2 * math.pi / 632.8e-9
    beta1 = math.sqrt((math.pi / 0.25e-6) ** 2 - k * k)
    assert v["T_TE"] < 5 * math.exp(-2 * beta1 * 0.6e-6) and v["T_TM"] > 0.3
    assert _seg_vec(hv)["wV"] == pytest.approx(1.0) and _seg_vec(hh)["wH"] == pytest.approx(1.0)
    assert _seg_vec(hv)["p_trans"] < 1e-3 * _seg_vec(hh)["p_trans"]


def test_vector_and_scalar_curves_approach_each_other_for_wide_slits():
    def spread(a_um, L2):
        h = Harness(V, None, {"screen_model": "pec", "a_um": a_um, "d_um": 4 * a_um, "L2_m": L2, "pol_state": "D"})
        cur = h.sim.theory["curves"]
        return float(np.max(np.abs(cur["all"] - cur["kir"])) / np.max(cur["kir"])), _seg_vec(h)
    (narrow, _), (wide, vw) = spread(0.4, 0.01), spread(8.0, 0.2)  # thin screen, D
    assert narrow > 0.15 and wide < 0.02 and wide < narrow / 10
    # review B8 C7: at a = 8 um (k a = 79) the thin screen is solved by the edge basis, whose error is far below the
    # difference shown (the waveguide modes there were 0.2-0.5 % off, as large as the difference)
    assert vw["method"] == "edge" and max(vw["err_TE"], vw["err_TM"]) < 0.1 * wide


def _vector_counting(monkeypatch):
    import importlib
    vz = importlib.import_module("v02_double_slit.viz")
    calls = []
    orig = vz.vslit.solve

    def counting(*a, **k):
        calls.append(a[3] if len(a) > 3 else k.get("thickness"))
        return orig(*a, **k)
    monkeypatch.setattr(vz.vslit, "solve", counting)
    return calls


def test_vector_mode_detector_efficiency_and_dark_counts_in_the_expectation():
    """Review B8 C3: the vector curves left out the detector efficiency, so with dark counts a correct run's chi^2
    failed (p = 0.0 with eff = 0.2, 300 dark counts/s). Now they carry it; negative control: the curve without it."""
    h = Harness(V, "vector_narrow", {"eff": 0.2, "dark_rate": 300.0}, seed=7)
    rate = h.of("header")[0]["rate"]
    h.run_to(60000 / rate)
    hist = h.sim.hist["bins"].sum(axis=0).astype(float)
    cur = h.sim.theory["curves"]
    nb = len(hist)
    dark = 300.0 / rate / nb
    _, p_run, _ = stats.chi2(hist, cur["all"])
    _, p_noeff, _ = stats.chi2(hist, (cur["all"] - dark) / 0.2 + dark)
    assert p_run > 1e-4 and p_noeff < 1e-8
    assert h.sim.counts["dark"] > h.sim.counts["detected"]  # the dark counts matter here
    for name in ("kir", "vTE", "vTM"):  # the other curves in the same unit (with the efficiency)
        assert name in cur
    assert np.sum(cur["vTE"] + cur["vTM"]) == pytest.approx(np.sum(cur["all"] - dark), rel=1e-12)


def test_vector_curve_with_scalar_hits_is_a_shape_comparison():
    """Review B8 C8: with scalar hits the vector curve was per particle on the open width, without the efficiency or
    the elements' transmission (a zero-phase element: 'difference' 0.96 of the curve). Now it is the shape, scaled to
    the same total, and no difference is drawn."""
    h = Harness(V, "photon_young", {"screen_model": "pec", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1, "pol_state": "D",
                                    "eff": 0.5, "el1": "phase", "el1_angle": 0.0}, seed=2)
    seg = h.of("segment")[0]
    cur = h.sim.theory["curves"]
    assert seg["vector"]["hits"] == "scalar" and seg["vector"]["unit"] == "shape" and "diff" not in cur
    assert np.sum(cur["vec"]) == pytest.approx(np.sum(cur["all"]), rel=1e-12)
    # the same slits without the element (vector hits): the shapes agree to the vector-scalar difference of a = 2 um
    h2 = Harness(V, "photon_young", {"screen_model": "pec", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1, "pol_state": "D",
                                     "eff": 0.5}, seed=2)
    c2 = h2.sim.theory["curves"]
    assert np.max(np.abs(cur["vec"] / np.sum(cur["vec"]) - c2["all"] / np.sum(c2["all"]))) < 1e-12


def test_vector_solution_is_not_solved_again_for_the_source_or_the_detector(monkeypatch):
    """Review B8 C9: a change of the efficiency, the dark counts or the polarisation re-solved the conductor (15-17 s at
    k a = 129). The solution depends on none of them: kept and reweighted. A change of the screen distance recomputes
    the flux only; a change of the thickness solves again."""
    calls = _vector_counting(monkeypatch)
    h = Harness(V, "vector_narrow", seed=1)
    n0 = len(calls)
    # TE and TM, and no convergence solves (the error estimate uses sub-blocks); only TM solved again with twice the
    # modes, because its estimate on the screen exceeded the display's tolerance
    assert h.sim._vec_cache["doubled"] == {"TE": False, "TM": True} and n0 == 3
    for change in ({"eff": 0.5}, {"dark_rate": 10.0}, {"pol_state": "V"}, {"pol_state": "H"}, {"L2_m": 0.02}):
        h.set(**change)
        assert len(calls) == n0, change
    assert not h.errors()
    v = _seg_vec(h)
    assert v["wH"] == pytest.approx(1.0) and v["eff"] == 0.5
    h.set(screen_t_um=0.25)
    assert len(calls) >= n0 + 2 and not h.errors()


def test_vector_mode_error_estimate_bounds_the_truncation_error():
    """Review B8 C6: v02 showed T(1.25 M)/T(M) - 1, 3-6 times below the true error. Now the estimate (Richardson from
    sub-blocks, ``SlitSolution.error_estimate``) is shown, and lies above the true error of vector_narrow against the
    Richardson limits from 52, 104 and 208 modes (processing of review B8; the review's s02 gives the same digits)."""
    h = Harness(V, "vector_narrow", seed=1)
    V_ = h.sim.exp.vec
    for pol, lim in (("TE", 1.05651704), ("TM", 0.97420636)):
        true = abs(V_[pol]["T"] / lim - 1)
        assert true < V_[pol]["err_T"] < 4 * true and V_[pol]["err"] < 4e-3
        ch = h.checks()[f"vconv{pol}0"]
        assert ch["ok"] and ch["value"] == V_[pol]["err"] and "Richardson" in _en(ch["note"])


def test_vector_mode_announces_its_width_limit_with_one_number():
    """Review B8 C15: the limit is in the select's help and the refusal says the same number (20.7 lambda)."""
    from lfviz import registry
    sch = registry.load(V)["schema"]
    par = sch.by_id["screen_model"]
    assert "20.7 λ" in _en(par.help) and "k·a ≤ 130" in _en(par.help)
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"screen_model": "pec"})
    assert "20.7 λ" in _txt(e.value)


def test_vector_mode_refusals():
    for bad in ({"species": "electron", "energy_by": "ekin", "ekin_ev": 5e4, "a_um": 0.1, "d_um": 0.5},
                {"L1_m": 0.5}, {"dlam_rel": 0.05}, {"a_um": 30.0, "d_um": 100.0}):
        with pytest.raises(ValueError):
            Harness(V, None, {"screen_model": "pec", **bad})


def test_vector_mode_with_marks_keeps_scalar_hits_and_says_so():
    h = Harness(V, "photon_eraser", {"screen_model": "pec", "a_um": 2.0, "d_um": 10.0, "L2_m": 0.1}, seed=2)
    seg = h.of("segment")[0]
    assert seg["vector"]["hits"] == "scalar" and "marks" in _en(seg["vector"]["why"])
    assert {"all", "cl", "vec"} <= set(seg["curves"]) and "diff" not in seg["curves"]  # B8 C8: units differ, no strip
    assert any("scalar model" in _en(a) for a in seg["approx"])
    h.run_to(5000 / 1000.0)
    assert h.sim.counts["reflected"] == 0


def test_live_switch_to_the_conductor_screen_and_back():
    h = Harness(V, None, {"a_um": 1.0, "d_um": 5.0, "L2_m": 0.02})
    h.run_to(0.05)
    h.set(screen_model="pec", screen_t_um=0.3)
    h.run_to(0.1)
    h.set(screen_model="kirchhoff")
    segs = h.of("segment")
    assert [s["vector"] is not None for s in segs] == [False, True, False]
    assert not h.errors()


def test_a_vector_world_continues_from_its_checkpoint_as_the_original(tmp_path):
    """The vector screen's arrays are part of the world's state: a checkpoint of a vector world, continued in a new
    process, emits what the original emits (the shared test does this for the default, scalar world)."""
    import queue
    from lfviz import registry
    from lfviz.sim import Runner
    import test_checkpoint as tc
    viz = registry.load(V)
    params, errs = viz["schema"].resolve("vector_narrow", {})
    assert not errs
    msgs = []

    def emit(meta, blobs=None):  # one output function for the world and the runner (a checkpoint keeps it by reference)
        msgs.append((meta, blobs))
    sim = viz["simulation"](params, 7, emit)
    run = Runner(sim, emit, queue.Queue())
    run._start_world()
    tc._play(run, tc._steps(sim, 0, 12))
    file = tc._checkpoint(run, tmp_path)
    ck = [m for m, _ in msgs if m.get("type") == "checkpoint"][-1]
    n0 = len(msgs)
    times = tc._steps(sim, 12, 8)
    tc._play(run, times)
    original = tc._bytes(msgs[n0:])
    continued = tc._continue_in_new_process(tmp_path, file, [], ck["t"], times)
    assert any(m.get("type") == "detections" for m, _ in msgs[n0:])
    assert continued == original


# --- review UX-params (2026-11-04): P8, P15, P17, P18 ----------------------------------------------------------------
def test_dark_counts_are_bounded_per_step_and_refused_far_above_the_source():
    """P8: “Dark counts” = 1e12 1/s drew every dark count of a frame as an event (~2e9, 31 GB). Now a dark rate
    above 100 per emitted particle is refused before anything is built (check_params, the world, a live change), saying
    what to change; below it every step holds at most ~STEP_EVENTS events. Negative control: the step of before
    (4000/rate) at the limit would hold 100 times more dark counts."""
    from v02_double_slit.viz import DARK_PER_PARTICLE_MAX, SCHEMA, STEP_EVENTS, Simulation
    with pytest.raises(ValueError) as e:
        Simulation.check_params({**SCHEMA.defaults(), "dark_rate": 1e12})
    assert "Dark counts” to 1e+05" in _txt(e.value)
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"dark_rate": 1e12})
    assert "false counts per particle" in _txt(e.value)
    h = Harness(V, None, {})
    h.set(dark_rate=1e12)
    assert "false counts" in _en(h.errors()[-1]) and h.sim.dark_rate == 0.0  # refused, the world as it was
    rate = 1000.0
    h = Harness(V, None, {"dark_rate": DARK_PER_PARTICLE_MAX * rate}, seed=3)
    assert h.sim.max_step() == pytest.approx(STEP_EVENTS / (rate * (1 + DARK_PER_PARTICLE_MAX)))
    h.runner._advance(0.05)
    sizes = [m["n"] for m in h.of("detections")]
    assert sizes and max(sizes) < 1.2 * STEP_EVENTS  # Poisson around at most STEP_EVENTS per step
    assert 4000.0 / rate * DARK_PER_PARTICLE_MAX * rate > 50 * STEP_EVENTS  # the old step's dark counts


def test_coherence_is_undefined_when_a_slit_is_dark():
    """P15 [error in earlier]: polarisers at 0° and 90° in the slits (source H: slit 2 dark) showed |gamma_12| = 1.108, a
    fit of rounding noise against the reference 6e-17, failed. Now the check says why it is undefined (info, no value)
    and the frame's histogram fit too. Negative control: both slits open, and the same polarisers with D light (both
    pass: the which-path marks give 0), stay defined and pass."""
    h = Harness(V, None, {"el1": "polarizer", "el2": "polarizer", "el1_angle": 0.0, "el2_angle": 90.0})
    c = h.checks()["coh0"]
    assert c["value"] is None and c.get("info") and "slit 2 is dark" in _en(c["note"])
    h.run_to(400 / 1000.0)
    st = h.sim.frame()[0]
    assert st.get("coh") is None or st["coh"].get("why")
    for vals, ref in (({}, 1.0), ({"pol_state": "D", "el1": "polarizer", "el2": "polarizer", "el2_angle": 90.0}, 0.0)):
        c = Harness(V, None, vals).checks()["coh0"]
        assert c["value"] == pytest.approx(ref, abs=1e-6) and not c.get("info")


def test_refusals_name_the_choice_and_what_to_take():
    """P17 / UX-ui U13: the element was named by its id ('rot_y') and the slit by a bare number. Now the element by its label,
    the particle, and the choices that work (each of them builds). The schema marks the options per particle
    (option-level show_if, when the framework has it)."""
    import re
    import v02_double_slit.viz as VZ
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"el1": "rot_y"})
    text = _txt(e.value)
    assert "“spin rotation about y” at slit 1 does not act on a photon" in text and "rot_y" not in text
    for lab in re.findall(r"“([^”]+)”", text.split("one of these for")[1].split(":", 1)[1]):
        kind = next(k for k, v in VZ._ELEM_LABEL.items() if _en(v) == lab)
        Harness(V, None, {"el1": kind})
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"wp_mode": "qubit", "wp_slit": 5})
    assert "from 1 to 2" in _txt(e.value)
    with pytest.raises(ValueError) as e:
        Harness(V, "c60", {"analyzer": "on"})
    assert "“Analyser in front of the screen” = none" in _txt(e.value)
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"energy_by": "speed"})
    assert "“Set by”" in _txt(e.value)
    if VZ.OPTION_SHOW_IF:
        el1 = next(p for p in VZ.SCHEMA.to_json()["params"] if p["id"] == "el1")
        shown = {o["value"]: o.get("show_if") for o in el1["options"]}
        assert shown["rot_y"] == {"species": ["electron", "neutron", "custom"]} and shown["polarizer"] == {
            "species": ["photon"]} and shown["phase"] is None


def test_probe_recoil_and_grw_kicks_beyond_the_screen_are_refused_with_the_threshold():
    """P18: a probe λ of 0.001 nm (50 keV electrons) allocated 2 GiB in one array of the screen's expectation (the
    screen grid extended by the recoil, ±10.7 m); GRW λ = 1e12, r_C = 1e-3 nm overflowed numpy. Now refused before
    the allocation, with the shift, the grid and the probe wavelength that fits; that wavelength builds."""
    import re
    with pytest.raises(ValueError) as e:
        Harness(V, "electron_microscope", {"mic_lambda_nm": 0.001})
    text = _txt(e.value)
    assert "up to ±10.7 m" in text and "GB" in text
    lam = float(re.search(r"at least ~([\d.e+-]+) nm", text).group(1))
    Harness(V, "electron_microscope", {"mic_lambda_nm": 1.05 * lam})
    h = Harness(V, "electron_eraser")
    h.set(wp_mode="microscope", mic_lambda_nm=0.001)
    assert "are shifted" in _en(h.errors()[-1]) and h.sim.app.wp_mode == "qubit"  # refused, the world as it was
    with pytest.raises(ValueError) as e:
        Harness(V, None, {"collapse": "grw", "grw_lambda": 1e12, "grw_rc_nm": 0.001, "species": "c60"})
    assert "weaken the GRW collapse" in _txt(e.value)


def test_honest_failures_are_marked_expected():
    """Review UX-params P23: the Sorkin parameter of «triple_mod» (the Born rule changed) fails by design; it carries
    `expected` and the preset a note; the same check under the Born rule carries none (negative control)."""
    from v02_double_slit.viz import SCHEMA as S2
    h = Harness(V, "triple_mod")
    c = h.checks()["sork0"]
    assert c["ok"] is False and "Born rule is changed" in _en(c["expected"])
    assert S2.presets["triple_mod"]["note"]
    c = Harness(V, "triple").checks()["sork0"]
    assert c["ok"] and not c.get("expected")
