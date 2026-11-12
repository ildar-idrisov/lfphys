# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Direct manipulation (plan P16.2) and the framework's parts of the instruments (P16.3) on the toy section of
``tests/playgrounds`` (the integrator's API of 2026-11-11):

* a palette type's ``handles`` are checked against its schema (list positions, velocities, sizes and the axis form with
  its three spellings of the axis) and sent in the header's palette;
* the scene op ``edit`` changes only the handles, through the section's edit path (``on_set``), applies every handle
  sent (also one equal to its stored value), is refused with a Russian text where the type has no handles, a parameter
  is not a handle or the section refuses (the scene then exactly as it was), and is repeated exactly by a restore and
  after a checkpoint;
* ``measurables()`` is sent in the scene message (entries that are not in the API's form dropped, a failure never
  breaking the scene), and the toy's frames carry ``at`` and ``meas``;
* the worker command ``checkpoint_now`` (integrator, 2026-11-11): always answered by a ``checkpoint`` message carrying
  the request's tag; a fresh file when the world changed, the latest file's message again when it did not; an error
  when no file can be given; never recorded as a command, never making the state stale, never resuming a run."""

import asyncio
import queue
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import checkpoint, protocol, registry
from lfviz.app import MGR, create_app
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, axis_index, check_handles
from lfviz.sim import Runner

HERE = Path(__file__).resolve().parent
WALL = ("cpu_ms", "speed_actual", "lag")


@pytest.fixture(autouse=True)
def _toy(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(HERE / "playgrounds"))


def _world(msgs, preset="two", values=None, seed=3, cls=None):
    viz = registry.load("p99_toy")
    sim_cls = cls or viz["simulation"]

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))

    def make_world(pr, vals, sd):
        p, errs = viz["schema"].resolve(pr, vals or {})
        if errs:
            raise ValueError("; ".join(errs))
        return sim_cls(p, 3 if sd in (None, "") else int(sd), emit), {"preset": pr}
    sim, _ = make_world(preset, values, seed)
    return sim, Runner(sim, emit, queue.Queue(), make_world=make_world)


def _of(msgs, typ):
    return [m for m, _ in msgs if m.get("type") == typ]


def _bytes(msgs):
    return [protocol.encode({k: v for k, v in m.items() if k not in WALL}, b) for m, b in msgs]


def _edit(run, oid, values):
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": oid, "values": values}})


# --- handles ------------------------------------------------------------------------------------------------------
def test_handles_are_checked_against_the_type_and_sent_in_the_palette():
    sch = Schema([Param("x", "x", "float", 0.0), Param("y", "y", "float", 0.0), Param("z", "z", "float", 0.0),
                  Param("vx", "vx", "float", 0.0), Param("vy", "vy", "float", 0.0), Param("vz", "vz", "float", 0.0),
                  Param("r", "r", "float", 1.0), Param("name", "имя", "select", "a", options=[("a", "a")]),
                  Param("ax", "ось", "select", "x", options=[("x", "x"), ("y", "y"), ("z", "z")]),
                  Param("axn", "ось", "select", 0, options=[(0, "x"), (1, "y"), (2, "z")]),
                  Param("axs", "ось", "select", "0", options=[("0", "x"), ("1", "y"), ("2", "z")])])
    ok = check_handles({"position": ["x", "y", "z"], "velocity": ["vx", "vy", "vz"], "size": "r"}, sch)
    assert ok == {"position": ["x", "y", "z"], "velocity": ["vx", "vy", "vz"], "size": "r"}
    assert check_handles({"position": ["x", "y"]}, sch) == {"position": ["x", "y"]}
    # the largest speed the world carries: a number or a parameter's id (integrator, 2026-11-11)
    assert check_handles({"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_max": 3}, sch)["velocity_max"] == 3.0
    assert check_handles({"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_max": "r"}, sch)["velocity_max"] == "r"
    for bad in ({"position": ["x", "y"], "velocity_max": 3.0}, {"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_max": -1},
                {"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_max": float("inf")},
                {"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_max": "name"},
                {"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_max": True}):
        with pytest.raises(ValueError):
            check_handles(bad, sch)
    # the unit a throw is shown in (integrator, 2026-11-12): {unit, factor > 0}, with a velocity
    vd = {"position": ["x", "y"], "velocity": ["vx", "vy"], "velocity_display": {"unit": " м/с ", "factor": 1e-9}}
    assert check_handles(vd, sch)["velocity_display"] == {"unit": "м/с", "factor": 1e-9}
    for bad_vd in ({"unit": "м/с"}, {"unit": "", "factor": 1.0}, {"unit": "м/с", "factor": 0}, {"unit": "м/с", "factor": -2},
                   {"unit": "м/с", "factor": float("nan")}, {"unit": "м/с", "factor": True}, {"unit": 5, "factor": 1.0},
                   {"unit": "м/с", "factor": 1.0, "offset": 3}, "м/с", {"unit": "x" * 30, "factor": 1.0}):
        with pytest.raises(ValueError):
            check_handles({**vd, "velocity_display": bad_vd}, sch)
    with pytest.raises(ValueError):  # without a velocity
        check_handles({"position": ["x", "y"], "velocity_display": {"unit": "м/с", "factor": 1.0}}, sch)
    for axp in ("ax", "axn", "axs"):  # the three spellings of an axis (integrator, 2026-11-11)
        assert check_handles({"position": {"param": "x", "axis_param": axp}}, sch)["position"]["axis_param"] == axp
    assert [axis_index(v) for v in ("x", "y", "z", 0, 1, 2, "0", "1", "2")] == [0, 1, 2] * 3
    assert [axis_index(v) for v in ("w", 3, "3", True, None, 1.5)] == [None] * 6
    # negative controls: every malformed declaration is a definition error
    for bad in ({"position": ["x", "q"]}, {"position": ["x"]}, {"position": ["x", "y", "z", "vx"]},
                {"position": ["x", "name"]}, {"position": ["x", "y"], "velocity": ["vx", "vy", "vz"]},
                {"velocity": ["vx", "vy"]}, {"position": ["x", "y"], "size": "name"}, {"position": ["x", "x"]},
                {"position": ["x", "y"], "velocity": ["x", "vy"]}, {"position": {"param": "x", "axis_param": "name"}},
                {"position": {"param": "name", "axis_param": "ax"}}, {"position": {"param": "x"}},
                {"position": {"param": "x", "axis_param": "ax"}, "velocity": ["vx"]}, {"grip": ["x", "y"]}, ["x"]):
        with pytest.raises(ValueError):
            check_handles(bad, sch)
    with pytest.raises(ValueError):
        ObjectType("t", "T", "body", sch, handles={"position": ["x", "nope"]})
    ot = ObjectType("t", "T", "body", sch, handles={"position": ["x", "y"]})
    assert ot.to_json()["handles"] == {"position": ["x", "y"]} and ot.handle_ids() == ["x", "y"]
    assert "handles" not in ObjectType("u", "U", "body", sch).to_json()  # no handles: nothing sent
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    pal = {p["type"]: p for p in _of(msgs, "header")[-1]["playground"]["palette"]}
    assert pal["particle"]["handles"] == {"position": ["x", "y", "z"], "velocity": ["vx", "vy", "vz"], "size": "r",
                                          "velocity_max": "vmax"}
    assert pal["probe"]["handles"] == {"position": ["x", "y"]}
    assert pal["wall"]["handles"] == {"position": {"param": "position", "axis_param": "axis"}}
    assert pal["cloud"]["handles"]["velocity_display"] == {"unit": "см/с", "factor": 100.0}


def test_a_throw_is_logged_in_the_unit_the_type_shows():
    """``velocity_display`` (integrator, 2026-11-12): the log shows the throw in the declared unit, the edit and the
    world stay in world units. Negative control: a type without it logs the parameter's unit."""
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "cloud", "values": {"x": 0.0, "y": 1.0}}})
    cid = _of(msgs, "scene")[-1]["objects"][-1]["id"]
    _edit(run, cid, {"x": 0.5, "y": 1.0, "vx": 0.25, "vy": -1.5})
    assert sim.objects[cid]["values"]["vx"] == 0.25 and list(sim.clouds[cid][1]) == [0.25, -1.5]  # world units (m/s)
    assert _of(msgs, "event")[-1]["text"] == "«Облако точек 1»: перемещение в (0,5; 1) м; бросок: v = (25; −150) см/с"
    _edit(run, "o1", {"x": 0.0, "y": 0.0, "z": 0.0, "vx": 0.25, "vy": 0.0, "vz": 0.0})
    assert _of(msgs, "event")[-1]["text"].endswith("бросок: v = (0,25; 0; 0) м/с")


