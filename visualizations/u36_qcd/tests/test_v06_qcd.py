# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""v06: the running coupling and the quarkonium model, through the run."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.i18n import render  # noqa: E402
from v06_qcd.viz import SCHEMA  # noqa: E402

V = "v06_qcd"


@pytest.mark.parametrize("preset", [p for p in SCHEMA.presets if p != "strong"])
def test_presets_run_and_checks_agree(preset):
    h = Harness(V, preset)
    h.run_to(3.0)
    assert not h.errors()
    bad = [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False
           or (c.get("ok") is None and c.get("rel") is not None and c.get("ref") is not None and abs(c["rel"]) > c["tol"]))]
    assert not bad
    # the model-vs-core comparison is informational (review V6-2): never painted as a failure
    assert all(c.get("info") for c in h.checks().values() if c["id"].startswith("kap"))


def test_strong_coupling_world_breaks_perturbation_theory():
    """alpha_s(M_Z) = 0.15 (a declared modification): the Landau pole rises to ~1.7 GeV and the loop expansion at
    2 GeV no longer converges - the run reports it as a failed convergence check and a notice."""
    h = Harness(V, "strong")
    assert h.checks()["conv0"]["ok"] is False
    assert any("Landau pole" in render(m["text"]) for m in h.of("notice"))


def test_probe_sweeps_and_alpha_falls():
    h = Harness(V, "standard")
    a1 = h.sim.frame()[0]["alpha"]
    h.run_to(1.0)  # half a decade up
    a2 = h.sim.frame()[0]["alpha"]
    assert a2 < a1


def test_modified_coupling_is_flagged_and_live_change_recomputes():
    h = Harness(V, "strong")
    assert h.of("header")[0]["modifications"]
    h.set(system="bottom")
    seg = h.of("segment")[-1]
    assert seg["system"] == "bottom" and seg["mq"] == pytest.approx(5.18)
    h.set(alpha_mz=0.11)  # a world parameter: refused while the world runs, named by its label
    assert h.errors() and "α_s(M_Z)" in render(h.errors()[-1]) and h.sim.params["alpha_mz"] == 0.15


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and c.get("ref") is not None and abs(c["rel"]) > c["tol"]))]


@pytest.mark.parametrize("a_mz", [0.205, 0.25, 0.3])
def test_large_coupling_worlds_are_built(a_mz):
    """Review V6-1: alpha_s(M_Z) >= 0.205 put the Landau pole above 2 GeV and the one-loop check killed the world."""
    h = Harness(V, "standard", {"alpha_mz": a_mz})
    assert not h.errors()
    one2 = h.checks()["one0_2"]
    assert one2.get("info") and "Landau pole" in render(one2["note"])
    assert h.checks()["one0_1000"]["rel"] is not None and abs(h.checks()["one0_1000"]["rel"]) < 1e-10


@pytest.mark.parametrize("loops", [1, 2, 3, 4])
def test_threshold_jump_is_the_decoupling_relation(loops):
    """Review V6-3: the threshold check compares the jump with the decoupling relation of loops - 1 loops (a jump at
    3 and 4 loops, continuity at 1 and 2), not a continuity that holds by construction."""
    h = Harness(V, "standard")
    h.set(loops=loops)
    pre = f"thr{h.sim.seg}"
    ch = {k[len(pre):]: c for k, c in h.checks().items() if k.startswith(pre)}
    assert set(ch) == {"c", "b", "t"}
    for q, c in ch.items():
        assert abs(c["rel"]) < c["tol"]
    jump_c = ch["c"]["note"]["a"]["jump"]
    assert (jump_c > 1e-3) == (loops >= 3)


def test_sweep_speed_change_keeps_the_probe_where_it_is():
    """Review V6-4: a new speed continues from the current scale (the probe used to jump back to mu)."""
    h = Harness(V, "standard")
    h.run_to(3.0)
    mu_before = h.sim.mu_now()
    assert mu_before > 100.0
    h.set(sweep=0.6)
    assert h.sim.mu_now() == pytest.approx(mu_before, rel=1e-12)
    h.run_to(4.0)
    assert h.sim.mu_now() == pytest.approx(mu_before * 10 ** 0.6, rel=1e-9)
    h.set(mu=20.0)
    assert h.sim.mu_now() == pytest.approx(20.0, rel=1e-12)


