# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The one server: message format, parameter schema, REST + WebSocket API, recording and lifecycle."""

import asyncio
import json
import math
import struct
from pathlib import Path

import numpy as np
import pytest
from aiohttp import WSMsgType
from aiohttp.test_utils import TestClient, TestServer

from lfviz import protocol, registry
from lfviz.app import MGR, create_app
from lfviz.i18n import T, english
from lfviz.params import Param, Schema


def test_protocol_round_trip_and_alignment():
    blobs = {"a": np.arange(5, dtype=np.float64), "b": np.array([1, 2, 3], np.uint8), "c": np.ones((2, 3), np.float32)}
    msg = protocol.encode({"type": "x", "v": float("nan"), "w": [np.float64(1.5), np.int64(3)]}, blobs)
    meta, out = protocol.decode(msg)
    assert meta["v"] is None and meta["w"] == [1.5, 3]
    for k, v in blobs.items():
        assert np.array_equal(out[k], v)
    jlen = int.from_bytes(msg[:4], "little")
    base = 4 + jlen + (-(4 + jlen)) % 8
    for d in meta["blobs"]:
        assert (base + d["offset"]) % 8 == 0


def test_schema_resolve_and_modifications():
    s = Schema([Param("law", "Law", "select", "std", options=[("std", "s"), ("mod", "m")], standard="std"),
                Param("c", "c", "float", 1.0, standard=1.0, min=0.1, max=10),
                Param("n", "n", "int", 3, min=1, max=5)],
               presets={"p": {"label": "P", "params": {"law": "mod"}}})
    vals, err = s.resolve("p", {"c": 2})
    assert not err and vals == {"law": "mod", "c": 2.0, "n": 3}
    mods = {m["id"] for m in s.modifications(vals)}
    assert mods == {"law", "c"}
    _, err = s.resolve(None, {"n": 9, "zzz": 1})
    assert len(err) == 2


def test_registry_lists_visualizations():
    ids = registry.viz_ids()
    assert "v01_light_travel" in ids and "v02_double_slit" in ids
    for vid in ids:
        v = registry.load(vid)
        assert v["schema"].presets and callable(v["simulation"])
        assert (registry.ROOT / vid / "web" / "view.js").is_file()
        assert (registry.ROOT / vid / "README.md").is_file()


async def _run_api(tmp_path):
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        r = await cl.get("/api/viz")
        assert r.status == 200
        ids = [v["id"] for v in await r.json()]
        assert "v01_light_travel" in ids
        r = await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c", "seed": 7})
        body = await r.json()
        assert r.status == 200, body
        rid = body["id"]
        ws = await cl.ws_connect(f"/ws/runs/{rid}")
        seen = []
        await ws.send_str(json.dumps({"cmd": "speed", "args": {"value": 0.01}}))
        await ws.send_str(json.dumps({"cmd": "play"}))
        frames = 0
        async def read(n_frames):
            nonlocal frames
            while frames < n_frames:
                m = await asyncio.wait_for(ws.receive(), 30)
                assert m.type == WSMsgType.BINARY
                meta, _ = protocol.decode(m.data)
                seen.append(meta["type"])
                if meta["type"] == "frame":
                    frames += 1
        await read(10)
        # an early viewer: an empty history first; the worker's "busy" notices (not recorded) around the build
        real = [t for t in seen if t not in ("history_start", "history_end", "busy")]
        assert real[0] == "header" and "state" in real and "worldline" in real
        # second viewer joins late: gets the record so far, then live
        ws2 = await cl.ws_connect(f"/ws/runs/{rid}")
        types2 = []
        while "history_end" not in types2:
            m = await asyncio.wait_for(ws2.receive(), 30)
            types2.append(protocol.decode(m.data)[0]["type"])
        assert types2[:2] == ["history_start", "header"]
        await ws2.close()
        r = await cl.get("/api/runs")
        runs = await r.json()
        assert runs[0]["id"] == rid and runs[0]["state"] == "running"
        # action through REST
        r = await cl.post(f"/api/runs/{rid}/command",
                          json={"cmd": "action", "args": {"name": "measure", "args": {"obj": "obs1"}}})
        assert r.status == 200
        r = await cl.post(f"/api/runs/{rid}/stop", json={})
        assert r.status == 200
        await ws.close()
        for _ in range(50):
            meta = await (await cl.get(f"/api/runs/{rid}")).json()
            if meta["state"] != "running":
                break
            await asyncio.sleep(0.1)
        assert meta["state"] == "suspended" and meta["code"] and meta["seed"] == 7 and meta["restorable"]
        assert any(c["cmd"] == "action" for c in meta["commands"])
        rec = tmp_path / rid / "stream.lfrec"
        data = rec.read_bytes()
        assert data.startswith(protocol.MAGIC)
        heads = [protocol.peek_meta(m) for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]
        types = [h["type"] for h in heads]
        assert types[0] == "header" and types[-1] == "end" and "event" in types
        assert any(h["type"] == "command" and h["cmd"] == "action" for h in heads)  # with its world time
        t_susp = meta["sim_t"]
        # the owner, 2026-10-28: a run can always be continued — a command that computes resumes it, rebuilt from its
        # record, and its record goes on from where it ended (no second header, the time goes on)
        ws = await cl.ws_connect(f"/ws/runs/{rid}")
        while True:
            m = await asyncio.wait_for(ws.receive(), 30)
            meta_h = protocol.decode(m.data)[0]
            if meta_h["type"] == "history_end":
                assert meta_h["resumable"] and not meta_h["live"]
                break
        await ws.send_str(json.dumps({"cmd": "play"}))
        t_new = None
        for _ in range(400):
            m = await asyncio.wait_for(ws.receive(), 60)
            mm = protocol.decode(m.data)[0]
            if mm["type"] == "frame" and mm["t"] > t_susp:
                t_new = mm["t"]
                break
        assert t_new is not None
        await ws.close()
        await cl.post(f"/api/runs/{rid}/stop", json={})
        data = rec.read_bytes()
        heads = [protocol.peek_meta(m) for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]
        assert sum(1 for h in heads if h["type"] == "header") == 1
        # continued from the state saved at the suspension (owner, 2026-10-29), not recomputed
        assert any(h["type"] == "notice" and "The world continued from its saved state" in english(h.get("text", "")) for h in heads)
        ts = [h["t"] for h in heads if h["type"] == "frame"]
        assert ts == sorted(ts) and ts[-1] > t_susp
        r = await cl.delete(f"/api/runs/{rid}")
        assert r.status == 200 and not rec.exists()
        # a bad request is refused with a reason
        r = await cl.post("/api/runs", json={"viz": "v01_light_travel", "params": {"kinematics": "nope"}})
        assert r.status == 400


def test_api_end_to_end(tmp_path):
    asyncio.run(_run_api(tmp_path))