# --- the edit -------------------------------------------------------------------------------------------------------
def test_a_drag_moves_and_a_throw_sets_the_velocity_at_the_current_moment():
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    run._advance(0.4)
    _edit(run, "o1", {"x": 2.0, "y": -1.5, "z": 0.75})
    assert list(sim.state["o1"][[0, 1, 4]]) == [2.0, -1.5, 0.75] and list(sim.state["o1"][[2, 3, 5]]) == [1.0, 0.0, 0.0]
    ev = _of(msgs, "event")[-1]
    assert ev["kind"] == "scene" and ev["name"] == "edit" and ev["args"]["id"] == "o1"
    # the log line in the player's short form with the parameters' unit (review LB1-F13, LB1-p02-ux X12): a noun, no
    # labels inside the brackets, the Russian number format (decimal comma, the minus sign −)
    assert ev["text"] == "«Частица 1»: перемещение в (2; −1,5; 0,75) м"
    assert _of(msgs, "command")[-1]["args"]["op"] == "edit" and _of(msgs, "command")[-1]["t"] == pytest.approx(0.4)
    _edit(run, "o1", {"x": 1.0, "y": 1.0, "z": 0.0, "vx": -0.5, "vy": 2.0, "vz": 0.25})
    assert list(sim.state["o1"]) == [1.0, 1.0, -0.5, 2.0, 0.0, 0.25]
    assert _of(msgs, "event")[-1]["text"] == "«Частица 1»: перемещение в (1; 1; 0) м; бросок: v = (−0,5; 2; 0,25) м/с"
    run._advance(0.6)
    run._frame(0.0)
    f = _of(msgs, "frame")[-1]
    assert f["at"]["o1"] == pytest.approx([1.0 - 0.5 * 0.2, 1.0 + 2.0 * 0.2, 0.25 * 0.2])
    # the probe: a 2-D handle in the plane z = 0
    _edit(run, "o3", {"x": -2.0, "y": 3.0})
    run._frame(0.0)
    assert _of(msgs, "frame")[-1]["at"]["o3"] == [-2.0, 3.0, 0.0]


