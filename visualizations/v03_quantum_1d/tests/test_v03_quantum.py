# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v03: the run's wave, its detectors and the three readings of the outcome."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from v03_quantum_1d.viz import FS, SCHEMA  # noqa: E402

V = "v03_quantum_1d"


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_run_and_checks_agree(preset):
    h = Harness(V, preset)
    h.run_to(h.sim.cycle * FS * 30)
    assert not h.errors()
    bad = [c["id"] for c in h.checks().values() if c.get("ok") is False
           or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"])]
    assert not bad


def test_packet_transmission_equals_the_stationary_reference():
    h = Harness(V, "tunnel")
    c = h.checks()["T0"]
    assert c["ok"] and abs(c["value"] - c["ref"]) < 1e-4


@pytest.mark.parametrize("interp", ["copenhagen", "bohm", "everett"])
def test_three_readings_give_the_same_statistics(interp):
    h = Harness(V, "above", params={"interp": interp}, seed=7)
    h.run_to(h.sim.cycle * FS * 400)
    n = h.sim.counts["left"] + h.sim.counts["right"]
    PR = h.sim.PR[-1] / (h.sim.PL[-1] + h.sim.PR[-1])
    sd = np.sqrt(PR * (1 - PR) / n)
    assert abs(h.sim.counts["right"] / n - PR) < 4 * sd


def test_clicks_are_revealed_only_when_reached():
    h = Harness(V, "tunnel")
    c = h.sim.particle["click"]
    h.run_to(c * 0.999)
    assert not [e for e in h.of("event") if e.get("kind") == "click"]
    h.run_to(c * 1.001)
    assert len([e for e in h.of("event") if e.get("kind") == "click"]) == 1


def test_live_change_rebuilds_and_reading_change_does_not():
    h = Harness(V, "tunnel")
    n_grid = h.sim.n_grid
    h.set(interp="everett")
    assert not h.errors() and h.sim.n_grid == n_grid and h.of("segment")[-1]["interp"] == "everett"
    h.set(width=1.2)
    seg = h.of("segment")[-1]
    assert "изменена установка" in seg["reason"] and h.checks()[f"T{seg['seg']}"]["ok"]


def test_oscillator_levels_and_period():
    h = Harness(V, "oscillator")
    ch = h.checks()
    assert abs(ch["lev0"]["rel"]) < 1e-9 and abs(ch["per0"]["value"] - ch["per0"]["ref"]) < 1e-3


def test_live_message_carries_the_engine_modules_in_force():
    """A live change of the reading brings a theory module in or out: the live message lists the modules in force."""
    h = Harness(V)
    ids = lambda msg: {d["id"] for d in msg["engine"]}  # noqa: E731
    assert "theories.interpretations.everett" not in ids(h.of("header")[-1])
    h.set(interp="everett")
    assert "theories.interpretations.everett" in ids(h.of("live")[-1])
    assert all(d["layer"] for d in h.of("live")[-1]["engine"])


def _checks_ok(h):
    bad = [c["id"] for c in h.checks().values() if c.get("ok") is False
           or (c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"])]
    return not bad, bad


@pytest.mark.parametrize("params", [
    {"scenario": "step", "V0": 0.75, "energy": 0.8},            # V3-1: transmitted wave slow, was T 0.26 vs 0.60
    {"scenario": "barrier", "V0": 1.0, "width": 5.0},           # V3-2: T ~ 1.6e-6, was cut by 55 %
    {"scenario": "free", "energy": 0.05, "sigma": 2.5},         # V3-3: slow packet, full-Gaussian reference
])
def test_review_cases_converge_to_the_stationary_reference(params):
    h = Harness(V, "tunnel", params)
    ok, bad = _checks_ok(h)
    assert ok, bad
    c = h.checks()[f"T{h.sim.seg}"]
    assert abs(c["value"] - c["ref"]) <= 1e-7 + 2e-3 * c["ref"] + h.sim.leftover
    assert h.sim.leftover <= h.sim.leftover_allowed and not h.sim.capped


def test_unreachable_set_ups_are_refused_with_the_reason():
    """V3-3: a packet too wide in momentum; V3-4: a trap needing more than 32768 points (was capped silently)."""
    h = Harness(V, "tunnel")
    n_seg = h.sim.seg
    h.set(energy=0.05, sigma=1.0)
    assert "слишком широк по импульсу" in h.errors()[-1] and h.sim.seg == n_seg
    h.set(scenario="oscillator", hw=1.0, x0=60.0)
    assert "сетка" in h.errors()[-1] and h.sim.params["scenario"] == "barrier"


def test_heavy_trap_is_refused_and_levels_come_from_a_window():
    """V3-4: hw = 0.05 eV, x0 = 60 nm (16384 points, 1.5e5 steps) was OOM-killed by a dense 16384^2 level
    Hamiltonian after minutes; now it is refused with the cost estimate before anything is computed. The levels of
    any trap come from a 256-point window around it."""
    h = Harness(V, "oscillator")
    h.set(x0=60.0)
    assert "слишком дорог" in h.errors()[-1] and h.sim.params["x0"] == 15.0
    assert abs(h.checks()[f"lev{h.sim.seg}"]["rel"]) < 1e-9 and abs(h.checks()[f"lev3{h.sim.seg}"]["rel"]) < 1e-9


# --- review UX-params P13, P19 ---------------------------------------------------------------------------------------
def test_a_step_above_the_energy_runs_to_its_transmission():
    """P13: «Ступенька» from the defaults (E = 0.8 eV below the step V0 = 1 eV): only the fast tail of the packet passes,
    near the threshold and slowly. Before, the run waited for it until its budget (52-88 s) and ended with T 8 % low and
    the absorption check failed. Now the expected time includes the slowest part that carries 1e-3 of T (from the
    stationary reference's transmitted spectrum) and the right detector is chosen for that spectrum: it ends without
    the budget, every check passes and T agrees with the reference to its tolerance. Negative control: the right ramp
    chosen as before, for the incident spectrum, sends 19 % of T back."""
    h = Harness(V, None, {"scenario": "step"})
    assert not h.sim.capped and h.sim.det > 15.0
    assert not h.errors()
    bad = [c["id"] for c in h.checks().values() if c.get("ok") is False]
    assert not bad, [(c["id"], c["value"], c["ref"]) for c in h.checks().values() if c.get("ok") is False]
    c = h.checks()["T0"]
    assert abs(c["value"] - c["ref"]) <= 2e-3 * c["ref"]
    from lfphys.core.quantum import transfer
    from v03_quantum_1d.viz import HBAR
    s_ = h.sim
    ks, T, w = s_._exp[1], s_._exp[2], s_._exp[3]
    on = T > 0
    E = HBAR ** 2 * ks[on] ** 2 / (2 * s_.m) - 1.0
    ok = E > 1e-4
    ramp = lambda xx: np.where(np.asarray(xx) <= 15.0, -2j * np.clip(np.asarray(xx) / 15.0, 0, 1) ** 2, 0.0)  # noqa: E731
    R = np.zeros(on.sum())
    R[ok] = transfer.transmission_profile(E[ok], ramp, 0.0, 15.0, 2000, s_.m, HBAR, return_r=True)[1]
    assert np.sum(w[on] * T[on] * R) / np.sum(w[on] * T[on]) > 0.1  # the 15-nm ramp of before: ~0.19 of T back


def test_sharp_edges_shorten_the_step_where_the_transmission_is_small():
    """P19: a 3 nm barrier (T ~ 1e-5) with edges of delta = 0.02 nm transmitted 8x too much at the phase step's dt
    (the splitting error at an edge is set by hbar^2/(2 m delta^2) = 95 eV, not by the particle's energy); with
    delta = 0.05 nm the edges' step (phi <= 0.25) makes T agree with the stationary reference to 1e-4 of itself; with
    0.02 nm the step needed costs too much for a live world and the world is refused at once with what to change (the
    10 nm barrier of the review alike). Negative control: without the edges' step (T_EDGE = 0) the 0.02 nm world runs
    at the old step and its T fails the check by far."""
    import v03_quantum_1d.viz as M
    h = Harness(V, None, {"width": 3.0, "edge": 0.05})
    c = h.checks()["T0"]
    assert c["ok"] and abs(c["value"] - c["ref"]) <= 1e-4 * c["ref"], (c["value"], c["ref"])
    assert h.sim._dt_max() < h.sim._dt_phase()
    for width in (3.0, 10.0):
        p, _ = SCHEMA.resolve(None, {"width": width, "edge": 0.02})
        with pytest.raises(ValueError, match="края барьера резкие") as e:
            M.Simulation(p, 1, lambda *a, **k: None)
        assert "увеличьте размытие краёв δ" in str(e.value) and "review" not in str(e.value)
    p, _ = SCHEMA.resolve(None, {"width": 3.0, "edge": 0.02})
    old = M.T_EDGE
    try:
        M.T_EDGE = 0.0
        s = M.Simulation(p, 1, lambda *a, **k: None)
    finally:
        M.T_EDGE = old
    T = s.PR[-1] / (s.PL[-1] + s.PR[-1])
    ref = s._expected_T()[0]
    assert T > 3 * ref  # 8x measured


def test_refusals_name_what_this_scenario_can_change():
    """P19: the cost refusal advised «ширину пакета, энергию или высоту потенциала» also in the trap, where only ħω and x0
    are shown; the momentum refusal ended with «(review V3-3)»."""
    p, _ = SCHEMA.resolve(None, {"scenario": "oscillator", "hw": 1.0, "x0": 60.0})
    import v03_quantum_1d.viz as M
    with pytest.raises(ValueError) as e:
        M.Simulation(p, 1, lambda *a, **k: None)
    assert ("ħω" in str(e.value) or "x₀" in str(e.value)) and "ширину пакета" not in str(e.value)
    p, _ = SCHEMA.resolve(None, {"energy": 0.05, "sigma": 1.0})
    with pytest.raises(ValueError) as e:
        M.Simulation(p, 1, lambda *a, **k: None)
    assert "review" not in str(e.value)
