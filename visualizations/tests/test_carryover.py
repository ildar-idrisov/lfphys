# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A new world that keeps the scene (plan P16.1, «перенести сцену»; the integrator's API of 2026-11-11, §5), on the toy
section of ``tests/playgrounds``: ``new_world`` with ``carry`` exports the current world (its objects with their state,
the time) into the new world's initial scene, re-adds each object through ``place`` and the add path, skips the
objects the new world refuses and names them in a notice («не перенесены: …»). The carried scene is the new world's
parameter (its header holds it), so a restore — from a checkpoint, or by replay from the header — rebuilds the very
same world; negative controls: without ``carry`` the new world starts empty, and a world refused as a whole leaves the
previous one going on (also when the refusal is repeated by a restore)."""

import asyncio
import hashlib
import queue
from pathlib import Path

import numpy as np
import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import playground as PG
from lfviz import protocol, registry
from lfviz.app import MGR, create_app
from lfviz.i18n import T
from lfviz.i18n import english as E
from lfviz.sim import Runner

HERE = Path(__file__).resolve().parent
WALL = ("cpu_ms", "speed_actual", "lag")


@pytest.fixture(autouse=True)
def _toy(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(HERE / "playgrounds"))


def _world(msgs, preset="two", values=None, seed=3):
    viz = registry.load("p99_toy")

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))

    def make_world(pr, vals, sd):
        p, errs = viz["schema"].resolve(pr, vals or {})
        if errs:
            raise ValueError("; ".join(errs))
        return viz["simulation"](p, 3 if sd in (None, "") else int(sd), emit), {"preset": pr}
    sim, _ = make_world(preset, values, seed)
    return sim, Runner(sim, emit, queue.Queue(), make_world=make_world), make_world


def _of(msgs, typ):
    return [m for m, _ in msgs if m.get("type") == typ]


def _bytes(msgs):
    return [protocol.encode({k: v for k, v in m.items() if k not in WALL}, b) for m, b in msgs]


def _build(run):
    """A scene worth carrying: moved particles, one lifted off the plane z = 0, a wall and a mirror."""
    run._advance(0.35)
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"x": 2.0, "y": 1.0, "z": 0.8,
                                                                                   "vz": 0.1, "kick": 0.2}}})
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "wall", "values": {"axis": "y", "position": 4.0}}})
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "mirror", "values": {"axis": 2, "position": -2.0}}})
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o1", "values": {"x": -0.5, "y": 0.5, "z": 0.0,
                                                                                "vx": 0.5, "vy": 0.25, "vz": 0.0}}})
    run._advance(0.6)
    run._frame(0.0)


def test_the_scene_carries_over_to_a_new_world_with_other_laws():
    msgs = []
    sim, run, _ = _world(msgs)
    run._start_world()
    _build(run)
    old = {E(o["label"]): (dict(o["values"]), sim.object_state(o)) for o in sim.objects.values()}
    n0 = len(msgs)
    run.handle({"cmd": "new_world", "args": {"params": {"drag": 0.5, "ndim": 3}, "seed": 7, "carry": True}})
    new = run.sim
    assert run.world == 2 and new is not sim and new.params["drag"] == 0.5
    head = _of(msgs[n0:], "header")[0]
    assert head["params"]["scene"]["carry"] is True and head["t"] == pytest.approx(0.6)  # the world's time goes on
    assert [o["type"] for o in head["params"]["scene"]["objects"]] == ["particle", "particle", "probe", "particle",
                                                                        "wall", "mirror"]
    assert {E(o["label"]): (dict(o["values"]), new.object_state(o)) for o in new.objects.values()} == old
    note = [m for m in _of(msgs[n0:], "notice") if "The scene was carried" in E(m["text"])][0]
    # what went how (review LB1-F5): the particles with their state, the probe and the walls by their parameters (no
    # state of their own), the world's own state (the toy's visits) carried
    assert E(note["text"]) == ("The scene was carried into the new world: all objects (6). With their state — "
                               "“Particle 1”, “Particle 2”, “Particle 3”. By their parameters (no state of their own) — "
                               "“Probe 1”, “Wall (reflects) 1”, “Mirror (reflects; the axis is a number) 1”. The world's "
                               "state carried over") and note["not_carried"] == 0
    assert [(o["id"], o["was"], o["how"]) for o in note["carry"]["objects"]] == [
        ("o1", "o1", "state"), ("o2", "o2", "state"), ("o3", "o3", "params"), ("o4", "o4", "state"),
        ("o5", "o5", "params"), ("o6", "o6", "params")]
    assert note["carry"]["world"] == {"how": "state", "notes": []} and (new.visits == sim.visits).all()
    # the command recorded is small (the scene is in the new world's header, not in the command)
    cmd = [c for c in _of(msgs[n0:], "command") if c["cmd"] == "new_world"][0]
    assert cmd["args"] == {"params": {"drag": 0.5, "ndim": 3}, "seed": 7, "carry": True}
    # the new world is computed by its laws from the carried state
    run._advance(1.0)
    assert new.state["o1"][2] == pytest.approx(old["Particle 1"][1]["xv"][2] * __import__("math").exp(-0.5 * 0.4))


def test_objects_the_new_world_refuses_are_named_and_the_rest_carried():
    msgs = []
    sim, run, _ = _world(msgs)
    run._start_world()
    _build(run)
    n0 = len(msgs)
    run.handle({"cmd": "new_world", "args": {"params": {"ndim": 2}, "carry": True}})
    assert run.world == 2 and run.sim.ndim == 2
    kept = [E(o["label"]) for o in run.sim.objects.values()]
    assert kept == ["Particle 1", "Particle 2", "Probe 1", "Wall (reflects) 1"]
    note = [m for m in _of(msgs[n0:], "notice") if "The scene was carried" in E(m["text"])][0]
    text = E(note["text"])
    assert text.startswith("The scene was carried into the new world: 4 of 6 objects. With their state — “Particle 1”, "
                           "“Particle 2”. By their parameters (no state of their own) — “Probe 1”, “Wall (reflects) 1"
                           "”. Not carried: ")
    assert text.endswith("The world's state carried over: the visits were carried into the plane z = 0 (the cells along "
                         "x, y are the same)")
    assert ("“Particle 3” — The particle is off the plane z = 0 (z = 0.8 m, vz = 0.1 m/s). What to change: carry it "
            "into a 3-D world") in text
    assert "“Mirror (reflects; the axis is a number) 1” — " in text and note["not_carried"] == 2
    # a carried particle keeps its dynamic state; the planar world drags it in its plane
    assert list(run.sim.state["o1"]) == list(sim.state["o1"])
    # negative control: without «перенести сцену» the new world starts empty (as before P16.1)
    m2 = []
    _, r2, _ = _world(m2)
    r2._start_world()
    _build(r2)
    r2.handle({"cmd": "new_world", "args": {"params": {"ndim": 2}}})
    assert r2.world == 2 and not r2.sim.objects and not [m for m in _of(m2, "notice") if "The scene was carried" in E(m["text"])]


def test_a_carried_world_is_rebuilt_the_same_by_a_restore_and_a_refused_one_stays_refused():
    msgs = []
    sim, run, make_world = _world(msgs)
    run._start_world()
    _build(run)
    run.handle({"cmd": "new_world", "args": {"params": {"ndim": 2, "drag": 0.1}, "seed": 5, "carry": True}})
    n_head = max(i for i, (m, _) in enumerate(msgs) if m["type"] == "header")
    for dt in (0.1, 0.07, 0.2):
        run._advance(run.sim.t + dt)
        run._frame(0.0)
    run.handle({"cmd": "scene", "args": {"op": "edit", "id": "o2", "values": {"x": 1.0, "y": -1.0}}})
    # a world refused as a whole (a dimension the toy has not): the carried world goes on, and so does its restore
    run.handle({"cmd": "new_world", "args": {"params": {"ndim": 4}, "carry": True}})
    assert run.world == 2 and "New world not created" in E(_of(msgs, "error")[-1]["text"])
    for dt in (0.13, 0.05):
        run._advance(run.sim.t + dt)
        run._frame(0.0)
    # the restore by replay: world 2 built from its header's parameters (with the carried scene), then its record
    head = msgs[n_head][0]
    script = [{"frame": m["t"]} if m["type"] == "frame" else {"t": m["t"], "cmd": m["cmd"], "args": m["args"]}
              for m, _ in msgs[n_head + 1:] if m["type"] in ("frame", "command")]
    m2 = []

    def emit2(meta, blobs=None):
        m2.append((meta, blobs))
    viz = registry.load("p99_toy")
    sim2 = viz["simulation"](head["params"], head["seed"], emit2)

    def make2(pr, vals, sd):
        p, errs = viz["schema"].resolve(pr, vals or {})
        if errs:
            raise ValueError("; ".join(errs))
        return viz["simulation"](p, 3 if sd in (None, "") else int(sd), emit2), {"preset": pr}
    run2 = Runner(sim2, emit2, queue.Queue(), make_world=make2)
    run2.restore(2, script, run.sim.t, lambda on: None)
    assert run2.world == 2 and run2.sim.t == run.sim.t
    assert {k: o["values"] for k, o in run2.sim.objects.items()} == {k: o["values"] for k, o in run.sim.objects.items()}
    assert all((run2.sim.state[k] == run.sim.state[k]).all() for k in run.sim.state)
    # and both go on identically
    n1, n2 = len(msgs), len(m2)
    for r in (run, run2):
        for dt in (0.11, 0.09):
            r._advance(r.sim.t + dt)
            r._frame(0.0)
    assert _bytes(m2[n2:]) == _bytes(msgs[n1:])
    # determinism of the carry itself: the same old world carried twice gives the same header
    a, b = [], []
    for out in (a, b):
        _, r, _ = _world(out)
        r._start_world()
        _build(r)
        r.handle({"cmd": "new_world", "args": {"params": {"ndim": 2}, "seed": 5, "carry": True}})
    ha = [protocol.encode({k: v for k, v in m.items() if k not in ("engine", "backend")}) for m in _of(a, "header")]
    hb = [protocol.encode({k: v for k, v in m.items() if k not in ("engine", "backend")}) for m in _of(b, "header")]
    assert ha == hb


def test_a_carried_world_is_resumed_the_same_through_the_server(tmp_path, monkeypatch):
    """Through a worker: a run whose second world took the scene over is suspended, its checkpoints made unusable (the
    replay from the header is the path tested), and resumed: the world rebuilt has the carried objects, the same."""
    from lfviz import checkpoint as CKmod

    async def go():
        app = create_app(tmp_path, max_workers=1, idle_pause=60, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            mgr = app[MGR]
            rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 2})).json())["id"]
            run = mgr.get(rid)
            cmd = lambda c, a=None: cl.post(f"/api/runs/{rid}/command", json={"cmd": c, "args": a or {}})  # noqa: E731
            await cmd("scene", {"op": "add", "type": "particle", "values": {"x": 1.5, "y": -1.0, "z": 0.6}})
            await cmd("scene", {"op": "add", "type": "wall", "values": {"axis": "x", "position": 4.5}})
            await cmd("play")
            await asyncio.sleep(0.8)
            await cmd("new_world", {"params": {"drag": 0.2}, "carry": True})
            for _ in range(300):
                if any(e.kind == "header" and protocol.peek_meta(run._read(e, {})).get("world") == 2 for e in run.entries):
                    break
                await asyncio.sleep(0.05)
            await cmd("play")
            await asyncio.sleep(0.8)
            await cmd("pause")
            await asyncio.sleep(0.5)

            async def scene_now():
                ws = await cl.ws_connect(f"/ws/runs/{rid}")
                last = None
                while True:
                    m, _ = protocol.decode((await asyncio.wait_for(ws.receive(), 30)).data)
                    if m["type"] == "scene":
                        last = m
                    if m["type"] == "history_end":
                        break
                await ws.close()
                return last
            before = await scene_now()
            assert len(before["objects"]) == 5 and before["objects"][-1]["type"] == "wall"
            await cl.post(f"/api/runs/{rid}/stop", json={})
            w = run._latest_world()
            assert w["header"]["world"] == 2 and w["header"]["params"]["scene"]["carry"] is True
            monkeypatch.setattr(CKmod, "files_hash", lambda root, files: "another-code")  # no usable checkpoint
            assert run._latest_world()["checkpoint"] is None
            await cl.post(f"/api/runs/{rid}/resume", json={})
            for _ in range(400):
                if run.running and not run.rebuilding:
                    break
                await asyncio.sleep(0.05)
            assert run.meta["resumes"][-1]["from"] == "replay"
            await cmd("scene", {"op": "label", "id": "o1", "label": "after the continuation"})
            await asyncio.sleep(1.0)
            after = await scene_now()
            assert [(o["type"], o["values"]) for o in after["objects"]] == [(o["type"], o["values"]) for o in before["objects"]]
            await cl.post(f"/api/runs/{rid}/stop", json={})
    asyncio.run(go())


# --- review LB1-F5, F15: the state that goes with a carried scene, said exactly; the ids kept ------------------------
def _world_cls(msgs, cls, preset="two"):
    viz = registry.load("p99_toy")

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))

    def make_world(pr, vals, sd):
        p, errs = viz["schema"].resolve(pr, vals or {})
        if errs:
            raise ValueError("; ".join(errs))
        return cls(p, 3 if sd in (None, "") else int(sd), emit), {"preset": pr}
    sim, _ = make_world(preset, None, 3)
    return sim, Runner(sim, emit, queue.Queue(), make_world=make_world)


def _cloudy(run):
    """The toy with a cloud (its points in no scene file: carried only by carry_state), one object removed (ids with a
    gap) and the world's own state (visits) grown."""
    run._advance(0.3)
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "cloud", "values": {"x": 1.0, "y": -1.0, "vx": 0.5,
                                                                                "n": 7, "spread": 3.0}}})
    run.handle({"cmd": "scene", "args": {"op": "remove", "id": "o2"}})
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"x": 2.0, "z": 0.0}}})
    run._advance(0.9)
    run._frame(0.0)