def test_a_throw_faster_than_the_world_carries_is_clamped():
    """``velocity_max`` (the toy particle's own parameter ``vmax``, 12 m/s): a throw above it is clamped, its direction
    kept, and the log says so («ограничено до …»), also when the player clamped it already (``asked``: what the hand
    gave). Negative control: a throw below it is applied as sent."""
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    _edit(run, "o1", {"x": 0.0, "y": 0.0, "z": 0.0, "vx": 30.0, "vy": 40.0, "vz": 0.0})
    v = sim.state["o1"][[2, 3, 5]]
    assert v == pytest.approx([7.2, 9.6, 0.0]) and sim.objects["o1"]["values"]["vx"] == pytest.approx(7.2)
    assert _of(msgs, "event")[-1]["text"].endswith("— ограничено наибольшей скоростью 12 м/с (рука дала 50; уменьшите "
                                                   "масштаб броска)")
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o2", "values": {"x": 1.0, "y": 0.0, "z": 0.0, "vx": 12.0,
                                                                                "vy": 0.0, "vz": 0.0}, "asked": 31.5}})
    assert sim.state["o2"][2] == 12.0 and _of(msgs, "event")[-1]["text"].endswith(
        "— ограничено наибольшей скоростью 12 м/с (рука дала 31,5; уменьшите масштаб броска)")
    # the player's clamped speed rounded a hair above the largest one is clamped here again: the log names the hand's
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o2", "values": {"x": 1.0, "y": 0.0, "z": 0.0, "vx": 12.0004,
                                                                                "vy": 0.0, "vz": 0.0}, "asked": 50.0}})
    assert sim.state["o2"][2] == 12.0 and "(рука дала 50;" in _of(msgs, "event")[-1]["text"]
    # review LB1-F13: a clamp is said only when one happened. A throw below the largest speed with an ``asked`` above it
    # (nothing clamped), an infinite or a non-number ``asked``: applied as sent, no clamp in the log
    for asked in (31.5, float("inf"), "много", -3.0):
        run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o2", "values": {"x": 1.0, "y": 0.0, "z": 0.0,
                                                                                    "vx": 6.0, "vy": 0.0, "vz": 0.0},
                                             "asked": asked}})
        ev = _of(msgs, "event")[-1]["text"]
        assert sim.state["o2"][2] == 6.0 and "ограничено" not in ev and ev.endswith("бросок: v = (6; 0; 0) м/с"), asked
    run.handle({"cmd": "scene", "args": {"op": "set", "id": "o2", "values": {"vmax": 100.0}}})
    _edit(run, "o2", {"x": 1.0, "y": 0.0, "z": 0.0, "vx": 30.0, "vy": 40.0, "vz": 0.0})
    assert list(sim.state["o2"][[2, 3, 5]]) == [30.0, 40.0, 0.0] and "ограничено" not in _of(msgs, "event")[-1]["text"]


