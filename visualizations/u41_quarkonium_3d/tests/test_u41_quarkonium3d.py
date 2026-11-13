# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u41: quarkonium in 3-D (the Cornell model, flagged as a model). Every preset builds and passes its checks; the
world's levels are those of ``cornell.splittings``; the radial functions converge and their energies agree with the
eigenvalues; the drawn cloud is |psi|^2 of the independent route (a finer radial solve, scipy's harmonics) to its 8-bit
resolution; bottomonium is smaller than charmonium; the superposition oscillates at the model's transition frequency
and is periodic; the schema's edges are refused with a reason."""

import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.i18n import english, text_of  # noqa: E402
from lfphys.theories.models import cornell  # noqa: E402
from u41_quarkonium_3d.engine import pair as Q  # noqa: E402
from u41_quarkonium_3d.viz import SCHEMA  # noqa: E402

V = "u41_quarkonium_3d"


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build_and_pass(preset):
    h = Harness(V, preset)
    if h.sim.nb > 1:
        h.run_to(h.sim.period * 1.0001)
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    hdr = h.of("header")[0]
    assert hdr["approximations"] and "theories.models.cornell" in [e["id"] for e in hdr["engine"]]
    ids = h.checks()
    for k in range(len(h.sim.state.orbitals)):
        assert ids[f"conv_{k}"]["value"] < 1e-3 and ids[f"energy_{k}"]["ok"]
    assert all(c.get("info") for i, c in ids.items() if i.startswith("split_"))  # a model against data: information


def test_levels_are_the_models_splittings():
    """The world's level diagram (its own solves, N = 800) against cornell.splittings (N = 700): the same model to the
    solver's accuracy (Richardson-extrapolated levels: ~1e-5 GeV)."""
    for system in ("charm", "bottom"):
        sim = Harness(V, None, {"system": system}).sim
        ref = cornell.splittings(Q.mass(system))
        for lev in sim.levels:
            n, L = (int(c) for c in lev["key"].split(","))
            assert lev["E"] == pytest.approx(ref[(n, L)] * 1e3, abs=0.05), (system, n, L)


def test_the_drawn_cloud_is_the_density_of_the_independent_route():
    for preset in ("cc_2S", "bb_1P", "cc_1P_m1"):
        h = Harness(V, preset)
        sim = h.sim
        (m, b), = [(m, b) for m, b in h.msgs if m["type"] == "cloud"]
        q = np.frombuffer(zlib.decompress(b["data"].tobytes()), np.uint8).reshape(m["dims"])
        g = sim.axis / sim.Lu
        Z, X, Y = np.meshgrid(g, g, g, indexing="ij")
        psi, tol = Q.reference(sim.system, sim.specs, sim.state.c, X, Y, Z, 0.0, sim.ref_tabs, sim.tabs)
        amp = np.sqrt(np.abs(psi) ** 2 / sim.peak)
        assert np.max(np.abs(q / 255.0 - amp)) <= 0.5 / 255 + 2 * float(np.max(tol)) / math.sqrt(sim.peak), preset


def test_bottomonium_is_smaller_and_the_states_grow_with_n_and_L():
    r = {}
    for preset in ("cc_1S", "cc_2S", "cc_1P", "bb_1S", "bb_2S"):
        r[preset] = Harness(V, preset).of("header")[0]["states"][0]["r_mean_quad"]
    assert r["bb_1S"] < 0.6 * r["cc_1S"] and r["bb_2S"] < r["cc_2S"]
    assert r["cc_1S"] < r["cc_1P"] < r["cc_2S"]
    assert 0.25 < r["cc_1S"] < 0.45  # fm: the measured-order size of J/psi (model value 0.337 fm)


def test_superposition_oscillates_at_the_transition_frequency():
    h = Harness(V, "cc_super")
    sim = h.sim
    dE = sim.state.orbitals[1].energy - sim.state.orbitals[0].energy
    assert sim.period == pytest.approx(2 * math.pi / dE * Q.HBAR_GEV_S, rel=1e-12)
    assert 1e-24 < sim.period < 1e-22
    h.run_to(sim.period * 1.0001)
    assert h.checks()["period"]["ok"] and h.checks()["dipole"]["ok"] and h.checks()["continuity"]["ok"]


@pytest.mark.parametrize("params,why", [
    ({"mode": "super", "n2": 1, "l2": 0, "m2": 0}, "equals the first"),
    ({"mode": "super", "l": 1, "m": 1, "real": False, "n2": 1, "l2": 1, "m2": 1, "real2": True}, "not orthogonal"),
])
def test_schema_edges_are_refused_with_a_reason(params, why):
    with pytest.raises(ValueError) as e:
        Harness(V, None, params)
    assert why in english(text_of(e.value))


def test_highest_states_of_the_schema_build():
    for system in ("charm", "bottom"):
        h = Harness(V, None, {"system": system, "n": 3, "l": 2, "m": -2, "real": True, "ng": 64})
        assert not failed(h) and h.checks()["nodes_0"]["value"] == 2


def test_m_beyond_L_is_fitted_and_a_default_second_state_equal_to_the_first_is_replaced():
    """Review UX-params P10: |m| > L was refused at the start (34 combinations, hidden by the player); now m is taken
    nearest to what was asked and said. "Superposition" with a first state of 1P_z and the default second (1P_z) takes
    1S; a second state chosen equal to the first by hand is still refused (test above)."""
    h = Harness(V, None, {"l": 1, "m": 2, "ng": 64})
    hp = h.of("header")[-1]["params"]
    assert (hp["l"], hp["m"]) == (1, 1) and any("m = 1 taken" in english(m["text"]) for m in h.of("notice"))
    h = Harness(V, None, {"mode": "super", "l": 1, "ng": 64})
    hp = h.of("header")[-1]["params"]
    assert (hp["n2"], hp["l2"], hp["m2"]) == (1, 0, 0) and h.sim.nb > 1 and not failed(h)


def test_a_state_set_live_is_prepared_in_the_same_world():
    """Review UX-ui U12: the state is live — 1P_z prepared in a running 1S world is the cloud of a world built with 1P_z
    (bit for bit), its checks pass (the model's splitting against data stays information), the 1S-only checks are
    replaced, and no new world starts; the quark pair stays a world parameter."""
    h = Harness(V, None, {"ng": 64})
    h.run_to(3e-24)
    n0 = len(h.msgs)
    h.set(l=1)
    assert not h.errors(), h.errors()
    assert [m["type"] for m, _ in h.msgs[n0:] if m["type"] != "command"][0] == "prepared"
    assert [m["world"] for m in h.of("header")] == [1]
    clouds = [(m, b) for m, b in h.msgs[n0:] if m["type"] == "cloud"]
    built = Harness(V, "cc_1P", {"ng": 64})
    ref = [(m, b) for m, b in built.msgs if m["type"] == "cloud"]
    dec = lambda mb: np.frombuffer(zlib.decompress(mb[1]["data"].tobytes()), np.uint8)  # noqa: E731
    assert len(clouds) == 1 and np.array_equal(dec(clouds[0]), dec(ref[0]))
    assert not failed(h), failed(h)
    assert h.checks()["split_0"]["info"] and h.sim.frame()[0]["t_prep"] == h.sim.t
    h.set(system="bottom")
    assert "Quark pair" in english(h.errors()[-1]) and h.sim.system == "charm"


def test_a_box_too_small_for_the_states_is_refused_with_the_engines_code(monkeypatch):
    """Review i18n-code F5: the world's radial solve enlarges its box like the engine's Cornell spectrum
    (cornell._box_needed); when four enlargements do not hold the states (forced here: the needed box always grows),
    the refusal carries the engine's code "cornell.box" and the world's own msgid. The engine's spectrum itself refuses
    the same condition with the same code."""
    from lfphys.codes import code_of
    calls = []

    def growing(kappa, a, mu, L, E):  # always twice the box asked last time
        calls.append(1)
        return 50.0 * 2.0 ** len(calls)
    monkeypatch.setattr(cornell, "_box_needed", growing)
    Q.solve.cache_clear()
    try:
        with pytest.raises(ValueError) as e:
            Q.solve("charm", 1, 3, 200)
        assert code_of(e.value) == "cornell.box"
        assert text_of(e.value).msgid == "the states with L = {L} do not fit into the box of radius {R:.3g} GeV⁻¹"
        calls.clear()
        with pytest.raises(ValueError) as e2:
            cornell.spectrum(Q.mass("charm"), L_max=0, n_max=1, N=200)
        assert code_of(e2.value) == "cornell.box"
    finally:
        Q.solve.cache_clear()
