# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p03 as a bench that never restarts (LB1: plan P16.1–P16.3): the box (Lx, Ly, Lz) changed at the current moment —
affinely with its work in the first law, or a wall moved over empty space —, the dynamics switched between continuous
forces and hard spheres in the same world, the handles of direct manipulation (a drag moves a group as a whole, a throw
gives it a centre-of-mass velocity), ``at`` and ``meas`` in every frame, the measurables, a scene carried between a plane
and a volume, and a restore repeating all of it. The engine's physics of the deformation and the switch:
lfphys/tests/test_md_deform.py."""

import math
import queue
import re
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from harness import Harness  # noqa: E402

from lfphys.i18n import english, is_t, msgids, text_of  # noqa: E402
from lfviz import registry  # noqa: E402
from lfviz.i18n import catalogue  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
from p03_molecules.viz import KELVIN, NM, U  # noqa: E402

V = "p03_molecules"
ENGINE = ("jammed", "overlap: an inserted", "Traceback", "bond would", "piston needs", "it has no wall", "outside the walls on axis")
RU = catalogue("ru")


class _Text(str):
    """An English rendering that remembers the text it renders (``translated`` checks the text itself)."""


def en(x):
    """A text as the player shows it in English (numbers in Python's format)."""
    s = _Text(english(x))
    s.raw = x
    return s


def translated(x):
    """The owner's text: a translatable text whose every part has a Russian translation, with none of the engine's
    English sentences (review UX-ui U13)."""
    x = getattr(x, "raw", x)
    ids = msgids(x) if is_t(x) else set()
    return bool(ids) and all(i in RU or not re.search(r"[A-Za-z]", re.sub(r"\{\w+(?::[^{}]*)?\}", "", i)) for i in ids) \
        and not any(w in english(x) for w in ENGINE)



def run(h, ps, n=10):
    t0 = h.sim.t
    for k in range(1, n + 1):
        h.run_to(t0 + ps * 1e-12 * k / n)
        h.runner._frame(0.0)



def added(h, typ):
    return [o for o in h.sim.objects.values() if o["type"] == typ]


def frame(h):
    h.runner._frame(0.0)
    return [m for m, _ in h.msgs if m.get("type") == "frame"][-1]


def _eq(a, b):
    """Equal to the bit: NumPy arrays element by element (NaN equal to NaN), containers recursively."""
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        a, b = np.asarray(a), np.asarray(b)
        return a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b, equal_nan=a.dtype.kind == "f")
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return type(a) is type(b) and a == b if not callable(a) else repr(a) == repr(b)


def same_world(a, b, skip=("stats",)):
    """The whole engine state of ``a`` equals the state dict ``b`` to the bit (every key but the timing statistics)."""
    sa, sb = a.state_dict(), b
    if sa.keys() != sb.keys():
        return False
    return all(_eq(sa[k], sb[k]) for k in sa if k not in skip)


# --- the box at the current moment (P16.1) -------------------------------------------------------------------------
def test_live_box_affine_books_its_work_and_shows_the_new_box():
    """Lx 12 → 10.5 nm in one jump (time 0) in the Maxwell preset (2-D argon, periodic): the same atoms scaled with the
    box (x × 0.875), the peculiar velocities × 1/0.875 along x; the work W = ΔE booked in the first law (the residual
    stays at the Verlet level); the event states W, −P·ΔV, the temperature's change and that a jump is not
    quasi-static; the view gets a ``box`` message; the world runs on."""
    h = Harness(V, "maxwell")
    run(h, 1.0, 4)
    h.set(box_time_ps=0.0)
    md = h.sim.md
    x0, v0, E0 = md.positions().copy(), md.velocities().copy(), md.energy()
    res0 = md.energy_balance()["residual"]
    t0 = time.perf_counter()
    h.set(Lx=10.5)
    lat = time.perf_counter() - t0
    assert not h.errors(), h.errors()
    md = h.sim.md
    lam = 10.5 / 12.0
    assert md.L[0] * NM == pytest.approx(10.5) and h.sim.box[0] * NM == pytest.approx(10.5)
    assert np.allclose(md.positions()[:, 0], x0[:, 0] * lam, atol=1e-12)
    vc = v0[:, 0].mean()
    assert np.allclose(md.velocities()[:, 0], vc + (v0[:, 0] - vc) / lam, atol=1e-12)
    b = md.energy_balance()
    assert b["W_box"] == pytest.approx(md.energy() - E0, rel=1e-9)
    assert abs(b["residual"] - res0) < 1e-9
    ev = en(h.of("event")[-1]["text"])
    assert "the work on the system" in ev and "−P·ΔV" in ev and "temperature" in ev and translated(ev)
    assert "instantaneously" in ev and "not quasi-static" in ev
    box = h.of("box")[-1]["box"]
    assert box[1][0] == pytest.approx(10.5) and box[1][1] == pytest.approx(12.0)
    assert h.of("live")[-1]["values"]["Lx"] == 10.5
    f = frame(h)
    assert f["box_nm"][0] == pytest.approx(10.5)
    run(h, 1.0, 4)
    assert not h.errors(), h.errors()
    assert lat < 1.0, lat


