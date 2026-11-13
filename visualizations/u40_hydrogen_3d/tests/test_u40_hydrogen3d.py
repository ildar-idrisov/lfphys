# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u40: the hydrogen atom in 3-D. Every preset builds and passes its checks; the drawn cloud is |psi|^2 of the
independent route to the 8-bit resolution it is sent with; a superposition's phases are revealed only when the world's
time reaches them and the record stops growing after one period; real orbitals carry no current, complex ones circulate;
2p_x + i 2p_y is the m = +1 state; the reduced mass and the charge scale the atom; the slice planes of the shared
environment (any orientation, three at most, each checked, kept in a new world, coarse while moving); the schema's
edges are refused with a reason."""

import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest
from scipy import constants as sc

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.core.quantum import hydrogen as H  # noqa: E402
from lfphys.i18n import english, text_of  # noqa: E402
from u40_hydrogen_3d.engine import atoms as A  # noqa: E402
from u40_hydrogen_3d.viz import SCHEMA  # noqa: E402

V = "u40_hydrogen_3d"


def failed(h):
    return [c["id"] for c in h.checks().values() if not c.get("info") and (c.get("ok") is False or (
        c.get("ok") is None and c.get("rel") is not None and abs(c["rel"]) > c["tol"]))]


def clouds(h):
    out = {}
    for m, b in h.msgs:
        if m.get("type") == "cloud":
            q = np.frombuffer(zlib.decompress(b["data"].tobytes()), np.uint8).reshape(m["dims"])
            out[m["bin"]] = (m, q)
    return out


@pytest.mark.parametrize("preset", list(SCHEMA.presets))
def test_presets_build_and_pass(preset):
    h = Harness(V, preset)
    if h.sim.nb > 1:
        h.run_to(h.sim.period * 1.0001)
    assert not h.errors() and not failed(h), (h.errors(), failed(h))
    ids = set(h.checks())
    k = len(h.sim.state.orbitals)
    assert {f"norm_{i}" for i in range(k)} | {f"energy_{i}" for i in range(k)} | {"slice_1", "box"} <= ids
    assert ("dipole" in ids) == ("period" in ids) == (h.sim.nb > 1)
    assert ("current" in ids) == (k == 1) and ("continuity" in ids) == (k == 2)
    assert len(clouds(h)) == h.sim.nb


def test_the_drawn_cloud_is_the_density_of_the_independent_route():
    """Decode the cloud (sqrt(|psi|^2/peak) in 8 bits) and compare it with the series + scipy route at every grid
    node: within half a step of 1/255 (plus the reference's own tolerance, far below)."""
    for preset in ("3dz2", "2p_m1", "super_1s2p"):
        h = Harness(V, preset)
        sim = h.sim
        if sim.nb > 1:
            h.run_to(sim.period * 0.5)
        g = sim.axis / sim.Lu
        Z, X, Y = np.meshgrid(g, g, g, indexing="ij")
        for k, (m, q) in clouds(h).items():
            psi, _ = A.reference(sim.specs, sim.state.c, sim.Z, X, Y, Z, sim._t_bin(k))
            amp = np.sqrt(np.abs(psi) ** 2 / sim.peak)
            assert np.max(np.abs(q / 255.0 - amp)) <= 0.5 / 255 + 1e-9, (preset, k)
            assert m["peak"] == pytest.approx(sim.peak / sim.Lu**3)


def test_phases_are_revealed_when_time_reaches_them_and_the_record_stops_growing():
    h = Harness(V, "super_1s2p")
    sim = h.sim
    T, nb = sim.period, sim.nb
    assert nb == 24 and T == pytest.approx(2 * math.pi / (3 / 8) * A.units("H")["tu"], rel=1e-12)
    assert sorted(clouds(h)) == [0] and h.sim.next_event_time() == pytest.approx(T / nb)
    h.run_to(T / nb * 0.999)
    assert sorted(clouds(h)) == [0] and sim.frame()[0]["bin"] == 0  # never a later phase
    h.run_to(T / nb * 1.001)
    assert sorted(clouds(h)) == [0, 1] and sim.frame()[0]["bin"] == 1
    for t in np.linspace(0.0, 0.99 * T, 37):
        h.run_to(max(t, sim.t))
        assert sim.frame()[0]["bin"] <= max(clouds(h))
    h.run_to(T * 1.0001)
    assert sorted(clouds(h)) == list(range(nb)) and "period" in h.checks()
    n_before = len([m for m, _ in h.msgs if m["type"] in ("cloud", "vectors", "slice")])
    h.run_to(3.5 * T)
    assert len([m for m, _ in h.msgs if m["type"] in ("cloud", "vectors", "slice")]) == n_before
    assert sim.frame()[0]["bin"] == 12  # 3.5 periods: half a period, the phase reached
    assert sim.next_event_time() is None


def test_real_orbitals_carry_no_current_complex_ones_circulate():
    hr, hc = Harness(V, "2px_real"), Harness(V, "2p_m1")
    assert not hr.of("vectors") and hr.checks()["current"]["value"] == 0.0
    v = [(m, b) for m, b in hc.msgs if m["type"] == "vectors"]
    assert len(v) == 1
    pos, vec = v[0][1]["pos"].astype(float), v[0][1]["vec"].astype(float)
    assert np.max(np.abs(vec[:, 2])) < 1e-6 * np.max(np.abs(vec))  # rings around z
    turn = pos[:, 0] * vec[:, 1] - pos[:, 1] * vec[:, 0]  # (r x j)_z > 0 for m = +1
    assert np.all(turn >= -1e-6 * np.max(np.abs(turn))) and np.max(turn) > 0


def test_px_plus_i_py_is_the_m1_state():
    a = Harness(V, "px_ipy").sim
    b = Harness(V, "2p_m1", {"ng": 64}).sim
    assert a.nb == 1 and a.rb == pytest.approx(b.rb, rel=1e-12)
    assert np.max(np.abs(a._density_grid(0) - b._density_grid(0))) < 1e-14 * b.peak


def test_reduced_mass_and_charge_scale_the_atom():
    """E and a scale with mu (deuterium, positronium) and with Z (He+: radii / Z, energies x Z^2)."""
    uH, uD, uP, uHe = (A.units(k) for k in ("H", "D", "Ps", "He+"))
    assert uH["eV"] / uD["eV"] == pytest.approx(uH["mu"] / uD["mu"], rel=1e-14)
    assert uP["mu"] == pytest.approx(sc.m_e / 2, rel=1e-15) and uP["Lu"] == pytest.approx(2 * 0.529177210544, rel=1e-9)
    hH = Harness(V, "3dz2").sim
    hHe = Harness(V, "3dz2", {"atom": "He+"}).sim
    assert hHe.rb * hHe.Lu == pytest.approx(hH.rb * hH.Lu / 2 * uHe["a"] / uH["a"], rel=1e-9)
    E = {h.params["atom"]: h.header()[0]["states"][0]["E"] for h in (hH, hHe)}
    assert E["He+"] / E["H"] == pytest.approx(4 * uHe["mu"] / uH["mu"], rel=1e-12)
    assert hH.header()[0]["states"][0]["E"] == pytest.approx(H.level(3, 1, uH["mu"]) / sc.e, rel=1e-14)


def test_planes_any_orientation_three_at_most_each_checked_kept_and_coarse_when_moving():
    h = Harness(V, "3dz2")
    for pid, n in ((2, [0.3, -0.5, 0.8]), (3, [1.0, 1.0, 0.0])):
        h.cmd("view", op="plane", id=pid, origin=[0.2, 0.1, -0.3], normal=n)
    ids = h.checks()
    assert all(ids[f"slice_{p}"]["ok"] for p in (1, 2, 3)), [ids[f"slice_{p}"] for p in (1, 2, 3)]
    n_err = len(h.errors())
    h.cmd("view", op="plane", id=4, normal=[0, 0, 1])
    assert len(h.errors()) == n_err + 1 and 4 not in h.sim.planes
    sl = [m for m in h.of("slice") if m["id"] == 2][-1]
    assert sl["verify"]["points"] >= 1 and sl["verify"]["ok"] and sl["units"] == "Å" and sl["depth"] is False
    h.cmd("view", op="remove", id=3)
    assert h.checks()["slice_3"].get("info")
    h.cmd("new_world", preset="1s")
    planes = h.of("planes")[-1]["planes"]
    assert [p["id"] for p in planes] == [1, 2]
    h.cmd("view", op="plane", id=2, auto=True, speed=0.5)
    n0 = len(h.of("slice"))
    h.cmd("play")
    h.run_to(h.sim.t + 10 * h.sim.default_speed)
    moved = h.of("slice")[n0:]
    assert moved and all(m["coarse"] and not m["verify"]["points"] for m in moved[1:])
    h.cmd("view", op="reset")
    assert [p["id"] for p in h.of("planes")[-1]["planes"]] == [1]


def test_a_plane_placed_mid_period_gets_the_phases_reached_and_the_rest_later():
    h = Harness(V, "super_1s2p")
    T = h.sim.period
    h.run_to(T * 5.5 / 24)
    n0 = len(h.msgs)
    h.cmd("view", op="plane", id=2, normal=[1.0, 0.0, 0.0])
    bins = sorted(m["bin"] for m, _ in h.msgs[n0:] if m["type"] == "slice" and m["id"] == 2)
    assert bins == list(range(6))
    h.run_to(T * 1.0001)
    bins = sorted(m["bin"] for m in h.of("slice") if m["id"] == 2)
    assert bins == list(range(24)) and h.checks()["slice_2"]["ok"]


@pytest.mark.parametrize("params,why", [
    ({"mode": "super", "n": 2, "l": 1, "m": 0, "n2": 2, "l2": 1, "m2": 0}, "equals the first"),
    ({"mode": "super", "n": 2, "l": 1, "m": 1, "real": False, "n2": 2, "l2": 1, "m2": 1, "real2": True},
     "not orthogonal"),
])
def test_schema_edges_are_refused_with_a_reason(params, why):
    p, err = SCHEMA.resolve(None, params)
    assert not err
    with pytest.raises(ValueError) as e:
        Harness(V, None, params)
    assert why in english(text_of(e.value))


def test_largest_states_of_the_schema_build():
    h = Harness(V, None, {"n": 12, "l": 11, "m": 11, "real": False, "ng": 64})
    assert not failed(h) and h.checks()["nodes_0"]["value"] == 0
    h = Harness(V, None, {"n": 12, "l": 0, "m": 0, "ng": 64})
    assert not failed(h) and h.checks()["nodes_0"]["value"] == 11
    h = Harness(V, None, {"mode": "super", "n": 12, "l": 3, "m": 1, "n2": 11, "l2": 2, "m2": 1, "ng": 64})
    h.run_to(h.sim.period * 0.3)
    assert not failed(h) and h.sim.nb == 24


@pytest.mark.parametrize("params,state,note", [
    ({"n": 1}, (1, 0, 0), "l = 0 taken"), ({"n": 2, "l": 2}, (2, 1, 0), "for l = 2 choose n ≥ 3"),
    ({"n": 3, "l": 1, "m": 2}, (3, 1, 1), "m = 1 taken"), ({"l": 11, "m": -11}, (2, 1, -1), "m = -1 taken"),
])
def test_quantum_numbers_the_form_cannot_bound_are_fitted_and_said(params, state, note):
    """Review UX-params P10 (was: refused at the start, 102 of 235 combinations, hidden by the player): the world takes
    l < n and |m| <= l nearest to what was asked, says so, and its header carries the state shown; idempotent."""
    from u40_hydrogen_3d.viz import _fit_numbers
    h = Harness(V, None, {**params, "ng": 64})
    hp = h.of("header")[-1]["params"]
    assert (hp["n"], hp["l"], hp["m"]) == state and not failed(h)
    assert any(note in english(m["text"]) for m in h.of("notice"))
    assert _fit_numbers(dict(hp)) == []


def test_superposition_from_the_defaults_and_a_current_free_one():
    """Review UX-params P10: "Superposition" alone was refused (the second state's defaults were the first's); now the
    second state defaults to 1s (2p_z + 1s oscillates at the 2p-1s frequency), and a first state of 1s takes 2p_z.
    P3 (world part): 2p_z + 2s, real states of one energy, have j = 0 and d rho/dt = 0 everywhere, and the continuity
    check divided by a zero scale («float division by zero» killed the worker); now it passes with a residual of
    exactly 0. Negative control: the same pair with a phase of 90° carries a current and is checked as before."""
    h = Harness(V, None, {"mode": "super", "ng": 64})
    hp = h.of("header")[-1]["params"]
    assert (hp["n2"], hp["l2"], hp["m2"]) == (1, 0, 0) and h.sim.nb > 1
    h.run_to(h.sim.period * 1.0001)
    assert not failed(h) and h.checks()["continuity"]["ok"]
    h = Harness(V, None, {"mode": "super", "n": 1, "ng": 64})
    hp = h.of("header")[-1]["params"]
    assert (hp["n2"], hp["l2"], hp["m2"]) == (2, 1, 0) and any("2p_z taken" in english(m["text"]) for m in h.of("notice"))
    h = Harness(V, None, {"mode": "super", "n2": 2, "l2": 0, "ng": 64})
    h.run_to(1.0)
    c = h.checks()["continuity"]
    assert c["ok"] and c["value"] == 0.0 and "the current is zero everywhere" in english(c["note"])
    h = Harness(V, None, {"mode": "super", "n2": 2, "l2": 0, "phase2": 90.0, "ng": 64})
    h.run_to(1.0)
    c = h.checks()["continuity"]
    assert c["ok"] and "fraction of the scale" in english(c["note"])


# --- the state is live: an ideal preparation at the current moment (review UX-ui U12) -----------------------------------
def _since(h, n0, typ):
    return [(m, b) for m, b in h.msgs[n0:] if m.get("type") == typ]


def _cloud(m, b):
    return np.frombuffer(zlib.decompress(b["data"].tobytes()), np.uint8).reshape(m["dims"])


def test_a_state_set_live_is_prepared_in_the_same_world():
    """n, l, m changed while the world runs: no new world; `prepared` comes first with the new state's header parts,
    then the new cloud — the very cloud of a world built with that state (bit for bit) — its current, slices and checks,
    all passing; checks of the former state that the new one does not give are retired as information; frames carry
    the moment of preparation."""
    h = Harness(V, "super_1s2p")
    h.run_to(h.sim.period * 0.37)
    t_p = h.sim.t
    n0 = len(h.msgs)
    h.set(mode="single", n=3, l=2, m=0)
    assert not h.errors(), h.errors()
    new = [m["type"] for m, _ in h.msgs[n0:] if m.get("type") != "command"]
    assert new[0] == "prepared" and "header" not in new and "cloud" in new and "slice" in new
    pm = h.msgs[n0 + [m.get("type") for m, _ in h.msgs[n0:]].index("prepared")][0]
    assert pm["t_prep"] == t_p and [s["label"] for s in pm["header"]["states"]] == ["3d_z²"]
    assert pm["header"]["nb"] == 1 and pm["header"]["scene3d"]["box"] != h.of("header")[-1]["scene3d"]["box"]
    built = Harness(V, "3dz2", {"ng": 64})
    (ma, ba), = _since(h, n0, "cloud")
    (mb, bb), = [(m, b) for m, b in built.msgs if m["type"] == "cloud"]
    assert np.array_equal(_cloud(ma, ba), _cloud(mb, bb)) and ma["peak"] == mb["peak"]
    c = h.checks()
    assert not failed(h), failed(h)
    for k in ("norm_1", "energy_1", "dipole", "continuity"):
        assert c[k]["info"] and c[k]["value"] is None and "former state" in english(c[k]["label"]), k
    assert c["current"]["ok"] and c["norm_0"]["value"] == pytest.approx(1.0)
    assert h.sim.frame()[0]["t_prep"] == t_p and h.sim.live_values()["n"] == 3
    assert h.of("live")[-1]["values"]["l"] == 2
    assert "prepared the state 3d_z²" in english(h.of("event")[-1]["text"])


def test_a_superposition_prepared_mid_world_counts_its_period_from_the_preparation():
    """1s + 2p_z prepared at t_p (not a multiple of a phase step): its phases are revealed at t_p + kT/24 and each is the
    cloud of a world that started with it at 0, bit for bit; the period check comes at t_p + T. Negative control: phases
    counted from t = 0 (the former rule) would show another phase at the same moment."""
    h = Harness(V, "2pz", {"ng": 64})
    h.run_to(1.234e-16)
    t_p = h.sim.t
    n0 = len(h.msgs)
    h.set(mode="super", n=1, l=0, m=0, n2=2, l2=1, m2=0)
    s = h.sim
    T, nb = s.period, s.nb
    assert nb == 24 and s.next_event_time() == pytest.approx(t_p + T / nb)
    h.run_to(t_p + 5.5 * T / nb)
    got = {m["bin"]: _cloud(m, b) for m, b in _since(h, n0, "cloud")}
    assert sorted(got) == list(range(6)) and s.frame()[0]["bin"] == 5
    assert int(math.floor(s.t / T * nb)) != 5  # counted from t = 0 the phase would differ here
    ref = Harness(V, "super_1s2p")
    ref.run_to(5.5 * T / nb)
    want = {m["bin"]: _cloud(m, b) for m, b in ref.msgs if m["type"] == "cloud"}
    for k in range(6):
        assert np.array_equal(got[k], want[k]), k
    assert "period" not in [m["id"] for m, _ in _since(h, n0, "check") if not m.get("info")]
    h.run_to(t_p + T * 1.0001)
    assert h.checks()["period"]["ok"] and not failed(h)


def test_a_refused_preparation_leaves_the_world_as_it_was():
    """A second state chosen by hand equal to the first is refused: the state, its time, the planes and the parameters
    are as before, and only the refusal and the live values in force are emitted."""
    h = Harness(V, None, {"mode": "super", "n": 2, "l": 1, "m": 0, "n2": 3, "l2": 0, "ng": 64})
    h.run_to(h.sim.period * 0.2)
    before = (h.sim.state, h.sim.t_prep, dict(h.sim.planes), h.sim.revealed, dict(h.sim.params), h.sim.box)
    n0 = len(h.msgs)
    h.set(n2=2, l2=1)
    assert "equals the first" in english(h.errors()[-1])
    assert (h.sim.state, h.sim.t_prep, dict(h.sim.planes), h.sim.revealed, dict(h.sim.params), h.sim.box) == before
    types = {m["type"] for m, _ in h.msgs[n0:]}
    assert "error" in types and types <= {"command", "error", "live"}, types
    assert h.of("live")[-1]["values"]["n2"] == 3


def test_the_planes_placed_stay_through_a_preparation_and_the_grid_is_live():
    """A slice plane placed before a preparation is placed again in the new state (same normal, new box), computed and
    checked; the cloud's grid changed alone resamples the same state at the same moment of preparation (the player
    sends a select's value as text)."""
    h = Harness(V, "1s", {"ng": 64})
    h.cmd("view", op="plane", id=2, normal=[1.0, 0.0, 0.0])
    h.set(n=4, l=3, m=1)
    planes = h.of("planes")[-1]["planes"]
    assert [p["id"] for p in planes] == [1, 2] and planes[1]["normal"] == [1.0, 0.0, 0.0]
    assert h.checks()["slice_2"]["ok"] and "former" not in english(h.checks()["slice_2"]["label"])
    t_p = h.sim.t_prep
    h.run_to(h.sim.t + 1e-16)
    h.set(ng="96")
    assert not h.errors(), h.errors()
    assert h.sim.ng == 96 and h.sim.t_prep == t_p and h.of("cloud")[-1]["dims"] == [96, 96, 96]
    assert h.of("prepared")[-1]["keep_time"] and "the state and its time stay the same" in english(h.of("event")[-1]["text"])


def test_the_atom_stays_a_world_parameter():
    h = Harness(V, "1s", {"ng": 64})
    h.set(atom="He+")
    assert "Atom" in english(h.errors()[-1]) and h.sim.params["atom"] == "H"


def test_a_preparation_is_continued_from_a_checkpoint_byte_for_byte(tmp_path):
    """A preparation before a checkpoint and another after it: the world continued from the checkpoint in a new process
    emits the original's bytes (the shared session of tests/test_checkpoint.py, with the state live)."""
    import json
    import queue
    import subprocess
    import test_checkpoint as TC
    from lfviz.sim import Runner
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    make_world = TC._maker(V, emit)
    sim, _ = make_world("super_1s2p", {}, 7)
    run = Runner(sim, emit, queue.Queue(), make_world=make_world)
    run._start_world()
    sp = sim.default_speed
    TC._apply(run, [{"adv": 0.5 * sp}, {"cmd": "set", "args": {"values": {"n": 2, "l": 1, "m": 1, "real": False}}},
                    {"adv": 0.7 * sp}, {"cmd": "view", "args": {"op": "plane", "id": 2, "normal": [1.0, 0.0, 0.0]}}])
    file = TC._checkpoint(run, tmp_path)
    n0 = len(msgs)
    after = [{"adv": 0.3 * sp}, {"cmd": "set", "args": {"values": {"mode": "super", "n2": 3, "l2": 2, "m2": 1}}},
             {"adv": 2.0 * sp}, {"adv": 3.0 * sp}]
    TC._apply(run, after)
    original = TC._bytes(msgs[n0:])
    assert any(m.get("type") == "prepared" for m, _ in msgs[n0:])
    out = tmp_path / "session.bin"
    code = TC.SESSION_CHILD.format(paths=repr(list(sys.path)), file=str(file), viz=V, ops=json.dumps(after),
                                   out=str(out))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=900,
                       cwd=str(Path(TC.__file__).parent))
    assert r.returncode == 0, r.stderr[-4000:]
    data, cont, i = out.read_bytes(), [], 0
    while i < len(data):
        n = int.from_bytes(data[i:i + 8], "little")
        cont.append(data[i + 8:i + 8 + n])
        i += 8 + n
    assert cont == original
