# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Instruments (plan P16.3): the measurables' series read back from a run's record, as JSON and CSV.

The fixture world ``tests/instruments_worlds/p97_osc`` (found through ``LFVIZ_EXTRA``) advances harmonic oscillators by
the exact rotation of their phase plane, so every recorded value has a closed form: x(t) = x0 cos ωt + v0/ω sin ωt,
E = m v²/2 + k x²/2. The series must give back exactly what the frames carried, at their world times, for the latest
world or a chosen one, thinned uniformly to a cap with the last frame kept, and the CSV must hold every frame with its
labels and units."""

import asyncio
import csv
import io
import math
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from lfviz import protocol
from lfviz.app import MGR, create_app

HERE = Path(__file__).resolve().parent
WORLDS = HERE / "instruments_worlds"


@pytest.fixture(autouse=True)
def _extra(monkeypatch):
    monkeypatch.setenv("LFVIZ_EXTRA", str(WORLDS))


def x_exact(t, x0=1.0, v0=0.0, k=4.0, m=1.0):
    w = math.sqrt(k / m)
    return x0 * math.cos(w * t) + v0 / w * math.sin(w * t)


async def wait_for(pred, timeout=60.0, step=0.05):
    t0 = asyncio.get_event_loop().time()
    while not pred():
        if asyncio.get_event_loop().time() - t0 > timeout:
            raise TimeoutError("condition not reached")
        await asyncio.sleep(step)


def frames_of(run, world=None):
    out, cur = [], None
    for e in run.entries:
        m = protocol.peek_meta(run._read(e, {}))
        if m.get("type") == "header":
            cur = m.get("world", 1)
        elif m.get("type") == "frame" and (world is None or cur == world):
            out.append(m)
    return out


async def start_played(cl, app, preset="one", play_s=1.5, speed=1.0, **body):
    r = await cl.post("/api/runs", json={"viz": "p97_osc", "preset": preset, "seed": 5, **body})
    rid = (await r.json())["id"]
    run = app[MGR].get(rid)
    await wait_for(lambda: any(e.kind == "header" for e in run.entries))
    await cl.post(f"/api/runs/{rid}/command", json={"cmd": "speed", "args": {"value": speed}})
    await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
    await asyncio.sleep(play_s)
    await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})
    await asyncio.sleep(0.6)
    return rid, run


async def _series(tmp_path):
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=600, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        rid, run = await start_played(cl, app)
        fr = frames_of(run)
        assert len(fr) > 15 and all("meas" in f for f in fr)
        # JSON: the recorded values at the frames' world times, equal to the exact motion (k = 4, m = 1: ω = 2)
        r = await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x,E"})
        js = await r.json()
        assert r.status == 200, js
        assert js["world"] == 1 and js["worlds"] == [1] and js["t_unit"] == "с" and js["stride"] == 1
        assert js["n"] == js["n_frames"] == len(fr)
        assert js["t"] == [f["t"] for f in fr]
        assert js["values"]["o1.x"] == [f["meas"]["o1.x"] for f in fr]
        assert max(abs(x - x_exact(t)) for t, x in zip(js["t"], js["values"]["o1.x"])) < 1e-12
        assert max(abs(e - 2.0) for e in js["values"]["E"]) < 1e-12
        assert js["measurables"][0]["title"] == "Осциллятор 1: положение" and js["measurables"][0]["unit"] == "м"
        # negative control: another law's motion does not fit the record
        assert max(abs(x - x_exact(t, k=4.4)) for t, x in zip(js["t"], js["values"]["o1.x"])) > 1e-2
        # a time range
        t_mid = js["t"][len(js["t"]) // 2]
        js2 = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x", "from": str(t_mid)})).json()
        assert js2["t"][0] == t_mid and js2["t"] == [t for t in js["t"] if t >= t_mid]
        # the cap: uniform stride, the last frame kept
        js3 = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x", "max_points": "5"})).json()
        assert js3["n"] <= 5 and js3["stride"] > 1 and js3["t"][-1] == js["t"][-1] and js3["t"][0] == js["t"][0]
        assert js3["t"][1] == js["t"][js3["stride"]]
        # CSV: every frame, one header line with the time unit, labels, units and ids
        r = await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x,E,x_first", "format": "csv"})
        assert r.status == 200 and r.headers["Content-Type"].startswith("text/csv")
        rows = list(csv.reader(io.StringIO(await r.text())))
        assert rows[0] == ["t, с", "Осциллятор 1: положение, м [o1.x]", "Полная энергия, Дж [E]",
                           "Положение первого осциллятора, м [x_first]"]
        assert len(rows) - 1 == len(fr)
        assert [float(r_[0]) for r_ in rows[1:]] == js["t"]
        assert [float(r_[1]) for r_ in rows[1:]] == js["values"]["o1.x"]  # exact: repr round trip
        # an undefined value (null in the record) is an empty cell: the scene emptied
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "scene", "args": {"op": "clear"}})
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "step", "args": {"dt": 0.1}})
        await asyncio.sleep(1.0)
        js4 = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "x_first"})).json()
        assert js4["values"]["x_first"][-1] is None and js4["notes"]["x_first"] == "в сцене нет осцилляторов"
        text = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "x_first,E", "format": "csv"})).text()
        assert text.rstrip().splitlines()[-1].split(",")[1] == "" and text.rstrip().splitlines()[-1].split(",")[2] == "0.0"
        # refusals in the owner's words
        for q, word in (({"ids": ""}, "укажите величины"), ({"ids": "nope"}, "нет величин: nope"),
                        ({"ids": "E", "world": "7"}, "нет мира 7"), ({"ids": "E", "from": "x"}, "«from» — число"),
                        ({"ids": "E", "format": "xml"}, "json или csv"), ({"ids": "E", "max_points": "1"}, "max_points")):
            r = await cl.get(f"/api/runs/{rid}/series", params=q)
            assert r.status == 400 and word in (await r.json())["error"], (q, await r.json())
        assert (await cl.get("/api/runs/nope/series", params={"ids": "E"})).status == 404
        # a new world: the latest by default, the first on request
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "new_world", "args": {"preset": "one", "params": {"k": 9.0}}})
        await wait_for(lambda: sum(1 for e in run.entries if e.kind == "header") == 2)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "step", "args": {"dt": 0.3}})
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "step", "args": {"dt": 0.3}})
        await asyncio.sleep(1.0)
        j_new = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x"})).json()
        j_old = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x", "world": "1"})).json()
        assert j_new["world"] == 2 and j_new["worlds"] == [1, 2] and j_old["world"] == 1
        assert j_old["t"] == [f["t"] for f in frames_of(run, 1)] and j_new["t"] == [f["t"] for f in frames_of(run, 2)]
        assert max(abs(x - x_exact(t, k=9.0)) for t, x in zip(j_new["t"], j_new["values"]["o1.x"])) < 1e-12
        await cl.post(f"/api/runs/{rid}/stop")


def test_series_json_csv_ranges_worlds_and_refusals(tmp_path):
    asyncio.run(_series(tmp_path))


async def _playground_window(tmp_path, monkeypatch):
    """A playground's record kept as a moving window: the series covers what the window keeps, the world taken from the
    segment (its header may be gone) — and the index is rebuilt when the window drops segments."""
    monkeypatch.setenv("LFVIZ_PLAYGROUND_CKPT", "0.4")
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=600, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        rid, run = await start_played(cl, app, play_s=0.1)
        run.meta["buffer"]["window_s"] = 1.0  # a short window: segments leave it while playing
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "play"})
        js0 = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x"})).json()
        await asyncio.sleep(4.0)
        await cl.post(f"/api/runs/{rid}/command", json={"cmd": "pause"})
        await asyncio.sleep(0.8)
        assert run.meta["buffer"].get("trimmed"), "the window should have dropped segments"
        js = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "o1.x"})).json()
        kept = [protocol.peek_meta(run._read(e, {}))["t"] for e in run.entries if e.is_frame]
        assert js["t"] == kept and js["t"][0] > js0["t"][0]
        assert max(abs(x - x_exact(t)) for t, x in zip(js["t"], js["values"]["o1.x"])) < 1e-12
        await cl.post(f"/api/runs/{rid}/stop")


def test_series_of_a_playground_window(tmp_path, monkeypatch):
    asyncio.run(_playground_window(tmp_path, monkeypatch))


def test_index_spans_and_labels(tmp_path):
    """The index's pieces on a record written by hand: worlds from headers, measurables from any message (a
    demonstration's header too), a probe's label from the scene, the time unit from the header."""
    from lfviz import instruments as I
    from lfviz.runs import Entry

    class FakeRun:
        buffered = False
        headers: dict = {}

        def __init__(self, path):
            self.path = path

        def seg_path(self, k):
            return self.path

    msgs = [{"type": "header", "world": 1, "t": 0.0, "units": {"t": "фс (время мира)"},
             "measurables": [{"id": "a", "label": "А", "unit": "м"}]},
            {"type": "frame", "t": 0.5, "meas": {"a": 1.0}},
            {"type": "scene", "t": 0.5, "objects": [{"id": "o1", "type": "probe", "label": "Датчик 1"}],
             "measurables": [{"id": "o1.d", "label": "расстояние", "unit": "м", "of": "o1"}]},
            {"type": "frame", "t": 1.0, "meas": {"a": 2.0, "o1.d": None}},
            {"type": "header", "world": 2, "t": 0.0},
            {"type": "frame", "t": 0.25, "meas": {}}]
    data, entries, off = bytearray(protocol.MAGIC), [], len(protocol.MAGIC)
    for m in msgs:
        b = protocol.encode(m)
        data += len(b).to_bytes(4, "little") + b
        entries.append(Entry(off + 4, len(b), m["type"] == "frame", m["type"] if m["type"] == "header" else "",
                             m.get("t"), 0))
        off += 4 + len(b)
    p = tmp_path / "rec.lfrec"
    p.write_bytes(bytes(data))
    run = FakeRun(p)
    idx = I.Index()
    idx.scan(run, entries, 3)  # part of the record, then the rest: the scan goes on where it stopped
    idx.scan(run, entries, len(entries))
    assert idx.spans == [[1, 0, 4], [2, 4, 6]]
    w1 = idx.worlds[1]
    assert w1.t_unit == "фс" and set(w1.decl) == {"a", "o1.d"} and idx.worlds[2].t_unit == "с"
    assert I.column_title(w1, w1.decl["o1.d"]) == "Датчик 1: расстояние, м [o1.d]"
    assert [e.t for e in idx.frames(entries, 1, 0.0, 0.9)] == [0.5] and len(idx.frames(entries, 2, -1, 9)) == 1
    ts, rows, _ = I.read_rows(run, idx.frames(entries, 1, -math.inf, math.inf), ["a", "o1.d"])
    assert ts == [0.5, 1.0] and rows == [[1.0, None], [2.0, None]]
    fr = list(range(10))
    assert I.thin(fr, 4) == ([0, 4, 8, 9], 4) and I.thin(fr, 10) == (fr, 1)
    assert I.thin(list(range(11)), 4) == ([0, 4, 8, 10], 4)


async def _csv_off_the_loop(tmp_path, monkeypatch):
    """Review LB1-framework F11: each batch of a CSV is read and formatted in a thread (formatting 4000 rows of 100
    columns in the event loop held every viewer for 0.36 s); an id named twice counts once; a CSV is bounded by its
    cells too (rows × columns), beyond which it takes every stride-th frame and says so."""
    import threading

    from lfviz import instruments as I
    where = []
    real = I.csv_batch

    def spy(*a):
        where.append(threading.current_thread() is threading.main_thread())
        return real(*a)
    monkeypatch.setattr(I, "csv_batch", spy)
    app = create_app(tmp_path / "runs", max_workers=2, idle_pause=600, idle_suspend=3600)
    async with TestClient(TestServer(app)) as cl:
        rid, run = await start_played(cl, app)
        n = len(frames_of(run))
        text = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "E,E,o1.x,E", "format": "csv"})).text()
        rows = list(csv.reader(io.StringIO(text)))
        assert rows[0] == ["t, с", "Полная энергия, Дж [E]", "Осциллятор 1: положение, м [o1.x]"] and len(rows) - 1 == n
        assert where and not any(where)  # never in the event loop's thread
        js = await (await cl.get(f"/api/runs/{rid}/series", params={"ids": "E,E"})).json()
        assert js["ids"] == ["E"]
        monkeypatch.setattr(I, "CSV_MAX_CELLS", 3 * 10)  # 3 columns: at most 10 rows
        r = await cl.get(f"/api/runs/{rid}/series", params={"ids": "E,o1.x", "format": "csv"})
        rows = list(csv.reader(io.StringIO(await r.text())))
        assert len(rows) - 1 <= 10 and "предел 10 строк" in rows[0][0] and int(r.headers["X-Lfviz-Stride"]) > 1
        await cl.post(f"/api/runs/{rid}/stop")


def test_csv_is_formatted_off_the_event_loop(tmp_path, monkeypatch):
    asyncio.run(_csv_off_the_loop(tmp_path, monkeypatch))