def test_the_carried_state_is_said_object_by_object_and_the_ids_are_kept(tmp_path):
    msgs = []
    viz = registry.load("p99_toy")
    sim, run = _world_cls(msgs, viz["simulation"])
    run.ckpt_dir = tmp_path
    run._start_world()
    _cloudy(run)
    pts = sim.clouds["o4"][0].copy()
    ids = list(sim.objects)
    assert ids == ["o1", "o3", "o4", "o5"] and sim.visits.sum() > 0
    n0 = len(msgs)
    run.handle({"cmd": "new_world", "args": {"params": {"ndim": 2}, "carry": True}})
    new = run.sim
    assert run.world == 2 and new is not sim
    # F15: the same ids (o2 stays free), a new object gets the next id after them
    assert list(new.objects) == ids and new.next_id == 6
    # the cloud's points went with it (a file of the run, named with its hash in the header), the visits too
    assert (new.clouds["o4"][0] == pts + 0.0).all() and (new.visits == sim.visits).all()
    head = _of(msgs[n0:], "header")[0]
    ref = head["params"]["scene"]["carry_file"]
    data = (tmp_path / ref["file"]).read_bytes()
    assert PG.CARRY_NAME.match(ref["file"]) and hashlib.sha256(data).hexdigest() == ref["sha256"]
    assert "pts" not in str(head["params"]["scene"]["objects"])  # the heavy state is not in the header
    note = [m for m in _of(msgs[n0:], "notice") if "The scene was carried" in E(m["text"])][0]
    how = {o["id"]: o["how"] for o in note["carry"]["objects"]}
    assert how == {"o1": "state", "o3": "params", "o4": "state", "o5": "state"}
    # a value the new world changed is said (the toy's plane takes clouds at most 2 m wide)
    assert note["carry"]["objects"][2]["changed"] == {"spread": [3.0, 2.0]}
    assert "Changed in the carry-over — “Cloud of points 1”: spread 3 → 2" in E(note["text"])
    assert "The world's state carried over: the visits were carried into the plane z = 0" in E(note["text"])
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "probe", "values": {}}})
    assert list(new.objects)[-1] == "o6"
    # a world refused as a whole leaves no carried file behind; the earlier world's file is gone once a later world
    # exists (only the latest world is ever restored)
    before = sorted(p.name for p in tmp_path.glob("carry-*"))
    run.handle({"cmd": "new_world", "args": {"params": {"ndim": 4}, "carry": True}})
    assert run.world == 2 and sorted(p.name for p in tmp_path.glob("carry-*")) == before
    run.handle({"cmd": "new_world", "args": {"params": {"ndim": 2, "drag": 0.1}, "carry": True}})
    assert run.world == 3 and len(list(tmp_path.glob("carry-w3-*.npz"))) == 1 and not list(tmp_path.glob("carry-w2-*"))