def test_an_edit_applies_a_value_equal_to_the_stored_one():
    """The stored position of a moving object is where it was set: a drag back onto it must move the body (the
    section's on_set sees such a handle as changed: ``old`` holds None for it). Negative control: ``set`` with the stored
    value changes nothing — the reason the edit cannot be a plain ``set``."""
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    run._advance(1.0)
    assert sim.state["o1"][0] == pytest.approx(0.0)  # x = -1 + 1 * 1
    run.handle({"cmd": "scene", "args": {"op": "set", "id": "o1", "values": {"x": -1.0}}})
    assert sim.state["o1"][0] == pytest.approx(0.0)  # the control: nothing happened
    _edit(run, "o1", {"x": -1.0, "y": 0.0, "z": 0.0})
    assert sim.state["o1"][0] == -1.0
    seen = []

    class Spy(registry.load("p99_toy")["simulation"]):
        def on_set(self, obj, old):
            seen.append((dict(obj["values"]), dict(old)))
            super().on_set(obj, old)
    m2 = []
    s2, r2 = _world(m2, cls=Spy)
    r2._start_world()
    _edit(r2, "o1", {"x": -1.0, "y": 0.5, "z": 0.0})
    new, old = seen[-1]
    assert old["x"] is None and old["z"] is None and old["y"] == 0.0 and old["vx"] == 1.0 and new["y"] == 0.5


def test_refused_edits_leave_the_scene_exactly_as_it_was():
    viz = registry.load("p99_toy")
    base = viz["simulation"]

    class WithFixed(base):
        PALETTE = {**base.PALETTE, "post": ObjectType("post", "Столб", "body",
                                                      Schema([Param("x", "x", "float", 0.0), Param("h", "h", "float", 1.0)]))}
    msgs = []
    sim, run = _world(msgs, cls=WithFixed)
    run._start_world()
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "post", "values": {}}})
    post = _of(msgs, "scene")[-1]["objects"][-1]["id"]
    before = ({k: dict(o["values"]) for k, o in sim.objects.items()}, {k: v.copy() for k, v in sim.state.items()}, sim.rev)
    n_err = len(_of(msgs, "error"))
    cases = [
        ("o1", {"mass": 5.0}, "только положение и скорость, а не «масса»"),          # not a handle
        ("o1", {"x": 9.0, "y": 0.0, "z": 0.0}, "вне области игрушки"),              # the section refuses (Refusal)
        ("o1", {"x": "abc"}, "не число"),                                           # the schema refuses
        ("o3", {"x": 1.0, "vx": 2.0}, "а не «vx»"),                                 # a probe has no velocity
        (post, {"x": 1.0}, "нельзя перетаскивать"),                                 # a type without handles
        ("o1", {}, "без новых значений"),
        ("o999", {"x": 1.0}, "нет объекта"),
    ]
    for oid, vals, why in cases:
        _edit(run, oid, vals)
        assert why in _of(msgs, "error")[-1]["text"], (oid, vals, _of(msgs, "error")[-1]["text"])
    assert len(_of(msgs, "error")) == n_err + len(cases)
    after = ({k: dict(o["values"]) for k, o in sim.objects.items()}, {k: v.copy() for k, v in sim.state.items()}, sim.rev)
    assert after[0] == before[0] and after[2] == before[2] and all((after[1][k] == before[1][k]).all() for k in before[1])
    assert _of(msgs, "error")[-6]["text"].startswith("Сцена не изменена: «Частица 1»: точка вне области игрушки")
    assert "Что изменить: отпустите объект внутри области" in _of(msgs, "error")[-6]["text"]


