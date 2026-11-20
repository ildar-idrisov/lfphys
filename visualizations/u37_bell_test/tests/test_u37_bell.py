# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u37 Bell test with real detectors: every preset, the statistics against the engine's predictions for the devices,
the detectors' closed forms, the slots, no-signalling, causality, live changes, the reviews' regressions."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.constants import C  # noqa: E402
from lfphys.i18n import render  # noqa: E402
from lfphys.theories.models import photodetector as PD  # noqa: E402
from lfphys.tools import bell_stats as BS  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.errors import Refusal  # noqa: E402

V = "u37_bell_test"
VIZ = registry.load(V)
PRESETS = list(VIZ["schema"].presets)
TSIRELSON = 2 * math.sqrt(2)
MOD = __import__("u37_bell_test.viz", fromlist=["Simulation"])
EXP = __import__("u37_bell_test.engine.experiment", fromlist=["Law"])


def run(preset, seconds=1.0, seed=1, **params):
    """A stream world for ``seconds`` of world time (10⁴ pairs per second: about 4 600 coincidences per second), in
    ten steps; a slots world for 10⁹ slots."""
    h = Harness(V, preset, params or None, seed=seed)
    tend = 1000.0 if h.sim.slots_mode else seconds
    for k in range(1, 11):
        h.run_to(tend * k / 10)
    return h


def coincs(h, since=-1.0):
    """The coincidences sent in detail ("pairs" messages), with the time of the message that revealed them."""
    out = {}
    for m, b in h.msgs:
        if m.get("type") != "pairs" or m["t"] <= since or "c_tA" not in b:
            continue
        tA = np.asarray(b["c_tA"], float)
        d = {"tA": tA, "tB": tA + b["c_dtB"], "te": tA + b["c_dte"], "tcA": tA + b["c_dtcA"], "tcB": tA + b["c_dtcB"],
             "sA": b["c_sA"], "sB": b["c_sB"], "oA": b["c_oA"], "oB": b["c_oB"], "alA": b["c_alA"],
             "alB": b["c_alB"], "fl": b["c_fl"], "msg_t": np.full(len(tA), m["t"])}
        for k, v in d.items():
            out.setdefault(k, []).append(np.asarray(v))
    return {k: np.concatenate(v) for k, v in out.items()}


def failed(h):
    return {k: (c.get("value"), c.get("ref"), render(c.get("note", ""))[:160]) for k, c in h.checks().items()
            if c.get("ok") is False}


# --- every preset -------------------------------------------------------------------------------------------
@pytest.mark.parametrize("preset", PRESETS)
def test_every_preset_runs_and_no_check_fails(preset):
    h = run(preset)
    assert not h.errors()
    assert not failed(h)
    for c in h.checks().values():  # the player's own verdict for checks without an explicit ok (info: no verdict)
        if "ok" not in c and not c.get("info") and c["ref"] is not None and c["rel"] is not None:
            assert abs(c["rel"]) <= max(c["tol"], 1e-12), c
    assert h.of("header")[0]["title"]["$t"] == "Bell test: {law}"
    assert h.sim.seg_counts["coinc"] > 2000


# --- the laws -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("preset", ["photon_chsh", "spin_chsh"])
def test_quantum_worlds_reach_tsirelson_and_violate_chsh_under_fair_sampling(preset):
    h = run(preset, 2.0)
    s = h.sim._S(h.sim._cells())
    assert abs(abs(s["S"]) - TSIRELSON) < 5 * s["se"]
    assert (abs(s["S"]) - 2) / s["se"] > 15
    assert any(render(e["text"]).startswith("Violation of the CHSH inequality under fair sampling")
               for e in h.of("event"))
    assert h.of("header")[0]["modifications"] == []
    # with the real detectors (η 0.68) the same run does not violate J: the detection loophole stays open
    j = h.sim._J()
    assert j["Jexp"] < 0 and j["J"] < 5 * j["se"]