def test_live_box_refusals_leave_the_world_bit_for_bit():
    """A crystal squeezed into overlap, molecules' bonds stretched by more than 10 %, a wall moved over atoms, a wall
    on a periodic axis, the piston's axis affinely, Lz in a plane: each refused in Russian with what fits; the world
    is bit for bit as before and the live value rolls back."""
    h = Harness(V, "melting")
    run(h, 0.5, 2)
    h.set(box_time_ps=0.0)     # jumps: the overlap and the bond limit are a jump's refusals
    st = h.sim.md.state_dict()
    Lx = h.sim.live["Lx"]
    h.set(Lx=Lx * 0.7)
    e = en(h.errors()[-1])
    assert "would overlap" in e and "now it can go to" in e and translated(e), e
    assert same_world(h.sim.md, st) and h.sim.live["Lx"] == Lx and h.of("live")[-1]["values"]["Lx"] == Lx
    h.set(box_mode="wall", Ly=h.sim.live["Ly"] + 1.0)
    assert "periodic" in en(h.errors()[-1]) and translated(en(h.errors()[-1]))
    h.set(Lz=3.0)
    assert "a plane has no axis z" in en(h.errors()[-1])

    m = Harness(V, "molecules")
    m.set(box_time_ps=0.0)
    m.set(Lx=5.0 * 1.2)
    assert "the molecules' bonds" in en(m.errors()[-1]) and "10 %" in en(m.errors()[-1]) and translated(en(m.errors()[-1]))
    m.set(Lx=5.0 * 1.05)
    assert len(m.errors()) == 1, m.errors()

    p = Harness(V, "piston")
    p.set(Ly=17.0)
    assert "piston" in en(p.errors()[-1]) and translated(en(p.errors()[-1]))
    p.set(box_mode="wall", Ly=17.0)        # the piston's upper stop: allowed
    assert len(p.errors()) == 1, p.errors()
    p.set(Ly=9.0)                          # below the piston's face
    assert "piston" in en(p.errors()[-1])
    p.set(Lx=8.0)                          # the gas is in the whole width: atoms beyond the moved wall
    assert "atoms would be left behind" in en(p.errors()[-1]) and translated(en(p.errors()[-1]))


def test_live_box_wall_mode_is_a_free_expansion():
    """The piston preset without its piston: the side wall moved out over empty space does no work (W_box = 0, the
    energy unchanged); the gas spreads into it."""
    h = Harness(V, "piston")
    pid = added(h, "piston")[0]["id"]
    h.cmd("scene", op="remove", id=pid)
    run(h, 0.5, 2)
    E0 = h.sim.md.energy()
    h.set(box_mode="wall", Lx=20.0)
    assert not h.errors(), h.errors()
    assert h.sim.md.energy() == E0 and h.sim.md.energy_balance()["W_box"] == 0.0
    assert "no work on the system" in en(h.of("event")[-1]["text"])
    run(h, 20.0, 10)
    assert np.max(h.sim.md.positions()[:, 0]) * NM > 12.0


def test_hard_world_box_only_by_a_wall():
    h = Harness(V, None, {"dynamics": "hard", "boundary": "walls"})
    h.cmd("scene", op="add", type="gas", values={"n": 30, "sx": 5.0, "sy": 5.0, "x": 3.0, "y": 3.0})
    h.set(Lx=14.0)
    e = en(h.errors()[-1])
    assert "affine" in e and "move the upper wall" in e and translated(e)
    h.set(box_mode="wall", Lx=14.0)
    assert len(h.errors()) == 1 and h.sim.md.L[0] * NM == pytest.approx(14.0)
    run(h, 2.0, 4)
    assert len(h.errors()) == 1, h.errors()


# --- the dynamics at the current moment (P16.1) ------------------------------------------------------------------
def test_switch_hard_to_soft_and_back_keeps_atoms_and_states_the_jump():
    """Hard disks → forces (Lennard-Jones): the same keys, positions, velocities and time; the event states the energy
    jump (the potential energy appearing); the palette opens. Back to hard disks after a dilute WCA phase: allowed when
    no pair is inside contact, else refused with the count and the advice (lower density or temperature)."""
    h = Harness(V, None, {"dynamics": "hard", "Lx": 30.0, "Ly": 30.0})
    h.cmd("scene", op="add", type="gas", values={"n": 60, "T": 100.0})
    run(h, 1.0, 2)
    md = h.sim.md
    k, x, v, t = md.keys.copy(), md.positions() % md.L, md.velocities().copy(), md.t
    assert set(h.sim.palette_state()) >= {"molecule", "piston", "thermostat", "gravity"}
    assert translated(en(h.sim.palette_state()["piston"]))
    h.set(dynamics="forces")
    assert not h.errors(), h.errors()
    md = h.sim.md
    assert not h.sim.hard and type(md).__name__ == "MD"
    assert np.array_equal(md.keys, k) and np.allclose(md.positions(), x, atol=1e-12)
    assert np.array_equal(md.velocities(), v) and md.t == t
    ev = en(h.of("event")[-1]["text"])
    assert "potential energy appeared" in ev and translated(ev)
    assert "molecule" not in h.sim.palette_state()
    assert "lfphys.core.md.hard" not in [e["module"] if isinstance(e, dict) and "module" in e else e
                                         for e in h.sim.engine_modules()]
    run(h, 1.0, 4)
    assert not h.errors(), h.errors()
    h.set(model="wca")
    h.set(dynamics="hard")
    err = h.errors()
    if err:      # a pair inside contact at this moment: the refusal names the count and the way out
        assert "pairs of atoms closer than σ" in en(err[-1]) and "lower the density" in en(err[-1]) and translated(en(err[-1]))
        assert not h.sim.hard
    else:
        assert h.sim.hard and "potential energy" in en(h.of("event")[-1]["text"])