def test_an_axis_bound_handle_moves_along_its_axis_in_all_three_spellings():
    msgs = []
    sim, run = _world(msgs, "empty")
    run._start_world()
    for typ, axis in (("wall", "y"), ("mirror", 2), ("screen", "0")):
        run.handle({"cmd": "scene", "args": {"op": "add", "type": typ, "values": {"axis": axis}}})
    ids = [o["id"] for o in _of(msgs, "scene")[-1]["objects"]]
    for oid, x in zip(ids, (1.25, -2.5, 4.0)):
        _edit(run, oid, {"position": x})
    run._frame(0.0)
    at = _of(msgs, "frame")[-1]["at"]
    assert at[ids[0]] == [0.0, 1.25, 0.0] and at[ids[1]] == [0.0, 0.0, -2.5] and at[ids[2]] == [4.0, 0.0, 0.0]
    assert _of(msgs, "event")[-1]["text"] == "«Экран (отражает; ось — номер текстом) 1»: перемещение: x = 4 м"
    _edit(run, ids[0], {"axis": "x"})  # the axis is not a handle: refused
    assert "а не «Ось»" in _of(msgs, "error")[-1]["text"] and sim.objects[ids[0]]["values"]["axis"] == "y"
    # the wall reflects a particle crossing it (its physics follows the edit)
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"y": 0.0, "vy": 1.0, "vx": 0.0}}})
    pid = _of(msgs, "scene")[-1]["objects"][-1]["id"]
    run._advance(2.0)
    assert sim.state[pid][1] == pytest.approx(2 * 1.25 - 2.0) and sim.state[pid][3] == -1.0


def _session(run):
    """Edits and throws between irregular frames (the kick draws random numbers)."""
    for i, dt in enumerate([0.13, 0.07, 0.21, 0.05, 0.17, 0.11]):
        run._advance(run.sim.t + dt)
        run._frame(0.0)
        if i == 1:
            _edit(run, "o2", {"x": -0.5, "y": 1.25, "z": 0.5})
        if i == 2:
            _edit(run, "o1", {"x": 0.25, "y": 0.0, "z": -0.5, "vx": 0.0, "vy": -1.5, "vz": 0.5})
        if i == 3:
            _edit(run, "o1", {"x": 99.0, "y": 0.0, "z": 0.0})  # refused: repeated as refused
        if i == 4:
            _edit(run, "o3", {"x": 1.0, "y": -1.0})


def test_a_restore_and_a_checkpoint_repeat_the_edits_exactly(tmp_path):
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    _session(run)
    assert sum(1 for c in _of(msgs, "command") if c["args"].get("op") == "edit") == 4
    script = [{"frame": m["t"]} if m["type"] == "frame" else {"t": m["t"], "cmd": m["cmd"], "args": m["args"]}
              for m, _ in msgs if m["type"] in ("frame", "command")]
    m2 = []
    _, run2 = _world(m2)
    run2.restore(1, script, sim.t, lambda on: None)
    assert all((run2.sim.state[k] == sim.state[k]).all() for k in sim.state)
    assert _bytes(m2) == _bytes(msgs)
    # a checkpoint after the edits: the world continued from it emits what the original emits
    run.ckpt_dir, run.ckpt_dirty = tmp_path, True
    run.checkpoint("test")
    run.ckpt_writer.wait()
    n0 = len(msgs)
    _session(run)
    ck = [m for m, _ in msgs[:n0] if m["type"] == "checkpoint"][-1]
    m3 = []
    state = checkpoint.loads((tmp_path / ck["file"]).read_bytes(), lambda m, b=None: m3.append((m, b)))
    run3 = Runner(state["sim"], state["sim"].emit, queue.Queue())
    run3.restore_from(state, [], state["sim"].t, lambda on: None)
    _session(run3)
    assert _bytes(m3) == _bytes(msgs[n0:])


