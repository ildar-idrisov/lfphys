# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u37 Bell test: every preset, the statistics against the laws, no-signalling, causality, live changes."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.constants import C  # noqa: E402
from lfphys.i18n import render  # noqa: E402
from lfviz import registry  # noqa: E402

V = "u37_bell_test"
PRESETS = list(registry.load(V)["schema"].presets)
TSIRELSON = 2 * math.sqrt(2)


def run(preset, n_pairs=20000, seed=1, **params):
    h = Harness(V, preset, params or None, seed=seed)
    h.run_to(n_pairs / h.params["rate"])
    return h


def details(h, since=-1.0):
    """Per-pair detail of the 'pairs' messages (with the time of the message that revealed them)."""
    out = {}
    for m, b in h.msgs:
        if m.get("type") != "pairs" or m["t"] <= since:
            continue
        b = dict(b)
        b["msg_t"] = np.full(len(b["t"]), m["t"])
        for k, v in b.items():
            out.setdefault(k, []).append(np.asarray(v))
    return {k: np.concatenate(v) for k, v in out.items()}


# --- every preset -------------------------------------------------------------------------------------------
@pytest.mark.parametrize("preset", PRESETS)
def test_every_preset_runs_and_no_check_fails(preset):
    h = run(preset)
    assert not h.errors()
    assert h.sim.counts["detected"] > 15000
    checks = h.checks()
    bad = {k: (c["value"], c["ref"], c["note"]) for k, c in checks.items() if c.get("ok") is False}
    assert not bad
    for c in checks.values():  # the player's own verdict for checks without an explicit ok (info: no verdict)
        if "ok" not in c and not c.get("info") and c["ref"] is not None and c["rel"] is not None:
            assert abs(c["rel"]) <= max(c["tol"], 1e-12), c
    assert h.of("header")[0]["title"]["$t"] == "Bell test: {law}"


# --- the laws -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("preset", ["photon_chsh", "spin_chsh"])
def test_quantum_worlds_reach_tsirelson_and_violate_chsh_by_many_sigma(preset):
    h = run(preset, 40000)
    s = h.sim._S(h.sim._cells())
    assert abs(abs(s["S"]) - TSIRELSON) < 5 * s["se"]
    assert (abs(s["S"]) - 2) / s["se"] > 15
    assert h.checks()["bound"]["ok"] is True
    assert any(render(e["text"]).startswith("Violation of the CHSH inequality") for e in h.of("event"))
    assert h.of("header")[0]["modifications"] == []


@pytest.mark.parametrize("preset,S_exact", [("photon_lhv", math.sqrt(2)), ("spin_lhv", 2.0)])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_local_hidden_variables_never_exceed_two(preset, S_exact, seed):
    h = run(preset, 40000, seed=seed)
    s = h.sim._S(h.sim._cells())
    assert abs(s["S"]) <= 2 + 5 * s["se"]
    assert abs(abs(s["S"]) - S_exact) < 5 * s["se"]  # the model's own expectation (sign model saturates 2)
    assert h.checks()["bound"]["ok"] is True
    mods = h.of("header")[0]["modifications"]
    assert [m["id"] for m in mods] == ["law"]
    assert any(e["id"] == "theories.alternatives.local_hidden" for e in h.of("header")[0]["engine"])


def test_engine_modules_of_a_quantum_world_are_core_and_tools():
    h = Harness(V, "photon_chsh")
    layers = {e["id"]: e["layer"] for e in h.of("header")[0]["engine"]}
    assert layers["core.quantum.qubits"] == "core" and layers["core.causality"] == "core"
    assert "theories.alternatives.local_hidden" not in layers


def test_no_signalling_from_the_run_counts():
    h = run("photon_chsh", 40000)
    ch = h.checks()
    for cid in ("nsA0", "nsA1", "nsB0", "nsB1"):
        assert ch[cid]["ok"] is True and abs(ch[cid]["value"]) < 0.05
    assert ch["nosig_law"]["ok"] is True and ch["nosig_law"]["value"] < 1e-14