@pytest.mark.parametrize("preset,S_exact", [("photon_lhv", math.sqrt(2)), ("spin_lhv", 2.0)])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_local_hidden_variables_never_exceed_two(preset, S_exact, seed):
    h = run(preset, 2.0, seed=seed)
    s = h.sim._S(h.sim._cells())
    assert abs(s["S"]) <= 2 + 5 * s["se"]
    assert abs(abs(s["S"]) - S_exact) < 5 * s["se"]  # the model's own expectation (the sign model saturates 2)
    assert h.checks()["bound"]["ok"] is True and h.checks()["J_bound"]["ok"] is True
    assert [m["id"] for m in h.of("header")[0]["modifications"]] == ["law"]
    assert any(e["id"] == "theories.alternatives.local_hidden" for e in h.of("header")[0]["engine"])


def test_gisin_and_gisins_model_passes_two_under_fair_sampling_and_keeps_J_below_zero():
    h = run(None, 2.0, law="gg", eta_A=1.0, eta_B=1.0)
    s = h.sim._S(h.sim._cells())
    assert abs(s["S"] - TSIRELSON) < 5 * s["se"]       # the detected pairs: the singlet's correlation
    j = h.sim._J()
    assert j["J"] < 5 * j["se"] and j["Jexp"] < 0       # all the slots: local
    meas = h.sim.frame()[0]["meas"]
    # each detector fires for 3/8 of the pairs (3/4 of them at the station), η = 1
    rate = meas["singles_A"] / (h.sim.store.get_time("A", 0.0) + h.sim.store.get_time("A", 45.0))
    assert rate == pytest.approx(0.75 * 1e4 + 2 * 250.0, rel=0.03)
    assert not failed(h)


def test_engine_modules():
    h = Harness(V, "photon_chsh")
    layers = {e["id"]: e["layer"] for e in h.of("header")[0]["engine"]}
    assert layers["core.quantum.qubits"] == "core" and layers["core.causality"] == "core"
    assert layers["theories.models.photodetector"] == "theories"
    assert "theories.alternatives.local_hidden" not in layers


def test_no_signalling_from_the_run_counts():
    h = run("photon_chsh", 2.0)
    ch = h.checks()
    for cid in ("nsA0", "nsA1", "nsB0", "nsB1"):
        assert ch[cid]["ok"] is True and abs(ch[cid]["value"]) < 0.06
    assert ch["nosig_law"]["ok"] is True and ch["nosig_law"]["value"] < 1e-14


def test_sampled_ports_match_the_closed_forms_at_many_angles():
    """The wrapper's port mapping (0: +, 1: −) and angle conventions against textbook closed forms."""
    rng = np.random.default_rng(5)
    forms = {("photon", "quantum"): lambda d: math.cos(2 * d), ("spin", "quantum"): lambda d: -math.cos(d),
             ("photon", "lhv"): lambda d: 0.5 * math.cos(2 * d),
             ("spin", "lhv"): lambda d: -1 + 2 * abs((d + math.pi) % (2 * math.pi) - math.pi) / math.pi,
             ("photon", "gg"): lambda d: math.cos(2 * d)}
    n = 40000
    for (pair, law), f in forms.items():
        L = EXP.Law(pair, law)
        for a, b in rng.uniform(-180, 180, (5, 2)):
            iA, iB = L.sample(a, b, n, rng)
            both = (iA >= 0) & (iB >= 0)
            A, B = 1 - 2 * iA[both].astype(float), 1 - 2 * iB[both].astype(float)
            ref = f(math.radians(a - b))
            assert L.E(a, b) == pytest.approx(ref, abs=1e-12)
            assert np.mean(A * B) == pytest.approx(ref, abs=5 * math.sqrt((1 - ref ** 2) / both.sum()) + 1e-9)
            if law == "gg":
                assert both.mean() == pytest.approx(0.5, abs=0.01)  # both detected in half of the pairs