# --- measurables ------------------------------------------------------------------------------------------------------
def test_measurables_go_with_the_scene_and_their_values_with_the_frames():
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    sc = _of(msgs, "scene")[-1]
    ids = [m["id"] for m in sc["measurables"]]
    assert ids == ["ke", "visits", "speed.o1", "speed.o2", "near.o3"]
    assert sc["measurables"][0] == {"id": "ke", "label": "Кинетическая энергия частиц", "unit": "Дж", "of": None}
    assert sc["measurables"][-1]["of"] == "o3" and sc["measurables"][-1]["group"] == "Датчики"
    run.handle({"cmd": "scene", "args": {"op": "remove", "id": "o2"}})
    assert [m["id"] for m in _of(msgs, "scene")[-1]["measurables"]] == ["ke", "visits", "speed.o1", "near.o3"]
    run._frame(0.0)
    f = _of(msgs, "frame")[-1]
    assert f["meas"]["ke"] == pytest.approx(0.5) and f["meas"]["speed.o1"] == pytest.approx(1.0) and "near.o3" in f["meas"]
    run.handle({"cmd": "scene", "args": {"op": "remove", "id": "o1"}})
    run._frame(0.0)
    assert _of(msgs, "frame")[-1]["meas_note"] == {"near.o3": "частиц нет"}
    # the framework keeps the scene whole: entries not in the API's form are dropped, a failure sends none
    base = registry.load("p99_toy")["simulation"]

    class Bad(base):
        def measurables(self):
            return [{"id": "ok", "label": "Хорошая", "unit": "м", "of": None}, {"id": 5, "label": "x", "unit": ""},
                    {"id": "noLabel", "unit": ""}, {"id": "o", "label": "y", "unit": "", "of": 3}, "text"]

    class Broken(base):
        def measurables(self):
            raise RuntimeError("сломано")
    m2 = []
    _, r2 = _world(m2, cls=Bad)
    r2._start_world()
    assert _of(m2, "scene")[-1]["measurables"] == [{"id": "ok", "label": "Хорошая", "unit": "м", "of": None}]
    m3 = []
    _, r3 = _world(m3, cls=Broken)
    r3._start_world()
    assert "measurables" not in _of(m3, "scene")[-1] and len(_of(m3, "scene")[-1]["objects"]) == 3


# --- checkpoint_now -------------------------------------------------------------------------------------------------
def test_checkpoint_now_always_answers_with_the_tag(tmp_path):
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    # no folder for checkpoints: answered with an error, still carrying the tag
    run.handle({"cmd": "checkpoint_now", "args": {"tag": "a0"}})
    ck = _of(msgs, "checkpoint")[-1]
    assert ck["tag"] == "a0" and ck["error"] and "file" not in ck
    run.ckpt_dir = tmp_path
    run._advance(0.3)
    run.handle({"cmd": "checkpoint_now", "args": {"tag": "a1"}})
    run.ckpt_writer.wait()
    c1 = _of(msgs, "checkpoint")[-1]
    assert c1["tag"] == "a1" and c1["reason"] == "request" and (tmp_path / c1["file"]).is_file() and not run.ckpt_dirty
    # nothing changed: the same file's message again, with the new tag
    run.handle({"cmd": "checkpoint_now", "args": {"tag": "a2"}})
    c2 = _of(msgs, "checkpoint")[-1]
    assert c2["tag"] == "a2" and c2["file"] == c1["file"] and c2["t"] == c1["t"] and not run.ckpt_dirty
    # not a change of the world: no command recorded, the state not stale
    assert not [c for c in _of(msgs, "command") if c["cmd"] == "checkpoint_now"]
    # the world changed: a fresh file of this state; a periodic checkpoint after it is not written again (not dirty)
    run._advance(0.5)
    run.handle({"cmd": "checkpoint_now", "args": {"tag": "a3"}})
    run.ckpt_writer.wait()
    c3 = _of(msgs, "checkpoint")[-1]
    assert c3["file"] != c1["file"] and c3["t"] == pytest.approx(0.5) and (tmp_path / c3["file"]).is_file()
    n = len(_of(msgs, "checkpoint"))
    run.checkpoint("periodic")
    assert len(_of(msgs, "checkpoint")) == n
    # the file is the state: a world continued from it goes on as the original does
    m2 = []
    state = checkpoint.loads((tmp_path / c3["file"]).read_bytes(), lambda m, b=None: m2.append((m, b)))
    run2 = Runner(state["sim"], state["sim"].emit, queue.Queue())
    run2.restore_from(state, [], state["sim"].t, lambda on: None)
    n0 = len(msgs)
    _session(run)
    _session(run2)
    assert _bytes(m2) == _bytes(msgs[n0:])
    # a world whose state cannot be pickled: an error with the tag
    run.ckpt_failed = run.world
    run.handle({"cmd": "checkpoint_now", "args": {"tag": "a4"}})
    assert _of(msgs, "checkpoint")[-1]["tag"] == "a4" and _of(msgs, "checkpoint")[-1]["error"]