def test_switch_to_hard_names_what_blocks_it_and_restores_bit_for_bit():
    h = Harness(V, "molecules")
    st = h.sim.md.state_dict()
    h.set(dynamics="hard")
    e = en(h.errors()[-1])
    assert "molecules “Molecules X₂”" in e and translated(e), e
    assert same_world(h.sim.md, st) and not h.sim.hard and h.of("live")[-1]["values"]["dynamics"] == "forces"
    p = Harness(V, "melting")
    p.set(dynamics="hard")
    assert "the thermostat “Heating to 120 K”" in en(p.errors()[-1])


def test_switch_overlap_refusal_counts_pairs():
    """A dense Lennard-Jones liquid always has pairs inside σ: the switch is refused with their number."""
    h = Harness(V, None, {"Lx": 6.0, "Ly": 6.0})
    h.cmd("scene", op="add", type="crystal", values={"density": 0.95, "T": 120.0})
    run(h, 1.0, 4)
    h.set(dynamics="hard")
    e = en(h.errors()[-1])
    assert "pairs of atoms closer than σ" in e and "the closest" in e and translated(e), e


# --- handles: a drag and a throw (P16.2) -------------------------------------------------------------------------------
def test_palette_declares_handles():
    pal = {p["type"]: p for p in h_header()["playground"]["palette"]}
    if "handles" not in pal["gas"]:
        pytest.skip("the framework does not send handles")
    # a throw comes in the world's units, nm per second of world time (review LB1-p02-ux X4): its own parameters,
    # at most 500 m/s
    assert pal["gas"]["handles"]["position"] == ["x", "y"]
    assert pal["gas"]["handles"]["velocity"] == ["throw_vx", "throw_vy"]
    assert pal["atom"]["handles"]["velocity"] == ["throw_vx", "throw_vy"]
    assert pal["gas"]["handles"]["velocity_max"] == pytest.approx(500.0 * 1e9)
    for t in ("gas", "crystal", "atom", "molecule"):     # every type with a throw shows it in m/s
        assert pal[t]["handles"]["velocity_display"] == {"unit": "m/s", "factor": pytest.approx(1e-9)}
    assert pal["probe"]["handles"] == {"position": ["x", "y"], "size": "r"}
    assert pal["piston"]["handles"]["position"] == {"param": "position", "axis_param": "axis"}
    assert "handles" not in pal["wall"] and "handles" not in pal["thermostat"]


def h_header():
    return Harness(V, None, {}).of("header")[-1]


def _op():
    from lfviz import playground as PG
    return "edit" if "def _edit" in open(PG.__file__, encoding="utf-8").read() else "set"


def test_drag_moves_a_group_as_a_whole_and_a_throw_gives_its_centre_a_velocity():
    """A gas block dragged by (2, −1) nm: every atom moves by that (its relative positions kept, minimum image),
    velocities unchanged, ``at`` follows the centre; thrown: its centre-of-mass velocity is the one given, the motion
    about the centre unchanged; the world runs on."""
    h = Harness(V, None, {"Lx": 20.0, "Ly": 20.0})
    h.cmd("scene", op="add", type="gas", values={"n": 40, "x": 6.0, "y": 6.0, "sx": 4.0, "sy": 4.0})
    gid = added(h, "gas")[0]["id"]
    f = frame(h)
    c0 = np.array(f["at"][gid][:2])
    x0, v0 = h.sim.md.positions().copy(), h.sim.md.velocities().copy()
    t0 = time.perf_counter()
    h.cmd("scene", op=_op(), id=gid, values={"x": float(c0[0] + 2.0), "y": float(c0[1] - 1.0)})
    lat = time.perf_counter() - t0
    assert not h.errors(), h.errors()
    d = (h.sim.md.positions() - x0) * NM
    assert np.allclose(d, [2.0, -1.0], atol=1e-9)
    assert np.array_equal(h.sim.md.velocities(), v0)
    c1 = np.array(frame(h)["at"][gid][:2])
    assert np.allclose(c1 - c0, [2.0, -1.0], atol=1e-6)
    h.cmd("scene", op=_op(), id=gid, values={"throw_vx": 300.0e9, "throw_vy": -100.0e9})   # nm/s: 300, −100 m/s
    assert not h.errors(), h.errors()
    log = english([m.get("text", "") for m in h.of("event") if m.get("name") == "edit"][-1])
    assert "m/s" in log and "nm/s" not in log and "300" in log, log      # logged in m/s (velocity_display)
    assert h.sim.objects[gid]["values"]["vx"] == pytest.approx(300.0)
    vc = h.sim.md.velocities().mean(axis=0) * U.velocity_m_s
    assert np.allclose(vc, [300.0, -100.0], atol=1e-9)
    dv = h.sim.md.velocities() - v0
    assert np.allclose(dv - dv.mean(axis=0), 0.0, atol=1e-12)
    run(h, 1.0, 4)
    assert not h.errors(), h.errors()
    assert lat < 0.5, lat


def test_a_drag_onto_other_atoms_or_through_a_wall_is_refused():
    h = Harness(V, None, {"Lx": 20.0, "Ly": 20.0, "boundary": "walls"})
    h.cmd("scene", op="add", type="crystal", values={"density": 0.9, "x": 5.0, "y": 5.0, "sx": 4.0, "sy": 4.0})
    h.cmd("scene", op="add", type="crystal", values={"density": 0.9, "x": 14.0, "y": 14.0, "sx": 4.0, "sy": 4.0})
    a, b = [o["id"] for o in added(h, "crystal")]
    st = h.sim.md.state_dict()
    at = frame(h)["at"]
    h.cmd("scene", op=_op(), id=a, values={"x": at[b][0], "y": at[b][1]})
    e = en(h.errors()[-1])
    assert "closer than σ to atoms of other objects" in e and translated(e), e
    h.cmd("scene", op=_op(), id=a, values={"x": -3.0, "y": at[a][1]})
    e = en(h.errors()[-1])
    assert "beyond the wall" in e and "the centre along x from" in e, e
    assert same_world(h.sim.md, st)