def test_the_sequential_quantum_draw_is_the_joint_born_rule():
    """L_A ≠ L_B: the first particle by the reduced state, its partner conditioned on it (Lüders), give the joint Born
    probabilities."""
    L = EXP.Law("photon", "quantum", "eberhard", -2.9, 0.9)
    rng = np.random.default_rng(2)
    n = 200000
    a, b = 62.4, 25.5
    first = L.sample_first("A", a, n, rng)
    second = L.sample_second("B", a, b, first, rng)
    P = L.port_table(a, b)
    obs = np.zeros((2, 2))
    np.add.at(obs, (first, second), 1)
    assert np.allclose(obs / n, P, atol=5 * np.sqrt(P * (1 - P) / n).max())


# --- the detectors, the window, the accidentals ------------------------------------------------------------
def test_the_counts_follow_the_detectors_closed_forms():
    h = run("photon_chsh", 2.0)
    ch = h.checks()
    for cid in ("singles", "window", "acc", "J", "CH", "S", "S_sub", "slot_coupling"):
        assert ch[cid]["ok"] is True, (cid, ch[cid])
    assert ch["slot_coupling"]["value"] == pytest.approx((20e-9 + 5 * 350e-12 * PD.FWHM_TO_SIGMA) / 1e-6)


def test_a_bright_background_and_a_wide_window_add_the_accidentals_the_estimate_finds():
    h = run(None, 2.0, bg_rate=1e5, window_ns=25.0)
    cells = h.sim._cells()
    s = h.sim._S(cells)
    Ssub, se_sub, accs = h.sim._S_sub(cells)
    est, own = sum(a.sum() for a in accs), sum(sum(c["acc"]) for c in cells)
    assert own > 0.15 * (h.sim.seg_counts["coinc"] - own)  # about a fifth of the true coincidences
    assert abs(own - est) < 5 * math.sqrt(est)
    assert s["S"] < 2.5 and abs(Ssub - TSIRELSON) < 5 * se_sub
    assert not failed(h)


def test_the_dead_time_carries_across_the_steps_and_the_emissions_do_not_depend_on_them():
    """The emissions and the slots' bits come from their own generators in blocks: the same whatever the steps."""
    a = Harness(V, "photon_chsh")
    b = Harness(V, "photon_chsh")
    a.run_to(0.05)
    for k in range(1, 51):
        b.run_to(0.001 * k)
    assert a.sim.counter.counts["emitted"] == b.sim.counter.counts["emitted"]
    ka = np.arange(0, 49000)
    assert np.array_equal(a.sim.counter.setting("A", ka), b.sim.counter.setting("A", ka))
    # a detector is dead after each recorded count, also across a step: no two raw counts of one detector closer than
    # t_d (the calls go A+, A−, B+, B− in every step; a bright background makes the dead time matter)
    h = Harness(V, None, {"bg_rate": 5e6, "dark_rate": 0.0})
    raw = []
    orig = PD.detect

    def spy(arr, det, t0, t1, rng):
        out = orig(arr, det, t0, t1, rng)
        raw.append(out)
        return out
    PD.detect = spy
    try:
        for k in range(1, 41):
            h.run_to(2e-6 * k)
    finally:
        PD.detect = orig
    assert len(raw) >= 4 * 40
    for d in range(4):
        t = np.concatenate(raw[d::4])
        assert len(t) > 100 and np.all(np.diff(t) >= 20e-9 * (1 - 1e-9))


# --- causality and the slots -------------------------------------------------------------------------------
def test_outcomes_are_revealed_only_when_the_particles_arrive_and_clicks_carry_the_jitter():
    h = run("photon_chsh", 0.3)
    d = coincs(h)
    true = (d["fl"] & EXP.F_TRUE) > 0
    flight = 500.0 / C
    assert np.all(np.maximum(d["tA"], d["tB"]) <= d["msg_t"] + 1e-9)  # never shown before the click
    sig = 350e-12 * PD.FWHM_TO_SIGMA
    assert np.all(np.abs(d["tA"][true] - d["te"][true] - flight) < 7 * sig)  # a click at the arrival ± jitter
    assert np.all(d["tcA"] < d["tA"]) and np.all(d["tcB"] < d["tB"])  # the choice precedes the click
    # the choice comes τ before the slot: between τ and τ + T_s before the click (± jitter)
    lead = d["tA"] - d["tcA"]
    assert np.all(lead > 100e-9 - 7 * sig) and np.all(lead < 1.1e-6 + 7 * sig)
    first = [e for e in h.of("event") if e.get("kind") == "detection"][0]
    assert first["t"] >= flight