def test_light_quark_is_refused_and_the_box_grows():
    """Review V6-5: below 1 GeV the heavy-quark model is refused with the reason; a weak string with m_q = 1 GeV
    gets a box large enough (the levels used to be box levels)."""
    h = Harness(V, "standard")
    h.set(m_q=0.3)
    assert h.errors() and "heavy quarks" in render(h.errors()[-1]) and h.sim.params["m_q"] == 0.0
    n_seg, n_err = h.sim.seg, len(h.errors())
    h.set(m_q=1.0, kappa=0.0, a_conf=5.0)
    assert len(h.errors()) == n_err and h.sim.seg == n_seg + 1
    assert not failed(h) or all(i.startswith("lev") for i in failed(h))  # the model may miss PDG, nothing else


def test_coupling_with_its_pole_at_a_threshold_builds():
    """Review UX-params P5: alpha_s(M_Z) = 0.19 (4 loops) was refused with the raw «RG integration failed» (the
    matching at m_b pushed the coupling past the pole bound). Now the world is built, its curve ends at the pole near
    m_b (NaN below it), and no failure text reaches the user. Negative control: the world average draws the whole
    curve."""
    import math
    h = Harness(V, params={"alpha_mz": 0.19})
    assert not h.errors()
    seg = h.of("segment")[-1]
    assert seg["alpha_mz"] == 0.19
    st = h.sim.state
    below = st["curves"]["L4"][st["mus"] < 4.18]
    above = st["curves"]["L4"][st["mus"] > 4.19]
    assert below.size and all(math.isnan(x) for x in below)
    assert above.size and all(math.isfinite(x) for x in above)
    h0 = Harness(V, "standard")
    assert all(math.isfinite(x) for x in h0.sim.state["curves"]["L4"])


def test_honest_failures_are_marked_expected():
    """Review UX-params P23: a «what if» coupling fails the convergence check by design, and a model with other
    parameters than the fit fails the PDG levels: such failures carry `expected` (the player draws them apart); the
    standard world's checks carry none (negative control)."""
    h = Harness(V, "strong")
    c = h.checks()["conv0"]
    assert c["ok"] is False and "is changed" in render(c["expected"])
    assert "does not converge" in str(SCHEMA.presets["strong"]["note"])
    h = Harness(V, "standard")
    h.set(kappa=0.0)
    assert any(c.get("expected") for k, c in h.checks().items() if k.startswith("lev1_") and c.get("ok") is False)
    assert not any(c.get("expected") for c in Harness(V, "standard").checks().values())


# --- the engine's refusals matched by their machine codes (review 2026-11-12 i18n-code F5) ------------------------
def test_landau_pole_code_gives_nan_in_the_world():
    """qcd.landau_pole: alpha_s is NaN below the pole (the world's curve has a gap), never a refusal."""
    import math

    from lfphys.codes import code_of
    from lfphys.core.qcd import running
    from lfphys.core import data
    from v06_qcd.viz import THRESH
    h = Harness(V, "standard")
    with pytest.raises(ValueError) as e:
        running.alpha_s(1.0, 0.3, data.M_Z[0], THRESH, 1)
    assert code_of(e.value) == "qcd.landau_pole"
    assert math.isnan(h.sim._alpha(1.0, loops=1, a_mz=0.3))


def test_rg_failure_code_becomes_the_worlds_refusal(monkeypatch):
    """qcd.rg_failed: the world says what failed and what to change; the solver's own words go to the details."""
    from lfphys.codes import coded
    from lfphys.core.qcd import running
    from lfphys.i18n import T
    from lfviz.errors import Refusal

    def fail(*a, **k):
        raise coded(ValueError(T("reworded by the engine at μ = {mu:.4g} GeV", mu=3.0)), "qcd.rg_failed",
                    solver="step size too small")

    h = Harness(V, "standard")
    monkeypatch.setattr(running, "alpha_s", fail)
    with pytest.raises(Refusal) as e:
        h.sim._alpha(3.0)
    assert e.value.text["$t"].startswith("the renormalisation-group equation was not solved")
    assert e.value.hint["$t"] == "take α_s(M_Z) closer to the world average {avg}"
    assert "step size too small" in str(e.value.detail)