def test_atom_drag_keeps_its_velocity_and_a_throw_keeps_its_place():
    h = Harness(V, None, {"Lx": 20.0, "Ly": 20.0})
    h.cmd("scene", op="add", type="atom", values={"x": 5.0, "y": 5.0, "vx": 100.0, "vy": 0.0})
    aid = added(h, "atom")[0]["id"]
    run(h, 0.2, 2)
    v0 = h.sim.md.velocities().copy()
    h.cmd("scene", op=_op(), id=aid, values={"x": 12.0, "y": 9.0})
    assert not h.errors(), h.errors()
    assert np.allclose(h.sim.md.positions()[0] * NM, [12.0, 9.0], atol=1e-9)
    assert np.array_equal(h.sim.md.velocities(), v0)
    x0 = h.sim.md.positions().copy()
    h.cmd("scene", op=_op(), id=aid, values={"throw_vx": -50.0e9, "throw_vy": 20.0e9})
    assert np.array_equal(h.sim.md.positions(), x0)
    assert np.allclose(h.sim.md.velocities()[0] * U.velocity_m_s, [-50.0, 20.0], atol=1e-9)
    assert frame(h)["at"][aid][:2] == pytest.approx([12.0, 9.0], abs=0.05)


def test_probe_and_piston_handles():
    h = Harness(V, "piston")
    h.cmd("scene", op="add", type="probe", values={"x": 6.0, "y": 4.0, "r": 2.0})
    pr = added(h, "probe")[0]["id"]
    pi = added(h, "piston")[0]["id"]
    h.cmd("scene", op=_op(), id=pr, values={"x": 3.0, "y": 5.0})
    f = frame(h)
    assert f["at"][pr] == [3.0, 5.0, 0.0]
    assert f["at"][pi][1] == pytest.approx(h.sim.md.piston()["X"] * NM)
    X = h.sim.md.piston()["X"] * NM
    h.cmd("scene", op=_op(), id=pi, values={"position": X + 1.0})
    assert not h.errors(), h.errors()
    assert h.sim.md.piston()["X"] * NM == pytest.approx(X + 1.0, abs=1e-5)


# --- at and meas (P16.2, P16.3) -----------------------------------------------------------------------------------------
def test_every_positioned_object_is_in_at_and_every_measurable_in_meas():
    """The piston preset with a thermometer and molecules: ``at`` has every particle object, the thermometer and the
    piston (nm, 3 numbers); ``meas`` has every measurable's id each frame (NaN only with a note); the measurables are
    well formed, Russian, sent in the scene message; their values agree with the engine's (T, ρ, the piston's X)."""
    h = Harness(V, None, {"dim": "3d", "Lx": 5.0, "Ly": 5.0, "Lz": 5.0, "boundary": "walls"})
    h.cmd("scene", op="add", type="molecule", values={"count": 20, "T": 200.0})
    h.cmd("scene", op="add", type="gas", values={"n": 30, "T": 200.0})
    h.cmd("scene", op="add", type="probe", values={"x": 2.5, "y": 2.5, "z": 2.5, "r": 1.5})
    h.cmd("scene", op="add", type="piston", values={"axis": "z", "position": 4.9})
    assert not h.errors(), h.errors()
    run(h, 0.5, 3)
    ms = h.sim.measurables()
    ids = [m["id"] for m in ms]
    assert len(set(ids)) == len(ids)
    for m in ms:
        assert isinstance(m["id"], str) and is_t(m["label"]) and is_t(m["unit"])
        assert m["of"] is None or m["of"] in h.sim.objects
        assert translated(m["label"]) and translated(m["unit"])
    sc = h.of("scene")[-1]
    if "measurables" in sc:
        assert [m["id"] for m in sc["measurables"]] == ids
    f = frame(h)
    for oid, o in h.sim.objects.items():
        assert oid in f["at"] and len(f["at"][oid]) == 3, o
    assert set(f["meas"]) == set(ids)
    for k, val in f["meas"].items():     # NaN travels as null (JSON)
        if val is None or not math.isfinite(val):
            assert k in f.get("meas_note", {}), k
    assert f["meas"]["T"] == pytest.approx(h.sim.md.temperature()["T"] * KELVIN)
    assert f["meas"]["rho"] == pytest.approx(h.sim.md.n / (h.sim.md.volume() * NM ** 3))
    pid = added(h, "piston")[0]["id"]
    assert f["meas"][f"{pid}.X"] == pytest.approx(h.sim.md.piston()["X"] * NM)
    mid = added(h, "molecule")[0]["id"]
    assert math.isfinite(f["meas"][f"{mid}.T_rot"])
    assert h.sim.measure().keys() == f["meas"].keys()