def test_sampled_correlations_match_the_closed_forms_at_many_angles():
    """The wrapper's outcome mapping (index 0 -> +1) and angle conventions against textbook closed forms."""
    from u37_bell_test.engine.experiment import Law
    rng = np.random.default_rng(5)
    forms = {("photon", "quantum"): lambda d: math.cos(2 * d), ("spin", "quantum"): lambda d: -math.cos(d),
             ("photon", "lhv"): lambda d: 0.5 * math.cos(2 * d),
             ("spin", "lhv"): lambda d: -1 + 2 * abs((d + math.pi) % (2 * math.pi) - math.pi) / math.pi}
    n = 40000
    for (pair, law), f in forms.items():
        L = Law(pair, law)
        for a, b in rng.uniform(-180, 180, (6, 2)):
            A, B = L.sample(a, b, n, rng)
            ref = f(math.radians(a - b))
            assert L.E(a, b) == pytest.approx(ref, abs=1e-12)
            assert np.mean(A * B) == pytest.approx(ref, abs=5 * math.sqrt((1 - ref**2) / n) + 1e-9)
            assert abs(np.mean(A)) < 5 / math.sqrt(n)  # unbiased marginals


# --- causality and the live set-up --------------------------------------------------------------------------
def test_outcomes_are_revealed_only_when_the_particles_arrive():
    h = run("photon_chsh", 5000)
    d = details(h)
    L = h.params["L_m"]
    assert np.all(d["t"] <= d["msg_t"])  # never shown before the arrival
    assert np.allclose(d["t"] - d["te"], L / C, rtol=1e-9, atol=1e-15)  # arrival = emission + L/c
    assert np.all(d["tcA"] < d["t"]) and np.all(d["tcB"] < d["t"])  # the choice precedes the detection
    assert np.allclose(d["t"] - d["tcA"], h.params["tau_ns"] * 1e-9, rtol=1e-6)
    first = [e for e in h.of("event") if e.get("kind") == "detection"][0]
    assert first["t"] >= L / C


def test_random_choice_is_space_like_and_a_slow_choice_is_not():
    h = run("photon_chsh", 5000)
    fl = details(h)["fl"]
    assert np.all(fl & 3 == 3)  # both choices outside the light cone of the other side's detection
    h2 = run("photon_slow_choice", 5000)
    fl2 = details(h2)["fl"]
    assert np.all(fl2 & 3 == 0)
    assert "OPEN" in render(h2.checks()["st_loc"]["label"]) and "closed" in render(h.checks()["st_loc"]["label"])


def test_fixed_settings_become_time_like_as_they_age():
    h = Harness(V, "scan")
    assert "space-like" in render(h.checks()["st_loc"]["label"])  # set at t = 0: the next pair is outside
    h.run_to(5000 / h.params["rate"])
    assert "OPEN" in render(h.checks()["st_loc"]["label"])  # known long before: inside the light cone
    fl = details(h)["fl"]
    late = details(h)["t"] > 4 * h.params["L_m"] / C
    assert np.all(fl[late] & 3 == 0)


@pytest.mark.parametrize("L,tau_ns", [(500.0, 100.0), (2.0, 5.0), (1e4, 5e4), (30.0, 300.0)])
def test_space_time_checks_against_closed_forms(L, tau_ns):
    h = Harness(V, "photon_chsh", {"L_m": L, "tau_ns": tau_ns})
    ch = h.checks()
    tau = tau_ns * 1e-9
    assert ch["st_loc"]["value"] == pytest.approx((C * tau) ** 2 - 4 * L * L, rel=1e-9)
    if C * tau < 2 * L:
        assert ch["st_rev"]["value"] == pytest.approx(C * tau / (2 * L), rel=1e-12)
        assert ch["st_rev"]["ref"] == pytest.approx(C * tau / (2 * L), rel=1e-9)
    else:
        assert ch["st_rev"]["value"] is None


def test_live_angle_change_applies_at_once():
    h = run("scan", 3000)
    t1 = h.sim.t
    h.set(b_deg=30.0)
    assert h.sim.params["b_deg"] == 30.0 and h.sim.t_set["B"][0] == t1
    assert h.of("live")[-1]["values"]["b_deg"] == 30.0
    h.run_to(t1 + 20000 / h.params["rate"])
    before = details(h)
    before = {k: v[before["t"] <= t1] for k, v in before.items()}
    after = details(h, since=t1)
    assert np.all(before["alB"] == 0.0) and len(before["alB"])
    assert np.all(after["alB"] == 30.0) and np.all(after["alA"] == 0.0) and len(after["alB"])
    E, se, N = h.sim._cells()[0]["E"], h.sim._cells()[0]["se"], h.sim._cells()[0]["N"]
    assert N > 15000 and E == pytest.approx(math.cos(math.radians(60)), abs=5 * se)
    # both angle pairs remain on the E(delta) plot
    pts = h.sim._points()
    assert sorted(np.round(pts[:, 0], 9)) == [-30.0, 0.0]


