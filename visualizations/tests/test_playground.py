# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The playground's framework (plan P15.0, lfviz.playground and the buffer of lfviz.runs), on the toy section of
``tests/playgrounds`` (found through ``LFVIZ_EXTRA``, never in the catalogue): the scene changed by hand at any moment
(add, remove, set, duplicate, label, clear; a refused change leaves it as it was), the scene as a file and a world
started from it, a restore and a checkpoint repeating the scene's changes exactly, and the record kept as a moving
window (segments at the checkpoints, old ones deleted unless recording was switched on, the worlds' headers kept apart,
a reload of the server finding the same record)."""

import asyncio
import json
import queue
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import checkpoint, protocol, registry
from lfviz.app import MGR, create_app
from lfviz.i18n import T
from lfviz.i18n import english as E
from lfviz.sim import Runner

HERE = Path(__file__).resolve().parent
WALL = ("cpu_ms", "speed_actual", "lag")


@pytest.fixture(autouse=True)
def _toy(monkeypatch):
    """The toy section is found by this process and its workers (only within these tests)."""
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
    return sim, Runner(sim, emit, queue.Queue(), make_world=make_world)


def _of(msgs, typ):
    return [m for m, _ in msgs if m.get("type") == typ]


def test_the_scene_is_changed_by_hand_at_the_current_moment():
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    assert [o["type"] for o in _of(msgs, "scene")[-1]["objects"]] == ["particle", "particle", "probe"]
    run._advance(0.5)
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"x": 3.0, "vy": 2.0}}})
    sc = _of(msgs, "scene")[-1]
    new = sc["objects"][-1]
    assert new["t_added"] == pytest.approx(0.5) and new["values"]["x"] == 3.0 and sc["rev"] == 1
    assert _of(msgs, "event")[-1]["kind"] == "scene" and "added" in E(_of(msgs, "event")[-1]["text"])
    run.handle({"cmd": "scene", "args": {"op": "set", "id": new["id"], "values": {"vx": -4.0}}})
    assert sim.state[new["id"]][2] == -4.0 and sim.objects[new["id"]]["values"]["vx"] == -4.0
    run.handle({"cmd": "scene", "args": {"op": "duplicate", "id": new["id"]}})
    dup = _of(msgs, "scene")[-1]["objects"][-1]
    assert E(dup["label"]).endswith("(copy)") and list(sim.state[dup["id"]]) == list(sim.state[new["id"]])
    run.handle({"cmd": "scene", "args": {"op": "label", "id": dup["id"], "label": "B"}})
    assert sim.objects[dup["id"]]["label"] == "B"
    run.handle({"cmd": "scene", "args": {"op": "remove", "id": new["id"]}})
    assert new["id"] not in sim.objects and new["id"] not in sim.state
    # refused changes: reported, the scene as it was
    n_err, rev = len(_of(msgs, "error")), sim.rev
    for bad in ({"op": "set", "id": dup["id"], "values": {"mass": -1}}, {"op": "add", "type": "black_hole"},
                {"op": "remove", "id": "o999"}, {"op": "nonsense"}):
        run.handle({"cmd": "scene", "args": bad})
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "probe"}})
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "probe"}})
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "probe"}})  # the limit is 3
    assert len(_of(msgs, "error")) == n_err + 5 and sim.rev == rev + 2
    assert sim.objects[dup["id"]]["values"]["mass"] == 1.0
    run.handle({"cmd": "scene", "args": {"op": "clear"}})
    assert not sim.objects and not sim.state and _of(msgs, "scene")[-1]["objects"] == []
    # every change was recorded as a command with its time (a restore repeats them)
    assert sum(1 for c in _of(msgs, "command") if c["cmd"] == "scene") == 13


def test_the_scene_as_a_file_and_a_world_from_it():
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    run._advance(0.7)
    run.handle({"cmd": "scene", "args": {"op": "export"}})
    ex = _of(msgs, "scene_export")[-1]["scene"]
    assert ex["format"] == "lfscene" and ex["viz"] == "p99_toy" and ex["t"] == pytest.approx(0.7)
    assert ex["laws"] == {"drag": 0.0, "ndim": 3} and len(ex["objects"]) == 3
    assert ex["objects"][0]["state"]["xv"] == [float(x) for x in sim.state["o1"]]
    assert not [e for e in _of(msgs, "event") if e.get("name") == "export"]  # not a change of the scene
    text = json.dumps(ex)  # what the player saves
    m2 = []
    sim2, run2 = _world(m2, None, {**json.loads(text)["laws"], "scene": json.loads(text)})
    assert sim2.t == pytest.approx(0.7) and [o["values"] for o in sim2.objects.values()] == \
        [o["values"] for o in sim.objects.values()]
    assert all((sim2.state[k] == sim.state[k]).all() for k in sim.state)
    with pytest.raises(ValueError, match="a scene of another section"):
        _world([], None, {"scene": {**ex, "viz": "p01_gravity"}})
    run.handle({"cmd": "new_world", "args": {"params": {"scene": ex}, "seed": 5}})
    assert _of(msgs, "header")[-1]["world"] == 2 and len(_of(msgs, "scene")[-1]["objects"]) == 3


def _session(run):
    """A session of scene changes between irregular frames (the kick draws random numbers)."""
    for i, dt in enumerate([0.13, 0.07, 0.21, 0.05, 0.17, 0.11]):
        run._advance(run.sim.t + dt)
        run._frame(0.0)
        if i == 1:
            run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"y": 1.0, "kick": 0.3}}})
        if i == 3:
            run.handle({"cmd": "scene", "args": {"op": "set", "id": "o1", "values": {"vx": 2.5, "kick": 0.2}}})
        if i == 4:
            run.handle({"cmd": "scene", "args": {"op": "duplicate", "id": "o2"}})


def _bytes(msgs):
    return [protocol.encode({k: v for k, v in m.items() if k not in WALL}, b) for m, b in msgs]


def test_a_restore_repeats_the_scenes_changes_exactly():
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    _session(run)
    script = []
    for m, _ in msgs:
        if m["type"] == "frame":
            script.append({"frame": m["t"]})
        elif m["type"] == "command":
            script.append({"t": m["t"], "cmd": m["cmd"], "args": m["args"]})
    m2 = []
    _, run2 = _world(m2)
    run2.restore(1, script, sim.t, lambda on: None)
    assert run2.sim.t == sim.t and set(run2.sim.state) == set(sim.state)
    assert all((run2.sim.state[k] == sim.state[k]).all() for k in sim.state)
    assert _bytes(m2) == _bytes(msgs)


def test_a_checkpoint_continues_the_scene_exactly(tmp_path):
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    _session(run)
    run.ckpt_dir, run.ckpt_dirty = tmp_path, True
    run.checkpoint("test")
    run.ckpt_writer.wait()
    types = [m["type"] for m, _ in msgs]
    i = types.index("record_segment")
    # a segment drawable on its own: the scene, the section's kept trails, the latest set-like messages, the state
    assert types[i:i + 5] == ["record_segment", "scene", "trail", "box", "checkpoint"], types[i:i + 5]
    n0 = len(msgs)
    _session(run)
    orig = _bytes(msgs[n0:])
    ck = _of(msgs, "checkpoint")[-1]
    m2 = []
    state = checkpoint.loads((tmp_path / ck["file"]).read_bytes(), lambda m, b=None: m2.append((m, b)))
    run2 = Runner(state["sim"], state["sim"].emit, queue.Queue())
    run2.restore_from(state, [], state["sim"].t, lambda on: None)
    _session(run2)
    assert _bytes(m2) == orig


def test_a_segment_start_repeats_what_a_view_holds_and_changes_nothing(tmp_path):
    """Review B6-F4, F5, F8: a segment's start carries the trails kept so far (marked reset: a viewer's trails do not
    vanish) and the latest value of every set-like message at the current time, and it changes nothing in the world:
    the same world without it (a world rebuilt by replay has no segment starts) emits the same messages afterwards."""
    a, b = [], []
    sim_a, run_a = _world(a)
    sim_b, run_b = _world(b)
    for run in (run_a, run_b):
        run._start_world()
        _session(run)
    run_a.ckpt_dir, run_a.ckpt_dirty = tmp_path, True
    n_a = len(a)
    run_a.checkpoint("test")
    run_a.ckpt_writer.wait()
    start = a[n_a:]
    trail = [(m, bl) for m, bl in start if m["type"] == "trail"][0]
    assert trail[0]["reset"] and trail[0]["ids"] == list(sim_a.trail_kept)
    assert trail[0]["counts"] == [len(sim_a.trail_kept[k]) for k in trail[0]["ids"]] and sum(trail[0]["counts"]) > 0
    box = [m for m, _ in start if m["type"] == "box"][0]
    assert box["t"] == sim_a.t and box["box"] == _of(a[:n_a], "box")[-1]["box"]
    # the base's repetitions are marked: a viewer that holds the same box already ignores it (review UX-ui U1: an unchanged
    # box re-sent at every segment put the camera back); the section's own rekey (trails) is not a repetition
    assert box["repeat"] is True and [m for m, _ in start if m["type"] == "scene"][0]["repeat"] is True
    assert "repeat" not in trail[0]
    n_a, n_b = len(a), len(b)
    _session(run_a)
    _session(run_b)
    assert _bytes(a[n_a:]) == _bytes(b[n_b:])


async def _wait(cl, rid, cond, n=300):
    for _ in range(n):
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        if cond(meta):
            return meta
        await asyncio.sleep(0.1)
    raise AssertionError(meta)


async def _history(cl, rid):
    ws = await cl.ws_connect(f"/ws/runs/{rid}")
    out = []
    while True:
        m = await asyncio.wait_for(ws.receive(), 30)
        meta = protocol.decode(m.data)[0]
        out.append(meta)
        if meta["type"] == "history_end":
            break
    await ws.close()
    return out


async def _buffer(tmp_path, monkeypatch):
    monkeypatch.setenv("P99_CKPT", "0.4")  # a segment every 0.4 s of computation
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        r = await cl.get("/api/viz")
        assert [v for v in await r.json() if v["id"] == "p99_toy"][0]["kind"] == "playground"
        rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two"})).json())["id"]
        run = mgr.get(rid)
        assert run.buffered and run.meta["kind"] == "playground"
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "scene", "args": {"op": "add", "type": "particle"}})
        await _wait(cl, rid, lambda m: len(m["buffer"]["segs"]) >= 5)
        segs = [dict(sg) for sg in run.meta["buffer"]["segs"]]
        assert all(run.seg_path(sg["k"]).is_file() for sg in segs)
        # every segment after the first starts with its marker, the scene, then the checkpoint
        firsts = {}
        for e in run.entries:
            firsts.setdefault(e.seg, []).append(e)
        cache = {}
        newest = max(firsts)
        for k, es in firsts.items():
            if k == 0 or (k == newest and len(es) < 5):  # the segment being written may not have its checkpoint yet
                continue
            kinds = [protocol.peek_meta(run._read(e, cache))["type"] for e in es[:5]]
            assert kinds == ["record_segment", "scene", "trail", "box", "checkpoint"], (k, kinds)
        # the window: segments that left it are deleted (here: aged by hand), never the newest two
        _age(run)
        n_before = len(run.meta["buffer"]["segs"])
        run._trim()
        kept = [sg["k"] for sg in run.meta["buffer"]["segs"]]
        assert len(kept) == 2 and n_before > 2 and run.meta["buffer"]["trimmed"]
        dropped = [sg["k"] for sg in segs if sg["k"] not in kept]
        assert {e.seg for e in run.entries} <= set(kept) and dropped
        assert all(not run.seg_path(k).exists() for k in dropped if k) and \
            (0 not in dropped or run.seg_path(0).read_bytes() == protocol.MAGIC)
        # a viewer joining now gets the world's header first (kept apart), then the window
        h = await _history(cl, rid)
        real = [m["type"] for m in h if m["type"] not in ("history_start",)]
        assert real[0] == "header" and "frame" in real and h[0]["buffer"]["trimmed"]
        # recording on: what the window holds and everything after it is kept for good
        st = await (await cl.post(f"/api/runs/{rid}/record", json={"on": True})).json()
        assert st["recording"]
        kept_on = [sg["k"] for sg in run.meta["buffer"]["segs"]]
        await _wait(cl, rid, lambda m: len(m["buffer"]["segs"]) >= len(kept_on) + 3)
        _age(run)
        run._trim()
        assert [sg["k"] for sg in run.meta["buffer"]["segs"]][:len(kept_on)] == kept_on
        st = await (await cl.post(f"/api/runs/{rid}/record", json={"on": False})).json()
        assert not st["recording"] and st["protected"][-1][1] is not None
        assert (await cl.post(f"/api/runs/{rid}/record", json={"on": True, "window_s": 5})).status == 400
        # the API's body (review B6-F12): "on" a boolean, unchanged when absent; numbers; an object
        assert (await cl.post(f"/api/runs/{rid}/record", json={"on": "false"})).status == 400
        assert (await cl.post(f"/api/runs/{rid}/record", json=[1])).status == 400
        assert (await cl.post(f"/api/runs/{rid}/record", json={"window_s": [60]})).status == 400
        st = await (await cl.post(f"/api/runs/{rid}/record", json={"window_s": 300})).json()
        assert st["recording"] is False and st["window_s"] == 300
        # a scene file that is not one: refused before a worker starts (B6-F17)
        for bad in ([1, 2], {"objects": {"a": 1}}, {"objects": [], "t": 1e300}, {"objects": [5]}):
            r = await cl.post("/api/runs", json={"viz": "p99_toy", "params": {"scene": bad}})
            assert r.status == 400, (bad, r.status)
        # a demonstration has no window
        did = (await (await cl.post("/api/runs", json={"viz": "u31_light_travel", "preset": "measure_c"})).json())["id"]
        assert (await cl.post(f"/api/runs/{did}/record", json={"on": True})).status == 409
        await cl.post(f"/api/runs/{did}/stop", json={})
        # the joined record for download: magic, the header, then the kept messages
        data = await (await cl.get(f"/api/runs/{rid}/stream")).read()
        kinds = [protocol.peek_meta(m)["type"] for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]
        assert data.startswith(protocol.MAGIC) and kinds[0] == "header" and kinds.count("header") == 1
        # suspended and resumed: from its checkpoint
        await cl.post(f"/api/runs/{rid}/stop", json={})
        t_stop = run.meta["sim_t"]
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        await _wait(cl, rid, lambda m: m["state"] == "running" and m.get("sim_t", 0) > t_stop + 0.2)
        assert run.meta["resumes"][-1]["from"] == "checkpoint"
        await cl.post(f"/api/runs/{rid}/stop", json={})
        n_entries, headers = len(run.entries), set(run.headers)
        # the server restarted: the same record found in its segments
        run2 = mgr._load_one(run.dir)
        assert len(run2.entries) == n_entries and set(run2.headers) == headers and run2.seg == run.seg
        # the saved state unusable and the world's start out of the window: the resume says why
        from lfviz import checkpoint as CKmod
        monkeypatch.setattr(CKmod, "files_hash", lambda root, files: "another-code")
        r = await cl.post(f"/api/runs/{rid}/resume", json={})
        assert r.status == 409 and "left the record's window" in (await r.json())["text"]


def _age(run, s=10_000.0):
    """Age every segment by hand: as if the world had been shown computing for ``s`` seconds in each."""
    for sg in run.meta["buffer"]["segs"]:
        sg["play_s"] = s


def test_the_record_of_a_playground_is_a_moving_window(tmp_path, monkeypatch):
    asyncio.run(_buffer(tmp_path, monkeypatch))


def test_the_window_counts_the_time_the_world_was_computing(tmp_path, monkeypatch):
    """Review B6-F10: a pause (or a suspension) does not age the record; the window is the time frames flowed. A
    ``Run`` with a controlled clock: 9 minutes of play, a long pause, one more minute: nothing computed is dropped."""
    from lfviz import runs as R
    clock = [1000.0]
    monkeypatch.setattr(R.time, "time", lambda: clock[0])

    async def go():
        app = create_app(tmp_path, max_workers=1, idle_pause=3600, idle_suspend=7200)
        async with TestClient(TestServer(app)):
            run = R.Run(app[MGR], "x", "p99_toy", {"buffer": dict(R.BUFFER_DEFAULT, segs=[])}, tmp_path / "x")
            run.dir.mkdir()
            run.file = open(run.seg_path(0), "wb")
            run.file.write(protocol.MAGIC)
            run.meta["buffer"]["segs"].append({"k": 0, "wall0": clock[0], "t0": 0.0, "world": 1})

            def play(seconds, t0):
                for i in range(int(seconds * 4)):  # frames 4 per second
                    clock[0] += 0.25
                    run._ingest(protocol.encode({"type": "frame", "t": t0 + i * 0.25}))
                    if i % 240 == 239:  # a segment every minute of play
                        run._ingest(protocol.encode({"type": "record_segment", "t": t0 + i * 0.25, "world": 1}))
            play(540, 0.0)
            clock[0] += 20 * 60  # paused for 20 minutes: no frames
            play(60, 540.0)
            kept_from = run.buffer_state()["kept_from_t"]
            assert kept_from is not None and kept_from < 1.0 + 60, run.meta["buffer"]["segs"]  # the first minute kept
            play(300, 600.0)  # 15 minutes computed in all: about the first 5 have left the 10-minute window
            assert 180.0 <= run.buffer_state()["kept_from_t"] <= 300.0, run.buffer_state()
            run.file.close()
    asyncio.run(go())


async def _resume_cases(tmp_path, monkeypatch):
    """Review B6-F1, F2, F3 (the reviewer's scenarios A, B, C on the toy): a resume after the window trimmed the record
    never continues another world."""
    monkeypatch.setenv("P99_CKPT", "0.4")
    app = create_app(tmp_path, max_workers=2, idle_pause=600, idle_suspend=3600)
    from lfviz import checkpoint as CKmod
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]

        async def new_run():
            rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 3})).json())["id"]
            await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
            return rid, mgr.get(rid)

        async def segs_at_least(run, n):
            for _ in range(600):
                if len(run.meta["buffer"]["segs"]) >= n:
                    return
                await asyncio.sleep(0.05)
            raise AssertionError(run.meta["buffer"]["segs"])

        # A: recording on, then off: a protected head, a trimmed stretch with a scene change, no usable checkpoint
        rid, run = await new_run()
        await cl.post(f"/api/runs/{rid}/record", json={"on": True})
        await segs_at_least(run, 3)
        await cl.post(f"/api/runs/{rid}/record", json={"on": False})
        await segs_at_least(run, len(run.meta["buffer"]["segs"]) + 2)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "scene", "args": {"op": "set", "id": "o1",
                                                                                  "values": {"vx": 5.0}}})
        await segs_at_least(run, len(run.meta["buffer"]["segs"]) + 4)
        _age(run)
        run._trim()
        await cl.post(f"/api/runs/{rid}/stop", json={})
        assert run._latest_world()["complete"] is False
        with monkeypatch.context() as mp:
            mp.setattr(CKmod, "files_hash", lambda root, files: "another-code")
            r = await cl.post(f"/api/runs/{rid}/resume", json={})
            assert r.status == 409 and "left the record's window" in (await r.json())["text"]
        # B: the header trimmed, the checkpoint unloadable in the worker: an error, not a rebuild from a lost start
        rid, run = await new_run()
        await segs_at_least(run, 6)
        _age(run)
        run._trim()
        await cl.post(f"/api/runs/{rid}/stop", json={})
        w = run._latest_world()
        assert w["complete"] is False
        Path(w["checkpoint"]["file"]).write_bytes(b"\x00" * 64)
        n0 = len(run.entries)
        await cl.post(f"/api/runs/{rid}/resume", json={})
        for _ in range(400):
            if not run.running and run.meta.get("resume_error"):
                break
            await asyncio.sleep(0.05)
        assert "left the record's window" in E(run.meta["resume_error"]), run.meta.get("resume_error")
        assert not any(e.is_frame for e in run.entries[n0:])
        # C: world 1 kept, world 2's header trimmed: the resume continues world 2 at its own time
        rid, run = await new_run()
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "speed", "args": {"value": 50.0}})
        await cl.post(f"/api/runs/{rid}/record", json={"on": True})
        await asyncio.sleep(1.5)
        await cl.post(f"/api/runs/{rid}/record", json={"on": False})
        await segs_at_least(run, len(run.meta["buffer"]["segs"]) + 2)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "new_world", "args": {"preset": "two", "seed": 4}})
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await segs_at_least(run, len(run.meta["buffer"]["segs"]) + 5)
        _age(run)
        run._trim()
        await cl.post(f"/api/runs/{rid}/stop", json={})
        cache = {}
        last2 = max(protocol.peek_meta(run._read(e, cache))["t"] for e in run.entries
                    if e.is_frame and run._world_of_seg(e.seg) == 2)
        w = run._latest_world()
        assert w["header"]["world"] == 2 and w["t_end"] == pytest.approx(last2), (w["t_end"], last2)


def test_a_resume_after_the_window_trimmed_never_continues_another_world(tmp_path, monkeypatch):
    asyncio.run(_resume_cases(tmp_path, monkeypatch))


def test_a_thermal_switch_in_the_middle_of_a_world_is_said(monkeypatch):
    """Review B6-F19: when the backend's temperature guard moves GPU 0's kernels to the CPU (or back), the runner says
    so at once (a notice with the backend's report), once per switch, not only in the next world's header."""
    from lfphys.core import backend as B
    msgs = []
    sim, run = _world(msgs)
    run._start_world()
    state = {"hot": False, "temp": 60.0}
    monkeypatch.setattr(B, "thermal", lambda: {**B.THERMAL, "hot": state["hot"], "temp": state["temp"],
                                               "last_temp": state["temp"], "error": ""})
    run._thermal_note()
    assert not _of(msgs, "notice")
    state.update(hot=True, temp=83.0)
    run._thermal_note()
    run._thermal_note()
    notes = _of(msgs, "notice")
    assert len(notes) == 1 and "83 °C" in E(notes[0]["text"]) and "CPU" in E(notes[0]["text"]) and "backend" in notes[0]
    state.update(hot=False, temp=69.0)
    run._thermal_note()
    assert len(_of(msgs, "notice")) == 2 and "has cooled" in E(_of(msgs, "notice")[-1]["text"])


def test_place_palette_state_and_removals_asked_first():
    """The integrator's API of 2026-11-05 for reviews UX-ui U4, U7, U22 and UX-params P28: ``place`` completes a new
    object's values (the point clicked in the scene arrives as ``position``; without ``place`` it goes to x, y), a
    refusal there adds nothing; ``palette_state`` is sent in every scene message; ``can_remove`` is asked before a
    removal and for every object before «Очистить сцену» removes any (a refused clear leaves the scene whole)."""
    from lfviz.errors import Refusal
    msgs = []
    viz = registry.load("p99_toy")
    base = viz["simulation"]

    class Placed(base):
        def place(self, kind, values):
            if values.get("x") == 99.0:
                raise Refusal(T("a wall is there"), T("move x to the left"))
            if kind == "particle" and "position" not in values and not values.get("x"):
                values["x"] = 4.0  # a free spot
            return values

        def palette_state(self):
            return {"probe": T("there is a probe already") if any(o["type"] == "probe" for o in self.objects.values()) else None}

        def can_remove(self, obj):
            return T("the probe is fixed") if obj["type"] == "probe" else None

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    p, _ = viz["schema"].resolve("two", {})
    sim = Placed(p, 3, emit)
    run = Runner(sim, emit, queue.Queue())
    run._start_world()
    assert _of(msgs, "scene")[-1]["palette_state"] == {"probe": {"$t": "there is a probe already"}}
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {}}})
    assert _of(msgs, "scene")[-1]["objects"][-1]["values"]["x"] == 4.0
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"position": [1.5, -2.0, 0.0]}}})
    v = _of(msgs, "scene")[-1]["objects"][-1]["values"]
    assert (v["x"], v["y"]) == (1.5, -2.0) and "position" not in v
    n, rev = len(sim.objects), sim.rev
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"x": 99.0}}})
    assert len(sim.objects) == n and sim.rev == rev
    assert E(_of(msgs, "error")[-1]["text"]) == "Scene not changed: a wall is there. What to change: move x to the left"
    probe = [o for o in sim.objects.values() if o["type"] == "probe"][0]
    run.handle({"cmd": "scene", "args": {"op": "remove", "id": probe["id"]}})
    assert probe["id"] in sim.objects and "is fixed" in E(_of(msgs, "error")[-1]["text"])
    run.handle({"cmd": "scene", "args": {"op": "clear"}})
    assert len(sim.objects) == n and "the scene cannot be cleared" in E(_of(msgs, "error")[-1]["text"])
    assert all(k in sim.state for k, o in sim.objects.items() if o["type"] == "particle")  # nothing half-removed
    # without the section's place: a clicked point goes to the type's x, y
    msgs2 = []
    sim2, run2 = _world(msgs2)
    run2._start_world()
    run2.handle({"cmd": "scene", "args": {"op": "add", "type": "probe", "values": {"position": [0.25, 0.5, 0.0]}}})
    v2 = _of(msgs2, "scene")[-1]["objects"][-1]["values"]
    assert (v2["x"], v2["y"]) == (0.25, 0.5)


def test_a_parameter_named_position_is_kept():
    """Found by the p03 agent: ``position`` was taken as a clicked point whatever it held, so p03's piston lost its own
    scalar «Положение». Only a list of 2 or 3 numbers is a clicked point; any other ``position`` is the type's own."""
    from lfviz.params import Param, Schema
    from lfviz.playground import ObjectType
    viz = registry.load("p99_toy")
    base = viz["simulation"]

    class WithPiston(base):
        PALETTE = {**base.PALETTE, "piston": ObjectType("piston", "Piston", "body",
                                                        Schema([Param("position", "Position, nm", "float", 10.0)]))}
    msgs = []

    def emit(meta, blobs=None):
        msgs.append((meta, blobs))
    p, _ = viz["schema"].resolve("two", {})
    sim = WithPiston(p, 3, emit)
    run = Runner(sim, emit, queue.Queue())
    run._start_world()
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "piston", "values": {"position": 3.5}}})
    assert _of(msgs, "scene")[-1]["objects"][-1]["values"]["position"] == 3.5
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "piston", "values": {"position": [1.0, 2.0, 0.0]}}})
    assert _of(msgs, "scene")[-1]["objects"][-1]["values"]["position"] == 10.0  # a clicked point is not the parameter
    run.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"position": [1.5, -2.0]}}})
    v = _of(msgs, "scene")[-1]["objects"][-1]["values"]
    assert (v["x"], v["y"]) == (1.5, -2.0)