def test_meas_is_cheap():
    """The measurements of a frame (without the order parameter, computed with the statistics) cost little against the
    frame's computation: a 2-D gas of 2000 atoms."""
    h = Harness(V, None, {"Lx": 40.0, "Ly": 40.0})
    h.cmd("scene", op="add", type="gas", values={"n": 2000})
    h.cmd("scene", op="add", type="probe", values={"x": 20.0, "y": 20.0, "r": 5.0})
    run(h, 0.2, 2)
    t0 = time.perf_counter()
    for _ in range(5):
        h.sim._readings(full=False)
    per = (time.perf_counter() - t0) / 5
    t0 = time.perf_counter()
    h.sim.md.step(20)
    step = (time.perf_counter() - t0) / 20
    print(f"meas {per * 1e3:.2f} ms; step {step * 1e3:.2f} ms")
    assert per < 2.0 * step + 0.004, (per, step)


# --- the scene carried between a plane and a volume (P16.1) --------------------------------------------------------
def test_scene_carried_from_a_volume_into_a_plane_and_back():
    h = Harness(V, "molecules")
    h.cmd("scene", op="add", type="wall", values={"axis": "z", "side": "lo", "kind": "thermal"})
    h.cmd("scene", op="add", type="probe", values={"x": 2.0, "y": 2.0, "z": 2.0})
    h.cmd("scene", op="export")
    sc = h.of("scene_export")[-1]["scene"]
    laws = {**sc["laws"], "dim": "2d", "Lx": 14.0, "Ly": 14.0}
    w = Harness(V, None, {**laws, "scene": {**sc, "carry": True}})
    types = [o["type"] for o in w.sim.objects.values()]
    notes = [en(m["text"]) for m in w.of("notice")]
    assert "molecule" in types and "probe" in types and "wall" not in types, notes
    if any("carried into the new world" in t for t in notes):     # the framework's notice names what was not carried and why
        assert any("a plane has no axis z" in t.lower() for t in notes), notes
    run(w, 0.3, 2)
    assert not w.errors(), w.errors()
    w.cmd("scene", op="export")
    sc2 = w.of("scene_export")[-1]["scene"]
    back = Harness(V, None, {**sc2["laws"], "dim": "3d", "Lz": 8.0, "scene": {**sc2, "carry": True}})
    assert [o["type"] for o in back.sim.objects.values()] == [o["type"] for o in w.sim.objects.values()]


# --- all of it repeated by a restore -----------------------------------------------------------------------------------
def _world(params):
    viz = registry.load(V)
    p, errors = viz["schema"].resolve(None, params)
    assert not errors
    frames, script = [], []

    def emit(meta, blobs=None):
        if meta.get("type") == "frame":
            frames.append((meta, blobs))
            script.append({"frame": meta["t"]})
        elif meta.get("type") == "command":
            script.append({"t": meta["t"], "cmd": meta["cmd"], "args": meta["args"]})
    sim = viz["simulation"](p, 7, emit)
    return sim, Runner(sim, emit, queue.Queue()), frames, script


def test_live_box_switch_and_drags_are_replayed_by_a_restore():
    params = {"dim": "2d", "dynamics": "hard", "Lx": 30.0, "Ly": 30.0, "boundary": "walls"}
    sim, run_, frames, script = _world(params)
    run_._start_world()
    run_.handle({"cmd": "scene", "args": {"op": "add", "type": "gas", "values": {"n": 40, "x": 10.0, "y": 10.0,
                                                                                  "sx": 8.0, "sy": 8.0}}})
    run_._advance(0.5e-12)
    run_._frame(0.0)
    gid = next(iter(sim.objects))
    run_.handle({"cmd": "set", "args": {"values": {"box_mode": "wall", "Lx": 34.0}}})
    run_.handle({"cmd": "set", "args": {"values": {"dynamics": "forces", "model": "wca"}}})
    run_._advance(1.0e-12)
    run_._frame(0.0)
    run_.handle({"cmd": "scene", "args": {"op": _op(), "id": gid, "values": {"x": 20.0, "y": 15.0}}})
    run_.handle({"cmd": "set", "args": {"values": {"box_mode": "affine", "Ly": 28.0}}})
    run_._advance(1.5e-12)
    run_._frame(0.0)
    sim2, run2, frames2, _ = _world(params)
    run2.restore(1, list(script)[:-1], sim.t, lambda on: None)
    run2._frame(0.0)
    a, b = frames[-1], frames2[-1]
    assert np.array_equal(a[1]["q"], b[1]["q"]) and a[0]["box_nm"] == b[0]["box_nm"] and a[0]["at"] == b[0]["at"]
    assert sim2.live == sim.live and not sim2.hard
    # the whole engine state, not only the 16-bit drawing positions (review LB1-physics P11): positions, velocities,
    # the generator, energies, the books and the change of the box still running at the end
    assert sim.md.ramp_running() and same_world(sim2.md, sim.md.state_dict())
    run_._advance(2.5e-12)
    run2._advance(2.5e-12)
    assert same_world(sim2.md, sim.md.state_dict())
    # the negative control: one atom's velocity changed by one unit in the last place is seen
    st = sim.md.state_dict()
    st["v"] = st["v"].copy()
    st["v"][0, 0] = np.nextafter(st["v"][0, 0], np.inf)
    assert not same_world(sim2.md, st)