def test_random_choice_per_slot_is_space_like_and_a_slow_choice_is_not():
    h = run("photon_chsh", 0.3)
    fl = coincs(h)["fl"]
    assert np.all(fl & 3 == 3)  # both choices outside the light cone of the other side's click
    h2 = run("photon_slow_choice", 0.3)
    assert np.all(coincs(h2)["fl"] & 3 == 0)
    assert "OPEN" in render(h2.checks()["st_loc"]["label"]) and "closed" in render(h.checks()["st_loc"]["label"])
    assert h.sim.frame()[0]["meas"]["local_frac"] == 1.0 and h2.sim.frame()[0]["meas"]["local_frac"] == 0.0


def test_fixed_settings_become_time_like_as_they_age():
    h = Harness(V, "scan")
    assert "space-like" in render(h.checks()["st_loc"]["label"])  # set at t = 0: the next pair is outside
    for k in range(1, 6):
        h.run_to(0.02 * k)
    assert "OPEN" in render(h.checks()["st_loc"]["label"])  # known long before: inside the light cone
    d = coincs(h)
    late = d["tA"] > 4 * 500.0 / C
    assert np.all(d["fl"][late] & 3 == 0)


@pytest.mark.parametrize("L,tau_ns,slot_ns", [(500.0, 100.0, 1000.0), (2.0, 5.0, 10.0), (1e4, 5e4, 1000.0),
                                              (300.0, 300.0, 1000.0)])
def test_space_time_checks_against_closed_forms(L, tau_ns, slot_ns):
    h = Harness(V, "photon_chsh", {"L_A_m": L, "L_B_m": L, "tau_ns": tau_ns, "slot_ns": slot_ns})
    ch = h.checks()
    lead = (tau_ns + slot_ns) * 1e-9
    assert ch["st_loc"]["value"] == pytest.approx((C * lead) ** 2 - 4 * L * L, rel=1e-9)
    if C * lead < 2 * L:
        assert ch["st_rev"]["value"] == pytest.approx(C * lead / (2 * L), rel=1e-12)
        assert ch["st_rev"]["ref"] == pytest.approx(C * lead / (2 * L), rel=1e-9)
    else:
        assert ch["st_rev"]["value"] is None


def test_unequal_distances_take_the_later_detection_for_the_locality_check():
    """Review R2-W F8: each station's slots start at its own arrival time, so the latest detection at B comes
    τ + T_s + (L_B − L_A)/v after the choice at A. At L_A = 100 m, L_B = 500 m that is 2.43 µs: c·Δt = 730 m > 600 m,
    time-like (with τ + T_s alone, 330 m, it read «space-like»); the coincidences' own flags agree. Mirrored, the
    direction is B → A; the freedom of choice is checked at the nearer station."""
    for LA, LB, x, y in ((100.0, 500.0, "A", "B"), (500.0, 100.0, "B", "A")):
        h = run(None, 0.2, L_A_m=LA, L_B_m=LB)
        ch = h.checks()
        lead = (100.0 + 1000.0) * 1e-9 + abs(LB - LA) / C
        assert ch["st_loc"]["value"] == pytest.approx((C * lead) ** 2 - (LA + LB) ** 2, rel=1e-9)
        assert ch["st_loc"]["value"] > 0
        lab = ch["st_loc"]["label"]
        assert "OPEN" in render(lab) and render(lab).startswith(f"Choice at {x} ↔ the latest detection at {y} ")
        assert ch["st_rev"]["value"] is None
        assert h.sim.frame()[0]["meas"]["local_frac"] < 1.0  # some coincidences are time-like
        near = min(LA, LB)
        tau = 100e-9
        assert ch["st_free"]["value"] == pytest.approx((near - C * tau) ** 2 - near ** 2, rel=1e-9)
        assert render(ch["st_free"]["label"]).startswith(f"Choice at {'A' if LA < LB else 'B'} ↔ emission")
    # a space-like case at unequal distances: the reversal speed with the longer lead, mirrored for Bob's choice too
    h = Harness(V, "photon_chsh", {"L_A_m": 300.0, "L_B_m": 900.0})
    ch = h.checks()
    lead = 1.1e-6 + 600.0 / C
    assert ch["st_loc"]["value"] < 0 and ch["st_rev"]["value"] == pytest.approx(C * lead / 1200.0, rel=1e-12)
    assert ch["st_rev"]["ref"] == pytest.approx(C * lead / 1200.0, rel=1e-9)
    h = Harness(V, "photon_chsh", {"L_A_m": 900.0, "L_B_m": 300.0})
    ch = h.checks()
    assert render(ch["st_rev"]["label"]).startswith("The order “choice at B → detection at A”") and ch["st_rev"]["ref"] == pytest.approx(C * lead / 1200.0, rel=1e-9)