def test_a_refused_change_leaves_the_world_as_it_was():
    h = run("photon_chsh", 1000)
    before = dict(h.sim.params)
    h.set(rate=-5.0)
    assert h.sim.params == before and h.errors()
    assert h.of("live")[-1]["values"]["rate"] == before["rate"]


def test_moving_the_stations_loses_overtaken_pairs_and_delays_the_others():
    h = Harness(V, "photon_chsh", {"rate": 2e7})  # about 33 pairs in flight
    h.run_to(5e-5)
    t1 = h.sim.t
    p = h.sim.exp.p
    r = C * (t1 - p["te"])
    expect_lost = int(np.sum(r > 100.0))
    assert expect_lost > 0
    h.set(L_m=100.0)
    assert h.sim.counts["lost"] == expect_lost
    assert any(render(n["text"]).startswith(f"The stations were moved: pairs in flight lost: {expect_lost} ")
               for n in h.of("notice"))
    h.run_to(t1 + 2e-6)
    d = details(h, since=t1)
    assert len(d["t"]) and np.allclose(d["t"] - d["te"], 100.0 / C, rtol=1e-9)
    assert np.all(d["L"] == 100.0)


def test_switching_the_mode_reschedules_the_choices():
    h = Harness(V, "photon_chsh", {"rate": 2e7})
    h.run_to(3e-5)
    h.set(switch="fixed")
    t1 = h.sim.t
    h.run_to(t1 + 1e-5)
    d = details(h, since=t1)
    assert np.all(d["sA"] == 0) and np.all(d["sB"] == 0) and np.all(d["tcA"] == t1)
    h.set(switch="random")
    t2 = h.sim.t
    h.run_to(t2 + 1e-5)
    d = details(h, since=t2)
    assert set(np.unique(d["sA"])) == {0, 1}
    assert np.all(d["tcA"] >= t2)  # no choice is placed before the switch that made it possible


def test_clear_resets_the_statistics_but_not_the_set_up():
    h = run("photon_chsh", 5000)
    n_flight = h.sim.exp.n_flight
    h.action("clear")
    assert h.sim.store.cells == {} and h.sim.exp.n_flight == n_flight
    assert h.checks()["S"]["value"] is None
    h.run_to(h.sim.t + 5000 / h.params["rate"])
    assert h.checks()["S"]["value"] is not None


def test_new_world_with_another_law_inside_the_same_run():
    h = run("photon_chsh", 2000)
    h.cmd("new_world", preset="photon_lhv")
    assert len(h.of("header")) == 2 and h.sim.law.law == "lhv"
    assert h.of("header")[1]["modifications"][0]["id"] == "law"


def test_frames_carry_the_state_the_view_draws():
    h = run("photon_chsh", 3000)
    meta, blobs = h.sim.frame()
    assert set(meta) >= {"settings", "flight", "counts", "cells", "S", "S_law"}
    assert blobs["flight"].shape[1] == 6 and blobs["pts"].shape[1] == 5
    hdr = h.of("header")[0]
    _, hb = [x for x in h.msgs if x[0].get("type") == "header"][0]
    assert len(hb["cd"]) == len(hb["cq"]) == len(hb["ch"]) == 361
    assert hb["cq"][180] == pytest.approx(1.0) and hb["ch"][180] == pytest.approx(0.5)
    assert hdr["period"] == 180.0


# --- review 2026-10-23 ------------------------------------------------------------------------------------------
@pytest.mark.parametrize("pair,a,b,E", [("photon", 30.0, 30.0, 1.0), ("photon", 30.0, 120.0, -1.0),
                                        ("spin", 30.0, 30.0, -1.0), ("spin", 50.0, 230.0, 1.0)])
def test_perfectly_correlated_settings_run(pair, a, b, E):
    """V7-1: an exactly-zero joint Born probability came out as -1e-17 and Generator.choice raised in advance."""
    h = Harness(V, None, {"pair": pair, "switch": "fixed", "a_deg": a, "b_deg": b})
    h.run_to(h.sim._flight() + 3000 / h.params["rate"])
    assert not h.errors()
    c = h.sim._cells()[0]
    assert c["N"] > 2000 and c["E"] == E  # every pair perfectly (anti)correlated
    assert h.checks()["E0"]["ok"] is True