def test_a_section_that_gives_no_state_is_said_to_restart():
    """Negative control of the above: the same toy without carry_state (as p03 and p04 were): the cloud is rebuilt
    from its parameters (other points), the visits start from zero, and the notice says both — never «все объекты» with
    nothing more."""
    class NoState(registry.load("p99_toy")["simulation"]):
        def carry_state(self):
            return None
    msgs = []
    sim, run = _world_cls(msgs, NoState)
    run._start_world()
    _cloudy(run)
    pts = sim.clouds["o4"][0].copy()
    n0 = len(msgs)
    run.handle({"cmd": "new_world", "args": {"params": {"drag": 0.2}, "carry": True}})
    new = run.sim
    assert "carry_file" not in _of(msgs[n0:], "header")[0]["params"]["scene"]
    assert not np.allclose(new.clouds["o4"][0], pts) and new.visits.sum() == 0
    note = [m for m in _of(msgs[n0:], "notice") if "The scene was carried" in E(m["text"])][0]
    assert {o["id"]: o["how"] for o in note["carry"]["objects"]}["o4"] == "restarted"
    assert "The state not carried, started afresh from the parameters — “Cloud of points 1”" in E(note["text"])
    assert note["carry"]["world"] == {"how": "restarted", "notes": [{"$t": "the visits of the cells started afresh from zero"}]}
    assert E(note["text"]).endswith("The world's state: the visits of the cells started afresh from zero")
    # a state the new world cannot take is said too (the toy refuses a cloud of another size: rebuilt, with why)
    m2 = []
    _, r2 = _world_cls(m2, registry.load("p99_toy")["simulation"])
    r2._start_world()
    _cloudy(r2)
    r2.sim.clouds["o4"][0] = r2.sim.clouds["o4"][0][:5]
    r2.handle({"cmd": "new_world", "args": {"params": {"drag": 0.2}, "carry": True}})
    note = [m for m, _ in m2 if m["type"] == "notice" and "The scene was carried" in E(m["text"])][-1]
    assert "“Cloud of points 1” (the number of points 5 → 7: the cloud is drawn anew)" in E(note["text"])
    # a world state the new world refuses (raised in carry_world): started afresh, with the reason
    class Refuses(registry.load("p99_toy")["simulation"]):
        def carry_world(self, state, laws):
            raise PG.Refusal(T("the grid of visits is another"))
    m3 = []
    _, r3 = _world_cls(m3, Refuses)
    r3._start_world()
    _cloudy(r3)
    r3.handle({"cmd": "new_world", "args": {"params": {"drag": 0.2}, "carry": True}})
    note = [m for m, _ in m3 if m["type"] == "notice" and "The scene was carried" in E(m["text"])][-1]
    assert note["carry"]["world"]["how"] == "restarted" and r3.sim.visits.sum() == 0
    assert E(note["text"]).endswith("The world's state: started afresh — The grid of visits is another")