def test_checkpoint_now_through_a_worker_and_never_resuming(tmp_path):
    async def go():
        app = create_app(tmp_path, max_workers=1, idle_pause=60, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            mgr = app[MGR]
            rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 2})).json())["id"]
            run = mgr.get(rid)
            await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
            await asyncio.sleep(1.0)

            def tagged(tag):
                cache = {}
                for e in run.entries:
                    if e.kind == "checkpoint":
                        m = protocol.peek_meta(run._read(e, cache))
                        if m.get("tag") == tag:
                            return m
                return None
            run.command({"cmd": "checkpoint_now", "args": {"tag": "sweep-1"}}, "test")
            for _ in range(200):
                if tagged("sweep-1"):
                    break
                await asyncio.sleep(0.05)
            m = tagged("sweep-1")
            assert m and m["world"] == 1
            path = run.ckpt_dir / m["file"]
            for _ in range(200):  # the file is written by the worker's background writer
                if path.is_file():
                    break
                await asyncio.sleep(0.05)
            assert path.is_file() and checkpoint.loads(path.read_bytes(), lambda *a: None)["sim"].t == pytest.approx(m["t"])
            kinds = [protocol.peek_meta(run._read(e, {})) for e in run.entries if e.kind == "command"]
            assert not [k for k in kinds if k.get("cmd") == "checkpoint_now"]
            # a viewer cannot send it (review LB1-F6: only the server's sweeps do, through Run.command): refused with 403,
            # and a suspended run is not resumed by the refused request
            r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": "checkpoint_now", "args": {"tag": "viewer"}})
            assert r.status == 403 and "error" in await r.json()
            await cl.post(f"/api/runs/{rid}/stop", json={})
            assert run.meta["state"] == "suspended"
            r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": "checkpoint_now", "args": {"tag": "x"}})
            assert r.status == 403 and not run.running and run.meta["state"] == "suspended"
            assert not tagged("viewer") and not tagged("x")
    asyncio.run(go())


def test_the_log_lines_and_numbers_are_in_the_players_form():
    """Reviews LB1-F13, LB1-p02-ux X6, X12: the scene's log lines are short (a label without its explanation in brackets,
    a select by its option's name, the unit), and every number has one Russian form, the player's (``ui.js`` ``num``):
    a decimal comma also in the mantissa of m·10ⁿ, the minus sign −. Negative control: the Python form is not it."""
    from lfviz.playground import fmt
    assert fmt(-0.137, 3) == "−0,137" and fmt(3.25e13, 3) == "3,25·10¹³" and fmt(1e14) == "1·10¹⁴"
    assert fmt(-9.76e12, 3) == "−9,76·10¹²" and fmt(9.99996e-5) == "1·10⁻⁴" and fmt(0) == "0" and fmt(2.0) == "2"
    assert fmt(12345.6, 6) == "12\u00a0345,6" and fmt(1234.56) == "1235" and fmt(-0.5) == "−0,5"
    assert fmt(float("nan")) == "—" and fmt(-float("inf")) == "−∞" and f"{-0.137:.3g}" != fmt(-0.137, 3)
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    run.handle({"cmd": "scene", "args": {"op": "set", "id": "o1", "values": {"kick": 0.25, "vmax": 20.0}}})
    assert _of(msgs, "event")[-1]["text"] == "«Частица 1»: толчок = 0,25; Наибольшая скорость броска = 20 м/с"
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "wall", "values": {"axis": "x"}}})
    wid = _of(msgs, "scene")[-1]["objects"][-1]["id"]
    run.handle({"cmd": "scene", "args": {"op": "set", "id": wid, "values": {"axis": "y", "position": -1.5e-5}}})
    assert _of(msgs, "event")[-1]["text"] == "«Стенка (отражает) 1»: Положение = −1,5·10⁻⁵ м; Ось: y"
    # a no-op set logs nothing (no empty line in «События»)
    n = len(_of(msgs, "event"))
    run.handle({"cmd": "scene", "args": {"op": "set", "id": wid, "values": {"axis": "y"}}})
    assert len(_of(msgs, "event")) == n