# --- the box over a time (review LB1-physics P3) -------------------------------------------------------------------
def test_live_box_over_a_time_is_a_ramp_with_its_work_and_an_end_event():
    """Lx 12 → 10.5 nm over 10 ps (affine): the change is said at once with the faces' speed against the thermal speed;
    the view gets the region it spans; mid-way the frames show an intermediate box; at the end an event states the
    work (booked step by step: equal to the first law's W_box), −∫P dV and the temperature, and the final box."""
    h = Harness(V, "maxwell")
    run(h, 1.0, 2)
    h.set(box_time_ps=10.0)
    W0 = h.sim.md.energy_balance()["W_box"]
    h.set(Lx=10.5)
    assert not h.errors(), h.errors()
    ev = en(h.of("event")[-1]["text"])
    assert "affinely in 10 ps" in ev and "the box's faces move" in ev and "thermal speed" in ev and translated(ev), ev
    assert h.of("box")[-1]["box"][1][0] == pytest.approx(12.0)          # the region the change spans
    run(h, 4.0, 4)
    f = frame(h)
    assert 10.5 < f["box_nm"][0] < 12.0 and h.sim.md.ramp_running()
    assert f["box_nm"][0] == pytest.approx(h.sim.md.L[0] * NM)
    run(h, 8.0, 4)
    md = h.sim.md
    assert not md.ramp_running() and md.L[0] * NM == pytest.approx(10.5) and h.sim.box[0] * NM == pytest.approx(10.5)
    end = [en(m["text"]) for m in h.of("event") if "the change of the box finished" in en(m.get("text", ""))]
    assert len(end) == 1 and "the work on the system W" in end[0] and "−∫P dV" in end[0] and "temperature" in end[0], end
    r = md.box_ramp()
    assert md.energy_balance()["W_box"] - W0 == pytest.approx(r["W"], rel=1e-9)
    assert h.of("box")[-1]["box"][1][0] == pytest.approx(10.5)
    assert frame(h)["box_nm"][0] == pytest.approx(10.5)
    assert not h.errors(), h.errors()


def test_a_new_size_stops_the_change_running_and_a_too_fast_one_is_refused():
    h = Harness(V, "maxwell")
    run(h, 0.5, 1)
    h.set(box_time_ps=20.0)
    h.set(Lx=11.0)
    run(h, 5.0, 2)
    L_mid = h.sim.md.L[0] * NM
    assert 11.0 < L_mid < 12.0
    h.set(Ly=11.0)                            # a new size while the first runs: it stops where it is, said
    ev = en(h.of("event")[-1]["text"])
    assert "the change of the box stopped (a new size was set)" in ev and translated(ev), ev
    r = h.sim.md.box_ramp()     # a new change from where the box is to both live sizes
    assert r["running"] and r["L0"][0] * NM == pytest.approx(L_mid, abs=0.02)
    assert np.allclose(np.array(r["L1"]) * NM, [11.0, 11.0])
    h.set(box_time_ps=0.01)
    n = len(h.errors())
    h.set(Lx=8.0)
    e = h.errors()[n:]
    assert e and "too fast" in en(e[-1]) and "at least" in en(e[-1]) and translated(en(e[-1])), e
    h.set(box_time_ps=30.0)
    h.set(Lx=1.5)                              # 300 atoms in 1.5 × 11 nm: beyond close packing at σ
    assert "close packing" in en(h.errors()[-1]) and translated(en(h.errors()[-1])), en(h.errors()[-1])


def test_switching_to_hard_spheres_stops_the_change_and_says_so():
    h = Harness(V, None, {"Lx": 30.0, "Ly": 30.0})
    h.cmd("scene", op="add", type="gas", values={"n": 30, "T": 300.0})
    h.set(box_time_ps=50.0, Lx=33.0)
    run(h, 2.0, 2)
    h.set(dynamics="hard")
    ev = [en(m["text"]) for m in h.of("event")][-1]
    if h.errors():
        assert "would overlap" in en(h.errors()[-1])
        return
    assert "the switch to hard spheres" in ev and "dynamics: hard" in ev, ev
    assert 30.0 < h.sim.md.L[0] * NM < 33.0


# --- the wall mode next to a soft wall (review LB1-physics P8) ----------------------------------------------------
def test_wall_mode_next_to_a_soft_wall_states_its_work():
    h = Harness(V, None, {"dim": "2d", "Lx": 6.0, "Ly": 6.0, "boundary": "walls"})
    h.cmd("scene", op="add", type="wall", values={"axis": "y", "side": "hi", "kind": "soft"})
    h.cmd("scene", op="add", type="gas", values={"n": 80, "T": 150.0, "x": 3.0, "y": 2.8, "sx": 5.0, "sy": 4.4})
    run(h, 2.0, 5)
    W0 = h.sim.md.energy_balance()["W_box"]
    h.set(box_mode="wall", Ly=6.15)
    assert not h.errors(), h.errors()
    W = h.sim.md.energy_balance()["W_box"] - W0
    ev = en(h.of("event")[-1]["text"])
    assert W != 0.0 and "the soft wall" in ev and "the work on the system W" in ev and "no work on the system" not in ev
    assert f"{abs(U.to_kJ_mol(W)):.3g}"[:4] in ev, ev
    # the control: specular walls over empty space - no work, said so
    g = Harness(V, None, {"dim": "2d", "Lx": 6.0, "Ly": 6.0, "boundary": "walls"})
    g.cmd("scene", op="add", type="gas", values={"n": 20, "T": 150.0, "x": 3.0, "y": 2.0, "sx": 5.0, "sy": 3.0})
    g.set(box_mode="wall", Ly=6.15)
    assert "no work on the system" in en(g.of("event")[-1]["text"])