def test_unequal_distances_reveal_each_outcome_at_its_own_arrival():
    h = run(None, 0.5, L_A_m=200.0, L_B_m=800.0)
    d = coincs(h)
    true = (d["fl"] & EXP.F_TRUE) > 0
    assert np.allclose(d["tB"][true] - d["tA"][true], 600.0 / C, atol=1e-9)
    s = h.sim._S(h.sim._cells())
    assert abs(s["S"] - TSIRELSON) < 5 * s["se"]
    assert not failed(h)


def test_the_world_refuses_what_it_cannot_compute():
    S = MOD.Simulation
    p = VIZ["schema"].resolve("photon_lhv", {"L_A_m": 100.0})[0]
    with pytest.raises(Refusal):
        S.check_params(p)
    with pytest.raises(Refusal):
        S.check_params(VIZ["schema"].resolve(None, {"pair": "spin", "state": "eberhard"})[0])
    with pytest.raises(Refusal):
        S.check_params(VIZ["schema"].resolve(None, {"law": "lhv", "visibility": 0.9})[0])
    with pytest.raises(Refusal):
        S.check_params(VIZ["schema"].resolve("detectors", {"law": "lhv"})[0])
    with pytest.raises(Refusal):
        S.check_params(VIZ["schema"].resolve("detectors", {"slot_ns": 30.0})[0])  # (t_d + 5σ)/T_s > 0.1


# --- the counting by slots --------------------------------------------------------------------------------------
def test_the_counting_by_slots_matches_the_engines_prediction_and_shows_slots_in_time():
    h = run("giustina")
    j = h.sim._J()
    assert j["trials"] == pytest.approx(1e9, abs=2)
    assert abs(j["J"] - j["Jexp"]) < 5 * j["se"]
    # [error in earlier] with the SPCM-NIR's dark counts over 1 µs slots J stays below 0 even at Giustina's
    # efficiencies (the design's way 14 holds without dark counts)
    assert j["Jexp"] < 0
    shown = [b["slots"] for m, b in h.msgs if m.get("type") == "slots"]
    assert len(shown) == 10 and all(s.shape == (40, 6) for s in shown)
    assert not failed(h)
    h0 = run("giustina", dark_rate=0.0)
    j0 = h0.sim._J()
    assert j0["Jexp"] > 0 and j0["J"] / j0["se"] > 5  # Giustina's state and efficiencies without background


