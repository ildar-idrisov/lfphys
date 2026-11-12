# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v12: arrival times. Every preset builds and passes its static checks; a small free packet runs to the end of its
window and passes every check (the flux and psi on the plane against the exact free evolution, the Bohm hit times
against the first-arrival law, the soft detector's reflection against stationary transfer matrices, the ABR
identity, v11's checks); nothing arrives before the wave can; the backflow state's flux goes negative while Bohm's
first-arrival density does not; a train's exponential rule damps the later peaks; through the slits a slit closed in
flight acts on both runs; refusals; GPU = CPU. The geometry of these tests is small."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core import backend  # noqa: E402
from v11_double_slit_2d.viz import COST_LIMIT  # noqa: E402
from v12_arrival_times_2d.viz import SCHEMA  # noqa: E402

V = "v12_arrival_times_2d"
SMALL = {"grid": "coarse", "n_bohm": 300, "n_tracks": 20, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0}


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def run_out(h):
    while not h.sim.done:
        h.run_to(h.sim.t + 2.0 * h.sim.tunit)
    return h


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build(preset):
    h = Harness(V, preset)
    hd = h.of("header")[-1]
    assert hd["arrival"]["rules"][:2] == ["flux", "bohm"]
    assert not failed(h), failed(h)  # the static checks: grid, absorbers, the initial state, the soft detector
    assert "arr_state" in h.checks()
    # the initial state's rules are computed at the start but revealed only with the run's time; the window's length
    # (a consequence of the run) is not in the header (review B4-5)
    assert (h.sim.curves is not None) == (hd["arrival"]["scene"] == "free")
    assert "tau_obs" not in hd["arrival"]
    assert not any(m.get("ref_n") for m in h.of("arrival"))
    assert 0 < h.sim.est_cost < COST_LIMIT[h.sim.prop.device]


def test_small_free_packet_passes_every_check():
    h = run_out(Harness(V, "gauss", SMALL))
    ids = set(h.checks())
    assert {"norm", "numerics", "flux_absorbed", "bohm_born", "bohm_fraction", "symmetry", "arr_flux_exact",
            "arr_plane_psi", "arr_bohm_times", "arr_soft_reflection", "arr_abr_identity", "arr_det_norm",
            "screen_y", "bohm_y", "bohm_y_motion"} <= ids  # the third dimension: the exact product with eta (v11)
    assert not failed(h), [(i, h.checks()[i]) for i in failed(h)]
    r = h.of("arrival_result")[-1]
    for k in ("flux", "bohm_law", "abk", "sc"):
        assert abs(r["rules"][k]["total"] - 1) < 2e-3, (k, r["rules"][k])
    revealed = sum(m["ref_n"] for m in h.of("arrival"))
    assert revealed == len(h.sim.curves["tau"])  # by the end, every sample of the initial-state curves
    # far from a wide packet the ideal rules agree on the mean time; the detector models lose particles
    m = r["rules"]["flux"]["mean"]
    for k in ("bohm_law", "abk", "sc"):
        assert abs(r["rules"][k]["mean"] / m - 1) < 0.02, k
    assert 0 < r["none"]["wlodarz"] < 1 and 0 < r["soft"]["reflected"] < 0.01
    # the joint distribution: rows of J(x, t) over the screen, their time integral is the pattern
    n = sum(m["row_n"] for m in h.of("arrival"))
    assert n == len(h.sim.rows) and n > 10
    assert not h.errors()


def test_nothing_arrives_before_the_wave_can():
    """The packet's front 5 sigma ahead, at 5 standard deviations above the mean speed, needs a time to reach the
    plane: before half of it no hit, no current, no click of any rule."""
    h = Harness(V, "gauss", SMALL)
    s = h.sim
    vmax = 2 * math.pi * (1 + 5 / (2 * s.geo.sz * 2 * math.pi))
    t_first = (s.D - 5 * s.geo.sz) / vmax
    h.run_to(0.5 * t_first * s.tunit)
    assert s.tau > 0.2 * t_first
    assert not h.of("hits")
    ser = s._series()
    for k in ("flux", "wlodarz", "ms", "soft"):
        assert np.max(np.abs(ser[k])) < 1e-6, k


def test_backflow_flux_goes_negative_but_bohm_first_arrivals_do_not():
    """The slow and the fast packet meet at the plane: there the current flows back for a while (closed form: 1.5 % of
    the probability); the first-arrival density of Bohm's trajectories stays >= 0."""
    h = Harness(V, "backflow", {**SMALL, "sigma_z": 2.0, "L": 11.0, "soft": False, "n_bohm": 200})
    s = h.sim
    t_meet = s.D / (0.25 * 2 * math.pi)
    while s.tau < 1.6 * t_meet:
        h.run_to(s.t + 2.0 * s.tunit)
    ser = s._series()
    assert ser["flux"].min() < -0.01
    assert ser["bohm_law"].min() >= 0
    Jx = s.fg.current(s.D, ser["tau"])
    assert np.max(np.abs(ser["flux"] - Jx)) < 1e-3 * np.max(np.abs(Jx))


def test_a_train_damps_the_exponential_rule():
    h = run_out(Harness(V, "train", {**SMALL, "n_train": 3, "sep": 12.0, "soft": False}))
    assert not failed(h), failed(h)
    c = h.checks()["arr_train"]
    assert c["info"] and c["value"] < 0.15  # small packets spread: Das's no-spreading ratio within 15 %
    ser = h.sim._series()
    tau, D, sep, v0 = ser["tau"], h.sim.D, 12.0, 2 * math.pi
    peaks = [ser["wlodarz"][np.abs(tau - (D + j * sep) / v0) < 0.5 * sep / v0].max() for j in range(3)]
    assert peaks[0] > peaks[1] > peaks[2]


def test_through_the_slits_a_slit_closed_in_flight_acts_on_both_runs():
    """Slit B is closed while the packet flies, before its front (3 sigma ahead) reaches the plate. (Closed while the
    wave is inside the slit, the wall appears at once inside the wave: it makes waves the coarse test grid does not
    resolve, and `numerics` says so.)"""
    h = Harness(V, "slits", {"grid": "coarse", "n_bohm": 600, "n_tracks": 10, "a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0,
                             "sigma_x": 3.0, "sigma_z": 2.0, "soft": True})
    s = h.sim
    assert "arr_flux_exact" not in h.checks() and not h.of("arrival_ref")
    h.run_to(s.t + 0.1 * s.t0 * s.tunit)
    assert s.geo.z_src + 3 * s.geo.sz + 2 * math.pi * s.tau < -0.5 * s.geo.w
    h.set(slit_b=False)
    assert not s.live["slit_b"]
    assert np.array_equal(np.asarray(s.det.H.V), np.asarray(s.prop.H.V))
    run_out(h)
    assert not failed(h), failed(h)
    assert "arr_bohm_times" in h.checks() and "arr_det_norm" in h.checks()


def test_refusals():
    with pytest.raises(ValueError, match="перекрываются"):
        Harness(V, "train", {**SMALL, "sep": 8.0})
    with pytest.raises(ValueError, match="слишком близко"):
        Harness(V, "gauss", {**SMALL, "L": 6.0})


@pytest.mark.skipif(not backend.devices()["gpu"]["available"], reason="no GPU")
def test_gpu_equals_cpu():
    from lfphys.core.quantum import schrodinger_nd as S
    h = Harness(V, "gauss", SMALL)
    assert h.sim.prop.device == "gpu" and h.sim.det.device == "gpu"
    H = h.sim.det.H
    cpu = S.SplitOperator(H, h.sim.dt, track_absorbed=True, force_cpu=True, why="тест")
    a = h.sim.det.put(h.sim._packet(H, h.sim.g))
    b = cpu.put(h.sim._packet(H, h.sim.g))
    a = h.sim.det.step(a, 200)
    b = cpu.step(b, 200)
    assert np.max(np.abs(h.sim.det.get(a) - cpu.get(b))) < 1e-11
    pa, da = h.sim.det.plane(a, 1, h.sim.iL, 32)
    pb, db = cpu.plane(b, 1, h.sim.iL, 32)
    assert np.max(np.abs(da - db)) < 1e-9


# --- live detectors and plate (review UX-ui U12) ------------------------------------------------------------------------
def test_a_detector_strength_set_before_the_signal_is_the_world_built_with_it():
    """λ₀ of the exponential rules and W₀ of the soft detector set live at t = 0 give the very series of a world built
    with them (bit for bit after 60 pairs); the event says the detector had not been reached."""
    live = Harness(V, "gauss", SMALL)
    live.set(mu_w=3.0, mu_ms=0.5, W0=2.0)
    assert not live.errors() and "ещё не дошла" in live.of("event")[-1]["text"]
    built = Harness(V, "gauss", {**SMALL, "mu_w": 3.0, "mu_ms": 0.5, "W0": 2.0})
    for h in (live, built):
        h.run_to(60 * h.sim.pair * h.sim.tunit)
    a, b = live.sim._series(), built.sim._series()
    for k in ("wlodarz", "ms", "soft"):
        assert np.array_equal(a[k], b[k]), k
    assert np.array_equal(live.sim.det.get(live.sim.psi_d), built.sim.det.get(built.sim.psi_d))


def test_a_detector_strength_changed_while_the_signal_arrives_acts_from_that_moment():
    """λ₀ of Włodarz's rule raised half-way through the arrival: the rule's density before the change is the one of the
    unchanged world (the past is not rewritten), after it it is λ₀′ v₀ ρ e^{−Λ} with Λ continuous (second method: the
    rate integrated from the record by hand); the unchanged world's density differs after the change (negative control).
    The comparison that assumes one λ₀ for the whole flight is not made."""
    ref = Harness(V, "gauss", {**SMALL, "soft": False})
    h = Harness(V, "gauss", {**SMALL, "soft": False})
    t_half = h.sim.t0 * h.sim.tunit
    for g in (ref, h):
        g.run_to(t_half)
    h.set(mu_w=4.0)
    assert "до этого момента посчитано с прежним значением" in h.of("event")[-1]["text"]
    tau_c = h.sim.tau
    for g in (ref, h):
        g.run_to(t_half + 0.6 * h.sim.t0 * h.sim.tunit)
    a, b = h.sim._series(), ref.sim._series()
    before = a["tau"] <= tau_c
    assert before.sum() > 10 and (~before).sum() > 10
    assert np.array_equal(a["wlodarz"][before], b["wlodarz"][before])
    rho, dt, v0 = np.asarray(h.sim.rec["rho"]), h.sim.dt, 2 * math.pi
    lam = np.where(before, 1.0, 4.0) * v0 * rho
    Lam = np.cumsum(lam) * dt
    hand = -np.diff(np.concatenate([[1.0], np.exp(-Lam)])) / dt
    assert np.max(np.abs(a["wlodarz"] - hand)) < 1e-12 * np.max(hand)
    assert np.max(np.abs(a["wlodarz"][~before] - b["wlodarz"][~before])) > 0.1 * np.max(b["wlodarz"])
    assert h.sim._one_value("mu_w") is None and h.sim._one_value("mu_ms") == 1.0


def test_soft_detector_height_changed_at_the_detector_leaves_the_stationary_comparison_out():
    """W₀ raised while the wave is at the detector: the second run's absorber is rebuilt from that moment (its norm +
    absorbed stays 1), the grid's check takes the highest W₀, and the stationary reflection for one W₀ is reported as
    not applicable (information) instead of a pass or a failure."""
    h = Harness(V, "gauss", SMALL)
    h.run_to(h.sim.t0 * h.sim.tunit)
    h.set(W0=3.0)
    assert not h.errors()
    from v12_arrival_times_2d.engine import apparatus as AP12
    W_d = h.sim.W + AP12.soft_detector(h.sim.g, h.sim.zL, 3.0 * AP12.E0, h.sim.geo.edge)
    assert np.array_equal(np.asarray(h.sim.det.H.W), W_d)
    assert "W₀ = 3 E₀" in h.checks()["soft_grid"]["note"]
    run_out(h)
    c = h.checks()
    assert c["arr_soft_reflection"]["info"] and c["arr_soft_reflection"]["value"] is None
    assert c["arr_det_norm"]["ok"]
    assert not failed(h), failed(h)


def test_detector_and_plate_refusals_leave_the_world_unchanged():
    """No soft detector: its W₀ is refused; free flight: the plate's a, d, w, V₀ are refused (no plate); the live values
    are as before."""
    h = Harness(V, "gauss", {**SMALL, "soft": False})
    live = dict(h.sim.live)
    h.set(W0=2.0)
    assert "мягкого детектора в этом мире нет" in h.errors()[-1]
    h.set(a=3.0)
    assert "пластины нет" in h.errors()[-1]
    assert h.sim.live == live and h.sim.det_hist["W0"] == [(0.0, 1.0, True)]


def test_through_the_slits_a_live_plate_acts_on_both_runs():
    """The plate's width changed in flight through the slits: the soft detector's run gets the same new plate."""
    h = Harness(V, "slits", {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0,
                             "sigma_x": 3.0, "sigma_z": 2.0, "soft": True})
    h.run_to(h.sim.t + 0.1 * h.sim.t0 * h.sim.tunit)
    peak = float(np.max(np.asarray(h.sim.prop.H.V)))  # the wall's top (its tanh edges keep it below V0 E0 on the grid)
    h.set(a=2.0, V0=5.0)
    assert not h.errors(), h.errors()
    s = h.sim
    assert s.geo.a == 2.0 and np.array_equal(np.asarray(s.det.H.V), np.asarray(s.prop.H.V))
    assert float(np.max(np.asarray(s.prop.H.V))) == pytest.approx(peak * 5.0 / 4.0, rel=1e-12)


def test_a_new_world_from_the_header_and_the_live_values_builds():
    """The player's «Начать новый мир» without a scenario sends the header's parameters with the live values in force:
    they are this world's own (v11's fixed path mark and flux were among them, and every such new world was refused:
    «нет параметра «mark»», found while processing review UX-ui U12); the negative control: with them it is refused."""
    h = Harness(V, "gauss", SMALL)
    hd = h.of("header")[-1]
    assert set(hd["params"]) == set(SCHEMA.by_id) and set(hd["live"]) == set(SCHEMA.live_ids())
    h.set(mu_w=2.0)
    h.cmd("new_world", params={**hd["params"], **h.of("live")[-1]["values"]})
    assert [m["world"] for m in h.of("header")] == [1, 2] and h.sim.params["mu_w"] == 2.0
    _, errors = SCHEMA.resolve(None, {**hd["params"], "mark": "none", "mark_deg": 0.0, "flux": 0.0})
    assert errors


def test_every_length_and_detector_parameter_carries_its_unit_in_the_label():
    """Review UX-ui U19: the player shows a parameter's label, not its unit field."""
    for p in SCHEMA.params:
        if p.unit:
            assert p.unit in p.label, (p.id, p.label, p.unit)
    for k in ("W0", "kappa", "V0"):
        assert "в " + SCHEMA.by_id[k].unit in SCHEMA.by_id[k].label
    for k in ("mu_w", "mu_ms"):
        assert "безразмерная" in SCHEMA.by_id[k].label