@pytest.mark.parametrize("a,a2,b,b2", [(0.0, 0.0, 45.0, 0.0), (0.0, 0.0, 0.0, 45.0), (0.0, 45.0, 22.5, 22.5)])
def test_coinciding_settings_get_the_right_error_of_S(a, a2, b, b2):
    """V7-2: with a' = a (or b' = b) two CHSH cells are the same pairs; the error of S must count them once
    (reviewer: empirical SD 0.049 against a reported 0.032 at a = a' = 0, b = 45, b' = 0)."""
    S, se = [], []
    for seed in range(40):
        h = Harness(V, "photon_chsh", {"a_deg": a, "a2_deg": a2, "b_deg": b, "b2_deg": b2}, seed=seed)
        h.run_to(h.sim._flight() + 4000 / h.sim.params["rate"])
        s = h.sim._S(h.sim._cells())
        S.append(s["S"])
        se.append(s["se"])
        assert "the settings coincide" in render(h.checks()["S"]["note"])  # flagged: S is not a CHSH test here
    S, se = np.array(S), np.array(se)
    if np.all(se == 0):  # S = 2 E(0, 0) = 2 exactly in every run: no spread, no error
        assert np.all(S == 2.0)
        return
    ratio = S.std(ddof=1) / se.mean()
    assert 0.75 < ratio < 1.3, ratio  # the SD of 40 values is known to about 11 %


def test_lhv_identities_are_shown_as_information():
    """V7-3: in LHV worlds the law's no-signalling (P(+) = 1/2 by construction) and |S| <= 2 sqrt 2 (implied by the
    CHSH bound) are identities, shown for information, not as checks."""
    h = Harness(V, "photon_lhv")
    ch = h.checks()
    for cid in ("nosig_law", "tsir_law"):
        assert ch[cid].get("info") is True and "ok" not in ch[cid], ch[cid]
    assert ch["chsh_law"]["ok"] is True and not ch["chsh_law"].get("info")
    hq = Harness(V, "photon_chsh")  # in a quantum world both are computed from the engine's trace: real checks
    assert hq.checks()["nosig_law"]["ok"] is True and hq.checks()["tsir_law"]["ok"] is True


def test_reversal_speed_reference_at_extreme_settings():
    """Review UX-params P21: at τ = 0.001 ns and L = 1e5 m the reference of v* (bisection on the Lorentz matrices)
    boosted the two events apart and subtracted terms ~L, losing ~eps L/(c τ) of the root: 1.2e-8 against the 1e-9
    tolerance, a failed check on a correct world. Now the matrices act on the separation: the check passes at 1e-9.
    Negative control: the old route (events boosted apart) misses by more than the tolerance at these settings."""
    import math as _m
    import numpy as _np
    from lfphys.core import relativity as R
    from lfphys.core.constants import C
    from u37_bell_test.viz import _reversal_by_boosts
    h = Harness("u37_bell_test", None, {"switch": "random", "tau_ns": 0.001, "L_m": 1e5})
    c = h.checks()["st_rev"]
    assert c["ref"] is not None and abs(c["rel"]) <= 1e-9

    def old(e1, e2):
        def dt_prime(beta):
            M = R.boost_matrix(_np.array([beta * C, 0.0]), C)
            a = M @ _np.array([C * e1[0], e1[1], 0.0])
            b = M @ _np.array([C * e2[0], e2[1], 0.0])
            return (b[0] - a[0]) / C
        lo, hi = 0.0, 1.0 - 1e-15
        s0 = _m.copysign(1.0, dt_prime(lo))
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if _m.copysign(1.0, dt_prime(mid)) == s0 else (lo, mid)
        return 0.5 * (lo + hi)
    tarr, L, tau = 1e5 / C, 1e5, 1e-12
    e1, e2 = (tarr - tau, -L), (tarr, L)
    new = _reversal_by_boosts(e1, e2)
    closed = C * (e2[0] - e1[0]) / (2 * L)
    assert abs(new / closed - 1) <= 1e-12
    assert abs(old(e1, e2) / closed - 1) > 1e-9