def test_a_carried_state_is_plain_data_and_a_scene_file_cannot_name_one(tmp_path):
    st = {"objects": {"o1": {"pts": np.arange(6.0).reshape(3, 2), "n": np.int64(3), "ok": True}},
          "world": {"f": np.ones((2, 2, 9), np.float32), "c": np.array([1 + 2j]), "nan": float("nan"), "l": [1, None]}}
    back = PG.unpack_state(PG.pack_state(st))
    assert (back["objects"]["o1"]["pts"] == st["objects"]["o1"]["pts"]).all() and back["objects"]["o1"]["n"] == 3
    assert back["world"]["f"].dtype == np.float32 and back["world"]["c"][0] == 1 + 2j and back["world"]["l"] == [1, None]
    for bad in ({"x": object()}, {"a": np.array([object()], dtype=object)}, {1: 2}, {"__nd__": "a0"}):
        with pytest.raises(TypeError):
            PG.pack_state(bad)
    # a scene file (a REST start, a loaded file) may not name a carried state: only the runner's new world does
    with pytest.raises(ValueError, match="carried state"):
        PG.check_scene({"objects": [], "carry_file": {"file": "carry-w2-1.npz", "sha256": "0"}}, "p99_toy")
    PG.check_scene({"objects": [], "carry_file": {"file": None, "sha256": "0"}}, "p99_toy", carried_ok=True)
    # a reference to a state that is not there, or not the same, is refused in the owner's words (the world is not built)
    PG.set_carry_dir(tmp_path)
    try:
        ref = PG.store_carry({"world": {"a": np.zeros(3)}}, 2)
        PG._carry_cache.clear()
        assert (PG.load_carry(ref)["world"]["a"] == 0).all()
        PG._carry_cache.clear()
        (tmp_path / ref["file"]).write_bytes(PG.pack_state({"world": {"a": np.ones(3)}}))
        with pytest.raises(ValueError, match="was changed"):
            PG.load_carry(ref)
        (tmp_path / ref["file"]).unlink()
        with pytest.raises(ValueError, match="is not found"):
            PG.load_carry(ref)
    finally:
        PG.set_carry_dir(None)
        PG._carry_cache.clear()