async def _worker_error(tmp_path):
    app = create_app(tmp_path)
    async with TestClient(TestServer(app)) as cl:
        # a combination the schema accepts but the world refuses when it is built (v04: the start inside the body)
        r = await cl.post("/api/runs", json={"viz": "v04_orbits", "params": {"radius_km": 1000, "r0": 2.1}})
        rid = (await r.json())["id"]
        for _ in range(200):
            meta = await (await cl.get(f"/api/runs/{rid}")).json()
            if meta["state"] != "running":
                break
            await asyncio.sleep(0.1)
        # review UX-params P1: the run is failed (not resumable: it has no world), and says why in the owner's terms
        assert meta["state"] == "failed", meta["state"]
        assert english(meta["errors"][-1]).startswith("World not created: ") and "Traceback" not in english(meta["errors"][-1])
        row = [x for x in await (await cl.get("/api/runs")).json() if x["id"] == rid][0]
        assert row["error"] == meta["errors"][-1]  # the run list shows the reason
        ws = await cl.ws_connect(f"/ws/runs/{rid}")
        seen = []
        while True:
            m = await asyncio.wait_for(ws.receive(), 30)
            meta2, _ = protocol.decode(m.data)
            seen.append(meta2)
            if meta2["type"] == "history_end":
                break
        await ws.close()
        end = seen[-1]
        assert end["resumable"] is False and end["start_error"] == meta["errors"][-1]
        assert [x["type"] for x in seen if x["type"] == "header"] == []  # nothing of the world was recorded
        assert [x["type"] for x in seen if x["type"] in ("error", "end")] == ["error", "end"]


def test_worker_reports_refused_laws(tmp_path):
    asyncio.run(_worker_error(tmp_path))