# --- the bisection respects the bond limit (review LB1-physics P13) -----------------------------------------------
def test_the_size_named_after_an_overlap_respects_the_bond_limit(monkeypatch):
    """The bisection behind “now it can go to …” (``_box_refusal`` after an overlap) tries every size with the 10 % bond
    limit of the change itself (review P13), so the size it names is one the bonds allow. The engine checks the bonds
    at the asked size before the overlap, so in p03 an overlap refusal is reached only within the limit; the
    bisection is driven here directly with a 30 % change of a box with molecules: with the limit the named size stays
    within 10 % (the control: without it, the old call, it named 30 %)."""
    from lfphys.core.md.system import MD
    seen = []
    orig = MD.deform

    def spy(self, L, mode="affine", max_bond_strain=None):
        seen.append(max_bond_strain)
        return orig(self, L, mode=mode, max_bond_strain=max_bond_strain)
    h = Harness(V, None, {"Lx": 8.0, "Ly": 8.0})
    h.cmd("scene", op="add", type="molecule", values={"count": 20, "T": 100.0})
    assert not h.errors(), h.errors()
    monkeypatch.setattr(MD, "deform", spy)
    L0 = np.array(h.sim.box)
    L = L0 * np.array([0.7, 1.0])
    from lfphys.codes import coded
    from lfphys.i18n import T as T_
    over = coded(ValueError(T_("overlap: an inserted particle's potential energy {e:.4g} exceeds the limit {lim}", e=99.0,
                               lim=50.0)), "md.overlap")   # the engine's coded refusal (review i18n-code F5)
    e = h.sim._box_refusal(over, L, "affine")
    import re
    fit = float(re.search(r"Lx ≈ ([\d.]+) nm", english(text_of(e))).group(1))
    assert len(seen) == 10 and all(q == pytest.approx(0.10) for q in seen), seen
    assert 1.0 - fit / (L0[0] * NM) <= 0.10 + 1e-3, fit
    seen.clear()
    # the control: the same bisection without the limit names nearly the whole 30 %
    lo_t, hi_t = 0.0, 1.0
    st = h.sim.md.state_dict()
    for _ in range(10):
        mid = 0.5 * (lo_t + hi_t)
        try:
            orig(MD.from_state_dict(st), L0 + mid * (L - L0))
            lo_t = mid
        except ValueError:
            hi_t = mid
    assert lo_t > 0.9


# --- the switch keeps the region of the centres (review LB1-physics P4) -------------------------------------------
def test_switch_in_a_walled_box_keeps_the_region_of_the_centres():
    """A WCA gas in a walled box with atoms next to the walls: the switch to hard disks is not refused by the walls
    (both solvers' walls act on the centres), every position and the box are the same, the event says the density did
    not change; the hard world started as such has the same walls; back to forces nothing moves."""
    h = Harness(V, None, {"Lx": 6.0, "Ly": 6.0, "boundary": "walls", "model": "wca"})
    h.cmd("scene", op="add", type="gas", values={"n": 12, "T": 120.0})
    md = h.sim.md
    k = md.keys
    x = md.positions().copy()
    x[0] = [0.05, 3.0]                 # a centre 0.05 nm from the lo wall: the old switch refused this
    md.set(k[:1], x=x[:1])
    while True:
        from lfphys.core.md import hard as HD
        cv = HD.contact_violations(md.positions(), np.ones(md.n), md.L, md.periodic, walls_on="centre")
        if not cv["pairs"]:
            break
        run(h, 0.05, 1)
    x0 = h.sim.md.positions().copy()
    h.set(dynamics="hard")
    assert not h.errors(), h.errors()
    assert h.sim.md.walls_on == "centre" and np.array_equal(h.sim.md.positions(), x0)
    assert "the centres' region and the density did not change" in en(h.of("event")[-1]["text"])
    h.set(dynamics="forces")
    assert np.array_equal(h.sim.md.positions(), x0) and not h.errors()
    assert Harness(V, None, {"dynamics": "hard", "boundary": "walls"}).sim.md.walls_on == "centre"


# --- the throw in the world's units and its largest speed (review LB1-p02-ux X4) ------------------------------------
@pytest.mark.parametrize("dim,q", [("2d", 0.34), ("3d", 0.37)])
def test_the_largest_throw_is_resolved_by_the_default_step(dim, q):
    """The palette's velocity_max (500 m/s, in the world's nm/s) thrown on a 300 K argon gas: q = 12 v dt / r_t
    (the README's 0.34 in a plane, 0.37 in a volume, below Q_MAX = 0.4) and the world takes it; three times as fast is
    refused by the time step with what to change (the control)."""
    from p03_molecules import viz as P
    h = Harness(V, None, {"dim": dim, "Lx": 12.0, "Ly": 12.0, "Lz": 12.0})
    h.cmd("scene", op="add", type="gas", values={"n": 40, "T": 300.0})
    gid = added(h, "gas")[0]["id"]
    vm = h.of("header")[-1]["playground"]["palette"][0]["handles"]["velocity_max"]
    assert vm == pytest.approx(P.THROW_MAX_M_S * 1e9)
    nd = 2 if dim == "2d" else 3
    T = 300.0 / KELVIN
    vel = math.sqrt(nd * T) + P.THROW_MAX_M_S / U.velocity_m_s
    assert h.sim._step_q(vel, 0.5 * vel * vel, 1.0, 1.0, h.sim.md.dt) == pytest.approx(q, abs=0.005)
    h.cmd("scene", op=_op(), id=gid, values={"throw_vx": vm, **({"throw_vz": 0.0} if nd == 3 else {})})
    assert not h.errors(), h.errors()
    assert h.sim.objects[gid]["values"]["vx"] == pytest.approx(500.0)
    vc = h.sim.md.velocities().mean(axis=0)[0] * U.velocity_m_s
    assert vc == pytest.approx(500.0, rel=1e-9)
    h.cmd("scene", op="set", id=gid, values={"vx": 1500.0})
    e = en(h.errors()[-1])
    assert "does not resolve the atoms' collisions" in e and "Time step" in e and translated(e), e