def test_the_counting_by_slots_has_an_independent_check_and_says_which_rows_test_only_the_sampling(monkeypatch):
    """Review R2-W F2: the counts of the counting by slots are drawn from the engine's slot probabilities and
    coincidence rates, so E, S, J, CH, … against them test the bookkeeping (their group says so); the slots simulated
    in time (``photodetector.pair_slots``) against ``Law.slot_table`` are its independent check. A slot table that is
    wrong (here: η 10 % too low) leaves every sampled row ✓ and fails the independent one (its power on the 10⁶ slots
    simulated in time: χ² ≈ 180 for 32 degrees of freedom at 10 %, ≈ 65 at 5 %, which it does not resolve)."""
    h = run("detectors")
    ch = h.checks()
    t = ch["timed"]
    assert t["ok"] is True and t["value"] is not None and render(t["group"]).startswith("Counting by slots: the slots")
    n = sum(int(v.sum()) for v in h.sim.store.timed.values())
    assert n == 10 * EXP.Slots.N_TIME
    sampled = {k for k, c in ch.items() if render(c["group"]).startswith("Counting by slots: the counts drawn")}
    assert {"E0", "E1", "E2", "E3", "S", "tsir", "S_sub", "acc", "J", "CH", "curve", "nsA0", "nsB0"} <= sampled
    assert "J_bound" not in sampled and "timed" not in sampled
    # a stream world keeps its groups and has no such row
    hs = run("photon_chsh", 0.2)
    assert "timed" not in hs.checks()
    assert not any(render(c["group"]).startswith("Counting by slots") for c in hs.checks().values())
    # the slot table made wrong: the sampled rows cannot see it, the slots simulated in time do
    real = EXP.Law.slot_table

    def wrong(self, a, b, eta_a, eta_b, pd_a, pd_b, mu):
        return real(self, a, b, 0.9 * eta_a, 0.9 * eta_b, pd_a, pd_b, mu)
    monkeypatch.setattr(EXP.Law, "slot_table", wrong)
    hw = run("detectors")
    cw = hw.checks()
    assert cw["timed"]["ok"] is False
    assert all(cw[k].get("ok") is not False for k in sampled)


def test_the_j_curve_of_the_header_crosses_zero_at_the_threshold():
    h = Harness(V, "detectors", {"dark_rate": 0.0})
    hb = [b for m, b in h.msgs if m.get("type") == "header"][0]
    e, j = np.asarray(hb["je"]), np.asarray(hb["jq"])
    k = int(np.argmax(j > 0))
    assert e[k - 1] < 2 / (1 + math.sqrt(2)) + 0.005 and e[k] > 2 / (1 + math.sqrt(2)) - 0.005
    assert j[-1] == pytest.approx((math.sqrt(2) - 1) / 2, abs=0.005)
    # the view marks where this curve crosses 0 (review R2-W F9): the threshold of |Φ+⟩ at the CHSH angles at μ = 0.01
    hd = [m for m, b in h.msgs if m.get("type") == "header"][0]
    assert hd["j_threshold"] == pytest.approx(MOD.THRESHOLDS[("max", -1.0, 0.0)], abs=1e-6)
    # with the SPCM-NIR's dark counts: 87.6 %; Eberhard's state at Giustina's angles 90.55 %, above the 90.23 % of the
    # best angles; with 10⁵ background counts per second it never crosses
    th = {k: [m for m, b in Harness(V, p, q).msgs if m.get("type") == "header"][0]["j_threshold"]
          for k, p, q in (("phi", "detectors", None), ("eb", "giustina", {"eta_A": 0.8, "eta_B": 0.8}),
                          ("bright", "detectors", {"bg_rate": 1e5}))}
    assert th["phi"] == pytest.approx(0.87622, abs=2e-5) and th["eb"] == pytest.approx(0.90554, abs=2e-5)
    assert th["eb"] > MOD.THRESHOLDS[("eberhard", -2.9, 250.0)] and th["bright"] is None
    assert [m for m, b in Harness(V, "photon_chsh").msgs if m.get("type") == "header"][0]["j_threshold"] is None


# --- live changes --------------------------------------------------------------------------------------------
def test_live_angle_change_applies_at_once():
    h = Harness(V, "scan")
    h.run_to(0.2)
    t1 = h.sim.t
    h.set(b_deg=30.0)
    assert h.sim.params["b_deg"] == 30.0 and h.sim.counter.t_set["B"][0] == t1
    assert h.of("live")[-1]["values"]["b_deg"] == 30.0
    for k in range(1, 6):
        h.run_to(t1 + 0.1 * k)
    before = coincs(h)
    before = {k: v[before["tB"] <= t1] for k, v in before.items()}
    after = coincs(h, since=t1 + 1e-5)
    assert np.all(before["alB"] == 0.0) and len(before["alB"])
    assert np.all(after["alB"] == 30.0) and np.all(after["alA"] == 0.0) and len(after["alB"])
    c = h.sim._cells()[0]
    assert c["N"] > 1500 and c["E"] == pytest.approx(math.cos(math.radians(60)), abs=5 * c["se"])
    assert sorted(np.round(h.sim._points()[:, 0], 9)) == [-30.0, 0.0]  # both angle pairs stay on E(Δ)