async def _housekeeping(tmp_path):
    """A busy server frees a worker by suspending the run idle longest without viewers; runs whose last action is
    older than keep_days (3 by default) are removed unless kept; a restorable run interrupted by a server restart is
    loaded as suspended."""
    import time as _time
    app = create_app(tmp_path, max_workers=1, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        assert mgr.keep_days == 3.0
        a = (await (await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c"})).json())["id"]
        r = await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c"})
        b = (await r.json())["id"]
        assert r.status == 200 and mgr.get(a).meta["state"] == "suspended" and mgr.get(b).running
        await cl.post(f"/api/runs/{b}/stop", json={})
        mgr.get(a).meta["last_action"] = _time.time() - 4 * 86400
        mgr.get(b).meta["last_action"] = _time.time() - 4 * 86400
        mgr.get(b).meta["keep"] = True
        assert mgr.cleanup() == [a] and b in mgr.runs
    meta = json.loads((tmp_path / b / "meta.json").read_text())
    meta["state"] = "running"
    (tmp_path / b / "meta.json").write_text(json.dumps(meta))
    app2 = create_app(tmp_path)
    assert app2[MGR].get(b).meta["state"] == "suspended"


def test_housekeeping_frees_workers_and_removes_old_runs(tmp_path):
    asyncio.run(_housekeeping(tmp_path))


async def _removal_period(tmp_path):
    """The removal period is set on the catalogue page and kept on the server (owner, 2026-10-29): whole days only;
    applied at once; a period that would remove runs is refused with their list until exactly those runs are
    confirmed; kept across a restart and used by the cleanup; a bad saved value falls back to the option."""
    import time as _time
    app = create_app(tmp_path, max_workers=2)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        assert (await (await cl.get("/api/settings/runs")).json())["keep_days"] == 3
        for bad in ({"keep_days": 0}, {"keep_days": 2.5}, {"keep_days": 3651}, {"keep_days": True},
                    {"keep_days": "5"}, {"keep_days": None}, {}, {"keep_days": 3, "x": 1},
                    {"keep_days": 1, "confirm": "abc"}, [5]):
            assert (await cl.put("/api/settings/runs", json=bad)).status == 400, bad
        for raw in ("[", '{"keep_days": NaN}', '{"keep_days": Infinity}'):
            assert (await cl.put("/api/settings/runs", data=raw)).status == 400, raw
        ids = []
        for _ in range(3):
            rid = (await (await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c"})).json())["id"]
            await cl.post(f"/api/runs/{rid}/stop", json={})
            ids.append(rid)
        a, b, c = ids
        for rid in (a, b):
            mgr.get(rid).meta["last_action"] = _time.time() - 2 * 86400
        mgr.get(b).meta["keep"] = True
        r = await cl.put("/api/settings/runs", json={"keep_days": 1})
        assert r.status == 409 and (await r.json())["would_remove"] == [a]
        assert mgr.keep_days == 3 and a in mgr.runs and not (tmp_path / "settings.json").exists()
        r = await cl.put("/api/settings/runs", json={"keep_days": 1, "confirm": [c]})  # not the runs it would remove
        assert r.status == 409 and a in mgr.runs
        r = await cl.put("/api/settings/runs", json={"keep_days": 1, "confirm": [a]})
        assert r.status == 200 and await r.json() == {"keep_days": 1, "removed": [a]}
        assert a not in mgr.runs and not (tmp_path / a).exists() and b in mgr.runs and c in mgr.runs
        r = await cl.put("/api/settings/runs", json={"keep_days": 10})  # a longer period removes nothing, asks nothing
        assert r.status == 200 and await r.json() == {"keep_days": 10, "removed": []}
        assert json.loads((tmp_path / "settings.json").read_text()) == {"keep_days": 10}
        mgr.get(c).meta["last_action"] = _time.time() - 5 * 86400
        assert mgr.cleanup() == [] and c in mgr.runs
        mgr.get(c).meta["last_action"] = _time.time() - 11 * 86400
        assert mgr.cleanup() == [c]
    app2 = create_app(tmp_path, keep_days=3.0)
    assert app2[MGR].keep_days == 10 and "settings.json" not in app2[MGR].runs and b in app2[MGR].runs
    for saved in ('{"keep_days": 0}', '{"keep_days": 2.5}', "not json", "{}"):
        (tmp_path / "settings.json").write_text(saved)
        assert create_app(tmp_path, keep_days=4.0)[MGR].keep_days == 4.0, saved


def test_the_removal_period_is_set_on_the_page_and_kept_on_the_server(tmp_path):
    asyncio.run(_removal_period(tmp_path))


async def _legal(tmp_path):
    """The licence page and its texts reach a viewer of the player (review of 2026-10-29, R4, R8): the code's licence,
    the notices with three.js, its MIT text; only the listed texts are served."""
    app = create_app(tmp_path)
    async with TestClient(TestServer(app)) as cl:
        page = await cl.get("/legal")
        assert page.status == 200 and "Licence, citation and disclaimer" in await page.text()
        texts = {}
        for name in ("LICENSE.md", "NOTICE", "PUBLICATIONS.md", "COMMERCIAL.md", "LICENSE-DOCS.txt", "three.js-LICENSE"):
            r = await cl.get(f"/legal/{name}")
            assert r.status == 200 and r.content_type == "text/plain", name
            texts[name] = await r.text()
        assert "lfphys Research Licence 1.0" in texts["LICENSE.md"] and "three.js r185.1" in texts["NOTICE"]
        assert "Permission is hereby granted" in texts["three.js-LICENSE"]
        for bad in ("settings.json", "..%2F..%2FAGENTS.md", "app.py"):
            assert (await cl.get(f"/legal/{bad}")).status == 404, bad
        for page in ("/", "/run", "/settings"):
            assert 'href="/legal"' in await (await cl.get(page)).text(), page
        cite = (await (await cl.get("/api/health")).json())["cite"]  # the version to cite, shown on /legal (§5)
        assert cite["version"] == "0.1.0" and len(cite["code"]) == 12 and "lfphys" in cite["text"]


def test_the_licence_page_serves_the_licences_and_notices(tmp_path):
    asyncio.run(_legal(tmp_path))


def test_runner_coalesces_set_commands():
    from lfviz.sim import Runner
    msgs = [{"cmd": "set", "args": {"values": {"a": 1}}}, {"cmd": "set", "args": {"values": {"a": 2, "b": 3}}},
            {"cmd": "play"}, {"cmd": "set", "args": {"values": {"c": 4}}}]
    out = Runner.coalesce(msgs)
    assert out == [{"cmd": "set", "args": {"values": {"a": 2, "b": 3}}}, {"cmd": "play"},
                   {"cmd": "set", "args": {"values": {"c": 4}}}]


def test_runner_measures_the_speed_the_world_reaches():
    """The frames carry the world's actual speed (world seconds per wall second over the last 1.5 s of play): equal to
    the chosen speed when the computation keeps up, below it (and `lag`) when it does not (the owner's note of
    2026-10-28: at high speeds the black-hole world ran at 1 % of the label and the player did not say so)."""
    import queue
    import threading
    import time as _time

    from lfviz.sim import Runner, Simulation

    class Slow(Simulation):
        cost = 0.0  # wall seconds per world second

        def header(self):
            return {"title": "t"}, {}

        def advance(self, t_target):
            _time.sleep(self.cost * (t_target - self.t))
            self.t = t_target

        def frame(self):
            return {}, {}

        step = 0.05

        def max_step(self):
            return self.step

    # keeps up; falls behind inside a frame (the advance stops short); one step longer than a frame (review B4-11:
    # `lag` stayed false there although the world ran at half speed)
    for cost, speed, keeps_up, step in ((0.0, 2.0, True, 0.05), (0.5, 20.0, False, 0.05), (0.5, 20.0, False, None)):
        frames = []
        sim = Slow({}, 1, lambda m, b=None: frames.append(m) if m.get("type") == "frame" else None)
        sim.cost, sim.step = cost, step
        q = queue.Queue()
        r = Runner(sim, sim.emit, q)
        th = threading.Thread(target=r.run, daemon=True)
        th.start()
        q.put({"cmd": "speed", "args": {"value": speed}})
        q.put({"cmd": "play"})
        _time.sleep(2.5)
        r.stopped = True
        th.join(2)
        rates = [f["speed_actual"] for f in frames if f.get("speed_actual") is not None]
        assert rates, frames[-3:]
        if keeps_up:
            assert abs(rates[-1] / speed - 1) < 0.05 and not frames[-1]["lag"]
        else:
            assert rates[-1] < 0.5 * speed and frames[-1]["lag"]


def test_runner_refuses_frame_keys_of_its_own():
    """A world's frame must not carry the runner's keys (review B4-1: `rate` silently overwrote v04's dτ/dt)."""
    from lfviz.sim import RUNNER_FRAME_KEYS, Runner, Simulation

    class Clash(Simulation):
        def header(self):
            return {"title": "t"}, {}

        def advance(self, t_target):
            self.t = t_target

        def frame(self):
            return {"lag": 1.0}, {}

    sim = Clash({}, 1, lambda m, b=None: None)
    r = Runner(sim, sim.emit, None)
    with pytest.raises(ValueError, match="lag"):
        r._frame(1.0)
    assert {"lag", "speed_actual", "cpu_ms", "type"} <= RUNNER_FRAME_KEYS


async def _new_world_in_same_run(tmp_path):
    """Owner, 2026-10-23: a new world is created inside the running run (same id, same record), not as a new run."""
    app = create_app(tmp_path)
    async with TestClient(TestServer(app)) as cl:
        r = await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c", "seed": 3})
        rid = (await r.json())["id"]
        r = await cl.post(f"/api/runs/{rid}/command",
                          json={"cmd": "new_world", "args": {"params": {"scenario": "measure_c",
                                                                         "kinematics": "ether", "gravity": "none"}}})
        assert r.status == 200
        for _ in range(100):
            meta = await (await cl.get(f"/api/runs/{rid}")).json()
            if len(meta.get("worlds", [])) >= 2:
                break
            await asyncio.sleep(0.1)
        assert [w["n"] for w in meta["worlds"]] == [1, 2] and meta["params"]["kinematics"] == "ether"
        assert meta["modifications"] and len((await (await cl.get("/api/runs")).json())) == 1
        # a bad new world is refused and the current one goes on
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "new_world", "args": {"params": {"c_factor": -1}}})
        await asyncio.sleep(0.5)
        await cl.post(f"/api/runs/{rid}/stop", json={})
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        assert len(meta["worlds"]) == 2 and any("New world not created" in english(e) for e in meta.get("errors", []))
        data = (tmp_path / rid / "stream.lfrec").read_bytes()
        heads = [protocol.peek_meta(m) for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]
        heads = [h for h in heads if h["type"] == "header"]
        assert [h["world"] for h in heads] == [1, 2] and heads[1]["params"]["kinematics"] == "ether"


def test_new_world_inside_the_same_run(tmp_path):
    asyncio.run(_new_world_in_same_run(tmp_path))


async def _settings_api(tmp_path, monkeypatch):
    from lfviz import devices
    monkeypatch.setattr(devices, "SETTINGS_FILE", tmp_path / "settings.local.json")  # never the owner's file
    devices._CACHE.clear()
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        r = await cl.get("/api/devices")
        d = await r.json()
        assert r.status == 200, d
        assert d["devices"]["cpu"]["available"] and "gpu" in d["devices"]
        names = {k["name"]: k for k in d["kernels"]}
        assert names["optics.angular_spectrum"]["gpu"] and not names["gravity.geodesics"]["gpu"]
        # a change is validated by the engine and saved at once; impossible choices come back adjusted, with notes
        r = await cl.put("/api/settings", json={"kernels": {
            "optics.angular_spectrum": {"device": "cpu", "precision": "fp32"},
            "gravity.geodesics": {"device": "gpu", "precision": "fp32"}}})
        body = await r.json()
        assert r.status == 200, body
        assert body["settings"]["kernels"]["optics.angular_spectrum"] == {"device": "cpu", "precision": "fp32"}
        assert body["settings"]["kernels"]["gravity.geodesics"] == {"device": "cpu", "precision": "fp64"}
        assert body["notes"] and json.loads((tmp_path / "settings.local.json").read_text())["kernels"]
        assert (await (await cl.get("/api/settings")).json())["kernels"]["optics.angular_spectrum"]["precision"] == "fp32"
        r = await cl.get("/settings")
        assert r.status == 200 and "Devices and precision" in await r.text()
        # a run carries the settings in force at its start: in its passport and in its header
        r = await cl.post("/api/runs", json={"viz": "v06_qcd", "preset": "standard", "seed": 3})
        rid = (await r.json())["id"]
        ws = await cl.ws_connect(f"/ws/runs/{rid}")
        header = None
        for _ in range(200):
            msg = await asyncio.wait_for(ws.receive(), 30)
            if msg.type != WSMsgType.BINARY:
                continue
            m, _ = protocol.decode(msg.data)
            if m.get("type") == "header":
                header = m
                break
        await ws.close()
        await cl.post(f"/api/runs/{rid}/stop", json={})
        assert header["backend"]["settings"]["kernels"]["optics.angular_spectrum"]["precision"] == "fp32"
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        assert meta["backend_settings"]["kernels"]["optics.angular_spectrum"]["device"] == "cpu"


def test_device_settings_api(tmp_path, monkeypatch):
    asyncio.run(_settings_api(tmp_path, monkeypatch))


async def _settings_hardening(tmp_path, monkeypatch):
    """Review B1-10, B1-11: malformed settings get 400 with the reason (never a traceback, never a wiped file);
    writes are serialised (a calibration and a change in flight both survive); a run can override the devices."""
    from lfviz import devices
    monkeypatch.setattr(devices, "SETTINGS_FILE", tmp_path / "settings.local.json")  # never the owner's file
    devices._CACHE.clear()
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        r = await cl.put("/api/settings", json={"kernels": {"optics.angular_spectrum": {"device": "cpu"}}})
        assert r.status == 200
        for bad in ({"kernels": []}, {"kernels": {"optics.angular_spectrum": "gpu"}},
                    {"crossover": {"optics.angular_spectrum": True}}, {"crossover": {"optics.angular_spectrum": -5}},
                    {"crossover": {"optics.angular_spectrum": "big"}}, {"other": 1}, [1, 2]):
            r = await cl.put("/api/settings", json=bad)
            text = await r.text()
            assert r.status == 400 and "Traceback" not in text, (bad, r.status, text)
        r = await cl.put("/api/settings", data=json.dumps({"kernels": {"x" * 200000: {}}}),
                         headers={"Content-Type": "application/json"})
        assert r.status == 413
        assert json.loads((tmp_path / "settings.local.json").read_text())["kernels"]["optics.angular_spectrum"][
            "device"] == "cpu"  # nothing above touched the file
        # serialised writes: the engine answers slowly for the first PUT; the second PUT and a calibration that
        # completes meanwhile must all end up in the file, the newest choice winning
        real = devices._backend
        delays = iter([0.5, 0.0])

        async def slow(*args, **kw):
            if "--configure" in args:
                await asyncio.sleep(next(delays, 0.0))
            if "--calibrate" in args:
                return {"calibration": {"optics.angular_spectrum": {"rows": [], "crossover": 4096,
                                                                    "measured": "now", "gpu": "test"}}}
            return await real(*args, **kw)
        monkeypatch.setattr(devices, "_backend", slow)
        a = asyncio.create_task(cl.put("/api/settings", json={"kernels": {"optics.angular_spectrum":
                                                                           {"device": "gpu"}}}))
        await asyncio.sleep(0.05)
        b = asyncio.create_task(cl.put("/api/settings", json={"kernels": {"optics.angular_spectrum":
                                                                           {"device": "cpu"}}}))
        c = asyncio.create_task(cl.post("/api/settings/calibrate", json={}))
        await asyncio.gather(a, b, c)
        saved = json.loads((tmp_path / "settings.local.json").read_text())
        assert saved["kernels"]["optics.angular_spectrum"]["device"] == "cpu"
        assert saved["crossover"]["optics.angular_spectrum"] == 4096 and "calibration" in saved
        monkeypatch.setattr(devices, "_backend", real)
        # a run with its own devices: validated, recorded in its passport, the file unchanged
        r = await cl.post("/api/runs", json={"viz": "v06_qcd", "preset": "standard", "seed": 3,
                                             "backend": {"kernels": {"optics.angular_spectrum": "gpu"}}})
        assert r.status == 400 and "devices" in (await r.json())["text"]
        r = await cl.post("/api/runs", json={"viz": "v06_qcd", "preset": "standard", "seed": 3, "backend": {
            "kernels": {"optics.angular_spectrum": {"device": "cpu", "precision": "fp32"}}}})
        rid = (await r.json())["id"]
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        await cl.post(f"/api/runs/{rid}/stop", json={})
        bs = meta["backend_settings"]
        assert bs["kernels"]["optics.angular_spectrum"]["precision"] == "fp32" and bs["override"]
        assert meta["devices_override"] is True
        assert json.loads((tmp_path / "settings.local.json").read_text())["kernels"]["optics.angular_spectrum"][
            "precision"] == "fp64"


def test_device_settings_are_validated_serialised_and_overridable_per_run(tmp_path, monkeypatch):
    asyncio.run(_settings_hardening(tmp_path, monkeypatch))


def test_view_command_is_refused_by_worlds_without_views_and_never_changes_the_world():
    """The runner's command "view" (RULES.md §2.9): a world without view requests answers with an error and goes on."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from harness import Harness
    h = Harness("v06_qcd", "standard")
    n_err = len(h.errors())
    h.cmd("view", op="plane", id=1)
    # in the owner's terms (review UX-ui U13): what was not done, then the world's own reason
    assert len(h.errors()) == n_err + 1 and english(h.errors()[-1]).startswith("Slice not built: this world has no view requests")


async def _approximations_follow_the_world(tmp_path):
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        r = await cl.post("/api/runs", json={"viz": "v08_wave_3d", "preset": "double_slices", "seed": 1,
                                             "params": None})
        rid = (await r.json())["id"]
        ws = await cl.ws_connect(f"/ws/runs/{rid}")

        async def until(pred, limit=120):
            for _ in range(limit * 20):
                msg = await asyncio.wait_for(ws.receive(), 120)
                if msg.type == WSMsgType.BINARY:
                    m, _ = protocol.decode(msg.data)
                    if pred(m):
                        return m
            raise AssertionError("message not seen")
        await until(lambda m: m.get("type") == "slice")
        runs = await (await cl.get("/api/runs")).json()
        assert next(x for x in runs if x["id"] == rid)["approximations"]
        await ws.send_str(json.dumps({"cmd": "view", "args": {"op": "remove", "id": 1}}))
        await until(lambda m: m.get("type") == "modelling")
        await asyncio.sleep(0.2)
        runs = await (await cl.get("/api/runs")).json()
        assert next(x for x in runs if x["id"] == rid)["approximations"] == []  # review C11
        await ws.close()
        await cl.post(f"/api/runs/{rid}/stop", json={})


def test_run_list_follows_the_worlds_approximations(tmp_path):
    asyncio.run(_approximations_follow_the_world(tmp_path))


async def _wait_state(cl, rid, cond, n=200):
    for _ in range(n):
        meta = await (await cl.get(f"/api/runs/{rid}")).json()
        if cond(meta):
            return meta
        await asyncio.sleep(0.1)
    raise AssertionError(meta)


def _messages(path):
    data = path.read_bytes()
    return [protocol.peek_meta(m) for _, m in protocol.iter_stream(data, len(protocol.MAGIC))]


async def _resume_races_and_failures(tmp_path):
    """Review C1-1, C1-2, C1-14, C1-15: two ⏺ at once resume one worker; a world-changing command while the world is
    rebuilt is refused (it could not be applied before the rebuild ends); a failed rebuild leaves the run suspended and
    ⏺ tries again once the cause is gone; a run without viewers is deleted even while it computes, one open in a tab
    is not."""
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        rid = (await (await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c"})).json())["id"]
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await _wait_state(cl, rid, lambda m: m.get("sim_t", 0) > 0)
        await cl.post(f"/api/runs/{rid}/stop", json={})
        assert mgr.get(rid).meta["state"] == "suspended"
        rs = await asyncio.gather(*(cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"}) for _ in range(3)))
        assert [r.status for r in rs] == [200] * 3
        run = mgr.get(rid)
        assert mgr.n_running() == 1 and run.meta["resumed"] == 1
        assert sum(1 for m in _messages(run.stream_path) if m["type"] == "notice"
                   and english(m["text"]).startswith("Going on")) == 1
        run.rebuilding = True  # as while a long record is replayed
        r = await cl.post(f"/api/runs/{rid}/command", json={"cmd": "set", "args": {"values": {}}})
        assert r.status == 409 and "being restored" in (await r.json())["text"]
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})).status == 200
        run.rebuilding = False
        ws = await cl.ws_connect(f"/ws/runs/{rid}")
        r = await cl.delete(f"/api/runs/{rid}")
        assert r.status == 409 and run.running  # open in a tab
        await ws.close()
        await asyncio.sleep(0.2)
        r = await cl.delete(f"/api/runs/{rid}")
        assert r.status == 200 and rid not in mgr.runs and not run.dir.exists() and not run.running

        # a rebuild that fails (here: the record's parameters unknown to the code, as after a rename) ...
        rid = (await (await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c"})).json())["id"]
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await _wait_state(cl, rid, lambda m: m.get("sim_t", 0) > 0)
        await cl.post(f"/api/runs/{rid}/stop", json={})
        run = mgr.get(rid)
        good = run.stream_path.read_bytes()

        def with_header_params(extra):
            out, pos = bytearray(protocol.MAGIC), len(protocol.MAGIC)
            for _, msg in protocol.iter_stream(good, pos):
                meta, blobs = protocol.decode(msg)
                if meta["type"] == "header":
                    meta = {**meta, "params": {**meta["params"], **extra}}
                    meta.pop("blobs", None)
                    msg = protocol.encode(meta, blobs)
                out += protocol.frame_stream_item(msg)
            return bytes(out)

        run.stream_path.write_bytes(with_header_params({"renamed_param": 1}))
        for f in run.ckpt_dir.glob("*.pkl"):  # no saved state: the world is rebuilt from the record's parameters
            f.unlink()
        run.entries, run.size = [], len(protocol.MAGIC)
        mgr.runs[rid] = run = mgr._load_one(run.dir)
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        meta = await _wait_state(cl, rid, lambda m: m["state"] != "running")
        assert meta["state"] == "suspended" and "renamed_param" in english(meta["resume_error"])
        assert run.meta["sim_t"] > 0  # the failure is reported at the record's end, not at t = 0
        # ... is tried again by the next ⏺ once its cause is gone
        n = len(run.entries)
        tail = run.stream_path.read_bytes()[len(with_header_params({"renamed_param": 1})):]
        run.stream_path.write_bytes(good + tail)
        mgr.runs[rid] = run = mgr._load_one(run.dir)
        assert len(run.entries) == n
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        meta = await _wait_state(cl, rid, lambda m: not m.get("resume_error") and m["state"] == "running"
                                 and any("World restored" in english(x.get("text") or "") for x in _messages(run.stream_path)))
        await cl.post(f"/api/runs/{rid}/stop", json={})


def test_resume_races_failures_and_delete(tmp_path):
    asyncio.run(_resume_races_and_failures(tmp_path))


async def _resume_from_checkpoint(tmp_path, monkeypatch):
    """Owner, 2026-10-29: a suspended run continues from its world's last state, not by recomputing its record. The
    suspension writes a checkpoint (recorded with its place); ⏺ loads it; without a usable one — its file gone, or
    the code changed since — the world is rebuilt from its record as before."""
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        rid = (await (await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c"})).json())["id"]
        run = mgr.get(rid)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await _wait_state(cl, rid, lambda m: m.get("sim_t", 0) > 0)
        await cl.post(f"/api/runs/{rid}/stop", json={})
        ck = [m for m in _messages(run.stream_path) if m["type"] == "checkpoint"]
        assert ck and ck[-1]["reason"] == "suspend" and not ck[-1].get("error")
        assert (run.ckpt_dir / ck[-1]["file"]).is_file() and run.disk_size() > run.size
        t_ck = ck[-1]["t"]
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        await _wait_state(cl, rid, lambda m: m["state"] == "running" and m.get("sim_t", 0) > t_ck)
        texts = [english(m.get("text") or "") for m in _messages(run.stream_path)]
        assert any("Going on from the world's saved state" in x for x in texts)
        assert any("The world continued from its saved state" in x for x in texts)
        assert not any("World restored" in x for x in texts)
        assert run.meta["resumes"][-1]["from"] == "checkpoint"
        # without its file: rebuilt from the record
        await cl.post(f"/api/runs/{rid}/stop", json={})
        for f in run.ckpt_dir.glob("*.pkl"):
            f.unlink()
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        await _wait_state(cl, rid, lambda m: m["state"] == "running" and any(
            "World restored" in english(x.get("text") or "") for x in _messages(run.stream_path))
            and (m.get("resumes") or [{}])[-1].get("from") == "replay")
        # the code changed since the checkpoint was written: rebuilt from the record
        await cl.post(f"/api/runs/{rid}/stop", json={})
        assert list(run.ckpt_dir.glob("*.pkl"))
        from lfviz import checkpoint as CKmod
        monkeypatch.setattr(CKmod, "files_hash", lambda root, files: "another-code")  # a file the world ran changed
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        await _wait_state(cl, rid, lambda m: m["state"] == "running" and (m.get("resumes") or [{}])[-1].get("from") == "replay")
        await cl.post(f"/api/runs/{rid}/stop", json={})


def test_a_suspended_run_continues_from_its_checkpoint(tmp_path, monkeypatch):
    asyncio.run(_resume_from_checkpoint(tmp_path, monkeypatch))


async def _record_during_suspension(tmp_path):
    """Review CK-4: ⏺ pressed while the run is being suspended (its worker writing its checkpoint) waits for the
    suspension and resumes the run, instead of being acknowledged and lost; the passport says how the worker actually
    continued (review CK-11)."""
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        rid = (await (await cl.post("/api/runs", json={"viz": "v02_double_slit"})).json())["id"]
        run = mgr.get(rid)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await _wait_state(cl, rid, lambda m: m.get("sim_t", 0) > 0)
        for delay in (0.0, 0.01, 0.05):
            async def play_soon():
                await asyncio.sleep(delay)
                return await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
            stop, play = await asyncio.gather(cl.post(f"/api/runs/{rid}/stop", json={}), play_soon())
            assert stop.status == 200 and play.status == 200
            await _wait_state(cl, rid, lambda m: m["state"] == "running" and m.get("playing"))
            assert run.running and run.meta["resumes"][-1]["from"] == "checkpoint", run.meta.get("resumes")
        await cl.post(f"/api/runs/{rid}/stop", json={})


def test_record_pressed_during_a_suspension_resumes_the_run(tmp_path):
    asyncio.run(_record_during_suspension(tmp_path))


async def _record_is_the_truth(tmp_path):
    """Review C1-10, C1-16: a record cut by a crash is cut back to its last whole message at the next start (the cut
    bytes kept apart) and goes on correctly; an unreadable record does not keep the server down; a meta.json that missed
    a new world (a crash within seconds of it) is corrected from the record, and the resume rebuilds the new world."""
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        rid = (await (await cl.post("/api/runs", json={"viz": "v01_light_travel", "preset": "measure_c",
                                                         "seed": 5})).json())["id"]
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        await _wait_state(cl, rid, lambda m: m.get("sim_t", 0) > 0)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "new_world", "args": {
            "params": {"scenario": "measure_c", "kinematics": "ether", "gravity": "none"}}})
        await _wait_state(cl, rid, lambda m: len(m.get("worlds", [])) == 2)
        await asyncio.sleep(0.5)
        await cl.post(f"/api/runs/{rid}/stop", json={})
    rec = tmp_path / rid / "stream.lfrec"
    whole = rec.read_bytes()
    n_whole = len(_messages(rec))
    meta = json.loads((tmp_path / rid / "meta.json").read_text())
    stale = {**meta, "worlds": meta["worlds"][:1], "params": meta["worlds"][0]["params"], "sim_t": 123.0,
             "state": "running"}
    (tmp_path / rid / "meta.json").write_text(json.dumps(stale))
    rec.write_bytes(whole + struct.pack("<I", 1000) + b"cut msg")  # a message cut by the crash
    bad = tmp_path / "20260101-000000-v01-dead"
    bad.mkdir()
    (bad / "meta.json").write_text(json.dumps({"id": bad.name, "viz": "v01_light_travel", "state": "suspended"}))
    (bad / "stream.lfrec").write_bytes(b"\0" * 64)  # zeros after a power cut: not a record
    app = create_app(tmp_path, max_workers=2, idle_pause=60, idle_suspend=3600)  # the server comes up
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        run = mgr.get(rid)
        assert bad.name not in mgr.runs and run.meta["state"] == "suspended"
        assert rec.read_bytes() == whole and (tmp_path / rid / "stream.cut-tail.bin").read_bytes().endswith(b"cut msg")
        assert [w["n"] for w in run.meta["worlds"]] == [1, 2] and run.meta["params"]["kinematics"] == "ether"
        assert run.meta["sim_t"] == [m["t"] for m in _messages(rec) if m.get("t") is not None][-1] != 123.0
        w = run._latest_world()
        assert w["header"]["world"] == 2 and w["seed0"] == 5
        # the suspension saved world 2's state: the run continues from it (owner, 2026-10-29), not from world 1
        assert w["checkpoint"] is not None and Path(w["checkpoint"]["file"]).name.startswith("w2-")
        assert (await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})).status == 200
        await _wait_state(cl, rid, lambda m: any("The world continued from its saved state" in english(x.get("text") or "")
                                                 for x in _messages(rec)))
        await asyncio.sleep(0.5)
        await cl.post(f"/api/runs/{rid}/stop", json={})
    msgs = _messages(rec)
    assert len(msgs) > n_whole and msgs[-1]["type"] == "end"
    assert sum(len(m) + 4 for _, m in protocol.iter_stream(rec.read_bytes(), len(protocol.MAGIC))) \
        == len(rec.read_bytes()) - len(protocol.MAGIC)  # every byte belongs to a whole message
    assert sum(1 for m in msgs if m["type"] == "header") == 2


def test_the_record_is_the_truth_after_a_crash(tmp_path):
    asyncio.run(_record_is_the_truth(tmp_path))


def _fake_record(root, rid, created, last_action=None, mb=1):
    d = root / rid
    d.mkdir()
    hdr = protocol.encode({"type": "header", "t": 0.0, "world": 1, "params": {}, "seed": 1, "title": rid},
                          {"pad": np.zeros(int(mb * 1e6), np.uint8)})
    (d / "stream.lfrec").write_bytes(protocol.MAGIC + protocol.frame_stream_item(hdr))
    meta = {"id": rid, "viz": "v01_light_travel", "created": created, "state": "suspended", "restorable": True}
    if last_action is not None:
        meta["last_action"] = last_action
    (d / "meta.json").write_text(json.dumps(meta))
    return d


def test_cleanup_follows_the_last_action_and_spares_open_runs(tmp_path):
    """Review C1-9: beyond the quota the run with the oldest last action goes first (not the oldest created); a run
    open in a tab is never removed; a visit to a suspended run is saved at once; a record from before the last action
    was kept gets its record's time, not the time of the server's start."""
    import os
    import time as _time

    from lfviz.runs import RunManager
    now = _time.time()
    _fake_record(tmp_path, "a-old-but-used", "2026-10-01T00:00:00", now - 60)
    _fake_record(tmp_path, "b-newer-unused", "2026-10-20T00:00:00", now - 2 * 86400)
    _fake_record(tmp_path, "c-viewed", "2026-10-21T00:00:00", now - 2.5 * 86400)
    d = _fake_record(tmp_path, "d-before-last-action", "2026-10-22T00:00:00")
    os.utime(d / "stream.lfrec", (now - 5 * 86400, now - 5 * 86400))
    mgr = RunManager(tmp_path, quota_gb=2.5e-3)
    assert abs(mgr.get("d-before-last-action").meta["last_action"] - (now - 5 * 86400)) < 5
    mgr.get("c-viewed").viewers.add(object())
    assert mgr.cleanup() == ["d-before-last-action", "b-newer-unused"]
    assert set(mgr.runs) == {"a-old-but-used", "c-viewed"}
    run = mgr.get("a-old-but-used")
    run.meta["last_action"] = now - 10 * 86400
    run.touch()
    assert json.loads((run.dir / "meta.json").read_text())["last_action"] > now - 5


# --- reviews 2026-11-04 UX-params and UX-ui: what the owner reads, the memory budget, busy and cancel ---------------------

def test_parameter_refusals_are_in_the_owners_words():
    """UX-params P2: a refused value names the parameter by its label and unit, says what is allowed, and carries the
    parameter's id for the form; an emptied field is not read as 0. P17: an option may carry its own show_if."""
    from lfviz.params import Param, ParamError, Schema
    sch = Schema([Param("lam_nm", T("Wavelength λ, nm"), "float", 633.0, min=300.0, max=1600.0, live=True),
                  Param("n", T("Number of slits"), "int", 2, min=1, max=10),
                  Param("species", T("Particle"), "select", "photon", options=[("photon", T("photon")), ("electron", T("electron"))]),
                  Param("mark", T("Path mark"), "select", "pol", standard="pol",
                        options=[("pol", T("polarizer")), ("mic", T("microscope"), {"species": ["electron"]})])],
                 presets={"a": {"label": T("Scenario A"), "params": {}}})
    _, errs = sch.resolve(None, {"lam_nm": 2000})
    assert [str(e) for e in errs] == ["“Wavelength λ, nm”: 2000 is above the maximum 1600; allowed: from 300 to 1600"]
    assert isinstance(errs[0], ParamError) and errs[0].pid == "lam_nm"
    _, errs = sch.resolve(None, {"lam_nm": ""})
    assert str(errs[0]) == "“Wavelength λ, nm”: the field is empty — enter a number from 300 to 1600"
    _, errs = sch.resolve(None, {"n": "abc", "species": "neutron"})
    assert str(errs[0]).startswith("“Number of slits”: “abc” is not a whole number") and \
        "there is no option “neutron”" in str(errs[1])
    _, errs = sch.resolve("zzz", {})
    assert [str(e) for e in errs] == ["there is no scenario “zzz”; there are: “Scenario A”"]
    _, errs = sch.coerce_live({"lam_nm": 633.0}, {"lam_nm": 100.0, "n": 3})
    assert "is below the minimum 300" in str(errs[0]) and "“Number of slits” cannot be changed while the world runs" in str(errs[1])
    for e in errs:
        assert not any(w in e for w in ("max", "min", "cannot", "unknown", "lam_nm:"))
    opts = sch.by_id["mark"].to_json()["options"]
    assert opts == [{"value": "pol", "label": {"$t": "polarizer"}},
                    {"value": "mic", "label": {"$t": "microscope"}, "show_if": {"species": ["electron"]}}]
    params, errs = sch.resolve(None, {"mark": "mic", "species": "electron"})
    assert not errs and sch.modifications(params)[0]["value"] == {"$t": "microscope"}  # 3-tuples in the modified-physics list


def test_owner_text_of_refusals_and_failures():
    """UX-params P4, UX-ui U13 (the integrator's wording of 2026-11-05): a refusal is shown with what to change; a plain
    ValueError keeps its own text; known English library sentences are put into the owner's terms; any other exception
    is a short Russian sentence — its type and own text only as a one-line detail, never a traceback."""
    from lfviz.errors import Refusal, owner_text
    t, d = owner_text(Refusal(T("the packet is inside the wall"), hint=T("move it along x")), "scene")
    assert str(t) == "Scene not changed: the packet is inside the wall. What to change: move it along x" and d is None
    t, d = owner_text(ValueError(T("GR needs SR")), "build")
    assert str(t) == "World not created: GR needs SR" and d is None and t["a"]["body"] == {"$t": "GR needs SR"}
    t, d = owner_text(ValueError("Probabilities contain NaN"), "scene")
    assert "probabilities became not-a-number" in str(t) and d == "ValueError: Probabilities contain NaN"
    try:
        1 / 0
    except ZeroDivisionError as e:
        t, d = owner_text(e, "advance", t=1.5)
    t = str(t)
    assert t.startswith("The world's computation stopped at t = 1.5 s: internal error of the world — division by zero "
                        "(ZeroDivisionError)")
    assert "the run is saved" in t and "The world is paused" in t and "Traceback" not in t + d and "\n" not in d
    t, d = owner_text(MemoryError("Unable to allocate 591. GiB for an array with shape (440, 180400000)"), "build")
    assert str(t).startswith("World not created: out of memory (asked for 591 GB)") and "What to change" in str(t)
    t, _ = owner_text(KeyError("o1"), "scene")
    assert str(t) == ("Scene not changed: internal error of the world — KeyError — the run is saved; you can go back or "
                      "change the parameters")


def _toy_runner(out_stream, after_header_fails=False):
    """The toy section (tests/playgrounds) run by a Runner writing through the worker's Output, as in a worker."""
    import io  # noqa: F401
    from lfviz.worker import Output
    viz = registry.load("p99_toy")
    out = Output(out_stream)

    def make_world(pr, vals, sd):
        p, errs = viz["schema"].resolve(pr, vals or {})
        sim = viz["simulation"](p, 3, out.emit)
        if (vals or {}).get("drag") == 0.5:  # a world that fails to show itself
            def bad():
                raise ZeroDivisionError("float division by zero")
            sim.after_header = bad
        return sim, {"preset": pr}
    sim, _ = make_world("two", {"drag": 0.5} if after_header_fails else {}, 3)
    from lfviz.sim import Runner
    import queue
    r = Runner(sim, out.emit, queue.Queue(), make_world=make_world)
    r.out = out
    return r


def _decoded(stream):
    data = stream.getvalue()
    return [protocol.decode(m)[0] for _, m in protocol.iter_stream(data, 0)]


def test_a_world_that_fails_to_show_itself_is_not_built(tmp_path, monkeypatch):
    """UX-params P3: an exception in ``after_header`` (v13's continuity check at a zero scale) killed the worker and
    every ⏺ repeated «Мир не восстановлен: float division by zero». Now the first world is reported as not built and the
    worker ends with that reason (the server keeps the run failed, never resumable); a new world that fails so is
    refused whole and the previous one goes on."""
    import io
    monkeypatch.setenv("LFVIZ_EXTRA", str(Path(__file__).resolve().parent / "playgrounds"))
    s = io.BytesIO()
    r = _toy_runner(s, after_header_fails=True)
    assert r.start() is False
    msgs = _decoded(s)
    assert [m["type"] for m in msgs][-2:] == ["error", "end"] and msgs[-1]["reason"] == "world not built"
    assert english(msgs[-2]["text"]).startswith("World not created: internal error of the world — division by zero "
                                                "(ZeroDivisionError)")
    s2 = io.BytesIO()
    r2 = _toy_runner(s2)
    assert r2.start() is True
    n0, sim0 = len(_decoded(s2)), r2.sim
    r2.handle({"cmd": "new_world", "args": {"params": {"drag": 0.5}}})
    new = _decoded(s2)[n0:]
    assert [m["type"] for m in new] == ["busy", "busy", "command", "error"], [m["type"] for m in new]
    assert english(new[-1]["text"]).startswith("New world not created: internal error of the world") and \
        "The previous world goes on" in english(new[-1]["text"])
    assert r2.sim is sim0 and r2.world == 1
    r2.handle({"cmd": "new_world", "args": {"params": {"drag": 0.25}}})
    assert r2.world == 2 and [m["type"] for m in _decoded(s2)].count("header") == 2

    async def server_side():  # the run of a world not built is failed and says why, never «⏺ продолжит»
        app = create_app(tmp_path / "runs", max_workers=1)
        async with TestClient(TestServer(app)) as cl:
            run = app[MGR].get((await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two"})).json())["id"])
            for _ in range(300):
                if any(e.kind == "header" for e in run.entries):
                    break
                await asyncio.sleep(0.05)
            # what a worker writes when its first world fails to show itself (Runner.start), then it ends by itself
            run._ingest(protocol.encode({"type": "error", "t": 0.0, "text": T("World not created: a probe")}))
            run._ingest(protocol.encode({"type": "end", "t": 0.0, "reason": "world not built"}))
            run.proc.kill()
            await asyncio.wait_for(asyncio.shield(run._reader), 30)
            assert run.meta["state"] == "failed" and run.summary()["error"] == {"$t": "World not created: a probe"}
            ws = await cl.ws_connect(f"/ws/runs/{run.id}")
            while True:
                m, _ = protocol.decode((await asyncio.wait_for(ws.receive(), 30)).data)
                if m["type"] == "history_end":
                    break
            await ws.close()
            assert m["resumable"] is False and m["start_error"] == {"$t": "World not created: a probe"}
    asyncio.run(server_side())


def test_a_computing_command_is_announced_and_written_as_one_piece(monkeypatch):
    """UX-ui U9: a computing command is announced at once ("busy" with what it does, not recorded by the server), its
    messages are held and written after the announcement's end — so the server knows when it is done, and a cancel
    decided before that drops it whole."""
    import io
    monkeypatch.setenv("LFVIZ_EXTRA", str(Path(__file__).resolve().parent / "playgrounds"))
    s = io.BytesIO()
    r = _toy_runner(s)
    r.start()
    n0 = len(_decoded(s))
    r.handle({"cmd": "scene", "args": {"op": "add", "type": "particle", "values": {"x": 2.0}}})
    r.handle({"cmd": "play", "args": {}})
    new = _decoded(s)[n0:]
    assert [m["type"] for m in new] == ["busy", "busy", "command", "scene", "event", "state"]
    assert new[0]["on"] is True and english(new[0]["what"]) == "scene: an object “particle” is being added" and new[1]["on"] is False
    assert "busy" in __import__("lfviz.runs", fromlist=["NOT_RECORDED"]).NOT_RECORDED


async def _cancel(tmp_path):
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=60, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        mgr = app[MGR]
        rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two", "seed": 1})).json())["id"]
        run = mgr.get(rid)
        for _ in range(300):
            if any(e.kind == "header" for e in run.entries):
                break
            await asyncio.sleep(0.05)
        r = await cl.post(f"/api/runs/{rid}/cancel")
        assert r.status == 409 and "nothing to cancel" in (await r.json())["text"]
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})
        await asyncio.sleep(0.5)
        n = len(run.entries)
        # the worker announces a command it computes; the cancel is decided before its end arrives
        run._ingest(protocol.encode({"type": "busy", "on": True, "cmd": "scene", "what": T("scene: an object is being added"),
                                     "wall": 0.0, "t": run.meta.get("sim_t", 0.0)}))
        assert [x for x in await (await cl.get("/api/runs")).json() if x["id"] == rid][0]["busy"]["cmd"] == "scene"
        res = await (await cl.post(f"/api/runs/{rid}/cancel")).json()
        assert res["ok"] and res["cancelled"]["cmd"] == "scene"
        for _ in range(300):
            if run.running and not run.rebuilding:
                break
            await asyncio.sleep(0.05)
        assert run.running and run.meta["state"] == "running" and run.busy is None
        kinds = [protocol.peek_meta(run._read(e, {})).get("type") for e in run.entries[n:]]
        assert "notice" in kinds and "header" not in kinds  # resumed: the same world, from its record
        texts = [english(protocol.peek_meta(run._read(e, {})).get("text", "")) for e in run.entries[n:]]
        assert any(t.startswith("Cancelled: scene: an object is being added") for t in texts)
        await cl.post(f"/api/runs/{rid}/stop")


def test_cancel_puts_the_world_back_to_just_before_the_command(tmp_path, monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(Path(__file__).resolve().parent / "playgrounds"))
    asyncio.run(_cancel(tmp_path))


def test_workers_hold_a_memory_budget(tmp_path, monkeypatch):
    """UX-params P8 (one world took 31 GB of the shared host): every worker gets the budget as its hard limit of private
    memory, an allocation beyond it fails inside the worker (reported in Russian), and a world's estimate above it is
    refused before anything is built — at the start (400, the catalogue says why) and for a new world."""
    import subprocess
    import sys
    from lfviz import limits
    from lfviz.errors import owner_text
    code = ("import numpy as np, sys; sys.path.insert(0, %r); from lfviz import limits; limits.apply_hard_limit();\n"
            "try:\n np.ones(2**31 // 8)\nexcept MemoryError as e:\n print('MemoryError', e)\n") % str(Path(limits.__file__).parents[1])
    out = subprocess.run([sys.executable, "-c", code], env={**__import__("os").environ, limits.ENV: str(600 * 2**20)},
                         capture_output=True, text=True, timeout=60).stdout
    assert out.startswith("MemoryError"), out
    assert str(owner_text(MemoryError(out[12:]), "set")[0]).startswith("Change not applied: out of memory")
    assert 2**30 <= limits.default_budget(3) <= 8 * 2**30
    assert str(limits.fmt_bytes(591 * 2**30)) == "591 GB" and str(limits.fmt_bytes(6.56 * 2**30)) == "6.56 GB"
    assert limits.fmt_bytes(591 * 2**30) == {"$t": "{n:.3g} GB", "a": {"n": 591.0}}  # the number for the viewer

    monkeypatch.setenv("LFVIZ_EXTRA", str(Path(__file__).resolve().parent / "playgrounds"))
    sim_cls = registry.load("p99_toy")["simulation"]
    monkeypatch.setattr(sim_cls, "estimate_bytes", classmethod(
        lambda cls, p: (80 * 2**30, T("a grid of {nx:d} × {ny:d} nodes", nx=440, ny=180400000), T("reduce nx")) if p.get("drag") else None), raising=False)

    async def go():
        app = create_app(tmp_path / "runs", max_workers=2, worker_mem_gb=1.5)
        async with TestClient(TestServer(app)) as cl:
            r = await cl.post("/api/runs", json={"viz": "p99_toy", "params": {"drag": 0.1}})
            j = await r.json()
            assert r.status == 400 and j["text"] == ("A grid of 440 × 180400000 nodes would need about 80 GB of memory, "
                                                     "while the worker is given 1.5 GB. What to change: reduce nx")
            assert not list((tmp_path / "runs").glob("*/meta.json"))  # nothing was started
            rid = (await (await cl.post("/api/runs", json={"viz": "p99_toy", "preset": "two"})).json())["id"]
            run = app[MGR].get(rid)
            for _ in range(300):
                if any(e.kind == "header" for e in run.entries):
                    break
                await asyncio.sleep(0.05)
            lim = Path(f"/proc/{run.proc.pid}/limits").read_text()
            row = [ln for ln in lim.splitlines() if ln.startswith("Max data size")][0].split()
            assert int(row[3]) == int(row[4]) == int(1.5 * 2**30), row
            await cl.post(f"/api/runs/{rid}/stop")
    asyncio.run(go())


def test_a_check_refusal_of_parameters_is_said_at_the_start(tmp_path, monkeypatch):
    """UX-params P1: a combination a world refuses is said before anything is started (``check_params``), so that the
    catalogue shows it on the form where the owner set it."""
    from lfviz.errors import Refusal
    monkeypatch.setenv("LFVIZ_EXTRA", str(Path(__file__).resolve().parent / "playgrounds"))
    sim_cls = registry.load("p99_toy")["simulation"]

    def check(cls, p):
        if p.get("drag", 0) > 1:
            raise Refusal(T("a drag above 1 stops the particles within one step"), T("take “Drag” ≤ 1"))
    monkeypatch.setattr(sim_cls, "check_params", classmethod(check), raising=False)

    async def go():
        app = create_app(tmp_path / "runs", max_workers=1)
        async with TestClient(TestServer(app)) as cl:
            r = await cl.post("/api/runs", json={"viz": "p99_toy", "params": {"drag": 2.0}})
            j = await r.json()
            assert r.status == 400 and j["text"].endswith("What to change: take “Drag” ≤ 1")
            r = await cl.post("/api/runs", json={"viz": "p99_toy", "params": {"drag": -1}})
            j = await r.json()
            assert r.status == 400 and j["fields"] == {"drag": j["error"]} and "is below the minimum 0" in j["text"]
    asyncio.run(go())


def test_a_slice_plane_asked_beyond_the_box_stays_a_step_inside():
    """UX-params P22: a plane moved past the box stayed on its face (an empty window); now it is put a grid step inside
    the box, and the view's text says so."""
    from lfviz.planes3d import SlicePlanes

    class W(SlicePlanes):
        t = 0.0
        box = ((-1.0, -1.0, 0.0), (1.0, 1.0, 10.0))
        plane_center = (0.0, 0.0, 5.0)
        default_normals = {1: (0.0, 0.0, 1.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0)}
        plane_min_step = 0.1

        def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
            return {}

        def _plane_emit(self, pid):
            pass

        def _msg(self, meta):
            pass
    w = W()
    w._init_planes()
    text = w.view({"op": "plane", "id": 1, "origin": [0, 0, 50.0], "normal": [0, 0, 1]})
    assert w.planes[1]["origin"][2] == pytest.approx(9.9) and "at the edge" in str(text)
    text = w.view({"op": "plane", "id": 1, "origin": [0, 0, 3.0], "normal": [0, 0, 1]})
    assert w.planes[1]["origin"][2] == pytest.approx(3.0) and "at the edge" not in str(text)