# --- the scene carried into a new world with its state (review LB1-framework F5) ------------------------------------
def _new_world(h, **params):
    h.cmd("new_world", params={**h.sim.params, **h.sim.live_values(), **params, "scene": None}, carry=True)
    return [m for m in h.of("notice") if "carry" in m][-1]


def test_a_new_world_of_the_same_space_takes_the_atoms_as_they_are():
    """The reviewer's case: a 3-D argon gas, the boundary periodic → walls (a law that is not live), the same box. The
    atoms keep their places and velocities bit for bit, T and the energy at the same time are the old world's, the
    random generator continues; the notice says the gas went “with its state” and the world's state was taken over.
    The control (another space): into a plane the atoms are made again from the parameters, and the notice says why."""
    h = Harness(V, None, {"dim": "3d", "Lx": 12.0, "Ly": 12.0, "Lz": 12.0, "boundary": "periodic"})
    h.cmd("scene", op="add", type="gas", values={"n": 1500, "T": 300.0})
    gid = added(h, "gas")[0]["id"]
    run(h, 0.3, 2)
    md = h.sim.md
    x0, v0, K0, t0 = md.positions().copy(), md.velocities().copy(), md.kinetic_energy(), h.sim.t
    rng0 = md.rng.bit_generator.state
    note = _new_world(h, boundary="walls")
    md = h.sim.md
    assert h.sim.t == t0 and not md.periodic.any()
    assert np.array_equal(md.positions(), x0) and np.array_equal(md.velocities(), v0)
    assert md.rng.bit_generator.state == rng0
    from p03_molecules.viz import PS
    assert md.kinetic_energy() == K0 and md.t == pytest.approx(t0 * 1e12 / PS, rel=1e-12)   # the solver at the scene's t
    rows = {r["id"]: r for r in note["carry"]["objects"]}
    assert rows[gid]["how"] == "state" and note["carry"]["world"]["how"] == "state", note["carry"]
    assert "random sequence" in en(note["text"]) and "continues" in en(note["text"]), en(note["text"])
    run(h, 0.3, 2)
    assert not h.errors(), h.errors()
    g = Harness(V, None, {"dim": "3d", "Lx": 12.0, "Ly": 12.0, "Lz": 12.0})
    g.cmd("scene", op="add", type="gas", values={"n": 100, "T": 300.0})
    run(g, 0.1, 1)
    plane = _new_world(g, dim="2d")
    r = plane["carry"]["objects"][0]
    assert r["how"] == "restarted" and "another dimension" in en(plane["text"]), en(plane["text"])
    assert g.sim.md.n == 100 and g.sim.ndim == 2


def test_molecules_and_the_piston_carry_their_state():
    """Molecules (bonded pairs, 3-D) into a world with other boundaries: every atom at its place with its velocity,
    the bonds the same; the piston preset into the slab boundaries: the piston's face and velocity are the old ones."""
    h = Harness(V, "molecules")
    run(h, 0.3, 2)
    md = h.sim.md
    x0, v0, nb0 = md.positions().copy(), md.velocities().copy(), len(md.topology()["bonds"])
    note = _new_world(h, boundary="walls")
    md = h.sim.md
    assert np.array_equal(md.velocities(), v0) and len(md.topology()["bonds"]) == nb0, en(note["text"])
    assert note["carry"]["objects"][0]["how"] == "state", en(note["text"])
    L = md.L
    d = md.positions() - x0
    d -= L * np.rint(d / L)                       # the same place, or a whole molecule moved in from a face
    same = np.all(d == 0.0, axis=1)
    assert same.mean() > 0.6 and np.max(np.abs(d)) < 2.0, (same.mean(), np.max(np.abs(d)))
    if not same.all():
        assert "moved inside as a whole" in en(note["text"]), en(note["text"])
    run(h, 0.2, 2)
    assert not h.errors(), h.errors()

    p = Harness(V, "piston")
    run(p, 3.0, 3)
    pi = p.sim.md.piston()
    X, Vp = pi["X"], pi["V"]
    note = _new_world(p, boundary="slab")
    q = p.sim.md.piston()
    assert q is not None and q["X"] == X and q["V"] == Vp, (en(note["text"]), q)
    rows = {en(r["label"]): r["how"] for r in note["carry"]["objects"]}
    assert rows["Piston"] == "state" and rows["Argon"] == "state", rows


def test_a_smaller_box_starts_the_atoms_again_and_says_why():
    """The negative control: a new world whose box (here Lx 6 nm of 12) cuts through the gas: its atoms cannot stay
    where they were; the gas is made again from its parameters, and the notice names the reason."""
    h = Harness(V, None, {"Lx": 12.0, "Ly": 12.0, "boundary": "walls"})
    h.cmd("scene", op="add", type="gas", values={"n": 60, "T": 300.0})
    run(h, 0.2, 1)
    note = _new_world(h, Lx=6.0, boundary="slab")
    r = note["carry"]["objects"][0]
    assert r["how"] == "restarted" and "started anew from the parameters" in en(note["text"]), note
    assert np.max(h.sim.md.positions()[:, 0]) * NM <= 6.0