def test_a_refused_change_leaves_the_world_as_it_was():
    h = run("photon_chsh", 0.05)
    before = dict(h.sim.params)
    h.set(rate=-5.0)
    assert h.sim.params == before and h.errors()
    assert h.of("live")[-1]["values"]["rate"] == before["rate"]


def test_switching_the_mode_fixes_the_settings_and_back():
    h = run("photon_chsh", 0.05)
    h.set(switch="fixed")
    t1 = h.sim.t
    for k in range(1, 4):
        h.run_to(t1 + 0.02 * k)
    d = coincs(h, since=t1 + 2e-6)
    assert len(d["sA"]) and np.all(d["sA"] == 0) and np.all(d["sB"] == 0) and np.allclose(d["tcA"], t1)
    h.set(switch="random")
    t2 = h.sim.t
    for k in range(1, 4):
        h.run_to(t2 + 0.02 * k)
    d = coincs(h, since=t2 + 2e-6)
    assert set(np.unique(d["sA"])) == {0, 1}


def test_clear_resets_the_statistics_but_not_the_set_up():
    h = run("photon_chsh", 0.5)
    h.action("clear")
    assert h.sim.store.coinc == {} and h.sim.seg == 1
    assert h.checks()["S"]["value"] is None
    h.run_to(h.sim.t + 0.5)
    assert h.checks()["S"]["value"] is not None


def test_the_window_share_after_a_reset_counts_both_from_the_reset():
    """Review R2-W F7: the window's share compares the true coincidences of the segment with the pairs detected at both
    sides in the same segment; with the lifetime count of the latter it fell after «Reset the statistics» (here to
    about a third: two segments before, one after) and failed."""
    h = run("photon_chsh", 1.0)
    both_before = h.sim.counter.counts["both"]
    h.action("clear")
    for k in range(1, 6):
        h.run_to(h.sim.t + 0.1)
    w = h.checks()["window"]
    both_seg = h.sim.counter.counts["both"] - both_before
    assert both_seg > 1000 and w["value"] == pytest.approx(h.sim.seg_counts["true"] / both_seg, rel=1e-12)
    share = PD.window_share(h.sim._si()["w"], h.sim._si()["sigma"], h.sim._si()["sigma"])
    assert w["ok"] is True and w["ref"] == pytest.approx(share, rel=1e-12)
    assert not failed(h)


def test_new_world_with_another_law_inside_the_same_run():
    h = run("photon_chsh", 0.1)
    h.cmd("new_world", preset="photon_lhv")
    assert len(h.of("header")) == 2 and h.sim.law.law == "lhv"
    assert h.of("header")[1]["modifications"][0]["id"] == "law"


def test_frames_carry_the_state_the_view_draws():
    h = run("photon_chsh", 0.2)
    meta, blobs = h.sim.frame()
    assert set(meta) >= {"settings", "flight", "counts", "cells", "S", "S_law", "J", "meas", "now_slots"}
    assert blobs["slots"].shape[1] == 4 and blobs["pts"].shape[1] == 5
    hdr = h.of("header")[0]
    _, hb = [x for x in h.msgs if x[0].get("type") == "header"][0]
    assert len(hb["cd"]) == len(hb["cq"]) == len(hb["ch"]) == 361 and len(hb["sd"]) == len(hb["sq"]) == 181
    assert hb["cq"][180] == pytest.approx(1.0) and hb["ch"][180] == pytest.approx(0.5)
    assert hb["sq"][45] == pytest.approx(TSIRELSON)  # Δ = 22.5°
    assert hdr["period"] == 180.0 and {m["id"] for m in hdr["measurables"]} >= {"S", "J", "n_pp", "local_frac"}
    # every counter's measurable is a whole number ≥ 0 or None in every frame (EX2 §5 F4)
    for f in [m for m, _b in h.msgs if m.get("type") == "frame"]:
        for k in ("n_pp", "n_pm", "n_mp", "n_mm", "coinc"):
            v = f["meas"][k]
            assert v is None or (isinstance(v, int) and v >= 0)