def test_a_carried_state_is_resumed_the_same_by_replay_through_the_server(tmp_path, monkeypatch):
    """Through a worker (another process): the cloud's points and the visits carried into world 2 come back from the
    run's file when world 2 is rebuilt by replay; the first frame after the resume equals the last before it (t, at,
    meas). Negative control: the file changed — the resume refuses with the reason, it never makes another world."""
    from lfviz import checkpoint as CKmod

    async def go():
        app = create_app(tmp_path, max_workers=1, idle_pause=60, idle_suspend=3600)
        async with TestClient(TestServer(app)) as cl:
            mgr = app[MGR]
            rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 2})).json())["id"]
            run = mgr.get(rid)
            cmd = lambda c, a=None: cl.post(f"/api/runs/{rid}/command", json={"cmd": c, "args": a or {}})  # noqa: E731
            await cmd("scene", {"op": "add", "type": "cloud", "values": {"x": 1.0, "y": 1.0, "vx": -0.3, "n": 9}})
            await cmd("play")
            await asyncio.sleep(0.8)
            await cmd("new_world", {"params": {"drag": 0.2}, "carry": True})
            for _ in range(300):
                if any(e.kind == "header" and protocol.peek_meta(run._read(e, {})).get("world") == 2 for e in run.entries):
                    break
                await asyncio.sleep(0.05)
            await cmd("play")
            await asyncio.sleep(0.8)
            await cmd("pause")
            await asyncio.sleep(0.5)

            async def frames():
                ws = await cl.ws_connect(f"/ws/runs/{rid}")
                out = []
                while True:
                    m, _ = protocol.decode((await asyncio.wait_for(ws.receive(), 30)).data)
                    if m["type"] == "frame":
                        out.append(m)
                    if m["type"] == "history_end":
                        break
                await ws.close()
                return out
            last = (await frames())[-1]
            assert last["at"]["o4"][0] != 1.0 and last["meas"]["visits"] > 0
            await cl.post(f"/api/runs/{rid}/stop", json={})
            w = run._latest_world()
            ref = w["header"]["params"]["scene"]["carry_file"]
            assert (run.ckpt_dir / ref["file"]).is_file()
            monkeypatch.setattr(CKmod, "files_hash", lambda root, files: "another-code")  # no usable checkpoint
            await cl.post(f"/api/runs/{rid}/resume", json={})
            for _ in range(400):
                if run.running and not run.rebuilding:
                    break
                await asyncio.sleep(0.05)
            assert run.meta["resumes"][-1]["from"] == "replay"
            await asyncio.sleep(1.0)
            after = [f for f in await frames() if f["t"] >= last["t"]]
            first = [f for f in after if f is not last and f["t"] == last["t"]][-1]
            assert first["at"] == last["at"] and first["meas"] == last["meas"]
            await cl.post(f"/api/runs/{rid}/stop", json={})
            # the carried file changed: the resume says why and makes no other world
            p = run.ckpt_dir / ref["file"]
            p.write_bytes(p.read_bytes() + b"x")
            monkeypatch.setattr(CKmod, "files_hash", lambda root, files: "third-code")  # the replay again
            assert run._latest_world()["checkpoint"] is None
            await cl.post(f"/api/runs/{rid}/resume", json={})
            for _ in range(400):
                if not run.running and not run.rebuilding:
                    break
                await asyncio.sleep(0.05)
            await asyncio.sleep(0.5)
            # a failed resume is kept out of the record and said in the run's state (lfviz.runs: resume_error)
            assert not run.running and "was changed" in E(run.meta.get("resume_error") or ""), run.meta.get("resume_error")
    asyncio.run(go())


def test_hidden_parameters_are_not_listed_as_changed_by_a_carry():
    """A hidden parameter the new world recomputes (p02's v_max) is not reported as an owner's value changed (the
    integrator, after review LB1-p02-ux's p02 processing); a visible one still is (negative control)."""
    from lfviz.playground import _changed
    sent = {"x": 1.0, "v_max": 5.0, "r": 2.0}
    now = {"x": 1.0, "v_max": 7.0, "r": 3.0}
    assert _changed(sent, now, {"v_max"}) == {"r": [2.0, 3.0]}
    assert "v_max" in _changed(sent, now)