# --- the reviews' regressions -----------------------------------------------------------------------------------
@pytest.mark.parametrize("pair,a,b,E", [("photon", 30.0, 30.0, 1.0), ("photon", 30.0, 120.0, -1.0),
                                        ("spin", 30.0, 30.0, -1.0), ("spin", 50.0, 230.0, 1.0)])
def test_perfectly_correlated_settings_run(pair, a, b, E):
    """V7-1: an exactly-zero joint Born probability came out as -1e-17 and Generator.choice raised in advance. With
    real detectors a rare accidental coincidence may land in the other cells."""
    h = Harness(V, None, {"pair": pair, "switch": "fixed", "a_deg": a, "b_deg": b})
    for k in range(1, 6):
        h.run_to(0.1 * k)
    assert not h.errors()
    c = h.sim._cells()[0]
    assert c["N"] > 1500 and abs(c["E"] - E) < 0.005
    assert h.checks()["E0"]["ok"] is True


@pytest.mark.parametrize("a,a2,b,b2", [(0.0, 0.0, 45.0, 0.0), (0.0, 0.0, 0.0, 45.0), (0.0, 45.0, 22.5, 22.5)])
def test_coinciding_settings_get_the_right_error_of_S(a, a2, b, b2):
    """V7-2: with a' = a (or b' = b) two CHSH cells are the same pairs; the error of S must count them once."""
    S, se = [], []
    for seed in range(30):
        h = Harness(V, "photon_chsh", {"a_deg": a, "a2_deg": a2, "b_deg": b, "b2_deg": b2}, seed=seed)
        h.run_to(0.5)
        s = h.sim._S(h.sim._cells())
        S.append(s["S"])
        se.append(s["se"])
        assert "the settings coincide" in render(h.checks()["S"]["note"])  # flagged: S is not a CHSH test here
    S, se = np.array(S), np.array(se)
    if np.all(se < 0.01):  # S = 2 E(0, 0) ≈ 2 in every run (up to a rare accidental): no spread to compare
        assert np.all(np.abs(S - 2.0) < 0.01)
        return
    ratio = S.std(ddof=1) / se.mean()
    assert 0.7 < ratio < 1.35, ratio  # the SD of 30 values is known to about 13 %


def test_local_identities_are_shown_as_information():
    """V7-3: in local worlds the law's no-signalling and |S| ≤ 2√2 are identities, shown for information."""
    h = Harness(V, "photon_lhv")
    ch = h.checks()
    for cid in ("nosig_law", "tsir_law"):
        assert ch[cid].get("info") is True and "ok" not in ch[cid], ch[cid]
    assert ch["chsh_law"]["ok"] is True and not ch["chsh_law"].get("info")
    hq = Harness(V, "photon_chsh")
    assert hq.checks()["nosig_law"]["ok"] is True and hq.checks()["tsir_law"]["ok"] is True


def test_reversal_speed_reference_at_extreme_settings():
    """Review UX-params P21: the reference of v* (bisection on the Lorentz matrices) acts on the separation, so it
    keeps 1e-9 at a lead of 10 ns over 2·10⁵ m (the old route, boosting the events apart, did not)."""
    from u37_bell_test.viz import _reversal_by_boosts
    h = Harness(V, None, {"switch": "random", "tau_ns": 0.001, "slot_ns": 10.0, "dead_ns": 0.0, "L_A_m": 1e5,
                          "L_B_m": 1e5})
    c = h.checks()["st_rev"]
    assert c["ref"] is not None and abs(c["rel"]) <= 1e-9
    tarr, L, lead = 1e5 / C, 1e5, 10.001e-9
    e1, e2 = (tarr - lead, -L), (tarr, L)
    assert abs(_reversal_by_boosts(e1, e2) / (C * lead / (2 * L)) - 1) <= 1e-12
